"""Fix batch for core PR #50 after the first independent review (ledger BL-core-pr50-r2-001 to 006).

Every test here was run against 2e8a28c (the reviewed head) and fails there EXCEPT the regression guards that pass on it on purpose:
test_attacks_are_still_withheld_whole_and_never_emitted_folded, test_native_digits_of_a_value_are_masked_in_place_not_withheld, and the
tests that read the repository's docs, manifest, CHANGELOG or tools/ (those fail against the old repository state, not the old source:
test_every_promoted_file_is_pinned_or_named_as_pinned_by_core_commit, test_the_guarantee_sentence_states_its_own_limit,
test_the_unicode_version_dependence_of_the_fold_is_documented_and_checked, test_the_runner_wires_pinned_so_another_failing_test_is_other_test).
No wall-clock
assertion except one ratio test marked ``perf`` (the count-based test beside it is the deterministic one). Look-alikes and secrets are
built from parts with ``chr()``."""

import json
import re
import socket
import threading
import time
import unicodedata
from pathlib import Path

import pytest
from tools.mutation_runner import Mutant, run_mutants

from hadavin_sdk import defaults
from hadavin_sdk.audit.capped import CappedAudit, sink_append
from hadavin_sdk.guard import egress_text, http, textnorm
from hadavin_sdk.guard.egress_text import LeakPolicy
from hadavin_sdk.guard.redact import FOLD_NOTE, _Redactor, redact
from hadavin_sdk.guard.runmap import InputTooLarge
from hadavin_sdk.models import KillSwitch as StoredKillSwitch
from hadavin_sdk.runtime import config_view
from hadavin_sdk.runtime.rowstore import RowStore
from hadavin_sdk.runtime.stop_gate import StopGate, StopGateBusy, _label
from hadavin_sdk.testing.contracts import check_rowstore_contract
from hadavin_sdk.testing.mutation import Verdict, first_failure_junit
from tests.test_promoted_controls import FakeLimits, RecordingSink, _pk_tree

ROOT = Path(__file__).resolve().parents[1]
KEY = "AKIA" + "IOSFODNN7EXAMPLE"


def _digits(base: int, s: str) -> str:
    return "".join(chr(base + int(c)) if c.isdigit() else c for c in s)


# ---- 1. drift: every promoted file is pinned, or the docs say why not -----------------------------------------------------------------------------
PINNED = (
    "src/hadavin_sdk/runtime/rowstore.py",
    "src/hadavin_sdk/runtime/config_view.py",
    "src/hadavin_sdk/audit/capped.py",
    "src/hadavin_sdk/testing/mutation.py",
    "src/hadavin_sdk/testing/contracts.py",
    "tools/mutation_runner.py",
)
UNPINNED = ()  # batch 2 pinned redact.py and limits.py too (see test_pr50_fix_batch2.py)


def test_every_promoted_file_is_pinned_or_named_as_pinned_by_core_commit():
    manifest = json.loads((ROOT / "tests/fixtures/textnorm_manifest.json").read_text("utf-8"))
    for rel in PINNED:
        assert rel in manifest["files"], rel  # FAIL-BEFORE: only five files were pinned
    if not (ROOT / "CHANGELOG.md").exists():
        pytest.skip("the mutation copies do not carry the CHANGELOG")
    docs = (ROOT / "docs/promoted-controls.md").read_text("utf-8")
    log = (ROOT / "CHANGELOG.md").read_text("utf-8")
    for rel in UNPINNED:
        assert rel not in manifest["files"]
        name = rel.removeprefix("src/hadavin_sdk/")
        assert (
            f"`{name}` is NOT pinned by hash" in docs and f"`{name}` is NOT pinned by hash" in log
        ), rel
    for rel in PINNED:
        assert f'"core_path": "{rel}"' in docs, rel  # a core_copies.json row for every pinned file


