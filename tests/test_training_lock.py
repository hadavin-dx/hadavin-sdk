"""P6b1: the no-training statement check inside the llm kind.

No code can see what a provider does with our text. These tests pin a RECORD of an operator's promise: a pilot or
prod config with a real model backend needs a dated, well formed statement for the servers it talks to. The check
does not stop a provider from training, and nothing here proves a statement is true.

Every import of a name that does not exist on the base tree is INSIDE the test function, so this file collects
there and the fail-before run shows assertions, not an import error. No network, no Postgres, no real keys.
"""

from __future__ import annotations

import datetime as dt
import itertools
import re
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

import hadavin_sdk.config as config_mod
from hadavin_sdk.backends.table import DEV_ONLY, TABLE
from hadavin_sdk.config import ConfigError, load_config
from tests.test_k3_pilot_env import pilot_cfg

_COUNTER = itertools.count()
FIXED_TODAY = dt.date(2027, 3, 1)
GOOD_REF = "Example provider API terms v1"
SENTINEL = "<host not usable in a statement>"

# One minimal valid settings dict per llm kind, written by hand, and the hosts each one talks to, ALSO written by
# hand (not computed from the host functions, so the hosts test is not a tautology).
SAMPLES: dict[str, dict] = {
    "anthropic": {"kind": "anthropic", "platform": "api", "api_key_secret_name": "llm-key"},
    "bedrock": {"kind": "bedrock", "region": "us-east-1"},
    "openai_compat": {"kind": "openai_compat", "base_url": "https://llm.example/v1"},
    "gemini": {"kind": "gemini", "api_key_secret_name": "llm-key"},
    "fake": {"kind": "fake", "recorded_dir": "recorded"},
}
HOSTS: dict[str, list[str]] = {
    "anthropic": ["api.anthropic.com"],
    "bedrock": ["bedrock-runtime.us-east-1.amazonaws.com"],
    "openai_compat": ["llm.example"],
    "gemini": ["generativelanguage.googleapis.com"],
}
REAL = list(HOSTS)
PAIRS = [  # hard-coded (kind, basis) pairs each kind accepts
    ("anthropic", "contract_terms"),
    ("anthropic", "account_setting"),
    ("bedrock", "contract_terms"),
    ("bedrock", "account_setting"),
    ("gemini", "contract_terms"),
    ("gemini", "account_setting"),
    ("openai_compat", "contract_terms"),
    ("openai_compat", "account_setting"),
    ("openai_compat", "self_hosted"),
]
NOT_SELF_HOSTED = ["anthropic", "bedrock", "gemini"]
VERTEX = {
    "kind": "anthropic",
    "platform": "vertex",
    "project_id": "proj-1",
    "region": "us-central1",
}
VERTEX_HOSTS = ["us-central1-aiplatform.googleapis.com", "oauth2.googleapis.com"]
FOUNDRY = {
    "kind": "anthropic",
    "platform": "foundry",
    "api_key_secret_name": "llm-key",
    "resource": "res1",
}


def _st(kind: str, today, **over) -> dict:
    """A valid statement for `kind`, dated `today`."""
    return {
        "basis": "contract_terms",
        "reference": GOOD_REF,
        "hosts": list(HOSTS[kind]),
        "checked_on": today,
        **over,
    }


def _real_today() -> dt.date:
    """The real UTC day, read here (not through the seam under test, so pins that need no seam also run on the base)."""
    return dt.datetime.now(dt.UTC).date()


def _write_llm(root: Path, llm: dict) -> None:
    path = root / "config.yaml"
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    cfg["backends"]["llm"] = llm
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")


def _make(tmp_path: Path, env: str, llm: dict, config: dict | None = None) -> Path:
    root = pilot_cfg(tmp_path / f"c{next(_COUNTER)}", env=env, config=config)
    _write_llm(root, llm)
    return root


def _load(tmp_path: Path, env: str, llm: dict, config: dict | None = None):
    return load_config(_make(tmp_path, env, llm, config))


def _cross_check_text(excinfo, env: str) -> str:
    """The exact text of the cross-check refusal, read from the error's cause (never from the wrapped str())."""
    cause = excinfo.value.__cause__
    assert isinstance(cause, ValidationError), f"cause is {cause!r}"
    errs = cause.errors()
    assert len(errs) == 1 and errs[0]["type"] == "value_error", errs
    text = str(errs[0]["ctx"]["error"])
    assert text.startswith(f"environment {env}: refused: "), text
    return text


