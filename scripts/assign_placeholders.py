#!/usr/bin/env python
"""Write class-based broad-match placeholders for unidentified numbered clusters.

Generic across projects. A cluster counts as an unidentified placeholder per the
project's `unidentified.rule` (config.yaml); it is assigned the broad FBbt anchor
for its author cell `class` (`unidentified.class_anchors`), as a broad match with
low confidence. Classes in `unidentified.hold_classes` are held (no placeholder),
as are all unidentified clusters when `unidentified.hold_unidentified` is true.
All project/tissue specifics live in config.yaml — see vfb_scrnaseq.project_config.

Idempotent: never overwrites an existing mapping file.

Usage:
    uv run python scripts/assign_placeholders.py --project kurmangaliyev_2020
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vfb_scrnaseq.project_config import (  # noqa: E402
    annotation_kind,
    broad_anchor,
    label_slug,
    load_config,
)


def placeholder(label: str, cls: str, anchor: dict) -> dict:
    return {
        "cluster_label": label,
        "working_definition": (
            f"Unidentified numbered cluster (class {cls}) with no named cell-type "
            f"identity assigned by the atlas authors."
        ),
        "searches_performed": ["(placeholder: class-based broad assignment; no literature search performed)"],
        "best_match": {
            "fbbt_term": anchor["label"],
            "fbbt_id": anchor["fbbt_id"],
            "fbbt_definition": anchor.get("definition", anchor["label"]),
            "match_type": "broad match",
            "skos_mapping": "skos:broadMatch",
            "confidence": "low",
        },
        "justification": (
            f"No named identity was assigned to cluster {label}; only its cell class "
            f"({cls}) is known. The honest mapping is a broad match to the class-level "
            f"FBbt term {anchor['fbbt_id']} ({anchor['label']}). Not a specific assignment."
        ),
        "other_candidates": [],
        "recommendation": (
            f"Class-based broad placeholder ({anchor['label']}). Revisit if the cluster's "
            f"identity is resolved in future work."
        ),
        "new_term_needed": False,
        "verification_needed": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    cfg = load_config(args.project)
    kind_of = annotation_kind(args.project, cfg)

    proj = REPO_ROOT / "projects" / args.project
    anns = json.loads((proj / "cell_type_annotations.json").read_text())["annotations"]
    mdir = proj / "mapping"
    mdir.mkdir(exist_ok=True)

    written = skipped_existing = held_n = no_anchor = 0
    for a in anns:
        label, cls = a["label"], a.get("class", "")
        kind = kind_of(a)
        if kind == "named":
            continue
        if kind == "held":
            held_n += 1
            continue
        anchor = broad_anchor(args.project, cfg, cls, a.get("clustering"))
        if not anchor:
            no_anchor += 1
            print(f"  WARNING: no class_anchor for class {cls!r} (cluster {label}); skipped", file=sys.stderr)
            continue
        out = mdir / f"{label_slug(label)}.fbbt_mapping.json"
        if out.exists():
            skipped_existing += 1
            continue
        data = placeholder(label, cls, anchor)
        out.write_text(json.dumps(data, indent=2) + "\n")
        payload = json.dumps({"tool_input": {"file_path": str(out), "content": json.dumps(data)}})
        r = subprocess.run([sys.executable, ".claude/hooks/check_fbbt_mapping.py"],
                           input=payload, capture_output=True, text=True, cwd=REPO_ROOT)
        if r.returncode != 0:
            raise SystemExit(f"placeholder for {label} failed validation:\n{r.stderr}")
        written += 1

    print(f"placeholders written: {written}; skipped (existing): {skipped_existing}; "
          f"held classes: {held_n}; missing-anchor: {no_anchor}")


if __name__ == "__main__":
    main()
