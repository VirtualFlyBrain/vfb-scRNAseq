"""Assemble schema-conformant LinkML objects from curated project data.

STUB. Lifts a project (config + curated cluster labels + reviewed FBbt mapping)
into instances of the LinkML classes in ``schema/VFB_scRNAseq_schema.yaml``,
minting ids via :mod:`vfb_scrnaseq.ids` and attaching GEO/SRA accessions as
cross-references.

Intended flow:
    1. Read project ``config.yaml`` -> Dataset (site=GEO, accession=GSE...).
    2. Read GSM list                -> Sample / Assay (accessions as dbxrefs).
    3. Read ``cell_type_annotations.json`` + reviewed mapping.tsv
                                     -> Clustering + Cluster (cell_type -> FBbt).
    4. Return a holder object ready for :mod:`vfb_scrnaseq.emit`.

Pydantic models should be generated from the LinkML schema with::

    gen-pydantic src/vfb_scrnaseq/schema/VFB_scRNAseq_schema.yaml \\
        > src/vfb_scrnaseq/model.py
"""

from __future__ import annotations

from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema" / "VFB_scRNAseq_schema.yaml"


def build_project(project_dir: str | Path):
    """Build LinkML objects for a project directory. TODO: implement."""
    raise NotImplementedError("build_project: pending model generation + curation inputs")
