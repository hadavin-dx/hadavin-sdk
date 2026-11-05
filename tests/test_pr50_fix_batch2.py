"""Fix batch 2 for core PR #50 after the second independent review of fa184e7 (ledger BL-core-pr50-r2-007 to 023).

Every test whose docstring-free comment says FAIL-BEFORE was run against the fa184e7 source and fails there; the tests without that word are
regression guards (they pass on fa184e7 on purpose) and are listed in the batch's handoff note. Look-alikes and secrets are built with chr()
and string parts."""

import json
import re
import sys
import unicodedata
from pathlib import Path

import pytest
from tools.mutation_runner import Mutant, run_mutants

from hadavin_sdk import defaults
from hadavin_sdk.audit import capped
from hadavin_sdk.audit.capped import CappedAudit, _clip, _name, sink_append
from hadavin_sdk.guard import textnorm
from hadavin_sdk.guard.redact import FOLD_NOTE, _Redactor, redact
from hadavin_sdk.guard.runmap import InputTooLarge, redact_text
from hadavin_sdk.runtime.rowstore import RowStore, StoreFull
from hadavin_sdk.runtime.stop_gate import StopGate, StopGateBusy, _label
from hadavin_sdk.testing import mutation as mutmod
from hadavin_sdk.testing.mutation import Verdict, first_failure_junit
from tests.test_promoted_controls import FakeLimits, RecordingSink, _pk_tree

redact_mod = sys.modules[
    "hadavin_sdk.guard.redact"
]  # the package re-exports a function named `redact`
ROOT = Path(__file__).resolve().parents[1]
KEY = "AKIA" + "IOSFODNN7EXAMPLE"


# ---- A. stop gate ------------------------------------------------------------------------------------------------------------------------------
def test_restore_true_then_false_cannot_clear_a_stop_on_an_unaudited_gate():
    g = StopGate(None, unaudited=True)
    g.restore(True)
    with pytest.raises(StopGateBusy):
        g.restore(
            False, by="ops"
        )  # FAIL-BEFORE: cleared silently, no audit row, nothing to say it happened
    assert g.engaged and g.blocked()


def test_restore_false_needs_the_durable_switch_off_and_writes_an_audit_row():
    lim = FakeLimits()
    g = StopGate(lim)
    g.restore(True)
    lim.store.ks = type(lim.store.ks)(on=True)  # an operator's stop is on in the store
    with pytest.raises(StopGateBusy):
        g.restore(False, by="ops")
    assert g.engaged
    lim.store.ks = type(lim.store.ks)(on=False)
    g.restore(False, by="ops")
    assert not g.engaged
    rows = [e for e in lim.audit.intents if e.operation == "restore"]  # FAIL-BEFORE: no row
    assert len(rows) == 1 and rows[0].result == "off" and rows[0].source == "gate"
    g.restore(False, by="ops")  # already off: nothing to audit
    assert len([e for e in lim.audit.intents if e.operation == "restore"]) == 1


def test_a_failed_restore_audit_leaves_the_flag_on():
    lim = FakeLimits()
    g = StopGate(lim)
    g.restore(True)
    lim.audit.down = True
    with pytest.raises(Exception):  # noqa: B017 - AuditUnavailable
        g.restore(False, by="ops")
    assert g.engaged


def test_restore_false_does_not_make_a_release_in_flight_raise_when_no_engage_ran():
    lim = FakeLimits()
    g = StopGate(lim)
    g.restore(True)
    lim.during_reset = lambda: g.restore(
        False, by="ops"
    )  # an operator restore while the reset is in flight
    g.release(
        by="u1"
    )  # FAIL-BEFORE: StopGateBusy("an engage ran during the release") though no engage ran
    assert not g.engaged


def test_a_label_that_starts_with_id_is_hashed_and_the_hash_is_salted():
    fake = "id:0123456789abcdef"
    out = _label(fake)
    assert out != fake and re.fullmatch(
        r"id:[0-9a-f]{32}", out
    )  # FAIL-BEFORE: passed through, impersonating a hash
    import hashlib

    assert (
        out != "id:" + hashlib.sha256(fake.encode()).hexdigest()[:32]
    )  # not a plain hash a dictionary could reverse
    assert _label("José") == _label("José") != _label("Josè")
    assert re.fullmatch(r"id:[0-9a-f]{32}", _label("José"))


