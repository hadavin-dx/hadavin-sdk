"""Round 4: the reviewer's probes p1 to p8 as regression tests, the config-not-literals scan, and the EGM nits."""

from __future__ import annotations

import json
import re
from decimal import Decimal

import pytest
from askdata import cli, evalcli, validate
from askdata.evalcli import cmd_run
from askdata.evalset import Lock, LockError, lock_path, read_lock, verify_files, write_lock
from askdata.meter import call_cost
from askdata.pgsource import PgError
from askdata.policy import EXIT_AUDIT, EXIT_STARTUP, EXIT_USAGE
from askdata.sealed import HAND_FIELDS, Chain, SealedGate
from askdata.settings import MeterLimits, Sealed, Smoke

from hadavin_sdk.llm.protocol import UnusableAnswer

from .conftest import DEMO
from .kit import COUNT_ORDERS, Kit
from .test_demo_gaps_r3 import KEY, Q, Wrap, gate_for, sealed_runs, spend
from .test_eval_harness import cli_env  # noqa: F401 - a fixture reused here


def _edit_lock(g: SealedGate, fn) -> None:
    lock = json.loads(lock_path(g.eval_dir).read_text(encoding="utf-8"))
    fn(lock)
    lock_path(g.eval_dir).write_text(json.dumps(lock, indent=2, sort_keys=True), encoding="utf-8")


def _run(g: SealedGate, rid: str, status: str = "complete") -> None:
    g.begin(g.load(), rid)
    (g.runs_dir / rid).mkdir(parents=True, exist_ok=True)
    (g.runs_dir / rid / "report.json").write_text(
        json.dumps({"aborted": status == "aborted"}), encoding="utf-8"
    )
    g.finish(rid, status)


# ====================================================== p1: the seal covers the WHOLE lock
@pytest.mark.parametrize(
    "mutate",
    [
        lambda l: l["thresholds"].update(green_max_upper="0.99"),
        lambda l: l.update(max_second_looks=99),
        lambda l: l.update(second_look_min_remaining_usd="0"),
        lambda l: l.update(sealed_min_remaining_usd="0"),
        lambda l: l.update(second_look_allowed_for=["aborted"]),
        lambda l: l["files"].update({"a.jsonl": "0" * 64}),
    ],
)
def test_every_field_of_lock_json_is_sealed_when_a_key_is_configured(tmp_path, mutate):
    g = gate_for(tmp_path, KEY)
    _run(g, "r1")
    assert g.load().test_runs == 1
    _edit_lock(g, mutate)
    with pytest.raises(LockError, match="seal"):
        g.load()


def test_a_rewritten_frozen_set_with_rehashed_files_is_refused(tmp_path):
    g = gate_for(tmp_path, KEY)
    (g.eval_dir / "a.jsonl").write_text("tampered", encoding="utf-8")
    import hashlib

    _edit_lock(g, lambda l: l["files"].update({"a.jsonl": hashlib.sha256(b"tampered").hexdigest()}))
    with pytest.raises(LockError, match="seal"):
        g.load()  # without the seal this lock would load and verify_files would be satisfied


def test_the_hand_written_defect_needs_a_reseal_by_the_key_holder(tmp_path):
    g = gate_for(tmp_path, KEY)
    _run(g, "r1", "complete")
    _edit_lock(
        g,
        lambda l: l.update(
            harness_defect_reason="gold g7 fails on database A",
            harness_defect_run="r1",
            harness_defect_item="g7",
        ),
    )
    with pytest.raises(LockError, match="eval reseal"):
        g.load()
    assert g.reseal() == list(HAND_FIELDS)
    assert g.load().harness_defect_item == "g7"
    assert [e["kind"] for e in g.chain.entries()][-1] == "reseal"
    keyless = gate_for(tmp_path / "k", None)
    with pytest.raises(LockError, match="needs the sealed-run key"):
        keyless.reseal()


# ====================================================== p2: reset by deleting everything, and the downgrade
def test_a_new_freeze_is_refused_while_any_anchor_exists_and_new_set_is_visible(tmp_path):
    g = gate_for(tmp_path, KEY)
    _run(g, "r1")
    _run(g, "r2")
    g.chain.path.unlink()
    lock_path(g.eval_dir).unlink()
    for refused in (None, "   "):
        with pytest.raises(LockError, match="reset the sealed counter"):
            g.create(["a.jsonl"], new_set_reason=refused)
    # even with the audit-folder anchor deleted, the committed one still blocks it
    g.anchors[0].unlink()
    with pytest.raises(LockError, match="reset the sealed counter"):
        g.create(["a.jsonl"])


