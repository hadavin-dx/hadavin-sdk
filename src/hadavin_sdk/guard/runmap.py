"""The run's one redaction map (K5, design 6.3, M14, R2, R6).

One map per run, started at intake (empty until K4) and continued for the document and every tool result, so a
value always gets the same placeholder and a placeholder never restores to a different value. Only **identifier
kinds** are ever stored or restored; secret and regulated kinds are placeholdered for the model but their originals
live in memory for the run and nowhere else.

Pure functions over a plain ``dict[str, str]`` (placeholder -> original). Stdlib and the studio redactor only.
"""

from __future__ import annotations

import collections
import functools
import hashlib
import html
import re
import time
import unicodedata
from collections.abc import Callable
from typing import Any
from urllib.parse import unquote

from hadavin_sdk import defaults
from hadavin_sdk.guard import hidden
from hadavin_sdk.guard.redact import ARN_TAIL, PATTERNS, SECRET_KINDS, kind_of, mask_spans, redact

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
    return canonical(fits_after_nfkc(text))


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


def undo(text: str, clean: bool = False, strip_hidden: bool = False) -> str:
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
    dropped before every decoder (the tail a cut left). With `strip_hidden`, every round ends by removing the hidden
    items (`hidden.strip`, the joined reading) that the decoders produced or exposed, so one that cuts an encoding
    token (`%4` + a colour code + `1KIA...`) no longer hides what the token spells; a placeholder or marker shape that
    only that removal would create is written in its escaped look-alike form (`_no_created_shapes`). The default keeps
    every existing caller unchanged."""
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
        if strip_hidden:
            step = _no_created_shapes(step, hidden.strip(step)[0])
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
    full-width `＜ＩＰＶ４＿２＞` becomes `<IPV4_2>`) with every ignorable character removed (a zero-width space, a
    variation selector or a Hangul filler inside a token no longer hides it). Ignorable = `hidden.IGNORABLE_RE`: the
    Unicode Default_Ignorable_Code_Point property plus the rest of category Cf (main dropped category Cf only)."""
    return hidden.IGNORABLE_RE.sub("", unicodedata.normalize("NFKC", text))


def _canonical_view(text: str) -> tuple[str, list[int]]:
    """The canonical form of `text` (NFKC, ignorable characters removed) and, for each canonical
    character, the index of the original character it came from."""
    chars: list[str] = []
    index: list[int] = []
    for i, c in enumerate(text):
        for d in unicodedata.normalize("NFKC", c):
            if not hidden.is_ignorable(d):
                chars.append(d)
                index.append(i)
    return "".join(chars), index


