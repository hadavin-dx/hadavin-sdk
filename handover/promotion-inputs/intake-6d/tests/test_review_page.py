"""6c: the view builders of ``review_page`` and the HTML ``ui.render_*`` makes from them (brief-v3 10, 15.3). No HTTP: the service (6d) has its own tests.

Every test builds a real queue in a temporary folder with the fake backend and reads it through the builders, so a builder that skips its check (shows
Approve for a reject-only flag, hands the invoice text to a viewer, shows a halt reason, opens a write connection) fails here."""

from __future__ import annotations

import ast
import hashlib
import logging
import re
from datetime import UTC, datetime
from html import escape
from pathlib import Path

import pytest
from queue_helpers import GOOD_FIELDS, REASON, approve, drop_triggers, reject, sha

from conftest import settings_for_tests
from intake import access, decisions, exporter, inbox, invoicecheck, review_page, routes, settings, ui, workqueue
from intake.codes import Refused

SRC = Path(__file__).resolve().parents[1] / "src" / "intake" / "review_page.py"
SPEND_OK = review_page.SpendReading(1_230_000, (False, ""))
HOSTILE = (
    "\u0600\u06dd\u070f\ufe0f\u034f\u3164\u202e<script>alert(1)</script>\u200b"  # for text that is not validated (invoice text, file names)
)
FIELD_HOSTILE = (
    "\ue000\u00a0\ufe0f\u034f\u3164\u2800\u0378<script>alert(1)</script>"  # what a stored record may still hold (no Cc, Cf, Cs, Zl, Zp)
)
FORBIDDEN_WORDS = ("hard cap", "real ceiling", "accuracy", "robust", "model_mismatch", "mismatch")


def session(role: str = routes.APPROVER, name: str = "ap-a") -> access.Session:
    return access.Session("sid-secret", name, role, "csrf-token-1", access.Stamp(0.0, 0.0), access.Stamp(0.0, 0.0))


APPROVER, VIEWER = session(), session(routes.VIEWER, "viewer-1")


class ScanStub:
    def __init__(self, running: bool = False) -> None:
        self._running = running

    def running(self) -> bool:
        return self._running


@pytest.fixture
def s(tmp_path, monkeypatch, request):
    spec = getattr(request.node, "callspec", None)
    if (
        spec is None or spec.params.get("mode") != "unreadable"
    ):  # the "unreadable" case needs the REAL read_kill_switch (it fails closed inside)
        monkeypatch.setattr(settings, "read_kill_switch", lambda: False)
    return settings_for_tests(tmp_path)


def make(s, stem, text="invoice text", fields=GOOD_FIELDS, flags=(), failing=()):
    """An item with chosen invoice text, through the public API."""
    it = workqueue.insert_received(s, f"{stem}.txt", sha(stem + text), text, s.tenant_id, stem)
    assert isinstance(it, workqueue.Item)
    return workqueue.set_result(
        s,
        it.uid,
        "NEEDS_PERSON" if flags else "READY",
        fields=fields,
        flags=flags,
        failing_fields=failing,
        model_id="model-x",
        tier="read",
        prompt_sha256="p" * 64,
        cost_micro=0,
    )


def damage(s, item, column="flags_json", value="not json"):
    with workqueue.opened(s) as c:
        drop_triggers(c)
        c.execute(f"UPDATE items SET {column} = ? WHERE uid = ?", (value, item.uid))


def html(page) -> str:
    return str(page.html)


def list_page(s, who=APPROVER, query="", refused=(), spend=SPEND_OK, scan_running=False):
    v = review_page.queue_view(s, who, ui.parse_list_query(query), tuple(refused), spend, scan_running=scan_running, refused_total=None)
    return v, ui.render_list(v, review_page.session_view(who))


def item_page(s, item_id, who=APPROVER, **kw):
    v = review_page.invoice_view(s, who, item_id, **kw)
    return v, ui.render_item(v, review_page.session_view(who))


def export_page(s, who=APPROVER, run=None, **kw):
    v = review_page.export_view(s, who, run, **kw)
    return v, ui.render_export(v, review_page.session_view(who))


def calm(fn, *a, **k):
    """Call a page builder that must NOT raise; a raise is reported as a plain failure (so a mutant that removes the guard is a KILL, not a crash)."""
    try:
        return fn(*a, **k)
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"raised {type(e).__name__} where the page must still be built")


def banner_texts(v) -> list[str]:
    return [b.text for b in v.banners]


# ---- spec 4 render names ------------------------------------------------------------------------------------------------------------------------------
def test_script_tag_escaped(s):
    it = make(s, "inv", text="<script>alert(1)</script> invoice", fields={**GOOD_FIELDS, "supplier_name": "<script>x</script>"})
    _, page = item_page(s, it.id)
    out = html(page)
    assert "<script" not in out.lower() and "&lt;script&gt;" in out
    _, lst = list_page(s)
    assert "<script" not in html(lst).lower()


def test_bidi_shown_as_markers(s):
    it = make(s, "inv", text="pay\u202e 123\u202c now \u2066x")
    out = html(item_page(s, it.id)[1])
    assert "\u202e" not in out and "\u2066" not in out and "U+202E" in out and "U+2066" in out
    lst = html(list_page(s, refused=(inbox.Refusal("a\u202eb.txt", "bad_name"),))[1])
    assert "\u202e" not in lst and "U+202E" in lst


def test_login_field_is_password_type(s):
    out = html(ui.render_login(None, csrf="tok", banners=review_page.banners(s, None, SPEND_OK)))
    assert re.search(r'<input[^>]*type="password"[^>]*name="passphrase"|<input[^>]*name="passphrase"[^>]*type="password"', out)
    assert 'autocomplete="off"' in out and 'name="csrf"' in out


def test_stale_content_code_refused(s):
    it = make(s, "inv")
    v = review_page.invoice_view(s, APPROVER, it.id, refusal_code="stale_content")
    out = html(ui.render_error(409, "Not recorded", review_page.ERROR_TEXT["stale_content"], review_page.session_view(APPROVER)))
    assert review_page.ERROR_TEXT["stale_content"] in out
    assert v.refusal == review_page.ERROR_TEXT["stale_content"]
    assert review_page.ERROR_TEXT["stale_content"] in html(ui.render_item(v, review_page.session_view(APPROVER)))


# ---- the list -----------------------------------------------------------------------------------------------------------------------------------------
def test_list_order(s):
    clock = iter(datetime(2026, 11, 4, 10, m, tzinfo=UTC) for m in range(10))

    def later(stem, **kw):
        workqueue.set_fixed_clock(s, next(clock))
        return make(s, stem, **kw)

    done = later("done")
    ready = later("ready")
    need_a = later("needa", flags=("D06",))
    need_b = later("needb", flags=("D12",))
    approve(s, done, "a reason that is long enough")
    v, _ = list_page(s)
    assert [r.item_id for r in v.rows] == [need_a.id, need_b.id, ready.id, done.id]
    v2, _ = list_page(s, query="sort=supplier&dir=asc&state=READY")
    assert [r.item_id for r in v2.rows] == [ready.id]


