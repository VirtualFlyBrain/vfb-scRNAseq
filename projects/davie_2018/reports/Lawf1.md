# Lawf1

*Cluster `Lawf1` (Seurat res-2.0 cluster 58; 246 cells; ages 0-50 days) in
Davie et al. 2018 (GSE107451, 57K adult brain). One of two lamina wide-field
(Lawf) neuron clusters identified directly at res-2.0 by literature markers.*

## Summary

Lawf1 (lamina wide-field neuron 1) is an optic-lobe interneuron with
processes spanning multiple lamina cartridges (a wide-field, rather than
columnar, arborisation pattern), distinct from the small-field lamina
monopolar (L1-L5) and centrifugal (C2/C3) neurons. The paper identified this
cluster directly, using the combination of eya and hth expression to
distinguish it from Lawf2 (eya, hth and Lim1) (main text: "using the
expression of eya, hth, and Lim1, we were able to identify separate clusters
for the two types of lamina wide-field (Lawf) neurons: Lawf1 (eya and hth)
and Lawf2 (eya, hth, and Lim1)"; Chen et al., 2016).

## Markers

- eya and hth co-expression, without Lim1 — the combination distinguishing
  Lawf1 from Lawf2 (Chen et al., 2016).
- hth appears among the Table S3 top markers for this cluster (CG3257, Frq1,
  Eip63F-1, CG8641, Npc2a, dpr3, hth, msi, igl, CG12994, Ggamma30A, CG43795,
  Cngl, luna, app, Fer2, Fas2, CG13954, CG33639, CG15312), consistent with
  the paper's marker call; eya itself is not in the top-20 list.

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

Table S2 res-2.0 cluster 58 is annotated "Lawf1" directly by literature
markers (Chen et al., 2016; Konstantinides et al., 2018). label_validation.tsv
records this as an exact match, no REVIEW flag, and no subclustering was
performed on this cluster.

## Mapping notes

Lawf1 is called directly at res-2.0 by specific literature markers (eya,
hth, not Lim1) and is not merged with any other cell type in this atlas; an
FBbt term for "lamina wide-field neuron Lawf1" is expected and this cluster
should map to it as a single type, high confidence.
