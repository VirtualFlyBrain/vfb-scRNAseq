#!/usr/bin/env python
"""Map a project's gene ids to current FlyBase genes -> projects/<p>/gene_id_map.tsv.

Gene ids come from the GEO features file(s) as published, so some are no longer
current. This queries FlyBase Chado (public read-only:
`psql`, VFB's copy chado.flybase.virtualflybrain.org:443 or chado.flybase.org) once and writes a committed table the
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

The Chado queries and classification are in `vfb_scrnaseq.gene_ids`. The FlyBase release is read from the FlyBase homepage ("FB2026_03, released
September 17, 2026"; the website and Chado are updated together) and recorded in the
table header with Chado's last-modified date (its data freeze for that release).

Usage:
    uv run python scripts/update_gene_ids.py --project davie_2018 [--release FB2026_03]
"""

from __future__ import annotations

import argparse
import gzip
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vfb_scrnaseq.ingest_h5ad import expression_h5ads, read_genes  # noqa: E402
from vfb_scrnaseq.project_config import load_config  # noqa: E402
from vfb_scrnaseq import gene_ids  # noqa: E402
from vfb_scrnaseq.gene_ids import read_map  # noqa: E402

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
        ids = gene_ids.chado_annotation_lookup(sorted(set(ann.values())))
        return [(ids.get(ann[name], ""), name) for name in seen]
    if ex.get("features_keyed_by") == "symbol":
        # features files that carry gene symbols only (e.g. exported from Seurat
        # objects): the FBgn another project's input files give the symbol
        # (`expression.gene_ids_from`; symbols the projects disagree on skipped), else
        # looked up by symbol, as for h5ad projects
        ids = _input_ids(ex.get("gene_ids_from", []))
        return [(ids.get(sym, ""), sym) for sym in seen]
    return list(seen.items())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--release", default="", help="override the FlyBase release read from flybase.org")
    args = ap.parse_args()

    release = args.release or gene_ids.flybase_release()
    if not release:
        print("  WARNING: could not read the FlyBase release from flybase.org; pass --release", file=sys.stderr)
    rows = gene_ids.reclassify(features(load_config(args.project)))
    out = REPO_ROOT / "projects" / args.project / "gene_id_map.tsv"
    counts = gene_ids.write_map(out, rows, release)
    merges = counts.pop("merges")
    print(f"wrote {out}: {counts}; merges: {merges}")

if __name__ == "__main__":
    main()
