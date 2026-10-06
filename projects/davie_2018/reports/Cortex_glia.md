# Cortex_glia

*Cluster `Cortex_glia` (Seurat res-2.0 cluster 60; 239 cells; ages 0-50 days)
in Davie et al. 2018 (GSE107451, 57K adult brain). Cortex glia that
ensheathe neuronal cell bodies in the cell-body rind.*

## Summary

Cortex glia surround and individually wrap neuronal (and glial) cell bodies
in the cortex/cell-body rind of the Drosophila CNS, forming a
trophic/insulating scaffold distinct from the surface glia (perineurial,
subperineurial) that form the outer blood-brain barrier and from the
neuropil-infiltrating astrocyte-like and ensheathing glia. The paper
identifies this cluster among the glial subtypes directly by the marker
wrapper, citing Konstantinides et al. (2018) and Spindler et al. (2009).

## Markers

- wrapper — the defining marker used by the paper to call this cluster
  (Spindler et al., 2009).
- Table S3 top markers for res-2.0 cluster 60 include CG9686, MtnA, wrapper,
  fabp, CG6218, apolpp — apolpp (apolipophorin) and fabp (fatty-acid binding
  protein) are consistent with cortex glia's known lipid-transport/trophic
  role in supporting neuronal cell bodies.

## Location

- **Compartment:** cell-body rind/cortex, ensheathing individual neuronal
  (and glial) somata; does not infiltrate synaptic neuropil.
- **Cell class:** cortex glia (non-neuronal), class G.

## Function

- Wraps individual cell bodies, providing trophic and metabolic support
  (lipid transport via apolpp) and structural insulation between somata
  (Spindler et al., 2009; Konstantinides et al., 2018).

## Label provenance

Table S2 res-2.0 cluster 60 is annotated "Cortex Glia" by literature
markers/mapping (Konstantinides et al., 2018; Spindler et al., 2009); the GEO
label matches exactly (label_validation.tsv: match). No REVIEW flag.

## Mapping notes

Cortex glia are an established, single Drosophila glial subtype; an FBbt term
for "cortex glial cell" is expected and this cluster should map to it as a
single type. The whole-brain dataset (central brain + optic lobes) does not
report a region-specific split for cortex glia, so this is likely a merged,
brain-wide pool rather than a resolved central-brain-only or
optic-lobe-only population; flag this if FBbt distinguishes region-specific
cortex glia subtypes.
