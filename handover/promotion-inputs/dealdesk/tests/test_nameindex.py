"""The account-name index (burst scaling fix). The answer must equal the linear scan on every input; the cost must not depend on the number of accounts;
ingest-ack time is measured on its own, apart from processing."""

import random
import time

import pytest
from engine_kit import Kit, mk_deal

from dealdesk import desk_rules as dr
from dealdesk import gate_rules as g
from dealdesk import inbox as ib
from dealdesk.desk import SYS
from dealdesk.handler import other_accounts_named
from dealdesk.nameindex import NameIndex, lower_norm
from dealdesk.textnorm import views

PIECES = [
    "acme",
    "Acme",
    "ACME",
    "corp",
    "ltd",
    "x",
    "é",
    "ü",
    "İ",
    "_",
    "-",
    " ",
    "  ",
    ".",
    "1",
    "7",
    "Ａ",
    "ａcme",
    "а",
    "o",
    "О",
    "(",
    ")",
    "&",
    "\u200b",
    "ß",
    "nord",
]


def _names(rnd, n):
    return ["".join(rnd.choice(PIECES) for _ in range(rnd.randint(1, 5))) for _ in range(n)]


def _linear_quote(account_name, accounts):
    own = views(account_name)
    from dealdesk.core_copy.textnorm import names_equal

    return any(
        any(dr._whole(h, v) for h in own for v in views(n) if v) for _a, n in accounts.items() if not names_equal(n, account_name)
    )


def test_quote_scan_equals_the_linear_scan_on_random_and_hostile_names():
    rnd = random.Random(20261102)
    hits = 0
    for _ in range(400):
        accounts = {f"a{i}": nm for i, nm in enumerate(_names(rnd, 12))}
        idx = NameIndex(accounts)
        text = "".join(rnd.choice(PIECES) for _ in range(rnd.randint(1, 8)))
        got = "other_account" in dr.quote_name_findings(text, idx, {"competitor_names": []})
        assert got == _linear_quote(text, accounts), (text, accounts)
        hits += got
    assert 10 < hits < 390, hits  # the property is not vacuous: both outcomes occur


def test_message_scan_equals_the_linear_scan_on_random_and_hostile_names():
    rnd = random.Random(7)
    hits = 0
    for _ in range(400):
        accounts = {f"a{i}": nm for i, nm in enumerate(_names(rnd, 12))}
        idx = NameIndex(accounts)
        text = "".join(rnd.choice(PIECES) for _ in range(rnd.randint(1, 10)))
        own_id, own_name = "a0", accounts["a0"]
        want = g.names_in_text(text, [n for aid, n in accounts.items() if aid != own_id and n != own_name])
        got = other_accounts_named(idx, text, own_name)
        assert sorted(got) == sorted(want), (text, accounts)
        hits += bool(want)
    assert 10 < hits < 390, hits


def test_names_without_an_alphanumeric_run_are_still_found():
    idx = NameIndex({"a": "(((", "b": "Acme"})
    assert [a for a, _n in idx.by_lower("see ((( here")] == ["a"]
    assert "a" in [a for a, _n in idx.by_views(views("x ((( y"))]


def test_a_rename_is_seen_by_the_cached_index():
    k = Kit(deals=[mk_deal("deal-1", "acct-1", "Zephyr Works"), mk_deal("deal-2", "acct-2", "Quokka Labs")])
    before = k.desk.ports.account_name_index(SYS)
    assert [n for _a, n in before.by_lower("quokka labs")] == ["Quokka Labs"]
    k.world.rename_account("acct-2", "Narwhal Labs")
    after = k.desk.ports.account_name_index(SYS)
    assert [n for _a, n in after.by_lower("narwhal labs")] == ["Narwhal Labs"]
    assert not after.by_lower("quokka labs")


@pytest.mark.parametrize("n", [3000])
def test_ack_time_is_measured_apart_from_processing_and_is_far_under_the_target(n):
    """Target: ingest acknowledgement p99 under 1,000 ms (inbound ledger load profile). Receive writes the ledger row and returns; it never runs the handler."""
    ran = []
    inbox = ib.Inbox(ib.MemoryLedger(), lambda *a, **kw: ran.append(1))
    times = []
    for i in range(n):
        m = {
            "msg_id": f"m{i:05d}",
            "kind": "request",
            "requester_id": "p-ae-01",
            "deal_id": f"deal-{i:05d}",
            "text": "15% please",
        }
        t0 = time.perf_counter()
        inbox.receive("t-a", m)
        times.append(time.perf_counter() - t0)
    times.sort()
    assert not ran, "receive must not run the handler"
    assert times[int(0.99 * n) - 1] < 1.0
    assert lower_norm(" A  b ") == "a b"
