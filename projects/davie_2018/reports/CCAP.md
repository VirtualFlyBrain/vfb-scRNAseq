# CCAP

*Cluster `CCAP` (Seurat res-2.0 cluster 5; 9 cells; ages 1, 3, 6, 30 days) in
Davie et al. 2018 (GSE107451, 57K adult brain). A small population of
crustacean-cardioactive-peptide-expressing neurons recovered from the
neuropeptide re-clustering.*

## Summary

CCAP neurons are a small, molecularly and functionally well-defined
neuropeptidergic population that express crustacean cardioactive peptide
(CCAP), classically studied via the CCAP-GAL4 driver (Luan et al., 2006) and
implicated in ecdysis behaviour, cardiac modulation and (with co-released
bursicon) post-eclosion wing expansion. In this atlas the 9 CCAP cells were
recovered specifically by the authors' targeted re-clustering of the 1,269
cells with >=100 UMIs for any neuropeptide-encoding gene (Figure 2K), and are
independently confirmed at Seurat resolution 8.0 as cluster 151, annotated
"CCAP" using the same literature marker/reference.

## Markers

- Defining marker: CCAP (peptide-hormone gene), per Luan et al. (2006).
- The listed Table S3 markers (Imp, mamo, futsch, mbl, Msp300, Rbp9, hth,
  chic, Gpb5, etc.) belong to parent res-2.0 cluster 5, a large heterogeneous
  neuronal cluster (several temporal-identity TFs present) — not specific to
  the CCAP subcluster.

## Location

- CCAP neurons in the adult CNS include a mix of central-brain/subesophageal
  and ventral-nerve-cord neurons; the brain-restricted subset captured here
  is consistent with brain-resident CCAP-expressing interneurons/efferents.

## Function

- Ecdysis behaviour, cardiac and abdominal muscle modulation, and (with
  bursicon) wing-expansion/cuticle-tanning after eclosion.

## Label provenance

No REVIEW flag. GEO label "CCAP" comes from the S2 neuropeptide re-clustering
(cells drawn from multiple res-2.0 clusters, majority from 5); independently,
S2 also annotates res-8.0 cluster 151 as "CCAP" (Luan et al., 2006),
corroborating the identity from a second, higher-resolution clustering.

## Mapping notes

CCAP-expressing neurons are a recognised, named anatomical/functional class
(not a single morphological "type" — the CCAP-GAL4 pattern includes several
distinct neuron subsets), so an FBbt term for "CCAP neuron" at the class
level is the expected honest granularity. Do not expect finer resolution
(e.g. specific individual CCAP interneuron subtypes) from this cluster; the
9-cell size and small, corroborating res-8.0 cluster support a genuine,
if rare, population rather than an artifact.
