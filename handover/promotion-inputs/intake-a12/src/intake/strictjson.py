"""The one place the demo parses JSON that came from a file or a request (seam over the byte copy ``core_copy/strict_json.py``).

Refuses NaN, Infinity and -Infinity (also via ``1e999``) and duplicate keys (both are accepted silently by ``json.loads``), and input nested deeper
than ``MAX_DEPTH`` (also when the parser itself runs out of stack) and lone surrogates in strings and keys (they cannot be encoded as UTF-8). Every refusal is a ``ValueError``. A repo test fails on any other ``json.loads``
or ``json.load`` call in ``src/intake`` outside this module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from intake.core_copy.strict_json import loads as _core_loads

MAX_DEPTH = 64
MAX_INT_BITS = 80


def _check(obj: Any) -> None:
    """Iterative walk: depth over ``MAX_DEPTH`` or any lone surrogate in a string or a key is refused."""
    stack = [(obj, 1)]
    while stack:
        cur, d = stack.pop()
        if isinstance(cur, str):
            _no_surrogate(cur)
        elif isinstance(cur, int) and not isinstance(cur, bool):
            if cur.bit_length() > MAX_INT_BITS:  # independent of PYTHONINTMAXSTRDIGITS (which a caller can disable)
                raise ValueError("integer out of range")
        elif isinstance(cur, dict | list):
            if d > MAX_DEPTH:
                raise ValueError("JSON is nested too deeply")
            if isinstance(cur, dict):
                for k in cur:
                    _no_surrogate(k)
            stack.extend((c, d + 1) for c in (cur.values() if isinstance(cur, dict) else cur))


def _no_surrogate(s: str) -> None:
    if any(0xD800 <= ord(c) <= 0xDFFF or c == chr(0) for c in s):
        raise ValueError("lone surrogate or NUL in a JSON string")


def loads(text: str | bytes) -> Any:
    if isinstance(text, bytes | bytearray):
        text = bytes(text).decode("utf-8")
    try:
        data = _core_loads(text)
    except RecursionError:
        raise ValueError("JSON is nested too deeply") from None
    _check(data)
    return data


MAX_FILE_BYTES = 2_000_000  # config, policy and prices files are small local files; a larger one is refused before it is parsed


def load_path(path: Path | str, max_bytes: int = MAX_FILE_BYTES) -> Any:
    with Path(path).open("rb") as f:
        raw = f.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError("JSON file is too large")
    return loads(raw)
