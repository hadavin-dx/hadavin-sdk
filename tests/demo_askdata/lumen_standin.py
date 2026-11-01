"""A small STAND-IN for the Lumen Goods seed, used only to execute the gold SQL twice over two databases.

The real seeds A and B belong to phase P1 (design section 11) and had not merged when this was written. This module
follows the design's table and column names, the trap list (11.4) and the status quotas (11.3), but it is smaller
(about 1,500 orders) and is NOT the dataset the demo ships. A gold item that passes here has been *executed* only on
this stand-in; `goldcheck.py` runs the same checks against the real seed databases once they exist.

Standard library only. Seeds are for reproducibility inside this test, not a cross-version promise.
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal

AS_OF = date(2026, 10, 15)
COUNTRIES = [("US", 45), ("UK", 18), ("CA", 12), ("AU", 10), ("DE", 8), ("IN", 7)]
CATEGORIES = ["Home", "Kitchen", "Outdoor", "Office", "Toys", "Beauty", "Fitness", "Pets"]
PRICE_RANGE = {"Home": (12, 180), "Kitchen": (8, 140), "Outdoor": (20, 320), "Office": (5, 250),
               "Toys": (6, 90), "Beauty": (4, 70), "Fitness": (10, 200), "Pets": (5, 80)}  # fmt: skip
STATUSES = [
    ("delivered", 62),
    ("shipped", 8),
    ("paid", 6),
    ("placed", 3),
    ("cancelled", 8),
    ("refunded", 13),
]
CHANNELS = [("web", 55), ("mobile", 30), ("marketplace", 15)]
REASONS = [("damaged", 30), ("late", 25), ("wrong_item", 20), ("changed_mind", 20), ("fraud", 5)]
N_CUSTOMERS, N_PRODUCTS, N_ORDERS, N_TICKETS = 240, 40, 1500, 300
NEVER_SOLD = (38, 39, 40)

SCHEMA_SQL = """
CREATE SCHEMA shop; CREATE SCHEMA analytics;
CREATE TABLE shop.customers (customer_id integer PRIMARY KEY, full_name text, email text, country text,
  signup_date date, segment text, marketing_opt_in boolean);
CREATE TABLE shop.products (product_id integer PRIMARY KEY, sku text, name text, category text,
  unit_cost numeric(10,2), list_price numeric(10,2), is_active boolean, created_at timestamp);
CREATE TABLE shop.orders (order_id integer PRIMARY KEY, customer_id integer, order_ts timestamp, status text,
  channel text, shipping_country text, discount_pct integer, notes text, fl_cd char(1));
CREATE TABLE shop.order_items (order_item_id integer PRIMARY KEY, order_id integer, product_id integer,
  quantity integer, unit_price numeric(10,2));
CREATE TABLE shop.payments (payment_id integer PRIMARY KEY, order_id integer, method text, amount numeric(12,2),
  paid_at timestamp, status text);
CREATE TABLE shop.refunds (refund_id integer PRIMARY KEY, order_id integer, refunded_at timestamp,
  amount numeric(12,2), reason text);
CREATE TABLE shop.support_tickets (ticket_id integer PRIMARY KEY, customer_id integer, opened_at timestamp,
  closed_at timestamp, category text, priority text, subject text, csat_score integer);
CREATE VIEW analytics.customers_v AS SELECT customer_id, full_name, country, signup_date, segment,
  marketing_opt_in FROM shop.customers;
CREATE VIEW analytics.products_v AS SELECT product_id, sku, name, category, unit_cost, list_price, is_active,
  created_at FROM shop.products;
CREATE VIEW analytics.orders_v AS SELECT order_id, customer_id, order_ts, status, channel, shipping_country,
  discount_pct, notes, fl_cd FROM shop.orders;
CREATE VIEW analytics.order_items_v AS SELECT order_item_id, order_id, product_id, quantity, unit_price
  FROM shop.order_items;
CREATE VIEW analytics.payments_v AS SELECT payment_id, order_id, method, amount, paid_at, status
  FROM shop.payments;
CREATE VIEW analytics.refunds_v AS SELECT refund_id, order_id, refunded_at, amount, reason FROM shop.refunds;
CREATE VIEW analytics.support_tickets_v AS SELECT ticket_id, customer_id, opened_at, closed_at, category,
  priority, subject, csat_score FROM shop.support_tickets;
