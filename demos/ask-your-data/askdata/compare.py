"""Result comparison rules (design 12.3, amendments A-16). Pure functions, no database, no model.

* Rows are a multiset; column order is ignored (a column permutation is searched); column names are ignored.
* Numbers are rounded half-even to the item's scale (default 2 decimals; a gold item may list a scale per gold column).
* Timestamps compare by value in UTC. NULL equals NULL only.
* Row order matters only when `order_matters` (top-N); then a tie at the cut makes the item unusable (`tie_at_cut`).
* An extra or missing column is NOT correct (stricter than many published numbers).
* A candidate must match on BOTH seed databases (`agrees`).
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

DEFAULT_SCALE = 2
NULL = "\x00null"


def norm(value: object, scale: int = DEFAULT_SCALE) -> object:
    """A hashable, comparable form of one cell."""
    if value is None:
        return NULL
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float | Decimal):
        d = Decimal(str(value)) if not isinstance(value, Decimal) else value
        try:
            return ("n", str(d.quantize(Decimal(1).scaleb(-scale), rounding=ROUND_HALF_EVEN)))
        except InvalidOperation:  # inf, nan or a value too large to round
            return ("n", str(d))
    if isinstance(value, datetime):
        v = value if value.tzinfo else value.replace(tzinfo=UTC)
        return ("t", v.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"))
    if isinstance(value, date):
        return ("d", value.isoformat())
    return ("s", str(value))


def _scales(scale: list[int] | None, width: int) -> list[int]:
    return [(scale[i] if scale and i < len(scale) else DEFAULT_SCALE) for i in range(width)]


@dataclass(frozen=True)
class Match:
    ok: bool
    reason: str  # "match", "row_count", "column_count", "no_column_mapping", "row_order"


def _rows(rows: list[tuple], perm: tuple[int, ...], scales: list[int]) -> list[tuple]:
    return [tuple(norm(r[p], s) for p, s in zip(perm, scales, strict=True)) for r in rows]


def match(
    gold: list[tuple],
    cand: list[tuple],
    *,
    order_matters: bool = False,
    scale: list[int] | None = None,
    gold_width: int | None = None,
    cand_width: int | None = None,
) -> Match:
    """Does the candidate result equal the gold result? Widths are passed for empty results."""
    gw = gold_width if gold_width is not None else (len(gold[0]) if gold else 0)
    cw = cand_width if cand_width is not None else (len(cand[0]) if cand else 0)
    if gw != cw:
        return Match(False, "column_count")
    if len(gold) != len(cand):
        return Match(False, "row_count")
    if not gold:
        return Match(True, "match")
    sc = _scales(scale, gw)
    g = _rows(gold, tuple(range(gw)), sc)
    g_sig = [Counter(r[i] for r in g) for i in range(gw)]
    # candidate columns that can stand in for each gold column (same multiset of values at that column's scale)
    options = [
        [j for j in range(gw) if Counter(norm(r[j], sc[i]) for r in cand) == g_sig[i]]
        for i in range(gw)
    ]
    saw_perm = False
    for perm in itertools.islice(itertools.product(*options), 5000):  # bounded: many equal columns
        if len(set(perm)) != gw:
            continue
        saw_perm = True
        c = _rows(cand, perm, sc)
        if (c == g) if order_matters else (Counter(c) == Counter(g)):
            return Match(True, "match")
    if saw_perm and not order_matters:
        return Match(False, "no_column_mapping")
    if saw_perm:  # same rows in another order
        return Match(False, "row_order")
    return Match(False, "no_column_mapping")


def agrees(a: Match, b: Match) -> bool:
    """Second-seed agreement: correct only if it matches on both seed databases."""
    return a.ok and b.ok


def tie_at_cut(order_keys: list[object], n: int) -> bool:
    """True if the sort key at row N equals the key at row N+1 (a top-N cut that splits a tie). `order_keys` are
    the keys of the UNLIMITED gold result, in order. Such an item must be rewritten."""
    if n <= 0 or len(order_keys) <= n:
        return False
    return norm(order_keys[n - 1], 6) == norm(order_keys[n], 6)


def matches_interpretation(
    cand: list[tuple],
    interpretations: dict[str, list[tuple]],
    *,
    order_matters: bool = False,
    scale: list[int] | None = None,
) -> str | None:
    """The id of the first interpretation whose result equals the candidate's, else None."""
    for iid, rows in interpretations.items():
        if match(rows, cand, order_matters=order_matters, scale=scale).ok:
            return iid
    return None


def result_hash(rows: list[tuple], *, ordered: bool, scale: list[int] | None = None) -> str:
    """Canonical SHA-256 of a result (design 10): numbers with their scale, UTC timestamps, one NULL token, column
    order as returned, rows in returned order when the SQL has an ORDER BY, else sorted by their text."""
    width = len(rows[0]) if rows else 0
    sc = _scales(scale, width)
    lines = [
        json.dumps(
            [norm(v, s) for v, s in zip(r, sc, strict=True)], ensure_ascii=True, sort_keys=True
        )
        for r in rows
    ]
    if not ordered:
        lines.sort()
    h = hashlib.sha256()
    for line in lines:
        h.update(line.encode("ascii") + b"\n")
    return h.hexdigest()
