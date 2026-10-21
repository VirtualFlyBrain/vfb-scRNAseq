#!/usr/bin/env python
"""Baker 2021: one count matrix from the four sucrose (control) libraries (GEO).

GEO (GSE152495) has a Cell Ranger filtered matrix per library; each author cluster spans
the four sucrose (control) libraries, so the expression build reads one matrix with them side by side. Cells are named
<GEO sample dir>_<barcode> (e.g. 1_S1_L001_AAACCCAAGCACCGAA-1), as in build_clusters.py's
memberships.
The libraries share one feature list (checked).

Reads .cache/baker/geo/<sample dir>/{barcodes,features}.tsv.gz + matrix.mtx.gz; writes
.cache/baker/combined/{matrix.mtx.gz, features.tsv.gz, barcodes.tsv.gz}.

Usage:
    uv run python projects/baker_2021/combine_matrices.py
"""

from __future__ import annotations

import gzip
from pathlib import Path

CACHE = Path(__file__).resolve().parents[2] / ".cache" / "baker"
LIBS = ('1_S1_L001', '2_S2_L001', '3_S3_L001', '4_S4_L001')


def main() -> None:
    feats = {gzip.decompress((CACHE / "geo" / lib / "features.tsv.gz").read_bytes()) for lib in LIBS}
    assert len(feats) == 1, "libraries differ in their features"
    heads, bodies = {}, {}
    for lib in LIBS:
        with gzip.open(CACHE / "geo" / lib / "matrix.mtx.gz", "rt") as fh:
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
            with gzip.open(CACHE / "geo" / lib / "matrix.mtx.gz", "rt") as fh:
                line = fh.readline()
                while line.startswith("%"):
                    line = fh.readline()              # the size line follows the comments
                for line in fh:
                    g, c, v = line.split()
                    mo.write(f"{g} {int(c) + offset} {v}\n")
            offset += heads[lib][2]
    print(f"wrote {len(LIBS)} libraries: {n_cells} cells, {n_entries} entries -> {out}")


if __name__ == "__main__":
    main()
