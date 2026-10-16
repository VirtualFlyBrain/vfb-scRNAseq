#!/usr/bin/env python
"""Hörmann 2020: one count matrix from the ten GEO libraries.

GEO (GSE147987) has a filtered 10x matrix per library; each author cluster spans the two
replicate libraries of its stage, so the expression build reads one matrix with the
libraries side by side. Cells are named <GSM title>_<10x barcode> (e.g.
24h_APF_1_AAACCCAAGACCACGA-1), as in build_clusters.py's memberships. The libraries
share one feature list (checked).

Reads .cache/hormann/geo/GSM*_{barcodes,features,matrix}; writes
.cache/hormann/combined/{matrix.mtx.gz, features.tsv.gz, barcodes.tsv.gz}.

Usage:
    uv run python projects/hormann_2020/combine_matrices.py
"""

from __future__ import annotations

import gzip
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GEO = REPO_ROOT / ".cache" / "hormann" / "geo"
OUT = REPO_ROOT / ".cache" / "hormann" / "combined"


def _header(path: Path) -> tuple[str, int, int, int]:
    """(banner, genes, cells, entries) of a MatrixMarket coordinate file."""
    with gzip.open(path, "rt") as fh:
        banner = fh.readline()
        line = fh.readline()
        while line.startswith("%"):
            line = fh.readline()
        g, c, n = map(int, line.split())
    return banner, g, c, n


def main() -> None:
    libs = sorted({re.match(r"(GSM\d+_.+)_matrix\.mtx\.gz", p.name).group(1)
                   for p in GEO.glob("GSM*_matrix.mtx.gz")})
    features = {gzip.decompress((GEO / f"{lib}_features.tsv.gz").read_bytes()) for lib in libs}
    assert len(features) == 1, "libraries differ in their features"
    heads = {lib: _header(GEO / f"{lib}_matrix.mtx.gz") for lib in libs}
    n_genes = {h[1] for h in heads.values()}
    assert len(n_genes) == 1
    banner = heads[libs[0]][0]
    n_cells = sum(h[2] for h in heads.values())
    n_entries = sum(h[3] for h in heads.values())
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "features.tsv.gz").write_bytes(gzip.compress(features.pop()))
    offset = 0
    with gzip.open(OUT / "matrix.mtx.gz", "wt", compresslevel=6) as mo, \
            gzip.open(OUT / "barcodes.tsv.gz", "wt") as bo:
        mo.write(banner)
        mo.write(f"{n_genes.pop()} {n_cells} {n_entries}\n")
        for lib in libs:
            title = lib.split("_", 1)[1]                 # e.g. 24h_APF_1
            with gzip.open(GEO / f"{lib}_barcodes.tsv.gz", "rt") as fh:
                for b in fh:
                    bo.write(f"{title}_{b.strip()}\n")
            with gzip.open(GEO / f"{lib}_matrix.mtx.gz", "rt") as fh:
                line = fh.readline()
                while line.startswith("%"):
                    line = fh.readline()                 # the size line follows the comments
                for line in fh:
                    g, c, v = line.split()
                    mo.write(f"{g} {int(c) + offset} {v}\n")
            offset += heads[lib][2]
    print(f"wrote {len(libs)} libraries: {n_cells} cells x {heads[libs[0]][1]} features, "
          f"{n_entries} entries -> {OUT}")


if __name__ == "__main__":
    main()
