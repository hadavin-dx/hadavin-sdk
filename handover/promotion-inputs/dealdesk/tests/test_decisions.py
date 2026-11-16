"""B1/M11/M12: a signed decision binds what the approver saw (core approval-signature format, Ed25519, private key outside the engine); ids carry 128 bits."""

import dataclasses
from datetime import UTC, datetime, timedelta

import pytest

from dealdesk import canon, tools
from dealdesk.core_copy.approvals_signed import ApprovalVerifier, issue
from dealdesk.desk import APPROVAL_SCHEMA
from dealdesk.signing import LocalSigner

SIGNER = LocalSigner()
FIELDS = {
    "approval_id": "apr-" + "0" * 32, "tenant_id": "t-a", "requested_at": "2026-11-09T10:00:00+00:00", "deal_id": "deal-0001", "terms_hash": "a" * 64,
    "quote_hash": "c" * 64, "snapshot_hash": "b" * 64, "lane": "commercial", "min_role": "regional_vp", "epoch": 1, "approver_id": "p-rvp-01",
    "decision": "approve", "ts": "2026-11-09T12:00:00Z",
}  # fmt: skip
NOW = datetime(2026, 11, 9, 12, tzinfo=UTC)


def signed(**over):
    f = {**FIELDS, **over}
    f["args_hash"] = canon.decision_args_hash(f)
    return issue(SIGNER, {k: f[k] for k in canon.APPROVAL_FIELDS}, APPROVAL_SCHEMA)


def verify(a):
    v = ApprovalVerifier.single(SIGNER.public_key(), "ed25519", SIGNER.key_id, APPROVAL_SCHEMA)
    return v.verify(a, tenant_id="t-a", args_hash=canon.decision_args_hash(a) if isinstance(a, dict) and "decision" in a else "x", now=NOW,
                    max_age=timedelta(days=1)).ok  # fmt: skip


def test_signature_is_128_hex_and_verifies_with_the_public_key_alone():
    a = signed()
    assert len(a["sig"]) == 128 and a["sig"] == a["sig"].lower() and int(a["sig"], 16) >= 0
    assert verify(a)
    assert ApprovalVerifier.can_mint is False


@pytest.mark.parametrize(
    "field", [f for f in canon.APPROVAL_FIELDS if f not in ("approval_id", "tenant_id", "args_hash", "requested_at", "ts")]
)
def test_changing_any_bound_field_invalidates_the_signature(field):
    a = signed()
    other = {"epoch": 2, "decision": "reject", "lane": "legal"}.get(field) or a[field] + "x"
    assert not verify({**a, field: other})


@pytest.mark.parametrize("field", ["approval_id", "requested_at", "ts", "tenant_id"])
def test_other_signed_fields_are_covered_too(field):
    a = signed()
    assert not verify({**a, field: a[field] + "x"})


def test_missing_wrong_length_uppercase_and_foreign_key_all_fail():
    a = signed()
    for bad in (None, "", a["sig"][:-1], a["sig"].upper(), a["sig"] + "0"):
        assert verify({**a, "sig": bad}) is False
    assert verify({**a, "key_id": "ed25519:other"}) is False
    other = LocalSigner()
    forged = issue(other, {k: a[k] for k in canon.APPROVAL_FIELDS}, APPROVAL_SCHEMA)
    assert verify({**forged, "key_id": a["key_id"]}) is False  # another key's signature under this key id


def test_extra_fields_are_refused():
    assert verify({**signed(), "extra": 1}) is False


def test_signed_decision_dataclass_carries_every_signed_field():
    names = {f.name for f in dataclasses.fields(tools.SignedDecision)}
    assert set(canon.APPROVAL_FIELDS) | {"key_id", "sig"} == names


def test_approval_ids_carry_128_bits_of_entropy():
    i = canon.mint_id("apr", bytes(range(16)))
    assert i == "apr-" + bytes(range(16)).hex() and len(i) == 4 + 32
    with pytest.raises(ValueError):
        canon.mint_id("apr", b"short")
