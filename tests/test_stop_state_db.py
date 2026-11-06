"""Stop state against a real PostgreSQL, through real logins (never a superuser's shortcut).

Skipped without HADAVIN_TEST_PG_DSN. Roles are cluster-wide, so every name carries a random suffix."""

from __future__ import annotations

import os
import uuid

import pytest

psycopg = pytest.importorskip("psycopg")
from psycopg import errors, sql
from psycopg.conninfo import make_conninfo

from hadavin_sdk.audit.labelkey import NOKEY_LABEL
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store.migrate import migrate
from tests.stop_state_helpers import RESET_GROUP

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"), reason="needs HADAVIN_TEST_PG_DSN"
)
LABEL_A = "id:k1:" + "a" * 32
LABEL_R = "id:k1:" + "b" * 32
CAP = 3
# A login with no schema rights cannot even see the function (UndefinedFunction); one with them is refused.
DENIED = (errors.InsufficientPrivilege, errors.UndefinedFunction)


class World:
    def __init__(self):
        sfx = uuid.uuid4().hex[:8]
        self.dsn = os.environ["HADAVIN_TEST_PG_DSN"]
        self.schema = f"p2a1_s_{sfx}"
        self.runtime, self.stoprole = f"p2a1_rt_{sfx}", f"p2a1_st_{sfx}"
        self.member, self.unregistered, self.outsider = (
            f"p2a1_{n}_{sfx}" for n in ("mem", "unreg", "out")
        )
        self.roles = [self.runtime, self.stoprole, self.member, self.unregistered, self.outsider]
        self.scoped = make_conninfo(self.dsn, options=f"-c search_path={self.schema}")

    def admin(self):
        return psycopg.connect(self.scoped, autocommit=True)

    def as_(self, role):
        return psycopg.connect(make_conninfo(self.scoped, user=role), autocommit=True)

    def migrate(self, **kw):
        return migrate(
            self.scoped,
            runtime_role=self.runtime,
            stop_role=self.stoprole,
            reset_role=RESET_GROUP,
            max_open_stop_requests=CAP,
            **kw,
        )

    def stop(self, role, label=LABEL_A):
        with self.as_(role) as db:
            return db.execute("SELECT * FROM hadavin_kill_switch_stop(%s)", (label,)).fetchone()

    def state(self):
        with self.admin() as db:
            return db.execute(
                'SELECT "on", "by", version, open_requests FROM kill_switch_state'
            ).fetchone()

    def reset(self, role, version, opened, label=LABEL_R):
        with self.as_(role) as db:
            return db.execute(
                "SELECT * FROM hadavin_kill_switch_reset(%s, %s, %s)", (label, version, opened)
            ).fetchone()


@pytest.fixture
def w():
    world = World()
    with psycopg.connect(world.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(world.schema)))
        for r in world.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
        for r in (world.member, world.unregistered):
            db.execute(
                sql.SQL("GRANT {} TO {}").format(sql.Identifier(RESET_GROUP), sql.Identifier(r))
            )
    world.migrate()
    with world.admin() as db:
        db.execute(
            "INSERT INTO kill_switch_login_labels (login_name, label) VALUES (%s, %s)",
            (world.member, LABEL_R),
        )
    yield world
    with psycopg.connect(world.dsn, autocommit=True) as db:
        db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(world.schema)))
        for r in world.roles:
            db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))


def _sqlstate(excinfo):
    return excinfo.value.sqlstate


def test_stop_by_runtime_and_stop_logins_reads_on(w):
    assert w.state()[0] is False
    assert w.stop(w.stoprole)[0] is True
    row = w.stop(w.runtime, "id:k1:" + "c" * 32)
    assert row[0] is True and row[5] == 2
    assert w.state()[0] is True and w.state()[3] == 2


@pytest.mark.parametrize(
    "bad",
    [
        None,
        "user:a",
        "",
        LABEL_A + "\n",
        "id:k1:" + "A" * 32,
        "id::" + "a" * 32,
        "id:k1:" + "a" * 31,
    ],
)
def test_stop_refuses_a_non_label_with_hd004(w, bad):
    with pytest.raises(psycopg.Error) as e:
        w.stop(w.stoprole, bad)
    assert _sqlstate(e) == "HD004"
    assert w.state()[0] is False


def test_the_cap_bounds_open_requests_and_a_stop_still_reads_on(w):
    for _ in range(CAP + 2):
        assert w.stop(w.stoprole)[0] is True
    assert w.state()[3] == CAP


def test_reset_by_a_registered_member_with_the_right_pair(w):
    w.stop(w.stoprole)
    w.stop(w.runtime)
    version, opened = w.state()[2], w.state()[3]
    row = w.reset(w.member, version, opened)
    assert row[0] is False and row[5] == 0 and row[4] == version + 1
    assert w.state()[0] is False
    with w.admin() as db:
        recorded = db.execute("SELECT old_version, login_label FROM kill_switch_resets").fetchall()
    assert recorded == [(version, LABEL_R)]


