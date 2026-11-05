"""Text folding and name tokens, in one place (kit-local until the core guard/textnorm module is adopted).

`fold` is NFKC plus casefold, with a leading byte-order mark dropped: the comparison used for deny-lists and for
"the same key once case is ignored". `tokens` splits an identifier on separators and camelCase boundaries
(`amountUsd` -> amount, usd; `refund_amount_usd` -> refund, amount, usd) so a name can be matched word by word.
It does NOT fold look-alike letters from other scripts: callers refuse non-ASCII identifiers instead.
"""

from __future__ import annotations

import re
import unicodedata

_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_SPLIT = re.compile(r"[^A-Za-z0-9]+")


def fold(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold().lstrip("\ufeff")


def alnum(name: str) -> str:
    """Lower-case letters and digits only: how tool and action names are compared."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def tokens(name: str) -> list[str]:
    out: list[str] = []
    for part in _SPLIT.split(name):
        out += [t.lower() for t in _CAMEL.split(part) if t]
    return out
