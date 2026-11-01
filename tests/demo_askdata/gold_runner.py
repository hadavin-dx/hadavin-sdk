"""Test-side helpers: build the stand-in Lumen Goods database twice (two seeds) and run SELECTs for goldcheck.

The driver import lives here (tests), never in `demos/ask-your-data/data/goldcheck.py`.
"""

from __future__ import annotations

import importlib.util
import sys

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from .conftest import DEMO
from .lumen_standin import SCHEMA_SQL, build

TABLE_ORDER = [
    "customers",
    "products",
    "orders",
    "order_items",
    "payments",
    "refunds",
    "support_tickets",
]


def load_standin(conn: psycopg.Connection, seed: int) -> None:
    conn.execute(SCHEMA_SQL)
    data = build(seed)
    for table in TABLE_ORDER:
        rows = data[table]
        marks = ", ".join(["%s"] * len(rows[0]))
        with conn.cursor() as cur:
            cur.executemany(f"INSERT INTO shop.{table} VALUES ({marks})", rows)  # noqa: S608  # fixed table names


def make_runner(conn: psycopg.Connection):
    def run(sql: str) -> tuple[list[str], list[tuple]]:
        with conn.cursor() as cur:
            cur.execute(sql)  # type: ignore[arg-type]  # gold SQL is plain text from the data files
            return [d.name for d in cur.description], cur.fetchall()

    return run


def dsn_for(admin_dsn: str, dbname: str) -> str:
    parts = conninfo_to_dict(admin_dsn)
    parts["dbname"] = dbname
    return make_conninfo(**parts)


def load_goldcheck():
    """Import demos/ask-your-data/data/goldcheck.py by path (data/ is a folder of files, not a package)."""
    if "goldcheck" not in sys.modules:
        spec = importlib.util.spec_from_file_location("goldcheck", DEMO / "data" / "goldcheck.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["goldcheck"] = mod
        spec.loader.exec_module(mod)
    return sys.modules["goldcheck"]
