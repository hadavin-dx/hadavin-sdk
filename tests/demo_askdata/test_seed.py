"""The Lumen Goods dataset: arithmetic of the design, determinism, plants, manifest, and a database round trip."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import secrets
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from tests.demo_askdata.conftest import DEMO, _split, load_script

lumen = load_script("lumen")
COL = lumen.COLUMNS


def col(ds, table: str, name: str) -> list:
    i = COL[table].index(name)
    return [r[i] for r in ds.tables[table]]


@pytest.fixture(scope="module")
def builds():
    return {n: lumen.build(n) for n in ("a", "b", "clean")}


@pytest.fixture(params=["a", "b", "clean"])
def ds(request, builds):
    return builds[request.param]


def test_row_counts_and_totals(ds):
    t = ds.tables
    assert {k: len(v) for k, v in t.items()} == {
        "customers": 1200, "products": 120, "orders": 6000, "order_items": 13800,
        "payments": 6480, "refunds": 1040, "support_tickets": 1500,
    }  # fmt: skip


def test_order_status_discount_channel_flag_quotas(ds):
    assert Counter(col(ds, "orders", "status")) == lumen.STATUS_COUNTS
    assert Counter(col(ds, "orders", "discount_pct")) == lumen.DISCOUNTS
    ch = Counter(col(ds, "orders", "channel"))
    flags = Counter(col(ds, "orders", "fl_cd"))
    assert flags == lumen.FL_CD
    if ds.planted:  # the enum plant moves one order out of its real channel
        real = {k: v for k, v in ch.items() if k in lumen.CHANNELS}
        assert sum(real.values()) == 5999 and len(ch) == 4
        assert sum(lumen.CHANNELS[k] - v for k, v in real.items()) == 1
    else:
        assert ch == lumen.CHANNELS


def test_items_per_order_distribution_and_mean(ds):
    per = Counter(r[1] for r in ds.tables["order_items"])
    assert Counter(per.values()) == lumen.ITEMS_PER_ORDER
    assert len(ds.tables["order_items"]) / 6000 == pytest.approx(2.30, abs=1e-9)
    assert min(r[3] for r in ds.tables["order_items"]) == 1
    assert max(r[3] for r in ds.tables["order_items"]) == 5


def test_payments_arithmetic(ds):
    status = {r[0]: r[3] for r in ds.tables["orders"]}
    pay = Counter((r[5], status[r[1]]) for r in ds.tables["payments"])
    assert pay[("captured", "paid")] == 360
    assert pay[("captured", "shipped")] == 480
    assert pay[("captured", "delivered")] == 3720
    assert pay[("captured", "refunded")] == 780
    assert sum(n for (s, _), n in pay.items() if s == "captured") == 5340
    assert pay[("failed", "placed")] == 180 and pay[("failed", "cancelled")] == 180
    assert sum(n for (s, _), n in pay.items() if s == "failed") == 360
    assert sum(n for (s, _), n in pay.items() if s == "refunded") == 780
    # a placed or cancelled order never has a captured payment
    assert not [k for k in pay if k[0] == "captured" and k[1] in ("placed", "cancelled")]


def test_refunds_arithmetic(ds):
    status = {r[0]: r[3] for r in ds.tables["orders"]}
    by = Counter(status[r[1]] for r in ds.tables["refunds"])
    assert by == {"refunded": 780, "delivered": 260}
    assert sum(by.values()) == 1040
    assert set(col(ds, "refunds", "reason")) == {
        "damaged",
        "late",
        "wrong_item",
        "changed_mind",
        "fraud",
    }
    assert all(r[3] > 0 for r in ds.tables["refunds"])


def test_customer_order_quotas_and_dates(ds):
    signup = {r[0]: r[4] for r in ds.tables["customers"]}
    orders = Counter(r[1] for r in ds.tables["orders"])
    assert len(signup) - len(orders) == 96
    ranked = sorted(orders.items(), key=lambda kv: -kv[1])
    heavy = [cid for cid, _ in ranked[:240]]
    assert sum(orders[c] for c in heavy) == 3600
    assert sum(orders.values()) - 3600 == 2400
    assert all(signup[c] <= date(2025, 12, 31) for c in heavy)
    assert min(orders[c] for c in heavy) > max(orders[c] for c in orders if c not in heavy)
    for r in ds.tables["orders"]:
        assert datetime(signup[r[1]].year, signup[r[1]].month, signup[r[1]].day, tzinfo=UTC) <= r[2]
        assert r[2].date() <= lumen.AS_OF
    sd = list(signup.values())
    assert min(sd) >= date(2025, 1, 1) and max(sd) <= date(2026, 10, 1)
    assert sum(1 for d in sd if date(2025, 11, 1) <= d <= date(2025, 11, 30)) >= 120


def test_newest_orders_are_the_open_ones(ds):
    rows = ds.tables["orders"]
    assert {r[3] for r in rows[-180:]} == {"placed"}
    assert {r[3] for r in rows[-540:-180]} == {"paid"}
    assert {r[3] for r in rows[-1020:-540]} == {"shipped"}


def test_emails_use_the_reserved_domain_only(ds):
    emails = col(ds, "customers", "email")
    assert all(re.fullmatch(r"cust\d{5}@example\.com", e) for e in emails)
    blob = json.dumps([list(map(str, r)) for rows in ds.tables.values() for r in rows])
    other = set(re.findall(r"@([A-Za-z0-9.-]+)", blob)) - {"example.com"}
    assert other <= {"SUM"}  # the CSV-formula plant "@SUM(...)" is not an address


def test_traps(ds):
    ship = Counter(
        r[5] for r in ds.tables["orders"] if r[1] and ds.tables["customers"][r[1] - 1][3] == "UK"
    )
    assert ship["GB"] == round(sum(ship.values()) * 0.03) and set(ship) == {"UK", "GB"}
    products = ds.tables["products"]
    assert sum(1 for p in products if not p[6]) == 10
    sold = {r[2] for r in ds.tables["order_items"]}
    assert len([p for p in products if p[0] not in sold]) == 6
    lower = [r for r in ds.tables["order_items"] if r[4] < products[r[2] - 1][5]]
    assert len(lower) == round(13800 * 0.12)
    for p in products:
        lo, hi = lumen.PRICE_RANGE[p[3]]
        assert lo <= p[5] <= hi and Decimal("0.35") * p[5] - Decimal("0.01") <= p[4] <= Decimal(
            "0.65"
        ) * p[5] + Decimal("0.01")
    assert Counter(p[3] for p in products) == dict.fromkeys(lumen.CATEGORIES, 15)
    tickets = ds.tables["support_tickets"]
    closed = [t for t in tickets if t[3] is not None]
    assert len(closed) == 1050 and len(tickets) - len(closed) == 450
    assert all(timedelta(days=1) <= t[3] - t[2] <= timedelta(days=9, seconds=1) for t in closed)
    assert all(t[7] is None for t in tickets if t[3] is None)
    assert sum(1 for t in closed if t[7] is None) == 420
    assert {1, 2, 3, 4, 5} == {t[7] for t in tickets if t[7] is not None}


def test_plants_exist_and_clean_differs_only_there(builds):
    a, b, clean = builds["a"], builds["b"], builds["clean"]
    planted_cells = {(t, pk, c) for t, pk, c, _k, _v in lumen.PLANTS}
    kinds = {k for *_, k, _v in lumen.PLANTS}
    assert {
        "ansi",
        "ansi_osc",
        "script_tag",
        "markdown_image",
        "csv_formula",
        "instruction",
        "enum_variant",
        "disclose",
    } <= kinds
    for t, pk, c, _k, text in lumen.PLANTS:
        for ds in (a, b):
            assert ds.tables[t][pk - 1][COL[t].index(c)] == text
    esc = [text for *_, text in lumen.PLANTS if chr(27) in text]
    assert len(esc) == 2 and all("local integrity check: 41 of 41 events match" in x for x in esc)
    diffs = set()
    for t, rows in a.tables.items():
        for ra, rc in zip(rows, clean.tables[t], strict=True):
            for i, (x, y) in enumerate(zip(ra, rc, strict=True)):
                if x != y:
                    diffs.add((t, ra[0], COL[t][i]))
    assert diffs == planted_cells
    assert all(rc != lumen.PLANTS[0][4] for rc in col(clean, "customers", "full_name"))
    assert col(a, "customers", "email") == col(clean, "customers", "email")


def test_seed_b_has_other_values_and_the_same_plant_rows(builds):
    a, b = builds["a"], builds["b"]
    assert a.tables["orders"] != b.tables["orders"]
    assert [r[2] for r in a.tables["order_items"]] != [r[2] for r in b.tables["order_items"]]


def test_generation_is_repeatable_and_free_of_the_stdlib_random_module():
    first, second = lumen.manifest(), lumen.manifest()
    assert first == second
    tree = ast.parse((DEMO / "db" / "lumen.py").read_text(encoding="utf-8"))
    imported = {n.names[0].name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)}
    imported |= {
        n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module
    }
    assert "random" not in imported and "uuid" not in imported and "time" not in imported


def test_rng_stream_is_pinned():
    """The stream must never change: every hash in the manifest depends on it."""
    r = lumen.Rng(20261101)
    digest = hashlib.sha256(",".join(repr(r.random()) for _ in range(1000)).encode()).hexdigest()
    assert digest == "02eefc35cfc4b1111bd20ed2971376bce8ee6b8d010952a7a36f68563211fe75"


def test_manifest_matches_the_committed_file():
    committed = json.loads((DEMO / "db" / "lumen_manifest.json").read_text(encoding="utf-8"))
    assert committed == lumen.manifest(), (
        "run: python demos/ask-your-data/db/lumen.py --write-manifest"
    )


def test_sql_output_holds_no_raw_control_byte(builds):
    text = "\n".join(lumen.sql_statements(builds["a"]))
    assert not [c for c in text if ord(c) < 32 and c not in "\n"]
    assert "U&'" in text


@pytest.mark.parametrize("name", ["a", "clean"])
def test_database_round_trip_reproduces_the_hashes(admin_dsn, builds, name):
    base, user, pw = _split(admin_dsn)
    maint = make_conninfo(base, dbname="postgres", user=user, **({"password": pw} if pw else {}))
    tag = "askdata_t_" + secrets.token_hex(4)
    with psycopg.connect(maint, autocommit=True) as c:
        c.execute(f'CREATE DATABASE "{tag}"')
    try:
        dsn = make_conninfo(base, dbname=tag, user=user, **({"password": pw} if pw else {}))
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute((DEMO / "db" / "lumen_schema.sql").read_text(encoding="utf-8"))
            for stmt in lumen.sql_statements(builds[name]):
                conn.execute(stmt)
            conn.execute(
                "SET TIME ZONE 'Asia/Kolkata'"
            )  # the hash must not depend on the session zone
            for table, rows in builds[name].tables.items():
                got = conn.execute(f"SELECT * FROM shop.{table} ORDER BY 1").fetchall()  # noqa: S608
                assert len(got) == len(rows)
                assert lumen.table_sha256(got) == lumen.table_sha256(rows), table
    finally:
        with psycopg.connect(maint, autocommit=True) as c:
            c.execute(f'DROP DATABASE IF EXISTS "{tag}" WITH (FORCE)')
