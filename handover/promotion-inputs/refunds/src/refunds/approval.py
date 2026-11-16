"""One-use signed approvals (R-REF-004, R-REF-016; design reviews 6 and 7).

An approval is a small dict: approval_id, tenant_id, args_hash, tier, requested_at, requester, steps[{person, role}], mac, and NOTHING else (an extra
field is NO_APPROVAL). `mac` is the signature of the `signers` kind over every other field (the field name predates the asymmetric kind).

WHO CAN MINT (stated plainly, and tested as stated): the signature scheme is a `signer` kind (signers.py). With the neutral default `hmac` the scheme is
SYMMETRIC: the verifier the write path holds has the same key, so `verifier.can_mint` is True and the executor side COULD mint; the desk process builds
both objects. That default is a LABEL check, not authentication: `issue(identity="approver_human", ...)` trusts a caller-asserted string, and nothing
proves a person pressed a button. With the `ed25519` kind (optional extra) the verifier holds only the public key, `can_mint` is False, and a test walks
everything reachable from the gate for the private key. A client build uses ed25519 or a KMS/passkey kind; the checks below do not change.

FOUR-EYES IS A SHAPE: one `issue` call names both people, in order, and the MAC covers the list. The verifier checks ordered roles and distinct people.
It does NOT check two independent signatures; per-person signatures are stage 2.

`verify` returns None when the approval is good and otherwise ONE typed code, in this order: NO_APPROVAL (not a well-formed approval, or anything that
makes the MAC or the hash unusable) -> APPROVAL_INVALID (MAC does not verify) -> ARGS_HASH_MISMATCH (not the action being executed: tenant, action,
order, lines, amount, currency, key, customer, beneficiary, cluster, requester, tier, basis and request time are all inside the hash, and the signed tier
and request time must equal the request's) -> EXPIRED (older than the TTL, or from the future) -> ROLE_NOT_IN_MATRIX (tier unknown, lower than the
cumulative basis or risk floor needs, or a role outside the matrix) -> APPROVER_UNKNOWN (person not in the directory or without that role) -> STEP_ORDER
(right roles, wrong order) -> KEY_INVALID (a name with a separator, mark, filler or non-ASCII approver) -> REQUESTER_IS_APPROVER -> APPROVER_IS_BENEFICIARY -> SAME_PERSON. People are compared after NFKC, strip and casefold, the same way
everywhere. KEY_COOLDOWN (a rejected key waits) is NOT implemented: a void (WriteGate.void) releases the reservation and audits it, but stage 1 does not block a
re-proposal of the same key.
"""

from __future__ import annotations

import secrets
from datetime import datetime
from types import MappingProxyType

from refunds import identities, textnorm
from refunds.config import APPROVAL_TTL_S, APPROVER_MATRIX, TEXT_MAX
from refunds.hashing import canonical_json
from refunds.signers import HmacSigner, SignatureVerifier, Signer, default_kind, make_signer

FIELDS = ("approval_id", "tenant_id", "args_hash", "tier", "requested_at", "requester", "steps")
ROLES = frozenset(r for rs in APPROVER_MATRIX.values() for r in rs)


