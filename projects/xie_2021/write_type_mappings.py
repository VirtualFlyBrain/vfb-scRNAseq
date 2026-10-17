#!/usr/bin/env python
"""Xie et al. 2021: the type-level FBbt mappings.

Curator 2026-10-17: immature terms up to the pupal stage (0 h, 24 h APF), mature from the
pharate adult stage (48 h APF, adult); ambiguous author types to their common parent.
FBbt has adult PN type terms with lineage (adPN / lPN / vPN; the authors' `lineage`
column) but no immature (or remodelling) projection neuron terms yet (requested), so the
0 h / 24 h types map meanwhile to the stage-neutral PN class of their lineage, broad
(curator 2026-10-17; type_mapping/immature/); APL, with no stage-neutral class, is held. Terms and definitions are read from OLS.

Usage:
    uv run python projects/xie_2021/write_type_mappings.py
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

from vfb_scrnaseq.project_config import label_slug

PROJ = Path(__file__).resolve().parent
OLS = "https://www.ebi.ac.uk/ols4/api/ontologies/fbbt/terms?obo_id="
ADPN_PARENT = "FBbt:00100368"      # adult uniglomerular antennal lobe projection neuron adPN
EXACT, BROAD = "exact match", "broad match"
MATURE = {   # author type: (FBbt id, match, justification)
    "D": ("FBbt:00067355", EXACT, "D PNs; the authors' lineage adPN."),
    "DA1": ("FBbt:00067363", EXACT, "DA1 PNs; lineage lPN."),
    "DA1_fru+": ("FBbt:00067363", BROAD, "The fru+ subset of DA1 lPNs; FBbt has no fru+ / fru- DA1 subtypes."),
    "DA1_fru-": ("FBbt:00067363", BROAD, "The fru- subset of DA1 lPNs; FBbt has no fru+ / fru- DA1 subtypes."),
    "DC3": ("FBbt:00040000", EXACT, "DC3 PNs; lineage adPN."),
    "DL1": ("FBbt:00067353", EXACT, "DL1 PNs; lineage adPN."),
    "DL3": ("FBbt:00067364", EXACT, "DL3 PNs; lineage lPN."),
    "DM6": ("FBbt:00067360", EXACT, "DM6 PNs; lineage adPN."),
    "VA1d": ("FBbt:00067357", EXACT, "VA1d PNs; lineage adPN."),
    "VA1v": ("FBbt:00067361", EXACT, "VA1v PNs; lineage adPN."),
    "VA5": ("FBbt:00067366", EXACT, "VA5 PNs; lineage lPN."),
    "VA6": ("FBbt:00007447", EXACT, "VA6 PNs; lineage adPN."),
    "VC2": ("FBbt:00007449", EXACT, "VC2 PNs; lineage lPN."),
    "VM2": ("FBbt:00067359", EXACT, "VM2 PNs; lineage adPN."),
    "VM7 or VM5v #1": (ADPN_PARENT, BROAD, "VM7 or VM5v PNs (the authors could not tell which; one of two such "
                                           "clusters): the common parent of VM7 adPN and VM5v adPN."),
    "VM7 or VM5v #2": (ADPN_PARENT, BROAD, "VM7 or VM5v PNs (the authors could not tell which; one of two such "
                                           "clusters): the common parent of VM7 adPN and VM5v adPN."),
    "DC3 and VA1d": (ADPN_PARENT, BROAD, "DC3 and VA1d PNs together (not separated in adults): the common "
                                         "parent of DC3 adPN and VA1d adPN."),
    "vPN": ("FBbt:00007437", EXACT, "Ventral PNs (vPNs), not resolved to a type."),
    "vPN_DA1": ("FBbt:00067372", EXACT, "DA1 vPNs (knot analysis)."),
    "APL": ("FBbt:00100222", EXACT, "The APL neuron (labelled by GH146; not a projection neuron)."),
}
LINEAGE_CLASS = {   # stage-neutral PN classes, for the immature-stage types meanwhile (curator 2026-10-17)
    "adPN": "FBbt:00067349",   # antennal lobe projection neuron adPN
    "lPN": "FBbt:00067362",    # antennal lobe projection neuron of ALl1 lineage (FBbt's former lPN)
    "vPN": "FBbt:00067351",    # antennal lobe projection neuron vPN
}
IMMATURE = {   # author type: lineage (the authors' `lineage` column); None: no stage-neutral class
    "APL": None, "D": "adPN", "DA1_fru+": "lPN", "DA1_fru-": "lPN", "DA3": "adPN", "DA4l": "adPN",
    "DC2": "adPN", "DC3": "adPN", "DL1": "adPN", "DL3": "lPN", "DM2": "lPN", "DM6": "adPN",
    "VA1d": "adPN", "VA1v": "adPN", "VA2": "adPN", "VA5": "lPN", "VA6": "adPN", "VC2": "lPN",
    "VM2": "adPN", "VM7 or VM5v #1": "adPN", "VM7 or VM5v #2": "adPN", "vPN": "vPN", "vPN_DA1": "vPN",
}


def term(fbbt_id: str) -> dict:
    with urllib.request.urlopen(OLS + urllib.parse.quote(fbbt_id)) as r:
        t = json.load(r)["_embedded"]["terms"][0]
    assert not t["is_obsolete"], fbbt_id
    return {"fbbt_term": t["label"], "fbbt_id": fbbt_id, "fbbt_definition": " ".join(t["description"])}


def write(path: Path, m: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    for typ, (fid, match, why) in MATURE.items():
        best = term(fid)
        write(PROJ / "type_mapping" / f"{label_slug(typ)}.fbbt_mapping.json", {
            "cluster_label": typ,
            "working_definition": f"Olfactory projection neuron type {typ} of Xie et al. 2021 at 48 h APF or "
                                  f"adult (pharate adult / adult).",
            "searches_performed": [f"adult antennal lobe projection neuron {typ}"],
            "best_match": {**best, "match_type": match,
                           "skos_mapping": "skos:exactMatch" if match == EXACT else "skos:broadMatch",
                           "confidence": "high"},
            "justification": why + " Mature term from the pharate adult stage (curator).",
            "other_candidates": [],
            "recommendation": f"Map to {fid} {best['fbbt_term']} ({match}).",
            "new_term_needed": False,
            "verification_needed": False,
        })
    for typ, lineage in IMMATURE.items():
        path = PROJ / "type_mapping" / "immature" / f"{label_slug(typ)}.fbbt_mapping.json"
        base = {
            "cluster_label": typ,
            "working_definition": f"Olfactory projection neuron type {typ} (Xie et al. 2021) at 0 h or 24 h APF.",
            "searches_performed": [f"immature antennal lobe projection neuron {typ}",
                                   "immature antennal lobe projection neuron"],
            "other_candidates": [],
            "new_term_needed": True,
            "verification_needed": False,
        }
        if lineage is None:
            write(path, {**base, "best_match": None,
                         "justification": "Up to the pupal stage the immature term is used (curator), but FBbt has no "
                                          "pupal term for this cell and no stage-neutral parent; held until FBbt adds "
                                          "one (requested, curator 2026-10-17).",
                         "recommendation": "Hold until FBbt has a pupal-stage term."})
            continue
        best = term(LINEAGE_CLASS[lineage])
        write(path, {**base,
                     "best_match": {**best, "match_type": "broad match", "skos_mapping": "skos:broadMatch",
                                    "confidence": "high"},
                     "justification": f"Up to the pupal stage the immature term is used (curator), but FBbt has no "
                                      f"immature (or remodelling) antennal lobe projection neuron terms yet "
                                      f"(requested, curator 2026-10-17); meanwhile the stage-neutral class for the "
                                      f"authors' lineage ({lineage}), to be refined when the new terms exist.",
                     "recommendation": f"Map to {best['fbbt_id']} {best['fbbt_term']} (broad match) until FBbt has the "
                                       f"immature / remodelling term for {typ}."})
    print(f"wrote {len(MATURE)} mature and {len(IMMATURE)} immature-stage type mappings (lineage classes; APL held)")


if __name__ == "__main__":
    main()
