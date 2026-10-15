# Design decisions & reference notes

This document records the *why* behind the repo's structure and the external
conventions it must conform to. It is the shareable, version-controlled home for
decisions that would otherwise only live in a maintainer's head.

## Purpose

Produce RDF metadata for *Drosophila* single-cell RNA-seq data: dataset / sample
/ cluster annotations, linking clusters to **FBbt** anatomy terms, plus summary
expression statistics (extent and level per cluster × gene) computed the FlyBase way.

## Architecture

Built on the [atlas-chat](https://github.com/Cellular-Semantics/atlas-chat)
template (literature-grounded, quote-validated cell type reports). The repo's
`.claude/` carries adapted atlas-chat agents and hooks, plus skills
(`local-paper-index`, `anndata-zarr-summary`).

**Two schemas, two jobs** — the key structural decision:

- **Working / annotation format** — `projects/<id>/cell_type_annotations.json`
  (atlas-chat shape). Where curation happens: cluster
  labels, generated literature reports, and the proposed FBbt mapping.
- **Publishing format** — `src/vfb_scrnaseq/schema/VFB_scRNAseq_schema.yaml`
  (LinkML). The RDF target: `Dataset / Sample / Assay / Clustering / Cluster`,
  the FBbt `cell_type` link, and the expression slots. Because it is LinkML,
  RDF/TTL is produced with `linkml-convert`; predicates come from the schema's
  `slot_uri` / `class_uri` / `owl.fstring` annotations.

### Schema master copy & deprecation

`VFB_scRNAseq_schema.yaml` here is the **new master copy**, imported from
`VirtualFlyBrain/vfb-scRNAseq-ontology` and extended here since (the `VFBseq`
prefix, stock, sex, site, `parent_cluster`, gene-count and expression slots). That
repo will be **deprecated** once this one is running. Remaining clean-up: legacy
FlyBase / TSV-loader wording in some slot descriptions.

### Pipeline (cell-type-annotation focus)

```
project config (+ project script for bespoke clusterings)
  -> cell_type_annotations.json   (build_annotations_from_geo.py, or from the authors' AnnData
                                   files: fetch_h5ad.py + build_annotations_from_h5ad.py;
                                   one entry per author cluster)
  -> samples.json                 (build_samples_from_geo.py / build_samples_from_arrayexpress.py:
                                   Samples / Assays / Clusterings)
  -> per-type reports             (write-cell-type-report agent; Atlas-reporter paper index)
  -> FBbt mapping JSON            (map-clusters-to-fbbt agent via OLS; assign_placeholders.py;
                                   type-level mappings copied per cluster by expand_type_mappings.py)
  -> mapping.tsv + human review   (collate_mapping.py)
  -> entities -> metadata OWL/TTL (build_rdf.py: linkml-validate / -convert / linkml-owl)
  -> current FlyBase gene ids     (update_gene_ids.py)
  -> expression stats + OWL       (build_expression.py, then build_rdf.py again for gene counts)
  -> CI                           (tests, file validation, mapping.tsv freshness, weekly
                                   FBbt / FlyBase release check)
```

See *Adding a new dataset* (end of this document) for the step-by-step checklist.

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

- **Metadata only — never the expression matrix.** The matrix is read only by
  `stats.py` (`build_expression.py`). (Same philosophy as the `anndata-zarr-summary`
  skill, which reads `obs/` only.)
- **Raw characteristics in, ontology mapping out.** `ingest` surfaces GEO's raw
  strings (`stage_hint`, `sex_hint`, `characteristic(...)`); mapping them onto
  FBdv stages and the schema's `sex` enum needs ontology lookup and lives in
  `build.py`.
- **`supplementary_files` is the hook for cluster labels from GEO** — many atlases
  attach a per-cell metadata file with cluster assignments; `ingest` captures
  those URLs, so they are an authoritative alternative to scraping supp tables.

**ArrayExpress** (`src/vfb_scrnaseq/ingest_arrayexpress.py`,
`scripts/build_samples_from_arrayexpress.py`) is the non-GEO source: the experiment's
MAGE-TAB IDF + SDRF are fetched over HTTPS from the BioStudies FTP area (cached in
`.cache/`) and grouped into Samples and Assays by config — `sample_columns` (the SDRF
columns that define one biological sample), `assay_column` or `assay_regex` (the
library / plate), `assay_xrefs` (ENA / BioSamples ids, only when single-valued per
assay) and curated `sex_map` / `age_map` / `tissue_map` / `stock_map`. `sdrf_corrections`
records curator fixes to SDRF values that the paper contradicts (applied before grouping;
the note is kept on each affected Sample as `curation_notes`). It writes the same
`samples.json` as the GEO builder. A Sample may have several FBbt tissues. The `vfb:ArrayExpress`
Site node was added to the KB on 2026-10-07.

GEOparse / pysradb are optional swap-ins (e.g. richer SOFT parsing, GSM→SRX/SRR
resolution) but are **not required**; the stdlib path covers what the schema records.

### `retrieve-dataset` skill — not copied (deferred)

The upstream `Cellular-Semantics/claude-skills` `retrieve-dataset` skill was
**deliberately not copied**. It is a **MapMyCells annotation-transfer** tool
(load → convert → emit a `cell_id → cluster` JSON for F1 scoring against the
Allen/CL taxonomies), pulling the `annotation-transfer` CLI plus R/Seurat — none
of which serves FBbt mapping. Its only reusable kernel (multi-format → AnnData +
`obs` inspection) is already covered by `anndata-zarr-summary` for the obs path.
It was not needed for expression either: the authors' AnnData files are read
directly with h5py (`ingest_h5ad.py`).

## General curation rules

Rules that apply to every project (agreed with the curator; the per-project sections
below record how each was applied).

- **The unit is the authors' cluster.** One row = one cluster the authors defined
  (it gets a VFBseq id and an FBbt annotation). Clusters are never merged by cell
  type: two clusters of the same type stay two Clusters with the same FBbt term
  (unlike the old SCEA loads, which re-analysed and merged by type).
- **Complete sets, not cherry-picking.** Choose which kinds of author analysis to
  load (e.g. per-tissue 10x vs integrated vs cross-tissue), then load every
  clustering and every cluster of the chosen kinds — duplicates across technologies
  included. Relevance to VFB users (e.g. the nervous system) can justify leaving out
  a whole kind of analysis, never individual clusterings or clusters.
- **Typing comes from the authors, not from re-analysis.** Map each cluster from what
  the authors say it is (GEO metadata, paper, supplementary tables). Curators do not
  overturn or hedge the authors' typing on the basis of their own reading of markers,
  cell counts, likely contamination or dissection details. Where author sources
  disagree, the project config decides which is authoritative and the other is
  recorded as a flag (`verification_needed`).
- **Relation is *composed primarily of*** (RO:0002473), so not every cell in a cluster
  need be of the annotated type. A cluster the authors name for two co-expressed
  markers may be mapped to both classes (`additional_matches`).
- **No FBbt term → held, and not loaded.** A cluster with no adequate FBbt term is
  held: it is not given a generic fallback term just to have one, and it is left out
  of the build entirely (no VFBseq id, no Cluster entity, no expression rows). Its
  cells still count towards the Dataset's total/filtered gene counts, which measure
  what the experiment detected. VFB is organised around cell types, so an untyped
  cluster adds nothing there (curator decision, 2026-10-14). Held clusters stay in
  `mapping.tsv` (`kind` held, with a `hold_reason`) so they can be loaded if a term
  becomes available. `collate_mapping.py` marks any mapping with a null `best_match`
  as held. Hold reasons: `no term` (an author type with no adequate FBbt term),
  `untyped` (the authors left the cluster numbered), `undefined class` (a class in
  `hold_classes`), and per-project values from `unidentified.hold_reasons` (FCA:
  `leftover`, `artefact`, `unassigned`).
- **New FBbt terms from gene expression alone are the exception.** `new_term_needed`
  records a gap; it is not a queue of requests. Do not request terms defined only by
  transcriptomic clusters/markers as a matter of course (we do not want thousands of
  expression-defined terms); any request needs explicit curator sign-off.
- **Reuse entities that are truly identical; curate the source study first.** When a
  study reuses another study's material — the same flies/dissections (Samples) or the
  same sequencing libraries (Assays), e.g. the Aging Fly Cell Atlas re-analysing the
  FCA's 5-day head and body libraries — its build references the existing entities by
  their VFBseq ids instead of minting duplicates. The reused entities stay owned by
  (and are emitted only by) the project that first curated them; the reusing project
  links to them from its own Clusterings (`associated_sample_or_assay_for_clustering`).
  Only identical entities are reused: a re-analysis is a new Clustering with new
  Clusters, even over the same cells. If the source study has not been curated yet,
  the build stops and tells the curator, with the suggestion to curate that study
  first (so the shared Samples/Assays get their ids, labels and metadata there).
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

When a request is opened, add it to `checks/pending_fbbt_requests.json` (issue,
labels, affected clusters, `status: pending`) so the weekly FBbt release check opens
a re-mapping reminder once FBbt releases the terms (see *Continuous integration*).

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
- `local-paper-index` (the genuinely useful, free part of atlas-chat) is run from a
  sibling clone of **Atlas-reporter** (atlas-chat's new name,
  `Cellular-Semantics/Atlas-reporter`), pinned to commit `2acd38e`, with the project
  **symlinked** into its `projects/`, so the built index and generated `reports/` land
  back in this repo:

  ```sh
  git clone https://github.com/Cellular-Semantics/Atlas-reporter.git ~/git/Atlas-reporter
  cd ~/git/Atlas-reporter && git checkout 2acd38e && uv sync --extra local-index
  mkdir -p projects && ln -s <this repo>/projects/<name> projects/<name>
  uv run python scripts/setup_local_index.py add --project <name> --doi <DOI> \
      --jats paper.xml --role atlas            # or --pdf paper.pdf
  uv run python scripts/setup_local_index.py search --project <name> --query "..." -k 5
  ```

  The existing indexes were built with atlas-chat commit `4c90b6c` (cited in the
  projects' `provenance.json`). That commit survives upstream only on feature
  branches, but the local-index code (`setup_local_index.py`, the JATS/PDF parsers,
  `local_snippet_index.py`, `pyproject.toml`) is byte-identical at `2acd38e`, and
  re-ingesting the Davie paper there reproduced its index exactly (chunks, snippets,
  embeddings), so nothing built at `4c90b6c` needs regenerating.
- Reports are **background evidence, not mapping decisions**; `mapping.tsv` is the
  authoritative copy. `collate_mapping.py` adds a generic `reports/README.md` saying so
  (template `src/vfb_scrnaseq/templates/reports_README.md`) when a project's reports
  folder has none; an existing README is never overwritten.

## Generic pipeline vs per-project config

The scripts in `scripts/` (e.g. `build_annotations_from_geo.py`,
`build_annotations_from_h5ad.py`, `assign_placeholders.py`, `expand_type_mappings.py`,
`collate_mapping.py`, `build_expression.py`) are **dataset-agnostic drivers**.
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
    author class, so no broad anchor can be chosen; e.g. Davie 2018);
  - `hold_reasons` — `hold_reason` (mapping.tsv) of an `unannotated` entry, by its
    type (e.g. FCA `{unannotated: leftover, artefact: artefact, unknown: unassigned}`);
    default `untyped`.
- **`sample_build.title_pattern`** — how GSM titles split into set / timepoint /
  biological replicate (/ technical replicate): the default
  `set_timepoint_biorep_techrep`, or `regex:` with named groups. GSMs that do not
  match are out of the project's scope (lets one GEO series contribute a subset).
- **`sample_build.sex: mixed`** — curator-confirmed pooled-sex samples; the
  single-valued `sex` slot stays unset without the "check the paper" warning.
- **`annotations.barcode_column`** — the per-cell metadata column that matches the
  matrix barcodes (default `barcode`).
- **`prior_mapping`** — optional TSV of a previous load's FBbt terms per cluster
  (`cluster_label`, `old_fbbt_id`, `old_fbbt_label`); `collate_mapping.py` adds
  `prior_fbbt_*` / `prior_agrees` columns as a cross-check while reviewing a dataset
  that was loaded before by the old FlyBase/SCEA mechanism. Never an input to the
  mapping itself; drop it once the review is done (as for Davie and Kurmangaliyev).
- **`annotations.extra_clusterings`** — further author clusterings in other GEO
  metadata files (`{id, name, source_file, label_prefix}`), ingested by
  `build_annotations_from_geo.py` as entries of that Clustering with prefixed labels
  (e.g. Kurmangaliyev's early dataset → `early_L1`); label rules apply to the authors'
  own cluster id. The main clustering can be prefixed and named the same way
  (`annotations.label_prefix` / `clustering_id` / `clustering_name`, e.g. `main_L1`). **`unidentified.clustering_class_anchors.<clustering>`** overrides the
  class anchors for one clustering (e.g. immature anchors for an early-stage one).
  **`expression.extra_parts`** adds further matrices (same genes) to the expression
  stats, with the matching `label_prefix`.
- **`annotations.review_columns`** — extra per-cluster fields from
  `cell_type_annotations.json` shown after the cluster key in `mapping.tsv` (e.g.
  Davie's clustering, the authors' cluster id, the Table S2 call and any conflict).
  Re-running `collate_mapping.py` keeps the `reviewed`/`review_notes` already there;
  a `reviewed` mark of `y`/`yes` is converted to the date (ISO) of that run.
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
GEO ingester and `build_annotations_from_h5ad.py` (with
`build_samples_from_arrayexpress.py` for samples) the AnnData / ArrayExpress one;
both emit the same `cell_type_annotations.json`, with the config/placeholder/collate
layers downstream unchanged. Another source (e.g. CELLxGENE) would be a further
sibling script.

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
`check_provenance.py` hook): what the build was made from and how, so a result can
be understood, reproduced and re-checked when a source changes.

- **summary** — a short paragraph: what the project is, what was built, from what;
- **decisions** — dated `{date, by, decision}` entries in date order, `by` being
  `curator` (decided or approved by the curator) or `pipeline` (a method or build
  choice); general rules that shaped the project are included with their own dates;
- **checks** — dated `{date, check, result}` verifications (FBbt term currency,
  cross-checks against earlier loads, marker spot checks, conversion checks);
- **people**, **pipeline** (repo, plain `commit`, `uncommitted_changes`);
- **ontologies** — id, version + `version_iri`, how and when accessed;
- **data_sources** — publications, preprints, archive datasets, the authors' own
  files, previous loads (`previous_load`, e.g. an FBlc) and other projects of this
  repo whose entities or mappings are reused (`project`), with the specific files
  used (`path`, `sha256` + byte size);
- **software** — tools, libraries, services (with versions: e.g. FlyBase Chado with
  its FlyBase release) and repositories (with commits);
- **models** — the orchestrating, mapping/report and embedding models.

Every entry uses the same field names: `id` is an identifier only (DOI, accession,
CURIE, model id, or a short slug such as `flybase-chado`), `label` a short name or
title, `type` the kind of thing from the section's list, `description` free text on
how or why it was used, `xrefs` other identifiers of the same thing as CURIEs
(`PMID:`, `PMCID:`, `FlyBase:FBrf…`), and `accessed_at` the date it was retrieved or
queried.

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
- **`sex`:** set from GEO / the ArrayExpress SDRF where present, else curator-confirmed from the paper;
  unset only when genuinely unknown (see the *sex* note below).
- **`Assay.method`:** the sequencing method as an FBcv term (e.g. `FBcv:0009008`
  "10x sequencing"), from `sample_build`.
- **Labels.** A Sample's label is its raw tissue, age, sex/genotype and replicate (plus
  the authors' sample id where samples are otherwise alike: `sample_label_id`, e.g.
  FCA "FCA4"). An Assay's label is its Sample's plus what the assay is
  (`sample_build.assay_label`: `unit`, optional `pattern` on the library id and
  `of_total`), e.g. "optic lobes, 24h APF, W1118 rep A, 10x lane 1 of 4
  (Kurmangaliyev 2020)" (the paper: 4 Chromium lanes per W1118 sample, one GSM each),
  "brain, 15 Days, DGRP-551 rep r1, 10x library (Davie 2018)", "…, FCA46, 10x library
  S14 (Li 2022)", "…, Smart-seq2 plate P5 (Li 2022)". Accessions stay as dbxrefs
  (`xref_library_id` adds the full library id where the label shortens it). Sample and
  Assay labels are unique within a project (tested).
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
  This is the **VFB-pipeline-compatible**
  output → `projects/<name>/<accession>.ofn`.
