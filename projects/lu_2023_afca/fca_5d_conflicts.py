#!/usr/bin/env python
"""AFCA review aid: where the FCA typed an AFCA type's 5-day cells as something else.

The AFCA's 5-day cells are FCA 10x head/body cells, and the authors' files carry both
annotations (`fca_annotation`, `afca_annotation`). For each mapped AFCA type, any FCA
label covering >= 20% of its 5-day cells is compared by FBbt term (the FCA's
type-level mapping vs this project's): the same term, or a broader one (an is_a /
part_of ancestor, i.e. the FCA head/body call was coarser), is expected; anything
else is listed in fca_5d_conflicts.tsv for the curator. "unannotated" is ignored.

This is information only: the AFCA label is the authors' typing for these clusters
and is mapped as given (general curation rules).

Usage (needs .cache/h5ad/GSE218661/{head,body}.h5ad and .cache/fbbt.obo):
    uv run python projects/lu_2023_afca/fca_5d_conflicts.py
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJ = Path(__file__).resolve().parent
REPO_ROOT = PROJ.parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vfb_scrnaseq.ingest_h5ad import h5ad_path, read_obs  # noqa: E402
from vfb_scrnaseq.project_config import label_slug  # noqa: E402

FCA_TYPES = REPO_ROOT / "projects" / "li_2022_fca_10x" / "type_mapping"
MIN_SHARE = 0.2


def fbbt_parents(obo: Path) -> dict[str, set[str]]:
    par: dict[str, set[str]] = defaultdict(set)
    cur = None
    for line in obo.open():
        if line.startswith("[Term]"):
            cur = None
        elif line.startswith("id: FBbt:"):
            cur = line.split()[1]
        elif cur and line.startswith("is_a: FBbt:"):
            par[cur].add(line.split()[1])
        elif cur and line.startswith("relationship: part_of FBbt:"):
            par[cur].add(line.split()[2])
    return par


def ancestors(term: str, par: dict[str, set[str]]) -> set[str]:
    seen, todo = set(), [term]
    while todo:
        for p in par.get(todo.pop(), ()):
            if p not in seen:
                seen.add(p)
                todo.append(p)
    return seen


def fca_term(label: str) -> str | None:
    f = FCA_TYPES / f"{label_slug(label)}.fbbt_mapping.json"
    return ((json.loads(f.read_text()).get("best_match")) or {}).get("fbbt_id") if f.exists() else None


def main() -> None:
    par = fbbt_parents(REPO_ROOT / ".cache" / "fbbt.obo")
    with (PROJ / "mapping.tsv").open() as fh:
        afca = {(r["clustering"], r["type"]): r["fbbt_id"].split(" | ")[0]
                for r in csv.DictReader(fh, delimiter="\t") if r["fbbt_id"]}
    rows = []
    for clustering in ("head", "body"):
        obs = read_obs(h5ad_path("GSE218661", clustering), ["dataset", "fca_annotation", "afca_annotation"])
        by_type: dict[str, Counter] = defaultdict(Counter)
        for ds, fca, a in zip(obs["dataset"], obs["fca_annotation"], obs["afca_annotation"]):
            if ds == "FCA":
                by_type[a][fca] += 1
        for typ, counts in sorted(by_type.items()):
            term = afca.get((clustering, typ))
            if not term:
                continue
            n = sum(counts.values())
            for fca, k in counts.most_common():
                if fca == "unannotated" or k / n < MIN_SHARE:
                    continue
                ft = fca_term(fca)
                if ft is None or ft == term or ft in ancestors(term, par):
                    continue
                rows.append((clustering, typ, term, n, fca, ft, k, round(k / n, 2)))
    out = PROJ / "fca_5d_conflicts.tsv"
    with out.open("w") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["clustering", "afca_type", "afca_fbbt", "fca_5d_cells", "fca_annotation",
                    "fca_fbbt", "cells", "share"])
        w.writerows(rows)
    print(f"{len(rows)} conflicts -> {out}")


if __name__ == "__main__":
    main()
