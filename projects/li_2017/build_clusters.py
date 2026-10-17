#!/usr/bin/env python
"""Li, Horns et al. 2017: cell_type_annotations.json from the authors' repository files.

- GH146 24 h APF: one entry per HDBSCAN cluster (FlyPN data/labels_HDBSCAN.csv, 0-29) and
  one for the cells left unclustered (-1). Clusters the paper decoded are typed from
  config `decoded_clusters` (linked to the paper's figure labels by match_clusters.py);
  the rest stay numbered (held: untyped); the unclustered cells are held (unassigned).
- Mz19 developmental series: one entry per type per stage, from the authors' per-type,
  per-stage cell lists (config `mz19_lists`).

  label              GH146_24h_<n> / GH146_24h_unclustered; Mz19_<stage>_<type>
  type               the PN type (DA1, VA1d, DC3, DC2, VM2, DL3, "VA1d or DC3"), else the label
  source_cluster_id  the HDBSCAN number; the type for Mz19 (the authors' lists are by type)
  author_note        for decoded GH146 clusters: the paper's figure label and the basis
  cells_by_sample    cells per Sample (sort)

Also writes .cache/li2017/memberships.tsv.gz (library<TAB>cluster) for the expression build.

Usage:
    uv run python projects/li_2017/build_clusters.py
"""

from __future__ import annotations

import csv
import gzip
import json
from collections import Counter
from pathlib import Path

import yaml

PROJ = Path(__file__).resolve().parent
CACHE = PROJ.parents[1] / ".cache" / "li2017"


def names(f: str) -> list[str]:
    return [ln.strip() for ln in (CACHE / f).read_text().splitlines() if ln.strip()]


def main() -> None:
    cfg = yaml.safe_load((PROJ / "config.yaml").read_text())
    cname = {c["id"]: c["name"] for c in cfg["sample_build"]["clusterings"]}
    with gzip.open(CACHE / "df_libs.csv.gz", "rt") as fh:
        libs = {r["library"]: r for r in csv.DictReader(fh)}

    def sample_of(lib: str) -> str:
        r = libs[lib]
        driver, _, stage = r["label"].partition(",")
        return f"exp{r['experiment']}_{driver.removesuffix('-GFP')}_{stage or '24hAPF'}"

    groups: dict[tuple[str, str], list[str]] = {}     # (clustering, label) -> libraries
    meta: dict[str, dict] = {}
    with open(CACHE / "labels_HDBSCAN.csv") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            n = r["label"]
            label = "GH146_24h_unclustered" if n == "-1" else f"GH146_24h_{n}"
            groups.setdefault(("GH146_24h", label), []).append(r["name"])
            if label not in meta:
                dec = cfg["decoded_clusters"].get(n)
                meta[label] = {"source_cluster_id": n, "type": dec["type"] if dec else label}
                if dec:
                    meta[label]["author_note"] = f"paper cluster {dec['figure']} ({dec['type']}): {dec['basis']}"
                elif n == "-1":
                    meta[label].update(type="unclustered", unannotated=True)
                else:
                    meta[label]["unannotated"] = True            # left numbered by the authors
    stage_ids = {"24hAPF": "24h", "36hAPF": "36h", "48hAPF": "48h", "72hAPF": "72h", "adult": "adult"}
    for stage, lists in cfg["mz19_lists"].items():
        cid = f"Mz19_{stage_ids[stage]}"
        for typ, f in lists.items():
            label = f"{cid}_{typ.replace(' ', '_')}"
            groups[(cid, label)] = names(f)
            meta[label] = {"source_cluster_id": typ, "type": typ}

    anns, membership = [], []
    order = [c["id"] for c in cfg["sample_build"]["clusterings"]]
    def key(k):
        cid, label = k
        n = meta[label]["source_cluster_id"]
        return (order.index(cid), int(n) if n.lstrip("-").isdigit() else 999, label)
    for cid, label in sorted(groups, key=key):
        cells = groups[(cid, label)]
        missing = [c for c in cells if c not in libs]
        if missing:
            raise SystemExit(f"{label}: cells not in the library table: {missing[:5]}")
        anns.append({"label": label, "clustering": cid, "clustering_name": cname[cid],
                     **meta[label], "cell_number": len(cells),
                     "cells_by_sample": dict(sorted(Counter(sample_of(c) for c in cells).items()))})
        membership += [(c, label) for c in cells]
    with gzip.open(CACHE / "memberships.tsv.gz", "wt") as fh:
        fh.write("barcode\tcluster\n")
        fh.writelines(f"{c}\t{label}\n" for c, label in membership)
    out = {
        "source": {"doi": cfg["source"]["doi"], "title": cfg["source"]["title"]},
        "dataset": {
            "accession": cfg["dataset"]["accession"],
            "label_source": "authors' repository (github.com/felixhorns/FlyPN data/): GH146 HDBSCAN "
                            "clusters (labels_HDBSCAN.csv), decoded clusters linked to the paper's "
                            "figure labels by the authors' criteria; Mz19 per-type, per-stage cell lists",
            "label_level": "author cluster (GH146) / author type per stage (Mz19)",
            "validate_against": "paper, Figures 3-4 and 6",
        },
        "annotations": anns,
    }
    (PROJ / "cell_type_annotations.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    by = Counter(a["clustering"] for a in anns)
    held = sum(1 for a in anns if a.get("unannotated"))
    print(f"wrote {len(anns)} entries ({dict(by)}), {len(membership)} cell memberships; {held} held")


if __name__ == "__main__":
    main()
