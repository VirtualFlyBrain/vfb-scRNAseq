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
  not_gene   a current FlyBase feature that is not a gene (e.g. an FBti
             transposable-element insertion)              -> dropped

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

Features files keyed by FlyBase **annotation id** (`expression.features_keyed_by:
annotation_id`, e.g. "Dmel_CG17636" from an NCBI GenBank reference; an optional
`expression.annotation_id_prefix` such as "Dmel_" is stripped) take the gene that Chado
records for the annotation id (FlyBase Annotation IDs dbxref, current or retired; an id
of several genes is left unresolved), then are mapped as above; the feature name is kept
as `input_symbol`, which the expression build uses as the key.

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

from vfb_scrnaseq.ingest_h5ad import expression_h5ads, read_genes  # noqa: E402
from vfb_scrnaseq.project_config import load_config  # noqa: E402

PSQL = ["psql", "-h", "chado.flybase.org", "-U", "flybase", "flybase", "-At", "-F", "\t"]
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


def _h5ad_ids(project: str) -> tuple[list[str], dict[str, str]]:
    """(gene symbols in first-seen order, {symbol: FBgn from the authors' files}) over
    a project's h5ad files."""
    cfg = load_config(project)
    order: dict[str, None] = {}
    ids: dict[str, str] = {}
    for path in dict.fromkeys(expression_h5ads(cfg)):
        genes, fbgns = read_genes(path)
        for g, f in zip(genes, fbgns):
            order.setdefault(g)
            if f:
                ids.setdefault(g, f)
    return list(order), ids


def _input_ids(projects: list[str]) -> dict[str, str]:
    """{input symbol: input FBgn} pooled over other projects' committed gene_id_map.tsv
    (the ids their source files gave each symbol); a symbol given different ids by
    different projects is left out."""
    seen: dict[str, set[str]] = defaultdict(set)
    for other in projects:
        _, rows = read_map(REPO_ROOT / "projects" / other / "gene_id_map.tsv")
        for r in rows:
            if r["input_fbgn"] and r["input_symbol"]:
                seen[r["input_symbol"]].add(r["input_fbgn"])
    return {s: next(iter(f)) for s, f in seen.items() if len(f) == 1}


def features(cfg: dict) -> list[tuple[str, str]]:
    """(fbgn, symbol) over the project's features files (or h5ad genes, fbgn '' when
    the files give none), in first-seen order."""
    ex = cfg["expression"]
    if ex.get("source") == "h5ad":
        symbols, ids = _h5ad_ids(cfg["project"])
        # other projects' ids for a symbol: from their h5ad files when they are h5ad-sourced
        # (e.g. FCA Smart-seq2), else from their committed gene id maps
        others = ex.get("gene_ids_from", [])
        h5ad_src = [o for o in others if (load_config(o).get("expression") or {}).get("source") == "h5ad"]
        for other in h5ad_src:
            for g, f in _h5ad_ids(other)[1].items():
                ids.setdefault(g, f)
        for g, f in _input_ids([o for o in others if o not in h5ad_src]).items():
            ids.setdefault(g, f)
        return [(ids.get(g, ""), g) for g in symbols]
    files = [ex["features_file"]] + [p["features_file"] for p in ex.get("extra_parts", [])]
    seen: dict[str, str] = {}
    for f in files:
        with gzip.open(REPO_ROOT / ".cache" / f, "rt") as fh:
            for ln in fh:
                r = ln.rstrip("\n").split("\t")
                seen.setdefault(r[0], r[1] if len(r) > 1 else r[0])
    if ex.get("features_keyed_by") == "annotation_id":
        # features named by annotation id (e.g. Dmel_CG17636): the gene Chado records for it
        prefix = ex.get("annotation_id_prefix", "")
        ann = {name: name[len(prefix):] if name.startswith(prefix) else name for name in seen}
        ids = chado_annotation_lookup(sorted(set(ann.values())))
        return [(ids.get(ann[name], ""), name) for name in seen]
    if ex.get("features_keyed_by") == "symbol":
        # features files that carry gene symbols only (e.g. exported from Seurat
        # objects): the FBgn another project's input files give the symbol
        # (`expression.gene_ids_from`; symbols the projects disagree on skipped), else
        # looked up by symbol, as for h5ad projects
        ids = _input_ids(ex.get("gene_ids_from", []))
        return [(ids.get(sym, ""), sym) for sym in seen]
    return list(seen.items())


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
        out = subprocess.run(PSQL + ["-c", ANNOTATION_QUERY.format(ids=",".join(ids[i:i + 2000]))],
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
    out = subprocess.run(PSQL + ["-c", QUERY.format(ids=",".join(ids))],
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
    out = subprocess.run(PSQL + ["-v", "syms=" + "\t".join(symbols)], input=SYMBOL_QUERY,
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
