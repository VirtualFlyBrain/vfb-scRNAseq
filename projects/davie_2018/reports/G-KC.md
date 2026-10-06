# G-KC

*Cluster `G-KC` (Seurat res-2.0 cluster 8; 1,642 cells; ages 0-50 days) in
Davie et al. 2018 (GSE107451, 57K adult brain). Gamma-lobe Kenyon cells of the
mushroom body.*

## Summary

Gamma Kenyon cells (γ-KCs) are the intrinsic neurons of the mushroom body
gamma lobe, one of the three principal Kenyon cell classes (γ, α/β, α'/β')
that together form the mushroom body's parallel-fibre association-memory
circuitry. The paper identifies this cluster among the KCs (marked overall by
ey and prt) by its co-expression of sNPF and trio, distinguishing it from the
α/β (sNPF only) and α'/β' (trio only) clusters.

## Markers

- sNPF and trio co-expression (paper's discriminating marker logic for γ vs
  α/β vs α'/β' KCs).
- Table S3 top markers for res-2.0 cluster 8 include Pka-R2, sNPF, prt, Rgk1,
  GstD11, Pka-C1, mub, Imp, mamo, Pka-C3, rut, Bx — consistent with a
  cAMP/PKA-signalling-rich, learning-and-memory neuron (rut/Pka pathway genes
  are canonical KC/mushroom-body memory genes).
- The authors attempted to subcluster the KC lobes further but found cells
  separated mainly by technical covariates (age, sex) rather than genuine
  subtypes, so no finer γ-KC subtype resolution is available from this atlas.

## Location

- **Neuropil:** mushroom body, gamma lobe (vertical + medial lobe branch of
  the gamma-lobe Kenyon cells).
- **Cell body:** Kenyon cell body cluster, dorsal posterior cortex (calyx
  region).
- **Cell class:** intrinsic mushroom body neuron (Kenyon cell), class N.

## Function

- Intrinsic mushroom body neuron; gamma-lobe KCs contribute to short-term and
  some longer-term olfactory associative memory, with lobe-specific roles
  distinct from α/β and α'/β' KCs in the classical memory-consolidation model
  of the fly mushroom body.

## Label provenance

Table S2 res-2.0 cluster 8 is annotated "G-KC" by literature markers/mapping
(Awasaki et al., 2000; Crocker et al., 2016; Johard et al., 2008); the GEO
label matches exactly (label_validation.tsv: match). No REVIEW flag.

## Mapping notes

Gamma Kenyon cells are an established, morphologically and functionally
distinct KC subclass; an adult-specific FBbt term for "gamma Kenyon cell"
should exist and this cluster is expected to map to it as a single type at
that granularity (not further split into the gamma-main/gamma-d subtypes
described by later connectomic work, since the atlas could not resolve
subtypes within the lobe).