# ---- 2. the fold pass does not withhold legitimate non-ASCII lines -----------------------------------------------------------------------------------
BENIGN_EMAIL = [  # a legitimate accented address inside a sentence of another script: ONE value to mask, the sentence to keep
    "écrire à josé@exemple.fr bientôt",
    "Contacto: señor.muñoz@correo.es para más información",
    "Bitte an jürgen.müller@beispiel.de schreiben, danke",
    "Escreva para joão.conceição@exemplo.pt hoje",
    "Napište na petr.novák@příklad.cz prosím",
    "Liên hệ nguyễn.văn@ví-dụ.vn ngay",
    "للتواصل راسلنا على josé@example.com شكرا لكم",
    "संपर्क करें josé@example.com धन्यवाद",
    "お問い合わせは" + chr(0x3000) + "josé@example.com" + chr(0x3000) + "まで",
    "联系" + chr(0x3000) + "señora@example.com" + chr(0x3000) + "谢谢",
    "ติดต่อ josé@example.com ขอบคุณ",
    "Привет, пишите на josé@example.com пожалуйста",
]
BENIGN_PLAIN = [  # no value in them at all: must come out unchanged
    "Café résumé naïve façade Zürich Ångström",
    "الطلب رقم " + _digits(0x660, "42") + " تم الشحن",
    "संस्करण " + _digits(0x966, "1") + "." + _digits(0x966, "2"),
    "订单 " + _digits(0xFF10, "123") + " 已发货",
    "السعر " + _digits(0x660, "1299") + " ريال",
    "यह एक सामान्य वाक्य है जिसमें कोई रहस्य नहीं है",
    "これは通常の文章です。秘密はありません。",
    "Ceci est une très longue phrase avec des accents éèêë àâä ôö ùûü",
    "التاريخ " + _digits(0x660, "2026") + "-" + _digits(0x660, "11") + "-" + _digits(0x660, "05"),
    "ภาษาไทยเป็นภาษาที่สวยงามมาก",
]


def test_benign_multilingual_corpus_has_a_zero_false_withhold_rate():
    corpus = BENIGN_EMAIL + BENIGN_PLAIN
    withheld = [ln for ln in corpus if FOLD_NOTE in redact(ln).text]
    rate = len(withheld) / len(corpus)
    assert rate == 0.0, (
        rate,
        withheld,
    )  # FAIL-BEFORE: every accented-address line was withheld whole
    for ln in BENIGN_PLAIN:
        assert redact(ln).text == ln, ln
    for ln in BENIGN_EMAIL:
        r = redact(ln)
        assert "<EMAIL_1>" in r.text and "@" not in r.text, (ln, r.text)
        # only the value went: the words before and after it are still there, as written
        before, after = re.split(r"\S+@\S+", ln, maxsplit=1)
        assert r.text.startswith(before) and r.text.endswith(after), (ln, r.text)
        assert textnorm.fold(r.mapping["<EMAIL_1>"]).count("@") == 1


def test_native_digits_of_a_value_are_masked_in_place_not_withheld():
    ln = "card " + _digits(0x660, "4111 1111 1111 1111") + " thanks, café"
    r = redact(ln)
    assert FOLD_NOTE not in r.text and "café" in r.text and "thanks" in r.text
    assert not re.search(r"\d{4}", textnorm.fold(r.text)), r.text


def test_attacks_are_still_withheld_whole_and_never_emitted_folded():
    cyr = chr(0x410) + "KIA" + "IOSFODNN7EXAMPLE"
    fw = "<!channel>".translate({ord(c): ord(c) + 0xFEE0 for c in "<>!abcdefghijklmnopqrstuvwxyz"})
    for ln in (f"key {cyr} {fw}", f"{fw} {cyr}", "mail al" + chr(0x456) + "ce@example.com now"):
        out = redact(ln).text
        assert out.startswith(FOLD_NOTE), (ln, out)
        assert KEY not in textnorm.fold(out) and "<!" not in textnorm.fold(out)
    # a hidden value next to accented text: the look-alike makes it an attack, the whole line goes
    assert FOLD_NOTE in redact("café " + cyr).text


def test_a_lookalike_copy_of_a_value_that_also_stands_in_clear_is_still_a_hit():
    ln = f"first {KEY} then second {chr(0x410)}{KEY[1:]}"
    out = redact(ln).text
    assert KEY not in textnorm.fold(out), (
        out
    )  # FAIL-BEFORE: a set compare saw "nothing new"; the look-alike copy stayed in the text


