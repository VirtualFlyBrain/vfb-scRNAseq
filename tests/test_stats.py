"""Expression stats on a tiny synthetic 10x matrix: guards the gene-count
definitions (dataset total = expressed in any cluster; dataset filtered = union of
extent > cutoff across clusters, NOT a dataset-wide extent) and the extent filter.

4 genes x 10 cells, clusters A (cells 1-5) and B (cells 6-10):
  g1: cells 1,2,3 (A: 3/5=0.6) + 6 (B: 1/5=0.2)   -> filtered in A only
  g2: cell 1      (A: 1/5=0.2)                     -> expressed, never > cutoff
  g3: cells 6,7,8 (B: 3/5=0.6)                     -> filtered in B only
  g4: none                                         -> not expressed at all
cutoff 0.2 (strict >). So dataset total=3 (g1,g2,g3), filtered=2 (g1,g3).
"""

import gzip

from vfb_scrnaseq import stats


class _FakeReg:
    @classmethod
    def load(cls, path):
        return cls()

    def get(self, entity_type, key):
        return "VFBseq_TEST"


def _write(path, text):
    with gzip.open(path, "wt") as fh:
        fh.write(text)


def _setup(tmp_path, monkeypatch):
    cache = tmp_path / ".cache"
    cache.mkdir()
    entries = [(1, 1), (1, 2), (1, 3), (1, 6), (2, 1), (3, 6), (3, 7), (3, 8)]  # (gene, cell), value 1
    mtx = "%%MatrixMarket matrix coordinate real general\n%\n"
    mtx += f"4 10 {len(entries)}\n" + "".join(f"{g} {c} 1\n" for g, c in entries)
    _write(cache / "m.mtx.gz", mtx)
    _write(cache / "f.tsv.gz", "".join(f"FBgn000000{i}\tsym{i}\n" for i in range(1, 5)))
    _write(cache / "b.tsv.gz", "".join(f"bc{i}\n" for i in range(1, 11)))
    md = "barcode\tsubtype\n" + "".join(
        f"bc{i}\t{'A' if i <= 5 else 'B'}\n" for i in range(1, 11))
    _write(cache / "md.tsv.gz", md)

    monkeypatch.setattr(stats, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(stats, "IDRegistry", _FakeReg)
    cfg = {
        "dataset": {"accession": "GSETEST"},
        "annotations": {"subset": "main", "label_column": "subtype", "source_file": "md.tsv.gz"},
        "expression": {"matrix_file": "m.mtx.gz", "features_file": "f.tsv.gz",
                       "barcodes_file": "b.tsv.gz", "extent_cutoff": 0.2, "normalisation": "CPM"},
    }
    return cfg


def test_dataset_gene_counts_union_not_datasetwide(tmp_path, monkeypatch):
    cfg = _setup(tmp_path, monkeypatch)
    _, _, meta = stats.compute_expression("t", cfg)
    assert meta["dataset_total_gene_count"] == 3       # g1,g2,g3 expressed (g4 never)
    assert meta["dataset_filtered_gene_count"] == 2     # g1 (A) + g3 (B); g2 max extent 0.2 not > cutoff


def test_per_cluster_counts_and_extent_filter(tmp_path, monkeypatch):
    cfg = _setup(tmp_path, monkeypatch)
    rows, counts, _ = stats.compute_expression("t", cfg)
    by = {c.label: c for c in counts}
    assert by["A"].cells == 5 and by["B"].cells == 5
    assert (by["A"].total_gene_count, by["A"].filtered_gene_count) == (2, 1)  # g1,g2 expressed; g1>cutoff
    assert (by["B"].total_gene_count, by["B"].filtered_gene_count) == (2, 1)  # g1,g3 expressed; g3>cutoff
    # only the two above-cutoff cluster x gene rows survive the filter
    kept = {(label, round(extent, 2)) for _iri, label, _fbgn, _sym, _lvl, extent in rows}
    assert kept == {("A", 0.6), ("B", 0.6)}
