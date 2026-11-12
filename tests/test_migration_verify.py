"""`verify` without a database: what `_judge` makes of hand-built rows, the words of every problem line, the order of the
printed statements, and the checks on the query texts (ticket P3a-2, section 3). The real-server halves are in
`tests/test_migration_verify_pg.py`. Rows are made up; no name here is a real role."""

from __future__ import annotations

import ast
import re
from collections import namedtuple
from pathlib import Path

import pytest

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migration_verify as v
from hadavin_sdk.store.migrate import GRANTS
from tests.test_migration_steps import harness  # noqa: F401  (the fixture: `migrate` on made-up files and a stub)

SCHEMA = "app"
NAMED = {"rt": "runtime", "po": "portal", "pu": "purge"}
FAMILY = ["mig"]

_SUBJ = namedtuple(
    "S",
    "start_role member_of uses_rights_at_once rolsuper rolcreaterole rolcreatedb rolbypassrls rolreplication",
)
_MEM = namedtuple("M", "member role_name grantor admin_option inherit_option set_option")
_ITEM = namedtuple(
    "I",
    "kind relkind schema system name sub owner family_owned definer row_type extension extension_owner "
    "extension_family_owned grantee grantee_is_subject grantee_is_named owner_item privilege_type is_grantable "
    "grantor grantor_is_owner",
)
_OWN = namedtuple("O", "deptype catalog objid objsubid role described temporary")
_DEF = namedtuple(
    "D", "kind schema set_for set_for_family grantee grantee_is_subject privilege_type is_grantable"
)


def subj(start, member_of=None, at_once=True, **flags):
    return _SUBJ(
        start,
        member_of or start,
        at_once,
        flags.get("rolsuper", False),
        flags.get("rolcreaterole", False),
        flags.get("rolcreatedb", False),
        flags.get("rolbypassrls", False),
        flags.get("rolreplication", False),
    )


def mem(member, role, grantor="boss"):
    return _MEM(member, role, grantor, False, True, True)


def item(**kw):
    base = {
        "kind": "table", "relkind": "r", "schema": SCHEMA, "system": False, "name": "t", "sub": "", "owner": "mig", "family_owned": True,
        "definer": False, "row_type": False, "extension": None, "extension_owner": None, "extension_family_owned": None,
        "grantee": None, "grantee_is_subject": False, "grantee_is_named": False, "owner_item": False, "privilege_type": "SELECT",
        "is_grantable": False, "grantor": "mig", "grantor_is_owner": True,
    }  # fmt: skip
    base.update(kw)
    return _ITEM(**base)


def own(**kw):
    base = {
        "deptype": "o",
        "catalog": "pg_class",
        "objid": 1,
        "objsubid": 0,
        "role": "rt",
        "described": "table x",
        "temporary": False,
    }
    base.update(kw)
    return _OWN(**base)


def dflt(**kw):
    base = {"kind": "r", "schema": None, "set_for": "mig", "set_for_family": True, "grantee": "x", "grantee_is_subject": False,
                "privilege_type": "SELECT", "is_grantable": False}  # fmt: skip
    base.update(kw)
    return _DEF(**base)


# The schema of the run holds the usable-schema item every clean database has.
USAGE = item(kind="schema", relkind="", name="", owner="mig", grantee=None, privilege_type="USAGE")


def rows(
    subjects=None,
    items=None,
    memberships=(),
    owned=(),
    defaults=(),
    family=None,
    db_owner="dbo",
    usage=True,
):
    subjects = [subj(n) for n in NAMED] if subjects is None else subjects
    its = list(items or [])
    if usage:
        its.append(USAGE)
    return v.Rows(
        160015, db_owner, tuple(v.KNOWN_ACL_COLUMNS), tuple(subjects),
        tuple(family if family is not None else [subj("mig")]), tuple(memberships), tuple(its), tuple(owned), tuple(defaults),
    )  # fmt: skip


def judge(r, named=None, reviewed=frozenset(), managed_functions=("door",)):
    return v._judge(
        r,
        named_roles=named or NAMED,
        family=FAMILY,
        grant_map=GRANTS,
        schema=SCHEMA,
        managed_relations=[*GRANTS, "schema_migrations"],
        managed_functions=list(managed_functions),
        reviewed_definers=reviewed,
    )


def kinds(problems):
    return sorted({p.kind for p in problems})


# One case per problem kind: (rows, the kind it must produce).
CASES = {
    "flag": lambda: rows(subjects=[subj("rt", rolcreatedb=True), subj("po"), subj("pu")]),
    "built_in_role": lambda: rows(
        subjects=[subj("rt"), subj("rt", "pg_read_server_files"), subj("po"), subj("pu")],
        memberships=[mem("rt", "pg_read_server_files")],
    ),
    "can_act_as_family": lambda: rows(
        subjects=[subj("rt"), subj("rt", "mig"), subj("po"), subj("pu")],
        memberships=[mem("rt", "mig")],
    ),
    "named_roles_overlap": lambda: rows(
        subjects=[subj("rt"), subj("rt", "po"), subj("po"), subj("pu")],
        memberships=[mem("rt", "po")],
    ),
    "owns": lambda: rows(owned=[own()]),
    "right": lambda: rows(
        items=[
            item(
                schema="other",
                name="secret",
                grantee="rt",
                grantee_is_subject=True,
                grantee_is_named=True,
            )
        ]
    ),
    "grant_option": lambda: rows(
        items=[
            item(
                name="runs",
                grantee="rt",
                grantee_is_subject=True,
                privilege_type="SELECT",
                is_grantable=True,
            )
        ]
    ),
    "definer_callable": lambda: rows(
        items=[
            item(
                kind="function",
                relkind="",
                name="door",
                sub="q text",
                definer=True,
                privilege_type="EXECUTE",
            )
        ]
    ),
    "unread_catalog": lambda: rows(owned=[own(deptype="a", catalog="pg_event_trigger", role="rt")]),
    "unread_relation_kind": lambda: rows(
        items=[item(kind="relation of an unread kind", relkind="c")]
    ),
    "foreign_owner": lambda: rows(
        items=[
            item(
                name="runs",
                owner="third",
                family_owned=False,
                grantor="third",
                grantee="third",
                owner_item=True,
            )
        ]
    ),
    "other_grantee": lambda: rows(items=[item(name="runs", grantee="third")]),
    "everyone": lambda: rows(items=[item(name="runs")]),
    "object_grant_option": lambda: rows(
        items=[item(name="runs", grantee="third", is_grantable=True)]
    ),
    "definer_unreviewed": lambda: rows(
        items=[
            item(
                kind="function",
                relkind="",
                name="door",
                sub="",
                definer=True,
                grantee="mig",
                owner_item=True,
                privilege_type="EXECUTE",
            )
        ]
    ),
    "schema_right": lambda: rows(
        items=[item(kind="schema", relkind="", name="", privilege_type="CREATE")]
    ),
    "default_for_named": lambda: rows(defaults=[dflt(grantee="rt", grantee_is_subject=True)]),
    "default_for_everyone": lambda: rows(defaults=[dflt(grantee=None)]),
    "default_for_other": lambda: rows(defaults=[dflt(grantee="third")]),
    "default_unknown_kind": lambda: rows(defaults=[dflt(kind="L")]),
    "missing_schema_usage": lambda: rows(usage=False),
}


