"""Client / demo segregation (segregation rule). Every store, index, embedding set, cache, prompt/few-shot set, golden/eval set, log, secret and
model config is addressed through a Namespace bound to ONE client id. There is no shared pool: a key from another client is refused, and a
key without the client prefix is refused. Stage 2 binds the same rule to real stores (separate databases, indexes, buckets and keys)."""

from __future__ import annotations

KINDS = (
    "store",
    "index",
    "embeddings",
    "cache",
    "prompts",
    "fewshot",
    "golden",
    "eval",
    "logs",
    "memory",
    "feedback",
    "secrets",
    "model_config",
)
CLIENT_ID = "refunds"


class CrossClientAccess(PermissionError):
    pass


def config_key(name: str, client_id: str = CLIENT_ID) -> str:
    """Every config key carries the client id: 'refunds.<name>'."""
    return f"{client_id}.{name}"


class Namespace:
    def __init__(self, client_id: str, backing: dict | None = None) -> None:
        if not client_id or "/" in client_id or "." in client_id:
            raise ValueError("bad client id")
        self.client_id = client_id
        self._d = backing if backing is not None else {}

    def key(self, kind: str, name: str) -> str:
        if kind not in KINDS:
            raise ValueError(f"unknown kind {kind}")
        return f"{self.client_id}/{kind}/{name}"

    def _check(self, full_key: str) -> None:
        parts = full_key.split("/")
        if parts[0] != self.client_id or len(parts) < 3 or any(p in ("", ".", "..") for p in parts) or "\\" in full_key:
            raise CrossClientAccess(f"{self.client_id} may not touch {full_key.split('/')[0]!r} data")

    def put(self, kind: str, name: str, value) -> None:
        self._d[self.key(kind, name)] = value

    def get(self, kind: str, name: str, default=None):
        return self._d.get(self.key(kind, name), default)

    def get_raw(self, full_key: str):
        self._check(full_key)
        return self._d.get(full_key)

    def items(self) -> dict:
        return {k: v for k, v in self._d.items() if k.startswith(self.client_id + "/")}
