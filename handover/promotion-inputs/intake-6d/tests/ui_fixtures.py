"""Made-up view objects for the 12 slice-1 states (portal contract, section 1). No database, no real data: the pages render from these alone."""

from __future__ import annotations

from intake import ui

APPROVER = ui.SessionView("ap-a", "approver", "csrf-token-1")
VIEWER = ui.SessionView("viewer-1", "viewer", "csrf-token-2")

ID_A = "invoice-a-1a2b3c4d"
ID_B = "invoice-b-2b3c4d5e"
ID_C = "invoice-c-3c4d5e6f"
ROW_ID = "ab" * 32  # 64 hex

BANK_ON_FILE = "ACCT-" + "0011" + "2233"  # planted originals: they must never reach a viewer page
BANK_IN_TEXT = "ACCT-" + "9988" + "7766"
TEXT_ORIGINAL = f"Invoice C. Please pay to account {BANK_IN_TEXT}. Contact billing@" + "example.test"
PLANTED = (BANK_ON_FILE, BANK_IN_TEXT, "billing@" + "example.test", "Please pay to account")
D10_REFUSAL = "Approve is not offered: a flagged problem on this invoice allows rejecting only."
D06_REFUSAL_NONE = None


def _bank(n: int, restored: str | None) -> ui.SensitiveValue:
    return ui.SensitiveValue(f"<BANK_{n}>", "BANK", restored)


def inv_a(state: str = "READY", **kw) -> ui.InvoiceView:
    base = dict(
        item_id=ID_A, state=state, supplier="Northwind Test Supplies", invoice_no="INV-A-001", invoice_date="2026-10-02",
        total_minor=125_000, currency="USD", flags=(), content_code="a1b2c3d4e5f6", version=1, may_approve=True,
        created_at="2026-11-04T09:00:01Z", order=1,
        fields=(ui.FieldView("Supplier", "Northwind Test Supplies", True), ui.FieldView("Invoice number", "INV-A-001", True),
                ui.FieldView("Total", "1,250.00 USD", True)),
        source_text="Invoice A from Northwind Test Supplies. Total 1,250.00 USD.",
    )  # fmt: skip
    base.update(kw)
    return ui.InvoiceView(**base)


def inv_b(**kw) -> ui.InvoiceView:
    base = dict(
        item_id=ID_B, state="NEEDS_PERSON", supplier="Contoso Sample Parts", invoice_no="INV-B-002", invoice_date="2026-10-03",
        total_minor=48_050, currency="EUR", flags=(ui.flag_view("D06"),), content_code="b1b2b3b4b5b6", version=1, may_approve=True,
        approve_needs_reason=True, created_at="2026-11-04T09:00:02Z", order=2,
        source_text="Invoice B. Lines 400.00 and 80.50 EUR. Total 480.50 EUR.",
    )  # fmt: skip
    base.update(kw)
    return ui.InvoiceView(**base)


def inv_c(role: str = "approver", **kw) -> ui.InvoiceView:
    app = role == "approver"
    base = dict(
        item_id=ID_C, state="NEEDS_PERSON", supplier="Fabrikam Demo Freight", invoice_no="INV-C-003", invoice_date="2026-10-04",
        total_minor=910_000, currency="GBP", flags=(ui.flag_view("D10"),), content_code="c1c2c3c4c5c6", version=1, may_approve=False,
        approve_refusal=D10_REFUSAL, created_at="2026-11-04T09:00:03Z", order=3,
        bank_on_file=_bank(1, BANK_ON_FILE if app else None), bank_in_text=(_bank(2, BANK_IN_TEXT if app else None),),
        source_text=TEXT_ORIGINAL if app else None,
    )  # fmt: skip
    base.update(kw)
    return ui.InvoiceView(**base)


def banners_demo() -> tuple[ui.BannerView, ...]:
    return (ui.BannerView("demo", "Only files on the made-up list reach the AI model.", "info"),)


def export_row() -> ui.ExportRowView:
    a = inv_a("APPROVED")
    return ui.ExportRowView(a.item_id, a.supplier, a.invoice_no, a.invoice_date, a.total_minor, a.currency)


def pages() -> dict[str, ui.Page]:
    ready, d06, d10 = inv_a(), inv_b(), inv_c()
    q1 = ui.QueueView(ui.default_order((ready, d06, d10)), ui.ListQuery(), banners=banners_demo())
    approved = inv_a(
        "APPROVED", may_approve=False, decision=ui.DecisionView("approved", "ap-a", "2026-11-04 10:00", "Totals checked by hand.", ())
    )
    rej_b = inv_b(state="REJECTED", may_approve=False, decision=ui.DecisionView("rejected", "ap-a", "2026-11-04 10:01", "Total wrong.", ()))
    rej_c = inv_c(state="REJECTED", decision=ui.DecisionView("rejected", "ap-a", "2026-11-04 10:02", "Bank details differ.", ()))
    q2 = ui.QueueView(ui.default_order((approved, rej_b, rej_c)), ui.ListQuery(), banners=banners_demo())
    states = tuple(
        (s, ui.STATE_LABELS[s][0], c) for s, c in (("NEEDS_PERSON", 0), ("READY", 0), ("APPROVED", 0), ("EXPORTED", 1), ("REJECTED", 2))
    )
    ov = ui.OverviewView(states, 3, 3_200_000, 100_000_000, 90_000_000, False, "2026-10-30", ())
    warn = (
        ui.BannerView("no_list", "Live AI calls stopped: the made-up list is empty.", "warn"),
        ui.BannerView("halt", "Spending halted: our spend counter stopped new AI calls. Run intake check.", "bad"),
        ui.BannerView("unavailable", "Status unavailable: scan state", "warn"),
    )
    ov2 = ui.OverviewView(states, 3, 100_000_000, 100_000_000, 90_000_000, True, "2026-10-30", warn)
    preview = ui.ExportPageView((export_row(),), kill_switch=False, may_export=True)
    result = ui.ExportPageView(
        (),
        kill_switch=False,
        results=((ID_A, "Written to the spreadsheet file."),),
        file_text="The spreadsheet file was updated.",
    )
    return {
        "01-login": ui.render_login(csrf="csrf-login-1"),
        "02-list-after-scan": ui.render_list(q1, APPROVER),
        "03-item-d06": ui.render_item(d06, APPROVER),
        "04-item-d10-approver": ui.render_item(d10, APPROVER),
        "05-item-d10-viewer": ui.render_item(inv_c("viewer"), VIEWER),
        "06-item-ready": ui.render_item(ready, APPROVER),
        "07-item-approved": ui.render_item(approved, APPROVER),
        "08-list-after-decisions": ui.render_list(q2, APPROVER),
        "09-export-preview": ui.render_export(preview, APPROVER),
        "10-export-result": ui.render_export(result, APPROVER),
        "11-overview": ui.render_overview(ov, APPROVER),
        "12-overview-banners": ui.render_overview(ov2, APPROVER),
    }
