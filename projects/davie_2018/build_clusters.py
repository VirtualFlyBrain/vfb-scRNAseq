#!/usr/bin/env python
"""Davie 2018: define the authors' clusters, type them, and assemble cluster mappings.

Project-specific (the paper's clustering layout and Table S2 are this atlas's), so it
lives in the project folder. One row = one author cluster. Clusterings:

  res2          Seurat res-2.0, the paper's "87 initial clusters" (Table S2) -- GEO `res.2`
  res8          the res-8.0 clusters Table S2 annotates                      -- GEO `res.8`
  sub20/27/42/64  the authors' sub-clusterings of res-2.0 clusters 20, 27, 42, 64
  neuropeptide  the re-clustering of neuropeptide-expressing cells (Figure 2K)
Sub-clustering / neuropeptide membership has no cluster-id column in GEO, so it is
taken from the authors' per-cell `annotation` (their name for that sub-cluster).
Sub-clusters (sub20/27/42/64) carry `parent_cluster` = the res-2.0 cluster the authors
re-clustered (emitted as *part of*); res-8.0 clusters and the neuropeptide groups are
not nested in a single res-2.0 cluster, so get no parent.

Typing (curator decision): the authors' GEO annotation is authoritative; Table S2 is
recorded alongside, and where S2 makes a different call the cluster is flagged
(`author_conflict`, -> verification_needed). A res-2.0 cluster the authors sub-
clustered takes its S2 parent call (GEO only names the sub-clusters). Clusters the
authors left numbered are `unannotated` (held: listed in mapping.tsv, not loaded).

Writes
  cell_type_annotations.json                         one entry per cluster
  .cache/GSE107451_57k_cluster_membership.tsv.gz     barcode -> cluster (expression stats)
  mapping/<cluster>.fbbt_mapping.json                from type_mapping/<type>.fbbt_mapping.json
                                                     (+ the S2-conflict flag)
Usage:
    uv run python projects/davie_2018/build_clusters.py
"""

from __future__ import annotations

import csv
import gzip
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJ = Path(__file__).resolve().parent
REPO = PROJ.parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(PROJ))

from supp_evidence import SYNONYMS, _norm, read_s2  # noqa: E402
from vfb_scrnaseq.project_config import label_slug, load_config  # noqa: E402

PROJECT = "davie_2018"
MEMBERSHIP = REPO / ".cache" / "GSE107451_57k_cluster_membership.tsv.gz"

SUBCLUSTERED = {"20": "sub20", "27": "sub27", "42": "sub42", "64": "sub64"}
# res-8.0 clusters annotated in Table S2
RES8_ANNOTATED = ["30", "118", "119", "129", "151"]
# GEO labels from the neuropeptide re-clustering ("all cells expressing neuropeptides";
# Table S2 lists LNv, IPC, Capa, Hugin, CCAP; GEO names further groups)
NEUROPEPTIDE = ["LNv", "IPC", "Capa", "Hug", "CCAP", "AstA/Nplp1", "AstA/NPF", "CCHa1",
                "Crz", "FMRFa", "ITP", "Mip/ITP", "Mip/OCT", "Proc/Ms", "Proc/Gpb5"]
# GEO labels that are exactly a res-8.0 cluster (checked: 98/98 and 79/79 cells)
RES8_LABELS = {"DCN": "118", "Gr43a": "129"}
# Table S2 names for the neuropeptide / sub-cluster groups, where S2 lists them
S2_GROUP_NAMES = {"LNv": "LNv", "IPC": "IPC", "Capa": "Capa neurons", "Hug": "Hugin neurons",
                  "CCAP": "CCAP", "L1": "L1", "L2": "L2", "L3": "L3", "L4/L5": "L4/L5",
                  "PAM": "PAM (Fer2(+)) neurons", "Dopaminergic": "Fer2(-) neurons",
                  "Octopaminergic": "Octopaminergic", "Tyraminergic": "Tyraminergic",
                  "adPN/C15": "C15(+) adPNs", "adPN/C15&kn": "C15(+) kn(+) adPNs",
                  "adPN/kn": "kn(+) adPNs", "lPN/unpg": "unpg(+) lPNs",
                  "lPN/CG31676": "CG31676(+) lPNs"}
CLUSTERING_DESC = {
    "res2": "res-2.0", "res8": "res-8.0",
    "sub20": "sub-clustering of cluster 20", "sub27": "sub-clustering of cluster 27",
    "sub42": "sub-clustering of cluster 42", "sub64": "sub-clustering of cluster 64",
    "neuropeptide": "neuropeptide re-clustering",
}


def same_call(geo: str, s2: str) -> bool:
    return _norm(geo) == _norm(s2) or _norm(SYNONYMS.get(geo, "")) == _norm(s2)


