"""Pipeline behaviour that otherwise only real runs exercise: annotation ingest with
extra clusterings / a prefixed main clustering, and mapping.tsv collation (held when
no FBbt term, row order, prior cross-check, kept review marks). Offline: tiny
projects in tmp_path, with the scripts' and project_config's REPO_ROOT pointed there.
"""

import csv
import datetime
import gzip
import importlib.util
import json
import sys
from pathlib import Path

import yaml

from vfb_scrnaseq import project_config

REPO = Path(__file__).resolve().parents[1]


def _script(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _tsv_gz(path, header, rows):
    with gzip.open(path, "wt") as fh:
        fh.write("\t".join(header) + "\n")
        fh.writelines("\t".join(r) + "\n" for r in rows)


def _project(tmp_path, monkeypatch, cfg):
    proj = tmp_path / "projects" / "p"
    proj.mkdir(parents=True)
    (tmp_path / ".cache").mkdir()
    (proj / "config.yaml").write_text(yaml.safe_dump(cfg))
    monkeypatch.setattr(project_config, "REPO_ROOT", tmp_path)
    return proj


# --- annotation ingest ---------------------------------------------------------

def test_ingest_prefixed_main_and_extra_clustering(tmp_path, monkeypatch):
    cfg = {"source": {"doi": "d", "title": "t"}, "dataset": {"accession": "GSE1"},
           "annotations": {"source_file": "main.tsv.gz", "subset": "main", "label_column": "subtype",
                           "carry_columns": ["class"], "timepoint_column": "time",
                           "label_prefix": "main_", "clustering_id": "main", "clustering_name": "main set",
                           "extra_clusterings": [{"id": "early", "name": "early set",
                                                  "source_file": "early.tsv.gz", "label_prefix": "early_"}]}}
    _project(tmp_path, monkeypatch, cfg)
    hdr = ["barcode", "subtype", "class", "time"]
    _tsv_gz(tmp_path / ".cache" / "main.tsv.gz", hdr,
            [["a", "L1", "N", "24h"], ["b", "L1", "N", "48h"], ["c", "N7", "N", "24h"]])
    _tsv_gz(tmp_path / ".cache" / "early.tsv.gz", hdr, [["d", "L1", "N", "0h"], ["e", "x3", "x", "0h"]])
    mod = _script("build_annotations_from_geo")
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["x", "--project", "p"])
    mod.main()
    anns = {a["label"]: a for a in json.loads(
        (tmp_path / "projects/p/cell_type_annotations.json").read_text())["annotations"]}
    assert set(anns) == {"main_L1", "main_N7", "early_L1", "early_x3"}
    assert anns["main_L1"]["cell_number"] == 2 and anns["main_L1"]["clustering"] == "main"
    assert anns["early_L1"]["source_cluster_id"] == "L1" and anns["early_L1"]["clustering_name"] == "early set"
    # label rules apply to the authors' cluster id, not the prefixed label
    cfg_u = {"unidentified": {"rule": "class_prefixed_numbered", "hold_classes": ["x"]}}
    kind = project_config.annotation_kind("p", cfg_u)
    assert kind(anns["main_N7"]) == "placeholder"
    assert kind(anns["early_x3"]) == "held"
    assert kind(anns["main_L1"]) == "named"


def test_clustering_class_anchor_override():
    cfg = {"unidentified": {"class_anchors": {"N": {"fbbt_id": "FBbt:1", "label": "adult"}},
                            "clustering_class_anchors": {"early": {"N": {"fbbt_id": "FBbt:2", "label": "immature"}}}}}
    assert project_config.broad_anchor("nonexistent", cfg, "N")["label"] == "adult"
    assert project_config.broad_anchor("nonexistent", cfg, "N", "early")["label"] == "immature"


# --- collate -------------------------------------------------------------------

def _mapping(label, fbbt=None, term=None):
    bm = None if fbbt is None else {"fbbt_term": term, "fbbt_id": fbbt, "fbbt_definition": "d",
                                    "match_type": "exact match", "skos_mapping": "skos:exactMatch",
                                    "confidence": "high"}
    return {"cluster_label": label, "working_definition": "w", "searches_performed": ["s"],
            "best_match": bm, "justification": "j", "other_candidates": [], "recommendation": "r",
            "new_term_needed": False, "verification_needed": False}