"""


def _pick(rnd: random.Random, weighted: list[tuple[str, int]]) -> str:
    x = rnd.random() * sum(w for _, w in weighted)
    for value, w in weighted:
        x -= w
        if x < 0:
            return value
    return weighted[-1][0]


def _money(x: Decimal | float) -> Decimal:
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def build(seed: int) -> dict[str, list[tuple]]:
    rnd = random.Random(seed)  # noqa: S311  # test data, not security
    start = date(2025, 1, 1)
    customers = []
    for i in range(1, N_CUSTOMERS + 1):
        signup = start + timedelta(days=int(rnd.random() * 639))
        customers.append((i, f"Customer {i}", f"cust{i:05d}@example.com", _pick(rnd, COUNTRIES), signup,
                          "business" if rnd.random() < 0.15 else "consumer", rnd.random() < 0.5))  # fmt: skip
    products = []
    for i in range(1, N_PRODUCTS + 1):
        cat = CATEGORIES[(i - 1) % len(CATEGORIES)]
        lo, hi = PRICE_RANGE[cat]
        price = _money(lo + rnd.random() * (hi - lo))
        cost = _money(price * Decimal(str(round(0.35 + rnd.random() * 0.30, 4))))
        products.append((i, f"LG-{i:04d}", f"{cat} item {i}", cat, cost, price, i % 10 != 0,
                         datetime.combine(date(2024, 12, 1), datetime.min.time()) + timedelta(days=i)))  # fmt: skip
    ordering = [c for c in customers if c[0] % 10 != 0]  # every tenth customer never orders
    heavy = ordering[: len(ordering) // 5]
    orders, items, payments, refunds = [], [], [], []
    item_id = pay_id = ref_id = 0
    sellable = [p for p in products if p[0] not in NEVER_SOLD]
    failed_budget = 0
    for oid in range(1, N_ORDERS + 1):
        pool = heavy if rnd.random() < 0.6 else ordering
        cust = pool[int(rnd.random() * len(pool))]
        span = (AS_OF - cust[4]).days
        ts = datetime.combine(cust[4], datetime.min.time()) + timedelta(
            days=int(rnd.random() * (span + 1)), seconds=int(rnd.random() * 86400)
        )
        ts = min(ts, datetime.combine(AS_OF, datetime.min.time()) + timedelta(seconds=86399))
        status = _pick(rnd, STATUSES)
        ship = cust[3] if rnd.random() < 0.9 else _pick(rnd, COUNTRIES)
        if ship == "UK" and rnd.random() < 0.03:
            ship = "GB"
        discount = (
            0
            if rnd.random() < 0.7
            else int(_pick(rnd, [("5", 1), ("10", 1), ("15", 1), ("20", 1)]))
        )
        fl = _pick(rnd, [("N", 92), ("R", 5), ("F", 3)])
        orders.append((oid, cust[0], ts, status, _pick(rnd, CHANNELS), ship, discount, None, fl))
        n_items = int(_pick(rnd, [("1", 30), ("2", 32), ("3", 22), ("4", 10), ("5", 6)]))
        total = Decimal(0)
        for _ in range(n_items):
            item_id += 1
            prod = sellable[int(rnd.random() * len(sellable))]
            price = (
                prod[5]
                if rnd.random() >= 0.12
                else _money(prod[5] * Decimal(str(round(1 - (0.05 + rnd.random() * 0.10), 4))))
            )
            qty = 1 + int(rnd.random() * 5)
            total += price * qty
            items.append((item_id, oid, prod[0], qty, price))
        paid_total = _money(total * (Decimal(100 - discount) / Decimal(100)))
        method = _pick(rnd, [("card", 60), ("paypal", 25), ("bank_transfer", 15)])
        if status in ("paid", "shipped", "delivered", "refunded"):
            pay_id += 1
            payments.append(
                (pay_id, oid, method, paid_total, ts + timedelta(minutes=5), "captured")
            )
        if status == "placed" or (status == "cancelled" and failed_budget < 60):
            pay_id += 1
            failed_budget += status == "cancelled"
            payments.append((pay_id, oid, method, paid_total, ts + timedelta(minutes=5), "failed"))
        if status == "refunded":
            pay_id += 1
            ref_id += 1
            when = min(
                ts + timedelta(days=3 + int(rnd.random() * 17)),
                datetime.combine(AS_OF, datetime.min.time()),
            )
            payments.append((pay_id, oid, method, paid_total, when, "refunded"))
            refunds.append((ref_id, oid, when, paid_total, _pick(rnd, REASONS)))
        elif status == "delivered" and rnd.random() < 0.07:
            ref_id += 1
            when = min(
                ts + timedelta(days=5 + int(rnd.random() * 20)),
                datetime.combine(AS_OF, datetime.min.time()),
            )
            part = _money(paid_total * Decimal(str(round(0.10 + rnd.random() * 0.50, 4))))
            refunds.append((ref_id, oid, when, part, _pick(rnd, REASONS)))
    tickets = []
    for tid in range(1, N_TICKETS + 1):
        cust = customers[int(rnd.random() * N_CUSTOMERS)]
        opened = datetime.combine(cust[4], datetime.min.time()) + timedelta(
            seconds=int(rnd.random() * (AS_OF - cust[4]).days * 86400)
        )
        closed = csat = None
        if rnd.random() < 0.70:
            closed = opened + timedelta(
                days=1 + int(rnd.random() * 9), seconds=int(rnd.random() * 20000)
            )
            closed = min(
                closed, datetime.combine(AS_OF, datetime.min.time()) + timedelta(seconds=86399)
            )
            if closed <= opened:
                closed = opened + timedelta(days=1)
            csat = None if rnd.random() < 0.4 else 1 + int(rnd.random() * 5)
        tickets.append((tid, cust[0], opened, closed, _pick(rnd, [("billing", 1), ("shipping", 1), ("product", 1), ("account", 1)]),
                        _pick(rnd, [("low", 4), ("medium", 3), ("high", 2), ("urgent", 1)]), f"Ticket {tid}", csat))  # fmt: skip
    return {"customers": customers, "products": products, "orders": orders, "order_items": items,
            "payments": payments, "refunds": refunds, "support_tickets": tickets}  # fmt: skip
