# P2a round 8 probes (run by the round 8 resolve session, throwaway PostgreSQL 16.15, 2026-11-06 ~02:01-02:05 UTC / 07:31-07:35 IST)

Server: initdb in the session scratchpad, socket only (no TCP), port 54338, trust auth, superuser `postgres` as owner of everything (NOT the non-superuser migrator of the ticket's fixtures). Data made up; labels are repeated letters; no secret of any kind. Purpose: order 7(2), check the SQL claims of round 8 findings ADV M1, COR N2, COR N10, ADV N3 (F15) and ADV N5. Nothing run against the repository suites; psycopg not used. The cluster was stopped and deleted after the run.

Model: `setup.sql` = the revision 9 texts of field 11 and the SETUP of field 12 copied verbatim (view, stop, reset, guard functions), with <S>=t_p2a9, <N>=5, <GROUP>=r_grp; roles r_grp (NOLOGIN), r_alice and r_bob (LOGIN, members of r_grp, labels b... and e...), r_exec (EXECUTE on stop). Output columns of the functions: on|by|ts|schema_version|version|open_requests unless a narrower select is shown.

## raw output: m1
```
== setup
psql:setup.sql:2: NOTICE:  schema "t_p2a9" does not exist, skipping
== M1: stop A (r_exec), alice resets (0,1), stop B, bob resets (1,1)
t|id:k1:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa|2026-11-06 02:01:24.530133+00|1|0|1
f|id:k1:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb|2026-11-06 02:01:24.559575+00|1|1|0
t|id:k1:cccccccccccccccccccccccccccccccc|2026-11-06 02:01:24.588647+00|1|1|1
f|id:k1:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee|2026-11-06 02:01:24.617653+00|1|2|0
-- kill_switch_resets (old_version|login_label|old_by):
0|id:k1:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb|<NULL>
1|id:k1:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee|id:k1:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
-- kill_switch row:
f|id:k1:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee|2
== DBA recipe hand ON: UPDATE kill_switch SET on=true; view by =
t|id:k1:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee|2|0
```

## raw output: fixb
```
== FIX (b): trigger OFF->ON clears an unchanged by
DETAIL:  drop cascades to table t_p2a9.kill_switch
drop cascades to table t_p2a9.kill_switch_stop_requests
drop cascades to table t_p2a9.kill_switch_resets
drop cascades to table t_p2a9.kill_switch_login_labels
drop cascades to view t_p2a9.kill_switch_state
drop cascades to function t_p2a9.hadavin_kill_switch_stop(text)
drop cascades to function t_p2a9.hadavin_kill_switch_reset(text,bigint,integer)
drop cascades to function t_p2a9.hadavin_kill_switch_guard()
t|1
f|id:k1:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb|1
t|1
f|id:k1:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee|2
-- resets:
0|id:k1:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb|<NULL>
1|id:k1:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee|<NULL>
-- who stopped, per runbook query (cleared_by = 2):
id:k1:cccccccccccccccccccccccccccccccc
-- DBA hand ON without by -> view by:
t|<NULL>|2
-- third reset (alice, 2, 0) of the hand ON -> old_by:
f|3
2|<NULL>
-- DBA hand ON WITH by='dba' -> view by:
t|dba
-- old-release style upsert after reset (raw by) keeps its by:
4
t|user:old
```

## raw output: n10n2
```
== N10 as written (after g: OFF, 0 open, v1): uncommitted stop on A, reset (1,0) on B
g:
f|1|0
i (B):
ERROR:  kill switch: the open count changed
CONTEXT:  PL/pgSQL function t_p2a9.hadavin_kill_switch_reset(text,bigint,integer) line 13 at RAISE
   elapsed .031648696 s
[1]+  Done                    ( echo "BEGIN; SELECT 1 FROM t_p2a9.hadavin_kill_switch_stop('id:k1:'||repeat('1',32)); SELECT pg_sleep(2); COMMIT;" | $P -U r_exec ) > /dev/null 2>&1
view after A commits:
t|1|1
== N10 proposed: reset that to v2, commit stop '2' (open 1); uncommitted stop '3' on A; reset (2,1) on B
2
1
i (B):
f|3|0
   elapsed .033715303 s
[1]+  Done                    ( echo "BEGIN; SELECT 1 FROM t_p2a9.hadavin_kill_switch_stop('id:k1:'||repeat('3',32)); SELECT pg_sleep(2); COMMIT;" | $P -U r_exec ) > /dev/null 2>&1
view after A commits:
t|id:k1:33333333333333333333333333333333|3|1
== N2: lock_timeout 2000 set BEFORE pg_advisory_xact_lock; A holds the advisory lock 4 s
2s
ERROR:  canceling statement due to lock timeout
   elapsed 2.029944360 s
[1]+  Done                    ( $P -U postgres -c "BEGIN; SELECT pg_advisory_xact_lock(4242); SELECT pg_sleep(4); COMMIT;" ) > /dev/null 2>&1
-- lock_timeout set AFTER the advisory lock:

2s
2s
[1]+  Done                    ( $P -U postgres -c "BEGIN; SELECT pg_advisory_xact_lock(4242); SELECT pg_sleep(4); COMMIT;" ) > /dev/null 2>&1
   elapsed 3.531773998 s
```

## raw output: f15n5
```
== N3/F15: stop function mutated to IF n <= 5; 7 stops
1 2 3 4 5 6 7 
== F15 redefined: IF n < 5 - 1
1 2 3 4 4 4 
== N5: two open stops, row deleted, a third stop: returned row vs table
t|id:k1:ffffffffffffffffffffffffffffffff|0|1
3
0
```

## Fix (b) as run (the ELSIF branch of the guard; the rest of the function unchanged)
```sql
  ELSIF NEW."on" AND NOT OLD."on" THEN
    IF NEW."by" IS NOT DISTINCT FROM OLD."by" THEN NEW."by" := NULL; END IF;
    NEW.version := OLD.version; NEW.ts := now();
```

## Reading (what the output shows; the resolve file judges it)
- m1: rev 9 text, two request-only resets by two logins: resets row 1 has old_by = r_alice's label (the previous resetter), not NULL. After the DBA hand `UPDATE ... SET "on" = true` the view reports `by` = r_bob's label (the last resetter) as who stopped.
- fixb: with fix (b) both resets rows have old_by NULL; the runbook query `cleared_by = 2` returns the real stopper; a hand ON without `by` reads NULL; a hand ON with `by = 'dba'` and an old-release style upsert with a raw `by` keep their value.
- n10n2 part 1: S31 case i as written gets HD003 (0.03 s), so it never shows a reset beside an in-flight stop. Part 2 (one committed stop first, reset with (2,1)): the reset succeeds in 0.03 s without waiting and returns on=f; after the in-flight stop commits the view reads ON with open 1 and by = that stop (this is also ADV N6(c): the returned row says OFF while a stop is in flight).
- n10n2 part 3: `set_config('lock_timeout','2000',true)` BEFORE `pg_advisory_xact_lock` makes the waiting call fail with "canceling statement due to lock timeout" after 2.03 s; set AFTER the lock, the call waits about 3.5 s and succeeds.
- f15n5: F15 as written (`n <= N`) never caps (7 rows from 7 stops): same behaviour as removing the cap (F13). `n < N - 1` caps at 4. Missing row: the stop returns open_requests 1 and by = the new caller while 3 requests are open; the view returns 0 rows.
- Not run: fix (a); a non-superuser owner; PostgreSQL 17; psycopg; concurrency loops; anything else in S29-S42.
