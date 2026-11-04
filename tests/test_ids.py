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


def _git(cwd, *args):
    import subprocess
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t", "PATH": __import__("os").environ["PATH"]})


def _repo_with_branch(tmp_path):
    """A git repo whose main registry has counter 2, and branch `other` that minted ids 3-4."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    path = repo / "id_registry" / "registry.json"
    reg = IDRegistry.load(path)
    reg.mint("Dataset", "A")
    reg.mint("Dataset", "B")
    reg.save()
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "main")
    _git(repo, "switch", "-q", "-c", "other")
    reg = IDRegistry.load(path)
    reg.mint("Cluster", "x")
    reg.mint("Cluster", "y")
    reg.save()
    _git(repo, "commit", "-q", "-am", "other")
    _git(repo, "switch", "-q", "main")
    return repo, path


def test_new_ids_skip_those_minted_on_another_branch(tmp_path, monkeypatch):
    monkeypatch.delenv("VFBSEQ_IDS_LOCAL_ONLY", raising=False)
    repo, path = _repo_with_branch(tmp_path)
    reg = IDRegistry.load(path)
    assert reg.get("Dataset", "A") == "VFBseq_00000001"          # existing ids untouched
    assert reg.mint("Dataset", "A") == "VFBseq_00000001"
    assert reg.mint("Cluster", "z") == "VFBseq_00000005"          # past branch `other` (3-4)
    assert reg.mint("Cluster", "w") == "VFBseq_00000006"


def test_new_ids_skip_those_minted_in_another_worktree(tmp_path, monkeypatch):
    monkeypatch.delenv("VFBSEQ_IDS_LOCAL_ONLY", raising=False)
    repo, path = _repo_with_branch(tmp_path)
    wt = tmp_path / "wt"
    _git(repo, "worktree", "add", "-q", "-b", "third", str(wt), "main")
    reg = IDRegistry.load(wt / "id_registry" / "registry.json")   # uncommitted mints: 5-7
    for k in "pqr":
        reg.mint("Cluster", k)
    reg.save()
    assert IDRegistry.load(path).mint("Cluster", "s") == "VFBseq_00000008"


def test_local_only_opt_out(tmp_path, monkeypatch):
    repo, path = _repo_with_branch(tmp_path)
    monkeypatch.setenv("VFBSEQ_IDS_LOCAL_ONLY", "1")
    assert IDRegistry.load(path).mint("Cluster", "z") == "VFBseq_00000003"