class ApprovalDenied(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def norm(s: str) -> str:
    """One way to compare people, requesters and beneficiaries everywhere: the SAME fold as the output scanners (textnorm.normalise: NFKD, drop
    combining marks, format/control and invisible filler characters, NFKC, collapse whitespace, casefold). A look-alike made with U+0301, U+FE0F or
    U+3164 therefore folds to the real address; the write path also refuses such text outright (writegate._text_ok)."""
    return textnorm.normalise(s)


def _skeleton(s: str) -> str:
    """The over-matching key for a must-DIFFER check: the shared core fold (look-alike letters from other scripts mapped to Latin, marks and
    invisible characters dropped, case folded). A disguised copy of an approver collides with the real one, so the check fails SAFE."""
    return textnorm.skeleton(s)


def _is_hex64(x: object) -> bool:
    return isinstance(x, str) and len(x) == 64 and all(c in "0123456789abcdef" for c in x)


def _body(a: dict) -> bytes:
    return canonical_json({k: a[k] for k in FIELDS}).encode("ascii")


class ApprovalVerifier:
    """Checks approvals. Holds a `SignatureVerifier` and a READ-ONLY view of the directory {person: roles they may sign as}; the view is live (the issuer's
    directory changes show through) but nothing here can add an approver."""

    def __init__(self, sigver: SignatureVerifier, directory, ttl_s: int = APPROVAL_TTL_S) -> None:
        self._sigver, self.ttl_s = sigver, ttl_s
        self.directory = MappingProxyType(directory) if isinstance(directory, dict) else directory

    @property
    def can_mint(self) -> bool:
        return self._sigver.can_mint

    @property
    def signer_kind(self) -> str:
        """Written into every applied audit row, so a reviewer can see which approvals were signed by a verifier that could also mint."""
        return str(getattr(self._sigver, "kind", "unknown"))

    def _well_formed(self, a: object) -> bool:
        if not isinstance(a, dict) or set(a) != {*FIELDS, "mac"}:
            return False
        steps = a["steps"]
        return (
            isinstance(a["approval_id"], str)
            and 0 < len(a["approval_id"]) <= 64
            and _is_hex64(a["args_hash"])
            and all(isinstance(a[f], str) for f in ("tenant_id", "tier", "requested_at", "requester", "mac"))
            and a["mac"].isascii()  # a signature is hex; non-ASCII text is not a signature, it is not an approval
            and isinstance(steps, list)
            and len(steps) <= 4
            and all(
                isinstance(s, dict) and set(s) == {"person", "role"} and all(isinstance(v, str) for v in s.values())
                for s in steps
            )
        )

    def verify(
        self, approval: object, *, args_hash: str, tenant_id: str, tier: str, requested_at: str, min_tier: str, requester: str, beneficiary: str,
        now: datetime,
    ) -> str | None:  # fmt: skip
        """`min_tier` is the lowest tier the write path computed itself (human | four_eyes | above); 'above' is left to the cap checks."""
        if not self._well_formed(approval):
            return "NO_APPROVAL"
        a = approval
        body = _body(a)  # type: ignore[arg-type]  # every field was shape-checked above (text, ASCII mac, string-only steps): this cannot raise
        if not self._sigver.verify(body, a["mac"]):  # type: ignore[index]
            return "APPROVAL_INVALID"
        if (
            a["args_hash"] != args_hash  # type: ignore[index]
            or a["tenant_id"] != tenant_id  # type: ignore[index]
            or a["requester"] != requester  # type: ignore[index]
            or a["tier"] != tier  # type: ignore[index]
            or a["requested_at"] != requested_at  # type: ignore[index]
        ):
            return "ARGS_HASH_MISMATCH"
        try:
            age = (now - datetime.fromisoformat(a["requested_at"])).total_seconds()  # type: ignore[index]
        except (ValueError, OverflowError, TypeError):
            return "EXPIRED"
        if age < 0 or age > self.ttl_s:
            return "EXPIRED"
        steps = a["steps"]  # type: ignore[index]
        if tier not in APPROVER_MATRIX or (min_tier == "four_eyes" and tier == "human"):
            return "ROLE_NOT_IN_MATRIX"  # unknown tier, or one approver signed for a basis that needs two
        wanted = APPROVER_MATRIX[tier]
        if len(steps) != len(wanted) or any(s["role"] not in ROLES for s in steps):
            return "ROLE_NOT_IN_MATRIX"
        if any(s["role"] not in self.directory.get(norm(s["person"]), frozenset()) for s in steps):
            return "APPROVER_UNKNOWN"
        if [s["role"] for s in steps] != wanted:
            return "STEP_ORDER"
        if not (textnorm.text_ok(requester, TEXT_MAX) and textnorm.text_ok(beneficiary, TEXT_MAX)) or not all(
            textnorm.text_ok(s["person"], TEXT_MAX) for s in steps
        ):
            return "KEY_INVALID"  # defence in depth: any space, line or paragraph separator, mark or filler in a name is refused here too, whoever called us
        if not all(s["person"].isascii() for s in steps):
            return "KEY_INVALID"  # approvers are staff: ASCII ids, so no approver can be a disguised copy of someone else
        people = [norm(s["person"]) for s in steps]
        skeletons = [_skeleton(s["person"]) for s in steps]
        if norm(requester) in people or _skeleton(requester) in skeletons:
            return "REQUESTER_IS_APPROVER"
        if norm(beneficiary) in people or _skeleton(beneficiary) in skeletons:
            return "APPROVER_IS_BENEFICIARY"  # the skeleton also equates a Cyrillic/Greek/Armenian look-alike spelling of an approver
        if len(set(people)) != len(people):
            return "SAME_PERSON"
        return None


class ApprovalIssuer:
    """Signs approvals for the human approver identity. The write path never receives this object (see `verifier()`)."""

    def __init__(
        self, directory: dict[str, list[str]], key: bytes | None = None, ttl_s: int = APPROVAL_TTL_S, signer: Signer | None = None
    ) -> None:
        # An explicit key means a DEV HMAC signer (can mint). No key and no signer: ed25519, or SignerNotConfigured: never a silent HMAC.
        self._signer: Signer = (
            signer if signer is not None else (HmacSigner(key) if key is not None else make_signer(default_kind()))
        )
        self.directory: dict[str, frozenset] = {norm(p): frozenset(r) for p, r in directory.items()}
        self.ttl_s = ttl_s

    def verifier(self) -> ApprovalVerifier:
        """A verify-only object: the signer kind's verifier plus a read-only live view of the directory."""
        return ApprovalVerifier(self._signer.verifier(), self.directory, self.ttl_s)

    def issue(
        self,
        identity: str,
        *,
        tenant_id: str,
        args_hash: str,
        tier: str,
        requested_at: str,
        requester: str,
        people: list[tuple[str, str]],
    ) -> dict:
        """Only the human approver identity may sign (a label check). `people` is [(person, role signed as)] in step order."""
        if not identities.authorize(identity, "approve"):
            raise ApprovalDenied("IDENTITY_DENIED")
        body = {
            "approval_id": "ap-" + secrets.token_hex(12),
            "tenant_id": tenant_id,
            "args_hash": args_hash,
            "tier": tier,
            "requested_at": requested_at,
            "requester": requester,
            "steps": [{"person": p, "role": r} for p, r in people],
        }
        return {**body, "mac": self._signer.sign(_body(body))}
