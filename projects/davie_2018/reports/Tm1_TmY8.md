# Tm1/TmY8

*Cluster `Tm1/TmY8` (Seurat res-2.0 cluster 45; 325 cells; ages 0-50 days) in
Davie et al. 2018 (GSE107451, 57K adult brain). Author-merged label for two
distinct transmedullary neuron types.*

## Summary

Tm1/TmY8 is one of several "newly annotated" optic-lobe clusters the authors
identified by regression-mapping against the Konstantinides et al. (2018)
optic-lobe scRNA-seq/connectome atlas, rather than by literature marker
genes. Tm1 and TmY8 are transcriptionally inseparable at this clustering
resolution and are reported as one merged cluster by both Table S2 and GEO.

## Markers

Table S2 annotation "Tm1/TmY8" (method: mapping; ref Konstantinides et al.,
2018). Top Table S3 markers for res-2.0 cluster 45: Pka-C3, CG2016, Tk,
CG14340, ckn, CG42458, Drgx, ST6Gal, CG3257, GABA-B-R1, Con, Pde1c, beat-IIa,
Mmp2, kek3, Octbeta1R. No marker set is offered that separates Tm1 from
TmY8.

## Location

Tm1 is a transmedullary neuron with dendrites in the medulla (receiving L2
input) and axon terminal in lobula layer 1, part of the OFF motion pathway.
TmY8 is a transmedullary-Y neuron with processes in both the medulla and
lobula; it is less thoroughly characterized in the classical literature than
Tm1.

## Function

Tm1 is a core OFF-pathway element downstream of lamina neuron L2, feeding
into the T5 direction-selective circuit. TmY8's specific functional role is
not established in the sources used here.

## Label provenance

Table S2 and GEO agree: both give res-2.0 cluster 45 the merged label
"Tm1/TmY8" (label_validation.tsv: "match"). No REVIEW flag, but the merge
itself is intrinsic to the data, not a curation artifact — the authors state
this cluster was newly annotated only by cross-dataset mapping, with no
marker-based confirmation.

## Mapping notes

Genuine merged group of two anatomically distinct types (Tm1, a well-defined
OFF-pathway transmedullary neuron, and TmY8, a separate transmedullary-Y
type). Because no markers in this dataset distinguish them, the honest FBbt
level is a common parent covering both, not either type individually.
