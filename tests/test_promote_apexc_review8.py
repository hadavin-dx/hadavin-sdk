"""Generic controls promoted from a demo's review 8 and hardened by two reviews of PR #50: read-only config view, stop gate,
row store, capped audit, one text fold, output check, mutation judge. No demo import; look-alikes are built with chr()."""

import copy
import json
import pickle
import random
import re
import threading
import time
import unicodedata
from pathlib import Path

import pytest

from hadavin_sdk.audit.capped import CappedAudit, sink_append
from hadavin_sdk.guard.egress_text import (
    DEFAULT_POLICY,
    LeakPolicy,
    Violation,
    check_text,
    text_leaks,
)
from hadavin_sdk.guard.textnorm import LOOKALIKES, fold, squeeze
from hadavin_sdk.models import KillSwitch as StoredKillSwitch
from hadavin_sdk.runtime.control import (
    ConfigHolder,
    EffectBlocked,
    FrozenDict,
    FrozenList,
    StopGate,
    freeze,
    thaw,
)
from hadavin_sdk.runtime.rowstore import DuplicateKey, RowStore, copy_row, json_keys_ok
from hadavin_sdk.testing.contracts import check_rowstore_contract
from hadavin_sdk.testing.mutation import Verdict, first_failure, judge


def pol():
    return {"limits": {"cap": 5}, "types": ["a", "b"], "tags": {"x", "y"}}


def directory():
    return {"u1": {"roles": ["clerk"], "employee_id": "e1"}}


# ---- read-only views --------------------------------------------------------------------------------------------------------------------------
def test_frozen_views_refuse_every_in_place_edit_at_every_depth():
    h = ConfigHolder(pol(), directory())
    edits = [
        lambda: h.pol["limits"].update(cap=1),
        lambda: h.pol["limits"].__ior__({"cap": 1}),
        lambda: h.pol["types"].append("c"),
        lambda: h.pol["types"].__iadd__(["c"]),
        lambda: h.pol["types"].__imul__(2),
        lambda: h.pol["types"].sort(),
        lambda: h.pol.pop("limits"),
        lambda: h.pol["limits"].__init__({"cap": 9}),  # re-running __init__ is an in-place edit
        lambda: h.pol["types"].__init__(["z"]),
        lambda: h.directory["u1"]["roles"].append("controller"),
        lambda: h.directory.__setitem__("evil", {}),
        lambda: h.pol["tags"].add("z"),  # a set is a frozenset
    ]
    for e in edits:
        with pytest.raises((TypeError, AttributeError)):
            e()
    assert h.pol["limits"]["cap"] == 5 and h.pol["tags"] == frozenset({"x", "y"})


def test_freeze_copies_deeply_and_rejects_unknown_mutable_types():
    src = pol()
    h = ConfigHolder(src, directory())
    src["limits"]["cap"] = 99
    src["tags"].add("zzz")
    assert h.pol["limits"]["cap"] == 5 and "zzz" not in h.pol["tags"]
    for bad in (bytearray(b"x"), object(), {"a": object()}, [bytearray(1)]):
        with pytest.raises(TypeError):
            freeze(bad)
    assert thaw(freeze({"a": [1, {"b": {2}}]})) == {"a": [1, {"b": {2}}]}


def test_frozen_views_behave_like_plain_json_pickle_and_deepcopy():
    f = freeze({"a": [1, {"b": 2}]})
    assert (
        isinstance(f, FrozenDict)
        and isinstance(f["a"], FrozenList)
        and json.loads(json.dumps(f)) == f
    )
    back = pickle.loads(pickle.dumps(f))  # noqa: S301 - our own bytes
    assert back == f and isinstance(back, FrozenDict)
    d = copy.deepcopy(f)  # by design the editable copy a change is prepared from
    assert type(d) is dict and type(d["a"]) is list
    d["a"].append(3)
    assert f["a"] == [1, {"b": 2}]


def test_the_holder_gives_one_consistent_pair_across_1000_swaps():
    h = ConfigHolder({"n": 0}, {"n": 0})
    stop, bad = threading.Event(), []

    def reader():
        while not stop.is_set():
            v = h.view()
            if v.pol["n"] != v.directory["n"]:
                bad.append((v.pol["n"], v.directory["n"]))

    ts = [threading.Thread(target=reader) for _ in range(4)]
    [t.start() for t in ts]
    for i in range(1, 1001):
        h.swap({"n": i}, {"n": i})
    stop.set()
    [t.join() for t in ts]
    assert bad == [] and h.view().version == 1000
    with pytest.raises(TypeError):
        h.swap({"n": object()}, {"n": 1})  # freezing fails before the lock and changes nothing
    assert h.view().version == 1000


