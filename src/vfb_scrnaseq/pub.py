"""Resolve a dataset's publication to an existing VFB ``:pub`` node (FlyBase FBrf).

VFB datasets link to a publication via a ``:pub`` node keyed on its FlyBase
``FBrf`` id (the Dataset gets ``dc:references <FBrf>``). To avoid orphaning that
link, we resolve the FBrf from an authority rather than inventing it.

Lookup order (see :func:`resolve_pub`):

1. The **VFB curation KB** (``kb.virtualflybrain.org``) — queried by PMID. This is
   where a freshly-curated pub appears first, so it is checked every build even
   when the config already carries an ``fbrf``.
2. **VFB production** (``pdb.virtualflybrain.org``, no credentials) — where pubs of
   already-released data live (the scRNAseq pubs are in production, not the KB).
3. The config fallback (``source.fbrf``) — a curator-supplied FBrf, used when
   neither database has a matching node.

Each lookup degrades gracefully: any network/query error returns ``None`` so a
build never fails just because a database is unreachable.

Endpoints are read-only (public KB login ``neo4j``/``vfb``; production needs none) and
overridable via env ``VFBSEQ_KB_URL``, ``VFBSEQ_KB_USER``, ``VFBSEQ_KB_PASSWORD``,
``VFBSEQ_PDB_URL``. These are deliberately NOT the ``VFB_KB_*`` names, which curators
commonly set for the *writable* KB (kbw) — reusing them sent the wrong credentials to the
public KB (HTTP 401).
"""

from __future__ import annotations

import base64
import json
import os
import ssl
import sys
import urllib.request

KB_URL = os.environ.get("VFBSEQ_KB_URL", "https://kb.virtualflybrain.org/db/neo4j/tx/commit")
KB_USER = os.environ.get("VFBSEQ_KB_USER", "neo4j")
KB_PASSWORD = os.environ.get("VFBSEQ_KB_PASSWORD", "vfb")
PDB_URL = os.environ.get("VFBSEQ_PDB_URL", "https://pdb.virtualflybrain.org/db/neo4j/tx/commit")

PUB_BY_PMID = ("MATCH (p:pub) WHERE $pmid IN p.PMID "
               "RETURN p.short_form AS fbrf, p.PMID AS pmid, p.iri AS iri LIMIT 1")


def _neo4j_query(url: str, cypher: str, params: dict | None = None, timeout: float = 30.0,
                 auth: tuple[str, str] | None = None) -> list:
    """POST a Cypher query to a neo4j HTTP transaction endpoint; return rows."""
    body = json.dumps({"statements": [{"statement": cypher, "parameters": params or {}}]}).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    if auth:
        token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
        req.add_header("Authorization", "Basic " + token)
    with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as r:
        data = json.loads(r.read())
    if data.get("errors"):
        raise RuntimeError(str(data["errors"]))
    return data["results"][0]["data"]


def _kb_query(cypher: str, params: dict | None = None, timeout: float = 30.0) -> list:
    return _neo4j_query(KB_URL, cypher, params, timeout, auth=(KB_USER, KB_PASSWORD))


def _pdb_query(cypher: str, params: dict | None = None, timeout: float = 30.0) -> list:
    return _neo4j_query(PDB_URL, cypher, params, timeout)


def _lookup(query, name: str, pmid: str | None, timeout: float) -> dict | None:
    if not pmid:
        return None
    try:
        rows = query(PUB_BY_PMID, {"pmid": str(pmid)}, timeout=timeout)
    except Exception as e:  # noqa: BLE001 — never fail a build on a pub lookup
        print(f"  WARNING: {name} pub lookup failed ({type(e).__name__}: {str(e)[:100]})",
              file=sys.stderr)
        return None
    if not rows:
        return None
    fbrf, pmid_val, iri = rows[0]["row"]
    return {"fbrf": fbrf, "pmid": pmid_val, "iri": iri}


def resolve_pub_in_kb(pmid: str | None = None, timeout: float = 30.0) -> dict | None:
    """Look up an existing ``:pub`` node by PMID in the VFB curation KB.

    Returns ``{'fbrf', 'pmid', 'iri'}`` or ``None`` (also on any error, with a
    warning). ``:pub`` nodes store ``PMID`` as a list, so we test list membership.
    """
    return _lookup(_kb_query, "VFB KB", pmid, timeout)


def resolve_pub_in_pdb(pmid: str | None = None, timeout: float = 30.0) -> dict | None:
    """As :func:`resolve_pub_in_kb`, against VFB production (pdb)."""
    return _lookup(_pdb_query, "VFB production", pmid, timeout)


def resolve_pub(pmid: str | None = None, doi: str | None = None,
                fallback_fbrf: str | None = None) -> dict | None:
    """Resolve the FBrf for a dataset's publication.

    Checks the VFB KB by PMID first (catches freshly-added pubs), then VFB
    production, then falls back to a config-supplied FBrf. Returns ``{'fbrf', 'source', ...}`` or ``None`` if
    nothing resolves (caller should warn the curator).
    """
    hit = resolve_pub_in_kb(pmid)
    if hit:
        return {**hit, "source": "vfb_kb"}
    hit = resolve_pub_in_pdb(pmid)
    if hit:
        return {**hit, "source": "vfb_pdb"}
    if fallback_fbrf:
        return {"fbrf": fallback_fbrf, "pmid": pmid, "iri": None, "source": "config"}
    return None
