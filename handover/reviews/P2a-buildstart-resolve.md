# P2a build-start resolve (order 20, one round)

Status: resolved (AUTO mode; the interactive gate was skipped as the lead ordered). Model output, not user authority.
Target: `tickets/P2a.md` revision 10 (FROZEN), full file. Findings: `reviews/P2a-buildstart-adv.md` (15 rows) and `reviews/P2a-buildstart-cor.md` (9 rows), 24 in all. Both reports use the ids `BS-P2a-COR-1..6` for DIFFERENT findings, so here `A-` = the adv file and `C-` = the cor file.
Gate: order 20(3). Fixes go into the ticket's section "Build notes (build-start review, order 20)" (B0-B22 plus six "corrected at build start" lines). The frozen body was not rewritten. No second round.
Facts: I checked these myself, by reading or by running them.
- Read: `.github/workflows/ci.yml` (one service, `postgres:17.10@sha256:...`, no 16 job); `store/migrate.py:283-300` (`migrate()` has no `reset_role`, stop role, timeout or cap arguments); `config.py` and `backends/table.py` (no runtime-role or stop-role name in config); `cli.py:93-95, 312-346, 383-410` (`--by` is required, `choices=["stop","reset"]`, and `kill_switch` prints the raw `by` at 396 and 409); `limits.py:43-51`; `store/postgres.py:2` (unqualified names; the schema comes from migrate). A grep of `src` and `tests` found 0 matches for `StoreBusy`, `require_backend`, `@_writes`, `ACCEPTED_CHANGES`, `call_budget_ms` and `lock_timeout_ms`, and there are no `tools/` or `testing/` folders.
- Python (`python3 -I`): `re.match('^[A-Za-z0-9_-]{1,32}$', 'k1\n')` matches, but `re.fullmatch` and `\Z` do not; `'k1\r'` does not match. The label pattern with `^...$` accepts a label with a trailing newline. With `errors="replace"`, `'\ud800'`, `'\udfff'` and `'?'` all encode to `b'?'`, so they collide; with `surrogatepass` they stay distinct.
- Probes R20-1 to R20-5, run on a throwaway PostgreSQL 16.15 (my own data folder in the scratchpad, Unix socket only, port 54392). I used a hand-written model schema `t` with the view and the stop and reset function texts from field 11, cap 5, run as a superuser:
  - R20-1: PostgreSQL's `$` does NOT match before a trailing newline. A stop with a trailing newline, or with a newline inside `key_id`, raised `HD004` (so the custom `HD` code is accepted). Both function texts compiled and returned rows. The guard trigger was not installed.
  - R20-2: `has_table_privilege(..., 'MAINTAIN')` raises `22023 unrecognized privilege type` on 16. For a member of `pg_write_all_data`, `has_table_privilege` reports write as true. `GRANT ... WITH INHERIT TRUE/FALSE` works: `USAGE` is t/f and `MEMBER` is t. `pg_advisory_xact_lock(bigint)` can be run by any role (PUBLIC).
  - R20-3: two open transactions each called the stop 7 times under cap 5. Each returned 1,2,3,4,5,5,5, and after both committed there were 10 open requests.
  - R20-4: session M ran `ALTER TABLE kill_switch ADD COLUMN`, waited 1.5 s, then ran `CREATE INDEX` on the request table. A stop called at 1.0 s failed with `40P01 deadlock detected`, raised inside the stop's view read. The STOP was the victim, and M committed.
  - R20-5: `ALTER TABLE ... ENABLE ALWAYS TRIGGER` takes `ShareRowExclusiveLock`. Held on the request table, it made the stop's INSERT end with `lock timeout` (800 ms). Held on `kill_switch`, it did not stop the stop from completing.

Honest note (first: what I did NOT check, and my slips):
- Nothing was run on PostgreSQL 17: there is no binary here. So these stay UNVERIFIED: that `MAINTAIN` and `pg_maintain` exist on 17.10 and allow `LOCK TABLE` in any mode, `transaction_timeout`, and whether the function texts compile on 17. They come from my knowledge of the PostgreSQL 17 release, and the 17 CI job (B1) settles them.
- The probes ran as a superuser on a model schema, not with the real migrator, runtime and stop logins, and not with the guard trigger installed. The deadlock victim depends on timing, so R20-4 shows the stop CAN be the victim, not that it always is.
- I did not check psycopg behaviour (40P01 and 53300 class names), the P4d, P3a, P4b1 or P5 sibling tickets, the pool-size setting name (PENDING LEAD 27(c) stays open), `bible/RULES.md`, or any planned test id. No test suite was run.
- The 21 new mutant rows (B22) are planned. Their killers are not built, and the count of 199 is arithmetic (178 + 21), not a runner result.
- My slip: I ran `rm -rf` on my own data folder before my `pg_ctl stop` had succeeded (it failed on a permission error). The server kept running on a deleted folder, and I stopped it with SIGINT to its own PID (31168, after checking that its arguments held my folder). It and my files are gone. A second postgres belonging to another session (folder `pg3a`) was running when I started and was gone at the end. I never signalled it, so I believe its owner stopped it, but I cannot prove that.

