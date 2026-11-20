"""Step C, the price rule pinned from both sides in each test: the fake llm kind in demo may hold a zero price AND
the same zero is refused as soon as the kind is real or the stage is live. Each test fails if the rule is removed
(the refused side loads) or reversed (the allowed side is refused), so none can pass either way.

Written by a different agent than the builder of the source."""

from __future__ import annotations

from datetime import date

import pytest

from hadavin_sdk import config as config_mod
from hadavin_sdk.config import load_config
from tests.test_price_constraint import (
    FIELDS,
    ZERO_TEXT,
    add_route,
    real_kind,
    refusal,
    set_price,
)


@pytest.mark.parametrize("field", FIELDS)
def test_m1_zero_is_allowed_for_fake_in_demo_and_refused_for_a_real_kind(cfg_dir, field):
    set_price(cfg_dir, "0", field)
    cfg = load_config(cfg_dir)  # reversed rule: refused here
    assert cfg.backends.llm.kind == "fake"
    assert getattr(cfg.routes["default"], field) == 0
    assert config_mod._price_refusals(cfg) == []
    text = refusal(real_kind(cfg_dir))  # removed rule: loads here
    assert f"routes.default.{field}: {ZERO_TEXT}" in text


@pytest.mark.parametrize("field", FIELDS)
def test_m2_the_helper_names_the_zero_for_real_and_live_and_stays_silent_for_fake_demo(
    cfg_dir, field
):
    set_price(cfg_dir, "0", field)
    fake_demo = load_config(cfg_dir)
    want = [f"routes.default.{field}: {ZERO_TEXT}"]
    assert config_mod._price_refusals(fake_demo) == []
    real = fake_demo.model_copy(
        update={
            "backends": fake_demo.backends.model_copy(
                update={"llm": fake_demo.backends.llm.model_copy(update={"kind": "openai_compat"})}
            )
        }
    )
    assert config_mod._price_refusals(real) == want
    for env in ("pilot", "prod"):
        live = fake_demo.model_copy(update={"environment": env, "prices_as_of": date(2020, 1, 1)})
        assert config_mod._price_refusals(live) == want, env


def test_m3_only_the_zero_fields_are_named_and_a_positive_price_is_never_refused(cfg_dir):
    """Reversed to `!= 0` names the priced field; removed names nothing."""
    add_route(cfg_dir, "spare")  # both fields priced
    set_price(cfg_dir, "0", FIELDS[0], route="default")
    real_kind(cfg_dir)
    text = refusal(cfg_dir)
    assert f"routes.default.{FIELDS[0]}: {ZERO_TEXT}" in text
    assert text.count(ZERO_TEXT) == 1
    assert "routes.spare" not in text
    assert f"routes.default.{FIELDS[1]}" not in text


@pytest.mark.parametrize("value", ["-1", "-0.000001"])
@pytest.mark.parametrize("field", FIELDS)
def test_m4_a_negative_price_is_refused_for_fake_in_demo_while_zero_loads(cfg_dir, value, field):
    assert getattr(load_config(set_price(cfg_dir, "0", field)).routes["default"], field) == 0
    assert "a price must not be negative" in refusal(set_price(cfg_dir, value, field))
    assert getattr(load_config(set_price(cfg_dir, "0.000001", field)).routes["default"], field) > 0
