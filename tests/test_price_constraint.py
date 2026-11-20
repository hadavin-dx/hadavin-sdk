"""Step C, the price constraint: a route price that is zero, negative, not finite, too large or too fine is refused
when the config loads, and a pilot or prod config must say the day its prices were read (`prices_as_of`).

Written from the ticket's invariants by a different agent than the builder of the source."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
import yaml

from hadavin_sdk import config as config_mod
from hadavin_sdk.config import Config, ConfigError, load_config
from hadavin_sdk.registry import load_registry
from tests.test_client_profile import prod_cfg
from tests.test_k3_pilot_env import pilot_cfg

TODAY = date(2026, 11, 20)
IN, OUT = "input_usd_per_mtok", "output_usd_per_mtok"
FIELDS = (IN, OUT)
REAL_LLM = {"kind": "openai_compat", "base_url": "https://llm.example/v1"}
ZERO_TEXT = "a zero price is allowed only for the fake llm kind in demo"
# config_hash("test-agent") of the fixture config; the same value on the commit before the source change.
FIXTURE_HASH = "3ac5b7c34e7a0d7750a75adcd4642364be70af601e8078ee6b46c0dfb0f1be9e"
ZEROS = ["0", "0.00", "0E-10", 0]


def edit(cfg_dir: Path, fn) -> Path:
    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    fn(data)
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return cfg_dir


def set_price(cfg_dir: Path, value, field: str = IN, route: str = "default") -> Path:
    return edit(cfg_dir, lambda d: d["routes"][route].__setitem__(field, value))


def real_kind(cfg_dir: Path) -> Path:
    """The demo fixture with a real llm kind (allowed in demo only beside `made_up_data_only`)."""

    def fn(d):
        d["backends"]["llm"] = dict(REAL_LLM)
        d["made_up_data_only"] = True

    return edit(cfg_dir, fn)


def add_route(cfg_dir: Path, name: str, **prices) -> Path:
    route = {"model_id": "other-model", IN: "2", OUT: "10", "max_tokens": 64, **prices}
    return edit(cfg_dir, lambda d: d["routes"].__setitem__(name, route))


def refusal(cfg_dir: Path) -> str:
    with pytest.raises(ConfigError) as err:
        load_config(cfg_dir)
    return str(err.value)


@pytest.fixture
def today(monkeypatch):
    monkeypatch.setattr(config_mod, "_today", lambda: TODAY)
    return TODAY


# --- FAIL-BEFORE: both configs loaded before the source change (no `_today`, no `prices_as_of`) -------------


def test_fail_before_zero_price_with_a_real_kind_in_demo_is_refused(cfg_dir):
    with pytest.raises(ConfigError):
        load_config(set_price(real_kind(cfg_dir), "0"))


def test_fail_before_negative_price_with_the_fake_kind_is_refused(cfg_dir):
    with pytest.raises(ConfigError):
        load_config(set_price(cfg_dir, "-1"))


# --- normal -----------------------------------------------------------------------------------------------


def test_n1_demo_fake_priced_loads_without_a_date(cfg_dir):
    cfg = load_config(cfg_dir)
    assert cfg.prices_as_of is None
    assert cfg.backends.llm.kind == "fake"
    assert config_mod._price_refusals(cfg) == []


def test_n2_pilot_and_prod_load_with_the_date(tmp_path, today):
    pilot = load_config(pilot_cfg(tmp_path / "a"))
    assert (pilot.environment, pilot.prices_as_of) == ("pilot", date(2026, 11, 1))
    prod = load_config(prod_cfg(tmp_path / "b"))
    assert (prod.environment, prod.prices_as_of) == ("prod", date(2026, 11, 1))


def test_n3_demo_real_kind_priced_loads_without_a_date(cfg_dir):
    cfg = load_config(real_kind(cfg_dir))
    assert cfg.backends.llm.kind == "openai_compat"
    assert cfg.prices_as_of is None


# --- zero: only the fake kind AND demo ---------------------------------------------------------------------


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("zero", ZEROS, ids=repr)
def test_e1_zero_loads_for_fake_in_demo(cfg_dir, zero, field):
    assert getattr(load_config(set_price(cfg_dir, zero, field)).routes["default"], field) == 0


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("zero", ZEROS, ids=repr)
def test_e2_zero_refused_for_a_real_kind_in_demo(cfg_dir, zero, field):
    text = refusal(set_price(real_kind(cfg_dir), zero, field))
    assert f"routes.default.{field}: {ZERO_TEXT}" in text
    other = OUT if field == IN else IN
    assert f"routes.default.{other}" not in text


def test_e3_zero_on_a_route_no_agent_uses_is_refused(cfg_dir):
    text = refusal(add_route(real_kind(cfg_dir), "spare", **{OUT: "0"}))
    assert f"routes.spare.{OUT}: {ZERO_TEXT}" in text
    assert f"routes.spare.{IN}" not in text
    assert "routes.default" not in text


@pytest.mark.parametrize("field", FIELDS)
def test_e3_zero_on_a_judge_route_is_refused(cfg_dir, field):
    def judge(d):
        d["backends"]["detector"] = [
            {"kind": "regex", "threshold": 0.5},
            {"kind": "llm_judge", "route": "screen"},
        ]

    cfg_dir = add_route(real_kind(cfg_dir), "screen")
    assert load_config(edit(cfg_dir, judge)).routes["screen"]  # priced: loads
    text = refusal(set_price(cfg_dir, "0", field, route="screen"))
    assert f"routes.screen.{field}: {ZERO_TEXT}" in text


def test_e4_fake_in_pilot_with_zero_is_refused_beside_the_other_refusals(cfg_dir):
    """The stage is tested by itself: fake is not let through just because it is fake."""
    text = refusal(edit(set_price(cfg_dir, "0"), lambda d: d.__setitem__("environment", "pilot")))
    assert "environment pilot: refused:" in text
    assert "llm: fake" in text
    assert f"routes.default.{IN}: {ZERO_TEXT}" in text
    assert "prices_as_of is required in pilot and prod" in text


@pytest.mark.parametrize("env", ["pilot", "prod"])
def test_e4_fake_kind_zero_price_refusals_do_not_depend_on_the_demo_only_table(cfg_dir, env):
    """`_price_refusals` itself names the zero price for fake outside demo (model_copy skips validation)."""
    cfg = load_config(set_price(cfg_dir, "0", OUT)).model_copy(update={"environment": env})
    assert cfg.backends.llm.kind == "fake"
    assert f"routes.default.{OUT}: {ZERO_TEXT}" in config_mod._price_refusals(cfg)


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("env", ["pilot", "prod"])
def test_e5_zero_refused_for_a_real_kind_in_pilot_and_prod(tmp_path, today, env, field):
    root = prod_cfg(tmp_path) if env == "prod" else pilot_cfg(tmp_path)
    text = refusal(set_price(root, "0", field))
    assert f"environment {env}: refused:" in text
    assert f"routes.default.{field}: {ZERO_TEXT}" in text
    assert "prices_as_of" not in text  # the date is there: only the price is refused


def test_h5_a_config_changed_by_model_copy_is_still_named_by_the_helper(cfg_dir):
    cfg = load_config(real_kind(cfg_dir))
    route = cfg.routes["default"].model_copy(update={IN: 0})
    changed = cfg.model_copy(update={"routes": {"default": route}})
    assert config_mod._price_refusals(changed) == [f"routes.default.{IN}: {ZERO_TEXT}"]


# --- the price date ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("env", ["pilot", "prod"])
def test_e5_date_required_in_pilot_and_prod(tmp_path, today, env):
    root = prod_cfg(tmp_path) if env == "prod" else pilot_cfg(tmp_path)
    text = refusal(edit(root, lambda d: d.pop("prices_as_of")))
    assert f"environment {env}: refused:" in text
    assert "prices_as_of is required in pilot and prod (the day the route prices were read)" in text


def test_e5_date_set_to_null_counts_as_missing_in_pilot(tmp_path, today):
    text = refusal(edit(pilot_cfg(tmp_path), lambda d: d.__setitem__("prices_as_of", None)))
    assert "prices_as_of is required in pilot and prod" in text


@pytest.mark.parametrize(
    "day",
    [TODAY, TODAY - timedelta(days=1), date(2023, 11, 20), date(1999, 1, 1)],
    ids=["today", "yesterday", "three-years-old", "very-old"],
)
@pytest.mark.parametrize("quoted", [True, False], ids=["text", "yaml-date"])
def test_e6_today_and_old_dates_load(tmp_path, cfg_dir, today, day, quoted):
    value = day.isoformat() if quoted else day
    pilot = edit(pilot_cfg(tmp_path), lambda d: d.__setitem__("prices_as_of", value))
    assert load_config(pilot).prices_as_of == day
    demo = edit(cfg_dir, lambda d: d.__setitem__("prices_as_of", value))
    assert load_config(demo).prices_as_of == day


def test_e6_unquoted_yaml_date_loads(tmp_path, today):
    root = pilot_cfg(tmp_path)
    path = root / "config.yaml"
    text = path.read_text(encoding="utf-8")
    assert "prices_as_of: '2026-11-01'" in text
    path.write_text(
        text.replace("prices_as_of: '2026-11-01'", "prices_as_of: 2026-11-20"), encoding="utf-8"
    )
    assert load_config(root).prices_as_of == TODAY


@pytest.mark.parametrize("days", [1, 2, 366])
def test_e6_future_date_refused_in_every_stage(tmp_path, cfg_dir, today, days):
    value = (TODAY + timedelta(days=days)).isoformat()
    for root in (pilot_cfg(tmp_path), cfg_dir):
        text = refusal(edit(root, lambda d: d.__setitem__("prices_as_of", value)))
        assert "refused:" in text
        assert "prices_as_of is in the future (UTC)" in text
        assert "prices_as_of is required" not in text


def test_e6_the_day_is_read_from_the_clock_at_load(tmp_path, monkeypatch):
    root = edit(pilot_cfg(tmp_path), lambda d: d.__setitem__("prices_as_of", "2026-11-20"))
    monkeypatch.setattr(config_mod, "_today", lambda: date(2026, 11, 19))
    assert "in the future" in refusal(root)
    monkeypatch.setattr(config_mod, "_today", lambda: date(2026, 11, 20))
    assert load_config(root).prices_as_of == TODAY


def test_today_is_the_utc_date(monkeypatch):
    before = datetime.now(UTC).date()
    got = config_mod._today()
    assert type(got) is date
    assert before <= got <= datetime.now(UTC).date()


H4 = [
    0,
    1700006400,
    "1700006400",
    1700006400.0,
    True,
    False,
    "",
    " ",
    "20/11/2026",
    "2026-11-20T00:00:00",
    "2026-11-20T00:00:00Z",
    "2026-11-20 00:00:00",
    "2026-11-20 ",
    " 2026-11-20",
    "2026-11-20\n",
    "2026-02-30",
    "2026-13-01",
    "2026-00-10",
    "0000-01-01",
    "2026-1-5",
    "20261120",
    "+2026-11-20",
    "today",
    datetime(2026, 11, 20, 0, 0, 0),  # noqa: DTZ001 (what YAML reads from an unquoted timestamp)
    datetime(2026, 11, 19, 12, 30, 0),  # noqa: DTZ001
    "٢٠٢٦-١١-٢٠",
    ["2026-11-20"],
    {"year": 2026},
]


@pytest.mark.parametrize("value", H4, ids=repr)
@pytest.mark.parametrize("env_name", ["pilot", "demo"])
def test_h4_only_a_plain_date_is_read(tmp_path, cfg_dir, today, value, env_name):
    root = pilot_cfg(tmp_path) if env_name == "pilot" else cfg_dir
    text = refusal(edit(root, lambda d: d.__setitem__("prices_as_of", value)))
    assert "prices_as_of" in text
    shape = ("-" not in value) if isinstance(value, str) else True
    if shape or not str(value).isascii() or len(str(value)) != 10:
        assert "prices_as_of must be a date written YYYY-MM-DD" in text


def test_h4_a_datetime_object_is_refused_directly(cfg_dir, today):
    raw = load_config(cfg_dir).model_dump()
    assert Config(**{**raw, "prices_as_of": TODAY}).prices_as_of == TODAY
    with pytest.raises(ValueError, match="prices_as_of must be a date written YYYY-MM-DD"):
        Config(**{**raw, "prices_as_of": datetime(2026, 11, 20, tzinfo=UTC)})


def test_h6_the_date_under_a_route_is_refused(cfg_dir):
    text = refusal(
        edit(cfg_dir, lambda d: d["routes"]["default"].__setitem__("prices_as_of", "2026-11-01"))
    )
    assert "routes.default.prices_as_of" in text


# --- sign, finiteness, ceiling, decimals: any stage, any kind ---------------------------------------------

BIG = "9" * 10_000
H1 = [
    ("-1", "a price must not be negative"),
    ("-0", "a price must not be negative"),
    ("-0.00", "a price must not be negative"),
    ("-0E+5", "a price must not be negative"),
    ("-0.000001", "a price must not be negative"),
    (-1, "a price must not be negative"),
    ("-1E-30", "a price must not be negative"),
    ("-" + BIG, "a price must not be negative"),
    ("NaN", "finite number"),
    ("-NaN", "finite number"),
    ("sNaN", "finite number"),
    ("Infinity", "finite number"),
    ("-Infinity", "finite number"),
    ("inf", "finite number"),
    (0.0, "not a float"),
    (-0.0, "not a float"),
    (3.0, "not a float"),
    (float("nan"), "not a float"),
    (float("inf"), "not a float"),
    (True, ""),
    (False, ""),
    (None, ""),
    ("", ""),
    ("three", ""),
    ("1,5", ""),
    (["3.00"], ""),
    ("1000000.000001", "a price may be at most 1000000"),
    ("1000001", "a price may be at most 1000000"),
    (1000001, "a price may be at most 1000000"),
    ("1E+30", "a price may be at most 1000000"),
    ("1E+999999", "a price may be at most 1000000"),
    (BIG, "a price may be at most 1000000"),
    ("0.0000001", "a price may have at most 6 decimal places"),
    ("1E-30", "a price may have at most 6 decimal places"),
    ("1E-999999", "a price may have at most 6 decimal places"),
    ("3.0000001", "a price may have at most 6 decimal places"),
    ("999999.9999999", "a price may have at most 6 decimal places"),
    ("999999." + "9" * 40, "a price may have at most 6 decimal places"),
    ("0." + "0" * 9_999 + "1", "a price may have at most 6 decimal places"),
]


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize(("value", "why"), H1, ids=lambda v: repr(v)[:24])
def test_h1_e7_bad_price_refused_for_fake_in_demo(cfg_dir, value, why, field):
    text = refusal(set_price(cfg_dir, value, field))
    assert f"routes.default.{field}" in text
    assert why in text
    assert len(text) < 2_000  # the 10,000-digit number is not echoed
    assert "99999" not in text


@pytest.mark.parametrize(
    "value", ["-1", "-0", "NaN", "Infinity", "1000000.000001", "0.0000001", 0.0, True]
)
@pytest.mark.parametrize("env_name", ["demo-real", "pilot", "prod"])
def test_i1_bad_price_refused_in_every_stage_and_kind(tmp_path, cfg_dir, today, value, env_name):
    root = {
        "demo-real": lambda: real_kind(cfg_dir),
        "pilot": lambda: pilot_cfg(tmp_path),
        "prod": lambda: prod_cfg(tmp_path),
    }[env_name]()
    load_config(root)
    assert f"routes.default.{OUT}" in refusal(set_price(root, value, OUT))


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize(
    "value",
    ["0.000001", "1000000", "1000000.000000", "1E+6", "1E-6", "999999.999999", 1000000, 1, "3"],
    ids=repr,
)
def test_e7_prices_at_the_bounds_load(cfg_dir, value, field):
    price = getattr(
        load_config(set_price(real_kind(cfg_dir), value, field)).routes["default"], field
    )
    assert 0 < price <= 1_000_000


@pytest.mark.parametrize("zero", ["0E+30", "0E+999999", "0E-999999", "0." + "0" * 9_999])
def test_hostile_zero_spellings_never_escape_as_another_error(cfg_dir, zero):
    """A zero with a huge exponent is either loaded as zero (fake in demo) or refused: never a crash, and
    never loaded for a real kind."""
    try:
        assert load_config(set_price(cfg_dir, zero)).routes["default"].input_usd_per_mtok == 0
    except ConfigError as exc:
        assert f"routes.default.{IN}" in str(exc)
    assert f"routes.default.{IN}" in refusal(set_price(real_kind(cfg_dir), zero))


def test_i3_both_fields_and_every_route_are_checked_for_sign(cfg_dir):
    add_route(cfg_dir, "spare")
    for route in ("default", "spare"):
        for field in FIELDS:
            assert f"routes.{route}.{field}" in refusal(set_price(cfg_dir, "-1", field, route))
            set_price(cfg_dir, "2", field, route)
    load_config(cfg_dir)


# --- the refusal names route and field, never the value ----------------------------------------------------


@pytest.mark.parametrize("field", FIELDS)
def test_h2_negative_price_text_has_no_value(cfg_dir, field):
    text = refusal(set_price(cfg_dir, "-123.456789", field))
    assert f"routes.default.{field}" in text
    assert "a price must not be negative" in text
    assert "123" not in text
    assert "456789" not in text


@pytest.mark.parametrize(
    "value", ["7654321.5", "0.7654321", "7654321E+20", "-7654321", 7654321.5, "7654321x"]
)
def test_h2_no_refused_price_is_echoed(cfg_dir, value):
    text = refusal(set_price(cfg_dir, value))
    assert f"routes.default.{IN}" in text
    assert "7654321" not in text


def test_h2_zero_refusal_names_the_route_and_no_price(cfg_dir):
    real_kind(cfg_dir)
    set_price(cfg_dir, "0.000000", IN)
    text = refusal(set_price(cfg_dir, "7654.321", OUT))
    assert f"routes.default.{IN}: {ZERO_TEXT}" in text
    assert "7654" not in text
    assert "0.000000" not in text
    assert "0.0" not in text


def test_h3_two_routes_with_negative_prices_are_both_named(cfg_dir):
    add_route(cfg_dir, "spare", **{OUT: "-2"})
    text = refusal(set_price(cfg_dir, "-1", IN))
    assert f"routes.default.{IN}" in text
    assert f"routes.spare.{OUT}" in text
    assert text.count("a price must not be negative") == 2


def test_h3_all_zero_fields_in_one_error_sorted_by_route(cfg_dir):
    real_kind(cfg_dir)
    add_route(cfg_dir, "zeta", **{IN: "0"})
    add_route(cfg_dir, "alpha", **{IN: "0", OUT: "0.00"})
    set_price(cfg_dir, "0", OUT)
    text = refusal(cfg_dir)
    want = [
        f"routes.alpha.{IN}: {ZERO_TEXT}",
        f"routes.alpha.{OUT}: {ZERO_TEXT}",
        f"routes.default.{OUT}: {ZERO_TEXT}",
        f"routes.zeta.{IN}: {ZERO_TEXT}",
    ]
    assert ", ".join(want) in text
    assert text.count(ZERO_TEXT) == 4


def test_i4_zero_and_date_refusals_share_one_error_with_the_environment_refusals(tmp_path, today):
    def fn(d):
        d.pop("prices_as_of")
        d["routes"]["default"][OUT] = "0"
        d["allow_insecure_loopback"] = True

    text = refusal(edit(pilot_cfg(tmp_path), fn))
    assert "environment pilot: refused:" in text
    assert "allow_insecure_loopback" in text
    assert f"routes.default.{OUT}: {ZERO_TEXT}" in text
    assert "prices_as_of is required in pilot and prod" in text


# --- config_hash -------------------------------------------------------------------------------------------


def test_e8_config_hash_of_the_fixture_agent_is_the_value_before_the_change(cfg_dir):
    assert load_registry(load_config(cfg_dir)).config_hash("test-agent") == FIXTURE_HASH


def test_e8_config_hash_is_the_same_with_and_without_the_date(cfg_dir, tmp_path, today):
    assert load_registry(load_config(cfg_dir)).config_hash("test-agent") == FIXTURE_HASH
    for day in ("2026-11-01", "2026-11-20", "2020-01-01"):
        edit(cfg_dir, lambda d, day=day: d.__setitem__("prices_as_of", day))
        cfg = load_config(cfg_dir)
        assert cfg.prices_as_of == date.fromisoformat(day)
        assert load_registry(cfg).config_hash("test-agent") == FIXTURE_HASH

    pilot = pilot_cfg(tmp_path)
    first = load_registry(load_config(pilot)).config_hash("ito-agent")
    edit(pilot, lambda d: d.__setitem__("prices_as_of", "2025-05-05"))
    assert load_registry(load_config(pilot)).config_hash("ito-agent") == first
