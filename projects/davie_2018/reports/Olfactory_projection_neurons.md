# Olfactory_projection_neurons

*Cluster `Olfactory_projection_neurons` (Seurat res-2.0 cluster 27; 71 cells;
ages 0-50 days) in Davie et al. 2018 (GSE107451, 57K adult brain). Cells of
the OPN (olfactory projection neuron) cluster resolved only at the parent
level, not assigned to the adPN or lPN lineage or to any Li et al. 2017
marker subgroup.*

## Summary

Res-2.0 cluster 27 ("OPN: adPN and lPN") contains 543 antennal-lobe olfactory
projection neurons, identified by expression of tup, otp, C15 and hth
(Komiyama and Luo, 2007; Li et al., 2017). The authors subclustered these 543
cells against a SMART-seq2 reference of sorted adPNs/lPNs (Li et al., 2017,
Cell) and recovered all of that study's reported subclusters (Figure 2H).
This GEO label is the residual fraction of the 543 OPN cells that GEO
metadata records only as "Olfactory_projection_neurons" - i.e., not resolved
to adPN, lPN, or any of the five marker-defined subgroups (C15+/kn+/unpg+/
CG31676+ combinations) reported in Table S2.

## Markers

- Table S3 top markers are for the parent res-2.0 cluster 27, not specific to
 this unresolved fraction: otp, ST6Gal, hth, Oaz, CG43729, caup, acj6, mirr,
 C15, Drep3, CR32111, ara, mbl, cpo, tup, tnc, kn, CG7708, ChAT, VAChT.
 ChAT/VAChT indicate a cholinergic phenotype, typical of most PN classes.

## Location

- **Neuropil:** antennal lobe (dendrites in glomeruli) with axons via one of
 the antennal-lobe tracts to the mushroom body calyx and lateral horn.
- **Cell body:** anterior/lateral cell clusters around the antennal lobe.
- **Cell class:** olfactory projection neuron (second-order olfactory
 interneuron), class N.

## Function

- Relay odor information from olfactory receptor neurons in the antennal
 lobe glomeruli to the mushroom body (learned responses) and lateral horn
 (innate responses).

## Label provenance

Table S2 res-2.0 cluster 27 is annotated "OPN: adPN and lPN" (literature
markers/mapping; Komiyama and Luo, 2007; Komiyama et al., 2003; Li et al.,
2017). label_validation.tsv: match (curated synonym of S2 'OPN: adPN and
lPN'). No REVIEW flag. This label sits at the coarsest resolution within
cluster 27 - below it, GEO further splits cells into adPN, lPN, and five
Li-et-al.-matched marker subgroups (see Table S2 subcluster rows).

## Mapping notes

Honest level is the general "olfactory projection neuron" grouping - this
label carries no lineage (adPN vs lPN) or marker information, so it cannot be
mapped below "olfactory projection neuron" as a class. It is a
remainder/unresolved group, not a single type, and should not be forced to a
lineage- or glomerulus-specific term.