def test_a_clean_state_has_no_problem():
    assert judge(rows()) == []


@pytest.mark.parametrize("kind", v.PROBLEM_KINDS)
def test_judge_makes_the_problem_kind(kind):
    got = judge(CASES[kind]())
    assert kind in kinds(got), [p.line() for p in got]


def test_every_problem_kind_is_produced():
    assert set(CASES) == set(v.PROBLEM_KINDS)
    assert len(v.PROBLEM_KINDS) == len(set(v.PROBLEM_KINDS)) == 21
    produced = {p.kind for build in CASES.values() for p in judge(build())}
    assert produced == set(v.PROBLEM_KINDS)


def test_every_problem_kind_has_a_line_form():
    for kind in v.PROBLEM_KINDS:
        p = v.Problem(kind, "s", "o", "d", "r", "SELECT", "g", owner="w", via="x", word="table")
        text = p.line()
        assert text and not re.search(r"[\x00-\x08\x0b-\x1f\x7f]", text), (kind, text)


def test_a_line_escapes_control_characters_in_names():
    p = v.Problem(
        "everyone", "a\nb", "t\x1b[2J", "", v.EVERYONE, "SELECT", "g", word="table", by_hand="name"
    )
    assert "\n" not in p.line() and "\x1b" not in p.line()
    assert "NOT THIS PACKAGE" not in p.line()


def test_a_statement_with_a_non_plain_name_is_not_printed_and_the_line_says_so():
    got = judge(rows(items=[item(name="we\nird")]))
    assert [p.fix for p in got] == [""] and got[0].by_hand == "name"
    assert "by hand" in got[0].line() and "\n" not in got[0].line()


def test_the_everyone_problem_prints_the_revoke_of_the_plan():
    (p,) = judge(rows(items=[item(name="audit_entries")]))
    assert p.line() == (
        'table app.audit_entries: everyone (PUBLIC) has SELECT. To remove: REVOKE SELECT ON TABLE "app"."audit_entries" FROM PUBLIC;'
    )


def test_the_grant_map_is_what_a_named_role_may_hold():
    ok = [
        item(
            name="runs",
            grantee="rt",
            grantee_is_subject=True,
            grantee_is_named=True,
            privilege_type=p,
            grantor="mig",
        )
        for p in ("SELECT", "INSERT", "UPDATE")
    ]
    ok.append(
        item(
            name="runs",
            grantee="po",
            grantee_is_subject=True,
            grantee_is_named=True,
            privilege_type="SELECT",
        )
    )
    ok.append(item(kind="column", name="runs", sub="state", grantee="pu", grantee_is_subject=True,
                   grantee_is_named=True, privilege_type="SELECT"))  # fmt: skip
    assert judge(rows(items=ok)) == []
    bad = item(
        name="runs",
        grantee="po",
        grantee_is_subject=True,
        grantee_is_named=True,
        privilege_type="INSERT",
    )
    assert kinds(judge(rows(items=[bad]))) == ["right"]
    other_schema = item(
        schema="other", name="runs", grantee="rt", grantee_is_subject=True, grantee_is_named=True
    )
    assert kinds(judge(rows(items=[other_schema]))) == ["right"]


def test_the_rights_on_a_map_table_before_the_run_are_repaired_by_the_run_only_for_the_migration_roles_grants():
    mine = item(
        name="runs",
        grantee="rt",
        grantee_is_subject=True,
        grantee_is_named=True,
        privilege_type="DELETE",
        grantor="mig",
    )
    theirs = item(name="runs", grantee="rt", grantee_is_subject=True, grantee_is_named=True, privilege_type="DELETE", grantor="boss",
                  grantor_is_owner=False)  # fmt: skip
    assert [p.repaired_by_run for p in judge(rows(items=[mine]))] == [True]
    assert [p.repaired_by_run for p in judge(rows(items=[theirs]))] == [False]


def test_a_group_reached_by_two_named_roles_is_judged_for_each():
    subjects = [subj("rt"), subj("rt", "grp"), subj("po"), subj("po", "grp"), subj("pu")]
    grp_insert = item(name="runs", grantee="grp", grantee_is_subject=True, privilege_type="INSERT")
    got = judge(
        rows(
            subjects=subjects, items=[grp_insert], memberships=[mem("rt", "grp"), mem("po", "grp")]
        )
    )
    assert [(p.kind, p.role, p.via) for p in got] == [("right", "po", "grp")]
    assert "can use it through the role grp, INSERT" in got[0].line()
    assert got[0].fix == 'REVOKE "grp" FROM "po" GRANTED BY "boss";'


def test_a_built_in_role_is_one_membership_statement_however_many_roles_it_brings():
    subjects = [
        subj("rt"),
        subj("rt", "pg_monitor"),
        subj("rt", "pg_read_all_stats"),
        subj("po"),
        subj("pu"),
    ]
    got = judge(rows(subjects=subjects, memberships=[mem("rt", "pg_monitor", "postgres")]))
    assert len(got) == 2
    assert v.statements_for(got) == ['REVOKE "pg_monitor" FROM "rt" GRANTED BY "postgres";']


def test_the_database_owner_reaches_pg_database_owner_and_gets_no_statement():
    subjects = [subj("rt"), subj("rt", "dbo"), subj("po"), subj("pu")]
    got = judge(rows(subjects=subjects, memberships=[mem("rt", "dbo")]))
    by_owner = [p for p in got if p.via == "pg_database_owner"]
    assert [p.by_hand for p in by_owner] == ["database_owner"] and v.statements_for(by_owner) == []


