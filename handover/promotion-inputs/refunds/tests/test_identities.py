"""Least-privilege identities (owner HARD RULE; review M7): deny-all start, exact allow-lists, negative tests per identity."""

import pytest

from refunds import identities as idn
from refunds import tools

MONEY = ("execute_approved", "payments.refund", "payments.credit", "orders.cancel", "orders.reship")
MUST_DENY = {
    "agent_runtime": [
        "reserve",
        "release",
        "approve",
        "approvals.void",
        "approvals.convert_executed",
        "killswitch.operate",
        "migrate.schema",
        "ci.deploy",
        "breakglass.use",
        "audit.append",
        "audit.read",
        "helpdesk.create_draft",
        "helpdesk.add_note",
        "approvals.create_pending",
        "lookup_by_key",
        "secrets.read",
        *MONEY,
    ],
    "harness": ["approve", "reserve", "audit.append", "read.payments", "read.orders", "approvals.void", *MONEY],
    "gate_service": ["approve", "audit.append", "helpdesk.create_draft", "release", "approvals.void", *MONEY],
    "approval_verifier": ["approve", "reserve", "audit.append", "helpdesk.add_note", "approvals.void", *MONEY],
    "approver_human": [
        "reserve",
        "audit.append",
        "read.payments",
        "approvals.create_pending",
        "approvals.void",
        "killswitch.operate",
        *MONEY,
    ],
    "executor": [
        "approve",
        "audit.append",
        "reserve",
        "helpdesk.create_draft",
        "approvals.create_pending",
        "secrets.read",
        "killswitch.operate",
        "migrate.schema",
    ],
    "sweeper": ["approve", "reserve", "read.orders", "audit.append", "approvals.void", *MONEY],
    "reconciler": ["approve", "reserve", "audit.append", "approvals.void", *MONEY],
    "audit_writer": ["audit.read", "approve", "reserve", "secrets.read", *MONEY],
    "audit_reader": ["audit.append", "approve", "reserve", *MONEY],
    "kill_switch_operator": [
        "approve",
        "reserve",
        "read.orders",
        "read.payments",
        "audit.append",
        "approvals.void",
        "migrate.schema",
        *MONEY,
    ],
    "migrations": ["approve", "reserve", "read.orders", "audit.append", "killswitch.operate", "schema.change", *MONEY],
    "ci_deploy": ["approve", "reserve", "read.orders", "audit.append", "migrate.schema", "credential.change", *MONEY],
    "breakglass": [a for a in idn.ACTIONS],
}


@pytest.mark.parametrize("identity", sorted(idn.IDENTITIES))
def test_each_identity_is_denied_what_it_must_not_do(identity):
    for action in MUST_DENY[identity]:
        assert action in idn.ACTIONS
        assert not idn.authorize(identity, action), (identity, action)


def test_every_identity_has_a_negative_test_entry():
    assert set(MUST_DENY) == set(idn.IDENTITIES)


def test_deny_all_start_unknown_identity_or_action_is_denied():
    assert not idn.authorize("nobody", "read.orders") and not idn.authorize("agent_runtime", "does.not.exist")
    for identity, entry in idn.IDENTITIES.items():
        assert entry["allow"] <= set(idn.ACTIONS), identity
        assert entry["policy"], f"{identity} needs a policy text"
        assert set(entry["why"]) or not entry["allow"], f"{identity} needs a per-action justification"
    assert not idn.IDENTITIES["breakglass"]["allow"], "breakglass is dormant: no standing action"


def test_no_identity_both_approves_and_moves_money_and_no_wildcards():
    for identity, entry in idn.IDENTITIES.items():
        assert not ({"approve"} & entry["allow"] and set(MONEY) & entry["allow"]), identity
        assert not any("*" in a for a in entry["allow"])
    assert [i for i, e in idn.IDENTITIES.items() if "approve" in e["allow"]] == ["approver_human"]
    assert [i for i, e in idn.IDENTITIES.items() if "audit.append" in e["allow"]] == ["audit_writer"]
    assert "audit.append" not in idn.IDENTITIES["executor"]["allow"]


def test_execute_approved_is_not_model_callable():
    assert "execute_approved" not in idn.model_callable_tools()
    assert not idn.authorize("agent_runtime", "execute_approved")
    names = {t["name"] for t in tools.REGISTRY}
    assert names == {
        "get_ticket",
        "get_order",
        "find_orders",
        "get_policy",
        "check_eligibility",
        "draft_reply",
        "hand_back",
        "propose_refund",
        "propose_cancel_order",
        "propose_reship",
        "propose_goodwill_credit",
    }
    assert all(not n.startswith(("execute", "issue", "approve")) for n in names)
    assert idn.MODEL_FACING == {"agent_runtime"}


def test_every_action_is_granted_to_someone_and_money_moves_only_for_the_executor():
    granted = set().union(*(e["allow"] for e in idn.IDENTITIES.values()))
    assert granted == set(idn.ACTIONS) - {
        "secrets.read",
        "schema.change",
        "permission.change",
        "credential.change",
        "bulk_delete",
        "breakglass.use",
    }
    for money in ("payments.refund", "payments.credit", "orders.cancel", "orders.reship"):
        assert [i for i, e in idn.IDENTITIES.items() if money in e["allow"]] == ["executor"], money
    assert [i for i, e in idn.IDENTITIES.items() if "approvals.void" in e["allow"]] == ["executor"], (
        "voiding at execute has an owner"
    )
    assert [i for i, e in idn.IDENTITIES.items() if "killswitch.operate" in e["allow"]] == ["kill_switch_operator"]


def test_the_approver_can_read_what_it_signs_and_nothing_more():
    assert idn.authorize("approver_human", "approvals.read_pending") and not idn.authorize("approver_human", "approvals.read")
