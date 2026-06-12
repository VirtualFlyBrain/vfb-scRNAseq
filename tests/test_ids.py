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