| id | category | decision |
|---|---|---|
| A-COR-1 | PROPOSE FIX | Valid: CI is 17.10 only, so 16 is the missing version. B1 adds `ci.yml` to field 9 with a 16 job pinned by digest, and Done requires green on 16 AND 17 (order 20(1)). The false sentence is corrected. |
| A-ADV-1 | PROPOSE FIX | B2: a privilege list per server version (MAINTAIN on 17+, TRIGGER and REFERENCES on all versions), one builder for the probe and `effective_problems`, plus a `pg_maintain` membership check. A separate `pg_write_all_data` check is not needed, because R20-2 shows `has_table_privilege` already sees it. Negative tests on both versions. |
| A-ADV-2 | PROPOSE FIX | B3: DELETE and TRUNCATE refusal triggers, and an UPDATE trigger that allows only `cleared_by` NULL → value, all ENABLE ALWAYS and probed. The limit for the owner is stated. This adds surface, so PENDING LEAD 37. |
| A-ADV-3 | PROPOSE FIX | B13: `fullmatch` everywhere and `surrogatepass` (both confirmed in Python). The final-label re-check in `Limits.stop` is NOT added: it is dead code once `key_id` is checked with fullmatch (field 13, equivalent row 4). |
| A-COR-2 | PROPOSE FIX | B6: config gets `limits.runtime_role` and `limits.stop_role`; the probe checks the named roles, never `current_user`. Test from three logins. The false "runs as the runtime" sentence is corrected. |
| A-COR-3 | PROPOSE FIX | B4 and B5, confirmed by R20-5: re-point the G45 killer to a writer lock; re-assert ENABLE ALWAYS only when `tgenabled <> 'A'`; field 11 says a routine migrate delays resets, not stops. |
| A-ADV-4 | PROPOSE FIX | B7, confirmed by R20-4 (the stop was the victim): one lock order (`kill_switch` first) for the stop and the migrations, 40P01 maps to StoreBusy, the stop retries once, the reset never retries, plus a deadlock test. |
| A-ADV-5 | PROPOSE FIX | B8: a bounded wait (`limits.migrate_advisory_wait_ms`) before the advisory lock, with a clear message. New config, so PENDING LEAD 38. The existing two-migrate tests must still pass. |
| A-ADV-6 | PROPOSE FIX | B9 and a correction, confirmed by R20-3: the bound is concurrent transactions × N (22,000 at the defaults), not N + 22. Test with two transactions. |
| A-ADV-7 | PROPOSE FIX | B10: `old_by` keeps only NULL, a label or `dba`, and writes anything else as `unlabelled`; the migration replaces a raw `by` already in the row. Touches personal data, so PENDING LEAD 39. The false sentence is corrected. |
| A-ADV-8 | PROPOSE FIX | B11: 53300 maps to StoreBusy, pool max + 2 ≤ the runtime connection limit, and a runbook line for `pg_use_reserved_connections`. The reviewer's `reserved_connections` fix does not cover the PER-ROLE limit; I say so in B11. PENDING LEAD 41. |
| A-ADV-9 | PROPOSE FIX | B12: an exact `strpos(prosrc, quote_literal(g)||'::text')` check, with a killer that uses a similar group name (mut-P29). |
| A-COR-4 | PROPOSE FIX | B15: config is the one source; the `--reset-role` and `--stop-role` flags default to config, and a flag that differs is refused (mut-K9). |
| A-COR-5 | PROPOSE FIX | B20: the store calls the functions unqualified, as every store statement does (`store/postgres.py:2`). |
| A-COR-6 | PROPOSE FIX | B21 (a Nit, worth the one line): fixtures use `WITH INHERIT TRUE/FALSE` (works on 16, R20-2), and `transaction_timeout` joins the "not a control" list. |
| C-COR-1 | PROPOSE FIX | B0: a start gate (P1m, P3a and all five P4d merged, which matches order 20(2)), with the real names re-grepped at the base. Confirmed by grep: none exist today. |
| C-COR-2 | PROPOSE FIX | B14: item (d) passes `expect_version=0, expect_open=0` and returns 5; `cli.kill_switch` reset with a None argument returns 2 before calling `Limits.reset`. The false sentence is corrected. |
| C-COR-3 | PROPOSE FIX | B15: the full `migrate()` signature; numeric arguments default from `defaults.py` and tests pass N=5 directly; `reset_role` is required and keyword-only. |
| C-COR-4 | PROPOSE FIX | B16: the parser shape (`--by` enforced for stop and reset through `parser.error`, `whois NAME`, int flags for reset) and a store-down text for each action (mut-L50). |
| C-COR-5 | PROPOSE FIX | B17: both function texts compiled and ran on 16.15 (R20-1). The builder runs all three texts first on 16 and 17, and uses `#variable_conflict use_column` only if 17 refuses. |
| C-COR-6 | PROPOSE FIX | B18: detect the memory store with `isinstance(store, MemoryStore)`. |
| C-COR-7 | PROPOSE FIX | B19: print the masked label, never the typed text (`cli.py:396, 409` print the raw `by` today; mut-L51). |
| C-COR-8 | PROPOSE FIX | B12's last sentence: write `%%` for a literal `%` in a parameterised query. The probe's LIKE is gone after B12 anyway. |
| C-COR-9 | DECLINE | A Nit, and the reviewer says it is harmless and proposes no fix. B10 keeps NULL as NULL, so the `IS NOT DISTINCT FROM` path is unchanged. |

