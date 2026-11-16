"""Outbound allowlist: every host the core calls must be listed in ``egress.yaml``."""

from __future__ import annotations

import unicodedata
from urllib.parse import urlsplit


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
    host = urlsplit(host_or_url).hostname if "://" in host_or_url else host_or_url
    host = normalise_host(host)
    if not host or host not in {normalise_host(a) for a in allowed}:
        raise EgressRefused(f"host not in egress.yaml: {host or '?'}")
    return host
