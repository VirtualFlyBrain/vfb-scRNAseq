#!/usr/bin/env python
"""Özel 2021: cell_type_annotations.json from the authors' final identities.

Each stage's Seurat object (exported by export_seurat.R to .cache/ozel/<stage>/)
gives every cell a final identity (`FinalIdents`): an adult cluster number. The
numbers are named in the paper's Supplementary Table 1 (Nature MOESM4,
projects/ozel_2021/supp/, not in git). One entry per (stage, identity) present at
that stage — the authors' unit; the per-stage unsupervised clusters are an
intermediate step.

  label             <stage>_<number> (names repeat across numbers, e.g. six T4/T5)
  type              the authors' name, without the less-confident '*'
  source_cluster_id the number
  author_confidence 'less confident' where the table marks the name with '*'
  class             'glia' for the numbered glial identities (G01, G02, ...)
  unannotated       True for identities the authors left numbered, low-quality ('LQ')
                    identities, and identity 0 (cells given no final identity)
  cells_by_library  cells per library (`orig.ident`)
  author_note       the table's annotation comment for the identity at that stage (the
                    adult comment for the adult, else the pupal one; either as fallback) —
                    e.g. the basis of the Im calls ("... probably immature Tm9")

The P50 object also has `FinalIdents.T45separate`, the authors' split of the T4/T5
identities 234 (T4-5a/b) and 235 (T4-5c/d) into the eight subtypes T4a-d / T5a-d
(identities 261-268, "only in the P50 dataset ... in a separate metadata field"):
these are a further Clustering (`P50_T45`, labels P50_T45_<number>), each a sub-cluster
(`parent_cluster`) of the P50 identity most of its cells had.

Usage:
    uv run --with openpyxl python projects/ozel_2021/build_clusters.py
"""

from __future__ import annotations

import csv
import gzip
import json
import re
from collections import Counter
from pathlib import Path

import openpyxl
import yaml

PROJ = Path(__file__).resolve().parent
REPO_ROOT = PROJ.parents[1]
CACHE = REPO_ROOT / ".cache" / "ozel"
TABLE = PROJ / "supp" / "41586_2020_2879_MOESM4_ESM.xlsx"
STAGE_FILES = {"P15": "P15", "P30": "P30", "P40": "P40", "P50": "P50", "P70": "P70", "adult": "Adult"}
SUBTYPES = ("P50", "FinalIdents.T45separate", "P50_T45")   # stage, column, clustering id


def author_names() -> tuple[dict[str, str], dict[str, tuple[str, str]]]:
    """({cluster number: name as given (may end in '*')}, {number: (adult comment,
    pupal comment)}) from Supplementary Table 1."""
    ws = openpyxl.load_workbook(TABLE, read_only=True)["Annotation"]
    names, notes = {}, {}
    clean = (lambda v: " ".join(str(v).split()) if v else "")
    for row in list(ws.iter_rows(values_only=True))[1:]:
        if row[0] is None:
            continue
        num = str(row[0]).strip()
        names[num] = str(row[1]).strip() if row[1] is not None else ""
        notes[num] = (clean(row[2]), clean(row[3]))
    return names, notes


def note_for(notes: dict[str, tuple[str, str]], num: str, stage: str) -> str:
    adult, pupal = notes.get(num, ("", ""))
    return (adult or pupal) if stage == "adult" else (pupal or adult)


def is_low_quality(name: str) -> bool:
    return bool(re.search(r"(^|/)LQ\d*( \(in pupae\))?$", name))


def is_numbered(name: str, num: str) -> bool:
    """Left numbered by the authors: the number itself, or a number with a letter
    suffix for its parts (e.g. 88a / 88b)."""
    return not name or name == num or bool(re.fullmatch(r"\d+[a-z]?", name))


def main() -> None:
    cfg = yaml.safe_load((PROJ / "config.yaml").read_text())
    names = {c["id"]: c["name"] for c in cfg["sample_build"]["clusterings"]}
    table, notes = author_names()
    anns, unknown = [], set()
    for stage, folder in STAGE_FILES.items():
        with gzip.open(CACHE / folder / "metadata.tsv.gz", "rt") as fh:
            rows = list(csv.DictReader(fh, delimiter="\t"))
        cells = Counter(r["FinalIdents"] for r in rows)
        libs: dict[str, Counter] = {}
        for r in rows:
            libs.setdefault(r["FinalIdents"], Counter())[r["orig.ident"]] += 1
        for num in sorted(cells, key=lambda x: int(x)):
            given = table.get(num)
            if given is None and num != "0":
                unknown.add(num)
            name = (given or "").rstrip("*").strip()
            rec = {
                "label": f"{stage}_{num}",
                "type": name or num,
                "clustering": stage,
                "clustering_name": names[stage],
                "source_cluster_id": num,
                "cell_number": cells[num],
                "cells_by_library": dict(sorted(libs[num].items(), key=lambda kv: (len(kv[0]), kv[0]))),
            }
            if given and given.endswith("*"):
                rec["author_confidence"] = "less confident"
            if note_for(notes, num, stage):
                rec["author_note"] = note_for(notes, num, stage)
            if re.fullmatch(r"G\d+[a-z]*", name):
                rec["class"] = "glia"
            if num == "0":
                rec["type"] = "0"
                rec["unannotated"] = True            # no final identity
            elif is_numbered(name, num) or is_low_quality(name):
                rec["unannotated"] = True            # left numbered, or low quality
            anns.append(rec)
    # P50 T4/T5 subtypes: identities that FinalIdents.T45separate adds
    stage, col, sub = SUBTYPES
    with gzip.open(CACHE / STAGE_FILES[stage] / "metadata.tsv.gz", "rt") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    main_ids = {r["FinalIdents"] for r in rows}
    parent: dict[str, Counter] = {}
    libs = {}
    for r in rows:
        n = r[col]
        if n not in main_ids:
            parent.setdefault(n, Counter())[r["FinalIdents"]] += 1
            libs.setdefault(n, Counter())[r["orig.ident"]] += 1
    for num in sorted(parent, key=int):
        given = table.get(num)
        if given is None:
            unknown.add(num)
        anns.append({
            "label": f"{sub}_{num}",
            "type": (given or num).rstrip("*").strip(),
            "clustering": sub,
            "clustering_name": names[sub],
            "source_cluster_id": num,
            "cell_number": sum(parent[num].values()),
            "cells_by_library": dict(sorted(libs[num].items(), key=lambda kv: (len(kv[0]), kv[0]))),
            "parent_cluster": f"{stage}_{parent[num].most_common(1)[0][0]}",
            **({"author_note": note_for(notes, num, stage)} if note_for(notes, num, stage) else {}),
        })
    if unknown:
        raise SystemExit(f"identities not in Supplementary Table 1: {sorted(unknown, key=int)}")
    out = {
        "source": {"doi": cfg["source"]["doi"], "title": cfg["source"]["title"]},
        "dataset": {
            "accession": cfg["dataset"]["accession"],
            "label_source": "authors' Seurat objects (GEO GSE142787) obs `FinalIdents`, named from "
                            "Supplementary Table 1",
            "label_level": "author final identity (one entry per identity per stage)",
            "validate_against": "paper and Supplementary Table 1",
        },
        "annotations": anns,
    }
    (PROJ / "cell_type_annotations.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    by = Counter(a["clustering"] for a in anns)
    held = sum(1 for a in anns if a.get("unannotated"))
    print(f"wrote {len(anns)} entries ({dict(by)}); {held} held (numbered / LQ / 0)")


if __name__ == "__main__":
    main()
