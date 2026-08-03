"""Assemble schema-conformant entity records from the curated project data.

Reads the working-format JSON (config.yaml, samples.json, cell_type_annotations.json,
mapping/*.fbbt_mapping.json), mints Cluster IDs, and emits a flat list of entity
records keyed by LinkML **slot names** (the entity IRIs are minted VFBseq IRIs;
GEO/SRA accessions are dbxrefs). :mod:`vfb_scrnaseq.emit` turns these into RDF
using the schema's slot_uri/class_uri.

Object-valued slots carry CURIEs (FBbt:..., FBcv:...) or full IRIs (VFBseq
entities, DOI, licence); literal slots carry plain strings/ints. emit.py decides
IRI-vs-literal from the schema slot range, so build.py just supplies values.

Usage:
    python scripts/build.py --project kurmangaliyev_2020   # thin CLI wrapper
"""

from __future__ import annotations

import json
from pathlib import Path

from vfb_scrnaseq.ids import IDRegistry

REPO_ROOT = Path(__file__).resolve().parents[2]
VFB_BASE = "http://virtualflybrain.org/reports/"
CC_BY_4 = "https://creativecommons.org/licenses/by/4.0/"


def iri(vfbseq_id: str) -> str:
    return VFB_BASE + vfbseq_id


def build_entities(project: str) -> list[dict]:
    proj = REPO_ROOT / "projects" / project
    cfg = _yaml(proj / "config.yaml")
    samples = json.loads((proj / "samples.json").read_text())
    anns = json.loads((proj / "cell_type_annotations.json").read_text())["annotations"]
    src, ds_cfg = cfg.get("source", {}), cfg.get("dataset", {})

    # citation forms used in entity rdfs:labels
    author, year = src.get("first_author"), src.get("year")
    cite = f"{author} ({year})" if author and year else (author or str(year or ""))
    cite_suffix = f" ({author} {year})" if author and year else ""

    reg = IDRegistry.load(REPO_ROOT / "id_registry" / "registry.json")
    entities: list[dict] = []

    # --- Dataset ---
    d = samples["dataset"]
    dataset_iri = iri(d["vfbseq_id"])
    dataset = {
        "type": "Dataset", "id": dataset_iri,
        "name": f"scRNAseq data from {cite}" if cite else d["accession"],
        "title": src.get("title"),
        "accession": d["accession"],
        "neo_label": "DataSet",
    }
    if src.get("doi"):
        dataset["publication"] = f"https://doi.org/{src['doi']}"
    if ds_cfg.get("licence"):
        dataset["licence"] = CC_BY_4
    if ds_cfg.get("assay_type"):
        dataset["assay_type"] = ds_cfg["assay_type"]
    entities.append(dataset)

    # --- Samples ---
    for s in samples["samples"]:
        # name from ORIGINAL GEO info (tissue/age/strain/replicate), not the FBbt/FBdv
        # mapping (which is not 1:1 — e.g. 48h & 72h both map to 'pharate adult stage').
        tissue = s.get("tissue_raw") or (s.get("sample_tissue") or {}).get("label") or "sample"
        age = s.get("age_raw") or s.get("timepoint")
        parts = [p for p in (tissue, age) if p]
        if s.get("set"):
            parts.append(f"{s['set']} rep {s.get('biorep')}" if s.get("biorep") else s["set"])
        descr = ", ".join(parts)
        rec = {
            "type": "Sample", "id": iri(s["vfbseq_id"]),
            "name": (f"{descr}{cite_suffix}" if descr else s["sample_id"]),
            "associated_dataset": dataset_iri,
            "associated_assay": [iri(a) for a in s["assay_vfbseq_ids"]],
            "neo_label": "Sample",
        }
        if s.get("sample_tissue"):
            rec["sample_tissue"] = [s["sample_tissue"]["fbbt_id"]]
        if s.get("stage"):
            rec["stage"] = s["stage"]["fbdv_id"]
        if s.get("genotype"):
            rec["genotype"] = s["genotype"]
        entities.append(rec)

    # --- Assays ---
    for a in samples["assays"]:
        xrefs = [a["accession"]]
        if a.get("sra"):
            xrefs.append(a["sra"])
        if a.get("biosample"):
            xrefs.append(a["biosample"])
        entities.append({
            "type": "Assay", "id": iri(a["vfbseq_id"]),
            "name": a["accession"],
            "method": a["method"]["fbcv_id"],
            "associated_sample_for_assay": [iri(a["sample_vfbseq_id"])],
            "associated_dataset": dataset_iri,
            "dbxref": xrefs,
            "neo_label": "Assay",
        })

    # --- Clusterings ---
    clustering_iri_by_subset = {}
    for c in samples["clusterings"]:
        clustering_iri_by_subset[c["subset"]] = iri(c["vfbseq_id"])
        entities.append({
            "type": "Clustering", "id": iri(c["vfbseq_id"]),
            "name": f"{d['accession']} {c['subset']} clustering",
            "associated_dataset": dataset_iri,
            "neo_label": "Clustering",
        })

    # --- Clusters (annotated clusters belong to the 'main' clustering) ---
    subset = anns_subset(proj)
    main_clustering = clustering_iri_by_subset.get(subset)
    ecf = proj / "expression_counts.json"
    expr_counts = json.loads(ecf.read_text()) if ecf.exists() else {}
    for ann in anns:
        label = ann["label"]
        cid = reg.mint("Cluster", f"{d['accession']}:{subset}:{label}", label=label)
        rec = {
            "type": "Cluster", "id": iri(cid),
            "name": f"{label} cluster{cite_suffix}",
            "associated_clustering": main_clustering,
            "associated_dataset": dataset_iri,
            "cell_number": ann.get("cell_number"),
            "neo_label": "Cluster",
        }
        m = _mapping(proj, label)
        bm = (m or {}).get("best_match") or {}
        if bm.get("fbbt_id"):
            rec["cell_type"] = [bm["fbbt_id"]]
        if label in expr_counts:
            rec["total_gene_count"] = expr_counts[label]["total_gene_count"]
            rec["filtered_gene_count"] = expr_counts[label]["filtered_gene_count"]
        entities.append(rec)

    reg.save()
    return entities


def anns_subset(proj: Path) -> str:
    cta = json.loads((proj / "cell_type_annotations.json").read_text())
    return cta.get("dataset", {}).get("subset", "main")


def _mapping(proj: Path, label: str) -> dict | None:
    f = proj / "mapping" / f"{label}.fbbt_mapping.json"
    return json.loads(f.read_text()) if f.exists() else None


def _yaml(path: Path) -> dict:
    import yaml
    return yaml.safe_load(path.read_text())


def build_project(project: str):
    """Build entity records and write projects/<project>/entities.json."""
    entities = build_entities(project)
    out = REPO_ROOT / "projects" / project / "entities.json"
    out.write_text(json.dumps(entities, indent=2) + "\n")
    return out, entities
