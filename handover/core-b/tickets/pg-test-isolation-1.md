# pg-test-isolation-1: PG tests collide on cluster-wide roles under `-n 3`

Branch: local/code-Y (worktree /tmp/core-b-wt/Y). Status: investigated only; no source or test edited there.
The patch below was built and checked on a scratch copy of the worktree, not applied.

## Symptoms
1. `tests/test_spend_reservations_pg.py::test_the_purge_login_is_denied[TRUNCATE spend...]` ends in a SETUP ERROR in a
   full `-n 3` run, passes alone.
2. `test_grants_negative_roles.py::test_pg_step_b_the_runtime_role_cannot_switch_the_stop_off` and
   `tests/demo_askdata/test_validate_harm.py[dblink-connect]` were reported as ignoring HADAVIN_TEST_PG_DSN.

## Cause of 1 (reproduced)
Reproduced with all pg test files under `-n 3` (3 of 3 runs gave 1-2 setup errors; the two named files alone gave none).
First error line (fixture `w`, `World.migrate()` in setup):

    hadavin_sdk.errors.ConfigError: roles other than the reset role could clear a stop (a right on kill_switch or
    kill_switch_clears, or membership in a role that holds one): sb_mo_<sfx>   (also sb_wa_<sfx>, sb_mw_<sfx>)

`store/migrate.py:_CAN_CLEAR` / `who_else_can_clear` scans `pg_roles` for the WHOLE CLUSTER, not the schema. Each worker
has its own schema and uuid-suffixed names, so schemas, role names and DROPs do not collide (no role is dropped while in
use). The collision is a cross-worker read: `tests/test_stop_state_roles.py` creates stray roles through
`World.new_role` that are visible cluster-wide: `sb_mo_*` (member of the owner, a superuser:
`test_migrate_refuses_a_reset_role_that_is_a_member_of_the_owner`), `sb_wa_*` (member of pg_write_all_data,
`test_s2_migrate_refuses_a_member_of_pg_write_all_data`), `sb_mw_*` and others. While such a role exists, the migrate
of ANY other worker's World (this file, test_spend_reservations_pg.py, contracts) is refused. The window is the
test's duration, so it is timing dependent and shows up only when two workers overlap.
Also: the 8 failures in test_grants_negative_roles.py (`-n 3` and alone) are NOT isolation: they are deterministic on
this branch (the GRANTS map has `purge: spend_reservations DELETE`, reset_role etc. that the file's reviewed lists do not
yet have; and `test_pg_step_b_...` is `XPASS(strict)`, the stop-off step is built so the xfail marker must go).

## Cause of 2
- `test_pg_step_b_the_runtime_role_cannot_switch_the_stop_off`: it uses the DSN (`_as` = `make_conninfo(dsn, user=...)`).
  It fails with `XPASS(strict)`, not with a socket error. The claim does not hold for this test.
- `test_validate_harm[dblink-connect]`: the test connects with the DSN. The attack SQL is
  `SELECT dblink_connect('dbname=postgres')` (tests/demo_askdata/corpus.py:216), executed BY THE SERVER, which dials its
  own default unix socket `/var/run/postgresql/.s.PGSQL.5432`. That socket does not exist on this server
  (127.0.0.1:55439), error: `connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed`. It fails alone
  too. CI works only if the service has that socket.

## Owners (git log of the files)
- tests/test_stop_state_roles.py, tests/test_spend_reservations_pg.py: Claude sessions on this branch (code-Y lane).
- tests/demo_askdata/test_validate_harm.py, corpus.py: Veera Rakesh Kethari (askdata demo).
- tests/test_grants_negative_roles.py: code-Y lane (grants-map drift, separate ticket needed).

## Smallest fix (patch text; verified: 3 clean `-n 3` runs of stop_state_roles + spend_reservations_pg after the
last change, `test_the_python_signatures_are_unchanged` and `dblink-connect` pass)
A Postgres advisory lock: every migrate takes it shared; a World that makes a cluster-wide stray role takes it exclusive
until teardown. Not fixed by it: other files that call `migrate()` with roles directly (test_k2_migrations,
test_p7_store, test_k5_*, tests/contracts) take no shared lock; add the same wrapper there if they show the error.
A less invasive alternative: run the stray-role tests in one `xdist_group` with `--dist loadgroup` only if everything
else migrating is also grouped, which is not practical.

