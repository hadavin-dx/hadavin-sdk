"""Q8a-1: a pilot or prod process is never built with a test object by accident, and never with a static Vault token.

`app.build` takes six keyword arguments that exist for tests (`secrets=`, `channel=`, `detector=`, `llm=`, `clock=`,
`timeout_s=`). In demo each replaces one configured part. In pilot and prod (any stage that is not exactly demo) a build
that is given one of them is refused. `hold_run_ids=` is a production hook and stays allowed. `run_tick` refuses its
`now=` in the same way.

The Vault kinds (`vault` for secrets, `vault_transit` for the audit signer, and any kind built on the same settings
class) sign in with a static token by default (`auth: token`). A pilot or prod BUILD refuses that, written or left out.
The config still loads, so the one-off commands that only load the config (limits stop and reset, audit verify, gate,
migrate, replay, score) keep working with a person's own short-lived token.

What these refusals do not cover: they refuse the six keywords of build and now= of run_tick; any route that does not
pass through them is not covered (constructing App, Runtime or Approvals directly, assigning attributes after build, a
kind added to the table).

No test here needs a database. The stage words that are not stages are built from parts (a class test scans this folder).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
import yaml

from hadavin_sdk import app as app_mod
from hadavin_sdk import cli as cli_mod
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.approvals.channel import FakeChannel
from hadavin_sdk.backends import factory as factory_mod
from hadavin_sdk.backends.table import TABLE, Entry, KindSettings, VaultConnection
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.guard.injection import RegexDetector
from hadavin_sdk.models import now
from hadavin_sdk.registry import load_registry
from hadavin_sdk.runtime.tick import run_tick
from hadavin_sdk.store.memory import MemoryStore
from tests.conftest import make_cfg, qualify
from tests.test_k3_pilot import ScriptedLLM
from tests.test_k3_pilot_env import PILOT_KINDS, asked, pilot_cfg, plant_test_backends

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


@pytest.mark.parametrize(
    "value", [0, 0.0, -1, -0.5, True, False, float("nan"), float("inf"), "5", [5]]
)
def test_demo_refuses_a_timeout_that_is_not_a_number_greater_than_0(demo_dir, value):
    """0 would make every executor call fail at once (a socket that never waits), so it is refused, not passed on."""
    with pytest.raises(ConfigError, match=exactly("timeout_s= must be greater than 0")):
        app_mod.build(
            demo_dir, ["test-agent"], secrets=FakeSecretProvider(DEMO_SECRETS), timeout_s=value
        )


@pytest.mark.parametrize("value", [3, 0.001, 2.5])
def test_demo_uses_a_timeout_greater_than_0_as_given(demo_dir, value):
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
    with pytest.raises(ConfigError) as err:
        app_mod.build(root, ["ito-agent"])
    for capability, kind in (("secrets", "vault"), ("signer", "vault_transit")):
        assert f"{capability}: {kind} auth token" in str(err.value)


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
    assert ("secrets", "vault", None) in calls
    assert f"kill switch {'ON' if action == 'stop' else 'OFF'}" in capsys.readouterr().out
    # the long-running process with the same config is refused
    with pytest.raises(ConfigError, match=exactly(vault_message(where, "secrets", "vault"))):
        app_mod.build(root, ["ito-agent"])
