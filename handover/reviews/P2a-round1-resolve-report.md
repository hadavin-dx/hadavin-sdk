# Goldfish Annotated Review Report (resolve, round 1)

Status: findings categorised; fixes to be applied by the ticket author under the owner's standing instruction (see the note below)

**Target:** `handover/tickets/P2a.md` (full file). Findings: `handover/reviews/P2a-round1-adversarial.md`, `handover/reviews/P2a-round1-correctness.md`. Decisions applied: `handover/studio-notes/amendments.md` A11, A12, A13.

Counts: PROPOSE FIX 31, ESCALATE 3, CONTEST 0, DECLINE 0. Nothing was contested: for every finding the reviewer cited a file and line that could be read, and the author re-checks it before editing. The skill's severity names are Blocker / Major / Nit; the review files say BLOCKER / MAJOR / MINOR (MINOR = Nit, and every Nit is also fixed because the fix is cheap).

Note on the gate (skill Step 4): the owner told the cloud session to run resolve and rewrite the tickets, and set the standing rule that only major decisions wait for the owner. So the "auto accept" path is taken for every PROPOSE FIX; ESCALATE items are NOT applied as decisions: the ticket carries the recommended position marked PENDING LEAD and the item is listed in `handover/questions-for-lead.md`.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`egm-design`] - Severity: Blocker (finding id A1, adversarial)
*   **Affected Scope:** "Who may stop, who may reset"; Security notes of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The allow-list checks a caller-supplied string, not an authenticated identity. It is a typo guard, not access control.
*   **Rationale:** evidence: `limits.py:57-70` (`by` is a free string). `cli.py:383-409`, `--by X` is a free string. Core `store/migrate.py:55` has `Grant("table", _RW)` on `kill_switch`. The ticket concedes "enforced in code, not by the database".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decided by A13(3): real enforcement is a separate DB role for reset (runtime role read-only on kill_switch); this touches store/migrate.py GRANTS (hot file): state the order against P3a/P4d. The finding is valid: the reviewer cites evidence that can be read (`limits.py:57-70` (`by` is a free string). `cli.py:383-409`, `--by X` is a free string. Core `store/migrate.py:55` has `Grant("table", _RW)` on `kill_switch`. T). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: "Who may stop, who may reset"; Security notes
    *   Change: Do not claim "an agent never holds reset" until it is enforced below the code. Either split the DB roles (runtime gets SELECT only, a separate reset role gets UPDATE) as a gating item for P2a-1, or derive `by` from an authenticated credential (the connecting DB role or OIDC subject), never from an argument. Rewrite the negative tests to attempt the direct store write with the runtime credential. State the residual risk honestly in the ticket.

