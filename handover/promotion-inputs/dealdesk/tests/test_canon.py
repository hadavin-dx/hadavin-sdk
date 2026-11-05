"""Canonical serialisation: pinned vectors so two implementations cannot disagree on a hash or an idempotency key."""

import json
from pathlib import Path

import pytest

from dealdesk import canon

D = Path(__file__).resolve().parent.parent
BOOK = json.loads((D / "tests/fixtures/pricebook.json").read_text())


def test_canonical_json_is_sorted_compact_ascii():
    assert canon.canonical_json({"b": 1, "a": ["x", 2]}) == b'{"a":["x",2],"b":1}'
    assert canon.canonical_json({"k": "caf\u00e9"}) == b'{"k":"caf\\u00e9"}'
    with pytest.raises(ValueError):
        canon.canonical_json({"x": float("nan")})


def test_idem_key_vector_and_epoch_moves_it():
    k1 = canon.idem_key("request_approval", "deal-0001", "ab" * 32, "commercial", 1)
    assert k1 == canon.sha256_hex(["request_approval", "deal-0001", "ab" * 32, "commercial", 1])
    assert len(k1) == 64 and k1 != canon.idem_key("request_approval", "deal-0001", "ab" * 32, "commercial", 2)
    # no delimiter ambiguity: moving text between fields changes the key
    assert canon.idem_key("a", "b|c", "d") != canon.idem_key("a|b", "c", "d")


def test_snapshot_changes_with_every_listed_field():
    deal = {
        "plan": "team",
        "currency": "USD",
        "seats": 10,
        "customer_tier": "mid",
        "arr_minor": "0",
        "request_type": "new",
        "owner_rep": "p-ae-01",
    }
    base = canon.snapshot_hash(deal, BOOK)
    for k, v in (
        ("seats", 11),
        ("customer_tier", "smb"),
        ("arr_minor", "5"),
        ("request_type", "renewal"),
        ("owner_rep", "p-ae-02"),
        ("plan", "business"),
        ("currency", "GBP"),
    ):
        assert canon.snapshot_hash({**deal, k: v}, BOOK) != base, k
    assert canon.snapshot_hash(deal, {**BOOK, "version": "pb-next"}) != base
    assert canon.snapshot_hash(deal, {**BOOK, "floor_bps": {**BOOK["floor_bps"], "team": 6400}}) != base
