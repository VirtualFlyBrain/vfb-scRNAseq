# Dm9

*Cluster `Dm9` (Seurat res-2.0 cluster 74; 139 cells; ages 0-50 days) in Davie
et al. 2018 (GSE107451, 57K adult brain). GEO-only label for an Unannotated,
ort+/VGlut+ cluster; marker profile is consistent with, but not confirmed as,
Dm9.*

## Summary

The GEO label "Dm9" is not annotated in Table S2 (Unannotated - REVIEW) and
Dm9 is not named anywhere in the Davie et al. 2018 main text. The cluster's
markers - ort (histamine receptor) and VGlut (glutamatergic) - are consistent
with the general criterion the paper uses to flag R7/R8-photoreceptor-
postsynaptic optic-lobe cells, and are also consistent with Dm9's later
characterisation elsewhere in the literature as an ort-expressing, glutamatergic
medulla amacrine cell providing feedback to R7/R8 (a finding published after
this 2018 paper, so not something the authors could have annotated).

## Markers

- ort, VGlut - histaminergic-input-receiving, glutamatergic.
- Octbeta1R, Oamb, SPR, SIFaR - several aminergic/neuropeptide receptor genes,
  not diagnostic of a specific cell type on their own.
- Other top markers: CG8034, Fife, Sytalpha, Ca-alpha1T, Ggamma30A, fd59A,
  kcc, dve, unc-13-4A.

## Location

- Optic lobe medulla (inferred from ort/VGlut co-expression); specific layer
  not established by the authors for this cluster.

## Function

- If confirmed as Dm9, expected role is glutamatergic feedback/lateral
  interaction onto R7/R8 photoreceptor terminals in the medulla. Not directly
  stated by Davie et al. 2018 for this cluster.

## Label provenance

Table S2 res-2.0 cluster 74: Unannotated, no method, no references -
`label_validation.tsv`: "named in GEO; S2 res-2.0 Unannotated - REVIEW". The
GEO label likely reflects a later curator assignment based on ort/VGlut
marker match to subsequently published Dm9 characterisations, not an
annotation made by Davie et al. 2018 themselves.

## Mapping notes

Plausible single-type match to Dm9, but confidence rests on markers general
to a class of R7/R8-postsynaptic medulla cells rather than a Dm9-specific
signature, and the identity was not made by the original authors. Treat as
REVIEW-level: a reasonable candidate exactMatch to Dm9 if the mapping step's
external ontology definition for Dm9 is markers-consistent (ort+, glutamatergic
medulla amacrine), but not paper-confirmed.
