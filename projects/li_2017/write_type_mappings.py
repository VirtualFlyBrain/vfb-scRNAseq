#!/usr/bin/env python
"""Li, Horns et al. 2017: the type-level FBbt mappings (no judgement needed).

Curator 2026-10-17: immature terms up to the pupal stage (24 h, 36 h APF), mature from the
pharate adult stage (48 h, 72 h APF, adult). FBbt has the mature PN types but no immature
(or remodelling) projection neuron terms yet (requested with Xie 2021's), so the 24 h /
36 h types map meanwhile to the stage-neutral PN class of their lineage, broad (curator
2026-10-17; type_mapping/immature/); the mature types are mapped
in type_mapping/. Terms and definitions are read from OLS.

Usage:
    uv run python projects/li_2017/write_type_mappings.py
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

from vfb_scrnaseq.project_config import label_slug

PROJ = Path(__file__).resolve().parent
OLS = "https://www.ebi.ac.uk/ols4/api/ontologies/fbbt/terms?obo_id="
MATURE = {   # author type: (FBbt id, match, justification)
    "DA1": ("FBbt:00067363", "exact match", "Mz19+/acj6- DA1 PNs are lateral (lPN) DA1 projection neurons."),
    "VA1d": ("FBbt:00067357", "exact match", "Mz19+/acj6+ VA1d PNs are anterodorsal (adPN) VA1d projection neurons."),
    "DC3": ("FBbt:00040000", "exact match", "Mz19+/acj6+ DC3 PNs are anterodorsal (adPN) DC3 projection neurons."),
    "VA1d or DC3": ("FBbt:00100368", "broad match",
                    "The authors' adult Mz19+ adPN list, VA1d and DC3 not separated: the most specific "
                    "common parent of VA1d adPN and DC3 adPN."),
}
LINEAGE_CLASS = {   # stage-neutral PN classes, for the immature-stage types meanwhile (curator 2026-10-17)
    "adPN": "FBbt:00067349",   # antennal lobe projection neuron adPN
    "lPN": "FBbt:00067362",    # antennal lobe projection neuron of ALl1 lineage (FBbt's former lPN)
    "vPN": "FBbt:00067351",    # antennal lobe projection neuron vPN
}
IMMATURE = {   # author type: lineage (the paper: DA1 / DL3 acj6- lPNs; the others adPNs)
    "DA1": "lPN", "VA1d": "adPN", "DC3": "adPN", "DC2": "adPN", "VM2": "adPN", "DL3": "lPN",
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
            "working_definition": f"Olfactory projection neurons of type {typ} (Li et al. 2017), "
                                  f"48 h / 72 h APF or adult (pharate adult and adult).",
            "searches_performed": [f"antennal lobe projection neuron {typ}"],
            "best_match": {**best, "match_type": match,
                           "skos_mapping": "skos:exactMatch" if match == "exact match" else "skos:broadMatch",
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
            "working_definition": f"Olfactory projection neuron type {typ} (Li et al. 2017) at 24 h or 36 h APF.",
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
                                      f"authors' lineage ({lineage}), to be refined when the new terms exist. "
                                      f"Lineage from the paper's definitions: DA1 and DL3 PNs are acj6- lPNs "
                                      f"(Mz19+/acj6- DA1; the acj6-/CG31676+ clusters #6 / #6' DL3), VA1d, DC3, "
                                      f"DC2 and VM2 acj6+ adPNs (Figures 3-4).",
                     "recommendation": f"Map to {best['fbbt_id']} {best['fbbt_term']} (broad match) until FBbt has the "
                                       f"immature / remodelling term for {typ}."})
    print(f"wrote {len(MATURE)} mature and {len(IMMATURE)} immature-stage type mappings (lineage classes)")


if __name__ == "__main__":
    main()
