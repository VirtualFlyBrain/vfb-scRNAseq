"""Assemble schema-conformant entity records from the curated project data.

Reads the working-format JSON (config.yaml, samples.json, cell_type_annotations.json,
mapping/*.fbbt_mapping.json), mints Cluster IDs, and emits a flat list of entity
records keyed by LinkML **slot names** (the entity IRIs are minted VFBseq IRIs;
GEO/SRA accessions are dbxrefs). :mod:`vfb_scrnaseq.emit` turns these into RDF
using the schema's slot_uri/class_uri.

Object-valued slots carry CURIEs (FBbt:..., FBcv:...) or full IRIs (VFBseq
entities, DOI, licence); literal slots carry plain strings/ints. emit.py decides
IRI-vs-literal from the schema slot range, so build.py just supplies values.

Usage (via the CLI wrapper):
    uv run python scripts/build_rdf.py --project kurmangaliyev_2020
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from vfb_scrnaseq.ids import IDRegistry
from vfb_scrnaseq.project_config import fbbt_mapping
from vfb_scrnaseq.pub import resolve_pub

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

    # gene counts from the expression phase (if computed): dataset-level -> Dataset,
    # per-cluster -> each Cluster. Written by scripts/build_expression.py.
    ecf = proj / "expression_counts.json"
    expr_counts = json.loads(ecf.read_text()) if ecf.exists() else {}
    clu_counts = expr_counts.get("clusters", expr_counts)  # tolerate the older flat shape
    ds_counts = expr_counts.get("dataset")

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
    if d.get("site"):
        # VFB Site node CURIE (e.g. GEO -> vfb:GEO = http://virtualflybrain.org/reports/GEO);
        # the schema's `site` owl.fstring emits hasDbXref->site annotated with the accession.
        dataset["site"] = f"vfb:{d['site']}"
    if ds_cfg.get("licence"):
        dataset["licence"] = CC_BY_4
    if ds_cfg.get("assay_type"):
        dataset["assay_type"] = ds_cfg["assay_type"]
    if ds_counts:
        dataset["total_gene_count"] = ds_counts["total_gene_count"]
        dataset["filtered_gene_count"] = ds_counts["filtered_gene_count"]

    # Publication: link the Dataset to an existing VFB :pub node (FlyBase FBrf).
    # Check the VFB curation KB by PMID first (catches freshly-added pubs), then
    # fall back to a curator-supplied source.fbrf in config.
    pub = resolve_pub(pmid=src.get("pmid"), doi=src.get("doi"),
                      fallback_fbrf=src.get("fbrf"))
    if pub:
        pub_curie = f"FlyBase:{pub['fbrf']}"
        dataset["publication"] = pub_curie
        entities.append({
            "type": "Publication", "id": pub_curie, "neo_label": "pub",
        })
        print(f"  linked publication {pub['fbrf']} (via {pub['source']})", file=sys.stderr)
    else:
        print(f"  WARNING: no VFB :pub node found for PMID {src.get('pmid')!r} in the KB "
              f"and no `source.fbrf` in config; Dataset left without a publication link. "
              f"Curator should add the pub to VFB or set `source.fbrf`.", file=sys.stderr)
    entities.append(dataset)

    # --- Samples ---
    sample_descr: dict[str, str] = {}              # sample VFBseq id -> description (Assay names)
    for s in samples["samples"]:
        # name from ORIGINAL GEO info (tissue/age/strain/replicate), not the FBbt/FBdv
        # mapping (which is not 1:1 — e.g. 48h & 72h both map to 'pharate adult stage').
        # one or several FBbt tissues per sample (e.g. FCA "mixed proboscis and maxillary palpus")
        st = s.get("sample_tissue")
        tissues = st if isinstance(st, list) else ([st] if st else [])
        if s.get("label"):
            descr = s["label"]                     # builder-supplied (e.g. ArrayExpress samples)
        else:
            tissue = s.get("tissue_raw") or (tissues[0]["label"] if tissues else "sample")
            # `sample_build.tissue_labels`: display name for a raw tissue, e.g. GEO
            # "P70 optic lobe" -> "optic lobe" when the stage is already in the label
            tissue = ((cfg.get("sample_build") or {}).get("tissue_labels") or {}).get(tissue, tissue)
            age = s.get("age_raw") or s.get("timepoint")
            parts = [p for p in (tissue, age) if p]
            if s.get("set"):
                parts.append(f"{s['set']} rep {s.get('biorep')}" if s.get("biorep") else s["set"])
            elif s.get("biorep"):
                parts.append(f"rep {s['biorep']}")
            descr = ", ".join(parts)
        sample_descr[s["vfbseq_id"]] = descr
        rec = {
            "type": "Sample", "id": iri(s["vfbseq_id"]),
            "name": (f"{descr}{cite_suffix}" if descr else s["sample_id"]),
            "associated_dataset": dataset_iri,
            "associated_assay": [iri(a) for a in s["assay_vfbseq_ids"]],
            "neo_label": "Sample",
        }
        if tissues:
            rec["sample_tissue"] = [t["fbbt_id"] for t in tissues]
        if s.get("stage"):
            rec["stage"] = s["stage"]["fbdv_id"]
        if s.get("stock"):
            # FlyBase stock refs: bare FBst ids -> FlyBase: CURIEs (IRIs in RDF)
            rec["stock"] = [f"FlyBase:{fbst}" for fbst in s["stock"]]
        if s.get("sex"):
            # emit the FBbt organism CURIE (schema sex_options meanings) so the OWL
            # renders `part of some FBbt:0000701x`, matching the FlyBase/VFB convention.
            rec["sex"] = {"female": "FBbt:00007011", "male": "FBbt:00007004"}[s["sex"]]
        entities.append(rec)

    # --- Assays ---
    assay_name = _assay_namer(cfg, samples["assays"], sample_descr, cite_suffix)
    sb_cfg = cfg.get("sample_build") or {}
    for a in samples["assays"]:
        xrefs = [x for x in [a.get("accession")] + a.get("dbxrefs", []) if x]
        if (sb_cfg.get("assay_label") or {}).get("xref_library_id") and a.get("library_id"):
            xrefs.append(a["library_id"])          # the source's own library id (name shortens it)
        xrefs = list(dict.fromkeys(xrefs))         # de-duplicated, order kept
        if a.get("sra"):
            xrefs.append(a["sra"])
        if a.get("biosample"):
            xrefs.append(a["biosample"])
        entities.append({
            "type": "Assay", "id": iri(a["vfbseq_id"]),
            "name": assay_name(a),
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
        rec = {
            "type": "Clustering", "id": iri(c["vfbseq_id"]),
            "name": c.get("name") or f"{d['accession']} {c['subset']} clustering",
            "associated_dataset": dataset_iri,
            "neo_label": "Clustering",
        }
        if c.get("samples"):
            # the Samples it used, own or reused from another dataset (those are
            # emitted only by the project that curated them)
            rec["associated_sample_or_assay_for_clustering"] = [iri(s) for s in c["samples"]]
        entities.append(rec)

    # --- Clusters ---
    # An annotation may name its own clustering (projects with several clusterings,
    # e.g. Davie 2018); otherwise it belongs to the dataset's annotated subset.
    # Only clusters with an FBbt term are loaded (held ones get no id or entity).
    subset = anns_subset(proj)
    main_clustering = clustering_iri_by_subset.get(subset)
    for ann in anns:
        label = ann["label"]
        m = fbbt_mapping(proj, label)
        bm = (m or {}).get("best_match") or {}
        if not bm.get("fbbt_id"):
            continue
        cid = reg.mint("Cluster", f"{d['accession']}:{subset}:{label}", label=label)
        if ann.get("clustering"):
            clustering = clustering_iri_by_subset[ann["clustering"]]
            src_id, typ = str(ann.get("source_cluster_id", label)), ann.get("type", label)
            where = ann.get("clustering_name", ann["clustering"])
            if ann.get("membership") == "label_transfer":
                # cells typed one by one by the authors' classifier, not clustered
                name = f"{typ} cells, predicted ({where}){cite_suffix}"
            elif ann.get("membership") == "sorted":
                # a FACS-sorted population the authors typed as a whole
                name = f"{typ} cells, sorted ({where}){cite_suffix}"
            elif ann.get("unannotated") or typ == src_id:
                name = f"cluster {src_id} ({where}){cite_suffix}" if ann.get("unannotated") \
                    else f"{typ} cluster ({where}){cite_suffix}"
            else:
                name = f"{typ} cluster {src_id} ({where}){cite_suffix}"
        else:
            clustering, name = main_clustering, f"{label} cluster{cite_suffix}"
        rec = {
            "type": "Cluster", "id": iri(cid),
            "name": name,
            "associated_clustering": clustering,
            "associated_dataset": dataset_iri,
            "cell_number": ann.get("cell_number"),
            "neo_label": "Cluster",
        }
        title = MEMBERSHIP_TITLES.get(ann.get("membership"))
        if title:
            rec["title"] = title.format(type=ann.get("type", label))
        parent = ann.get("parent_cluster")
        if parent and ((fbbt_mapping(proj, parent) or {}).get("best_match") or {}).get("fbbt_id"):
            # sub-cluster -> the cluster whose cells were re-clustered (part of),
            # when that cluster is loaded
            rec["parent_cluster"] = iri(reg.mint(
                "Cluster", f"{d['accession']}:{subset}:{ann['parent_cluster']}",
                label=ann["parent_cluster"]))
        # composed primarily of: the best match plus any additional_matches
        rec["cell_type"] = [bm["fbbt_id"]] + [
            a["fbbt_id"] for a in (m.get("additional_matches") or [])]
        if label in clu_counts:
            rec["total_gene_count"] = clu_counts[label]["total_gene_count"]
            rec["filtered_gene_count"] = clu_counts[label]["filtered_gene_count"]
        entities.append(rec)

    reg.save()
    return entities


MEMBERSHIP_TITLES = {
    "label_transfer": "Cells assigned the type '{type}' by the authors' classifier (label "
                      "transfer from an annotated analysis), not a transcriptomic cluster.",
    "sorted": "Cells FACS-sorted by the authors as '{type}' and analysed as a whole; "
              "typed from the authors' sample description, not a transcriptomic cluster.",
}


def _assay_namer(cfg: dict, assays: list[dict], sample_descr: dict[str, str], cite_suffix: str):
    """Return ``name(assay)``: its Sample's description plus what the assay is, from
    `sample_build.assay_label` in config:

      unit      e.g. "10x lane", "10x library", "Smart-seq2 plate"
      pattern   optional regex on the library id; group 1 numbers the assay
                (e.g. "_(\\d+)$" -> "10x lane 1"); without it, the unit alone
      of_total  true -> "... of <assays of that Sample>" (e.g. "10x lane 1 of 8")
      xref_library_id  true -> the full library id is also kept as a dbxref

    Without `assay_label` the accession (or library id) is the name, as before."""
    import re
    al = (cfg.get("sample_build") or {}).get("assay_label")
    if not al:
        return lambda a: a.get("accession") or a.get("library_id")
    pat = re.compile(al["pattern"]) if al.get("pattern") else None
    n_by_sample: dict[str, int] = {}
    for a in assays:
        n_by_sample[a["sample_vfbseq_id"]] = n_by_sample.get(a["sample_vfbseq_id"], 0) + 1

    def name(a: dict) -> str:
        what = al["unit"]
        if pat:
            m = pat.search(a.get("library_id") or "")
            if not m:
                raise ValueError(f"assay_label.pattern {al['pattern']!r} does not match "
                                 f"library id {a.get('library_id')!r}")
            what += f" {m.group(1)}"
            if al.get("of_total"):
                what += f" of {n_by_sample[a['sample_vfbseq_id']]}"
        return f"{sample_descr[a['sample_vfbseq_id']]}, {what}{cite_suffix}"
    return name


def anns_subset(proj: Path) -> str:
    cta = json.loads((proj / "cell_type_annotations.json").read_text())
    return cta.get("dataset", {}).get("subset", "main")


def _yaml(path: Path) -> dict:
    import yaml
    return yaml.safe_load(path.read_text())


def build_project(project: str):
    """Build entity records and write projects/<project>/entities.json."""
    entities = build_entities(project)
    out = REPO_ROOT / "projects" / project / "entities.json"
    out.write_text(json.dumps(entities, indent=2) + "\n")
    return out, entities
