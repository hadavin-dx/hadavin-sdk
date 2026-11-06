# AK-G15: item states, the re-run transaction and the grants per role

*   **Author:** AK-G15 PL13 draft session (AUTO mode; `git config user.name` is empty in this worktree)
*   **Status:** Draft (input to the build-start review; not reviewed)
*   **Date:** 2026-11-06

--------------------------------------------------------------------------------

## Read this first

- **What this is.** The short `egm:egm-draft` that lead order 43 item 13 (PL13 (a), `LEAD-ORDERS.md:277`) asks for, written from `concepts_brief.md` in this folder. It covers three things only: the item states and moves, the re-run transaction, and the database rights of each role. It is not an extra ticket round and changes nothing in `tickets/AK-G15.md`.
- **Sources.** `tickets/AK-G15.md` FROZEN at revision 3 with build notes AK-G15 BN-1 to BN-27 (`:608-902`; the build notes win over the text above them); `reviews/AK-G15-round3-resolve.md`; AK-G2 build notes BN-4 (`tickets/AK-G2.md:529-532`), BN-24 (`:720-732`), BN-25 (`:734`); lead orders 43 (`LEAD-ORDERS.md:274-290`) and 45 (`:303-310`). No other review file was read.
- **Code cites.** Paths like `store/migrate.py:330` are relative to `<repo>/src/hadavin_sdk/`, re-read for this draft at the last commit touching `src/`, `ce70eb5`. Ticket cites like `tickets/AK-G15.md:223` are relative to `<repo>/handover/`.
- **Not run.** No Python, no tests, no PostgreSQL. **Every statement about how PostgreSQL behaves is UNVERIFIED** (general knowledge only) and is marked so where it matters; the full list is in "UNVERIFIED".
- **AUTO mode.** The skill's approval gates were skipped. Where an architecture choice existed, this draft takes the option the frozen ticket took and says so. No Goldfish reviewer ran in the brainstorm (no sub-agent tool in that session), so nothing in this document has had an independent review yet.
- **Still open (not decided here).** NEEDS LEAD 23 (how the function gets its owner), 24 (a cap on `readers`), 25 (one waiting-item ceiling or one per kind). Their MEANWHILE texts (AK-G15 BN-6 part, BN-2 part, BN-4) appear below only as labelled recommendations.
- **Contradictions with the frozen ticket or its build notes** are listed in one place, section "Where this design contradicts or adds to the frozen ticket" (D1-D6). The ticket is not edited.

## Overview

A queue item is one row in table `queue_items` that says "a person must look at this". It holds ids, a closed reason code, staff ids, its state, times and a counter, and never message text (`tickets/AK-G15.md:88`). Three database roles touch it: the agent's runtime role opens items; a new login role, the queue worker, acts for persons (claim, release, close, reopen); a new role that cannot log in, the re-run owner role, owns the one database function that may start a received message again. This document says, in plain words, which moves each role can make, what the re-run function does step by step, and exactly which rights each role holds.

## The Problem

Today a run that needs a person sits in `NEEDS_PERSON`, which has no way out (`runtime/runs.py:10-22`: `ALLOWED` has no entry for it; `FINAL` is every state not in `ALLOWED`). The only way to find such runs is `Store.list_runs`, oldest first and at most 100 (`store/protocol.py:64-66`, revision 1 reading in the ticket, not re-read here). There is no record of who looked, and two people can act at once.

The money risk is the re-run. For a received message, "start it again" means a second paid run. As AK-G2's frozen text stood, the agent's own role held UPDATE on `inbound_receipts` (`tickets/AK-G2.md:221`) and AK-G2's trigger allowed `needs_person -> received` for any role (`:175`), so the agent could start that paid run by itself. AK-G2 BN-24 (`tickets/AK-G2.md:720-732`) closes that hole by allowing the move only when `current_user` is the re-run owner role. AK-G15 builds the only door that remains, the function `hadavin_queue_close_rerun`, and the queue around it.

## Goals

*   Every item move is listed with the role that makes it, the check that allows it, and the database guard that refuses everything else.
*   A re-run happens only through `hadavin_queue_close_rerun`, in one transaction that either closes the item AND moves the receipt, or changes nothing.
*   At most `queue.max_reruns + 1` runs per message through the normal path (default 3, so 4 runs), and at most 11 for someone who holds the worker password (ticket entry 15, R2-ADV-11, `tickets/AK-G15.md:36`).
*   Each role holds exactly the rights in the grants table below and nothing else, checked against the catalogue by the tests (AK-G15 BN-22).

## Non-Goals

