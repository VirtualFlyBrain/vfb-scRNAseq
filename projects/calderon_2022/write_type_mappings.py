#!/usr/bin/env python
"""Calderon et al. 2022: the type-level FBbt mappings (curator 2026-10-18/19).

Types are the authors' annotations (Table S1 for the modelled-window clusters; the
neuronal re-clusterings' annotations without their numbers). The nuclei are embryonic
(0-18 h), so embryonic, embryonic/larval or (for the late embryo, as FBbt's larval CNS
neuron / larval glial cell cover it) larval cell terms; primordium and anlage
annotations to the somatic cell terms of those structures. Curator decisions:

- CNS tissue types: brain / ventral nerve cord to larval CNS neuron, brain / VNC
  primordium and the neuronal "Neural progenitors" to embryonic neuroblast (broad);
- PNS: peripheral nervous system to larval PNS neuron, the PNS / sensory nervous system
  primordia to peripheral sensory precursor cell, sensory nervous system to
  embryonic/larval sensory neuron (broad);
- combined gut types: hindgut / anal pad to somatic cell of embryonic/larval hindgut (the
  anal pad is part of the hindgut in FBbt); foregut / hindgut (/ anal pad) to somatic
  cell of ectoderm (broad);
- Malpighian tubule: embryonic specialized Malpighian tubule cell; the 16-18 h cluster
  embryonic/larval (override_cluster_mappings.py, after expand_type_mappings.py);
- yolk nuclei: yolk nucleus (a cell component, accepted: the data are nuclei);
- late-embryonic neurotransmitter classes: the larval class terms;
- held (no term): "anlage in statu nascendi", "cellular blastoderm / pole cell", "Head
  epid. /muscle", "Undiff.", "Chordotonal glia", "Ventral midline", "spiracle (tracheal
  system)".

Terms and definitions are read from OLS.

Usage:
    uv run python projects/calderon_2022/write_type_mappings.py
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

from vfb_scrnaseq.project_config import label_slug

PROJ = Path(__file__).resolve().parent
OLS = "https://www.ebi.ac.uk/ols4/api/ontologies/fbbt/terms?obo_id="
E, B = "exact match", "broad match"
ECTO = "FBbt:00059305"           # somatic cell of ectoderm
NB = "FBbt:00001332"             # embryonic neuroblast
PSP = "FBbt:00052556"            # peripheral sensory precursor cell
MAPPED = {   # author type: (FBbt id, match, note)
    "amnioserosa": ("FBbt:00059314", E, ""),
    "ectoderm anlage": ("FBbt:00059301", E, ""),
    "ectoderm anlage in statu nascendi": ("FBbt:00059301", E, "The ectoderm anlage as it forms."),
    "ectoderm primordium": (ECTO, E, ""),
    "endoderm primordium": ("FBbt:00059306", E, ""),
    "mesoderm primordium": ("FBbt:00059307", E, ""),
    "trunk mesoderm primordium": ("FBbt:00059310", E, ""),
    "visceral muscle primordium": ("FBbt:00059309", E, "The visceral trunk mesoderm gives rise to the visceral muscles."),
    "visceral muscle": ("FBbt:00005653", E, ""),
    "somatic muscle primordium": ("FBbt:00000463", E, "Embryonic myoblasts form the somatic muscles."),
    "somatic muscle": ("FBbt:00005649", E, ""),
    "muscle": ("FBbt:00005074", B, "The authors do not say somatic or visceral muscle."),
    "epidermis primordium": ("FBbt:00004994", E, "Epidermoblasts are the progenitors of epidermal cells."),
    "epidermis": ("FBbt:00058243", E, ""),
    "midgut primordium": ("FBbt:00059319", E, ""),
    "midgut": ("FBbt:00001886", E, ""),
    "hindgut primordium": ("FBbt:00059318", E, ""),
    "hindgut / anal pad": ("FBbt:00059315", E, "The anal pad is part of the hindgut in FBbt (anal pad -> anus -> rectum "
                                               "-> embryonic/larval hindgut; curator)."),
    "foregut / hindgut / anal pad": (ECTO, B, "Foregut and hindgut (with the anal pad) together: their common, "
                                              "ectodermal, origin (curator)."),
    "foregut / hindgut primordium": (ECTO, B, "Foregut and hindgut primordia together: their common, ectodermal, "
                                              "origin (curator)."),
    "proventriculus": ("FBbt:00059316", E, ""),
    "midline primordium": ("FBbt:00059320", E, ""),
    "salivary gland primordium": ("FBbt:00059322", E, ""),
    "salivary gland body primordium": ("FBbt:00059321", E, ""),
    "salivary gland": ("FBbt:00059317", E, ""),
    "tracheal primordium": ("FBbt:00005041", E, ""),
    "tracheal system": ("FBbt:00005038", E, ""),
    "fat body": ("FBbt:00046052", E, "The fat body's principal cell type."),
    "plasmatocytes anlage": ("FBbt:00005249", E, "Immature plasmatocytes."),
    "plasmatocytes": ("FBbt:00001685", E, ""),
    "procrystal cell": ("FBbt:00001689", E, ""),
    "crystal cell": ("FBbt:00001690", E, ""),
    "germ cell": ("FBbt:00000092", E, "Pole cells become primordial germ cells as they migrate to the gonad."),
    "Germline": ("FBbt:00000092", E, "Germline cells in the neuroectoderm re-clustering."),
    "glia": ("FBbt:00052369", E, "Glia at 10-14 h, before their mature larval form."),
    "Oenocytes": ("FBbt:00001694", E, ""),
    "Sensory progenitors": ("FBbt:00001137", E, ""),
    "Immature neurons": ("FBbt:00051424", E, ""),
    "Mature neurons": ("FBbt:00047097", E, "Neurons born in the embryo are primary neurons."),
    "Multidendritic sensory": ("FBbt:00048285", E, ""),
    "External sensory": ("FBbt:00052615", E, ""),
    "Chordotonal sensory": ("FBbt:00005222", E, ""),
    "brain": ("FBbt:00059273", B, "Brain clusters at 10-18 h, mostly neurons: larval CNS neuron, which covers the late "
                                  "embryo (curator: a tissue type to its main cell type)."),
    "ventral nerve cord": ("FBbt:00059273", B, "VNC clusters at 12-16 h, mostly neurons: larval CNS neuron, which covers "
                                               "the late embryo (curator: a tissue type to its main cell type)."),
    "brain primordium": (NB, B, "The brain primordium at 6-10 h: its neuroblasts (curator)."),
    "ventral nerve cord primordium": (NB, B, "The VNC primordium at 4-6 h: its neuroblasts (curator)."),
    "Neural progenitors": (NB, B, "Neural progenitors of the neuroectoderm re-clustering: embryonic neuroblast (curator)."),
    "peripheral nervous system": ("FBbt:00059275", B, "PNS at 8-10 h: larval PNS neuron, which covers the late embryo "
                                                      "(curator)."),
    "peripheral nervous system primordium": (PSP, B, "The PNS primordium: its sensory precursors (curator)."),
    "sensory nervous system primordium": (PSP, B, "The sensory nervous system primordium: its sensory precursors (curator)."),
    "sensory nervous system": ("FBbt:00058245", B, "Sensory nervous system at 12-18 h: its sensory neurons (curator)."),
    "Malpighian tubule": ("FBbt:00005642", E, "Specialized Malpighian tubule cells cover all tubule cell types "
                                              "(curator: embryonic; the 16-18 h cluster embryonic/larval)."),
    "yolk nuclei": ("FBbt:00000057", E, "FBbt's yolk nucleus is a cell component, not a cell; accepted as the data are "
                                        "nuclei (curator)."),
    "Cholinergic": ("FBbt:00058215", E, "Late-embryonic neurons: the larval class term (curator)."),
    "Glutamatergic": ("FBbt:00058218", E, "Late-embryonic neurons: the larval class term (curator)."),
    "Monoaminergic": ("FBbt:00058211", E, "Late-embryonic neurons: the larval class term (curator)."),
    "Peptidergic": ("FBbt:00058212", E, "Late-embryonic neurons: the larval class term (curator)."),
}
HELD = {
    "anlage in statu nascendi": "No tissue is named: an anlage still forming, of unknown fate.",
    "cellular blastoderm / pole cell": "Two unrelated cell types together; their only common parent is cell.",
    "Head epid. /muscle": "Head epidermis and muscle together; their only common parent is somatic cell.",
    "Undiff.": "Mature neurons the authors left undifferentiated (untyped).",
    "Chordotonal glia": "FBbt has no chordotonal glial cell term; the chordotonal cap and scolopale cells are support "
                        "cells, not glia.",
    "Ventral midline": "Midline neurons and glia pooled over 6-18 h; no adequate common cell term.",
    "spiracle (tracheal system)": "FBbt has no spiracle cell term (curator: hold).",
}


def term(fbbt_id: str) -> dict:
    with urllib.request.urlopen(OLS + urllib.parse.quote(fbbt_id)) as r:
        t = json.load(r)["_embedded"]["terms"][0]
    assert not t["is_obsolete"], fbbt_id
    return {"fbbt_term": t["label"], "fbbt_id": fbbt_id, "fbbt_definition": " ".join(t["description"])}


def write(typ: str, m: dict) -> None:
    path = PROJ / "type_mapping" / f"{label_slug(typ)}.fbbt_mapping.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"cluster_label": typ, **m}, indent=2, ensure_ascii=False) + "\n")


def base(typ: str) -> dict:
    return {"working_definition": f"Nuclei of the authors' {typ!r} cluster(s) (Calderon et al. 2022), embryos 0-18 h.",
            "searches_performed": [typ], "other_candidates": [], "new_term_needed": False,
            "verification_needed": False}


def main() -> None:
    cache: dict[str, dict] = {}
    for typ, (fid, match, note) in MAPPED.items():
        best = cache.setdefault(fid, term(fid))
        write(typ, {**base(typ),
                    "best_match": {**best, "match_type": match,
                                   "skos_mapping": "skos:exactMatch" if match == E else "skos:broadMatch",
                                   "confidence": "high"},
                    "justification": (f"The authors' annotation {typ!r}. " + note).strip(),
                    "recommendation": f"Map to {fid} {best['fbbt_term']} ({match})."})
    for typ, why in HELD.items():
        write(typ, {**base(typ), "best_match": None, "justification": why + " Held (curator 2026-10-18).",
                    "recommendation": "Hold: no adequate FBbt term."})
    print(f"wrote {len(MAPPED)} mapped and {len(HELD)} held type mappings ({len(cache)} terms)")


if __name__ == "__main__":
    main()
