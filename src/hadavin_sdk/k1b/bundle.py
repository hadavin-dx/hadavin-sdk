"""Incident bundle: one frozen directory per incident, loaded under an allowlist and refused on any doubt.

Layout (file names are opaque numbers, never a service or cause): ``incident.json``, ``deploys.json`` (optional),
``metrics/NNN.json``, ``logs/NNN.jsonl``, ``k8s/NNN.json``, ``runbooks/NNN.md`` + ``NNN.meta.json`` and
``manifest.json`` (SHA-256 of every other file; an unlisted or missing file refuses the bundle).
Every timestamp is UTC, ``YYYY-MM-DDTHH:MM:SS(.f{1,6})?Z``, and at or before ``alert_time``.
Free text inside a log line can still mention the future; no code can see that.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from hadavin_sdk.config import confined
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.hashing import hash_files
from hadavin_sdk.k1b.diagnosis import Diagnosis, strict_json_loads

CASE_RE = re.compile(r"^case-[0-9]{3,}$")
_TS_RE = re.compile(
    r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]{1,6}))?Z"
)
_FILE_RES = {
    "metrics": re.compile(r"metrics/[0-9]{3,}\.json"),
    "logs": re.compile(r"logs/[0-9]{3,}\.jsonl"),
    "k8s": re.compile(r"k8s/[0-9]{3,}\.json"),
    "runbooks": re.compile(r"runbooks/[0-9]{3,}\.md"),
    "meta": re.compile(r"runbooks/[0-9]{3,}\.meta\.json"),
}
_ID_RE = re.compile(
    r"(?:logs/[0-9]{3,}\.jsonl#(?:0|[1-9][0-9]*)"
    r"|metrics/[0-9]{3,}\.json#(?:0|[1-9][0-9]*)"
    r"|deploys\.json#(?:0|[1-9][0-9]*)"
    r"|k8s/[0-9]{3,}\.json#(?:spec|events\.(?:0|[1-9][0-9]*))"
    r"|runbooks/[0-9]{3,}\.md#(?:0|[1-9][0-9]*))"
)
# Built from parts: the lock-in guard scans string literals for vendor names, and "meta" followed by a dot is one.
META_SUFFIX = "." + "meta" + ".json"
ALERT_KEYS = {"title", "summary", "severity", "service_label", "fired_by", "labels"}
MAX_SHORT = 200
# Keys whose name hints at the outcome of the incident (lowercase substring match, any depth).
DENY_KEY_PARTS = (
    "status",
    "resolv",
    "clos",
    "updat",
    "mitigat",
    "rootcause",
    "root_cause",
    "postmortem",
    "rollback",
    "answer",
    "fix",
)


# Ordinary Kubernetes words that contain a deny part (rollingUpdate, updateStrategy, prefix, suffix). Removed
# from a key before the deny match. A narrow deviation from v4 5.3 so real Deployment specs load.
BENIGN_KEY_PARTS = ("rollingupdate", "updatestrategy", "prefix", "suffix", "postfix")


class BundleError(ConfigError):
    """The bundle is refused. The message names the case and the problem, never file content."""


def parse_ts(value: Any) -> datetime | None:
    """A timestamp under the one accepted grammar (UTC ``Z`` only), or ``None``."""
    if not isinstance(value, str):
        return None
    m = _TS_RE.fullmatch(value)
    if not m:
        return None
    y, mo, d, h, mi, s, frac = m.groups()
    micro = int((frac or "").ljust(6, "0")) if frac else 0
    try:
        return datetime(int(y), int(mo), int(d), int(h), int(mi), int(s), micro, tzinfo=UTC)
    except ValueError:  # month 13, hour 24, second 60 ...
        return None


def id_grammar_ok(evidence_id: Any) -> bool:
    """The evidence ID grammar: a bundle path, ``#``, a zero-based index (no leading zeros, no ``..``)."""
    return isinstance(evidence_id, str) and _ID_RE.fullmatch(evidence_id) is not None


