"""The one list of loopback spellings and the two questions asked of it. A leaf module: it imports only the
standard library, so the settings, the HTTP guard, the model clients, the stores and the bind check can all ask
here instead of each keeping its own list.

One list, ``LOOPBACK_LITERALS`` (``127.0.0.1``, ``localhost``, ``::1``), and two named questions, kept apart on
purpose:

Question | function | who asks it:

* Is this exact text one of the three spellings a plain-http endpoint may use? | ``is_loopback_literal`` | the
  settings checks and the model clients; ``guard/http.py`` asks the same list after its own
  ``normalise_host`` step.
* Is this bind host this computer (any 127.x.x.x address, ``::1`` with or without brackets, a mapped loopback
  address, ``localhost`` in any letter case)? | ``is_loopback_host`` | ``bindguard`` (a bind a stranger could
  reach is refused).

* ``is_loopback_host``: the strict reading of a bind address. It never looks a name up, so the answer cannot
  change with a DNS reply. Anything it cannot read is not loopback. A dotted address with a zero in front of a
  number (``0177.0.0.1``, ``127.000.000.001``) is refused here on purpose, before the standard library is asked, so
  the answer is the same on every Python the package supports (``requires-python = ">=3.12"`` in
  ``pyproject.toml``); the standard library itself only started refusing those in Python 3.9.5.
* ``LOOPBACK_LITERALS`` / ``is_loopback_literal``: the exact, small list for callers that send a request, because
  a wider list would widen what they allow.
"""

from __future__ import annotations

import ipaddress

# the address the name ``localhost`` is bound as, and the default host of a local server
LOOPBACK_V4 = "127.0.0.1"
LOOPBACK_LITERALS: frozenset[str] = frozenset({LOOPBACK_V4, "localhost", "::1"})


def is_loopback_literal(host: object) -> bool:
    """True only for the exact spellings in LOOPBACK_LITERALS (no letter-case change, no brackets, no range)."""
    return isinstance(host, str) and host in LOOPBACK_LITERALS


def _has_leading_zero_octet(text: str) -> bool:
    """True when the dotted-quad part of ``text`` (the whole text, or the text after the last colon of a mapped
    IPv6 address) has an octet such as ``0177`` or ``000``: a leading zero that some systems read as octal."""
    tail = text.rsplit(":", 1)[-1].rstrip("]")
    parts = tail.split(".")
    return len(parts) == 4 and any(len(p) > 1 and p.startswith("0") and p.isdigit() for p in parts)


def is_localhost_name(text: object) -> bool:
    """True for the name ``localhost`` in any letter case (and nothing else: no trailing dot, no white space)."""
    # str.lower, not casefold: casefold would also read the long-s letter as "s"
    return isinstance(text, str) and text.lower() == "localhost"


def parse_ip_literal(text: object) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    """The IP address that ``text`` writes out, or None. Only a plain written-out address is read: no name, no
    short or number-only spelling (``127.1``, ``2130706433``), no zero in front of a number (``0177.0.0.1``), no
    scope id (``::1%eth0``), no brackets round an IPv4 address, no unbalanced bracket; square brackets round an
    IPv6 address (the URL form) are accepted. Never looks a name up."""
    if not isinstance(text, str) or _has_leading_zero_octet(text):
        return None
    bare = text
    bracketed = text.startswith("[") and text.endswith("]")
    if bracketed:
        bare = text[1:-1]
    # a scope id (the standard library reads ``::1%eth0`` since Python 3.9): not a plain address. A single or
    # doubled bracket needs no check of its own: the standard library refuses any bracket left in ``bare``.
    if "%" in bare:
        return None
    try:
        ip = ipaddress.ip_address(bare)
    except ValueError:
        return None
    if bracketed and ip.version != 6:
        return None  # brackets belong to IPv6 only
    return ip


def is_loopback_host(name: object) -> bool:
    """True for ``localhost`` and for a loopback IP address; a wildcard, any other name and any other address
    can be reached from, or reach, other computers. Never resolves a name. Fails closed.

    Refused on purpose (each has a test): a name that only starts like loopback (``127.0.0.1.example.test``,
    ``localhost.example.test``), a trailing dot, white space, short or number-only spellings of an address
    (``127.1``, ``0x7f.0.0.1``, ``2130706433``, ``0177.0.0.1``), brackets round an IPv4 address or an
    unbalanced bracket, a scope id (``::1%eth0``), the wildcard addresses and a mapped address that holds a
    non-loopback IPv4 address. Square brackets round an IPv6 address are accepted (the URL form)."""
    if is_localhost_name(name):
        return True
    ip = parse_ip_literal(name)
    if ip is None:
        return False
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        # read the address inside: the same answer on every Python version (3.13 changed is_loopback for mapped forms)
        ip = ip.ipv4_mapped
    return ip.is_loopback