# ---- stop gate --------------------------------------------------------------------------------------------------------------------------------
class FakeStore:
    def __init__(self):
        self.ks = StoredKillSwitch(on=False)
        self.writes = []

    def get_kill_switch(self):
        return self.ks

    def set_kill_switch(self, ks):
        self.writes.append(ks.on)
        self.ks = ks


def test_the_gate_is_not_the_stored_kill_switch_and_honours_it():
    store = FakeStore()
    a, b = StopGate(store), StopGate(store)  # two instances over one durable switch (two workers)
    assert not a.blocked() and not b.blocked()
    a.engage(list, lambda k: "x", by="u-ctl-01")
    assert (
        store.writes == [True] and store.ks.by == "u-ctl-01"
    )  # the durable switch was written (first)
    assert b.blocked()  # the other instance sees it without being engaged
    with pytest.raises(EffectBlocked), b.effect():
        raise AssertionError("an effect must not start")
    a.release(by="u-ctl-01")
    assert not b.blocked()
    store.ks = StoredKillSwitch(on=True, by="someone")  # switched on elsewhere
    assert StopGate(store).blocked()
    assert StopGate(None).blocked() is False


def test_a_port_that_checks_outside_the_lock_cannot_escape_the_gate():
    g = StopGate()
    checked, go, started = threading.Event(), threading.Event(), []

    def port():
        if not g.blocked():  # the racy convention: check ...
            checked.set()
            go.wait(5)
            try:
                with g.effect():  # ... then act: the barrier re-checks atomically
                    started.append(1)
            except EffectBlocked:
                started.append(0)

    t = threading.Thread(target=port)
    t.start()
    assert checked.wait(5)
    g.engage(
        list, lambda k: "x", by="u1", timeout=1
    )  # engaged between the port's check and its effect
    go.set()
    t.join(5)
    assert started == [0]


def test_engage_waits_for_effects_in_flight_with_a_timeout_and_sweeps_after():
    g = StopGate()
    entered, release = threading.Event(), threading.Event()
    swept = []

    def effect():
        with g.effect():
            entered.set()
            release.wait(5)

    t = threading.Thread(target=effect)
    t.start()
    assert entered.wait(5)
    res = g.engage(lambda: ["k1"], lambda k: swept.append(k) or "dequeued", by="u1", timeout=0.2)
    assert (
        res.complete is False and res.in_flight_at_timeout == 1 and swept == []
    )  # timed out, typed, nothing swept
    out = []
    t2 = threading.Thread(
        target=lambda: out.append(
            g.engage(lambda: ["k1"], lambda k: swept.append(k) or "dequeued", by="u1", timeout=5)
        )
    )
    t2.start()
    time.sleep(0.1)
    assert swept == []  # still waiting for the effect in flight
    release.set()
    t.join(5)
    t2.join(5)
    assert swept == ["k1"] and out[0].complete and out[0].results == [("k1", "dequeued")]


def test_one_failing_undo_does_not_stop_the_sweep_and_an_interrupt_keeps_the_partial_result():
    g = StopGate()

    def undo(k):
        if k == "bad":
            raise RuntimeError("x")
        return "ok"

    assert g.engage(lambda: ["bad", "good"], undo, by="u").results == [
        ("bad", "error:RuntimeError"),
        ("good", "ok"),
    ]
    g2 = StopGate()

    def undo2(k):
        if k == "b":
            raise KeyboardInterrupt
        return "ok"

    with pytest.raises(KeyboardInterrupt):
        g2.engage(lambda: ["a", "b", "c"], undo2, by="u")
    assert g2.last.results == [("a", "ok"), ("b", "interrupted")] and g2.last.complete is False
    st = FakeStore()
    assert StopGate(st).engage(list, lambda k: "", by="bad\nlabel; DROP").results == []
    assert st.ks.by == "?"  # a free-text label is never stored raw


# ---- row store --------------------------------------------------------------------------------------------------------------------------------
def test_the_row_store_meets_the_contract():
    check_rowstore_contract(RowStore)


