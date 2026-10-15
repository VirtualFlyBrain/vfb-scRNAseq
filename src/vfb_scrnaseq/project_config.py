"""Load per-project config and expose the project-specific knobs the generic
pipeline scripts need, so the scripts in ``scripts/`` stay dataset-agnostic.

All project-specific knowledge lives in ``projects/<name>/config.yaml`` (column
mapping, the unidentified-cluster rule, class->FBbt broad anchors, held classes,
``hold_unidentified`` and ``hold_reasons``; the builders also read e.g.
``annotation_build``, ``type_mapping`` and ``expression``). For logic that config can't express, a project may ship an
**escape hatch** module ``projects/<name>/project.py`` defining any of:

    def is_unidentified(label: str, cls: str, config: dict) -> bool: ...
    def broad_anchor(cls: str, config: dict) -> dict | None: ...   # {fbbt_id,label,definition}

When present, these override the config-driven defaults below.
"""

from __future__ import annotations

import importlib.util
import json
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
        # label rules apply to the authors' own cluster id (labels may be prefixed
        # to keep them unique across clusterings, e.g. early_N1)
        label, cls = ann.get("source_cluster_id", ann["label"]), ann.get("class", "")
        if ann.get("unannotated"):
            return "held" if hold_all else "placeholder"
        if is_held(label, cls):
            return "held"
        if is_unidentified(label, cls):
            return "placeholder"
        return "named"
    return kind


def hold_reason(project: str, config: dict) -> Callable[[dict, dict], str]:
    """Return ``reason(annotation, mapping) -> str`` for a cluster with no FBbt term
    ("" for a mapped one). Held clusters are recorded in mapping.tsv but not loaded.

    - an ``unannotated`` entry: ``unidentified.hold_reasons[<its type>]`` if given
      (e.g. FCA "artefact" -> artefact, "unannotated" -> leftover), else ``untyped``
      (the authors left the cluster without a type);
    - a cluster of a class in ``unidentified.hold_classes``: ``undefined class``;
    - any other cluster without an FBbt term: ``no term``.
    """
    reasons = (config.get("unidentified") or {}).get("hold_reasons") or {}
    classes = hold_classes(config)

    def reason(ann: dict, mapping: dict) -> str:
        if ((mapping or {}).get("best_match") or {}).get("fbbt_id"):
            return ""
        if ann.get("unannotated"):
            return reasons.get(ann.get("type", ""), "untyped")
        if ann.get("class", "") in classes:
            return "undefined class"
        return "no term"
    return reason


def fbbt_mapping(proj: Path, label: str) -> dict | None:
    """A cluster's mapping/<slug>.fbbt_mapping.json, or None."""
    f = proj / "mapping" / f"{label_slug(label)}.fbbt_mapping.json"
    return json.loads(f.read_text()) if f.exists() else None


def mapped_labels(proj: Path) -> set[str]:
    """Labels of the clusters that are loaded: those with an FBbt term. Clusters
    without one (held) stay in mapping.tsv for curation but get no id, entity or
    expression."""
    anns = json.loads((proj / "cell_type_annotations.json").read_text())["annotations"]
    return {a["label"] for a in anns
            if ((fbbt_mapping(proj, a["label"]) or {}).get("best_match") or {}).get("fbbt_id")}


# Characters allowed verbatim in per-cluster file names; others are substituted.
# '*' is the prime convention in some atlases (e.g. Davie 2018 "A/B*-KC" = α'/β').
_SLUG_SUBS = {"/": "_", "*": "p", "&": "+", " ": "_"}


def label_slug(label: str) -> str:
    """File-name-safe stem for a cluster label (mapping/<slug>.fbbt_mapping.json,
    reports/<slug>.md). Identity for labels already made of [A-Za-z0-9._+-]."""
    s = "".join(_SLUG_SUBS.get(ch, ch) for ch in label)
    return re.sub(r"[^A-Za-z0-9._+-]", "_", s)


def broad_anchor(project: str, config: dict, cls: str, clustering: str | None = None) -> dict | None:
    """Return the broad FBbt anchor {fbbt_id,label,definition} for a cell class.

    `unidentified.clustering_class_anchors.<clustering>` overrides `class_anchors`
    for clusters of that clustering (e.g. an early-stage clustering needs immature /
    stage-neutral anchors rather than adult ones).
    """
    overrides = _load_overrides(project)
    if overrides and hasattr(overrides, "broad_anchor"):
        return overrides.broad_anchor(cls, config)
    unid = config.get("unidentified") or {}
    per = (unid.get("clustering_class_anchors") or {}).get(clustering or "", {})
    return per.get(cls) or unid.get("class_anchors", {}).get(cls)


class SourceNotCurated(SystemExit):
    """A project reuses entities from a study that has not been curated yet."""


def reused_samples(config: dict) -> list[dict]:
    """Samples (and their Assays) this project reuses from other, already-curated
    projects (``reuse`` in config.yaml), as records for samples.json::

        reuse:
          - from_project: li_2022_fca_10x
            note: "5-day head/body samples re-analysed with the new ages"
            samples: [d541ae4e__FCA1_MaleFemale_Head, ...]   # source sample_id values

    Identical entities are referenced by their existing VFBseq ids, never re-minted
    (general curation rule). Stops with a message for the curator if the source study
    has not been curated (no samples.json) or lacks a listed sample: curate it first.
    """
    out = []
    for entry in config.get("reuse") or []:
        src = entry["from_project"]
        sfile = project_dir(src) / "samples.json"
        if not sfile.exists():
            raise SourceNotCurated(
                f"{config.get('_project')}: reuses samples from {src!r}, which has not been "
                f"curated yet (no projects/{src}/samples.json). CURATOR: curate {src} first, "
                f"so the shared Samples/Assays get their ids and metadata there.")
        by_id = {s["sample_id"]: s for s in json.loads(sfile.read_text())["samples"]}
        missing = [sid for sid in entry["samples"] if sid not in by_id]
        if missing:
            raise SourceNotCurated(
                f"{config.get('_project')}: samples not found in {src} (curate them there "
                f"first): {missing}")
        for sid in entry["samples"]:
            s = by_id[sid]
            out.append({"vfbseq_id": s["vfbseq_id"], "sample_id": sid, "from_project": src,
                        "tissue_raw": s.get("tissue_raw"),
                        "assay_vfbseq_ids": s["assay_vfbseq_ids"]})
    return out


def clustering_samples(entry: dict, own: list[dict], reused: list[dict]) -> list[str]:
    """VFBseq ids of the Samples a clustering uses: with ``sample_tissue_raw`` in its
    `sample_build.clusterings` entry, the own and reused samples of that raw tissue;
    otherwise none recorded."""
    tissue = entry.get("sample_tissue_raw") if isinstance(entry, dict) else None
    if not tissue:
        return []
    return [s["vfbseq_id"] for s in own + reused if s.get("tissue_raw") == tissue]
