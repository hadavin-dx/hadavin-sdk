"""Fix batch 3 for core PR #50 after the third independent review of 659dfc6 (ledger BL-core-pr50-r2-024, BL-core-pr50-r3-001 to 020).

A comment FAIL-BEFORE marks a check that fails on the 659dfc6 source; the others are regression guards or are killed by a mutant of
promoted_mutants.py (named there). No test here depends on a clock."""

import logging
import re
import sys
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from tools import mutation_runner as mr
from tools.mutation_runner import Mutant, run_mutants

from hadavin_sdk.audit import capped, labelkey
from hadavin_sdk.audit.capped import CappedAudit, _clip
from hadavin_sdk.errors import SwitchChanged
from hadavin_sdk.guard import http, textnorm
from hadavin_sdk.guard.redact import FOLD_NOTE, _Redactor, redact
from hadavin_sdk.guard.runmap import InputTooLarge, redact_text
from hadavin_sdk.limits import Limits
from hadavin_sdk.models import KillSwitch
from hadavin_sdk.runtime import rowstore
from hadavin_sdk.runtime.rowstore import RowStore, StoreFull
from hadavin_sdk.runtime.stop_gate import StopGate, StopGateBusy, _label
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.testing.contracts import check_rowstore_contract
from hadavin_sdk.testing.mutation import Verdict
from tests.test_promoted_controls import FakeLimits, RecordingSink, _pk_tree

ROOT = Path(__file__).resolve().parents[1]
redact_mod = sys.modules["hadavin_sdk.guard.redact"]


def _fold(t):
    return textnorm.fold(t)


# ---- 1. bank context in the fold path ------------------------------------------------------------------------------------------------------------
def test_an_account_number_below_an_accented_or_full_width_keyword_is_masked_when_a_bank_word_stands_elsewhere():
    accent = "BSB 062-000\naccó" + "unt number 12345678"
    wide = "BSB 062-000\n" + "".join(chr(ord(c) + 0xFEE0) for c in "account") + " number 12345678"
    for text in (accent, wide):
        out = redact(text).text
        assert "12345678" not in _fold(out), out  # FAIL-BEFORE: the number stayed in clear
    assert (
        "12345678" not in redact("BSB 062-000\naccount number 12345678").text
    )  # the ASCII control case


# ---- 2. pattern indexes per line, CPU clock ---------------------------------------------------------------------------------------------------------
def test_a_suspect_line_loops_only_the_patterns_that_matched_it(monkeypatch):
    seen = []
    real = _Redactor._mask_in_place

    def spy(self, body, folded, where, alike, only=None):
        seen.append(only)
        return real(self, body, folded, where, alike, only=only)

    monkeypatch.setattr(_Redactor, "_mask_in_place", spy)
    assert redact("mail josé@example.com now").text == "mail <EMAIL_1> now"
    assert seen and all(o is not None and 0 < len(o) < 10 for o in seen), (
        seen
    )  # FAIL-BEFORE: every pattern (about 95) took a round


def test_the_budget_is_cpu_time_of_the_thread_not_the_wall_clock(monkeypatch):
    def forbidden():
        raise AssertionError("the wall clock was read")

    monkeypatch.setattr(time, "monotonic", forbidden)
    assert (
        redact("café josé@example.com").text == "café <EMAIL_1>"
    )  # FAIL-BEFORE: read time.monotonic
    redact_text("mail josé@example.com café", {})


def test_the_cookie_line_really_takes_three_rounds(monkeypatch):
    calls = []
    real = _Redactor._aligned_fold
    monkeypatch.setattr(
        _Redactor, "_aligned_fold", staticmethod(lambda b, d: calls.append(b) or real(b, d))
    )
    assert redact("Cookie: sid=josé@example.com; a=bé").text == "Cookie: <SECRET_1>"
    assert len(calls) >= 3, calls  # two rounds that change the text and one that finds nothing


def test_aligned_fold_checks_the_budget_every_4096_characters():
    with pytest.raises(InputTooLarge):
        _Redactor._aligned_fold("é" * 5000, 0.0)  # a deadline in the past


def test_one_half_is_masked_around_but_a_full_width_slash_is_still_an_attack():
    assert (
        redact("½ cup, mail josé@example.com now").text == "½ cup, mail <EMAIL_1> now"
    )  # FAIL-BEFORE: withheld
    assert redact("mail josé@example.com ／／ x").text.startswith(FOLD_NOTE)


