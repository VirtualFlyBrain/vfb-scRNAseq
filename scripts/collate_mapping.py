#!/usr/bin/env python
"""Collate per-cluster fbbt_mapping.json files into a reviewable mapping.tsv.

Joins each mapping result with the cluster's annotation metadata
(type/class/cell_number from cell_type_annotations.json) and writes a flat TSV
with a blank ``reviewed`` column for human curation.

Usage:
    python scripts/collate_mapping.py --project kurmangaliyev_2020
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

COLUMNS = [
    "cluster_label", "type", "class", "cell_number",
    "fbbt_id", "fbbt_label", "match_type", "confidence",
    "new_term_needed", "verification_needed", "n_other_candidates", "recommendation",
    "reviewed", "review_notes",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    proj = REPO_ROOT / "projects" / args.project
    anns = {a["label"]: a for a in json.loads((proj / "cell_type_annotations.json").read_text())["annotations"]}

    rows = []
    for f in sorted((proj / "mapping").glob("*.fbbt_mapping.json")):
        m = json.loads(f.read_text())
        label = m["cluster_label"]
        ann = anns.get(label, {})
        bm = m.get("best_match") or {}
        rows.append({
            "cluster_label": label,
            "type": ann.get("type", ""),
            "class": ann.get("class", ""),
            "cell_number": ann.get("cell_number", ""),
            "fbbt_id": bm.get("fbbt_id", ""),
            "fbbt_label": bm.get("fbbt_term", ""),
            "match_type": bm.get("match_type", "no match"),
            "confidence": bm.get("confidence", ""),
            "new_term_needed": m.get("new_term_needed", ""),
            "verification_needed": m.get("verification_needed", ""),
            "n_other_candidates": len(m.get("other_candidates", [])),
            "recommendation": " ".join(m.get("recommendation", "").split()),
            "reviewed": "",
            "review_notes": "",
        })

    # order: exact matches first, then broad/narrow, then no-match; high conf first
    order = {"exact match": 0, "narrow match": 1, "broad match": 2, "no match": 3}
    conf = {"high": 0, "medium": 1, "low": 2, "": 3}
    rows.sort(key=lambda r: (order.get(r["match_type"], 9), conf.get(r["confidence"], 9), r["cluster_label"]))

    out = proj / "mapping.tsv"
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
