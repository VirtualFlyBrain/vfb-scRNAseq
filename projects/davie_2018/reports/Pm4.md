# Pm4

*Cluster `Pm4` (Seurat res-2.0 cluster 55; 271 cells; ages 0-50 days) in Davie
et al. 2018 (GSE107451, 57K adult brain). GEO-only label for an
Unannotated res-2.0 cluster; weak, ambiguous support for a fourth Pm type.*

## Summary

The GEO label "Pm4" is not annotated in Table S2 (Unannotated - REVIEW), and
"Pm4" is not mentioned anywhere in the main text of Davie et al. 2018, which
discusses only Pm1, Pm2 and Pm3 as the GABAergic proximal medulla family
(Erclik et al., 2017). The label appears to be a post-hoc GEO/curator guess
based on partial marker overlap with the Pm family rather than an
author-confirmed cell type.

## Markers

- Gad1, VGAT, Lim3 - consistent with GABAergic/Pm-family identity (Lim3 is the
  authors' pan-Pm marker).
- D (Dichaete) and Sox21b/SoxN also prominent. The paper separately notes that
  large, otherwise-unannotated central clusters at the centre of its t-SNE
  were distinguished only by the transcription factors D and disco, describing
  these as possibly "generic" neurons specialised by neurotransmitter rather
  than deeper identity - the presence of D here raises the possibility that
  this cluster is one such generic/residual GABAergic group rather than a
  clean fourth Pm type.
- Other top markers: Nos, Cngl, sNPF, Pde1c, Pvf3, Nckx30C.

## Location

- Optic lobe medulla is likely (by Lim3/Gad1 co-expression with other Pm
  clusters) but not established by the authors for this cluster.

## Function

- Unclear; if genuinely a Pm-family neuron, presumed GABAergic local
  interneuron function as for Pm1-3.

## Label provenance

Table S2 res-2.0 cluster 55: Unannotated, no method, no references -
`label_validation.tsv` flags this as "named in GEO; S2 res-2.0 Unannotated -
REVIEW". There is no Table S2 or Table S3 support tying this cluster
specifically to a "Pm4" identity beyond the shared Lim3/Gad1/VGAT signature
also seen in the confirmed Pm1/Pm2 and Pm3 clusters.

## Mapping notes

Low-confidence, possibly a remainder/generic GABAergic optic-lobe cluster
rather than a distinct established type. If a "Pm4" cell type exists in the
literature, this cluster's marker evidence is not strong enough on its own to
confirm it; mapping should treat this as REVIEW-level uncertain support,
possibly better characterised as an unresolved GABAergic medulla group than as
a specific fourth Pm subtype.
