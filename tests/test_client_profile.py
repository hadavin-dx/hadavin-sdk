"""The client-profile check: what a pilot or prod start refuses that a demo start allows.

The prod fixture loads; demo-only kinds not covered elsewhere are refused; every TABLE pair is decided; the build
keywords are checked in a client profile (pilot or prod); a demo config that names a real model, a vendor detector
or a real approval channel must say it holds only made-up data.

Import rule: module-level names must exist before the check was added, so that a missing name fails one row and
not the whole file. Names that exist only with the check (`_test_doubles_given`, `_LIVE_HOOKS`, `LOCAL_DETECTORS`,
`_sends_text_out`, the keyword `allow_test_doubles`, the config key `made_up_data_only`) are read inside row bodies, so without the check each
row fails alone.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import os
import sys
from itertools import product
from pathlib import Path
from types import SimpleNamespace

import pytest

from hadavin_sdk import app as app_mod
from hadavin_sdk.approvals.channel import FakeChannel
from hadavin_sdk.backends.table import DEMO_ONLY, NOT_PROD, TABLE
from hadavin_sdk.config import ConfigError, load_config
from tests.k5_support import edit_config as _edit
from tests.test_k3_pilot import ScriptedLLM
from tests.test_k3_pilot_env import pilot_cfg
from tests.test_stage_names import ANCHOR, KEY_SECRET

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src" / "hadavin_sdk"
DEMOS = REPO / "demos"


# --- shared helpers ----------------------------------------------------------------------------------------


def prod_cfg(tmp_path: Path) -> Path:
    """`pilot_cfg` as prod: a signer whose key comes from the secrets kind, and an anchor whose retention is agreed."""
    root = pilot_cfg(tmp_path, env="prod")

    def prod(
        d,
    ):  # the signer and anchor dicts of test_stage_names (prod refuses a key file and an unagreed anchor)
        d["backends"]["signer"] = dict(KEY_SECRET)
        d["backends"]["anchor"] = ANCHOR | {"retention_ack": True}

    _edit(root, prod)
    return root


def _cfg_for(tmp_path: Path, env: str) -> Path:
    return prod_cfg(tmp_path) if env == "prod" else pilot_cfg(tmp_path, env=env)


class _Reached(Exception):
    """Raised by the patched `make` for every capability but secrets: the check let the build through."""


class _MadeSecrets:
    """A made-up provider that answers EVERY secret name with a made-up value built from parts. Not
    `FakeSecretProvider`: that one raises KeyError for a name it was not given, and these rows reach `build` with
    a config whose secret names they do not list (the patched `make` stops the build right after secrets)."""

    def get(self, name: str) -> str:
        return "made" + "-up-" + name


class _FalsyChannel:
    def __len__(self) -> int:
        return 0


class _StubDetector:
    backend = "regex"

    def check(self, text, source):
        raise AssertionError("the detector is named in the config, never run")


@pytest.fixture
def made(monkeypatch):
    """Patch `app.make`: records capabilities, answers `secrets`, raises `_Reached` for the rest. So no row builds
    a signer, a store or a channel, and none touches a network, a folder of secrets or Postgres."""
    record: list[str] = []

    def fake_make(capability, *args, **kwargs):
        record.append(capability)
        if capability == "secrets":
            return _MadeSecrets()
        raise _Reached(capability)

    monkeypatch.setattr(app_mod, "make", fake_make)
    return record


# One value per refused build keyword, not equal to its default. A new keyword with no sample fails
# test_every_refused_keyword_has_a_sample (and the rows that read SAMPLES), so it gets decided: a sample, or a reviewed `_LIVE_HOOKS` entry.
SAMPLES = {
    "secrets": _MadeSecrets(),
    "channel": FakeChannel(),
    "detector": _StubDetector(),
    "llm": ScriptedLLM(),
    "clock": lambda: None,
}
REFUSED = [
    n
    for n, p in inspect.signature(app_mod.build).parameters.items()
    if p.kind is p.KEYWORD_ONLY
    and n not in {"tools", "sources", "hold_run_ids", "timeout_s", "allow_test_doubles"}
]


# --- the prod fixture --------------------------------------------------------------------------------------


def test_the_prod_fixture_loads(tmp_path):
    assert load_config(prod_cfg(tmp_path)).environment == "prod"


# --- demo-only kinds refused in a client profile -----------------------------------------------------------


@pytest.mark.parametrize("env", ["pilot", "prod"])
def test_secrets_env_is_refused_in_a_client_profile(tmp_path, env):
    root = _cfg_for(tmp_path, env)
    _edit(root, lambda d: d["backends"].update(secrets={"kind": "env"}))
    with pytest.raises(ConfigError, match=f"environment {env}: refused") as err:
        load_config(root)
    assert "secrets: env" in str(err.value)
    assert "made_up_data_only" not in str(err.value)  # the field is refused here: never advise it


def test_a_pilot_config_that_omits_store_is_refused(tmp_path):
    root = pilot_cfg(tmp_path)
    _edit(root, lambda d: d["backends"].pop("store"))
    with pytest.raises(ConfigError, match="environment pilot: refused") as err:
        load_config(root)
    assert "store: memory" in str(err.value)
    assert "made_up_data_only" not in str(err.value)


def test_a_demo_anchor_only_failure_does_not_advise_the_field(cfg_dir):
    """A demo config that fails only on a COMPLIANCE anchor sends no text out: no advice about made-up data."""

    def anchor_only(d):
        d["backends"]["audit"] = {"kind": "chain"}
        d["backends"]["anchor"] = ANCHOR | {"mode": "COMPLIANCE"}

    _edit(cfg_dir, anchor_only)
    with pytest.raises(ConfigError, match="COMPLIANCE") as err:
        load_config(cfg_dir)
    assert "made_up_data_only" not in str(err.value)


# --- every TABLE pair is decided ---------------------------------------------------------------------------

# One reason per pair: who runs the kind, and what the check does about it. Three kinds of statement are checked
# against the code by `test_the_facts_stated_in_the_reasons_are_true`: "refused in prod by NOT_PROD", "sends text out"
# and "sends no text out". The rest says who runs it and what it can and cannot do.
CLIENT_REVIEWED: dict[tuple[str, str], str] = {
    (
        "secrets",
        "aws_secrets_manager",
    ): "the client's managed secret store; read by name, no value in config",
    (
        "secrets",
        "vault",
    ): "a self-hostable secret store the client runs; read by name, no value in config",
    (
        "secrets",
        "azure_key_vault",
    ): "the client's managed secret store; read by name, no value in config",
    (
        "secrets",
        "gcp_secret_manager",
    ): "the client's managed secret store; read by name, no value in config",
    (
        "secrets",
        "mounted_file",
    ): "files the platform mounts for the process; read by name, never written",
    ("signer", "none"): "no signature; allowed in pilot, refused in prod by `NOT_PROD`",
    (
        "signer",
        "ed25519_local",
    ): "a local key from the secrets kind; prod refuses a key file in the image",
    (
        "signer",
        "aws_kms",
    ): "the client's managed key service; it signs digests and never exports the key",
    ("signer", "azure_key_vault_key"): "the client's managed key service; it signs digests only",
    (
        "signer",
        "gcp_kms",
    ): "the client's managed key service; it signs digests and never exports the key",
    (
        "signer",
        "vault_transit",
    ): "a self-hostable signing service the client runs; it signs digests only",
    ("anchor", "none"): "no outside anchor; allowed in pilot, refused in prod by `NOT_PROD`",
    ("anchor", "s3_object_lock"): "write-once storage; prod needs the client's retention agreement",
    (
        "anchor",
        "azure_immutable_blob",
    ): "write-once storage; prod needs the client's retention agreement",
    (
        "anchor",
        "gcs_retention_lock",
    ): "write-once storage; prod needs the client's retention agreement",
    ("store", "postgres"): "the client's own database; the production store",
    ("audit", "chain"): "the tamper-evident audit trail; the production audit kind",
    ("llm", "anthropic"): "a real model that sends text out; a demo config needs made_up_data_only",
    ("llm", "bedrock"): "a real model that sends text out; a demo config needs made_up_data_only",
    (
        "llm",
        "openai_compat",
    ): "a real or self-hosted model that sends text out; a demo config needs made_up_data_only",
    ("llm", "gemini"): "a real model that sends text out; a demo config needs made_up_data_only",
    ("detector", "regex"): "a local check that sends no text out",
    (
        "detector",
        "llm_judge",
    ): "sends no text out itself; it calls the llm kind, so the model rules apply",
    (
        "detector",
        "bedrock_guardrail",
    ): "a vendor screening service that sends text out; a demo config needs made_up_data_only",
    (
        "channel",
        "slack",
    ): "the real approval channel; it sends text out; a demo config needs made_up_data_only",
}


def completeness_problems(table, demo_only, reviewed) -> list[str]:
    """Every pair of `table` is in exactly one of `demo_only` and `reviewed`; each reviewed entry has a reason."""
    pairs = {(cap, kind) for cap, kinds in table.items() for kind in kinds}
    out = [
        f"{c}/{k}: in neither DEMO_ONLY nor CLIENT_REVIEWED"
        for c, k in sorted(pairs - demo_only - set(reviewed))
    ]
    out += [
        f"{c}/{k}: in both DEMO_ONLY and CLIENT_REVIEWED"
        for c, k in sorted(demo_only & set(reviewed))
    ]
    out += [f"{c}/{k}: no reason" for (c, k), why in sorted(reviewed.items()) if not why.strip()]
    out += [f"{c}/{k}: not in TABLE" for c, k in sorted((demo_only | set(reviewed)) - pairs)]
    return out


def test_demo_only_is_exactly_the_six_pairs():
    assert DEMO_ONLY == {
        ("llm", "fake"),
        ("channel", "fake"),
        ("secrets", "fake"),
        ("secrets", "env"),
        ("store", "memory"),
        ("audit", "local_dir"),
    }


def test_every_pair_is_decided_with_a_reason():
    assert completeness_problems(TABLE, DEMO_ONLY, CLIENT_REVIEWED) == []


def test_the_facts_stated_in_the_reasons_are_true():
    """A reason that says `NOT_PROD`, "sends text out" or "sends no text out" is checked against the code, both
    ways: the claim must be true, and a pair the code treats that way must say so."""
    from hadavin_sdk.config import _sends_text_out

    def listed(cap: str, kind: str) -> bool:
        backends = SimpleNamespace(
            llm=SimpleNamespace(kind=kind if cap == "llm" else "fake"),
            channel=SimpleNamespace(kind=kind if cap == "channel" else "fake"),
            detector=[SimpleNamespace(kind=kind)] if cap == "detector" else [],
        )
        return f"{cap}: {kind}" in _sends_text_out(backends)

    for (cap, kind), why in CLIENT_REVIEWED.items():
        assert ("refused in prod by `NOT_PROD`" in why) == ((cap, kind) in NOT_PROD), (cap, kind)
        if cap in {"llm", "detector", "channel"}:
            says_out, says_none = "sends text out" in why, "sends no text out" in why
            assert says_out != says_none, f"{cap}/{kind}: must say one of the two"
            assert says_out == listed(cap, kind), (
                f"{cap}/{kind}: the reason disagrees with the code"
            )


def test_planted_kind_in_neither_set_is_reported():
    extra = {**TABLE, "llm": {**TABLE["llm"], "madeup": TABLE["llm"]["fake"]}}
    found = completeness_problems(extra, DEMO_ONLY, CLIENT_REVIEWED)
    assert any("llm/madeup" in p and "neither" in p for p in found)


def test_planted_pair_in_both_sets_is_reported():
    both = {**CLIENT_REVIEWED, ("llm", "fake"): "planted"}
    found = completeness_problems(TABLE, DEMO_ONLY, both)
    assert any("llm/fake" in p and "both" in p for p in found)


def test_planted_empty_reason_is_reported():
    empty = {**CLIENT_REVIEWED, ("llm", "gemini"): "  "}
    found = completeness_problems(TABLE, DEMO_ONLY, empty)
    assert any("llm/gemini" in p and "no reason" in p for p in found)


# --- build keywords in a client profile --------------------------------------------------------------------


@pytest.mark.parametrize(("keyword", "env"), list(product(REFUSED, ["pilot", "prod"])))
def test_each_test_double_is_refused_alone(tmp_path, made, keyword, env):
    root = _cfg_for(tmp_path, env)
    with pytest.raises(ConfigError, match="allow_test_doubles") as err:
        app_mod.build(root, ["ito-agent"], **{keyword: SAMPLES[keyword]})
    assert f"{keyword}=" in str(err.value)


def test_all_at_once_names_all_in_signature_order(tmp_path, made):
    root = pilot_cfg(tmp_path)
    with pytest.raises(ConfigError, match="allow_test_doubles") as err:
        app_mod.build(root, ["ito-agent"], **{k: SAMPLES[k] for k in REFUSED})
    assert ", ".join(f"{k}=" for k in REFUSED) in str(err.value)


def test_sources_keeps_its_own_refusal(tmp_path, made):
    root = pilot_cfg(tmp_path)
    with pytest.raises(ConfigError, match="configure Config.sources") as err:
        app_mod.build(root, ["ito-agent"], sources={"k8s": object()})
    assert "allow_test_doubles" not in str(err.value)


def test_tools_keeps_its_own_refusal(tmp_path, made):
    root = pilot_cfg(tmp_path)
    with pytest.raises(ConfigError, match="plain callables") as err:
        app_mod.build(root, ["ito-agent"], tools={"echo": lambda a: "x"})
    assert "allow_test_doubles" not in str(err.value)


def _door_problems(root: Path) -> list[str]:
    """A tripwire, not a proof: it reports a call with an `allow_test_doubles=` keyword (any function, so it covers
    `partial(build, allow_test_doubles=True)`) and a `**` expansion in a call whose function is named `build`. It
    misses every other way to reach the switch: `getattr(app, "build")(..., **opts)` or a `**` call through an
    alias (`b = build; b(**opts)`), a `partial` that gets the keyword from a `**` dict, and the switch passed
    positionally to a wrapper. It catches the plain copy-and-paste door only."""
    out = []
    for py in sorted(root.rglob("*.py")):
        for node in ast.walk(ast.parse(py.read_text(encoding="utf-8"), filename=str(py))):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            for kw in node.keywords:
                if kw.arg == "allow_test_doubles":
                    out.append(f"{py.name}:{node.lineno}: allow_test_doubles keyword")
                if kw.arg is None and name == "build":
                    out.append(f"{py.name}:{node.lineno}: build(**...)")
    return out


def test_no_door_in_src_or_demos():
    assert _door_problems(SRC) == []
    assert _door_problems(DEMOS) == []
    assert _door_problems(REPO / "tools") == []


@pytest.mark.parametrize(
    "code",
    [
        "from m import build\nbuild(None, [], allow_test_doubles=True)\n",
        "import functools\nfrom m import build\nf = functools.partial(build, allow_test_doubles=True)\n",
        "from m import build\nopts = {}\nbuild(None, [], **opts)\n",
    ],
    ids=["direct", "partial", "double_star"],
)
def test_planted_doors_are_reported(tmp_path, code):
    (tmp_path / "planted.py").write_text(code, encoding="utf-8")
    assert len(_door_problems(tmp_path)) == 1


def test_the_refusal_text_is_true_for_every_value_that_reaches_it(tmp_path, made, monkeypatch):
    """The refusal fires for every environment value that is not `demo` (`uat`, an empty value, `Demo` included), so
    its text must say that and not name only the two real stages."""
    copied = load_config(pilot_cfg(tmp_path)).model_copy(update={"environment": "uat"})
    monkeypatch.setattr(app_mod, "load_config", lambda _dir: copied)
    with pytest.raises(ConfigError, match="allow_test_doubles") as err:
        app_mod.build(tmp_path, ["ito-agent"], llm=ScriptedLLM())
    assert "every environment other than demo" in str(err.value)
    assert "in pilot and prod pass" not in str(err.value)


def test_the_build_params_snapshot_is_the_signature_of_build():
    """`_BUILD_PARAMS` is read once, at import, from `build`; it must be `build`'s own signature (a signature of
    another function would make the check judge the wrong keywords, and nothing else would notice)."""
    assert list(app_mod._BUILD_PARAMS) == list(inspect.signature(app_mod.build).parameters)
    assert dict(app_mod._BUILD_PARAMS) == dict(inspect.signature(app_mod.build).parameters)


@pytest.mark.parametrize("switch", [False, True], ids=["no_switch", "switch_true"])
def test_demo_ignores_the_switch_and_the_doubles(tmp_path, made, caplog, switch):
    """In `demo` the check does not run: every test double passes with or without the switch, and no warning line is
    written (the switch changes nothing there)."""
    root = pilot_cfg(tmp_path, env="demo")
    _edit(root, lambda d: d.update(made_up_data_only=True))
    doubles = {k: SAMPLES[k] for k in REFUSED}
    with caplog.at_level("WARNING", logger="hadavin_sdk.app"), pytest.raises(_Reached):
        app_mod.build(root, ["ito-agent"], allow_test_doubles=switch, **doubles)
    assert made  # the build went on past the check and reached the first backend it makes
    assert [r for r in caplog.records if r.name == "hadavin_sdk.app"] == []


def test_a_falsy_double_is_refused(tmp_path, made):
    root = pilot_cfg(tmp_path)
    with pytest.raises(ConfigError, match="allow_test_doubles") as err:
        app_mod.build(root, ["ito-agent"], channel=_FalsyChannel())
    assert "channel=" in str(err.value)


def test_a_refusal_builds_nothing_first(tmp_path, made):
    root = pilot_cfg(tmp_path)
    with pytest.raises(ConfigError, match="allow_test_doubles"):
        app_mod.build(root, ["ito-agent"], llm=ScriptedLLM())
    assert made == []


def test_a_keyword_added_later_is_refused_by_default():
    helper = app_mod._test_doubles_given

    def stub(*, secrets=None, extra=None, allow_test_doubles=False, sources=None):
        return None

    params = inspect.signature(stub).parameters
    assert helper(params, {"extra": 1}) == ["extra"]
    assert helper(params, {"secrets": None, "extra": None}) == []


@pytest.mark.parametrize("environment", ["Demo", "uat", ""])
def test_any_environment_that_is_not_demo_is_live(tmp_path, made, monkeypatch, environment):
    """An environment value that is not a stage is live: the switch is needed there too. `Config.environment` is a
    Literal, so such a value never comes out of `load_config`; `model_copy` builds it. Defence in depth for a hand-built
    Config, not a reachable load (only this synthetic state reaches that branch)."""
    copied = load_config(pilot_cfg(tmp_path)).model_copy(update={"environment": environment})
    monkeypatch.setattr(app_mod, "load_config", lambda _dir: copied)
    with pytest.raises(ConfigError, match="allow_test_doubles") as err:
        app_mod.build(tmp_path, ["ito-agent"], llm=ScriptedLLM())
    assert "llm=" in str(err.value)
    assert made == []


@pytest.mark.parametrize("switch", ["no", "yes", 1, [True]], ids=["no", "yes", "one", "list"])
def test_only_the_value_true_is_the_switch(tmp_path, made, switch):
    root = pilot_cfg(tmp_path)
    with pytest.raises(ConfigError, match="allow_test_doubles") as err:
        app_mod.build(root, ["ito-agent"], llm=ScriptedLLM(), allow_test_doubles=switch)
    assert "llm=" in str(err.value)


@pytest.mark.parametrize("env", ["pilot", "prod"])
def test_no_override_passes_the_check(tmp_path, made, env):
    root = _cfg_for(tmp_path, env)
    with pytest.raises(_Reached):
        app_mod.build(root, ["ito-agent"])
    assert made[0] == "secrets"


def test_the_switch_lets_a_test_double_through(tmp_path, made):
    root = pilot_cfg(tmp_path)
    with pytest.raises(_Reached):
        app_mod.build(root, ["ito-agent"], llm=ScriptedLLM(), allow_test_doubles=True)
    assert "secrets" in made


def test_the_switch_leaves_a_log_line_naming_the_keywords(tmp_path, made, caplog):
    root = pilot_cfg(tmp_path)
    with caplog.at_level("WARNING", logger="hadavin_sdk.app"), pytest.raises(_Reached):
        app_mod.build(
            root, ["ito-agent"], llm=ScriptedLLM(), channel=FakeChannel(), allow_test_doubles=True
        )
    lines = [r.getMessage() for r in caplog.records if r.name == "hadavin_sdk.app"]
    assert len(lines) == 1
    assert "allow_test_doubles=True" in lines[0] and "pilot" in lines[0]
    assert lines[0].endswith("channel, llm")


def test_the_switch_with_no_test_double_leaves_no_log_line(tmp_path, made, caplog):
    root = pilot_cfg(tmp_path)
    with caplog.at_level("WARNING", logger="hadavin_sdk.app"), pytest.raises(_Reached):
        app_mod.build(root, ["ito-agent"], allow_test_doubles=True)
    assert [r for r in caplog.records if r.name == "hadavin_sdk.app"] == []


def test_the_keyword_snapshot_is_the_first_statement_of_build():
    """`given = dict(locals())` sees the keyword values only while no name has been rebound, so it must come first."""
    fn = ast.parse(inspect.getsource(app_mod.build).lstrip()).body[0]
    body = [
        s
        for s in fn.body
        if not (
            isinstance(s, ast.Expr)
            and isinstance(s.value, ast.Constant)
            and isinstance(s.value.value, str)
        )
    ]
    first = body[0]
    assert isinstance(first, ast.Assign)
    assert [t.id for t in first.targets] == ["given"]
    assert ast.unparse(first.value) == "dict(locals())"


@pytest.mark.parametrize(
    "hook", [{"hold_run_ids": lambda: set()}, {"timeout_s": 1.0}], ids=["hold_run_ids", "timeout_s"]
)
def test_the_live_hooks_need_no_switch(tmp_path, made, hook):
    root = pilot_cfg(tmp_path)
    with pytest.raises(_Reached):
        app_mod.build(root, ["ito-agent"], **hook)


def test_the_live_hooks_are_exactly_two_parameters_of_build():
    hooks = app_mod._LIVE_HOOKS
    assert set(hooks) == {"hold_run_ids", "timeout_s"}
    assert set(hooks) <= set(inspect.signature(app_mod.build).parameters)


def test_every_refused_keyword_has_a_sample():
    assert set(REFUSED) <= set(SAMPLES), (
        f"build keywords with no sample: {sorted(set(REFUSED) - set(SAMPLES))}"
    )


# --- a demo config that sends text out must say it holds only made-up data --------------------------------

LLM_SETTINGS = {
    "anthropic": {"platform": "api", "api_key_secret_name": "madeup-llm-key"},
    "bedrock": {"region": "madeup-region-1"},
    "openai_compat": {"base_url": "https://llm.example/v1"},
    "gemini": {"api_key_secret_name": "madeup-llm-key"},
}
GUARDRAIL = {
    "kind": "bedrock_guardrail",
    "guardrail_id": "madeup-guardrail",
    "guardrail_version": "1",
    "region": "madeup-region-1",
}
SLACK = {
    "kind": "slack",
    "channel_id": "C0MADEUP",
    "signing_secret_name": "madeup-sign",
    "bot_token_secret_name": "madeup-token",
}
REAL_LLM_KINDS = sorted(k for k in TABLE["llm"] if ("llm", k) not in DEMO_ONLY)
REAL_CHANNEL_KINDS = sorted(k for k in TABLE["channel"] if ("channel", k) not in DEMO_ONLY)


@pytest.mark.parametrize("kind", REAL_LLM_KINDS)
def test_a_real_llm_kind_in_demo_needs_the_field(cfg_dir, kind):
    _edit(cfg_dir, lambda d: d["backends"].update(llm={"kind": kind, **LLM_SETTINGS[kind]}))
    with pytest.raises(ConfigError, match="made_up_data_only") as err:
        load_config(cfg_dir)
    assert f"llm: {kind}" in str(err.value)


COMMANDS = {
    "gate": ["gate", "madeup-agent"],
    "replay": [
        *("replay", "madeup-agent", "--bundles", "b", "--cause-list", "c"),
        *("--max-usd", "1", "--out", "o"),
    ],
    "score": [
        *("score", "--outputs", "o", "--answers", "a", "--cause-list", "c", "--bundles", "b"),
    ],
}


@pytest.mark.parametrize("command", COMMANDS)
def test_the_command_line_refuses_a_demo_config_that_sends_text_out(cfg_dir, command, capsys):
    """`gate`, `replay` and `score` read the same config, so a demo config naming a real model is refused for each."""
    from hadavin_sdk import cli

    _edit(
        cfg_dir,
        lambda d: d["backends"].update(llm={"kind": "anthropic", **LLM_SETTINGS["anthropic"]}),
    )
    code = cli.main(["--config", str(cfg_dir), *COMMANDS[command]])
    err = capsys.readouterr().err
    assert code == 2 and "made_up_data_only" in err, err


def test_the_vendor_detector_in_demo_needs_the_field(cfg_dir):
    _edit(cfg_dir, lambda d: d["backends"].update(detector=[GUARDRAIL]))
    with pytest.raises(ConfigError, match="made_up_data_only") as err:
        load_config(cfg_dir)
    assert "detector: bedrock_guardrail" in str(err.value)


def test_every_detector_kind_is_local_or_refused_in_demo():
    from hadavin_sdk.backends.table import LOCAL_DETECTORS
    from hadavin_sdk.config import _sends_text_out

    for kind in sorted(TABLE["detector"]):
        backends = SimpleNamespace(
            llm=SimpleNamespace(kind="fake"),
            channel=SimpleNamespace(kind="fake"),
            detector=[SimpleNamespace(kind=kind)],
        )
        listed = f"detector: {kind}" in _sends_text_out(backends)
        assert listed is (kind not in LOCAL_DETECTORS), kind
    assert LOCAL_DETECTORS <= set(TABLE["detector"])


def test_a_detector_kind_nobody_reviewed_is_treated_as_sending_text_out():
    from hadavin_sdk.config import _sends_text_out

    backends = SimpleNamespace(
        llm=SimpleNamespace(kind="fake"),
        channel=SimpleNamespace(kind="fake"),
        detector=[SimpleNamespace(kind="madeup_vendor")],
    )
    assert _sends_text_out(backends) == ["detector: madeup_vendor"]


def test_the_local_detector_list_is_exactly_regex_and_llm_judge():
    """The allow-list of detectors that send no text out is a reviewed decision: a kind joins it only by a change
    that names it here too."""
    from hadavin_sdk.backends.table import LOCAL_DETECTORS

    assert LOCAL_DETECTORS == {"regex", "llm_judge"}


def test_a_real_channel_kind_in_demo_needs_the_field(cfg_dir):
    assert REAL_CHANNEL_KINDS == ["slack"]
    _edit(cfg_dir, lambda d: d["backends"].update(channel=SLACK))
    with pytest.raises(ConfigError, match="made_up_data_only") as err:
        load_config(cfg_dir)
    assert "channel: slack" in str(err.value)


def test_with_the_field_a_real_llm_kind_loads_in_demo(cfg_dir):
    def both(d):
        d["made_up_data_only"] = True
        d["backends"]["llm"] = {"kind": "openai_compat", **LLM_SETTINGS["openai_compat"]}

    _edit(cfg_dir, both)
    assert load_config(cfg_dir).backends.llm.kind == "openai_compat"


def test_three_refusals_come_in_one_error(cfg_dir):
    def many(d):
        d["backends"]["llm"] = {"kind": "openai_compat", **LLM_SETTINGS["openai_compat"]}
        d["backends"]["detector"] = [GUARDRAIL]
        d["backends"]["audit"] = {"kind": "chain"}
        d["backends"]["anchor"] = ANCHOR | {"mode": "COMPLIANCE"}

    _edit(cfg_dir, many)
    with pytest.raises(ConfigError, match="made_up_data_only") as err:
        load_config(cfg_dir)
    text = str(err.value)
    assert "llm: openai_compat" in text
    assert "detector: bedrock_guardrail" in text
    assert "COMPLIANCE" in text


def test_the_field_is_refused_in_pilot_and_prod(tmp_path):
    for env in ("pilot", "prod"):
        root = _cfg_for(tmp_path / env, env)
        _edit(root, lambda d: d.update(made_up_data_only=True))
        with pytest.raises(ConfigError, match="made_up_data_only") as err:
            load_config(root)
        assert "demo configs only" in str(err.value)


@pytest.mark.parametrize("environment", ["Demo", "uat", ""])
def test_the_field_is_refused_in_any_environment_that_is_not_demo(tmp_path, environment):
    """A copied config whose environment is not a stage is live, so it may not say it holds made-up data. Such a value
    never comes out of `load_config` (Literal); `model_copy` builds it. Defence in depth, not a reachable load: only
    this synthetic state tells a rule that names pilot and prod apart from one that names every non-demo value."""
    copied = load_config(pilot_cfg(tmp_path)).model_copy(
        update={"environment": environment, "made_up_data_only": True}
    )
    with pytest.raises(ValueError, match="made_up_data_only"):
        copied._cross_checks()


def test_the_field_still_loads_in_demo(cfg_dir):
    _edit(cfg_dir, lambda d: d.update(made_up_data_only=True))
    assert load_config(cfg_dir).made_up_data_only is True


@pytest.mark.parametrize("value", ["yes", 1, "true", "on"])
def test_a_loose_yes_does_not_switch_the_field_on(cfg_dir, value):
    """The field is a strict bool: "yes", 1, "true" and "on" are refused, so a safety switch cannot turn on from
    loose input. A plain bool would let these through."""
    _edit(cfg_dir, lambda d: d.update(made_up_data_only=value))
    with pytest.raises(ConfigError, match="made_up_data_only") as err:
        load_config(cfg_dir)
    assert "valid boolean" in str(err.value)


@pytest.mark.parametrize("value", ["maybe", None, [True]], ids=["word", "null", "list"])
def test_a_value_that_is_not_a_bool_is_refused_at_load(cfg_dir, value):
    """A null or a list is not a yes: the config does not load (the field is not optional)."""
    _edit(cfg_dir, lambda d: d.update(made_up_data_only=value))
    with pytest.raises(ConfigError, match="made_up_data_only") as err:
        load_config(cfg_dir)
    assert "valid boolean" in str(
        err.value
    )  # a type error, not "extra input" (which the base already says)


def test_an_unquoted_yes_in_the_file_is_the_yaml_true(cfg_dir):
    """Pins today's behaviour so a change is seen: the file is read as YAML 1.1, where an unquoted `yes` is the
    boolean true (the quoted string "yes" is refused, see the loose-yes row). So `made_up_data_only: yes` in the
    file switches the field on, the same as `true`; it is the operator's own word either way."""
    path = cfg_dir / "config.yaml"
    path.write_text(
        path.read_text(encoding="utf-8") + "\nmade_up_data_only: yes\n", encoding="utf-8"
    )
    assert load_config(cfg_dir).made_up_data_only is True


