"""Server-free tests of the before/after comparison of `migrate` and of the check of rights after the files
(`_changed_since`, `_refuse_unlisted_grantees`, the message helpers, the lock-holder message). No database: the rows a
server would answer are made up here, so each branch is shown with exactly the row that reaches it. The same behaviour
against a real server is in tests/test_migration_postgres.py (round 12 section).

These tests call functions that are new in round 12 (or whose arguments changed), so they cannot run against the
source of 8382bdd; the proof that the old code was wrong is in the server tests, which say "Fails on 8382bdd".
"""

from __future__ import annotations

import contextlib

import pytest
from psycopg import errors as pg_errors

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migrate as mig

# One made-up state row per catalog, in the order of the fields (without the id): in scope, owner, then the rest.
FUNCTION = (True, "migrator", False, "{10 0 EXECUTE false}", "SELECT 1", None, None, 14, None)
RELATION = (True, "migrator", "", "")
SCHEMA = (True, "migrator", "{10 10 USAGE false}")
ROWS = {"functions": FUNCTION, "relations": RELATION, "schemas": SCHEMA}
FIELDS = {
    "functions": mig._FUNCTION_FIELDS,
    "relations": mig._RELATION_FIELDS,
    "schemas": mig._SCHEMA_FIELDS,
}


def _objects(**catalogs) -> mig._Objects:
    return mig._Objects(
        catalogs.get("functions", {}), catalogs.get("relations", {}), catalogs.get("schemas", {})
    )


def _with(row: tuple, index: int, value) -> tuple:
    return (*row[:index], value, *row[index + 1 :])


def _other_value(value):
    """A value of the same kind that differs."""
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1
    return "changed" if value != "changed" else "changed again"


# --- _changed_since ----------------------------------------------------------------------------------------------------


def test_the_field_names_match_the_rows_the_state_queries_return():
    """The rows above have one value per named field, and the two places every catalog shares are the first two."""
    for catalog, row in ROWS.items():
        assert len(row) == len(FIELDS[catalog]), catalog
        assert FIELDS[catalog][mig._IN_SCOPE] == "in scope"
        assert FIELDS[catalog][mig._OWNER] == "owner"


@pytest.mark.parametrize(
    ("catalog", "index"),
    [(c, i) for c, row in ROWS.items() for i in range(1, len(row))],
    ids=lambda v: str(v),
)
def test_a_difference_in_any_one_field_of_an_object_in_scope_makes_it_changed(catalog, index):
    """Every field is compared on its own: a function whose language, library file, SQL-standard body, saved settings,
    text body, rights, SECURITY DEFINER flag or owner differs is changed; the same for the fields of a relation and of
    a schema. Killed by: mutant CS1 (only the owner is compared)."""
    before = _objects(**{catalog: {7: ROWS[catalog]}})
    row = _with(ROWS[catalog], index, _other_value(ROWS[catalog][index]))
    changed = mig._changed_since(before, _objects(**{catalog: {7: row}}))
    assert getattr(changed, catalog) == frozenset({7}), FIELDS[catalog][index]
    others = {"functions", "relations", "schemas"} - {catalog}
    assert all(getattr(changed, other) == frozenset() for other in others)


@pytest.mark.parametrize("catalog", list(ROWS))
def test_an_object_that_is_out_of_scope_before_and_after_is_never_changed(catalog):
    """Another role owns it and the migration role gave no right on it: whatever another session did to it while the
    run was open (a new owner, new rights, a new body), and also when it appeared during the run, it is not listed.
    Killed by: mutant CS2 (the scope is not asked)."""
    theirs = _with(ROWS[catalog], mig._IN_SCOPE, False)
    moved = _with(_with(theirs, mig._OWNER, "somebody_else"), 2, _other_value(theirs[2]))
    changed = mig._changed_since(
        _objects(**{catalog: {7: theirs}}), _objects(**{catalog: {7: moved, 8: theirs}})
    )
    assert getattr(changed, catalog) == frozenset()