def test_a_stale_pair_is_refused_with_hd003_and_the_switch_stays_on(w):
    w.stop(w.stoprole)
    version, opened = w.state()[2], w.state()[3]
    w.stop(w.runtime)  # a second stop after the operator read the status
    for v, n in ((version, opened), (version + 1, opened + 1), (version, 0)):
        with pytest.raises(psycopg.Error) as e:
            w.reset(w.member, v, n)
        assert _sqlstate(e) == "HD003"
    assert w.state()[0] is True and w.state()[3] == 2


def test_reset_of_an_off_switch_is_stale(w):
    with pytest.raises(psycopg.Error) as e:
        w.reset(w.member, w.state()[2], 0)
    assert _sqlstate(e) == "HD003"


def test_member_without_a_registered_label_is_refused_with_hd001(w):
    w.stop(w.stoprole)
    with pytest.raises(psycopg.Error) as e:
        w.reset(w.unregistered, w.state()[2], 1)
    assert _sqlstate(e) == "HD001"
    assert w.state()[0] is True


def test_non_members_cannot_even_call_reset(w):
    w.stop(w.stoprole)
    for role in (w.outsider, w.runtime, w.stoprole):
        with pytest.raises(DENIED):
            w.reset(role, w.state()[2], 1)
    assert w.state()[0] is True


def test_reset_with_a_bad_label_is_hd004(w):
    w.stop(w.stoprole)
    with pytest.raises(psycopg.Error) as e:
        w.reset(w.member, w.state()[2], 1, label="user:a")
    assert _sqlstate(e) == "HD004"


def test_even_the_owner_cannot_flip_the_flag_off_without_the_group(w):
    """The guard fires for every session (ENABLE ALWAYS), the owner or a superuser included."""
    with w.admin() as db:
        db.execute('UPDATE kill_switch SET "on" = true WHERE id = 1')
        with pytest.raises(psycopg.Error) as e:
            db.execute('UPDATE kill_switch SET "on" = false WHERE id = 1')
        assert _sqlstate(e) == "HD001"
    assert w.state()[0] is True


def test_runtime_and_stop_logins_hold_no_table_rights(w):
    for role in (w.runtime, w.stoprole):
        with w.as_(role) as db:
            for statement in (
                'UPDATE kill_switch SET "on" = false',
                "SELECT * FROM kill_switch",
                "INSERT INTO kill_switch_stop_requests (\"by\") VALUES ('x')",
                "SELECT * FROM kill_switch_stop_requests",
                "UPDATE kill_switch_stop_requests SET cleared_by = 1",
                "DELETE FROM kill_switch_stop_requests",
                "TRUNCATE kill_switch_stop_requests",
                "INSERT INTO kill_switch_resets VALUES (1, now(), 'x', 'y')",
                "SELECT * FROM kill_switch_login_labels",
                "INSERT INTO kill_switch_login_labels VALUES ('x', 'y')",
                "SELECT nextval('kill_switch_stop_requests_id_seq')",
            ):
                with pytest.raises(errors.InsufficientPrivilege):
                    db.execute(statement)
            assert db.execute("SELECT count(*) FROM kill_switch_state").fetchone()[0] == 1


def test_request_and_reset_tables_are_append_only_even_for_the_owner(w):
    w.stop(w.stoprole)
    w.reset(w.member, w.state()[2], 1)
    with w.admin() as db:
        for statement in (
            "DELETE FROM kill_switch_stop_requests",
            "TRUNCATE kill_switch_stop_requests",
            "UPDATE kill_switch_stop_requests SET \"by\" = 'x'",
            "UPDATE kill_switch_stop_requests SET cleared_by = NULL",
            "UPDATE kill_switch_resets SET login_label = 'x'",
            "DELETE FROM kill_switch_resets",
            "TRUNCATE kill_switch_resets",
        ):
            with pytest.raises(psycopg.Error):
                db.execute(statement)


def test_the_functions_are_not_executable_by_public(w):
    with w.as_(w.outsider) as db, pytest.raises(errors.InsufficientPrivilege):
        db.execute("SELECT * FROM hadavin_kill_switch_stop(%s)", (LABEL_A,))


def test_migrate_again_keeps_the_state_and_reinstalls_a_disabled_guard(w):
    w.stop(w.stoprole)
    with w.admin() as db:
        db.execute("ALTER TABLE kill_switch DISABLE TRIGGER kill_switch_guard")
    w.migrate()
    with w.admin() as db:
        enabled = db.execute(
            "SELECT tgenabled FROM pg_trigger WHERE tgname = 'kill_switch_guard' "
            "AND tgrelid = 'kill_switch'::regclass"
        ).fetchone()[0]
    assert enabled == "A"
    assert w.state()[0] is True and w.state()[3] == 1


def test_migrate_refuses_a_missing_or_login_reset_group_and_a_missing_name(w):
    with pytest.raises(ConfigError, match="reset_role"):
        migrate(w.scoped)
    with pytest.raises(ConfigError, match="does not exist"):
        migrate(w.scoped, reset_role="p2a1_nope_" + uuid.uuid4().hex[:6])
    with pytest.raises(ConfigError, match="NOLOGIN"):
        migrate(w.scoped, reset_role=w.member)
    with pytest.raises(ConfigError, match="different roles"):
        migrate(w.scoped, runtime_role=w.runtime, reset_role=w.runtime)


def test_nokey_label_is_a_valid_stop_label(w):
    assert w.stop(w.stoprole, NOKEY_LABEL)[0] is True
