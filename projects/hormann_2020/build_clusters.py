#!/usr/bin/env python
"""Hörmann 2020: cell_type_annotations.json from the authors' per-stage clusters.

The authors clustered each stage separately and assigned each of its eight clusters to
one T4/T5 subtype ("all eight single cell clusters to four T4 and four T5 subtypes in
every examined developmental stage"). GEO (GSE147987) carries only the per-library
matrices; the per-cell labels are the authors' as given to the Single Cell Expression
Atlas (E-GEOD-147987 experiment design, "inferred cell type - authors labels"), e.g.
"T4a neuron 0": the subtype, then a number 0-8 that appears to be the cross-stage
integrated clustering (Fig 3D; not loaded). A cell's stage (its library) and subtype
give its author cluster: one entry per stage x subtype.

  label              <stage>_<subtype> (e.g. 24h_T4a)
  type               the subtype as the authors label it (e.g. "T4a neuron")
  clustering         the stage (24h, 36h, 48h, 60h, 72h)
  source_cluster_id  the subtype label (the authors give the per-stage clusters no numbers)
  cells_by_library   cells per GEO library (GSM title)

Also writes .cache/hormann/memberships.tsv.gz (cell<TAB>cluster, cells named
<GSM title>_<10x barcode>, as in the combined matrix of combine_matrices.py) for the
expression build.

Usage:
    uv run python projects/hormann_2020/build_clusters.py
"""

from __future__ import annotations

import csv
import gzip
import json
import re
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

import yaml

PROJ = Path(__file__).resolve().parent
REPO_ROOT = PROJ.parents[1]
CACHE = REPO_ROOT / ".cache" / "hormann"
SCEA = CACHE / "scea"
SCEA_URL = "https://www.ebi.ac.uk/gxa/sc/experiment/E-GEOD-147987/download"
AUTHOR_COL = "Factor Value[inferred cell type - authors labels]"


def fetch_scea() -> None:
    """The SCEA experiment design (per-cell labels) and MAGE-TAB (SDRF), cached."""
    SCEA.mkdir(parents=True, exist_ok=True)
    if not (SCEA / "design.tsv").exists():
        urllib.request.urlretrieve(SCEA_URL + "?fileType=experiment-design&accessKey=", SCEA / "design.tsv")
    if not (SCEA / "E-GEOD-147987.sdrf.txt").exists():
        urllib.request.urlretrieve(SCEA_URL + "/zip?fileType=experiment-metadata&accessKey=", SCEA / "meta.zip")
        zipfile.ZipFile(SCEA / "meta.zip").extractall(SCEA)


def main() -> None:
    cfg = yaml.safe_load((PROJ / "config.yaml").read_text())
    names = {c["id"]: c["name"] for c in cfg["sample_build"]["clusterings"]}
    fetch_scea()
    with open(SCEA / "E-GEOD-147987.sdrf.txt", newline="") as fh:
        library = {r["Comment[BioSD_Sample]"]: r["Comment[Sample_title]"]
                   for r in csv.DictReader(fh, delimiter="\t")}
    cells: dict[str, list[str]] = {}               # cluster label -> cell names
    types: dict[str, str] = {}
    with open(SCEA / "design.tsv", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if not r[AUTHOR_COL]:
                continue                           # removed by the authors' filtering
            biosample, barcode = r["Assay"].split("-", 1)
            lib = library[biosample]               # e.g. 24h_APF_1
            stage = lib.split("_")[0]
            subtype = re.fullmatch(r"(T[45][a-d]) neuron \d+", r[AUTHOR_COL]).group(1)
            label = f"{stage}_{subtype}"
            types[label] = f"{subtype} neuron"
            cells.setdefault(label, []).append(f"{lib}_{barcode}-1")
    order = {c: i for i, c in enumerate(names)}
    anns = []
    for label in sorted(cells, key=lambda x: (order[x.split("_")[0]], x)):
        stage, subtype = label.split("_")
        libs = Counter(c.rsplit("_", 1)[0] for c in cells[label])
        anns.append({
            "label": label,
            "type": types[label],
            "clustering": stage,
            "clustering_name": names[stage],
            "source_cluster_id": types[label],     # no cluster numbers: the subtype
            "cell_number": len(cells[label]),
            "cells_by_library": dict(sorted(libs.items())),
        })
    with gzip.open(CACHE / "memberships.tsv.gz", "wt") as fh:
        fh.write("barcode\tcluster\n")
        for label, cs in cells.items():
            for c in cs:
                fh.write(f"{c}\t{label}\n")
    out = {
        "source": {"doi": cfg["source"]["doi"], "title": cfg["source"]["title"]},
        "dataset": {
            "accession": cfg["dataset"]["accession"],
            "label_source": "the authors' per-cell labels in SCEA E-GEOD-147987 ('inferred cell "
                            "type - authors labels': the subtype of the cell's per-stage cluster), "
                            "with the cell's stage from its GEO library",
            "label_level": "author cluster (one per stage x subtype)",
            "validate_against": "paper (per-stage clusters assigned to the eight subtypes)",
        },
        "annotations": anns,
    }
    (PROJ / "cell_type_annotations.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    by = Counter(a["clustering"] for a in anns)
    print(f"wrote {len(anns)} clusters ({dict(by)}), {sum(a['cell_number'] for a in anns)} cells")


if __name__ == "__main__":
    main()
