"""Reservations: the pure part. The rows and the transaction live in the Store (memory, postgres); this module holds the
validation and the limit decision both stores call, and the start-up check for an ordered limits table.

A reservation holds a share of a limit while something waits for a person (a proposal to move money, to send, to
delete). Without a bound, a looping agent that files many valid proposals fills the limit with holds nobody approved.
`decide` bounds the open holds per scope (for example per customer or per ticket), per actor (the sender or
requester) and in total per unit (a currency or a quota), from the store's own rows.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime

from hadavin_sdk.models import Reservation, ReservationLimits

OPEN_LIMIT = "OPEN_LIMIT"
UNIT_UNKNOWN = "UNIT_UNKNOWN"
KEY_CONFLICT = "KEY_CONFLICT"
MAX_FIELD = 200
MAX_SCOPES = 50


class ReservationError(ValueError):
    """The input is malformed (not a limit being hit). `code` names the first broken rule."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _text(v: object) -> bool:
    return isinstance(v, str) and 0 < len(v) <= MAX_FIELD and v.isprintable()


def validate(res: Reservation, since: datetime) -> None:
    for name in ("tenant", "key", "actor", "unit"):
        if not _text(getattr(res, name)):
            raise ReservationError(f"BAD_{name.upper()}")
    if (
        not (0 < len(res.scopes) <= MAX_SCOPES)
        or not all(_text(s) for s in res.scopes)
        or len(set(res.scopes)) != len(res.scopes)
    ):
        raise ReservationError("BAD_SCOPES")
    if isinstance(res.amount, bool) or not isinstance(res.amount, int) or res.amount <= 0:
        raise ReservationError("BAD_AMOUNT")
    if res.created_at.tzinfo is None or since.tzinfo is None:
        raise ReservationError("NAIVE_TIME")
    if since > res.created_at:
        raise ReservationError("SINCE_AFTER_CREATED")


def decide(
    n_scope: int, n_actor: int, held: int, res: Reservation, limits: ReservationLimits
) -> str | None:
    """None when the new hold fits. `n_scope`/`n_actor`/`held` count the OTHER open holds (younger than the window)."""
    if res.unit not in limits.unit_caps:
        return UNIT_UNKNOWN
    if (
        n_scope >= limits.max_per_scope
        or n_actor >= limits.max_per_actor
        or held + res.amount > limits.unit_caps[res.unit]
    ):
        return OPEN_LIMIT
    return None


def same_content(a: Reservation, b: Reservation) -> bool:
    return (sorted(a.scopes), a.actor, a.unit, a.amount) == (
        sorted(b.scopes),
        b.actor,
        b.unit,
        b.amount,
    )


def check_ordered_limits(
    tables: Mapping[str, Mapping[str, int]],
    order: Sequence[str],
    *,
    strict_before: Sequence[str] = (),
) -> None:
    """Each table (for example one per currency) holds the named fields as positive ints (not bool) in the order
    given: `a <= b <= c`, and strictly `<` before every field named in `strict_before`. ValueError names the first break."""
    for name, row in tables.items():
        if set(row) < set(order):
            raise ValueError(f"{name}: missing {sorted(set(order) - set(row))}")
        vals = [row[f] for f in order]
        if any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in vals):
            raise ValueError(f"{name}: every limit must be a positive int")
        for (fa, a), (fb, b) in zip(
            zip(order, vals, strict=True), zip(order[1:], vals[1:], strict=True), strict=False
        ):
            if a > b or (a == b and fb in strict_before):
                raise ValueError(f"{name}: need {fa} {'<' if fb in strict_before else '<='} {fb}")
