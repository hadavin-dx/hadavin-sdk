"""The start-up and tick probe of the kill switch guard: it reads the database catalog and says whether the guard
is in place for the NAMED roles. It never changes anything and never calls the stop or the reset.

Three answers: OK, FAILED (the guard is wrong: a finding about grants, triggers or functions) and INCONCLUSIVE (the
database was busy, so nothing is known; never reported as a finding about the grants)."""

from __future__ import annotations

from dataclasses import dataclass

from hadavin_sdk.store.protocol import Store, StoreBusy

OK, FAILED, INCONCLUSIVE = "ok", "failed", "inconclusive"
LIVE_STAGES = frozenset({"pilot", "prod"})


class ProbeInconclusive(RuntimeError):
    """The database was busy, so the probe could not tell."""


@dataclass(frozen=True)
class ProbeResult:
    status: str
    problems: tuple[str, ...] = ()


def probe(
    store: Store,
    *,
    environment: str,
    runtime_role: str | None,
    stop_role: str | None,
    reset_group: str | None,
) -> ProbeResult:
    """In pilot and prod the tolerated findings (a superuser-owned function) count as problems too."""
    try:
        report = store.guard_report(runtime_role, stop_role, reset_group)
    except StoreBusy:
        return ProbeResult(INCONCLUSIVE)
    problems = report.problems + (report.dev_tolerated if environment in LIVE_STAGES else ())
    if (
        environment in LIVE_STAGES
        and runtime_role
        and report.runtime_connection_limit in (None, -1)
    ):
        problems += ("the runtime role has no connection limit",)
    return ProbeResult(FAILED if problems else OK, problems)
