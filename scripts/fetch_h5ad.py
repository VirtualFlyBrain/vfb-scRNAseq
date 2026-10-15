#!/usr/bin/env python
"""Download the authors' per-analysis AnnData (.h5ad) files for a project.

Each `sample_build.clusterings` entry in config.yaml may carry an `h5ad` URL (one
author analysis = one Clustering). Files go to `.cache/h5ad/<accession>/<id>.h5ad`
(gitignored); existing complete files are skipped and partial ones resumed (HTTP
range requests). Nextcloud share links (`.../index.php/s/<token>`) are fetched via
their `/download` endpoint. A gzipped file (URL ending `.gz`, e.g. GEO supplementary
files) is downloaded next to the target and decompressed; the .gz is then removed, so
an existing decompressed file counts as done.

Usage:
    uv run python scripts/fetch_h5ad.py --project li_2022_fca_10x [--only head body]
"""

from __future__ import annotations

import argparse
import gzip
import shutil
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vfb_scrnaseq.ingest_h5ad import h5ad_path  # noqa: E402,F401  (re-exported)
from vfb_scrnaseq.project_config import load_config  # noqa: E402

_USER_AGENT = "vfb-scrnaseq/0.0 (https://github.com/VirtualFlyBrain)"


def download_url(url: str) -> str:
    return url.rstrip("/") + "/download" if "/index.php/s/" in url else url


def remote_size(url: str) -> int | None:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT, "Range": "bytes=0-0"})
    with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310
        cr = r.headers.get("Content-Range", "")
    return int(cr.rsplit("/", 1)[1]) if "/" in cr else None


def fetch(url: str, dest: Path) -> None:
    url = download_url(url)
    size = remote_size(url)
    have = dest.stat().st_size if dest.exists() else 0
    if size is not None and have == size:
        print(f"  ok      {dest.name} ({size / 1e6:.0f} MB)")
        return
    if size is not None and have > size:
        have = 0
    dest.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": _USER_AGENT}
    if have:
        headers["Range"] = f"bytes={have}-"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, "ab" if have else "wb") as out:  # noqa: S310
        while chunk := r.read(1 << 22):
            out.write(chunk)
    got = dest.stat().st_size
    if size is not None and got != size:
        raise RuntimeError(f"{dest.name}: got {got} of {size} bytes")
    print(f"  fetched {dest.name} ({got / 1e6:.0f} MB)")


def fetch_any(url: str, dest: Path) -> None:
    """fetch(), decompressing a .gz download into `dest`."""
    if not url.endswith(".gz"):
        fetch(url, dest)
        return
    gz = dest.with_name(dest.name + ".gz")
    if dest.exists() and not gz.exists():
        print(f"  ok      {dest.name} ({dest.stat().st_size / 1e6:.0f} MB, decompressed)")
        return
    fetch(url, gz)
    tmp = dest.with_name(dest.name + ".part")
    with gzip.open(gz, "rb") as src, open(tmp, "wb") as out:
        shutil.copyfileobj(src, out, 1 << 22)
    tmp.replace(dest)
    gz.unlink()
    print(f"  decompressed {dest.name} ({dest.stat().st_size / 1e6:.0f} MB)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--only", nargs="*", help="clustering ids to fetch (default: all)")
    args = ap.parse_args()
    cfg = load_config(args.project)
    acc = cfg["dataset"]["accession"]
    failed = []
    for c in cfg["sample_build"]["clusterings"]:
        if not isinstance(c, dict) or not c.get("h5ad") or (args.only and c["id"] not in args.only):
            continue
        try:
            fetch_any(c["h5ad"], h5ad_path(acc, c["id"]))
        except Exception as e:  # noqa: BLE001 - report and carry on with the rest
            failed.append(c["id"])
            print(f"  FAILED  {c['id']}: {e}", file=sys.stderr)
    if failed:
        sys.exit(f"failed: {' '.join(failed)}")


if __name__ == "__main__":
    main()
