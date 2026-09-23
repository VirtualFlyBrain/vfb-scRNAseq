"""Publication resolver: VFB KB lookup first, config fallback, graceful degradation."""

from vfb_scrnaseq import pub


def test_kb_hit_wins(monkeypatch):
    # KB returns a :pub row -> that FBrf is used, source vfb_kb.
    monkeypatch.setattr(pub, "_kb_query",
                        lambda q, params=None, timeout=30.0: [{"row": ["FBrf0000001", ["12345"], "iri"]}])
    got = pub.resolve_pub(pmid="12345", fallback_fbrf="FBrf9999999")
    assert got == {"fbrf": "FBrf0000001", "pmid": ["12345"], "iri": "iri", "source": "vfb_kb"}


def test_kb_miss_falls_back_to_config(monkeypatch):
    # KB has no matching pub -> fall back to the config-supplied fbrf.
    monkeypatch.setattr(pub, "_kb_query", lambda q, params=None, timeout=30.0: [])
    got = pub.resolve_pub(pmid="12345", fallback_fbrf="FBrf0247594")
    assert got["fbrf"] == "FBrf0247594"
    assert got["source"] == "config"


def test_kb_error_never_fails_build(monkeypatch):
    # A KB error must degrade to the fallback, not raise.
    def boom(*a, **k):
        raise OSError("network down")
    monkeypatch.setattr(pub, "_kb_query", boom)
    assert pub.resolve_pub_in_kb("12345") is None
    got = pub.resolve_pub(pmid="12345", fallback_fbrf="FBrf0247594")
    assert got["fbrf"] == "FBrf0247594" and got["source"] == "config"


def test_no_pmid_and_no_fallback_is_none(monkeypatch):
    # Nothing to resolve -> None (caller warns). KB not even queried without a pmid.
    monkeypatch.setattr(pub, "_kb_query", lambda *a, **k: (_ for _ in ()).throw(AssertionError("queried")))
    assert pub.resolve_pub(pmid=None, fallback_fbrf=None) is None
