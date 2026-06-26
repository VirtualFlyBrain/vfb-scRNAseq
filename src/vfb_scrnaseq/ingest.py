"""Fetch dataset/sample metadata from GEO.

This module retrieves *metadata only* — the Series/Sample structure, accessions,
characteristics (stage/sex/strain), platform, SRA/BioProject relations, and
supplementary-file URLs. It never downloads the expression matrix; that is a
later (expression-stats) concern.

Source of truth is GEO's SOFT text endpoint (the same content GEOparse parses
from the FTP ``*_family.soft.gz``), fetched over plain HTTP with no auth:

    https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE...&targ=all&form=text&view=full

Design notes:
- Stdlib only (``urllib``) so it runs in CI without extra deps. If GEOparse /
  pysradb are installed they can be slotted into :func:`fetch_series` later for
  richer parsing and GEO<->SRA (GSM->SRX/SRR) resolution; the parsing here is a
  faithful subset sufficient for the metadata our LinkML schema records.
- Parsing is offline-testable: :func:`parse_soft` takes a string, so fixtures
  exercise it without network access.
- Mapping characteristics onto FBdv stages / the schema's sex enum is *not* done
  here — that needs ontology lookup and belongs in :mod:`vfb_scrnaseq.build`.
  This module exposes the raw characteristics plus light hint accessors.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from urllib.parse import urlencode

GEO_ACC_URL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"
_USER_AGENT = "vfb-scrnaseq/0.0 (https://github.com/VirtualFlyBrain)"


@dataclass
class GeoSample:
    """One GEO Sample (GSM) — maps toward the schema's Sample / Assay."""

    accession: str
    title: str | None = None
    organism: str | None = None
    #: Raw "tag: value" characteristics, tag-keyed (lowercased tag).
    characteristics: dict[str, str] = field(default_factory=dict)
    #: Sample_relation entries, e.g. {"SRA": "SRX...", "BioSample": "SAMN..."}.
    relations: dict[str, str] = field(default_factory=dict)
    supplementary_files: list[str] = field(default_factory=list)

    def characteristic(self, *tags: str) -> str | None:
        """First matching characteristic value across the given (lowercased) tags."""
        for tag in tags:
            val = self.characteristics.get(tag.lower())
            if val:
                return val
        return None

    @property
    def stage_hint(self) -> str | None:
        return self.characteristic("developmental stage", "stage", "age", "time")

    @property
    def sex_hint(self) -> str | None:
        return self.characteristic("sex", "gender")


@dataclass
class GeoSeries:
    """A GEO Series (GSE) — maps toward the schema's Dataset."""

    accession: str
    title: str | None = None
    summary: str | None = None
    platform_ids: list[str] = field(default_factory=list)
    #: Series_relation entries, e.g. {"BioProject": "PRJNA...", "SRA": "SRP..."}.
    relations: dict[str, str] = field(default_factory=dict)
    samples: list[GeoSample] = field(default_factory=list)
    supplementary_files: list[str] = field(default_factory=list)

    @property
    def bioproject(self) -> str | None:
        return self.relations.get("BioProject")

    @property
    def sra_study(self) -> str | None:
        return self.relations.get("SRA")


def soft_url(accession: str) -> str:
    query = urlencode({"acc": accession, "targ": "all", "form": "text", "view": "full"})
    return f"{GEO_ACC_URL}?{query}"


def fetch_soft(accession: str, *, timeout: float = 60.0, retries: int = 4,
               backoff: float = 3.0) -> str:
    """Download the SOFT text for a GEO accession (no auth).

    GEO's acc.cgi intermittently returns 5xx (502/503) or times out; retry with
    exponential backoff on transient errors before giving up.
    """
    req = urllib.request.Request(soft_url(accession), headers={"User-Agent": _USER_AGENT})
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (trusted host)
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            last_err = exc
            if exc.code < 500:  # 4xx is not transient — fail fast
                raise
        except (urllib.error.URLError, TimeoutError) as exc:
            last_err = exc
        if attempt < retries - 1:
            time.sleep(backoff * (2 ** attempt))
    raise RuntimeError(f"GEO fetch for {accession} failed after {retries} attempts: {last_err}")


def _strip_relation_value(raw: str) -> tuple[str, str]:
    """Parse a *_relation value like 'SRA: https://.../?term=SRP123' -> ('SRA','SRP123')."""
    kind, _, rest = raw.partition(":")
    kind = kind.strip()
    rest = rest.strip()
    # Relations are usually a URL whose last path/query segment is the accession.
    token = rest.rstrip("/").split("/")[-1]
    if "=" in token:
        token = token.split("=")[-1]
    return kind, token or rest


def parse_soft(text: str) -> GeoSeries:
    """Parse GEO SOFT text into a :class:`GeoSeries` (offline-testable)."""
    series: GeoSeries | None = None
    current: GeoSample | None = None  # the sample block currently being filled

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")
        if not line or line.startswith(("#", "^DATABASE", "^PLATFORM")):
            # We don't model platforms as blocks; platform id comes via Series_platform_id.
            if line.startswith("^PLATFORM"):
                current = None
            continue

        if line.startswith("^SERIES"):
            acc = line.split("=", 1)[1].strip() if "=" in line else ""
            series = GeoSeries(accession=acc)
            current = None
            continue

        if line.startswith("^SAMPLE"):
            acc = line.split("=", 1)[1].strip() if "=" in line else ""
            current = GeoSample(accession=acc)
            if series is not None:
                series.samples.append(current)
            continue

        if not line.startswith("!") or "=" not in line:
            continue

        key, value = line[1:].split("=", 1)
        key = key.strip()
        value = value.strip()

        if key.startswith("Series_") and series is not None:
            _apply_series_field(series, key, value)
        elif key.startswith("Sample_") and current is not None:
            _apply_sample_field(current, key, value)

    if series is None:
        raise ValueError("No ^SERIES record found in SOFT text")
    return series


def _apply_series_field(series: GeoSeries, key: str, value: str) -> None:
    if key == "Series_title":
        series.title = value
    elif key == "Series_summary":
        series.summary = f"{series.summary} {value}".strip() if series.summary else value
    elif key == "Series_geo_accession":
        series.accession = value or series.accession
    elif key == "Series_platform_id":
        series.platform_ids.append(value)
    elif key == "Series_relation":
        kind, token = _strip_relation_value(value)
        series.relations[kind] = token
    elif key.startswith("Series_supplementary_file"):
        series.supplementary_files.append(value)


def _apply_sample_field(sample: GeoSample, key: str, value: str) -> None:
    if key == "Sample_title":
        sample.title = value
    elif key == "Sample_geo_accession":
        sample.accession = value or sample.accession
    elif key == "Sample_organism_ch1":
        sample.organism = value
    elif key == "Sample_characteristics_ch1":
        tag, _, val = value.partition(":")
        if val:
            sample.characteristics[tag.strip().lower()] = val.strip()
    elif key == "Sample_relation":
        kind, token = _strip_relation_value(value)
        sample.relations[kind] = token
    elif key.startswith("Sample_supplementary_file"):
        sample.supplementary_files.append(value)


def fetch_series(accession: str, *, timeout: float = 60.0) -> GeoSeries:
    """Fetch and parse a GEO Series into a :class:`GeoSeries`."""
    return parse_soft(fetch_soft(accession, timeout=timeout))
