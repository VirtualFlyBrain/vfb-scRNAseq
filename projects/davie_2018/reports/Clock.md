# Clock

*Cluster `Clock` (Seurat res-2.0 cluster 36 minus the LNv subcluster; 389
cells; ages 0-50 days) in Davie et al. 2018 (GSE107451, 57K adult brain). The
remainder of the "Clock neurons" cluster after Pdf(+) LNv cells were pulled
out via neuropeptide re-clustering.*

## Summary

Res-2.0 cluster 36 was annotated "Clock neurons" from literature
markers/mapping (Abruzzi et al., 2017; Klarsfeld et al., 2004; Park et al.,
2000). Separately, the paper's neuropeptide-focused re-clustering (1,269
high-neuropeptide-UMI cells) identified "a cluster with Pdf-expressing cells,
which contain all but one neuron of the lateral ventral neurons (LNvs)" -
reported here as the `LNv` cluster/label. `Clock` is the remainder of
cluster 36 once the Pdf+ LNv cells are excluded. The core Drosophila clock
circuit comprises several anatomically distinct groups beyond the LNv (small
and large ventral lateral neurons): LNd (dorsal lateral neurons), DN1
(dorsal neurons 1, split out separately here as the `DN1` cluster), DN2, DN3,
and LPN (lateral posterior neurons). Since LNv and DN1 are both broken out
separately, the `Clock` remainder most likely represents an unresolved mix
of LNd, DN2, DN3 and/or LPN neurons (and possibly residual DN1 cells not
captured by the smaller, separately-clustered DN1 group).

## Markers

Res-2.0 cluster 36 markers (pre-LNv-removal, so still Pdf-weighted): Pdf,
AstC, CG17777, bru3, CG18599, bi, CG13054, tim, IA-2, 7B2, vri, fax, Clk,
cry, Dh44, Dr, amon. Core clock genes (tim, Clk, cry, vri) confirm a
clock-neuron identity generically; AstC is a marker reported for non-LNv
clock groups (e.g. LNd/DN3) in the literature.

## Location

Clock neuron somata lie in the dorsal and lateral protocerebrum, with
projections into the dorsal protocerebrum and accessory medulla; exact
subgroup(s) present here are not resolved.

## Function

Circadian pacemaker neurons; the non-LNv, non-DN1 groups (LNd, DN2, DN3,
LPN) contribute to circadian timekeeping, light entrainment, and evening/
morning activity peaks in coordination with the LNv.

## Label provenance

Table S2 res-2.0 annotation for cluster 36 is "Clock neurons" (match,
curated synonym). No REVIEW flag. The GEO `Clock` label represents this
cluster net of the separately-labelled `LNv` subset.

## Mapping notes

This is a remainder/unresolved group of clock neurons: it most likely mixes
several named clock-neuron classes (LNd, DN2, DN3, LPN) without
transcriptomic separation between them. A single specific FBbt term is not
appropriate; the honest level is a broad "circadian clock neuron" (or
"non-LNv, non-DN1 clock neuron") parent term, flagged as a merged group of
uncertain subgroup composition.
