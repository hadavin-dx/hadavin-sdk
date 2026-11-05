"""One safe way to put an exception into a log line or a stored error field.

Exception text can carry the very values the redactor exists to hide (a detector that chokes on a document
repeats pieces of it). `safe_text`, `safe_message` and `safe_str` therefore:

* show the text of an exception ONLY if its class belongs to ``hadavin_sdk`` (or to a module the caller names in
  ``also_trust``) and every other class in its MRO is a built-in base. Everything else, including every plain
  built-in (``KeyError(field)``, ``ValueError("could not convert string to float: '...'")``,
  ``UnicodeEncodeError``, ``ImportError``), every OSError, and any class with a driver or user ancestor,
  shows its class name only: their text routinely quotes the document or a host. `locator` gives a safe
  ``file:line`` for those so a failure stays diagnosable without any document content;
* read at most 64*limit characters; remove every terminal escape sequence (7-bit and 8-bit forms, with their
  parameters), lone ESC, control characters and invisible characters BEFORE any pattern runs; fold look-alikes
  (NFKC); drop combining marks; squeeze whitespace (single newlines stay, multi-line secrets need them); cap
  the input BEFORE NFKC and again after it;
* mask first and cut second, so a value that straddles the cut is not half shown. When something was cut
  before masking, the text is backed off to the last word boundary before any open quote, ``=`` or trailing
  digit run, and ``[truncated]`` is added;
* mask e-mail addresses with its own Unicode-aware pattern (the redactor's address pattern is ASCII-only),
  then run the redactor;
* mask several forms of the same text and take the UNION of what they found: an invisible character may be a
  separator (a key after it needs a space) or a splitter (a value split by it needs removal), and which one it
  is differs by position. Forms: all removed, all spaced, and for each of the first 8 invisible runs "only this
  one spaced" and "only this one removed". Every original any form masked is then replaced in the text, so no
  vote between forms exists and nothing the text itself says (a literal ``<EMAIL_1>``) can steer the result;
* fail closed and never raise on exception-derived data: a failing check withholds, a failing mask gives a
  fixed note.

What this does NOT promise (stated so nobody over-trusts it): only patterns the redactor and the e-mail mask
recognise are masked. A name in free prose, a spaced IBAN, a lowercase IBAN, dotted card or Aadhaar numbers,
US phone numbers written with brackets or dots, and lowercase-hex presigned-URL signatures are not
recognised (strict xfail tests mark each; when the redactor learns one, that test XPASSes, the run fails and
the test must become a normal test; review again 2027-01-31, nothing enforces the date). A value split by
invisible characters at MORE than one position, beyond the 8 tracked runs, is masked only in the all-removed
and all-spaced forms. ``str(exc)`` itself is computed in full before it is cut (Python offers no bounded
``str``). The allowlist trusts the declared ``__module__``. The redactor's address pattern gap is recorded for
the pattern ticket (BL-core-c1a-001); this module does not edit ``guard/redact.py``.
"""

from __future__ import annotations

import os
import re
import unicodedata

from hadavin_sdk.guard.redact import redact

# The text of an exception is shown only if its class lives in one of these (built-in ANCESTORS are fine).
_TRUSTED_MODULES = frozenset({"hadavin_sdk"})
_RAW_FACTOR = 64  # at most limit * 64 characters of str(exc) are read
_PRECAP_FACTOR = 8  # redact sees at most limit * 8 characters
_TRACKED_RUNS = 8  # invisible runs that get their own "only this one" forms
UNAVAILABLE = "(message unavailable)"
WITHHELD = "(withheld)"
TRUNCATED = " [truncated]"
_SENT = chr(0xE000)  # marks an invisible run until the forms decide between removal and a space
_KEEP_CONTROL = "\t\n\r\x0b\x0c"
_FILLERS = frozenset(map(chr, (0x034F, 0x115F, 0x1160, 0x3164, 0xFFA0, 0x2800)))
# Complete terminal sequences (OSC, DCS/SOS/PM/APC, CSI), then a lone ESC. A CSI's final byte may be a real
# letter of the text that follows (ESC[31AKIA...), so there are two readings: FULL eats the final byte
# (colour codes), NOFINAL leaves it. The text is masked in both and the NOFINAL text is the one shown.
_ANSI_COMMON = [
    r"(?:\x1b\]|\x9d)[^\x07\x1b\x9c]*(?:\x07|\x1b\\|\x9c|\Z)",
    r"(?:\x1bP|\x1bX|\x1b\^|\x1b_|\x90|\x98|\x9e|\x9f)[^\x1b\x9c]*(?:\x1b\\|\x9c|\Z)",
]
_ANSI_FULL = re.compile("|".join([*_ANSI_COMMON, r"(?:\x1b\[|\x9b)[0-?]*[ -/]*[@-~]"]))
_ANSI_NOFINAL = re.compile("|".join([*_ANSI_COMMON, r"(?:\x1b\[|\x9b)[0-?]*[ -/]*"]))
_DOTS = "." + chr(0x3002) + chr(0xFF61)
_LOCAL = r"(?:\"[^\"\n]{1,64}\"|[\w.+'&-]+)"
# A domain: dotted names need a letter in the last label (numpy@1.26.4 is a version, not a mailbox); a single
# label (bob@corp) and a bracketed address (bob@[10.0.0.1]) are masked too (fail closed).
_DOMAIN = r"(?:\[[0-9A-Fa-f:.]+\]|[^\W\d_][\w-]*(?:[" + _DOTS + r"][\w-]+)*)"
_EMAIL = re.compile(r"(?<![\w.+'&-])" + _LOCAL + "@" + _DOMAIN)
_SPACES = re.compile(r"[ \t\f\v\r]+")
_NEWLINES = re.compile(r" ?\n[ \n]*")
_AT_FORMS = ("&#64;", "&#x40;", "&commat;", "%2540", "%40", "\\" + "u0040")


