# Photoreceptors

*Cluster `Photoreceptors` (Seurat res-2.0 cluster 53; 277 cells; ages 0-50
days) in Davie et al. 2018 (GSE107451, 57K adult brain). Identified directly
by phototransduction markers, in a dataset where the retina itself was
removed at dissection.*

## Summary

The paper identifies this cluster directly as photoreceptors using the
phototransduction genes ninaC, trp and trpl (main text: "We also
distinguished photoreceptors (ninaC, trp, and trpl)"; Bernardo-Garcia et al.,
2016; Goto et al., 2003; Montell and Rubin, 1988). Because this atlas is
built from dissected adult brains with the retina (compound-eye
photoreceptor somata) removed, these 277 cells cannot represent the bulk
retinal R1-R8 population; they most plausibly represent extraretinal
photoreceptor types whose cell bodies remain with the brain after
dissection — candidates include the ocelli (simple eyes on the dorsal head,
if not fully excluded by the dissection) and the Hofbauer-Buchner (H-B)
eyelet, an extraretinal photoreceptor associated with the optic stalk/
accessory medulla. Axon terminals of retinal photoreceptors are not cells
and cannot by themselves populate a single-cell cluster, though some
transcript contamination from retained R1-R8 axon terminals in the lamina/
medulla cannot be ruled out.

## Markers

- Table S3 top markers: Arr2, Arr1, ninaE, rtp, Gbeta76C, ninaC, CG34134,
  trp, Galphaq, Cpn, inaC, inaD, ninaA, Rh2, chp, SmydA-8, trpl, CG9780,
  Culd, CG7220 — a generic phototransduction-cascade signature (arrestins,
  rhodopsin pathway components, TRP channels).
- Notably this list mixes ninaE (Rh1, the outer-photoreceptor R1-R6
  rhodopsin) with Rh2 (the ocellar-specific rhodopsin) — genes that mark
  different photoreceptor populations in an intact fly. Their co-occurrence
  here is consistent with either a mixed/generic phototransduction
  signature not resolved to a single photoreceptor subtype, or low-level
  contamination alongside a genuine extraretinal (ocellar/H-B eyelet)
  population.

## Location

- If ocellar: cell bodies in the ocelli (dorsal head cuticle), which may be
  retained with the brain depending on the precision of dissection.
- If Hofbauer-Buchner eyelet: cell bodies near the optic stalk/base of the
  lamina, projecting to the accessory medulla — an extraretinal
  photoreceptor type expected to survive retina removal.
- The paper does not specify which of these (or a mixture) the cluster
  represents.

## Function

- Phototransduction (light detection); role depends on identity — ocelli
  contribute to horizon/flight stabilisation, the H-B eyelet contributes to
  circadian photoentrainment via the accessory medulla clock circuit.

## Label provenance

Table S2 res-2.0 cluster 53 is annotated "Photoreceptors" (method: literature
markers/mapping; refs: Bernardo-Garcia et al., 2016; Montell and Rubin,
1988; Tan et al., 2015). label_validation.tsv records the GEO label as an
exact match, no REVIEW flag. Neither the paper nor Table S2 distinguishes a
photoreceptor subtype or notes the retina-removal caveat explicitly.

## Mapping notes

This is likely a possible-state-or-mixed-identity case rather than a single
clean cell type: the generic "Photoreceptors" label and its mixed Rh1/Rh2
marker signature do not resolve which extraretinal photoreceptor population
(ocellar, H-B eyelet) is present, or whether the cluster is a pool of more
than one. Given the retina was removed at dissection, do not map this
directly to a generic "photoreceptor cell" term implying retinal R1-R8;
instead flag for the mapping step to consider extraretinal-specific FBbt
terms (e.g. ocellar photoreceptor, Hofbauer-Buchner eyelet neuron) and treat
single-type resolution as low confidence.
