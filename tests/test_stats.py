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


def test_membership_file_overlapping_clusterings(tmp_path, monkeypatch):
    # a second clustering "sub" splits A into A1 (cells 1-2) and A2 (cells 3-5): each
    # cell is counted once per clustering, and the A/B results are unchanged
    cfg = _setup(tmp_path, monkeypatch)
    mem = "barcode\tcluster\n" + "".join(
        f"bc{i}\t{'A' if i <= 5 else 'B'}\n" for i in range(1, 11))
    mem += "".join(f"bc{i}\t{'A1' if i <= 2 else 'A2'}\n" for i in range(1, 6))
    _write(tmp_path / ".cache" / "mem.tsv.gz", mem)
    cfg["expression"]["membership_file"] = "mem.tsv.gz"
    rows, counts, meta = stats.compute_expression("t", cfg)
    by = {c.label: c for c in counts}
    assert {k: v.cells for k, v in by.items()} == {"A": 5, "B": 5, "A1": 2, "A2": 3}
    assert (by["A"].total_gene_count, by["A"].filtered_gene_count) == (2, 1)
    ext = {(label, sym): round(extent, 3) for _i, label, _f, sym, _l, extent in rows}
    assert ext[("A1", "sym1")] == 1.0          # g1 in cells 1,2
    assert ext[("A1", "sym2")] == 0.5          # g2 in cell 1
    assert ext[("A2", "sym1")] == round(1 / 3, 3)
    assert meta["n_cells"] == 10               # distinct cells, not memberships


def test_extra_parts_combine_second_matrix(tmp_path, monkeypatch):
    # a second matrix (same genes) with its own cells/clusters is added as a part;
    # the main part's results are unchanged and the extra clusters get their prefix
    cfg = _setup(tmp_path, monkeypatch)
    cache = tmp_path / ".cache"
    entries = [(1, 1), (1, 2), (3, 2)]                       # cells e1,e2 in cluster X
    mtx = "%%MatrixMarket matrix coordinate real general\n%\n"
    mtx += f"4 2 {len(entries)}\n" + "".join(f"{g} {c} 1\n" for g, c in entries)
    _write(cache / "m2.mtx.gz", mtx)
    _write(cache / "b2.tsv.gz", "e1\ne2\n")
    _write(cache / "md2.tsv.gz", "barcode\tsubtype\ne1\tX\ne2\tX\n")
    cfg["expression"]["extra_parts"] = [{"matrix_file": "m2.mtx.gz", "features_file": "f.tsv.gz",
                                         "barcodes_file": "b2.tsv.gz", "metadata_file": "md2.tsv.gz",
                                         "label_prefix": "early_"}]
    rows, counts, meta = stats.compute_expression("t", cfg)
    by = {c.label: c for c in counts}
    assert set(by) == {"A", "B", "early_X"} and by["early_X"].cells == 2
    assert (by["A"].total_gene_count, by["A"].filtered_gene_count) == (2, 1)    # main part unchanged
    ext = {(label, sym): round(extent, 2) for _i, label, _f, sym, _l, extent in rows}
    assert ext[("early_X", "sym1")] == 1.0 and ext[("early_X", "sym3")] == 0.5
    assert meta["n_cells"] == 12


def test_gene_id_map_merge_rename_drop(tmp_path, monkeypatch):
    # g2 is a retired id of g1 (merge: cell 1 expresses both and must count once),
    # g3 is renamed to a current id, g4 is dropped (split/withdrawn)
    cfg = _setup(tmp_path, monkeypatch)
    proj = tmp_path / "projects" / "t"
    proj.mkdir(parents=True)
    (proj / "gene_id_map.tsv").write_text(
        "# test\ninput_fbgn\tinput_symbol\tstatus\tcurrent_fbgn\tcurrent_symbol\n"
        "FBgn0000001\tsym1\tcurrent\tFBgn0000001\tnew1\n"
        "FBgn0000002\tsym2\tsecondary\tFBgn0000001\tnew1\n"
        "FBgn0000003\tsym3\tsecondary\tFBgn0000099\tsym99\n"
        "FBgn0000004\tsym4\tsplit\t\tFBgn1 a; FBgn2 b\n")
    cfg["expression"]["gene_id_map"] = "gene_id_map.tsv"
    rows, counts, meta = stats.compute_expression("t", cfg)
    got = {(label, fbgn, sym): (lvl, ext) for _i, label, fbgn, sym, lvl, ext in rows}
    # merged gene in A: cells 1,2,3 express it (cell 1 once) -> extent 0.6; each of those
    # cells' library is all in this gene -> CPM 1e6 -> level 1e6 (not halved/doubled)
    assert got[("A", "FBgn0000001", "new1")] == (1e6, 0.6)
    assert ("B", "FBgn0000099", "sym99") in got
    assert not any(f in ("FBgn0000002", "FBgn0000003", "FBgn0000004") for _l, f, _s in got)
    assert meta["n_genes"] == 2                               # new1 + sym99
