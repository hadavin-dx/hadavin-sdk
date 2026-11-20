"""Mutants of the spend reservations (step F-store): the ticket's mutants 1 to 22 (handover/core-b/tickets/F-store.md,
"Mutants", plus 20 of R3 and 21, 22 of review round 2), as far as they apply to the built code. Each reverts ONE
guard; the pinned test must fail, and for the reason named in ``expect``. Not collected by pytest.

Two lists, because the guards live in two places:

``M`` is run by ``tools/mutation_runner.py`` (a temp copy of the package per mutant, no DSN, no conftest). Its
killers need no database: the memory store's form of a guard, ``Limits.reserve`` / ``settle``, the amount helper and
the tick step. The runner starts pytest with ``--noconftest`` and the store contract tests take the ``store`` fixture
of ``tests/contracts/conftest.py``, so this file is ALSO the test file the runner's pytest child is given: when it is
imported (not run as a script) it defines ``store`` as the memory store and takes over the tests of
``tests/contracts/test_store_spend.py`` and ``tests/test_limits_reserve.py`` and the tests of
``tests/test_spend_reservations_pg.py`` that need no database, unchanged. A pinned id therefore reads
``tests/reserve_mutants::<test>``.

``HAND`` holds the PostgreSQL form of the guards (the SQL of ``store/postgres.py``, the session isolation of
``connect()``, the grant row). Their killers need a real PostgreSQL, so they are applied one at a time to THIS
working tree, the killer is run with the caller's HADAVIN_TEST_PG_DSN, and the file is put back byte for byte:

    uv run --all-extras --group test python tests/reserve_mutants.py                 # M; exit 1 if one is not good
    uv run --all-extras --group test python tests/reserve_mutants.py "M15"           # only names that hold the text
    HADAVIN_TEST_PG_DSN=<dsn> uv run --all-extras --group test python tests/reserve_mutants.py --hand
    HADAVIN_TEST_PG_DSN=<dsn> uv run --all-extras --group test python tests/reserve_mutants.py --hand "H5"

``--hand`` refuses to start when a target file has uncommitted changes, runs each killer on the clean tree first (it
must pass, or the kill means nothing) and restores the file in a ``finally``. Both modes end with the line
``N of N good; problems: [...]``.

``EQUIVALENT`` names forms of a ticket mutant that change no behaviour of the built code, with the reason; they are
printed and not run."""

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
SELF = "tests/reserve_mutants.py"
CONTRACT = "tests/contracts/test_store_spend.py"
T1 = "tests/contracts/test_t1_reserve_cap.py"
PGT = "tests/test_spend_reservations_pg.py"
SCHEMAQ = "tests/test_store_schema_qualified_pg.py"
MEM = "src/hadavin_sdk/store/memory.py"
PG = "src/hadavin_sdk/store/postgres.py"
PROTO = "src/hadavin_sdk/store/protocol.py"
LIM = "src/hadavin_sdk/limits.py"
TICK = "src/hadavin_sdk/runtime/tick.py"
MIG = "src/hadavin_sdk/store/migrate.py"
SQL11 = (
    "src/hadavin_sdk/store/migrations/0011_money_definer.sql"  # the SQL of the bookings (step 3)
)

if (
    __name__ != "__main__"
):  # imported by the runner's pytest child as its test file (see the module docstring)
    import pytest

    import tests.contracts.test_store_spend as _contract
    import tests.test_limits_reserve as _limits
    import tests.test_spend_reservations_pg as _pg
    from hadavin_sdk.store.memory import MemoryStore

    def _needs_a_database(fn):
        return any(m.name == "skipif" for m in getattr(fn, "pytestmark", []))

    for _mod in (_contract, _limits, _pg):
        for _name in dir(_mod):
            if _name.startswith("test_") and not _needs_a_database(getattr(_mod, _name)):
                assert _name not in globals(), f"two killers are called {_name}"
                globals()[_name] = getattr(_mod, _name)
    tomorrow = _contract.tomorrow

    @pytest.fixture
    def store():
        return MemoryStore()


NOT_RAISED = "DID NOT RAISE"

