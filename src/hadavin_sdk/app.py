"""App wiring: builds every module from one client config and connects runtime, approvals and executor.

This is the only place that hands the secret provider to the executor; runtime gets bound callables.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from hadavin_sdk import deferred
from hadavin_sdk import sources as sources_mod
from hadavin_sdk import tools as tools_mod
from hadavin_sdk.actions.contract import schema_errors
from hadavin_sdk.actions.executor import Executor
from hadavin_sdk.actions.secrets import SecretProvider
from hadavin_sdk.approvals import Approvals, Channel
from hadavin_sdk.approvals.cards import Card, Delivery
from hadavin_sdk.approvals.requests import summary
from hadavin_sdk.audit import AuditSink
from hadavin_sdk.backends import make, platform_secrets
from hadavin_sdk.config import Config, ConfigError, load_config
from hadavin_sdk.guard.injection import Detector, combine
from hadavin_sdk.limits import Limits
from hadavin_sdk.llm.protocol import LLM
from hadavin_sdk.models import now
from hadavin_sdk.registry import Registry, load_registry
from hadavin_sdk.runtime import evidence
from hadavin_sdk.runtime.agent_loop import Hooks, Runtime
from hadavin_sdk.sources import Source
from hadavin_sdk.store import Store

_LOG = logging.getLogger("hadavin_sdk.app")


@dataclass
class App:
    config: Config
    registry: Registry
    store: Store
    audit: AuditSink
    limits: Limits
    executor: Executor | None  # None in pilot and prod: Hadavin executes nothing there
    approvals: Approvals
    runtime: Runtime


def build(
    config_dir: Path | None,
    agents: list[str],
    *,
    secrets: SecretProvider | None = None,
    channel: Channel | None = None,
    detector: Detector | None = None,
    llm: LLM | None = None,
    tools: dict[str, Callable[[dict], str]] | None = None,
    sources: Mapping[str, Source] | None = None,
    clock: Callable[[], datetime] = now,
    timeout_s: float = 10.0,
) -> App:
    """Build every backend from the config's table entries, in the design 4.2 order. The keyword overrides
    replace one configured backend (tests); `secrets` replaces the configured provider for both the executor
    and the backends' own secrets. Missing or shared secret names fail here, before the first run."""
    cfg = load_config(config_dir)
    reg = load_registry(cfg)
    b = cfg.backends
    secrets = secrets or make("secrets", b.secrets)
    live = cfg.environment in deferred.LIVE
    # Only http contracts hold a client-system secret; pilot and prod have none (http is refused there).
    executor_names = {
        c.executor.secret_name for c in reg.contracts.values() if c.executor.kind == "http"
    }
    tool_secret_names = {
        n for specs in reg.tools.values() for t in specs.values() for n in t.secret_names
    }
    platform_secrets.check(secrets, [s for _, s in b.entries()], executor_names, tool_secret_names)
    # Design 6.6: every read source has a passing scope probe or a client-signed inventory; else no start.
    if problems := sources_mod.scope_problems(sources or {}, cfg.scope_inventory):
        raise ConfigError("; ".join(problems))
    toolbox = _toolbox(cfg, reg, secrets)
    signer = make("signer", b.signer, secrets)
    anchor = make("anchor", b.anchor, secrets)
    store = make("store", b.store, secrets)
    audit = make("audit", b.audit, secrets, store=store, signer=signer, anchor=anchor)
    llm = llm or make("llm", b.llm, secrets, routes=cfg.routes)
    summary_detector = detector
    if detector is None:
        members = [make("detector", d, secrets, llm=llm) for d in b.detector]
        detector = combine(members)
        # The approval summary screen has no agent to charge, so it runs the unmetered members only; the judge
        # screens the document and tool output, where untrusted text enters (config refuses a judge alone).
        summary_detector = combine([m for m in members if m.backend != "llm_judge"])
    channel = channel or make("channel", b.channel, secrets, store=store)
    limits = Limits(store, audit, reg)
    executor = None if live else Executor(reg, secrets, timeout_s=timeout_s)
    holder: dict[str, Runtime] = {}
    approvals = Approvals(
        store,
        audit,
        reg,
        channel,
        lambda run_id, status, d: holder["rt"].on_decided(run_id, status, d),
        clock,
        summary_detector,
    )

    def post_card(card: Card) -> Delivery:
        if len(card.text) > channel.max_card_chars:
            return Delivery(ok=False, reason="card_too_long")
        try:
            return channel.post_card(card)
        except Exception as exc:  # noqa: BLE001 - a broken channel is an undelivered card, never a crash
            return Delivery(ok=False, reason=type(exc).__name__)

    def request_approval(plan, decision, requested_by) -> Delivery:
        if len(summary(plan, summary_detector)) > channel.max_card_chars:
            return Delivery(ok=False, reason="card_too_long")
        # A failed send is NOT terminal: the request stays PENDING and tick resends it
        # (tests/test_p7_tick.py::test_failed_send_is_resent_by_tick), so a saved request is delivered-or-retrying.
        req = approvals.request(plan, decision, requested_by)
        return Delivery(ok=True, ref=req.channel_ref)

    hooks = Hooks(
        request_approval=request_approval,
        execute=executor.execute if executor else None,
        verify=executor.verify if executor else None,
        rollback=executor.rollback if executor else None,
        post_card=post_card,
        tools=dict(tools or {}),
        toolbox=toolbox,
        validate_proposal=evidence.make_validator(store),
    )
    runtime = Runtime(
        reg,
        store,
        audit,
        llm,
        detector,
        limits,
        agents,
        hooks,
    )
    holder["rt"] = runtime
    return App(cfg, reg, store, audit, limits, executor, approvals, runtime)


def _toolbox(cfg: Config, reg: Registry, secrets: SecretProvider) -> tools_mod.ToolBox | None:
    """Resolve every manifest tool's function (from `tool_modules` only) and bind the secret resolver. The
    resolver reads any name; `ToolContext.secret` lets a tool ask only for the names in its own manifest."""
    specs: dict[str, tools_mod.ToolSpec] = {}
    for per_agent in reg.tools.values():
        for name, spec in per_agent.items():
            if specs.setdefault(name, spec) != spec:
                raise ConfigError(f"tool {name} is defined differently for two agents")
    if not specs:
        return None
    fns = {n: tools_mod.resolve_function(spec, cfg.tool_modules) for n, spec in specs.items()}
    for agent_id, agent in reg.agents.items():
        if not agent.tools_allowed:
            continue
        for action in agent.scope_allowed:
            if not evidence.identifier_inputs(reg.contracts[action]):
                _LOG.info(
                    "agent %s, action %s: no input is flagged identifier, so grounding is skipped",
                    agent_id,
                    action,
                )
    return tools_mod.ToolBox(
        specs,
        fns,
        timeout_s=cfg.tool_timeout_s,
        secret_resolver=secrets.get,
        arg_errors=schema_errors,
    )
