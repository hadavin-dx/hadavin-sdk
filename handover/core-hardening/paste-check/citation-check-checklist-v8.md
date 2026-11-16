# Citation check of LEAD-CHECKLIST-v5.md and LEAD-FILL-list-v5.md (2026-11-16)
Role: citation checker. Nothing was fixed or edited except this file. No commit. Read-only tools: sha256sum, grep (-c, -o, -n, -F), sed, cmp, diff, patch and git apply on COPIES made in the scratchpad folder (the real `inputs/` file was never changed). Method: I rebuilt the patched plan myself (`plan-v5-fixes.patch`, then `plan-v5-repin-v6.patch`, `patch -p1`, both `rc=0`) and read every cited count, line number and command against that copy and against the real files.

## FAILURES (2 wrong or overstated, 1 imprecise)
| cite | claimed | actual | verdict |
|---|---|---|---|
| LEAD-CHECKLIST-v5.md A (line 9): "Do not use `plan-v5-repin-v5.patch` or older (v1 to v4): they are replaced and fail or give wrong counts" | all older repin patches fail or give wrong counts | After `plan-v5-fixes.patch`: `plan-v5-repin.patch` gives counts 4/0/2/0 (wrong, true); `-v2` gives 24/0/2/1 (wrong, true); but `-v3`, `-v4` and `-v5` APPLY CLEANLY (rc 0) and print the right four counts 24/10/2/1. Their result differs from the v6 result (55, 53 and 28 differing lines). So for v3 to v5 the A6 counts do NOT detect a wrong patch | WRONG (the warning is right to say "do not use"; the reason "fail or give wrong counts" is false for v3, v4, v5. The four counts cannot tell you that an old patch was used) |
| LEAD-CHECKLIST-v5.md line 2: "Every command below was copied by a script from the patched plan, not retyped" | all commands come from the plan | Only these blocks are verbatim substrings of the patched plan: B1 grep (line 69), C1 (75), C4 (92), C5 (97), C7 (106), C8 (110). C6 contains the C5 text exactly (790 characters) inside a wrapper that the plan does not hold. 21 of the 27 bash blocks are NOT in the plan: A1, A2, A3, A4, A5 (two blocks), A6, A7, A8, A9 (two), C2b (two), C6 wrapper, C9, D1, D2 (four). `acc5.sh` is named 0 times in the plan | OVERSTATED (the ready blocks are checklist text; they were tested in evidence-c7g.md sections 11 to 14, not copied from the plan) |
| LEAD-CHECKLIST-v5.md D2 (4): the two messages to the runner (`P-4b STOP is cleared: run P-3b, then P-4b, then P-5. Do not repeat P-1 or P-2.` and `Fresh start: restart at P-1; the RE-PIN step (e) counts run first, as the plan says.`) "The plan (P-4b step) names the same two ways" | same two ways in plan line 258 | Meaning matches (plan line 258: resume with P-3b, P-4b, P-5, P-1 not repeated; or lead deletes `$HOME/hadavin-smoke` folder and restarts at P-1). The exact message texts occur 0 times in the plan | OK for meaning, text not in plan (not a failure, noted so nobody searches the plan for the sentence) |

