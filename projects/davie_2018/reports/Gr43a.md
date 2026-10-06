# Gr43a

*Cluster `Gr43a` (Seurat res-2.0 cluster 46; 79 cells; ages 0, 1, 3, 6, 9,
15, 30, 50 days) in Davie et al. 2018 (GSE107451, 57K adult brain). The
internal fructose-sensing Gr43a neurons, also independently annotated at
res-8.0.*

## Summary

Gr43a is a gustatory receptor that in the brain marks a specific,
functionally characterised population of internal fructose-sensing
neurons (Miyamoto and Amrein, 2014), which also co-express corazonin (Crz)
and act as a hemolymph-fructose sensor regulating feeding/satiety-related
signalling. The paper's main text explicitly states: "Using this higher
resolution [res-8.0], we are also able to identify the fructose-sensing
neurons that co-express Gr43a and Crz (Miyamoto and Amrein, 2014)," and
Table S2 independently annotates res-8.0 cluster 129 as "Gr43a neurons"
(literature markers, same reference). This is the best-corroborated
cluster among the neuropeptide-subcluster set, with agreement across the
res-2.0 neuropeptide re-clustering, a dedicated res-8.0 cluster, and an
explicit literature citation.

## Markers

- Gr43a is among the top Table S3 markers of the shared parent res-2.0
  cluster 46 ("Peptidergic"), alongside Hug, Proc, Crz, ITP — consistent
  with the co-expression of Gr43a and Crz reported by Miyamoto and Amrein.

## Location

- Internal fructose-sensing Gr43a neurons are located in the brain near
  the pars intercerebralis / corpus cardiaca-adjacent region (per Miyamoto
  and Amrein, 2014); not independently re-derived here.

## Function

- Hemolymph fructose sensing; regulates internal nutrient-state signalling
  and downstream feeding-related insulin/corazonin release.

## Label provenance

No REVIEW flag. GEO label "Gr43a" (res2_ambiguous is null/monotypic, i.e.
these 79 cells were consistently drawn from cluster 46) matches Table S2's
independent res-8.0 annotation "Gr43a neurons" (cluster 129; Miyamoto and
Amrein, 2014) — a genuine convergent identification, not just a
neuropeptide re-clustering artifact.

## Mapping notes

This is the strongest case among the neuropeptide clusters for a KNOWN,
anatomically and functionally defined cell type: internal fructose-sensing
Gr43a(+Crz) neurons of Miyamoto and Amrein (2014). Expect a specific FBbt
term (or a clear candidate for a new one) at the single-type level, high
confidence, well supported by an independent higher-resolution cluster and
an explicit paper citation.
