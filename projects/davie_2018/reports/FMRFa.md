# FMRFa

*Cluster `FMRFa` (Seurat res-2.0 cluster 16; 44 cells; ages 0, 1, 3, 6, 9, 15,
30, 50 days) in Davie et al. 2018 (GSE107451, 57K adult brain). An
FMRFamide-expressing population from the neuropeptide re-clustering.*

## Summary

FMRFamide (FMRFa) is a classical Drosophila neuropeptide gene expressed by
a numerous and heterogeneous set of distinct neurons throughout the CNS
(e.g. ~90 FMRFa-immunoreactive neurons of many different morphological
types are described by White et al., 1999, spanning brain, subesophageal
zone and ventral nerve cord). It is not a marker of a single cell type, but
of a neurochemical class distributed across many otherwise-unrelated
neurons. This atlas cluster (44 cells) was recovered from the S2
neuropeptide re-clustering of cells with >=100 neuropeptide-gene UMIs; no
Table S2 direct annotation or res-8.0 cross-check exists for it.

## Markers

- FMRFa itself is not among the top Table S3 markers listed (those belong
  to the parent res-2.0 cluster 16: Sp1, Six4, Optix, eya, Dll, salr, jeb,
  pros, mbl, dati, Ddc, etc. — several of these, e.g. Optix, eya, Dll,
  salr, are classic eye/optic-lobe developmental TFs), consistent with
  parent cluster 16 being large and heterogeneous, not FMRFa-specific.

## Location

- FMRFa-expressing neurons are distributed across brain, SEZ and VNC
  (White et al., 1999); this atlas is brain-only, so the captured subset
  is whichever brain FMRFa+ neurons had sufficient UMI counts.

## Function

- Diverse; FMRFa-family peptides modulate cardiac activity, ecdysis,
  and various circuits depending on the specific neuron subtype.

## Label provenance

No REVIEW flag. GEO label "FMRFa" comes solely from the S2 neuropeptide
re-clustering; Table S2 lists the parent res-2.0 cluster 16 as
"Unannotated" with no supporting reference.

## Mapping notes

FMRFa marks a co-expression CLASS spanning many distinct, anatomically
separate neuron types, not a single type. The honest mapping is at the
level of "FMRFamide-expressing neuron" (a broad class term, if one exists
in FBbt) rather than any specific morphological cell type; alternatively
this may be best treated as an unresolved/merged remainder group requiring
a common, non-specific parent term. Confidence in cell-type specificity is
low; confidence that the underlying gene expression (FMRFa) is correctly
identified is high.
