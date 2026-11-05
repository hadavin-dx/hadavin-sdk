"""The address guard of `guard.http`: one documented metadata deny table built from numbers, and what `_refused` and
`checked_connection` do with every kind of address (metadata, embedded IPv4 forms, special ranges, allowed private ranges).

The refusal tests are characterization tests: `_refused` and `checked_connection` behave as before this change, and they pin
that. What the change adds is the table, and the tests that name it (table equality, built from numbers, per-row checks)."""

from __future__ import annotations

import ast
import ipaddress
import re
import socket
from pathlib import Path

import pytest

from hadavin_sdk.guard import http
from hadavin_sdk.guard.egress import EgressRefused

# The independent check of the table: the six addresses as text, copied from the earlier reviewed version of the module
# (the former `_METADATA` set of `guard/http.py`, before this change). The module now holds them as numbers.
EXPECTED = {
    "169.254.169.254",
    "100.100.100.200",
    "192.0.0.192",
    "fd00:ec2::254",
    "168.63.129.16",
    "fd20:ce::254",
}
PUBLIC_V4 = ["93.184.216.34", "1.1.1.1", "8.8.8.8"]
PUBLIC_V6 = ["2606:4700:4700::1111", "2001:4860:4860::8888"]
SOURCE = Path(http.__file__)


def _v4(text: str) -> ipaddress.IPv4Address:
    return ipaddress.IPv4Address(text)


def _sixtofour(v4: str) -> ipaddress.IPv6Address:
    return ipaddress.IPv6Address(b"\x20\x02" + _v4(v4).packed + b"\x00" * 10)


def _teredo(server: str, client: str) -> ipaddress.IPv6Address:
    """2001:0::/32, the server, flags and port, then the client with every bit flipped (that is how Teredo writes it)."""
    flipped = bytes(b ^ 0xFF for b in _v4(client).packed)
    return ipaddress.IPv6Address(
        b"\x20\x01\x00\x00" + _v4(server).packed + b"\x00\x00\x00\x00" + flipped
    )


def _nat64(prefix: bytes, v4: str) -> ipaddress.IPv6Address:
    return ipaddress.IPv6Address((prefix + b"\x00" * 16)[:12] + _v4(v4).packed)


# ---- the table -------------------------------------------------------------------------------------------------


def test_the_table_is_documented_and_equals_the_independent_copy():
    assert {str(e.address) for e in http.METADATA_ENDPOINTS} == EXPECTED
    assert len(http.METADATA_ENDPOINTS) == len(EXPECTED)  # no duplicate row
    for entry in http.METADATA_ENDPOINTS:
        assert (
            len(entry.provider) > 20 and len(entry.why) > 10
        )  # who serves it and why it is refused
    assert http._METADATA == frozenset(e.address for e in http.METADATA_ENDPOINTS)


def test_the_ranges_are_built_from_numbers_and_are_the_documented_ones():
    assert http._BENCHMARK == ipaddress.ip_network("198.18.0.0/15")
    assert http._THIS_NETWORK == ipaddress.ip_network("0.0.0.0/8")
    assert http._NAT64 == ipaddress.ip_network("64:ff9b::/96")
    assert http._NAT64_LOCAL == ipaddress.ip_network("64:ff9b:1::/48")


def _string_constants(source: str) -> list[ast.Constant]:
    tree = ast.parse(source)
    doc_nodes = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                doc_nodes.add(id(body[0].value))
    return [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc_nodes
    ]


def test_the_module_text_holds_no_ip_address_literal():
    # a deny list written as numbers: no dotted or colon address (or network with a prefix) is a string in the code
    # (SonarCloud rule S1313). Comments are not code; the loopback NAMES of LOOPBACK are not a deny list.
    v4 = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}(?:/\d+)?")
    v6 = re.compile(
        r"[0-9a-fA-F:]*::[0-9a-fA-F:]*(?:/\d+)?|(?:[0-9a-fA-F]{1,4}:){3,7}[0-9a-fA-F]{1,4}(?:/\d+)?"
    )
    found = [
        n.value
        for n in _string_constants(SOURCE.read_text(encoding="utf-8"))
        if (v4.search(n.value) or v6.search(n.value)) and n.value not in {"::1", "127.0.0.1"}
    ]
    assert found == [], found
    # the checker sees what it must: a prefixed IPv6 network and a dotted address are both caught
    for sample in (
        "64:ff9b::/96",
        "64:ff9b:1::/48",
        "198.18.0.0/15",
        "fd00:ec2::254",
        "169.254.169.254",
    ):
        assert v4.search(sample) or v6.search(sample), sample


