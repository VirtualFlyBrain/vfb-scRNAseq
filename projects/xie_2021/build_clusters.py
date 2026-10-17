#!/usr/bin/env python
"""Xie et al. 2021: cell_type_annotations.json from the authors' annotated h5ads (GEO).

The authors typed each cell (`PN_type`) at each stage, matching types across stages
(Figures 5-6): the main pan-PN analysis (GSE161228_adata_all_panPN_annotated_final.h5ad)
and the knot analysis (GSE161228_knot_24h_48h_adult.h5ad). One entry per analysis x
stage x PN type, the authors' per-stage typed clusters.

  label              <clustering>_<PN type> (clustering: main_0h, ..., knot_adult)
  type               the authors' PN type (e.g. "DA1_fru+", "VM7 or VM5v #1", "vPN")
  source_cluster_id  the PN type
  unannotated        cells the authors gave no type ("nan" / "NaN": held, unassigned) and
                     types left numbered ("MARS_<n>": held, untyped)
  cells_by_sample    cells per Sample (a main-analysis 24 h cell is in a Li 2017 sort)

Also writes .cache/xie/memberships.tsv.gz (cell<TAB>cluster) for the expression build.

Usage:
    uv run python projects/xie_2021/build_clusters.py
"""

from __future__ import annotations

import csv
import gzip
import json
import re
from collections import Counter
from pathlib import Path

import h5py
import yaml

PROJ = Path(__file__).resolve().parent
REPO_ROOT = PROJ.parents[1]
CACHE = REPO_ROOT / ".cache" / "xie"
H5ADS = {"main": "all.h5ad", "knot": "knot_24h_48h_adult.h5ad"}   # GEO GSE161228_adata_all_panPN_annotated_final / _knot_24h_48h_adult
UNTYPED = re.compile(r"MARS_\d+")


def obs(path: Path) -> tuple[list[str], dict[str, list[str]]]:
    f = h5py.File(path, "r")
    o = f["obs"]

    def col(name):
        v = o[name]
        if isinstance(v, h5py.Group):                # anndata >= 0.8 categoricals
            cats = [c.decode() if isinstance(c, bytes) else c for c in v["categories"][:]]
            return [cats[c] if c >= 0 else "nan" for c in v["codes"][:]]
        vals = v[:]
        if "categories" in v.attrs:                  # anndata 0.7 categoricals
            cats = [c.decode() if isinstance(c, bytes) else c for c in o["__categories"][name][:]]
            return [cats[c] if c >= 0 else "nan" for c in vals]
        return [x.decode() if isinstance(x, bytes) else str(x) for x in vals]
    return [x.decode() for x in o["_index"][:]], {c: col(c) for c in ("stage", "PN_type")}


def main() -> None:
    cfg = yaml.safe_load((PROJ / "config.yaml").read_text())
    cname = {c["id"]: c["name"] for c in cfg["sample_build"]["clusterings"]}
    sort_of = {p: s["id"] for p, s in cfg["sample_build"]["sorts"].items()}
    with gzip.open(REPO_ROOT / ".cache" / "li2017" / "df_libs.csv.gz", "rt") as fh:
        li = {r["library"]: f"exp{r['experiment']}_GH146_24hAPF" for r in csv.DictReader(fh)
              if r["label"] == "GH146-GFP"}

    def sample_of(cell: str) -> str:
        if cell in li:
            return f"li_2017:{li[cell]}"
        prefix = re.sub(r"(_P\d+)?_[A-P]\d+$", "", cell)
        prefix = {"PN_24h_KnotGAL4": "PN_24h_KnotGAL4_GH146"}.get(prefix, prefix)
        return sort_of[prefix]

    groups: dict[tuple[str, str], list[str]] = {}
    for analysis, f in H5ADS.items():
        cells, cols = obs(CACHE / f)
        for cell, stage, typ in zip(cells, cols["stage"], cols["PN_type"]):
            stage = stage.replace(" APF", "")
            groups.setdefault((f"{analysis}_{stage}", "unassigned" if typ in ("nan", "NaN") else typ), []).append(cell)

    order = [c["id"] for c in cfg["sample_build"]["clusterings"]]
    anns, membership = [], []
    for cid, typ in sorted(groups, key=lambda k: (order.index(k[0]), k[1].lower())):
        cells = groups[(cid, typ)]
        label = f"{cid}_{typ}"
        rec = {"label": label, "type": typ, "clustering": cid, "clustering_name": cname[cid],
               "source_cluster_id": typ, "cell_number": len(cells),
               "cells_by_sample": dict(sorted(Counter(sample_of(c) for c in cells).items()))}
        if typ == "unassigned" or UNTYPED.fullmatch(typ):
            rec["unannotated"] = True
        anns.append(rec)
        membership += [(c, label) for c in cells]
    with gzip.open(CACHE / "memberships.tsv.gz", "wt") as fh:
        fh.write("barcode\tcluster\n")
        fh.writelines(f"{c}\t{label}\n" for c, label in membership)
    out = {
        "source": {"doi": cfg["source"]["doi"], "title": cfg["source"]["title"]},
        "dataset": {
            "accession": cfg["dataset"]["accession"],
            "label_source": "authors' annotated h5ads on GEO (GSE161228): obs `PN_type` per cell and "
                            "`stage`, main pan-PN and knot analyses",
            "label_level": "author type per analysis and stage",
            "validate_against": "paper, Figures 2, 5-6",
        },
        "annotations": anns,
    }
    (PROJ / "cell_type_annotations.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    by = Counter(a["clustering"] for a in anns)
    held = sum(1 for a in anns if a.get("unannotated"))
    print(f"wrote {len(anns)} entries ({dict(by)}), {len(membership)} cells; {held} held")


if __name__ == "__main__":
    main()