def replace_canonical(
    text: str, pattern: re.Pattern[str], repl: Callable[[re.Match[str]], str]
) -> str:
    """Find `pattern` in the canonical view of `text` and replace only the matched stretches IN THE ORIGINAL.
    The model keeps seeing the text as it was written (accents, CJK, emoji, joiners untouched); only a stretch
    that, once folded, is the thing being guarded (a placeholder, a result marker) is rewritten. All-ASCII text
    is its own canonical form."""
    if text.isascii():
        return pattern.sub(repl, text)
    canon, index = _canonical_view(text)
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
    check would treat it as that value. Every placeholder-shaped literal becomes a non-placeholder. Call it on
    `canonical(text)`, so Unicode look-alikes are already ASCII."""
    return replace_canonical(text, _LOOKALIKE, lambda m: f"\u2039{m.group(1)}_{m.group(2)}\u203a")


_MARKER = re.compile(r"<<(?=\s*(?:end\s+)?tool\s+result)", re.IGNORECASE)


def escape_markers(text: str) -> str:
    """Neutralise anything shaped like our result markers, in any case and spacing, including full-width and
    zero-width spellings (found in the canonical form, rewritten in the original; the rest of the text is left
    as it was written)."""
    return replace_canonical(text, _MARKER, lambda m: "[[")


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


def _repair(text: str) -> str:
    """Lone surrogates become '?' so the text always encodes. NUL is NOT touched here: it is a removed item, taken out
    with the other hidden items (`hidden.strip`) with the same glue rule."""
    return text.encode("utf-8", "replace").decode("utf-8", "replace")


def _views(text: str) -> list[str]:
    """Other forms a secret can hide in: the canonical view (NFKC, ignorable characters removed) and the same
    with JSON `\\uXXXX` escapes decoded. Only forms that differ from `text` are returned."""
    # `\\/` too (PHP writes every slash that way); `\\n` and the like are left alone here: a log line full of them
    # would come back with real newlines whenever the second pass finds anything.
    unescaped = fits_after_nfkc(json_unescape(text, simple="/"))
    out = []
    # the layers undone to a fixed point (percent, entity, backslash, NFKC, any order, up to the depth cap; deeper
    # raises TooDeep and nothing is redacted or shown): `%41KIA...`, `&#65;KIA...`, `password%3Dx`
    decoded = fits_after_nfkc(undo(text))
    views = [canonical(text), canonical(unescaped), decoded]
    # One more, only when it can differ from the plain decode (a decoder never removes a control character, so when
    # neither the text nor its decode holds a hidden item the stripped decode IS the plain one and is not computed):
    # the decode with the hidden items removed at the end of every round, so a hidden item that cuts an encoding
    # token (`%4` + a colour code + `1KIA...`) is read.
    if any(c in text for c in _ENCODED_MARKS) and (
        hidden.ANY.search(text) or hidden.ANY.search(decoded)
    ):
        views.append(fits_after_nfkc(undo(text, strip_hidden=True)))
    for view in views:
        view = _clean(view)
        if view != text and view not in out:
            out.append(view)
    return out


def _held(text: str) -> int:
    return len(PLACEHOLDER.findall(text))


_VALUE_END = frozenset(" \t\n;&,\"'")
_ENCODED_MARKS = ("%", chr(92), "&")
MAX_DECODED_MASKS = 256


def _decoded_masks(current: dict[str, str], text: str) -> list[tuple[str, str]]:
    """(placeholder, decoded original) for the values pass one masked WHOLE whose decoded spelling would stop a value
    pattern early (the decoded text holds white space of any kind, or `;`, `&`, `,` or a quote): `password=ab%3Bzq9` is
    one value in pass one and `password=ab;zq9` in the decoded view, which would mask only `ab`. Only entries whose
    original occurs in THIS text and holds an encoding character are considered (so earlier junk in the run's map cannot
    use up the slots); more than `MAX_DECODED_MASKS` of them, or one that cannot be decoded (nested too deep), cannot be
    paired and the text is refused (`InputTooLarge`, nothing shown), never skipped. Computed once per call."""
    out = []
    for ph, original in current.items():
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


def _keep_earlier_masks(view: str, pairs: list[tuple[str, str]], mapping: dict[str, str]) -> str:
    """Before a decoded VIEW is redacted, the decoded spelling of every value pass one masked is replaced by its
    placeholder: if the view then replaces the text, the part of the value its pattern would not reach is not shown.
    Every copy of every spelling is a span on the view as it stands and one rule puts the placeholders in
    (`redact.mask_spans`): values that overlap partially come back as ONE new placeholder for the merged text, issued
    into `mapping` (the map the view is then redacted with), so no piece of either value stays readable."""
    spans: list[tuple[int, int, str]] = []
    for ph, decoded in pairs:
        if not decoded:
            continue
        at = view.find(decoded)
        while at >= 0:
            spans.append((at, at + len(decoded), ph))
            at = view.find(decoded, at + 1)
    return mask_spans(view, spans, mapping) if spans else view


def _check_budget(started: float) -> None:
    """Refuse (`InputTooLarge`, nothing shown) when this call has used more than `defaults.REDACT_BUDGET_S`: a hostile
    text must not keep the process busy. Checked before every pass, so one call overruns the budget by at most one."""
    if time.monotonic() - started > defaults.REDACT_BUDGET_S:
        raise InputTooLarge("InputTooLarge")


def _no_created_shapes(before: str, after: str) -> str:
    """`after` is `before` with hidden items removed. Removing them must never ASSEMBLE a genuine-shaped placeholder or a
    result-marker shape that was not there as written: `<` + a colour code + `IPV4_2>` is harmless as written and a real
    looking `<IPV4_2>` once the colour code is gone. Every genuine-shaped placeholder that occurs more often in `after`
    than in `before` is written in the escaped look-alike form (`\u2039IPV4_2\u203a`, the spelling `escape_placeholders`
    writes), and a marker shape that occurs more often in the canonical form of `after` than in that of `before` is
    escaped by `escape_markers`. Counting, not positions: when a text holds the same placeholder both plainly and
    created, both are written escaped (it fails to the escaped spelling). Returns `after` itself when nothing was
    removed or nothing was created."""
    if after == before:
        return after
    fits_after_nfkc(before)
    fits_after_nfkc(after)
    had = collections.Counter(m.group(0) for m in PLACEHOLDER.finditer(before))
    now = collections.Counter(m.group(0) for m in PLACEHOLDER.finditer(after))
    created = {p for p, n in now.items() if n > had.get(p, 0)}
    if created:
        after = PLACEHOLDER.sub(
            lambda m: (
                f"\u2039{m.group(1)}_{m.group(2)}\u203a" if m.group(0) in created else m.group(0)
            ),
            after,
        )
    if len(_MARKER.findall(canonical(after))) > len(_MARKER.findall(canonical(before))):
        after = escape_markers(after)
    return after


def _refuse_forgery(out: str, mapping: dict[str, str]) -> None:
    """Last check on the output of an untrusted text: no result-marker shape and no genuine-shaped placeholder that is not
    a key of the call's map, read as written AND in the canonical form (a full-width spelling folds into one). A backstop
    behind the escaping and `_no_created_shapes`; it raises `RedactionError` (the callers turn that into a fixed note or
    an abstention) and never repairs."""
    for t in (out,) if out.isascii() else (out, canonical(out)):
        if _MARKER.search(t) or any(m.group(0) not in mapping for m in PLACEHOLDER.finditer(t)):
            raise RedactionError("forged marker or placeholder")


def _gap_pattern(value: str) -> re.Pattern[str]:
    """The value as the spaced reading can hold it: its characters, with ONE optional space between two neighbouring
    word characters (a run of hidden items between two word characters left exactly one space there, so no optional
    space ever competes with a character of the value: at each position there is at most one way to go on, and a search is
    linear). A value of fewer than 4 characters is matched only as a whole word, as the redactor's sweep does."""
    parts = []
    for i, c in enumerate(value):
        if i and hidden.is_word(value[i - 1]) and hidden.is_word(c):
            parts.append(" ?")
        parts.append(re.escape(c))
    body = "".join(parts)
    return re.compile(body if len(value) >= 4 else r"(?<!\w)" + body + r"(?!\w)")


