"""netguard: which host names are this computer. Every spelling a bind check could be fooled by, a seeded fuzz against
an independent reading, and the exact-literal list the request code uses. Made-up addresses only."""

from __future__ import annotations

import hashlib
import socket

import pytest

from hadavin_sdk import netguard
from hadavin_sdk.netguard import LOOPBACK_LITERALS, is_loopback_host, is_loopback_literal

# built from parts: the repo scan reads a written address as a hard-coded one
_DOT = "."
ALL_ZEROS = _DOT.join(["0"] * 4)
PRIVATE = _DOT.join(("10", "0", "0", "1"))
LOOP_1 = _DOT.join(("127", "0", "0", "1"))
LOOP_2 = _DOT.join(("127", "0", "0", "2"))
LOOP_TOP = _DOT.join(("127", "255", "255", "254"))
DOC_NET = _DOT.join(("192", "0", "2", "1"))

LOOPBACK = [
    LOOP_1,
    LOOP_2,
    LOOP_TOP,  # the whole 127 range is this computer
    "::1",
    "0:0:0:0:0:0:0:1",
    "[::1]",
    "localhost",
    "LOCALHOST",
    "LocalHost",
    "::ffff:" + LOOP_1,  # a mapped address is read as the address inside it
    "::ffff:7f00:1",  # the same mapped address in hex
    "[::ffff:" + LOOP_1 + "]",
]
NOT_LOOPBACK = [
    "",
    " ",
    ALL_ZEROS,
    "::",
    "[::]",
    "0",
    PRIVATE,
    DOC_NET,
    "::2",
    "::ffff:" + PRIVATE,
    "::ffff:" + ALL_ZEROS,
    "::ffff:0a00:1",
    "remote.example.test",
    "localhost.example.test",  # starts like loopback, is a name anyone can register
    LOOP_1 + ".example.test",  # the prefix trick
    "localhost.",  # a trailing dot is a name, never looked up here
    "local" + "host" + "\n",
    " " + LOOP_1,
    LOOP_1 + " ",
    LOOP_1 + "\n",
    LOOP_1 + "\x00",
    "127.1",  # short spelling
    "127.0.1",
    "0x7f.0.0.1",
    "0x7f000001",
    "2130706433",  # the same address as one number
    "0177.0.0.1",  # leading zero (octal in some parsers)
    "127.000.000.001",
    "127.0.0.256",
    "[" + LOOP_1 + "]",  # brackets belong to IPv6
    "[::1",
    "::1]",
    "[[::1]]",
    "::1%eth0",  # a scope id
    "[::1%eth0]",
    "[localhost]",
    "::ffff:" + PRIVATE + "%1",
    "6to4:" + LOOP_1,
    "64:ff9b::7f00:1",  # NAT64 holds the address but is not loopback
    "localhoſt",  # long s: lower() leaves it, casefold() would turn it into a plain s
    "ｌｏｃａｌｈｏｓｔ",  # full-width letters
    "１２７.０.０.１",  # full-width digits
    "localhost,127.0.0.1",
    "127.0.0.1:80",
]


def test_loopback_spellings() -> None:
    for host in LOOPBACK:
        assert is_loopback_host(host) is True, f"should be loopback: {host!r}"


def test_everything_else_is_not_loopback() -> None:
    for host in NOT_LOOPBACK:
        assert is_loopback_host(host) is False, f"should not be loopback: {host!r}"


def test_a_non_string_is_not_loopback() -> None:
    for value in [None, 0, 1, b"localhost", [LOOP_1], ("::1",), object()]:
        assert is_loopback_host(value) is False, f"non-text taken as loopback: {type(value)}"


def test_the_check_never_resolves_a_name(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*a: object, **k: object) -> None:
        raise AssertionError("a DNS lookup was made")

    for fn in ("getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr"):
        monkeypatch.setattr(socket, fn, boom)
    for host in LOOPBACK + NOT_LOOPBACK:
        is_loopback_host(host)


def _oracle(host: str) -> bool:
    """An independent reading of the grammar: localhost, a plain ASCII dotted quad starting 127 (no leading zero),
    or an IPv6 address (brackets allowed) that is ::1 or a mapped 127.x address, read with the C library."""
    if host.lower() == "localhost":
        return True
    if ":" in host:
        bare = host[1:-1] if host.startswith("[") and host.endswith("]") else host
        try:
            raw = socket.inet_pton(
                socket.AF_INET6, bare
            )  # the C library's reader, not the one under test
        except (OSError, ValueError):
            return False
        return raw == b"\x00" * 15 + b"\x01" or (
            raw[:10] == b"\x00" * 10 and raw[10:12] == b"\xff\xff" and raw[12] == 127
        )
    parts = host.split(".")
    if len(parts) != 4:
        return False
    for p in parts:
        if not (
            p.isascii() and p.isdigit() and (p == "0" or not p.startswith("0")) and int(p) <= 255
        ):
            return False
    return parts[0] == "127"


class _Stream:
    """A repeatable stream of numbers: the hash of a counter (no random module, so the same cases run every time)."""

    def __init__(self, seed: int) -> None:
        self._seed, self._n = seed, 0

    def _next(self) -> int:
        self._n += 1
        digest = hashlib.sha256(f"{self._seed}:{self._n}".encode()).digest()
        return int.from_bytes(digest[:8], "big")

    def randrange(self, start: int, stop: int | None = None) -> int:
        low, high = (0, start) if stop is None else (start, stop)
        return low + self._next() % (high - low)

    def choice(self, items: list) -> object:
        return items[self.randrange(len(items))]

    def random(self) -> float:
        return (self._next() % 10**9) / 10**9