# --- killers (test function names; a pinned id may add the parameter in brackets) ------------------------------------
EXACT = "test_a_reserve_that_reaches_the_cap_exactly_passes"
OVER_DAY = "test_one_micro_dollar_over_the_day_cap_is_refused_with_which_day"
MONTH = "test_the_month_cap_binds_when_it_is_the_lower_one"
ZERO_BUDGET = "test_a_budget_of_zero_refuses_even_an_amount_of_zero"
REFUSED = "test_a_refused_reserve_leaves_the_totals_and_the_rows_unchanged"
SETTLE = "test_settle_lower_equal_and_higher_books_the_actual_amount"
DUP_ID = "test_a_duplicate_id_is_stale_state_and_is_booked_once"
SCHEMAQ_TEST = (
    "test_the_money_function_calls_name_their_schema_so_a_temporary_function_never_answers"
)
TWICE = "test_settle_twice_the_first_wins_and_the_second_changes_nothing"
NEXT_DAY = "test_a_settle_on_the_next_day_moves_only_the_day_and_month_of_the_reserve"
CLOCK = "test_a_settle_when_the_clock_says_the_next_day_moves_only_the_reserved_day"
EXPIRE_OLD = "test_expire_closes_old_rows_only_and_the_counters_do_not_move"
EXPIRE_ZERO = "test_expire_with_age_zero_closes_every_open_row_with_the_totals_unchanged"
YOUNG = "test_expire_leaves_young_rows_alone"
LATE_LOW = "test_expired_then_settled_lower_settles_the_row_and_keeps_the_counters"
PURGE_OPEN = "test_purge_with_a_cutoff_in_the_future_still_keeps_open_rows"
RUN_COST = "test_settle_adds_the_actual_amount_to_the_cost_of_a_run_that_exists"
HELPER = "test_the_amount_helper_refuses_every_hostile_amount"
HELPER_TYPE = "test_the_amount_helper_returns_a_good_amount_unchanged"
STORE_DOWN = "test_a_store_that_raises_in_reserve_spend_is_limits_unavailable"
STOP = "test_the_stop_state_refuses_with_kill_switch_and_nothing_is_booked"
BAD_AMOUNT = "test_a_hostile_amount_is_bad_amount_and_the_store_is_never_asked"
UNKNOWN = "test_an_unknown_agent_is_a_key_error_even_while_the_stop_state_is_on"
OVERSHOOT = "test_an_overshoot_is_booked_in_full_returned_and_audited_once"
AUDIT_DOWN = "test_a_raising_audit_sink_does_not_make_settle_raise"
LAST_STEP = "test_the_step_is_the_last_one_and_comes_after_audit_drain"
TWO_AGENTS = "test_the_expiry_age_with_two_agents_is_the_larger_of_their_quiet_times"
FLOOR = "test_the_expiry_age_is_never_below_the_default"
PURGE_LINE = "test_the_evidence_purge_also_purges_closed_reservations_before_the_hook"
T1_CAP3 = "test_t1_cap_3_and_worst_1_grants_exactly_3_of_50"
T1_MONTH = "test_t1_the_month_cap_binds_when_it_is_the_lower_one"
T1_RR = "test_t1_with_a_role_default_of_repeatable_read_still_grants_exactly_3"
WAITED = "test_a_settle_that_waits_for_an_uncommitted_expiry_sees_the_row_as_expired"
RACE = "test_settle_racing_the_expire_step_never_lowers_a_booking"
NO_DELETE = "test_the_runtime_login_cannot_delete_or_truncate_reservations"
C3 = "test_c3_a_fault_at_the_month_update_in_reserve_changes_nothing"


def mutant(name, file, old, new, killer, expect, crash=""):
    return Mutant(
        name,
        file,
        old,
        new,
        expect,
        allow_crash=bool(crash),
        crash_type=crash,
        test_file=SELF,
        only_test=killer.split("[")[0],
        pinned=SELF[:-3] + "::" + killer,
    )


# --- M: run by the mutation runner, no database ----------------------------------------------------------------------
M_DAY = "            if not (booked < day_cap and booked + usd <= day_cap):"
M_MONTH = "            if not (month < month_cap and month + usd <= month_cap):"
M_BOOK = "            self._spend[(row.agent_id, row.day)] += booked - row.reserved_usd"
M_BOOKED = '            booked = max(actual_usd, row.reserved_usd) if row.status == "expired" else actual_usd'
M_EXPIRE_LOOP = (
    "            for r in old:  # a status change only: the counters keep the worst case\n"
)
L_OVER = "        over = max(Decimal(0), (row.settled_usd or Decimal(0)) - row.reserved_usd)"

