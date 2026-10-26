"""VFBseq id minting: format, idempotence on natural keys, registry round trip."""

from vfb_scrnaseq.ids import IDRegistry, _format_id


def test_format_id_width():
    assert _format_id(1) == "VFBseq_00000001"
    assert _format_id(123) == "VFBseq_00000123"


def test_mint_is_sequential(tmp_path):
    reg = IDRegistry.load(tmp_path / "r.json")
    a = reg.mint("Dataset", "GSE156455")
    b = reg.mint("Sample", "GSM4731869")
    assert a == "VFBseq_00000001"
    assert b == "VFBseq_00000002"


def test_mint_is_idempotent(tmp_path):
    reg = IDRegistry.load(tmp_path / "r.json")
    first = reg.mint("Cluster", "T4 neuron", label="T4 neuron")
    again = reg.mint("Cluster", "T4 neuron")
    assert first == again
    # a different entity_type with the same natural key is a distinct entity
    other = reg.mint("Sample", "T4 neuron")
    assert other != first


def test_roundtrip_persists_counter(tmp_path):
    path = tmp_path / "r.json"
    reg = IDRegistry.load(path)
    reg.mint("Dataset", "GSE156455")
    reg.mint("Sample", "GSM4731869")
    reg.save()

    reloaded = IDRegistry.load(path)
    # existing ids are returned, not re-minted
    assert reloaded.get("Dataset", "GSE156455") == "VFBseq_00000001"
    assert reloaded.mint("Assay", "SRX1") == "VFBseq_00000003"


def test_unknown_entity_type_rejected(tmp_path):
    reg = IDRegistry.load(tmp_path / "r.json")
    try:
        reg.mint("Gizmo", "x")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for unknown entity_type")


def test_committed_registry_has_unique_ids():
    from pathlib import Path
    IDRegistry.load(Path(__file__).resolve().parents[1] / "id_registry" / "registry.json")   # check() on load


def test_load_rejects_an_id_minted_twice(tmp_path):
    import json
    import pytest
    path = tmp_path / "r.json"
    entry = {"id": "VFBseq_00000001", "entity_type": "Dataset", "label": None, "accession": None}
    path.write_text(json.dumps({"counter": 1, "entries": {
        "Dataset::A": {**entry, "natural_key": "A"}, "Dataset::B": {**entry, "natural_key": "B"}}}))
    with pytest.raises(ValueError, match="minted twice"):
        IDRegistry.load(path)


def test_load_rejects_a_counter_behind_the_ids(tmp_path):
    import json
    import pytest
    path = tmp_path / "r.json"
    path.write_text(json.dumps({"counter": 1, "entries": {"Dataset::A": {
        "id": "VFBseq_00000005", "entity_type": "Dataset", "natural_key": "A", "label": None, "accession": None}}}))
    with pytest.raises(ValueError, match="behind"):
        IDRegistry.load(path)
