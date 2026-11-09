#!/usr/bin/env python
"""Verify every assigned FBbt term against the current FBbt release (via OLS).

For each mapping/*.fbbt_mapping.json best_match and additional_matches (and
placeholder anchors), look up
the recorded fbbt_id in the live OLS FBbt (or, given `terms` from
`release_terms`, in one downloaded FBbt release file) and confirm it is (a) found, (b) not
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
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OLS_SEARCH = "https://www.ebi.ac.uk/ols4/api/search"
RELEASE_OBO = "http://purl.obolibrary.org/obo/fbbt/releases/{version}/fbbt-simple.obo"
RETRY_DELAYS = (5, 15, 45)   # seconds before each retry


def urlopen_retry(req, timeout: float = 30):
    """urllib.request.urlopen, retried on server errors (5xx, 429), timeouts and dropped connections.

    OLS sometimes returns a 500 for one request in hundreds; a retry gets through.
    Client errors (other 4xx) are raised at once.
    """
    for delay in (*RETRY_DELAYS, None):
        try:
            return urllib.request.urlopen(req, timeout=timeout)  # noqa: S310
        except urllib.error.HTTPError as e:
            if delay is None or not (e.code >= 500 or e.code == 429):
                raise
            err = f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if delay is None:
                raise
            err = str(e)
        url = req.full_url if isinstance(req, urllib.request.Request) else req
        print(f"  {err} from {url.split('?')[0]}; retrying in {delay}s", file=sys.stderr)
        time.sleep(delay)


def release_terms(version: str) -> dict[str, dict]:
    """{FBbt id: {obo_id, label, is_obsolete}} for every term in one FBbt release, from one download.

    Reads the release's fbbt-simple.obo (obsolete terms included) from its versioned
    PURL, so the terms checked are exactly that release's.
    """
    url = RELEASE_OBO.format(version=version)
    req = urllib.request.Request(url, headers={"User-Agent": "vfb-scrnaseq/0.0"})
    with urlopen_retry(req, timeout=300) as r:
        text = r.read().decode("utf-8")
    head = text[:2000]
    if f"releases/{version}/" not in head:
        raise ValueError(f"{url} is not FBbt {version}: {head.splitlines()[:3]}")
    terms = {}
    for block in text.split("\n[Term]\n")[1:]:
        block = block.split("\n[", 1)[0]
        tid = re.search(r"^id: (\S+)", block, re.M)
        name = re.search(r"^name: (.*)$", block, re.M)
        if tid and name:
            terms[tid.group(1)] = {"obo_id": tid.group(1), "label": name.group(1),
                                   "is_obsolete": bool(re.search(r"^is_obsolete: true", block, re.M))}
    return terms


def lookup(curie: str) -> dict | None:
    q = urllib.parse.urlencode({
        "q": curie, "ontology": "fbbt", "queryFields": "obo_id",
        "fieldList": "obo_id,label,is_obsolete", "exact": "true", "rows": 5,
    })
    req = urllib.request.Request(f"{OLS_SEARCH}?{q}", headers={"User-Agent": "vfb-scrnaseq/0.0"})
    with urlopen_retry(req, timeout=30) as r:
        docs = json.load(r).get("response", {}).get("docs", [])
    for doc in docs:
        if doc.get("obo_id") == curie:
            return doc
    return None


def verify(project: str, terms: dict[str, dict] | None = None) -> tuple[dict, list]:
    """Check every FBbt term a project's mappings use against live OLS FBbt.

    With `terms` (from `release_terms`), check against those instead of querying OLS
    once per term.

    Returns (terms, problems): terms = {fbbt_id: {recorded_label, clusters}},
    problems = [(fbbt_id, message, info)] for missing / obsolete / relabelled terms.
    """
    mdir = REPO_ROOT / "projects" / project / "mapping"
    # unique (fbbt_id -> recorded_label), with the clusters that use each
    release = terms
    terms = {}
    for f in sorted(mdir.glob("*.fbbt_mapping.json")):
        m = json.loads(f.read_text())
        for bm in [m.get("best_match") or {}] + (m.get("additional_matches") or []):
            fid = bm.get("fbbt_id")
            if not fid:
                continue
            terms.setdefault(fid, {"recorded_label": bm.get("fbbt_term", ""), "clusters": []})
            terms[fid]["clusters"].append(m["cluster_label"])

    problems = []
    for fid, info in sorted(terms.items()):
        doc = release.get(fid) if release is not None else lookup(fid)
        if doc is None:
            problems.append((fid, "NOT FOUND in current FBbt", info))
        elif doc.get("is_obsolete"):
            problems.append((fid, f"OBSOLETE (label: {doc.get('label')})", info))
        elif doc.get("label") != info["recorded_label"]:
            problems.append((fid, f"LABEL CHANGED: recorded {info['recorded_label']!r} -> current {doc.get('label')!r}", info))
    return terms, problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    terms, problems = verify(args.project)
    print(f"verifying {len(terms)} distinct FBbt terms across "
          f"{sum(len(t['clusters']) for t in terms.values())} clusters against live OLS FBbt\n")

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
