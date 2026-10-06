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


def _label_memberships(meta_f: Path, bc_col: str, label_col: str, prefix: str = "") -> dict[str, list[str]]:
    with gzip.open(meta_f, "rt") as fh:
        return {r[bc_col]: [prefix + r[label_col]] for r in csv.DictReader(fh, delimiter="\t")}


def load_gene_id_map(path: Path) -> dict[str, tuple[str, str] | None]:
    """gene_id_map.tsv (scripts/update_gene_ids.py) -> {input fbgn: (current fbgn,
    current symbol)}, or None for ids to drop (split / withdrawn)."""
    with path.open() as fh:
        rows = csv.DictReader((ln for ln in fh if not ln.startswith("#")), delimiter="\t")
        return {r["input_fbgn"]: ((r["current_fbgn"], r["current_symbol"]) if r["current_fbgn"] else None)
                for r in rows}


def _accumulate(mtx: Path, feats: Path, bcs: Path, memberships: dict[str, list[str]],
                gene_map: dict[str, tuple[str, str] | None] | None = None) -> dict:
    """Stream one 10x matrix: per (gene, cluster) CPM sums over expressing cells (S),
    expressing-cell counts (N) and cluster sizes, for the clusters in `memberships`.

    With `gene_map`, input genes are remapped to current FlyBase genes as the matrix
    streams: retired ids -> their current gene, unmappable ids dropped, and genes that
    several input ids now map to (merges) have their counts summed per cell before
    extent/level are taken. CPM still uses each cell's full library size."""
    with gzip.open(feats, "rt") as fh:
        rows = [ln.rstrip("\n").split("\t") for ln in fh]
    in_fbgn = [r[0] for r in rows]
    in_symbol = [r[1] if len(r) > 1 else r[0] for r in rows]
    if gene_map is None:
        fbgn, symbol = in_fbgn, in_symbol
        remap = np.arange(len(in_fbgn), dtype=np.int64)
        merged = np.zeros(len(fbgn), dtype=bool)
    else:
        fbgn, symbol, idx = [], [], {}
        remap = np.full(len(in_fbgn), -1, dtype=np.int64)
        for i, f in enumerate(in_fbgn):
            tgt = gene_map.get(f, (f, in_symbol[i]))   # ids not in the map are kept as is
            if tgt is None:
                continue
            if tgt[0] not in idx:
                idx[tgt[0]] = len(fbgn)
                fbgn.append(tgt[0])
                symbol.append(tgt[1])
            remap[i] = idx[tgt[0]]
        sources = np.bincount(remap[remap >= 0], minlength=len(fbgn))
        merged = sources > 1
    with gzip.open(bcs, "rt") as fh:
        barcodes = [ln.strip() for ln in fh]

    _, _, n_cells, _ = _open_mtx(mtx)
    n_genes = len(fbgn)
    clusters = sorted({c for b in barcodes for c in memberships.get(b, [])})
    cidx = {c: i for i, c in enumerate(clusters)}
    n_clu = len(clusters)
    # layers: the k-th membership of each cell -> layer k, so within a layer a cell has
    # at most one cluster (-1 = none) and the bincount accumulation stays vectorised
    n_layers = max((len(memberships.get(b, [])) for b in barcodes), default=0)
    layers = np.full((n_layers, n_cells), -1, dtype=np.int32)
    for j, b in enumerate(barcodes):
        for k, c in enumerate(memberships.get(b, [])):
            layers[k, j] = cidx[c]
    cluster_size = np.zeros(n_clu, dtype=np.int64)
    for lay in layers:
        cluster_size += np.bincount(lay[lay >= 0], minlength=n_clu)

    col_total = np.zeros(n_cells, dtype=np.float64)
    for chunk in _read_chunks(mtx):
        col_total += np.bincount(chunk.c.values - 1, weights=chunk.v.values, minlength=n_cells)

    S = np.zeros(n_genes * n_clu, dtype=np.float64)
    N = np.zeros(n_genes * n_clu, dtype=np.int64)

    def add(g, c, v):
        w = v / col_total[c]
        for lay in layers:
            k = lay[c]
            keep = k >= 0
            flat = g[keep] * n_clu + k[keep]
            S[:] += np.bincount(flat, weights=w[keep], minlength=n_genes * n_clu)
            N[:] += np.bincount(flat, minlength=n_genes * n_clu)

    held_g, held_c, held_v = [], [], []          # entries of merged genes, summed at the end
    for chunk in _read_chunks(mtx):
        g = remap[chunk.g.values - 1]
        c = chunk.c.values - 1
        v = chunk.v.values
        keep = g >= 0
        g, c, v = g[keep], c[keep], v[keep]
        m = merged[g]
        if m.any():
            held_g.append(g[m]); held_c.append(c[m]); held_v.append(v[m])
            g, c, v = g[~m], c[~m], v[~m]
        add(g, c, v)
    if held_g:
        g = np.concatenate(held_g); c = np.concatenate(held_c); v = np.concatenate(held_v)
        key, inv = np.unique(g.astype(np.int64) * n_cells + c, return_inverse=True)
        add(key // n_cells, key % n_cells, np.bincount(inv, weights=v))
    cells = {b for j, b in enumerate(barcodes) if (layers[:, j] >= 0).any()}
    return {"fbgn": fbgn, "symbol": symbol, "clusters": clusters, "cluster_size": cluster_size,
            "S": S.reshape(n_genes, n_clu), "N": N.reshape(n_genes, n_clu), "cells": cells}


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

    # cell -> cluster(s). Default: one cluster per cell from the metadata label column.
    # `expression.membership_file` (barcode<TAB>cluster, in .cache) instead allows a
    # cell to belong to clusters of several (overlapping) clusterings.
    memberships: dict[str, list[str]] = {}
    if ex.get("membership_file"):
        with gzip.open(cache / ex["membership_file"], "rt") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                memberships.setdefault(r["barcode"], []).append(r["cluster"])
    else:
        # the per-cell id column must match the matrix barcodes file (default
        # "barcode"; e.g. Davie 2018 needs the sample-suffixed "new_barcode").
        memberships = _label_memberships(cache / cfg["annotations"]["source_file"],
                                         cfg["annotations"].get("barcode_column", "barcode"),
                                         label_col, prefix=cfg["annotations"].get("label_prefix", ""))
    # current FlyBase gene ids (`expression.gene_id_map`, from scripts/update_gene_ids.py)
    gene_map = (load_gene_id_map(REPO_ROOT / "projects" / project / ex["gene_id_map"])
                if ex.get("gene_id_map") else None)
    parts = [_accumulate(cache / ex["matrix_file"], cache / ex["features_file"],
                         cache / ex["barcodes_file"], memberships, gene_map)]
    # further matrices (`expression.extra_parts`, e.g. a separately clustered early
    # dataset): same genes, own cells; cluster labels get the part's label_prefix
    for part in ex.get("extra_parts", []):
        pm = _label_memberships(cache / part["metadata_file"],
                                cfg["annotations"].get("barcode_column", "barcode"),
                                label_col, prefix=part.get("label_prefix", ""))
        parts.append(_accumulate(cache / part["matrix_file"], cache / part["features_file"],
                                 cache / part["barcodes_file"], pm, gene_map))
    fbgn, symbol = parts[0]["fbgn"], parts[0]["symbol"]
    for p in parts[1:]:
        if p["fbgn"] != fbgn:
            raise SystemExit("expression parts have different feature lists; cannot combine")
    n_genes = len(fbgn)
    clusters = [c for p in parts for c in p["clusters"]]
    if len(set(clusters)) != len(clusters):
        raise SystemExit("cluster labels repeat across expression parts; set a label_prefix")
    cidx = {c: i for i, c in enumerate(clusters)}
    cluster_size = np.concatenate([p["cluster_size"] for p in parts])
    S = np.concatenate([p["S"] for p in parts], axis=1)
    N = np.concatenate([p["N"] for p in parts], axis=1)
    n_cells = len(set().union(*(p["cells"] for p in parts)))
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

    meta = {"n_genes": n_genes, "n_cells": n_cells, "cutoff": cutoff,
            "normalisation": ex.get("normalisation", "CPM"),
            "dataset_total_gene_count": dataset_total_gene_count,
            "dataset_filtered_gene_count": dataset_filtered_gene_count}
    return out_rows, counts, meta
