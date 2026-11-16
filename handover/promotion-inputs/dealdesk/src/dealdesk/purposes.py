"""Purpose limitation (blast radius (1); R-DEALDESK-092). The job: read a sales rep's discount/terms request, find the facts the policy needs, apply the
written approval matrix in code, route approvals, and produce a DRAFT quote for a person. Client data is used for nothing else: not training,
analytics, benchmarking, marketing, other clients or a model shared across clients. Every field that reaches the model is listed with its purpose; a field NOT listed
never leaves the port (deny-all start). Deliberately excluded: cost per seat and margin floor (HZ-9), customer tier and ARR (the code uses them, the model
need not), CRM notes and thread (untrusted, never an input), owner, other accounts, approver identities and keys."""

from __future__ import annotations

PURPOSE: dict[str, str] = {
    "request.text": "extract the stated discount and terms (fenced untrusted text; R-DEALDESK-005 re-derives every figure from it in code)",
    "request.attachment_text": "screened for instruction-like text only; NEVER a source of figures (R-DEALDESK-050)",
    "deal.deal_id": "name the deal in a proposal (trusted intake metadata)",
    "deal.account_name": "whole-name match of the account in the message (R-DEALDESK-006)",
    "deal.plan": "cross-check the plan the rep mentions (R-DEALDESK-002)",
    "deal.currency": "currency check (R-DEALDESK-004)",
    "deal.seats": "cross-check the seat count the rep mentions (R-DEALDESK-002)",
    "price_book.standard_terms": "fill unstated terms with the standard ones",
}


CODE_PURPOSE: dict[str, str] = {  # fields CODE reads from the ports to apply the policy; they never reach the model
    "deal.account_id": "pool quotes of one account (R-DEALDESK-080); exemption lookup",
    "deal.owner_rep": "scope: the requester must own the deal (R-DEALDESK-003)",
    "deal.customer_tier": "tier cap (R-DEALDESK-011)",
    "deal.request_type": "renewal downsell and CRM consistency (R-DEALDESK-017, 007)",
    "deal.arr_minor": "renewal downsell and CRM consistency (R-DEALDESK-017, 007)",
    "deal.price_book_version": "quote and snapshot binding (R-DEALDESK-085)",
    "deal.tax_region": "tax rate (R-DEALDESK-082)",
    "pricebook.plans": "list price per seat and cost per seat (cost never leaves the code: HZ-9)",
    "pricebook.floor_bps": "margin floor (R-DEALDESK-012; never shown to a rep)",
    "pricebook.standard_terms": "fill unstated terms",
    "directory.person": "role, employee id and active flag of one person (R-DEALDESK-022, 087)",
    "directory.role_members": "route a step to people with the role",
    "billing.exemption": "tax exemption certificate valid-until date (R-DEALDESK-083)",
}
DEAL_FIELDS = (
    "deal_id",
    "account_id",
    "account_name",
    "owner_rep",
    "currency",
    "customer_tier",
    "request_type",
    "plan",
    "seats",
    "arr_minor",
    "price_book_version",
    "tax_region",
)  # fmt: skip  (CRM notes and anything else never leave the port)


def model_view(request: dict, deal: dict, book: dict) -> dict:
    """The ONLY projection of port data that may reach the model, prompt logs or any output."""
    t = {
        "request.text": request.get("text", ""),
        "request.attachment_text": "\n".join(a.get("text", "") for a in request.get("attachments", [])),
        "deal.deal_id": deal["deal_id"],
        "deal.account_name": deal["account_name"],
        "deal.plan": deal["plan"],
        "deal.currency": deal["currency"],
        "deal.seats": deal["seats"],
        "price_book.standard_terms": dict(book["standard_terms"]),
    }
    if not set(t) <= set(PURPOSE):
        raise ValueError(f"field outside any stated purpose: {sorted(set(t) - set(PURPOSE))}")
    return t
