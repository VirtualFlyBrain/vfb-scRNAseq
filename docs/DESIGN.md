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

### Mapping outcome flags: `new_term_needed` vs `verification_needed`

`fbbt_mapping.json` records two independent booleans (not the inverse of "exact
match"):

- **`new_term_needed`** — true only when *no adequate FBbt term exists at any
  level* (best_match null, or only a too-broad parent). A real request-a-new-term
  case.
- **`verification_needed`** — true when a plausible specific term *exists but its
  equivalence is unconfirmed* (e.g. a same-named subtype defined from a different
  source/modality). A curator-verification task, not a new term.
- A confident exact match → both false.

This split was added after the pilot: Dm3a/Dm3b broad-match the `Dm3` parent while
FBbt subtype terms (FBbt:00052303/4, from Özel 2021 connectome data) exist but
can't be confirmed equivalent to Kurmangaliyev's transcriptomic a/b — that is
`verification_needed`, not `new_term_needed`.

### Author cell class drives the broad-match ceiling

The GEO metadata annotates a `class` per cluster: **N** (neuron, 153 types),
**G** (glia, 19), **R** (photoreceptor, 3), **C** (undefined in the README —
likely cone/pigment/accessory eye cells; confirm in the paper before mapping
C-class clusters). For unidentified numbered clusters the class still fixes the
correct high-level FBbt term (N→neuron, G→glial cell, R→photoreceptor), so e.g.
`N1` (class N) broad-matches `adult optic lobe neuron` rather than being left
unmapped. The mapping step is given the cluster's class for this reason.

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

## Generic pipeline vs per-project config

The scripts in `scripts/` (`build_annotations_from_geo.py`,
`assign_placeholders.py`, `collate_mapping.py`) are **dataset-agnostic drivers**.
All project/tissue-specific knowledge lives in `projects/<name>/config.yaml` and
is read through `src/vfb_scrnaseq/project_config.py`. Config sections:

- **`annotations`** — which metadata columns are the label / class / grouping /
  timepoint, and the source file. (Kurmangaliyev: `subtype`/`class`/`type`/`time`.)
- **`unidentified`** — how to handle clusters with no named identity:
  - `rule` — `class_prefixed_numbered` (label == `<class><digits>`), `none`, or
    `regex:<pattern>`;
  - `hold_classes` — classes of undefined meaning, held not mapped (e.g. `C`);
  - `class_anchors` — the broad FBbt term per author class for this tissue
    (e.g. N→`adult optic lobe neuron`, G→`adult optic lobe glial cell`).

Nothing optic-lobe-specific remains in the shared code: a different atlas ships a
different `config.yaml` and the `scripts/`/`src/` code is reused untouched.

**Escape hatch for bespoke logic:** a project may include
`projects/<name>/project.py` defining `is_unidentified(label, cls, config)` and/or
`broad_anchor(cls, config)`; `project_config` prefers these over the config-driven
defaults. So the common cases are declarative, and the rare oddball overrides in
its own folder — never in the shared pipeline.

**Source adapters** are a separate axis: `build_annotations_from_geo.py` is the
GEO ingester; a non-GEO source (h5ad `obs`, CELLxGENE) would be a sibling script
emitting the same `cell_type_annotations.json`, with the config/placeholder/collate
layers downstream unchanged.

## Recording manual edits to mappings

Per-term *full* provenance isn't recorded (the set-level `provenance.json` covers
versions/tools). But **manual edits are** — they're the non-reproducible part a
re-run would otherwise silently erase. A mapping JSON carries an optional
`manual_edit` block **only when a human has hand-edited it**:

```json
"manual_edit": { "by": "curator", "date": "2026-06-20",
                 "change": "best_match FBbt:00003770 -> FBbt:00052303; broad -> exact",
                 "reason": "curator confirmed the Wnt marker corresponds to bi" }
```

Absent = pipeline-generated (agent or placeholder script). Agents/scripts must
**never** set it. `collate_mapping.py` surfaces a `manual_edit` column so overrides
are visible in `mapping.tsv`, and a re-run should skip/flag clusters carrying it so
a curator decision is not lost. Git history remains the full diff backstop.

## Provenance & version recording

Each project records a `provenance.json` (schema:
`src/vfb_scrnaseq/schemas/provenance.schema.json`, validated by the
`check_provenance.py` hook) capturing the exact versions of **everything used to
produce the mappings**, so a result can be re-checked when a source changes:

- **ontologies** — id, version + `version_iri`, how/when accessed (e.g. FBbt
  `2026-06-11` via OLS MCP);
