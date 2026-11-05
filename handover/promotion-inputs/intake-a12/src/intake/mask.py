"""Hide sensitive values before the AI service, put them back after (design WP2c B1-B5).

Detectors: the Intake bank finder (``invoicecheck.bank_detail_findings``) and the byte copy of the core redactor (``coreredact.find``). New code
here is only the LOCATION and DECISION layer: where in the original text a recognised value sits (one pass builds a digit skeleton and an index of
6-digit prefixes; no regular expression runs per candidate), and rules R1 to R4 of design B1.0 (the single rule table).

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
from urllib.parse import quote, quote_plus

from . import coreredact, invoicecheck, strictjson, validators
from .checks import fold as _checks_fold
from .ground import money_spans
from .selfcheck_codes import SELFCHECK_CODES, SelfCheckFailed

MASK_MAX_LINE_CHARS = 2000  # a longer line (between \n characters) is held back before any detector runs (OPINION, B1.9)
MASK_MAX_DOC_CHARS = 20000  # a longer document is held back (the reader already caps it at the policy value; this is the ReDoS bound)
MASKED_MAX_CHARS = 40000  # a longer model text is held back (mask_too_large); budget.min_limit_micro derives its worst case from it
MODE = "known"
DETECTOR_VERSION = "wp2c-1;core-ce70eb5;wp3-lang1"
BODY_START, BODY_END = "<<<INVOICE_START>>>", "<<<INVOICE_END>>>"  # same text as model_anthropic (a test pins the equality)
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
    """The Intake fold (``invoicecheck._f``) applied to ONE character: NFKD, invisible characters deleted, confusables, ``checks.fold``, casefold,
    look-alikes, dashes, slashes, line breaks. A test compares it with ``_f`` character by character over a test alphabet."""
    ic = invoicecheck
    t = unicodedata.normalize("NFKD", c).translate(ic._DELETE).translate(ic._CONF)
    t = _checks_fold(t).casefold()
    t = t.translate(ic._CONF).translate(ic._LOOKALIKE).translate(ic._DASHES).translate(ic._SLASHES).translate(ic._BREAKS)
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

    __slots__ = ("bad", "chars", "idx", "outside", "pref")

    def __init__(self, chars: str, idx: list[int], bad: list[int], outside: frozenset[str]) -> None:
        self.chars, self.idx, self.bad, self.outside = chars, idx, bad, outside
        self.pref: dict[str, list[int]] = {}
        for k in range(len(chars) - 5):
            self.pref.setdefault(chars[k : k + 6], []).append(k)


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


def _find(sk: _Skel, fp_: list[str], cand: str) -> list[tuple[int, int]]:
    """Every place in the original text where ``cand`` appears as a whole value (gap rule and end rule of design B1.0)."""
    n = len(cand)
    out: list[tuple[int, int]] = []
    if n == 0 or n > len(sk.chars):
        return out
    if n >= 6:
        starts: Any = sk.pref.get(cand[:6], ())
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
        if _outside_ok(fp_, a, -1, sk.outside) and _outside_ok(fp_, b, 1, sk.outside):
            out.append((a, b + 1))
    return out


# ---------------------------------------------------------------------------------------------------------------- lines and context
_NUMBER_ONLY = re.compile(r"[0-9][0-9 ./,-]*")
_ROUTING_W = re.compile(r"sort\W{0,3}code|routing|branch\W{0,3}code|(?<![a-z])(?:aba|bsb|ifsc|blz|clabe|transit|clearing)(?![a-z])")
_OTHER_W = re.compile(r"acct|acc|a/c|bank|iban|konto|swift|bic|cuenta|compte|conto|rekening")
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
        bw = [invoicecheck.bank_word_in(ln) for ln in self.lines]
        folded = [_fold_str(ln).strip() for ln in self.lines]
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
    return any(c.isalpha() for c in around) and not invoicecheck.bank_word_in(text[lo:hi])


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
_PHONE_WORD = re.compile(r"(?<![a-z])(?:tel|phone|mobile|mob|fax)(?![a-z])|(?<![a-z])ph[.:]")
_SSN_WORD = re.compile(r"(?<![a-z])(?:ssn|social security|tin|ein)(?![a-z])")
_AADHAAR_WORD = re.compile(r"(?<![a-z])(?:aadhaar|uid)(?![a-z])")
_PAN_WORD = re.compile(r"(?<![a-z])pan(?![a-z])")
_DEAR_BEFORE = re.compile(r"(?<![a-z])dear\W+(?:(?:mr|mrs|ms|miss|dr|prof)\.?\s+)?$")


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
        if any(c in original for c in "+()") or any(_word_before(text, s, _PHONE_WORD, 28, 12) for s in starts):
            return None
        return "narrowed_phone"
    if core_kind == "SSN":
        rx = _SSN_WORD
    elif core_kind == "AADHAAR":
        rx = _AADHAAR_WORD
    elif core_kind == "PAN":
        rx = _PAN_WORD
    elif core_kind == "NAME":
        ok = all(_DEAR_BEFORE.search(text[max(0, s - 24) : s].lower()) for s in starts)
        return None if ok else "narrowed_person"
    else:
        return None
    return None if any(_word_before(text, s, rx, 20 + 14) for s in starts) else "narrowed_id"


# ---------------------------------------------------------------------------------------------------------------- the detector seam
def _alnum_lower(s: str) -> str:
    return "".join(ch for ch in _fold_str(s) if ch in _ALNUM)


def _overlaps(money: list[tuple[int, int]], s: int, e: int) -> bool:
    return any(a < e and s < b for a, b in money)


def _bank_candidates(text: str, core: list[tuple[str, str]]) -> dict[str, str]:
    """Candidate (digits, or lower-case letters and digits for an IBAN) -> hint of the core kind ('' when only the Intake finder saw it)."""
    out: dict[str, str] = {}
    for f in invoicecheck.bank_detail_findings(text, ""):
        if f.kind == "number" and f.candidate:
            out.setdefault(f.candidate, "")
    for ck, original in core:
        if ck in _CORE_BANK:
            cand = _alnum_lower(original)
            if cand:
                out[cand] = _CORE_BANK[ck] if not out.get(cand) else out[cand]
    return out


def detect(text: str) -> Detection:
    """What would be hidden, left visible on purpose, or could not be located (design B1.0 table R1-R4)."""
    fp_ = _fold_list(text)
    raw, look, alnum = _skeletons(text, fp_)
    lines = _Lines(text)
    money = money_spans(text)
    core = coreredact.find(text)
    cands = _bank_candidates(text, core)
    notes = dict.fromkeys(
        ("kept_money", "kept_id", "kept_name", "joined_unlocated", "narrowed_phone", "narrowed_id", "narrowed_person", "money_cut"), 0
    )
    spans: list[Span] = []
    kept: list[Kept] = []
    unlocated: list[str] = []
    hidden_cands: set[str] = set()
    located: set[str] = set()
    missing: list[str] = []

    for cand, hint in cands.items():
        if cand.isdigit():
            occs = sorted(set(_find(raw, fp_, cand)) | set(_find(look, fp_, cand)))
        else:
            occs = sorted(set(_find(alnum, fp_, cand)))
        if not occs:
            missing.append(cand)
            continue
        located.add(cand)
        non_money, is_id = [], {}
        for o in occs:
            m = _overlaps(money, *o)
            if m:
                kept.append(Kept(o[0], o[1], "money"))
                notes["kept_money"] += 1
                continue
            li = lines.of(o[0])
            is_id[o] = (not lines.ctx[li]) and _id_shaped(text, *o)
            non_money.append(o)
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
            subs = [d for d in located if d != cand and d in cand]
            if not subs:
                unlocated.append(cand)
                continue
            notes["joined_unlocated"] += 1
            if any(len(p) >= 3 and p not in hidden_cands for p in pieces_of.get(cand, ())):
                unlocated.append(cand)

    seen_core: set[tuple[str, str]] = set()
    nonbank: list[tuple[str, int, int]] = []
    for ck, original in core:
        kind = _CORE_KIND.get(ck)
        if kind is None or not original or (ck, original) in seen_core:
            continue
        seen_core.add((ck, original))
        starts = _occurrences(text, original)
        if not starts:
            unlocated.append(original)
            continue
        why = _narrow(ck, original, text, starts)
        if why:
            notes[why] += 1
            if why == "narrowed_person":
                notes["kept_name"] += 1
            continue
        nonbank += [(kind, s, s + len(original)) for s in starts]

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
                    if text[a:b].strip():
                        spans.append(Span(a, b, kind, detector=DETECTOR_VERSION))
                continue
        spans.append(Span(s, e, kind, detector=DETECTOR_VERSION))
    return Detection(tuple(spans), tuple(unlocated), tuple(kept), over, notes)


def _wp3_pieces(text: str) -> dict[str, set[str]]:
    """For each joined run of the Intake finder: the digit blocks it was joined from (needed to tell whether a short block stays visible)."""
    out: dict[str, set[str]] = {}
    ic = invoicecheck
    for ln in ic._f(text).split("\n"):
        for v in {ln, ic._digitise(ln)}:
            for _, blocks in ic._runs(v):
                if len(blocks) > 1:
                    out.setdefault("".join(blocks), set()).update(blocks)
    return out


# ---------------------------------------------------------------------------------------------------------------- marks
_MARK = re.compile(r"<([A-Z][A-Z0-9]*)_([0-9]+)>")
_MARK_LIKE = re.compile(r"<\s*([A-Za-z][A-Za-z0-9]*)\s*_\s*(\d+)\s*>")


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
        raise SelfCheckFailed("mask_failed") from None


def issued(masked: Masked) -> frozenset[str]:
    return frozenset(s.placeholder for s in masked.spans)


NEUTRAL = (
    "argument"  # filler for an issued mark: no bank word, no look-alike digit letter, and a word the core secret rule ignores (a one-letter
)
# filler such as ``x`` after ``password=`` would be taken as a secret value and then replaced everywhere, which would fail check a2 for every such invoice)


def neutralise(text: str, masked: Masked) -> str:
    """Every mark this document was given replaced by a plain filler word, so the mark words (BANK, ...) cannot be taken for bank words."""
    ok = issued(masked)
    return _MARK.sub(lambda m: NEUTRAL if m.group(0) in ok else m.group(0), text)


def cut_visible(text: str, masked: Masked) -> str:
    """Every surface string kept visible on purpose (amounts, id tokens) replaced by ``x`` before searching for hidden spellings."""
    for t in masked.kept_visible_texts:
        if t:
            text = text.replace(t, "x")
            if not t.isascii():  # the same text as a JSON body writes it (\uXXXX escapes)
                text = text.replace(json.dumps(t)[1:-1], "x")
    return text


def check_model_text(masked: Masked) -> None:
    """Checks a3 and a2 on the finished model text. Raises ``SelfCheckFailed``."""
    marks = [m.group(0) for m in _MARK.finditer(masked.text)]
    look = [f"<{m.group(1)}_{m.group(2)}>" for m in _MARK_LIKE.finditer(canonical(masked.text))]
    ok = issued(masked)
    if sorted(marks) != sorted(look) or any(m not in ok for m in marks) or len(set(marks)) != len(ok):
        raise SelfCheckFailed("mask_failed")
    det = detect(neutralise(masked.text, masked))
    if det.unlocated or det.spans:
        raise SelfCheckFailed("mask_residual")
    if det.money_overlap:
        raise SelfCheckFailed("mask_money_overlap")


# ---------------------------------------------------------------------------------------------------------------- spellings and search
def spellings(value: str) -> tuple[str, ...]:
    """The listed spellings of a SURFACE string: raw and casefold always; at 6 or more characters also the derived forms (design B5)."""
    out = [value, value.casefold()]
    if len(value) >= 6:
        n = unicodedata.normalize("NFKC", value)
        out += [n, n.casefold()]
        for ascii_only in (True, False):
            j = json.dumps(value, ensure_ascii=ascii_only)
            out += [j[1:-1], json.dumps(j)[1:-1]]
        out += [html.escape(value), quote(value, safe=""), quote_plus(value)]
        raw = value.encode("utf-8", "surrogatepass")
        b64 = base64.b64encode(raw).decode().rstrip("=")
        out += [b64, base64.urlsafe_b64encode(raw).decode().rstrip("="), raw.hex(), raw.hex().upper()]
    return tuple(dict.fromkeys(s for s in out if s))


def hit_in(haystack: str, lowered: str, value: str) -> bool:
    """True when any listed spelling of ``value`` is in ``haystack`` (``lowered`` = its casefold). Below 6 characters a spelling counts only as a
    whole token (letters and digits on neither side)."""
    if len(value) < 6:
        for sp in {value, value.casefold()}:
            if re.search(r"(?<![0-9A-Za-z])" + re.escape(sp) + r"(?![0-9A-Za-z])", haystack, re.IGNORECASE):
                return True
        return False
    ci = {value.casefold(), unicodedata.normalize("NFKC", value).casefold()}
    return any(sp in haystack for sp in spellings(value)) or any(sp in lowered for sp in ci)


def surfaces(masked: Masked, document_text: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(document_text[s.start : s.end] for s in masked.spans))


def hidden_hits(haystack: str, values: tuple[str, ...]) -> int:
    low = haystack.casefold()
    return sum(1 for v in values if hit_in(haystack, low, v))


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
            if hidden_hits(cut_visible(h, fresh), vals):
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


def _walk(node: Any, schema: Any, shown: str, generic: str, visit) -> Any:
    """Rebuilds ``node`` calling ``visit(text, shown, generic)`` on each string value; any key the schema does not know is written as ``other``."""
    if isinstance(node, str):
        return visit(node, shown, generic)
    if isinstance(node, list):
        item = schema.get("items") if isinstance(schema, dict) else None
        return [_walk(v, item, f"{shown}[{i}]", generic + "[]", visit) for i, v in enumerate(node)]
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            sub = _child(schema, k) if isinstance(k, str) else None
            name = k if sub is not None else "other"
            if isinstance(k, str) and _MARK_LIKE.search(canonical(k)):
                e = SelfCheckFailed("forged_mark")
                e.detail = (f"{shown}.{name}".lstrip("."), len(k), "")
                raise e
            out[k] = _walk(v, sub, f"{shown}.{name}".lstrip("."), f"{generic}.{name}".lstrip("."), visit)
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

    _walk(fields, schema, "", "", check_b)
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

    out = _walk(fields, schema, "", "", put)
    left = [0]

    def count_left(s: str, shown: str, generic: str) -> str:
        left[0] += len(_MARK.findall(s))
        return s

    _walk(out, schema, "", "", count_left)
    try:
        fresh = mask(document_text, key)
    except SelfCheckFailed:
        raise SelfCheckFailed("restore_mismatch") from None

    def sig(m: Masked) -> tuple:
        return (m.text, tuple((s.placeholder, s.kind, s.start, s.end, s.fingerprint) for s in m.spans))

    if sig(fresh) != sig(masked) or left[0] or any(v[3] != "same" for v in items.values()):
        raise SelfCheckFailed("restore_mismatch")
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
    if not on_file.strip() or not invoicecheck.bank_detail_findings(on_file, ""):
        return "no_details_on_file", key, (), len(found)
    diff = invoicecheck.bank_detail_findings(document_text, on_file)
    if diff:
        return "changed", key, _words_near(document_text, [f.candidate for f in diff if f.kind == "number"]), len(diff)
    if not found:
        return "none_found", key, (), 0
    return "ok", key, (), len(found)
