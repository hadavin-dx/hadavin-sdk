"""Pins the payment-scan exclude list, kept apart from the list and from the scanner so one edit cannot loosen both."""

from __future__ import annotations

from conftest import ROOT

LIST = ROOT / "tests" / "fixtures" / "payment_scan_exclude.txt"
PINNED = {"tools/mutate_src.py", "tools/check_core_copies.py"}  # changed only by the lead


def patterns() -> list[str]:
    return [ln.strip() for ln in LIST.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]


def test_the_exclude_list_is_exactly_the_pinned_files():
    assert set(patterns()) == PINNED and len(patterns()) == len(PINNED)


def test_no_wildcard_no_src_no_order_flow_file_in_the_list():
    for pat in patterns():
        assert "*" not in pat, pat
        assert not pat.startswith(("src/", "demo_only/")), pat
        assert pat.rsplit("/", 1)[-1] not in {"executor.py", "tools.py"} and "adapters" not in pat.split("/"), pat
