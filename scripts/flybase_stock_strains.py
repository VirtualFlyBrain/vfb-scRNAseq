#!/usr/bin/env python
"""Find the FlyBase strains (FBsn) for stocks or strain names, to fill a project's
`sample_build.strain` / `strain_map`.

FlyBase links a strain to its centre stocks by strainprop `derived_stock_strain_<centre>`
(value e.g. "25177 @FBst0025177:DGRP-304@"); there is no stock -> strain table. A stock
FlyBase has dropped can still have a current strain: look that up by name.

Usage:
    uv run python scripts/flybase_stock_strains.py FBst0025177 FBst0055026
    uv run python scripts/flybase_stock_strains.py --name DGRP-28 Canton-S
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # finds scripts/chado.py when loaded by path
from chado import psql as _psql  # VFB's Chado copy first, FlyBase's as fallback (FB_CHADO_HOST overrides)
BY_STOCK = """
select substring(sp.value from '@(FBst[0-9]{{7}}):'), s.uniquename, s.name
from strain s
join strainprop sp on sp.strain_id = s.strain_id
join cvterm t on t.cvterm_id = sp.type_id
where t.name like 'derived_stock_strain%' and not s.is_obsolete
  and substring(sp.value from '@(FBst[0-9]{{7}}):') in ({ids})
"""
BY_NAME = "select name, uniquename, name from strain where not is_obsolete and name in ({ids})"


def query(sql: str, values: list[str]) -> list[tuple[str, str, str]]:
    ids = ",".join("'" + v.replace("'", "''") + "'" for v in values)
    out = subprocess.run(_psql() + ["-c", sql.format(ids=ids)], capture_output=True, text=True, check=True)
    return [tuple(ln.split("\t")) for ln in out.stdout.splitlines() if ln.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("values", nargs="+", help="FBst ids, or strain names with --name")
    ap.add_argument("--name", action="store_true", help="look up strains by name")
    args = ap.parse_args()
    if not args.name and not all(re.fullmatch(r"FBst\d{7}", v) for v in args.values):
        sys.exit("give FBst ids, or strain names with --name")
    found = {}
    for key, fbsn, name in query(BY_NAME if args.name else BY_STOCK, args.values):
        found.setdefault(key, []).append((fbsn, name))
    for v in args.values:
        hits = found.get(v)
        print("\t".join([v] + ([f"{f} {n}" for f, n in hits] if hits else ["- (no FlyBase strain)"])))


if __name__ == "__main__":
    main()
