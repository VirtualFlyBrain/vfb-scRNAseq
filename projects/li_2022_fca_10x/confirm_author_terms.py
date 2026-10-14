"""Type-level FBbt mappings for FCA author types whose author term needs no judgement.

Fly Cell Atlas (Li et al. 2022) types annotated by the authors with a single, current
(non-obsolete) FBbt **cell** term (is_a descendant of 'cell') are mapped to that term
— or to its 'adult X' variant where FBbt has one (the data are adult; curation rule 4).
Everything else (no author term / "Manual Annotation", several author terms, tissue or
organ terms, obsolete terms, stage-qualified types) is mapped by the
`map-clusters-to-fbbt` agent from a report, not here.

Input: type_evidence.json (type_evidence.py). Output:
type_mapping/<slug>.fbbt_mapping.json for each confirmed type (same schema as the
agents' output; validated by the check_fbbt_mapping hook via
scripts/validate_project_files.py). Never overwrites a file with `manual_edit`.

Usage: uv run python projects/li_2022_fca_10x/confirm_author_terms.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJ.parents[1] / "src"))

from vfb_scrnaseq.project_config import label_slug  # noqa: E402

# author types with a single current FBbt cell term that still go to the agents
# (stage-qualified or otherwise not a plain restatement of the term)
JUDGED = {
    "crystal cell", "follicle cell St. 9+", "main body follicle cell ca. until St. 5",
    "posterior terminal follicle cell ca. St. 5-8", "spermatogonium-spermatocyte transition",
    "spermatocyte cyst cell branch a", "spermatocyte cyst cell branch b",
    "transmedullary neuron Tm3a",
}


def confirmable(t: dict) -> bool:
    a = t["author"]
    return (len(a) == 1 and a[0]["id"].startswith("FBbt:") and a[0].get("is_cell")
            and not a[0].get("obsolete") and t["type"] not in JUDGED
            and not t["type"].startswith("spermatocyte "))


def mapping(t: dict, version: str) -> dict:
    a = t["author"][0]
    adult = [c for c in t["candidates"] if c["why"] == "adult variant"]
    where = ", ".join(f"{k} ({v} cells)" for k, v in sorted(t["where"].items()))
    author_term = {"fbbt_term": a["name"], "fbbt_id": a["id"], "fbbt_definition": a.get("definition") or ""}
    searches = [f"authors' ontology id {a['id']} (FBbt {version})",
                f"'adult {a['name']}' (exact label / exact synonym, FBbt {version})",
                f"'{t['type']}' (exact label / exact synonym, FBbt {version})"]
    base = (f"Author cell type '{t['type']}' of the Fly Cell Atlas (Li et al. 2022; adult flies), "
            f"annotated by the authors with {a['id']} '{a['name']}'. Found in: {where}.")
    if adult:
        c = adult[0]
        best = {"fbbt_term": c["name"], "fbbt_id": c["id"], "fbbt_definition": c.get("definition") or "",
                "match_type": "exact match", "skos_mapping": "skos:exactMatch", "confidence": "high"}
        others = [dict(author_term, reason_rejected=(
            "The authors' term; FBbt has the adult-specific variant, preferred because the "
            "data are from adult flies (curation rule 4)."))]
        just = (f"The authors annotated this type with {a['id']} '{a['name']}', a current FBbt cell "
                f"term. FBbt has the adult-specific variant {c['id']} '{c['name']}', which denotes the "
                f"same cells in the adult; the data are from adult flies, so the adult term is used.")
        rec = f"Map to {c['id']} '{c['name']}' (adult variant of the authors' term), exact match."
    else:
        best = dict(author_term, match_type="exact match", skos_mapping="skos:exactMatch", confidence="high")
        others = []
        just = (f"The authors annotated this type with {a['id']} '{a['name']}', a current "
                f"(non-obsolete) FBbt cell term; FBbt has no adult-specific variant of it. The "
                f"authors' typing is taken at face value.")
        rec = f"Map to the authors' term {a['id']} '{a['name']}', exact match."
    return {
        "cluster_label": t["type"],
        "working_definition": base,
        "searches_performed": searches,
        "best_match": best,
        "justification": just,
        "other_candidates": others,
        "recommendation": rec,
        "new_term_needed": False,
        "verification_needed": False,
    }


def main() -> None:
    ev = json.loads((PROJ / "type_evidence.json").read_text())
    out_dir = PROJ / "type_mapping"
    out_dir.mkdir(exist_ok=True)
    n = n_adult = 0
    for t in ev["types"]:
        if not confirmable(t):
            continue
        path = out_dir / f"{label_slug(t['type'])}.fbbt_mapping.json"
        if path.exists() and "manual_edit" in json.loads(path.read_text()):
            continue
        m = mapping(t, ev["fbbt_version"])
        path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
        n += 1
        n_adult += m["best_match"]["fbbt_id"] != t["author"][0]["id"]
    print(f"wrote {n} confirmed type mappings ({n_adult} upgraded to the adult variant) -> {out_dir}")


if __name__ == "__main__":
    main()
