#!/usr/bin/env python
"""Map a project's gene ids to current FlyBase genes -> projects/<p>/gene_id_map.tsv.

Gene ids come from the GEO features file(s) as published, so some are no longer
current. This queries FlyBase Chado (public read-only:
`psql -h chado.flybase.org -U flybase flybase`) once and writes a committed table the
expression build applies (`expression.gene_id_map`), so builds stay reproducible and
need no Chado access:

  current    the id is a current gene                    -> kept (symbol refreshed)
  secondary  a retired id of exactly one current gene    -> replaced by that gene
             (two retired ids of the same gene = a merge: counts are summed per cell)
  split      a retired id of more than one current gene  -> dropped (reads can't be
             attributed to the new genes; curator decision 2026-10-06)
  withdrawn  no current gene                             -> dropped

h5ad projects (`expression.source: h5ad`) are keyed by gene **symbol** (the
matrix's gene names): a symbol takes the FBgn the authors' files give it (`var` /
`raw.var` column `ID`, pooled over the project's files and any `expression.gene_ids_from`
projects) and is then mapped as above; a symbol with no FBgn is looked up by name
(D. melanogaster genes only):

  current    the current symbol of a gene                -> that gene
  synonym    no current match; a synonym of exactly one gene -> that gene
  ambiguous  a synonym of several genes                  -> dropped
  unmatched  no gene                                     -> dropped

Chado records a current gene's own FBgn and each retired FBgn it absorbed as its
FlyBase dbxrefs (feature_dbxref.is_current true / false).

The FlyBase release is read from the FlyBase homepage ("FB2026_03, released
September 17, 2026"; the website and Chado are updated together) and recorded in the
table header with Chado's last-modified date (its data freeze for that release).

Usage:
    uv run python scripts/update_gene_ids.py --project davie_2018 [--release FB2026_03]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import re
import subprocess
import urllib.request
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vfb_scrnaseq.ingest_h5ad import h5ad_path, read_genes  # noqa: E402
from vfb_scrnaseq.project_config import load_config  # noqa: E402

PSQL = ["psql", "-h", "chado.flybase.org", "-U", "flybase", "flybase", "-At", "-F", "\t"]
COLUMNS = ["input_fbgn", "input_symbol", "status", "current_fbgn", "current_symbol"]

QUERY = """
with ids as (select unnest(string_to_array('{ids}', ',')) u),
cur as (select ids.u, f.uniquename as cur, f.name as sym from ids
        join feature f on f.uniquename = ids.u and not f.is_obsolete),
sec as (select ids.u, f.uniquename as cur, f.name as sym from ids
        join dbxref d on d.accession = ids.u
        join db on db.db_id = d.db_id and db.name = 'FlyBase'
        join feature_dbxref fd on fd.dbxref_id = d.dbxref_id and not fd.is_current
        join feature f on f.feature_id = fd.feature_id and not f.is_obsolete
                       and f.uniquename like 'FBgn%'
        where ids.u not in (select u from cur))
select u, 'current', cur, sym from cur
union all select u, 'secondary', cur, sym from sec
union all select u, 'withdrawn', '', '' from ids
  where u not in (select u from cur) and u not in (select u from sec);
"""


SYMBOL_QUERY = """
with s as (select unnest(string_to_array(:'syms', E'\\t')) u),
dmel as (select organism_id from organism where genus = 'Drosophila' and species = 'melanogaster'),
genes as (select f.feature_id, f.uniquename, f.name from feature f
          where not f.is_obsolete and f.uniquename like 'FBgn%'
            and f.organism_id in (select organism_id from dmel))
select distinct s.u, 'current', g.uniquename, g.name from s join genes g on g.name = s.u
union all
select distinct s.u, 'synonym', g.uniquename, g.name from s
  join synonym y on y.name = s.u
  join feature_synonym fs on fs.synonym_id = y.synonym_id
  join genes g on g.feature_id = fs.feature_id;
