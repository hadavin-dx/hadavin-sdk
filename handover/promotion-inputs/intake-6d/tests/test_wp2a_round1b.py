"""Round 1b: tests that kill the surviving mutants of the first evidence run (pound/euro prefixes, handle closed on failure)."""

from __future__ import annotations

import os

import pytest

from intake import ground, lockfile


@pytest.mark.parametrize("sym", [chr(0xA3), chr(0x20AC)])
@pytest.mark.parametrize("space", ["", " "])
def test_pound_and_euro_amounts_are_not_quantities(sym, space):
    text = f"INV-1001 Acme Ltd 2026-10-01 EUR\nWidget A  {sym}{space}250.00  {sym}{space}500.00\nTotal {sym}500.00\n"
    f = {
        "invoice_no": "INV-1001",
        "supplier_name": "Acme Ltd",
        "po_ref": None,
        "currency": "EUR",
        "invoice_date": "2026-10-01",
        "lines": [{"description": "Widget A", "qty": 250, "unit_cost_minor": 25000, "amount_minor": 50000}],
        "adjustments": [],
        "total_minor": 50000,
    }
    assert ground.ground(f, text).failing_fields == ("lines",)


def test_a_refused_acquire_closes_its_handle(tmp_path, monkeypatch):
    p = tmp_path / "serve.lock"
    h = lockfile.acquire(p)
    opened = []
    real = os.fdopen

    def spy(*a, **k):
        f = real(*a, **k)
        opened.append(f)
        return f

    monkeypatch.setattr(os, "fdopen", spy)
    try:
        with pytest.raises(lockfile.LockHeld):
            lockfile.acquire(p)
        assert len(opened) == 1 and opened[0].closed
    finally:
        lockfile.release(h)
