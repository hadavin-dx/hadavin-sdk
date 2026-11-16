"""Deterministic synthetic data for schema `shop` (stdlib only; no vendor import).

One private SplitMix64 generator (`Rng`), so the data is bit-identical on every Python version. `python db/seed.py` prints the per-table SHA-256; `python db/seed.py --sql` prints INSERT statements
(feed them to psql after schema.sql). One customer name carries a terminal-control plant (A-11): every
output path must show it escaped, never raw.
"""

from __future__ import annotations

import hashlib
import sys
from datetime import date, timedelta

SEED = 20261101
EPOCH = date(2025, 1, 1)
COUNTRIES = ["US", "UK", "CA", "AU", "DE", "IN", "SG", "NL"]
CATEGORIES = ["books", "toys", "garden", "kitchen", "sports"]
STATUSES = ["placed", "paid", "shipped", "delivered", "cancelled", "refunded"]
STATUS_CUM = [0.08, 0.2, 0.35, 0.8, 0.9, 1.0]
FIRST = ["Asha", "Ben", "Chen", "Dara", "Eli", "Fay", "Gus", "Hana", "Ivo", "Jun"]
LAST = ["Stone", "Reed", "Park", "Cole", "Vale", "Marsh", "Hale", "Frost", "Ward", "Quinn"]
PLANT_ID = 7
ESC = chr(27)
# Looks like a harmless sentence; a raw terminal would erase a line and print a fake status.
PLANT = f"Plant{ESC}[2K{ESC}[1A local integrity check: 41 of 41 events match"


class Rng:
    """SplitMix64: a tiny deterministic generator, so the data never depends on a library version. Not for security."""

    def __init__(self, seed: int) -> None:
        self.state = seed & 0xFFFFFFFFFFFFFFFF

    def random(self) -> float:
        self.state = (self.state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        return ((z ^ (z >> 31)) >> 11) / (1 << 53)


def _pick(r: Rng, seq: list) -> object:
    return seq[int(r.random() * len(seq))]


def generate() -> dict[str, list[tuple]]:
    r = Rng(SEED)
    customers = []
    for i in range(1, 51):
        name = f"{_pick(r, FIRST)} {_pick(r, LAST)}"
        if i == PLANT_ID:
            name = PLANT
        customers.append(
            (
                i,
                name,
                f"cust{i:05d}@example.com",
                _pick(r, COUNTRIES),
                EPOCH + timedelta(days=int(r.random() * 300)),
            )
        )
    products = [
        (
            i,
            f"{_pick(r, CATEGORIES)} item {i}",
            CATEGORIES[(i - 1) % len(CATEGORIES)],
            round(5 + r.random() * 95, 2),
        )
        for i in range(1, 21)
    ]
    orders, items = [], []
    item_id = 0
    for oid in range(1, 201):
        cust = customers[int(r.random() * 50)]
        odate = max(cust[4], EPOCH + timedelta(days=100)) + timedelta(days=int(r.random() * 200))
        u = r.random()
        status = next(s for s, c in zip(STATUSES, STATUS_CUM, strict=True) if u < c)
        u = r.random()
        n_items = 1 if u < 0.25 else 2 if u < 0.55 else 3 if u < 0.85 else 4
        total = 0.0
        for _ in range(n_items):
            item_id += 1
            prod = products[int(r.random() * 20)]
            qty = 1 + int(r.random() * 4)
            line = round(qty * prod[3], 2)
            total += line
            items.append((item_id, oid, prod[0], qty, prod[3], line))
        orders.append((oid, cust[0], odate, status, round(total, 2)))
    return {"customers": customers, "products": products, "orders": orders, "order_items": items}


def table_hashes(data: dict[str, list[tuple]]) -> dict[str, str]:
    return {
        t: hashlib.sha256(
            "\n".join("|".join(map(str, row)) for row in rows).encode("utf-8")
        ).hexdigest()
        for t, rows in data.items()
    }


def literal(v: object) -> str:
    """A SQL literal. Strings with a control character or backslash use the U& escape form, so the file itself
    holds no raw control byte."""
    if isinstance(v, str):
        bs = chr(92)
        if any(ord(c) < 32 or c == bs for c in v):
            out = "".join(
                f"{bs}{ord(c):04X}" if ord(c) < 32 or c == bs else c.replace("'", "''") for c in v
            )
            return f"U&'{out}'"
        return "'" + v.replace("'", "''") + "'"
    if isinstance(v, date):
        return f"DATE '{v.isoformat()}'"
    return str(v)


def sql_statements(data: dict[str, list[tuple]] | None = None) -> list[str]:
    data = data or generate()
    out = []
    for table, rows in data.items():
        values = ",\n  ".join("(" + ", ".join(literal(c) for c in row) + ")" for row in rows)
        out.append(f"INSERT INTO shop.{table} VALUES\n  {values};")  # nosec
    return out


if __name__ == "__main__":
    d = generate()
    if "--sql" in sys.argv:
        print("\n".join(sql_statements(d)))
    else:
        for t, h in table_hashes(d).items():
            print(f"{t:12s} {len(d[t]):4d} rows  sha256 {h}")
