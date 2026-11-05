"""Canonical serialisation for the approval args hash (R-REF-016, design review M13). RFC 8785-style: sorted keys,
no whitespace, ASCII-escaped, UTF-8. The hash covers tenant, tool, args, tier, basis snapshot, business key, ToolContext.customer_id and the request time (an altered request time would extend the TTL)."""

from __future__ import annotations

import hashlib
import json


def canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def args_hash(
    tenant_id: str, tool: str, args: dict, tier: str, basis_snapshot: dict, key: str, customer_id: str, requested_at: str
) -> str:
    body = {
        "tenant_id": tenant_id,
        "tool": tool,
        "args": args,
        "tier": tier,
        "basis": basis_snapshot,
        "key": key,
        "customer_id": customer_id,
        "requested_at": requested_at,
    }
    return hashlib.sha256(canonical_json(body).encode("ascii")).hexdigest()