def _field_error(excinfo) -> tuple[tuple, str]:
    """(loc, type) of the first error of the cause: settings-level and Config-level field errors."""
    cause = excinfo.value.__cause__
    assert isinstance(cause, ValidationError), f"cause is {cause!r}"
    err = cause.errors()[0]
    return tuple(err["loc"]), err["type"]


def _refused(tmp_path: Path, env: str, llm: dict, config: dict | None = None) -> str:
    with pytest.raises(ConfigError) as ei:
        _load(tmp_path, env, llm, config)
    return _cross_check_text(ei, env)


def _no_training_error(tmp_path: Path, llm: dict) -> ConfigError:
    """A statement-level refusal: the first error is under `no_training` and is not the old unknown-key error."""
    with pytest.raises(ConfigError) as ei:
        _load(tmp_path, "dev", llm)
    loc, typ = _field_error(ei)
    assert loc[0] == "no_training", (loc, typ)
    assert typ != "extra_forbidden" or len(loc) >= 2, (loc, typ)
    return ei.value


def _settings(kind: str, statement: dict | None):
    data = {**SAMPLES[kind]}
    if statement is not None:
        data["no_training"] = statement
    return TABLE["llm"][kind].settings(**data)


def _planted_settings(statement: dict | None):
    from hadavin_sdk.backends.table import OpenAICompatSettings

    data = {"kind": "planted", "base_url": "https://llm.example/v1"}
    if statement is not None:
        data["no_training"] = statement
    return OpenAICompatSettings(**data)


def _call(env: str, kind: str, statement: dict | None, today=FIXED_TODAY, limit=90, settings=None):
    from hadavin_sdk.config import _no_training_refusals

    return _no_training_refusals(env, settings or _settings(kind, statement), limit, today)


def _only(msgs: list[str]) -> str:
    assert len(msgs) == 1, msgs
    return msgs[0]


@pytest.fixture
def clock(monkeypatch):
    def set_today(day: dt.date) -> None:
        monkeypatch.setattr(config_mod, "_utc_today", lambda: day)

    return set_today


@pytest.fixture
def planted(monkeypatch):
    """A new llm kind added to the table with no `no_training` declaration (the fail-closed default)."""
    from hadavin_sdk.backends.table import Entry, OpenAICompatSettings

    monkeypatch.setitem(TABLE["llm"], "planted", Entry(OpenAICompatSettings, "x:y"))
    return {"kind": "planted", "base_url": "https://llm.example/v1"}


# ---------------------------------------------------------------------------------------------------- T1, T1b


@pytest.mark.parametrize("env", ["pilot", "prod"])
@pytest.mark.parametrize("kind", REAL)
def test_t1_no_statement_is_refused_in_pilot_and_prod(tmp_path, kind, env):
    text = _refused(tmp_path, env, SAMPLES[kind])
    assert f"llm: {kind}: no_training statement missing" in text


@pytest.mark.parametrize("env", ["pilot", "prod"])
def test_t1b_fake_keeps_its_own_dev_only_refusal(tmp_path, env):
    assert ("llm", "fake") in DEV_ONLY
    text = _refused(tmp_path, env, SAMPLES["fake"])
    assert re.search(r"refused: (.*, )?llm: fake(, |$)", text), text
    assert "declares no" not in text


# ---------------------------------------------------------------------------------------------------- T2, T3


@pytest.mark.parametrize("env", ["pilot", "prod"])
@pytest.mark.parametrize(("kind", "basis"), PAIRS)
def test_t2_each_accepted_basis_loads(tmp_path, kind, basis, env):
    llm = {**SAMPLES[kind], "no_training": _st(kind, _real_today(), basis=basis)}
    if env == "pilot":
        assert _load(tmp_path, "pilot", llm).backends.llm.no_training.basis == basis
    else:  # prod has other refusals (no anchor, the signer key file); none may be about the llm
        assert "llm:" not in _refused(tmp_path, "prod", llm)


@pytest.mark.parametrize("kind", NOT_SELF_HOSTED)
def test_t3_self_hosted_is_refused_for_hosted_kinds(tmp_path, kind):
    llm = {**SAMPLES[kind], "no_training": _st(kind, _real_today(), basis="self_hosted")}
    assert "no_training basis self_hosted not allowed" in _refused(tmp_path, "pilot", llm)


