#!/usr/bin/env python
"""Claude Code hook: validate provenance.json against its JSON Schema.

Invoked as a PostToolUse hook when a Write tool targets a file named
``provenance.json``. Validates against
``src/vfb_scrnaseq/schemas/provenance.schema.json``.

Exit codes:
    0 — valid, or file is not a provenance.json
    2 — validation failed (Claude sees stderr and self-corrects)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCHEMA_PATH = Path("src/vfb_scrnaseq/schemas/provenance.schema.json")

REQUIRED_TOP = {"project", "generated_at", "summary", "pipeline", "ontologies", "data_sources", "software"}


def main() -> int:
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return 0

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path or not file_path.endswith("provenance.json"):
        return 0

    content = tool_input.get("content", "")
    if not content:
        print("provenance.json is empty", file=sys.stderr)
        return 2

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        print(f"provenance.json is not valid JSON: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []
    if SCHEMA_PATH.exists():
        try:
            import jsonschema

            schema = json.loads(SCHEMA_PATH.read_text())
            validator = jsonschema.Draft7Validator(schema)
            for e in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
                path = ".".join(str(p) for p in e.absolute_path) or "(root)"
                errors.append(f"{path}: {e.message}")
        except ImportError:
            errors = _validate_inline(data)
    else:
        errors = _validate_inline(data)

    if not errors:
        return 0

    print("PROVENANCE VALIDATION FAILED", file=sys.stderr)
    print("Fix these issues and rewrite provenance.json:", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    return 2


def _validate_inline(data: dict) -> list[str]:
    """Fallback validation without the jsonschema library."""
    errors = []
    missing = REQUIRED_TOP - set(data)
    if missing:
        errors.append(f"missing required top-level fields: {sorted(missing)}")
    for key in ("ontologies", "data_sources", "software"):
        if key in data and not isinstance(data[key], list):
            errors.append(f"'{key}' must be a list")
    if "pipeline" in data:
        p = data["pipeline"]
        if not isinstance(p, dict) or not {"id", "url", "commit"} <= set(p):
            errors.append("'pipeline' must be an object with 'id', 'url' and 'commit'")
    return errors


if __name__ == "__main__":
    sys.exit(main())
