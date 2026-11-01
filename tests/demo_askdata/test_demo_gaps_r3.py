"""Round 3: the CLASS fixes behind the independent reviews of PR 43, each with crash-injection, concurrency or
property-style tests.

Classes: (A) a counter/guard in a plain editable file -> HMAC-keyed hash chain + write-ahead replay (sealed.py);
(B) state written before the work and cleared only on the happy path -> derived status, replay, `finally`;
(C) spend recorded from the last attempt only / a reservation nobody closes -> `meter.call_cost` + open records;
(D) claims of tamper-evidence the code does not have -> wording and tests that state the limit.
"""

from __future__ import annotations

import json
import random
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from askdata import cli, evalcli, evalrun, live, sealed
from askdata.config import ConfigError
from askdata.evalcli import cmd_run
from askdata.evalset import Lock, LockError, lock_guard, lock_path, read_lock, write_lock
from askdata.fixtures import Step
from askdata.meter import Meter, call_cost
from askdata.pgsource import PgError
from askdata.pipeline import Settings
from askdata.policy import EXIT_AUDIT, EXIT_FAILED, EXIT_OK, EXIT_REFUSED, EXIT_STARTUP, EXIT_USAGE
from askdata.sealed import Chain, SealedGate, key_from
from askdata.settings import MeterLimits

from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.llm.protocol import ProviderError, ProviderExhausted
from hadavin_sdk.models import Reply

from .kit import COUNT_ORDERS, Kit
from .test_demo_gaps import make_cfg
from .test_eval_harness import cli_env  # noqa: F401 - a fixture reused here

STALE_OPEN_AFTER = timedelta(minutes=MeterLimits().stale_open_minutes)
KEY = ("k3y-" * 6).encode()
Q = "How many orders are there"


# ------------------------------------------------------------------------------------------ helpers
def gate_for(tmp_path: Path, key: bytes | None = None) -> SealedGate:
    ev = tmp_path / "ev"
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "a.jsonl").write_text("x" + chr(10), encoding="utf-8")
    anchors = [tmp_path / "audit" / "sealed-anchor.json", tmp_path / "committed-anchor.json"]
    g = SealedGate(ev, tmp_path / "audit" / "chain.jsonl", tmp_path / "runs", key, anchors)
    g.create(["a.jsonl"])
    return g


def sealed_runs(g: SealedGate) -> int:
    return sum(1 for e in g.chain.entries() if e["kind"] == "sealed_run")


# ============================================================ (A) tamper evidence of the sealed-run counter
@pytest.mark.parametrize("key", [None, KEY])
def test_a_single_edit_of_the_chain_or_the_lock_is_detected(tmp_path, key):
    g = gate_for(tmp_path, key)
    g.begin(g.load(), "r1")
    g.finish("r1", "complete")
    g.begin(g.load(), "r2")
    original = g.chain.path.read_text(encoding="utf-8")
    lines = original.splitlines()
    # 1. delete the LAST line only: lock.json names a chain position that is gone
    g.chain.path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    with pytest.raises(LockError):
        g.load()
    # 2. delete a MIDDLE line: the chain breaks
    g.chain.path.write_text("\n".join([lines[0], *lines[2:]]) + "\n", encoding="utf-8")
    with pytest.raises(LockError, match="broken"):
        g.load()
    # 3. edit a line's data
    bad = json.loads(lines[0])
    bad["data"]["run_id"] = "other"
    g.chain.path.write_text("\n".join([json.dumps(bad), *lines[1:]]) + "\n", encoding="utf-8")
    with pytest.raises(LockError, match="broken"):
        g.load()
    # 4. put the chain back and edit only lock.json's counter
    g.chain.path.write_text(original, encoding="utf-8")
    assert g.load().test_runs == 2
    write_lock(g.eval_dir, read_lock(g.eval_dir).model_copy(update={"test_runs": 0}))
    with pytest.raises(LockError):
        g.load()


