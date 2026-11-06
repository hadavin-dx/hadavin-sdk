# AK-G15: item states, the re-run transaction and the grants (short brainstorm, PL13 (a))

* **Author:** AK-G15 PL13 brainstorm session (AUTO mode; `git config user.name` is empty in this worktree)
* **Date:** 2026-11-06

## Read this first (what was and was not done)

- **Scope.** This short brainstorm covers three things only, as lead order 43 item 13 (`LEAD-ORDERS.md:277`) asks: (1) the states of a queue item and the moves between them, (2) the one transaction that closes an item with outcome `rerun` and starts the message again, (3) the database rights of each role. Everything else in AK-G15 is out of scope here.
- **Input.** `tickets/AK-G15.md`, FROZEN at revision 3, with its build notes AK-G15 BN-1 to BN-27 (the build notes win where they disagree with the text above them); `reviews/AK-G15-round3-resolve.md`; AK-G2 build notes BN-4, BN-24, BN-25 (`tickets/AK-G2.md:529-532`, `:720-734`); lead orders 43 and 45. No other review file was read.
- **AUTO mode.** The skill's interactive steps (clarifying questions, the readiness gate, the hand-off gate) were skipped, as the brief from the lead ordered. Where an architecture choice existed, this brief takes the option the frozen ticket already took and says so.
- **No Goldfish review ran.** The skill asks for six reviewers in fresh contexts. This session has no tool to start a sub-agent, so the "Analysis" below is the author's own stress test in one context. It is NOT a Goldfish review and must not be counted as one. The `egm:egm-review` step that follows the draft is the first independent review.
- **Not reopened.** The lead's answers PL13-PL19 (order 43) and PL20-PL22 (order 45) stand. NEEDS LEAD 23, 24 and 25 are still open: their MEANWHILE texts (AK-G15 BN-6 part, BN-2 part, BN-4) are recommendations, not decisions, and are labelled that way below.
- **Code.** Every claim about existing code was re-read in `<repo>/src/hadavin_sdk` (last commit touching `src/`: `ce70eb5`). Nothing was run: no Python, no PostgreSQL. Every PostgreSQL behaviour below is UNVERIFIED.

## Overview

When the core decides that a person must look at something, it parks a run in `NEEDS_PERSON`, a state with no way out (`runtime/runs.py:10-22`: `ALLOWED` has no entry for it, and `FINAL` is every state not in `ALLOWED`). Nobody owns the case, nothing records who looked, and two people can act on the same message. AK-G15 adds a table of "a person must look" items. A person claims an item for a limited time, then closes it with one recorded outcome. For a received message (an inbound item), one outcome, `rerun`, starts the message again, which costs money (a second paid run). That one outcome goes through one database function owned by a role that nobody can log in as, so neither the agent's own database role nor a stray SQL statement can start a second paid run.

## Analysis (author's own stress test; not a Goldfish review)

Weakest points first.

1. **The deployment's role name cannot sit in a fixed migration file.** `migrate()` sends each migration file to the database exactly as written (`store/migrate.py:330`); nothing in today's code replaces a placeholder. AK-G2 BN-24 needs the re-run owner role's name written into AK-G2's trigger as a literal, and AK-G15 BN-6 (MEANWHILE) needs an `ALTER FUNCTION ... OWNER TO <that role>`. Both names are chosen per deployment (no hard-coding rule). So these statements must be built by `migrate()` in Python after the file is applied (with safely quoted names, as `_apply_grants` already does, `store/migrate.py:169-187`), or by P2a-1's placeholder mechanism if it is extended to role names (P2a-1 is not merged; UNVERIFIED). Either way they run inside `migrate`'s single transaction (`store/migrate.py:308-314`).
2. **A direct worker UPDATE can close an item `rerun` without re-running anything.** The worker role holds UPDATE on `outcome` (ticket grants table, `tickets/AK-G15.md:264`), the CHECK allows `rerun` for inbound items (`:219`), and the update trigger has no rule that ties `rerun` to the function (`:223`). Such an item is then final: its receipt stays `needs_person` at the same generation, collection skips it because a round-0 item already exists (AK-G15 BN-5, "the anti-join excludes a receipt whose round-0 item exists in any state"), and reopen is refused because the outcome is `rerun` (`:232` check (4)). The message is silently lost. A bug in the Python close path (outcome `rerun` passed with `rerun=False`) reaches the same state. The fix is small and the design proposes it: the update trigger refuses `outcome = 'rerun'` unless `current_user` is the re-run owner role, and the store method refuses `outcome="rerun"` unless `rerun=True`. This is NOT in the frozen ticket; it is listed as a contradiction for the build-start review.
3. **"No capped re-run is wasted" is overstated.** The ticket says the in-function body check means "no capped re-run is wasted" (`:202`, step 5). The function only checks that the body row exists; it does not lock it, and it should not (a lock would delay a purge, against "never delays a purge", `:144`; a row lock also needs UPDATE rights on that table, UNVERIFIED). So a purge that lands after step 5 and before the next run reads the body still spends one re-run of the cap. The body is gone, so AK-G2's dispatch should end that run without a model call (AK-G2 ticket text, UNVERIFIED here). Erasure still wins; only the wording is wrong.
4. **The temporary ownership-transfer rights (NEEDS LEAD 23, MEANWHILE).** Recommendation (a) grants the migrating role membership of the owner role and the owner role CREATE on the schema, changes the owner, then revokes both. Because `migrate` runs every step in one transaction (`store/migrate.py:312`), the temporary rights are never visible outside it if the transaction commits with the revokes in it. That makes (a) safer than it reads. Still open for the lead, and the PostgreSQL rules behind it are UNVERIFIED.
5. **A later deploy with a different owner-role name.** Once the function exists with owner X, a `migrate` call naming owner Y would leave the trigger literal and the function owner out of step, or silently re-grant. The design adds a check: if the function exists, its owner must equal the `rerun_owner_role` argument, else `ConfigError`. Not in the ticket; additive.
6. **The database cannot check queue roles.** The function trusts that the caller named the item's assignee; it does not know who has the `rerun` queue role (that check is Python, `:232` check (3)). Someone holding the worker password can re-run any item that some person has claimed, up to 10 re-runs per message (ticket entry 15, R2-ADV-11). This is the ticket's stated limit 16, not new; restated so the draft does not overclaim.
7. **The lease does not expire by itself.** An expired claim stays `claimed`; it only becomes claimable (`:198`). Nothing moves it back to `open`. This is simpler (no tick write) and correct, but the screen must show "claimed, lease expired" as claimable. Kept as the ticket chose.

