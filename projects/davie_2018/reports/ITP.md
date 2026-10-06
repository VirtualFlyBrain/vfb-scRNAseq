# ITP

*Cluster `ITP` (Seurat res-2.0 cluster 32, "Unannotated" at res-2.0; 25 cells;
ages 0-15,3,6,9 days) in Davie et al. 2018 (GSE107451, 57K adult brain). A
neuropeptide-defined subcluster from the paper's 1,269-cell re-clustering of
neuropeptide-high cells (Figure 2K).*

## Summary

A subcluster of ITP (ion transport peptide)-expressing neurons pulled out by
the authors' neuropeptide re-clustering. ITP+ neurons in Drosophila are a
small, previously characterised set that includes clock-circuit-associated
cells (e.g. the ITP-expressing lateral neuron, part of the circadian network)
and other CNS/abdominal-ganglion neurosecretory cells reported in the
literature; the paper itself gives no further annotation or reference for
this specific subcluster beyond the ITP marker identity. Assignment back to
res-2.0 clusters is highly ambiguous (spread across clusters 32, 36, 46, 43,
59), reflecting that these are rare cells recovered only by the dedicated
neuropeptide-focused reclustering, not a clean res-2.0 population.

## Markers

No dedicated Table S3 marker list exists for the ITP subcluster itself; the
listed markers are for its nominal res-2.0 parent cluster 32, which are
generic/housekeeping (ribosomal, mitochondrial translation genes: mRpL27,
mRpL52, mRpL28, mRpL51, mRpL24, mRpS25, l(2)tid, Tim9a) and not informative
about neuronal identity - consistent with ITP+ cells being rare cells embedded
in an otherwise unrelated res-2.0 cluster.

## Location

Not established by this atlas; ITP-expressing neurons described in the wider
literature include clock-associated lateral neurons and neurosecretory cells
in the pars lateralis/abdominal ganglion, but this paper does not localise its
ITP subcluster to a specific site.

## Function

Neuromodulatory/neurosecretory via ion transport peptide signalling; in the
clock circuit, ITP+ neurons contribute to circadian output, but this
attribution is from the general literature, not demonstrated in this dataset.

## Label provenance

Table S2 res-2.0 cluster 32 = "Unannotated" (no method/references).
`label_validation.tsv`: status "S2 neuropeptide re-clustering (cells from
multiple res-2.0 clusters)" - the ITP label comes entirely from the Figure 2K
neuropeptide subclustering, not from any primary res-2.0 annotation; the
res-2.0 cluster id recorded is only "where most cells came from" and is itself
transcriptionally uninformative (ribosomal/mitochondrial genes).

## Mapping notes

Likely corresponds to a real, literature-known ITP-expressing neuron marker
identity, but the atlas cluster itself is small (n=25), ambiguous in origin,
and not further resolved into the specific known ITP+ subtypes (e.g. clock
LNd vs. other ITP+ populations). Best treated as "ITP-expressing neurons"
at a marker-defined granularity - a plausible single-marker group, not
necessarily a single anatomical neuron type - pending confirmation from the
cited literature on which ITP+ population(s) it represents.
