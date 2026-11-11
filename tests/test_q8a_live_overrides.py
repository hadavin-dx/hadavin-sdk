"""Q8a-1: a pilot or prod process is never built with a test object by accident, and never with a static Vault token.

`app.build` takes six keyword arguments that exist for tests (`secrets=`, `channel=`, `detector=`, `llm=`, `clock=`,
`timeout_s=`). In demo each replaces one configured part. In pilot and prod (any stage that is not exactly demo) a build
that is given one of them is refused. `hold_run_ids=` is a production hook and stays allowed. `run_tick` refuses its
`now=` and its `steps=` in the same way.

The Vault kinds (`vault` for secrets, `vault_transit` for the audit signer, and any kind built on the same settings
class) sign in with a static token by default (`auth: token`). A pilot or prod BUILD refuses that, written or left out.
The config still loads, so the one-off commands that only load the config (limits stop and reset, audit verify, gate,
migrate, replay, score) keep working with a person's own short-lived token.

What these refusals do not cover: they refuse the six keywords of build and now= and steps= of run_tick; any route
that does not pass through them is not covered (constructing App, Runtime or Approvals directly, assigning attributes
after build, a kind added to the table, a direct call of the factory, a leftover patch of app.make or app.now, a
changed or patched runtime.tick.STEPS that still holds every built-in step name (reordering, or replacing a step's
function), a clock replaced after build, the time parameters of Approvals.sweep and resend_unsent, the store's
purge_tool_calls(before) and purge_redaction_maps(before)). A runtime.tick.STEPS that lacks a built-in step IS refused
outside demo, and so is a tick context (TickContext) that is handed a time: a tick step called by hand cannot work with
a time of the caller's choice. A tick step outside demo takes only an object whose type is exactly TickContext (a plain
stand-in, a Mock(spec=TickContext) and a subclass are refused), and a STEPS list with a name used twice is refused.
Not covered, and said so in the docstrings and the CHANGELOG: object.__setattr__ on a real context, a context built
without its constructor, an app wrapper reporting demo, a reordered STEPS or a same-name replacement of a step, a
rebound _BUILT_IN, and the store's purge methods called directly with a time (no test here pretends otherwise).

No test here can read a real Vault credential: the two environment variables a Vault sign-in reads are removed for
every test of this module, so a broken check fails at once and never reaches the network.

No test here needs a database. The stage words that are not stages are built from parts (a class test scans this folder).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from types import SimpleNamespace

import pytest
import yaml

from hadavin_sdk import app as app_mod
from hadavin_sdk import cli as cli_mod
from hadavin_sdk import defaults
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.approvals.channel import FakeChannel
from hadavin_sdk.backends import factory as factory_mod
from hadavin_sdk.backends.table import TABLE, Entry, KindSettings
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.guard.injection import RegexDetector
from hadavin_sdk.models import now
from hadavin_sdk.registry import load_registry
from hadavin_sdk.runtime import tick as tick_mod
from hadavin_sdk.runtime.tick import STEPS, TickStep, run_tick
from hadavin_sdk.store.memory import MemoryStore
from tests.conftest import make_cfg, qualify, vault_connection_class
from tests.test_k3_pilot import ScriptedLLM
from tests.test_k3_pilot_env import (
    PILOT_KINDS,
    asked,
    assert_asked_as_configured,
    pilot_cfg,
    plant_test_backends,
)

VaultConnection = vault_connection_class()

# What a context built with a given time says outside demo (a copy made by dataclasses.replace says the same).
COPY_REFUSAL = (
    "now= is for tests; it is refused in pilot and prod. Build the context as TickContext(app), which takes "
    "the time from the app's clock (a copy made by replace() carries the old time as a given one, so it is "
    "refused too)"
)
NAMES = ("secrets", "channel", "detector", "llm", "clock", "timeout_s")
NOT_A_STAGE = ["stag" + "ing", "Demo", "demo ", "", None]
DEMO_SECRETS = {"fixture-token": "tok" + "-q8a"}
PILOT_SECRETS = {
    "slack-token": "t",
    "slack-sign": "s",
    "pg-dsn": "unused",
    "pg-purge": "unused",
    "restored-key": "r" * 16,
    "audit-key": "unused",
}


@pytest.fixture(autouse=True)
def _no_vault_credentials(monkeypatch):
    """A Vault sign-in reads these two variables. Without them a broken check stops at 'variable not set' and never
    sends a real credential anywhere."""
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    monkeypatch.delenv("VAULT_SECRET_ID", raising=False)


def _fixed_clock() -> datetime:
    return datetime(2026, 11, 11, tzinfo=UTC)


def override(name: str, secrets: dict[str, str] | None = None):
    """One test object for the keyword `name`."""
    return {
        "secrets": lambda: FakeSecretProvider(secrets or {}),
        "channel": FakeChannel,
        "detector": lambda: RegexDetector(0.5),
        "llm": ScriptedLLM,
        "clock": lambda: _fixed_clock,
        "timeout_s": lambda: 2.5,
    }[name]()


def message(name: str) -> str:
    if name in ("clock", "timeout_s"):
        return f"{name}= is for tests; it is refused in pilot and prod"
    return f"{name}= is for tests; configure backends.{name} in pilot and prod"


def exactly(text: str) -> str:
    return "^" + re.escape(text) + "$"


def edit(root, fn) -> None:
    path = root / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    fn(data)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def live_dir(tmp_path, monkeypatch, where):
    """A config folder whose stage is `where`, made from the pilot config (real kinds only), with the empty folder the
    mounted-file secrets kind reads from. For a stage other than pilot the loaded pilot config is copied with the stage
    changed (model_copy skips the checks at load) and `build` is handed that copy."""
    root = pilot_cfg(tmp_path)
    (root / "secrets").mkdir()
    if where != "pilot":
        cfg = load_config(root)
        reg = load_registry(cfg)
        copy = cfg.model_copy(update={"environment": where})
        monkeypatch.setattr(app_mod, "load_config", lambda _d: copy)
        monkeypatch.setattr(app_mod, "load_registry", lambda _c: reg)
    return root


class Falsy:
    """Makes an object falsy (an empty container is the usual way an object gets that way)."""

    def __bool__(self) -> bool:
        return False


class FalsyChannel(Falsy, FakeChannel):
    pass


class FalsySecrets(Falsy, FakeSecretProvider):
    pass


class FalsyLLM(Falsy, ScriptedLLM):
    pass


class FalsyDict(Falsy, dict):
    """A mapping that holds entries and is falsy all the same."""


def echo(_args: dict) -> str:
    return "x"


# --- behaviour 1: the six test keywords are refused outside demo ---------------------------------------------------------


@pytest.mark.parametrize("where", ["pilot", "prod"])
@pytest.mark.parametrize("name", NAMES)
def test_each_test_keyword_is_refused_in_pilot_and_prod(tmp_path, monkeypatch, where, name):
    root = live_dir(tmp_path, monkeypatch, where)
    with pytest.raises(ConfigError, match=exactly(message(name))):
        app_mod.build(root, ["ito-agent"], **{name: override(name, PILOT_SECRETS)})


@pytest.mark.parametrize("where", NOT_A_STAGE)
def test_a_test_keyword_is_refused_for_a_value_that_is_not_a_stage(tmp_path, monkeypatch, where):
    """Only exactly demo is relaxed: a config whose stage is anything else is live."""
    root = live_dir(tmp_path, monkeypatch, where)
    with pytest.raises(ConfigError, match=exactly(message("channel"))):
        app_mod.build(root, ["ito-agent"], channel=FakeChannel())


def test_a_falsy_test_object_is_refused_in_pilot(tmp_path, monkeypatch):
    """The check asks 'was an object given' (is not None), not 'is the object truthy'."""
    root = live_dir(tmp_path, monkeypatch, "pilot")
    channel = FalsyChannel()
    assert not channel
    with pytest.raises(ConfigError, match=exactly(message("channel"))):
        app_mod.build(root, ["ito-agent"], channel=channel)


@pytest.mark.parametrize("value", [0, 0.0])
def test_a_zero_timeout_is_refused_in_pilot_as_a_test_keyword(tmp_path, monkeypatch, value):
    """In pilot and prod the keyword itself is refused, whatever its value."""
    root = live_dir(tmp_path, monkeypatch, "pilot")
    with pytest.raises(ConfigError, match=exactly(message("timeout_s"))):
        app_mod.build(root, ["ito-agent"], timeout_s=value)


@pytest.mark.parametrize(
    ("given", "named"),
    [
        (("timeout_s", "clock", "llm", "detector", "channel", "secrets"), "secrets"),
        (("timeout_s", "clock", "llm", "detector", "channel"), "channel"),
        (("timeout_s", "clock", "llm", "detector"), "detector"),
        (("timeout_s", "clock", "llm"), "llm"),
        (("timeout_s", "clock"), "clock"),
    ],
)
def test_with_several_given_only_the_first_in_the_fixed_order_is_named(
    tmp_path, monkeypatch, given, named
):
    root = live_dir(tmp_path, monkeypatch, "pilot")
    with pytest.raises(ConfigError, match=exactly(message(named))):
        app_mod.build(root, ["ito-agent"], **{n: override(n, PILOT_SECRETS) for n in given})


def test_the_earlier_refusals_still_come_first(tmp_path, monkeypatch):
    """`sources=` and `tools=` keep their own message when a test keyword is given beside them."""
    root = live_dir(tmp_path, monkeypatch, "pilot")
    with pytest.raises(ConfigError, match="plain callables"):
        app_mod.build(root, ["ito-agent"], channel=FakeChannel(), tools={"echo": echo})
    with pytest.raises(ConfigError, match=re.escape("sources= is for tests")):
        app_mod.build(root, ["ito-agent"], channel=FakeChannel(), sources={"s": object()})


@pytest.mark.parametrize("where", ["pilot", "prod", *NOT_A_STAGE])
def test_a_live_build_with_no_test_keyword_is_not_refused(tmp_path, monkeypatch, where):
    """The refusal must not catch an ordinary pilot or prod start (`clock` has no default object any more), and
    `hold_run_ids=` (a production hook) stays allowed. Every backend comes from the factory, which this test
    replaces for the four capabilities that would contact a real service; the test asserts what the build asked for."""
    root = live_dir(tmp_path, monkeypatch, where)
    qualify(load_registry(load_config(root)), "ito-agent")
    channel, secrets = FakeChannel(), FakeSecretProvider(PILOT_SECRETS)
    for kwargs in ({}, {"hold_run_ids": lambda: frozenset()}):
        calls = plant_test_backends(
            monkeypatch, secrets=secrets, store=MemoryStore, channel=channel, llm=ScriptedLLM()
        )
        app = app_mod.build(root, ["ito-agent"], **kwargs)
        assert asked(calls, secrets) == PILOT_KINDS
        assert_asked_as_configured(calls, app.config)
        assert app.config.environment == where
        assert app.executor is None
        assert app.approvals.channel is channel
        assert app.approvals.clock is now, "with no clock= given the real clock is used"
        assert app.runtime.hooks.hold_run_ids is kwargs.get("hold_run_ids")


# --- sources= and tools=: 'given' means not None there too ------------------------------------------------------------


def test_a_falsy_sources_mapping_is_refused_in_pilot(tmp_path, monkeypatch):
    """A mapping that holds a source and is falsy was let past the refusal (and then dropped without a word)."""
    root = live_dir(tmp_path, monkeypatch, "pilot")
    with pytest.raises(ConfigError, match=re.escape("sources= is for tests")):
        app_mod.build(root, ["ito-agent"], sources=FalsyDict({"s": object()}))


def test_a_falsy_tools_mapping_is_refused_in_pilot(tmp_path, monkeypatch):
    root = live_dir(tmp_path, monkeypatch, "pilot")
    with pytest.raises(ConfigError, match="plain callables"):
        app_mod.build(root, ["ito-agent"], tools=FalsyDict({"echo": echo}))


def test_an_empty_sources_or_tools_mapping_is_refused_in_pilot(tmp_path, monkeypatch):
    """Given means not None: an empty mapping is a given one. (Before, an empty mapping was let through.)"""
    root = live_dir(tmp_path, monkeypatch, "pilot")
    with pytest.raises(ConfigError, match=re.escape("sources= is for tests")):
        app_mod.build(root, ["ito-agent"], sources={})
    with pytest.raises(ConfigError, match="plain callables"):
        app_mod.build(root, ["ito-agent"], tools={})


# --- demo keeps every test keyword ------------------------------------------------------------------------------------


@pytest.fixture
def demo_dir(tmp_path):
    cfg_dir = make_cfg(tmp_path)
    qualify(load_registry(load_config(cfg_dir)))
    return cfg_dir


@pytest.mark.parametrize("name", NAMES)
def test_demo_accepts_each_test_keyword(demo_dir, monkeypatch, name):
    given = override(name, DEMO_SECRETS)
    if name != "secrets":
        # the fixture's fake secrets kind is empty: the build needs the fixture's one secret
        plant_test_backends(monkeypatch, secrets=FakeSecretProvider(DEMO_SECRETS))
    app = app_mod.build(demo_dir, ["test-agent"], **{name: given})
    used = {
        "secrets": lambda: app.executor._secrets,
        "channel": lambda: app.approvals.channel,
        "detector": lambda: app.runtime.detector,
        "llm": lambda: app.runtime.llm,
        "clock": lambda: app.approvals.clock,
        "timeout_s": lambda: app.executor.timeout_s,
    }[name]()
    assert used is given or used == given == 2.5, f"demo did not use the {name}= it was given"


def test_demo_uses_a_falsy_test_object_instead_of_dropping_it(demo_dir):
    """An object that is falsy was replaced by the configured backend without a word; it is used as given now."""
    secrets, channel, llm = FalsySecrets(DEMO_SECRETS), FalsyChannel(), FalsyLLM()
    assert not secrets and not channel and not llm
    app = app_mod.build(demo_dir, ["test-agent"], secrets=secrets, channel=channel, llm=llm)
    assert app.executor._secrets is secrets, "a falsy secrets= object was dropped"
    assert app.approvals.channel is channel, "a falsy channel= object was dropped"
    assert app.runtime.llm is llm, "a falsy llm= object was dropped"


def test_demo_uses_a_falsy_sources_or_tools_mapping_instead_of_dropping_it(demo_dir):
    source = SimpleNamespace(probe_scope=list)
    sources, tools = FalsyDict({"s": source}), FalsyDict({"echo": echo})
    assert not sources and not tools
    app = app_mod.build(
        demo_dir,
        ["test-agent"],
        secrets=FakeSecretProvider(DEMO_SECRETS),
        sources=sources,
        tools=tools,
    )
    assert app.sources.get("s") is source, "a falsy sources= mapping was dropped"
    assert app.runtime.hooks.tools == {"echo": echo}, "a falsy tools= mapping was dropped"


# The two bounds, written out here once as the pin (a test below holds them against `defaults`); every other place
# in this file uses these two names.
MIN_S, MAX_S = 0.001, 3600
TIMEOUT_RULE = f"must be an int or float between {MIN_S} and {MAX_S}"
TIMEOUT_MESSAGE = f"timeout_s= {TIMEOUT_RULE}"
TIMEOUT_REFUSED = [
    0,
    0.0,
    -1,
    -0.5,
    True,
    False,
    float("nan"),
    float("inf"),
    "5",
    [5],
    Decimal("2.5"),
    Fraction(5, 2),
    10**400,
    MAX_S + 1,
    MAX_S + 0.1,
    MAX_S + 0.0000001,
    MIN_S / 2,
    1e-9,
    5e-324,
]


@pytest.mark.parametrize("value", TIMEOUT_REFUSED, ids=[repr(v)[:12] for v in TIMEOUT_REFUSED])
def test_demo_refuses_a_timeout_outside_the_range_or_of_another_type(demo_dir, value):
    """0 would make every executor call fail at once (a socket that never waits), so it is refused, not passed on.
    Only int and float count as a number here: True and False, Decimal and Fraction are refused, and so is a
    number over one hour (ten to the power 400 would overflow at the socket) or under one millisecond (no network
    call can finish in less; such a value would act like 0)."""
    with pytest.raises(ConfigError, match=exactly(TIMEOUT_MESSAGE)):
        app_mod.build(
            demo_dir, ["test-agent"], secrets=FakeSecretProvider(DEMO_SECRETS), timeout_s=value
        )


@pytest.mark.parametrize("value", [3, MIN_S, 2.5, MAX_S, float(MAX_S)])
def test_demo_uses_a_timeout_in_the_range_as_given(demo_dir, value):
    app = app_mod.build(
        demo_dir, ["test-agent"], secrets=FakeSecretProvider(DEMO_SECRETS), timeout_s=value
    )
    assert app.executor.timeout_s == value


class _Reads(KindSettings):
    kind: str = "q8a_reads"
    token_secret_name: str


def _reading_channel(settings, deps):
    _reading_channel.seen.append(deps.resolve(settings.token_secret_name))
    return FakeChannel()


def test_the_factory_hands_a_falsy_secret_provider_to_the_backend(monkeypatch):
    """The same class of slip one level down: `make` must not swap a falsy provider for an empty one."""
    seen: list[str] = []
    monkeypatch.setitem(
        TABLE["channel"], "q8a_reads", Entry(_Reads, f"{__name__}:_reading_channel")
    )
    monkeypatch.setattr(_reading_channel, "seen", seen, raising=False)
    # the one secret name of the fixture, as a config file would give it
    (name,) = DEMO_SECRETS
    settings = _Reads.model_validate({"token_secret_name": name})
    factory_mod.make("channel", settings, FalsySecrets(DEMO_SECRETS))
    assert seen == [DEMO_SECRETS[name]], "a falsy provider was replaced by an empty one"


# --- run_tick: now= is for tests -------------------------------------------------------------------------------------


def _demo_app_at(demo_dir, where):
    """A built demo app whose config says the stage is `where` (an unvalidated copy: only the stage is changed)."""
    app = app_mod.build(demo_dir, ["test-agent"], secrets=FakeSecretProvider(DEMO_SECRETS))
    app.config = app.config.model_copy(update={"environment": where})
    return app


@pytest.mark.parametrize("where", ["pilot", "prod", *NOT_A_STAGE])
def test_run_tick_refuses_a_given_time_outside_demo(demo_dir, where):
    """A time in the future handed to the tick would purge evidence early; outside demo the clock is the app's own."""
    app = _demo_app_at(demo_dir, where)
    future = datetime.now(UTC) + timedelta(days=500)
    with pytest.raises(
        ConfigError, match=exactly("now= is for tests; it is refused in pilot and prod")
    ):
        run_tick(app, now=future)
    assert app.store.get_tick_state("purge_evidence") is None, "a step ran before the refusal"
    assert run_tick(app) == 0, "a tick with no now= must run outside demo"


