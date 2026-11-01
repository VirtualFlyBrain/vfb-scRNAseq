#!/usr/bin/env python
"""Check every entity in the released metadata links each entity type it should.

Reads metadata/vfb_scRNAseq_metadata_*.owl, the files VFB loads, as one graph (a
Clustering can use Samples another project emits), so it also catches a link the
build meant to make but the OWL emission dropped. Rules (docs/DESIGN.md, *Entity
links*): an entity must have at least one edge, in either direction, to each type
listed for it, and the listed class / annotation links.

    Dataset     Sample, Assay, Clustering, Cluster; publication, licence, assay type
    Sample      Dataset, Assay, Clustering; tissue, stage
    Assay       Dataset, Sample; method
    Clustering  Dataset, Sample (or Assay), Cluster
    Cluster     Dataset, Clustering; cell type

Exemptions, each with its reason in the project config, are the only way past a
missing link:
- a Sample no clustering uses: `sample_build.unclustered_samples` (sample_id -> reason);
- a Clustering whose clusters are all held: `no_clusters: <reason>` on its
  `sample_build.clusterings` entry.

Usage:
    uv run python scripts/check_entity_links.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import rdflib
import yaml
from rdflib import OWL, RDF

REPO_ROOT = Path(__file__).resolve().parents[1]
OBO = "http://purl.obolibrary.org/obo/"
VFB = "http://virtualflybrain.org/reports/"

#: Entity type class -> name.
TYPES = {
    OBO + "FBcv_0003023": "Dataset",
    OBO + "FBcv_0003024": "Sample",
    OBO + "FBcv_0003025": "Assay",
    OBO + "FBcv_0009002": "Clustering",
    OBO + "FBcv_0009003": "Cluster",
}

#: Entity type -> groups of entity types it must link; each group needs one edge to
#: any of its types (a Clustering's parts may be Samples or Assays).
ENTITY_LINKS = {
    "Dataset": [{"Sample"}, {"Assay"}, {"Clustering"}, {"Cluster"}],
    "Sample": [{"Dataset"}, {"Assay"}, {"Clustering"}],
    "Assay": [{"Dataset"}, {"Sample"}],
    "Clustering": [{"Dataset"}, {"Sample", "Assay"}, {"Cluster"}],
    "Cluster": [{"Dataset"}, {"Clustering"}],
}

#: Entity type -> (description, property IRI) of class-valued (restriction) or
#: annotation links it must have.
OTHER_LINKS = {
    "Dataset": [("publication", "http://purl.org/dc/terms/references"),
                ("licence", "http://purl.org/dc/terms/licence"),
                ("assay type", OBO + "OBI_0000312")],
    "Sample": [("tissue", OBO + "RO_0002131"), ("stage", OBO + "RO_0002490")],
    "Assay": [("method", "http://www.bioassayontology.org/bao#BAO_0000212")],
    "Cluster": [("cell type", OBO + "RO_0002473")],
}


def load_graph(files: list[Path]) -> rdflib.Graph:
    g = rdflib.Graph()
    for f in files:
        g.parse(f, format="xml")
    return g


def exemptions(root: Path = REPO_ROOT) -> dict[tuple[str, str], str]:
    """(entity IRI, entity type it may lack) -> reason, from the project configs."""
    out = {}
    for cfg_path in sorted((root / "projects").glob("*/config.yaml")):
        sb = (yaml.safe_load(cfg_path.read_text()) or {}).get("sample_build") or {}
        listed = sb.get("unclustered_samples") or {}
        no_clusters = {c["id"]: c["no_clusters"] for c in sb.get("clusterings") or []
                       if isinstance(c, dict) and c.get("no_clusters")}
        if not (listed or no_clusters):
            continue
        built = json.loads((cfg_path.parent / "samples.json").read_text())
        by_id = {s["sample_id"]: s["vfbseq_id"] for s in built["samples"]}
        for sample_id, reason in listed.items():
            if sample_id not in by_id:
                raise ValueError(f"{cfg_path}: unclustered_samples names unknown sample {sample_id!r}")
            out[(VFB + by_id[sample_id], "Clustering")] = reason
        by_subset = {c["subset"]: c["vfbseq_id"] for c in built["clusterings"]}
        for subset, reason in no_clusters.items():
            out[(VFB + by_subset[subset], "Cluster")] = reason
    return out


def check(g: rdflib.Graph, exempt: dict[tuple[str, str], str] | None = None) -> list[str]:
    """Problems, one line each; empty when every entity has its links."""
    exempt = exempt or {}
    kind = {}
    for s, o in g.subject_objects(RDF.type):
        if str(o) in TYPES:
            kind[s] = TYPES[str(o)]

    linked = defaultdict(set)              # entity -> entity types it has an edge to
    props = defaultdict(set)               # entity -> property IRIs it uses (direct or restriction)
    for s, p, o in g:
        if s in kind and o in kind:
            linked[s].add(kind[o])
            linked[o].add(kind[s])
        if s in kind:
            props[s].add(str(p))
    for s, o in g.subject_objects(RDF.type):
        if s in kind and isinstance(o, rdflib.BNode):
            on = g.value(o, OWL.onProperty)
            if on is not None:
                props[s].add(str(on))

    problems = []
    for ent, k in sorted(kind.items(), key=lambda kv: (kv[1], str(kv[0]))):
        label = g.value(ent, rdflib.RDFS.label)
        name = f"{k} {str(ent).replace(VFB, '')} ({label})"
        for group in ENTITY_LINKS[k]:
            if linked[ent] & group:
                continue
            if len(group) == 1 and (str(ent), next(iter(group))) in exempt:
                continue
            problems.append(f"{name}: no link to a {' or '.join(sorted(group))}")
        for what, prop in OTHER_LINKS.get(k, []):
            if prop not in props[ent]:
                problems.append(f"{name}: no {what}")
    return problems


def main() -> None:
    files = sorted((REPO_ROOT / "metadata").glob("vfb_scRNAseq_metadata_*.owl"))
    problems = check(load_graph(files), exemptions())
    if problems:
        print(f"{len(problems)} missing entity links:")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print(f"entity links ok ({len(files)} metadata files)")


if __name__ == "__main__":
    main()
