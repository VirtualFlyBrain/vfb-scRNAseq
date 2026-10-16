#!/usr/bin/env python
"""Build Sample / Assay / Clustering / Dataset metadata for a project from GEO.

Config-driven (see the `sample_build` section of config.yaml). Parses GSM titles
(per `sample_build.title_pattern`: `set_timepoint_biorep_techrep` by default, or a
named-group `regex:`; non-matching GSMs are out of scope) into biological Samples
and their 10x-library Assays, attaches FBdv stage + FBbt tissue (per the curated timepoint map),
genotype, and assay method, mints stable VFBseq IDs (idempotent registry), and
writes projects/<name>/samples.json. GEO/SRA accessions are dbxrefs, never IRIs.

Usage:
    uv run python scripts/build_samples_from_geo.py --project kurmangaliyev_2020
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vfb_scrnaseq.ids import IDRegistry  # noqa: E402
from vfb_scrnaseq.ingest import fetch_series  # noqa: E402
from vfb_scrnaseq.project_config import (  # noqa: E402
    clustering_samples,
    load_config,
    reused_samples,
)


def normalize_sex(raw: str | None) -> str | None:
    """Map a raw GEO/config sex string onto the schema enum ('male'/'female')."""
    if not raw:
        return None
    r = raw.strip().lower()
    if r in ("female", "f", "females"):
        return "female"
    if r in ("male", "m", "males"):
        return "male"
    return None  # unrecognised -> treat as unknown (unset)


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


def title_parser(pattern: str | None) -> Callable[[str], dict | None]:
    """Return a GSM-title parser for `sample_build.title_pattern`.

    - ``set_timepoint_biorep_techrep`` (default): underscore-split, see parse_title.
    - ``regex:<pattern>``: full-match regex with named groups ``timepoint`` and
      ``biorep``, and optionally ``set`` (strain/genotype group) and ``techrep``. Without ``techrep`` each GSM is its own
      biological sample (one library per sample). Any further named groups (e.g.
      ``tissue``) also go into the sample id, after ``set``. GSMs whose title does not match
      are not part of this dataset's scope and are skipped.
    """
    if pattern in (None, "set_timepoint_biorep_techrep"):
        return parse_title
    if not pattern.startswith("regex:"):
        raise ValueError(f"unknown sample_build.title_pattern: {pattern!r}")
    rx = re.compile(pattern[len("regex:"):])

    def parse(title: str) -> dict | None:
        m = rx.fullmatch(title or "")
        if not m:
            return None
        g = m.groupdict()
        extra = [v for k, v in g.items() if k not in ("set", "timepoint", "biorep", "techrep")]
        return {
            "set": g.get("set"),
            "timepoint": g["timepoint"],
            "biorep": g["biorep"],
            "techrep": g.get("techrep"),
            "sample_id": "_".join(v for v in (g.get("set"), *extra, g["timepoint"], g["biorep"]) if v),
        }
    return parse


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    cfg = load_config(args.project)
    sb = cfg["sample_build"]
    accession = cfg["dataset"]["accession"]
    site = cfg["dataset"].get("site", "GEO")

    reused = reused_samples(cfg)        # stops first if a source study is not curated yet
    series = fetch_series(accession)
    reg = IDRegistry.load(REPO_ROOT / "id_registry" / "registry.json")

    dataset_id = reg.mint("Dataset", accession, label=series.title, accession=accession)

    # group GSMs into biological samples and libraries (assays)
    parse = title_parser(sb.get("title_pattern"))
    libraries = []   # (parsed, GeoSample)
    by_sample: dict[str, list] = defaultdict(list)
    unmatched = []
    for gsm in series.samples:
        p = parse(gsm.title)
        if not p:
            unmatched.append(gsm)
            continue
        libraries.append((p, gsm))
        by_sample[p["sample_id"]].append((p, gsm))
    if unmatched:
        shown = ", ".join(f"{g.accession} {g.title!r}" for g in unmatched[:5])
        print(f"  NOTE: {len(unmatched)} GSM(s) do not match sample_build.title_pattern and "
              f"are out of scope (e.g. {shown}{', ...' if len(unmatched) > 5 else ''})",
              file=sys.stderr)

    # build samples (sorted for stable id minting)
    samples_out, assays_out = [], []
    for sample_id in sorted(by_sample):
        members = by_sample[sample_id]
        p0 = members[0][0]
        gsm0 = members[0][1]  # original GEO characteristics (consistent within a sample)
        age_raw = gsm0.stage_hint
        tp = sb["age_map"].get(age_raw, {})
        if not tp:
            print(f"  WARNING: no age_map entry for age {age_raw!r} (sample {sample_id}); "
                  f"stage/tissue left unset", file=sys.stderr)

        # Sex: prefer the GEO characteristic; fall back to a curator-confirmed
        # `sample_build.sex` in config (used when GEO carries no sex). If neither is
        # present, leave unset and prompt the curator to check the paper.
        # `sample_build.sex: mixed` = curator-confirmed pooled-sex sample: left unset
        # (the schema sex slot is single-valued male/female), without the warning.
        geo_sex = normalize_sex(gsm0.sex_hint)
        cfg_sex = normalize_sex(sb.get("sex"))
        cfg_mixed = str(sb.get("sex", "")).strip().lower() == "mixed"
        sex = geo_sex or cfg_sex
        if geo_sex is None and cfg_sex is None and not cfg_mixed:
            print(f"  WARNING: sex not in GEO metadata for sample {sample_id!r} and no "
                  f"`sample_build.sex` in config; CURATOR should check the paper for the "
                  f"sex of the animals and set `sample_build.sex` (sex left unset)",
                  file=sys.stderr)
        elif geo_sex and cfg_sex and geo_sex != cfg_sex:
            print(f"  WARNING: sample {sample_id!r} GEO sex {geo_sex!r} disagrees with "
                  f"config `sample_build.sex` {cfg_sex!r}; using GEO value", file=sys.stderr)
        # natural keys are dataset-scoped (accession prefix) so they never collide
        # across projects/datasets (e.g. a 'DGRP_All_A' sample in another GEO series).
        sample_vid = reg.mint("Sample", f"{accession}:{sample_id}", label=sample_id)
        assay_vids = []
        for p, gsm in sorted(members, key=lambda m: m[1].accession):
            assay_vid = reg.mint("Assay", f"{accession}:{gsm.accession}",
                                 label=p["techrep"] or gsm.title, accession=gsm.accession)
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
            "tissue_raw": gsm0.characteristic("tissue"),   # original GEO characteristics
            "age_raw": gsm0.stage_hint,
            "stock": sb.get("stock_map", {}).get(p0["set"]),  # FlyBase FBst ref(s)
            "sex": sex,
            "stage": tp.get("stage"),
            # `sample_build.tissue_map` (keyed on the GEO tissue characteristic) when
            # one series covers several tissues at each age; else the age_map tissue
            "sample_tissue": sb.get("tissue_map", {}).get(gsm0.characteristic("tissue"),
                                                          tp.get("tissue")),
            "associated_dataset": dataset_id,
            "assay_vfbseq_ids": assay_vids,
            "n_assays": len(assay_vids),
        })
        if samples_out[-1]["set"] is None:
            del samples_out[-1]["set"]                 # no strain/genotype group in the titles

    clusterings_out = []
    # entries are a subset name, or {id, name} for a described clustering
    for entry in sb.get("clusterings", []):
        subset = entry["id"] if isinstance(entry, dict) else entry
        name = entry.get("name") if isinstance(entry, dict) else None
        cid = reg.mint("Clustering", f"{accession}:{subset}",
                       label=name or f"{accession} {subset} clustering")
        rec = {"vfbseq_id": cid, "subset": subset, "associated_dataset": dataset_id}
        if name:
            rec["name"] = name
        used = clustering_samples(entry, samples_out, reused)
        if used:
            rec["samples"] = used
        clusterings_out.append(rec)

    out = {
        "dataset": {"vfbseq_id": dataset_id, "accession": accession, "site": site},
        "samples": samples_out,
        "assays": assays_out,
        "clusterings": clusterings_out,
    }
    if reused:
        out["reused_samples"] = reused
    out_path = REPO_ROOT / "projects" / args.project / "samples.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    reg.save()
    print(f"wrote {len(samples_out)} samples, {len(assays_out)} assays, "
          f"{len(clusterings_out)} clusterings"
          f"{f', {len(reused)} reused samples' if reused else ''} -> {out_path}")


if __name__ == "__main__":
    main()
