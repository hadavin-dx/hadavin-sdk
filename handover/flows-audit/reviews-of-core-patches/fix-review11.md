# fix-review11 (round 11 of REVIEW.md; static, nothing run, nothing committed)

Inputs: review-design-r11.md and review-codebase-r11.md (reviewer words, unverified). Each claim was opened against src before editing. Backup: scratchpad bak-rev11.md. EGM skipped: fixer role.

## Unverified or not done (first)
- Nothing ran. Every Postgres, trigger, foreign key, column-grant and patch statement is unverified; REVIEW.md says so in the rows and in "Not checked".
- The identity table for X-6 is a PROPOSED deployment, not a fact: the repository does not say whether the agent loop and the tick are one process. The row says so and says what still holds if they are one.
- Not opened: the secrets kinds (can a process be scoped to a list of secret names), migration 0001 column names for `approval_decisions`, what `execute` checks beyond the restored-value recheck, C-7 consumers outside the files listed.
- My own round-10 mistake, found while weighing the foreign key: the primary key `(seq, hash)` I proposed for the head-seq checkpoint case does not work, because the runtime role can read the true hash (needed to append, chain.py:187) and the junk row can copy it. Corrected in X-5 (f).

## Reviewer claims checked
- Design B1 (identity table): right in substance; added (X-6) with live-profile refusal and negative test shape. Half right on one point: the repo does not show agent and tick as separate processes, so the table says what holds either way.
- Codebase M1 (self-approval via approval_requests): CONFIRMED. The agent INSERTs (requests.py:107) and the tick UPDATEs (requests.py:126, :210) approval_requests; tick.py:85-95 reconcile lists APPROVED and calls on_decided, which calls execute (agent_loop.py:799-806). The earlier X-6 fix would have left the hole. Added a guard trigger (INSERT must be PENDING; APPROVED or REJECTED only with a matching decision row); the alternative (move the tick UPDATE) rejected with a reason.
- Codebase M2 (receiver grants): CONFIRMED: decide calls _audit at requests.py:163 and :173. The "no write on runs" hedge closed: receiver.py:30 passes record_only=True and decide returns at requests.py:177 before on_decided.
- Codebase M3 (X-5 (f) test): CONFIRMED. chain.py:307-308 returns the head seq on old code, so assertion (A) passes there; only (B) valid row at head and (C) signed_through()==head fail. Corrected.
- Design M1 (spend trigger): right that owner/superuser can disable it and that the upsert path must be tested; weighed append-only spend (option B) against the trigger (option A) with costs; proposed A now, B named.
- Design M2 (FK): weighed; it stops above-head and wrong-hash junk rows but not a junk row with the true hash. Adopted as a second guard only. Also stated (i)'s cost (signer credential must not sit in the tick process).
- Design M3 (verdict vs C-3): CONFIRMED. Split: new row C-7 (unconditional negative token count and negative usd), C-3 keeps the conditional price check; Short answer, counts and the effective-Major paragraph updated.
- D1 C-4 reworded (after C-3's choke-point decision). D2 C-1 changed PROPOSE FIX to DECLINE with the reason in the row. D3 C-5 said to be a weaker DECLINE (patched-copy lines not read).
- O1-O4: "Open for the studio head" rewritten with the cost of accepting each choice, the fraction fixed by the drain (one of five problems), sub-choice costs, and "five, of which four live".
- G1 column grant chosen, "plain SELECT also works" dropped. G2 half right: operator needs no DELETE and no full SELECT, but INSERT alone fails because _append reads event_id, seq, hash (chain.py:185, :187), so reset is refused with exit 3; exact list written. G3 receiver list written incl. audit rights. G4 non-Postgres outline and trigger added. G5 two-release rollout order and rollback added. G6 lock_timeout tied to X-4.
- N1 (header): shortened to status plus pointer to logs. N2 five of which four live. N3 "four problems" now five (read-side denial added). N4 correction moved into X-2. N5 counts: current first.
- Codebase nits: migrate.py cite 333-339 fixed; header and log pointer fixed; "four named roles" replaced (up to seven) and the missing cli.py changes listed (cli.py:98, :138, :313-334, :341-343, :376-377); distinct migration numbers 0006 (FK), 0007 (spend), 0008 (approval guard), 0009 (checkpoint key, only if chosen).
- Round labels: my earlier "round 9" text is renamed "round 10" so the label matches fix-review10.md.

## Counts (script, exit code 0)
rows 26; Nit 10, Major 12, Minor 4; PROPOSE FIX 23, DECLINE 3 (C-1, C-5, A-9). Live Majors without any patch: X-4, X-5, X-6, C-7 (4); 5 after G5, 6 with C-3.

## Checks
See the final report for exit codes (count_review.py, check_secrets.py, check_refs.py, ruff check ., ruff format --check .).