M = [
    mutant("M1 memory: the day cap clause is removed", MEM, M_DAY, "            if False:",
        OVER_DAY, NOT_RAISED),
    mutant("M2 memory: the month cap clause is removed", MEM, M_MONTH, "            if False:",
        MONTH, NOT_RAISED),
    mutant("M3 memory: <= becomes < on the day cap", MEM, "booked + usd <= day_cap", "booked + usd < day_cap",
        EXACT, "day cap reached", crash="SpendCapExceeded"),
    mutant("M3 memory: <= becomes < on the month cap", MEM, "month + usd <= month_cap", "month + usd < month_cap",
        MONTH, "month cap reached", crash="SpendCapExceeded"),
    mutant("M4 memory: booked < day_cap is removed", MEM, "booked < day_cap and ", "",
        ZERO_BUDGET, NOT_RAISED),
    mutant("M4 memory: month < month_cap is removed", MEM, "month < month_cap and ", "",
        ZERO_BUDGET, NOT_RAISED),
    mutant("M7 memory: a settled row is claimed again", MEM,
        '            if row.status == "settled":\n                return row, False\n', "",
        TWICE + "[0.40]", "assert True is False"),
    mutant("M8 memory: the delta sign is flipped", MEM, M_BOOK,
        "            self._spend[(row.agent_id, row.day)] += row.reserved_usd - booked",
        SETTLE + "[0]", "== (Decimal('0'), Decimal('0'))"),
    mutant("M9 memory: settle books on today's day", MEM, M_BOOK,
        "            self._spend[(row.agent_id, now().date())] += booked - row.reserved_usd",
        NEXT_DAY + "[0.40]", "assert (Decimal('1.0"),
    mutant("M11 memory: expire sets settled_usd to 0", MEM,
        '"settled_usd": r.reserved_usd, "closed_at": at', '"settled_usd": Decimal(0), "closed_at": at',
        EXPIRE_OLD, "'expired'"),
    mutant("M11 memory: expire lowers the counters", MEM, M_EXPIRE_LOOP,
        M_EXPIRE_LOOP + "                self._spend[(r.agent_id, r.day)] -= r.reserved_usd\n",
        EXPIRE_ZERO, "assert (Decimal('0.0"),
    mutant("M12 memory: expire ignores the age", MEM,
        'if r.status == "open" and r.created_at <= cutoff', 'if r.status == "open"',
        YOUNG, "assert 1 == 0"),
    mutant("M13 memory: the counters go down after expiry", MEM, M_BOOK,
        "            self._spend[(row.agent_id, row.day)] += actual_usd - row.reserved_usd",
        LATE_LOW + "[0.40]", "assert (Decimal('0.4"),
    mutant("M14 memory: the actual amount is clamped to the reserved one", MEM, M_BOOKED,
        M_BOOKED.replace("else actual_usd", "else min(actual_usd, row.reserved_usd)"),
        SETTLE + "[1.75]", "assert ('settled', D"),
    mutant("M19 memory: purge deletes open rows", MEM,
        'if r.status != "open" and r.closed_at is not None and r.closed_at < before',
        'if r.status == "open" or (r.closed_at is not None and r.closed_at < before)',
        PURGE_OPEN, "assert 2 == 1"),
    mutant("M20 memory: the run cost update is removed", MEM,
        "            if run is not None:  # a missing run row moves only the counters", "            if False:",
        RUN_COST, "Decimal('0.40')"),
    mutant("M21 memory: the booked amount ignores the prior status", MEM, M_BOOKED,
        "            booked = actual_usd",
        LATE_LOW + "[0.40]", "assert ('settled', D"),
    mutant("M9b amount helper: the exponent bounds are removed", PROTO,
        "        or not -MAX_SPEND_DECIMALS <= usd.as_tuple().exponent <= MAX_SPEND_EXPONENT\n", "",
        HELPER + "[huge_exponent_zero]", NOT_RAISED),
    mutant("M9c amount helper: a Decimal subclass is accepted", PROTO,
        "type(usd) is not Decimal", "not isinstance(usd, Decimal)",
        HELPER_TYPE, NOT_RAISED),
    mutant("M15 Limits.reserve returns an id after a store error", LIM,
        '            raise SpendRefused("limits_unavailable") from None', "            return rid",
        STORE_DOWN + "[key_error]", NOT_RAISED),
    mutant("M16 Limits.reserve skips the stop state", LIM,
        "            if self.store.get_kill_switch().on:", "            if False:",
        STOP, NOT_RAISED),
    mutant("M16b Limits.reserve does not check the amount", LIM,
        '            raise SpendRefused("bad_amount") from None', "            pass",
        BAD_AMOUNT + "[bool]", "limits_unavailable"),
    mutant("M16c Limits.reserve looks the agent up after the stop state", LIM,
        "        budget = self.registry.agents[agent_id].budget_usd\n        try:\n",
        "        try:\n            budget = self.registry.agents[agent_id].budget_usd\n",
        UNKNOWN, "limits_unavailable", crash="SpendRefused"),
    mutant("M16d Limits.settle audits a replay again", LIM,
        "        if applied and over > 0:", "        if over > 0:",
        OVERSHOOT, "assert 4 == 1"),
    mutant("M16e Limits.settle takes the overshoot from the request, not the stored row", LIM, L_OVER,
        "        over = max(Decimal(0), actual_usd - row.reserved_usd)",
        OVERSHOOT, "Decimal('0.90')"),
    mutant("M16f Limits.settle lets an audit failure through", LIM,
        "            except Exception as exc:  # noqa: BLE001 - the booking is done; an audit failure must not undo the reply",
        "            except ZeroDivisionError as exc:",
        AUDIT_DOWN, "audit down", crash="RuntimeError"),
    mutant("M18 the tick step row is removed", TICK,
        '    TickStep("expire_reservations", 0, expire_reservations),\n', "",
        LAST_STEP, "['sweep', 'reconcile'"),
    mutant("M18b the expiry age takes the smallest stuck-run age", TICK,
        "longest = max((stuck_after_s(app, a) for a in app.registry.agents), default=0)",
        "longest = min((stuck_after_s(app, a) for a in app.registry.agents), default=0)",
        TWO_AGENTS, "assert 3600 == 24060"),
    mutant("M18c the expiry age is the bare default", TICK,
        "    return max(defaults.RESERVATION_EXPIRE_S, math.ceil(longest))",
        "    return defaults.RESERVATION_EXPIRE_S",
        TWO_AGENTS, "assert 3600 == 24060"),
    mutant("M18d the expiry age may fall below the default", TICK,
        "    return max(defaults.RESERVATION_EXPIRE_S, math.ceil(longest))",
        "    return math.ceil(longest) or defaults.RESERVATION_EXPIRE_S",
        FLOOR, "== 3600"),
    mutant("M18e the purge line is removed from the evidence purge", TICK,
        "    reservations = store.purge_spend_reservations(\n"
        "        ctx.now - timedelta(days=keep.held_tool_calls_max_days)\n    )\n",
        "    reservations = 0\n",
        PURGE_LINE, "assert {"),
]  # fmt: skip