# ---------------------------------------------------------------------------------------------------- T4, T5


def test_t4_staleness_on_the_function():
    assert _call("pilot", "gemini", _st("gemini", FIXED_TODAY - dt.timedelta(days=90))) == []
    msgs = _call("pilot", "gemini", _st("gemini", FIXED_TODAY - dt.timedelta(days=91)))
    assert len(msgs) == 1 and "91 days old (limit 90)" in msgs[0]
    forty = _st("gemini", FIXED_TODAY - dt.timedelta(days=40))
    assert len(_call("pilot", "gemini", forty, limit=30)) == 1
    assert _call("pilot", "gemini", forty, limit=90) == []


def test_t4_staleness_at_load(tmp_path, clock):
    clock(FIXED_TODAY)
    llm = SAMPLES["openai_compat"]
    ok = {**llm, "no_training": _st("openai_compat", FIXED_TODAY - dt.timedelta(days=90))}
    assert _load(tmp_path, "pilot", ok)
    old = {**llm, "no_training": _st("openai_compat", FIXED_TODAY - dt.timedelta(days=91))}
    assert "91 days old (limit 90)" in _refused(tmp_path, "pilot", old)
    forty = {**llm, "no_training": _st("openai_compat", FIXED_TODAY - dt.timedelta(days=40))}
    assert _load(tmp_path, "pilot", forty)  # the default limit
    assert "40 days old (limit 30)" in _refused(
        tmp_path, "pilot", forty, {"no_training_max_age_days": 30}
    )


def test_t4_limit_bounds(tmp_path, clock):
    clock(FIXED_TODAY)
    llm = {**SAMPLES["openai_compat"], "no_training": _st("openai_compat", FIXED_TODAY)}
    for ok in (90, 1):
        cfg = _load(tmp_path, "pilot", llm, {"no_training_max_age_days": ok})
        assert cfg.no_training_max_age_days == ok
    for value, typ in ((0, "greater_than_equal"), (91, "less_than_equal")):
        with pytest.raises(ConfigError) as ei:
            _load(tmp_path, "pilot", llm, {"no_training_max_age_days": value})
        assert _field_error(ei) == (("no_training_max_age_days",), typ)


@pytest.mark.parametrize("value", [True, "30", 30.0], ids=["bool", "text", "float"])
def test_t4_limit_must_be_a_whole_number_not_a_look_alike(tmp_path, clock, value):
    """StrictInt: lax int would take `true` as 1, "30" as 30 and 30.0 as 30."""
    clock(FIXED_TODAY)
    llm = {**SAMPLES["openai_compat"], "no_training": _st("openai_compat", FIXED_TODAY)}
    with pytest.raises(ConfigError) as ei:
        _load(tmp_path, "pilot", llm, {"no_training_max_age_days": value})
    assert _field_error(ei) == (("no_training_max_age_days",), "int_type")


def test_t4b_future_beats_stale_when_both_are_true_only_for_a_direct_call():
    """Config holds the limit to 1 or more and the slack is 0 or more, so no loaded config can be both future and
    stale; only a direct call with a negative limit can. This row pins the documented order (future first)."""
    msgs = _call("pilot", "gemini", _st("gemini", FIXED_TODAY + dt.timedelta(days=3)), limit=-5)
    assert len(msgs) == 1 and "checked_on is in the future" in msgs[0], msgs


def test_t5_future_dates_on_the_function():
    assert _call("pilot", "bedrock", _st("bedrock", FIXED_TODAY + dt.timedelta(days=1))) == []
    msgs = _call("pilot", "bedrock", _st("bedrock", FIXED_TODAY + dt.timedelta(days=2)))
    assert len(msgs) == 1 and "checked_on is in the future" in msgs[0]


def test_t5_future_dates_at_load_use_the_seam(tmp_path, clock):
    day = _real_today() + dt.timedelta(
        days=10
    )  # far from the real clock, so a real-clock call site shows
    clock(day)
    llm = SAMPLES["openai_compat"]
    ok = {**llm, "no_training": _st("openai_compat", day + dt.timedelta(days=1))}
    assert _load(tmp_path, "pilot", ok)
    bad = {**llm, "no_training": _st("openai_compat", day + dt.timedelta(days=2))}
    assert "checked_on is in the future" in _refused(tmp_path, "pilot", bad)


# ---------------------------------------------------------------------------------------------------- T6, T6b


