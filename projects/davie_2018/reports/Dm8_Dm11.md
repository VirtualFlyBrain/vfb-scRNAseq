# Dm8/Dm11

*Cluster `Dm8/Dm11` (Seurat res-2.0 cluster 52; 276 cells; ages 0-50 days) in
Davie et al. 2018 (GSE107451, 57K adult brain). GEO-only label for an
Unannotated, ort+/VGlut+ optic-lobe cluster; weak support for a specific
Dm8/Dm11 identity.*

## Summary

The GEO label "Dm8/Dm11" is not annotated in Table S2 (Unannotated - REVIEW)
and is not the pairing the main text discusses. The paper does describe an
unresolved VGlut+/ort+ pairing, but explicitly for a *different* res-2.0
cluster: "Two clusters co-express VGlut and ort, which could be linked to
Tm5c and Dm8, but a division between the two could not be made" - this refers
to this atlas's separate `Tm5c` cluster (res-2.0 cluster 39, S2-annotated
"Dm8/Tm5c", itself flagged REVIEW). Cluster 52 is a distinct, additional
VGlut+/ort+ cluster that the paper does not name at all.

## Markers

- VGlut, ort - glutamatergic, histamine-receptor-positive: consistent with an
  optic-lobe amacrine/interneuron postsynaptic to R7/R8 photoreceptors (the
  general criterion the paper uses for this family of cells).
- DIP-gamma, AstC-R1, Tk, Grd, scro, fd59A, CG13739 among other top markers -
  none of these are markers the paper specifically attributes to Dm8 or Dm11.

## Location

- Optic lobe medulla (inferred from ort/VGlut co-expression pattern shared
  with other R7/R8-postsynaptic clusters); specific layer not established by
  the authors for this cluster.

## Function

- If genuinely Dm8 and/or Dm11, expected to be glutamatergic medulla amacrine
  interneuron(s) downstream of R7/R8 (see e.g. established Dm8 biology:
  Karuppudurai et al., 2014). Not confirmed here.

## Label provenance

Table S2 res-2.0 cluster 52: Unannotated, no method, no references -
`label_validation.tsv`: "named in GEO; S2 res-2.0 Unannotated - REVIEW". The
GEO curator label combines two named cell types (Dm8, Dm11) with a slash,
suggesting an unresolved co-cluster, but this is not corroborated by any
Table S2/S3 annotation, and the paper's only explicit statement about an
unresolved Dm8-containing pair concerns the separate `Tm5c` cluster, not this
one.

## Mapping notes

Possible merged group of two established types (Dm8, Dm11) or possibly
neither - support is limited to a generic ort+/VGlut+ signature shared by
several distinct R7/R8-postsynaptic optic-lobe cell types in this dataset.
Flag as REVIEW-level uncertain; if mapped at all, a common parent covering
R7/R8-postsynaptic medulla amacrine interneurons is the most that is honestly
supported, not an exact Dm8 or Dm11 match.