# --- HAND: applied to the working tree, killers need PostgreSQL ------------------------------------------------------
@dataclass(frozen=True)
class Hand:
    name: str
    file: str
    old: str
    new: str
    node: str  # the pytest node id of the killer
    expect: str  # must be in the killer's output


S_DAY = "WHERE s.agent_id = p_agent AND s.day = p_day AND s.usd < p_day_cap AND s.usd + p_usd <= p_day_cap;"
S_MONTH = "WHERE m.agent_id = p_agent AND m.month = v_month AND m.usd < p_month_cap AND m.usd + p_usd <= p_month_cap;"
S_DAY_BLOCK = (
    f"    UPDATE spend s SET usd = s.usd + p_usd\n     {S_DAY}\n"  # noqa: S608
    "    IF NOT FOUND THEN\n        RAISE EXCEPTION 'day' USING ERRCODE = 'HD001';\n    END IF;\n"
)
S_CHECK_THEN_BOOK = (
    f"    PERFORM 1 FROM spend s {S_DAY}\n"  # noqa: S608
    "    IF NOT FOUND THEN\n        RAISE EXCEPTION 'day' USING ERRCODE = 'HD001';\n    END IF;\n"
    "    UPDATE spend s SET usd = s.usd + p_usd WHERE s.agent_id = p_agent AND s.day = p_day;\n"
)
S_DELTA = "    v_delta := rec.settled_usd - rec.reserved_usd;"
S_AGE = "AND r.created_at <= pg_catalog.clock_timestamp() - pg_catalog.make_interval(secs => p_age_s::double precision);"
S_CLAIM_STATUS = " AND r.status IN ('open', 'expired')\n       FOR UPDATE;"
S_DAYROW = "WHERE s.agent_id = rec.agent_id AND s.day = rec.day;"
S_MONTHROW = "m.month = pg_catalog.date_trunc('month', rec.day)::date;"
S_ISOLATION = '    conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL READ COMMITTED")\n'
TOTALS = "assert _totals(store) == (D(actual), D(actual))"
PGP = "[postgres]"