@pytest.mark.parametrize("catalog", list(ROWS))
def test_an_object_in_scope_only_before_or_only_after_is_compared(catalog):
    """In scope before and not after: the migration role's object was handed to a role it does not belong to. In scope
    after and not before: the migration role now owns it or gave a right on it. Both are changes. A new object in
    scope is one too. Killed by: mutants CS4 (only the scope after the files counts) and CS5 (only the scope before)."""
    mine = ROWS[catalog]
    theirs = _with(_with(mine, mig._IN_SCOPE, False), mig._OWNER, "stranger")
    handed = mig._changed_since(
        _objects(**{catalog: {7: mine}}), _objects(**{catalog: {7: theirs}})
    )
    taken = mig._changed_since(_objects(**{catalog: {7: theirs}}), _objects(**{catalog: {7: mine}}))
    new = mig._changed_since(_objects(), _objects(**{catalog: {7: mine}}))
    same = mig._changed_since(_objects(**{catalog: {7: mine}}), _objects(**{catalog: {7: mine}}))
    assert getattr(handed, catalog) == getattr(taken, catalog) == getattr(new, catalog) == {7}
    assert getattr(same, catalog) == frozenset()
    kept = "kept_" + catalog
    assert getattr(handed, kept) == getattr(taken, kept) == getattr(new, kept) == frozenset()
    assert getattr(same, kept) == {7}


def test_the_ids_that_kept_their_owner_are_one_set_per_catalog():
    """An id is unique only inside its catalog: function 7, relation 7 and schema 7 are three objects. Here function 7
    kept its owner and relation 7 and schema 7 did not; one mixed set would let the function's id excuse the other two
    (an owner that a file handed over would pass as "it had that owner before"). Killed by: mutants KC1 and KC2 (the
    relations or the schemas take the kept ids of the functions) and OW7 (a function that kept its owner is not
    remembered)."""
    group = _with(FUNCTION, mig._OWNER, "group")
    before = _objects(functions={7: group}, relations={7: RELATION}, schemas={7: SCHEMA})
    after = _objects(
        functions={7: _with(group, 4, "SELECT 2")},
        relations={7: _with(RELATION, mig._OWNER, "group")},
        schemas={7: _with(SCHEMA, mig._OWNER, "group")},
    )
    changed = mig._changed_since(before, after)
    assert (changed.functions, changed.relations, changed.schemas) == ({7}, {7}, {7})
    assert changed.kept_functions == {7}
    assert changed.kept_relations == frozenset() and changed.kept_schemas == frozenset()


# --- the loops of `_refuse_unlisted_grantees` ---------------------------------------------------------------------------


class _Result:
    def __init__(self, rows):
        self.rows = list(rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)


class _Db:
    """Answers each query of the check with the made-up rows given for it (by the exact query text) and records every
    statement with its parameters."""

    def __init__(self, rows: dict[str, list[tuple]] | None = None):
        self.rows, self.log = rows or {}, []

    def execute(self, query, params=None):
        text = query if isinstance(query, str) else query.as_string(None)
        self.log.append((text, params))
        if text == "SELECT current_schema()":
            return _Result([("s",)])
        return _Result(self.rows.get(text, []))


def _problems(
    rows: dict[str, list[tuple]], named=(), changed=None, texts=()
) -> tuple[list[str], _Db]:
    """The list of things the refusal names (empty: no refusal) and the connection."""
    db = _Db(rows)
    try:
        mig._refuse_unlisted_grantees(db, list(texts), named, changed)
    except ConfigError as e:
        text = str(e)
        assert "Nothing was changed." in text and "another session" in text
        listed = text.split("elsewhere in this database: ", 1)[1].split(
            ". Nothing was changed.", 1
        )[0]
        return listed.split("; "), db
    return [], db