def test_refused_files_panel_text(s):
    refused = tuple(inbox.Refusal(f"file{i}.txt", code) for i, code in enumerate(inbox.REFUSAL_CODES))
    refused += (inbox.Refusal("odd.txt", "not_a_known_code"),)
    v, page = list_page(s, refused=refused)
    out = html(page)
    for r in refused[:-1]:
        assert r.name in out and review_page.ERROR_TEXT[r.reason] in out
    assert review_page.ERROR_TEXT["internal"] in out and "not_a_known_code" not in out  # an unknown code is "internal", never the code
    assert f"Files not processed ({len(refused)})" in out


def test_unreadable_items_panel(s):
    good = make(s, "good")
    bad = make(s, "bad")
    damage(s, bad)
    v, page = list_page(s)
    assert [r.item_id for r in v.rows] == [good.id]
    assert any(bad.id in t and "1 invoice(s) cannot be shown" in t for t in banner_texts(v))
    assert bad.id in html(page)
    many = [make(s, f"m{i}") for i in range(7)]
    for m in many:
        damage(s, m)
    v, _ = list_page(s)
    assert any("8 invoice(s) cannot be shown" in t and "and more" in t for t in banner_texts(v))


def test_one_bad_row_never_breaks_the_list(s, monkeypatch, caplog):
    a, b = make(s, "a"), make(s, "b")
    real = ui.flag_view
    flagged = make(s, "c", flags=("D06",))

    def boom(code):
        raise RuntimeError("builder bug")

    monkeypatch.setattr(ui, "flag_view", lambda code: boom(code) if code == "D06" else real(code))
    before = review_page.degraded_counts().get("row_not_built", 0)
    with caplog.at_level(logging.WARNING, logger="intake.review_page"):
        v, page = calm(list_page, s)
    assert {r.item_id for r in v.rows} == {a.id, b.id}  # the bad row is out, the rest stays
    assert review_page.degraded_counts().get("row_not_built", 0) == before + 1
    assert any("row_not_built" in r.getMessage() and flagged.id in r.getMessage() for r in caplog.records)
    assert flagged.id in html(page)  # named in the notice
    kinds = [b.kind for b in v.banners]
    assert "rows_not_built" in kinds and "unreadable_items" not in kinds  # a fault in this page is not "damaged stored data"


def test_inconsistent_approve_verdict_degrades_one_row_and_is_counted(s, monkeypatch, caplog):
    ok, odd = make(s, "ok"), make(s, "odd", flags=("D10",))
    real = review_page._approval

    def liar(settings_, item):
        out = real(settings_, item)
        return {**out, "may_approve": True, "approve_refusal": None} if item.id == odd.id else out

    monkeypatch.setattr(review_page, "_approval", liar)
    before = review_page.degraded_counts().get("approve_inconsistent", 0)
    with caplog.at_level(logging.WARNING, logger="intake.review_page"):
        v, page = calm(list_page, s)
    rows = {r.item_id: r for r in v.rows}
    assert set(rows) == {ok.id, odd.id}  # the degraded row is still listed
    assert rows[ok.id].may_approve and not rows[odd.id].may_approve and rows[odd.id].approve_refusal
    assert review_page.degraded_counts().get("approve_inconsistent", 0) == before + 1
    assert any("approve_inconsistent" in r.getMessage() for r in caplog.records)


# ---- the invoice page: approve rules, reason box -------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("code", ["D10", "X10", "X18", "X28", "L01", "L02", "unknown"])
def test_approve_form_absent_for_each_reject_only_code(s, code):
    if code == "unknown":
        it = make(s, "inv", flags=("L01",))
        damage(s, it, "flags_json", '["Z99"]')
    else:
        it = make(s, "inv", flags=(code,))
    v, page = item_page(s, it.id)
    out = html(page)
    assert v.may_approve is False and v.approve_refusal
    assert 'value="approve"' not in out and 'value="reject"' in out
    _, lst = list_page(s)
    assert 'value="approve"' not in html(lst)


def test_approve_offered_when_clean_and_needs_reason_for_d06_and_d12(s):
    clean = make(s, "clean")
    d06 = make(s, "d06", flags=("D06",))
    d12 = make(s, "d12", flags=("D12",))
    v, page = item_page(s, clean.id)
    assert v.may_approve and not v.approve_needs_reason
    assert 'value="approve"' in html(page) and "Reason for approving (optional)" in html(page)
    for it in (d06, d12):
        v, page = item_page(s, it.id)
        assert v.may_approve and v.approve_needs_reason
        out = html(page)
        assert "Reason for approving (required)" in out
    assert not decisions.may_approve(s, d06, None) and decisions.may_approve(
        s, d06, REASON
    )  # the page follows the decision module, not a copy


def test_reject_reason_required(s):
    it = make(s, "inv")
    out = html(item_page(s, it.id)[1])
    assert "Reason for rejecting (required)" in out
    reject_form = out[out.index('value="reject"') :]
    assert re.search(r'<input type="text" name="reason"[^>]* required', reject_form)


def test_reason_box_single_line_no_suggestions(s):
    it = make(s, "inv")
    out = html(item_page(s, it.id)[1])
    boxes = re.findall(r'<input type="text" name="reason"[^>]*>', out)
    assert len(boxes) == 2 and "<textarea" not in out
    for b in boxes:
        assert f'maxlength="{s.review.reason_max_chars}"' in b and 'autocomplete="off"' in b
        assert "value=" not in b and "placeholder" not in b  # no pre-filled or suggested text


def test_form_carries_version_content_code_and_csrf(s):
    it = make(s, "inv")
    v, page = item_page(s, it.id)
    out = html(page)
    from intake import content_code

    assert v.content_code == content_code.content_code(it) and v.version == it.version
    assert f'name="content_code" value="{v.content_code}"' in out and 'name="csrf" value="csrf-token-1"' in out


# ---- D10 and D12 ---------------------------------------------------------------------------------------------------------------------------------------
D10_TEXT = "INVOICE\nSupplier: Acme Ltd\nBank: IBAN GB82 WEST 1234 5698 7654 99\nPlease pay promptly ZZPLANT991\n"


def test_d10_shows_candidate_and_on_file(s):
    it = make(s, "inv", text=D10_TEXT, flags=("D10",))
    on_file = invoicecheck.load_suppliers(s.intake_home / "suppliers.csv")[invoicecheck._key("Acme Ltd")]
    cands = [f.candidate for f in invoicecheck.bank_detail_findings(D10_TEXT, on_file)]
    assert cands
    v, page = item_page(s, it.id)
    out = html(page)
    assert v.bank_on_file is not None and v.bank_in_text, "the D10 card was not built"
    assert v.bank_on_file.restored == on_file and [b.restored for b in v.bank_in_text] == list(dict.fromkeys(cands))
    assert on_file in out and all(c in out for c in cands)
    assert "Computed now from the current suppliers file." in out
    # a viewer sees chips, never the values (and not the text)
    vv, vpage = item_page(s, it.id, who=VIEWER)
    vout = html(vpage)
    assert (
        "bank number 1, hidden" in vout and "bank number 2, hidden" in vout and "hidden value" not in vout
    )  # real chips, not the fallback
    assert vv.bank_on_file is not None and vv.bank_on_file.restored is None and all(b.restored is None for b in vv.bank_in_text)
    assert on_file not in vout and not any(c in vout for c in cands) and "ZZPLANT991" not in vout and "chip" in vout