### [Issue 2] [`egm-design`] - Severity: Blocker (finding id A2, adversarial)
*   **Affected Scope:** "Who may stop" plus Rollback (1) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** Deny-all `stop_identities` makes the emergency stop unavailable by default. The ticket is also inconsistent: only `Limits.reset` is said to check, yet the negative tests mention "engage by an unknown name". Existing `Limits.stop` has no check.
*   **Rationale:** evidence: Ticket text. Core `limits.py:44-51` has no check.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decided by A13(3): stop stays open to any caller (audited); only reset is restricted. The finding is valid: the reviewer cites evidence that can be read (Ticket text. Core `limits.py:44-51` has no check.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: "Who may stop" plus Rollback (1)
    *   Change: Stop must stay open to any caller who can reach the store. Audit it and restrict only reset. Delete `stop_identities` or turn it into an audit tag. Define the breakglass reset (a dormant identity, alarmed, audited) and the bootstrap of `reset_identities` (the CLI refuses to start with an empty list and says how to fix it).

### [Issue 3] [`egm-design`] - Severity: Blocker (finding id A3, adversarial)
*   **Affected Scope:** Interface: `release`, audited reset, labelkey of `handover/tickets/P2a.md`
*   **Discrepancy Description:** Masking is applied in the gate, but the identity check is in `Limits.reset`. The gate calls `Limits.reset(self._lbl(by))`, so `reset_identities` is compared with a masked label.
*   **Rationale:** evidence: `stop_gate.py:336, 386-388` pass `self._lbl(by)`. `limits.py:38-46` sets `principal=by` raw.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decided by A13(3): check the raw name before masking, mask once. The finding is valid: the reviewer cites evidence that can be read (`stop_gate.py:336, 386-388` pass `self._lbl(by)`. `limits.py:38-46` sets `principal=by` raw.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface: `release`, audited reset, labelkey
    *   Change: Do the check on the raw authenticated identity inside `Limits.reset` first, then mask. Mask once, in `Limits._event` and in the stored `KillSwitch.by`, so every path (CLI, gate) gets the same label. Say which form the lists hold.

### [Issue 4] [`egm-codebase-details`] - Severity: Blocker (finding id C1, correctness)
*   **Affected Scope:** Interface "Who may stop, who may reset" (L26); Security (L40-44); Tests (L47) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The authorization rule is not buildable as written. (a) It says `Limits.reset` is the "shared choke point" and checks the name. But the gate never passes the name: it passes the masked label (`self._lbl(by)`). So the allow-list compares a label. For any name outside the plain class the label is `id:`+hex, which depends on `label_key` and can never match a name list. The CLI passes the raw `--by`. The same person therefore arrives as two different strings. (b) The ticket says both lists are "deny-all". It never says whether `Limits.stop` / `engage` is checked. If it is, an empty default config means nobody can stop. That contradicts the problem statement (an emergency stop that always works). If it is not, L40 and L44 are wrong. (c) Nothing says where `Limits` gets the lists. `Limits.__init__(store, audit, registry)` has no such parameter.
*   **Rationale:** evidence: L stop_gate.py:336 `limits.stop(self._lbl(by), ...)`, :386 and :388 `limits.reset(self._lbl(by), ...)`. L limits.py:15 (constructor). M app.py:171 and M cli.py:209 build `Limits(store, audit, reg)`. M config.py has no identity field (grep found none).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Same decision as A2/A3 (A13(3)); the Limits constructor gets the reset list; app.py and cli.py join the change list. The finding is valid: the reviewer cites evidence that can be read (L stop_gate.py:336 `limits.stop(self._lbl(by), ...)`, :386 and :388 `limits.reset(self._lbl(by), ...)`. L limits.py:15 (constructor). M app.py:171 and M cli.py:). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface "Who may stop, who may reset" (L26); Security (L40-44); Tests (L47)
    *   Change: State explicitly: authorization runs on the raw name before masking, in one place, with raw name plus label both written to the audit. Say that `stop`/`engage` is never blocked by a list (the in-process flag and the store write always happen), or give the default. Give `Limits` a constructor argument for the lists, and add `app.py:171` and `cli.py:209` to the change list.

### [Issue 5] [`egm-design`] - Severity: Major (finding id A10, adversarial)
*   **Affected Scope:** Test plan (b), (a), (d) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The process tests are vacuous or non-deterministic. (a) "final row equals one of them" passes with an unconditional upsert. (b) cannot force "B writes between A's read and write" across OS processes without a barrier hook, which the ticket does not describe. The tests skip silently without `HADAVIN_TEST_PG_DSN`, so the key Tier A proof can skip green. (d) is threads on a fake.
*   **Rationale:** evidence: Ticket "Race and process tests".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket "Race and process tests".). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Test plan (b), (a), (d)
    *   Change: Test the race deterministically at store level: `clear_kill_switch_if(stale)` returns False, and the row remains. Use an interleaving hook or a paused connection. CI must fail if these tests skip (`HADAVIN_REQUIRE_PG=1`). For (a), assert 8 distinct audit rows and a consistent (by, ts) pair. Add a cross-process in-flight test: stop in process A, tick in process B.

### [Issue 6] [`egm-design`] - Severity: Major (finding id A11, adversarial)
*   **Affected Scope:** In-flight barrier of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The barrier is per process. `engage` waits only for this process's `_inflight`. Test (c) covers threads in one process.
*   **Rationale:** evidence: `stop_gate.py:171-184, 284-292, 343-349`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`stop_gate.py:171-184, 284-292, 343-349`.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: In-flight barrier
    *   Change: Document it as a per-process barrier. Either add a cross-process in-flight registry (a store lease) or define `complete` as per-process, and say what the sweep may assume. Cap `cache_ttl` in config and test the stale-allow window.

### [Issue 7] [`egm-design`] - Severity: Major (finding id A12, adversarial)
*   **Affected Scope:** Open point 2 / row store of `handover/tickets/P2a.md`
*   **Discrepancy Description:** `RowStore` is memory-only and has no consumer in core. Nothing imports it except `testing/contracts.py`. The `config_view` has none either, so the only "link" (`ConfigHolder.swap` for the allow-lists) is not implemented in P2a-1 and nothing reloads the lists.
*   **Rationale:** evidence: Ticket "Files" (P2a-3), Open point 2.
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** Plan-v3 row P2a (frozen) says 3 PRs: gate, row store, config view. The reviewer's point (two sub-PRs have no caller) is valid, but cutting or moving them needs an amendment by the lead. Recommended: keep them in the ticket, state plainly that they ship without a core caller, and ask the lead to move P2a-2/P2a-3 to the first consumer if the review budget is tight.
*   ***Proposed Edit:***
    *   Location: Open point 2 / row store
    *   Change: Cut P2a-2 and P2a-3 from the Tier A path, or move them to the first consumer. Keep the stop store-backed. If they stay, say which function reads the lists at call time.

### [Issue 8] [`egm-design`] - Severity: Major (finding id A13, adversarial)
*   **Affected Scope:** Sub-PR coupling and file ownership of `handover/tickets/P2a.md`
*   **Discrepancy Description:** Internal contradictions. P2a-1 CREATEs `tests/stop_state_mutants.py`, the runner and `testing/mutation.py`. P2a-2 also adds rows to `stop_state_mutants.py` and is meant to merge first, because it carries the weak-row fix. The Done section says "P2a-2 first", yet P2a-2's file list has no runner, so the weak-row fix cannot be proved there.
*   **Rationale:** evidence: Ticket "Files" vs "Done".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket "Files" vs "Done".). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Sub-PR coupling and file ownership
    *   Change: Pick one owner for runner + mutants file (P2a-2, since it merges first), and have P2a-1 and P2a-3 only append rows. Update the file lists.

