"""Text normalisation for output scanning and injection-marker matching (checks.md).

Confusable folding (Cyrillic, Greek, Armenian ... look-alike letters read as Latin) comes from ONE place: the verbatim copy of core PR 50's
`guard/textnorm.py` in `core_copy/` (awaiting core PR 50; see CORE_COPIES.md). THIS module is the only importer of that copy: every other
module reaches it through `skeleton` and `mixed_script` here (`approval.py` and `writegate.py` call those two; `contains_marker` has NO runtime caller, it is
tested here and is the scan the stage-2 scorer would use), so the switch to `hadavin_sdk.guard.textnorm` is the one import line below.
`normalise` stays NFKD-drop-NFKC-casefold WITHOUT the look-alike table (it is the stored/compared form of approvals, `approval.norm`); the
look-alike fold is applied only where a DENY or a scan wants over-matching (`skeleton`, `contains_marker`). The real control against free text
reaching a customer is that customer-facing drafts are harness templates with typed slots; the scan is defence in depth for staff-facing fields.
"""

from __future__ import annotations

import re
import unicodedata

from refunds.core_copy import (
    textnorm as _core,  # the ONLY import of the core copy (swap to hadavin_sdk.guard.textnorm after PR 50 merges)
)

_DROP_CATS = {
    "Cf",
    "Cc",
    "Zl",
    "Zp",
    "Mn",
}  # format (ZWSP, ZWJ, BOM, word joiner, bidi controls, tag chars), control, separators, marks
FILLERS = {"\u3164", "\u115f", "\u1160", "\u2800", "\uffa0"}  # invisible 'letters' (category Lo / So) used to glue or split words


# control, format, separators, private-use, surrogates, combining marks
_BAD_CATS = frozenset({"Cc", "Cf", "Zl", "Zp", "Co", "Cs", "Mn", "Me"})


def text_ok(s: object, max_len: int) -> bool:
    """Bounded printable text for requester, beneficiary and operator reasons. Refused: control, format (bidi, zero-width), line/paragraph separators,
    private-use, COMBINING MARKS, invisible filler letters and every space except U+0020, and text that is nothing once folded. Call it BEFORE any
    comparison: a space inside an id is a different id, so the fold alone does not equate it with the real one."""
    return (
        isinstance(s, str)
        and isinstance(max_len, int)
        and 0 < len(s) <= max_len
        and normalise(s) != ""
        and not any(
            unicodedata.category(ch) in _BAD_CATS or ch in FILLERS or (ch != " " and unicodedata.category(ch) == "Zs") for ch in s
        )
    )


def hidden_text(text: str) -> str:
    """Decode Unicode tag characters (U+E0020-E007E mirror ASCII) so text hidden in them is visible to scanners and flagged."""
    return "".join(chr(ord(ch) - 0xE0000) for ch in text if 0xE0020 <= ord(ch) <= 0xE007E)


def _norm(text: str, replacement: str) -> str:
    t = unicodedata.normalize("NFKD", text)
    t = "".join(replacement if (unicodedata.category(ch) in _DROP_CATS or ch in FILLERS) and ch not in "\n\t" else ch for ch in t)
    t = unicodedata.normalize("NFKC", t)
    return " ".join(t.casefold().split())


def normalise(text: str) -> str:
    """NFKD (so a base letter + combining mark is separated), DROP format/control/bidi/tag/zero-width/combining/filler characters, recompose with
    NFKC, collapse whitespace, casefold. Order matters: dropping marks AFTER composition would keep 'a' + U+0301 as one letter."""
    return _norm(text, "")


def normalise_keep_case(text: str) -> str:
    """The same drop-and-recompose as `normalise` but the case is kept (whitespace still collapses): for a check that reads capitals, such as
    'a dot, one space, a LOWERCASE word is a host; a capital starts a new sentence'."""
    t = unicodedata.normalize("NFKD", text)
    t = "".join("" if (unicodedata.category(ch) in _DROP_CATS or ch in FILLERS) and ch not in "\n\t" else ch for ch in t)
    return " ".join(unicodedata.normalize("NFKC", t).split())


