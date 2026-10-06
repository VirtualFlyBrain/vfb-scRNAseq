# adPN/kn&CG31676

*Cluster `adPN/kn&CG31676` (Seurat res-2.0 cluster 27; 11 cells; ages 3-50
days, sparsely sampled) in Davie et al. 2018 (GSE107451, 57K adult brain). A
very small marker-combination subgroup within the OPN cluster, NOT listed in
Table S2.*

## Summary

Within res-2.0 cluster 27 (543 OPN cells, subclustered per Figure 2H against
Li et al. 2017's SMART-seq2 adPN/lPN reference), Table S2 lists five named
marker subgroups: C15(+) adPNs, C15(+) kn(+) adPNs, kn(+) adPNs, unpg(+)
lPNs, and CG31676(+) lPNs. "adPN/kn&CG31676" is not among them. Its label
combines an adPN-lineage marker (kn), normally reported for adPNs, with
CG31676, which Table S2 associates only with lPNs (as "CG31676(+) lPNs").
This is most plausibly a small GEO-metadata subgroup at the boundary/overlap
of the kn(+) adPN and CG31676(+) lPN calls, rather than a discrete cell
population the authors describe - only 11 cells, one of the smallest labels
in the dataset.

## Markers

- Label implies kn-positive and CG31676-positive; this specific combination
 is not discussed in the paper text or Table S2.
- Table S3 top markers are for the parent res-2.0 cluster 27, not specific to
 this subgroup: otp, ST6Gal, hth, Oaz, CG43729, caup, acj6, mirr, C15,
 Drep3, CR32111, ara, mbl, cpo, tup, tnc, kn, CG7708, ChAT, VAChT (CG31676
 is not among the top 20 parent-cluster markers).

## Location

- **Neuropil:** antennal lobe (if adPN- or lPN-lineage, dendrites in one or
 more glomeruli); axons via iACT (adPN) or mACT (lPN) - lineage identity
 itself is ambiguous for this label.
- **Cell class:** olfactory projection neuron, lineage/subtype ambiguous,
 class N.

## Function

- Presumed odor relay to mushroom body and/or lateral horn, consistent with
 other OPN subgroups; no specific function is described for this label.

## Label provenance

Not present in Table S2 (neither at the res-2.0 nor the subcluster level).
label_validation.tsv carries a note "S2 neuropeptide re-clustering (cells
from multiple res-2.0 clusters)" for this row, but that description matches
the method used for the unrelated neuropeptide subclusters (e.g. AstA/Nplp1,
IPC, LNv), not an OPN marker combination - this looks like a stale or
mismatched annotation rather than a genuine statement about this label's
origin, and should be treated as a REVIEW-worthy discrepancy. The most
defensible reading is that this is a small, GEO-specific subdivision of
cluster 27 not reported by the authors, likely artefactual or a boundary
case between the kn(+) adPN and CG31676(+) lPN calls.

## Mapping notes

Given the small cell number (11), the marker combination not matching any
Table S2 subgroup, and the mismatched provenance note, this label should be
treated as unresolved/uncertain rather than mapped to a specific PN identity.
It may represent doublets, transitional/ambiguous cells, or a curation
artifact rather than a genuine cell state or type. Recommend flagging for
human review before any FBbt mapping is attempted; if a mapping is required,
the most honest level is the general "olfactory projection neuron" class.
