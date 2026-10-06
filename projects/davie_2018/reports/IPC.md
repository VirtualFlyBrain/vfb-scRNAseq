# IPC

*Cluster `IPC` (Seurat res-2.0 cluster 25, "Unannotated" at res-2.0, but also
independently annotated as IPC at res-8.0 cluster 30; 17 cells; ages
0,1,3,6,9 days) in Davie et al. 2018 (GSE107451, 57K adult brain). Also
recovered by the paper's 1,269-cell neuropeptide re-clustering (Figure 2K).*

## Summary

Insulin-producing cells (IPCs): a well-established, anatomically defined
neurosecretory cell type in the Drosophila brain, located in the pars
intercerebralis, that produces multiple Drosophila insulin-like peptides
(Brogiolo et al., 2001; Rulifson et al., 2002). The paper explicitly
identifies this population by its clean marker signature (Ilp2, Ilp3, Ilp5)
both as a res-8.0 literature-marker cluster (cluster 30) and independently as
one of the specific neuropeptide subclusters recovered in Figure 2K
("a cluster expressing Ilp2, Ilp3, and Ilp5, which are markers for the
insulin-producing cells (IPCs)"). This is one of the most confidently resolved
cell types in the entire neuropeptide subclustering exercise.

## Markers

Top markers for res-2.0 cluster 25 (the primary-clustering home of these
cells): Ilp2, Ilp3, Ilp5, TM4SF, CG31808, Gpb5, Pdf, CG42394, spab. Ilp2/3/5
co-expression is the canonical, highly specific IPC signature.

## Location

Pars intercerebralis of the adult central brain (median neurosecretory cell
cluster); IPCs project to the corpora cardiaca and other neurohemal/peripheral
release sites.

## Function

Endocrine/systemic: production and release of Drosophila insulin-like
peptides (Ilp2, Ilp3, Ilp5) regulating growth, metabolism, and lifespan,
analogous to vertebrate pancreatic beta cells (Brogiolo et al., 2001;
Rulifson et al., 2002).

## Label provenance

Table S2 res-2.0 cluster 25 = "Unannotated" (no method/references at res-2.0),
but Table S2 records a related res-8.0 annotation (cluster 30 = "IPC",
method "literature markers", references Brogiolo et al., 2001; Rulifson et
al., 2002) and a subcluster-level annotation ("all cells expressing
neuropeptides" -> "IPC", same references). `label_validation.tsv`: status
"S2 neuropeptide re-clustering (cells from multiple res-2.0 clusters)" - the
GEO `IPC` label reflects the Figure 2K subclustering result, consistent with
and corroborated by the independent res-8.0 IPC annotation.

## Mapping notes

Single, well-defined cell type: the insulin-producing cells are a specific,
long-established Drosophila neuron type with a clear, specific marker
signature and two independent annotation routes (res-8.0 clustering and
neuropeptide subclustering) agreeing on identity. Expect an exact,
adult-appropriate FBbt term for the IPC/insulin-producing cell type; this is
one of the highest-confidence mappings among these clusters.
