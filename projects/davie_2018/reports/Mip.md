# Mip

*Cluster `Mip` (Seurat res-2.0 cluster 17; 814 cells; ages 0-50 days) in Davie
et al. 2018 (GSE107451, 57K adult brain). Identified directly by literature
markers for the neuropeptide gene Mip (myoinhibitory peptide), not via the
paper's separate 1,269-cell neuropeptide re-clustering.*

## Summary

A cluster of Mip (myoinhibitory peptide / prothoracicostatic-peptide family)
neuropeptide-expressing neurons, annotated by the authors using literature
markers with reference to Carlsson et al. (2010) and Min et al. (2016), who
mapped Mip-expressing neurons in the Drosophila brain. Mip is expressed by a
distributed, multi-part set of neurosecretory and local neurons rather than a
single morphological type, and this cluster (814 cells) is large relative to
the small numbers of Mip+ cells reported by immunohistochemistry, suggesting
it captures Mip+ neurons together with closely related, transcriptionally
similar cells.

## Markers

Top res-2.0 cluster-17 markers include Optix, Lim1, NPF, Ets65A, Mip, Rx,
robo2, Ten-a, IA-2, Rim. The presence of Optix, Rx and Lim1 (visual-system/eye
patterning transcription factors) alongside Mip and NPF suggests this
population is concentrated in or near the optic lobe.

## Location

Not pinned down beyond the marker inference above; consistent with optic-lobe
and/or central-brain Mip-immunoreactive neurons described in the cited
literature (Carlsson et al., 2010; Min et al., 2016).

## Function

Neuromodulation via myoinhibitory peptide signalling (implicated in feeding,
sleep, and ecdysis-related processes in the broader literature); specific
adult-brain function of this population not detailed in the paper.

## Label provenance

Table S2 res-2.0 cluster 17 = "Mip", method "literature markers", references
(Carlsson et al., 2010; Min et al., 2016). `label_validation.tsv`: status
"match" (no discrepancy). Unlike Mip/ITP, ITP, IPC, AstA/Nplp1, AstA/NPF and
Capa, this label comes from the primary res-2.0 clustering, not from the
paper's 1,269-cell neuropeptide subclustering (Figure 2K) - it is the parent
population that some of those finer subclusters (Mip/ITP, AstA/NPF) partly
draw from.

## Mapping notes

Likely a merged group rather than one anatomical type: markers point to a
mixed optic-lobe/Mip-expressing population, and cell number (814) is large
compared to typical counts of individually characterized Mip+ neuron types.
Expect at best a mapping to a broad "Mip-expressing neuron" grouping, not a
single named FBbt cell type, unless the underlying literature resolves
discrete Mip+ subtypes at this location.
