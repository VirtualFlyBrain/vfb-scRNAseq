#!/usr/bin/env python
"""Copy type-level FBbt mappings to every cluster of that type.

When an atlas's author types recur across clusterings (e.g. the same Fly Cell Atlas
type in many tissue analyses, 10x and Smart-seq2), the mapping is made once per type
in `type_mapping/<type slug>.fbbt_mapping.json` and copied here to
`mapping/<cluster label slug>.fbbt_mapping.json` (with `cluster_label` set to the
cluster) for every annotation that is not held (`unannotated`, or held by the
project's `unidentified` rules).

Config (optional, config.yaml):
  type_mapping:
    from: <project>      # also take type mappings from another project (the project's
                         # own type_mapping/ is searched first, when it has one)
    aliases:             # this project's type -> the type it is in `from` (e.g. an AFCA
      <type>: <type>     # "epithelial cell_head" is the FCA "epithelial cell")

Curators normally edit the type-level file; its `manual_edit` block is copied to the
clusters (so mapping.tsv shows it). A cluster-level file whose own `manual_edit`
differs from its type's (a cluster-specific edit) is never overwritten. Stale cluster
files for labels no longer present are removed.

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

from vfb_scrnaseq.project_config import annotation_kind, label_slug, load_config  # noqa: E402


def _type_mapping(typ: str, type_dirs: list[Path], aliases: dict[str, str], own: Path) -> dict | None:
    """The first type-level mapping found for `typ` (own dir first); in another
    project's dir it is looked up under its alias, if any."""
    for d in type_dirs:
        name = typ if d == own else aliases.get(typ, typ)
        src = d / f"{label_slug(name)}.fbbt_mapping.json"
        if src.exists():
            return json.loads(src.read_text())
    return None


def expand(proj: Path, type_dirs: list[Path] | Path, aliases: dict[str, str] | None = None,
           is_held=None) -> tuple[int, list[str], list[str]]:
    """Returns (n written, labels kept for manual_edit, (label, type) pairs missing)."""
    type_dirs = [type_dirs] if isinstance(type_dirs, Path) else type_dirs
    aliases = aliases or {}
    is_held = is_held or (lambda a: bool(a.get("unannotated")))
    anns = json.loads((proj / "cell_type_annotations.json").read_text())["annotations"]
    mdir = proj / "mapping"
    mdir.mkdir(exist_ok=True)
    wanted, kept, missing, n = set(), [], [], 0
    for a in anns:
        if is_held(a):
            continue
        dest = mdir / f"{label_slug(a['label'])}.fbbt_mapping.json"
        wanted.add(dest.name)
        m = _type_mapping(a.get("type", a["label"]), type_dirs, aliases, proj / "type_mapping")
        if dest.exists():
            own = json.loads(dest.read_text()).get("manual_edit")
            if own and own != (m or {}).get("manual_edit"):
                kept.append(a["label"])          # cluster-specific curator edit
                continue
        if m is None:
            missing.append(f"{a['label']} (type {a.get('type')!r})")
            continue
        m["cluster_label"] = a["label"]
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
    tm = cfg.get("type_mapping") or {}
    own = REPO_ROOT / "projects" / args.project / "type_mapping"
    type_dirs = [own] if own.is_dir() or not tm.get("from") else []
    if tm.get("from"):
        type_dirs.append(REPO_ROOT / "projects" / tm["from"] / "type_mapping")
    kind = annotation_kind(args.project, cfg)
    n, kept, missing = expand(REPO_ROOT / "projects" / args.project, type_dirs,
                              tm.get("aliases"), lambda a: kind(a) == "held")
    print(f"{args.project}: wrote {n} cluster mappings from "
          f"{', '.join(str(d.relative_to(REPO_ROOT)) for d in type_dirs)}")
    if kept:
        print(f"  kept {len(kept)} cluster files with manual_edit: {kept}")
    if missing:
        print(f"  {len(missing)} clusters lack a type mapping:")
        for m in missing:
            print(f"    {m}")


if __name__ == "__main__":
    main()