def test_d10_card_follows_the_current_suppliers_file(s):
    it = make(s, "inv", text=D10_TEXT, flags=("D10",))
    (s.intake_home / "suppliers.csv").write_text("supplier_name,bank_detail\nAcme Ltd,GB82 WEST 1234 5698 7654 99\n", encoding="utf-8")
    v, _ = item_page(s, it.id)
    assert v.bank_in_text == ()  # the candidate now equals what is on file
    (s.intake_home / "suppliers.csv").write_text("nonsense", encoding="utf-8")
    v, page = item_page(s, it.id)
    assert v.bank_on_file is None and any("suppliers file could not be read" in t for t in banner_texts(v))


def test_d12_shows_unexplained_numbers(s):
    text = "INVOICE\nSupplier: Acme Ltd\nReference 987654321098\nTotal due $33.00\n"
    it = make(s, "inv", text=text, flags=("D12",))
    want = invoicecheck.unexplained_numbers(
        GOOD_FIELDS, text, invoicecheck.load_suppliers(s.intake_home / "suppliers.csv")[invoicecheck._key("Acme Ltd")]
    )
    assert want
    v, page = item_page(s, it.id)
    assert v.d12_numbers == tuple(want) and "Numbers not explained" in html(page) and want[0] in html(page)
    vv, vpage = item_page(s, it.id, who=VIEWER)
    assert vv.d12_numbers == () and want[0] not in html(vpage) and "Numbers not explained" not in html(vpage)


def test_supplier_lookup_uses_the_check_key(s):
    sup = invoicecheck.load_suppliers(s.intake_home / "suppliers.csv")
    for name in ("Acme Ltd", "ACME   ltd", " acme ltd ", "Acme\u00a0Ltd", "\uff21cme Ltd", "Nobody", "", None, 5):
        want = sup.get(invoicecheck._key(name)) if isinstance(name, str) else None
        assert review_page._on_file(sup, name) == want, name
    assert review_page._on_file(sup, "ACME   ltd") is not None


def test_check_fault_is_shown_and_counted(s, monkeypatch):
    it = make(s, "inv", text=D10_TEXT, flags=("D10",))

    def boom(*a, **k):
        raise RuntimeError("check bug")

    monkeypatch.setattr(invoicecheck, "bank_detail_findings", boom)
    before = review_page.degraded_counts().get("bank_or_numbers_not_shown", 0)
    v, page = calm(item_page, s, it.id)
    assert review_page.degraded_counts().get("bank_or_numbers_not_shown", 0) == before + 1
    assert any("could not be shown" in t for t in banner_texts(v)) and 'value="reject"' in html(page)


def test_unknown_flag_renders(s):
    it = make(s, "inv", flags=("L01",))
    damage(s, it, "flags_json", '["Z99"]')
    v, page = item_page(s, it.id)
    assert v.flags[0].reject_only and "no sentence for" in html(page) and v.may_approve is False
    assert "Z99" in html(list_page(s)[1])
    assert "Z99" in html(page)  # the code is shown as escaped text


def test_stored_data_bad_item_page(s):
    it = make(s, "inv")
    damage(s, it, "flags_json", "not json")
    with pytest.raises(Refused) as e:
        review_page.invoice_view(s, APPROVER, it.id)
    assert e.value.code == "stored_data_bad" and "not json" not in str(e.value)
    out = html(ui.render_error(409, "Cannot be shown", review_page.ERROR_TEXT[e.value.code], review_page.session_view(APPROVER)))
    assert escape(review_page.ERROR_TEXT["stored_data_bad"]) in out
    with pytest.raises(Refused) as e2:
        review_page.invoice_view(s, APPROVER, "nope-00000000")
    assert e2.value.code == "not_found"


# ---- viewer ----------------------------------------------------------------------------------------------------------------------------------------------
def test_viewer_sees_no_invoice_text(s):
    text = "INVOICE\nSupplier: Acme Ltd\nBank: IBAN GB82 WEST 1234 5698 7654 99\nNote ZZPLANTTEXT4711\n"
    it = make(s, "inv", text=text, flags=("D10",))
    ok = make(s, "ok", text="other invoice ZZPLANTOK123")
    approve(s, ok)
    on_file = "GB82 WEST 1234 5698 7654 32"
    cands = [f.candidate for f in invoicecheck.bank_detail_findings(text, on_file)]
    planted = ["ZZPLANTTEXT4711", "ZZPLANTOK123", on_file, *cands]
    pages = [html(list_page(s, VIEWER)[1]), html(item_page(s, it.id, VIEWER)[1]), html(item_page(s, ok.id, VIEWER)[1])]
    with pytest.raises(Refused) as e:
        review_page.export_view(s, VIEWER)
    assert e.value.code == "role_denied"
    pages.append(html(ui.render_export(ui.ExportPageView(rows=()), review_page.session_view(VIEWER))))
    for out in pages:
        for p in planted:
            assert p not in out, p
    v, _ = item_page(s, it.id, VIEWER)
    assert v.source_text is None and "Invoice text is shown to the approver only." in html(item_page(s, it.id, VIEWER)[1])
    assert 'name="decision"' not in pages[1]  # no forms for a viewer
    # both ways: the approver does see them
    a_item = html(item_page(s, it.id)[1])
    assert "ZZPLANTTEXT4711" in a_item and on_file in a_item and all(c in a_item for c in cands)


