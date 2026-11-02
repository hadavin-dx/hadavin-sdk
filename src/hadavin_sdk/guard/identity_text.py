"""Identity text at a trust boundary: one validator, two comparison keys, and which one to use for which question.

`text_ok(s, max_len)`   bounded printable text: no control, format, separator, private-use, combining-mark or filler
                        character, no space other than U+0020, not empty once folded. Call it FIRST at the boundary.
`identity_key(raw)`     (`ascii_only=True` refuses every non-ASCII character: use it where a safe charset is enough) the key for "must these two be DIFFERENT people?" (separation of duties, requester != approver).
                        It is the over-matching fold of `guard.textnorm` (accents, case, look-alike letters and
                        invisible characters all fold away), so a disguised copy of an approver collides with the real
                        one and the check fails SAFE. Input that is not `text_ok`, or that contains a look-alike letter
                        from another script, gives None by default (`lookalikes="refuse"`): a caller treats None as a
                        refusal. Pass `lookalikes="fold"` to accept such names (legitimate Cyrillic or Greek names) and
                        compare their Latin skeleton instead.
`exact_key(raw)`        the key for "is this EXACTLY the verified recipient / owner?" (a reply address, an account id).
                        NFC + casefold only, after `text_ok`: `jos\u00e9@x` and `jose@x` are different mailboxes and must
                        not match. Never use `identity_key` for this direction: its fold would let a reply go to a
                        different mailbox.
`same_person`, `same_recipient` apply the right key and return False for anything refused.
Not covered: scripts outside the `guard.textnorm` look-alike table (a curated list, not the full Unicode confusables set).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from typing import Literal

from hadavin_sdk.guard.textnorm import (
    FILLERS,
    LOOKALIKES,
    confusable_not_equal,
    fold,
    mixed_script,
    safe_equal,
)

DEFAULT_MAX_LEN = (
    254  # an e-mail address is at most 254 characters (RFC 5321); callers pass their own limit
)
_REFUSE = frozenset(
    {"Cc", "Cf", "Zl", "Zp", "Co", "Cs", "Cn", "Mn", "Me"}
)  # Cn: unassigned (tag characters) are refused like the fold drops them


def text_ok(s: object, max_len: int = DEFAULT_MAX_LEN) -> bool:
    return (
        isinstance(s, str)
        and isinstance(max_len, int)
        and 0 < len(s) <= max_len
        and not any(
            unicodedata.category(c) in _REFUSE
            or c in FILLERS
            or (c != " " and unicodedata.category(c) == "Zs")
            for c in s
        )
        and fold(s, casefold=True, collapse_ws=True) != ""
    )


def identity_key(
    raw: object,
    *,
    max_len: int = DEFAULT_MAX_LEN,
    lookalikes: Literal["refuse", "fold"] = "refuse",
    ascii_only: bool = False,
) -> str | None:
    if not text_ok(raw, max_len):
        return None
    assert isinstance(raw, str)  # noqa: S101 - narrowed by text_ok
    if (
        ascii_only and not raw.isascii()
    ):  # the strictest rule: a safe charset beats any confusables table
        return None
    if lookalikes == "refuse" and (
        any(c in LOOKALIKES or (c.isdecimal() and not c.isascii()) for c in raw)
        or mixed_script(raw)
    ):
        return None  # mixed_script: a fail-closed backstop for look-alikes the table does not know (eta, Armenian co, ...)
    return fold(raw, casefold=True, collapse_ws=True)


def exact_key(raw: object, *, max_len: int = DEFAULT_MAX_LEN) -> str | None:
    if not text_ok(raw, max_len):
        return None
    assert isinstance(raw, str)  # noqa: S101
    if mixed_script(
        raw
    ):  # an ALLOW target never mixes Latin with another script inside a word (a look-alike the table may not list)
        return None
    return " ".join(unicodedata.normalize("NFC", raw).casefold().split())


def same_person(a: object, b: object, **kw) -> bool:
    """True when the two names collide under the over-matching key (so True also means 'a disguised copy')."""
    ka, kb = identity_key(a, **kw), identity_key(b, **kw)
    return ka is not None and ka == kb


def same_recipient(a: object, b: object, *, max_len: int = DEFAULT_MAX_LEN) -> bool:
    """An ALLOW decision ("is this the verified address / owner?"): both are `text_ok`, neither mixes scripts, the exact keys are equal AND the shared
    `safe_equal` agrees. A look-alike that merely FOLDS equal is not equal here (see `lookalike_of`)."""
    ka, kb = exact_key(a, max_len=max_len), exact_key(b, max_len=max_len)
    return ka is not None and ka == kb and safe_equal(a, b)  # type: ignore[arg-type]


def lookalike_of(a: object, b: object) -> bool:
    """True when `a` is a look-alike spelling of `b`: they fold to the same text but are not `safe_equal`. An ALLOW check must refuse on True (and may
    report it), a DENY check treats the pair as the same."""
    return isinstance(a, str) and isinstance(b, str) and confusable_not_equal(a, b)


def unique_ids(ids: object, *, max_n: int, pattern: str = r"[a-z0-9-]{1,40}") -> bool:
    """A bounded list of distinct ids, each matching `pattern` completely (duplicates are refused, not collapsed)."""
    if not isinstance(ids, list | tuple) or not 0 < len(ids) <= max_n:
        return False
    rx = re.compile(pattern)
    return all(isinstance(i, str) and rx.fullmatch(i) for i in ids) and len(set(ids)) == len(ids)


def any_same_person(candidates: Iterable[object], target: object, **kw) -> bool:
    return any(same_person(c, target, **kw) for c in candidates)
