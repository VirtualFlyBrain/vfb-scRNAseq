"""Fetch and parse ArrayExpress (BioStudies) experiment metadata: IDF + SDRF.

The non-GEO counterpart of `ingest`: an ArrayExpress experiment (E-MTAB-...) is
described by a MAGE-TAB IDF (investigation) and SDRF (sample and data relationships)
file, served from the BioStudies FTP area over HTTPS. Metadata only, never the reads.

Files are cached in `.cache/` (they can be large: one SDRF row per single cell for
plate-based experiments).
"""

from __future__ import annotations

import csv
import io
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FILES_URL = "https://ftp.ebi.ac.uk/biostudies/fire/E-MTAB-/{tail}/{acc}/Files/{acc}.{kind}.txt"
_USER_AGENT = "vfb-scrnaseq/0.0 (https://github.com/VirtualFlyBrain)"


def files_url(accession: str, kind: str) -> str:
    """URL of an experiment's `idf` or `sdrf` file (BioStudies files are bucketed by
    the last three digits of the accession number)."""
    return FILES_URL.format(tail=accession.split("-")[-1][-3:], acc=accession, kind=kind)


def fetch_text(accession: str, kind: str, cache: Path | None = None) -> str:
    cache = cache or (REPO_ROOT / ".cache")
    path = cache / f"{accession}.{kind}.txt"
    if not path.exists():
        cache.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(files_url(accession, kind), headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=300) as r:  # noqa: S310
            path.write_bytes(r.read())
    return path.read_text(encoding="utf-8")


def parse_sdrf(text: str) -> list[dict[str, str]]:
    """SDRF rows as dicts. MAGE-TAB repeats some column names (`Protocol REF`,
    `Term Source REF`, ...); the first occurrence of each name is kept."""
    reader = csv.reader(io.StringIO(text), delimiter="\t")
    header = next(reader)
    first = {}
    for i, name in enumerate(header):
        first.setdefault(name.strip(), i)
    rows = []
    for r in reader:
        if not any(c.strip() for c in r):
            continue
        rows.append({name: (r[i].strip() if i < len(r) else "") for name, i in first.items()})
    return rows


def parse_idf(text: str) -> dict[str, list[str]]:
    """IDF as {field: [values]} (tab-separated, field name first; blanks dropped)."""
    out: dict[str, list[str]] = {}
    for line in text.splitlines():
        parts = line.split("\t")
        if parts and parts[0].strip():
            out[parts[0].strip()] = [p.strip() for p in parts[1:] if p.strip()]
    return out


def fetch_experiment(accession: str, cache: Path | None = None) -> tuple[dict, list[dict]]:
    """(idf, sdrf rows) for an ArrayExpress experiment."""
    return (parse_idf(fetch_text(accession, "idf", cache)),
            parse_sdrf(fetch_text(accession, "sdrf", cache)))
