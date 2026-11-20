"""The run's one redaction map (K5, design 6.3, M14, R2, R6).

One map per run, started at intake (empty until K4) and continued for the document and every tool result, so a
value always gets the same placeholder and a placeholder never restores to a different value. Only **identifier
kinds** are ever stored or restored; secret and regulated kinds are placeholdered for the model but their originals
live in memory for the run and nowhere else.

Pure functions over a plain ``dict[str, str]`` (placeholder -> original). Stdlib and the studio redactor only.
"""

from __future__ import annotations

import base64
import binascii
import bisect
import collections
import functools
import hashlib
import html
import re
import time
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, NamedTuple
from urllib.parse import unquote

from hadavin_sdk import defaults
from hadavin_sdk.guard.redact import (
    _EVERY_COPY,
    _PLACEHOLDER,
    ARN_TAIL,
    PATTERNS,
    SECRET_KINDS,
    RedactionResult,
    _alias_keys,
    _joins,
    _plain,
    _Redactor,
    _replace_standalone,
    _sweep,
    kind_of,
    place_encoded,
    redact,
    strip_ansi,
)
from hadavin_sdk.guard.textnorm import without_spacing_marks

# Identifier kinds a fix or a read may need back (M14): the spec list plus the other identifier kinds the
# redactor emits (IPV6 beside IPV4, hostnames, UUIDs, GCP and Azure resource ids). Anything not listed (every
# secret kind, every regulated kind, and any kind added later) is NOT stored: an allowlist fails safe.
STORED_KINDS = frozenset(defaults.STORED_KINDS)
PLACEHOLDER = re.compile(
    r"<([A-Z][A-Z0-9]*)_([0-9]+)>"
)  # a genuine placeholder: exactly this, ASCII, upper case
# What a person could mistake for one: any case, any Unicode digit (escaped in untrusted text).
_LOOKALIKE = re.compile(r"<([A-Za-z][A-Za-z0-9]*)_(\d+)>")


class RedactionError(RuntimeError):
    """The redactor failed: nothing may be sent to the model."""


class InputTooLarge(RedactionError):
    """The text, or a view of it that the second pass would scan, is longer than `defaults.MAX_REDACT_CHARS`."""


# The end of a text cut inside an escape: a spelling the decoder cannot read yet, so no form matches it and the
# front of a character stays visible (`\u005`, `&#9`, `%C3`, half of a surrogate pair). Every alternative here is
# short, or is one character class under one star whose first character cannot occur inside it, so a search is
# linear. The one open-ended spelling, a run of `%XX` bytes, is scanned by `_pct_run_start`: a regex with a repeated
# group before an end anchor takes time that grows with the square of the run.
_PARTIAL_ESCAPE = re.compile(
    r"(?:&#(?:[xX][0-9a-fA-F]*|[0-9]*)|&[A-Za-z]*|\\u[dD][89abAB][0-9a-fA-F]{2}(?:\\u?[0-9a-fA-F]{0,3}|\\)?|\\u[0-9a-fA-F]{0,3}|\\|%[0-9a-fA-F]?)$"
)
_HEXDIGITS = frozenset("0123456789abcdefABCDEF")
_HIGH_HEX = frozenset("89abcdefABCDEF")


def _pct_run_start(text: str, pos: int) -> int | None:
    """The leftmost start (at or after `pos`) of a run of one or more `%XX` bytes (first digit 8 to F) that ends the
    text, optionally followed by a lone `%`, a lone hex digit, or `%` and a hex digit. Linear: it walks back from the
    end, three characters at a time, for each of the few shapes the end can have."""
    n = len(text)
    ends = [n, n - 1] if text.endswith("\n") else [n]  # `$` also matches before a final line break
    best: int | None = None
    for end in ends:
        for tail in (0, 1, 2):
            i = end - tail
            if i < 0:
                continue
            tail_text = text[i:end]
            if tail == 1 and tail_text != "%" and tail_text not in _HEXDIGITS:
                continue
            if tail == 2 and not (tail_text[0] == "%" and tail_text[1] in _HEXDIGITS):
                continue
            while (
                i - 3 >= pos
                and text[i - 3] == "%"
                and text[i - 2] in _HIGH_HEX
                and text[i - 1] in _HEXDIGITS
            ):
                i -= 3
                if best is None or i < best:
                    best = i
    return best


def partial_escape_start(text: str, pos: int = 0) -> int | None:
    """Where the half-written escape that ends `text` starts (the leftmost start at or after `pos`), or None."""
    # the old regex search read a negative start as 0; the run walk would wrap around
    pos = max(pos, 0)
    found = _PARTIAL_ESCAPE.search(text, pos)
    run = _pct_run_start(text, pos)
    if found is None:
        return run
    return found.start() if run is None else min(found.start(), run)


class TooDeep(RedactionError):
    """A text still changes after `defaults.SCRUB_MAX_LAYERS` rounds of decoding: more nested encodings than any
    honest producer writes. The scrub cannot say what it holds, so it fails closed (a marker, never the text)."""


def nfkc(text: str) -> str:
    """NFKC and invisible characters. It runs INSIDE every round: a full-width `%` or `&` is an escape character
    only after NFKC, and NFKC expands some characters (U+FDFA becomes 18), so a text whose canonical form would pass
    the redactor's cap is refused first (InputTooLarge, a RedactionError), as redact_text does for its own views."""
    if text.isascii():  # NFKC leaves ASCII alone, and ASCII has no invisible format characters
        return text
    # the WHOLE text is composed (a base letter joins its combining mark, Hangul jamo join), then the invisible characters go:
    # main's `canonical`. `canonical` itself is per character now (index fidelity for replacement) and composes nothing,
    # which is wrong for decoding: a secret stored precomposed and shown decomposed must be found
    return "".join(
        c
        for c in unicodedata.normalize("NFKC", fits_after_nfkc(text))
        if unicodedata.category(c) != "Cf"
    )


_HEX_ESCAPE = re.compile(r"\\(?:x([0-9a-fA-F]{2})|U([0-9a-fA-F]{8})|([0-3][0-7]{2}))")
_PCT_U = re.compile(r"%u([0-9a-fA-F]{4})")
_BRACE_U = re.compile(r"\\u\{([0-9a-fA-F]{1,6})\}")


def _one_escape(m: re.Match[str]) -> str:
    if m.group(1):
        return chr(int(m.group(1), 16))
    if m.group(2):
        cp = int(m.group(2), 16)
        return chr(cp) if cp <= 0x10FFFF else m.group(0)
    return chr(int(m.group(3), 8))


def hex_unescape(text: str) -> str:
    """Backslash escapes a log pipeline or a language writes for one character: backslash-x and two hex digits,
    backslash-U and eight hex digits, and a three-digit octal escape (backslash and 000 to 377). NOT decoded: a one- or
    two-digit octal escape and named escapes (`\1` and Windows paths would decode wrongly)."""
    if "%u" in text:
        text = _PCT_U.sub(lambda m: chr(int(m.group(1), 16)), text)
    if chr(92) in text:
        text = _BRACE_U.sub(
            lambda m: chr(int(m.group(1), 16)) if int(m.group(1), 16) <= 0x10FFFF else m.group(0),
            text,
        )
        text = _HEX_ESCAPE.sub(_one_escape, text)
    return text


def undo(text: str, clean: bool = False) -> str:
    """The text with the encodings an attacker or a log pipeline layers over a value undone: JSON string escapes
    (backslash-u with surrogate pairs joined, and the one-character escapes: PHP writes every slash as backslash-slash),
    backslash-x, backslash-U and octal escapes, percent-encoding, HTML entities, then NFKC and invisible characters. Each round applies the three decoders ONE
    AT A TIME (a combined step turns a half-written `&#10` that percent-decoding just exposed into a newline before
    anyone can see it was half an escape), and the round repeats to a fixed point: the layers nest in any order
    and depth (`&#37;41`, `%2541`, `%26%2390%3B`). The depth is capped at `defaults.SCRUB_MAX_LAYERS`; a text that
    still changes then raises `TooDeep` (fail closed). This is our own design, not a quoted standard: the scrub must
    FIND a secret in any spelling, so it decodes more than a validator would. The sources only bound it: CWE-174
    (MITRE CWE list, entry 174, fetched 2026-11-03) warns that decoding the same input twice lets
    values slip past checks, and says to reject input that does not conform; OWASP's Input Validation Cheat Sheet
    (fetched 2026-11-03) says to decode before checking, to cap parser nesting depth, and does not describe
    decoding to a fixed point; CWE-176 is Unicode handling. With `clean`, a half-written escape at the end of the text is
    dropped before every decoder (the tail a cut left)."""
    cur = text
    for _ in range(defaults.SCRUB_MAX_LAYERS + 1):
        step = cur
        for decode in (nfkc, json_unescape, hex_unescape, unquote, html.unescape):
            if clean:
                while (
                    cut := partial_escape_start(
                        step, max(len(step) - 4 * defaults.SCRUB_PARTIAL_END, 0)
                    )
                ) is not None:
                    step = step[
                        :cut
                    ]  # repeat: the look-back may start inside a run of half escapes
            step = decode(step)
        if step == cur:
            return cur
        cur = step
    raise TooDeep("TooDeep")


def _within_cap(text: str) -> str:
    if len(text) > defaults.MAX_REDACT_CHARS:
        raise InputTooLarge("InputTooLarge")
    return text


@functools.lru_cache(maxsize=4096)
def _nfkd_len(char: str) -> int:
    return len(unicodedata.normalize("NFKD", char))


def _expanded_len(text: str) -> int:
    """An upper bound of the NFKC length of `text` (the NFKD length of each distinct character, cached). It can be
    higher than the real NFKC length where composition shortens a sequence (a Greek iota with dialytika and tonos,
    U+0390, is 3 characters in NFKD and 1 in NFKC): a text of mostly such characters near the cap is refused
    although its canonical form would fit. The false refusal is fail-closed and needs a text of that kind within
    a factor of three of the cap."""
    if text.isascii():
        return len(text)
    return sum(n * _nfkd_len(c) for c, n in collections.Counter(text).items())


def fits_after_nfkc(text: str) -> str:
    """Refuse BEFORE the work if the canonical view of `text` could pass the cap. NFKC of a string is never longer
    than the NFKD of its characters, which is looked up once per distinct character (the normalisation itself
    takes seconds on a million characters, so it must not run first)."""
    if _expanded_len(text) > defaults.MAX_REDACT_CHARS:
        raise InputTooLarge("InputTooLarge")
    return text


