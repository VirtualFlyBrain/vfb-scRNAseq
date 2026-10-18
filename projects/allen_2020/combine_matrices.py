#!/usr/bin/env python
"""Allen 2020: one count matrix from the four GEO DGE matrices.

GEO (GSE141807) has a dense Drop-seq DGE matrix (gene symbol x cell barcode, raw UMI
counts) per library; each author cluster spans all four libraries, so the expression
build reads one sparse matrix with the libraries side by side, over the union of their
genes. Only the cells clustered (in .cache/allen/memberships.tsv.gz, from
build_clusters.py) are kept. Cells are named <Sex>_rep<n>_<barcode> (e.g.
Female_rep1_TCAGGTATCGTGACAT), as in the memberships.

Reads .cache/allen/InputFiles/GSM*_<sex>_rep<n>_dge.txt.gz; writes
.cache/allen/combined/{matrix.mtx.gz, features.tsv.gz, barcodes.tsv.gz}
(features: symbol<TAB>symbol; the DGEs carry symbols only).

Usage:
    uv run python projects/allen_2020/combine_matrices.py
"""

from __future__ import annotations

import csv
import gzip
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE = REPO_ROOT / ".cache" / "allen"
OUT = CACHE / "combined"


def main() -> None:
    with gzip.open(CACHE / "memberships.tsv.gz", "rt") as fh:
        wanted = {r["barcode"] for r in csv.DictReader(fh, delimiter="\t")}
    genes: dict[str, int] = {}
    cells: list[str] = []
    entries: list[tuple[int, int, str]] = []
    for path in sorted(CACHE.glob("InputFiles/GSM*_dge.txt.gz")):
        sex, rep = re.match(r"GSM\d+_(female|male)_(rep\d)_dge", path.name).groups()
        prefix = f"{sex.capitalize()}_{rep}_"
        with gzip.open(path, "rt") as fh:
            header = fh.readline().rstrip("\n").split("\t")[1:]
            keep = [(i, len(cells) + k) for k, i in
                    enumerate(i for i, b in enumerate(header) if prefix + b in wanted)]
            cells += [prefix + header[i] for i, _ in keep]
            for line in fh:
                row = line.rstrip("\n").split("\t")
                g = genes.setdefault(row[0], len(genes))
                vals = row[1:]
                entries += [(g, c, vals[i]) for i, c in keep if vals[i] != "0"]
    missing = wanted - set(cells)
    if missing:
        raise SystemExit(f"{len(missing)} clustered cells not in the DGE matrices, e.g. {sorted(missing)[:3]}")
    OUT.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT / "features.tsv.gz", "wt") as fh:
        fh.writelines(f"{g}\t{g}\n" for g in genes)
    with gzip.open(OUT / "barcodes.tsv.gz", "wt") as fh:
        fh.writelines(f"{c}\n" for c in cells)
    with gzip.open(OUT / "matrix.mtx.gz", "wt", compresslevel=6) as fh:
        fh.write("%%MatrixMarket matrix coordinate integer general\n")
        fh.write(f"{len(genes)} {len(cells)} {len(entries)}\n")
        fh.writelines(f"{g + 1} {c + 1} {v}\n" for g, c, v in entries)
    print(f"wrote {len(cells)} cells x {len(genes)} genes, {len(entries)} entries -> {OUT}")


if __name__ == "__main__":
    main()
