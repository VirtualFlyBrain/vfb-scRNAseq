#!/usr/bin/env python
"""Xie et al. 2021: samples.json from the GEO family SOFT file (GSE161228).

GEO has one sample (GSM) per cell, titled "PN_<stage>_<driver>[_<plate>]_<well>". The sorts
in scope (config `sample_build.sorts`, keyed by title prefix) become Samples, their plates
Assays. The main analysis's 24 h cells are Li et al. 2017's: those Samples are reused from
li_2017 by VFBseq id (config `reuse`; the source must be curated).

Usage:
    uv run python projects/xie_2021/build_samples.py
"""

from __future__ import annotations

import gzip
import json
import re
import urllib.request
from collections import defaultdict
from pathlib import Path

import yaml

from vfb_scrnaseq.ids import IDRegistry
from vfb_scrnaseq.ingest import parse_soft
from vfb_scrnaseq.project_config import reused_samples

PROJ = Path(__file__).resolve().parent
REPO_ROOT = PROJ.parents[1]
CACHE = REPO_ROOT / ".cache" / "xie"
SOFT = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE161nnn/GSE161228/soft/GSE161228_family.soft.gz"
TITLE = re.compile(r"(?P<prefix>.+?)(?:_(?P<plate>P\d+))?_(?P<well>[A-P]\d+)")


def main() -> None:
    cfg = yaml.safe_load((PROJ / "config.yaml").read_text())
    cfg["_project"] = cfg["project"]
    sb, acc = cfg["sample_build"], cfg["dataset"]["accession"]
    reused = reused_samples(cfg)                      # stops first if li_2017 is not curated
    CACHE.mkdir(parents=True, exist_ok=True)
    if not (CACHE / "GSE161228_family.soft.gz").exists():
        urllib.request.urlretrieve(SOFT, CACHE / "GSE161228_family.soft.gz")
    series = parse_soft(gzip.open(CACHE / "GSE161228_family.soft.gz", "rt").read())
    reg = IDRegistry.load(REPO_ROOT / "id_registry" / "registry.json")
    dataset_id = reg.mint("Dataset", acc, label=series.title, accession=acc)

    groups: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))  # sample -> plate -> GSMs
    for g in series.samples:
        m = TITLE.fullmatch(g.title)
        if m and m["prefix"] in sb["sorts"]:
            sid = sb["sorts"][m["prefix"]]["id"]
            plate = m["plate"] or "P1"
            if m["prefix"] == "PN_0h_VT":
                plate = m["plate"]                    # PN_0h_VT_P8: plate P8 of the 0 h sort
            groups[sid][plate].append(g)
    sorts = {s["id"]: s for s in sb["sorts"].values()}
    samples, assays = [], []
    for sid in sorted(groups):
        s, st = sorts[sid], sb["stages"][sorts[sid]["stage"]]
        svid = reg.mint("Sample", f"{acc}:{sid}", label=sid)
        avids = []
        for plate in sorted(groups[sid], key=lambda p: int(p[1:])):
            avid = reg.mint("Assay", f"{acc}:{sid}:{plate}", label=f"{sid} {plate}")
            avids.append(avid)
            assays.append({"vfbseq_id": avid, "library_id": f"plate {plate}", "accession": None,
                           "dbxrefs": [], "n_sources": len(groups[sid][plate]),
                           "method": sb["assay_method"], "sample_vfbseq_id": svid,
                           "associated_dataset": dataset_id})
        samples.append({
            "vfbseq_id": svid, "sample_id": sid,
            "label": f"{st['tissue']['label']}, {st['age']}, {s['name']}",
            "tissue_raw": None, "age_raw": st["age"], "genotype": s["name"], "stock": None,
            "genotype_includes": s["genotype_includes"], "sex": None, "stage": st["stage"],
            "sample_tissue": [st["tissue"]], "associated_dataset": dataset_id,
            "assay_vfbseq_ids": avids, "n_assays": len(avids),
        })
    by_id = {s["sample_id"]: s["vfbseq_id"] for s in samples}
    clusterings = []
    for c in sb["clusterings"]:
        cid = reg.mint("Clustering", f"{acc}:{c['id']}", label=c["name"])
        used = [r["vfbseq_id"] for r in reused] if c.get("reused") else [by_id[s] for s in c["samples"]]
        clusterings.append({"vfbseq_id": cid, "subset": c["id"], "associated_dataset": dataset_id,
                            "name": c["name"], "samples": used})
    out = {"dataset": {"vfbseq_id": dataset_id, "accession": acc, "site": cfg["dataset"]["site"]},
           "samples": samples, "assays": assays, "clusterings": clusterings, "reused_samples": reused}
    (PROJ / "samples.json").write_text(json.dumps(out, indent=2) + "\n")
    reg.save()
    print(f"wrote {len(samples)} samples ({sum(a['n_sources'] for a in assays)} cells), {len(assays)} assays, "
          f"{len(clusterings)} clusterings, {len(reused)} reused samples")


if __name__ == "__main__":
    main()