def test_run_tick_accepts_a_given_time_in_demo(demo_dir):
    app = _demo_app_at(demo_dir, "demo")
    at = datetime(2026, 11, 11, 12, 0, tzinfo=UTC)
    assert run_tick(app, now=at) == 0
    assert app.store.get_tick_state("purge_evidence").last_run_at == at


def _recording_step(ran: list[str]) -> TickStep:
    return TickStep("recorded", 0, lambda _ctx: ran.append("recorded"))


@pytest.mark.parametrize("empty", [False, True], ids=["one-step", "empty-list"])
@pytest.mark.parametrize("where", ["pilot", "prod", *NOT_A_STAGE])
def test_run_tick_refuses_a_given_step_list_outside_demo(demo_dir, where, empty):
    """A tick with a step list of the caller's choice could return 0 without the sweep or the purge ever running."""
    app = _demo_app_at(demo_dir, where)
    ran: list[str] = []
    steps = [] if empty else [_recording_step(ran)]
    with pytest.raises(
        ConfigError, match=exactly("steps= is for tests; it is refused in pilot and prod")
    ):
        run_tick(app, steps=steps)
    assert ran == [], "a given step ran before the refusal"
    assert all(app.store.get_tick_state(s.name) is None for s in STEPS), "a step ran"
    assert run_tick(app) == 0
    assert all(app.store.get_tick_state(s.name) is not None for s in STEPS), (
        "a tick with no steps= must run every step of STEPS outside demo"
    )


