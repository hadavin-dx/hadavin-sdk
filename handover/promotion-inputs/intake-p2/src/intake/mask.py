"""Hide sensitive values before the AI service, put them back after (design WP2c B1-B5).

Detectors: the Intake bank finder (``invoicecheck.bank_detail_findings``) and the byte copy of the core redactor (``coreredact.find``). New code
here is only the LOCATION and DECISION layer: where in the original text a recognised value sits (one pass builds a digit skeleton; an index of the
prefixes of 6, 10, 16 and 24 characters is built when first needed; no regular expression runs per candidate), and rules R1 to R4 of design B1.0 (the single rule table).

What the checks prove and what they do not: for every value a detector recognised and decided to hide, the value is replaced before the request is
sent, none of its listed spellings is in the request (a1), and what is put back is the same text that was taken out (c). They cannot prove that the
detectors recognised everything. Missed and deliberately visible values are listed in the README limits (design B9).

Errors: a failing step raises ``SelfCheckFailed`` with a code only, from ``None``. No message, no value, no traceback detail is kept. There are exactly
two ``except Exception`` handlers (``mask`` gives ``mask_failed``; ``BodyCheck.__call__`` gives ``body_unsafe``); the broad-catch pin counts them.
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import re
import unicodedata
from bisect import bisect_right
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote_from_bytes, unquote

from . import coreredact, invoicecheck, strictjson, validators
from .checks import decoded_extras
from .checks import fold as _checks_fold
from .ground import money_spans
from .selfcheck_codes import SELFCHECK_CODES, SelfCheckFailed

MASK_MAX_LINE_CHARS = 2000  # a longer line (between \n characters) is held back before any detector runs (OPINION, B1.9)
MASK_MAX_DOC_CHARS = 20000  # a longer document is held back (the reader already caps it at the policy value; this is the ReDoS bound)
MASKED_MAX_CHARS = 40000  # a longer model text is held back (mask_too_large); budget.min_limit_micro derives its worst case from it
MODE = "known"
DETECTOR_VERSION = "wp2c-1;core-ce70eb5;wp3-lang1"
BODY_START, BODY_END = "<<<INVOICE_START>>>", "<<<INVOICE_END>>>"  # same text as model_anthropic (a test pins the equality)
_ALLOWED_CONTROLS = frozenset(
    "\t\n\r\v\f\x1c\x1d\x1e\x85"
)  # control characters that are line breaks or white space; any other is held back
_EXPECTED_ERRORS = (
    TypeError,
    AttributeError,
    ValueError,
    LookupError,
    ArithmeticError,
    RuntimeError,
    re.error,
)  # a tuple: the broad-catch pin counts only a bare Exception
KIND_LABELS = {
    "IBAN": "international bank account number (IBAN)",
    "BANK": "bank account number",
    "ROUTING": "bank sort or routing code",
    "CARD": "card number",
    "EMAIL": "email address",
    "PHONE": "phone number",
    "PERSON": "personal name",
    "ID": "personal ID number",
    "SECRET": "password, key or access code",
}
PRIORITY = ("SECRET", "CARD", "IBAN", "ROUTING", "BANK", "ID", "EMAIL", "PHONE", "PERSON")  # highest first
_FREE_TEXT_KINDS = ("EMAIL", "PHONE", "PERSON")
_FREE_TEXT_PATHS = ("lines[].description", "adjustments[].label")
_SECRET_CORE = frozenset("APIKEY PRIVKEY JWT GCPTOKEN AZURESAS WEBHOOK URLCRED BEARER BASIC SECRET HIGHENTROPY".split())
_CORE_KIND = {"EMAIL": "EMAIL", "PHONE": "PHONE", "NAME": "PERSON", "SSN": "ID", "AADHAAR": "ID", "PAN": "ID", "CREDITCARD": "CARD"}
_CORE_KIND.update(dict.fromkeys(_SECRET_CORE, "SECRET"))
_CORE_BANK = {"IBAN": "IBAN", "BANKCODE": "ROUTING", "BANKACCT": "BANK"}
SKELETON_BUILDS = [0]  # counts skeleton builds (a test asserts one build per detect call, not one per candidate)


# ---------------------------------------------------------------------------------------------------------------- results
@dataclass(frozen=True)
class Span:
    """A place in the ORIGINAL text. Positions only: the value is ``document_text[start:end]`` (a span is never a copy)."""

    start: int
    end: int
    kind: str
    placeholder: str = ""
    fingerprint: str = ""
    detector: str = ""


@dataclass(frozen=True)
class Kept:
    """A recognised bank-class value left visible on purpose (``money`` or ``id_token``)."""

    start: int
    end: int
    reason: str


@dataclass(frozen=True)
class Detection:
    spans: tuple[Span, ...] = field(default=(), repr=False)
    unlocated: tuple[str, ...] = field(default=(), repr=False)
    kept_visible: tuple[Kept, ...] = field(default=(), repr=False)
    money_overlap: bool = False
    notes: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class Masked:
    text: str = field(repr=False)
    spans: tuple[Span, ...] = field(repr=False)
    counts: dict[str, int] = field(default_factory=dict)
    money_cut: int = 0
    kept_visible: tuple[Kept, ...] = field(default=(), repr=False)
    kept_visible_texts: tuple[str, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class Restored:
    fields: Any = field(repr=False)
    items: tuple[tuple[str, str, str, str], ...] = ()  # (mark, stored fingerprint, restored fingerprint, "same"/"MISMATCH")
    restored: int = 0
    unknown: int = 0
    left: int = 0


def fp(key: bytes, value: str) -> str:
    """Keyed 8-hex index of a value (an index to match log lines, not a proof)."""
    return hashlib.blake2b(value.encode("utf-8", "surrogatepass"), key=key, digest_size=4).hexdigest()


# ---------------------------------------------------------------------------------------------------------------- fold per character
_DIGITS = frozenset("0123456789")
_LOOK = frozenset("oilsbz")
_LOOKDIGIT = str.maketrans("oilsbz", "011582")
_ALNUM = frozenset("abcdefghijklmnopqrstuvwxyz0123456789")
_WS_RUN = re.compile(r"[^\S\n]+")


def _fold_char(c: str) -> str:
    """The Intake fold (``invoicecheck.fold_text``) applied to ONE character: NFKD, invisible characters deleted, confusables, ``checks.fold``, casefold,
    look-alikes, dashes, slashes, line breaks. A test compares it with ``_f`` character by character over a test alphabet."""
    ic = invoicecheck
    t = unicodedata.normalize("NFKD", c).translate(ic.FOLD_DELETE).translate(ic.FOLD_CONFUSABLES)
    t = _checks_fold(t).casefold()
    t = (
        t.translate(ic.FOLD_CONFUSABLES)
        .translate(ic.FOLD_LOOKALIKE)
        .translate(ic.FOLD_DASHES)
        .translate(ic.FOLD_SLASHES)
        .translate(ic.FOLD_BREAKS)
    )
    return _WS_RUN.sub(" ", t.replace("\r\n", "\n").replace("\r", "\n"))


fold_char = _fold_char  # public name: the locator fold of one character; a test pins it equal to the Intake finder's fold


def _fold_list(s: str) -> list[str]:
    """The fold of every character (a per-call table of the distinct characters; no module-level cache)."""
    seen: dict[str, str] = {}
    out = []
    for c in s:
        f = seen.get(c)
        if f is None:
            f = seen[c] = _fold_char(c)
        out.append(f)
    return out


def _fold_str(s: str) -> str:
    return "".join(_fold_list(s))


def _word(c: str) -> bool:
    """The WP3 notion of a word character (``invoicecheck._word``)."""
    return c.isalnum() and unicodedata.category(c) != "Lm"


class _Skel:
    """Characters of one kind (digits, digits with look-alike letters, or letters and digits) with their positions in the original text.

    ``bad`` is a running count of pairs of neighbours whose gap breaks the gap rule, so a candidate is checked in constant time."""

    __slots__ = ("bad", "chars", "idx", "levels", "outside")
    PREFIX_LEVELS = (6, 10, 16, 24)  # a candidate is looked up by the longest of these not longer than itself

    def __init__(self, chars: str, idx: list[int], bad: list[int], outside: frozenset[str]) -> None:
        self.chars, self.idx, self.bad, self.outside = chars, idx, bad, outside
        self.levels: dict[int, dict[str, list[int]]] = {}

    def starts_for(self, cand: str) -> list[int]:
        """Positions where ``cand``'s prefix (6, 10, 16 or 24 characters, the longest that fits) stands. One index per length, built when first needed:
        candidates that share a short prefix share only the positions that match their longer prefix (worst case: candidates times the positions
        sharing 24 characters)."""
        length = max(lv for lv in self.PREFIX_LEVELS if lv <= len(cand))
        table = self.levels.get(length)
        if table is None:
            table = self.levels[length] = {}
            chars = self.chars
            for k in range(len(chars) - length + 1):
                table.setdefault(chars[k : k + length], []).append(k)
        return table.get(cand[:length], [])


def _build_skel(
    text: str, fp_: list[str], members: frozenset[str], mapper, outside: frozenset[str], max_breaks: int, block_words: bool
) -> _Skel:
    chars: list[str] = []
    idx: list[int] = []
    bad = [0]
    blocked = False
    breaks = 0
    have = False
    for i, p in enumerate(fp_):
        for ch in p:
            if ch in members:
                if have:
                    bad.append(bad[-1] + (1 if (blocked or breaks > max_breaks) else 0))
                chars.append(ch.translate(mapper) if mapper else ch)
                idx.append(i)
                have, blocked, breaks = True, False, 0
            elif ch == "\n":
                if not (text[i] == "\n" and i > 0 and text[i - 1] == "\r"):
                    breaks += 1
            elif block_words and _word(ch):
                blocked = True
    return _Skel("".join(chars), idx, bad, outside)


def _skeletons(text: str, fp_: list[str]) -> tuple[_Skel, _Skel, _Skel]:
    SKELETON_BUILDS[0] += 1
    raw = _build_skel(text, fp_, _DIGITS, None, _DIGITS, 1, True)
    look = _build_skel(text, fp_, _DIGITS | _LOOK, _LOOKDIGIT, _DIGITS | _LOOK, 1, True)
    alnum = _build_skel(text, fp_, _ALNUM, None, _ALNUM, 3, False)
    return raw, look, alnum


def _outside_ok(fp_: list[str], i: int, step: int, outset: frozenset[str]) -> bool:
    j = i + step
    while 0 <= j < len(fp_) and fp_[j] == "":
        j += step
    if not 0 <= j < len(fp_):
        return True
    p = fp_[j]
    return p[-1 if step < 0 else 0] not in outset


def _find(sk: _Skel, fp_: list[str], cand: str, ends: bool = True) -> list[tuple[int, int]]:
    """Every place in the original text where ``cand`` appears as a whole value (gap rule and end rule of design B1.0). ``ends=False`` drops the end
    rule: the candidate may then stand inside a longer run (used only to see where a padded IBAN-shaped reference sits)."""
    n = len(cand)
    out: list[tuple[int, int]] = []
    if n == 0 or n > len(sk.chars):
        return out
    if n >= 6:
        starts: Any = sk.starts_for(cand)
    else:
        starts = []
        k = sk.chars.find(cand)
        while k >= 0:
            starts.append(k)
            k = sk.chars.find(cand, k + 1)
    for k in starts:
        e = k + n - 1
        if e >= len(sk.chars) or not sk.chars.startswith(cand, k) or sk.bad[e] - sk.bad[k]:
            continue
        a, b = sk.idx[k], sk.idx[e]
        if (k and sk.idx[k - 1] == a) or (e + 1 < len(sk.idx) and sk.idx[e + 1] == b):
            continue
        if not ends or (_outside_ok(fp_, a, -1, sk.outside) and _outside_ok(fp_, b, 1, sk.outside)):
            out.append((a, b + 1))
    return out


# ---------------------------------------------------------------------------------------------------------------- lines and context
_NUMBER_ONLY = re.compile(r"[0-9][0-9 ./,-]*")
_ROUTING_W = re.compile(r"sort\W{0,3}code|routing|branch\W{0,3}code|(?<![a-z])(?:aba|bsb|ifsc|blz|clabe|transit|clearing)(?![a-z])")
_OTHER_W = re.compile(r"acct|acc|a/c|bank|iban|konto|swift|bic|cuenta|compte|conto|rekening|banco|banque|rib")
# Masking-only bank words (errata 94): they make a line bank context for MASKING; the D10 check (bank_word_in) is unchanged.
_LANG_WORD = re.compile(r"(?<![a-z])(?:cuenta|compte|conto|rekening|banco|banque|rib)(?![a-z])")
_BANK_STEMS = (
    "acc",
    "a/c",
    "bank",
    "sort",
    "routing",
    "swift",
    "clearing",
    "konto",
    "branch",
    "iban",
    "aba",
    "bic",
    "bsb",
    "blz",
    "ifsc",
    "clabe",
)
_ID_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._/-")
_ID_SCAN = 200  # characters looked at on each side of an occurrence for the id test


class _Lines:
    def __init__(self, text: str) -> None:
        self.lines = text.splitlines(keepends=True)
        self.starts: list[int] = []
        pos = 0
        for ln in self.lines:
            self.starts.append(pos)
            pos += len(ln)
        n = len(self.lines)
        # a line with an entity or a non-ASCII character is folded by the finder's own fold (it unescapes after NFKD, twice, and a third time for the CamelCase copy); any other line
        # by the cheap per-character fold, which is the same function for it
        folded = [(invoicecheck.fold_text(ln) if ("&" in ln or not ln.isascii()) else _fold_str(ln)).strip() for ln in self.lines]
        # bank_word_in folds each line again (costly): ask it only when a stem of some bank word is in the line (the cheap test cannot miss one)
        bw = [
            (("&" in ln or not ln.isascii() or any(st in f for st in _BANK_STEMS)) and invoicecheck.bank_word_in(ln))
            or bool(_LANG_WORD.search(f))
            for ln, f in zip(self.lines, folded, strict=True)
        ]
        self.ctx = [False] * n
        for i in range(n):
            if not bw[i]:
                continue
            self.ctx[i] = True
            for j in range(i + 1, min(n, i + 1 + invoicecheck.NEXT_LINES)):  # first non-blank line among the next three
                if folded[j]:
                    self.ctx[j] = True
                    break
            if i and _NUMBER_ONLY.fullmatch(folded[i - 1]):  # the line directly above, when it holds only a number
                self.ctx[i - 1] = True

    def of(self, pos: int) -> int:
        return max(0, bisect_right(self.starts, pos) - 1)


def _id_shaped(text: str, s: int, e: int) -> bool:
    lo = s
    while lo > 0 and s - lo < _ID_SCAN and text[lo - 1] in _ID_CHARS:
        lo -= 1
    hi = e
    while hi < len(text) and hi - e < _ID_SCAN and text[hi] in _ID_CHARS:
        hi += 1
    around = text[lo:s] + text[e:hi]
    return any(c.isalpha() for c in around)  # a token holding a bank word sits on a bank-context line, which the caller already excluded


_KIND_LOOKBACK = 200  # characters to the left of an occurrence searched for the nearest bank word (bounds the cost on very long lines)


def _bank_kind(fp_: list[str], line_start: int, s: int, hint: str) -> str:
    left = "".join(fp_[max(line_start, s - _KIND_LOOKBACK) : s])
    best, cls = -1, ""
    for m in _ROUTING_W.finditer(left):
        if m.start() > best:
            best, cls = m.start(), "R"
    for m in _OTHER_W.finditer(left):
        if m.start() > best:
            best, cls = m.start(), "O"
    if cls == "R":
        return "ROUTING"
    if cls == "O":
        return "BANK"
    return "ROUTING" if hint == "ROUTING" else "BANK"


# ---------------------------------------------------------------------------------------------------------------- core kinds, narrowing
_PHONE_WORD = re.compile(
    r"(?<![a-z])(?:telephone|tel|phone|mobile|mob|cell|whatsapp|fax|telefon|telefono|contact no|contact number)(?![a-z])|(?<![a-z])ph[.:]"
)
_SSN_WORD = re.compile(r"(?<![a-z])(?:ssn|social security|tin|ein)(?![a-z])")
_AADHAAR_WORD = re.compile(r"(?<![a-z])(?:aadhaar|uid)(?![a-z])")
_PAN_WORD = re.compile(r"(?<![a-z])pan(?![a-z])")
_TITLES = r"(?:mr|mrs|ms|miss|dr|prof|shri|smt|sri|mx)"
_DEAR_BEFORE = re.compile(  # a name context: Dear, Attn, a title, or a name label (errata 94)
    r"(?:(?<![a-z])(?:dear|attn|attention)[:.]?\W{0,3}|(?<![a-z])"
    + _TITLES
    + r"\.?\s+|(?:contact name|cardholder name|name on card|account holder)\s*:\s*)"
    r"(?:" + _TITLES + r"\.?\s+)?$"
)
_NAME_FIND = re.compile(
    r"(?:\b(?:Dear|Attn|Attention)[:.]?\s+(?:(?:Mr|Mrs|Ms|Miss|Dr|Prof|Shri|Smt|Sri|Mx)\.?\s+)?|\b(?:Mr|Mrs|Ms|Miss|Dr|Prof|Shri|Smt|Sri|Mx)\.?\s+"
    r"|(?:Contact name|Cardholder name|Name on card|Account holder)\s*:\s*)([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)"
)
_PHONE_LABELLED = re.compile(
    r"(?<![a-z])(?:telephone|tel|phone|mobile|mob|cell|whatsapp|fax|telefon|telefono|contact no|contact number)(?![a-z])"
    r"(?:\s*\([a-z ]{1,15}\))?[^\w+(]{0,4}"
    r"|(?<![a-z])ph(?=[.:])[.:]\s{0,3}",
    re.IGNORECASE,
)
_PHONE_NUM = re.compile(r"[+(]?\d[\d ()./-]{5,70}\d")
_PHONE_PLUS = re.compile(r"(?<![\w])\+\d[\d ()./-]{6,70}\d")
_NANP_END = r"(?![\d-]|\.\d)"
_NANP_BRACKET = re.compile(r"(?<![\w.-])\([2-9]\d{2}\)[ .-]?\d{3}[ .-]\d{4}" + _NANP_END)  # a parenthesised area code is a phone signal
_NANP_LEADING = re.compile(r"(?<![\w.-])(?:\+1[ .-]?|1[.-])[2-9]\d{2}[ .-]\d{3}[ .-]\d{4}" + _NANP_END)  # a leading +1 or 1-
_NANP_BARE = re.compile(r"(?<![\w.-])[2-9]\d{2}[ .-]\d{3}[ .-]\d{4}" + _NANP_END)  # needs a phone word before it
_DATEISH = re.compile(r"(?<!\d)(?:\d{1,2}[/.-]\d{1,2}[/.-](?:\d{2}|\d{4})|\d{4}-\d{2}-\d{2})(?!\d)")
_CARD_WORDS = re.compile(r"(?<![a-z])(?:card|visa|mastercard|master card|amex|american express|credit|debit|cc|pan)(?![a-z])")
_CARD_SHAPES = (
    re.compile(r"(?<!\d)\d{13,19}(?!\d)"),  # contiguous
    re.compile(r"(?<!\d)\d{4}(?:[ -]{1,2}\d{4}){3}(?!\d)"),  # 4-4-4-4
    re.compile(r"(?<!\d)\d{4}[ -]{1,2}\d{6}[ -]{1,2}\d{5}(?!\d)"),  # 4-6-5
    re.compile(r"(?<!\d)\d{4}[ -]{1,2}\d{6}[ -]{1,2}\d{4}(?!\d)"),  # 4-6-4
)


def _iban_valid(cand: str) -> bool:
    """ISO 13616 check: move the first four characters to the end, letters to numbers (a=10), the number modulo 97 is 1."""
    if not 15 <= len(cand) <= 34 or not cand.isalnum():
        return False
    moved = cand[4:] + cand[:4]
    return int("".join(str(int(c, 36)) for c in moved)) % 97 == 1


IBAN_REF_MAX_LEN = (
    13  # a place this short (SO20261015001), far from its country's length, with no IBAN word and a failed checksum, is a reference
)
_IBAN_SEP = (
    r"[ \t\-/.,;:|>]"  # what may stand between two groups of one IBAN, in FOLDED text (a no-break space is a space, an en dash a hyphen)
)
_IBAN_GAP = re.compile(_IBAN_SEP + "{0,6}(?:\n" + _IBAN_SEP + "{0,6}){0,6}")  # a CRLF is two newlines once folded: up to three line breaks
_IBAN_MONTH, _IBAN_DAY, _IBAN_YEAR = r"(?:0?[1-9]|1[0-2])", r"(?:0?[1-9]|[12]\d|3[01])", r"(?:19|20)\d{2}"
_IBAN_DATE_AHEAD = re.compile(  # a plausible calendar date (d m yyyy or yyyy m d, separated by . / - or a space), not followed by another digit or by a separator and a digit (``1970 04.11`` in front of ``.2026`` is account digits)
    rf"(?:{_IBAN_DAY}[./\- ]{_IBAN_MONTH}[./\- ]{_IBAN_YEAR}|{_IBAN_YEAR}[./\- ]{_IBAN_MONTH}[./\- ]{_IBAN_DAY})(?![./\-]?\d)"
)
_IBAN_AMOUNT_AHEAD = re.compile(r"\d{1,3}(?:,\d{3})*[.,]\d{2}(?!\d)")  # an amount with two decimals, as written after an account
_BANK_CODE_AND_DIGITS = re.compile(r"[a-z]{4}[0-9]+")  # a bank code and its digits read as one group (a zero-width character between them)
_IBAN_CURRENCY = re.compile(r"(?i)\b(?:eur|usd|gbp|cad|aud|chf|inr|jpy|sek|nok|dkk|pln|czk)\b")
_IBAN_LAST_GROUP_SLACK = 3  # a group may run this much past the registry length (a typed extra digit)
_IBAN_MIN_BEYOND = 16  # a candidate that runs beyond a hidden place at least this long is hidden whole


def _padding_after(text: str, end: int) -> bool:
    """True when what follows a place is padding the finder added and not more of the account: a date, or a word without a digit (read on the
    FOLDED text, so an en dash or a no-break space in the date does not matter)."""
    tail = _fold_str(text[end : end + 40])
    i = 0
    while i < len(tail) and not tail[i].isalnum():
        i += 1
    if _IBAN_DATE_AHEAD.match(tail, i) or _IBAN_AMOUNT_AHEAD.match(tail, i):
        return True
    j = i
    while j < len(tail) and tail[j].isalnum():
        j += 1
    return not any(c.isdigit() for c in tail[i:j])


def _iban_places(text: str, fp_: list[str], alnum: _Skel, money: list[tuple[int, int]]) -> list[tuple[int, int, str]]:
    """Every IBAN-SHAPED place, whatever the checksum says. It starts at a country code of the registry followed by two digits (side by side, or the
    code and the two digits as two tokens), then walks the following groups up to the registry length, joined by spaces, hyphens, dots, slashes, bars
    and similar across one line or several. Gaps and dates are read from the FOLDED text. A group has a digit; a letters-only group is a bank code:
    exactly four letters, followed by a group with a digit, at most twice, the first right after the check digits, never at the end (a word there is no bank code); a letters-only group of up to three that completes
    the length is the tail some countries print (``NO29 1111 1111 ABC``). Digit groups longer than
    four characters run at most three past the registry length. The walk stops before a date and before an amount (one with a currency sign or a
    thousands comma, or a decimal amount beside a currency code). ``(start, end, lower-case alphanumerics)`` in the original text; the decision to
    hide a place is made per place."""
    chars, idx = alnum.chars, alnum.idx
    length = invoicecheck.IBAN_LENGTH_FOLDED
    folded = "".join(fp_)
    fstart = [0]
    for piece in fp_:
        fstart.append(fstart[-1] + len(piece))
    stops = [(a, b) for a, b in money if re.search("[$£€,]", text[a:b])]
    for m_ in re.finditer(r"(?<![\d.,])\d{1,3}\.\d{2}(?!\d)", text):  # a decimal amount beside a currency code
        if _IBAN_CURRENCY.search(text[max(0, m_.start() - 6) : m_.end() + 6]):
            stops.append((m_.start(), m_.end()))
    out: list[tuple[int, int, str]] = []
    n = len(chars)

    def gap(i: int, j: int) -> str:
        return "".join(fp_[idx[i] + 1 : idx[j]])

    def raw_end(i: int) -> int:
        """End of the token at i: characters side by side, or separated only by zero-width characters (they show nothing: ``N<ZW>W<ZW>B<ZW>K``)."""
        while i + 1 < n and gap(i, i + 1) == "":
            i += 1
        return i

    group_end = raw_end

    def solid_end(i: int) -> int:
        """End of the characters side by side with i in the original text (a zero-width character ends them): the check digits are exactly two."""
        while i + 1 < n and idx[i + 1] - idx[i] <= 1:
            i += 1
        return i

    def stop_at(i: int, e: int) -> bool:
        return any(x < idx[e] + 1 and idx[i] < y for x, y in stops)

    def date_ahead(i: int) -> bool:
        return _IBAN_DATE_AHEAD.match(folded, fstart[idx[i]]) is not None

    def next_has_digit(i: int) -> bool:
        """True when the group at i exists, is joined by a valid gap, is no amount, and has a digit."""
        if i >= n or not _IBAN_GAP.fullmatch(gap(i - 1, i)):
            return False
        e = group_end(i)
        return not stop_at(i, e) and any(c.isdigit() for c in chars[i : e + 1])

    k = 0
    while k < n - 3:
        cc = chars[k : k + 2]
        if not (
            cc in length and cc.isalpha() and (_outside_ok(fp_, idx[k], -1, _ALNUM) or (idx[k] > 0 and fp_[idx[k] - 1] == ""))
        ):  # a zero-width character before the code separates it
            k += 1
            continue
        first = raw_end(k)
        if first >= k + 3 and chars[k + 2 : k + 4].isdigit():  # GB29, GB29NWBK, GB29NWBK60161331926819
            last = first
        elif (
            first == k + 1
            and k + 3 < n
            and chars[k + 2 : k + 4].isdigit()
            and solid_end(k + 2) == k + 3
            and _IBAN_GAP.fullmatch(gap(k + 1, k + 2))
        ):
            last = raw_end(k + 2)  # the code and the check digits (with whatever sticks to them) as two tokens: DE 89 3704 ...
        else:
            k += 1
            continue
        count = last - k + 1
        pos, codes = last + 1, 0
        while count < length[cc] and pos < n:
            if not _IBAN_GAP.fullmatch(gap(pos - 1, pos)) or date_ahead(pos):
                break
            e = group_end(pos)
            m = e - pos + 1
            if stop_at(pos, e):
                break
            if not any(c.isdigit() for c in chars[pos : e + 1]):
                tail_code = count + m == length[cc] and m <= 3 and not _IBAN_CURRENCY.fullmatch(chars[pos : e + 1])  # NO29 1111 1111 ABC
                bank_code = m == 4 and (count <= 8 or codes == 1) and next_has_digit(e + 1)
                if not (tail_code or bank_code):
                    break
                codes += 1
            elif m > 4 and (
                m > length[cc] - count + _IBAN_LAST_GROUP_SLACK
                or (not _BANK_CODE_AND_DIGITS.fullmatch(chars[pos : e + 1]) and not chars[pos : e + 1].isdigit())
            ):
                break  # a long group is digits (or the bank code stuck to digits by a zero-width character), not much more than what is missing: a letter elsewhere in it is the next reference
            last, count, pos = e, count + m, e + 1
        out.append((idx[k], idx[last] + 1, chars[k : last + 1]))
        k = last + 1
    return out


def _iban_reference(place: str, iban_word: bool) -> bool:
    """The ONE skip rule: a short place that is no IBAN. No IBAN word in the text, a length more than two away from its country's and at most ``IBAN_REF_MAX_LEN``
    characters (a valid IBAN has at least 15, so no checksum test is needed). Every other IBAN-shaped place is hidden: a false hide costs at most a hold-back, a leak is worse."""
    return (not iban_word) and abs(len(place) - invoicecheck.IBAN_LENGTH_FOLDED[place[:2]]) > 2 and len(place) <= IBAN_REF_MAX_LEN


def _luhn(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


def _trim_phone(num: str, limit: int = 15) -> str:
    """A matched phone number cut after its ``limit``-th digit and before a date-like group that follows it, without trailing separators."""
    m = _DATEISH.search(num, 4)
    if m and sum(c.isdigit() for c in num[: m.start()]) >= 7:
        num = num[: m.start()]
    if " / " in num and sum(c.isdigit() for c in num[: num.index(" / ")]) >= 7:  # a second number after a slash is its own number
        num = num[: num.index(" / ")]
    seen = 0
    for i, ch in enumerate(num):
        if ch.isdigit():
            seen += 1
            if seen == limit:
                num = num[: i + 1]
                break
    return num.rstrip(" ./-(")


def _phone_len(text: str, start: int, length: int) -> int:
    """Length of a phone number the core found at ``start``, cut before a date that follows it (the core pattern can stop inside the date)."""
    window = text[start : start + length + 14]
    m = _DATEISH.search(window, 4)
    if m and m.start() <= length + 2 and sum(c.isdigit() for c in window[: m.start()]) >= 7:
        return len(window[: m.start()].rstrip(" ./-("))
    return length


def _card_spans(text: str, fp_: list[str]) -> list[tuple[str, int, int]]:
    """Card numbers on the folded text (so a no-break space, an en dash or a zero-width character between groups does not hide one): contiguous 13 to
    19 digits, or the groupings 4-4-4-4, 4-6-5 and 4-6-4, with a valid Luhn check; a 13-digit run also needs a card word before it or a leading 4."""
    folded = "".join(fp_)
    owner = [i for i, piece in enumerate(fp_) for _ in piece]
    out: list[tuple[str, int, int]] = []
    for rx in _CARD_SHAPES:
        for m in rx.finditer(folded):
            digits = re.sub(r"\D", "", m.group())
            if not _luhn(digits):
                continue
            if len(digits) == 13 and digits[0] != "4" and not _CARD_WORDS.search(folded[max(0, m.start() - 30) : m.start()]):
                continue
            start = owner[m.start()]
            if start > 0 and len(digits) <= (
                15 if text[start - 1] == "+" else 0
            ):  # an international phone number (a bracketed one has at most 12 digits, a card at least 13)
                continue
            out.append(("CARD", start, owner[m.end() - 1] + 1))
    return out


def _extra_pass(text: str, fp_: list[str]) -> list[tuple[str, int, int]]:
    """This module's OWN extra detectors (errata 94 and 99; the core copy stays identical): phone numbers (labelled, with a plus sign, a leading 1,
    a parenthesised area code, or a bare North American number right after a phone word), card numbers, and titled or labelled names."""
    out: list[tuple[str, int, int]] = []
    for m in _PHONE_LABELLED.finditer(text):
        n = _PHONE_NUM.match(text, m.end())
        if n:
            full, offset = n.group(), 0
            for i, part in enumerate(full.split(" / ")):  # a number after a slash is its own number (or a short extension of the first)
                num = _trim_phone(part)
                digits = sum(c.isdigit() for c in num)
                if i > 0 and _DATEISH.match(part):
                    pass  # a date after a slash
                elif digits >= 7 or (i > 0 and 3 <= digits <= 6 and re.fullmatch(r"[\d ()./-]+", num)):
                    out.append(("PHONE", n.start() + offset, n.start() + offset + len(num)))
                offset += len(part) + 3
    for m in _PHONE_PLUS.finditer(text):
        num = _trim_phone(m.group())
        if 8 <= sum(c.isdigit() for c in num):
            out.append(("PHONE", m.start(), m.start() + len(num)))
    for rx in (_NANP_BRACKET, _NANP_LEADING):
        out += [("PHONE", m.start(), m.end()) for m in rx.finditer(text)]
    out += [("PHONE", m.start(), m.end()) for m in _NANP_BARE.finditer(text) if _word_before(text, m.start(), _PHONE_WORD, 28, 12)]
    return out + _card_spans(text, fp_)


def _occurrences(text: str, needle: str) -> list[int]:
    out, k = [], text.find(needle)
    while k >= 0:
        out.append(k)
        k = text.find(needle, k + 1)
    return out


def _word_before(text: str, s: int, rx: re.Pattern[str], window: int, near: int | None = None) -> bool:
    w = text[max(0, s - window) : s].lower()
    return any(near is None or len(w) - m.end() <= near for m in rx.finditer(w))


def _narrow(core_kind: str, original: str, text: str, starts: list[int]) -> str | None:
    """None when the value is kept (hidden); otherwise the name of the narrowing count it falls under."""
    if core_kind == "PHONE":
        if any(c in original for c in "+()") or any(text[max(0, s - 2) : s].strip() in ("(", "+") for s in starts):
            return None
        if any(_word_before(text, s, _PHONE_WORD, 28, 12) for s in starts):
            return None
        return "narrowed_phone"
    if core_kind == "SSN":
        rx = _SSN_WORD
    elif core_kind == "AADHAAR":
        rx = _AADHAAR_WORD
    elif core_kind == "PAN":
        rx = _PAN_WORD
    elif core_kind == "NAME":
        ok = all(_DEAR_BEFORE.search(text[max(0, s - 40) : s].lower()) for s in starts)
        return None if ok else "narrowed_person"
    else:
        return None
    return None if any(_word_before(text, s, rx, 20 + 14) for s in starts) else "narrowed_id"


# ---------------------------------------------------------------------------------------------------------------- the detector seam
def _alnum_lower(s: str) -> str:
    return "".join(ch for ch in _fold_str(s) if ch in _ALNUM)


def _overlaps(money: list[tuple[int, int]], s: int, e: int) -> bool:
    return any(a < e and s < b for a, b in money)


def _lang_candidates(text: str) -> list[str]:
    """Digit runs near a masking-only bank word (cuenta, compte, ...): the same line, the first non-blank line below and a number-only line above,
    read as a bare bank word (8 or more digits)."""
    ic = invoicecheck
    if (
        "&" not in text and text.isascii() and not _LANG_WORD.search(_fold_str(text))
    ):  # cheap test first: the finder's fold is costly per line
        return []
    lines = [ic.fold_text(html.unescape(ln)) for ln in text.splitlines()]
    out: list[str] = []
    for i, ln in enumerate(lines):
        if not _LANG_WORD.search(ln) or ic.bank_word_in(ln):
            continue
        out += ic.line_candidates(ln, ic.THRESHOLD_BARE, "bare")
        j = ic.next_nonblank(lines, i)
        if j is not None:
            out += ic.line_candidates(lines[j], ic.THRESHOLD_BARE, "bare")
        if i and _NUMBER_ONLY.fullmatch(lines[i - 1].strip()):
            out += ic.line_candidates(lines[i - 1], ic.THRESHOLD_BARE, "strong")
    return out


def _bank_candidates(text: str, core: list[tuple[str, str]]) -> tuple[dict[str, str], set[str]]:
    """``(candidates, decoded_only)``. Candidate (digits, or lower-case letters and digits for an IBAN) -> hint of the core kind ('' when only the
    Intake finder saw it). ``decoded_only`` holds the candidates the finder found ONLY inside a decoded base64, percent or hex form: their text is
    not in the document as written, so they can never be located (errata 94)."""
    ic = invoicecheck
    # the plain candidates are needed only when the finder also decodes something (a base64, percent or hex form): otherwise nothing is decoded-only
    plain = set(ic.candidates(ic.fold_text(text), ic.fold_text(ic.camel_split(text)))) if len(ic.decoded_bodies(text)) > 1 else None
    out: dict[str, str] = {}
    decoded_only: set[str] = set()
    for f in invoicecheck.bank_detail_findings(text, ""):
        if f.kind == "number" and f.candidate:
            out.setdefault(f.candidate, "")
            if plain is not None and f.candidate not in plain:
                decoded_only.add(f.candidate)
    for c in _lang_candidates(text):
        out.setdefault(c, "")
        decoded_only.discard(c)
    for ck, original in core:
        if ck in _CORE_BANK:
            cand = _alnum_lower(original)
            if cand:
                out[cand] = _CORE_BANK[ck] if not out.get(cand) else out[cand]
                decoded_only.discard(cand)
    return out, decoded_only


def detect(text: str, *, residual: bool = True) -> Detection:
    """What would be hidden, left visible on purpose, or could not be located (design B1.0 table R1-R4).

    Only ``SelfCheckFailed`` leaves for the error types in ``_EXPECTED_ERRORS``; a ``MemoryError`` or ``OSError`` is not converted (callers wrap the
    call, as ``mask`` does). ``residual=False`` skips the second finder pass over the text with the hidden places blanked out (check a2 needs no
    blanking: it runs on a text that must have nothing left to hide, so its own pass is that check)."""
    if not isinstance(text, str):
        raise SelfCheckFailed("mask_failed")
    try:
        return _detect(text, residual)
    except _EXPECTED_ERRORS:
        pass
    raise SelfCheckFailed("mask_failed")


def _detect(text: str, residual: bool = True) -> Detection:
    fp_ = _fold_list(text)
    raw, look, alnum = _skeletons(text, fp_)
    lines = _Lines(text)
    money = money_spans(text)
    core = coreredact.find(text)
    cands, decoded_only = _bank_candidates(text, core)
    notes = dict.fromkeys(
        ("kept_money", "kept_id", "kept_name", "joined_unlocated", "narrowed_phone", "narrowed_id", "narrowed_person", "money_cut"), 0
    )
    spans: list[Span] = []
    kept: list[Kept] = []
    unlocated: list[str] = []
    hidden_cands: set[str] = set()
    located: set[str] = set()
    missing: list[str] = []

    kept_cands: set[str] = set()
    iban_word = "iban" in "".join(fp_)
    # every base64-looking run that decodes to a bank detail is hidden whole (the AI never sees it), whether or not the digits also stand in the text
    blobs = _base64_blobs(text) if len(invoicecheck.decoded_bodies(text)) > 1 else []
    for a_, b_, cs in blobs:
        if cs:
            spans.append(Span(a_, b_, "BANK", detector=DETECTOR_VERSION))
    # a run of percent-encoded characters that spells a candidate is hidden whole; a candidate proven by a run also has its plain copies hidden
    in_blob = set().union(*(cs for _, _, cs in blobs)) if blobs else set()
    proven = set(in_blob)
    pct_hide: set[tuple[int, int]] = set()
    if "%" in text:
        for a_, b_, digits in _percent_runs(text):
            for cand in cands:
                if cand.isdigit() and cand in digits:
                    pct_hide.add((a_, b_))
                    proven.add(cand)
    spans += [Span(a_, b_, "BANK", detector=DETECTOR_VERSION) for a_, b_ in sorted(pct_hide)]
    places = _iban_places(text, fp_, alnum, money)
    place_len = {(a_, b_): len(pl) for a_, b_, pl in places}
    place_hidden = [(a_, b_) for a_, b_, pl in places if not _iban_reference(pl, iban_word)]
    place_left = [(a_, b_) for a_, b_, pl in places if _iban_reference(pl, iban_word)]
    spans += [Span(a_, b_, "IBAN", detector=DETECTOR_VERSION) for a_, b_ in place_hidden]
    for cand, hint in cands.items():
        if not cand.isdigit():
            # an IBAN-shaped candidate the finder reports (it may be padded with the next line or a date): covered when its leading part stands in a
            # place decided above (hidden or left alone), unless it is a valid IBAN that runs beyond that place (an odd separator): then it is hidden whole
            rel = _find(alnum, fp_, cand, ends=False)
            ranges = place_hidden + place_left
            hit = [next((r for r in ranges if r[0] <= o[0] < r[1]), None) for o in rel]
            beyond = [(o, h) for o, h in zip(rel, hit, strict=True) if h and o[1] > h[1]]
            # a candidate that runs beyond its place is more of the account (hidden whole) when it is a valid IBAN, or when the place is long enough
            # to be an IBAN of its own and what follows is no date and no word; a short place (a VAT or PO reference) is padded by the finder
            more = (_iban_valid(cand) and bool(beyond)) or any(
                place_len[h] >= _IBAN_MIN_BEYOND and not _padding_after(text, h[1]) for _, h in beyond
            )
            if rel and all(hit) and not more:
                continue
        if cand in decoded_only and cand not in proven:  # found only inside a hex form: it cannot be located, so the item is held back
            unlocated.append(cand)
            continue
        if cand.isdigit():
            occs = sorted(set(_find(raw, fp_, cand)) | set(_find(look, fp_, cand)))
        else:
            occs = sorted(set(_find(alnum, fp_, cand)))
        if not occs:
            if cand not in decoded_only:  # a candidate only a run holds is covered by the run
                missing.append(cand)
            continue
        located.add(cand)
        force = cand in proven  # a base64 or percent run proves the number: every plain copy is hidden too, with no id-token excuse
        non_money, is_id = [], {}
        for o in occs:
            m = _overlaps(money, *o)
            if m:
                kept.append(Kept(o[0], o[1], "money"))
                notes["kept_money"] += 1
                continue
            li = lines.of(o[0])
            is_id[o] = (not force) and (not lines.ctx[li]) and _id_shaped(text, *o)
            non_money.append(o)
        if not non_money or all(is_id[o] for o in non_money):
            kept_cands.add(cand)
        if non_money and all(is_id[o] for o in non_money):  # R3
            for o in non_money:
                kept.append(Kept(o[0], o[1], "id_token"))
                notes["kept_id"] += 1
        elif non_money:  # R4
            hidden_cands.add(cand)
            for o in non_money:
                if cand.isdigit():
                    kind = _bank_kind(fp_, lines.starts[lines.of(o[0])], o[0], hint)
                else:
                    kind = "IBAN"
                spans.append(Span(o[0], o[1], kind, detector=DETECTOR_VERSION))
        # else R2: every occurrence was a money occurrence and is already in ``kept``

    if missing:  # R1 / R1b
        pieces_of = _wp3_pieces(text)
        for cand in missing:
            pieces = pieces_of.get(cand, ())  # R1b only for a located block this joined whole was made of; a single block has none
            if not any(d in pieces for d in located):
                unlocated.append(cand)
                continue
            notes["joined_unlocated"] += 1
            if any(len(p) >= 3 and p not in hidden_cands for p in pieces):
                unlocated.append(cand)

    seen_core: set[tuple[str, str]] = set()
    nonbank: list[tuple[str, int, int]] = []
    own_names = [("NAME", m.group(1)) for m in _NAME_FIND.finditer(text)]
    for ck, original in [*core, *own_names]:
        kind = _CORE_KIND.get(ck)
        if kind is None or not original or (ck, original) in seen_core:
            continue
        seen_core.add((ck, original))
        starts = _word_occurrences(text, original) if ck == "NAME" else _occurrences(text, original)
        if not starts:
            unlocated.append(original)
            continue
        why = _narrow(ck, original, text, starts)
        if why:
            notes[why] += 1
            if why == "narrowed_person":
                notes["kept_name"] += 1
            continue
        nonbank += [(kind, s, s + (_phone_len(text, s, len(original)) if ck == "PHONE" else len(original))) for s in starts]

    nonbank += [x for x in _extra_pass(text, fp_) if not (x[0] == "CARD" and _overlaps(money, x[1], x[2]))]
    over = False
    for kind, s, e in nonbank:
        if kind in _FREE_TEXT_KINDS and money:
            pieces, cur = [], s
            hit = False
            for a, b in sorted(x for x in money if x[0] < e and s < x[1]):
                hit = True
                if a > cur:
                    pieces.append((cur, a))
                cur = max(cur, b)
            if hit:
                notes["money_cut"] += 1
                if cur < e:
                    pieces.append((cur, e))
                for a, b in pieces:
                    if re.search(r"[0-9]{4}", text[a:b]):
                        over = True
                    if any(c.isdigit() for c in text[a:b]):  # a fragment with no digit (a bare + or bracket) is not hidden
                        spans.append(Span(a, b, kind, detector=DETECTOR_VERSION))
                continue
        spans.append(Span(s, e, kind, detector=DETECTOR_VERSION))
    if residual:
        unlocated += _residual_copies(text, spans, kept, place_left)
    return Detection(tuple(spans), tuple(unlocated), tuple(kept), over, notes)


def _word_occurrences(text: str, name: str) -> list[int]:
    """Places where ``name`` stands as a whole word (``Mark`` is not found inside ``Marketing``)."""
    return [m.start() for m in re.finditer(r"(?<![A-Za-z])" + re.escape(name) + r"(?![A-Za-z])", text)]


def _padded_tail(text: str, ends: list[int], rest: str) -> bool:
    """True when ``rest`` (lower-case letters and digits) is only part of the padding that follows a hidden place: a date or a word without a
    digit, plus the amount after it, read on the folded text."""
    for b in ends:
        if _padding_after(text, b):
            tail = re.sub(r"[^0-9a-z]", "", _fold_str(text[b : b + 60]).lower())
            it = iter(tail)
            if all(ch in it for ch in rest):  # rest is made of characters of the tail, in order (the finder drops some)
                return True
    return False


def _residual_copies(text: str, spans: list[Span], kept: list[Kept], left_alone: list[tuple[int, int]]) -> list[str]:
    """With every hidden place AND every place kept on purpose (an amount, an id token) blanked out, the Intake finder must find no bank candidate at
    all: whatever it still sees is a copy that was not hidden (an HTML entity inside the digits, a clean copy beside an obfuscated one). Those are
    unlocated and the item is held back. An IBAN-shaped candidate whose leading part stands in a place left alone (a short reference the finder padded
    with the next line or a date) is not a copy."""
    blank = list(text)
    for a, b in [(sp.start, sp.end) for sp in spans] + [(k.start, k.end) for k in kept]:
        for i in range(a, b):
            if blank[i] not in "\n\r":
                blank[i] = "x"
    view = "".join(blank)
    found = [f.candidate for f in invoicecheck.bank_detail_findings(view, "") if f.kind == "number" and f.candidate]
    out: list[str] = []
    alnum_view = None
    for c in dict.fromkeys(found):
        if set(c) <= {"x"}:  # the blanking filler itself (the finder reads any 15 to 34 characters after the word iban)
            continue
        rest = c.lstrip("x")
        if rest and len(c) - len(rest) >= 8 and _padded_tail(text, [sp.end for sp in spans], rest):
            continue  # the blanked place plus the date or word written right after it (the finder pads a place with what follows)
        if not c.isdigit() and left_alone:
            if alnum_view is None:
                fp_view = _fold_list(view)
                alnum_view = (_skeletons(view, fp_view)[2], fp_view)
            rel = _find(alnum_view[0], alnum_view[1], c, ends=False)
            if rel and all(any(a_ <= o[0] < b_ for a_, b_ in left_alone) for o in rel):
                continue
        out.append(c)
    return out


def _percent_runs(text: str) -> list[tuple[int, int, str]]:
    """Runs of three or more percent-encoded characters: ``(start, end, the digits they spell)``."""
    return [(m.start(), m.end(), re.sub(r"\D", "", unquote(m.group()))) for m in re.finditer(r"(?:%[0-9A-Fa-f]{2}){3,}", text)]


def _base64_blobs(text: str) -> list[tuple[int, int, set[str]]]:
    """Runs of base64-looking text that decode to something holding a bank candidate: ``(start, end, candidates)``."""
    out = []
    for m in re.finditer(r"[A-Za-z0-9+/_-]{16,}={0,2}", text):
        cs: set[str] = set()
        for decoded in decoded_extras(m.group()):
            cs |= {f.candidate for f in invoicecheck.bank_detail_findings(decoded, "") if f.kind == "number" and f.candidate}
        if cs:
            out.append((m.start(), m.end(), cs))
    return out


def _wp3_pieces(text: str) -> dict[str, set[str]]:
    """For each joined run of the Intake finder: the digit blocks it was joined from (needed to tell whether a short block stays visible)."""
    out: dict[str, set[str]] = {}
    ic = invoicecheck
    for ln in ic.fold_text(text).split("\n"):
        for v in {ln, ic.digitise(ln)}:
            for _, blocks in ic.digit_runs(v):
                if len(blocks) > 1:
                    out.setdefault("".join(blocks), set()).update(blocks)
    return out


# ---------------------------------------------------------------------------------------------------------------- marks
_KINDS_RX = "|".join(PRIORITY)
_MARK = re.compile(r"<(" + _KINDS_RX + r")_([0-9]+)>")
_MARK_LIKE = re.compile(
    r"<\s*(" + _KINDS_RX + r")\s*_\s*(\d+)\s*>", re.IGNORECASE
)  # only the kinds this module issues (a text like <INV_2026> is no mark)


def canonical(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKC", text) if unicodedata.category(c) != "Cf")


def _merge(spans: list[Span]) -> list[Span]:
    out: list[Span] = []
    for s in sorted(spans, key=lambda x: (x.start, -x.end)):
        if out and s.start <= out[-1].end:
            last = out[-1]
            kind = min(last.kind, s.kind, key=PRIORITY.index)
            out[-1] = Span(last.start, max(last.end, s.end), kind, detector=last.detector)
        else:
            out.append(s)
    return out


def _mask(text: str, key: bytes) -> Masked:
    if len(text) > MASK_MAX_DOC_CHARS or any(len(ln) > MASK_MAX_LINE_CHARS for ln in text.split("\n")):
        raise SelfCheckFailed("mask_too_large")
    if any(
        unicodedata.category(c) == "Cc" and c not in _ALLOWED_CONTROLS for c in text
    ):  # an escape sequence can split a number past the finders
        raise SelfCheckFailed("mask_residual")
    if _MARK_LIKE.search(canonical(text)):
        raise SelfCheckFailed("mark_like_text")
    det = detect(text)
    if det.unlocated:
        raise SelfCheckFailed("mask_residual")
    if det.money_overlap:
        raise SelfCheckFailed("mask_money_overlap")
    merged = _merge(list(det.spans))
    marks: dict[str, tuple[str, str]] = {}  # surface string -> (mark, kind of its first appearance)
    counters: dict[str, int] = dict.fromkeys(PRIORITY, 0)
    final: list[Span] = []
    out: list[str] = []
    pos = 0
    for s in merged:
        surface = text[s.start : s.end]
        if surface not in marks:
            counters[s.kind] += 1
            marks[surface] = (f"<{s.kind}_{counters[s.kind]}>", s.kind)
        ph, kind = marks[surface]
        final.append(Span(s.start, s.end, kind, ph, fp(key, surface), s.detector))
        out += [text[pos : s.start], ph]
        pos = s.end
    out.append(text[pos:])
    model_text = "".join(out)
    if len(model_text) > MASKED_MAX_CHARS:
        raise SelfCheckFailed("mask_too_large")
    kept_texts = sorted({text[k.start : k.end] for k in det.kept_visible}, key=len, reverse=True)
    counts = dict(det.notes)
    counts["total"] = len(final)
    counts["distinct"] = len(marks)
    for kind in PRIORITY:
        counts[kind] = sum(1 for _, k in marks.values() if k == kind)
    return Masked(model_text, tuple(final), counts, det.notes["money_cut"], det.kept_visible, tuple(kept_texts))


def mask(text: str, key: bytes) -> Masked:
    try:
        return _mask(text, key)
    except SelfCheckFailed:
        raise
    except Exception:
        pass  # the code is raised below, outside the handler, so no chained exception (and no value) travels with it
    raise SelfCheckFailed("mask_failed")


def issued(masked: Masked) -> frozenset[str]:
    return frozenset(s.placeholder for s in masked.spans)


NEUTRAL = "flags"  # filler for an issued mark: at most 7 characters, no bank word, and matching no core secret rule (a test runs every one of them);
# a one-letter filler such as ``x`` after ``password=`` would be taken as a secret value and replaced everywhere, failing check a2


def neutralise(text: str, masked: Masked) -> str:
    """Every mark this document was given replaced by a plain filler word, so the mark words (BANK, ...) cannot be taken for bank words."""
    if not isinstance(masked, Masked) or not isinstance(text, str):
        raise SelfCheckFailed("mask_failed")
    ok = issued(masked)
    return _MARK.sub(lambda m: NEUTRAL if m.group(0) in ok else m.group(0), text)


def check_model_text(masked: Masked) -> None:
    """Checks a3 and a2 on the finished model text. Raises ``SelfCheckFailed``."""
    if not isinstance(masked, Masked):
        raise SelfCheckFailed("mask_failed")
    marks = [m.group(0) for m in _MARK.finditer(masked.text)]
    look = [f"<{m.group(1)}_{m.group(2)}>" for m in _MARK_LIKE.finditer(canonical(masked.text))]
    ok = issued(masked)
    if sorted(marks) != sorted(look) or any(m not in ok for m in marks) or len(set(marks)) != len(ok):
        raise SelfCheckFailed("mask_failed")
    nt = neutralise(masked.text, masked)
    det = detect(nt, residual=False)
    # a span that is exactly the filler is a mark standing where a value was (a URL password, for example): the core rule fires on any word there
    if det.unlocated or any(nt[sp.start : sp.end] != NEUTRAL for sp in det.spans):
        raise SelfCheckFailed("mask_residual")
    if det.money_overlap:
        raise SelfCheckFailed("mask_money_overlap")


# ---------------------------------------------------------------------------------------------------------------- spellings and search
SPELLING_NAMES = (
    "raw",
    "casefold",
    "nfkc",
    "nfkc_casefold",
    "json_ascii",
    "json_ascii_twice",
    "json_utf8",
    "json_utf8_twice",
    "html_escape",
    "percent",
    "percent_plus",
    "base64",
    "base64_url",
    "hex_lower",
    "hex_upper",
)
_SHORT_NAMES = ("raw", "casefold")  # below 6 characters only these, and only as whole tokens


def named_spellings(value: str) -> tuple[tuple[str, str], ...]:
    """``(name, spelling)`` of a SURFACE string, names from ``SPELLING_NAMES`` in that order, each name once and each spelling text once (the first
    name wins). Raw and casefold always; the derived forms from 6 characters (design B5)."""
    n = unicodedata.normalize("NFKC", value)
    raw = value.encode("utf-8", "surrogatepass")
    forms = {
        "raw": value,
        "casefold": value.casefold(),
        "nfkc": n,
        "nfkc_casefold": n.casefold(),
        "json_ascii": json.dumps(value, ensure_ascii=True)[1:-1],
        "json_ascii_twice": json.dumps(json.dumps(value, ensure_ascii=True))[1:-1],
        "json_utf8": json.dumps(value, ensure_ascii=False)[1:-1],
        "json_utf8_twice": json.dumps(json.dumps(value, ensure_ascii=False))[1:-1],
        "html_escape": html.escape(value),
        "percent": quote_from_bytes(raw, safe=""),
        "percent_plus": quote_from_bytes(raw, safe=" ").replace(" ", "+"),
        "base64": base64.b64encode(raw).decode().rstrip("="),
        "base64_url": base64.urlsafe_b64encode(raw).decode().rstrip("="),
        "hex_lower": raw.hex(),
        "hex_upper": raw.hex().upper(),
    }
    out, seen = [], set()
    for name in SPELLING_NAMES if len(value) >= 6 else _SHORT_NAMES:
        text = forms[name]
        if text and text not in seen:
            seen.add(text)
            out.append((name, text))
    return tuple(out)


def spellings(value: str) -> tuple[str, ...]:
    return tuple(t for _, t in named_spellings(value))


def _kept_intervals(haystack: str, kept_texts: tuple[str, ...]) -> list[tuple[int, int]]:
    """Every place in ``haystack`` where a kept-visible string stands (also as a JSON body writes it)."""
    out: list[tuple[int, int]] = []
    for t in kept_texts:
        for form in {t, json.dumps(t, ensure_ascii=True)[1:-1], json.dumps(t, ensure_ascii=False)[1:-1]}:
            k = haystack.find(form) if form else -1
            while k >= 0:
                out.append((k, k + len(form)))
                k = haystack.find(form, k + 1)
    return out


def _lower1(text: str) -> str:
    """Lower case that never changes the length (a character whose lower case is longer stays as it is), so positions stay valid."""
    return "".join(c.lower() if len(c.lower()) == 1 else c for c in text)


def find_hidden(haystack: str, value: str, kept_texts: tuple[str, ...] = (), low: str | None = None) -> tuple[tuple[int, int, str], ...]:
    """POSITION-based search (errata 88): ``(start, end, spelling name)`` of every place a listed spelling of ``value`` stands in the UNCUT
    ``haystack``. A hit is dropped only when its whole span lies inside ONE occurrence of a kept-visible string. The haystack is never rewritten.
    Below 6 characters a spelling counts only as a whole token (letters and digits on neither side). ``low`` is ``_lower1(haystack)`` when the
    caller searches many values in one haystack."""
    low = _lower1(haystack) if low is None or len(low) != len(haystack) else low
    hits: list[tuple[int, int, str]] = []
    for name, sp in named_spellings(value):
        if len(value) < 6:
            for m in re.finditer(r"(?<![0-9A-Za-z])" + re.escape(sp) + r"(?![0-9A-Za-z])", haystack, re.IGNORECASE):
                hits.append((m.start(), m.end(), name))
            continue
        ci = name in ("raw", "casefold", "nfkc", "nfkc_casefold")  # these forms also match in any letter case
        for src, needle in ((haystack, sp), (low, _lower1(sp) if ci else None)):
            if needle is None:
                continue
            k = src.find(needle)
            while k >= 0:
                hits.append((k, k + len(needle), name))
                k = src.find(needle, k + 1)
    if not hits:
        return ()
    kept = _kept_intervals(haystack, kept_texts)
    return tuple(sorted({h for h in hits if not any(a <= h[0] and h[1] <= b for a, b in kept)}))


def surfaces(masked: Masked, document_text: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(document_text[s.start : s.end] for s in masked.spans))


def hidden_hits(haystack: str, values: tuple[str, ...], kept_texts: tuple[str, ...] = ()) -> int:
    """How many of ``values`` have a hit (position-based, see ``find_hidden``)."""
    low = _lower1(haystack)
    return sum(1 for v in values if find_hidden(haystack, v, kept_texts, low))


# ---------------------------------------------------------------------------------------------------------------- the body check (a1)
def _strings(node: Any):
    stack = [node]
    while stack:
        cur = stack.pop()
        if isinstance(cur, str):
            yield cur
        elif isinstance(cur, dict):
            stack.extend(cur.keys())
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)


class BodyCheck:
    """Checks the exact bytes about to be sent against a fresh recompute (a1). Attributes are the ``model.BodyCheck`` protocol."""

    def __init__(self, parsed: Any, masked: Masked, key: bytes) -> None:
        self._document_text = parsed.text
        self._source_sha256 = parsed.source_sha256
        self._key = key
        self.masked = masked
        self.last_code: str | None = None

    document_text = property(lambda self: self._document_text)
    source_sha256 = property(lambda self: self._source_sha256)
    key = property(lambda self: self._key)

    def refuse(self, code: str) -> None:
        if code not in SELFCHECK_CODES:
            raise ValueError("unknown self-check code")
        self.last_code = code

    def __call__(self, body: bytes) -> str | None:
        self.last_code = None
        try:
            return self._check(body)
        except SelfCheckFailed as e:
            self.last_code = e.code
            return "body_unsafe"
        except Exception:
            self.last_code = "mask_failed"
            return "body_unsafe"

    def _check(self, body: bytes) -> str | None:
        data = strictjson.loads(body)
        fresh = mask(self._document_text, self._key)
        if fresh.text != self.masked.text or fresh.spans != self.masked.spans:
            raise SelfCheckFailed("mask_failed")
        vals = surfaces(fresh, self._document_text)
        for h in (body.decode("utf-8"), "\n".join(_strings(data))):
            if hidden_hits(h, vals, fresh.kept_visible_texts):
                raise SelfCheckFailed("body_has_original")
        if not isinstance(data, dict):
            raise SelfCheckFailed("mask_failed")
        if data.get("fake") is True:
            if data.get("doc_sha") != self._source_sha256:
                raise SelfCheckFailed("doc_sha_mismatch")
            same = data.get("text") == fresh.text
        else:
            msgs = data.get("messages")
            content = msgs[0].get("content") if isinstance(msgs, list) and msgs and isinstance(msgs[0], dict) else None
            same = content == BODY_START + fresh.text + BODY_END
        if not same:
            raise SelfCheckFailed("mask_failed")
        return None

    def __repr__(self) -> str:
        return "BodyCheck()"


# ---------------------------------------------------------------------------------------------------------------- restore (b, restore, field rule, c)
def _child(schema: Any, name: str) -> Any:
    props = schema.get("properties") if isinstance(schema, dict) else None
    return props.get(name) if isinstance(props, dict) else None


def _walk(node: Any, schema: Any, shown: str, generic: str, visit, key_for_detail: bytes = b"", depth: int = 0) -> Any:
    """Rebuilds ``node`` calling ``visit(text, shown, generic)`` on each string value; any key the schema does not know is written as ``other``."""
    if depth > 64:
        raise SelfCheckFailed("mask_failed")
    if isinstance(node, str):
        return visit(node, shown, generic)
    if isinstance(node, list):
        item = schema.get("items") if isinstance(schema, dict) else None
        return [_walk(v, item, f"{shown}[{i}]", generic + "[]", visit, key_for_detail, depth + 1) for i, v in enumerate(node)]
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            sub = _child(schema, k) if isinstance(k, str) else None
            name = k if sub is not None else "other"
            if isinstance(k, str) and _MARK_LIKE.search(canonical(k)):
                e = SelfCheckFailed("forged_mark")
                e.detail = (f"{shown}.{name}".lstrip("."), len(k), fp(key_for_detail, k))
                raise e
            out[k] = _walk(v, sub, f"{shown}.{name}".lstrip("."), f"{generic}.{name}".lstrip("."), visit, key_for_detail, depth + 1)
        return out
    return node


def restore(fields: Any, masked: Masked, key: bytes, document_text: str) -> Restored:
    """Check (b), put the values back, the field rule and check (c), in that order. Raises ``SelfCheckFailed`` (forged_mark,
    hidden_value_in_field or restore_mismatch)."""
    ok = issued(masked)
    first: dict[str, Span] = {}
    for s in masked.spans:
        first.setdefault(s.placeholder, s)
    schema = validators.RECORD_SCHEMA

    def check_b(s: str, shown: str, generic: str) -> str:
        strict = sorted(m.group(0) for m in _MARK.finditer(s))
        look = sorted(f"<{m.group(1)}_{m.group(2)}>" for m in _MARK_LIKE.finditer(canonical(s)))
        if strict != look or any(m not in ok for m in strict):
            e = SelfCheckFailed("forged_mark")
            e.detail = (shown, len(s), fp(key, s))
            raise e
        return s

    _walk(fields, schema, "", "", check_b, key)
    items: dict[str, tuple[str, str, str, str]] = {}
    count = [0]

    def put(s: str, shown: str, generic: str) -> str:
        def sub(m: re.Match[str]) -> str:
            sp = first[m.group(0)]
            value = document_text[sp.start : sp.end]
            if sp.kind not in _FREE_TEXT_KINDS or generic not in _FREE_TEXT_PATHS:
                e = SelfCheckFailed("hidden_value_in_field")
                e.detail = (shown, len(value), sp.fingerprint)
                raise e
            fr = fp(key, value)
            items.setdefault(m.group(0), (m.group(0), sp.fingerprint, fr, "same" if fr == sp.fingerprint else "MISMATCH"))
            count[0] += 1
            return value

        return _MARK.sub(sub, s)

    out = _walk(fields, schema, "", "", put, key)
    left = [0]

    def count_left(s: str, shown: str, generic: str) -> str:
        left[0] += len(_MARK.findall(s))
        return s

    _walk(out, schema, "", "", count_left, key)
    fresh = None
    try:
        fresh = mask(document_text, key)
    except SelfCheckFailed:
        pass
    if fresh is None:
        bad = SelfCheckFailed("restore_mismatch")
        bad.detail = tuple(items.values())
        raise bad

    def sig(m: Masked) -> tuple:
        return (m.text, tuple((s.placeholder, s.kind, s.start, s.end, s.fingerprint) for s in m.spans))

    if sig(fresh) != sig(masked) or left[0] or any(v[3] != "same" for v in items.values()):
        bad = SelfCheckFailed("restore_mismatch")
        bad.detail = tuple(items.values())  # (mark, stored fingerprint, restored fingerprint, "same"/"MISMATCH") for the trace
        raise bad
    return Restored(out, tuple(items.values()), count[0], 0, 0)


# ---------------------------------------------------------------------------------------------------------------- WARN scan
_D8 = re.compile(r"[0-9]{8,}")
_D13 = re.compile(r"[0-9](?:[ -]?[0-9]){12,18}")
_MIXED = re.compile(r"[A-Za-z0-9]{20,}")


def residual_warn(text: str, masked: Masked) -> dict[str, int]:
    """Counts of things in the model text that still LOOK sensitive, plus the recognised-but-sent counts. A hint for a person, not a proof."""
    t = neutralise(text, masked)
    out = {
        "digit8": len(_D8.findall(t)),
        "at_sign": t.count("@"),
        "digit13_19": len(_D13.findall(t)),
        "mixed20": sum(1 for w in _MIXED.findall(t) if any(c.isdigit() for c in w) and any(c.isalpha() for c in w)),
    }
    for k in ("kept_money", "kept_id", "kept_name", "joined_unlocated", "narrowed_phone", "narrowed_id", "narrowed_person"):
        out[k] = masked.counts.get(k, 0)
    return out


# ---------------------------------------------------------------------------------------------------------------- the bank check for held-back invoices
_BANK_WORDS = re.compile(
    r"sort\W{0,3}code|routing|swift|clearing|konto|branch\W{0,3}code|iban|(?:account|acct|acc|a/c)\W{0,3}(?:no|num|number|nr|nbr|id|#)"
    r"|(?<![a-z])(?:aba|bic|bsb|blz|ifsc|clabe|cuenta|compte|conto|rekening)(?![a-z])|bank|acct|acc|a/c"
)


def _words_near(text: str, cands: list[str]) -> tuple[str, ...]:
    fp_ = _fold_list(text)
    raw, look, alnum = _skeletons(text, fp_)
    lines = _Lines(text)
    found: set[str] = set()
    for cand in cands:
        occ = _find(raw, fp_, cand) if cand.isdigit() else _find(alnum, fp_, cand)
        for s, _ in occ or (_find(look, fp_, cand) if cand.isdigit() else []):
            i = lines.of(s)
            for j in (i, *range(i - 1, max(-1, i - 4), -1), i + 1):
                if 0 <= j < len(lines.lines):
                    ws = [
                        re.sub(r"\s+", " ", re.sub(r"[^a-z/# ]", " ", m.group(0))).strip()
                        for m in _BANK_WORDS.finditer(_fold_str(lines.lines[j]))
                    ]
                    if ws:
                        found.update(w for w in ws if w)
                        break
    return tuple(sorted(found))


def bank_check_outcome(document_text: str, suppliers: Any) -> tuple[str, str | None, tuple[str, ...], int]:
    """``(outcome, supplier key, bank words, n found)`` computed on the ORIGINAL text (design B5: five outcomes). The words are bank words, never numbers."""
    key = invoicecheck.supplier_on_file(document_text, suppliers)
    found = invoicecheck.bank_detail_findings(document_text, "")
    if key is None:
        return "not_run", None, (), len(found)
    on_file = suppliers[key]
    if not on_file.strip() or not invoicecheck.on_file_components(on_file):
        return "no_details_on_file", key, (), len(found)
    diff = invoicecheck.bank_detail_findings(document_text, on_file)
    if diff:
        return "changed", key, _words_near(document_text, [f.candidate for f in diff if f.kind == "number"]), len(diff)
    if not found:
        return "none_found", key, (), 0
    return "ok", key, (), len(found)
