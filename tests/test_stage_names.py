"""The stages are exactly demo, pilot and prod. The old first stage name is refused, never read as a stage, and a
class test keeps the old word out of every place that names a stage.

No stage is stored anywhere today, so there is no read site to test. The first change that stores one must map an old
value to demo on read for display only (never for a guard decision) and add a test through that real read site.

Rows: unknown stage and half-renamed flag refuse start; the class test looks at stage POSITIONS only; pilot and prod
refuse relaxed kinds; the live and prod-only guards fail closed on a value that is not a stage.
"""

import enum
import re
import typing
import unicodedata
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import yaml

from hadavin_sdk import app as app_mod
from hadavin_sdk import config as config_mod
from hadavin_sdk import deferred
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.app import build
from hadavin_sdk.approvals.channel import FakeChannel
from hadavin_sdk.backends import table
from hadavin_sdk.config import Config, ConfigError, _anchor_refusals, load_config, parse_backends
from hadavin_sdk.registry import _module_pin_problems, load_registry
from hadavin_sdk.stages import STAGES, is_live, is_prod
from tests.conftest import make_cfg, qualify
from tests.test_k3_pilot_env import pilot_cfg

# The old word is built from parts in this file: the class test never scans this file, but a grep for it should find
# only the places that matter.
OLD = "d" + "ev"
RENAMED = (
    "environment: "
    + OLD
    + " was renamed to demo; write environment: demo (allowed values: demo, pilot, prod)"
)
ROOT = Path(__file__).resolve().parents[1]
ALLOWED = "Input should be 'demo', 'pilot' or 'prod'"  # pydantic's text for a value outside the three stages


@pytest.fixture
def cfg_dir(tmp_path):
    """A copy of the fixture config. Defined here, not taken from conftest, because the mutation runner runs with --noconftest."""
    return make_cfg(tmp_path)


def _edit(cfg_dir, fn):
    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    fn(data)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def _set_env(cfg_dir, value):
    _edit(cfg_dir, lambda d: d.update(environment=value))


# --- the stage set -------------------------------------------------------------------------------------------------


def test_the_stages_are_exactly_demo_pilot_prod(tmp_path):
    assert STAGES == ("demo", "pilot", "prod")
    # the field's allowed values are the same tuple, not a second copy that can drift
    assert typing.get_args(Config.model_fields["environment"].annotation) == STAGES
    # the one place that decides "live": only exactly the first stage is relaxed, anything else is live
    assert [is_live(s) for s in STAGES] == [False, True, True], "is_live is wrong for a stage"
    assert [is_prod(s) for s in STAGES] == [False, False, True], "is_prod is wrong for a stage"
    nonstage = ("stag" + "ing", "Demo", OLD, "", None)
    assert all(is_live(v) for v in nonstage), "is_live is wrong for a value that is not a stage"
    assert all(is_prod(v) for v in nonstage), "is_prod is wrong for a value that is not a stage"
    assert not hasattr(deferred, "LIVE"), (
        "an allowlist of live stages is back: a new value would count as not live"
    )
    try:
        demo_sites = _live_by_site(tmp_path / "a", "demo")
    except (
        ConfigError
    ) as exc:  # a guard that treats demo as live refuses the demo config while it loads
        raise AssertionError(
            f"demo is not live, but a guard refused it as live: {exc}"[:200]
        ) from None
    assert demo_sites == {
        "registry": False,
        "deferred": False,
        "app": False,
    }, "demo is not live"
    for stage in ("pilot", "prod"):
        assert _live_by_site(tmp_path / stage, stage) == {
            "registry": True,
            "deferred": True,
            "app": True,
        }, f"{stage} is live"


def test_dev_is_refused_with_the_rename(cfg_dir):
    _set_env(cfg_dir, OLD)
    with pytest.raises(ConfigError) as via_load:
        load_config(cfg_dir)
    assert RENAMED in str(via_load.value), "the refusal does not name the rename"
    # a reader sees that one sentence and nothing of pydantic's wrapper around it
    assert str(via_load.value) == RENAMED, (
        "pydantic's wrapper is visible around the rename sentence"
    )
    # beside another problem in the same file: both are shown, the sentence still without the wrapper
    _edit(cfg_dir, lambda d: d.update(nonsense_key=1))
    with pytest.raises(ConfigError) as both:
        load_config(cfg_dir)
    assert RENAMED in str(both.value), "the rename sentence is lost beside another problem"
    # the other problem is shown, but an unknown key is pasted text, so its name is never shown (a secret can sit there)
    assert "<unknown key>: Extra inputs are not permitted" in str(both.value), (
        "the other problem is hidden by the rename sentence"
    )
    assert "nonsense_key" not in str(both.value), "an unknown key name is shown"
    assert "validation error" not in str(both.value), "pydantic's wrapper is visible"
    # direct construction gets the same text
    loaded = load_config(make_cfg(cfg_dir.parent / "again"))
    fields = {name: getattr(loaded, name) for name in type(loaded).model_fields}
    with pytest.raises(ValueError) as direct:
        Config(**{**fields, "environment": OLD})
    assert RENAMED in str(direct.value), "the refusal does not name the rename"


INEXACT = [
    "Demo",
    "DEMO",
    " demo",
    "demo ",
    "demo-eu",
    "uat",
    "staging",
    "development",
    "test",
    "",
    "stage",
    # the old word in other spellings: refused by the allowed-values rule, like any other non-stage
    "Dev",
    "DEV",
    " dev",
    "dev\n",
    "d"
    + chr(0x0435)
    + "v",  # the old word with a Cyrillic e: no rename hint, only the allowed-values refusal
    # six look-alikes and invisible characters, built from code points (no literal look-alike in this file); the
    # allowed-values rule in pydantic refuses the rest of the family, so these are the ones a "tidy" step would let in
    "d" + chr(0x0435) + "mo",  # Cyrillic small ie in place of e
    "".join(chr(0xFF00 + ord(c) - 0x20) for c in "demo"),  # fullwidth demo (NFKC gives demo)
    "de" + chr(0x200B) + "mo",  # zero-width space inside
    "demo" + chr(0x00A0),  # no-break space (NFKC gives a plain space)
    chr(0x217E) + "emo",  # small roman numeral five hundred (NFKC gives d)
    "demo" + chr(0x0301),  # demo plus a combining accent
    "demo\n",
    "~",
    "null",
    "None",
]


def test_values_are_compared_exactly_never_normalised(cfg_dir):
    """Case, spaces, a prefix such as demo-eu, and a project label (uat) are not the stage. Every spelling of the old
    word gets the rename sentence (a hint only; it is refused all the same)."""
    for value in INEXACT:
        _set_env(cfg_dir, value)
        try:
            cfg = load_config(cfg_dir)
        except ConfigError as exc:
            message = str(exc)
        else:
            raise AssertionError(
                f"a stage that is not exactly demo, pilot or prod was accepted: {value!r} -> {cfg.environment}"
            )
        # the allowed-values text (it lists demo, not dev), or the rename sentence for the old word's spellings
        want = RENAMED if value.strip().casefold() == OLD else ALLOWED
        assert want in message, f"{value!r}: refused for another reason: {message[:150]}"


@pytest.mark.parametrize("value", [None, 0, 1.5, True, ["demo"], {"demo": 1}])
def test_a_stage_that_is_not_a_string_is_refused(cfg_dir, value):
    _set_env(cfg_dir, value)
    with pytest.raises(ConfigError, match="environment") as err:
        load_config(cfg_dir)
    assert ALLOWED in str(err.value), f"{value!r}: not refused by the allowed-values rule"


def test_a_missing_stage_is_refused(cfg_dir):
    """Passes on the old code too (a missing field was always refused): it pins that no default fills the gap."""
    _edit(cfg_dir, lambda d: d.pop("environment"))
    with pytest.raises(ConfigError, match="environment\n  Field required"):
        load_config(cfg_dir)


@pytest.mark.parametrize("raw", ["~", "null", "Null", "NULL", ""])
def test_a_yaml_null_stage_is_refused(cfg_dir, raw):
    """`environment: ~` (and the other YAML spellings of null, and a bare key) reads as None: refused, never a default."""
    path = cfg_dir / "config.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("environment: demo", f"environment: {raw}"), encoding="utf-8")
    assert f"environment: {raw}" in path.read_text(encoding="utf-8")
    with pytest.raises(ConfigError, match="environment") as err:
        load_config(cfg_dir)
    assert ALLOWED in str(err.value), "a null stage is not refused by the allowed-values rule"


def test_demo_loads_and_pilot_and_prod_load_only_without_the_fakes(cfg_dir):
    assert load_config(cfg_dir).environment == "demo"
    for stage in ("pilot", "prod"):
        _set_env(cfg_dir, stage)
        with pytest.raises(ConfigError, match=f"environment {stage}: refused"):
            load_config(
                cfg_dir
            )  # a valid stage, refused for the fixture's fake kinds, not for its name


# --- demo-only kinds -----------------------------------------------------------------------------------------------

SIX_PAIRS = {
    ("llm", "fake"),
    ("channel", "fake"),
    ("secrets", "fake"),
    ("secrets", "env"),
    ("store", "memory"),
    ("audit", "local_dir"),
}


def test_demo_only_is_exactly_the_six_pairs():
    assert table.DEMO_ONLY == SIX_PAIRS
    assert isinstance(table.DEMO_ONLY, frozenset)


def test_demo_accepts_every_demo_only_kind(cfg_dir):
    try:
        cfg = load_config(cfg_dir)  # the fixture is the demo config and holds fakes
    except ConfigError as exc:
        raise AssertionError("demo config was refused: " + str(exc)) from None
    assert cfg.environment == "demo"
    held = {(c, s.kind) for c, s in cfg.backends.entries()}
    assert {("llm", "fake"), ("channel", "fake"), ("secrets", "fake"), ("store", "memory")} <= held
    assert ("audit", "local_dir") in held
    assert cfg.allow_insecure_loopback is True


def test_pilot_and_prod_refuse_every_relaxed_kind(cfg_dir):
    """The fake model, the memory store, the other fakes and the loopback switch."""
    for stage in ("pilot", "prod"):
        _set_env(cfg_dir, stage)
        with pytest.raises(ConfigError, match=f"environment {stage}: refused: ") as err:
            load_config(cfg_dir)
        for item in (
            "llm: fake",
            "store: memory",
            "audit: local_dir",
            "secrets: fake",
            "channel: fake",
            "allow_insecure_loopback",
        ):
            assert item in str(err.value), f"{stage} did not refuse {item}"


@pytest.mark.parametrize("pair", sorted(SIX_PAIRS))
def test_each_demo_only_pair_is_named_in_the_pilot_and_prod_refusal(cfg_dir, pair):
    """One test per pair, so a pair dropped from the set is named by its own failing test."""
    cap, kind = pair
    if pair == ("secrets", "env"):  # the fixture holds the other five
        _edit(cfg_dir, lambda d: d["backends"].update(secrets={"kind": "env"}))
    for stage in ("pilot", "prod"):
        _set_env(cfg_dir, stage)
        with pytest.raises(ConfigError, match=f"environment {stage}: refused: ") as err:
            load_config(cfg_dir)
        assert f"{cap}: {kind}" in str(err.value), f"{pair} was not refused in {stage}"


def test_demo_is_not_live(tmp_path):
    """A tool module with no pin loads in demo and is refused in pilot and prod; no restored-hash key is needed in demo."""
    cfg_dir = make_cfg(tmp_path)
    loaded = load_config(cfg_dir)
    fields = {name: getattr(loaded, name) for name in type(loaded).model_fields}
    fields["tool_modules"] = ["tests.fixtures.k5_tools"]
    demo = Config(**fields)
    assert _module_pin_problems(demo) == [], "demo was treated as live"
    for stage in ("pilot", "prod"):
        # the same config in a live stage is refused for its fake kinds before anything else; the pin check is a
        # separate function, so ask it directly with the stage changed.
        live = demo.model_copy(update={"environment": stage})
        problems = _module_pin_problems(live)
        assert any("no tool_module_hashes pin" in p for p in problems), (
            f"{stage} accepted an unpinned module"
        )
    # app.build in demo needs no restored hash key
    qualify(load_registry(load_config(cfg_dir)))
    build(cfg_dir, ["test-agent"], secrets=FakeSecretProvider({"fixture-token": "tok" + "-stage"}))


# --- the live guards fail closed -----------------------------------------------------------------------------------------


def _live_by_site(tmp_path, stage):
    """Ask each of the three places that decide 'live' (the unpinned tool module check in registry.py, the pilot and prod
    rules in deferred.py, the startup checks in app.py) about a config whose stage is `stage`, set on an unvalidated copy
    (model_copy skips the check that only demo, pilot and prod load). True: that place treated the config as live."""
    cfg_dir = make_cfg(tmp_path)
    cfg = load_config(cfg_dir)
    reg = load_registry(cfg)
    qualify(reg)
    copy = cfg.model_copy(
        update={"environment": stage, "tool_modules": ["tests.fixtures.k5_tools"]}
    )
    in_registry = any("no tool_module_hashes pin" in p for p in _module_pin_problems(copy))
    agent = SimpleNamespace(id="a", max_run_usd=None, data_class="internal", levels=None)
    probe = SimpleNamespace(config=copy, contracts={}, agents={"a": agent})
    in_deferred = any("is required in pilot and prod" in p for p in deferred.check(probe))
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(app_mod, "load_config", lambda _d: copy)
        mp.setattr(app_mod, "load_registry", lambda _c: reg)
        try:
            app_mod.build(
                cfg_dir,
                ["test-agent"],
                secrets=FakeSecretProvider({"fixture-token": "tok" + "-stage"}),
            )
            in_app = False
        except ConfigError as exc:
            in_app = "restored_hash_key_secret_name is required in pilot and prod" in str(exc)
    return {"registry": in_registry, "deferred": in_deferred, "app": in_app}


def test_a_value_that_is_not_a_stage_is_live_for_every_guard(tmp_path):
    """Config refuses such a value at load, but model_copy(update=...) and model_construct skip that check. The guards
    must then treat the config as live (strict), not as demo: only exactly demo is relaxed."""
    for n, bad in enumerate(["stag" + "ing", "Demo", "demo ", OLD, "", None, "uat"]):
        got = _live_by_site(tmp_path / str(n), bad)
        for site, live in got.items():
            assert live, f"{site} treated {bad!r} as not live (an allowlist of live stages)"


def _build_refusal(tmp_path, stage, edit=None, made=None, plant=None, **given):
    """What `app.build` says when a config whose stage is `stage` (the pilot config, real kinds only, changed by
    `edit`; for a stage other than pilot an unvalidated copy with the stage changed) is built with the keyword
    arguments `given`. '' when it builds. (Past the refusals this config stops at the empty secrets folder, also a
    ConfigError.) `made` collects the capabilities the build asked the factory for. `plant` is one extra kind for
    the table: (capability, kind, entry).

    No real Vault credential can be read or sent from here: the two environment variables a Vault sign-in reads are
    removed, and a backend whose settings are a Vault sign-in is never built (an empty test provider stands in)."""
    root = pilot_cfg(tmp_path)
    # the mounted-file secrets kind reads nothing until a secret is asked for
    (root / "secrets").mkdir()
    if edit:
        _edit(root, edit)
    with pytest.MonkeyPatch.context() as mp:
        mp.delenv("VAULT_TOKEN", raising=False)
        mp.delenv("VAULT_SECRET_ID", raising=False)
        if plant:
            mp.setitem(table.TABLE[plant[0]], plant[1], plant[2])
        cfg = load_config(root)
        reg = load_registry(cfg)
        copy = cfg.model_copy(update={"environment": stage})
        real_make = app_mod.make

        def recording(capability, settings, *args, **kwargs):
            if made is not None:
                made.append(capability)
            if hasattr(settings, "token_env"):
                return FakeSecretProvider({})
            return real_make(capability, settings, *args, **kwargs)

        mp.setattr(app_mod, "make", recording)
        mp.setattr(app_mod, "load_config", lambda _d: copy)
        mp.setattr(app_mod, "load_registry", lambda _c: reg)
        try:
            app_mod.build(root, ["ito-agent"], **given)
        except ConfigError as exc:
            return str(exc)
    return ""


class _FalsyChannel(FakeChannel):
    def __bool__(self) -> bool:
        return False


class _FalsyDict(dict):
    def __bool__(self) -> bool:
        return False


def _fixed_clock():
    return None


def _echo(_args):
    return "x"


def test_pilot_and_prod_refuse_a_test_object_handed_to_build(tmp_path):
    """`secrets=`, `channel=`, `detector=`, `llm=`, `clock=` and `timeout_s=` hand `build` an object in place of a
    configured part. That is for tests: only exactly demo accepts it, and an object that is falsy counts as given.
    Each keyword and each stage has its own test in tests/test_q8a_live_overrides.py; this one needs no database and
    no conftest fixture."""
    backend = "{0}= is for tests; configure backends.{0} in pilot and prod"
    other = "{0}= is for tests; it is refused in pilot and prod"
    for n, stage in enumerate(["pilot", "prod", "stag" + "ing", "Demo", "", None]):
        got = _build_refusal(tmp_path / str(n), stage, channel=FakeChannel())
        assert got == backend.format("channel"), (
            f"a live build took a test object ({stage!r}): {got[:80]!r}"
        )
    six = {
        "secrets": (FakeSecretProvider({}), backend),
        "channel": (FakeChannel(), backend),
        "detector": (object(), backend),
        "llm": (object(), backend),
        "clock": (_fixed_clock, other),
        "timeout_s": (2.5, other),
    }
    for name, (value, text) in six.items():
        got = _build_refusal(tmp_path / name, "pilot", **{name: value})
        assert got == text.format(name), f"a live build took the keyword {name}=: {got[:80]!r}"
    falsy = _FalsyChannel()
    got = _build_refusal(tmp_path / "falsy", "pilot", channel=falsy)
    assert not falsy and got == backend.format("channel"), (
        f"a live build took a falsy test object: {got[:80]!r}"
    )


def test_pilot_and_prod_refuse_sources_and_tools_handed_to_build(tmp_path):
    """`sources=` and `tools=` hand `build` objects that no config names. They count as given when they are not None:
    a mapping that is falsy, and an empty mapping, are refused like any other."""
    cases = {
        "sources": ("sources= is for tests", {"s": object()}),
        "tools": ("tools= (plain callables) is for replay and tests", {"echo": _echo}),
    }
    n = 0
    for stage in ("pilot", "prod", "stag" + "ing"):
        for name, (want, entries) in cases.items():
            for value in (entries, _FalsyDict(entries), {}):
                n += 1
                got = _build_refusal(tmp_path / str(n), stage, **{name: value})
                assert got.startswith(want), (
                    f"a live build took {name}= ({stage!r}, {type(value).__name__} of "
                    f"{len(value)}): {got[:80]!r}"
                )


