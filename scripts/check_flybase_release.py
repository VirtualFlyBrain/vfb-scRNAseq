#!/usr/bin/env python
"""Weekly: when FlyBase has a newer release than the gene id maps, open a reminder issue.

Reads the current FlyBase release from flybase.org and the release recorded in each
`projects/*/gene_id_map.tsv` header. If FlyBase is newer, re-classifies every project's
input gene ids (or, for h5ad projects, symbols without ids) against FlyBase Chado
(the committed map already lists them, so no source files are needed) and compares with the committed map. If any gene id or symbol used
by the expression output has changed, it opens an issue in this repo with the counts
and the commands to run (`update_gene_ids.py`, `build_expression.py`, `build_rdf.py`); if nothing
changed, it records the release without an issue. If Chado can't be reached, the
issue is still opened, without counts.

Each release is handled once: `checks/flybase_release_check.json` records the last
release checked.

Usage:
    uv run python scripts/check_flybase_release.py [--dry-run]
Writes `changed=true|false` (checks/ record changed) to $GITHUB_OUTPUT when set.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RECORD = REPO_ROOT / "checks" / "flybase_release_check.json"


def _script(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _output(**kv) -> None:
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            fh.writelines(f"{k}={str(v).lower()}\n" for k, v in kv.items())


def compare(old: list[dict], new: list[dict]) -> dict:
    """Changes between a committed map and a re-classification of the same ids."""
    nb = {(r["input_fbgn"], r["input_symbol"]): r for r in new}
    ids, symbols, examples = 0, 0, []
    for r in old:
        n = nb.get((r["input_fbgn"], r["input_symbol"]))
        if n is None:
            continue
        if (n["status"], n["current_fbgn"]) != (r["status"], r["current_fbgn"]):
            ids += 1
            if len(examples) < 5:
                examples.append(f"{r['input_fbgn'] or 'symbol'} ({r['input_symbol']}): {r['status']} "
                                f"{r['current_fbgn'] or '-'} -> {n['status']} {n['current_fbgn'] or '-'}")
        elif n["current_symbol"] != r["current_symbol"]:
            symbols += 1
    return {"ids": ids, "symbols": symbols, "examples": examples}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print the issue instead of opening it")
    args = ap.parse_args()

    ug = _script("update_gene_ids")
    open_issue = _script("check_fbbt_release").open_issue
    full = ug.flybase_release()
    m = re.match(r"(FB\d{4}_\d{2})", full)
    if not m:
        print("could not read the FlyBase release from flybase.org")
        _output(changed=False)
        return 1
    release = m.group(1)
    maps = sorted(REPO_ROOT.glob("projects/*/gene_id_map.tsv"))
    behind = {p.parent.name: ug.map_release(p) for p in maps if ug.map_release(p) != release}
    record = json.loads(RECORD.read_text()) if RECORD.exists() else {}
    if not behind or record.get("release") == release:
        print(f"FlyBase {full}: gene id maps {'current' if not behind else 'already reported'}; nothing to do")
        _output(changed=False)
        return 0

    print(f"FlyBase {full}; gene id maps at: {behind}")
    results, chado_ok = {}, True
    for p in maps:
        project = p.parent.name
        if project not in behind:
            continue
        _, old = ug.read_map(p)
        try:
            new = ug.reclassify([(r["input_fbgn"], r["input_symbol"]) for r in old])
        except Exception as e:  # noqa: BLE001 - Chado unreachable / psql missing
            print(f"  {project}: Chado query failed ({type(e).__name__}: {str(e)[:120]})")
            chado_ok = False
            break
        results[project] = compare(old, new)
        print(f"  {project}: {results[project]['ids']} id change(s), {results[project]['symbols']} symbol change(s)")

    changes = sum(r["ids"] + r["symbols"] for r in results.values())
    issue = None
    if not chado_ok or changes:
        lines = [f"FlyBase **{full}** is newer than the gene id maps "
                 f"({', '.join(f'`{k}`: {v or 'unrecorded'}' for k, v in behind.items())}).", ""]
        if chado_ok:
            lines += ["Gene ids used by the expression output that changed:", ""]
            for project, r in results.items():
                lines.append(f"- `{project}`: {r['ids']} id change(s) (remap/split/withdrawn), "
                             f"{r['symbols']} symbol change(s)")
                lines += [f"  - {ex}" for ex in r["examples"]]
        else:
            lines += ["Chado could not be queried from CI, so the number of changed ids is unknown."]
        lines += ["", "To update (needs `psql` access to chado.flybase.org and the source files in `.cache/`):",
                  "```sh"]
        for project in behind:
            lines += [f"uv run python scripts/update_gene_ids.py  --project {project}",
                      f"uv run python scripts/build_expression.py --project {project}",
                      f"uv run python scripts/build_rdf.py        --project {project}"]
        lines += ["```", "Then update the projects' provenance and open a PR.",
                  "", "_Opened automatically by the weekly release check._"]
        issue = open_issue(f"Update gene ids to FlyBase {release}", "\n".join(lines), args.dry_run)
        print(f"  -> {issue}")
    else:
        print("  no gene id or symbol used by the expression output changed; no issue")

    if not args.dry_run:
        RECORD.parent.mkdir(exist_ok=True)
        RECORD.write_text(json.dumps({"release": release, "release_text": full,
                                      "checked_at": dt.date.today().isoformat(),
                                      "chado_queried": chado_ok, "changes": results,
                                      "issue": issue}, indent=2) + "\n")
        _output(changed=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