def test_collate_held_order_prior_and_review(tmp_path, monkeypatch):
    cfg = {"annotations": {"review_columns": ["clustering"]},
           "unidentified": {"rule": "none"}, "prior_mapping": "prior.tsv"}
    proj = _project(tmp_path, monkeypatch, cfg)
    anns = [{"label": l, "clustering": "c", "cell_number": 1} for l in ("c_10", "c_2", "c_x", "c_1")]
    (proj / "cell_type_annotations.json").write_text(json.dumps({"annotations": anns}))
    (proj / "mapping").mkdir()
    for lab, fb in (("c_10", "FBbt:00000010"), ("c_2", "FBbt:00000002"), ("c_1", "FBbt:00000001")):
        (proj / "mapping" / f"{lab}.fbbt_mapping.json").write_text(json.dumps(_mapping(lab, fb, "t" + lab)))
    (proj / "mapping" / "c_x.fbbt_mapping.json").write_text(json.dumps(_mapping("c_x")))   # no term
    (proj / "prior.tsv").write_text("cluster_label\told_fbbt_id\told_fbbt_label\n"
                                    "c_1\tFBbt:00000001\tx\nc_2\tFBbt:99999999\ty\n")
    (proj / "mapping.tsv").write_text("cluster_label\treviewed\treview_notes\n"
                                         "c_2\tYes\tok\nc_1\t2026-01-02\t\n")
    mod = _script("collate_mapping")
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    cols, rows = mod.collate("p")
    assert cols[:2] == ["cluster_label", "clustering"] and "prior_agrees" in cols
    assert [r["cluster_label"] for r in rows] == ["c_1", "c_2", "c_10", "c_x"]   # mapped first, numeric order
    by = {r["cluster_label"]: r for r in rows}
    assert by["c_x"]["kind"] == "held" and by["c_x"]["match_type"] == "HELD"   # no FBbt term -> held
    assert by["c_x"]["hold_reason"] == "no term" and by["c_1"]["hold_reason"] == ""
    assert by["c_1"]["prior_agrees"] == "yes" and by["c_2"]["prior_agrees"] == "NO"
    assert by["c_10"]["prior_agrees"] == ""
    today = datetime.date.today().isoformat()
    assert (by["c_2"]["reviewed"], by["c_2"]["review_notes"]) == (today, "ok")    # y/yes -> date
    assert by["c_1"]["reviewed"] == "2026-01-02"                                  # date kept


# --- committed project structure -----------------------------------------------

def _anns(project):
    return json.loads((REPO / "projects" / project / "cell_type_annotations.json").read_text())["annotations"]


def test_davie_clusters_structure():
    anns = _anns("davie_2018")
    by_cl = {}
    for a in anns:
        by_cl.setdefault(a["clustering"], []).append(a)
    assert {k: len(v) for k, v in by_cl.items()} == {
        "res2": 87, "res8": 5, "sub20": 5, "sub27": 9, "sub42": 2, "sub64": 2, "neuropeptide": 15}
    cells = {a["label"]: a["cell_number"] for a in anns}
    assert sum(a["cell_number"] for a in by_cl["res2"]) == 56902          # res-2.0 partitions the 57K cells
    for parent in ("20", "27", "42", "64"):                                 # sub-clusters nest in their parent
        subs = [a for a in anns if a.get("parent_cluster") == f"res2_{parent}"]
        assert subs and all(a["clustering"] == f"sub{parent}" for a in subs)
        assert sum(a["cell_number"] for a in subs) <= cells[f"res2_{parent}"]
    assert not any(a.get("parent_cluster") for a in by_cl["res8"] + by_cl["neuropeptide"])


def test_kurmangaliyev_clusters_structure():
    anns = _anns("kurmangaliyev_2020")
    main = [a for a in anns if a["clustering"] == "main"]
    early = [a for a in anns if a["clustering"] == "early"]
    assert len(main) == 196 and len(early) == 110 and len(anns) == 306
    assert all(a["label"] == "main_" + a["source_cluster_id"] for a in main)
    assert all(a["label"] == "early_" + a["source_cluster_id"] for a in early)
    assert sum(a["cell_number"] for a in main) == 193727


def test_mapping_files_match_cluster_labels():
    for project in ("davie_2018", "kurmangaliyev_2020"):
        labels = {a["label"] for a in _anns(project)}
        for f in (REPO / "projects" / project / "mapping").glob("*.fbbt_mapping.json"):
            m = json.loads(f.read_text())
            assert m["cluster_label"] in labels, (project, f.name)
            assert f.name == project_config.label_slug(m["cluster_label"]) + ".fbbt_mapping.json"