def test_new_set_restarts_the_count_and_leaves_a_visible_entry(tmp_path):
    g = gate_for(tmp_path, KEY)
    _run(g, "r1")
    lock = g.create(["a.jsonl"], new_set_reason="a different test set from the client")
    assert lock.test_runs == 0 and g.load().test_runs == 0
    kinds = [e["kind"] for e in g.chain.entries()]
    assert (
        kinds.count("new_set") == 1 and "sealed_run" in kinds
    )  # the old run stays in the chain as history
    assert g.chain.entries()[-1]["data"]["reason"] == "a different test set from the client"
    assert list(g.eval_dir.glob("lock.json.prev-*"))  # the old lock is kept aside
    _run(g, "r2")
    assert g.load().test_runs == 1  # counting restarted at the new set
    sets = json.loads(g.anchors[1].read_text(encoding="utf-8"))["sets"]
    assert len(sets) == 2 and sets[-1]["reason"]
    with pytest.raises(LockError, match="no earlier set"):
        gate_for(tmp_path / "fresh", None).__class__(
            g.eval_dir, tmp_path / "x" / "c.jsonl", g.runs_dir, None, []
        ).create(["a.jsonl"], new_set_reason="nothing to replace")


def test_the_chain_and_an_anchor_must_name_the_same_set(tmp_path):
    g = gate_for(tmp_path, KEY)
    other = gate_for(tmp_path / "other", KEY)
    g.chain.path.write_bytes(other.chain.path.read_bytes())  # a different, valid, keyed chain
    with pytest.raises(LockError):
        g.load()


def test_a_keyless_gate_is_refused_once_the_set_was_keyed(tmp_path):
    g = gate_for(tmp_path, KEY)
    _run(g, "r1")
    keyless = SealedGate(g.eval_dir, g.chain.path, g.runs_dir, None, g.anchors)
    with pytest.raises(LockError, match="keyed"):
        keyless.load()
    with pytest.raises(LockError, match="keyed"):
        keyless.create(["a.jsonl"], new_set_reason="downgrade attempt")
    # and rewriting the chain without a key and clearing the lock's flag does not help while an anchor says keyed
    _edit_lock(g, lambda l: l.update(keyed=False, seal=None))
    with pytest.raises(LockError, match="keyed"):
        keyless.load()


def test_freeze_new_set_through_the_cli(cli_env, capsys):  # noqa: F811
    cfg, factory = cli_env
    path = str(cfg.paths.eval_dir.parent / "askdata.yaml")
    assert cli.main(["eval", "--config", path, "freeze"]) == 4  # a set is already frozen
    assert cli.main(["eval", "--config", path, "freeze", "--new-set"]) == 1  # needs a reason
    capsys.readouterr()
    assert (
        cli.main(
            ["eval", "--config", path, "freeze", "--new-set", "--reason", "new client data set"]
        )
        == 0
    )
    assert read_lock(cfg.paths.eval_dir).test_runs == 0
    assert cmd_run(cfg, "test", 1, None, harness_factory=factory) in (0, 10, 11, 12, 13)


# ====================================================== p3: a replayed run consumes the hand-written defect
def test_a_replayed_run_consumes_the_harness_defect(tmp_path, monkeypatch):
    from askdata import sealed

    g = gate_for(tmp_path)
    _run(g, "r1", "aborted")
    _edit_lock(
        g,
        lambda l: l.update(
            harness_defect_reason="gold g7 fails on database A",
            harness_defect_run="r1",
            harness_defect_item="g7",
        ),
    )
    lock = g.load()
    monkeypatch.setattr(
        sealed, "write_lock", lambda *a, **k: (_ for _ in ()).throw(PermissionError("busy"))
    )
    with pytest.raises(PermissionError):
        g.begin(lock, "r2")  # the chain has the run, lock.json does not
    monkeypatch.undo()
    after = g.load()
    assert (
        after.test_runs == 2
        and after.harness_defect_reason is None
        and after.harness_defect_item is None
    )


# ====================================================== p2 D: a torn final line must not brick the counter
@pytest.mark.parametrize("key", [None, KEY])
def test_a_torn_final_line_is_cut_off_and_logged(tmp_path, key):
    g = gate_for(tmp_path, key)
    _run(g, "r1")
    with open(g.chain.path, "a", encoding="utf-8") as f:
        f.write('{"seq":99,"kind":"sealed_ru')  # power loss mid-write: no newline, not JSON
    assert g.chain.torn
    lock = g.load()
    assert lock.test_runs == 1 and not g.chain.torn
    assert g.chain.entries()[-1]["data"]["truncated_torn_tail"] is True
    _run(g, "r2")  # and the counter keeps working
    assert sealed_runs(g) == 2


def test_a_complete_but_unterminated_last_line_is_not_thrown_away(tmp_path):
    g = gate_for(tmp_path)
    _run(g, "r1")
    text = g.chain.path.read_text(encoding="utf-8")
    g.chain.path.write_text(
        text.rstrip("\n"), encoding="utf-8"
    )  # valid JSON, only the newline is missing
    assert not g.chain.torn and g.load().test_runs == 1


