#!/usr/bin/env python
"""Baker et al. 2021: the type-level FBbt mappings (curator 2026-10-21).

Types are the authors' own "Inferred cell type" per cluster (build_clusters.py), adult
brains (optic lobes included). Adult cell terms; FBbt has no central-brain versions of the
neurotransmitter classes, so "Central brain ..." maps to the class term. Curator calls
(shared with Mokashi 2021):

- clusters naming different structures together (optic lobe and antennal lobe; mushroom
  body and ellipsoid body; surface glia and fat body) held: only neuron / cell in common;
- two neurotransmitter classes in one name: both terms only where co-expression is stated
  (annotations or paper), else held: neither "Neuropeptides/cholinergic neurons" nor
  "GABAergic and monoaminergic neurons" is stated, so both held;
- "Central brain neurons type A" held (typeable only as neuron);
- "Optic lobe" to adult optic lobe neuron (broad: the tissue to its main cell type).

Terms and definitions are read from OLS.

Usage:
    uv run python projects/baker_2021/write_type_mappings.py
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
NO_CB = "FBbt has no central-brain version of the class."
MAPPED = {   # author type: (FBbt id, match, justification)
    "GABAergic neurons": ("FBbt:00058207", E, ""),
    "Central brain GABAergic neurons": ("FBbt:00058207", E, NO_CB),
    "Glutamatergic neurons": ("FBbt:00058208", E, ""),
    "Central Brain type 2 glutamatergic neurons": ("FBbt:00058208", E, NO_CB),
    "Central brain type B cholinergic neurons": ("FBbt:00058205", E, NO_CB),
    "Central brain type 2 monoaminergic neurons": ("FBbt:00058201", E, NO_CB),
    "Dopaminergic neurons": ("FBbt:00058206", E, ""),
    "Astrocytes": ("FBbt:00047841", E, ""),
    "Glia": ("FBbt:00100499", E, "Glia of the dissected brains (CNS)."),
    "Kenyon cells": ("FBbt:00049825", E, ""),
    "Olfactory projection neurons": ("FBbt:00051299", E, ""),
    "Optic lobe neurons": ("FBbt:00003702", E, ""),
    "Optic lobe": ("FBbt:00003702", B, "The optic lobe: its main cell type, the neuron."),
    "Photoreceptor cells": ("FBbt:00006009", E, "Photoreceptors of the adult compound eye (retina attached to the "
                                                "dissected brains)."),
    "Tachykinin/neuropeptidergic neurons": ("FBbt:00110061", E, ""),
}
HELD = {
    "Optic lobe and antennal lobe neurons": "Two structures together; their only common parent is neuron (curator).",
    "Mushroom body and ellipsoid body": "Two structures together; their only common parent is neuron (curator).",
    "Surface glia and fat body": "Glia and fat body together; their only common parent is cell (curator).",
    "Neuropeptides/cholinergic neurons": "Two classes in one name, and neither the annotations nor the paper say they "
                                         "are co-expressed (curator: hold if unclear).",
    "GABAergic and monoaminergic neurons": "Two classes in one name, and neither the annotations nor the paper say "
                                           "they are co-expressed (curator: hold if unclear).",
    "Central brain neurons type A": "Typeable only as neuron (curator).",
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
    return {"working_definition": f"Cells of the authors' {typ!r} cluster(s), adult brains (sucrose controls).",
            "searches_performed": [typ], "other_candidates": [], "new_term_needed": False,
            "verification_needed": False}


def main() -> None:
    anns = json.loads((PROJ / "cell_type_annotations.json").read_text())["annotations"]
    types = {a["type"] for a in anns if not a.get("unannotated")}
    if types != set(MAPPED) | set(HELD):
        raise SystemExit(f"types differ: {sorted(types ^ (set(MAPPED) | set(HELD)))}")
    for typ, (fid, match, why) in MAPPED.items():
        best = term(fid)
        write(typ, {**base(typ),
                    "best_match": {**best, "match_type": match,
                                   "skos_mapping": "skos:exactMatch" if match == E else "skos:broadMatch",
                                   "confidence": "high"},
                    "justification": f"The authors' annotation {typ!r}. {why}".strip(),
                    "recommendation": f"Map to {fid} {best['fbbt_term']} ({match})."})
    for typ, why in HELD.items():
        write(typ, {**base(typ), "best_match": None, "justification": f"The authors' annotation {typ!r}. {why}",
                    "recommendation": "Hold: no adequate FBbt term."})
    print(f"wrote {len(MAPPED)} mapped and {len(HELD)} held type mappings")


if __name__ == "__main__":
    main()
