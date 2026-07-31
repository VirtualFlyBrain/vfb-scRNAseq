#!/usr/bin/env python
"""Verify every assigned FBbt term against the current FBbt release (via OLS).

For each mapping/*.fbbt_mapping.json best_match (and placeholder anchors), look up
the recorded fbbt_id in the live OLS FBbt and confirm it is (a) found, (b) not
obsolete, and (c) still carries the label we recorded. Catches ontology drift —
renamed/obsoleted/re-IDed terms — deterministically, so a mapping set can be
re-certified against any FBbt release (e.g. the 2026-06-11 release that fixed the
Dm8 rename). Does NOT re-run the LLM judgement; it certifies term validity only.

Usage:
    uv run python scripts/verify_mappings.py --project kurmangaliyev_2020
Exit code 1 if any term fails verification.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OLS_SEARCH = "https://www.ebi.ac.uk/ols4/api/search"


def lookup(curie: str) -> dict | None:
    q = urllib.parse.urlencode({
        "q": curie, "ontology": "fbbt", "queryFields": "obo_id",
        "fieldList": "obo_id,label,is_obsolete", "exact": "true", "rows": 5,
    })
    req = urllib.request.Request(f"{OLS_SEARCH}?{q}", headers={"User-Agent": "vfb-scrnaseq/0.0"})
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310
        docs = json.load(r).get("response", {}).get("docs", [])
    for doc in docs:
        if doc.get("obo_id") == curie:
            return doc
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    mdir = REPO_ROOT / "projects" / args.project / "mapping"
    # unique (fbbt_id -> recorded_label), with the clusters that use each
    terms: dict[str, dict] = {}
    for f in sorted(mdir.glob("*.fbbt_mapping.json")):
        m = json.loads(f.read_text())
        bm = m.get("best_match") or {}
        fid = bm.get("fbbt_id")
        if not fid:
            continue
        terms.setdefault(fid, {"recorded_label": bm.get("fbbt_term", ""), "clusters": []})
        terms[fid]["clusters"].append(m["cluster_label"])

    print(f"verifying {len(terms)} distinct FBbt terms across "
          f"{sum(len(t['clusters']) for t in terms.values())} clusters against live OLS FBbt\n")

    problems = []
    for fid, info in sorted(terms.items()):
        doc = lookup(fid)
        if doc is None:
            problems.append((fid, "NOT FOUND in current FBbt", info))
        elif doc.get("is_obsolete"):
            problems.append((fid, f"OBSOLETE (label: {doc.get('label')})", info))
        elif doc.get("label") != info["recorded_label"]:
            problems.append((fid, f"LABEL CHANGED: recorded {info['recorded_label']!r} -> current {doc.get('label')!r}", info))

    if not problems:
        print(f"OK — all {len(terms)} terms current, non-obsolete, labels match.")
        return 0

    print(f"{len(problems)} PROBLEM(S):")
    for fid, msg, info in problems:
        ex = ", ".join(info["clusters"][:6]) + ("..." if len(info["clusters"]) > 6 else "")
        print(f"  {fid}: {msg}")
        print(f"     used by: {ex}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
