"""The one place the demo asks for the look-alike text fold (confusables, invisible characters, width, case-insensitive digits).

It is a seam, not logic: today it delegates to `intake.core_copy.textnorm`, a byte copy of core PR #50 `hadavin_sdk/guard/textnorm.py`
(see CORE_COPIES.md / core_copies.json). When PR #50 is merged and the demo pin moves, change the one import below to
`hadavin_sdk.guard.textnorm` and delete `core_copy/`. The API shape (`fold(raw, *, casefold=False, collapse_ws=False)`) is the core one.
A fold makes look-alike text EQUAL: use it for DENY decisions and scans (egress, blocklists), never to decide that an address is the verified one.
"""

from __future__ import annotations

from intake.core_copy.textnorm import fold as _core_fold


def fold_text(raw: str, *, casefold: bool = False, collapse_ws: bool = False) -> str:
    return _core_fold(raw, casefold=casefold, collapse_ws=collapse_ws)
