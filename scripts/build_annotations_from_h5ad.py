#!/usr/bin/env python
"""Build cell_type_annotations.json for a project from the authors' .h5ad files.

The h5ad counterpart of build_annotations_from_geo.py, writing the same
cell_type_annotations.json shape. One h5ad = one author analysis = one Clustering
(`sample_build.clusterings` entries with an `h5ad` URL; files fetched by
scripts/fetch_h5ad.py). Within each, cells are grouped by the author annotation
column and one annotation entry is written per (analysis, annotation): the authors'
unit when the typing is not tied to a single clustering resolution (e.g. FCA, where
a type is "a transcriptomic cluster detected at any clustering resolution").

Config (`annotation_build` in config.yaml):

  annotation_column       obs column with the author cell type (e.g. annotation)
  ontology_column         obs column with the author's ontology id (optional)
  broad_column            obs column with the author's broad class (optional)
  broad_ontology_column   ... and its ontology id (optional)
  sex_column              obs column for per-sex cell counts (optional)
  unannotated_values      annotation values that are not a cell type (e.g.
                          "unannotated", "artefact"): the entry is kept, flagged
                          `unannotated`, and held (in mapping.tsv, not loaded)

  membership              how cells were assigned to the annotation, when not by the
                          authors clustering them: `label_transfer` (a classifier
                          trained on another analysis, e.g. FCA Smart-seq2) or
                          `sorted` (a FACS-sorted population typed as a whole);
                          recorded on each entry and used for Cluster names/titles
  author_ontology_from    another project whose entries supply author_ontology_id /
                          author_broad by (clustering, type) — for transferred labels

A clustering entry may set `fixed_annotation` (+ `membership`): every cell of that
analysis gets that type (for sorted populations the authors did not annotate).

Labels are `<clustering id>_<annotation>`; `source_cluster_id` is the annotation.

Usage:
    uv run python scripts/build_annotations_from_h5ad.py --project li_2022_fca_10x
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from fetch_h5ad import h5ad_path  # noqa: E402
from vfb_scrnaseq.ingest_h5ad import obs_columns, read_obs  # noqa: E402
from vfb_scrnaseq.project_config import load_config  # noqa: E402


def _ontology_ids(v):
    """Author ontology ids: several are sometimes stored as a Python list string
    ("['FBbt:1', 'FBbt:2']") -> "FBbt:1; FBbt:2"."""
    if isinstance(v, str) and v.startswith("[") and v.endswith("]"):
        return "; ".join(x.strip(" '\"") for x in v[1:-1].split(",") if x.strip(" '\""))
    return v


def _dominant(counter: Counter) -> tuple[str | None, bool]:
    """(most common value, ambiguous?)"""
    if not counter:
        return None, False
    (v, _), *rest = counter.most_common()
    return v, bool(rest)


def build_clustering(obs: dict[str, list], ab: dict, clustering: str, clustering_name: str,
                     warnings: list[str]) -> list[dict]:
    ann_col = ab["annotation_column"]
    if ann_col not in obs:
        warnings.append(f"{clustering}: no {ann_col} column")
        return []
    extra = {k: ab.get(k) for k in ("ontology_column", "broad_column", "broad_ontology_column")}
    sex_col = ab.get("sex_column")
    unannotated = set(ab.get("unannotated_values", []))

    cells: Counter[str] = Counter()
    carried: dict[str, dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
    sexes: dict[str, Counter] = defaultdict(Counter)
    for i, a in enumerate(obs[ann_col]):
        if a is None:
            warnings.append(f"{clustering}: cell {obs['_index'][i]} has no {ann_col}")
            continue
        cells[a] += 1
        for key, col in extra.items():
            if col:
                carried[a][key][obs[col][i]] += 1
        if sex_col:
            sexes[a][obs[sex_col][i]] += 1

    out = []
    for a in sorted(cells):
        rec = {
            "label": f"{clustering}_{a}",
            "type": a,
            "clustering": clustering,
            "clustering_name": clustering_name,
            "source_cluster_id": a,
            "cell_number": cells[a],
        }
        for key, field in (("ontology_column", "author_ontology_id"), ("broad_column", "author_broad"),
                           ("broad_ontology_column", "author_broad_ontology_id")):
            if extra[key]:
                v, ambiguous = _dominant(carried[a][key])
                rec[field] = _ontology_ids(v) if "ontology" in field else v
                if ambiguous:
                    warnings.append(f"{clustering}/{a}: {extra[key]} not single-valued "
                                    f"{dict(carried[a][key])}")
        if sex_col:
            rec["cells_by_sex"] = dict(sorted(sexes[a].items()))
        if a in unannotated:
            rec["unannotated"] = True
        elif ab.get("membership"):
            rec["membership"] = ab["membership"]
        out.append(rec)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()
    cfg = load_config(args.project)
    ab = cfg["annotation_build"]
    acc = cfg["dataset"]["accession"]
    wanted = [c for c in (ab["annotation_column"], ab.get("ontology_column"), ab.get("broad_column"),
                          ab.get("broad_ontology_column"), ab.get("sex_column")) if c]
    lookup = {}
    if ab.get("author_ontology_from"):
        other = REPO_ROOT / "projects" / ab["author_ontology_from"] / "cell_type_annotations.json"
        lookup = {(a["clustering"], a["type"]): a for a in json.loads(other.read_text())["annotations"]}

    annotations, warnings, missing = [], [], []
    for c in cfg["sample_build"]["clusterings"]:
        path = h5ad_path(acc, c["id"])
        if not path.exists():
            missing.append(c["id"])
            continue
        obs = read_obs(path, [col for col in wanted if col in obs_columns(path)])
        cab = ab
        if c.get("fixed_annotation"):
            obs[ab["annotation_column"]] = [c["fixed_annotation"]] * len(obs["_index"])
            cab = dict(ab, membership=c.get("membership", ab.get("membership")))
        anns = build_clustering(obs, cab, c["id"], c.get("name", c["id"]), warnings)
        if lookup:
            for a in anns:
                src = lookup.get((a["clustering"], a["type"]))
                if src:
                    for f in ("author_ontology_id", "author_broad", "author_broad_ontology_id"):
                        if f in src:
                            a[f] = src[f]
                elif not c.get("fixed_annotation") and not a.get("unannotated"):
                    warnings.append(f"{c['id']}/{a['type']}: not in {ab['author_ontology_from']}")
        print(f"  {c['id']}: {len(obs['_index'])} cells, {len(anns)} annotations")
        annotations.extend(anns)
    if missing:
        sys.exit(f"missing h5ad (run scripts/fetch_h5ad.py): {' '.join(missing)}")
    for w in warnings:
        print(f"  WARNING: {w}", file=sys.stderr)

    out = {
        "source": {"doi": cfg["source"]["doi"], "title": cfg["source"].get("title")},
        "dataset": {
            "accession": acc,
            "label_source": "authors' per-analysis h5ad files (flycellatlas.org), obs "
                            f"`{ab['annotation_column']}`",
            "label_level": "author cell type (one entry per annotation, per analysis)",
            "validate_against": "paper and supplementary tables",
        },
        "annotations": annotations,
    }
    out_path = REPO_ROOT / "projects" / args.project / "cell_type_annotations.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(annotations)} annotations -> {out_path}")


if __name__ == "__main__":
    main()
