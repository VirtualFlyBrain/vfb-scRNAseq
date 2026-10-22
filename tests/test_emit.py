"""emit: the Container index node is stripped, and the recently-added slots
(site, publication, sex, stock, gene counts) validate and render with the right
predicates. Uses the standard LinkML tools via emit_ttl (validation included)."""

import rdflib
from rdflib import RDF, Literal, URIRef

from vfb_scrnaseq import emit

VFB = "http://virtualflybrain.org/reports/"
DS = URIRef(VFB + "VFBseq_00000001")
SA = URIRef(VFB + "VFBseq_00000002")

BFO = "http://purl.obolibrary.org/obo/BFO_"
BAO = "http://www.bioassayontology.org/bao#BAO_"
OBOINOWL = "http://www.geneontology.org/formats/oboInOwl#"
NEO_CUSTOM = "http://n2o.neo/custom/"
DCTERMS = "http://purl.org/dc/terms/"
FLYBASE = "http://flybase.org/reports/"


def _entities():
    return [
        {"type": "Dataset", "id": str(DS), "name": "ds", "accession": "GSE156455",
         "neo_label": ["DataSet"], "site": "vfb:GEO", "publication": "FlyBase:FBrf0247594",
         "assay_type": "FBcv:0009000", "total_gene_count": 15700, "filtered_gene_count": 7031},
        {"type": "Publication", "id": "FlyBase:FBrf0247594", "neo_label": ["pub"]},
        {"type": "Sample", "id": str(SA), "name": "sample", "associated_dataset": str(DS),
         "neo_label": ["Sample"], "sample_tissue": ["FBbt:00003701"], "stage": "FBdv:00007001",
         "sex": "FBbt:00007011", "stock": ["FlyBase:FBst0005905"],
         "genotype_includes": ["FlyBase:FBco0000215"]},
        {"type": "Cluster", "id": str(URIRef(VFB + "VFBseq_00000047")), "name": "cl",
         "associated_dataset": str(DS), "cell_number": 100, "neo_label": ["Cluster"],
         "cell_type": ["FBbt:00003791"], "total_gene_count": 11538, "filtered_gene_count": 2536},
    ]


def _graph(tmp_path):
    out = tmp_path / "out.ttl"
    emit.emit_ttl(_entities(), out)          # validates against the schema, then converts
    g = rdflib.Graph(); g.parse(out, format="turtle")
    return g


def test_container_node_stripped(tmp_path):
    g = _graph(tmp_path)
    # the tree_root Container index node must not leak into the emitted RDF
    assert not list(g.subjects(RDF.type, emit.CONTAINER_TYPE))
    schema_ns = "http://github.org/vfb/vfb-scRNAseq-ontology/VFB_scRNAseq/"
    leaked = [p for p in set(g.predicates()) if str(p).startswith(schema_ns)]
    assert leaked == [], f"container slots leaked: {leaked}"


def test_dataset_site_publication_and_counts(tmp_path):
    g = _graph(tmp_path)
    assert (DS, URIRef(DCTERMS + "references"), URIRef(FLYBASE + "FBrf0247594")) in g
    assert (DS, URIRef(OBOINOWL + "hasDbXref"), URIRef(VFB + "GEO")) in g
    assert (DS, URIRef(NEO_CUSTOM + "total_gene_count"), Literal(15700)) in g
    assert (DS, URIRef(NEO_CUSTOM + "filtered_gene_count"), Literal(7031)) in g


def test_sample_sex_and_stock(tmp_path):
    g = _graph(tmp_path)
    # sex as part_of FBbt organism; stock as is-derived-from FBst
    assert (SA, URIRef(BFO + "0000050"), URIRef("http://purl.obolibrary.org/obo/FBbt_00007011")) in g
    assert (SA, URIRef(BAO + "0095000"), URIRef(FLYBASE + "FBst0005905")) in g
    # genetic entities in the genotype: GENO has_genotype
    assert (SA, URIRef("http://purl.obolibrary.org/obo/GENO_0000222"),
            URIRef(FLYBASE + "FBco0000215")) in g


def test_cluster_title_is_a_definition(tmp_path):
    ents = _entities()
    ents[-1]["title"] = "Cells assigned the type 'x' by the authors' classifier."
    out = tmp_path / "t.ttl"
    emit.emit_ttl(ents, out)
    g = rdflib.Graph(); g.parse(out, format="turtle")
    iao = URIRef("http://purl.obolibrary.org/obo/IAO_0000115")
    assert list(g.objects(URIRef(VFB + "VFBseq_00000047"), iao)) == [
        Literal("Cells assigned the type 'x' by the authors' classifier.")]


def test_cluster_stage_from_its_own_expression(tmp_path):
    ents = _entities()
    ents[-1]["stage"] = "FBdv:00005311"
    out = tmp_path / "s.ttl"
    emit.emit_ttl(ents, out)
    g = rdflib.Graph(); g.parse(out, format="turtle")
    assert (URIRef(VFB + "VFBseq_00000047"), URIRef("http://purl.obolibrary.org/obo/RO_0002490"),
            URIRef("http://purl.obolibrary.org/obo/FBdv_00005311")) in g
