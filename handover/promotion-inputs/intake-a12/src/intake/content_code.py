"""Content code and row id (spec 8). The content code binds an approval to the exact values a person saw: sha256 of the canonical JSON of a
12-key record. It covers the UNGUARDED values (the CSV cell guard changes only the exported text)."""

from __future__ import annotations

import hashlib

from . import flags as flagtable
from . import rules, tools
from .textfold import fold_text
from .workqueue import Item

SCHEMA_VERSION = 1
SEP = "\u001f"


def _line(x: object) -> list:
    keys = ("description", "qty", "unit_cost_minor", "amount_minor")
    return [x.get(k) for k in keys] if isinstance(x, dict) else [None] * 4


def _adjustment(x: object) -> list:
    return [x.get("label"), x.get("amount_minor")] if isinstance(x, dict) else [None, None]


def _flags(item: Item) -> list[str]:
    """Sorted codes. A stored code the flag table no longer knows is kept as text (so the item still has a code and can be rejected; it can never be
    approved: ``decisions.approve_refusal`` refuses an unknown flag)."""
    try:
        return flagtable.sorted_codes(item.flags)
    except flagtable.UnknownFlag:
        return sorted({str(c) for c in item.flags})


def record(item: Item) -> dict:
    """The 12-key record. An item with no fields uses null scalars and empty lists (so every item has a code; none of them can be approved). It
    never raises on a malformed stored record (missing keys become null), so a person can still reject such an item."""
    f = item.fields if isinstance(item.fields, dict) else None
    scalar_keys = ("invoice_no", "supplier_name", "po_ref", "currency", "invoice_date", "total_minor")
    if f is None:
        scalars = dict.fromkeys(scalar_keys)
        lines: list = []
        adjustments: list = []
    else:
        scalars = {k: f.get(k) for k in scalar_keys}
        lines = [_line(x) for x in f["lines"]] if isinstance(f.get("lines"), list) else []
        adjustments = [_adjustment(x) for x in f["adjustments"]] if isinstance(f.get("adjustments"), list) else []
    return {
        "schema_version": SCHEMA_VERSION,
        "tenant_id": item.tenant_id,
        "source_sha256": item.source_sha256,
        **scalars,
        "lines": lines,
        "adjustments": adjustments,
        "flags": _flags(item),
    }


def content_code(item: Item) -> str:
    return hashlib.sha256(tools.canonical_json(record(item)).encode()).hexdigest()


def row_id(tenant_id: str, supplier_name: str, invoice_no: str, policy: rules.Policy) -> str:
    """sha256 hex of tenant_id, supplier_key and invoice_key joined by U+001F. Both keys go through the studio's look-alike fold
    (``textfold.fold_text``: NFKC, confusables such as Cyrillic or Greek letters, invisible characters, width), so a look-alike supplier or invoice
    number gives the SAME row id and an export of the twin is refused as ``row_id_conflict``. supplier_key = fold, casefold, spaces collapsed;
    invoice_key = ``rules.norm_invoice_no`` of the fold (None if it is still not ASCII: then the casefolded, whitespace-collapsed fold).
    ``policy`` is loaded once by the caller (``rules.load_policy()``)."""
    supplier_key = fold_text(supplier_name, casefold=True, collapse_ws=True)
    folded_invoice = fold_text(invoice_no)
    invoice_key = rules.norm_invoice_no(folded_invoice, policy)
    if invoice_key is None:
        invoice_key = fold_text(invoice_no, casefold=True, collapse_ws=True)
    return hashlib.sha256(SEP.join((tenant_id, supplier_key, invoice_key)).encode("utf-8")).hexdigest()


def item_row_id(item: Item, policy: rules.Policy) -> str | None:
    """None for an item with no usable record (no fields, or a supplier or invoice number that is not text): such an item has no row id and can never
    be exported. Never raises on a malformed stored record."""
    f = item.fields
    if not isinstance(f, dict) or not isinstance(f.get("supplier_name"), str) or not isinstance(f.get("invoice_no"), str):
        return None
    return row_id(item.tenant_id, f["supplier_name"], f["invoice_no"], policy)
