"""App wiring: builds every module from one client config and connects runtime, approvals and executor.

This is the only place that hands the secret provider to the executor; runtime gets bound callables.
"""

from __future__ import annotations

import enum
import logging
import numbers
import re
import ssl
import uuid
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

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
from hadavin_sdk.mode_banner import (
    DEFAULT_WORDS,
    OVERRIDES,
    BannerWords,
    _services_in,
    banner_or_unconfirmed,
    not_confirmed_banner,
)
from hadavin_sdk.models import now
from hadavin_sdk.registry import Registry, load_registry
from hadavin_sdk.runtime import evidence
from hadavin_sdk.runtime.agent_loop import Hooks, Runtime
from hadavin_sdk.sources import Source
from hadavin_sdk.sources.kinds import KINDS, source_endpoint
from hadavin_sdk.stages import is_live
from hadavin_sdk.store import Store
from hadavin_sdk.store.protocol import missing_methods

_LOG = logging.getLogger("hadavin_sdk.app")

# Attribute values that are data, not a connection: a change of one (a counter, a time, a list refilled in place) is not a new
# part (see `App._connected_parts`). A client, a session, a callable or any other object is not data.
_PLAIN_DATA = (
    str,
    bytes,
    bytearray,
    numbers.Number,
    type(None),
    list,
    dict,
    set,
    frozenset,
    tuple,
    deque,
    date,
    timedelta,
    uuid.UUID,
    enum.Enum,
)
_PLAIN = object()  # stands for "plain data" in the list of references
# What `_sealed` holds when `build` could not read the app (a config the banner cannot read, a named container missing): the
# banner of that app is the unconfirmed one, and `build` itself goes on (the banner never decides whether the app starts).
_UNREADABLE: tuple = ("the app could not be read when it was built",)
# The errors that reading an app for the seal can raise (a shape the banner cannot read: a tool spec without hosts, a backend
# entry without a kind, a named container that is missing or not a mapping, an attribute that is not there).
_SEAL_ERRORS = (TypeError, ValueError, AttributeError, LookupError, RuntimeError)


class _Given(tuple):
    """The names of the `build` overrides that were given, as `_given_overrides` computed them. `_seal` takes nothing else: a
    plain tuple, such as `()`, is refused, so a stray call cannot seal an app with an answer of its own. Python has no
    private methods: code that deliberately calls `_given_overrides` itself can still make one, and that is not supported."""

    __slots__ = ()


_WARNED: set[tuple[str, str]] = set()


