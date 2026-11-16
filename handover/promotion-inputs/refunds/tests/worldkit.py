"""Tiny hand-built worlds for probes and property tests (independent of the generator and of the gold)."""

import hashlib
from datetime import timedelta

import reference as ref


def ts(days=0, seconds=0):
    return (ref.NOW - timedelta(days=days, seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def customer(
    cid, email, fp=None, fraud=False, verified=True, line1="1 Main Street", pc="10001", cc="US", cur="USD", name="Pat Lee"
):
    return {
        "customer_id": cid,
        "email": email,
        "name": name,
        "currency": cur,
        "fraud_flag": fraud,
        "email_verified": verified,
        "instrument_fp": fp or ("fp-" + hashlib.sha256(cid.encode()).hexdigest()[:16]),
        "ship_to": {"name": name, "line1": line1, "postcode": pc, "country": cc},
    }


def line(lid, unit=2500, qty=1, refunded=0, comp="none"):
    return {
        "line_id": lid,
        "item": "tote",
        "qty": qty,
        "unit_minor": str(unit),
        "refunded_minor": str(refunded),
        "compensation": comp,
    }


def order(
    oid,
    cust,
    lines,
    status="delivered",
    cur="USD",
    ship=500,
    delivered_days=5,
    late_days=None,
    refunds=(),
    other=(),
    goodwill=0,
    fraud=False,
    dispute="none",
):
    sub = sum(int(x["unit_minor"]) * x["qty"] for x in lines)
    refunded = sum(int(x["refunded_minor"]) for x in lines)
    if refunded and not refunds:
        refunds = [
            {
                "refund_id": "rf-auto",
                "amount_minor": str(refunded),
                "ts": ts(3),
                "line_ids": [x["line_id"] for x in lines if int(x["refunded_minor"]) > 0],
            }
        ]
    o = {
        "order_id": oid,
        "customer_id": cust["customer_id"],
        "currency": cur,
        "payments_currency": cur,
        "status": status,
        "lines": lines,
        "shipping_minor": str(ship),
        "shipping_refunded_minor": "0",
        "captured_minor": str(sub + ship),
        "refunded_minor": str(refunded),
        "refunds": list(refunds),
        "other_actions": list(other),
        "goodwill_minor": str(goodwill),
        "fraud_flag": fraud,
        "dispute_status": dispute,
        "ship_address_id": "adr",
        "ship_address_changed_at": None,
        "ship_to": cust["ship_to"],
        "notes": [],
        "shipped_at": ts(delivered_days + 3),
        "delivered_at": ts(delivered_days) if status == "delivered" else None,
        "carrier_eta": None,
        "tracking": "T",
    }
    if late_days is not None:
        o["carrier_eta"] = ts((delivered_days if status == "delivered" else 0) + late_days)
    return o


def world(customers, orders):
    return {"customers": customers, "orders": orders}


def case(email, hint=None, tags=(), images=1, verified=True, port_state=None, tenant=None):
    c = {
        "ticket": {
            "sender_verified": verified,
            "verified_sender_email": email if verified else None,
            "tags": list(tags),
            "attachments": [{"ref": "a", "type": "image", "filename": "p.jpg"}] * images,
        },
        "order_hint": hint,
    }
    if port_state:
        c["port_state"] = port_state
    if tenant:
        c["tenant_id"] = tenant
    return c


def refund(oid, lines, amount, reason="damaged", cur="USD", basis="line_total"):
    return {
        "tool": "propose_refund",
        "args": {
            "order_id": oid,
            "reason": reason,
            "basis": basis,
            "line_ids": lines,
            "amount": {"amount_minor": str(amount), "currency": cur},
        },
    }


def reship(oid, lines, value, cur="USD"):
    return {
        "tool": "propose_reship",
        "args": {
            "order_id": oid,
            "reason": "not_delivered",
            "line_ids": lines,
            "value": {"amount_minor": str(value), "currency": cur},
        },
    }


def goodwill(oid, amount=1500, cur="USD"):
    return {
        "tool": "propose_goodwill_credit",
        "args": {"order_id": oid, "reason": "late_delivery", "amount": {"amount_minor": str(amount), "currency": cur}},
    }