def test_a_bad_row_fails_before_the_audit_and_a_failed_audit_inserts_nothing():
    rs, audited = RowStore(), []
    for bad in (
        {"a": float("nan")},
        {1: "x"},
        {"a": {(1, 2): 1}},
        {"a": {1}},
        {"a": object()},
        {"a": float("inf")},
    ):
        with pytest.raises(ValueError):
            rs.put_audited(lambda kind, **f: audited.append(kind), "k", "r", bad)
    assert audited == [] and rs.keys() == []

    def boom(*a, **k):
        raise OSError("down")

    with pytest.raises(OSError):
        rs.put_audited(boom, "k", "r", {"a": 1})
    assert rs.keys() == []
    rs.put_audited(
        lambda *a, **k: None, "k", "r", {"a": 1}
    )  # the key was released after the failure
    with pytest.raises(DuplicateKey):
        rs.put_audited(lambda *a, **k: None, "k", "r", {"a": 2})


def test_an_audit_callback_can_read_the_store_and_a_slow_audit_does_not_block_readers():
    rs = RowStore()
    rs.put_audited(lambda *a, **k: None, "k", "one", {"n": 1})
    seen = []
    rs.put_audited(
        lambda kind, **f: seen.append(rs.snapshot()), "k", "two", {"n": 2}
    )  # would deadlock with a non-reentrant lock held
    assert seen == [{"one": {"n": 1}}]
    started, done = threading.Event(), threading.Event()

    def slow(kind, **f):
        started.set()
        done.wait(5)

    t = threading.Thread(target=lambda: rs.put_audited(slow, "k", "three", {"n": 3}))
    t.start()
    assert started.wait(5)
    t0 = time.monotonic()
    assert sorted(rs.snapshot()) == [
        "one",
        "two",
    ]  # a reader is not blocked by an audit write in progress
    assert time.monotonic() - t0 < 1
    with pytest.raises(DuplicateKey):
        rs.put_audited(
            lambda *a, **k: None, "k", "three", {}
        )  # the key is reserved while its audit is written
    done.set()
    t.join(5)
    assert "three" in rs.snapshot()


def test_snapshot_copies_under_the_lock_and_the_rows_are_private():
    rs = RowStore()
    rs.put_audited(lambda *a, **k: None, "k", "a", {"n": [1]})
    snap = rs.snapshot()
    snap["a"]["n"].append(2)
    assert rs.get("a") == {"n": [1]} and not hasattr(rs, "rows")
    assert json_keys_ok({"a": [{"b": 1}]}) and not json_keys_ok({7: 1})
    with pytest.raises(ValueError):
        copy_row({"a": float("nan")})


# ---- capped audit -----------------------------------------------------------------------------------------------------------------------------
def test_capped_audit_is_per_tenant_per_bucket_bounded_and_visible():
    rows = []
    ca = CappedAudit(lambda kind, **f: rows.append((kind, f["tenant"])), cap=2)
    for _ in range(6):
        ca.deny("t1", "denied", "2026-11-02")
    ca.deny("t2", "denied", "2026-11-02")  # another tenant is not starved
    assert [r for r in rows if r[1] == "t1"] == [
        ("denied", "t1"),
        ("denied", "t1"),
        ("audit_suppressed", "t1"),
    ]
    assert ("denied", "t2") in rows and ca.suppressed("t1", "denied") == 4
    ca.deny(
        "t1", "denied", "2026-11-03"
    )  # a new bucket resets, and the old bucket's counter is dropped
    assert ca.suppressed("t1", "denied") == 0 and len(ca._n) == 2
    with pytest.raises(ValueError):
        CappedAudit(lambda *a, **k: None, cap=0)


def test_capped_audit_retries_a_failed_suppression_marker_and_never_raises_from_deny():
    state = {"fail": True}
    rows = []

    def append(kind, **f):
        if kind == "audit_suppressed" and state["fail"]:
            raise OSError("down")
        rows.append(kind)

    ca = CappedAudit(append, cap=1)
    ca.deny("t", "d", "b")
    ca.deny("t", "d", "b")  # marker write fails, swallowed by deny
    state["fail"] = False
    ca.deny("t", "d", "b")  # retried
    assert rows == ["d", "audit_suppressed"]
    with pytest.raises(OSError):
        CappedAudit(lambda *a, **k: (_ for _ in ()).throw(OSError()), 1).append("t", "d", "b")


