"""Round 16 of Q8a-1: the fixes of this round, each with a test that fails on the code of round 15 (head c098aacf). Every
test is free of `conftest` fixtures so that the mutant runner can use it. A marker that must never be shown is built
from parts so that it is no secret-shaped literal."""

from __future__ import annotations

import sys

import pytest

from tests.k5_support import TOOL, k5_cfg


def _marker(tag: str) -> str:
    return "zq-b16-" + tag + "-" + "Wm4"


# ---- Issue 1: `check-config` never runs a tool module ---------------------------------------------------------------------

_SIDE_EFFECT_MODULE = """\
import os

with open(os.environ["B16_TOOL_MARKER"], "w", encoding="utf-8") as _f:
    _f.write("the tool module ran")

READ_OPERATIONS = {"bundle.read": ("GET", r"/.*")}


def read_logs(args, ctx):
    return "x"
"""


def _config_naming_a_tool_module(tmp_path, monkeypatch):
    mods = tmp_path / "mods"
    mods.mkdir()
    (mods / "zzb16_tool.py").write_text(_SIDE_EFFECT_MODULE, encoding="utf-8")
    marker = tmp_path / "ran.txt"
    monkeypatch.setenv("B16_TOOL_MARKER", str(marker))
    monkeypatch.syspath_prepend(str(mods))
    monkeypatch.delitem(sys.modules, "zzb16_tool", raising=False)
    cfg = k5_cfg(
        tmp_path / "cfg",
        tools=[{**TOOL, "function": "zzb16_tool:read_logs"}],
        config={"tool_modules": ["zzb16_tool"]},
    )
    return cfg, marker


def test_check_config_does_not_run_a_tool_module(tmp_path, monkeypatch, capsys):
    from hadavin_sdk import cli
    from hadavin_sdk.config import load_config
    from hadavin_sdk.registry import load_registry

    cfg, marker = _config_naming_a_tool_module(tmp_path, monkeypatch)
    # control: the way `tick` loads the registry DOES run the module, so this probe can see a side effect
    load_registry(load_config(cfg))
    assert marker.exists(), "control: loading the registry must run the tool module (the probe is blind)"
    marker.unlink()
    monkeypatch.delitem(sys.modules, "zzb16_tool", raising=False)

    code = cli.main(["--config", str(cfg), "check-config"])
    seen = capsys.readouterr()
    assert code == 0, seen.err
    assert not marker.exists(), "check-config ran a tool module (client code)"
    assert "zzb16_tool" not in sys.modules, "check-config imported a tool module"


def test_check_config_says_what_it_did_not_check(tmp_path, monkeypatch, capsys):
    from hadavin_sdk import cli

    cfg, _ = _config_naming_a_tool_module(tmp_path, monkeypatch)
    assert cli.main(["--config", str(cfg), "check-config"]) == 0
    out = capsys.readouterr().out
    assert "Not checked" in out and "tool module code is not run" in out, (
        "check-config must say what it did not check"
    )


def test_check_config_still_refuses_a_tool_with_no_module_in_tool_modules(
    tmp_path, monkeypatch, capsys
):
    from hadavin_sdk import cli

    cfg, marker = _config_naming_a_tool_module(tmp_path, monkeypatch)
    cfg2 = k5_cfg(
        tmp_path / "cfg2",
        tools=[{**TOOL, "function": "zzb16_tool:read_logs"}],
        config={"tool_modules": []},
    )
    assert cli.main(["--config", str(cfg2), "check-config"]) == 2
    assert "outside tool_modules" in capsys.readouterr().err
    assert not marker.exists()


def test_check_config_exit_codes_are_those_of_main_and_tick(tmp_path, monkeypatch, capsys):
    from hadavin_sdk import cli

    def boom(*a, **k):
        raise RuntimeError(_marker("exit"))

    from tests.conftest import make_cfg

    monkeypatch.setattr(cli, "load_registry", boom)
    assert cli.main(["--config", str(make_cfg(tmp_path)), "check-config"]) == 3
    seen = capsys.readouterr()
    assert "RuntimeError" in seen.err and _marker("exit") not in seen.err + seen.out
