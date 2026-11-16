# Goldfish Annotated Review Report (resolve, round 1)

Status: findings categorised; fixes to be applied by the ticket author under the owner's standing instruction (see the note below)

**Target:** `handover/tickets/P4d.md` (full file). Findings: `handover/reviews/P4d-round1-adversarial.md`, `handover/reviews/P4d-round1-correctness.md`. Decisions applied: `handover/studio-notes/amendments.md` A11, A12, A13.

Counts: PROPOSE FIX 37, ESCALATE 0, CONTEST 0, DECLINE 0. Nothing was contested: for every finding the reviewer cited a file and line that could be read, and the author re-checks it before editing. The skill's severity names are Blocker / Major / Nit; the review files say BLOCKER / MAJOR / MINOR (MINOR = Nit, and every Nit is also fixed because the fix is cheap).

Note on the gate (skill Step 4): the owner told the cloud session to run resolve and rewrite the tickets, and set the standing rule that only major decisions wait for the owner. So the "auto accept" path is taken for every PROPOSE FIX; ESCALATE items are NOT applied as decisions: the ticket carries the recommended position marked PENDING LEAD and the item is listed in `handover/questions-for-lead.md`.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`egm-design`] - Severity: Blocker (finding id A1, adversarial)
*   **Affected Scope:** Interface `reserve_spend`; "Existing core code reused" (add_spend's upsert pattern); M4; R2 of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The ticket tells the builder to reuse the `add_spend` upsert pattern but gives no statement shape for the cap check. The natural form is `INSERT ... ON CONFLICT DO UPDATE SET usd = spend.usd + EXCLUDED.usd WHERE spend.usd + EXCLUDED.usd <= cap`. The DO UPDATE ... WHERE runs only on the conflict path. On the insert path (first reservation of the day or month, no row yet) the cap is never evaluated. Scenario: day_cap=1.00, empty database, `reserve_spend("r1","a",d,Decimal("5"), day_cap=Decimal("1"))`. The row is inserted with 5, no `SpendCapExceeded`, the cap is overshot on the very first call. Every R2 row uses amounts at or below the cap and starts from a fresh counter, so no listed test or mutant catches it. M4 only covers "check in Python".
*   **Rationale:** evidence: The reuse source is postgres.py:416-431, where the `ON CONFLICT` has no WHERE. Ticket lines 24, 38, 50 and 68.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decided by A13(2). The finding is valid: the reviewer cites evidence that can be read (The reuse source is postgres.py:416-431, where the `ON CONFLICT` has no WHERE. Ticket lines 24, 38, 50 and 68.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface `reserve_spend`; "Existing core code reused" (add_spend's upsert pattern); M4; R2
    *   Change: Specify the shape in the ticket. For example: ensure both counter rows exist (insert 0 on conflict do nothing), then `UPDATE spend SET usd = usd + %s WHERE agent_id=%s AND day=%s AND (%s IS NULL OR usd + %s <= %s) RETURNING`, then the same for the month, all in one transaction. Zero rows returned means rollback and `SpendCapExceeded`. Add tests: first reservation larger than each cap on an empty store (day cap and month cap separately), on both backends. Add mutants: "cap WHERE only on conflict path", "day cap ignored", "month cap ignored", "`<=` changed to `<`".

### [Issue 2] [`egm-design`] - Severity: Blocker (finding id A2, adversarial)
*   **Affected Scope:** `settle_spend`; R2 list; M6 of `handover/tickets/P4d.md`
*   **Discrepancy Description:** Settle-once is described as sequential ("first call sets status settled"). Nothing says the first-call decision must be one atomic claim, and no concurrent-settle test exists. R2 lists concurrent tests for add_spend, reserve, transition, create_run, record_decision, save_gate_decision and add_tool_call, but not settle. Expected naive build under READ COMMITTED: read the reservation, see open, move counters, write settled. Scenario: two handles settle R (reserved 1.00) with 0.20 and 0.40 at the same time. Both read "open" and both move counters, so the counters drop by 1.40 instead of 0.80. That is double settle and a lost reservation, and the sequential M6 test passes.
*   **Rationale:** evidence: Ticket lines 25, 50 and 70. The Postgres compare-and-set precedent is `UPDATE ... WHERE state = %s RETURNING`, postgres.py:257-268.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decided by A13(2). The finding is valid: the reviewer cites evidence that can be read (Ticket lines 25, 50 and 70. The Postgres compare-and-set precedent is `UPDATE ... WHERE state = %s RETURNING`, postgres.py:257-268.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: `settle_spend`; R2 list; M6
    *   Change: Mandate `UPDATE spend_reservations SET status='settled', settled_usd=%s WHERE reservation_id=%s AND status='open' RETURNING ...` as the claim, in the same transaction as the counter moves. The loser reads the stored first result. Fix the lock order in the ticket: reservation row, then day row, then month row. Add the R2 row "two handles settle the same id with different amounts, N repeats: counters reflect exactly one". Add a mutant "read-then-write settle". Memory is safe only because of its global lock; say so.

### [Issue 3] [`egm-design`] - Severity: Blocker (finding id A3, adversarial)
*   **Affected Scope:** `reserve_spend` idempotency ("Same id and same content returns the existing reservation") of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The rule says nothing about the status of the existing reservation. If a content-derived id is reused (for example the same prompt hash), the replay returns a SETTLED reservation and books nothing. The caller thinks it holds an open reservation, makes the provider call and nothing is counted. A lost reservation is silent overspend. The rule also never says which fields make up "content". Repeating the call after midnight changes `day`, so the idempotent retry becomes `ReservationConflict` and the first reservation stays open. Cap parameters are not stored, so "same content" cannot cover them.
*   **Rationale:** evidence: Ticket lines 24 and 58. The model has `status` and `day` (line 27).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decided by A13(2). The finding is valid: the reviewer cites evidence that can be read (Ticket lines 24 and 58. The model has `status` and `day` (line 27).). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: `reserve_spend` idempotency ("Same id and same content returns the existing reservation")
    *   Change: Define content as exactly (agent_id, day, reserved_usd, run_id), compared numerically on `Decimal`. A replay of a SETTLED id must raise `StaleState`, not return the row. A replay of an open id returns the row with `status == "open"`, and the Protocol docstring tells callers to check it. Decide and document whether `day` belongs in identity. Safest is that the first reservation's day stands and a retry with a different day is `ReservationConflict` with a documented meaning. Tests: reserve, settle, reserve again with the same id on both backends; a retry across a midnight boundary.

### [Issue 4] [`egm-design`] - Severity: Major (finding id A10, adversarial)
*   **Affected Scope:** Interface (first paragraph "a store never lets a driver exception type escape"); R4; R6; Files (`_insert`) of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The ticket contradicts itself. The new Protocol rule says no driver exception escapes. R6 expects the new methods to raise a driver error classed NOT connectivity (a missing table), and R4/`is_connectivity_error` recognises `psycopg` classes by name along the MRO of exceptions that escape the store. After a dropped connection, store methods raise raw `OperationalError` today. A builder who implements the rule literally removes the signal `tick` relies on. Separately, "`_insert` translates at that one place" is not true: `record_decision`, `add_spend`, `put_redaction_map`, `set_kill_switch` and the new methods do not go through `_insert`, so `CheckViolation` / `UniqueViolation` still escape from them (class-level miss).
*   **Rationale:** evidence: protocol.py:29-38; postgres.py:204-218, 337-373, 416-431, 453-464.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (protocol.py:29-38; postgres.py:204-218, 337-373, 416-431, 453-464.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface (first paragraph "a store never lets a driver exception type escape"); R4; R6; Files (`_insert`)
    *   Change: Rewrite the rule: "a refused WRITE is `StaleState` or `ValueError`; a store that cannot be reached or answers with a schema/privilege error raises a driver error that `is_connectivity_error` classifies". Put the translation in one wrapper used by every write method, not only `_insert`. Add a sibling grep to the evidence.

### [Issue 5] [`egm-design`] - Severity: Major (finding id A11, adversarial)
*   **Affected Scope:** Security (lock-in decision D1, guard changes a-d); Files (six test files) of `handover/tickets/P4d.md`
*   **Discrepancy Description:** `pg_driver()` returns the psycopg module to any test, so a test calls `pg_driver().connect(...)` without any `import psycopg`; the "only kinds/ may import psycopg" rule becomes cosmetic. Other routes the new scan does not mention: `pytest.importorskip("psycopg")` (test_p2_postgres.py:26 and others, a string call, not caught by the `_dynamic_target` logic); `monkeypatch.setattr(postgres.psycopg, "connect", ...)` in test_p3b_neutral_audit:310 reaches the driver via a src attribute; the proposed `tests/demo_askdata/` exemption covers any NEW file placed there. "Bodies unchanged" is also wrong: 18 further references use `from psycopg import sql`, `psycopg.errors.X`, `psycopg.sql` (test_k2_migrations 9, warden_port/test_audit_chain 4, test_k5_round10_postgres 3, and others), which cannot be replaced by a one-line `pg_driver()` swap.
*   **Rationale:** evidence: Ticket lines 36 and 43; tests/test_lockin_guard.py:69, 129-152; grep counts above.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 36 and 43; tests/test_lockin_guard.py:69, 129-152; grep counts above.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Security (lock-in decision D1, guard changes a-d); Files (six test files)
    *   Change: Make the helper hand out only what tests need (`connect_admin(dsn)`, `sql`, `errors` namespaces), not the module. The guard must also flag `importorskip("psycopg")`, `import_module`/`__import__` with the name, and any `pg_driver()` call outside the allowed set of test files (an allow-list of files, not directories, with a stale-entry check as the existing `PENDING` mechanism has). Scope the `demo_askdata` exemption to the 8 named files with a dated, expiring entry. Record the demo `pgsource.py` and `postgres.psycopg` attribute as dated exceptions too. Correct the "bodies unchanged" claim.

### [Issue 6] [`egm-design`] - Severity: Major (finding id A12, adversarial)
*   **Affected Scope:** Scope ("Files to create, change, delete") of `handover/tickets/P4d.md`
*   **Discrepancy Description:** One pull request holds: Store Protocol, two backends, a migration and grant change, 2 money methods, 8 contract gaps, behaviour changes to existing methods (plan_id, tick step, error translation), a guard rewrite, edits to 6 other test files, a CI workflow change and hostile-input rules. Tier A review has no round cap, so every unrelated change is re-reviewed each round. The guard work and the money work touch different hot files.
*   **Rationale:** evidence: Ticket lines 31-37, 62-86.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decided by A13(1): P4d is split P4d-a / P4d-b / P4d-c. The finding is valid: the reviewer cites evidence that can be read (Ticket lines 31-37, 62-86.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Scope ("Files to create, change, delete")
    *   Change: Split into three pull requests, in order. (1) P4d-a: contract harness (`store_pair`, `require_backend`, registry test, recording-proxy introspection, gaps 1-4, 6, 7, 9 for existing methods), plus the fixes they need in the existing methods (plan_id reuse, tick step, error translation, NUL/ids), no new money SQL. (2) P4d-b, Tier A money: migration 0006, GRANTS row, `reserve_spend` / `settle_spend`, the P-rows written first, and A1-A9. (3) P4d-c: guard (D1), `pg_driver`, the six test files, the demo exemption. (3) can run in parallel with (1) but must precede P5c per the hot-file order.

### [Issue 7] [`egm-design`] - Severity: Major (finding id A13, adversarial)
*   **Affected Scope:** Hostile inputs (ids over 2.7 KB, empty ids, NUL, surrogates); Interface of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The list names cases but gives no rule or expected result for them. Details. (a) An empty `reservation_id` would make every unkeyed call share one reservation (the replay returns the first, nothing more is booked): a lost reservation. (b) Long ids: a btree PK entry above about 2.7 KB fails with `ProgramLimitExceeded` (a raw driver error, not `ValueError`). Because Postgres compresses index values, a repetitive id such as `"a"*3000` can succeed while random bytes fail, so a hostile test using repetitive text passes vacuously on Postgres and fails to match memory. (c) NUL and lone surrogates must be refused in every text value, including nested JSON values and dict keys (`put_redaction_map` mapping keys, `inputs`); Postgres jsonb refuses `\u0000` (expected from docs). Memory accepts everything. The ticket's recommended rule is "both refuse with `ValueError`" but only for open point 6. (d) NaN or Infinity floats inside JSON.
*   **Rationale:** evidence: Ticket lines 59 and 98; postgres.py:178-189 (`_row`); 0001_core.sql (all PKs are unbounded TEXT).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 59 and 98; postgres.py:178-189 (`_row`); 0001_core.sql (all PKs are unbounded TEXT).). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Hostile inputs (ids over 2.7 KB, empty ids, NUL, surrogates); Interface
    *   Change: Choose a grammar for all ids (for example `^[A-Za-z0-9._:-]{1,200}$`, checked with `fullmatch`) and enforce it in one shared function used by both backends before any write. Deep-scan values and keys for NUL and surrogates in `_row` and the memory copy path. Use incompressible random data in the long-id test. State the expected exception for each case in a table.

### [Issue 8] [`egm-design`] - Severity: Major (finding id A14, adversarial)
*   **Affected Scope:** `require_backend`; R9; Evidence of `handover/tickets/P4d.md`
*   **Discrepancy Description:** "Silent skip must fail in CI" is only partly closed. `CI` is checked by being "set": `CI=false` or `CI=0` counts as set. Other skip routes stay: module-level `pytest.importorskip("psycopg")` in the old files, R4's memory "not applicable" skip, the `-m "not live and not perf"` marker, and tests deselected by name. Nothing proves that the Postgres parametrisation ran: the registry test only checks that the kind names are registered, and registration is unconditional (the skip happens inside the fixture, `store_postgres.py:22-24`). The workflow change is "lead only".
*   **Rationale:** evidence: store_postgres.py:22-26; ci.yml:84-88 (CI env only adds the DSN, not a require flag).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (store_postgres.py:22-26; ci.yml:84-88 (CI env only adds the DSN, not a require flag).). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: `require_backend`; R9; Evidence
    *   Change: Define the rule exactly: fail when `HADAVIN_REQUIRE_PG` is non-empty and not "0", or `CI` is "true" or "1". Add a session-finish check (in `tests/contracts/conftest.py`) that fails the run under that rule when any `tests/contracts` test was skipped or when fewer than N `[postgres]` tests ran. Keep the evidence line "0 postgres skipped" as raw output.

### [Issue 9] [`egm-design`] - Severity: Major (finding id A15, adversarial)
*   **Affected Scope:** Mutation plan; R2; R7; R9; settle clamp of `handover/tickets/P4d.md`
*   **Discrepancy Description:** Mutants and tests that survive or pass vacuously. (a) M4 ("cap check in Python") is killed only by a thread race, which is timing-dependent, so it can survive. Deterministic version: an admin connection locks the day counter row (`SELECT ... FOR UPDATE`), the test starts a reserve in a thread (it blocks), the admin commits a booking that fills the cap, then the thread must see `SpendCapExceeded`. (b) M9 (memory lock removed) is also probabilistic under the GIL. (c) R7 AST scan only proves a method name appears in a test file, not that it ran on both backends; a call in a dead branch or an unparametrised test satisfies it. Use a recording proxy in the `store` fixture and assert at session end that each Protocol method was called on each backend. (d) R9 "`list_approvals` oldest first": memory returns dict insertion order, Postgres `ORDER BY created_at` with no tie-break, so a test that inserts in created_at order is vacuous; insert in reverse order and add a tie-break column. (e) R1 lists "duplicate `create_run` is StaleState" as fail-before, but it already holds on ce70eb5 (memory.py:51-55, postgres.py:238-242). (f) R5's fail-before "migration without a GRANTS row makes migrate refuse" already exists as `check_grants`. (g) R4's fail-before is a mutant, not a failing test on old code. (h) Missing mutants: day taken from today instead of the reservation's day, settle applies `actual` not `actual - reserved`, settle moves only one counter, replay compares only the amount, reservation row left behind after a cap refusal (M5 covers counters only), `<=` vs `<`, zero-amount handling, clamp. (i) The clamp rule hides drift: it is reachable only through corruption or the pinned negative `add_spend`, and a silent clamp would hide a deleted counter row (P4b2's prune).
*   **Rationale:** evidence: Ticket lines 49-57, 62-78; memory.py:182-186; postgres.py:399-406.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 49-57, 62-78; memory.py:182-186; postgres.py:399-406.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Mutation plan; R2; R7; R9; settle clamp
    *   Change: Apply (a)-(i). Replace the silent clamp with a loud result (log at error, or refuse and leave the reservation open), or keep the clamp and add a test through an admin connection that damages the counter.

### [Issue 10] [`egm-design`] - Severity: Major (finding id A16, adversarial)
*   **Affected Scope:** R9 (`check_step_name`); Interface of `handover/tickets/P4d.md`
*   **Discrepancy Description:** Python `re` and Postgres POSIX regex disagree on `$`. The Postgres CHECK is `step ~ '^[a-z_]+$'` (0003:31); Python `re.match(r"^[a-z_]+$", "abc\n")` also matches a string with a trailing newline, Postgres does not. A shared `check_step_name` copied from the CHECK text accepts `"abc\n"` in memory and gets a `CheckViolation` from Postgres: the exact divergence R9 is meant to remove, and the listed hostile inputs do not include a trailing newline.
*   **Rationale:** evidence: 0003_approvals_tick.sql:31; ticket line 57.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (0003_approvals_tick.sql:31; ticket line 57.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: R9 (`check_step_name`); Interface
    *   Change: Use `re.fullmatch(r"[a-z_]+", step)`. Add `"abc\n"`, `"abc "`, `"ABC"`, `""`, Unicode letters and NUL to the step table, both backends.

### [Issue 11] [`egm-design`] - Severity: Major (finding id A17, adversarial)
*   **Affected Scope:** Interface `reserve_spend`; R2 of `handover/tickets/P4d.md`
*   **Discrepancy Description:** Lock order and deadlock/retry are unspecified. Reserve and settle both lock day then month rows, but the reservation row's place is open: if one path takes the reservation row first and the other the counters first, two same-id calls can deadlock. Postgres raises `DeadlockDetected` or a serialization failure as `OperationalError` subclasses, and `is_connectivity_error` (matches class name "OperationalError" by MRO) classes these as "store unreachable". Under 8 processes some reserves fail with a raw driver error and the "granted count equals cap divided by amount" assertion becomes flaky or wrongly red.
*   **Rationale:** evidence: protocol.py:33-38; ticket line 50.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (protocol.py:33-38; ticket line 50.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface `reserve_spend`; R2
    *   Change: Document one global lock order: reservation row, day row, month row. Decide the contention behaviour (retry a bounded number of times inside the store, or a typed `StoreBusy`); make `is_connectivity_error` not treat `TransactionRollbackError` as a connectivity failure. Add a multi-handle stress test with a barrier and assert no raw driver error.

### [Issue 12] [`egm-design`] - Severity: Major (finding id A18, adversarial)
*   **Affected Scope:** Files (migration 0006 and `migrate.py` row); R5; R6; Security (identities) of `handover/tickets/P4d.md`
*   **Discrepancy Description:** (a) The file name `0006_...` is hard-coded while A3 says "whoever merges first takes the next free number" and P3b/P3c also want one. If the branch is applied to a scratch database and then renamed 0007, `migrate` refuses with the "applied migrations have no file" error (migrate.py:320-326). The ticket does not say what the builder does on a number clash. (b) Applying 0006 does not grant anything: grants are applied only when `migrate(runtime_role=...)` is passed the role, so a database that is migrated without the role argument has the table but the runtime role gets `InsufficientPrivilege` on the new methods; R6 covers only "migration not applied". (c) Every test migrates as the superuser in the CI DSN (`postgres`, trust), so no test runs the migration as a plain non-superuser owner or checks that the runtime role cannot run it. (d) Closed-port test: binding then closing a port and connecting later is racy under parallel runs.
*   **Rationale:** evidence: ci.yml:42, 86; store_postgres.py:29-45; migrate.py:320-326, 340-345.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (ci.yml:42, 86; store_postgres.py:29-45; migrate.py:320-326, 340-345.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Files (migration 0006 and `migrate.py` row); R5; R6; Security (identities)
    *   Change: Rebase the number at merge time (the builder renumbers before any shared database applies it). Add R6 cases: table present but no grant, and 0006 absent, each asserting counters are unchanged after the failure. Add one test that migrates as a dedicated non-superuser owner role. For the closed-port test, use a host that refuses (127.0.0.1 with a port the test just proved free in the same step) or accept `OperationalError` from either state.

### [Issue 13] [`egm-design`] - Severity: Major (finding id A19, adversarial)
*   **Affected Scope:** R2; "Not in P4d" (8-process test is P4b1's) of `handover/tickets/P4d.md`
*   **Discrepancy Description:** P4d closes as "Tier A done" with only in-process, multi-connection tests. If P4b1's 8-process test finds an overshoot in P4d's SQL, a closed Tier A package reopens, with `store/postgres.py` a hot file. Separate connections in one process are fine for the SQL itself, but no process-level behaviour (forked connections, process kill mid-transaction) is covered. Memory cannot be cross-process at all.
*   **Rationale:** evidence: Ticket lines 28, 50; memo-3 section 5 gap 2.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 28, 50; memo-3 section 5 gap 2.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: R2; "Not in P4d" (8-process test is P4b1's)
    *   Change: Add a small `multiprocessing` test in P4d (4 processes, barrier, same agent and cap, reserve and settle), skipped only without Postgres under `require_backend`. Add a kill test: a process is killed after the counter update and before commit, and the counters and table are unchanged afterwards. State in the ticket that memory has no cross-process guarantee and is DEV_ONLY.

### [Issue 14] [`egm-design`] - Severity: Major (finding id A4, adversarial)
*   **Affected Scope:** Open point 1; Interface; Files (migration, postgres.py) of `handover/tickets/P4d.md`
*   **Discrepancy Description:** Authority conflict. Amendment F2 (which wins over any message) says P4b1 holds "the Postgres implementation inside store/postgres.py (after P4d)", and P4d "carries the store-protocol methods". The ticket follows "the message", which is not in the authority order, and builds memory and Postgres, migration 0006, GRANTS and the money SQL inside P4d. Open point 1 only flags it. If F2 stands, half of this ticket (all of the Tier A SQL) is built in the wrong package. F7 also wants "settle twice" rows written first, which cannot pass on Postgres without that SQL.
*   **Rationale:** evidence: Amendments F2 and F7; ticket line 93.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decided by A11: money SQL lives in P4d; P4b1 builds the meter on top and imports no database library. The finding is valid: the reviewer cites evidence that can be read (Amendments F2 and F7; ticket line 93.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Open point 1; Interface; Files (migration, postgres.py)
    *   Change: The lead rules before build and the ticket is rewritten once. The least risky reading: P4d is Protocol, memory, migration 0006, GRANTS and contract rows, with the Postgres money SQL in P4d as well so the rows can go green. If so, record "F2 amended: Postgres implementation moves to P4d" in amendments.md.

### [Issue 15] [`egm-design`] - Severity: Major (finding id A5, adversarial)
*   **Affected Scope:** Interface; "Not in P4d" of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The interface is not sufficient for P4b1/P4b2, so P4b1 will edit the signature of a method P4d just closed (hot file `store/postgres.py`). Missing: (a) no run-level cap or run counter in the same atomic step, though memo-3 says pr/48 books worst case on run, day and month, and the ticket stores `run_id` but books nothing against it; (b) no kill switch check inside the atomic step (memo-2 says A has it), so there is a window between `Limits.blocked` and the reserve; (c) `SpendCapExceeded` carries no detail on which cap (day or month), but `limits.blocked` reports `daily_budget` / `monthly_budget` and R215 wants a loud alert with a reason; (d) no `get_reservation` or open-reservation listing for the P4b2 sweep; (e) `created_at` comes from the Python wall clock, but P4b2 needs a monotonic or database-clock age. Adding the column or index later is additive, but changing the Protocol is not: `missing_methods` makes `app` refuse older custom stores each time (protocol.py:151-160).
*   **Rationale:** evidence: Ticket lines 24, 27, 28; memo-3 sections 2 and 5; memo-2 "What the losers have"; limits.py:24-30; protocol.py:151-160.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 24, 27, 28; memo-3 sections 2 and 5; memo-2 "What the losers have"; limits.py:24-30; protocol.py:151-160.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface; "Not in P4d"
    *   Change: Before building, agree the P4b1/P4b2 call shapes with those tickets. At minimum add keyword-only `run_cap` (with run counter semantics) and a kill-switch refusal to the single atomic step, add `SpendCapExceeded.which`, add `get_spend_reservation(id)`, take creation time from `clock_timestamp()` in SQL (and a monotonic stamp for memory), and add a partial index `(created_at) WHERE status='open'`. State in the ticket which of these P4b1/P4b2 will not need, with evidence.

### [Issue 16] [`egm-design`] - Severity: Major (finding id A6, adversarial)
*   **Affected Scope:** Interface `reserve_spend` errors; "Hostile inputs" (Decimal edges) of `handover/tickets/P4d.md`
*   **Discrepancy Description:** Input rules are incomplete and will diverge between backends. (a) No type rule: a float 0.1 is converted to NUMERIC by Postgres (expected) but raises `TypeError` in memory; `True` becomes 1; a str is dumped by psycopg. Memory `+=` on a mixed Decimal and float raises `TypeError`. (b) The order of checks is not stated: comparing a NaN with `< 0` raises `InvalidOperation` in Python, so `is_finite()` must come first. (c) A builder who validates "at most 6 decimals" with `quantize(Decimal("1E-6"))` gets `decimal.InvalidOperation` for `Decimal("1E+30")` (context precision 28) instead of `ValueError`. (d) There is no upper bound. Memory sums with default context precision 28, so `Decimal("1E+22") + Decimal("0.000001")` silently rounds in memory, while Postgres NUMERIC is exact. A huge `Decimal("1E+200000")` goes to Postgres and fails as a raw DataError. (e) Zero amount is neither allowed nor refused. (f) Trailing zeros (`Decimal("1.0000000")`) are 7 digits but numerically 6 decimals. (g) The cap arguments have no rules at all: `day_cap=Decimal("NaN")` raises in memory, and in Postgres `x <= 'NaN'` is true, so it means "no cap". Negative caps are unspecified. `day_cap=None, month_cap=None` means uncapped. (h) `day: date` accepts a `datetime` subclass: memory keys it differently from the Postgres DATE, so memory silently splits the counters.
*   **Rationale:** evidence: Ticket lines 24, 25, 59; memory.py:196-216 uses default-context arithmetic; postgres.py:416.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 24, 25, 59; memory.py:196-216 uses default-context arithmetic; postgres.py:416.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface `reserve_spend` errors; "Hostile inputs" (Decimal edges)
    *   Change: One validation function in `store/protocol.py`, shared by both backends. Order: `type(x) is Decimal` (reject bool, int, float, str), `is_finite()`, `x >= 0`, range `<= 10**12` (or similar), then `x == x.quantize(...)` inside a context with enough precision, or check `x.as_tuple().exponent >= -6` after `normalize()`, with trailing-zero behaviour written down. Apply the same function to caps (non-negative, finite or None) and refuse `day` unless `type(day) is date`. Contract table of 20+ edge cases run on both backends: 0, -0, NaN, sNaN, Inf, 1E-6, 1E-7, 1.0000000, 1E+13, True, 0.1, "1", datetime. Add mutants: "skip is_finite", "skip type check", "limit 7 instead of 6".

### [Issue 17] [`egm-design`] - Severity: Major (finding id A7, adversarial)
*   **Affected Scope:** Hostile inputs ("for add_spend/add_cost current behaviour pinned"); open point 6 of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The suite pins the permissive behaviour: a contract test asserts a negative `add_spend` is accepted. NaN is not mentioned at all. Negative spend lets any caller erase reservations: reserve fills the cap, `add_spend(-cap)` reopens it. `add_spend(NaN)` poisons the counter permanently in both stores: the runtime role has no DELETE, memory `Decimal + NaN` is NaN forever, `limits.blocked` then raises on memory while Postgres refuses everything. The ticket defers refusal to P4b1, but P4d is the store-contract package and a pinned test makes the later fix a changed test, which the CLAUDE.md quality gates forbid. The clamp test also needs a way to push a counter below the reserved amount, and the only listed way is a negative `add_spend`.
*   **Rationale:** evidence: Ticket lines 59 and 98; limits.py:17-18 (`charge` passes any Decimal); memory.py:196-204.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decided by A13(2): NaN, Infinity and negative amounts are refused in the OLD add_spend/add_cost now. The finding is valid: the reviewer cites evidence that can be read (Ticket lines 59 and 98; limits.py:17-18 (`charge` passes any Decimal); memory.py:196-204.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Hostile inputs ("for add_spend/add_cost current behaviour pinned"); open point 6
    *   Change: Refuse negative, NaN, infinite and over-range amounts in `add_spend` and `add_cost` now, with `ValueError`. Keep accepting 8 decimals (the existing test needs it). Do not pin the accept-negative behaviour. For the clamp test use a deliberate corruption via an admin connection, or drop the clamp (see A15).

### [Issue 18] [`egm-design`] - Severity: Major (finding id A8, adversarial)
*   **Affected Scope:** Files (migration 0006 and GRANTS row); Security notes of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The ticket gives no DDL. Runtime gets `SELECT, INSERT, UPDATE` on the whole table, so any code path or compromised runtime can rewrite `reserved_usd`, the `agent_id` and `day`, or flip `settled` back to `open` and settle again; settle-once then lives only in application code. The repo precedent for tables that must not be rewritten is a trigger (audit tables, see the `GRANTS` comment). No CHECKs are stated: `reserved_usd >= 0`, `status IN ('open','settled')`, `(status='settled') = (settled_usd IS NOT NULL)`, `settled_usd <= reserved_usd`. No NUMERIC scale is stated. The ticket says "ValueError (a value the store cannot hold)" via `CheckViolation`, so those CHECKs are what makes that translation work.
*   **Rationale:** evidence: migrate.py:46-68, 73-85 (`_SAFE_CREATE` allows `CREATE TRIGGER` and `CREATE OR REPLACE FUNCTION`, not a plain `CREATE FUNCTION`); 0001_core.sql:87-92 (no CHECK on spend.usd).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (migrate.py:46-68, 73-85 (`_SAFE_CREATE` allows `CREATE TRIGGER` and `CREATE OR REPLACE FUNCTION`, not a plain `CREATE FUNCTION`); 0001_core.sql:87-92 (no CHECK). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Files (migration 0006 and GRANTS row); Security notes
    *   Change: Put the DDL in the ticket. Add the CHECKs above. Add a `BEFORE UPDATE` trigger that allows only open to settled once and freezes the other columns (and refuses a settled row any update), plus a negative test via the runtime role: `UPDATE ... SET reserved_usd = 0` and `SET status='open'` on a settled row both fail. Keep `check_grants` and `effective_problems` green. Say that the reservation table has `purge=""` and no portal read, and why.

### [Issue 19] [`egm-design`] - Severity: Major (finding id A9, adversarial)
*   **Affected Scope:** Rollback of `handover/tickets/P4d.md`
*   **Discrepancy Description:** "Old code ignores the new table" is wrong for money. Counters in `spend` and `spend_month` include open reservations (the ticket says so for `spend_totals`). After a code rollback to `pre-P4d` there is no code that settles, so every open reservation holds budget forever and the table cannot be reconciled by the old runtime. If the table is dropped, the counters stay inflated with no record. Old code also cannot read the new schema_migrations row's file: `migrate` raises "applied migrations have no file in this release" (migrate.py:320-326). The ticket does not list this.
*   **Rationale:** evidence: Ticket lines 24, 26, 90; migrate.py:320.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 24, 26, 90; migrate.py:320.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Rollback
    *   Change: Write a rollback procedure: before rolling back, settle or release all open reservations (a one-off script under the migration identity), or document a counter rebuild. Mark the migration non-revertible and add the loud-failure test the template asks for. Also list under "behaviour changes": new Protocol methods make older custom stores fail `missing_methods` at app start.

### [Issue 20] [`egm-codebase-details`] - Severity: Major (finding id C1, correctness)
*   **Affected Scope:** Contract rows R6; Rollback; Files (0006) of `handover/tickets/P4d.md`
*   **Discrepancy Description:** R6 tests the wrong direction. memo-3 gap 6 and plan-v3 line 193 ("each migration includes the downgrade-read test of P3a") require old code against the new schema (N code, N+1 schema). R6 tests new code on an old schema (0006 not applied) and hands the old-code test to P3a. The Rollback line "Old code ignores the new table" is asserted, not tested. The R6 setup is also not buildable as described. `migrate()` runs `check_grants`, which refuses a GRANTS row whose table no migration creates. `_apply_grants` also runs GRANT on every GRANTS name. So a "one migration behind" database cannot be made with `migrate()` once the `spend_reservations` GRANTS row exists.
*   **Rationale:** evidence: memo-3:54 (gap 6). plan-v3:193. migrate.py:150-166 (`check_grants`), :174-181 (`_apply_grants`), :305-306. The old-code `migrate` raises the loud `gone` error at migrate.py:320-326.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (memo-3:54 (gap 6). plan-v3:193. migrate.py:150-166 (`check_grants`), :174-181 (`_apply_grants`), :305-306. The old-code `migrate` raises the loud `gone` error a). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Contract rows R6; Rollback; Files (0006)
    *   Change: Add a row for old code on a 0006 database: runtime works, old `migrate` fails loudly with the `gone` message. Keep R6 as the second row. Say the "behind" database is built by hand (SQL files 0001-0005 plus a manual ledger and manual grants, as `test_p2_postgres.py:276-290` does). The ledger is read by `SELECT version FROM schema_migrations` (migrate.py:319), so drop the UNVERIFIED mark.

### [Issue 21] [`egm-codebase-details`] - Severity: Major (finding id C2, correctness)
*   **Affected Scope:** Files to change of `handover/tickets/P4d.md`
*   **Discrepancy Description:** Adding 0006 breaks an existing test the ticket never names. `test_p2_postgres.py:290` asserts `migrate(fresh_dsn) == ["0004_audit_checkpoint_meta", "0005_evidence"]`. With 0006 it returns three versions. The ticket lists that file only for the `pg_driver` edit.
*   **Rationale:** evidence: tests/test_p2_postgres.py:276-290.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (tests/test_p2_postgres.py:276-290.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Files to change
    *   Change: List this assertion as a required change. Use a prefix check or derive the expected list from the files.

### [Issue 22] [`egm-codebase-details`] - Severity: Major (finding id C3, correctness)
*   **Affected Scope:** Interface (error rule); R6; Files (`_insert`) of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The ticket contradicts itself and the plan to implement it is thin. The Protocol rule says "a store never lets a driver exception type escape". R6 expects the new methods to "raise a driver error that `is_connectivity_error` classes as NOT connectivity". The classifier works only by driver class name (protocol.py:33-37). The only translation point planned is `_insert`. The other Postgres paths (`_select`, `transition`, `add_spend`, `spend_totals`, `_purge`, `record_decision`) still leak `psycopg` errors. `tick.py:342,362`, `chain.py:531` and `cli.py:368` rely on those leaking driver classes to tell "unreachable" from "answered".
*   **Rationale:** evidence: postgres.py:204-218, :260-268, :416-442. protocol.py:29-38.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (postgres.py:204-218, :260-268, :416-442. protocol.py:29-38.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface (error rule); R6; Files (`_insert`)
    *   Change: Pick one rule and state it. Option A: translate everywhere, with a typed `StoreError` or `StoreUnavailable` split, and change `is_connectivity_error` and its callers. Option B: narrow the rule to "constraint violations map to Protocol errors; connection and schema errors stay driver types, classified by `is_connectivity_error`". Then say that R6 depends on it.

### [Issue 23] [`egm-codebase-details`] - Severity: Major (finding id C4, correctness)
*   **Affected Scope:** R2; Mutation plan (M6) of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The money races that P4b1 depends on are untested. R2 races `add_spend`, `reserve_spend` against a cap, `transition`, `create_run`, `record_decision`, `save_gate_decision` and `add_tool_call`. It does not race two handles settling the same id at once, or reserving the same id at once. "Settle twice returns the first result" is tested only in sequence. Mutant M6 ("second call books again") is killed by the sequential row. A check-then-write settle (read status, then update without `WHERE status='open'`) survives. memo-3 gap 2 asks for "settle twice does not double count".
*   **Rationale:** evidence: Ticket lines 50, 58, 70. memo-3:50.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 50, 58, 70. memo-3:50.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: R2; Mutation plan (M6)
    *   Change: Add R2 rows: N handles settle the same id, so exactly one books and all get the same result. Also N handles reserve the same id and same content, so it books once. Add a mutant for a non-atomic settle. Add a first-insert cap case. An upsert `ON CONFLICT ... WHERE total+amt<=cap` does not run its WHERE on the insert path, so an amount over the cap on a fresh day row would be booked unless it is checked separately.

### [Issue 24] [`egm-codebase-details`] - Severity: Major (finding id C5, correctness)
*   **Affected Scope:** Interface (old methods "pinned"); Hostile inputs; Open point 6 of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The shared money counter can be poisoned through the unvalidated old path. `add_spend` and `add_cost` accept NaN, Infinity and negatives. Postgres NUMERIC stores NaN, and from PG14 Infinity. The ticket pins this "current behaviour" and leaves it to P4b1. `spend_totals` includes reservations and `reserve_spend` shares the same rows. One NaN `add_spend` then makes every cap check wrong. In SQL, NUMERIC NaN sorts above every number, so every cap check would fail. In memory, comparing a NaN Decimal raises `InvalidOperation`. This defeats R2 and R3. STUDIO-RULES 1 and class-level fixes say to fix and not defer.
*   **Rationale:** evidence: memory.py:196-204, postgres.py:276-277 and :416-431. The 0001 and 0003 NUMERIC columns have no CHECK. The ticket pins this at "Hostile inputs" (line 59) and open point 6.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (memory.py:196-204, postgres.py:276-277 and :416-431. The 0001 and 0003 NUMERIC columns have no CHECK. The ticket pins this at "Hostile inputs" (line 59) and ope). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface (old methods "pinned"); Hostile inputs; Open point 6
    *   Change: Make NaN and Infinity a `ValueError` in `add_spend` and `add_cost` on both stores now (it is a refusal of garbage, not a rule change). Pin negatives only if the lead decides. Do not write a test that locks in accepting NaN.

### [Issue 25] [`egm-codebase-details`] - Severity: Major (finding id C6, correctness)
*   **Affected Scope:** Security, Lock-in (b); Open point 2 of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The guard rule as written cannot go green. Rule (b) says "only `tests/contracts/kinds/` may import psycopg". Eight files under `tests/demo_askdata/` import it, so (b) fails on them. The ticket then proposes an exemption that contradicts A9 F7 ("tests are exempt ... only inside tests/contracts/kinds/"). Plan: that needs a lead amendment before the build, or `pg_driver` in those 8 files too. Today they use module-level `import psycopg` (conftest.py:20-23) and `psycopg.Connection` in annotations (gold_runner.py:28,38; test_gold_exec.py:22,27).
*   **Rationale:** evidence: amendments.md F7. grep: conftest, gold_runner, test_gold_exec, test_pgsource_layers, test_roles, test_seed, test_validate_harm, test_verify_readonly.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (amendments.md F7. grep: conftest, gold_runner, test_gold_exec, test_pgsource_layers, test_roles, test_seed, test_validate_harm, test_verify_readonly.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Security, Lock-in (b); Open point 2
    *   Change: Get the lead's decision first and record it as an amendment. Then make guard (b) match it exactly, with the exempt folder named in the guard's code and a plant test for it.

### [Issue 26] [`egm-codebase-details`] - Severity: Major (finding id C7, correctness)
*   **Affected Scope:** Files (the six-file `pg_driver` change) of `handover/tickets/P4d.md`
*   **Discrepancy Description:** "Replace their `import psycopg` lines ... bodies unchanged" does not keep the six files green. (a) There are 12 more `from psycopg ...` lines to change. Counted by file, k2_migrations has 6, k5_round10 has 2, audit_chain has 2, p7_store has 1 (module level, line 13), p2_postgres has 1 (line 175). Each is `from psycopg import sql` or `from psycopg.conninfo import ...`. (b) `test_p7_store.py:11-13` and `test_p2_postgres.py:26` run at module level. A `pytest.skip` or `pytest.fail` there needs `allow_module_level=True`, and a fail at module level is a collection error. (c) Five more `importorskip("psycopg")` calls sit outside the six: `test_p7_tick.py:378`, `test_migrate_regex_linear.py:7`, `test_k5_fixes2.py:285`, `test_p2_postgres.py:26`, `test_p7_store.py:11`. They still skip silently under `HADAVIN_REQUIRE_PG`. The ticket's "0 skipped" claim covers only the contract rows. Evidence command 2 even lists `test_migrate_regex_linear` and `test_p7_tick` is not in it.
*   **Rationale:** evidence: Greps above.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Greps above.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Files (the six-file `pg_driver` change)
    *   Change: Specify `pg_driver()` to return the module, with `sql` and `conninfo` reached as attributes (`drv.sql`, `drv.conninfo`). Define `allow_module_level` behaviour. Say whether the guard sees `importorskip`. Convert the remaining `importorskip` calls, or state the skip is accepted.

### [Issue 27] [`egm-design`] - Severity: Nit (finding id A20, adversarial)
*   **Affected Scope:** Security (tenants, R8) of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The deferral to P7b is acceptable for isolation (no tenant concept on main, A3 verified), but the new money table is keyed by a global `reservation_id` with no tenant column. P7b would then change the primary key of a money table (memo-3 expects tenant first in every new table's PK). Id squatting across agents is also possible inside one process: agent B using agent A's id gets `ReservationConflict` and can block A.
*   **Rationale:** evidence: Memo-3 section 2 (tenant row); ticket lines 44, 56.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decision: name the P7b change to the new table's primary key in the ticket; do not add a tenant column now. The finding is valid: the reviewer cites evidence that can be read (Memo-3 section 2 (tenant row); ticket lines 44, 56.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Security (tenants, R8)
    *   Change: Name the P7b migration in the ticket (a new table or a PK change with data copy) or add a nullable `tenant` column now with an index. Say which. Document that ids are caller-generated and unguessable (random), and test that a cross-agent clash is `ReservationConflict` with no change.

### [Issue 28] [`egm-design`] - Severity: Nit (finding id A21, adversarial)
*   **Affected Scope:** Interface; wording of `handover/tickets/P4d.md`
*   **Discrepancy Description:** (a) Settle with a different amount on an already-settled id silently returns the first result, but reserve with different content raises `ReservationConflict`: inconsistent, and a caller never learns its amount was ignored. Return the stored row (fine) but document it and add a test that the second call's amount is ignored. (b) `limits.blocked` refuses at `day >= daily` (limits.py:26) while `reserve_spend` allows reaching exactly the cap ("stay within"): one counter, two boundaries. State `<=` and test the boundary one micro under, at and one micro over. (c) "Same content", "settle zero is a release" and "release" are not defined (status `settled` with `settled_usd` 0): P4b2's billing contract needs to tell a release from a settle at zero; say whether it can. (d) "Not in P4d: run-level cap" sits beside a `run_id` argument that does nothing. (e) The count "32+2" is correct (I counted 32 in protocol.py), fine. (f) The `CI` and `HADAVIN_REQUIRE_PG` wording should say exact values.
*   **Rationale:** evidence: limits.py:26; protocol.py:49-148.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (limits.py:26; protocol.py:49-148.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface; wording
    *   Change: Edit the ticket text; add the boundary test.

### [Issue 29] [`egm-codebase-details`] - Severity: Nit (finding id C10, correctness)
*   **Affected Scope:** Verified facts, Security of `handover/tickets/P4d.md`
*   **Discrepancy Description:** Three wrong citations. (1) `backends/table.py:597 DEV_ONLY` should be :593 (the set) and :599 (`("store","memory")`); A8 says 593. (2) "refused UPDATE on gate_decisions (existing, `test_p2_postgres.py:173`)": that test checks DELETE and TRUNCATE on `runs` via `has_table_privilege`. The `gate_decisions` UPDATE check is `test_p7_store.py:136-152`, and it also uses `has_table_privilege` (catalog), not a refused statement. (3) "runtime ... append-only tables INSERT only": `audit_outbox` gives the runtime role `SELECT, INSERT, DELETE` (migrate.py:59). R5's "runtime cannot DELETE append-only tables" must exclude it.
*   **Rationale:** evidence: table.py:593-602. test_p2_postgres.py:173-192. test_p7_store.py:136-154.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (table.py:593-602. test_p2_postgres.py:173-192. test_p7_store.py:136-154.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Verified facts, Security
    *   Change: Correct the three. Make R5 run real DELETE/UPDATE statements as the runtime role.

### [Issue 30] [`egm-codebase-details`] - Severity: Nit (finding id C11, correctness)
*   **Affected Scope:** Contract rows R1, R4, R5; Tests summary of `handover/tickets/P4d.md`
*   **Discrepancy Description:** "FAIL-BEFORE rows named in R1, R4, R5, R9" is misleading. Duplicate `create_run` is already `StaleState` on both stores (memory.py:53, postgres.py:241-242). R4: `build()` already maps `OperationalError` to `StoreUnavailable` (postgres.py:170-174) and `is_connectivity_error` already says true for it. R5: the grants already exist (`check_grants`). The registry test passes on ce70eb5 too, because `@kind("store","postgres")` registers unconditionally (store_postgres.py:76; the skip is inside the generator). These rows pass on the old code; only a mutant kills them.
*   **Rationale:** evidence: Sources as cited.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Sources as cited.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Contract rows R1, R4, R5; Tests summary
    *   Change: Mark these rows "regression pin, killed by mutant Mx" and not fail-before. Keep fail-before for save_plan duplicate, tick step, CI-without-DSN, and the new methods.

### [Issue 31] [`egm-codebase-details`] - Severity: Nit (finding id C12, correctness)
*   **Affected Scope:** Rollback / behaviour changes of `handover/tickets/P4d.md`
*   **Discrepancy Description:** One side effect is undeclared. New Protocol methods make `missing_methods()` list them for any custom store, and `app.py:147` then refuses to start. That is a behaviour change for a client with a custom store. It is not in the "non-revertible, loud-failure" list.
*   **Rationale:** evidence: app.py:147. protocol.py:151-160. test_k5_round6_contracts.py:14-31.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (app.py:147. protocol.py:151-160. test_k5_round6_contracts.py:14-31.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Rollback / behaviour changes
    *   Change: Add it to the list, with a test for the old-store message.

### [Issue 32] [`egm-codebase-details`] - Severity: Nit (finding id C13, correctness)
*   **Affected Scope:** Hostile inputs; R9 step grammar of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The Postgres CHECK `step ~ '^[a-z_]+$'` is end-anchored. A Python `re.match(r"^[a-z_]+$")` also accepts "abc\n" (trailing newline), so `check_step_name` could pass a value Postgres refuses. Use `fullmatch` or `\Z`. Also `Decimal("NaN") < 0` raises `InvalidOperation`, not `ValueError`, so validation must test `is_finite()` first. Add "abc\n" to the hostile list.
*   **Rationale:** evidence: 0003_approvals_tick.sql:31.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (0003_approvals_tick.sql:31.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Hostile inputs; R9 step grammar
    *   Change: As stated.

### [Issue 33] [`egm-codebase-details`] - Severity: Nit (finding id C14, correctness)
*   **Affected Scope:** Interface (A9 B1 rounding / exponent) of `handover/tickets/P4d.md`
*   **Discrepancy Description:** A9 B1 says "Decimal with a fixed exponent of -6 at the Store boundary". The ticket says "at most 6 decimal places" and does not quantize outputs. NUMERIC with no scale returns the scale as stored, so `reserved_usd` or totals can come back as `Decimal('1.5')`, `1.500000` or an 8-decimal value from `add_spend`. Equality tests pass either way. The ticket should say whether returned amounts are quantized. The "NO money migration" wording (line 24) sits beside a new migration that holds money columns. A3 anticipated 0006 ("0006 for P4b if needed") and A9 B1 means no change to existing money columns, so this is consistent. The wording should say that, and cite A3. Reserve and settle edge cases are unspecified: replaying `reserve_spend` for an id already settled; a second `settle_spend` with an invalid amount (first result or `ValueError`?); `reserve_spend` with an unknown `run_id`.
*   **Rationale:** evidence: amendments.md A3 and A9 B1.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (amendments.md A3 and A9 B1.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface (A9 B1 rounding / exponent)
    *   Change: Add one line each.

### [Issue 34] [`egm-codebase-details`] - Severity: Nit (finding id C15, correctness)
*   **Affected Scope:** Hot files; template order of `handover/tickets/P4d.md`
*   **Discrepancy Description:** Plan rule 10 orders `memory.py`, `migrate.py` and `CHANGELOG.md` as P3a, P4d, P4a, P4b; the ticket gives no order for them. `tests/contracts/test_store.py`, `tests/test_k2_migrations.py` and `tests/test_p2_postgres.py` are named in plan-v3 P3b's conflict surface (line 130), and P4d edits all three. P3b depends on P1, P2a and P3a, not P4d, so overlap is possible. The ticket's F6 entries (lock-in guard; postgres.py) are correct. Template order: "Mutation plan" comes before "Tests". The extra sections "Verified facts" and "Contract rows" sit between template fields. All template fields are present.
*   **Rationale:** evidence: plan-v3:68, :130.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (plan-v3:68, :130.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Hot files; template order
    *   Change: Add the orders and the three test files to the hot list. Move the Mutation plan after the Tests field.

### [Issue 35] [`egm-codebase-details`] - Severity: Nit (finding id C16, correctness)
*   **Affected Scope:** R2/R7 of `handover/tickets/P4d.md`
*   **Discrepancy Description:** R7's AST scan counts any call whose attribute name matches a method (`touch`, `get_run`, ...), on any object, so it can pass without a store call. Require the receiver to be the `store` fixture or `store_pair` handle. R2's "50 repeats ... small `sys.setswitchinterval`" gives no pass rule for Postgres where one connection per handle makes interleaving real.
*   **Rationale:** evidence: Ticket lines 50, 55.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 50, 55.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: R2/R7
    *   Change: State the receiver rule and the pass criterion.

### [Issue 36] [`egm-codebase-details`] - Severity: Nit (finding id C8, correctness)
*   **Affected Scope:** Header ("Path class") of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The ticket labels the path "other" while saying "spend counters, which are money". Template and plan classes are money/redaction/security/other; the work is money plus store, Tier A. A label of "other" invites the 2-round cap in review-loop-speed-rules.
*   **Rationale:** evidence: Template line 4. plan-v3:61.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decided by A11: P4d carries money SQL, so its path class is money (no round cap). The finding is valid: the reviewer cites evidence that can be read (Template line 4. plan-v3:61.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Header ("Path class")
    *   Change: Set "money" (store included).

### [Issue 37] [`egm-codebase-details`] - Severity: Nit (finding id C9, correctness)
*   **Affected Scope:** Files (0006), Security of `handover/tickets/P4d.md`
*   **Discrepancy Description:** The 0006 DDL is not given. For a Tier A money table the ticket should state the columns, the PK on `reservation_id`, CHECKs (`reserved_usd >= 0`, status in open/settled, `settled_usd` set only when settled, and `settled_usd <= reserved_usd`) and an index. Runtime gets UPDATE (GRANTS row), so any runtime session can rewrite a settled row unless the settle SQL is guarded with `WHERE status='open'` or a trigger refuses it. The security text does not mention that.
*   **Rationale:** evidence: migrate.py:40-41, :46-68.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (migrate.py:40-41, :46-68.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Files (0006), Security
    *   Change: Add the DDL and the settle guard to the ticket, with a negative test.
