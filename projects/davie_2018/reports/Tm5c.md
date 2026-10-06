# Tm5c

*Cluster `Tm5c` (Seurat res-2.0 cluster 39; 382 cells; ages 0-50 days) in
Davie et al. 2018 (GSE107451, 57K adult brain). Author's own text says this
identity could not be cleanly separated from Dm8.*

## Summary

Tm5c is a GEO simplification of Table S2's own merged annotation for
res-2.0 cluster 39, "Dm8/Tm5c". The main text is explicit about the
ambiguity: "Two clusters co-express VGlut and ort, which could be linked to
Tm5c and Dm8, but a division between the two could not be made"
(Karuppudurai et al., 2014; Melnattur et al., 2014). This cluster is
therefore evidence for a Tm5c/Dm8-mixed population, not a resolved Tm5c
identity.

## Markers

Table S2 annotation "Dm8/Tm5c" (method: literature markers/mapping; refs
Karuppudurai et al., 2014; Konstantinides et al., 2018; Melnattur et al.,
2014). Top Table S3 markers for res-2.0 cluster 39: CG2016, CG42540, CG6044,
CG1358, CG34355, CG3822, Npc2a, CG33777, VepD, nAChRalpha7, VGlut, Scp2. Both
Tm5c and Dm8 are glutamatergic and co-express VGlut and the histamine
receptor ort, consistent with shared R7/R8 photoreceptor input and the
authors' inability to separate them by markers.

## Location

Tm5c and Dm8 are both distal-medulla neurons downstream of R7/R8
photoreceptors; Tm5c is a transmedullary neuron projecting to the lobula,
while Dm8 is a distal medulla amacrine interneuron confined to layer M6 (see
the Kurmangaliyev 2020 `Dm8.md` report for Dm8 anatomy). They are
anatomically distinct cell types despite the shared transcriptional
signature seen here.

## Function

Both cell types sit in the UV-wavelength colour-discrimination pathway
downstream of R7 (Gao et al., 2008; Karuppudurai et al., 2014); this cluster
cannot distinguish which functional role (transmedullary relay vs. wide-field
amacrine) individual cells occupy.

## Label provenance

REVIEW: GEO's "Tm5c" label drops half of Table S2's own merged annotation
"Dm8/Tm5c" for res-2.0 cluster 39, and the main text explicitly states the
two identities could not be separated (label_validation.tsv: "differs from
S2 res-2.0 'Dm8/Tm5c' — REVIEW"). Treat the GEO label as a simplification,
not evidence that this cluster is pure Tm5c.

## Mapping notes

This is likely a merged/unresolved group covering both Tm5c and Dm8 rather
than a single cell type, by the authors' own admission. The safest FBbt
level is a common parent (or explicit "Tm5c or Dm8, undetermined" framing)
rather than an exact match to Tm5c alone; flag for careful handling in the
mapping step given the direct textual caveat.
