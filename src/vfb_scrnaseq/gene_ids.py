"""Map gene ids or symbols to current FlyBase genes, via FlyBase Chado.

The dataset-agnostic part of ``scripts/update_gene_ids.py`` (which documents the
statuses and reads each project's input files), shared with other repos that use this
package (vfb-EPseq-ontology). A gene_id_map.tsv has a ``#`` header line recording the
Chado server, query date, Chado's data last-modified date and the FlyBase release,
then the :data:`COLUMNS`.
"""

from __future__ import annotations

import csv
import datetime as dt
import re
import subprocess
import urllib.request
from collections import defaultdict
from pathlib import Path

from vfb_scrnaseq.chado import psql as _psql  # VFB's Chado copy first, FlyBase's as fallback

COLUMNS = ["input_fbgn", "input_symbol", "status", "current_fbgn", "current_symbol"]

QUERY = """
with ids as (select unnest(string_to_array('{ids}', ',')) u),
cur as (select ids.u, f.uniquename as cur, f.name as sym from ids
        join feature f on f.uniquename = ids.u and not f.is_obsolete
                       and f.uniquename like 'FBgn%'),
nongene as (select ids.u from ids
        join feature f on f.uniquename = ids.u and not f.is_obsolete
                       and f.uniquename not like 'FBgn%'),
sec as (select ids.u, f.uniquename as cur, f.name as sym from ids
        join dbxref d on d.accession = ids.u
        join db on db.db_id = d.db_id and db.name = 'FlyBase'
        join feature_dbxref fd on fd.dbxref_id = d.dbxref_id and not fd.is_current
        join feature f on f.feature_id = fd.feature_id and not f.is_obsolete
                       and f.uniquename like 'FBgn%'
        where ids.u not in (select u from cur) and ids.u not in (select u from nongene))
select u, 'current', cur, sym from cur
union all select u, 'secondary', cur, sym from sec
union all select u, 'not_gene', '', '' from nongene
union all select u, 'withdrawn', '', '' from ids
  where u not in (select u from cur) and u not in (select u from sec)
    and u not in (select u from nongene);
"""


SYMBOL_QUERY = """
with s as (select unnest(string_to_array(:'syms', E'\\t')) u),
dmel as (select organism_id from organism where genus = 'Drosophila' and species = 'melanogaster'),
genes as (select f.feature_id, f.uniquename, f.name from feature f
          where not f.is_obsolete and f.uniquename like 'FBgn%'
            and f.organism_id in (select organism_id from dmel))
select distinct s.u, 'current', g.uniquename, g.name, 0 from s join genes g on g.name = s.u
union all
select s.u, 'synonym', g.uniquename, g.name, count(distinct fs.pub_id) from s
  join synonym y on y.name = s.u
  join feature_synonym fs on fs.synonym_id = y.synonym_id
  join genes g on g.feature_id = fs.feature_id
  group by s.u, g.uniquename, g.name;
"""


ANNOTATION_QUERY = """
with ids as (select unnest(string_to_array('{ids}', ',')) u)
select ids.u, f.uniquename from ids
join dbxref d on d.accession = ids.u
join db on db.db_id = d.db_id and db.name = 'FlyBase Annotation IDs'
join feature_dbxref fd on fd.dbxref_id = d.dbxref_id
join feature f on f.feature_id = fd.feature_id and not f.is_obsolete and f.uniquename like 'FBgn%';
"""


def chado_annotation_lookup(ids: list[str]) -> dict[str, str]:
    """{annotation id: FBgn} for ids that Chado records against exactly one current gene."""
    genes: dict[str, set[str]] = defaultdict(set)
    for i in range(0, len(ids), 2000):
        out = subprocess.run(_psql() + ["-c", ANNOTATION_QUERY.format(ids=",".join(ids[i:i + 2000]))],
                             capture_output=True, text=True, check=True).stdout
        for line in out.splitlines():
            u, fbgn = line.split("\t")
            genes[u].add(fbgn)
    return {u: g.pop() for u, g in genes.items() if len(g) == 1}


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
    out = subprocess.run(_psql() + ["-c", QUERY.format(ids=",".join(ids))],
                         capture_output=True, text=True, check=True).stdout
    hits: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for line in out.splitlines():
        u, status, cur, sym = line.split("\t")
        hits[u].append((status, cur, sym))
    return hits


def chado_symbol_lookup(symbols: list[str]) -> dict[str, list[tuple]]:
    """{symbol: [(current|synonym, fbgn, current symbol, publications using the
    synonym for that gene)]} for D. melanogaster genes."""
    if not symbols:
        return {}
    out = subprocess.run(_psql() + ["-v", "syms=" + "\t".join(symbols)], input=SYMBOL_QUERY,
                         capture_output=True, text=True, check=True).stdout
    hits: dict[str, list[tuple]] = defaultdict(list)
    for line in out.splitlines():
        u, how, cur, sym, pubs = line.split("\t")
        hits[u].append((how, cur, sym, int(pubs)))
    return hits


MAJORITY_MIN_PUBS, MAJORITY_RATIO = 10, 5


def _majority(syn: list[tuple], pubs: dict) -> list[tuple]:
    """An old symbol that is a synonym of several genes is taken as the one gene that
    the literature overwhelmingly uses it for (>= MAJORITY_MIN_PUBS publications and
    >= MAJORITY_RATIO times the next gene) — e.g. 'Cha' for ChAT (41 vs 2); otherwise
    left ambiguous."""
    ranked = sorted(syn, key=lambda fs: -pubs.get(fs, 0))
    top, nxt = pubs.get(ranked[0], 0), pubs.get(ranked[1], 0)
    return [ranked[0]] if top >= MAJORITY_MIN_PUBS and top >= MAJORITY_RATIO * max(nxt, 1) else syn


def classify_symbols(symbols: list[str], hits: dict) -> list[dict]:
    rows = []
    for sym in symbols:
        h = hits.get(sym, [])
        cur = sorted({(x[1], x[2]) for x in h if x[0] == "current"})
        syn = sorted({(x[1], x[2]) for x in h if x[0] == "synonym"})
        pubs: dict = defaultdict(int)
        for x in h:
            if x[0] == "synonym" and len(x) > 3:
                pubs[(x[1], x[2])] += x[3]
        if not cur and len(syn) > 1:
            syn = _majority(syn, pubs)
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
    out = subprocess.run(_psql() + ["-c", "select max(timelastmodified) from feature where uniquename like 'FBgn%'"],
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




def write_map(path: Path, rows: list[dict], release: str = "") -> dict[str, int]:
    """Write a gene_id_map.tsv (header line + rows); returns {status: count}, plus
    ``merges`` (current genes that several input ids map to)."""
    with Path(path).open("w", newline="") as fh:
        fh.write(f"# FlyBase Chado ({_psql()[2].split()[0][5:]}), queried {dt.date.today().isoformat()}; "
                 f"data last modified {chado_last_modified()}"
                 f"{'; FlyBase ' + release if release else ''}\n")
        w = csv.DictWriter(fh, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    counts: dict[str, int] = defaultdict(int)
    targets: dict[str, int] = defaultdict(int)
    for r in rows:
        counts[r["status"]] += 1
        if r["current_fbgn"]:
            targets[r["current_fbgn"]] += 1
    counts["merges"] = sum(1 for n in targets.values() if n > 1)
    return dict(counts)
