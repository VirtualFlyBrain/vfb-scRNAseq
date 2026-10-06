# Astrocyte-like

*Cluster `Astrocyte-like` (Seurat res-2.0 cluster 10; 1,421 cells; ages 0-50
days) in Davie et al. 2018 (GSE107451, 57K adult brain). Astrocyte-like glia
of the adult brain, identified by canonical astrocyte markers.*

## Summary

Astrocyte-like glia are the main "processes-bearing" astrocytic glial cell
type of the adult Drosophila CNS, morphologically and molecularly analogous
to vertebrate astrocytes. The paper identifies this cluster among the glial
subtypes directly by the marker alrm, following the astrocyte definition of
Doherty et al. (2009) and the transcriptomic mapping approach of
Konstantinides et al. (2018). Astrocyte-like glia infiltrate neuropil and
support synaptic function, distinct from surface (perineurial/subperineurial)
and cortex glia, which occupy different anatomical compartments.

## Markers

- alrm (astrocyte leucine-rich repeat molecule) — the defining marker used by
  the paper to call this cluster (Doherty et al., 2009).
- Table S3 top markers for res-2.0 cluster 10 include CG9394, Gat, CG31705,
  Gs2, alrm, CG1552, CG13631, Eaat1, ogre — Gat and Eaat1 (GABA and glutamate
  transporters) are consistent with an astrocyte-like role in neurotransmitter
  clearance from the synaptic neuropil.

## Location

- **Neuropil:** infiltrates neuropil throughout the brain (both central brain
  and optic lobe); the whole-brain dataset does not distinguish
  region-specific astrocyte subpopulations for this cluster, and the paper
  does not report separating central-brain from optic-lobe astrocyte-like
  glia at this resolution.
- **Cell class:** astrocyte-like glia (non-neuronal), class G.

## Function

- Neuropil-associated glia thought to support synaptic homeostasis and
  neurotransmitter clearance (Gat, Eaat1 expression), by analogy with
  vertebrate astrocytes (Doherty et al., 2009).

## Label provenance

Table S2 res-2.0 cluster 10 is annotated "Astrocyte-like" by literature
markers/mapping (Doherty et al., 2009; Konstantinides et al., 2018); the GEO
label matches exactly (label_validation.tsv: match). No REVIEW flag.

## Mapping notes

Astrocyte-like glia are an established Drosophila glial subtype (distinct
from cortex, perineurial, subperineurial, ensheathing and chiasm glia); an
FBbt term for "astrocyte-like glial cell" is expected and this cluster should
map to it as a single type. Because the atlas covers the whole brain
including optic lobes and the paper does not report a region-specific split
for this cluster, this is likely a merged, brain-wide pool of astrocyte-like
glia rather than a resolved central-brain-only or optic-lobe-only population;
flag this for the mapping step if FBbt distinguishes region-specific
astrocyte-like glia subtypes.
