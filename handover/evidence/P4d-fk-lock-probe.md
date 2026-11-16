# Probe: does a foreign-key INSERT wait on a parent row held FOR UPDATE / FOR NO KEY UPDATE? (P4d round 5, F1)

Run by the lead 2026-11-05 on a throwaway PostgreSQL 16 (port 54329, data dir /tmp/pgprobe, superuser). Not CI's version (17.10): UNVERIFIED on 17 (documented PG behaviour, row-lock conflict table, says the same).

Setup: `CREATE TABLE p(id int primary key, v int); CREATE TABLE c(id int primary key, pid int references p(id)); INSERT INTO p VALUES (1,0);`
Session A: `BEGIN; SELECT * FROM p WHERE id=1 <MODE>; SELECT pg_sleep(3); COMMIT;`
Session B (0.7 s later): `SET lock_timeout='1s'; INSERT INTO c VALUES (<n>,1);`

Raw output:
- holder `FOR UPDATE`: `ERROR: canceling statement due to lock timeout / CONTEXT: while locking tuple (0,1) in relation "p"` (the child INSERT waited on the parent row: the FK check takes FOR KEY SHARE).
- holder `FOR NO KEY UPDATE`: no error (the child INSERT succeeded without waiting).

Meaning for P4d F1: a test that holds `FOR UPDATE` on the `runs` row blocks `reserve_spend` at its first INSERT (FK check) in both lock orders, so it cannot tell them apart; `FOR NO KEY UPDATE` lets the INSERT through and blocks only at the later `UPDATE runs`. The reviewer's fix is correct on this point.
