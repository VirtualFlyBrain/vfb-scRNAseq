#!/usr/bin/env python
"""Brunet Avalos 2019: the type-level FBbt mappings (curator 2026-10-19).

Types are the authors' cluster names without their numbers (build_clusters.py). First
instar larval brain, so the larval cell terms (FBbt has no larval-brain-specific versions,
so the dissection narrows nothing):

- neurotransmitter classes: the larval class terms; Glutamatergic/GABAergic neurons (cells
  co-expressing both, Figure 3-figure supplement 1): larval glutamatergic neuron, with
  larval GABAergic neuron as an additional match;
- Neural progenitor cells: larval neuroblast (broad); Mushroom Body: larval Kenyon cell
  (broad: the authors' re-clustering also finds MB neuroblasts and undifferentiated
  neurons, but Kenyon cells are probably the main component); Undifferentiated neurons:
  immature neuron (not known to be secondary);
- glia, optic lobe epithelium, muscle, hemocytes: their larval / stage-neutral terms;
  Prothoracic gland: endocrine cell of the larval ring gland (broad: the cluster also
  expresses Akh, corpora cardiaca, Figure 4C);
- held: "Corpora allata, Ring gland, Gut" (endocrine and gut cells together).

Terms and definitions are read from OLS.

Usage:
    uv run python projects/avalos_2019/write_type_mappings.py
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
MAPPED = {   # author type: (FBbt id, match, justification, additional FBbt ids)
    "Cholinergic neurons": ("FBbt:00058215", E, "The authors' cholinergic neurons (ChAT, VAChT).", []),
    "GABAergic neurons": ("FBbt:00058217", E, "The authors' GABAergic neurons (Gad1).", []),
    "Glutamatergic neurons": ("FBbt:00058218", E, "The authors' glutamatergic neurons (VGlut).", []),
    "Glutamatergic/GABAergic neurons": ("FBbt:00058218", E, "Neurons co-expressing glutamatergic and GABAergic "
                                        "markers (validated, Figure 3-figure supplement 1): each cell is both, so "
                                        "larval GABAergic neuron as an additional match (curator).",
                                        ["FBbt:00058217"]),
    "Peptidergic neurons": ("FBbt:00058212", E, "The authors' peptidergic neurons.", []),
    "Monoaminergic neurons": ("FBbt:00058211", E, "The authors' monoaminergic neurons (mostly dopaminergic, "
                                                  "Figure 3-figure supplement 2).", []),
    "Neural progenitor cells": ("FBbt:00007115", B, "The authors' neural progenitors (neuroblasts and their "
                                                    "progeny, Figure 2): larval neuroblast (curator).", []),
    "Mushroom Body": ("FBbt:00049826", B, "The authors' mushroom body cluster; its re-clustering finds MB "
                                          "neuroblasts, MB undifferentiated neurons and Kenyon cells (Figure 5), "
                                          "Kenyon cells probably the main component (curator).", []),
    "Undifferentiated neurons": ("FBbt:00051424", E, "Presumptive undifferentiated neurons (hdc high, elav low; "
                                                     "Figure 2-figure supplement 2): immature neuron; not known "
                                                     "to be secondary (curator).", []),
    "Glial cells": ("FBbt:00001251", E, "The authors' glia (repo).", []),
    "Optic lobe epithelium": ("FBbt:00111738", E, "Optic lobe neuroepithelium (Egger et al., 2010).", []),
    "Muscle cells": ("FBbt:00058231", E, "Muscle attached to the dissected brain (contaminating tissue, Figure "
                                         "1-figure supplement 2).", []),
    "Hemocytes": ("FBbt:00001684", E, "Hemocytes attached to the dissected brain (contaminating tissue).", []),
    "Prothoracic gland": ("FBbt:00058236", B, "Ring gland tissue attached to the brain; the cluster also expresses "
                                              "Akh (corpora cardiaca, Figure 4C): endocrine cell of the larval ring "
                                              "gland (curator; FBbt has no prothoracic gland cell term).", []),
}
HELD = {
    "Corpora allata, Ring gland, Gut": "Endocrine and gut cells together (contaminating tissue); no adequate common "
                                       "cell term. Held (curator 2026-10-19).",
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
    return {"working_definition": f"Cells of the authors' {typ!r} cluster(s) (Brunet Avalos et al. 2019, Figure 1), "
                                  f"first instar larval brain, fed.",
            "searches_performed": [typ], "other_candidates": [], "new_term_needed": False,
            "verification_needed": False}


def main() -> None:
    for typ, (fid, match, why, extra) in MAPPED.items():
        best = term(fid)
        m = {**base(typ),
             "best_match": {**best, "match_type": match,
                            "skos_mapping": "skos:exactMatch" if match == E else "skos:broadMatch",
                            "confidence": "high"},
             "justification": f"The authors' annotation {typ!r}. " + why,
             "recommendation": f"Map to {fid} {best['fbbt_term']} ({match})."}
        if extra:
            m["additional_matches"] = [{**term(x), "match_type": E, "skos_mapping": "skos:exactMatch",
                                        "confidence": "high"} for x in extra]
        write(typ, m)
    for typ, why in HELD.items():
        write(typ, {**base(typ), "best_match": None, "justification": why,
                    "recommendation": "Hold: no adequate FBbt term."})
    print(f"wrote {len(MAPPED)} mapped and {len(HELD)} held type mappings")


if __name__ == "__main__":
    main()
