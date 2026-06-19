#!/usr/bin/env python
"""Build cell_type_annotations.json for a project from its GEO metadata file.

Generic across GEO projects: all column names, the source file, DOI/title and
accession are read from the project's config.yaml (`annotations`, `source`,
`dataset` sections) via vfb_scrnaseq.project_config. Per-label it records the
cell count, the dominant value of each `carry_columns` entry (flagging any that
are ambiguous), and the set of timepoints seen.

(For non-GEO sources, write a sibling ingester that emits the same
cell_type_annotations.json shape; the downstream config/placeholder/collate
layers are unchanged.)

Usage:
    python scripts/build_annotations_from_geo.py --project kurmangaliyev_2020
    # optional: --metadata /path/to/local_copy.tsv.gz   (else downloaded from GEO)
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vfb_scrnaseq.project_config import load_config  # noqa: E402

_USER_AGENT = "vfb-scrnaseq/0.0 (https://github.com/VirtualFlyBrain)"


def geo_suppl_url(accession: str, filename: str) -> str:
    stub = accession[:-3] + "nnn"
    return f"https://ftp.ncbi.nlm.nih.gov/geo/series/{stub}/{accession}/suppl/{filename}"


def ensure_metadata(accession: str, filename: str, metadata: Path | None) -> Path:
    if metadata and metadata.exists():
        return metadata
    dest = metadata or (REPO_ROOT / ".cache" / filename)
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = geo_suppl_url(accession, filename)
    print(f"downloading {url} -> {dest}")
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as fh:  # noqa: S310
        fh.write(resp.read())
    return dest


def build(rows, *, label_col, carry_cols, time_col):
    counts: Counter[str] = Counter()
    carried: dict[str, dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
    times: dict[str, set] = defaultdict(set)

    for row in rows:
        label = row[label_col]
        counts[label] += 1
        for col in carry_cols:
            if col in row and col != label_col:
                carried[label][col][row[col]] += 1
        if time_col and time_col in row:
            times[label].add(row[time_col])

    annotations = []
    for label, n in counts.most_common():
        ann = {"label": label, "granularity": label_col, "cell_number": n}
        for col in carry_cols:
            counter = carried[label].get(col)
            if counter:
                dom, _ = counter.most_common(1)[0]
                ann[col] = dom
                if len(counter) > 1:
                    ann[f"{col}_ambiguous"] = dict(counter)
        if times[label]:
            ann["timepoints"] = sorted(times[label])
        annotations.append(ann)
    return annotations


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--metadata", type=Path, default=None, help="local metadata file (else downloaded)")
    args = ap.parse_args()

    cfg = load_config(args.project)
    acfg = cfg["annotations"]
    src, ds = cfg.get("source", {}), cfg.get("dataset", {})

    meta_path = ensure_metadata(ds["accession"], acfg["source_file"], args.metadata)
    with gzip.open(meta_path, "rt") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))

    annotations = build(
        rows,
        label_col=acfg["label_column"],
        carry_cols=acfg.get("carry_columns", []),
        time_col=acfg.get("timepoint_column"),
    )

    out = {
        "source": {"doi": src.get("doi"), "title": src.get("title")},
        "dataset": {
            "accession": ds.get("accession"),
            "subset": acfg.get("subset"),
            "label_source": f"GEO {acfg['source_file']}",
            "label_level": acfg["label_column"],
            "validate_against": "paper PDF (description/names)",
        },
        "annotations": annotations,
    }

    out_path = REPO_ROOT / "projects" / args.project / "cell_type_annotations.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {len(annotations)} annotations ({acfg['label_column']}) -> {out_path}")


if __name__ == "__main__":
    main()
