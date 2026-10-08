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
