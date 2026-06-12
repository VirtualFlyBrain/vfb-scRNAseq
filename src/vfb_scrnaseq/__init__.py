"""vfb_scrnaseq: produce RDF metadata for Drosophila scRNAseq datasets.

Pipeline (cell-type-annotation focus):
    project config + curated cluster labels
        -> literature reports (atlas-chat report pipeline)
        -> FBbt mapping candidates (map-clusters-to-fbbt agent) + human review
        -> LinkML objects (build)
        -> RDF/TTL (emit)

The LinkML schema in ``schema/VFB_scRNAseq_schema.yaml`` is the new master copy,
duplicated from VirtualFlyBrain/vfb-scRNAseq-ontology (to be deprecated).
"""

__version__ = "0.0.0"
