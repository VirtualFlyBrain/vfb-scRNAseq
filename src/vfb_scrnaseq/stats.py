"""FlyBase-style summary expression statistics (extent + CPM level) per cluster x gene.

Streams the GEO 10x MatrixMarket (genes x cells) in two chunked passes:
  1. per-cell total counts (for CPM normalisation);
  2. per (gene, cluster): sum of CPM over expressing cells + count of expressing cells.
Then (FlyBase SOP):
  extent = expressing_cells / cluster_cells             (normalisation-invariant)
  level  = mean CPM over EXPRESSING cells = 1e6 * sum(count / cell_total) / expressing
Filter: extent > cutoff (default 0.2, from the old vfb-scRNAseq-ontology repo).

Memory stays low: the only dense accumulators are genes x clusters. Cluster IRIs
come from the id registry (build must have minted the Cluster ids first).
"""

from __future__ import annotations

import csv
import gzip
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from vfb_scrnaseq.ids import IDRegistry

REPO_ROOT = Path(__file__).resolve().parents[2]
CHUNK = 5_000_000


@dataclass
class ClusterCount:
    label: str
    vfbseq_id: str
    cells: int
    total_gene_count: int      # genes with any expression (extent > 0)
    filtered_gene_count: int   # genes with extent > cutoff


def _open_mtx(path: Path):
    fh = gzip.open(path, "rt")
    line = fh.readline()
    while line.startswith("%"):
        line = fh.readline()
    n_genes, n_cells, nnz = (int(x) for x in line.split())
    return fh, n_genes, n_cells, nnz


def _read_chunks(path: Path):
    fh, *_ = _open_mtx(path)
    yield from pd.read_csv(fh, sep=r"\s+", header=None, names=["g", "c", "v"],
                           chunksize=CHUNK, dtype={"g": np.int32, "c": np.int32, "v": np.float64})
    fh.close()


def compute_expression(project: str, cfg: dict):
    """Return (rows, counts, meta).

    rows: list of (cluster_vfbseq_id, cluster_label, fbgn, symbol, level, extent)
          for cluster x gene with extent > cutoff, sorted by (label, fbgn).
    counts: list[ClusterCount] per cluster.
    meta: dict with n_genes, n_cells, cutoff, normalisation.
    """
    acc = cfg["dataset"]["accession"]
    subset = cfg["annotations"].get("subset", "main")
    label_col = cfg["annotations"]["label_column"]
    ex = cfg["expression"]
    cutoff = float(ex.get("extent_cutoff", 0.2))
    cache = REPO_ROOT / ".cache"
    mtx = cache / ex["matrix_file"]
    feats = cache / ex["features_file"]
    bcs = cache / ex["barcodes_file"]
    meta_f = cache / cfg["annotations"]["source_file"]

    with gzip.open(feats, "rt") as fh:
        rows = [ln.rstrip("\n").split("\t") for ln in fh]
    fbgn = [r[0] for r in rows]
    symbol = [r[1] if len(r) > 1 else r[0] for r in rows]
    with gzip.open(bcs, "rt") as fh:
        barcodes = [ln.strip() for ln in fh]
    with gzip.open(meta_f, "rt") as fh:
        bc2cluster = {r["barcode"]: r[label_col] for r in csv.DictReader(fh, delimiter="\t")}

    _, n_genes, n_cells, _ = _open_mtx(mtx)
    clusters = sorted(set(bc2cluster.values()))
    cidx = {c: i for i, c in enumerate(clusters)}
    n_clu = len(clusters)
    col_cluster = np.array([cidx[bc2cluster[b]] for b in barcodes], dtype=np.int32)
    cluster_size = np.bincount(col_cluster, minlength=n_clu).astype(np.int64)

    col_total = np.zeros(n_cells, dtype=np.float64)
    for chunk in _read_chunks(mtx):
        col_total += np.bincount(chunk.c.values - 1, weights=chunk.v.values, minlength=n_cells)

    S = np.zeros(n_genes * n_clu, dtype=np.float64)
    N = np.zeros(n_genes * n_clu, dtype=np.int64)
    for chunk in _read_chunks(mtx):
        c = chunk.c.values - 1
        flat = (chunk.g.values - 1) * n_clu + col_cluster[c]
        S += np.bincount(flat, weights=chunk.v.values / col_total[c], minlength=n_genes * n_clu)
        N += np.bincount(flat, minlength=n_genes * n_clu)
    S = S.reshape(n_genes, n_clu)
    N = N.reshape(n_genes, n_clu)
    with np.errstate(divide="ignore", invalid="ignore"):
        extent = N / cluster_size[None, :]
        level = np.where(N > 0, 1e6 * S / N, 0.0)

    reg = IDRegistry.load(REPO_ROOT / "id_registry" / "registry.json")
    cluster_iri = {}
    for lab in clusters:
        cid = reg.get("Cluster", f"{acc}:{subset}:{lab}")
        if cid is None:
            raise SystemExit(f"No minted Cluster id for {lab!r}; run build_rdf first (mints Cluster ids).")
        cluster_iri[lab] = cid

    # filtered rows, sorted for stable diffs
    gi, ki = np.where(extent > cutoff)
    order = np.lexsort((np.array(fbgn)[gi], np.array(clusters)[ki]))  # by (label, fbgn)
    out_rows = [
        (cluster_iri[clusters[ki[j]]], clusters[ki[j]], fbgn[gi[j]], symbol[gi[j]],
         round(float(level[gi[j], ki[j]]), 3), round(float(extent[gi[j], ki[j]]), 4))
        for j in order
    ]

    counts = [ClusterCount(lab, cluster_iri[lab], int(cluster_size[k]),
                           int((N[:, k] > 0).sum()), int((extent[:, k] > cutoff).sum()))
              for lab, k in cidx.items()]
    counts.sort(key=lambda c: c.label)

    # dataset-level gene counts, matching the old repo's get_gene_counts: distinct
    # genes over the per-cluster x gene expression (union across clusters, NOT a
    # dataset-wide extent). total = genes expressed in any cluster; filtered = genes
    # with extent > cutoff in at least one cluster (== distinct genes in expression.tsv).
    dataset_total_gene_count = int((N > 0).any(axis=1).sum())
    dataset_filtered_gene_count = int((extent > cutoff).any(axis=1).sum())

    meta = {"n_genes": n_genes, "n_cells": int(cluster_size.sum()), "cutoff": cutoff,
            "normalisation": ex.get("normalisation", "CPM"),
            "dataset_total_gene_count": dataset_total_gene_count,
            "dataset_filtered_gene_count": dataset_filtered_gene_count}
    return out_rows, counts, meta
