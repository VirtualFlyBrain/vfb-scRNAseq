# DCN

*Cluster `DCN` (Seurat res-2.0 cluster 13, refined at res-8.0 cluster 118;
98 cells; ages 0-50 days) in Davie et al. 2018 (GSE107451, 57K adult brain).
Dorsal cluster neurons, directly discussed and cell-count-validated in the
main text.*

## Summary

Dorsal cluster neurons (DCNs) are a well-established, small (~40 per
hemisphere, ~80 per brain) group of neurons expressing atonal (ato) and acj6,
first characterised by Hassan et al. (2000); ~80 DCNs are expected per brain
(Srahna et al., 2006) and the authors detect 98, calling this a good match.
The authors state DCNs are one of the few known cell types that could not be
resolved at res-2.0 and only separate into their own cluster at res-8.0 (S2
cluster 118); res-2.0 cluster 13 is mostly (94/98) these cells, with 4 cells
falling in a neighbouring res-2.0 cluster (9).

## Markers

- acj6 - matches the paper's stated DCN marker (Hassan et al., 2000); note
  ato itself is not in the top-20 Table S3 list, but acj6 is.
- VAChT, nAChRalpha5/7 - cholinergic markers.
- Other top markers (fkh, bi, salr, toy, futsch, beat-IIIc, etc.) are for the
  parent res-2.0 cluster 13, not a DCN-only marker set - see Label
  provenance.

## Location

- Cell bodies dorsal-posterior in the brain, near the mushroom body calyx;
  axons cross the midline via the posterior commissure and project to the
  contralateral lobula/lobula plate (Hassan et al., 2000; Srahna et al.,
  2006).

## Function

- Studied chiefly for stochastic, Notch-dependent left-right axon-guidance
  asymmetry (Hassan et al., 2000; Srahna et al., 2006). In connectome-based
  visual-projection-neuron nomenclature these cells have been identified with
  the lobula columnar type LC14 (Wu et al., 2016) - noted here as a literature
  cross-reference for the mapping step to check, not independently verified
  against this dataset.

## Label provenance

Table S2 res-2.0 cluster 13 itself is Unannotated; DCN identity is only
established at res-8.0 (S2 cluster 118, annotation "DCN", method: literature
markers, ref Hassan et al., 2000). `label_validation.tsv` records this as
"named in GEO; S2 res-2.0 Unannotated (S2 res-8.0/subcluster: DCN)" - not a
REVIEW flag, since the res-8.0 refinement directly supports the GEO label; it
is simply a finer-resolution annotation than the default res-2.0 table.
`res2_ambiguous` shows 94/98 GEO-labelled cells fall in res-2.0 cluster 13 and
4 in cluster 9, i.e. the res-2.0 clustering does not cleanly separate DCNs
from a neighbouring group, and the Table S3 marker list given is for the
broader parent res-2.0 cluster 13, not DCNs specifically.

## Mapping notes

Strong single-type match: DCN is a specific, established, author-confirmed
cell type (via res-8.0 refinement, explicit expected-vs-observed cell-count
check, and a named marker/reference). Expect an existing FBbt term for dorsal
cluster neuron; if the DCN/LC14 identity above is correct and already
reflected in FBbt, note that possible synonymy for the mapping step to
confirm.
