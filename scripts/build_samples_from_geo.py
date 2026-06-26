#!/usr/bin/env python
"""Build Sample / Assay / Clustering / Dataset metadata for a project from GEO.

Config-driven (see the `sample_build` section of config.yaml). Parses GSM titles
(`set_timepoint_biorep_techrep`) into biological Samples and their 10x-library
Assays, attaches FBdv stage + FBbt tissue (per the curated timepoint map),
genotype, and assay method, mints stable VFBseq IDs (idempotent registry), and
writes projects/<name>/samples.json. GEO/SRA accessions are dbxrefs, never IRIs.

Usage:
    python scripts/build_samples_from_geo.py --project kurmangaliyev_2020
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vfb_scrnaseq.ids import IDRegistry  # noqa: E402
from vfb_scrnaseq.ingest import fetch_series  # noqa: E402
from vfb_scrnaseq.project_config import load_config  # noqa: E402


def parse_title(title: str) -> dict | None:
    """set_timepoint_biorep_techrep -> components (techrep may contain underscores)."""
    parts = (title or "").split("_")
    if len(parts) < 4:
        return None
    return {
        "set": parts[0],
        "timepoint": parts[1],
        "biorep": parts[2],
        "techrep": "_".join(parts[3:]),
        "sample_id": "_".join(parts[:3]),  # biological sample = set_timepoint_biorep
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    cfg = load_config(args.project)
    sb = cfg["sample_build"]
    accession = cfg["dataset"]["accession"]
    site = cfg["dataset"].get("site", "GEO")

    series = fetch_series(accession)
    reg = IDRegistry.load(REPO_ROOT / "id_registry" / "registry.json")

    dataset_id = reg.mint("Dataset", accession, label=series.title, accession=accession)

    # group GSMs into biological samples and libraries (assays)
    libraries = []   # (parsed, GeoSample)
    by_sample: dict[str, list] = defaultdict(list)
    for gsm in series.samples:
        p = parse_title(gsm.title)
        if not p:
            print(f"  WARNING: cannot parse title {gsm.title!r} ({gsm.accession})", file=sys.stderr)
            continue
        libraries.append((p, gsm))
        by_sample[p["sample_id"]].append((p, gsm))

    # build samples (sorted for stable id minting)
    samples_out, assays_out = [], []
    for sample_id in sorted(by_sample):
        members = by_sample[sample_id]
        p0 = members[0][0]
        tp = sb["timepoint_map"].get(p0["timepoint"], {})
        sample_vid = reg.mint("Sample", sample_id, label=sample_id)
        assay_vids = []
        for p, gsm in sorted(members, key=lambda m: m[1].accession):
            assay_vid = reg.mint("Assay", gsm.accession, label=p["techrep"], accession=gsm.accession)
            assay_vids.append(assay_vid)
            assays_out.append({
                "vfbseq_id": assay_vid,
                "library_id": gsm.title,
                "accession": gsm.accession,
                "sra": gsm.relations.get("SRA"),
                "biosample": gsm.relations.get("BioSample"),
                "method": sb["assay_method"],
                "sample_vfbseq_id": sample_vid,
                "associated_dataset": dataset_id,
            })
        samples_out.append({
            "vfbseq_id": sample_vid,
            "sample_id": sample_id,
            "set": p0["set"],
            "timepoint": p0["timepoint"],
            "biorep": p0["biorep"],
            "genotype": sb.get("genotype_map", {}).get(p0["set"]),
            "sex": None,
            "stage": tp.get("stage"),
            "sample_tissue": tp.get("tissue"),
            "associated_dataset": dataset_id,
            "assay_vfbseq_ids": assay_vids,
            "n_assays": len(assay_vids),
        })

    clusterings_out = []
    for subset in sb.get("clusterings", []):
        cid = reg.mint("Clustering", f"{accession}:{subset}", label=f"{accession} {subset} clustering")
        clusterings_out.append({
            "vfbseq_id": cid,
            "subset": subset,
            "associated_dataset": dataset_id,
        })

    out = {
        "dataset": {"vfbseq_id": dataset_id, "accession": accession, "site": site},
        "samples": samples_out,
        "assays": assays_out,
        "clusterings": clusterings_out,
    }
    out_path = REPO_ROOT / "projects" / args.project / "samples.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    reg.save()
    print(f"wrote {len(samples_out)} samples, {len(assays_out)} assays, "
          f"{len(clusterings_out)} clusterings -> {out_path}")


if __name__ == "__main__":
    main()