HAND = [
    Hand("H1 the day cap clause is removed", SQL11, S_DAY, "WHERE s.agent_id = p_agent AND s.day = p_day;",
        f"{T1}::{T1_CAP3}", "{'granted': 50}"),
    Hand("H2 the month cap clause is removed", SQL11, S_MONTH, "WHERE m.agent_id = p_agent AND m.month = v_month;",
        f"{T1}::{T1_MONTH}", "{'granted': 50}"),
    Hand("H3 <= becomes < on the day cap", SQL11, S_DAY, S_DAY.replace("<= p_day_cap", "< p_day_cap"),
        f"{CONTRACT}::{EXACT}{PGP}", "SpendCapExceeded: day cap reached"),
    Hand("H3 <= becomes < on the month cap", SQL11, S_MONTH, S_MONTH.replace("<= p_month_cap", "< p_month_cap"),
        f"{CONTRACT}::{MONTH}{PGP}", "SpendCapExceeded: month cap reached"),
    Hand("H4 usd < cap is removed on the day", SQL11, S_DAY, S_DAY.replace("AND s.usd < p_day_cap ", ""),
        f"{CONTRACT}::{ZERO_BUDGET}{PGP}", NOT_RAISED),
    Hand("H4 usd < cap is removed on the month", SQL11, S_MONTH, S_MONTH.replace("AND m.usd < p_month_cap ", ""),
        f"{CONTRACT}::{ZERO_BUDGET}{PGP}", NOT_RAISED),
    Hand("H5 the cap is checked by a SELECT, then an unconditional UPDATE books", SQL11, S_DAY_BLOCK, S_CHECK_THEN_BOOK,
        f"{T1}::{T1_CAP3}", "'granted': "),
    Hand("H7 the settle claim has no status test", SQL11, S_CLAIM_STATUS, "\n       FOR UPDATE;",
        f"{CONTRACT}::{TWICE}[postgres-0.40]", "assert applied_again is False"),
    Hand("H8 the delta sign is flipped", SQL11, S_DELTA, "    v_delta := rec.reserved_usd - rec.settled_usd;",
        f"{CONTRACT}::{SETTLE}[postgres-0]", TOTALS),
    Hand("H9 settle books on today's day", SQL11, S_DAYROW, "WHERE s.agent_id = rec.agent_id AND s.day = current_date;",
        f"{CONTRACT}::{CLOCK}[postgres-0.40]", "spend counter row missing"),
    Hand("H9 (no row for today) settle books on today's day", SQL11, S_DAYROW,
        "WHERE s.agent_id = rec.agent_id AND s.day = current_date;",
        f"{CONTRACT}::{NEXT_DAY}[postgres-0.40]", "spend counter row missing"),
    Hand("H10 the month key is taken from today", SQL11, S_MONTHROW,
        "m.month = pg_catalog.date_trunc('month', current_date)::date;",
        f"{CONTRACT}::{CLOCK}[postgres-0.40]", "spend counter row missing"),
    Hand("H11 expire sets settled_usd to 0", SQL11, "SET status = 'expired', settled_usd = r.reserved_usd,",
        "SET status = 'expired', settled_usd = 0,",
        f"{CONTRACT}::{EXPIRE_ZERO}{PGP}", "CheckViolation"),
    Hand("H12 expire ignores the age", SQL11, S_AGE, "AND TRUE;",
        f"{CONTRACT}::{YOUNG}{PGP}", "assert 1 == 0"),
    Hand("H13 the counters go down after expiry", SQL11, S_DELTA, "    v_delta := p_actual - rec.reserved_usd;",
        f"{CONTRACT}::{LATE_LOW}[postgres-0.40]", 'assert _totals(store) == (D("1.00"), D("1.00"))'),
    Hand("H14 the actual amount is clamped to the reserved one", SQL11, "ELSE p_actual END",
        "ELSE LEAST(p_actual, r.reserved_usd) END",
        f"{CONTRACT}::{SETTLE}[postgres-1.75]", "Decimal('1.75')"),
    Hand("H17 the runtime grant gains DELETE", MIG, '"spend_reservations": Grant("table", _RW, purge="DELETE"',
        '"spend_reservations": Grant("table", _RW + ", DELETE", purge="DELETE"',
        f"{PGT}::{NO_DELETE}", NOT_RAISED),
    Hand("H19 purge deletes open rows", SQL11, "WHERE r.status = 'settled' AND r.closed_at < p_before;",
        "WHERE r.status = 'open' OR r.closed_at < p_before;",
        f"{CONTRACT}::{PURGE_OPEN}{PGP}", "assert 2 == 1"),
    Hand("H20 the runs update is removed", SQL11, "    IF rec.run_id IS NOT NULL THEN  -- the real",
        "    IF FALSE THEN  -- the real",
        f"{CONTRACT}::{RUN_COST}{PGP}", 'assert _cost(store, run_id) == D("0.40")'),
    Hand("H21 the booked amount ignores the prior status", SQL11, "CASE WHEN v_was = 'expired' THEN",
        "CASE WHEN FALSE THEN",
        f"{PGT}::{WAITED}[0.25-1.00]", "Decimal('0.25')"),
    Hand("H21 (contract form) the booked amount ignores the prior status", SQL11, "CASE WHEN v_was = 'expired' THEN",
        "CASE WHEN FALSE THEN",
        f"{CONTRACT}::{LATE_LOW}[postgres-0.40]", "Decimal('0.40')"),
    Hand("H21 (race form) the booked amount ignores the prior status", SQL11, "CASE WHEN v_was = 'expired' THEN",
        "CASE WHEN FALSE THEN",
        f"{PGT}::{RACE}[0.25]", "expired=1"),
    Hand("H21b the claim reads the status without the row lock", SQL11, S_CLAIM_STATUS,
        " AND r.status IN ('open', 'expired');",
        f"{PGT}::{WAITED}[0.25-1.00]", "Decimal('0.25')"),
    Hand("H22 the session isolation SET is removed", PG, S_ISOLATION, "",
        f"{T1}::{T1_RR}", "SerializationFailure"),
    Hand("H23 the money call is not schema-qualified", PG,
        "sql.Identifier(self._schema), sql.Identifier(function), sql.SQL(placeholders)",
        "sql.Identifier(function), sql.Identifier(function), sql.SQL(placeholders)",
        f"{SCHEMAQ}::{SCHEMAQ_TEST}", "decoy was called"),
    Hand("H24 a duplicate reservation id is not mapped to StaleState", PG, 'if code == "23505":',
        'if code == "00000":',
        f"{CONTRACT}::{DUP_ID}{PGP}", "UniqueViolation"),
    Hand("H25 a cap refusal is not mapped to SpendCapExceeded", PG, 'if code == "HD001":',
        'if code == "00000":',
        f"{CONTRACT}::{REFUSED}{PGP}", "OperationalError"),
]  # fmt: skip