### [Issue 9] [`egm-design`] - Severity: Major (finding id A14, adversarial)
*   **Affected Scope:** Hot files of `handover/tickets/P2a.md`
*   **Discrepancy Description:** P2a-1 touches `limits.py`, three store files, `config.py`, `cli.py` and `CHANGELOG.md`, and has to wait for P4d. F6 does not list P2a for `config.py`/`cli.py`. P4b1 and P4c queue behind it on `limits.py`.
*   **Rationale:** evidence: Ticket Depends-on and Open point 5.
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** Amendment F6 lists P2a only for limits.py; the reviewer says P2a-1 also touches config.py and cli.py and waits for P4d. Whether F6 is extended (P2a in the config.py and cli.py lists, order against P4a/P4b1) is the lead's decision. Recommended: extend F6 and keep P2a-1 as one sub-PR split into two commits (Limits identity/CAS/label first, gate second).
*   ***Proposed Edit:***
    *   Location: Hot files
    *   Change: Split P2a-1: (i) `Limits` identity/CAS/label, (ii) gate and runner. The lead should decide the F6 amendment before building.

### [Issue 10] [`egm-design`] - Severity: Major (finding id A15, adversarial)
*   **Affected Scope:** Rollback / non-revertible semantics of `handover/tickets/P2a.md`
*   **Discrepancy Description:** Deny-all lists lock out every reset on first deploy. "Old code ignores the list" is only a loud failure if config rejects unknown keys. I saw `extra="forbid"` on one config model (`config.py:52`) and did not check that it covers the new section.
*   **Rationale:** evidence: `config.py:52`. Ticket Rollback.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`config.py:52`. Ticket Rollback.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Rollback / non-revertible semantics
    *   Change: Test that `ce70eb5` rejects the new keys. If it does not, ship a no-op field in a prior PR. Define the first-deploy bootstrap.

### [Issue 11] [`egm-design`] - Severity: Major (finding id A16, adversarial)
*   **Affected Scope:** Unreadable store / fail-safe of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The fail-closed claim has a gap. The ticket itself marks as UNVERIFIED what `agent_loop._limits_stop` does when `limits.blocked()` raises. The core `Limits.blocked` also raises on a store read error.
*   **Rationale:** evidence: Ticket "Fail closed". `limits.py:21-35`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket "Fail closed". `limits.py:21-35`.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Unreadable store / fail-safe
    *   Change: Read the caller and add a test: the store raises, the loop ends STOPPED with a reason. Make this a gate for P2a-1.

