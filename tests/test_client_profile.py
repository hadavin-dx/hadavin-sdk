"""P6a-1: the client-profile check (ticket P6a, revision 3 plus build notes BN-1 to BN-15).

T0 the prod fixture loads; T1 demo-only kinds not covered elsewhere; T2 every TABLE pair is decided; T5 the build
keywords in a client profile (pilot or prod); T7 a demo config that names a real model, a vendor detector or a
real approval channel must say it holds only made-up data.

Import rule (ticket R2-ADV-1): module-level names exist on the base. Names that exist only after P6a-1
(`_test_doubles_given`, `_LIVE_HOOKS`, the keyword `allow_test_doubles`, the config key `made_up_data_only`) are
read inside row bodies, so on the base each row fails alone.
"""

from __future__ import annotations

import ast
import inspect
from itertools import product
from pathlib import Path

import pytest
import yaml

from hadavin_sdk import app as app_mod
from hadavin_sdk.approvals.channel import FakeChannel
from hadavin_sdk.backends.table import DEMO_ONLY, TABLE
from hadavin_sdk.config import ConfigError, load_config
from tests.test_k3_pilot import ScriptedLLM
from tests.test_k3_pilot_env import pilot_cfg

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src" / "hadavin_sdk"
DEMOS = REPO / "demos"


# --- shared helpers ----------------------------------------------------------------------------------------


def _edit(cfg_dir: Path, fn) -> None:
    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    fn(data)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def prod_cfg(tmp_path: Path) -> Path:
    """`pilot_cfg` as prod: a signer whose key comes from the secrets kind, and an anchor whose retention is agreed."""
    root = pilot_cfg(tmp_path, env="prod")

    def prod(d):
        d["backends"]["signer"] = {
            "kind": "ed25519_local",
            "private_key_secret_name": "audit-key",
        }
        d["backends"]["anchor"] = {
            "kind": "s3_object_lock",
            "bucket": "madeup-bucket",
            "region": "madeup-region-1",
            "retention_ack": True,
        }

    _edit(root, prod)
    return root


def _cfg_for(tmp_path: Path, env: str) -> Path:
    return prod_cfg(tmp_path) if env == "prod" else pilot_cfg(tmp_path, env=env)


class _Reached(Exception):
    """Raised by the patched `make` for every capability but secrets: the check let the build through."""


class _MadeSecrets:
    """A made-up provider: answers every secret name with a made-up value built from parts."""

    def get(self, name: str) -> str:
        return "made" + "-up-" + name


class _FalsyChannel:
    def __len__(self) -> int:
        return 0


class _StubDetector:
    backend = "regex"

    def check(self, text, source):  # pragma: no cover - never called
        raise AssertionError


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


# One value per refused build keyword, not equal to its default. A new keyword with no sample fails collection.
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
assert set(REFUSED) <= set(SAMPLES), (
    f"build keywords with no sample: {sorted(set(REFUSED) - set(SAMPLES))}"
)


# --- T0 ----------------------------------------------------------------------------------------------------


def test_t0_the_prod_fixture_loads(tmp_path):
    assert load_config(prod_cfg(tmp_path)).environment == "prod"


# --- T1 ----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("env", ["pilot", "prod"])
def test_t1a_secrets_env_is_refused_in_a_client_profile(tmp_path, env):
    root = _cfg_for(tmp_path, env)
    _edit(root, lambda d: d["backends"].update(secrets={"kind": "env"}))
    with pytest.raises(ConfigError, match=f"environment {env}: refused") as err:
        load_config(root)
    assert "secrets: env" in str(err.value)


def test_t1d_a_pilot_config_that_omits_store_is_refused(tmp_path):
    root = pilot_cfg(tmp_path)
    _edit(root, lambda d: d["backends"].pop("store"))
    with pytest.raises(ConfigError, match="environment pilot: refused") as err:
        load_config(root)
    assert "store: memory" in str(err.value)


# --- T2: every TABLE pair is decided -----------------------------------------------------------------------

