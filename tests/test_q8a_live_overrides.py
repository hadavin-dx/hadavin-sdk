"""Q8a-1: a pilot or prod process is never built with a test object by accident, and never with a static Vault token.

`app.build` takes six keyword arguments that exist for tests (`secrets=`, `channel=`, `detector=`, `llm=`, `clock=`,
`timeout_s=`). In demo each replaces one configured part. In pilot and prod (any stage that is not exactly demo) a build
that is given one of them is refused. `hold_run_ids=` is a production hook and stays allowed.

The Vault kinds (`vault` for secrets, `vault_transit` for the audit signer) sign in with a static token by default
(`auth: token`); that is refused in pilot and prod, written or left out.

No test here needs a database. The stage words that are not stages are built from parts (a class test scans this folder).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

import pytest
import yaml

from hadavin_sdk import app as app_mod
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.approvals.channel import FakeChannel
from hadavin_sdk.backends import factory as factory_mod
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.guard.injection import RegexDetector
from hadavin_sdk.models import now
from hadavin_sdk.registry import load_registry
from hadavin_sdk.store.memory import MemoryStore
from tests.conftest import make_cfg, qualify
from tests.test_k3_pilot import ScriptedLLM
from tests.test_k3_pilot_env import pilot_cfg

NAMES = ("secrets", "channel", "detector", "llm", "clock", "timeout_s")
NOT_A_STAGE = ["stag" + "ing", "Demo", "demo ", "", None]
DEMO_SECRETS = {"fixture-token": "tok" + "-q8a"}
PILOT_SECRETS = {
    "slack-token": "t",
    "slack-sign": "s",
    "pg-dsn": "unused",
    "pg-purge": "unused",
    "restored-key": "r" * 16,
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


def plant(monkeypatch, **objects):
    """Make `app.build` take the given objects from the factory (the real build path, no keyword override)."""

    def wrapper(capability, settings, *args, **kwargs):
        if capability in objects:
            made = objects[capability]
            return made() if callable(made) and capability == "store" else made
        return factory_mod.make(capability, settings, *args, **kwargs)

    monkeypatch.setattr(app_mod, "make", wrapper)


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


class FalsyChannel(FakeChannel):
    """A channel object that is falsy (an empty container is the usual way an object gets that way)."""

    def __bool__(self) -> bool:
        return False


class FalsySecrets(FakeSecretProvider):
    def __bool__(self) -> bool:
        return False


class FalsyLLM(ScriptedLLM):
    def __bool__(self) -> bool:
        return False


def test_a_falsy_test_object_is_refused_in_pilot(tmp_path, monkeypatch):
    """The check asks 'was an object given' (is not None), not 'is the object truthy'."""
    root = live_dir(tmp_path, monkeypatch, "pilot")
    channel = FalsyChannel()
    assert not channel
    with pytest.raises(ConfigError, match=exactly(message("channel"))):
        app_mod.build(root, ["ito-agent"], channel=channel)


@pytest.mark.parametrize("value", [0, 0.0])
def test_a_zero_timeout_is_refused_in_pilot(tmp_path, monkeypatch, value):
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
        app_mod.build(root, ["ito-agent"], channel=FakeChannel(), tools={"echo": lambda a: "x"})
    with pytest.raises(ConfigError, match=re.escape("sources= is for tests")):
        app_mod.build(root, ["ito-agent"], channel=FakeChannel(), sources={"s": object()})


@pytest.mark.parametrize("where", ["pilot", "prod", *NOT_A_STAGE])
def test_a_live_build_with_no_test_keyword_is_not_refused(tmp_path, monkeypatch, where):
    """The refusal must not catch an ordinary pilot or prod start (`clock` has no default object any more), and
    `hold_run_ids=` (a production hook) stays allowed. Every backend comes from the factory, which this test
    replaces for the four capabilities that would contact a real service."""
    root = live_dir(tmp_path, monkeypatch, where)
    qualify(load_registry(load_config(root)), "ito-agent")
    channel = FakeChannel()
    plant(
        monkeypatch,
        secrets=FakeSecretProvider(PILOT_SECRETS),
        store=MemoryStore,
        channel=channel,
        llm=ScriptedLLM(),
    )
    for kwargs in ({}, {"hold_run_ids": lambda: frozenset()}):
        app = app_mod.build(root, ["ito-agent"], **kwargs)
        assert app.config.environment == where
        assert app.executor is None
        assert app.approvals.channel is channel
        assert app.approvals.clock is now, "with no clock= given the real clock is used"
        assert app.runtime.hooks.hold_run_ids is kwargs.get("hold_run_ids")


# --- demo keeps every test keyword ------------------------------------------------------------------------------------


@pytest.fixture
def demo_dir(tmp_path):
    cfg_dir = make_cfg(tmp_path)
    qualify(load_registry(load_config(cfg_dir)))
    return cfg_dir


@pytest.mark.parametrize("name", NAMES)
def test_demo_accepts_each_test_keyword(demo_dir, monkeypatch, name):
    given = override(name, DEMO_SECRETS)
    if (
        name != "secrets"
    ):  # the fixture's fake secrets kind is empty: the build needs the fixture's one secret
        plant(monkeypatch, secrets=FakeSecretProvider(DEMO_SECRETS))
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


def test_demo_uses_a_zero_timeout_as_given(demo_dir):
    app = app_mod.build(
        demo_dir, ["test-agent"], secrets=FakeSecretProvider(DEMO_SECRETS), timeout_s=0.0
    )
    assert app.executor.timeout_s == 0.0, "timeout_s=0 was replaced by the configured timeout"


def test_the_factory_hands_a_falsy_secret_provider_to_the_backend(demo_dir):
    """The same class of slip one level down: `make` must not swap a falsy provider for an empty one."""
    from hadavin_sdk.backends.table import TABLE, Entry, KindSettings

    seen = []

    class Reads(KindSettings):
        kind: str = "q8a_reads"
        token_secret_name: str

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(TABLE["channel"], "q8a_reads", Entry(Reads, f"{__name__}:_reading_channel"))
        mp.setattr(_reading_channel, "seen", seen, raising=False)
        (name,) = DEMO_SECRETS  # the one secret name of the fixture, as a config file would give it
        settings = Reads.model_validate({"token_secret_name": name})
        factory_mod.make("channel", settings, FalsySecrets(DEMO_SECRETS))
    assert seen == [DEMO_SECRETS["fixture-token"]], "a falsy provider was replaced by an empty one"


def _reading_channel(settings, deps):
    _reading_channel.seen.append(deps.resolve(settings.token_secret_name))
    return FakeChannel()


# --- behaviour 2: a static Vault token is refused outside demo ---------------------------------------------------------

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


def vault_dir(tmp_path, where, capability, settings):
    """The pilot config with one Vault kind. Prod also gets what prod needs for other reasons (an anchor whose retention
    the client agreed, and a signer key that is not a file), so the Vault rule is the only refusal."""
    root = pilot_cfg(tmp_path, env=where)
    path = root / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if where == "prod":
        data["backends"]["anchor"] = PROD_ANCHOR
        data["backends"]["signer"] = KEY_FROM_SECRETS
    data["backends"][capability] = settings
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return root


def vault_message(where, capability) -> str:
    kind = VAULT_CASES[capability]["kind"]
    return (
        f"environment {where}: refused: {capability}: {kind} auth token "
        "(the default; set auth: kubernetes or auth: approle)"
    )


@pytest.mark.parametrize("written", [True, False], ids=["auth-written", "auth-left-out"])
@pytest.mark.parametrize("capability", ["secrets", "signer"])
@pytest.mark.parametrize("where", ["pilot", "prod"])
def test_a_static_vault_token_is_refused_in_pilot_and_prod(tmp_path, where, capability, written):
    settings = VAULT_CASES[capability] | ({"auth": "token"} if written else {})
    root = vault_dir(tmp_path, where, capability, settings)
    with pytest.raises(ConfigError, match=re.escape(vault_message(where, capability))):
        load_config(root)


@pytest.mark.parametrize(
    "auth", [{"auth": "kubernetes", "role": "hadavin"}, {"auth": "approle", "role_id": "r-1"}]
)
@pytest.mark.parametrize("capability", ["secrets", "signer"])
@pytest.mark.parametrize("where", ["pilot", "prod"])
def test_the_other_vault_sign_ins_are_accepted_in_pilot_and_prod(tmp_path, where, capability, auth):
    """The fixtures above are refused for the token only: the same config with another sign-in loads."""
    root = vault_dir(tmp_path, where, capability, VAULT_CASES[capability] | auth)
    cfg = load_config(root)
    assert getattr(cfg.backends, capability).auth == auth["auth"]


@pytest.mark.parametrize("written", [True, False], ids=["auth-written", "auth-left-out"])
@pytest.mark.parametrize("capability", ["secrets", "signer"])
def test_demo_accepts_a_static_vault_token(tmp_path, capability, written):
    cfg_dir = make_cfg(tmp_path)
    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["backends"][capability] = VAULT_CASES[capability] | ({"auth": "token"} if written else {})
    if capability == "signer":
        data["backends"]["audit"] = {"kind": "chain"}  # a signer needs the chained audit
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    cfg = load_config(cfg_dir)
    assert cfg.environment == "demo"
    assert getattr(cfg.backends, capability).auth == "token"
