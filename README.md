# vfb-scRNAseq

Produce RDF metadata for *Drosophila* single-cell RNA-seq data: dataset / sample
/ cluster annotations, linking clusters to **FBbt** anatomy terms, plus summary
expression statistics (extent and level per cluster × gene) computed the FlyBase way.

This repo is built on the [atlas-chat](https://github.com/Cellular-Semantics/atlas-chat)
template and will become the **new master copy** of the VFB scRNAseq LinkML
schema, deprecating
[`VirtualFlyBrain/vfb-scRNAseq-ontology`](https://github.com/VirtualFlyBrain/vfb-scRNAseq-ontology).

See [`docs/DESIGN.md`](docs/DESIGN.md) for the design decisions and external
conventions behind the structure below (the two-schema split, the `VFBseq` id
policy, FBbt mapping & term-request intake, and the FlyBase expression-stat
definitions).

## Two schemas, two jobs

- **Working / annotation format** — `projects/<id>/cell_type_annotations.json`
  (atlas-chat shape). Where curation happens: cluster labels, the generated
  literature reports, and the proposed FBbt mapping.
- **Publishing format** — `src/vfb_scrnaseq/schema/VFB_scRNAseq_schema.yaml`
  (LinkML). The RDF target: `Dataset / Sample / Assay / Clustering / Cluster`,
  the FBbt `cell_type` link, and the expression slots. **This file is the master
  copy** (imported from the old repo and extended here since).

## Pipeline (cell-type-annotation focus)

```
project config (+ project script for bespoke clusterings)
  -> author clusters + samples    (GEO: build_annotations_from_geo.py, build_samples_from_geo.py;
                                   ArrayExpress + h5ad: build_samples_from_arrayexpress.py,
                                   fetch_h5ad.py, build_annotations_from_h5ad.py)
  -> per-type reports             (write-cell-type-report agent)
  -> FBbt mapping + human review  (map-clusters-to-fbbt agent; expand_type_mappings.py;
                                   collate_mapping.py -> mapping.tsv)
  -> metadata RDF/OWL             (build_rdf.py -> metadata/)
  -> current FlyBase gene ids     (update_gene_ids.py)
  -> expression stats + OWL       (build_expression.py -> expression/)
```

To add a dataset, follow *Adding a new dataset* in [`docs/DESIGN.md`](docs/DESIGN.md#adding-a-new-dataset).

## Identifiers

Every published entity gets an opaque, registry-backed **`VFBseq_########`** IRI
(`src/vfb_scrnaseq/ids.py`, registry in `id_registry/`). GEO/SRA accessions
(GSE/GSM/PRJNA/SRP/GPL) are **cross-references**, carried in the schema's
`site` / `accession` slots — never used as the IRI. (Identifiers previously came
from FlyBase; that authority is being dropped.)

## Projects

- `projects/kurmangaliyev_2020/` — Kurmangaliyev et al. 2020, *Drosophila* visual
  system developmental atlas ([GSE156455](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE156455),
  PMID 33125872): the 24-96h main dataset (196 clusters) and the 0-24h early
  dataset (110 clusters); 232 with an FBbt term are loaded.
- `projects/davie_2018/` — Davie et al. 2018, ageing adult brain atlas
  ([GSE107451](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE107451),
  PMID 29909982), 57K 10x set (125 clusters; 82 with an FBbt term are loaded).
  Replaces the old FlyBase/SCEA load (FBlc0006090).
- `projects/li_2022_fca_10x/` and `projects/li_2022_fca_ss2/` — Fly Cell Atlas, Li et
  al. 2022 (PMID 35239393), from ArrayExpress
  ([E-MTAB-10519](https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-10519) 10x,
  [E-MTAB-10628](https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-10628)
  Smart-seq2) and the authors' per-tissue h5ad analyses: 17 analyses each, one entry
  per author annotation (370 and 237; 335 and 211 with an FBbt term are loaded).
  FBbt mappings are made once per author type and shared. Replaces the old SCEA-based
  loads (FBlc0003846 / 4307 / 4785).

## Layout

```
src/vfb_scrnaseq/
  schema/VFB_scRNAseq_schema.yaml   # MASTER LinkML schema
  schemas/                          # JSON Schemas: FBbt mapping, term request, samples, provenance
  templates/                        # generic reports/ README
  ids.py        # VFBseq id minting (registry-backed, idempotent)
  build.py      # curated annotations + samples -> entity records (+ mints Cluster ids)
  emit.py       # entities -> validate + flat RDF (linkml-convert) + OWL (linkml-owl)
  stats.py      # FlyBase-style expression extent/level per cluster x gene
  project_config.py / ingest.py / pub.py   # config knobs, GEO SOFT ingest, :pub lookup
  ingest_arrayexpress.py / ingest_h5ad.py  # ArrayExpress IDF/SDRF; AnnData obs/var/matrix (h5py)
scripts/                                 # dataset-agnostic pipeline + CI check scripts
tests/                                   # pytest suite (run in CI)
docs/DESIGN.md                           # design decisions, curation rules, per-project notes
.claude/agents/map-clusters-to-fbbt.md   # FBbt mapper (curation rules built in)
.claude/agents/write-cell-type-report.md # per-type background reports
.claude/agents/fbbt-term-request.md      # draft FBbt term request (curator sign-off only)
.claude/hooks/                           # validate mapping/report/sample/provenance files on write
.claude/skills/                          # local-paper-index, anndata-zarr-summary
checks/                                  # FBbt / FlyBase release-check records + pending term requests
projects/kurmangaliyev_2020/             # first worked example (visual system development)
projects/davie_2018/                     # adult brain, ageing
projects/li_2022_fca_10x/, li_2022_fca_ss2/  # Fly Cell Atlas (ArrayExpress + h5ad)
metadata/                                # VFB-loadable metadata OWL, one per project
expression/                              # VFB-loadable expression OWL (.owl.gz), one per project
id_registry/                             # minted-id registry (JSON)
```

## Develop & run

The environment is managed with **uv** (`pyproject.toml` + `uv.lock`); run
everything via `uv run` so the locked deps (linkml, linkml-owl, …) are used.

```sh
uv sync                      # create/update the .venv from uv.lock
uv run pytest                # tests

# full pipeline for a project (GEO -> working JSON -> RDF + OWL):
uv run python scripts/build_annotations_from_geo.py --project kurmangaliyev_2020
uv run python scripts/build_samples_from_geo.py     --project kurmangaliyev_2020
uv run python scripts/assign_placeholders.py        --project kurmangaliyev_2020
uv run python scripts/collate_mapping.py            --project kurmangaliyev_2020
uv run python scripts/verify_mappings.py            --project kurmangaliyev_2020   # FBbt terms current (OLS)
uv run python scripts/build_rdf.py                  --project kurmangaliyev_2020   # -> .ttl + .ofn + metadata/*.owl (mints Cluster ids)
uv run python scripts/update_gene_ids.py            --project kurmangaliyev_2020   # needs psql (FlyBase Chado)
uv run python scripts/build_expression.py           --project kurmangaliyev_2020   # -> expression/*.owl.gz
uv run python scripts/build_rdf.py                  --project kurmangaliyev_2020   # again: adds the gene counts

# ArrayExpress + h5ad projects (e.g. the Fly Cell Atlas) start differently:
uv run python scripts/build_samples_from_arrayexpress.py --project li_2022_fca_10x
uv run python scripts/fetch_h5ad.py                      --project li_2022_fca_10x   # -> .cache/h5ad/
uv run python scripts/build_annotations_from_h5ad.py     --project li_2022_fca_10x
uv run python scripts/expand_type_mappings.py            --project li_2022_fca_10x   # type_mapping/ -> mapping/
# (bespoke layouts use a project script, e.g. projects/davie_2018/build_clusters.py)

# the CI checks
uv run python scripts/validate_project_files.py
uv run python scripts/check_mapping_tsv.py

# the weekly release checks (also run by .github/workflows/fbbt-release-check.yml)
uv run python scripts/check_fbbt_release.py [--force]
uv run python scripts/check_flybase_release.py [--dry-run]   # opens an issue on change
```

Cell-type FBbt mapping itself runs as Claude Code subagents (`map-clusters-to-fbbt`)
against the OLS MCP — see `docs/DESIGN.md`.

## Curation rules (summary)

One row per author cluster (never merged by type); typing from the authors, not
re-analysis; *composed primarily of*; no FBbt term → held (listed in `mapping.tsv`
with a reason, not loaded); no routine new-term
requests from expression alone; stage on Samples, on Clusters only when determined
from the cluster's expression. Details: [`docs/DESIGN.md`](docs/DESIGN.md#general-curation-rules).

## Status

All four projects are curated and built: every mapped cluster has been reviewed (bar
three Kurmangaliyev early clusters awaiting FBbt #2216, below), and
each project has validated metadata OWL (`metadata/`), summary expression OWL
(`expression/`, CPM for every dataset) and a `provenance.json`. Gene ids in the
expression output are mapped to current FlyBase genes (`scripts/update_gene_ids.py`;
see *Expression statistics* in `docs/DESIGN.md`). A weekly workflow
(`fbbt-release-check.yml`) re-checks the FBbt terms on each new FBbt release, opens
an issue when a FlyBase release changes a gene id in use, and reminds when a pending
FBbt term request is closed (`checks/`).

Outstanding, outside this repo: loading the OWL into VFB, and retiring the old loads
these replace (FBlc0006090, FBlc0003846 / 4307 / 4785). One FBbt request is pending
([#2216](https://github.com/FlyBase/drosophila-anatomy-developmental-ontology/issues/2216),
immature T2 / T2a / T3 neurons; see `checks/pending_fbbt_requests.json`).
