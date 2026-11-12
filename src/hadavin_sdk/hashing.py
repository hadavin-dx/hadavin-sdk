"""One digest over a set of files, used by K1b for bundle sets and replay outputs."""

from __future__ import annotations

import hashlib
from pathlib import Path

from hadavin_sdk.config import ConfigError, confined


def hash_files(root: Path, rel_paths: list[str]) -> str:
    r"""Hex SHA-256 over lines ``<posix path>\0<file sha256 hex>\n``, sorted by path bytes.

    Every path is confined to ``root`` (``..`` or absolute paths raise ``ConfigError``), must be a file, and
    may not contain a backslash or NUL. Paths are named by their canonical form, so ``a/b``, ``./a/b`` and
    ``a//b`` are one entry.
    """
    base = Path(root).resolve()
    entries: dict[str, str] = {}
    for rel in rel_paths:
        if chr(92) in rel or chr(0) in rel:
            raise ConfigError("path has a backslash or NUL character")
        path = confined(root, rel)
        if not path.is_file():
            raise ConfigError(f"not a file: {rel}")
        failed = False
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            failed = True  # the OS error quotes the full path; raised after this block, so nothing carries it
        if failed:
            raise ConfigError(f"cannot read: {rel}")
        entries[path.relative_to(base).as_posix()] = digest
    outer = hashlib.sha256()
    for name, digest in sorted((k.encode("utf-8"), v) for k, v in entries.items()):
        outer.update(name + b"\0" + digest.encode("ascii") + b"\n")
    return outer.hexdigest()
