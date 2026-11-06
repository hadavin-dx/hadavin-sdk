"""Helpers for the stop-state tests: a test label key (built from parts) and an operator-side `Limits`."""

from __future__ import annotations

from hadavin_sdk.limits import Limits

# Built from parts: no key-looking literal in the repo.
KEY = b"".join([b"test-label-", b"key-part-", b"0123456789abcdef"])
RESET_NAME = "user:a"


def operator_limits(limits: Limits, names: tuple[str, ...] = (RESET_NAME,), **kw) -> Limits:
    """A `Limits` like the operator's process: same store, audit and registry, a fixed label key, and the
    store itself as the reset handle. (The app's own `limits` has no reset handle, by design.)"""
    return Limits(
        limits.store,
        limits.audit,
        limits.registry,
        environment="dev",
        reset_store=kw.pop("reset_store", limits.store),
        reset_names=frozenset(names),
        label_key=KEY,
        key_id="k1",
        **kw,
    )


def expect(limits: Limits) -> dict[str, int]:
    """What the operator copies from `limits status` into `limits reset`."""
    s = limits.status()
    return {"expect_version": s.version, "expect_open": s.open_requests}


RESET_GROUP = "hadavin_test_reset"
