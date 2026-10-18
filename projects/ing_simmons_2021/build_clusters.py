#!/usr/bin/env python
"""Ing-Simmons 2021: cell_type_annotations.json from the authors' clusters (controls).

The authors integrated their five libraries (two controls and three maternal-mutant
genotypes) and clustered them together into 15 clusters, named by cell identity
("mesoderm1", "ectoderm3", "pole cells", ...; Fig. 2, Supplementary Table 2).
ArrayExpress (E-MTAB-9304) has FASTQs only; the per-cell labels are the authors' as
given to the Single Cell Expression Atlas (E-MTAB-9304 experiment design, "inferred cell
type - authors labels"; 16,786 cells, the paper 16,790). Curator 2026-10-18: controls
only, so each cluster keeps its cells from the two control Samples.

  label              the authors' cluster name (e.g. "mesoderm1")
  type               the cell identity, without the cluster number (e.g. "mesoderm";
                     "haemocytes" -> "haemocyte", "pole cells" -> "pole cell")
  source_cluster_id  the authors' cluster name
  cells_by_sample    control cells per Sample (replicate)
  all_genotypes_cell_number  the cluster's cells in all five libraries (the authors' size)

Also writes .cache/ing_simmons/memberships.tsv.gz (cell<TAB>cluster; cells named as in
SCEA, <BioSample>-<barcode>) for the expression build.

Usage:
    uv run python projects/ing_simmons_2021/build_clusters.py
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
CACHE = REPO_ROOT / ".cache" / "ing_simmons"
DESIGN = CACHE / "scea_design.tsv"
SCEA_URL = "https://www.ebi.ac.uk/gxa/sc/experiment/E-MTAB-9304/download?fileType=experiment-design&accessKey="
AUTHOR_COL = "Factor Value[inferred cell type - authors labels]"
CONTROLS = {"SAMEA7039590": "control_stage5_Rep1", "SAMEA7039591": "control_stage5_Rep2"}   # BioSample -> SDRF source
TYPE = {"haemocytes": "haemocyte", "pole cells": "pole cell"}


def main() -> None:
    cfg = yaml.safe_load((PROJ / "config.yaml").read_text())
    (clustering,) = cfg["sample_build"]["clusterings"]
    if not DESIGN.exists():
        urllib.request.urlretrieve(SCEA_URL, DESIGN)
    cells: dict[str, list[str]] = {}
    total: Counter = Counter()
    with open(DESIGN, newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            lab = r[AUTHOR_COL]
            if not lab:
                continue                           # removed by the authors' filtering
            total[lab] += 1
            if r["Assay"].split("-", 1)[0] in CONTROLS:
                cells.setdefault(lab, []).append(r["Assay"])
    if len(total) != 15 or set(cells) != set(total):
        raise SystemExit(f"expected the authors' 15 clusters in the controls: {sorted(total)} / {sorted(cells)}")
    anns = []
    for lab in sorted(cells):
        base = re.sub(r"\d+$", "", lab)
        anns.append({
            "label": lab,
            "type": TYPE.get(base, base),
            "clustering": clustering["id"],
            "clustering_name": clustering["name"],
            "source_cluster_id": lab,
            "cell_number": len(cells[lab]),
            "cells_by_sample": dict(sorted(Counter(CONTROLS[c.split("-", 1)[0]] for c in cells[lab]).items())),
            "all_genotypes_cell_number": total[lab],
        })
    with gzip.open(CACHE / "memberships.tsv.gz", "wt") as fh:
        fh.write("barcode\tcluster\n")
        fh.writelines(f"{c}\t{lab}\n" for lab in sorted(cells) for c in cells[lab])
    out = {
        "source": {"doi": cfg["source"]["doi"], "title": cfg["source"]["title"]},
        "dataset": {
            "accession": cfg["dataset"]["accession"],
            "label_source": "the authors' per-cell labels in SCEA E-MTAB-9304 ('inferred cell type - "
                            "authors labels'), control cells only",
            "label_level": "author cluster (restricted to the control cells)",
            "validate_against": "paper, Fig. 2 and Extended Data Fig. 3",
        },
        "annotations": anns,
    }
    (PROJ / "cell_type_annotations.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    n = sum(a["cell_number"] for a in anns)
    print(f"wrote {len(anns)} clusters, {n} control cells of {sum(total.values())}; "
          f"{ {a['label']: a['cell_number'] for a in anns} }")


if __name__ == "__main__":
    main()
