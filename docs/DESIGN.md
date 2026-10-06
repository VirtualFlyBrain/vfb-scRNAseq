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

## General curation rules

Rules that apply to every project (agreed with the curator; the per-project sections
below record how each was applied).

- **The unit is the authors' cluster.** One row = one cluster the authors defined
  (it gets a VFBseq id and an FBbt annotation). Clusters are never merged by cell
  type: two clusters of the same type stay two Clusters with the same FBbt term
  (unlike the old SCEA loads, which re-analysed and merged by type).
- **Typing comes from the authors, not from re-analysis.** Map each cluster from what
  the authors say it is (GEO metadata, paper, supplementary tables). Curators do not
  overturn or hedge the authors' typing on the basis of their own reading of markers,
  cell counts, likely contamination or dissection details. Where author sources
  disagree, the project config decides which is authoritative and the other is
  recorded as a flag (`verification_needed`).
- **Relation is *composed primarily of*** (RO:0002473), so not every cell in a cluster
  need be of the annotated type. A cluster the authors name for two co-expressed
  markers may be mapped to both classes (`additional_matches`).
- **No FBbt term → held.** A cluster with no adequate FBbt term is held (no
  `cell_type`), not given a generic fallback term just to have one.
  `collate_mapping.py` marks any mapping with a null `best_match` as held.
- **New FBbt terms from gene expression alone are the exception.** `new_term_needed`
  records a gap; it is not a queue of requests. Do not request terms defined only by
  transcriptomic clusters/markers as a matter of course (we do not want thousands of
  expression-defined terms); any request needs explicit curator sign-off.
- **Stage belongs on the Sample.** Samples carry their FBdv stage. A Cluster gets a
  `stage` only when the stage is determined from the cluster's own gene expression
  (e.g. a cluster the authors identify as a particular developmental stage) — not
  copied from the samples it was built from, which would be redundant.

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

The two are distinct because a transcriptomic subtype can share a name with an FBbt
subtype term defined from a different modality (e.g. connectome data) without
confirmed equivalence: an adequate specific term exists but its identity is
unconfirmed, so the cluster broad-matches the parent and is flagged
`verification_needed`, not `new_term_needed`.

### Author cell class drives the broad-match ceiling

Atlas metadata often annotates a broad `class` per cluster (e.g. neuron / glia /
photoreceptor). For unidentified numbered clusters the class still fixes the correct
high-level FBbt term (neuron → a neuron term, glia → a glial-cell term, …), so such a
cluster broad-matches its class anchor rather than being left unmapped. The mapping
step is given the cluster's class for this reason, and the per-class broad FBbt
anchors are declared in the project `config.yaml` (`unidentified.class_anchors`).
A class of undefined meaning can instead be **held** (listed in `hold_classes`) and
left unmapped pending curation.

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
- Reports are **background evidence, not mapping decisions**; `mapping.tsv` is the
  authoritative copy. `collate_mapping.py` adds a generic `reports/README.md` saying so
  (template `src/vfb_scrnaseq/templates/reports_README.md`) when a project's reports
  folder has none; an existing README is never overwritten.

## Generic pipeline vs per-project config

The scripts in `scripts/` (`build_annotations_from_geo.py`,
`assign_placeholders.py`, `collate_mapping.py`) are **dataset-agnostic drivers**.
All project/tissue-specific knowledge lives in `projects/<name>/config.yaml` and
is read through `src/vfb_scrnaseq/project_config.py`. Config sections:

- **`annotations`** — which metadata columns are the label / class / grouping /
  timepoint, and the source file.
- **`unidentified`** — how to handle clusters with no named identity:
  - `rule` — `class_prefixed_numbered` (label == `<class><digits>`), `none`, or
    `regex:<pattern>`;
  - `hold_classes` — classes of undefined meaning, held not mapped (e.g. `C`);
  - `class_anchors` — the broad FBbt term per author class for this tissue
    (e.g. N→`adult optic lobe neuron`, G→`adult optic lobe glial cell`).

  - `hold_unidentified` — hold *every* unidentified cluster (for atlases with no
    author class, so no broad anchor can be chosen; e.g. Davie 2018).
- **`sample_build.title_pattern`** — how GSM titles split into set / timepoint /
  biological replicate (/ technical replicate): the default
  `set_timepoint_biorep_techrep`, or `regex:` with named groups. GSMs that do not
  match are out of the project's scope (lets one GEO series contribute a subset).
- **`sample_build.sex: mixed`** — curator-confirmed pooled-sex samples; the
  single-valued `sex` slot stays unset without the "check the paper" warning.
- **`annotations.barcode_column`** — the per-cell metadata column that matches the
  matrix barcodes (default `barcode`).