def test_an_extension_member_is_refused_with_no_statement():
    ext = item(kind="view", relkind="v", schema="public", name="pg_stat_statements", owner="postgres", family_owned=False,
               extension="pg_stat_statements", extension_owner="postgres", extension_family_owned=False)  # fmt: skip
    (p,) = [p for p in judge(rows(items=[ext])) if p.kind == "everyone"]
    assert p.by_hand == "extension" and p.fix == "" and "ALTER EXTENSION" in p.line()
    owned = item(kind="view", relkind="v", schema="public", name="x", owner="mig", extension="e", extension_owner="mig",
                 extension_family_owned=True)  # fmt: skip
    assert [p.by_hand for p in judge(rows(items=[owned])) if p.kind == "everyone"] == [""]


def test_a_row_type_may_be_used_by_everyone_and_a_plain_type_may_not():
    row = item(kind="type", relkind="r", name="runs", row_type=True, privilege_type="USAGE")
    plain = item(kind="type", relkind="", name="mood", privilege_type="USAGE")
    assert judge(rows(items=[row])) == []
    assert kinds(judge(rows(items=[plain]))) == ["everyone"]


def test_a_reviewed_definer_is_excused_only_with_its_exact_key():
    fn = item(kind="function", relkind="", name="door", sub="q text", definer=True, grantee="mig", owner_item=True,
              privilege_type="EXECUTE")  # fmt: skip
    assert kinds(judge(rows(items=[fn]))) == ["definer_unreviewed"]
    assert judge(rows(items=[fn]), reviewed=frozenset({(SCHEMA, "door", "q text")})) == []
    assert kinds(judge(rows(items=[fn]), reviewed=frozenset({("other", "door", "q text")}))) == [
        "definer_unreviewed"
    ]
    assert kinds(judge(rows(items=[fn]), reviewed=frozenset({(SCHEMA, "door", "")}))) == [
        "definer_unreviewed"
    ]


def test_the_default_everyone_function_and_type_entry_for_all_schemas_is_not_refused():
    ok = [
        dflt(kind="f", grantee=None, privilege_type="EXECUTE"),
        dflt(kind="T", grantee=None, privilege_type="USAGE"),
    ]
    assert judge(rows(defaults=ok)) == []
    one_schema = dflt(kind="f", schema="app", grantee=None, privilege_type="EXECUTE")
    assert kinds(judge(rows(defaults=[one_schema]))) == ["default_for_everyone"]


def test_a_default_right_statement_names_the_role_the_schema_and_the_kind():
    (p,) = judge(rows(defaults=[dflt(schema="app", grantee="third")]))
    assert (
        p.fix
        == 'ALTER DEFAULT PRIVILEGES FOR ROLE "mig" IN SCHEMA "app" REVOKE SELECT ON TABLES FROM "third";'
    )


def test_statements_are_ordered_by_group_and_without_duplicates():
    problems = [
        v.Problem("flag", "", "", "", "rt", "CREATEDB", "", fix="ALTER ROLE rt NOCREATEDB;"),
        v.Problem(
            "definer_callable",
            "a",
            "f",
            "",
            v.EVERYONE,
            "EXECUTE",
            "g",
            fix="ALTER FUNCTION f() SECURITY INVOKER;",
        ),
        v.Problem(
            "grant_option",
            "a",
            "t",
            "",
            "x",
            "SELECT",
            "mig",
            grantor_is_owner=True,
            fix="REVOKE GRANT OPTION owner;",
        ),
        v.Problem(
            "grant_option",
            "a",
            "t",
            "",
            "x",
            "SELECT",
            "boss",
            fix="SET ROLE boss; REVOKE GRANT OPTION; RESET ROLE;",
        ),
        v.Problem(
            "everyone",
            "a",
            "t",
            "",
            v.EVERYONE,
            "SELECT",
            "mig",
            grantor_is_owner=True,
            fix="REVOKE owner;",
        ),
        v.Problem(
            "everyone",
            "a",
            "t",
            "",
            v.EVERYONE,
            "SELECT",
            "boss",
            fix="SET ROLE boss; REVOKE other; RESET ROLE;",
        ),
        v.Problem(
            "default_for_other", "", "", "r", "x", "SELECT", "", fix="ALTER DEFAULT PRIVILEGES ...;"
        ),
        v.Problem(
            "built_in_role",
            "",
            "",
            "",
            "rt",
            "MEMBER",
            "g",
            fix="REVOKE pg_x FROM rt GRANTED BY g;",
        ),
        v.Problem("owns", "", "t", "", "rt", "OWNER", "", by_hand="owner"),
    ]
    got = v.statements_for(problems + problems)
    assert got == [
        "REVOKE pg_x FROM rt GRANTED BY g;",
        "ALTER DEFAULT PRIVILEGES ...;",
        "SET ROLE boss; REVOKE other; RESET ROLE;",
        "SET ROLE boss; REVOKE GRANT OPTION; RESET ROLE;",
        "REVOKE owner;",
        "REVOKE GRANT OPTION owner;",
        "ALTER ROLE rt NOCREATEDB;",
        "ALTER FUNCTION f() SECURITY INVOKER;",
    ]
    assert [p.order for p in problems] == [6, 7, 5, 3, 4, 2, 1, 0, 8]


def test_statements_are_split_into_the_packages_own_and_other_applications():
    mine = v.Problem("everyone", "app", "t", "", v.EVERYONE, "SELECT", "mig", fix="REVOKE mine;")
    other = v.Problem(
        "everyone",
        "elsewhere",
        "t",
        "",
        v.EVERYONE,
        "SELECT",
        "mig",
        fix="REVOKE theirs;",
        outside_package=True,
    )
    assert v.statement_blocks([other, mine]) == (["REVOKE mine;"], ["REVOKE theirs;"])
    assert other.line().startswith("NOT THIS PACKAGE'S OBJECT: ")


# --- the checks on the query texts ----------------------------------------------------------------------------------

_RELATIONS = [
    "pg_attribute",
    "pg_class",
    "pg_namespace",
    "pg_type",
    "pg_roles",
    "pg_auth_members",
    "pg_proc",
    "pg_database",
    "pg_foreign_data_wrapper",
    "pg_foreign_server",
    "pg_language",
    "pg_largeobject_metadata",
    "pg_largeobject",
    "pg_parameter_acl",
    "pg_tablespace",
    "pg_depend",
    "pg_extension",
    "pg_shdepend",
    "pg_authid",
    "pg_default_acl",
]
_UNQUALIFIED = re.compile(r"(?<![\w.])(pg_[a-z_]+)\b(?!\s*\()")


