# LNv

*Cluster `LNv` (identified via neuropeptide re-clustering, dominant
contributor Seurat res-2.0 cluster 36; 41 cells; ages 0-50 days) in Davie et
al. 2018 (GSE107451, 57K adult brain). Pdf(+) lateral ventral clock neurons,
recovered from a separate neuropeptide-focused analysis, not a direct res-2.0
subcluster.*

## Summary

The paper re-clustered 1,269 cells with high neuropeptide-gene UMI counts
(selected across the whole dataset, not from a single res-2.0 cluster) and
identified within it "another cluster with Pdf-expressing cells, which
contain all but one neuron of the lateral ventral neurons (LNvs), an
important clock-neuron subtype" (Klarsfeld et al., 2004 cited in Table S2).
LNv comprises the small (sLNv) and large (lLNv) ventral lateral clock
neurons, both Pdf-expressing; the authors state their reclustered group
recovers essentially the complete LNv population per brain ("all but one").
Consistent with this cross-cluster origin, most contributing cells trace to
res-2.0 cluster 36 ("Clock neurons"), with smaller numbers from clusters 32,
23, 25, 34 and 50 - reflecting imperfect original clustering of these rare,
Pdf-driven cells before the targeted re-clustering.

## Markers

Table S3 markers are for the dominant parent (res-2.0 cluster 36): Pdf,
AstC, CG17777, tim, Clk, cry, vri, Dh44, IA-2, 7B2 - Pdf being the defining
LNv marker. These are parent-cluster markers, not LNv-subcluster-specific.

## Location

Lateral protocerebrum; sLNv project to the dorsal protocerebrum and
accessory medulla, lLNv arborize in the medulla and across both optic lobes
via the posterior optic commissure.

## Function

Master circadian pacemaker neurons; Pdf release synchronizes the fly's
circadian clock network and drives morning locomotor activity.

## Label provenance

No direct res-2.0 Table S2 row for "LNv" - it appears in Table S2 as a
subcluster derived from "all cells expressing neuropeptides" (a re-clustering
across multiple res-2.0 input clusters), annotated "LNv" by literature
markers (Klarsfeld et al., 2004). `label_validation.tsv` confirms: "S2
neuropeptide re-clustering (cells from multiple res-2.0 clusters)." No
REVIEW flag, but note the multi-cluster origin.

## Mapping notes

LNv as recovered here likely represents a merged group of sLNv and lLNv
(both Pdf+), since the paper's description does not distinguish them within
this subcluster. A term covering "Pdf-expressing lateral ventral neurons"
(parent of sLNv/lLNv) is the honest mapping level unless further evidence
resolves the two; a specific sLNv- or lLNv-only term would overstate the
resolution actually achieved.
