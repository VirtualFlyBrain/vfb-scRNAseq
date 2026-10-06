# Davie 2018 cell-type reports

One report per author cell type (`<type>.md`, named after the GEO label; `/`, `*`,
`&` in labels become `_`, `p`, `+`). They were written by Claude Code subagents from
the paper's full text, Table S2 (annotation method and references) and Table S3
(markers), as background evidence for the FBbt mapping.

**These reports are not the mapping decisions.** Their "Mapping notes" (and some of
the Summary/Markers text) record the agents' own reading at the time, including
doubts about marker lists, cell counts, possible contamination or merged types. Many
of those suggestions were deliberately not followed: curation takes the authors'
typing at face value (see "General curation rules" in `docs/DESIGN.md`), and several
mappings were later re-done or hand-edited by the curator.

**The authoritative mapping is `../mapping.tsv`** (one row per author cluster),
backed by the per-cluster JSON in `../mapping/` and the per-type JSON in
`../type_mapping/`. Hand edits are recorded in each mapping's `manual_edit` block and
shown in the `manual_edit` column of `mapping.tsv`.

Reports exist for the authors' named types only; the four sub-clustered res-2.0
parent clusters (20, 27, 42, 64) were mapped from Table S2 and their sub-cluster
reports.
