#!/usr/bin/env python
"""Calderon et al. 2022: samples.json from the GEO per-nucleus metadata (GSE190147).

The GSMs are sci-RNA-seq3 PCR wells pooling nuclei of several collection windows, so they
are not Samples. Each nucleus's collection window (`time`, from its RT barcode) and
experiment (`exp`) are in GEO's per-cell metadata
(GSE190147_scirnaseq_gene_matrix.columns.txt.gz). One Sample per collection window
(config `sample_build.windows`: hours and FBdv stage), one Assay per experiment x window.

Each Clustering uses the Samples its nuclei come from: the modelled windows from
.cache/calderon/cells.tsv.gz (export_windows.R), the neuronal re-clusterings from the
authors' annotation files (cell names prefixed with the modelled window). Only collection
windows giving at least `sample_build.min_sample_fraction` of a Clustering's nuclei are
linked (curator 2026-10-18: 1%); every modelled window has thin tails of nuclei from
distant collections (e.g. 7 of 0-2 h's 122,331 from 16-20 h), likely mis-aged.

Usage:
    uv run python projects/calderon_2022/build_samples.py
"""

from __future__ import annotations

import csv
import gzip
import json
import re
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from vfb_scrnaseq.ids import IDRegistry

PROJ = Path(__file__).resolve().parent
REPO_ROOT = PROJ.parents[1]
CACHE = REPO_ROOT / ".cache" / "calderon"
GEO_COLUMNS = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE190nnn/GSE190147/suppl/GSE190147_scirnaseq_gene_matrix.columns.txt.gz"
NEURONAL = {"neuronal": "neuronal_subcluster_annotations.txt",
            "neuronal_mature": "neuronal_subsubcluster_annotations.txt"}


def neuronal_cells(path: Path) -> list[tuple[str, str, str]]:
    """(cell, annotation, cluster) from an authors' neuronal annotation file; names are
    <modelled window>_<GEO cell name>, annotations may contain line breaks."""
    body = path.read_text().split("\n", 1)[1]
    recs = re.findall(r"(\d+_\d+)_(exp\S+)\t(.*?)\t(\d+)\n", body, re.S)
    return [(cell, " ".join(ann.split()), clu) for _w, cell, ann, clu in recs]


def main() -> None:
    cfg = yaml.safe_load((PROJ / "config.yaml").read_text())
    sb, acc = cfg["sample_build"], cfg["dataset"]["accession"]
    cols = CACHE / "GSE190147_scirnaseq_gene_matrix.columns.txt.gz"
    if not cols.exists():
        urllib.request.urlretrieve(GEO_COLUMNS, cols)
    window_of: dict[str, str] = {}
    by_assay: Counter = Counter()
    with gzip.open(cols, "rt") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            window_of[r["cell"]] = r["time"]
            by_assay[(r["time"], r["exp"])] += 1
    unknown = {w for w, _ in by_assay} - set(sb["windows"])
    if unknown:
        raise SystemExit(f"collection windows not in config: {sorted(unknown)}")

    reg = IDRegistry.load(REPO_ROOT / "id_registry" / "registry.json")
    dataset_id = reg.mint("Dataset", acc, label=cfg["source"]["title"], accession=acc)
    samples, assays, sample_of = [], [], {}
    for w, spec in sb["windows"].items():
        svid = reg.mint("Sample", f"{acc}:{w}", label=w)
        sample_of[w] = svid
        exps = sorted((e for ww, e in by_assay if ww == w), key=lambda e: int(e[3:]))
        avids = []
        for e in exps:
            avid = reg.mint("Assay", f"{acc}:{w}:{e}", label=f"{w} {e}")
            avids.append(avid)
            assays.append({"vfbseq_id": avid, "library_id": e, "accession": None, "dbxrefs": [],
                           "n_sources": by_assay[(w, e)], "method": sb["assay_method"],
                           "sample_vfbseq_id": svid, "associated_dataset": dataset_id})
        samples.append({
            "vfbseq_id": svid, "sample_id": w,
            "label": f"{sb['tissue']['label']}, {spec['hours']} after egg laying, {sb['genotype']}",
            "tissue_raw": None, "age_raw": spec["hours"], "genotype": sb["genotype"], "stock": None,
            "sex": None, "stage": spec["stage"], "sample_tissue": [sb["tissue"]],
            "associated_dataset": dataset_id, "assay_vfbseq_ids": avids, "n_assays": len(avids),
        })

    # the Samples (collection windows) each Clustering's nuclei come from
    counts: dict[str, Counter] = defaultdict(Counter)
    with gzip.open(CACHE / "cells.tsv.gz", "rt") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            counts[r["window"]][r["time"]] += 1
    for cid, f in NEURONAL.items():
        counts[cid] = Counter(window_of[c] for c, _a, _k in neuronal_cells(CACHE / f))
    floor = float(sb["min_sample_fraction"])
    used = {cid: {w for w, n in cnt.items() if n >= floor * sum(cnt.values())} for cid, cnt in counts.items()}
    clusterings = []
    for c in sb["clusterings"]:
        if not used.get(c["id"]):
            raise SystemExit(f"no nuclei for clustering {c['id']}")
        clusterings.append({
            "vfbseq_id": reg.mint("Clustering", f"{acc}:{c['id']}", label=c["name"]),
            "subset": c["id"], "associated_dataset": dataset_id, "name": c["name"],
            "samples": [sample_of[w] for w in sb["windows"] if w in used[c["id"]]],
        })
    out = {"dataset": {"vfbseq_id": dataset_id, "accession": acc, "site": cfg["dataset"]["site"]},
           "samples": samples, "assays": assays, "clusterings": clusterings}
    (PROJ / "samples.json").write_text(json.dumps(out, indent=2) + "\n")
    reg.save()
    print(f"wrote {len(samples)} samples ({sum(a['n_sources'] for a in assays)} nuclei), {len(assays)} assays, "
          f"{len(clusterings)} clusterings: " + ", ".join(f"{c['subset']} <- {len(c['samples'])}" for c in clusterings))


if __name__ == "__main__":
    main()
