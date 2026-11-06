"""P4d-a2-i [PL17]: a model route's price is checked when the configuration loads."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from hadavin_sdk import defaults
from hadavin_sdk.config import Route

D = Decimal


def _route(**kw):
    base = {
        "model_id": "m",
        "input_usd_per_mtok": D(1),
        "output_usd_per_mtok": D(1),
        "max_tokens": 10,
    }
    return Route(**{**base, **kw})


@pytest.mark.parametrize("field", ["input_usd_per_mtok", "output_usd_per_mtok"])
@pytest.mark.parametrize("bad", ["NaN", "sNaN", "Infinity", "-Infinity"])
def test_non_finite_prices_are_refused_regression_pin_on_pydantic(field, bad):
    with pytest.raises(ValidationError):
        _route(**{field: D(bad)})


@pytest.mark.parametrize("field", ["input_usd_per_mtok", "output_usd_per_mtok"])
@pytest.mark.parametrize("bad", ["-1", "-0", "1E+30", "1000000.000001", "0.0000001"])
def test_negative_over_bound_and_seven_decimal_prices_are_refused(field, bad):
    with pytest.raises(ValidationError):
        _route(**{field: D(bad)})


@pytest.mark.parametrize("field", ["input_usd_per_mtok", "output_usd_per_mtok"])
@pytest.mark.parametrize("ok", ["1000000", "0", "0.000001", "0.0750000", "999999.999999"])
def test_good_prices_are_accepted(field, ok):
    assert _route(**{field: D(ok)}).model_dump()[field] == D(ok)


def test_the_bound_is_one_named_constant():
    assert getattr(defaults, "MAX_ROUTE_PRICE_USD_PER_MTOK", None) == 10**6


@pytest.mark.parametrize("bad", ["-1", "1E+30", "0.0000001"])
def test_a_bad_price_fails_through_load_config(cfg_dir, bad):
    import yaml

    from hadavin_sdk.config import ConfigError, load_config

    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["routes"]["default"]["input_usd_per_mtok"] = bad
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(cfg_dir)
