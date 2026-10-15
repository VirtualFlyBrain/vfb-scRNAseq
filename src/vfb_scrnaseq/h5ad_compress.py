"""Lossless HDF5 gzip compression of cached .h5ad files, verified before use.

Authors' AnnData files are often stored uncompressed (several GB). Recompressing
every non-trivial dataset with HDF5's own gzip filter (+ shuffle for numbers) keeps
them readable as they are — h5py decompresses transparently, so nothing in the
pipeline changes — at a third of the size or less.

`compress(src, dst)` writes the copy, then compares it with the source dataset by
dataset (values, dtype, shape, attributes; object-reference attributes, as in the
AnnData 0.7 layout, are re-pointed and compared by target path) and raises
`CompressionMismatch` (removing the copy) if anything differs.
"""

from __future__ import annotations

import os
from pathlib import Path

import h5py
import numpy as np

BLOCK = 1 << 24          # elements copied / compared per slice
MIN_SIZE = 1024          # datasets smaller than this are left uncompressed


class CompressionMismatch(RuntimeError):
    pass


def is_compressed(path: Path) -> bool:
    """True if every non-trivial dataset in the file already uses a compression filter."""
    found = []

    def visit(_name, obj):
        if isinstance(obj, h5py.Dataset) and obj.shape and obj.size > MIN_SIZE:
            found.append(obj.compression is not None)
    with h5py.File(path, "r") as f:
        f.visititems(visit)
    return all(found)


def _rows_per_block(shape: tuple[int, ...]) -> int:
    per_row = int(np.prod(shape[1:])) if len(shape) > 1 else 1
    return max(1, BLOCK // max(1, per_row))


def _copy_attrs(sobj, dobj, refs: list) -> None:
    for k, v in sobj.attrs.items():
        if isinstance(v, h5py.Reference):
            refs.append((dobj.name, k, sobj.file[v].name))   # re-pointed after the copy
        else:
            dobj.attrs[k] = v


def _copy(src: h5py.Group, dst: h5py.Group, refs: list) -> None:
    _copy_attrs(src, dst, refs)
    for name, obj in src.items():
        if isinstance(obj, h5py.Group):
            _copy(obj, dst.create_group(name), refs)
            continue
        kw = {}
        if obj.shape and obj.size > MIN_SIZE:
            kw = dict(compression="gzip", compression_opts=4, chunks=True,
                      shuffle=obj.dtype.kind in "iuf")
        d = dst.create_dataset(name, shape=obj.shape, dtype=obj.dtype, **kw)
        if obj.shape:
            step = _rows_per_block(obj.shape)
            for a in range(0, obj.shape[0], step):
                d[a:a + step] = obj[a:a + step]
        else:
            d[()] = obj[()]
        _copy_attrs(obj, d, refs)


def _differs(a, b, path: str = "/") -> str | None:
    if set(a.attrs.keys()) != set(b.attrs.keys()):
        return f"{path}: attribute names"
    for k in a.attrs:
        x, y = a.attrs[k], b.attrs[k]
        if isinstance(x, h5py.Reference) or isinstance(y, h5py.Reference):
            if not (isinstance(x, h5py.Reference) and isinstance(y, h5py.Reference)
                    and a.file[x].name == b.file[y].name):
                return f"{path}: reference attribute {k}"
        elif not np.array_equal(np.asarray(x), np.asarray(y)):
            return f"{path}: attribute {k}"
    if isinstance(a, h5py.Group):
        if not isinstance(b, h5py.Group) or set(a.keys()) != set(b.keys()):
            return f"{path}: members"
        for k in a:
            r = _differs(a[k], b[k], f"{path}{k}/")
            if r:
                return r
        return None
    if a.shape != b.shape or a.dtype != b.dtype:
        return f"{path}: shape or dtype"
    if not a.shape:
        return None if np.array_equal(a[()], b[()]) else f"{path}: value"
    step = _rows_per_block(a.shape)
    for s in range(0, a.shape[0], step):
        x, y = a[s:s + step], b[s:s + step]
        same = np.array_equal(x, y, equal_nan=True) if x.dtype.kind == "f" else np.array_equal(x, y)
        if not same:
            return f"{path}: values from row {s}"
    return None


def compress(src: Path, dst: Path) -> None:
    """Write a gzip-compressed, verified copy of `src` to `dst`."""
    refs: list = []
    try:
        with h5py.File(src, "r") as s, h5py.File(dst, "w") as d:
            _copy(s, d, refs)
            for obj, k, target in refs:
                d[obj].attrs[k] = d[target].ref
        with h5py.File(src, "r") as a, h5py.File(dst, "r") as b:
            bad = _differs(a, b)
        if bad:
            raise CompressionMismatch(f"{src.name}: compressed copy differs at {bad}")
    except BaseException:
        if dst.exists():
            os.remove(dst)
        raise