- **Flat RDF** (`--format ttl`) via **`linkml-convert`**, which uses `slot_uri`/
  `class_uri` only — simpler generic RDF (ontology-term links are plain triples,
  no OWL restrictions), Container node stripped → `<accession>.ttl`.
- **OWL/XML** — the `.ofn` is then converted to RDF/XML with **`robot convert`** →
  `metadata/vfb_scRNAseq_metadata_<project>.owl` (lossless; round-trip verified).
  (The expression axioms are not emitted here: see *Emission* under expression.) ROBOT is an external Java tool,
  not a pip/uv dep, so this step is skipped with a warning if `robot` isn't on PATH.

Both are preceded by **`linkml-validate`** (types, ranges, required slots, rejects
unknown slots). Use OWL for VFB/reasoning; flat RDF for generic SPARQL. See the
`owl.fstring` discussion — the OWL path restores the existential-restriction
semantics the flat path drops, and is required for the expression-stats axioms.

Schema use: the LinkML schema now drives **validation** (`linkml-validate`),
**flat RDF** (`linkml-convert`), and **OWL** (`linkml-owl`) — the `owl.*`
annotations are the linkml-owl input format the schema was authored for.

**Caveats / deferred** (deliberately not done here):
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
FBbt:00007004). `build_samples_from_geo.py` takes sex from the GEO characteristic
(`build_samples_from_arrayexpress.py`: from the SDRF via `sex_column` / `sex_map`),
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
- **Normalisation**: SOP uses the SCEA *Normalised Counts* table; we replicate the
  *method* with **CPM** (linear) for every dataset (curator decision 2026-10-14) —
  `level` cannot be SCEA-identical, but extent is exact.