- **data_sources** — datasets/publications and the specific files used, with
  `sha256` + byte size for exact reproducibility (GEO metadata file, the PDF);
- **software** — external code/libraries/services with versions and git commits
  (atlas-chat commit, sentence-transformers, pymupdf4llm, OLS, Python);
- **models** — the mapping/report LLM and the local-index embedding model.

Motivation: the FBbt `2026-06-11` release fixed a Dm8 rename error — recording the
FBbt `version_iri` makes it explicit which release a mapping was made against, so
mappings can be revisited when the ontology moves. (A future helper can auto-stamp
git commits / file checksums rather than hand-filling.)

## Sample / Assay / Dataset metadata (beyond cell types)

The cluster→FBbt layer is done; the rest of the schema is populated from GEO
(`ingest.fetch_series`) + `config.yaml`. Decisions for the Kurmangaliyev worked
example:

- **Granularity: 7 `Sample`s + 36 `Assay`s.** Biological `Sample` =
  `set_timepoint_biorep` (DGRP_All_A/B, W1118_{24h,48h_A,48h_B,72h,Adult}_A);
  `Assay` = each 10x library/techrep (the 36 GSMs), carrying GSM + SRX as dbxrefs.
  (README: techrep = "a single 10X library".)
- **Genotype/stock:** the master schema has no slot for strain (DGRP vs W1118) —
  **add a `genotype`/`stock` slot to `Sample`** (we own the schema). Real
  biological metadata we shouldn't drop.
- **`stage` → FBdv and `sample_tissue` → FBbt**, curated and keyed on the GEO
  **`age` characteristic** (`age_map` in config), NOT the sample-title token — the
  token is not 1:1 with age (the sample titled `Adult` is actually `96h APF` =
  pharate adult). Both the mapping and the sample `rdfs:label` derive from the raw
  GEO info:

  | GEO age | FBdv stage | FBbt tissue |
  |---|---|---|
  | 24h APF | `FBdv:00005349` pupal stage | `FBbt:00001930` embryonic/larval optic lobe |
  | 48h / 72h / 96h APF | `FBdv:00006011` pharate adult stage | `FBbt:00003701` adult optic lobe |
  | 0–96h APF (DGRP pooled) | `FBdv:00007001` P-stage *(broader than "pupal stage")* | `FBbt:00003701` adult optic lobe |

- **Developmental atlas, not adult.** Kurmangaliyev is pupal (24–96h APF) + adult.
  At the **sample** level the gradient is captured above (24h → embryonic/larval
  optic lobe). At the **cell-type** level, FBbt has distinct `immature X neuron`
  terms; the cell-type mapping agent was corrected to weigh developmental stage
  (integrated/late clusters → mature form; early-stage-specific → immature form)
  rather than assume "adult". The **main integrated clusters** (cells pooled 24–96h
  APF) keep the **mature** resolved-identity terms; **immature forms apply to the
  `early` subset and any future per-timepoint layer.**
- **`sex`:** unannotated → unset (schema enum is male/female only).
- **`Assay.method`:** `FBcv:0009008` "10x sequencing".
- **`Clustering`:** two — `main` and `early` — each linked to its dataset + the
  samples/assays that fed it.

New ontologies now in play (add to provenance `ontologies`): **FBdv** (stages),
**FBcv** (assay method), and FBbt also for tissue. Tissue→FBbt and stage→FBdv are
new mapping steps alongside the existing cell-type mapping.

## RDF assembly & emission

`vfb_scrnaseq.build` reads the working-format JSON (config, `samples.json`,
`cell_type_annotations.json`, `mapping/*.json`), mints `Cluster` IDs, and writes
`entities.json` — a flat list of records keyed by LinkML **slot names**, with
minted `VFBseq` IRIs and GEO/SRA accessions as `dbxref`s.

`vfb_scrnaseq.emit` then uses the **standard LinkML tools** (not hand-written
triples): it groups the entities into the schema's `tree_root` **Container** and
runs
  - **`linkml-validate`** — conforms the data to the schema (types, ranges,
    required slots; **rejects unknown slots**, so mis-keyed data errors loudly
    instead of being silently dropped); then
  - **`linkml-convert -t ttl`** — emits RDF from the schema's `slot_uri`/`class_uri`.

`scripts/build_rdf.py` runs build → emit, in **two representations** (both from
the same schema + `Container` data, no custom triple code):

