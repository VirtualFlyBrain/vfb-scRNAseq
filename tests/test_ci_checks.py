"""The CI check scripts: mapping.tsv freshness, the FBbt- and FlyBase-release checks,
gene ids by symbol (h5ad projects) and the release file set. Offline."""

import gzip
import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _script(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_davie_mapping_tsv_is_current():
    chk = _script("check_mapping_tsv")
    assert chk.check("davie_2018", chk._collate_module().collate) == []


def test_mapping_tsv_check_reports_stale_cell(monkeypatch):
    chk = _script("check_mapping_tsv")
    real = chk._collate_module().collate

    def edited(project):
        cols, rows = real(project)
        rows = [dict(r) for r in rows]
        rows[0]["fbbt_label"] = "something else"
        return cols, rows
    diffs = chk.check("davie_2018", edited)
    assert len(diffs) == 1 and "fbbt_label" in diffs[0]


def _gate(tmp_path, monkeypatch, recorded, current, problems=()):
    mod = _script("check_fbbt_release")
    record = tmp_path / "fbbt_last_checked.json"
    if recorded:
        record.write_text(json.dumps({"version": recorded, "checked_at": "2026-01-01"}))
    monkeypatch.setattr(mod, "RECORD", record)
    monkeypatch.setattr(mod, "PENDING", tmp_path / "no_pending.json")   # keep offline
    monkeypatch.setattr(mod, "REPO_ROOT", REPO)
    monkeypatch.setattr(mod, "current_release", lambda: {"version": current, "version_iri": "iri"})
    calls = []

    class _V:
        @staticmethod
        def verify(project):
            calls.append(project)
            return {"FBbt:00000001": {}}, list(problems)
    monkeypatch.setattr(mod, "_verify_module", lambda: _V)
    monkeypatch.setattr("sys.argv", ["check_fbbt_release.py"])
    return mod.main(), calls, record


def test_fbbt_gate_skips_unchanged_release(tmp_path, monkeypatch):
    rc, calls, record = _gate(tmp_path, monkeypatch, "2026-10-01", "2026-10-01")
    assert rc == 0 and calls == []
    assert json.loads(record.read_text())["checked_at"] == "2026-01-01"   # untouched


def test_fbbt_gate_verifies_and_records_new_release(tmp_path, monkeypatch):
    rc, calls, record = _gate(tmp_path, monkeypatch, "2026-10-01", "2026-11-01")
    assert rc == 0 and "davie_2018" in calls
    assert json.loads(record.read_text())["version"] == "2026-11-01"


def test_fbbt_gate_failure_keeps_old_record(tmp_path, monkeypatch):
    bad = [("FBbt:00000001", "OBSOLETE", {"clusters": ["x"]})]
    rc, calls, record = _gate(tmp_path, monkeypatch, "2026-10-01", "2026-11-01", bad)
    assert rc == 1
    assert json.loads(record.read_text())["version"] == "2026-10-01"


def _pending(tmp_path, monkeypatch, issue, status="pending"):
    mod = _script("check_fbbt_release")
    pend = tmp_path / "pending.json"
    pend.write_text(json.dumps([{"fbbt_issue": "FlyBase/x#1", "labels": ["immature T2 neuron"],
                                 "clusters": {"proj": ["early_T2"]}, "status": status}]))
    monkeypatch.setattr(mod, "PENDING", pend)
    monkeypatch.setattr(mod, "fbbt_issue", lambda ref: issue)
    monkeypatch.setattr(mod, "find_term", lambda label: "FBbt:00099999")
    opened = []
    monkeypatch.setattr(mod, "open_issue", lambda title, body, dry_run: opened.append((title, body)) or "url")
    release = {"version": "2026-11-01", "version_iri": "iri"}
    return mod, pend, opened, release


def test_pending_request_closed_before_release_opens_reminder_once(tmp_path, monkeypatch):
    issue = {"state": "closed", "state_reason": "completed", "closed_at": "2026-10-20T10:00:00Z", "html_url": "u"}
    mod, pend, opened, rel = _pending(tmp_path, monkeypatch, issue)
    assert mod.check_pending(rel) is True
    assert len(opened) == 1 and "early_T2" in opened[0][1] and "FBbt:00099999" in opened[0][1]
    assert json.loads(pend.read_text())[0]["status"] == "released"
    assert mod.check_pending(rel) is False and len(opened) == 1          # reported only once


def test_pending_request_closed_on_release_day_counts(tmp_path, monkeypatch):
    issue = {"state": "closed", "state_reason": None, "closed_at": "2026-11-01T23:00:00Z", "html_url": "u"}
    mod, pend, opened, rel = _pending(tmp_path, monkeypatch, issue)
    assert mod.check_pending(rel) is True and len(opened) == 1


def test_pending_request_closed_after_release_waits(tmp_path, monkeypatch):
    issue = {"state": "closed", "state_reason": None, "closed_at": "2026-11-02T01:00:00Z", "html_url": "u"}
    mod, pend, opened, rel = _pending(tmp_path, monkeypatch, issue)
    assert mod.check_pending(rel) is False and opened == []


def test_pending_request_still_open_waits(tmp_path, monkeypatch):
    issue = {"state": "open", "state_reason": None, "closed_at": None, "html_url": "u"}
    mod, pend, opened, rel = _pending(tmp_path, monkeypatch, issue)
    assert mod.check_pending(rel) is False and opened == []


# --- FlyBase release -> gene id reminder ----------------------------------------

def _flybase(tmp_path, monkeypatch, website, lookup):
    mod = _script("check_flybase_release")
    ug = _script("update_gene_ids")
    proj = tmp_path / "projects" / "p"
    proj.mkdir(parents=True)
    (proj / "gene_id_map.tsv").write_text(
        "# FlyBase Chado; FlyBase FB2026_03, released September 17, 2026\n"
        "input_fbgn\tinput_symbol\tstatus\tcurrent_fbgn\tcurrent_symbol\n"
        "FBgn0000001\ta\tcurrent\tFBgn0000001\ta\n"
        "FBgn0000002\tb\tcurrent\tFBgn0000002\tb\n")
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "RECORD", tmp_path / "checks" / "flybase_release_check.json")
    monkeypatch.setattr(ug, "flybase_release", lambda: website)
    monkeypatch.setattr(ug, "chado_lookup", lookup)
    opened = []

    class _Fbbt:
        @staticmethod
        def open_issue(title, body, dry_run):
            opened.append((title, body))
            return "issue-url"
    monkeypatch.setattr(mod, "_script", lambda name: ug if name == "update_gene_ids" else _Fbbt)
    monkeypatch.setattr("sys.argv", ["check_flybase_release.py"])
    return mod, opened


