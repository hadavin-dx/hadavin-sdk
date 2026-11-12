"""Round 13 of Q8a-1: the two fixes that need the shared fixtures of `conftest.py` (a live fixture system). They are not
run by the mutation tool, which runs without `conftest.py`; the same fixes have their mutants in `test_q8a1_b13_fixes.py`
where a fixture-free test exists."""

from __future__ import annotations

from types import SimpleNamespace

MARKER = "zq-b13-" + "Wm4" + "-text"


def test_an_executor_answer_gives_the_error_code_through_status_text(live_cfg_dir, fake_system):
    """A status is an int here (a text one fails at the comparison, with a TypeError that is class-only); the code of the
    refusal is built by `status_text`. This test passes on round 12 too: it pins the form, it is not a fail-first test."""
    from hadavin_sdk.actions.executor import Executor
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.config import load_config
    from hadavin_sdk.registry import load_registry
    from tests.test_executor import _approved, _plan

    reg = load_registry(load_config(live_cfg_dir))
    ex = Executor(reg, FakeSecretProvider({"fixture-token": fake_system.token}), timeout_s=0.5)
    ex._caller = lambda contract, heartbeat: lambda *a, **k: (418, {})
    plan = _plan()
    assert ex.execute(plan, *_approved(plan)).error_code == "http_418"


def test_the_gate_line_does_not_print_an_agent_id_that_the_registry_does_not_hold(
    live_cfg_dir, fake_system, capsys, monkeypatch
):
    from hadavin_sdk import cli

    run = SimpleNamespace(
        agent_id=MARKER, n=1, k=1, passed=1, pass_rate=1.0, threshold=1.0, green=True,
        pass_k=1, abstain_rate=0.0, upper_error_bound=0.5,
    )  # fmt: skip
    monkeypatch.setattr(cli.evals, "gate", lambda *a, **k: run)
    assert cli.main(["--config", str(live_cfg_dir), "gate", "test-agent"]) == 0
    out = capsys.readouterr().out
    assert MARKER not in out and "GREEN" in out
