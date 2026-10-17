#!/usr/bin/env python
"""Li, Horns et al. 2017: samples.json from GEO GSE100058 and the authors' library table.

GEO has one sample (GSM) per cell, titled "<driver> [<library>]", without the stage. The
authors' library table (GSE100058_df_libs.csv.gz) gives each library its sort
(`experiment`), Smart-seq2 `plate` and driver / stage `label` (e.g. "Mz19-GFP,48hAPF";
GH146 sorts are all 24 h APF). Samples are the sorts in scope (driver in
`sample_build.drivers`): one per experiment x label; Assays are their plates (or the
pooled sequencing library where no plate is recorded). Every library in scope must
have its GEO sample (checked). The cluster build maps cells to Samples from the same table.

Usage:
    uv run python projects/li_2017/build_samples.py
"""

from __future__ import annotations

import csv
import gzip
import json
import re
import urllib.request
from collections import defaultdict
from pathlib import Path

import yaml

from vfb_scrnaseq.ids import IDRegistry
from vfb_scrnaseq.ingest import parse_soft

PROJ = Path(__file__).resolve().parent
REPO_ROOT = PROJ.parents[1]
CACHE = REPO_ROOT / ".cache" / "li2017"
GEO = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE100nnn/GSE100058"
FILES = {"GSE100058_family.soft.gz": f"{GEO}/soft/GSE100058_family.soft.gz",
         "df_libs.csv.gz": f"{GEO}/suppl/GSE100058_df_libs.csv.gz"}


def main() -> None:
    cfg = yaml.safe_load((PROJ / "config.yaml").read_text())
    sb, acc = cfg["sample_build"], cfg["dataset"]["accession"]
    CACHE.mkdir(parents=True, exist_ok=True)
    for name, url in FILES.items():
        if not (CACHE / name).exists():
            urllib.request.urlretrieve(url, CACHE / name)
    series = parse_soft(gzip.open(CACHE / "GSE100058_family.soft.gz", "rt").read())
    gsm = {}
    for g in series.samples:
        m = re.fullmatch(r".+ \[(.+)\]", g.title)
        if m:
            gsm[m.group(1)] = g
    with gzip.open(CACHE / "df_libs.csv.gz", "rt") as fh:
        libs = list(csv.DictReader(fh))
    reg = IDRegistry.load(REPO_ROOT / "id_registry" / "registry.json")
    dataset_id = reg.mint("Dataset", acc, label=series.title, accession=acc)

    groups: dict[tuple[int, str, str], list[dict]] = defaultdict(list)
    for r in libs:
        driver, _, stage = r["label"].partition(",")
        if driver not in sb["drivers"]:
            continue                                  # controls: not in the analyses loaded
        groups[(int(r["experiment"]), driver, stage or "24hAPF")].append(r)

    samples, assays = [], []
    for (exp, driver, stage) in sorted(groups):
        rows = groups[(exp, driver, stage)]
        st, drv = sb["stages"][stage], sb["drivers"][driver]
        sample_id = f"exp{exp}_{driver.removesuffix('-GFP')}_{stage}"
        svid = reg.mint("Sample", f"{acc}:{sample_id}", label=sample_id)
        by_plate: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            plate = r["plate"].split(".")[0] if r["plate"] else f"pool {r['pooled_library']}"
            by_plate[plate].append(r)
        avids = []
        for plate in sorted(by_plate):
            avid = reg.mint("Assay", f"{acc}:{sample_id}:{plate}", label=f"{sample_id} {plate}")
            avids.append(avid)
            assays.append({
                "vfbseq_id": avid,
                "library_id": plate if plate.startswith("pool") else f"plate {plate}",
                "accession": None,
                "dbxrefs": [],
                "n_sources": len(by_plate[plate]),
                "method": sb["assay_method"],
                "sample_vfbseq_id": svid,
                "associated_dataset": dataset_id,
            })
        samples.append({
            "vfbseq_id": svid,
            "sample_id": sample_id,
            "label": f"{st['tissue']['label']}, {st['age']}, {drv['name']}, sort {exp}",
            "tissue_raw": None,
            "age_raw": st["age"],
            "genotype": drv["name"],
            "stock": None,
            "genotype_includes": drv["genotype_includes"],
            "sex": None,
            "stage": st["stage"],
            "sample_tissue": [st["tissue"]],
            "associated_dataset": dataset_id,
            "assay_vfbseq_ids": avids,
            "n_assays": len(avids),
        })
        missing = [r["library"] for r in rows if r["library"] not in gsm]
        if missing:
            raise SystemExit(f"{sample_id}: libraries without a GEO sample: {missing[:5]}")

    clusterings = []
    for c in sb["clusterings"]:
        cid = reg.mint("Clustering", f"{acc}:{c['id']}", label=c["name"])
        used = [s["vfbseq_id"] for s in samples
                if s["sample_id"].split("_")[1] == c["driver"].removesuffix("-GFP")
                and (not c.get("stage") or s["sample_id"].endswith("_" + c["stage"]))]
        clusterings.append({"vfbseq_id": cid, "subset": c["id"], "associated_dataset": dataset_id,
                            "name": c["name"], "samples": used})
    out = {"dataset": {"vfbseq_id": dataset_id, "accession": acc, "site": cfg["dataset"]["site"]},
           "samples": samples, "assays": assays, "clusterings": clusterings}
    (PROJ / "samples.json").write_text(json.dumps(out, indent=2) + "\n")
    reg.save()
    print(f"wrote {len(samples)} samples ({sum(len(v) for v in groups.values())} cells), "
          f"{len(assays)} assays, {len(clusterings)} clusterings")


if __name__ == "__main__":
    main()
