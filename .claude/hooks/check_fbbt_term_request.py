#!/usr/bin/env python
"""Claude Code hook: validate fbbt_term_request.json against JSON Schema.

Invoked as a PostToolUse hook when a Write tool targets a file named
``fbbt_term_request.json`` (output of the ``fbbt-term-request`` agent).

The FBbt intake (FlyBase drosophila-anatomy-developmental-ontology issue
template) requires only References + Term label(s); curators author the
authoritative definition/axioms. Everything under ``suggested_details`` is
optional, non-authoritative help.

Exit codes:
    0 — valid, or file is not an fbbt_term_request.json
    2 — validation failed (Claude sees stderr and self-corrects)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCHEMA_PATH = Path("src/vfb_scrnaseq/schemas/fbbt_term_request.schema.json")

FBBT_ID_RE = re.compile(r"^FBbt:[0-9]{8}$")


def main() -> int:
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return 0

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path or not file_path.endswith("fbbt_term_request.json"):
        return 0

    content = tool_input.get("content", "")
    if not content:
        print("fbbt_term_request.json is empty", file=sys.stderr)
        return 2

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        print(f"fbbt_term_request.json is not valid JSON: {exc}", file=sys.stderr)
        return 2

    if SCHEMA_PATH.exists():
        try:
            import jsonschema

            schema = json.loads(SCHEMA_PATH.read_text())
            errors = []
            validator = jsonschema.Draft202012Validator(schema)
            for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
                path = ".".join(str(p) for p in error.absolute_path) or "(root)"
                errors.append(f"{path}: {error.message}")
        except ImportError:
            errors = _validate_inline(data)
    else:
        errors = _validate_inline(data)

    errors.extend(_semantic_checks(data))

    if not errors:
        return 0

    print("FBBT TERM REQUEST VALIDATION FAILED", file=sys.stderr)
    print("Fix these issues and rewrite fbbt_term_request.json:", file=sys.stderr)
    for error in errors:
        print(f"  - {error}", file=sys.stderr)
    return 2


def _semantic_checks(data: dict) -> list[str]:
    """Cross-field checks beyond the JSON Schema."""
    errors = []

    # The issue body must carry the two required FBbt template sections.
    ntr = data.get("ntr_markdown", "")
    if ntr:
        for section in ["Reference(s)", "Term label(s)"]:
            if section not in ntr:
                errors.append(f"ntr_markdown missing required FBbt section: '{section}'")

    return errors


def _validate_inline(data: dict) -> list[str]:
    """Fallback validation without the jsonschema library."""
    errors = []

    if not isinstance(data.get("cluster_label"), str) or not data.get("cluster_label", "").strip():
        errors.append("Missing or empty required field: 'cluster_label'")
    if not isinstance(data.get("ntr_markdown"), str) or not data.get("ntr_markdown", "").strip():
        errors.append("Missing or empty required field: 'ntr_markdown'")

    refs = data.get("references")
    if not isinstance(refs, list) or len(refs) == 0:
        errors.append("'references' must be a non-empty list (FBrf / DOI / PMID)")
    elif not all(isinstance(r, str) for r in refs):
        errors.append("'references' must contain only strings")

    labels = data.get("term_labels")
    if not isinstance(labels, list) or len(labels) == 0:
        errors.append("'term_labels' must be a non-empty list")
    elif not all(isinstance(s, str) for s in labels):
        errors.append("'term_labels' must contain only strings")

    sd = data.get("suggested_details")
    if sd is not None:
        if not isinstance(sd, dict):
            errors.append("'suggested_details' must be an object or null")
        else:
            allowed_sd = {"draft_definition", "parent_term", "location", "markers", "synonyms"}
            extra_sd = set(sd.keys()) - allowed_sd
            if extra_sd:
                errors.append(f"suggested_details has extra fields: {extra_sd}")
            for key in ("parent_term", "location"):
                obj = sd.get(key)
                if obj is not None:
                    if not isinstance(obj, dict):
                        errors.append(f"suggested_details.{key} must be an object")
                    elif not FBBT_ID_RE.match(obj.get("fbbt_id", "")):
                        errors.append(f"suggested_details.{key}.fbbt_id must match FBbt:NNNNNNNN")
            syns = sd.get("synonyms")
            if syns is not None and isinstance(syns, list):
                for i, syn in enumerate(syns):
                    if not isinstance(syn, dict) or syn.get("scope") not in {"exact", "related", "broad", "narrow"}:
                        errors.append(f"suggested_details.synonyms[{i}].scope must be exact/related/broad/narrow")

    allowed_top = {"cluster_label", "references", "term_labels", "suggested_details", "ntr_markdown"}
    extra = set(data.keys()) - allowed_top
    if extra:
        errors.append(f"Extra top-level fields not allowed: {extra}")

    return errors


if __name__ == "__main__":
    sys.exit(main())