def test_run_tick_names_now_first_when_both_are_given_outside_demo(demo_dir):
    app = _demo_app_at(demo_dir, "pilot")
    with pytest.raises(
        ConfigError, match=exactly("now= is for tests; it is refused in pilot and prod")
    ):
        run_tick(app, now=datetime.now(UTC), steps=[])


def test_run_tick_accepts_a_given_step_list_in_demo(demo_dir):
    app = _demo_app_at(demo_dir, "demo")
    ran: list[str] = []
    assert run_tick(app, steps=[_recording_step(ran)]) == 0
    assert ran == ["recorded"]
    assert run_tick(app, steps=[]) == 0


# --- the built-in steps of the tick may not go missing outside demo ----------------------------------------------------


@pytest.mark.parametrize("gone", ["sweep", "purge_evidence"])
@pytest.mark.parametrize("where", ["pilot", "prod", *NOT_A_STAGE])
def test_run_tick_refuses_a_step_list_that_lacks_a_built_in_step_outside_demo(
    demo_dir, monkeypatch, where, gone
):
    """`runtime.tick.STEPS` is where a deployment adds a step. With a built-in step taken out, a tick would return 0
    without that step ever running; outside demo it is refused before anything runs."""
    app = _demo_app_at(demo_dir, where)
    monkeypatch.setattr(tick_mod, "STEPS", [s for s in STEPS if s.name != gone])
    with pytest.raises(ConfigError, match=exactly(f"a built-in tick step is missing: {gone}")):
        run_tick(app)
    assert all(app.store.get_tick_state(s.name) is None for s in STEPS), "a step ran"


