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
import bisect
import re
import time
import unicodedata
from collections.abc import Callable
from typing import Any
from urllib.parse import unquote

from hadavin_sdk import defaults
from hadavin_sdk.guard import hidden
from hadavin_sdk.guard.redact import (
    ARN_TAIL,
    MAX_DECODED_MASKS,
    PATTERNS,
    SECRET_KINDS,
    WITHHELD_NOTE,
    SpacedRunLimit,
    collapse_runs,
    gap_pattern,
    kind_of,
    mask_spans,
    redact,
    spaced_unknown,
)

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


class RedactorCrash(RedactionError):
    """The redactor itself raised something that is not one of its own refusals (a bug or a broken stand-in). Nothing
    is sent, and every catcher of `RedactionError` in the tool and logging path (`tools.redact_layered`, `tools._found_values`,
    `tools._first_decoded`, `tools.error_reason`, `safe_head`) lets it pass: a crash must stop the run, not be shown as an
    ordinary limit (batch 11, group 4). The agent loop turns it into the stop `redaction_error`."""


class InputTooLarge(RedactionError):
    """The text, or a view of it that the second pass would scan, is longer than `defaults.MAX_REDACT_CHARS`."""


class RedactionLimit(InputTooLarge):
    """A work limit fired on a text of ANY size (the time budget, the pass count, the number of values to pair, two
    readings that cannot be merged), not the size of the text. It is an `InputTooLarge` for every caller that already
    catches that, so nothing is shown; the tool paths (`tools.prepare_output`, `tools.error_reason`) turn it into the
    fixed withheld note, because a small text must still come back as text or as a note, never as a raised error that
    drops the whole run (class: a limit reported as a size error, PR H batch 7, issue 2)."""


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


# `\e` is ESC in shell and logging dialects, read like `\x1b` (batch 9, class: a spelled-out ESC the decoder did not know). It is read
# as ESC in these places only (batch 10 narrowed it to the first, batch 11 added the second as a length rule, batch 12 replaced the
# length rule by the shape of the word): (1) directly before `[`, `]`, `(` or `)` (the characters that start the sequences this
# reader knows), anywhere; (2) GLUED inside a word: a character that is no space and no backslash on each side (`qZ7k\eM3vR`,
# `Ab3+\edE6/`), except inside a Windows path word (a drive letter, a colon and a backslash, then every character up to the next
# space: `C:\Users\err\x`, `C:\env\etc`; see `path_words`), where the spelling is a folder name and is left as written; (3) 12 or more
# token characters (letters, digits, `_`, `-`) after it, with anything or nothing in front; 6 or more on each side; next to another
# `\e` that is one token character away (`q\eZ\e7`). A `\e` that is read adds one reading, never removes one.
_T = "[A-Za-z0-9_-]"
ESC_E = (
    rf"e(?:(?=[\[\]()])|(?=(?:{_T}){{12}})|(?<=(?:{_T}){{6}}\\e)(?=(?:{_T}){{6}})"
    rf"|(?<=[^\s\\]\\e)(?=[^\s\\])(?![^\s\\]{{0,12}}\\)"
    rf"|(?<=\\e{_T}\\e)|(?={_T}\\e))"
)
_DRIVE_PATH = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:\\\S*")
_HEX_ESCAPE = re.compile(
    rf"\\(?:x([0-9a-fA-F]{{2}})|U([0-9a-fA-F]{{8}})|([0-3][0-7]{{2}})|({ESC_E}))"
)
_PCT_U = re.compile(r"%u([0-9a-fA-F]{4})")
_BRACE_U = re.compile(r"\\u\{([0-9a-fA-F]{1,6})\}")


def _one_escape(m: re.Match[str]) -> str:
    if m.group(1):
        return chr(int(m.group(1), 16))
    if m.group(2):
        cp = int(m.group(2), 16)
        return chr(cp) if cp <= 0x10FFFF else m.group(0)
    if m.group(4):
        return "\x1b"
    return chr(int(m.group(3), 8))


def path_words(text: str) -> list[tuple[int, int]]:
    """The (start, end) of each Windows path word in `text`: a drive letter, a colon, a backslash and every character up to the next
    white space. A spelling of backslash-e that is neither before a bracket nor 12 or more token characters before the end of such
    a word is a folder name there (`C:\\Users\\err\\x`), not ESC (batch 12, issue 2)."""
    return [m.span() for m in _DRIVE_PATH.finditer(text)] if ":" + chr(92) in text else []


def without_path_names(text: str) -> str:
    """`text` with the spellings of backslash-e that are folder names (see `path_words`) taken out, for the check "does this text
    hold a spelled-out hidden item" (`tools._HIDDENISH`): a path word is not skipped as a whole (a `\\x1b` or a `%1b` in it still counts)."""
    spans = path_words(text)
    if not spans:
        return text
    out, last = [], 0
    for s, e in spans:
        out.append(text[last:s])
        out.append(re.sub(r"\\e(?![\[\]()])", "", text[s:e]))
        last = e
    out.append(text[last:])
    return "".join(out)


