# Dopaminergic

*Cluster `Dopaminergic` (Seurat res-2.0 cluster 42; 125 cells; ages 0-50 days)
in Davie et al. 2018 (GSE107451, 57K adult brain). The Fer2-negative
remainder of the parent dopaminergic cluster, after the PAM subcluster was
split out.*

## Summary

Res-2.0 cluster 42 was annotated "Dopaminergic" from literature markers and
subsequently subclustered using the transcription factor Fer2 into two
groups: Fer2(+) = PAM (protocerebral anterior-medial) dopaminergic neurons
(reported separately as the `PAM` cluster/GEO label), and Fer2(-) = the
remaining dopaminergic neurons. The GEO label `Dopaminergic` (125 cells) is
this Fer2(-) remainder. The paper states dopaminergic neurons form eight
known clusters in the adult central brain (PAM, PPL1, PPL2ab, PPM1/2, PPM3,
PAL, etc.); only the PAM cluster was resolved by Fer2, so `Dopaminergic` here
is an unresolved mixture of the other ~7 non-PAM dopaminergic neuron groups.

## Markers

Top res-2.0 cluster 42 markers (shared with PAM, pre-split): DAT (dopamine
transporter), ple (tyrosine hydroxylase), Vmat, Fer2, JhI-21, Ddc, DIP-delta,
Dhpr, Dop2R, hth, Lim1 - a canonical dopaminergic signature; Fer2 itself
marks only the PAM sub-fraction, not this Fer2(-) remainder.

## Location

Central brain; the non-PAM dopaminergic clusters (PPL1, PPL2ab, PPM1/2, PPM3,
PAL) innervate the mushroom body lobes/peduncle, central complex, and other
protocerebral targets from somata in the posterior lateral/medial and
anterior lateral protocerebrum.

## Function

Dopaminergic neuromodulation; the non-PAM clusters include mushroom-body
punishment/aversive-learning DANs (PPL1) and neurons implicated in arousal,
locomotion and other central-brain circuits.

## Label provenance

Table S2 res-2.0 annotation for cluster 42 is "Dopaminergic" (match). The
S2-related subcluster rows record the Fer2-based split into "PAM (Fer2(+))
neurons" (Bou Dib et al., 2014) and "Fer2(-) neurons" (no reference given).
No REVIEW flag.

## Mapping notes

This is a remainder/unresolved group: several distinct dopaminergic neuron
clusters (PPL1, PPL2ab, PPM1/2, PPM3, PAL) are merged here with no further
transcriptomic separation. A single specific FBbt term is not appropriate;
the honest level is a parent term such as "dopaminergic neuron" (or "central
brain dopaminergic neuron, PAM excluded"), flagged as covering multiple
named anatomical DAN clusters.
