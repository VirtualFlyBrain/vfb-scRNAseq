# AstA/Nplp1

*Cluster `AstA/Nplp1` (Seurat res-2.0 cluster 73, annotated "Pm3"; 83 cells;
ages 0-50 days) in Davie et al. 2018 (GSE107451, 57K adult brain). A
neuropeptide co-expression subcluster (Allatostatin A + Nplp1) from the
paper's 1,269-cell neuropeptide re-clustering (Figure 2K).*

## Summary

Cells co-expressing the neuropeptide genes AstA (Allatostatin A) and Nplp1,
recovered by the neuropeptide-focused subclustering. Of the 83 cells in this
label, 72 map back to res-2.0 cluster 73, which the primary clustering
annotated as "Pm3" - the GABAergic proximal medulla (Pm) interneuron subtype
of the optic lobe, identified via literature markers/mapping to Erclik et al.
(2017) and Konstantinides et al. (2018). Erclik et al. (2017) characterise Pm
neurons as peptidergic GABAergic optic-lobe interneurons, and Vsx2 (listed
among this cluster's markers) is reported there as specific to Pm3 among the
three Pm subtypes (Pm1-3). This strong overlap indicates AstA/Nplp1 largely
represents the neuropeptide-expressing signature of the Pm3 population, not
an unrelated cell group.

## Markers

Top res-2.0 cluster-73 markers: AstA, CG32017, CG10257, nAChRalpha6,
CR45312, heph, mAChR-B, IA-2, mAChR-A, Lmx1a, Dat, hbn, fend, Nplp1, Vsx2,
twz. AstA and Nplp1 are the co-expression markers defining this subcluster;
Vsx2 supports the Pm3 identity of the parent cluster.

## Location

Optic lobe, proximal medulla (Pm neuron layer), per the Pm3 identity of the
parent res-2.0 cluster.

## Function

GABAergic inhibitory interneuron of the medulla, additionally peptidergic
(AstA/Nplp1 co-release); specific circuit role of the neuropeptide
co-expression not detailed by the paper.

## Label provenance

Table S2 res-2.0 cluster 73 = "Pm3", method "literature markers/mapping",
references (Erclik et al., 2017; Konstantinides et al., 2018).
`label_validation.tsv`: status "S2 neuropeptide re-clustering (cells from
multiple res-2.0 clusters)" - the GEO `AstA/Nplp1` label itself comes from the
Figure 2K subclustering, but its strong (72/83) correspondence to the
independently annotated Pm3 cluster indicates it is not a spurious mixture -
it likely captures the peptidergic-marker-positive fraction of Pm3.

## Mapping notes

Probably corresponds to a genuine, previously characterised optic-lobe
interneuron subtype (Pm3), rather than being purely a co-expression artefact -
moderate-to-high confidence given the marker (Vsx2) and majority res-2.0
cluster overlap. However, because the label is defined by neuropeptide
co-expression within a subset of Pm3 cells (not all Pm3 cells), it may
represent a peptide-expressing state or substate of Pm3 rather than the full
Pm3 population; mapping should note this distinction rather than assuming
AstA/Nplp1 == all of Pm3.
