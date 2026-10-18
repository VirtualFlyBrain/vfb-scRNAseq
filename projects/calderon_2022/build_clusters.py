#!/usr/bin/env python
"""Calderon et al. 2022: cell_type_annotations.json from the authors' clusters.

Modelled windows (9 Clusterings, 0-18 h): the authors binned nuclei by their NNv1 age
into 2-hour windows, clustered each and annotated each cluster by hand (Table S1,
supp/table_s1_withLineage.xlsx). Each nucleus's cluster comes from the authors' window
objects (.cache/calderon/cells.tsv.gz, export_windows.R).

  label              <window>h_<cluster> (e.g. 10_12h_5)
  type               the authors' "selected annotation (manual)" (e.g. "epidermis primordium")
  author_germ_layer, author_lineage, author_automated  the table's other calls
  stage              the narrowest FBdv term covering the window's stages, where one is
                     narrower than embryonic stage (config `cluster_stages`; the nuclei's
                     ages come from their own transcriptomes; curator 2026-10-18)
  unannotated        "ubiquitous", "maternal" and "unknown" clusters (held: untyped)

Neuronal re-clusterings (2 Clusterings, 6-18 h pooled): the authors' sub-clusters of the
neuroectoderm and sub-sub-clusters of its mature neurons (portal annotation files).

  label              neuronal_<n> / neuronal_mature_<n>
  type               the authors' annotation without its number ("Cholinergic 1" -> "Cholinergic")
  source_cluster_id  the authors' cluster number; author_annotation keeps the full name

Also writes .cache/calderon/memberships.tsv.gz (GEO cell name<TAB>cluster label; a nucleus
in a neuronal cluster is also in its window cluster) for the expression build.

Usage:
    uv run --with openpyxl python projects/calderon_2022/build_clusters.py
"""

from __future__ import annotations

import csv
import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl
import yaml

PROJ = Path(__file__).resolve().parent
REPO_ROOT = PROJ.parents[1]
CACHE = REPO_ROOT / ".cache" / "calderon"
TABLE = PROJ / "supp" / "table_s1_withLineage.xlsx"
HELD = {"ubiquitous", "maternal", "unknown"}
SPELLING = {"spiracles (tracheal system)": "spiracle (tracheal system)"}   # one type, two spellings in Table S1
NEURONAL = {"neuronal": "neuronal_subcluster_annotations.txt",
            "neuronal_mature": "neuronal_subsubcluster_annotations.txt"}


def clean(v) -> str | None:
    v = " ".join(str(v).split()) if v is not None else ""
    return v if v and v != "NA" else None


def table() -> dict[tuple[str, str], dict]:
    rows = list(openpyxl.load_workbook(TABLE, read_only=True).active.iter_rows(values_only=True))[1:]
    out = {}
    for r in rows:
        if r[0]:
            out[(r[0].replace("-", "_"), str(r[1]))] = {
                "annotation": SPELLING.get(clean(r[6]), clean(r[6])), "germ_layer": clean(r[7]), "lineage": clean(r[11]),
                "automated": clean(r[2])}
    return out


def neuronal_cells(path: Path) -> list[tuple[str, str, str]]:
    """(GEO cell name, annotation, cluster) from an authors' neuronal annotation file."""
    body = path.read_text().split("\n", 1)[1]
    recs = re.findall(r"(\d+_\d+)_(exp\S+)\t(.*?)\t(\d+)\n", body, re.S)
    return [(cell, " ".join(ann.split()), clu) for _w, cell, ann, clu in recs]


def main() -> None:
    cfg = yaml.safe_load((PROJ / "config.yaml").read_text())
    sb = cfg["sample_build"]
    names = {c["id"]: c["name"] for c in sb["clusterings"]}
    window_of: dict[str, str] = {}
    with gzip.open(CACHE / "GSE190147_scirnaseq_gene_matrix.columns.txt.gz", "rt") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            window_of[r["cell"]] = r["time"]
    tab = table()
    cells: dict[str, list[str]] = defaultdict(list)
    meta: dict[str, dict] = {}
    with gzip.open(CACHE / "cells.tsv.gz", "rt") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            label = f"{r['window']}h_{r['cluster']}"
            cells[label].append(r["cell"])
            meta.setdefault(label, {"clustering": r["window"], "n": r["cluster"]})
    anns = []
    order = [c["id"] for c in sb["clusterings"]]
    for label in sorted(meta, key=lambda x: (order.index(meta[x]["clustering"]), int(meta[x]["n"]))):
        w, n = meta[label]["clustering"], meta[label]["n"]
        t = tab[(w, n)]
        rec = {"label": label, "type": t["annotation"], "clustering": w, "clustering_name": names[w],
               "source_cluster_id": n, "cell_number": len(cells[label]),
               "cells_by_sample": dict(sorted(Counter(window_of[c] for c in cells[label]).items()))}
        for k in ("germ_layer", "lineage", "automated"):
            if t[k]:
                rec[f"author_{k}"] = t[k]
        stage = sb["cluster_stages"].get(w)
        if stage:
            rec["stage"] = stage
        if t["annotation"] in HELD:
            rec["unannotated"] = True
        anns.append(rec)
    for cid, f in NEURONAL.items():
        groups: dict[str, list[str]] = defaultdict(list)
        full: dict[str, str] = {}
        for cell, ann, clu in neuronal_cells(CACHE / f):
            groups[clu].append(cell)
            full[clu] = ann
        for clu in sorted(groups, key=int):
            label = f"{cid}_{clu}"
            cells[label] = groups[clu]
            anns.append({"label": label, "type": re.sub(r"\s+\d+$", "", full[clu]), "clustering": cid,
                         "clustering_name": names[cid], "source_cluster_id": clu,
                         "cell_number": len(groups[clu]), "author_annotation": full[clu],
                         "cells_by_sample": dict(sorted(Counter(window_of[c] for c in groups[clu]).items()))})
    with gzip.open(CACHE / "memberships.tsv.gz", "wt") as fh:
        fh.write("barcode\tcluster\n")
        for a in anns:
            fh.writelines(f"{c}\t{a['label']}\n" for c in cells[a["label"]])
    out = {
        "source": {"doi": cfg["source"]["doi"], "title": cfg["source"]["title"]},
        "dataset": {
            "accession": cfg["dataset"]["accession"],
            "label_source": "the authors' clusters per modelled 2-hour window (NNv1 window Seurat objects, "
                            "Table S1 manual annotations) and their neuronal re-clusterings (portal annotation files)",
            "label_level": "author cluster",
            "validate_against": "paper, Fig. 3 and Table S1",
        },
        "annotations": anns,
    }
    (PROJ / "cell_type_annotations.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    by = Counter(a["clustering"] for a in anns)
    held = Counter(a["type"] for a in anns if a.get("unannotated"))
    print(f"wrote {len(anns)} clusters ({dict(by)}); held {sum(held.values())} {dict(held)}; "
          f"{len({a['type'] for a in anns if not a.get('unannotated')})} types to map")


if __name__ == "__main__":
    main()