def test_sink_append_adapts_an_audit_sink_without_leaking_fields():
    got = []

    class Sink:
        def write_outcome(self, ev):
            got.append(ev)

    ca = CappedAudit(sink_append(Sink(), "run1", "dom"), cap=1)
    ca.append("t", "refused", "b", secret_body="do not store", key="k1")  # noqa: S106
    assert (
        got[0].operation == "refused"
        and got[0].object_ref == "k1"
        and "do not store" not in got[0].model_dump_json()
    )


# ---- one text fold ----------------------------------------------------------------------------------------------------------------------------
def test_fold_is_stable_under_combining_marks_and_format_characters():
    rnd = random.Random(7)  # noqa: S311
    marks = [
        chr(0x301),
        chr(0x300),
        chr(0x200B),
        chr(0xFE0F),
        chr(0x3164),
        chr(0x202E),
        chr(0xAD),
        chr(0xE000),
    ]
    for _ in range(300):
        x = "".join(rnd.choice("abcXYZ019 -.") for _ in range(rnd.randint(0, 12)))
        for m in marks:
            assert fold(x + m) == fold(x) == fold(m + x)


def test_fold_covers_the_listed_look_alikes_in_every_script_and_all_map_to_ascii_letters():
    listed = {0x405: "S", 0x406: "I", 0x408: "J", 0x423: "Y", 0x41E: "O", 0x455: "s", 0x3B9: "i", 0x3BA: "k", 0x3C1: "p", 0x3C4: "t",
              0x3C5: "u", 0x3C7: "x", 0x501: "d", 0x131: "i", 0x130: "I", 0x585: "o", 0x57D: "u", 0x555: "O", 0x54D: "U", 0x3BF: "o"}  # fmt: skip
    for cp, latin in listed.items():
        assert fold(chr(cp)) == latin, hex(cp)
    assert all(re.fullmatch("[A-Za-z]", v) for v in LOOKALIKES.values())
    assert fold("١٢３") == "123" and fold("a\nb\tc") == "a b c"
    for sp in (
        0x85,
        0x1C,
        0x1F,
        0x2028,
        0x2029,
        0xA0,
        0x3000,
        0x2003,
    ):  # every Unicode space separates words
        assert fold("ab" + chr(sp) + "cd") == "ab cd", hex(sp)
    assert (
        squeeze("AB-12 3" + chr(0x200B) + "4") == squeeze("ab1234")
        and squeeze("O0Il1", loose=True) == "00111"
    )
    assert not any(
        unicodedata.category(c) in ("Cc", "Cf") for c in fold("x" + chr(0x200B) + chr(0x202E))
    )


def test_gate_views_use_the_shared_fold():
    from hadavin_sdk.approvals.gate import _views

    assert "AKIAIOSFODNN7EXAMPLE" in _views(
        "AK" + chr(0x406) + "A" + chr(0x406) + "OSFODNN7EXAMPLE"
    )


# ---- output check -----------------------------------------------------------------------------------------------------------------------------
SEPS = [" ", "_", ":", "|", "ab", " ab ", chr(0xA0), chr(0x200B), chr(0x301), chr(0x2013), chr(0xE9), chr(0x65E5), chr(0x405), chr(0x43E),
        chr(0x4AE), ".", ",", "-", "/"]  # fmt: skip


def test_digit_budget_beats_separators_letters_scripts_and_punctuation():
    rnd = random.Random(1)  # noqa: S311
    for _ in range(400):
        digs = "".join(
            chr(rnd.choice((0x30, 0xFF10, 0x660, 0x966)) + rnd.randrange(10))
            for _ in range(rnd.randint(8, 18))
        )
        text = "acct " + "".join(d + (rnd.choice(SEPS) if rnd.random() < 0.7 else "") for d in digs)
        v = check_text(text)
        assert v is not None, text
    assert (
        text_leaks("1234 ab 5678 ab 9012") and text_leaks("1234-12-12") and text_leaks("1999-12-12")
    )