CLIENT_REVIEWED: dict[tuple[str, str], str] = {
    ("secrets", "aws_secrets_manager"): "a managed secret store the client runs; no test double",
    ("secrets", "vault"): "a self-hostable secret store; the client runs it",
    ("secrets", "azure_key_vault"): "a managed secret store the client runs; no test double",
    ("secrets", "gcp_secret_manager"): "a managed secret store the client runs; no test double",
    (
        "secrets",
        "mounted_file",
    ): "secrets mounted as files by the platform; read-only by the process",
    ("signer", "none"): "allowed in pilot, refused in prod by `NOT_PROD`",
    ("signer", "ed25519_local"): "a local key from the secrets kind; prod refuses a key file",
    ("signer", "aws_kms"): "a managed key service; signs digests only",
    ("signer", "azure_key_vault_key"): "a managed key service; signs digests only",
    ("signer", "gcp_kms"): "a managed key service; signs digests only",
    ("signer", "vault_transit"): "a self-hostable signing service; signs digests only",
    ("anchor", "none"): "allowed in pilot, refused in prod by `NOT_PROD`",
    ("anchor", "s3_object_lock"): "write-once storage the client agreed retention for",
    ("anchor", "azure_immutable_blob"): "write-once storage the client agreed retention for",
    ("anchor", "gcs_retention_lock"): "write-once storage the client agreed retention for",
    ("store", "postgres"): "the client's own database; the production store",
    ("audit", "chain"): "the tamper-evident audit trail; the production audit kind",
    ("llm", "anthropic"): "a real model; masked text only (P5c); a pilot or prod config names it",
    ("llm", "bedrock"): "a real model; masked text only (P5c); a pilot or prod config names it",
    ("llm", "openai_compat"): "a real or self-hosted model; masked text only (P5c)",
    ("llm", "gemini"): "a real model; masked text only (P5c); a pilot or prod config names it",
    ("detector", "regex"): "a local check; sends nothing out",
    ("detector", "llm_judge"): "uses the llm kind, so the model rules apply",
    ("detector", "bedrock_guardrail"): "a vendor screening service; demo needs made_up_data_only",
    ("channel", "slack"): "the real approval channel; demo needs made_up_data_only",
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


def test_t2a_demo_only_is_exactly_the_six_pairs():
    assert DEMO_ONLY == {
        ("llm", "fake"),
        ("channel", "fake"),
        ("secrets", "fake"),
        ("secrets", "env"),
        ("store", "memory"),
        ("audit", "local_dir"),
    }


def test_t2b_every_pair_is_decided_with_a_reason():
    assert completeness_problems(TABLE, DEMO_ONLY, CLIENT_REVIEWED) == []


def test_t2c_planted_kind_in_neither_set_is_reported():
    extra = {**TABLE, "llm": {**TABLE["llm"], "madeup": TABLE["llm"]["fake"]}}
    found = completeness_problems(extra, DEMO_ONLY, CLIENT_REVIEWED)
    assert any("llm/madeup" in p and "neither" in p for p in found)


def test_t2c_planted_pair_in_both_sets_is_reported():
    both = {**CLIENT_REVIEWED, ("llm", "fake"): "planted"}
    found = completeness_problems(TABLE, DEMO_ONLY, both)
    assert any("llm/fake" in p and "both" in p for p in found)


def test_t2c_planted_empty_reason_is_reported():
    empty = {**CLIENT_REVIEWED, ("llm", "gemini"): "  "}
    found = completeness_problems(TABLE, DEMO_ONLY, empty)
    assert any("llm/gemini" in p and "no reason" in p for p in found)


# --- T5: build keywords in a client profile ----------------------------------------------------------------


@pytest.mark.parametrize(("keyword", "env"), list(product(REFUSED, ["pilot", "prod"])))
def test_t5b_each_test_double_is_refused_alone(tmp_path, made, keyword, env):
    root = _cfg_for(tmp_path, env)
    with pytest.raises(ConfigError, match="allow_test_doubles") as err:
        app_mod.build(root, ["ito-agent"], **{keyword: SAMPLES[keyword]})
    assert f"{keyword}=" in str(err.value)


def test_t5c_all_at_once_names_all_in_signature_order(tmp_path, made):
    root = pilot_cfg(tmp_path)
    with pytest.raises(ConfigError, match="allow_test_doubles") as err:
        app_mod.build(root, ["ito-agent"], **{k: SAMPLES[k] for k in REFUSED})
    assert ", ".join(f"{k}=" for k in REFUSED) in str(err.value)


def test_t5f_sources_keeps_its_own_refusal(tmp_path, made):
    root = pilot_cfg(tmp_path)
    with pytest.raises(ConfigError, match="configure Config.sources") as err:
        app_mod.build(root, ["ito-agent"], sources={"k8s": object()})
    assert "allow_test_doubles" not in str(err.value)


def test_t5h_tools_keeps_its_own_refusal(tmp_path, made):
    root = pilot_cfg(tmp_path)
    with pytest.raises(ConfigError, match="plain callables") as err:
        app_mod.build(root, ["ito-agent"], tools={"echo": lambda a: "x"})
    assert "allow_test_doubles" not in str(err.value)


def _door_problems(root: Path) -> list[str]:
    """Calls that pass `allow_test_doubles` in any way: a keyword in any call (covers `partial(build, ...)`), or a
    `**` expansion in a call whose function is named `build`."""
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


def test_t5g_no_door_in_src_or_demos():
    assert _door_problems(SRC) == []
    assert _door_problems(DEMOS) == []


@pytest.mark.parametrize(
    "code",
    [
        "from m import build\nbuild(None, [], allow_test_doubles=True)\n",
        "import functools\nfrom m import build\nf = functools.partial(build, allow_test_doubles=True)\n",
        "from m import build\nopts = {}\nbuild(None, [], **opts)\n",
    ],
    ids=["direct", "partial", "double_star"],
)
def test_t5g_planted_doors_are_reported(tmp_path, code):
    (tmp_path / "planted.py").write_text(code, encoding="utf-8")
    assert len(_door_problems(tmp_path)) == 1


def test_t5i_a_falsy_double_is_refused(tmp_path, made):
    root = pilot_cfg(tmp_path)
    with pytest.raises(ConfigError, match="allow_test_doubles") as err:
        app_mod.build(root, ["ito-agent"], channel=_FalsyChannel())
    assert "channel=" in str(err.value)


def test_t5j_a_refusal_builds_nothing_first(tmp_path, made):
    root = pilot_cfg(tmp_path)
    with pytest.raises(ConfigError, match="allow_test_doubles"):
        app_mod.build(root, ["ito-agent"], llm=ScriptedLLM())
    assert made == []


def test_t5l_a_keyword_added_later_is_refused_by_default():
    helper = app_mod._test_doubles_given

    def stub(*, secrets=None, extra=None, allow_test_doubles=False, sources=None):
        return None

    params = inspect.signature(stub).parameters
    assert helper(params, {"extra": 1}) == ["extra"]
    assert helper(params, {"secrets": None, "extra": None}) == []


@pytest.mark.parametrize("env", ["pilot", "prod"])
def test_t5m_no_override_passes_the_check(tmp_path, made, env):
    root = _cfg_for(tmp_path, env)
    with pytest.raises(_Reached):
        app_mod.build(root, ["ito-agent"])
    assert made[0] == "secrets"


def test_t5n_the_switch_lets_a_test_double_through(tmp_path, made):
    root = pilot_cfg(tmp_path)
    with pytest.raises(_Reached):
        app_mod.build(root, ["ito-agent"], llm=ScriptedLLM(), allow_test_doubles=True)
    assert "secrets" in made


@pytest.mark.parametrize(
    "hook", [{"hold_run_ids": lambda: set()}, {"timeout_s": 1.0}], ids=["hold_run_ids", "timeout_s"]
)
def test_t5o_the_live_hooks_need_no_switch(tmp_path, made, hook):
    root = pilot_cfg(tmp_path)
    with pytest.raises(_Reached):
        app_mod.build(root, ["ito-agent"], **hook)


def test_t5p_the_live_hooks_are_exactly_two_parameters_of_build():
    hooks = app_mod._LIVE_HOOKS
    assert set(hooks) == {"hold_run_ids", "timeout_s"}
    assert set(hooks) <= set(inspect.signature(app_mod.build).parameters)


# --- T7: a demo config that sends text out must say it holds only made-up data -------------------------------

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
def test_t7a_a_real_llm_kind_in_demo_needs_the_field(cfg_dir, kind):
    _edit(cfg_dir, lambda d: d["backends"].update(llm={"kind": kind, **LLM_SETTINGS[kind]}))
    with pytest.raises(ConfigError, match="made_up_data_only") as err:
        load_config(cfg_dir)
    assert f"llm: {kind}" in str(err.value)


def test_t7a2_the_vendor_detector_in_demo_needs_the_field(cfg_dir):
    _edit(cfg_dir, lambda d: d["backends"].update(detector=[GUARDRAIL]))
    with pytest.raises(ConfigError, match="made_up_data_only") as err:
        load_config(cfg_dir)
    assert "detector: bedrock_guardrail" in str(err.value)


def test_t7a3_a_real_channel_kind_in_demo_needs_the_field(cfg_dir):
    assert REAL_CHANNEL_KINDS == ["slack"]
    _edit(cfg_dir, lambda d: d["backends"].update(channel=SLACK))
    with pytest.raises(ConfigError, match="made_up_data_only") as err:
        load_config(cfg_dir)
    assert "channel: slack" in str(err.value)


def test_t7b_with_the_field_a_real_llm_kind_loads_in_demo(cfg_dir):
    def both(d):
        d["made_up_data_only"] = True
        d["backends"]["llm"] = {"kind": "openai_compat", **LLM_SETTINGS["openai_compat"]}

    _edit(cfg_dir, both)
    assert load_config(cfg_dir).backends.llm.kind == "openai_compat"


def test_t7d_three_refusals_come_in_one_error(cfg_dir):
    def many(d):
        d["backends"]["llm"] = {"kind": "openai_compat", **LLM_SETTINGS["openai_compat"]}
        d["backends"]["detector"] = [GUARDRAIL]
        d["backends"]["audit"] = {"kind": "chain"}
        d["backends"]["anchor"] = {
            "kind": "s3_object_lock",
            "bucket": "madeup-bucket",
            "region": "madeup-region-1",
            "mode": "COMPLIANCE",
        }

    _edit(cfg_dir, many)
    with pytest.raises(ConfigError, match="made_up_data_only") as err:
        load_config(cfg_dir)
    text = str(err.value)
    assert "llm: openai_compat" in text
    assert "detector: bedrock_guardrail" in text
    assert "COMPLIANCE" in text
