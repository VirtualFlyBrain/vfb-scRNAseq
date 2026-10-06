# Mip/ITP

*Cluster `Mip/ITP` (Seurat res-2.0 cluster 46, i.e. the parent "Peptidergic"
cluster; 9 cells; ages 0,1,3,30,50 days) in Davie et al. 2018 (GSE107451, 57K
adult brain). A neuropeptide co-expression subcluster from the paper's
1,269-cell re-clustering of all cells with >=100 UMIs for any neuropeptide
gene (Figure 2K).*

## Summary

A very small (n=9) subcluster of cells co-expressing the neuropeptide genes
Mip (myoinhibitory peptide) and ITP (ion transport peptide), recovered from
the neuropeptide-focused re-clustering described in the paper's rare-cell-type
section. Assignment back to the primary res-2.0 clustering is itself
ambiguous - these 9 cells split across four different res-2.0 clusters (46:
6 cells, 17: 1, 1: 1, 36: 1) - underlining that this is a small, marginal
group defined purely by co-expression in the subclustering exercise rather
than a population with a single stable transcriptomic identity elsewhere in
the dataset.

## Markers

No separate Table S3 marker list exists for this subcluster; the only
available markers are those of its res-2.0 parent cluster 46 ("Peptidergic":
Hug, Proc, twit, rhea, Crz, ITP, ...), which are not specific to a Mip/ITP
co-expressing group.

## Location

Not resolved; ITP-expressing neurons in Drosophila are a small, scattered set
(including clock-associated and abdominal-ganglion populations) and Mip is
also broadly distributed (see the `Mip` and `ITP` reports), so no single
neuropil can be inferred for this specific co-expression group from the
available evidence.

## Function

Not established for this specific group; consistent only with general
neuropeptide (Mip and ITP) co-release if genuine, which would imply
neuromodulatory/neurosecretory function.

## Label provenance

Not a Table S2 res-2.0 annotation in its own right. `label_validation.tsv`
flags it as "S2 neuropeptide re-clustering (cells from multiple res-2.0
clusters)" - i.e. it derives from the authors' Figure 2K subclustering of the
1,269 neuropeptide-high cells, not from the primary whole-brain clustering.
Its nominal res-2.0 parent (cluster 46) is the same "Peptidergic" cluster used
for the `Peptidergic` report, but only 6 of its 9 cells actually fall there.

## Mapping notes

Almost certainly a transcriptomic co-expression artefact of the small-n
subclustering rather than a known, anatomically defined neuron type: n=9,
ambiguous parent-cluster assignment, and no independent marker set or
literature reference support it as a discrete population. If Mip/ITP
co-expression does mark a genuine small neuron group, it is not established by
this paper; treat as low-confidence / possible technical grouping rather than
a mappable cell type, and flag for caution in FBbt mapping.
