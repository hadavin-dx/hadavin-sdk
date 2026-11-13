"""Replay: run every recorded incident through the agent's model, k times, and write the outputs folder.

    OUT/run1/case-001.json ... , OUT/run1/run.json, OUT/run2/... (only with k > 1)
    OUT/outputs.sha256 (convenience copy of the outputs digest, not trusted), OUT/replay-report.md

Report only: nothing here is a warranty and a replay pass is not evidence of live accuracy.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from hadavin_sdk import __version__, pathguard
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.guard.injection import Detector
from hadavin_sdk.hashing import hash_files
from hadavin_sdk.k1b import loop
from hadavin_sdk.k1b.atomic import atomic_write
from hadavin_sdk.k1b.audit_sink import K1bAudit
from hadavin_sdk.k1b.bundle import Bundle, bad_citations, bundle_set_sha256, load_bundles
from hadavin_sdk.k1b.causelist import load_cause_list
from hadavin_sdk.k1b.diagnosis import Diagnosis
from hadavin_sdk.k1b.redaction import SCHEME, redact_bundle
from hadavin_sdk.k1b.report import DISCLAIMER, render_replay_report
from hadavin_sdk.llm.protocol import LLM
from hadavin_sdk.models import new_id
from hadavin_sdk.registry import Registry

_COUNT_KEYS = (
    "ok",
    "unreadable",
    "error",
    "timeout",
    "capped",
    "uncited_conversions",
    "hard_check_a",
    "injection_flagged",
)
_ISSUES = ("unreadable", "error", "timeout", "capped", "uncited")
_NAME_RE = re.compile(r"[a-z_]{1,64}")


__all__ = ["DISCLAIMER", "ReplayResult", "outputs_files", "replay"]


@dataclass
class ReplayResult:
    exit_code: int  # 0 complete, 1 aborted or capped
    result: str  # complete | aborted | capped
    replay_run_id: str
    out: Path
    runs: list[dict[str, Any]] = field(default_factory=list)  # each run.json content


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _diagnosis_dict(d: Diagnosis) -> dict[str, Any]:
    out: dict[str, Any] = {"causes": [c.model_dump() for c in d.causes], "not_sure": d.not_sure}
    if d.reason:
        out["reason"] = d.reason
    return out


def _run_dir(out: Path, run_index: int) -> Path:
    """``out/run<N>``, checked again for every write: a run folder swapped for a link to another folder since the last
    write is refused (R8) before the next file is written. A swap between this check and the write itself is outside the
    threat model (see ``pathguard``)."""
    return pathguard.join(out, f"run{run_index}", what="run folder", must_exist=True, kind="dir")


def _write_json(base: Path, name: str, obj: Any) -> None:
    """Write ``base/name`` as JSON. ``base`` is a folder already validated; the name (a case id or a fixed name) goes
    through ``pathguard`` inside ``atomic_write``."""
    atomic_write(base, name, json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=1) + "\n")


def outputs_files(out: Path) -> list[str]:
    """Every file under ``run*/`` as a posix path relative to ``out`` (what the outputs digest covers)."""
    out = pathguard.operator_dir(out, what="outputs folder")
    found = []
    for run in out.glob(
        "run*"
    ):  # names from a listing: each goes through pathguard before it is used
        rdir = pathguard.join(out, run.name, what="run folder", must_exist=True)
        found += [
            f"{run.name}/{p.relative_to(rdir).as_posix()}" for p in rdir.rglob("*") if p.is_file()
        ]
    return sorted(found)


def _refuse_zero_price(registry: Registry, agent_id: str, llm_kind: str) -> None:
    route = registry.config.routes[registry.agents[agent_id].model_route]
    zero = route.input_usd_per_mtok == 0 or route.output_usd_per_mtok == 0
    if zero and llm_kind != "fake":
        # A zero price makes every reply cost 0 and the --max-usd cap could never fire.
        raise ConfigError("replay refuses a route with a zero input or output price")


class _Progress:
    """One flag: has ``_replay`` made the output folder yet? Set by ``_replay``, read by ``replay``."""

    output_created = False


def _replay(
    registry: Registry,
    llm: LLM,
    detector: Detector,
    audit: K1bAudit,
    *,
    agent_id: str,
    bundles_dir: Path,
    cause_list_dir: Path,
    k: int,
    max_usd: Decimal,
    out: Path,
    llm_kind: str | None = None,
    acknowledge_masked: bool = False,
    clock: Callable[[], float] | None = None,
    progress: _Progress | None = None,
) -> ReplayResult:
    """Raises ``ConfigError`` for any refusal before the output folder exists (nothing written), ``AuditUnavailable``
    when an event cannot be written. ``progress`` is set by ``replay`` so it knows whether the folder exists. Aborts (non-transient provider error) and the USD cap return exit code 1."""
    cfg = registry.config
    if k < 1:
        raise ConfigError("replay k must be at least 1")
    if not max_usd.is_finite() or max_usd <= 0:
        raise ConfigError("replay --max-usd must be above zero")
    if agent_id not in registry.agents:
        raise ConfigError(f"unknown agent {agent_id!r}")
    _refuse_zero_price(registry, agent_id, llm_kind or cfg.backends.llm.kind)
    if not cfg.k1b.redact and not acknowledge_masked:
        raise ConfigError(
            "k1b.redact is false: client data would go to the model unmasked. Pass "
            "--i-know-data-is-already-masked only if the bundles are already masked"
        )
    try:
        out = pathguard.operator_dir(out, what="replay output folder", must_exist=False)
    except pathguard.PathRefused as exc:  # it exists and is a file
        raise pathguard.mapped(exc, R11="replay output folder exists and is not empty") from None
    if out.exists() and any(out.iterdir()):
        raise ConfigError("replay output folder exists and is not empty")
    cause = load_cause_list(cause_list_dir)
    bundles: list[Bundle] = load_bundles(bundles_dir)
    set_sha = bundle_set_sha256(bundles_dir, bundles)
    agent = registry.agents[agent_id]
    system = registry.prompt(agent_id) + "\n\n" + loop.SYSTEM_PROMPT
    max_steps = min(cfg.k1b.max_steps, agent.max_steps)
    out.mkdir(parents=True, exist_ok=True)
    if progress is not None:
        progress.output_created = True

    run_id = new_id("k1b")
    budget = loop.Budget(max_usd)
    stop: str | None = None  # None | "capped" | "aborted"
    runs: list[dict[str, Any]] = []
    extra = {"clock": clock} if clock else {}
    masked_cache: dict[
        str, tuple[Bundle, Counter[str]]
    ] = {}  # masked once per case, reused for every run
    for run_index in range(1, k + 1):
        rdir = pathguard.join(out, f"run{run_index}", what="run folder")
        rdir.mkdir()
        counts = dict.fromkeys(_COUNT_KEYS, 0)
        run_usd = Decimal(0)
        issue_cases: dict[str, list[str]] = {k: [] for k in _ISSUES}
        masked: Counter[str] = Counter()
        masked_cases = 0
        for b in bundles:
            before = budget.spent
            record: dict[str, Any]
            shown = b
            if stop is None:
                if cfg.k1b.redact:  # the map is dropped inside; only the per-class counts come back
                    if b.case_id not in masked_cache:
                        masked_cache[b.case_id] = redact_bundle(b)
                    shown, counts_by_kind = masked_cache[b.case_id]
                    masked += counts_by_kind
                    masked_cases += bool(counts_by_kind)
                o = loop.run_case(
                    llm,
                    system=system,
                    route=agent.model_route,
                    route_prices=cfg.routes[agent.model_route],
                    bundle=shown,
                    detector=detector,
                    budget=budget,
                    max_steps=max_steps,
                    max_tool_calls=cfg.k1b.max_tool_calls,
                    timeout_s=cfg.k1b.case_timeout_s,
                    **extra,
                )
                stop = o.halt
            else:
                o = loop.CaseOutcome(
                    status="capped" if stop == "capped" else "error", stop_reason=stop
                )
            record = {"case_id": b.case_id, "status": o.status}
            if o.stop_reason:
                record["stop_reason"] = o.stop_reason
            diag = o.diagnosis if o.status == "ok" else None
            for name in o.hard_check_a:
                audit.emit(
                    "hard_check_a",
                    run_id,
                    object_ref=b.case_id,
                    inputs_hash=_sha(name),
                    decision="blocked",
                    rule_id="hard_check_a",
                    result="blocked",
                    error_code=name if _NAME_RE.fullmatch(name) else "invalid_name",
                )
            if diag is not None and not diag.not_sure:
                bad = bad_citations(diag, shown, o.returned_ids)
                if bad:
                    audit.emit(
                        "hard_check_b",
                        run_id,
                        object_ref=b.case_id,
                        inputs_hash=_sha(json.dumps(bad)),
                        decision="converted",
                        rule_id="hard_check_b",
                        result="not_sure",
                    )
                    record["converted"] = "uncited"
                    diag = Diagnosis(causes=[], not_sure=True)
                    counts["uncited_conversions"] += 1
            record["diagnosis"] = _diagnosis_dict(diag) if diag is not None else None
            if o.raw is not None:
                record["raw"] = o.raw
            record["returned_ids"] = sorted(o.returned_ids)
            if o.via:
                record["answered_via"] = o.via
            if o.status != "ok":
                issue_cases[o.status].append(b.case_id)
            elif diag is None:
                issue_cases["unreadable"].append(b.case_id)
            if record.get("converted") == "uncited":
                issue_cases["uncited"].append(b.case_id)
            _write_json(_run_dir(out, run_index), f"{b.case_id}.json", record)
            counts[o.status] += 1
            counts["unreadable"] += o.status == "ok" and diag is None
            counts["hard_check_a"] += len(o.hard_check_a)
            counts["injection_flagged"] += o.injection_flagged
            run_usd += budget.spent - before
        meta = {
            "schema": 1,
            "run_index": run_index,
            "k": k,
            "replay_run_id": run_id,
            "agent": agent_id,
            "model_id": cfg.routes[agent.model_route].model_id,
            "config_hash": registry.config_hash(agent_id),
            "prompt_sha256": _sha(system),
            "agent_prompt_sha256": registry.prompt_sha256(agent_id),
            "bundle_set_sha256": set_sha,
            "cause_services_sha256": cause.services_sha256,
            "cause_fault_types_sha256": cause.fault_types_sha256,
            "cases": len(bundles),
            "counts": counts,
            "redaction": {
                "mode": "on" if cfg.k1b.redact else "off_acknowledged",
                "scheme": SCHEME
                if cfg.k1b.redact
                else "none: the operator stated the bundles are already masked",
                "distinct_values_masked": dict(sorted(masked.items())),
                "cases_with_masking": masked_cases,
            },
            "issue_cases": issue_cases,  # ids only, never answers
            "usd": format(run_usd, "f"),
            "sdk_version": __version__,
            "temperature": "provider default",
        }
        _write_json(_run_dir(out, run_index), "run.json", meta)
        runs.append(meta)

    result = stop or "complete"
    audit.emit("replay_run", run_id, object_ref=agent_id, inputs_hash=set_sha, result=result)
    atomic_write(out, "outputs.sha256", hash_files(out, outputs_files(out)) + "\n")
    atomic_write(out, "replay-report.md", render_replay_report(runs, result))
    return ReplayResult(0 if result == "complete" else 1, result, run_id, out, runs)


def _mark_failed(out_arg: Path, exc: BaseException) -> None:
    """Write ``FAILED.txt`` into the output folder, empty or not (the folder exists: ``_replay`` made it). A folder that
    cannot be validated is left alone."""
    try:
        out = pathguard.operator_dir(out_arg, what="replay output folder", must_exist=False)
    except pathguard.PathRefused:
        return
    if out.is_dir():
        atomic_write(out, "FAILED.txt", f"replay did not finish: {type(exc).__name__}\n")


def replay(*args: Any, **kwargs: Any) -> ReplayResult:
    """Run a replay (arguments: see ``_replay``). If it dies after the output folder exists, ``FAILED.txt`` is
    written into it so the operator can tell a dead run from a finished one; delete the folder to run again."""
    progress = _Progress()
    try:
        return _replay(*args, progress=progress, **kwargs)
    except (
        BaseException
    ) as exc:  # includes Ctrl-C and a refusal (PathRefused is a ConfigError) after output exists
        if progress.output_created:  # a refusal before the folder exists wrote nothing: no marker
            try:
                _mark_failed(kwargs["out"], exc)
            except (
                OSError,
                ConfigError,
            ) as second:  # the original error is the one the caller must see; this one is a note
                exc.add_note(f"FAILED.txt was not written ({type(second).__name__})")
            except (
                KeyboardInterrupt,
                MemoryError,
            ) as stop:  # raised unchanged, with the first error named
                stop.add_note(f"the replay had already stopped with {type(exc).__name__}")
                raise
        raise