def test_run_tick_refuses_an_emptied_step_list_outside_demo(demo_dir, monkeypatch):
    app = _demo_app_at(demo_dir, "pilot")
    names = ", ".join(s.name for s in STEPS)
    monkeypatch.setattr(tick_mod, "STEPS", list(STEPS))
    tick_mod.STEPS.clear()
    with pytest.raises(ConfigError, match=exactly(f"a built-in tick step is missing: {names}")):
        run_tick(app)
    assert all(app.store.get_tick_state(s.name) is None for s in STEPS), "a step ran"


@pytest.mark.parametrize("where", ["pilot", "prod"])
def test_an_appended_step_runs_outside_demo_after_every_built_in_step(demo_dir, monkeypatch, where):
    """The supported way to add a step: append a TickStep to `runtime.tick.STEPS`."""
    app = _demo_app_at(demo_dir, where)
    seen: list[list[str]] = []
    extra = TickStep("extra_step", 0, lambda ctx: seen.append(sorted(ctx.results)))
    monkeypatch.setattr(tick_mod, "STEPS", [*STEPS, extra])
    assert run_tick(app) == 0
    assert seen == [sorted(s.name for s in STEPS)], (
        "the appended step did not run after the built-in steps"
    )
    assert all(app.store.get_tick_state(s.name) is not None for s in [*STEPS, extra])


def test_demo_runs_a_step_list_that_lacks_a_built_in_step(demo_dir, monkeypatch):
    """Demo is unchanged: the list is run as it is."""
    app = _demo_app_at(demo_dir, "demo")
    monkeypatch.setattr(tick_mod, "STEPS", [s for s in STEPS if s.name != "purge_evidence"])
    assert run_tick(app) == 0
    assert app.store.get_tick_state("purge_evidence") is None
    assert app.store.get_tick_state("sweep") is not None


# --- the approvals object: a time handed to it is used as given -----------------------------------------------------------


class FalsyTime(datetime):
    """A time that is falsy (no real datetime is; this pins 'given means not None' for the two methods below)."""

    def __bool__(self) -> bool:
        return False


