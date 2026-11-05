"""Offline guard: sockets may reach loopback only (the simulator and the local postgres test service)."""

import ipaddress
import socket

import pytest

_REAL_CONNECT = socket.socket.connect


def _is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


@pytest.fixture(autouse=True)
def _socket_guard(monkeypatch):
    def guarded(self, address, *a, **k):
        if self.family in (socket.AF_INET, socket.AF_INET6) and not _is_loopback(str(address[0])):
            raise RuntimeError("tests are offline: only loopback is allowed")
        return _REAL_CONNECT(self, address, *a, **k)

    monkeypatch.setattr(socket.socket, "connect", guarded)


@pytest.fixture(autouse=True, scope="session")
def _render_config():
    """A bare `pytest` works on a fresh clone: render config/config.yaml from its template first (design 10.16)."""
    from jagrat.render_config import render

    render()