gap_pattern = (
    _gap_pattern  # the name other guard modules use (tools: the scrub of handed-out secrets)
)


def _held_placeholders(found_text: str, joined: str, mapping: dict[str, str]) -> list[str]:
    """The placeholders this find pass put into `found_text` (one that stands in the text as written does not count)."""
    out: list[str] = []
    for ph in dict.fromkeys(m.group(0) for m in PLACEHOLDER.finditer(found_text)):
        if ph in mapping and found_text.count(ph) > joined.count(ph):
            out.append(ph)
    return out


def _redact_stripped(
    joined: str, spaced: str, mapping: dict[str, str], cache: dict | None, started: float
) -> tuple[str, dict[str, str]]:
    """Redact one text that holds no hidden item, given as its two readings (`hidden.strip`): values are FOUND in the
    joined reading and MASKED in the spaced reading, which is what the reader is given. Returns (text, map).

    1. Both readings equal: one pass over `spaced`.
    2. Otherwise a find pass over `joined`; the placeholders that stand in its result are the "held" values.
    3. "Needed" = the held values whose text does not occur as written in `spaced` (a value that does is masked by the
       sweep of known values in step 6) and that are not seed entries.
    4. More than `MAX_DECODED_MASKS` needed values: `InputTooLarge`, nothing shown.
    5. Each needed value is looked for in `spaced` by its gap pattern (`_gap_pattern`); every match is a span and the one
       span rule (`redact.mask_spans`) puts the placeholders in.
    6. The mask pass over that text with the map of the find pass. If a held value is then missing (not standing, and
       not inside a placeholder that took its place) the text is refused (`RedactionError`), never the joined result:
       the joined reading has lost the boundaries that main's behaviour relies on."""
    if joined == spaced:
        result = redact(spaced, mapping=mapping, _cache=cache)
        return result.text, result.mapping
    found = redact(joined, mapping=mapping, _cache=cache)
    held = _held_placeholders(found.text, joined, found.mapping)
    needed = [
        ph
        for ph in held
        if not found.mapping[ph].startswith("\0seed") and found.mapping[ph] not in spaced
    ]
    if len(needed) > MAX_DECODED_MASKS:
        raise InputTooLarge("InputTooLarge")
    spans: list[tuple[int, int, str]] = []
    for ph in needed:
        spans.extend(
            (m.start(), m.end(), ph) for m in _gap_pattern(found.mapping[ph]).finditer(spaced)
        )
    work = dict(found.mapping)
    masked = mask_spans(spaced, spans, work) if spans else spaced
    _check_budget(started)
    result = redact(masked, mapping=work, _cache=cache)
    standing = {m.group(0) for m in PLACEHOLDER.finditer(result.text)}
    for ph in held:
        value = found.mapping[ph]
        if ph not in standing and not any(value in result.mapping.get(q, "") for q in standing):
            raise RedactionError("held value lost")
    return result.text, result.mapping