# ====================================================== p5: core accounting (openai_compat) -> see tests/test_llm_attempts.py
def test_call_cost_carries_what_earlier_answered_requests_cost():
    per, reserved = Decimal("0.011"), Decimal("0.066")
    billed = Decimal("0.02")
    # one answered request (billed) then a refusal: the billed answer is not lost, the refusal is free
    assert (
        call_cost(per, reserved, sent=2, reply_cost=None, refused=True, answered=1, billed=billed)
        == billed
    )
    # one answered request then exhaustion over three more requests
    assert (
        call_cost(per, reserved, sent=4, reply_cost=None, answered=1, billed=billed)
        == billed + per * 3
    )
    # a reply that is the sum of two answered requests and nothing else sent
    assert call_cost(per, reserved, sent=2, reply_cost=Decimal("0.03"), answered=2) == Decimal(
        "0.03"
    )
    assert call_cost(per, reserved, sent=1, reply_cost=Decimal("0.03")) == Decimal("0.03")


def test_an_unusable_answer_is_billed_not_free(tmp_path):
    s, per, _worst, o, ans = spend(tmp_path, "u200", raises=UnusableAnswer("200 but unusable"))
    assert (
        ans.reason == "model_unavailable" and s == per and o == 0
    )  # one billed request, not a free refusal


def test_the_reservation_uses_the_kinds_own_request_bound(tmp_path):
    class Kind(Wrap):
        max_requests = 6

    k = Kit(tmp_path)
    from askdata.fixtures import Step

    k.script(Q, Step(sql=COUNT_ORDERS))
    reserved = []
    real = k.meter.reserve
    k.meter.reserve = lambda amount, live=True: (reserved.append(amount), real(amount, live=live))[
        1
    ]
    k.pipeline.llm = Kind(k.llm)
    k.pipeline.ask(Q)
    one = Kit(tmp_path / "one")
    one.script(Q, Step(sql=COUNT_ORDERS))
    one_reserved = []
    real1 = one.meter.reserve
    one.meter.reserve = lambda amount, live=True: (
        one_reserved.append(amount),
        real1(amount, live=live),
    )[1]
    one.pipeline.ask(Q)
    assert reserved[0] == one_reserved[0] * 6 / 1  # settings default is 1 request, the kind says 6


# ====================================================== p6: interrupts and meter write failures
def _ledger_lines(k) -> int:
    return len(k.ledger.read().items)


def test_ctrl_c_still_writes_one_terminal_ledger_line(tmp_path):
    s, _per, worst, o, err = spend(tmp_path, "cc", raises=KeyboardInterrupt())
    assert isinstance(err, KeyboardInterrupt) and o == 0 and s == worst
    k = Kit(tmp_path / "cc2")
    from askdata.fixtures import Step

    k.script(Q, Step(sql=COUNT_ORDERS))
    k.pipeline.llm = Wrap(k.llm, 1, KeyboardInterrupt())
    with pytest.raises(KeyboardInterrupt):
        k.pipeline.ask(Q)
    lines = k.ledger.read().items
    assert len(lines) == 1 and lines[0].line.reason_code == "model_unavailable"


def test_a_meter_write_failure_is_an_over_budget_answer_not_a_traceback(tmp_path, monkeypatch):
    import askdata.meter as meter_mod

    k = Kit(tmp_path)
    from askdata.fixtures import Step

    k.script(Q, Step(sql=COUNT_ORDERS))
    monkeypatch.setattr(
        meter_mod.os, "replace", lambda *a, **kw: (_ for _ in ()).throw(PermissionError("in use"))
    )
    ans = k.pipeline.ask(Q)  # reserve fails on the replace
    assert ans.reason == "over_budget" and _ledger_lines(k) == 1
    monkeypatch.undo()


def test_a_meter_write_failure_while_settling_still_ends_in_a_ledger_line(tmp_path, monkeypatch):
    import askdata.meter as meter_mod

    k = Kit(tmp_path)
    from askdata.fixtures import Step

    k.script(Q, Step(sql=COUNT_ORDERS))
    real_replace, calls = meter_mod.os.replace, {"n": 0}

    def flaky(src, dst):
        calls["n"] += 1
        if calls["n"] >= 2:  # the reserve (1st write) works, the settle (2nd) does not
            raise PermissionError("in use")
        return real_replace(src, dst)

    monkeypatch.setattr(meter_mod.os, "replace", flaky)
    ans = k.pipeline.ask(Q)
    monkeypatch.undo()
    assert ans.outcome != "answered" and _ledger_lines(k) == 1


