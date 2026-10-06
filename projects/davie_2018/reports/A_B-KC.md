# A/B-KC

*Cluster `A/B-KC` (Seurat res-2.0 cluster 22; 688 cells; ages 0-50 days) in
Davie et al. 2018 (GSE107451, 57K adult brain). Alpha/beta-lobe Kenyon cells
of the mushroom body.*

## Summary

Alpha/beta Kenyon cells (α/β-KCs) are the intrinsic neurons of the mushroom
body alpha/beta lobes, one of the three principal KC classes. The paper
identifies this cluster among the KCs (marked overall by ey and prt) by sNPF
expression without trio, distinguishing it from γ-KCs (sNPF + trio) and
α'/β'-KCs (trio only).

## Markers

- sNPF-positive, trio-negative (paper's discriminating logic for α/β vs the
  other two KC classes).
- Table S3 top markers for res-2.0 cluster 22 include Pka-R2, Eip93F, crb,
  mub, Rgk1, Pka-C1, Mef2, Dop1R2, Nep1, 5-HT1A, sNPF, Pkc53E, Appl —
  again a PKA/cAMP-signalling-dominated profile typical of KCs, plus
  serotonin-receptor (5-HT1A) and dopamine-receptor (Dop1R2) expression
  consistent with known KC neuromodulation.
- As with the other KC lobes, further subclustering by the authors separated
  cells mainly on technical covariates (age, sex), so no finer α/β subtype
  (e.g. αβ-core/surface/posterior distinctions from other studies) is
  resolved here.

## Location

- **Neuropil:** mushroom body, alpha and beta lobes.
- **Cell body:** Kenyon cell body cluster, dorsal posterior cortex (calyx
  region).
- **Cell class:** intrinsic mushroom body neuron (Kenyon cell), class N.

## Function

- Intrinsic mushroom body neuron; α/β-KCs are required for long-term memory
  consolidation and retrieval in the classical model of fly olfactory
  associative learning, distinct in temporal/behavioural role from γ and
  α'/β' KCs.

## Label provenance

Table S2 res-2.0 cluster 22 is annotated "a/b-KC" by literature
markers/mapping (Crocker et al., 2016; Johard et al., 2008); the GEO label
"A/B-KC" matches this exactly modulo case (label_validation.tsv: match). No
REVIEW flag.

## Mapping notes

Alpha/beta Kenyon cells are an established, morphologically and functionally
distinct KC subclass; an adult-specific FBbt term for "alpha/beta Kenyon
cell" should exist and this cluster is expected to map to it as a single type
at that granularity, without resolution of the further αβ subtypes
(core/surface/posterior) known from other (non-transcriptomic-resolvable in
this dataset) work.