# --- what may be stored: an allowlist grammar per kind --------------------------------------------------------
# A redactor pattern is a regex for FINDING an identifier; a stored original must be exactly one. Each stored
# kind has the characters its grammar allows (RFC 5322 local part and RFC 1123 host names, dotted quads, AWS ARN
# resource ids, GCP and Azure resource paths). An original with anything else in it (`;token=...` glued to an ARN
# by a pattern that over-matched, a quote, a separator) is not stored, whatever pattern produced it.
_HUMAN = r"[\w ,.'#/()+:=\-]{1,256}"  # names, addresses, phone numbers, tenant ids: words and light punctuation
_GRAMMAR: dict[str, re.Pattern[str]] = {
    k: re.compile(v)
    for k, v in {
        "ARN": r"arn:aws[a-z\-]*:[a-z0-9\-]*:[a-z0-9\-]*:(?:[0-9]{12})?:" + ARN_TAIL + r"+",
        "ACCOUNTID": r"[0-9]{12}",
        "EMAIL": r"[A-Za-z0-9._+\-]+(?:@|%40)[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
        "MAC": r"[0-9A-Fa-f:.\-]{12,17}",
        # a dotted quad, the dashed form (ec2 / pod DNS names), with the redactor's own prefix and suffix
        "IPV4": r"(?:(?:ip|ec2)-)?[0-9]{1,3}(?:[.\-][0-9]{1,3}){3}(?:\.[A-Za-z0-9\-]+\.pod)?",
        "IPV6": r"[0-9A-Fa-f:.]{2,45}",
        "HOSTNAME": r"[A-Za-z0-9.\-]{3,253}",
        "GCPRESOURCE": r"projects/[A-Za-z0-9_\-]+(?:/" + ARN_TAIL + r"+)?",
        "AZURERESOURCE": r"/subscriptions/[0-9A-Fa-f\-]{36}(?:/" + ARN_TAIL + r"+)?",
        "TENANT": _HUMAN,
        "NAME": _HUMAN,
        "ADDRESS": _HUMAN,
        "PHONE": r"[0-9 ()+.\-]{5,32}",
    }.items()
}
# tests/test_k5_classes.py: every stored kind has a grammar.
# Only the secret patterns: an identifier original must also hold no secret-shaped text.
# HIGHENTROPY is left out: it matches any long mixed-case path (an Azure resource id), and an original that already
# fits its grammar has no `key=value` in it where a credential could hide.
_SECRET_PATTERNS = tuple(
    p for label, p in PATTERNS if label in SECRET_KINDS and label != "HIGHENTROPY"
)


_STORABLE_CACHE: dict[str, bool] = {}
_STORABLE_CACHE_MAX = 1 << 16


def storable_original(kind: str, original: str) -> bool:
    """True if `original` is a whole identifier of `kind` by the allowlist grammar and holds no secret-shaped
    text. Anything that cannot be checked is not stored. Cached by a SHA-256 digest, so the cache holds no
    original value (a map is re-filtered after every redaction)."""
    key = hashlib.sha256(f"{kind}\0{original}".encode("utf-8", "surrogatepass")).hexdigest()
    hit = _STORABLE_CACHE.get(key)
    if hit is not None:
        return hit
    grammar = _GRAMMAR.get(kind)
    ok = False
    if grammar is not None and grammar.fullmatch(original) is not None:
        try:
            ok = not any(p.search(original) for p in _SECRET_PATTERNS)
        except Exception:  # noqa: BLE001 - fail closed
            ok = False
    if len(_STORABLE_CACHE) >= _STORABLE_CACHE_MAX:
        _STORABLE_CACHE.clear()
    _STORABLE_CACHE[key] = ok
    return ok


def storable(mapping: dict[str, str], kinds: frozenset[str] | None = None) -> dict[str, str]:
    """The part of a run's map that may be stored and restored: identifier kinds whose originals fit their
    allowlist grammar and hold no secret-shaped text."""
    allowed = STORED_KINDS if kinds is None else kinds
    return {
        p: v
        for p, v in mapping.items()
        if kind_of(p) in allowed and storable_original(kind_of(p), v)
    }


def canonical(text: str) -> str:
    """Untrusted text in one canonical form before it is escaped, redacted or compared: Unicode NFKC (a
    full-width `＜ＩＰＶ４＿２＞` becomes `<IPV4_2>`) with the invisible format characters removed (a zero-width
    space inside a token no longer hides it). It is THE SAME TEXT as the first result of `_canonical_view`: NFKC is applied one
    character at a time, so the text a match is searched in and the text the match positions refer to never differ (they did when
    the whole text was composed: a + U+0301 became U+00E1 here and not in the view). A base letter and a combining mark are therefore
    not composed."""
    if text.isascii():
        return text  # NFKC changes nothing and ASCII has no format character
    return _canonical_view(text)[0]


_ASCII_OR_ONE = re.compile(r"[\x00-\x7f]+|[^\x00-\x7f]")  # a run of ASCII, or one other character


_INVISIBLE = frozenset({"Cf"})
# G13 (E19 N3): what the result-marker search also drops. `canonical` composes nothing, so a combining mark after `<` (U+0338)
# stays between the two `<` of a marker look-alike and `_MARKER` did not match it.
_INVISIBLE_OR_MARK = frozenset({"Cf", "Mn", "Me"})


def _canonical_view(text: str, drop: frozenset[str] = _INVISIBLE) -> tuple[str, list[int]]:
    """The canonical form of `text` (NFKC, characters of a category in `drop` removed: by default the invisible format
    characters) and, for each canonical character, the index of the original character it came from."""
    chars: list[str] = []
    index: list[int] = []
    for run in _ASCII_OR_ONE.finditer(text):
        piece = run.group()
        if piece.isascii():  # NFKC changes no ASCII character and ASCII has no format character (Cf): the run is copied whole
            chars.append(piece)
            index.extend(range(run.start(), run.end()))
            continue
        for d in unicodedata.normalize("NFKC", piece):
            if unicodedata.category(d) not in drop:
                chars.append(d)
                index.append(run.start())
    return "".join(chars), index


def replace_canonical(
    text: str,
    pattern: re.Pattern[str],
    repl: Callable[[re.Match[str]], str],
    drop: frozenset[str] = _INVISIBLE,
) -> str:
    """Find `pattern` in the canonical view of `text` and replace only the matched stretches IN THE ORIGINAL.
    The model keeps seeing the text as it was written (accents, CJK, emoji, joiners untouched); only a stretch
    that, once folded, is the thing being guarded (a placeholder, a result marker) is rewritten. All-ASCII text
    is its own canonical form."""
    if text.isascii():
        return pattern.sub(repl, text)
    canon, index = _canonical_view(text, drop)
    out: list[str] = []
    last = 0
    for m in pattern.finditer(canon):
        if m.end() == m.start():
            continue
        start, end = index[m.start()], index[m.end() - 1] + 1
        if start < last:
            continue
        out += [text[last:start], repl(m)]
        last = end
    out.append(text[last:])
    return "".join(out)


def escape_placeholders(text: str) -> str:
    """Untrusted text may contain a literal `<IPV4_2>` in any case (`<ipv4_2>`, `<Ipv4_2>`). Left as typed it
    would look like the placeholder the redactor later issues to a different value, and restore or the grounding
    check would treat it as that value. Every placeholder-shaped literal becomes a non-placeholder. It is found in the canonical
    view (NFKC one character at a time, invisible format characters removed), so a COMPATIBILITY spelling (full-width
    `\uff1c\uff29\uff30\uff36\uff14\uff3f\uff12\uff1e`, a zero-width space inside) is caught; a confusable from another script that NFKC keeps (Cyrillic `\u0410` for
    `A`, UTS #39 look-alikes) is not folded and is not escaped (G13, E19 N2)."""
    return replace_canonical(text, _LOOKALIKE, lambda m: f"\u2039{m.group(1)}_{m.group(2)}\u203a")


_MARKER = re.compile(r"<<(?=\s*(?:end\s+)?tool\s+result)", re.IGNORECASE)


def escape_markers(text: str) -> str:
    """Neutralise anything shaped like our result markers, in any case and spacing, including full-width and
    zero-width spellings (found in the canonical form, rewritten in the original; the rest of the text is left
    as it was written). Combining marks are dropped for this search too (G13, E19 N3): `<<` + U+0338 + `TOOL RESULT` is a
    marker look-alike."""
    return replace_canonical(text, _MARKER, lambda m: "[[", _INVISIBLE_OR_MARK)


def neutralise_untrusted(text: str) -> str:
    """Untrusted text made safe to hand on: result markers and placeholder look-alikes are escaped."""
    return escape_placeholders(escape_markers(text))


def redact_untrusted(text: str, mapping: dict[str, str]) -> str:
    """`redact_text` for text from outside (the document, a tool result, an error message): markers and
    placeholder-shaped literals are escaped in the text AND in every decoded view the second pass may return
    (see `redact_text`). Model-written text (tool arguments, proposal inputs) uses `redact_text` as it is: a
    placeholder the model writes is meant to be one."""
    return redact_text(text, mapping, neutralise=neutralise_untrusted)


_JSON_ESCAPE = re.compile(r'\\(u[0-9a-fA-F]{4}|["\\/bfnrt])')
_JSON_SIMPLE = {
    '"': '"',
    "\\": "\\",
    "/": "/",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}


def json_unescape(text: str, simple: str = '"\\/bfnrt') -> str:
    """The text with JSON string escapes undone: `\\uXXXX` (a valid surrogate pair becomes the one astral
    character it spells; a lone half becomes U+FFFD) and the one-character escapes named in `simple`
    (`\\/` is how PHP's json_encode writes every slash). One left-to-right pass, as JSON is read: `\\\\u0041`
    is a backslash and `u0041`."""

    def one(m: re.Match[str]) -> str:
        g = m.group(1)
        if g[0] == "u":
            return chr(int(g[1:], 16))
        return _JSON_SIMPLE[g] if g in simple else m.group(0)

    out = _JSON_ESCAPE.sub(one, text)
    if out.isascii():
        return out
    return out.encode("utf-16", "surrogatepass").decode("utf-16", "replace")


