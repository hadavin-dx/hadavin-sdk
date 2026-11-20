"""The one canonical form of a secret name (re-exported by backends.platform_secrets). Kept in a module that holds
no secret so ``config`` can use it without reaching a secret holder (tests/test_repo_rules.py)."""

from __future__ import annotations

import re
from collections.abc import Iterable

_NON_ALNUM = re.compile(r"[^A-Za-z0-9]+")


def canonical_secret_name(name: str) -> str:
    """The one form in which secret names are compared: every run of characters outside [A-Za-z0-9] becomes one
    "_" FIRST (so every non-ASCII character is a separator, as the env kind treats it, and a Unicode case fold such
    as the dotted capital I or the Kelvin sign cannot turn into an ASCII letter), then lower case, no leading or
    trailing "_". Deliberately stricter than any single provider: the env kind folds "db-pass", "DB_PASS" and
    "db.pass" onto one variable. The mounted_file kind also resolves dot-segments ("a/../x" is the file "x"); that
    is not folded here but refused: see ``is_path_shaped``, which ``collides`` and the sender check apply."""
    return _NON_ALNUM.sub("_", name).lower().strip("_")


def is_path_shaped(name: str) -> bool:
    """A name with a "." or ".." segment or a leading or trailing "/": a mounted_file provider resolves it to
    another file ("a/../x" is "x"), which no fold of the text can predict, so such a name is refused where names
    are compared rather than guessed at."""
    return (
        name.startswith("/")
        or name.endswith("/")
        or any(part in (".", "..") for part in name.split("/"))
    )


def collides(ref: str, names: Iterable[str]) -> bool:
    """True when ``ref`` is, in canonical form, one of ``names``. The one comparison every "this login must not be
    a secret the runtime reads" check uses."""
    names = list(names)
    if is_path_shaped(ref) or any(is_path_shaped(n) for n in names):
        return True  # fail closed: a path-shaped name may be any file in the folder
    canon = canonical_secret_name(ref)
    return any(canonical_secret_name(n) == canon for n in names)
