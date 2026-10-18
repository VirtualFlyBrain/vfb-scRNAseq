#!/usr/bin/env python
"""Allen et al. 2020: add the authors' neurotransmitter class to hemilineage clusters.

The authors give each neuronal cluster a neurotransmitter as well as a predicted
hemilineage (Figure 1-source data 2). Clusters are typed by the hemilineage (best_match,
per type); the neurotransmitter, which varies within some hemilineage types, is added per
cluster as an additional match, the adult class term, broad (curator 2026-10-18).

Run after scripts/expand_type_mappings.py (which rewrites mapping/), then collate.

Usage:
    uv run python projects/allen_2020/add_neurotransmitter_matches.py
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

from vfb_scrnaseq.project_config import label_slug

PROJ = Path(__file__).resolve().parent
OLS = "https://www.ebi.ac.uk/ols4/api/ontologies/fbbt/terms?obo_id="
NT_TERM = {"acetylcholine": "FBbt:00058205", "GABA": "FBbt:00058207", "glutamate": "FBbt:00058208"}


def term(fbbt_id: str) -> dict:
    with urllib.request.urlopen(OLS + urllib.parse.quote(fbbt_id)) as r:
        t = json.load(r)["_embedded"]["terms"][0]
    assert not t["is_obsolete"], fbbt_id
    return {"fbbt_term": t["label"], "fbbt_id": fbbt_id, "fbbt_definition": " ".join(t["description"])}


def main() -> None:
    terms = {nt: term(fid) for nt, fid in NT_TERM.items()}
    anns = json.loads((PROJ / "cell_type_annotations.json").read_text())["annotations"]
    added = 0
    for a in anns:
        nt = a.get("author_neurotransmitter")
        path = PROJ / "mapping" / f"{label_slug(a['label'])}.fbbt_mapping.json"
        if not a.get("author_hemilineage") or nt not in NT_TERM or not path.exists():
            continue
        m = json.loads(path.read_text())
        if m.get("manual_edit") or not m.get("best_match") or m["best_match"]["fbbt_id"] == NT_TERM[nt]:
            continue
        m["additional_matches"] = [{**terms[nt], "match_type": "broad match", "skos_mapping": "skos:broadMatch",
                                    "confidence": "high"}]
        m["justification"] += (f" Also the authors' neurotransmitter for this cluster ({nt}): "
                               f"{terms[nt]['fbbt_term']} (additional match).")
        path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
        added += 1
    print(f"added a neurotransmitter match to {added} clusters")


if __name__ == "__main__":
    main()
