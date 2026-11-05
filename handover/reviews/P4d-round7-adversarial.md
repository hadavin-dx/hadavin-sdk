# P4d round 7 adversarial review (egm:egm-design), ticket rev 8 (head 8680691). Condensed by the lead; read-only, ran nothing, no Postgres.
Verdict: no blocker; five majors, eight minors/nits. Lock order, FK-lock fix and rounding rows a1-a8 held up by hand.
| id | sev | where | problem | fix |
|---|---|---|---|---|
| R7-1 | Major | L148-149,168,179,186-227 | `release_spend` lowers counters with no `CounterDamaged` guard (only settle has it); counters have no CHECK usd>=0, so release can drive them negative = free headroom | Apply settle guard to release on both stores (`WHERE usd >= amt`, zero rows = CounterDamaged, rollback); B3 rows; mutant |
| R7-2 | Major | L7,28,37,174,253,279,107 | Ticket says P2a keeps SELECT, UPDATE (rev 5); P2a is rev 7: SELECT only + SECURITY DEFINER stop; P2a coupling note's four fixes not applied | Re-read P2a rev 7; rewrite bullets; withdraw v1.1 row 1; mark A2b rows; cite by item |
| R7-3 | Major | L236 (P4d-c), L163 | P3a creates tests/migration_schemas.py, test_migration_postgres.py, test_migration_numbers.py; P4d-c allow-list and exact-set test omit them; B8 builds a separate behind-schema helper | Add the 3 files to allow-list; B8 reuses P3a's helper |
| R7-4 | Major | L71, L70 | Round-up + 8-decimal refusal only at two producers; other Reply/Verdict.cost_usd sources would raise after the paid call | field_validator on Reply/Verdict.cost_usd (one helper) or state custom producers must; row with 9-decimal stub |
| R7-5 | Major | L35 | "At most one statement's timeout over" wrong: set_config once, ~6 lock statements each can wait the budget | Re-issue set_config per statement, or state real bound and add two-lock row |
| R7-6 | Minor | L71-72 | "Round up never down" false for >28 significant digits (default context rounds first) | Limit price decimals (12) or localcontext(prec=60); 30-decimal row |
| R7-7 | Minor | L101,170,107; memory.py:31 | Memory store plain Lock; new memory methods calling get_run self-deadlock | Lock-free private helpers or RLock; lone-caller join-timeout rows; daemon threads |
| R7-8 | Minor | L180 | vii rows run with lock_timeout 1000 ms; CI load can trip StoreBusy | Build store with lock_timeout_ms=60000 and large call budget |
| R7-9 | Minor | L147,266 | Settle above reservation skips caps; a bad actual of 1e12 poisons the day/month counters | Per-settle excess bound or record accepted exposure in PL16 |
| R7-10 | Minor | L15,249-251 | Hot-file orders stale (P4c-1, P6b1, P4b2-b); P4b1:195 and :248 missing from Tell the authors | Update |
| R7-11 | Minor | L230 | migrate() FK creation needs lock on runs, no lock_timeout, queues writers | lock_timeout for the migration or runbook step |
| R7-12 | Minor | L25,29-30,72,77 | "ran in the venv" claims with no saved output | Save evidence/P4d-venv-probe.md or relabel |
| R7-13 | Nit | L77,87,145 | i10f wording; edge-table values not fixed (0.000..1 does not kill i5); db_date-1 at month boundary | Tighten |
Unverified: any PG16/17 behaviour (trigger text, nested transaction(), pg_stat_activity waits, make_interval, ON CONFLICT lock), set_config lifetime under psycopg, existing suite stubs with Decimal(cost).
