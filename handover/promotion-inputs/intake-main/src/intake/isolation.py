"""Per-client segregation (segregation). A `ClientContext` owns EVERYTHING that can learn or remember: few-shot examples, memory, cache, logs, and the namespaces of the store, index,
embeddings, prompts, eval sets, secrets and model config. Nothing is shared between contexts: no module-level pool, cache or memory exists in this package (a test scans for
that), `add_example` refuses an example owned by another client, and every namespace key starts with the client id from `config/policy.json`. Improvements that travel between
clients are CODE and prompt templates written without client data; they enter through `build_prompt`'s template argument, never through learned state."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[2] / "config"
KINDS = ("data_store", "vector_index", "embeddings", "cache", "prompts", "few_shot", "memory", "eval", "logs", "secrets", "model_config")


def policy_namespaces(path: Path = CONFIG / "policy.json") -> tuple[str, dict[str, str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw["client_id"], raw["namespaces"]


def demo_path(rel: str, root: Path | None = None) -> Path:
    """Resolve a path INSIDE this demo's folder; an absolute path or a `..` escape is refused (nothing here reads another demo's data, eval or memory)."""
    base = (root or CONFIG.parent).resolve()
    p = (base / rel).resolve()
    if p != base and base not in p.parents:
        raise ValueError(f"{rel!r} escapes the demo folder")
    return p


class ClientContext:
    def __init__(self, client_id: str) -> None:
        self.client_id = client_id
        self.few_shot: list[str] = []
        self.memory: dict[str, str] = {}
        self.cache: dict[str, str] = {}
        self.log: list[str] = []
        self.feedback: list[str] = []
        self.eval_set: list[str] = []

    def ns(self, kind: str, name: str) -> str:
        if kind not in KINDS:
            raise ValueError(f"unknown namespace kind {kind!r}")
        return f"{self.client_id}/{kind}/{name}"

    def add_example(self, owner_client_id: str, text: str) -> None:
        if owner_client_id != self.client_id:
            raise PermissionError("a few-shot example belongs to exactly one client")
        self.few_shot.append(text)

    def remember(self, key: str, value: str) -> None:
        self.memory[self.ns("memory", key)] = value

    def build_prompt(self, document: str, template: str = "Extract raw fields only. Never resolve ids, prices or currency.") -> str:
        parts = [f"TEMPLATE: {template}", f"CLIENT: {self.client_id}", *[f"EXAMPLE: {e}" for e in self.few_shot], "DOCUMENT:", document]
        prompt = "\n".join(parts)
        h = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        self.cache[self.ns("cache", h)] = prompt
        self.log.append(f"prompt {h} len={len(prompt)}")
        return prompt

    def run(self, runner: Callable[[dict, dict, str], dict], cases: list[dict], seed: dict, text_of: Callable[[dict], str]) -> bytes:
        """Deterministic outputs of THIS client's pipeline over its own cases and its own seed, as bytes."""
        out = []
        for c in cases:
            d = runner(seed, c, text_of(c))
            out.append({"case": c["case_id"], "exc": sorted(d["exc"]), "verdict": d["verdict"], "tier": d["tier"], "draft": d["draft"]})
            self.log.append(f"run {c['case_id']} {d['verdict']}")
        return json.dumps(out, sort_keys=True).encode()
