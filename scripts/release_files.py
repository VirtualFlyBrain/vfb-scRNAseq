#!/usr/bin/env python
"""Write the files VFB loads from this repo, under their published names, into a directory.

VFB reads the scRNAseq files from its OWL server (http://virtualflybrain.org/data/VFB/OWL/),
where the vfb-k8s `scrnaseq-publish` workflow puts them by running this script:

    VFB_scRNAseq_metadata_<project>.owl   metadata/vfb_scRNAseq_metadata_<project>.owl, as is;
                                          vfb-pipeline-collectdata loads it into the main graph
    VFB_scRNAseq_exp_<project>.owl        expression/vfb_scRNAseq_expression_<project>.owl.gz,
                                          unzipped; vfb-pipeline-dumps side-loads it (edges only)
    release_manifest.tsv                  file, bytes: the set the workflow checks before publishing

The names are what VFB's loaders match: collectdata's `VFB_scRNAseq_metadata_*`, and the
dumps / data-release `VFB_scRNAseq_exp_*.owl` (uncompressed). Every project must have both
files. Standard library only, so it runs from a plain clone (no uv environment).

Usage:
    python scripts/release_files.py <out_dir>
"""

from __future__ import annotations

import argparse
import gzip
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
METADATA_PREFIX = "vfb_scRNAseq_metadata_"
EXPRESSION_PREFIX = "vfb_scRNAseq_expression_"
MANIFEST = "release_manifest.tsv"


def projects(root: Path = REPO_ROOT) -> list[str]:
    """Projects with released files; both a metadata and an expression file, or an error."""
    meta = {p.name[len(METADATA_PREFIX):-len(".owl")]
            for p in (root / "metadata").glob(f"{METADATA_PREFIX}*.owl")}
    expr = {p.name[len(EXPRESSION_PREFIX):-len(".owl.gz")]
            for p in (root / "expression").glob(f"{EXPRESSION_PREFIX}*.owl.gz")}
    if meta != expr:
        raise SystemExit(f"metadata and expression files differ: metadata only {sorted(meta - expr)}, "
                         f"expression only {sorted(expr - meta)}")
    return sorted(meta)


def check_owl(path: Path) -> None:
    head = path.open("rb").read(200)
    if not head.startswith(b"<?xml") or b"<rdf:RDF" not in head:
        raise SystemExit(f"{path}: not RDF/XML")


def write_release(out: Path, root: Path = REPO_ROOT) -> list[tuple[str, int]]:
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for p in projects(root):
        meta = out / f"VFB_scRNAseq_metadata_{p}.owl"
        shutil.copyfile(root / "metadata" / f"{METADATA_PREFIX}{p}.owl", meta)
        exp = out / f"VFB_scRNAseq_exp_{p}.owl"
        with gzip.open(root / "expression" / f"{EXPRESSION_PREFIX}{p}.owl.gz", "rb") as src, \
                exp.open("wb") as dst:
            shutil.copyfileobj(src, dst, 1 << 20)
        for f in (meta, exp):
            check_owl(f)
            written.append((f.name, f.stat().st_size))
    (out / MANIFEST).write_text("".join(f"{name}\t{size}\n" for name, size in written))
    return written


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir", type=Path)
    args = ap.parse_args()
    written = write_release(args.out_dir)
    total = sum(size for _, size in written)
    print(f"wrote {len(written)} files ({total / 1e9:.2f} GB) + {MANIFEST} to {args.out_dir}")


if __name__ == "__main__":
    sys.exit(main())
