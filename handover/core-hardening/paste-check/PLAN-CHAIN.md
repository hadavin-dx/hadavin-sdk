# PLAN-CHAIN: the one order in which the plan is patched (2026-11-16, chain builder; fixes finding 1 of `../cross-read/one-place-sweep-r2.md`; fix pass 2 after `review-chain-r1.md`: final sha is now `28f92c5d1211207c`, see section 6)
Words: "the plan" = `inputs/plan-wp6-resmoke-v5.md` (never edited; every step below ran on a copy). "Chain" = the patch steps in order. "Edit list" = `plan-v10-real-v5-edits.md` (text for the lead; 29 edits).

## 0. What failed, what is uncertain, what I did not check (read first)
1. **`LEAD-CHECKLIST-v5.md:9` and `LEAD-FILL-list-v5.md:2` name TWO patches (fixes, then repin-v6). The chain has THREE patch steps, then the edit list.** With two patches the plan is 172 min; with `plan-v5-gate-rows-v3.patch` as the third step it is 174 min; with the edit list on top it is 176 min. Those two files are owned by another builder and I did not edit them. Both the checklist and the fill list need one line saying which end state the lead builds (the lead decides whether `plan-v5-gate-rows-v3.patch` is part of the run).
2. **The old edit list does not apply after the chain.** `plan-v10-real-v5-edits.md` was written against the unpatched plan. After the chain 5 of its 29 edits find no old text (2, 18, 19, 20, 21: floor minutes, steps, unrun files, section 7 row count) and edit 5 still applies but writes a wrong number. The corrected text is in `plan-v10-corrections-after-chain.md` (9 blocks after fix pass 2: edits 2, 4, 5, 18, 19, 20, 21, 29 and an added 30, plus a renumbering rule for edits 8, 13 and 27). The old file's text is unchanged; only a warning banner was added at the end of its line 1. Fix pass 2 (review `review-chain-r1.md`, M1 to M3) found that the first corrections were not enough: old edit 29 would have numbered the new UNVERIFIED items 13 to 16 a second time (chain items 13 to 16 already exist), old edit 4 wrote 151 to 153 and 171 to 173, and corrected edit 21 had dropped the INDEX.md line 1 sentence.
3. The edit list cannot go BEFORE the chain: applied first, `plan-v5-fixes.patch`, `plan-v5-repin-v6.patch` and `plan-v5-gate-rows-v3.patch` all fail (tested, section 3). Cannot go between fixes and repin-v6 either (repin-v6 fails).
4. Not checked: I did not run the plan, any paste in it, n8n, Git Bash or the laptop. I did not recompute the section 5 totals (151, 152, 154, 156) from their rows; they are the numbers printed in the plan text and the v10 arithmetic (+2 steps, +2 minutes). The "+1 unrun file" and "+1 row" of the edit list were taken from v10 edits 20 and 21, not counted again. I did not read all 29 edits for meaning; I read edits 4, 5, 8, 13, 21, 27 and 29 for the numbers and cross-references the review named, and checked that old text is found exactly once and that the result is stable. The marker count (17 marker texts on 10 lines) is not re-counted here; I counted only the four checklist greps.
5. Patch dry-runs used GNU `patch -p1` on Linux, same as `gate-rows/patch-chain-output.txt`. Git Bash `patch` behaviour is untested (also stated in `REPORT-repin-v6.md` section 1).

## 1. The chain (order matters; each step was applied to the output of the one before)
Start file: sha256 `67a0a195537de8754ef80bd3bd8d8a4d78a507ca8418bec8f835a0e99abb41f1`, 558 lines. Patch files, all in this folder; apply with `patch -p1` from the folder that holds `inputs/`.

