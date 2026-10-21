#!/usr/bin/env python
"""Mokashi et al. 2021: the type-level FBbt mappings (curator 2026-10-21).

Types are the authors' own "Inferred cell type" per cluster (build_clusters.py), adult
brains (optic lobes included). Adult cell terms; FBbt has no central-brain versions of the
neurotransmitter classes, so "... of central brain" maps to the class term. Curator calls
(shared with Baker 2021):

- clusters naming different structures together (optic lobe and antennal lobe; ellipsoid
  body and mushroom body; eye, cuticle and glia; surface glia and fat body) held: their
  only common parent is neuron / cell;
- clusters the authors leave undetermined ("Undetermined, perhaps optic lobe neurons",
  "Mostly undetermined, dorsal fan-shaped body") held; "Neuropeptides in perhaps cholinergic
  neurons" to adult peptidergic neuron only (the part they are sure of);
- two neurotransmitter classes in one name: both terms only where co-expression is stated
  (annotations or paper), else held: "Neuropeptides/cholinergic neurons" is not stated, so
  held;
- "Developmental genes" held (not a cell type);
- surface glia narrowed to the brain (brain-only dissection makes it exact).

Terms and definitions are read from OLS.

Usage:
    uv run python projects/mokashi_2021/write_type_mappings.py
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
    "GABAergic neurons of central brain": ("FBbt:00058207", E, NO_CB),
    "Glutamatergic neurons": ("FBbt:00058208", E, ""),
    "Glutamaterigic neurons of central brain": ("FBbt:00058208", E, "(Sic.) " + NO_CB),
    "Cholinergic neurons of central brain": ("FBbt:00058205", E, NO_CB),
    "Adult dopaminergic neurons": ("FBbt:00058206", E, ""),
    "5-HT and DA neurons": ("FBbt:00058201", B, "Serotonergic and dopaminergic neurons together: their common class."),
    "Astrocytes": ("FBbt:00047841", E, ""),
    "Kenyon cells": ("FBbt:00049825", E, ""),
    "Olfactory projection neurons": ("FBbt:00051299", E, ""),
    "Optic lobe neurons": ("FBbt:00003702", E, ""),
    "Photoreceptor cells": ("FBbt:00006009", E, "Photoreceptors of the adult compound eye (retina attached to the "
                                                "dissected brains)."),
    "Surface glia": ("FBbt:00100500", E, "Brain-only dissection, so the brain surface glia term is exact."),
    "Tachykinin/neuropeptidergic neurons": ("FBbt:00110061", E, ""),
    "Cells of ellipsoid body and fan shaped body": ("FBbt:00049819", B, "Ellipsoid body and fan-shaped body cells: the "
                                                    "central complex neuron (the fan-shaped body-ellipsoid body neuron "
                                                    "is one specific class the name does not imply)."),
    "Neuropeptides in perhaps cholinergic neurons": ("FBbt:00058202", E, "Peptidergic; the authors hedge the "
                                                     "cholinergic part, so peptidergic only (curator)."),
}
HELD = {
    "Optic lobe and antennal lobe neurons": "Two structures together; their only common parent is neuron (curator).",
    "Ellipsoid body, mushroom body": "Two structures together; their only common parent is neuron (curator).",
    "Eye, cuticle, glia": "Different tissues together; their only common parent is cell (curator).",
    "Surface glia and fat body": "Glia and fat body together; their only common parent is cell (curator).",
    "Undetermined, perhaps optic lobe neurons": "The authors leave it undetermined (curator).",
    "Mostly undetermined, dorsal fan-shaped body": "The authors leave it mostly undetermined (curator).",
    "Neuropeptides/cholinergic neurons": "Two classes in one name, and neither the annotations nor the paper say they "
                                         "are co-expressed (curator: hold if unclear).",
    "Neuropeptides/cholinergic neurons, central brain": "Two classes in one name, and neither the annotations nor the "
                                                        "paper say they are co-expressed (curator: hold if unclear).",
    "Developmental genes": "Not a cell type (curator).",
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
    return {"working_definition": f"Cells of the authors' {typ!r} cluster(s), adult brains (reference medium).",
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
