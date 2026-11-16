"""The one place the demo asks the core redactor what it recognises (seam over the byte copy ``core_copy/redact.py``).

It is a seam, not logic: it runs the copied ``redact`` and returns each recognised original with its core kind. The core placeholders are
discarded (``mask.py`` issues its own marks). When core is a declared dependency, change the one import below and delete ``core_copy/redact.py``
(CORE_COPIES.md). Nothing here catches or formats an exception: the caller decides.
"""

from __future__ import annotations

from intake.core_copy.redact import kind_of as _kind_of
from intake.core_copy.redact import redact as _redact


def find(text: str) -> list[tuple[str, str]]:
    """``(core kind, original text)`` for every value the core redactor replaced, in first-seen order."""
    return [(_kind_of(placeholder), original) for placeholder, original in _redact(text).mapping.items()]