def redact_text(
    text: str, mapping: dict[str, str], neutralise: Callable[[str], str] | None = None
) -> str:
    """Redact `text` with the run's map, continuing it in place. Any failure is a RedactionError.

    Hidden items (the removed and space-like characters and the escape sequences of `hidden`) are taken out FIRST, before
    anything else reads the text: the escaping step, the patterns and the decoded readings all see the text as a reader
    sees it. Values are found in the joined reading and masked in the spaced reading (`_redact_stripped`), so a key cut
    by a colour code is masked, and a word boundary that main relied on (`user` + bell + a key) stays one. Removing them
    never creates a placeholder or a marker shape (`_no_created_shapes`).

    A second pass runs over the canonical view (and the JSON-unescaped view, and the layers-undone views) of the INPUT: a
    secret hidden by a full-width letter, a zero-width space or a `\\u0041` escape is found there. When that pass finds
    something new (the map grows) the redacted VIEW is returned, trading fidelity of that one string for safety. The
    caller's `neutralise` (untrusted text: escape result markers and placeholder look-alikes) runs on the input
    and on every view BEFORE it is redacted, so the returned text is never a decoded view that was not
    neutralised: a `\\u003c<IPV4_2>` cannot come back as a real placeholder. For untrusted text a last check
    (`_refuse_forgery`) refuses an output that still holds a marker shape or a placeholder the call did not issue. Output
    is cleaned of NUL and lone surrogates last, so it always encodes.

    Passes (one pass = all patterns over one reading): the text 1 pass, or 2 when a run of hidden items stands between two
    word characters; each other reading the same; at most 10 in all. The 6-second budget is checked before every pass.

    The one choke point for input size. The cap is on the WORK, not only on the input: the text, the text after
    `neutralise`, and every view the second pass will scan must each be within `defaults.MAX_REDACT_CHARS`, else
    `InputTooLarge` (a RedactionError) is raised and nothing is redacted. NFKC expands some characters (U+FDFA
    becomes 18), so 87,000 of them are under the input cap and a 1.5-million-character view (24 s measured).
    That covers every caller that goes through `redact_text` / `redact_untrusted` / `redact_value` (document, tool
    result, model-written argument, eval case, card text, log and tick lines through `safe_head`, the judge and the
    vendor guardrail input); the registry (`guard/producers.py`) lists them. No bare `redact()` call remains outside
    this module: the second pass of `approvals/channel.py` `clean` is this function too."""
    _within_cap(text)
    started = time.monotonic()
    try:
        cache = getattr(mapping, "redact_cache", None)
        text = fits_after_nfkc(_repair(text))
        joined, spaced = hidden.strip(text)
        if joined is not text:
            same = spaced is joined
            joined = _no_created_shapes(text, joined)
            spaced = joined if same else _no_created_shapes(text, spaced)

        def esc(t: str) -> str:
            return fits_after_nfkc(neutralise(t)) if neutralise is not None else t

        e_text = esc(text)  # the escaped ORIGINAL: the decoded readings are built from it
        e_joined = e_text if joined is text else esc(joined)
        e_spaced = e_joined if spaced is joined else esc(spaced)
        _check_budget(started)
        out, current = _redact_stripped(e_joined, e_spaced, mapping, cache, started)
        # The decoded readings are built from the text with its hidden items already taken out (joined reading), never
        # from the original: a decoder reads across a run of hidden items, so the backslash that ends a string
        # terminator (ESC then backslash) followed by `n` became a newline, or by digits an octal escape, and cut the value.
        base = e_text if joined is text else e_joined
        scan = not base.isascii() or any(c in base for c in "\\%&")
        views = [v for v in (_views(base) if scan else []) if v not in (e_joined, e_spaced)]
        # What the caller's own cleaning leaves of a reading (the approval card deletes control characters before any
        # value is looked for, which main relied on) is a reading too, when it is not the one already read. They go
        # last, so every other reading keeps its masks; the cleaning must not create a shape either.
        cleaned: list[str] = []
        if joined is not text and hidden.strip(e_text)[0] not in (e_joined, e_spaced):
            cleaned.append(_no_created_shapes(text, e_text))
        if neutralise is not None:
            for v in views:
                if (
                    hidden.ANY.search(v)
                    and (c := esc(v)) != v
                    and hidden.strip(c)[0] not in hidden.strip(v)
                ):
                    cleaned.append(_no_created_shapes(v, c))
        views += [c for c in dict.fromkeys(cleaned) if c not in views]

        def make_pairs(cur: dict[str, str], bases: tuple[str, ...]) -> list[tuple[str, str]]:
            made: list[tuple[str, str]] = []
            for base in dict.fromkeys(bases):
                made += [p for p in _decoded_masks(cur, base) if p not in made]
            if (
                neutralise is not None
            ):  # the view is neutralised before it is redacted: pair the neutralised spelling too
                made += [
                    (ph, n)
                    for ph, d in made
                    if (n := esc(d)) != d and len(n) >= 4 and (ph, n) not in made
                ]
            # a decoded spelling that holds hidden items is looked for without them too (the view has none)
            made += [
                (ph, sj)
                for ph, d in made
                if (sj := hidden.strip(d)[0]) != d and len(sj) >= 4 and (ph, sj) not in made
            ]
            return made

        base_texts = (e_spaced, e_joined)
        pairs = make_pairs(current, base_texts) if views else []
        for view in views:
            _check_budget(started)  # a hostile text: fail closed, nothing shown
            vj, vs = hidden.strip(view)
            if vj is not view:
                same = vs is vj
                vj = _no_created_shapes(view, vj)
                vs = vj if same else _no_created_shapes(view, vs)
            same = vs is vj
            # a merged placeholder (W0) is issued into this copy, not into the finished map
            work = dict(current)
            vj = _keep_earlier_masks(esc(vj), pairs, work)
            vs = vj if same else _keep_earlier_masks(esc(vs), pairs, work)
            again, again_map = _redact_stripped(vj, vs, work, cache, started)
            # a new value, or a known one only the view spells in a way pass one could not read
            if again_map != current or _held(again) > _held(out):
                out, current = again, again_map
                # the values this reading found are carried into the readings still to come, so a later reading that
                # finds less does not replace the output with one that has lost them
                base_texts += (vj, vs)
                pairs = make_pairs(current, base_texts)
        out = _clean(out)
        if neutralise is neutralise_untrusted:
            _refuse_forgery(out, current)
    except (InputTooLarge, TooDeep):
        raise
    except Exception as exc:  # noqa: BLE001 - whatever the redactor raised, nothing is sent
        raise RedactionError(type(exc).__name__) from None
    mapping.clear()
    mapping.update(current)
    return out


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
