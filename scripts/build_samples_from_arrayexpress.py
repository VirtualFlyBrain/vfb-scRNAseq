#!/usr/bin/env python
"""Build Sample / Assay / Clustering / Dataset metadata for a project from ArrayExpress.

The ArrayExpress counterpart of build_samples_from_geo.py, writing the same
projects/<name>/samples.json. Config-driven (`sample_build` in config.yaml):

  sample_columns   SDRF columns whose values together define one biological Sample
                   (e.g. [Extract Name] for FCA 10x; organism part + sex + genotype +
                   age for FCA Smart-seq2, where every cell is its own SDRF source)
  assay_column     SDRF column whose distinct values are the Assays (libraries), or
  assay_regex      {column, pattern} with a named group `assay` (e.g. the Smart-seq2
                   plate parsed from the cell name)
  assay_xrefs      SDRF columns recorded as Assay dbxrefs when single-valued per assay
                   (ENA experiment, BioSamples); per-cell ids are not listed
  sample_label_id  regex on the sample id; group 1 (the authors' sample id, e.g.
                   FCA4) is added to the Sample label, to tell like samples apart
  sex_column / sex_map, age_column / age_map, tissue_column / tissue_map,
  genotype_columns / stock_map / genotype_includes_map, assay_method, clusterings
  sdrf_corrections [{match: {column: value}, set: {column: value}, note}] curator
                   fixes to SDRF values (e.g. an age contradicted by the paper),
                   applied before grouping; the note is kept on the affected Samples

Values come from the authors' SDRF annotations (curator decision: tissue and sex
follow the authors, not inferred from drivers). Minted VFBseq ids are idempotent on
dataset-scoped natural keys; ArrayExpress/ENA/BioSamples ids are xrefs, never IRIs.

Usage:
    uv run python scripts/build_samples_from_arrayexpress.py --project li_2022_fca_10x
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vfb_scrnaseq.ids import IDRegistry  # noqa: E402
from vfb_scrnaseq.ingest_arrayexpress import fetch_experiment  # noqa: E402
from vfb_scrnaseq.project_config import clustering_samples, load_config, reused_samples  # noqa: E402


def assay_key(row: dict, sb: dict) -> str | None:
    if sb.get("assay_regex"):
        rx = sb["assay_regex"]
        m = re.search(rx["pattern"], row.get(rx["column"], ""))
        return m.group("assay") if m else None
    return row.get(sb["assay_column"]) or None


def single(values: set[str]) -> str | None:
    vals = {v for v in values if v}
    return vals.pop() if len(vals) == 1 else None


def apply_corrections(rows: list[dict], corrections: list[dict]) -> list[dict]:
    """Copies of the rows with curator `sdrf_corrections` applied; each corrected row
    carries the notes in `_notes`."""
    out = []
    for r in rows:
        r = dict(r)
        for c in corrections:
            if all(r.get(k) == v for k, v in c["match"].items()):
                r.update(c["set"])
                r.setdefault("_notes", []).append(c["note"])
        out.append(r)
    return out


def build(rows: list[dict], sb: dict, accession: str, reg: IDRegistry, dataset_id: str):
    """Group SDRF rows into samples and assays; returns (samples, assays, warnings)."""
    warnings = []
    rows = apply_corrections(rows, sb.get("sdrf_corrections", []))
    for c in sb.get("sdrf_corrections", []):
        if not any(all(r.get(k) == v for k, v in c["set"].items()) and c["note"] in r.get("_notes", [])
                   for r in rows):
            warnings.append(f"sdrf_correction matched no rows: {c['match']}")
    by_sample: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        by_sample[tuple(r.get(c, "") for c in sb["sample_columns"])].append(r)

    samples_out, assays_out = [], []
    for key in sorted(by_sample):
        members = by_sample[key]
        sample_id = " | ".join(k for k in key if k)

        def one(col):
            v = single({m.get(col, "") for m in members}) if col else None
            if col and v is None:
                warnings.append(f"sample {sample_id!r}: {col} not single-valued")
            return v

        tissue_raw = one(sb.get("tissue_column"))
        sex_raw = one(sb.get("sex_column"))
        age_raw = one(sb.get("age_column"))
        genotype = " ; ".join(v for v in (one(c) for c in sb.get("genotype_columns", [])) if v) or None

        sex = sb.get("sex_map", {}).get(sex_raw, sex_raw) if sex_raw else None
        if sex not in ("male", "female"):
            sex = None                              # mixed / unknown -> unset
        age = sb.get("age_map", {}).get(age_raw, {}) if age_raw else {}
        if age_raw and not age:
            warnings.append(f"sample {sample_id!r}: no age_map entry for {age_raw!r}")
        tissues = sb.get("tissue_map", {}).get(tissue_raw)
        if tissue_raw and tissues is None:
            warnings.append(f"sample {sample_id!r}: no tissue_map entry for {tissue_raw!r}")
        stock = sb.get("stock_map", {}).get(genotype) if genotype else None
        # FlyBase genetic entities of a cross (`genotype_includes_map`, keyed like stock_map)
        geno_parts = sb.get("genotype_includes_map", {}).get(genotype) if genotype else None
        if genotype and genotype not in sb.get("wild_type_genotypes", []) and not (stock or geno_parts):
            warnings.append(f"sample {sample_id!r}: genotype {genotype!r} has no stock_map or "
                            f"genotype_includes_map entry")

        sample_vid = reg.mint("Sample", f"{accession}:{sample_id}", label=sample_id)
        by_assay: dict[str, list[dict]] = defaultdict(list)
        for m in members:
            k = assay_key(m, sb)
            if k is None:
                warnings.append(f"sample {sample_id!r}: row without an assay key")
                continue
            by_assay[k].append(m)
        assay_vids = []
        for akey in sorted(by_assay):
            arows = by_assay[akey]
            vid = reg.mint("Assay", f"{accession}:{akey}", label=akey)
            assay_vids.append(vid)
            xrefs = [v for v in (single({r.get(c, "") for r in arows}) for c in sb.get("assay_xrefs", [])) if v]
            assays_out.append({
                "vfbseq_id": vid,
                "library_id": akey,
                "accession": xrefs[0] if xrefs else None,
                "dbxrefs": xrefs,
                "n_sources": len({r.get("Source Name", "") for r in arows}),
                "method": sb["assay_method"],
                "sample_vfbseq_id": sample_vid,
                "associated_dataset": dataset_id,
            })
        label_bits = [tissue_raw, f"{age_raw} {sb.get('age_unit', 'days')}" if age_raw else None, sex_raw,
                      genotype if genotype and genotype not in sb.get("wild_type_genotypes", []) else None]
        if sb.get("sample_label_id"):
            # the authors' own sample id, to tell apart samples that are otherwise alike
            m = re.search(sb["sample_label_id"], sample_id)
            if not m:
                raise SystemExit(f"sample_label_id {sb['sample_label_id']!r} does not match {sample_id!r}")
            label_bits.append(m.group(1))
        notes = sorted({n for m in members for n in m.get("_notes", [])})
        rec = {
            "vfbseq_id": sample_vid,
            "sample_id": sample_id,
            "label": ", ".join(b for b in label_bits if b),
            "tissue_raw": tissue_raw,
            "age_raw": f"{age_raw} {sb.get('age_unit', 'days')}" if age_raw else None,
            "genotype": genotype,
            "stock": stock,
            **({"genotype_includes": geno_parts} if geno_parts else {}),
            "sex": sex,
            "stage": age.get("stage"),
            "sample_tissue": tissues,
            "associated_dataset": dataset_id,
            "assay_vfbseq_ids": assay_vids,
            "n_assays": len(assay_vids),
        }
        if notes:
            rec["curation_notes"] = notes
        samples_out.append(rec)
    return samples_out, assays_out, warnings


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    cfg = load_config(args.project)
    sb = cfg["sample_build"]
    accession = cfg["dataset"]["accession"]
    site = cfg["dataset"].get("site", "ArrayExpress")

    reused = reused_samples(cfg)        # stops first if a source study is not curated yet
    idf, rows = fetch_experiment(accession)
    reg = IDRegistry.load(REPO_ROOT / "id_registry" / "registry.json")
    title = (idf.get("Investigation Title") or [accession])[0]
    dataset_id = reg.mint("Dataset", accession, label=title, accession=accession)

    samples_out, assays_out, warnings = build(rows, sb, accession, reg, dataset_id)
    for w in sorted(set(warnings))[:30]:
        print(f"  WARNING: {w}", file=sys.stderr)

    clusterings_out = []
    for entry in sb.get("clusterings", []):
        subset = entry["id"] if isinstance(entry, dict) else entry
        name = entry.get("name") if isinstance(entry, dict) else None
        cid = reg.mint("Clustering", f"{accession}:{subset}", label=name or f"{accession} {subset} clustering")
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
