"""Mutants of the money meter and its spend ledger, for tests T1 (``tests/test_t1_meter_cap.py``) and T2
(``tests/test_t2_ledger_replay.py``). Same runner and judge as ``tests/stage_mutants.py`` (``tools/mutation_runner.py``);
each mutant changes ONE thing in a temp copy of the package and a named test must fail with a message holding ``expect``.
Not collected by pytest. Run from the repo root:

    python tests/meter_mutants.py             # all mutants; exit 1 if any is not good
    python tests/meter_mutants.py L3          # only mutants whose name contains the text

The 50-parallel tests (``tests/test_t1_meter_parallel.py``) are NOT in this run: they fail on the unmutated code (a
real finding, see the T1 docstring), and the runner refuses a baseline that fails.
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
CAP = "tests/test_t1_meter_cap.py"
LED = "tests/test_t2_ledger_replay.py"
LIM = "src/hadavin_sdk/limits.py"
MEM = "src/hadavin_sdk/store/memory.py"
ADD_SPEND_FILTER = "for (a, d), v in self._spend.items()\n                if a == agent_id and (d.year, d.month) == (day.year, day.month)"  # only add_spend
SPEND_TOTALS_FILTER = "                    if a == agent_id and (d.year, d.month) == (day.year, day.month)"  # 20 spaces: only spend_totals


def m(name, file, old, new, test_file, killer, expect):
    return Mutant(name, file, old, new, expect, test_file=test_file, only_test=killer)


M = [
    m(
        "L1 daily check is > instead of >= (one extra call at the exact cap)",
        LIM,
        "if day >= budget.daily:",
        "if day > budget.daily:",
        CAP,
        "test_a_cap_that_is_a_multiple_of_the_cost_is_never_overshot_when_one_at_a_time",
        "assert 4 == 3",
    ),
    m(
        "L2 the daily check is gone",
        LIM,
        "if day >= budget.daily:",
        "if False:",
        CAP,
        "test_one_caller_at_a_time_admits_ceil_cap_over_cost_and_overshoots_by_less_than_one_call",
        "admitted 50",
    ),
    m(
        "L3 monthly check is > instead of >= (one extra call at the exact cap)",
        LIM,
        "if month >= budget.monthly:",
        "if month > budget.monthly:",
        CAP,
        "test_the_monthly_cap_binds_when_it_is_lower_than_the_daily_cap",
        "assert 3 == 2",
    ),
    m(
        "L4 charge returns totals but records nothing",
        LIM,
        "return self.store.add_spend(agent_id, now().date(), usd)",
        "return (usd, usd)",
        CAP,
        "test_one_caller_at_a_time_admits_ceil_cap_over_cost_and_overshoots_by_less_than_one_call",
        "admitted 50",
    ),
    m(
        "L5 blocked also writes (a read adds spend)",
        LIM,
        "day, month = self.store.spend_totals(agent_id, now().date())  # a read, no write",
        "day, month = self.store.spend_totals(agent_id, now().date())\n"
        "        self.store.add_spend(agent_id, now().date(), Decimal('0.01'))",
        LED,
        "test_reads_never_change_a_total_and_a_replay_gives_the_same_totals",
        "assert {",
    ),
    m(
        "L6 charge books the day one hour late",
        LIM,
        "return self.store.add_spend(agent_id, now().date(), usd)",
        "return self.store.add_spend(agent_id, (now() + __import__('datetime').timedelta(hours=1)).date(), usd)",
        LED,
        "test_every_charge_lands_in_its_own_day_and_month_exactly_once",
        "read at",
    ),
    m(
        "L7 blocked reads yesterday's bucket",
        LIM,
        "day, month = self.store.spend_totals(agent_id, now().date())  # a read, no write",
        "day, month = self.store.spend_totals(agent_id, (now() - __import__('datetime').timedelta(days=1)).date())",
        LED,
        "test_the_daily_budget_stops_at_the_cap_and_frees_at_utc_midnight",
        "assert [] == ['daily_budget']",
    ),
    m(
        "S1 the ledger double counts a day",
        MEM,
        "self._spend[(agent_id, day)] += usd",
        "self._spend[(agent_id, day)] += usd + usd",
        LED,
        "test_every_charge_lands_in_its_own_day_and_month_exactly_once",
        "charge 0",
    ),
    m(
        "S2 the month total sums every month (spend_totals)",
        MEM,
        SPEND_TOTALS_FILTER,
        "                    if a == agent_id",
        LED,
        "test_a_month_total_does_not_carry_over_31_days",
        "assert",
    ),
    m(
        "S3 the month total sums every agent (spend_totals)",
        MEM,
        SPEND_TOTALS_FILTER,
        "                    if (d.year, d.month) == (day.year, day.month)",
        LED,
        "test_one_agent_never_sees_another_agents_spend",
        "assert",
    ),
    m(
        "S4 the month total a charge returns sums every month (add_spend)",
        MEM,
        ADD_SPEND_FILTER,
        "for (a, d), v in self._spend.items()\n                if a == agent_id",
        LED,
        "test_every_charge_lands_in_its_own_day_and_month_exactly_once",
        "charge",
    ),
    m(
        "S5 the month total a charge returns sums every agent (add_spend)",
        MEM,
        ADD_SPEND_FILTER,
        "for (a, d), v in self._spend.items()\n                if (d.year, d.month) == (day.year, day.month)",
        LED,
        "test_a_charge_returns_only_its_own_agents_month_total",
        "assert",
    ),
    m(
        "S6 a charge replaces the day total instead of adding to it",
        MEM,
        "self._spend[(agent_id, day)] += usd",
        "self._spend[(agent_id, day)] = usd",
        LED,
        "test_every_charge_lands_in_its_own_day_and_month_exactly_once",
        "read at",
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
        ROOT, M, [CAP, LED], extra_dirs=("tests", "tools", "demos", "docs"),
        only=only, on_result=show, first_lines=first_lines,
    )  # fmt: skip
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
