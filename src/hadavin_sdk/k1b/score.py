"""Scorer (lite): count how a replay's outputs match the sealed answers. Report only, no verdict.

Per incident, first match wins (v3 section 6, items 1-6):
  1. status error / timeout / capped, or unreadable diagnosis: Miss.
  2. no_evidence incident: Not sure and not converted: Hit (no_evidence); anything else: Miss.
  3. Not sure (including an uncited conversion): Not sure.
  4. any of the first 3 causes off the Cause List: Miss.
  5. any of the first 3 causes equals an accepted pair: Hit.
  6. otherwise Miss.

Errors name only ordinals and counts, never a value from the answers file.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.hashing import hash_files
from hadavin_sdk.k1b.bundle import Bundle, bad_citations, bundle_set_sha256, load_bundles
from hadavin_sdk.k1b.causelist import CauseList, load_cause_list, norm
from hadavin_sdk.k1b.diagnosis import Diagnosis, parse_diagnosis, strict_json_loads
from hadavin_sdk.k1b.replay import outputs_files
from hadavin_sdk.stats import upper_error_bound

STATUSES = ("ok", "error", "timeout", "capped")
REPORT_DIR = "score"
_EXTRA_TOP = {"outputs.sha256", "replay-report.md", REPORT_DIR}
_RUN_RE = re.compile(r"run([1-9][0-9]*)")
_PLAIN_RE = re.compile(r"[A-Za-z0-9._:/+@=-]{1,200}")
_TEXT_KEYS = ("agent", "model_id", "config_hash", "replay_run_id", "prompt_sha256", "sdk_version")
_COUNT_KEYS = (
    "ok",
    "unreadable",
    "error",
    "timeout",
    "capped",
    "uncited_conversions",
    "hard_check_a",
)


def _count(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def _plain(v: Any) -> bool:
    return isinstance(v, str) and _PLAIN_RE.fullmatch(v) is not None


@dataclass(frozen=True)
class Answer:
    accepted: frozenset[tuple[str, str]]
    no_evidence: bool


@dataclass(frozen=True)
class RunScore:
    run_index: int
    classes: dict[str, str]  # case_id -> hit | hne | miss | not_sure
    hits: int  # excluding no_evidence hits
    hne: int
    misses: int
    not_sure: int
    unreadable: int
    error: int
    timeout: int
    capped: int
    uncited: int
    hard_check_a: int
    bad_citations: int  # incidents whose saved answer cites an ID that fails the grammar / bundle / returned check
    n: int  # scored incidents excluding no_evidence incidents
    h: int  # their hits
    misses_scored: int  # misses among them
    bound: float | None  # Hit-rate lower bound, None when n == 0
    precision: float | None  # hits / (hits + misses) over those incidents, None when 0
    issues: dict[str, list[str]] = field(default_factory=dict)  # kind -> case ids (never answers)


@dataclass(frozen=True)
class ScoreResult:
    runs: list[RunScore]
    incidents: int
    no_evidence_incidents: int
    pass_k: int  # incidents that are a Hit (including no_evidence) in every run
    meta: dict[str, Any]
    answers_sha256: str
    outputs_digest: str
    outputs_changed: bool
    warnings: list[str] = field(default_factory=list)


def load_answers(path: Path, cause: CauseList) -> tuple[dict[str, Answer], str]:
    """``answers.json`` (``sealed`` is ignored in lite). Returns the answers and the SHA-256 of the file."""
    try:
        raw = Path(path).read_bytes()  # NOSONAR S8707: the operator's own --answers file
        data = strict_json_loads(raw.decode("utf-8-sig"))
    except (OSError, ValueError, RecursionError) as exc:
        raise ConfigError("answers file is missing or not valid JSON") from exc
    if not isinstance(data, dict) or not set(data) <= {"sealed", "cases"}:
        raise ConfigError("answers file must be an object with the keys sealed and cases")
    cases = data.get("cases")
    if not isinstance(cases, dict) or not cases:
        raise ConfigError("answers file needs a non-empty cases object")
    out: dict[str, Answer] = {}
    for ordinal, cid in enumerate(sorted(cases), 1):
        item = cases[cid]
        if (
            not isinstance(item, dict)
            or set(item) != {"accepted", "no_evidence"}
            or not isinstance(item["no_evidence"], bool)
            or not isinstance(item["accepted"], list)
        ):
            raise ConfigError(f"answer {ordinal} has the wrong shape")
        pairs = []
        for entry in item["accepted"]:
            ok = (
                isinstance(entry, dict)
                and set(entry) == {"service", "fault_type"}
                and all(isinstance(v, str) for v in entry.values())
            )
            if not ok:
                raise ConfigError(f"answer {ordinal} has the wrong shape")
            if not cause.contains(entry["service"], entry["fault_type"]):
                raise ConfigError(f"answer {ordinal} names a value outside the Cause List")
            pairs.append((norm(entry["service"]), norm(entry["fault_type"])))
        low = 0 if item["no_evidence"] else 1
        if not low <= len(pairs) <= 3:
            raise ConfigError(f"answer {ordinal} must list {low} to 3 accepted answers")
        out[cid] = Answer(frozenset(pairs), item["no_evidence"])
    return out, hashlib.sha256(raw).hexdigest()


def classify(
    record: dict[str, Any], diag: Diagnosis | None, answer: Answer, cause: CauseList
) -> str:
    """One incident to ``hit | hne | miss | not_sure`` (the class table above)."""
    if record["status"] != "ok" or diag is None:
        return "miss"
    if answer.no_evidence:
        return "hne" if diag.not_sure and "converted" not in record else "miss"
    if diag.not_sure:
        return "not_sure"
    first = [(norm(c.service), norm(c.fault_type)) for c in diag.scored]
    if any(not cause.contains(s, f) for s, f in first):
        return "miss"
    return "hit" if any(pair in answer.accepted for pair in first) else "miss"


def _recorded_digest(sha_file: Path) -> str | None:
    """The digest the replay wrote, ``None`` when absent, ``""`` when unreadable (counts as changed)."""
    try:
        if not sha_file.is_file():  # NOSONAR S8707: inside the operator's own --outputs folder
            return None
        return sha_file.read_text(encoding="utf-8").strip()  # NOSONAR S8707
    except (OSError, ValueError):
        return ""


def _read_json(path: Path, what: str) -> Any:
    try:
        return strict_json_loads(path.read_bytes().decode("utf-8-sig"))
    except (OSError, ValueError, RecursionError) as exc:
        raise ConfigError(f"{what} is missing or not valid JSON") from exc


def _record(path: Path, case_id: str, ordinal: int) -> dict[str, Any]:
    rec = _read_json(path, f"output file {ordinal}")
    bad = (
        not isinstance(rec, dict)
        or rec.get("case_id") != case_id
        or rec.get("status") not in STATUSES
        or "diagnosis" not in rec
        or not isinstance(rec["diagnosis"], dict | None)
        or not isinstance(rec.get("returned_ids"), list)
        or not all(isinstance(i, str) for i in rec["returned_ids"])
        or rec.get("converted", "uncited") != "uncited"
    )
    if not bad and rec["status"] != "ok" and rec["diagnosis"] is not None:
        bad = True  # an error, timeout or capped incident carries no answer
    if bad:
        raise ConfigError(f"output file {ordinal} has the wrong shape")
    return rec


def _check_layout(out: Path, case_ids: list[str]) -> list[int]:
    """Refuse a folder that is not exactly ``run1..runK`` with every case file and ``run.json``."""
    if not out.is_dir():
        raise ConfigError("outputs folder does not exist")
    names = {p.name for p in out.iterdir()}
    if "FAILED.txt" in names:
        raise ConfigError("outputs folder holds FAILED.txt: the replay did not finish")
    runs = sorted(int(m.group(1)) for n in names if (m := _RUN_RE.fullmatch(n)))
    stray = names - _EXTRA_TOP - {f"run{i}" for i in runs}
    if stray or not runs or runs != list(range(1, len(runs) + 1)):
        raise ConfigError("outputs folder is not exactly run1..runK plus its summary files")
    want = {f"{c}.json" for c in case_ids} | {"run.json"}
    for i in runs:
        files = {p.name for p in (out / f"run{i}").rglob("*")}
        if files != want or any(not p.is_file() for p in (out / f"run{i}").iterdir()):
            raise ConfigError(
                f"run{i} files differ from the answers (missing, extra or temporary files)"
            )
    return runs


def score(out: Path, answers_path: Path, cause_dir: Path, bundles_dir: Path) -> ScoreResult:
    """Score a replay's outputs. Raises ``ConfigError`` for any refusal; nothing is written here."""
    out = Path(out)
    cause = load_cause_list(cause_dir)
    answers, answers_sha = load_answers(answers_path, cause)
    bundles: dict[str, Bundle] = {b.case_id: b for b in load_bundles(bundles_dir)}
    if set(bundles) != set(answers):
        raise ConfigError(
            f"answers cover {len(answers)} incidents but the bundles folder holds {len(bundles)} "
            "(or the incident names differ)"
        )
    case_ids = sorted(answers)
    set_sha = bundle_set_sha256(bundles_dir, [bundles[c] for c in case_ids])
    runs = _check_layout(out, case_ids)
    digest = hash_files(out, outputs_files(out))
    sha_file = out / "outputs.sha256"
    recorded = _recorded_digest(sha_file)
    changed = recorded is not None and recorded != digest
    warnings = (
        [
            "no replay digest (outputs.sha256) found, so it cannot be confirmed that the outputs are unchanged"
        ]
        if recorded is None
        else []
    )

    scores: list[RunScore] = []
    metas: list[dict[str, Any]] = []
    for i in runs:
        rdir = out / f"run{i}"
        meta = _read_json(rdir / "run.json", f"run{i}/run.json")
        ok_meta = (
            isinstance(meta, dict)
            and meta.get("schema") == 1
            and meta.get("run_index") == i
            and meta.get("k") == len(runs)
            and meta.get("cause_services_sha256") == cause.services_sha256
            and meta.get("cause_fault_types_sha256") == cause.fault_types_sha256
            and meta.get("bundle_set_sha256") == set_sha
            and isinstance(meta.get("counts"), dict)
            and all(_count(meta["counts"].get(k)) for k in _COUNT_KEYS)
            and all(_plain(meta.get(k)) for k in _TEXT_KEYS)
        )
        if not ok_meta:
            raise ConfigError(
                f"run{i}/run.json does not match the run, the Cause List or the bundles"
            )
        metas.append(meta)
        classes: dict[str, str] = {}
        tally = {"unreadable": 0, "error": 0, "timeout": 0, "capped": 0, "uncited": 0, "bad": 0}
        issues: dict[str, list[str]] = {
            k: [] for k in ("unreadable", "error", "timeout", "capped", "uncited")
        }
        for ordinal, cid in enumerate(case_ids, 1):
            rec = _record(rdir / f"{cid}.json", cid, ordinal)
            diag = parse_diagnosis(rec["diagnosis"]) if rec["diagnosis"] is not None else None
            if rec["status"] != "ok":
                tally[rec["status"]] += 1
                issues[rec["status"]].append(cid)
            elif diag is None:
                tally["unreadable"] += 1
                issues["unreadable"].append(cid)
            tally["uncited"] += rec.get("converted") == "uncited"
            if rec.get("converted") == "uncited":
                issues["uncited"].append(cid)
            if diag is not None and not diag.not_sure:
                bad = bad_citations(diag, bundles[cid], set(rec["returned_ids"]))
                tally["bad"] += bool(bad)
            classes[cid] = classify(rec, diag, answers[cid], cause)
        counts = meta["counts"]
        recomputed = {
            "ok": len(case_ids) - tally["error"] - tally["timeout"] - tally["capped"],
            "unreadable": tally["unreadable"],
            "error": tally["error"],
            "timeout": tally["timeout"],
            "capped": tally["capped"],
            "uncited_conversions": tally["uncited"],
        }
        if any(counts[k] != v for k, v in recomputed.items()):
            raise ConfigError(f"run{i}/run.json counts disagree with the incident files")
        if (
            "issue_cases" in meta and meta["issue_cases"] != issues
        ):  # absent in runs made before it existed
            raise ConfigError(f"run{i}/run.json issue_cases disagree with the incident files")
        scores.append(_run_score(i, classes, answers, tally, counts["hard_check_a"], issues))

    for key in (
        "agent",
        "model_id",
        "config_hash",
        "replay_run_id",
        "prompt_sha256",
        "sdk_version",
    ):
        if len({m.get(key) for m in metas}) != 1:
            raise ConfigError(f"runs disagree on {key}")
    pass_k = sum(all(s.classes[c] in ("hit", "hne") for s in scores) for c in case_ids)
    first = metas[0]
    info = {
        k: first[k]
        for k in (
            "agent",
            "model_id",
            "config_hash",
            "sdk_version",
            "replay_run_id",
            "cause_services_sha256",
            "cause_fault_types_sha256",
            "bundle_set_sha256",
        )
    }
    info["usd"] = format(sum(_dec(m.get("usd")) for m in metas), "f")
    info["k"] = len(runs)
    return ScoreResult(
        runs=scores,
        incidents=len(case_ids),
        no_evidence_incidents=sum(a.no_evidence for a in answers.values()),
        pass_k=pass_k,
        meta=info,
        answers_sha256=answers_sha,
        outputs_digest=digest,
        outputs_changed=changed,
        warnings=warnings,
    )


