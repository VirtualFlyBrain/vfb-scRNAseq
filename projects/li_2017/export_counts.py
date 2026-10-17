#!/usr/bin/env python
"""Li, Horns et al. 2017: the GEO raw counts as a MatrixMarket matrix for the expression build.

GEO's GSE100058_htseq.tab.gz is a CSV of HTSeq read counts (gene symbol x library, genome
r6.10), with ERCC spike-ins and HTSeq's summary rows ("__no_feature" etc.), which are
dropped. Only the cells in the loaded analyses (the memberships from build_clusters.py)
are kept. Writes .cache/li2017/counts/{matrix.mtx.gz, features.tsv.gz, barcodes.tsv.gz}.

Usage:
    uv run python projects/li_2017/export_counts.py
"""

from __future__ import annotations

import csv
import gzip
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path(__file__).resolve().parents[2] / ".cache" / "li2017"
URL = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE100nnn/GSE100058/suppl/GSE100058_htseq.tab.gz"


def main() -> None:
    src = CACHE / "GSE100058_htseq.tab.gz"
    if not src.exists():
        urllib.request.urlretrieve(URL, src)
    with gzip.open(CACHE / "memberships.tsv.gz", "rt") as fh:
        cells = sorted({r["barcode"] for r in csv.DictReader(fh, delimiter="\t")})
    counts = pd.read_csv(src, index_col=0)
    counts = counts[~counts.index.str.startswith(("ERCC-", "__"))]
    missing = [c for c in cells if c not in counts.columns]
    if missing:
        raise SystemExit(f"cells without counts: {missing[:5]} ({len(missing)})")
    m = counts[cells]
    m = m[(m > 0).any(axis=1)]                       # genes detected in any loaded cell
    out = CACHE / "counts"
    out.mkdir(exist_ok=True)
    rows, cols = np.nonzero(m.values)
    vals = m.values[rows, cols]
    with gzip.open(out / "matrix.mtx.gz", "wt") as fh:
        fh.write("%%MatrixMarket matrix coordinate integer general\n")
        fh.write(f"{m.shape[0]} {m.shape[1]} {len(vals)}\n")
        fh.writelines(f"{r + 1} {c + 1} {int(v)}\n" for r, c, v in zip(rows, cols, vals))
    with gzip.open(out / "features.tsv.gz", "wt") as fh:
        fh.writelines(f"{g}\t{g}\n" for g in m.index)
    with gzip.open(out / "barcodes.tsv.gz", "wt") as fh:
        fh.writelines(f"{c}\n" for c in m.columns)
    print(f"wrote {m.shape[0]} genes x {m.shape[1]} cells, {len(vals)} non-zero -> {out}")


if __name__ == "__main__":
    main()