def _invisible(c: str, marks: bool = False) -> bool:
    """Characters that can split a value without changing how it looks. `marks` also covers combining marks."""
    cat = unicodedata.category(c)
    if cat == "Cc":
        return c not in _KEEP_CONTROL
    if cat in {"Cf", "Co", "Cn", "Cs", "Zl", "Zp"} or c in _FILLERS or c == chr(0x1680):
        return True
    return marks and cat in {"Mn", "Me"}


def _mark_runs(s: str, ansi: re.Pattern[str]) -> str:
    """Complete escape sequences and invisible characters become one _SENT per run."""
    s = ansi.sub(_SENT, s)
    out: list[str] = []
    prev = False
    for c in s:
        if c == _SENT or _invisible(c):
            if not prev:
                out.append(_SENT)
            prev = True
        else:
            out.append(c)
            prev = False
    return "".join(out)


def _squeeze(s: str) -> str:
    return _NEWLINES.sub("\n", _SPACES.sub(" ", s)).strip()


def _form(marked: str, spaced: set[int] | None, everything: bool, invert: bool) -> str:
    """Replace each _SENT run by a space or nothing: `everything` spaces all, else only those in `spaced`
    (or all but those, when `invert`)."""
    out: list[str] = []
    for i, part in enumerate(marked.split(_SENT)):
        if i:
            space = everything or ((i - 1 in (spaced or ())) != invert)
            out.append(" " if space else "")
        out.append(part)
    return "".join(out)


def _decode_at(s: str) -> str:
    for form in _AT_FORMS:
        s = s.replace(form, "@")
    return s


def _last_ws(s: str, end: int | None = None) -> int:
    end = len(s) if end is None else end
    return max(s.rfind(" ", 0, end), s.rfind("\n", 0, end))


def _back_off(s: str) -> str:
    """Drop the trailing word, then anything that could be the start of a value cut in half."""
    cut = _last_ws(s)
    s = s[:cut] if cut >= 0 else ""
    for q in ('"', "'"):  # an open quote: back off to the whitespace before it
        if s.count(q) % 2 == 1:
            cut = _last_ws(s, s.rfind(q))
            s = s[:cut] if cut >= 0 else ""
    i = s.rfind("=")  # key=value near the end
    if i >= max(0, len(s) - 200):
        cut = _last_ws(s, i)
        s = s[:cut] if cut >= 0 else ""
    words = s.split(" ")  # a trailing run of digit groups (card, Aadhaar, phone)
    while words and words[-1].isdigit():
        words.pop()
    return " ".join(words)


def _prepare(form: str, cap: int, truncated: bool, repl: str) -> tuple[str, bool]:
    """Squeeze, cap BEFORE NFKC, fold, drop marks, squeeze, cap again, back off if anything was cut."""
    text = _squeeze(form)
    if len(text) > cap:
        text, truncated = text[:cap], True
    text = unicodedata.normalize("NFKC", text)
    text = "".join(
        " "
        if unicodedata.category(c) in {"Zs", "Zl", "Zp"}
        else (repl if _invisible(c, True) else c)
        for c in text
    )
    text = _squeeze(_decode_at(text))
    if len(text) > cap:
        text, truncated = text[:cap], True
    return (_back_off(text) if truncated else text), truncated


def _next_email(mapping: dict[str, str]) -> int:
    nums = [int(k[7:-1]) for k in mapping if k.startswith("<EMAIL_") and k[7:-1].isdigit()]
    return max(nums, default=0) + 1


def _mask_form(text: str, mapping: dict[str, str]) -> dict[str, str]:
    """Mask e-mail addresses (own pattern) and then run the redactor; returns the grown placeholder map."""
    reverse = {v: k for k, v in mapping.items()}

    def mark(m: re.Match[str]) -> str:
        orig = m.group(0)
        if orig not in reverse:
            ph = f"<EMAIL_{_next_email(mapping)}>"
            mapping[ph] = orig
            reverse[orig] = ph
        return reverse[orig]

    return redact(_EMAIL.sub(mark, text), mapping=mapping).mapping


