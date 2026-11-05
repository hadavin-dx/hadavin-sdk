"""Creates the four secrets the owner does not supply (webhook token, approver passphrase, n8n encryption key, n8n owner password) in
``HADAVIN_LOCAL/secrets/secrets.env``. The API key is the owner's and is never created here.

Never prints a value (only the names it added and ``done``), never overwrites or reorders an existing line, creates the file with only the
new names if it is absent. The approver passphrase is also written ALONE into ``secrets/approver-passphrase.txt`` so the owner can open that
file without seeing the API key; ``--passphrase-file`` recreates that copy on request. An exclusive lock file ``secrets.env.lock`` (created with
O_EXCL, removed in ``finally``) guards the whole run; a lock left by a crashed run must be deleted by hand (the error says so). The folder is 0700
and the files 0600 on POSIX (an existing looser file is tightened and a note is printed); on Windows the protection is the inherited ACL of the
user's profile folder. Usage: ``python tools/make_secrets.py [--passphrase-file]``."""

from __future__ import annotations

import os
import re
import secrets
import sys
from pathlib import Path

from intake import secret_store
from intake.codes import ConfigError, Refused

PASSPHRASE_FILE = secret_store.PASSPHRASE_COPY
LOCK_NAME = secret_store.LOCK_FILE
# name -> bytes of randomness for token_urlsafe (24 bytes = 32 characters, which meets every minimum length)
CREATED = {
    secret_store.WEBHOOK_SECRET: 24,
    secret_store.APPROVER_PASSPHRASE: 24,
    secret_store.N8N_ENCRYPTION_KEY: 32,
    secret_store.N8N_PASSWORD: 24,
}
try:
    _NOFOLLOW = os.O_NOFOLLOW
except AttributeError:  # no such flag on Windows
    _NOFOLLOW = 0


