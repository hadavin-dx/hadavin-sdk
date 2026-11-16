# AK-G15 round 3 resolve (ticket revision 3; LAST review round)

**Honest note (read first).** This is the resolve step: `egm:egm-resolve`, invoked through the Skill tool in AUTO mode. As the brief ordered, I skipped the interactive gate and wrote this file in place of the skill's default `goldfish_review_report.md`. I did not write revision 3, so I have no author memory of it.

**What I ran.** Nothing was executed: no pytest, no PostgreSQL, no import of the package, no install, no network. I read:
- the whole ticket, all 606 lines at `d725725`;
- both round 3 reports and the round 2 resolve;
- `LEAD-ORDERS.md:51` and `:80`, which hold the round cap;
- `tickets/P8a.md:5` and the AK-G16 freeze notes (`tickets/AK-G16.md:462-470`), for the banner and MEANWHILE style;
- the AK-G2 lines `:142`, `:148`, `:167`, `:172`, `:175`, `:181`, `:185`, `:221` and AK-G2 BN-24/BN-25 (`:718-734`);
- `tickets/P2a.md:244-245` and `:515` (B20).

In `src/` (last commit touching it: `ce70eb5`) I read and grepped:
- `store/migrate.py:75-90`, `:150-211` and `:283-300`;
- `cli.py:138` and `:312-341`;
- `models.py:36-47` and `:69-75`;
- `app.py:148-160`;
- a grep for `def resolve` and `deps`.

**What I did NOT check:**
- Any PostgreSQL behaviour. That covers `ALTER FUNCTION ... OWNER TO` rights, INHERIT and SET membership options, custom SQLSTATE classes, whether functions are looked up in `pg_temp`, CHECKs over `text[]`, and the planner. Where a decision leans on one of these, the note says UNVERIFIED and names the evidence row.
- P2a-1 as merged (it is not merged), including how it substitutes `<S>` into function bodies.
- AK-G1 lines. No R3 finding needed a new AK-G1 cite; the AK-G1 sweep's behaviour on a new refusal code is relayed, not checked.
- Whether `tests/test_repo_rules.py` accepts `queue/`.
- `origin/main` against `ce70eb5`.
- The R3-COR reviewer's "?" lines. I re-found each one by its quoted text, and every row below cites the line I found.

I edited the ticket only by appending the build notes and changing line 1 to say FROZEN. I committed only this file and the ticket. I did not push and did not write DECISIONS.md.

- **Status:** resolved (AUTO). The ticket is FROZEN at revision 3. Build notes AK-G15 BN-1 to BN-27 are appended to the end of `tickets/AK-G15.md`.
- **Target:** `tickets/AK-G15.md` revision 3 DRAFT, commit `d725725`, full file (606 lines).
- **Findings:**
  - `reviews/AK-G15-round3-adversarial.md`: R3-ADV-1..18; 0 Blocker, 8 Major, 1 Minor-to-Major, 7 Minor, 2 Nit.
  - `reviews/AK-G15-round3-correctness.md`: R3-COR-1..17; 0 Blocker, 6 Major, 8 Minor, 3 Nit. The reviewer's context was compacted, so every R3-COR row below was re-verified by me.
- **Gate:** round 3 of 3 (order 20 item 6, `LEAD-ORDERS.md:80`: "The cap is 3 rounds counting from round 1; a money or redaction package whose last round had no Blocker and at most 2 Majors may take one more").
  - Round 3 had 0 Blocker and 14 Majors (8 adversarial plus 6 correctness; ADV-9 "Minor-to-Major" not counted).
  - So the round-4 condition is NOT met: no round 4.
  - Under the design-doc stop rule (`.claude/rules/review-loop-speed-rules.md`), the remaining Majors become build-time fixes. They are the build notes.
  - The RESULT review of built code has no round cap (money, redaction, security path).
- **Build-blocking items:** NEEDS LEAD 23, 24 and 25 below. Until the lead answers, the builder leaves out exactly the parts their MEANWHILE notes name (AK-G15 BN-6, AK-G15 BN-2, AK-G15 BN-4). Everything else is decided.

## Facts I checked myself (they decide rows)

