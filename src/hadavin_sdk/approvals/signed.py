"""Signed approvals on the existing `audit.signer.Signer` kind (Ed25519 / ECDSA P-256; local, AWS, Azure, GCP, Vault).

The signer holds the private key; the verifier is built from the PUBLIC key alone and so cannot mint (`can_mint` is False by construction,
there is no symmetric secret). The body is canonical JSON of the approval fields; an approval with any extra field is refused. Needs the
`signer` extra (cryptography), as `audit.signer` does.
"""

from __future__ import annotations

import json

from hadavin_sdk.audit.signer import Alg, Signer, verify_signature

FIELDS = ("approval_id", "tenant_id", "args_hash", "tier", "requested_at", "requester", "steps")


def _body(a: dict) -> bytes:
    return json.dumps(
        {k: a[k] for k in FIELDS}, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def issue(signer: Signer, body: dict) -> dict:
    """`body` holds exactly FIELDS; returns it plus `sig` (hex) and `key_id`."""
    if set(body) != set(FIELDS):
        raise ValueError("approval body must hold exactly " + ", ".join(FIELDS))
    return {**body, "sig": signer.sign(_body(body)).hex(), "key_id": signer.key_id}


class ApprovalVerifier:
    can_mint = False

    def __init__(self, public_key: bytes, alg: Alg = "ed25519") -> None:
        self._pub, self._alg = public_key, alg

    def verify(self, approval: object) -> bool:
        if not isinstance(approval, dict) or set(approval) != {*FIELDS, "sig", "key_id"}:
            return False
        try:
            sig = bytes.fromhex(approval["sig"])
            return verify_signature(self._pub, sig, _body(approval), self._alg)
        except (ValueError, TypeError, KeyError):
            return False
