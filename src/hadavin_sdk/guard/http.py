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
import threading
import urllib.request

from hadavin_sdk.guard.egress import EgressRefused, normalise_host

LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})


# Addresses that name a cloud's metadata service (they are private or link-local, and a request there hands out
# credentials). The AWS one over IPv6 is `fd00:ec2::254`.
_METADATA = frozenset(
    ipaddress.ip_address(a)
    for a in (
        "169.254.169.254",
        "100.100.100.200",
        "192.0.0.192",
        "fd00:ec2::254",
        "168.63.129.16",
        "fd20:ce::254",
    )
)
_BENCHMARK = ipaddress.ip_network("198.18.0.0/15")
_THIS_NETWORK = ipaddress.ip_network(
    "0.0.0.0/8"
)  # "this host on this network": Linux connects it to the local host
# 100.64.0.0/10 (carrier-grade NAT, where some clouds and VPNs put in-cluster services) is allowed on purpose,
# like the other private ranges; the manifest host allowlist bounds what a tool may name.
# NAT64 (the well-known prefix) is refused whole, by this rule and not by the standard library's flags (which differ
# between Python versions): an IPv6-only cluster behind DNS64/NAT64 cannot use the in-process fetch and needs the
# egress proxy (K7) instead.
_NAT64 = ipaddress.ip_network("64:ff9b::/96")
_NAT64_LOCAL = ipaddress.ip_network(
    "64:ff9b:1::/48"
)  # the local-use NAT64 prefix (RFC 8215): refused whole
# One budget for the whole process: the read tools, the LLM clients and the executor share it. During a real DNS
# outage 8 stuck lookups refuse every new outbound name lookup until the resolver gives up (fail closed, and
# self-healing: a permit comes back when its thread ends).
MAX_STUCK_LOOKUPS = 8
_STUCK = threading.BoundedSemaphore(MAX_STUCK_LOOKUPS)
RESOLVE_TIMEOUT_S = (
    5.0  # a name lookup that takes longer is refused (getaddrinfo has no timeout of its own)
)


def _refused(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Loopback, link-local, unspecified, multicast, reserved, a metadata address, or an IPv6 form that carries
    one (IPv4-mapped, 6to4, Teredo, NAT64)."""
    if ip in _METADATA or (ip.version == 4 and (ip in _BENCHMARK or ip in _THIS_NETWORK)):
        return True
    if ip.is_loopback or ip.is_link_local or ip.is_unspecified or ip.is_multicast or ip.is_reserved:
        return True
    if ip.version == 6:
        embedded = [ip.ipv4_mapped, ip.sixtofour]
        if ip.teredo:
            embedded += list(ip.teredo)
        if ip in _NAT64 or ip in _NAT64_LOCAL:
            return True
        return any(e is not None and _refused(e) for e in embedded)
    return False


def _resolve(host: str, port: int):
    """getaddrinfo with a timeout. getaddrinfo cannot be cancelled, so a lookup that times out leaves its thread
    running until the resolver gives up: at most MAX_STUCK_LOOKUPS such threads exist, then lookups are refused
    (a flood of hostile names that never answer cannot pile up threads)."""
    box: dict = {}
    if not _STUCK.acquire(blocking=False):
        raise OSError(f"{host}: too many name lookups are stuck")

    def lookup() -> None:
        try:
            box["answers"] = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except BaseException as exc:  # noqa: BLE001 - handed to the caller
            box["error"] = exc
        finally:
            _STUCK.release()  # the thread is over, whether or not anybody still waits for it

    worker = threading.Thread(target=lookup, daemon=True, name="hadavin-resolve")
    try:
        worker.start()
    except BaseException:
        _STUCK.release()  # the thread never ran, so nothing else will give the permit back
        raise
    worker.join(RESOLVE_TIMEOUT_S)
    if worker.is_alive():
        raise OSError(f"{host}: the name lookup took more than {RESOLVE_TIMEOUT_S} s")
    if "error" in box:
        raise box["error"]
    return box["answers"]


def checked_connection(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None):
    """Resolve the host ONCE, refuse it if any answer is loopback, link-local (the cloud metadata address),
    unspecified, multicast or reserved, and connect to a checked address. The name is looked up exactly once, so
    a DNS answer that changes between the check and the connect (rebinding) cannot reach the socket; TLS still
    verifies the certificate against the NAME (the connection keeps `host` for SNI). Private ranges are allowed:
    in-cluster services live there. An explicit loopback NAME (127.0.0.1, localhost, ::1) is connected as it is,
    without the address check: that is for tests and local development, and tools cannot name one (a manifest host
    may not be loopback). The LLM clients and the executor use this connection too, so a pilot or prod deployment
    must not point their endpoints at a loopback name."""
    host, port = address
    if normalise_host(host) in LOOPBACK:
        return socket.create_connection(address, timeout, source_address)
    ips: list[str] = []
    for _, _, _, _, sockaddr in _resolve(host, port):
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


# Tools never go through an environment proxy: a proxy resolves the target itself, so the address check and the
# pinned connection below would not apply. The LLM clients and the executor (`ENV_PROXY_OPENER`) may use one.
OPENER = urllib.request.build_opener(
    NoRedirect, urllib.request.ProxyHandler({}), CheckedHTTPHandler, CheckedHTTPSHandler
)
LOCAL_OPENER = OPENER
ENV_PROXY_OPENER = urllib.request.build_opener(NoRedirect, CheckedHTTPHandler, CheckedHTTPSHandler)


def opener_for(context: ssl.SSLContext, direct: bool = False) -> urllib.request.OpenerDirector:
    """An opener that trusts exactly the CAs in `context` (a per-source or per-tool CA bundle), still without
    redirects and with the same resolve-once address check."""
    handlers: list = [
        NoRedirect(),
        urllib.request.ProxyHandler(
            {}
        ),  # never via an environment proxy (it would skip the address check)
        CheckedHTTPSHandler(context=context),
        CheckedHTTPHandler(),
    ]
    return urllib.request.build_opener(*handlers)