def test_demo_refuses_a_timeout_that_is_out_of_range(tmp_path):
    """The demo executor's timeout has ONE rule on both routes, the `timeout_s=` keyword of `build` (demo only: pilot
    and prod refuse the keyword itself) and the config field `executor_timeout_s`: an int or float, not True or False,
    from one millisecond to one hour."""
    least, most = 0.001, 3600
    rule = "must be an int or float between 0.001 and 3600"
    cfg_dir = make_cfg(tmp_path / "keyword")
    qualify(load_registry(load_config(cfg_dir)))
    secrets = FakeSecretProvider({"fixture-token": "tok" + "-timeout"})
    for value in (0, -1, float("inf"), most + 1, True, 1e-9):
        try:
            build(cfg_dir, ["test-agent"], secrets=secrets, timeout_s=value)
            got = ""
        except ConfigError as exc:
            got = str(exc)
        assert got == "timeout_s= " + rule, f"demo took timeout_s={value!r}: {got[:80]!r}"
    for value in (least, most):
        app = build(cfg_dir, ["test-agent"], secrets=secrets, timeout_s=value)
        assert app.executor.timeout_s == value
    # the same rule in the config file, written as a config file holds the value
    for n, text in enumerate([f"{most}.1", ".inf", "0", "true", "'5'", "1.0e-9"]):
        in_file = make_cfg(tmp_path / f"file{n}")
        path = in_file / "config.yaml"
        path.write_text(
            path.read_text(encoding="utf-8") + f"\nexecutor_timeout_s: {text}\n", encoding="utf-8"
        )
        try:
            got = f"loaded as {load_config(in_file).executor_timeout_s}"
        except ConfigError as exc:
            got = str(exc)
        assert "executor_timeout_s" in got and rule in got, (
            f"the config took executor_timeout_s: {text} ({got[:60]!r})"
        )
    from hadavin_sdk import defaults

    assert (defaults.EXECUTOR_TIMEOUT_MIN_S, defaults.EXECUTOR_TIMEOUT_MAX_S) == (least, most), (
        "a bound changed: the rule sentence above and the CHANGELOG name them"
    )


VAULT_KINDS = {
    "secrets": {"kind": "vault", "address": "https://vault.example"},
    "signer": {
        "kind": "vault_transit",
        "address": "https://vault.example",
        "key_name": "k",
        "key_version": 1,
    },
}
VAULT_FIX = "(the default; set auth: kubernetes (recommended) or auth: approle)"


def _never_built(settings, deps):
    raise AssertionError("the planted kind must be refused before it is built")


def test_pilot_and_prod_refuse_a_static_vault_token(tmp_path):
    """The Vault kinds sign in with a static token unless the config says otherwise (`auth: token` is the default).
    A pilot or prod BUILD refuses that, written or left out, before any backend is made, for the two kinds and for
    any new kind built on the same settings class; the other sign-ins are not refused. The config itself loads (the
    one-off commands that only load it, such as the kill switch, keep working), and demo keeps the token."""
    n = 0
    for stage in ("pilot", "prod", "stag" + "ing"):
        for cap, settings in VAULT_KINDS.items():
            for extra in ({}, {"auth": "token"}):
                n += 1

                def use(data, cap=cap, settings=settings, extra=extra):
                    data["backends"][cap] = settings | extra

                want = f"environment {stage}: refused: {cap}: {settings['kind']} auth token {VAULT_FIX}"
                made: list[str] = []
                # _build_refusal loads the config first: a loader that refuses the token fails there
                got = _build_refusal(tmp_path / str(n), stage, use, made)
                assert got == want, (
                    f"a static Vault token was accepted for {cap} ({stage}, {extra}): {got[:80]!r}"
                )
                assert made == [], f"a backend was made before the Vault refusal: {made}"

    # a third kind built on the shared settings class, under a name the check has never seen
    class ThirdKind(table.VaultConnection):
        kind: str = "third_vault_kind"

    entry = table.Entry(ThirdKind, f"{__name__}:_never_built")
    third = {"kind": "third_vault_kind", "address": "https://vault.example"}
    got = _build_refusal(
        tmp_path / "third",
        "pilot",
        lambda d: d["backends"].update(channel=third),
        plant=("channel", "third_vault_kind", entry),
    )
    assert got == f"environment pilot: refused: channel: third_vault_kind auth token {VAULT_FIX}", (
        f"a static Vault token was accepted for a new kind built on the Vault settings: {got[:80]!r}"
    )
    # the other two sign-ins are not a static token
    for extra in ({"auth": "kubernetes", "role": "r"}, {"auth": "approle", "role_id": "r-1"}):
        got = _build_refusal(
            tmp_path / extra["auth"],
            "pilot",
            lambda d, extra=extra: d["backends"].update(secrets=VAULT_KINDS["secrets"] | extra),
        )
        assert "auth token" not in got, (
            f"a Vault sign-in that is not a static token was refused ({extra['auth']}): {got[:80]!r}"
        )
    demo = make_cfg(tmp_path / "demo")
    _edit(demo, lambda d: d["backends"].update(secrets=VAULT_KINDS["secrets"]))
    assert load_config(demo).backends.secrets.auth == "token", "demo refused a static Vault token"


def test_pilot_and_prod_refuse_a_time_or_a_step_list_handed_to_the_tick(tmp_path):
    """`run_tick(app, now=...)` sets the time of the approval sweep, the stuck-run check and the evidence purge;
    `run_tick(app, steps=...)` replaces the steps, so a tick could return 0 with no sweep and no purge. Both are for
    tests: only exactly demo accepts them, and an empty step list counts as given."""
    from hadavin_sdk.runtime.tick import STEPS, TickStep, run_tick

    cfg_dir = make_cfg(tmp_path)
    qualify(load_registry(load_config(cfg_dir)))
    app = build(
        cfg_dir, ["test-agent"], secrets=FakeSecretProvider({"fixture-token": "tok" + "-tick"})
    )
    at = app.approvals.clock()
    ran: list[str] = []
    step = TickStep("recorded", 0, lambda _ctx: ran.append("recorded"))

    def refusal(**given) -> str:
        try:
            run_tick(app, **given)
        except ConfigError as exc:
            return str(exc)
        return ""

    assert refusal(now=at) == "", "demo refused a time handed to the tick"
    assert refusal(steps=[step]) == "" and ran == ["recorded"], (
        "demo refused a step list handed to the tick"
    )
    ran.clear()
    no_time = "now= is for tests; it is refused in pilot and prod"
    no_steps = "steps= is for tests; it is refused in pilot and prod"
    for stage in ("pilot", "prod"):
        app.config = app.config.model_copy(update={"environment": stage})
        got = refusal(now=at)
        assert got == no_time, f"a live tick took a time handed to it ({stage!r}): {got[:80]!r}"
        got = refusal(steps=[step])
        assert got == no_steps and ran == [], (
            f"a live tick took a step list handed to it ({stage!r}): {got[:80]!r}, ran {ran}"
        )
        got = refusal(steps=[])
        assert got == no_steps, f"a live tick took an empty step list ({stage!r}): {got[:80]!r}"
        assert refusal(now=at, steps=[]) == no_time, "with both given, now= is the one named"
    for stage in ("stag" + "ing", "Demo", "", None):
        app.config = app.config.model_copy(update={"environment": stage})
        got = [refusal(now=at), refusal(steps=[step])]
        assert got == [no_time, no_steps] and ran == [], (
            f"the tick treated {stage!r} as not live (an allowlist of live stages): {got}"
        )
    # one level down: the context that carries the time into the steps, and a stand-in object in its place
    from datetime import timedelta

    from hadavin_sdk.runtime import tick as tick_mod

    ahead = at + timedelta(days=500)
    purged: list[str] = []
    real_purge = app.store.purge_tool_calls
    app.store.purge_tool_calls = lambda *a, **k: purged.append("tool calls") or real_purge(*a, **k)

    def by_hand(ctx_of) -> str:
        try:
            tick_mod.purge_evidence(ctx_of())
        except ConfigError as exc:
            return str(exc)
        return ""

    app.config = app.config.model_copy(update={"environment": "demo"})
    assert by_hand(lambda: tick_mod.TickContext(app, at)) == "" and purged, (
        "demo refused a tick context with a time handed to it"
    )
    purged.clear()
    for stage in ("pilot", "prod"):
        app.config = app.config.model_copy(update={"environment": stage})
        got = by_hand(lambda: tick_mod.TickContext(app, ahead))
        assert got == tick_mod.NO_GIVEN_TIME_COPY and got.startswith(no_time) and purged == [], (
            f"a live tick step took a time handed to its context ({stage!r}): {got[:60]!r}, {purged}"
        )
        got = by_hand(lambda: SimpleNamespace(app=app, now=ahead, results={}))
        assert got == no_time and purged == [], (
            f"a live tick step took a stand-in context with a time ({stage!r}): {got[:60]!r}, {purged}"
        )

        def spec_mock():
            mock = MagicMock(spec=tick_mod.TickContext)
            mock.app, mock.now = app, ahead
            return mock

        got = by_hand(spec_mock)
        assert got == no_time and purged == [], (
            f"a live tick step took a Mock(spec=TickContext) with a time ({stage!r}): {got[:60]!r}, {purged}"
        )
    with pytest.raises(TypeError, match="cannot be subclassed"):

        class _Sub(
            tick_mod.TickContext
        ):  # a subclass could skip the refusal in its own __post_init__
            def __post_init__(self) -> None:
                pass

        raise AssertionError("a subclass of TickContext was allowed")
    for stage in ("stag" + "ing", "Demo", "", None):
        app.config = app.config.model_copy(update={"environment": stage})
        got = by_hand(lambda: tick_mod.TickContext(app, ahead))
        assert got == tick_mod.NO_GIVEN_TIME_COPY and got.startswith(no_time) and purged == [], (
            f"the tick context treated {stage!r} as not live (an allowlist of live stages): {got[:60]!r}"
        )
        got = by_hand(lambda: SimpleNamespace(app=app, now=ahead, results={}))
        assert got == no_time and purged == [], (
            f"the tick step treated {stage!r} as not live for a stand-in context: {got[:60]!r}"
        )
    app.config = app.config.model_copy(update={"environment": "pilot"})
    assert by_hand(lambda: tick_mod.TickContext(app)) == "" and purged, (
        "a live tick context with no time handed to it (the app's clock) must work"
    )
    # a tick with nothing handed to it runs every step of STEPS: asked of a fresh app, so each step must be new
    fresh = build(
        cfg_dir, ["test-agent"], secrets=FakeSecretProvider({"fixture-token": "tok" + "-tick"})
    )
    fresh.config = fresh.config.model_copy(update={"environment": "pilot"})
    assert not any(fresh.store.get_tick_state(s.name) for s in STEPS)
    assert run_tick(fresh) == 0, "a live tick with nothing handed to it must run"
    not_run = [s.name for s in STEPS if fresh.store.get_tick_state(s.name) is None]
    assert not_run == [], f"a live tick did not run these steps of STEPS: {not_run}"


def test_pilot_and_prod_refuse_a_tick_whose_step_list_lacks_a_built_in_step(tmp_path):
    """`runtime.tick.STEPS` is the list a deployment appends a step to. Outside demo a tick refuses to run when a
    built-in step is no longer in it (a cut or emptied list would return 0 with no sweep and no purge); an appended
    step runs; demo runs the list as it is."""
    from hadavin_sdk.runtime import tick as tick_mod

    cfg_dir = make_cfg(tmp_path)
    qualify(load_registry(load_config(cfg_dir)))
    built_in = list(tick_mod.STEPS)

    def tick_with(steps, stage):
        """(what the tick said or returned, the built-in steps that ran) for a fresh app whose stage is `stage`."""
        app = build(
            cfg_dir, ["test-agent"], secrets=FakeSecretProvider({"fixture-token": "tok" + "-steps"})
        )
        app.config = app.config.model_copy(update={"environment": stage})
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(tick_mod, "STEPS", steps)
            try:
                said = tick_mod.run_tick(app)
            except ConfigError as exc:
                said = str(exc)
        return said, [s.name for s in built_in if app.store.get_tick_state(s.name) is not None]

    without_purge = [s for s in built_in if s.name != "purge_evidence"]
    for stage in ("pilot", "prod", "stag" + "ing", None):
        got = tick_with(without_purge, stage)
        assert got == ("a built-in tick step is missing: purge_evidence", []), (
            f"a live tick ran without a built-in step ({stage!r}): {got}"
        )
        got = tick_with([], stage)
        assert got[0].startswith("a built-in tick step is missing: sweep, ") and got[1] == [], (
            f"a live tick ran an emptied step list ({stage!r}): {got}"
        )
    ran: list[str] = []
    extra = tick_mod.TickStep("extra_step", 0, lambda _ctx: ran.append("extra_step"))
    got = tick_with([*built_in, extra], "pilot")
    assert got == (0, [s.name for s in built_in]) and ran == ["extra_step"], (
        f"a live tick did not run an appended step with every built-in step: {got}, {ran}"
    )
    got = tick_with(without_purge, "demo")
    assert got == (0, [s.name for s in without_purge]), f"demo did not run the list as it is: {got}"
    # A second step with a built-in name would overwrite the built-in step's outcome (results and the tick_state
    # row are kept by name), so a failed built-in step would be recorded as ok.
    twice = tick_mod.TickStep("purge_evidence", 0, lambda _ctx: None)
    for stage in ("pilot", "prod", "stag" + "ing", None):
        got = tick_with([*built_in, twice], stage)
        assert got == ("a tick step name is used twice: purge_evidence", []), (
            f"a live tick ran a step list with a name used twice ({stage!r}): {got}"
        )
    got = tick_with([*built_in, twice], "demo")
    assert got[0] == 0, f"demo did not run the list as it is: {got}"


ANCHOR = {"kind": "s3_object_lock", "bucket": "b", "region": "r"}
KEY_FILE = {"kind": "ed25519_local", "private_key_path": "k.pem"}
KEY_SECRET = {"kind": "ed25519_local", "private_key_secret_name": "audit-key"}


def _backends(anchor, signer):
    raw = {"signer": signer, "anchor": anchor, "audit": {"kind": "chain"}}
    return parse_backends({**raw, "llm": {"kind": "fake", "recorded_dir": "r"}}, Path("."))


def test_a_value_that_is_not_a_stage_gets_the_prod_only_rules():
    """model_copy and model_construct skip the check that only demo, pilot and prod load. The prod-only rules (no local
    key file, an anchor whose retention the client agreed, no signer or anchor of kind none) must then apply, as in
    prod; and COMPLIANCE (undeletable) stays allowed in exactly prod."""
    acked = ANCHOR | {"retention_ack": True}
    cases = [(acked, KEY_FILE), ("none", KEY_FILE), (ANCHOR, KEY_SECRET)]
    for (
        anchor,
        signer,
    ) in cases:  # each is refused in prod, accepted in pilot: the rule is prod-only
        assert _anchor_refusals("prod", _backends(anchor, signer)), (
            "the case must be refused in prod"
        )
        assert _anchor_refusals("pilot", _backends(anchor, signer)) == [], (
            "the case must pass pilot"
        )
    compliance = _backends(acked | {"mode": "COMPLIANCE"}, KEY_SECRET)
    assert _anchor_refusals("prod", compliance) == [], "prod refused COMPLIANCE with retention_ack"
    for bad in ("stag" + "ing", "Prod", "prod ", "", None):
        for anchor, signer in cases:
            found = _anchor_refusals(bad, _backends(anchor, signer))
            assert found, f"{bad!r}: no prod-only rule applied to {anchor} / {signer}"
            assert found == _anchor_refusals("prod", _backends(anchor, signer)), (
                f"{bad!r}: not as prod"
            )
        assert any("COMPLIANCE outside prod" in r for r in _anchor_refusals(bad, compliance)), (
            f"{bad!r}: COMPLIANCE was allowed outside the three stages"
        )


# --- fail closed on a half-renamed flag ----------------------------------------------------------------------


def test_no_old_spelling_of_the_demo_only_flag_is_left():
    assert not hasattr(table, "DE" + "V_ONLY"), (
        "half-renamed: the old flag name still exists next to DEMO_ONLY"
    )
    assert not hasattr(config_mod, "DE" + "V_ONLY")
    assert hasattr(table, "DEMO_ONLY") and hasattr(config_mod, "DEMO_ONLY")


@pytest.mark.parametrize("key", [OLD + "_only", "demo_only", "demo", OLD, "stage"])
def test_a_config_key_for_either_spelling_of_the_flag_refuses_start(cfg_dir, key):
    """Config has no such key; the strict model refuses it, so a half-renamed pair never starts. The refusal says an
    unknown key was found and where (the parent path), never the key's own text (a secret can sit in a key)."""
    _edit(cfg_dir, lambda d: d.update({key: True}))
    with pytest.raises(ConfigError, match="<unknown key>") as refused:
        load_config(cfg_dir)
    assert "Extra inputs are not permitted" in str(refused.value)


def test_both_spellings_of_the_stage_together_refuse_start(cfg_dir):
    """`environment: demo` beside an old-spelling key is refused (strict keys), never read as allowed."""
    _edit(cfg_dir, lambda d: d.update({"environment_" + OLD: "demo"}))
    with pytest.raises(ConfigError, match="<unknown key>") as refused:
        load_config(cfg_dir)
    assert "environment_" + OLD not in str(refused.value)


# --- the class test, stage POSITIONS only ------------------------------------------------------------------
# The old word (dev) and its siblings (staging, the bare stage) must not name a stage anywhere. A word is "used as a
# stage" in a position: a value after a stage-like name (config, CLI, env var, enum member), a quoted string literal
# (dict key, list or set member on any line, case label, conditional), a member of a stage list. Prose such as "the
# demo stage", "developer", "stddev" and a dataset split are not positions; the data splits are listed one exact line at
# a time in tests/stage_exemptions.tsv, each with its reason.

