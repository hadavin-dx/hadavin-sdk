"""Decisions, API cases (spec 6.5, 6.6, 7, 8). The page cases land in WP6."""

from __future__ import annotations

import copy
import threading

import pytest
from queue_helpers import GOOD_FIELDS, REASON, approve, assertive_all, new_item, reject, sha

from conftest import settings_for_tests
from intake import decisions, flags, workqueue
from intake.codes import Refused
from intake.content_code import content_code

ZW = chr(0x200B)  # zero-width space, built at run time (no invisible character in a tracked file)


def refused(fn, *a, **k) -> str:
    with pytest.raises(Refused) as e:
        fn(*a, **k)
    return e.value.code


def _decisions(s):
    with workqueue.opened(s) as c:
        return [dict(r) for r in c.execute("SELECT * FROM decisions ORDER BY seq")]


# ---- reason rule (6.6) ---------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "text,ok",
    [
        ("looks fine to me", True),
        ("x" * 10, True),  # ten identical characters: allowed, a person's choice
        ("a" * 500, True),
        ("a" * 501, False),  # more than reason_max_chars in all
        (" " * 10, False),
        ("\t" * 10, False),
        ("abc   def", False),  # eight non-whitespace characters
        ("abcdefghi", False),  # nine visible characters: one under the minimum
        ("abcde fghij", True),  # ten non-whitespace characters, one space between
        ("", False),
        (None, False),
        (12345678901, False),
        ("valid reason" + ZW, False),  # zero-width space
        ("valid" + ZW * 5 + "x", False),
        ("valid reason" + chr(0xFEFF), False),
        ("valid reason" + chr(0x202E), False),  # bidi override (format character)
        ("valid reason\n", False),  # control character
        ("valid reason" + chr(0), False),
        ("valid reason" + chr(0x7F), False),
        ("valid reason" + chr(0x85), False),  # C1 control
        ("a valid reason" + chr(0x3164), False),  # blank-looking Hangul filler
        ("a valid reason" + chr(0x2028), False),
        ("zurück geprüft ok", True),  # ordinary non-ASCII text
        ("zuru" + chr(0x308) + "ck gepruft ok", True),  # a decomposed accent is composed first (NFC)
        ("valid reason " + chr(0x301), False),  # a stray combining mark
        ("valid reason" + chr(0xFE0F), False),  # variation selector
        ("valid reason" + chr(0x34F), False),  # combining grapheme joiner
        ("a valid reason" + chr(0x378), False),  # unassigned code point: refused by default (allowlist)
        ("a valid reason" + chr(0xE000), False),  # private use
        ("a valid reason" + chr(0xD800), False),  # lone surrogate
        ("a valid reason" + chr(0x2800), False),  # braille blank
        ("a valid reason" + chr(0xA0), True),  # a no-break space is an ordinary space (Zs)
    ],
)
def test_reason_vectors(intake_settings, text, ok):
    assert decisions.valid_reason(intake_settings, text) is ok


def test_reason_whitespace_does_not_count_toward_the_minimum(intake_settings):
    assert not decisions.valid_reason(intake_settings, " a " * 5)  # five visible characters
    assert decisions.valid_reason(intake_settings, " a " * 10)


# ---- may_approve ---------------------------------------------------------------------------------------------------------------------------
def _it(s, flags_=(), fields=GOOD_FIELDS, name="m"):
    from test_content_code import item

    return item(fields=fields, flags=flags_, state="NEEDS_PERSON" if flags_ else "READY")


@pytest.mark.parametrize("code", flags.reject_only_codes())
def test_every_reject_only_code_is_refused_by_may_approve(code, tmp_path):
    s = settings_for_tests(tmp_path)
    it = _it(s, (code,))
    assert not decisions.may_approve(s, it, REASON)
    assert not decisions.may_approve(s, it, None)
    assert decisions.approve_refusal(s, it, REASON).code == "reject_only"


def test_may_approve_rules(tmp_path):
    s = settings_for_tests(tmp_path)
    assert decisions.may_approve(s, _it(s), None) and decisions.may_approve(s, _it(s), REASON)
    d06 = _it(s, ("D06",))
    assert (
        not decisions.may_approve(s, d06, None)
        and not decisions.may_approve(s, d06, "short")
        and not decisions.may_approve(s, d06, " " * 12)
    )
    assert decisions.may_approve(s, d06, REASON)
    assert not decisions.may_approve(s, _it(s, fields=None), REASON)  # no fields
    bad = copy.deepcopy(GOOD_FIELDS)
    bad["currency"] = "XXX"
    assert not decisions.may_approve(s, _it(s, fields=bad), REASON)  # fails the 6.2 validators
    bad = copy.deepcopy(GOOD_FIELDS)
    bad["total_minor"] = True
    assert not decisions.may_approve(s, _it(s, fields=bad), REASON)
    assert not decisions.may_approve(s, _it(s, ("D06", "D10")), REASON)  # one reject-only flag among several
    assert not decisions.may_approve(s, _it(s, ("NOPE",)), REASON)  # an unknown flag is not approvable


