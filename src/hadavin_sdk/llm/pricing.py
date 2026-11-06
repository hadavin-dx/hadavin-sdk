"""What a call costs, exactly, from the counts a provider reported and the route's prices (P4a-1).

`cost_usd` never rounds: the one upward rounding (`models.round_cost_up`) is done once, at the producers of a `Reply`.
It refuses what cannot be priced: a cache class with a count (cache prices are not built), and an input count of zero
on a route that charges for input (a real prompt is never free). The route is read by attribute, so this module
imports no `config`.
"""

from __future__ import annotations

import decimal
from decimal import Decimal
from typing import Any

from hadavin_sdk.llm.protocol import UnpricedUsage, UsageMissing
from hadavin_sdk.models import ToolCall, Usage


def check_priceable(usage: Usage) -> None:
    """A non-zero cache class is `UnpricedUsage` (this core never asks a provider to use a cache, so a count is a
    surprise: it is refused, not priced)."""
    if usage.cache_write_tokens != 0:
        raise UnpricedUsage("cache_write_tokens")
    if usage.cache_read_tokens != 0:
        raise UnpricedUsage("cache_read_tokens")


def check_input_plausible(usage: Usage, route: Any) -> None:
    """An input count of zero on a route with a positive input price cannot be true. The count is tested BEFORE the
    price, so a NaN price is never ordered when the count is above 0."""
    if usage.input_tokens == 0 and route.input_usd_per_mtok > 0:
        raise UsageMissing("implausible_zero", "input_tokens")


def check_output_plausible(usage: Usage, text: str, calls: list[ToolCall]) -> None:
    """A reported output of 0 is kept only for an empty reply (no text, no tool call): a refusal, an empty answer or a
    blocked prompt. A reply with text or a tool call cannot have used no output tokens."""
    if usage.output_tokens == 0 and (text.strip() or calls):
        raise UsageMissing("implausible_zero", "output_tokens")


def cost_usd(usage: Usage, route: Any) -> Decimal:
    """Exact USD for one call; never rounds. Order: cache class, then zero input, then the sum."""
    check_priceable(usage)
    check_input_plausible(usage, route)
    ctx = decimal.Context(prec=60, traps=[decimal.Inexact, decimal.InvalidOperation])
    try:
        return ctx.divide(
            ctx.add(
                ctx.multiply(Decimal(usage.input_tokens), route.input_usd_per_mtok),
                ctx.multiply(Decimal(usage.output_tokens), route.output_usd_per_mtok),
            ),
            Decimal(1_000_000),
        )
    except decimal.DecimalException as exc:
        raise UsageMissing("invalid") from exc
