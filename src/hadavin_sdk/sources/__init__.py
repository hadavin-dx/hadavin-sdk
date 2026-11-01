"""Read-source interfaces (K5-core): what a read tool asks of an incident, metrics, logs or change system.

Four small interfaces so the agent never depends on one vendor's API: each adapter (Kubernetes here, CloudWatch,
PagerDuty, GitHub, Prometheus and others in the packs) implements the ones it can answer, and one contract suite
per interface (tests/contracts/test_sources.py) runs against every adapter. Records are plain dicts that each
carry a string ``id``; "no data" is an empty list, never an error, and an adapter that cannot answer raises
``SourceError``.

``probe_scope`` is the design 6.6 start-up probe: a list of problems found in the read credential (an empty list
means the probe passed), or ``None`` when the source cannot be probed, in which case the config must carry a
``scope_inventory`` reference: an operator attestation that is format-checked and logged, not verified. ``scope_problems`` combines the two.

Neutral protocol: plain Python protocols; adapters speak whatever the source speaks.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

Record = dict[str, Any]


class SourceError(RuntimeError):
    """The source could not answer (unreachable, refused, malformed). Never raised for "no data"."""

    too_large = False  # the reply was over the fetch cap: asking for less may work


class Source(Protocol):
    name: str

    def probe_scope(self) -> list[str] | None:
        """Problems found in the read credential's scope (empty: passed), or None when it cannot be probed."""
        ...


@runtime_checkable
class IncidentSource(Source, Protocol):
    def get_incident(self, incident_id: str) -> Record | None: ...
    def list_open(self, limit: int) -> list[Record]: ...


@runtime_checkable
class MetricsSource(Source, Protocol):
    def query_metrics(self, query: str, start: str, end: str, step_s: int) -> list[Record]: ...


@runtime_checkable
class LogsSource(Source, Protocol):
    def query_logs(self, query: str, start: str, end: str, limit: int) -> list[Record]: ...


@runtime_checkable
class ChangeSource(Source, Protocol):
    def recent_changes(self, scope: str, start: str, end: str) -> list[Record]: ...


def scope_problems(sources: Mapping[str, Source], inventory: Mapping[str, str]) -> list[str]:
    """Design 6.6: every source has a passing probe or an operator-attested inventory reference (format-checked, not verified); otherwise the
    process does not start. A probe that finds a problem is never overridden by an inventory."""
    out: list[str] = []
    for key, source in sorted(sources.items()):
        try:
            found = source.probe_scope()
        except Exception as exc:  # noqa: BLE001 - an unprobeable credential is an unproven one
            out.append(f"source {key}: scope probe failed ({type(exc).__name__})")
            continue
        if found is None:
            if key not in inventory:
                out.append(
                    f"source {key}: cannot be probed and has no scope_inventory reference (design 6.6)"
                )
        else:
            out += [f"source {key}: {p}" for p in found]
    return out
