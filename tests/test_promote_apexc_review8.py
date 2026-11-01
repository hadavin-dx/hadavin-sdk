"""Generic controls promoted from a demo's review 8: read-only shared config, kill switch, ledger helpers,
digit-budget leak check, and the mutation judge. No demo import; look-alikes are built with chr()."""

import copy
import json
import random
import threading
import time

import pytest

from hadavin_sdk.guard.leakcheck import fold, text_leaks
from hadavin_sdk.runtime.control import ConfigHolder, KillSwitch, freeze, thaw
from hadavin_sdk.runtime.ledger import CappedAudit, Ledger, copy_deep, json_keys_ok
from hadavin_sdk.runtime.mutation import judge

POL = {"limits": {"cap": 5}, "types": ["a", "b"]}
DIR = {"u1": {"roles": ["clerk"], "employee_id": "e1"}}


def test_frozen_views_refuse_every_in_place_edit_at_every_depth():
    h = ConfigHolder(POL, DIR)
    POL["limits"]["cap"] = 99  # the caller's own dict is not shared
    assert h.pol["limits"]["cap"] == 5
    edits = [
        lambda: h.pol["limits"].update(cap=1),
        lambda: h.pol["types"].append("c"),
        lambda: h.pol.pop("limits"),
        lambda: h.directory["u1"]["roles"].append("controller"),
        lambda: h.directory.__setitem__("evil", {}),
        lambda: h.pol["types"].sort(),
    ]
    for e in edits:
        with pytest.raises(TypeError):
            e()
    assert json.loads(json.dumps(h.pol)) == h.pol and type(copy.deepcopy(h.pol)) is dict
    assert thaw(freeze({"a": [1, {"b": 2}]})) == {"a": [1, {"b": 2}]}
    POL["limits"]["cap"] = 5


def test_one_holder_serves_every_reader_and_swap_is_the_only_way_to_change_it():
    h = ConfigHolder(POL, DIR)
    seen = h.pol
    h.swap({"limits": {"cap": 7}}, DIR)
    assert h.pol is not seen and h.pol["limits"]["cap"] == 7


def test_kill_switch_blocks_ports_first_and_waits_for_work_in_flight():
    h = ConfigHolder(POL, DIR)
    ks = KillSwitch(h)
    queued: list[str] = []
    undone: list[str] = []

    def in_flight():
        with h.lock:  # a release past its gates
            for _ in range(200):
                if ks.engaged:
                    break
                time.sleep(0.01)
            time.sleep(0.2)
            queued.append("k1")

    t = threading.Thread(target=in_flight)
    t.start()
    time.sleep(0.05)
    out = ks.engage(lambda: list(queued), lambda k: undone.append(k) or "dequeued")
    t.join()
    assert h.blocked() and out == [("k1", "dequeued")]
    ks.release()
    assert not h.blocked()


def test_one_failing_undo_does_not_stop_the_sweep():
    ks = KillSwitch(ConfigHolder(POL, DIR))

    def undo(k):
        if k == "bad":
            raise RuntimeError("x")
        return "ok"

    assert ks.engage(lambda: ["bad", "good"], undo) == [
        ("bad", "error:RuntimeError"),
        ("good", "ok"),
    ]


class _Racing(dict):
    """Iteration is joined by a concurrent writer: it lands mid-iteration unless iteration holds the lock."""

    ledger = None

    def items(self):
        first = True
        for kv in dict.items(self):
            if first:
                first = False
                t = threading.Thread(
                    target=lambda: self.ledger.write_after_audit(
                        lambda *a, **k: None, "k", "new", {"x": 1}
                    )
                )
                t.start()
                t.join(0.3)
            yield kv


def test_snapshot_is_taken_under_the_lock_and_returns_copies():
    led = Ledger()
    led.rows = _Racing({"a": {"n": [1]}})
    led.rows.ledger = led
    snap = led.snapshot()  # raises RuntimeError if the writer lands mid-iteration
    snap["a"]["n"].append(2)
    assert led.rows["a"] == {"n": [1]}


