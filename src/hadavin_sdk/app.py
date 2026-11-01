"""App wiring: builds every module from one client config and connects runtime, approvals and executor.

This is the only place that hands the secret provider to the executor; runtime gets bound callables.
"""

from __future__ import annotations

import logging
import re
import ssl
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

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
from hadavin_sdk.backends import platform_secrets
from hadavin_sdk.backends.factory import make
from hadavin_sdk.config import Config, ConfigError, confined, load_config
from hadavin_sdk.guard.injection import Detector, combine
from hadavin_sdk.limits import Limits
from hadavin_sdk.llm.protocol import LLM
from hadavin_sdk.models import now
from hadavin_sdk.registry import Registry, load_registry
from hadavin_sdk.runtime import evidence
from hadavin_sdk.runtime.agent_loop import Hooks, Runtime
from hadavin_sdk.sources import Source
from hadavin_sdk.sources.kinds import KINDS
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
    hold_run_ids: Callable[[], set[str] | frozenset[str]] | None = None,
    clock: Callable[[], datetime] = now,
    timeout_s: float | None = None,
) -> App:
    """Build every backend from the config's table entries, in the design 4.2 order. The keyword overrides
    replace one configured backend (tests); `secrets` replaces the configured provider for both the executor
    and the backends' own secrets. Missing or shared secret names fail here, before the first run."""
    cfg = load_config(config_dir)
    reg = load_registry(cfg)
    b = cfg.backends
    secrets = secrets or make("secrets", b.secrets)
    live = cfg.environment in deferred.LIVE
    if sources and live:
        # A source handed in as an object would replace a configured, probed one; live deployments use Config.sources.
        raise ConfigError("sources= is for tests; configure Config.sources in pilot and prod")
    if tools and live:
        # Plain callables run with no egress allowlist, operation binding, deadline or schema: they are for replay
        # and tests. A pilot or prod deployment declares its tools in tools/<agent>.yaml.
        raise ConfigError(
            "tools= (plain callables) is for replay and tests; use tools/<agent>.yaml in pilot and prod"
        )
    # Only http contracts hold a client-system secret; pilot and prod have none (http is refused there).
    executor_names = {
        c.executor.secret_name for c in reg.contracts.values() if c.executor.kind == "http"
    }
    built_sources = {
        name: _build_source(name, sc, cfg, secrets) for name, sc in cfg.sources.items()
    }
    extra_secret_names = (
        {n for specs in reg.tools.values() for t in specs.values() for n in t.secret_names}
        | {
            t.ca_secret_name
            for specs in reg.tools.values()
            for t in specs.values()
            if t.ca_secret_name
        }
        | {sc.token_secret_name for sc in cfg.sources.values() if sc.token_secret_name}
    )
    platform_secrets.check(secrets, [s for _, s in b.entries()], executor_names, extra_secret_names)
    # Design 6.6: every read source has a passing scope probe or a client-signed inventory; else no start. The
    # configured sources (Config.sources) are probed here, so a deployed cluster is never read unprobed.
    if problems := sources_mod.scope_problems(
        {**built_sources, **(sources or {})}, cfg.scope_inventory
    ):
        raise ConfigError("; ".join(problems))
    if problems := _unprobed_tools(cfg, reg):
        raise ConfigError("; ".join(problems))
    for name in cfg.scope_inventory:
        _LOG.warning(
            "scope_inventory %s: operator-attested, format-checked only; its hash is not compared with the page",
            name,
        )
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
    executor = (
        None if live else Executor(reg, secrets, timeout_s=timeout_s or cfg.executor_timeout_s)
    )
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
        hold_run_ids=hold_run_ids,
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


def _own_secrets(secrets: SecretProvider, spec: tools_mod.ToolSpec) -> Callable[[str], str]:
    """A secret reader limited to the tool's own `secret_names`: a tool is never handed the global provider."""
    allowed = frozenset(spec.secret_names)

    def read(name: str) -> str:
        if name not in allowed:
            raise PermissionError(f"secret {name!r} is not one of tool {spec.name}'s secrets")
        return secrets.get(name)

    return read


def _tls_context(
    cfg: Config, secrets: SecretProvider, ca_file: str | None, ca_secret_name: str | None
) -> ssl.SSLContext | None:
    """The CA bundle that signs a private endpoint (a cluster API server): from a file under the config folder, or
    from a named secret. None: the system CAs. Either way verification stays on."""
    if not (ca_file or ca_secret_name):
        return None
    pem = (
        confined(cfg.root, ca_file).read_text(encoding="utf-8")
        if ca_file
        else secrets.get(ca_secret_name or "")
    )
    if not pem or not pem.strip():
        # A CA that was asked for and is empty must not fall back to the system CAs.
        raise ConfigError(f"the CA {ca_file or ca_secret_name!r} is empty")
    try:
        return ssl.create_default_context(cadata=pem)
    except ssl.SSLError:
        raise ConfigError(
            f"the CA {ca_file or ca_secret_name!r} holds no valid PEM certificate"
        ) from None


