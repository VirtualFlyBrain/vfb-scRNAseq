# Tm5c

*Cluster `Tm5c` (subtype == type `Tm5c`, class N) in Kurmangaliyev et al. 2020
(GSE156455). One of the medulla transmedullary neuron subtypes profiled in the
adult optic lobe atlas. Tm5 has three established subtypes (Tm5a, Tm5b, Tm5c);
anatomy of Tm5c is well characterised by connectome and genetic studies.*

## Summary

Tm5c is a wide-field transmedullary columnar neuron of the adult optic lobe.
Its dendritic arbors span approximately eight medulla columns with lateral
branches in medulla layers M1, M3, and M6 emanating from a single vertical
dendrite. It preferentially receives synaptic input from R8 photoreceptor cells
(rather than R7), with a strong bias toward yellow (rather than pale) ommatidia;
R8 input is concentrated in layer M3. It also receives input from the distal
medullary amacrine neuron Dm8 in layer M6. Its axon crosses the second optic
chiasma and terminates near the boundary between lobula layers 5 and 6, with
some cells bearing an additional branch in layer 4. Tm5c provides presynaptic
output to the lobula intrinsic neuron Li4. It is a glutamatergic neuron.

## Markers

- Identity as Tm5c subtype (vs Tm5a/Tm5b) established by connectome data:
  preferential R8 input (yellow ommatidia) distinguishes it from Tm5a (R7,
  yellow) and Tm5b (R7, pale) (Karuppudurai et al., 2014; Kind et al., 2021).
- Glutamatergic identity confirmed by vGlut (OK371-GAL4) driver labelling,
  RT-PCR, and immunohistochemistry (Gao et al., 2008; Karuppudurai et al., 2014).
- Connectivity with R8 verified by GRASP experiments and EM reconstruction
  (Karuppudurai et al., 2014; Lin et al., 2016; Kind et al., 2021).

## Location

- **Cell class:** wide-field transmedullary (Tm) columnar neuron; class N
  (neuron) in the atlas; Notch OFF hemilineage secondary neuron.
- **Dendrites:** medulla layers M1, M3, M6 (primary R8 input zone M3; Dm8
  input in M6); arbor spans approximately 8 medulla columns.
- **Axon terminal:** lobula, near the boundary of layers 5 and 6 (occasional
  branch in layer 4).
- **Organisation:** columnar; one Tm5c cell per optic column.

## Function

- Glutamatergic; relays chromatic (R8-dominant, yellow-ommatidium-biased)
  visual information from the medulla to the lobula.
- Receives R8 photoreceptor and Dm8 amacrine input; outputs to lobula intrinsic
  neuron Li4.
- Part of the colour-processing pathway in the optic lobe; contributes to
  spectral preference behaviour.

## Mapping notes

- Expect a direct exact FBbt term for "transmedullary neuron Tm5c".
- FBbt also contains "immature transmedullary neuron Tm5c" (FBbt:00052332) and
  the parent "transmedullary neuron Tm5" (FBbt:00003793); neither is the correct
  match for adult cells in this scRNAseq atlas.
