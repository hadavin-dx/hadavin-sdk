# EVIDENCE RUNNER: evidence-chain-r3 (raw output, no judgement)
Run date 2026-11-16 (about 11:35 to 11:45 UTC). Independent repeat of Part G of `evidence-chain-r1.md`. GNU patch on Linux, `python3 -I`, all work on scratch copies in the session scratchpad (`<scratch>`). The original input `inputs/plan-wp6-resmoke-v5.md` was only copied; its sha256 stayed `67a0a195537de8754ef80bd3bd8d8a4d78a507ca8418bec8f835a0e99abb41f1`. The chained plan `515cf470...` also stayed unchanged after all hostile runs.

## Read first: failures, differences, what I did not run
1. **No case failed against its expectation.** All 17 cases of the test script match the Part G text; all 9 hostile cases behaved as a safe tool should (refuse, or write the expected sha).
2. **Stale expected checksum in the checklist (already known, still present):** `LEAD-CHECKLIST-v5.md` line 64 still names `b0caeb84c5a28a94` for CHAIN=4; the real result is `28f92c5d1211207c`. `PLAN-CHAIN.md` line 66 already says so; I did not edit the checklist (edit only this file). So running the checklist as written with CHAIN=4 would print STOP.
3. **Hostile case 8 (read-only folder) is only half tested.** I ran as uid 0 (root): `chmod 555` does not stop root, so the script WROTE into the "read-only" folder (rc 0). Not a script fault; this test does not show the permission refusal. A second try with `chattr +i` on the folder gave a clean refusal (`cannot create output exclusively ... Operation not permitted`, rc 1, nothing created). A non-root permission-denied run was not done.
4. **Edits file with CRLF is accepted, not refused (cases 4 and 4b):** Python text mode turns CRLF into LF when it reads the edit files, so the result is byte-identical (`28f92c5d`). Harmless here (same sha), but the script does not detect a CRLF edits file. A single stray CR inside an old text is refused (edit 3 found 0 times, rc 1).
5. Flake claim: the numbers match (details in part 4), but the cited log `sibling-clean-allids-OLD.log` holds only 4 lines: three sample `bad` lines (all prefix `run`, ids `ec2a`, `ec2b`, `ec2c`) and the total line `clean() ids 262144 bad 24`. The "4 prefixes x 6 values" split is NOT visible in that log (the script `sib.py` prints only the first 3 bad ids). I therefore re-ran `sib.py` myself (part 4): same total 24.
6. Not run: the plan itself or any paste in it, n8n, Git Bash, `git apply`, `patch --fuzz=0` (step 3 patch needed fuzz 2 on hunk 1, rc 0; the build still gave the expected sha), the 200,000-iteration flake loop, the full pytest suite, the fix patch `FIX-id-vs-command-withheld.patch`, mutation runs, a non-root read-only test. Two untracked-looking files in the repo that I did not create: five `*.whl` files in the repo root (mtime 11:30 UTC, before my first command) and other files under core-hardening (ORDERS.md, STATUS-BOARD.md, mutation-lane/run.py and a checkpoint note) changed during my run (not by me).

