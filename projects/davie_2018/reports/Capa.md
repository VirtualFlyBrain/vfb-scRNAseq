# Capa

*Cluster `Capa` (Seurat res-2.0 cluster 44, "Unannotated" at res-2.0, but also
independently annotated as a "Capa" cluster at res-8.0 (cluster 119); 73
cells; ages 0-50 days) in Davie et al. 2018 (GSE107451, 57K adult brain). Also
recovered by the paper's 1,269-cell neuropeptide re-clustering (Figure 2K).*

## Summary

Capa (Capability/periviscerokinin/pyrokinin family) neuropeptide-expressing
neurons: a small, well-characterised Drosophila neurosecretory population
(described in the wider neuropeptide literature, e.g. Kean et al., 2002;
Predel and Wegener) classically comprising a few pairs of neurons in the
abdominal ganglion (the "Va" neurons) plus additional neurosecretory cells in
the brain/subesophageal region. In this atlas the population is recovered
independently at both res-2.0/neuropeptide-subclustering and res-8.0 levels
(res-8.0 cluster 119, per the accompanying supp_evidence relations), giving
reasonable confidence that a coherent Capa+ population is being captured,
though the paper does not give a specific literature reference for its own
Capa annotation.

## Markers

Top res-2.0 cluster-44 markers: Ms (Myosuppressin), Capa, dve, CG4577, bru3,
7B2, amon, Ptx1, fru, IA-2, Sytbeta, mbl, Phm, CR31451, Pdi, beat-VII. Beyond
the defining Capa marker, several markers are general neurosecretory/
peptide-processing genes (7B2, amon [amontillado, PC2 protease], Phm
[peptidylglycine alpha-hydroxylating monooxygenase], IA-2, Pdi), consistent
with a neurosecretory cell identity. Co-expression of Ms (Myosuppressin) and
the transcription factors dve and Ptx1 (both reported markers of
neurosecretory/abdominal ganglion neuron populations) is notable but not
further interpreted by the paper.

## Location

Consistent with the wider literature's Capa+ neurons: abdominal ganglion
(ventral nerve cord) neurosecretory neurons (Va neurons) and/or brain
neurosecretory cells; not independently localised within this atlas (which
profiles whole brains, so any VNC-restricted Capa neurons would not be
represented - see Mapping notes).

## Function

Neurosecretion via Capa/periviscerokinin-family neuropeptide signalling,
implicated in the wider literature in diuresis and stress responses; specific
role not detailed in this paper.

## Label provenance

Table S2 res-2.0 cluster 44 = "Unannotated" (no method/references at
res-2.0), but Table S2 records a related res-8.0 annotation (cluster 119 =
"Capa"). `label_validation.tsv`: status "S2 neuropeptide re-clustering (cells
from multiple res-2.0 clusters)" - the GEO `Capa` label derives from the
Figure 2K neuropeptide subclustering; the independent res-8.0 "Capa" cluster
supports this as a real, reproducibly separable population rather than a
one-off artefact.

## Mapping notes

Likely corresponds to a genuine, specific neuron type (Capa-expressing
neurosecretory cells), moderate-to-high confidence given the specific marker
(Capa) and reproducible recovery across two clustering resolutions. Caveat:
because the dataset is whole adult BRAIN only (VNC not included), if the
classic Capa/Va neurons described in the literature are primarily VNC
(abdominal ganglion) neurons, this cluster more likely represents a
brain-resident Capa+ neurosecretory population rather than the VNC Va
neurons themselves - flag this brain-vs-VNC distinction for the mapping step.
