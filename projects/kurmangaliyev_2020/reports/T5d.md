# T5d

*Cluster `T5d` (subtype; parent type `T4.T5`, class N) in Kurmangaliyev et al.
2020 (GSE156455). Dataset facts from the atlas paper; directional/layer identity
is established optic-lobe anatomy.*

## Summary

T5d is one of the four subtypes (a-d) of T5 neurons, the OFF-motion
direction-selective columnar neurons of the Drosophila optic lobe. T5 (OFF) and
T4 (ON) are transcriptomically closely related and form a single combined `type`
(`T4.T5`) here, resolving into eight directional subtypes (T4a-d, T5a-d). Each T5
subtype projects to one of the four lobula plate layers and is tuned to one
cardinal direction; **T5d corresponds to lobula plate layer d (layer 4) and is
tuned to downward motion**.

## Markers

- T5 shares most transcriptomic markers with T4; the atlas distinguishes the
  directional subtypes within the combined T4/T5 population.
- Subtype identity (a-d) is defined by lobula-plate layer targeting and direction
  tuning rather than a single unique transcriptomic marker.

## Location

- **Cell class:** columnar neuron of the optic lobe (class N).
- **Dendrites:** lobula layer 1 (Lo1) -- distinguishing T5 from T4, whose
  dendrites are in medulla M9/M10.
- **Axon terminals:** lobula plate layer d (layer 4).

## Function

- First-order OFF-pathway direction-selective motion-detecting neuron; T5d encodes
  downward motion, read out in lobula plate layer 4.

## Mapping notes

- Expect an exact FBbt match: FBbt has T5 neuron subtypes by lobula-plate layer.
  T5d should map to "T5d neuron" (lobula plate layer 4, downward motion); broad-
  match to "T5 neuron" only if the layer-specific subtype is absent.
- Unlike T5a and T5b, FBbt does not further divide T5d into sub-subtypes
  (no T5di/T5dii), so FBbt:00003740 is the most specific available term.