def test_release_clears_the_engaged_marker_so_restore_works_after_it():
    lim = FakeLimits()
    g = StopGate(lim)
    g.engage(list, lambda k: "x", by="u1")
    g.release(by="u1")
    g.restore(True)
    g.restore(False, by="ops")  # only possible because release cleared _engaged_here
    assert not g.engaged


# ---- B. outsider text in the append-only audit ----------------------------------------------------------------------------------------------------
def test_a_huge_non_ascii_value_is_pre_clipped_before_the_redactor_sees_it(monkeypatch):
    seen = []
    real = capped.redact_bounded
    monkeypatch.setattr(
        capped, "redact_bounded", lambda text, m: seen.append(len(text)) or real(text, m)
    )
    out = _clip("é\n" * 500_000, 128)
    assert seen and max(seen) <= 128 + 4096, (
        seen
    )  # FAIL-BEFORE: the whole 1,000,000 characters were redacted
    assert len(out) <= 128 and "\n" not in out


def test_a_secret_straddling_the_limit_is_not_shown_as_a_fragment():
    # an e-mail address cut in half is no longer an address, so only redacting BEFORE the clip hides it (a key is caught even in part)
    ref = (
        "x " * 62 + "alice" + "@example.com" + " y" * 50_000
    )  # the address starts at character 124, the limit is 128
    out = _clip(ref, 128)
    assert "alice" not in out and "@ex" not in out, out
    tenant = "x " * 28 + "alice@example.com"  # starts at character 56, the limit is 64
    assert "alice" not in _name(tenant) and "@ex" not in _name(tenant), _name(
        tenant
    )  # FAIL-BEFORE: clipped to 64 first, then redacted: "alice@ex" stayed


def test_a_value_the_redactor_refuses_keeps_its_length_and_a_hash_but_no_content(monkeypatch):
    def refuse(text, m):
        raise InputTooLarge("InputTooLarge")

    monkeypatch.setattr(capped, "redact_bounded", refuse)
    a, b = _clip("secret-one" * 10, 128), _clip("secret-two" * 10, 128)
    assert re.fullmatch(r"\(details withheld; len=100; sha8=[0-9a-f]{8}\)", a), a
    assert a != b and "secret" not in a  # FAIL-BEFORE: both became the same fixed note


def test_control_characters_never_reach_any_audit_field():
    sink = RecordingSink()
    app = sink_append(sink, "r", "d")
    nasty = "a\nb\x1b[31mc\rd e f\x85g\x00h"
    app(
        nasty, tenant=nasty, object_ref=nasty, error_code=nasty, bucket=nasty, suppressed_kind=nasty
    )
    ev = sink.events[0]
    for field in (ev.operation, ev.object_ref, ev.error_code):
        assert not any(unicodedata.category(c) in ("Cc", "Zl", "Zp") for c in field), repr(
            field
        )  # FAIL-BEFORE: newline and ESC survived
    assert _name(nasty).count("\n") == 0


# ---- C. buckets ----------------------------------------------------------------------------------------------------------------------------------------
def test_rotating_three_buckets_cannot_reset_the_cap():
    ca = CappedAudit(lambda kind, **f: None, cap=1)
    assert [ca.append("t", "refused", b) for b in ("d1", "d2", "d3")] == [True, True, True]
    assert (
        ca.append("t", "refused", "d1") is False
    )  # FAIL-BEFORE: d1 had been evicted by the keep-last-two list, so it counted from zero
    assert ca.append("t", "refused", "d1") is False


def test_a_late_event_of_an_old_bucket_never_evicts_a_newer_one():
    ca = CappedAudit(lambda kind, **f: None, cap=1)
    seq = ["2026-11-01", "2026-11-02", "2026-10-31", "2026-11-01"]
    assert [ca.append("t", "refused", b) for b in seq] == [
        True,
        True,
        False,
        False,
    ]  # FAIL-BEFORE: the last was True
    assert ca.suppressed("t", "refused", "2026-11-01") == 1


def test_a_key_flood_on_one_day_does_not_overflow_the_next_day():
    ca = CappedAudit(lambda kind, **f: None, cap=1, max_keys=2)
    for t in "abcd":
        ca.deny(t, "refused", "2026-11-01")  # c and d share the overflow counter of day 1
    ca.deny("e", "refused", "2026-11-02")
    ca.deny("e", "refused", "2026-11-02")
    assert (
        ca.suppressed("e", "refused", "2026-11-02") == 1
    )  # FAIL-BEFORE: e was sent to the overflow counter (0 here)
    assert ca.overflow_suppressed("refused", "2026-11-02") == 0


