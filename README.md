# vfb-scRNAseq

Produce RDF metadata for *Drosophila* single-cell RNA-seq data: dataset / sample
/ cluster annotations, linking clusters to **FBbt** anatomy terms, plus (later
phase) summary expression statistics computed the FlyBase way.

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
  copy** (currently a verbatim import from the old repo; will be extended here).

## Pipeline (cell-type-annotation focus)

```
project config (+ project script for bespoke clusterings)
  -> author clusters + samples    (build_annotations_from_geo.py, build_samples_from_geo.py)
  -> per-type reports             (write-cell-type-report agent)
  -> FBbt mapping + human review  (map-clusters-to-fbbt agent; collate_mapping.py -> mapping.tsv)
  -> metadata RDF/OWL             (build_rdf.py)
  -> expression stats + OWL       (build_expression.py)
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
  dataset (110 clusters).
- `projects/davie_2018/` — Davie et al. 2018, ageing adult brain atlas
  ([GSE107451](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE107451),
  PMID 29909982), 57K 10x set. Replaces the old FlyBase/SCEA load (FBlc0006090).

## Layout

```
src/vfb_scrnaseq/
  schema/VFB_scRNAseq_schema.yaml   # MASTER LinkML schema
  schemas/fbbt_mapping.schema.json  # FBbt mapping agent output contract
  ids.py        # VFBseq id minting (registry-backed, idempotent)
  build.py      # curated annotations + samples -> entity records (+ mints Cluster ids)
  emit.py       # entities -> validate + flat RDF (linkml-convert) + OWL (linkml-owl)
  stats.py      # FlyBase-style expression extent/level per cluster x gene
  project_config.py / ingest.py / pub.py   # config knobs, GEO SOFT ingest, :pub lookup
scripts/                                 # dataset-agnostic pipeline + CI check scripts
.claude/agents/map-clusters-to-fbbt.md   # FBbt mapper (curation rules built in)
.claude/agents/write-cell-type-report.md # per-type background reports
checks/                                  # weekly FBbt check record + pending term requests
projects/kurmangaliyev_2020/             # first worked example
projects/davie_2018/                     # second project (adult brain, ageing)
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
uv run python scripts/build_rdf.py                  --project kurmangaliyev_2020   # -> .ttl + .ofn + metadata/*.owl
uv run python scripts/update_gene_ids.py            --project kurmangaliyev_2020   # needs psql (FlyBase Chado)
uv run python scripts/build_expression.py           --project kurmangaliyev_2020   # -> expression/*.owl.gz

# the CI checks
uv run python scripts/validate_project_files.py
uv run python scripts/check_mapping_tsv.py
```

Cell-type FBbt mapping itself runs as Claude Code subagents (`map-clusters-to-fbbt`)
against the OLS MCP — see `docs/DESIGN.md`.

## Curation rules (summary)

One row per author cluster (never merged by type); typing from the authors, not
re-analysis; *composed primarily of*; no FBbt term → held; no routine new-term
requests from expression alone; stage on Samples, on Clusters only when determined
from the cluster's expression. Details: [`docs/DESIGN.md`](docs/DESIGN.md#general-curation-rules).

## Status

`ids.py`, `ingest.py`, `build.py`, `emit.py`, and the `scripts/` pipeline are
implemented; the worked example emits validated RDF (`linkml-convert`) and OWL
(`linkml-owl`), and expression statistics are computed for both projects.

Gene ids in the expression output are mapped to current FlyBase genes
(`scripts/update_gene_ids.py`; see *Expression statistics* in `docs/DESIGN.md`).
