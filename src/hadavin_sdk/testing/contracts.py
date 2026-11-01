# ruff: noqa: S101
"""Reusable contract checks: run one against every implementation of a Protocol so a second backend cannot drift.

``check_rowstore_contract(make)`` takes a zero-argument factory for anything that implements
``runtime.rowstore.RowStoreLike`` and asserts the behaviour callers rely on (audit before write, copies out, bad rows
fail before the audit, snapshot while an audit callback reads)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def check_rowstore_contract(make: Callable[[], Any]) -> None:
    store, audited = make(), []
    store.put_audited(
        lambda kind, **f: audited.append((kind, f["key"])), "row_added", "k1", {"a": [1, 2]}
    )
    assert audited == [("row_added", "k1")]
    got = store.get("k1")
    got["a"].append(3)
    assert store.get("k1") == {"a": [1, 2]}, "get must return a copy"
    snap = store.snapshot()
    snap["k1"]["a"].clear()
    assert store.snapshot() == {"k1": {"a": [1, 2]}}, "snapshot must return copies"

    def failing(kind: str, **f: Any) -> None:
        raise OSError("audit down")

    try:
        store.put_audited(failing, "row_added", "k2", {"a": 1})
    except OSError:
        pass
    else:
        raise AssertionError("a failed audit write must propagate")
    assert store.keys() == ["k1"], "a failed audit write must insert nothing"

    calls = []
    for bad in ({"a": float("nan")}, {1: "x"}, {"a": {(1, 2): 1}}, {"a": {1, 2}}):
        try:
            store.put_audited(lambda kind, **f: calls.append(kind), "row_added", "k3", bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"a bad row must be refused: {bad!r}")
    assert calls == [] and store.keys() == ["k1"], "a bad row must fail before the audit"

    seen = []
    store.put_audited(
        lambda kind, **f: seen.append(sorted(store.snapshot())), "row_added", "k4", {}
    )
    assert seen == [["k1"]], "an audit callback may read the store"
