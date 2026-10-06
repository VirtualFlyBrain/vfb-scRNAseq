# Plasmatocytes

*Cluster `Plasmatocytes` (Seurat res-2.0 cluster 43; 329 cells; ages 0-50
days) in Davie et al. 2018 (GSE107451, 57K adult brain). Hemocytes (blood
cells) present in the dissected brain sample, not a brain cell type.*

## Summary

This cluster is composed of hemocytes (blood cells) rather than intrinsic
neurons or glia of the brain. The paper explicitly identifies it as
"hemocytes" among the non-neuronal cell types detected in the dissected
tissue, marked by Hml (Hemolectin) and cited to Goto et al. (2001, 2003).
Hemocytes/plasmatocytes are hemolymph-circulating immune cells that adhere to
or are trapped within brain tissue during dissection (e.g. at the surface or
in the perineurial sheath/hemolymph-facing surfaces); they are not generated
by or resident components of neural circuitry, and their presence reflects
sample composition rather than a brain-intrinsic cell type.

## Markers

- Hml (Hemolectin) — the defining plasmatocyte/hemocyte marker used by the
  paper (Goto et al., 2001, 2003).
- Table S3 top markers for res-2.0 cluster 43 include CG4250, regucalcin,
  CG14629, Col4a1, Ppn, Hml, Inos, lectin-28C, lectin-24Db, Sr-CI — Col4a1
  (Collagen IV), Ppn (Peroxidasin), and the lectin/Sr-CI (scavenger receptor)
  genes are canonical hemocyte/plasmatocyte markers involved in basement
  membrane deposition and phagocytic/immune surveillance functions.

## Location

- Circulating/adherent hemolymph cells associated with the brain surface and
  vasculature-adjacent tissue at the time of dissection; not a resident
  neural or glial cell type and not assignable to a brain neuropil or cortex
  compartment.
- **Cell class:** plasmatocyte (hemocyte), non-neural, non-CNS-derived.

## Function

- Innate immune/phagocytic blood cells (plasmatocytes are the major
  Drosophila hemocyte class, responsible for phagocytosis and basement
  membrane/extracellular matrix deposition); function is systemic/immune, not
  neural (Goto et al., 2001, 2003).

## Label provenance

Table S2 res-2.0 cluster 43 is annotated "Hemocytes" by literature markers
(Goto et al., 2001, 2003). label_validation.tsv records this as a "match
(curated synonym of S2 'Hemocytes')" — i.e. the GEO label `Plasmatocytes`
is a curator-applied synonym for the authors' broader "Hemocytes" annotation;
plasmatocytes are indeed the dominant hemocyte type expected in this context.
No REVIEW flag.

## Mapping notes

This cluster should NOT be mapped as a brain cell type. Plasmatocytes/
hemocytes are blood cells incidentally captured with the dissected brain
tissue, not a neuron or glial subtype intrinsic to the CNS; any FBbt mapping
should reflect this as a hemolymph/immune cell type (if represented in FBbt
at all) or be flagged for exclusion from brain-cell-type mapping altogether,
distinguishing it clearly from the true glial/neuronal clusters in this
atlas.
