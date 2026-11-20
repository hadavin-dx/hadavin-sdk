"""Mutants of the price constraint (step C): the 20 mutants of the ticket's mutation plan and of the by-hand kill
table, run by ``tools/mutation_runner.py``.

Each mutant reverts ONE guard of ``config.py`` in a temp copy of the package; the pinned test of
``tests/test_price_constraint.py`` must be the one that fails first, and its first failing line must hold ``expect``.
No database is needed. Not collected by pytest in an ordinary run (the file name is not a test file name). Run from
the repo root:

    uv run --all-extras --group test python tests/price_mutants.py          # all; exit 1 if any is not good
    uv run --all-extras --group test python tests/price_mutants.py M10      # only names that hold the text

How the killers reach the runner. The runner starts pytest with ``--noconftest``, and the killers need the ``cfg_dir``
fixture of ``tests/conftest.py``, so ``tests/test_price_constraint.py`` cannot be handed to it directly: its unmutated
baseline would fail on a missing fixture. This file is therefore ALSO the test file the runner's pytest child is
given: when it is imported (not run as a script) it names ``tests.conftest`` as a plugin (the copy inside the
runner's snapshot, loaded by name, no file in a parent folder) and takes over every test and fixture of
``tests/test_price_constraint.py`` unchanged. A pinned id therefore reads ``tests/price_mutants::<test>``; the function
is the one defined in ``tests/test_price_constraint.py``.

Three mutants (M6c, M7, M9) make a config that must LOAD be refused. No test asserts on such a load, so their
killer ends in an exception and not in a failed assertion: they are marked ``allow_crash``. The first failing line
the runner reads is pydantic's ``ValidationError: 1 validation error for Config`` (the cause of the ``ConfigError``),
so for these three the class name and that text are checked, not which refusal it was.

``HOLES`` names a mutant that no test of the file kills; it is printed and not run. M12 in ``M`` is the form of it
that the tests do kill (the order reversed)."""

import os
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
SELF = "tests/price_mutants.py"
CFG = "src/hadavin_sdk/config.py"

if (
    __name__ != "__main__"
):  # imported by the runner's pytest child as its test file (see the module docstring)
    import tests.test_price_constraint as _killers

    pytest_plugins = ("tests.conftest",)
    globals().update(
        {n: getattr(_killers, n) for n in dir(_killers) if n.startswith("test_") or n == "today"}
    )

IN, OUT = "input_usd_per_mtok", "output_usd_per_mtok"
E2 = "test_e2_zero_refused_for_a_real_kind_in_demo"
E3_SPARE = "test_e3_zero_on_a_route_no_agent_uses_is_refused"
E3_JUDGE = "test_e3_zero_on_a_judge_route_is_refused"
E4 = "test_e4_fake_in_pilot_with_zero_is_refused_beside_the_other_refusals"
E5_ZERO = "test_e5_zero_refused_for_a_real_kind_in_pilot_and_prod"
E5_DATE = "test_e5_date_required_in_pilot_and_prod"
E6_LOAD = "test_e6_today_and_old_dates_load"
E6_FUTURE = "test_e6_future_date_refused_in_every_stage"
E7 = "test_e7_prices_at_the_bounds_load"
H1 = "test_h1_e7_bad_price_refused_for_fake_in_demo"
H3 = "test_h3_all_zero_fields_in_one_error_sorted_by_route"
H4 = "test_h4_only_a_plain_date_is_read"
H4_OBJECT = "test_h4_a_datetime_object_is_refused_directly"
H5 = "test_h5_a_config_changed_by_model_copy_is_still_named_by_the_helper"
N1 = "test_n1_demo_fake_priced_loads_without_a_date"
NEGATIVE = "test_fail_before_negative_price_with_the_fake_kind_is_refused"
NOT_RAISED = "DID NOT RAISE"
REFUSED = "validation error for Config"  # the first failing line names pydantic's error class, not the refusal text
ARABIC = "-".join(
    "".join(f"\\u066{d}" for d in part) for part in ("2026", "11", "20")
)  # as pytest writes the id

SIGNED = '        if v.is_signed():\n            raise ValueError("a price must not be negative")\n'
CEILING = (
    "        if v > defaults.MAX_ROUTE_PRICE_USD_PER_MTOK:\n"
    '            raise ValueError(f"a price may be at most {defaults.MAX_ROUTE_PRICE_USD_PER_MTOK}")\n'
)
DECIMALS = (
    '        if v != v.quantize(Decimal("1E-6")):\n'
    '            raise ValueError("a price may have at most 6 decimal places")\n'
)
PLAIN = "        if v is not None and not text and (not isinstance(v, date) or isinstance(v, datetime)):"
SHAPE = 'r"[0-9]{4}-[0-9]{2}-[0-9]{2}"'
FUTURE = "    if cfg.prices_as_of is not None and cfg.prices_as_of > _today():"


