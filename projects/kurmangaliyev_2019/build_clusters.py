#!/usr/bin/env python
"""Kurmangaliyev 2019: cell_type_annotations.json from the authors' per-stage clusters.

The authors analysed the 24 h and 48 h APF libraries separately and assigned each
stage's eight clusters to the subtypes T4a-d / T5a-d. GEO (GSE126139) has one per-cell
file per library, GSM*_clust24.txt / GSM*_clust48.txt (barcode<TAB>cluster: the subtype,
or "filtered" for cells removed by the authors' quality control). A cell's stage (its
library) and subtype give its author cluster: one entry per stage x subtype.

  label              <stage>_<subtype> (e.g. 24h_T4a)
  type               "<subtype> neuron" (the type name in Hörmann 2020's type mappings)
  clustering         the stage (24h, 48h)
  source_cluster_id  the subtype label (the authors give the per-stage clusters no numbers)
  cells_by_library   cells per GEO library (GSM title)

Also writes .cache/kurmangaliyev_2019/memberships.tsv.gz (cell<TAB>cluster, cells named
<stage>_<10x barcode>, as in the combined matrix of combine_matrices.py) for the
expression build.

Usage:
    uv run python projects/kurmangaliyev_2019/build_clusters.py
"""

from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

import yaml

PROJ = Path(__file__).resolve().parent
REPO_ROOT = PROJ.parents[1]
CACHE = REPO_ROOT / ".cache" / "kurmangaliyev_2019"
GEO = CACHE / "geo"
GEO_URL = "https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM3592nnn/{gsm}/suppl/{file}"
# stage -> (GSM, GEO library title, per-cell cluster file)
LIBRARIES = {
    "24h": ("GSM3592259", "T4/T5 24h APF", "GSM3592259_clust24.txt.gz"),
    "48h": ("GSM3592260", "T4/T5 48h APF", "GSM3592260_clust48.txt.gz"),
}


def main() -> None:
    cfg = yaml.safe_load((PROJ / "config.yaml").read_text())
    names = {c["id"]: c["name"] for c in cfg["sample_build"]["clusterings"]}
    anns, members = [], []
    for stage, (gsm, title, fname) in LIBRARIES.items():
        path = GEO / fname
        if not path.exists():
            raise SystemExit(f"missing {path}: download {GEO_URL.format(gsm=gsm, file=fname)}")
        cells: dict[str, list[str]] = {}
        with gzip.open(path, "rt") as fh:
            assert fh.readline().split() == ["barcode", "cluster"]
            for line in fh:
                barcode, cluster = line.split()
                if cluster == "filtered":
                    continue
                assert re.fullmatch(r"T[45][a-d]", cluster), cluster
                cells.setdefault(cluster, []).append(f"{stage}_{barcode}-1")
        assert len(cells) == 8, (stage, sorted(cells))
        for subtype in sorted(cells):
            label = f"{stage}_{subtype}"
            anns.append({
                "label": label,
                "type": f"{subtype} neuron",
                "clustering": stage,
                "clustering_name": names[stage],
                "source_cluster_id": subtype,
                "cell_number": len(cells[subtype]),
                "cells_by_library": {title: len(cells[subtype])},
            })
            members += [(c, label) for c in cells[subtype]]
    with gzip.open(CACHE / "memberships.tsv.gz", "wt") as fh:
        fh.write("barcode\tcluster\n")
        for c, label in members:
            fh.write(f"{c}\t{label}\n")
    out = {
        "source": {"doi": cfg["source"]["doi"], "title": cfg["source"]["title"]},
        "dataset": {
            "accession": cfg["dataset"]["accession"],
            "label_source": "the authors' per-cell cluster files on GEO (GSM3592259_clust24.txt, "
                            "GSM3592260_clust48.txt: each cell's subtype, per stage)",
            "label_level": "author cluster (one per stage x subtype)",
            "validate_against": "paper (per-stage clusters assigned to the eight subtypes)",
        },
        "annotations": anns,
    }
    (PROJ / "cell_type_annotations.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(anns)} clusters, {len(members)} cells")


if __name__ == "__main__":
    main()