def safe_str(raw: str, limit: int = 300) -> str:
    """Mask and bound a plain string the same way as exception text. UNAVAILABLE if masking failed."""
    if limit <= 0:
        raise ValueError("limit must be positive")
    try:
        cut = raw[: limit * _RAW_FACTOR]
        cap = limit * _PRECAP_FACTOR
        was_cut = len(raw) > len(cut)
        readings = [_ANSI_NOFINAL] + ([_ANSI_FULL] if _ANSI_FULL.search(cut) else [])
        forms: dict[str, str] = {}
        base, truncated = "", False
        for n, ansi in enumerate(readings):
            marked = _mark_runs(cut, ansi)
            plan = [(None, False, False, ""), (None, True, False, " ")]  # all removed, all spaced
            for i in range(min(marked.count(_SENT), _TRACKED_RUNS)):
                plan += [
                    ({i}, False, False, ""),
                    ({i}, False, True, ""),
                ]  # only i spaced, only i removed
            for k, (spaced, everything, invert, repl) in enumerate(plan):
                text, cut_here = _prepare(
                    _form(marked, spaced, everything, invert), cap, was_cut, repl
                )
                forms.setdefault(text, "")
                if n == 0 and k == 0:
                    base, truncated = text, cut_here
        mapping: dict[str, str] = {}
        for text in forms:
            mapping = _mask_form(text, mapping)
        out = base
        for ph, orig in sorted(mapping.items(), key=lambda kv: -len(kv[1])):
            if orig and orig in out:
                out = out.replace(orig, ph)
        flat = " ".join(out.split())
        flat = flat + TRUNCATED if truncated else flat
        if len(flat) <= limit:
            return flat
        if truncated and limit > 2 * len(TRUNCATED):  # keep the marker, make room for it
            return flat[: limit - len(TRUNCATED)].rstrip() + TRUNCATED
        return flat[:limit]
    except Exception:  # noqa: BLE001 - fail closed on anything, RecursionError included
        return UNAVAILABLE


def _trusted(exc: BaseException, also_trust: frozenset[str]) -> bool:
    if isinstance(exc, OSError):  # sockets, files, DNS: hosts and paths
        return False
    allowed = _TRUSTED_MODULES | also_trust
    for i, cls in enumerate(type(exc).__mro__):
        if cls is object:
            continue
        root = cls.__module__.split(".")[0]  # a non-str __module__ raises: the caller withholds
        if root in allowed or (root == "builtins" and i > 0):  # a built-in INSTANCE is withheld
            continue
        return False
    return True


def class_name(exc: BaseException) -> str:
    """The class name made safe to put in a log field: printable, no whitespace, at most 64 characters."""
    try:
        raw = str(type(exc).__name__)
    except Exception:  # noqa: BLE001 - a hostile metaclass must not break the handler
        raw = ""
    return "".join(c for c in raw if c.isprintable() and not c.isspace())[:64] or "Exception"


_name = class_name


def locator(exc: BaseException) -> str:
    """``file.py:123`` of the innermost frame the exception passed through, or "" (no document content)."""
    try:
        tb = exc.__traceback__
        if tb is None:
            return ""
        while tb.tb_next is not None:
            tb = tb.tb_next
        where = f"{os.path.basename(tb.tb_frame.f_code.co_filename)}:{tb.tb_lineno}"
        return "".join(c for c in where if c.isprintable() and not c.isspace())[:80]
    except Exception:  # noqa: BLE001 - never raise while describing an error
        return ""


def safe_text(
    exc: BaseException, limit: int = 300, also_trust: frozenset[str] = frozenset()
) -> str:
    """The masked, one-line text of `exc`, at most `limit` characters.

    WITHHELD if the class may not show its text, UNAVAILABLE if reading or masking failed, "" if no text."""
    if limit <= 0:
        raise ValueError("limit must be positive")
    try:
        trusted = _trusted(exc, also_trust)
    except Exception:  # noqa: BLE001 - a hostile __module__ or metaclass: withhold
        return WITHHELD
    if not trusted:
        return WITHHELD
    try:
        raw = str(exc)
    except Exception:  # noqa: BLE001 - a broken __str__ must not break the handler that logs it
        return UNAVAILABLE
    return safe_str(raw, limit)


def with_class(exc: BaseException, text: str) -> str:
    """`ClassName: text`; the class name alone if the text is empty or withheld."""
    name = class_name(exc)
    return f"{name}: {text}" if text and text != WITHHELD else name


def safe_message(
    exc: BaseException, limit: int = 300, also_trust: frozenset[str] = frozenset()
) -> str:
    """`ClassName: text` (masked, one line); `ClassName` alone if the text is withheld or empty."""
    return with_class(exc, safe_text(exc, limit, also_trust))