# ---- decide: approve -----------------------------------------------------------------------------------------------------------------------
def test_approve_a_ready_item_without_a_reason(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s)
    d = approve(s, it)
    assert (d.decision, d.approver, d.reason, d.content_code, d.item_uid) == ("approve", "ap-a", None, content_code(it), it.uid)
    got = workqueue.get(s, it.id)
    assert got.state == "APPROVED" and got.version == it.version + 1
    assert _decisions(s) == [{"seq": d.seq, "item_uid": it.uid, "decision": "approve", "approver": "ap-a", "reason": None,
                              "content_code": content_code(it), "at": d.at}]  # fmt: skip


def test_a_blank_reason_field_on_a_ready_approve_means_no_reason(tmp_path):
    s = settings_for_tests(tmp_path)
    assert approve(s, new_item(s), "").reason is None


def test_a_supplied_but_invalid_reason_is_refused_even_for_a_ready_item(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s)
    for bad in (" " * 10, "short", "ok reason" + ZW, "a" * 501):
        assert refused(approve, s, it, bad) == "invalid_reason"
    assert workqueue.get(s, it.id).state == "READY" and _decisions(s) == []


def test_d06_approve_needs_a_valid_reason_and_keeps_it(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s, flags=["D06"])
    assert refused(approve, s, it, None) == "invalid_reason"
    assert refused(approve, s, it, "tiny") == "invalid_reason"
    d = approve(s, it, REASON)
    assert d.reason == REASON and workqueue.get(s, it.id).state == "APPROVED"


@pytest.mark.parametrize("code", flags.reject_only_codes())
def test_decide_refuses_every_reject_only_code_and_allows_reject(code, tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s, flags=[code])
    assert refused(approve, s, it, REASON) == "reject_only"
    assert refused(approve, s, it, None) == "reject_only"
    assert workqueue.get(s, it.id).state == "NEEDS_PERSON" and _decisions(s) == []
    assert reject(s, it).decision == "reject" and workqueue.get(s, it.id).state == "REJECTED"


def test_a_null_field_item_can_be_rejected_and_never_approved(tmp_path):
    s = settings_for_tests(tmp_path)
    it = workqueue.insert_flagged(s, "x.pdf", sha("x"), "", s.tenant_id, "x", "X18")
    assert refused(approve, s, it, REASON) == "not_approvable"
    assert refused(approve, s, it, None) == "not_approvable"
    d = reject(s, it)
    assert d.content_code == content_code(it) and workqueue.get(s, it.id).state == "REJECTED"
    ro = new_item(s, "ro", fields=None, flags=["L02"])
    assert refused(approve, s, ro, REASON) == "not_approvable"


# ---- decide: reject ------------------------------------------------------------------------------------------------------------------------
def test_reject_needs_a_valid_reason(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s)
    for bad in (None, "", " " * 12, "short", "fine reason" + chr(1)):
        assert refused(reject, s, it, bad) == "invalid_reason"
    assert _decisions(s) == [] and workqueue.get(s, it.id).state == "READY"
    d = reject(s, it)
    assert d.reason == REASON and workqueue.get(s, it.id).state == "REJECTED"


# ---- binding, staleness, double decisions --------------------------------------------------------------------------------------------------
def test_a_second_decision_is_refused(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s)
    approve(s, it)
    assert refused(approve, s, it) == "already_decided"
    assert refused(reject, s, it) == "already_decided"
    rj = new_item(s, "r2")
    reject(s, rj)
    assert refused(approve, s, rj) == "already_decided"
    assert len(_decisions(s)) == 2


def test_a_wrong_content_code_is_stale(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s)
    assert refused(decisions.decide, s, it.id, "approve", "ap-a", None, "0" * 64, it.version) == "stale_content"
    assert refused(decisions.decide, s, it.id, "approve", "ap-a", None, "", it.version) == "stale_content"
    assert _decisions(s) == []


def test_a_stale_version_is_refused_and_leaves_no_decision_row(tmp_path):
    """The decision row is written first and the state move compares the version: a mismatch rolls the whole transaction back."""
    s = settings_for_tests(tmp_path)
    it = new_item(s)
    code = refused(decisions.decide, s, it.id, "approve", "ap-a", None, content_code(it), it.version + 1)
    assert code == "stale_content"
    assert _decisions(s) == [] and workqueue.get(s, it.id).state == "READY" and workqueue.get(s, it.id).version == it.version