- **`prior_mapping`** — optional TSV of a previous load's FBbt terms per cluster;
  `collate_mapping.py` adds `prior_fbbt_*` / `prior_agrees` columns as a cross-check.
  Never an input to the mapping itself.
- **`annotations.review_columns`** — extra per-cluster fields from
  `cell_type_annotations.json` shown after the cluster key in `mapping.tsv` (e.g.
  Davie's clustering, the authors' cluster id, the Table S2 call and any conflict).
  Re-running `collate_mapping.py` keeps the `reviewed`/`review_notes` already there.
- **Per-cluster annotation entries** may carry `clustering` (a `sample_build.clusterings`
  id; entries there may be `{id, name}`), `source_cluster_id` and `unannotated`
  (held when `hold_unidentified`). **`expression.membership_file`** (barcode→cluster)
  lets a cell belong to one cluster in each of several clusterings.

Cluster labels are used verbatim in the data but pass through
`project_config.label_slug` for per-cluster file names (`mapping/<slug>…`,
`reports/<slug>.md`): `/`→`_`, `*`→`p`, `&`→`+`. Labels already made of
`[A-Za-z0-9._+-]` are unchanged.

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

Absent = pipeline-generated (agent or placeholder script).

A mapping may also list **`additional_matches`** (same shape as `best_match`) when the
authors' name places a cluster in more than one class — e.g. Davie's neuropeptide
group "Mip/ITP" is *composed primarily of* both myoinhibitory peptide neurons and ITP
neurons. `build.py` emits every term as `cell_type`; `mapping.tsv` joins them with
` | `; `verify_mappings.py` checks them all. Agents/scripts must
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

Motivation: ontology releases can rename, re-home, or obsolete terms, so recording
the FBbt `version_iri` makes it explicit which release a mapping was made against,
and mappings can be revisited when the ontology moves. (A future helper can
auto-stamp git commits / file checksums rather than hand-filling.)

## Sample / Assay / Dataset metadata (beyond cell types)

Beyond the cluster→FBbt layer, the rest of the schema is populated from GEO
(`ingest.fetch_series`) + `config.yaml`. Design decisions:

- **Granularity — biological `Sample` vs `Assay`.** A biological `Sample` groups the
  libraries from one biological condition/replicate; an `Assay` is a single
  sequencing library (one GSM), carrying GSM + SRX (+ BioSample) as dbxrefs. The
  GSM→Sample grouping is driven by the GSM-title pattern declared in `sample_build`.
- **Stock:** the master schema had no slot for the source stock — a `stock` slot was
  **added to `Sample`** (we own the schema), carrying the FlyBase FBst reference(s).
  Real biological metadata we shouldn't drop; see the *Stock* note below.
- **`stage` → FBdv and `sample_tissue` → FBbt**, curated and keyed on the GEO
  **`age` characteristic** (`age_map` in config), NOT the sample-title token — a title
  token is not always 1:1 with developmental age. Both the FBdv/FBbt mapping and the
  sample `rdfs:label` derive from the raw GEO info.
- **Developmental atlases.** Where a dataset spans developmental stages, the
  sample-level `stage`/`tissue` capture the gradient, and the cell-type mapping weighs
  developmental stage (integrated/late clusters → mature form; early-stage-specific →
  immature form) rather than assuming the adult form.
- **`sex`:** set from GEO where present, else curator-confirmed from the paper;
  unset only when genuinely unknown (see the *sex* note below).
- **`Assay.method`:** the sequencing method as an FBcv term (e.g. `FBcv:0009008`
  "10x sequencing"), from `sample_build`.
- **`Clustering`:** one per clustering analysis in the dataset, each linked to its
  dataset (and, where the link is 1:1, the samples/assays that fed it).

New ontologies in play beyond FBbt: **FBdv** (stages) and **FBcv** (assay method),
plus FBbt for tissue — record all in provenance `ontologies`.

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
  output → `projects/<name>/<accession>.ofn`.
- **Flat RDF** (`--format ttl`) via **`linkml-convert`**, which uses `slot_uri`/
  `class_uri` only — simpler generic RDF (ontology-term links are plain triples,
  no OWL restrictions), Container node stripped → `<accession>.ttl`.
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
- **Dataset gene counts** (`total/filtered_gene_count`) need the expression
  matrix — expression-stats phase.
- **`Clustering.associated_sample_or_assay_for_clustering`** left unwired when a
  sample/assay feeds more than one clustering (the slot is single-valued), so the
  sample→clustering link is not 1:1. Only `associated_dataset` is set.

## Publication → VFB `:pub` node