def _relation(
    who,
    priv,
    *,
    owner=False,
    col=None,
    schema="s",
    grantable=False,
    managed=True,
    kind="r",
    rel="t",
):
    return (rel, who, priv, owner, col, schema, grantable, managed, kind)


def test_the_relation_loop_refuses_each_kind_of_right_with_its_own_words():
    """One row per branch: the owner's own right (skipped), a role the run does not name, a named role on a relation of
    the grant map (accepted), the same with the grant option, and a named role outside the grant map (refused whatever
    the right, SELECT and USAGE on a sequence included). The place is the kind of relation, the schema, the name, and
    the column when the right is on one. Killed by: mutants RO1 and RO3 (rights of a named role outside the grant map),
    GO5 (the grant option), AC4 (any role is allowed)."""
    rows = [
        _relation("migrator", "INSERT", owner=True),
        _relation("stranger", "SELECT", col="a"),
        _relation("PUBLIC", "SELECT", kind="m", schema="other", rel="mv"),
        _relation("rt", "SELECT"),
        _relation("rt", "UPDATE", grantable=True),
        _relation("rt", "SELECT", managed=False, kind="v", rel="v"),
        _relation("rt", "USAGE", managed=False, kind="S", rel="seq"),
        _relation("rt", "SELECT", managed=False, kind="f", rel="ft", col="a"),
    ]
    found, _db = _problems({mig._ACL_RELATION_SQL: rows}, named=["rt"])
    outside = "(a role named in this run gets no right outside the grant map, which holds tables, views and sequences only)"
    assert sorted(found) == sorted(
        [
            "stranger has SELECT on the table s.t, column a",
            "PUBLIC has SELECT on the materialized view other.mv",
            "rt may pass UPDATE on the table s.t on to others (WITH GRANT OPTION)",
            f"rt has SELECT on the view s.v, which is not in the grant map {outside}",
            f"rt has USAGE on the sequence s.seq, which is not in the grant map {outside}",
            f"rt has SELECT on the foreign table s.ft, column a, which is not in the grant map {outside}",
        ]
    )


def test_the_owner_loop_says_what_the_object_is_and_names_it_with_its_schema():
    """A view is called a view (not "table or sequence"), a procedure a procedure, and every name starts with the
    schema; a function carries its argument list. Killed by: mutant OW9 (every relation is called a table)."""
    rows = [
        ("r", "v", "other", "v1", "", "boss"),
        ("r", "S", "s", "seq", "", "boss"),
        ("r", "f", "s", "ft", "", "boss"),
        ("f", "p", "s", "proc", "a integer", "boss"),
        ("f", "f", "other", "fn", "", "boss"),
        ("n", "", "other", "", "", "boss"),
    ]
    found, _db = _problems({mig._ACL_OWNER_SQL: rows})
    tail = " was handed to boss (it is not owned by the migration role)"
    assert sorted(found) == sorted(
        [
            "the view other.v1" + tail,
            "the sequence s.seq" + tail,
            "the foreign table s.ft" + tail,
            "the procedure s.proc(a integer)" + tail,
            "the function other.fn()" + tail,
            "the schema other" + tail,
        ]
    )


def _function(
    name,
    who=None,
    priv=None,
    *,
    definer=False,
    default=False,
    owner=False,
    grantable=False,
    judged=True,
    args="",
):
    return (name, "s", args, definer, default, who, priv, owner, grantable, judged)