def test_with_a_key_even_a_consistent_rewrite_of_both_files_is_refused(tmp_path):
    g = gate_for(tmp_path, KEY)
    g.begin(g.load(), "r1")
    # the attacker removes the run from the chain AND resets lock.json completely (no key, so no valid seal)
    g.chain.path.unlink()
    write_lock(g.eval_dir, Lock(files=read_lock(g.eval_dir).files, test_runs=0))
    with pytest.raises(LockError, match="seal"):
        g.load()
    # re-hashing the chain with the WRONG key (the best an attacker without the key can do) is refused too
    forged = SealedGate(g.eval_dir, tmp_path / "forged.jsonl", g.runs_dir, b"x" * 32)
    forged.chain.append("sealed_run", {"run_id": "r1", "n": 1})
    with pytest.raises(LockError, match="broken"):
        Chain(forged.chain.path, KEY).entries()


def test_without_a_key_deleting_everything_resets_the_counter_and_the_docs_say_so(tmp_path):
    """The limit, pinned: with no key and no committed anchor, a writer of every file can start over."""
    g = gate_for(tmp_path)
    g.begin(g.load(), "r1")
    g.chain.path.unlink()
    lock_path(g.eval_dir).unlink()
    with pytest.raises(
        LockError, match="already exists"
    ):  # the committed anchor still blocks a plain re-freeze
        g.create(["a.jsonl"])
    for a in g.anchors:
        a.unlink(missing_ok=True)
    assert g.create(["a.jsonl"]).test_runs == 0 and g.load().test_runs == 0  # reset succeeded
    assert "NOT keyed" in (Path(evalcli.__file__).read_text(encoding="utf-8"))
    assert "tamper-resistant only by git history" in (
        Path(evalcli.__file__).parents[1] / "README.md"
    ).read_text(encoding="utf-8")


def test_dropping_the_audit_index_line_changes_nothing_because_the_counter_is_not_there(cli_env):  # noqa: F811
    cfg, factory = cli_env
    cmd_run(cfg, "test", 1, None, harness_factory=factory)
    index = cfg.paths.audit_dir / "index.jsonl"
    if index.exists():
        index.write_text("", encoding="utf-8")  # the reviewer's probe: wipe the audit index
    write_lock(
        cfg.paths.eval_dir, read_lock(cfg.paths.eval_dir).model_copy(update={"test_runs": 0})
    )
    assert cmd_run(cfg, "test", 1, None, harness_factory=factory) == 14


# ============================================================ (B) crash injection: write-ahead and replay
def test_crash_between_the_chain_and_the_lock_is_replayed_not_stuck(cli_env, monkeypatch, capsys):  # noqa: F811
    cfg, factory = cli_env
    real = sealed.write_lock
    monkeypatch.setattr(
        sealed, "write_lock", lambda *a, **k: (_ for _ in ()).throw(PermissionError("busy"))
    )
    assert (
        cmd_run(cfg, "test", 1, None, harness_factory=factory) == EXIT_AUDIT
    )  # died after the chain append
    monkeypatch.setattr(sealed, "write_lock", real)
    assert read_lock(cfg.paths.eval_dir).test_runs == 0  # the lock is behind...
    capsys.readouterr()
    assert (
        cli.main(["eval", "--config", str(cfg.paths.eval_dir.parent / "askdata.yaml"), "reconcile"])
        == 0
    )
    assert "0 -> 1" in capsys.readouterr().out
    assert (
        read_lock(cfg.paths.eval_dir).test_runs == 1
    )  # ...and rolled forward, audited by a chain entry
    kinds = [e["kind"] for e in Chain(cfg.paths.audit_dir / "sealed-chain.jsonl").entries()]
    assert kinds == ["genesis", "sealed_run", "reconcile"]
    assert (
        cmd_run(cfg, "test", 1, None, harness_factory=factory) == 14
    )  # the run was counted: no free second pass


def test_a_crash_before_the_next_command_also_recovers_without_reconcile(cli_env, monkeypatch):  # noqa: F811
    cfg, factory = cli_env
    monkeypatch.setattr(
        sealed, "write_lock", lambda *a, **k: (_ for _ in ()).throw(OSError("disk"))
    )
    cmd_run(cfg, "test", 1, None, harness_factory=factory)
    monkeypatch.undo()
    with lock_guard(cfg.paths.eval_dir):
        assert evalcli._gate(cfg).load().test_runs == 1


