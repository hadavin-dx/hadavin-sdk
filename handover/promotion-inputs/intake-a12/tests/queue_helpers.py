"""Shared builders for the queue, decision, content-code and trigger tests (the page cases of WP6 reuse them)."""

from __future__ import annotations

import functools
import hashlib
import json
import re

import pytest

from intake import decisions, queue_schema, workqueue
from intake.content_code import content_code

GOOD_FIELDS = {
    "invoice_no": "INV-1001",
    "supplier_name": "Acme Ltd",
    "po_ref": None,
    "currency": "USD",
    "invoice_date": "2026-10-01",
    "lines": [
        {"description": "Widget A", "qty": 2, "unit_cost_minor": 1250, "amount_minor": 2500},
        {"description": "Shipping line", "qty": 1, "unit_cost_minor": 500, "amount_minor": 500},
    ],
    "adjustments": [{"label": "VAT", "amount_minor": 300}],
    "total_minor": 3300,
}
REASON = "checked against the purchase order"


def sha(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def new_item(s, name="inv", fields=GOOD_FIELDS, flags=(), cost=0):
    """An item that went RECEIVED -> READY (no flags) or NEEDS_PERSON (flags), through the public API."""
    it = workqueue.insert_received(s, f"{name}.txt", sha(name), "invoice text", s.tenant_id, name)
    assert isinstance(it, workqueue.Item)
    state = "NEEDS_PERSON" if flags else "READY"
    return workqueue.set_result(
        s,
        it.uid,
        state,
        fields=fields,
        flags=flags,
        failing_fields=[],
        model_id="model-x",
        tier="read",
        prompt_sha256="p" * 64,
        cost_micro=cost,
    )


def approve(s, item, reason=None, approver="ap-a"):
    return decisions.decide(s, item.id, "approve", approver, reason, content_code(item), item.version)


def reject(s, item, reason=REASON, approver="ap-a"):
    return decisions.decide(s, item.id, "reject", approver, reason, content_code(item), item.version)


def raw_insert(conn, iid, state="RECEIVED", fields=None, flags="[]", sha_=None, tenant="demo-intake"):
    """A hand-written INSERT (the triggers are the second line behind the API, so tests also go around it)."""
    conn.execute(
        "INSERT INTO items (id, source_name, source_sha256, tenant_id, state, fields_json, flags_json, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, '2026-11-03T00:00:00Z')",
        (iid, iid + ".txt", sha_ or sha(iid), tenant, state, None if fields is None else json.dumps(fields), flags),
    )
    return conn.execute("SELECT uid FROM items WHERE id = ?", (iid,)).fetchone()["uid"]


def raw_decision(conn, uid, decision="approve", code="c" * 64):
    conn.execute(
        "INSERT INTO decisions (item_uid, decision, approver, reason, content_code, at) VALUES (?, ?, 'ap-a', NULL, ?, '2026-11-03T00:00:00Z')",
        (uid, decision, code),
    )


def raw_export(conn, uid, row_id="r" * 64, code="c" * 64):
    conn.execute(
        "INSERT INTO exports (row_id, item_uid, content_code, row_json, at) VALUES (?, ?, ?, '{}', '2026-11-03T00:00:00Z')",
        (row_id, uid, code),
    )


def drop_triggers(conn, *names):
    """Drop the named guard triggers on THIS connection (set-up of a forged state or a stub test). No names = all of them."""
    have = [r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'")]
    for n in names or have:
        conn.execute(f"DROP TRIGGER {n}")


def only_triggers(conn, *names):
    """Leave exactly the named guard triggers on this connection (recreated from ``queue_schema.trigger_sql``)."""
    from intake import queue_schema

    drop_triggers(conn)
    for n in names:
        conn.execute(queue_schema.trigger_sql()[n])


def assertive(fn):
    """A test that fails by an unexpected EXCEPTION (the code under test raised something the test did not expect) is reported as a plain test
    failure with a readable message. Class-level reason: the mutation judge counts only assertion failures as kills, and a mutant that makes the code
    raise a different exception is exactly as detected as one that makes an assert fail."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (AssertionError, pytest.fail.Exception, pytest.skip.Exception):
            raise
        except Exception as e:  # noqa: BLE001
            pytest.fail(f"unexpected {type(e).__name__}: {str(e)[:160]}")

    return wrapper


def assertive_all(namespace: dict) -> None:
    """Wrap every ``test_*`` function of a test module (call as ``assertive_all(globals())`` at the end of the module)."""
    for name, obj in list(namespace.items()):
        if name.startswith("test_") and callable(obj) and getattr(obj, "__module__", None) == namespace.get("__name__"):
            namespace[name] = assertive(obj)


def disabled_sql(name: str) -> str:
    """The trigger with a condition that never holds (``WHEN 0``): present in the schema, never fires. The 'drop trigger' mutants use the same change."""
    sql = queue_schema.trigger_sql()[name]
    if " WHEN " in sql:
        return re.sub(r" WHEN .* BEGIN ", " WHEN 0 BEGIN ", sql, count=1)
    return sql.replace(" BEGIN ", " WHEN 0 BEGIN ", 1)


def only_disabled_trigger(conn, name: str) -> None:
    """Leave exactly one trigger on this connection: the named one, disabled."""
    drop_triggers(conn)
    conn.execute(disabled_sql(name))