def test_stale_form_after_purge_and_rescan_with_different_content(tmp_path):
    s = settings_for_tests(tmp_path)
    old = new_item(s, "inv")  # the person has this form open
    workqueue.purge(s, old.id)
    again = workqueue.insert_received(s, "inv.txt", sha("inv"), "invoice text", s.tenant_id, "inv")  # same bytes: same id, new uid
    changed = copy.deepcopy(GOOD_FIELDS)
    changed["total_minor"] = 9900
    workqueue.set_result(
        s,
        again.uid,
        "NEEDS_PERSON",
        fields=changed,
        flags=["D06"],
        failing_fields=[],
        model_id="m",
        tier="read",
        prompt_sha256="p" * 64,
        cost_micro=0,
    )
    assert again.id == old.id and again.uid != old.uid
    assert refused(decisions.decide, s, old.id, "approve", "ap-a", REASON, content_code(old), old.version) == "stale_content"
    assert _decisions(s) == []
    fresh = workqueue.get(s, old.id)
    assert approve(s, fresh, REASON).item_uid == again.uid  # decisions of the old uid do not carry over


def test_unknown_item_decision_value_approver_and_received(tmp_path):
    s = settings_for_tests(tmp_path)
    assert refused(decisions.decide, s, "nope-00000000", "approve", "ap-a", None, "0" * 64, 1) == "not_found"
    it = new_item(s)
    for dec in ("APPROVE", "maybe", "", None):
        assert refused(decisions.decide, s, it.id, dec, "ap-a", REASON, content_code(it), it.version) == "bad_decision"
    for who in ("", "  ", None):
        assert refused(decisions.decide, s, it.id, "reject", who, REASON, content_code(it), it.version) == "bad_decision"
    rec = workqueue.insert_received(s, "r.txt", sha("r"), "t", s.tenant_id, "r")
    assert refused(decisions.decide, s, rec.id, "reject", "ap-a", REASON, content_code(rec), rec.version) == "state_conflict"
    assert _decisions(s) == []


def test_eight_threads_deciding_the_same_item_exactly_one_wins(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s)
    code, barrier = content_code(it), threading.Barrier(8)
    results: list[object] = []

    def worker(i):
        barrier.wait()
        try:
            dec = "approve" if i % 2 == 0 else "reject"
            results.append(decisions.decide(s, it.id, dec, f"ap-{i}", REASON, code, it.version))
        except Refused as e:
            results.append(e.code)
        except Exception as e:  # noqa: BLE001  (anything else is a failure of the test below)
            results.append(repr(e))

    ts = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    [t.start() for t in ts]
    [t.join(60) for t in ts]
    wins = [r for r in results if isinstance(r, decisions.Decision)]
    assert len(results) == 8 and len(wins) == 1, results
    assert sorted(r for r in results if not isinstance(r, decisions.Decision)) == ["already_decided"] * 7
    assert len(_decisions(s)) == 1
    assert workqueue.get(s, it.id).state == ("APPROVED" if wins[0].decision == "approve" else "REJECTED")
    assert workqueue.get(s, it.id).version == it.version + 1


def test_decide_reads_its_own_limits_from_the_review_config(tmp_path):
    s = settings_for_tests(tmp_path)
    assert (s.review.reason_min_chars, s.review.reason_max_chars) == (10, 500)
    assert decisions.valid_reason(s, "x" * 10) and not decisions.valid_reason(s, "x" * 9)


# ---- approver, partial records, caller-held transaction -----------------------------------------------------------------------------------------
@pytest.mark.parametrize("who", ["ap-a", "a", "ap.a@x_y-1", "a" * 64])
def test_a_plain_approver_name_is_accepted(who, tmp_path):
    s = settings_for_tests(tmp_path)
    assert approve(s, new_item(s), None, who).approver == who


@pytest.mark.parametrize(
    "who", ["", " ", "a b", "-a", "a" * 65, "ap\n", "ap" + chr(0x200B), "ap" + chr(0), "ap-\u00e4", "a;b", "a'b", None, 7]
)
def test_a_bad_approver_name_is_refused(who, tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s)
    assert refused(approve, s, it, None, who) == "bad_decision"
    assert _decisions(s) == []


