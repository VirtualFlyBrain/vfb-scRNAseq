# Pm1/Pm2/Pm3

*Cluster `Pm1/Pm2/Pm3` (Seurat res-2.0 cluster 48; 316 cells; ages 0-50 days)
in Davie et al. 2018 (GSE107451, 57K adult brain). A coarser, three-way merge
of all GABAergic proximal-medulla (Pm) interneuron types.*

## Summary

This is a second, independent cluster covering the GABAergic Pm interneuron
family, distinct from the `Pm1/Pm2` cluster (res-2.0 cluster 12). Table S2
annotates it "Pm1/Pm2/Pm3" by literature markers alone (Erclik et al., 2017),
i.e. here the Vsx1+ Pm3 cells were not separable from the svp+ Pm1/Pm2 cells,
so all three are lumped together. This represents a coarser split than the
`Pm1/Pm2` cluster and is not simply a superset/subset of it or of the separate
`Pm3` cluster (res-2.0 cluster 73) - it is a distinct group of 316 cells with
its own res-2.0 identity.

## Markers

- Gad1, VGAT - GABAergic identity.
- Lim3, svp (Pm1/Pm2 markers) together with Vsx1 and Vsx2 (Pm3 marker family)
  both present in the top markers, consistent with a mixed Pm1+Pm2+Pm3
  population that could not be resolved further at this resolution.
- Other top markers: CG14989, br, DIP-delta, msi, mAChR-A, heph, rad.

## Location

- **Neuropil:** medulla, proximal layers.
- **Cell class:** GABAergic optic-lobe local interneuron (Pm family).

## Function

- Local inhibitory processing in the proximal medulla, as for Pm1/Pm2/Pm3
  individually (Erclik et al., 2017).

## Label provenance

Table S2 res-2.0 cluster 48 annotation "Pm1/Pm2/Pm3" (method: literature
markers; ref Erclik et al., 2017) - GEO label matches S2 exactly, no REVIEW
flag. Two other, non-identical GEO clusters in this atlas also carry Pm
identities: `Pm1/Pm2` (res-2.0 cluster 12, 1162 cells) and `Pm3` (res-2.0
cluster 73, 82 cells). All three should be treated as separate pieces of
evidence for the same underlying cell-type family, not reconciled into one.

## Mapping notes

A three-way merged/remainder group: it represents cells whose Pm1 vs Pm2 vs
Pm3 identity could not be resolved, so mapping should go no finer than a
common parent for the Pm1-3 GABAergic proximal-medulla interneuron group.
Given three separate GEO clusters exist for overlapping Pm identities at
different resolutions, flag for the mapping step that Pm1/Pm2, Pm3 and
Pm1/Pm2/Pm3 are three distinct, non-overlapping cell groups in this atlas
version and should not all be forced to the same single FBbt term.