class RunMap(dict):
    """A run's redaction map. It carries the redactor's built state between calls: without it every redacted
    string rebuilt the finders over the whole map (cost = strings x map size; a document can plant thousands of
    distinct values). The state is per run and dies with it (R371), and it is reused only while the map is
    unchanged."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.redact_cache: dict[str, Any] = {}


def _clean(text: str) -> str:
    """NUL and lone surrogates cannot be sent or stored and can split a secret: NUL goes, a surrogate becomes
    '?'. Applied before AND after the second pass (a `\\ud800` escape decodes to a lone surrogate)."""
    return text.replace("\x00", "").encode("utf-8", "replace").decode("utf-8", "replace")


def composed(text: str) -> str:
    """The COMPOSED form of `text`: the invisible format characters removed first (so one between a letter and its accent does
    not keep them apart), then NFKC of the WHOLE text, which joins a base letter and its combining marks (e + U+0301 becomes the
    precomposed letter) and Hangul conjoining jamo. `canonical` normalises one character at a time (so its match positions stay
    exact) and so composes nothing; a value that was stored precomposed and is written decomposed (macOS file names, many PDF
    extractors) is found only in this view. The text returned has no index back into the original: it is used to FIND, never to cut."""
    if text.isascii():
        return text
    kept = "".join(c for c in text if unicodedata.category(c) != "Cf")
    return unicodedata.normalize("NFKC", kept)


def _views(text: str) -> list[str]:
    """Other forms a secret can hide in: the canonical view (NFKC one character at a time, invisible characters removed), the same
    with JSON `\\uXXXX` escapes decoded, and for each of them the COMPOSED view (`composed`: base letters joined with their marks),
    then the canonical and the composed view of the text without its spacing marks, modifier letters and modifier symbols.
    Only forms that differ from `text` are returned; a text with no combining sequence has the same composed and canonical view,
    so it costs nothing."""
    # `\\/` too (PHP writes every slash that way); `\\n` and the like are left alone here: a log line full of them
    # would come back with real newlines whenever the second pass finds anything.
    unescaped = fits_after_nfkc(json_unescape(text, simple="/"))
    out = []
    # the layers undone to a fixed point (percent, entity, backslash, NFKC, any order, up to the depth cap; deeper
    # raises TooDeep and nothing is redacted or shown): `%41KIA...`, `&#65;KIA...`, `password%3Dx`
    undone = fits_after_nfkc(undo(text))
    # and the text without its spacing marks, modifier letters and modifier symbols (textnorm, "MARKS AND SCANS": NFKC reads a modifier
    # letter as a letter and keeps a spacing vowel sign, so "AKIA" + U+093E + "IOSFODNN7EXAMPLE" is not the key in `canonical` alone), in
    # the canonical view and in its composed twin (they differ when the text holds a letter and a combining accent, also when the
    # removed mark stood between the two: `canonical` composes nothing)
    unmarked = without_spacing_marks(text)
    for view in (
        canonical(text),
        canonical(unescaped),
        undone,
        composed(text),
        composed(unescaped),
        composed(undone),
        canonical(unmarked),
        composed(unmarked),
    ):
        view = _clean(view)
        if view != text and view not in out:
            out.append(view)
    return out


def _held(text: str) -> int:
    return len(PLACEHOLDER.findall(text))


_VALUE_END = frozenset(" \t\n;&,\"'")
_ENCODED_MARKS = ("%", chr(92), "&")
MAX_DECODED_MASKS = 256


def _decoded_masks(
    current: dict[str, str], text: str, deadline: float | None = None
) -> list[tuple[str, str]]:
    """(placeholder, decoded original) for the values pass one masked WHOLE whose decoded spelling would stop a value
    pattern early (the decoded text holds white space of any kind, or `;`, `&`, `,` or a quote): `password=ab%3Bzq9` is
    one value in pass one and `password=ab;zq9` in the decoded view, which would mask only `ab`. Only entries whose
    original occurs in THIS text and holds an encoding character are considered (so earlier junk in the run's map cannot
    use up the slots); more than `MAX_DECODED_MASKS` of them, or one that cannot be decoded (nested too deep), cannot be
    paired and the text is refused (`InputTooLarge`, nothing shown), never skipped. Computed once per call.
    `deadline` (a `time.thread_time()` value, shared with stage 1 and every view) is checked once per stored original, before
    any skip; a spent deadline raises `InputTooLarge`.
    """
    out = []
    for ph, original in current.items():
        if deadline is not None and time.thread_time() > deadline:
            raise InputTooLarge("InputTooLarge")  # one check per stored original, before any skip
        if original.startswith("\0seed") or not (
            any(c in original for c in _ENCODED_MARKS) or not original.isascii()
        ):
            continue
        if original not in text:
            continue
        if len(out) >= MAX_DECODED_MASKS:
            raise InputTooLarge("InputTooLarge")
        decoded = undo(
            original
        )  # a RedactionError (nested too deep) propagates: fail closed, nothing shown
        if (
            decoded != original
            and len(decoded) >= 4
            and any(c.isspace() or c in _VALUE_END for c in decoded)
        ):
            out.append((ph, decoded))
    return out


def _keep_earlier_masks(view: str, pairs: list[tuple[str, str]]) -> str:
    """Before a decoded VIEW is redacted, the decoded spelling of every value pass one masked is replaced by its
    placeholder: if the view then replaces the text, the part of the value its pattern would not reach is not shown."""
    for ph, decoded in pairs:
        if decoded in view:
            view = view.replace(decoded, ph)
    return view


@dataclass
class _ScanBudget:
    """The base64 step's budget for ONE redact_text call; the text, every view and every depth share it."""

    started: float  # redact_text's `started`; the deadline is started + defaults.REDACT_BUDGET_S
    units: int = (
        0  # units decoded or masked unread so far (decodable, not held), all views and depths
    )
    decoded_chars: int = 0  # characters of decoded text read so far (len of each _b64_text result)
    part_chars: int = 0  # decoded characters of the lines and trimmed joins of blocks tried alone (a count of their own)

    def clock(self) -> None:
        """ONE time.thread_time() read; past the deadline: InputTooLarge."""
        if time.thread_time() - self.started > defaults.REDACT_BUDGET_S:
            raise InputTooLarge("InputTooLarge")

    def take(self, chars: int, part: bool = False) -> None:
        if part:
            self.part_chars += chars
            if self.part_chars > defaults.B64_MAX_DECODED_CHARS:
                raise InputTooLarge("InputTooLarge")
            return
        self.units += 1
        self.decoded_chars += chars
        if (
            self.units > defaults.B64_MAX_UNITS
            or self.decoded_chars > defaults.B64_MAX_DECODED_CHARS
        ):
            raise InputTooLarge("InputTooLarge")


class _B64Unit(NamedTuple):
    start: int  # offset in the ANSI-stripped text (3.1 point 5)
    end: int
    written: str  # the unit as written, line breaks included: the ENCODED original
    joined: str  # its lines, stripped, joined with nothing between: what _b64_text decodes
    lines: tuple[str, ...]  # its lines as written (stripped), for the held rule
    parts: tuple[
        _B64Unit, ...
    ] = ()  # a block's lines of at least B64_MIN_CHARS characters, each a one-line unit; () for a run
    trims: tuple[
        _B64Unit, ...
    ] = ()  # a block of 3 or more lines: its lines without the last, and without the first (2 or more lines)


_B64_LINE = re.compile(r"[A-Za-z0-9+/_\-]+={0,2}")  # one line of a block, matched whole (fullmatch)
_B64_RUN = re.compile(
    rf"(?<![A-Za-z0-9+/_\-])[A-Za-z0-9+/_\-]{{{defaults.B64_MIN_CHARS},}}={{0,2}}(?![A-Za-z0-9+/_\-=])"
)
# Blanked before runs are found (3.1 point 2): a placeholder of ours, or a marker shape. STATED LIMIT (L-B6, design result review 1 N6): the
# `[A-Z][A-Z0-9_]*` branch blanks ANY all-uppercase-and-digit text in angle brackets, so a blob whose base64 characters are all
# uppercase letters, digits and `_`, written between `<` and `>` (or `‹` and `›`), is never a run: an author who controls the payload
# bytes can pick a payload that encodes so. No input a real secret would produce has that shape (pinned by TB-3.3b).
_B64_TOKEN_SKIP = re.compile(r"[<‹](?:[A-Za-z][A-Za-z0-9]*_\d+|[A-Z][A-Z0-9_]*)[>›]")
_B64_SEP = "\n\n;\n\n"  # between decoded texts: survives `neutralise_untrusted`, holds no run character, no `\`, `%` or `&`


def _b64_lines(search: str) -> list[tuple[int, int]]:
    """(start, end) of each line's content: split on `\\n`, one trailing `\\r` and spaces or tabs at both ends dropped."""
    spans: list[tuple[int, int]] = []
    pos = 0
    for line in search.split("\n"):
        s, e = pos, pos + len(line)
        pos = e + 1
        if e > s and search[e - 1] == "\r":
            e -= 1
        while s < e and search[s] in " \t":
            s += 1
        while e > s and search[e - 1] in " \t":
            e -= 1
        spans.append((s, e))
    return spans


def _b64_units(text: str) -> tuple[str, list[_B64Unit]]:
    """(the ANSI-stripped text, its base64 units in order); (text, []) when the text holds no run. A unit is a wrapped block
    (two or more lines of one length) or a run that does not start inside a block. Placeholders and markers are never runs."""
    stripped = strip_ansi(text)
    search = stripped
    if "<" in search or "‹" in search:
        search = _B64_TOKEN_SKIP.sub(lambda m: " " * len(m.group()), search)
    if not _B64_RUN.search(search):
        return stripped, []
    spans = _b64_lines(search)
    blocks: list[_B64Unit] = []
    i = 0
    while i < len(spans):
        first_start, first_end = spans[i]
        width = first_end - first_start
        line = search[first_start:first_end]
        if width < defaults.B64_WRAP_MIN_CHARS or "=" in line or not _B64_LINE.fullmatch(line):
            i += 1
            continue
        taken = [i]
        for j in range(i + 1, len(spans)):
            s, e = spans[j]
            line = search[s:e]
            if not line or len(line) > width or not _B64_LINE.fullmatch(line):
                break
            taken.append(j)
            if len(line) < width or "=" in line:
                break  # a shorter or padded line is the last
        if len(taken) >= 2:
            start, end = spans[taken[0]][0], spans[taken[-1]][1]
            lines = tuple(search[s:e] for s, e in (spans[k] for k in taken))
            parts = tuple(
                _B64Unit(s, e, search[s:e], search[s:e], (search[s:e],))
                for s, e in (spans[k] for k in taken)
                if len(search[s:e].rstrip("=")) >= defaults.B64_MIN_CHARS
            )
            trims: list[_B64Unit] = []
            if len(taken) >= 3:  # the blob without a closing word, and without an odd first line
                for ks in (taken[:-1], taken[1:]):
                    ts, te = spans[ks[0]][0], spans[ks[-1]][1]
                    tl = tuple(search[s:e] for s, e in (spans[k] for k in ks))
                    trims.append(_B64Unit(ts, te, stripped[ts:te], "".join(tl), tl))
            blocks.append(
                _B64Unit(
                    start, end, stripped[start:end], "".join(lines), lines, parts, tuple(trims)
                )
            )
            i = taken[-1] + 1
        else:
            i += 1
    starts = [b.start for b in blocks]
    units = list(blocks)
    for m in _B64_RUN.finditer(search):
        k = bisect.bisect_right(starts, m.start()) - 1
        if k < 0 or m.start() >= blocks[k].end:  # a run inside a block is not a unit
            units.append(_B64Unit(m.start(), m.end(), m.group(), m.group(), (m.group(),)))
    units.sort(key=lambda u: u.start)
    return stripped, units


