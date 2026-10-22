#!/usr/bin/env python
"""Write expression/FBgn_list.txt: every gene in the projects' expression output.

VFB's scRNAseq gene ontology (VirtualFlyBrain/vfb-scRNAseq-gene-annotations) builds
its Gene classes, with their gene-group and GO function labels, from a list of the
FBgns used by the scRNAseq expression data; VFB's cluster / gene queries need each
expressed gene to be one of them. One FBgn per line, sorted, from every
projects/<p>/expression.tsv(.gz).

Usage:
    uv run python scripts/write_fbgn_list.py           # write
    uv run python scripts/write_fbgn_list.py --check   # fail if it is out of date (CI)
"""

from __future__ import annotations

import argparse
import csv
import gzip
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "expression" / "FBgn_list.txt"


def fbgns() -> list[str]:
    genes: set[str] = set()
    for tsv in sorted((REPO_ROOT / "projects").glob("*/expression.tsv*")):
        opener = gzip.open if tsv.suffix == ".gz" else open
        with opener(tsv, "rt", encoding="utf-8", newline="") as fh:
            # genes only: an FBti (transposable-element insertion) is not a VFB Gene
            genes.update(row["fbgn"] for row in csv.DictReader(fh, delimiter="\t")
                         if row["fbgn"].startswith("FBgn"))
    return sorted(genes)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    text = "".join(f"{g}\n" for g in fbgns())
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            sys.exit(f"{OUT.relative_to(REPO_ROOT)} is out of date: run scripts/write_fbgn_list.py")
        print(f"{OUT.relative_to(REPO_ROOT)} up to date ({text.count(chr(10))} genes)")
        return
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(REPO_ROOT)} ({text.count(chr(10))} genes)")


if __name__ == "__main__":
    main()