@pytest.mark.parametrize("method", ["sweep", "resend_unsent"])
def test_the_approvals_object_uses_a_time_that_is_falsy_as_given(demo_dir, method):
    """`at=` is the tick's own parameter. A given time is used, never swapped for the clock because it is falsy."""
    app = _demo_app_at(demo_dir, "demo")
    at = FalsyTime(2026, 11, 11, tzinfo=UTC)
    assert not at

    def clock_must_not_be_asked():
        raise AssertionError("the clock was asked although a time was given")

    app.approvals.clock = clock_must_not_be_asked
    assert getattr(app.approvals, method)(at) == []


# --- one rule for the executor timeout, on both routes (the keyword of build, the field of the config file) ---------------

# (the text in a config file, the same value handed to the keyword). YAML has no Decimal or Fraction.
BOTH_ROUTES_REFUSE = [
    ("0", 0),
    ("-1", -1),
    ("true", True),
    ("false", False),
    ("'5'", "5"),
    (".inf", float("inf")),
    (".nan", float("nan")),
    (f"{MAX_S}.0000001", MAX_S + 0.0000001),
    (f"{MAX_S + 1}", MAX_S + 1),
    ("1" + "0" * 400, 10**400),
    ("1.0e-9", 1e-9),
    ("5.0e-324", 5e-324),
    ("[5]", [5]),
    ("5/2", "5/2"),
]
BOTH_ROUTES_ACCEPT = [
    (f"{MIN_S}", MIN_S),
    ("0.5", 0.5),
    ("3", 3),
    ("3.5", 3.5),
    (f"{MAX_S}", MAX_S),
]


def _config_with_timeout(tmp_path, text):
    cfg_dir = make_cfg(tmp_path)
    path = cfg_dir / "config.yaml"
    path.write_text(
        path.read_text(encoding="utf-8") + f"\nexecutor_timeout_s: {text}\n", encoding="utf-8"
    )
    return cfg_dir


@pytest.mark.parametrize(
    ("text", "value"), BOTH_ROUTES_REFUSE, ids=[t[:10] for t, _ in BOTH_ROUTES_REFUSE]
)
def test_the_config_file_and_the_keyword_refuse_the_same_executor_timeouts(
    demo_dir, tmp_path, text, value
):
    """One rule in one place (`config.executor_timeout_ok`) for both routes: what `timeout_s=` refuses, the config
    field `executor_timeout_s` refuses too, with the same sentence. `true` and '5' are refused before they could
    be read as 1.0 and 5.0."""
    with pytest.raises(ConfigError, match=exactly(TIMEOUT_MESSAGE)):
        app_mod.build(
            demo_dir, ["test-agent"], secrets=FakeSecretProvider(DEMO_SECRETS), timeout_s=value
        )
    with pytest.raises(ConfigError, match="executor_timeout_s") as err:
        load_config(_config_with_timeout(tmp_path / "file", text))
    assert TIMEOUT_RULE in str(err.value), "the config file gives another reason than the keyword"


@pytest.mark.parametrize(
    ("text", "value"), BOTH_ROUTES_ACCEPT, ids=[t for t, _ in BOTH_ROUTES_ACCEPT]
)
def test_the_config_file_and_the_keyword_accept_the_same_executor_timeouts(
    demo_dir, tmp_path, text, value
):
    by_keyword = app_mod.build(
        demo_dir, ["test-agent"], secrets=FakeSecretProvider(DEMO_SECRETS), timeout_s=value
    )
    cfg_dir = _config_with_timeout(tmp_path / "file", text)
    assert load_config(cfg_dir).executor_timeout_s == value
    qualify(load_registry(load_config(cfg_dir)))
    by_file = app_mod.build(cfg_dir, ["test-agent"], secrets=FakeSecretProvider(DEMO_SECRETS))
    assert by_keyword.executor.timeout_s == by_file.executor.timeout_s == value


def test_the_default_executor_timeout_passes_the_rule():
    from hadavin_sdk.config import executor_timeout_ok

    assert executor_timeout_ok(defaults.EXECUTOR_TIMEOUT_S)
    assert (defaults.EXECUTOR_TIMEOUT_MIN_S, defaults.EXECUTOR_TIMEOUT_MAX_S) == (MIN_S, MAX_S)
    assert 0 < MIN_S < defaults.EXECUTOR_TIMEOUT_S < MAX_S


# --- the tick context: where the time enters the steps -------------------------------------------------------------------


def _purge_spy(app, monkeypatch) -> list[str]:
    """Record every purge call that reaches the store the purge uses (nothing is deleted through the spy's eyes
    unless the real method is reached, which is what the tests below rule out)."""
    reached: list[str] = []
    store = app.purge_store or app.store
    for name in ("purge_tool_calls", "purge_redaction_maps"):
        real = getattr(store, name)

        def spy(*args, _real=real, _name=name, **kwargs):
            reached.append(_name)
            return _real(*args, **kwargs)

        monkeypatch.setattr(store, name, spy)
    return reached


FAR_AHEAD = timedelta(days=500)


@pytest.mark.parametrize("where", ["pilot", "prod", *NOT_A_STAGE])
def test_a_tick_context_refuses_a_time_handed_to_it_outside_demo(demo_dir, monkeypatch, where):
    """The evidence purge deletes by age from the context's time. With a time 500 days ahead handed in by hand,
    `purge_evidence(TickContext(app, <time>))` deleted every stored tool call and redaction map of a pilot app. The
    context is where the time enters every step, so the refusal sits there: no purge call reaches the store."""
    app = _demo_app_at(demo_dir, where)
    reached = _purge_spy(app, monkeypatch)
    ahead = datetime.now(UTC) + FAR_AHEAD
    with pytest.raises(ConfigError, match=exactly(COPY_REFUSAL)):
        tick_mod.purge_evidence(tick_mod.TickContext(app, ahead))
    with pytest.raises(ConfigError, match=exactly(COPY_REFUSAL)):
        tick_mod.TickContext(app, now=datetime.now(UTC))
    assert reached == [], "a purge reached the store with a time handed in by hand"


