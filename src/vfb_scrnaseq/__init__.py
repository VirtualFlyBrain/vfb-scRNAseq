"""vfb_scrnaseq: produce RDF metadata for Drosophila scRNAseq datasets.

Pipeline (cell-type-annotation focus):
    project config + author clusters and samples (GEO: ingest; ArrayExpress /
    AnnData: ingest_arrayexpress, ingest_h5ad)
        -> per-type reports (write-cell-type-report agent)
        -> FBbt mapping candidates (map-clusters-to-fbbt agent) + human review
        -> entity records (build)
        -> validated RDF/TTL + OWL (emit)
        -> summary expression statistics + expression OWL (stats, emit)

The LinkML schema in ``schema/VFB_scRNAseq_schema.yaml`` is the new master copy,
imported from VirtualFlyBrain/vfb-scRNAseq-ontology (to be deprecated) and extended
here.
"""

__version__ = "0.0.0"