# Forms of a ticket mutant that change nothing in the built code: (name, why).
EQUIVALENT = [
    ("19 (plain form) purge: `status <> 'open' AND` removed from the DELETE",
        "an open row has closed_at NULL (table CHECK), so `closed_at < before` alone never matches it: see H19, M19"),
    ("10 (memory form) the month key taken from today",
        "the memory store keeps no month counter: the month is the sum over the days, so only M9 applies"),
    ("6 (memory form) the reservation insert outside the transaction",
        "the memory store checks both caps before it writes anything, under one lock: there is no partial state"),
    ("5 (memory form) check by SELECT, then an unconditional UPDATE",
        "one process, one lock around the check and the booking: the two steps cannot interleave"),
    ("22 (memory form) the session isolation SET removed", "the memory store has no session"),
    ("6 (PostgreSQL form, H6) the reservation insert outside the store's transaction",
        "since step 3 the insert, both bookings and the cap checks are ONE function call, atomic in the database "
        "even without the store's `transaction()`: a fault inside the function is the constraint form of "
        + C3 + "[constraint] (the owner's CHECK), which changes nothing in the tables"),
    ("17 (runner form) the runtime grant gains DELETE", "a grant is only real in a database: see H17"),
]  # fmt: skip


def _killer(node: str) -> tuple[int, str]:
    done = subprocess.run(  # noqa: S603 - this interpreter, a fixed test id
        [sys.executable, "-m", "pytest", node, "-q", "-x", "-p", "no:cacheprovider"],
        cwd=ROOT, capture_output=True, text=True, timeout=900, check=False,
    )  # fmt: skip
    return done.returncode, done.stdout + done.stderr