# ---- 3. a suppressed event does no redaction ------------------------------------------------------------------------------------------------------
def test_suppressed_events_do_no_redaction(monkeypatch):
    calls = []
    real = capped.redact_bounded
    monkeypatch.setattr(capped, "redact_bounded", lambda t, m: calls.append(len(t)) or real(t, m))
    ca = CappedAudit(lambda kind, **f: None, cap=1, max_keys=1)
    ca.deny("first", "refused", "2026-11-05")
    base = len(calls)
    for i in range(60):
        ca.deny(
            "é" * 1088 + str(i), "refused", "2026-11-05"
        )  # unique long tenants: all land on the overflow counter
    assert len(calls) - base < 12, (
        len(calls) - base
    )  # FAIL-BEFORE: about 120 (tenant and kind redacted on every request)


# ---- 4. release is a compare-and-set ----------------------------------------------------------------------------------------------------------------
class HookSink(RecordingSink):
    hook = None

    def write_intent(self, ev):
        r = super().write_intent(ev)
        if self.hook and ev.operation == "reset":
            self.hook()
        return r


def _real_limits():
    store, sink = MemoryStore(), HookSink()
    return Limits(store, sink, None), store, sink


def test_a_release_does_not_turn_off_a_stop_an_operator_set_after_the_gate_engaged():
    lim, store, _ = _real_limits()
    a = StopGate(lim)
    a.engage(list, lambda k: "x", by="alice")
    lim.stop("ops")  # an operator stops it again
    with pytest.raises(StopGateBusy):
        a.release("alice")  # FAIL-BEFORE: turned the switch off for everyone
    assert store.get_kill_switch().on and a.engaged


def test_a_stop_that_lands_between_the_reset_intent_and_the_write_is_kept():
    lim, store, sink = _real_limits()
    a = StopGate(lim)
    a.engage(list, lambda k: "x", by="alice")
    sink.hook = lambda: lim.stop(
        "bee"
    )  # gate B engages while A's reset is between its intent and its write
    with pytest.raises(StopGateBusy):
        a.release("alice")
    assert store.get_kill_switch().on and store.get_kill_switch().by == "bee"
    assert any(e.operation == "reset_refused" for e in sink.events)  # no dangling intent
    sink.hook = None


def test_an_undisturbed_release_still_clears_and_reset_expect_is_checked():
    lim, store, _ = _real_limits()
    a = StopGate(lim)
    a.engage(list, lambda k: "x", by="alice")
    a.release("alice")
    assert not store.get_kill_switch().on and not a.engaged
    with pytest.raises(SwitchChanged):
        lim.stop("x")
        lim.reset("y", expect=("someone else", None))


# ---- 5. labels --------------------------------------------------------------------------------------------------------------------------------------
def test_labels_are_stable_across_gates_with_the_same_key_and_differ_with_another():
    k1, k2 = b"k" * 32, b"j" * 32
    a, b = StopGate(FakeLimits(), label_key=k1), StopGate(FakeLimits(), label_key=k1)
    assert (
        a._lbl("José") == b._lbl("José") != StopGate(FakeLimits(), label_key=k2)._lbl("José")
    )  # FAIL-BEFORE: no label_key
    assert re.fullmatch(r"id:[0-9a-f]{32}", a._lbl("José"))
    lim = FakeLimits()
    StopGate(lim, label_key=k1).engage(list, lambda k: "", by="José")
    assert lim.log == [("stop", a._lbl("José"))]


def test_the_fallback_key_is_logged_once(monkeypatch, caplog):
    monkeypatch.setattr(labelkey, "_fallback", None)
    with caplog.at_level(logging.WARNING, logger=labelkey.__name__):
        x, y = _label("José"), _label("José")
    assert x == y and len([r for r in caplog.records if "per-process key" in r.message]) == 1


def test_restore_false_needs_by_and_writes_it_as_the_principal():
    lim = FakeLimits()
    g = StopGate(lim)
    g.restore(True)
    with pytest.raises(ValueError):
        g.restore(False)  # FAIL-BEFORE: no by parameter, principal "-"
    g.restore(False, by="ops")
    assert [e.principal for e in lim.audit.intents if e.operation == "restore"] == ["ops"]
    assert "as written" in _label.__doc__.lower()


# ---- 8. restore: fresh read, second critical section, outcome rows --------------------------------------------------------------------------------
def test_restore_false_reads_the_durable_switch_fresh_not_through_the_cache():
    lim = FakeLimits()
    g = StopGate(lim, cache_ttl=1000.0)
    assert not g.durable_on()  # caches "off"
    g.restore(True)
    lim.store.ks = KillSwitch(on=True, by="ops")
    with pytest.raises(StopGateBusy):
        g.restore(
            False, by="ops"
        )  # FAIL-BEFORE: the cached "off" cleared the flag while the switch was ON
    assert g.engaged


def test_an_engage_during_the_restore_audit_keeps_the_stop_and_writes_a_refused_outcome():
    lim = FakeLimits()
    g = StopGate(lim)
    g.restore(True)
    lim.audit.write_intent = lambda ev: g.engage(list, lambda k: "", by="u1") and None
    with pytest.raises(StopGateBusy):
        g.restore(False, by="ops")
    assert g.engaged
    assert [e.operation for e in lim.audit.events][
        -1
    ] == "restore_refused"  # FAIL-BEFORE: no outcome row


