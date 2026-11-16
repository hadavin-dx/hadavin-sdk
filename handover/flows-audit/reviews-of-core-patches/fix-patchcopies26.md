# fix-patchcopies26 (twenty-fourth fixer pass on patch-copies/README.md and DEAD-MAN-CHECK.md; answers patch-copies-reader-r26.md)
Security path, no round cap. Static work: nothing was applied to a real repository; made-up data; no secret, baseline-tree commit id or personal handle written here. EGM: the lead runs the review of this result; the fixer did not review itself. Report time: 2026-11-16 about 20:35 UTC (02:05 IST on 2026-11-17).

## Not verified, not run, or open (first)
1. The recipe as one piece, real `uv`, real pytest and the real repository were NOT run (as before). The new proof check was run only on a made-up pytest log.
2. The failed-test names in `pwant` were derived from the test names in the patch files and the old list "The failures on old code". They were NEVER compared with a real pytest summary. If a real run prints other names the proof says PROOF FAILED and prints the difference: fail safe, but it may then be the list that is wrong, not the patch. UNVERIFIED.
3. `verdict_run` with its one new line (the second line of `verdict.stamp`) was NOT run as a whole (it needs a real patched clone). The same two lines were run in a scratch test in the form written in the test; `bash -n` passes on the real block.
4. Which git version first has `git patch-id --verbatim` is still UNVERIFIED; only 2.43.0 (the git on this machine) was seen to work. The setup now tries the command; the text says so in parts (1), (0c) and clause (e).
5. LEAD DECIDES (by 21:30Z (03:00 IST) on 2026-11-17 is not needed for this pass; before the first real run): whether to state a hard minimum git version. AUDIT PROPOSAL (default): keep the probe and the text "2.43.0 is the one version seen to work"; a throwaway machine with an older git (for example the one of an older long-term-support Linux) should try the probe once to find the real minimum, then the text is changed to that number.
6. The stamp and the fingerprints are a guard against slips and quiet edits; a person who edits a file AND recomputes the stamp by hand is not stopped (no secret key). The README now says so plainly (paragraph above `verdict`).

## Findings of the reader report and what was done
| Finding | Done | Where |
|---|---|---|
| Weak point 1: proof compared counts only | `pwant`, `pnames`, `pcheck` compare the exit code, the counts AND the failed test names (parameter ids cut off, counted per test function); a difference is printed (recorded left, seen right); `proof-failed.txt` is kept; `keep_logs` copies it | README proof block, pass rule, proof text |
| Weak point 2: stamp did not cover verdict.txt, proof.txt, proof.log | `verdict.stamp` line 2 = fingerprint of `verdict.txt` (`hf`, checked by `vs_ok` in `proof` and `final`); `proof.txt` line 2 = fingerprints of `proof.log` and `proof.rc`; `final` checks them and runs `pcheck` again from the log, not from the words of `proof.txt`; `verdict` also removes old proof files | README helper functions, verdict_run, proof, final |
| M1 four-row result table | a table under part (7) (PASSED, ADDS NO NEW FAILURE, NOT PASSED, no FINAL line) | README top |
| M2 git gate too low for clause (e) | probe `printf '' \| git patch-id --verbatim` in `setup` before the clone; minimum git stated in parts (1), START HERE (0c) and clause (e) | README setup block and text |
| M3 wall of text | short answer, "NOT YET RUN" and "START HERE" are bullets | README top |
| D9 contradiction | README decision row 8 now says job interval only; the tick period belongs to D2 | README row 8 |
| Stale "line 142 of the script" | now "the line of the script that starts `IFS=: read -r -a PDIRS`" | DMC settings text |
| Exit-code row for other 128 + n | new last row (137, 139, 132 to 136, 138, 140); START HERE line and fact 3 name it | DMC table, lines 3 and fact 3 |
| Settings-table pointer | pointer in row T1 and at the start of the job section | DMC |
| Pass-number gap | explained in the date paragraph: since round 23 the report number is a shared round counter, files 23 and 24 do not exist; pass 23 = report 25, pass 24 = report 26; the old sentence "numbered by the fix report files" now stops at pass 15 | README date paragraph and history |
| "FAILED" wording | warning now says the word in capitals (for example `(e) FAILED`, `GATES FAILED`, `PROOF FAILED`) or NOT PASSED | README warning |
| Two UTC/IST pairs | pass 21 "= 00:42 to 01:20 IST", pass 22 "= 00:55 to 01:15 IST" (2026-11-17) | README date paragraph |
| DMC 101-102 sample timestamps UTC only | left as the reader said acceptable (sample output lines, not times of events) | none |

## What was run (raw results summarised; scratch files under the session scratchpad, not in the repository)
- Backup of both files made first (scratchpad `bak/`).
- `bash -n` on all 12 fenced blocks of README.md after the edits: no output (all pass). DEAD-MAN-CHECK.md: its fenced blocks are byte-identical to the backup (python compare printed True), so no new shell was added there.
- Scratch functional test of `hf`, `vs_ok`, `pwant`, `pnames`, `pcheck`, `proof`, `final` taken from the edited README (fake `E` that prints a made-up pytest log; made-up git clones; made-up stamp). Results: good price-only run -> `PROOF OK`, `FINAL: VERDICT`; good C-01.patch run (13 failed, 19 passed) -> `FINAL: VERDICT`; twelve unrelated failures with the right counts -> difference printed, `PROOF FAILED`, `FINAL: NOT PASSED`; hand-edited verdict.txt before proof -> proof STOP; after proof -> `FINAL: NOT PASSED`; changed name in proof.log -> NOT PASSED; forged proof.txt -> NOT PASSED; 12-count log with C-01.patch -> PROOF FAILED; one-line stamp -> STOP; changed patched.log -> STOP.
- The `setup` probe line alone: real git 2.43.0 -> passes (rc 0); a stub git that refuses `patch-id` -> prints the STOP line (rc 1).
- `sha256sum patch-copies/*.patch` prefixes: 64fdf315, e7ff677e, ca4982eb (unchanged).
- `python3 -I tools/check_refs.py` PASS 5190 references; `check_names.py` PASS 655 rows; `check_secrets.py` PASS 0 hits in 2998 files (run before this report was written; re-run after, see below); `check_counts.py` PASS 52 files / 655 nodes; `ruff format --check .` 1123 files already formatted.

## Test honesty
The scratch tests do not prove the real recipe works. They show the new comparison logic refuses the cases above and accepts the two good cases. New tests were not run against the old code form of `final` (the old form is gone from the file); the old text is in the backup, and by reading it the old `final` would have printed a result for the "twelve unrelated failures" and the "hand-edited verdict.txt" cases (that is the reader's finding, not a run).

## Files changed
`handover/flows-audit/reviews-of-core-patches/patch-copies/README.md`, `.../DEAD-MAN-CHECK.md`, this report. No commit, no push. No agent, shell or container left running.
R-numbers: the studio bible was not available in this checkout; the preamble rules 5, 6, 11 and 13 (fix, honesty, least privilege, EGM) were followed as written; no bible R-number was looked up (not checked).
