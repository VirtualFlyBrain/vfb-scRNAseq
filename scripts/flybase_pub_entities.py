#!/usr/bin/env python
"""List the genetic entities FlyBase curated for a paper, to scope a dataset's Samples.

Queries FlyBase Chado (feature_pub) for the alleles, insertions, constructs, split
combinations and stocks linked to the paper (FBal / FBti / FBtp / FBco / FBst), and
marks which are already in VFB production (the `genotype_includes` targets VFB can link
now; the others are imported later). FlyBase curates what the paper describes, which may
include lines used only in other experiments; and it may not link everything in the
sequenced genotypes (e.g. a tub-GAL80ts the paper mentions only in passing), so check the
paper as well.

Usage:
    uv run python scripts/flybase_pub_entities.py --fbrf FBrf0252876 [--no-vfb]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request

PSQL = ["psql", "-h", "chado.flybase.org", "-U", "flybase", "flybase", "-At", "-F", "\t"]
VFB_PDB = "https://pdb.virtualflybrain.org/db/neo4j/tx/commit"
PREFIXES = ("FBco", "FBal", "FBti", "FBtp", "FBst")
QUERY = """
select f.uniquename, f.name, c.name
from feature f
join feature_pub fp on fp.feature_id = f.feature_id
join pub p on p.pub_id = fp.pub_id
join cvterm c on c.cvterm_id = f.type_id
where p.uniquename = '{fbrf}' and not f.is_obsolete and f.uniquename ~ '^FB(co|al|ti|tp)'
union
select s.uniquename, s.name, 'stock'
from stock s
join stock_pub sp on sp.stock_id = s.stock_id
join pub p on p.pub_id = sp.pub_id
where p.uniquename = '{fbrf}' and not s.is_obsolete
"""


def chado_entities(fbrf: str) -> list[tuple[str, str, str]]:
    out = subprocess.run(PSQL + ["-c", QUERY.format(fbrf=fbrf)], capture_output=True, text=True, check=True)
    rows = [tuple(ln.split("\t")) for ln in out.stdout.splitlines() if ln.strip()]
    return sorted(rows, key=lambda r: (PREFIXES.index(r[0][:4]), r[0]))


def in_vfb(ids: list[str]) -> set[str]:
    body = json.dumps({"statements": [{"statement": "MATCH (n) WHERE n.short_form IN $ids RETURN n.short_form",
                                       "parameters": {"ids": ids}}]}).encode()
    req = urllib.request.Request(VFB_PDB, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return {row["row"][0] for row in json.load(r)["results"][0]["data"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fbrf", required=True, help="FlyBase reference id, e.g. FBrf0252876")
    ap.add_argument("--no-vfb", action="store_true", help="do not check VFB production")
    args = ap.parse_args()
    if not re.fullmatch(r"FBrf\d{7}", args.fbrf):
        sys.exit(f"not an FBrf id: {args.fbrf!r}")
    rows = chado_entities(args.fbrf)
    vfb = set() if args.no_vfb else in_vfb([r[0] for r in rows])
    for fbid, name, kind in rows:
        mark = "" if args.no_vfb else ("in VFB" if fbid in vfb else "-")
        print(f"{fbid}\t{name}\t{kind}\t{mark}")
    print(f"{len(rows)} entities for {args.fbrf}", file=sys.stderr)


if __name__ == "__main__":
    main()
