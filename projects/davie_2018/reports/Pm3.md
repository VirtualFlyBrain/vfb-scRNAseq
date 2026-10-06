# Pm3

*Cluster `Pm3` (Seurat res-2.0 cluster 73; 82 cells; ages 0-50 days) in Davie
et al. 2018 (GSE107451, 57K adult brain). GABAergic proximal-medulla Pm3
neurons, but with a marker profile dominated by neuropeptide genes.*

## Summary

Pm3 is the Vsx1+ member of the GABAergic Pm1-3 proximal medulla interneuron
family (Erclik et al., 2017); the paper distinguishes it from Pm1/Pm2 because
Vsx1 is expressed only in Pm3, while Lim3 is shared by all three and svp marks
only Pm1/Pm2. However, this cluster's own top markers (Table S3) are
dominated by the neuropeptide genes AstA and Nplp1, plus dopaminergic markers
Dat and Lmx1a, rather than by Lim3/Vsx1 - see Label provenance.

## Markers

- AstA, Nplp1 - top two markers, both neuropeptides.
- Dat, Lmx1a - dopaminergic-neuron markers also prominent.
- Vsx2 (Vsx1 paralog), mAChR-A/B, IA-2, hbn among other top markers; classic
  Pm markers Lim3/svp are notably absent from the top-20 list for this
  specific cluster.

## Location

- **Neuropil:** medulla, proximal layers (Pm interneurons).
- **Cell class:** GABAergic optic-lobe local interneuron, Vsx1+ subtype.

## Function

- Local inhibitory processing in the proximal medulla (Pm family, Erclik et
  al., 2017); the strong AstA/Nplp1 neuropeptide signature suggests a
  peptidergic co-transmission role for at least part of this cluster.

## Label provenance

Table S2 res-2.0 cluster 73 is annotated "Pm3" (method: literature
markers/mapping; refs Erclik et al., 2017; Konstantinides et al., 2018) - GEO
label matches S2, no REVIEW flag. However, `label_validation.tsv` also records
that the GEO label `AstA/Nplp1` (a neuropeptide-defined subcluster built from
cells across multiple res-2.0 clusters) maps back to this same res-2.0 cluster
73/"Pm3". Combined with this cluster's own marker list being AstA/Nplp1-led
rather than Lim3/Vsx1-led, this cluster likely captures the neuropeptidergic
subset of Pm3 (or a Pm3-enriched population overlapping with AstA/Nplp1+
cells) rather than a clean, marker-confirmed Pm3 population.

## Mapping notes

Likely a single established type (Pm3), but the evidence for that identity
here is the authors' literature-based S2 call rather than this cluster's own
top markers, which instead point to a neuropeptide (AstA/Nplp1)-expressing
substate. Flag for mapping: possible conflation of a cell type (Pm3) with a
cell state/co-transmitter signature (AstA/Nplp1+), and note the two other Pm
clusters in this atlas (`Pm1/Pm2`, `Pm1/Pm2/Pm3`) as related, non-identical
evidence.
