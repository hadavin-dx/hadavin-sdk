"""Builders for the write-path tests: a mutable server clock, a store, an approval service and ready-made requests with matching approvals."""

from refunds.adapters.ports import business_key
from refunds.approval import ApprovalIssuer
from refunds.store import Store
from refunds.writegate import WriteGate, hash_request

START = "2026-10-20T12:00:00Z"
DIRECTORY = {
    "lead@desk.example": ["support_lead"],
    "finance@desk.example": ["finance_approver"],
    "both@desk.example": ["support_lead", "finance_approver"],
    "pat@example.com": ["support_lead"],  # an approver who is also the customer (APPROVER_IS_BENEFICIARY)
    "staff@desk.example": ["janitor"],
    "agent-run": ["support_lead"],  # the requester id is also a directory member (REQUESTER_IS_APPROVER)
}
ONE = [("lead@desk.example", "support_lead")]
TWO = [("lead@desk.example", "support_lead"), ("finance@desk.example", "finance_approver")]


class Clock:
    def __init__(self, now: str = START) -> None:
        self.now = now

    def __call__(self) -> str:
        return self.now


def ex_safe(wg, *args, **kw):
    """For the HOSTILE-INPUT tests only, where 'execute never raises' is the asserted property: an escaping exception becomes an outcome the test asserts on."""
    try:
        return wg.execute(*args, **kw)
    except Exception as e:  # noqa: BLE001
        return {"outcome": "exception", "code": type(e).__name__}


def ex(wg, *args, **kw):
    """Plain call. A crash inside execute propagates as an error (crash-only in the mutation report), it is never dressed up as an assertion."""
    return wg.execute(*args, **kw)


def make(path: str = ":memory:", key: bytes = b"k" * 32, clock: Clock | None = None):
    clock = clock or Clock()
    store = Store(path)
    svc = ApprovalIssuer(DIRECTORY, key=key)
    return store, svc, clock, WriteGate(store, svc.verifier(), clock)


def request(**kw) -> dict:
    base = {
        "tenant_id": "t1", "action": "refund", "order_id": "ord-1", "line_ids": ["l1"], "amount_minor": "2500", "currency": "USD",
        "customer_id": "c1", "cluster": ["c1"], "requested_at": START, "tier": "human", "requester": "agent-run", "beneficiary": "pat@example.com",
        "basis": {"captured_minor": "6000", "prior_order_minor": "0", "prior_customer_30d_minor": "0", "prior_refunded_minor": "0", "tier_floor": "", "request": "2500"},
    }  # fmt: skip
    out = {**base, **kw}
    # convenience: the signed basis["request"] is the amount; a test that changes only the amount (or passes the default basis for another amount) keeps
    # them equal. A test that wants a MISMATCH sets basis["request"] to something other than the default "2500" (or changes the amount after signing).
    if isinstance(out["basis"], dict) and out["basis"].get("request") == "2500" and isinstance(out["amount_minor"], str):
        out["basis"] = {**out["basis"], "request": out["amount_minor"]}
    return out


def key_of(req: dict) -> str:
    return business_key(req["tenant_id"], req["action"], req["order_id"], req["line_ids"], req["amount_minor"], req["currency"])


def sign(svc: ApprovalIssuer, req: dict, people=ONE, identity: str = "approver_human") -> dict:
    return svc.issue(
        identity, tenant_id=req["tenant_id"], args_hash=hash_request(req, key_of(req)), tier=req["tier"], requested_at=req["requested_at"],
        requester=req["requester"], people=people,
    )  # fmt: skip


def burst(n: int, tenant: str = "t1", amount: int = 1000) -> list[dict]:
    """n different small requests (distinct orders), all well inside every cap."""
    return [
        request(tenant_id=tenant, order_id=f"ord-{i + 1}", line_ids=[f"l{i + 1}"], amount_minor=str(amount), customer_id=f"c{i + 1}", cluster=[f"c{i + 1}"],
                basis={"captured_minor": "6000", "prior_order_minor": "0", "prior_customer_30d_minor": "0", "prior_refunded_minor": "0", "tier_floor": "", "request": str(amount)})
        for i in range(n)
    ]  # fmt: skip


def raw_reserve(store, tenant, key, customer_id, order_id, amount, currency, at, sender="") -> None:
    """Insert a reservation row directly, BYPASSING the flooding caps in Store.reserve: for the tests that need a day-cap-sized reservation to exist
    (state left by another instance, or by a build with other caps). The capped path is tested through Store.reserve / Desk.propose."""
    with store.transaction() as db:
        db.execute(
            "INSERT OR IGNORE INTO reservations(tenant,key,customer_id,order_id,amount_minor,currency,created_at,sender) VALUES(?,?,?,?,?,?,?,?)",
            (tenant, key, customer_id, order_id, amount, currency, at, sender),
        )


def consume(store, tenant, approval_id, key, requester="agent-run", executed_by="executor") -> None:
    store.consume_approval(
        tenant,
        approval_id,
        key,
        requester,
        [{"person": "lead@desk.example", "role": "support_lead"}],
        "human",
        executed_by,
        START,
    )


def reserve(store, tenant, key, customer_id, order_id, amount, currency, at, sender="s@x.example"):
    """The real, capped reservation with the cluster defaulting to the customer alone."""
    return store.reserve(tenant, key, customer_id, order_id, amount, currency, at, cluster=[customer_id], sender=sender)
