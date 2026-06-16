#!/usr/bin/env python
"""Claude Code hook: flag suspicious characters in generated cell-type reports.

Cell-type reports under ``.../reports/*.md`` are produced by in-session LLM
synthesis, which occasionally emits a stray homoglyph / wrong-script character
(e.g. an Ethiopic or Cyrillic letter inside an English word) or an invisible
control/format character. These are cosmetic-to-subtle bugs that can corrupt a
gene/marker name. This hook rejects such writes so the report is rewritten clean.

Policy:
- LETTERS must be Latin or Greek (Greek is common in fly nomenclature, e.g.
  DIP-beta written with a Greek letter). Any other-script letter is flagged.
- Invisible format chars (zero-width space/joiners) and control chars (except
  tab/newline/CR) are flagged.
- Symbols and punctuation are allowed (en/em dash, →, ×, ≥, ≤, µ, °, curly quotes,
  ellipsis, etc.) — these are legitimate in scientific text.

Exit codes:
    0 — clean, or the file is not a report markdown
    2 — suspicious characters found (Claude sees stderr and rewrites)
"""

from __future__ import annotations

import json
import sys
import unicodedata

ALLOWED_CONTROL = {"\t", "\n", "\r"}

# Letter-category Unicode symbols that are legitimate in scientific text.
# (Unicode classifies these as letters, but they are units/symbols, not script.)
ALLOWED_LETTERLIKE = {
    "µ",  # MICRO SIGN (µ)
    "Å",  # ANGSTROM SIGN (Å)
    "Ω",  # OHM SIGN (Ω)
    "K",  # KELVIN SIGN (K)
}


def _is_suspicious(ch: str) -> str | None:
    """Return a reason string if the character is suspicious, else None."""
    cat = unicodedata.category(ch)

    # Control characters (Cc) other than tab/newline/CR.
    if cat == "Cc" and ch not in ALLOWED_CONTROL:
        return "control character"

    # Format characters (Cf): zero-width space/joiner, bidi marks, etc.
    if cat == "Cf":
        return "invisible format character"

    # Letters must be Latin or Greek (plus a few letterlike technical symbols).
    if cat.startswith("L"):
        if ch in ALLOWED_LETTERLIKE:
            return None
        try:
            name = unicodedata.name(ch)
        except ValueError:
            return "unnamed letter"
        first = name.split(" ", 1)[0]
        if first not in ("LATIN", "GREEK"):
            return f"non-Latin/Greek letter ({name})"

    return None


def scan(content: str) -> list[str]:
    findings: list[str] = []
    for lineno, line in enumerate(content.splitlines(), 1):
        for col, ch in enumerate(line, 1):
            reason = _is_suspicious(ch)
            if reason:
                ctx = line.strip()[:70]
                findings.append(
                    f"line {lineno} col {col}: U+{ord(ch):04X} {reason} -> {ctx!r}"
                )
    return findings


def _is_report_md(file_path: str) -> bool:
    return "/reports/" in file_path and file_path.endswith(".md")


def main() -> int:
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return 0

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not _is_report_md(file_path):
        return 0

    content = tool_input.get("content", "")
    findings = scan(content)
    if not findings:
        return 0

    print("REPORT TEXT CHECK FAILED — stray/suspicious characters:", file=sys.stderr)
    for f in findings:
        print(f"  - {f}", file=sys.stderr)
    print(
        "Rewrite the report with plain Latin/Greek text "
        "(these are usually homoglyph slips inside a word).",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