def test_export_page_is_refused_for_a_viewer_before_anything_is_read(s, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("the queue was read for a viewer")

    monkeypatch.setattr(workqueue, "connect_readonly", boom)
    monkeypatch.setattr(exporter, "preview_rows", boom)
    with pytest.raises(Refused) as e:
        review_page.export_view(s, VIEWER)
    assert e.value.code == "role_denied"


# ---- banners ---------------------------------------------------------------------------------------------------------------------------------------------
def test_model_mismatch_never_shown(s):
    make(s, "inv")
    for out in (html(list_page(s)[1]), html(item_page(s, workqueue.list_items(s)[0].id)[1]), html(export_page(s)[1])):
        assert "model_mismatch" not in out and "mismatch" not in out.lower()
    assert "model_mismatch" not in "".join(
        banner_texts(review_page.queue_view(s, APPROVER, ui.ListQuery(), (), SPEND_OK, refused_total=None))
    )


def test_halted_banner_has_no_reason_code(s):
    make(s, "inv")
    spend = review_page.SpendReading(5_000_000, (True, "cap_reached_SECRETCODE"))
    v, page = list_page(s, spend=spend)
    assert "Spending halted: our spend counter stopped new AI calls. Run intake check." in banner_texts(v)
    assert "SECRETCODE" not in html(page) and "cap_reached" not in html(page)
    _, ipage = item_page(s, workqueue.list_items(s)[0].id, spend=spend)
    assert "SECRETCODE" not in html(ipage)


@pytest.mark.parametrize("spend", [None, review_page.SpendReading(None, None), review_page.SpendReading(10_000, None)])
def test_spend_unavailable_shown(s, spend):
    make(s, "inv")
    v, page = list_page(s, spend=spend)
    assert "Spending status unavailable" in banner_texts(v) and "Spending status unavailable" in html(page)
    assert not any("not halted" in t.lower() for t in banner_texts(v))


def test_spend_line_on_the_invoice_page(s):
    it = make(s, "inv")
    v, page = item_page(s, it.id, spend=SPEND_OK)
    assert "Our spend counter: US$ 1.23" in banner_texts(v) and "Our spend counter: US$ 1.23" in html(page)
    v, _ = item_page(s, it.id, spend=review_page.SpendReading(None, (False, "")))
    assert not any(t.startswith("Our spend counter") for t in banner_texts(v))


def test_empty_made_up_list_and_scan_banners(s):
    (s.intake_home / "synthetic_hashes.txt").write_text("", encoding="utf-8")
    v, _ = list_page(s, scan_running=True)
    assert "Live AI calls stopped: the made-up list is empty" in banner_texts(v) and "A scan is running" in banner_texts(v)
    v, _ = list_page(s, scan_running=False)
    assert "A scan is running" not in banner_texts(v)


def test_scan_running_banner_on_every_page(s):
    it = approve(s, make(s, "inv"))
    iid = workqueue.list_items(s)[0].id
    for build in (
        lambda **k: review_page.queue_view(s, APPROVER, ui.ListQuery(), (), SPEND_OK, **{"refused_total": None, **k}),
        lambda **k: review_page.invoice_view(s, APPROVER, iid, spend=SPEND_OK, **k),
        lambda **k: review_page.export_view(s, APPROVER, spend=SPEND_OK, **k),
    ):
        assert "A scan is running" in banner_texts(build(scan_running=True))
        assert "A scan is running" not in banner_texts(build())
        assert "A scan is running" not in banner_texts(build(scan_running=False))
    assert "A scan is running" in [b.text for b in review_page.banners(s, ScanStub(True), SPEND_OK)]  # the older scanner form still works
    assert it is not None


@pytest.mark.parametrize("mode", ["true", "false", "unreadable"])
def test_kill_switch_engaged_shown_and_closes_the_write_form(s, monkeypatch, mode):
    approve(s, make(s, "inv"))
    assert workqueue.list_items(s)[0].state == "APPROVED"
    if (
        mode == "unreadable"
    ):  # the policy file cannot be read: ``read_kill_switch`` itself fails closed (engaged), so the page must close the write form

        def unreadable():
            raise OSError("policy unreadable")

        monkeypatch.setattr(settings, "_raw_policy", unreadable)  # the fixture left read_kill_switch alone for this case
    else:
        monkeypatch.setattr(settings, "read_kill_switch", {"true": lambda: True, "false": lambda: False}[mode])
    v, page = export_page(s)
    out = html(page)
    if mode == "false":
        assert v.kill_switch is False and v.may_export and 'name="passphrase"' in out and "Export is switched off" not in out
        return
    assert v.kill_switch is True and "Export is switched off" in out and 'name="passphrase"' not in out and not v.may_export
    assert "Export is switched off" in banner_texts(review_page.queue_view(s, APPROVER, ui.ListQuery(), (), SPEND_OK, refused_total=None))


def test_kill_switch_unreadable_shown_engaged(s, monkeypatch):
    """``settings.read_kill_switch`` fails closed inside and never raises; if a replacement did, the banner source still shows ENGAGED, never unavailable."""

    def raising():
        raise OSError("policy unreadable")

    monkeypatch.setattr(settings, "read_kill_switch", raising)
    v = review_page.queue_view(s, APPROVER, ui.ListQuery(), (), SPEND_OK, refused_total=None)
    assert "Export is switched off" in banner_texts(v) and not any("Status unavailable: kill_switch" in t for t in banner_texts(v))


def test_banner_isolation(s, monkeypatch):
    make(s, "inv")

    def broken(path):
        raise RuntimeError("secret detail that must not show")

    monkeypatch.setattr(settings, "load_hash_list", broken)
    v, page = calm(list_page, s, spend=review_page.SpendReading(1, (True, "x")))
    texts = banner_texts(v)
    assert "Status unavailable: hash_list" in texts and any(t.startswith("Spending halted") for t in texts)  # the others still show
    assert "secret detail" not in html(page) and "invoice(s) shown" in html(page)  # and the page still renders


# ---- missing queue, read-only ---------------------------------------------------------------------------------------------------------------------------
def test_pages_on_a_missing_queue_create_nothing(s):
    qdir = workqueue.queue_path(s).parent
    before = sorted(p.name for p in qdir.iterdir()) if qdir.exists() else []
    v, page = list_page(s)
    assert v.rows == () and "No invoices to show" in html(page)
    with pytest.raises(Refused) as e:
        review_page.invoice_view(s, APPROVER, "inv-00000000")
    assert e.value.code == "not_found"
    ev, epage = export_page(s)
    assert ev.rows == () and "Nothing to export" in html(epage)
    assert not workqueue.queue_path(s).exists()
    assert (sorted(p.name for p in qdir.iterdir()) if qdir.exists() else []) == before


def test_view_builders_never_write_the_queue(s):
    it = approve(s, make(s, "a"))
    make(s, "b", flags=("D06",))
    db = workqueue.queue_path(s)

    def state():
        wal = db.with_name(db.name + "-wal")
        return hashlib.sha256(
            db.read_bytes()
        ).hexdigest(), wal.stat().st_size if wal.exists() else 0  # a reader may create an EMPTY wal file; no bytes change

    ids = [i.id for i in workqueue.list_items(s)]
    before = state()
    list_page(s)
    export_page(s)
    for i in ids:
        item_page(s, i)
    assert state() == before and it is not None


def test_review_page_opens_the_queue_only_read_only():
    """AST: the builders call ``workqueue.connect_readonly`` and nothing that can create or write the file (brief 4.5 ``gets_use_readonly_connection``)."""
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    used = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "workqueue"}
    assert "connect_readonly" in used
    assert used.isdisjoint({"connect", "opened", "get", "scope", "transaction", "apply_decision", "set_result", "record_export", "purge"})
    called = {
        n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "decisions"
    }
    assert called == {"approve_refusal"}  # the approve rule has one home; the page never records a decision


