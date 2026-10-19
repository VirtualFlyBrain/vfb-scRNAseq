#!/usr/bin/env python
"""Calderon et al. 2022: cluster-level exceptions to the type mappings.

The type mappings are per author type; where the curator chose a different term for one
window's cluster of a type, this rewrites that cluster's mapping/ file. Run after
scripts/expand_type_mappings.py (which rewrites mapping/), then collate.

- Malpighian tubule at 16-18 h: embryonic/larval specialized Malpighian tubule cell (the
  6-8 h and 12-14 h clusters keep the embryonic term; curator 2026-10-19).
- brain at 10-12 h and 12-14 h: immature primary neuron (the 14-18 h clusters keep larval
  CNS neuron; curator 2026-10-19).

Usage:
    uv run python projects/calderon_2022/override_cluster_mappings.py
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

from vfb_scrnaseq.project_config import label_slug

PROJ = Path(__file__).resolve().parent
OLS = "https://www.ebi.ac.uk/ols4/api/ontologies/fbbt/terms?obo_id="
OVERRIDES = {   # (author type, clustering): (FBbt id, justification)
    ("Malpighian tubule", "16_18"): ("FBbt:00001904", "Specialized Malpighian tubule cells cover all tubule cell "
                                                      "types; at 16-18 h, near hatching, the embryonic/larval term "
                                                      "(curator)."),
    ("brain", "10_12"): ("FBbt:00052663", "Brain clusters at 10-12 h, mostly neurons not yet mature: immature primary "
                                          "neuron (curator: a tissue type to its main cell type)."),
    ("brain", "12_14"): ("FBbt:00052663", "Brain clusters at 12-14 h, mostly neurons not yet mature: immature primary "
                                          "neuron (curator: a tissue type to its main cell type)."),
}


def term(fbbt_id: str) -> dict:
    with urllib.request.urlopen(OLS + urllib.parse.quote(fbbt_id)) as r:
        t = json.load(r)["_embedded"]["terms"][0]
    assert not t["is_obsolete"], fbbt_id
    return {"fbbt_term": t["label"], "fbbt_id": fbbt_id, "fbbt_definition": " ".join(t["description"])}


def main() -> None:
    anns = json.loads((PROJ / "cell_type_annotations.json").read_text())["annotations"]
    done, keys = 0, set()
    for a in anns:
        o = OVERRIDES.get((a["type"], a["clustering"]))
        if not o:
            continue
        path = PROJ / "mapping" / f"{label_slug(a['label'])}.fbbt_mapping.json"
        m = json.loads(path.read_text())
        if m.get("manual_edit"):
            continue
        best = term(o[0])
        m["best_match"] = {**m["best_match"], **best}
        m["justification"] = f"The authors' annotation {a['type']!r}. " + o[1]
        m["recommendation"] = f"Map to {best['fbbt_id']} {best['fbbt_term']} ({m['best_match']['match_type']})."
        path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
        done += 1
        keys.add((a["type"], a["clustering"]))
    if keys != set(OVERRIDES):
        raise SystemExit(f"overrides matched no cluster: {sorted(set(OVERRIDES) - keys)}")
    print(f"applied {done} cluster override(s)")


if __name__ == "__main__":
    main()