def normalise_keep_marks(text: str) -> str:
    """NFKC only (no NFKD mark-drop, no casefold): drops format, control, separator and filler characters and collapses whitespace, but KEEPS combining
    marks and the exact letters. This is the view for an ALLOW decision on a host or link: an accent or a look-alike letter must still be there when the
    text is compared with the allow-list (`shop.ex\u00e1mple` is not `shop.example`)."""
    t = unicodedata.normalize("NFKC", text)
    t = "".join(
        ""
        if (unicodedata.category(ch) in _DROP_CATS and unicodedata.category(ch) not in ("Mn", "Me") or ch in FILLERS)
        and ch not in "\n\t"
        else ch
        for ch in t
    )
    return " ".join(t.split())


def normalise_spaced(text: str) -> str:
    """Same, but the dropped characters become a SPACE, so an invisible character between two words cannot glue them ('approved<ZWSP>now')."""
    return _norm(text, " ")


def skeleton(s: str) -> str:
    """The over-matching DENY key: look-alike letters read as Latin, marks and invisible characters dropped, case folded. Never an ALLOW."""
    return _core.fold_key(s)


def mixed_script(s: str) -> bool:
    """One word mixing Latin with Cyrillic, Greek, Armenian ... letters (the fail-closed look-alike signal)."""
    return _core.has_mixed_script(s)


_SEP = r"[\s._*\-]"  # separators an attacker can put BETWEEN the letters of a word ("appro ved", "a.p.p.r.o.v.e.d")
MIN_SEPARATED_LEN = 5  # shorter markers, and any marker with a digit, must match with NO separator inside a word


def _hit(m: str, hay: str) -> bool:
    """The marker as a whole word (markers under 12 characters need non-LETTER boundaries on both sides: 'disapproved' is not 'approved'; longer
    ones match as substrings). A LETTER-only marker of 5+ characters also matches with ANY run of separators (space, TAB, `.`, `_`, `*`, `-`) between
    its letters (a bound on the count would only invite one more separator; a run of any length is still linear); the marker's own spaces match one or
    more separators. Markers with a digit ('999900') or under 5 letters allow no separator inside a word: '9999.00' and 'a.p.p' are not them.
    Documented false-positive set of the separator rule: 'ap.prove', 'a p p r o v e', 'app-roved' read as 'approve(d)'. Not caused by it, but true of
    the word match itself: 'pre-approved', 'not approved', 'dis approved' contain the WORD 'approved' after a non-letter and DO match."""
    loose = len(m.replace(" ", "")) >= MIN_SEPARATED_LEN and not any(ch.isdigit() for ch in m)
    if loose:
        pat = "".join(_SEP + "+" if ch == " " else re.escape(ch) + _SEP + "*" for ch in m).removesuffix(_SEP + "*")
    else:
        pat = re.escape(m)
    if len(m) < 12:
        pat = r"(?<![^\W\d_])" + pat + r"(?![^\W\d_])"
    return re.search(pat, hay) is not None


def contains_marker(output: str, marker: str) -> bool:
    """Marker present in the dropped-form OR the spaced-form of the output, or in the decoded hidden (tag-character) text, plainly or after the
    look-alike fold (a Cyrillic-a 'approved' is found). Markers of 12+ characters match as substrings; shorter ones match as whole words where a
    boundary is any non-LETTER ('approved.', 'approved_x', 'approved123'). A run of separators between the letters of a LETTER-only marker of 5+ characters does not hide it ('appro ved', 'appro..ved'); digit markers and short markers
    get no separator tolerance (see `_hit` for the false-positive set)."""
    m = normalise(marker)
    if not m:
        return False
    views = (normalise(output), normalise_spaced(output), normalise(hidden_text(output)))
    fm = skeleton(m)
    return any(_hit(m, h) for h in views) or bool(fm) and any(_hit(fm, skeleton(h)) for h in views)