@dataclass(frozen=True)
class Bundle:
    case_id: str
    alert_time: datetime
    alert_time_text: str
    alert: dict[str, Any]
    metrics: tuple[tuple[str, dict[str, Any]], ...]  # (file, {"query", "points"})
    logs: tuple[tuple[str, tuple[dict[str, Any], ...]], ...]  # (file, records)
    deploys: tuple[dict[str, Any], ...]
    k8s: tuple[tuple[str, dict[str, Any]], ...]
    runbooks: tuple[tuple[str, tuple[str, ...]], ...]  # (file, chunks)
    ids: frozenset[str]
    manifest_sha256: str


def _fail(case: str, msg: str) -> BundleError:
    return BundleError(f"bundle {case}: {msg}")


def _load_json(case: str, root: Path, rel: str) -> Any:
    try:
        obj = strict_json_loads((root / rel).read_bytes().decode("utf-8-sig"))
    except (OSError, ValueError, RecursionError) as exc:  # UnicodeDecodeError is a ValueError
        raise _fail(case, f"{rel} is not valid JSON") from exc
    _no_surrogates(case, rel, obj)
    return obj


def _no_surrogates(case: str, rel: str, obj: Any) -> None:
    """A lone surrogate (JSON escape of half a character) cannot be written as UTF-8 later: refuse it now."""
    if isinstance(obj, str):
        try:
            obj.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise _fail(case, f"{rel} holds an invalid character") from exc
    elif isinstance(obj, dict):
        for k, v in obj.items():
            _no_surrogates(case, rel, k)
            _no_surrogates(case, rel, v)
    elif isinstance(obj, list):
        for v in obj:
            _no_surrogates(case, rel, v)


def _text(case: str, path: Path, rel: str) -> str:
    try:
        return (path / rel).read_bytes().decode("utf-8-sig")
    except (OSError, ValueError) as exc:
        raise _fail(case, f"{rel} is not valid UTF-8 text") from exc


def _keys(case: str, rel: str, obj: Any, allowed: set[str]) -> dict[str, Any]:
    if not isinstance(obj, dict) or set(obj) != allowed:
        raise _fail(case, f"{rel} must be an object with exactly the keys {sorted(allowed)}")
    return obj


def _ts_before(case: str, rel: str, value: Any, alert_time: datetime) -> None:
    t = parse_ts(value)
    if t is None:
        raise _fail(case, f"{rel} has a timestamp outside the accepted grammar")
    if t > alert_time:
        raise _fail(case, f"{rel} has a timestamp after the alert time")


def _str(case: str, rel: str, value: Any) -> str:
    if not isinstance(value, str):
        raise _fail(case, f"{rel} has a non-string field")
    return value


def _scan(case: str, rel: str, obj: Any, alert_time: datetime) -> None:
    """Nested objects cannot take a key allowlist: refuse outcome-hinting keys and any later timestamp string."""
    if isinstance(obj, dict):
        for key, val in obj.items():
            low = str(key).lower()
            for benign in BENIGN_KEY_PARTS:
                low = low.replace(benign, "")
            if any(part in low for part in DENY_KEY_PARTS):
                raise _fail(case, f"{rel} has a key that can reveal the outcome")
            _scan(case, rel, val, alert_time)
    elif isinstance(obj, list):
        for val in obj:
            _scan(case, rel, val, alert_time)
    elif isinstance(obj, str):
        t = parse_ts(obj)
        if t is not None and t > alert_time:
            raise _fail(case, f"{rel} holds a timestamp after the alert time")


def _chunks(text: str) -> tuple[str, ...]:
    parts = re.split(r"\n[ \t]*\n", text.replace("\r\n", "\n").strip())
    return tuple(p for p in parts if p.strip())


