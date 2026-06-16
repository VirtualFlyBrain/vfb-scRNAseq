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

## Data acquisition (GEO)

GEO metadata is fetched in `src/vfb_scrnaseq/ingest.py` from GEO's **SOFT** text
endpoint (`acc.cgi?...&targ=all&form=text&view=full`) over plain HTTP — no auth,
deterministic, CI-friendly. `fetch_series("GSE...")` returns a typed `GeoSeries`
(title, summary, platform ids, BioProject, SRA study, supplementary-file URLs)
with a list of `GeoSample` (accession, title, organism, raw `characteristics`,
`relations` such as `SRA`/`BioSample`, supp-file URLs). Parsing (`parse_soft`)
is split from the network call so it is unit-tested against a fixture.

Deliberate boundaries:

- **Metadata only — never the expression matrix.** The matrix is an
  expression-stats-phase concern. (Same philosophy as the `anndata-zarr-summary`
  skill, which reads `obs/` only.)
- **Raw characteristics in, ontology mapping out.** `ingest` surfaces GEO's raw
  strings (`stage_hint`, `sex_hint`, `characteristic(...)`); mapping them onto
  FBdv stages and the schema's `sex` enum needs ontology lookup and lives in
  `build.py`.
- **`supplementary_files` is the hook for cluster labels from GEO** — many atlases
  attach a per-cell metadata file with cluster assignments; `ingest` captures
  those URLs, so they are an authoritative alternative to scraping supp tables.

GEOparse / pysradb are optional swap-ins (e.g. richer SOFT parsing, GSM→SRX/SRR
resolution) but are **not required**; the stdlib path covers what the schema records.

### `retrieve-dataset` skill — not copied (deferred)

The upstream `Cellular-Semantics/claude-skills` `retrieve-dataset` skill was
**deliberately not copied**. It is a **MapMyCells annotation-transfer** tool
(load → convert → emit a `cell_id → cluster` JSON for F1 scoring against the
Allen/CL taxonomies), pulling the `annotation-transfer` CLI plus R/Seurat — none
of which serves FBbt mapping. Its only reusable kernel (multi-format → AnnData +
`obs` inspection) is already covered by `anndata-zarr-summary` for the obs path.
Revisit only in the expression-stats phase, and even then lift just the loader.

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

## Report generation & cost model

Per-cluster cell-type reports (the descriptive evidence that feeds FBbt mapping)
are generated with the **Claude Code agentic flow**, not atlas-chat's standalone
`atlas-report` CLI.

- The `atlas-report` CLI makes its own **paid** Anthropic API calls per report —
  an ongoing per-cluster cost. We avoid it.
- Instead, the LLM work runs as **Claude Code subagents in-session** (covered by
  an existing Claude Code subscription — no metered API billing), drawing evidence
  from free sources: the **local PDF index** (`local-paper-index`, local MiniLM
  embeddings), the **OLS MCP** (FBbt), and **PubMed / Europe PMC** in place of
  ASTA. No `ANTHROPIC_API_KEY` / `ASTA_API_KEY` required.
- `local-paper-index` (the genuinely useful, free part of atlas-chat) is installed
  in a sibling clone and the project is **symlinked** in, so the built index and
  generated `reports/` land back in this repo.

**Validated end-to-end on `T4a`** (zero API cost): local-index evidence →
in-session synthesis (`reports/T4a.md`) → `map-clusters-to-fbbt` (OLS) →
`mapping/T4a.fbbt_mapping.json`, an **exact match to FBbt:00003732 (T4a neuron)**,
high confidence, schema-validated by the hook. The agent correctly rejected the
parent `T4 neuron` (too broad) and the child `T4ai` (too specific).

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
(24/48/72h) + adult. Chosen as a good FBbt-mapping stress test: canonical
optic-lobe types (T4/T5, lamina monopolar L1–L5, medulla neurons) map cleanly,
while marker- and temporal-stage labels exercise the human-review path.

Structure confirmed by `ingest.fetch_series("GSE156455")`:

- **36 samples**, each with `BioSample` (SAMN…) and `SRA` (SRX…) resolved;
  platform `GPL25244`, BioProject `PRJNA658010`, SRA study `SRP278058`.
- **Sparse characteristics:** only `tissue` (optic lobes) and `age` — **no sex**,
  so the schema `sex` slot is unset/mixed for this dataset.
- **Stages are APF time windows** (`0-96h`, `24h`, `48h`, `72h`, `96h APF`) →
  map to FBdv pupal stages.
- **Two sub-datasets, `early` and `main`**, in the supplementary files:
  `matrix_{early,main}.mtx.gz` (MatrixMarket — the FlyBase/fuzzy-onions format),
  `barcodes_*`, `features_*`, and `metadata_{early,main}.tsv.gz`.
- **Cluster labels:** the `metadata_*.tsv.gz` files hold per-cell cluster /
  cell-type assignments at three granularity levels — `class` (4: N/G/C/R),
  `type` (187 in `main`), `subtype` (196 in `main`). The `early` subset is mostly
  provisional `x*` clusters.

**First annotation pass (decided):** scope = **`main`** subset only; granularity =
**`subtype`** (the finest resolved identity; `type`/`class` retained as grouping).
`scripts/build_annotations_from_geo.py` derives
`projects/kurmangaliyev_2020/cell_type_annotations.json` from the GEO metadata —
196 subtype annotations, each with `cell_number`, parent `type`, `class`, and the
`timepoints` it appears at (193,727 cells total).

**Label provenance policy:** take cluster labels from the **most authoritative
machine-readable source**, and use the other source to validate.

- *Preferred when present:* clean supplementary tables (curated, human-authored
  naming), validated against the GEO `metadata_*.tsv.gz` label set.
- *When the supp is figures-only* (as for Kurmangaliyev — the PDF has no
  spreadsheets), this **inverts**: the GEO `metadata_*.tsv.gz` is the authoritative
  label source, and the **paper PDF** is the description/validation source.

The GEO metadata wins here on the merits, not just as a fallback: it is
machine-readable, carries named types at multiple granularity levels, is the
*corrected* version (the README documents the T4c/T4d label-swap fix that PDF
figures may predate), and yields per-cluster cell counts (`cell_number`) directly.
Either way, mismatches are **flagged for review**, never silently resolved.