def test_a_successful_restore_writes_the_done_row():
    lim = FakeLimits()
    g = StopGate(lim)
    g.restore(True)
    g.restore(False, by="ops")
    assert [e.operation for e in lim.audit.events] == ["restore_done"]


# ---- 7. capped minors ---------------------------------------------------------------------------------------------------------------------------------
def test_the_clip_never_exceeds_its_limit_and_strips_format_characters():
    assert len(_clip("a b " * 100, 10)) <= 10
    odd = [
        chr(0x200B),
        chr(0x202E),
        chr(0x2066),
    ]  # zero-width space, right-to-left override, isolate
    assert not any(
        c in _clip("a" + odd[0] + "b" + odd[1] + "c" + odd[2] + "d", 20) for c in odd
    )  # FAIL-BEFORE: only Cc and two separators were replaced


def test_a_long_password_that_needs_context_beyond_the_cut_is_withheld_not_cut():
    ref = (
        "https://" + "u" * 100 + ":" + "Hunter2!" * 700 + "@db.example/x"
    )  # 5,600 characters of credentials
    out = _clip(ref, 128)
    assert (
        out.startswith("(details withheld; len=") and "Hunter2" not in out
    )  # FAIL-BEFORE: the head, 'u' x 100 plus the start of the password
    inside = _clip("https://" + "u" * 100 + ":" + "Hunter2!" * 115 + "@db.example/x", 128)
    assert "Hunter2" not in inside


def test_the_withheld_hash_is_keyed_and_no_raw_head_is_cached():
    a, b = _clip("x" * 9000, 128, b"a" * 32), _clip("x" * 9000, 128, b"b" * 32)
    assert a != b and re.fullmatch(
        r"\(details withheld; len=9000; sha8=[0-9a-f]{8}\)", a
    )  # FAIL-BEFORE: unkeyed sha256
    import functools

    assert not any(isinstance(v, functools._lru_cache_wrapper) for v in vars(capped).values())


def test_the_marker_passes_a_clipped_bucket_and_a_stale_bucket_leaves_one_trace():
    rows = []
    ca = CappedAudit(lambda kind, **f: rows.append((kind, f)), cap=1)
    long_bucket = "b" * 100 + "\n"
    ca.deny("t", "refused", long_bucket)
    ca.deny("t", "refused", long_bucket)
    marker = next(f for k, f in rows if k == "audit_suppressed")
    assert (
        len(marker["bucket"]) <= 64 and "\n" not in marker["bucket"]
    )  # FAIL-BEFORE: the raw bucket
    rows.clear()
    ca2 = CappedAudit(lambda kind, **f: rows.append((kind, f)), cap=1)
    for b in ("d1", "d2", "d3", "d1", "d1", "d1"):
        ca2.deny("t", "refused", b)
    assert [k for k, _ in rows].count(
        "audit_stale_bucket"
    ) == 1  # FAIL-BEFORE: dropped without a trace


def test_kinds_are_purged_with_their_bucket_and_the_marker_kinds_are_reserved():
    ca = CappedAudit(lambda kind, **f: None, cap=5, max_kinds=1)
    ca.deny("t", "k1", "d1")
    ca.deny("t", "k2", "d2")  # past max_kinds: shares "*"
    ca.deny("t", "k3", "d3")
    assert ("t", "k3", "d3") in ca._n  # FAIL-BEFORE: k1 pinned the only kind slot for ever
    for kind in ("audit_suppressed", "audit_stale_bucket"):
        with pytest.raises(ValueError):
            ca.append("t", kind, "d3")


# ---- 9. row store ---------------------------------------------------------------------------------------------------------------------------------------
def test_a_huge_string_is_refused_by_length_without_encoding_it(monkeypatch):
    import json as _json

    chunks = []
    real = _json.JSONEncoder.iterencode

    def spy(self, o, *a, **k):
        for c in real(self, o, *a, **k):
            chunks.append(len(c))
            yield c

    monkeypatch.setattr(_json.JSONEncoder, "iterencode", spy)
    monkeypatch.setattr(
        _json, "dumps", lambda *a, **k: (_ for _ in ()).throw(AssertionError("encoded"))
    )
    with pytest.raises(ValueError, match="over max_row_bytes"):
        RowStore().put_audited(lambda *a, **k: None, "k", "a", {"v": "x" * 5_000_000})
    assert (
        sum(chunks) < 1000
    )  # FAIL-BEFORE: a 5 MB string was encoded as one chunk before the size was looked at


