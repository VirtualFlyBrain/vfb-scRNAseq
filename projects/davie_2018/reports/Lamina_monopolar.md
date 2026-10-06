# Lamina_monopolar

*Cluster `Lamina_monopolar` (Seurat res-2.0 cluster 20; 307 cells; ages 0-50
days) in Davie et al. 2018 (GSE107451, 57K adult brain). The remainder of the
merged L1/L2/L3/L4/L5 res-2.0 cluster left over after subclustering; not
resolved to an individual lamina monopolar subtype.*

## Summary

Res-2.0 cluster 20 (391 cells total) was annotated "L1/L2/L3/L4/L5" by
regression-model mapping to Tan et al. (2015) bulk transcriptomes and then
subclustered by the authors (Figure 2E-F), yielding subclusters callable as
L1 (VGlut), L4/L5 (bsh), L2 and L3 (regression-model matches). The GEO
"Lamina_monopolar" label is the part of cluster 20 (307 of 391 cells, i.e.
the majority) that this subclustering did not resolve to any specific L1-L5
subtype — a residual, mixed-identity lamina monopolar pool.

## Markers

- No subtype-specific marker; this is the unresolved remainder of the
  cluster after L1, L2, L3 and L4/L5 subclusters were separated out.
- Table S3 top markers for res-2.0 cluster 20 (CG18598, CG11000, Rbp6,
  shakB, Teh2, CG14509, CG42392, CG10947, CG9813, scro, CG31345, glob1, slp1,
  pdm3, AstA-R1, cpx, CG32647, slp2, para, CR45621) describe the pooled
  L1-L5 population as a whole, including this remainder; they do not
  distinguish it from the resolved subtypes.

## Location

- **Cell class:** lamina monopolar columnar interneurons (class N),
  identity spanning some mix of L1-L5.
- **Soma/dendrites:** lamina cortex and cartridges; **axons:** project to the
  medulla (specific layer/target varies by the underlying, unresolved
  subtype).

## Function

- Downstream relay of outer photoreceptor (R1-R6) histaminergic input from
  the lamina cartridge to the medulla; specific pathway role (ON/OFF/
  lateral/feedback) cannot be assigned without subtype resolution.

## Label provenance

Table S2 res-2.0 cluster 20 is annotated "L1/L2/L3/L4/L5" (method: mapping,
ref: Tan et al., 2015). label_validation.tsv records the GEO
"Lamina_monopolar" label as a curated synonym of this S2 annotation, matching
at the res-2.0 (unresolved, pooled) level — it is not itself one of the
subclustered L1/L2/L3/L4/L5 labels, but the cells left unassigned by that
subclustering. No REVIEW flag.

## Mapping notes

This cluster is a remainder/unresolved group, not a single cell type: it is
the pooled lamina-monopolar population minus the cells confidently assigned
to L1, L2, L3 or L4/L5. The honest mapping level is a parent grouping term
such as "lamina monopolar neuron" (covering L1-L5 collectively), not any
individual subtype — assigning it to one specific L-neuron FBbt term would
overstate the evidence. Flag for the mapping step that this is best treated
as an "unresolved/mixed" bucket rather than a distinct biological cell type.
