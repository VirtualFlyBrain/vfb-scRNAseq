#!/usr/bin/env python
"""Li, Horns et al. 2017: link the paper's decoded GH146 clusters to the authors' HDBSCAN
cluster numbers.

The authors' per-cell GH146 clusters (FlyPN data/labels_HDBSCAN.csv: 0-29) are numbered
differently from the paper's figure labels, which name the decoded clusters (#1 DC2,
#2 / #2' DA1, #3 VA1d, #4 DC3, #5 VM2, #6 / #6' DL3) and define them by driver mapping
and markers (Figures 3-4):
  - "All 91G04+ PNs mapped to one GH146+ cluster ... (Cluster #1) ... using a random
    forest classifier" -> DC2;
  - Mz19+/acj6- DA1 PNs "map to two clusters, #2 and #2'"; Mz19+/acj6+ VA1d and DC3 PNs
    "map to two clusters, #3 and #4"; "CG31676 is highly expressed in Cluster #3, but not
    #4" -> #3 VA1d, #4 DC3;
  - "trol-GAL4+ PNs map to one GH146+ PN cluster ... which expresses high levels of trol"
    -> #5 VM2;
  - "the remaining acj6-/CG31676+ cells (Clusters #6 and #6')" -> DL3.
This repeats that procedure on the authors' data: a random forest on the authors' ICIM
genes (data/genes_GH146_ICIM.txt), trained on the GH146 cells' HDBSCAN clusters, assigns
the driver cells (the authors' Mz19 24 h DA1 / VA1d / DC3 lists; 91G04 cells; NP5103
cells expressing trol, as the authors selected them: log2 CPM > 3), and the markers are
summarised per cluster. Writes projects/li_2017/cluster_matching.tsv.

Usage:
    uv run --with scikit-learn python projects/li_2017/match_clusters.py
"""

from __future__ import annotations

import gzip
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

PROJ = Path(__file__).resolve().parent
CACHE = PROJ.parents[1] / ".cache" / "li2017"
MARKERS = ["acj6", "CG31676", "trol", "fru", "vvl"]


def names(f: str) -> list[str]:
    return [ln.strip() for ln in (CACHE / f).read_text().splitlines() if ln.strip()]


def main() -> None:
    with gzip.open(CACHE / "htseq_logCPM_neurons.tab.gz", "rt") as fh:
        X = pd.read_csv(fh, sep="\t", index_col=0)
    libs = pd.read_csv(CACHE / "df_libs.csv.gz").set_index("library")
    labels = pd.read_csv(CACHE / "labels_HDBSCAN.csv", sep="\t").set_index("name")["label"]
    genes = [g for g in names("genes_GH146_ICIM.txt") if g in X.index]
    train = labels[labels >= 0]
    rf = RandomForestClassifier(n_estimators=1000, random_state=0, n_jobs=-1)
    rf.fit(X.loc[genes, train.index].T.values, train.values)

    queries = {f"Mz19 {t} 24h": names(f"names_{t}_24hAPF.txt") for t in ("DA1", "VA1d", "DC3")}
    queries["91G04"] = [c for c in libs.index[libs.label == "91G04-GFP"] if c in X.columns]
    np5103 = [c for c in libs.index[libs.label == "NP5103-GFP"] if c in X.columns]
    queries["NP5103 trol+"] = [c for c in np5103 if X.at["trol", c] > 3]
    rows = []
    for q, cells in queries.items():
        cells = [c for c in cells if c in X.columns]
        pred = pd.Series(rf.predict(X.loc[genes, cells].T.values)).value_counts()
        rows.append({"query": q, "cells": len(cells),
                     "predicted_clusters": "; ".join(f"{k}: {v}" for k, v in pred.items())})
    print(pd.DataFrame(rows).to_string(index=False))

    frac = pd.DataFrame({m: (X.loc[m, train.index] > 0).groupby(train).mean() for m in MARKERS})
    frac["cells"] = train.value_counts()
    frac.index.name = "hdbscan_cluster"
    frac.round(2).to_csv(PROJ / "cluster_matching.tsv", sep="\t")
    print(frac.round(2).to_string())


if __name__ == "__main__":
    main()
