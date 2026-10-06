# Lawf2

*Cluster `Lawf2` (Seurat res-2.0 cluster 72; 173 cells; ages 0-50 days) in
Davie et al. 2018 (GSE107451, 57K adult brain). One of two lamina wide-field
(Lawf) neuron clusters identified directly at res-2.0 by literature markers.*

## Summary

Lawf2 (lamina wide-field neuron 2) is an optic-lobe interneuron with
processes spanning multiple lamina cartridges (a wide-field, rather than
columnar, arborisation pattern), distinct from the small-field lamina
monopolar (L1-L5) and centrifugal (C2/C3) neurons, and from its sister type
Lawf1. The paper identified this cluster directly, using the additional
expression of Lim1 on top of eya and hth to distinguish it from Lawf1 (main
text: "using the expression of eya, hth, and Lim1, we were able to identify
separate clusters for the two types of lamina wide-field (Lawf) neurons:
Lawf1 (eya and hth) and Lawf2 (eya, hth, and Lim1)"; Chen et al., 2016).

## Markers

- eya, hth and Lim1 co-expression — Lim1 is the marker distinguishing Lawf2
  from Lawf1 (Chen et al., 2016).
- Lim1 appears among the Table S3 top markers for this cluster (mbl,
  Eip63F-1, CG14274, CG12672, CG10257, DIP-beta, CG32982, CG33639, hbn,
  Fer2, CG42342, dpr17, bi, BicD, CG11317, CG42674, opa, Lim1, CngA,
  CG43795), directly consistent with the paper's marker call; eya and hth
  themselves are not in the top-20 list.

## Location

- **Neuropil:** lamina and proximal medulla; wide-field arborisation
  spanning multiple optic cartridges (as opposed to the single-cartridge
  span of L1-L5).
- **Cell class:** optic lobe wide-field interneuron (class N).

## Function

- Lamina wide-field neurons are thought to integrate signal across multiple
  ommatidial columns, contributing to spatial pooling/gain-control in early
  visual processing, in contrast to the columnar, single-cartridge L-neurons
  and centrifugal C-neurons.

## Label provenance

Table S2 res-2.0 cluster 72 is annotated "Lawf2" directly by literature
markers (Chen et al., 2016; Konstantinides et al., 2018). label_validation.tsv
records this as an exact match, no REVIEW flag, and no subclustering was
performed on this cluster.

## Mapping notes

Lawf2 is called directly at res-2.0 by specific literature markers (eya,
hth, Lim1) and is not merged with any other cell type in this atlas; an FBbt
term for "lamina wide-field neuron Lawf2" is expected and this cluster
should map to it as a single type, high confidence.
