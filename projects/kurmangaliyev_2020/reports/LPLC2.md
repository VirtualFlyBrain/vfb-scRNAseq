# LPLC2

*Cell-type report for cluster `LPLC2` (type LPLC2, class N -- neuron)
in Kurmangaliyev et al. 2020, Drosophila visual system developmental atlas
(GSE156455, DOI 10.1016/j.neuron.2020.10.006). Evidence from the atlas paper
local index and established optic-lobe anatomy (Wu et al., 2016;
Klapoetke et al., 2017).*

## Summary

LPLC2 is a lobula plate-lobula columnar (LPLC) projection neuron of the adult
Drosophila optic lobe. Its cell body resides in the dorsal area of the lateral
cell body rind. Dendrites arborise across all four layers of the lobula plate
with a distinct arbor in each layer extending outward from the main fibre in the
direction of motion detection for that layer; this geometry confers sensitivity to
looming (expanding) stimuli. In the lobula the main dendritic arbors occupy layers
4 and 5B, with minor processes in layer 5A, and presynaptic sites in layer 4.
Each LPLC2 cell spans approximately 25 lobula optic columns, overlapping
extensively with neighbouring LPLC2 cells. The axon projects to a dedicated optic
glomerulus in the posterior ventrolateral protocerebrum (PVLP), positioned
anterior to the LPLC1 glomerulus and dorsal to the LC4 glomerulus. Activation of
LPLC2 elicits a jump escape response. LPLC2 is cholinergic, with approximately
80 cells per optic lobe. In the Kurmangaliyev 2020 atlas LPLC2 is identified as a
distinct transcriptomic cluster among the unicolumnar and wide-field columnar
neuron types of the optic lobe.

## Markers

- Cholinergic identity confirmed by scRNAseq detection of *ChAT* and *VAChT*
  expression (Davis et al., 2020, referenced in FBbt definition).
- No single unique driver marker is cited for this cluster in the atlas paper;
  the cluster identity is established by correlation of transcriptomic profile
  with known LPLC2 morphological and functional signatures.
- Key functional marker: sensitivity to looming stimuli (expanding-field
  motion), mediated by the layer-by-layer dendritic geometry in the lobula plate.

## Location

- **Soma:** dorsal lateral cell body rind.
- **Dendrites (input):** all four layers of the lobula plate (each layer arbor
  oriented along the preferred-motion axis of that layer); lobula layers 4 and 5B
  (primary), 5A (minor).
- **Axon terminals (output):** LPLC2 optic glomerulus in the PVLP, anterior to
  LPLC1 and dorsal to LC4; no retinotopic organisation within the glomerulus.

## Function

LPLC2 is a visual projection neuron specialised for the detection of looming
(approaching-object) stimuli. Its multi-layer dendritic geometry in the lobula
plate integrates motion-direction signals across layers, making it selective for
radial expansion rather than translational motion. Activation triggers a jump
escape response, making LPLC2 a key node in the visual threat-detection circuit;
it provides input to the giant fibre pathway.

## Mapping notes

FBbt contains a directly named term "lobula plate-lobula columnar neuron LPLC2"
(FBbt:00111763) whose definition matches this cluster in every dimension:
lobula plate and lobula dendritic targets, cholinergic identity, loom detection,
escape behaviour, and optic glomerulus in the PVLP. An exact match is expected.