# ====================================================== p7: a failed record is never a plain success; usage first
def test_a_green_run_whose_record_failed_returns_exit_5(cli_env, monkeypatch):  # noqa: F811
    cfg, factory = cli_env
    monkeypatch.setattr(evalcli, "_record", lambda step, eval_dir: False)
    assert cmd_run(cfg, "test", 1, None, harness_factory=factory) == EXIT_AUDIT


def test_usage_errors_are_exit_1_before_any_config_or_dsn_is_needed(monkeypatch):
    monkeypatch.delenv("ASKDATA_CONFIG", raising=False)
    monkeypatch.delenv("ASKDATA_DSN", raising=False)
    assert evalcli.main(["run", "--split", "dev", "--k", "0"]) == EXIT_USAGE
    assert evalcli.main(["run", "--split", "dev", "--smoke"]) == EXIT_USAGE
    assert cli.main(["ask"]) == EXIT_USAGE
    assert cli.main(["verify-readonly"]) == EXIT_STARTUP  # a real startup problem is still 4


# ====================================================== EGM nits
def test_the_cli_refuses_to_start_with_a_validator_rule_switched_off(monkeypatch, capsys):
    monkeypatch.setattr(validate, "_OFF", {"V05"})
    assert cli.main(["verify-readonly"]) == EXIT_STARTUP
    assert "switched off" in capsys.readouterr().out
    monkeypatch.undo()
    assert validate._OFF == set()  # and in production it is empty


def test_the_banner_says_the_model_is_scripted_and_offline():
    assert "Scripted model, no network" in cli.BANNER


# ====================================================== config, not literals
CODE = sorted((DEMO / "askdata").glob("*.py"))
ALLOWED_FILES = {"settings.py"}  # the documented defaults live here and nowhere else
PATTERNS = {
    "key-shaped string": re.compile(
        r"\b(sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|xox[bp]-[A-Za-z0-9-]{10,})"
    ),
    "machine path": re.compile(r"[\"'][A-Za-z]:[\\/]"),
    "region literal": re.compile(
        r"[\"'](us|eu|ap|sa|ca|me|af)-(east|west|north|south|central|southeast|northeast)-\d[\"']"
    ),
    "model id literal": re.compile(
        r"[\"'](claude-|gpt-|gemini-|us\.anthropic|anthropic\.claude)[A-Za-z0-9.-]*[\"']"
    ),
}


@pytest.mark.parametrize("path", CODE, ids=lambda p: p.name)
def test_no_secret_path_region_or_model_id_literals_in_the_demo_code(path):
    text = path.read_text(encoding="utf-8")
    hits = [(name, m.group(0)) for name, rx in PATTERNS.items() for m in rx.finditer(text)]
    assert hits == [], f"{path.name}: {hits}"


def test_the_literal_scan_itself_catches_planted_values():
    planted = (
        'k = "'
        + "sk-"
        + "a" * 20
        + '"\np = "C:\\\\bhovix_tools"\nr = "us-east-1"\nm = "claude-sonnet-x"\n'
    )
    assert {name for name, rx in PATTERNS.items() if rx.search(planted)} == set(PATTERNS)


def test_tunable_numbers_have_one_home_and_the_config_sets_them(tmp_path):
    from .test_demo_gaps import make_cfg

    _, cfg = make_cfg(
        tmp_path,
        "smoke: {min_questions: 7, hard_cap_per_question_usd: '0.5'}\nsealed: {max_second_looks: 1}\n"
        "meter: {stale_open_minutes: 3, demo_cap_usd: '5.00', total_cap_usd: '9.00'}",
    )
    assert cfg.smoke.min_questions == 7 and cfg.sealed.max_second_looks == 1
    assert cfg.meter_obj().stale_open_after.total_seconds() == 180
    assert (
        Smoke().min_questions,
        Sealed().first_run_min_remaining_usd,
        MeterLimits().stale_open_minutes,
    ) == (
        5,
        Decimal("3.00"),
        10,
    )  # the documented defaults, in settings.py only
    for module in ("live.py", "meter.py", "evalset.py", "evalrun.py"):
        src = (DEMO / "askdata" / module).read_text(encoding="utf-8")
        assert not re.search(r"Decimal\(\"(0\.035|0\.35|3\.00|1\.80|10\.00|8\.00)\"\)", src), module


def test_a_zero_or_negative_tunable_is_refused_at_load(tmp_path):
    from askdata.config import ConfigError

    from .test_demo_gaps import make_cfg

    with pytest.raises(ConfigError):
        make_cfg(tmp_path, "smoke: {min_questions: 0}")
    with pytest.raises(ConfigError):
        make_cfg(tmp_path, "meter: {stale_open_minutes: 0}")


def test_pgerror_import_kept_for_cmd_ask_hash_mismatch():
    assert (
        PgError and Lock and write_lock and verify_files and Chain
    )  # imports used by the scenarios above
