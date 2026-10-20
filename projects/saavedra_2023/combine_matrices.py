#!/usr/bin/env python
"""Saavedra 2023: one count matrix from the two control libraries (GEO).

GEO (GSE227038) has a Cell Ranger 7 filtered matrix per library (MatrixMarket, named
.matrix.tsv.gz); each author cluster spans both control libraries (wt1, wt2), so the
expression build reads one matrix with them side by side. Nuclei are named
<library>_<barcode> (e.g. wt1_AAACCCAAGAGTCAGC-1), as in build_clusters.py's memberships.
The libraries share one feature list (checked).

Reads .cache/saavedra/geo/<library>/{barcodes,features,matrix}.tsv.gz; writes
.cache/saavedra/combined/{matrix.mtx.gz, features.tsv.gz, barcodes.tsv.gz}.

Usage:
    uv run python projects/saavedra_2023/combine_matrices.py
"""

from __future__ import annotations

import gzip
from pathlib import Path

CACHE = Path(__file__).resolve().parents[2] / ".cache" / "saavedra"
LIBS = ("wt1", "wt2")


def main() -> None:
    feats = {gzip.decompress((CACHE / "geo" / lib / "features.tsv.gz").read_bytes()) for lib in LIBS}
    assert len(feats) == 1, "libraries differ in their features"
    heads, bodies = {}, {}
    for lib in LIBS:
        with gzip.open(CACHE / "geo" / lib / "matrix.tsv.gz", "rt") as fh:
            banner = fh.readline()
            line = fh.readline()
            while line.startswith("%"):
                line = fh.readline()
            heads[lib] = (banner, *map(int, line.split()))
    n_genes = {h[1] for h in heads.values()}
    assert len(n_genes) == 1
    out = CACHE / "combined"
    out.mkdir(parents=True, exist_ok=True)
    (out / "features.tsv.gz").write_bytes(gzip.compress(feats.pop()))
    n_cells = sum(h[2] for h in heads.values())
    n_entries = sum(h[3] for h in heads.values())
    offset = 0
    with gzip.open(out / "matrix.mtx.gz", "wt") as mo, gzip.open(out / "barcodes.tsv.gz", "wt") as bo:
        mo.write(heads[LIBS[0]][0])
        mo.write(f"{n_genes.pop()} {n_cells} {n_entries}\n")
        for lib in LIBS:
            with gzip.open(CACHE / "geo" / lib / "barcodes.tsv.gz", "rt") as fh:
                bo.writelines(f"{lib}_{b.strip()}\n" for b in fh)
            with gzip.open(CACHE / "geo" / lib / "matrix.tsv.gz", "rt") as fh:
                line = fh.readline()
                while line.startswith("%"):
                    line = fh.readline()              # the size line follows the comments
                for line in fh:
                    g, c, v = line.split()
                    mo.write(f"{g} {int(c) + offset} {v}\n")
            offset += heads[lib][2]
    print(f"wrote {len(LIBS)} libraries: {n_cells} nuclei, {n_entries} entries -> {out}")


if __name__ == "__main__":
    main()
