# fix-review12: round 12 of REVIEW.md (security and money path, no round cap)

Backup: scratchpad bak-rev12.md. Not committed.

## Unverified or not done (first)
- Nothing was run. The approval guard trigger, the column-level UPDATE grants, BEFORE UPDATE on the upsert DO UPDATE branch, the foreign key and the new constraints are Postgres behaviour I did not test. Patches and patched tree are not on disk.
- Not built: no source was edited. All new designs (guard, build profile, audit-writer function, moving ALLOW-class execution to the tick) are proposals in the rows.
- Not opened fully: `tests/contracts/test_store.py:237`; whether `approval_requests.summary` is changed anywhere; SQL column names of `approval_decisions`.
- Not decided (lead choices, listed in the file): audit-writer identity; ALLOW-class execution to the tick; FK second guard.

## Reviewer claims confirmed against src
- Design B1 (retarget, reset and replay, upsert over APPROVED): `models.py:182-190` (decision has no run_id), `tick.py:88-95`, `agent_loop.py:776-797`, `postgres.py:311` and `:204-218`, `requests.py:107`. All confirmed; guard in X-6 rebuilt.
- Design M1: `agent_loop.py:768` executes ALLOW plans, hooks at `:886-909`. Confirmed; identity table corrected.
- Design M2: `migrate.py:5`, `:320-326`; `chain.py:312`, `:315-317`. Confirmed; rollback now = snapshot, ON CONFLICT change one release before 0009, NOT VALID or pre-check.
- Design M3: `app.py:144-145`, `161-162`, `170-174`. Confirmed; build profile added.
- Design M4 (column-level UPDATE), M5 (FK weakness, tests `test_p2_postgres.py:289,296,299`), M6 (spend trigger not a guarantee), M7 (audit writer). Confirmed or reasoned from the grants; recorded.
- Design minor: fixture breakage list `test_store.py:103,114,166,237`; I found no direct DB hit in `test_p7_tick.py` (reviewer count differs; stated in the row).
- Codebase M1 (C-7 not live; producers `anthropic.py:142`, `openai_compat.py:142`, `bedrock.py:176`, `fake.py:54`): confirmed; row relabelled, fix is "negative = missing" with `ge=0` backstop (`common.py:164-165`, `:171`).
- Codebase M2 (headline: 6 price cases + 5 A-01 + 2 ceiling; evidence-13.md:43-58, :99): confirmed; evidence bullet and Short answer restated.
- Codebase N1 (count_review.py robustness): done. N3 (`tick.py:91-92`, `postgres.py:389-397`): hedge narrowed. N5-N7 cites fixed: `app.py:151-160`, `tick.py:59-60`, `chain.py:184-186`, `evalcli.py:154-157`, `0004:6-7`. N6 (verify flags unparseable JSON via `chain.py:397-400`) is true; reads still fail.
- Contested: none.

## Changes
REVIEW.md: Short answer rewritten in plain words; X-6 guard, identity table, rollback, migration numbers, build profile, audit writes, spend wording; C-7 relabel and fix; X-5(f) FK note; effective-Major paragraph (live X-4, X-5, X-6; C-7 apart; arithmetic 3+1+1+1+1+5=12); evidence headline; cites; Not checked; header status. count_review.py: decision cell found by pattern in cells 3 or 4. Counts unchanged (26 rows; Major 12, Minor 4, Nit 10; PROPOSE FIX 23, DECLINE 3).

## Checks
See the final report for exit codes (run from handover/flows-audit).

# Round 13 (review-design-r13.md and review-codebase-r13.md; log appended here as the brief said)

Backup: scratchpad bak-rev13.md. Not committed. Nothing was run against Postgres or the patches; every SQL statement is a proposal.