def _b64_held(unit: _B64Unit, secret: frozenset[str], wholes: str) -> bool:
    """A unit pass one already masked: its text (padding ignored) is the original of a secret placeholder, or every line is one or a
    piece of a JWT or key original (`wholes`: those originals joined by NUL, built once per `_pass_one`)."""
    if unit.written.rstrip("=") in secret:
        return True
    return all(line.rstrip("=") in secret or line in wholes for line in unit.lines)


def _printable_text(s: str | None) -> str | None:
    """`s` when at least `defaults.B64_PRINTABLE_SHARE` of its characters are printable (tab, line feed and carriage return count),
    else None. STATED LIMIT (L-B8, design result review 1 M2): a decoded text with 10 % or more non-printable characters is never
    scanned, and `str.isprintable()` is False for NBSP and U+3000 as well as for control characters. A blob padded on purpose with
    such characters, or a binary container (protobuf, msgpack) that holds an ASCII credential among its non-text bytes, is not a
    unit hit and stays readable beside pass one's misses. No fallback is built (a lead decision; an ASCII-strings extraction of at
    least 8 characters changed 0 of the 142 probe rows and 0 of the 1,978 property inputs, measured: G4-build-notes.md). Pinned by
    `test_limit_padded_blob` (strict xfail)."""
    if (
        s is not None
        and s
        and sum(c.isprintable() or c in "\t\n\r" for c in s)
        >= defaults.B64_PRINTABLE_SHARE * len(s)
    ):
        return s
    return None


def _decoded(raw: bytes, codec: str) -> str | None:
    try:
        return raw.decode(codec)
    except UnicodeDecodeError:
        return None


def _b64_text(joined: str) -> str | None:
    """The text a base64 run (standard or URL-safe alphabet, padded or not) decodes to, or None when it is not text."""
    body = joined.rstrip("=")
    std = "+" in body or "/" in body
    url = "-" in body or "_" in body
    if std and url:
        return None
    if url:
        body = body.replace("-", "+").replace("_", "/")
    if len(body) % 4 == 1:
        return None
    try:
        raw = base64.b64decode(body + "=" * (-len(body) % 4), validate=True)
    except (binascii.Error, ValueError):
        return None
    if raw[:2] == b"\xff\xfe":
        return _printable_text(_decoded(raw[2:], "utf-16-le"))
    if raw[:2] == b"\xfe\xff":
        return _printable_text(_decoded(raw[2:], "utf-16-be"))
    if raw[:3] == b"\xef\xbb\xbf":
        return _printable_text(_decoded(raw[3:], "utf-8"))
    text = _printable_text(_decoded(raw, "utf-8"))
    if text is not None:
        return text
    if len(raw) % 2 == 0 and len(raw) >= 4:
        odd, even = raw[1::2], raw[0::2]
        if odd.count(0) >= defaults.B64_UTF16_ZERO_SHARE * len(odd):
            return _printable_text(_decoded(raw, "utf-16-le"))
        if even.count(0) >= defaults.B64_UTF16_ZERO_SHARE * len(even):
            return _printable_text(_decoded(raw, "utf-16-be"))
    return None


def _b64_hits(
    units: list[_B64Unit],
    known: dict[str, str],
    budget: _ScanBudget,
    depth: int,
    part: bool = False,
) -> tuple[list[bool], list[tuple[str, str]]]:
    """For each unit, whether it is a HIT (its decoded text held a value the scan masks, or it was masked unread because it was too
    long or too deep), and the KEPT entries: (kind, original) pairs of the decoded view's new values of kinds that are never stored
    (kept as pairs, not as placeholders: two scans number their entries from the same start). `part=True` is the call for the lines
    and trimmed joins of blocks: nothing counts against `B64_MAX_UNITS` and the decoded characters go to `budget.part_chars`."""
    hits = [False] * len(units)
    pieces: list[str] = []
    idx: list[int] = []
    for k, u in enumerate(units):
        budget.clock()
        if len(u.joined) > defaults.B64_MAX_UNIT_CHARS:
            budget.take(0, part)
            hits[k] = True
            continue
        d = _b64_text(u.joined)
        if d is None:
            continue
        if depth >= defaults.B64_MAX_DEPTH:
            budget.take(0, part)
            hits[k] = True
            continue
        budget.take(len(d), part)
        piece = _clean(d)
        if _B64_SEP in piece:  # a decoded text cannot fake the boundaries
            hits[k] = True
            continue
        pieces.append(piece)
        idx.append(k)

    def all_hit() -> tuple[list[bool], list[tuple[str, str]]]:
        for k in idx:
            hits[k] = True
        return hits, []

    if not pieces:
        return hits, []
    joined = _B64_SEP.join(pieces)
    if _expanded_len(joined) > defaults.MAX_REDACT_CHARS:
        return all_hit()
    seen = fits_after_nfkc(neutralise_untrusted(fits_after_nfkc(_clean(joined)))).split(_B64_SEP)
    if len(seen) != len(pieces):
        return all_hit()
    try:
        out, scanned_map = _scan(joined, dict(known), None, neutralise_untrusted, budget, depth + 1)
    except TooDeep:
        return all_hit()
    after = out.split(_B64_SEP)
    if len(after) != len(pieces):
        return all_hit()
    for i, a, s in zip(idx, after, seen, strict=False):
        hits[i] = _held(a) > _held(s)
    kept = [
        (kind_of(k), v)
        for k, v in scanned_map.items()
        if k not in known and kind_of(k) not in STORED_KINDS and kind_of(k) != "ENCODED"
    ]
    return hits, kept


def _b64_place(stripped: str, units: list[_B64Unit], placeholders: dict[str, str]) -> str:
    """`stripped` with each chosen unit (sorted, not overlapping) replaced by the placeholder of its `written`."""
    out: list[str] = []
    pos = 0
    for u in units:
        out.append(stripped[pos : u.start])
        out.append(placeholders[u.written])
        pos = u.end
    out.append(stripped[pos:])
    return "".join(out)


_ONLY_PLACEHOLDERS = re.compile(r"(?:<ENCODED_[1-9][0-9]{0,5}>)+")


def _only_encoded(t2: str, base: dict[str, str]) -> bool:
    """True when `t2` is nothing but `<ENCODED_n>` placeholders and no stored original (ASCII, so with no folded spelling) occurs
    inside it: a second `redact` over such a text reads nothing and writes nothing.

    A performance win for all-ASCII maps only (E22): the shortcut is OFF whenever any stored value is non-ASCII (its folded spelling
    is not known here, so `redact` runs) or occurs in `t2`. Pinned by TB-3.44 and TB-3.45 and three mutants."""
    if not _ONLY_PLACEHOLDERS.fullmatch(t2):
        return False
    return all(v.isascii() and v not in t2 for v in base.values())


def _pass_one(
    text: str, mapping: dict[str, str], cache, budget: _ScanBudget, depth: int
) -> RedactionResult:
    """Pass one (`redact`, with G7's settle) and, when a base64 run that pass one did not hold decodes to text in which the scan
    masks something, a second `redact` over the text with each such run replaced whole by one `<ENCODED_n>`."""
    started = budget.started
    first = redact(
        text, mapping=mapping, _cache=cache, _deadline=started + defaults.REDACT_BUDGET_S
    )
    stripped, units = _b64_units(text)
    if not units:
        return first
    secret = frozenset(
        v.rstrip("=") for k, v in first.mapping.items() if kind_of(k) in SECRET_KINDS
    )
    wholes = "\x00".join(v for k, v in first.mapping.items() if kind_of(k) in ("JWT", "PRIVKEY"))
    units = [u for u in units if not _b64_held(u, secret, wholes)]
    distinct = list({u.written: u for u in units}.values())
    if not distinct:
        return first
    hits, kept = _b64_hits(distinct, first.mapping, budget, depth)
    hit_of = {u.written: hit for u, hit in zip(distinct, hits, strict=True)}
    fallback: dict[str, _B64Unit] = {}
    for unit in distinct:
        if (unit.parts or unit.trims) and not hit_of[unit.written]:
            for p in (*unit.trims, *unit.parts):
                if p.written not in hit_of and not _b64_held(p, secret, wholes):
                    fallback.setdefault(p.written, p)
    if fallback:
        part_hits, part_kept = _b64_hits(
            list(fallback.values()), first.mapping, budget, depth, part=True
        )
        hit_of.update(zip(fallback, part_hits, strict=True))
        have = {v for _, v in kept}
        for kind, original in part_kept:
            if original not in have:
                kept.append((kind, original))
                have.add(original)
    if not any(hit_of.values()):
        return first
    base = dict(mapping)
    counters = _Redactor(dict(base)).counters
    for kind, original in kept:
        counters[kind] += 1
        base[f"<{kind}_{counters[kind]}>"] = original
    chosen: list[_B64Unit] = []
    for unit in units:
        if hit_of[unit.written]:
            chosen.append(unit)
        elif unit.parts or unit.trims:
            trim = next((t for t in unit.trims if hit_of.get(t.written)), None)
            if trim is not None:
                chosen.append(trim)
            chosen.extend(
                p
                for p in unit.parts
                if hit_of.get(p.written)
                and (trim is None or p.end <= trim.start or p.start >= trim.end)
            )
    chosen.sort(key=lambda u: u.start)
    runs = list(dict.fromkeys(u.written for u in chosen))
    placeholders = dict(zip(runs, place_encoded(base, runs), strict=True))
    t2 = _b64_place(stripped, chosen, placeholders)
    if _only_encoded(t2, base):
        # E22: the whole text is one run (or runs) now held as `<ENCODED_n>`: `redact` would rebuild its finder around the run's
        # original (the full length of the text) to read back 11 characters, and returns them as they are
        return RedactionResult(text=t2, mapping=base, actions=0)
    return redact(t2, mapping=base, _cache=cache, _deadline=started + defaults.REDACT_BUDGET_S)