def test_a_long_bucket_is_clipped_in_the_counter_key_and_the_docstring_is_current():
    ca = CappedAudit(lambda kind, **f: None, cap=1)
    ca.deny("t", "refused", "b" * 100_000)
    assert all(len(k[2]) <= 64 for k in ca._n)  # FAIL-BEFORE: the whole bucket text was a key
    assert "not the current one" not in CappedAudit.suppressed.__doc__


# ---- D. in-place masking: each case decided, none leaked or misaligned -----------------------------------------------------------------------------------
def _fold(t):
    return textnorm.fold(t)


@pytest.mark.parametrize(
    ("line", "expected", "value"),
    [
        (
            "mail josé@example.com now",
            "mail <EMAIL_1> now",
            "jose@example.com",
        ),  # a combining mark inside the value
        (
            "x ́josé@example.coḿ y",
            "x ́<EMAIL_1>́ y",
            "jose@example.com",
        ),  # marks around it stay where they were
        (
            "mail al\u200bice@example.com now",
            "mail <EMAIL_1> now",
            "alice@example.com",
        ),  # a zero-width space inside the local part
        (
            "\u200balice@example.com\u200b",
            "\u200b<EMAIL_1>\u200b",
            "alice@example.com",
        ),  # leading and trailing zero-width spaces
        (
            "mail alice@example.com end",
            "mail <EMAIL_1> end",
            "alice@example.com",
        ),  # no-break spaces
        (
            "key AKIAIOSFODNN7EXAMPLE end",
            "key <APIKEY_1> end",
            KEY,
        ),  # a Kelvin sign inside the value: masked whole
        (
            "a josé@example.com b maría@example.com c",
            "a <EMAIL_1> b <EMAIL_2> c",
            "jose@example.com",
        ),  # two values, offsets of the second
        (
            "Acme™ mail josé@example.com … done",
            "Acme™ mail <EMAIL_1> … done",
            "jose@example.com",
        ),  # signs outside the value stay
        (
            "ﬁle josé@example.com",
            "ﬁle <EMAIL_1>",
            "jose@example.com",
        ),  # a ligature outside the value
        (
            "Cookie: sid=josé@example.com; a=bé",
            "Cookie: <SECRET_1>",
            None,
        ),  # two rounds change the text, a third finds nothing
    ],
)
def test_in_place_masking_cases(line, expected, value):
    r = redact(line)
    assert r.text == expected, (line, r.text)
    assert FOLD_NOTE not in r.text
    if value:
        assert value in r.mapping.values()


def test_a_sign_inside_a_value_withholds_the_line_instead_of_masking_around_it():
    # an ellipsis or a one-half sign INSIDE the matched value is a flagged character: the whole line goes, never a half-masked value
    for ln in ("mail jose…@example.com", "mail jos½@example.com"):
        assert redact(ln).text.startswith(FOLD_NOTE), ln


def test_the_cases_that_fall_back_to_withholding_leak_nothing():
    for ln in ("mail jose…@example.com", "key " + chr(0x410) + KEY[1:] + " x"):
        out = redact(ln).text
        assert "jose" not in _fold(out) and KEY not in _fold(out), out


def test_four_rounds_that_never_converge_fall_through_to_the_withhold(monkeypatch):
    calls = []

    def never_done(self, body, folded, where, alike, only=None):
        calls.append(body)
        return body + " "

    monkeypatch.setattr(_Redactor, "_mask_in_place", never_done)
    out = redact("mail josé@example.com now").text
    assert len(calls) == 4  # FAIL-BEFORE (mutant): a loop that is not capped at four rounds
    assert out.startswith(FOLD_NOTE) and "jose@example.com" not in _fold(out)


def test_the_malformed_offset_is_caught_by_a_value_in_front_of_and_behind_other_text():
    # the output must be the original text with ONLY the value replaced: every other character, accents included, in its place
    ln = "café été josé@example.com naïve über"
    assert redact(ln).text == "café été <EMAIL_1> naïve über"


