"""The one answer to "is this host name this computer?". A leaf module: it imports only the standard library, so
the settings, the HTTP guard, the model clients and the stores can all ask here instead of each keeping its own list.

Two questions, kept apart on purpose:

* ``is_loopback_host``: the strict reading of a bind address or a host. True only for ``localhost`` (any letter
  case) and a loopback address written as a plain IP address (the whole 127.x.x.x range, ``::1``, and an IPv4-mapped
  IPv6 address that holds a loopback IPv4 address). It never looks a name up, so the answer cannot change with a DNS
  reply. Anything it cannot read is not loopback.
* ``LOOPBACK_LITERALS`` / ``is_loopback_literal``: the three exact spellings a plain-http endpoint may use
  (``127.0.0.1``, ``localhost``, ``::1``). The callers that send a request (the model clients, the HTTP guard, the
  settings checks) need an exact, small list, because a wider list would widen what they allow.
"""

from __future__ import annotations

import ipaddress

LOOPBACK_LITERALS: frozenset[str] = frozenset({"127.0.0.1", "localhost", "::1"})


def is_loopback_literal(host: object) -> bool:
    """True only for the exact spellings in LOOPBACK_LITERALS (no letter-case change, no brackets, no range)."""
    return isinstance(host, str) and host in LOOPBACK_LITERALS


def is_loopback_host(name: object) -> bool:
    """True for ``localhost`` and for a loopback IP address; a wildcard, any other name and any other address
    can be reached from, or reach, other computers. Never resolves a name. Fails closed.

    Refused on purpose (each has a test): a name that only starts like loopback (``127.0.0.1.example.test``,
    ``localhost.example.test``), a trailing dot, white space, short or number-only spellings of an address
    (``127.1``, ``0x7f.0.0.1``, ``2130706433``, ``0177.0.0.1``), brackets round an IPv4 address or an
    unbalanced bracket, a scope id (``::1%eth0``), the wildcard addresses and a mapped address that holds a
    non-loopback IPv4 address. Square brackets round an IPv6 address are accepted (the URL form)."""
    if not isinstance(name, str):
        return False
    # str.lower, not casefold: casefold would also read the long-s letter as "s"
    if name.lower() == "localhost":
        return True
    bare = name
    bracketed = name.startswith("[") and name.endswith("]")
    if bracketed:
        bare = name[1:-1]
    # one bracket only, or a scope id: not a plain address
    if "[" in bare or "]" in bare or "%" in bare:
        return False
    try:
        ip = ipaddress.ip_address(bare)
    except ValueError:
        return False
    if bracketed and ip.version != 6:
        return False  # brackets belong to IPv6 only
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        # read the address inside: the same answer on every Python version (3.13 changed is_loopback for mapped forms)
        ip = ip.ipv4_mapped
    return ip.is_loopback
