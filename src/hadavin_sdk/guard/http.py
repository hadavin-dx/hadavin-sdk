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
from dataclasses import dataclass

from hadavin_sdk.guard.egress import EgressRefused, normalise_host
from hadavin_sdk.netguard import LOOPBACK_LITERALS

LOOPBACK = LOOPBACK_LITERALS  # the one list lives in netguard


def _v4(*octets: int) -> ipaddress.IPv4Address:
    """An IPv4 address from its four numbers (the table below is read as numbers, not as dotted text)."""
    return ipaddress.IPv4Address(bytes(octets))


def _v6(*hextets: int) -> ipaddress.IPv6Address:
    """An IPv6 address from its eight 16-bit groups."""
    return ipaddress.IPv6Address(b"".join(h.to_bytes(2, "big") for h in hextets))


@dataclass(frozen=True)
class MetadataEndpoint:
    """One address a platform serves its instance-metadata service on. The notes are vendor-neutral on purpose (no
    vendor name in a string); the comments beside each row say which platform it is."""

    address: ipaddress.IPv4Address | ipaddress.IPv6Address
    provider: str
    why: str  # why a request there is refused


# DENY LIST, on purpose: these addresses are private or link-local, so a plain "is it public" check would let them through,
# and a request to one hands out the credentials of the machine it runs on (the classic server-side request forgery
# target). The numbers are written as numbers; no address appears in a string in the code (a few comments show one, for the reader).
METADATA_ENDPOINTS: tuple[MetadataEndpoint, ...] = (
    MetadataEndpoint(  # AWS, Azure, Google Cloud, OpenStack, DigitalOcean and others
        _v4(169, 254, 169, 254),
        "link-local metadata address shared by most clouds",
        "instance credentials and identity tokens",
    ),
    MetadataEndpoint(  # Alibaba Cloud
        _v4(100, 100, 100, 200),
        "carrier-grade-NAT address used by one provider",
        "instance role credentials",
    ),
    MetadataEndpoint(  # Oracle Cloud (its older metadata address); the address is inside 192.0.0.0/24, the IETF protocol assignments
        _v4(192, 0, 0, 192),
        "address inside the IETF protocol-assignments range (a /24), used by one provider",
        "instance credentials",
    ),
    MetadataEndpoint(  # AWS over IPv6
        _v6(0xFD00, 0x0EC2, 0, 0, 0, 0, 0, 0x0254),
        "IPv6 unique-local metadata address of one provider",
        "instance credentials and identity tokens",
    ),
    MetadataEndpoint(  # Azure (the virtual public IP of the host)
        _v4(168, 63, 129, 16),
        "public-looking address one provider serves to its own virtual machines only",
        "host services for the machine: provisioning data and extension secrets",
    ),
    MetadataEndpoint(  # Google Cloud over IPv6
        _v6(0xFD20, 0x00CE, 0, 0, 0, 0, 0, 0x0254),
        "IPv6 unique-local metadata address of one provider",
        "instance credentials and identity tokens",
    ),
)
_METADATA = frozenset(e.address for e in METADATA_ENDPOINTS)
# Reserved for benchmarking (RFC 2544), never a public service a tool should call.
_BENCHMARK = ipaddress.IPv4Network((bytes((198, 18, 0, 0)), 15))
# 0.0.0.0 reaches the local host on Linux; the whole /8 is not a routable destination.
_THIS_NETWORK = ipaddress.IPv4Network((bytes((0, 0, 0, 0)), 8))
# 100.64.0.0/10 (carrier-grade NAT, where some clouds and VPNs put in-cluster services) is allowed on purpose,
# like the other private ranges; the manifest host allowlist bounds what a tool may name.
# NAT64 (the well-known prefix) is refused whole by an explicit rule here, so the refusal does not depend on the
# standard library (which also refuses it today, because the whole range is reserved there): an IPv6-only cluster
# behind DNS64/NAT64 cannot use the in-process fetch and needs the egress proxy (K7) instead.
_NAT64 = ipaddress.IPv6Network((_v6(0x64, 0xFF9B, 0, 0, 0, 0, 0, 0), 96))
# the local-use NAT64 prefix (RFC 8215): refused whole
_NAT64_LOCAL = ipaddress.IPv6Network((_v6(0x64, 0xFF9B, 1, 0, 0, 0, 0, 0), 48))
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
    """Resolve the host ONCE, refuse it if any answer is loopback, link-local, unspecified, multicast, reserved, a
    cloud metadata address (METADATA_ENDPOINTS), in the benchmarking range or "this network", NAT64, or an IPv6 form that
    carries one of these (IPv4-mapped, 6to4, Teredo), and connect to a checked address. The name is looked up exactly once, so
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
