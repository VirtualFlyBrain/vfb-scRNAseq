#!/usr/bin/env python
"""Copy type-level FBbt mappings to every cluster of that type.

When an atlas's author types recur across clusterings (e.g. the same Fly Cell Atlas
type in many tissue analyses, 10x and Smart-seq2), the mapping is made once per type
in `type_mapping/<type slug>.fbbt_mapping.json` and copied here to
`mapping/<cluster label slug>.fbbt_mapping.json` (with `cluster_label` set to the
cluster) for every annotation that is not `unannotated`.

Config (optional, config.yaml):
  type_mapping:
    from: <project>      # take the type mappings from another project (default: own)

A cluster-level file carrying `manual_edit` is never overwritten (curators should
normally edit the type-level file instead); stale cluster files for labels no longer
present are removed.

Usage:
    uv run python scripts/expand_type_mappings.py --project li_2022_fca_ss2
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vfb_scrnaseq.project_config import label_slug, load_config  # noqa: E402


def expand(proj: Path, type_dir: Path) -> tuple[int, list[str], list[str]]:
    """Returns (n written, labels kept for manual_edit, (label, type) pairs missing)."""
    anns = json.loads((proj / "cell_type_annotations.json").read_text())["annotations"]
    mdir = proj / "mapping"
    mdir.mkdir(exist_ok=True)
    wanted, kept, missing, n = set(), [], [], 0
    for a in anns:
        if a.get("unannotated"):
            continue
        dest = mdir / f"{label_slug(a['label'])}.fbbt_mapping.json"
        wanted.add(dest.name)
        if dest.exists() and "manual_edit" in json.loads(dest.read_text()):
            kept.append(a["label"])
            continue
        src = type_dir / f"{label_slug(a.get('type', a['label']))}.fbbt_mapping.json"
        if not src.exists():
            missing.append(f"{a['label']} (type {a.get('type')!r})")
            continue
        m = json.loads(src.read_text())
        m["cluster_label"] = a["label"]
        m.pop("manual_edit", None)      # a type-level curator edit is recorded on the type file
        dest.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
        n += 1
    for stale in mdir.glob("*.fbbt_mapping.json"):
        if stale.name not in wanted:
            stale.unlink()
    return n, kept, missing


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()
    cfg = load_config(args.project)
    src_project = (cfg.get("type_mapping") or {}).get("from", args.project)
    type_dir = REPO_ROOT / "projects" / src_project / "type_mapping"
    n, kept, missing = expand(REPO_ROOT / "projects" / args.project, type_dir)
    print(f"{args.project}: wrote {n} cluster mappings from {type_dir.relative_to(REPO_ROOT)}")
    if kept:
        print(f"  kept {len(kept)} cluster files with manual_edit: {kept}")
    if missing:
        print(f"  {len(missing)} clusters lack a type mapping:")
        for m in missing:
            print(f"    {m}")


if __name__ == "__main__":
    main()
