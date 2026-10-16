# PR

*Cluster `PR` (author class 3, one cluster per stage in the supervised annotation; cells per stage: P15 44, P30 135, P40 116, P50 69, P70 228, adult 92; stages P15, P30, P40, P50, P70, adult) in Ozel et al. 2021 (GEO GSE142787). Female Canton-S optic lobe scRNAseq, pupal time given as % pupal development at 25 C.*

## Summary
Photoreceptor cluster; the authors state it contains photoreceptor cells R1 to R8 (PR = photoreceptors in this paper).

## Markers
Not given as specific genes; clear match to the photoreceptor transcriptome (Extended Data Fig. 3). The paper notes Wnt4-Gal4 is restricted to ventral R7/R8 in pupae but not in adult, but this is not a cluster marker.

## Location
Retina; axons project to lamina (R1-R6) and medulla (R7, R8). This projection pattern is general fly neuroanatomy and is not taken from the table.

## Function
Light-detecting cells of the compound eye.

## Label provenance
Label assigned by the authors. The table states the adult cluster was impure and that non-photoreceptor cells were removed using the P70 classifier; at P30 and P15 only a fraction of class cells (83% and 58%) were kept as a single unsupervised cluster, so counts are for the retained cells. Source: Supplementary Table 1, row 3. Adult annotation comment: "Clear match to photoreceptors trancriptome (Extended data Fig.3). Contains photoreceptor cells R1 to R8. The adult cluster was impure, but non-photoreceptor cells were later discarded (see pupal stages annotation + Methods)." Pupal annotation comment: "The unsupervised adult cluster 3 was impure: consequently, our NN classifier assigned the class 3 to P70 unsupervised cluster 49 and to low quality P70 cells. Thus, at P70 we kept only the cells from the unsupervised cluster 49 as photoreceptors, and removed non-photoreceptors cells from adult cluster 3 by applying the P70 NN classifier to the adult stage. P30: we kept only the 83% of class 3 cells belonging to a single unsupervised cluster. P15: we kept only the 58% of class 3 cells belonging to a single unsupervised cluster."

## Mapping notes
A single mixed cluster of photoreceptor cell subtypes (R1-R8, not separated); the authors flag impurity in the original adult cluster. Mixed-subtype grouped call; the cells are retina photoreceptors, not optic-lobe neurons. Note that photoreceptors were excluded from some downstream marker analyses in the paper. P15, P30 and P40 cells are developing (immature) neurons, still wiring; P50 and P70 are pharate-adult stages (P70 = late pupa) and the adult sample is 1-3-day-old adult. The authors report that neuronal transcriptomes converge on those of older cells of the same type within ~15 h of birth, so type identity is already recognisable at P15.
