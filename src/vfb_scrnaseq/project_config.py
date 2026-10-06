"""Load per-project config and expose the project-specific knobs the generic
pipeline scripts need, so the scripts in ``scripts/`` stay dataset-agnostic.

All Kurmangaliyev/optic-lobe specifics live in ``projects/<name>/config.yaml``
(column mapping, the unidentified-cluster rule, class->FBbt broad anchors,
held classes). For logic that config can't express, a project may ship an
**escape hatch** module ``projects/<name>/project.py`` defining any of:

    def is_unidentified(label: str, cls: str, config: dict) -> bool: ...
    def broad_anchor(cls: str, config: dict) -> dict | None: ...   # {fbbt_id,label,definition}

When present, these override the config-driven defaults below.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Any, Callable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def project_dir(project: str) -> Path:
    return REPO_ROOT / "projects" / project


def load_config(project: str) -> dict[str, Any]:
    cfg = yaml.safe_load((project_dir(project) / "config.yaml").read_text())
    cfg.setdefault("_project", project)
    return cfg


def _load_overrides(project: str) -> Any | None:
    """Import projects/<name>/project.py if it exists (the escape hatch)."""
    path = project_dir(project) / "project.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"project_{project}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def unidentified_classifier(project: str, config: dict) -> Callable[[str, str], bool]:
    """Return ``is_unidentified(label, cls) -> bool`` from config (or project.py)."""
    overrides = _load_overrides(project)
    if overrides and hasattr(overrides, "is_unidentified"):
        return lambda label, cls: overrides.is_unidentified(label, cls, config)

    rule = (config.get("unidentified") or {}).get("rule", "none")
    if rule == "none":
        return lambda label, cls: False
    if rule == "class_prefixed_numbered":
        # label is exactly its own class code + digits (e.g. N1, G37, C16);
        # excludes named types that merely start with a class letter (e.g. C2/C3).
        return lambda label, cls: bool(cls) and re.fullmatch(rf"{re.escape(cls)}\d+", label) is not None
    if rule.startswith("regex:"):
        pat = re.compile(rule[len("regex:"):])
        return lambda label, cls: pat.fullmatch(label) is not None
    raise ValueError(f"unknown unidentified.rule: {rule!r}")


def hold_classes(config: dict) -> set[str]:
    return set((config.get("unidentified") or {}).get("hold_classes", []))


def held_classifier(project: str, config: dict) -> Callable[[str, str], bool]:
    """Return ``is_held(label, cls) -> bool``: held clusters are left unmapped.

    A cluster is held if its class is in ``unidentified.hold_classes``, or — when
    ``unidentified.hold_unidentified`` is true — if it is an unidentified cluster at
    all (for atlases with no author class to derive a broad anchor from).
    """
    unid = config.get("unidentified") or {}
    held = hold_classes(config)
    is_unidentified = unidentified_classifier(project, config)
    hold_all = bool(unid.get("hold_unidentified", False))
    return lambda label, cls: cls in held or (hold_all and is_unidentified(label, cls))


def annotation_kind(project: str, config: dict) -> Callable[[dict], str]:
    """Return ``kind(annotation) -> 'named' | 'placeholder' | 'held'``.

    An annotation entry may itself say it is ``unannotated`` (the authors left the
    cluster without a type); with ``unidentified.hold_unidentified`` it is held.
    Otherwise the label/class rules (``held_classifier`` / ``unidentified_classifier``).
    """
    is_held = held_classifier(project, config)
    is_unidentified = unidentified_classifier(project, config)
    hold_all = bool((config.get("unidentified") or {}).get("hold_unidentified", False))

    def kind(ann: dict) -> str:
        label, cls = ann["label"], ann.get("class", "")
        if ann.get("unannotated"):
            return "held" if hold_all else "placeholder"
        if is_held(label, cls):
            return "held"
        if is_unidentified(label, cls):
            return "placeholder"
        return "named"
    return kind


# Characters allowed verbatim in per-cluster file names; others are substituted.
# '*' is the prime convention in some atlases (e.g. Davie 2018 "A/B*-KC" = α'/β').
_SLUG_SUBS = {"/": "_", "*": "p", "&": "+", " ": "_"}


def label_slug(label: str) -> str:
    """File-name-safe stem for a cluster label (mapping/<slug>.fbbt_mapping.json,
    reports/<slug>.md). Identity for labels already made of [A-Za-z0-9._+-]."""
    s = "".join(_SLUG_SUBS.get(ch, ch) for ch in label)
    return re.sub(r"[^A-Za-z0-9._+-]", "_", s)


def broad_anchor(project: str, config: dict, cls: str) -> dict | None:
    """Return the broad FBbt anchor {fbbt_id,label,definition} for a cell class."""
    overrides = _load_overrides(project)
    if overrides and hasattr(overrides, "broad_anchor"):
        return overrides.broad_anchor(cls, config)
    anchors = (config.get("unidentified") or {}).get("class_anchors", {})
    return anchors.get(cls)