1. **The canary fits `READER_PATTERN` (ADV-1 is right).** `person-1@example.invalid` uses only `a-z`, `0-9`, `-`, `@` and `.`, and is 24 characters long. Every character is in `[A-Za-z0-9_.:@-]`, and the first character is a letter, so it matches `[A-Za-z0-9][A-Za-z0-9_.:@-]{0,127}` (ticket `:220`). The `tenant` CHECK (`^[a-z0-9][a-z0-9_-]{0,62}$`) does refuse it, because `@` and `.` are outside that set. So only the `readers`, `assignee` and `closed_by` cases of Q4 (`:297`) cannot pass.
2. **A waiting receipt always has a `run_id` (COR-2 is right; the ticket misread AK-G2).**
   - `tickets/AK-G2.md:142`: `run_id` is "`run_id_for(delivery_key, generation)` on every receipt that is not an id-reuse row; `None` on an id-reuse row, which never gets a run, a dead letter or a reopen".
   - `:181`: `receive` writes `run_id=run_id_for(key, 0)`.
   - `:167`: a reopen writes the formula again.
   - `:148` and `:242`: an id-reuse row is always `refused`, and `needs_person`/`id_reuse` is a `ValueError`.
   - So no `needs_person` receipt has a NULL `run_id`. `:172` ("nullable") and `:175` ("a NULL `run_id` stays NULL") are about id-reuse rows only.
   - The ticket's example (`:184`, "a `body_missing` receipt that never ran") is wrong: `:185` sets `body_missing` on a receipt whose `run_id` was written at `:181`.
   - This also removes the text tension of PENDING LEAD 21: the NULL case never reaches the re-run.
3. **Collection starves behind a full tenant (ADV-3 and COR-1 are right).**
   - The SELECT is one global `ORDER BY r.received_at ... LIMIT 500` (`:211`).
   - `room` is applied only after the SELECT (`:212`).
   - `queue_watch` stops a tick when a batch "creates fewer than the limit" (`:242`).
   - So a tenant at its ceiling with 500 or more older receipts fills batch 1, nothing is created, and the loop stops.
   - The "many `key_conflict` rows never cleared" half of COR-1 does NOT hold. A held key's columns equal the receipt's (the key CHECK, `:220`), so the anti-join (`:211`) excludes that receipt and it never re-enters a batch. That part is contested.
4. **How roles reach the database today (COR-3, COR-9 and ADV-6).**
   - `migrate()` takes only `runtime_role`, `portal_role` and `purge_role` (`store/migrate.py:285-292`). `cli._migrate` passes exactly those three (`cli.py:138`, `:312-334`). No migration creates a role.
   - `_SAFE_CREATE` (`store/migrate.py:80-84`) accepts `CREATE OR REPLACE FUNCTION` and `CREATE TRIGGER`. Every other `CREATE`, `CREATE ROLE` included, is refused ("extend the guard", `:78-79`).
   - So:
     - the re-run function passes the guard as `CREATE OR REPLACE FUNCTION`;
     - neither new role can be created in a migration file;
     - the ticket's "the `queue_worker` role" in -a's migration (`:159`) and "the creation of the re-run owner role" under AK-G2 BN-24 option (ii) (`:249`) cannot be built as written;
     - a literal role name `queue_worker` would break the no-hardcoding rule. The three existing roles are arguments.
   - `migrate` grants `USAGE ON SCHEMA current_schema()` to each role it handles (`:172-173`). `effective_problems` already reports a role that can CREATE in the schema (`:197`, `:210-211`).
   - P2a's frozen `migrate(reset_role=...)` is REQUIRED and checked NOLOGIN, distinct and not a member (`tickets/P2a.md:244-245`). That is the pattern to follow.
   - `cli.py` is therefore touched, whatever `:150` says: it must pass the new role arguments.
5. **The schema name is resolved at migration time (COR-10).**
   - `migrate` reads `current_schema()` (`store/migrate.py:172`, `:210`).
   - P2a B20 (`tickets/P2a.md:515`): "The store calls the functions UNQUALIFIED ... like every other store statement (the schema comes from the DSN's `search_path`) ... `<S>` stays only inside the function bodies and in `migrate()`."
   - So `<schema>` is not an open name. It is `migrate`'s `current_schema()`, substituted into function and trigger bodies. The store's own SQL (`:201` call, `:211` SELECT) is unqualified.
6. **Cites (ADV-17, COR-11, COR-16, COR-17).**
   - `canonical_json` is at `models.py:38-43` and `sha256_hex` at `:46-47`. The ticket's `:116` is right; `:192` says `:36-41`.
   - The `OPEN_STATES` comment is at `models.py:72-74`, not `:71-73` (`:115`).
   - `deps.resolve` does not exist: grep finds no `deps` in `app.py` and no `def resolve` outside `actions/executor.py:33`, `backends/platform_secrets.py:26` and `tools.py`. The purge store is built by `make("store", b.store.model_copy(...), secrets)` (`app.py:151-160`).