# ---- 3. outsider text is clipped and redacted before the append-only audit ---------------------------------------------------------------------
def test_ref_key_and_error_code_are_redacted_and_clipped_before_the_audit():
    sink = RecordingSink()
    app = sink_append(sink, "r", "d")
    app("refused", tenant="t1", object_ref=KEY + "x" * 100_000, error_code=KEY + "y" * 100_000)
    app("refused", tenant="t1", key=f"password=hunter2xyz-{KEY}" + "z" * 100_000)
    for ev in sink.events:
        assert KEY not in ev.object_ref and KEY not in (ev.error_code or ""), ev
        assert "hunter2xyz" not in ev.object_ref
        assert len(ev.object_ref) <= 64 + 1 + 128 and len(ev.error_code or "") <= 96, ev


def test_the_escaped_tenant_is_clipped_after_the_escaping():
    sink = RecordingSink()
    sink_append(sink, "r", "d")("k", tenant="|" * 200 + "%" * 200, key="a")
    tenant_part = sink.events[0].object_ref.rsplit("|", 1)[0]
    assert len(tenant_part) <= 64 and "|" not in tenant_part, (
        tenant_part
    )  # FAIL-BEFORE: 64 x 3 = 192
    assert not re.search(r"%(?![0-9A-F]{2})", tenant_part), (
        tenant_part
    )  # no escape cut in the middle


def test_rowstore_caps_keys_and_rows_and_the_audited_key_is_clipped():
    rs = RowStore()
    with pytest.raises(ValueError):
        rs.put_audited(lambda *a, **k: None, "k", "k" * 257, {})
    with pytest.raises(ValueError):
        rs.put_audited(lambda *a, **k: None, "k", "ok", {"blob": "x" * 100_000})
    assert rs.keys() == []
    rs.put_audited(
        lambda *a, **k: None, "k", "ok", {"blob": "x" * 60_000}
    )  # inside the default 65,536
    big = RowStore(max_row_bytes=None)
    big.put_audited(lambda *a, **k: None, "k", "ok", {"blob": "x" * 100_000})
    small = RowStore(max_row_bytes=10)
    with pytest.raises(ValueError):
        small.put_audited(lambda *a, **k: None, "k", "k1", {"a": "1234567890"})
    for bad in (0, -1, 1.5, True):
        with pytest.raises(ValueError):
            RowStore(max_row_bytes=bad)
        with pytest.raises(ValueError):
            RowStore(max_key_chars=bad)
    sink = RecordingSink()
    store = RowStore()
    store.put_audited(sink_append(sink, "r", "d", intent=True), "row_added", KEY, {"a": 1})
    assert KEY not in sink.intents[0].object_ref


def test_a_late_event_of_the_previous_bucket_neither_resets_nor_bypasses_the_cap():
    seen = []
    ca = CappedAudit(lambda kind, **f: seen.append((kind, f.get("bucket"))), cap=2)
    assert ca.append("t", "refused", "d1") and ca.append("t", "refused", "d1")
    assert ca.append("t", "refused", "d2")  # the new bucket has its own count
    assert (
        ca.append("t", "refused", "d1") is False
    )  # FAIL-BEFORE: the purge for d2 had reset d1, so this was allowed
    assert ca.suppressed("t", "refused", "d1") == 1 and ca.suppressed("t", "refused") == 0
    for bucket in ("d3", "d4"):
        ca.append("t", "refused", bucket)
    assert ca.suppressed("t", "refused", "d1") == 0  # three buckets back: purged


def test_a_non_string_tenant_is_a_name_not_a_type_error():
    ca = CappedAudit(lambda kind, **f: None, cap=1)
    for tenant in (None, 7, b"x", ("a",)):
        assert ca.append(tenant, "refused", "d1") in (
            True,
            False,
        )  # FAIL-BEFORE: TypeError on the slice
        ca.deny(tenant, "refused", "d1")
    assert ca.suppressed(None, "refused", "d1") >= 0