@pytest.mark.parametrize("kind", REAL)
def test_t6_dev_without_a_statement_loads(tmp_path, kind):
    assert _load(tmp_path, "dev", SAMPLES[kind])


def test_t6b_dev_validates_a_present_statement(tmp_path):
    old = _st("openai_compat", _real_today() - dt.timedelta(days=400))
    cfg = _load(tmp_path, "dev", {**SAMPLES["openai_compat"], "no_training": old})
    assert cfg.backends.llm.no_training.checked_on == old["checked_on"]
    bad = {**SAMPLES["openai_compat"], "no_training": _st("openai_compat", "x", basis="nope")}
    with pytest.raises(ConfigError) as ei:
        _load(tmp_path, "dev", bad)
    loc, _ = _field_error(ei)
    assert loc[0] == "no_training" and len(loc) >= 2


# ---------------------------------------------------------------------------------------------------- T7

BAD_REFERENCES = [
    "user:pw@host terms v1",
    "Example terms?token=abc",
    "Example terms v1\nsecond line",
    "Example terms v1\rsecond",
    "Example\x00terms v1",
    "Example\tterms v1",
    "ab",
    "abcdefg",  # 7 characters
    "a" + "b" * 199 + "c",  # 201
    "a" + "b" * 208 + "c",  # 210
    " " * 10,
    "",
    12345,
    ["Example terms v1"],
    "arn:aws:iam::" + "123456" + "789012" + ":role/x",  # a 12-digit run, built from parts
    GOOD_REF + "\n",
]
BAD_HOSTS = [
    [],
    ["a"] * 9,
    ["a/b"],
    ["a b"],
    ["a@b"],
    ["a?b"],
    ["a#b"],
    ["a" * 254],
    "llm.example",
    ["llm.example\n"],
]
BAD_DATES = [
    20000,
    1767000000,
    0,
    86400,
    1767225600,
    "1767225600",
    1767225600.0,
    "0",
    "20261105",
    "05/11/2026",
    True,
    dt.datetime.fromisoformat("2026-11-05T09:30:00"),
    dt.datetime.fromisoformat(
        "2026-11-05T00:00:00"
    ),  # what YAML 2026-11-05T00:00:00 unquoted loads as
    None,
    "".join(
        chr(0x0660 + int(c)) if c.isdigit() else c for c in "2026-11-05"
    ),  # Arabic-Indic digits
    "".join(chr(0xFF10 + int(c)) if c.isdigit() else c for c in "2026-11-05"),  # fullwidth digits
    "2026-11-05\n",
]
IMPOSSIBLE_DATES = ["2026-13-45", "2026-02-30", "0000-00-00"]


def _with_statement(**over) -> dict:
    return {**SAMPLES["openai_compat"], "no_training": _st("openai_compat", _real_today(), **over)}


@pytest.mark.parametrize("value", BAD_REFERENCES, ids=lambda v: repr(v)[:30])
def test_t7_bad_reference_is_refused(tmp_path, value):
    _no_training_error(tmp_path, _with_statement(reference=value))


@pytest.mark.parametrize("value", BAD_HOSTS, ids=lambda v: repr(v)[:30])
def test_t7_bad_hosts_are_refused(tmp_path, value):
    _no_training_error(tmp_path, _with_statement(hosts=value))


@pytest.mark.parametrize("value", BAD_DATES, ids=lambda v: repr(v)[:30])
def test_t7_bad_checked_on_is_refused(tmp_path, value):
    _no_training_error(tmp_path, _with_statement(checked_on=value))


@pytest.mark.parametrize("value", IMPOSSIBLE_DATES)
def test_t7_impossible_dates_give_the_fixed_text_and_no_input(tmp_path, value):
    err = _no_training_error(tmp_path, _with_statement(checked_on=value))
    assert "checked_on must be a date written YYYY-MM-DD" in str(err)
    assert value not in str(err)


def test_t7_non_ascii_digits_are_refused_by_the_pattern_not_only_by_the_parser(monkeypatch):
    """CPython's C `fromisoformat` happens to refuse non-ASCII digits, and the pure-Python one on 3.12 accepts them.
    The `[0-9]` pattern must refuse them first: swap in a lax parser (`int()` reads any Unicode digit) and see it."""
    import hadavin_sdk.backends.table as table_mod
    from hadavin_sdk.backends.table import NoTrainingStatement

    arabic = "\u0662\u0660\u0662\u0666-\u0661\u0661-\u0660\u0665"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", arabic)  # what a `\d` pattern would let through

    def lax(text):
        return dt.date(int(text[:4]), int(text[5:7]), int(text[8:10]))

    assert lax(arabic) == dt.date(2026, 11, 5)
    monkeypatch.setattr(table_mod, "_iso_date_or_none", lax)
    with pytest.raises(ValidationError) as ei:
        NoTrainingStatement(**_st("openai_compat", arabic))
    assert "checked_on must be a date written YYYY-MM-DD" in str(ei.value)


