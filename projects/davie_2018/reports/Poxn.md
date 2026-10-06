# Poxn

*Cluster `Poxn` (Seurat res-2.0 cluster 80; 99 cells; ages 0-50 days) in Davie
et al. 2018 (GSE107451, 57K adult brain). Poxn-expressing cells; likely only
part of the ~350 Poxn+ cells the text describes across two anatomical groups.*

## Summary

The paper states: "Other groups of neurons that are identified are ~350
Poxn-expressing cells of the protocerebral dorsal cluster and the neurons of
the deutocerebral ventral cluster (Boll and Noll, 2002; Minocha et al.,
2017)." Poxn (Pox neuro) is a well-established homeodomain transcription
factor marking specific poly-innervating/mechanosensory-associated interneuron
populations in these two distinct brain regions. This transcriptomic cluster
contains only 99 cells, well under the ~350 the text quotes, so it likely
captures only a subset (one of the two anatomical groups, or the more
transcriptomically distinct portion of both) rather than the full Poxn+
population described.

## Markers

- Poxn - the defining transcription factor itself is in the top markers,
  directly supporting the label.
- Dat (dopaminergic) and Gad1/Rdl (GABAergic) both present among top markers -
  a heterogeneous neurotransmitter signature consistent with this cluster
  spanning more than one anatomically distinct Poxn+ population.
- Other top markers: CG14687, Mcm5, Nep1, Dh31, Tomosyn, HLH3B, Lim1, Dr.

## Location

- Two anatomically distinct groups are described: the protocerebral dorsal
  cluster and the deutocerebral ventral cluster (Boll and Noll, 2002; Minocha
  et al., 2017). Which of these (or what mixture) this specific 99-cell
  transcriptomic cluster represents is not distinguished in the atlas
  metadata.

## Function

- Poxn+ neurons in these clusters have been studied mainly in the context of
  gustatory/mechanosensory processing and brain patterning (Boll and Noll,
  2002; Minocha et al., 2017); no cluster-specific function is stated by Davie
  et al. 2018 beyond the marker-based identification.

## Label provenance

Table S2 res-2.0 cluster 80 is annotated "Poxn" (method: literature markers;
refs Boll and Noll, 2002; Minocha et al., 2017) - GEO label matches S2
exactly, no REVIEW flag. Note, however, the cell-count discrepancy versus the
main text's "~350 Poxn-expressing cells" figure (this cluster = 99 cells),
which was not itself flagged in `label_validation.tsv` but is worth surfacing
for mapping.

## Mapping notes

Likely a merged group (protocerebral dorsal cluster + deutocerebral ventral
cluster Poxn+ neurons) rather than a single cell type, given the text
explicitly names two separate anatomical populations under this marker and
the cell count here is much smaller than the combined ~350 described - a
common parent (e.g. "Poxn-expressing neuron") is the safer mapping level
unless further evidence resolves which population(s) this cluster contains.