## Unverified or not done (first)
- All Postgres behaviour in the new text (temporary schema lookup, `TG_TABLE_SCHEMA` with `EXECUTE`, `REVOKE TEMPORARY`, `ENABLE ALWAYS`, `session_replication_role`, SECURITY DEFINER with a pinned search path) is the design reviewer's knowledge, not checked by me. No source or test was edited.
- Not designed: the receiver recomputing the approval summary (lead choice (5)(b)); the SQL version of the hash (byte-equality with Python's `json.dumps`).

## Findings, each opened in src
- Design B1 (temporary table bypass): CONFIRMED for the source part: `migrate.py:210-212` checks CREATE on `current_schema()` only; a grep of `src/hadavin_sdk` for TEMP, search_path, SECURITY DEFINER, ENABLE ALWAYS and session_replication_role finds nothing relevant. X-6 row: the false claim is withdrawn, three-part fix and negative tests (f) added, verdict "do not build the guard as written" in the Short answer and the row. Severity: row stays Major (scale note in Counts; the Blocker is a flaw in a proposed fix, not in today's code or the three patches); flagged to the lead as choice (5)(c).
- Design M1 (audit-writer function): confirmed as reasoning; minimum rules written in AUDIT WRITES. `migrate.py:80-85` accepts only `CREATE OR REPLACE FUNCTION`: confirmed.
- Design M2 (INSERT rule): CONFIRMED: `requests.py:97-107`, `agent_loop.py:747` and `:762-763` (gate decision and WAITING state come before the request, so the INSERT checks are feasible), `_recheck` `:776-797` never reads the approval. Added to the guard.
- Design M3 (frozen columns): CONFIRMED; `summary` has no update path (`requests.py:124,166,198,207` change other columns), `step_expires_at` changes only in the escalation (`requests.py:196-201`); clock-skew allowance added (`tick.py:81`).
- Design M4: CONFIRMED in src (`0002_audit_chain.sql:28-35` plain triggers; `migrate.py:219` compares owner name only; `migrate.py:285-288` optional roles). PARTLY CONTESTED: "like app.py:86-89" - that line checks only a purge secret name; the app cannot see how `migrate` was called, so the refusal is written as a start-up `effective_problems` check, a new piece of code.
- Design M5: CONFIRMED: `migrate.py:256` excuses only SELECT columns.
- Design Nits 1-4 added to the guard (shared Python transition function; `save_approval_decision` has no src caller, only `test_store.py:131,132,135`; second trigger on `approval_decisions`, which breaks `test_store.py:131-135`; race: reviewer found none, I did not look independently). Nit 5: `:114` was already in the breakage list.
- Codebase M1: line 106 said four live choices; fixed to two (matches line 23). M2: `agent_loop.py:742` sets `restored_hash` on every `gate.decide`; `:845-866` stops with `restored_unbound` for every plan; qualifier fixed, conclusion unchanged.
- Codebase Nits: 1 (`chain.py:397-400`, `_body_event_id` `:406-410`) added; 2 (migrate callers) list completed incl. `cli.py:330`; 3 (`test_p2_postgres.py:290`, `test_store.py:237` rationale) fixed; 4 (`model_copy` has many src hits, none a Route) fixed; 5 (22 collection errors) fixed; 6 (`askdata/config.py:61-70` - the reviewer's `config.py:61-69` is the demo's file, not `src`; `_migrate` `cli.py:312`, call `:330-339`; `checkpoint()` `:295-320`) fixed.
- Contested: none outright; one partial (M4 wording above). The reviewer said "Row counts 26, Major 12..." true and unchanged.

## Changes
REVIEW.md only (header, Short answer, counts line, evidence bullet, C-4, X-5 (c)(iii) and (i), X-6, single-dependency outline, Counts reading and effective-Major paragraph, Not checked, Open for the studio head). Counts unchanged: 26 rows; 0 Blocker, 12 Major, 4 Minor, 10 Nit; 23 PROPOSE FIX, 3 DECLINE. count_review.py not changed (the row parser needed nothing).

# Round 14 (review-design-r14.md and review-codebase-r14.md; log appended here)

Backup: scratchpad bak-rev14b.md. Not committed. Nothing was run against Postgres or the patches; every SQL statement is a proposal.

## Unverified or not done (first)
- All Postgres behaviour in the new text (function and operator lookup through the temporary schema, `session_replication_role` grant, BEFORE UPDATE on the upsert branch, `TG_TABLE_SCHEMA` with `EXECUTE format()`, `ENABLE ALWAYS TRIGGER` through the scanner, a changed `schema_version` failing `model_validate`, hash parity of SQL and Python JSON text) is the design reviewer's knowledge, not checked by me. No source or test was edited; nothing was built.
- Not opened: how the plan hash is built (design point 3 says it covers placeholders; reviewer words); the other `runs` columns (point 2 names only `cost_usd`); the patched copies (still not on disk).
- Round 13 log above, Findings, Design B1 line, still says the search "finds nothing relevant"; that wording is wrong (see below) and is corrected only in REVIEW.md, because this log is append-only history.

## Findings, each opened in src
- Design Major 1 (functions and operators): CONFIRMED in src for the part that can be read: `migrate.py:210-212` checks CREATE only on `current_schema()`. Written into X-6 fix (1) (now "and", with `SET search_path = pg_catalog, <schema>, pg_temp`), (3) (every schema on the search path) and test (f).
- Design Major 2 (spend): CONFIRMED: key columns `0001_core.sql:87-91`, `0003_approvals_tick.sql:15-19`; grants `migrate.py:53-54`, `:47`; `postgres.py:433-442`; `limits.py:24-29`; `agent_loop.py:256-257`. Freeze keys, no decrease, monotonic `runs.cost_usd`, tests. Full `runs` column list not written.
- Design Major 3 (approval binding): CONFIRMED in src: `agent_loop.py:845-867`, `:273-278`, `:292`; `migrate.py:57`, `:65`. Plan-hash coverage not opened. X-6 point 3 and the AUDIT WRITES choice (1) now say it is a bypass, not harmless; studio head choice (5)(g).
- Design Major 4 (release A): CONFIRMED: `migrate.py:51`, `requests.py:97-107`. Written into X-6 point 4 and the CHANGELOG note.
- Design Major 5 (INSERT and UPDATE rules): CONFIRMED with one correction: the update builders SET every column except `approval_id` (`postgres.py:316-326`, `:349-355`), so the reviewer's "written by update builders" is true for `schema_version` only; `approval_id` is the WHERE key. The denylist point stands. `requests.py:103` confirms the agent writes `step_expires_at`.
- Minors 6 to 9: CONFIRMED in src (`requests.py:171`, `:211`; `chain.py:68-72`, `:397-410`; `postgres.py:349-355`; ENABLE ALWAYS needs a new migration because 0002 is released). Written as X-6 points 6 to 9.
- Wrong-claim note: CONFIRMED: hits at `migrate.py:126`, `migration_numbers.py:12-14`, `:251`; `refused_statements` `:633-639`. REVIEW.md B1 wording now says migration-time only and that `REVOKE TEMPORARY` is an operator deployment step.
- Codebase cites 1 to 7: all CONFIRMED and fixed: X-2 `record_decision` at `:337`; X-5 callers (`test_k5_fixes2.py:302`, `test_p3b_neutral_audit.py:324`, `test_k2_migrations.py:115,120,125`, `test_p2_postgres.py:78`; "completes" withdrawn); B1 wording; C-4 `tools.py:494`; G-2 `gate.py:59` (also `:42` found by me); C-3 `config.py:80-94`; X-6 (4) `agent_loop.py:809` loads, `:814` rechecks.
- Contested: none outright; the one partial is the `approval_id` point above.

## Changes
REVIEW.md only: header status, round log sentence, Short answer (X-6 round 14), X-2, X-5, X-6 (status, B1 wording, fix (1) and (3), test (f), point (4) wording, AUDIT WRITES choice (1), new ROUND 14 block), C-3, C-4, G-2, Not checked, Open for the studio head (sub-choices (d) to (g)). Severity of X-6 kept Major: no defect in today's source or the three patches beyond what the row records. Counts unchanged: 26 rows; 0 Blocker, 12 Major, 4 Minor, 10 Nit; 23 PROPOSE FIX, 3 DECLINE.

# Round 15 (review-design-r15.md F1-F13 and review-codebase-r15.md facts 1-5; log appended here)

Backup: scratchpad `REVIEW.md.bak` (taken before the first edit). Not committed. Scratch copies of the source trees were made under the session scratchpad; no source tree or patch file was edited. Nothing was run against Postgres, n8n, HubSpot or the network.

## Unverified or not done (first)
- I ran `git apply --check` and `py_compile` only. I did NOT run pytest, ruff or bandit on any patched tree, so "the rebased C-01 and G5 work" means "they apply and compile", not "their tests pass".
- Postgres behaviour in the X-5 (h) correction (user-settable timeouts, `REVOKE EXECUTE` on advisory-lock functions) is my own knowledge, marked UNVERIFIED in the text. The psycopg placeholder syntax in D-3 (4) is also from memory.
- The design reviewer wrote "two live Majors" in F13. I count three (X-4, X-5, X-6); the text says so plainly. Not changed to two.
- Reviewer F1 offered "drop C-3 to Minor"; I did not (reason in the C-3 row). F6 asked for no silent change; I changed no table severity for X-5 and X-6.

## Evidence I ran (commands in REVIEW.md, section "Inputs read", bullet "PATCH BASES AND git apply --check")
- b4cce5b copy: `git apply --check` C-01 0, A-01 0, G5-wording 0; applying all three in order 0, 0, 0.
- This checkout (commit 176a0cbe0): C-01 exit 1 (`config.py:362`, hunk 2 context `refused = []` and `!= "dev"`), A-01 exit 0, G5-wording exit 1 (`tests/warden_port/test_gate.py:1`, docstring text differs). With `-C1`: C-01 0, G5-wording 0; in-order apply with `-C1` 0, 0, 0; `py_compile` of the seven touched `src` files 0.

## Per finding
- Facts 1 and 3, design F10: fixed. "NOT on disk" wording removed or corrected everywhere it occurred (Inputs read, convention line, C-3, C-5, G-1, Effective Major paragraph, three Not checked sentences, Update section); three line bases stated; apply exit codes written; README claim "b4cce5b or later" marked untrue for C-01 and G5; Update section says the 9404-pass run was on b4cce5b, not on the current head. The pydantic pin at b4cce5b (2.14.1) was also checked.
- F1: CONFIRMED (`backends/table.py:545` comment, `guard/judge.py:40` `JudgeDetector(deps.llm, ...)`); C-3 rationale replaced; the remaining argument (Route built outside Config) kept; rating kept Major with a written reason.
- F2: CONFIRMED (evidence-13.md:99: two list tests failed when the step was removed; A-01.patch lines 190-205 assert `last_ok_at`); A-5 rewritten; rating Major to Minor.
- F3: CONFIRMED (`channel.py:29,36`, `slack_channel.py:81`); G-1 now says "understates", scoped to the approval channel; Short answer and Inputs wording fixed; G-1 Major to Minor.
- F4: C-2 Major to Nit, C-7 Major to Minor (threat model stated: hostile or compromised openai_compat endpoint or tampered recording), A-1 Major to Minor (README half of the claim is wrong, docstring right); each with a written reason in its row. A-5 and G-1 followed from F2 and F3. Counts re-run: 27 rows, 0 Blocker, 7 Major, 9 Minor, 11 Nit; 24 PROPOSE FIX, 3 DECLINE.
- F5: CONFIRMED (`llm/common.py:59-62`, `:164-165`); C-7 fix now charges the worst case, not the estimate.
- F6: kept the table as is; added a separate by-hand line "Blocker for the proposal and for pilot and production: 2 (X-5, X-6)" with the reasoning, in the Short answer counts paragraph, the Counts section, the Effective Major paragraph and the choices list ((6)). `count_review.py` does not count that line (it reads table rows only); not edited, reported.
- F7: C-01 verdict is now "DO NOT APPLY THE FILE AS WRITTEN", with the four parts and which hunks and tests to remove (ceiling hunk in `config.py`, `defaults.py` hunk, two ceiling tests and the `defaults` import).
- F8: CONFIRMED all four points (`migrate.py:56` no `portal=True`; `tick.py:287-292`; permanent alert from the missing A-01 row); new row D-3 (Minor). The note file itself was not edited (outside my edit scope); the corrections are recorded in REVIEW.md.
- F9: CONFIRMED as reasoning, UNVERIFIED against Postgres; X-5 (h) now says the timeouts are accident controls only and names the real control.
- F11: A-6 now states the per-row guard is a precondition of A-01.
- F12: added to A-4 (neutralise control characters, cap length, test with newline and ANSI escape); `models.py:196` confirmed free string.
- F13: plain first paragraph added at the top of the Short answer.
- "Missed in patches": folded into A-4 (no ERROR on the local-directory last resort, no local-directory test, the WARNING is untested) and noted that drained rows go in under the tick's own identity (X-2, X-5).
- Facts 2, 4, 5: C-5 cite explained (`config.py:373` patched b4cce5b; `:401` = this checkout with C-01 rebased; `:401` unpatched = environment raise); G-2 rewritten with a tree per number and `:203` addressed, `redact.py:947/:948` now read; C-4 `config.py:61` vs `:64` fixed; X-6 `migration_numbers.py` header `:3-5` to `:5-7`; A-1 README claim corrected; A-4 patch contents stated. Fact 2/4/5 cites were each opened and were right.

## Changes
REVIEW.md only (header, round log, Inputs read, new bases and commands bullets, Short answer and counts paragraph, evidence bullets, three patch headings, rows C-2, C-3, C-4, C-5, C-7, A-1, A-4, A-5, A-6, G-1, G-2, new D-3, X-2, X-5 (h), X-6 cite, Counts section and pasted output, Effective Major paragraph, README claims, Not checked, Open for the studio head, Update section).

# Round 16 (review-design-r16.md Majors 1-5, Minors 6-10, Nits 11-13; review-codebase-r16.md Minors 1-2, Nits 3-7; log appended here)
Fixer run 2026-11-16. Backup of the file before the edit: the session scratchpad, file REVIEW.r16.bak. Edited only REVIEW.md and this log. Nothing under /tmp/ch, /tmp/smfull, /tmp/core-b4p or /tmp/core-b4m was changed. EGM skipped for the edit itself: it is the fix step (egm-resolve) of a review round; the lead runs the next review.

## Unverified or not done (first)
- No test, lint, bandit or Postgres statement was run on any patch. Every Postgres statement in the X-6 parts is still UNVERIFIED. The new test proposed in row C-8 was not written into the patch and not run.
- Strangers item (design Major 5) is only partly done. Done: a ten-point plain summary and a one-line-per-row index at the top, a short labels section, process-log lines and old count history moved to the end ('History'), X-6 split into seven parts with what is wrong, who can do it and what it costs, plain lead sentences added to C-3, X-2, X-4 and X-5. NOT done: the round numbers and reviewer ids inside the rows (about 150 'round N' mentions, about 25 'design reviewer F' or 'design M' ids, many (a)/(i) sub-points) were not rewritten; the labels section explains them. X-5 (about 28,000 characters) and C-3 (about 9,000) are not split into parts. Next step: one more pass that rewrites X-5 and C-3 the way X-6 was done; I did not do it in this round because it is a rewrite of those rows' text, not an edit.
- `tools/check_secrets.py` returns exit code 1 on a file I did not touch (`flow-check/raw/test-take-check.txt:177`, token-like string of length 1100); not caused by this round, not fixed (outside the files I may edit); the studio head or the owner of that file must look.

## Per finding (reviewer words opened against source or patch before changing; none rejected outright)
- Design Major 1 (zero price on a self-hosted model): CONFIRMED. C-01.patch lines 14-26 exempt only kind `fake`; `backends/table.py:71-85` and `:529-535` register `openai_compat` as neutral, keyless on a loopback address; `k1b/replay.py:85-90` already refuses zero for every kind except `fake`. New row C-8 (Minor): the only exemption is `fake`; a self-hosted model needs a positive notional price so the limits still fire; exact README note and one test written in the row; single-dependency bullet; choice (8); C-6 points to it. Reviewer's statement that REVIEW had no text on this: true (grep of the backup for 'ollama', 'self-host', 'local model': 0 hits).
- Design Major 2 / codebase Minor 2 (C-7 stale sentence): CONFIRMED (the row said 'Severity stays Major' and later 'Major to Minor'); sentence deleted.
- Design Major 3 (uneven Major rule): ACCEPTED in substance. One rule written under 'Rating rule' (Major = a shown loss or bypass, or a broken written rule). C-3 stays Major (shown: the check sits in `Config`, the demo builds `Route` outside it; not shown: a live zero-price route); X-4 stays Major (shown: no caller, DB-down loss path at `chain.py:229`; not shown: frequency); A-2 and A-3 go to Minor (A-2: no sink shown that lacks `reconcile`; A-3: hidden backlog, no loss shown). X-2, X-5, X-6 keep Major under part (b) or (a). Counts: 27 rows became 28 (C-8), Major 7 to 5, Minor 9 to 12. Because the rule is my choice, it is recorded as choice (9) with the cost; if the studio head wants gaps in deferred patches to count, A-2 and A-3 return to Major.
- Design Major 4 (0 Blocker vs 2 Blockers): the line 'Blocker for the proposal and for pilot and production: 2 (X-5, X-6)' now sits directly under the pasted script output, and is repeated in the plain summary and the counts paragraph with one sentence saying the two lines use two scales.
- Design Major 5: partly done, see above.
- Design Minor 6 / codebase Nit 3 (A-4 'all five'): CONFIRMED (A-01.patch: ChainAudit at lines 146, 166, 176; list test 141 builds no sink; skip test 161 uses `object()`); now 'three of five'.
- Design Minor 7 (stale text): line 12 'earlier text said NOT on disk' and the Not checked clause 'not available to me then' removed; the eight rounds of count history moved out of the current counts line into History.
- Design Minor 8 (G-1 'understates'): softened to 'may understate'; the same-patterns comparison was NOT done and the row says so.
- Design Minor 9 (G2 check): read `approvals/gate.py:354`: `_UNVERIFIABLE` is defined and never called (grep over src), no `hedge` function exists; 'G2 not built' is true; recorded in G-1.
- Design Minor 10 (D-1 vs D-3): one numbered edit list for DEAD-MAN-CHECK.md added after the D rows; while A-01 is deferred the note names four steps and says nothing checks the audit outbox (X-4).
- Design Nit 11 (C-6 ceiling): C-6 now says the ceiling part is moot like C-2 and X-1. Nit 12: every Postgres statement in the X-6 parts is marked UNVERIFIED. Nit 13: X-4 now says the rating rests on the missing caller and the read loss path, not on measured loss.
- Codebase Minor 1 (pydantic text): CONFIRMED: `/tmp/core-b4p/pyproject.toml:16` reads `pydantic==2.14.1` and so does `pyproject.toml:16` of this checkout; fixed in Inputs read, the evidence bullet, row C-1 and Not checked.
- Codebase Nit 4 (G-2 :7-10): CONFIRMED by reading the patched header (lines 7-10, line 10 ends 'design only.'); fixed. Nit 5 (evidence log tests): CONFIRMED by reading A-01.patch (lines 165 and 175 call `write_outcome`); two evidence bullets corrected, marked as my reading, not evidence output. Nit 6 (C-3 :381-385): CONFIRMED (`_zero_price` runs 381-385, `model_copy` at 382); fixed. Nit 7 (diffstat): CONFIRMED and extended: evidence-13.md:105 says +37 and +55, patch hunks say 53 and 74 lines, `wc -l` of the patched files says 53 and 74; one bullet added; reason for the difference unknown, so the evidence may describe other versions of those two test files.

## What the studio head must decide (all in the file under 'Open for the studio head')
(5) and (4) X-6 and X-5: the shared login. (6) whether the proposal may be sent while it is shared. (8) notional price for self-hosted models. (9) the Major rating rule.

## Changes
REVIEW.md only (top restructured, rows C-3, C-6, C-7, A-2, A-3, A-4, G-1, G-2, D-1, X-2, X-4, X-5, X-6 edited, rows C-8 and the X-6 parts table and the DEAD-MAN-CHECK.md edit list added, Counts section and pasted output, Not checked, Open for the studio head, History and 'X-6 full working text' appended). Not committed.

# Round 17 (review-reader-r17.md and review-design-r17.md; log appended here)
Fixer run 2026-11-16. Backup before the edit: session scratchpad, file REVIEW.r17.bak. Edited only REVIEW.md and this log. The new REVIEW.md was produced by a script (cleaning plus hand-written sections); the removed process tags and old text are kept verbatim in its History section.
Checkpoint: the 20-minute checkpoint line was NOT written at 20 minutes (the context was compacted and the script was still being finished); this line is written at the end, 14:09 UTC.

## Unverified or not done (first)
- No test, lint, bandit or Postgres statement was run on any patch. Every Postgres statement in the X-6 parts stays UNVERIFIED. Nothing was applied to any patch or to DEAD-MAN-CHECK.md; the file only lists edits.
- The full-repository run is NOT green: 2 guard tests fail and block a pull request. They were not re-run after the files that quoted the forbidden string were replaced, so their current state is unknown.
- The claim of 13 new tests (+37/+55 versus +53/+74) is marked UNVERIFIED. The counts 41 and 14 (total 70) are UNVERIFIED (the codebase reviewer counted 39 and 4).
- No price-only patch exists for C-01, so "do not apply C-01 now" is stated and none was created.
- I did not re-read every row of the new file against the two reviews one by one. I checked only by a residual search (no "round N", reviewer ids, "CORRECTION OF MY ROUND", "Decision 21" outside History). Remaining hits: "queue item F2" (a real queue item name) and "ROUND 14 point 3" inside the X-6 map to the old paragraph labels (deliberate).
- The question for the lead about DECISIONS-2026-11-16.md line 5 is asked in the file, not answered.
- `tools/check_secrets.py` still reports 2 hits on files I did not touch (flow-check/evidence-f8-r8.md:55 and flow-check/raw/test-take-check.txt:177); not fixed here (outside my two files).

## Commands run from handover/flows-audit
- `python3 -I reviews-of-core-patches/count_review.py reviews-of-core-patches/REVIEW.md`: rc 0; rows 28; severity Nit 11, Major 5, Minor 12; decision DECLINE 3, PROPOSE FIX 25 (same text is pasted in the file's Counts section).
- `python3 tools/check_refs.py`: PASS 5167 references.
- `ruff check .`: All checks passed. `ruff format --check .`: 592 files already formatted.
- `python3 -I tools/check_secrets.py`: FAIL 2 hits (above, not mine).

## Changes
One severity scale and the hold sentence defined once at the top; rating rule applied evenly (3 live Major X-4, X-5, X-6; 2 conditional C-3, X-2); round numbers, reviewer ids and correction layers moved to History; X-5 split into X-5.1 to X-5.6 and X-6 parts mapped to the old paragraph labels; choices (4) and (5) split into 20 numbered decisions with cost of accepting and recommended default; DEAD-MAN-CHECK added to summary and index; edit-list pointers fixed; per-process secret scoping prerequisite and the purge_store precedent caveat added to X-6; project terms defined; one decider name (studio head).

## Round 18 (fixer, security and money path, no round cap; backup /tmp/REVIEW.md.r18.bak)
Inputs: reviews/review-reader-r18.md, review-design-r18.md, review-facts-r18.md (all three present; facts review fixed in the same round). Reviewer words were confirmed against source or evidence before editing where I could: blank-line counts (53-16=37, 74-19=55, read from the patched scratch tree), `evidence-guards-after-fix.md` (rc=0, "2 passed, 10551 deselected", `-k` selection), the file name `tests/test_review_pr3_round2.py`, `0002_audit_chain.sql:15-17`, `store/migrate.py` grants, `agent_loop.py:260-282`, `app.py:80-90,250-264`, `secrets_env.py`, `store/auth_aws.py`.

Not done or uncertain, first:
- Nothing was applied; no Postgres was run; every Postgres statement in REVIEW.md stays UNVERIFIED. The facts reviewer's "cannot check" items (git apply exit codes, commit ids) were not re-run by me.
- BLOCKED: rotation owner and date for each login secret (needs the studio head); breakglass, CI deploy and human identities need the studio head's decision whether ROLES-PROPOSAL.md is un-parked; G5-wording.patch not copied into the repository because its context lines carry a personal repository handle (studio head decides on a cleaned copy).
- `python3 -I tools/check_secrets.py` FAILS with 1 hit in `flow-check/evidence-f8-r8.md:55` (token-like, not in a file I edited; value not printed). Not fixed: not my file; needs the lead.
- Heavy lane `SUMMARY.md` line 31 is stale (says the guard tests were not re-run); I did not edit it (not my file). REVIEW.md now quotes the evidence file.
- A personal repository handle also remains in `G5-wording.patch` (in /tmp, outside the repository); it is not in REVIEW.md or `patch-copies/` (grep count 0).

Changes (all in REVIEW.md): old row letters replaced by X-5.n/X-6.n ids; hold sentence and Decision 1 with exact exit criteria and "Blocker-equivalent"; Decision 7 and summary: per-process secret scoping first, size large, owner split, real isolation via separate processes; C-3 one placement merged with C-7 (llm/common.py, llm/fake.py, Limits.charge); C-3 re-rated Minor so C-3, C-7, X-2 follow one rule (counts now 28 rows, 4 Major, 13 Minor, 11 Nit); one 'Not checked' list; guard tests quoted with the -k caveat; +37/+55 explained by blank lines; cite fixed to test_review_pr3_round2.py:321; new part X-6.8 (reading redaction_maps and tool_calls); HMAC against SHA-256 digest threat model in X-6.4; identity table gaps (exact rights list, credential lifetime, breakglass/CI/human, audit-writer departure); extra over-breadth checks; per-part ratings for X-5 and X-6; undefined terms and double-sense words defined; costs added to Decisions 9, 11, 13; round leftovers removed outside History; DEAD-MAN liveness sentence; SUMMARY option A conflict with DECISIONS item 11 noted; soft facts items (README.md:23-24 wording, 0002 columns, test counts 41 and 14) fixed; patch copies kept in `patch-copies/`.

Commands (from handover/flows-audit):
- `python3 -I reviews-of-core-patches/count_review.py reviews-of-core-patches/REVIEW.md`: rows 28; Nit 11, Minor 13, Major 4; DECLINE 3, PROPOSE FIX 25.
- `python3 tools/check_refs.py`: PASS 5166 references.
- `python3 -I tools/check_secrets.py`: FAIL 1 hit (not my file, above).
- `ruff check .`: All checks passed. `ruff format --check .`: 613 files already formatted.
