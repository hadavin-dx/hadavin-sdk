"""The one no-redirect HTTP opener, shared by the executor, the model clients and the read tools.

A redirect would carry a bearer token or API key to a host nobody configured or allowlisted: every redirect is
refused. Kept here, neutral and secret-free, so ``runtime`` and ``tools`` can use it without importing a module
that holds a secret (tests/test_repo_rules.py scans the transitive imports).

Neutral protocol: HTTP/1.1 over the standard library.
"""

from __future__ import annotations

import http.client
import ipaddress
import socket
import ssl
import urllib.request

from hadavin_sdk.guard.egress import EgressRefused, normalise_host

LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})


def _refused(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    mapped = getattr(ip, "ipv4_mapped", None)
    ip = mapped or ip
    return (
        ip.is_loopback or ip.is_link_local or ip.is_unspecified or ip.is_multicast or ip.is_reserved
    )


def checked_connection(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None):
    """Resolve the host ONCE, refuse it if any answer is loopback, link-local (the cloud metadata address),
    unspecified, multicast or reserved, and connect to a checked address. The name is looked up exactly once, so
    a DNS answer that changes between the check and the connect (rebinding) cannot reach the socket; TLS still
    verifies the certificate against the NAME (the connection keeps `host` for SNI). Private ranges are allowed:
    in-cluster services live there. An explicit loopback name (tests) is connected as it is."""
    host, port = address
    if normalise_host(host) in LOOPBACK:
        return socket.create_connection(address, timeout, source_address)
    ips: list[str] = []
    for _, _, _, _, sockaddr in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM):
        ip = ipaddress.ip_address(sockaddr[0].split("%")[0])
        if _refused(ip):
            raise EgressRefused(f"{host} resolves to a refused address")
        ips.append(sockaddr[0])
    if not ips:
        raise OSError(f"{host} did not resolve")
    last: OSError | None = None
    for ip in dict.fromkeys(ips):
        try:
            return socket.create_connection((ip, port), timeout, source_address)
        except OSError as exc:
            last = exc
    raise last or OSError(f"{host} could not be reached")


class _CheckedMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._create_connection = checked_connection


class CheckedHTTPConnection(_CheckedMixin, http.client.HTTPConnection):
    pass


class CheckedHTTPSConnection(_CheckedMixin, http.client.HTTPSConnection):
    pass


class CheckedHTTPHandler(urllib.request.HTTPHandler):
    def http_open(self, req):
        return self.do_open(CheckedHTTPConnection, req)


class CheckedHTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(CheckedHTTPSConnection, req, context=self._context)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirect, CheckedHTTPHandler, CheckedHTTPSHandler)
# A loopback host is reached directly: an HTTP_PROXY would otherwise carry plain-http traffic off the machine.
LOCAL_OPENER = urllib.request.build_opener(
    NoRedirect, urllib.request.ProxyHandler({}), CheckedHTTPHandler, CheckedHTTPSHandler
)


def opener_for(context: ssl.SSLContext, direct: bool = False) -> urllib.request.OpenerDirector:
    """An opener that trusts exactly the CAs in `context` (a per-source or per-tool CA bundle), still without
    redirects and with the same resolve-once address check."""
    handlers: list = [NoRedirect(), CheckedHTTPSHandler(context=context), CheckedHTTPHandler()]
    if direct:  # never via an environment proxy
        handlers.append(urllib.request.ProxyHandler({}))
    return urllib.request.build_opener(*handlers)
