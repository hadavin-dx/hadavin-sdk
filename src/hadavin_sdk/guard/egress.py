"""Outbound allowlist: every host the core calls must be listed in ``egress.yaml``."""

from __future__ import annotations

import re
import unicodedata

from hadavin_sdk.safe_url import InvalidUrl, safe_urlsplit

# What a refusal may print of the host: a host name or an address (letters, digits, dot, hyphen, colon), at most 253
# characters. Anything else is printed as `?`: a refused host can be a pasted text, and it is the operator's own
# host list that has to name the host, not this message.
_HOSTNAME = re.compile(r"[a-z0-9:](?:[a-z0-9.:-]{0,251}[a-z0-9:])?")


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
        raise EgressRefused(
            f"host not in egress.yaml: {host if _HOSTNAME.fullmatch(host) else '?'}"
        )
    return host
