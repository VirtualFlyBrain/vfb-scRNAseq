"""FlyBase-style summary expression statistics (extent + CPM level) per cluster x gene.

Streams the GEO 10x MatrixMarket (genes x cells) in two chunked passes:
  1. per-cell total counts (for CPM normalisation);
  2. per (gene, cluster): sum of CPM over expressing cells + count of expressing cells.
Then (FlyBase SOP):
  extent = expressing_cells / cluster_cells             (normalisation-invariant)
  level  = mean CPM over EXPRESSING cells = 1e6 * sum(count / cell_total) / expressing
Filter: extent > cutoff (default 0.2, from the old vfb-scRNAseq-ontology repo).

h5ad projects (`expression.source: h5ad`, e.g. the Fly Cell Atlas) store normalised
values, not counts: one file per Clustering, read in one chunked pass; the values are
converted back to CPM (`expression.values`: `log1p_cp10k` -> (e^x - 1) x 100,
`log2_cpm1` -> 2^x - 1) and every cell's CPM total is checked. Files may have different
gene sets; a gene a file lacks is unexpressed in that file's clusters.

Only clusters with an FBbt term are summarised (held clusters are not loaded; their
cells still count towards the dataset-level gene counts, which measure what the
experiment detected).

Memory stays low: the only dense accumulators are genes x clusters. Cluster IRIs
come from the id registry (build must have minted the Cluster ids first).
"""

from __future__ import annotations

import csv
import gzip
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from vfb_scrnaseq.ids import IDRegistry
from vfb_scrnaseq.ingest_h5ad import expression_h5ads, h5ad_path, iter_matrix, matrix_shape, read_genes, read_obs
from vfb_scrnaseq.project_config import mapped_labels

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


def load_gene_id_map(path: Path, key: str = "input_fbgn") -> dict[str, tuple[str, str] | None]:
    """gene_id_map.tsv (scripts/update_gene_ids.py) -> {input fbgn (or `key`, e.g.
    input_symbol for h5ad projects): (current fbgn, current symbol)}, or None for genes
    to drop (split / withdrawn / unmatched)."""
    with path.open() as fh:
        rows = csv.DictReader((ln for ln in fh if not ln.startswith("#")), delimiter="\t")
        return {r[key]: ((r["current_fbgn"], r["current_symbol"]) if r["current_fbgn"] else None)
                for r in rows}


def _remap(keys: list[str], targets: list[tuple[str, str] | None]):
    """Input genes -> output genes: (fbgn, symbol, remap index per input gene (-1 =
    dropped), merged flag per output gene)."""
    fbgn, symbol, idx = [], [], {}
    remap = np.full(len(keys), -1, dtype=np.int64)
    for i, tgt in enumerate(targets):
        if tgt is None:
            continue
        if tgt[0] not in idx:
            idx[tgt[0]] = len(fbgn)
            fbgn.append(tgt[0])
            symbol.append(tgt[1])
        remap[i] = idx[tgt[0]]
    sources = np.bincount(remap[remap >= 0], minlength=len(fbgn))
    return fbgn, symbol, remap, sources > 1


