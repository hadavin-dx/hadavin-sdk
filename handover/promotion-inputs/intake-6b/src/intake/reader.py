"""Reader (spec 6.1). ``normalise_for_model`` is the ONE function that makes ``send_text``; ``read`` decides the reader flag (None, X18 or X28);
``gate_decision`` is the data-gate decision for one parsed file (used by the scan, and by ``demo_ctl register`` through ``send_text_hash``).

A flagged file never reaches the model, costs nothing and bypasses the gate: it becomes a reject-only item."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass

from .checks import POLICY, fold, normalise_document

MAX_SEND_CHARS = POLICY["max_document_chars"]  # the one source of the size cap (also rules.document_too_large)
DELIMITERS = ("<<<INVOICE_START>>>", "<<<INVOICE_END>>>")
SUFFIX = ".txt"
X18, X28 = "X18", "X28"
_SQUASH = re.compile(r"[\s_.-]+")


@dataclass(frozen=True)
class ParsedDoc:
    text: str  # send_text; "" for an X18 item; the full normalised text for an X28 item
    source_sha256: str  # sha256 of the RAW bytes
    name: str
    flag: str | None  # None, "X18" or "X28"


def normalise_for_model(raw_bytes: bytes) -> str:
    """The ONE function that produces ``send_text``: decode UTF-8 (strict: bad bytes raise ``UnicodeDecodeError``, the caller flags X18), NFC,
    CRLF to LF, then ``checks.normalise_document`` (leading BOMs stripped, lone CR to LF). The gate hash and the request use this same string."""
    text = unicodedata.normalize("NFC", raw_bytes.decode("utf-8"))
    return normalise_document(text.replace("\r\n", "\n"))


def stem(name: str) -> str:
    """The name without its final suffix (the stem of the item id)."""
    dot = name.rfind(".")
    return name[:dot] if dot > 0 else name


def send_text_hash(text: str) -> str:
    """The data-gate hash: sha256 of the UTF-8 bytes of ``send_text``, lowercase hex."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read(name: str, data: bytes) -> ParsedDoc:
    """Decide the flag. X18: a suffix other than ``.txt`` (case-insensitive), a NUL byte, bytes that are not UTF-8, an empty or whitespace-only file,
    or a delimiter of the prompt inside the normalised text (also in a folded form: case, width, entities, invisible characters); ``text`` is then empty. X28: the normalised text is over 20000 characters
    (X18 wins when both apply: the delimiter check comes first). ``normalise_for_model`` runs only on bytes that decode."""
    sha = hashlib.sha256(data).hexdigest()

    def unreadable() -> ParsedDoc:
        return ParsedDoc("", sha, name, X18)

    if not name.lower().endswith(SUFFIX) or b"\x00" in data:
        return unreadable()
    try:
        text = normalise_for_model(data)
    except UnicodeDecodeError:
        return unreadable()
    folded = fold(text)  # case, width, entities and invisible characters cannot hide a delimiter
    if not folded.strip():  # empty, whitespace-only or zero-width-only
        return unreadable()
    squashed = _SQUASH.sub("", folded)  # spaces, underscores, hyphens and dots inside a delimiter cannot hide it either
    if any(_SQUASH.sub("", fold(d)) in squashed for d in DELIMITERS):
        return unreadable()
    if len(text) > MAX_SEND_CHARS:
        return ParsedDoc(text, sha, name, X28)
    return ParsedDoc(text, sha, name, None)


def gate_decision(doc: ParsedDoc, listed: frozenset[str]) -> str | None:
    """The scan's gate decision (spec 5.4 and 11 step 7): ``None`` = go on (a flagged file bypasses the gate; a clean file whose ``send_text`` hash is on
    the made-up list), ``"not_on_list"`` = refuse, store no item. An empty list refuses every clean file (the STOP state)."""
    if doc.flag is not None:
        return None
    return None if send_text_hash(doc.text) in listed else "not_on_list"
