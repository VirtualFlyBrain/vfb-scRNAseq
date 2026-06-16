#!/usr/bin/env python
"""Build cell_type_annotations.json for a project from a GEO metadata file.

For GSE156455 (Kurmangaliyev 2020) the GEO ``metadata_<subset>.tsv.gz`` file is
the authoritative cluster-label source: it carries named cell types at three
granularity levels (``class`` -> ``type`` -> ``subtype``) as data columns, is the
*corrected* version (e.g. the T4c/T4d label swap fixed per the GEO README), and
yields per-label cell counts for free. We therefore take labels from GEO and use
the paper PDF only for description/validation.

This builder is intentionally stdlib-only and reproducible: re-running it
regenerates the annotations deterministically from the metadata file.

Usage:
    python scripts/build_annotations_from_geo.py \\
        --project kurmangaliyev_2020 \\
        --accession GSE156455 --subset main \\
        --level subtype \\
        [--metadata /path/to/metadata_main.tsv.gz]   # downloaded if omitted

Column names default to this dataset's convention (class/type/subtype/time);
override with --class-col / --type-col / --level / --time-col for other datasets.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
_USER_AGENT = "vfb-scrnaseq/0.0 (https://github.com/VirtualFlyBrain)"


def geo_suppl_url(accession: str, filename: str) -> str:
    # GEO groups series under GSE<nnn>nnn/<acc>/suppl/
    stub = accession[:-3] + "nnn"
    return f"https://ftp.ncbi.nlm.nih.gov/geo/series/{stub}/{accession}/suppl/{filename}"


def ensure_metadata(accession: str, subset: str, metadata: Path | None) -> Path:
    if metadata and metadata.exists():
        return metadata
    filename = f"{accession}_metadata_{subset}.tsv.gz"
    dest = metadata or (REPO_ROOT / ".cache" / filename)
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = geo_suppl_url(accession, filename)
    print(f"downloading {url} -> {dest}")
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as fh:  # noqa: S310
        fh.write(resp.read())
    return dest


def build(rows, *, level, class_col, type_col, time_col):
    """Aggregate per-label: cell count, dominant class/type, timepoints seen."""
    counts: Counter[str] = Counter()
    classes: dict[str, Counter] = defaultdict(Counter)
    types: dict[str, Counter] = defaultdict(Counter)
    times: dict[str, set] = defaultdict(set)

    for row in rows:
        label = row[level]
        counts[label] += 1
        if class_col in row:
            classes[label][row[class_col]] += 1
        if type_col in row and type_col != level:
            types[label][row[type_col]] += 1
        if time_col in row:
            times[label].add(row[time_col])

    annotations = []
    for label, n in counts.most_common():
        ann = {"label": label, "granularity": level, "cell_number": n}
        if types[label]:
            dom_type, _ = types[label].most_common(1)[0]
            ann["type"] = dom_type
            if len(types[label]) > 1:
                ann["type_ambiguous"] = dict(types[label])
        if classes[label]:
            dom_class, _ = classes[label].most_common(1)[0]
            ann["class"] = dom_class
            if len(classes[label]) > 1:
                ann["class_ambiguous"] = dict(classes[label])
        if times[label]:
            ann["timepoints"] = sorted(times[label])
        annotations.append(ann)
    return annotations


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True)
    p.add_argument("--accession", required=True)
    p.add_argument("--subset", default="main")
    p.add_argument("--level", default="subtype", help="metadata column used as the cluster label")
    p.add_argument("--class-col", default="class")
    p.add_argument("--type-col", default="type")
    p.add_argument("--time-col", default="time")
    p.add_argument("--metadata", type=Path, default=None)
    p.add_argument("--doi", default="10.1016/j.neuron.2020.10.006")
    p.add_argument("--title", default="Transcriptional Programs of Circuit Assembly in the Drosophila Visual System")
    args = p.parse_args()

    meta_path = ensure_metadata(args.accession, args.subset, args.metadata)
    with gzip.open(meta_path, "rt") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))

    annotations = build(
        rows,
        level=args.level,
        class_col=args.class_col,
        type_col=args.type_col,
        time_col=args.time_col,
    )

    out = {
        "source": {"doi": args.doi, "title": args.title},
        "dataset": {
            "accession": args.accession,
            "subset": args.subset,
            "label_source": f"GEO {args.accession}_metadata_{args.subset}.tsv.gz",
            "label_level": args.level,
            "validate_against": "paper PDF (description/names)",
        },
        "annotations": annotations,
    }

    out_path = REPO_ROOT / "projects" / args.project / "cell_type_annotations.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {len(annotations)} annotations ({args.level}) -> {out_path}")


if __name__ == "__main__":
    main()
