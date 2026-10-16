#!/usr/bin/env python
"""Özel 2021: type-level FBbt mappings that need no judgement.

Two mapping sets (curator 2026-10-16: immature FBbt terms up to the pupal stage, mature
from the pharate adult stage): `type_mapping/` for P50, P70, adult and the P50 T4/T5
subtypes; `type_mapping/immature/` for P15, P30 and P40 (config
`type_mapping.clustering_dirs`). Written here:

- a named neuron type whose name is the exact label or EXACT synonym of one current
  FBbt neuron term: that term (mature set), and its 'immature X' term where FBbt has
  one (immature set);
- in the immature set, a named neuron without an 'immature X' term: the most specific
  FBbt ancestor that has an 'immature' form, as a broad match (as Kurmangaliyev's early
  clusters), with new_term_needed recording the gap (no request is made);
- the authors' pupal transient types with their own FBbt terms (TEd, TEv): that term
  in both sets;
- the numbered glial identities (G01-G17): adult optic lobe glial cell (mature set;
  exact for an optic-lobe dissection) / glial cell (immature set; FBbt has no immature
  optic lobe glia term), as broad matches.

Less-confident names ('*' in Supplementary Table 1) get verification_needed. Everything
else goes to the map-clusters-to-fbbt agents. Never overwrites a file with manual_edit.

Usage: uv run python projects/ozel_2021/confirm_terms.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

PROJ = Path(__file__).resolve().parent
REPO_ROOT = PROJ.parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vfb_scrnaseq.project_config import label_slug  # noqa: E402

IMMATURE = {"P15", "P30", "P40"}
NEURON = "FBbt:00005106"
GLIA = {"mature": ("FBbt:00100517", "adult optic lobe glial cell"), "immature": ("FBbt:00005144", "glial cell")}
TRANSIENT = {"TEd", "TEv"}
# abbreviations that mean something else in this paper than the FBbt synonym they match
# (LPC: lamina precursor cell, not lobula plate columnar neuron; NB: neuroblast; PR:
# photoreceptor, not protocerebrum): always judged by the agents
AMBIGUOUS = {"LPC", "NB", "PR"}
RELEASE = "FBbt fbbt/releases/2026-10-01"


def load_obo(path: Path) -> dict[str, dict]:
    terms, cur = {}, None
    for line in path.open():
        line = line.rstrip("\n")
        if line == "[Term]":
            cur = {"syn": [], "isa": []}
        elif line.startswith("["):
            cur = None
        elif cur is None:
            continue
        elif line.startswith("id: FBbt:"):
            cur["id"] = line[4:]
            terms[cur["id"]] = cur
        elif line.startswith("name: "):
            cur["name"] = line[6:]
        elif line.startswith("def: "):
            cur["def"] = re.match(r'def: "(.*)"', line).group(1).replace('\\"', '"')
        elif line.startswith("synonym: "):
            m = re.match(r'synonym: "(.*)" (\w+)', line)
            cur["syn"].append((m.group(1), m.group(2)))
        elif line.startswith("is_a: FBbt:"):
            cur["isa"].append(line.split()[1])
        elif line == "is_obsolete: true":
            cur["obs"] = True
    return {k: v for k, v in terms.items() if not v.get("obs")}


def main() -> None:
    fbbt = load_obo(REPO_ROOT / ".cache" / "fbbt.obo")
    by_label = {v["name"]: k for k, v in fbbt.items()}
    by_exact = defaultdict(set)
    for k, v in fbbt.items():
        by_exact[v["name"]].add(k)
        for s, scope in v["syn"]:
            if scope == "EXACT":
                by_exact[s].add(k)

    def ancestors(t: str) -> set[str]:
        out, todo = set(), [t]
        while todo:
            for p in fbbt.get(todo.pop(), {}).get("isa", []):
                if p not in out:
                    out.add(p)
                    todo.append(p)
        return out

    def is_neuron(t: str) -> bool:
        return t == NEURON or NEURON in ancestors(t)

    def nearest_immature(t: str) -> str | None:
        """The most specific ancestor of t that has an 'immature <label>' term."""
        cands = [a for a in ancestors(t) if f"immature {fbbt[a]['name']}" in by_label]
        best = [a for a in cands if not any(a in ancestors(b) for b in cands if b != a)]
        return by_label[f"immature {fbbt[best[0]]['name']}"] if len(best) == 1 else None

    stages, less_conf = defaultdict(set), set()
    for r in csv.DictReader((PROJ / "mapping.tsv").open(), delimiter="\t"):
        if r["kind"] == "held":
            continue
        stages[r["type"]].add("immature" if r["clustering"] in IMMATURE else "mature")
        if r.get("author_confidence"):
            less_conf.add(r["type"])

    def entry(typ, tid, match, conf, justification, other=(), new_term=False, searches=()):
        bm = {"fbbt_term": fbbt[tid]["name"], "fbbt_id": tid, "fbbt_definition": fbbt[tid].get("def", ""),
              "match_type": match, "skos_mapping": {"exact match": "skos:exactMatch",
                                                     "broad match": "skos:broadMatch"}[match],
              "confidence": conf}
        return {
            "cluster_label": typ,
            "working_definition": f"Author type '{typ}' of the Özel et al. 2021 optic lobe atlas "
                                  f"(Supplementary Table 1).",
            "searches_performed": list(searches) or [f"'{typ}' (exact label / exact synonym, {RELEASE})"],
            "best_match": bm,
            "justification": justification,
            "other_candidates": [{"fbbt_term": fbbt[o]["name"], "fbbt_id": o,
                                  "fbbt_definition": fbbt[o].get("def", ""), "reason_rejected": why}
                                 for o, why in other],
            "recommendation": f"Map to {tid} '{fbbt[tid]['name']}' ({match}).",
            "new_term_needed": new_term,
            "verification_needed": typ in less_conf,
        }

    out = {"mature": {}, "immature": {}}
    for typ, groups in sorted(stages.items()):
        if re.fullmatch(r"G\d+[a-z]*", typ):
            for g in groups:
                tid, lab = GLIA[g]
                out[g][typ] = entry(
                    typ, tid, "broad match", "high",
                    f"A glial identity the authors left numbered ({typ}); class glia. "
                    + ("The dissection is the optic lobe only, so adult optic lobe glial cell is exact "
                       "for the class (curator rule: narrow by dissected tissue where exact)."
                       if g == "mature" else
                       "FBbt has no immature or pupal optic lobe glia term; the stage-neutral glial cell "
                       "is used (as for Kurmangaliyev 2020 early glia)."),
                    searches=[f"'{lab}' ({RELEASE})"])
            continue
        if typ in AMBIGUOUS:
            continue
        hits = [t for t in by_exact.get(typ, ()) if is_neuron(t)]
        if len(hits) != 1:
            continue                                      # not a single neuron term: agents
        tid = hits[0]
        if typ in TRANSIENT:
            for g in groups:
                out[g][typ] = entry(typ, tid, "exact match", "high",
                                    f"'{typ}' is an exact synonym of {tid} '{fbbt[tid]['name']}', a pupal "
                                    f"type defined from this paper; the same term at every stage it occurs.")
            continue
        if "mature" in groups:
            out["mature"][typ] = entry(typ, tid, "exact match", "high",
                                       f"'{typ}' is the exact label or an exact synonym of {tid} "
                                       f"'{fbbt[tid]['name']}'.")
        if "immature" in groups:
            imm = by_label.get(f"immature {fbbt[tid]['name']}")
            if imm:
                out["immature"][typ] = entry(
                    typ, imm, "exact match", "high",
                    f"'{typ}' is {tid} '{fbbt[tid]['name']}'; at P15-P40 the cells are developing, so its "
                    f"immature form {imm} (curator: immature terms up to the pupal stage).",
                    other=[(tid, "Mature form; used from the pharate adult stage.")])
            else:
                par = nearest_immature(tid)
                if par is None:
                    continue                              # agents
                out["immature"][typ] = entry(
                    typ, par, "broad match", "medium",
                    f"'{typ}' is {tid} '{fbbt[tid]['name']}', which has no immature form in FBbt; at "
                    f"P15-P40 the cells are developing (curator: immature terms up to the pupal stage), so "
                    f"the most specific ancestor with an immature form is used: {par} "
                    f"'{fbbt[par]['name']}' (as for Kurmangaliyev 2020 early clusters).",
                    other=[(tid, "Mature form, used from the pharate adult stage; no immature form in FBbt.")],
                    new_term=True)

    n = 0
    for group, maps in out.items():
        d = PROJ / "type_mapping" / ("immature" if group == "immature" else "")
        d.mkdir(parents=True, exist_ok=True)
        for typ, m in maps.items():
            f = d / f"{label_slug(typ)}.fbbt_mapping.json"
            if f.exists() and json.loads(f.read_text()).get("manual_edit"):
                continue
            f.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
            n += 1
    left = {g: sorted(t for t, gs in stages.items() if g in gs and t not in out[g]) for g in out}
    print(f"wrote {n} type mappings (mature {len(out['mature'])}, immature {len(out['immature'])})")
    for g, ts in left.items():
        print(f"  for the agents ({g}, {len(ts)}): {ts}")


if __name__ == "__main__":
    main()