def _created_length(name: str) -> int:
    """Characters in ``token_urlsafe(n)`` (base64 without padding): a created value always has exactly this length."""
    return -(-CREATED[name] * 4 // 3)


def _has_complexity(v: str) -> bool:
    return any(c.isdigit() for c in v) and any(c.isupper() for c in v) and any(c.islower() for c in v)


_PRINTABLE = re.compile(r"[A-Za-z0-9_-]+")  # generated values are printable ASCII only (no space, quote, control or non-ASCII character)


def _new_value(name: str) -> str:
    while True:
        v = secrets.token_urlsafe(CREATED[name])
        if not _PRINTABLE.fullmatch(v) or len(v) != _created_length(name):
            continue  # redraw: never write a value the parser or a shell could mangle
        if name == secret_store.N8N_PASSWORD and not _has_complexity(v):  # n8n may enforce complexity (NOT CHECKED)
            continue
        return v


def _write_private(path: Path, data: str, flags: int) -> None:
    fd = os.open(path, flags | os.O_WRONLY | _NOFOLLOW, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)


def _atomic_write(path: Path, data: bytes) -> None:
    """Write ``data`` to a temporary file next to ``path`` (exclusive create, 0600, fsync) and ``os.replace`` it over ``path``: a crash leaves the old
    file or the new file whole, never a torn one. The temporary file is removed on failure."""
    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY | _NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _write_copy(path: Path, data: str) -> None:
    """Unlink (a symlink is removed, never followed) then create exclusively: the copy never keeps an old mode, an old target or a hard link."""
    path.unlink(missing_ok=True)
    _write_private(path, data, os.O_CREAT | os.O_EXCL)


def _check_not_torn(path: Path) -> None:
    """A last line with no newline may be a torn write. Refuse to append after it when it is a known name whose value is unusable, or (for a
    value this tool creates) does not have exactly the length this tool creates."""
    raw = path.read_bytes() if path.exists() else b""
    if not raw or raw.endswith(b"\n"):
        return
    last = raw.decode("utf-8").replace("\r\n", "\n").rsplit("\n", 1)[-1]
    name, _, value = last.partition("=")
    if name not in secret_store.NAMES:
        return
    torn = False
    try:
        secret_store.check_value(name, value)
    except Refused:
        torn = True
    if name in CREATED and len(value) != _created_length(name):
        torn = True
    if torn:
        raise secret_store.SecretError(
            "key_malformed",
            "the last line of the key file has no newline and an unusable or truncated value (possibly a torn write): open the file, repair or remove that line, end it with a newline, then run again",
        )


def _tighten(path: Path) -> None:
    if sys.platform != "win32" and path.exists() and path.stat().st_mode & 0o077:
        os.chmod(path, 0o600)
        print(f"tightened the mode of {path.name} to 0600", file=sys.stderr)


def _mkdirs(d: Path) -> None:
    """Create every missing level 0700 (``Path.mkdir(parents=True, mode=...)`` applies the mode to the last level only); chmod the folder on POSIX."""
    missing = []
    cur = d
    while not cur.exists():
        missing.append(cur)
        cur = cur.parent
    for m in reversed(missing):
        m.mkdir(mode=0o700)
        if sys.platform != "win32":
            os.chmod(m, 0o700)
    if sys.platform != "win32":
        if d.stat().st_mode & 0o077:
            print("set the mode of the existing key folder to 0700", file=sys.stderr)
        os.chmod(d, 0o700)


def make_secrets(local: str | os.PathLike, passphrase_file: bool = False) -> list[str]:
    """Add the missing names under ``local``/secrets; returns the names added (never values). Names kept with an unusable value are noted on stderr."""
    path = secret_store.secrets_path(local)
    have = secret_store.present_names(path)  # raises on a corrupt or non-UTF-8 file: we never append to one
    _check_not_torn(path)
    for name in CREATED:
        if name in have and secret_store.status(name, local) != "ok":
            print(f"kept existing {name} (run intake check)", file=sys.stderr)
    _mkdirs(path.parent)
    lock = path.parent / LOCK_NAME
    try:
        os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
    except FileExistsError:
        raise ConfigError(
            "bad_config", f"lock file {LOCK_NAME} exists; if no other make_secrets run is active, delete it and run again"
        ) from None
    try:
        stale = path.with_name(path.name + ".tmp")
        if (
            stale.exists()
        ):  # only this run holds the lock: a temporary file now is the leftover of a crashed run (it holds key file content)
            stale.unlink()
            print(f"removed a stale temporary key file ({stale.name}) left by a crashed run", file=sys.stderr)
        have = secret_store.present_names(path)  # re-read and re-check under the lock
        _check_not_torn(path)
        _tighten(path)
        _tighten(path.parent / PASSPHRASE_FILE)
        if passphrase_file and secret_store.APPROVER_PASSPHRASE in have:
            secret_store.get(
                secret_store.APPROVER_PASSPHRASE, local=local
            )  # validate BEFORE any append: no partial apply on a duplicated or bad value
        added = [n for n in CREATED if n not in have]
        lines = [f"{n}={_new_value(n)}\n" for n in added]
        if lines:
            raw = path.read_bytes() if path.exists() else b""
            prefix = b"" if (not raw or raw.endswith(b"\n")) else b"\n"
            _atomic_write(
                path, raw + prefix + "".join(lines).encode("utf-8")
            )  # existing lines first and unchanged; the whole file is replaced atomically
        if secret_store.APPROVER_PASSPHRASE in added or passphrase_file:
            value = secret_store.get(secret_store.APPROVER_PASSPHRASE, local=local)
            _write_copy(path.parent / PASSPHRASE_FILE, value + "\n")
            added.append(PASSPHRASE_FILE)
    finally:
        lock.unlink(missing_ok=True)
    return added


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if any(a != "--passphrase-file" for a in argv):
        print("error: bad_config: usage: make_secrets.py [--passphrase-file]", file=sys.stderr)
        return 3
    local = os.environ.get("HADAVIN_LOCAL", "")
    if not local.strip():
        print("error: local_unset: HADAVIN_LOCAL is not set", file=sys.stderr)
        return 3
    if not Path(local).is_absolute():
        print("error: bad_config: HADAVIN_LOCAL must be an absolute path", file=sys.stderr)
        return 3
    try:
        added = make_secrets(local, "--passphrase-file" in argv)
    except Refused as e:
        print(f"refused: {e.code}: {e.text}", file=sys.stderr)
        return 2
    except ConfigError as e:
        print(f"error: {e.code}: {e.text}", file=sys.stderr)
        return 3
    except OSError:
        print("error: bad_config: file error", file=sys.stderr)  # fixed text: an OS error message can carry a path
        return 3
    for name in added:
        print(f"added {name}" if name != PASSPHRASE_FILE else f"wrote {name}")
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
