"""Resolve a dataset's publication to an existing VFB ``:pub`` node (FlyBase FBrf).

VFB datasets link to a publication via a ``:pub`` node keyed on its FlyBase
``FBrf`` id (the Dataset gets ``dc:references <FBrf>``). To avoid orphaning that
link, we resolve the FBrf from an authority rather than inventing it.

Lookup order (see :func:`resolve_pub`):

1. The **VFB curation KB** (``kb.virtualflybrain.org``) — queried by PMID. This is
   where a freshly-curated pub appears first, so it is checked every build even
   when the config already carries an ``fbrf``.
2. The config fallback (``source.fbrf``) — a curator-supplied / production-confirmed
   FBrf, used when the KB has no matching node (e.g. an older pub already released
   to production but not present in the curation KB).

The KB lookup degrades gracefully: any network/query error returns ``None`` so a
build never fails just because the KB is unreachable — it falls back to config.

Credentials/endpoint are read-only and overridable via env (``VFB_KB_URL``,
``VFB_KB_USER``, ``VFB_KB_PASSWORD``).
"""

from __future__ import annotations

import base64
import json
import os
import ssl
import sys
import urllib.request

KB_URL = os.environ.get("VFB_KB_URL", "https://kb.virtualflybrain.org/db/neo4j/tx/commit")
KB_USER = os.environ.get("VFB_KB_USER", "neo4j")
KB_PASSWORD = os.environ.get("VFB_KB_PASSWORD", "vfb")


def _kb_query(cypher: str, params: dict | None = None, timeout: float = 30.0) -> list:
    """POST a Cypher query to the KB neo4j HTTP transaction endpoint; return rows."""
    body = json.dumps({"statements": [{"statement": cypher, "parameters": params or {}}]}).encode()
    req = urllib.request.Request(KB_URL, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    token = base64.b64encode(f"{KB_USER}:{KB_PASSWORD}".encode()).decode()
    req.add_header("Authorization", "Basic " + token)
    with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as r:
        data = json.loads(r.read())
    if data.get("errors"):
        raise RuntimeError(str(data["errors"]))
    return data["results"][0]["data"]


def resolve_pub_in_kb(pmid: str | None = None, timeout: float = 30.0) -> dict | None:
    """Look up an existing VFB ``:pub`` node by PMID in the curation KB.

    Returns ``{'fbrf', 'pmid', 'iri'}`` or ``None``. On any error (network, auth,
    query) returns ``None`` and warns — the caller falls back to config.
    ``:pub`` nodes store ``PMID`` as a list, so we test list membership.
    """
    if not pmid:
        return None
    try:
        rows = _kb_query(
            "MATCH (p:pub) WHERE $pmid IN p.PMID "
            "RETURN p.short_form AS fbrf, p.PMID AS pmid, p.iri AS iri LIMIT 1",
            {"pmid": str(pmid)}, timeout=timeout)
    except Exception as e:  # noqa: BLE001 — never fail a build on the KB check
        print(f"  WARNING: VFB KB pub lookup failed ({type(e).__name__}: {str(e)[:100]}); "
              f"falling back to config", file=sys.stderr)
        return None
    if not rows:
        return None
    fbrf, pmid_val, iri = rows[0]["row"]
    return {"fbrf": fbrf, "pmid": pmid_val, "iri": iri}


def resolve_pub(pmid: str | None = None, doi: str | None = None,
                fallback_fbrf: str | None = None) -> dict | None:
    """Resolve the FBrf for a dataset's publication.

    Checks the VFB KB by PMID first (catches freshly-added pubs), then falls back
    to a config-supplied FBrf. Returns ``{'fbrf', 'source', ...}`` or ``None`` if
    nothing resolves (caller should warn the curator).
    """
    hit = resolve_pub_in_kb(pmid)
    if hit:
        return {**hit, "source": "vfb_kb"}
    if fallback_fbrf:
        return {"fbrf": fallback_fbrf, "pmid": pmid, "iri": None, "source": "config"}
    return None