def test_a_multi_line_value_that_only_the_fold_sees_is_replaced_not_left(monkeypatch):
    pat = re.compile(r"BEGINX\nKEY=([A-Z0-9]{8})")
    monkeypatch.setattr(redact_mod, "PATTERNS", [*redact_mod.PATTERNS, ("SECRET", pat)])
    text = "BEGINX\nKEY=ABCD" + chr(0x412) + "EFG\nafter café"
    out = redact(text).text
    assert "ABCD" not in _fold(out) and "EFG" not in _fold(out), (
        out
    )  # FAIL-BEFORE: the match starts on an ASCII line that nothing treated
    assert out.endswith("after café")


def test_the_budget_is_checked_inside_the_per_line_work(monkeypatch):
    seen = []
    real = _Redactor._over_budget
    monkeypatch.setattr(
        _Redactor, "_over_budget", staticmethod(lambda d: seen.append(1) or real(d))
    )
    redact("mail josé@example.com now")
    assert (
        len(seen) >= 6
    )  # the scan, two sweeps, the suspect line, the rounds and the alignment each ask


def test_line_hits_asks_for_the_budget_once_per_pattern(monkeypatch):
    seen = []
    real = _Redactor._over_budget
    monkeypatch.setattr(
        _Redactor, "_over_budget", staticmethod(lambda d: seen.append(1) or real(d))
    )
    _Redactor(None)._line_hits("café x", [0], 1e18)
    assert len(seen) == len(redact_mod.PATTERNS)


# ---- E. shared deadline, benign corpus with the signs ------------------------------------------------------------------------------------------
def test_one_deadline_covers_the_text_and_all_its_views(monkeypatch):
    seen = []
    real = redact_mod.redact

    def spy(text, **kw):
        seen.append(kw.get("_deadline"))
        return real(text, **kw)

    monkeypatch.setattr("hadavin_sdk.guard.runmap.redact", spy)
    redact_text("mail josé@example.com %41KIA" + "IOSFODNN7EXAMPLE café", {})
    assert (
        len(seen) >= 2 and all(d is not None for d in seen) and len(set(seen)) == 1
    )  # FAIL-BEFORE: no deadline passed, 6 s per view


def test_a_spent_budget_refuses_before_any_line_is_treated(monkeypatch):
    calls = []
    real = _Redactor._folded_line
    monkeypatch.setattr(
        _Redactor, "_folded_line", lambda self, *a: calls.append(1) or real(self, *a)
    )
    monkeypatch.setattr(defaults, "REDACT_BUDGET_S", -1.0)
    text = "".join(f"user{i} café: josé{i}@exemple.fr" + chr(10) for i in range(3_000))
    with pytest.raises(InputTooLarge):
        redact(text)
    assert calls == []  # a work count, not a clock: nothing was treated once the budget was spent


SIGN_LINES = [  # lines with signs the fold changes into several characters or into non-ASCII text
    "Acme™ contact josé@example.com",  # TM
    "wait… mail josé@example.com",  # ellipsis
    "ﬁle sent to josé@example.com",  # ligature
    "area 25 m² contact josé@example.com",  # superscript digit
    "½ cup, mail josé@example.com",  # one-half sign (folds to a fraction slash: not ASCII)
    "contact josé@example.com — thanks",  # em dash
]


def test_withhold_rate_on_lines_with_signs_is_measured_and_pinned():
    withheld = [ln for ln in SIGN_LINES if FOLD_NOTE in redact(ln).text]
    # honest number: 0 of 6 since batch 3 (the one-half sign folds to a fraction slash, which is now mapped to "/" and masked around;
    # TM, ellipsis, ligature, superscript are masked in place, the em dash is not changed by the fold). With the 22 lines of the first
    # corpus: 0 of 28. A sign INSIDE a value, or a full-width slash anywhere, still withholds the line (see test_pr50_fix_batch3.py).
    assert withheld == [], withheld


# ---- F. row store ------------------------------------------------------------------------------------------------------------------------------------
def test_the_total_cap_refuses_the_row_that_would_pass_it_and_frees_on_delete():
    rs = RowStore(max_total_bytes=200, max_row_bytes=150)
    rs.put_audited(lambda *a, **k: None, "k", "a", {"v": "x" * 100})
    with pytest.raises(StoreFull):
        rs.put_audited(
            lambda *a, **k: None, "k", "b", {"v": "y" * 100}
        )  # FAIL-BEFORE: no aggregate cap
    rs.delete_audited(lambda *a, **k: None, "k", "a")
    rs.put_audited(lambda *a, **k: None, "k", "b", {"v": "y" * 100})
    rs.update_audited(lambda *a, **k: None, "k", "b", {"v": "z" * 50})
    rs.put_audited(lambda *a, **k: None, "k", "c", {"v": "w" * 100})
    for bad in (0, 1, -5, 1.5, True):
        with pytest.raises(ValueError):
            RowStore(max_total_bytes=bad)