def unqualified_catalog_names(text: str) -> list[str]:
    return [m for m in _UNQUALIFIED.findall(text) if m in _RELATIONS]


@pytest.mark.parametrize("name", sorted(v.QUERY_TEXTS))
def test_every_catalog_name_in_the_queries_is_qualified(name):
    assert unqualified_catalog_names(v.QUERY_TEXTS[name]) == []


def test_the_qualified_name_check_catches_a_missing_prefix():
    broken = v.Q2.replace("pg_catalog.pg_depend xd", "pg_depend xd", 1)
    assert broken != v.Q2 and unqualified_catalog_names(broken) == ["pg_depend"]


def test_the_new_module_never_names_the_session_role_or_the_session_schema_or_the_privilege_functions():
    text = Path(v.__file__).read_text(encoding="utf-8")
    for word in ("current_user", "session_user", "current_schema"):
        assert word not in text, word
    for word in (
        "has_table_privilege",
        "has_column_privilege",
        "has_sequence_privilege",
        "has_schema_privilege",
        "pg_has_role",
    ):
        assert word not in text, word


def test_every_live_acl_column_is_read_by_a_query():
    assert len(v.KNOWN_ACL_COLUMNS) == 14
    for column, (query, fragment) in v.KNOWN_ACL_COLUMNS.items():
        catalog = column.split(".")[0]
        if query == "none":
            assert column == "pg_init_privs.initprivs"
            continue
        text = v.QUERY_TEXTS[query]
        assert fragment in text, column
        assert f"pg_catalog.{catalog}" in text, column