_W = r"(?<![A-Za-z0-9])" + OLD + r"(?![A-Za-z0-9])"  # the old word as a whole word
_ANY = r"(?<![A-Za-z0-9])(?:" + OLD + r"|staging|stage)(?![A-Za-z0-9])"  # the old word or a sibling
_STAGE = r"(?:pilot|prod|production|demo)"
_Q = r"[`'\"]?"  # a quote or backtick around the word
_NAME = r"(?<![A-Za-z0-9])(?:env(?:ironment)?|stage|tier|profile|mode)(?![A-Za-z0-9])"
_BEFORE = r"(?:in|for|outside|than|kept in|refused in)"
_AFTER = r"(?:only|executor|stage|tier|environment|config|app|runtime|slice|install)"
# (name, regex). The first three look for the old word and its siblings; the rest for the old word only.
POSITIONS = {
    # `environment: dev`, `ENV=dev`, `APP_ENV=dev`, `--env dev`, `STAGE_DEV`, `Environment.DEV`, `"mode": "dev"`
    "value after a stage name": re.compile(_NAME + r"[^A-Za-z0-9\n]{1,4}" + _ANY, re.IGNORECASE),
    # a quoted literal: `== "dev"`, `{"dev": 1}`, `case "dev":`, `"dev" if x`, a set member alone on its line
    "quoted literal": re.compile(r"[`'\"](?:" + OLD + r"|staging|stage)[`'\"]", re.IGNORECASE),
    # beside another stage in a list: `dev|pilot|prod`, `demo, dev`, a YAML list item `- dev`
    "list member": re.compile(
        _ANY
        + r"\s*[,|/;]\s*"
        + _STAGE
        + r"\b|\b"
        + _STAGE
        + r"\s*[,|/;]\s*"
        + _ANY
        + r"|^\s*-\s+"
        + _ANY
        + r"\s*$",
        re.IGNORECASE,
    ),
    "flag or helper name": re.compile(
        _W
        + r"_(?:only|cfg|config|env|stage|tier|mode|app|runtime)\b|\b(?:in|outside|is|for|not)_"
        + OLD
        + r"(?![A-Za-z0-9])|_"
        + OLD
        + r"(?:_only)?\(",
        re.IGNORECASE,
    ),
    "stage phrase": re.compile(
        r"\b" + _BEFORE + r" " + _Q + OLD + r"(?![A-Za-z0-9])|" + _W + _Q + r" " + _AFTER + r"\b",
        re.IGNORECASE,
    ),
    "url host": re.compile(r"://" + OLD + r"\.|://[^/\s]*-" + OLD + r"\.", re.IGNORECASE),
    "heading": re.compile(r"^#{1,6} .*" + _W, re.IGNORECASE),
}
# Every file of these types below these folders, and in the repo root except the three skipped by name (history, the
# packaging group called dev, a lock file). Not scanned by type: .jsonl, the ask-your-data gold data (42 records hold the
# data split in a tier field).
SCANNED = ("src", "tests", "docs", "demos", ".github", "tools")
TYPES = (
    ".py",
    ".md",
    ".txt",
    ".toml",
    ".json",
    ".yaml",
    ".yml",
    ".sql",
    ".properties",
    ".cfg",
    ".ini",
)
SKIPPED_ROOT = ("CHANGELOG.md", "pyproject.toml", "uv.lock")
EXEMPT_FILE = ROOT / "tests" / "stage_exemptions.tsv"
SELF = Path(__file__).resolve()
# Letters that look like Latin ones, as code points (no look-alike in this file). NFKC and casefold cover fullwidth,
# roman-numeral and capital forms. A plain list until the shared fold (P1a) is merged.
CONFUSABLES = {
    0x0435: "e",
    0x0501: "d",
    0x0475: "v",
    0x03BD: "v",
    0x0455: "s",
    0x0456: "i",
    0x0430: "a",
    0x0261: "g",
}
INVISIBLE = re.compile(
    "[" + "".join(map(chr, (0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0xAD))) + "]"
)


def _exemptions() -> dict:
    """(file, exact stripped line) -> reason, from the tsv. Real non-stage uses only: a data split, a tool name."""
    rows = [r.split("\t") for r in EXEMPT_FILE.read_text(encoding="utf-8").splitlines() if r]
    assert all(len(r) == 3 for r in rows), (
        "a row of stage_exemptions.tsv is not file TAB line TAB reason"
    )
    return {(f, line): why for f, line, why in rows}


def _fold(line: str) -> str:
    """The line as a reader sees it: NFKC, casefold, invisible characters out, look-alike letters made Latin."""
    folded = unicodedata.normalize("NFKC", line).casefold()
    return INVISIBLE.sub("", folded).translate(CONFUSABLES)


def _hits(line: str, markdown: bool = True) -> list[str]:
    """Names of the positions in `line`. A heading is a position in a Markdown file only (a `#` line in code is a comment)."""
    line = re.sub(
        r"\bfor \w+ in " + OLD + r"\b", "", _fold(line)
    )  # `for row in dev`: a dataset split
    return [n for n, rx in POSITIONS.items() if rx.search(line) and (markdown or n != "heading")]


def _scan_text(rel: str, text: str, exempt: dict | None = None) -> tuple[list[str], set]:
    """Hits in one file's text; a line that is exactly an exempt line is excused and its entry is marked used."""
    exempt, out, used = _exemptions() if exempt is None else exempt, [], set()
    for number, line in enumerate(text.splitlines(), 1):
        names = _hits(line, rel.endswith(".md"))
        if names and (rel, line.strip()) in exempt:
            used.add((rel, line.strip()))
            names = []
        if names:
            out.append(f"{rel}:{number} [{', '.join(names)}] {line.strip()[:100]}")
    return out, used


def _scan() -> tuple[list[str], set]:
    """(hits, the exemption entries that matched a line)."""
    paths = [p for folder in SCANNED for p in (ROOT / folder).rglob("*")]
    paths += [p for p in ROOT.glob("*") if p.name not in SKIPPED_ROOT]
    paths = [
        p for p in paths if p.suffix in TYPES or p.name.startswith(".git")
    ]  # .gitleaks.toml, .gitignore
    out, used = [], set()
    for path in paths:
        if not path.is_file() or path in (SELF, EXEMPT_FILE) or "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        found, hit_entries = _scan_text(path.relative_to(ROOT).as_posix(), text)
        out += found
        used |= hit_entries
    return sorted(set(out)), used


def test_the_old_stage_word_is_gone():
    found, _ = _scan()
    assert not found, "the old stage word is still used as a stage:\n" + "\n".join(found)


def test_the_exemptions_have_no_stale_entry():
    """An entry that matches no line is stale and fails; each entry is one exact line of one file, with its reason."""
    _, used = _scan()
    exempt = _exemptions()
    assert used == set(exempt), f"stale entries: {sorted(set(exempt) - used)}"
    for (rel, _), why in exempt.items():
        assert why.strip() and (ROOT / rel).is_file(), rel


def test_a_stage_shaped_line_in_a_file_that_holds_an_exempt_line_still_fails():
    """Run the real scan on the real text of a file with an exempt line, plus one added line: the exempt line stays
    excused, the added line is a hit."""
    rel, line = "demos/ask-your-data/askdata/evalset.py", 'split: Literal["dev", "test"]'
    text = (ROOT / rel).read_text(encoding="utf-8")
    assert _scan_text(rel, text)[0] == [], "the file as it is should be clean"
    for added in (
        f"environment: {OLD}",
        f'ENV = "{OLD}"',
        f'split: Literal["{OLD}", "test", "pilot"]',
    ):
        found, used = _scan_text(rel, text + "\n" + added + "\n")
        assert len(found) == 1 and added in found[0], f"the added line was not found: {added}"
        assert used == {(rel, line)}


def _lookalike(word: str) -> str:
    """The word with its e written as a Cyrillic ie (a code point, so no look-alike literal in this file)."""
    return word.replace("e", chr(0x0435))


# One template per shape; {w} is each of the three words in turn (the old word, staging, the bare stage), {W} upper case.
SHAPES = [
    "environment: {w}",
    'environment="{w}"',
    '"environment": "{w}"',
    "ENV={w}",  # unquoted, and the CLI and CI forms
    "APP_ENV={w}",
    "docker run --env {w} app",
    "      env: {w}",
    "STAGE_{W}",  # an enum or constant name, and an enum member
    "Environment.{W}",
    "tier: {w}",
    "profile={w}",
    '"mode": "{w}"',
    'x = {{"{w}": 1}}',  # a dict key
    "    case '{w}':",
    "y = 1 if ok else '{w}'",  # a conditional expression
    '    "{w}",',  # a set or list member alone on its line
    'if env == "{w}":',
    "x = {w}|pilot|prod",
    "demo, {w}",
    "  - {w}",
]
# Only for the old word: "stage" and "staging" are ordinary words in these places.
OLD_ONLY = [
    "{W}_ONLY = frozenset()",
    "def {w}_cfg(tmp_path):",
    "def test_x_outside_{w}(cfg):",
    "kept in {w} for the tests",
    "kinds allowed only in `{w}`.",
    "a {w} executor",
    "https://{w}.example.org/x",
    "## Running in {w}",
]


@pytest.mark.parametrize("shape", SHAPES)
def test_the_scanner_finds_each_shape_for_each_word(shape):
    for word in (OLD, "staging", "stage"):
        line = shape.format(w=word, W=word.upper())
        assert _hits(line), f"not found: {line}"


@pytest.mark.parametrize("shape", OLD_ONLY)
def test_the_scanner_finds_each_old_word_only_shape(shape):
    line = shape.format(w=OLD, W=OLD.upper())
    assert _hits(line), f"not found: {line}"


FULLWIDTH = "".join(chr(0xFF00 + ord(c) - 0x20) for c in OLD)


@pytest.mark.parametrize(
    "word", [FULLWIDTH, _lookalike(OLD), "D" + chr(0x0435) + "V", OLD[0] + chr(0x200B) + OLD[1:]]
)
def test_the_scanner_finds_the_word_spelled_with_look_alike_letters(word):
    for line in (f"environment: {word}", f'x = "{word}"', f"demo, {word}"):
        assert _hits(line), f"not found: {line!r}"
    assert _hits(f"environment: {_lookalike('staging')}"), "staging with a look-alike letter"


@pytest.mark.parametrize(
    "line",
    [
        "a developer wrote this",
        "the device is on",
        "stddev = 3",
        "a real `vault server -" + OLD + "` in CI",
        f"the CI Vault {OLD} server",
        f"{OLD} split of the dataset",
        "(?:com|net|io|" + OLD + "|ai|cloud)",
        "[dependency-groups]",
        f'{OLD} = ["pytest"]',
        "Dev-tool constants",
        "environment variable HADAVIN_X",
        "environment: demo",
        f"for row in {OLD}:",
        "modern mode: developer",
        "stage: demo",
        "the demo stage and the pilot stage",
        "  - demo",
        f'default-groups = ["{OLD}x"]',
        f"mode: {OLD}elop",
        'pytest.mark.parametrize("test")',
    ],
)
def test_the_scanner_ignores_words_that_are_not_stage_positions(line):
    assert not _hits(line), f"false hit: {line}: {_hits(line)}"


@pytest.mark.parametrize("name", ["env", "environment", "tier", "stage", "profile", "mode"])
def test_the_reach_between_a_stage_name_and_the_old_word_is_four_characters(name):
    """`stage = "dev"` has four characters (space, equals, space, quote) between the words, `"mode": "dev"` has four
    as well: both found. Five is outside the position."""
    for sep in ('": "', ' = "', '"=: ', "':'", ": ", "="):
        assert _hits(name + sep + OLD), f"not found: {name}{sep}{OLD}"
    assert not _hits(name + " " * 5 + OLD), "the reach is four characters, not more"


# --- the redactor treats stage words as ordinary words, so `demo` joins them ----------------------------------


def test_the_redactor_does_not_sweep_the_stage_words_but_still_sweeps_secrets_and_other_names():
    from hadavin_sdk.guard.redact import _sweep

    for word in ("prod", "pilot", "demo", OLD):
        assert _sweep("<TENANT_1>", word) is None, f"{word} is swept like a name"
    assert _sweep("<TENANT_1>", "acme" + "corp") is not None
    assert _sweep("<SECRET_1>", "pilot") is not None, (
        "a secret that reads 'pilot' must still be swept"
    )
    assert _sweep("<SECRET_1>", "demo") is not None, (
        "a secret that reads 'demo' must still be swept"
    )


# --- a configuration error never shows the value that was refused (Q8a-1 fix batch 5, item 1) ------------------------
# The class: error text built from a refused value (a login inside base_url, a line of YAML, a duplicate key, the text
# of a wrapped exception, the cause printed under the error). The shared choke point is `config.config_error_text`
# plus `from None` at every site that wraps. Made-up credentials are built from parts.
PW = "Zq" + "9x" + "-pw-" + "4417"
USER = "svc" + "-user"
LOGIN_URL = "https://" + USER + ":" + PW + "@records.example.invalid/api"


def _everything_shown(exc: BaseException) -> str:
    """All the text a person could see for this error: its message, its repr, the cause and the whole traceback
    text with the chain (what the command line prints)."""
    import traceback

    return "\n".join(
        [
            str(exc),
            repr(exc),
            str(exc.__cause__),
            "".join(traceback.format_exception(exc)),
        ]
    )


def _refused(cfg_dir, *, edit=None, text=None, extra_file=None):
    """Load the config (and the registry) and return the ConfigError it raises."""
    if edit is not None:
        _edit(cfg_dir, edit)
    if text is not None:
        path = cfg_dir / "config.yaml"
        path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")
    if extra_file is not None:
        name, content = extra_file
        (cfg_dir / name).write_text(content, encoding="utf-8")
    with pytest.raises(ConfigError) as err:
        load_registry(load_config(cfg_dir))
    return err.value


def _assert_value_free(exc: ConfigError, *secrets: str) -> None:
    shown = _everything_shown(exc)
    for secret in secrets:
        assert secret not in shown, f"the error shows the refused value: {shown[:300]!r}"
    assert exc.__cause__ is None, "the cause (whose text may hold the value) is still attached"
    assert "errors.pydantic.dev" not in shown and "input_value" not in shown, shown[:300]


def test_a_login_inside_a_system_base_url_is_refused_without_showing_the_url(cfg_dir):
    exc = _refused(
        cfg_dir, edit=lambda d: d["systems"]["fixture-records"].update(base_url=LOGIN_URL)
    )
    assert "systems.fixture-records.base_url" in str(
        exc
    ) and "a URL must not contain a login" in str(exc)
    _assert_value_free(exc, PW, USER, LOGIN_URL, "records.example.invalid")


def test_a_system_base_url_that_is_not_https_is_refused_without_showing_the_url(cfg_dir):
    url = "http://" + USER + ":" + PW + "@10.1.2.3/api"
    exc = _refused(cfg_dir, edit=lambda d: d["systems"]["fixture-records"].update(base_url=url))
    _assert_value_free(exc, PW, USER, "10.1.2.3")
    plain = (
        "http://" + "host-" + PW + ".example.invalid/api"
    )  # no login: the https rule, still without the URL
    cfg2 = make_cfg(cfg_dir.parent / "second")
    exc = _refused(cfg2, edit=lambda d: d["systems"]["fixture-records"].update(base_url=plain))
    assert "base_url must be https" in str(exc)
    _assert_value_free(exc, PW, "host-")


def test_a_line_of_broken_yaml_is_not_quoted_in_the_error(cfg_dir):
    exc = _refused(cfg_dir, text='\nnote: "' + PW + " and no closing quote\nother: 1\n")
    assert re.search(r"not valid YAML \(line \d+, column \d+\)", str(exc)), str(exc)
    _assert_value_free(exc, PW, "no closing quote")


def test_a_line_of_broken_yaml_in_a_registry_file_is_not_quoted_in_the_error(cfg_dir):
    exc = _refused(cfg_dir, extra_file=("agents.yaml", "- id: [" + PW + "\n  status: {\n"))
    assert "not valid YAML" in str(exc), str(exc)
    _assert_value_free(exc, PW)


def test_a_duplicate_key_is_reported_by_line_only(cfg_dir):
    exc = _refused(cfg_dir, text="\n" + PW + ": 1\n" + PW + ": 2\n")
    assert re.fullmatch(r"duplicate key \(line \d+\)", str(exc)), str(exc)
    _assert_value_free(exc, PW)


def test_a_duplicate_id_in_a_registry_file_is_reported_by_entry_number_only(cfg_dir):
    ident = "person-" + PW + "@example.invalid"  # a personal e-mail address as an id
    content = f"- id: {ident}\n  kind: person\n- id: {ident}\n  kind: person\n"
    exc = _refused(cfg_dir, extra_file=("principals.yaml", content))
    assert "principals.yaml: duplicate id in entry 2" in str(exc), str(exc)
    _assert_value_free(exc, PW, "example.invalid")


def test_a_registry_validation_error_does_not_echo_the_value(cfg_dir):
    """`principals.yaml` models do not hide their input: pydantic's own text would print `input_value='...'`."""
    content = "- id: user:z\n  kind: " + PW + "\n"
    exc = _refused(cfg_dir, extra_file=("principals.yaml", content))
    assert "validation error" in str(exc), str(exc)
    _assert_value_free(exc, PW)


def test_a_backend_settings_error_does_not_echo_the_value_or_keep_the_cause(cfg_dir):
    exc = _refused(
        cfg_dir, edit=lambda d: d["backends"].update(detector=[{"kind": "regex", "threshold": PW}])
    )
    assert "backends.detector (regex)" in str(exc), str(exc)
    _assert_value_free(exc, PW)


def test_an_unknown_kind_or_capability_is_not_echoed(cfg_dir):
    exc = _refused(cfg_dir, edit=lambda d: d["backends"].update(channel={"kind": PW}))
    assert "unknown kind; known:" in str(exc), str(exc)
    _assert_value_free(exc, PW)
    cfg2 = make_cfg(cfg_dir.parent / "second")
    exc = _refused(cfg2, edit=lambda d: d["backends"].update({PW: "fake"}))
    assert "1 unknown capability name(s); known:" in str(exc), str(exc)
    _assert_value_free(exc, PW)


def test_an_unknown_source_kind_or_route_is_not_echoed(cfg_dir):
    exc = _refused(cfg_dir, edit=lambda d: d.update(sources={"s": {"kind": PW, "settings": {}}}))
    assert "source kind is unknown" in str(exc), str(exc)
    _assert_value_free(exc, PW)
    cfg2 = make_cfg(cfg_dir.parent / "second")

    def judge(d):
        d["routes"]["screen"] = dict(d["routes"]["default"], max_tokens=64)
        d["backends"]["detector"] = [{"kind": "regex"}, {"kind": "llm_judge", "route": PW}]

    exc = _refused(cfg2, edit=judge)
    assert "its route is not in routes" in str(exc), str(exc)
    _assert_value_free(exc, PW)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("case_insensitive_targets", ["Bad " + PW]),
        ("stored_kinds", [PW]),
        ("cluster_suffixes", ["." + PW]),
        ("https_ports", [70000 + 4417]),
    ],
)
def test_a_refused_list_entry_in_the_evidence_settings_is_counted_not_shown(cfg_dir, field, value):
    exc = _refused(cfg_dir, edit=lambda d: d.update(evidence={field: value}))
    assert f"evidence.{field}: 1 entries" in str(exc), str(exc)
    _assert_value_free(exc, PW, "74417")


def test_a_path_that_leaves_its_folder_is_refused_without_the_path(tmp_path):
    with pytest.raises(ConfigError) as err:
        config_mod.confined(tmp_path, "../" + PW)
    assert str(err.value) == "path escapes its folder"
    _assert_value_free(err.value, PW)


def test_any_other_error_while_loading_is_reduced_to_its_type(cfg_dir, monkeypatch):
    """The last-resort branch (`except (ValueError, TypeError, ...)` in load_config) never prints `str(exc)`."""

    def boom(*_a, **_k):
        raise ValueError("secret value " + PW)

    monkeypatch.setattr(config_mod, "parse_backends", boom)
    with pytest.raises(ConfigError) as err:
        load_config(cfg_dir)
    assert str(err.value) == "a value was refused (ValueError)"
    _assert_value_free(err.value, PW)