```diff
diff --git a/tests/demo_askdata/test_validate_harm.py b/tests/demo_askdata/test_validate_harm.py
index 50bf4373b..d3bf7d0d5 100644
--- a/tests/demo_askdata/test_validate_harm.py
+++ b/tests/demo_askdata/test_validate_harm.py
@@ -130,7 +130,12 @@ def prove_harm(attack: Attack, dsn: str) -> str:
         return f"still running when the {TIMEOUT_MS} ms statement_timeout cancelled it"
     if kind in ("leak", "exec"):
         with psycopg.connect(dsn, autocommit=True) as c:
-            cur = c.execute(attack.sql)
+            # dblink dials from the SERVER process: aim it at the host and port this test reached it on
+            info = c.info
+            statement = attack.sql.replace(
+                "dbname=postgres", f"host={info.host} port={info.port} dbname=postgres"
+            )
+            cur = c.execute(statement)
             cells = _cells(cur) if kind == "leak" else []
         if kind == "leak":
             assert any(needle in cell for cell in cells), f"no cell contains {needle!r}"
diff --git a/tests/test_stop_state_roles.py b/tests/test_stop_state_roles.py
index 98e1ded45..faff786e1 100644
--- a/tests/test_stop_state_roles.py
+++ b/tests/test_stop_state_roles.py
@@ -8,6 +8,7 @@ never counts as a denial. Needs HADAVIN_TEST_PG_DSN (CI: the postgres service);
 
 from __future__ import annotations
 
+import functools
 import inspect
 import os
 import threading
@@ -32,7 +33,8 @@ from hadavin_sdk.config import ConfigError
 from hadavin_sdk.limits import Limits
 from hadavin_sdk.models import KillSwitch, RunState
 from hadavin_sdk.store import migrate as migrate_mod
-from hadavin_sdk.store.migrate import GRANTS, migrate
+from hadavin_sdk.store.migrate import GRANTS
+from hadavin_sdk.store.migrate import migrate as _migrate
 from hadavin_sdk.store.protocol import Store
 
 pytestmark = pytest.mark.skipif(
@@ -47,6 +49,22 @@ SETTINGS = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}
 RESET_REF = "reset-dsn"  # the NAME of a secret (config), never a value
 
 
+CLUSTER_ROLES_LOCK = 7_204_113  # shared by every World.migrate, exclusive while a cluster-wide stray role exists
+
+
+_HOLDS_CLUSTER_LOCK = False  # this process (one test at a time) holds the exclusive lock
+
+
+@functools.wraps(_migrate)
+def migrate(dsn, **kw):
+    """`migrate` that waits while another worker has a stray cluster-wide role (see World.new_role)."""
+    if _HOLDS_CLUSTER_LOCK:
+        return _migrate(dsn, **kw)
+    with psycopg.connect(os.environ["HADAVIN_TEST_PG_DSN"], autocommit=True) as lock:
+        lock.execute("SELECT pg_advisory_lock_shared(%s)", (CLUSTER_ROLES_LOCK,))
+        return _migrate(dsn, **kw)
+
+
 class World:
     """One schema and four logins. Everything it creates is recorded and dropped by the fixture."""
 
@@ -62,6 +80,14 @@ class World:
         self.roles = [self.runtime, self.portal, self.purge, self.reset]
         self.scoped = self.scope(self.schema)
         self.stores = []
+        self._exclusive = None
+
+    def release_cluster_lock(self):
+        if self._exclusive is not None:
+            self._exclusive.close()  # closing the session drops its advisory lock
+            self._exclusive = None
+            global _HOLDS_CLUSTER_LOCK
+            _HOLDS_CLUSTER_LOCK = False
 
     def scope(self, schema):
         return make_conninfo(self.dsn, options=f"-c search_path={schema}")
@@ -96,7 +122,14 @@ class World:
         s._db.execute("SET statement_timeout = '30s'")  # a blocked statement fails, never hangs
         return s
 
-    def new_role(self, part, options="LOGIN"):
+    def new_role(self, part, options="LOGIN", cluster_wide=True):
+        """`cluster_wide`: the role is visible to the cluster-wide scan of `migrate` in every other schema (a member
+        of a superuser or of pg_write_all_data), so no other World may migrate until this one is dropped."""
+        if cluster_wide and self._exclusive is None:
+            self._exclusive = psycopg.connect(self.dsn, autocommit=True)
+            self._exclusive.execute("SELECT pg_advisory_lock(%s)", (CLUSTER_ROLES_LOCK,))
+            global _HOLDS_CLUSTER_LOCK
+            _HOLDS_CLUSTER_LOCK = True
         name = f"sb_{part}_{self.sfx}"
         with psycopg.connect(self.dsn, autocommit=True) as db:
             db.execute(sql.SQL("CREATE ROLE {} {}").format(sql.Identifier(name), sql.SQL(options)))
@@ -184,6 +217,7 @@ def stop_world():
             for r in world.roles:
                 db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
                 db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))
+        world.release_cluster_lock()
 
 
 def _stop(w, by="ops:stop"):
@@ -642,7 +676,7 @@ def test_migrate_refuses_a_reset_role_that_owns_a_relation(w):
 
 def test_migrate_refuses_a_reset_role_that_is_a_member_of_the_owner(w):
     owner = w.run("SELECT current_user")[0][0]
-    member = w.new_role("mo", "NOLOGIN NOINHERIT")
+    member = w.new_role("mo", "NOLOGIN NOINHERIT", cluster_wide=True)
     w.grant("GRANT {} TO {}", owner, member)
     try:
         with pytest.raises(
@@ -1215,7 +1249,7 @@ def test_s2_migrate_refuses_the_runtime_role_as_a_noinherit_member_of_a_group_th
 
 def test_s2_migrate_refuses_a_member_of_pg_write_all_data(w):
     """A predefined role that may INSERT and UPDATE everywhere: its member can clear without any grant here."""
-    writer = w.new_role("wa", "LOGIN")
+    writer = w.new_role("wa", "LOGIN", cluster_wide=True)
     w.grant("GRANT pg_write_all_data TO {}", writer)
     _refused_naming(w, writer)
 
```

Note: the dblink change makes the attack dial host/port of the test connection; needs trust or matching auth from the
server to itself (true here). Owner of that file should confirm it does not weaken what the case proves (it still runs
`dblink_connect` unvalidated and shows it executes).

Not done: nothing committed or pushed; no source or test edited under /tmp/core-b-wt/Y.