def test_audit_comes_before_the_write():
    led = Ledger()

    def failing(*a, **k):
        raise OSError("audit down")

    with pytest.raises(OSError):
        led.write_after_audit(failing, "k", "r1", {"a": 1})
    assert led.rows == {}
    led.write_after_audit(lambda *a, **k: None, "k", "r1", {"a": 1})
    assert led.rows == {"r1": {"a": 1}}


def test_json_keys_and_copies():
    assert json_keys_ok({"a": [{"b": 1}]})
    assert (
        not json_keys_ok({"a": {(1, 2): 1}})
        and not json_keys_ok({"a": {7: 1}})
        and not json_keys_ok({"a": (1,)})
    )
    src = {"a": [1]}
    c = copy_deep(src)
    c["a"].append(2)
    assert src == {"a": [1]}


def test_capped_audit_caps_per_bucket_and_never_raises():
    rows: list[tuple] = []
    ca = CappedAudit(lambda kind, **f: rows.append((kind, f)), cap=2)
    for _ in range(6):
        ca.deny("denied", "2026-11-02", who="x")
    assert [r[0] for r in rows] == ["denied", "denied", "audit_suppressed"]
    ca.deny("denied", "2026-11-03", who="x")
    assert len(rows) == 4

    def boom(*a, **k):
        raise OSError

    CappedAudit(boom, 1).deny("denied", "d")  # an audit outage never changes the refusal


SEPS = [
    " ",
    "_",
    ":",
    "|",
    "ab",
    " ab ",
    chr(0xA0),
    chr(0x200B),
    chr(0x301),
    chr(0x2013),
    chr(0xE9),
    chr(0x65E5),
    chr(0x405),
    chr(0x43E),
    chr(0x4AE),
]


def test_digit_budget_beats_separators_letters_and_scripts():
    rnd = random.Random(1)  # noqa: S311 - test data
    for _ in range(300):
        digs = "".join(
            chr(rnd.choice((0x30, 0xFF10, 0x660, 0x966)) + rnd.randrange(10))
            for _ in range(rnd.randint(8, 18))
        )
        text = "acct " + "".join(d + (rnd.choice(SEPS) if rnd.random() < 0.7 else "") for d in digs)
        assert text_leaks(text), text
    assert (
        text_leaks("1234 ab 5678 ab 9012") and text_leaks("1234-12-12") and text_leaks("1999-12-12")
    )


def test_what_passes_and_the_full_homoglyph_fold():
    for ok in (
        "price differs by 2 percent",
        "dated 2026-11-01, total 1,500,000 USD",
        "qty 12 at 450 each, line 7",
        "line 3 short by 4",
    ):
        assert not text_leaks(ok), ok
    for cp, latin in {
        0x405: "S",
        0x406: "I",
        0x408: "J",
        0x423: "Y",
        0x41E: "O",
        0x455: "s",
    }.items():
        assert fold(chr(cp)) == latin
    secret = "ACCOUNTSIJY77"  # noqa: S105 - test data
    spoof = "acct " + secret.replace("S", chr(0x405)).replace("I", chr(0x406)).replace(
        "J", chr(0x408)
    ).replace("Y", chr(0x423))
    assert text_leaks(spoof, [secret])
    assert not text_leaks("ref ABC-2026-0482 ok", allowed=["ABC-2026-0482"]) and text_leaks(
        "ABC-2026-0482 ok"
    )


def test_mutation_judge_checks_reason_pin_and_crash():
    plain = "t.py::test_a | E   AssertionError: assert 1 == 2"
    assert (
        judge(1, plain) == "KILLED"
        and judge(0, plain) == "SURVIVED"
        and judge(5, plain) == "NO TESTS RAN"
    )
    assert (
        judge(1, plain, "test_a") == "KILLED" and judge(1, plain, "other") == "KILLED-WRONG-REASON"
    )
    assert judge(1, plain, None, "t.py::test_b") == "KILLED-OTHER-TEST"
    assert judge(1, "t.py::t | E   KeyError: 'x'") == "KILLED-CRASH"
    assert (
        judge(1, "t.py::t | E   AssertionError: assert 'denied:internal_error' == 'queued'")
        == "KILLED-CRASH"
    )