def _scan(
    text: str,
    mapping: dict[str, str],
    cache,
    neutralise: Callable[[str], str] | None,
    budget: _ScanBudget,
    depth: int,
) -> tuple[str, dict[str, str]]:
    """The whole of `redact_text` but the cap, the exception wrapper and the map write: the text and its views, each through
    `_pass_one`. Returns the output and the new map; never writes `mapping`."""
    started = budget.started
    text = fits_after_nfkc(_clean(text))
    if neutralise is not None:
        text = fits_after_nfkc(neutralise(text))
    scan = not text.isascii() or any(c in text for c in "\\%&")
    views = _views(text) if scan else []  # _views refuses a view that would pass the cap
    result = _pass_one(text, mapping, cache, budget, depth)
    out, current = result.text, result.mapping
    if views and time.thread_time() - started > defaults.REDACT_BUDGET_S:
        raise InputTooLarge("InputTooLarge")
    pairs = _decoded_masks(current, text, started + defaults.REDACT_BUDGET_S) if views else []
    if (
        neutralise is not None
    ):  # the view is neutralised before it is redacted: pair the neutralised spelling too
        pairs += [
            (ph, n) for ph, d in pairs if (n := fits_after_nfkc(neutralise(d))) != d and len(n) >= 4
        ]
    for view in views:
        if (
            time.thread_time() - started > defaults.REDACT_BUDGET_S
        ):  # a hostile text: fail closed, nothing shown
            raise InputTooLarge("InputTooLarge")
        if neutralise is not None:
            view = fits_after_nfkc(neutralise(view))
        view = _keep_earlier_masks(view, pairs)
        again = _pass_one(view, current, cache, budget, depth)
        # a new value, or a known one only the view spells in a way pass one could not read
        if again.mapping != current or _held(again.text) > _held(out):
            out, current = again.text, again.mapping
    return _clean(out), current


def redact_text(
    text: str, mapping: dict[str, str], neutralise: Callable[[str], str] | None = None
) -> str:
    """Redact `text` with the run's map, continuing it in place. Any failure is a RedactionError.

    A second pass runs over the canonical view (and the JSON-unescaped view) of the INPUT: a secret hidden by a
    full-width letter, a zero-width space or a `\\u0041` escape is found there. When that pass finds something
    new (the map grows) the redacted VIEW is returned, trading fidelity of that one string for safety. The
    caller's `neutralise` (untrusted text: escape result markers and placeholder look-alikes) runs on the input
    and on every view BEFORE it is redacted, so the returned text is never a decoded view that was not
    neutralised: a `\\u003c<IPV4_2>` cannot come back as a real placeholder. Output is cleaned of NUL and lone
    surrogates last, so it always encodes.

    Base64 step (G4): every run of the base64 alphabet that pass one did not mask as a secret and that decodes to text is decoded;
    the decoded texts are scanned as ONE text by this same procedure (escaped with `neutralise_untrusted` whatever the caller's hook
    is, then views, decoded masks and nested base64 to `defaults.B64_MAX_DEPTH`), and a run whose decoded text held anything that
    scan masks is replaced whole by one `<ENCODED_n>` before pass one runs again. ENCODED is a secret kind, never stored or restored.
    A wrapped block (lines of one length) is decoded joined; when the join holds nothing, its lines are decoded one by one, and those
    lines are not counted as units (their decoded characters have a count of their own under the same limit); a block of 3 or more lines
    is also tried with its first or its last line left out (`unit.trims`, a trimmed join), counted the same way in `part_chars`. At most
    `defaults.B64_MAX_UNITS` units and `defaults.B64_MAX_DECODED_CHARS` decoded characters per call, the deadline read before
    each unit; past either, `InputTooLarge`; the decoded texts are scanned joined by a line holding `;`, and a decoded value of a kind
    that is never stored stays in the run's map (its plain copies are masked).

    The one choke point for input size. The cap is on the WORK, not only on the input: the text, the text after
    `neutralise`, and every view the second pass will scan must each be within `defaults.MAX_REDACT_CHARS`, else
    `InputTooLarge` (a RedactionError) is raised and nothing is redacted. NFKC expands some characters (U+FDFA
    becomes 18), so 87,000 of them are under the input cap and a 1.5-million-character view (24 s measured).
    That covers every caller that goes through `redact_text` / `redact_untrusted` / `redact_value` (document, tool
    result, model-written argument, eval case, card text, log and tick lines through `safe_head`, the judge and the
    vendor guardrail input); the registry (`guard/producers.py`) lists them. No bare `redact()` call remains outside
    this module: the second pass of `approvals/channel.py` `clean` is this function too."""
    _within_cap(text)
    started = time.thread_time()
    try:
        cache = getattr(mapping, "redact_cache", None)
        budget = _ScanBudget(started)
        out, current = _scan(text, mapping, cache, neutralise, budget, 0)
    except (InputTooLarge, TooDeep, RedactionError):
        raise  # as raised: the text of `NotSettled` (the settle loop's cap) is kept for the caller's log
    except Exception as exc:  # noqa: BLE001 - whatever the redactor raised, nothing is sent
        raise RedactionError(type(exc).__name__) from None
    # No `clear()` first: another thread (the model gate holds this map by reference) must never read it
    # empty. `current` is always the old map plus new entries: the redactor copies the map, only ever adds
    # to its copy, and numbers a new placeholder above every number already held (`redact._Redactor`).
    # STATED LIMIT (lead review round 2, m-new-7; older than this change): two threads that write ONE map at
    # the same time each number from their own copy, so two different values can get the same placeholder
    # and the later `update` wins. One run's map has one writer at a time today.
    mapping.update(current)
    return out


# The most sweeps one `enforce_map` call makes over a text. A text with nothing to replace takes one, an
# ordinary text with replacements two (the second finds nothing). Small and constant: past it the call fails.
ENFORCE_MAX_SWEEPS = 4
# The enforce step's own size cap (design review E1). The redaction cap (`defaults.MAX_REDACT_CHARS`) is a cap on
# text still to be redacted. What the gate holds has already been through a producer, and masking GROWS a text:
# a value of 3 characters becomes a placeholder of up to `<KIND_NNNNN>`. A document just under the redaction cap
# made of short values is longer than the cap once masked and was refused on every call. The factor is safe because
# one sweep cannot grow a text by more than `max placeholder length / 3` (a value under 3 characters is never
# replaced); `test_e1_the_growth_factor_covers_the_longest_placeholder` derives that bound from the redactor's own
# labels. WHAT IS BOUNDED (review rounds 2 and 3, dz2-M3, design M2): each input text stays under ENFORCE_MAX_CHARS and
# each sweep's output under ENFORCE_MAX_OUT_CHARS (checked after the sweep that made it); one `EnforceBudget` (one per
# `snapshot`, so one per chat call of the gate) bounds the characters of ALL texts of the call, the steps (one per text
# and one per held-back value that really occurs in a text: NOT one per value per sweep, so a long honest history is
# not refused for the size of the map) and the time. The time is a CPU deadline (`time.thread_time()`, the clock of
# `redact.py`) that is passed INTO the redactor's `sweep` (checked before each segment and each value replaced) and
# its build, and a wall-clock deadline checked between values: one `sweep` over a large text with many known values
# stops at the deadline (InputTooLarge), it is no longer unbounded.
ENFORCE_GROWTH_FACTOR = 8
ENFORCE_MAX_CHARS = ENFORCE_GROWTH_FACTOR * defaults.MAX_REDACT_CHARS
ENFORCE_MAX_OUT_CHARS = ENFORCE_GROWTH_FACTOR * ENFORCE_MAX_CHARS
ENFORCE_MAX_TOTAL_CHARS = (
    4 * ENFORCE_MAX_CHARS
)  # all texts of one chat call together (input; plus growth)
# Held-back values (a known value that is a piece of a placeholder or an edge value) one snapshot accepts. The
# old cap of 256 refused EVERY later call of a run that a hostile document had planted 257 values in (the map only
# grows). The work per held-back value is one substring test per text and round, and one sweep only where it occurs, so
# the cap is set by memory and the deadline, not by one call's step count. Past it the call is refused with
# `InputTooLarge` (gate code `mask_budget_exceeded`); the producer side should stop registering (core-b, request 3).
ENFORCE_MAX_HELD = 4096
# entries of the map one snapshot accepts (K): 20,480; past it, InputTooLarge
ENFORCE_MAX_ENTRIES = 5 * ENFORCE_MAX_HELD
# 32,768: one per text, one per held-back value that occurs in a text (per round)
ENFORCE_MAX_STEPS = 8 * ENFORCE_MAX_HELD
# Above defaults.MAX_MAP_ENTRIES on purpose: the run cap is checked after a producer call; these bound the call before it.


class EnforceBudget:
    """One deadline, one character budget and one step budget for every `enforce_map` call that shares a snapshot
    (the gate takes one snapshot per chat call). Raises `InputTooLarge` when one runs out. Not shared between
    threads. `cpu_deadline` is a `time.thread_time()` value (the redactor's clock): `enforce_map` passes it into
    `_Redactor.sweep`."""

    __slots__ = ("chars", "cpu_deadline", "deadline", "steps")

    def __init__(self) -> None:
        self.deadline = time.monotonic() + defaults.REDACT_BUDGET_S
        self.cpu_deadline = time.thread_time() + defaults.REDACT_BUDGET_S
        self.chars, self.steps = ENFORCE_MAX_TOTAL_CHARS, ENFORCE_MAX_STEPS

    def check(self) -> None:
        if time.monotonic() > self.deadline or time.thread_time() > self.cpu_deadline:
            raise InputTooLarge("InputTooLarge")

    def spend_chars(self, n: int) -> None:
        self.chars -= n
        if self.chars < 0:
            raise InputTooLarge("InputTooLarge")

    def step(self) -> None:
        self.steps -= 1
        if self.steps < 0:
            raise InputTooLarge("InputTooLarge")
        if self.steps % 16 == 0:
            self.check()


_NOT_RAW = re.compile(r"<[A-Z][A-Z0-9]*_\d+>")
# A known value that begins with the tail of a placeholder (`>abc`, `ECRET_1>abc`) or ends with the head of one
# (`xyz<`, `xyz<SEC`) can be matched ACROSS the edge of a placeholder the same sweep has just written, and would
# damage it (`<SECRET_1<SECRET_2>`). Such a value is held back like a piece of a placeholder (design review E2).
# Review round 2 (dz2-M2) claimed that `S3cr3t>abcdef` (two secret kinds `S3cr3t` and `>abcdef`) leaks the tail:
# NOT REPRODUCED (the placeholder `<SECRET_1>` and the raw `>` that follows it are two characters; the held-back
# sweep then finds `>abcdef`); a swept-first order was tried and rejected: it lets a shorter edge value cut a longer
# secret (`pass>` and `>abc` in `pass>abc` left `pass` raw). `tests/test_model_gate.py::test_r2_m2_*` pin the case.
_EDGE_HEAD = re.compile(r"[A-Z0-9_]*>")
_EDGE_TAIL = re.compile(r"<[A-Z0-9_]*\Z")


def _is_edge_value(original: str) -> bool:
    return _EDGE_HEAD.match(original) is not None or _EDGE_TAIL.search(original) is not None


