# Hug

*Cluster `Hug` (Seurat res-2.0 cluster 46; 42 cells; ages 0, 1, 3, 6, 9, 15,
30, 50 days) in Davie et al. 2018 (GSE107451, 57K adult brain). The hugin
(gustatory) neuropeptide neurons of the subesophageal zone.*

## Summary

Hugin (Hug) neurons are a well-established, anatomically defined
neuropeptidergic population of the subesophageal zone (SEZ), comprising
several morphologically distinct subtypes (hugin-PC, hugin-VNC, hugin-RG;
Melcher and Pankratz, 2005; Schoofs et al., 2014) with roles in feeding
suppression and gustatory-to-motor circuit relay. The paper's own main text
explicitly names this cluster: "This allowed us to identify multiple
specific peptidergic neurons such as the CCAP and gustatory Hug neurons
from the subesophageal ganglion" (Figure 2K), confirming the authors
themselves recognised it as a known anatomical group, not merely a
transcriptomic artifact.

## Markers

- Hug is the top Table S3 marker of the shared parent res-2.0 cluster 46
  (annotated "Peptidergic"), alongside Proc, Crz, ITP, Gr43a and other
  neuropeptide genes — consistent with cluster 46 being the general
  peptidergic cluster from which Hug, Gr43a and Proc/Gpb5 were all
  subclustered.

## Location

- Subesophageal zone (SEZ); hugin-PC neurons project to the protocerebrum,
  hugin-VNC to the ventral nerve cord, hugin-RG to the ring gland —
  the atlas cannot distinguish these subtypes.

## Function

- Feeding-related gustatory processing and suppression; relay of taste
  information to feeding motor circuits and endocrine output (via
  hugin-RG to ring gland).

## Label provenance

No REVIEW flag. GEO label "Hug" comes from the S2 neuropeptide
re-clustering; Table S2 annotates the shared parent res-2.0 cluster 46 as
"Peptidergic" (literature markers, no specific reference), and the paper's
main text independently and explicitly names "Hug neurons from the
subesophageal ganglion" as a directly identified population.

## Mapping notes

Hugin neurons are a KNOWN anatomical group, but comprise at least three
morphologically and functionally distinct subtypes (hugin-PC/VNC/RG) that
this transcriptomic cluster does not resolve. The honest mapping target is
therefore a common parent term ("hugin neuron"/gustatory hugin-expressing
neuron of the SEZ) rather than any single subtype, unless further evidence
(e.g. co-markers distinguishing projection target) becomes available.