# ---- 4. the fold pass is bounded -------------------------------------------------------------------------------------------------------------------
def test_many_short_non_ascii_lines_cost_no_per_line_pattern_runs(monkeypatch):
    calls = []
    real_hits, real_line = _Redactor._dry_hits, _Redactor._folded_line
    monkeypatch.setattr(
        _Redactor, "_dry_hits", staticmethod(lambda t: calls.append(1) or real_hits(t))
    )
    monkeypatch.setattr(
        _Redactor, "_folded_line", lambda self, ln: calls.append(1) or real_line(self, ln)
    )
    out = redact("é\n" * 20_000).text
    assert out == "é\n" * 20_000
    assert calls == [], len(
        calls
    )  # FAIL-BEFORE: 2 runs of every pattern for each of the 20,000 lines


def test_the_fold_scan_stops_at_the_time_budget_with_input_too_large(monkeypatch):
    monkeypatch.setattr(defaults, "REDACT_BUDGET_S", -1.0)
    with pytest.raises(InputTooLarge):
        redact("café josé@example.com\n" * 50)  # FAIL-BEFORE: no check inside the fold pass


@pytest.mark.perf
def test_130k_short_non_ascii_lines_cost_a_small_multiple_of_ascii_lines():
    def timed(text):
        best = 1e9
        for _ in range(2):
            t0 = time.perf_counter()
            redact(text)
            best = min(best, time.perf_counter() - t0)
        return best

    ascii_s, non_s = timed("e\n" * 130_000), timed("é\n" * 130_000)
    assert non_s < 5 * ascii_s + 0.5, (ascii_s, non_s)  # the reviewed head took about 9x


# ---- 5. the stop gate cannot be cleared or run without an audit ---------------------------------------------------------------------------------
def test_a_gate_without_an_audit_trail_must_say_so():
    with pytest.raises(ValueError):
        StopGate()  # FAIL-BEFORE: allowed, and engage/release wrote nothing
    with pytest.raises(ValueError):
        StopGate(None)
    assert StopGate(None, unaudited=True).blocked() is False
    assert StopGate(FakeLimits()).blocked() is False


def test_restore_false_cannot_clear_a_stop_this_process_engaged():
    lim = FakeLimits()
    g = StopGate(lim)
    g.engage(list, lambda k: "x", by="u1")
    with pytest.raises(StopGateBusy):
        g.restore(False)  # FAIL-BEFORE: silently cleared the flag, no audit
    assert g.engaged and g.blocked()
    lim.store.ks = StoredKillSwitch(
        on=False
    )  # an operator reset the durable switch behind the gate's back
    with pytest.raises(StopGateBusy):
        g.restore(False)  # still refused: only the audited release clears what this process engaged
    lim.store.ks = StoredKillSwitch(on=True)
    g.release(by="u1")
    g.restore(False)  # nothing engaged here any more
    g.restore(True)
    assert g.engaged
    g.restore(False)  # a restart restoring "off" from persisted state
    assert not g.engaged


def test_restore_false_is_refused_during_a_sweep_and_restore_true_wins_over_a_release_in_flight():
    lim = FakeLimits()
    g = StopGate(lim)
    inside, go, errors = threading.Event(), threading.Event(), []

    def undo(k):
        inside.set()
        go.wait(5)
        return "ok"

    t = threading.Thread(target=lambda: g.engage(lambda: ["a"], undo, by="u1"))
    t.start()
    assert inside.wait(5)
    try:
        g.restore(False)
    except StopGateBusy as e:
        errors.append(e)
    go.set()
    t.join(5)
    assert errors and g.engaged
    # a release whose reset is in flight while restore(True) runs does not clear the flag
    g2 = StopGate(lim2 := FakeLimits())
    g2.restore(True)
    lim2.during_reset = lambda: g2.restore(True)
    with pytest.raises(StopGateBusy):
        g2.release(by="u1")
    assert g2.engaged


def test_odd_principals_keep_a_distinct_audit_label_instead_of_a_question_mark():
    a, b = _label("José"), _label("Josè")
    assert re.fullmatch(r"id:[0-9a-f]{32}", a) and a != b  # FAIL-BEFORE: both were "?"
    assert re.fullmatch(r"id:[0-9a-f]{32}", _label("+"))
    assert re.fullmatch(r"id:[0-9a-f]{32}", _label("x" * 200))
    assert _label("alice smith") == "alice smith"
    for hostile in ("bad\nlabel; DROP", "", 7, None, "tab\there"):
        assert _label(hostile) == "?", hostile
    lim = FakeLimits()
    StopGate(lim).engage(list, lambda k: "", by="José")
    assert lim.log == [("stop", a)]


