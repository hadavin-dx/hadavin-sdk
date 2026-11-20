"""One shared `qualified_agents` helper (core-a request 004): lenient list, strict Runtime, cli tick line."""

from types import SimpleNamespace

import pytest

from hadavin_sdk import cli
from hadavin_sdk.runtime import agent_loop
from hadavin_sdk.runtime.agent_loop import Unqualified, qualified_agents
from tests.conftest import qualify


def _reg(*ids):
    return SimpleNamespace(agents={i: object() for i in ids})


def _patch(monkeypatch, bad=(), boom=()):
    def fake(registry, agent_id):
        if agent_id in boom:
            raise RuntimeError("secret detail /etc/passwd")
        if agent_id in bad:
            raise Unqualified(agent_id)

    monkeypatch.setattr(agent_loop, "assert_qualified", fake)


def test_all_qualified(monkeypatch):
    _patch(monkeypatch)
    seen = []
    assert qualified_agents(_reg("a", "b", "c"), seen.append) == ["a", "b", "c"]
    assert seen == []


def test_some_unqualified_callback_once_each_in_order(monkeypatch):
    _patch(monkeypatch, bad={"b", "d"})
    seen = []
    assert qualified_agents(_reg("a", "b", "c", "d"), seen.append) == ["a", "c"]
    assert seen == ["b", "d"]


def test_callback_none(monkeypatch):
    _patch(monkeypatch, bad={"b"})
    assert qualified_agents(_reg("a", "b")) == ["a"]


def test_empty_registry(monkeypatch):
    _patch(monkeypatch)
    seen = []
    assert qualified_agents(_reg(), seen.append) == []
    assert seen == []


def test_exception_is_unqualified_and_text_never_leaks(monkeypatch):
    _patch(monkeypatch, boom={"b"})
    seen = []
    assert qualified_agents(_reg("a", "b", "c"), seen.append) == ["a", "c"]
    assert seen == ["b"]


def test_runtime_stays_strict(monkeypatch):
    _patch(monkeypatch, bad={"b", "c"})
    with pytest.raises(Unqualified) as ei:
        agent_loop.Runtime(_reg("a", "b", "c"), None, None, None, None, None, ["a", "b", "c"])
    assert ei.value.args == ("b",)


def test_cli_tick_still_prints_its_line(cfg_dir, monkeypatch, capsys):
    from hadavin_sdk.config import load_config
    from hadavin_sdk.registry import load_registry

    qualify(load_registry(load_config(cfg_dir)))
    built = []

    def fake_build(_cfg, agents):
        built.append(list(agents))
        raise RuntimeError("stop here")  # start-up failure: exit 2

    monkeypatch.setattr("hadavin_sdk.app.build", fake_build)
    assert cli.main(["--config", str(cfg_dir), "tick"]) == 2
    assert built == [["test-agent"]]
    assert "is not qualified" not in capsys.readouterr().err

    def never(registry, agent_id):
        raise Unqualified(agent_id)

    monkeypatch.setattr(agent_loop, "assert_qualified", never)
    built.clear()
    assert cli.main(["--config", str(cfg_dir), "tick"]) == 2
    assert built == [[]]
    assert "tick: test-agent is not qualified; its new runs are refused" in capsys.readouterr().err
