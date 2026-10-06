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
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vfb_scrnaseq.project_config import (  # noqa: E402
    annotation_kind,
    label_slug,
    load_config,
)

COLUMNS = [
    "cluster_label", "type", "class", "cell_number", "kind",
    "fbbt_id", "fbbt_label", "match_type", "confidence",
    "new_term_needed", "verification_needed", "n_other_candidates", "recommendation",
    "manual_edit", "reviewed", "review_notes",
]


PRIOR_COLUMNS = ["prior_fbbt_id", "prior_fbbt_label", "prior_agrees"]


def _load_prior(proj: Path, cfg: dict) -> dict[str, tuple[str, str]] | None:
    """Optional `prior_mapping` TSV (cluster_label, old_fbbt_id, old_fbbt_label): the
    FBbt terms of a previous load of this dataset, used only as a cross-check."""
    name = cfg.get("prior_mapping")
    if not name:
        return None
    with (proj / name).open() as fh:
        return {r["cluster_label"]: (r["old_fbbt_id"], r["old_fbbt_label"])
                for r in csv.DictReader(fh, delimiter="\t")}


REPORTS_README = REPO_ROOT / "src" / "vfb_scrnaseq" / "templates" / "reports_README.md"


def ensure_reports_readme(proj: Path) -> Path | None:
    """Give a project's reports/ folder the generic README (reports are background
    evidence; mapping.tsv is authoritative) if it has reports but no README yet.
    Never overwrites an existing README. Returns the path written, else None."""
    rdir = proj / "reports"
    readme = rdir / "README.md"
    if readme.exists() or not any(p.name != "README.md" for p in rdir.glob("*.md")):
        return None
    readme.write_text(REPORTS_README.read_text())
    return readme


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
    kind_of = annotation_kind(args.project, cfg)

    proj = REPO_ROOT / "projects" / args.project
    anns = json.loads((proj / "cell_type_annotations.json").read_text())["annotations"]
    prior = _load_prior(proj, cfg)
    # extra per-cluster fields from cell_type_annotations.json shown after the label
    # (`annotations.review_columns`, e.g. the authors' clustering + cluster id)
    source_cols = [c for c in (cfg.get("annotations") or {}).get("review_columns", [])
                   if c not in COLUMNS]
    # keep any review already recorded in an existing mapping.tsv
    out = proj / "mapping.tsv"
    previous = {}
    if out.exists():
        with out.open() as fh:
            previous = {r["cluster_label"]: r for r in csv.DictReader(fh, delimiter="\t")}

    rows = []
    for ann in anns:
        label, cls = ann["label"], ann.get("class", "")
        kind = kind_of(ann)
        mfile = proj / "mapping" / f"{label_slug(label)}.fbbt_mapping.json"
        m = json.loads(mfile.read_text()) if mfile.exists() else {}
        bm = m.get("best_match") or {}
        if kind != "held" and m and not bm:
            kind = "held"   # general rule: a cluster with no FBbt term is held
        rows.append({
            "cluster_label": label,
            "type": ann.get("type", ""),
            "class": cls,
            "cell_number": ann.get("cell_number", ""),
            "kind": kind,
            # best match first, then any additional_matches, " | "-joined
            "fbbt_id": " | ".join(x.get("fbbt_id", "") for x in [bm] + m.get("additional_matches", []) if x),
            "fbbt_label": " | ".join(x.get("fbbt_term", "") for x in [bm] + m.get("additional_matches", []) if x),
            "match_type": bm.get("match_type", "HELD" if kind == "held" else "pending" if not m else "no match"),
            "confidence": bm.get("confidence", ""),
            "new_term_needed": m.get("new_term_needed", ""),
            "verification_needed": m.get("verification_needed", ""),
            "n_other_candidates": len(m.get("other_candidates", [])),
            "recommendation": " ".join(m.get("recommendation", "").split()),
            "manual_edit": _manual_edit_summary(m),
            "reviewed": previous.get(label, {}).get("reviewed", ""),
            "review_notes": previous.get(label, {}).get("review_notes", ""),
        })
        for c in source_cols:
            rows[-1][c] = ann.get(c, "")
        if prior is not None:
            pid, plab = prior.get(label) or prior.get(ann.get("type", ""), ("", ""))
            new = bm.get("fbbt_id", "")
            rows[-1].update({
                "prior_fbbt_id": pid, "prior_fbbt_label": plab,
                # "" = nothing to compare (no prior term, or not yet mapped / held)
                "prior_agrees": ("" if not (pid and new) else "yes" if pid == new else "NO"),
            })

    # stable order: clusters with an FBbt term first (presence, not value), then by
    # cluster label with numbers compared numerically (res2_2 < res2_10)
    rows.sort(key=lambda r: (not r["fbbt_id"], [int(t) if t.isdigit() else t
                                                 for t in re.split(r"(\d+)", r["cluster_label"])]))

    with out.open("w", newline="") as fh:
        cols = COLUMNS[:1] + source_cols + COLUMNS[1:]
        if prior is not None:
            cols = (cols[:cols.index("manual_edit")] + PRIOR_COLUMNS
                    + cols[cols.index("manual_edit"):])
        w = csv.DictWriter(fh, fieldnames=cols, delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows -> {out}")
    if (readme := ensure_reports_readme(proj)):
        print(f"wrote {readme} (generic reports README)")


if __name__ == "__main__":
    main()