| Step | File (sha256 first 16) | Dry run | Plan sha256 after (first 16) | Lines | `<FINAL[-]`, `LEAD-FILL [0-9]`, `HEAD_PIN` line, `RE-PIN` line (checklist A6) | Steps | Floor | Unrun files | Section 7 rows |
|---|---|---|---|---|---|---|---|---|---|
| 0 | none (original) | n/a | `67a0a195537de875` | 558 | 0 0 2 0 | 151 | 171 min = 2 h 51 | 76 | 20 |
| 1 | `plan-v5-fixes.patch` (`9e8d06ddb5bb5b57`) | rc 0 | `53f1670383a2c728` | 561 | 0 0 2 0 | 151 | 171 min = 2 h 51 | 76 | 20 |
| 2 | `plan-v5-repin-v6.patch` (`8a83abaa5c10db10`) | rc 0 | `39af84aec78b650f` | 587 | **24 10 2 1** | 152 | 172 min = 2 h 52 | 77 | 21 |
| 3 | `plan-v5-gate-rows-v3.patch` (`498c1e5f4b3debc9`) | rc 0 | `515cf4704ebba5bd` | 622 | **24 10 2 1** | 154 | 174 min = 2 h 54 | 77 | 23 |
| 4 | edit list v10 + `plan-v10-corrections-after-chain.md`, via `apply-v10-after-chain.py` | 29 old edits plus 1 added edit, each found once | `28f92c5d1211207c` | 780 | 24 10 2 1 | 156 | 176 min = 2 h 56 | 78 | 24 |

Full sha256: step 1 `53f1670383a2c728c4bdbb560f5444766aa0df773ac6f85a4c6496aca1bb1c2a`; step 2 `39af84aec78b650f287d20013cdfa2d45dde8b75632e6d6729660bbc21ce3f5b`; step 3 `515cf4704ebba5bdc00e3c2ab9fdce7f65a2a7b8467ceec0bf0942b7e21a7e45`; step 4 `28f92c5d1211207cce0222c87bb7a6e6dc8e39a21a659624a1a7fe9cc32992ce` (the first fix pass gave `b0caeb84c5a28a94`, 779 lines; that file had the wrong UNVERIFIED numbering and the 171 to 173 row, do not use it).
The four counts become `24 10 2 1` at step 2, not at step 1 (step 1 gives `0 0 2 0`). Steps 2 and 3 give the same four counts, so the checklist A6 check cannot tell them apart; use the sha256 column.
The floor numbers 171, 172, 174 and 173 (the last is the old v10 text at `plan-v10-real-v5-edits.md:262`, which is 171 + 2 on the unpatched plan) are not four plans: they are steps 0/1, 2, 3 and "v10 on the unpatched plan". The right number for each end state is the Floor column.

## 2. Which end state to use (the lead decides; the three possible end states)
- Two patches (what the checklist says): step 2, sha `39af84aec78b650f`, 172 min. The edit list v10 cannot be put on it without the corrections (same five failures).
- Three patches (adds the gate rows, the pass/fail check the lead asked for in Q18 item 2): step 3, 174 min.
- Three patches plus real-v5 edits (the video run as planned in v10): step 4, 176 min = 2 h 56 min.
A later step is applied only to the exact sha of the step before. The old edit list alone (on the unpatched plan, 173 min) is a fourth end state that has none of the re-pin, fixes or gate-rows text; do not use it with the chain.

## 3. Order tests (all on scratch copies under the scratchpad; the real input was only read, sha unchanged `67a0a195537de875`)
| Test | Result |
|---|---|
| fixes, repin-v6, gate-rows-v3, each `patch -p1 --dry-run` then real apply on the output of the one before | all three rc 0 |
| old edit list v10 on the ORIGINAL plan | 29 of 29 found once (agrees with `dryrun-v10.txt`, `apply-v10.py`) |
| old edit list v10 on step 1 (fixes only) | 29 of 29 found once |
| old edit list v10 on step 2 and on step 3 | FAIL: edits 2, 18, 19, 20, 21 find 0 old text |
| old edit list + corrections on step 3 | 29 old edits and the added edit 30 each found once (`apply-v10-after-chain.py`); result sha `28f92c5d1211207c` |
| edit list v10 on the original, THEN fixes, repin-v6, gate-rows-v3 | all three patches FAIL (rejected hunks) |
| fixes, then edit list v10, THEN repin-v6 and gate-rows-v3 | repin-v6 and gate-rows-v3 FAIL |
Earlier checks of the wrong order for the patches alone (gate-rows first fails 7 of 8 hunks; v6 on the original 5 of 15 hunks fail) are in `gate-rows/patch-chain-output.txt` and `REPORT-repin-v6.md`; the evidence runner repeated them (`evidence-chain-r1.md` Part A) and got the same counts. One more fact from that run: in the order fixes, gate-rows-v3, repin-v6, the gate-rows-v3 step fails (5 of 8 hunks) but repin-v6 still applied (rc 0) on the damaged file; so rc 0 of the last step does not show the order was right: check the sha256 after every step.