## Part 1: chain rebuild (three patches with GNU patch, then the script)
Counts column = checklist line 64 greps (`<FINAL[-]`, `LEAD-FILL [0-9]`, `^**HEAD_PIN = |^$HEAD_PIN = ` lines, `RE-PIN (lead only). FOUR places hold` line), expected `24 10 2 1` from step 2 on.
| step | expected sha256 (first 16) | actual sha256 (first 16) | expected lines | actual lines | counts expected | counts actual | match |
|---|---|---|---|---|---|---|---|
| 0 original | 67a0a195537de875 | 67a0a195537de875 | 558 | 558 | 0 0 2 0 | 0 0 2 0 | yes |
| 1 plan-v5-fixes.patch (dry rc 0, apply rc 0) | 53f1670383a2c728 | 53f1670383a2c728 | 561 | 561 | 0 0 2 0 | 0 0 2 0 | yes |
| 2 plan-v5-repin-v6.patch (dry rc 0, apply rc 0) | 39af84aec78b650f | 39af84aec78b650f | 587 | 587 | 24 10 2 1 | 24 10 2 1 | yes |
| 3 plan-v5-gate-rows-v3.patch (dry rc 0, apply rc 0, hunk 1 fuzz 2) | 515cf4704ebba5bd | 515cf4704ebba5bd | 622 | 622 | 24 10 2 1 | 24 10 2 1 | yes |
| 4 apply-v10-after-chain.py (rc 0; 29 old edits; corrected/added 2,4,5,18,19,20,21,29,30; failing []) | 28f92c5d1211207cce0222c87bb7a6e6dc8e39a21a659624a1a7fe9cc32992ce | 28f92c5d1211207cce0222c87bb7a6e6dc8e39a21a659624a1a7fe9cc32992ce | 780 | 780 | 24 10 2 1 | 24 10 2 1 | yes |
Full sha256 at steps 1 to 3 (from my own `sha256sum`): 53f1670383a2c728c4bdbb560f5444766aa0df773ac6f85a4c6496aca1bb1c2a, 39af84aec78b650f287d20013cdfa2d45dde8b75632e6d6729660bbc21ce3f5b, 515cf4704ebba5bdc00e3c2ab9fdce7f65a2a7b8467ceec0bf0942b7e21a7e45. Step 4 has no CR (`grep -c $'\r'` = 0). A looser grep (plain count of `HEAD_PIN` and `RE-PIN` strings) gave 13 and 19 at steps 2 to 4; those are not the checklist command and are not the numbers to compare.

## Part 2: marker lines at CHAIN=4 (`grep -n -o 'LEAD-FILL [0-9][0-9a-z]*' step4.md`)
| expected (builder) | actual | match |
|---|---|---|
| 17 markers | 17 | yes |
| 10 lines: 2, 3, 4, 137, 270, 287, 509, 510, 774, 775 | 10 distinct lines: 2 3 4 137 270 287 509 510 774 775 | yes |
Raw: `2:LEAD-FILL 7 3:LEAD-FILL 5 3:LEAD-FILL 6 3:LEAD-FILL 9 3:LEAD-FILL 7 4:LEAD-FILL 8 4:LEAD-FILL 3 137:LEAD-FILL 4 270:LEAD-FILL 1 270:LEAD-FILL 1b 270:LEAD-FILL 2 270:LEAD-FILL 1b 287:LEAD-FILL 6 509:LEAD-FILL 4 510:LEAD-FILL 4 774:LEAD-FILL 7 775:LEAD-FILL 1`

