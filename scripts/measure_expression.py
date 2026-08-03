#!/usr/bin/env python
"""Measurement pass / prototype for the FlyBase-style summary expression stats.

Streams the GEO 10x MatrixMarket (genes x cells) in two chunked passes:
  1. per-cell total counts (for CPM normalisation);
  2. per (gene, cluster): sum of CPM over expressing cells + count of expressing cells.
Then, per FlyBase SOP:
  extent = expressing_cells / cluster_cells        (normalisation-invariant)
  level  = mean CPM over EXPRESSING cells = 1e6 * sum(count/cell_total) / expressing
Filter: extent > 0.2 (from the old repo's process_metadata.py).

Reports gene/cell/cluster counts, total vs filtered rows (-> file-size estimate),
and a spot-check of top genes for a couple of clusters. Memory stays low (dense
accumulators are genes x clusters only); the 1 GB gz is never fully materialised.

Usage:
    uv run python scripts/measure_expression.py --project kurmangaliyev_2020
"""

from __future__ import annotations

import argparse
import csv
import gzip
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
from vfb_scrnaseq.project_config import load_config  # noqa: E402

CUTOFF = 0.2
CHUNK = 5_000_000


def _open_mtx(path: Path):
    fh = gzip.open(path, "rt")
    line = fh.readline()
    while line.startswith("%"):
        line = fh.readline()
    n_genes, n_cells, nnz = (int(x) for x in line.split())
    return fh, n_genes, n_cells, nnz


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--spotcheck", nargs="*", default=["T4a", "Mi1"])
    args = ap.parse_args()

    cfg = load_config(args.project)
    acc = cfg["dataset"]["accession"]
    subset = cfg["annotations"].get("subset", "main")
    label_col = cfg["annotations"]["label_column"]
    cache = REPO_ROOT / ".cache"
    mtx = cache / f"{acc}_matrix_{subset}.mtx.gz"
    feats = cache / f"{acc}_features_{subset}.tsv.gz"
    bcs = cache / f"{acc}_barcodes_{subset}.tsv.gz"
    meta = cache / f"{acc}_metadata_{subset}.tsv.gz"

    # gene ids/symbols (row order), barcodes (col order), barcode -> cluster label
    with gzip.open(feats, "rt") as fh:
        gene_rows = [ln.rstrip("\n").split("\t") for ln in fh]
    gene_id = [r[0] for r in gene_rows]
    gene_sym = [r[1] if len(r) > 1 else r[0] for r in gene_rows]
    with gzip.open(bcs, "rt") as fh:
        barcodes = [ln.strip() for ln in fh]
    with gzip.open(meta, "rt") as fh:
        bc2cluster = {r["barcode"]: r[label_col] for r in csv.DictReader(fh, delimiter="\t")}

    _, n_genes, n_cells, nnz = _open_mtx(mtx)
    print(f"matrix: {n_genes} genes x {n_cells} cells, {nnz} nonzeros; "
          f"features={len(gene_id)} barcodes={len(barcodes)} meta={len(bc2cluster)}")

    clusters = sorted(set(bc2cluster.values()))
    cidx = {c: i for i, c in enumerate(clusters)}
    n_clu = len(clusters)
    col_cluster = np.array([cidx[bc2cluster[b]] for b in barcodes], dtype=np.int32)
    cluster_size = np.bincount(col_cluster, minlength=n_clu).astype(np.int64)

    # pass 1: per-cell totals
    col_total = np.zeros(n_cells, dtype=np.float64)
    fh, *_ = _open_mtx(mtx)
    for chunk in pd.read_csv(fh, sep=r"\s+", header=None, names=["g", "c", "v"],
                             chunksize=CHUNK, dtype={"g": np.int32, "c": np.int32, "v": np.float64}):
        col_total += np.bincount(chunk.c.values - 1, weights=chunk.v.values, minlength=n_cells)
    fh.close()

    # pass 2: per (gene, cluster) sum of CPM-contribution and count of expressing cells
    S = np.zeros(n_genes * n_clu, dtype=np.float64)   # sum of count/cell_total
    N = np.zeros(n_genes * n_clu, dtype=np.int64)     # expressing-cell count
    fh, *_ = _open_mtx(mtx)
    for chunk in pd.read_csv(fh, sep=r"\s+", header=None, names=["g", "c", "v"],
                             chunksize=CHUNK, dtype={"g": np.int32, "c": np.int32, "v": np.float64}):
        g = chunk.g.values - 1
        c = chunk.c.values - 1
        k = col_cluster[c]
        flat = g * n_clu + k
        S += np.bincount(flat, weights=chunk.v.values / col_total[c], minlength=n_genes * n_clu)
        N += np.bincount(flat, minlength=n_genes * n_clu)
    fh.close()

    S = S.reshape(n_genes, n_clu)
    N = N.reshape(n_genes, n_clu)
    with np.errstate(divide="ignore", invalid="ignore"):
        extent = N / cluster_size[None, :]
        level = np.where(N > 0, 1e6 * S / N, 0.0)

    total_rows = int((N > 0).sum())
    filtered_rows = int((extent > CUTOFF).sum())
    print(f"\nclusters: {n_clu} | cells: {int(cluster_size.sum())}")
    print(f"rows (cluster x gene) with extent>0   : {total_rows:,}")
    print(f"rows with extent>{CUTOFF}                  : {filtered_rows:,}")
    print(f"mean genes/cluster: total={total_rows/n_clu:.0f}  filtered={filtered_rows/n_clu:.0f}")
    # size estimates
    print(f"\nParquet est (filtered, ~12 B/row): ~{filtered_rows*12/1e6:.1f} MB   "
          f"(unfiltered ~{total_rows*12/1e6:.1f} MB)")
    print(f"TTL est (filtered, ~4 triples/row, ~50 B/triple): ~{filtered_rows*4*50/1e6:.0f} MB")

    for name in args.spotcheck:
        if name not in cidx:
            print(f"\n[{name}] not a cluster"); continue
        k = cidx[name]
        keep = np.where(extent[:, k] > CUTOFF)[0]
        order = keep[np.argsort(-level[keep, k])][:8]
        print(f"\n[{name}] cells={cluster_size[k]}  total_genes={(N[:,k]>0).sum()}  "
              f"filtered(extent>0.2)={len(keep)}  — top by level:")
        for gi in order:
            print(f"    {gene_sym[gi]:14} {gene_id[gi]:14} level={level[gi,k]:9.1f} extent={extent[gi,k]:.2f}")


if __name__ == "__main__":
    main()
