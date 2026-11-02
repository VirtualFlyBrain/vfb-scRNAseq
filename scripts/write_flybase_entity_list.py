#!/usr/bin/env python
"""Write metadata/FlyBase_entity_list.txt: the FlyBase stocks, strains and genetic
entities the projects' Samples link.

Samples link FlyBase stocks (`stock`, FBst) and strains (`strain`, FBsn), or the
genetic entities in a cross's genotype (`genotype_includes`: FBal / FBti / FBtp / FBco). VFB has no labels for
most of these, so VirtualFlyBrain/vfb-scRNAseq-gene-annotations reads this list
and adds them, labelled from FlyBase, to VFB_scRNAseq_genes.owl, as it does for the
expressed genes (expression/FBgn_list.txt). One id per line, sorted, from every
projects/<p>/entities.json.

Usage:
    uv run python scripts/write_flybase_entity_list.py           # write
    uv run python scripts/write_flybase_entity_list.py --check   # fail if out of date (CI)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "metadata" / "FlyBase_entity_list.txt"
SLOTS = ("stock", "strain", "genotype_includes")
PREFIX = "FlyBase:"


def flybase_entities() -> list[str]:
    ids: set[str] = set()
    for path in sorted((REPO_ROOT / "projects").glob("*/entities.json")):
        for ent in json.loads(path.read_text()):
            if ent.get("type") != "Sample":
                continue
            for slot in SLOTS:
                vals = ent.get(slot) or []
                ids.update(v[len(PREFIX):] for v in ([vals] if isinstance(vals, str) else vals)
                           if v.startswith(PREFIX))
    return sorted(ids)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    text = "".join(f"{i}\n" for i in flybase_entities())
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            sys.exit(f"{OUT.relative_to(REPO_ROOT)} is out of date: run scripts/write_flybase_entity_list.py")
        print(f"{OUT.relative_to(REPO_ROOT)} up to date ({text.count(chr(10))} ids)")
        return
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(REPO_ROOT)} ({text.count(chr(10))} ids)")


if __name__ == "__main__":
    main()
