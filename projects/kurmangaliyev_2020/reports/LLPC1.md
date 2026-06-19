# LLPC1

*Cell-type report for cluster `LLPC1` (type LLPC1, class N -- neuron)
in Kurmangaliyev et al. 2020, Drosophila visual system developmental atlas
(GSE156455, DOI 10.1016/j.neuron.2020.10.006). Evidence from established
optic-lobe anatomy (Isaacson 2019; Davis et al. 2020; Nern et al. 2025;
Dorkenwald et al. 2024; Schlegel et al. 2024).*

## Summary

LLPC1 is a lobula-lobula plate columnar neuron of the adult Drosophila optic
lobe. It is one of the LLPC family (LLPC1, LLPC2, LLPC3), which are columnar
interneurons that connect the lobula and the lobula plate. LLPC1 receives
input from approximately 5-10 columns of lobula layer 4 and approximately 10
columns of lobula plate layer 1, with additional postsynapses in lobula plate
layers 2-3. It projects ipsilaterally, sending output to the posterior lateral
protocerebrum. LLPC1 is cholinergic and is highly sensitive to front-to-back
motion on the ipsilateral eye. Approximately 100-120 LLPC1 cells are present
per hemisphere.

## Markers

- Cluster label is the canonical anatomical name; no driver-based alias is
  used in this atlas.
- Neurotransmitter: **cholinergic** (vesicular acetylcholine transporter
  pathway; confirmed by Davis et al. 2020).
- Directional motion tuning (front-to-back) distinguishes LLPC1 from its
  siblings LLPC2 and LLPC3.

## Location

- **Soma / cell class:** columnar neuron of the optic lobe (class N).
- **Dendrites (input):** lobula layer 4 (5-10 columns); lobula plate layers
  1-3 (approximately 10 columns in layer 1, additional in layers 2-3).
- **Axon terminals (output):** posterior lateral protocerebrum (ipsilateral).
- Remains strictly ipsilateral; no contralateral projections.

## Function

- LLPC1 is a visual motion processing interneuron integrating lobula and
  lobula plate signals.
- It is highly sensitive to **front-to-back** optic-flow motion on the
  ipsilateral eye (Isaacson 2019).
- Together with LLPC2 and LLPC3 it constitutes the LLPC class of lobula
  complex columnar neurons connecting lobula to lobula plate.

## Mapping notes

- FBbt:00058227 "lobula-lobula plate columnar neuron LLPC1" is a named,
  well-defined term matching this cluster exactly by name and by all
  anatomical features (connectivity, neurotransmitter, motion tuning).
- Expect `skos:exactMatch` with high confidence; no additional verification
  or new term request is needed.