*   The screen where a person reads content and acts (G14), notices (V5), the client-tool mirror (V1), item purge (V4), `compare_ids`, collection batching (AK-G15 BN-3), config and the tick step (-c), test and mutant totals (AK-G15 BN-27). These are in the ticket and not re-described here.
*   Deciding NEEDS LEAD 23, 24 or 25.

## Open Questions

*   **NEEDS LEAD 23 (open):** how the re-run function gets its owner. MEANWHILE recommendation (a), AK-G15 BN-6 (`tickets/AK-G15.md:701-715`): grant temporary rights, change the owner, revoke them, all in one transaction. See "Step 0" below.
*   **NEEDS LEAD 24 (open):** `cardinality(readers) <= 50` (AK-G15 BN-2, `:640-648`). Not part of the state machine; noted only.
*   **NEEDS LEAD 25 (open):** the waiting-item ceiling per (tenant, kind) (AK-G15 BN-4, `:663-672`). It changes the count inside `open_queue_item`, not any state or move.
*   **Where AK-G2 BN-24 is built** (option (i) AK-G2-a or (ii) AK-G15-b) is still the lead's choice (`tickets/AK-G15.md:574`). This design works for both.
*   **D1 to D6 below** need a yes or no at the build-start review.

## Critical User Journeys (CUJs)

### CUJ 1: A person deals with a hand-off and closes it

*   **Given**: the runtime role opened a chat item (`open`, version 0) for run `run-<hex>`; `person-1` is a current queue reader of `tenant-a` with queue role `work`.
*   **When**: `person-1` claims it with the version and binding it saw (version 0 -> 1, `claimed`), then closes it `answered` before the lease ends.
*   **Then**: the item is `closed`, outcome `answered`, `closed_by = person-1`, version 2; one intent and one outcome audit event per action; the row never changes again.

### CUJ 2: A person re-runs a waiting message

*   **Given**: an inbound item for a receipt at generation 0 in `needs_person`, the body still stored, no open run for the receipt's run id; `person-1` has queue roles `work` and `rerun` and holds a live claim.
*   **When**: `person-1` closes it with outcome `rerun`.
*   **Then**: in one transaction the item is `closed`/`rerun` and the receipt is `received` at generation 1 with run id `run_id_for(key, 1)`; AK-G2's dispatch then starts the second run. If any check fails, nothing changes and the person sees one refusal code.

### CUJ 3: The agent's own role tries to re-run a message

*   **Given**: a session of the runtime role.
*   **When**: it runs `UPDATE inbound_receipts SET state = 'received', ...` on a `needs_person` row, or calls `hadavin_queue_close_rerun`.
*   **Then**: the UPDATE is refused by AK-G2's BN-24 guard (`current_user` is not the owner role), and the call is refused for lack of EXECUTE (SQLSTATE `42501`); rows N13 and N12 of the ticket (UNVERIFIED until run).

## Technical Plan (Architecture)

### Part A. Item states and allowed moves

Three states (`tickets/AK-G15.md:187`, `:92`):
- **`open`**: waiting; nobody holds it. `assignee` and `lease_until` are empty (CHECK, `:219`).
- **`claimed`**: one person holds it until `lease_until`. `assignee` and `lease_until` are set (CHECK, `:219`). When the lease time passes, the row does NOT change by itself: it stays `claimed` and simply becomes claimable by anyone (`:198`). No job moves it back to `open` (the runtime role holds no UPDATE on `queue_items`, `:262`).
- **`closed`**: final. Exactly one outcome (`answered`, `no_action`, or `rerun` for inbound only), `closed_by` and `closed_at` are set (CHECK, `:219`). A trigger refuses any later update (`:223`) and any delete (`:224`).

Every move raises `version` by exactly 1 and is a compare-and-set on the version the person saw (`:95`; update trigger requires `NEW.version = OLD.version + 1`, `:223`). A person action also passes the item's `binding` (a SHA-256 of its ids, `:192`), so an action cannot land on another item.

