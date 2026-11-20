"""Static properties of the 0011 SQL (money definer functions), by a different agent than the builders. No database.

The comments of the file are stripped first (they name things like EXECUTE and 1e9 on purpose). Every rule is a
function of the text, `static_problems(text)`, so the mutant harness (`tests/test_money_definer_mutants.py`) runs
the same rules over each mutated copy. "Every hadavin_* function is in the map" belongs to the migrate tests
(`tests/test_money_definer_migrate.py`) and is not repeated here.

The second half reads `store/postgres.py`: once builder D's step 3 is merged it must call the money functions only
by their schema-qualified name and hold no INSERT/UPDATE/DELETE of its own on the three money tables. Until then
that test SKIPS with the reason."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from hadavin_sdk.store import migrate as mig

SQL_FILE = mig.MIGRATIONS / "0011_money_definer.sql"
POSTGRES_PY = Path(mig.__file__).with_name("postgres.py")
FUNCTION_NAMES = (
    "hadavin_reserve_spend",
    "hadavin_settle_spend",
    "hadavin_expire_spend_reservations",
    "hadavin_purge_spend_reservations",
    "hadavin_add_spend",
)
# Added by the caps work (builder E1): not called by the money paths of the store, but the same static rules apply.
CAP_FUNCTION_NAMES = ("hadavin_set_cap", "hadavin_cap_matches")
# 0011 replaces the release function of 0008 (review M1: the minimum age); the same static rules apply to it.
RELEASE_FUNCTION_NAMES = ("hadavin_release_expired_spend",)
ALL_FUNCTION_NAMES = FUNCTION_NAMES + CAP_FUNCTION_NAMES + RELEASE_FUNCTION_NAMES
# The defaults the limits are seeded with: none of them may appear as a literal in a function (parity with the
# defaults would hide a hard-coded limit from every behavioural test that leaves the limits alone). A neighbouring
# hyphen excludes the parts of a date literal such as DATE '9999-12-31' (the day window is not a limit).
LIMIT_LITERALS = re.compile(r"(?<![\w.-])(?:1e9|1E9|1000000000|10000000|200|12)(?![\w.-])")
UNQUALIFIED_BUILTINS = re.compile(
    r"(?<![\w.])(?:char_length|scale|isfinite|clock_timestamp|date_trunc|make_interval)\s*\("
)


def strip_comments(text: str) -> str:
    return re.sub(r"--[^\n]*", "", text)


def _functions(code: str) -> dict[str, str]:
    parts = re.split(r"(?=CREATE OR REPLACE FUNCTION )", code)
    out = {}
    for part in parts:
        m = re.match(r"CREATE OR REPLACE FUNCTION (\w+)\(", part)
        if m:
            out[m.group(1)] = part
    return out


def static_problems(text: str) -> list[str]:
    code = strip_comments(text)
    problems: list[str] = []
    funcs = _functions(code)
    if set(funcs) != set(ALL_FUNCTION_NAMES):
        problems.append(f"the functions are {sorted(funcs)}")
    for name, body in funcs.items():
        header = body.split("$fn$", 1)[0]
        if "SECURITY DEFINER" not in header or "SECURITY INVOKER" in header:
            problems.append(f"{name}: not SECURITY DEFINER")
        if not re.search(r"SET search_path = pg_catalog, pg_temp\s+AS$", header.rstrip()):
            problems.append(f"{name}: no placeholder pin `SET search_path = pg_catalog, pg_temp`")
        if re.search(r"\bSTRICT\b|RETURNS NULL ON NULL INPUT", header):
            problems.append(f"{name}: STRICT")
        if "VOLATILE" not in header:
            problems.append(f"{name}: VOLATILE not stated")
        if not re.search(rf"REVOKE ALL ON FUNCTION {name}\([^)]*\) FROM PUBLIC;", code):
            problems.append(f"{name}: no REVOKE ALL ... FROM PUBLIC")
        inner = body.split("$fn$")[1] if body.count("$fn$") >= 2 else ""
        if re.search(r"\bEXCEPTION\b(?!\s*')", inner):
            problems.append(f"{name}: an EXCEPTION block (a subtransaction)")
        if re.search(
            r"\bEXECUTE\b|\bformat\s*\(|\|\||\bquote_(?:ident|literal)\b", inner, re.IGNORECASE
        ):
            problems.append(f"{name}: dynamic SQL")
        if hit := LIMIT_LITERALS.search(inner):
            problems.append(f"{name}: limit literal {hit.group(0)!r} (read hadavin_limits)")
        if hit := UNQUALIFIED_BUILTINS.search(inner):
            problems.append(f"{name}: built-in called without pg_catalog.: {hit.group(0)!r}")
        if "pg_temp." in inner:
            problems.append(f"{name}: names pg_temp")
        if "STABLE" in header or "IMMUTABLE" in header:
            problems.append(f"{name}: not VOLATILE")
    if re.search(r"\bGRANT\b", code):
        problems.append("the file grants a right (grants are migrate's)")
    if not re.search(r"REVOKE ALL ON hadavin_limits FROM PUBLIC;", code):
        problems.append("hadavin_limits is not revoked from PUBLIC")
    # the one allowed ALTER: the usd range CHECKs of the counter tables (review N1), added NOT VALID and validated
    allowed = re.compile(
        r"ALTER\s+TABLE\s+spend(?:_month)?\s+(?:ADD\s+CONSTRAINT\s+\w+\s+CHECK\s*\([^;]*\)\s+NOT\s+VALID|VALIDATE\s+CONSTRAINT\s+\w+)\s*;"
    )
    rest = allowed.sub("", code)
    if "SECURITY DEFINER" in code and re.search(r"\bALTER\s+(?:FUNCTION|TABLE)\b", rest):
        problems.append("the file alters an object (owner and pins are migrate's)")
    return problems


def test_the_real_0011_has_no_static_problem():
    assert static_problems(SQL_FILE.read_text(encoding="utf-8")) == []


def test_the_rules_are_not_vacuous_each_plant_is_found():
    base = SQL_FILE.read_text(encoding="utf-8")
    cut = base.index(
        "CREATE TABLE hadavin_limits"
    )  # the header comment names every one of these words

    def plant(old: str, new: str, count: int = 1) -> str:
        assert old in base[cut:], old
        return base[:cut] + base[cut:].replace(old, new, count)

    plants = {
        "limit literal 1e9": plant("p_usd < v_max_amount", "p_usd < 1000000000"),
        "limit literal 200": plant("NOT BETWEEN 1 AND v_max_id", "NOT BETWEEN 1 AND 200"),
        "limit literal 12": plant("scale(p_usd) > v_max_decimals", "scale(p_usd) > 12"),
        "exception block": plant(
            "RETURN NEXT;\nEND\n$fn$", "RETURN NEXT;\nEXCEPTION WHEN others THEN RETURN;\nEND\n$fn$"
        ),
        "execute": plant(
            "v_month := pg_catalog.date_trunc",
            "EXECUTE 'SELECT 1'; v_month := pg_catalog.date_trunc",
        ),
        "format": plant(
            "v_month := pg_catalog.date_trunc",
            "PERFORM format('%s', 1); v_month := pg_catalog.date_trunc",
        ),
        "concatenation": plant("'invalid argument: p_agent'", "'x' || p_agent"),
        "no definer": plant("VOLATILE\nSECURITY DEFINER", "VOLATILE\nSECURITY INVOKER"),
        "no pin": plant("SET search_path = pg_catalog, pg_temp\nAS", "AS"),
        "temp first": plant(
            "SET search_path = pg_catalog, pg_temp\nAS", "SET search_path = pg_temp, pg_catalog\nAS"
        ),
        "strict": plant("VOLATILE\nSECURITY", "VOLATILE STRICT\nSECURITY"),
        "public not revoked": plant(
            "REVOKE ALL ON FUNCTION hadavin_add_spend(TEXT, DATE, NUMERIC) FROM PUBLIC;", ""
        ),
        "unqualified built-in": plant("pg_catalog.scale(p_usd)", "scale(p_usd)"),
        "stable": plant("VOLATILE\nSECURITY", "STABLE\nSECURITY"),
        "a grant": base
        + "\nGRANT EXECUTE ON FUNCTION hadavin_add_spend(TEXT, DATE, NUMERIC) TO PUBLIC;",
    }
    for name, text in plants.items():
        assert text != base, f"{name}: the plant changed nothing"
        assert static_problems(text), f"{name}: not found"


def test_no_exception_block_no_dynamic_sql_no_limit_literal_in_any_function():
    code = strip_comments(SQL_FILE.read_text(encoding="utf-8"))
    assert not re.search(r"\bEXCEPTION\b(?!\s*')", code), "an EXCEPTION block"
    assert not re.search(r"\bEXECUTE\b|\bformat\s*\(", code, re.IGNORECASE)
    for name, body in _functions(code).items():
        assert not LIMIT_LITERALS.search(body.split("$fn$")[1]), name


def test_every_function_pins_the_search_path_with_the_temp_schema_last():
    code = strip_comments(SQL_FILE.read_text(encoding="utf-8"))
    pins = re.findall(r"SET search_path = ([^\n]*)\n", code)
    assert len(pins) == len(ALL_FUNCTION_NAMES) and set(pins) == {"pg_catalog, pg_temp"}


# --- the store calls only the functions ------------------------------------------------------------------------------

_WRITES_MONEY = re.compile(
    r"(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+\{?\"?(?:spend|spend_month|spend_reservations)\b",
    re.IGNORECASE,
)


def _store_sql_text() -> str:
    return POSTGRES_PY.read_text(encoding="utf-8")


def _no_money_writes_or_skip(text: str) -> None:
    if _WRITES_MONEY.search(text):
        pytest.skip(
            "store/postgres.py still holds its own INSERT/UPDATE/DELETE on spend, spend_month or "
            "spend_reservations (builder D's step 3 is not merged here); this test starts to run when it is"
        )


def test_postgres_py_calls_the_money_functions_schema_qualified_and_writes_no_money_table_itself():
    text = _store_sql_text()
    _no_money_writes_or_skip(text)
    # The store builds the call in ONE helper, `_money_call(function, placeholders)`, from the quoted schema and the
    # function name as two identifiers; the names are passed to it as string literals.
    helper = re.search(r"def _money_call\(.*?(?=\n    def )", text, re.DOTALL)
    assert helper, "no _money_call helper"
    assert re.search(r'FROM \{\}\.\{\}\(\{\}\)"', helper.group(0)) and re.search(
        r"sql\.Identifier\(self\._schema\),\s*sql\.Identifier\(function\)", helper.group(0)
    ), "_money_call does not schema-qualify"
    names = set(re.findall(r'"(hadavin_[a-z_]+)"', text))
    direct = list(re.finditer(r"(?<![\w])hadavin_[a-z_]+\s*\(", text))
    names |= {m.group(0).rstrip("( ") for m in direct}
    assert set(FUNCTION_NAMES) <= names, f"the store never calls {set(FUNCTION_NAMES) - names}"
    for name in FUNCTION_NAMES:  # none of the new functions is ever written as an unqualified call
        assert not re.search(rf"FROM\s+{name}\s*\(", text), f"unqualified call of {name}"


def test_postgres_py_has_no_unqualified_call_of_any_hadavin_function():
    text = _store_sql_text()
    _no_money_writes_or_skip(text)
    unqualified = [m.group(0) for m in re.finditer(r"(?<![\w.])hadavin_[a-z_]+\s*\(", text)]
    assert not unqualified, f"unqualified calls: {unqualified}"
