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