## All other cites (OK)
| cite | claimed | actual | OK/WRONG |
|---|---|---|---|
| A2 sha256 of `inputs/plan-wp6-resmoke-v5.md`, first 16 characters | `67a0a195537de875` | `67a0a195537de875` | OK |
| A2 CR count of plan copy and of both patches | `0` | `0`, `0`, `0` | OK |
| A3 / A4 `patch -p1 --dry-run` then real, both patches in order | `rc=0` each | `rc=0` x4 | OK |
| A5 `git apply -p1 --check` and apply, both patches | same result as `patch` | `rc=0` both; result `cmp` identical to the `patch` result | OK |
| Patch order (A, line 9): v6 on the unpatched plan | fails | `patch --dry-run` rc=1 | OK |
| A6 / LEAD-FILL-list line 2 counts: `<FINAL[-]` | 24 | 24 | OK |
| A6 `LEAD-FILL [0-9]` lines | 10 | 10 | OK |
| A6 HEAD_PIN control lines | 2 | 2 (plan lines 2 and 251) | OK |
| A6 patch-marker lines | 1 | 1 (plan line 3) | OK |
| B (line 67) and list line 2: "17 markers on 10 lines" | 17 on 10 | 17 markers (`grep -o`), 10 lines: 2, 3, 4, 125, 258, 275, 433, 434, 585, 586 | OK |
| List table, marker places Q1 | 258; 586 | 258 (LEAD-FILL 1); 586 (UNVERIFIED 15) | OK |
| Q1b | 258 (two places) | 258, twice | OK |
| Q2 | 258 | 258 (once) | OK |
| Q3 "4 WORDS" | line 4 | line 4 holds `LEAD-FILL 3` (the WORDS paragraph) | OK |
| Q4 | 125; 433 (13.1); 434 (13.3) | 125 (R2 exit 3); 433 is 13.1; 434 is 13.3 | OK |
| Q5 | "3 RE-PIN" | line 3, once | OK |
| Q6 | 3; 275 (0.1) | line 3 and line 275 | OK |
| Q7 | 2 header; 3; 585 UNVERIFIED 14 | lines 2, 3, 585 (item 14) | OK |
| Q8 "4 WORDS" | line 4 | line 4 | OK |
| Q9 | 3 | line 3 | OK |
| List: "ten questions (1, 1b, 2 to 9)" | 10 | 10 distinct (1, 1b, 2 to 9) | OK |
| A9: Windows-form path string (1) | found 1 time, line 3 | 1 time, line 3 | OK |
| A9: `PF=<path>;` strings (2) and (3) | found 2 times, line 3 | 2 times, both on line 3 | OK |
| A9 flip target | `LEAD-FILL 9` on the RE-PIN line (line 3) | line 3 only | OK |
| Plan section 11 table: 20 cells with `<FINAL-LINES>` | 20 (C4 "20 rows") | 20 occurrences, lines 538 to 557, one per line | OK |
| Plan line 536 header holds `<FINAL-SHA-7>` | yes | yes | OK |
| Plan first line of P-2 block starts `$HEAD_PIN =` | yes | line 251 | OK |
| "four places" (1) HEAD_PIN line, (2) section 2 `code` row, (3) P-2 line, (4) section 11 | four | lines 2, 136, 251, 536 to 557 | OK |
| C1 / C4 fill command | identical to the plan | verbatim substring of plan (1059 characters) | OK |
| C5 wording-diff command | identical to the plan | verbatim substring (790 characters) | OK |
| C7 last check, four numbers `0`, `0`, `2`, `1` | after fill | the command is verbatim in the plan; on the PATCHED UNFILLED plan it gives 24, 10, 2, 1 (as the plan says); the filled result `0 0 2 1` was NOT run by me (no filled copy exists) | OK (command text); filled result not run, see list below |
| C8 `grep -n -o -E 'nlite-fix5\|nlite-int-r5'` | verbatim in plan | verbatim; 10 lines in the patched plan hold one of the two names | OK |
| C9 / plan (e): release pattern `^LEAD-GO RE-PIN( \|$)` | in plan | present in plan line 3 | OK |
| D1 / plan: `NEED-LEAD R2 pid=<digits>` and `LEAD-YES R2 pid=` | in plan | both present (2 and 6 times) | OK |
| Plan: `CR-FIX strings.txt` message | in plan | 1 time | OK |
| Plan P-3b control line shape `^P-4b-HIT pid=[0-9]+$`, first line `P-4b.sh sha256` | in plan | 2 and 2 times | OK |
| List Q4: after `kill exit=3`: 13.4 and 13.5 run, 13.6 to 13.9 only if none alive | plan 13.1 (line 433) | plan line 433 says exactly that | OK |
| List Q2 / checklist D2: fresh start deletes the smoke folder, restart at P-1, P-1 not repeated otherwise | plan P-4b (line 258) | line 258 says so | OK |
| `acc5.sh` exists; checklist C6 "applies the same rule" | exit 2/3 kinds, `sys.exit(main())`, comment lines, `return 3` only in the kill block | `acc5.sh` read; rule matches plan; `bash acc5-cases.sh` printed `cases ok=18 bad=0` | OK |
| Checklist C6 block contains C5 block unchanged | yes | exact (790 characters) | OK |
| evidence-c7g.md section 9 = P-4b proposal tests | list last paragraph | heading "## 9 P-4b proposal ..." | OK |
| evidence-c7g.md section 13 = cygpath stand-in test (A9) | "evidence section 13" | 13.4 text, line 632 | OK |
| List: stand-in one-line test expected values (as user 65534: folder owned by user, environ `0`, `Permission denied`) | tested | evidence-c7g.md lines 457 to 461 show `me=65534`, `65534 /proc/<pid>`, `status-uid=65534`, `Permission denied` | OK |
| Checklist: tested "on a Linux container" | Linux container | `uname -r` here 6.18.44; evidence says kernel 6.18 | OK |
| Evidence: checklist had 27 bash blocks (14.2) | 27 | my count of fenced `bash` blocks in the checklist: 27 | OK |

## NOT checked (said plainly)
- Nothing was run in Git Bash, PowerShell or WSL; the checklist says the same of itself and I did not contradict it.
- The filled-plan result `0 0 2 1` (C7): there is no filled copy; the placeholders need the lead's commit, which does not exist yet.
- The 20 rows printed by C1/C4 at a real commit: the worktree `nlite-fix5`, `strings.txt` and the n8n scripts are not in this tree.
- Windows paths (`C:/Users/...`) and the guessed evidence folder: not checkable here; the plan itself says they are guesses.
- Whether `eec6ba4` exists in any worktree (plan UNVERIFIED 14).
- Raw sha256 values written in `evidence-c7g.md` for the three patches beyond one line (line 541: `plan-v5-repin-v6.patch` begins `8a83abaa5c10db10`, matches my `sha256sum`); `plan-v5-fixes.patch` starts `9e8d06ddb5bb5b57` here, I did not find a line in evidence that cites it by name in the 54 lines I read.
- The words and claims inside REPORT-repin-v6.md and the review files (out of scope).
- Wording claims ("the plan is right and this file is wrong") are rules, not citations.

Rules cited from the studio preamble: 1 (read first, bible R-numbers not looked up: this is a citation check, no bible rule was used), 5, 6, 12. Files changed: only this one. Head SHA: none (not a git repository).