def test_exempt_tokens_are_not_a_free_pass_for_a_card_number():
    for text in (
        "$4111111.11 $1111111.11 1111",
        "$1,234,567.89 $1,234,567.89",
        "2026-11-01 2026-11-02 2026-11-03 2026-11-04",
        "$1.50 $2.50 $3.50 $4.50 $5.50 $6.50 $7.50",
    ):
        assert check_text(text) == Violation.EXEMPT_TOKENS, text
    # amounts need a currency: unanchored decimals and groups are plain digits and hit the budget
    for text in (
        "1,234 ab 5,678 ab 9,012",
        "2.8 and 5.6 and 7.9 and 1.2 and 3.4",
        "4111111.11 1111111.11 1111",
    ):
        assert check_text(text) == Violation.DIGIT_BUDGET, text
    assert check_text("dated 2026-11-01, total 1,500,000 USD") is None
    # the caps work on their own: seven small tokens (count) and four dates (digits) separated by words
    assert check_text(" and ".join(f"${i}.50" for i in range(1, 8))) == Violation.EXEMPT_TOKENS
    assert (
        check_text("on 2026-11-01 and 2026-11-02 and 2026-11-03 and 2026-11-04")
        == Violation.EXEMPT_TOKENS
    )
    # the caps work on their own: seven small tokens (count) and four dates (digits) separated by words
    assert check_text(" and ".join(f"${i}.50" for i in range(1, 8))) == Violation.EXEMPT_TOKENS
    assert (
        check_text("on 2026-11-01 and 2026-11-02 and 2026-11-03 and 2026-11-04")
        == Violation.EXEMPT_TOKENS
    )
    assert check_text("total $1,500.00 due 2026-11-30") is None
    assert check_text("tax 12,345,678.90", policy=LeakPolicy(amounts_need_currency=False)) is None


def test_digit_like_letters_count_when_chained_to_digits():
    assert check_text("8 O 1 l 5 S 7 B 3") == Violation.DIGIT_BUDGET
    assert check_text("8-O-1-l-5-S-7-B-3") == Violation.DIGIT_BUDGET
    assert check_text("order of 3 small boxes and one big sale") is None


def test_what_passes_and_the_full_homoglyph_fold_for_protected_values():
    for ok in (
        "price differs by 2 percent",
        "dated 2026-11-01, total 1,500,000 USD",
        "qty 12 at 450 each, line 7",
        "line 3 short by 4",
    ):
        assert not text_leaks(ok), ok
    secret = "ACCOUNTSIJY77"  # noqa: S105
    spoof = "acct " + secret.replace("S", chr(0x405)).replace("I", chr(0x406)).replace(
        "J", chr(0x408)
    ).replace("Y", chr(0x423))
    assert check_text(spoof, [secret]) == Violation.PROTECTED_VALUE
    assert (
        check_text("pay " + "ACC" + chr(0x4C0) + chr(0x3B9) + "NT" + "XQ", ["ACCIINTXQ"])
        == Violation.PROTECTED_VALUE
    )


def test_allowed_references_need_a_boundary_and_ignore_case():
    assert check_text("ref ABC-2026-0482 ok", allowed=["ABC-2026-0482"]) is None
    assert check_text("ref abc-2026-0482 ok", allowed=["ABC-2026-0482"]) is None
    assert check_text("ABC-2026-0482 ok") is not None
    assert (
        check_text("XABC-2026-04829999 ok", allowed=["ABC-2026-0482"]) is not None
    )  # not a standalone reference


def test_short_protected_values_raise_and_the_length_is_bounded_first():
    with pytest.raises(ValueError):
        check_text("anything", ["ab"])
    assert (
        check_text(None) == Violation.TEXT_NOT_STRING
        and check_text(b"x") == Violation.TEXT_NOT_STRING
    )
    assert check_text("x" * (DEFAULT_POLICY.max_len + 1)) == Violation.TEXT_TOO_LONG
    big = "x " * 600_000  # 1.2 MB: refused at once, never folded
    t0 = time.monotonic()
    assert check_text(big) == Violation.TEXT_TOO_LONG and time.monotonic() - t0 < 0.5
    t0 = time.monotonic()
    check_text("word " * 800)  # at the cap, still fast (linear fold)
    assert time.monotonic() - t0 < 1


def test_thresholds_come_from_a_validated_policy():
    p = LeakPolicy.from_mapping({"max_digits": 12, "date_years": [1990, 2100]})
    assert check_text("id 1234 5678 9012", policy=LeakPolicy(max_digits=13)) is None
    assert (
        check_text("id 1234 5678 9012", policy=LeakPolicy(max_digits=12)) == Violation.DIGIT_BUDGET
    )
    assert check_text("1995-05-05", policy=p) is None
    for bad in (
        {"max_digits": 0},
        {"max_len": -1},
        {"date_years": [2100, 2000]},
        {"nope": 1},
        {"max_digits": "8"},
    ):
        with pytest.raises(ValueError):
            LeakPolicy.from_mapping(bad)