def hex_unescape(text: str) -> str:
    """Backslash escapes a log pipeline or a language writes for one character: backslash-x and two hex digits,
    backslash-U and eight hex digits, a three-digit octal escape (backslash and 000 to 377), and backslash-e. NOT decoded: a one- or
    two-digit octal escape and named escapes (`\\1` and Windows paths would decode wrongly)."""
    if "%u" in text:
        text = _PCT_U.sub(lambda m: chr(int(m.group(1), 16)), text)
    if chr(92) in text:
        text = _BRACE_U.sub(
            lambda m: chr(int(m.group(1), 16)) if int(m.group(1), 16) <= 0x10FFFF else m.group(0),
            text,
        )
        spans = path_words(text)
        starts = [s for s, _ in spans]

        def one(m: re.Match[str]) -> str:
            if m.group(4) and starts and text[m.end() : m.end() + 1] not in ("[", "]", "(", ")"):
                i = bisect.bisect_right(starts, m.start()) - 1
                if i >= 0 and m.start() < spans[i][1]:
                    return m.group(0)  # a folder name in a Windows path word
            return _one_escape(m)

        text = _HEX_ESCAPE.sub(one, text)
    return text


_CONTROL_REF = re.compile(r"&#(?:[xX]0*([0-9a-fA-F]{1,2})|0*([0-9]{1,3}))(;|(?=[\[(\]]))")


def _control_ref(m: re.Match[str]) -> str:
    n = int(m.group(1), 16) if m.group(1) else int(m.group(2))
    if m.group(3) != ";" and n != 0x1B:  # unterminated: only an ESC that starts a sequence is read
        return m.group(0)
    c = chr(n) if 0 < n < 0x80 else ""
    return c if c in hidden.REMOVED_CHARS or c in hidden.SPACE_LIKE else m.group(0)


def control_refs(text: str) -> str:
    """Every numeric reference to a control character below U+0080 (`&#27;`, `&#x1b;`, leading zeros allowed) written as that
    character, and every UNTERMINATED reference to ESC (`&#27`, `&#x1B`, no semicolon) that stands directly before `[`, `(`
    or `]` (the start of a colour code, a `tput sgr0` sequence or a title string; `html.unescape` reads an unterminated
    reference too). `html.unescape` deletes such a reference, and a deleted escape character leaves the rest of its sequence
    (`(B`, `[m`) in the text as plain letters, so the hidden-item reader could no longer take the sequence out (and an entity
    it stood inside, `&#6` + `&#27;[0m` + `5;`, was already decoded wrongly). Any other unterminated reference is left to the
    decoder."""
    return _CONTROL_REF.sub(_control_ref, text) if "&#" in text else text


def html_unescape(text: str) -> str:
    """`html.unescape`, except that a terminated reference to a control character is kept as that character (`control_refs`)."""
    return html.unescape(control_refs(text))


