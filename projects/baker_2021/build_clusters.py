#!/usr/bin/env python
"""Baker et al. 2021: cell_type_annotations.json from the authors' clusters (sucrose cells).

The authors integrated all 8 samples and clustered them together (Seurat v3, resolution
0.8: clusters 0-35). Their complete per-cell table is in the Single Cell Expression Atlas
FTP folder (E-GEOD-152495.cells.txt: run, barcode, the authors' "Inferred cell type",
cluster, SCEA's standardised "authors labels"): 86,223 cells, as the authors' script's
filters keep (the paper 86,224), every sample's count equal. Curator 2026-10-19/21:
sucrose (control) cells only.

  label              <cluster>_<the authors' inferred cell type> (e.g. "1_GABAergic neurons")
  type               the authors' inferred cell type, first letter capitalised (their own
                     wording; SCEA's standardised label kept as author_scea_label)
  source_cluster_id  the cluster number
  unannotated        "Undetermined" (held: untyped)
  cells_by_sample    sucrose cells per Sample
  all_samples_cell_number  the cluster's cells in all 8 samples

Also writes .cache/baker/memberships.tsv.gz (cell<TAB>cluster; cells
<GEO sample dir>_<barcode>-1, as in combine_matrices.py) for the expression build.

Usage:
    uv run python projects/baker_2021/build_clusters.py
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
CACHE = PROJ.parents[1] / ".cache" / "baker"
CELLS = CACHE / "scea_cells.txt"
CELLS_URL = ("https://ftp.ebi.ac.uk/pub/databases/microarray/data/atlas/sc_experiments/"
             "E-GEOD-152495/E-GEOD-152495.cells.txt")
CONTROLS = {   # ENA run -> (Sample id, GEO sample directory): the sucrose (control) samples
    "SRR12016929": ("Female_Sucrose_1", "1_S1_L001"), "SRR12016930": ("Female_Sucrose_2", "2_S2_L001"),
    "SRR12016931": ("Male_Sucrose_1", "3_S3_L001"), "SRR12016932": ("Male_Sucrose_2", "4_S4_L001")}
AUTHOR_CELLS, AUTHOR_CLUSTERS = 86223, 36
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
            if r["ENA RUN"] in CONTROLS:
                cells[clu].append((r["ENA RUN"], r["cell barcode"]))
    if sum(total.values()) != AUTHOR_CELLS or len(total) != AUTHOR_CLUSTERS or set(cells) != set(total):
        raise SystemExit(f"expected the authors' {AUTHOR_CLUSTERS} clusters / {AUTHOR_CELLS} cells: "
                         f"{len(total)} / {sum(total.values())}")
    anns = []
    for clu in sorted(cells, key=int):
        (t,), lab = typ[clu], scea[clu]
        rec = {"label": f"{clu}_{t}", "type": t, "clustering": clustering["id"],
               "clustering_name": clustering["name"], "source_cluster_id": clu, "cell_number": len(cells[clu]),
               "cells_by_sample": dict(sorted(Counter(CONTROLS[run][0] for run, _ in cells[clu]).items())),
               "all_samples_cell_number": total[clu], "author_scea_label": "; ".join(sorted(lab))}
        if t == HELD:
            rec["unannotated"] = True
        anns.append(rec)
    with gzip.open(CACHE / "memberships.tsv.gz", "wt") as fh:
        fh.write("barcode\tcluster\n")
        for a in anns:
            fh.writelines(f"{CONTROLS[run][1]}_{bc}-1\t{a['label']}\n" for run, bc in cells[a["source_cluster_id"]])
    out = {
        "source": {"doi": cfg["source"]["doi"], "title": cfg["source"]["title"]},
        "dataset": {
            "accession": cfg["dataset"]["accession"],
            "label_source": "the authors' complete per-cell table in SCEA (E-GEOD-152495.cells.txt): cluster and the "
                            "authors' inferred cell type; sucrose (control) cells only",
            "label_level": "author cluster (restricted to the sucrose cells)",
            "validate_against": "paper; the authors' script (filters keep 86,223 cells)",
        },
        "annotations": anns,
    }
    (PROJ / "cell_type_annotations.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(anns)} clusters, {sum(a['cell_number'] for a in anns)} sucrose cells of {AUTHOR_CELLS}; "
          f"held {sum(1 for a in anns if a.get('unannotated'))}; {len({a['type'] for a in anns})} types")


if __name__ == "__main__":
    main()