STEP_FUNCTIONS = ["sweep", "reconcile", "stuck", "checkpoint", "purge_evidence", "reprobe_sources"]


def test_the_step_functions_checked_here_are_the_built_in_steps():
    assert [s.name for s in STEPS] == STEP_FUNCTIONS
    assert all(getattr(tick_mod, s.name) is s.fn for s in STEPS)


@pytest.mark.parametrize("step", ["sweep", "stuck", "purge_evidence"])
@pytest.mark.parametrize("where", ["pilot", "prod", *NOT_A_STAGE])
def test_a_step_refuses_a_stand_in_context_with_a_time_outside_demo(
    demo_dir, monkeypatch, where, step
):
    """An object that merely looks like a context (it has `app`, `now`, `results`) is the other way a hand-made time
    could reach a step. Every step that reads the time (the approval sweep, the stuck-run check, the evidence purge)
    takes it through one function, which outside demo takes a real TickContext only."""
    app = _demo_app_at(demo_dir, where)
    reached = _purge_spy(app, monkeypatch)
    stand_in = SimpleNamespace(app=app, now=datetime.now(UTC) + FAR_AHEAD, results={})
    with pytest.raises(
        ConfigError, match=exactly("now= is for tests; it is refused in pilot and prod")
    ):
        getattr(tick_mod, step)(stand_in)
    assert reached == []


class _LiesAboutItsClass:
    """Says `__class__` is TickContext, like a spec'd Mock does, and carries a time far ahead."""

    def __init__(self, app):
        self.app, self.now, self.results = app, datetime.now(UTC) + FAR_AHEAD, {}

    @property
    def __class__(self):
        return tick_mod.TickContext


@pytest.mark.parametrize("step", ["sweep", "stuck", "purge_evidence"])
@pytest.mark.parametrize("where", ["pilot", "prod", *NOT_A_STAGE])
def test_a_step_refuses_an_object_that_says_it_is_a_tick_context_outside_demo(
    demo_dir, monkeypatch, where, step
):
    """`isinstance` believes a `Mock(spec=TickContext)` and any object with a `__class__` property; the step asks for
    the exact type. No purge call reaches the store."""
    from unittest.mock import Mock

    app = _demo_app_at(demo_dir, where)
    reached = _purge_spy(app, monkeypatch)
    spec_mock = Mock(spec=tick_mod.TickContext)
    spec_mock.app, spec_mock.now = app, datetime.now(UTC) + FAR_AHEAD
    for stand_in in (spec_mock, _LiesAboutItsClass(app)):
        assert isinstance(stand_in, tick_mod.TickContext), "the stand-in no longer fools isinstance"
        with pytest.raises(
            ConfigError, match=exactly("now= is for tests; it is refused in pilot and prod")
        ):
            getattr(tick_mod, step)(stand_in)
    assert reached == []


def test_a_tick_context_cannot_be_subclassed():
    with pytest.raises(TypeError, match="cannot be subclassed"):
        type("Sub", (tick_mod.TickContext,), {})


@pytest.mark.parametrize("where", ["pilot", "prod"])
def test_run_tick_refuses_a_step_name_used_twice_outside_demo(demo_dir, monkeypatch, where):
    """Results and the tick_state row are kept by name: a step appended under a built-in name, with a failed
    built-in step before it, would record the built-in step as ok and the tick would return 0."""
    app = _demo_app_at(demo_dir, where)

    def broken(_ctx):
        raise RuntimeError("purge failed")

    built_in = [TickStep(s.name, 0, broken if s.name == "purge_evidence" else s.fn) for s in STEPS]
    monkeypatch.setattr(
        tick_mod, "STEPS", [*built_in, TickStep("purge_evidence", 0, lambda _c: None)]
    )
    with pytest.raises(
        ConfigError, match=exactly("a tick step name is used twice: purge_evidence")
    ):
        run_tick(app)
    assert app.store.get_tick_state("purge_evidence") is None, "a step ran before the refusal"


def test_a_config_error_never_shows_the_value_that_was_refused(tmp_path):
    secret_like = "not" + "-a-number-" + "zq81"
    with pytest.raises(ConfigError, match="executor_timeout_s") as err:
        load_config(_config_with_timeout(tmp_path, f"'{secret_like}'"))
    text = str(err.value)
    assert TIMEOUT_RULE in text
    assert secret_like not in text, "the config error repeats the refused value"
    assert "input_value" not in text and "errors.pydantic" not in text, text


def test_the_time_of_a_tick_context_cannot_be_changed_afterwards(demo_dir):
    import dataclasses

    app = _demo_app_at(demo_dir, "pilot")
    ctx = tick_mod.TickContext(app)
    with pytest.raises(dataclasses.FrozenInstanceError):
        ctx.now = datetime.now(UTC) + FAR_AHEAD
    with pytest.raises(ConfigError, match=exactly(COPY_REFUSAL)):
        dataclasses.replace(ctx, now=datetime.now(UTC) + FAR_AHEAD)
    with pytest.raises(ConfigError, match=exactly(COPY_REFUSAL)):
        dataclasses.replace(ctx, results={})  # `now` is never None once the context exists
    assert "replace()" in (tick_mod.TickContext.__doc__ or "")


@pytest.mark.parametrize("where", ["pilot", "prod"])
def test_a_tick_context_without_a_given_time_takes_the_apps_clock_outside_demo(
    demo_dir, monkeypatch, where
):
    """Not refused: one step called by hand with the clock's time (not a supported entry point, but it cannot delete
    early)."""
    app = _demo_app_at(demo_dir, where)
    at = datetime(2026, 11, 11, 9, 0, tzinfo=UTC)
    app.approvals.clock = lambda: at
    reached = _purge_spy(app, monkeypatch)
    ctx = tick_mod.TickContext(app)
    assert ctx.now == at
    tick_mod.purge_evidence(ctx)
    assert sorted(set(reached)) == ["purge_redaction_maps", "purge_tool_calls"]


