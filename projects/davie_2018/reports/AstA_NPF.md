# AstA/NPF

*Cluster `AstA/NPF` (Seurat res-2.0 cluster 17, annotated "Mip"; 20 cells;
ages 0,1,3,30,50,6,9 days) in Davie et al. 2018 (GSE107451, 57K adult brain).
A neuropeptide co-expression subcluster (Allatostatin A + NPF) from the
paper's 1,269-cell neuropeptide re-clustering (Figure 2K).*

## Summary

Cells co-expressing the neuropeptide genes AstA (Allatostatin A) and NPF
(neuropeptide F), recovered by the neuropeptide-focused subclustering. Nearly
all cells (19/20) map back to res-2.0 cluster 17, the same parent cluster as
the atlas's separate `Mip` label (annotated by literature markers, Carlsson et
al., 2010; Min et al., 2016), whose own top markers already include NPF and
Optix/Lim1/Rx (optic-lobe patterning genes). This means AstA/NPF is not an
independent population but a neuropeptide co-expression subset drawn from the
same broader, likely optic-lobe-associated cluster as `Mip`.

## Markers

Top res-2.0 cluster-17 markers: Optix, Lim1, NPF, Ets65A, Mip, Rx, robo2,
Ten-a, IA-2, Rim. AstA and NPF are the specific co-expression markers that
define this subcluster; they are drawn from the same parent-cluster gene list
that also yields the `Mip` label, so no marker set specific to AstA/NPF alone
is available.

## Location

Not independently resolved; consistent with the optic-lobe-leaning signature
of the parent cluster (see `Mip` report).

## Function

Not established for this specific co-expression group beyond general
neuropeptide (AstA, NPF) signalling.

## Label provenance

Table S2 res-2.0 cluster 17 = "Mip", method "literature markers", references
(Carlsson et al., 2010; Min et al., 2016). `label_validation.tsv`: status "S2
neuropeptide re-clustering (cells from multiple res-2.0 clusters)" - AstA/NPF
is a Figure 2K subcluster whose cells overwhelmingly derive from the same
res-2.0 cluster as the independently labelled `Mip` cluster, i.e. these two
GEO labels likely partition (or overlap within) the same underlying
population by different neuropeptide markers.

## Mapping notes

Best treated as a transcriptomic co-expression subgroup, not a confirmed,
separately characterised anatomical neuron type: unlike AstA/Nplp1 (which
tracks a specifically named, marker-supported Pm3 identity), AstA/NPF's
parent cluster ("Mip") is itself only loosely localised and the co-expression
of AstA and NPF is not called out or referenced by the paper as a known cell
type. Lower confidence than AstA/Nplp1 that this corresponds to one discrete,
previously described neuron; flag for the mapping step as possibly needing a
broad/parent-level term or treatment as a marker co-expression state rather
than a distinct type.
