import os
import subprocess
from unittest import mock

from vfb_scrnaseq import chado


def _ok(*a, **k):
    return subprocess.CompletedProcess(a[0], 0, "1\n", "")


def _fail(*a, **k):
    return subprocess.CompletedProcess(a[0], 2, "", 'psql: error: connection to server failed')


def setup_function(_):
    chado._chosen = None


def test_default_order_and_443_flags():
    with mock.patch.dict(os.environ, {}, clear=True):
        cmds = [chado._psql_for(h) for h in chado.DEFAULT_CHADO_HOSTS.split(",")]
    assert cmds[0] == ["psql", "-d", "host=chado.flybase.virtualflybrain.org dbname=flybase user=flybase port=443 "
                                    "sslmode=require sslnegotiation=direct", "-At", "-F", "\t"]
    assert cmds[1] == ["psql", "-d", "host=chado.flybase.org dbname=flybase user=flybase", "-At", "-F", "\t"]


def test_falls_back_to_flybase():
    calls = []

    def run(cmd, **k):
        calls.append(cmd[2].split()[0][5:])
        return _fail(cmd) if "virtualflybrain" in cmd[2] else _ok(cmd)

    with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(subprocess, "run", side_effect=run):
        assert chado.psql()[2].startswith("host=chado.flybase.org ")
        chado.psql()  # cached
    assert calls == ["chado.flybase.virtualflybrain.org", "chado.flybase.org"]


def test_env_override():
    with mock.patch.dict(os.environ, {"FB_CHADO_HOST": "db.example:5433"}), mock.patch.object(subprocess, "run", side_effect=_ok):
        assert chado.psql()[2] == "host=db.example dbname=flybase user=flybase port=5433"
