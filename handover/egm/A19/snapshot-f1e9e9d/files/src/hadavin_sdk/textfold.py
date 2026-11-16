"""The one canonical text form of the redactor and of the id check. A leaf module: it imports only the standard library,
so `stages.py` (which every guard imports at the top of its file) can use it without loading the guard package.
tests/test_tenant_ids.py pins this import list by an AST walk."""

from __future__ import annotations

import unicodedata


def canonical(text: str) -> str:
    """Untrusted text in one canonical form before it is escaped, redacted or compared: Unicode NFKC (a
    full-width `＜ＩＰＶ４＿２＞` becomes `<IPV4_2>`) with the invisible format characters removed (a zero-width
    space inside a token no longer hides it)."""
    return "".join(
        c for c in unicodedata.normalize("NFKC", text) if unicodedata.category(c) != "Cf"
    )
