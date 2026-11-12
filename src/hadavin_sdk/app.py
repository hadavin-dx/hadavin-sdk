"""App wiring: builds every module from one client config and connects runtime, approvals and executor.

This is the only place that hands the secret provider to the executor; runtime gets bound callables.
"""

from __future__ import annotations

import logging
import re
import ssl
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

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
from hadavin_sdk.backends.table import VaultConnection
from hadavin_sdk.config import (
    EXECUTOR_TIMEOUT_RULE,
    Backends,
    Config,
    ConfigError,
    confined,
    executor_timeout_ok,
    load_config,
)
from hadavin_sdk.errors import read_configured, shown_name
from hadavin_sdk.guard.injection import Detector, combine
from hadavin_sdk.limits import Limits
from hadavin_sdk.llm.protocol import LLM
from hadavin_sdk.models import now
from hadavin_sdk.registry import Registry, load_registry
from hadavin_sdk.runtime import evidence
from hadavin_sdk.runtime.agent_loop import Hooks, Runtime
from hadavin_sdk.safe_url import safe_urlsplit
from hadavin_sdk.sources import Source
from hadavin_sdk.sources.kinds import KINDS
from hadavin_sdk.stages import is_live
from hadavin_sdk.store import Store
from hadavin_sdk.store.protocol import missing_methods

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
    # The configured read sources (probed at start-up and again by the tick) and the store the purge step
    # runs under (its own database role when `purge_dsn_secret_name` is set; else the store above).
    sources: dict[str, Source] = field(default_factory=dict)
    disabled_sources: set[str] = field(default_factory=set)
    purge_store: Store | None = None


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
    clock: Callable[[], datetime] | None = None,
    timeout_s: float | None = None,
) -> App:
    """Build every backend from the config's table entries, in the design 4.2 order. Missing or shared secret
    names fail here, before the first run.

    `secrets=`, `channel=`, `detector=`, `llm=`, `clock=` and `timeout_s=` are for tests and are accepted in demo
    only: each replaces one configured part with an object the caller hands in (`secrets` replaces the configured
    provider for both the executor and the backends' own secrets). In pilot and prod (any stage that is not exactly
    demo) a build that is given one of them is refused with a ConfigError. An object counts as given when it is not
    None, so an object that is falsy is refused too. With several given, only the first in the order secrets,
    channel, detector, llm, clock, timeout_s is named. `hold_run_ids=` stays allowed in pilot and prod: it is a
    production hook (the caller's list of runs whose evidence the purge must keep), not a test object. In demo a
    given `timeout_s=` must be an int or float (not True or False) from `defaults.EXECUTOR_TIMEOUT_MIN_S` to
    `defaults.EXECUTOR_TIMEOUT_MAX_S` seconds (one rule, `config.executor_timeout_ok`, shared with the config field
    `executor_timeout_s`). `sources=` and
    `tools=` take a mapping (name to object); the code copies them with `dict()`, so a list of pairs also works in
    demo, but that is an accident of the copy and not part of the contract.

    Five checks run before that refusal in pilot and prod, in this order, each with its own message: the static
    Vault token (below), the missing restored-hash key, the missing purge DSN of a Postgres store, `sources=`, and
    `tools=`. The Vault check runs before any backend is built; the other four and the refusal of the six keywords
    run after the secrets backend is built and before any other backend.

    Static Vault token: a pilot or prod build refuses a backend whose settings are a Vault sign-in
    (`backends.table.VaultConnection`: the `vault` secrets kind, the `vault_transit` signer, any kind built on that
    class) with `auth: token`, written or left out (it is the default). This covers every process that calls
    `app.build`, which for the command line is `tick`. It does not cover the one-off commands that load the config
    without `build` (limits stop and reset, audit verify, gate, migrate, replay, score): a person may run those
    with a short-lived token of their own. Nothing checks how long that token lives, and a scheduled job that runs
    one of these commands with a static token in its environment is not refused either.

    Limit of these refusals: `build` refuses the six keywords above; `run_tick` refuses its `now=` and `steps=`
    and a `runtime.tick.STEPS` that lacks a built-in step or holds a name twice; a `TickContext` refuses a time
    handed to it (so a tick step called by hand cannot work with a time of the caller's choice), and outside demo a
    step takes only an object whose type is exactly `TickContext`.
    Any route that does not pass through them is not covered: constructing App, Runtime or Approvals directly (a
    hand-built `Approvals(clock=...)` among them), assigning attributes after build, a kind added to the table, a
    direct call of `backends.factory.make`, a leftover patch of `app.make` or `app.now`, a changed or patched
    `runtime.tick.STEPS` that holds every built-in name once (reordering, replacing a step's function under the same
    name, a huge interval on a built-in name), a rebound `runtime.tick._BUILT_IN`, a clock replaced after build, a
    context altered with `object.__setattr__`, built without its constructor, or given a wrapped app, and the
    methods below the tick that take a time or a cut-off date directly: the store's `purge_tool_calls(before)` and
    `purge_redaction_maps(before)` (called directly with a time far ahead on a pilot or prod app they delete
    everything, no refusal), and the time parameters
    of `Approvals.sweep(at=)` and `Approvals.resend_unsent(at=)`. The refusals stop a test object that reaches a
    pilot or prod process by ACCIDENT, not hostile code in the same process."""
    cfg = load_config(config_dir)
    reg = load_registry(cfg)
    b = cfg.backends
    given = [
        name
        for name, value in (
            ("secrets", secrets),
            ("channel", channel),
            ("detector", detector),
            ("llm", llm),
            ("clock", clock),
            ("timeout_s", timeout_s),
        )
        if value is not None
    ]
    live = is_live(cfg.environment)
    if live and (static := _static_vault_tokens(b)):
        # Before any backend is built: the token is never read from the environment of this process.
        raise ConfigError(f"environment {cfg.environment}: refused: {', '.join(static)}")
    if secrets is None:
        secrets = make("secrets", b.secrets)
    if live and not cfg.evidence.restored_hash_key_secret_name:
        raise ConfigError("evidence.restored_hash_key_secret_name is required in pilot and prod")
    if live and getattr(b.store, "kind", "") == "postgres" and not b.store.purge_dsn_secret_name:
        # Only the purge role may DELETE evidence; without its DSN the purge fails every tick and the
        # redaction maps (plaintext originals) are kept for ever.
        raise ConfigError("backends.store.purge_dsn_secret_name is required in pilot and prod")
    if sources is not None and live:
        # A source handed in as an object would replace a configured, probed one; live deployments use Config.sources.
        raise ConfigError("sources= is for tests; configure Config.sources in pilot and prod")
    if tools is not None and live:
        # Plain callables run with no egress allowlist, operation binding, deadline or schema: they are for replay
        # and tests. A pilot or prod deployment declares its tools in tools/<agent>.yaml.
        raise ConfigError(
            "tools= (plain callables) is for replay and tests; use tools/<agent>.yaml in pilot and prod"
        )
    if live and given:
        # An object handed in would replace a configured backend (or the clock, or the executor's timeout) in a live
        # process. Only the first given name is reported.
        name = given[0]
        fix = (
            "it is refused in pilot and prod"
            if name in ("clock", "timeout_s")
            else f"configure backends.{name} in pilot and prod"
        )
        raise ConfigError(f"{name}= is for tests; {fix}")
    if timeout_s is not None and not executor_timeout_ok(timeout_s):
        # 0 (and anything under a millisecond) would make every executor call fail at once. The config field
        # `executor_timeout_s` is checked by the same function, so the two routes cannot disagree.
        raise ConfigError(f"timeout_s= {EXECUTOR_TIMEOUT_RULE}")
    clock = now if clock is None else clock
    given_sources = {} if sources is None else dict(sources)
    # Only http contracts hold a client-system secret; pilot and prod have none (http is refused there).
    executor_names = {
        c.executor.secret_name for c in reg.contracts.values() if c.executor.kind == "http"
    }
    fetch_counter = tools_mod.FetchCounter(cfg.evidence.max_tool_calls_per_minute)
    disabled_sources: set[str] = (
        set()
    )  # sources switched off by a failed re-probe (tick `reprobe_sources`)
    built_sources = {
        name: _build_source(name, sc, cfg, secrets, disabled_sources, fetch_counter)
        for name, sc in cfg.sources.items()
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
        | ({cfg.evidence.restored_hash_key_secret_name} - {None})
    )
    platform_secrets.check(secrets, [s for _, s in b.entries()], executor_names, extra_secret_names)
    # Design 6.6: every read source has a passing scope probe or a client-signed inventory; else no start. The
    # configured sources (Config.sources) are probed here, so a deployed cluster is never read unprobed.
    if problems := sources_mod.scope_problems(
        {**built_sources, **given_sources}, cfg.scope_inventory
    ):
        raise ConfigError("; ".join(problems))
    if problems := _unprobed_tools(cfg, reg):
        raise ConfigError("; ".join(problems))
    attestable = set(cfg.sources) | {f"tool:{n}" for per in reg.tools.values() for n in per}
    for name in cfg.scope_inventory:
        _LOG.warning(
            "scope_inventory %s: operator-attested, format-checked only; its hash is not compared with the page",
            shown_name(name, attestable),
        )
    toolbox = _toolbox(
        cfg,
        reg,
        secrets,
        disabled_sources=disabled_sources,
        source_hosts={n: _source_host(sc) for n, sc in cfg.sources.items()},
        fetch_counter=fetch_counter,
    )
    signer = make("signer", b.signer, secrets)
    anchor = make("anchor", b.anchor, secrets)
    store = make("store", b.store, secrets)
    if lacking := missing_methods(store):
        raise ConfigError(
            f"the store backend lacks {', '.join(lacking)}: added to the Store protocol in this version (see CHANGELOG, Upgrade steps)"
        )
    purge_store = store
    if purge_name := getattr(b.store, "purge_dsn_secret_name", None):
        # The purge step deletes evidence; the runtime identity cannot. A second connection, a second role.
        purge_store = make(
            "store",
            b.store.model_copy(
                update={"dsn_secret_name": purge_name, "purge_dsn_secret_name": None}
            ),
            secrets,
        )
    audit = make("audit", b.audit, secrets, store=store, signer=signer, anchor=anchor)
    if llm is None:
        llm = make("llm", b.llm, secrets, routes=cfg.routes)
    summary_detector = detector
    if detector is None:
        members = [make("detector", d, secrets, llm=llm) for d in b.detector]
        detector = combine(members)
        # The approval summary screen has no agent to charge, so it runs the unmetered members only; the judge
        # screens the document and tool output, where untrusted text enters (config refuses a judge alone).
        summary_detector = combine([m for m in members if m.backend != "llm_judge"])
    if channel is None:
        channel = make("channel", b.channel, secrets, store=store)
    limits = Limits(store, audit, reg)
    if timeout_s is None:
        timeout_s = cfg.executor_timeout_s
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

    restored_key: bytes | None = None
    if key_name := cfg.evidence.restored_hash_key_secret_name:
        restored_key = _restored_key(secrets, key_name)
    elif live:
        raise ConfigError("evidence.restored_hash_key_secret_name is required in pilot and prod")
    hooks = Hooks(
        request_approval=request_approval,
        execute=executor.execute if executor else None,
        verify=executor.verify if executor else None,
        rollback=executor.rollback if executor else None,
        post_card=post_card,
        tools={} if tools is None else dict(tools),
        toolbox=toolbox,
        validate_proposal=evidence.make_validator(
            store,
            suffixes={
                t.name: t.generated_suffix
                for per in reg.tools.values()
                for t in per.values()
                if t.generated_suffix
            },
            case_insensitive_targets=cfg.evidence.case_insensitive_targets,
        ),
        hold_run_ids=hold_run_ids,
        restored_key=restored_key,
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
    return App(
        cfg,
        reg,
        store,
        audit,
        limits,
        executor,
        approvals,
        runtime,
        sources={**built_sources, **given_sources},
        disabled_sources=disabled_sources,
        purge_store=purge_store,
    )


def _static_vault_tokens(backends: Backends) -> list[str]:
    """The backends that sign in to Vault with a static token, one refusal item each. `auth: token` is the default,
    so a config that leaves `auth` out is found too. The match is by settings type, not by kind name, so a new kind
    built on `VaultConnection` is covered. `auth: approle` is allowed: its secret id is also read from the
    environment, so set a short secret id lifetime on the Vault side; this code cannot check that."""
    return [
        f"{c}: {s.kind} auth token (the default; set auth: kubernetes (recommended) or auth: approle)"
        for c, s in backends.entries()
        if isinstance(s, VaultConnection) and s.auth == "token"
    ]


def _own_secrets(secrets: SecretProvider, spec: tools_mod.ToolSpec) -> Callable[[str], str]:
    """A secret reader limited to the tool's own `secret_names`: a tool is never handed the global provider."""
    allowed = frozenset(spec.secret_names)

    def read(name: str) -> str:
        if name not in allowed:
            raise PermissionError("that secret is not one of this tool's own secrets")
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
        read_configured(confined(cfg.root, ca_file), "the CA file (ca_file)")
        if ca_file
        else secrets.get(ca_secret_name or "")
    )
    if not pem or not pem.strip():
        # A CA that was asked for and is empty must not fall back to the system CAs.
        raise ConfigError("the CA bundle is empty")
    try:
        return ssl.create_default_context(cadata=pem)
    except ssl.SSLError:
        raise ConfigError("the CA bundle holds no valid PEM certificate") from None


