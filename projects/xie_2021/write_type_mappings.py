#!/usr/bin/env python
"""Xie et al. 2021: the type-level FBbt mappings.

Curator 2026-10-17: immature terms up to the pupal stage (0 h, 24 h APF), mature from the
pharate adult stage (48 h APF, adult); ambiguous author types to their common parent.
The 0 h / 24 h types (type_mapping/immature/) map to FBbt's pupal PN terms, requested for
this paper (FBbt #2220, in FBbt 2026-11-02): *immature adult ... PN* for larval-born PNs,
*pupal ... PN* for embryonic-born ones (remodelling) and vPNs, and *pupal mushroom body anterior
paired lateral cell* for APL. Until then they mapped to the stage-neutral PN class of
their lineage (broad) and APL was held. Terms and definitions are read from OLS.

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
IMMATURE_ADPN = "FBbt:00053704"   # immature adult uniglomerular antennal lobe projection neuron adPN
IMMATURE = {   # author type: (pupal FBbt term from FBbt #2220, match, justification)
    "APL": ("FBbt:00053708", EXACT, "The APL neuron (labelled by GH146; not a projection neuron)."),
    "D": ("FBbt:00053686", EXACT, "D adPNs."),
    "DA1_fru+": ("FBbt:00053697", BROAD, "The fru+ subset of DA1 lPNs; FBbt has no fru+ / fru- DA1 subtypes."),
    "DA1_fru-": ("FBbt:00053697", BROAD, "The fru- subset of DA1 lPNs; FBbt has no fru+ / fru- DA1 subtypes."),
    "DA3": ("FBbt:00053687", EXACT, "DA3 adPNs."),
    "DA4l": ("FBbt:00053705", EXACT, "DA4l adPNs (embryonic-born, remodelling)."),
    "DC2": ("FBbt:00053688", EXACT, "DC2 adPNs."),
    "DC3": ("FBbt:00053689", EXACT, "DC3 adPNs."),
    "DL1": ("FBbt:00053690", EXACT, "DL1 adPNs."),
    "DL3": ("FBbt:00053698", EXACT, "DL3 lPNs."),
    "DM2": ("FBbt:00053699", EXACT, "DM2 lPNs."),
    "DM6": ("FBbt:00053691", EXACT, "DM6 adPNs."),
    "VA1d": ("FBbt:00053692", EXACT, "VA1d adPNs."),
    "VA1v": ("FBbt:00053693", EXACT, "VA1v adPNs."),
    "VA2": ("FBbt:00053707", EXACT, "VA2 adPNs (embryonic-born, remodelling)."),
    "VA5": ("FBbt:00053700", EXACT, "VA5 lPNs."),
    "VA6": ("FBbt:00053706", EXACT, "VA6 adPNs (embryonic-born, remodelling)."),
    "VC2": ("FBbt:00053701", EXACT, "VC2 lPNs."),
    "VM2": ("FBbt:00053694", EXACT, "VM2 adPNs."),
    "VM7 or VM5v #1": (IMMATURE_ADPN, BROAD, "VM7 or VM5v adPNs (the authors could not tell which; one of two such "
                                             "clusters): the common parent of immature adult VM7 adPN and VM5v adPN."),
    "VM7 or VM5v #2": (IMMATURE_ADPN, BROAD, "VM7 or VM5v adPNs (the authors could not tell which; one of two such "
                                             "clusters): the common parent of immature adult VM7 adPN and VM5v adPN."),
    "vPN": ("FBbt:00053703", EXACT, "Ventral PNs (vPNs), not resolved to a type."),
    "vPN_DA1": ("FBbt:00053702", EXACT, "DA1 vPNs (knot analysis)."),
}


def term(fbbt_id: str) -> dict:
    with urllib.request.urlopen(OLS + urllib.parse.quote(fbbt_id)) as r:
        t = json.load(r)["_embedded"]["terms"][0]
    assert not t["is_obsolete"], fbbt_id
    return {"fbbt_term": t["label"], "fbbt_id": fbbt_id, "fbbt_definition": " ".join(t["description"])}


def write(path: Path, m: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")


KNOT_TYPES = {"D", "DM6", "VA1v", "VM2", "VM7 or VM5v #1", "VM7 or VM5v #2", "vPN", "vPN_DA1"}
KNOT_NOTE = ("kn+ PNs (knot analysis, no lineage column): the paper states they \"include six types of "
             "adPNs and two vPNs\" (Figure 2), i.e. D, DM6, VA1v, VM2, VM7, VM5v (adPN) and the two vPNs.")


def lineage_evidence() -> dict[str, str]:
    """{author type: the authors' per-cell lineage counts in the main analysis}, as text."""
    import collections
    import h5py
    o = h5py.File(PROJ.parents[1] / ".cache" / "xie" / "all.h5ad", "r")["obs"]

    def col(name):
        v = o[name]
        if isinstance(v, h5py.Group):
            cats = [c.decode() if isinstance(c, bytes) else c for c in v["categories"][:]]
            return [cats[c] if c >= 0 else "nan" for c in v["codes"][:]]
        cats = [c.decode() if isinstance(c, bytes) else c for c in o["__categories"][name][:]]
        return [cats[c] if c >= 0 else "nan" for c in v[:]]
    counts: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for typ, lin in zip(col("PN_type"), col("lineage")):
        counts[typ][lin or "unlabelled"] += 1
    return {typ: ", ".join(f"{k} {n}" for k, n in c.most_common()) for typ, c in counts.items()}


def lineage_note(typ: str, ev: dict[str, str]) -> str:
    parts = []
    if typ in ev:
        parts.append(f"Lineage: the authors' per-cell `lineage` for this type in the main analysis: {ev[typ]}.")
    if typ in KNOT_TYPES:
        parts.append(KNOT_NOTE)
    return (" " + " ".join(parts)) if parts else ""


def main() -> None:
    ev = lineage_evidence()
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
            "justification": why + " Mature term from the pharate adult stage (curator)." + lineage_note(typ, ev),
            "other_candidates": [],
            "recommendation": f"Map to {fid} {best['fbbt_term']} ({match}).",
            "new_term_needed": False,
            "verification_needed": False,
        })
    for typ, (fid, match, why) in IMMATURE.items():
        best = term(fid)
        write(PROJ / "type_mapping" / "immature" / f"{label_slug(typ)}.fbbt_mapping.json", {
            "cluster_label": typ,
            "working_definition": f"Olfactory projection neuron type {typ} (Xie et al. 2021) at 0 h or 24 h APF.",
            "searches_performed": [f"immature antennal lobe projection neuron {typ}",
                                   "immature antennal lobe projection neuron",
                                   "FBbt #2220 terms (FBbt 2026-11-02)"],
            "best_match": {**best, "match_type": match,
                           "skos_mapping": "skos:exactMatch" if match == EXACT else "skos:broadMatch",
                           "confidence": "high"},
            "justification": why + " Up to the pupal stage the immature or pupal term is used (curator); FBbt #2220, "
                                   "release 2026-11-02."
                             + lineage_note(typ, ev),
            "other_candidates": [],
            "recommendation": f"Map to {fid} {best['fbbt_term']} ({match}).",
            "new_term_needed": False,
            "verification_needed": False,
        })
    print(f"wrote {len(MATURE)} mature and {len(IMMATURE)} immature-stage type mappings")


if __name__ == "__main__":
    main()
