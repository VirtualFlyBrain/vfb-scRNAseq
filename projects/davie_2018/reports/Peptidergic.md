# Peptidergic

*Cluster `Peptidergic` (Seurat res-2.0 cluster 46; 155 cells; ages 0-50 days) in
Davie et al. 2018 (GSE107451, 57K adult brain). The main dimm-positive
peptidergic supercluster, annotated directly from literature markers rather
than by the paper's later 1,269-cell neuropeptide re-clustering.*

## Summary

This is the principal peptidergic neuron cluster of the whole-brain atlas: a
population of Dimmed (dimm)-dependent neurosecretory/peptidergic cells
distinguished from other neurons mainly by broad expression of neuropeptide
precursor genes and peptide-processing machinery, not by a single cell-type
identity. The authors themselves used this cluster as the source pool for
finer subclustering (selecting all cells with >=100 UMIs for any neuropeptide
gene and re-clustering 1,269 cells; Figure 2K), from which they pulled out
CCAP, Hugin (gustatory, subesophageal), IPC (Ilp2/3/5), and LNv (Pdf) neurons,
among others. Cells remaining in the parent "Peptidergic" cluster label are
therefore a heterogeneous mixture of peptidergic neuron types not further
resolved.

## Markers

Top res-2.0 cluster-46 markers: Hug, Proc, twit, rhea, Crz, CG42394, ITP,
CG10527, CG1648, AnxB9, bark, lbm, and others. This gene list itself spans
multiple distinct neuropeptides (Hugin, Proctolin, Corazonin, ITP), consistent
with a mixed population rather than one neuron type.

## Location

Not resolved to a single neuropil; peptidergic/neurosecretory cells in
Drosophila are broadly distributed (protocerebrum, subesophageal ganglion,
pars intercerebralis/lateralis), and this cluster likely pools cells from
several of these sites.

## Function

Neurosecretion/neuromodulation via diverse neuropeptides; unified only by the
shared Dimmed-dependent peptidergic differentiation program (Hadzic et al.,
2015; SCENIC Dimm regulon, Figure 3C/S4B), not by a single physiological role.

## Label provenance

Table S2 res-2.0 cluster 46 = "Peptidergic", method "literature markers", no
specific reference given. `label_validation.tsv`: status "match" (no
discrepancy). This is the parent cluster from which the paper's finer
neuropeptide subclusters (Mip, Mip/ITP, ITP, IPC, AstA/Nplp1, AstA/NPF, Capa,
etc.) were derived by re-clustering; those labels split out defined
subpopulations while "Peptidergic" retains the unresolved remainder.

## Mapping notes

Heterogeneous remainder group, not a single cell type: this is explicitly the
dimm-positive peptidergic bucket left after specific subtypes were carved out.
An honest mapping target is a broad grouping term (e.g. "peptidergic neuron")
rather than any specific FBbt neuron type; treating it as one discrete type
would over-claim precision.
