# Subperineurial_glia

*Cluster `Subperineurial_glia` (Seurat res-2.0 cluster 66; 217 cells; ages
0-50 days) in Davie et al. 2018 (GSE107451, 57K adult brain). Inner surface
glia forming the septate-junction-sealed layer of the blood-brain barrier.*

## Summary

Subperineurial glia form the inner layer of the two-layer surface glia that
constitute the Drosophila blood-brain barrier, sealed by septate junctions
(moody-dependent) that provide the barrier's diffusion-blocking function,
lying internal to the perineurial glia. The paper identifies this cluster
among the "surface glia (Indy)" subtypes, distinguishing subperineurial by
marker moody, citing Bainton et al. (2005), DeSalvo et al. (2014) and Stork
et al. (2012).

## Markers

- Table S3 top markers for res-2.0 cluster 66 include CG3036, eEF1alpha1,
  Timp, CG9338, Fas2, sog, SPARC, lama — Fas2 (Fasciclin 2, a septate-junction
  associated cell-adhesion molecule) and lama (laminin) are consistent with
  subperineurial glia's known septate-junction and basal-lamina biology.

## Location

- **Compartment:** inner surface glial layer, forming the septate-junction
  sealed barrier at the brain surface, internal to perineurial glia.
- **Cell class:** subperineurial (surface) glia (non-neuronal), class G.

## Function

- Inner blood-brain-barrier glia; forms septate junctions (moody-dependent)
  that block paracellular diffusion, the principal barrier function of the
  Drosophila BBB (Bainton et al., 2005; Stork et al., 2012).

## Label provenance

Table S2 res-2.0 cluster 66 is annotated "Subperineurial Glia" by literature
markers/mapping (Bainton et al., 2005; DeSalvo et al., 2014; Stork et al.,
2012); the GEO label matches exactly (label_validation.tsv: match). No REVIEW
flag for this cluster itself. Note, however, that a separate res-2.0 cluster
also annotated "Subperineurial Glia" in Table S2 (cluster 85) contributes 59
cells to the *different* GEO cluster `Perineurial_glia` (see that report's
Label provenance / REVIEW note) — i.e. some genuine subperineurial-glia cells
by the authors' own S2 annotation are not present in this `Subperineurial_glia`
GEO cluster but sit instead in `Perineurial_glia`.

## Mapping notes

Subperineurial glia are an established, single Drosophila surface-glia
subtype distinct from perineurial glia; an FBbt term for "subperineurial
glial cell" is expected and this cluster should map to it as a single type.
Be aware when reconciling counts/coverage across the two surface-glia
clusters in this atlas that a second, S2-annotated "Subperineurial Glia"
population (res-2.0 cluster 85) was split off into the `Perineurial_glia` GEO
cluster rather than this one; this cluster (res-2.0 66) is nonetheless
internally clean (single res-2.0 cluster, no ambiguous mixing) and maps
straightforwardly.
