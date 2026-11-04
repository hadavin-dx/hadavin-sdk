"""The metadata-service deny list of `guard.http`: one documented table, built once from numbers, and every address in it
(and every form of it the guard handles) is refused, while an ordinary public address passes."""

from __future__ import annotations

import ipaddress
import socket
from pathlib import Path

import pytest

from hadavin_sdk.guard import http
from hadavin_sdk.guard.egress import EgressRefused

# The same six addresses the module documents, spelled as text only HERE (the test is the independent check of the table).
EXPECTED = {
    "169.254.169.254",
    "100.100.100.200",
    "192.0.0.192",
    "fd00:ec2::254",
    "168.63.129.16",
    "fd20:ce::254",
}
PUBLIC = ["93.184.216.34", "1.1.1.1", "2606:4700:4700::1111", "8.8.8.8"]


def test_the_table_is_documented_and_equals_the_expected_set():
    assert {str(e.address) for e in http.METADATA_ENDPOINTS} == EXPECTED
    assert len(http.METADATA_ENDPOINTS) == len(EXPECTED)  # no duplicate row
    for entry in http.METADATA_ENDPOINTS:
        assert entry.provider.strip() and len(entry.why) > 20  # who runs it and why it is refused
    assert http._METADATA == frozenset(e.address for e in http.METADATA_ENDPOINTS)


def test_the_networks_are_built_from_numbers_and_are_the_documented_ranges():
    assert http._BENCHMARK == ipaddress.ip_network("198.18.0.0/15")
    assert http._THIS_NETWORK == ipaddress.ip_network("0.0.0.0/8")


def test_the_module_text_holds_no_ip_address_literal():
    # a deny list written as numbers: the dotted text of an address never appears in the source (SonarCloud rule S1313)
    import re

    source = Path(http.__file__).read_text(encoding="utf-8")
    code = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("#"))
    literal = re.compile(
        r"[\"'](?:\d{1,3}\.){3}\d{1,3}(?:/\d+)?[\"']|[\"'][0-9a-fA-F:]*::[0-9a-fA-F:]*[\"']"
    )
    found = [
        m.group(0)
        for m in literal.finditer(code)
        if m.group(0).strip("\"'") not in {"::1", "127.0.0.1"}
    ]  # the loopback names of LOOPBACK are not a deny list
    assert found == [], found


@pytest.mark.parametrize("address", sorted(EXPECTED))
def test_each_metadata_address_is_refused_in_every_form_the_guard_handles(address):
    ip = ipaddress.ip_address(address)
    assert http._refused(ip)
    if ip.version == 4:
        assert http._refused(ipaddress.ip_address("::ffff:" + address))  # IPv4-mapped
        packed = ip.packed
        assert http._refused(ipaddress.ip_address(b"\x20\x02" + packed + b"\x00" * 10))  # 6to4
        nat64 = ipaddress.ip_address(b"\x00\x64\xff\x9b" + b"\x00" * 8 + packed)
        assert http._refused(nat64)  # NAT64 well-known prefix
        teredo = ipaddress.ip_address(
            b"\x20\x01\x00\x00"
            + packed
            + b"\x00\x00\x00\x00"
            + bytes(b ^ 0xFF for b in b"\x00\x00\x00\x01")
        )
        assert http._refused(teredo)  # Teredo carrying it as the server


@pytest.mark.parametrize("address", PUBLIC)
def test_an_ordinary_public_address_passes(address):
    assert not http._refused(ipaddress.ip_address(address))


@pytest.mark.parametrize("address", sorted(EXPECTED))
def test_a_name_that_resolves_to_a_metadata_address_is_refused_before_any_connection(
    address, monkeypatch
):
    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    answers = [(family, socket.SOCK_STREAM, 6, "", (address, 80))]
    monkeypatch.setattr(http, "_resolve", lambda host, port: answers)
    monkeypatch.setattr(
        socket, "create_connection", lambda *a, **k: pytest.fail("connected to a refused address")
    )
    with pytest.raises(EgressRefused):
        http.checked_connection(("service.example", 80))


def test_one_public_answer_among_metadata_answers_still_refuses_the_whole_name(monkeypatch):
    answers = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 80)),
    ]
    monkeypatch.setattr(http, "_resolve", lambda host, port: answers)
    monkeypatch.setattr(
        socket, "create_connection", lambda *a, **k: pytest.fail("connected to a refused address")
    )
    with pytest.raises(EgressRefused):
        http.checked_connection(("service.example", 80))


def test_a_public_answer_is_connected_to(monkeypatch):
    answers = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))]
    monkeypatch.setattr(http, "_resolve", lambda host, port: answers)
    seen = []
    monkeypatch.setattr(
        socket, "create_connection", lambda addr, *a, **k: seen.append(addr) or "ok"
    )
    assert http.checked_connection(("service.example", 80)) == "ok"
    assert seen == [("93.184.216.34", 80)]


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