class _Sums:
    """Per (gene, cluster) sums of CPM/1e6 over expressing cells (S) and expressing-cell
    counts (N), with cells assigned to clusters by membership layers (the k-th
    membership of each cell -> layer k; -1 = none)."""

    def __init__(self, n_genes: int, n_clu: int, layers: np.ndarray):
        self.n_genes, self.n_clu, self.layers = n_genes, n_clu, layers
        self.S = np.zeros(n_genes * n_clu, dtype=np.float64)
        self.N = np.zeros(n_genes * n_clu, dtype=np.int64)

    def add(self, g: np.ndarray, c: np.ndarray, w: np.ndarray) -> None:
        for lay in self.layers:
            k = lay[c]
            keep = k >= 0
            flat = g[keep] * self.n_clu + k[keep]
            self.S += np.bincount(flat, weights=w[keep], minlength=self.n_genes * self.n_clu)
            self.N += np.bincount(flat, minlength=self.n_genes * self.n_clu)

    def add_merged(self, g, c, w, n_cells: int) -> None:
        """Entries of merged genes: sum per (gene, cell) first, so a cell expressing
        several input genes of one output gene counts once."""
        key, inv = np.unique(g.astype(np.int64) * n_cells + c, return_inverse=True)
        self.add(key // n_cells, key % n_cells, np.bincount(inv, weights=w))


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
    targets = [(f, in_symbol[i]) if gene_map is None else gene_map.get(f, (f, in_symbol[i]))
               for i, f in enumerate(in_fbgn)]     # ids not in the map are kept as is
    fbgn, symbol, remap, merged = _remap(in_fbgn, targets)
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

    sums = _Sums(n_genes, n_clu, layers)
    held_g, held_c, held_v = [], [], []          # entries of merged genes, summed at the end
    for chunk in _read_chunks(mtx):
        g = remap[chunk.g.values - 1]
        c = chunk.c.values - 1
        v = chunk.v.values
        keep = g >= 0
        g, c, v = g[keep], c[keep], v[keep]
        m = merged[g]
        if m.any():
            held_g.append(g[m]); held_c.append(c[m]); held_v.append(v[m] / col_total[c[m]])
            g, c, v = g[~m], c[~m], v[~m]
        sums.add(g, c, v / col_total[c])
    if held_g:
        sums.add_merged(np.concatenate(held_g), np.concatenate(held_c), np.concatenate(held_v), n_cells)
    S, N = sums.S, sums.N
    cells = {b for j, b in enumerate(barcodes) if (layers[:, j] >= 0).any()}
    return {"fbgn": fbgn, "symbol": symbol, "clusters": clusters, "cluster_size": cluster_size,
            "S": S.reshape(n_genes, n_clu), "N": N.reshape(n_genes, n_clu), "cells": cells}


TO_CPM = {
    "log1p_cp10k": lambda x: np.expm1(x) * 100.0,    # log(counts per 10k + 1)
    "log2_cpm1": lambda x: np.exp2(x) - 1.0,         # log2(CPM + 1)
}


def _accumulate_h5ad(path: Path, labels: list[str | None], values: str,
                     gene_map: dict[str, tuple[str, str] | None], name: str) -> dict:
    """One h5ad file: per (gene, cluster) CPM sums over expressing cells, as
    `_accumulate`. `labels` gives each cell's cluster (None = in none). Genes are keyed
    by name through `gene_map` (symbol -> current gene); every gene must be in it."""
    genes, _ids = read_genes(path)
    missing = [g for g in genes if g not in gene_map]
    if missing:
        raise SystemExit(f"{path.name}: {len(missing)} genes not in the gene id map "
                         f"(re-run scripts/update_gene_ids.py), e.g. {missing[:5]}")
    fbgn, symbol, remap, merged = _remap(genes, [gene_map[g] for g in genes])
    n_cells, n_in = matrix_shape(path)
    if n_in != len(genes) or n_cells != len(labels):
        raise SystemExit(f"{path.name}: matrix {n_cells}x{n_in} vs {len(labels)} cells, {len(genes)} genes")
    clusters = sorted({lab for lab in labels if lab is not None})
    cidx = {c: i for i, c in enumerate(clusters)}
    layer = np.array([cidx[lab] if lab is not None else -1 for lab in labels], dtype=np.int32)
    cluster_size = np.bincount(layer[layer >= 0], minlength=len(clusters)).astype(np.int64)
    to_cpm = TO_CPM[values]

    sums = _Sums(len(fbgn), len(clusters), layer[None, :])
    cell_total = np.zeros(n_cells, dtype=np.float64)
    held_g, held_c, held_w = [], [], []
    for gi, ci, v in iter_matrix(path):
        w = to_cpm(v)
        cell_total += np.bincount(ci, weights=w, minlength=n_cells)
        g = remap[gi]
        keep = (g >= 0) & (w > 0)
        g, c, w = g[keep], ci[keep], w[keep] / 1e6
        m = merged[g]
        if m.any():
            held_g.append(g[m]); held_c.append(c[m]); held_w.append(w[m])
            g, c, w = g[~m], c[~m], w[~m]
        sums.add(g, c, w)
    if held_g:
        sums.add_merged(np.concatenate(held_g), np.concatenate(held_c), np.concatenate(held_w), n_cells)
    # the conversion is right only if cells' CPM sums to 1e6: never more, and the median
    # cell at 1e6. Some cells may sum to less where the authors normalised before
    # dropping genes (e.g. FCA Smart-seq2 dilp2IPC); those values are still CPM.
    med, lo, hi = np.median(cell_total), cell_total.min(), cell_total.max()
    if not (0.99e6 <= med <= 1.001e6) or hi > 1.001e6:
        raise SystemExit(f"{path.name}: per-cell CPM totals median {med:.0f} (range {lo:.0f}-{hi:.0f}), "
                         f"not 1e6; check expression.values ({values})")
    note = f"; lowest cell CPM total {lo:.0f} (genes dropped after normalisation)" if lo < 0.95e6 else ""
    return {"fbgn": fbgn, "symbol": symbol, "clusters": clusters, "cluster_size": cluster_size,
            "S": sums.S.reshape(len(fbgn), len(clusters)), "N": sums.N.reshape(len(fbgn), len(clusters)),
            "cells": {f"{name}:{i}" for i in np.flatnonzero(layer >= 0)}, "note": note}


def _h5ad_parts(project: str, cfg: dict, gene_map) -> list[dict]:
    """One part per Clustering h5ad; a cell's cluster is `<clustering>_<annotation>`
    (or the clustering's `fixed_annotation`), as build_annotations_from_h5ad.py labels
    them. Cluster sizes are checked against cell_type_annotations.json."""
    acc = cfg["dataset"]["accession"]
    col = (cfg.get("annotation_build") or {}).get("annotation_column")
    proj = REPO_ROOT / "projects" / project
    expected = {a["label"]: a["cell_number"] for a in
                json.loads((proj / "cell_type_annotations.json").read_text())["annotations"]}
    parts = []
    ex = cfg["expression"]
    if ex.get("h5ad_files"):
        # files holding several Clusterings: each cell's cluster from the membership file
        with gzip.open(REPO_ROOT / ".cache" / ex["membership_file"], "rt") as fh:
            member = {r["barcode"]: r["cluster"] for r in csv.DictReader(fh, delimiter="\t")}
        for path in expression_h5ads(cfg):
            labels = [member.get(cell) for cell in read_obs(path, [])["_index"]]
            part = _accumulate_h5ad(path, labels, ex["values"], gene_map, path.stem)
            for lab, size in zip(part["clusters"], part["cluster_size"]):
                if expected.get(lab) != int(size):
                    raise SystemExit(f"{lab}: {size} cells in {path.name}, "
                                     f"{expected.get(lab)} in cell_type_annotations.json")
            print(f"    {path.name}: {sum(lab is not None for lab in labels)} cells, "
                  f"{len(part['clusters'])} clusters, {len(part['fbgn'])} genes{part['note']}")
            parts.append(part)
        return parts
    for c in cfg["sample_build"]["clusterings"]:
        path = h5ad_path(acc, c["id"])
        if c.get("fixed_annotation"):
            n = len(read_obs(path, [])["_index"])
            labels = [f"{c['id']}_{c['fixed_annotation']}"] * n
        else:
            labels = [f"{c['id']}_{a}" if a is not None else None for a in read_obs(path, [col])[col]]
        part = _accumulate_h5ad(path, labels, cfg["expression"]["values"], gene_map, c["id"])
        for lab, size in zip(part["clusters"], part["cluster_size"]):
            if expected.get(lab) != int(size):
                raise SystemExit(f"{lab}: {size} cells in {path.name}, "
                                 f"{expected.get(lab)} in cell_type_annotations.json")
        print(f"    {c['id']}: {len(labels)} cells, {len(part['clusters'])} clusters, "
              f"{len(part['fbgn'])} genes{part['note']}")
        parts.append(part)
    return parts


def _union_genes(parts: list[dict]) -> tuple[list[str], list[str], np.ndarray, np.ndarray]:
    """Combine parts with (possibly) different gene lists: (fbgn, symbol, S, N) over the
    union of genes, a part's clusters having zero for genes its file lacks."""
    gidx: dict[str, int] = {}
    fbgn, symbol = [], []
    for p in parts:
        for f, s in zip(p["fbgn"], p["symbol"]):
            if f not in gidx:
                gidx[f] = len(fbgn)
                fbgn.append(f)
                symbol.append(s)
    n_clu = sum(len(p["clusters"]) for p in parts)
    S = np.zeros((len(fbgn), n_clu))
    N = np.zeros((len(fbgn), n_clu), dtype=np.int64)
    k = 0
    for p in parts:
        rows = np.array([gidx[f] for f in p["fbgn"]], dtype=np.int64)
        w = len(p["clusters"])
        S[rows, k:k + w] = p["S"]
        N[rows, k:k + w] = p["N"]
        k += w
    return fbgn, symbol, S, N


def compute_expression(project: str, cfg: dict):
    """Return (rows, counts, meta).

    rows: list of (cluster_vfbseq_id, cluster_label, fbgn, symbol, level, extent)
          for cluster x gene with extent > cutoff, sorted by (label, fbgn).
    counts: list[ClusterCount] per cluster.
    meta: dict with n_genes, n_cells, cutoff, normalisation, dataset gene counts and
          the held clusters left out (held_clusters, held_cells).
    """
    acc = cfg["dataset"]["accession"]
    subset = (cfg.get("annotations") or {}).get("subset", "main")
    ex = cfg["expression"]
    cutoff = float(ex.get("extent_cutoff", 0.2))
    cache = REPO_ROOT / ".cache"
    if ex.get("source") == "h5ad":
        gene_map = load_gene_id_map(REPO_ROOT / "projects" / project / ex["gene_id_map"], key="input_symbol")
        parts = _h5ad_parts(project, cfg, gene_map)
    else:
        parts = _mtx_parts(project, cfg, cache)
    return _summarise(parts, acc, subset, cutoff, ex, mapped_labels(REPO_ROOT / "projects" / project))


def _mtx_parts(project: str, cfg: dict, cache: Path) -> list[dict]:
    label_col = cfg["annotations"].get("label_column")    # not needed with a membership_file
    ex = cfg["expression"]

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
    # current FlyBase gene ids (`expression.gene_id_map`, from scripts/update_gene_ids.py);
    # keyed by symbol when the features files carry symbols only
    # (`expression.features_keyed_by: symbol`)
    # (`expression.features_keyed_by: symbol`) or annotation ids (`annotation_id`)
    key = "input_symbol" if ex.get("features_keyed_by") in ("symbol", "annotation_id") else "input_fbgn"
    gene_map = (load_gene_id_map(REPO_ROOT / "projects" / project / ex["gene_id_map"], key=key)
                if ex.get("gene_id_map") else None)
    parts = [_accumulate(cache / ex["matrix_file"], cache / ex["features_file"],
                         cache / ex["barcodes_file"], memberships, gene_map)]
    # further matrices (`expression.extra_parts`, e.g. a separately clustered early
    # dataset): same genes, own cells; cluster labels get the part's label_prefix
    for part in ex.get("extra_parts", []):
        if part.get("membership_file"):     # barcode<TAB>cluster: overlapping clusterings
            pm = {}
            with gzip.open(cache / part["membership_file"], "rt") as fh:
                for r in csv.DictReader(fh, delimiter="\t"):
                    pm.setdefault(r["barcode"], []).append(r["cluster"])
        else:
            pm = _label_memberships(cache / part["metadata_file"],
                                    cfg["annotations"].get("barcode_column", "barcode"),
                                    label_col, prefix=part.get("label_prefix", ""))
        parts.append(_accumulate(cache / part["matrix_file"], cache / part["features_file"],
                                 cache / part["barcodes_file"], pm, gene_map))
    return parts


def _summarise(parts: list[dict], acc: str, subset: str, cutoff: float, ex: dict,
               keep: set[str] | None = None):
    """`keep`: labels of the clusters to summarise (default all)."""
    fbgn, symbol, S, N = _union_genes(parts)
    n_genes = len(fbgn)
    clusters = [c for p in parts for c in p["clusters"]]
    if len(set(clusters)) != len(clusters):
        raise SystemExit("cluster labels repeat across expression parts; set a label_prefix")
    cluster_size = np.concatenate([p["cluster_size"] for p in parts])
    # distinct cells within a part (a cell may be in several of its clusters); parts are
    # separate matrices, so their cells add up even where barcodes repeat between them
    n_cells = sum(len(p["cells"]) for p in parts)
    # dataset-level gene counts, matching the old repo's get_gene_counts: distinct
    # genes over the per-cluster x gene expression (union across clusters, NOT a
    # dataset-wide extent). total = genes expressed in any cluster; filtered = genes
    # with extent > cutoff in at least one cluster. Over ALL clusters, held ones
    # included: the genes were detected whether or not their cluster is loaded.
    with np.errstate(divide="ignore", invalid="ignore"):
        all_extent = N / cluster_size[None, :]
    dataset_total_gene_count = int((N > 0).any(axis=1).sum())
    dataset_filtered_gene_count = int((all_extent > cutoff).any(axis=1).sum())

    held_clusters = held_cells = 0
    if keep is not None:
        cols = [i for i, c in enumerate(clusters) if c in keep]
        held_clusters = len(clusters) - len(cols)
        held_cells = int(cluster_size.sum() - cluster_size[cols].sum())
        clusters = [clusters[i] for i in cols]
        cluster_size, S, N = cluster_size[cols], S[:, cols], N[:, cols]
    cidx = {c: i for i, c in enumerate(clusters)}
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

    meta = {"n_genes": n_genes, "n_cells": n_cells, "cutoff": cutoff,
            "normalisation": ex.get("normalisation", "CPM"),
            "dataset_total_gene_count": dataset_total_gene_count,
            "dataset_filtered_gene_count": dataset_filtered_gene_count,
            "held_clusters": held_clusters, "held_cells": held_cells}
    return out_rows, counts, meta
