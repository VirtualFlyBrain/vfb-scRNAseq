"""emit with an extension schema: one in another repo that imports the master schema as
`vfb_scrnaseq` and adds a Sample subclass and its own container (as vfb-EPseq-ontology
does). Validation follows the import; linkml-data2owl gets a merged copy."""

import gzip

import pytest

from vfb_scrnaseq import emit

EXTENSION = """\
id: http://example.org/test_extension
name: test_extension
imports:
  - linkml:types
  - vfb_scrnaseq
prefixes:
  linkml: https://w3id.org/linkml/
default_range: string
classes:
  DriverSample:
    is_a: Sample
    attributes:
      expression_pattern:
        range: Thing
        annotations:
          owl.fstring: ClassAssertion( {V} {id} )
  TestContainer:
    is_a: Container
    tree_root: true
    attributes:
      driver_samples: { range: DriverSample, multivalued: true, inlined_as_list: true }
"""

DS = "http://virtualflybrain.org/reports/VFBseq_00000001"
SA = "http://virtualflybrain.org/reports/VFBseq_00000002"
ENTITIES = [
    {"type": "Dataset", "id": DS, "name": "ds", "neo_label": ["DataSet"]},
    {"type": "DriverSample", "id": SA, "name": "s1", "associated_dataset": DS,
     "neo_label": ["Sample"], "sample_tissue": ["FBbt:00000004"], "stage": "FBdv:00005369",
     "expression_pattern": "vfb:VFBexp_FBtp0117228FBtp0117182"},
]


@pytest.fixture
def schema(tmp_path):
    p = tmp_path / "test_extension.yaml"
    p.write_text(EXTENSION)
    return p


def test_load_schema(schema):
    sch = emit.load_schema(schema)
    assert sch.container == "TestContainer"
    assert sch.groups["DriverSample"] == "driver_samples"
    assert sch.groups["Dataset"] == "datasets"       # inherited from Container
    assert emit.load_schema().container == "Container"


def test_unknown_entity_type(schema):
    with pytest.raises(ValueError, match="no list"):
        emit.container_from_entities([{"type": "Nonesuch", "id": "x"}], schema)


def test_emit_owl(schema, tmp_path):
    out = emit.emit_owl(ENTITIES, tmp_path / "out.ofn", schema_path=schema)
    text = out.read_text()
    sa = "vfb:VFBseq_00000002"
    for axiom in (f"ClassAssertion(FBcv:0003024 {sa})",                  # Sample's own
                  f"ClassAssertion(vfb:VFBexp_FBtp0117228FBtp0117182 {sa})",  # the extension's
                  f"ClassAssertion(ObjectSomeValuesFrom(RO:0002131 FBbt:00000004) {sa})"):
        assert axiom in text, axiom


def test_emit_ttl_strips_container(schema, tmp_path):
    out = emit.emit_ttl(ENTITIES, tmp_path / "out.ttl", schema_path=schema)
    assert "TestContainer" not in out.read_text()


def test_validate_rejects_unknown_slot(schema):
    bad = [dict(ENTITIES[1], driver="x")]
    with pytest.raises(RuntimeError, match="linkml-validate failed"):
        emit.validate(emit.container_from_entities(bad, schema), schema)


def test_expression_without_extent(schema, tmp_path):
    rows = [("VFBseq_00000002", "s1", "FBgn0000003", "7SLRNA:CR32864", 2.3, None)]
    out = emit.emit_expression_owl(rows, tmp_path / "exp.owl.gz", schema_path=schema)
    text = (gzip.open(out, "rt") if out.suffix == ".gz" else open(out)).read()
    assert "expression_level" in text and "expression_extent" not in text
