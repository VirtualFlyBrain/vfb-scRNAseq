# Tm9

*Cluster `Tm9` (Seurat res-2.0 cluster 63; 229 cells; ages 0-50 days) in
Davie et al. 2018 (GSE107451, 57K adult brain). GEO label provenance is
disputed: Table S2 itself names a DIFFERENT cluster "Tm9".*

## Summary

Tm9 in GEO refers to res-2.0 cluster 63, which Table S2 lists as
"Unannotated" (no method, no references). Confusingly, Table S2's own
res-2.0 table separately annotates a *different* cluster, 18, as "Tm9" — but
GEO leaves cluster 18 numbered/unlabelled and instead applies the name "Tm9"
to cluster 63. This is a genuine label-assignment discrepancy, not a minor
wording difference.

## Markers

Top Table S3 markers for res-2.0 cluster 63 (GEO's "Tm9"): mspo, CR45621,
CG42394, CG32982, eys, Rbp6, mbl, kirre, dpr17, Wnt10, vvl, Pvf3, scro, Ktl,
ChAT, Octbeta3R, Octbeta2R. Note ChAT (cholinergic) is present, consistent
with Tm9 being a cholinergic OFF-pathway neuron, but no evidence here ties
these specific markers to the authors' own cluster-18 "Tm9" call — cluster
18's own Table S3 markers were not retrieved as part of this cluster's
evidence set.

## Location

Classically, Tm9 is a transmedullary neuron with dendrites in the medulla
receiving lamina neuron L3 input and axon terminating in lobula layer 4,
part of the OFF motion pathway alongside Tm1, Tm2, and Tm4.

## Function

Tm9 provides L3-derived, contrast-related input to the T5 OFF
direction-selective circuit (Shinomiya et al., 2014; Behnia et al., 2014).

## Label provenance

REVIEW (significant): label_validation.tsv shows two separate rows relevant
to "Tm9" — this cluster (GEO label "Tm9", res-2.0 cluster 63, S2
"Unannotated"), and a distinct row "(18) — 18 — Tm9 — S2-named cluster left
numbered in GEO — REVIEW", i.e. Table S2 itself calls res-2.0 cluster 18
"Tm9", but GEO's metadata leaves cluster 18 as a bare number and instead
names cluster 63 "Tm9". The GEO "Tm9" label used for this cluster therefore
has no direct Table S2 support and may reflect a curation
swap/mix-up rather than the authors' intended Tm9 assignment.

## Mapping notes

Treat this cluster's identity as unconfirmed. Before mapping to FBbt Tm9,
the discrepancy with Table S2's cluster 18 (the author-intended "Tm9")
should be resolved or explicitly caveated; do not commit to an exact FBbt
Tm9 match without flagging this provenance issue to the curator.