The `Dataset` links to an existing VFB `:pub` node via `dc:references` pointing at
the paper's FlyBase **`FBrf`** IRI, and a minimal `Publication` entity
(`id = FlyBase:FBrf…`, `neo_label: pub`) is emitted so the loader attaches the
`:pub` label.

The FBrf is resolved by `vfb_scrnaseq.pub.resolve_pub`, by PMID, in order: the **VFB
curation KB** (`kb.virtualflybrain.org`, public read-only login `neo4j`/`vfb`) so a
freshly-curated pub is picked up; then **VFB production** (`pdb.virtualflybrain.org`,
no credentials), where already-released pubs live (the scRNAseq pubs are in production,
not the KB); then a curator-supplied `source.fbrf` in `config.yaml`. Each lookup
degrades gracefully (network/auth errors → next source, never fail the build). If
none resolves, the build warns and leaves the Dataset without a publication link.
Env overrides are `VFBSEQ_KB_*` / `VFBSEQ_PDB_URL` — deliberately not `VFB_KB_*`,
which curators often set for the writable KB.

## `sex`

Modelled as `part of some <FBbt organism>` (female = FBbt:00007011, male =
FBbt:00007004). `build_samples_from_geo.py` takes sex from the GEO characteristic,
falls back to a curator-confirmed `sample_build.sex` in config, and **warns the
curator to check the paper** when neither is present — so an unannotated dataset is
never silently left sexless.

## Stock

A `Sample` links to the FlyBase **stock(s)** it derives from via a multivalued
`stock` slot (`FlyBase:FBst…`), driven by `sample_build.stock_map` in config (stock
ids resolved from the paper against FlyBase Chado,
`psql -h chado.flybase.org -U flybase flybase`). Stocks are preferred over alleles,
and a genuinely **pooled** sample links **all** applicable stocks.

The link uses **`BAO:0095000` "is derived from"** (an object property; BAO is already
imported for the assay method). It is undefined in BAO, but reads correctly and
avoids `RO:0001000` derives_from's strict "source ceases to exist" clause, which is
wrong for a persistent stock. Emitted as an IRI object in flat RDF (`BAO:0095000` →
FBst IRI) and as `ObjectPropertyAssertion(BAO:0095000 …)` in OWL.

## Expression statistics

Computed **the way FlyBase did** (fuzzy-onions `summarise_expression`; FlyBase SOP)
by `vfb_scrnaseq.stats` (`scripts/build_expression.py`). Per cluster × gene:

- `expression_extent` = cells expressing (value > 0) / total cells in cluster —
  **normalisation-invariant, so exact**.
