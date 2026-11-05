"""How far to trust what Jagrat said about an incident (item 16c): Low, Medium or High, from signals anyone can check.

Never the model's own confidence: a model that is sure of a wrong answer reads as sure (README, "What it is not").
Each signal below is a fact on the incident's signed record, and the block shows every one of them and which decided
the level:

- evidence: what Jagrat read - something was read, and no read failed;
- diagnosis: Jagrat's own confidence in the diagnosis, as it was recorded when the rules checked it
  (`incident.verify`'s `source_confidence`, confidence.py) - high passes, low fails, medium says no more; an
  incident recorded before Jagrat kept it says "not recorded", and it is never worked out again here, so the page
  shows one level for the diagnosis, the one on the record;
- rules: Jagrat's deterministic rules let the answer stand - the verdict was not rejected, and nothing but the model's
  own low confidence (P4, which this block does not count either way) escalated it;
- fix verified: Jagrat's fix ran and its own checks saw the service recover and stay recovered;
- proven fix: a record this one is linked to as sharing its cause holds a fix that was applied and verified (only when
  the record carries linked records, links.py).

The level - the trust in this outcome: **Low** when any signal failed; **High** when evidence, diagnosis and rules all
passed and at least one of
fix verified and proven fix backs them; **Medium** otherwise - nothing failed, but not enough was
checked to say more.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

LOW, MEDIUM, HIGH = "Low", "Medium", "High"
EVIDENCE, DIAGNOSIS, RULES = "evidence", "diagnosis", "rules"  # the signals, by name
FIX, PROVEN = "fix verified", "proven fix"
COLOUR = {LOW: "bad", MEDIUM: "warn", HIGH: "ok"}  # red, amber, green on the records page
RECORDED_LEVELS = (
    "low",
    "medium",
    "high",
)  # confidence.py's levels, as the verify row records them
SELF_CONFIDENCE = frozenset(
    {"P4-LOW-CONFIDENCE"}
)  # the model's own confidence: not a signal here, either way
NO_DIAGNOSIS = "P0-MODEL-UNAVAILABLE"
FAILED_FIX = frozenset(
    {
        "relapsed",
        "rolled_back",
        "not_recovered",
        "rollback_failed",
        "apply_failed",
        "side_effects",
        "failed_after_apply",
        "cancelled_after_apply",
    }
)
BASE = (EVIDENCE, DIAGNOSIS, RULES)
VERIFY = (
    "incident.verify"  # the rules' check of the diagnosis, and Jagrat's recorded confidence in it
)
GATHER = "incident.gather"  # the evidence read; every check below must come after the newest one
BACKING = (FIX, PROVEN)


@dataclass
class Signal:
    name: str
    passed: bool | None  # None: not checked for this incident
    why: str


@dataclass
class Block:
    level: str
    signals: list[Signal]
    decided_by: list[str]

    @property
    def colour(self) -> str:
        return COLOUR[self.level]


def _last(r: Any, kind: str) -> dict[str, Any] | None:
    rows = [e["body"] for e in r.rows if e["kind"] == kind]
    return rows[-1] if rows else None


def _stale(r: Any, kind: str) -> bool:
    """The last `kind` row comes before the newest run's start (cards.RUN_STARTS: its evidence read, or the incident
    reopening): it checked an earlier run, not this one - the same run boundary the investigation card beside this
    block uses, so the two never speak of different runs.

    An incident run restarted under the same id reads its evidence again; until its own checks are on the record, the
    earlier run's verdict or fix do not back it (CodeRabbit security review, PR 100).
    """
    from .record_kinds import RUN_STARTS

    kinds = [e["kind"] for e in r.rows]
    starts = [i for i, k in enumerate(kinds) if k in RUN_STARTS]
    mine = [i for i, k in enumerate(kinds) if k == kind]
    return bool(starts and mine) and mine[-1] < starts[-1]


def _count(value: Any) -> int | None:
    """A count as Jagrat writes it - a whole number, 0 or more, or nothing - else None."""
    if value is None:
        return 0
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


# The investigation card (cards.py) beside this block already shows what was read and what the rules decided; these
# signals say only whether each passed, and point to the card's line rather than repeat it.
READ_LINE, RULES_LINE = "the card's Read line", "the card's Rules line"


def _evidence(r: Any) -> Signal:
    g = _last(r, GATHER)
    if g is None or _stale(r, GATHER):
        return Signal(EVIDENCE, None, "no evidence read is on the record for the latest run")
    counts = [_count(g.get(k)) for k in ("logs", "metrics", "deploys", "tool_errors")]
    if (
        None in counts
    ):  # a row that is not Jagrat's shape says nothing either way (CodeRabbit, PR 100)
        return Signal(EVIDENCE, None, "the record's read counts could not be read")
    read, failed = sum(counts[:3]), counts[3]
    if failed:
        return Signal(EVIDENCE, False, f"a read failed: the picture is partial ({READ_LINE})")
    if not read:
        return Signal(EVIDENCE, False, f"nothing was read ({READ_LINE})")
    return Signal(EVIDENCE, True, f"something was read and no read failed ({READ_LINE})")


def _verify(r: Any) -> tuple[str, set[str]] | None:
    v = _last(r, VERIFY)
    if v is not None and _stale(r, VERIFY):
        return None
    return (str(v.get("status") or ""), {str(p) for p in v.get("policies") or []}) if v else None


def recorded(r: Any) -> dict[str, Any] | None:
    """Jagrat's confidence in the diagnosis exactly as the last verify row recorded it: its level and each
    check's name and whether it held - or None when the row has none in that shape (an incident from before it was
    recorded, or no diagnosis). Never worked out again here."""
    v = _last(r, VERIFY)
    got = (v or {}).get("source_confidence")
    if not isinstance(got, dict) or got.get("level") not in RECORDED_LEVELS:
        return None
    checks = [
        {"name": str(c["name"]), "met": c["met"]}
        for c in got.get("checks") or []
        if isinstance(c, dict) and isinstance(c.get("name"), str) and isinstance(c.get("met"), bool)
    ]
    return {"level": got["level"], "checks": checks}


def _diagnosis(r: Any) -> Signal:
    if _verify(r) is None and _last(r, VERIFY) is not None:
        return Signal(
            DIAGNOSIS,
            None,
            "Jagrat's confidence was recorded in an earlier run, before the latest evidence read",
        )
    got = recorded(r)
    if got is None:
        return Signal(
            DIAGNOSIS,
            None,
            "Jagrat's confidence in the diagnosis is not recorded for this incident",
        )
    if got["level"] == "high":
        return Signal(
            DIAGNOSIS, True, "Jagrat's own checks of the diagnosis all held (recorded: high)"
        )
    if got["level"] == "low":
        return Signal(
            DIAGNOSIS, False, "Jagrat's own checks of the diagnosis did not hold (recorded: low)"
        )
    return Signal(
        DIAGNOSIS, None, "Jagrat's own checks of the diagnosis held only in part (recorded: medium)"
    )


def _rules(r: Any) -> Signal:
    v = _verify(r)
    if v is None:
        return Signal(RULES, None, "the rules have not checked a diagnosis in the latest run yet")
    status, fired = v
    others = sorted(fired - SELF_CONFIDENCE - {NO_DIAGNOSIS})
    if status == "rejected":
        return Signal(RULES, False, f"the rules rejected the answer ({RULES_LINE})")
    if status == "escalated" and others:
        return Signal(
            RULES,
            False,
            f"a rule other than the model's own confidence (P4) sent it to a person ({RULES_LINE})",
        )
    if NO_DIAGNOSIS in fired:
        return Signal(RULES, None, "no diagnosis: the rules alone sent it to a person")
    return Signal(RULES, True, f"Jagrat's rules let the answer stand ({RULES_LINE})")


def _fix(r: Any) -> Signal:
    end = _last(r, "workflow.end")
    if end is not None and _stale(r, "workflow.end"):
        return Signal(FIX, None, "the last fix ran in an earlier run")
    status = str((end or {}).get("status") or "")
    if status == "recovered":
        return Signal(FIX, True, "the fix's own checks saw recovery, and the re-checks held")
    if status == "mitigated":  # the fix held the harm and did not end it (CodeRabbit, PR 100)
        return Signal(FIX, False, "the fix held the harm but did not fix the cause")
    if status in FAILED_FIX:
        return Signal(FIX, False, f"the fix did not hold ({status.replace('_', ' ')})")
    return Signal(FIX, None, "no fix has run to its checks")


def _proven(r: Any) -> Signal:
    proven = getattr(r, "proven", None)  # linked records (links.py), when the record carries them
    if proven:
        return Signal(
            PROVEN,
            True,
            "a linked record holds a fix that was applied and verified (shown under Decisions)",
        )
    return Signal(PROVEN, None, "no linked record holds a proven fix")


def block(r: Any) -> Block:
    """The confidence block of a record built with its steps (records.record, not `light`)."""
    signals = [_evidence(r), _diagnosis(r), _rules(r), _fix(r), _proven(r)]
    by = {s.name: s for s in signals}
    failed = [s.name for s in signals if s.passed is False]
    if failed:
        return Block(LOW, signals, failed)
    backing = [n for n in BACKING if by[n].passed]
    if all(by[n].passed for n in BASE) and backing:
        return Block(HIGH, signals, [*BASE, *backing])
    missing = [n for n in BASE if by[n].passed is None] + ([] if backing else list(BACKING))
    return Block(MEDIUM, signals, missing)
