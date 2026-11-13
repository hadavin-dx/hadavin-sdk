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
