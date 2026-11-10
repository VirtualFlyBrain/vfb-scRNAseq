"""scripts/check_merged_genes.py: grouping input genes by current gene and comparing them."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "check_merged_genes", Path(__file__).resolve().parents[1] / "scripts" / "check_merged_genes.py")
cmg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cmg)


def test_merge_groups():
    targets = [("FBgn1", "a"), ("FBgn9", "m"), None, ("FBgn9", "m"), ("FBgn2", "b")]
    assert cmg.merge_groups(targets) == {"FBgn9": [1, 3]}


def test_compare():
    names = ["x1", "x2", "y1", "y2", "z1", "z2"]
    groups = {"FBgnX": [0, 1], "FBgnY": [2, 3], "FBgnZ": [4, 5]}
    entries = {0: {0: 1.0, 5: 2.0}, 1: {5: 1.0, 7: 3.0},       # differ, one shared cell
               2: {1: 4.0}, 3: {1: 4.0}}                        # identical; z zero everywhere
    got = {r["gene"]: r for r in cmg.compare("m.mtx.gz", names, groups, entries)}
    assert got["FBgnX"]["cells"] == [2, 2] and got["FBgnX"]["shared"] == 1
    assert not got["FBgnX"]["identical"]
    assert got["FBgnY"]["identical"] and got["FBgnY"]["inputs"] == ["y1", "y2"]
    assert got["FBgnZ"]["identical"] and got["FBgnZ"]["cells"] == [0, 0]