### [Issue 12] [`egm-design`] - Severity: Major (finding id A17, adversarial)
*   **Affected Scope:** "Mutation runner carried from PR #50" of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The runner in `src/hadavin_sdk/testing/mutation.py` ships in the wheel. It rewrites source files, which the repo's own rule says leaves a mutated `src/` when killed (long-jobs rule). The "small" PR carries about 400 lines of tool, plus rewrites of 774 lines of mutant rows.
*   **Rationale:** evidence: Ticket "Files"; `.claude/rules/long-jobs-run-detached.md`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket "Files"; `.claude/rules/long-jobs-run-detached.md`.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: "Mutation runner carried from PR #50"
    *   Change: Move it to `tools/`, not the wheel. Have the runner work in a temp copy, with a `git status` clean check in evidence.

### [Issue 13] [`egm-design`] - Severity: Major (finding id A4, adversarial)
*   **Affected Scope:** "Personal data in principal" of `handover/tickets/P2a.md`
*   **Discrepancy Description:** Masking is not at the choke point. `Limits.stop/reset` and the `kill_switch.by` column store whatever `by` the CLI gives, e-mail included, in clear. The `@`-removal fix lives in `stop_gate._label`, so it only covers gate callers.
*   **Rationale:** evidence: `limits.py:38-50`, `cli.py:391, 399`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`limits.py:38-50`, `cli.py:391, 399`.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: "Personal data in principal"
    *   Change: Move `_label` (with the `@` change) into `Limits` or `audit/labelkey`. Test the CLI path and the table column.

### [Issue 14] [`egm-design`] - Severity: Major (finding id A5, adversarial)
*   **Affected Scope:** `label_key` / keyed-label fix of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The fix is sound (HMAC-SHA256, truncated to 128 bits) but incompletely specified.
*   **Rationale:** evidence: Ticket Open point 4. `stop_gate.py:106-108` (random per-process key).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket Open point 4. `stop_gate.py:106-108` (random per-process key).). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: `label_key` / keyed-label fix
    *   Change: Make the fallback refuse unless an explicit dev flag is set, in P2a itself. Write a key id into the label (`id:k1:...`) so rotation is traceable. State the retention rule for old keys.

### [Issue 15] [`egm-design`] - Severity: Major (finding id A6, adversarial)
*   **Affected Scope:** "Audited reset" / reset race of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The compare-and-set is opt-in. The CLI path and plain `Limits.reset(by)` have `expect=None`, which is an unconditional clear.
*   **Rationale:** evidence: `limits.py:57-70`, `cli.py:399` (no `expect`).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`limits.py:57-70`, `cli.py:399` (no `expect`).). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: "Audited reset" / reset race
    *   Change: The CLI must show the current (by, ts) and require it back as the token (`reset --expect <ts>`), or reset must always CAS on what the caller last read. Add a mutant row "CLI reset unconditional" with a killing test.

### [Issue 16] [`egm-design`] - Severity: Major (finding id A7, adversarial)
*   **Affected Scope:** `release`/`engage` semantics of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The CAS token can be wrong, and it disappears silently. Both failures make `release` unconditional.
*   **Rationale:** evidence: `stop_gate.py:336-338, 385-388, 144, 191`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`stop_gate.py:336-338, 385-388, 144, 191`.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: `release`/`engage` semantics
    *   Change: `Limits.stop` should return the stored record, so there is no second read. A missing token must refuse `release` (not downgrade). Require `expect` in the gate's constructor check, as is done for `source`. Distinguish "switch written, audit failed" from "switch not written".

### [Issue 17] [`egm-design`] - Severity: Major (finding id A8, adversarial)
*   **Affected Scope:** `release` re-stop of `handover/tickets/P2a.md`
*   **Discrepancy Description:** In `release`, the reset is committed to the store before the gate checks `_gen`. If an engage ran meanwhile, the stop is written again. Between those two writes the durable switch is OFF.
*   **Rationale:** evidence: `stop_gate.py:394-411`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`stop_gate.py:394-411`.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: `release` re-stop
    *   Change: Check `_gen` before the store write, or make release a single store CAS. Test: assert the store is never observed OFF while any engage is pending.