def test_demo_keeps_a_tick_context_with_a_given_time_and_a_stand_in_context(demo_dir, monkeypatch):
    app = _demo_app_at(demo_dir, "demo")
    reached = _purge_spy(app, monkeypatch)
    at = datetime(2026, 11, 11, 9, 0, tzinfo=UTC)
    assert tick_mod.TickContext(app, at).now == at
    tick_mod.purge_evidence(tick_mod.TickContext(app, at))
    tick_mod.purge_evidence(SimpleNamespace(app=app, now=at, results={}))
    assert len(reached) >= 4


# --- behaviour 2: a static Vault token is refused by a pilot or prod build ------------------------------------------------

VAULT = {"kind": "vault", "address": "https://vault.example"}
TRANSIT = {
    "kind": "vault_transit",
    "address": "https://vault.example",
    "key_name": "k",
    "key_version": 1,
}
PROD_ANCHOR = {"kind": "s3_object_lock", "bucket": "b", "region": "r", "retention_ack": True}
KEY_FROM_SECRETS = {"kind": "ed25519_local", "private_key_secret_name": "audit-key"}
VAULT_CASES = {"secrets": VAULT, "signer": TRANSIT}
TOKEN_FORMS = [{"auth": "token"}, {}]
TOKEN_IDS = ["auth-written", "auth-left-out"]


def vault_dir(tmp_path, where, capability, settings):
    """The pilot config with `settings` as the backend of `capability`. Prod also gets what prod needs for other
    reasons: an anchor whose retention the client agreed and, unless the signer itself is the backend under test, a
    signer key that is not a file."""
    root = pilot_cfg(tmp_path, env=where)
    (root / "secrets").mkdir()

    def use(data):
        if where == "prod":
            data["backends"]["anchor"] = PROD_ANCHOR
            data["backends"]["signer"] = KEY_FROM_SECRETS
        data["backends"][capability] = settings

    edit(root, use)
    return root


def vault_message(where, capability, kind) -> str:
    return (
        f"environment {where}: refused: {capability}: {kind} auth token "
        "(the default; set auth: kubernetes (recommended) or auth: approle)"
    )


@pytest.mark.parametrize("form", TOKEN_FORMS, ids=TOKEN_IDS)
@pytest.mark.parametrize("capability", ["secrets", "signer"])
@pytest.mark.parametrize("where", ["pilot", "prod"])
def test_a_build_refuses_a_static_vault_token_in_pilot_and_prod_and_the_config_still_loads(
    tmp_path, monkeypatch, where, capability, form
):
    settings = VAULT_CASES[capability] | form
    root = vault_dir(tmp_path, where, capability, settings)
    # the loader accepts it: the one-off commands that only load the config are not refused
    cfg = load_config(root)
    assert getattr(cfg.backends, capability).auth == "token"
    calls = plant_test_backends(monkeypatch)
    want = vault_message(where, capability, settings["kind"])
    with pytest.raises(ConfigError, match=exactly(want)):
        app_mod.build(root, ["ito-agent"])
    assert calls == [], "a backend was built before the refusal (the token could have been read)"


@pytest.mark.parametrize("where", NOT_A_STAGE)
def test_a_build_refuses_a_static_vault_token_for_a_value_that_is_not_a_stage(
    tmp_path, monkeypatch, where
):
    root = vault_dir(tmp_path, "pilot", "secrets", VAULT)
    cfg = load_config(root)
    reg = load_registry(cfg)
    copy = cfg.model_copy(update={"environment": where})
    monkeypatch.setattr(app_mod, "load_config", lambda _d: copy)
    monkeypatch.setattr(app_mod, "load_registry", lambda _c: reg)
    with pytest.raises(ConfigError, match=exactly(vault_message(where, "secrets", "vault"))):
        app_mod.build(root, ["ito-agent"])


def test_both_static_vault_tokens_are_named_in_one_refusal(tmp_path):
    root = vault_dir(tmp_path, "pilot", "secrets", VAULT)
    edit(root, lambda d: d["backends"].update(signer=TRANSIT))
    fix = "(the default; set auth: kubernetes (recommended) or auth: approle)"
    want = (
        "environment pilot: refused: "
        f"secrets: vault auth token {fix}, signer: vault_transit auth token {fix}"
    )
    with pytest.raises(ConfigError, match=exactly(want)):
        app_mod.build(root, ["ito-agent"])


class _VaultBuilt(VaultConnection):
    """A third kind that signs in to Vault: built on the shared settings class, with a name of its own."""

    kind: str = "q8a_vault_built"


def test_a_new_kind_built_on_the_vault_settings_class_is_refused_too(tmp_path, monkeypatch):
    """The check asks for the settings type, not for the two kind names it knew when it was written."""
    monkeypatch.setitem(
        TABLE["channel"], "q8a_vault_built", Entry(_VaultBuilt, f"{__name__}:_reading_channel")
    )
    root = vault_dir(
        tmp_path,
        "pilot",
        "channel",
        {"kind": "q8a_vault_built", "address": "https://vault.example"},
    )
    assert load_config(root).backends.channel.auth == "token"
    with pytest.raises(
        ConfigError, match=exactly(vault_message("pilot", "channel", "q8a_vault_built"))
    ):
        app_mod.build(root, ["ito-agent"])


# Every field of the Vault settings that says how to sign in. Looked up 2026-11-11: in the table only the two Vault
# kinds have any of them.
SIGN_IN_FIELDS = {"auth", "token_env", "secret_id_env", "role_id", "jwt_path"}


def vault_like_kinds_outside_the_class() -> list[str]:
    """The kinds in the table whose settings have a sign-in field of the Vault settings (`SIGN_IN_FIELDS`) and are
    NOT built on `VaultConnection`: `app.build` would not see their static token."""
    return sorted(
        f"{capability}: {kind}"
        for capability, kinds in TABLE.items()
        for kind, entry in kinds.items()
        if SIGN_IN_FIELDS & set(entry.settings.model_fields)
        and not issubclass(entry.settings, VaultConnection)
    )


class _SignsInByItself(KindSettings):
    """A kind with its own `auth` and `token_env` fields, not built on the shared class."""

    kind: str = "q8a_signs_in_by_itself"
    auth: str = "token"
    token_env: str | None = None


