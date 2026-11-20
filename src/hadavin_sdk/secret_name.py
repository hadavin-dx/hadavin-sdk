"""The one canonical form of a secret name (re-exported by backends.platform_secrets). Kept in a module that holds
no secret so ``config`` can use it without reaching a secret holder (tests/test_repo_rules.py)."""

from __future__ import annotations

import re
import unicodedata
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


_SEPARATORS = re.compile(r"[/\\]")


def has_dot_segment(name: str) -> bool:
    """A "." or ".." segment, split on "/" and on the Windows separator "\\" (over-refusing on Linux, where "\\"
    is an ordinary character, is harmless: a secret name never needs one)."""
    return any(part in (".", "..") for part in _SEPARATORS.split(name))


def is_path_shaped(name: str) -> bool:
    """A name with a "." or ".." segment or a leading or trailing "/" (or "\\"): a mounted_file provider resolves
    it to another file ("a/../x" is "x"), which no fold of the text can predict. Only the dot-segment half is a
    problem for every provider; a leading or trailing "/" is a plain name to aws or vault ("/hadavin/prod/dsn"),
    so callers ask ``path_form_problem`` with the provider kind."""
    return has_dot_segment(name) or name.startswith(("/", "\\")) or name.endswith(("/", "\\"))


def path_form_problem(name: str, file_backed: bool) -> bool:
    """True when ``name`` cannot be compared by its text: a dot segment (any provider's rules may differ, so it is
    always refused) or, for a file-backed provider only, a leading or trailing separator."""
    return is_path_shaped(name) if file_backed else has_dot_segment(name)


def forms(name: str, file_backed: bool = False) -> set[str]:
    """The canonical form of ``name`` and, for a file-backed provider, also its NFKC plus case-folded form: a
    normalising or case-folding file system (macOS APFS and HFS+, Windows NTFS) maps the Kelvin sign to "K" and the
    long s to "s", so the file of ``\u212alack`` is the file of ``Klack``. Not testable on Linux (byte-exact, case
    sensitive); the macOS and Windows behaviour is stated, not run."""
    out = {canonical_secret_name(name)}
    if file_backed:
        out.add(canonical_secret_name(unicodedata.normalize("NFKC", name).casefold()))
    return out


def collides(ref: str, names: Iterable[str], *, file_backed: bool = False) -> bool:
    """True when ``ref`` is, in canonical form, one of ``names``. The one comparison every "this login must not be
    a secret the runtime reads" check uses. With nothing to compare against it is False. A file-backed provider
    also fails closed on a path-shaped name (it may be any file in the folder) and compares the file-system folds."""
    names = list(names)
    if not names:
        return False
    if file_backed and (is_path_shaped(ref) or any(is_path_shaped(n) for n in names)):
        return True
    mine = forms(ref, file_backed)
    return any(mine & forms(n, file_backed) for n in names)