def mutant(name, old, new, killer, expect, crash=False):
    return Mutant(
        name,
        CFG,
        old,
        new,
        expect,
        allow_crash=crash,
        crash_type="ValidationError" if crash else "",
        test_file=SELF,
        only_test=killer.split("[")[0],
        pinned=SELF[:-3] + "::" + killer,
    )


M = [
    mutant("M1 the zero rule does not look at the environment", '    if live or cfg.backends.llm.kind != "fake":',
        '    if cfg.backends.llm.kind != "fake":', E4, "a zero price is allowed"),
    mutant("M2 the zero rule does not look at the llm kind", '    if live or cfg.backends.llm.kind != "fake":',
        "    if live:", E2 + f"['0'-{IN}]", NOT_RAISED),
    mutant("M3 the zero rule compares with < 0", "if getattr(route, field) == 0", "if getattr(route, field) < 0",
        H5, "assert [] == ["),
    mutant("M4 only the input field is checked for zero", f'for field in ("{IN}", "{OUT}")', f'for field in ("{IN}",)',
        E3_SPARE, NOT_RAISED),
    mutant("M4b only the output field is checked for zero", f'for field in ("{IN}", "{OUT}")', f'for field in ("{OUT}",)',
        E3_JUDGE + f"[{IN}]", NOT_RAISED),
    mutant("M5 the is_signed branch is removed", SIGNED, "", NEGATIVE, NOT_RAISED),
    mutant("M5b is_signed becomes v < 0 (minus zero loads)", "        if v.is_signed():", "        if v < 0:",
        H1 + f"['-0'-'a price must not be neg-{IN}]", NOT_RAISED),
    mutant("M6a the ceiling branch is removed", CEILING, "",
        H1 + f"['1000000.000001'-'a price may be at most -{IN}]", NOT_RAISED),
    mutant("M6b the decimals branch is removed", DECIMALS, "",
        H1 + f"['0.0000001'-'a price may have at mos-{IN}]", NOT_RAISED),
    mutant("M6c the ceiling itself is refused (> becomes >=)", "        if v > defaults.MAX_ROUTE_PRICE_USD_PER_MTOK:",
        "        if v >= defaults.MAX_ROUTE_PRICE_USD_PER_MTOK:", E7 + f"['1000000'-{IN}]", REFUSED, crash=True),
    mutant("M7 the date is required in demo too", "    if live and cfg.prices_as_of is None:",
        "    if cfg.prices_as_of is None:", N1, REFUSED, crash=True),
    mutant("M8 the required-date rule is removed", "    if live and cfg.prices_as_of is None:", "    if False:",
        E5_DATE + "[pilot]", NOT_RAISED),
    mutant("M9 a date of today counts as the future (> becomes >=)", "cfg.prices_as_of > _today()",
        "cfg.prices_as_of >= _today()", E6_LOAD + "[text-today]", REFUSED, crash=True),
    mutant("M9b the future rule is removed", FUTURE, "    if False:", E6_FUTURE + "[1]", NOT_RAISED),
    mutant("M10 _plain_date returns the value unchecked", PLAIN, "        if False:", H4 + "[pilot-0]", NOT_RAISED),
    mutant("M10b a datetime object is allowed", "(not isinstance(v, date) or isinstance(v, datetime))",
        "(not isinstance(v, date))", H4_OBJECT, NOT_RAISED),
    mutant("M10c the date text is matched at its start only", "re.fullmatch(" + SHAPE, "re.match(" + SHAPE,
        H4 + "[pilot-'2026-11-20T00:00:00']", NOT_RAISED),
    mutant("M10d the date text may hold digits that are not ASCII", SHAPE, 'r"\\d{4}-\\d{2}-\\d{2}"',
        H4 + "[pilot-'" + ARABIC + "']", "prices_as_of must be a date written"),
    mutant("M11 the price refusals are not added to the refused list", "        refused += _price_refusals(self)\n", "",
        E5_ZERO + f"[pilot-{IN}]", NOT_RAISED),
    mutant("M12 the routes are sorted last name first", "sorted(cfg.routes.items())",
        "sorted(cfg.routes.items(), reverse=True)", H3, "routes.alpha"),
]  # fmt: skip

# A mutant NO test of tests/test_price_constraint.py kills (the whole file passes with it): (name, old, new, why).
HOLES = [
    ("M12 (plain form) the routes are not sorted", "sorted(cfg.routes.items())", "cfg.routes.items()",
        "the tests write config.yaml with yaml.safe_dump, which sorts the keys, so the routes arrive sorted anyway"),
]  # fmt: skip


if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in m.name for m in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
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
        ROOT,
        M,
        [SELF],
        extra_dirs=("tests", "tools"),
        only=only,
        on_result=show,
        first_lines=first_lines,
        timeout=300,
    )
    for name, _old, _new, why in HOLES:
        print(f"hole (not run, no test kills it): {name}: {why}")
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
