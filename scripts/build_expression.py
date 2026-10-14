#!/usr/bin/env python
"""Compute + emit the summary expression data for a project.

Runs vfb_scrnaseq.stats (streaming CPM extent/level, filter extent>cutoff) and writes:
  - projects/<p>/expression.tsv            filtered rows (committed, diffable; written
                                           gzipped, expression.tsv.gz, with
                                           `expression.gzip_tsv: true` for large datasets)
  - projects/<p>/expression_report.md      per-cluster cell + total/filtered gene counts
  - projects/<p>/expression_counts.json    {label: {total,filtered}} for build.py
  - expression/vfb_scRNAseq_expression_<project>.owl.gz   gzipped OWL (committed,
                                                 loadable; aggregated across projects for VFB)

Requires the Cluster ids to be minted first (run build_rdf.py). The GEO matrix/
features/barcodes (or, for `expression.source: h5ad`, the h5ad files from
scripts/fetch_h5ad.py) must be in .cache (see config `expression`).

Usage:
    uv run python scripts/build_expression.py --project kurmangaliyev_2020
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vfb_scrnaseq.emit import emit_expression_owl  # noqa: E402
from vfb_scrnaseq.project_config import load_config  # noqa: E402
from vfb_scrnaseq.stats import compute_expression  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    cfg = load_config(args.project)
    proj = REPO_ROOT / "projects" / args.project
    acc = cfg["dataset"]["accession"]
    hide = str(cfg["expression"].get("hide_in_terminfo", "true"))

    print("computing expression stats (streaming CPM)...")
    rows, counts, meta = compute_expression(args.project, cfg)
    print(f"  {meta['n_genes']} genes, {meta['n_cells']} cells, {len(counts)} clusters; "
          f"{len(rows):,} rows with extent>{meta['cutoff']}")

    # 1. filtered expression table (diffable)
    gz = bool(cfg["expression"].get("gzip_tsv"))
    tsv = proj / ("expression.tsv.gz" if gz else "expression.tsv")
    with (gzip.GzipFile(tsv, "wb", mtime=0) if gz else tsv.open("wb")) as raw, \
            io.TextIOWrapper(raw, encoding="utf-8", newline="") as fh:     # mtime=0: byte-identical rebuilds
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["cluster_id", "cluster_label", "fbgn", "gene_symbol",
                    "expression_level", "expression_extent"])
        w.writerows(rows)
    print(f"  wrote {tsv}")

    # 2. per-cluster report (unfiltered vs filtered gene counts)
    report = proj / "expression_report.md"
    with report.open("w") as fh:
        fh.write(f"# Expression summary — {acc}\n\n")
        fh.write(f"- normalisation: **{meta['normalisation']}**; extent filter: **> {meta['cutoff']}**\n")
        fh.write(f"- {meta['n_genes']} genes x {meta['n_cells']} cells; {len(counts)} clusters; "
                 f"{len(rows):,} filtered rows\n")
        fh.write(f"- dataset-level: total_gene_count **{meta['dataset_total_gene_count']}**, "
                 f"filtered_gene_count **{meta['dataset_filtered_gene_count']}**\n\n")
        fh.write("| cluster | cells | total_gene_count | filtered_gene_count |\n")
        fh.write("|---|---|---|---|\n")
        for c in counts:
            fh.write(f"| {c.label} | {c.cells} | {c.total_gene_count} | {c.filtered_gene_count} |\n")
    print(f"  wrote {report}")

    # 3. gene counts for build.py: dataset-level (-> Dataset) + per-cluster (-> Cluster).
    counts_json = proj / "expression_counts.json"
    counts_json.write_text(json.dumps({
        "dataset": {"total_gene_count": meta["dataset_total_gene_count"],
                    "filtered_gene_count": meta["dataset_filtered_gene_count"]},
        "clusters": {c.label: {"total_gene_count": c.total_gene_count,
                               "filtered_gene_count": c.filtered_gene_count} for c in counts},
    }, indent=2) + "\n")
    print(f"  wrote {counts_json}")

    # 4. gzipped OWL (efficient direct emit + single robot convert) — the loadable
    #    artifact, aggregated across projects in the top-level expression/ folder.
    expr_dir = REPO_ROOT / "expression"
    expr_dir.mkdir(exist_ok=True)
    out = emit_expression_owl(rows, expr_dir / f"vfb_scRNAseq_expression_{args.project}.owl.gz", hide=hide)
    print(f"  emitted {out}")


if __name__ == "__main__":
    main()
