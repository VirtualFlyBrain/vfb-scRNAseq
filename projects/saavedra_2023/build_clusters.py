#!/usr/bin/env python
"""Saavedra et al. 2023: cell_type_annotations.json from the authors' clusters (controls).

The authors clustered all six libraries together (Seurat 4.3, Harmony, resolution 0.3: 17
clusters, annotated against the Fly Cell Atlas). Their per-nucleus clusters are on GEO
(GSE227038_2023-02-21_metadata_Pedro_thorax_10K_final.csv: barcode, "<n>_<name>", library),
for all 45,335 nuclei the paper reports. Curator 2026-10-20: control nuclei only (libraries
wt1 and wt2, one Sample).

  label              the authors' cluster as given (e.g. "0_Indirect flight muscle")
  type               the name (e.g. "Indirect flight muscle")
  source_cluster_id  the cluster number
  unannotated        "Unknown cluster" (held: untyped)
  cells_by_library   control nuclei per library (wt1, wt2)
  all_genotypes_cell_number  the cluster's nuclei in all six libraries

Also writes .cache/saavedra/memberships.tsv.gz (nucleus<TAB>cluster; nuclei named
<library>_<barcode>) for the expression build.

Usage:
    uv run python projects/saavedra_2023/build_clusters.py
"""

from __future__ import annotations

import csv
import gzip
import json
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import yaml

PROJ = Path(__file__).resolve().parent
CACHE = PROJ.parents[1] / ".cache" / "saavedra"
META = CACHE / "GSE227038_2023-02-21_metadata_Pedro_thorax_10K_final.csv.gz"
META_URL = ("https://ftp.ncbi.nlm.nih.gov/geo/series/GSE227nnn/GSE227038/suppl/"
            "GSE227038_2023-02-21_metadata_Pedro_thorax_10K_final.csv.gz")
CONTROLS = ("wt1", "wt2")
PAPER_NUCLEI = 45335
HELD = "Unknown cluster"


def main() -> None:
    cfg = yaml.safe_load((PROJ / "config.yaml").read_text())
    (clustering,) = cfg["sample_build"]["clusterings"]
    if not META.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(META_URL, META)
    cells: dict[str, list[str]] = defaultdict(list)
    total: Counter = Counter()
    n = 0
    with gzip.open(META, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            n += 1
            total[r["Cluster"]] += 1
            if r["Sample"] in CONTROLS:
                cells[r["Cluster"]].append(f"{r['Sample']}_{r['Barcode']}")
    if n != PAPER_NUCLEI or len(total) != 17 or set(cells) != set(total):
        raise SystemExit(f"expected the authors' 17 clusters / {PAPER_NUCLEI} nuclei: {len(total)} / {n}")
    anns = []
    for lab in sorted(cells, key=lambda x: int(x.split("_", 1)[0])):
        num, name = lab.split("_", 1)
        rec = {"label": lab, "type": name, "clustering": clustering["id"], "clustering_name": clustering["name"],
               "source_cluster_id": num, "cell_number": len(cells[lab]),
               "cells_by_library": dict(sorted(Counter(c.split("_", 1)[0] for c in cells[lab]).items())),
               "all_genotypes_cell_number": total[lab]}
        if name == HELD:
            rec["unannotated"] = True
        anns.append(rec)
    with gzip.open(CACHE / "memberships.tsv.gz", "wt") as fh:
        fh.write("barcode\tcluster\n")
        for a in anns:
            fh.writelines(f"{c}\t{a['label']}\n" for c in cells[a["label"]])
    out = {
        "source": {"doi": cfg["source"]["doi"], "title": cfg["source"]["title"]},
        "dataset": {
            "accession": cfg["dataset"]["accession"],
            "label_source": "the authors' per-nucleus clusters in their GEO metadata file "
                            "(GSE227038_2023-02-21_metadata_Pedro_thorax_10K_final.csv), control libraries only",
            "label_level": "author cluster (restricted to the control nuclei)",
            "validate_against": "paper, Figure 3a",
        },
        "annotations": anns,
    }
    (PROJ / "cell_type_annotations.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(anns)} clusters, {sum(a['cell_number'] for a in anns)} control nuclei of {n}; "
          f"held {[a['label'] for a in anns if a.get('unannotated')]}")


if __name__ == "__main__":
    main()