def test_the_error_text_function_keeps_a_yaml_position_and_drops_the_rest():
    with pytest.raises(yaml.YAMLError) as err:
        yaml.safe_load("a: '" + PW + "\nb: 1\n")
    assert PW in str(err.value), "the premise of the test: the YAML error itself quotes the value"
    text = config_mod.config_error_text(err.value)
    assert PW not in text and text.startswith("not valid YAML")


def test_a_live_tick_runs_the_step_list_its_checks_saw_even_if_the_list_is_edited_in_place(
    tmp_path,
):
    """One copy of `STEPS` is taken at the start of `run_tick` and serves the checks and the loop: a list cut in place
    after the checks (here by the first read of the store) must not change what runs."""
    from hadavin_sdk.runtime import tick as tick_mod

    cfg_dir = make_cfg(tmp_path)
    qualify(load_registry(load_config(cfg_dir)))
    app = build(
        cfg_dir, ["test-agent"], secrets=FakeSecretProvider({"fixture-token": "tok" + "-copy"})
    )
    app.config = app.config.model_copy(update={"environment": "pilot"})
    ran: list[str] = []
    steps = [
        tick_mod.TickStep(s.name, 0, lambda _c, n=s.name: ran.append(n)) for s in tick_mod.STEPS
    ]
    names = [s.name for s in steps]
    original = app.store.get_tick_state

    def cut_after_the_checks(name):
        steps[:] = steps[:1]
        return original(name)

    app.store.get_tick_state = cut_after_the_checks
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(tick_mod, "STEPS", steps)
        assert tick_mod.run_tick(app) == 0
    assert ran == names, f"the tick ran a list other than the one its checks saw: {ran}"


def test_a_refused_stored_kind_is_counted_not_shown(cfg_dir):
    exc = _refused(cfg_dir, edit=lambda d: d.update(evidence={"stored_kinds": [PW]}))
    assert "evidence.stored_kinds: 1 entries cannot be stored" in str(exc), str(exc)
    _assert_value_free(exc, PW)


# --- Q8a-1 batch 6: library error texts, the YAML reader, unknown keys and names -----------------------------------------
# Class 1: a library's own error text (here `urllib.parse.urlsplit`) copied into our error text. Class 2: a read site
# outside the one YAML reader. Class 3: a name or key taken from a file shown in an error text. Each test below fails
# on the head before this batch (3f3d4b6c); `tests/stage_mutants.py` (M16*) holds one mutant per guard.

WIDE_AT, WIDE_COLON = "＠", "："  # full-width `@` and `:`; under NFKC they become `@` and `:`
# a login written with full-width characters: `urlsplit` refuses it and quotes the whole host in its error text
WIDE_LOGIN_HOST = USER + WIDE_COLON + PW + WIDE_AT + "records.example.invalid"
WIDE_URL = "https://" + WIDE_LOGIN_HOST + "/api"
OPENAI_COMPAT = {"kind": "openai_compat", "base_url": WIDE_URL}
VAULT_WIDE = {"kind": "vault", "address": WIDE_URL}


def _set_backend(capability, settings):
    return lambda d: d["backends"].update({capability: settings})


@pytest.mark.parametrize(
    "edit",
    [
        lambda d: d["systems"]["fixture-records"].update(base_url=WIDE_URL),
        _set_backend("llm", OPENAI_COMPAT),
        _set_backend("secrets", VAULT_WIDE),
        _set_backend(
            "signer", {**VAULT_WIDE, "kind": "vault_transit", "key_name": "k", "key_version": 1}
        ),
        _set_backend(
            "anchor",
            {"kind": "s3_object_lock", "bucket": "b", "region": "r", "endpoint_url": WIDE_URL},
        ),
    ],
    ids=[
        "systems.base_url",
        "openai_compat.base_url",
        "vault.address",
        "vault_transit.address",
        "s3.endpoint_url",
    ],
)
def test_a_host_that_changes_under_nfkc_is_refused_without_its_text(cfg_dir, edit):
    """`urlsplit` raises a `ValueError` that holds the whole host, login included. It must never reach our error."""
    exc = _refused(cfg_dir, edit=edit)
    _assert_value_free(exc, PW, USER, "records.example.invalid", WIDE_AT, WIDE_COLON, "netloc")
    assert "not a valid URL" in str(exc), str(exc)


def test_the_one_url_splitter_gives_a_fixed_sentence_and_no_cause():
    from hadavin_sdk.safe_url import NOT_A_URL, InvalidUrl, safe_urlsplit

    for bad in (WIDE_URL, "https://[" + PW, "https://host:" + PW + "x/"):
        with pytest.raises(InvalidUrl) as err:
            safe_urlsplit(bad)
        assert str(err.value) == NOT_A_URL and err.value.__cause__ is None
        assert PW not in _everything_shown(err.value)
        assert isinstance(err.value, ValueError)
    assert safe_urlsplit("https://records.example.invalid:8443/x").port == 8443


def test_a_url_that_cannot_be_read_is_never_called_loginless_or_allowed():
    """The old `url_has_login` (removed: no production code used it) said False for a text it could not read; the one
    splitter every field uses, `config_urlsplit`, refuses it."""
    from hadavin_sdk.config import url_allowed
    from hadavin_sdk.safe_url import InvalidUrl, config_urlsplit

    with pytest.raises(InvalidUrl):
        config_urlsplit(WIDE_URL)
    assert url_allowed(WIDE_URL, True) is False


def test_no_module_splits_a_configured_url_without_the_safe_splitter():
    """The class: every `urlsplit` of a value that came from a file or a model goes through `safe_urlsplit`."""
    own = ROOT / "src" / "hadavin_sdk" / "safe_url.py"
    users = [
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "src").rglob("*.py")
        if p != own
        and re.search(
            r"\b(?:urlsplit|urlparse)\b",  # also `parse.urlsplit`, `up.urlsplit`, `import urlsplit as x`
            p.read_text(encoding="utf-8"),
        )
    ]
    assert users == [], f"these files split a URL themselves: {users}"


def test_the_one_yaml_reader_gives_a_value_free_error_for_every_caller():
    from hadavin_sdk.config import load_yaml

    with pytest.raises(ConfigError) as err:
        load_yaml("tool:\n  token: [" + PW + " no closing bracket\n")
    assert re.fullmatch(r"not valid YAML \(line \d+, column \d+\)", str(err.value)), str(err.value)
    _assert_value_free(err.value, PW)


@pytest.mark.parametrize(
    "name, content",
    [
        ("tools/test-agent.yaml", "- name: x\n  note: {a: 1, b: " + PW + "\n"),
        ("agents.yaml", "- id: x\n  note: [" + PW + "\n"),
        ("principals.yaml", "- id: x\n  note: '" + PW + "\n"),
        ("chains.yaml", "- id: x\n  note: {" + PW + "\n"),
        ("egress.yaml", "hosts: [" + PW + "\n"),
    ],
)
def test_a_broken_yaml_line_in_any_file_of_the_folder_is_not_quoted(cfg_dir, name, content):
    """`tools/<agent>.yaml` was read outside the guarded block and its YAML error quoted the line."""
    (cfg_dir / "tools").mkdir(exist_ok=True)
    exc = _refused(cfg_dir, extra_file=(name, content))
    assert re.search(r"not valid YAML \(line \d+, column \d+\)", str(exc)), str(exc)
    _assert_value_free(exc, PW)


def test_a_tool_file_that_is_not_utf8_is_reported_by_its_type_only(cfg_dir):
    (cfg_dir / "tools").mkdir(exist_ok=True)
    (cfg_dir / "tools" / "test-agent.yaml").write_bytes(b"- name: \xff\xfe" + PW.encode())
    with pytest.raises(ConfigError) as err:
        load_registry(load_config(cfg_dir))
    assert "UnicodeDecodeError" in str(err.value)
    _assert_value_free(err.value, PW)


# Unknown keys: the key text is what a person pasted, so it is never shown. Five places (the evidence probe rows).
KEY = PW
UNKNOWN_KEY_ROWS = {
    "config.yaml top level": lambda d: d.update({KEY: 1}),
    "backend setting": lambda d: d["backends"].update(channel={"kind": "fake", KEY: 1}),
    "systems entry": lambda d: d["systems"]["fixture-records"].update({KEY: 1}),
}


@pytest.mark.parametrize("row", sorted(UNKNOWN_KEY_ROWS))
def test_an_unknown_key_in_the_config_is_not_shown(cfg_dir, row):
    exc = _refused(cfg_dir, edit=UNKNOWN_KEY_ROWS[row])
    _assert_value_free(exc, KEY)
    assert "<unknown key>" in str(exc) and "Extra inputs are not permitted" in str(exc), str(exc)


@pytest.mark.parametrize(
    "name, content",
    [
        (
            "agents.yaml",
            "- id: test-agent\n  status: live\n  data_class: internal\n  model_route: default\n  prompt_file: prompts/test-agent.md\n  scope_allowed: []\n  max_steps: 4\n  budget_usd: {daily: '1.00', monthly: '10.00'}\n  "
            + KEY
            + ": 1\n",
        ),
    ],
)
def test_an_unknown_key_in_an_agent_entry_is_not_shown(cfg_dir, name, content):
    exc = _refused(cfg_dir, extra_file=(name, content))
    _assert_value_free(exc, KEY)
    assert "<unknown key>" in str(exc), str(exc)


def test_an_unknown_key_in_an_action_file_is_not_shown(cfg_dir):
    path = cfg_dir / "actions" / "lookup_record.yaml"
    path.write_text(path.read_text(encoding="utf-8") + KEY + ": 1\n", encoding="utf-8")
    with pytest.raises(ConfigError) as err:
        load_registry(load_config(cfg_dir))
    _assert_value_free(err.value, KEY)
    assert "<unknown key>" in str(err.value), str(err.value)


def test_a_mapping_key_that_is_not_a_plain_name_is_not_shown_in_the_place(cfg_dir):
    """`systems.<name>.base_url`: a name that is not a plain identifier (here with capital letters) is not shown."""
    exc = _refused(
        cfg_dir,
        edit=lambda d: d["systems"].update({KEY: {"base_url": 5}}),
    )
    _assert_value_free(exc, KEY)
    assert "systems.<not shown>.base_url" in str(exc), str(exc)


# Names as VALUES in the registry cross-check: the file and the field are said, the pasted name is not.
def _agent_entry(**over):
    entry = {
        "id": "test-agent",
        "status": "live",
        "data_class": "internal",
        "model_route": "default",
        "prompt_file": "prompts/test-agent.md",
        "scope_allowed": ["lookup_record"],
        "max_steps": 4,
        "budget_usd": {"daily": "1.00", "monthly": "10.00"},
    }
    entry.update(over)
    return yaml.safe_dump([entry])


@pytest.mark.parametrize(
    "over, said",
    [
        ({"model_route": PW}, "model_route is not one of the configured routes"),
        ({"scope_allowed": [PW]}, "scope_allowed entry 0 has no contract"),
    ],
)
def test_a_name_pasted_where_the_registry_expects_a_known_one_is_not_shown(cfg_dir, over, said):
    exc = _refused(cfg_dir, extra_file=("agents.yaml", _agent_entry(**over)))
    _assert_value_free(exc, PW)
    assert said in str(exc), str(exc)


def test_a_plain_looking_name_that_matched_nothing_is_not_shown_either(cfg_dir):
    """Round 7: a value that matched nothing is named by its field, not quoted, even when it looks like a plain
    identifier (a pasted token can look like one: `shown_name` is a shape filter, not a secret detector)."""
    exc = _refused(cfg_dir, extra_file=("agents.yaml", _agent_entry(model_route="no-such-route")))
    assert "agent test-agent: model_route is not one of the configured routes" in str(exc), str(exc)
    assert "no-such-route" not in _everything_shown(exc)


def test_the_name_filter_is_a_shape_and_membership_check_only():
    from hadavin_sdk.errors import NOT_SHOWN, shown_name

    assert (
        shown_name("lookup_record") == "lookup_record"
        and shown_name("k8s.pods-list") == "k8s.pods-list"
    )
    for fine in (
        "x" * 40,
        "a",
        "a.b-c_d9",
        "svc:test-agent",  # a colon is part of a real id
        "z" * 39,
        "tools.read-pods_v2",
        "k" + "0123456789" * 1 + "-" + "9876543210",  # digit runs under 20 are word-like
    ):  # 40 is the longest shown name (D-2322: letter first, at most 40 characters)
        assert shown_name(fine) == fine, fine
    cyrillic_a = "\u0430"  # looks like the Latin a
    for odd in (
        PW,
        "",
        "a b",
        "x" * 41,  # too long
        "x" * 64,
        "0",  # a digit first
        "1abc",
        "ａbc",
        "naïve",
        None,
        5,
        "Lookup",
        cyrillic_a + "bc",
        "ab" + cyrillic_a,
        "a\n",
    ):
        assert shown_name(odd) == NOT_SHOWN, odd


def test_a_name_with_a_long_run_of_hex_or_digits_is_not_shown_and_a_reference_that_matched_nothing_is_not_shown():
    """D-2322: word-like (letter first, at most 40 characters, no run of 20 or more hex or digit characters) AND the id
    of something that was loaded (a member of `loaded`, or of the names `loaded_ids` made active)."""
    from hadavin_sdk.errors import NOT_SHOWN, loaded_ids, shown_name

    for token in ("k" + "0123456789abcdef" * 2, "a" + "9" * 20, "tok-" + "deadbeef" * 3, "f" * 20):
        assert shown_name(token) == NOT_SHOWN, token  # hex-like or digit-run: a key, hash or token
    assert shown_name("z" + "9" * 19) == "z" + "9" * 19  # 19 digits: one short of the run limit
    assert shown_name("a" + "9" * 19) == NOT_SHOWN  # but `a` is a hex digit, so this run is 20
    assert shown_name("agent-a", ["agent-a"]) == "agent-a"
    assert shown_name("agent-b", ["agent-a"]) == NOT_SHOWN  # not a loaded id
    assert shown_name("agent-b", []) == NOT_SHOWN
    with loaded_ids(["agent-a"], {"chain-1": 1}):
        assert shown_name("agent-a") == "agent-a" and shown_name("chain-1") == "chain-1"
        assert shown_name("agent-b") == NOT_SHOWN
        with loaded_ids(["agent-b"]):  # groups add to the active names
            assert shown_name("agent-a") == "agent-a" and shown_name("agent-b") == "agent-b"
        assert shown_name("agent-b") == NOT_SHOWN  # and leave with their block
    assert shown_name("agent-b") == "agent-b"  # no active set: only the word-like test


def test_a_name_in_a_tool_manifest_problem_is_not_shown(cfg_dir):
    from hadavin_sdk.tools import ToolSpec, spec_problems

    spec = ToolSpec(
        name="a_tool", function="m:f", description="d", input_schema={"type": "object"},
        side_effect="none", hosts=(USER + ":" + PW + "@records.example.invalid",),
    )  # fmt: skip
    shown = " ".join(spec_problems(spec, ["m"]))
    assert "bare lowercase hostname" in shown and PW not in shown and USER not in shown, shown


def test_a_keyword_or_property_name_in_an_input_schema_is_not_shown():
    from hadavin_sdk.actions.contract import schema_problems

    shown = " ".join(
        schema_problems(
            {"type": "object", "properties": {PW: {"type": "string", PW + "k": 1, "pattern": "("}}}
        )
    )
    assert PW not in shown and "unsupported keyword <not shown>" in shown, shown
    assert PW not in " ".join(schema_problems({"type": PW}))


# Class 3b: a ValueError that a LIBRARY raised inside a validator quotes the value; only ours keep their sentence.
def test_a_library_value_error_in_a_validator_shows_its_type_only_but_our_sentence_stays():
    from pydantic import BaseModel, field_validator

    from hadavin_sdk.config import config_error_text

    class Probe(BaseModel):
        number: str

        @field_validator("number")
        @classmethod
        def _read(cls, v):
            int(v)  # the library's text: "invalid literal for int() with base 10: '<the value>'"
            return v

    with pytest.raises(Exception) as lib:
        Probe(number=PW)
    text = config_error_text(lib.value)
    assert PW not in text and "a value was refused (ValueError)" in text, text


def test_our_own_value_error_sentence_is_kept(cfg_dir):
    exc = _refused(cfg_dir, edit=lambda d: d.update(executor_timeout_s=0))
    assert "must be an int or float between 0.001 and 3600" in str(exc)


def test_the_rename_sentence_shows_no_unknown_key_beside_it(cfg_dir):
    _set_env(cfg_dir, OLD)
    _edit(cfg_dir, lambda d: d.update({KEY: 1}))
    with pytest.raises(ConfigError) as both:
        load_config(cfg_dir)
    assert RENAMED in str(both.value) and "<unknown key>: Extra inputs are not permitted" in str(
        both.value
    )
    _assert_value_free(both.value, KEY)


def test_the_given_time_refusal_is_true_for_a_direct_context_and_a_copy():
    """The copy sentence was attached to every refusal, so a direct `TickContext(app, t)` was told about replace()."""
    from hadavin_sdk.runtime import tick as tick_mod

    text = tick_mod.NO_GIVEN_TIME_COPY
    assert text.startswith(tick_mod.NO_GIVEN_TIME) and "TickContext(app)" in text
    assert "is not copied" not in text, "a direct construction is told it copied something"
    assert text.endswith(
        "(a copy made by replace() carries the old time as a given one, so it is refused too)"
    )
    doc = " ".join((tick_mod.TickContext.__doc__ or "").split())
    assert (
        "refused with the same message, which also says that a copy made by replace() is refused too"
        in doc
    ), "the class docstring quotes a sentence the code does not say"


def test_an_unknown_key_in_a_tool_manifest_entry_is_not_shown(cfg_dir):
    """`parse_manifest` joined the raw `loc` of each problem: an unknown key was shown as written."""
    (cfg_dir / "tools").mkdir(exist_ok=True)
    entry = "- {name: a_tool, " + KEY + ": 1}\n"
    exc = _refused(cfg_dir, extra_file=("tools/test-agent.yaml", entry))
    assert "invalid tool entry" in str(exc) and "<unknown key>" in str(exc), str(exc)
    _assert_value_free(exc, KEY)


def test_egress_check_refuses_a_url_it_cannot_read_without_its_text():
    from hadavin_sdk.guard.egress import EgressRefused, egress_check

    with pytest.raises(EgressRefused) as err:
        egress_check(WIDE_URL, frozenset({"records.example.invalid"}))
    assert str(err.value) == "host not in egress.yaml: ?"
    assert PW not in _everything_shown(err.value) and err.value.__cause__ is None


# ======================================================================================================================
# Round 7. The made-up marker below is built from parts and LOOKS like a plain identifier on purpose: `shown_name` is a
# shape filter, so a marker with capital letters (PW) is hidden by it and proves nothing about a value that passed it.
# ======================================================================================================================
MARK = "zq" + "-probe-" + "mk4417"


