"""Client-facing reports (Markdown): ``replay-report.md`` and ``score-report.md``. Counts only, no answers.

Rules: ``n/a`` for undefined values, integers for counts, percentages with one decimal, USD never in
scientific notation. The first paragraph of every report is the disclaimer.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hadavin_sdk.k1b.score import RunScore, ScoreResult

DISCLAIMER = (
    "Report only; not a warranty; not evidence of live accuracy; replay does not run the production "
    "approval and limits path."
)
CONFIDENT_WRONG = (
    "Confidently wrong answers are not hidden: they are counted as Misses, never as Not sure."
)


def sdk_label(version: str) -> str:
    return "unreleased build" if version == "0.0.0" else version


def pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x * 100:.1f}%"


def usd(value: Decimal) -> str:
    return format(value, "f")


def _issue_lines(per_run: Any) -> list[str]:
    """ "Which cases" lines (ids only, never answers) so an operator can open the case files."""
    out: list[str] = []
    for index, issues in per_run:
        parts = [f"{k} {', '.join(v)}" for k, v in issues.items() if v]
        if parts:
            out.append(f"- Run {index}: " + "; ".join(parts))
    return ["", "Cases to inspect (case ids):", "", *out] if out else []


def render_replay_report(runs: list[dict[str, Any]], result: str) -> str:
    capped = sum(r["counts"]["capped"] for r in runs)
    lines = ["# Replay report", "", DISCLAIMER, "", f"Replay ended: {result}.", ""]
    lines += [
        f"**Capped cases: {capped}.** A capped case hit a step, tool-call or cost limit and counts as a Miss.",
        "",
    ]
    lines += [
        "| Run | OK | Unreadable | Error | Timeout | Capped | Uncited conversions | Hard-check (a) |"
    ]
    lines += ["|---|---|---|---|---|---|---|---|"]
    for r in runs:
        c = r["counts"]
        lines.append(
            f"| {r['run_index']} | {c['ok']} | {c['unreadable']} | {c['error']} | {c['timeout']} | "
            f"{c['capped']} | {c['uncited_conversions']} | {c['hard_check_a']} |"
        )
    lines += _issue_lines((r["run_index"], r.get("issue_cases") or {}) for r in runs)
    first = runs[0]
    lines += [
        "",
        (
            f"Model: {first['model_id']}. Cost: USD {usd(sum(Decimal(r['usd']) for r in runs))}. "
            f"SDK: {sdk_label(first['sdk_version'])}. Config hash: {first['config_hash']}. "
            f"Bundle set: {first['bundle_set_sha256']}."
        ),
        "",
        "This replay only collects the agent's answers; scoring is a separate step.",
        "",
    ]
    return "\n".join(lines)


def _worst(runs: list[RunScore]) -> list[str]:
    low = min(runs, key=lambda r: (r.hits + r.hne, r.run_index))
    miss = max(runs, key=lambda r: (r.misses, -r.run_index))
    unsure = max(runs, key=lambda r: (r.not_sure, -r.run_index))
    return [
        f"- Fewest Hits (including no-evidence Hits): {low.hits + low.hne} (run {low.run_index})",
        f"- Most Misses: {miss.misses} (run {miss.run_index})",
        f"- Most Not sure: {unsure.not_sure} (run {unsure.run_index})",
    ]


def render_score_report(r: ScoreResult) -> str:
    k = len(r.runs)
    m = r.meta
    out = ["# Replay score report", "", DISCLAIMER, ""]
    out += [
        (
            f"This report counts how the agent answered {r.incidents} recorded incidents in {k} run(s). "
            "It is not contract-grade: there is no tamper-evident lock, no probe cap and no met / not met verdict, "
            "and no payment can depend on it."
        ),
        "",
    ]
    unfinished = sum(s.capped + s.error + s.timeout for s in r.runs)
    if unfinished:
        out += [
            (
                f"The replay did not run every incident to completion ({unfinished} capped, error or timed-out "
                "incident results across the runs); they are counted as Misses."
            ),
            "",
        ]
    for w in r.warnings:
        out += [f"**Note: {w}.**", ""]
    if r.outputs_changed:
        out += [
            "**Warning: outputs changed since replay.** The saved outputs no longer match the digest the replay wrote.",
            "",
        ]
    out += ["## Per run", ""]
    out += [
        (
            "| Run | Hits | No-evidence Hits | Misses | Not sure | Unreadable/error/timeout/capped | "
            "Uncited conversions | Hard-check (a) events |"
        ),
        "|---|---|---|---|---|---|---|---|",
    ]
    for s in r.runs:
        out.append(
            f"| {s.run_index} | {s.hits} | {s.hne} | {s.misses} | {s.not_sure} | "
            f"{s.unreadable}/{s.error}/{s.timeout}/{s.capped} | {s.uncited} | {s.hard_check_a} |"
        )
    out += ["", "Unreadable, error, timeout and capped incidents are counted inside Misses.", ""]
    inspect = _issue_lines((s.run_index, s.issues) for s in r.runs)
    if inspect:
        out += [*inspect[1:], ""]
    out += ["## Worst per row", "", *_worst(r.runs), ""]
    out += [
        "## Same incidents right in every run (pass^k)",
        "",
        f"{r.pass_k} of {r.incidents} incidents were a Hit in all {k} run(s) (includes no-evidence Hits).",
        "",
    ]
    out += ["## Hit-rate range", ""]
    for s in r.runs:
        if s.bound is None:
            out.append(f"- Run {s.run_index}: n/a (no scored incidents).")
        else:
            out.append(
                f"- Run {s.run_index}: Hit rate at least {pct(s.bound)} (95%, one-sided), computed over {s.n} "
                f"scored incidents excluding {r.no_evidence_incidents} no-evidence incidents"
                + ("; with so few incidents this range is wide." if s.n < 30 else ".")
            )
    out += ["", "## Precision", ""]
    for s in r.runs:
        out.append(
            f"- Run {s.run_index}: precision {pct(s.precision)} "
            f"({s.h} Hits and {s.misses_scored} Misses among scored incidents"
            + ("; too few to judge" if 0 < s.h + s.misses_scored < 5 else "")
            + f"); Not sure: {s.not_sure}."
        )
    out += ["", "## Misses and Not sure", "", CONFIDENT_WRONG, ""]
    for s in r.runs:
        out.append(
            f"- Run {s.run_index}: Misses {s.misses}, Not sure {s.not_sure}, "
            f"saved answers citing evidence that fails the checks: {s.bad_citations}."
        )
    out += [
        "",
        "## Cost and settings",
        "",
        f"- Model id: {m['model_id']}",
        f"- Config hash: {m['config_hash']}",
        f"- SDK version: {sdk_label(m['sdk_version'])}",
        f"- Cause List hashes: services {m['cause_services_sha256']}, fault types {m['cause_fault_types_sha256']}",
        f"- Bundle set hash: {m['bundle_set_sha256']}",
        f"- Outputs digest: {r.outputs_digest}",
        f"- Cost: USD {m['usd']}",
        "",
        (
            f"With only {r.incidents} incidents, these numbers can show that the agent got some right or wrong on "
            "this set; they cannot show how it will behave on new incidents. Ranges are wide, one incident moves "
            "the rates a lot, and a replay does not run the production approval and limits path."
        ),
        "",
    ]
    return "\n".join(out)