- **Filter**: `extent > 0.2` (from the old repo's `process_metadata.py`);
  `Cluster.total_gene_count` (any expression) vs `filtered_gene_count` (> 0.2).
  The Dataset's counts are genes with any expression / extent > 0.2 in at least one
  cluster, held clusters included (they measure what the experiment detected), so
  the filtered count can exceed the distinct genes in `expression.tsv`.

**Compute**: two chunked streaming passes over the 1 GB 10x `.mtx.gz` (cell totals
for CPM, then per-cluster×gene sums via `bincount`) — dense accumulators genes×clusters
only, ~95 s, low memory. The matrix lives in `.cache/` (gitignored).

**h5ad source** (`expression.source: h5ad`; the Fly Cell Atlas): the authors' per-analysis
files hold *normalised* values, not counts. One file per Clustering is read in one
chunked pass (`ingest_h5ad.iter_matrix`: dense, CSR or CSC; `raw` when present, as
the main `X` may be scaled highly-variable genes only), and `expression.values` converts
back to CPM — `log1p_cp10k` (log(counts per 10k + 1)) → (eˣ − 1) × 100, `log2_cpm1`
(log2(CPM + 1)) → 2ˣ − 1. The build checks the conversion: the median cell must sum to
1e6 CPM and none above (cells may sum lower where the authors normalised before dropping
genes, e.g. FCA Smart-seq2 dilp2IPC; those values are still CPM). A cell's cluster is
`<clustering>_<annotation>` (or the clustering's `fixed_annotation`), and cluster
sizes must equal `cell_type_annotations.json`. Files may carry different gene sets; a
gene a file lacks is unexpressed in its clusters. `expression.gzip_tsv: true` writes
`expression.tsv.gz` (deterministic gzip) for datasets too large to commit plain.

**Scale & outputs** (Kurmangaliyev, main + early: 17,556 genes, 209k cells → **686,568
rows** after the filter):
- `projects/<p>/expression.tsv` — filtered rows, plain/diffable, **committed** (~40 MB;
  `expression.tsv.gz` with `gzip_tsv`).
- `projects/<p>/expression_report.md` — per-cluster cells + total/filtered gene counts.
- `expression/vfb_scRNAseq_expression_<project>.owl.gz` — **committed, loadable**
  (~16 MB; one annotated `expresses` axiom per row).
- `total/filtered_gene_count` also set on the `Cluster` and `Dataset` entities in the
  metadata OWL.

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

**Gene id currency.** Gene ids are published with the data (GEO features file), so
some are no longer current FlyBase genes. `scripts/update_gene_ids.py` queries FlyBase
Chado (`psql -h chado.flybase.org -U flybase flybase`; a current gene's FlyBase
dbxrefs list its own FBgn as current and the retired FBgns it absorbed as non-current)
and writes a committed `projects/<p>/gene_id_map.tsv`, which the expression build
applies (`expression.gene_id_map`) as the matrix streams. The table header records
the FlyBase release (read from the flybase.org homepage, e.g. "FB2026_03, released
September 17, 2026" — the website and Chado are updated together) and Chado's
last-modified date (the release's data freeze).

**h5ad projects are keyed by gene symbol** (the matrix's gene names). A symbol takes
the FBgn given in the authors' files (`var`/`raw.var` column `ID`, pooled over the
project's files and `expression.gene_ids_from` projects) and is mapped as below; a
symbol with no FBgn is looked up by name among *D. melanogaster* genes: a current
symbol → that gene; else a synonym of exactly one gene → that gene; a synonym of
several genes (**ambiguous**) or of none (**unmatched**) → dropped.

Mapping rules:

- **secondary** id of one current gene → that gene (and its current symbol);
- **merge** (several input ids → one current gene) → counts summed per cell before
  extent/level, so a cell expressing both is counted once;
- **split** (one retired id → several current genes) → dropped, since the reads
  can't be attributed (curator decision); **withdrawn** → dropped.

As of FB2026_03: Davie 132 secondary (5 merges), 5 splits, 1 withdrawn; Kurmangaliyev
86 secondary (3 merges), 1 split, 1 withdrawn; symbols refreshed for every gene (FCA:
see *Fly Cell Atlas*, expression). The
Chado result agreed with FlyBase's `fbgn_annotation_ID_fb_2026_03.tsv` for every
secondary/withdrawn id. Re-run the script (and the expression build) to move to a
later FlyBase release; the weekly release check opens a reminder issue when one is out
(see *Continuous integration*).

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
- **Sparse characteristics:** only `tissue` (optic lobes) and `age` — **no sex** in
  GEO; set to female from the paper (`sample_build.sex`).
- **Stages are APF time windows** (`0-96h`, `24h`, `48h`, `72h`, `96h APF`) →
  map to FBdv pupal stages.
- **Two sub-datasets, `early` and `main`**, in the supplementary files:
  `matrix_{early,main}.mtx.gz` (MatrixMarket — the FlyBase/fuzzy-onions format),
  `barcodes_*`, `features_*`, and `metadata_{early,main}.tsv.gz`.
- **Cluster labels:** the `metadata_*.tsv.gz` files hold per-cell cluster /
  cell-type assignments at three granularity levels — `class` (4: N/G/C/R),
  `type` (187 in `main`), `subtype` (196 in `main`). The `early` subset is mostly
  provisional `x*` clusters.

**First annotation pass** (since extended: the `early` dataset was added in the
2026-10 regeneration below, 306 entries in all): scope = **`main`** subset only; granularity =
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

## Continuous integration

`.github/workflows/ci.yml` runs on every PR and push to `main` (offline, ~seconds):
`pytest`; `scripts/validate_project_files.py`, which feeds every committed mapping /
type_mapping / term-request / provenance / samples file through the same
`.claude/hooks/check_*.py` validators Claude Code uses on write (hand edits otherwise
bypass them); and `scripts/check_mapping_tsv.py`, which fails if a `mapping.tsv` no
longer matches what `collate_mapping.py` would produce.

`.github/workflows/fbbt-release-check.yml` runs weekly (and on demand).
`scripts/check_fbbt_release.py` compares OLS's current FBbt release with the one
recorded in `checks/fbbt_last_checked.json` and only when it is newer re-verifies
every project's FBbt terms (current, non-obsolete, label unchanged). On success the
record is updated and committed by the workflow; on failure the job fails and the
record is kept, so the next run re-checks.

The same run follows up **pending FBbt term requests** (`checks/pending_fbbt_requests.json`:
FBbt issue, requested labels, clusters waiting on them). A request whose FBbt issue was
closed on or before the new release's date is taken to be in that release: the job
opens a reminder issue in this repo listing the clusters to re-map (with the new term
ids where the requested labels are found in the release, and the closing reason if not
"completed"), and marks the request `released` so it is reported once. A request closed
after the release waits for the next one.

It also checks **FlyBase releases** (`scripts/check_flybase_release.py`): if flybase.org
reports a release newer than the one recorded in the projects' `gene_id_map.tsv`
headers, it re-classifies each project's input gene ids against FlyBase Chado (the
committed maps list them, so no GEO files are needed) and, if any id or symbol used by
the expression output changed, opens an issue with the counts and the commands to run
(`update_gene_ids.py` → `build_expression.py` → `build_rdf.py`). No change → the
release is recorded without an issue; Chado unreachable from CI → the issue is opened
without counts. `checks/flybase_release_check.json` makes each release reported once.
The full rebuild is not automated (it needs the GEO matrices / h5ad files and ROBOT).
(`checks/flybase_release_check.json` is created on the first FlyBase release check.) Not run on PRs: it needs OLS, which is
sometimes unavailable.

### 2026-10 regeneration under the general curation rules

The main dataset already had one row per author cluster: the paper's clustering
"revealed 196 transcriptionally distinct cell populations", which are the 196
`subtype` values; `type` only groups them (T4/T5 matched eight clusters; Dm3 and Tm9
two each). Its clusters, mappings and ids are unchanged; its labels now carry the
clustering prefix (`main_L1`, alongside `early_L1`), with the registry keys renamed so
every cluster kept its VFBseq id. The DGRP samples stay as the GEO-based pooled
samples (`DGRP_All_A/B`): the per-animal samples recovered by demultiplexing (3
animals × 9 timepoints × 2 rounds) are not modelled separately — curator decision;
clusters span timepoints and genotypes regardless. Added:

- **The early dataset (0–24h APF)** — the authors' separate clustering of 0/12/24h
  APF cells (GEO `metadata_early` / `matrix_early`; 24h cells are in both datasets) —
  as 110 Clusters of the existing `early` Clustering (`early_<cluster>`): 28 named
  clusters mapped to **immature** FBbt terms (these are developing neurons; unsplit
  T4.T5 / Dm3 / Tm9 / R1.6 / R7.8 map to the immature group or nearest parent), 20
  numbered N/G clusters with early anchors (N → *immature adult optic lobe neuron*;
  G → *glial cell*, as FBbt has no immature optic-lobe glia term), 62 held (class `x`
  = unresolved, and class C).
- **Held clusters not loaded (2026-10-14):** the 74 held clusters (12 main class C,
  62 early) are left out of the build; 232 Clusters are loaded (184 main, 48 early).
- **Cross-check against the old FlyBase/SCEA load (FBlc0006237)** during review:
  183 of 184 comparable main clusters agreed (crosswalk since removed).

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
  clusters the authors left numbered are `unannotated` and held
  (`hold_unidentified: true`). With the one named type lacking a term (Hsp), 43
  clusters are held and not loaded; 82 Clusters are loaded.
- **Fresh VFBseq ids, no FBlc link.** Retiring the old load is handled outside
  this repo. The old FBbt assignments were used as a cross-check during review
  (crosswalked to the authors' types by name + cell count; since removed).
- **Sex mixed** (20 female + 20 male brains per run); **stocks** FBst0055026
  (DGRP-551, BDSC 55026) and FBst0003605 (w[1118], BDSC 3605), from the Key
  Resources Table via Chado; stages = FBdv "day N of adulthood".
- Evidence for reports: the open-access JATS full text (PMC6086935) in the local
  index, plus Tables S2 (annotation method + references per cluster) and S3
  (markers per res-2.0 cluster) joined per author type in `supp_evidence.json`;
  reports are per author type (`reports/<type>.md`).

## Adding a new dataset

A checklist; each step's details are in the sections above. Nothing is loaded into
VFB until the release files are merged, so ids can still change during review.

1. **Scope with the curator first:** which part of the series (matrices / subsets),
   which author clusterings, where the authors' cluster labels live (GEO metadata,
   supplementary tables), whether the dataset was in the old FlyBase/SCEA load.
2. **`projects/<name>/config.yaml`:** `source` (DOI, PMID, FBrf fallback),
   `dataset` (GEO / BioProject / SRA, or ArrayExpress), `sample_build` (GEO: title
   pattern, sex, stocks from the paper's Key Resources Table resolved in FlyBase
   Chado, `age_map` → FBdv stage + FBbt tissue, `tissue_map` when one series has
   several tissues, clusterings (`sample_tissue_raw` links a clustering to the
   samples of that tissue); ArrayExpress: also
   `sample_columns`, `assay_column` / `assay_regex`, `sex_column` / `sex_map`,
   `sdrf_corrections`), `annotation_build` (h5ad obs columns,
   `unannotated_values`), `annotations` (label/class/timepoint
   columns, extra clusterings, prefixes), `unidentified` (rule, held classes, hold reasons,
   class anchors), `expression` (matrix files, extra parts; or `source: h5ad` with
   `values`, `gene_ids_from`, `gzip_tsv`), and `reuse` (Samples/Assays reused by
   VFBseq id from an already-curated project; see *General curation rules*).
3. **Clusters:** `build_annotations_from_geo.py` (one entry per author cluster;
   the main cluster label must be the authors' cluster, not a merged type). For
   layouts it can't express, a project script writes `cell_type_annotations.json`
   (as `projects/davie_2018/build_clusters.py` does).
   When the authors publish AnnData files (one per analysis), list each as an
   `h5ad` URL on its clustering, fetch with `fetch_h5ad.py` (into `.cache/h5ad/`; gzipped downloads are decompressed, and files the authors stored uncompressed are recompressed with HDF5's own gzip filter — lossless, verified dataset by dataset, read transparently by h5py — `--compress-existing` for files already cached) and
   build with `build_annotations_from_h5ad.py` (`annotation_build` config: the obs
   annotation / author ontology id / broad class / sex columns; `unannotated_values`
   are kept as one flagged entry per analysis, held and so not loaded). `ingest_h5ad.read_obs` reads obs with h5py from the
   old, 0.7 and 0.8+ AnnData layouts.
4. **Samples:** `build_samples_from_geo.py` (GEO) or `build_samples_from_arrayexpress.py`
   (ArrayExpress) → `samples.json`.
5. **Paper index:** add the paper (JATS if open access, else PDF) with the
   Atlas-reporter clone (`local-paper-index` skill); keep supplementary tables in
   `projects/<name>/supp/` (gitignored).
6. **Reports:** dispatch `write-cell-type-report` subagents in batches of related
   types.
7. **Mapping:** dispatch `map-clusters-to-fbbt` subagents (the curation rules are in
   the agent); `assign_placeholders.py` for class-anchored unnamed clusters. Check
   that broad-match parents are true ancestors of the members.
   When author types recur across clusterings, map once per type into
   `type_mapping/` and copy per cluster with `expand_type_mappings.py` (config
   `type_mapping.from` lets another project share them, the project's own
   `type_mapping/` taking precedence; `type_mapping.aliases` maps a type to its name
   in that project, e.g. AFCA "epithelial cell_head" → FCA "epithelial cell").
8. **Review:** `collate_mapping.py` → `mapping.tsv` (optionally with a `prior_mapping`
   crosswalk to the old load); curator changes are made in the mapping JSON with a
   `manual_edit` block.
9. **Build:** `update_gene_ids.py` (current FlyBase genes) → `build_rdf.py` (mints
   Cluster ids) → `build_expression.py` →
   `build_rdf.py` again (gene counts) → `verify_mappings.py`.
10. **Record:** `provenance.json` (ontology versions, files + sha256, software,
    models, curator decisions); add the release files to the `metadata/` and
    `expression/` READMEs and the project to README.
11. **Term requests:** only with curator sign-off; add each to
    `checks/pending_fbbt_requests.json`.
12. **Check:** `pytest`, `validate_project_files.py`, `check_mapping_tsv.py`; commit
    in stages on a branch and open a PR (CI runs the same checks).

## Fly Cell Atlas (Li et al. 2022)

Science 2022, PMID 35239393, FBrf0252876. Raw data only in ArrayExpress
(E-MTAB-10519 10x, E-MTAB-10628 Smart-seq2); the authors' analyses (annotations with
author-chosen FBbt ids, Leiden clusterings, counts) are h5ad/loom files at
flycellatlas.org. Previously in VFB from the SCEA reprocessing (FBlc0003846 / 4307 /
4785: SCEA's own cell calling, author annotations carried over, split by sex).

Curator decisions (2026-10-07):
- **Two projects, one per accession:** `li_2022_fca_10x`, `li_2022_fca_ss2`.
- **Analyses:** the 10x **Stringent** per-tissue analyses (17: 15 dissected tissues +
  whole head + whole body) and **all** Smart-seq2 per-tissue analyses (17: 15 tissues +
  dilp2 IPC + Akh CC). Left out: Relaxed (alternative filtering of the same cells),
  10x+SS2 Integrated (no head/body; mixing technologies would distort expression),
  cross-tissue (no finer neural/glial types — only hemocytes gained finer groups) and
  "All" (re-clustering of the same cells).
- **Unit:** one Cluster per author annotation per tissue analysis. FCA cell types were
  annotated by consensus across Leiden resolutions 0.8-8 ("a transcriptomic cluster
  detected at any clustering resolution"), so no single Leiden resolution matches the
  annotation; the (analysis, annotation) group is the authors' unit.
- **Samples:** 10x Sample = author sample (SDRF Extract Name = h5ad `sample_id`; 61),
  Assay = 10x library (160); Smart-seq2 Sample = tissue × sex × genotype × age (31),
  Assay = sorted plate (35). Tissue and sex follow the authors' SDRF annotation, not
  the drivers (e.g. oenocytes sorted with PromE800-GAL4 are "thorax" in 10x and
  "abdominal segment element" in Smart-seq2, as recorded). Samples overlap their
  tissues: "body" = adult postcephalic region (FBbt:00059181); "male reproductive
  gland" = accessory gland + ejaculatory duct + ejaculatory bulb. The supplement gives
  only one stock number (UAS-lamGFP, FBst0007378, fat body and trachea crosses), none for w1118.
  Fat body age: the SDRF says 3 days, the supplement 5 (all tissues are 5-day adults
  except male reproductive gland and testis, with stated reasons) — treated as an
  ArrayExpress error and corrected via `sdrf_corrections` (noted on the Samples).
- **Mapping:** the authors' FBbt ids as a first pass, upgraded where a better term now
  exists (adult-specific, or new terms for "Manual Annotation" types).
- **10x annotations** (`annotation` obs column of each Stringent h5ad; 370 entries,
  506,660 cells): the author ontology id (FBbt, several FBbt, or "Manual Annotation")
  is kept as `author_ontology_id` for the mapping step. Each analysis's "unannotated"
  (`leftover`) and "artefact" cells are one held entry each, not loaded. `R_annotation` (transferred relaxed
  label) is not used.
- **Smart-seq2 has no author clusters:** cells were typed one by one by a logistic-
  regression classifier trained on the 10x annotation (supplement, "Annotating
  Smart-Seq2 data"); the h5ad/loom carry only `transf_annotation` (235 tissue x label
  groups, many < 10 cells) and dilp2 IPC / Akh CC carry no annotation at all.
  Curator decision (2026-10-08): the predictions are the authors' typing, so each
  (tissue, predicted type) is a Cluster with `membership: label_transfer` (237 entries
  in all, 9,892 cells); "unknown" (`unassigned`) / "artefact" are held, not loaded. Author FBbt ids are copied
  from the same 10x tissue (`author_ontology_from`). dilp2 IPC and Akh CC are one
  Cluster each (`fixed_annotation`, `membership: sorted`), typed from the authors'
  sample description. Such Clusters are named "<type> cells, predicted / sorted (...)"
  and carry a `title` (IAO:0000115) saying they are not transcriptomic clusters.
- **Mapping (stage 3, FBbt 2026-10-01):** once per author type (252 types) in
  `li_2022_fca_10x/type_mapping/`, copied to every cluster of both projects by
  `expand_type_mappings.py`. 135 types with a single current author FBbt cell term were
  confirmed by script (`confirm_author_terms.py`: the author term, or its 'adult X'
  variant — 22 upgraded); the other 117 (no author term, several terms, tissue/organ or
  obsolete terms, stage-qualified labels) got reports and `map-clusters-to-fbbt`
  agents. Curator rules (2026-10-08): **cell-level terms only** — a tissue/organ author
  term maps to its cell-level equivalent, else the cluster is held; **no narrowing by
  dissected tissue** — generic types map at the authors' level in every tissue.
  11 types are held (no adequate cell term; not loaded); 5 curator edits (`manual_edit`).
- **Expression (stage 4):** from the same h5ad files, as CPM. 10x: each file's `raw.X`
  (all retained genes, log(counts per 10k + 1)); the main `X` is scaled HVGs only.
  Smart-seq2: `X` (all genes, log2(CPM + 1)). Genes keyed by symbol: FBgn from the 10x
  files' `ID` column (the leg file's raw IDs are undecodable; the Smart-seq2 files have
  none, so both take the other files' ids), the rest by symbol in Chado (FB2026_03):
  10x 16,270 current, 80 secondary, 15 synonym, 1 split; Smart-seq2 16,203 current,
  79 secondary, 26 synonym, 1 split, 2 unmatched (an unnamed gene and snRNA:U3).
  Held clusters get no expression rows; their cells still count towards the
  dataset-level gene counts. 10x: 16,363
  genes × 506,660 cells, 335 loaded clusters (35 held, 132,493 cells), 512,215 rows;
  Smart-seq2: 16,306 genes × 9,892 cells, 211 loaded clusters (26 held, 2,552 cells),
  426,111 rows.
  `expression.tsv.gz` is committed gzipped (too large otherwise).
- **Build (stage 5):** `build_rdf.py` for both projects (10x: 1 Dataset, 61 Samples,
  160 Assays, 17 Clusterings, 335 Clusters; Smart-seq2: 31 Samples, 35 Assays, 17
  Clusterings, 211 Clusters; held entries not loaded); publication FBrf0252876 from VFB production;
  `verify_mappings.py` OK (190 and 109 distinct FBbt terms), and every FBbt/FBdv/FBcv
  term on Samples, Assays and the Dataset checked current (FBdv 2026-09-30, FBcv
  2026-10-01). Recorded in each project's `provenance.json`.

## Aging Fly Cell Atlas (Lu et al. 2023)

Science 2023, PMID 37319212, FBrf0256843; GEO GSE218661 (`lu_2023_afca`). Whole head
and body, male and female, single-nucleus 10x, flies F1 of female W1118 × male Oregon R
(no stock numbers given). Replaces the old FlyBase/SCEA load FBlc0006422
(`scRNAseq_2023_AFCA`: per-age re-analyses with head and body merged and clusters
merged by type — D30 FBlc0006423, D50 FBlc0006887, D70 FBlc0007347, ~95–99 clusters
each, plus female/male sub-datasets), with fresh VFBseq ids; its type-level FBbt
assignments are a mapping cross-check only. Licence CC-BY-4.0. Curator decisions
2026-10-15.

- **New vs reused data.** GEO holds the new 30/50/70-day data: 72 GSMs (head/body ×
  sex × age × 6), each its own sample with one 10x library (the paper: "each age group
  had 12 samples with 6 females and 6 males"; heads and bodies processed separately).
  The 5-day data are the FCA's ("5d samples are from the FCA"): every 5-day cell in the
  authors' h5ad files is an FCA 10x Stringent Head / Body cell (same barcode and
  library, 100,311 head + 96,594 body; the files even carry the FCA annotation,
  identical to ours). So the 26 FCA head/body Samples (FCA1, FCA4–15; FCA2, FCA16–27)
  and their Assays are **reused** from `li_2022_fca_10x` by VFBseq id (config `reuse`),
  not re-minted — the first use of the entity-reuse rule.
- **Clusterings / Clusters are new.** The authors co-clustered the new ages with the
  5-day cells and re-annotated them all (`afca_annotation`: 91 head, 73 body types),
  so AFCA head and body are new Clusterings whose Clusters are the authors' types
  over all ages (not split by age; age stays on the Samples). The annotation differs
  from the FCA's for 23% of head / 36% of body 5-day cells (renamed with a tissue
  suffix, split, newly typed, a few moved), so a 5-day cell is in one FCA and one AFCA
  cluster. Each Clustering links (`associated_sample_or_assay_for_clustering`) to its
  36 new and 13 reused Samples.
- **Samples (stage 1):** `build_samples_from_geo.py` — 72 Samples / 72 Assays; stage
  day 30 / 50 / 70 of adulthood (FBdv:00007105 / 00007125 / 0010010); tissue head →
  *adult head*, body → *adult postcephalic region* (as for the FCA); sex from GEO.
- **Clusters (stage 2):** `build_annotations_from_h5ad.py` (files fetched gzipped from
  GEO by `fetch_h5ad.py` and decompressed): one entry per `afca_annotation` type per
  analysis over all ages, 164 in all (91 head, 73 body; 566,254 cells), with the
  authors' broad class and cell counts by sex, age and source (`count_columns`: FCA
  5-day vs AFCA). Held (listed, not loaded): the two "unannotated" groups (`leftover`;
  108,647 head and 6,250 body cells) and "neuron 1"–"neuron 17" (`untyped`, via
  `unidentified.rule`). 145 named types to map; 143 share a name with an FCA type
  (10 of them with a `_head`/`_body` suffix), new: "cyst cell", "seminal vesicle &
  testis epithelia".
- **Mapping (stage 3, FBbt 2026-10-01).** The AFCA labels were transferred from the
  FCA's annotations (preprint methods: from "the body and individual tissues (e.g.,
  gut, wing, leg, testis, ovary, fat body etc)", then checked against markers), so
  each AFCA type takes the FCA's curator-reviewed type-level mapping by name
  (`type_mapping.from: li_2022_fca_10x`): 133 by the same name, 10 `_head`/`_body`
  types by alias to the FCA type (no narrowing by dissected tissue). The two types
  the FCA lacks got reports (`reports/`; the PMC text is only Science's short article,
  so the preprint methods were used) and agent mappings in `lu_2023_afca/type_mapping/`:
  "cyst cell" → *cyst cell of testis* (broad; a grouped call over the FCA testis
  cyst-cell stages) and "seminal vesicle & testis epithelia" → *adult epithelial cell*
  (broad; FBbt has no cell-level term for seminal vesicle epithelium — the FCA held
  "seminal vesicle"). 143 Clusters mapped (130 distinct FBbt terms, all current); held:
  the FCA's no-term types "Poxn neuron" and "female reproductive system", plus the 17
  untyped and 2 leftover entries.
- **Cross-checks.** (1) The old load's terms: 93 of its 100 FBbt terms are used here;
  the 7 others are granularity or newer-term differences (e.g. old *antennal lobe
  projection neuron* vs the adult term now used; generic "neurons"). (2) The 5-day
  cells: where the FCA head/body analysis called an AFCA type's 5-day cells something
  with a different, non-broader FBbt term (≥ 20% of them), listed in
  `fca_5d_conflicts.tsv` (`fca_5d_conflicts.py`; 16 types, e.g. AFCA "T neuron T4/T5"
  whose 5-day cells the FCA called LC17, and R7 vs R8). Information for review only:
  the AFCA label is the authors' typing for these clusters. Most other differences
  are expected — the FCA head/body calls were coarser ("muscle cell", unannotated).
- **Expression (stage 4):** from `X` of the same files (log1p(CP10k), all genes, no
  `raw`) → CPM, as for the FCA 10x. Gene ids: symbols only in the AFCA files, so ids
  from the FCA 10x files' `ID` column (`gene_ids_from`), else Chado by symbol
  (FB2026_03): 15,891 current, 80 secondary, 20 synonym, 1 split; none unmatched.
  15,989 genes × 566,254 cells; 143 Clusters, 133,771 rows (extent > 0.2); held entries
  left out (126,573 cells) but counted in the Dataset's gene counts (total 15,962,
  filtered 5,399). A reused FCA 5-day cell counts towards its AFCA cluster here, as
  the authors grouped it (and towards its FCA cluster in `li_2022_fca_10x`). Checks:
  per-cluster filtered gene counts close to (mostly a little below) the FCA's for
  the same types; markers in place (Rh3/Rh4 in R7, SP in male accessory gland main
  cells, apolpp in fat body; indirect flight muscle led by bt / sls / Zasp52 / up —
  Act88F is below the cutoff in the FCA cluster too).
- **Build (stage 5):** `build_rdf.py`: 1 Dataset, 72 Samples, 72 Assays, 2 Clusterings
  (each linked to its 36 new and 13 reused FCA Samples), 143 Clusters; publication
  FBrf0256843 from VFB production; `verify_mappings.py` OK (130 FBbt terms); every
  FBbt/FBdv/FBcv term on Samples, Assays and the Dataset current in OLS (FBdv day 70
  is `FBdv:0010010`). Recorded in `provenance.json`.
- **Author files:** `GSE218661_adata_{head,body}_S_v1.0.h5ad` (no `raw`; `X` = all
  15,992 genes as log1p(CP10k), symbols only); a cell's library is in its name
  (`…_AFCA_female_head_30_S1`, or the FCA sample id). Not annotated: 108,647 head /
  6,250 body cells ("unannotated"); 17 numbered head types "neuron 1"–"neuron 17"
  (new in the paper, unnamed).

