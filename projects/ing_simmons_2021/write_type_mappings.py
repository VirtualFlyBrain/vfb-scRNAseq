#!/usr/bin/env python
"""Ing-Simmons et al. 2021: the type-level FBbt mappings (curator 2026-10-18).

Types are the authors' cluster identities without the cluster number
(build_clusters.py). The embryos are 2.5-3.5 h after egg laying (stage 5 to the
gastrula stage), so the embryonic cell-level terms apply:

- ectoderm / mesoderm: the germ-layer cell terms (somatic cell of ectoderm / mesoderm),
  the authors' words, not the pre-gastrulation anlage terms (curator);
- cellularisation: somatic cell of stage 5 embryo (the authors: "cells from embryos in
  the earlier stages of cellularization"; the clusters also carry embryonic stage 5);
- amnioserosa, terminal: the somatic cell terms of those structures;
- pole cells: embryonic pole cell; haemocytes: embryonic/larval hemocyte; trachea
  precursor: tracheal precursor cell;
- neural: held (curator): FBbt has no cell-level term for a generic embryonic neural
  cell, and embryonic neuroblast would go beyond the authors' typing (neural2's markers
  are neuronal).

Terms and definitions are read from OLS.

Usage:
    uv run python projects/ing_simmons_2021/write_type_mappings.py
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

from vfb_scrnaseq.project_config import label_slug

PROJ = Path(__file__).resolve().parent
OLS = "https://www.ebi.ac.uk/ols4/api/ontologies/fbbt/terms?obo_id="
MAPPED = {   # author type: (FBbt id, markers the authors name, justification)
    "ectoderm": ("FBbt:00059305", "ab, sca, SoxN",
                 "The authors' ectoderm clusters; the germ-layer term (curator: the authors' word, and most "
                 "embryos in the 2.5-3.5 h window are gastrulating), not the pre-gastrulation anlage."),
    "mesoderm": ("FBbt:00059307", "twi, Mlc2, Mdr49",
                 "The authors' mesoderm clusters; the germ-layer term (curator: the authors' word, and most "
                 "embryos in the 2.5-3.5 h window are gastrulating), not the pre-gastrulation anlage."),
    "cellularisation": ("FBbt:00059313", "bnk, slam",
                        "The authors: \"Two clusters express cellularization stage genes (bnk, slam) and "
                        "represent cells from embryos in the earlier stages of cellularization due to the "
                        "timed collection\": somatic cells of the stage 5 embryo (the clusters' stage, "
                        "embryonic stage 5, from their own expression)."),
    "amnioserosa": ("FBbt:00059314", "Ance, peb", "The authors' amnioserosa cluster."),
    "terminal": ("FBbt:00059312", "fkh",
                 "The authors' cluster of the terminal regions of the embryo."),
    "pole cell": ("FBbt:00053322", "pgc",
                  "The authors' pole cells, at 2.5-3.5 h still pole cells (the primordial germ cell term "
                  "covers their later fate in the gonad)."),
    "haemocyte": ("FBbt:00001684", "PPO1",
                  "The authors' haemocyte clusters (embryonic)."),
    "trachea precursor": ("FBbt:00005041", "Osiris gene cluster",
                          "The authors' trachea precursor cluster."),
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
    for typ, (fid, markers, why) in MAPPED.items():
        best = term(fid)
        write(typ, {
            "working_definition": f"Cells of the authors' {typ} cluster(s) (Ing-Simmons et al. 2021, Fig. 2; "
                                  f"markers {markers}), control embryos at 2.5-3.5 h after egg laying.",
            "searches_performed": [best["fbbt_term"]],
            "best_match": {**best, "match_type": "exact match", "skos_mapping": "skos:exactMatch",
                           "confidence": "high"},
            "justification": why,
            "other_candidates": [],
            "recommendation": f"Map to {fid} {best['fbbt_term']} (exact match).",
            "new_term_needed": False,
            "verification_needed": False,
        })
    write("neural", {
        "working_definition": "Cells of the authors' neural clusters (Ing-Simmons et al. 2021, Fig. 2): neural1 "
                              "with neuroblast / ganglion mother cell markers (wor, pros, insb, nerfin-1, scrt), "
                              "neural2 with neuronal markers (chinmo, Appl, Rdl); control embryos at 2.5-3.5 h.",
        "searches_performed": ["embryonic neural cell", "neuroectodermal cell", "embryonic neuroblast"],
        "best_match": None,
        "justification": "FBbt has no cell-level term for a generic embryonic neural cell (neuroectoderm and the "
                         "neurogenic regions are tissues); embryonic neuroblast would go beyond the authors' "
                         "typing, and neural2's markers are neuronal. Held (curator 2026-10-18).",
        "other_candidates": [],
        "recommendation": "Hold: no adequate FBbt term.",
        "new_term_needed": False,
        "verification_needed": False,
    })
    print(f"wrote {len(MAPPED) + 1} type mappings (neural held)")


if __name__ == "__main__":
    main()
