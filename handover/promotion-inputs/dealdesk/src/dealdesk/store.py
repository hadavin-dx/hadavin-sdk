"""Tenant-scoped data layer (R-DEALDESK-094, 095; tenant isolation and segregation). Every key is `dealdesk/<tenant>/<kind>/<name>`. The layer, not the caller, refuses a
missing, malformed, unknown or foreign tenant (fail CLOSED: no tenant id never means 'all tenants'), a kind outside KINDS and any path trick.
Stage 2 binds the same rule to separate databases/schemas/keys (row-level security); the in-memory dict is the neutral default."""

from __future__ import annotations

import copy
import hashlib
import re
import threading

from dealdesk.canon import canonical_json, sha256_hex
from dealdesk.errors import CrossTenantAccess, Malformed

CLIENT_ID = "dealdesk"
KINDS = ("quotes", "approvals", "decisions", "commits", "drafts", "rejections", "audit", "budget", "ledger", "cache", "memory", "feedback", "prompts",
         "fewshot", "golden", "eval", "logs", "outbox", "index", "embeddings", "secrets", "model_config")  # fmt: skip
_TENANT = re.compile(r"[a-z0-9][a-z0-9-]{0,39}", re.ASCII)


def check_tenant(tenant_id: object) -> str:
    if not isinstance(tenant_id, str) or not _TENANT.fullmatch(tenant_id):
        raise Malformed("tenant id missing or malformed (fail closed)")
    return tenant_id


class TenantStore:
    def __init__(self, tenant_id: str, backing: dict | None = None) -> None:
        self.tenant_id = check_tenant(tenant_id)
        self._d = backing if backing is not None else {}
        self.lock = threading.RLock()

    def key(self, kind: str, name: str) -> str:
        if kind not in KINDS:
            raise Malformed(f"unknown kind {kind!r}")
        if not isinstance(name, str) or not name or "/" in name or "\\" in name or name in (".", ".."):
            raise Malformed("bad name")
        return f"{CLIENT_ID}/{self.tenant_id}/{kind}/{name}"

    def _check_raw(self, full_key: object) -> None:
        parts = full_key.split("/") if isinstance(full_key, str) else []
        if len(parts) != 4 or parts[0] != CLIENT_ID or any(p in ("", ".", "..") for p in parts) or "\\" in str(full_key):
            raise CrossTenantAccess("malformed key")
        if parts[1] != self.tenant_id:
            raise CrossTenantAccess(f"tenant {self.tenant_id!r} may not touch another tenant's data")

    def put(self, kind: str, name: str, value) -> None:
        with self.lock:
            self._d[self.key(kind, name)] = copy.deepcopy(value)

    def put_many(self, items: list[tuple[str, str, object]]) -> None:
        """Several records in ONE write (all keys are validated first; then all are stored under one lock acquisition). A client build maps this to one
        database transaction, so a crash can never leave the first record without the second."""
        keyed = [(self.key(k, n), copy.deepcopy(v)) for k, n, v in items]
        with self.lock:
            self._d.update(keyed)

    def get(self, kind: str, name: str, default=None):
        with self.lock:
            return copy.deepcopy(self._d.get(self.key(kind, name), default))

    def get_raw(self, full_key: str):
        self._check_raw(full_key)
        with self.lock:
            return copy.deepcopy(self._d.get(full_key))

    def names(self, kind: str) -> list[str]:
        pre = self.key(kind, "x")[:-1]
        with self.lock:
            return sorted(k[len(pre) :] for k in self._d if k.startswith(pre))

    def all_items(self) -> dict:
        pre = f"{CLIENT_ID}/{self.tenant_id}/"
        with self.lock:
            return {k: copy.deepcopy(v) for k, v in self._d.items() if k.startswith(pre)}


class AuditChain:
    """Append-only hash chain per tenant. Tamper-EVIDENT only if the head is kept outside the store (the operator hand-over lock); never 'immutable'."""

    def __init__(self, store: TenantStore) -> None:
        self.store = store

    def append(self, event: dict) -> dict:
        with self.store.lock:
            head = self.store.get("logs", "audit-head", {"n": 0, "sha256": "0" * 64})
            n, prev = head["n"], head["sha256"]
            body = {"seq": n, "prev_sha256": prev, "tenant_id": self.store.tenant_id, **event}
            rec = {**body, "sha256": hashlib.sha256(canonical_json(body)).hexdigest()}
            self.store.put("audit", f"{n:08d}", rec)
            self.store.put("logs", "audit-head", {"n": n + 1, "sha256": rec["sha256"]})
            return rec

    def verify(self) -> bool:
        prev = "0" * 64
        for i, name in enumerate(self.store.names("audit")):
            rec = self.store.get("audit", name)
            body = {k: v for k, v in rec.items() if k != "sha256"}
            if rec["seq"] != i or rec["prev_sha256"] != prev or sha256_hex(body) != rec["sha256"]:
                return False
            prev = rec["sha256"]
        return prev == self.head()  # a deleted tail record is detected too

    def head(self) -> str:
        return self.store.get("logs", "audit-head", {"sha256": "0" * 64})["sha256"]
