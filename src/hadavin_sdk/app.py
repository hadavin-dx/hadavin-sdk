"""App wiring: builds every module from one client config and connects runtime, approvals and executor.

This is the only place that hands the secret provider to the executor; runtime gets bound callables.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from hadavin_sdk import deferred
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
from hadavin_sdk.measure import BASELINE_FILE, Measure, load_baseline
from hadavin_sdk.models import now
from hadavin_sdk.registry import Registry, load_registry
from hadavin_sdk.runtime.agent_loop import Hooks, Runtime
from hadavin_sdk.store import Store


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
    measure: Measure | None = None  # K6: labels, demotion, promotion evidence, the weekly report


def build(
    config_dir: Path | None,
    agents: list[str],
    *,
    secrets: SecretProvider | None = None,
    channel: Channel | None = None,
    detector: Detector | None = None,
    llm: LLM | None = None,
    tools: dict[str, Callable[[dict], str]] | None = None,
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
    platform_secrets.check(secrets, [s for _, s in b.entries()], executor_names)
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

    # K6. The ceiling is required in pilot and prod ("the pilot tooling refuses to start without it"); in dev it is
    # used when baseline.yaml exists and the report is simply off when it does not.
    ceiling = load_baseline(cfg.root) if live or (cfg.root / BASELINE_FILE).is_file() else None
    measure = Measure(store, audit, reg, channel, ceiling=ceiling, clock=clock, limits=limits)
    approvals.measure = measure  # the receiver on these approvals also takes label and clear clicks
    if live:
        if not measure.line_owners():  # nobody could clear a demotion or be told about a breach
            raise ConfigError(
                "principals.yaml: in pilot and prod at least one person must hold the admin right clear_override"
            )
        if problems := measure.promotion_store_problems():
            raise ConfigError("promotion evidence: " + "; ".join(problems))

    hooks = Hooks(
        request_approval=request_approval,
        execute=executor.execute if executor else None,
        verify=executor.verify if executor else None,
        rollback=executor.rollback if executor else None,
        post_card=post_card,
        tools=dict(tools or {}),
        level_override=measure.level_override,
    )
    # K5-core adds `Hooks.hold_run_ids` (its purge skips the runs this returns). Wired when the field exists, so
    # K6 works before and after K5 without either having to edit the other's Hooks line.
    if hasattr(hooks, "hold_run_ids"):
        hooks.hold_run_ids = measure.hold_run_ids
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
    return App(cfg, reg, store, audit, limits, executor, approvals, runtime, measure)
