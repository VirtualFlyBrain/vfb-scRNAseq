#!/usr/bin/env python
"""Allen et al. 2020: the type-level FBbt mappings (curator 2026-10-18).

Types are the authors' calls in Figure 1-source data 2 (build_clusters.py): the predicted
hemilineage, else the neurotransmitter class, else the non-neuronal cell type.

- a single hemilineage: its secondary neuron term ("hemilineage 12B secondary neuron");
  where FBbt has no hemilineage term (10B, 15B, 16B, 23B; the authors predict none of
  these lineages' A hemilineages), the lineage's secondary neuron term, broad;
- hemilineage pairs the authors could not separate: their common Notch class (13A/19A,
  20A/22A Notch ON; 5B/6B Notch OFF), broad; 8A/24B (Notch ON / OFF, no common class) by
  the authors' neurotransmitter, adult glutamatergic neuron, broad;
- neurotransmitter classes: the adult class term (monoaminergic: adult aminergic neuron);
- glia: adult CNS glial cell (curator); sperm: spermatozoon.

The authors' neurotransmitter for hemilineage clusters is added per cluster afterwards
(add_neurotransmitter_matches.py, after scripts/expand_type_mappings.py).

Not added (curator 2026-10-18): neuromere terms from the authors' enriched Hox genes. The
authors assign cells, not clusters, to neuromeres, approximately (Figure 3E), and per
cluster this contradicts their own hemilineage calls (e.g. Antp-enriched 23B).

Held in build_clusters.py instead (no mapping): undefined, neuron, mixed neurotransmitter,
neuronal/glial (untyped) and salivary gland (artefact). Terms and definitions are read
from OLS.

Usage:
    uv run python projects/allen_2020/write_type_mappings.py
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

from vfb_scrnaseq.project_config import label_slug

PROJ = Path(__file__).resolve().parent
OLS = "https://www.ebi.ac.uk/ols4/api/ontologies/fbbt/terms?obo_id="
EXACT, BROAD = "exact match", "broad match"
HEMILINEAGE = {   # single hemilineages with an FBbt hemilineage term
    "0A": "FBbt:00053055", "1A": "FBbt:00051455", "1B": "FBbt:00051467", "4B": "FBbt:00053311",
    "6A": "FBbt:00051460", "8B": "FBbt:00051468", "9A": "FBbt:00051457", "9B": "FBbt:00051469",
    "11B": "FBbt:00051478", "12B": "FBbt:00051475", "13B": "FBbt:00051470", "14A": "FBbt:00053278",
    "21A": "FBbt:00051459",
}
LINEAGE = {"10B": "FBbt:00048899", "15B": "FBbt:00048900", "16B": "FBbt:00048896", "23B": "FBbt:00048920"}
NOTCH_ON, NOTCH_OFF = "FBbt:00049541", "FBbt:00049542"
OTHER = {   # author type: (FBbt id, match, justification)
    "hemilineages 13A/19A": (NOTCH_ON, BROAD, "The authors could not separate hemilineages 13A and 19A; both "
                                              "are Notch ON hemilineages: their common class."),
    "hemilineages 20A/22A": (NOTCH_ON, BROAD, "The authors could not separate hemilineages 20A and 22A; both "
                                              "are Notch ON hemilineages: their common class."),
    "hemilineages 5B/6B": (NOTCH_OFF, BROAD, "The authors could not separate hemilineages 5B and 6B; both are "
                                             "Notch OFF hemilineages: their common class."),
    "cholinergic neuron": ("FBbt:00058205", EXACT, "The authors' neurotransmitter class (ChAT, VAChT), adult VNC."),
    "GABAergic neuron": ("FBbt:00058207", EXACT, "The authors' neurotransmitter class (Gad1, VGAT), adult VNC."),
    "glutamatergic neuron": ("FBbt:00058208", EXACT, "The authors' neurotransmitter class (VGlut), adult VNC."),
    "peptidergic neuron": ("FBbt:00058202", EXACT, "The authors' class (peptidergic, no fast-acting "
                                                   "neurotransmitter), adult VNC."),
    "monoaminergic neuron": ("FBbt:00058201", EXACT, "The authors' monoaminergic class (Vmat), adult VNC: "
                                                     "adult aminergic neuron (curator)."),
    "glia": ("FBbt:00100499", EXACT, "The authors' glial clusters (repo), adult VNC: adult CNS glial cell "
                                     "(curator; the authors do not subtype them)."),
    "hemilineages 8A/24B": ("FBbt:00058208", BROAD, "The authors could not separate hemilineages 8A and 24B "
                                                    "(Notch ON / OFF: no adequate common hemilineage class); all "
                                                    "three clusters are glutamatergic (the authors' neurotransmitter "
                                                    "call): adult glutamatergic neuron (curator 2026-10-18)."),
    "sperm": ("FBbt:00004954", EXACT, "The authors' sperm cluster (non-neuronal; carried over in dissection, "
                                      "mostly male cells)."),
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


def mapped(typ: str, fid: str, match: str, why: str, search: str) -> None:
    best = term(fid)
    write(typ, {
        "working_definition": f"Adult VNC cells of the authors' type {typ} (Allen et al. 2020, Figure 1-source "
                              f"data 2), 5-day-old adults.",
        "searches_performed": [search],
        "best_match": {**best, "match_type": match,
                       "skos_mapping": "skos:exactMatch" if match == EXACT else "skos:broadMatch",
                       "confidence": "high"},
        "justification": why,
        "other_candidates": [],
        "recommendation": f"Map to {fid} {best['fbbt_term']} ({match}).",
        "new_term_needed": False,
        "verification_needed": False,
    })


def main() -> None:
    for hl, fid in HEMILINEAGE.items():
        mapped(f"hemilineage {hl}", fid, EXACT, f"The authors' predicted hemilineage {hl} (lineage markers and "
               f"fast-acting neurotransmitter, Figure 4): its secondary (postembryonic) neurons.",
               f"hemilineage {hl} secondary neuron")
        assert hl in term(fid)["fbbt_term"], fid
    for hl, fid in LINEAGE.items():
        n = hl[:-1]
        mapped(f"hemilineage {hl}", fid, BROAD, f"The authors' predicted hemilineage {hl} (Figure 4). FBbt has "
               f"no hemilineage {hl} term; lineage {n}'s secondary neurons are its parent (the authors predict "
               f"no {n}A cells).", f"hemilineage {hl} secondary neuron")
        assert f"lineage {n} " in term(fid)["fbbt_term"], fid
    for typ, (fid, match, why) in OTHER.items():
        mapped(typ, fid, match, why, term(fid)["fbbt_term"])
    print(f"wrote {len(HEMILINEAGE) + len(LINEAGE) + len(OTHER)} type mappings")


if __name__ == "__main__":
    main()