def _warn_once(what: str, exc: Exception) -> None:
    """Say at warning level, once per reason and exception type in this process, that the banner of an app fell back to the
    unconfirmed one because of an error (not the name of a tampered app: the type only, never the message, which could hold
    a value). A typo in this module would otherwise turn every app permanently unconfirmed with nothing in the log."""
    key = (what, type(exc).__name__)
    if key not in _WARNED:
        _WARNED.add(key)
        _LOG.warning("mode banner: %s (%s): showing the not-confirmed banner", what, key[1])


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
    # The `build` overrides that were given (names only, in the fixed order of `mode_banner.OVERRIDES`): objects the caller
    # made replace what the config names, and the mode banner cannot judge them (it says so and claims nothing made-up).
    # None means "not recorded" (an App made by hand, not by `build`): the banner is then the unconfirmed one.
    overridden: tuple[str, ...] | None = None
    # What `build` saw when it recorded `overridden` (`_connected_parts`): the names, the REFERENCES
    # of the connected parts (compared with `is`, never by `id()`, so a freed object whose number is
    # reused cannot pass as the old one: the sealed tuple keeps every part alive, so no part can be
    # freed and its number reused while the seal exists), the lists of services the banner reads
    # from the config and the tool manifests (`_services_in`, compared by value: it is the very
    # value the banner is made from) and the stage text `config.environment` (compared by value). An
    # App that was copied with `dataclasses.replace` (this field is not an init argument) or had a
    # connected part replaced after it was built, or had an entry of the config, the registry or the
    # toolbox removed or swapped, no longer matches, and its banner is the unconfirmed one. A
    # `copy.copy` of an App keeps the same parts, so it stays known (it connects to exactly what the
    # original connects to). A `copy.deepcopy` of an App is REFUSED (`__deepcopy__`): a built App
    # holds locks and connections that cannot be copied (the standard library raises there already),
    # and a refusal that holds for every App is one rule, not a result that depends on what the copy
    # happens to hold. Chosen over a frozen App because callers set fields (tests, the tick) and a
    # frozen App would break them; the fingerprint is the smaller change. If `build` could not read
    # the app, the field holds `_UNREADABLE` (the banner is then the unconfirmed one and `build`
    # still returns the app).
    _sealed: tuple | None = field(default=None, init=False, repr=False, compare=False)

    def _connected_parts(self) -> tuple:
        """The references of every part that can connect the app to something, as (label, reference)
        pairs. Read by the core: every field of the App except the four names skipped below
        (`overridden` and `_sealed` are the record itself, `disabled_sources` is a set the tick
        fills, `sources` is a dict listed entry by entry); every field of the hooks (`Hooks`, each
        callable and each entry of its `tools`); the runtime's registry, store, audit, llm, detector
        and limits; the channel of the approvals; and for each of those parts and each source its
        `__dict__`: the NAMES of its attributes, and the reference of each attribute value that is
        not plain data (text, numbers, lists, dicts, times: a counter that changes during a run must
        not read as a new part). Nothing deeper is read, except the entries of the containers named
        at the end of the method. Any error here propagates (a `TypeError` that names the container
        when a named container is missing or is not a mapping, or when the toolbox has no attribute
        dictionary): `_seal` seals the app as unreadable and `mode_banner` turns it into the
        unconfirmed banner."""
        out: list[tuple[str, object]] = []

        def add(label: str, obj: object) -> None:
            out.append((label, obj))
            attrs = getattr(obj, "__dict__", None)
            if isinstance(attrs, dict):
                for key, value in list(attrs.items()):
                    out.append(
                        (f"{label}.{key}", _PLAIN if isinstance(value, _PLAIN_DATA) else value)
                    )

        for f in fields(self):
            if f.name in ("overridden", "_sealed", "disabled_sources", "sources"):
                continue
            add(f.name, getattr(self, f.name, None))
        own = {f.name for f in fields(self)}
        for key, value in list(
            vars(self).items()
        ):  # an attribute set on the object that is not a field
            if key not in own:
                add(f"extra.{key}", value)
        for key, source in list(dict(self.sources).items()):
            add(f"sources[{key!r}]", source)
        rt = self.runtime
        for name in ("registry", "store", "audit", "llm", "detector", "limits"):
            add(f"runtime.{name}", getattr(rt, name, None))
        hooks = getattr(rt, "hooks", None)
        add("runtime.hooks", hooks)
        if is_dataclass(hooks):
            for f in fields(hooks):
                value = getattr(hooks, f.name, None)
                if f.name == "tools":
                    out.append(
                        ("runtime.hooks.tools", _PLAIN)
                    )  # the dict itself: its entries are listed next
                    for key, tool in list(dict(value).items()):
                        add(f"runtime.hooks.tools[{key!r}]", tool)
                else:
                    add(f"runtime.hooks.{f.name}", value)
        add("approvals.channel", getattr(getattr(self, "approvals", None), "channel", None))

        # The entries of the few containers that decide where the app connects, one level down, each by reference: a mapping
        # of the config (`systems`, `sources`), of the registry (contracts, agents, principals, chains, and the tool
        # manifests of each agent) and of the toolbox (`specs`, and the functions it calls). They do not change after
        # `build`, so a removed, added or swapped entry is a change of what the app connects to. Containers that fill
        # during a run (counters, queues, caches) are NOT read.
        def members(label: str, container: object) -> None:
            # a named container that is missing or is not a mapping is an error that names it: it must not drop out of the
            # seal without a word (a renamed field of the registry or the toolbox would otherwise go unseen)
            if not isinstance(container, Mapping):
                raise TypeError(f"{label} is missing or is not a mapping in this app")
            for key, value in list(container.items()):
                out.append((f"{label}[{key!r}]", value))

        cfg = self.config
        for name in ("systems", "sources"):
            members(f"config.{name}", getattr(cfg, name, None))
        reg = self.registry
        for name in ("agents", "principals", "chains", "contracts"):
            members(f"registry.{name}", getattr(reg, name, None))
        tools = getattr(reg, "tools", None)
        members("registry.tools", tools)
        for agent, per_agent in list(tools.items()):
            members(f"registry.tools[{agent!r}]", per_agent)
        toolbox = getattr(hooks, "toolbox", None)
        if toolbox is not None:
            attrs = getattr(toolbox, "__dict__", None)
            if not isinstance(attrs, dict):
                raise TypeError("the toolbox of the hooks has no attribute dictionary to read")
            for name in ("specs", "_fns"):
                members(f"toolbox.{name}", attrs.get(name))
        return tuple(out)

    def _banner_services(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """The two lists of services the banner is made from (`_services_in` of this config and these tool manifests). Read at
        `_seal` (an error there seals the app as unreadable: the unconfirmed banner, `build` goes on) and again at every banner
        (an error there is caught by `_known_overrides`: the unconfirmed banner)."""
        return _services_in(self.config, self.registry.tools)

    def _stage(self) -> str:
        """The stage the banner reads (`config.environment`, a plain text value). The seal keeps its
        VALUE, not a reference: a text has no identity worth keeping, and a stage changed after
        `build` (a forced `object.__setattr__` on the config) would otherwise leave a made-up banner
        beside real services."""
        stage = getattr(self.config, "environment", None)
        if not isinstance(stage, str):
            raise TypeError("the config of this app has no stage text to read")
        return stage

    def __deepcopy__(self, memo: dict) -> App:
        """A deep copy of an App is refused (see the comment on `_sealed`)."""
        raise TypeError(
            "an App cannot be deep-copied: it holds live connections; build another App, or use copy.copy"
        )

    def _seal(self, overridden: _Given) -> None:
        """Record what was handed to `build` and what the app was made of; `build` calls this once, at the end, with the
        names `_given_overrides` computed (a `_Given`; any other value, such as `()`, is refused). Private by name: it is not
        part of the supported API. If the app cannot be read (see `_SEAL_ERRORS`), one warning line names the error type
        and the app is sealed as unreadable: its banner is the unconfirmed one and `build` still returns it."""
        if not isinstance(overridden, _Given):
            raise TypeError("an app is sealed only with the names that build worked out")
        self.overridden = tuple(overridden)
        try:
            self._sealed = (
                self.overridden,
                self._connected_parts(),
                self._banner_services(),
                self._stage(),
            )
        except _SEAL_ERRORS as exc:
            _warn_once("the app could not be read when it was built", exc)
            self._sealed = _UNREADABLE

    def _known_overrides(self) -> tuple[str, ...] | None:
        """`overridden` when this app is exactly what `build` sealed (the recorded names equal the sealed names, every
        connected part is the same object as then, and the services the banner reads are the same lists), else None. Never
        raises: any failure to read the parts is None."""
        try:
            sealed = self._sealed
            if (
                sealed is None
                or sealed is _UNREADABLE
                or self.overridden is None
                or tuple(self.overridden) != sealed[0]
            ):
                return None
            now_parts = self._connected_parts()
            if len(now_parts) != len(sealed[1]) or any(
                la != lb or a is not b
                for (la, a), (lb, b) in zip(now_parts, sealed[1], strict=True)
            ):
                return None
            if self._banner_services() != sealed[2]:
                return None
            if self._stage() != sealed[3]:
                return None
            return sealed[0]
        except Exception as exc:
            _warn_once("the connected parts of the app could not be read", exc)
            return None

    def mode_banner(
        self, names: Mapping[str, str] | None = None, words: BannerWords = DEFAULT_WORDS
    ) -> dict:
        """The banner for a screen (the supported call): `mode_banner.banner_or_unconfirmed` for this app's config, tool
        manifests and overrides. An app that `build` did not record, or whose connected parts changed since (see
        `_connected_parts`), gets the unconfirmed banner (`overridden=None`). Never raises."""
        try:
            known = self._known_overrides()
            if known is None:
                return not_confirmed_banner(words)
            return banner_or_unconfirmed(
                self.config, names, words, tool_specs=self.registry.tools, overridden=known
            )
        except Exception as exc:
            # whatever is wrong with the app, the screen must still say something
            _warn_once("the app could not be read", exc)
            return not_confirmed_banner(words)


def _given_overrides(**given: object) -> _Given:
    """The names of the `build` overrides that replace something: an object handed in (not None), or a mapping that holds
    at least one entry (an empty `tools={}` or `sources={}` replaces nothing). Names only, in the order of `OVERRIDES`. A
    name `OVERRIDES` does not list is a ValueError here, but this only fires for names passed in: that every `build`
    parameter is either an override or on `NOT_CONNECTIVITY` is checked by a test that reads the signature of `build`."""
    if unknown := sorted(set(given) - set(OVERRIDES)):
        raise ValueError(f"build override not known to the mode banner: {unknown[0]}")
    return _Given(
        n
        for n in OVERRIDES
        if given.get(n) is not None and not (isinstance(given[n], Mapping) and not given[n])
    )


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
    overridden = _given_overrides(
        tools=tools,
        sources=sources,
        channel=channel,
        llm=llm,
        detector=detector,
        secrets=secrets,
        hold_run_ids=hold_run_ids,
        clock=None if clock is now else clock,
    )  # before the names below are reassigned
    cfg = load_config(config_dir)
    reg = load_registry(cfg)
    b = cfg.backends
    secrets = secrets or make("secrets", b.secrets)
    live = is_live(cfg.environment)
    if live and not cfg.evidence.restored_hash_key_secret_name:
        raise ConfigError("evidence.restored_hash_key_secret_name is required in pilot and prod")
    if live and getattr(b.store, "kind", "") == "postgres" and not b.store.purge_dsn_secret_name:
        # Only the purge role may DELETE evidence; without its DSN the purge fails every tick and the
        # redaction maps (plaintext originals) are kept for ever.
        raise ConfigError("backends.store.purge_dsn_secret_name is required in pilot and prod")
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
        except Exception as exc:  # a broken channel is an undelivered card, never a crash
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
        tools=dict(tools or {}),
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
    app = App(
        cfg,
        reg,
        store,
        audit,
        limits,
        executor,
        approvals,
        runtime,
        sources={**built_sources, **(sources or {})},
        disabled_sources=disabled_sources,
        purge_store=purge_store,
    )
    app._seal(overridden)
    return app


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
    parts = urlsplit(kind.endpoint(settings))
    plain = parts.scheme == "http"
    if plain and sc.token_secret_name:
        raise ConfigError(f"source {name}: a bearer token never travels over plain http; use https")
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
        if disabled and name in disabled and not sources_mod.PROBING.get():
            raise tools_mod.ToolRefused(f"source {name} is switched off: its scope probe failed")
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
    return (urlsplit(source_endpoint(sc)).hostname or "").lower()


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
            return f"source {named} is switched off: its scope probe failed"
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
        scrub=ev.scrub,
        stored_kinds=frozenset(ev.stored_kinds),
        max_abandoned=ev.max_abandoned_tool_threads,
        max_concurrent=ev.max_concurrent_tool_calls,
        max_per_minute=ev.max_tool_calls_per_minute,
        fetch_counter=fetch_counter,
        disabled=_switched_off(disabled_sources, source_hosts or {}),
        ssl_context_for=lambda spec: contexts.get(spec.name),
    )
