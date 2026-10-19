#!/usr/bin/env python
"""Brunet Avalos 2019: cell_type_annotations.json from the authors' 29 clusters (fed cells).

The per-cell cluster assignments are the authors' own, in their UCSC Cell Browser dataset
(https://cells.ucsc.edu/?ds=dros-brain+normal, submitted by the Sprecher lab; `Cluster`
in meta.tsv); every cluster size equals the paper's Figure 1-source data 1. Cells are named
by their barcode in GEO's aggregated fed matrix (<barcode>-<n>), the suffix giving the
library: -3 Normal A (GSM3964166), -1 / -2 Normal B.1 / B.2 (GSM3964167 / GSM3964168),
-4 Normal C (GSM4132287), matched by the per-library barcode files.

  label              the authors' cluster name (e.g. "Cholinergic neurons 1")
  type               without its number (e.g. "Cholinergic neurons"; "Glia cells" ->
                     "Glial cells", the paper's spelling)
  cells_by_sample    cells per Sample (Normal A, B, C: sample ids Normal_sample_1 / _2 / _4)

Also writes .cache/avalos/memberships.tsv.gz (cell<TAB>cluster) for the expression build.

Usage:
    uv run python projects/avalos_2019/build_clusters.py
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

PROJ = Path(__file__).resolve().parent
CACHE = PROJ.parents[1] / ".cache" / "avalos"
META = CACHE / "cellbrowser" / "normal_meta.tsv"
META_URL = "https://cells.ucsc.edu/dros-brain/normal/meta.tsv"
SAMPLE = {"3": "Normal_sample_1", "1": "Normal_sample_2", "2": "Normal_sample_2",   # aggr suffix -> Sample id
          "4": "Normal_sample_4"}                       # (Normal A, B, C)
FIGURE_SIZES = 4407     # Figure 1-source data 1, summed


def main() -> None:
    cfg = yaml.safe_load((PROJ / "config.yaml").read_text())
    (clustering,) = cfg["sample_build"]["clusterings"]
    if not META.exists():
        META.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(META_URL, META)
    cells: dict[str, list[str]] = defaultdict(list)
    with open(META, newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            cells[r["Cluster"]].append(r["Cell"])
    n = sum(len(v) for v in cells.values())
    if len(cells) != 29 or n != FIGURE_SIZES:
        raise SystemExit(f"expected the authors' 29 clusters / {FIGURE_SIZES} cells, got {len(cells)} / {n}")
    anns = []
    for lab in sorted(cells, key=lambda x: -len(cells[x])):
        typ = re.sub(r"\s+\d+$", "", lab).replace("Glia cells", "Glial cells")
        anns.append({
            "label": lab.replace("Glia cells", "Glial cells"),
            "type": typ,
            "clustering": clustering["id"],
            "clustering_name": clustering["name"],
            "source_cluster_id": lab,
            "cell_number": len(cells[lab]),
            "cells_by_sample": dict(sorted(Counter(SAMPLE[c.rsplit("-", 1)[1]] for c in cells[lab]).items())),
        })
    with gzip.open(CACHE / "memberships.tsv.gz", "wt") as fh:
        fh.write("barcode\tcluster\n")
        for a in anns:
            fh.writelines(f"{c}\t{a['label']}\n" for c in cells[a["source_cluster_id"]])
    out = {
        "source": {"doi": cfg["source"]["doi"], "title": cfg["source"]["title"]},
        "dataset": {
            "accession": cfg["dataset"]["accession"],
            "label_source": "the authors' per-cell clusters in their UCSC Cell Browser dataset (dros-brain/normal); "
                            "every cluster size equals Figure 1-source data 1",
            "label_level": "author cluster",
            "validate_against": "paper, Figure 1-source data 1",
        },
        "annotations": anns,
    }
    (PROJ / "cell_type_annotations.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(anns)} clusters, {n} cells; types: {dict(Counter(a['type'] for a in anns))}")


if __name__ == "__main__":
    main()
