"""One fold for comparing people, requesters and beneficiaries (separation-of-duties checks), and the text rule that goes with it.

`fold` is the fold output scanners use: NFKD (a base letter and its combining mark separate), drop combining marks, format, control and
separator characters and invisible filler letters, recompose with NFKC, collapse whitespace, casefold. A look-alike made with U+0301,
U+FE0F, U+3164 or U+00A0 therefore folds to the real id. `text_ok` refuses such text outright at the trust boundary, so what is accepted
compares exactly. Standard library only. Not covered: cross-script look-alikes (Cyrillic/Greek letters that look Latin).
"""

from __future__ import annotations

import unicodedata

_DROP = frozenset({"Cf", "Cc", "Zl", "Zp", "Mn"})
FILLERS = frozenset(
    {"\u3164", "\u115f", "\u1160", "\u2800", "\uffa0"}
)  # invisible letters/symbols used to glue or split words
_REFUSE = frozenset({"Cc", "Cf", "Zl", "Zp", "Co", "Cs", "Mn", "Me"})


def fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text)
    t = "".join(
        "" if (unicodedata.category(c) in _DROP or c in FILLERS) and c not in "\n\t" else c
        for c in t
    )
    return " ".join(unicodedata.normalize("NFKC", t).casefold().split())


def same_person(a: str, b: str) -> bool:
    folded = fold(a)
    return folded != "" and folded == fold(b)


def text_ok(s: object, max_len: int = 254) -> bool:
    """Bounded printable text: no control, format, separator, private-use, combining-mark, filler or non-ASCII space characters, and not empty once folded."""
    return (
        isinstance(s, str)
        and 0 < len(s) <= max_len
        and fold(s) != ""
        and not any(
            unicodedata.category(c) in _REFUSE
            or c in FILLERS
            or (c != " " and unicodedata.category(c) == "Zs")
            for c in s
        )
    )