def test_sample_and_assay_names_unique():
    """Sample and Assay labels are unique within each project (Assay labels are the
    Sample's plus the lane / library / plate, `sample_build.assay_label`)."""
    for ent_file in sorted((REPO / "projects").glob("*/entities.json")):
        ents = json.loads(ent_file.read_text())
        for t in ("Sample", "Assay"):
            names = [e["name"] for e in ents if e["type"] == t]
            dups = sorted({n for n in names if names.count(n) > 1})
            assert not dups, f"{ent_file.parent.name}: duplicate {t} names {dups[:3]}"


def test_assay_namer():
    from vfb_scrnaseq.build import _assay_namer
    assays = [{"library_id": f"W_24h_A_{i}", "sample_vfbseq_id": "S1"} for i in (1, 2)]
    descr = {"S1": "optic lobes, 24h APF, W rep A"}
    cfg = {"sample_build": {"assay_label": {"unit": "10x lane", "pattern": r"_(\d+)$", "of_total": True}}}
    name = _assay_namer(cfg, assays, descr, " (X 2020)")
    assert name(assays[1]) == "optic lobes, 24h APF, W rep A, 10x lane 2 of 2 (X 2020)"
    cfg = {"sample_build": {"assay_label": {"unit": "10x library"}}}
    assert _assay_namer(cfg, assays, descr, "")(assays[0]) == "optic lobes, 24h APF, W rep A, 10x library"
    assert _assay_namer({}, [{"accession": "GSM1"}], {}, "")({"accession": "GSM1"}) == "GSM1"


def test_geo_title_regex_extra_groups_join_sample_id():
    mod = _script("build_samples_from_geo")
    parse = mod.title_parser(r"regex:(?P<set>Male|Female)_(?P<tissue>head|body)_adult_"
                             r"(?P<timepoint>\d+d)WT_Hongjie_(?P<biorep>S\d+)_S\d+")
    p = parse("Female_body_adult_30dWT_Hongjie_S1_S1")
    assert p["sample_id"] == "Female_body_30d_S1" and p["set"] == "Female" and p["techrep"] is None
    assert parse("Female_wing_adult_30dWT_Hongjie_S1_S1") is None


def test_expand_type_mappings_own_dir_aliases_and_held(tmp_path):
    mod = _script("expand_type_mappings")
    proj, other = tmp_path / "p", tmp_path / "src" / "type_mapping"
    (proj / "type_mapping").mkdir(parents=True)
    other.mkdir(parents=True)

    def m(label, fb):
        return json.dumps({"cluster_label": label, "best_match": {"fbbt_id": fb}})
    (other / "epithelial_cell.fbbt_mapping.json").write_text(m("epithelial cell", "FBbt:00000001"))
    (other / "cyst_cell.fbbt_mapping.json").write_text(m("cyst cell", "FBbt:00000002"))
    (proj / "type_mapping" / "cyst_cell.fbbt_mapping.json").write_text(m("cyst cell", "FBbt:00000003"))
    anns = [{"label": "h_epithelial cell_head", "type": "epithelial cell_head"},
            {"label": "b_cyst cell", "type": "cyst cell"},
            {"label": "h_neuron 5", "type": "neuron 5"},
            {"label": "h_unannotated", "type": "unannotated", "unannotated": True}]
    (proj / "cell_type_annotations.json").write_text(json.dumps({"annotations": anns}))
    held = lambda a: a.get("unannotated") or a["type"].startswith("neuron ")  # noqa: E731
    n, kept, missing = mod.expand(proj, [proj / "type_mapping", other],
                                  {"epithelial cell_head": "epithelial cell"}, held)
    assert (n, kept, missing) == (2, [], [])
    got = {p.name: json.loads(p.read_text()) for p in (proj / "mapping").glob("*.json")}
    assert got["h_epithelial_cell_head.fbbt_mapping.json"]["best_match"]["fbbt_id"] == "FBbt:00000001"
    assert got["b_cyst_cell.fbbt_mapping.json"]["best_match"]["fbbt_id"] == "FBbt:00000003"  # own first
    assert got["b_cyst_cell.fbbt_mapping.json"]["cluster_label"] == "b_cyst cell"


def test_geo_title_regex_without_set_group():
    mod = _script("build_samples_from_geo")
    parse = mod.title_parser(r"regex:(?P<timepoint>Adult|P\d+)[_-]?(?P<biorep>[^_-].*?)_scRNAseq")
    assert parse("P70-5_scRNAseq")["sample_id"] == "P70_5"
    assert parse("Adult1_scRNAseq")["sample_id"] == "Adult_1"
    p = parse("Adult_1d_F_3rd_scRNAseq")
    assert (p["set"], p["timepoint"], p["biorep"]) == (None, "Adult", "1d_F_3rd")


