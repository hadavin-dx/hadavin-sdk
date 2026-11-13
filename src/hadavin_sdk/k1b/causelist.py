"""Cause List: the closed set of services and fault types an answer may name.

``DIR/services.json``: list of unique strings (1-200). ``DIR/fault_types.json``: list of unique strings (1-15).
Read with ``utf-8-sig``. Matching is Unicode NFC plus strip, then exact case-sensitive equality; the same rule
applies to the list, the agent's outputs and the sealed answers.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from hadavin_sdk import pathguard
from hadavin_sdk.errors import ConfigError

MAX_SERVICES = 200  # a sanity bound, not a contract number
MAX_FAULT_TYPES = 15


def norm(value: str) -> str:
    return unicodedata.normalize("NFC", value).strip()


@dataclass(frozen=True)
class CauseList:
    services: frozenset[str]
    fault_types: frozenset[str]
    services_sha256: str
    fault_types_sha256: str

    def contains(self, service: str, fault_type: str) -> bool:
        return norm(service) in self.services and norm(fault_type) in self.fault_types


def _load(directory: Path, name: str, limit: int) -> tuple[frozenset[str], str]:
    """Read ``DIR/name`` (``name`` is a constant of ours). Containment is ``pathguard.join``; the file is then read by
    its resolved name, so a swap between the check and the read is out of scope (the threat model of ``pathguard``)."""
    try:
        path = pathguard.join(directory, name, what="cause list file", must_exist=True, kind="file")
    except pathguard.PathRefused as exc:
        inside_only = f"cause list: {name} must be a file inside the directory"
        raise pathguard.mapped(
            exc,
            R10=f"cause list: {name} is missing or not readable",  # missing file, symlink loop, permission
            R8=inside_only,
            R11=inside_only,
        ) from None
    try:
        raw = path.read_bytes()
        data = json.loads(raw.decode("utf-8-sig"))
    except (
        OSError,
        ValueError,
        RecursionError,
        RuntimeError,
    ):  # missing file, bad UTF-8, bad JSON
        raise ConfigError(f"cause list: {name} is missing or not valid JSON") from None
    if not isinstance(data, list) or not all(isinstance(v, str) for v in data):
        raise ConfigError(f"cause list: {name} must be a list of strings")
    values = [norm(v) for v in data]
    try:
        for v in values:
            v.encode("utf-8")
    except UnicodeEncodeError:  # a lone surrogate would crash later writes
        raise ConfigError(f"cause list: {name} has an invalid character") from None
    if not 1 <= len(values) <= limit:
        raise ConfigError(f"cause list: {name} must hold 1 to {limit} entries, has {len(values)}")
    if "" in values:
        raise ConfigError(f"cause list: {name} has an empty entry")
    if len(set(values)) != len(values):
        raise ConfigError(f"cause list: {name} has duplicate entries")
    return frozenset(values), hashlib.sha256(raw).hexdigest()


def load_cause_list(directory: Path) -> CauseList:
    try:
        directory = pathguard.operator_dir(directory, what="cause list folder")
    except pathguard.PathRefused:  # missing, not a folder, cannot be resolved, a control character
        raise ConfigError("cause list: directory not found") from None
    services, s_hash = _load(directory, "services.json", MAX_SERVICES)
    faults, f_hash = _load(directory, "fault_types.json", MAX_FAULT_TYPES)
    return CauseList(services, faults, s_hash, f_hash)