- `expression_level` = **mean over *expressing cells only*** (Σ / n_expressing),
  NOT over all cells (the detail scanpy's default gets wrong).
- **Normalisation**: SOP uses the SCEA *Normalised Counts* table; a GEO-raw dataset
  (one that never went through SCEA) instead replicates the *method* with **CPM**
  (linear) — `level` cannot be SCEA-identical, but extent is exact.
- **Filter**: `extent > 0.2` (from the old repo's `process_metadata.py`);
  `Cluster.total_gene_count` (any expression) vs `filtered_gene_count` (> 0.2).

**Compute**: two chunked streaming passes over the 1 GB 10x `.mtx.gz` (cell totals
for CPM, then per-cluster×gene sums via `bincount`) — dense accumulators genes×clusters
only, ~95 s, low memory. The matrix lives in `.cache/` (gitignored).

**Scale & outputs** (worked example: 17,561 genes, 194k cells → **584,710 rows**
after the filter):
- `projects/<p>/expression.tsv` — filtered rows, plain/diffable, **committed** (~32 MB).
- `projects/<p>/expression_report.md` — per-cluster cells + total/filtered gene counts.
- `expression/vfb_scRNAseq_expression_<project>.owl.gz` — **committed, loadable**
  (~13.5 MB; 584,710 annotated `expresses` axioms).
- `total/filtered_gene_count` also set on the `Cluster` entities in the metadata OWL.

**Release layout.** The VFB-loadable OWL is aggregated across projects in two
top-level folders so the loader picks them up from one place (mirrors the old
repo's `metadata_release_files/` + `expression_data/`):
`metadata/vfb_scRNAseq_metadata_<project>.owl` (dataset metadata) and
`expression/vfb_scRNAseq_expression_<project>.owl.gz` (expression). The build
scripts write there directly; per-project dirs keep only the
intermediates/diffables (`.ttl`, `.ofn`, `expression.tsv`, report, counts).

**Emission — efficient, NOT linkml-owl.** linkml-owl renders *and re-parses* the
template per row (~1.4 ms/row → ~14 min / ~3 GB at this scale). Instead we render
the schema's `gene` `owl.template` per row (Jinja) straight to one `.ofn` (~0.6 s),
then a single `robot convert` → `.owl` → gzip (~30 s total). linkml-owl is kept for
the *metadata* (small). NB the `gene` template was fixed for the modern
`py-horned-owl` backend (quoted/typed literals, `xsd:` prefix); gene fillers are
`FlyBase:FBgn…` CURIEs.

**TODO — gene id currency.** Gene ids are taken as published in the GEO features
file, so some are no longer current FlyBase ids: Davie 2018 has 137 secondary FBgns
(5 of them split) and 1 with no current gene; Kurmangaliyev 2020 has 87 secondary and
1 withdrawn (FlyBase Chado, 2026-09-23). Expression rows for these won't link to the
current gene in VFB. To do: map secondary → current FBgns at emission (handling
merges/splits), as the old repo's `update_FBgns_in_files.py` did.

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

## Second project: Davie 2018

`projects/davie_2018/` — Davie et al. 2018, *A Single-Cell Transcriptome Atlas of
the Aging Drosophila Brain* (Cell; GSE107451, PMID 29909982, FBrf0239740). Already
in VFB from the old FlyBase/SCEA mechanism (`FBlc0006090`, SCEA `E-CURD-91`,
59 clusters); rebuilt here from GEO. Curator decisions:

- **Scope: the 57K 10x set only** — the paper's stringently filtered atlas, 26 runs
  (12 DGRP-551 + 14 w1118, adults 0–50 days). The rest of GSE107451 (157K lenient
  set, Drop-seq, SMART-seq2/CEL-seq2 on R23E10 cells, bulk) is excluded by the
  `title_pattern` regex. One GSM = one replicate = one library, so Sample:Assay 1:1.
- **One row per author cluster, never merged by cell type.** Curators annotate the
  clusters the authors defined; two clusters of the same type stay two Clusters with
  the same FBbt term (unlike the old SCEA load, which merged by type). The relation
  is *composed primarily of* (RO:0002473), so not every cell need be of the type.
  Seven Clusterings, built by `projects/davie_2018/build_clusters.py`:
  the 87 res-2.0 clusters (Table S2's "87 initial clusters"); the 5 res-8.0 clusters
  Table S2 annotates; the authors' sub-clusterings of res-2.0 clusters 20, 27, 42 and
  64; and the named groups of the neuropeptide re-clustering (Figure 2K) — 125
  Clusters. res-2.0/res-8.0 membership comes from GEO's `res.2`/`res.8` columns;
  sub-cluster membership (no id column in GEO) from the authors' per-cell
  `annotation`. A cell is in one cluster per Clustering, so expression stats are
  computed per Clustering from a barcode→cluster membership file.
- **Sub-clusters are *part of* their parent cluster.** The 18 clusters of the four
  sub-clusterings carry `parent_cluster` (schema slot on `Cluster`, BFO:0000050
  *part of*, the same predicate as Cluster→Clustering) pointing at the res-2.0
  cluster the authors re-clustered — nested by construction. res-8.0 clusters and
  the neuropeptide groups are not given a parent: res-8.0 is an independent
  resolution (its overlap with res-2.0 is empirical, not an author statement) and the
  neuropeptide groups draw cells from many res-2.0 clusters.
- **Typing from the authors, not re-analysis.** Each cluster takes the authors' GEO
  annotation (a sub-clustered res-2.0 cluster takes its Table S2 parent call). Table
  S2 is recorded per cluster (`s2_annotation`); where it makes a different call the
  cluster carries `author_conflict` and `verification_needed` (14 clusters). Mapping
  takes the authors' type at face value — no downgrading on our own reading of
  markers, cell counts or contamination; a grouped call ("Pm1/Pm2") maps to the
  common parent. Type-level mappings live in `type_mapping/` and are copied per
  cluster into `mapping/`.
- **Numbered clusters held.** No author class exists, so there is no broad anchor;
  clusters the authors left numbered are `unannotated` and emitted without an FBbt
  link (`hold_unidentified: true`).
- **Fresh VFBseq ids, no FBlc link.** Retiring the old load is handled outside
  this repo. The old FBbt assignments are kept only as a cross-check
  (`prior_mapping_FBlc0006090.tsv`, crosswalked to the authors' types by name +
  cell count).
- **Sex mixed** (20 female + 20 male brains per run); **stocks** FBst0055026
  (DGRP-551, BDSC 55026) and FBst0003605 (w[1118], BDSC 3605), from the Key
  Resources Table via Chado; stages = FBdv "day N of adulthood".
- Evidence for reports: the open-access JATS full text (PMC6086935) in the local
  index, plus Tables S2 (annotation method + references per cluster) and S3
  (markers per res-2.0 cluster) joined per author type in `supp_evidence.json`;
  reports are per author type (`reports/<type>.md`).