def test_flybase_newer_release_with_changes_opens_issue_once(tmp_path, monkeypatch):
    def lookup(ids):   # FBgn0000002 retired into FBgn0000009; FBgn0000001 renamed
        return {"FBgn0000001": [("current", "FBgn0000001", "a2")],
                "FBgn0000002": [("secondary", "FBgn0000009", "z")]}
    mod, opened = _flybase(tmp_path, monkeypatch, "FB2026_04, released December 1, 2026", lookup)
    assert mod.main() == 0 and len(opened) == 1
    title, body = opened[0]
    assert "FB2026_04" in title and "1 id change(s)" in body and "1 symbol change(s)" in body
    assert "update_gene_ids.py  --project p" in body
    assert mod.main() == 0 and len(opened) == 1                      # same release: not re-reported


def test_flybase_newer_release_no_changes_records_without_issue(tmp_path, monkeypatch):
    def lookup(ids):
        return {"FBgn0000001": [("current", "FBgn0000001", "a")],
                "FBgn0000002": [("current", "FBgn0000002", "b")]}
    mod, opened = _flybase(tmp_path, monkeypatch, "FB2026_04, released December 1, 2026", lookup)
    assert mod.main() == 0 and opened == []
    assert json.loads((tmp_path / "checks" / "flybase_release_check.json").read_text())["release"] == "FB2026_04"


def test_flybase_chado_unreachable_still_opens_issue(tmp_path, monkeypatch):
    def lookup(ids):
        raise FileNotFoundError("psql")
    mod, opened = _flybase(tmp_path, monkeypatch, "FB2026_04, released December 1, 2026", lookup)
    assert mod.main() == 0 and len(opened) == 1 and "could not be queried" in opened[0][1]


def test_flybase_same_release_does_nothing(tmp_path, monkeypatch):
    mod, opened = _flybase(tmp_path, monkeypatch, "FB2026_03, released September 17, 2026",
                           lambda ids: (_ for _ in ()).throw(AssertionError("queried")))
    assert mod.main() == 0 and opened == []
    assert not (tmp_path / "checks" / "flybase_release_check.json").exists()