def enforce_map(text: str, mapping: Mapping[str, str]) -> str:
    """`text` with every raw copy of a value the map already holds replaced by that value's EXISTING
    placeholder. No pattern is run: nothing new is found, no entry is added, no placeholder is invented,
    and `mapping` (a `collections.abc.Mapping`, placeholder -> original) and its `redact_cache` are never
    written. A text that holds no raw copy comes back equal. IDEMPOTENT: the text returned is one the
    sweep leaves unchanged, so `enforce_map(enforce_map(x, m), m) == enforce_map(x, m)`.

    The replace is the redactor's own final sweep (`guard/redact.py` `_Redactor.sweep`), so the rules are
    the ones every producer's output already follows: longest originals first (a value that contains
    another is replaced whole); nothing is replaced inside a placeholder already in the text. Which copies
    (`redact._sweep`): a value of a secret kind of 4 characters or more, every copy; any other value, only
    where no ASCII letter or digit touches it (a PHONE value: where no digit does; `redact._joins`, ticket G8).

    Two things are added to the sweep.
    1. Held-back values. Inside one stretch of text the sweep replaces value after value and does not look
       again at the placeholders it has just written, so a shorter known value that is itself a piece of a
       placeholder of this map (`SECRET`, `UUID_1`) would be replaced INSIDE a placeholder written a moment
       before (`<<SECRET_1>_2>`). Every value that the sweep can replace at all and that is a piece of one
       of the map's placeholders is therefore held back and swept
       afterwards, one at a time, longest first: each of those sweeps starts by setting every placeholder
       in the text aside. A value the sweep never replaces (see the limits) is not held back.
    2. Repeat until nothing changes (lead review round 2, MJ2). One sweep is not a fixed point: an
       identifier glued to a shorter secret (`abc123xyz9Zq9x`) is skipped because a letter touches it, the
       secret is then replaced, and the identifier stands alone and raw (`abc123xyz9<SECRET_1>`). So the
       sweep runs again while the text changes, at most `ENFORCE_MAX_SWEEPS` times; a text that is still
       changing then is REFUSED (RedactionError: fail closed, the gate makes no call), never sent half done.

    Limits, on purpose (each pinned by a test in tests/test_runmap_enforce_map.py):
    - NOT replaced at all: a value under 3 characters; and, unless it is a secret kind of 4 characters or
      more, a value that is all digits and under 6 characters or a common word (`redact._COMMON`).
    - A value that is not a secret kind of 4 or more is left where an ASCII letter or digit (for a PHONE value: a
      digit) touches it and
      keeps touching it after every other replacement.
    - Only the spelling held in the map is replaced (for a value that is not ASCII, also its folded NFKC spellings,
      which the redactor sweeps with it: each is its own held-back item when it is a piece of a placeholder). A copy hidden by full-width letters, a zero-width
      space or an escape is NOT found here: finding those is the pattern redactor's work (`redact_text`),
      and returning a decoded view from here could turn a look-alike into a real placeholder. The text is
      not cleaned either: a copy split by NUL characters (a UTF-16 document read as UTF-8 has one after
      every character) is not found. The gate's net reads those forms of a SECRET value (`held_in_views`, G13).
    - A value that itself holds a placeholder-shaped token (`ab<X_1>cd`) is never replaced: the sweep
      sets every token aside first, so the value never lies in one stretch of text.
    - A known value written inside angle brackets so that it reads as a token (the value `ABC_1` written
      as `<ABC_1>`) is taken for a placeholder and left.
    - Two known values that overlap in the text without one containing the other (`abcd` and `cdef` in
      `abcdef`): since G9 the sweep reads the text back with the map's placeholders put back and replaces the
      readable rest by the EXISTING placeholder of a value that covers it, a secret's where one does, else the
      identifier's (`<SECRET_1><SECRET_2>`); the map is not written. A held-back value is not in this sweep's
      map: its rest stays here. The net (`held_value_left`) checks values of SECRET kinds only: the rest of a held-back
      secret refuses the call, the rest of a held-back identifier passes the net silently (a stated limit).
      Where one value is held under both an identifier and a secret kind, since G4 the secret's placeholder is the one used.
    - A known value that begins with the tail of a placeholder (`>abc`) or ends with its head is swept first,
      on the raw text, with every placeholder set aside; where it touches a placeholder that is ALREADY in the
      text it is not replaced (the `>` belongs to that placeholder) and its tail stays readable (4 or more characters
      of a SECRET value there: the net refuses the call, `_touching_piece`, G13).
    - A map key that is not a genuine placeholder (`<host_1>`: lower case) is not set aside by any sweep,
      so a known value that is a piece of it (`host`) is replaced inside it, held back or not: a damaged
      placeholder, no raw value. The redactor only writes genuine keys.
    - A chain of glued identifiers that needs more than `ENFORCE_MAX_SWEEPS` sweeps is refused, not sent.

    Bounds: the input cap of `redact_text` and the time budget `defaults.REDACT_BUDGET_S`, but one budget for ALL
    texts that share a snapshot (`EnforceBudget`: time, characters, steps; see ENFORCE_MAX_CHARS for what is and is
    not bounded; one regex scan of one stretch of text inside the redactor cannot be interrupted). Past any of them, `InputTooLarge`. Any other failure (a map that is not text to
    text) is a RedactionError that names the error's type and never the text."""
    try:
        if len(text) > ENFORCE_MAX_CHARS:
            raise InputTooLarge("InputTooLarge")
        snap = snapshot(mapping)
        budget = snap.budget
        budget.spend_chars(len(text))
        budget.step()  # one step per text
        first, held_back = snap.sweeps
        deadline = budget.cpu_deadline
        out = text
        for _ in range(ENFORCE_MAX_SWEEPS):
            before = out
            out = first.sweep(out, deadline)
            for n, (spelling, placeholder, rule) in enumerate(held_back):
                if not n % 64:
                    budget.check()  # the substring tests below cost one pass over the text each
                if spelling in out:
                    budget.step()  # only a value that really occurs costs a step
                    out = _sweep_held(out, spelling, placeholder, rule, deadline)
            if len(out) > ENFORCE_MAX_OUT_CHARS:
                raise InputTooLarge("InputTooLarge")
            budget.check()  # a hostile text or map: fail closed
            if out == before:
                budget.spend_chars(max(0, len(out) - len(text)))
                return out
    except RedactionError:
        raise
    except Exception as exc:  # noqa: BLE001 - whatever the sweep raised, nothing is sent
        raise RedactionError(type(exc).__name__) from None
    raise RedactionError("NotSettled")  # still changing after the last sweep: nothing is sent


class MapSnapshot(dict):
    """ONE copy of a run's map, taken at one moment, with the sweeps `enforce_map` needs built from it once.
    `enforce_map(text, a_snapshot)` reuses them, so a caller with many texts (the model gate: every message
    and document of one call) copies the map once and builds its patterns at most once, and every text of
    that call is enforced against the same entries. Private to its maker: not shared between threads, and
    not kept after the call (a value the run learns later is in the next snapshot)."""

    sweeps: tuple[Any, list[tuple[str, str, Any]]]  # the main sweep, the held-back spellings
    budget: EnforceBudget
    secret_values: frozenset[str]  # originals swept in every copy (a secret kind of 4+ characters)
    checker: Any  # a redactor over exactly those secret values, for `held_value_left`
    # `_piece_index` of the secret values (G13)
    pieces: Any  # `PieceIndex`


def _rules_conflict(known: Mapping[str, str]) -> bool:
    """True when one original is held under two placeholders whose sweep rules differ (a secret kind and an
    identifier kind). Plain duplicates with one rule are not a conflict."""
    rules: dict[str, set[Any]] = {}
    for ph, original in known.items():
        rule = _sweep(ph, original)
        if rule is not None:
            rules.setdefault(original, set()).add(rule)
    return any(len(found) > 1 for found in rules.values())


def _late_values(known: Mapping[str, str]) -> dict[str, str]:
    """The entries to hold back: the sweep can replace the value (or one of its ALIAS spellings: a non-ASCII value
    is swept in its folded spellings too, `redact._alias_keys`) and it is a piece of one of the map's keys or an
    edge value (`_is_edge_value`). A value is a piece of a key only if all its characters occur in the keys, so
    most values are dismissed by one set test and only the rest are looked up in the joined keys; a value is
    looked up once however many placeholders hold it (design M2: the old test was one pass over all keys per
    value)."""
    tokens = "\n".join(known)
    alphabet = set(tokens)
    seen: dict[str, bool] = {}

    def held(spelling: str) -> bool:
        found = seen.get(spelling)
        if found is None:
            found = _is_edge_value(spelling) or (
                len(spelling) <= len(tokens)
                and alphabet.issuperset(spelling)
                and spelling in tokens
            )
            seen[spelling] = found
        return found

    late: dict[str, str] = {}
    for ph, original in known.items():
        if _sweep(ph, original) is None:
            continue
        spellings = (original,) if _plain(original) else (original, *_alias_keys(original))
        if any(held(spelling) for spelling in spellings if spelling):
            late[ph] = original
    return late


def _sweep_held(text: str, spelling: str, placeholder: str, rule: Any, deadline: float) -> str:
    """The redactor's final sweep for ONE spelling of one held-back value: every placeholder-shaped token is set
    aside, then the free stretches are replaced by the spelling's rule (`redact._sweep`). Not a `_Redactor`: a
    redactor built for a non-ASCII value would sweep that value's folded spellings too, in the same pass, and cut
    the placeholder it had just written (`<<TENANT_1>_1>`: code review round 3, M2). Each spelling is its own
    held-back item, longest first."""
    parts = _PLACEHOLDER.split(text)
    for i in range(0, len(parts), 2):
        if not i % 512 and time.thread_time() > deadline:
            raise InputTooLarge("InputTooLarge")
        segment = parts[i]
        if spelling in segment:
            if rule is _EVERY_COPY:
                parts[i] = segment.replace(spelling, placeholder)
            else:
                parts[i] = _replace_standalone(segment, spelling, placeholder, _joins(placeholder))
    return "".join(parts)


def _built(
    entries: dict[str, str], holder: dict[str, Any] | None, slot: str, deadline: float
) -> Any:
    """A `_Redactor` over `entries`, its patterns BUILT now (inside the budget), reusing the state `holder[slot]`
    holds when it was built for the same entries and storing the new state there as ONE assignment (a pair), so a
    thread that shares the holder never reads half of an update. `holder` is the bound gate's own: the run's
    `redact_cache` is never written."""
    scratch: dict[str, Any] = {}
    pair = holder.get(slot) if holder is not None else None
    if pair is not None and pair[0] == entries:
        scratch = {"map": pair[0], "state": pair[1]}
    redactor = _Redactor(entries, scratch, deadline)
    redactor.sweep("", deadline)  # builds the patterns now, under the deadline
    if holder is not None and "map" in scratch and "state" in scratch:
        holder[slot] = (scratch["map"], scratch["state"])
    return redactor


