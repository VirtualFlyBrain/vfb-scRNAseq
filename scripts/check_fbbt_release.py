#!/usr/bin/env python
"""Re-verify all FBbt mappings only when a new FBbt release is out.

Reads the FBbt release last verified from `checks/fbbt_last_checked.json` and asks
OLS for the current FBbt release. If it is the same, exits 0 without checking terms.
If it is new (or nothing is recorded), runs `verify_mappings.verify` for every project
with mappings; when every term is current, non-obsolete and still carries its recorded
label, the record is updated to the new release. If any term fails, the record is NOT
updated (so the next run re-checks) and the exit code is 1.

Usage:
    uv run python scripts/check_fbbt_release.py [--force]
Writes `checked=true|false` and `updated=true|false` to $GITHUB_OUTPUT when set.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RECORD = REPO_ROOT / "checks" / "fbbt_last_checked.json"
OLS_FBBT = "https://www.ebi.ac.uk/ols4/api/ontologies/fbbt"


def current_release() -> dict:
    req = urllib.request.Request(OLS_FBBT, headers={"User-Agent": "vfb-scrnaseq/0.0"})
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
        cfg = json.load(r)["config"]
    return {"version": cfg.get("version"), "version_iri": cfg.get("versionIri")}


def _verify_module():
    spec = importlib.util.spec_from_file_location(
        "verify_mappings", REPO_ROOT / "scripts" / "verify_mappings.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _output(**kv) -> None:
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            fh.writelines(f"{k}={str(v).lower()}\n" for k, v in kv.items())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="verify even if the release is unchanged")
    args = ap.parse_args()

    record = json.loads(RECORD.read_text()) if RECORD.exists() else {}
    rel = current_release()
    if not rel["version"]:
        print("could not read the current FBbt version from OLS")
        return 1
    if rel["version"] == record.get("version") and not args.force:
        print(f"FBbt {rel['version']} already verified on {record.get('checked_at')}; nothing to do")
        _output(checked=False, updated=False)
        return 0

    print(f"FBbt {rel['version']} (last verified: {record.get('version') or 'never'}) — verifying all mappings")
    verify = _verify_module().verify
    projects = sorted(p.parent.name for p in (REPO_ROOT / "projects").glob("*/mapping"))
    results, failed = {}, False
    for project in projects:
        terms, problems = verify(project)
        results[project] = {"terms": len(terms), "problems": len(problems)}
        print(f"  {project}: {len(terms)} terms, {len(problems)} problem(s)")
        for fid, msg, info in problems:
            ex = ", ".join(info["clusters"][:6]) + ("..." if len(info["clusters"]) > 6 else "")
            print(f"    {fid}: {msg}  [used by: {ex}]")
        failed |= bool(problems)

    if failed:
        print("\nSome FBbt terms need attention; record not updated (next run re-checks).")
        _output(checked=True, updated=False)
        return 1

    RECORD.parent.mkdir(exist_ok=True)
    RECORD.write_text(json.dumps({
        "version": rel["version"],
        "version_iri": rel["version_iri"],
        "checked_at": dt.date.today().isoformat(),
        "source": OLS_FBBT,
        "projects": results,
    }, indent=2) + "\n")
    print(f"\nAll terms OK; recorded FBbt {rel['version']} in {RECORD}")
    _output(checked=True, updated=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