VENDOR_WORDS = re.compile(
    r"(?<![A-Za-z0-9])(slack|teams|aws|azure|gcp|github|gitlab|bedrock|anthropic|vertex|gemini|openai|kms|s3|foundry"
    r"|google|alibaba|oracle|amazon|microsoft|digitalocean|openstack)(?![A-Za-z0-9])",
    re.IGNORECASE,
)  # not \b: that treats `_` as part of a word, and `aws_region` would pass


def test_the_vendor_words_check_sees_a_name_inside_an_identifier_and_ignores_a_word_that_only_contains_one():
    for text in (
        "aws_region",
        "AWS",
        "my-azure",
        "x.google.com",
        "the_gcp_zone",
        "Slack:",
        "s3://b",
        "KMS key",
    ):
        assert VENDOR_WORDS.search(text), text
    for text in ("laws", "teamsters", "awsome", "this s3rver", "none of these"):
        assert not VENDOR_WORDS.search(text), text


def test_the_table_names_no_vendor_in_any_string():
    # the lock-in rule: core logic names no vendor. The vendor names sit in comments (the scan skips comments).
    words = VENDOR_WORDS
    strings = [n.value for n in _string_constants(SOURCE.read_text(encoding="utf-8"))]
    assert [s for s in strings if words.search(s)] == []
    try:  # also the real guard's patterns, where this test file sits beside it (not in a mutation copy)
        from tests.test_lockin_guard import PATTERNS
    except ModuleNotFoundError as exc:
        if exc.name not in ("tests", "tests.test_lockin_guard"):
            raise  # a missing module INSIDE the guard file is a real failure, not a mutation copy
        pytest.skip("tests.test_lockin_guard is not importable here (a mutation copy)")
    hits = [
        (label, s)
        for s in strings
        for label, pattern in PATTERNS.items()
        if label != "bare vendor name" and re.search(pattern, s, re.IGNORECASE)
    ]
    assert hits == []


# ---- every metadata address, in every form ------------------------------------------------------------------------


@pytest.mark.parametrize("address", sorted(EXPECTED))
def test_each_metadata_address_is_refused(address):
    assert http._refused(ipaddress.ip_address(address))


MAPPED_REFUSED = sorted(a for a in EXPECTED if "." in a) + [
    "198.19.1.1",
    "0.5.5.5",
    "127.0.0.1",
    "169.254.1.1",
]
MAPPED_ALLOWED = [*PUBLIC_V4, "10.0.0.1", "100.64.0.1", "172.16.5.5", "192.168.1.1"]


@pytest.fixture
def v6_flags_off(monkeypatch):
    """The standard library's own IPv6 flags answer False, so only the guard's explicit rules can refuse an address. Whether
    `::ffff:0:0/96` counts as reserved there differs between Python versions; with the flags off the test does not depend on it."""
    for name in ("is_reserved", "is_loopback", "is_link_local", "is_unspecified", "is_multicast"):
        monkeypatch.setattr(ipaddress.IPv6Address, name, property(lambda self: False))


@pytest.mark.parametrize("address", MAPPED_REFUSED)
def test_an_ipv4_mapped_form_of_a_refused_address_is_refused(address, v6_flags_off):
    mapped = ipaddress.ip_address("::ffff:" + address)
    assert mapped.ipv4_mapped == _v4(address) and http._refused(_v4(address))
    assert http._refused(mapped)  # only the embedded-address rule can refuse it here


@pytest.mark.parametrize("address", MAPPED_ALLOWED)
def test_an_ipv4_mapped_form_of_an_allowed_address_is_allowed_by_the_guards_own_rules(
    address, v6_flags_off
):
    mapped = ipaddress.ip_address("::ffff:" + address)
    assert mapped.ipv4_mapped == _v4(address) and not http._refused(_v4(address))
    assert not http._refused(
        mapped
    )  # negative control: the rule above is not "refuse every mapped address"