def _results_written_then(cfg, factory, monkeypatch, how):
    """Run a sealed run, making the process 'die' right after the results were written."""
    if how == "render":
        monkeypatch.setattr(
            evalrun, "render_md", lambda rep: (_ for _ in ()).throw(RuntimeError("killed"))
        )
        with pytest.raises(RuntimeError):
            cmd_run(cfg, "test", 1, None, harness_factory=factory)
    else:  # SIGKILL: no finally runs at all
        monkeypatch.setattr(evalcli, "_record", lambda step, eval_dir: None)
        cmd_run(cfg, "test", 1, None, harness_factory=factory)


@pytest.mark.parametrize("how", ["render", "kill9"])
def test_results_on_disk_can_never_be_called_aborted(cli_env, monkeypatch, how, capsys):  # noqa: F811
    cfg, factory = cli_env
    _results_written_then(cfg, factory, monkeypatch, how)
    monkeypatch.undo()
    capsys.readouterr()
    assert cmd_run(cfg, "test", 1, "aborted", harness_factory=factory) == 14
    assert (
        "did not abort" in capsys.readouterr().out
    )  # the status is derived from report.json, not a stored flag


def test_a_keyboard_interrupt_mid_run_is_recorded_as_aborted_by_the_finally(cli_env):  # noqa: F811
    cfg, factory = cli_env

    def interrupted(*a, **k):
        harness, meter, meta = factory(*a, **k)
        harness.run_gold = lambda items: (_ for _ in ()).throw(KeyboardInterrupt())
        return harness, meter, meta

    with pytest.raises(KeyboardInterrupt):
        cmd_run(cfg, "test", 1, None, harness_factory=interrupted)
    chain = Chain(cfg.paths.audit_dir / "sealed-chain.jsonl").entries()
    assert [e["kind"] for e in chain] == ["genesis", "sealed_run", "sealed_done"]
    assert (
        chain[-1]["data"]["status"] == "aborted"
    )  # no results were written: a second look 'aborted' is honest
    assert read_lock(cfg.paths.eval_dir).test_runs == 1


def test_property_random_crashes_never_lose_or_reset_a_sealed_run(tmp_path, monkeypatch):
    """Seeded random operations with a crash injected at random points; after every recovery the counter equals the
    number of sealed runs the chain holds and never goes down."""
    rng = random.Random(20261101)  # noqa: S311 - seeded test data
    for trial in range(25):
        g = gate_for(tmp_path / f"t{trial}", KEY if trial % 2 else None)
        last = 0
        for step in range(12):
            op = rng.choice(["begin", "finish", "smoke", "load", "begin"])
            crash = rng.random() < 0.35
            real = sealed.write_lock
            if crash:
                monkeypatch.setattr(
                    sealed, "write_lock", lambda *a, **k: (_ for _ in ()).throw(OSError("x"))
                )
            try:
                if op == "begin":
                    g.begin(g.load(), f"r{trial}-{step}")
                elif op == "finish":
                    g.finish(f"r{trial}-{step}", rng.choice(["complete", "aborted"]))
                elif op == "smoke":
                    g.record_smoke(f"k{step}")
                else:
                    g.load()
            except OSError:
                assert crash
            finally:
                monkeypatch.setattr(sealed, "write_lock", real)
            now = g.load().test_runs
            assert now == sealed_runs(g) >= last
            last = now


def test_concurrent_sealed_runs_leave_one_sealed_run_in_the_chain_and_one_refusal(cli_env):  # noqa: F811
    import threading

    cfg, factory = cli_env
    codes = []
    go = threading.Event()

    def run():
        go.wait()
        codes.append(cmd_run(cfg, "test", 1, None, harness_factory=factory))

    threads = [threading.Thread(target=run) for _ in range(4)]
    for th in threads:
        th.start()
    go.set()
    for th in threads:
        th.join(timeout=120)
    assert codes.count(14) == 3 and len(codes) == 4, codes
    chain = Chain(cfg.paths.audit_dir / "sealed-chain.jsonl").entries()
    assert [e["kind"] for e in chain].count("sealed_run") == 1


