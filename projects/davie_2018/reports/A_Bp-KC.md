# A/B*-KC

*Cluster `A/B*-KC` (Seurat res-2.0 cluster 28; 518 cells; ages 0-50 days) in
Davie et al. 2018 (GSE107451, 57K adult brain). Alpha'/beta'-lobe Kenyon
cells of the mushroom body ('*' denotes prime: α'/β').*

## Summary

Alpha'/beta' Kenyon cells (α'/β'-KCs) are the intrinsic neurons of the
mushroom body alpha'/beta' lobes, the third of the three principal KC
classes. The paper identifies this cluster among the KCs (marked overall by
ey and prt) by trio expression without sNPF, and additionally reports DAT
(dopamine transporter) as a specific marker for this class (Figures S3G-H).

## Markers

- trio-positive, sNPF-negative (paper's discriminating logic for α'/β' vs
  the other two KC classes).
- DAT (dopamine transporter) reported by the authors as a specific α'/β'-KC
  marker.
- Table S3 top markers for res-2.0 cluster 28 include CG8641, mamo, jdp,
  Pka-C1, Pka-C3, Dop1R2, mub, DAT, trio, Rgk1, ey — confirming both trio and
  DAT, alongside the same PKA-pathway signature shared with the other KC
  lobes.
- α'/β'-KCs also stand out functionally in this paper: they show higher
  OxPhos gene expression and higher in vivo mitochondrial turnover (mitoTimer
  assay) than the other two MB lobes.
- No finer subtype resolution (e.g. α'β'-anterior-posterior vs -medial) is
  available; subclustering separated cells mainly by technical covariates.

## Location

- **Neuropil:** mushroom body, alpha' and beta' lobes.
- **Cell body:** Kenyon cell body cluster, dorsal posterior cortex (calyx
  region).
- **Cell class:** intrinsic mushroom body neuron (Kenyon cell), class N.

## Function

- Intrinsic mushroom body neuron; α'/β'-KCs are required for early memory
  consolidation (acquisition/short-term to middle-term memory) in the
  classical model of fly olfactory associative learning, and are
  dopaminergic-transporter-expressing, distinguishing their neuromodulatory
  profile from γ and α/β KCs.

## Label provenance

Table S2 res-2.0 cluster 28 is annotated "a'/b'-KC" by literature markers
(Medioni et al., 2014); the GEO label "A/B*-KC" is a curated ASCII-safe
synonym of this ('*' standing in for the prime symbol) (label_validation.tsv:
match, curated synonym). No REVIEW flag.

## Mapping notes

Alpha'/beta' Kenyon cells are an established, morphologically and
functionally distinct KC subclass; an adult-specific FBbt term for
"alpha'/beta' Kenyon cell" should exist and this cluster is expected to map
to it as a single type at that granularity, without resolution of any finer
α'β' subtypes.