# --- the mutant runner keeps cloud settings away from the tests --------------------------------------------


def _runner():
    spec = importlib.util.spec_from_file_location(
        "client_profile_mutants", REPO / "tools" / "client_profile_mutants.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize(
    "name",
    [
        "AWS_ACCESS_KEY_ID",
        "azure_client_id",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "ANTHROPIC_BASE_URL",
        "ARM_CLIENT_ID",  # Terraform azurerm provider
        "MSI_ENDPOINT",  # Azure App Service managed identity, older names
        "IDENTITY_ENDPOINT",  # Azure App Service and Functions managed identity
        "BOTO_CONFIG",
        "GCLOUD_PROJECT",
        "OCI_CLI_PROFILE",
        "VAULT_TOKEN",
        "SLACK_BOT_TOKEN",
        "CLOUDFLARE_API_TOKEN",
        "PGPASSWORD",
        "DATABASE_URL",
        "KUBECONFIG",
    ],
)
def test_the_mutant_runner_refuses_to_start_with_a_cloud_setting(monkeypatch, capsys, name):
    runner = _runner()
    for other in runner.cloud_variables():  # the test setup may already hold some
        monkeypatch.delenv(other)
    monkeypatch.setenv(name, "made-up")
    assert runner.cloud_variables() == [name]
    assert runner.main() == 3
    out = capsys.readouterr().out
    assert name in out and "made-up" not in out


