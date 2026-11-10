#!/usr/bin/env python
"""Mint VFBseq ids for another repo's entities (e.g. vfb-EPseq-ontology).

Other repos that publish VFBseq entities can't mint ids themselves: the registry is
here, so ids stay unique across repos. The other repo writes a key list (TSV with
columns entity_type, natural_key, label, accession; label and accession may be empty);
this mints an id for each row in id_registry/registry.json (idempotent: keys already
registered keep their id) and writes the list back with an `id` column, for that repo
to commit. Natural keys follow this repo's form: `<dataset accession>` for a Dataset,
`<dataset accession>:<key>` for anything else.

Commit the registry change here in a PR, as for any new ids.

Usage:
    uv run python scripts/mint_external_ids.py --keys ../vfb-EPseq-ontology/ids/keys.tsv \
        --out ../vfb-EPseq-ontology/ids/ids.tsv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vfb_scrnaseq.ids import ENTITY_TYPES, IDRegistry  # noqa: E402

COLUMNS = ["entity_type", "natural_key", "label", "accession"]


def mint(rows: list[dict], reg: IDRegistry) -> list[dict]:
    """Rows with an `id` added; raises on an unknown entity type or a repeated key."""
    seen, out = set(), []
    for r in rows:
        key = (r["entity_type"], r["natural_key"])
        if r["entity_type"] not in ENTITY_TYPES:
            raise ValueError(f"unknown entity_type {r['entity_type']!r} (expected one of {ENTITY_TYPES})")
        if not r["natural_key"] or key in seen:
            raise ValueError(f"empty or repeated natural key: {key}")
        seen.add(key)
        vid = reg.mint(r["entity_type"], r["natural_key"],
                       label=r.get("label") or None, accession=r.get("accession") or None)
        out.append({"id": vid, **{c: r.get(c, "") for c in COLUMNS}})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", required=True, type=Path, help="TSV: entity_type, natural_key, label, accession")
    ap.add_argument("--out", required=True, type=Path, help="TSV written with an id column")
    ap.add_argument("--registry", type=Path, default=REPO_ROOT / "id_registry" / "registry.json")
    args = ap.parse_args()

    with args.keys.open() as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    reg = IDRegistry.load(args.registry)
    before = reg._counter
    out = mint(rows, reg)
    reg.save()
    with args.out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", *COLUMNS], delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    print(f"{len(out)} ids ({reg._counter - before} new) -> {args.out}")


if __name__ == "__main__":
    main()