What holds up: one final state that a trigger freezes; every write a compare-and-set on `version`; the one door for a re-run is a function whose owner cannot log in; AK-G2's trigger stays the last guard on the receipt; the worker has no right at all on `inbound_receipts` or `runs` (INFORM I13).

## Goals vs. Non-Goals

* **In-scope goals:**
  - Write each item state and each allowed move in plain words, with who (which database role) makes it.
  - Write the re-run transaction step by step, with the role that runs each step and the error each step raises.
  - Write the rights of each role on each relation and the function, deny-all first.
  - List every place where the design differs from the frozen ticket or a build note.
* **Out-of-scope non-goals:** the screen (G14), notices (V5), the client-tool mirror (V1), item purge (V4), the readers cap (NEEDS LEAD 24, only mentioned), the per-kind ceiling (NEEDS LEAD 25, only mentioned), `compare_ids`, collection batching (AK-G15 BN-3), config and wiring (-c), test and mutant counts.

## Alternatives Weighed

- **Re-run as plain store code on the worker connection with UPDATE on `inbound_receipts`.** Rejected by the lead (PL15 (a), order 43, `LEAD-ORDERS.md:279`): the worker would then hold the right to re-run by direct SQL.
- **Function owned by the migration role.** Rejected in the ticket (R2-ADV-1, `tickets/AK-G15.md:27`) and by AK-G2 BN-24 (`tickets/AK-G2.md:723`): the migration role is a LOGIN role, so a direct session could re-run.
- **Guard on `session_user` (P2a's style).** Rejected by AK-G2 BN-24 (`tickets/AK-G2.md:723`): inside a SECURITY DEFINER function `session_user` stays the caller, so only `current_user` identifies the function (UNVERIFIED PostgreSQL behaviour).
- **Owner-role name kept in a one-row settings table that the trigger reads.** Rejected by the author: BN-24 chose a literal; a table adds a relation, grants and a way to change the name at run time.
- **A tick step that moves expired claims back to `open`.** Rejected by the author: it adds a write by the runtime role on `queue_items`, which the runtime role must not have (it holds no UPDATE, `:262`).
- **Lock the body row in the function.** Rejected by the author: it would delay a purge (`:144`) and needs UPDATE rights on `inbound_bodies` (UNVERIFIED).
- **Ownership transfer options (b) superuser runs the migration, (c) the migration role stays a member for ever.** Not decided here: NEEDS LEAD 23 is open; MEANWHILE recommendation (a) is carried as a recommendation.

## Key Decisions & Staging for Next Steps

Taken from the frozen ticket (not reopened):
1. Three states, `open`, `claimed`, `closed`; `closed` is final (`:92`, `:148`).
2. The re-run runs only inside `hadavin_queue_close_rerun`, SECURITY DEFINER, `search_path = pg_catalog, pg_temp`, owned by a NOLOGIN re-run owner role, EXECUTE for `queue_worker` only (PL15 (a); AK-G2 BN-24; `:201`).
3. Neither new role is created by a migration; `migrate` takes `worker_role` and `rerun_owner_role` (AK-G15 BN-6 decided part).
4. Refusals by SQLSTATE `QS001`-`QS004` (AK-G15 BN-16); `run_id` never NULL (AK-G15 BN-19).
5. Re-run cap `queue.max_reruns` default 3, range 0-10 inside the function (PL16 (a)).

New in this brainstorm, for the draft and then the build-start review (none changes the ticket):
- N-1: the role-name statements are built by `migrate()` (or P2a-1's substitution), not by a fixed SQL file (analysis 1).
- N-2: the `rerun` outcome guard in the update trigger and in the store method (analysis 2).
- N-3: correct the "no capped re-run is wasted" wording (analysis 3).
- N-4: `migrate` refuses an owner-role name that differs from the existing function's owner (analysis 5).

Next step: `egm:egm-draft` on this brief, output `design.md` in this folder.
