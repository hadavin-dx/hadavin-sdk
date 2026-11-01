"""Reason codes, exit codes and the retry policy by SQLSTATE (design 9.1, amendments A-14). Pure data and
functions, no I/O.

Nothing a server says is fed back to the model: only the SQLSTATE and a FIXED hint from this table.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Outcome = Literal["answered", "abstained", "refused", "failed"]
ReasonCode = Literal[
    "write_request", "restricted_data", "injection_suspected", "over_budget", "kill_switch",
    "out_of_scope", "ambiguous", "insufficient_schema", "uncertain",
    "unsafe_query", "execution_failed", "timeout", "schema_violation", "model_unavailable", "audit_unavailable",
]  # fmt: skip
Alarm = Literal["validator_gap", "role_gap", "readonly_violation", "hash_mismatch"]

# Exit codes of `ask`. 0 answered; 1 usage; 4 startup (red check, bad config, invalid authorization).
EXIT_OK, EXIT_USAGE, EXIT_STARTUP = 0, 1, 4


@dataclass(frozen=True)
class Reason:
    outcome: Outcome
    exit_code: int
    sentence: str


REASONS: dict[str, Reason] = {
    "write_request": Reason("refused", 2, "This tool only reads data."),
    "restricted_data": Reason("refused", 2, "That field is not exposed to this tool."),
    "injection_suspected": Reason("refused", 2, "That request looks like an instruction to the tool and was not run."),
    "over_budget": Reason("refused", 6, "Spending limit reached; not run."),
    "kill_switch": Reason("refused", 6, "The tool is switched off."),
    "out_of_scope": Reason("abstained", 7, "The data does not cover that."),
    "ambiguous": Reason("abstained", 7, "The question can be read more than one way."),
    "insufficient_schema": Reason("abstained", 7, "The data does not hold what is needed."),
    "uncertain": Reason("abstained", 7, "Two ways of asking gave different results."),
    "unsafe_query": Reason("failed", 3, "I could not produce a safe query for that."),
    "execution_failed": Reason("failed", 3, "The database could not run that query."),
    "timeout": Reason("failed", 3, "The query ran too long and was stopped."),
    "schema_violation": Reason("failed", 3, "The model did not return a usable answer."),
    "model_unavailable": Reason("failed", 3, "The model service is unavailable."),
    "audit_unavailable": Reason("failed", 5, "Audit unavailable; not run."),
}  # fmt: skip

# The model's own `abstain_reason` values are reason codes (the five of the GenerateOutput schema).
ABSTAIN_REASONS = (
    "out_of_scope",
    "ambiguous",
    "write_request",
    "restricted_data",
    "insufficient_schema",
)

# When more than one applies to the final result, the first in this list wins (non-terminal ones: the LAST attempt).
PRECEDENCE = (
    "audit_unavailable", "kill_switch", "over_budget", "model_unavailable",
    "schema_violation", "timeout", "unsafe_query", "execution_failed",
)  # fmt: skip


def pick_reason(candidates: list[str]) -> str:
    for code in PRECEDENCE:
        if code in candidates:
            return code
    return candidates[-1] if candidates else "execution_failed"


def exit_code(outcome: Outcome, reason: str | None) -> int:
    return EXIT_OK if outcome == "answered" else REASONS[reason or "execution_failed"].exit_code


# ------------------------------------------------------------------------------------------ SQLSTATE table

Action = Literal["stop", "retry", "retry_once", "reconnect", "abort"]


@dataclass(frozen=True)
class Decision:
    action: Action
    reason: str
    hint: str | None = None
    alarm: Alarm | None = None


_MISSING = "an object does not exist: use only the catalog"
_TYPES = "type or grouping error: check casts and GROUP BY"
_VALUE = "a value was invalid for the operation: guard with NULLIF or filter"
_SLOW = "the query was too slow: add filters or reduce joins"

_TABLE: dict[str, Decision] = {
    "42501": Decision("stop", "execution_failed", alarm="role_gap"),
    "25006": Decision("stop", "unsafe_query", alarm="readonly_violation"),
    "42601": Decision("stop", "execution_failed", alarm="validator_gap"),
    "53200": Decision("stop", "execution_failed"),
    "57014": Decision("retry_once", "timeout", _SLOW),
    **dict.fromkeys(("42P01", "42703", "42883", "42P10"), Decision("retry", "execution_failed", _MISSING)),
    **dict.fromkeys(("42804", "42803", "42725", "42P18"), Decision("retry", "execution_failed", _TYPES)),
    **dict.fromkeys(("22012", "22003", "22007", "22008", "22P02", "22023"), Decision("retry", "execution_failed", _VALUE)),
    **dict.fromkeys(("53300", "57P03", "57P01"), Decision("reconnect", "execution_failed")),
    **dict.fromkeys(("55P03", "40001", "40P01"), Decision("retry_once", "execution_failed")),
}  # fmt: skip


def decide(sqlstate: str | None) -> Decision:
    """What to do after the database failed an accepted statement. `None` = no SQLSTATE (a connection failure)."""
    if sqlstate is None:
        return Decision("reconnect", "execution_failed")
    if sqlstate in _TABLE:
        return _TABLE[sqlstate]
    if sqlstate.startswith("08"):
        return Decision("reconnect", "execution_failed")
    if sqlstate.startswith("28"):
        return Decision("abort", "execution_failed")
    return Decision("stop", "execution_failed")


def rule_hint(rule: str, descriptions: dict[str, str]) -> str:
    """The fixed one-line hint for a validator rejection: the rule id and its registry description."""
    return f"{rule}: {descriptions.get(rule, 'rejected')}"