def undo(
    text: str,
    clean: bool = False,
    strip_hidden: bool = False,
    consume: bool = False,
    escapes: list[bool] | None = None,
    characters: bool = False,
    keep: bool = False,
) -> str:
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
    only that removal would create is written in its escaped look-alike form (`_no_created_shapes`). With `consume` as
    well, the removal reads every escape sequence with its final byte, a letter or digit too (`hidden.strip_consuming`,
    the consuming reading: `%4` + `ESC ( B` + `1KIA...` needs it). With `characters`, the removal deletes every hidden character on
    its own and reads no sequence (`hidden.strip_characters`, the character reading): the letter after a decoded ESC stays
    (`%1b%54r0ub...` is `Tr0ub...`, not `r0ub...`). With `keep`, an ESC that opens no sequence takes nothing after it
    (`hidden.strip_keeping`: `ESC K` + `I...` keeps the `K`). The default keeps every existing caller unchanged."""
    cur = text
    strip_fn = (
        (lambda t: (hidden.strip_characters(t), ""))
        if characters
        else hidden.strip_consuming
        if consume
        else hidden.strip_keeping
        if keep
        else hidden.strip
    )
    for _ in range(defaults.SCRUB_MAX_LAYERS + 1):
        step = cur
        for decode in (nfkc, json_unescape, hex_unescape, unquote, html_unescape):
            if clean:
                while (
                    cut := partial_escape_start(
                        step, max(len(step) - 4 * defaults.SCRUB_PARTIAL_END, 0)
                    )
                ) is not None:
                    step = step[
                        :cut
                    ]  # repeat: the look-back may start inside a run of half escapes
            if strip_hidden and decode is html_unescape:
                # the references to control characters first, then the hidden items out, then the rest of the references:
                # an entity that a hidden item cuts (`&#6` + `&#27;[0m` + `5;`) is whole when the item is gone
                step = control_refs(step)
                if escapes is not None and "\x1b" in step:
                    escapes.append(
                        True
                    )  # an escape character stood here: the consuming reading may differ
                step = _no_created_shapes(step, strip_fn(step)[0])
            step = decode(step)
        if strip_hidden:
            if escapes is not None and "\x1b" in step:
                escapes.append(
                    True
                )  # an escape character stood here: the consuming reading may differ
            step = _no_created_shapes(step, strip_fn(step)[0])
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


def redact_untrusted(text: str, mapping: dict[str, str], refuse_remnants: bool = True) -> str:
    """`redact_text` for text from outside (the document, a tool result, an error message): markers and
    placeholder-shaped literals are escaped in the text AND in every decoded view the second pass may return
    (see `redact_text`). Model-written text (tool arguments, proposal inputs) uses `redact_text` as it is: a
    placeholder the model writes is meant to be one."""
    return redact_text(
        text, mapping, neutralise=neutralise_untrusted, refuse_remnants=refuse_remnants
    )


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
    return _decode_views(text)[0]


def _decode_views(text: str) -> tuple[list[str], str]:
    """(views, plain decode). Other forms a secret can hide in: the canonical view (NFKC, ignorable characters removed) and the same
    with JSON `\\uXXXX` escapes decoded. Only forms that differ from `text` are returned."""
    # `\\/` too (PHP writes every slash that way); `\\n` and the like are left alone here: a log line full of them
    # would come back with real newlines whenever the second pass finds anything.
    unescaped = fits_after_nfkc(json_unescape(text, simple="/"))
    out = []
    # the layers undone to a fixed point (percent, entity, backslash, NFKC, any order, up to the depth cap; deeper
    # raises TooDeep and nothing is redacted or shown): `%41KIA...`, `&#65;KIA...`, `password%3Dx`
    decoded = fits_after_nfkc(undo(text))
    views = [canonical(text), canonical(unescaped), decoded]
    # The decode with the hidden items removed at the end of every round (`decodes`: `%4` + a colour code + `1KIA...`) is
    # read by `redact_text` as the consuming pair, judged by `_consuming_wins`; it is not a view of its own.
    for view in views:
        view = _clean(view)
        if view != text and view not in out:
            out.append(view)
    return out, decoded


def decodes(text: str, characters: bool = False, keeping: bool = False) -> tuple[str, ...]:
    """The layers of `text` undone with the hidden items removed at the end of every round, in each reading that can differ:
    the grammar's (`undo(strip_hidden=True)`) and, only when an escape character stood in the text or a decoder wrote one
    (`%1B`, `\\u001b`, `&#27;`), the consuming reading (`undo(strip_hidden=True, consume=True)`: `ESC ( B` takes its letter).
    The one place that says which decodes a searcher must look in (the redactor's views and the scrub of tool results).
    With `characters` the character reading (`undo(strip_hidden=True, characters=True)`) is added when it differs, LAST:
    a decoded escape character takes the letter after it in the grammar's reading (`%1b%54r0ub...` reads `r0ub...`), and
    the character reading keeps it. The scrub of handed-out secrets asks for it; `_consuming_view` takes the last
    reading and does not."""
    seen: list[bool] = []
    plain = undo(text, strip_hidden=True, escapes=seen)
    if not seen:
        return (plain,)
    out = [plain]
    consuming = undo(text, strip_hidden=True, consume=True)
    if consuming != plain:
        out.append(consuming)
    if keeping:  # an ESC that opens no sequence takes nothing after it (`ESC K` keeps the `K`)
        kept = undo(text, strip_hidden=True, keep=True)
        if kept not in out:
            out.append(kept)
    if characters:
        chars = undo(text, strip_hidden=True, characters=True)
        if chars not in out:
            out.append(chars)
    return tuple(out)


def _consuming_view(text: str) -> str:
    """The last decode of `text` (`decodes`: the consuming reading when it differs), the way `_views` cleans a view: `%4` +
    `ESC ( B` + `1KIA...`; `%1B%28B`, which a decoder turns into `ESC ( B`, cut by a colour code."""
    return _clean(fits_after_nfkc(decodes(text)[-1]))


_PIECE = 5
_MAX_SWALLOWED = defaults.MAX_SWALLOWED_CHARS


def _swallowed_pieces(chars: str, joined: str) -> set[str] | None:
    """The `_PIECE`-character pieces of the text the grammar's reading removed beyond the control characters themselves
    (the body of a string sequence, the parameters of a control sequence): `joined` is `chars` with some runs left out,
    so one pass with two positions finds the runs. None when more than `_MAX_SWALLOWED` characters were left out (the
    character reading is then not used: a hostile text must not make this check long)."""
    runs: list[str] = []
    i = j = start = 0
    n, m = len(chars), len(joined)
    swallowed = 0
    while i < n:
        if j < m and chars[i] == joined[j]:
            if start < i:
                runs.append(chars[start:i])
            i += 1
            j += 1
            start = i
        else:
            swallowed += 1
            i += 1
            if swallowed > _MAX_SWALLOWED:
                return None
    if start < n:
        runs.append(chars[start:])
    return {r[k : k + _PIECE] for r in runs for k in range(len(r) - _PIECE + 1)}


def _has_novel_value(new_map: dict[str, str], known: dict[str, str]) -> bool:
    """Does a reading hold a value that is not a piece of a value of a SECRET kind the run already holds? A value that is only a
    piece of a held identifier (an ARN, a host) is not "already found": the cut copy of it stays readable if the reading is
    dropped (batch 12, issue 3: the same containment shape as `_only_inside_held`, which batch 11 fixed at one site only; class: a
    piece of a held identifier called already found, at every site that asks "is this value new")."""
    holders = [
        v for ph, v in known.items() if not v.startswith("\0seed") and kind_of(ph) in SECRET_KINDS
    ]
    return any(not any(v in k for k in holders) for ph, v in new_map.items() if ph not in known)


def _char_reading_wins(
    shown: str,
    new_map: dict[str, str],
    known: dict[str, str],
    before: dict[str, str],
    pieces: set[str] | None,
    out: str = "",
) -> bool:
    """May the character reading's output replace the output of the grammar's reading (`out`)? Only when
    1. no piece of `_PIECE` or more characters of a value already held stands in it, and it shows no piece of the text the
       grammar's reading removed (`pieces`; the character reading must hide more, never show more, than the grammar's
       reading); and
    2. EITHER it holds a value that is not a piece of one already held, and the grammar's reading found NO new value of a
       secret kind in this text (an address or a name it found is no reason: it shares the text with a cut key; a value an
       escape sequence cut is what this reading exists for; a garbled reading, `password=h` + `]0;t` + `unter2...`, finds a
       short wrong value and shows the rest);
       OR it masks MORE copies than the grammar's reading (`_held`): the same value, one copy the grammar's reading could not
       read because an escape character took its first letter (`AK` + `ESC I` + `AIOS...` next to a plain key). Condition 1
       holds for it as for the first."""
    if pieces is None:
        return False
    values = [v for v in known.values() if not v.startswith("\0seed")]
    if any(v[i : i + _PIECE] in shown for v in values for i in range(len(v) - _PIECE + 1)) or any(
        shown[i : i + _PIECE] in pieces for i in range(len(shown) - _PIECE + 1)
    ):
        return False
    novel = _has_novel_value(new_map, known)
    new_secret = any(
        ph not in before and (kind_of(ph) not in STORED_KINDS or kind_of(ph) == "SECRET")
        for ph in known
    )
    if novel and not new_secret:
        return True
    return _held(shown) > _held(out) and set(new_map.values()) >= set(known.values())


def _consuming_wins(shown: str, new_map: dict[str, str], known: dict[str, str]) -> bool:
    """May the output of a CONSUMING reading (`hidden.strip_consuming`) replace the output so far? Its own rule, not the
    character reading's: that reading can SHOW text the grammar's reading removed, so it needs the swallowed-piece check
    (`_char_reading_wins`); the consuming reading only deletes one more byte per escape sequence, it never shows more.
    1. It must hold a value that is not a piece of one already held (the cut key the other readings could not join); if it
       does not, the output stays as it is.
    2. When it does, no piece of `_PIECE` or more characters of a value already held may stand in it. If one does, the
       reading lost a letter that the value began with (`ESC e` + `yJ...`): replacing the output would show that value and
       keeping it would show the cut key, and the two readings cannot be merged, so the text is refused (`InputTooLarge`,
       nothing shown) rather than left.
    Every value an earlier reading found is carried into this reading (`work` of the caller), so a second masked value,
    text before or after the key and a tail of any length do not reject it."""
    values = [v for v in known.values() if not v.startswith("\0seed")]
    novel = _has_novel_value(new_map, known)
    if not novel:
        return False
    # No `compare_readings` call here (batch 8, issue 2): `new_map` is built from the map the earlier readings made and nothing
    # removes an entry, so it always holds every value of `known` and the call could only answer "same" or "second"
    # (7413 calls over 6,000+ texts: 6307 "same", 1106 "second", 0 "conflict"; `handover/evidence/PRH/b8/consuming_conflict_dead.py`).
    # The real refusal is the window check below.
    if any(v[i : i + _PIECE] in shown for v in values for i in range(len(v) - _PIECE + 1)):
        raise RedactionLimit("InputTooLarge")
    return True


REMNANT_WINDOW = 8  # characters of a masked secret that may not stand in the result of a text that held hidden items


def _refuse_remnant(out: str, current: dict[str, str]) -> None:
    """A text that held hidden items is read in several readings that cannot be merged (a copy found whole in one reading
    may stand cut in the output of another: `AK` + `ESC I` + `AIOS...` next to a plain key, where the grammar's reading
    took the `I`). When a stretch of `REMNANT_WINDOW` characters of a value this run masked (a secret kind: its placeholder
    is never restored) still stands in the result, the text is refused (`RedactionLimit`, nothing shown) and the tool paths
    show the withheld note. Linear in the output for each masked value (class: a cut copy left readable beside a masked
    one, PR H batch 7, issue 4)."""
    w = REMNANT_WINDOW
    for ph, value in current.items():
        if value.startswith("\0seed") or len(value) < w or kind_of(ph) in STORED_KINDS:
            continue
        if any(value[i : i + w] in out for i in range(len(value) - w + 1)):
            raise RedactionLimit("InputTooLarge")


def _held(text: str) -> int:
    return len(PLACEHOLDER.findall(text))


_GAPS = re.compile(rf"[\s{hidden.IGNORABLE_RE.pattern[1:-1]}]")


_HOLDER_CHECK_EVERY = (
    4096  # hits between two looks at the clock while the copies of a value are counted
)


def _only_inside_held(
    value: str,
    current: dict[str, str],
    readings: tuple[str, ...],
    work: _Work | None = None,
) -> bool:
    """Is EVERY copy of `value` in the readings of a view part of a value of a SECRET kind that the run already holds (`current`:
    a secret that is only a piece of a held identifier is not "already found", batch 10 group 5; batch 11, group 2:
    the batch 10 test was `value in held value`, which says "already found" for a shorter secret whose only copy this view
    found, because a longer held value happens to contain it)? Copies are counted in the reading with the gaps taken out (a copy
    written with spaces is a copy), overlapping ones too; a copy is covered when it lies inside one occurrence of a held value
    that contains `value`. Only a held value of `defaults.SPACED_VALUE_MIN_CHARS` or more characters can cover a copy: the spaced
    sweep masks no spaced copy of a shorter one, so a gap-stripped match of it proves nothing (batch 12, issue 7). A reading with no copy of `value` at all
    (it was found in a spelling no gap rule can see) is not proved covered: False, so the view is not dropped.
    Work (batch 12, issue 7): each reading is searched once per held value that contains `value`, plus once for `value`; every hit is
    one interval comparison (no slice is filled), and with `work` the clock is looked at every `_HOLDER_CHECK_EVERY` hits, so a
    262,144-character text with a PEM-size held value cannot keep the call busy past `defaults.REDACT_BUDGET_S`."""
    holders = [
        k
        for ph, k in current.items()
        if value in k
        and len(k) >= defaults.SPACED_VALUE_MIN_CHARS
        and not k.startswith("\0seed")
        and kind_of(ph) in SECRET_KINDS
    ]
    if not holders:
        return False
    saw_a_copy = False
    hits = 0

    def occurrences(text: str, needle: str) -> list[int]:
        nonlocal hits
        out, i = [], text.find(needle)
        while i >= 0:
            out.append(i)
            hits += 1
            if work is not None and hits % _HOLDER_CHECK_EVERY == 0:
                work.check()
            i = text.find(needle, i + 1)
        return out

    for reading in readings:
        compact = _GAPS.sub("", reading)
        merged: list[
            list[int]
        ] = []  # the stretches the occurrences of the holders cover, sorted and joined where they touch
        for lo, hi in sorted((i, i + len(k)) for k in holders for i in occurrences(compact, k)):
            if merged and lo <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], hi)
            else:
                merged.append([lo, hi])
        starts = [m[0] for m in merged]
        for i in occurrences(compact, value):
            saw_a_copy = True
            j = bisect.bisect_right(starts, i) - 1
            if j < 0 or i + len(value) > merged[j][1]:
                return False
    return saw_a_copy


_VALUE_END = frozenset(" \t\n;&,\"'")
_ENCODED_MARKS = ("%", chr(92), "&")


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
            raise RedactionLimit("InputTooLarge")
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


class _Work:
    """What one `redact_text` call has used: the time since it started and the number of passes (one pass = all patterns of
    `redact` over one reading). Both are bounded, and a call that passes a bound is refused (`InputTooLarge`, nothing shown):
    a hostile text must not keep the process busy. `defaults.REDACT_BUDGET_S` is checked before every pass, so one call
    overruns it by at most one pass; `defaults.MAX_REDACT_PASSES` is counted in `count_pass`, which every pass goes through."""

    __slots__ = ("passes", "spaced_chars", "started")

    def __init__(self) -> None:
        self.started = time.monotonic()
        self.passes = 0
        self.spaced_chars = (
            0  # characters the reads of spaced-out runs will scan, over every view of the call
        )

    def charge_spaced(self, chars: int) -> None:
        """Count the characters of one read of a spaced-out run BEFORE it runs (`redact.spaced_unknown`): over
        `defaults.SPACED_READ_MAX_CHARS` for the whole call, or past the time budget, the call is refused (batch 11, group 5)."""
        self.spaced_chars += chars
        if self.spaced_chars > defaults.SPACED_READ_MAX_CHARS:
            raise SpacedRunLimit
        self.check()

    def check(self) -> None:
        if time.monotonic() - self.started > defaults.REDACT_BUDGET_S:
            raise RedactionLimit("InputTooLarge")

    def count_pass(self) -> None:
        self.passes += 1
        if self.passes > defaults.MAX_REDACT_PASSES:
            raise RedactionLimit("InputTooLarge")


def _check_budget(work: _Work) -> None:
    work.check()


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


def _held_placeholders(found_text: str, joined: str, mapping: dict[str, str]) -> list[str]:
    """The placeholders this find pass put into `found_text` (one that stands in the text as written does not count)."""
    out: list[str] = []
    for ph in dict.fromkeys(m.group(0) for m in PLACEHOLDER.finditer(found_text)):
        if ph in mapping and found_text.count(ph) > joined.count(ph):
            out.append(ph)
    return out


def _redact_stripped(
    joined: str, spaced: str, mapping: dict[str, str], cache: dict | None, work: _Work
) -> tuple[str, dict[str, str]]:
    """Redact one text that holds no hidden item, given as its two readings (`hidden.strip`): values are FOUND in the
    joined reading and MASKED in the spaced reading, which is what the reader is given. Returns (text, map).

    1. Both readings equal: one pass over `spaced`.
    2. Otherwise a find pass over `joined`; the placeholders that stand in its result are the "held" values.
    3. "Needed" = the held values with a copy in `joined` that does not occur as written in `spaced` (a copy that does is masked
       by the sweep of known values in step 6) and that are not seed entries.
    4. More than `MAX_DECODED_MASKS` needed values: `InputTooLarge`, nothing shown.
    5. Each needed value is looked for in `spaced` by its gap pattern (`redact.gap_pattern`); every match is a span and the one
       span rule (`redact.mask_spans`) puts the placeholders in.
    6. The mask pass over that text with the map of the find pass. If a held value is then missing (not standing, and
       not inside a placeholder that took its place) the text is refused (`RedactionError`), never the joined result:
       the joined reading has lost the boundaries that main's behaviour relies on."""
    if joined == spaced:
        work.count_pass()
        result = redact(spaced, mapping=mapping, _cache=cache, _readings=False)
        return result.text, result.mapping
    work.count_pass()
    found = redact(joined, mapping=mapping, _cache=cache, _readings=False)
    held = _held_placeholders(found.text, joined, found.mapping)
    needed = [
        ph
        for ph in held
        if not found.mapping[ph].startswith("\0seed")
        and (
            found.mapping[ph] not in spaced
            # a value that stands whole in one place and cut in another (`AK` + `ESC I` + `AIOS...` next to a plain copy): the
            # sweep of step 6 masks the whole copy only, so the cut one is needed too (counted per copy, not per value)
            or spaced.count(found.mapping[ph]) < joined.count(found.mapping[ph])
        )
    ]
    if len(needed) > MAX_DECODED_MASKS:
        raise RedactionLimit("InputTooLarge")
    spans: list[tuple[int, int, str]] = []
    for ph in needed:
        spans.extend(
            (m.start(), m.end(), ph) for m in gap_pattern(found.mapping[ph]).finditer(spaced)
        )
    merged = dict(found.mapping)
    masked = mask_spans(spaced, spans, merged) if spans else spaced
    work.check()
    work.count_pass()
    result = redact(masked, mapping=merged, _cache=cache, _readings=False)
    standing = {m.group(0) for m in PLACEHOLDER.finditer(result.text)}
    for ph in held:
        value = found.mapping[ph]
        if ph not in standing and not any(value in result.mapping.get(q, "") for q in standing):
            raise RedactionError("held value lost")
    return result.text, result.mapping


