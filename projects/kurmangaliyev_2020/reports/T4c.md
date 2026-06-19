# T4c

*Cell-type report for cluster `T4c` (subtype; parent type `T4.T5`, class N -- neuron)
in Kurmangaliyev et al. 2020, Drosophila visual system developmental atlas
(GSE156455, DOI 10.1016/j.neuron.2020.10.006). Evidence from established
optic-lobe anatomy; directional/layer identity is well-established in the
literature (Fischbach and Dittrich, 1989; Maisak et al., 2013; Henning et al., 2022).
NOTE: the GEO README documents that T4c/T4d labels were previously swapped and
have been corrected; the label T4c as used here refers to the layer-3, upward-motion
subtype.*

## Summary

T4c is one of the four subtypes (a-d) of T4 neurons, the ON-motion
direction-selective columnar neurons of the *Drosophila* optic lobe. T4 (ON) and
T5 (OFF) neurons are transcriptomically closely related -- in this atlas they
form a single combined `type` (`T4.T5`) that resolves into eight directional
subtypes (T4a-d, T5a-d). Each of the four subtypes projects to one of the four
layers of the lobula plate and is tuned to one of the four cardinal directions of
visual motion; **T4c corresponds to lobula plate layer c (layer 3) and responds
to upward motion**.

## Markers

- T4 and T5 share most transcriptomic markers; the atlas distinguishes directional
  subtypes within the combined T4/T5 population primarily by lobula-plate layer
  targeting.
- The paper validates T4/T5 subtypes using transgenic driver lines and regional
  spatial markers restricted to specific lobula plate layers.
- Directional subtype identity (a-d) is defined by lobula-plate layer targeting
  and direction tuning, not by a single unique transcriptomic marker.
- T4 neurons are cholinergic (Mauss et al., 2014; Shinomiya et al., 2014).

## Location

- **Soma / cell class:** columnar neuron of the optic lobe (class N).
- **Dendrites:** medulla layer M10.
- **Axon terminals:** lobula plate -- T4c terminates in **lobula plate layer c (layer 3)**.

## Function

- T4 neurons are first-order **ON-pathway, direction-selective** motion-detecting
  neurons. The four subtypes encode the four cardinal directions of visual motion,
  one per lobula-plate layer.
- **T4c encodes upward motion** (Henning et al., 2022), read out in lobula plate
  layer 3.
- T4c and T5c neurons together provide input to lobula plate intrinsic neurons
  (e.g. LPi3-4) and lobula plate columnar neurons (e.g. LPC2) that arborise in
  layer 3.

## Mapping notes

- FBbt contains an exact term for this subtype: FBbt:00003734 "T4c neuron",
  defined as "T4 neuron with its lobula plate arbor in layer 3 (Fischbach and
  Dittrich, 1989). It responds to motion in an upwards direction (Henning et al.,
  2022)." The label, layer identity, and directional tuning match the cluster
  exactly.
- Parent term: T4 neuron (FBbt:00003731).
- FBbt also contains an "immature T4c neuron" (FBbt:00052265) for the
  developmental precursor, which is not appropriate for an adult scRNAseq cluster.
