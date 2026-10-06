# Mip/OCT

*Cluster `Mip/OCT` (Seurat res-2.0 cluster 64 dominant contributor; 26 cells;
ages 0-50 days, day 15 not sampled) in Davie et al. 2018 (GSE107451, 57K
adult brain). A small neuropeptide-co-expression subcluster, not explicitly
named in Table S2.*

## Summary

`Mip/OCT` groups cells co-expressing the neuropeptide Mip (myoinhibitory
peptide) with an octopaminergic (OCT) identity. Its dominant parent is res-2.0
cluster 64 ("Octopaminergic-Tyraminergic"), the same cluster the paper split
by Tbh into Octopaminergic and Tyraminergic subclusters. Unlike those two,
`Mip/OCT` is not one of the explicitly named worked examples in the text
(which cites CCAP/Hug neurons, Ilp2/3/5 insulin-producing cells, and Pdf+
LNv as products of the neuropeptide-focused re-clustering of 1,269
high-neuropeptide-UMI cells). Given its small size, its "marker1/celltype2"
naming (matching the atlas's convention for co-expression subclusters, e.g.
AstA/Nplp1, adPN/C15&kn), and its parent-cluster composition, `Mip/OCT` is
most plausibly a small octopaminergic (Tbh+) subset additionally expressing
Mip, recovered via that same neuropeptide re-clustering strategy rather than
being a directly Table-S2-annotated res-2.0 subcluster. This identification
is an inference from label composition and naming convention, not a direct
textual statement - moderate confidence only.

## Markers

Parent res-2.0 cluster 64 markers: Vmat, Tdc2, Tbh, SIFa, Sox21a, Lim1,
CR44165, Imp, Nep1/2, hig. Mip is not among the top 20 parent-cluster
markers (expected, given only 26 of ~320 parent-cluster cells express it);
Mip is independently confirmed elsewhere in the paper as a target gene of
the Dimm-regulated peptidergic network (SCENIC analysis).

## Location

Not independently established here; if genuinely an octopaminergic subset,
locations would overlap the broader octopaminergic distribution.

## Function

Presumed co-transmission of octopamine and the neuropeptide Mip; specific
behavioural role not established in this atlas.

## Label provenance

No Table S2 row names "Mip/OCT" directly. `label_validation.tsv` flags it as
arising from "S2 neuropeptide re-clustering (cells from multiple res-2.0
clusters)," the same provenance category as `LNv`.

## Mapping notes

Treat as a possible cell state/co-expression subset rather than an
established discrete cell type: the identity ("Mip-expressing octopaminergic
neurons") is inferred, not directly named by the authors, and no anatomical
location is given. Any FBbt mapping should be flagged low-confidence and, if
no exact term exists, should not go beyond a generic octopaminergic-neuron
parent with a note on Mip co-expression.