def test_keys_count_in_the_total_and_an_inflight_write_counts_too():
    rs = RowStore(max_total_bytes=100, max_row_bytes=100)
    rs.put_audited(lambda *a, **k: None, "k", "k" * 80, {})
    with pytest.raises(StoreFull):
        rs.put_audited(lambda *a, **k: None, "k", "j" * 80, {})  # FAIL-BEFORE: a key cost nothing
    rs2 = RowStore(max_total_bytes=150, max_row_bytes=150)
    inside, go, errors = threading.Event(), threading.Event(), []

    def slow(*a, **k):
        inside.set()
        go.wait(5)

    t = threading.Thread(target=lambda: rs2.put_audited(slow, "k", "a", {"v": "x" * 90}))
    t.start()
    assert inside.wait(5)
    try:
        rs2.put_audited(lambda *a, **k: None, "k", "b", {"v": "y" * 90})
    except StoreFull as e:
        errors.append(e)
    go.set()
    t.join(5)
    assert errors  # the row in flight is reserved


def test_a_store_without_a_limit_needs_the_named_opt_out_and_the_contract_checks_full_stores():
    for kw in ({"max_rows": None}, {"max_row_bytes": None}, {"max_total_bytes": None}):
        with pytest.raises(ValueError):
            RowStore(**kw)
        RowStore(**kw, allow_unbounded=True)
    check_rowstore_contract(RowStore, make_small=lambda: RowStore(max_rows=1))

    class Silent(RowStore):
        def put_audited(self, append, kind, key, row):
            if key == "b":
                raise ValueError("not StoreFull")
            super().put_audited(append, kind, key, row)

    with pytest.raises(AssertionError):
        check_rowstore_contract(Silent, make_small=lambda: Silent(max_rows=1))
    assert rowstore.DEFAULT_MAX_ROW_BYTES == 65_536


# ---- 10. loopback name ------------------------------------------------------------------------------------------------------------------------------
def test_localhost_tries_ipv4_then_ipv6_and_an_explicit_address_is_used_alone(monkeypatch):
    import socket

    seen = []

    def fake(addr, *a, **k):
        seen.append(addr[0])
        if addr[0] == "127.0.0.1":
            raise OSError("refused")
        return "s"

    monkeypatch.setattr(socket, "create_connection", fake)
    assert http.checked_connection(("localhost", 9)) == "s" and seen == [
        "127.0.0.1",
        "::1",
    ]  # FAIL-BEFORE: only 127.0.0.1
    seen.clear()
    with pytest.raises(OSError):
        http.checked_connection(("127.0.0.1", 9))
    assert seen == ["127.0.0.1"]


# ---- 6. mutation tooling ---------------------------------------------------------------------------------------------------------------------------
def _raising_tree(tmp_path):
    return _pk_tree(
        tmp_path, "from pk.core import go\n\ndef test_a():\n    assert go(True) is True\n"
    )


def test_a_crash_row_is_good_only_when_the_exception_class_is_the_declared_one(tmp_path):
    root = _raising_tree(tmp_path)
    base = ("src/pk/core.py", "return flag", 'raise ValueError("boom")', "test_a")
    right = Mutant("right", *base, allow_crash=True, crash_type="ValueError")
    wrong = Mutant("wrong", *base, allow_crash=True, crash_type="KeyError")
    res = {
        n: (v, good)
        for n, v, _t, good in run_mutants(
            root, [right, wrong], ["tests/test_core.py"], extra_dirs=(), timeout=120
        )
    }
    assert res["right"] == (Verdict.CRASH, True)
    assert res["wrong"] == (Verdict.CRASH, False)  # FAIL-BEFORE: any exception counted as good
    assert "ValueError" in mr.FIRST_LINES["right"]


def test_allow_crash_without_a_crash_type_is_refused_and_a_truncated_junit_marks_the_mutant_error(
    tmp_path, monkeypatch
):
    with pytest.raises(ValueError):
        Mutant("m", "src/pk/core.py", "a", "b", "test_a", allow_crash=True)
    with pytest.raises(ValueError):
        Mutant("m", "src/pk/core.py", "a", "b", "test_a", crash_type="ValueError")
    root = _raising_tree(tmp_path)

    def truncated(text):
        raise ET.ParseError("no element found")

    monkeypatch.setattr(mr, "first_failure_junit", truncated)
    m = Mutant("m", "src/pk/core.py", "return flag", "return False", "test_a")
    ((_name, v, tid, good),) = run_mutants(
        root, [m], ["tests/test_core.py"], extra_dirs=(), timeout=120
    )
    assert (v, tid, good) == (
        Verdict.ERROR,
        "JUNIT REFUSED",
        False,
    )  # FAIL-BEFORE: ParseError aborted the whole run


def test_taskkill_is_resolved_under_system_root():
    path = Path(mr._taskkill())
    assert path.name.lower() == "taskkill.exe" and path.parent.name.lower() == "system32"