def _yaml_edit(name, fn):
    def go(root):
        path = root / name
        path.write_text(yaml.safe_dump(fn(yaml.safe_load(path.read_text(encoding="utf-8")))))

    return go


def _raw_file(name, text, append=True):
    def go(root):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        old = path.read_text(encoding="utf-8") if (append and path.exists()) else ""
        path.write_text(old + text, encoding="utf-8")

    return go


def _setitem(d, key, value):
    d[key] = value
    return d


_FW_AT, _FW_COLON, _FW_HASH, _FW_SLASH, _FW_Q = "＠", "：", "＃", "／", "？"
_SM_AT, _SM_COLON, _SM_HASH, _SM_Q = "﹫", "﹕", "﹟", "﹖"
_NETLOCS = {
    "fw-at-and-colon": f"user{_FW_COLON}{MARK}{_FW_AT}host.example",
    "fw-at-only": f"{MARK}{_FW_AT}host.example",
    "fw-colon-port": f"host.example{_FW_COLON}{MARK}",
    "fw-bad-port": f"host.example{_FW_COLON}99999999{MARK}",
    "fw-hash": f"host.example{_FW_HASH}{MARK}",
    "fw-slash": f"host.example{_FW_SLASH}{MARK}",
    "fw-question": f"host.example{_FW_Q}{MARK}",
    "small-at-colon": f"user{_SM_COLON}{MARK}{_SM_AT}host.example",
    "u2100": f"{MARK}℀host.example",
    "u2105": f"{MARK}℅host.example",
    "fw-brackets": f"［{MARK}］host.example",
    "ascii-bracket-open": f"[{MARK}host.example",
    "ascii-bad-ipv6": f"[{MARK}]",
    "ascii-bad-port": f"host.example:{MARK}",
    "ascii-login": f"user:{MARK}@host.example",
    "fw-percent": f"host％{MARK}.example",
    "ascii-percent": f"host%{MARK}.example",
}


def _url_rows():
    rows = {}
    for shape, netloc in _NETLOCS.items():
        rows[f"systems.base_url {shape}"] = _yaml_edit(
            "config.yaml",
            lambda d, n=netloc: (
                d["systems"]["fixture-records"].update(base_url=f"https://{n}/x") or d
            ),
        )
        rows[f"openai_compat.base_url {shape}"] = _yaml_edit(
            "config.yaml",
            lambda d, n=netloc: (
                d["backends"].update(llm={"kind": "openai_compat", "base_url": f"https://{n}/v1"})
                or d
            ),
        )
        rows[f"vault.address {shape}"] = _yaml_edit(
            "config.yaml",
            lambda d, n=netloc: (
                d["backends"].update(secrets={"kind": "vault", "address": f"https://{n}"}) or d
            ),
        )
        rows[f"s3.endpoint_url {shape}"] = _yaml_edit(
            "config.yaml",
            lambda d, n=netloc: (
                d["backends"].update(
                    anchor={
                        "kind": "s3_object_lock",
                        "bucket": "b",
                        "region": "r",
                        "endpoint_url": f"https://{n}",
                    }
                )
                or d
            ),
        )
    return rows


_BAD_YAML = f"- name: x\n  function: [{MARK}\n  bad: : {MARK}\n"
_TOOL_HEAD = "- name: t\n  function: m:f\n  description: d\n  input_schema: {type: object}\n  side_effect: none\n"
PROBE_ROWS = {
    **_url_rows(),
    "broken yaml tools": _raw_file("tools/test-agent.yaml", _BAD_YAML, append=False),
    "broken yaml tools tab": _raw_file(
        "tools/test-agent.yaml", f"- name: x\n\tfunction: {MARK}\n", append=False
    ),
    "broken yaml config": _raw_file("config.yaml", f"\nbroken: [unclosed {MARK}\nx: {{a: {MARK}\n"),
    "broken yaml config indent": _raw_file("config.yaml", f"\n  stray: {MARK}\n bad: {MARK}\n"),
    "duplicate key config": _raw_file("config.yaml", f"\nenvironment: {MARK}\n"),
    "broken yaml agents": _raw_file("agents.yaml", f"\n- id: [{MARK}\n"),
    "broken yaml principals": _raw_file("principals.yaml", f"\n- id: [{MARK}\n"),
    "broken yaml chains": _raw_file("chains.yaml", f"\n- id: [{MARK}\n"),
    "broken yaml egress": _raw_file("egress.yaml", f"\nhosts: [{MARK}\n"),
    "broken yaml action": _raw_file("actions/lookup_record.yaml", f"\nx: [{MARK}\n"),
    "yaml python tag": _raw_file("config.yaml", f"\nz: !!python/object:os.system {MARK}\n"),
    "yaml alias": _raw_file("config.yaml", f"\nz: *{MARK}\n"),
    "yaml list as a key": _raw_file("config.yaml", f"\n? [{MARK}]\n: 1\n"),
    "yaml list as a key in agents": _raw_file("agents.yaml", f"\n- id: x\n  ? [{MARK}]\n  : 1\n"),
    "yaml list as a key in a tool manifest": _raw_file(
        "tools/test-agent.yaml", f"? [{MARK}]\n: 1\n", append=False
    ),
    "unknown key config": _yaml_edit("config.yaml", lambda d: _setitem(d, MARK, 1)),
    "unknown key agents": _yaml_edit("agents.yaml", lambda d: _setitem(d[0], MARK, 1) and d),
    "unknown key principals": _yaml_edit(
        "principals.yaml", lambda d: _setitem(d[0], MARK, 1) and d
    ),
    "unknown key chains": _yaml_edit("chains.yaml", lambda d: _setitem(d[0], MARK, 1) and d),
    "unknown key action": _yaml_edit("actions/lookup_record.yaml", lambda d: _setitem(d, MARK, 1)),
    "unknown key egress": _yaml_edit("egress.yaml", lambda d: _setitem(d, MARK, 1)),
    "unknown key route": _yaml_edit(
        "config.yaml", lambda d: _setitem(d["routes"]["default"], MARK, 1) and d
    ),
    "unknown key backends": _yaml_edit(
        "config.yaml", lambda d: _setitem(d["backends"], MARK, 1) and d
    ),
    "unknown key system": _yaml_edit(
        "config.yaml", lambda d: _setitem(d["systems"]["fixture-records"], MARK, 1) and d
    ),
    "unknown key llm setting": _yaml_edit(
        "config.yaml", lambda d: _setitem(d["backends"]["llm"], MARK, 1) and d
    ),
    "unknown key tool entry": _raw_file(
        "tools/test-agent.yaml", _TOOL_HEAD + f"  {MARK}: 1\n", append=False
    ),
    "unknown key budget": _yaml_edit(
        "agents.yaml", lambda d: _setitem(d[0]["budget_usd"], MARK, "1") and d
    ),
    "unknown key executor": _yaml_edit(
        "actions/lookup_record.yaml", lambda d: _setitem(d["executor"], MARK, 1) and d
    ),
    "unknown key chain step": _yaml_edit(
        "chains.yaml", lambda d: _setitem(d[0]["steps"][0], MARK, 1) and d
    ),
    "value model_route": _yaml_edit(
        "agents.yaml", lambda d: _setitem(d[0], "model_route", MARK) and d
    ),
    "value scope_allowed": _yaml_edit(
        "agents.yaml", lambda d: _setitem(d[0], "scope_allowed", [MARK]) and d
    ),
    "value status": _yaml_edit("agents.yaml", lambda d: _setitem(d[0], "status", MARK) and d),
    "value data_class": _yaml_edit(
        "agents.yaml", lambda d: _setitem(d[0], "data_class", MARK) and d
    ),
    "value environment": _yaml_edit("config.yaml", lambda d: _setitem(d, "environment", MARK)),
    "value backend kind": _yaml_edit(
        "config.yaml", lambda d: _setitem(d["backends"], "store", MARK)
    ),
    "value backend kind mapping": _yaml_edit(
        "config.yaml", lambda d: _setitem(d["backends"], "llm", {"kind": MARK})
    ),
    "value target_system": _yaml_edit(
        "actions/lookup_record.yaml", lambda d: _setitem(d, "target_system", MARK)
    ),
    "value chain_id": _yaml_edit(
        "actions/lookup_record.yaml", lambda d: _setitem(d, "chain_id", MARK)
    ),
    "value risk_class": _yaml_edit(
        "actions/lookup_record.yaml", lambda d: _setitem(d, "risk_class", MARK)
    ),
    "value executor kind": _yaml_edit(
        "actions/lookup_record.yaml", lambda d: _setitem(d["executor"], "kind", MARK) and d
    ),
    "value verify_check": _yaml_edit(
        "actions/lookup_record.yaml", lambda d: _setitem(d, "verify_check", MARK)
    ),
    "value rollback": _yaml_edit(
        "actions/lookup_record.yaml", lambda d: _setitem(d, "rollback", MARK)
    ),
    "value approver_of": _yaml_edit(
        "principals.yaml", lambda d: _setitem(d[1], "approver_of", [MARK]) and d
    ),
    "value principal kind": _yaml_edit(
        "principals.yaml", lambda d: _setitem(d[0], "kind", MARK) and d
    ),
    "value approver_ids": _yaml_edit(
        "chains.yaml", lambda d: _setitem(d[0]["steps"][0], "approver_ids", [MARK]) and d
    ),
    "value rights": _yaml_edit("principals.yaml", lambda d: _setitem(d[0], "rights", [MARK]) and d),
    "value egress host": _yaml_edit("egress.yaml", lambda d: _setitem(d, "hosts", [MARK])),
    "value prompt_file": _yaml_edit(
        "agents.yaml", lambda d: _setitem(d[0], "prompt_file", MARK) and d
    ),
    "value tool file name": _raw_file(f"tools/{MARK}.yaml", "[]\n", append=False),
    "value tool function and operations and hosts": _raw_file(
        "tools/test-agent.yaml",
        _TOOL_HEAD.replace("m:f", f"{MARK}:f")
        + f"  operations: [{MARK}]\n  hosts: [{MARK}]\n  secret_names: [{MARK}]\n",
        append=False,
    ),
    "value tool side_effect": _raw_file(
        "tools/test-agent.yaml",
        _TOOL_HEAD.replace("side_effect: none", f"side_effect: {MARK}"),
        append=False,
    ),
    "value tool name": _raw_file(
        "tools/test-agent.yaml", _TOOL_HEAD.replace("name: t", f"name: {MARK}"), append=False
    ),
    "value tools_allowed without a manifest": _yaml_edit(
        "agents.yaml", lambda d: _setitem(d[0], "tools_allowed", [MARK]) and d
    ),
    "value tools_allowed with a manifest": _raw_file(
        "tools/test-agent.yaml", _TOOL_HEAD.replace("name: t", "name: t_a"), append=False
    ),
    "value route key": _yaml_edit(
        "config.yaml", lambda d: _setitem(d["routes"], MARK, d["routes"]["default"]) and d
    ),
    "value check_modules": _yaml_edit(
        "config.yaml", lambda d: _setitem(d, "check_modules", [MARK, "tests.fixtures.checks"])
    ),
    "value tool list not a list": _raw_file("tools/test-agent.yaml", f"{MARK}: 1\n", append=False),
    "value tool entry not a mapping": _raw_file(
        "tools/test-agent.yaml", f"- {MARK}\n", append=False
    ),
}

# Rows that raise nothing, each with the line that makes that safe (a typo there narrows or does nothing; it never
# turns a check off). A row that starts raising, or a new row that does not raise, must be looked at.
ACCEPTED_ROWS = {
    "value egress host": "a host name in egress.yaml is a grant the operator writes; a wrong one allows a host nobody calls, "
    "and every entry must be a bare host (`_bare_host`, tested below)",
    "value tools_allowed without a manifest": "no manifest: the callables handed to app.build are the tools; an entry "
    "that matches none is never offered (registry.Registry.tools_for intersects with what exists), so it only narrows",
    "value route key": "a route no agent names is never used; an agent's model_route that names no route is refused "
    "(registry._cross_check)",
    "value check_modules": "a module listed there that no action names is never imported for a check",
}


def _run_probe(cfg_dir, mutate):
    """The error `load_config` then `load_registry` raise for one mutated config folder, or None."""
    mutate(cfg_dir)
    try:
        load_registry(load_config(cfg_dir))
    except ConfigError as exc:
        return exc
    return None


@pytest.mark.parametrize("row", sorted(PROBE_ROWS))
def test_the_marker_is_in_no_error_text_in_any_probe_row(cfg_dir, row):
    """The evidence probe set (107 results; at 4ccb4f9a eight of them showed the marker, from a1869655 on none) as a test: one made-up marker per row; where an error is
    raised, no copy of it is in `str`, `repr`, the cause or the printed traceback (the chain a command line prints)."""
    exc = _run_probe(cfg_dir, PROBE_ROWS[row])
    if exc is None:
        assert row in ACCEPTED_ROWS, f"nothing was refused for: {row}"
        return
    assert row not in ACCEPTED_ROWS, f"now refused, take it off ACCEPTED_ROWS: {row}"
    assert MARK not in _everything_shown(exc), _everything_shown(exc)[:400]
    assert exc.__cause__ is None
    # A context that exists is hidden from the printed traceback (`from None`); none at all is also fine.
    assert exc.__context__ is None or exc.__suppress_context__ is True, row


def test_every_probe_row_either_raises_or_is_listed_with_its_reason():
    assert set(ACCEPTED_ROWS) <= set(PROBE_ROWS)
    assert all(isinstance(r, str) and len(r) >= 30 for r in ACCEPTED_ROWS.values()), (
        "each accepted row says why"
    )


# ---- Issue 1: which pydantic message may be shown ------------------------------------------------------------------
def _validation_errors(model, data):
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as err:
        model(**data) if isinstance(model, type) else model.validate_python(data)
    return err.value.errors(include_url=False, include_input=False)


def test_the_fixed_sentence_types_are_real_pydantic_error_types():
    from pydantic_core.core_schema import ErrorType

    assert config_mod._FIXED_SENTENCE_TYPES <= set(typing.get_args(ErrorType))


def _fixed_sentence_cases():
    from decimal import Decimal

    from pydantic import BaseModel, ConfigDict, Field

    class Inner(BaseModel):
        model_config = ConfigDict(extra="forbid", frozen=True)
        a: int

    class Color(enum.Enum):
        RED = "red"

    class M(BaseModel):
        model_config = ConfigDict(extra="forbid", frozen=True)
        lit: typing.Literal["x", "y"] = "x"
        text: str = "a"
        number: int = 1
        real: float = 1.0
        flag: bool = False
        money: Decimal = Decimal(1)
        items: list[str] = []
        named: dict[str, int] = {}
        inner: Inner | None = None
        gt: int = Field(default=5, gt=0)
        ge: int = Field(default=5, ge=0)
        lt: int = Field(default=5, lt=10)
        le: int = Field(default=5, le=10)
        short: str = Field(default="abc", min_length=2)
        long: str = Field(default="a", max_length=2)
        pat: str = Field(default="abc", pattern=r"^abc$")
        many: list[int] = Field(default=[1], min_length=1)
        few: list[int] = Field(default=[], max_length=1)
        path: Path = Path(".")
        req: int = 0
        mult: int = Field(default=3, multiple_of=3)
        tup: tuple[int, int] = (1, 2)
        st: set[int] = set()
        fst: frozenset[int] = frozenset()
        raw: bytes = b""
        whole: int = 1
        fin: float = Field(default=1.0, allow_inf_nan=False)
        nothing: None = None
        color: Color = Color.RED

    # One typed value per problem type; the value is the marker, or holds it.
    cases = {
        "literal_error": {"lit": MARK},
        "string_type": {"text": 5},
        "int_parsing": {"number": MARK},
        "float_parsing": {"real": MARK},
        "bool_parsing": {"flag": MARK},
        "decimal_parsing": {"money": MARK},
        "list_type": {"items": MARK},
        "dict_type": {"named": MARK},
        "model_type": {"inner": MARK},
        "greater_than": {"gt": -1},
        "greater_than_equal": {"ge": -1},
        "less_than": {"lt": 99},
        "less_than_equal": {"le": 99},
        "string_too_short": {"short": "a"},
        "string_too_long": {"long": MARK},
        "string_pattern_mismatch": {"pat": MARK},
        "too_short": {"many": []},
        "too_long": {"few": [1, 2]},
        "extra_forbidden": {MARK: 1},
        "int_type": {"number": [MARK]},
        "float_type": {"real": [MARK]},
        "bool_type": {"flag": [MARK]},
        "decimal_type": {"money": [MARK]},
        "multiple_of": {"mult": 4},
        "tuple_type": {"tup": MARK},
        "set_type": {"st": MARK},
        "frozen_set_type": {"fst": MARK},
        "bytes_type": {"raw": 5},
        "int_from_float": {"whole": 1.5},
        "int_parsing_size": {"number": "9" * 5000},
        "finite_number": {"fin": float("inf")},
        "none_required": {"nothing": MARK},
        "enum": {"color": MARK},
    }
    return M, cases


def test_every_pydantic_message_type_that_is_shown_as_written_holds_no_typed_value():
    model, cases = _fixed_sentence_cases()
    seen = set()
    for kind, data in cases.items():
        for e in _validation_errors(model, data):
            seen.add(e["type"])
            assert e["type"] in config_mod._FIXED_SENTENCE_TYPES, (kind, e["type"])
            assert MARK not in config_mod._what(e), (kind, config_mod._what(e))
            assert config_mod._what(e) == e["msg"]
    # The two types a file cannot produce by a plain call: an assignment to a frozen model, and an object read by attribute.
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as err:
        model().number = 2
    seen |= {e["type"] for e in err.value.errors(include_url=False, include_input=False)}
    with pytest.raises(ValidationError) as err:
        model.model_validate(5, from_attributes=True)
    seen |= {e["type"] for e in err.value.errors(include_url=False, include_input=False)}
    # Every member of the shown-as-written set is produced by a case here (none is listed that no case reaches), and
    # `missing` comes from `req` having no value only when it is required; checked on its own below.
    assert seen >= config_mod._FIXED_SENTENCE_TYPES - {"missing"}, (
        config_mod._FIXED_SENTENCE_TYPES - seen
    )


@pytest.mark.parametrize(
    "kind, expected",
    [
        ("union_tag_invalid", "the kind is missing or not one of the known kinds"),
        ("union_tag_not_found", "the kind is missing or not one of the known kinds"),
        ("assertion_error", "a value was refused (assertion_error)"),
        ("json_invalid", "a value was refused (json_invalid)"),
        ("url_parsing", "a value was refused (url_parsing)"),
        ("a_type_added_later", "a value was refused (a_type_added_later)"),
    ],
)
def test_a_pydantic_type_off_the_allow_list_gets_the_fixed_sentence(kind, expected):
    said = config_mod._what({"type": kind, "msg": f"Input {MARK} is wrong", "ctx": {}})
    assert said == expected and MARK not in said, said


