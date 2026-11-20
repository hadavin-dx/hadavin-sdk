"""Killing tests for the money definer functions of 0011, by a different agent than the builders (ticket
F-money-definer, mutants M-a to M-j and friends; same shape as `tests/test_money_guard_mutants.py`).

Each mutant is a COPY of the 0011 SQL (never the repo file) or a changed pin, grant or owner, applied in a scratch
schema of its own with its own throwaway roles. The battery of `tests/test_money_definer_pg.py` (`BATTERY`, run as the
runtime login of the FINAL design) and the static rules of `tests/test_money_definer_static.py` are then run; the
mutant must fail the named checks (or the static rules). The control, the real SQL, must pass everything, so the
battery is proven able to tell. Needs HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import os
import re
import shutil

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

from hadavin_sdk.store import migrate as mig
from tests.test_money_definer_pg import (
    BATTERY,
    NAMES,
    build_world,
    run_battery,
    teardown_world,
)
from tests.test_money_definer_static import SQL_FILE, static_problems

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

ALL_SIGS = mig.MONEY_FUNCTIONS[:5]
SIG = dict(zip(NAMES, mig.MONEY_FUNCTIONS[:5], strict=True))


def in_fn(fn: str, pattern: str, repl: str, flags: int = re.DOTALL):
    """A text mutator: one regex substitution inside one function of the file (it must match exactly once)."""

    def mutate(text: str) -> str:
        start = text.index(f"CREATE OR REPLACE FUNCTION {NAMES[fn]}(")
        end = text.index("$fn$;", text.index("$fn$", text.index("$fn$", start) + 1)) + 5
        chunk = text[start:end]
        new, n = re.subn(pattern, repl, chunk, count=1, flags=flags)
        assert n == 1, f"mutant pattern did not match in {fn}: {pattern}"
        return text[:start] + new + text[end:]

    return mutate


def everywhere(old: str, new: str):
    def mutate(text: str) -> str:
        cut = text.index("CREATE TABLE hadavin_limits")
        assert old in text[cut:], old
        return text[:cut] + text[cut:].replace(old, new)

    return mutate


def drop_check(fn: str, param: str):
    return in_fn(
        fn, rf"(IF )[^;]*?( THEN\s+RAISE EXCEPTION 'invalid argument: {param}')", r"\1false\2"
    )


def sql_all(template: str):
    """Post-migrate SQL for every one of the five functions; {sig} {schema} {runtime} {portal}."""

    def hook(w):
        for sig in ALL_SIGS:
            w.do(template.format(sig=sig, schema=w.schema, runtime=w.runtime, portal=w.portal))

    return hook


def sql_once(*templates: str):
    def hook(w):
        for t in templates:
            w.do(
                t.format(
                    schema=w.schema,
                    runtime=w.runtime,
                    portal=w.portal,
                    purge=w.purge,
                    release=w.release,
                    reserve=SIG["reserve"],
                    settle=SIG["settle"],
                    add=SIG["add"],
                    purgefn=SIG["purge"],
                    expire=SIG["expire"],
                )
            )

    return hook


def _owner_swap(w):
    for sig in ALL_SIGS:
        w.do(f"ALTER FUNCTION {sig} OWNER TO {w.runtime}")


def _one_owner_swapped(w):
    w.do(f"ALTER FUNCTION {SIG['add']} OWNER TO {w.portal}")


def _pin_dropped_on_rerun(monkeypatch):
    monkeypatch.setattr(mig, "_pin_money_functions", lambda db: None)


# name: (text mutator or None, post-migrate hook or None, pre-migrate monkeypatch hook or None, battery killers,
#        static rules must also fire?)
MUTANTS = {
    # M-a: the search path
    "a_search_path_without_pg_temp": (
        None,
        sql_all("ALTER FUNCTION {sig} SET search_path = pg_catalog, {schema}"),
        None,
        {"temp_shadow", "definer_and_pins"},
        False,
    ),
    "a2_pg_temp_first": (
        None,
        sql_all("ALTER FUNCTION {sig} SET search_path = pg_temp, pg_catalog, {schema}"),
        None,
        {"temp_shadow", "definer_and_pins"},
        False,
    ),
    "a3_search_path_unpinned": (
        None,
        sql_all("ALTER FUNCTION {sig} RESET search_path"),
        None,
        {"definer_and_pins"},
        False,
    ),
    "a4_pin_dropped_on_the_run": (
        None,
        None,
        _pin_dropped_on_rerun,
        {"definer_and_pins", "behaviour"},
        False,
    ),
    # M-b: EXECUTE
    "b_execute_left_to_public": (
        None,
        sql_once("GRANT EXECUTE ON FUNCTION {reserve} TO PUBLIC"),
        None,
        {"execute_map"},
        False,
    ),
    "b_purge_to_public": (
        None,
        sql_once("GRANT EXECUTE ON FUNCTION {purgefn} TO PUBLIC"),
        None,
        {"execute_map"},
        False,
    ),
    "b2_execute_to_the_portal_role": (
        None,
        sql_once("GRANT EXECUTE ON FUNCTION {settle} TO {portal}"),
        None,
        {"execute_map"},
        False,
    ),
    "b3_purge_to_the_runtime": (
        None,
        sql_once("GRANT EXECUTE ON FUNCTION {purgefn} TO {runtime}"),
        None,
        {"execute_map"},
        False,
    ),
    "b4_runtime_runs_the_release_function": (
        None,
        sql_once(
            "GRANT EXECUTE ON FUNCTION hadavin_release_expired_spend(text, date) TO {runtime}"
        ),
        None,
        {"release_function_not_callable"},
        False,
    ),
    "b5_runtime_lost_execute": (
        None,
        sql_once("REVOKE EXECUTE ON FUNCTION {add} FROM {runtime}"),
        None,
        {"execute_map", "behaviour"},
        False,
    ),
    # M-c: invoker
    "c_security_invoker": (
        everywhere("SECURITY DEFINER", "SECURITY INVOKER"),
        None,
        None,
        {"behaviour", "definer_and_pins"},
        True,
    ),
    # M-d: grants widened to the runtime on the tables
    "d_update_on_spend": (
        None,
        sql_once("GRANT UPDATE ON spend TO {runtime}"),
        None,
        {
            "no_table_rights"
        },  # the 0010 tripwire still refuses a lowering UPDATE: the grant check is the kill
        False,
    ),
    "d_update_on_spend_month": (
        None,
        sql_once("GRANT UPDATE ON spend_month TO {runtime}"),
        None,
        {"no_table_rights"},
        False,
    ),
    "d_insert_on_reservations": (
        None,
        sql_once("GRANT INSERT ON spend_reservations TO {runtime}"),
        None,
        {"no_table_rights", "attack_h2_forged_settled_hold"},
        False,
    ),
    "d_update_on_reservations": (
        None,
        sql_once("GRANT UPDATE ON spend_reservations TO {runtime}"),
        None,
        {"no_table_rights"},
        False,
    ),
    "d_column_update_usd": (
        None,
        sql_once("GRANT UPDATE (usd) ON spend TO {runtime}"),
        None,
        {"no_table_rights"},
        False,
    ),
    "d_delete_on_reservations": (
        None,
        sql_once("GRANT DELETE ON spend_reservations TO {runtime}"),
        None,
        {"no_table_rights"},
        False,
    ),
    "d_trigger_on_spend": (
        None,
        sql_once("GRANT TRIGGER ON spend TO {runtime}"),
        None,
        {"no_table_rights"},
        False,
    ),
    "d_select_on_reservations": (
        None,
        sql_once("GRANT SELECT ON spend_reservations TO {runtime}"),
        None,
        {"no_table_rights"},
        False,
    ),
    "d_rights_on_the_limits": (
        None,
        sql_once("GRANT SELECT, UPDATE ON hadavin_limits TO {runtime}"),
        None,
        {"no_table_rights"},
        False,
    ),
    "d_all_rights_at_the_old_map": (
        None,
        sql_once(
            "GRANT SELECT, INSERT, UPDATE ON spend, spend_month, spend_reservations TO {runtime}"
        ),
        None,
        {
            "no_table_rights",
            "attack_h1_repeated_lowering",
            "attack_h2_forged_settled_hold",
            "attack_h2_inflate_reserved",
        },
        False,
    ),
    # M-e: owner swapped
    "e_functions_owned_by_the_runtime": (None, _owner_swap, None, {"owner", "behaviour"}, False),
    "e2_one_function_owned_by_another_role": (None, _one_owner_swapped, None, {"owner"}, False),
    "e3_limits_table_owned_by_the_runtime": (
        None,
        sql_once("ALTER TABLE hadavin_limits OWNER TO {runtime}"),
        None,
        {"owner", "no_table_rights"},
        False,
    ),
    # M-f: one argument check removed
    **{
        f"f_{fn}_{param}_check_removed": (
            drop_check(fn, param),
            None,
            None,
            {"hostile_arguments"},
            False,
        )
        for fn, param in (
            ("reserve", "p_id"),
            ("reserve", "p_agent"),
            ("reserve", "p_run_id"),
            ("reserve", "p_day"),
            ("reserve", "p_usd"),
            # no ("reserve", "p_day_cap") / "p_month_cap": the caps are read from hadavin_caps now, not passed in; the
            # missing-cap-row guard (HD005) is killed by tests/test_money_caps_mutants.py
            ("settle", "p_id"),
            ("settle", "p_actual"),
            ("settle", "p_agent"),
            ("expire", "p_age_s"),
            ("purge", "p_before"),
            ("add", "p_agent"),
            ("add", "p_day"),
            ("add", "p_usd"),
        )
    },
    # M-f2: STRICT
    **{
        f"f2_{fn}_strict": (
            in_fn(fn, r"VOLATILE\nSECURITY", "VOLATILE STRICT\nSECURITY"),
            None,
            None,
            {"hostile_arguments", "definer_and_pins"},
            True,
        )
        for fn in NAMES
    },
    # M-g: dynamic SQL built from the argument
    "g_dynamic_sql_in_add_spend": (
        in_fn(
            "add",
            r"INSERT INTO spend AS s \(agent_id, day, usd\) VALUES \(p_agent, p_day, p_usd\)\s+ON CONFLICT \(agent_id, day\) "
            r"DO UPDATE SET usd = s.usd \+ EXCLUDED.usd\s+RETURNING s.usd INTO day_usd;",
            "EXECUTE 'INSERT INTO spend (agent_id, day, usd) VALUES (''' || p_agent || ''', ''' || p_day || ''', ' "
            "|| p_usd || ') ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd' "
            "INTO day_usd;",
        ),
        None,
        None,
        {"injection_agent_ids_are_stored_verbatim"},
        True,
    ),
    # M-h: a table named through pg_temp
    "h_body_names_pg_temp_spend": (
        in_fn("reserve", r"UPDATE spend s SET", "UPDATE pg_temp.spend s SET"),
        None,
        None,
        {"behaviour"},
        True,
    ),
    # M-i: the cap comparison weakened
    "i_day_cap_weakened": (
        in_fn("reserve", r"s\.usd < v_day_cap", "s.usd <= v_day_cap"),
        None,
        None,
        {"cap_comparison"},
        False,
    ),
    "i_month_cap_weakened": (
        in_fn("reserve", r"m\.usd < v_month_cap", "m.usd <= v_month_cap"),
        None,
        None,
        {"cap_comparison"},
        False,
    ),
    "i_sum_check_dropped_on_the_day": (
        in_fn("reserve", r" AND s\.usd \+ p_usd <= v_day_cap", ""),
        None,
        None,
        {"behaviour"},
        False,
    ),
    "i_month_cap_ignored": (
        in_fn("reserve", r"AND m\.usd < v_month_cap AND m\.usd \+ p_usd <= v_month_cap", ""),
        None,
        None,
        {"cap_comparison"},
        False,
    ),
    # M-j: settle lowers an expired hold
    "j_settle_lowers_an_expired_hold": (
        in_fn(
            "settle",
            r"CASE WHEN v_was = 'expired' THEN GREATEST\(p_actual, r\.reserved_usd\) ELSE p_actual END",
            "p_actual",
        ),
        None,
        None,
        {"settle_never_lowers_an_expired_hold"},
        False,
    ),
    # the claim
    "k_settle_without_the_row_lock": (
        in_fn("settle", r"\s+FOR UPDATE;", ";"),
        None,
        None,
        {"concurrent_settle"},
        False,
    ),
    "k_settle_without_the_open_guard": (
        in_fn("settle", r"AND r\.status IN \('open', 'expired'\)", ""),
        None,
        None,
        {"behaviour", "concurrent_settle"},
        False,
    ),
    # hard-coded limits (equal to the defaults, so only a test that moves the limit can tell)
    "l_amount_limit_literal_in_reserve": (
        in_fn("reserve", r"p_usd < v_max_amount", "p_usd < 1000000000"),
        None,
        None,
        {"limits_are_read_not_hardcoded"},
        True,
    ),
    "l_decimals_literal_in_add": (
        in_fn(
            "add", r"pg_catalog\.scale\(p_usd\) > v_max_decimals", "pg_catalog.scale(p_usd) > 12"
        ),
        None,
        None,
        {"limits_are_read_not_hardcoded"},
        True,
    ),
    "l_id_length_literal_in_settle": (
        in_fn("settle", r"NOT BETWEEN 1 AND v_max_id OR p_id", "NOT BETWEEN 1 AND 200 OR p_id"),
        None,
        None,
        {"limits_are_read_not_hardcoded"},
        True,
    ),
    "l_expiry_age_literal": (
        in_fn("expire", r"p_age_s > v_max_age", "p_age_s > 10000000"),
        None,
        None,
        {"limits_are_read_not_hardcoded"},
        True,
    ),
}


@pytest.fixture(name="scratch")
def scratch_world():
    w = build_world()
    try:
        yield w
    finally:
        teardown_world(w)


def _apply_text_mutation(tmp_path, monkeypatch, mutate):
    text = SQL_FILE.read_text(encoding="utf-8")
    mutated = mutate(text)
    folder = tmp_path / "migrations"
    shutil.copytree(mig.MIGRATIONS, folder)
    (folder / SQL_FILE.name).write_text(mutated, encoding="utf-8")
    real = mig._migration_files
    monkeypatch.setattr(mig, "_migration_files", lambda folder_=None: real(folder))
    return text, mutated


def test_the_control_the_real_sql_passes_every_check(scratch):
    w = scratch
    w.migrate(release_role=w.release)
    assert run_battery(w) == {}


@pytest.mark.parametrize("name", list(MUTANTS))
def test_the_battery_kills_every_mutant(name, scratch, tmp_path, monkeypatch):
    mutate, post, pre, killers, static_too = MUTANTS[name]
    assert killers <= set(BATTERY), f"{name}: unknown check {killers - set(BATTERY)}"
    mutated = None
    if mutate is not None:
        original, mutated = _apply_text_mutation(tmp_path, monkeypatch, mutate)
        assert mutated != original, (
            f"{name}: the mutation did not change the SQL: it proves nothing"
        )
    if pre is not None:
        pre(monkeypatch)
    w = scratch
    w.migrate(release_role=w.release)
    if post is not None:
        post(w)
    failed = run_battery(w)
    missing = killers - set(failed)
    assert not missing, f"{name}: survived the checks {sorted(missing)}; failed: {failed}"
    if static_too and mutated is not None:
        assert static_problems(mutated), f"{name}: the static rules let this mutant through"
