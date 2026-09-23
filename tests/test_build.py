"""build_entities on the real worked-example project: checks the assembled records
carry the recently-wired fields (dataset site/publication/gene counts, sample
sex/stock CURIEs, a Publication :pub node, cluster cell_type). Offline and
side-effect-free: the KB pub lookup and the registry save are stubbed out.
"""

import pytest

from vfb_scrnaseq import build

PROJECT = "kurmangaliyev_2020"


@pytest.fixture
def entities(monkeypatch):
    # no network (KB) and no registry write during the test
    monkeypatch.setattr(build, "resolve_pub",
                        lambda pmid=None, doi=None, fallback_fbrf=None:
                        {"fbrf": fallback_fbrf, "pmid": pmid, "iri": None, "source": "config"})
    monkeypatch.setattr(build.IDRegistry, "save", lambda self: None)
    return build.build_entities(PROJECT)


def _one(entities, etype):
    got = [e for e in entities if e["type"] == etype]
    assert got, f"no {etype} entity"
    return got


def test_dataset_identifier_and_xrefs(entities):
    ds, = _one(entities, "Dataset")
    assert ds["id"].startswith("http://virtualflybrain.org/reports/VFBseq_")  # minted IRI, not GEO
    assert ds["accession"] == "GSE156455"          # GEO accession is an xref
    assert ds["site"] == "vfb:GEO"                 # VFB Site node CURIE
    assert ds["publication"].startswith("FlyBase:FBrf")
    assert isinstance(ds["total_gene_count"], int) and ds["total_gene_count"] > 0
    assert isinstance(ds["filtered_gene_count"], int) and ds["filtered_gene_count"] > 0


def test_publication_pub_node(entities):
    pubs = _one(entities, "Publication")
    assert len(pubs) == 1
    assert pubs[0]["id"].startswith("FlyBase:FBrf")
    assert pubs[0]["neo_label"] == "pub"


def test_samples_sex_and_stock_curies(entities):
    samples = _one(entities, "Sample")
    for s in samples:
        assert s["sex"] == "FBbt:00007011"                       # female, confirmed from paper
        assert s["stock"] and all(x.startswith("FlyBase:FBst") for x in s["stock"])
    # a pooled DGRP sample links many stocks; a w1118 sample links one
    stock_counts = sorted({len(s["stock"]) for s in samples})
    assert stock_counts[0] == 1 and stock_counts[-1] > 1


def test_clusters_have_celltype(entities):
    clusters = _one(entities, "Cluster")
    assert any(c.get("cell_type") for c in clusters)
    assert all(c["id"].startswith("http://virtualflybrain.org/reports/VFBseq_") for c in clusters)
