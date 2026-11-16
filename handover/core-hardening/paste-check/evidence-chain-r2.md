# evidence-chain-r2 (EVIDENCE RUNNER; raw results, no judgement). 2026-11-16
Scratch: scratchpad folder r2 (patches on a copy; real input sha256 unchanged 67a0a195537de875). No file other than this one was written in the repository.
Method: my own commands (patch -p1 dry run then apply; own grep for the four A6 counts, same patterns as LEAD-CHECKLIST-v5.md A6), then test-apply-v10-after-chain.sh and my own hostile inputs.

## FAILURES AND MISMATCHES FIRST
F1. A7 marker lines for CHAIN=4 do not match. Checklist A7 expects 2, 3, 4, 137, 270, 287, 509, 510, 777, 778. Actual in the final plan: 2, 3, 4, 137, 270, 287, 509, 510, 774, 775 (lines 774 = UNVERIFIED item 14 "LEAD-FILL 7", 775 = item 15 "LEAD-FILL 1"). Total marker texts 17 on 10 lines, as stated. Only the last two line numbers are wrong (3 too high).
F2. LEAD-CHECKLIST-v5.md line 64 still contains `b0caeb84c5a28a94` (the old CHAIN=4 sha), not `28f92c5d1211207c`. PLAN-CHAIN.md section 6 already says this; still unfixed when I ran.
F3. RENUMBER line damaged: the script does not refuse. Deleting the line, `shift=0`, or `shift = 4` (spaces) each exit rc=0 and write a 780-line file with sha 5453169115cd74c4 (wrong; right is 28f92c5d1211207c): the cross-references "UNVERIFIED 13/14/15" in edits 8, 13, 27 stay unshifted. Silent wrong output. (Changing `to=16` to `to=15` still gave the right sha, so item 16 is not referenced by those edits.)
F4. Output path that is a DANGLING symlink: the script writes through it (rc=0, created the link target, sha 28f92c5d1211207c). The "output already exists" check uses os.path.exists, which is false for a dangling link. A symlink to an existing file is refused (H2). The symlink-to-input case is refused (T5).

## Chain table
| Step | Expected | Actual | Match |
|---|---|---|---|
| 0 original | sha 67a0a195537de875, 558 lines, A6 0 0 2 0 | sha 67a0a195537de8754ef80bd3bd8d8a4d78a507ca8418bec8f835a0e99abb41f1, 558, 0 0 2 0 | yes |
| 1 plan-v5-fixes.patch | dry rc 0, apply rc 0, 53f1670383a2c728, 561, 0 0 2 0 | dry 0, apply 0, 53f1670383a2c728c4bdbb560f5444766aa0df773ac6f85a4c6496aca1bb1c2a, 561, 0 0 2 0 | yes |
| 2 plan-v5-repin-v6.patch | 39af84aec78b650f, 587, 24 10 2 1 | dry 0, apply 0, 39af84aec78b650f287d20013cdfa2d45dde8b75632e6d6729660bbc21ce3f5b, 587, 24 10 2 1 | yes |
| 3 plan-v5-gate-rows-v3.patch | 515cf4704ebba5bd, 622, 24 10 2 1 | dry 0, apply 0, 515cf4704ebba5bdc00e3c2ab9fdce7f65a2a7b8467ceec0bf0942b7e21a7e45, 622, 24 10 2 1 | yes |
| 4 apply-v10-after-chain.py | 28f92c5d1211207c..., 780, 24 10 2 1 | rc 0, "29 old edits; corrected or added 2 4 5 18 19 20 21 29 30; failing []", 28f92c5d1211207cce0222c87bb7a6e6dc8e39a21a659624a1a7fe9cc32992ce, 780 (wc -l 780), 24 10 2 1 | yes |
| final: steps 156 | 156 | line 539 "156", line 18 "156" | yes |
| final: floor 176 min = 2 h 56 | 176 / 2 h 56 | lines 6, 18, 35, 85, 541 | yes |
| final: unrun files 78 | 78 | line 543 "about 78 file" | yes |
| final: section 7 rows 24 | 24 | line 562 "(24 rows)" | yes |
| UNVERIFIED numbering 1-20 | each once | list at lines 761-780; leading numbers 1..20 each counted once, no duplicate | yes |
| marker lines CHAIN=4 | 2,3,4,137,270,287,509,510,777,778 | 2,3,4,137,270,287,509,510,774,775 | NO (F1) |
| test-apply-v10-after-chain.sh, 9 cases | T1 rc0 sha 28f92c5d1211207c; T2-T9 rc1, nothing written | T1 rc0 sha 28f92c5d1211207c, 780 lines; T2 rc1 none; T3 rc1 none; T4 rc1 sha 515cf470 unchanged; T5 rc1 unchanged; T6 rc1 content "keep"; T7 rc1 failing [('3',0)] none; T8 rc1; T9 rc1 | yes (9 of 9) |

Old-number leftovers: grep for 151/152/154/171/172/173/174 followed by "min" or "steps" in the final plan: 2 hits, both HISTORY rows (lines 35 and 85: "2 h 50 min is a floor", "150 step minutes + 20 write-up = 170 min"), older estimate text, not the current total.

## Hostile inputs (own)
| Input | Expected | Actual | Match |
|---|---|---|---|
| H1 wrong sha input (T2, T3 above; also final.md fed back in) | refuse, no output | refuse rc1, none | yes |
| H2 output symlink to existing file | refuse, file untouched | REFUSED, other file still "keep" | yes |
| H3 output symlink dangling | refuse | wrote through the link, rc0 | NO (F4) |
| H4 existing output | refuse, untouched | REFUSED, content "keep" | yes |
| H5 one edit's old text duplicated (edit 3 old text appended to a plan copy; sha constant patched in a script copy only) | refuse | REFUSED, failing [('3', 2)], no output | yes |
| H6 edits applied twice (final.md as input, sha constant patched in a script copy only) | refuse | REFUSED, 23 edits find 0, no output | yes |
| H7 RENUMBER line damaged (delete / shift=0 / spaces) | refuse | rc0, wrong sha 5453169115cd74c4 | NO (F3) |
| H8 RENUMBER to=15 | same result | sha 28f92c5d1211207c | yes |

## What I did not run
- No Git Bash `patch` (GNU patch on Linux only). No Windows paths.
- Did not read the plan for meaning; did not run any paste in it, n8n, Docker or WSL.
- Did not recompute the 156 / 176 / 78 / 24 totals from their rows; I only read the printed numbers.
- Did not check every one of the 29 edits for meaning; no check of LEAD-CHECKLIST-v5.md beyond lines 31, 62-66 and the sha on line 64.
- Wrong-order patch tests (PLAN-CHAIN.md section 3 table rows beyond step order) not repeated.
- The H5/H6 sha-bypass tests changed the INPUT_SHA constant in a scratch copy of the script only; the real script was not edited.
