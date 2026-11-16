"""PROOF-ONLY extra tests (scratch copy, not applied): kill the C-01 survivors."""

import pytest
import yaml

from hadavin_sdk.config import ConfigError, load_config

LIVE_LLM = {"kind": "anthropic", "api_key_secret_name": "a", "platform": "api"}


def _load(cfg_dir, *, llm=None, extra_routes=None, **route):
    path = cfg_dir / "config.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if llm is not None:
        raw["backends"]["llm"] = llm
    raw["routes"]["default"].update(route)
    raw["routes"].update(extra_routes or {})
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return load_config(cfg_dir)


def test_max_tokens_one_loads(cfg_dir):
    assert _load(cfg_dir, max_tokens=1).routes["default"].max_tokens == 1


def test_the_ceiling_is_exactly_200_000(cfg_dir):
    assert _load(cfg_dir, max_tokens=200_000).routes["default"].max_tokens == 200_000
    with pytest.raises(ConfigError):
        _load(cfg_dir, max_tokens=200_001)
    with pytest.raises(ConfigError):
        _load(cfg_dir, max_tokens=2_000_000)


def test_every_route_is_checked_and_the_message_names_the_free_one(cfg_dir):
    zcheap = {
        "model_id": "m2",
        "input_usd_per_mtok": "0",
        "output_usd_per_mtok": "3",
        "max_tokens": 1024,
    }
    with pytest.raises(ConfigError, match=r"zero or negative price: \['zcheap'\]"):
        _load(cfg_dir, llm=LIVE_LLM, extra_routes={"zcheap": zcheap})
