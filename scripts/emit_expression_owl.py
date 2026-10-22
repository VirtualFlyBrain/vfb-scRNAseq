#!/usr/bin/env python
"""Re-emit a project's expression OWL from its committed expression table.

build_expression.py computes the statistics from the count matrices (in .cache) and
emits the OWL from them. When only the OWL rendering changes (the schema's `gene`
template), the committed projects/<p>/expression.tsv(.gz) holds every row the OWL
needs, so this re-emits expression/vfb_scRNAseq_expression_<project>.owl.gz from it
without the matrices.

Usage:
    uv run python scripts/emit_expression_owl.py --project kurmangaliyev_2020
    uv run python scripts/emit_expression_owl.py --all
"""

from __future__ import annotations

import argparse
import csv
import gzip
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vfb_scrnaseq.emit import emit_expression_owl  # noqa: E402
from vfb_scrnaseq.project_config import load_config  # noqa: E402


def expression_table(project: str) -> Path | None:
    proj = REPO_ROOT / "projects" / project
    for name in ("expression.tsv", "expression.tsv.gz"):
        if (proj / name).exists():
            return proj / name
    return None


def read_rows(tsv: Path) -> list[tuple]:
    opener = gzip.open if tsv.suffix == ".gz" else open
    with opener(tsv, "rt", encoding="utf-8", newline="") as fh:
        r = csv.reader(fh, delimiter="\t")
        next(r)                                   # header
        return [tuple(row) for row in r]


def emit(project: str) -> None:
    cfg = load_config(project)
    tsv = expression_table(project)
    if tsv is None:
        raise SystemExit(f"{project}: no expression.tsv(.gz); run build_expression.py")
    rows = read_rows(tsv)
    hide = str(cfg["expression"].get("hide_in_terminfo", "true"))
    out = emit_expression_owl(rows, REPO_ROOT / "expression" / f"vfb_scRNAseq_expression_{project}.owl.gz",
                              hide=hide)
    print(f"{project}: {len(rows):,} rows -> {out.relative_to(REPO_ROOT)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--project")
    g.add_argument("--all", action="store_true", help="every project with an expression table")
    args = ap.parse_args()
    projects = ([args.project] if args.project else
                sorted(p.name for p in (REPO_ROOT / "projects").iterdir() if expression_table(p.name)))
    for p in projects:
        emit(p)


if __name__ == "__main__":
    main()
