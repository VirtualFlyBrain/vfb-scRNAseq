#!/usr/bin/env python
"""Assemble entities and emit RDF/TTL for a project.

Runs vfb_scrnaseq.build (-> entities.json, minting Cluster IDs) then
vfb_scrnaseq.emit (-> <accession>.ttl), driven by the LinkML schema.

Usage:
    uv run python scripts/build_rdf.py --project kurmangaliyev_2020
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vfb_scrnaseq.build import build_project  # noqa: E402
from vfb_scrnaseq.emit import emit_owl, emit_ttl, to_owlxml  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--format", choices=["owl", "ttl", "both"], default="both",
                    help="owl = linkml-owl (restrictions, VFB-compatible); ttl = flat linkml-convert RDF")
    args = ap.parse_args()

    ent_path, entities = build_project(args.project)
    print(f"built {len(entities)} entities -> {ent_path}")

    proj = REPO_ROOT / "projects" / args.project
    accession = json.loads((proj / "samples.json").read_text())["dataset"]["accession"]
    if args.format in ("ttl", "both"):
        print(f"emitted flat RDF -> {emit_ttl(entities, proj / f'{accession}.ttl')}")
    if args.format in ("owl", "both"):
        ofn = emit_owl(entities, proj / f"{accession}.ofn")
        print(f"emitted OWL      -> {ofn}")
        owlxml = to_owlxml(ofn)               # RDF/XML via ROBOT (skipped if robot absent)
        if owlxml:
            print(f"converted OWL/XML -> {owlxml}")


if __name__ == "__main__":
    main()
