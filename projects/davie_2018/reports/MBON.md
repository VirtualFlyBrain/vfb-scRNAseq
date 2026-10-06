# MBON

*Cluster `MBON` (Seurat res-2.0 cluster 57; 257 cells; ages 0-50 days) in
Davie et al. 2018 (GSE107451, 57K adult brain). Mushroom body output
neurons.*

## Summary

Mushroom body output neurons (MBONs) are the ~34 morphologically and
physiologically distinct cell types (Aso et al., 2014) that read out Kenyon
cell activity from the mushroom body lobes and convey it to downstream
circuits controlling learned approach/avoidance behaviour. The paper
annotates this cluster generically as "MBON" (elsewhere in the text also
called "MB output neurons") by mapping to a previously published MBON
transcriptome rather than by identifying an individual named MBON.

## Markers

- Table S3 top markers for res-2.0 cluster 57 include Yp1, Yp2, Yp3, CG6503,
  CG34166, Nplp2, Sxl, orb2, Rbp9, Rbp1-like, hdc, mbt, side, rut. orb2 and
  rut are notable memory/plasticity genes consistent with a downstream
  learning-circuit neuron; side (sidestep, an Ig-superfamily axon-guidance
  gene) fits a wiring-specific interneuron identity.
- The Yp1/Yp2/Yp3 (yolk protein / vitellogenin-family) genes at the top of
  the marker list are unusual for a defined neuron type and are not discussed
  by the authors in this context; they may reflect a minor
  contamination/ambient-RNA signal in this comparatively small cluster rather
  than a defining feature of MBON identity. Treat with caution.

## Location

- **Neuropil:** mushroom body lobes (dendrites) projecting to a range of
  downstream neuropils depending on MBON identity (e.g. lateral horn,
  superior protocerebrum, crepine) — not resolved to a specific compartment
  by this atlas.
- **Cell body:** cortex surrounding the mushroom body lobes.
- **Cell class:** mushroom body output neuron (extrinsic MB neuron), class N.

## Function

- MBONs read out the valence/identity information encoded by Kenyon cell
  ensembles in specific MB lobe compartments and drive approach or avoidance
  behaviour; as a class they are the principal output stage of the
  associative-memory circuit downstream of dopaminergic-neuron-gated
  plasticity at KC-MBON synapses.

## Label provenance

Table S2 res-2.0 cluster 57 is annotated "MBON" by mapping (to published data,
Crocker et al., 2016); the GEO label matches exactly (label_validation.tsv:
match). No REVIEW flag.

## Mapping notes

There are on the order of 20 MBON cell types with distinct individual
identities (MBON01-MBON34-style nomenclature, Aso et al., 2014), each
innervating a specific MB lobe compartment. This single 257-cell cluster is
not resolved to any individual MBON type — it is a merged group representing
the MBON class in general (identified by mapping/similarity to a bulk MBON
reference, not by compartment-specific markers). The honest mapping level is
therefore the parent "mushroom body output neuron" grouping term, not any
individual named MBON.
