"""Purpose limitation (purpose-and-blast-radius rule (1)): client data is read only for the stated job, only the fields that job needs, and used for nothing else.

The job: decide whether a refund / cancel / reship / goodwill request is eligible, compute the amount, and draft a template reply. Every field
that reaches the model is listed below with its purpose. A field NOT in this table never leaves the port (deny-all start). Not used for training,
analytics, benchmarking, marketing, other clients or a model shared across clients (that purpose is not in the table and no identity is granted it).
Deliberately excluded: customer name and From display (the greeting is a harness slot from the Orders record), order notes, attachment file
names, customer created_at, internal memos, ship-to name and address text (the reship uses the address ON FILE by id, the model never sees it).
"""

from __future__ import annotations

PURPOSE: dict[str, str] = {
    "ticket.subject": "understand the request (fenced untrusted text)",
    "ticket.body": "understand the request (fenced untrusted text)",
    "ticket.quoted_thread": "understand the request (fenced untrusted text)",
    "ticket.attachment_ocr": "understand the request (fenced untrusted text)",
    "ticket.image_count": "eligibility: damaged / wrong_item need >= 1 image reported by the helpdesk (R-REF-014)",
    "ticket.tags": "dispute hold (R-REF-008)",
    "order.order_id": "name the order in a proposal",
    "order.status": "eligibility (R-REF-009/014/015)",
    "order.currency": "currency check (R-REF-010)",
    "order.lines": "ledger and amount (line id, item title, qty, unit, refunded, compensation) (R-REF-002/022)",
    "order.shipping_minor": "whole-order basis amount",
    "order.captured_minor": "whole-order basis amount",
    "order.refunded_minor": "ledger (R-REF-002)",
    "order.delivered_at": "return window (R-REF-014)",
    "order.carrier_eta": "lateness (R-REF-015)",
    "order.tracking": "template slot for status replies",
    "order.goodwill_minor": "one goodwill per order (R-REF-023)",
}


def model_view(ticket: dict, order: dict | None) -> dict:
    """The ONLY projection of port data that may reach the model, the logs of prompts, or any output. Anything else is dropped here."""
    t = {
        "ticket.subject": ticket.get("subject", ""),
        "ticket.body": ticket.get("body", ""),
        "ticket.quoted_thread": ticket.get("quoted_thread", ""),
        "ticket.attachment_ocr": ticket.get("attachment_ocr", ""),
        "ticket.image_count": sum(1 for a in ticket.get("attachments", []) if a.get("type") == "image"),
        "ticket.tags": list(ticket.get("tags", [])),
    }
    if order is not None:
        t.update(
            {
                "order.order_id": order["order_id"],
                "order.status": order["status"],
                "order.currency": order["currency"],
                "order.lines": [
                    {k: ln[k] for k in ("line_id", "item", "qty", "unit_minor", "refunded_minor", "compensation")}
                    for ln in order["lines"]
                ],
                "order.shipping_minor": order["shipping_minor"],
                "order.captured_minor": order["captured_minor"],
                "order.refunded_minor": order["refunded_minor"],
                "order.delivered_at": order["delivered_at"],
                "order.carrier_eta": order["carrier_eta"],
                "order.tracking": order["tracking"],
                "order.goodwill_minor": order["goodwill_minor"],
            }
        )
    if not set(t) <= set(PURPOSE):
        raise PermissionError(f"field outside any stated purpose: {sorted(set(t) - set(PURPOSE))}")
    return t