# ---- decision card and export receipt --------------------------------------------------------------------------------------------------------------------
def test_decision_and_receipt_shown(s):
    it = make(s, "inv")
    reject(s, it, "<b>looks wrong</b> to me")
    v, page = item_page(s, it.id, outcome_code="rejected")
    out = html(page)
    assert v.decision.decision == "rejected" and v.decision.approver == "ap-a" and v.may_approve is False
    assert "&lt;b&gt;looks wrong" in out and "Recorded as" in out and 'name="decision"' not in out  # no forms after a decision
    assert "Rejected. Recorded as ap-a (a sign-in name, not a proven person)." in banner_texts(v)
    ok = make(s, "ok")
    approve(s, ok)
    v, _ = item_page(s, ok.id, outcome_code="approved")
    assert v.decision.decision == "approved" and any(t.startswith("Approved. Recorded as ap-a") for t in banner_texts(v))
    v, _ = item_page(s, ok.id, outcome_code="whatever")
    assert not any(b.kind == "decision_recorded" for b in v.banners)
    v, _ = item_page(s, ok.id, outcome_code="rejected")  # the stored decision is an approve: no banner for a different outcome
    assert not any(b.kind == "decision_recorded" for b in v.banners)
    waiting = make(s, "waiting")
    v, _ = item_page(s, waiting.id, outcome_code="approved")  # no stored decision: no banner
    assert not any(b.kind == "decision_recorded" for b in v.banners)
    other = session(name="ap-b")  # the banner names the recorded approver, not whoever opens the page
    v = review_page.invoice_view(s, other, ok.id, outcome_code="approved")
    assert any("Recorded as ap-a" in t for t in banner_texts(v))


def test_exported_item_shows_a_receipt_with_utc_time(s):
    it = approve(s, make(s, "inv"))
    run = exporter.export_pending(s)
    assert run.ok
    iid = workqueue.list_items(s)[0].id
    v, page = item_page(s, iid)
    assert v.state == "EXPORTED" and v.export is not None and re.fullmatch(r".*(Z|\+00:00)", v.export.at_utc)
    assert len(v.export.content_code_prefix) <= 16 and "Written to the spreadsheet file" in html(page)
    assert it is not None


def test_bad_receipt_time_degrades_not_fails(s, monkeypatch):
    approve(s, make(s, "inv"))
    exporter.export_pending(s)
    iid = workqueue.list_items(s)[0].id
    with workqueue.opened(s) as c:
        drop_triggers(c)
        c.execute("UPDATE exports SET at = '2026-11-04T11:00:00+05:30'")
    before = review_page.degraded_counts().get("receipt_not_shown", 0)
    v, _ = calm(item_page, s, iid)
    assert v.export is None and review_page.degraded_counts().get("receipt_not_shown", 0) == before + 1


# ---- export page ----------------------------------------------------------------------------------------------------------------------------------------
def test_export_preview_and_run_results(s):
    a = approve(s, make(s, "inv"))
    make(s, "waiting")
    v, page = export_page(s)
    assert len(v.rows) == 1 and v.may_export and v.kill_switch is False and 'name="passphrase"' in html(page)
    assert v.rows[0].total_minor == GOOD_FIELDS["total_minor"] and "33.00 USD" in html(page)  # the real total, not a made-up 0
    run = exporter.export_pending(s)
    v2, page2 = export_page(s, run=run)
    iid = [i.id for i in workqueue.list_items(s) if i.state == "EXPORTED"][0]
    assert v2.results == ((iid, exporter.RESULT_TEXT["exported"]),) and v2.file_text == exporter.FILE_TEXT["written"]
    assert exporter.FILE_TEXT["written"] in html(page2) and iid in html(page2) and a is not None
    assert v2.rows == () and not v2.may_export


def test_export_kill_switch_shown(s, monkeypatch):
    approve(s, make(s, "inv"))
    monkeypatch.setattr(settings, "read_kill_switch", lambda: True)
    run = exporter.export_pending(s)
    v, page = export_page(s, run=run)
    out = html(page)
    assert v.results == (("Whole export", exporter.RESULT_TEXT["kill_switch"]),) and v.file_text == exporter.FILE_TEXT["kill_switch"]
    assert exporter.RESULT_TEXT["kill_switch"] in out and exporter.FILE_TEXT["kill_switch"] in out
    assert "Export is switched off" in out and 'name="passphrase"' not in out


def test_export_refusal_and_unknown_codes_use_plain_text(s):
    v, _ = export_page(s, refusal_code="role_denied")
    assert v.refusal == review_page.ERROR_TEXT["role_denied"]
    v, _ = export_page(s, refusal_code="made_up_code")
    assert v.refusal == review_page.ERROR_TEXT["internal"]
    run = exporter.ExportRun((exporter.ExportResult("made_up_code"),), "written")
    v, _ = export_page(s, run=run)
    assert v.results[0][1] == review_page.ERROR_TEXT["internal"]


def test_invalid_reason_sentence_is_filled_from_config(s):
    it = make(s, "inv")
    v, _ = item_page(s, it.id, refusal_code="invalid_reason")
    assert str(s.review.reason_min_chars) in v.refusal and str(s.review.reason_max_chars) in v.refusal and "{" not in v.refusal


def test_session_view_hides_secrets_in_repr():
    sv = review_page.session_view(APPROVER)
    assert (sv.login_name, sv.role, sv.csrf) == ("ap-a", "approver", "csrf-token-1")
    assert "csrf-token-1" not in repr(sv) and "sid-secret" not in repr(sv)


# ---- whole-page checks ----------------------------------------------------------------------------------------------------------------------------------
def _all_pages(s, who):
    it = [i for i in workqueue.list_items(s) if i.state in ("READY", "NEEDS_PERSON")][0]
    pages = [list_page(s, who, refused=(inbox.Refusal("a.txt", "too_large"),))[1], item_page(s, it.id, who)[1]]
    if who.role == routes.APPROVER:
        pages.append(export_page(s, who)[1])
    return pages


def test_no_style_attribute_no_script(s):
    make(s, "a", text=D10_TEXT, flags=("D10",))
    make(s, "b", flags=("D12",))
    for who in (APPROVER, VIEWER):
        for page in _all_pages(s, who):
            low = html(page).lower()
            assert " style=" not in low and "<script" not in low and "javascript:" not in low and not re.search(r"\son[a-z]+\s*=", low)
            assert low.count("<style>") == 1 and page.profile == "strict"


def test_wording_scan_on_pages(s):
    make(s, "a", text=D10_TEXT, flags=("D10",))
    make(s, "b", flags=("D12",))
    for who in (APPROVER, VIEWER):
        for spend in (SPEND_OK, None, review_page.SpendReading(3, (True, "x"))):
            v, page = list_page(s, who, spend=spend)
            for out in (html(page), " ".join(banner_texts(v))):
                low = re.sub(r"<[^>]+>", " ", out.split("</style>")[-1]).lower()
                for w in FORBIDDEN_WORDS:
                    assert w not in low, w
    for text in review_page.ERROR_TEXT.values():
        assert not any(w in text.lower() for w in FORBIDDEN_WORDS)


