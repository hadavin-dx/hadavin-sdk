"""Test kit for the pipeline, ledger, meter and eval tests: a scripted model (the core FakeLLM over recordings built
by the fixture builder), two in-memory SQLite stand-ins for the seed databases, and a one-call pipeline factory.
No network, no key, no Postgres: the tests that need Postgres live in the other files.
"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from askdata import prompt as prompt_mod
from askdata.audit import AskAudit, local_dir_sink
from askdata.fixtures import ROUTE, Step, write_script
from askdata.ledger import QueryLedger
from askdata.meter import KillSwitch, Meter
from askdata.pgsource import PgError, RunResult
from askdata.pipeline import Pipeline, Settings

from hadavin_sdk.llm.fake import FakeLLM

PROMPT = prompt_mod.render(
    "Rules. Today is {{AS_OF}}. Functions: {{FUNCTIONS}}\n{{CATALOG}}\n{{GLOSSARY}}\n{{EXEMPLARS}}",
    as_of="2026-10-15", catalog=prompt_mod.catalog_text(), glossary="revenue = paid, shipped, delivered orders",
)  # fmt: skip

COUNT_ORDERS = "SELECT count(*) AS n FROM analytics.orders_v"
BY_STATUS = "SELECT status, count(*) AS n FROM analytics.orders_v GROUP BY status ORDER BY status"
TOP2 = "SELECT order_id, total_amount FROM analytics.orders_v ORDER BY total_amount DESC, order_id LIMIT 2"


def sqlite_db(seed: int) -> sqlite3.Connection:
    """A tiny stand-in for one seed database: the four exposed views as tables under the `analytics` name."""
    conn = sqlite3.connect(":memory:")
    conn.execute("ATTACH ':memory:' AS analytics")
    conn.execute(
        "CREATE TABLE analytics.customers_v (customer_id, full_name, country, signup_date)"
    )
    conn.execute(
        "CREATE TABLE analytics.products_v (product_id, product_name, category, unit_price)"
    )
    conn.execute(
        "CREATE TABLE analytics.orders_v (order_id, customer_id, order_date, status, total_amount)"
    )
    conn.execute(
        "CREATE TABLE analytics.order_items_v (order_item_id, order_id, product_id, quantity, unit_price, line_amount)"
    )
    statuses = ["paid", "shipped", "delivered", "cancelled"]
    for i in range(
        1, 11 + seed
    ):  # seed 1 has 11 orders, seed 2 has 12: counts differ, structure is the same
        conn.execute(
            "INSERT INTO analytics.orders_v VALUES (?, ?, '2026-01-01', ?, ?)",
            (i, 1 + i % 3, statuses[i % 4], 10 * i + seed),
        )
    for c in range(1, 4):
        conn.execute(
            "INSERT INTO analytics.customers_v VALUES (?, ?, 'US', '2025-01-01')",
            (c, f"Customer {c}"),
        )
    return conn


class SqliteExecutor:
    """Runs canonical SQL against a SQLite database as if it were `PgSource.run`."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.calls: list[str] = []

    def run(self, canonical_sql: str, *, sql_sha256: str | None = None, limits=None) -> RunResult:
        self.calls.append(canonical_sql)
        try:
            cur = self.conn.execute(canonical_sql)
        except sqlite3.OperationalError:
            raise PgError("42P01", "undefined") from None
        rows = [tuple(r) for r in cur.fetchall()]
        digest = hashlib.sha256(canonical_sql.encode()).hexdigest()
        return RunResult(
            [d[0] for d in cur.description],
            rows,
            False,
            hashlib.sha256(repr(rows).encode()).hexdigest(),
            digest,
            wire_sha256=digest[::-1],
        )


@dataclass
class Scripted:
    """An executor that returns or raises what it is told, in order, then falls back to `inner`."""

    inner: SqliteExecutor
    script: list = field(default_factory=list)
    calls: list[str] = field(default_factory=list)

    def run(self, canonical_sql: str, *, sql_sha256: str | None = None, limits=None) -> RunResult:
        self.calls.append(canonical_sql)
        if self.script:
            nxt = self.script.pop(0)
            if isinstance(nxt, Exception):
                raise nxt
            return nxt
        return self.inner.run(canonical_sql, sql_sha256=sql_sha256, limits=limits)


class Kit:
    """Everything one pipeline needs, rooted in `tmp`."""

    def __init__(
        self,
        tmp: Path,
        *,
        executor=None,
        settings: Settings | None = None,
        demo_cap: str = "8.00",
        sleep=lambda _s: None,
    ) -> None:
        self.tmp = Path(tmp)
        self.recorded = self.tmp / "recorded"
        self.recorded.mkdir(parents=True, exist_ok=True)
        self.meter = Meter(self.tmp / "meter.json")
        Meter.create(self.meter.path, total_cap="10.00", reserve="1.00", demo_cap=demo_cap)
        self.ledger = QueryLedger(self.tmp / "ledger.jsonl")
        self.sink = local_dir_sink(self.tmp / "audit")
        self.kill = KillSwitch(self.tmp / "kill.flag")
        self.llm = FakeLLM(self.recorded, {"sql_generate": ROUTE})
        self.db_a = SqliteExecutor(sqlite_db(1))
        self.scripted = Scripted(self.db_a)
        self.executor = executor or self.scripted
        self.pipeline = Pipeline(
            llm=self.llm, routes={"sql_generate": ROUTE}, executor=self.executor, audit=AskAudit(self.sink, principal="claimed:test"),
            ledger=self.ledger, meter=self.meter, kill=self.kill, prompt=PROMPT, config_hash="c" * 64,
            settings=settings or Settings(), sleep=sleep,
        )  # fmt: skip

    def fail(self, *errors: Exception) -> None:
        """The next executions raise these, in order."""
        self.scripted.script.extend(errors)

    def script(self, question: str, *steps: Step) -> None:
        write_script(self.recorded, PROMPT.text, question, list(steps))
