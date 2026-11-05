"""One safe way to put an exception into a log line or a stored error field.

Exception text can carry the very values the redactor exists to hide (a detector that chokes on a document
repeats pieces of it). `safe_text`, `safe_message` and `safe_str` therefore:

* show the text of an exception ONLY if its class belongs to ``hadavin_sdk`` (or to a module the caller names in
  ``also_trust``) and every other class in its MRO is a built-in base. Everything else, including every plain
  built-in (``KeyError(field)``, ``ValueError("could not convert string to float: '...'")``,
  ``UnicodeEncodeError``, ``ImportError``), every OSError, and any class with a driver or user ancestor,
  shows its class name only: their text routinely quotes the document or a host;
* read at most 64*limit characters, replace invisible characters, fold look-alikes (NFKC), drop combining
  marks, squeeze whitespace (but keep single newlines so multi-line secrets still match) and cap the input;
* mask first and cut second, so a value that straddles the cut is not half shown. When something was cut
  before masking, the text is backed off to the last word boundary before any open quote, ``=`` or trailing
  digit run, and ``[truncated]`` is added;
* mask e-mail addresses with its own Unicode-aware pattern (the redactor's address pattern is ASCII-only),
  then run the redactor. Invisible characters are removed in one candidate and replaced by a space in the
  other (a key after an escape sequence needs the space; a value split by a zero-width character needs the
  removal); the candidate with more masks wins;
* fail closed and never raise on exception-derived data: a failing check withholds, a failing mask gives a
  fixed note.

What this does NOT promise (stated so nobody over-trusts it): only patterns the redactor and the e-mail mask
recognise are masked. A name in free prose, a spaced IBAN and lowercase-hex presigned-URL signatures are not
recognised (strict xfail tests mark each; when the redactor learns one, that test XPASSes, the run fails and
the test must become a normal test; review again 2027-01-31, nothing enforces the date). A text that has BOTH
a key after an escape sequence and a value split by a zero-width character gets only one of the two forms
masked. The allowlist trusts the declared ``__module__``. The redactor's own address pattern gap is recorded
for the pattern ticket (BL-core-c1a-001); this module does not edit ``guard/redact.py``.
"""

from __future__ import annotations

import re
import unicodedata

from hadavin_sdk.guard.redact import redact

# The text of an exception is shown only if its class lives in one of these (built-in ANCESTORS are fine).
_TRUSTED_MODULES = frozenset({"hadavin_sdk"})
_RAW_FACTOR = 64  # at most limit * 64 characters of str(exc) are read
_PRECAP_FACTOR = 8  # redact sees at most limit * 8 characters
UNAVAILABLE = "(message unavailable)"
WITHHELD = "(withheld)"
TRUNCATED = " [truncated]"
_ESC = chr(0x1B)
_KEEP_CONTROL = (
    "\t\n\r\x0b\x0c" + _ESC
)  # ESC is left to the redactor's ANSI handling, removed afterwards
_FILLERS = frozenset(map(chr, (0x034F, 0x115F, 0x1160, 0x3164, 0xFFA0, 0x2800)))
# A Unicode-aware address: word characters (any script) in the local part and the domain.
_EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_MARK = re.compile(r"<[A-Z_]+_\d+>")
_SPACES = re.compile(r"[ \t\f\v\r]+")
_NEWLINES = re.compile(r" ?\n[ \n]*")


def _invisible(c: str, marks: bool = False) -> bool:
    """Characters that can split a value without changing how it looks. `marks` also covers combining marks."""
    cat = unicodedata.category(c)
    if cat == "Cc":
        return c not in _KEEP_CONTROL
    if cat in {"Cf", "Co", "Cn", "Cs"} or c in _FILLERS:
        return True
    return marks and cat in {"Mn", "Me"}


def _fold(s: str, repl: str) -> str:
    s = "".join(repl if _invisible(c) else c for c in s)
    s = unicodedata.normalize("NFKC", s)
    return "".join(repl if _invisible(c, True) else c for c in s)


def _squeeze(s: str) -> str:
    return _NEWLINES.sub("\n", _SPACES.sub(" ", s)).strip()


def _mask_emails(s: str) -> str:
    n = 0

    def mark(_m: re.Match[str]) -> str:
        nonlocal n
        n += 1
        return f"<EMAIL_{n}>"

    return _EMAIL.sub(mark, s)


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


def _candidate(text: str, cap: int, truncated: bool) -> str:
    if len(text) > cap:
        text, truncated = text[:cap], True
    if truncated:
        text = _back_off(text)
    masked = redact(_mask_emails(text)).text.replace(_ESC, "")
    return masked + TRUNCATED if truncated else masked


def safe_str(raw: str, limit: int = 300) -> str:
    """Mask and bound a plain string the same way as exception text. UNAVAILABLE if masking failed."""
    if limit <= 0:
        raise ValueError("limit must be positive")
    try:
        cut = raw[: limit * _RAW_FACTOR]
        truncated = len(raw) > len(cut)
        cap = limit * _PRECAP_FACTOR
        forms = dict.fromkeys(
            _squeeze(_fold(cut, repl)) for repl in ("", " ")
        )  # one form if nothing invisible
        outs = [_candidate(text, cap, truncated) for text in forms]
        best = max(outs, key=lambda o: len(_MARK.findall(o)))  # ties keep the first (removal) form
        flat = " ".join(best.split())
        if len(flat) <= limit:
            return flat
        if best.endswith(TRUNCATED) and limit > 2 * len(
            TRUNCATED
        ):  # keep the marker, make room for it
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


def _name(exc: BaseException) -> str:
    try:
        raw = str(type(exc).__name__)
    except Exception:  # noqa: BLE001 - a hostile metaclass must not break the handler
        raw = ""
    return "".join(c for c in raw if c.isprintable() and not c.isspace())[:64] or "Exception"


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
    name = _name(exc)
    return f"{name}: {text}" if text and text != WITHHELD else name


def safe_message(
    exc: BaseException, limit: int = 300, also_trust: frozenset[str] = frozenset()
) -> str:
    """`ClassName: text` (masked, one line); `ClassName` alone if the text is withheld or empty."""
    return with_class(exc, safe_text(exc, limit, also_trust))
