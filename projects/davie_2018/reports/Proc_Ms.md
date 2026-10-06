# Proc/Ms

*Cluster `Proc/Ms` (Seurat res-2.0 cluster 0; 71 cells; ages 0, 1, 3, 6, 9,
15, 30, 50 days) in Davie et al. 2018 (GSE107451, 57K adult brain). A
proctolin/myosuppressin co-expression subcluster with an unusually
scattered cell-of-origin distribution.*

## Summary

"Proc/Ms" denotes cells co-expressing proctolin (Proc) and myosuppressin
(Ms), two separate, independently well-studied Drosophila neuropeptides
(Proc: modulates muscle contraction and locomotion; Ms: inhibits gut/heart
motility and modulates feeding via sNPF-related pathways). Unlike Hug,
Gr43a and Proc/Gpb5 (which are all drawn predominantly from the same
"Peptidergic" parent cluster 46), the 71 Proc/Ms cells are scattered across
more than 20 different res-2.0 parent clusters, with no single cluster
contributing more than ~17% of cells (12/71 from cluster 0, the nominal
res-2.0 parent). This indicates the label reflects a co-expression
signature detected across a heterogeneous mix of underlying transcriptomic
states, not cells drawn from one coherent parent population.

## Markers

- Table S3 top markers listed are for parent cluster 0 (VGlut, Nplp1, 7B2,
  IA-2, pros, dati, Corin, Lmx1a, etc.) — broadly peptidergic/glutamatergic
  markers of a large, heterogeneous cluster, not specific to Proc or Ms.

## Location

- Not resolved; Proc- and Ms-expressing neurons individually are each
  distributed across multiple brain regions (median neurosecretory cells,
  ventral nerve cord, and elsewhere), and no single co-expression locus is
  established here.

## Function

- Proctolin: locomotor/muscle modulation. Myosuppressin: feeding/gut and
  cardiac inhibition. Combined functional significance of co-expression is
  not addressed in this paper.

## Label provenance

No REVIEW flag. GEO label "Proc/Ms" comes from the S2 neuropeptide
re-clustering; Table S2 marks the nominal parent res-2.0 cluster 0 as
"Unannotated", and the cells' scattered origin (>20 source clusters) is
notably more diffuse than the other neuropeptide subclusters.

## Mapping notes

Given the scattered cell-of-origin and lack of a coherent parent cluster,
this looks like a co-expression REMAINDER group rather than a single,
coherent cell type — possibly pooling several distinct Proc+ and/or Ms+
neuron types that happen to co-express both peptides at low level, or a
genuine but heterogeneous small population. Recommend mapping (if at all)
to a generic "proctolin- and myosuppressin-expressing neuron" class with
low confidence, flagging that this may not correspond to a single
established anatomical cell type.