def test_the_function_loop_refuses_rights_and_security_definer_and_removes_the_default_for_everyone():
    """A function with no rights list keeps the server default "everyone may call it": that default is taken away, once
    per function, by its exact name (schema first, quoted) and argument list. A right for a role the run does not
    name, for a named role (a named role gets no right on a function), and a right that may be passed on are refused.
    A SECURITY DEFINER function is refused; when it is listed only because the migration role owns it (`judged` is
    false) the message says no file made it, and its rights are NOT read and its default is NOT taken away. Killed by:
    mutants RO4 (a named role may have a right on a function), GO4 (the grant option), SD9 (the rights of a function
    that is only listed for its flag are read), AC5 (the default is not removed)."""
    rows = [
        _function("plain", default=True),
        _function('odd"name', default=True, args="a integer, b text"),
        _function('odd"name', default=True, args="a integer, b text"),
        _function("granted", "migrator", "EXECUTE", owner=True),
        _function("granted", "stranger", "EXECUTE"),
        _function("granted", "rt", "EXECUTE", grantable=True),
        _function("definer_new", "migrator", "EXECUTE", owner=True, definer=True),
        _function("definer_old", "stranger", "EXECUTE", definer=True, judged=False),
        _function("definer_old_default", default=True, definer=True, judged=False),
    ]
    found, db = _problems({mig._ACL_FUNCTION_SQL: rows}, named=["rt"])
    outside = "(a role named in this run gets no right outside the grant map, which holds tables, views and sequences only)"
    old = ", and no file of this run made or changed it: the migration role or a role it belongs to owns it"
    assert sorted(found) == sorted(
        [
            "stranger has EXECUTE on the function s.granted()",
            f"rt has EXECUTE on the function s.granted() {outside}",
            "rt may pass EXECUTE on the function s.granted() on to others (WITH GRANT OPTION)",
            "the function s.definer_new() is SECURITY DEFINER (it runs with the rights of its owner)",
            "the function s.definer_old() is SECURITY DEFINER (it runs with the rights of its owner)"
            + old,
            "the function s.definer_old_default() is SECURITY DEFINER (it runs with the rights of its owner)"
            + old,
        ]
    )
    assert not [t for t, _ in db.log if t.startswith("REVOKE")], "a refused run changes nothing"
    _none, db = _problems({mig._ACL_FUNCTION_SQL: rows[:3] + rows[3:4]})
    assert [t for t, _ in db.log if t.startswith("REVOKE")] == [
        'REVOKE ALL ON ROUTINE "s"."plain"() FROM PUBLIC',
        'REVOKE ALL ON ROUTINE "s"."odd""name"(a integer, b text) FROM PUBLIC',
    ]


def test_the_schema_loop_lets_any_role_look_a_name_up_and_refuses_everything_else():
    """USAGE on a schema is not refused for anybody. CREATE is refused for every role but the owner and the migration
    role (the last column of the row): also for a role named in the run (it may not create where this package lives;
    until round 12 a line here let a named role create in the schema of the run, which no run could reach because the
    role check refuses that earlier) and for the built-in `pg_database_owner` where it is not the owner. A right that may be passed on is
    refused, USAGE included. Killed by: mutants PDO2 (the pseudo-role is skipped), SC14 (a named role may create), GO6
    (the grant option)."""
    rows = [
        ("s", "migrator", "CREATE", False, True),
        ("s", "PUBLIC", "USAGE", False, False),
        ("s", "rt", "USAGE", False, False),
        ("s", "rt", "CREATE", False, False),
        ("s", "pg_database_owner", "CREATE", False, False),
        ("other", "stranger", "CREATE", False, False),
        ("other", "rt", "USAGE", True, False),
    ]
    found, _db = _problems({mig._ACL_SCHEMA_SQL: rows}, named=["rt"])
    assert sorted(found) == sorted(
        [
            "rt has CREATE on the schema s itself",
            "pg_database_owner has CREATE on the schema s itself",
            "stranger has CREATE on the schema other itself",
            "rt may pass USAGE on the schema other on to others (WITH GRANT OPTION)",
        ]
    )


