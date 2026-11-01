"""The run's one redaction map (K5, design 6.3, M14, R2, R6).

One map per run, started at intake (empty until K4) and continued for the document and every tool result, so a
value always gets the same placeholder and a placeholder never restores to a different value. Only **identifier
kinds** are ever stored or restored; secret and regulated kinds are placeholdered for the model but their originals
live in memory for the run and nowhere else.

Pure functions over a plain ``dict[str, str]`` (placeholder -> original). Stdlib and the studio redactor only.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Callable
from typing import Any

from hadavin_sdk import defaults
from hadavin_sdk.guard.redact import ARN_TAIL, PATTERNS, SECRET_KINDS, kind_of, redact

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
    space inside a token no longer hides it)."""
    return "".join(
        c for c in unicodedata.normalize("NFKC", text) if unicodedata.category(c) != "Cf"
    )


def _canonical_view(text: str) -> tuple[str, list[int]]:
    """The canonical form of `text` (NFKC, invisible format characters removed) and, for each canonical
    character, the index of the original character it came from."""
    chars: list[str] = []
    index: list[int] = []
    for i, c in enumerate(text):
        for d in unicodedata.normalize("NFKC", c):
            if unicodedata.category(d) != "Cf":
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


_UNICODE_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})")


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


def _views(text: str) -> list[str]:
    """Other forms a secret can hide in: the canonical view (NFKC, invisible characters removed) and the same
    with JSON `\\uXXXX` escapes decoded. Only forms that differ from `text` are returned."""
    unescaped = _UNICODE_ESCAPE.sub(lambda m: chr(int(m.group(1), 16)), text)
    out = []
    for view in (canonical(text), canonical(unescaped)):
        view = _clean(view)
        if view != text and view not in out:
            out.append(view)
    return out


def _held(text: str) -> int:
    return len(PLACEHOLDER.findall(text))


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
    surrogates last, so it always encodes."""
    try:
        text = _clean(text)
        if neutralise is not None:
            text = neutralise(text)
        cache = getattr(mapping, "redact_cache", None)
        result = redact(text, mapping=mapping, _cache=cache)
        out, current = result.text, result.mapping
        if not text.isascii() or "\\u" in text:
            for view in _views(text):
                if neutralise is not None:
                    view = neutralise(view)
                again = redact(view, mapping=current, _cache=cache)
                # a new value, or a known one only the view spells in a way pass one could not read
                if again.mapping != current or _held(again.text) > _held(out):
                    out, current = again.text, again.mapping
        out = _clean(out)
    except Exception as exc:  # noqa: BLE001 - whatever the redactor raised, nothing is sent
        raise RedactionError(type(exc).__name__) from None
    mapping.clear()
    mapping.update(current)
    return out


def redact_value(value: Any, mapping: dict[str, str]) -> Any:
    """`redact_text` over every string (and dict key) inside a JSON-shaped value."""
    if isinstance(value, str):
        return redact_text(value, mapping)
    if isinstance(value, dict):
        return {
            (redact_text(k, mapping) if isinstance(k, str) else k): redact_value(v, mapping)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact_value(v, mapping) for v in value]
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