def _dec(value: Any) -> Decimal:
    try:
        d = Decimal(str(value))
    except InvalidOperation as exc:
        raise ConfigError("a run.json usd value is not a number") from exc
    if not d.is_finite():
        raise ConfigError("a run.json usd value is not a number")
    return d


def _run_score(
    index: int,
    classes: dict[str, str],
    answers: dict[str, Answer],
    tally: dict[str, int],
    hard_a: int,
    issues: dict[str, list[str]] | None = None,
) -> RunScore:
    def count(cls: str) -> int:
        return sum(v == cls for v in classes.values())

    scored = [c for c in classes if not answers[c].no_evidence]
    h = sum(classes[c] == "hit" for c in scored)
    misses_scored = sum(classes[c] == "miss" for c in scored)
    n = len(scored)
    ub = upper_error_bound(n - h, n)
    return RunScore(
        run_index=index,
        classes=classes,
        hits=count("hit"),
        hne=count("hne"),
        misses=count("miss"),
        not_sure=count("not_sure"),
        unreadable=tally["unreadable"],
        error=tally["error"],
        timeout=tally["timeout"],
        capped=tally["capped"],
        uncited=tally["uncited"],
        hard_check_a=hard_a,
        bad_citations=tally["bad"],
        n=n,
        h=h,
        misses_scored=misses_scored,
        bound=None if ub is None else 1 - ub,
        precision=(h / (h + misses_scored)) if h + misses_scored else None,
        issues=issues or {},
    )


def audit_result(r: RunScore) -> str:
    """The ``score_run`` event's result string for one run (counts only)."""
    return (
        f"H={r.hits + r.hne};Hne={r.hne};M={r.misses};S={r.not_sure};"
        f"ic={r.uncited};ha={r.hard_check_a}"
    )


__all__ = ["Answer", "RunScore", "ScoreResult", "audit_result", "classify", "load_answers", "score"]
