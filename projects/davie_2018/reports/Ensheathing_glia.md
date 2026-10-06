# Ensheathing_glia

*Cluster `Ensheathing_glia` (Seurat res-2.0 cluster 14, with a minority of
cells from cluster 35; 1,517 cells; ages 0-50 days) in Davie et al. 2018
(GSE107451, 57K adult brain). Ensheathing glia wrapping neuropil
compartments/tracts.*

## Summary

Ensheathing glia form thin glial sheaths around neuropil compartments and
axon tracts (including the optic chiasmata, which have their own dedicated
"chiasm glia" cluster in this atlas), separating them from surrounding
structures and clearing degenerating axonal debris. Unlike astrocyte-like
glia, ensheathing glia do not infiltrate the neuropil interior. The paper
lists ensheathing glia among clusters newly annotated in this study by
transcriptomic mapping to markers from Konstantinides et al. (2018), grouped
in the text alongside newly annotated optic-lobe cell types (L1-5, T2/T3,
T4/T5, TmY14, etc.), consistent with at least part of this population being
optic-lobe-associated ensheathing glia; the paper does not explicitly state
whether central-brain and optic-lobe ensheathing glia are transcriptomically
distinguished here.

## Markers

- Table S3 top markers for res-2.0 cluster 14 include CG9377, CG16743, Tsf1,
  Ugt35b, CG8369, CG31706, GstD9, CAH1, nrv2 — nrv2 (Na+/K+ ATPase beta
  subunit) is a recognized glial marker consistent with an ensheathing/
  membrane-rich glial identity.

## Location

- **Compartment:** ensheathes neuropil compartments and axon tracts
  throughout the brain, including (per the atlas) tracts near the optic
  chiasmata; does not infiltrate neuropil interior.
- **Cell class:** ensheathing glia (non-neuronal), class G.

## Function

- Compartmental boundary/insulating glia; also implicated in phagocytic
  clearance of degenerating axons (established Drosophila ensheathing-glia
  biology, e.g. Doherty et al., 2009).

## Label provenance

Table S2 res-2.0 cluster 14 is annotated "Ensheathing glia" by mapping
(Konstantinides et al., 2018); the GEO label matches exactly for the majority
of cells (label_validation.tsv: match). However, the GEO `Ensheathing_glia`
label merges cells from two res-2.0 clusters: 1,068 cells from cluster 14
("Ensheathing glia") and 449 cells from cluster 35, which Table S2 also
annotates "Ensheathing glia" — so both contributing res-2.0 clusters carry
the same S2 annotation and there is no discrepancy, but the Table S3 marker
list above reflects only the parent cluster 14, not cluster 35.

## Mapping notes

Ensheathing glia are an established Drosophila glial subtype; an FBbt term
for "ensheathing glial cell" is expected. Because this GEO cluster merges two
res-2.0 clusters both annotated "Ensheathing glia" by the authors, it is
reasonable to treat it as a single type at the ensheathing-glia level.
However, since whole-brain ensheathing glia are known to include
morphologically distinct central-brain and optic-lobe (e.g. chiasm-adjacent)
populations, and the paper's own listing groups "ensheathing and chiasm glia"
alongside newly annotated optic-lobe types, this cluster may represent a
partially merged group spanning both regions; flag for the mapping step in
case FBbt requires resolving central-brain vs optic-lobe ensheathing glia
separately from this single transcriptomic cluster.
