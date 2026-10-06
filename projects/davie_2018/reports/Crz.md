# Crz

*Cluster `Crz` (Seurat res-2.0 cluster 37; 9 cells; ages 6, 9 days) in
Davie et al. 2018 (GSE107451, 57K adult brain). A small corazonin-expressing
population from the neuropeptide re-clustering, but with a notable parent-
cluster discrepancy (see below).*

## Summary

Corazonin (Crz) neurons are a classical, well-characterised small
neuropeptidergic population in the Drosophila brain (the "dorsal lateral
peptidergic" neurons; Veenstra, 1989; Choi et al., 2005; Kubrak et al. and
others), implicated in stress response, ethanol sensitivity, metabolism and
lifespan. However, in this atlas the 9 Crz-labelled cells are drawn mostly
(7/9) from res-2.0 cluster 37, whose parent-level Table S2 annotation is
"T1" — an unrelated optic-lobe interneuron type identified by the marker
Eaat1 (Hamanaka and Meinertzhagen, 2010). Eaat1 also appears among this
Crz cluster's own top markers, reinforcing that these 9 cells sit within
the T1 transcriptional neighbourhood rather than a distinct corazonin
signature space.

## Markers

- Crz itself is a top marker (as expected, since it defines the subcluster).
- Eaat1, the diagnostic T1 marker, is also a top marker — an unusual
  co-occurrence given T1 and Crz neurons are anatomically and
  functionally unrelated cell types.

## Location

- Classical Crz neurons: a few pairs of dorsal-lateral protocerebral
  peptidergic neurons. Not independently confirmed here given the T1
  parent-cluster overlap.

## Function

- Corazonin signalling: stress/metabolic modulation (established
  literature); not further addressed for this cluster in the paper text.

## Label provenance

No REVIEW flag in `label_validation.tsv`, but this is a genuine concern:
Table S2's res-2.0 annotation for cluster 37 is "T1" (literature
markers/mapping; Hamanaka and Meinertzhagen, 2010; Konstantinides et al.,
2018), not corazonin/peptidergic. The GEO "Crz" label comes from the
separate S2 neuropeptide re-clustering, but most of its cells originate
from the T1-dominated cluster 37, and share the T1 marker Eaat1.

## Mapping notes

Corazonin neurons are a KNOWN, anatomically defined class (dorsal-lateral
peptidergic neurons), so an existing FBbt term for "corazonin neuron" is
the expected target. But given the small cell number (9), narrow age
range, and overlap with the unrelated T1 optic-lobe cluster and its
marker, this cluster's identity is uncertain — it may represent doublets,
ambient-RNA contamination from T1 cells, or a genuine but very sparse
capture of true Crz neurons. Flag for cautious/low-confidence mapping and
possible exclusion or manual review before committing to a specific FBbt
term.