@pytest.mark.parametrize("break_", ["no_lines", "line_not_dict", "line_missing_key", "no_adjustments", "adj_not_dict"])
def test_a_malformed_stored_record_can_be_rejected_never_approved_and_never_crashes(break_, tmp_path):
    """The validators keep this out of the queue (``set_result`` refuses it), but a damaged row must still be decidable: reject works, approve is refused."""
    import json

    s = settings_for_tests(tmp_path)
    it = new_item(s, "dmg")
    bad = copy.deepcopy(GOOD_FIELDS)
    if break_ == "no_lines":
        del bad["lines"]
    elif break_ == "line_not_dict":
        bad["lines"] = ["x"]
    elif break_ == "line_missing_key":
        del bad["lines"][0]["qty"]
    elif break_ == "no_adjustments":
        del bad["adjustments"]
    elif break_ == "adj_not_dict":
        bad["adjustments"] = [5]
    else:
        bad = [1, 2]
    with workqueue.opened(s) as c:
        from queue_helpers import drop_triggers

        drop_triggers(c, "intake_b_immutable")  # a damaged row, forged under the guard that would stop the edit
        c.execute("UPDATE items SET fields_json = ? WHERE uid = ?", (json.dumps(bad), it.uid))
    dmg = workqueue.get(s, it.id)
    assert refused(approve, s, dmg, REASON) == "not_approvable"
    assert reject(s, dmg).decision == "reject"


def test_set_result_turns_a_record_that_fails_the_validators_into_an_x10_result(tmp_path):
    s = settings_for_tests(tmp_path)
    it = workqueue.insert_received(s, "a.txt", sha("a"), "t", s.tenant_id, "a")
    bad = copy.deepcopy(GOOD_FIELDS)
    bad["currency"] = "XXX"
    got = workqueue.set_result(
        s, it.uid, "READY", fields=bad, flags=[], failing_fields=[], model_id="m", tier="read", prompt_sha256=None, cost_micro=7
    )
    assert (got.state, got.flags, got.fields, got.failing_fields, got.cost_micro) == ("NEEDS_PERSON", ("X10",), None, ("currency",), 7)
    assert refused(approve, s, got, REASON) == "not_approvable"


def test_decide_inside_a_caller_transaction_is_undone_by_the_callers_rollback(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s)
    with workqueue.opened(s) as c:
        with pytest.raises(RuntimeError):
            with workqueue.transaction(c):
                decisions.decide(s, it.id, "approve", "ap-a", None, content_code(it), it.version, conn=c)
                assert workqueue.get_in(c, it.id).state == "APPROVED"
                raise RuntimeError("caller fails after the decision")
    assert workqueue.get(s, it.id).state == "READY" and _decisions(s) == []
    with workqueue.opened(s) as c, workqueue.transaction(c):
        decisions.decide(s, it.id, "approve", "ap-a", None, content_code(it), it.version, conn=c)
    assert workqueue.get(s, it.id).state == "APPROVED" and len(_decisions(s)) == 1


def test_a_database_guard_refusal_is_a_refused_not_a_traceback(tmp_path):
    """Hand-forge a state the API would refuse earlier (an approve for a record with a reject-only flag stored under a changed flag table)."""
    from queue_helpers import drop_triggers

    s = settings_for_tests(tmp_path)
    it = new_item(s, "g", flags=["D06"])
    with workqueue.opened(s) as c:
        drop_triggers(c, "intake_b_immutable")
        c.execute("UPDATE items SET flags_json = ? WHERE uid = ?", ('["D10"]', it.uid))
    forged = workqueue.get(s, it.id)
    assert refused(decisions.decide, s, it.id, "approve", "ap-a", REASON, content_code(forged), forged.version) == "reject_only"
    # the API refuses first; to reach the trigger, call the lower layer with the checks skipped
    with workqueue.opened(s) as c, pytest.raises(Refused) as e, workqueue.transaction(c):
        workqueue.apply_decision(c, forged, "approve", "APPROVED", "ap-a", REASON, content_code(forged), forged.version)
    assert e.value.code == "state_conflict" and "guard" in e.value.text


def test_d12_needs_a_valid_reason_like_d06_and_is_not_reject_only(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s, "d12", flags=["D12"])
    assert refused(approve, s, it, None) == "invalid_reason"
    assert refused(approve, s, it, "short") == "invalid_reason"
    assert decisions.may_approve(s, it, REASON) and not decisions.may_approve(s, it, " " * 12)
    assert approve(s, it, REASON).reason == REASON
    both = new_item(s, "d12d06", flags=["D06", "D12"])
    assert refused(approve, s, both, None) == "invalid_reason" and decisions.may_approve(s, both, REASON)
    ro = new_item(s, "d12d10", flags=["D12", "D10"])
    assert refused(approve, s, ro, REASON) == "reject_only"  # a reject-only flag still wins


assertive_all(globals())
