# Design decisions & reference notes

This document records the *why* behind the repo's structure and the external
conventions it must conform to. It is the shareable, version-controlled home for
decisions that would otherwise only live in a maintainer's head.

## Purpose

Produce RDF metadata for *Drosophila* single-cell RNA-seq data: dataset / sample
/ cluster annotations, linking clusters to **FBbt** anatomy terms, plus (a later
phase) summary expression statistics computed the FlyBase way.

## Architecture

Built on the [atlas-chat](https://github.com/Cellular-Semantics/atlas-chat)
template (literature-grounded, quote-validated cell type reports). The repo's
`.claude/` already carries adapted atlas-chat agents, hooks, and commands.

**Two schemas, two jobs** — the key structural decision:

- **Working / annotation format** — `projects/<id>/cell_type_annotations.json`
  (atlas-chat shape; JSON Schema → Pydantic). Where curation happens: cluster
  labels, generated literature reports, and the proposed FBbt mapping.
- **Publishing format** — `src/vfb_scrnaseq/schema/VFB_scRNAseq_schema.yaml`
  (LinkML). The RDF target: `Dataset / Sample / Assay / Clustering / Cluster`,
  the FBbt `cell_type` link, and the expression slots. Because it is LinkML,
  RDF/TTL is produced with `linkml-convert`; predicates come from the schema's
  `slot_uri` / `class_uri` / `owl.fstring` annotations.

### Schema master copy & deprecation

`VFB_scRNAseq_schema.yaml` here is the **new master copy**, imported verbatim
from `VirtualFlyBrain/vfb-scRNAseq-ontology`. That repo will be **deprecated**
once this one is running. The schema is kept verbatim for now so the migration
diff stays clean; planned edits (e.g. the `VFBseq` prefix, dropping the FlyBase
`id` guidance) are tracked as follow-ups.

### Pipeline (cell-type-annotation focus)

```
project config + curated cluster labels
  -> literature reports        (atlas-chat report pipeline)
  -> FBbt mapping candidates   (.claude/agents/map-clusters-to-fbbt.md, via OLS MCP)
  -> human review              (projects/<id>/mapping.tsv)
  -> LinkML objects            (vfb_scrnaseq.build)
  -> RDF/TTL                   (vfb_scrnaseq.emit -> linkml-convert)
```

## Identifiers

Every published entity (Dataset, Sample, Assay, Clustering, Cluster) gets an
opaque, registry-backed **`VFBseq_########`** IRI (`src/vfb_scrnaseq/ids.py`,
registry in `id_registry/`). Minting is idempotent on `(entity_type, natural_key)`.

GEO/SRA accessions (GSE / GSM / PRJNA / SRP / GPL) are **cross-references**,
carried in the schema's `site` / `accession` slots and dbxrefs — **never** used
as the IRI.

Rationale:

- GEO accessions are not dereferenceable RDF identifiers, and their granularity
  does not match the schema 1:1 (a GSM bundles sample + library + assay, which
  the schema separates into `Sample` / `Assay`).
- `Clustering` / `Cluster` / the cell-type assignment have **no** GEO IDs at all
  and must be minted regardless — so minting uniformly beats mixing authorities.
- We are deliberately moving **off** FlyBase-minted IDs; minting under a
  VFB-controlled namespace keeps id stability under our control through that
  transition.
- The schema already anticipates this: `Dataset.accession` + `Dataset.site` exist
  precisely to hold the external id while the IRI stays internal.

Prefix is `VFBseq` (not `VFBexp`, which is already in use).

## FBbt mapping & new-term requests

### Mapping (`map-clusters-to-fbbt` agent)

Adapted from atlas-chat's Cell Ontology mapper, retargeted to **FBbt** via the
OLS MCP (`ontology_id: "fbbt"`). For each cluster it searches FBbt with the label
plus report context, scores candidates against the report definition, and writes
`fbbt_mapping.json` (schema: `src/vfb_scrnaseq/schemas/fbbt_mapping.schema.json`,
enforced by the `check_fbbt_mapping.py` hook). It **proposes**; a human reviews.
Fly cluster labels are often marker-/driver-based, so expect a lower clean-match
rate than for canonical label sets.

### New-term requests — how FBbt intake actually works

FBbt is maintained at
[`FlyBase/drosophila-anatomy-developmental-ontology`](https://github.com/FlyBase/drosophila-anatomy-developmental-ontology)
(OBO `fbbt.obo` / `.owl`; FBdv split into its own repo in 2019). New terms are
requested by **opening a GitHub issue**. The repo's root `issue_template.md`
(there is no `.github/ISSUE_TEMPLATE/` directory) asks for only:

- **Reference(s)** *(required)* — FBrf / DOI / PMID
- **Term label(s)** — name(s) from the publication, or a pointer to where the
  types are listed (e.g. "Table S3").

This is a **minimal request, expert curation** model: FlyBase curators author the
authoritative definition, hierarchy placement, logical axioms, and synonyms — the
inverse of the Cell Ontology process. Accordingly, the `fbbt-term-request` agent
emits References + Term label(s) as the deliverable, plus an optional,
**clearly-marked non-authoritative** "Suggested details" block (parent / location
/ markers / draft definition / synonyms) drawn from the report, never presented
as authoritative.

## Expression statistics (later phase)

Summary stats must be computed **the way FlyBase did** (fuzzy-onions
`Project.summarise_expression()`; FlyBase SOP). Per cluster × gene, on the
**normalised** counts matrix:

- `expression_level` = sum of expression values / **number of cells that express
  the gene** — i.e. the mean over *expressing cells only*, NOT over all cells in
  the cluster. (This is the detail most often gotten wrong — scanpy's usual mean
  is over all cells.)
- `expression_extent` = number of cells expressing / total cells in cluster.
- "Expressing" = value `> 0` in the normalised matrix.

These map onto `Cluster.expression_level` / `Cluster.expression_extent` (with
`gene` via `RO:0002292`).

## Worked example

`projects/kurmangaliyev_2020/` — Kurmangaliyev et al. 2020, *Drosophila* visual
system developmental atlas
([GSE156455](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE156455),
DOI `10.1016/j.neuron.2020.10.006`, PMID 33125872). 36 GSM samples
(GSM4731869–GSM4731904) across DGRP + w1118 strains and pupal timepoints
(24/48/72h) + adult. Cluster labels are curated from the paper / supplementary
tables. Chosen as a good FBbt-mapping stress test: canonical optic-lobe types
(T4/T5, lamina monopolar L1–L5, medulla neurons) map cleanly, while marker- and
temporal-stage labels exercise the human-review path.