@pytest.mark.parametrize("address", MAPPED_REFUSED + MAPPED_ALLOWED)
def test_with_the_real_standard_library_a_mapped_address_is_never_allowed_when_its_embedded_one_is_refused(
    address,
):
    mapped = ipaddress.ip_address("::ffff:" + address)
    if http._refused(_v4(address)):
        assert http._refused(mapped)  # on every Python version
    # an allowed embedded address may still be refused where the standard library reserves the whole mapped range (fail closed)


@pytest.mark.parametrize("address", sorted(a for a in EXPECTED if "." in a))
def test_a_6to4_form_of_a_metadata_address_is_refused(address):
    assert http._refused(_sixtofour(address))
    assert not http._refused(_sixtofour(PUBLIC_V4[0]))  # negative control


@pytest.mark.parametrize("address", sorted(a for a in EXPECTED if "." in a))
def test_a_teredo_address_whose_server_is_a_metadata_address_is_refused(address):
    # the CLIENT is a public address, so only the server path can refuse it
    ip = _teredo(address, PUBLIC_V4[2])
    assert ip.teredo == (_v4(address), _v4(PUBLIC_V4[2]))
    assert not http._refused(ipaddress.ip_address(PUBLIC_V4[2]))
    assert http._refused(ip)


@pytest.mark.parametrize("address", sorted(a for a in EXPECTED if "." in a))
def test_a_teredo_address_whose_client_is_a_metadata_address_is_refused(address):
    # the SERVER is a public address, so only the client path can refuse it
    ip = _teredo(PUBLIC_V4[0], address)
    assert ip.teredo == (_v4(PUBLIC_V4[0]), _v4(address))
    assert http._refused(ip)


def test_a_teredo_address_with_a_public_server_and_a_public_client_is_allowed():
    ip = _teredo(PUBLIC_V4[0], PUBLIC_V4[2])
    assert ip.teredo == (_v4(PUBLIC_V4[0]), _v4(PUBLIC_V4[2]))
    assert not http._refused(
        ip
    )  # negative control: the checks above are not true for every Teredo address


@pytest.mark.parametrize("prefix", [b"\x00\x64\xff\x9b", b"\x00\x64\xff\x9b\x00\x01"])
def test_a_nat64_address_is_refused_whatever_it_embeds(prefix, v6_flags_off):
    # the prefix is refused whole by the guard's own explicit rule, so the standard library's flags are switched off here
    # (it also reserves the range, which would hide a deleted rule): even a public embedded address
    assert http._refused(_nat64(prefix, PUBLIC_V4[0]))
    assert http._refused(_nat64(prefix, "169.254.169.254"))


# ---- the special ranges and what stays allowed -----------------------------------------------------------------------


@pytest.mark.parametrize("address", ["198.18.0.0", "198.18.5.5", "198.19.1.1", "198.19.255.255"])
def test_the_benchmarking_range_is_refused_to_its_last_address(address):
    assert http._refused(ipaddress.ip_address(address))


@pytest.mark.parametrize("address", ["198.17.255.255", "198.20.0.0"])
def test_the_addresses_next_to_the_benchmarking_range_are_allowed(address):
    assert not http._refused(ipaddress.ip_address(address))


@pytest.mark.parametrize("address", ["0.0.0.0", "0.5.5.5", "0.255.255.255"])  # noqa: S104 - the refused address, not a bind
def test_this_network_is_refused(address):
    assert http._refused(ipaddress.ip_address(address))
    assert not http._refused(ipaddress.ip_address("1.0.0.0"))  # the first address after it


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1", "127.5.5.5", "::1",  # loopback
        "169.254.0.1", "169.254.169.253", "fe80::1",  # link-local
        "::",  # unspecified
        "224.0.0.1", "239.255.255.255", "ff02::1",  # multicast
        "240.0.0.1",  # reserved
    ],
)  # fmt: skip
def test_loopback_link_local_unspecified_multicast_and_reserved_addresses_are_refused(address):
    assert http._refused(ipaddress.ip_address(address))


@pytest.mark.parametrize(
    "address",
    [
        "100.64.0.1", "100.127.255.254",  # carrier-grade NAT: in-cluster services, allowed on purpose
        "10.0.0.1", "172.16.5.5", "192.168.1.1",  # RFC 1918
        "fc00::1", "fd12:3456::1",  # unique-local IPv6
        "100.100.100.201", "168.63.129.17", "192.0.0.193", "fd00:ec2::255",  # next to a metadata address: only the exact address is refused
    ],
)  # fmt: skip
def test_private_ranges_and_the_neighbours_of_metadata_addresses_are_allowed(address):
    assert not http._refused(ipaddress.ip_address(address))


