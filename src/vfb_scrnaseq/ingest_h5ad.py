"""Read AnnData .h5ad files with h5py — no anndata/scanpy.

Cell metadata (`obs`) and gene metadata (`var`, `raw/var`) in the three on-disk
layouts:

- **old** (anndata < 0.7): the frame is a compound dataset; a categorical column stores
  integer codes and its categories live in `uns/<column>_categories` (for `raw.var`:
  `raw.cat/<column>_categories`); `raw` is stored as `raw.X` / `raw.var`;
- **0.7** : the frame is a group of 1-D datasets; categories in `<frame>/__categories/<column>`;
- **0.8+** (encoding-type `dataframe`): a categorical column is a group with
  `categories` and `codes`.

Codes of -1 (missing) become None. Values are returned as str (numbers are kept as
their Python value). A categorical column whose categories were not saved (seen in
some 0.7 `raw/var` frames) comes back as its integer codes.

The expression matrix (`X`, or `raw.X` / `raw/X`) is read in chunks of non-zero
entries (`iter_matrix`), whether stored dense, CSR or CSC.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import h5py
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
CHUNK = 5_000_000          # non-zero entries per chunk (iter_matrix)


def h5ad_path(accession: str, clustering_id: str) -> Path:
    """Where scripts/fetch_h5ad.py puts a clustering's h5ad."""
    return REPO_ROOT / ".cache" / "h5ad" / accession / f"{clustering_id}.h5ad"


def expression_h5ads(cfg: dict) -> list[Path]:
    """The h5ad files an h5ad-sourced expression build reads: `expression.h5ad_files`
    (paths in .cache, when one file holds several Clusterings and cells are assigned by
    `expression.membership_file`), else one per Clustering (scripts/fetch_h5ad.py)."""
    files = (cfg.get("expression") or {}).get("h5ad_files")
    if files:
        return [REPO_ROOT / ".cache" / f for f in files]
    acc = cfg["dataset"]["accession"]
    return [h5ad_path(acc, c["id"]) for c in cfg["sample_build"]["clusterings"]]


def _str(v):
    return v.decode("utf-8") if isinstance(v, bytes) else v


def _decode(codes: np.ndarray, categories) -> list:
    cats = [_str(c) for c in categories[()]]
    return [cats[c] if c >= 0 else None for c in codes]


def _plain(arr: np.ndarray) -> list:
    return [_str(v) if isinstance(v, bytes) else v.item() if hasattr(v, "item") else v for v in arr]


def _frame(f: h5py.File, frame: str):
    """(frame node, where old-layout categories live) for 'obs', 'var' or 'raw/var'."""
    if frame == "raw/var" and "raw.var" in f:
        return f["raw.var"], "raw.cat"
    return f[frame], "uns"


def obs_columns(path: Path) -> list[str]:
    with h5py.File(path, "r") as f:
        obs = f["obs"]
        if isinstance(obs, h5py.Dataset):
            return [n for n in obs.dtype.names if n != "index"]
        order = obs.attrs.get("column-order")
        return [_str(c) for c in order] if order is not None else \
            [k for k in obs.keys() if not k.startswith("__") and k != "_index"]


def read_frame(path: Path, frame: str, columns: list[str]) -> dict[str, list]:
    """{column: [value per row]} for the requested columns of `frame` ('obs', 'var' or
    'raw/var'), plus `_index` (the row names). Columns the frame lacks are left out."""
    out: dict[str, list] = {}
    with h5py.File(path, "r") as f:
        node, old_cats = _frame(f, frame)
        if isinstance(node, h5py.Dataset):                                  # old layout
            data = node[()]
            out["_index"] = _plain(data["index"])
            for c in columns:
                if c not in data.dtype.names:
                    continue
                cat = f.get(f"{old_cats}/{c}_categories")
                out[c] = _decode(data[c], cat) if cat is not None else _plain(data[c])
            return out
        idx = _str(node.attrs.get("_index", "_index"))
        out["_index"] = _plain(node[idx][()])
        for c in columns:
            if c not in node:
                continue
            col = node[c]
            if isinstance(col, h5py.Group):                                 # 0.8+ categorical
                out[c] = _decode(col["codes"][()], col["categories"])
            elif "__categories" in node and c in node["__categories"]:      # 0.7 categorical
                out[c] = _decode(col[()], node["__categories"][c])
            else:
                out[c] = _plain(col[()])
    return out


