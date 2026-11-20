"""The one canonical form of a secret name (re-exported by backends.platform_secrets). Kept in a module that holds
no secret so ``config`` can use it without reaching a secret holder (tests/test_repo_rules.py)."""

from __future__ import annotations

import re
from collections.abc import Iterable

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def canonical_secret_name(name: str) -> str:
    """The one form in which secret names are compared: lower case, every run of characters outside [a-z0-9]
    becomes one "_", no leading or trailing "_". Deliberately stricter than any single provider: the env kind
    folds "db-pass", "DB_PASS" and "db.pass" onto one variable, the mounted_file kind resolves "x", "./x" and
    "a/../x" to one file, so any two names a provider could fold together must collide here."""
    return _NON_ALNUM.sub("_", name.lower()).strip("_")


def collides(ref: str, names: Iterable[str]) -> bool:
    """True when ``ref`` is, in canonical form, one of ``names``. The one comparison every "this login must not be
    a secret the runtime reads" check uses."""
    canon = canonical_secret_name(ref)
    return any(canonical_secret_name(n) == canon for n in names)
