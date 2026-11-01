"""The ONE place for the tunable numbers of the demo, with their documented defaults.

Anything a client or an operator may reasonably change lives here as a validated model and is set in the askdata config
(`smoke:`, `sealed:`, `meter:` blocks). Code reads these models; it holds no copy of the numbers. Secrets are not here
(they come from the core secrets kind by configured name), and neither are environment names, regions, model ids or
machine paths (those are config entries without defaults, or the `route:` block).
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Smoke(_Strict):
    """The live smoke run's abort rule (amendments A-03, step 1). Money in US dollars."""

    max_cost_per_question_usd: Decimal = Field(
        Decimal("0.035"), gt=0
    )  # strictly more aborts, from min_questions on
    hard_cap_per_question_usd: Decimal = Field(
        Decimal("0.35"), gt=0
    )  # ONE question above this aborts from call 1
    max_schema_violation_rate: Decimal = Field(Decimal("0.10"), ge=0, le=1)
    min_questions: int = Field(5, ge=1)  # the two rate rules wait for this many questions


class Sealed(_Strict):
    """Budget and count rules of the sealed test set; written into lock.json at freeze."""

    first_run_min_remaining_usd: Decimal = Field(Decimal("3.00"), ge=0)
    second_look_min_remaining_usd: Decimal = Field(Decimal("1.80"), ge=0)
    max_second_looks: int = Field(2, ge=0)
    # the pass/fail gate on the confident-wrong rate (one-sided 95 % upper bound), fixed at freeze
    green_max_upper: Decimal = Field(Decimal("0.10"), gt=0, le=1)
    amber_max_upper: Decimal = Field(Decimal("0.15"), gt=0, le=1)


class MeterLimits(_Strict):
    """Caps of the shared spend meter (`meter --init`) and its timing rules."""

    total_cap_usd: Decimal = Field(Decimal("10.00"), gt=0)
    reserve_usd: Decimal = Field(Decimal("1.00"), ge=0)
    demo_cap_usd: Decimal = Field(Decimal("8.00"), gt=0)
    stale_open_minutes: int = Field(
        10, gt=0
    )  # an unsettled reservation older than this is a crashed call
    max_external_age_hours: int = Field(
        24, gt=0
    )  # external_usd typed in longer ago than this blocks a live step
