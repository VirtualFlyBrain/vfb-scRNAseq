#!/usr/bin/env python
"""Validate every committed project working file, as the Claude Code hooks do.

The `.claude/hooks/check_*.py` scripts validate files when an agent writes them, but
hand edits (or edits in a GitHub PR) bypass them. This runs the same hooks over the
committed files so CI enforces the same rules:

  projects/*/mapping/*.fbbt_mapping.json        -> check_fbbt_mapping.py
  projects/*/type_mapping/*.fbbt_mapping.json   -> check_fbbt_mapping.py
  projects/*/reports/*.md                       -> check_report_text.py
  projects/*/**/*fbbt_term_request*.json         -> check_fbbt_term_request.py
  projects/*/provenance.json                    -> check_provenance.py
  projects/*/samples.json                       -> check_samples.py

Usage:
    uv run python scripts/validate_project_files.py      # exit 1 on any failure
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS = REPO_ROOT / ".claude" / "hooks"

CHECKS = [
    ("projects/*/mapping/*.fbbt_mapping.json", "check_fbbt_mapping.py"),
    ("projects/*/type_mapping/*.fbbt_mapping.json", "check_fbbt_mapping.py"),
    ("projects/*/**/*fbbt_term_request*.json", "check_fbbt_term_request.py"),
    ("projects/*/provenance.json", "check_provenance.py"),
    ("projects/*/samples.json", "check_samples.py"),
    ("projects/*/reports/*.md", "check_report_text.py"),
]


def run_hook(hook: str, path: Path) -> tuple[bool, str]:
    """Feed a file to a hook exactly as Claude Code does (PostToolUse Write payload)."""
    rel = path.relative_to(REPO_ROOT)
    payload = json.dumps({"tool_input": {"file_path": str(rel), "content": path.read_text()}})
    r = subprocess.run([sys.executable, str(HOOKS / hook)], input=payload,
                       capture_output=True, text=True, cwd=REPO_ROOT)
    return r.returncode == 0, (r.stderr or r.stdout).strip()


def main() -> int:
    n, failures = 0, []
    for pattern, hook in CHECKS:
        for path in sorted(set(REPO_ROOT.glob(pattern))):
            n += 1
            ok, msg = run_hook(hook, path)
            if not ok:
                failures.append((path.relative_to(REPO_ROOT), msg))
    if failures:
        print(f"{len(failures)} of {n} project files failed validation:")
        for rel, msg in failures:
            print(f"\n  {rel}\n    " + msg.replace("\n", "\n    "))
        return 1
    print(f"OK — {n} project files valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
