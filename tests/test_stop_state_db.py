"""Stop state against a real PostgreSQL, through real logins (never a superuser's shortcut).

Fails in CI (and with HADAVIN_REQUIRE_PG) and skips on a laptop without HADAVIN_TEST_PG_DSN. Roles are cluster-wide, so every name carries a random suffix."""

from __future__ import annotations

import os
import uuid

import pytest

from tests.contracts.kinds import require_backend

require_backend("postgres", module_level=True)
import psycopg
from psycopg import errors, sql
from psycopg.conninfo import make_conninfo

from hadavin_sdk.audit.labelkey import NOKEY_LABEL
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store.migrate import migrate
from tests.stop_state_helpers import RESET_GROUP

LABEL_A = "id:k1:" + "a" * 32
LABEL_R = "id:k1:" + "b" * 32
CAP = 3
# Every denial is a privilege error; a missing function (UndefinedFunction) must NOT pass for a denial.
DENIED = (errors.InsufficientPrivilege,)


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

    def grant_usage(self, role):
        """Schema USAGE only, so a denial is about the function and not about an invisible schema."""
        with self.admin() as db:
            db.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    sql.Identifier(self.schema), sql.Identifier(role)
                )
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


@pytest.fixture(name="w")
def stop_world():
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
    w.grant_usage(w.outsider)
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
    w.grant_usage(w.outsider)
    with w.as_(w.outsider) as db, pytest.raises(DENIED):
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


def test_a_registered_login_outside_the_group_cannot_clear_even_with_table_rights(w):
    """The guard checks group membership itself; a registered label and an UPDATE grant are not enough."""
    with w.admin() as db:
        db.execute(
            "INSERT INTO kill_switch_login_labels (login_name, label) VALUES (%s, %s)",
            (w.outsider, "id:k1:" + "f" * 32),
        )
        db.execute(
            sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                sql.Identifier(w.schema), sql.Identifier(w.outsider)
            )
        )
        db.execute(
            sql.SQL("GRANT SELECT, UPDATE ON kill_switch TO {}").format(sql.Identifier(w.outsider))
        )
        db.execute('UPDATE kill_switch SET "on" = true WHERE id = 1')
    with w.as_(w.outsider) as db:
        with pytest.raises(psycopg.Error) as e:
            db.execute('UPDATE kill_switch SET "on" = false WHERE id = 1')
        assert _sqlstate(e) == "HD001"
    assert w.state()[0] is True


def test_a_migration_file_cannot_lengthen_the_table_lock_bound(monkeypatch):
    """Class: a file that SETs its own lock_timeout (0006 sets 10s) leaks that value to every later step.
    `migrate()` puts the configured bound back after every file."""
    from hadavin_sdk.store import migrate as m

    sfx = uuid.uuid4().hex[:8]
    schema = f"p2a1_lt_{sfx}"
    dsn = os.environ["HADAVIN_TEST_PG_DSN"]
    seen = []
    real = m._install_kill_switch

    def spy(db, schema_, group, cap):
        seen.append(db.execute("SELECT current_setting('lock_timeout')").fetchone()[0])
        return real(db, schema_, group, cap)

    monkeypatch.setattr(m, "_install_kill_switch", spy)
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    try:
        migrate(
            make_conninfo(dsn, options=f"-c search_path={schema}"),
            reset_role=RESET_GROUP,
            lock_timeout_ms=3000,
        )
    finally:
        with psycopg.connect(dsn, autocommit=True) as db:
            db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
    assert seen == ["3s"]  # 0006 set '10s'; without the fix this reads '10s'


def test_hand_set_raw_name_never_reaches_the_reset_record(w):
    """Build note B10: a typed (non-label) name in the flag becomes `unlabelled` in `old_by`."""
    with w.admin() as db:
        db.execute(
            sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                sql.Identifier(w.schema), sql.Identifier(w.member)
            )
        )
        db.execute(
            sql.SQL("GRANT SELECT, UPDATE ON kill_switch TO {}").format(sql.Identifier(w.member))
        )
        db.execute("""UPDATE kill_switch SET "on" = true, "by" = 'x@y.test' WHERE id = 1""")
    with w.as_(w.member) as db:
        db.execute('UPDATE kill_switch SET "on" = false WHERE id = 1')
    with w.admin() as db:
        assert db.execute("SELECT old_by FROM kill_switch_resets").fetchall() == [("unlabelled",)]


def test_a_stale_pair_from_before_another_reset_cannot_clear_a_newer_stop(w):
    """The main property of the (version, count) pair: stop A; read (v0, 1); someone resets; stop B lands (open is 1
    again); the stale reset (v0, 1) must be refused with HD003 and B must stay open."""
    w.stop(w.stoprole)
    v0, n0 = w.state()[2], w.state()[3]
    assert (v0, n0) == (0, 1)
    w.reset(w.member, v0, n0)  # the other operator's reset: version becomes 1
    w.stop(w.runtime, "id:k1:" + "d" * 32)  # stop B, open count is 1 again
    with pytest.raises(psycopg.Error) as e:
        w.reset(w.member, v0, n0)
    assert _sqlstate(e) == "HD003"
    assert (w.state()[0], w.state()[2], w.state()[3]) == (True, 1, 1)


def test_two_concurrent_resets_with_the_same_pair_clear_once(w):
    import threading

    w.stop(w.stoprole)
    pair = (w.state()[2], w.state()[3])
    out = []

    def go():
        try:
            w.reset(w.member, *pair)
            out.append("ok")
        except psycopg.Error as exc:
            out.append(exc.sqlstate)

    threads = [threading.Thread(target=go) for _ in range(2)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert sorted(out) == ["HD003", "ok"]
    assert w.state()[2] == 1  # one reset happened, the version moved once


def test_a_select_only_role_on_the_view_cannot_stop_or_reset(w):
    with w.admin() as db:
        db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(w.outsider + "_ro")))
        db.execute(
            sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                sql.Identifier(w.schema), sql.Identifier(w.outsider + "_ro")
            )
        )
        db.execute(
            sql.SQL("GRANT SELECT ON kill_switch_state TO {}").format(
                sql.Identifier(w.outsider + "_ro")
            )
        )
    try:
        with w.as_(w.outsider + "_ro") as db:
            assert db.execute("SELECT count(*) FROM kill_switch_state").fetchone()[0] == 1
            with pytest.raises(errors.InsufficientPrivilege):
                db.execute("SELECT * FROM hadavin_kill_switch_stop(%s)", (LABEL_A,))
            with pytest.raises(errors.InsufficientPrivilege):
                db.execute("SELECT * FROM hadavin_kill_switch_reset(%s, 0, 0)", (LABEL_R,))
    finally:
        with w.admin() as db:
            db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(w.outsider + "_ro")))
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(w.outsider + "_ro")))


def test_the_trigger_old_by_is_null_when_the_flag_was_never_named(w):
    w.stop(w.stoprole)
    w.reset(w.member, 0, 1)
    with w.admin() as db:
        assert db.execute("SELECT old_by FROM kill_switch_resets").fetchall() == [(None,)]


def test_a_noinherit_member_of_the_owner_role_is_refused_by_migrate(w):
    """A NOINHERIT member holds no rights by inheritance, yet can SET ROLE to the owner: the check is membership."""
    with w.admin() as db:
        owner = db.execute("SELECT current_user").fetchone()[0]
        db.execute(
            sql.SQL("GRANT {} TO {} WITH INHERIT FALSE, SET TRUE").format(
                sql.Identifier(owner), sql.Identifier(w.runtime)
            )
        )
    with pytest.raises(ConfigError, match="is a member of"):
        w.migrate()