def _build_source(
    name: str,
    sc,
    cfg: Config,
    secrets: SecretProvider,
    disabled: set[str] | None = None,
    fetch_counter: tools_mod.FetchCounter | None = None,
) -> Source:
    """Build a configured source: its settings validated, its fetch bound to the endpoint's host and port, the
    operation bindings of its kind, its CA, and its credential from the secrets kind."""
    kind = KINDS[sc.kind]
    settings = kind.settings(**sc.settings)
    parts = safe_urlsplit(kind.endpoint(settings))
    plain = parts.scheme == "http"
    if plain and sc.token_secret_name:
        raise ConfigError(
            f"source {shown_name(name, cfg.sources)}: a bearer token never travels over plain http; use https"
        )
    if why := tools_mod.forbidden_host((parts.hostname or "").lower()):
        raise ConfigError(
            f"source {shown_name(name, cfg.sources)}: the host of its endpoint is {why}"
        )  # as a tool manifest host
    spec = tools_mod.ToolSpec(
        name="source_" + re.sub(r"[^a-z0-9]", "_", name.lower())[:30],
        function="source:read",
        description=f"read source {shown_name(name, cfg.sources)}",
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
        if disabled and name in disabled and not sources_mod.PROBING.get():
            raise tools_mod.ToolRefused(
                f"source {shown_name(name, cfg.sources)} is switched off: its scope probe failed"
            )
        ctx = tools_mod.ToolContext(
            spec,
            cfg.tool_timeout_s,
            bindings=dict(kind.operations),
            fetch_ceiling=cfg.evidence.fetch_ceiling_bytes,
            https_ports=cfg.evidence.https_ports,
            cluster_ports=cfg.evidence.cluster_ports,
            cluster_suffixes=cfg.evidence.cluster_suffixes,
            scrub=cfg.evidence.scrub,
            ssl_context=ssl_ctx,
            on_fetch=fetch_counter.note if fetch_counter else None,
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
    return (safe_urlsplit(kind.endpoint(kind.settings(**sc.settings))).hostname or "").lower()


def _unprobed_tools(cfg: Config, reg: Registry) -> list[str]:
    """Design 6.6 for tools: a tool that holds a credential, or reads a configured kind of source (an operation
    with that kind's prefix), needs a probe or an operator-attested inventory entry. It is covered by

    * a scope_inventory entry `tool:<name>` (operator-attested, format-checked, not verified), or
    * a probed source it is explicitly mapped to (`options.source`) AND whose credential it uses: the tool's own
      `secret_names` must be nothing but that source's token secret (a probe vouches for one credential), and
      the source's host must be one of the tool's `hosts` (a probe vouches for one endpoint).

    A tool that merely shares a host with a probed source is NOT covered: it may hold a different credential."""
    out = []
    known = {t.name for per in reg.tools.values() for t in per.values()}
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
                f"tool {shown_name(t.name, known)}: reads a source or holds a credential that no probe vouches for: map it to a "
                f"configured source with options.source (using that source's token secret) or attest it with "
                f"scope_inventory 'tool:{shown_name(t.name, known)}' (design 6.6)"
            )
    return sorted(set(out))


MIN_RESTORED_KEY_BYTES = 16


def _restored_key(secrets: SecretProvider, name: str) -> bytes:
    """The key that makes the audit's hash of the restored inputs unguessable. An empty or short one would put
    brute-forceable plain hashes of IP addresses and short names back into the audit."""
    key = secrets.get(name).encode("utf-8")
    if len(key) < MIN_RESTORED_KEY_BYTES:
        raise ConfigError(f"the restored-hash key must be at least {MIN_RESTORED_KEY_BYTES} bytes")
    return key


def _switched_off(disabled: set[str] | None, source_hosts: dict[str, str]):
    """Why a tool may not run: a source it reads (named in `options.source`, or on one of its hosts) failed its
    scope re-probe and was switched off. The set is the app's own and the tick edits it."""

    def why(spec: tools_mod.ToolSpec) -> str | None:
        if not disabled:
            return None
        named = str(spec.options.get("source", ""))
        if named in disabled:
            return f"source {shown_name(named, disabled)} is switched off: its scope probe failed"
        if {source_hosts[n] for n in disabled if n in source_hosts} & set(spec.hosts):
            return "a source this tool reads is switched off: its scope probe failed"
        return None

    return why


def _toolbox(
    cfg: Config,
    reg: Registry,
    secrets: SecretProvider,
    disabled_sources: set[str] | None = None,
    source_hosts: dict[str, str] | None = None,
    fetch_counter: tools_mod.FetchCounter | None = None,
) -> tools_mod.ToolBox | None:
    """Resolve every manifest tool's function (from `tool_modules` only) and give each tool a secret reader
    limited to its own names and, if its manifest names a CA, a TLS context that trusts only that CA."""
    specs: dict[str, tools_mod.ToolSpec] = {}
    for per_agent in reg.tools.values():
        for name, spec in per_agent.items():
            if specs.setdefault(name, spec) != spec:
                raise ConfigError(
                    f"tool {shown_name(name, specs)} is defined differently for two agents"
                )
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
                    shown_name(agent_id, reg.agents),
                    shown_name(action, reg.contracts),
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
        scrub=ev.scrub,
        stored_kinds=frozenset(ev.stored_kinds),
        max_abandoned=ev.max_abandoned_tool_threads,
        max_concurrent=ev.max_concurrent_tool_calls,
        max_per_minute=ev.max_tool_calls_per_minute,
        fetch_counter=fetch_counter,
        disabled=_switched_off(disabled_sources, source_hosts or {}),
        ssl_context_for=lambda spec: contexts.get(spec.name),
    )