### [Issue 18] [`egm-design`] - Severity: Major (finding id A9, adversarial)
*   **Affected Scope:** "Nothing in core src calls StopGate" / Open point 7 of `handover/tickets/P2a.md`
*   **Discrepancy Description:** Module exists, nothing enforces it, and no package owns the wiring ("the lead adds it to P4c or a new row"). For a Tier A control that is a paper control.
*   **Rationale:** evidence: Core `runtime/agent_loop.py:241, 771` (the existing check). Ticket Open point 7.
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** Which package owns wiring StopGate into the run path is a scope decision of the lead (plan-v3 row P2a and amendment F6 name no such owner). Recommended: the ticket says the module is 'unwired' until an owner is named, adds the end-to-end test to P2a as an xfail-free test only if the owner is P2a; recommendation: add the wiring to P4c (agent_loop.py is its hot file).
*   ***Proposed Edit:***
    *   Location: "Nothing in core src calls StopGate" / Open point 7
    *   Change: Name an owner and a package before P2a-1 merges. Add an end-to-end test in P2a (agent loop, then stop, then a new action refused). Do not call the kind "done" for Tier A without the wiring, or label it "unwired" in the ledger and CHANGELOG.

### [Issue 19] [`egm-codebase-details`] - Severity: Major (finding id C2, correctness)
*   **Affected Scope:** Interface "Personal data in principal" (L25); Fail-before (4) (L47) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The e-mail fix covers only the gate path (`_label`). The CLI path (`limits stop/reset --by X`, the main reset path) writes `principal=by` raw into the audit row. It also stores `by` raw in `kill_switch.by`. The fail-before test would pass on the gate path while the CLI still logs the address. Removing only `@` leaves other personal names in clear: `[A-Za-z0-9_.:@ -]{1,60}` still matches "Alice Smith" and "alice.smith". The ticket's own L24 calls the principal a "masked label" while L25 says plain names are stored as written.
*   **Rationale:** evidence: M limits.py:32-41 (`principal=by`); M cli.py:391, 399, 396; L limits.py:38-46; L stop_gate.py:100-115 (class and docstring).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (M limits.py:32-41 (`principal=by`); M cli.py:391, 399, 396; L limits.py:38-46; L stop_gate.py:100-115 (class and docstring).). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface "Personal data in principal" (L25); Fail-before (4) (L47)
    *   Change: Mask at the one choke point, `Limits._event` and the `KillSwitch.by` write, for stop, reset, refused and denied rows. Decide whether human names count as personal data (rule 5). If yes, hash every principal, or allow only role-style ids. Add a CLI-path test.

