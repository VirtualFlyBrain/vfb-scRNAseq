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
project config + curated cluster labels
  -> literature reports        (atlas-chat report pipeline)
  -> FBbt mapping candidates   (.claude/agents/map-clusters-to-fbbt.md, via OLS MCP)
  -> human review              (projects/<id>/mapping.tsv)
  -> LinkML objects            (vfb_scrnaseq.build)
  -> validate + RDF + OWL      (vfb_scrnaseq.emit -> linkml-validate / -convert / linkml-owl)
```

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
  mapping.py    # collect FBbt candidates -> reviewable mapping.tsv
  build.py      # curated annotations + samples -> entity records (+ mints Cluster ids)
  emit.py       # entities -> validate + flat RDF (linkml-convert) + OWL (linkml-owl)
.claude/agents/map-clusters-to-fbbt.md   # FBbt mapper (adapted ontology-term-lookup)
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
uv run python scripts/collate_mapping.py            --project kurmangaliyev_2020
uv run python scripts/build_rdf.py                  --project kurmangaliyev_2020   # -> .ttl + .ofn
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

**TODO:** map secondary/withdrawn FBgns to current genes in the expression output
(see *Expression statistics* in `docs/DESIGN.md`).
