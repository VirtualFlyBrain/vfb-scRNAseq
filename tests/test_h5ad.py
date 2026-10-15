"""h5ad obs reading (old / 0.7 / 0.8+ AnnData layouts) and annotation grouping. Offline."""

import importlib.util
import sys
from pathlib import Path

import h5py
import numpy as np

from vfb_scrnaseq.ingest_h5ad import obs_columns, read_obs

REPO = Path(__file__).resolve().parents[1]
CELLS = [b"c1", b"c2", b"c3"]
ANN = ["neuron", "glia"]           # categories; codes below
CODES = np.array([0, 1, 0], dtype=np.int8)
STR = h5py.string_dtype()


def _builder():
    sys.path.insert(0, str(REPO / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "build_annotations_from_h5ad", REPO / "scripts" / "build_annotations_from_h5ad.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _old(path):
    with h5py.File(path, "w") as f:
        dt = np.dtype([("index", "S2"), ("annotation", "i1"), ("n_genes", "i4")])
        f["obs"] = np.array(list(zip(CELLS, CODES, [10, 20, 30])), dtype=dt)
        f["uns/annotation_categories"] = np.array([a.encode() for a in ANN])


def _v07(path):
    with h5py.File(path, "w") as f:
        obs = f.create_group("obs")
        obs.attrs["_index"] = "_index"
        obs.attrs["column-order"] = np.array(["annotation", "n_genes"], dtype=object).astype(STR)
        obs["_index"] = np.array(CELLS)
        obs["annotation"] = CODES
        obs["__categories/annotation"] = np.array(ANN, dtype=object).astype(STR)
        obs["n_genes"] = np.array([10, 20, 30])


def _v08(path):
    with h5py.File(path, "w") as f:
        obs = f.create_group("obs")
        obs.attrs["_index"] = "_index"
        obs.attrs["encoding-type"] = "dataframe"
        obs.attrs["column-order"] = np.array(["annotation", "n_genes"], dtype=object).astype(STR)
        obs["_index"] = np.array(CELLS)
        g = obs.create_group("annotation")
        g["categories"] = np.array(ANN, dtype=object).astype(STR)
        g["codes"] = CODES
        obs["n_genes"] = np.array([10, 20, 30])


def test_read_obs_all_layouts(tmp_path):
    for make in (_old, _v07, _v08):
        p = tmp_path / f"{make.__name__}.h5ad"
        make(p)
        assert obs_columns(p) == ["annotation", "n_genes"], make.__name__
        o = read_obs(p, ["annotation", "n_genes"])
        assert o["_index"] == ["c1", "c2", "c3"], make.__name__
        assert o["annotation"] == ["neuron", "glia", "neuron"], make.__name__
        assert o["n_genes"] == [10, 20, 30], make.__name__


def test_missing_category_code_is_none(tmp_path):
    p = tmp_path / "m.h5ad"
    with h5py.File(p, "w") as f:
        obs = f.create_group("obs")
        obs.attrs["_index"] = "_index"
        obs["_index"] = np.array([b"c1"])
        g = obs.create_group("annotation")
        g["categories"] = np.array(ANN, dtype=object).astype(STR)
        g["codes"] = np.array([-1], dtype=np.int8)
    assert read_obs(p, ["annotation"])["annotation"] == [None]


def test_build_clustering_one_entry_per_annotation():
    mod = _builder()
    obs = {"_index": ["a", "b", "c", "d"],
           "annotation": ["neuron", "neuron", "unannotated", "glia"],
           "annotation__ontology_id": ["FBbt:1", "FBbt:1", "unannotated", "Manual Annotation"],
           "sex": ["male", "female", "male", "male"]}
    ab = {"annotation_column": "annotation", "ontology_column": "annotation__ontology_id",
          "sex_column": "sex", "unannotated_values": ["unannotated"]}
    warnings = []
    anns = mod.build_clustering(obs, ab, "wing", "FCA Wing", warnings)
    by = {a["type"]: a for a in anns}
    assert [a["label"] for a in anns] == ["wing_glia", "wing_neuron", "wing_unannotated"]
    assert by["neuron"]["cell_number"] == 2 and by["neuron"]["author_ontology_id"] == "FBbt:1"
    assert by["neuron"]["cells_by_sex"] == {"female": 1, "male": 1}
    assert by["unannotated"]["unannotated"] is True and "unannotated" not in by["neuron"]
    assert by["neuron"]["clustering"] == "wing" and by["neuron"]["source_cluster_id"] == "neuron"
    assert warnings == []


def test_list_valued_author_ontology_ids_are_normalised():
    mod = _builder()
    assert mod._ontology_ids("['FBbt:00003731', 'FBbt:00003736']") == "FBbt:00003731; FBbt:00003736"
    assert mod._ontology_ids("FBbt:00000124") == "FBbt:00000124"


def test_membership_is_recorded_except_on_held_entries():
    mod = _builder()
    obs = {"_index": ["a", "b"], "transf_annotation": ["neuron", "unknown"]}
    ab = {"annotation_column": "transf_annotation", "unannotated_values": ["unknown"],
          "membership": "label_transfer"}
    by = {a["type"]: a for a in mod.build_clustering(obs, ab, "leg", "Leg", [])}
    assert by["neuron"]["membership"] == "label_transfer"
    assert "membership" not in by["unknown"] and by["unknown"]["unannotated"]


# --- genes and matrix (expression) -------------------------------------------------

# 3 cells x 4 genes; gene g3 unexpressed
DENSE = np.array([[1.0, 0, 2.0, 0],
                  [0, 3.0, 0, 0],
                  [4.0, 0, 5.0, 0]])
GENES = ["g0", "g1", "g2", "g3"]


def _sparse(dense, by_gene):
    """(data, indices, indptr) of `dense` as CSC (by_gene) or CSR."""
    m = dense.T if by_gene else dense
    data, indices, indptr = [], [], [0]
    for row in m:
        nz = np.flatnonzero(row)
        data += list(row[nz]); indices += list(nz); indptr.append(len(data))
    return np.array(data, dtype=np.float32), np.array(indices, dtype=np.int32), np.array(indptr)


def _old_raw(path):
    """anndata < 0.7: raw.X (h5sparse CSC) + raw.var compound with categorical ID."""
    with h5py.File(path, "w") as f:
        data, idx, ptr = _sparse(DENSE, by_gene=True)
        g = f.create_group("raw.X")
        g["data"], g["indices"], g["indptr"] = data, idx, ptr
        g.attrs["h5sparse_format"] = "csc"
        g.attrs["h5sparse_shape"] = np.array(DENSE.shape)
        dt = np.dtype([("index", "S2"), ("ID", "i2")])
        f["raw.var"] = np.array([(n.encode(), c) for n, c in zip(GENES, [0, 1, -1, 2])], dtype=dt)
        f["raw.cat/ID_categories"] = np.array([b"FBgn0000001", b"FBgn0000002", b"nan"])
        f["X"] = DENSE[:, :2]                      # the scaled HVG matrix: not read


def _v07_raw(path):
    """0.7: raw/X CSC; raw/var ID codes whose categories were not saved."""
    with h5py.File(path, "w") as f:
        data, idx, ptr = _sparse(DENSE, by_gene=True)
        x = f.create_group("raw/X")
        x["data"], x["indices"], x["indptr"] = data, idx, ptr
        x.attrs["encoding-type"] = "csc_matrix"
        x.attrs["shape"] = np.array(DENSE.shape)
        v = f.create_group("raw/var")
        v.attrs["_index"] = "index"
        v["index"] = np.array([n.encode() for n in GENES])
        v["ID"] = np.array([0, 1, 2, 3], dtype=np.int16)
        f["X"] = DENSE[:, :2]


def _csr_x(path):
    with h5py.File(path, "w") as f:
        data, idx, ptr = _sparse(DENSE, by_gene=False)
        x = f.create_group("X")
        x["data"], x["indices"], x["indptr"] = data, idx, ptr
        x.attrs["encoding-type"] = "csr_matrix"
        x.attrs["shape"] = np.array(DENSE.shape)
        v = f.create_group("var")
        v.attrs["_index"] = "_index"
        v["_index"] = np.array(GENES, dtype=object).astype(STR)


def _dense_x(path):
    with h5py.File(path, "w") as f:
        f["X"] = DENSE.astype(np.float32)
        v = f.create_group("var")
        v.attrs["_index"] = "_index"
        v["_index"] = np.array(GENES, dtype=object).astype(STR)


def test_matrix_and_genes_all_layouts(tmp_path):
    from vfb_scrnaseq.ingest_h5ad import iter_matrix, matrix_shape, read_genes
    expect_ids = {"_old_raw": ["FBgn0000001", "FBgn0000002", None, None]}
    for make in (_old_raw, _v07_raw, _csr_x, _dense_x):
        p = tmp_path / f"{make.__name__}.h5ad"
        make(p)
        genes, ids = read_genes(p)
        assert genes == GENES, make.__name__
        # ids only where the file gives decodable FBgn ids
        assert ids == expect_ids.get(make.__name__, [None] * 4), make.__name__
        assert matrix_shape(p) == DENSE.shape, make.__name__
        got = np.zeros(DENSE.shape)
        n = 0
        for g, c, v in iter_matrix(p, chunk=2):            # small chunks: several blocks
            got[c, g] += v
            n += len(v)
        assert n == np.count_nonzero(DENSE) and np.array_equal(got, DENSE), make.__name__


# --- lossless compression of cached files (vfb_scrnaseq.h5ad_compress, fetch_h5ad) ----

def _v07_with_refs(path):
    """AnnData 0.7 style: a categorical column points at its categories via an
    object-reference attribute; plus a sparse X large enough to be compressed."""
    _v07(path)
    with h5py.File(path, "a") as f:
        f["obs/annotation"].attrs["categories"] = f["obs/__categories/annotation"].ref
        x = f.create_group("X")
        x.attrs["encoding-type"] = "csr_matrix"
        x.attrs["shape"] = np.array([3, 2000])
        x["data"] = np.linspace(0, 1, 3000, dtype=np.float32)
        x["indices"] = np.tile(np.arange(1000, dtype=np.int32), 3)
        x["indptr"] = np.array([0, 1000, 2000, 3000], dtype=np.int64)


def test_compress_roundtrip_all_layouts(tmp_path):
    from vfb_scrnaseq.h5ad_compress import compress, is_compressed
    from vfb_scrnaseq.ingest_h5ad import iter_matrix
    for make in (_old, _v07_with_refs, _v08):
        src, dst = tmp_path / f"{make.__name__}.h5ad", tmp_path / f"{make.__name__}.gz.h5ad"
        make(src)
        compress(src, dst)
        assert is_compressed(dst)
        assert read_obs(dst, ["annotation", "n_genes"]) == read_obs(src, ["annotation", "n_genes"])
        if make is _v07_with_refs:
            assert not is_compressed(src)
            with h5py.File(dst) as f:      # the reference now points inside the new file
                assert f[f["obs/annotation"].attrs["categories"]].name == "/obs/__categories/annotation"
            got = [np.concatenate(p) for p in zip(*iter_matrix(dst, use_raw=False))]
            want = [np.concatenate(p) for p in zip(*iter_matrix(src, use_raw=False))]
            assert all(np.array_equal(a, b) for a, b in zip(got, want))


def test_compress_mismatch_is_caught(tmp_path, monkeypatch):
    import pytest
    from vfb_scrnaseq import h5ad_compress as hc
    src, dst = tmp_path / "a.h5ad", tmp_path / "b.h5ad"
    _v07_with_refs(src)
    real = hc._copy

    def corrupt(s, d, refs):
        real(s, d, refs)
        if "X" in d:
            d["X/data"][0] = 99.0
    monkeypatch.setattr(hc, "_copy", corrupt)
    with pytest.raises(hc.CompressionMismatch, match="X/data"):
        hc.compress(src, dst)
    assert not dst.exists()


def test_fetch_compresses_downloads(tmp_path):
    import gzip
    import shutil
    sys.path.insert(0, str(REPO / "scripts"))
    spec = importlib.util.spec_from_file_location("fetch_h5ad", REPO / "scripts" / "fetch_h5ad.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    from vfb_scrnaseq.h5ad_compress import is_compressed
    src = tmp_path / "remote.h5ad"
    _v07_with_refs(src)
    with open(src, "rb") as a, gzip.open(tmp_path / "remote.h5ad.gz", "wb") as b:
        shutil.copyfileobj(a, b)
    for url, name in ((src.as_uri(), "plain.h5ad"), ((tmp_path / "remote.h5ad.gz").as_uri(), "gz.h5ad")):
        dest = tmp_path / "cache" / name
        mod.fetch_any(url, dest)
        assert dest.exists() and is_compressed(dest)
        assert read_obs(dest, ["annotation"]) == read_obs(src, ["annotation"])
        assert not list(dest.parent.glob(name + ".*"))       # no leftover temp files
        mod.fetch_any(url, dest)                              # done: not fetched again