@pytest.mark.parametrize("address", PUBLIC_V4 + PUBLIC_V6)
def test_an_ordinary_public_address_passes(address):
    assert not http._refused(ipaddress.ip_address(address))


# ---- checked_connection --------------------------------------------------------------------------------------------


def _answers(*addresses):
    return [
        (socket.AF_INET6 if ":" in a else socket.AF_INET, socket.SOCK_STREAM, 6, "", (a, 80))
        for a in addresses
    ]


def _no_connection(monkeypatch):
    """Record every connection attempt (a list the test asserts is empty), so a mistake shows as an AssertionError."""
    connected: list = []
    monkeypatch.setattr(
        socket, "create_connection", lambda addr, *a, **k: connected.append(addr) or "connected"
    )
    return connected


@pytest.mark.parametrize("address", sorted(EXPECTED))
def test_a_name_that_resolves_to_a_metadata_address_is_refused_before_any_connection(
    address, monkeypatch
):
    monkeypatch.setattr(http, "_resolve", lambda host, port: _answers(address))
    connected = _no_connection(monkeypatch)
    with pytest.raises(EgressRefused):
        http.checked_connection(("service.example", 80))
    assert connected == []


def test_one_public_answer_among_metadata_answers_still_refuses_the_whole_name(monkeypatch):
    monkeypatch.setattr(
        http, "_resolve", lambda host, port: _answers(PUBLIC_V4[0], "169.254.169.254")
    )
    connected = _no_connection(monkeypatch)
    with pytest.raises(EgressRefused):
        http.checked_connection(("service.example", 80))
    assert connected == []


def test_a_public_answer_is_connected_to(monkeypatch):
    monkeypatch.setattr(http, "_resolve", lambda host, port: _answers(PUBLIC_V4[0]))
    seen = []
    monkeypatch.setattr(
        socket, "create_connection", lambda addr, *a, **k: seen.append(addr) or "ok"
    )
    assert http.checked_connection(("service.example", 80)) == "ok"
    assert seen == [(PUBLIC_V4[0], 80)]


@pytest.mark.parametrize("zone", ["%eth0", "%2"])
def test_an_ipv6_zone_id_does_not_hide_the_address(zone, monkeypatch):
    # getaddrinfo can answer `fe80::1%eth0`; an address with its zone is a different object, so the zone is cut first
    for address in ("fd00:ec2::254", "fe80::1"):
        monkeypatch.setattr(http, "_resolve", lambda host, port, a=address + zone: _answers(a))
        connected = _no_connection(monkeypatch)
        with pytest.raises(EgressRefused):
            http.checked_connection(("service.example", 80))
        assert connected == []


def test_a_trailing_dot_name_is_resolved_and_checked_like_any_name(monkeypatch):
    seen = []
    monkeypatch.setattr(
        http, "_resolve", lambda host, port: seen.append(host) or _answers("169.254.169.254")
    )
    connected = _no_connection(monkeypatch)
    with pytest.raises(EgressRefused):
        http.checked_connection(("metadata.example.", 80))
    assert connected == []
    assert seen == ["metadata.example."]


def test_an_explicit_loopback_name_is_connected_as_written_even_with_a_dot_or_capitals(monkeypatch):
    connected = []
    monkeypatch.setattr(
        socket, "create_connection", lambda addr, *a, **k: connected.append(addr) or "ok"
    )
    monkeypatch.setattr(
        http, "_resolve", lambda *a: pytest.fail("a loopback name is not looked up")
    )
    for host in ("localhost", "LOCALHOST.", "127.0.0.1", "::1"):
        assert http.checked_connection((host, 80)) == "ok"
    assert [h for h, _ in connected] == ["localhost", "LOCALHOST.", "127.0.0.1", "::1"]


@pytest.mark.parametrize(
    "host", ["2852039166", "0xa9fea9fe", "0251.0376.0251.0376", "169.254.169.254"]
)
def test_a_decimal_hex_or_octal_spelling_of_the_address_is_refused_as_the_system_reads_it(host):
    try:
        socket.getaddrinfo(host, 80, type=socket.SOCK_STREAM)
    except OSError:
        pytest.skip("this system's resolver does not read this spelling as an address")
    with pytest.raises(EgressRefused):
        http.checked_connection((host, 80))
