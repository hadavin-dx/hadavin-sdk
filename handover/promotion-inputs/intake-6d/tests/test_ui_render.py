"""The 12 slice-1 states render from fixtures alone (no database): headers, wording, role gates, no script, no outside asset."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import ui_fixtures as fx

from intake import flags as flagtable
from intake import ui

PAGES = fx.pages()
BANNED_WORDS = ("hard cap", "real ceiling", "audit chain", "tamper-evident", "verified trail", "model_mismatch", "bank detail ")
LOGOUT_FORM = '<form method="post" action="/logout">'


def _text(markup: str) -> str:
    return re.sub(r"<[^>]+>", " ", markup.split("</style>", 1)[1])


@pytest.mark.parametrize("name", sorted(PAGES))
def test_page_is_a_complete_script_free_document(name):
    p = PAGES[name]
    s = str(p.html)
    assert p.profile == "strict" and p.status == 200
    assert s.startswith("<!DOCTYPE html>") and s.count("<style>") == 1 and s.count("<html") == 1
    low = s.lower()
    for bad in (
        "<script",
        "javascript:",
        "<link",
        "<img",
        "<iframe",
        "<object",
        "<embed",
        "http://",
        "https://",
        "@import",
        "url(",
        " style=",
    ):
        assert bad not in low, (name, bad)
    assert not re.search(r"\son[a-z]+\s*=", low), name
    assert "prefers-color-scheme: dark" in s and "data-theme" not in s and "cookie" not in low


@pytest.mark.parametrize("name", sorted(PAGES))
def test_no_forbidden_wording_on_any_page(name):
    low = _text(str(PAGES[name].html)).lower()
    for w in BANNED_WORDS:
        assert w not in low, (name, w)


def test_forms_are_quoted_post_with_csrf():
    for name, p in PAGES.items():
        s = str(p.html)
        for m in re.finditer(r"<form[^>]*>", s):
            assert 'method="post"' in m.group(0) and re.search(r'action="/[^"]*"', m.group(0)), (name, m.group(0))
        if name != "01-login":
            assert s.count("<form") == s.count('name="csrf"'), name
    assert "Sign out" in str(PAGES["05-item-d10-viewer"].html)
    assert 'name="decision"' not in str(PAGES["05-item-d10-viewer"].html)


def test_d10_invoice_offers_reject_only_and_d06_offers_both_with_a_required_reason():
    d10 = str(PAGES["04-item-d10-approver"].html)
    assert 'value="reject"' in d10 and 'value="approve"' not in d10 and "Approve is not offered" in d10
    d06 = str(PAGES["03-item-d06"].html)
    assert 'value="approve"' in d06 and 'value="reject"' in d06 and "Reason for approving (required)" in d06
    assert "The total does not equal the lines plus adjustments." in d06
    ready = str(PAGES["06-item-ready"].html)
    assert 'value="approve"' in ready and "Reason for approving (optional)" in ready


def test_ui_has_no_approval_rule_of_its_own_it_follows_the_view():
    # the view builder (decision module) decides; ui.py only draws what the view says
    off = fx.inv_b(flags=(ui.flag_view("D06"),), may_approve=False, approve_refusal="Approve is not offered here.")
    out = str(ui.render_item(off, fx.APPROVER).html)
    assert 'value="approve"' not in out and "Approve is not offered here." in out and 'value="reject"' in out
    on = fx.inv_b(flags=(ui.flag_view("D06"),), may_approve=True, approve_needs_reason=False)
    out = str(ui.render_item(on, fx.APPROVER).html)
    assert 'value="approve"' in out and "Reason for approving (optional)" in out  # the view decides whether the reason is required
    out = str(ui.render_item(fx.inv_a(approve_needs_reason=True), fx.APPROVER).html)
    assert "Reason for approving (required)" in out
    assert "Approve is not offered for this invoice." in str(ui.render_item(fx.inv_a(may_approve=False), fx.APPROVER).html)


def test_reason_boxes_are_single_line_with_a_length_limit_and_reject_needs_a_reason():
    for v in (fx.inv_a(), fx.inv_b(), fx.inv_a(reason_max_chars=77)):
        s = str(ui.render_item(v, fx.APPROVER).html)
        assert "<textarea" not in s
        inputs = re.findall(r'<input type="text" name="reason"[^>]*>', s)
        assert len(inputs) == 2 and all(f'maxlength="{v.reason_max_chars}"' in i and 'autocomplete="off"' in i for i in inputs)
        reject_form = s[s.index('value="reject"') :]
        assert "Reason for rejecting (required)" in reject_form and "required" in re.search(
            r'<input type="text" name="reason"[^>]*>', reject_form
        ).group(0)
        assert 'value=""' not in s and "placeholder=" not in s  # nothing pre-filled or suggested
    ready = str(ui.render_item(fx.inv_a(), fx.APPROVER).html)
    approve_form = ready[ready.index('value="approve"') : ready.index('value="reject"')]
    assert "required" not in re.search(r'<input type="text" name="reason"[^>]*>', approve_form).group(0)
    needed = str(ui.render_item(fx.inv_b(), fx.APPROVER).html)
    approve_form = needed[needed.index('value="approve"') : needed.index('value="reject"')]
    assert "required" in re.search(r'<input type="text" name="reason"[^>]*>', approve_form).group(0)


def test_no_decision_form_after_a_decision_or_for_a_viewer():
    assert "<form" not in str(PAGES["07-item-approved"].html).replace(LOGOUT_FORM, "")
    assert 'name="decision"' not in str(ui.render_item(fx.inv_b(), fx.VIEWER).html)


def test_label_map_matches_the_flag_table():
    for code, (sentence, reject_only) in ui.FLAG_TEXT.items():
        assert sentence.endswith(".") and "  " not in sentence
        if code in flagtable.FLAGS:
            f = flagtable.FLAGS[code]
            assert f.reject_only is reject_only, code
            assert f.needs_reason is (not reject_only), code
    assert set(flagtable.FLAGS) <= set(ui.FLAG_TEXT), "every flag code has a sentence"
    assert set(ui.FLAG_TEXT) - set(flagtable.FLAGS) == {"M01", "M02"}  # held-back flags the masking step adds; neutral wording, reject-only
    for code in ("M01", "M02"):
        assert ui.FLAG_TEXT[code][1] is True and ui.flag_view(code).reject_only and "held back" in ui.FLAG_TEXT[code][0]


def test_unknown_flag_code_gets_the_neutral_reject_only_fallback():
    f = ui.flag_view("Z99")
    assert f.reject_only and "no sentence for" in f.sentence and f.code == "Z99"


def test_viewer_page_has_no_planted_original_and_no_invoice_text():
    viewer = str(PAGES["05-item-d10-viewer"].html)
    for planted in fx.PLANTED:
        assert planted not in viewer, planted
    assert "Invoice text is shown to the approver only." in viewer
    assert "bank number 1, hidden" in viewer and "bank number 2, hidden" in viewer


def test_approver_sees_the_restored_values_exactly():
    s = str(PAGES["04-item-d10-approver"].html)
    assert fx.BANK_ON_FILE in s and fx.BANK_IN_TEXT in s and "Please pay to account" in s


def test_a_viewer_session_never_sees_originals_even_if_the_builder_wrongly_passes_them():
    leak = fx.inv_c("approver")  # restored values and text present: ui.sensitive and the item page must still hide them
    out = str(ui.render_item(leak, fx.VIEWER).html)
    for planted in fx.PLANTED:
        assert planted not in out, planted


def test_missing_map_shows_the_placeholders_and_the_plain_sentence():
    v = fx.inv_c(
        bank_on_file=ui.SensitiveValue("<BANK_1>", "BANK", None),
        bank_in_text=(ui.SensitiveValue("<BANK_2>", "BANK", None),),
        restore_available=False,
    )
    s = str(ui.render_item(v, fx.APPROVER).html)
    assert "Original values are not available for this invoice; decide from what is shown or reject." in s
    assert "bank number 1, original not available" in s


def test_forged_placeholder_in_the_invoice_text_is_marked_not_a_chip():
    v = fx.inv_a(source_text="pay <BANK_1> and <EMAIL_9> today")
    s = str(ui.render_item(v, fx.APPROVER).html)
    assert s.count("not from our masking") == 2 and 'class="chip"' not in s


def test_money_is_right_aligned_with_a_currency_code():
    s = str(PAGES["02-list-after-scan"].html)
    assert '<td class="num">1,250.00 USD</td>' in s and '<td class="num">480.50 EUR</td>' in s and '<td class="num">9,100.00 GBP</td>' in s
    assert str(ui.money(-5, "JPY")) == "-5 JPY" and str(ui.money(7, "USD")) == "0.07 USD"
    with pytest.raises(TypeError):
        ui.money(1.5, "USD")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ui.money(True, "USD")  # type: ignore[arg-type]


def test_spend_wording_and_meter():
    s = str(PAGES["11-overview"].html)
    assert "Spent US$ 3.20 of US$ 100.00 (our spend counter)." in s and "Limit at the provider: US$ 90.00." in s
    assert 'width="3"' in s and "3 invoice(s) in this run." in s
    halted = str(PAGES["12-overview-banners"].html)
    assert "Spending halted" in halted and "Our spend counter stopped new AI calls. Run intake check." in halted
    assert (
        "the limit was reached" not in halted.split("</style>", 1)[1].split("Status messages", 1)[1].split("</section>", 1)[1]
    )  # never the reason
    assert "Status unavailable: scan state" in halted
    assert str(ui.usd_micro(1)) == "less than US$ 0.01" and str(ui.usd_micro(0)) == "US$ 0.00"
    assert str(ui.usd_micro(-1)) == "less than US$ 0.01" or str(ui.usd_micro(-1)) == "US$ 0.00"
    assert "-" not in str(ui.usd_micro(-4_999)) and str(ui.usd_micro(-5_000)) == "-US$ 0.01"
    assert (
        str(ui.money(-5, "USD")) == "-0.05 USD"
        and str(ui.money(5, "USD")) == "0.05 USD"
        and str(ui.money(-1_234_567, "USD")) == "-12,345.67 USD"
    )


def test_overview_never_shows_unknown_spend_as_not_halted():
    base = dict(counts_by_state=(), n_items=0, spend_cap_micro=100_000_000, provider_limit_micro=None, prices_date=None)
    for halted, spent in ((None, 5), (False, None), (None, None)):
        s = str(ui.render_overview(ui.OverviewView(spend_settled_micro=spent, halted=halted, **base), fx.APPROVER).html)
        assert "Spending status unavailable" in s and "Run intake check" in s
        assert "our spend counter)." not in s and "Spending halted" not in s and 'class="big"' not in s and 'class="meter"' not in s
    ok = str(ui.render_overview(ui.OverviewView(spend_settled_micro=5, halted=False, **base), fx.APPROVER).html)
    assert "Spending status unavailable" not in ok and "Spending halted" not in ok
    halted = str(ui.render_overview(ui.OverviewView(spend_settled_micro=5, halted=True, **base), fx.APPROVER).html)
    assert "Spending halted" in halted and "Spending status unavailable" not in halted


def test_empty_states_state_the_real_count():
    s = str(ui.render_list(ui.QueueView((), ui.ListQuery()), fx.APPROVER).html)
    assert "0 invoices match this view." in s
    s = str(ui.render_overview(ui.OverviewView((), 0, 0, None, None, (False, None), None), fx.APPROVER).html)
    assert "0 invoices in this run." in s and "no limit is recorded" in s


def test_sort_links_are_built_by_url_and_active_filter_is_marked():
    q = ui.QueueView(
        tuple(ui.apply_query((fx.inv_a(), fx.inv_b()), ui.ListQuery("total", "asc", None))), ui.ListQuery("total", "asc", None)
    )
    s = str(ui.render_list(q, fx.APPROVER).html)
    assert 'href="/?dir=desc&amp;sort=total"' in s and 'aria-current="true"' in s


def test_tokens_file_is_read_from_the_package_and_inlined_once():
    css = re.sub(r"/\*.*?\*/\s*", "", Path(ui.__file__).with_name("ui_tokens.css").read_text(encoding="utf-8"), flags=re.DOTALL)
    assert "/*" not in css and len(css) > 3000
    assert css in str(PAGES["01-login"].html)


def test_bars_never_overflow_their_track():
    over = str(ui.count_bar("x", 50, 3))
    assert 'width="360" height="8"/><text' in over and over.count('width="360"') == 2
    assert 'class="fill t-bad" x="0" y="0" width="100"' in str(ui.spend_meter(500, 100, False))
    assert 'width="0"' in str(ui.count_bar("x", 0, 3)) and 'width="0"' not in str(ui.count_bar("x", 1, 1000))


# ---------------------------------------------------------------------------------------------- export, login, style hash
def _export(view, session=fx.APPROVER):
    return ui.render_export(view, session)


def test_export_page_is_approver_only_in_the_nav_the_rows_and_the_render():
    viewer = _export(ui.ExportPageView((fx.export_row(),), kill_switch=False, may_export=True), fx.VIEWER)
    out = str(viewer.html)
    assert (
        viewer.status == 403
        and fx.export_row().supplier not in out
        and fx.export_row().invoice_no not in out
        and "<form" not in out.replace(LOGOUT_FORM, "")
    )
    assert "Not allowed" in out
    for name, p in PAGES.items():
        nav = str(p.html).split("</style>", 1)[1]
        if name.startswith("05"):
            assert 'href="/export"' not in nav and 'href="/overview"' in nav
        elif name != "01-login":
            assert 'href="/export"' in nav
    assert 'href="/export"' not in str(ui.render_list(ui.QueueView((), ui.ListQuery()), fx.VIEWER).html)
    assert 'href="/export"' not in str(ui.render_overview(ui.OverviewView((), 0, 0, None, None, False, None), fx.VIEWER).html)


@pytest.mark.parametrize("kill", [None, True])
def test_export_has_no_write_form_and_shows_the_engaged_banner_unless_the_switch_is_known_off(kill):
    out = str(_export(ui.ExportPageView((fx.export_row(),), kill_switch=kill, may_export=True)).html)
    assert "Write 1 invoice" not in out and 'name="passphrase"' not in out and "Export is switched off" in out
    assert fx.export_row().invoice_no in out  # the preview stays readable


def test_export_write_form_only_when_the_switch_is_known_off_and_export_is_allowed():
    on = str(_export(ui.ExportPageView((fx.export_row(),), kill_switch=False, may_export=True)).html)
    assert "Write 1 invoice(s) to the spreadsheet file" in on and "Export is switched off" not in on
    assert 'type="password" name="passphrase" autocomplete="off" required' in on and 'name="csrf"' in on
    assert "Write 1 invoice" not in str(_export(ui.ExportPageView((fx.export_row(),), kill_switch=False, may_export=False)).html)
    assert "Write 1 invoice" not in str(_export(ui.ExportPageView((), kill_switch=False, may_export=True)).html)
    default = str(_export(ui.ExportPageView((fx.export_row(),), may_export=True)).html)
    assert "Write 1 invoice" not in default and "Export is switched off" in default  # the default view fails closed


def test_export_result_page_shows_results_file_text_skipped_and_refusal():
    v = ui.ExportPageView(
        (), kill_switch=False, results=((fx.ID_A, "Written."), (fx.ID_B, "Refused: changed since approval.")), file_text="File left as it was.",
        skipped=("cd" * 32,), refusal="The passphrase was not accepted.",
    )  # fmt: skip
    out = str(_export(v).html)
    for needle in (
        fx.ID_A,
        "Written.",
        "Refused: changed since approval.",
        "File left as it was.",
        "cd" * 32,
        "The passphrase was not accepted.",
    ):
        assert needle in out, needle
    assert "Nothing to export" not in out


def test_login_page_has_the_csrf_field_and_no_stored_passphrase_hint():
    p = ui.render_login(csrf="tok-123")
    out = str(p.html)
    assert 'name="csrf" value="tok-123"' in out and 'name="passphrase" autocomplete="off"' in out and "current-password" not in out
    err = ui.render_login("Sign-in failed.", csrf="tok-9", banners=(ui.BannerView("demo", "Only made-up files.", "info"),))
    assert err.status == 401 and "Sign-in failed." in str(err.html) and "Only made-up files." in str(err.html)
    with pytest.raises(TypeError):
        ui.render_login()  # type: ignore[call-arg]


def test_style_hash_is_the_sha256_of_the_exact_text_inside_the_style_element_and_no_style_attribute_exists():
    import base64
    import hashlib

    for name, p in PAGES.items():
        s = str(p.html)
        inner = re.search(r"<style>(.*?)</style>", s, re.S).group(1)
        digest = base64.b64encode(hashlib.sha256(inner.encode("utf-8")).digest()).decode()
        assert digest == ui.STYLE_SHA256, name
        assert not re.search(r"<[a-z][^>]*\sstyle\s*=", s, re.I), name


def test_decision_outcome_says_recorded_as_the_login_name():
    s = str(PAGES["07-item-approved"].html)
    assert "Recorded as" in s and ">By<" not in s


def test_empty_states_are_not_boxes_inside_cards():
    s = str(ui.render_item(fx.inv_a(fields=()), fx.APPROVER).html)
    assert "Intake stored no extracted values for this invoice." in s and 'class="empty"' not in s
    s = str(ui.render_overview(ui.OverviewView((), 0, 0, None, None, False, None), fx.APPROVER).html)
    assert 'class="empty"' not in s


# ---------------------------------------------------------------------------------------------- fail-closed consistency (MJ2), kill switch (MJ4)
@pytest.mark.parametrize("code", ["D10", "M01", "M02", "L01", "X10", "L02", "Z99"])
def test_a_view_that_says_may_approve_next_to_a_reject_only_flag_is_refused(code):
    with pytest.raises(ValueError):
        fx.inv_b(flags=(ui.flag_view(code),), may_approve=True)
    with pytest.raises(ValueError):  # a flag built by hand with the wrong tone: an unknown or reject-only code still counts
        fx.inv_b(flags=(ui.FlagView(code, "x", "warn", False),), may_approve=True)
    assert fx.inv_b(flags=(ui.flag_view(code),), may_approve=False).may_approve is False


def test_may_approve_next_to_a_refusal_sentence_is_refused_and_the_allowed_flags_pass():
    with pytest.raises(ValueError):
        fx.inv_a(may_approve=True, approve_refusal="Approve is not offered.")
    for code in ("D06", "D12"):
        assert fx.inv_b(flags=(ui.flag_view(code),), may_approve=True).may_approve is True


@pytest.mark.parametrize("state", ["RECEIVED", "REJECTED", "EXPORTED", "APPROVED", "SOMETHING_ELSE"])
def test_no_decision_form_for_an_item_that_is_not_waiting_for_a_person(state):
    out = str(ui.render_item(fx.inv_a(state, may_approve=True), fx.APPROVER).html)
    assert "<form" not in out.replace(LOGOUT_FORM, "") and 'name="decision"' not in out


def test_no_decision_form_when_a_decision_is_already_recorded_even_in_a_waiting_state():
    v = fx.inv_a("READY", may_approve=True, decision=ui.DecisionView("approved", "ap-a", "t", None))
    assert 'name="decision"' not in str(ui.render_item(v, fx.APPROVER).html)


def test_export_banner_and_write_form_never_show_together_whatever_the_caller_says():
    row = fx.export_row()
    banner = (ui.KILL_SWITCH_ENGAGED,)
    for kill in (False, None, True):
        out = str(ui.render_export(ui.ExportPageView((row,), kill_switch=kill, may_export=True, banners=banner), fx.APPROVER).html)
        assert "Export is switched off" in out and "Write 1 invoice" not in out and 'name="passphrase"' not in out, kill
    # a banner of the same kind with other words counts too
    other = (ui.BannerView("kill_switch", "Switch is on", "bad"),)
    out = str(ui.render_export(ui.ExportPageView((row,), kill_switch=False, may_export=True, banners=other), fx.APPROVER).html)
    assert "Write 1 invoice" not in out and out.count("Switch is on") == 1 and "Export is switched off" not in out
    ok = str(ui.render_export(ui.ExportPageView((row,), kill_switch=False, may_export=True), fx.APPROVER).html)
    assert "Write 1 invoice" in ok and "Export is switched off" not in ok


# ---------------------------------------------------------------------------------------------- accessibility, receipt
def test_sortable_headers_say_how_they_are_sorted():
    rows = (fx.inv_a(), fx.inv_b())
    for q, expect in (
        (ui.ListQuery(), {"supplier": "none", "total": "none", "state": "none"}),
        (ui.ListQuery("total", "asc", None), {"supplier": "none", "total": "ascending", "state": "none"}),
        (ui.ListQuery("state", "desc", None), {"supplier": "none", "total": "none", "state": "descending"}),
    ):
        s = str(ui.render_list(ui.QueueView(rows, q), fx.APPROVER).html)
        heads = re.findall(r'<th scope="col"[^>]*aria-sort="([a-z]+)"[^>]*><a href="[^"]*sort=([a-z]+)', s)
        assert {k: v for v, k in heads} == expect, (q, heads)
    assert s.split("</style>", 1)[1].count("aria-sort") == 3  # only sortable columns carry it


def test_banners_are_announced_and_an_engaged_kill_switch_is_an_alert():
    out = str(
        ui.render_overview(
            ui.OverviewView((), 0, 1, None, None, False, None, (ui.BannerView("demo", "hello", "info"), ui.KILL_SWITCH_ENGAGED)),
            fx.APPROVER,
        ).html
    )
    assert '<div class="banner t-info" role="status">' in out and '<div class="banner t-bad" role="alert">' in out
    assert out.count('role="status"') == 1


def test_an_exported_item_shows_its_receipt():
    v = fx.inv_a("EXPORTED", may_approve=False, export=ui.ExportView("cd" * 32, "2026-11-04 11:00", "abcd1234"))
    out = str(ui.render_item(v, fx.APPROVER).html)
    assert "Written to the spreadsheet file" in out and "cd" * 32 in out and "abcd1234" in out and "2026-11-04 11:00" in out
    assert (
        "Written to the spreadsheet file"
        not in str(ui.render_item(fx.inv_a(), fx.APPROVER).html).split("</style>", 1)[1].split("Invoice text", 1)[0]
    )


# ---------------------------------------------------------------------------------------------- round 4
def test_flag_chip_never_promises_an_approve_button_the_view_would_refuse():
    for code in ("D10", "M01", "Z99"):
        out = str(ui.flag_chip(ui.FlagView(code, "x", "warn", False)))  # hand-built with the wrong tone
        assert "may only reject" in out and "t-bad" in out and "may approve" not in out, code
    ok = str(ui.flag_chip(ui.flag_view("D06")))
    assert "may approve" in ok and "t-warn" in ok


def test_a_look_alike_in_a_clipped_list_cell_shows_a_bang_and_the_item_page_shows_the_sentence():
    v = fx.inv_a(supplier="Acme <BANK_1>", invoice_no="INV <EMAIL_2>")
    lst = str(ui.render_list(ui.QueueView((v,), ui.ListQuery()), fx.APPROVER).html).split("</style>", 1)[1]
    assert lst.count('class="forged">! ') == 2 and "forged-note" not in lst and "not from our masking" not in lst
    item = str(ui.render_item(v, fx.APPROVER).html).split("</style>", 1)[1]
    assert item.count("not from our masking") >= 2


def test_the_receipt_is_shown_to_a_viewer_without_any_original_value():
    v = fx.inv_c(
        "viewer", state="EXPORTED", may_approve=False, approve_refusal=None, export=ui.ExportView("cd" * 32, "2026-11-04 11:00", "abcd1234")
    )
    out = str(ui.render_item(v, fx.VIEWER).html)
    assert "abcd1234" in out and "cd" * 32 in out and "Written to the spreadsheet file" in out
    for planted in fx.PLANTED:
        assert planted not in out
    assert "<form" not in out.replace(LOGOUT_FORM, "")


def test_typed_markers_in_field_names_recorded_as_and_results_are_not_real_markers():
    zw = chr(0x200B)
    inv = fx.inv_a(fields=(ui.FieldView("Na" + zw + "me", "v", True),))
    out = str(ui.render_item(inv, fx.APPROVER).html)
    assert 'Na<span class="mark">&lt;U+200B&gt;</span>me' in out
    dec = fx.inv_a("APPROVED", may_approve=False, decision=ui.DecisionView("approved", "ap" + zw + "a", "2026-11-04 10:00", None))
    assert 'ap<span class="mark">&lt;U+200B&gt;</span>a' in str(ui.render_item(dec, fx.APPROVER).html)
    res = ui.ExportPageView((), kill_switch=False, results=(("i" + zw, "o" + zw),))
    assert str(ui.render_export(res, fx.APPROVER).html).count('class="mark"') == 2


def test_a_stack_of_combining_marks_in_the_invoice_number_cannot_leave_the_title_box():
    zalgo = "INV" + "".join(chr(0x300 + i) for i in range(200))
    out = str(ui.render_item(fx.inv_a(invoice_no=zalgo), fx.APPROVER).html)
    body = out.split("</style>", 1)[1]
    h1 = re.search(r"<h1>(.*?)</h1>", body, re.S).group(1)
    assert h1.startswith("Invoice INV") and chr(0x300) in h1  # the text is shown, not stripped
    assert "<title>Invoice INV" in out


# ---------------------------------------------------------------------------------------------- round 5
@pytest.mark.parametrize(
    "junk", ["I" * 4000, "".join(chr(0x300 + i % 100) for i in range(4000)), "INV" + chr(0x301) * 4000, "\u202e" * 500]
)
def test_the_title_is_capped_and_the_decision_form_stays_near_the_top(junk):
    v = fx.inv_b(invoice_no=junk)
    out = str(ui.render_item(v, fx.APPROVER).html)
    body = out.split("</style>", 1)[1]
    h1 = re.search(r"<h1>(.*?)</h1>", body, re.S).group(1)
    assert len(h1) < 1500 and h1.startswith("Invoice ")
    title = re.search(r"<title>(.*?)</title>", out, re.S).group(1)
    assert len(title) < 1500
    assert body.index('name="decision"') < 40_000  # the Approve and Reject forms are not pushed thousands of lines down
    assert len(out) < 200_000
    # the Invoice card still holds the whole (marked) value
    assert body.count("INV") >= 0


def test_the_title_cuts_at_sixty_characters_and_marks_the_cut():
    assert ui._title("A" * 60) == "Invoice " + "A" * 60
    assert ui._title("A" * 61) == "Invoice " + "A" * 60 + "\u2026"
    assert ui._title(None) == "Invoice" and ui._title("") == "Invoice"
    short = str(ui.render_item(fx.inv_a(invoice_no="INV-1"), fx.APPROVER).html)
    assert "<h1>Invoice INV-1</h1>" in short


def test_the_list_carries_state_and_flags_in_the_first_cell_for_narrow_screens():
    out = str(PAGES["02-list-after-scan"].html).split("</style>", 1)[1]
    rows = re.findall(r"<tr>(.*?)</tr>", out.split("<tbody>", 1)[1])
    assert len(rows) == 3
    for r in rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)
        assert 'class="narrow-meta"' in cells[0] and "pill" in cells[0]
        tds = re.findall(r"<td([^>]*)>", r)
        assert tds[4] == ' class="meta"' and tds[5] == ' class="meta"'
    assert re.findall(r"<th scope=\"col\"( class=\"meta\")?[^>]*>", out).count(' class="meta"') == 2
    assert "D10" in rows[1] and rows[1].count("D10") == 2  # once in the narrow cell, once in the Flags column


def test_a_scrolling_table_is_a_named_focusable_region():
    for name in ("02-list-after-scan", "08-list-after-decisions", "09-export-preview"):
        out = str(PAGES[name].html).split("</style>", 1)[1]
        m = re.search(r'<div class="table-wrap" role="region" tabindex="0" aria-label="([^"]+)">', out)
        assert m and "invoice" in m.group(1), name
