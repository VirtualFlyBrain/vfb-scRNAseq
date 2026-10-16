#!/usr/bin/env python
"""Hörmann 2020: the type-level FBbt mappings (no judgement needed).

Each author type is one T4/T5 subtype, and FBbt has a term for each, mature and
immature (the immature ones defined from this paper). Curator 2026-10-16: immature
terms up to the pupal stage (24 h, 36 h APF: type_mapping/immature/), mature from the
pharate adult stage (48-72 h APF: type_mapping/). Terms and definitions are read
from OLS (FBbt release current at the time of the run).

Usage:
    uv run python projects/hormann_2020/write_type_mappings.py
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

PROJ = Path(__file__).resolve().parent
OLS = "https://www.ebi.ac.uk/ols4/api/ontologies/fbbt/terms?obo_id="
SUBTYPES = {   # subtype: (mature FBbt id, immature FBbt id)
    "T4a": ("FBbt:00003732", "FBbt:00052263"), "T4b": ("FBbt:00003733", "FBbt:00052264"),
    "T4c": ("FBbt:00003734", "FBbt:00052265"), "T4d": ("FBbt:00003735", "FBbt:00052266"),
    "T5a": ("FBbt:00003737", "FBbt:00052259"), "T5b": ("FBbt:00003738", "FBbt:00052260"),
    "T5c": ("FBbt:00003739", "FBbt:00052261"), "T5d": ("FBbt:00003740", "FBbt:00052262"),
}


def term(fbbt_id: str) -> dict:
    with urllib.request.urlopen(OLS + urllib.parse.quote(fbbt_id)) as r:
        t = json.load(r)["_embedded"]["terms"][0]
    assert not t["is_obsolete"], fbbt_id
    return {"fbbt_term": t["label"], "fbbt_id": fbbt_id, "fbbt_definition": " ".join(t["description"])}


def mapping(subtype: str, best: dict, other: dict, stage: str) -> dict:
    other_reason = ("Immature form; at the pharate adult stage the mature term is used (curator)."
                    if stage == "mature" else
                    "Mature form; up to the pupal stage the immature term is used (curator).")
    return {
        "cluster_label": f"{subtype} neuron",
        "working_definition": f"{subtype} neurons of Hörmann et al. 2020: one of the authors' eight "
                              f"clusters at each stage, assigned to subtype {subtype} by marker genes; "
                              f"FACS-sorted T4/T5 neurons, {'48-72 h APF (pharate adult)' if stage == 'mature' else '24 and 36 h APF (pupal)'}.",
        "searches_performed": [f"{subtype} neuron", f"immature {subtype} neuron"],
        "best_match": {**best, "match_type": "exact match", "skos_mapping": "skos:exactMatch",
                       "confidence": "high"},
        "justification": f"The authors assign the cluster to subtype {subtype}; FBbt has the "
                         f"{'mature' if stage == 'mature' else 'immature'} term for it"
                         f"{'' if stage == 'mature' else ' (defined from this paper)'}, as the stage requires.",
        "other_candidates": [{**other, "reason_rejected": other_reason}],
        "recommendation": f"Map to {best['fbbt_id']} {best['fbbt_term']} (exact match).",
        "new_term_needed": False,
        "verification_needed": False,
    }


def main() -> None:
    for subtype, (mature_id, immature_id) in SUBTYPES.items():
        mature, immature = term(mature_id), term(immature_id)
        for stage, best, other, folder in (("mature", mature, immature, PROJ / "type_mapping"),
                                           ("immature", immature, mature, PROJ / "type_mapping" / "immature")):
            folder.mkdir(parents=True, exist_ok=True)
            out = folder / f"{subtype}_neuron.fbbt_mapping.json"
            out.write_text(json.dumps(mapping(subtype, best, other, stage), indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {2 * len(SUBTYPES)} type mappings")


if __name__ == "__main__":
    main()
