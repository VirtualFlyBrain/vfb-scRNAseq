# Pm1/Pm2

*Cluster `Pm1/Pm2` (Seurat res-2.0 cluster 12; 1162 cells; ages 0-50 days) in
Davie et al. 2018 (GSE107451, 57K adult brain). A GABAergic proximal-medulla
interneuron cluster combining two closely related Pm cell types.*

## Summary

Pm1 and Pm2 are two of the three GABAergic proximal medulla (Pm) interneuron
types of the optic lobe medulla cortex (Erclik et al., 2017). The paper states
that all Pm neurons share Lim3, Vsx1 marks Pm3 only, and svp is expressed by
both Pm1 and Pm2 - i.e. svp/Lim3+, Vsx1- cells cannot be split further into Pm1
vs Pm2 by the markers available, so the atlas groups them as one cluster.

## Markers

- Gad1, VGAT - GABAergic identity.
- Lim3, svp - pan-Pm / Pm1+Pm2 markers (Erclik et al., 2017); Vsx1, the
  Pm3-specific marker, is absent from this cluster's top markers.
- hth, mab-21, Argk, CG13739, CG14989 among other top Table S3 markers.

## Location

- **Neuropil:** medulla, proximal layers (Pm interneurons).
- **Cell class:** GABAergic local interneuron of the optic lobe medulla.

## Function

- Local inhibitory processing within the proximal medulla; part of the Pm1-3
  interneuron family characterised developmentally by Erclik et al. (2017).

## Label provenance

Table S2 res-2.0 cluster 12 is annotated "Pm1/Pm2" (method: literature
markers/mapping; refs Erclik et al., 2017; Konstantinides et al., 2018). GEO
label matches S2 exactly - no REVIEW flag.

## Mapping notes

This is a merged group of two established cell types (Pm1 and Pm2), not
separable at this transcriptomic resolution - a common parent covering both
(or two exactMatch-candidate terms left unresolved) is the honest mapping
level. Note a related, coarser cluster in this atlas, `Pm1/Pm2/Pm3` (res-2.0
cluster 48), also exists and additionally includes Pm3 cells not separated out
there; the two clusters are not simply nested at different thresholds of the
same population, so mapping should treat them as distinct evidence, not
duplicates.