## 4. Why the five edits fail after the chain (plain words)
Edit 2 quotes "Floor about 2 h 51 min clean" (plan line 5). The re-pin patch changed the floor to 2 h 52 and the gate-rows patch to 2 h 54, and the re-pin patch added one header line (the RE-PIN line; the gate-rows patch adds none), so the quoted text and the line number are gone. Edits 18 to 20 quote the steps total 151, the clean total 171 min and the "2 h 51 min is a floor: about 76 files" sentence. Edit 21 quotes the section 7 heading "(20 rows)". Each of these numbers was moved by the two later patches. Edit 5 quotes "171 min clean is a floor" (an old table row the patches do not touch), so it applies, but its new text said 173; after the chain it must say 176. Also changed by fix pass 2: edit 4 (new CHANGES row, steps and floor), edit 21 (keeps the INDEX.md line 1 sentence), edit 29 (UNVERIFIED items numbered 17 to 20 and appended after chain item 16), the two "which is what section 5 says now" HISTORY texts (edit 5 and the added edit 30), and the cross-references "UNVERIFIED 13", "14" and "15" in edits 8, 13 and 27, which become 17, 18 and 19.

## 5. How to reproduce (read-only on the real files; output goes to a copy)
```bash
cd <path>/core-hardening && W=$(mktemp -d) && mkdir "$W/inputs" && cp inputs/plan-wp6-resmoke-v5.md "$W/inputs/" && cd "$W"
for p in fixes repin-v6 gate-rows-v3; do patch -p1 --dry-run < <path>/core-hardening/paste-check/plan-v5-$p.patch && patch -p1 < <path>/core-hardening/paste-check/plan-v5-$p.patch || break; done
sha256sum inputs/plan-wp6-resmoke-v5.md        # must start 515cf4704ebba5bd
python3 <path>/core-hardening/paste-check/apply-v10-after-chain.py inputs/plan-wp6-resmoke-v5.md "$W/real-v5-plan.md"   # failing []
sha256sum "$W/real-v5-plan.md"                  # must start 28f92c5d1211207c
```
The script reads `plan-v10-real-v5-edits.md` and `plan-v10-corrections-after-chain.md` from its own folder; it writes only to the second argument. It is a copy of the logic of `apply-v10.py` with the corrections table added; I did not change `apply-v10.py`. Fix pass 2 (review M2): the script now refuses an input whose sha256 is not the gate-rows-v3 result (`515cf4704ebba5bd...`), refuses equal or same-file paths (also by symlink), refuses an output that already exists, writes only when every edit found its old text exactly once, and exits 1 on any refusal or failure (0 only when written). Test on scratch copies: `test-apply-v10-after-chain.sh`, output in `evidence-chain-r1.md` Part F.

## 6. Final numbers of the chain (fix pass 2, recorded 2026-11-16)
| What | Value |
|---|---|
| Final plan sha256 | `28f92c5d1211207cce0222c87bb7a6e6dc8e39a21a659624a1a7fe9cc32992ce` |
| Lines | 780 (step 3 had 622) |
| Checklist A6 counts (`<FINAL[-]`, `LEAD-FILL [0-9]`, HEAD_PIN lines, RE-PIN line) | 24 10 2 1 |
| Steps, floor, unrun files, section 7 rows | 156, 176 min = 2 h 56 min, 78, 24 |
| UNVERIFIED items | numbered 1 to 20, each once (no duplicate number) |
**For the lead and the builder who owns `LEAD-CHECKLIST-v5.md`:** line 64 of that file names `b0caeb84c5a28a94` as the expected sha256 for CHAIN=4; it must now read `28f92c5d1211207c` (I may not edit that file). Not checked: the plan itself, any paste in it, n8n, Git Bash.