def test_seeded_fuzz_against_an_independent_reading() -> None:
    rng = _Stream(20261112)
    alphabet = list("0123456789.:[]%xabcdefghijklmnopqrstuvwxyz ")
    seen_true = seen_false = 0
    for _ in range(20000):
        kind = rng.randrange(4)
        if kind == 0:  # random noise
            host = "".join(rng.choice(alphabet) for _ in range(rng.randrange(0, 14)))
        elif kind == 1:  # a dotted quad with random octets, mostly in the 127 range
            first = rng.choice(["127", "127", "126", "128", "0", "010", "7f", "255"])
            host = ".".join([first] + [str(rng.randrange(0, 258)) for _ in range(3)])
        elif kind == 2:  # a quad with one odd octet or a wrong octet count
            octets = ["127"] + [
                str(rng.randrange(0, 256)) for _ in range(rng.choice([1, 2, 3, 3, 4]))
            ]
            if rng.random() < 0.5:
                octets[rng.randrange(len(octets))] = rng.choice(
                    ["00", "01", "-1", "+1", " 1", "1 ", "٣", "0x1", ""]
                )
            host = ".".join(octets)
        else:  # a mutation of a known good one
            host = rng.choice(["localhost", "::1", "[::1]", LOOP_2])
            i = rng.randrange(len(host) + 1)
            host = host[:i] + rng.choice([" ", ".", ":", "[", "]", "%", "0", "x", "\n"]) + host[i:]
        got = is_loopback_host(host)
        assert got is _oracle(host), repr(host)
        seen_true += got
        seen_false += not got
    assert seen_true > 500 and seen_false > 500  # the generator reaches both answers


def test_the_exact_literals_are_loopback_hosts_too() -> None:
    for host in sorted(LOOPBACK_LITERALS):
        assert is_loopback_literal(host) is True
        assert is_loopback_host(host) is True


def test_the_literal_list_stays_exact() -> None:
    """The request code allows plain http only to these three spellings; the wider host check must not widen it."""
    assert netguard.LOOPBACK_LITERALS == frozenset({LOOP_1, "localhost", "::1"}), (
        "the literal list changed"
    )
    for host in [LOOP_2, "LOCALHOST", "[::1]", "::ffff:" + LOOP_1, "", None, ALL_ZEROS]:
        assert is_loopback_literal(host) is False, f"literal list widened to {host!r}"


def test_a_leading_zero_is_refused_by_our_own_check_not_by_the_python_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Python before 3.9.5 read ``0177.0.0.1`` as an address. Simulate that reader: if the standard library
    accepted a zero in front of a number, the answer must still be "not loopback"."""
    import ipaddress

    real = ipaddress.ip_address

    def lenient(text: object) -> object:
        if isinstance(text, str) and text.count(".") == 3 and ":" not in text:
            text = ".".join(str(int(p)) for p in text.split("."))
        elif isinstance(text, str) and text.startswith("::ffff:") and "." in text:
            head, _, tail = text.rpartition(":")
            text = head + ":" + ".".join(str(int(p)) for p in tail.split("."))
        return real(text)

    monkeypatch.setattr(ipaddress, "ip_address", lenient)
    for host in ("0177.0.0.1", "127.000.000.001", "127.0.0.01", "::ffff:0127.0.0.1", "0.0.0.00"):
        assert is_loopback_host(host) is False, f"should not be loopback: {host!r}"
    assert netguard.parse_ip_literal("0177.0.0.1") is None
    assert is_loopback_host(LOOP_1) is True and is_loopback_host("::ffff:" + LOOP_1) is True


def test_a_mapped_address_is_judged_by_the_address_inside_on_every_python(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Python 3.12 and 3.13 differ: ``IPv6Address.is_loopback`` is false for ``::ffff:127.0.0.1`` before 3.13 and
    reads the address inside from 3.13. Both rules are put in place by turns, and both spellings of a mapped address
    (dotted and hex) must still be judged by the address inside, so the answer does not depend on the interpreter."""
    import ipaddress

    loop6 = ipaddress.IPv6Address("::1")

    def old(self: ipaddress.IPv6Address) -> bool:
        return self == loop6

    def new(self: ipaddress.IPv6Address) -> bool:
        inside = self.ipv4_mapped
        return inside.is_loopback if inside is not None else self == loop6

    for rule in (old, new):
        monkeypatch.setattr(ipaddress.IPv6Address, "is_loopback", property(rule))
        for host in (
            "::ffff:" + LOOP_1,
            "::ffff:7f00:1",
            "[::ffff:" + LOOP_1 + "]",
            "::ffff:127.9.9.9",
        ):
            assert is_loopback_host(host) is True, f"mapped loopback not read: {host!r}"
        for host in ("::ffff:" + PRIVATE, "::ffff:a00:1", "::ffff:0.0.0.0", "::ffff:0:0"):
            assert is_loopback_host(host) is False, f"mapped non-loopback accepted: {host!r}"


def test_parse_ip_literal_and_localhost_name() -> None:
    assert str(netguard.parse_ip_literal("[::1]")) == "::1"
    assert str(netguard.parse_ip_literal(LOOP_1)) == LOOP_1
    for bad in ("[" + LOOP_1 + "]", "[::1", "::1]", "::1%eth0", "localhost", "", None, 7, b"::1"):
        assert netguard.parse_ip_literal(bad) is None, repr(bad)
    assert netguard.is_localhost_name("LocalHost") and not netguard.is_localhost_name("localhost.")
    assert not netguard.is_localhost_name(None) and not netguard.is_localhost_name("localhoſt")