def test_every_kind_with_a_vault_sign_in_field_is_built_on_the_vault_settings_class(monkeypatch):
    """`app.build` finds a static Vault token by the settings TYPE. A kind that brings its own `auth` or `token_env`
    field without that type would pass in pilot and prod, so the table may hold none; a planted one is reported."""
    assert vault_like_kinds_outside_the_class() == []
    held = {
        f"{c}: {k}"
        for c, kinds in TABLE.items()
        for k, e in kinds.items()
        if issubclass(e.settings, VaultConnection)
    }
    assert held == {"secrets: vault", "signer: vault_transit"}, "the guard looked at no Vault kind"
    monkeypatch.setitem(
        TABLE["channel"],
        "q8a_signs_in_by_itself",
        Entry(_SignsInByItself, f"{__name__}:_reading_channel"),
    )
    assert vault_like_kinds_outside_the_class() == ["channel: q8a_signs_in_by_itself"]


@pytest.mark.parametrize(
    "auth", [{"auth": "kubernetes", "role": "hadavin"}, {"auth": "approle", "role_id": "r-1"}]
)
@pytest.mark.parametrize("capability", ["secrets", "signer"])
@pytest.mark.parametrize("where", ["pilot", "prod"])
def test_a_build_accepts_the_other_vault_sign_ins_in_pilot_and_prod(
    tmp_path, monkeypatch, where, capability, auth
):
    """The fixtures above are refused for the token only: the same config with another sign-in builds. The Vault
    backend, the signer and the anchor are test objects here (no Vault, no cloud)."""
    root = vault_dir(tmp_path, where, capability, VAULT_CASES[capability] | auth)
    qualify(load_registry(load_config(root)), "ito-agent")
    secrets = FakeSecretProvider(PILOT_SECRETS)
    calls = plant_test_backends(
        monkeypatch,
        secrets=secrets,
        store=MemoryStore,
        channel=FakeChannel(),
        llm=ScriptedLLM(),
        signer=None,
        anchor=None,
    )
    app = app_mod.build(root, ["ito-agent"])
    assert app.config.environment == where
    assert VAULT_CASES[capability]["kind"] in asked(calls, secrets)[capability]


@pytest.mark.parametrize("form", TOKEN_FORMS, ids=TOKEN_IDS)
@pytest.mark.parametrize("capability", ["secrets", "signer"])
def test_demo_accepts_a_static_vault_token(tmp_path, monkeypatch, capability, form):
    cfg_dir = make_cfg(tmp_path)

    def use(data):
        data["backends"][capability] = VAULT_CASES[capability] | form
        if capability == "signer":
            # a signer needs the chained audit
            data["backends"]["audit"] = {"kind": "chain"}

    edit(cfg_dir, use)
    cfg = load_config(cfg_dir)
    assert cfg.environment == "demo"
    assert getattr(cfg.backends, capability).auth == "token"
    qualify(load_registry(cfg))
    secrets = FakeSecretProvider(DEMO_SECRETS)
    calls = plant_test_backends(monkeypatch, secrets=secrets, signer=None)
    app_mod.build(cfg_dir, ["test-agent"])
    assert VAULT_CASES[capability]["kind"] in asked(calls, secrets)[capability]


# --- the one-off commands keep working with a static token --------------------------------------------------------------


@pytest.mark.parametrize("action", ["stop", "reset"])
@pytest.mark.parametrize("where", ["pilot", "prod"])
def test_the_kill_switch_command_is_not_refused_for_a_static_vault_token(
    tmp_path, monkeypatch, capsys, where, action
):
    """`hadavin-sdk limits stop` and `limits reset` load the config and build the store and the audit themselves (no
    `app.build`). A person with a short-lived Vault token of their own must be able to run them in pilot and prod.
    The command's own function is called; the Vault backend, the store, the signer and the anchor are test objects."""
    root = vault_dir(tmp_path, where, "secrets", VAULT)
    monkeypatch.setenv("HADAVIN_CONFIG_DIR", str(root))
    store, secrets = MemoryStore(), FakeSecretProvider(PILOT_SECRETS)
    calls = plant_test_backends(
        monkeypatch, module=cli_mod, secrets=secrets, store=lambda: store, signer=None, anchor=None
    )
    assert cli_mod._main(["limits", action, "--by", "ops"]) == 0
    first = calls[0]
    assert (first.capability, first.kind, first.provider) == ("secrets", "vault", None)
    assert f"kill switch {'ON' if action == 'stop' else 'OFF'}" in capsys.readouterr().out
    # the long-running process with the same config is refused
    with pytest.raises(ConfigError, match=exactly(vault_message(where, "secrets", "vault"))):
        app_mod.build(root, ["ito-agent"])


@pytest.mark.parametrize("where", ["pilot", "prod"])
def test_run_tick_takes_one_copy_of_the_step_list_for_the_checks_and_the_loop(
    demo_dir, monkeypatch, where
):
    """A list edited in place between the checks and the loop must change nothing: the loop runs the list the
    checks saw. Here the purge step is cut out of STEPS by the first read of the app's store (after the checks)."""
    app = _demo_app_at(demo_dir, where)
    ran: list[str] = []
    steps = [TickStep(s.name, 0, lambda _c, n=s.name: ran.append(n)) for s in STEPS]
    monkeypatch.setattr(tick_mod, "STEPS", steps)
    original = app.store.get_tick_state

    def edit_after_the_checks(name):
        steps[:] = steps[:1]  # the checks have passed; now the list is cut in place
        return original(name)

    app.store.get_tick_state = edit_after_the_checks
    assert run_tick(app) == 0
    assert ran == STEP_FUNCTIONS, f"the loop ran a list other than the one that was checked: {ran}"
    # the checks themselves read a copy too: a list that is complete when read is not refused later
    assert tick_mod._missing_built_in_steps(tuple(steps)) == STEP_FUNCTIONS[1:]
    assert tick_mod._repeated_step_names(steps + steps) == [steps[0].name]