def test_the_mutant_runner_gives_the_tests_only_plain_variables(monkeypatch):
    runner = _runner()
    for name in ["AWS_SECRET_ACCESS_KEY", "HTTPS_PROXY", "HADAVIN_TEST_PG_DSN", "PATH"]:
        monkeypatch.setenv(name, "made-up")
    env = runner.clean_env(PYTHONPATH="/x")
    assert set(env) <= {
        *runner.PLAIN_ENV,
        "HOME",
        "USERPROFILE",
        "PYTHONPATH",
        "PYTHONDONTWRITEBYTECODE",
    }
    assert env["PATH"] == "made-up" and env["PYTHONPATH"] == "/x"


def test_the_mutant_runner_gives_the_tests_an_empty_home(monkeypatch, tmp_path):
    """The cloud SDKs read credential files under HOME (~/.aws, ~/.azure, ~/.config/gcloud)."""
    runner = _runner()
    (tmp_path / ".aws").mkdir()
    (tmp_path / ".aws" / "credentials").write_text("made up\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))  # Windows reads this one and ignores HOME
    env = runner.clean_env()
    home = Path(env["HOME"])
    assert home != tmp_path and home.is_dir()
    assert env["USERPROFILE"] == env["HOME"]
    assert list(home.iterdir()) == []


def _row(killer: str) -> tuple:
    """A mutant row as the runner holds it: (number, description, file, mutation, tests, killer)."""
    number, description, path, mutation, tests = 1, "made up", "path", None, []
    return (number, description, path, mutation, tests, killer)


def test_a_killer_must_name_its_file_and_end_at_the_test_name():
    """A killer is matched against a failing test's id: a bare `::test_x` would also match `a.py::test_x_and_more`
    and `other.py::test_x`, and a second branch (`|`) would match anything."""
    runner = _runner()
    bad = [
        "::test_x$",  # no file
        "tests/a.py::test_x",  # no end
        "tests/a.py::test_x.*",
        "tests/a.py::test_x$|tests/b.py::test_y$",  # a second branch
        "tests/a.py::test_x\\[a|b",  # a second branch in the parameter part
        "test_x$",
    ]
    for killer in bad:
        assert runner.killer_problems([_row(killer)]), killer
    good = [
        "",
        "tests/a.py::test_x$",
        "tests/a.py::test_x\\[",
        "tests/a.py::test_x\\[(a|b)-",  # a branch inside a group is fine
        "tests/a.py::test_x\\[a-b\\]",
    ]
    for killer in good:
        assert runner.killer_problems([_row(killer)]) == [], killer
    assert runner.killer_problems() == []  # every killer of this tool


def test_the_mutant_runner_refuses_to_start_with_an_unanchored_killer(monkeypatch, capsys):
    runner = _runner()
    monkeypatch.setattr(runner, "DEF", [*runner.DEF, _row("::test_x")])

    def started(*_a):
        raise AssertionError("the runner went on to make its copy")

    monkeypatch.setattr(runner, "_git_in", started)
    assert runner.main() == 3
    assert "not anchored" in capsys.readouterr().out


@pytest.mark.parametrize("status", ["KILLED-OTHER", "SURVIVED", "ERROR", "NOT-LOCATED", "TIMEOUT"])
def test_only_a_kill_by_the_named_test_makes_the_run_pass(status):
    """The docstring of the tool: a mutant killed only by some other test is a failure, not a kill."""
    runner = _runner()
    clean = (1, "made up", "yes", "cp::test_x", "KILLED-NAMED", "")
    assert runner.verdict([clean])[0] is True
    assert runner.verdict([clean, (2, "made up", "yes", "cp::test_y", "KILLED", "")])[0] is True
    ok, not_clean = runner.verdict([clean, (2, "made up", "yes", "cp::test_y", status, "")])
    assert ok is False and [r[0] for r in not_clean] == [2]
    assert runner.verdict([])[0] is False


def test_a_run_of_only_some_mutants_is_never_a_pass():
    """MUTANT_ONLY picks mutants: even when every picked one is killed, the run did not cover the list."""
    runner = _runner()
    clean = (1, "made up", "yes", "cp::test_x", "KILLED-NAMED", "")
    assert runner.verdict([clean], expected=1)[0] is True
    assert runner.verdict([clean], expected=2)[0] is False


def test_the_mutant_numbers_are_one_to_n_without_gaps_or_repeats():
    numbers = [row[0] for row in _runner().DEF]
    assert numbers == list(range(1, len(numbers) + 1))


def test_two_same_size_mutants_in_one_second_do_not_run_each_others_code(tmp_path):
    """Python reuses a compiled file when the source has the same size and the same modification second. The runner
    plants every mutant into one copy, so it must leave no compiled files behind."""
    runner = _runner()
    mod = tmp_path / "planted.py"
    seen = []
    for value in ("1", "2"):  # same size, same modification time on purpose
        mod.write_text(f"VALUE = {value}\n", encoding="utf-8")
        os.utime(mod, (1_700_000_000, 1_700_000_000))
        run = runner._sh(
            [sys.executable, "-c", "import planted; print(planted.VALUE)"],
            timeout=60,
            cwd=tmp_path,
            env=runner.clean_env(PYTHONPATH=str(tmp_path)),
        )
        seen.append(run.stdout.strip())
    assert seen == ["1", "2"]
    assert list(tmp_path.rglob("*.pyc")) == []
