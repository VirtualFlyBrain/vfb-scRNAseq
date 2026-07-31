#!/usr/bin/env python
"""Collate per-cluster fbbt_mapping.json files into a reviewable mapping.tsv.

Generic across projects: the named/placeholder/held classification is driven by
the project's config.yaml (`unidentified` section) via vfb_scrnaseq.project_config.

Usage:
    uv run python scripts/collate_mapping.py --project kurmangaliyev_2020
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vfb_scrnaseq.project_config import (  # noqa: E402
    hold_classes,
    load_config,
    unidentified_classifier,
)

COLUMNS = [
    "cluster_label", "type", "class", "cell_number", "kind",
    "fbbt_id", "fbbt_label", "match_type", "confidence",
    "new_term_needed", "verification_needed", "n_other_candidates", "recommendation",
    "manual_edit", "reviewed", "review_notes",
]


def _manual_edit_summary(m: dict) -> str:
    me = m.get("manual_edit")
    if not me:
        return ""
    return f"{me.get('by', '?')}@{me.get('date', '?')}: {me.get('change') or me.get('reason', '')}".strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    cfg = load_config(args.project)
    is_unidentified = unidentified_classifier(args.project, cfg)
    held = hold_classes(cfg)

    def kind_of(label: str, cls: str) -> str:
        if cls in held:
            return "held"
        if is_unidentified(label, cls):
            return "placeholder"
        return "named"

    proj = REPO_ROOT / "projects" / args.project
    anns = json.loads((proj / "cell_type_annotations.json").read_text())["annotations"]

    rows = []
    for ann in anns:
        label, cls = ann["label"], ann.get("class", "")
        kind = kind_of(label, cls)
        mfile = proj / "mapping" / f"{label}.fbbt_mapping.json"
        m = json.loads(mfile.read_text()) if mfile.exists() else {}
        bm = m.get("best_match") or {}
        rows.append({
            "cluster_label": label,
            "type": ann.get("type", ""),
            "class": cls,
            "cell_number": ann.get("cell_number", ""),
            "kind": kind,
            "fbbt_id": bm.get("fbbt_id", ""),
            "fbbt_label": bm.get("fbbt_term", ""),
            "match_type": bm.get("match_type", "HELD" if kind == "held" else "pending" if not m else "no match"),
            "confidence": bm.get("confidence", ""),
            "new_term_needed": m.get("new_term_needed", ""),
            "verification_needed": m.get("verification_needed", ""),
            "n_other_candidates": len(m.get("other_candidates", [])),
            "recommendation": " ".join(m.get("recommendation", "").split()),
            "manual_edit": _manual_edit_summary(m),
            "reviewed": "",
            "review_notes": "",
        })

    kind_order = {"named": 0, "placeholder": 1, "held": 2}
    order = {"exact match": 0, "narrow match": 1, "broad match": 2, "no match": 3, "pending": 4, "HELD": 5}
    conf = {"high": 0, "medium": 1, "low": 2, "": 3}
    rows.sort(key=lambda r: (kind_order.get(r["kind"], 9), order.get(r["match_type"], 9),
                             conf.get(r["confidence"], 9), r["cluster_label"]))

    out = proj / "mapping.tsv"
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
