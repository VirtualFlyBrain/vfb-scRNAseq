#!/usr/bin/env python
"""Mokashi et al. 2021: cell_type_annotations.json from the authors' clusters (reference cells).

The authors integrated all 8 samples and clustered them together (Seurat v3, resolution
0.9: clusters 0-42). Their complete per-cell table is in the Single Cell Expression Atlas
FTP folder (E-GEOD-172231.cells.txt: run, barcode, the authors' "Inferred cell type",
cluster, SCEA's standardised "authors labels"): 104,984 cells, as the authors' script's
filters keep, every sample's count equal. Curator 2026-10-19/21: reference-medium cells
only.

  label              <cluster>_<the authors' inferred cell type> (e.g. "8_GABAergic neurons")
  type               the authors' inferred cell type, first letter capitalised (their own
                     wording; SCEA's standardised label kept as author_scea_label)
  source_cluster_id  the cluster number
  unannotated        "Undetermined" (held: untyped)
  cells_by_sample    reference cells per Sample
  all_samples_cell_number  the cluster's cells in all 8 samples

Also writes .cache/mokashi/memberships.tsv.gz (cell<TAB>cluster; cells
<GEO sample dir>_<barcode>-1, as in combine_matrices.py) for the expression build.

Usage:
    uv run python projects/mokashi_2021/build_clusters.py
"""

from __future__ import annotations

import csv
import json
import gzip
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import yaml

PROJ = Path(__file__).resolve().parent
CACHE = PROJ.parents[1] / ".cache" / "mokashi"
CELLS = CACHE / "scea_cells.txt"
CELLS_URL = ("https://ftp.ebi.ac.uk/pub/databases/microarray/data/atlas/sc_experiments/"
             "E-GEOD-172231/E-GEOD-172231.cells.txt")
REFERENCE = {   # ENA run -> (Sample id, GEO sample directory)
    "SRR14253618": ("Female_Reference_1", "1_F_R_1"), "SRR14253620": ("Female_Reference_2", "3_F_R_2"),
    "SRR14253622": ("Male_Reference_1", "5_M_R_1"), "SRR14253616": ("Male_Reference_2", "7_M_R_2")}
AUTHOR_CELLS, AUTHOR_CLUSTERS = 104984, 43
HELD = "Undetermined"


def main() -> None:
    cfg = yaml.safe_load((PROJ / "config.yaml").read_text())
    (clustering,) = cfg["sample_build"]["clusterings"]
    if not CELLS.exists():
        urllib.request.urlretrieve(CELLS_URL, CELLS)
    cells: dict[str, list[tuple[str, str]]] = defaultdict(list)
    total: Counter = Counter()
    typ, scea = {}, {}
    with open(CELLS, newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            clu = r["cluster"]
            total[clu] += 1
            t = r["Inferred cell type"].strip()
            typ.setdefault(clu, set()).add(t[0].upper() + t[1:])
            scea.setdefault(clu, set()).add(r["inferred cell type - authors labels"])
            if r["ENA RUN"] in REFERENCE:
                cells[clu].append((r["ENA RUN"], r["cell barcode"]))
    if sum(total.values()) != AUTHOR_CELLS or len(total) != AUTHOR_CLUSTERS or set(cells) != set(total):
        raise SystemExit(f"expected the authors' {AUTHOR_CLUSTERS} clusters / {AUTHOR_CELLS} cells: "
                         f"{len(total)} / {sum(total.values())}")
    anns = []
    for clu in sorted(cells, key=int):
        (t,), lab = typ[clu], scea[clu]
        rec = {"label": f"{clu}_{t}", "type": t, "clustering": clustering["id"],
               "clustering_name": clustering["name"], "source_cluster_id": clu, "cell_number": len(cells[clu]),
               "cells_by_sample": dict(sorted(Counter(REFERENCE[run][0] for run, _ in cells[clu]).items())),
               "all_samples_cell_number": total[clu], "author_scea_label": "; ".join(sorted(lab))}
        if t == HELD:
            rec["unannotated"] = True
        anns.append(rec)
    with gzip.open(CACHE / "memberships.tsv.gz", "wt") as fh:
        fh.write("barcode\tcluster\n")
        for a in anns:
            fh.writelines(f"{REFERENCE[run][1]}_{bc}-1\t{a['label']}\n" for run, bc in cells[a["source_cluster_id"]])
    out = {
        "source": {"doi": cfg["source"]["doi"], "title": cfg["source"]["title"]},
        "dataset": {
            "accession": cfg["dataset"]["accession"],
            "label_source": "the authors' complete per-cell table in SCEA (E-GEOD-172231.cells.txt): cluster and the "
                            "authors' inferred cell type; reference-medium cells only",
            "label_level": "author cluster (restricted to the reference cells)",
            "validate_against": "paper, Figure 4; the authors' script (filters keep 104,984 cells)",
        },
        "annotations": anns,
    }
    (PROJ / "cell_type_annotations.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(anns)} clusters, {sum(a['cell_number'] for a in anns)} reference cells of {AUTHOR_CELLS}; "
          f"held {sum(1 for a in anns if a.get('unannotated'))}; {len({a['type'] for a in anns})} types")


if __name__ == "__main__":
    main()
