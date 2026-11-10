#!/usr/bin/env python
"""Check that the counts of merged genes can be summed.

Where FlyBase has merged genes, several of a matrix's input genes map to one current
gene (projects/<p>/gene_id_map.tsv) and build_expression.py sums their counts per cell.
That is right only if each read was counted for at most one input gene, as count
pipelines do (a read on overlapping gene models is discarded). A pipeline that shares
or duplicates reads between overlapping models (e.g. EM read assignment, or bulk TPM
as in vfb-EPseq-ontology) gives such genes identical values, and summing them would
double the gene's counts.

For each merged gene this reads the project's matrices (as build_expression.py does,
from .cache) and compares its input genes cell by cell. A pair with expression and
identical values in every cell fails the check; pairs that are zero everywhere pass.
Run it after update_gene_ids.py for a new dataset or a new FlyBase release. Not in CI
(it needs the matrices).

Usage:
    uv run python scripts/check_merged_genes.py [--project P ...] [--all]
"""

from __future__ import annotations

import argparse
import gzip
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vfb_scrnaseq import stats  # noqa: E402
from vfb_scrnaseq.project_config import load_config  # noqa: E402

_EMPTY = {"fbgn": [], "symbol": [], "clusters": [], "cluster_size": [], "S": None, "N": None,
          "cells": set(), "note": ""}


def merge_groups(targets: list[tuple[str, str] | None]) -> dict[str, list[int]]:
    """{current gene: input gene indices} for current genes with several inputs."""
    by: dict[str, list[int]] = defaultdict(list)
    for i, t in enumerate(targets):
        if t is not None:
            by[t[0]].append(i)
    return {g: ix for g, ix in by.items() if len(ix) > 1}


def compare(source: str, names: list[str], groups: dict[str, list[int]],
            entries: dict[int, dict[int, float]]) -> list[dict]:
    """One result per merged gene: input names, cells expressing each input, cells
    expressing all of them, and whether the inputs are identical in every cell."""
    out = []
    for gene, ix in groups.items():
        vecs = [entries.get(i, {}) for i in ix]
        out.append({"source": source, "gene": gene, "inputs": [names[i] for i in ix],
                    "cells": [len(v) for v in vecs],
                    "shared": len(set.intersection(*(set(v) for v in vecs))),
                    "identical": all(v == vecs[0] for v in vecs[1:])})
    return out


def _collect(rows, want: np.ndarray, entries: dict) -> None:
    for g, c, v in rows:
        m = np.isin(g, want) & (v != 0)
        for a, b, x in zip(g[m], c[m], v[m]):
            entries[int(a)][int(b)] = float(x)


def check_project(project: str) -> list[dict]:
    """Runs stats.compute_expression's input handling with the accumulators replaced
    by collectors, so the matrices and gene mapping are exactly the build's."""
    results: list[dict] = []

    def mtx(mtx_path, feats, bcs, memberships, gene_map=None):
        with gzip.open(feats, "rt") as fh:
            rows = [ln.rstrip("\n").split("\t") for ln in fh]
        ids = [r[0] for r in rows]
        syms = [r[1] if len(r) > 1 else r[0] for r in rows]
        targets = [(f, syms[i]) if gene_map is None else gene_map.get(f, (f, syms[i]))
                   for i, f in enumerate(ids)]
        groups = merge_groups(targets)
        entries: dict[int, dict[int, float]] = defaultdict(dict)
        if groups:
            want = np.array(sorted(i for ix in groups.values() for i in ix))
            _collect(((ch.g.values - 1, ch.c.values - 1, ch.v.values)
                      for ch in stats._read_chunks(mtx_path)), want, entries)
        names = [f"{ids[i]} {syms[i]}" if ids[i] != syms[i] else ids[i] for i in range(len(ids))]
        results.extend(compare(Path(mtx_path).name, names, groups, entries))
        return dict(_EMPTY)

    def h5ad(path, labels, values, gene_map, name):
        genes, _ = stats.read_genes(path)
        groups = merge_groups([gene_map.get(g) for g in genes])
        entries: dict[int, dict[int, float]] = defaultdict(dict)
        if groups:
            want = np.array(sorted(i for ix in groups.values() for i in ix))
            _collect(stats.iter_matrix(path), want, entries)
        results.extend(compare(Path(path).name, genes, groups, entries))
        return dict(_EMPTY)

    saved = stats._accumulate, stats._accumulate_h5ad, stats._summarise
    stats._accumulate, stats._accumulate_h5ad = mtx, h5ad
    stats._summarise = lambda *a, **k: None
    try:
        stats.compute_expression(project, load_config(project))
    finally:
        stats._accumulate, stats._accumulate_h5ad, stats._summarise = saved
    return results


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", action="append", default=[])
    ap.add_argument("--all", action="store_true", help="every project with a gene_id_map.tsv")
    args = ap.parse_args()
    projects = args.project or (sorted(p.parent.name for p in (REPO_ROOT / "projects").glob("*/gene_id_map.tsv"))
                                if args.all else [])
    if not projects:
        ap.error("give --project or --all")
    bad, failed = [], []
    for p in projects:
        try:
            res = check_project(p)
        except (Exception, SystemExit) as e:  # noqa: BLE001 - report and go on to the next project
            failed.append(p)
            print(f"{p}: could not read its inputs ({e!r}); fetch / build them in .cache first")
            continue
        print(f"{p}: {len(res)} merged gene(s)")
        for r in res:
            zero = not any(r["cells"])
            verdict = "zero everywhere" if zero else "IDENTICAL" if r["identical"] else "differ"
            print(f"  {r['source']}\t{r['gene']}\t{' + '.join(r['inputs'])}\t"
                  f"cells {r['cells']}, shared {r['shared']}\t{verdict}")
            if r["identical"] and not zero:
                bad.append(f"{p} {r['source']} {r['gene']}")
    if bad:
        sys.exit("merged genes with identical values (summing would double them):\n  " + "\n  ".join(bad))
    if failed:
        sys.exit(f"not checked: {', '.join(failed)}")
    print("ok: no merged gene has identical input values")


if __name__ == "__main__":
    main()