def _held_items(late: Mapping[str, str], stored: set[str]) -> list[tuple[str, str, Any]]:
    """(spelling, placeholder, rule) for every spelling of every held-back value, longest first: the value itself and,
    for a non-ASCII value, the folded spellings the redactor would sweep with it (`redact._alias_keys`; one that is
    itself a stored value is that value's own item)."""
    items: dict[str, tuple[str, str, Any]] = {}
    for ph, original in late.items():
        spellings = (original,) if _plain(original) else (original, *_alias_keys(original))
        for spelling in spellings:
            rule = _sweep(ph, spelling)
            if spelling and rule is not None and (spelling == original or spelling not in stored):
                items.setdefault(spelling, (spelling, ph, rule))
    return sorted(items.values(), key=lambda item: -len(item[0]))


def snapshot(mapping: Mapping[str, str], cache: dict[str, Any] | None = None) -> MapSnapshot:
    """A `MapSnapshot` of `mapping` (itself when it already is one). `dict(mapping)` on a RunMap or a plain
    dict is one atomic copy, so a writer in another thread is seen whole or not at all. Never writes
    `mapping` or its `redact_cache`. Any failure (a map that is not text to text, a cache attribute that
    raises) is a RedactionError that names the error's type. Bounded: more than `ENFORCE_MAX_ENTRIES` entries or
    `ENFORCE_MAX_HELD` held-back values is `InputTooLarge`; the build runs under the budget's deadline.

    `cache`: a dict the CALLER owns (the bound gate keeps one per run) in which the built patterns of the held-back
    case are kept between calls. The run's own `redact_cache` cannot serve there: it is valid for the whole map, and
    a map with one held-back value is swept in two parts."""
    if isinstance(mapping, MapSnapshot):
        return mapping
    try:
        known = MapSnapshot(mapping)
        if len(known) > ENFORCE_MAX_ENTRIES:
            raise InputTooLarge("InputTooLarge")
        known.budget = budget = EnforceBudget()
        deadline = budget.cpu_deadline
        late = _late_values(known)
        if len(late) > ENFORCE_MAX_HELD:
            raise InputTooLarge("InputTooLarge")
        if _rules_conflict(known):
            # One original under two placeholders (E5). Since G4 the redactor itself keeps the secret kind's rule for that
            # original (the `_build` tie-break); this re-sort is kept because it also puts every every-copy entry before the
            # others, which decides the order of DIFFERENT overlapping originals at the gate (test_e5b). Built fresh: the
            # run's cache holds the map's own order.
            ordered = dict(sorted(known.items(), key=lambda kv: _sweep(*kv) is not _EVERY_COPY))
            first = _built(
                {ph: o for ph, o in ordered.items() if ph not in late}, cache, "first", deadline
            )
        elif late:
            first = _built(
                {ph: o for ph, o in known.items() if ph not in late}, cache, "first", deadline
            )
        else:
            # a private shallow copy of the run's built patterns: reused, and the caller's cache is not written
            first = _Redactor(known, dict(getattr(mapping, "redact_cache", None) or {}), deadline)
            first.sweep("", deadline)
        held_back = _held_items(late, set(known.values()))
        known.sweeps = (first, held_back)
        secrets = {ph: o for ph, o in known.items() if _sweep(ph, o) is _EVERY_COPY}
        known.secret_values = frozenset(secrets.values())
        known.checker = _built(secrets, cache, "check", deadline) if secrets else None
        known.pieces = _piece_index(known.secret_values)
    except RedactionError:
        raise
    except Exception as exc:  # noqa: BLE001 - fail closed
        raise RedactionError(type(exc).__name__) from None
    return known


# G13 (E19 M1): the shortest piece of a secret value that the net reads as a leak where it touches a placeholder.
NET_MIN_PIECE = 4
# G13b (design M-1): a piece that is only the public start of a value (its URL scheme `https://`, `postgres://`, or an
# auth word `Bearer `) or only separator characters is no leak: `https://<HOSTNAME_1>/health` is ordinary text beside a
# WEBHOOK value that starts `https://hooks...`. A piece that goes one character past that start (the scheme plus one letter) still is.
_LEAD = re.compile(
    r"(?:[A-Za-z][A-Za-z0-9+.\-]{0,14}://"
    r"|(?i:Bearer|Basic|Token|Digest|OAuth|ApiKey|Negotiate|NTLM|AWS4-HMAC-SHA256|Bot|Key)[ \t]+)"
)
_SEPARATORS = " \t\r\n/\\:;,.?&=#@!-_+*~|<>()[]{}'\"%"
_LOOKUP_COST = 64  # characters one piece lookup charges to the call budget (a compare stops at the first difference)
_KEY_HITS_MAX = 4096  # G13c: the most head hits the net reads around one key (both sides); past it InputTooLarge
PieceIndex = tuple[
    list[str],
    dict[int, list[str]],
    list[str],
    list[str],
    list[str],
    frozenset[str],
    frozenset[str],
    int,
]


def _piece_index(values: frozenset[str]) -> PieceIndex:
    """G13: the secret values longer than `NET_MIN_PIECE` that have no public start, sorted; those that have one (G13b:
    `_LEAD`; only starts of `NET_MIN_PIECE` or more matter), sorted, by the length of that start; the reversals of all of
    them, sorted; G13c: the values made only of separator characters (a piece of those is read even where it is only
    separators), forward and reversed, sorted, which are not in the lists before; the first and the last
    `NET_MIN_PIECE` characters of each; the longest length of any value (kept here so a chunk does not scan the
    values). `_touching_piece` looks a piece up by bisection."""
    fwd = [v for v in values if len(v) > NET_MIN_PIECE]
    plain: list[str] = []
    leaded: dict[int, list[str]] = {}
    seps: list[str] = []
    for v in fwd:
        lead = _LEAD.match(v)
        if not v.strip(_SEPARATORS):
            seps.append(v)
        elif lead and lead.end() >= NET_MIN_PIECE:
            leaded.setdefault(lead.end(), []).append(v)
        else:
            plain.append(v)
    plain.sort()
    for group in leaded.values():
        group.sort()
    seps.sort()
    rev = sorted(v[::-1] for v in fwd if v.strip(_SEPARATORS))
    seps_rev = sorted(v[::-1] for v in seps)
    heads = frozenset(v[:NET_MIN_PIECE] for v in fwd)
    tails = frozenset(v[-NET_MIN_PIECE:] for v in fwd)
    return plain, leaded, rev, seps, seps_rev, heads, tails, max(map(len, values), default=0)


def _digest(piece: str) -> bytes:
    """G13c: a 16-byte digest of a long piece (what `_touching_piece` remembers instead of the piece)."""
    return hashlib.blake2b(piece.encode("utf-8", "surrogatepass"), digest_size=16).digest()


def _starts_one(ordered: list[str], piece: str) -> bool:
    """True when some string of the sorted list `ordered` starts with `piece` (a string equal to it counts)."""
    i = bisect.bisect_left(ordered, piece)
    return i < len(ordered) and ordered[i].startswith(piece)


def _touching_piece(text: str, snap: MapSnapshot) -> bool:
    """G13 (E19 M1): True when a KEY of the map has, right before it, a piece of `NET_MIN_PIECE` or more characters
    that is the START of a secret value (shorter than or equal to the value), or right after it a piece that is the
    END of one: `hunter2-<SECRET_2>`, `<SECRET_1>-ZZZZ`. Such a piece is what is left when two known values overlap and
    one was masked across the other, whatever the placeholder holds. Not a piece (G13b, design M-1): characters that
    are only separators, and the public start of a value (`https://`, `Bearer `; `_LEAD`) taken alone: ordinary text
    beside a placeholder (`https://<HOSTNAME_1>/health`) is not refused because a webhook value starts the same way;
    a scheme plus one more character is a piece. G13c (m2): the separator rule exempts a piece only because of the
    value it is a piece OF: a piece that starts (ends) a value made ONLY of separators (`!!!!!!!!`, `....----`) is a
    piece however short, and a piece of separators that starts a value with other characters (`-----BEGIN`) is not. G13c (m1): the public auth words of `_LEAD` are read in any letter case
    (`bearer `, `BEARER `) and are `Bearer`, `Basic`, `Token`, `Digest`, `OAuth`, `ApiKey`, `Negotiate`, `NTLM`,
    `AWS4-HMAC-SHA256`, `Bot`, `Key`; any other word before a secret (a custom scheme) is not exempt. Stated limit:
    a secret whose own first characters are ordinary words (`the quick brown fox`) refuses text that starts the same way
    beside a key (`the <HOST_1>`; the net cannot tell a copy of those words from a leak), and that refusal stays for
    the run (the message stays in the history); it is the same `held_value_left` code as a leak (pinned, G13c-7). Only
    the text between the key and the next (or previous) key is read, at most the longest value's length minus one.
    Cost (G13c): a position is tested by its first (left) or last (right) `NET_MIN_PIECE` characters (a slice of
    that size) BEFORE the piece is cut, so a gap with no head hit copies nothing and a hit copies one piece (the
    earlier code cut a piece of up to the longest value's length at every position: quadratic in the gap, unbudgeted).
    A piece is looked up only where those characters are those of a value; a piece already looked up in this text is
    not looked up, nor charged, again; `seen` keeps the piece itself when it is at most `_LOOKUP_COST` characters and
    else a 16-byte digest, so its memory does not grow with the length of the pieces (it held every piece whole: about
    370 MB at a 16,000-character value on a hostile gap); each lookup spends at most `_LOOKUP_COST` characters of the
    call's budget (`InputTooLarge` past it) and the deadline is read every 256 hits. At most `_KEY_HITS_MAX` head hits
    are read around one key (both sides together, repeated pieces included): past it `InputTooLarge`, which the
    gate reports as `mask_budget_exceeded` (fail closed: a hostile run of one head repeated, one hit a character,
    would otherwise cost the whole call's budget; the 1,978-input property corpus never gets near it)."""
    plain, leaded, rev, seps, seps_rev, heads, tails, longest = snap.pieces
    if not heads:
        return False
    budget, k = snap.budget, NET_MIN_PIECE
    tokens = [m.span() for m in _PLACEHOLDER.finditer(text) if m.group() in snap]
    seen: set[tuple[bool, str | bytes]] = (
        set()
    )  # the pieces looked up in this text that were not a leak
    hits = 0
    for n, (start, end) in enumerate(tokens):
        if not n % 256:
            budget.check()
        before = tokens[n - 1][1] if n else 0
        after = tokens[n + 1][0] if n + 1 < len(tokens) else len(text)
        left = text[max(before, start - longest + 1) : start]
        key_hits = 0
        for i in range(len(left) - k, -1, -1):  # the piece left[i:] ends at the key
            if left[i : i + k] not in heads:
                continue
            key_hits += 1
            if key_hits > _KEY_HITS_MAX:
                raise InputTooLarge("InputTooLarge")
            hits += 1
            if not hits % 256:
                budget.check()
            piece = left[i:]
            mark = (True, piece if len(piece) <= _LOOKUP_COST else _digest(piece))
            if mark in seen:
                continue
            seen.add(mark)
            budget.spend_chars(min(len(piece), _LOOKUP_COST))
            if (
                _starts_one(plain, piece)
                or any(
                    len(piece) > lead and _starts_one(group, piece)
                    for lead, group in leaded.items()
                )
                if piece.strip(_SEPARATORS)
                else _starts_one(seps, piece)
            ):
                return True
        right = text[end : min(after, end + longest - 1)]
        for j in range(k, len(right) + 1):  # the piece right[:j] starts at the key
            if right[j - k : j] not in tails:
                continue
            key_hits += 1
            if key_hits > _KEY_HITS_MAX:
                raise InputTooLarge("InputTooLarge")
            hits += 1
            if not hits % 256:
                budget.check()
            piece = right[:j]
            mark = (False, piece if len(piece) <= _LOOKUP_COST else _digest(piece))
            if mark in seen:
                continue
            seen.add(mark)
            budget.spend_chars(min(len(piece), _LOOKUP_COST))
            if _starts_one(rev if piece.strip(_SEPARATORS) else seps_rev, piece[::-1]):
                return True
    return False


