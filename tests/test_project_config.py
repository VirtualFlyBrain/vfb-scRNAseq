"""Config-driven knobs added for the second project (Davie 2018): file-name-safe
label slugs, holding class-less unidentified clusters, and regex GSM-title parsing.
Offline."""

import importlib.util
import json
from pathlib import Path

from vfb_scrnaseq.project_config import held_classifier, label_slug

REPO = Path(__file__).resolve().parents[1]


def _script(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_label_slug_identity_for_safe_labels():
    for label in ("L1", "R1.6", "Lpi3.4", "Ensheathing_glia", "G-KC", "T4a"):
        assert label_slug(label) == label


def test_label_slug_unsafe_labels():
    assert label_slug("Pm1/Pm2") == "Pm1_Pm2"
    assert label_slug("A/B*-KC") == "A_Bp-KC"
    assert label_slug("adPN/C15&kn") == "adPN_C15+kn"


def test_label_slugs_unique_for_every_project():
    for cta in REPO.glob("projects/*/cell_type_annotations.json"):
        labels = [a["label"] for a in json.loads(cta.read_text())["annotations"]]
        assert len({label_slug(x) for x in labels}) == len(labels), cta


def test_hold_unidentified_holds_classless_numbered_clusters():
    cfg = {"unidentified": {"rule": r"regex:\d+", "hold_unidentified": True}}
    is_held = held_classifier("nonexistent_project", cfg)
    assert is_held("23", "")
    assert not is_held("Hsp", "")


def test_hold_classes_unchanged_without_hold_unidentified():
    cfg = {"unidentified": {"rule": "class_prefixed_numbered", "hold_classes": ["C"]}}
    is_held = held_classifier("nonexistent_project", cfg)
    assert is_held("C16", "C")
    assert not is_held("N1", "N")      # placeholder, not held


def test_regex_title_pattern_scopes_gsms():
    mod = _script("build_samples_from_geo")
    parse = mod.title_parser(r"regex:(?P<set>DGRP-551|w1118)_(?P<timepoint>\d+d)_(?P<biorep>r\d+)")
    p = parse("DGRP-551_0d_r1")
    assert p["sample_id"] == "DGRP-551_0d_r1" and p["set"] == "DGRP-551" and p["techrep"] is None
    for out_of_scope in ("DGRP-551_0d_r1 Drop-Seq", "DGRP-907_0d_s8", "DGRP-551_1d_r2_SDP"):
        assert parse(out_of_scope) is None


def test_default_title_pattern_is_legacy_parser():
    mod = _script("build_samples_from_geo")
    assert mod.title_parser(None)("W1118_24h_A_1")["sample_id"] == "W1118_24h_A"


def test_annotation_kind_holds_unannotated_entries():
    from vfb_scrnaseq.project_config import annotation_kind
    cfg = {"unidentified": {"rule": "none", "hold_unidentified": True}}
    kind = annotation_kind("nonexistent_project", cfg)
    assert kind({"label": "res2_13", "unannotated": True}) == "held"
    assert kind({"label": "res2_14", "type": "Ensheathing_glia"}) == "named"


def test_annotation_kind_matches_label_rules():
    from vfb_scrnaseq.project_config import annotation_kind
    cfg = {"unidentified": {"rule": "class_prefixed_numbered", "hold_classes": ["C"]}}
    kind = annotation_kind("nonexistent_project", cfg)
    assert kind({"label": "C16", "class": "C"}) == "held"
    assert kind({"label": "N1", "class": "N"}) == "placeholder"
    assert kind({"label": "L1", "class": "N"}) == "named"


def test_reports_readme_created_once_never_overwritten(tmp_path):
    mod = _script("collate_mapping")
    proj = tmp_path / "proj"
    (proj / "reports").mkdir(parents=True)
    assert mod.ensure_reports_readme(proj) is None          # no reports yet
    (proj / "reports" / "L1.md").write_text("# L1\n")
    readme = mod.ensure_reports_readme(proj)
    assert readme and "mapping.tsv" in readme.read_text()
    readme.write_text("project-specific notes\n")
    assert mod.ensure_reports_readme(proj) is None          # existing README kept
    assert readme.read_text() == "project-specific notes\n"


def test_hold_reason():
    from vfb_scrnaseq.project_config import hold_reason
    cfg = {"unidentified": {"hold_classes": ["C"], "hold_reasons": {"artefact": "artefact"}}}
    reason = hold_reason("nonexistent_project", cfg)
    term = {"best_match": {"fbbt_id": "FBbt:00000001"}}
    assert reason({"label": "a", "type": "artefact", "unannotated": True}, None) == "artefact"
    assert reason({"label": "n", "type": "13", "unannotated": True}, None) == "untyped"
    assert reason({"label": "C16", "class": "C"}, {"best_match": None}) == "undefined class"
    assert reason({"label": "Hsp"}, {"best_match": None}) == "no term"
    assert reason({"label": "KC"}, term) == ""


def test_reused_samples_and_clustering_links(tmp_path, monkeypatch):
    import json
    import pytest
    from vfb_scrnaseq import project_config as pc
    monkeypatch.setattr(pc, "REPO_ROOT", tmp_path)
    cfg = {"_project": "new", "reuse": [{"from_project": "src", "samples": ["s1"]}]}
    with pytest.raises(pc.SourceNotCurated, match="curate src first"):      # not curated yet
        pc.reused_samples(cfg)
    (tmp_path / "projects" / "src").mkdir(parents=True)
    (tmp_path / "projects" / "src" / "samples.json").write_text(json.dumps({"samples": [
        {"vfbseq_id": "VFBseq_00000001", "sample_id": "s1", "tissue_raw": "head",
         "assay_vfbseq_ids": ["VFBseq_00000002"]}]}))
    reused = pc.reused_samples(cfg)
    assert reused == [{"vfbseq_id": "VFBseq_00000001", "sample_id": "s1", "from_project": "src",
                       "tissue_raw": "head", "assay_vfbseq_ids": ["VFBseq_00000002"]}]
    with pytest.raises(pc.SourceNotCurated, match="not found"):
        pc.reused_samples({"reuse": [{"from_project": "src", "samples": ["s9"]}]})
    own = [{"vfbseq_id": "VFBseq_00000010", "tissue_raw": "head"},
           {"vfbseq_id": "VFBseq_00000011", "tissue_raw": "body"}]
    assert pc.clustering_samples({"id": "h", "sample_tissue_raw": "head"}, own, reused) == \
        ["VFBseq_00000010", "VFBseq_00000001"]
    assert pc.clustering_samples("main", own, reused) == []
