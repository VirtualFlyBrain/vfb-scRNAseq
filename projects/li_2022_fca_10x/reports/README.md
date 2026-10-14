# Fly Cell Atlas cell-type reports

One report per author cell type (`<type>.md`, named after the authors' label; `/`,
`*`, `&` in labels become `_`, `p`, `+`). They were written by Claude Code subagents
from the paper's full text and the supplementary materials (methods and figure legends;
no per-type marker tables were available), as background evidence for the FBbt mapping.

**These reports are not the mapping decisions.** Their "Mapping notes" (and some of
the Summary/Markers text) record the agents' own reading at the time, which may
include doubts about markers, cell counts, possible contamination or merged types.
Curation takes the authors' typing at face value (see "General curation rules" in
`docs/DESIGN.md`), so such suggestions are not necessarily followed, and mappings may
since have been re-done or hand-edited by a curator.

**The authoritative mapping is `../mapping.tsv`** (one row per author cluster),
backed by the per-cluster JSON in `../mapping/` and the per-type JSON in
`../type_mapping/` (shared with `li_2022_fca_ss2`). Hand edits are recorded in each
mapping's `manual_edit` block and shown in the `manual_edit` column of `mapping.tsv`.

Reports exist only for the 117 types that needed judgement (no author FBbt id, several
ids, a tissue/organ or obsolete author term, or a stage-qualified label). The other 135
types carry a single current FBbt cell term from the authors and were confirmed by
`../confirm_author_terms.py` (the author term, or its 'adult X' variant) from
`../type_evidence.json`, without a report.