def test_hostile_text_in_every_field(s):
    fields = {
        **GOOD_FIELDS,
        "supplier_name": "Sup" + FIELD_HOSTILE,
        "invoice_no": "N1" + FIELD_HOSTILE,
        "lines": [
            {"description": "Line" + FIELD_HOSTILE, "qty": 2, "unit_cost_minor": 1250, "amount_minor": 2500},
            GOOD_FIELDS["lines"][1],
        ],
    }
    it = make(s, "hostile", text="text" + HOSTILE, fields=fields)
    reject(s, it, "<script>alert(1)</script> not right")
    refused = (inbox.Refusal("file" + HOSTILE + ".txt", "bad_name"),)
    outs = [html(list_page(s, who, refused=refused)[1]) for who in (APPROVER, VIEWER)]
    outs += [html(item_page(s, it.id, who)[1]) for who in (APPROVER, VIEWER)]
    for out in outs:
        low = out.lower()
        assert "<script" not in low and "&lt;script&gt;" in out and "\u202e" not in out
        for ch in "\ue000\u00a0\ufe0f\u034f\u3164\u2800\u0378\u200b\u0600":
            assert ch not in out, hex(ord(ch))
        assert "U+3164" in out and "U+2800" in out and "U+E000" in out and "U+FE0F" in out
    assert "U+0600" in outs[2] and "U+200B" in outs[2] and "U+202E" in outs[2]  # the approver sees the invoice text with its markers
    assert v_ok(s, it)


def v_ok(s, it):
    v = review_page.invoice_view(s, APPROVER, it.id)
    return v.state == "REJECTED" and v.supplier.startswith("Sup")


def test_degrade_counter_is_a_copy():
    c = review_page.degraded_counts()
    c["row_not_built"] = 10**9
    assert review_page.degraded_counts().get("row_not_built", 0) != 10**9


# ---- fixes from the first independent result review ------------------------------------------------------------------------------------------------
def test_changed_while_read_has_its_own_sentence_and_refused_total_is_shown(s):
    assert "changed while it was being read" in review_page.ERROR_TEXT.get("changed_while_read", "")
    refused = tuple(inbox.Refusal(f"f{i}.txt", "changed_while_read") for i in range(100))
    v = review_page.queue_view(s, APPROVER, ui.ListQuery(), refused, SPEND_OK, refused_total=250)
    assert "250 files not processed, first 100 shown" in banner_texts(v)
    assert all(sentence == review_page.ERROR_TEXT["changed_while_read"] for _, sentence in v.refused_files)
    assert review_page.ERROR_TEXT["internal"] not in html(ui.render_list(v, review_page.session_view(APPROVER)))
    for total in (None, 100, 3):
        v = review_page.queue_view(s, APPROVER, ui.ListQuery(), refused, SPEND_OK, refused_total=total)
        assert not any("files not processed" in t for t in banner_texts(v)), total


def test_a_degraded_export_row_turns_write_off(s, monkeypatch):
    approve(s, make(s, "a"))
    approve(s, make(s, "b"))
    real = review_page._preview_row
    bad_id = workqueue.list_items(s)[0].id

    def flaky(p):
        if p.item_id == bad_id:
            raise ValueError("builder bug")
        return real(p)

    monkeypatch.setattr(review_page, "_preview_row", flaky)
    before = review_page.degraded_counts().get("export_row_not_built", 0)
    v, page = calm(export_page, s)
    out = html(page)
    assert len(v.rows) == 1 and v.may_export is False and 'name="passphrase"' not in out  # the other row is shown, but Write is off
    assert "Write is off until this is fixed." in out
    assert review_page.degraded_counts().get("export_row_not_built", 0) == before + 1
    monkeypatch.setattr(review_page, "_preview_row", real)
    assert export_page(s)[0].may_export is True  # and back on once every row can be shown


def test_a_row_the_export_would_refuse_is_listed_with_its_reason(s, monkeypatch):
    it = approve(s, make(s, "a"))
    iid = workqueue.list_items(s)[0].id
    monkeypatch.setattr(exporter, "preview_rows", lambda *a, **k: [exporter.PreviewRow(iid, None, "approval_mismatch")])
    v, _ = export_page(s)
    assert (
        v.rows == ()
        and v.results == ((iid, "Would not be written now: " + exporter.RESULT_TEXT["approval_mismatch"]),)
        and not v.may_export
    )
    assert it is not None


def test_item_page_degrades_a_contradicting_verdict_like_the_list(s, monkeypatch, caplog):
    it = make(s, "odd", flags=("D10",))
    real = review_page._approval
    monkeypatch.setattr(review_page, "_approval", lambda st, item: {**real(st, item), "may_approve": True, "approve_refusal": None})
    before = review_page.degraded_counts().get("approve_inconsistent", 0)
    with caplog.at_level(logging.WARNING, logger="intake.review_page"):
        v, page = calm(item_page, s, it.id)
    out = html(page)
    assert (
        v.may_approve is False and v.approve_refusal and 'value="approve"' not in out and 'value="reject"' in out
    )  # reject stays reachable
    assert review_page.degraded_counts().get("approve_inconsistent", 0) == before + 1
    assert any("approve_inconsistent" in r.getMessage() for r in caplog.records)


def test_viewer_never_gets_the_reason_text(s):
    it = make(s, "inv")
    reject(s, it, "paid by account 99887766 instead")
    a_v, a_page = item_page(s, it.id)
    v_v, v_page = item_page(s, it.id, who=VIEWER)
    assert a_v.decision.reason and "99887766" in html(a_page)
    assert v_v.decision.reason is None and "99887766" not in html(v_page)
    assert v_v.decision.decision == "rejected"  # the outcome itself stays visible


def test_missing_total_is_not_recorded_not_zero(s):
    it = make(s, "held", fields=None, flags=("X10",))
    v, lst = list_page(s)
    assert v.rows[0].total_minor is None and "not recorded" in html(lst) and "0.00" not in html(lst)
    iv, ipage = item_page(s, it.id)
    assert iv.total_minor is None and "not recorded" in html(ipage) and "0.00" not in html(ipage)
    v2, _ = list_page(s, query="sort=total&dir=asc")
    assert [r.item_id for r in v2.rows] == [it.id]


def test_failed_fields_are_named_and_missing_line_values_say_not_recorded(s):
    it = make(s, "inv", fields={**GOOD_FIELDS, "currency": "XXX"})  # not an allowed currency: held with X10 and the failing field names
    v, _ = item_page(s, it.id)
    assert any(b.kind == "failed_fields" and "Currency" in b.text for b in v.banners)
    import dataclasses

    good = make(s, "good")
    lines = [{"description": None, "qty": None, "unit_cost_minor": 1, "amount_minor": None}]
    shown = review_page._field_views(dataclasses.replace(good, fields={**GOOD_FIELDS, "lines": lines}))
    line = next(f for f in shown if f.name == "Line 1")
    assert "None" not in line.value and "not recorded" in line.value
    assert any(f.name == "Amount in the smallest currency unit" for f in shown)


def test_spend_total_line_wording(s):
    it = make(s, "inv")
    assert review_page._spend_line(review_page.SpendReading(1_230_000, (False, ""))).text == "Our spend counter: US$ 1.23"
    assert review_page._spend_line(None) is None and review_page._spend_line(review_page.SpendReading(None, None)) is None
    assert it is not None


def test_degrade_counter_is_exact_under_threads():
    import threading

    base = review_page.degraded_counts().get("thread_test", 0)

    def work():
        for _ in range(200):
            review_page._degrade("thread_test")

    ts = [threading.Thread(target=work) for _ in range(8)]
    [x.start() for x in ts]
    [x.join() for x in ts]
    assert review_page.degraded_counts()["thread_test"] == base + 1600