# ---- 6. minors ----------------------------------------------------------------------------------------------------------------------------------
def test_the_loopback_skip_connects_to_the_checked_host(monkeypatch):
    seen = []
    monkeypatch.setattr(
        socket, "create_connection", lambda addr, *a, **k: seen.append(addr) or "sock"
    )
    assert http.checked_connection(("LocalHost.", 8080)) == "sock"
    assert seen == [("127.0.0.1", 8080)]  # FAIL-BEFORE: connected to "LocalHost." as written


def test_junit_with_a_doctype_or_entity_is_refused_not_parsed():
    bomb = '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><testsuite><testcase classname="t" name="n"/></testsuite>'
    with pytest.raises(ValueError):
        first_failure_junit(bomb)  # FAIL-BEFORE: parsed
    ok = '<testsuite><testcase classname="tests.t" name="n"><failure message="m">E   assert 1 == 2</failure></testcase></testsuite>'
    assert first_failure_junit(ok) == ("tests/t::n", "E   assert 1 == 2")


def test_the_runner_wires_pinned_so_another_failing_test_is_other_test(tmp_path):
    body = "from pk.core import go\n\ndef test_a():\n    assert go(True) is True\n\ndef test_b():\n    assert go(True) is True\n"
    root = _pk_tree(tmp_path, body)
    base = ("m", "src/pk/core.py", "return flag", "return False", "test_")
    other = Mutant(*base, pinned="tests/test_core::test_does_not_exist")
    same = Mutant("m2", *base[1:], pinned="tests/test_core::test_a")
    res = run_mutants(root, [other, same], ["tests/test_core.py"], extra_dirs=(), timeout=120)
    verdicts = {name: v for name, v, _tid, _good in res}
    assert verdicts["m"] is Verdict.OTHER_TEST  # FAIL-BEFORE: Mutant had no pinned field
    assert verdicts["m2"] is Verdict.KILLED  # the pinned test is the one that failed first


def test_the_contract_also_checks_update_and_delete():
    check_rowstore_contract(RowStore)

    class WritesBeforeAudit(RowStore):
        def update_audited(self, append, kind, key, row):
            self._rows[key] = row  # the write first: the contract must notice
            super().update_audited(append, kind, key, row)

    with pytest.raises(AssertionError):
        check_rowstore_contract(lambda: WritesBeforeAudit())


def test_config_view_has_no_dead_leaf_entry_and_names_its_depth_honestly():
    assert frozenset not in config_view._LEAF
    deep: object = 1
    for _ in range(config_view.MAX_DEPTH + 2):
        deep = [deep]
    with pytest.raises(TypeError, match="levels below its top value"):
        config_view.freeze(deep)


def test_text_leaks_fails_closed_on_any_exception(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("policy exploded")

    monkeypatch.setattr(egress_text, "check_text", boom)
    assert (
        egress_text.text_leaks("hello", policy=LeakPolicy.payments()) is True
    )  # FAIL-BEFORE: RuntimeError


def test_the_guarantee_sentence_states_its_own_limit():
    docs = (ROOT / "docs/promoted-controls.md").read_text("utf-8")
    sentence = docs[docs.index("**Guarantee, both presets") :].split("The price:")[0]
    assert (
        "does NOT promise" in sentence
        and "IN THOSE FORMS" in sentence
        and "residual list" in sentence
    )


def test_the_unicode_version_dependence_of_the_fold_is_documented_and_checked():
    docs = (ROOT / "docs/promoted-controls.md").read_text("utf-8")
    assert "Unicode version" in docs and "unassigned" in docs
    # the property the docs state: an unassigned code point folds away, whatever the build says it is
    cn = next(c for c in map(chr, range(0x30000, 0x40000)) if unicodedata.category(c) == "Cn")
    assert textnorm.fold("a" + cn + "b") == "ab"