def test_gene_ids_by_symbol(monkeypatch):
    """h5ad projects: ids where the files give them, else by symbol; rows keep input order."""
    ug = _script("update_gene_ids")
    monkeypatch.setattr(ug, "chado_lookup", lambda ids: {"FBgn0000001": [("current", "FBgn0000001", "a")]})
    monkeypatch.setattr(ug, "chado_symbol_lookup", lambda syms: {
        "cur": [("current", "FBgn0000002", "cur"), ("synonym", "FBgn0000009", "other")],  # current wins
        "old": [("synonym", "FBgn0000003", "new")],
        "amb": [("synonym", "FBgn0000004", "x"), ("synonym", "FBgn0000005", "y")]})
    rows = ug.reclassify([("", "cur"), ("FBgn0000001", "a"), ("", "old"), ("", "amb"), ("", "gone"), ("", "")])
    got = [(r["input_symbol"], r["status"], r["current_fbgn"]) for r in rows]
    assert got == [("cur", "current", "FBgn0000002"), ("a", "current", "FBgn0000001"),
                   ("old", "synonym", "FBgn0000003"), ("amb", "ambiguous", ""),
                   ("gone", "unmatched", ""), ("", "unmatched", "")]


def test_pending_review_issue_opens_revisit_reminder(tmp_path, monkeypatch):
    issue = {"state": "closed", "state_reason": "completed", "closed_at": "2026-10-20T10:00:00Z", "html_url": "u"}
    mod, pend, opened, rel = _pending(tmp_path, monkeypatch, issue)
    pend.write_text(json.dumps([{"fbbt_issue": "FlyBase/x#2218", "kind": "review", "topic": "review adult fat terms",
                                 "labels": [], "clusters": {"proj": ["head_adult fat body"]}, "status": "pending"}]))
    assert mod.check_pending(rel) is True
    title, body = opened[0]
    assert title.startswith("Revisit mappings") and "review adult fat terms" in title
    assert "head_adult fat body" in body and "Requested terms" not in body
    assert json.loads(pend.read_text())[0]["status"] == "released"


def test_symbol_majority_tiebreak():
    mod = _script("update_gene_ids")
    hits = {"Cha": [("synonym", "FBgn0000303", "ChAT", 41), ("synonym", "FBgn0000302", "cha", 2)],
            "Cry": [("synonym", "FBgn0005664", "Crys", 6), ("synonym", "FBgn0025680", "cry", 4)]}
    rows = {r["input_symbol"]: r for r in mod.classify_symbols(["Cha", "Cry"], hits)}
    assert (rows["Cha"]["status"], rows["Cha"]["current_fbgn"]) == ("synonym", "FBgn0000303")
    assert rows["Cry"]["status"] == "ambiguous" and rows["Cry"]["current_fbgn"] == ""


def _fake_release_repo(root, projects, expression_only=()):
    owl = b'<?xml version="1.0"?>\n<rdf:RDF xmlns="http://www.w3.org/2002/07/owl#">\n</rdf:RDF>\n'
    (root / "metadata").mkdir()
    (root / "expression").mkdir()
    for p in projects:
        (root / "metadata" / f"vfb_scRNAseq_metadata_{p}.owl").write_bytes(owl)
    for p in (*projects, *expression_only):
        with gzip.open(root / "expression" / f"vfb_scRNAseq_expression_{p}.owl.gz", "wb") as fh:
            fh.write(owl)


def test_release_files_published_names(tmp_path):
    rel = _script("release_files")
    (tmp_path / "repo").mkdir()
    _fake_release_repo(tmp_path / "repo", ["a_2020", "b_2021"])
    written = rel.write_release(tmp_path / "out", root=tmp_path / "repo")
    names = sorted(n for n, _ in written)
    assert names == ["VFB_scRNAseq_exp_a_2020.owl", "VFB_scRNAseq_exp_b_2021.owl",
                     "VFB_scRNAseq_metadata_a_2020.owl", "VFB_scRNAseq_metadata_b_2021.owl"]
    assert (tmp_path / "out" / "VFB_scRNAseq_exp_a_2020.owl").read_bytes().startswith(b"<?xml")
    manifest = (tmp_path / "out" / "release_manifest.tsv").read_text().splitlines()
    assert len(manifest) == 4
    assert all(int(line.split("\t")[1]) > 0 for line in manifest)


def test_release_files_needs_both_files(tmp_path):
    rel = _script("release_files")
    (tmp_path / "repo").mkdir()
    _fake_release_repo(tmp_path / "repo", ["a_2020"], expression_only=["c_2022"])
    with pytest.raises(SystemExit, match="expression only"):
        rel.projects(tmp_path / "repo")


def test_release_files_cover_every_project():
    rel = _script("release_files")
    built = {p.parent.name for p in (REPO / "projects").glob("*/provenance.json")}
    assert set(rel.projects()) == built