def test_ui_placeholder_grammar_and_chip_words():
    assert ui.placeholder("BANK", 2) == "<BANK_2>"
    for kind, n in (("bank", 1), ("B", 1), ("BANK", 0.5), ("BANK", True), ("BANK", 1000), ("BANK_X", 1), ("A" * 13, 1)):
        with pytest.raises(ValueError):
            ui.placeholder(kind, n)
    chip = html(ui.page("t", ui.sensitive(ui.SensitiveValue(ui.placeholder("BANK", 2), "BANK", "SECRET9"), "viewer"), session=None))
    assert "bank number 2, hidden" in chip and "SECRET9" not in chip


def test_ui_total_none_is_accepted_and_other_types_are_not():
    base = dict(item_id="inv-00000000", state="READY", supplier=None, invoice_no=None, invoice_date=None, currency="USD")
    assert ui.InvoiceView(total_minor=None, **base).total_minor is None
    for bad in (1.5, "5", True):
        with pytest.raises(TypeError):
            ui.InvoiceView(total_minor=bad, **base)


# ---- erratum 102: the export Write form carries a token of what was previewed ----------------------------------------------------------------------------
def _hidden(page, name):
    return re.findall(rf'<input type="hidden" name="{name}" value="([^"]*)">', html(page))


def test_export_token_changes_when_a_row_is_added_or_removed(s):
    a = approve(s, make(s, "a"))
    t1 = review_page.export_token(s)
    assert re.fullmatch(r"[0-9a-f]{64}", t1) and review_page.export_token(s) == t1  # stable while nothing changes
    approve(s, make(s, "b"))
    t2 = review_page.export_token(s)
    assert t2 != t1  # a row approved after the page loaded
    exporter.export_pending(s)
    t3 = review_page.export_token(s)
    assert t3 not in (t1, t2)  # a row left the pending list
    assert a is not None


def test_export_page_form_sends_the_token_back_and_it_matches_the_write_path(s):
    approve(s, make(s, "a"))
    approve(s, make(s, "b"))
    v, page = export_page(s)
    assert v.preview_token == review_page.export_token(s) and _hidden(page, "preview") == [v.preview_token]
    approve(s, make(s, "c"))
    assert review_page.export_token(s) != v.preview_token  # the service would answer 409 export_changed
    assert review_page.ERROR_TEXT["export_changed"] == (
        "The list of approved invoices changed since you opened this page. Open the page again and check the list before writing."
    )


def test_token_covers_a_row_that_could_not_be_previewed(s, monkeypatch):
    approve(s, make(s, "a"))
    approve(s, make(s, "b"))
    real = review_page._preview_row
    monkeypatch.setattr(
        review_page, "_preview_row", lambda p: (_ for _ in ()).throw(ValueError("x")) if p.item_id.startswith("a-") else real(p)
    )
    v, _ = export_page(s)
    assert v.preview_token == review_page.export_token(s)  # the write path would try both rows, so the token names both


def test_no_token_no_write_form_and_a_viewer_never_gets_it(s):
    approve(s, make(s, "a"))
    row = ui.ExportRowView("a-00000000", "S", "N", "2026-01-01", 100, "USD")
    page = ui.render_export(ui.ExportPageView(rows=(row,), kill_switch=False, may_export=True), review_page.session_view(APPROVER))
    assert 'name="preview"' not in html(page)  # no token, no hidden field: the service refuses a Write without it (6d)
    tok = review_page.export_token(s)
    ok = ui.render_export(
        ui.ExportPageView(rows=(row,), kill_switch=False, may_export=True, preview_token=tok), review_page.session_view(APPROVER)
    )
    assert _hidden(ok, "preview") == [tok]
    denied = ui.render_export(
        ui.ExportPageView(rows=(row,), kill_switch=False, may_export=True, preview_token=tok), review_page.session_view(VIEWER)
    )
    assert tok not in html(denied) and 'name="preview"' not in html(denied) and 'name="passphrase"' not in html(denied)
    with pytest.raises(Refused):
        review_page.export_view(s, VIEWER)
    for bad in ("x", "A" * 64, "a" * 63, 5):
        with pytest.raises(ValueError):
            ui.ExportPageView(rows=(), preview_token=bad)


def test_refused_total_is_a_required_keyword(s):
    with pytest.raises(TypeError):
        review_page.queue_view(s, APPROVER, ui.ListQuery(), (), SPEND_OK)


def test_empty_cells_in_the_export_preview_say_not_recorded(s, monkeypatch):
    it = approve(s, make(s, "a"))
    iid = workqueue.list_items(s)[0].id
    row = {"supplier_name": "", "invoice_no": "  ", "invoice_date": "", "total_minor": "3300", "currency": "USD"}
    monkeypatch.setattr(exporter, "preview_rows", lambda *a, **k: [exporter.PreviewRow(iid, row, None)])
    v, page = export_page(s)
    assert (v.rows[0].supplier, v.rows[0].invoice_no, v.rows[0].invoice_date) == (None, None, None)
    assert html(page).count("not recorded") >= 3 and it is not None


# ---- erratum 103: the token also covers each pending row's content code, through one shared helper ---------------------------------------------------------
def test_token_changes_when_only_the_content_code_changes(s):
    approve(s, make(s, "a"))
    t1 = review_page.export_token(s)
    ids = [i.id for i in workqueue.list_items(s)]
    with workqueue.opened(s) as c:  # a record edited in the database after the preview (under the guard that would stop it)
        drop_triggers(c)
        c.execute("UPDATE items SET fields_json = replace(fields_json, 'Acme Ltd', 'Acme Limited')")
    assert [i.id for i in workqueue.list_items(s)] == ids  # same pending ids ...
    assert review_page.export_token(s) != t1  # ... a different token


def test_both_sides_use_the_one_helper_and_agree(s, monkeypatch):
    approve(s, make(s, "a"))
    v, _ = export_page(s)
    assert v.preview_token == review_page.export_token(s)
    seen = []
    real = review_page._token_of
    monkeypatch.setattr(review_page, "_token_of", lambda conn, previews: seen.append(1) or real(conn, previews))
    review_page.export_token(s)
    export_page(s)
    assert len(seen) == 2  # one call per side, nothing else computes a token


def _pending_item(s, stem="a", **kw):
    approve(s, make(s, stem, **kw))
    return [i for i in workqueue.list_items(s) if i.state == "APPROVED"][-1]


def test_token_changes_with_a_second_approve_decision(s):
    """m1: a later approve row (other approver, other time) changes approved_by and approved_at in the CSV row, so it must change the token."""
    it = _pending_item(s)
    before = review_page.export_token(s)
    from intake import content_code

    with workqueue.opened(s) as c:
        drop_triggers(c)
        c.execute(
            "INSERT INTO decisions (item_uid, decision, approver, reason, content_code, at) VALUES (?, 'approve', 'ap-b', NULL, ?, '2026-11-04T12:00:00Z')",
            (it.uid, content_code.content_code(it)),
        )
    assert review_page.export_token(s) != before