"""


def _h5ad_ids(project: str) -> tuple[list[str], dict[str, str]]:
    """(gene symbols in first-seen order, {symbol: FBgn from the authors' files}) over
    a project's h5ad files."""
    cfg = load_config(project)
    acc = cfg["dataset"]["accession"]
    order: dict[str, None] = {}
    ids: dict[str, str] = {}
    for c in cfg["sample_build"]["clusterings"]:
        genes, fbgns = read_genes(h5ad_path(acc, c["id"]))
        for g, f in zip(genes, fbgns):
            order.setdefault(g)
            if f:
                ids.setdefault(g, f)
    return list(order), ids


def features(cfg: dict) -> list[tuple[str, str]]:
    """(fbgn, symbol) over the project's features files (or h5ad genes, fbgn '' when
    the files give none), in first-seen order."""
    ex = cfg["expression"]
    if ex.get("source") == "h5ad":
        symbols, ids = _h5ad_ids(cfg["project"])
        for other in ex.get("gene_ids_from", []):
            for g, f in _h5ad_ids(other)[1].items():
                ids.setdefault(g, f)
        return [(ids.get(g, ""), g) for g in symbols]
    files = [ex["features_file"]] + [p["features_file"] for p in ex.get("extra_parts", [])]
    seen: dict[str, str] = {}
    for f in files:
        with gzip.open(REPO_ROOT / ".cache" / f, "rt") as fh:
            for ln in fh:
                r = ln.rstrip("\n").split("\t")
                seen.setdefault(r[0], r[1] if len(r) > 1 else r[0])
    return list(seen.items())


def read_map(path: Path) -> tuple[str, list[dict]]:
    """A committed gene_id_map.tsv -> (header comment line, rows)."""
    with path.open() as fh:
        header = fh.readline().rstrip("\n")
        return header, list(csv.DictReader(fh, delimiter="\t"))


def map_release(path: Path) -> str:
    """The FlyBase release ('FB2026_03') recorded in a gene_id_map.tsv header, or ''."""
    m = re.search(r"FlyBase (FB\d{4}_\d{2})", read_map(path)[0])
    return m.group(1) if m else ""


def chado_lookup(ids: list[str]) -> dict[str, list[tuple[str, str, str]]]:
    out = subprocess.run(PSQL + ["-c", QUERY.format(ids=",".join(ids))],
                         capture_output=True, text=True, check=True).stdout
    hits: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for line in out.splitlines():
        u, status, cur, sym = line.split("\t")
        hits[u].append((status, cur, sym))
    return hits


def chado_symbol_lookup(symbols: list[str]) -> dict[str, list[tuple[str, str, str]]]:
    """{symbol: [(current|synonym, fbgn, current symbol)]} for D. melanogaster genes."""
    if not symbols:
        return {}
    out = subprocess.run(PSQL + ["-v", "syms=" + "\t".join(symbols)], input=SYMBOL_QUERY,
                         capture_output=True, text=True, check=True).stdout
    hits: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for line in out.splitlines():
        u, how, cur, sym = line.split("\t")
        hits[u].append((how, cur, sym))
    return hits


def classify_symbols(symbols: list[str], hits: dict) -> list[dict]:
    rows = []
    for sym in symbols:
        h = hits.get(sym, [])
        cur = sorted({(f, s) for how, f, s in h if how == "current"})
        syn = sorted({(f, s) for how, f, s in h if how == "synonym"})
        pick = cur if cur else syn
        status = ("unmatched" if not pick else "ambiguous" if len(pick) > 1
                  else "current" if cur else "synonym")
        keep = status in ("current", "synonym")
        rows.append({"input_fbgn": "", "input_symbol": sym, "status": status,
                     "current_fbgn": pick[0][0] if keep else "",
                     "current_symbol": pick[0][1] if keep else
                     ("; ".join(f"{f} {s}" for f, s in pick) if status == "ambiguous" else "")})
    return rows


def reclassify(feats: list[tuple[str, str]]) -> list[dict]:
    """Map rows for (fbgn, symbol) inputs, in input order: by FBgn where given, else by
    symbol (fbgn '')."""
    with_id = [(f, g) for f, g in feats if f]
    by_id = classify(with_id, chado_lookup([f for f, _ in with_id])) if with_id else []
    no_id = [g for f, g in feats if not f and g]
    by_symbol = classify_symbols(no_id, chado_symbol_lookup(no_id))
    out, i, j = [], iter(by_id), iter(by_symbol)
    for f, g in feats:
        out.append(next(i) if f else next(j) if g else
                   {"input_fbgn": "", "input_symbol": "", "status": "unmatched",
                    "current_fbgn": "", "current_symbol": ""})
    return out


def flybase_release() -> str:
    """'FB2026_03, released September 17, 2026' from the FlyBase homepage ('' if unavailable)."""
    try:
        req = urllib.request.Request("https://flybase.org/", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
            text = r.read().decode("utf-8", "ignore")
    except OSError:
        return ""
    m = re.search(r"(FB\d{4}_\d{2})\s*,\s*released\s+([A-Z][a-z]+ \d{1,2}, \d{4})", text)
    return f"{m.group(1)}, released {m.group(2)}" if m else ""


def chado_last_modified() -> str:
    out = subprocess.run(PSQL + ["-c", "select max(timelastmodified) from feature where uniquename like 'FBgn%'"],
                         capture_output=True, text=True, check=True).stdout.strip()
    return out[:10]


def classify(feats: list[tuple[str, str]], hits: dict) -> list[dict]:
    rows = []
    for fbgn, sym in feats:
        h = hits.get(fbgn, [])
        status = h[0][0] if h else "withdrawn"
        if status == "secondary" and len(h) > 1:
            status = "split"
        keep = status in ("current", "secondary")
        rows.append({"input_fbgn": fbgn, "input_symbol": sym, "status": status,
                     "current_fbgn": h[0][1] if keep else "",
                     "current_symbol": h[0][2] if keep else
                     ("; ".join(f"{c} {s}" for _, c, s in h) if status == "split" else "")})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--release", default="", help="override the FlyBase release read from flybase.org")
    args = ap.parse_args()

    release = args.release or flybase_release()
    if not release:
        print("  WARNING: could not read the FlyBase release from flybase.org; pass --release", file=sys.stderr)
    cfg = load_config(args.project)
    feats = features(cfg)
    rows = reclassify(feats)
    out = REPO_ROOT / "projects" / args.project / "gene_id_map.tsv"
    with out.open("w", newline="") as fh:
        fh.write(f"# FlyBase Chado (chado.flybase.org), queried {dt.date.today().isoformat()}; "
                 f"data last modified {chado_last_modified()}"
                 f"{'; FlyBase ' + release if release else ''}\n")
        w = csv.DictWriter(fh, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    counts = defaultdict(int)
    for r in rows:
        counts[r["status"]] += 1
    targets = defaultdict(int)
    for r in rows:
        if r["current_fbgn"]:
            targets[r["current_fbgn"]] += 1
    print(f"wrote {out}: {dict(counts)}; merges: {sum(1 for n in targets.values() if n > 1)}")


if __name__ == "__main__":
    main()