| # | Move | Who (database role) | Allowed when (store method, ticket cite) | Refused otherwise with |
|---|---|---|---|---|
| M1 | (none) -> `open`, round 0, chat | runtime | `open_queue_item`: fresh row, `state = 'open'`, `version = 0`, no person fields, times inside the 600 s clock window, tenant below its ceiling, key not held (`:195`, insert trigger `:222`) | ceiling: returns `None` -> `QueueRefused("queue_full")`; key held by another binding or round -> `key_conflict`; key held by a `closed` item -> `key_closed` (AK-G15 BN-5) |
| M2 | (none) -> `open`, round 0, inbound | runtime (collection) | as M1, plus -b's insert trigger finds a `needs_person` receipt with the same tenant, source, key, generation, reason and `run_id` (`:222`; AK-G15 BN-7) | trigger raises; the tick step fails loudly |
| M3 | (none) -> `open`, round + 1 (reopen) | worker | `reopen_queue_item`: the predecessor is `closed`, its outcome is not `rerun`, round + 1 <= 20, same subject, one successor only (`:206`, `:218`, insert trigger `:222`) | `not_closed`, `bad_outcome`, `round_limit`, `subject_erased` (`:232` check (4)) |
| M4 | `open` -> `claimed` | worker | `claim_queue_item`: version and binding equal; sets `assignee`, `lease_until = now + lease_s`, `first_claimed_at` once (`:198`); `lease_until <= updated_at + 86400 s` (AK-G15 BN-9) | `StaleState` -> `stale` |
| M5 | `claimed` -> `claimed` | worker | same person renews; or anyone once `lease_until < now` (`:198`) | `stale` (another person's live lease, wrong version or binding) |
| M6 | `claimed` -> `open` (release) | worker | the holder, lease still live; clears `assignee` and `lease_until` (`:199`) | `stale` |
| M7 | `claimed` -> `closed` (`answered`, `no_action`) | worker | `close_queue_item`: the holder, lease live, version and binding equal; `closed_by = assignee` (store `:200`, trigger `:223`) | `stale`; `bad_outcome` for a chat item asked `rerun` |
| M8 | `claimed` -> `closed` (`rerun`) | re-run owner, ONLY inside `hadavin_queue_close_rerun`, which only the worker may call | Part B | `stale`, `outcome_unknown_not_acknowledged`, `rerun_limit`, `subject_erased` |
| - | `closed` -> anything; any DELETE; any change of the identity columns | nobody | - | update trigger, delete trigger, no DELETE grant (`:223-224`, `:274`) |

**What the database itself enforces, separate from Python.** The CHECKs (`:219-220`, with AK-G15 BN-8 and BN-19) fix the shape of each state. The update trigger (`:223`) allows only the four state changes `open -> claimed`, `claimed -> claimed`, `claimed -> open`, `claimed -> closed`, freezes the identity columns and a closed row, and requires `closed_by = OLD.assignee` on close. Who may act and the lease check against the injected clock stay in Python (`:232`; owner-visible limit 16): the trigger only bounds times to within 600 s of the database clock.

**A gap this design closes (D2).** As frozen, the worker can write `outcome = 'rerun'` with a plain UPDATE, because it holds UPDATE on `outcome` (`:264`), the CHECK allows `rerun` for inbound (`:219`), and the update trigger has no rule about it (`:223`). Such an item is final, its receipt stays `needs_person` at the same generation, collection skips it because a round-0 item exists (AK-G15 BN-5), and reopen refuses it (`:232` check (4)): the message is silently lost. This design adds: the update trigger refuses `NEW.outcome = 'rerun'` unless `current_user` is the re-run owner role (-a's trigger refuses `rerun` always; -b's migration replaces the trigger function, as it already does for the insert trigger, `:222`), and `close_queue_item` refuses `outcome="rerun"` with `rerun=False` (`ValueError`).

### Part B. The re-run transaction, step by step

**The pieces.**
- `hadavin_queue_close_rerun(p_tenant, p_item_id, p_assignee, p_expect_version, p_binding, p_now, p_ack_unknown, p_max_reruns)`: a `plpgsql` function, `SECURITY DEFINER SET search_path = pg_catalog, pg_temp`, every relation inside written with the schema name (`tickets/AK-G15.md:201`; AK-G15 BN-25: the schema is `migrate`'s `current_schema()`, `store/migrate.py:172`).
- **Re-run owner role**: NOLOGIN, owns only this function, no login role is a member of it (AK-G2 BN-24, `tickets/AK-G2.md:723`). Inside the function, `current_user` is this role and `session_user` stays the worker (UNVERIFIED PostgreSQL behaviour).
- **Queue worker** (`queue_worker` is the ticket's label; the real name is the `worker_role` argument, AK-G15 BN-6): a login role with EXECUTE on the function and no right on `inbound_receipts` or `runs` (INFORM I13, `:266`).

**Step 0 (migration time, once; how the function gets its owner).** Today `migrate()` sends each migration file to the database exactly as written (`store/migrate.py:330`), inside one transaction (`:308-314`), and replaces no placeholder. The owner role's name is chosen per deployment, so the statements that name it cannot be in a fixed file (D1). This design puts them in `migrate()` itself, built with quoted identifiers as `_apply_grants` already does (`store/migrate.py:169-187`), right after -b's file is applied and in the same transaction:
1. check the `rerun_owner_role` argument: plain name (`_ROLE`, `store/migrate.py:70`, `:298-300`), different from the other roles (`:301-303`), NOLOGIN (new check, the P2a `reset_role` pattern, `tickets/P2a.md:244-245`), and not a member of or containing any other named role (today's pairwise check covers runtime, portal and purge only, `store/migrate.py:333-339`; it is extended to worker and owner);
2. write the owner role's name into AK-G2's guarded trigger function as a quoted literal (whichever PR builds AK-G2 BN-24);
3. **MEANWHILE (NEEDS LEAD 23, recommendation (a), not decided):** grant the owner role CREATE on the schema, grant the migrating role membership of the owner role with SET (and INHERIT FALSE where the server supports it), `ALTER FUNCTION ... OWNER TO` the owner role, revoke the membership, revoke CREATE (AK-G15 BN-6, `tickets/AK-G15.md:703-708`). Because all of this is inside `migrate`'s single transaction (`store/migrate.py:312`), the temporary rights are never visible to another session, if PostgreSQL keeps uncommitted GRANTs private to the transaction as it does other catalogue changes (UNVERIFIED). Until the lead answers, -b leaves this step out and cannot reach Done (`:615-616`);
4. `REVOKE ALL ON FUNCTION ... FROM PUBLIC`, `GRANT EXECUTE ... TO` the worker role only (`:201`). PostgreSQL gives EXECUTE to PUBLIC by default on a new function (UNVERIFIED), which is why the revoke is needed;
5. on a later `migrate` run where the function already exists: its owner (read from the catalogue) must equal the `rerun_owner_role` argument, else `ConfigError` (D5). A later migration that replaces the function body repeats item 3 around its `CREATE OR REPLACE`, because only the owner or a member of it may replace a function (UNVERIFIED).

**Steps 1-9 (each call; the worker calls, the function runs as the owner role).** Before the call, Python (`StoreQueue.close`, `tickets/AK-G15.md:232-234`) checks the person has queue roles `work` and `rerun`, may see the tenant now, the item is inbound, and the body is still there (`queue_subject_present`); then `audit.write_intent(...)` with decision `rerun` or `rerun_ack_unknown`. `AuditUnavailable` stops here with nothing changed (`audit/protocol.py:19-21`). Then the worker connection runs the function in one transaction:

| Step | What happens (plain words) | Role whose rights are used | On failure |
|---|---|---|---|
| 1 | `p_max_reruns` must be 0 to 10 (the 10 is a SQL literal pinned to `defaults.QUEUE_MAX_RERUNS_CEILING` by row N14) | none (no table read) | `QS003` `rerun_limit` |
| 2 | Lock the item row (`SELECT ... FOR UPDATE`) and check: `claimed`, `assignee = p_assignee`, `lease_until >= p_now`, `version = p_expect_version`, `binding = p_binding`, kind `inbound` | owner: SELECT and column UPDATE on `queue_items` (a row lock needs UPDATE on at least one column, UNVERIFIED) | `QS001` `stale` |
| 3 | Lock the receipt with the item's tenant, source and key (`FOR UPDATE`); check `state = 'needs_person'` and `generation = item.generation` | owner: SELECT and column UPDATE on `inbound_receipts` | `QS001` `stale` |
| 4 | No run with the receipt's `run_id` is in an open state (a SQL literal of `OPEN_STATES`, `models.py:75-84`, pinned by N14); if that run is `NEEDS_PERSON` with reason `outcome_unknown` (the reason the tick gives a stuck `EXECUTING` run, `runtime/tick.py:112-119`), `p_ack_unknown` must be true. Always runs: `run_id` is never NULL (AK-G15 BN-19) | owner: SELECT (`run_id`, `state`, `reason_code`) on `runs` | `QS001` `stale`; `QS002` `outcome_unknown_not_acknowledged` |
| 5 | The `inbound_bodies` row for the key still exists (key columns only, never `body`). Not locked (see D4) | owner: SELECT key columns of `inbound_bodies` | `QS004` `subject_erased` |
| 6 | `generation < p_max_reruns`, else refuse (PL16 (a)) | none | `QS003` `rerun_limit` |
| 7 | UPDATE the item: `closed`, `outcome = 'rerun'`, `closed_by = assignee`, `closed_at = updated_at = p_now`, `version + 1`, where the key and `version = p_expect_version`; exactly one row, else refuse. The `queue_items` update trigger runs (and, with D2, sees `current_user` = owner) | owner: column UPDATE on `queue_items` | `QS001` `stale` |
| 8 | UPDATE the receipt with `reopen_inbound`'s update written out (never the store method): `state = 'received'`, `generation + 1`, `run_id = 'run-' || substr(delivery_key, 1, 28) || lpad(to_hex(generation + 1), 4, '0')`, `attempts = 0`, `reason = NULL`, `last_reason = NULL`, where the key, `state = 'needs_person'` and the locked generation; exactly one row, else refuse. AK-G2's trigger runs as the final guard: `current_user` must be the owner role, generation + 1, the same formula (`tickets/AK-G2.md:175`, `:158`, `:167`; AK-G2 BN-24 `:724`) | owner: column UPDATE on `inbound_receipts` | `QS001` `stale`, or the trigger's own error |
| 9 | Commit. Any raise in steps 1-8 rolls back everything: no item change, no receipt change | - | - |

After the call, the Postgres store maps by exact SQLSTATE only: `QS001` -> `StaleState`, `QS002`-`QS004` -> `RerunRefused(code)`; any other error is passed on unchanged (AK-G15 BN-16, `tickets/AK-G15.md:784-791`). `StoreQueue` turns these into `QueueRefused(code)` and writes `audit.write_outcome(...)`, which never raises (`audit/protocol.py:23-25`). A crash after the commit and before `write_outcome` leaves an intent with no outcome; the row change itself is complete. The memory store runs the same checks in the same order under its lock, with no roles (`tickets/AK-G15.md:204`).

**What happens next (outside this transaction).** AK-G2's dispatch sees a `received` receipt at generation + 1 and starts run `run_id_for(key, generation + 1)`. If that run also needs a person, the receipt goes back to `needs_person` and collection makes a NEW round-0 item for the new generation (the key includes the generation, `:191`). That is how the cap counts: generation 0, 1, 2 can be re-run with the default 3, so at most 4 runs.

### Part C. Grants per role

Deny-all start: "A relation not in `GRANTS` gets nothing" (`store/migrate.py:25-27`); `_apply_grants` revokes everything on each relation in `GRANTS` before granting (`:169-187`). Rights below are the frozen ticket's grants table (`tickets/AK-G15.md:258-276`) with the build-note changes (AK-G15 BN-6 item 5). Column lists replace the table-level right of that role on that relation (`:582`).

| Role (how it is created) | Relation or object | Rights (exact) | Why |
|---|---|---|---|
| runtime (exists; `migrate(runtime_role=...)`, `store/migrate.py:286`) | `queue_items` | INSERT; SELECT (`tenant`, `item_id`, `idempotency_key`, `state`, `opened_at`, `binding`, `kind`, `round`, `reason`, `source`, `delivery_key`, `generation`) | open with dedupe and ceiling count; decoy checks; collection anti-join; counts. No staff-id columns. No UPDATE, so it can make no move after M1/M2 |
| runtime | `inbound_receipts` | unchanged by AK-G15 (AK-G2 `:221`); AK-G2 BN-24 removes its path to `needs_person -> received` | collection reads receipts it already reads |
| runtime | `hadavin_queue_close_rerun` | nothing | rows N12, N12b |
| worker (new LOGIN role, made by the database administrator; `migrate(worker_role=...)`, AK-G15 BN-6) | `queue_items` | SELECT (all columns); INSERT (reopen); UPDATE (`state`, `assignee`, `lease_until`, `version`, `outcome`, `closed_by`, `first_claimed_at`, `closed_at`, `updated_at`) | moves M3-M7; triggers and CHECKs limit the moves; with D2 it can no longer write `outcome = 'rerun'` |
| worker | `hadavin_queue_close_rerun` | EXECUTE | the only way to re-run |
| worker | `inbound_receipts`, `runs` | nothing (INFORM I13) | the function reads and writes them as its owner |
| worker | `conversations` | SELECT (`tenant`, `conversation_id`) | chat `queue_subject_present` |
| worker | `inbound_bodies` | SELECT (`tenant`, `source`, `delivery_key`), never `body` | inbound `queue_subject_present` |
| worker | schema | USAGE only, never CREATE (`store/migrate.py:173`; `effective_problems` reports CREATE, `:211-212`) | needed to name objects; no CREATE so it cannot plant a same-named function |
| re-run owner (new NOLOGIN role, made by the database administrator; `migrate(rerun_owner_role=...)`, AK-G15 BN-6) | `hadavin_queue_close_rerun` | owner (so it may run it) | owns exactly this one function |
| re-run owner | `queue_items` | SELECT (all columns); UPDATE (`state`, `outcome`, `closed_by`, `closed_at`, `version`, `updated_at`) | steps 2 and 7 |
| re-run owner | `inbound_receipts` | SELECT (`tenant`, `source`, `delivery_key`, `state`, `generation`, `run_id`); UPDATE (`state`, `generation`, `run_id`, `attempts`, `reason`, `last_reason`, `updated_at`) | steps 3 and 8 |
| re-run owner | `runs` | SELECT (`run_id`, `state`, `reason_code`) | step 4, and AK-G2's BN-7 open-run check in its trigger, which runs with the owner's rights (UNVERIFIED) |
| re-run owner | `inbound_bodies` | SELECT (`tenant`, `source`, `delivery_key`) | step 5 |
| re-run owner | schema | USAGE; CREATE only for the instant of Step 0 item 3 under NEEDS LEAD 23 (a), then revoked | ownership change rule (UNVERIFIED) |
| purge, portal (exist) | `queue_items`, the function | nothing | not their job |
| migration role (the administrator's login; owns the tables) | owner-role membership | none after `migrate` returns (under NEEDS LEAD 23 (a)) | otherwise it could `SET ROLE` and re-run (`tickets/AK-G15.md:257`) |
| PUBLIC | the function | nothing (`REVOKE ALL ... FROM PUBLIC`) | default EXECUTE removed (UNVERIFIED default) |
| any role | `queue_items` | no DELETE, no TRUNCATE | items are the record |

**What the existing checks cover, and what they do not.** `check_grants` reads relations (table, view, sequence) from the migration files (`store/migrate.py:150-166`) and `effective_problems` scans relation kinds `r, p, v, m, S` only (`:213-215`). Neither sees a function or its EXECUTE grant. So the function's grants are checked by test rows N12b/N12c (catalogue queries), not by these helpers; extending `effective_problems` to functions is left to P2a-1 as merged (UNVERIFIED, `tickets/AK-G15.md:582`).

### Where this design contradicts or adds to the frozen ticket

None of these edits the ticket. Each needs a yes or no at the build-start review.

- **D1 (contradicts the wording of AK-G15 BN-6 and AK-G2 BN-24).** BN-6's MEANWHILE says "-b's migration, in one transaction" does the ownership change (`tickets/AK-G15.md:703`), and AK-G2 BN-24 says "The migration writes that role name into the trigger function as a literal" (`tickets/AK-G2.md:723`). A migration file is sent as written (`store/migrate.py:330`) and no placeholder mechanism exists at `ce70eb5`; P2a's `<S>` covers the schema name only (`tickets/AK-G15.md:864-870`, AK-G15 BN-25), and P2a-1 is not merged. This design does both inside `migrate()` in Python, in the same transaction. Alternative if P2a-1 merges a general placeholder mechanism: use it for the role name too.
- **D2 (adds a guard the ticket does not have).** The update trigger (`tickets/AK-G15.md:223`) gains "refuse `outcome = 'rerun'` unless `current_user` is the re-run owner role", and the store's `close_queue_item` refuses `outcome="rerun"` without `rerun=True` (`:200` says only that `rerun=True` is refused in -a). Reason: a direct worker UPDATE or a Python bug can otherwise close an item `rerun` without a re-run and lose the message silently (Part A). Cost: one test case per store and one or two new mutants, so AK-G15 BN-27's total of 143 mutants would change.
- **D3 (adds).** The worker's UPDATE grant on `outcome` stays (it needs it for `answered`/`no_action`); D2's trigger rule, not a narrower grant, closes the gap, because PostgreSQL column grants cannot restrict values (UNVERIFIED general knowledge). Listed so the reviewer does not read the unchanged grant as an oversight.
- **D4 (contradicts ticket wording).** Step (5) of the ticket says the in-function body check means "no capped re-run is wasted" (`tickets/AK-G15.md:202`). The body row is not locked (a lock would delay a purge, against `:144`, and needs UPDATE on `inbound_bodies`, UNVERIFIED), so a purge after step 5 still spends one re-run of the cap. AK-G2's dispatch should then end that run without a model call because the body is gone (AK-G2 ticket text, not re-read here; UNVERIFIED). The true wording: "a body purged before the function's check refuses the re-run; a body purged after it costs one re-run of the cap and no model call".
- **D5 (adds).** `migrate` refuses a `rerun_owner_role` that differs from the existing function's owner (Step 0 item 5). Not in AK-G15 BN-6.
- **D6 (adds).** `migrate`'s membership check is extended from runtime/portal/purge (`store/migrate.py:333-339`) to the worker and owner roles, in both directions (no named role is a member of another). AK-G15 BN-6 item 2 says "the pairwise not-member checks, as P2a's `reset_role`", which this follows; listed because today's code covers three roles only.

Followed without contradiction (build notes over the text): no NULL `run_id` branch (BN-19 over `:202` step 4); SQLSTATE mapping (BN-16 over `:204`); unqualified call from the store (BN-25 over `:201`); no role created by a migration (BN-6 over `:159`, `:249`).

## Alternatives Considered

### Alternative A: Re-run as plain store code on the worker connection

*   **Pros**: no database function, no extra role, simpler migration.
*   **Cons**: the worker would need UPDATE on `inbound_receipts`, so anyone with the worker password could re-run by direct SQL, with no check of the lease, version or cap.
*   **Reason for Rejection**: rejected by the lead, PL15 (a) (`LEAD-ORDERS.md:279`).

### Alternative B: Function owned by the migration role

*   **Pros**: no new role; the migrating role owns everything it creates.
*   **Cons**: the migration role is a LOGIN role, so a direct session of it passes a guard on "the owner" and can re-run.
*   **Reason for Rejection**: rejected in the ticket (R2-ADV-1, `tickets/AK-G15.md:27`) and by AK-G2 BN-24 (`tickets/AK-G2.md:723`).

### Alternative C: Guard on `session_user`

*   **Pros**: matches P2a's guard style (`tickets/P2a.md:215`).
*   **Cons**: inside a SECURITY DEFINER function `session_user` stays the worker, so the guard cannot tell the function from a direct session (UNVERIFIED).
*   **Reason for Rejection**: rejected by AK-G2 BN-24 (`tickets/AK-G2.md:723`).

### Alternative D: Owner-role name in a one-row settings table read by the trigger

*   **Pros**: no generated SQL; the role name is data.
*   **Cons**: a new relation, new grants, and a way to change the guard at run time.
*   **Reason for Rejection**: Rejected by author: AK-G2 BN-24 chose a literal; D1 builds the literal in `migrate()`.

### Alternative E: A tick step that moves expired claims back to `open`

*   **Pros**: the state shows the truth without reading `lease_until`.
*   **Cons**: the runtime role would need UPDATE on `queue_items`.
*   **Reason for Rejection**: Rejected by author: least privilege; an expired claim is already claimable (`tickets/AK-G15.md:198`).

### Alternative F: Lock the body row in step 5

*   **Pros**: no purge can land between the check and the commit.
*   **Cons**: delays a purge (against `tickets/AK-G15.md:144`); needs UPDATE rights on `inbound_bodies` (UNVERIFIED); the purge would still win after the commit.
*   **Reason for Rejection**: Rejected by author: erasure first; D4 corrects the wording instead.

### Alternative G: NEEDS LEAD 23 options (b) superuser migration, (c) permanent membership

*   **Reason**: not decided here. Recommendation (a) is carried as MEANWHILE only (AK-G15 BN-6, `tickets/AK-G15.md:714`).

--------------------------------------------------------------------------------

## Non-Functional Requirements

- **Security.** The money door is the owner role's function; the agent's role cannot reach it (no EXECUTE) and cannot make the receipt move itself (AK-G2 BN-24). The remaining holes, stated plainly: someone with the worker password can re-run any item some person has claimed, up to 10 re-runs per message, naming any `p_assignee` that matches the item's current holder, because queue roles are checked in Python only (`tickets/AK-G15.md:232`; owner-visible limit 16); a session of the migration role that is a member of the owner role can re-run (`:257`), which NEEDS LEAD 23 (a) removes by revoking the membership.
- **Redaction.** No new column. The function reads key columns of `inbound_bodies`, never `body`.
- **Rollback.** Dropping the function removes the only re-run path; receipts stay `needs_person` (nothing lost). The ticket's Rollback field is not repeated here.

## UNVERIFIED

- All PostgreSQL behaviour: `current_user` inside a SECURITY DEFINER function owned by a NOLOGIN role, including when AK-G2's trigger fires on the function's UPDATE; `session_user` staying the caller; the rights needed for `ALTER FUNCTION ... OWNER TO` (SET on the new owner, CREATE on the schema) and for `CREATE OR REPLACE` of a function owned by another role; whether GRANT and REVOKE inside an uncommitted transaction are invisible to other sessions; `GRANT ... WITH INHERIT FALSE, SET TRUE` syntax and server versions; that `SELECT ... FOR UPDATE` needs UPDATE on at least one column; default EXECUTE for PUBLIC on new functions; that functions are not looked up in `pg_temp` for an unqualified call; that a trigger function runs with the rights of `current_user`; custom SQLSTATE class `QS`; `clock_timestamp()` inside triggers; column-grant behaviour for `INSERT ... ON CONFLICT` and for UPDATE expressions that read columns.
- Everything taken from AK-G1, AK-G2, AK1 and P2a: ticket text, not code (none is built).
- `store/protocol.py:64-66` (`list_runs`): taken from the ticket's revision 1 reading, not re-read here.
- How P2a-1 creates roles, substitutes `<S>`, and handles function grants.
- AK-G2's dispatch behaviour on a missing body (D4).

--------------------------------------------------------------------------------

## Detailed Implementation Plan

Only the files the three topics touch; the ticket's full file list (`tickets/AK-G15.md:247-251`, with AK-G15 BN-6 item 3) stays the authority. No code here.

### Target Files to Create/Modify

#### 1. `src/hadavin_sdk/store/migrations/<next>_queue.sql` (Create, -a)

*   **Type / Scope**: SQL migration.
*   **Proposed Changes**: table `queue_items` with the CHECKs of `:219-220` as changed by AK-G15 BN-8 (per-round key CHECK) and BN-19 (`run_id` NOT NULL); insert, update and delete triggers of `:222-224` with BN-9's `lease_until` bound; the update trigger refuses `outcome = 'rerun'` in every case (D2; -b relaxes it). No role names in the file.

#### 2. `src/hadavin_sdk/store/migrations/<next>_queue_inbound.sql` (Create, -b)

*   **Type / Scope**: SQL migration.
*   **Proposed Changes**: the function of Part B (steps 1-8, SQLSTATEs `QS001`-`QS004`, every relation schema-qualified); the replaced insert-trigger function (receipt cross-check with `run_id`, BN-7); the replaced update-trigger function allowing `outcome = 'rerun'` only for the owner role (D2: the role-name literal comes from `migrate()`, D1); indexes of `:221`. No role names in the file.

#### 3. `src/hadavin_sdk/store/migrate.py` (Modify, -a and -b)

*   **Type / Scope**: Python.
*   **Proposed Changes**: `migrate(..., worker_role=None, rerun_owner_role=...)` (BN-6 item 2) with name, distinct, NOLOGIN (owner) and pairwise membership checks for all named roles (D6); `Grant` gains `runtime_select_cols`, `worker`, `worker_select_cols`, `worker_update_cols` (-a), `rerun_owner_select_cols`, `rerun_owner_update_cols` (-b) (`:276`); a post-file step that writes the owner-role literal into the guard trigger functions (D1), runs Step 0 item 3 only once NEEDS LEAD 23 is answered, revokes PUBLIC, grants EXECUTE to the worker, and checks an existing function's owner (D5).

#### 4. `src/hadavin_sdk/cli.py` (Modify)

*   **Type / Scope**: Python CLI.
*   **Proposed Changes**: `--worker-role` (-a) and `--rerun-owner-role` passed through `_migrate` (`cli.py:138`, `:312-334`; AK-G15 BN-6 item 3).

#### 5. `src/hadavin_sdk/store/protocol.py`, `store/memory.py`, `store/postgres.py` (Modify)

*   **Type / Scope**: Python store.
*   **Proposed Changes**: methods 4-7 of `:198-206` (moves M3-M8); `RerunRefused` (-b); Postgres `close_queue_item(rerun=True)` calls the function unqualified and maps by SQLSTATE (BN-16, BN-25); `close_queue_item` refuses `outcome="rerun"` without `rerun=True` on both stores (D2); the memory store runs steps 1-8 under its lock.

#### 6. `src/hadavin_sdk/queue/items.py` (Create, -a; Modify, -b)

*   **Type / Scope**: Python.
*   **Proposed Changes**: `StoreQueue` person checks and audit order of `:232-234`; maps `StaleState` and `RerunRefused` to `QueueRefused`.

#### 7. `src/hadavin_sdk/defaults.py` (Modify)

*   **Type / Scope**: constants.
*   **Proposed Changes**: `QUEUE_LEASE_MAX_S` (BN-9), `QUEUE_RERUN_SQLSTATES` (BN-16), with the ticket's other queue constants (`:248-250`).

#### 8. `tests/test_queue_items.py`, `tests/test_queue_inbound.py` (Create)

*   **Type / Scope**: tests.
*   **Proposed Changes**: the ticket's rows for moves and grants (Q5-Q10, Q15, N3, N3b, N4, N4b, N12, N12b, N12c, N13, N15, with BN-20 to BN-24). Added by D2: as worker on Postgres, `UPDATE queue_items SET state = 'closed', outcome = 'rerun', ...` on a claimed inbound item is refused by the trigger and the row is unchanged; on both stores `close_queue_item(outcome="rerun", rerun=False)` raises `ValueError`. Added by D5: `migrate` with a different `rerun_owner_role` after the function exists raises `ConfigError`.

### Verification Plan

*   **Unit and contract tests**: `uv run --all-extras --group test pytest` (repo rule), both stores.
*   **PostgreSQL 16 and 17**: the N12/N12b/N12c/N13/N15 rows, with raw output saved as the ticket's `b-postgres.txt`; this is where every UNVERIFIED PostgreSQL item above gets its evidence.
*   **Lint and scan**: `ruff check`, `ruff format --check`, `bandit -ll`.
*   **Mutation**: the ticket's mutants plus D2's (one for each removed guard: the trigger rule, the store refusal).

--------------------------------------------------------------------------------

*Drafted with EGM*
