"""Mutants of the money meter and its memory spend ledger, for the contract tests ``tests/contracts/test_t1_meter_cap.py``
and ``tests/contracts/test_store_time_rules.py``. Same runner and judge as ``tests/stage_mutants.py``
(``tools/mutation_runner.py``): each mutant changes ONE thing in a temp copy of the package and a named test must fail
with an assertion message holding ``expect``. The tests run through ``tests/meter_memory_killers.py`` (the runner has no
conftest, so that file supplies the memory ``store`` fixture). Not collected by pytest. Run from the repo root:

    python tests/meter_mutants.py             # all mutants; exit 1 if any is not good
    python tests/meter_mutants.py L3          # only mutants whose name contains the text

The same tests run against the postgres store in ``tests/postgres_mutants.py`` (needs HADAVIN_TEST_PG_DSN).
The 50-callers-at-once tests are not here; they are a later change (see tests/contracts/test_t1_meter_cap.py).
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
KILLERS = "tests/meter_memory_killers.py"
LIM = "src/hadavin_sdk/limits.py"
MEM = "src/hadavin_sdk/store/memory.py"
MOD = "src/hadavin_sdk/models.py"
ADD_SPEND_FILTER = "for (a, d), v in self._spend.items()\n                if a == agent_id and (d.year, d.month) == (day.year, day.month)"  # only add_spend
SPEND_TOTALS_FILTER = "                    if a == agent_id and (d.year, d.month) == (day.year, day.month)"  # 20 spaces: only spend_totals
BLOCKED_READ = "day, month = self.store.spend_totals(agent_id, now().date())  # a read, no write"
CHARGE = "return self.store.add_spend(agent_id, now().date(), usd)"


def m(name, file, old, new, killer, expect):
    return Mutant(name, file, old, new, expect, test_file=KILLERS, only_test=killer)


M = [
    m(
        "L1 daily check is > instead of >= (one extra call at the exact cap)",
        LIM,
        "if day >= budget.daily:",
        "if day > budget.daily:",
        "test_a_cap_that_is_a_multiple_of_the_cost_is_never_overshot_when_one_at_a_time",
        "the call at the exact cap was let through",
    ),
    m(
        "L2 the daily check is gone",
        LIM,
        "if day >= budget.daily:",
        "if False:",
        "test_one_caller_at_a_time_admits_ceil_cap_over_cost_and_overshoots_by_less_than_one_call",
        "admitted 50 calls for cap",
    ),
    m(
        "L3 monthly check is > instead of >= (one extra call at the exact cap)",
        LIM,
        "if month >= budget.monthly:",
        "if month > budget.monthly:",
        "test_the_monthly_cap_binds_when_it_is_lower_than_the_daily_cap",
        "monthly cap 2.00: admitted 3",
    ),
    m(
        "L4 charge returns totals but records nothing",
        LIM,
        CHARGE,
        "return (usd, usd)",
        "test_a_charge_is_recorded_in_the_ledger",
        "charge returned totals but the ledger holds nothing",
    ),
    m(
        "L5 blocked also writes (a read adds spend)",
        LIM,
        BLOCKED_READ,
        "day, month = self.store.spend_totals(agent_id, now().date())\n"
        "        self.store.add_spend(agent_id, now().date(), Decimal('0.01'))",
        "test_reads_never_change_a_total",
        "reads changed a total",
    ),
    m(
        "L6 charge books the day one hour late",
        LIM,
        CHARGE,
        "return self.store.add_spend(agent_id, (now() + __import__('datetime').timedelta(hours=1)).date(), usd)",
        "test_a_charge_at_23_30_utc_is_booked_on_its_own_day",
        "a charge at 23:30 UTC is not on its own UTC day",
    ),
    m(
        "L7 blocked reads yesterday's bucket",
        LIM,
        BLOCKED_READ,
        "day, month = self.store.spend_totals(agent_id, (now() - __import__('datetime').timedelta(days=1)).date())",
        "test_the_daily_budget_is_read_for_today_not_yesterday",
        "today's full budget was not read",
    ),
    m(
        "L8 now() reads the machine's local wall clock, not UTC",
        MOD,
        "return datetime.now(UTC)",
        "return datetime.now()",
        "test_the_real_now_is_aware_utc_and_books_23_00_utc_on_the_10th_on_a_machine_in_ist",
        "now() is not aware UTC",
    ),
    m(
        "L9 a caller over both caps is told about the daily one only",
        LIM,
        "        if month >= budget.monthly:",
        "        elif month >= budget.monthly:",
        "test_both_budgets_over_their_caps_are_both_named",
        "a caller over both caps must see both reasons",
    ),
    m(
        "L10 the daily check fires half a dollar early (a cost that is not W is cut short)",
        LIM,
        "if day >= budget.daily:",
        "if day + __import__('decimal').Decimal('0.50') >= budget.daily:",
        "test_one_caller_at_a_time_admits_ceil_cap_over_cost_and_overshoots_by_less_than_one_call",
        "admitted 2 calls for cap 2.50",
    ),
    m(
        "L11 charge turns a negative cost into 0 (the flip the pin test must notice)",
        LIM,
        CHARGE,
        "return self.store.add_spend(agent_id, now().date(), max(usd, __import__('decimal').Decimal(0)))",
        "test_pin_today_a_negative_or_infinite_charge_is_booked_as_it_is",
        "the charge -1 was not booked as it is",
    ),
    m(
        "L12 charge turns a NaN cost into 0 (the flip the NaN pin must notice)",
        LIM,
        CHARGE,
        "return self.store.add_spend(agent_id, now().date(), usd if usd == usd else __import__('decimal').Decimal(0))",
        "test_pin_today_a_nan_charge_is_booked_and_then_every_check_raises",
        "PIN: a NaN charge was not booked",
    ),
    m(
        "L13 a daily budget of 0 means no daily limit",
        LIM,
        "if day >= budget.daily:",
        "if budget.daily and day >= budget.daily:",
        "test_a_budget_of_zero_blocks_the_first_call",
        "a daily budget of 0 let the first call through",
    ),
    m(
        "L14 a monthly budget of 0 means no monthly limit",
        LIM,
        "if month >= budget.monthly:",
        "if budget.monthly and month >= budget.monthly:",
        "test_a_budget_of_zero_blocks_the_first_call",
        "a monthly budget of 0 let the first call through",
    ),
    m(
        "S1 the ledger double counts a day",
        MEM,
        "self._spend[(agent_id, day)] += usd",
        "self._spend[(agent_id, day)] += usd + usd",
        "test_two_charges_on_one_day_add_up",
        "the first charge of a day was not booked once",
    ),
    m(
        "S2 the month total sums every month (spend_totals)",
        MEM,
        SPEND_TOTALS_FILTER,
        "                    if a == agent_id",
        "test_a_month_total_does_not_carry_over_31_days",
        "January's month total changed",
    ),
    m(
        "S3 the month total sums every agent (spend_totals)",
        MEM,
        SPEND_TOTALS_FILTER,
        "                    if (d.year, d.month) == (day.year, day.month)",
        "test_one_agent_never_sees_another_agents_spend",
        "spend_totals showed this agent's spend to another agent",
    ),
    m(
        "S4 the month total a charge returns sums every month (add_spend)",
        MEM,
        ADD_SPEND_FILTER,
        "for (a, d), v in self._spend.items()\n                if a == agent_id",
        "test_a_charge_returns_the_total_of_its_own_month_only",
        "charge 1 at 2026-02-01 returned",
    ),
    m(
        "S5 the month total a charge returns sums every agent (add_spend)",
        MEM,
        ADD_SPEND_FILTER,
        "for (a, d), v in self._spend.items()\n                if (d.year, d.month) == (day.year, day.month)",
        "test_a_charge_returns_only_its_own_agents_month_total",
        "add_spend returned another agent's spend",
    ),
    m(
        "S6 a charge replaces the day total instead of adding to it",
        MEM,
        "self._spend[(agent_id, day)] += usd",
        "self._spend[(agent_id, day)] = usd",
        "test_two_charges_on_one_day_add_up",
        "the day total of two charges on one day did not add up",
    ),
    m(
        "S7 the year is dropped from the month a charge returns (add_spend)",
        MEM,
        ADD_SPEND_FILTER,
        "for (a, d), v in self._spend.items()\n                if a == agent_id and d.month == day.month",
        "test_the_same_month_of_another_year_is_a_different_month",
        "a March of another year was added to the March of 2026",
    ),
    m(
        "S8 the year is dropped from the month a read returns (spend_totals)",
        MEM,
        SPEND_TOTALS_FILTER,
        "                    if a == agent_id and d.month == day.month",
        "test_the_same_month_of_another_year_is_a_different_month",
        "the March totals of other years leaked into",
    ),
]

if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in x.name for x in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)
    first_lines: dict[str, str] = {}

    def show(row):
        name, v, test_id, good = row
        print(
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:60]}]",
            flush=True,
        )
        if not good:
            print("      first line:", first_lines.get(name, "")[:150], flush=True)

    res = run_mutants(
        ROOT,
        M,
        [KILLERS],
        extra_dirs=("tests", "tools", "demos", "docs"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