@pytest.mark.parametrize("value", ["unknown", "Contract_Terms", ["contract_terms"]])
def test_t7_bad_basis_is_refused(tmp_path, value):
    _no_training_error(tmp_path, _with_statement(basis=value))


@pytest.mark.parametrize(
    "statement",
    [
        {**_st("openai_compat", dt.date(2027, 1, 1)), "extra": "x"},
        "contract_terms",
        [_st("openai_compat", dt.date(2027, 1, 1))],
    ],
    ids=["extra-key", "bare-string", "list"],
)
def test_t7_bad_statement_shape_is_refused(tmp_path, statement):
    _no_training_error(tmp_path, {**SAMPLES["openai_compat"], "no_training": statement})


def test_t7_boundaries_are_accepted():
    from hadavin_sdk.backends.table import NoTrainingStatement

    base = _st("openai_compat", dt.date(2027, 1, 1))
    for over in (
        {"reference": "a" + "b" * 6 + "c"},  # exactly 8
        {"reference": "a" + "b" * 198 + "c"},  # exactly 200
        {"hosts": ["a" * 253]},
        {"hosts": ["::1"]},
        {"hosts": ["res" + "123456" + "789012" + ".example"]},  # a 12-digit run in a host is legal
        {
            "reference": "Terms id 1234-5678-9012 v1"
        },  # KNOWN tripwire gap, pinned: a split id passes
    ):
        assert NoTrainingStatement(**{**base, **over})


def test_t7_statement_on_fake_is_refused_as_an_unknown_key(tmp_path):
    llm = {**SAMPLES["fake"], "no_training": _st("openai_compat", dt.date(2027, 1, 1))}
    with pytest.raises(ConfigError) as ei:
        _load(tmp_path, "dev", llm)
    assert _field_error(ei) == (("no_training",), "extra_forbidden")