def test_the_default_right_loop_skips_only_the_servers_own_default_for_every_schema():
    """Skipped: `EXECUTE` on functions and `USAGE` on types for everyone, set for EVERY schema (the server writes that
    entry itself). Refused: the same two for ONE schema, any other right for everyone, and every default right for a
    role, named in the run or not; each with the statement that undoes it. Killed by: mutants DP4, DP7, DP8 and DP9
    (every default right for everyone is skipped)."""
    rows = [
        ("f", None, "PUBLIC", "EXECUTE", "migrator"),
        ("T", None, "PUBLIC", "USAGE", "group"),
        ("f", "s", "PUBLIC", "EXECUTE", "migrator"),
        ("T", "s", "PUBLIC", "USAGE", "migrator"),
        ("r", None, "PUBLIC", "SELECT", "migrator"),
        ("S", None, "rt", "USAGE", "migrator"),
        ("f", None, "rt", "EXECUTE", "group"),
        ("n", None, "stranger", "USAGE", "migrator"),
    ]
    found, _db = _problems({mig._ACL_DEFAULT_SQL: rows}, named=["rt"])
    said = [f.split(" (a default right")[0] for f in found]
    assert sorted(said) == sorted(
        [
            "PUBLIC gets EXECUTE on every new function that migrator makes in the schema s",
            "PUBLIC gets USAGE on every new type that migrator makes in the schema s",
            "PUBLIC gets SELECT on every new table that migrator makes in every schema",
            "rt gets USAGE on every new sequence that migrator makes in every schema",
            "rt gets EXECUTE on every new function that group makes in every schema",
            "stranger gets USAGE on every new schema that migrator makes in every schema",
        ]
    )
    undo = {f.split("which this statement undoes: ")[1] for f in found}
    assert (
        "ALTER DEFAULT PRIVILEGES FOR ROLE <that role> IN SCHEMA <that schema> REVOKE EXECUTE ON FUNCTIONS "
        "FROM <the role or PUBLIC>)" in undo
    )
    assert (
        "ALTER DEFAULT PRIVILEGES FOR ROLE <that role> REVOKE USAGE ON SEQUENCES FROM <the role or PUBLIC>)"
        in undo
    )


def test_nothing_found_means_no_refusal_and_the_queries_get_one_set_of_ids_per_catalog():
    """The ids of the three catalogs reach the queries under their own names (a function id is never tried against the
    relations), and the managed names are two lists: relations (the grant map and the ledger) and functions (what the
    files create). Killed by: mutants KC3 (the kept relations are given the kept functions) and MC2 (the function
    names are the relation names)."""
    changed = mig._Changed(
        functions=frozenset({1}),
        relations=frozenset({2}),
        schemas=frozenset({3}),
        kept_functions=frozenset({4}),
        kept_relations=frozenset({5}),
        kept_schemas=frozenset({6}),
    )
    text = "CREATE OR REPLACE FUNCTION audit_guard() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END $$;"
    found, db = _problems({}, changed=changed, texts=[text])
    assert found == []
    asked = {t: p for t, p in db.log if p}
    for query in (
        mig._ACL_RELATION_SQL,
        mig._ACL_OWNER_SQL,
        mig._ACL_FUNCTION_SQL,
        mig._ACL_SCHEMA_SQL,
    ):
        keys = asked[query]
        assert (keys["changed_fn"], keys["changed_rel"], keys["changed_schema"]) == ([1], [2], [3])
        assert (keys["kept_fn"], keys["kept_rel"], keys["kept_schema"]) == ([4], [5], [6])
        assert keys["managed_fn"] == ["audit_guard"]
        assert set(keys["managed_rel"]) == set(mig.GRANTS) | {"schema_migrations"}
        assert keys["schema"] == "s"


