#!/usr/bin/env python
"""Check each project's committed mapping.tsv matches what collate_mapping.py produces.

Catches a mapping JSON (or config / annotations) edited without re-running
`collate_mapping.py`, which would leave the review table stale. Compares parsed rows,
so line endings don't matter. Writes nothing.

Usage:
    uv run python scripts/check_mapping_tsv.py [--skip PROJECT ...]   # exit 1 if stale
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _collate_module():
    spec = importlib.util.spec_from_file_location(
        "collate_mapping", REPO_ROOT / "scripts" / "collate_mapping.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check(project: str, collate) -> list[str]:
    """Return human-readable differences between committed and regenerated rows."""
    with (REPO_ROOT / "projects" / project / "mapping.tsv").open() as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        old_cols, old_rows = reader.fieldnames, list(reader)
    cols, rows = collate(project)
    new_rows = [{c: str(r.get(c, "")) for c in cols} for r in rows]
    diffs = []
    if old_cols != cols:
        diffs.append(f"columns differ:\n      committed {old_cols}\n      expected  {cols}")
        return diffs
    old_by = {r["cluster_label"]: r for r in old_rows}
    new_by = {r["cluster_label"]: r for r in new_rows}
    for lab in sorted(set(old_by) - set(new_by)):
        diffs.append(f"{lab}: in mapping.tsv but no longer a cluster")
    for lab in sorted(set(new_by) - set(old_by)):
        diffs.append(f"{lab}: missing from mapping.tsv")
    for lab in sorted(set(old_by) & set(new_by)):
        for c in cols:
            if old_by[lab][c] != new_by[lab][c]:
                diffs.append(f"{lab}: {c} committed {old_by[lab][c]!r} expected {new_by[lab][c]!r}")
    if not diffs and [r["cluster_label"] for r in old_rows] != [r["cluster_label"] for r in new_rows]:
        diffs.append("row order differs")
    return diffs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip", nargs="*", default=[], help="projects not checked (yet)")
    args = ap.parse_args()

    collate = _collate_module().collate
    projects = sorted(p.parent.name for p in (REPO_ROOT / "projects").glob("*/mapping.tsv"))
    stale = {}
    for project in projects:
        if project in args.skip:
            print(f"  skip  {project}")
            continue
        diffs = check(project, collate)
        print(f"  {'STALE' if diffs else 'ok   '} {project}")
        if diffs:
            stale[project] = diffs
    for project, diffs in stale.items():
        print(f"\n{project}: mapping.tsv is out of date ({len(diffs)} difference(s)); "
              f"run: uv run python scripts/collate_mapping.py --project {project}")
        for d in diffs[:20]:
            print(f"    {d}")
        if len(diffs) > 20:
            print(f"    ... {len(diffs) - 20} more")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
