"""Read cell metadata (obs) from AnnData .h5ad files with h5py — no anndata/scanpy.

Handles the three on-disk layouts of `obs`:

- **old** (anndata < 0.7): `obs` is a compound dataset; a categorical column stores
  integer codes and its categories live in `uns/<column>_categories`;
- **0.7** : `obs` is a group of 1-D datasets; categories in `obs/__categories/<column>`;
- **0.8+** (encoding-type `dataframe`): a categorical column is a group with
  `categories` and `codes`.

Codes of -1 (missing) become None. Values are returned as str (numbers are kept as
their Python value).
"""

from __future__ import annotations

from pathlib import Path

import h5py
import numpy as np


def _str(v):
    return v.decode("utf-8") if isinstance(v, bytes) else v


def _decode(codes: np.ndarray, categories) -> list:
    cats = [_str(c) for c in categories[()]]
    return [cats[c] if c >= 0 else None for c in codes]


def _plain(arr: np.ndarray) -> list:
    return [_str(v) if isinstance(v, bytes) else v.item() if hasattr(v, "item") else v for v in arr]


def obs_columns(path: Path) -> list[str]:
    with h5py.File(path, "r") as f:
        obs = f["obs"]
        if isinstance(obs, h5py.Dataset):
            return [n for n in obs.dtype.names if n != "index"]
        order = obs.attrs.get("column-order")
        return [_str(c) for c in order] if order is not None else \
            [k for k in obs.keys() if not k.startswith("__") and k != "_index"]


def read_obs(path: Path, columns: list[str]) -> dict[str, list]:
    """{column: [value per cell]} for the requested obs columns (plus `_index`, the
    cell barcodes)."""
    out: dict[str, list] = {}
    with h5py.File(path, "r") as f:
        obs = f["obs"]
        if isinstance(obs, h5py.Dataset):                                   # old layout
            data = obs[()]
            out["_index"] = _plain(data["index"])
            for c in columns:
                cat = f.get(f"uns/{c}_categories")
                out[c] = _decode(data[c], cat) if cat is not None else _plain(data[c])
            return out
        idx = _str(obs.attrs.get("_index", "_index"))
        out["_index"] = _plain(obs[idx][()])
        for c in columns:
            node = obs[c]
            if isinstance(node, h5py.Group):                                # 0.8+ categorical
                out[c] = _decode(node["codes"][()], node["categories"])
            elif "__categories" in obs and c in obs["__categories"]:        # 0.7 categorical
                out[c] = _decode(node[()], obs["__categories"][c])
            else:
                out[c] = _plain(node[()])
    return out
