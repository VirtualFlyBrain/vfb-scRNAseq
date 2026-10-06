# dorsal_Fan-shaped_Body

*Cluster `dorsal_Fan-shaped_Body` (Seurat res-2.0 cluster 61; 232 cells; ages
0-50 days) in Davie et al. 2018 (GSE107451, 57K adult brain). Dorsal
fan-shaped body neurons ("dFB"), identified by FAC-sorting a Gal4 driver
line specifically for this study.*

## Summary

The dFB annotation comes from a dedicated validation experiment: the authors
used R23E10-Gal4 to genetically label and FAC-sort a small population of
~9-18 neurons per hemisphere that innervate the dorsal fan-shaped body (a
subset of dFB neurons), profiled them by CEL-Seq2 and two SMART-Seq2
protocols, and used a regression model to show they map onto whole-brain
Seurat cluster 61 as the single best match. R23E10-Gal4 is a well-known
driver line that labels the sleep-homeostat dorsal fan-shaped body neurons
studied extensively in the fly sleep literature (e.g. Donlea et al.; Liu et
al.), where their activity promotes sleep.

## Markers

- Immunofluorescence found ~18 R23E10-Gal4+ neurons, but whole-brain cluster
  61 contains 232 cells — i.e. the cluster is substantially larger than the
  R23E10-labelled population.
- When the authors subclustered cluster 61 into 7 subclusters, only one
  subcluster specifically matched (66% overlap) the R23E10-Gal4 FAC-sorted
  cells; the other 6 subclusters likely represent other dFB neuron types not
  labelled by this driver.
- Table S3 top markers for res-2.0 cluster 61 (the whole, unsplit cluster)
  include VGlut, CG11294, svp, msi, CG15478, CG10804, Rh7, tup, Nplp1, SoxN,
  Fife, Hmx, bi, Octbeta1R — VGlut indicates a glutamatergic identity for
  (at least part of) the cluster; tup, Hmx, svp and SoxN are transcription
  factors consistent with a specific central-complex-associated neuron
  identity.
- This cluster shows unusually high OxPhos (oxidative phosphorylation) gene
  expression and, in the R23E10-Gal4-marked cells specifically, significantly
  higher mitochondrial turnover (mitoTimer assay) than KCs, PDF neurons or
  OPNs — a distinguishing physiological feature of these neurons in this
  paper, though not necessarily a marker for the whole cluster.

## Location

- **Neuropil:** dorsal layer of the fan-shaped body (central complex).
- **Cell body:** cortex adjacent to the central complex.
- **Cell class:** central-complex neuron, class N; at least the R23E10-Gal4
  subset is glutamatergic.

## Function

- The R23E10-Gal4-labelled dFB neurons are established sleep-promoting
  neurons of the central complex (part of the classical sleep-homeostat
  circuit); their broader activity increases sleep drive/depth. The rest of
  cluster 61 likely comprises other, non-R23E10, dorsal fan-shaped body
  neuron types whose specific functions are not resolved here.

## Label provenance

Table S2 res-2.0 cluster 61 is annotated "dFB" with references "data
generated in this study" (the FAC-sort/regression-mapping experiment
described above), reflecting that this is a first-party identification
rather than a literature mapping. The GEO label "dorsal_Fan-shaped_Body" is a
curated expansion/synonym of "dFB" (label_validation.tsv: match, curated
synonym). No REVIEW flag.

## Mapping notes

This cluster is a merged/remainder group at the level of "dorsal fan-shaped
body neuron" in general, not a single cell type: only one of seven
subclusters specifically corresponds to the R23E10-Gal4-marked population
(the well-characterised sleep-promoting dFB neurons), while the remaining
~166 cells (the other six subclusters) represent additional, unidentified
dFB neuron type(s) not resolved by name in this paper. A mapping to a broad
"dorsal fan-shaped body neuron" grouping term is the honest level for the
whole cluster; a more specific term for the sleep-promoting R23E10-Gal4
subtype could be justified only for a hypothetical finer subcluster, not for
cluster 61 as a whole.