def run_by_hand(only: list[str]) -> list[tuple[str, str]]:
    """Apply each HAND mutant to the working tree, run its killer, restore. Returns (name, verdict) per mutant."""
    chosen = [m for m in HAND if not only or any(text in m.name for text in only)]
    dirty = subprocess.run(  # noqa: S603 - fixed arguments
        ["git", "status", "--porcelain", "--", *sorted({m.file for m in chosen})],  # noqa: S607 - git from PATH
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    if dirty.strip():
        raise SystemExit("refused: a target file has uncommitted changes:\n" + dirty)
    results, clean = [], {}
    for m in chosen:
        path = ROOT / m.file
        before = path.read_bytes()
        text = before.decode("utf-8")
        if m.node not in clean:
            clean[m.node] = _killer(m.node)[0] == 0
        if not clean[m.node]:
            verdict = "BASELINE FAILS (the killer fails on the clean tree)"
        elif text.count(m.old) != 1:
            verdict = f"NOT APPLIED (the old text is in the file {text.count(m.old)} times)"
        else:
            try:
                path.write_bytes(text.replace(m.old, m.new).encode("utf-8"))
                code, out = _killer(m.node)
            finally:
                path.write_bytes(before)
            if code == 0:
                verdict = "SURVIVED"
            elif m.expect not in out:
                verdict = f"FAILED FOR ANOTHER REASON (no {m.expect!r} in the output)"
                if os.environ.get("MUTANT_LINES"):
                    verdict += (
                        "\n" + "\n".join(x for x in out.splitlines() if x.startswith("E "))[:1500]
                    )
            else:
                verdict = "KILLED"
        results.append((m.name, verdict))
        print(
            f"{'ok ' if verdict == 'KILLED' else 'BAD'} {verdict:8} | {m.name} | {m.file} | {m.node}",
            flush=True,
        )
    return results


def _equivalent() -> None:
    for name, why in EQUIVALENT:
        print(f"equivalent (not run): {name}: {why}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--hand"]:
        if not os.environ.get("HADAVIN_TEST_PG_DSN"):
            print("HADAVIN_TEST_PG_DSN is not set: the killers would be skipped, nothing was run")
            sys.exit(1)
        done = run_by_hand(args[1:])
        _equivalent()
        bad = [n for n, v in done if v != "KILLED"]
        print(f"{len(done) - len(bad)} of {len(done)} good; problems: {bad}")
        sys.exit(1 if bad else 0)
    if args and not any(o in m.name for m in M for o in args):
        print(f"no mutant name contains any of {args}; nothing was run", file=sys.stderr)
        sys.exit(2)
    first_lines: dict[str, str] = {}

    def show(row):
        name, v, test_id, good = row
        print(
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:90]}]",
            flush=True,
        )
        if not good or os.environ.get("MUTANT_LINES"):
            print("      first line:", first_lines.get(name, "")[:200], flush=True)

    res = run_mutants(
        ROOT, M, [SELF], extra_dirs=("tests", "tools"), only=args, on_result=show,
        first_lines=first_lines, timeout=300,
    )  # fmt: skip
    for m in HAND:
        print(f"by hand (--hand, needs PostgreSQL): {m.name} -> {m.node.split('::')[-1]}")
    _equivalent()
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