def test_the_row_size_is_counted_while_encoding(monkeypatch):
    import json as _json

    called = []
    real = _json.JSONEncoder.iterencode

    def spy(self, o, *a, **k):
        for chunk in real(self, o, *a, **k):
            called.append(len(chunk))
            yield chunk

    monkeypatch.setattr(_json.JSONEncoder, "iterencode", spy)
    rs = RowStore(max_row_bytes=100)
    with pytest.raises(ValueError):
        rs.put_audited(lambda *a, **k: None, "k", "a", {"rows": ["x" * 40] * 10_000})
    assert sum(called) < 300, sum(
        called
    )  # FAIL-BEFORE: the whole 400 KB were encoded before the size was looked at


# ---- H. mutation runner ----------------------------------------------------------------------------------------------------------------------------
def test_a_refused_junit_marks_that_mutant_error_and_the_run_goes_on(tmp_path, monkeypatch):
    from tools import mutation_runner

    body = "from pk.core import go\n\ndef test_a():\n    assert go(True) is True\n"
    root = _pk_tree(tmp_path, body)
    real = mutation_runner.first_failure_junit
    state = {"n": 0}

    def flaky(text):
        state["n"] += 1
        if state["n"] == 1:
            raise ValueError("refused")
        return real(text)

    monkeypatch.setattr(mutation_runner, "first_failure_junit", flaky)
    m1 = Mutant("m1", "src/pk/core.py", "return flag", "return False", "test_")
    m2 = Mutant("m2", "src/pk/core.py", "return flag", "return False", "test_")
    res = run_mutants(root, [m1, m2], ["tests/test_core.py"], extra_dirs=(), timeout=120)
    got = {n: (v, tid) for n, v, tid, _ in res}
    assert got["m1"] == (
        Verdict.ERROR,
        "JUNIT REFUSED",
    )  # FAIL-BEFORE: the ValueError aborted the whole run
    assert got["m2"][0] is Verdict.KILLED


def test_a_junit_text_over_the_ceiling_is_refused():
    with pytest.raises(ValueError):
        first_failure_junit(
            "<testsuite>" + " " * getattr(mutmod, "MAX_JUNIT_CHARS", 8_000_000) + "</testsuite>"
        )  # FAIL-BEFORE: no size cap


# ---- G. http loopback --------------------------------------------------------------------------------------------------------------------------------
def test_the_loopback_skip_connects_to_a_literal_address(monkeypatch):
    import socket

    from hadavin_sdk.guard import http

    seen = []
    monkeypatch.setattr(socket, "create_connection", lambda addr, *a, **k: seen.append(addr) or "s")
    for host in ("localhost", "LocalHost.", "127.0.0.1", "::1"):
        http.checked_connection((host, 9))
    assert seen == [
        ("127.0.0.1", 9),
        ("127.0.0.1", 9),
        ("127.0.0.1", 9),
        ("::1", 9),
    ]  # FAIL-BEFORE: ("localhost", 9) was resolved by a resolver


# ---- I. pins -------------------------------------------------------------------------------------------------------------------------------------------
def test_redact_and_limits_are_not_byte_copy_files_and_the_docs_say_so():
    manifest = json.loads((ROOT / "tests/fixtures/textnorm_manifest.json").read_text("utf-8"))
    for rel in ("src/hadavin_sdk/guard/redact.py", "src/hadavin_sdk/limits.py"):
        assert rel not in manifest["files"], rel
    docs = (ROOT / "docs/promoted-controls.md").read_text("utf-8")
    assert (
        "NOT in the manifest and NOT byte-copy files" in docs
        and "core package at one commit" in docs
    )


def test_the_batch_one_module_docstring_names_the_tests_that_pass_on_old_code():
    text = (ROOT / "tests/test_pr50_fix_batch.py").read_text("utf-8")
    head = text.split('"""', 2)[1]
    assert (
        "pass on" in head
        and "test_attacks_are_still_withheld_whole_and_never_emitted_folded" in head
    )


def test_the_text_leaks_docstring_is_clean():
    from hadavin_sdk.guard.egress_text import text_leaks

    doc = text_leaks.__doc__
    assert "MemoryError-free" not in doc and "ANY other exception" in doc
