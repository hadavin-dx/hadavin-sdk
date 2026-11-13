"""One digest over a set of files, used by K1b for bundle sets and replay outputs."""

from __future__ import annotations

import hashlib
from pathlib import Path

from hadavin_sdk import pathguard
from hadavin_sdk.config import ConfigError, confined


def hash_files(root: Path, rel_paths: list[str]) -> str:
    r"""Hex SHA-256 over lines ``<posix path>\0<file sha256 hex>\n``, sorted by path bytes.

    Every path is confined to ``root`` (``..`` or absolute paths raise ``ConfigError``), must be a file, and
    may not contain a backslash or NUL. Paths are named by their canonical form, so ``a/b``, ``./a/b`` and
    ``a//b`` are one entry.
    """
    # the folder the caller names: shape checked, the resolved path is what is used below
    try:
        base = pathguard.operator_dir(root, what="hash folder")
    except pathguard.PathRefused as exc:
        raise pathguard.mapped(
            exc, R10="hash folder does not exist", R11="hash folder does not exist"
        ) from None
    entries: dict[str, str] = {}
    for rel in rel_paths:
        if chr(92) in rel or chr(0) in rel:
            raise ConfigError("path has a backslash or NUL character")
        # ``.``, ``//`` and ``a/../b`` fold away here; a link or ``..`` out of the folder is refused
        found = confined(base, rel)
        try:  # one guard before the read: every name that is left goes through ``pathguard.join``
            path = pathguard.join(
                base, *found.relative_to(base).parts, what="hash file", must_exist=True, kind="file"
            )
        except pathguard.PathRefused as exc:
            raise pathguard.mapped(
                exc, R10=f"not a file: {rel}", R11=f"not a file: {rel}"
            ) from None
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:  # no chain: its text can hold the path
            raise ConfigError(f"cannot read: {rel}") from None
        entries[path.relative_to(base).as_posix()] = digest
    outer = hashlib.sha256()
    for name, digest in sorted((k.encode("utf-8"), v) for k, v in entries.items()):
        outer.update(name + b"\0" + digest.encode("ascii") + b"\n")
    return outer.hexdigest()