def _duplicate_line(root: Path, key: str, value: str) -> None:
    path = root / "config.yaml"
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if m := re.match(rf"^( *){key}:", line):
            out.append(f"{m.group(1)}{key}: {value}")  # the same key twice in one mapping
        out.append(line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


@pytest.mark.parametrize(("key", "value"), [("no_training", "{}"), ("checked_on", "2020-01-01")])
def test_t7_duplicate_yaml_key_is_refused(tmp_path, key, value):
    root = _make(tmp_path, "dev", _with_statement())
    _duplicate_line(root, key, value)
    with pytest.raises(ConfigError, match="duplicate key"):
        load_config(root)


def test_t7b_checked_on_loads_as_a_yaml_date_or_a_quoted_text(tmp_path):
    day = dt.date(2026, 11, 5)
    for value in (day, "2026-11-05"):  # safe_dump writes the first unquoted and the second quoted
        root = _make(tmp_path, "dev", _with_statement(checked_on=value))
        text = (root / "config.yaml").read_text(encoding="utf-8")
        assert ("checked_on: '2026-11-05'" in text) == isinstance(value, str)
        assert load_config(root).backends.llm.no_training.checked_on == day


# ---------------------------------------------------------------------------------------------------- T8


def test_t8_statement_adds_no_secret_names():
    from hadavin_sdk.backends.platform_secrets import secret_names

    for kind in REAL:
        assert secret_names(_settings(kind, _st(kind, FIXED_TODAY))) == secret_names(
            _settings(kind, None)
        )


def test_t8_no_statement_field_ends_in_secret_name():
    from hadavin_sdk.backends.table import NoTrainingStatement

    for kind, entry in TABLE["llm"].items():
        fields = entry.settings.model_fields
        if kind == "fake":
            assert "no_training" not in fields
            continue
        assert fields["no_training"].annotation == (NoTrainingStatement | None), kind
        for name, field in fields.items():
            if field.annotation == (NoTrainingStatement | None):
                assert not name.endswith("_secret_name"), (kind, name)


CANARY_PARTS = ("Canary", "reference", "zq7x", "k2m9")


def test_t8_credential_shaped_reference_is_refused_and_absent(tmp_path):
    secret = "user:" + "pass" + "word@" + "host.example"
    err = _no_training_error(tmp_path, _with_statement(reference=secret))
    assert secret not in str(err) and "pass" + "word" not in str(err)


def test_t8_refusals_never_hold_the_reference(tmp_path):
    today = _real_today()
    canary = " ".join(CANARY_PARTS)
    cases = [
        ("openai_compat", {"checked_on": today - dt.timedelta(days=200)}),  # stale
        ("anthropic", {"basis": "self_hosted"}),  # wrong basis
        ("openai_compat", {"checked_on": today + dt.timedelta(days=30)}),  # future
        ("openai_compat", {"hosts": ["other.example"]}),  # hosts mismatch
    ]
    for kind, over in cases:
        statement = _st(kind, today, reference=canary, **over)
        msgs = _call("pilot", kind, statement, today=today)
        assert len(msgs) == 1, (kind, over, msgs)
        assert canary not in msgs[0] and CANARY_PARTS[2] not in msgs[0]
        llm = {**SAMPLES[kind], "no_training": statement}
        assert CANARY_PARTS[2] not in _refused(tmp_path, "pilot", llm)
        with pytest.raises(ConfigError) as ei:
            _load(tmp_path, "pilot", llm)
        assert CANARY_PARTS[2] not in str(ei.value)


# ---------------------------------------------------------------------------------------------------- T9b


def test_t9b_every_real_kind_declares_a_subset_of_the_three_bases():
    allowed = {"contract_terms", "account_setting", "self_hosted"}
    for kind, entry in TABLE["llm"].items():
        if ("llm", kind) in DEV_ONLY:
            assert entry.no_training == frozenset()
            continue
        assert entry.no_training, kind
        assert entry.no_training <= allowed, kind
    assert "self_hosted" in TABLE["llm"]["openai_compat"].no_training
    for kind in NOT_SELF_HOSTED:
        assert "self_hosted" not in TABLE["llm"][kind].no_training


def test_t9b_a_new_kind_with_no_declaration_is_refused_even_with_a_statement(tmp_path, planted):
    text = "llm: planted: declares no no_training basis"
    assert text in _refused(
        tmp_path, "pilot", {**planted, "no_training": _st("openai_compat", _real_today())}
    )
    assert text in _refused(tmp_path, "pilot", planted)


# ---------------------------------------------------------------------------------------------------- T10


def test_t10_the_statement_is_not_in_the_agent_hash(tmp_path):
    from hadavin_sdk.registry import load_registry

    def digest(llm: dict) -> str:
        return load_registry(load_config(_make(tmp_path, "dev", llm))).config_hash("ito-agent")

    plain = digest(SAMPLES["openai_compat"])
    day_a = digest(_with_statement(checked_on=dt.date(2026, 1, 1)))
    day_b = digest(_with_statement(checked_on=dt.date(2026, 6, 1)))
    assert plain == day_a == day_b


# ---------------------------------------------------------------------------------------------------- T12


def test_t12_pilot_cfg_dates_its_statement_from_the_clock_seam(tmp_path, clock):
    day = _real_today() + dt.timedelta(days=120)
    clock(day)
    root = pilot_cfg(tmp_path / "far")
    cfg = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
    assert cfg["backends"]["llm"]["no_training"]["checked_on"] == day
    assert load_config(root)  # age 0 at the patched clock; a literal date would be 120 days old


# ---------------------------------------------------------------------------------------------------- T13


def test_t13_each_message_names_the_kind_and_the_reason(planted):
    assert "llm: planted: declares no no_training basis (cannot run in pilot)" in _only(
        _call("pilot", "", None, settings=_planted_settings(None))
    )
    assert "llm: anthropic: no_training statement missing (add backends.llm.no_training" in _only(
        _call("pilot", "anthropic", None)
    )
    wrong_basis = _st("anthropic", FIXED_TODAY, basis="self_hosted")
    assert (
        "llm: anthropic: no_training basis self_hosted not allowed "
        "(allowed: account_setting | contract_terms)"
        in _only(_call("pilot", "anthropic", wrong_basis))
    )
    wrong_hosts = _st("anthropic", FIXED_TODAY, hosts=["other.example"])
    assert (
        "llm: anthropic: no_training hosts do not match the configured endpoint "
        "(expected: api.anthropic.com)" in _only(_call("pilot", "anthropic", wrong_hosts))
    )
    future = _st("anthropic", FIXED_TODAY + dt.timedelta(days=2))
    assert "llm: anthropic: no_training checked_on is in the future" in _only(
        _call("pilot", "anthropic", future)
    )
    stale = _st("anthropic", FIXED_TODAY - dt.timedelta(days=95))
    assert "llm: anthropic: no_training statement is 95 days old (limit 90)" in _only(
        _call("pilot", "anthropic", stale)
    )


# ---------------------------------------------------------------------------------------------------- T14


def _hosts_ok(tmp_path, llm: dict, hosts: list[str]) -> None:
    statement = _st("openai_compat", _real_today(), hosts=hosts)
    assert _load(tmp_path, "pilot", {**llm, "no_training": statement})


def _hosts_bad(tmp_path, llm: dict, hosts: list[str], expect: str | None = None) -> str:
    statement = _st("openai_compat", _real_today(), hosts=hosts)
    text = _refused(tmp_path, "pilot", {**llm, "no_training": statement})
    assert "hosts do not match" in text
    if expect:
        assert expect in text
    return text


@pytest.mark.parametrize("kind", REAL)
def test_t14_matching_hosts_pass_in_any_order_case_and_repeat(tmp_path, kind):
    hosts = HOSTS[kind]
    _hosts_ok(tmp_path, SAMPLES[kind], hosts)
    _hosts_ok(tmp_path, SAMPLES[kind], [h.upper() for h in hosts])
    _hosts_ok(tmp_path, SAMPLES[kind], hosts + hosts)  # one host written twice
    _hosts_ok(tmp_path, SAMPLES[kind], list(reversed(hosts)))


@pytest.mark.parametrize("kind", REAL)
def test_t14_wrong_and_extra_hosts_are_refused(tmp_path, kind):
    _hosts_bad(
        tmp_path, SAMPLES[kind], ["wrong.example"], f"expected: {', '.join(sorted(HOSTS[kind]))}"
    )
    _hosts_bad(tmp_path, SAMPLES[kind], HOSTS[kind] + ["extra.example"])  # a superset


def test_t14_vertex_needs_both_hosts_in_any_order(tmp_path):
    _hosts_ok(tmp_path, VERTEX, VERTEX_HOSTS)
    _hosts_ok(tmp_path, VERTEX, list(reversed(VERTEX_HOSTS)))
    _hosts_bad(tmp_path, VERTEX, VERTEX_HOSTS[:1])  # a missing host
    _hosts_bad(tmp_path, VERTEX, VERTEX_HOSTS[1:])


def test_t14_the_statement_must_follow_the_endpoint(tmp_path):
    _hosts_bad(tmp_path, VERTEX, HOSTS["anthropic"])  # written for api, config says vertex
    _hosts_bad(tmp_path, FOUNDRY, HOSTS["anthropic"])  # written for api, config says foundry
    _hosts_bad(tmp_path, {**SAMPLES["bedrock"], "region": "eu-west-1"}, HOSTS["bedrock"])
    other = {**SAMPLES["openai_compat"], "base_url": "https://other.example/v1"}
    _hosts_bad(tmp_path, other, HOSTS["openai_compat"])


def test_t14_names_with_capitals_digits_and_loopback_pass(tmp_path):
    _hosts_ok(tmp_path, {**FOUNDRY, "resource": "MyRes"}, ["myres.services.ai.azure.com"])
    digits = {**FOUNDRY, "resource": "res" + "123456" + "789012"}
    _hosts_ok(tmp_path, digits, ["res123456789012.services.ai.azure.com"])
    # This row only proves the config loads; nothing in config.py refuses a loopback llm in pilot.
    loopback = {"kind": "openai_compat", "base_url": "http://[::1]:8000/v1"}
    statement = _st("openai_compat", _real_today(), basis="self_hosted", hosts=["::1"])
    assert _load(tmp_path, "pilot", {**loopback, "no_training": statement})


@pytest.mark.parametrize(
    ("base_url", "host"),
    [("http://[::1]:8000/v1", "::1"), ("https://llm.example/v1", "llm.example")],
    ids=["loopback", "public-https"],
)
def test_t3b_self_hosted_is_the_operators_word_and_is_not_checked_against_the_host(
    tmp_path, base_url, host
):
    """Pins today's behaviour: openai_compat accepts `self_hosted` on ANY host, loopback or public. The code cannot
    tell a server the client runs from one it does not; refusing a public `self_hosted` belongs to P6a's
    client-profile check. If that check lands here instead, change this test on purpose."""
    llm = {"kind": "openai_compat", "base_url": base_url}
    statement = _st("openai_compat", _real_today(), basis="self_hosted", hosts=[host])
    assert _load(tmp_path, "pilot", {**llm, "no_training": statement})


def test_t14_an_endpoint_with_no_host_name_is_refused(tmp_path):
    llm = {**SAMPLES["openai_compat"], "base_url": "https:///v1"}
    text = _hosts_bad(tmp_path, llm, ["llm.example"])
    assert "expected: none (the endpoint has no host name)" in text


@pytest.mark.parametrize(
    ("llm", "raw"),
    [
        ({**SAMPLES["openai_compat"], "base_url": "https://bücher.example/v1"}, "bücher"),
        (
            {**SAMPLES["openai_compat"], "base_url": "https://ex" + chr(27) + "ample.com/v1"},
            chr(27),
        ),
        ({**FOUNDRY, "resource": "a" * 250}, "a" * 250),
    ],
    ids=["non-ascii", "escape", "too-long"],
)
def test_t14_a_host_the_pattern_cannot_hold_is_never_printed(tmp_path, llm, raw):
    text = _hosts_bad(tmp_path, llm, ["llm.example"], SENTINEL)
    assert raw not in text
    with pytest.raises(ConfigError) as ei:
        _load(tmp_path, "pilot", {**llm, "no_training": _st("openai_compat", _real_today())})
    assert raw not in str(ei.value)


# ---------------------------------------------------------------------------------------------------- T15


def test_t15_every_llm_kind_has_a_sample():
    assert set(SAMPLES) == set(TABLE["llm"]), (
        "a new llm kind needs a SAMPLES row and an Entry.no_training declaration"
    )


# ---------------------------------------------------------------------------------------------------- T16

WRONG_HOSTS = ["wrong.example"]
FUTURE = FIXED_TODAY + dt.timedelta(days=30)
STALE = FIXED_TODAY - dt.timedelta(days=200)
MARK = {
    "a": "declares no no_training basis",
    "b": "no_training statement missing",
    "c": "not allowed",
    "f": "hosts do not match",
    "d": "is in the future",
    "e": "days old",
}


def _one_message(msgs: list[str], mark: str) -> None:
    """Exactly one message, and it is the one for the first check in the order a, b, c, f, d, e."""
    assert len(msgs) == 1, msgs
    for other, text in MARK.items():
        assert (text in msgs[0]) == (other == mark), (mark, msgs[0])


@pytest.mark.parametrize("row", [1, 2, 3])
def test_t16_planted_kind_always_gets_the_declaration_message(planted, row):
    statement = {
        1: None,
        2: _st("openai_compat", FUTURE, hosts=WRONG_HOSTS),
        3: _st("openai_compat", STALE),
    }[row]
    _one_message(_call("pilot", "", None, settings=_planted_settings(statement)), "a")


@pytest.mark.parametrize("kind", REAL)
def test_t16_rows_4_and_7_to_10(kind):
    _one_message(_call("pilot", kind, None), "b")
    _one_message(_call("pilot", kind, _st(kind, FUTURE, hosts=WRONG_HOSTS)), "f")
    _one_message(_call("pilot", kind, _st(kind, STALE, hosts=WRONG_HOSTS)), "f")
    _one_message(_call("pilot", kind, _st(kind, FUTURE)), "d")
    _one_message(_call("pilot", kind, _st(kind, STALE)), "e")


@pytest.mark.parametrize("kind", NOT_SELF_HOSTED)
def test_t16_rows_5_and_6_wrong_basis_comes_first(kind):
    _one_message(
        _call("pilot", kind, _st(kind, FUTURE, basis="self_hosted", hosts=WRONG_HOSTS)), "c"
    )
    _one_message(
        _call("pilot", kind, _st(kind, STALE, basis="self_hosted", hosts=WRONG_HOSTS)), "c"
    )


def test_t16_dev_and_fake_are_never_checked():
    assert _call("dev", "anthropic", None) == []
    assert (
        _call("pilot", "fake", None, settings=TABLE["llm"]["fake"].settings(**SAMPLES["fake"]))
        == []
    )