# ---- the hand-written harness defect is bound to a run and an item, and capped
def test_a_harness_defect_must_name_a_real_run_and_a_frozen_item(cli_env, capsys):  # noqa: F811
    cfg, factory = cli_env
    ev = cfg.paths.eval_dir
    cmd_run(cfg, "test", 1, None, harness_factory=factory)
    first = next(cfg.paths.runs_dir.iterdir()).name
    item = json.loads((ev / "gold.test.jsonl").read_text().splitlines()[0])["id"]
    good = {
        "harness_defect_reason": "gold query is wrong",
        "harness_defect_run": first,
        "harness_defect_item": item,
    }
    for bad in (
        {**good, "harness_defect_run": "no-such-run"},
        {**good, "harness_defect_run": "../" + first},
        {**good, "harness_defect_item": "ZZZ"},
    ):
        write_lock(ev, read_lock(ev).model_copy(update=bad))
        capsys.readouterr()
        assert cmd_run(cfg, "test", 1, "harness_defect", harness_factory=factory) == 14
        assert "existing run folder" in capsys.readouterr().out
    assert read_lock(ev).test_runs == 1


def test_second_looks_are_capped():
    used = Lock(
        files={}, test_runs=3, last_test_status="aborted"
    )  # first run + 2 second looks already
    with pytest.raises(LockError, match="second looks"):
        evalrun.sealed_gate(used, Decimal(9), split="test", second_look="aborted")
    evalrun.sealed_gate(
        used.model_copy(update={"test_runs": 2}), Decimal(9), split="test", second_look="aborted"
    )


# ---- smoke pass is bound to the config and model, and audited
def test_a_smoke_pass_is_bound_to_this_config_and_model(cli_env, capsys):  # noqa: F811
    cfg, factory = cli_env
    notlive = lambda c, lk, rd, ecfg: factory(c, lk, rd, evalcli.replace(ecfg, live=False))
    cmd_run(cfg, "dev", 1, None, harness_factory=notlive, use_live=True, smoke=True)
    other = cfg.model_copy(
        update={"route": cfg.route.model_copy(update={"model_id": "another-model"})}
    )
    capsys.readouterr()
    assert cmd_run(other, "test", 1, None, harness_factory=notlive, use_live=True) == 14
    assert "THIS config and model" in capsys.readouterr().out
    assert cmd_run(cfg, "test", 1, None, harness_factory=notlive, use_live=True) in (
        0,
        10,
        11,
        12,
        13,
    )
    assert read_lock(cfg.paths.eval_dir).test_runs == 1


def test_the_chain_key_comes_from_the_secrets_kind_and_a_missing_one_fails_closed(tmp_path):
    assert key_from(FakeSecretProvider({"k": "x" * 20}), "k") == b"x" * 20
    assert key_from(FakeSecretProvider({}), None) is None
    with pytest.raises(LockError, match="cannot be read"):
        key_from(FakeSecretProvider({}), "missing")
    with pytest.raises(LockError, match="at least"):
        key_from(FakeSecretProvider({"k": "short"}), "k")
    _, cfg = make_cfg(tmp_path, "sealed_key_secret_name: chain-key")
    with pytest.raises(LockError, match="no `secrets` entry"):
        evalcli._gate(cfg)


