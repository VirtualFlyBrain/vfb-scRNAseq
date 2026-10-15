#!/usr/bin/env python
"""Download the authors' per-analysis AnnData (.h5ad) files for a project.

Each `sample_build.clusterings` entry in config.yaml may carry an `h5ad` URL (one
author analysis = one Clustering). Files go to `.cache/h5ad/<accession>/<id>.h5ad`
(gitignored). A file that is there and opens as HDF5 counts as done.

The download goes to `<id>.h5ad.download` first (partial downloads are resumed with
HTTP range requests); a gzipped one (URL ending `.gz`, e.g. GEO supplementary files)
is then decompressed. Before it is put in place, a file whose datasets are not
compressed is recompressed with HDF5's own gzip filter (lossless, verified dataset by
dataset; h5py reads it transparently — `vfb_scrnaseq.h5ad_compress`), which cuts
uncompressed author files to a third of the size or less. `--compress-existing`
does the same for files already in the cache. Nextcloud share links
(`.../index.php/s/<token>`) are fetched via their `/download` endpoint.

Usage:
    uv run python scripts/fetch_h5ad.py --project li_2022_fca_10x [--only head body]
    uv run python scripts/fetch_h5ad.py --project lu_2023_afca --compress-existing
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

import h5py  # noqa: E402

from vfb_scrnaseq.h5ad_compress import compress, is_compressed  # noqa: E402
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


def opens(path: Path) -> bool:
    """A complete h5ad: present and readable as HDF5 (a partial download is not)."""
    try:
        with h5py.File(path, "r"):
            return True
    except OSError:
        return False


def put_in_place(part: Path, dest: Path) -> None:
    """Move a downloaded h5ad to `dest`, gzip-compressing it first unless it already is."""
    if is_compressed(part):
        part.replace(dest)
        print(f"  ok      {dest.name} ({dest.stat().st_size / 1e6:.0f} MB, already compressed)")
        return
    tmp = dest.with_name(dest.name + ".compressing")
    before = part.stat().st_size
    compress(part, tmp)
    tmp.replace(dest)
    if part != dest:
        part.unlink()
    print(f"  compressed {dest.name}: {before / 1e6:.0f} -> {dest.stat().st_size / 1e6:.0f} MB (verified)")


def fetch_any(url: str, dest: Path) -> None:
    """Download `url` (decompressing a .gz download) and put it in place at `dest`,
    gzip-compressed."""
    if dest.exists() and opens(dest):
        print(f"  ok      {dest.name} ({dest.stat().st_size / 1e6:.0f} MB)")
        return
    dl = dest.with_name(dest.name + ".download")
    fetch(url, dl)
    if url.endswith(".gz"):
        part = dest.with_name(dest.name + ".part")
        with gzip.open(dl, "rb") as src, open(part, "wb") as out:
            shutil.copyfileobj(src, out, 1 << 22)
        dl.unlink()
        print(f"  decompressed {dest.name} ({part.stat().st_size / 1e6:.0f} MB)")
    else:
        part = dl
    put_in_place(part, dest)


def compress_existing(dest: Path) -> None:
    if not (dest.exists() and opens(dest)):
        print(f"  skip    {dest.name} (not downloaded)")
    elif is_compressed(dest):
        print(f"  ok      {dest.name} (already compressed)")
    else:
        put_in_place(dest, dest)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--only", nargs="*", help="clustering ids to fetch (default: all)")
    ap.add_argument("--compress-existing", action="store_true",
                    help="gzip-compress already-cached files that are not compressed (no download)")
    args = ap.parse_args()
    cfg = load_config(args.project)
    acc = cfg["dataset"]["accession"]
    failed = []
    for c in cfg["sample_build"]["clusterings"]:
        if not isinstance(c, dict) or not c.get("h5ad") or (args.only and c["id"] not in args.only):
            continue
        try:
            if args.compress_existing:
                compress_existing(h5ad_path(acc, c["id"]))
            else:
                fetch_any(c["h5ad"], h5ad_path(acc, c["id"]))
        except Exception as e:  # noqa: BLE001 - report and carry on with the rest
            failed.append(c["id"])
            print(f"  FAILED  {c['id']}: {e}", file=sys.stderr)
    if failed:
        sys.exit(f"failed: {' '.join(failed)}")


if __name__ == "__main__":
    main()