def held_in_views(text: str, snap: MapSnapshot) -> bool:
    """G13 (E19 M2): the net over the forms of `text` a reader (or the model) may decode: the text without NUL and lone
    surrogates (a UTF-16 document read as UTF-8) and, when it holds a non-ASCII character or `\\`, `%` or `&`, every
    `_views` form of that. True when `held_value_left` finds a secret value in any of them (that is the sweep over
    the form AND the piece rule `_touching_piece`, so a piece beside a key in a decoded form refuses too). Each
    view's characters are spent from the call's budget, and the deadline is read before each window's views are
    built; a text whose views would pass `defaults.MAX_REDACT_CHARS` is read in overlapping windows (`_windows`).
    `_views` can raise `InputTooLarge` or `TooDeep`: the caller refuses the call. Stated limits: a copy spelled in
    several stacked layers (`%26%23...`, up to `SCRUB_MAX_LAYERS` = 8 undone; each layer can multiply the spelling by up
    to 10) across a window edge of a text over `VIEW_WINDOW` characters is missed when the spelling is longer than the
    overlap (`WINDOW_OVERLAP_MAX`); the producers read the same layers whole, so this matters only where a producer was
    bypassed. Not pinned: the stacked-layer limit."""
    if not snap.secret_values:
        return False
    cleaned = _clean(text)
    if cleaned != text:
        snap.budget.spend_chars(len(cleaned))
        snap.budget.check()
        if held_value_left(cleaned, snap):
            return True
    if cleaned.isascii() and not any(c in cleaned for c in "\\%&"):
        return False
    for window in _windows(cleaned, snap.pieces[-1]):
        snap.budget.check()
        for view in _views(window):
            snap.budget.spend_chars(len(view))
            snap.budget.check()
            if held_value_left(view, snap):
                return True
    return False


# G13: a text longer than this is read by `held_in_views` in windows of this size (`_views` refuses a form past
# `defaults.MAX_REDACT_CHARS`, and NFKC can triple a text; the gate holds texts up to 8 times that cap).
VIEW_WINDOW = defaults.MAX_REDACT_CHARS // 4
# G13b (design M-2): the most two windows overlap. A value of up to (WINDOW_OVERLAP_MAX - 16) / 10 = 1,636 characters
# keeps the full overlap of ten characters a character; a longer one (a PEM key, a planted blob up to 65,536
# characters) is read with this overlap: its spelling of up to this many characters is found across a window edge
# (an NFKC or percent form is 1 to 3 characters a character, so values up to about 5,000 in a form of 3), and the
# raw copy is found by `held_value_left` on the whole text, which has no windows.
WINDOW_OVERLAP_MAX = VIEW_WINDOW // 4


def _windows(text: str, longest: int) -> list[str]:
    """`text` whole when it fits one window, else windows of `VIEW_WINDOW` characters that overlap by ten times the
    longest secret value plus 16 (an escaped spelling is at most ten characters a character: `&#1114111;`), at most
    `WINDOW_OVERLAP_MAX` (G13b: a long value no longer refuses every long text; its limit is in `held_in_views`)."""
    if len(text) <= VIEW_WINDOW:
        return [text]
    overlap = min(10 * longest + 16, WINDOW_OVERLAP_MAX)
    step = VIEW_WINDOW - overlap
    return [text[i : i + VIEW_WINDOW] for i in range(0, len(text) - overlap, step)]


def held_value_left(text: str, snap: MapSnapshot) -> bool:
    """Safety net for the gate (dz2-M2, design M3): True when a value of a SECRET kind (4 or more characters: the
    ones swept in every copy) still occurs raw in `text`. A placeholder-shaped token hides a value only if it is an
    exact KEY of the map; any other `<NAME_1>` (a forged `<AKIAEXAMPLE123_1>`) is opened up first, because the
    sweep itself sets every placeholder-shaped token aside. One pass of the same finder the sweep uses, under the
    call's deadline. Never returns or logs the value. A value that spans two chunks the gate enforced one by one
    (a fixed framing word between) is not seen here: a stated limit of the gate. Since G9 the checker's sweep reads
    the text back: a secret value spelled across a placeholder is found; that sweep can raise `InputTooLarge` (its
    work count, the deadline, `SpelledNotSettled`), which `_chunk` does not catch: `_enforced` reports it as
    `mask_budget_exceeded`. Since G13 the piece rule runs too (`_touching_piece`: a piece of a secret value beside a
    key of the map, `hunter2-<HOST_1>`; G13b: not a bare URL scheme or separators). `held_in_views` calls this on each
    decoded form of a text."""
    if not snap.secret_values:
        return False
    opened = _NOT_RAW.sub(
        lambda m: m.group() if m.group() in snap else m.group().replace("<", "<\0"), text
    )
    if snap.checker.sweep(opened, snap.budget.cpu_deadline) != opened:
        return True
    return _touching_piece(text, snap)  # G13 (E19 M1)


SAFE_HEAD_NOTE = "(details withheld)"


def safe_head(text: str, limit: int, mapping: dict[str, str] | None = None) -> str:
    """Redact FIRST, then keep the first `limit` characters: the order every short model-bound or logged message
    (an exception text, a validation error, a card line) needs, because a cut first splits a secret and the
    redactor no longer sees a whole one. The text is redacted up to the redactor's cap (`redact_bounded`: past the
    cap it is cut for bounded work and the end of the result is dropped), then the head is kept.
    Never raises: a text the redactor refuses (too large after NFKC, nested too deep, or any failure) becomes a
    fixed note."""
    try:
        return redact_bounded(text, {} if mapping is None else mapping)[0][:limit]
    except RedactionError:
        return SAFE_HEAD_NOTE


def drop_margin(text: str) -> str:
    """The end of a text cut at the redaction cap, dropped: `defaults.cut_margin` characters, and back to the last
    whitespace within 256 characters so the cut does not fall inside a word."""
    kept = text[: max(len(text) - defaults.cut_margin(len(text)), 0)]
    tail = kept[-256:]
    i = max(tail.rfind(" "), tail.rfind(chr(10)))
    return kept[: len(kept) - len(tail) + i + 1].rstrip(" ") if i >= 0 and len(kept) > 256 else kept


def redact_bounded(
    text: str, mapping: dict[str, str], neutralise: Callable[[str], str] | None = None
) -> tuple[str, bool]:
    """`redact_text` with bounded work for a text of any size: up to `defaults.MAX_REDACT_CHARS` the text is redacted
    whole (no cut before the redaction); past it the text is cut at the cap, redacted, and the last
    `defaults.CUT_MARGIN` characters of the result are dropped, because a secret straddling the cut is only a
    fragment there. Returns (redacted text, whether it was cut)."""
    cut = len(text) > defaults.MAX_REDACT_CHARS
    out = redact_text(text[: defaults.MAX_REDACT_CHARS], mapping, neutralise)
    if cut:
        out = drop_margin(out)
    return out, cut


def redact_value(value: Any, mapping: dict[str, str]) -> Any:
    """`redact_text` over every string (and dict key) inside a JSON-shaped value. The total text is capped too (a
    value of many small strings is as costly as one big one). The total is the expansion estimate of every string
    and key. The callers' own bounds (the model's output tokens for a tool call's inputs, `evidence.py` for the
    proposal's inputs) keep the real input far below the cap; this cap is the backstop, not the usual limit."""
    if _chars(value) > defaults.MAX_REDACT_CHARS:
        raise InputTooLarge("InputTooLarge")
    return _redact_value(value, mapping)


def _chars(value: Any) -> int:
    if isinstance(value, str):
        return _expanded_len(value)
    if isinstance(value, dict):
        return sum(_chars(k) + _chars(v) for k, v in value.items())
    if isinstance(value, list):
        return sum(_chars(v) for v in value)
    return 0


def _redact_value(value: Any, mapping: dict[str, str]) -> Any:
    if isinstance(value, str):
        return redact_text(value, mapping)
    if isinstance(value, dict):
        return {
            (redact_text(k, mapping) if isinstance(k, str) else k): _redact_value(v, mapping)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_redact_value(v, mapping) for v in value]
    return value


def restore_text(text: str, mapping: dict[str, str], kinds: frozenset[str] | None = None) -> str:
    """One pass, only stored kinds: a restored value is never expanded again, a secret kind never restored."""
    allowed = storable(mapping, kinds)
    return PLACEHOLDER.sub(lambda m: allowed.get(m.group(0), m.group(0)), text)


def restore_value(value: Any, mapping: dict[str, str], kinds: frozenset[str] | None = None) -> Any:
    if isinstance(value, str):
        return restore_text(value, mapping, kinds)
    if isinstance(value, dict):
        return {k: restore_value(v, mapping, kinds) for k, v in value.items()}
    if isinstance(value, list):
        return [restore_value(v, mapping, kinds) for v in value]
    return value


def has_placeholder(value: Any) -> bool:
    """True if any string in the value still holds a ``<KIND_n>`` placeholder (so it could not be restored)."""
    if isinstance(value, str):
        return PLACEHOLDER.search(value) is not None
    if isinstance(value, dict):
        return any(has_placeholder(v) for v in value.values())
    if isinstance(value, list):
        return any(has_placeholder(v) for v in value)
    return False
