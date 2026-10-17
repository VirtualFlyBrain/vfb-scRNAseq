"""ArrayExpress ingest: IDF/SDRF parsing and config-driven Sample/Assay grouping. Offline."""

import importlib.util
from pathlib import Path

from vfb_scrnaseq import ingest_arrayexpress as ae
from vfb_scrnaseq.ids import IDRegistry

REPO = Path(__file__).resolve().parents[1]


def _builder():
    spec = importlib.util.spec_from_file_location(
        "build_samples_from_arrayexpress", REPO / "scripts" / "build_samples_from_arrayexpress.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_files_url_buckets_by_last_three_digits():
    assert ae.files_url("E-MTAB-10519", "sdrf").endswith(
        "/E-MTAB-/519/E-MTAB-10519/Files/E-MTAB-10519.sdrf.txt")


def test_parse_sdrf_keeps_first_of_repeated_columns():
    text = "Source Name\tProtocol REF\tCharacteristics[sex]\tProtocol REF\n" \
           "s1\tP-1\tmale\tP-2\n\n"
    rows = ae.parse_sdrf(text)
    assert rows == [{"Source Name": "s1", "Protocol REF": "P-1", "Characteristics[sex]": "male"}]


def test_parse_idf():
    idf = ae.parse_idf("Investigation Title\tFly Cell Atlas\t\nPerson Last Name\tLi\tAerts\n")
    assert idf["Investigation Title"] == ["Fly Cell Atlas"] and idf["Person Last Name"] == ["Li", "Aerts"]


def _rows_10x():
    def r(src, ext, sex, erx, bsd):
        return {"Source Name": src, "Extract Name": ext, "Characteristics[sex]": sex,
                "Characteristics[age]": "5", "Characteristics[organism part]": "haltere",
                "Characteristics[strain]": "w1118", "Comment[ENA_EXPERIMENT]": erx,
                "Comment[BioSD_SAMPLE]": bsd}
    return [r("FCA47_S1", "h__FCA47", "male", "ERX1", "SAMEA1"),
            r("FCA47_S1", "h__FCA47", "male", "ERX1", "SAMEA1"),       # second lane, same library
            r("FCA47_S9", "h__FCA47", "male", "ERX2", "SAMEA2"),
            r("FCA48_S4", "h__FCA48", "femal", "ERX3", "SAMEA3")]       # SDRF typo


SB_COMMON = {"assay_method": {"fbcv_id": "FBcv:0009008", "label": "10x sequencing"},
             "sex_column": "Characteristics[sex]", "sex_map": {"femal": "female"},
             "age_column": "Characteristics[age]",
             "age_map": {"5": {"stage": {"fbdv_id": "FBdv:00007080", "label": "day 5 of adulthood"}}},
             "tissue_column": "Characteristics[organism part]",
             "tissue_map": {"haltere": [{"fbbt_id": "FBbt:00004783", "label": "haltere"}]}}


def test_10x_samples_are_extracts_assays_are_libraries(tmp_path):
    mod = _builder()
    sb = dict(SB_COMMON, sample_columns=["Extract Name"], assay_column="Source Name",
              assay_xrefs=["Comment[ENA_EXPERIMENT]", "Comment[BioSD_SAMPLE]"],
              genotype_columns=["Characteristics[strain]"], wild_type_genotypes=["w1118"])
    reg = IDRegistry.load(tmp_path / "reg.json")
    samples, assays, warnings = mod.build(_rows_10x(), sb, "E-MTAB-1", reg, "VFBseq_00000001")
    assert [s["sample_id"] for s in samples] == ["h__FCA47", "h__FCA48"]
    assert [s["n_assays"] for s in samples] == [2, 1]
    assert {s["sex"] for s in samples} == {"male", "female"}                # typo normalised
    assert samples[0]["stage"]["fbdv_id"] == "FBdv:00007080"
    assert samples[0]["sample_tissue"][0]["fbbt_id"] == "FBbt:00004783"
    a1 = next(a for a in assays if a["library_id"] == "FCA47_S1")
    assert a1["accession"] == "ERX1" and a1["dbxrefs"] == ["ERX1", "SAMEA1"]
    assert warnings == []


def test_ss2_samples_group_cells_assays_are_plates(tmp_path):
    mod = _builder()
    def cell(name, sex, part="wing"):
        return {"Source Name": name, "Characteristics[sex]": sex, "Characteristics[age]": "5",
                "Characteristics[organism part]": part, "Characteristics[genotype]": "wild type genotype",
                "Comment[ENA_EXPERIMENT]": "ERX" + name[-2:]}
    rows = [cell("FCA_P1_male_wing_A1", "male"), cell("FCA_P1_male_wing_A2", "male"),
            cell("FCA_P2_male_wing_A1", "male"), cell("FCA_P3_female_wing_A1", "female")]
    sb = dict(SB_COMMON, assay_method={"fbcv_id": "FBcv:0009007", "label": "Smart-seq2"},
              sample_columns=["Characteristics[organism part]", "Characteristics[sex]",
                              "Characteristics[genotype]", "Characteristics[age]"],
              assay_regex={"column": "Source Name", "pattern": r"^FCA_(?P<assay>P\d+)_"},
              assay_xrefs=["Comment[ENA_EXPERIMENT]"],
              genotype_columns=["Characteristics[genotype]"],
              tissue_map={"wing": [{"fbbt_id": "FBbt:00004729", "label": "wing"}]})
    reg = IDRegistry.load(tmp_path / "reg.json")
    samples, assays, _ = mod.build(rows, sb, "E-MTAB-2", reg, "VFBseq_00000001")
    assert len(samples) == 2                                   # wing x male, wing x female
    male = next(s for s in samples if s["sex"] == "male")
    assert male["n_assays"] == 2                               # plates P1, P2
    p1 = next(a for a in assays if a["library_id"] == "P1")
    assert p1["n_sources"] == 2 and p1["accession"] is None and p1["dbxrefs"] == []   # per-cell ids not listed



def test_cross_genotype_links_genetic_entities_and_unmapped_ones_warn(tmp_path):
    """A GAL4 > UAS genotype gets its `genotype_includes_map` entities (no stock); a
    non-wild-type genotype with neither map entry is flagged."""
    mod = _builder()
    rows = _rows_10x()
    for r in rows:
        r["Characteristics[strain]"] = "Cg-GAL4, UAS-lamGFP" if r["Extract Name"].endswith("47") else "drip-GAL4, UAS-nlsGFP"
    sb = dict(SB_COMMON, sample_columns=["Extract Name"], assay_column="Source Name",
              genotype_columns=["Characteristics[strain]"], wild_type_genotypes=["w1118"],
              genotype_includes_map={"Cg-GAL4, UAS-lamGFP": ["FBal0341663", "FBal0119470"]})
    reg = IDRegistry.load(tmp_path / "reg.json")
    samples, _, warnings = mod.build(rows, sb, "E-MTAB-1", reg, "VFBseq_00000001")
    cg = next(s for s in samples if s["genotype"] == "Cg-GAL4, UAS-lamGFP")
    assert cg["genotype_includes"] == ["FBal0341663", "FBal0119470"] and cg["stock"] is None
    drip = next(s for s in samples if s["genotype"] == "drip-GAL4, UAS-nlsGFP")
    assert "genotype_includes" not in drip
    assert any("drip-GAL4, UAS-nlsGFP" in w for w in warnings)

def test_sdrf_corrections_apply_before_grouping_and_leave_a_note(tmp_path):
    mod = _builder()
    rows = _rows_10x()
    for r in rows[:3]:
        r["Characteristics[age]"] = "3"                          # FCA47: wrong age in the SDRF
    sb = dict(SB_COMMON, sample_columns=["Extract Name"], assay_column="Source Name",
              sdrf_corrections=[{"match": {"Extract Name": "h__FCA47", "Characteristics[age]": "3"},
                                 "set": {"Characteristics[age]": "5"}, "note": "age per paper"}])
    reg = IDRegistry.load(tmp_path / "reg.json")
    samples, _, warnings = mod.build(rows, sb, "E-MTAB-1", reg, "VFBseq_00000001")
    s47 = samples[0]
    assert s47["age_raw"] == "5 days" and s47["curation_notes"] == ["age per paper"]
    assert "curation_notes" not in samples[1] and warnings == []