# ---- mutation judge ---------------------------------------------------------------------------------------------------------------------------
def test_mutation_judge_verdicts():
    a = "E   AssertionError: assert 1 == 2"
    assert judge(1, "t.py::a", a) == Verdict.KILLED and judge(0, "t.py::a", a) == Verdict.SURVIVED
    assert judge(5, "t.py::a", a) == Verdict.NO_TESTS and judge(2, "t.py::a", a) == Verdict.ERROR
    assert (
        judge(1, "t.py::a", a, expect="a") == Verdict.KILLED
        and judge(1, "t.py::a", a, expect="zz") == Verdict.WRONG_REASON
    )
    assert judge(1, "t.py::a", a, pinned="t.py::b") == Verdict.OTHER_TEST
    for line in (
        "E   KeyError: 'x'",
        "E   TypeError: boom",
        "E   RuntimeError: x",
        "E   ImportError: no",
        "E   apexc.fakes.AuditWriteError: audit write failed",
    ):
        assert judge(1, "t.py::a", line) == Verdict.CRASH, line
    assert judge(1, "t.py::a", "E   Failed: DID NOT RAISE <class 'TypeError'>") == Verdict.KILLED
    internal = "E   AssertionError: assert 'denied:internal_error' == 'queued'"
    assert judge(1, "t.py::a", internal) == Verdict.KILLED
    assert (
        judge(
            1, "t.py::a", internal, crash_markers=[re.compile(r"assert 'denied:internal_error' ==")]
        )
        == Verdict.CRASH
    )
    assert (
        judge(1, "t.py::test[a | b]", a, pinned="t.py::test[a | b]") == Verdict.KILLED
    )  # ids with ' | ' are never split
    out = "FAILED tests/t.py::test_x[1 | 2] - assert 1\nE   AssertionError: assert 1 == 2\n"
    assert first_failure(out) == ("tests/t.py::test_x[1 | 2]", "E   AssertionError: assert 1 == 2")


# ---- shared test vectors: the same file is for every consumer of the fold (SoD comparison, egress domain check) -------------------------------
VECTORS = json.loads(
    (Path(__file__).parent / "fixtures" / "textnorm_vectors.json").read_text(encoding="utf-8")
)


def _decode(s: str) -> str:
    return re.sub(r"\{U\+([0-9A-Fa-f]{4,6})\}", lambda m: chr(int(m[1], 16)), s)


def test_vectors_ids_with_homoglyphs_fold_to_the_real_id():
    for case in VECTORS["identities"]:
        real = fold(case["id"], casefold=True, collapse_ws=True)
        for variant in case["variants"]:
            assert fold(_decode(variant), casefold=True, collapse_ws=True) == real, (
                case["id"],
                variant,
            )
        for other in case.get("different", []):
            assert fold(_decode(other), casefold=True, collapse_ws=True) != real, (
                case["id"],
                other,
            )


def test_vectors_domains_with_cyrillic_and_greek_letters_fold_to_the_ascii_domain():
    for case in VECTORS["domains"]:
        for variant in case["variants"]:
            assert fold(_decode(variant), casefold=True) == case["domain"], (
                case["domain"],
                variant,
            )


def test_a_restart_restores_the_flag_without_touching_the_store():
    store = FakeStore()
    g = StopGate(store)
    g.restore(True)
    assert g.engaged and store.writes == []
    with pytest.raises(EffectBlocked), g.effect():
        raise AssertionError("an effect must not start")
    g.restore(False)
    assert not g.engaged


def test_promoted_files_match_the_pinned_hashes_the_demo_repo_copies():
    """The same list is pinned in the demo repo (`core_copies.json`): a change here without a new pin there fails one side."""
    import hashlib

    pins = json.loads(
        (Path(__file__).parent / "fixtures" / "core_copies.json").read_text(encoding="utf-8")
    )
    root = Path(__file__).resolve().parents[1]
    for rel, sha in pins["files"].items():
        text = (root / rel).read_text(encoding="utf-8").replace(chr(13) + chr(10), chr(10))
        assert hashlib.sha256(text.encode()).hexdigest() == sha, rel