## Part 3a: the 17 cases of `test-apply-v10-after-chain.sh` (run on my step-3 plan, sha 515cf470...)
Command: `bash test-apply-v10-after-chain.sh <my step 3 plan>`. Expected = the "must refuse / expected sha" labels in the script and Part G of r1. Raw output follows, then the table.
```
515cf4704ebba5bd
## T1 good input
29 old edits; corrected or added: ['2', '4', '5', '18', '19', '20', '21', '29', '30']
failing []
written <scratch>/tmp.Nalsza9AFM/out1.md 28f92c5d1211207c 780 lines
rc=0 out_exists=yes sha=28f92c5d1211207c
T1 full sha equals expected: YES lines=780
## T2 wrong input sha (one byte appended)
REFUSED: input sha256 is a908e9862ea369c9, expected 515cf4704ebba5bd (the plan after fixes, repin-v6 and gate-rows-v3)
rc=1 out_exists=no
## T3 wrong input: only the first 100 lines of the chained plan
REFUSED: input sha256 is 82dbe0f86a00b3a2, expected 515cf4704ebba5bd (the plan after fixes, repin-v6 and gate-rows-v3)
rc=1 out_exists=no
## T4 equal paths
REFUSED: input and output are the same path
rc=1 sha_after=515cf4704ebba5bd
## T5 same file by another name (symlink)
REFUSED: input and output are the same path
rc=1 sha_after=515cf4704ebba5bd
## T6 output already exists
REFUSED: output path already exists or is a symlink (this script never overwrites and never follows a link)
rc=1 content=keep
## T7 failed edit (old text of edit 3 damaged in a scratch copy of the edit list)
damaged edit 3 old text
REFUSED: 1 edit(s) did not find their old text exactly once; nothing written
29 old edits; corrected or added: ['2', '4', '5', '18', '19', '20', '21', '29', '30']
failing [('3', 0)]
rc=1 out_exists=no
## T8 missing output folder
REFUSED: output folder does not exist
rc=1
## T9 wrong argument count
REFUSED: usage: apply-v10-after-chain.py <chained plan> <new output file>
rc=1
## T10 RENUMBER line deleted (must refuse)
REFUSED: corrections file must hold exactly one RENUMBER line, found 0
rc=1 out_exists=no sha=
## T11 shift=0 (must refuse: edits 8, 13, 27 would not change)
REFUSED: RENUMBER changed nothing in edit(s) ['8', '13', '27'] (shift 0 or from/to range wrong); nothing written
29 old edits; corrected or added: ['2', '4', '5', '18', '19', '20', '21', '29', '30']
failing []
rc=1 out_exists=no sha=
## T12 'shift = 4' with spaces (malformed, must refuse)
REFUSED: RENUMBER line is malformed: 'RENUMBER edits=8,13,27 from=13 to=16 shift = 4'
rc=1 out_exists=no sha=
## T13 shift=4 text with a non-integer shift=x (must refuse)
REFUSED: RENUMBER line is malformed: 'RENUMBER edits=8,13,27 from=13 to=16 shift=x'
rc=1 out_exists=no sha=
## T14 to=15 (decision: accepted, item 16 is not referenced by edits 8, 13, 27, so the sha must stay 28f92c5d)
29 old edits; corrected or added: ['2', '4', '5', '18', '19', '20', '21', '29', '30']
failing []
written <scratch>/tmp.Nalsza9AFM/rn-to15/out.md 28f92c5d1211207c 780 lines
rc=0 out_exists=yes sha=28f92c5d1211207c
## T15 shift=4 but edit list reduced to 8,13 (must refuse: 27 missing)
REFUSED: RENUMBER must list edits 8, 13 and 27
rc=1 out_exists=no sha=
## T16 dangling symlink as output (must refuse, nothing created at the target)
REFUSED: output path already exists or is a symlink (this script never overwrites and never follows a link)
rc=1 target_exists=no
## T17 symlink to an existing file as output (must refuse, file untouched)
REFUSED: output path already exists or is a symlink (this script never overwrites and never follows a link)
rc=1 content=keep2
scratch folder: <scratch>/tmp.Nalsza9AFM (left in place; nothing in the repository was changed)
```
| case | expected | actual | match |
|---|---|---|---|
| T1 good input | rc 0, sha 28f92c5d..., 780 lines | rc 0, sha 28f92c5d1211207c, 780, "equals expected: YES" | yes |
| T2 one byte appended | refuse, no output | REFUSED sha a908e986..., rc 1, no file | yes |
| T3 first 100 lines | refuse, no output | REFUSED sha 82dbe0f8..., rc 1, no file | yes |
| T4 equal paths | refuse, input unchanged | REFUSED, rc 1, sha 515cf470 | yes |
| T5 symlink to input | refuse, input unchanged | REFUSED, rc 1, sha 515cf470 | yes |
| T6 output exists | refuse, content kept | REFUSED, rc 1, content `keep` | yes |
| T7 damaged edit 3 | refuse, no output | failing [('3', 0)], rc 1, no file | yes |
| T8 missing output folder | refuse | REFUSED, rc 1 | yes |
| T9 wrong argument count | refuse | REFUSED usage, rc 1 | yes |
| T10 RENUMBER deleted | refuse | found 0, rc 1, no file | yes |
| T11 shift=0 | refuse | changed nothing in 8, 13, 27, rc 1, no file | yes |
| T12 `shift = 4` | refuse | malformed, rc 1, no file | yes |
| T13 `shift=x` | refuse | malformed, rc 1, no file | yes |
| T14 to=15 | accepted, sha 28f92c5d | rc 0, sha 28f92c5d1211207c, 780 lines | yes |
| T15 edits 8,13 only | refuse | must list 8, 13 and 27, rc 1 | yes |
| T16 dangling symlink output | refuse, no target created | REFUSED, rc 1, target_exists=no | yes |
| T17 symlink to existing file | refuse, file untouched | REFUSED, rc 1, content keep2 | yes |

