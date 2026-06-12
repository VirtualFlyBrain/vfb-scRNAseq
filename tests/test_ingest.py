from vfb_scrnaseq.ingest import parse_soft, soft_url

# A trimmed SOFT fixture in GEO's text format (shape mirrors GSE156455).
SOFT_FIXTURE = """\
^SERIES = GSE156455
!Series_title = Transcriptional programs of circuit assembly in the Drosophila visual system
!Series_summary = scRNA-seq across pupal development.
!Series_summary = Second summary line.
!Series_geo_accession = GSE156455
!Series_platform_id = GPL25244
!Series_relation = BioProject: https://www.ncbi.nlm.nih.gov/bioproject/PRJNA658010
!Series_relation = SRA: https://www.ncbi.nlm.nih.gov/sra?term=SRP278058
!Series_supplementary_file_1 = ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE156nnn/GSE156455/suppl/GSE156455_metadata.tsv.gz
^SAMPLE = GSM4731869
!Sample_title = optic lobe P24 rep A
!Sample_geo_accession = GSM4731869
!Sample_organism_ch1 = Drosophila melanogaster
!Sample_characteristics_ch1 = developmental stage: pupa 24h APF
!Sample_characteristics_ch1 = Sex: mixed
!Sample_characteristics_ch1 = strain: DGRP
!Sample_relation = BioSample: https://www.ncbi.nlm.nih.gov/biosample/SAMN15700001
!Sample_relation = SRA: https://www.ncbi.nlm.nih.gov/sra?term=SRX9000001
!Sample_supplementary_file_1 = ftp://ftp.ncbi.nlm.nih.gov/.../GSM4731869_matrix.mtx.gz
^SAMPLE = GSM4731870
!Sample_title = optic lobe adult rep B
!Sample_geo_accession = GSM4731870
!Sample_organism_ch1 = Drosophila melanogaster
!Sample_characteristics_ch1 = developmental stage: adult
!Sample_characteristics_ch1 = Sex: female
"""


def test_soft_url_shape():
    url = soft_url("GSE156455")
    assert "acc=GSE156455" in url
    assert "form=text" in url and "view=full" in url


def test_parse_series_level():
    s = parse_soft(SOFT_FIXTURE)
    assert s.accession == "GSE156455"
    assert s.title.startswith("Transcriptional programs")
    # multi-line summary is concatenated
    assert "Second summary line." in s.summary
    assert s.platform_ids == ["GPL25244"]
    assert s.bioproject == "PRJNA658010"
    assert s.sra_study == "SRP278058"
    assert s.supplementary_files[0].endswith("GSE156455_metadata.tsv.gz")


def test_parse_samples():
    s = parse_soft(SOFT_FIXTURE)
    assert [sm.accession for sm in s.samples] == ["GSM4731869", "GSM4731870"]

    first = s.samples[0]
    assert first.organism == "Drosophila melanogaster"
    assert first.stage_hint == "pupa 24h APF"
    assert first.sex_hint == "mixed"
    assert first.characteristic("strain") == "DGRP"
    assert first.relations["SRA"] == "SRX9000001"
    assert first.relations["BioSample"] == "SAMN15700001"
    assert first.supplementary_files[0].endswith("GSM4731869_matrix.mtx.gz")

    second = s.samples[1]
    assert second.stage_hint == "adult"
    assert second.sex_hint == "female"
    # absent characteristic -> None
    assert second.characteristic("strain") is None


def test_missing_series_raises():
    import pytest

    with pytest.raises(ValueError):
        parse_soft("!Sample_title = orphan\n")
