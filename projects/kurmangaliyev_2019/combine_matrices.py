#!/usr/bin/env python
"""Kurmangaliyev 2019: one count matrix from the two GEO libraries.

GEO (GSE126139) has a CellRanger 2 matrix per library (barcodes / genes / matrix); the
expression build reads one matrix, so the libraries go side by side, cells named
<stage>_<10x barcode> (e.g. 24h_AAACCTGAGATAGTCA-1) as in build_clusters.py's
memberships. Both libraries share one gene list (checked).

Reads .cache/kurmangaliyev_2019/geo/GSM*_T4T5_<n>_{barcodes,genes,matrix}; writes
.cache/kurmangaliyev_2019/combined/{matrix.mtx.gz, features.tsv.gz, barcodes.tsv.gz}.

Usage:
    uv run python projects/kurmangaliyev_2019/combine_matrices.py
"""

from __future__ import annotations

import gzip
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GEO = REPO_ROOT / ".cache" / "kurmangaliyev_2019" / "geo"
OUT = REPO_ROOT / ".cache" / "kurmangaliyev_2019" / "combined"
LIBRARIES = {"24h": "GSM3592259_T4T5_24", "48h": "GSM3592260_T4T5_48"}


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
    genes = {gzip.decompress((GEO / f"{lib}_genes.tsv.gz").read_bytes()) for lib in LIBRARIES.values()}
    assert len(genes) == 1, "libraries differ in their genes"
    heads = {lib: _header(GEO / f"{lib}_matrix.mtx.gz") for lib in LIBRARIES.values()}
    n_genes = {h[1] for h in heads.values()}
    assert len(n_genes) == 1
    banner = next(iter(heads.values()))[0]
    n_cells = sum(h[2] for h in heads.values())
    n_entries = sum(h[3] for h in heads.values())
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "features.tsv.gz").write_bytes(gzip.compress(genes.pop()))
    offset = 0
    with gzip.open(OUT / "matrix.mtx.gz", "wt", compresslevel=6) as mo, \
            gzip.open(OUT / "barcodes.tsv.gz", "wt") as bo:
        mo.write(banner)
        mo.write(f"{n_genes.pop()} {n_cells} {n_entries}\n")
        for stage, lib in LIBRARIES.items():
            with gzip.open(GEO / f"{lib}_barcodes.tsv.gz", "rt") as fh:
                for b in fh:
                    bo.write(f"{stage}_{b.strip()}\n")
            with gzip.open(GEO / f"{lib}_matrix.mtx.gz", "rt") as fh:
                line = fh.readline()
                while line.startswith("%"):
                    line = fh.readline()                 # the size line follows the comments
                for line in fh:
                    g, c, v = line.split()
                    mo.write(f"{g} {int(c) + offset} {v}\n")
            offset += heads[lib][2]
    print(f"wrote {len(LIBRARIES)} libraries: {n_cells} cells x {next(iter(heads.values()))[1]} genes, "
          f"{n_entries} entries -> {OUT}")


if __name__ == "__main__":
    main()
