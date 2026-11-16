"""Before Jagrat undoes its own fix, it looks for anything else that landed on the target since the fix.

An undo puts back what the plan's snapshot recorded. If a deploy, another person's change or another run's fix
reached the target after Jagrat's fix, the undo may write over it. So before a rollback Jagrat reads, from the time
its fix was applied until now:
- Jagrat's own fixes of the same target by another run (the record of applied fixes);
- the simulated platform's change log, through the `changes` callable the verify step passes in.
Anything found, or a source that cannot be read, and the fix is not undone: a person decides.

Every read is whole or it is unknown. What landed is kept redacted. The platform's own change reader is a callable
`changes(since, until) -> list[{"at", "source", "what", "who", "target"?}]` (None where a platform has none: the
record then says "unchecked").
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from hadavin_sdk.guard.redact import redact

from .record_kinds import APPLIED

# A change log stamps an event to the second and the fix's own time is finer: an event in the same second can read
# as earlier, so the window reaches this far back.
SKEW = timedelta(seconds=2)

READ_ERRORS = (OSError, ValueError, KeyError, TypeError, RuntimeError)


def since_fix(
    *,
    target: str,
    workflow_id: str,
    applied_at: datetime,
    now: datetime,
    log: Any,
    changes: Callable[[datetime, datetime], list[dict[str, Any]]] | None = None,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """(what landed on the target after the fix, the sources that could not be read, the sources this target has none
    of)."""
    landed = [
        {
            "at": e["at"],
            "source": "jagrat",
            "what": f"{e['body'].get('action_class', '?')} by fix run "
            f"{e['body'].get('workflow_id', '?')}",
            "who": "Jagrat",
        }
        for e in log.entries(kinds=(APPLIED,), since=applied_at)
        if e["body"].get("service") == target and e["body"].get("workflow_id") != workflow_id
    ]
    unread: list[str] = []
    unchecked = (
        [] if changes is not None else ["change log (this target's platform has no change reader)"]
    )
    if changes is not None:
        try:
            found = [
                c
                for c in changes(applied_at - SKEW, now)
                if c.get("target", target) == target
                and (not isinstance(c.get("at"), datetime) or c["at"] >= applied_at - SKEW)
            ]
        except READ_ERRORS as exc:
            unread.append(f"change log ({type(exc).__name__})")
        else:
            landed += found
    landed.sort(key=lambda c: c["at"] if isinstance(c.get("at"), datetime) else applied_at)
    return landed, unread, unchecked


def shown(landed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """What landed, as the record keeps it: every text redacted, one mapping."""
    mapping: dict[str, str] = {}
    return [
        {
            k: (
                redact(v, mapping=mapping).text
                if isinstance(v, str)
                else v.isoformat()
                if isinstance(v, datetime)
                else v
            )
            for k, v in c.items()
        }
        for c in landed
    ]


def said(landed: list[dict[str, Any]], unread: list[str]) -> str:
    """Why the fix is not undone, in one line, redacted."""
    if landed:
        first = shown(landed[:1])[0]
        more = f" and {len(landed) - 1} more" if len(landed) > 1 else ""
        when = str(first.get("at") or "an unknown time")[:16].replace("T", " ")
        return (
            f"not rolled back: {first['source']} {first['what']} by {first['who']} landed on the target at "
            f"{when}Z, after Jagrat's fix{more}; undoing the fix now could undo or break that change - a person "
            "decides"
        )
    return (
        f"not rolled back: {', '.join(unread)} could not be read, so whether anything landed on the target after "
        "Jagrat's fix is unknown - a person decides"
    )
