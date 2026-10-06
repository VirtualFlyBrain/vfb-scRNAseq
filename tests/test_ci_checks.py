"""The CI check scripts: mapping.tsv freshness and the FBbt-release gate. Offline."""

import importlib.util
import json
from pathlib import Path

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