Cut surface: I looked for a feature whose deletion would close a finding. None does. B3 needs the request table, which the DBA recipe also uses. B8 cannot be closed by revoking the PUBLIC rights on the advisory-lock functions: that needs a superuser and affects other applications. The `limits check` and `whois` actions (C-COR-4) are needed for the probe and for "who stopped". PENDING LEAD 33 (cut reconciliation) remains the one open cut.

Couplings (each is a relay; I changed no sibling file):
- P4d owns `StoreBusy`, `is_connectivity_error` and the "Error rule". P2a-1 adds 40P01 and 53300 to the codes that mean busy and NOT done (B7, B11). P4d's text must not treat them as "unreachable".
- P3a owns migration numbering and `ACCEPTED_CHANGES`. The B3 triggers and the B10 `UPDATE` are new objects or data of P2a-1's own new release, so no new entry is expected (UNVERIFIED against P3a's layer-1 test). P3a's read-back of the lock settings must allow two `set_config('lock_timeout', ...)` calls (B8).
- P4b1: the meter's automatic stop shares the runtime connection limit (B11).
- P4d and P5 name the pool size, which B11 needs (PENDING LEAD 27(c)).
- The lead's S0 work also edits `ci.yml` (scan job, Dependabot). The 16 job lands in P2a-1's PR, rebased on main per order 20(5).
- P1m's runner: the new mutant total is 199 (196), B22.

PENDING LEAD (continues the ticket's numbering after 36; each has my recommendation; per CLAUDE.md I proceed with the recommendation if there is no answer):
37. Owner-side refusal triggers on the request table (B3; adds 3 G rows and 1 P row). Recommended: YES. A DBA's accidental `DELETE` would otherwise clear a stop and leave no trace, and the same friction already guards `kill_switch` and `kill_switch_resets`. Alternative: keep the body as it is and state the gap.
38. New config field `limits.migrate_advisory_wait_ms`, default 60000 ms, minimum 1 (B8). Recommended: YES, at 60000. Without it, any login can make `migrate` wait forever.
39. `old_by` and a raw `by` already in the row become `unlabelled` unless they are NULL, a label or `dba` (B10). The existing raw names stay only in core's older audit rows. Recommended: YES. It is the masking rule. The cost is that the "who" of a stop made before the migration is lost from the new table.
40. Config gets `limits.runtime_role` and `limits.stop_role`, and the CLI `migrate` role flags default to config and refuse a differing value (B6, B15). Recommended: YES. It gives one source and makes the probe correct from every login.
41. 53300 counts as "store busy", and the runtime connection limit must be at least the pool max + 2 (B11). Recommended: YES. The number waits on 27(c).

Counts: 24 findings: PROPOSE FIX 23, CONTEST 0, ESCALATE 0, DECLINE 1. 23 accepted fixes, written as build notes B0-B22 plus 6 "corrected at build start" lines. Remaining unaddressed: 0, apart from PENDING LEAD 37-41 (recommendations given) and the PostgreSQL 17 facts left UNVERIFIED for the 17 job. Mutants: 178 → 199 (196 if PENDING LEAD 33 is accepted).
