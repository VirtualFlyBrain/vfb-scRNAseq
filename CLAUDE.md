# vfb-scRNAseq

RDF/OWL metadata (+ summary expression) for *Drosophila* scRNAseq datasets, with
clusters mapped to FBbt, for loading into Virtual Fly Brain. Read `README.md`, then
`docs/DESIGN.md` — especially **General curation rules** and **Adding a new dataset**.

## Curation rules (summary; details in docs/DESIGN.md)

- One row per **author cluster**; never merge clusters by cell type.
- Type clusters from what the **authors** say (GEO metadata / paper / supp tables);
  do not overturn or hedge their typing from our own reading of the data.
- Cluster → FBbt is *composed primarily of* (RO:0002473).
- No adequate FBbt term → the cluster is **held** (no generic fallback): listed in
  `mapping.tsv` with a `hold_reason`, but **not loaded** (no id, entity or expression).
- New FBbt terms from gene expression alone are the exception. **Never open an FBbt
  term-request issue without explicit curator sign-off**; when one is opened, add it
  to `checks/pending_fbbt_requests.json`.
- Stage goes on Samples; on a Cluster only if determined from its own expression.

## Conventions

- Environment: `uv` (`uv sync`, `uv run ...`). Run the CI checks locally before
  committing: `uv run pytest`, `uv run python scripts/validate_project_files.py`,
  `uv run python scripts/check_mapping_tsv.py`.
- Project-specific knowledge lives in `projects/<name>/config.yaml` (or a project
  script); `scripts/` and `src/` stay dataset-agnostic.
- Mapping JSON is written with the Write tool so `.claude/hooks/check_fbbt_mapping.py`
  validates it. Agents never set `manual_edit`; it records a curator's hand edit.
- After changing mappings, re-run `scripts/collate_mapping.py` (CI fails on a stale
  `mapping.tsv`).
- VFBseq ids come from `id_registry/registry.json` (idempotent on natural keys).
  GEO/SRA accessions are xrefs, never IRIs.
- Large inputs (GEO matrices/metadata) go in `.cache/` (gitignored); paper full text
  and supplementary tables stay out of git.
- The paper index runs from a sibling Atlas-reporter clone pinned to `2acd38e`
  (`local-paper-index` skill).
- Pub lookup env overrides are `VFBSEQ_KB_*` / `VFBSEQ_PDB_URL` (not `VFB_KB_*`,
  which may hold writable-KB credentials).
- Commit in stages on a branch and open a PR; CI must pass.
