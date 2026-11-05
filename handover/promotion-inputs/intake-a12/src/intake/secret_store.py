"""Reads the owner's key file. The ONLY reader of that file in product code (``tools/make_secrets.py`` uses ``present_names`` and ``secrets_path``).

Named ``secret_store`` (not ``secrets``) so the standard-library module is not shadowed; run as ``python -m intake`` or the entry point.

``get(name)`` reads the key file ``HADAVIN_LOCAL/secrets/secrets.env`` ONLY: there is no environment lookup for a secret name (a stray environment
variable cannot replace the passphrase, the webhook token or the key; tests write a temporary key file instead).

Least privilege inside the module: the file is read as a STREAM, line by line, and only the wanted name's value is kept in memory; every other line is
checked for shape and dropped. Parse rules, fail closed: UTF-8, a leading BOM stripped, CRLF or LF; blank lines and ``#`` lines ignored;
``NAME=value`` with no spaces around ``=``; ANY malformed line refuses every name. Errors carry a code and the secret's NAME, never a value."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from .codes import SecretError

# provider registry for the model key: a second provider adds one line here (and to NAMES); the shape rule applies to every registered name
MODEL_KEYS = {"anthropic": "ANTHROPIC_API_KEY"}
API_KEY = MODEL_KEYS["anthropic"]
MODEL_KEY_NAMES = frozenset(MODEL_KEYS.values())
WEBHOOK_SECRET = "HADAVIN_WEBHOOK_SECRET"
APPROVER_PASSPHRASE = "HADAVIN_APPROVER_PASSPHRASE"
N8N_ENCRYPTION_KEY = "N8N_ENCRYPTION_KEY"
N8N_PASSWORD = "N8N_BASIC_AUTH_PASSWORD"
# name -> minimum length (the API key has its own shape below)
MIN_LENGTH = {WEBHOOK_SECRET: 32, APPROVER_PASSPHRASE: 24, N8N_ENCRYPTION_KEY: 32, N8N_PASSWORD: 24}
NAMES = (API_KEY, WEBHOOK_SECRET, APPROVER_PASSPHRASE, N8N_ENCRYPTION_KEY, N8N_PASSWORD)
API_KEY_RE = re.compile(r"[A-Za-z0-9_-]{20,300}")
_API_KEY_MIN = 20
MAX_FILE_BYTES = 64 * 1024
_LINE_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=(.*)")


def secrets_path(local: str | os.PathLike | None = None) -> Path:
    base = local if local is not None else os.environ.get("HADAVIN_LOCAL", "")
    if not str(base).strip():
        raise SecretError("key_file_missing", "HADAVIN_LOCAL is not set")
    if not Path(base).is_absolute():
        raise SecretError("key_file_missing", "HADAVIN_LOCAL must be an absolute path")
    return Path(base) / "secrets" / "secrets.env"


def _read(path: Path, wanted: frozenset[str] | None) -> dict[str, list[str]]:
    """Stream the key file. Returns ``{NAME: values}`` for every name seen; the VALUES are kept only for names in ``wanted`` (``None`` = keep all, an
    empty set = names only). Raises ``SecretError``: ``key_file_missing``, ``key_encoding``, or ``key_malformed`` with the line number."""
    try:
        size = path.stat().st_size
        f = path.open("rb")
    except OSError:
        raise SecretError("key_file_missing", "secrets file not found") from None
    if size > MAX_FILE_BYTES:  # checked BEFORE any line is read: a huge line is never loaded
        f.close()
        raise SecretError("key_malformed", "secrets file is larger than 64 KB")
    out: dict[str, list[str]] = {}
    with f:
        for lineno, raw in enumerate(f, 1):
            try:
                line = raw.decode("utf-8")
            except UnicodeDecodeError:
                raise SecretError("key_encoding", "secrets file is not UTF-8") from None
            if lineno == 1 and line.startswith(chr(0xFEFF)):
                line = line[1:]
            line = line.rstrip("\n")
            if line.endswith("\r"):
                line = line[:-1]
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            m = _LINE_RE.fullmatch(line)
            if not m:
                raise SecretError("key_malformed", f"secrets file line {lineno} is not NAME=value", line=lineno)
            values = out.setdefault(m.group(1), [])
            if wanted is None or m.group(1) in wanted:
                values.append(m.group(2))
    return out


def parse(path: Path) -> dict[str, list[str]]:
    """Every name with every value (kept for tests and tools that need the whole file; product code uses ``get``)."""
    return _read(path, None)


def check_value(name: str, value: str) -> None:
    """Shape and length rules for one value. Raises ``SecretError`` (never echoes the value)."""
    if value == "":
        raise SecretError("key_empty", f"{name} is empty")
    if value[0] in "\"'" or re.search(r"[\s\x00-\x1f\x7f]", value):
        raise SecretError("key_malformed", f"{name} starts with a quote or contains whitespace or a control character")
    if name in MODEL_KEY_NAMES:
        if len(value) < _API_KEY_MIN:
            raise SecretError("key_short", f"{name} is too short")
        if not API_KEY_RE.fullmatch(value):
            raise SecretError("key_malformed", f"{name} has an unexpected shape")
    elif len(value) < MIN_LENGTH[name]:
        raise SecretError("key_short", f"{name} is too short")


def get(name: str, *, local: str | os.PathLike | None = None) -> str:
    """The value of ``name`` from the key file (never from the environment). Raises ``SecretError`` with a code."""
    if name not in NAMES:
        raise SecretError("key_name_missing", f"{name} is not a known secret name")
    values = _read(secrets_path(local), frozenset({name})).get(name)
    if not values:
        raise SecretError("key_name_missing", f"{name} is not in the secrets file")
    if len(values) > 1:
        raise SecretError("key_duplicate", f"{name} appears more than once")
    check_value(name, values[0])
    return values[0]


def status(name: str, local: str | os.PathLike | None = None) -> str:
    """``ok`` or the failure code; used by ``intake check``. Reads the file only. Never returns or prints a value."""
    try:
        get(name, local=local)
    except SecretError as e:
        return e.code
    return "ok"


def parse_problem(local: str | os.PathLike | None = None) -> SecretError | None:
    """A whole-file parse failure that has a line number (code and line only), or None."""
    try:
        _read(secrets_path(local), frozenset())  # names only: no value is kept
    except SecretError as e:
        return e if e.line is not None else None
    return None


PASSPHRASE_COPY = "approver-passphrase.txt"


def _stat_mode(path: Path) -> int:
    return path.stat().st_mode


LOCK_FILE = "secrets.env.lock"
_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = (
    _ROOT if (_ROOT / "pyproject.toml").is_file() else None
)  # None for an installed wheel (no checkout): then nothing is "inside the repo"


def mode_problems(local: str | os.PathLike | None = None) -> list[str]:
    """Names (the folder as ``(folder)``, the key file, the passphrase copy) whose mode has group or other bits. POSIX only: on Windows the mode
    bits mean nothing (see ``mode_state``) and protection comes from the inherited ACL of the user's profile folder."""
    if sys.platform == "win32":
        return []
    base = secrets_path(local).parent
    named = (("(folder)", base), ("secrets.env", base / "secrets.env"), (PASSPHRASE_COPY, base / PASSPHRASE_COPY))
    return [n for n, p in named if p.exists() and _stat_mode(p) & 0o077]