def test_token_changes_with_a_second_decision_that_looks_identical(s):
    """The latest decision's seq is in the token on its own: a repeated approve row with the same approver and time leaves every CSV cell as it was."""
    it = _pending_item(s)
    before = review_page.export_token(s)
    from intake import content_code

    with workqueue.opened(s) as c:
        drop_triggers(c)
        last = workqueue.latest_decision(c, it.uid)
        c.execute(
            "INSERT INTO decisions (item_uid, decision, approver, reason, content_code, at) VALUES (?, 'approve', ?, NULL, ?, ?)",
            (it.uid, last.approver, content_code.content_code(it), last.at),
        )
    assert review_page.export_view(s, APPROVER).rows[0].invoice_no == "INV-1001"  # the page shows the same row ...
    assert review_page.export_token(s) != before  # ... under a different token


def test_token_changes_when_a_setting_changes_what_a_write_would_do(s):
    """m2: the currency list is a setting; with USD removed the same row would be refused, so a Write would do something else."""
    import dataclasses

    _pending_item(s)
    before = review_page.export_token(s)
    s2 = dataclasses.replace(s, service=dataclasses.replace(s.service, currencies=("EUR",)))
    assert review_page.export_token(s2) != before
    assert review_page.export_view(s2, APPROVER).rows == ()  # and the page for those settings shows the refusal, not the row


def test_token_changes_for_raw_duplicate_flags_even_though_the_content_code_does_not(s):
    """m3: build_row writes the flags as stored; content_code dedupes them. The token follows the CSV text."""
    from intake import content_code

    it = make(s, "a", flags=("D06",))
    approve(s, it, "checked against the purchase order")
    item = [i for i in workqueue.list_items(s) if i.state == "APPROVED"][0]
    before = review_page.export_token(s)
    with workqueue.opened(s) as c:
        drop_triggers(c)
        c.execute("UPDATE items SET flags_json = ? WHERE uid = ?", ('["D06","D06"]', item.uid))
    again = workqueue.get(s, item.id)
    assert content_code.content_code(again) == content_code.content_code(item)  # the old token (id + content code) could not see this
    assert review_page.export_token(s) != before


def test_two_different_refusal_codes_give_different_tokens(s):
    _pending_item(s)
    iid = workqueue.list_items(s)[0].id
    with workqueue.connect_readonly(s) as c:
        a = review_page._token_of(c, [exporter.PreviewRow(iid, None, "approval_mismatch")])
        b = review_page._token_of(c, [exporter.PreviewRow(iid, None, "not_approvable")])
    assert a != b and re.fullmatch(r"[0-9a-f]{64}", a)


def test_page_token_is_computed_from_the_rows_it_shows(s, monkeypatch):
    """A row approved after the preview was read is not in the page's token, so a Write with that token is refused by the service (no 'degraded' state)."""
    _pending_item(s, "a")
    real = exporter.preview_rows
    seen: list = []

    def preview_then_approval_lands(*a, **k):
        out = real(*a, **k)
        seen[:] = out  # the rows the page was built from (replace, never append)
        approve(s, make(s, "b", fields={**GOOD_FIELDS, "invoice_no": "INV-2002"}))
        return out

    monkeypatch.setattr(exporter, "preview_rows", preview_then_approval_lands)
    v, _ = calm(export_page, s)
    monkeypatch.setattr(exporter, "preview_rows", real)
    assert len(v.rows) == 1 and len(seen) == 1
    with workqueue.connect_readonly(s) as c:
        assert v.preview_token == review_page._token_of(
            c, seen
        )  # made from exactly the rows the page shows (a token of no rows is another value)
    assert v.preview_token != review_page.export_token(s)  # and not the token of the list as it is now


# ---- the token costs one decision query however many rows are pending ----------------------------------------------------------------------------------
def _approved(s, n, start=0):
    for i in range(start, start + n):
        approve(s, make(s, f"r{i}", fields={**GOOD_FIELDS, "invoice_no": f"INV-{3000 + i}"}))


def _reference_token(s):
    """The slow way (an item read and a decision read per row), the token as it was defined before the one-query change."""
    import hashlib as h
    import json as j

    with workqueue.connect_readonly(s) as c:
        parts = []
        for p in exporter.preview_rows(s, conn=c):
            d = workqueue.latest_decision(c, workqueue.get_in(c, p.item_id).uid)
            body = j.dumps(p.row, sort_keys=True, ensure_ascii=True) if p.row is not None else "refused:" + (p.refusal or "")
            parts.append(f"{p.item_id}|{'-' if d is None else d.seq}|{body}")
    return h.sha256(chr(10).join(parts).encode("utf-8")).hexdigest()


def test_token_is_unchanged_by_the_one_query_read(s):
    _approved(s, 3)
    assert review_page.export_token(s) == _reference_token(s)


def test_token_costs_a_constant_number_of_statements(s):
    def statements(n, start):
        _approved(s, n, start)
        c = workqueue.connect_readonly(s)
        try:
            previews = exporter.preview_rows(s, conn=c)
            seen = []
            c.set_trace_callback(seen.append)
            review_page._token_of(c, previews)
            return len(seen), len(previews)
        finally:
            c.close()

    one, n1 = statements(1, 0)
    many, n2 = statements(6, 1)  # 7 pending rows in all
    assert n2 > n1 and one == many == 1  # exactly one query, whatever the number of pending rows
    assert review_page._token_of(None, []) == review_page._token_of(None, [])  # no queue file: no query at all


def test_one_query_token_still_follows_the_latest_decision(s):
    _approved(s, 2)
    it = [i for i in workqueue.list_items(s) if i.state == "APPROVED"][1]
    before = review_page.export_token(s)
    from intake import content_code

    with workqueue.opened(s) as c:
        drop_triggers(c)
        last = workqueue.latest_decision(c, it.uid)
        c.execute(
            "INSERT INTO decisions (item_uid, decision, approver, reason, content_code, at) VALUES (?, 'approve', ?, NULL, ?, ?)",
            (it.uid, last.approver, content_code.content_code(it), last.at),
        )
    assert review_page.export_token(s) != before
    assert review_page.export_token(s) == _reference_token(s)


def test_latest_decision_seqs_matches_the_per_row_reads_and_the_pending_order(s):
    _approved(s, 4)
    forged = workqueue.list_items(s)[
        0
    ]  # an APPROVED item that already has a receipt (inconsistent data): not pending, as for approved_unexported
    with workqueue.opened(s) as c:
        drop_triggers(c)
        c.execute(
            "INSERT INTO exports (row_id, item_uid, content_code, row_json, at) VALUES (?, ?, ?, '{}', '2026-11-04T12:00:00Z')",
            ("f" * 64, forged.uid, "c" * 64),
        )
    exported_id = forged.id
    pending = [i for i in workqueue.list_items(s) if i.state == "APPROVED" and i.id != exported_id]
    reject(s, make(s, "x"))  # a decided item that is not pending must not appear
    with workqueue.connect_readonly(s) as c:
        seqs = workqueue.latest_decision_seqs(c)
        assert list(seqs) == [i.id for i in workqueue.approved_unexported(c)]
        assert exported_id not in seqs and len(seqs) == 3
        assert seqs == {i.id: workqueue.latest_decision(c, i.uid).seq for i in pending}
