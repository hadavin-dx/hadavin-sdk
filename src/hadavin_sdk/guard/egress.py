"""Outbound allowlist: every host the core calls must be listed in ``egress.yaml``."""

from __future__ import annotations

import ipaddress
import re
import unicodedata

from hadavin_sdk.safe_url import InvalidUrl, safe_urlsplit

# What a refusal may print of the host: a host name or an address (letters, digits, dot, hyphen, colon), at most 253
# characters, AND shaped like a host: it has a dot, or it is `localhost`, or it is an IP address. Anything else is
# printed as `?`: a refused host can be a pasted text or a pasted key (a lower-case hex or hyphenated key has only
# these characters, but no dot), and it is the operator's own host list that has to name the host, not this message.
# What this does not stop: a pasted text that has a dot and only host-name characters (a dotted token) is shown.
_HOSTNAME = re.compile(r"[a-z0-9:](?:[a-z0-9.:-]{0,251}[a-z0-9:])?")


def _shown_host(host: str) -> str:
    """The host for a refusal: shown only when it looks like a host (see `_HOSTNAME`), else `?`."""
    if not _HOSTNAME.fullmatch(host):
        return "?"
    if "." in host or host == "localhost":
        return host
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return "?"
    return host


class EgressRefused(PermissionError):
    pass


def normalise_host(host: str | None) -> str:
    """One spelling of a host: NFKC, lower case, no trailing dot, punycode for non-ASCII. Both the host being
    called and every allowlist entry go through it, so a trailing dot or capital letters name the same host."""
    host = unicodedata.normalize("NFKC", host or "").strip().lower().rstrip(".")
    if not host.isascii():
        try:
            host = host.encode("idna").decode("ascii")
        except UnicodeError:
            pass
    return host


def egress_check(host_or_url: str, allowed: frozenset[str]) -> str:
    try:
        host = safe_urlsplit(host_or_url).hostname if "://" in host_or_url else host_or_url
    except InvalidUrl:
        raise EgressRefused("host not in egress.yaml: ?") from None
    host = normalise_host(host)
    if not host or host not in {normalise_host(a) for a in allowed}:
        raise EgressRefused(f"host not in egress.yaml: {_shown_host(host)}")
    return host
