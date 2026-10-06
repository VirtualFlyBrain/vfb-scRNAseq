# Chiasm_glia

*Cluster `Chiasm_glia` (Seurat res-2.0 cluster 82; 86 cells; ages 0-50 days)
in Davie et al. 2018 (GSE107451, 57K adult brain). Glia associated with the
optic chiasmata of the optic lobe.*

## Summary

Chiasm glia are a glial population associated with the optic chiasmata
(the crossing fibre tracts connecting the lamina, medulla, and lobula
complex neuropils of the optic lobe), an optic-lobe-specific glial identity
distinct from the ensheathing, astrocyte-like, cortex, and surface glia found
throughout the brain. The paper lists "chiasm glia" among clusters newly
annotated in this study by transcriptomic mapping to markers from
Konstantinides et al. (2018), grouped in the text alongside other newly
annotated optic-lobe cell types (L1-5, T2/T3, T4/T5, TmY14, etc.), indicating
this is an optic-lobe glial cluster rather than a central-brain one — a
population identifiable because the atlas covers whole brains including the
optic lobes.

## Markers

- Table S3 top markers for res-2.0 cluster 82 include CG15201, Obp44a, wkd,
  euc, alrm, fabp, Irk3, NimB4, Tsf1 — the presence of alrm alongside
  Obp44a/fabp suggests some transcriptional overlap with astrocyte-like glia,
  though the cluster is distinctly and separately annotated.

## Location

- **Neuropil:** optic lobe, at the outer and/or inner optic chiasma (crossing
  fibre tracts between lamina-medulla and medulla-lobula complex).
- **Cell class:** chiasm glia (non-neuronal), optic-lobe-specific, class G.

## Function

- Ensheathes/organizes the crossing axon tracts of the optic chiasmata; exact
  functional role not detailed in the paper beyond marker-based annotation
  (Konstantinides et al., 2018).

## Label provenance

Table S2 res-2.0 cluster 82 is annotated "Chiasm Glia" by mapping
(Konstantinides et al., 2018); the GEO label matches exactly
(label_validation.tsv: match). No REVIEW flag.

## Mapping notes

Chiasm glia are a distinct, optic-lobe-specific Drosophila glial population;
an FBbt term for "chiasm glial cell" (or specifically for outer/inner
chiasm glia, if FBbt distinguishes them) should be sought. This is a small
cluster (86 cells) newly annotated by marker mapping rather than direct
literature markers, so confidence in its precise identity is somewhat lower
than for the literature-marker-based glial clusters (astrocyte-like, cortex,
perineurial, subperineurial); it likely represents a single type at the
"chiasm glia" level, but the paper does not distinguish outer vs. inner
chiasm glia, so if FBbt requires that split this cluster should be treated as
the honest, less granular parent level.