def _build_source(name: str, sc, cfg: Config, secrets: SecretProvider) -> Source:
    """Build a configured source: its settings validated, its fetch bound to the endpoint's host and port, the
    operation bindings of its kind, its CA, and its credential from the secrets kind."""
    kind = KINDS[sc.kind]
    settings = kind.settings(**sc.settings)
    parts = urlsplit(kind.endpoint(settings))
    plain = parts.scheme == "http"
    if why := tools_mod.forbidden_host((parts.hostname or "").lower()):
        raise ConfigError(
            f"source {name}: host {parts.hostname!r} is {why}"
        )  # as a tool manifest host
    spec = tools_mod.ToolSpec(
        name="source_" + re.sub(r"[^a-z0-9]", "_", name.lower())[:30],
        function="source:read",
        description=f"read source {name}",
        input_schema={"type": "object"},
        side_effect="none",
        operations=tuple(kind.operations),
        hosts=((parts.hostname or "").lower(),),
        ports=(parts.port or (80 if plain else 443),),
        cluster_http=plain,
    )
    ca = str(sc.ca_file) if sc.ca_file else None
    ssl_ctx = _tls_context(cfg, secrets, ca, None)

    def fetch(method, url, *, operation, body=None, headers=None, max_bytes=None):
        ctx = tools_mod.ToolContext(
            spec,
            cfg.tool_timeout_s,
            bindings=dict(kind.operations),
            fetch_ceiling=cfg.evidence.fetch_ceiling_bytes,
            https_ports=cfg.evidence.https_ports,
            cluster_ports=cfg.evidence.cluster_ports,
            cluster_suffixes=cfg.evidence.cluster_suffixes,
            ssl_context=ssl_ctx,
        )
        sent = dict(headers or {})
        if sc.token_secret_name:
            sent["Authorization"] = "Bearer " + secrets.get(sc.token_secret_name)
        return ctx.fetch(
            method, url, operation=operation, headers=sent, body=body, max_bytes=max_bytes
        )

    return kind.build(settings, fetch)


def _source_host(sc) -> str:
    kind = KINDS[sc.kind]
    return (urlsplit(kind.endpoint(kind.settings(**sc.settings))).hostname or "").lower()


def _unprobed_tools(cfg: Config, reg: Registry) -> list[str]:
    """Design 6.6 for tools: a tool that holds a credential, or reads a configured kind of source (an operation
    with that kind's prefix), needs a probe or an operator-attested inventory entry. It is covered by

    * a scope_inventory entry `tool:<name>` (operator-attested, format-checked, not verified), or
    * a probed source it is explicitly mapped to (`options.source`) AND whose credential it uses: the tool's own
      `secret_names` must be nothing but that source's token secret (a probe vouches for one credential), and
      the source's host must be one of the tool's `hosts` (a probe vouches for one endpoint).

    A tool that merely shares a host with a probed source is NOT covered: it may hold a different credential."""
    out = []
    for per_agent in reg.tools.values():
        for t in per_agent.values():
            reads_source = any(
                op.startswith(k.operation_prefix) for op in t.operations for k in KINDS.values()
            )
            if not (t.secret_names or reads_source) or f"tool:{t.name}" in cfg.scope_inventory:
                continue
            source = cfg.sources.get(str(t.options.get("source", "")))
            if (
                source is not None
                and source.token_secret_name
                and set(t.secret_names) <= {source.token_secret_name}
                and _source_host(source) in t.hosts
            ):
                continue
            out.append(
                f"tool {t.name}: reads a source or holds a credential that no probe vouches for: map it to a "
                f"configured source with options.source (using that source's token secret) or attest it with "
                f"scope_inventory 'tool:{t.name}' (design 6.6)"
            )
    return sorted(set(out))


def _toolbox(cfg: Config, reg: Registry, secrets: SecretProvider) -> tools_mod.ToolBox | None:
    """Resolve every manifest tool's function (from `tool_modules` only) and give each tool a secret reader
    limited to its own names and, if its manifest names a CA, a TLS context that trusts only that CA."""
    specs: dict[str, tools_mod.ToolSpec] = {}
    for per_agent in reg.tools.values():
        for name, spec in per_agent.items():
            if specs.setdefault(name, spec) != spec:
                raise ConfigError(f"tool {name} is defined differently for two agents")
    if not specs:
        return None
    fns = {
        n: tools_mod.resolve_function(spec, cfg.tool_modules, cfg.tool_module_hashes)
        for n, spec in specs.items()
    }
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
    contexts = {
        n: _tls_context(cfg, secrets, spec.ca_file, spec.ca_secret_name)
        for n, spec in specs.items()
    }
    ev = cfg.evidence
    return tools_mod.ToolBox(
        specs,
        fns,
        timeout_s=cfg.tool_timeout_s,
        secret_resolver_for=lambda spec: _own_secrets(secrets, spec),
        arg_errors=schema_errors,
        bindings=tools_mod.read_operations(cfg.tool_modules, cfg.tool_module_hashes),
        fetch_ceiling=ev.fetch_ceiling_bytes,
        https_ports=ev.https_ports,
        cluster_ports=ev.cluster_ports,
        cluster_suffixes=ev.cluster_suffixes,
        stored_kinds=frozenset(ev.stored_kinds),
        max_abandoned=ev.max_abandoned_tool_threads,
        ssl_context_for=lambda spec: contexts.get(spec.name),
    )
