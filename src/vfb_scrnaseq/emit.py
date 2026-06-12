"""Emit RDF/TTL from schema-conformant LinkML data.

STUB. Predicates and class assertions come straight from the schema's
``slot_uri`` / ``class_uri`` / ``owl.fstring`` annotations, so emission is
largely a call to ``linkml-convert``::

    linkml-convert -s src/vfb_scrnaseq/schema/VFB_scRNAseq_schema.yaml \\
        -t ttl -C Dataset <data.yaml> > out.ttl

The schema uses ``owl.fstring`` / ``owl.template`` annotations to control the
exact OWL produced (e.g. the per-gene expression ClassAssertion). Verify the TTL
against the previous FlyBase-produced output during the migration.
"""

from __future__ import annotations

from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema" / "VFB_scRNAseq_schema.yaml"


def emit_ttl(data, out_path: str | Path):
    """Serialise built LinkML objects to Turtle. TODO: implement."""
    raise NotImplementedError("emit_ttl: pending build step")