def test_update_gene_ids_annotation_id_features(tmp_path, monkeypatch):
    """`features_keyed_by: annotation_id`: the prefix is stripped, the gene Chado records
    for the annotation id becomes the input FBgn, the feature name stays the symbol."""
    import gzip
    mod = _script("update_gene_ids")
    (tmp_path / ".cache" / "f").mkdir(parents=True)
    with gzip.open(tmp_path / ".cache" / "f" / "features.tsv.gz", "wt") as fh:
        fh.write("Dmel_CG31240\tDmel_CG31240\tGene Expression\nDmel_CG0000\tDmel_CG0000\tGene Expression\n")
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "chado_annotation_lookup", lambda ids: {"CG31240": "FBgn0011701"})
    cfg = {"expression": {"features_file": "f/features.tsv.gz", "features_keyed_by": "annotation_id",
                          "annotation_id_prefix": "Dmel_"}}
    assert mod.features(cfg) == [("FBgn0011701", "Dmel_CG31240"), ("", "Dmel_CG0000")]


def test_geo_sample_groups_merge_libraries_of_one_sample():
    mod = _script("build_samples_from_geo")
    sb = {"sample_groups": {"Normal_sample_3": "Normal_sample_2"}}
    assert mod.sample_group({"sample_id": "Normal_sample_3"}, sb) == "Normal_sample_2"
    assert mod.sample_group({"sample_id": "Normal_sample_1"}, sb) == "Normal_sample_1"
    assert mod.sample_group({"sample_id": "x"}, {}) == "x"


def test_tissue_labels_shorten_sample_labels(tmp_path, monkeypatch):
    """`sample_build.tissue_labels` changes only the tissue shown in the Sample label."""
    import vfb_scrnaseq.build as b
    s = {"vfbseq_id": "VFBseq_00000001", "tissue_raw": "P70 optic lobe", "age_raw": "P70%", "biorep": "5"}
    cfg = {"sample_build": {"tissue_labels": {"P70 optic lobe": "optic lobe"}}}
    tissue = (cfg["sample_build"]["tissue_labels"]).get(s["tissue_raw"], s["tissue_raw"])
    assert ", ".join([tissue, s["age_raw"], f"rep {s['biorep']}"]) == "optic lobe, P70%, rep 5"
    assert "tissue_labels" in open(b.__file__).read()


def test_expand_type_mappings_clustering_dirs(tmp_path):
    mod = _script("expand_type_mappings")
    proj = tmp_path / "p"
    (proj / "type_mapping" / "immature").mkdir(parents=True)
    for d, fb in ((proj / "type_mapping", "FBbt:00000001"), (proj / "type_mapping" / "immature", "FBbt:00000002")):
        (d / "L1.fbbt_mapping.json").write_text(json.dumps({"cluster_label": "L1", "best_match": {"fbbt_id": fb}}))
    anns = [{"label": "P15_1", "type": "L1", "clustering": "P15"}, {"label": "adult_1", "type": "L1", "clustering": "adult"}]
    (proj / "cell_type_annotations.json").write_text(json.dumps({"annotations": anns}))
    n, _, missing = mod.expand(proj, [proj / "type_mapping"], {}, None, {"P15": "immature"})
    assert (n, missing) == (2, [])
    got = {p.stem: json.loads(p.read_text())["best_match"]["fbbt_id"] for p in (proj / "mapping").glob("*.json")}
    assert got == {"P15_1.fbbt_mapping": "FBbt:00000002", "adult_1.fbbt_mapping": "FBbt:00000001"}


def test_geo_sample_age_falls_back_to_config():
    """`sample_build.age` is used only when GEO records no age."""
    from types import SimpleNamespace
    mod = _script("build_samples_from_geo")
    sb = {"age": "wandering third instar larva"}
    assert mod.sample_age(SimpleNamespace(stage_hint=None), sb) == "wandering third instar larva"
    assert mod.sample_age(SimpleNamespace(stage_hint="P70%"), sb) == "P70%"
    assert mod.sample_age(SimpleNamespace(stage_hint=None), {}) is None


def test_geo_sample_stock_falls_back_to_config():
    """`sample_build.stock` gives every sample its stock when the sample's group has no
    `stock_map` entry."""
    mod = _script("build_samples_from_geo")
    assert mod.sample_stock({"set": None}, {"stock": ["FBst0086858"]}) == ["FBst0086858"]
    sb = {"stock_map": {"W1118": ["FBst0005905"]}, "stock": ["FBst0000001"]}
    assert mod.sample_stock({"set": "W1118"}, sb) == ["FBst0005905"]
    assert mod.sample_stock({"set": None}, {}) is None
