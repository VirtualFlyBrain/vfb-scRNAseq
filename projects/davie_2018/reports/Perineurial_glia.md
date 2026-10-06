# Perineurial_glia

*Cluster `Perineurial_glia` (Seurat res-2.0 cluster 70, plus a minority of
cells from cluster 85; 259 cells; ages 0-50 days) in Davie et al. 2018
(GSE107451, 57K adult brain). Outer surface glia forming the outer layer of
the blood-brain barrier.*

## Summary

Perineurial glia are the outermost of the two surface-glia layers that form
the Drosophila blood-brain barrier, lying external to the subperineurial
glia and mediating nutrient exchange and osmoregulation at the brain
surface. The paper identifies this cluster among the "surface glia (Indy)"
subtypes, distinguishing perineurial from subperineurial glia by marker
(Vmat for perineurial per the paper's Figure 1D text; DeSalvo et al., 2014;
Konstantinides et al., 2018).

## Markers

- Table S3 top markers for res-2.0 cluster 70 include CG3168, Cys, CG4797,
  CG14687, Tret1-1, CG6126, Gabat, SPARC — Tret1-1 (trehalose transporter)
  and SPARC are consistent with perineurial glia's known metabolic/barrier
  role at the brain surface.

## Location

- **Compartment:** outermost surface glial layer, forming the perineurial
  sheath at the brain surface, external to subperineurial glia.
- **Cell class:** perineurial (surface) glia (non-neuronal), class G.

## Function

- Outer blood-brain-barrier glia; mediates nutrient exchange and
  osmoregulation between hemolymph and the brain (DeSalvo et al., 2014).

## Label provenance

Table S2 res-2.0 cluster 70 is annotated "Perineurial glia" by literature
markers/mapping (DeSalvo et al., 2014; Konstantinides et al., 2018); the
majority of the GEO cluster (200 of 259 cells) matches this exactly
(label_validation.tsv: match). **REVIEW:** the remaining 59 cells in this GEO
cluster come from res-2.0 cluster 85, which Table S2 annotates
"Subperineurial Glia," not perineurial — i.e. a genuine discrepancy between
the GEO label and the authors' own S2 annotation for that minority
sub-population. This should be treated as a real ambiguity, not a labelling
error to silently resolve: a small fraction of cells assigned to
`Perineurial_glia` may actually be subperineurial glia by the authors' own
annotation.

## Mapping notes

Perineurial glia are an established, single Drosophila surface-glia subtype
distinct from subperineurial glia; an FBbt term for "perineurial glial cell"
is expected. Given the REVIEW-flagged mixing with cluster 85
("Subperineurial Glia"), this GEO cluster is not cleanly single-type: the
bulk (200/259 cells) should map cleanly to perineurial glia, but a minority
(59/259) may represent misassigned subperineurial glia. Recommend flagging
this cluster as predominantly-but-not-purely perineurial glia rather than
asserting an exact match without qualification.