## Part 3b: my own hostile inputs (not in the 17)
Each case ran on its own scratch copy of the script folder (script, edit list, corrections file), input = my step 3 plan unless stated.
| case | expected | actual | match |
|---|---|---|---|
| H1 output in a missing nested folder (`.../nodir/x/out.md`) | refuse, nothing created | `REFUSED: output folder does not exist`, rc 1, folder `nodir` not created | yes |
| H2 output path = the edits file (sha 3b9e12ac... before and after) | refuse, edits file unchanged | `REFUSED: output path already exists...`, rc 1, sha unchanged | yes |
| H2b output path = the corrections file | refuse | same refusal, rc 1 | yes |
| H3 input with CRLF line endings | refuse (sha differs), no output | `REFUSED: input sha256 is 1be0aaf1...`, rc 1, no file | yes |
| H4 edits file with CRLF on every line | (no expectation fixed; a safe tool refuses or gives the same sha) | accepted, rc 0, sha 28f92c5d1211207c, 780 lines (Python text mode folds CRLF to LF) | see note 4 |
| H4b corrections file with CRLF on every line | same | accepted, rc 0, sha 28f92c5d1211207c, 780 lines | see note 4 |
| H4c edits file with ONE stray CR inside edit 3's old text | refuse, no output | failing [('3', 0)], rc 1, no file | yes |
| H5 empty edits file | refuse | `old list parsed 0 edits, expected 29`, rc 1, no file | yes |
| H5b empty corrections file | refuse | `found 0` RENUMBER lines, rc 1, no file | yes |
| H6 RENUMBER line duplicated (2 lines) | refuse | `exactly one RENUMBER line, found 2`, rc 1, no file | yes |
| H7 RENUMBER from=16 to=13 (from > to) | refuse | `RENUMBER from is greater than to`, rc 1, no file | yes |
| H8 output in a folder with `chmod 555`, run as uid 0 | refuse (permission) | NOT refused: written, rc 0, sha 28f92c5d (root ignores mode bits) | test not valid, see note 3 |
| H8b same folder with `chattr +i` | refuse, no file | `cannot create output exclusively: ... Operation not permitted`, rc 1, no file | yes |
| H9 output name with spaces (`out with space.md`) | written, sha 28f92c5d | rc 0, sha 28f92c5d1211207c, 780 lines | yes |
| H9b second run to a new name | same sha (repeatable) | sha 28f92c5d1211207c | yes |
| input after all runs | unchanged | 515cf4704ebba5bd | yes |

## Part 4: flake arithmetic in `patches-ready/v6-extra/DESCRIBE-ONLY-flaky-id-test.md`
Source log: `patches-ready/v3/raw-c7b-fix1/sibling-clean-allids-OLD.log` (4 lines, see note 5); script `sib.py` in the same folder; text cites `v3/REPORT-c7b-fix1.md:17-18` and `flake-loop-OLD-200k.log`.
| claim | expected | actual | match |
|---|---|---|---|
| ids swept = 4 prefixes x 65,536 | 262,144 | log total line `clean() ids 262144`; 4 x 65536 = 262144 | yes |
| wrongly withheld | 24 | log `bad 24`; my own re-run of `sib.py` against the current `src` (unpatched base) printed the same 3 sample lines and `clean() ids 262144 bad 24` | yes |
| 24 = 4 prefixes x 6 values | 6 per prefix (`ec2a` to `ec2f`) | `sib.py` loops 4 prefixes x 16^4 values; the 6 values are the first-four-digits `ec2a`..`ec2f` by the rule in REPORT-c7b-fix1 line 17; the log itself lists only 3 samples (all prefix `run`), so the 4x6 split is by arithmetic (24 / 4 = 6), not seen in the log | partly (arithmetic yes, log shows 3 samples) |
| 1 id in 10,923 | 262144 / 24 | 10,922.67, rounds to 10,923 | yes |
| 4 ids per run, chance 4 x 24 / 262,144 | 1 in 2,731 | 4 x 24 / 262,144 = 3.662e-4 = 1 in 2,730.67, rounds to 2,731 | yes |
| 4-ids-per-run formula | 4 ids in the test (`run`, `pln`, `apr`, `evt`) | `sib.py` uses those 4 prefixes; I did not open `tests/test_s4_llm_guard.py` to count the ids the test builds | not checked here |
| loop: 81 of 800,000 | 81 | log line: `iterations 200000: iterations with a missing id/hash 81; ids missing 81 of 800000`; expected 800000 x 6/65536 = 73.24 (REPORT says 73.2) | yes |
Command used for my re-run (output kept to the tail): `PYTHONPATH=src uv run --no-project --with markdown-it-py --with pydantic python <scratch>/sib.py` from the repo root (a plain `python3` run failed first with `No module named 'markdown_it'`).
