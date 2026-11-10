"""Which FlyBase Chado server to query.

VFB's own copy first (chado.flybase.virtualflybrain.org, Postgres 17 "direct SSL" on port 443, so it needs psql 17
or newer), then FlyBase's public server. FB_CHADO_HOST overrides the list: comma-separated host or host:port.
The first server that answers a trivial query is used for the rest of the run.
"""
import os
import subprocess

DEFAULT_CHADO_HOSTS = "chado.flybase.virtualflybrain.org:443,chado.flybase.org"

_chosen = None


def _psql_for(entry):
    host, _, port = entry.partition(":")
    conninfo = "host=%s dbname=flybase user=flybase" % host
    if port:
        conninfo += " port=" + port
    if port == "443":
        # SNI-routed TLS on 443: TLS straight away, no Postgres SSLRequest round trip (libpq 17+)
        conninfo += " sslmode=require sslnegotiation=direct"
    return ["psql", "-d", conninfo, "-At", "-F", "\t"]


def psql():
    """The psql command (list) for the first reachable Chado server."""
    global _chosen
    if _chosen is not None:
        return _chosen
    hosts = [h.strip() for h in (os.environ.get("FB_CHADO_HOST") or DEFAULT_CHADO_HOSTS).split(",") if h.strip()]
    last = None
    for entry in hosts:
        cmd = _psql_for(entry)
        try:
            r = subprocess.run(cmd + ["-c", "select 1"], capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired) as e:
            last = str(e)
            continue
        if r.returncode == 0:
            _chosen = cmd
            return cmd
        last = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "exit %d" % r.returncode
    raise SystemExit("No FlyBase Chado server reachable (tried %s): %s" % (", ".join(hosts), last))