def test_judge_reads_only_columns_the_queries_return():
    tree = ast.parse(Path(v.__file__).read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_judge")
    row_variables = {"r", "it", "d", "i", "m"}
    used = {
        n.attr
        for n in ast.walk(fn)
        if isinstance(n, ast.Attribute)
        and isinstance(n.value, ast.Name)
        and n.value.id in row_variables
    }
    words = set(re.findall(r"\w+", " ".join(v.QUERY_TEXTS.values())))
    assert used and used <= words, sorted(used - words)


def test_a_server_below_16_is_refused_before_anything_else():
    with pytest.raises(ConfigError, match="needs PostgreSQL 16 or later"):
        v.check_version(150004, "15.4")
    v.check_version(160000)


def test_the_minor_label_of_a_server_below_16_is_the_server_number_split_in_two():
    """`150004` is PostgreSQL 15.4, not 15.4 by accident of a shorter number: the label is `version % 10000`."""
    with pytest.raises(ConfigError, match=r"PostgreSQL 15\.4;"):
        v.check_version(150004)
    with pytest.raises(ConfigError, match=r"PostgreSQL 15\.12;"):
        v.check_version(150012)


def test_the_extension_refusal_names_the_way_out_and_prints_no_statement():
    p = v.Problem(
        kind="right",
        schema="public",
        obj="pg_stat_statements",
        detail="",
        role="EVERYONE",
        right="SELECT",
        grantor="postgres",
        owner="postgres",
        extension="pg_stat_statements",
        by_hand="extension",
        word="view",
    )
    text = p.line()
    assert "a database of its own for this package" in text
    assert "the extension installed in another schema" in text
    assert "no statement is printed" in text


def test_the_self_check_names_an_unknown_and_a_missing_column():
    have = list(v.KNOWN_ACL_COLUMNS)
    v.check_acl_columns(have)
    with pytest.raises(ConfigError, match=r"does not read \(pg_made_up.acl\)"):
        v.check_acl_columns([*have, "pg_made_up.acl"])
    with pytest.raises(ConfigError, match=r"does not have \(pg_class.relacl\)"):
        v.check_acl_columns([c for c in have if c != "pg_class.relacl"])


# --- the commit outcome (ticket P3a-2, 4.1 step 7): refused or unknown ----------------------------------------------------


class _FakeCommitError(Exception):
    def __init__(self, sqlstate):
        super().__init__("made-up error at commit")
        self.sqlstate = sqlstate


def _fake_db(*, closed=False, status=None):
    import types

    from psycopg.pq import TransactionStatus

    status = TransactionStatus.IDLE if status is None else status
    return types.SimpleNamespace(
        closed=closed, info=types.SimpleNamespace(transaction_status=status)
    )


@pytest.mark.parametrize(
    "state",
    [
        "22001",
        "23503",
        "23505",
        "40001",
        "40P01",
        "42P01",
        "44000",
        "P0001",
        "55P03",
        "55000",
        "55006",
        "57014",
    ],
)
def test_commit_outcome_classes_refused(state):
    """A live session in IDLE state with an SQLSTATE of a refusing class: the server rolled back, nothing was kept."""
    from hadavin_sdk.store import migrate as mig

    assert mig._commit_outcome(_FakeCommitError(state), _fake_db()) == "refused"


@pytest.mark.parametrize(
    "state",
    [
        "08006",
        "08000",
        "57P01",
        "57P02",
        "57P03",
        "53100",
        "58030",
        "XX000",
        "25P02",
        "2D000",
        "0A000",
        "40003",
    ],
)
def test_commit_outcome_classes_unknown_by_code(state):
    """Connection loss, shutdown, resource, system and internal classes, and any code outside the list: unknown (the
    commit may or may not have happened)."""
    from hadavin_sdk.store import migrate as mig

    assert mig._commit_outcome(_FakeCommitError(state), _fake_db()) == "unknown"


def test_commit_outcome_classes_unknown_without_a_code_a_closed_connection_or_a_transaction_state():
    from psycopg.pq import TransactionStatus

    from hadavin_sdk.store import migrate as mig

    assert mig._commit_outcome(_FakeCommitError(None), _fake_db()) == "unknown"
    assert mig._commit_outcome(_FakeCommitError(""), _fake_db()) == "unknown"
    assert mig._commit_outcome(ValueError("no sqlstate attribute"), _fake_db()) == "unknown"
    assert mig._commit_outcome(_FakeCommitError("23503"), _fake_db(closed=True)) == "unknown"
    for status in (
        TransactionStatus.INTRANS,
        TransactionStatus.INERROR,
        TransactionStatus.ACTIVE,
        TransactionStatus.UNKNOWN,
    ):
        assert (
            mig._commit_outcome(_FakeCommitError("23503"), _fake_db(status=status)) == "unknown"
        ), status


# --- every catalog read that `migrate` can reach is pinned ---------------------------------------------------------------

# Runs once at the start, before any file and before a single statement of the run could have changed the session; when
# it fails it only asks the server who holds the lock. A catalog name here is found in `pg_catalog` first.
_UNPINNED_BEFORE_ANY_FILE = frozenset({"_take_the_lock"})
_UNQUALIFIED_CATALOG = re.compile(r"(?<![\w.\"])pg_(?!catalog\.|temp\b)\w+")


def _is_pinned_with(node: ast.AST) -> bool:
    return isinstance(node, ast.With) and any(
        isinstance(i.context_expr, ast.Call)
        and isinstance(i.context_expr.func, ast.Name)
        and i.context_expr.func.id == "pinned_read"
        for i in node.items
    )


def _calls_with_pinning(function: ast.FunctionDef):
    """Every `ast.Call` of the function, with whether a `with pinned_read(...)` block is around it."""

    def walk(node: ast.AST, pinned: bool):
        for child in ast.iter_child_nodes(node):
            inside = pinned or (_is_pinned_with(node) and child in node.body)
            if isinstance(child, ast.Call):
                yield child, inside
            yield from walk(child, inside)

    yield from walk(function, False)


def test_every_runner_catalog_read_is_pinned():
    """Every statement that `migrate()` can reach and that names a catalog object without `pg_catalog.` runs inside
    `with pinned_read(...)` (a temporary table or a function a file made cannot answer in its place), either in the
    function itself or because every call of the function is itself inside such a block. A statement with no unqualified
    catalog name (every name qualified, or only keywords) needs no block. Killed by: a call site of the read-backs, the
    role questions, the ownership read or the step-4 read that is moved out of `pinned_read`."""
    from hadavin_sdk.store import migrate as mig

    tree = ast.parse(Path(mig.__file__).read_text(encoding="utf-8"))
    functions = {f.name: f for f in tree.body if isinstance(f, ast.FunctionDef)}
    constants = {n: getattr(mig, n) for n in dir(mig) if isinstance(getattr(mig, n), str)}
    # which functions `migrate` can reach, and every call site of each (function, pinned or not)
    reached, queue, sites = set(), ["migrate"], {}
    while queue:
        name = queue.pop()
        if name in reached:
            continue
        reached.add(name)
        for call, pinned in _calls_with_pinning(functions[name]):
            target = call.func.id if isinstance(call.func, ast.Name) else None
            if target in functions:
                sites.setdefault(target, []).append((name, pinned))
                queue.append(target)
    assert {
        "_read_back",
        "_refuse_privileged_role",
        "_recheck_roles",
        "_revoke_default_execute",
    } <= reached
    # a function is "pinned by its callers" when every call of it is inside a block or inside another such function
    by_callers: set[str] = set()
    changed = True
    while changed:
        changed = False
        for target, calls in sites.items():
            if target not in by_callers and all(p or caller in by_callers for caller, p in calls):
                by_callers.add(target)
                changed = True
    loose = []
    for name in sorted(reached):
        if name in _UNPINNED_BEFORE_ANY_FILE or name in by_callers:
            continue
        for call, pinned in _calls_with_pinning(functions[name]):
            if not (
                isinstance(call.func, ast.Attribute) and call.func.attr == "execute" and call.args
            ):
                continue
            first = call.args[0]
            text = (
                constants.get(first.id, "") if isinstance(first, ast.Name) else ast.unparse(first)
            )
            if _UNQUALIFIED_CATALOG.search(text) and not pinned:
                loose.append(f"{name} line {call.lineno}: {text[:60]!r}")
    assert loose == [], "a catalog read outside `pinned_read`: " + "; ".join(loose)
    # the reads that must be pinned are really there to be found (the test is not vacuous)
    assert "_check_read_back" in reached
    assert {"_refuse_privileged_role", "_refuse_foreign_owned", "_recheck_roles"} <= by_callers


def test_the_pinned_read_check_finds_a_read_that_is_not_pinned():
    """The check above sees the difference between a pinned and a loose read (a self-test of the helpers)."""
    source = (
        "def f(db):\n    db.execute('SELECT 1 FROM pg_roles')\n"
        "def g(db):\n    with pinned_read(db, ()):\n        db.execute('SELECT 1 FROM pg_roles')\n"
    )
    tree = ast.parse(source)
    flat = [
        (c.func.attr, p) for c, p in _calls_with_pinning(tree.body[0]) if hasattr(c.func, "attr")
    ]
    pinned = [
        (c.func.attr, p) for c, p in _calls_with_pinning(tree.body[1]) if hasattr(c.func, "attr")
    ]
    assert flat == [("execute", False)] and pinned == [("execute", True)]
    assert _UNQUALIFIED_CATALOG.search("SELECT 1 FROM pg_roles")
    assert not _UNQUALIFIED_CATALOG.search("SELECT 1 FROM pg_catalog.pg_roles")


def test_the_rights_table_equals_what_apply_grants_is_called_with(harness, monkeypatch):  # noqa: F811
    """The rights `verify` allows a named role (`_rights_for`, and the purge columns of `_allowed_for`) are exactly what
    `migrate` gives that role: the functions step 4 passes to `_apply_grants` are evaluated on every relation of the
    grant map and compared. A right given by step 4 that `verify` would call excess (or the other way round) fails here."""
    from hadavin_sdk.store import migrate as mig

    calls = []
    monkeypatch.setattr(
        mig,
        "_apply_grants",
        lambda db, schema, role, privileges, columns=None: calls.append(
            (role, privileges, columns)
        ),
    )
    err, _opened, _rec, _applied = harness(
        runtime_role="rt_role", portal_role="pt_role", purge_role="pu_role"
    )
    assert err is None, err
    assert [c[0] for c in calls] == ["rt_role", "pu_role", "pt_role"]
    kinds = {"rt_role": "runtime", "pu_role": "purge", "pt_role": "portal"}
    for role, privileges, columns in calls:
        for name, g in GRANTS.items():
            given = frozenset(w.strip() for w in privileges(g).split(",") if w.strip())
            assert given == v._rights_for(kinds[role], g), (role, name)
            if kinds[role] == "purge":
                assert columns is not None and tuple(columns(g)) == g.purge_cols, name
            else:
                assert columns is None, (role, name)


def _between_markers(text: str) -> list[str]:
    start, stop = text.index("[promise table]"), text.index("[end of promise table]")
    lines = (line.strip() for line in text[start + len("[promise table]") : stop].splitlines())
    return [line for line in lines if line]


def test_the_promise_table_is_the_same_in_the_docstring_and_the_changelog():
    """Promise table, rows 1 to 3: the module text of `migrate.py` and the CHANGELOG item hold the same words between the
    two marker lines (leading space and blank lines apart), and each row names its word. Killed by: mutants that edit
    one copy only (the V mutants of the promise table, `V63` and `V64`)."""
    from hadavin_sdk.store import migrate as mig

    root = Path(__file__).resolve().parents[1]
    in_code = _between_markers(mig.__doc__)
    in_log = _between_markers((root / "CHANGELOG.md").read_text(encoding="utf-8"))
    assert in_code == in_log
    assert len(in_code) == 5 and in_code[2].endswith("| STOPPED |")
    assert in_code[3].endswith("| STOPPED, for lasting rights only |")
    assert in_code[4].endswith("| DETECTED, not stopped |")
    assert 'never in "applied"' in in_code[4]
    assert (root / "CHANGELOG.md").read_text(encoding="utf-8").count("[promise table]") == 1
    assert "What migrate promises" in (root / "CHANGELOG.md").read_text(encoding="utf-8")
    assert any("What migrate promises" in str(c) for c in mig._after_commit.__code__.co_consts)
    # Row 1 names the test of the shipped files (ticket 7.7) as built, and that test exists: the text and the file
    # cannot drift apart (Issue 2)
    matrix = (root / "tests/test_migration_matrix.py").read_text(encoding="utf-8")
    assert "def test_the_shipped_files_give_each_role_exactly_the_map(" in matrix
    assert "NOT BUILT YET" not in in_code[2]
    assert "test_the_shipped_files_give_each_role_exactly_the_map" in in_code[2]


def test_usage_on_a_language_is_refused_for_everyone_only_when_the_migration_family_owns_it():
    """Everyone holds USAGE on a language by default; one the migration role family owns, in the schema of the run, is
    refused; one another role owns is the server's, not ours. (V12: the language clause is not skipped.)"""
    mine = judge(
        rows(items=[item(kind="language", relkind="", name="lang", privilege_type="USAGE")])
    )
    assert kinds(mine) == ["everyone"], [p.line() for p in mine]
    theirs = judge(
        rows(
            items=[
                item(
                    kind="language",
                    relkind="",
                    name="lang",
                    privilege_type="USAGE",
                    owner="third",
                    family_owned=False,
                )
            ]
        )
    )
    assert "everyone" not in kinds(theirs), [p.line() for p in theirs]


@pytest.mark.parametrize(
    ("right", "refused"), [("CREATE", True), ("CONNECT", False), ("TEMPORARY", False)]
)
def test_a_right_of_everyone_on_the_database_is_refused_only_beyond_connect_and_temporary(
    right, refused
):
    """CONNECT is expected and TEMPORARY is the server default; CREATE on the database is refused. (V14.)"""
    got = judge(
        rows(items=[item(kind="database", relkind="", schema="", name="db", privilege_type=right)])
    )
    assert (kinds(got) == ["everyone"]) is refused, [p.line() for p in got]


def test_an_object_of_pg_database_owner_is_the_familys_when_the_database_owner_is_in_the_family():
    """`pg_database_owner` stands for whoever owns the database; when that is the migration role, what it owns is the
    package's: a function it owns that everyone may call is refused as the family's, not left alone as foreign."""
    mine = judge(
        rows(
            db_owner="mig",
            items=[
                item(
                    kind="function",
                    relkind="",
                    name="door",
                    sub="",
                    owner="pg_database_owner",
                    family_owned=False,
                    privilege_type="EXECUTE",
                )
            ],
        )
    )
    assert kinds(mine) == ["everyone"], [p.line() for p in mine]
    theirs = judge(
        rows(
            db_owner="dbo",
            items=[
                item(
                    kind="function",
                    relkind="",
                    name="door",
                    sub="",
                    owner="pg_database_owner",
                    family_owned=False,
                    privilege_type="EXECUTE",
                )
            ],
        )
    )
    assert "everyone" not in kinds(theirs), [p.line() for p in theirs]


def test_a_shipped_table_name_does_not_make_a_view_of_that_name_allowed():
    """The grant map is keyed by kind: `runs` is a table there, so a view called `runs` that the runtime role may read is
    a right the map does not give (V31)."""
    table = judge(
        rows(
            items=[
                item(
                    name="runs",
                    grantee="rt",
                    grantee_is_subject=True,
                    grantee_is_named=True,
                    privilege_type="SELECT",
                )
            ]
        )
    )
    assert "right" not in kinds(table), [p.line() for p in table]
    view = judge(
        rows(
            items=[
                item(
                    kind="view",
                    relkind="v",
                    name="runs",
                    grantee="rt",
                    grantee_is_subject=True,
                    grantee_is_named=True,
                    privilege_type="SELECT",
                )
            ]
        )
    )
    assert "right" in kinds(view), [p.line() for p in view]


def test_usage_on_the_schema_through_a_group_that_does_not_inherit_is_not_usage():
    """A membership with no inheritance does not hand the group's rights to the member at once, so USAGE that only the
    group holds does not count: the role is reported as unable to use the schema (V35)."""

    def missing(at_once: bool) -> list[str]:
        got = judge(
            rows(
                usage=False,
                subjects=[subj("rt"), subj("rt", "grp", at_once=at_once), subj("po"), subj("pu")],
                items=[
                    item(
                        kind="schema",
                        relkind="",
                        name="",
                        owner="mig",
                        grantee="grp",
                        grantee_is_subject=True,
                        privilege_type="USAGE",
                    )
                ],
            )
        )
        return [p.role for p in got if p.kind == "missing_schema_usage"]

    assert "rt" not in missing(True)
    assert "rt" in missing(False)


def test_the_read_refuses_an_old_server_before_it_runs_a_query_that_needs_16(monkeypatch):
    """`_read` checks the version as soon as it has it: nothing after the version query is run on PostgreSQL 15 (V39)."""
    ran: list[str] = []

    def fetch(db, text, params=None, *, named=True):
        ran.append(text)
        if text == v.V2_SQL:
            return ((150004, "dbo"),)
        raise AssertionError("a query that needs version 16 was run on version 15")

    monkeypatch.setattr(v, "_fetch", fetch)
    with pytest.raises(ConfigError, match="needs PostgreSQL 16 or later"):
        v._read(object(), named=["rt"], family=["mig"], schema=SCHEMA, managed_functions=[])
    assert ran == [v.V2_SQL]


def test_the_read_runs_the_self_check_before_the_queries_that_use_the_columns(monkeypatch):
    """`_read` calls the self-check of the access-list columns right after it has them (V40): a server with a column this
    package does not know ends the read there, before the queries that read the access lists."""
    ran: list[str] = []

    def fetch(db, text, params=None, *, named=True):
        ran.append(text)
        if text == v.V2_SQL:
            return ((160000, "dbo"),)
        if text == v.Q0:
            return tuple((c,) for c in [*v.KNOWN_ACL_COLUMNS, "pg_made_up.acl"])
        raise AssertionError("a query that reads the access lists ran after a failed self-check")

    monkeypatch.setattr(v, "_fetch", fetch)
    with pytest.raises(ConfigError, match=r"does not read \(pg_made_up.acl\)"):
        v._read(object(), named=["rt"], family=["mig"], schema=SCHEMA, managed_functions=[])
    assert ran == [v.V2_SQL, v.Q0]


def test_a_right_for_a_built_in_role_is_not_counted_a_second_time_as_a_right():
    """A named role in `pg_monitor` is refused once, as a membership (S2); the rights of `pg_monitor` itself are the
    server's and are not listed again as rights of the named role (V43)."""
    got = judge(
        rows(
            subjects=[subj("rt"), subj("rt", "pg_monitor"), subj("po"), subj("pu")],
            memberships=[mem("rt", "pg_monitor")],
            items=[
                item(
                    name="secret",
                    grantee="pg_monitor",
                    grantee_is_subject=True,
                    privilege_type="SELECT",
                )
            ],
        )
    )
    assert kinds(got) == ["built_in_role"], [p.line() for p in got]


def test_no_statement_is_printed_for_a_right_on_a_system_object():
    """An object of `pg_catalog` or `information_schema` is the server's: the right is named and judged, but no REVOKE is
    printed for it, and the line says a person decides (V44)."""
    got = judge(
        rows(
            items=[
                item(
                    schema="pg_catalog",
                    system=True,
                    name="pg_made_up_table",
                    grantee="rt",
                    grantee_is_subject=True,
                    grantee_is_named=True,
                    privilege_type="UPDATE",
                )
            ]
        )
    )
    assert [p.kind for p in got] == ["right"], [p.line() for p in got]
    assert got[0].fix == "" and got[0].by_hand == "system"


def test_pinned_read_sets_the_two_limits_and_the_path_before_any_read_and_always_rolls_back():
    """The limits are set first, then the search path, then the caller reads; the block ends by rolling back (V48)."""
    from contextlib import contextmanager

    from hadavin_sdk.store import postgres as pg

    log: list[str] = []

    class _Db:
        @contextmanager
        def transaction(self):
            log.append("begin")
            try:
                yield
            except pg.Rollback:
                log.append("rollback")

        def execute(self, text):
            log.append(text)

    limits = ["SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '2s'"]
    with v.pinned_read(_Db(), limits):
        log.append("the read")
    assert log == [
        "begin",
        *limits,
        "SET LOCAL search_path = pg_catalog, pg_temp",
        "the read",
        "rollback",
    ]


def test_the_revoke_of_a_right_that_another_role_granted_acts_as_that_role():
    """A right recorded as granted by someone other than the owner is removed by the grantor (`SET ROLE <grantor>`), not
    by the owner, who would revoke nothing (V45)."""
    got = judge(
        rows(
            items=[
                item(
                    name="secret",
                    grantee="rt",
                    grantee_is_subject=True,
                    grantee_is_named=True,
                    grantor="third",
                    grantor_is_owner=False,
                    privilege_type="UPDATE",
                )
            ]
        )
    )
    assert [p.kind for p in got] == ["right"], [p.line() for p in got]
    assert got[0].fix.startswith('SET ROLE "third";') and got[0].fix.endswith("RESET ROLE;"), got[
        0
    ].fix
    owner_form = judge(
        rows(
            items=[
                item(
                    name="secret",
                    grantee="rt",
                    grantee_is_subject=True,
                    grantee_is_named=True,
                    privilege_type="UPDATE",
                )
            ]
        )
    )
    assert "SET ROLE" not in owner_form[0].fix, owner_form[0].fix


@pytest.mark.parametrize(("right", "refused"), [("USAGE", False), ("CREATE", True)])
def test_a_named_role_may_use_the_schema_but_not_create_in_it(right, refused):
    """The grant map gives a named role USAGE on a schema and nothing more. (SC9: USAGE refused too; SC14: CREATE let
    through.)"""
    got = judge(
        rows(
            items=[
                item(
                    kind="schema",
                    relkind="",
                    name="",
                    grantee="rt",
                    grantee_is_subject=True,
                    grantee_is_named=True,
                    privilege_type=right,
                )
            ]
        )
    )
    assert (kinds(got) == ["right"]) is refused, [p.line() for p in got]


def test_a_right_of_a_named_role_on_a_column_of_another_schema_is_refused():
    """The subject side is judged in every schema, columns included. (RA4: only the schema of the run.)"""
    got = judge(
        rows(
            items=[
                item(
                    kind="column",
                    schema="other",
                    name="secret",
                    sub="c",
                    grantee="rt",
                    grantee_is_subject=True,
                    grantee_is_named=True,
                )
            ]
        )
    )
    assert kinds(got) == ["right"], [p.line() for p in got]


def test_a_default_right_for_everyone_is_skipped_only_when_it_is_the_servers_own_pair():
    """For all schemas the server writes EXECUTE on functions and USAGE on types for everyone; those two pairs are not
    refused, any other pair is. (DP9: every right on a function or type is skipped.)"""
    own_pair = judge(rows(defaults=[dflt(kind="f", grantee=None, privilege_type="EXECUTE")]))
    assert "default_for_everyone" not in kinds(own_pair), [p.line() for p in own_pair]
    other_pair = judge(rows(defaults=[dflt(kind="f", grantee=None, privilege_type="USAGE")]))
    assert kinds(other_pair) == ["default_for_everyone"], [p.line() for p in other_pair]


# --- rights by word, and objects with an empty access list (round 2 of 3c: Issues 5 and 11) -------------------------------


def _named_right(word, role="rt", name="runs"):
    return item(
        name=name,
        grantee=role,
        grantee_is_subject=True,
        grantee_is_named=True,
        privilege_type=word,
    )


def test_maintain_is_one_more_right_that_the_grant_map_does_not_give():
    """MAINTAIN (PostgreSQL 17 and later) is read like any other right word: for a named role on a map table it is a
    `right` (the runtime role's list is SELECT, INSERT, UPDATE); for everyone it is `everyone`; the rights the map does
    give pass. Killed by: the mutant V61 (a prefix test in `_allowed_for`) and by any edit that lets MAINTAIN through.
    Replaces two older tests of the same kind that lived in the real-server file and were retired."""
    assert kinds(judge(rows(items=[_named_right("MAINTAIN")]))) == ["right"]
    assert kinds(judge(rows(items=[item(name="runs", privilege_type="MAINTAIN")]))) == ["everyone"]
    assert judge(rows(items=[_named_right("SELECT")])) == []  # control: a right of the map


@pytest.mark.parametrize(
    "word", ["SELECTX", "SEL", "select", "SELECT ", "UPDATE,INSERT", "", "MAINTAINS"]
)
def test_an_unknown_right_word_is_refused_whole_never_by_prefix(word):
    """A word that is not exactly one of the map's rights is a `right`, whatever it starts with. Killed by: V61."""
    assert kinds(judge(rows(items=[_named_right(word)]))) == ["right"], word


def test_an_item_with_no_right_is_never_read_as_a_right_for_everyone():
    """Q2 returns an object with an empty access list as one row with `privilege_type` None and no grantee (Issue 11).
    The row must not become an `everyone` or `right` problem, and must still be judged for its owner and its SECURITY
    DEFINER flag. A crash of `_judge` on such a row is a failure of this test as well (it is reported as a plain
    failure, not as an error of the test). Killed by: V62 (the guard on a null right is removed)."""

    def judged(one):
        crash, out = None, None
        try:
            out = judge(rows(items=[one]))
        except (TypeError, AttributeError, KeyError, ValueError) as e:
            crash = type(e).__name__
        assert crash is None, f"_judge crashed on a row with no right: {crash}"
        return out

    assert judged(item(name="runs", grantee=None, privilege_type=None)) == []
    fn = item(kind="function", relkind="", name="door", sub="q text", definer=True, grantee=None,
              privilege_type=None)  # fmt: skip
    assert kinds(judged(fn)) == ["definer_unreviewed"]
    other = item(name="runs", owner="boss", family_owned=False, grantee=None, privilege_type=None)
    assert kinds(judged(other)) == ["foreign_owner"]


# --- the words of the message lines in the CHANGELOG are the words of the code (Issue 4) -----------------------------------


def _block(text: str, name: str) -> list[str]:
    start, stop = text.index(f"[{name}]"), text.index(f"[end of {name}]")
    return [ln.strip() for ln in text[start + len(name) + 2 : stop].splitlines() if ln.strip()]


def _forms_missing_from(forms: list[str], source: str) -> list[str]:
    """The forms (a sentence with `{placeholders}`) that the code does not write. A form is written when one f-string of
    the source holds every piece of it, in order, with a `{...}` where the form has a placeholder, and the pieces are
    taken with their spaces ("has " is not "hash"). Round 3 of 3d, Issue 1: no piece is skipped for being short."""
    missing = []
    for form in forms:
        pieces = re.split(r"\{[a-z_ ]+\}", form)
        pattern = r"\{[^{}]*\}".join(re.escape(piece) for piece in pieces)
        # a form that ends in a placeholder ends the pattern with `\{...}`; one that starts with a piece starts with it
        if not re.search(pattern, source):
            missing.append(form)
    return missing


def test_every_sentence_form_the_changelog_quotes_is_in_the_code_and_is_what_a_line_says():
    root = Path(__file__).resolve().parents[1]
    forms = _block((root / "CHANGELOG.md").read_text(encoding="utf-8"), "message words")
    assert forms, "the block of message words is empty"
    source = (root / "src/hadavin_sdk/store/migration_verify.py").read_text(encoding="utf-8")
    assert _forms_missing_from(forms, source) == [], "a form is in the CHANGELOG, not in the code"
    plain = v.Problem("right", "app", "plans", "", "portal_role", "DELETE", "mig", word="table",
                      fix="REVOKE DELETE ON TABLE app.plans FROM portal_role;")  # fmt: skip
    via = v.Problem("right", "app", "plans", "", "portal_role", "SELECT", "mig", word="table", via="grp",
                    fix="REVOKE grp FROM portal_role;")  # fmt: skip
    assert "portal_role has DELETE." in plain.line() and "To remove:" in plain.line()
    assert "can use it through the role grp, SELECT." in via.line()
    assert forms[0] == "has {right}" and forms[1] == "can use it through the role {via}, {right}"
    assert forms[2] == "To remove: {statement}"


def test_a_sentence_the_changelog_quotes_but_the_code_does_not_write_is_found():
    """The checker is not blind: it is run on planted blocks and returns the stale form. Killed by: V84 (the code writes
    "holds" where the CHANGELOG says "has")."""
    source = (
        Path(__file__).resolve().parents[1] / "src/hadavin_sdk/store/migration_verify.py"
    ).read_text(encoding="utf-8")
    assert _forms_missing_from(["can see it through the role {via}, {right}"], source) == [
        "can see it through the role {via}, {right}"
    ]
    assert _forms_missing_from(["the portal role has privileges outside the map"], source) != []
    # the short form `has {right}` is checked as a whole: the piece "has " followed by a placeholder
    assert _forms_missing_from(["has {right}"], source) == []
    assert _forms_missing_from(["holds {right}"], source) == ["holds {right}"]
    # a code that says "holds" where the block says "has" is found (the same source text with the word changed)
    stale = (
        source.replace('f"has {self.right}"', 'f"holds {self.right}"')
        .replace('f"has {self.right};', 'f"holds {self.right};')
        .replace('f"has {self.right} on', 'f"holds {self.right} on')
    )
    assert _forms_missing_from(["has {right}"], stale) != []