def test_freeze_with_a_key_seals_the_lock_and_an_oserror_is_exit_4(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("HADAVIN_SECRET_" + "CHAIN_KEY", "chain-key-" + "z" * 12)
    path, cfg = make_cfg(tmp_path, "secrets: {kind: env}\nsealed_key_secret_name: chain-key")
    for n in ("gold.dev.jsonl", "adversarial.dev.jsonl", "gold.test.jsonl", "adversarial.jsonl"):
        (cfg.paths.eval_dir / n).write_text(n + "\n", encoding="utf-8")
    with monkeypatch.context() as m:
        m.setattr("os.link", lambda *a, **k: (_ for _ in ()).throw(OSError("no hard links")))
        assert cli.main(["eval", "--config", str(path), "freeze"]) == 4
    assert not (cfg.paths.eval_dir / "lock.json").exists()
    assert cli.main(["eval", "--config", str(path), "freeze"]) == 0
    assert read_lock(cfg.paths.eval_dir).seal and "NOT keyed" not in capsys.readouterr().out


# ============================================================ (C) spend: every request sent is accounted
def test_call_cost_properties():
    rng = random.Random(7)  # noqa: S311 - seeded test data
    for _ in range(500):
        per = Decimal(rng.randint(1, 900)) / 10000
        n = rng.randint(1, 6)
        reserved = per * n
        sent = rng.randint(1, n)
        reply = Decimal(rng.randint(0, 900)) / 10000
        refused = rng.random() < 0.3
        with_reply = call_cost(per, reserved, sent=sent, reply_cost=reply)
        assert with_reply == per * (sent - 1) + reply >= reply  # earlier requests are never dropped
        assert call_cost(per, reserved, sent=1, reply_cost=reply) == reply
        failed = call_cost(per, reserved, sent=sent, reply_cost=None, refused=refused)
        assert 0 <= failed <= reserved  # without a reply the charge never exceeds the reservation
        assert (
            call_cost(per, reserved, sent=sent + 0, reply_cost=None, refused=True) <= failed
            or sent == 1
        )
        if sent < n:
            more = call_cost(per, reserved, sent=sent + 1, reply_cost=None, refused=refused)
            assert more >= failed  # more requests sent never cost less


class Wrap:
    """The fake model with a chosen number of requests per reply, or a chosen failure."""

    def __init__(self, inner, attempts=1, raises=None):
        self.inner, self.attempts, self.raises = inner, attempts, raises

    def chat(self, *a, **kw):
        if self.raises is not None:
            raise self.raises
        r = self.inner.chat(*a, **kw)
        return r.model_copy(update={"attempts": self.attempts})


def spend(tmp_path, name, *, attempts=1, raises=None, n=3):
    k = Kit(tmp_path / name, settings=Settings(llm_max_attempts=n))
    k.script(Q, Step(sql=COUNT_ORDERS))
    reserved = []
    real = k.meter.reserve
    k.meter.reserve = lambda amount, live=True: (reserved.append(amount), real(amount, live=live))[
        1
    ]
    k.pipeline.llm = Wrap(k.llm, attempts, raises)
    try:
        ans = k.pipeline.ask(Q)
    except BaseException as err:  # noqa: BLE001
        ans = err
    snap = k.meter.snapshot()
    return snap["askdata_spent"], reserved[0] / n, reserved[0], snap["open"], ans


def test_the_billed_earlier_attempts_of_a_retried_call_are_charged(tmp_path):
    once, per, _, open1, _ = spend(tmp_path, "a", attempts=1)
    twice, per2, _, open2, _ = spend(tmp_path, "b", attempts=2)
    thrice, _, _, _, _ = spend(tmp_path, "c", attempts=3)
    assert (
        per == per2 and twice - once == per and thrice - once == 2 * per
    )  # the last reply alone used to be settled
    assert open1 == open2 == 0


def test_a_provider_refusal_on_a_later_attempt_still_pays_for_the_earlier_ones(tmp_path):
    def refused(attempts):
        err = ProviderError("refused")
        err.attempts = attempts
        return err

    s1, per, worst, _, ans = spend(tmp_path, "r1", raises=refused(1))
    s3, _, _, o3, _ = spend(tmp_path, "r3", raises=refused(3))
    assert s1 == 0 and ans.reason == "model_unavailable"
    assert (
        s3 == 2 * per and o3 == 0
    )  # two transient failures were sent before the refusal; the refusal is free
    exhausted = ProviderExhausted("throttled")
    exhausted.attempts = 3
    sx, _, _, ox, _ = spend(tmp_path, "x", raises=exhausted)
    assert sx == worst == 3 * per and ox == 0


def test_an_unknown_failure_inside_the_kind_is_charged_in_full_and_ends_the_question(tmp_path):
    s, _, worst, o, ans = spend(tmp_path, "u", raises=RuntimeError("boom"))
    assert (
        ans.reason == "model_unavailable" and s == worst and o == 0
    )  # not an exception out of ask()


def test_ctrl_c_closes_the_reservation_before_it_propagates(tmp_path):
    s, _, worst, o, err = spend(tmp_path, "k", raises=KeyboardInterrupt())
    assert isinstance(err, KeyboardInterrupt) and s == worst and o == 0


def test_the_reservation_covers_the_forced_tool_schema(tmp_path):
    from askdata import llm_io
    from askdata.fixtures import ROUTE
    from askdata.meter import worst_case_usd

    _, per, _, _, _ = spend(tmp_path, "w")
    k = Kit(tmp_path / "w")
    content = llm_io.build_messages(k.pipeline.prompt.text, Q, None, None)[0]["content"]
    without = worst_case_usd(ROUTE, len(llm_io.SYSTEM) + len(content))
    assert per == worst_case_usd(
        ROUTE, len(llm_io.SYSTEM) + len(content) + len(json.dumps(llm_io.GENERATE_SCHEMA))
    )
    assert per > without


def test_a_process_that_dies_between_reserve_and_settle_leaves_a_visible_open_record(tmp_path):
    m = Meter(tmp_path / "meter.json")
    Meter.create(m.path, total_cap="10.00", reserve="1.00", demo_cap="8.00")
    m.reserve(Decimal("0.5"))  # ...and the process is killed here: settle never runs
    assert m.snapshot()["open"] == 1 and m.snapshot()["askdata_spent"] == Decimal(
        "0.5"
    )  # booked: fails safe
    assert m.stale_open() == []
    later = Meter(m.path, clock=lambda: m.clock() + STALE_OPEN_AFTER * 2)
    assert len(later.stale_open()) == 1  # a live run would now refuse to start
    assert later.clear_open() == 1 and later.snapshot()["askdata_spent"] == Decimal("0.5")


def test_a_live_run_refuses_to_start_over_a_stale_open_reservation(cli_env, capsys):  # noqa: F811
    cfg, factory = cli_env
    m = Meter(cfg.paths.meter_file)
    m.reserve(Decimal("0.01"))
    # make the file's reservation look old by rewriting its timestamp
    d = m._read()
    rid = next(iter(d["open"]))
    d["open"][rid]["ts"] = "2020-01-01T00:00:00Z"
    m._write(d)
    notlive = lambda c, lk, rd, ecfg: factory(c, lk, rd, evalcli.replace(ecfg, live=False))
    assert cmd_run(cfg, "dev", 1, None, harness_factory=notlive, use_live=True, smoke=True) == 14
    assert "never settled" in capsys.readouterr().out
    assert (
        cli.main(
            ["--config", str(cfg.paths.eval_dir.parent / "askdata.yaml"), "meter", "--clear-open"]
        )
        == 0
    )
    assert Meter(cfg.paths.meter_file).snapshot()["open"] == 0


# ---- the smoke abort rule has a bound from the first call
def test_the_smoke_rule_has_a_per_question_hard_cap_from_call_one():
    assert live.smoke_breach(Decimal("0.36"), 1, 1, 0, Decimal("0.36")) == "smoke_cost"
    assert (
        live.smoke_breach(Decimal("0.35"), 1, 1, 0, Decimal("0.35")) is None
    )  # at the cap, below the trend rule's N


# ============================================================ exit codes, every code driven through cli.main
def _stub(monkeypatch, red=False):
    check = SimpleNamespace(check="c", ok=not red, detail="d")
    monkeypatch.setattr(cli, "_source", lambda: SimpleNamespace(verify_readonly=lambda: [check]))


def test_every_documented_exit_code_is_produced_by_cli_main(monkeypatch, tmp_path):
    seen = {}
    _stub(monkeypatch)
    seen[EXIT_OK] = cli.main(["verify-readonly"])
    seen[EXIT_USAGE] = cli.main(["ask", "--bogus"])
    monkeypatch.setattr(cli, "gate", lambda s: 0)
    seen[EXIT_REFUSED] = cli.main(["ask", "--sql", "DELETE FROM shop.orders"])  # a write attempt
    seen[7] = cli.main(["ask", "a question the scripted model does not know"])
    _stub(monkeypatch, red=True)
    seen[EXIT_FAILED] = cli.main(["verify-readonly"])
    monkeypatch.undo()
    monkeypatch.delenv("ASKDATA_DSN", raising=False)
    monkeypatch.delenv("ASKDATA_CONFIG", raising=False)
    seen[EXIT_STARTUP] = cli.main(["verify-readonly"])
    audit_file = tmp_path / "not-a-folder"
    audit_file.write_text("x", encoding="utf-8")  # an audit folder that cannot be created
    yaml = tmp_path / "c.yaml"
    yaml.write_text(
        'as_of: "2026-01-01"\npaths: {ledger_file: l, audit_dir: '
        + str(audit_file).replace("\\", "/")
        + ", meter_file: m, "
        'kill_switch_file: k, eval_dir: e, runs_dir: r}\nroute: {model_id: m, input_usd_per_mtok: "1", '
        'output_usd_per_mtok: "1", max_tokens: 10}\n',
        encoding="utf-8",
    )
    seen[EXIT_AUDIT] = cli.main(["--config", str(yaml), "killswitch", "on"])
    assert seen == {0: 0, 1: 1, 2: 2, 7: 7, 3: 3, 4: 4, 5: 5}, seen


def test_exit_6_is_the_pipelines_per_question_code_and_no_cli_command_returns_it(tmp_path):
    k = Kit(tmp_path, demo_cap="0.0001")
    k.script(Q, Step(sql=COUNT_ORDERS))
    assert k.pipeline.ask(Q).exit_code == 6
    assert 6 not in (EXIT_OK, EXIT_USAGE, EXIT_REFUSED, EXIT_FAILED, EXIT_STARTUP, EXIT_AUDIT)


def test_a_write_the_validator_rejects_is_refused_with_the_same_code_in_ask_and_the_pipeline(
    tmp_path,
):
    k = Kit(tmp_path)
    k.script("remove the orders", *[Step(sql="DELETE FROM shop.orders")] * 3)
    ans = k.pipeline.ask("remove the orders")
    assert (ans.reason, ans.outcome, ans.exit_code) == ("write_request", "refused", EXIT_REFUSED)


# ============================================================ DSNs of b and clean through the same secret path
def test_the_b_and_clean_dsns_resolve_through_the_secrets_kind_and_errors_name_the_variable(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("HADAVIN_SECRET_" + "DSN_B", "postgresql://" + "b@x/b")
    monkeypatch.delenv("ASKDATA_DSN_B", raising=False)
    _, cfg = make_cfg(tmp_path, "secrets: {kind: env}\ndatabase: {dsn_secret_name_b: dsn-b}")
    assert live.resolve_dsn(cfg, which="b") == "postgresql://b@x/b"
    assert live.resolve_dsn(cfg, which="clean", environ={"ASKDATA_DSN_CLEAN": "e"}) == "e"
    monkeypatch.delenv("ASKDATA_DSN", raising=False)
    with pytest.raises(ConfigError, match="ASKDATA_DSN or database.dsn_secret_name"):
        evalcli.build_harness(cfg, Lock(files={}), tmp_path, evalrun.Config())
    _, bad = make_cfg(tmp_path, "database: {dsn_secret_name_b: dsn-b}")
    with pytest.raises(ConfigError, match="dsn_secret_name_b is set but"):
        live.resolve_dsn(bad, which="b")


# ============================================================ small honesty checks on the claims
def test_no_file_claims_a_tamper_proof_audit_folder():
    root = Path(evalcli.__file__).parent
    text = "\n".join(p.read_text(encoding="utf-8") for p in root.glob("*.py")) + (
        root.parent / "README.md"
    ).read_text(encoding="utf-8")
    assert "hash-chained audit" not in text and "hash-chained audit folder" not in text
    assert "tamper-resistant only by git history" in text


def test_pgerror_is_not_confused_with_a_hash_mismatch():
    assert (
        cli.cmd_ask(
            SimpleNamespace(run=lambda *a, **k: (_ for _ in ()).throw(PgError("42501", "x"))),
            "SELECT 1",
            who="t",
        )
        == EXIT_FAILED
    )


def test_reply_reports_how_many_requests_were_sent():
    assert Reply(model_id="m").attempts == 1
    assert Reply(model_id="m", attempts=3).attempts == 3
    with pytest.raises(ValueError):
        Reply(model_id="m", attempts=0)