7. **Mutant killers re-traced (COR-4, COR-5, COR-6, COR-7).**
   - **M-a9** (`version = expect_version` removed from claim). The case Q7 names, "one version, two claimers", is refused by the state clause anyway: the item is `claimed` with a live lease held by someone else. But Q7's first sentence, "a wrong `expect_version` gives `stale` for claim", on an OPEN item has no other guard, so it kills M-a9. COR-4 is right about the named case and wrong that nothing kills the mutant.
   - **M-b4** (no conflict clause). "A second collection creates none" (N1) never reaches the INSERT, because the anti-join excludes the receipt. COR-4 is right.
   - **M-b11** (Python body pre-check removed). The function's step (5) gives the same `subject_erased`, so N4 as written cannot tell the difference. COR-5 is right. But the pre-check runs BEFORE `write_intent` (check (3), `:232`, then the intent, `:234`). So "no audit event on this refusal" is an observable difference, and the mutant is not equivalent.
   - **M-a41, M-a43, M-b28.** Their extra right is still refused by a trigger (the update or delete trigger, or AK-G2's trigger), so "refused" alone does not kill them. Only the SQLSTATE (`42501`) or the catalogue does. COR-6 is right.
   - **M-a51 and M-b41 round arms.** A held chat key equals `run_id`, and a held inbound key is the round-0 formula. The key CHECK (`:220`) makes a `round > 0` holder of either key impossible on Postgres, even with the trigger disabled (disabling a trigger does not disable a CHECK). COR-7 is right; only the memory store's dict plant reaches those arms.
8. **COR-13 is wrong (contested).** `close` never takes `closed_by`:
   - the store method takes `assignee` and "sets `closed`, `outcome`, `closed_by = assignee`" (`:200`);
   - the function does the same (`:202` step 7);
   - `StoreQueue.close(tenant, item_id, person, ...)` (`:231`) passes `person` as `assignee`;
   - Q8 and Q9 test "`closed_by` different from `assignee`" only as an owner raw UPDATE (`:302`).
   
   Interface, function and tests agree.
9. **COR-15 is wrong (contested).** PL20-22 are marked "INFORM (new)" (`:531`, `:536`, `:537`). `:107` defines INFORM as "my decision on my recommendation, final unless the lead says otherwise". The CHANGELOG counts them as INFORM (`:604`). That is their status.

## Decisions (35 finding ids; duplicates merged into 28 rows; one decision per row)

| id(s) | category | decision (the build note that carries it) |
|---|---|---|
| R3-ADV-1 | PROPOSE FIX | A second canary for the staff-id columns: `person 1 note` (it holds spaces, so it fails `READER_PATTERN`). Q4's `readers`-element, `assignee` and `closed_by` cases use it. Every other Q4 case keeps `person-1@example.invalid`. Q4 also states that a reader-shaped string, e-mail shape included, passes the staff-id CHECKs by design (fact 1). AK-G15 BN-1. |
| R3-ADV-2 | PROPOSE FIX (wording) + **NEEDS LEAD 24** (redaction, threshold) | **Decided:** `:140` and `:285` ("cannot store text") are overstated. The true statement is that the CHECKs refuse free text (spaces, any character outside each pattern) but cannot stop a holder of the runtime or worker connection from encoding data into id-shaped columns: `readers` (no upper bound today, up to 128 characters per element), `assignee`, `closed_by`, and the hex columns `binding`, `delivery_key` and `item_id`. **MEANWHILE (NEEDS LEAD 24):** a cap `cardinality(readers) <= defaults.QUEUE_MAX_READERS` (50), a config validator, a Q4 case and mutants M-a83 and M-c18. Not built until answered. AK-G15 BN-2. |
| R3-ADV-3 + R3-COR-1 | PROPOSE FIX (COR-1's `key_conflict` half CONTESTED, fact 3) | Collection selects per tenant. For each configured tenant whose `room > 0`, in sorted order: one SELECT with `r.tenant = %s` and `LIMIT min(room, limit)`. Tenants with `room <= 0` are skipped before any SELECT. `queue_watch` repeats batches while any tenant filled its per-tenant limit, at most `QUEUE_COLLECT_BATCHES`. No signature change. New N2 case: `tenant-a` at its ceiling with 600 older waiting receipts plus 10 newer `tenant-b` receipts gives `tenant-b` 10 items on the first tick. Mutant M-b44 (one global SELECT again), killed by that case. AK-G15 BN-3. |
| R3-ADV-4 | **NEEDS LEAD 25** (thresholds from config; the safety path) | **MEANWHILE:** the ceiling counts per (tenant, kind). Chat hand-offs and inbound items each may have up to `queue.max_waiting_items` waiting items, with no new setting. A mass inbound event can then not refuse a chat hand-off. Entry 22's wording changes (PENDING LEAD 26). Not built until answered: the shared ceiling of revision 3 stays. If answered, Q21 and N2 gain the per-kind case and mutants M-a84 and M-b52 are added. AK-G15 BN-4. |
| R3-ADV-5 | PROPOSE FIX | A dedupe hit on a `closed` holder is a refusal, not a success. `open_handoff` raises `QueueRefused("key_closed")` (code 14) and writes no event. AK-G1 then ends the run `handoff_unavailable`: a person already closed that hand-off, and the conversation is not marked handed off with nobody looking. The decoy check runs first, so a closed decoy with another binding stays `key_conflict`. New Q1 case. Mutant M-a75. Relay to AK-G1 (PENDING LEAD 27). AK-G15 BN-5. |
| R3-ADV-6 + R3-COR-3 + R3-COR-9 + R3-COR-14 | PROPOSE FIX (roles, arguments, guard) + **NEEDS LEAD 23** (least privilege: the ownership transfer) | **Decided (fact 4):** neither role is created by a migration. The database administrator creates `queue_worker`'s login role and the NOLOGIN re-run owner role before migrating, as for the existing roles. `migrate` gains `worker_role` (optional, like `runtime_role`; -a) and `rerun_owner_role` (REQUIRED once -b's migration is pending; `ConfigError` naming the argument; -b, or AK-G2-a under AK-G2 BN-24 option (i)). Both go through `_ROLE`, the distinct check and the not-member checks, as `reset_role` does. `cli.py migrate` gains `--worker-role` (-a) and `--rerun-owner-role` (with AK-G2 BN-24's build). `:150` "`cli.py` is not touched" is withdrawn. The function is created as `CREATE OR REPLACE FUNCTION`, which `_SAFE_CREATE` accepts; the guard is not extended. The trigger literal is written by whichever migration builds AK-G2 BN-24's guard (the lead's open choice (i)/(ii), unchanged), from the same `rerun_owner_role` argument. Rows Q15 and N12c gain the argument cases; mutants M-a76 and M-b45. **MEANWHILE (NEEDS LEAD 23):** the ownership transfer. The migration grants the owner role CREATE on the schema and the migrating role SET membership of the owner role, runs `ALTER FUNCTION ... OWNER TO`, and REVOKES both in the same migration. N12c then asserts that the owner holds no CREATE and that no login role, the migration role included, is a member. N12b's expected set stays {worker, owner}. Not built until answered: -b leaves out the ownership-transfer step and the N12b/N12c expected-set assertions; it can build no re-run without them. AK-G15 BN-6. |
| R3-ADV-7 | PROPOSE FIX | -b's insert-trigger cross-check adds `NEW.run_id = <the receipt's run_id>`. This is possible because AK-G15 BN-19 makes it NOT NULL; the runtime role already reads the column, AK-G2 `:221`. The collect-side comparison already covers it through `binding`, which includes `run_id`. With this, `:44` item (6) and `:288` ("differ only in `readers` and `binding`") become true. N2's trigger-side decoy gains "another `run_id`". Mutant M-b46. AK-G15 BN-7. |
| R3-ADV-8 | PROPOSE FIX | The key CHECK is written per round: `round > 0` -> the reopen formula (both kinds); `round = 0 AND kind = 'chat'` -> `= run_id` and the run pattern; `round = 0 AND kind = 'inbound'` -> the inbound formula. Q10 gains a Postgres case: a CHAT item reopened (round 1) is accepted. M-a71's killer list adds it. AK-G15 BN-8. |
| R3-ADV-9 | PROPOSE FIX | The update trigger also refuses `NEW.lease_until > NEW.updated_at + defaults.QUEUE_LEASE_MAX_S` (86400 s). That constant replaces the literal `le 86400` on `queue.lease_s`, and N14 pins it. A Q15 case as worker. Mutant M-a77. AK-G15 BN-9. |
| R3-ADV-10 | PROPOSE FIX (wording) | `opened_at` of an inbound item is the collection tick's injected `now`, not `received_at`, which the clock window would refuse. So age counts from collection. A receipt held back by the ceiling is already loud (`queue_full`). Said in Interface 4 method 11 and in limit 13 (PENDING LEAD 26). AK-G15 BN-10. |
| R3-ADV-11 | PROPOSE FIX (wording) | `:229` becomes "repaired when the caller retries". Opens write no `write_intent` because an open is the safety path: an audit outage must not turn every hand-off into `handoff_unavailable`. `write_outcome` never raises (`audit/protocol.py:23-25`). `already_open` events stay: one per retry or sweep tick per not-yet-committed takeover. That growth is bounded by `queue_watch` failing the tick once the item passes the service time. Said plainly; no code change. AK-G15 BN-11. |
| R3-ADV-12 | PROPOSE FIX | N3b (2)'s second item is planted as owner with the insert trigger disabled, as a `round = 1` item: `reopens` = the first item's id, the reopen-formula key, `reason = 'reopened'`, the same subject columns, `state = 'claimed'` with its holder and lease. This passes every CHECK, the unique key, `queue_items_successor` and `queue_items_inbound_subject` (that index covers round 0 only). AK-G15 BN-12. |
| R3-ADV-13 + R3-COR-12 | PROPOSE FIX | New mutants: M-a78 (one id-pattern CHECK removed; one variant per CHECK over `tenant`, `item_id`/`reopens`, `conversation_id`, `run_id`, `delivery_key`, `source`, `binding`; each variant killed by its Q4 direct-INSERT case); M-a79 (the `assignee`/`closed_by` CHECK removed; Q4 worker case with AK-G15 BN-1's canary); M-a80 (the round-bound CHECK removed; Q9 trigger-disabled `round = 21`); M-a82 (the ceiling compare `<` changed to `<=`; Q21 boundary); M-b49 (function step (1), the 0-10 range check, removed; N4b direct call with `p_max_reruns = 11`). The 600-second window's exact boundary is NOT mutated: `clock_timestamp()` moves during the test, so a boundary case would be flaky. M-a68, M-a69 (removal) and N14 (the literal) cover it, said plainly. AK-G15 BN-13. |
| R3-ADV-14 | PROPOSE FIX | "Strict expected failure until BN-24 is built" is deleted from N13: AK-G2 BN-24 is a HARD dependency of -b. Under AK-G2 BN-24 option (ii), N13 fails by assertion on -b's base and is -b's FAIL-BEFORE (`b-failbefore.txt`); `:291` "-b has no fail-before" is corrected for that case. Under option (i) it is a premise check that passes on the base. AK-G15 BN-14. |
| R3-ADV-15 | PROPOSE FIX (wording) | `queue_full` in `queue_watch` means "AT the ceiling: the next new item will be refused". It fires at `open + claimed >= max_waiting_items` even when nothing was refused yet, on purpose (an early loud signal). Said in W4 and Interface 7. AK-G15 BN-15. |
| R3-ADV-16 | PROPOSE FIX | The function raises each code with its own SQLSTATE: `ERRCODE` `QS001` `stale`, `QS002` `outcome_unknown_not_acknowledged`, `QS003` `rerun_limit`, `QS004` `subject_erased`. These are constants in `defaults.py` and pinned by N14. The store maps by exact SQLSTATE only; any other error propagates unchanged, whatever its message. Whether these codes collide with a PostgreSQL class is UNVERIFIED (the `b-postgres.txt` evidence). N3 gains: a test-only trigger raising with message `stale` (default SQLSTATE) propagates as a database error, not `StaleState`. Mutant M-b47. AK-G15 BN-16. |
| R3-ADV-17 + R3-COR-11 + R3-COR-17 | PROPOSE FIX (cites) | `:192` `models.py:36-41` -> `:38-43`; `:115` `:71-73` -> `:72-74` (fact 6). Line numbers stay informative, never test literals (`:111`). AK-G15 BN-17. |
| R3-ADV-18 | PROPOSE FIX (wording) | Done names the helpers per sub-PR: `database_identity()` ships in -a (`:248`) and `role_memberships()` in -b (`:249`); both are first called by -c's `app.build`. AK-G15 BN-18. |
| R3-COR-2 | PROPOSE FIX (cut surface) | Fact 2. `NeedsPersonItem.run_id` becomes `str` (required) for both kinds; the CHECK requires `run_id IS NOT NULL` for every row. Deleted: function step (4)'s NULL branch; N1's and N3's NULL cases (N1 instead: a `needs_person` receipt planted as owner with a NULL `run_id` makes collection fail loudly, no item); the `item.run_id or "-"` fallback (every event writes `item.run_id`); R2-COR-3's text at `:16` and `:184`. PENDING LEAD 21 is WITHDRAWN (moot). Mutant M-b43 (the NOT NULL CHECK removed for inbound), killed by an N1 owner trigger-disabled INSERT. AK-G15 BN-19. |
| R3-COR-4 | PROPOSE FIX (CONTESTED in part, fact 7) | M-a9's killer is Q7's "wrong `expect_version` on an OPEN item" case, plus a new stale-view case: claim, release, then a claim with the version listed before the claim gives `stale`. The "one version, two claimers" case stays as a state-clause test, NOT named as M-a9's killer. M-b4's killer is a new N2 race case: a REAL second collection inserts the same receipt between this collection's SELECT and INSERT (the test hook of `:319`). With the clause this gives no error and no `key_conflict`; without it, the unique violation fails the call. AK-G15 BN-20. |
| R3-COR-5 | PROPOSE FIX (deletion option DECLINED) | M-b11 is not equivalent (fact 7). N4's "body erased" case also asserts that NO audit event (intent or outcome) was written, which only the Python pre-check gives. M-b11 is kept, with that killer. AK-G15 BN-21. |
| R3-COR-6 | PROPOSE FIX | Every denied statement in Q15, N12 and N12c runs as its role and asserts SQLSTATE `42501` (`insufficient_privilege`), not just "refused" or "row unchanged". Q15 and N12 also check the catalogue for every role and relation of the grants table: `has_table_privilege` / `has_column_privilege` true exactly for the listed rights. M-a41, M-a43 and M-b28 name these assertions. AK-G15 BN-22. |
| R3-COR-7 | PROPOSE FIX | M-a51 is redefined as "the dedupe-hit binding comparison removed", killed by Q1 on both stores. New M-a81 (round comparison removed), killed by Q1's memory dict plant only. M-b41 is redefined as the binding/reason arms (N2, both stores). New M-b48 (round arm), killed by N2's memory plant only. Said plainly: on Postgres the key CHECK makes the round arms unreachable (fact 7). They stay as a second line. AK-G15 BN-23. |
| R3-COR-8 | PROPOSE FIX | N3b's technique is named. A third connection holds `SELECT ... FOR UPDATE` on the receipt row, then both calls start. The test waits until both show `wait_event_type = 'Lock'` in `pg_stat_activity` (bounded: 10 s, then fail), then commits the third connection. Under M-b32 the calls do not wait. The test then asserts the outcome anyway: AK-G2's trigger refuses `received -> received`, so the second call fails with an error, not `stale`. M-b33's killer stays N3b (3). AK-G15 BN-24. |
| R3-COR-10 | PROPOSE FIX | Fact 5. `<schema>` is `migrate`'s `current_schema()`, substituted into the function and trigger bodies when the file is applied (P2a B20's `<S>`, as P2a-1 merges it). The store calls `hadavin_queue_close_rerun(...)` and runs the collection SELECT UNQUALIFIED, like every store statement. "UNVERIFIED" is removed from `:105` for the name source. Only P2a-1's substitution mechanism stays UNVERIFIED. N15 is unchanged. AK-G15 BN-25. |
| R3-COR-13 | CONTEST | Fact 8. No change. |
| R3-COR-15 | CONTEST | Fact 9. No change. PENDING LEAD 21's status does change, through AK-G15 BN-19 (WITHDRAWN). |
| R3-COR-16 | PROPOSE FIX (cite) | `:241` and `:278` "`deps.resolve`" become "`make("store", ..., secrets)`, as the purge store (`app.py:151-160`)"; the secret is read through the secrets kind passed to `make`. AK-G15 BN-26. |

**Category counts (28 rows):** 26 rows carry a build note: 23 PROPOSE FIX, 2 PROPOSE FIX with a NEEDS LEAD part (ADV-2, the ADV-6 group), 1 NEEDS LEAD (ADV-4). Three of the 23 hold a CONTESTED part (the ADV-3 group, COR-4, COR-5). CONTEST 2 (COR-13, COR-15). DECLINE 0. ESCALATE 0.

**Naming:** this ticket's new notes are "AK-G15 BN-n". In the ticket text above the notes, a bare "BN-24" or "BN-4" means AK-G2's build note, as before.

## Positions (the reasons behind the larger calls)

- **COR-2 is a cut, not a patch.** AK-G2's own text says a waiting receipt always has a `run_id`. Keeping a NULL branch meant:
  - a function branch;
  - two test cases;
  - an audit fallback;
  - an open text tension (PL21);
  
  all for a state that cannot occur. Making it NOT NULL removes all of it and makes ADV-7's fix possible. Confidence 85 percent: AK-G2 is not built, so this is ticket text. If AK-G2's build ever lets a waiting receipt hold NULL, collection fails loudly rather than silently, which fails closed.
- **ADV-3 is fixed per tenant in the store, not by a window query.** One SELECT per tenant with room is simpler to read and test than `row_number()` over a partition, and it uses AK-G2 BN-4's index (tenant leading) directly. The cost is one round trip per configured tenant per batch. That is a few per deployment (one client per deployment, order 27 item 56).
- **ADV-5 refuses instead of returning the closed item.** The two bad outcomes are not equal:
  - Returning the closed id silently loses a conversation: it is marked handed off and no one looks.
  - Refusing sends AK-G1 down its existing loud `handoff_unavailable` path.

  Refusing follows R368 ("terminal state for every message", never silent). Reopening the item does not clear it, because the sweep uses the run-id key. That is said in the relay to AK-G1 (PENDING LEAD 27).
- **ADV-6's open part is only the ownership transfer.** Who creates roles, the role arguments and the CLI flags follow the existing `runtime_role` and P2a `reset_role` pattern, so they are decided. The temporary CREATE and membership is a least-privilege choice about a DBA identity, so it goes to the lead.
- **ADV-4 goes to the lead even though it adds no setting.** It changes what an existing client-contract number means: the total waiting items can reach twice the number. That is the owner's "thresholds from config" rule.

## Couplings (text other owners change; this resolve edits none of their files)

- **AK-G2 BN-24.** Whichever PR builds the guard (option (i) AK-G2-a, or (ii) AK-G15-b, still the lead's choice) takes `migrate(rerun_owner_role=...)` as a required argument and the `--rerun-owner-role` CLI flag (AK-G15 BN-6). Under (i) that cost falls on AK-G2-a.
- **AK-G2 text:** PENDING LEAD 21 is withdrawn. AK-G2 needs no build-note question. The function always writes the formula `run_id`, exactly `:167`.
- **AK-G1:** PENDING LEAD 27 (new refusal `key_closed`).
- **owner-visible-limits.md (the lead's file):** PENDING LEAD 26.
- **P2a-1:** the `<S>` substitution and the role-argument checks are reused (AK-G15 BN-6, AK-G15 BN-25).

## PENDING LEAD (continuing the ticket's numbering after 22; my recommendation first)

- **23. NEEDS LEAD (least privilege): how the re-run function gets its owner.** PostgreSQL (general knowledge, UNVERIFIED here) lets a role run `ALTER FUNCTION ... OWNER TO r` only if it can SET ROLE to `r` and `r` holds CREATE on the schema; a superuser bypasses both.
  - (a) **Recommended:** the migration grants both temporarily (owner CREATE on the schema; the migrating role SET membership of the owner role, `INHERIT FALSE` where the server supports it), runs the ALTER, and revokes both in the same migration. N12c asserts the end state. A later migration that replaces the function body repeats the same grant-alter-revoke.
  - (b) A superuser runs -b's migration. That adds no extra grant, but the deploy then needs a superuser login.
  - (c) The migration role stays a member of the owner role permanently. That is simpler, but the migration role then holds the re-run right through `SET ROLE` for ever, and N12b's set grows.
  
  Confidence in (a) 65 percent: the revoke-by-self step is UNVERIFIED and P2a-1's role setup is not merged. **Build effect until answered:** -b builds everything except the ownership-transfer step and the N12b/N12c end-state assertions. No re-run works without them, so -b cannot finish before the answer.
- **24. NEEDS LEAD (redaction, threshold): an upper bound on the staff-id columns.**
  - (a) **Recommended:** `defaults.QUEUE_MAX_READERS = 50`, a CHECK `cardinality(readers) <= 50` pinned by N14, and a config validator that refuses a tenant with more than 50 queue readers. The honest residual is stated: a holder of the database password can still encode data into id-shaped columns, at most about 6.4 KB in `readers` plus the hex columns per row.
  - (b) No cap; the wording only.
  - (c) Stricter: a database table of allowed staff ids, with `readers`, `assignee` and `closed_by` checked against it. That is a new table, new grants and a new sync path.
  
  Confidence 70 percent. **Build effect until answered:** -a and -c leave out the cap, its Q4 and W2 cases and mutants M-a83 and M-c18. The corrected wording (AK-G15 BN-2) is built either way.
- **25. NEEDS LEAD (thresholds from config; a safety path): one ceiling for both kinds or one per kind.**
  - (a) **Recommended:** per (tenant, kind), the same `queue.max_waiting_items` for each. A burst of inbound messages can then not refuse chat hand-offs.
  - (b) Shared, as revision 3, with the trade-off said in entry 22.
  - (c) A separate setting for inbound.
  
  Confidence 70 percent. **Build effect until answered:** the shared ceiling of revision 3 is built; the per-kind count, its cases and mutants M-a84 and M-b52 are not.
- **26. INFORM: owner-visible wording for the lead** (`owner-visible-limits.md`).
  - (13) add: "The waiting time of a received message is counted from when the queue picked it up, at most one regular check after it arrived; while the queue is full, the full-queue alarm is raised instead."
  - (21) add: "A fake item for a received message must match the real message in every id, including its run, so it can differ only in who is listed as able to see it."
  - (22) add: "The alarm fires as soon as the queue is exactly full, before anything is refused." If PL25 (a) is chosen, also: "Chat hand-offs and received messages each have their own limit of that number."
  - New sentence for the redaction limits: "The database refuses free text in every queue column. Someone who holds the database password could still hide coded data in the id columns (at most about 6 KB per item if PL24 (a) is chosen)."
  
  Recommendation: apply as written. Confidence 75 percent. Not an owner item; the redaction residual is decided by PL24.
- **27. INFORM: relay to AK-G1.** `open_handoff` can raise `QueueRefused("key_closed")` when a person closed the hand-off item before the takeover committed. AK-G1 handles it as any raising hook (`handoff_unavailable`). Its sweep then fails loudly for that run; reopening the item does not clear it, because the key is the run id. Recommendation: the lead adds one line to AK-G1's build notes, as for AK-G1 BN-29. Not an owner item.

## Counts (after the decided notes; the MEANWHILE items apart)

- **Rows:** 51 stay 51 (a 24, b 18, c 9). Extended without a new id: Q1, Q4, Q7, Q9, Q10, Q15, Q21, N1, N2, N3, N3b, N4, N4b, N12, N12c, N13, N14, W4. Cases deleted: N1's and N3's NULL `run_id` cases (AK-G15 BN-19).
- **FAIL-BEFORE:** Q0 (premise); N13 under AK-G2 BN-24 option (ii) (AK-G15 BN-14).
- **Mutants:** 128 + 15 = **143** (a 80, b 46, c 17).
  - New in -a: M-a75 to M-a82 (8).
  - New in -b: M-b43 to M-b49 (7).
  - Redefined: M-a9 (killers), M-a51 (binding arm), M-b4 (killer), M-b11 (killer), M-b41 (binding/reason arms), M-a41/M-a43/M-b28 (SQLSTATE killers), M-a71 (killer list).
- **If PL23-25 are answered as recommended:** +M-b50, M-b51 (PL23), M-a83, M-c18 (PL24), M-a84, M-b52 (PL25), giving **149** (a 82, b 49, c 18). Rows stay 51.
- **Other counts:**
  - `QueueRefused` 14 codes (+`key_closed`); `RerunRefused` 3 codes.
  - Store methods 12 (a 10, b 2) plus 2 Postgres helpers (`database_identity` -a, `role_memberships` -b).
  - `migrate` arguments +2 (`worker_role`, `rerun_owner_role`); `cli.py migrate` flags +2.
  - New `defaults.py` constants: `QUEUE_LEASE_MAX_S`, `QUEUE_RERUN_SQLSTATES`, plus `QUEUE_MAX_READERS` only under PL24.
- **PENDING LEAD:** 27 items. Open NEEDS LEAD: 1-6, 11, 23, 24, 25. ANSWERED: 13-19. INFORM: 8, 9, 12, 20, 22, 26, 27. Replaced: 7, 10. WITHDRAWN: 21.
- **Ids:** 35 finding ids, 28 decision rows, 27 build notes (26 rows with a fix + AK-G15 BN-27 totals; the 2 CONTEST rows have no build note).