def test_a_typed_discriminator_value_is_never_quoted_and_the_allowed_kinds_are_listed(cfg_dir):
    path = cfg_dir / "actions" / "lookup_record.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for typed in (MARK, PW, "http "):
        data["executor"]["kind"] = typed
        path.write_text(yaml.safe_dump(data), encoding="utf-8")
        with pytest.raises(ConfigError) as err:
            load_registry(load_config(cfg_dir))
        assert typed.strip() not in _everything_shown(err.value).replace(
            "'none', 'manual', 'http'", ""
        )
        assert (
            "the kind is missing or not one of the known kinds; allowed: 'none', 'manual', 'http'"
            in str(err.value)
        )
    del data["executor"]["kind"]
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ConfigError) as err:
        load_registry(load_config(cfg_dir))
    assert "the kind is missing or not one of the known kinds" in str(err.value)


# ---- Issue 4: the marker class that says "Hadavin wrote this sentence" ---------------------------------------------
_PROBE_SOURCE = """
from decimal import Decimal
from pydantic import BaseModel, field_validator
from hadavin_sdk.errors import ConfigValueError

class Probe(BaseModel):
    kind: str
    value: str

    @field_validator("value")
    @classmethod
    def _check(cls, v, info):
        k = info.data.get("kind")
        if k == "int":
            int(v)
        elif k == "float":
            float(v)
        elif k == "decimal":
            Decimal(v)
        elif k == "fromhex":
            bytes.fromhex(v)
        elif k == "plain":
            raise ValueError("the value is " + v)
        elif k == "ours":
            raise ConfigValueError("the value is out of its range")
        return v
"""


def _probe_in_a_hadavin_module(kind, value):
    """A validator that lives in a module NAMED `hadavin_sdk...` (so the old last-frame test counted it as ours)."""
    import types

    mod = types.ModuleType("hadavin_sdk._round7_probe")
    exec(compile(_PROBE_SOURCE, "<round7-probe>", "exec"), mod.__dict__)  # noqa: S102  # nosec B102 - test source
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as err:
        mod.Probe(kind=kind, value=value)
    return config_mod.config_error_text(err.value)


@pytest.mark.parametrize("kind", ["int", "float", "fromhex", "plain"])
def test_a_library_or_plain_value_error_inside_a_hadavin_module_shows_no_text(kind):
    text = _probe_in_a_hadavin_module(kind, "x" + MARK)
    assert MARK not in text and "a value was refused (ValueError)" in text, text


def test_a_config_value_error_keeps_its_sentence_wherever_it_is_raised():
    text = _probe_in_a_hadavin_module("ours", MARK)
    assert "the value is out of its range" in text and MARK not in text, text


def test_a_config_error_is_not_the_marker_class():
    """`ConfigError` is a ValueError too, but only `ConfigValueError` marks a sentence as written for display."""
    from hadavin_sdk.errors import ConfigError as CE
    from hadavin_sdk.errors import ConfigValueError

    assert not issubclass(CE, ConfigValueError) and not issubclass(ConfigValueError, CE)


def test_no_validator_of_the_config_files_raises_a_plain_value_error():
    """The class: a pydantic validator of a configuration model raises `ConfigValueError`, never `ValueError`."""
    for name in ("config.py", "backends/table.py", "actions/contract.py"):
        text = (ROOT / "src" / "hadavin_sdk" / name).read_text(encoding="utf-8")
        assert not re.search(r"raise ValueError\(", text), name


# ---- Issue 6: URL fields, unknown values, files -------------------------------------------------------------------
URL_FIELDS = {
    "base_url",
    "address",
    "endpoint_url",
    "account_url",
    "vault_url",
    "key_id",
    "api_base",
    "api_url",
}


def test_every_settings_field_that_holds_a_url_uses_the_one_url_type():
    """The class: a field named like a URL is a `ConfigUrl` (login and look-alike hosts refused for every field)."""
    from hadavin_sdk.sources.kinds import KINDS

    models = {e.settings for caps in table.TABLE.values() for e in caps.values()}
    models |= {k.settings for k in KINDS.values()}
    models.add(config_mod.System)  # `systems.<name>.base_url` is a URL field too
    found = set()
    for model in models:
        for name, info in model.model_fields.items():
            if (
                name in URL_FIELDS and model.__name__ != "AwsKmsSettings"
            ):  # a key id, not an address
                found.add((model.__name__, name))
                assert "checked_url" in repr(info.annotation) + repr(info.metadata), (
                    model.__name__,
                    name,
                )
    assert len(found) >= 8, found


@pytest.mark.parametrize(
    "url",
    [
        f"https://user:{MARK}@host.example/x",
        f"https://{MARK}@host.example/x",
        "https://:" + MARK + "@host.example/",
        "https://［" + MARK + "］host.example/",
        "https://host％" + MARK + ".example/",
        "https://host%" + MARK + ".example/",
        "https://host.example:" + MARK + "/",
        "https://[" + MARK + "/",
    ],
)
def test_the_one_url_type_refuses_a_login_a_look_alike_host_and_a_bad_port_with_a_fixed_sentence(
    url,
):
    from pydantic import TypeAdapter, ValidationError

    from hadavin_sdk.config_url import ConfigUrl

    with pytest.raises(ValidationError) as err:
        TypeAdapter(ConfigUrl).validate_python(url)
    text = config_mod.config_error_text(err.value)
    assert MARK not in text, text
    assert "a URL must not contain a login" in text or "not a valid URL" in text, text


@pytest.mark.parametrize(
    "url",
    [
        "https://host.example/x",
        "http://127.0.0.1:8080",
        "https://[::1]:8443/v1",
        "https://xn--bcher-kva.example",
    ],
)
def test_the_one_url_type_keeps_ordinary_urls(url):
    from pydantic import TypeAdapter

    from hadavin_sdk.config_url import ConfigUrl

    assert TypeAdapter(ConfigUrl).validate_python(url) == url


def test_the_login_in_a_url_is_refused_for_the_two_fields_that_missed_it(cfg_dir):
    for edit in (
        lambda d: d["backends"].update(
            llm={"kind": "openai_compat", "base_url": f"https://u:{MARK}@h.example/v1"}
        ),
        lambda d: d["backends"].update(
            secrets={"kind": "vault", "address": f"https://u:{MARK}@h.example"}
        ),
    ):
        exc = _refused(cfg_dir, edit=edit)
        assert "a URL must not contain a login" in str(exc) and MARK not in _everything_shown(exc)
        _edit(
            cfg_dir,
            lambda d: d["backends"].update(
                llm={"kind": "fake", "recorded_dir": "../recorded"}, secrets="fake"
            ),
        )


def test_the_system_base_url_refuses_fullwidth_brackets_and_percent_like_the_other_url_fields():
    from hadavin_sdk.safe_url import InvalidUrl, UrlHasLogin, config_urlsplit

    for bad in ("https://［a］b.example/", "https://a％41.example/", "https://a%41.example/"):
        with pytest.raises(InvalidUrl) as err:
            config_urlsplit(bad)
        assert not isinstance(err.value, UrlHasLogin) and str(err.value) == "not a valid URL"
    with pytest.raises(UrlHasLogin):
        config_urlsplit("https://u:p@h.example/")


def _pilot_principals(cfg_dir, edit):
    _edit_file = _yaml_edit("principals.yaml", edit)
    _edit_file(cfg_dir)
    with pytest.raises(ConfigError) as err:
        load_registry(load_config(cfg_dir))
    return str(err.value)


def test_a_chain_approver_must_be_a_person_who_is_in_principals(cfg_dir):
    text = _yaml_edit(
        "chains.yaml",
        lambda d: _setitem(d[0]["steps"][0], "approver_ids", ["svc:test-agent", MARK]) and d,
    )
    text(cfg_dir)
    with pytest.raises(ConfigError) as err:
        load_registry(load_config(cfg_dir))
    msg = str(err.value)
    assert (
        "chain chain-abc step 0: approver_ids entry 0 is not a person" in msg
    )  # a service identity
    assert (
        "approver_ids entry 1 is not a person" in msg and MARK not in msg
    )  # one that is not there at all


def test_a_right_must_name_an_action_and_approver_of_must_name_a_chain(cfg_dir):
    msg = _pilot_principals(
        cfg_dir, lambda d: _setitem(d[0], "rights", ["lookup_record", MARK]) and d
    )
    assert "principal svc:test-agent: rights entry 1 names no action" in msg and MARK not in msg
    _yaml_edit("principals.yaml", lambda d: _setitem(d[0], "rights", ["lookup_record"]) and d)(
        cfg_dir
    )
    msg = _pilot_principals(
        cfg_dir, lambda d: _setitem(d[1], "approver_of", ["chain-abc", MARK]) and d
    )
    assert "principal user:a: approver_of entry 1 names no chain" in msg and MARK not in msg


def test_with_a_manifest_a_tools_allowed_entry_with_no_tool_in_it_is_refused(cfg_dir):
    _yaml_edit("agents.yaml", lambda d: _setitem(d[0], "tools_allowed", ["t_a", MARK]) and d)(
        cfg_dir
    )
    for path in (cfg_dir / "actions").glob(
        "*.yaml"
    ):  # a tooled agent: each string input says `identifier`
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for sub in ((data.get("input_schema") or {}).get("properties") or {}).values():
            if sub.get("type") == "string":
                sub.setdefault("identifier", False)
        path.write_text(yaml.safe_dump(data), encoding="utf-8")
    _raw_file("tools/test-agent.yaml", _TOOL_HEAD.replace("name: t", "name: t_a"), append=False)(
        cfg_dir
    )
    with pytest.raises(ConfigError) as err:
        load_registry(load_config(cfg_dir))
    assert "tools_allowed entry 1 has no tool in this manifest" in str(err.value)
    assert MARK not in _everything_shown(err.value)


def test_egress_yaml_takes_only_a_list_of_bare_hosts(cfg_dir):
    for edit, said in (
        (lambda d: _setitem(d, "host", ["a.example"]), "1 unknown key(s)"),
        (lambda d: _setitem(d, "hosts", "a.example"), "list of bare host names"),
        (lambda d: _setitem(d, "hosts", [f"https://{MARK}/x"]), "list of bare host names"),
        (lambda d: _setitem(d, "hosts", [f"{MARK}:443"]), "list of bare host names"),
        (lambda d: _setitem(d, "hosts", [f"u@{MARK}"]), "list of bare host names"),
        (lambda d: _setitem(d, "hosts", [f"{MARK} x"]), "list of bare host names"),
        (lambda d: _setitem(d, "hosts", [5]), "list of bare host names"),
    ):
        _yaml_edit("egress.yaml", edit)(cfg_dir)
        with pytest.raises(ConfigError) as err:
            load_config(cfg_dir)
        assert said in str(err.value) and MARK not in _everything_shown(err.value)
        (cfg_dir / "egress.yaml").write_text("hosts:\n  - 127.0.0.1\n", encoding="utf-8")
    for fine in (["a.example", "127.0.0.1", "::1"], []):
        (cfg_dir / "egress.yaml").write_text(yaml.safe_dump({"hosts": fine}), encoding="utf-8")
        assert load_config(cfg_dir).egress_hosts == frozenset(fine)


def test_a_config_file_that_cannot_be_read_is_reported_by_its_type_only(cfg_dir):
    (cfg_dir / "egress.yaml").unlink()
    (
        cfg_dir / "egress.yaml"
    ).mkdir()  # a folder where a file belongs: IsADirectoryError, whose text has the path
    with pytest.raises(ConfigError) as err:
        load_config(cfg_dir)
    assert str(err.value) == "egress.yaml: cannot be read (IsADirectoryError)", str(err.value)
    assert str(cfg_dir) not in _everything_shown(err.value)
    (cfg_dir / "agents.yaml").unlink()
    (cfg_dir / "agents.yaml").mkdir()
    (cfg_dir / "egress.yaml").rmdir()
    with pytest.raises(ConfigError) as err:
        load_registry(load_config(cfg_dir))
    assert str(cfg_dir) not in _everything_shown(err.value)


def test_a_yaml_key_that_is_a_list_is_a_config_error_not_a_type_error():
    from hadavin_sdk.config import load_yaml

    with pytest.raises(ConfigError) as err:
        load_yaml(f"? [{MARK}]\n: 1\n")
    assert (
        str(err.value) == "a mapping key must be a plain value (line 1)"
        and err.value.__cause__ is None
    )


# ---- Issue 5: the runtime path of a tool call --------------------------------------------------------------------
@pytest.mark.parametrize(
    "url",
    [
        "https://api.example.com:abc/x",
        "https://api.example.com:99999/x",
        "https://[api.example.com/x",
        "https://[" + MARK + "]/x",
    ],
)
def test_a_tool_call_with_an_unreadable_url_is_a_tool_refusal_with_a_fixed_sentence(url):
    from hadavin_sdk import tools as tools_mod
    from tests import k5_support
    from tests.test_k5_review import _ctx

    del k5_support
    with pytest.raises(tools_mod.ToolRefused) as err:
        _ctx().fetch("GET", url, operation="bundle.read")
    assert str(err.value) == "the URL is not valid" and MARK not in _everything_shown(err.value)
    assert err.value.__cause__ is None


class _StubReached(Exception):
    """Raised by the stand-in opener: the call got past every check and would have gone to the network."""


class _StubOpener:
    def open(self, *a, **k):
        raise _StubReached("no network in this test")


def test_a_tool_call_with_a_login_in_the_url_is_a_tool_refusal(monkeypatch):
    from hadavin_sdk import tools as tools_mod
    from tests.test_k5_review import _ctx

    monkeypatch.setattr(tools_mod.http_guard, "OPENER", _StubOpener())  # no real DNS or connection
    with pytest.raises(tools_mod.ToolRefused, match="credentials in the URL are refused") as err:
        _ctx().fetch("GET", f"https://u:{MARK}@api.example.com/x", operation="bundle.read")
    assert MARK not in _everything_shown(err.value)


# ---- Issue 2: the names in the deferred-feature checks ---------------------------------------------------------------
def test_an_agent_id_and_a_levels_key_that_are_not_plain_names_are_not_shown_by_the_deferred_checks(
    cfg_dir,
):
    agents = _agent_entry(id=PW, levels={"lookup_record": "act", PW: "act"})
    exc = _refused(cfg_dir, extra_file=("agents.yaml", agents))
    assert "agent <not shown>: level act for lookup_record arrives in Phase 4" in str(exc), str(exc)
    assert "agent <not shown>: levels names 1 action(s) that are not in scope_allowed" in str(
        exc
    ), str(exc)
    _assert_value_free(exc, PW)


def test_an_action_id_that_is_not_a_plain_name_is_not_shown_by_the_deferred_checks():
    """The check works on a loaded registry; a stand-in with the three fields it reads keeps the test to one rule."""
    contract = SimpleNamespace(
        id=PW, executor=SimpleNamespace(kind="manual"), risk_class="read_only"
    )
    reg = SimpleNamespace(
        config=SimpleNamespace(environment="demo"), contracts={PW: contract}, agents={}
    )
    assert deferred.check(reg) == [
        "action <not shown>: executor manual arrives with K8 (posted fixes)"
    ]


# ---- Issue 3: the sites in sources, secrets, the tool runner and the app ------------------------------------------------
def test_a_source_key_that_is_not_a_plain_name_is_not_shown():
    from hadavin_sdk.sources import scope_problems

    class Opaque:
        def probe_scope(self):
            return None

    class Broken:
        def probe_scope(self):
            raise RuntimeError(PW)

    class Wide:
        def probe_scope(self):
            return ["a rule is too wide"]

    out = scope_problems({PW + "1": Opaque(), PW + "2": Broken(), PW + "3": Wide()}, {})
    assert sorted(out) == [
        "source <not shown>: a rule is too wide",
        "source <not shown>: cannot be probed and has no scope_inventory reference (design 6.6)",
        "source <not shown>: scope probe failed (RuntimeError)",
    ], out


def test_a_secret_name_that_is_not_a_plain_name_is_not_shown_by_the_platform_secrets_checks():
    from pydantic import create_model

    from hadavin_sdk.backends import platform_secrets as ps

    field = (
        "token_secret" + "_name"
    )  # built from parts: the name alone makes a scanner see a password
    Settings = create_model("Settings", **{field: (str, "ok_name")})

    class Broken:
        def get(self, name):
            raise RuntimeError(name)

    with pytest.raises(ConfigError) as err:
        ps.bound(SimpleNamespace(get=lambda n: n), Settings(), "backend x")(PW)
    assert (
        str(err.value)
        == "backend x: may read only the secrets named in its own settings (a name that is not one of them is never quoted)"
    )
    both = Settings(**{field: PW})
    for kwargs, said in (
        (
            {"executor_names": {PW}},
            "secret names used by both a backend and an action executor: <not shown>;",
        ),
        (
            {"executor_names": set(), "tool_names": {PW}},
            "secret names used by both a backend and a read tool: <not shown>;",
        ),
    ):
        with pytest.raises(ConfigError) as err:
            ps.check(SimpleNamespace(get=lambda n: n), [both], **kwargs)
        assert str(err.value).startswith(said), str(err.value)
        assert PW not in _everything_shown(err.value)
    with pytest.raises(ConfigError) as err:
        ps.check(Broken(), [both], set())
    assert str(err.value) == "secret <not shown> cannot be read at start-up (RuntimeError)"
    assert err.value.__cause__ is None and PW not in _everything_shown(err.value)


