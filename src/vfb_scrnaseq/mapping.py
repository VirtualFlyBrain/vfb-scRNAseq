"""Cluster-label -> FBbt anatomy mapping helpers.

STUB. The heavy lifting is done by the ``map-clusters-to-fbbt`` Claude agent
(see ``.claude/agents/map-clusters-to-fbbt.md``), which searches FBbt via the
OLS MCP using each cluster's label plus its generated literature report, and
writes per-cluster candidate JSON conforming to
``schemas/fbbt_mapping.schema.json``.

This module collects those per-cluster JSON results into a single reviewable
``mapping.tsv`` (label, FBbt id, FBbt label, match type, confidence, reviewed)
and, after human review, exposes the finalised label -> FBbt id map to
:mod:`vfb_scrnaseq.build`.
"""

from __future__ import annotations

from pathlib import Path

FBBT_MAPPING_SCHEMA = Path(__file__).parent / "schemas" / "fbbt_mapping.schema.json"


def collect_mappings(reports_dir: str | Path) -> list[dict]:
    """Gather per-cluster fbbt_mapping JSON into rows for review. TODO."""
    raise NotImplementedError
