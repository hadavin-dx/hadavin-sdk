# Round 32 fix report: RUNBOOK, FIX-PLAN, TAKE-CHECKLIST

Fixer: one fixer, round 32. Input: `reviews/plan-files-reader-r31.md` (0 Blockers, 10 Majors) and the check 13 changes from `reviews/fix-findings-ledger16.md`. Edited only RUNBOOK.md, FIX-PLAN.md, TAKE-CHECKLIST.md. Nothing committed.

## Failures and uncertainty first

1. No fresh reviewer has read these edits. Every verdict below is my own, so it counts as unverified.
2. Every new or changed command is mine and was never run. I did not run any of them on the real tree. The only shell check I ran is `bash -n` (syntax only) on the commands in the three files. It does not show that a command does the right thing.
3. `bash -n` result: 227 backtick command spans plus 2 fenced blocks checked. 6 spans report a syntax error. All 6 are descriptive templates (they end in `&&`, contain `...` or a placeholder like `NAME ...`), not commands a reader types as they stand. I did not rewrite them. If the lead wants them to parse, that is a small follow-up.
4. Finding 10, Block R2j: the block cannot prove that each hit is closed. I kept it as a recorded judgement (Form 2, via `stepjudge`) and did not change it. That is a partial answer to the finding.
5. Finding 6: most of the conflict was answer-by time versus first-use time, and I fixed that with the one-time-per-input rule. One real conflict stays open (Q31 text 1 below).
6. TAKE-CHECKLIST check 7: I dropped the third command (the `awk` digit count) because it needed a vertical bar. The "sentence has no digit" test is now done by reading the sentence. That is a weaker check. The first command still fails when the sentence is missing.
7. Not fixed because they are not Majors: Clock case 4 (04:50Z versus 04:56Z) and the F-028 "Total" 20 versus 18. Not touched.
8. One literal `\|` is left in TAKE-CHECKLIST line 202 (check 6 prose, `yes\|no`). It is a description of answer values, not a command a reader types.

## Finding to result

| Finding | Result |
|---|---|
| 1 RUNBOOK step 1 unguarded git | Three guarded chains print `same-toplevel`, `on-patch-branch`, `is-ancestor-ok`. Pass cell and step 4 text updated. |
| 2 Step 17 (3) unguarded and weak | Commands guarded with positive echoes. (2) review grep has a `grep exit` line. (6a) has a positive `done` count. Block R1 prose has no pipe. |
| 3 Step 13 (a)(b)(c)(e)(f) | All guarded. (b) `cat` is inside the `if`. (f) has two guarded greps. Pass cell updated. |
| 4 Step 8 (v) old INSERTLOG | One chain prints `insert exit N`, the count of the refusal wording, and `grep exit`. Failure cell updated. (0b) uses `grep -c -e ... -e ...`. |
| 5 Step 6 TAKE_TREE and SRC_TAKE | Guarded `sha256sum`, `bash -n` requires a folder that is not a git work tree, SHA_SCRIPTS chain checks both files exist, are tracked, and match their copies (`cmp -s`). |
| 6 Same input, different due times | Rule written once in TAKE-CHECKLIST "Needed by": each input has an answer-by time (its Q31 item) and a first-use time. Items 1/2, 18, 24 aligned. False Block R3 claim removed. SHA_R20-23 and JUDGE_WHO answer-by times added in the skeleton. One conflict left open: Q31 text 1. |
| 7 Three due times for HubSpot permission answer | One time everywhere: default Wed 08:00Z (13:30 IST), with the conditional Tue 05:54Z (11:24 IST) if decided by Mon 21:00Z (Tue 02:30 IST). Step 16 / I21 and TAKE-CHECKLIST item 20 aligned. Open choice: Q31 text 2. |
| 8 Ambiguous step numbers | FIX-PLAN mapping rewritten as "FIX-PLAN Step N = RUNBOOK step M". Added the label "FIX-PLAN item N" for the numbered BEFORE THE VIDEO list to the Words boxes. Bare step numbers labelled in FIX-PLAN lines 67, 68, 70. |
| 9 Pipes in cells, `git add FILE1 FILE2` | Commits of more than two files now use `FILES=( ... )`, `test "${#FILES[@]}" -ge 1`, `git add -- "${FILES[@]}"`, `git commit ... -- "${FILES[@]}"`, `echo text-fixes-committed` (step 4a and step 14 (g)). Step 4b, 5, 7, 12, 18 (1b), 26 and FIX-PLAN item 7 are pipe-free guarded chains. TAKE-CHECKLIST checks 2 and 7 converted from `( ... || exit 1; ... )` groups and `-E "a|b"` patterns to `&&` chains, `if/else` and `grep -e A -e B`; each check 2 command now ends in its own pass word (`psql-a-ok` to `psql-d-ok`, `table-file-run`). |
| 10 Steps 16 and 17 count and grep guards | Positive counts and `grep exit` lines added. R2j kept as Form 2 (see failure 4). |
| Check 13 changes (ledger16) | Checked against F-007 and F-031 cells of FINDINGS.md; all four confirmed and applied (parts 0, 1, 2 plus control, 3, 3b, and the allowed-hit sentence aligned to FINDINGS). |

## Proposed Q31 texts (QUESTIONS.md is not mine; for the lead)

1. SHA_R20-23 and step 1. "Do the four values SHA_R20 to SHA_R23 block RUNBOOK step 1? Q31 item 38 (b) default says step 1 waits for them and the answer is NO-GO if they are missing by Tue 03:30Z (09:00 IST). The RUNBOOK skeleton and I48 now say due Tue 03:30Z but do not call it a step 1 blocker. Default if no answer: step 1 does not wait; the values are first used at the later step named in the skeleton. Lead: confirm or change Q31 item 38 (b)." The Clock block is silent on this, so I did not decide it.
2. HubSpot permission timing (Q31 items 27 and 30). "Default: the answer is due Wed 08:00Z (13:30 IST). If you decide by Mon 21:00Z (Tue 02:30 IST), the earlier time Tue 05:54Z (11:24 IST) applies. Which do you choose?"

## Raw outputs (run from handover/flows-audit)

```
python3 -I tools/check_refs.py      PASS 5177 references
python3 -I tools/check_names.py     PASS 655 rows
python3 -I tools/check_secrets.py   PASS 0 hits in 2715 files
python3 -I tools/check_counts.py    PASS 52 files / 655 nodes
ruff format --check .               863 files already formatted
diff Clock block (FIX-PLAN 14-47 vs TAKE-CHECKLIST 8-41)          empty
diff Who-is-needed block (FIX-PLAN 49-61 vs TAKE-CHECKLIST 43-55) empty
bash -n on checks 2 and 7 command spans: 9 spans, 0 bad
bash -n on all three files: 227 spans, 6 reported (descriptive templates, see failure 3); 2 RUNBOOK fenced blocks, 0 bad
pipe inside a backtick span in a table row: RUNBOOK 0, FIX-PLAN 0, TAKE-CHECKLIST 1 (the escaped prose in line 202)
```

Not run: any real-tree command, any test of the commands' behaviour, any fresh reviewer pass.
