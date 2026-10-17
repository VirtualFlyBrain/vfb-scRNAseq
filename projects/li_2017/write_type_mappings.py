#!/usr/bin/env python
"""Li, Horns et al. 2017: the type-level FBbt mappings (no judgement needed).

Curator 2026-10-17: immature terms up to the pupal stage (24 h, 36 h APF), mature from the
pharate adult stage (48 h, 72 h APF, adult). FBbt has the mature PN types but no immature
projection neuron terms, so the 24 h / 36 h types are held (no term; new terms to be
requested together with Xie 2021's) in type_mapping/immature/; the mature types are mapped
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
IMMATURE = ["DA1", "VA1d", "DC3", "DC2", "VM2", "DL3"]


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
    for typ in IMMATURE:
        write(PROJ / "type_mapping" / "immature" / f"{label_slug(typ)}.fbbt_mapping.json", {
            "cluster_label": typ,
            "working_definition": f"Olfactory projection neurons of type {typ} (Li et al. 2017) at "
                                  f"24 h or 36 h APF (pupal).",
            "searches_performed": [f"immature antennal lobe projection neuron {typ}",
                                   "immature antennal lobe projection neuron"],
            "best_match": None,
            "justification": "Up to the pupal stage the immature term is used (curator), but FBbt has no "
                             "immature antennal lobe projection neuron terms; the nearest immature ancestor "
                             "is immature neuron, which is too broad (held). New terms to be requested "
                             "with Xie 2021's (curator 2026-10-17).",
            "other_candidates": [],
            "recommendation": "Hold until FBbt has an immature term for this PN type.",
            "new_term_needed": True,
            "verification_needed": False,
        })
    print(f"wrote {len(MATURE)} mature and {len(IMMATURE)} held immature type mappings")


if __name__ == "__main__":
    main()
