"""expand_type_mappings: type-level mappings copied per cluster. Offline."""

import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _mod():
    spec = importlib.util.spec_from_file_location(
        "expand_type_mappings", REPO / "scripts" / "expand_type_mappings.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_expand_copies_per_cluster_and_keeps_manual_edits(tmp_path):
    proj, tdir = tmp_path / "p", tmp_path / "types"
    (proj / "mapping").mkdir(parents=True)
    tdir.mkdir()
    (proj / "cell_type_annotations.json").write_text(json.dumps({"annotations": [
        {"label": "wing_hemocyte", "type": "hemocyte"},
        {"label": "leg_hemocyte", "type": "hemocyte"},
        {"label": "leg_glia", "type": "glia"},
        {"label": "leg_unannotated", "type": "unannotated", "unannotated": True},
    ]}))
    (tdir / "hemocyte.fbbt_mapping.json").write_text(json.dumps({"cluster_label": "hemocyte", "x": 1}))
    (proj / "mapping" / "leg_hemocyte.fbbt_mapping.json").write_text(
        json.dumps({"cluster_label": "leg_hemocyte", "manual_edit": {"by": "curator"}}))
    (proj / "mapping" / "old_label.fbbt_mapping.json").write_text("{}")
    n, kept, missing = _mod().expand(proj, tdir)
    assert n == 1 and kept == ["leg_hemocyte"] and missing == ["leg_glia (type 'glia')"]
    assert json.loads((proj / "mapping" / "wing_hemocyte.fbbt_mapping.json").read_text()) == \
        {"cluster_label": "wing_hemocyte", "x": 1}
    assert "manual_edit" in json.loads((proj / "mapping" / "leg_hemocyte.fbbt_mapping.json").read_text())
    assert not (proj / "mapping" / "old_label.fbbt_mapping.json").exists()
