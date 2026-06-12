# vfb-scRNAseq

Produce RDF metadata for *Drosophila* single-cell RNA-seq data: dataset / sample
/ cluster annotations, linking clusters to **FBbt** anatomy terms, plus (later
phase) summary expression statistics computed the FlyBase way.

This repo is built on the [atlas-chat](https://github.com/Cellular-Semantics/atlas-chat)
template and will become the **new master copy** of the VFB scRNAseq LinkML
schema, deprecating
[`VirtualFlyBrain/vfb-scRNAseq-ontology`](https://github.com/VirtualFlyBrain/vfb-scRNAseq-ontology).

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
  -> RDF/TTL                   (vfb_scrnaseq.emit -> linkml-convert)
```

## Identifiers

Every published entity gets an opaque, registry-backed **`VFBseq_########`** IRI
(`src/vfb_scrnaseq/ids.py`, registry in `id_registry/`). GEO/SRA accessions
(GSE/GSM/PRJNA/SRP/GPL) are **cross-references**, carried in the schema's
`site` / `accession` slots — never used as the IRI. (Identifiers previously came
from FlyBase; that authority is being dropped.)

## Worked example

`projects/kurmangaliyev_2020/` — Kurmangaliyev et al. 2020, *Drosophila* visual
system developmental atlas ([GSE156455](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE156455),
PMID 33125872). Cluster labels are curated from the paper / supplementary tables.

## Layout

```
src/vfb_scrnaseq/
  schema/VFB_scRNAseq_schema.yaml   # MASTER LinkML schema
  schemas/fbbt_mapping.schema.json  # FBbt mapping agent output contract
  ids.py        # VFBseq id minting (registry-backed, idempotent)
  mapping.py    # collect FBbt candidates -> reviewable mapping.tsv
  build.py      # curated annotations -> LinkML objects   (stub)
  emit.py       # LinkML -> RDF/TTL                        (stub)
.claude/agents/map-clusters-to-fbbt.md   # FBbt mapper (adapted ontology-term-lookup)
projects/kurmangaliyev_2020/             # first worked example
id_registry/                             # minted-id registry (JSON)
```

## Status

Scaffold. `ids.py` is implemented and tested; `build.py` / `emit.py` are stubs
pending Pydantic-model generation from the schema and curated inputs.

## Develop

```sh
pip install -e ".[dev]"
pytest
# generate Pydantic models from the master schema:
gen-pydantic src/vfb_scrnaseq/schema/VFB_scRNAseq_schema.yaml > src/vfb_scrnaseq/model.py
```
