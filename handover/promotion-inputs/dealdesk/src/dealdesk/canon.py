"""Canonical serialisation and hashes (F10): one definition, so two implementations cannot disagree on a hash or an idempotency key."""

from __future__ import annotations

import hashlib
import json

SNAPSHOT_FIELDS = (
    "price_book_version",
    "plan",
    "currency",
    "list_seat",
    "cogs_seat",
    "floor_bps",
    "seats",
    "customer_tier",
    "arr_minor",
    "request_type",
    "owner_rep",
)
TERM_FIELDS = ("discount_bps", "term_years", "billing", "payment_terms_days", "sla_tier")


def canonical_json(obj) -> bytes:
    """Sorted keys, no spaces, ASCII escapes, UTF-8 bytes. Integers only (money is a string or int, never a float)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def sha256_hex(obj) -> str:
    return hashlib.sha256(canonical_json(obj)).hexdigest()


def idem_key(action: str, deal_id: str, terms_hash: str, *extra) -> str:
    """Business-scoped key: sha256 over the canonical JSON ARRAY [action, deal_id, terms_hash, *extra] (no delimiter ambiguity).
    request_approval: extra = (lane, epoch). generate_quote_draft: extra = (epoch,). Epoch = how many earlier approvals for this
    (deal, terms, lane) expired or were voided, plus 1: a replay of the same epoch is a duplicate; a re-request after expiry is not."""
    return sha256_hex([action, deal_id, terms_hash, *extra])


def snapshot_hash(deal: dict, book: dict) -> str:
    p = book["plans"][deal["plan"]][deal["currency"]]
    snap = {"price_book_version": book["version"], "plan": deal["plan"], "currency": deal["currency"], "list_seat": p["list_seat"], "cogs_seat": p["cogs_seat"],
            "floor_bps": book["floor_bps"][deal["plan"]], "seats": deal["seats"], "customer_tier": deal["customer_tier"], "arr_minor": deal["arr_minor"],
            "request_type": deal["request_type"], "owner_rep": deal["owner_rep"]}  # fmt: skip
    if tuple(snap) != SNAPSHOT_FIELDS:
        raise ValueError("snapshot fields drifted")
    return sha256_hex(snap)


def terms_hash(
    deal_id: str,
    currency: str,
    terms: dict,
    list_total: int,
    discount: int,
    net: int,
    price_book_version: str,
    matrix_sha256: str,
) -> str:
    return sha256_hex({"deal_id": deal_id, "currency": currency, "terms": {k: terms[k] for k in TERM_FIELDS}, "list_total": str(list_total),
                       "discount": str(discount), "net": str(net), "price_book_version": price_book_version, "matrix_sha256": matrix_sha256})  # fmt: skip


QUOTE_FIELDS = (
    "deal_id", "account_id", "account_name", "currency", "plan", "seats", "terms", "clauses", "list_total", "discount", "net", "tax_bps", "tax_minor",
    "total", "tax_region", "price_book_version", "matrix_sha256", "policy_sha256", "valid_days",
)  # fmt: skip


def quote_hash(q: dict) -> str:
    """R-DEALDESK-085: hash of the QUOTE document exactly as a customer would receive it. Closed field set; clauses are sorted and de-duplicated here so
    order and repeats cannot change the hash; money is carried as integer strings."""
    if set(q) != set(QUOTE_FIELDS):
        raise ValueError(f"quote fields differ: {sorted(set(q) ^ set(QUOTE_FIELDS))}")
    doc = {**q, "clauses": sorted(set(q["clauses"])), "terms": {k: q["terms"][k] for k in TERM_FIELDS}}
    for k in ("list_total", "discount", "net", "tax_minor", "total"):
        doc[k] = str(doc[k])
    return sha256_hex(doc)


# ------------------------------------------------------------------ signed decisions (B1, M11, M12)
# The approver signs, with a PRIVATE key the engine never holds (Ed25519), exactly the fields below plus `key_id`, using the core approval-signature
# format (`core_copy/approvals_signed.py`, copied from core PR #49, see CORE_COPIES.md). The generic core schema supplies the id, tenant, hash and time
# fields; `args_hash` is the hash of everything the approver saw and decided, so a changed field fails the signature, not only a comparison.
APPROVAL_FIELDS = (
    "approval_id", "tenant_id", "args_hash", "requested_at", "deal_id", "terms_hash", "quote_hash", "snapshot_hash", "lane", "min_role", "epoch",
    "approver_id", "decision", "ts",
)  # fmt: skip
BOUND_FIELDS = ("deal_id", "terms_hash", "quote_hash", "snapshot_hash", "lane", "min_role", "epoch", "approver_id", "decision")


def decision_args_hash(fields: dict) -> str:
    """Hash of what the approver saw and decided. `ts` is signed but informational; the authoritative time is the channel receipt time."""
    return sha256_hex({k: fields[k] for k in BOUND_FIELDS})


def mint_id(prefix: str, entropy: bytes) -> str:
    """Approval ids carry 128 bits of entropy (scripted runs: from the seeded run RNG; live: os.urandom(16)); never a truncated computable hash."""
    if len(entropy) != 16:
        raise ValueError("need 16 bytes")
    return f"{prefix}-{entropy.hex()}"
