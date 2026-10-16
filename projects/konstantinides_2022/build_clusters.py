#!/usr/bin/env python
"""Konstantinides 2022: cell_type_annotations.json from the authors' L3 clusters.

The authors' Seurat object (exported by export_seurat.R to
.cache/konstantinides/metadata.tsv.gz) gives every L3 cell its L3 cluster
(`integrated_snn_res.2`, L3_0-L3_94) and the cluster's neuropil class (`Neuropil`).
The paper names only a few L3 clusters; the per-cluster key is the authors' labels as
given to the Single Cell Expression Atlas (E-GEOD-167266 experiment design, "inferred
cell type - authors labels", numbered by L3 cluster, e.g. "glial cell 44"), matched to
the L3 cells by library (BioSample -> GSM title "rep <n>" -> Lib<n>) and barcode.

  label              L3_<n>
  type               the SCEA author label of most of the cluster's cells, without the
                     trailing cluster number ("glial cell 44" -> "glial cell")
  author_label       that label as given
  author_label_share fraction of the cluster's labelled cells with that label
  author_neuropil    the authors' neuropil class for the cluster (`Neuropil`)
  source_cluster_id  n
  cells_by_library   cells per library (`orig.ident`)
  unannotated        True for a cluster the authors left unlabelled ("unannonated N",
                     sic) or with no SCEA label (L3_0, not in SCEA), and for the author
                     types the curator holds (config `held_types`)

Usage:
    uv run python projects/konstantinides_2022/build_clusters.py
"""

from __future__ import annotations

import csv
import gzip
import json
import re
import urllib.request
from collections import Counter
from pathlib import Path

import yaml

PROJ = Path(__file__).resolve().parent
REPO_ROOT = PROJ.parents[1]
CACHE = REPO_ROOT / ".cache" / "konstantinides"
SCEA = CACHE / "scea"
SCEA_URL = "https://www.ebi.ac.uk/gxa/sc/experiment/E-GEOD-167266/download"
SCEA_FILES = {"design.tsv": "?fileType=experiment-design&accessKey=",
              "meta.zip": "/zip?fileType=experiment-metadata&accessKey="}
AUTHOR_COL = "Factor Value[inferred cell type - authors labels]"
CLUSTER_COL = "integrated_snn_res.2"
UNLABELLED = re.compile(r"unann?onated \d+")


def fetch_scea() -> None:
    """The SCEA experiment design (per-cell labels) and MAGE-TAB (SDRF), cached."""
    import zipfile
    SCEA.mkdir(parents=True, exist_ok=True)
    for name, query in SCEA_FILES.items():
        if not (SCEA / name).exists():
            urllib.request.urlretrieve(SCEA_URL + query, SCEA / name)
    if not (SCEA / "E-GEOD-167266.sdrf.txt").exists():
        zipfile.ZipFile(SCEA / "meta.zip").extractall(SCEA)


def scea_labels() -> dict[str, str]:
    """{Lib<n>_<barcode>: author label} from the SCEA experiment design."""
    with open(SCEA / "E-GEOD-167266.sdrf.txt", newline="") as fh:
        lib = {r["Comment[BioSD_Sample]"]: "Lib" + re.search(r"rep (\d+)$", r["Comment[Sample_title]"]).group(1)
               for r in csv.DictReader(fh, delimiter="\t")}
    out = {}
    with open(SCEA / "design.tsv", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r[AUTHOR_COL]:
                biosample, barcode = r["Assay"].split("-", 1)
                out[f"{lib[biosample]}_{barcode}"] = r[AUTHOR_COL]
    return out


def main() -> None:
    cfg = yaml.safe_load((PROJ / "config.yaml").read_text())
    (clustering,) = cfg["sample_build"]["clusterings"]
    held = set(cfg.get("held_types") or {})
    fetch_scea()
    labels = scea_labels()
    with gzip.open(CACHE / "metadata.tsv.gz", "rt") as fh:
        rows = [r for r in csv.DictReader(fh, delimiter="\t") if r["orig.ident"].startswith("Lib")]
    by_cluster: dict[str, list[dict]] = {}
    for r in rows:
        by_cluster.setdefault(r[CLUSTER_COL], []).append(r)
    anns = []
    for num in sorted(by_cluster, key=int):
        cells = by_cluster[num]
        # cell names are L3_<barcode>_<n>; SCEA keys on library + barcode
        got = Counter(labels.get(f"{r['orig.ident']}_{r['barcode'].split('_')[1]}") for r in cells)
        got.pop(None, None)
        neuropil = {r["Neuropil"] for r in cells}
        assert len(neuropil) == 1, (num, neuropil)
        rec = {
            "label": f"L3_{num}",
            "clustering": clustering["id"],
            "clustering_name": clustering["name"],
            "source_cluster_id": num,
            "cell_number": len(cells),
            "cells_by_library": dict(sorted(Counter(r["orig.ident"] for r in cells).items(),
                                            key=lambda kv: int(kv[0][3:]))),
            "author_neuropil": neuropil.pop(),
        }
        if got:
            label, n = got.most_common(1)[0]
            rec["type"] = re.sub(rf" {num}$", "", label)
            rec["author_label"] = label
            rec["author_label_share"] = round(n / sum(got.values()), 3)
            if UNLABELLED.fullmatch(label):
                rec["type"] = f"L3_{num}"
                rec["unannotated"] = True
            elif rec["type"] in held:
                rec["unannotated"] = True           # curator-held type
        else:
            rec["type"] = f"L3_{num}"
            rec["unannotated"] = True               # not in SCEA (no author label)
        anns.append(rec)
    out = {
        "source": {"doi": cfg["source"]["doi"], "title": cfg["source"]["title"]},
        "dataset": {
            "accession": cfg["dataset"]["accession"],
            "label_source": "authors' Seurat object (GEO GSE167266) obs `integrated_snn_res.2`, "
                            "named from the authors' labels in SCEA E-GEOD-167266 "
                            "('inferred cell type - authors labels')",
            "label_level": "author cluster (one entry per L3 cluster)",
            "validate_against": "paper, extended data figures and the authors' scripts",
        },
        "annotations": anns,
    }
    (PROJ / "cell_type_annotations.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    held = [a["label"] for a in anns if a.get("unannotated")]
    low = [(a["label"], a["author_label_share"]) for a in anns if a.get("author_label_share", 1) < 0.9]
    print(f"wrote {len(anns)} clusters; {len(held)} held (unlabelled or held types) {held}; label share < 0.9: {low}")


if __name__ == "__main__":
    main()
