# fix-review3: round-3 fixes to REVIEW.md (2026-11-16)
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-rev3/REVIEW.md
Source of findings: ../reviews/design-core-patches-r3.md (reviewer words, unverified; each cite below was opened by me in src/hadavin_sdk with sed or grep before editing).

## What failed or is unverified (first)
- My own first edit script cut out the whole tables of REVIEW.md (it matched a phrase that also appears in the new Short answer text). I noticed it because count_review.py printed rows 0, restored the file from the backup and re-ran with a corrected anchor. Final file: 96 lines, 22 table rows.
- Patch files, patched tree and DEAD-MAN-CHECK.md are still not on disk: every patched-copy cite and all statements about the patches stay unchecked. No failing test for C-3 exists. The X-2 grants were read from the grant map, not tested against Postgres. X-3 case (b) (what the database raises exactly) was not run.
- I did not open the G-1 header quote (patched copy).
- Judgement call: A-6 downgraded Major to Minor (reviewer said "reword or Minor"); the lead may overrule.

## Findings and what I did
- M1 X-2: rewritten from migrate.py:46-68. Audit append = SELECT, INSERT on audit_entries (:57); outbox already SELECT, INSERT, DELETE (:59); INSERT is needed for write_outcome last resort (chain.py:223-227, called by tick.py:133,162); inline checkpoint writes audit_checkpoints (chain.py:203-204, 295-311; migrate.py:58); tick as a whole holds UPDATE on tick_state, runs, approval_requests (:56, :47, :50), so "no UPDATE anywhere" holds only for the new step's reconcile; purge_store precedent tick.py:196 and roles migrate.py:286-288; no new grant needed if the tick keeps the runtime role; negative test rewritten to match (does not deny UPDATE on the three tick tables; uses effective_problems migrate.py:193). Note: tick.py already has a step called "reconcile" (approvals, tick.py:85-97); the new one is audit_reconcile.
- M2 C-3: all price consumers added (limits.py:17-28, agent_loop.py:256-257, :325-326, :485-486, evals.py:80, k1b/loop.py:120-121 and :169-170, k1b/replay.py:166, llm/common.py:167-168, llm/fake.py:51-52); reason is the runtime caps never fire at price 0; negative price note (replay.py:87 tests == 0 only; Route accepts '-1'); conditional on the take's model program loading Route config.
- M3 A-6: reason corrected (chain.py:243 raises before the DELETE at :244, row stays, head-of-line blocking, loud via tick.py:315-324; local_dir.py:143-147 silent quarantine, event kept); downgraded to Minor. Short answer no longer says "quietly" for the stuck backlog.
- M4 counts: effective Major count recomputed under DECISIONS-2026-11-16.md line 5 (item 4): 1 (G-1) or 2 with C-3 if the take loads Route config; X-2, A-1..A-3, A-5 return with A-01; C-2 moot. Short answer C-01 line, A-01 line and counts paragraph fixed. Raw counts now: 22 rows, Major 8, Minor 4, Nit 10.
- load_config statement corrected against evidence-pydantic-nan.md PART 2 (NaN, Infinity, -Infinity run and refused; sNaN, '0', '-1' not run through load_config); unsaved Decimal claim dropped; "when I mutated" now attributed to the evidence runner (evidence-13.md:99).
- A-4: local_dir.py has no logging at all; write path :110-124, reconcile :126-156; chain.py:229 area bare append (cites src).
- C-5: config.py:453 blank, _read_yaml :446-452; :401 stays tagged patched copy.
- Header status line updated to round 3 applied, round 4 to follow. Stale first count block deleted. Heavy-lane heading now cites SUMMARY.md 09:30 written, 09:45 corrected.
- Siblings: A-1 caller list (demo audit.py:60 is a write_outcome caller; k1b/replay.py:185,198,260, cli.py:262,273,275 and demo audit.py:45,78 go through write_intent, which raises, so no quiet loss: stated as such, not added as lossy); X-3 now has both forms (double count after DuplicateEvent, and a UNIQUE-constraint error that _drain turns into False, chain.py:253).

## Commands and real output (run from handover/flows-audit)
`python3 -I reviews-of-core-patches/count_review.py reviews-of-core-patches/REVIEW.md`
```
rows 22 ['C-1', 'C-2', 'C-3', 'C-4', 'C-5', 'C-6', 'A-1', 'A-2', 'A-3', 'A-4', 'A-5', 'A-6', 'A-7', 'A-8', 'A-9', 'G-1', 'G-2', 'D-1', 'D-2', 'X-1', 'X-2', 'X-3']
severity {'Nit': 10, 'Major': 8, 'Minor': 4}
decision {'PROPOSE FIX': 20, 'DECLINE': 2}
```
`python3 -I tools/check_secrets.py` -> `PASS 0 hits in 1755 files` (rc 0)
`grep -c COUNTS_OUTPUT_PLACEHOLDER reviews-of-core-patches/REVIEW.md` -> `0`
`ruff check count_review.py` -> `All checks passed!` (rc 0); `ruff format --check count_review.py` -> `1 file already formatted` (rc 0)
Not committed.
