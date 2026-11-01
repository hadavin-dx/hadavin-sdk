"""Intent -> call -> settle: the placement of a processor call relative to the store transaction.

Never call the processor inside the store's write transaction (it holds the lock across a network call, and a rollback would hide an
intent whose money moved). Three steps: (A) one transaction records the `intent` and commits; (B) the processor call runs OUTSIDE any
transaction with the business key as its idempotency key; (C) a second transaction records the outcome. A crash between A and C leaves an
intent with no outcome; `reconcile` resolves it by looking the key up at the processor (a failed lookup is UNKNOWN, never "not applied").
The two Protocols are the whole contract; a database and a processor client implement them.
"""

from __future__ import annotations

from typing import Protocol


class IntentStore(Protocol):
    def record_intent(self, key: str) -> bool:
        """Commit the intent in its own transaction. False if the key already has an intent or an outcome."""
        ...

    def settle(self, key: str, outcome: str) -> None: ...

    def open_intents(self) -> list[str]: ...


class Processor(Protocol):
    def apply(self, key: str) -> str:
        """Perform the action with `key` as the idempotency key; return an outcome string. May raise."""
        ...

    def lookup(self, key: str) -> str | None:
        """The outcome if applied, None if definitely not applied. Raises when it cannot tell."""
        ...


def run(store: IntentStore, processor: Processor, key: str) -> str:
    if not store.record_intent(key):
        return "duplicate_ignored"
    try:
        outcome = processor.apply(key)
    except Exception:  # noqa: BLE001 - the call may or may not have happened; reconcile decides
        return "unknown"
    store.settle(key, outcome)
    return outcome


def reconcile(store: IntentStore, processor: Processor) -> dict[str, str]:
    """Resolve every open intent: applied -> settle with the processor's outcome; not applied -> leave open for a same-key retry; cannot tell -> unknown."""
    result: dict[str, str] = {}
    for key in store.open_intents():
        try:
            found = processor.lookup(key)
        except Exception:  # noqa: BLE001
            result[key] = "unknown"
            continue
        if found is None:
            result[key] = "not_applied"
        else:
            store.settle(key, found)
            result[key] = found
    return result
