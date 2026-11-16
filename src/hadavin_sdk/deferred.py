"""Deferred features, refused at load with the phase they arrive in (kernel design 6.4).

Pure checks that return problem strings; ``registry.load_registry`` and ``config.load_config`` raise them as one
``ConfigError``. A refusal row lives here; the feature it guards arrives in a later PR or phase.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from hadavin_sdk import replay_records
from hadavin_sdk.actions.contract import effective_class

if TYPE_CHECKING:
    from hadavin_sdk.registry import Registry

# Top-level keys of config.yaml, agents.yaml entries and contracts that name a later phase.
DEFERRED_KEYS = {
    "memory": "Phase 5",
    "knowledge": "Phase 5",
    "cases": "Phase 5",
    "delegation": "Phase 5",
    "caps": "Phase 4",
    "log_only": "Phase 6",
    "step_up": "Phase 3",
    "stepup": "Phase 3",
    # Request-tracker features W1-W5 (design 15): no code exists; a signed request-tracker deal builds them.
    "requests": "Phase 2 (request tracker)",
    "org_directory": "Phase 2 (request tracker)",
    "intake_forms": "Phase 2 (request tracker)",
    "provisioning": "Phase 2 (request tracker)",
}
LIVE = ("pilot", "prod")


def key_problems(where: str, raw: Any) -> list[str]:
    if not isinstance(raw, dict):
        return []
    return [
        f"{where}: key {k!r} is not available until {DEFERRED_KEYS[k]}"
        for k in raw
        if k in DEFERRED_KEYS
    ]


def check(reg: Registry) -> list[str]:
    cfg = reg.config
    live = cfg.environment in LIVE
    out: list[str] = []
    for c in reg.contracts.values():
        if c.executor.kind == "manual":
            out.append(f"action {c.id}: executor manual arrives with K8 (posted fixes)")
        if live and c.executor.kind == "http":
            out.append(
                f"action {c.id}: executor http is not available in pilot or prod until Phase 2"
            )
        if live and c.risk_class == "read_only":
            out.append(
                f"action {c.id}: a read_only action is a tool in pilot or prod, not a contract"
            )
    for a in reg.agents.values():
        if live and a.max_run_usd is None:
            out.append(f"agent {a.id}: max_run_usd is required in pilot and prod")
        if live and a.data_class in {"confidential", "restricted"}:
            out.append(f"agent {a.id}: data_class {a.data_class} is not available until Phase 3")
        levels = a.levels
        if levels is None:
            if live:
                out.append(f"agent {a.id}: levels is required in pilot and prod")
            continue
        out += [
            f"agent {a.id}: levels names {x}, which is not in scope_allowed"
            for x in sorted(set(levels) - set(a.scope_allowed))
        ]
        if live:
            out += [
                f"agent {a.id}: levels must list {x} (every scope_allowed action)"
                for x in sorted(set(a.scope_allowed) - set(levels))
            ]
        for action, level in levels.items():
            contract = reg.contracts.get(action)
            if level == "act":
                out.append(f"agent {a.id}: level act for {action} arrives in Phase 4")
            if level != "suggest" or contract is None:
                continue
            if live:
                out.append(f"agent {a.id}: suggest for {action} cannot load before K6 and K8")
            if contract.executor.kind == "none":
                out.append(f"agent {a.id}: {action} is a none contract and can never be suggest")
            if effective_class(contract, a.data_class) == "sign_off":
                out.append(f"agent {a.id}: suggest for sign_off action {action} arrives in Phase 3")
        if (
            a.tools_allowed
            and "suggest" in levels.values()
            and not replay_records.has_green_record(reg, a.id)
        ):
            out.append(
                f"agent {a.id}: a tooled agent at suggest needs a green replay record "
                f"({replay_records.FILE}) for its current config hash"
            )
    return out