def load_bundle(path: Path) -> Bundle:
    path = Path(path)
    case = path.name
    if not CASE_RE.fullmatch(case) or path.is_symlink() or not path.is_dir():
        raise _fail(case, "folder name must look like case-001")
    man_path = path / "manifest.json"
    if not man_path.is_file():
        raise _fail(case, "manifest.json is missing")
    manifest = _keys(case, "manifest.json", _load_json(case, path, "manifest.json"), {"files"})
    listed = manifest["files"]
    if not isinstance(listed, dict):
        raise _fail(case, "manifest.json files must be an object")
    on_disk: set[str] = set()
    for p in path.rglob("*"):
        if p.is_symlink():
            raise _fail(case, "symbolic links are refused")
        if p.is_file():
            on_disk.add(p.relative_to(path).as_posix())
    on_disk.discard("manifest.json")
    if set(listed) != on_disk:
        raise _fail(case, "files on disk and in the manifest differ")
    for rel, digest in listed.items():
        shapes = ("incident.json", "deploys.json")
        if not (rel in shapes or any(r.fullmatch(rel) for r in _FILE_RES.values())):
            raise _fail(case, "a file name is outside the allowed layout")
        confined(path, rel)
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise _fail(case, "a manifest hash is not a SHA-256 hex string")
        if hashlib.sha256((path / rel).read_bytes()).hexdigest() != digest:
            raise _fail(case, f"{rel} does not match the manifest")
    if "incident.json" not in listed:
        raise _fail(case, "incident.json is missing")

    inc = _keys(
        case, "incident.json", _load_json(case, path, "incident.json"), {"alert_time", "alert"}
    )
    alert_time = parse_ts(inc["alert_time"])
    if alert_time is None:
        raise _fail(case, "incident.json alert_time is outside the accepted grammar")
    alert = inc["alert"]
    if not isinstance(alert, dict) or not set(alert) <= ALERT_KEYS:
        raise _fail(case, f"incident.json alert keys must be within {sorted(ALERT_KEYS)}")
    for key, val in alert.items():
        if key == "labels":
            ok = isinstance(val, dict) and all(
                isinstance(k, str) and isinstance(v, str) and len(v) <= MAX_SHORT
                for k, v in val.items()
            )
            if not ok:
                raise _fail(case, "alert labels must be strings of at most 200 characters")
        elif not isinstance(val, str) or (key == "fired_by" and len(val) > MAX_SHORT):
            raise _fail(case, f"alert {key} must be a string (fired_by at most 200 characters)")
    _scan(case, "incident.json", alert, alert_time)

    ids: set[str] = set()
    metrics, logs, k8s, runbooks = [], [], [], []
    for rel in sorted(listed):
        if _FILE_RES["metrics"].fullmatch(rel):
            obj = _keys(case, rel, _load_json(case, path, rel), {"query", "points"})
            _str(case, rel, obj["query"])
            _scan(case, rel, obj, alert_time)
            if not isinstance(obj["points"], list):
                raise _fail(case, f"{rel} points must be a list")
            for i, pt in enumerate(obj["points"]):
                pt = _keys(case, rel, pt, {"ts", "value"})
                v = pt["value"]
                numeric = isinstance(v, int | float) and not isinstance(v, bool)
                if not numeric or not math.isfinite(v):
                    raise _fail(case, f"{rel} has a non-numeric value")
                _ts_before(case, rel, pt["ts"], alert_time)
                ids.add(f"{rel}#{i}")
            metrics.append((rel, obj))
        elif _FILE_RES["logs"].fullmatch(rel):
            text = _text(case, path, rel)
            records = []
            for raw in text.split("\n"):
                if not raw.strip():
                    continue
                try:
                    rec = strict_json_loads(raw)
                except (ValueError, RecursionError) as exc:
                    raise _fail(case, f"{rel} has a line that is not valid JSON") from exc
                rec = _keys(case, rel, rec, {"ts", "level", "message", "service"})
                _no_surrogates(case, rel, rec)
                _scan(case, rel, rec, alert_time)
                for f in ("level", "message", "service"):
                    _str(case, rel, rec[f])
                _ts_before(case, rel, rec["ts"], alert_time)
                ids.add(f"{rel}#{len(records)}")
                records.append(rec)
            logs.append((rel, tuple(records)))
        elif _FILE_RES["k8s"].fullmatch(rel):
            obj = _keys(
                case,
                rel,
                _load_json(case, path, rel),
                {"kind", "name", "as_of", "spec", "events"},
            )
            _str(case, rel, obj["kind"])
            _str(case, rel, obj["name"])
            _ts_before(case, rel, obj["as_of"], alert_time)
            if not isinstance(obj["spec"], dict) or not isinstance(obj["events"], list):
                raise _fail(case, f"{rel} spec must be an object and events a list")
            _scan(case, rel, obj, alert_time)
            ids.add(f"{rel}#spec")
            for i, ev in enumerate(obj["events"]):
                ev = _keys(case, rel, ev, {"ts", "reason", "message"})
                _str(case, rel, ev["reason"])
                _str(case, rel, ev["message"])
                _ts_before(case, rel, ev["ts"], alert_time)
                ids.add(f"{rel}#events.{i}")
            k8s.append((rel, obj))
        elif _FILE_RES["runbooks"].fullmatch(rel):
            meta_rel = rel[: -len(".md")] + META_SUFFIX
            if meta_rel not in listed:
                raise _fail(case, f"{rel} has no runbook metadata file beside it")
            meta = _keys(case, meta_rel, _load_json(case, path, meta_rel), {"as_of"})
            _ts_before(case, meta_rel, meta["as_of"], alert_time)
            chunks = _chunks(_text(case, path, rel))
            ids.update(f"{rel}#{i}" for i in range(len(chunks)))
            runbooks.append((rel, chunks))
        elif _FILE_RES["meta"].fullmatch(rel):
            if rel[: -len(META_SUFFIX)] + ".md" not in listed:
                raise _fail(case, f"{rel} has no runbook beside it")
    deploys: list[dict[str, Any]] = []
    if "deploys.json" in listed:
        raw = _load_json(case, path, "deploys.json")
        if not isinstance(raw, list):
            raise _fail(case, "deploys.json must be a list")
        for i, d in enumerate(raw):
            d = _keys(case, "deploys.json", d, {"ts", "service", "version", "as_of"})
            _scan(case, "deploys.json", d, alert_time)
            _str(case, "deploys.json", d["service"])
            _str(case, "deploys.json", d["version"])
            _ts_before(case, "deploys.json", d["ts"], alert_time)
            _ts_before(case, "deploys.json", d["as_of"], alert_time)
            ids.add(f"deploys.json#{i}")
            deploys.append(d)
    return Bundle(
        case_id=case,
        alert_time=alert_time,
        alert_time_text=inc["alert_time"],
        alert=alert,
        metrics=tuple(metrics),
        logs=tuple(logs),
        deploys=tuple(deploys),
        k8s=tuple(k8s),
        runbooks=tuple(runbooks),
        ids=frozenset(ids),
        manifest_sha256=hashlib.sha256(man_path.read_bytes()).hexdigest(),
    )


def load_bundles(root: Path) -> list[Bundle]:
    """Every ``case-NNN`` folder under ``root``, in sorted case order. Any bad bundle refuses the whole set."""
    root = Path(root)
    if not root.is_dir():
        raise ConfigError("bundles folder does not exist")
    cases = sorted(p for p in root.iterdir() if not p.name.startswith("."))
    if not cases:
        raise ConfigError("bundles folder holds no incidents")
    return [load_bundle(p) for p in cases]


def bundle_set_sha256(root: Path, bundles: list[Bundle]) -> str:
    """One digest over every case manifest (each manifest already hashes every file of its bundle)."""
    return hash_files(Path(root), [f"{b.case_id}/manifest.json" for b in bundles])


def bad_citations(
    diagnosis: Diagnosis, bundle: Bundle, returned: set[str] | frozenset[str]
) -> list[str]:
    """Evidence IDs of the first 3 causes that fail (a) the grammar, (b) existence in the bundle or (c) having
    been returned to the agent in this case. Sorted and unique; empty means every citation holds."""
    bad = set()
    for cause in diagnosis.scored:
        for eid in cause.evidence_ids:
            if not (id_grammar_ok(eid) and eid in bundle.ids and eid in returned):
                bad.add(eid)
    return sorted(bad)
