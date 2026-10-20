#!/usr/bin/env python
"""Saavedra et al. 2023: the type-level FBbt mappings (2026-10-20).

Types are the authors' cluster names (build_clusters.py), annotated against the Fly Cell
Atlas, from dissected adult male thoraces. Adult cell terms; narrowed by the dissected
tissue only where that makes the term exact (the FCA rules): cell body glia are CNS-only
and the thorax's CNS is the VNC, so adult VNC cell body glial cell; perineurial glia also
sheath the thorax's peripheral nerves, so not narrowed. Tissue types (ventral nervous
system, peripheral nervous system, salivary gland) to their main cell type, broad, as the
curator chose for Calderon 2022's brain / VNC clusters. "Unknown cluster" is held in
build_clusters.py. Terms and definitions are read from OLS.

Usage:
    uv run python projects/saavedra_2023/write_type_mappings.py
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

from vfb_scrnaseq.project_config import label_slug

PROJ = Path(__file__).resolve().parent
OLS = "https://www.ebi.ac.uk/ols4/api/ontologies/fbbt/terms?obo_id="
E, B = "exact match", "broad match"
MAPPED = {   # author type: (FBbt id, match, justification)
    "Indirect flight muscle": ("FBbt:00003361", E, "Indirect flight muscle (adult-only)."),
    "Muscle cell": ("FBbt:00058230", E, "Thoracic muscle not resolved further by the authors."),
    "Adult alary muscle": ("FBbt:00003545", E, ""),
    "Epithelial cell": ("FBbt:00058238", E, "Thoracic epithelial cells not resolved further by the authors."),
    "Adipose tissue": ("FBbt:00049949", E, "The adipose tissue (fat body): its cell type, the fat cell."),
    "Tracheal": ("FBbt:00005040", E, "Tracheal cells."),
    "Hemocyte": ("FBbt:00058143", E, ""),
    "Cell body glial cell": ("FBbt:00059288", E, "Cell body glia are CNS-only and the thorax's CNS is the ventral "
                                                 "nerve cord, so the VNC term is exact (FCA rule)."),
    "Perineurial glial sheath": ("FBbt:00058251", E, "Perineurial glia; not narrowed to the VNC, since the thorax's "
                                                     "peripheral nerves also have a perineurial sheath (FCA rule)."),
    "Ventral nervous system": ("FBbt:00059289", B, "A tissue type (the ventral nervous system): its main cell type, "
                                                   "the neuron (as for Calderon 2022's brain / VNC clusters)."),
    "Peripheral nervous system": ("FBbt:00059276", B, "A tissue type (the peripheral nervous system): its main cell "
                                                      "type, the neuron (as for Calderon 2022)."),
    "Adult salivary gland": ("FBbt:00059269", B, "A tissue type: its epithelial cells (the secretory cell would be "
                                                 "narrower than the authors say)."),
}


def term(fbbt_id: str) -> dict:
    with urllib.request.urlopen(OLS + urllib.parse.quote(fbbt_id)) as r:
        t = json.load(r)["_embedded"]["terms"][0]
    assert not t["is_obsolete"], fbbt_id
    return {"fbbt_term": t["label"], "fbbt_id": fbbt_id, "fbbt_definition": " ".join(t["description"])}


def write(typ: str, m: dict) -> None:
    path = PROJ / "type_mapping" / f"{label_slug(typ)}.fbbt_mapping.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"cluster_label": typ, **m}, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    for typ, (fid, match, why) in MAPPED.items():
        best = term(fid)
        write(typ, {
            "working_definition": f"Nuclei of the authors' {typ!r} cluster(s) (Saavedra et al. 2023, Figure 3a), "
                                  f"dissected adult male thoraces, control genotype.",
            "searches_performed": [typ],
            "best_match": {**best, "match_type": match,
                           "skos_mapping": "skos:exactMatch" if match == E else "skos:broadMatch",
                           "confidence": "high"},
            "justification": (f"The authors' annotation {typ!r} (Fly Cell Atlas-based). " + why).strip(),
            "other_candidates": [],
            "recommendation": f"Map to {fid} {best['fbbt_term']} ({match}).",
            "new_term_needed": False,
            "verification_needed": False,
        })
    print(f"wrote {len(MAPPED)} type mappings")


if __name__ == "__main__":
    main()
