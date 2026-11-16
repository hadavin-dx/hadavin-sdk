"""Integration check (WP5 pipeline over WP2a extract and WP4 queue): a ledger write failure (``settle_failed``) leaves ``pipeline.process`` as an
exception (the process must stop), is not turned into an L02 flag, and the item stays RECEIVED so ``recover_received`` finds it after a restart."""

from __future__ import annotations

import pytest

from conftest import MINI, settings_for_tests
from intake import pipeline, reader, workqueue
from intake.codes import ConfigError


class LedgerDown:
    def __init__(self):
        self.calls = 0

    def call(self, req):
        self.calls += 1
        raise ConfigError("settle_failed", "the spend ledger could not write")


def test_settle_failed_leaves_process_and_the_item_stays_received(tmp_path):
    s = settings_for_tests(tmp_path)
    sup = pipeline.load_suppliers(s.intake_home / "suppliers.csv")
    m = LedgerDown()
    parsed = reader.read("inv-A.txt", (MINI / "inv-A.txt").read_bytes())
    with pytest.raises(ConfigError) as e:
        pipeline.process(s, parsed, m, sup)
    assert e.value.code == "settle_failed" and m.calls == 1  # no fallback call
    items = workqueue.list_items(s)
    assert [i.state for i in items] == ["RECEIVED"] and items[0].flags == ()