def read_obs(path: Path, columns: list[str]) -> dict[str, list]:
    """{column: [value per cell]} for the requested obs columns (plus `_index`, the
    cell barcodes)."""
    return read_frame(path, "obs", columns)


def _has_raw(f: h5py.File) -> bool:
    return "raw.X" in f or "raw" in f


def read_genes(path: Path, use_raw: bool = True) -> tuple[list[str], list[str | None]]:
    """(gene names, FlyBase gene id per gene or None) for the matrix `iter_matrix`
    reads: `raw` when present and `use_raw`, else `X`. Ids come from a `ID` column
    when it holds FBgn ids (it is absent, or undecodable, in some files)."""
    with h5py.File(path, "r") as f:
        frame = "raw/var" if use_raw and _has_raw(f) else "var"
    v = read_frame(path, frame, ["ID"])
    ids = [i if isinstance(i, str) and i.startswith("FBgn") else None
           for i in v.get("ID", [None] * len(v["_index"]))]
    return [str(g) for g in v["_index"]], ids


def _matrix(f: h5py.File, use_raw: bool):
    if use_raw and "raw.X" in f:
        return f["raw.X"]
    if use_raw and "raw" in f:
        return f["raw/X"]
    return f["X"]


def matrix_shape(path: Path, use_raw: bool = True) -> tuple[int, int]:
    """(cells, genes) of the matrix `iter_matrix` reads."""
    with h5py.File(path, "r") as f:
        m = _matrix(f, use_raw)
        if isinstance(m, h5py.Dataset):
            return tuple(m.shape)
        shape = m.attrs.get("h5sparse_shape", m.attrs.get("shape"))
        return int(shape[0]), int(shape[1])


def iter_matrix(path: Path, use_raw: bool = True, chunk: int = CHUNK
                ) -> Iterator[tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """Yield (gene index, cell index, value) arrays over the non-zero entries of the
    cells x genes matrix (`raw` when present and `use_raw`, else `X`), a chunk at a
    time, so large files are never loaded whole."""
    with h5py.File(path, "r") as f:
        m = _matrix(f, use_raw)
        if isinstance(m, h5py.Dataset):                                     # dense
            n_cells, n_genes = m.shape
            step = max(1, chunk // max(n_genes, 1))
            for a in range(0, n_cells, step):
                block = m[a:a + step]
                c, g = np.nonzero(block)
                yield g.astype(np.int64), (c + a).astype(np.int64), block[c, g].astype(np.float64)
            return
        fmt = _str(m.attrs.get("h5sparse_format") or m.attrs.get("encoding-type", ""))
        if fmt.startswith("csc"):
            major_is_gene = True
        elif fmt.startswith("csr"):
            major_is_gene = False
        else:
            raise ValueError(f"{path}: unknown sparse format {fmt!r}")
        indptr = m["indptr"][()]
        n_major = len(indptr) - 1
        a = 0
        while a < n_major:
            # extend the block of major rows until it holds ~chunk entries
            b = int(np.searchsorted(indptr, indptr[a] + chunk, side="right")) - 1
            b = min(max(b, a + 1), n_major)
            lo, hi = int(indptr[a]), int(indptr[b])
            minor = m["indices"][lo:hi].astype(np.int64)
            major = np.repeat(np.arange(a, b, dtype=np.int64), np.diff(indptr[a:b + 1]))
            vals = m["data"][lo:hi].astype(np.float64)
            yield (major, minor, vals) if major_is_gene else (minor, major, vals)
            a = b
