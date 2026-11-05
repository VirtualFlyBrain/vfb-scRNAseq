#!/usr/bin/env python
"""Li, Horns et al. 2017: the type-level FBbt mappings (no judgement needed).

Curator 2026-10-17: immature terms up to the pupal stage (24 h, 36 h APF), mature from the
pharate adult stage (48 h, 72 h APF, adult). The 24 h / 36 h types map to FBbt's pupal
PN terms (type_mapping/immature/), requested with Xie 2021's (FBbt #2220, in FBbt
2026-11-02; until then the stage-neutral PN class of the lineage, broad); the mature types
are mapped in type_mapping/. Terms and definitions are read from OLS.

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
IMMATURE = {   # author type: pupal FBbt term (FBbt #2220); lineage from the paper: DA1 / DL3 acj6- lPNs,
    # the others adPNs
    "DA1": "FBbt:00053697",    # immature adult antennal lobe projection neuron DA1 lPN
    "VA1d": "FBbt:00053692",   # immature adult antennal lobe projection neuron VA1d adPN
    "DC3": "FBbt:00053689",    # immature adult antennal lobe projection neuron DC3 adPN
    "DC2": "FBbt:00053688",    # immature adult antennal lobe projection neuron DC2 adPN
    "VM2": "FBbt:00053694",    # immature adult antennal lobe projection neuron VM2 adPN
    "DL3": "FBbt:00053698",    # immature adult antennal lobe projection neuron DL3 lPN
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
    for typ, fid in IMMATURE.items():
        best = term(fid)
        write(PROJ / "type_mapping" / "immature" / f"{label_slug(typ)}.fbbt_mapping.json", {
            "cluster_label": typ,
            "working_definition": f"Olfactory projection neuron type {typ} (Li et al. 2017) at 24 h or 36 h APF.",
            "searches_performed": [f"immature antennal lobe projection neuron {typ}",
                                   "immature antennal lobe projection neuron",
                                   "FBbt #2220 terms (FBbt 2026-11-02)"],
            "best_match": {**best, "match_type": "exact match", "skos_mapping": "skos:exactMatch",
                           "confidence": "high"},
            "justification": f"Up to the pupal stage the immature term is used (curator); FBbt's pupal form of the "
                             f"{typ} PN, added for these datasets (FBbt #2220, release 2026-11-02). Lineage from the "
                             f"paper's definitions: DA1 and DL3 PNs are acj6- lPNs (Mz19+/acj6- DA1; the "
                             f"acj6-/CG31676+ clusters #6 / #6' DL3), VA1d, DC3, DC2 and VM2 acj6+ adPNs (Figures 3-4).",
            "other_candidates": [],
            "recommendation": f"Map to {fid} {best['fbbt_term']} (exact match).",
            "new_term_needed": False,
            "verification_needed": False,
        })
    print(f"wrote {len(MATURE)} mature and {len(IMMATURE)} immature-stage type mappings")


if __name__ == "__main__":
    main()
