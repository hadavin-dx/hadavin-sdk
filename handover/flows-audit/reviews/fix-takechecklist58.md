# Fix report: TAKE-CHECKLIST.md, reviews r56 and r58

Only TAKE-CHECKLIST.md was edited (plus this report, the changelog and the checkpoint). Not committed or pushed. No heavy runs.

## Not fixed or not checked (first)
- Clock block (lines 32-79) must stay byte-identical with FIX-PLAN.md lines 37-84 (md5 dfd844ddb7085082534434075814e131, verified at the end). So these r56/r58 points that sit inside it are NOT fixed here and need a FIX-PLAN change by the lead: the "about 11:00Z" message 2, the "146 min" line, lead slot 08:00-09:30Z against step 16 at 08:29Z, the HubSpot row inside the block, and a few leftover round tags in the block.
- The Block R4/R4f "1 or 2" count needs a first real run (impossible now, exception 2(a)).
- Pass lines that depend on tools that do not exist yet stay LEAD FILLS and are marked NO PASS POSSIBLE UNTIL FILLED: the mailbox count command, the HubSpot search, the post-twice script, the `result.json` key name.
- The `ledger_check.py` output format is unknown, so the `ids-accounted` check in R6 is a superset check. Not tested against real output.
- Minor "message 1 contact counts 9/8/7/6 vs 9/8" in r58: not changed (not enough evidence which is right).
- r58 "Smaller" point on R3n: reviewer false positive (R3n uses JUDGE_WHO); no change.
- Edited blocks were read for shell sanity but NOT executed.

## Fixed
- r56 B1, B2 and M3-M15; r58 M1-M9: fixed in the checklist as follows.
  - Supplier words: five words defined once (LEAD FILLS, KEYSAVE, SKELETON, MADE BY COMMAND, LEAD DECIDES); one supplier per placeholder; example rows marked "made by keysave, never typed".
  - Case A / Case B and dated vs gated times defined at the one-page table; gated times added to rows 3-11; new row 1a (F-002 rule check 07:30Z).
  - Pass lines self-checking with PASS/FAIL words, shell-tested numbers, per-run log files, key printed: Check 2 (a)-(d), Check 4 (a)/(b), R5f, R6, R8 (typed DECISION, one decision line), check 13, check 8.
  - No pipes in table cells (rows 8-24 checked: 8 fields each); `tee -a` pipe in row 3 (e) replaced.
  - R3n unset of stale variables; R4 guard list; `mail-count N` format unified with RUNBOOK; ceiling unified (standing yes up to 3 live calls, stop at the fourth).
  - Round history moved to reviews/take-checklist-changelog.md.

## LEAD DECIDES (written in the checklist in the required form)
T19H (AUDIT PROPOSAL yes, by Tue 04:00Z); HubSpot ceiling; one or two rehearsals (proposal two); F-002 rule entries; row 6 margin (proposal 35 s); JUDGE_WHO; Case B recording-ready; item 24.

## Tool results (last lines)
- check_refs: PASS 5190 references
- check_names: PASS 655 rows
- check_secrets: PASS 0 hits in 2969 files
- check_counts: PASS 52 files / 655 nodes
- ruff format --check .: 1094 files already formatted
- check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md: RESULT: PASS
- clock block md5 of TAKE-CHECKLIST lines 32-79 and FIX-PLAN lines 37-84: both dfd844ddb7085082534434075814e131

## Slip admitted
A late tag-removal pass also changed the clock block; I noticed from the md5 mismatch and restored the block from FIX-PLAN.md; md5 equal again.