def test_a_tool_module_name_that_is_not_a_plain_name_is_not_shown_by_the_tool_loader(
    tmp_path, monkeypatch
):
    from hadavin_sdk import tools as tools_mod

    odd = "Zq9x" + "Mod"  # a legal module name that `shown_name` hides (upper-case letters)
    (tmp_path / (odd + ".py")).write_text("VALUE = 1\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    with pytest.raises(ConfigError) as err:
        tools_mod.load_tool_module(odd, {odd: "0" * 64})
    assert str(err.value).startswith("tool module <not shown>: its source hash is "), str(err.value)
    with pytest.raises(ConfigError) as err2:
        tools_mod.load_tool_module(odd + "Missing", {odd + "Missing": "0" * 64})
    assert str(err2.value) == "tool module <not shown> cannot be found on the module path"
    for err_ in (err, err2):
        assert odd not in _everything_shown(err_.value) and err_.value.__cause__ is None


def test_a_tls_ca_name_that_is_not_a_plain_name_is_not_shown_by_the_app(cfg_dir):
    cfg = load_config(cfg_dir)
    (cfg_dir / (PW + ".pem")).write_text(" ", encoding="utf-8")
    stub = SimpleNamespace(get=lambda name: " ")
    for ca_file, ca_secret in ((PW + ".pem", None), (None, PW)):
        with pytest.raises(ConfigError) as err:
            app_mod._tls_context(cfg, stub, ca_file, ca_secret)
        assert str(err.value) == "the CA bundle is empty", str(err.value)
        assert PW not in _everything_shown(err.value)


def test_a_tool_name_in_the_app_is_pattern_bound_so_shown_name_there_changes_nothing():
    """`app._unprobed_tools` prints `ToolSpec.name`, which is held to `^[a-z][a-z0-9_]{0,39}$` by the model; a name
    that `shown_name` would hide cannot reach it. Pinned here so a looser name pattern shows up as a failure."""
    from hadavin_sdk.tools import ToolSpec

    def make(name):
        return ToolSpec(
            name=name,
            function="m:f",
            description="d",
            input_schema={"type": "object"},
            side_effect="none",
        )

    assert (
        make("a_tool").name == "a_tool" and make("x" * 40).name == "x" * 40
    )  # the rest of the spec is valid
    for bad in (PW, "Tool", "a b", "x" * 41, "a.b", "1abc"):
        with pytest.raises(ValueError, match="string_pattern_mismatch|should match pattern"):
            make(bad)


# ---- Issue 8: the file readers and the nested settings error -------------------------------------------------------------
def test_a_source_whose_settings_hold_a_secret_as_api_url_and_an_unknown_key_shows_neither():
    from pydantic import ValidationError

    from hadavin_sdk.sources.kinds import KINDS

    kind = "kubernetes"
    assert kind in KINDS
    for settings in (
        {"api_url": LOGIN_URL, MARK: PW},
        {"api_url": "https://[" + PW, "extra_" + PW: 1},
        {"api_url": PW},
    ):
        with pytest.raises(ValidationError) as err:
            config_mod.SourceConfig(kind=kind, settings=settings)
        text = config_mod.config_error_text(err.value)
        assert PW not in text and MARK not in text and USER not in text, (
            text
        )  # the text the loader shows


def test_a_registry_file_that_is_a_folder_or_has_a_list_as_a_key_is_a_config_error_without_the_path(
    cfg_dir,
):
    (cfg_dir / "chains.yaml").unlink()
    (cfg_dir / "chains.yaml").mkdir()
    with pytest.raises(ConfigError) as err:
        load_registry(load_config(cfg_dir))
    assert str(err.value) == "chains.yaml: cannot be read (IsADirectoryError)"
    assert str(cfg_dir) not in _everything_shown(err.value)
    (cfg_dir / "chains.yaml").rmdir()
    (cfg_dir / "chains.yaml").write_text(f"? [{MARK}]\n: 1\n", encoding="utf-8")
    with pytest.raises(ConfigError) as err:
        load_registry(load_config(cfg_dir))
    assert "a mapping key must be a plain value" in str(
        err.value
    ) and MARK not in _everything_shown(err.value)


# ======================================================================================================================
# Round 8 (batch 8): which names may be shown (D-2322), every file open driven by a configured path, unreadable config
# files, library errors out of validators, pins, and the guard against a config-derived name outside the one filter.
# ======================================================================================================================
# Realistic secret shapes typed where an id belongs: lower case, so the old shape filter let them through.
SECRET_SHAPES = {
    "hex32": "t" + "0123456789abcdef" * 2,  # a letter, then 32 hex digits
    "hex64": "k" + "9f" * 32,
    "long-token": "tok-" + "abcdefghij" * 5,  # 54 characters
    "digit-run": "key" + "7" * 24,
    "forty-one": "w" * 41,
    "sk-style": "sk-" + "a1b2c3d4" * 4,  # a 32 character run of hex digits
    "upper": "Zq9x" + "Mod" + "pw",
}


def _registry_error(cfg_dir) -> str:
    with pytest.raises(ConfigError) as err:
        load_registry(load_config(cfg_dir))
    assert err.value.__cause__ is None
    return str(err.value)


@pytest.mark.parametrize("shape", sorted(SECRET_SHAPES))
def test_a_secret_shaped_text_typed_as_an_id_is_not_shown_by_any_loaded_id_message(cfg_dir, shape):
    """D-2322: the seven plain-id probes of the evidence (agent, action, chain, principal ids typed as a lower case
    secret) read 0 for these realistic shapes: long, hex-like or digit-run texts are shown by position."""
    secret = SECRET_SHAPES[shape]
    rows = (
        ("agents.yaml", lambda d: (d[0].update(id=secret, scope_allowed=["nope_action"]), d)[1]),
        ("agents.yaml", lambda d: (d[0].update(id=secret, model_route="nope_route"), d)[1]),
        (
            "actions/lookup_record.yaml",
            lambda d: (d.update(id=secret, target_system="nope_sys", chain_id="nope_chain"), d)[1],
        ),
        (
            "chains.yaml",
            lambda d: (d[0].update(id=secret), d[0]["steps"][0].update(approver_ids=["nope_p"]), d)[
                2
            ],
        ),
        ("principals.yaml", lambda d: (d[1].update(id=secret, approver_of=["nope_chain"]), d)[1]),
        ("principals.yaml", lambda d: (d[0].update(id=secret, rights=["nope_right"]), d)[1]),
    )
    for name, fn in rows:
        _yaml_edit(name, fn)(cfg_dir)
        try:
            text = _everything_shown(_first_error(lambda: load_registry(load_config(cfg_dir))))
        finally:
            for f in ("agents.yaml", "principals.yaml", "chains.yaml"):
                (cfg_dir / f).write_text(
                    (ROOT / "tests" / "fixtures" / "config" / f).read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
            (cfg_dir / "actions" / "lookup_record.yaml").write_text(
                (
                    ROOT / "tests" / "fixtures" / "config" / "actions" / "lookup_record.yaml"
                ).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        assert secret not in text, (name, text[:300])


def _first_error(fn):
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - the test wants whatever was raised
        return exc
    raise AssertionError("nothing was refused")


def test_a_word_like_loaded_id_prints_as_itself_and_a_reference_that_matched_nothing_never_does(
    cfg_dir,
):
    """The other side of D-2322: real ids (also with a colon) are readable, so a person can find the thing; a
    reference that names nothing is shown by position, even when it is word-like."""
    _yaml_edit("agents.yaml", lambda d: (d[0].update(scope_allowed=["lookup_record", MARK]), d)[1])(
        cfg_dir
    )
    msg = _registry_error(cfg_dir)
    assert "agent test-agent: scope_allowed entry 1 has no contract" in msg and MARK not in msg
    _yaml_edit("agents.yaml", lambda d: (d[0].update(scope_allowed=["lookup_record"]), d)[1])(
        cfg_dir
    )
    _yaml_edit("principals.yaml", lambda d: (d[0].update(rights=["lookup_record", MARK]), d)[1])(
        cfg_dir
    )
    msg = _registry_error(cfg_dir)
    assert "principal svc:test-agent: rights entry 1 names no action" in msg and MARK not in msg


# ---- Issue 2: one reader for every file whose path comes from the configuration -----------------------------------
def _unreadable_variants(tmp_path):
    from os import symlink

    d = tmp_path / ("dir-" + MARK)
    d.mkdir()
    loop = tmp_path / ("loop-" + MARK)
    symlink(loop.name, loop)
    binary = tmp_path / ("bin-" + MARK)
    binary.write_bytes(b"\xff\xfe\x00" + MARK.encode())
    return {
        "missing": tmp_path / ("missing-" + MARK),
        "folder": d,
        "loop": loop,
        "too long": tmp_path / ("n" * 300 + MARK),
        "null byte": tmp_path / (MARK + "\x00"),
        "not UTF-8": binary,
    }


def test_read_configured_gives_one_fixed_sentence_for_every_file_that_cannot_be_read(tmp_path):
    from hadavin_sdk.errors import read_configured

    for label, path in _unreadable_variants(tmp_path).items():
        for binary in (False, True):
            if label == "not UTF-8" and binary:
                continue  # bytes are not decoded
            with pytest.raises(ConfigError) as err:
                read_configured(path, "the test file (a_setting)", binary=binary)
            text = _everything_shown(err.value)
            assert str(err.value).startswith("the test file (a_setting): cannot be read ("), (
                label,
                str(err.value),
            )
            assert MARK not in text and str(tmp_path) not in text, (label, text[:300])
            assert err.value.__cause__ is None and err.value.__suppress_context__ is True


def test_read_configured_returns_none_for_a_missing_file_only_when_asked(tmp_path):
    from hadavin_sdk.errors import read_configured

    assert read_configured(tmp_path / "absent", "x", missing_ok=True) is None
    with pytest.raises(ConfigError):
        read_configured(tmp_path / "absent", "x")
    (tmp_path / "f").write_text("ünï", encoding="utf-8")
    assert read_configured(tmp_path / "f", "x") == "ünï"
    assert read_configured(tmp_path / "f", "x", binary=True) == "ünï".encode()
    # a loop is NOT "does not exist": it is refused even with missing_ok
    from os import symlink

    symlink("self", tmp_path / "self")
    with pytest.raises(ConfigError):
        read_configured(tmp_path / "self", "x", missing_ok=True)


def test_list_configured_reads_a_missing_folder_as_empty_and_an_unlistable_one_as_a_refusal(
    tmp_path, monkeypatch
):
    import os

    from hadavin_sdk.errors import list_configured

    assert list_configured(tmp_path / "absent", "the x folder", ".yaml") == []
    (tmp_path / "b.yaml").write_text("", encoding="utf-8")
    (tmp_path / "a.yaml").write_text("", encoding="utf-8")
    (tmp_path / "c.txt").write_text("", encoding="utf-8")
    assert [p.name for p in list_configured(tmp_path, "the x folder", ".yaml")] == [
        "a.yaml",
        "b.yaml",
    ]
    with pytest.raises(ConfigError) as err:  # a file where a folder belongs
        list_configured(tmp_path / "c.txt", "the x folder", ".yaml")
    assert str(err.value) == "the x folder: cannot be read (NotADirectoryError)"
    real = os.listdir

    def denied(path="."):
        if str(path) == str(tmp_path):
            raise PermissionError(13, "denied " + MARK, str(path))
        return real(path)

    monkeypatch.setattr(os, "listdir", denied)
    with pytest.raises(ConfigError) as err:
        list_configured(tmp_path, "the x folder", ".yaml")
    assert str(err.value) == "the x folder: cannot be read (PermissionError)"
    assert MARK not in _everything_shown(err.value)


@pytest.mark.parametrize(
    "name", ["config.yaml", "egress.yaml", "agents.yaml", "principals.yaml", "chains.yaml"]
)
def test_a_config_file_that_is_a_loop_of_links_is_refused_never_read_as_empty(cfg_dir, name):
    path = cfg_dir / name
    path.unlink()
    path.symlink_to(path.name)  # a link to itself
    exc = _first_error(lambda: load_registry(load_config(cfg_dir)))
    assert isinstance(exc, ConfigError) and f"{name}: cannot be read (" in str(exc), str(exc)
    assert exc.__cause__ is None and str(cfg_dir) not in _everything_shown(exc)


def test_an_actions_file_a_tools_manifest_or_a_folder_that_cannot_be_read_is_refused(
    cfg_dir, monkeypatch
):
    import os

    (cfg_dir / "actions" / "lookup_record.yaml").unlink()
    (cfg_dir / "actions" / "lookup_record.yaml").symlink_to("lookup_record.yaml")
    exc = _first_error(lambda: load_registry(load_config(cfg_dir)))
    assert "a file in actions/: cannot be read (" in str(exc), str(exc)
    (cfg_dir / "actions" / "lookup_record.yaml").unlink()
    (cfg_dir / "actions" / "lookup_record.yaml").write_text(
        (ROOT / "tests/fixtures/config/actions/lookup_record.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (cfg_dir / "tools").mkdir(exist_ok=True)
    (cfg_dir / "tools" / "test-agent.yaml").mkdir()  # a folder where the manifest belongs
    exc = _first_error(lambda: load_registry(load_config(cfg_dir)))
    assert "tools/test-agent.yaml (an agent's tool manifest): cannot be read (" in str(exc), str(
        exc
    )
    (cfg_dir / "tools" / "test-agent.yaml").rmdir()
    real = os.listdir
    target = str(cfg_dir / "actions")

    def denied(path="."):
        if str(path) == target:
            raise PermissionError(13, "denied", str(path))
        return real(path)

    monkeypatch.setattr(os, "listdir", denied)
    exc = _first_error(lambda: load_registry(load_config(cfg_dir)))
    assert str(exc) == "the actions/ folder: cannot be read (PermissionError)", str(exc)


def test_a_tls_ca_file_that_cannot_be_read_is_refused_with_a_fixed_sentence(cfg_dir):
    cfg = load_config(cfg_dir)
    stub = SimpleNamespace(get=lambda name: "x")
    (cfg_dir / ("bin-" + MARK + ".pem")).write_bytes(b"\xff\xfe" + MARK.encode())
    (cfg_dir / ("dir-" + MARK + ".pem")).mkdir()
    for name in (
        "absent-" + MARK + ".pem",
        "dir-" + MARK + ".pem",
        "bin-" + MARK + ".pem",
        "n" * 300 + MARK + ".pem",
        MARK + "\x00.pem",
    ):
        with pytest.raises(ConfigError) as err:
            app_mod._tls_context(cfg, stub, name, None)
        text = _everything_shown(err.value)
        assert MARK not in text and str(cfg_dir) not in text, (name[:20], text[:300])
        assert err.value.__cause__ is None


def test_a_ca_file_that_is_not_a_file_in_the_config_folder_is_refused_at_load(cfg_dir):
    """A missing, escaping or over-long ca_file is found when the registry loads (as `prompt_file` is), for a tool's
    manifest and for a configured source."""
    head = (
        "- name: t\n  function: m:f\n  description: d\n  input_schema: {type: object}\n"
        "  side_effect: none\n  hosts: [api.example.com]\n  ca_file: "
    )
    for ca, said in (
        ("absent.pem", "ca_file is not a file in the config folder"),
        ("../outside.pem", "ca_file escapes the config folder or cannot be resolved"),
        ("n" * 300 + MARK + ".pem", "ca_file"),
    ):
        _raw_file("tools/test-agent.yaml", head + ca + "\n", append=False)(cfg_dir)
        _yaml_edit("agents.yaml", lambda d: (d[0].update(tools_allowed=["t"]), d)[1])(cfg_dir)
        msg = _registry_error(cfg_dir)
        assert said in msg and MARK not in msg, (ca[:12], msg[:300])
    _yaml_edit("agents.yaml", lambda d: (d[0].update(tools_allowed=[]), d)[1])(cfg_dir)
    (cfg_dir / "tools" / "test-agent.yaml").unlink()
    _edit(
        cfg_dir,
        lambda d: d.update(
            sources={
                "k8s": {
                    "kind": "kubernetes",
                    "ca_file": "absent.pem",
                    "settings": {"api_url": "https://k8s.example", "namespaces": ["ns"]},
                }
            }
        ),
    )
    exc = _first_error(lambda: load_registry(load_config(cfg_dir)))
    assert "source k8s: ca_file is not a file in the config folder" in str(exc), str(exc)


def test_confined_refuses_a_loop_a_null_byte_and_an_over_long_name_with_a_fixed_sentence(tmp_path):
    from os import symlink

    symlink("a", tmp_path / "a")
    with pytest.raises(ConfigError) as err:
        config_mod.confined(tmp_path, "x\x00y")
    assert str(err.value) == "path cannot be resolved" and err.value.__cause__ is None
    # a loop or an over-long name resolves (the open that follows is what refuses it, through read_configured)
    for rel in ("a", "n" * 5000):
        assert config_mod.confined(tmp_path, rel).is_relative_to(tmp_path.resolve())


def test_the_other_configured_paths_say_a_fixed_sentence_when_they_cannot_be_read(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace as NS

    from hadavin_sdk.audit.local_dir import LocalDirSink
    from hadavin_sdk.audit.signer import build_local
    from hadavin_sdk.llm.fake import FakeLLM, UnknownRecording
    from hadavin_sdk.store.postgres import ca_file

    absent = tmp_path / ("absent-" + MARK)
    folder = tmp_path / ("folder-" + MARK)
    folder.mkdir()
    for path in (absent, folder, tmp_path / ("n" * 300 + MARK)):
        # private_key_path
        with pytest.raises(ConfigError) as err:
            build_local(
                NS(
                    private_key_path=path, private_key_secret_name=None, passphrase_secret_name=None
                ),
                NS(resolve=lambda n: ""),
            )
        assert "private_key_path" in str(err.value) and MARK not in _everything_shown(err.value)
        # sslrootcert
        with pytest.raises(ConfigError) as err:
            ca_file(NS(sslrootcert=str(path), sslrootcert_secret_name=None), None)
        assert "sslrootcert" in str(err.value) and MARK not in _everything_shown(err.value)
        # ca_cert and jwt_path (Vault)
        from hadavin_sdk.backends.factory import make

        base = {"kind": "vault", "address": "https://vault.example"}
        with pytest.raises(ConfigError) as err:
            make("secrets", table.VaultSettings(**base, ca_cert=path))
        assert "ca_cert" in str(err.value) and MARK not in _everything_shown(err.value)
        k8s = table.VaultSettings(**base, auth="kubernetes", role="r", jwt_path=path)
        with pytest.raises(ConfigError) as err:
            make("secrets", k8s).get("a_name")
        assert "jwt_path" in str(err.value) and MARK not in _everything_shown(err.value)
    # a recorded reply file that is a folder, and the audit folder's index
    digest_dir = tmp_path / "rec"
    digest_dir.mkdir()
    llm = FakeLLM(
        digest_dir, {"default": NS(input_usd_per_mtok=0, output_usd_per_mtok=0, model_id="m")}
    )
    import hashlib
    import json

    doc = json.dumps([{"role": "user", "content": "q"}], sort_keys=True).encode()
    (digest_dir / f"{hashlib.sha256(doc).hexdigest()}-1.json").write_bytes(b"\xff" + MARK.encode())
    with pytest.raises(ConfigError) as err:
        llm.chat([{"role": "user", "content": "q"}], system="s", route="default")
    assert "recorded_dir" in str(err.value) and MARK not in _everything_shown(err.value)
    with pytest.raises(UnknownRecording):  # an absent recording keeps its own error
        llm.chat([{"role": "user", "content": "z"}], system="s", route="default")
    sink = LocalDirSink(tmp_path / ("sink-" + MARK))
    (tmp_path / ("sink-" + MARK)).mkdir()
    (tmp_path / ("sink-" + MARK) / "index.jsonl").mkdir()  # a folder where the index belongs
    with pytest.raises(ConfigError) as err:
        sink._entries()
    assert "audit index" in str(err.value) and MARK not in _everything_shown(err.value)
    monkeypatch.undo()


# ---- Issue 3: a pin is a digest, and a pasted credential in the pin position is never printed ---------------------
def test_a_tool_module_pin_must_be_a_sha256_and_none_of_it_is_printed(cfg_dir):
    from hadavin_sdk.errors import NOT_SHOWN, digest_prefix, is_digest

    good = "ab" * 32
    assert is_digest(good) and digest_prefix(good) == good[:12] + "..."
    for bad in (MARK, "AB" * 32, "ab" * 31, "ab" * 33 + "x", 5, None, ""):
        assert not is_digest(bad) and digest_prefix(bad) == NOT_SHOWN
    _edit(cfg_dir, lambda d: d.update(tool_modules=["m"], tool_module_hashes={"m": MARK + "-pin"}))
    exc = _first_error(lambda: load_config(cfg_dir))
    assert "tool_module_hashes: entries 0 are not a SHA-256" in str(exc), str(exc)
    assert MARK not in _everything_shown(exc) and exc.__cause__ is None


def test_a_module_whose_pin_does_not_match_prints_the_real_digest_prefix_and_never_the_pin(
    tmp_path, monkeypatch
):
    from hadavin_sdk import tools as tools_mod

    (tmp_path / "pinmod.py").write_text("VALUE = 1\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    for pin in (MARK + "-" + "pin" * 8, "ab" * 32):
        with pytest.raises(ConfigError) as err:
            tools_mod.load_tool_module("pinmod", {"pinmod": pin})
        text = _everything_shown(err.value)
        assert "the pin says " + ("<not shown>" if pin != "ab" * 32 else "abababababab...") in text
        assert pin not in text and MARK not in text


# ---- Issue 4: names inside the secrets, model, source, tool and approval messages ------------------------------------
def test_a_vault_environment_variable_name_and_field_are_pattern_checked_and_never_quoted():
    from pydantic import ValidationError

    from hadavin_sdk.backends.factory import make

    base = {"kind": "vault", "address": "https://vault.example"}
    for field_name in ("token_env", "secret_id_env"):
        for bad in (PW, "hvs." + "a1" * 12, "9starts_with_digit", "has space", ""):
            with pytest.raises(ValidationError) as err:
                table.VaultSettings(**base, **{field_name: bad})
            assert bad == "" or bad not in config_mod.config_error_text(err.value)
    with pytest.raises(ValidationError):
        table.VaultSettings(**base, field="a b")
    with pytest.raises(ValidationError):
        table.VaultSettings(**base, auth="approle", role_id="has space")
    envname = "ZQ_PROBE_" + "MK4417"  # a legal name that is not set
    for settings in (
        table.VaultSettings(**base, token_env=envname),
        table.VaultSettings(**base, auth="approle", role_id="r", secret_id_env=envname),
    ):
        provider = make("secrets", settings)
        with pytest.raises(ConfigError) as err:
            provider.get("a_name")
        assert str(err.value) == "secrets vault: the configured environment variable is not set"
        assert envname not in _everything_shown(err.value)


def test_a_vault_secret_name_and_field_are_not_quoted_in_vault_refusals(monkeypatch):
    from hadavin_sdk.backends.factory import make
    from tests.contracts.vault_fake import ROOT as VAULT_ROOT
    from tests.contracts.vault_fake import fake_vault

    monkeypatch.setenv("VAULT_TOKEN", VAULT_ROOT)

    vault = fake_vault()
    vault.kv["secret/app/good_name"] = {"other": "x"}
    provider = make(
        "secrets",
        table.VaultSettings(
            kind="vault", address=vault.address, path_prefix="app/", field="fld" + MARK[:6]
        ),
    )
    with pytest.raises(ConfigError) as err:
        provider.get(PW + "/bad name")  # not a legal Vault name
    assert PW not in str(err.value) and "<not shown>" in str(err.value)
    with pytest.raises(ConfigError) as err:
        provider.get("a" * 64)
    assert "a" * 64 not in str(err.value) and "not found in Vault" in str(err.value)
    with pytest.raises(ConfigError) as err:
        provider.get("good_name")  # a real name, but the field is absent
    assert "good_name" in str(err.value) and "fld" + MARK[:6] not in str(err.value)


def test_an_alias_model_id_is_refused_without_quoting_the_model_id():
    from hadavin_sdk.llm.common import pinned

    routes = {"default": SimpleNamespace(model_id=MARK + "-latest")}
    with pytest.raises(ConfigError) as err:
        pinned(routes)
    assert "route default: model_id is an alias that moves to new models" in str(err.value)
    assert MARK not in _everything_shown(err.value)


def test_a_tool_call_names_no_operation_host_or_method_the_manifest_did_not_define():
    from hadavin_sdk import tools as tools_mod
    from tests.test_k5_review import _ctx

    for call, said in (
        ({"op": MARK + "op", "url": "https://api.example.com/x", "method": "GET"}, "the operation is not on"),
        ({"op": "bundle.read", "url": "https://" + MARK + ".example/x", "method": "GET"}, "the host is not in"),
        ({"op": "bundle.read", "url": "https://api.example.com/x", "method": "POST"}, "the method is not the one bound to operation bundle.read"),
    ):  # fmt: skip
        with pytest.raises(tools_mod.ToolRefused) as err:
            _ctx().fetch(call["method"], call["url"], operation=call["op"])
        assert said in str(err.value) and MARK not in _everything_shown(err.value), str(err.value)


def test_a_source_and_a_tool_secret_are_named_only_by_the_loaded_filter(cfg_dir):
    from hadavin_sdk import tools as tools_mod

    spec = tools_mod.ToolSpec(
        name="a_tool", function="m:f", description="d", input_schema={"type": "object"},
        side_effect="none", secret_names=("good_secret",),
    )  # fmt: skip
    read = app_mod._own_secrets(SimpleNamespace(get=lambda n: n), spec)
    with pytest.raises(PermissionError) as err:
        read(MARK)
    assert str(err.value) == "that secret is not one of tool a_tool's secrets"
    assert MARK not in _everything_shown(err.value)


def test_the_platform_secret_probe_shows_a_configured_name_and_hides_a_pasted_one():
    from hadavin_sdk.backends import platform_secrets as ps

    class Missing:
        def get(self, name):
            raise KeyError(name)

    with pytest.raises(ConfigError) as err:
        ps.check(Missing(), [], {"good_secret"})
    assert str(err.value) == "secret good_secret cannot be read at start-up (KeyError)"
    for pasted in (
        PW,
        SECRET_SHAPES["hex32"],
        SECRET_SHAPES["long-token"],
        SECRET_SHAPES["digit-run"],
    ):
        with pytest.raises(ConfigError) as err:
            ps.check(Missing(), [], {pasted})  # one name: the one that is refused first
        assert str(err.value) == "secret <not shown> cannot be read at start-up (KeyError)", pasted
        assert pasted not in str(err.value)


# ---- the guard: no config-derived name is put in a message except through the one filter -------------------------------
GUARDED_MODULES = (
    "app.py",
    "actions/secrets_vault.py",
    "actions/secrets_aws.py",
    "actions/secrets_azure.py",
    "actions/secrets_cache.py",
    "actions/secrets_env.py",
    "actions/secrets_file.py",
    "actions/secrets_gcp.py",
    "actions/contract.py",
    "llm/common.py",
    "backends/table.py",
    "backends/platform_secrets.py",
    "audit/signer.py",
    "tools.py",
    "registry.py",
    "config.py",
    "deferred.py",
    "sources/__init__.py",
)
# Spellings that, in these modules, hold text taken from a configuration file (a name, an id, a key, a path, a value).
CONFIG_DERIVED = frozenset(
    {
        "name", "agent_id", "action", "key", "source", "module", "route", "field", "auth_mount",
        "token_env", "secret_id_env", "jwt_path", "role_id", "host", "operation", "method", "pin",
        "named", "ca_file", "ca_cert", "model_id", "path",
    }
)  # fmt: skip
CONFIG_DERIVED_ATTRS = frozenset(
    {"name", "id", "model_id", "field", "auth_mount", "token_env", "secret_id_env", "jwt_path", "role_id", "hostname", "ca_file", "ca_cert", "private_key_path", "pin"}
)  # fmt: skip
# (module, source of the f-string or call) pairs that are allowed, each with the reason.
# One entry per f-string that holds a configuration-looking spelling but is not config text, each with its reason.
_FILTERED = "the variable was set from shown_name / _named on an earlier line"
_CODE_NAME = "the spelling is a constant or a keyword of the code, not a value read from a file"
_NOT_TEXT = "a URL, a dictionary key or a file name being built, never put in a message"
_OPERATOR = "an operator's own command-line key file (not a value read from the configuration file)"
GUARD_ALLOWED = {
    ("app.py", "f'configure backends.{name} in pilot and prod'"): _CODE_NAME,
    ("app.py", "f'{name}= is for tests; {fix}'"): _CODE_NAME,
    ("app.py", "f'tool:{t.name}'"): _NOT_TEXT,
    ("actions/secrets_gcp.py", "f'projects/{self.project_id}/secrets/{name}/versions/latest'"): _NOT_TEXT,
    ("actions/secrets_vault.py", "f'auth/{auth_mount}/login'"): _NOT_TEXT,
    ("actions/secrets_vault.py", "f'{self.address}/v1/{path}'"): _NOT_TEXT,
    ("actions/secrets_vault.py", "f'{self.mount}/data/{self.path_prefix}{name}'"): _NOT_TEXT,
    ("actions/contract.py", "f'{where}: {key} must be a non-negative integer'"): _CODE_NAME,
    ("audit/signer.py", "f'{path} is a symlink: a key file is never used through one'"): _OPERATOR,
    ("audit/signer.py", "f'{path} is outside {folder}: key files are kept only there (set {KEY_DIR_ENV} to choose another folder)'"): _OPERATOR,
    ("audit/signer.py", "f'{source} is not an Ed25519 private key'"): "source is a fixed label chosen by build_local",
    ("audit/signer.py", "f'{path} is not an Ed25519 public key'"): _OPERATOR,
    ("audit/signer.py", "f'signer ed25519_local: cannot load {source} ({type(exc).__name__})'"): "source is a fixed label chosen by build_local",
    ("tools.py", "f'[{host}]'"): _NOT_TEXT,
    ("tools.py", "f'{where}: key {key!r} is not available until {phase}'"): "key is one of the code's own _DEFERRED_KEYS",
    ("registry.py", "f'{agent_id}.jsonl'"): _NOT_TEXT,
    ("registry.py", "f'{agent_id}.yaml'"): _NOT_TEXT,
    ("registry.py", "f'principal {name}: rights entry {i} names no action'"): _FILTERED,
    ("registry.py", "f'principal {name}: approver_of entry {i} names no chain'"): _FILTERED,
    ("config.py", "f'evidence.{name}: {len(bad)} entries are not ports'"): _CODE_NAME,
    ("deferred.py", "f'agent {a_name}: level act for {name} arrives in Phase 4'"): _FILTERED,
    ("deferred.py", "f'agent {a_name}: suggest for {name} cannot load before K6 and K8'"): _FILTERED,
    ("deferred.py", "f'agent {a_name}: {name} is a none contract and can never be suggest'"): _FILTERED,
    ("deferred.py", "f'agent {a_name}: suggest for sign_off action {name} arrives in Phase 3'"): _FILTERED,
}  # fmt: skip


def _config_derived(expr) -> bool:
    import ast

    if isinstance(expr, ast.Name):
        return expr.id in CONFIG_DERIVED
    if isinstance(expr, ast.Attribute):
        return expr.attr in CONFIG_DERIVED_ATTRS
    return False


def _guard_violations() -> list[str]:
    import ast

    found = []
    for module in GUARDED_MODULES:
        tree = ast.parse((ROOT / "src" / "hadavin_sdk" / module).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.JoinedStr):
                text = ast.unparse(node)
                for part in node.values:
                    if (
                        isinstance(part, ast.FormattedValue)
                        and _config_derived(part.value)
                        and (module, text) not in GUARD_ALLOWED
                    ):
                        found.append(
                            f"{module}:{node.lineno}: {{{ast.unparse(part.value)}}} in {text}"
                        )
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"warning", "info", "error", "debug", "exception"}
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id.lower().endswith("log")
            ):
                found += [
                    f"{module}:{node.lineno}: log argument {ast.unparse(arg)}"
                    for arg in node.args[1:]
                    if _config_derived(arg)
                ]
    return found


def test_no_config_derived_name_is_put_in_a_message_outside_the_one_filter():
    """The class (Issue 4 of round 8): a name, id, key or path that a configuration file holds is printed only through
    `shown_name` (or said by position or as the field). Looks at every f-string and every log argument of the modules
    that build messages; the allowed exceptions are listed above with their reason."""
    assert not (found := _guard_violations()), "\n".join(found)


def test_the_guard_sees_a_name_printed_outside_the_filter(tmp_path, monkeypatch):
    """The guard fails on the pattern it is for: the same scan over a module with one raw name."""
    import ast

    bad = ast.parse('raise ValueError(f"secret {name} cannot be read")')
    assert any(
        isinstance(p, ast.FormattedValue) and _config_derived(p.value)
        for n in ast.walk(bad)
        if isinstance(n, ast.JoinedStr)
        for p in n.values
    )
    ok = ast.parse('raise ValueError(f"secret {shown_name(name)} cannot be read")')
    assert not any(
        isinstance(p, ast.FormattedValue) and _config_derived(p.value)
        for n in ast.walk(ok)
        if isinstance(n, ast.JoinedStr)
        for p in n.values
    )


# ---- Issue 7: a library error out of a validator, and a configuration that cannot be read ---------------------------
def test_a_decimal_error_out_of_a_validator_is_a_fixed_sentence_config_error(cfg_dir, monkeypatch):
    import dataclasses
    import sys
    import types
    from decimal import Decimal

    from pydantic import field_validator

    monkeypatch.setitem(sys.modules, "hadavin_sdk._decimal_probe", types.ModuleType("x"))

    class XS(table.KindSettings):
        n: str

        @field_validator("n")
        @classmethod
        def _c(cls, x):
            return Decimal(
                x
            )  # raises decimal.InvalidOperation, which pydantic does not turn into a problem

    XS.__module__ = "hadavin_sdk._decimal_probe"
    entry = dataclasses.replace(table.TABLE["secrets"]["env"], settings=XS)
    monkeypatch.setitem(table.TABLE["secrets"], "xx", entry)
    _edit(cfg_dir, lambda d: d["backends"].update(secrets={"kind": "xx", "n": MARK}))
    exc = _first_error(lambda: load_config(cfg_dir))
    assert isinstance(exc, ConfigError), type(exc)
    assert "InvalidOperation" in str(exc) and MARK not in _everything_shown(exc)
    assert exc.__cause__ is None and exc.__suppress_context__ is True


# ---- Issue 8: an empty manifest names no tool, so it cannot narrow tools_allowed -------------------------------------
def test_an_empty_tools_manifest_does_not_refuse_tools_allowed_but_a_manifest_with_tools_does(
    cfg_dir,
):
    _yaml_edit("agents.yaml", lambda d: (d[0].update(tools_allowed=["t_x"]), d)[1])(cfg_dir)
    (cfg_dir / "tools").mkdir(exist_ok=True)
    (cfg_dir / "tools" / "test-agent.yaml").write_text("[]\n", encoding="utf-8")
    reg = load_registry(load_config(cfg_dir))  # nothing is refused: the manifest holds no tool
    assert reg.tools["test-agent"] == {}
    (cfg_dir / "tools" / "test-agent.yaml").unlink()
    assert "test-agent" not in load_registry(load_config(cfg_dir)).tools  # no file: the same


# ---- Issue 9: a manifest entry that is not a mapping of text keys, and the ports ----------------------------------------
def test_a_manifest_entry_with_a_non_text_key_is_a_config_error_and_ports_are_counted():
    from hadavin_sdk.tools import ToolSpec, parse_manifest, spec_problems

    for entry in ({1: "x"}, {None: 2}, {MARK: 1, 3: 4}):
        with pytest.raises(ConfigError) as err:
            parse_manifest([entry], "tools/a.yaml")
        assert MARK not in _everything_shown(err.value) and err.value.__cause__ is None
    spec = ToolSpec(
        name="a_tool", function="m:f", description="d", input_schema={"type": "object"},
        side_effect="none", ports=(0, 70000, 443),
    )  # fmt: skip
    text = " ".join(spec_problems(spec, ["m"]))
    assert "2 ports entries are not valid" in text and "70000" not in text


def test_a_registry_file_entry_that_is_not_a_mapping_says_which_entry(cfg_dir):
    (cfg_dir / "chains.yaml").write_text("- just a text\n", encoding="utf-8")
    exc = _first_error(lambda: load_registry(load_config(cfg_dir)))
    assert str(exc) == "chains.yaml: entry 1 is not a mapping"


def test_a_chain_that_no_principal_names_keeps_channel_native_approver_ids(cfg_dir):
    """D-2322 / Issue 1: approver_ids are checked against principals.yaml only for a chain some principal names in
    `approver_of` (a person link). A chain nobody names keeps ids the channel understands (a Slack user id)."""
    _yaml_edit(
        "chains.yaml",
        lambda d: (d[0]["steps"][0].update(approver_ids=["slack:U12345678"]), d)[1],
    )(cfg_dir)
    _yaml_edit("principals.yaml", lambda d: ([p.update(approver_of=[]) for p in d], d)[1])(cfg_dir)
    load_registry(load_config(cfg_dir))  # nothing refused
    _yaml_edit("principals.yaml", lambda d: (d[1].update(approver_of=["chain-abc"]), d)[1])(cfg_dir)
    assert "approver_ids entry 0 is not a person" in _registry_error(cfg_dir)


# ---- the run-time opens driven by configured folders go through the same reader ---------------------------------------
def test_a_prompt_or_golden_file_that_cannot_be_read_is_refused_and_a_missing_golden_file_is_empty(
    cfg_dir,
):
    reg = load_registry(load_config(cfg_dir))
    assert reg.prompt_sha256("test-agent") and reg.prompt("test-agent")
    prompt = cfg_dir / "prompts" / "test-agent.md"
    saved = prompt.read_bytes()
    prompt.unlink()
    prompt.symlink_to(prompt.name)  # a loop of links
    for call in (reg.prompt, reg.prompt_sha256):
        with pytest.raises(ConfigError) as err:
            call("test-agent")
        assert str(err.value) == "an agent's prompt_file: cannot be read (OSError)" or str(
            err.value
        ).startswith("an agent's prompt_file: cannot be read (")
        assert str(cfg_dir) not in _everything_shown(err.value)
    prompt.unlink()
    prompt.write_bytes(saved)
    golden = reg.golden_path("test-agent")
    saved_golden = golden.read_bytes()
    golden.unlink()
    assert (
        reg.golden_sha256("test-agent") == ""
    )  # a missing set is not an error here (the gate says so)
    golden.mkdir()  # a folder where the file belongs: not read as empty
    with pytest.raises(ConfigError) as err:
        reg.golden_sha256("test-agent")
    assert str(err.value) == "a golden set file (golden_dir): cannot be read (IsADirectoryError)"
    golden.rmdir()
    golden.write_bytes(saved_golden)
    assert len(reg.golden_sha256("test-agent")) == 64


def test_a_kubernetes_api_url_with_a_login_does_not_put_the_url_in_the_raw_error_either():
    from pydantic import ValidationError

    from hadavin_sdk.sources.kubernetes import KubernetesSettings

    with pytest.raises(ValidationError) as err:
        KubernetesSettings(api_url="https://" + USER + ":" + PW + "@h.example", namespaces=("a",))
    assert PW not in str(err.value) and USER not in str(err.value)
