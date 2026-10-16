# T4-5a/b

*Cluster `T4-5a/b` (author class 234, one cluster per stage in the supervised annotation; cells per stage: P15 1219, P30 1739, P40 1101, P50 1261, P70 1657, adult 5422; stages P15, P30, P40, P50, P70, adult) in Ozel et al. 2021 (GEO GSE142787). Female Canton-S optic lobe scRNAseq, pupal time given as % pupal development at 25 C.*

## Summary
Combined T4/T5 subtypes a and b (T4a, T4b, T5a, T5b), directionally selective motion-detecting neurons.

## Markers
The paper reports three axes of division across T4/T5 subtypes: T4 vs T5 (TfAP-2), a/b vs c/d (bi), and b/c vs a/d (grn). Subtype markers are not retained in adults, and T4-5 subtypes are transcriptionally indistinguishable in adult. Genes used for subclustering included klg, bi, lea, Con, TfAP-2, grn, dpr10.

## Location
T4 dendrites in the medulla (layer M10) and T5 in the lobula (Lo1), with axons to the lobula plate layers. The authors state the polarised dendritic arbors mirror direction selectivity (their refs 6, 42). Layer details are general knowledge.

## Function
Each of four subtypes (a/b/c/d) processes motion in one of four cardinal directions (paper, ref 41).

## Label provenance
The authors' unsupervised clustering resolved the eight T4/T5 subtypes only at P50 (a separate P50 clustering splits this class into T4a, T4b, T5a, T5b); the a/b vs c/d division was projected to all other stages by supervised subclustering (ICA). The table: "Subdivision projected from P50 to all stages." Source: Supplementary Table 1, row 234. Adult annotation comment: "Subdivision projected from P50 to all stages (main text, Methods). The OOBE between class 234 and 235 is 7% in adults." Pupal annotation comment: "Subdivision projected from P50 to all stages (main text, Methods)."

## Mapping notes
Grouped call: a/b group spanning four types (T4a, T4b, T5a, T5b) with a common parent (T4/T5 neurons). Not a single type. At P50 only, the finer T4a/T4b/T5a/T5b clusters exist in a separate clustering. P15, P30 and P40 cells are developing (immature) neurons, still wiring; P50 and P70 are pharate-adult stages (P70 = late pupa) and the adult sample is 1-3-day-old adult. The authors report that neuronal transcriptomes converge on those of older cells of the same type within ~15 h of birth, so type identity is already recognisable at P15.
