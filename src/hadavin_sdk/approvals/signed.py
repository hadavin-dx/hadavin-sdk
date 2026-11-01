"""Signed approvals: an offline-checkable artifact, for an executor that runs in another trust zone than the approver.

Relation to the rest of `approvals`: `requests.Approvals` is the workflow (who must approve, timeouts, escalation) and
`models.ApprovalDecision` its stored result; `hmac_v0` verifies the transport signature of an inbound button click (Slack
and friends) and names the approver. This module answers a different question: "is this approval, handed to me by anyone,
exactly the one the approver signed, for this tenant and these arguments, still fresh, and not used before?". It signs
with the existing `audit.signer.Signer` kinds (Ed25519, ECDSA P-256; local, AWS, Azure, GCP, Vault) and verifies with the
PUBLIC key alone, so the verifier cannot mint. Needs the `signer` extra (cryptography).

The signed body is the schema's fields plus `key_id` (so the signing key is authenticated, and a verifier holding several
keys picks one by `key_id`: rotation without a flag day). `verify` checks, in order and with a typed reason: shape, key,
signature, tenant, args hash, age (`max_age`, boundary inclusive; an approval from the future is refused) and, if a
`consume` hook is given, single use (`consume(approval_id)` must return True exactly once; make it atomic in the caller's
store). An approval with any extra field is refused. Signatures are lowercase fixed-length hex (one encoding per signature).
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import get_args

from hadavin_sdk.audit.signer import Alg, Signer, verify_signature
from hadavin_sdk.errors import ConfigError

_KEY_LEN = {"ed25519": 32, "ecdsa-p256": 65}
_SIG = re.compile(r"[0-9a-f]{128}")  # 64 raw bytes for both algorithms


@dataclass(frozen=True)
class Schema:
    """The approval's field names. The defaults are generic; a build lists its own `fields` (for example `steps`, `requester`)."""

    fields: tuple[str, ...] = ("approval_id", "tenant_id", "args_hash", "requested_at")
    id_field: str = "approval_id"
    tenant_field: str = "tenant_id"
    hash_field: str = "args_hash"
    time_field: str = "requested_at"

    def __post_init__(self) -> None:
        named = (self.id_field, self.tenant_field, self.hash_field, self.time_field)
        if (
            not all(n in self.fields for n in named)
            or len(set(self.fields)) != len(self.fields)
            or {"key_id", "sig"} & set(self.fields)
        ):
            raise ConfigError(
                "approval schema: the id, tenant, hash and time fields are listed once; key_id and sig are reserved"
            )


DEFAULT_SCHEMA = Schema()


def _body(a: Mapping, schema: Schema) -> bytes:
    keys = (*schema.fields, "key_id")
    return json.dumps(
        {k: a[k] for k in keys}, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def issue(signer: Signer, body: Mapping, schema: Schema = DEFAULT_SCHEMA) -> dict:
    """`body` holds exactly the schema's fields; returns it plus `key_id` (signed) and `sig`."""
    if set(body) != set(schema.fields):
        raise ValueError("approval body must hold exactly " + ", ".join(schema.fields))
    signed = {**body, "key_id": signer.key_id}
    return {**signed, "sig": signer.sign(_body(signed, schema)).hex()}


@dataclass(frozen=True)
class Verdict:
    ok: bool
    # MALFORMED, UNKNOWN_KEY, BAD_SIGNATURE, TENANT_MISMATCH, HASH_MISMATCH, EXPIRED, FROM_FUTURE, ALREADY_USED
    reason: str | None = None
    approval: Mapping | None = None


class ApprovalVerifier:
    can_mint = False

    def __init__(
        self, keys: Mapping[str, tuple[Alg, bytes]], schema: Schema = DEFAULT_SCHEMA
    ) -> None:
        if not keys:
            raise ConfigError("approval verifier: at least one public key")
        for key_id, (alg, pub) in keys.items():
            if alg not in get_args(Alg):
                raise ConfigError(f"approval verifier: unknown algorithm {alg!r} for {key_id}")
            if not isinstance(pub, bytes) or len(pub) != _KEY_LEN[alg]:
                raise ConfigError(
                    f"approval verifier: {key_id}: a {alg} public key is {_KEY_LEN[alg]} bytes"
                )
        self._keys, self.schema = dict(keys), schema

    @classmethod
    def single(
        cls, public_key: bytes, alg: Alg, key_id: str, schema: Schema = DEFAULT_SCHEMA
    ) -> ApprovalVerifier:
        return cls({key_id: (alg, public_key)}, schema)

    def verify(
        self,
        approval: object,
        *,
        tenant_id: str,
        args_hash: str,
        now: datetime,
        max_age: timedelta,
        consume: Callable[[str], bool] | None = None,
    ) -> Verdict:
        s = self.schema
        if (
            not isinstance(approval, dict)
            or set(approval) != {*s.fields, "key_id", "sig"}
            or not isinstance(approval["sig"], str)
            or not _SIG.fullmatch(approval["sig"])
            or not isinstance(approval["key_id"], str)
        ):
            return Verdict(False, "MALFORMED")
        if approval["key_id"] not in self._keys:
            return Verdict(False, "UNKNOWN_KEY")
        alg, pub = self._keys[approval["key_id"]]
        try:
            body = _body(approval, s)
        except (TypeError, ValueError):
            return Verdict(False, "MALFORMED")
        if not verify_signature(pub, bytes.fromhex(approval["sig"]), body, alg):
            return Verdict(False, "BAD_SIGNATURE")
        if approval[s.tenant_field] != tenant_id:
            return Verdict(False, "TENANT_MISMATCH")
        if approval[s.hash_field] != args_hash:
            return Verdict(False, "HASH_MISMATCH")
        try:
            age = now - datetime.fromisoformat(approval[s.time_field])
        except (TypeError, ValueError):
            return Verdict(False, "MALFORMED")
        if age < timedelta(0):
            return Verdict(False, "FROM_FUTURE")
        if age > max_age:
            return Verdict(False, "EXPIRED")
        if consume is not None and not consume(approval[s.id_field]):
            return Verdict(False, "ALREADY_USED")
        return Verdict(True, None, approval)