- **OWL** (`--format owl`, default `both`) via **`linkml-owl` (`linkml-data2owl`)**,
  which honours the schema's `owl.fstring`/`owl.template` annotations →
  `ClassAssertion(ObjectSomeValuesFrom(R Term) {id})` existential restrictions,
  `ObjectPropertyAssertion`s, `AnnotationAssertion`s, and (expression phase) the
  annotated `expresses some gene` axioms. This is the **VFB-pipeline-compatible**
  output → `projects/<name>/<accession>.ofn`. Worked example: **1516 axioms** (242
  type + 235 restrictions + object/annotation assertions).
- **Flat RDF** (`--format ttl`) via **`linkml-convert`**, which uses `slot_uri`/
  `class_uri` only — simpler generic RDF (ontology-term links are plain triples,
  no OWL restrictions), Container node stripped → `<accession>.ttl` (1785 triples).
- **OWL/XML** — the `.ofn` is then converted to RDF/XML with **`robot convert`** →
  `<accession>.owl` (lossless; round-trip verified). ROBOT is an external Java tool,
  not a pip/uv dep, so this step is skipped with a warning if `robot` isn't on PATH.

Both are preceded by **`linkml-validate`** (types, ranges, required slots, rejects
unknown slots). Use OWL for VFB/reasoning; flat RDF for generic SPARQL. See the
`owl.fstring` discussion — the OWL path restores the existential-restriction
semantics the flat path drops, and is required for the expression-stats axioms.

Schema use: the LinkML schema now drives **validation** (`linkml-validate`),
**flat RDF** (`linkml-convert`), and **OWL** (`linkml-owl`) — the `owl.*`
annotations are the linkml-owl input format the schema was authored for.

**Caveats / deferred** (deliberately not done here):
- **owl.fstring / owl.template not applied.** The schema's bespoke OWL templates
  target the VFB *neo* pipeline; we emit the standard `slot_uri` RDF instead.
  Producing that exact OWL (ClassAssertion/ObjectSomeValuesFrom) would be a
  separate emitter.
- **Publication** is linked as the DOI IRI (`dc:references`), not a full
  `Publication` entity yet.
- **Dataset gene counts** (`total/filtered_gene_count`) need the expression
  matrix — expression-stats phase.
- **`Clustering.associated_sample_or_assay_for_clustering`** left unwired: cells
  from 24h APF appear in both `early` and `main`, so the sample→clustering link is
  not 1:1 (single-valued slot). Only `associated_dataset` is set.
- **`sex`** unset (not annotated in GEO).

## Expression statistics

Computed **the way FlyBase did** (fuzzy-onions `summarise_expression`; FlyBase SOP)
by `vfb_scrnaseq.stats` (`scripts/build_expression.py`). Per cluster × gene:

- `expression_extent` = cells expressing (value > 0) / total cells in cluster —
  **normalisation-invariant, so exact**.
- `expression_level` = **mean over *expressing cells only*** (Σ / n_expressing),
  NOT over all cells (the detail scanpy's default gets wrong).
- **Normalisation**: SOP uses the SCEA *Normalised Counts* table; Kurmangaliyev is
  GEO-raw (never went through SCEA), so we replicate the *method* with **CPM**
  (linear) — `level` cannot be SCEA-identical, but extent is exact.
- **Filter**: `extent > 0.2` (from the old repo's `process_metadata.py`);
  `Cluster.total_gene_count` (any expression) vs `filtered_gene_count` (> 0.2).

**Compute**: two chunked streaming passes over the 1 GB 10x `.mtx.gz` (cell totals
for CPM, then per-cluster×gene sums via `bincount`) — dense accumulators genes×clusters
only, ~95 s, low memory. The matrix lives in `.cache/` (gitignored).

**Scale & outputs** (worked example: 17,561 genes, 194k cells → **584,710 rows**
after the filter):
- `expression.tsv` — filtered rows, plain/diffable, **committed** (~32 MB).
- `expression_report.md` — per-cluster cells + total/filtered gene counts.
- `<accession>_expression.owl.gz` — **committed, loadable** (~13.5 MB; 584,710
  annotated `expresses` axioms).
- `total/filtered_gene_count` also set on the `Cluster` entities in the metadata OWL.

**Emission — efficient, NOT linkml-owl.** linkml-owl renders *and re-parses* the
template per row (~1.4 ms/row → ~14 min / ~3 GB at this scale). Instead we render
the schema's `gene` `owl.template` per row (Jinja) straight to one `.ofn` (~0.6 s),
then a single `robot convert` → `.owl` → gzip (~30 s total). linkml-owl is kept for
the *metadata* (small). NB the `gene` template was fixed for the modern
`py-horned-owl` backend (quoted/typed literals, `xsd:` prefix); gene fillers are
`FlyBase:FBgn…` CURIEs.

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
