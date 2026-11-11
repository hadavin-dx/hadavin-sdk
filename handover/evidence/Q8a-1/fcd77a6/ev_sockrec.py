"""EVIDENCE RUNNER pytest plugin: appends one line to $EV_SOCKREC for every socket connect and every name lookup the
test process makes, and one line per test saying whether the two Vault variables are set when the test body starts
(never their values)."""
import os, socket
import pytest
LOG = os.environ["EV_SOCKREC"]
def _w(line):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
_connect, _connect_ex, _gai = socket.socket.connect, socket.socket.connect_ex, socket.getaddrinfo
def connect(self, address):
    _w(f"connect {address!r}"); return _connect(self, address)
def connect_ex(self, address):
    _w(f"connect_ex {address!r}"); return _connect_ex(self, address)
def getaddrinfo(host, *a, **k):
    _w(f"getaddrinfo {host!r}"); return _gai(host, *a, **k)
socket.socket.connect, socket.socket.connect_ex, socket.getaddrinfo = connect, connect_ex, getaddrinfo
_w("plugin loaded; at load VAULT_TOKEN set=%s VAULT_SECRET_ID set=%s" % ("VAULT_TOKEN" in os.environ, "VAULT_SECRET_ID" in os.environ))
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_call(item):
    _w("test %s: in the test body VAULT_TOKEN set=%s VAULT_SECRET_ID set=%s" % (item.nodeid, "VAULT_TOKEN" in os.environ, "VAULT_SECRET_ID" in os.environ))