### [Issue 20] [`egm-codebase-details`] - Severity: Major (finding id C3, correctness)
*   **Affected Scope:** Depends on (L9) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The ticket says "P4d then P2a-1 (lead decision, amendment A9 F6 and memo-5)". Neither document says that. F6 lists `store/postgres.py` as (P4d, P4b1, P6b2) with no P2a. Memo-5 section 2 gives P2a no `store/*` files. The plan row says "Depends on P1". Plan section 7 step 5 says "P2a and P4d", with P2a first. So this is the ticket's own proposal presented as a decision. Open point 3 admits the slot is UNVERIFIED. Also missing: (i) `config.py` order against P4a. Memo-5 section 2 expects P4a to touch `config.py`, and rule 10 lists P4a on the hot files, but L11 orders P2a-1 only against P4b1, P5b3, P5c and P6a. (ii) P4d's contract suite carries an "introspection test for missing methods" (F7). A new Store method `clear_kill_switch_if` would trip it, yet L51 says P2a does not edit `test_store.py`. (iii) P4b1 also adds Store methods (`store/protocol.py`, `memory.py`), and no order against P2a-1 is given.
*   **Rationale:** evidence: A9 F6 (amendments.md:22); memo-5.md:29, 82-88; plan-v3 section 7 item 5 and row P2a.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (A9 F6 (amendments.md:22); memo-5.md:29, 82-88; plan-v3 section 7 item 5 and row P2a.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Depends on (L9)
    *   Change: Remove "lead decision" and ask the lead to ratify it with an amendment. Name the order on `config.py` (P2a-1 vs P4a) and on `store/protocol.py` / `memory.py` (P2a-1 vs P4b1). State how the new method gets its rows in P4d's suite.

### [Issue 21] [`egm-codebase-details`] - Severity: Major (finding id C4, correctness)
*   **Affected Scope:** Source / Files / Done: split into 3 PRs (L31-33, L65, Open point 6) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The three PRs are not separable as written. `tests/stop_state_mutants.py`, `testing/mutation.py` and `tools/mutation_runner.py` are CREATED in P2a-1 (L31). P2a-2 and P2a-3 add mutant rows to that file (L32-33) and run evidence command 3 (L60). But L65 says P2a-2/-3 may merge as soon as P1 has, while P2a-1 merges last, after P4d. L65 and Open point 6 say the runner "lands in the first to merge", which contradicts L31. `testing/` is a new package on M (no `src/hadavin_sdk/testing/` there). L has `testing/__init__.py`, which no PR in the ticket lists. Both P2a-1 (`mutation.py`) and P2a-2 (`contracts.py`) put files into it. The import graph itself is clean.
*   **Rationale:** evidence: M: Glob `src/hadavin_sdk/testing/*` returns nothing. L testing/__init__.py exists.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (M: Glob `src/hadavin_sdk/testing/*` returns nothing. L testing/__init__.py exists.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Source / Files / Done: split into 3 PRs (L31-33, L65, Open point 6)
    *   Change: Make P2a-2 the first PR and give it: `testing/__init__.py`, `mutation.py`, `tools/mutation_runner.py`, `tests/stop_state_mutants.py`, `contracts.py`. P2a-1 and P2a-3 then only append rows. Fix L31 accordingly.

### [Issue 22] [`egm-codebase-details`] - Severity: Major (finding id C5, correctness)
*   **Affected Scope:** Interface `release` (L23); Fail closed (L28) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The compare-and-set silently degrades to an unconditional clear. `_wrote` is set from `_read_switch()`, which returns None on any read error or if the switch reads off. `release` uses CAS only when `self._cas and self._wrote is not None`. Otherwise it calls `Limits.reset` with no `expect`. `_wrote` is also None after `restore(True)`, because only `engage` sets it. So the normal path restart, `restore(True)`, `release` has no CAS and clears another operator's newer stop. This is the same class as ledger BL-core-pr50-r3-014. The ticket says "compare-and-set against the stop THIS gate wrote" and says nothing of the fallback.
*   **Rationale:** evidence: L stop_gate.py:186-192, 338, 385-388, 144.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (L stop_gate.py:186-192, 338, 385-388, 144.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface `release` (L23); Fail closed (L28)
    *   Change: State the fallback and close it: no CAS means `release` refuses (fail closed), or `restore(True)` records the current `(by, ts)`. Add a test for each path.

### [Issue 23] [`egm-codebase-details`] - Severity: Major (finding id C6, correctness)
*   **Affected Scope:** Mutation plan (L52-55); Source (L14) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The counts are wrong. "189 rows" in `tests/promoted_mutants.py` contradicts the lead's own evidence: ledger BL-core-pr50-ev5-002 says "261 of 262 good". Statically I find 190 literal `Mutant(` rows plus at least three generated blocks (L promoted_mutants.py:1432-1569 holds 19 rows; others start at :1571 and :1892). The 31+7+3+14 = 55 split by name prefix is correct (I counted each prefix). But "the 55 rows for these modules" is not the base. Many more `fix:`, `b2:` and `b3:` rows target the gate, the row store and the label (for example `SG` rows at :1512-1540, `RS` at :1498-1511). Their killers live in `tests/test_pr50_fix_batch.py`, `-batch2.py` and `-batch3.py` (77 stop_gate/rowstore/labelkey references). The Files section never mentions moving those test files. Those batch files also hold tests of `capped`, `redact` and `http`, which are not P2a.
*   **Rationale:** evidence: L promoted_mutants.py:20-21, 1799, 1421-1600; ledger-seed.md:133.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (L promoted_mutants.py:20-21, 1799, 1421-1600; ledger-seed.md:133.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Mutation plan (L52-55); Source (L14)
    *   Change: Recount with the runner. List the exact killer tests to move or split per PR. Say which `CA`, `RD`, `HT`, `MU`, `MR`, `CT` rows stay out of P2a.

### [Issue 24] [`egm-codebase-details`] - Severity: Major (finding id C7, correctness)
*   **Affected Scope:** Files (L31) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The change list is incomplete for deny-all. These existing tests call `Limits.reset` or the CLI reset with an arbitrary name and would start failing: `tests/test_s5_runtime.py:127`, `tests/test_review_fixes.py:153`, `tests/test_cuj.py:254`, `tests/test_review_pr3_round2.py:282-288` (the `kill_switch` helper), `tests/test_p2_postgres.py:206-213`. The ticket lists the last one only as "reused" (L38). Other gaps: `app.py:171` (constructs `Limits`), `tests/contracts/conftest.py` (every contract suite needs a fixture there; P4d changes it too; "an entry in `tests/contracts/kinds/`" alone does nothing), and a new contract test module.
*   **Rationale:** evidence: grep of M tests and src (results above); M tests/contracts/conftest.py:29-70.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (grep of M tests and src (results above); M tests/contracts/conftest.py:29-70.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Files (L31)
    *   Change: Add all of them to Files, each marked Create/Modify, with the order against P4d on `conftest.py`.

### [Issue 25] [`egm-design`] - Severity: Nit (finding id A18, adversarial)
*   **Affected Scope:** Interface: stop reason of `handover/tickets/P2a.md`
*   **Discrepancy Description:** There is no reason and no stop-reason field. Two stops with different reasons overwrite `by` and `ts`; the first one's context survives only in the audit.
*   **Rationale:** evidence: `limits.py:44-51`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`limits.py:44-51`.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface: stop reason
    *   Change: Say it plainly in the CLI output ("last stop by..., N earlier stops in audit").

### [Issue 26] [`egm-design`] - Severity: Nit (finding id A19, adversarial)
*   **Affected Scope:** Hosted adapter outline of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The trigger "a client asks" is vague, and there is no stop-backend interface. `Limits` is a concrete class, so the outline has nothing to implement against.
*   **Rationale:** evidence: Ticket "Neutral default".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket "Neutral default".). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Hosted adapter outline
    *   Change: Define a Protocol (`stop/reset_if/is_stopped`) in P2a-1 and run the contract suite against the memory and Postgres stores. State a dated review (as the models rule does).

### [Issue 27] [`egm-design`] - Severity: Nit (finding id A20, adversarial)
*   **Affected Scope:** Clock / `ts` of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The CAS token uses `ts`, set client-side (`default_factory=now`). Equality on Postgres timestamptz round-trip is untested (tz-naive vs aware, precision).
*   **Rationale:** evidence: `models.py:251-254`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`models.py:251-254`.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Clock / `ts`
    *   Change: Test the round trip on Postgres. Prefer a server-side version counter.

### [Issue 28] [`egm-design`] - Severity: Nit (finding id A21, adversarial)
*   **Affected Scope:** Step 0 / unnamed failing test of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The failing test is unnamed, and the builder is asked to "fix at its cause" outside P2a's files.
*   **Rationale:** evidence: Ticket "THE FAILING TEST".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket "THE FAILING TEST".). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Step 0 / unnamed failing test
    *   Change: The evidence runner (not the builder) names it first.

### [Issue 29] [`egm-design`] - Severity: Nit (finding id A22, adversarial)
*   **Affected Scope:** Wording of `handover/tickets/P2a.md`
*   **Discrepancy Description:** "Audited reset" is used for both a gate release and the CLI; "stop identity" and "reset identity" are called "identities" while they are name strings; "complete" in `EngageResult` can read as "everything stopped".
*   **Rationale:** evidence: Ticket Interface.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket Interface.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Wording
    *   Change: Rename "allowed names"; define `complete` in one sentence.

### [Issue 30] [`egm-codebase-details`] - Severity: Nit (finding id C10, correctness)
*   **Affected Scope:** P2a-3 (L33) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** "Only link ... `ConfigHolder.swap(expect=)` lets two administrators change the two allow-lists" describes behaviour no file implements. `Config` is a frozen pydantic model loaded from files (M config.py:52, 316). The ticket wires nothing to `ConfigHolder`, and no core code uses it. If it were wired, a hot-swap of `reset_identities` would be an unaudited change to the control that guards the reset. Also, L33's "nothing under `src/` imports `config_view` or `rowstore` except `testing/contracts.py`" is wrong: `contracts.py` imports only `collections.abc` and `typing` and takes a factory.
*   **Rationale:** evidence: L testing/contracts.py:7-10, 18-21; grep over L src for `rowstore\|config_view`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (L testing/contracts.py:7-10, 18-21; grep over L src for `rowstore\|config_view`.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P2a-3 (L33)
    *   Change: Reword to say that P2a-3 ships a module with no core caller. Do not claim the link unless you add it and audit it.

### [Issue 31] [`egm-codebase-details`] - Severity: Nit (finding id C11, correctness)
*   **Affected Scope:** Open points 4, 3 and UNVERIFIED in Existing code (L25, L38, L76) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** "Needs a profile flag; P6a owns profiles" is partly wrong. `Config.environment` (dev, pilot, prod) already exists, with a refusal list in `_cross_checks`, so refusing the per-process label key outside "dev" can be a validator today. The "UNVERIFIED that no keyed-hash helper exists" can be answered: `agent_loop._restored_digest` is an HMAC under a deployment key (`hooks.restored_key`), and it also has an unkeyed fallback, the same weakness this ticket wants to remove.
*   **Rationale:** evidence: M config.py:317, 365-373; M agent_loop.py:256-267.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (M config.py:317, 365-373; M agent_loop.py:256-267.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Open points 4, 3 and UNVERIFIED in Existing code (L25, L38, L76)
    *   Change: Cite both. Use the existing `environment` field.

### [Issue 32] [`egm-codebase-details`] - Severity: Nit (finding id C12, correctness)
*   **Affected Scope:** various of `handover/tickets/P2a.md`
*   **Discrepancy Description:** Small factual slips. `limits.py:36-51` (L12) is 43-51 on ce70eb5 (`stop` 43-46, `reset` 48-51). agent-killswitch has 21 `.py` source files, not 20 (the 3,756 lines is right). MANIFEST ids 2962-2985 cover only 24 of about 66 killswitch rows. `ledger.md` has 4 lines by my count (ticket says 3). The Problem section is 6 sentences (template: 3-5). The `engage` signature omits `timeout: float \| None` (L stop_gate.py:316).
*   **Rationale:** evidence: as stated
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (as stated). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: various
    *   Change: Correct.

### [Issue 33] [`egm-codebase-details`] - Severity: Nit (finding id C8, correctness)
*   **Affected Scope:** Weak mutant row (L55) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The conclusion is right: the row is weak at PR50-local and not weak at PR50-pushed. The mechanism is stated wrongly. The `Mutant` for `rows: no default row limit` sets no `only_test`, so the whole test file runs. The first failing test is `test_the_row_store_meets_the_contract` (L test_promoted_controls.py:491), because the mutated default makes `RowStore()` raise ValueError at the `allow_unbounded` check (L rowstore.py:134-138). `judge()` returns WRONG_REASON because the `expect` string is not in that id or line (L testing/mutation.py:61-62). The CRASH check comes later and is never reached. The ticket's "the pinned test never reaches `assert`; the kill is by a crash" is not what the runner printed. At P the constructor has no check (P rowstore.py:73-79). The mutant leaves `RowStore()` valid, so `assert rs._max_rows == 100_000` fails (P test_promoted_controls.py:1791) with the expected name. That is a clean KILL. Also, the suggested snippet "`DEFAULT_MAX_ROWS = 100_000` to `10**12`" does not match at L: the constant is written over three lines (L rowstore.py:114-116), so the runner would print SNIPPET NOT FOUND (ERROR). Fix (ii) needs a new test: none exists for `RowStore(max_rows=None)` without opt-in (L tests contain only `allow_unbounded=True` uses).
*   **Rationale:** evidence: Use `old="max_rows: int
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Use `old="max_rows: int). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Weak mutant row (L55)
    *   Change: None = DEFAULT_MAX_ROWS"` and `new="... = 10**12"`, and set `only_test=` to the pinned test. Write the new `pytest.raises(ValueError)` test and say so.

### [Issue 34] [`egm-codebase-details`] - Severity: Nit (finding id C9, correctness)
*   **Affected Scope:** Files, `cli.py` (L31) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The description of today's CLI is not exact. It does not report "any non-audit error as store unreachable": `_kill_switch_store_down` returns exit 4 (unreachable) only when `is_connectivity_error` is true, otherwise exit 2. The real hazard is the design choice `StopNotPermitted(PermissionError)`: `is_connectivity_error` returns True for any `OSError`, and `PermissionError` is one. The CLI, `tick.py:342` and `:362`, and `audit/chain.py:533` would all call a refused reset "store unreachable".
*   **Rationale:** evidence: M cli.py:366-380; M store/protocol.py:33; M tick.py:342, 362; M audit/chain.py:531-533.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid: use RuntimeError, not PermissionError (OSError makes is_connectivity_error say 'store unreachable'). The finding is valid: the reviewer cites evidence that can be read (M cli.py:366-380; M store/protocol.py:33; M tick.py:342, 362; M audit/chain.py:531-533.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Files, `cli.py` (L31)
    *   Change: Do not derive from `OSError`; use `RuntimeError`, as `SwitchChanged` and `StopGateBusy` do. Reword the `cli.py` reason.
