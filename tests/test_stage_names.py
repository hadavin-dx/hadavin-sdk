"""The stages are exactly demo, pilot and prod. The old first stage name is refused, never read as a stage, and a
class test keeps the old word out of every place that names a stage.

No stage is stored anywhere today, so there is no read site to test. The first change that stores one must map an old
value to demo on read for display only (never for a guard decision) and add a test through that real read site.

Rows: unknown stage and half-renamed flag refuse start; the class test looks at stage POSITIONS only; pilot and prod
refuse relaxed kinds; the live and prod-only guards fail closed on a value that is not a stage.
"""

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
    assert "base_url must not contain a login" in str(exc)
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
    assert "not a valid URL" in str(exc) or "a value was refused" in str(exc), str(exc)


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
    """The old `url_has_login` said False for a text it could not read."""
    from hadavin_sdk.config import url_allowed, url_has_login
    from hadavin_sdk.safe_url import InvalidUrl

    with pytest.raises(InvalidUrl):
        url_has_login(WIDE_URL)
    assert url_allowed(WIDE_URL, True) is False


def test_no_module_splits_a_configured_url_without_the_safe_splitter():
    """The class: every `urlsplit` of a value that came from a file or a model goes through `safe_urlsplit`."""
    own = ROOT / "src" / "hadavin_sdk" / "safe_url.py"
    users = [
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "src").rglob("*.py")
        if p != own
        and re.search(
            r"(?<![\w.])urlsplit\(|urlparse\(|urllib\.parse\.urlsplit",
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
        ({"model_route": PW}, "unknown model_route <not shown>"),
        ({"scope_allowed": [PW]}, "no contract for <not shown>"),
    ],
)
def test_a_name_pasted_where_the_registry_expects_a_known_one_is_not_shown(cfg_dir, over, said):
    exc = _refused(cfg_dir, extra_file=("agents.yaml", _agent_entry(**over)))
    _assert_value_free(exc, PW)
    assert said in str(exc), str(exc)


def test_a_plain_name_is_still_shown_so_the_user_can_find_the_problem(cfg_dir):
    exc = _refused(cfg_dir, extra_file=("agents.yaml", _agent_entry(model_route="no-such-route")))
    assert "unknown model_route no-such-route" in str(exc), str(exc)


def test_the_name_filter_is_a_shape_check_only():
    from hadavin_sdk.errors import NOT_SHOWN, shown_name

    assert (
        shown_name("lookup_record") == "lookup_record"
        and shown_name("k8s.pods-list") == "k8s.pods-list"
    )
    for odd in (PW, "", "a b", "x" * 65, "ａbc", "naïve", None, 5, "Lookup"):
        assert shown_name(odd) == NOT_SHOWN, odd


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
    assert "replace()" in text and "refused too" in text


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