def mode_state(local: str | os.PathLike | None = None) -> str:
    """The text of the ``secrets_mode`` line: ``ok``, ``fail key_mode <names>`` or, on Windows where nothing is checked, ``not_checked (windows)``."""
    if sys.platform == "win32":
        return "not_checked (windows)"
    bad = mode_problems(local)
    return "ok" if not bad else "fail key_mode " + " ".join(bad)


def lock_state(local: str | os.PathLike | None = None) -> str:
    return "present" if (secrets_path(local).parent / LOCK_FILE).exists() else "absent"


def inside_repo(local: str | os.PathLike | None = None) -> bool:
    """True when the key folder resolves to a place inside this repository checkout (the key file must live outside it)."""
    if REPO_ROOT is None:
        return False
    try:
        secrets_path(local).resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return False
    return True


def secrets_location(local: str | os.PathLike | None = None) -> str:
    """``under_user_profile`` or ``elsewhere`` (a warning for the second, not a failure)."""
    try:
        secrets_path(local).resolve().relative_to(Path.home().resolve())
    except (ValueError, OSError, RuntimeError):
        return "elsewhere"
    return "under_user_profile"


def present_names(path: Path) -> set[str]:
    """Names already in the file (for ``tools/make_secrets.py``): NAMES ONLY, no value is kept. Raises like ``parse``; an absent file is the empty set."""
    if not path.exists():
        return set()
    return set(_read(path, frozenset()))