def test_the_ownership_check_before_the_files_gets_the_relation_names_and_the_function_names_apart():
    """`_refuse_foreign_owned` asks about relations with the relation names and about functions with the function
    names. Killed by: mutants OA4 (the function half gets no names) and MC1 (it gets the relation names)."""
    db = _Db()
    text = "CREATE OR REPLACE FUNCTION audit_guard() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END $$;"
    mig._refuse_foreign_owned(db, "s", [text])
    ((schema_a, relations, schema_b, functions),) = [
        p for t, p in db.log if t == mig._FOREIGN_OWNED_SQL
    ]
    assert (schema_a, schema_b) == ("s", "s")
    assert functions == ["audit_guard"]
    assert set(relations) == set(mig.GRANTS) | {"schema_migrations"}


def test_a_long_list_is_cut_with_a_count_of_what_was_left_out():
    """A refusal lists at most `_PROBLEMS_SHOWN` things and then says how many more there are (it used to stop without
    a word). Killed by: mutant SH1 (the count is left out)."""
    rows = [_relation(f"role_{i:02d}", "SELECT") for i in range(mig._PROBLEMS_SHOWN + 5)]
    found, _db = _problems({mig._ACL_RELATION_SQL: rows})
    assert len(found) == mig._PROBLEMS_SHOWN + 1 and found[-1] == "and 5 more"
    assert mig._shown(["a", "b"]) == "a; b" and mig._shown([]) == ""
    assert mig._shown(["a", "b", "c"], ", ", limit=2) == "a, b, and 1 more"
    assert mig._shown(iter(["a", "b"]), limit=2) == "a; b"


def test_a_function_is_written_for_the_revoke_with_quoted_names():
    assert mig._routine_name("s", "f", "") == '"s"."f"()'
    assert mig._routine_name('a"b', "F x", "integer") == '"a""b"."F x"(integer)'


# --- who holds the migration lock ----------------------------------------------------------------------------------------


class _LockDb(_Db):
    """A connection on which the wait for the migration lock runs out."""

    def transaction(self):
        return contextlib.nullcontext()

    def execute(self, query, params=None):
        if isinstance(query, str) and query.startswith("SELECT pg_advisory_xact_lock"):
            self.log.append((query, params))
            raise pg_errors.LockNotAvailable("made up: the wait ran out")
        return super().execute(query, params)


def test_a_lock_held_by_a_prepared_transaction_is_said_so_with_what_finishes_it():
    """No session holds the lock, and a lock row without a session exists: a prepared transaction holds it. The message
    says so, lists the prepared transactions of the database and the two statements that finish one, and does not tell
    the reader to end a session (there is none). Killed by: mutant LW8 (a lock without a session is not looked for)."""
    db = _LockDb(
        {
            mig._LOCK_HOLDER_SQL: [],
            mig._LOCK_PREPARED_SQL: [(1,)],
            mig._PREPARED_SQL: [("nightly\nbatch", "etl", "2026-01-01 00:00:00+00")],
        }
    )
    with pytest.raises(ConfigError, match="a prepared transaction holds it") as e:
        mig._take_the_lock(db, 3)
    text = str(e.value)
    assert "migrate waited 3 seconds for the migration lock and gave up" in text
    assert "nightly\\nbatch" in text and "\n" not in text, (
        "a control character is written as an escape"
    )
    assert "(owner etl, prepared 2026-01-01 00:00:00+00)" in text
    assert "ROLLBACK PREPARED" in text and "COMMIT PREPARED" in text
    assert "Nothing was changed." in text and "pg_terminate_backend" not in text


@pytest.mark.parametrize("prepared", [[], [(0,)]])
def test_a_lock_holder_that_cannot_be_seen_at_all_is_still_called_a_session_this_login_cannot_see(
    prepared,
):
    """No session row and no lock row without a session: the old words stay. Pin."""
    db = _LockDb({mig._LOCK_HOLDER_SQL: [], mig._LOCK_PREPARED_SQL: prepared})
    with pytest.raises(ConfigError, match="a session this login cannot see holds it") as e:
        mig._take_the_lock(db, 3)
    assert "prepared transaction" not in str(e.value)
    assert mig._PREPARED_SQL not in [t for t, _ in db.log]