def main() -> None:
    cfg = load_config(PROJECT)
    acfg = cfg["annotations"]
    with gzip.open(REPO / ".cache" / acfg["source_file"], "rt") as fh:
        cells = list(csv.DictReader(fh, delimiter="\t"))
    bc_col = acfg.get("barcode_column", "barcode")
    s2_res2, s2_other = read_s2()
    s2_res8 = {o["cluster_id"]: o["annotation"] for o in s2_other if o["level"] == "res8"}

    finer = set(NEUROPEPTIDE) | set(RES8_LABELS)
    by_res2: dict[str, list] = defaultdict(list)
    for c in cells:
        by_res2[c["res.2"]].append(c)
    for rid in SUBCLUSTERED:
        finer |= {c["annotation"] for c in by_res2[rid]} - set(NEUROPEPTIDE)

    clusters = []      # annotation entries
    membership = []    # (barcode, cluster label)

    def add(clustering, source_id, members, author_type, s2_call, s2_note="", s2_equivalent=False,
            parent=None):
        key = f"{clustering}_{source_id}"
        unannotated = bool(re.fullmatch(r"\d+", author_type))
        conflict = ""
        if s2_equivalent:
            pass                      # S2's own name for this sub-cluster (S2_GROUP_NAMES)
        elif s2_call and s2_call != "Unannotated" and not unannotated and not same_call(author_type, s2_call):
            conflict = f"Table S2 calls this cluster '{s2_call}'"
        elif s2_call == "Unannotated" and not unannotated:
            conflict = "Table S2 lists this cluster as Unannotated"
        elif unannotated and s2_call and s2_call != "Unannotated":
            conflict = f"Table S2 calls this cluster '{s2_call}' (GEO leaves it numbered)"
        clusters.append({
            "label": key,
            "type": author_type,
            "clustering": clustering,
            "clustering_name": CLUSTERING_DESC[clustering],
            "source_cluster_id": source_id,
            "cell_number": len(members),
            "timepoints": sorted({m["Age"] for m in members}, key=int),
            "s2_annotation": s2_call or s2_note,
            "author_conflict": conflict,
            "unannotated": unannotated,
        })
        if parent:
            clusters[-1]["parent_cluster"] = parent
        membership.extend((m[bc_col], key) for m in members)

    # res-2.0: all 87 clusters
    for rid in sorted(by_res2, key=int):
        members = by_res2[rid]
        s2 = s2_res2.get(rid, {}).get("annotation", "")
        if rid in SUBCLUSTERED:
            author_type = s2          # GEO names only the sub-clusters; S2 gives the parent
        else:
            own = Counter(m["annotation"] for m in members if m["annotation"] not in finer)
            author_type = own.most_common(1)[0][0]
        add("res2", rid, members, author_type, s2)

    # res-8.0: the clusters Table S2 annotates; typed by the GEO majority of their cells
    by_res8: dict[str, list] = defaultdict(list)
    for c in cells:
        by_res8[c["res.8"]].append(c)
    for rid in RES8_ANNOTATED:
        members = by_res8[rid]
        geo = Counter(m["annotation"] for m in members).most_common(1)[0][0]
        add("res8", rid, members, geo, s2_res8.get(rid, ""))

    # sub-clusterings: one cluster per GEO label inside the parent res-2.0 cluster
    for rid, clustering in SUBCLUSTERED.items():
        groups: dict[str, list] = defaultdict(list)
        for m in by_res2[rid]:
            if m["annotation"] not in NEUROPEPTIDE:
                groups[m["annotation"]].append(m)
        for lab in sorted(groups, key=lambda x: -len(groups[x])):
            add(clustering, lab, groups[lab], lab, S2_GROUP_NAMES.get(lab, ""),
                s2_note="(not listed in Table S2)", s2_equivalent=True,
                parent=f"res2_{rid}")   # all its cells are in the parent res-2.0 cluster

    # neuropeptide re-clustering: one cluster per GEO label
    groups = defaultdict(list)
    for c in cells:
        if c["annotation"] in NEUROPEPTIDE:
            groups[c["annotation"]].append(c)
    for lab in NEUROPEPTIDE:
        add("neuropeptide", lab, groups[lab], lab, S2_GROUP_NAMES.get(lab, ""),
            s2_note="(not listed in Table S2)", s2_equivalent=True)

    out = {
        "source": {"doi": cfg["source"]["doi"], "title": cfg["source"]["title"]},
        "dataset": {
            "accession": cfg["dataset"]["accession"],
            "subset": acfg.get("subset"),
            "label_source": f"GEO {acfg['source_file']} (cluster columns res.2/res.8 + "
                            f"authors' per-cell `annotation` for sub-clusterings)",
            "label_level": "author cluster (one entry per cluster, per clustering)",
            "validate_against": "Table S2 (s2_annotation / author_conflict)",
        },
        "annotations": clusters,
    }
    (PROJ / "cell_type_annotations.json").write_text(json.dumps(out, indent=2) + "\n")
    with gzip.open(MEMBERSHIP, "wt") as fh:
        fh.write("barcode\tcluster\n")
        fh.writelines(f"{b}\t{k}\n" for b, k in membership)

    # assemble cluster-level mappings from the type-level mappings
    mdir, tdir = PROJ / "mapping", PROJ / "type_mapping"
    mdir.mkdir(exist_ok=True)
    for old in mdir.glob("*.fbbt_mapping.json"):
        old.unlink()
    missing = []
    for a in clusters:
        if a["unannotated"]:
            continue
        type_key = a["type"] if a["clustering"] != "res2" or a["source_cluster_id"] not in SUBCLUSTERED \
            else a["label"]
        src = tdir / f"{label_slug(type_key)}.fbbt_mapping.json"
        if not src.exists():
            missing.append((a["label"], type_key))
            continue
        m = json.loads(src.read_text())
        m["cluster_label"] = a["label"]
        if a["author_conflict"]:
            m["verification_needed"] = True
            m["recommendation"] = (m["recommendation"].rstrip()
                                   + f" [Author sources differ: GEO labels this cluster "
                                     f"'{a['type']}'; {a['author_conflict']}.]")
        (mdir / f"{label_slug(a['label'])}.fbbt_mapping.json").write_text(json.dumps(m, indent=2) + "\n")

    per = Counter(a["clustering"] for a in clusters)
    print(f"{len(clusters)} clusters {dict(per)}; "
          f"{sum(a['unannotated'] for a in clusters)} unannotated; "
          f"{sum(bool(a['author_conflict']) for a in clusters)} with an S2 conflict")
    if missing:
        print(f"  {len(missing)} typed clusters lack a type mapping: {missing}")


if __name__ == "__main__":
    main()
