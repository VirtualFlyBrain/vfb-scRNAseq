# Hsp

*Cluster `Hsp` (Seurat res-2.0 cluster 23; 668 cells; ages 0-9 days only,
notably absent at 15/30/50 days) in Davie et al. 2018 (GSE107451, 57K adult
brain). Table S2 lists this cluster as "Unannotated"; the paper singles it
out as the sole cluster failing its reproducibility checks.*

## Summary

Cluster 23 is not given a cell-type annotation by the authors (Table S2:
"Unannotated"). The paper states: "all clusters except one (cluster 23) show
high reproducibility between male and female brains, between genetic
backgrounds, across ages, and between technical replicates" — i.e. this is
explicitly flagged as the outlier cluster in the paper's own QC, not merely
an unidentified cell type. Its marker signature (see below) is dominated by
heat-shock/chaperone and stress-response genes rather than by any
neuroanatomical identity, and it is absent from the older timepoints (15,
30, 50 days) in the supplied timepoint data, unlike the other clusters
reviewed here, which are consistently detected across all eight timepoints.

## Markers

- Table S3 top markers: Hug, CG11413, Obp44a, Irk2, CG14989, retinin,
  **Hsp23, Hsp26**, Gapdh1, eIF2Bbeta, **DnaJ-1**, Nplp3, CG9512, **Hsp83**,
  nSyb, **Hr38**, Gad1, **Hsp68**, alphagamma-element:CR32865, Vha13.
- Four of the top ~20 markers are classical inducible heat-shock/chaperone
  genes (Hsp23, Hsp26, Hsp68, Hsp83) plus the co-chaperone DnaJ-1; Hr38 is a
  well-established immediate-early/stress-response gene in Drosophila
  (Nr4a-family), induced non-specifically by cellular stress including
  dissociation. This combination is a recognised signature of dissociation-
  and/or heat/mechanical-stress-induced transcription in single-cell/nucleus
  protocols, not of a defined neuronal identity.
- The remaining markers are a heterogeneous mix (nSyb = pan-neuronal marker;
  Gad1 = GABAergic marker; Hug = hugin neuropeptide, normally restricted to a
  small subesophageal population; retinin = normally a retina/cone-cell gene,
  unexpected in dissected, retina-depleted brain tissue) that do not cohere
  into a single anatomical cell type. This mixed, "borrowed-marker" pattern is
  consistent with a cluster formed by pooling stressed cells drawn from
  multiple underlying true cell types, rather than one real population.
- Summary expression computed from the GEO matrix in this repo
  (`projects/davie_2018/expression.tsv`; CPM mean over expressing cells =
  "level", fraction of the 668 cluster cells expressing = "extent") confirms
  the heat-shock/chaperone signature is not restricted to a handful of top
  markers but is broadly and almost uniformly expressed across the cluster:
  Hsp83 extent 0.98, Hsp26 extent 0.93 (level ~3,904 CPM), DnaJ-1 extent 0.91,
  Hsp23 extent 0.85, stv extent 0.85, Hsp60A extent 0.80, Hsp70Bc extent 0.76,
  Hsp68 extent 0.69, Hsp27 extent 0.60, Hsp67Bc extent 0.50 — i.e. most of the
  cluster's cells co-express most of the chaperone family, not just a
  subpopulation. Notably the constitutively-expressed Hsp70Aa/Ab paralogs are
  much lower (extent ~0.26), consistent with an induced heat-shock/stress
  response rather than baseline chaperone expression.
- By this same expression computation, the highest-level genes overall are
  pan-neuronal/housekeeping (noe, Cam, Hsromega extent 0.9985, nrv3, cpx,
  nSyb extent 0.99, Sap47, several mitochondrial transcripts) plus pros
  (extent 0.91); elav extent 0.78 — confirming the cluster is broadly neuronal
  (and, via pros, includes an unusual mix with some neuroblast/progenitor-
  associated expression) rather than defined by any single lineage marker.
- Pdf (the clock-neuron neuropeptide gene, normally a tight marker of the
  ~16 LNv clock neurons) is detected in 40% of Hsp-cluster cells (level ~521
  CPM) — roughly 650-fold lower level than in the genuine LNv cluster (extent
  0.85, level ~340,000 CPM). Stated neutrally, this is consistent with
  low-level ambient/contaminating Pdf transcript rather than this cluster
  containing bona fide Pdf-expressing (LNv) neurons, and reinforces the
  picture of a heterogeneous, cross-contaminated/stressed cell population
  rather than a coherent cell type.

## Location

- Not resolved. No neuropil or cell-body location is reported or inferable
  from the marker set; the cluster does not correspond to a described
  anatomical location in the paper.

## Function

- Not resolved as a cell-type function. The marker profile (heat-shock
  proteins, chaperones, immediate-early gene) is consistent with a cellular
  stress-response state rather than any characteristic neuronal or glial
  function.

## Label provenance

Table S2 res-2.0 cluster 23 is listed as "Unannotated" with no method or
references. The GEO-supplied label "Hsp" is a post-hoc, marker-derived name
(after the heat-shock protein genes in its top markers) that does not appear
in Table S2 itself; label_validation.tsv flags this row REVIEW ("named in
GEO; S2 res-2.0 Unannotated"). This is a genuine discrepancy: the label
implies an identity the authors themselves declined to assign.

## Mapping notes

This cluster is best treated as a cell STATE / technical artifact grouping,
not a cell type, and should very likely NOT be mapped to any FBbt anatomical
class. Evidence: (1) the authors explicitly identify cluster 23 as the one
exception to otherwise high cross-condition reproducibility (sex, genetic
background, age, replicate) — the behaviour expected of a
batch/dissociation-stress-driven cluster rather than a true, robustly
recurring cell population; (2) its top markers are dominated by canonical
heat-shock/chaperone genes (Hsp23/26/68/83, DnaJ-1) and a stress-inducible
immediate-early gene (Hr38), a signature widely documented as an artifact of
tissue dissociation in single-cell transcriptomics rather than a defining
feature of any known Drosophila cell type; (3) the paper leaves it
"Unannotated" despite comprehensively naming all other clusters, and it is
missing at the older timepoints supplied here, unlike genuine cell-type
clusters; (4) its other markers span unrelated, non-overlapping identities
(neuropeptidergic, GABAergic, retinal), suggesting cells recruited from
multiple true types under a shared stress response rather than a coherent
population; (5) expression-level computation from the GEO matrix shows the
heat-shock/chaperone response is near-uniform across the cluster (extent
0.5-0.98 for eight distinct Hsp/DnaJ genes), i.e. a shared induced state
rather than a marker of a subset of "Hsp-type" cells, while the elevated but
constitutive Hsp70Aa/Ab paralogs are comparatively low (extent ~0.26),
consistent with an induced stress response over a baseline one; and (6) the
low-level, low-extent detection of the LNv-specific neuropeptide Pdf (~650x
lower level than in the true LNv cluster) points to ambient/cross-cell
contamination rather than a real co-identity, again arguing this is a
pooled, stressed population rather than a single cell type. Taken together,
the balance of evidence is that "Hsp" is a cell STATE (an induced
heat-shock/stress-response signature, most plausibly reflecting variable
dissociation stress prior to droplet capture) superimposed on cells drawn
from multiple underlying true types, not a discrete anatomical cell type. If
a mapping step is attempted at all, the honest annotation is "unresolved /
technical (dissociation-stress) cluster, not a cell type" — not an FBbt
term.