def redact_text(
    text: str,
    mapping: dict[str, str],
    neutralise: Callable[[str], str] | None = None,
    refuse_remnants: bool = True,
) -> str:
    """Redact `text` with the run's map, continuing it in place. Any failure is a RedactionError. With `refuse_remnants`
    False the check of `_refuse_remnant` is skipped: only the scrub of tool results asks for that, to learn which values the
    redactor finds in a text (`tools._found_values`) and mask them itself.

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

    Passes (one pass = all patterns of `redact` over one reading): the text 1 pass, or 2 when a run of hidden items stands
    between two word characters (found in the joined reading, masked in the spaced one); every other reading the same
    (the decoded readings, the character reading, the consuming reading in which an escape sequence takes its final letter,
    each also for every decoded reading that holds a hidden item). The number is COUNTED: a call that would make more than
    `defaults.MAX_REDACT_PASSES` (24; a one-time search found 17, the seeded search stays at 14 and the regression rows of the tests at 7) is refused (`InputTooLarge`, nothing shown),
    and the 6-second budget is checked before every pass.

    The one choke point for input size. The cap is on the WORK, not only on the input: the text, the text after
    `neutralise`, and every view the second pass will scan must each be within `defaults.MAX_REDACT_CHARS`, else
    `InputTooLarge` (a RedactionError) is raised and nothing is redacted. NFKC expands some characters (U+FDFA
    becomes 18), so 87,000 of them are under the input cap and a 1.5-million-character view (24 s measured).
    That covers every caller that goes through `redact_text` / `redact_untrusted` / `redact_value` (document, tool
    result, model-written argument, eval case, card text, log and tick lines through `safe_head`, the judge and the
    vendor guardrail input); the registry (`guard/producers.py`) lists them. No bare `redact()` call remains outside
    this module: the second pass of `approvals/channel.py` `clean` is this function too."""
    _within_cap(text)
    work_done = _Work()
    try:
        cache = getattr(mapping, "redact_cache", None)
        text = fits_after_nfkc(_repair(text))
        rd = hidden.readings(
            text
        )  # every reading of the text, from the one helper the scrub of tool results uses too
        joined, spaced = rd.joined, rd.spaced
        if joined is not text:
            same = spaced is joined
            joined = _no_created_shapes(text, joined)
            spaced = joined if same else _no_created_shapes(text, spaced)

        def esc(t: str) -> str:
            return fits_after_nfkc(neutralise(t)) if neutralise is not None else t

        e_text = esc(text)  # the escaped ORIGINAL: the decoded readings are built from it
        e_joined = e_text if joined is text else esc(joined)
        e_spaced = e_joined if spaced is joined else esc(spaced)
        _check_budget(work_done)
        out, current = _redact_stripped(e_joined, e_spaced, mapping, cache, work_done)
        # The decoded readings are built from the text with its hidden items already taken out (joined reading), never
        # from the original: a decoder reads across a run of hidden items, so the backslash that ends a string
        # terminator (ESC then backslash) followed by `n` became a newline, or by digits an octal escape, and cut the value.
        base = e_text if joined is text else e_joined
        scan = not base.isascii() or any(c in base for c in "\\%&")
        decoded_views, decoded = _decode_views(base) if scan else ([], base)
        views = [v for v in decoded_views if v not in (e_joined, e_spaced)]
        # What the caller's own cleaning leaves of a reading (the approval card deletes control characters before any
        # value is looked for, which main relied on) is a reading too, when it is not the one already read. They go
        # last, so every other reading keeps its masks; the cleaning must not create a shape either.
        cleaned: list[str] = []
        if joined is not text and hidden.strip(e_text)[0] not in (e_joined, e_spaced):
            cleaned.append(_no_created_shapes(text, e_text))
            # and the readings of that reading (its percent, entity and NFKC forms): `%4` + a form feed + `1KIA...`
            if not e_text.isascii() or any(c in e_text for c in "\\%&"):
                cleaned += [
                    _no_created_shapes(e_text, v)
                    for v in _views(e_text)
                    if v not in (e_joined, e_spaced) and v not in views
                ]
        # The character reading (`Readings.characters`: every control character deleted on its own, no sequence read) is
        # what main saw: a value that an escape sequence cut in the grammar's reading (a string that swallows the rest of
        # its line, an ESC that takes the letter after it) is found there. It is used only under the rule of
        # `_char_reading_wins`. PR H: no step back from main.
        char_views: dict[str, tuple[str, str]] = {}
        char_pairs: dict[str, tuple[str, str]] = {}
        mixed_keys: set[str] = (
            set()
        )  # soft views (the mixed reading, the collapsed spaced run): used only when they leave no remnant
        # The consuming reading (`Readings.consuming_joined` and `consuming_spaced`: an escape sequence takes its final byte,
        # a letter too) finds a value that `ESC ( B` (what `tput sgr0` writes) cut: the conservative reading keeps that
        # final byte (D-029). Each is a PAIR (found in the joined, masked in the spaced reading, as for the text itself)
        # under the rule of `_consuming_wins`, not the character reading's. Same helper for the text and for every decoded
        # reading that holds a hidden item.
        consuming: dict[str, tuple[str, str]] = {}

        def ignoring(t: str) -> str:
            # a cut reading is searched with the ignorable characters out, as the text itself is (its `canonical` view): a key
            # an ESC cut AND a zero-width joiner cut is whole only then (class: several cuts in one value, PR H batch 8)
            return hidden.IGNORABLE_RE.sub("", t)

        def mixed_reading(source: str, r: hidden.Readings) -> tuple[str, str] | tuple[None, None]:
            # the mixed reading (a lone ESC keeps its byte, a charset sequence goes whole) only when it is a NEW text: when it
            # equals a reading that has its own rule (the consuming one, the grammar's), that rule judges it
            if "\x1b" in source:
                m = hidden.strip_mixed(source)
                if m[0] not in (r.joined, r.characters, r.consuming_joined, r.keeping_joined):
                    return m
            return (None, None)

        def add_readings(source: str, r: hidden.Readings, found_in: str) -> None:
            found_in = ignoring(found_in)
            for chars, spaced_chars, is_mixed in (
                (r.characters, r.characters_spaced, False),
                (r.keeping_joined, r.keeping_spaced, False),
                (*mixed_reading(source, r), True),
            ):
                if chars is None:
                    continue
                # the character reading (every control character deleted on its own) and the keeping reading (an ESC that opens
                # no sequence takes nothing after it): pairs judged by the character reading's rule. The output is the SPACED
                # reading (`user` + BEL + an address stays two words), the values are found in the joined one (batch 6, H3)
                if (c := ignoring(esc(chars))) in (e_joined, e_spaced) or c in cleaned + views:
                    continue
                key = _no_created_shapes(source, c)
                if key in char_views:
                    continue
                char_views[key] = (c, found_in)
                if is_mixed:
                    mixed_keys.add(key)
                cs = ignoring(esc(spaced_chars))
                char_pairs[key] = (key, key if cs == c else _no_created_shapes(source, cs))
                cleaned.append(key)
            if r.consuming_joined is r.joined and r.consuming_spaced is r.spaced:
                return  # no sequence takes a letter here: the grammar's reading is the consuming one
            cj, cs = esc(r.consuming_joined), esc(r.consuming_spaced)
            if cj in (e_joined, e_spaced) and cs in (e_joined, e_spaced):
                return
            key = _no_created_shapes(source, cj)
            if key in char_views or key in consuming or key in cleaned:
                return
            consuming[key] = (key, key if cs == cj else _no_created_shapes(source, cs))
            cleaned.append(key)

        if joined is not text:
            add_readings(text, rd, e_joined)
        # the same for every decoded reading that holds a hidden item (`%C2%90` decodes to a string opener)
        for v in views:
            if hidden.ANY.search(v):
                r = hidden.readings(v)
                add_readings(v, r, esc(r.joined))
        # and the decode that removes the hidden items in the consuming reading at every round (`%4` + `ESC ( B` + `1KIA`;
        # `%1B%28B`): built from the text's consuming reading when the text holds an escape item, from the text itself when
        # only the decode exposes one
        if scan:
            csrc = base if joined is text else esc(_no_created_shapes(text, rd.consuming_joined))
            if csrc != base or hidden.ANY.search(decoded):
                cv = _consuming_view(csrc)
                if cv not in (e_joined, e_spaced, csrc) and cv not in views + cleaned:
                    consuming[cv] = (cv, cv)
                    cleaned.append(cv)
            # and the same with an ESC that opens no sequence taking nothing after it (`ESC K` + `I...` next to `&#x1b;[0m`)
            ksrc = base if joined is text else esc(_no_created_shapes(text, rd.keeping_joined))
            if ksrc != base or hidden.ANY.search(decoded):
                kv = _clean(fits_after_nfkc(undo(ksrc, strip_hidden=True, keep=True)))
                if kv not in (e_joined, e_spaced, csrc) and kv not in views + cleaned:
                    consuming[kv] = (kv, kv)
                    cleaned.append(kv)
        if neutralise is not None:
            for v in views:
                if (
                    hidden.ANY.search(v)
                    and (c := esc(v)) != v
                    and hidden.strip(c)[0] not in hidden.strip(v)
                ):
                    cleaned.append(_no_created_shapes(v, c))
        # an UNKNOWN secret written with a space between its characters (`A K I A ...`): the text with the spaces of such a run
        # taken out is one more view (the check is `redact.spaced_unknown`, its reads counted in the call's own work count: a run of ten or more single-character tokens that
        # the patterns read as a secret once collapsed; its measured rate on ordinary text is in SECURITY.md,
        # `defaults.READ_SPACED_OUT_UNKNOWN`). Batch 10, group 5: also in each DECODED view, so a gap spelled `%20` or `&#32;` is a
        # gap too (`A%20K%20I%20A...`); the work budget of `spaced_unknown` counts each view's runs on their own
        for source in dict.fromkeys(
            [e_spaced, *(v for v in views if v not in (e_joined, e_spaced))]
        ):
            try:
                runs = (
                    spaced_unknown(source, work_done.charge_spaced)
                    if defaults.READ_SPACED_OUT_UNKNOWN
                    and len(source) >= 2 * defaults.SPACED_RUN_MIN_TOKENS - 1
                    else []
                )
            except SpacedRunLimit:
                # too many runs of spaced-out characters to read each one: nothing is shown, never a skip (cost bound)
                raise RedactionLimit("InputTooLarge") from None
            if runs:
                collapsed = collapse_runs(source, runs)
                if collapsed not in (e_joined, e_spaced) and collapsed not in cleaned + views:
                    cleaned.append(collapsed)
                    mixed_keys.add(
                        collapsed
                    )  # a soft view: no refusal of its own (see `mixed_keys`)
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
            _check_budget(work_done)  # a hostile text: fail closed, nothing shown
            if view in consuming:
                vj, vs = consuming[view]
            elif view in char_pairs:
                vj, vs = char_pairs[view]
            else:
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
            again, again_map = _redact_stripped(vj, vs, work, cache, work_done)
            # a new value, or a known one only the view spells in a way pass one could not read
            if view in consuming:
                wins = _consuming_wins(again, again_map, current)
            elif view in char_views:
                wins = _char_reading_wins(
                    again, again_map, current, mapping, _swallowed_pieces(*char_views[view]), out
                )
            else:
                wins = again_map != current or _held(again) > _held(out)
            if wins and view in mixed_keys:
                # the mixed reading is one more way to read a cut value; it may add a mask but never causes a refusal the
                # other readings would not (a tail it cannot join stays for them to judge)
                try:
                    _refuse_remnant(again, again_map)
                except InputTooLarge:
                    # a view that found NO value the readings before it did not hold may be dropped (they judge the remnant); a
                    # view that alone found a value must not be dropped: the value would stay readable, so the text is refused
                    # (class: a find dropped silently, PR H batch 9, group 9)
                    # only a held value of a SECRET kind can hold the new value (a secret that is a piece of a held identifier is
                    # not "already found"; batch 10, group 5)
                    if any(
                        not _only_inside_held(v, current, (vj, vs), work)
                        for v in again_map.values()
                        if v not in current.values() and not v.startswith("\0seed")
                    ):
                        raise
                    wins = False
            if wins:
                out, current = again, again_map
                # the values this reading found are carried into the readings still to come, so a later reading that
                # finds less does not replace the output with one that has lost them
                base_texts += (vj, vs)
                pairs = make_pairs(current, base_texts)
        out = _clean(out)
        if joined is not text and refuse_remnants:
            _refuse_remnant(out, current)
        if neutralise is neutralise_untrusted:
            _refuse_forgery(out, current)
    except RedactionError:  # InputTooLarge, RedactionLimit, TooDeep and the plain refusals keep their own type and message
        raise
    except Exception as exc:  # noqa: BLE001 - whatever the redactor raised, nothing is sent
        raise RedactorCrash(type(exc).__name__) from None
    mapping.clear()
    mapping.update(current)
    return out


SAFE_HEAD_NOTE = WITHHELD_NOTE


def safe_head(text: str, limit: int, mapping: dict[str, str] | None = None) -> str:
    """Redact FIRST, then keep the first `limit` characters: the order every short model-bound or logged message
    (an exception text, a validation error, a card line) needs, because a cut first splits a secret and the
    redactor no longer sees a whole one. The text is redacted up to the redactor's cap (`redact_bounded`: past the
    cap it is cut for bounded work and the end of the result is dropped), then the head is kept.
    Raises only `RedactorCrash` (the redactor itself failed: a bug stops the run, it is never turned into a note); a
    text the redactor refuses (too large after NFKC, nested too deep, a work limit, a plain refusal) becomes a fixed note."""
    try:
        return redact_bounded(text, {} if mapping is None else mapping)[0][:limit]
    except RedactorCrash:
        raise  # one rule at every catcher: a crash of the redactor stops the run (batch 11, group 4)
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
