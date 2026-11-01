"""The ONE place for the tunable numbers of the demo, with their documented defaults.

Anything a client or an operator may reasonably change lives here as a validated model and is set in the askdata config
(`smoke:`, `sealed:`, `meter:` blocks). Code reads these models. The scan in tests/demo_askdata/test_demo_literals.py
lists what is NOT here and why: structural constants (exit codes, unicode ranges, validator rule limits, schema
bounds), the dataset generators db/lumen.py and db/seed.py, and the core SDK's own constants. Secrets are not here
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


class Runtime(_Strict):
    """Operational numbers that were literals in the demo modules. The demo's tunable defaults live here."""

    # questions and the pipeline
    max_attempts: int = Field(
        3, ge=1, le=3
    )  # model attempts per question (the prompt describes at most three)
    max_question_chars: int = Field(500, gt=0)
    # requests ONE call of the recorded (offline) model may send: it never retries inside a call
    recorded_llm_requests: int = Field(1, ge=1)
    injection_threshold: float = Field(
        0.05, gt=0, le=1
    )  # inert for the 0.0/1.0 regex detector (see README)
    transient_backoff_s: float = Field(1.0, ge=0)
    stored_question_chars: int = Field(500, gt=0)  # what a ledger line keeps of the question
    ledger_attempts_kept: int = Field(6, ge=1)
    ledger_assumptions_kept: int = Field(20, ge=1)
    # the database connection and its watchdog
    statement_timeout_s: float = Field(10.0, gt=0)
    max_statement_timeout_s: float = Field(300.0, gt=0)  # upper bound the config may set
    max_rows: int = Field(1000, gt=0)
    max_bytes: int = Field(1_000_000, gt=0)
    fetch_batch: int = Field(200, gt=0)
    connect_timeout_s: int = Field(5, gt=0)
    keepalives_idle_s: int = Field(10, gt=0)
    keepalives_interval_s: int = Field(5, gt=0)
    keepalives_count: int = Field(3, gt=0)
    watchdog_join_s: float = Field(5.0, gt=0)  # how long to wait for the cancel thread
    # the read-only login (db/roles.sql gets these as psql variables; the script has no numbers of its own)
    role_connection_limit: int = Field(5, gt=0)
    role_statement_timeout_s: int = Field(15, gt=0, le=999)
    role_lock_timeout_s: int = Field(1, gt=0, le=999)
    role_idle_in_transaction_timeout_s: int = Field(15, gt=0, le=999)
    # evaluation and locks
    max_duration_ms: int = Field(15_000, gt=0)  # a question slower than this is not "bounded"
    human_read_fraction: float = Field(0.2, gt=0, le=1)
    human_read_salt: str = "human-read-v1"  # makes the human-read sample deterministic
    lock_poll_s: float = Field(0.01, gt=0)  # how often a waiting process re-tries an OS lock
    lock_replace_attempts: int = Field(
        5, ge=1
    )  # os.replace of lock.json is retried (Windows readers)
    lock_replace_wait_s: float = Field(0.05, ge=0)
    connect_retry_wait_s: float = Field(
        0.25, ge=0
    )  # pause before the one reconnect of a dropped connection
    lock_wait_s: float = Field(5.0, gt=0)  # how long to wait for an OS lock (meter file, lock.json)
    email_pattern: str = (
        r"cust\d{5}@example\.com"  # the synthetic e-mail shape a leak check looks for
    )


RUNTIME = Runtime()


def role_psql_vars() -> dict[str, str]:
    """The psql variables db/roles.sql requires, from RUNTIME (the one home of the numbers)."""
    return {
        "ro_connection_limit": str(RUNTIME.role_connection_limit),
        "ro_statement_timeout": f"{RUNTIME.role_statement_timeout_s}s",
        "ro_lock_timeout": f"{RUNTIME.role_lock_timeout_s}s",
        "ro_idle_timeout": f"{RUNTIME.role_idle_in_transaction_timeout_s}s",
    }
