# Round 26 fix: RUNBOOK.md, FIX-PLAN.md, TAKE-CHECKLIST.md (one fixer)

Input: reviews/plan-files-reader-r25.md (0 Blockers, 11 Majors; the reviewer's words were unverified). Static work: nothing was run except `bash -n` (syntax parse only) and the four repo check tools. Made-up data only. Lines are those of the files AFTER this round.

Honest first: all 11 findings were checked against the three files, Q31 and ORDERS.md and all 11 are right (none contested). Three points are NOT closed by me because they are the lead's: see "needs lead" and "needs Q31 edit". No command was run for real, so every new command is "mine, not tried"; only its syntax was parsed.

## Per finding

| # | Result | Where (after this round) | What |
|---|---|---|---|
| 1 | fixed; one part needs lead / Q31 edit | R:209 (step 4a Fail cell), R:269-270, Clock row 4a and Wait rule (F:19, F:27, T:13, T:21), who-table WARN reader (F:52, T:46), T:85 | One rule everywhere: the wait runs 04:16Z to 04:46Z at most; the 10 min of 4a work come AFTER it, so 4b starts 04:56Z after a full wait (04:26Z with none) and the event ends 08:59Z (08:29Z with none). Pin 1 window after a full wait: 04:56Z to 05:21Z. CONFLICT NOT MINE TO SETTLE: Q31 item 51 (c) caps all Tuesday waits at 24 min and says that cap wins over "waits up to 30 min". I wrote the 30 as the upper bound, and the 24 case (wait ends 04:40Z, 4b 04:50Z, every wait case 6 min better) next to it. |
| 2 | fixed; one choice needs lead and Q31 edit | R:223 (step 16), R:270 new paragraph "Step 16 extras", Clock (row 16 and Wait rule), F:19 to F:28 region mirrored in T | The claim "the lead's slot to about 09:30Z holds the difference" was false: with step 1 at 04:00Z the re-smoke already ends 09:29Z (1 min slack). 60 min is now stated as the figure WITHOUT the extras; extras are stated: positive control 14 min, hand-run gate 11 min more. Cases 1 to 4 (429/459/459/489) stay as the baseline; cases 2 and 4 (90-min slot) already hold the extras (90 = 60 + 30 >= 60 + 25). New cases below. |
| 3 | fixed (siblings too); HubSpot row needs lead | T:73, T:76 (item 17), T:197, T:198, T:202, T:203, who-table owner row (F:54, T:48) | One time per input, from Q31: F-011 route Tue 03:00Z (item 10 (a)) at T:203; ledger rows Tue 07:00Z (item 26) at T:202; PIN_NAME Tue 03:30Z (item 48) at T:73 (the 04:26Z is when the reader first reads, now said); merge style and shas Tue 03:30Z (item 38 (b)) at T:197; list of reports Tue 10:30Z (item 67) at T:198 (was "before Tue 04:00Z", a sibling the reviewer did not name). HubSpot scopes: two decisions, item 30 (which reading) by Mon 20:30Z, then item 27 (when the ask goes) by Mon 21:00Z; with no answer item 30's own default stands (reading 1, ask Monday night), so the Wednesday times of that row are marked STALE for the lead. |
| 4 | fixed | R:52 | Short re-smoke = a second n8n start the lock file must refuse, one made-up lead sent twice, count proof; it does NOT repeat n8n start, import and fill (RUNBOOK steps 7 to 13 did them once). Now agrees with R:223 and T:116. |
| 5 | fixed | Clock block (F:14-47, T:8-41, same text), F:63, R section 6 not touched for this | Every bare "step N" or "Steps N" in the Clock block is now "RUNBOOK step N" (13 places, by a lookbehind regex; the "RUNBOOK step 16", "RUNBOOK step 22" forms already present stay). "FIX-PLAN step 22" is now "RUNBOOK step 22 (FIX-PLAN Step 12)" (FIX-PLAN has no step 22; F:107 Step 12 is the gated 08:33Z). F:63: Step 0 = RUNBOOK 1 plus the first command of RUNBOOK 2 (check_patches.sh); "16 = RUNBOOK 25 and 26 / 17 = RUNBOOK 26" now says 16 = RUNBOOK 25 and the take part of 26, 17 = the counts-proof and Step D message 2 part of 26. |
| 6 | fixed for the three named steps and for the dangerous siblings; the rest is stated below | R:206, R:212, R:215, R:216, R:219, R:220, R:221, R:224 | New first part `. "$ENVSH" && need_set NAMES &&` on step 9 (a), (b), (d), (e) (and the guarded forms), step 10 (check and four greps), step 14 greps (RUNSHEET, absolute `"$REPO/..."` paths, no `cd`, `test -s`/`test -d` first), step 2 (check_patches, apply, diff), step 6 `mkdir`, step 12 three export loops. "Prints nothing" checks now sit in `{ grep ...; echo "grep exit $?"; }` after a `test -d`/`test -s`, and the pass is "no hit line AND `grep exit 1`"; a missing `grep exit` line is not a pass. `bash -n` result below. |
| 7 | fixed | T:6 (Pass rule), R:191, R:220 step 13 (b), R:223-224 step 17 (4) | Pass rule now names the step records (`stepjudge`, `JUDGED step N check ... result ...`) as the second use of Form 2 with the steps that use them (13 (b), 17 (4), 22 to 26, 29) and says they never turn a failed Form 1 into a pass. Step 13 (b) hand `printf` (named `$PIN_NAME`, no result, no head) replaced by `stepjudge 13 bang-lines-read passed` with `need_set JUDGE_WHO JUDGELOG FINAL_SHA`. Step 17 (4) now first runs a mechanical presence check of the eleven step logs `runbook-step-N.log` (N = 1 2 3 4 4a 4b 6 9 10 13 14; `log-present` x11, no `LOG-MISSING`) before the `stepjudge 17` call. Step 15's note line stays a note (the person reads it, then the step 17 judgement). |
| 8 | fixed | R:210 pass cell | "the chain of (e) printed `sha-written` (route A), or, in route B, where (e) is not typed, Block P1c printed `sha-written`". Checked: T:397 and T:401 (Block P1c) print `sha-written` and `sha-written-repeat`. |
| 9 | fixed | R:363 (row I6) | First half deleted; now "step 8 (0b) creates it with DB_SETUP.sh, or the lead names an existing one". Agrees with R:214 and the second half of the same cell. |
| 10 | fixed; the clash itself needs lead | R:321 (N5), R:325, F:1, T:76, T:130 | ONE governing time named: Mon 23 Nov 07:00Z, the lead's own value (ORDERS line 156 item 6, Q27 item 6), read as the latest END of the re-pin. R:325 states that this puts the take start at 07:00 + 307 min = 12:07Z, 7 min after the 12:00Z slip limit (Q27 item 7), and offers 06:53Z (12:00 minus 307) as the alternative for the lead. T:76 no longer calls 18:29Z a re-pin time (it is the money stop). F:1 and T:130 point to N5. "The lead picks" removed. |
| 11 | fixed | R:3 | Status now "STATIC READ, newest round 26 (log reviews/fix-planfiles26.md; rounds 13 to 25 are in their own fix logs)". |

## Arithmetic (python3, run in this session)

Event 269 min. Baseline cases: 1 = 269+60+60+30+10 = 429 -> 14:00 minus 429 = 06:51Z. 2 = 269+90+60+30+10 = 459 -> 06:21Z. 3 = 429+30 = 459 -> 06:21Z. 4 = 489 -> 05:51Z. (unchanged)

New, with the Tuesday positive control (14 min, re-smoke 74) or control plus hand-run gate (14+11, re-smoke 85):
- 269+74+60+30+10 = 443 -> 06:37Z (12:07 IST); with a 30-min wait 473 -> 06:07Z (11:37 IST).
- 269+85+60+30+10 = 454 -> 06:26Z (11:56 IST); with a wait 484 -> 05:56Z (11:26 IST).
- Re-smoke end from a 04:00Z start, no wait: 09:29Z (60), 09:43Z (74), 09:54Z (85). Spare before 14:00Z = 271, 257, 246 minus 60, 30, 10 = 171, 157, 146. After one 146-min repeat of the flow files: 25 (baseline, R:279 says 24 from 170), 11, 0.
- Wait: 04:16 + 30 = 04:46, + 10 = 04:56 (4b); with the 24-min cap 04:16 + 24 = 04:40, + 10 = 04:50.
- NO-GO re-pin: 07:00 + 307 min = 12:07Z; 12:00Z minus 307 min = 06:53Z.

## bash -n (syntax parse only)

Every new or changed command span that starts with `. "$ENVSH"` in R:206, 212, 215, 216, 219, 220, 221, 224 was extracted and piped to `bash -n`: 29 spans parsed with rc 0, and 2 spans rc 2. The 2 are not commands but the words `. "$ENVSH" && need_set NAMES &&` and `... need_set NAMES && test -s FILE &&` that explain the rule in R:215 and R:221 (they end in `&&` on purpose); nothing else failed. Raw list: scratchpad `bn.txt` (29 lines `bash -n rc 0 | ...`, final line `parsed ok 29 bad 2`).

## RUNBOOK edits (the lead's frozen v4; every one is a wording or consistency fix)

R:3 status (11); R:52 glossary (4); R:191 pointer sentence (7); R:206 step 2 prefixes (6); R:209 step 4a Fail cell, 4a work after the wait (1); R:210 step 4b pass cell (8); R:212 step 6 mkdir prefix (6); R:215 step 9 prefixes (6); R:216 step 10 prefixes and pass cell (6); R:219 step 12 loops (6); R:220 step 13 (b) (7); R:221 step 14 greps (6); R:223 step 16 slot claim and extras (2); R:224 step 17 (4) (7); R:269 wait paragraph (1); R:270 NEW paragraph "Step 16 extras" (2); R:321 N5 (10); R:325 "Time statements that disagree" (10); R:363 row I6 (9). No time value of the lead was changed; the 269, 429/459/489, 146, 575 to 665 figures stand.

## needs lead

1. NO-GO latest re-pin: 07:00Z (lead's value) gives a take start 7 min after the 12:00Z slip limit; keep 07:00Z and accept a late start, or move to 06:53Z.
2. Tuesday positive control (14 min, Q27/round 21 M10): keep it on Tuesday (spare falls to 157, or 146 with a hand-run gate) or cut it (spare stays 171).
3. HubSpot scopes: which reading of "take prep" (Q31 item 30, due Mon 20:30Z). Default if silent: reading 1, ask Monday night; then the Wednesday asks in the who-table row, RUNBOOK step 19 and T:29 are stale.
4. Step 4a wait: 30 min (RUNBOOK) or the shared 24-min cap (Q31 item 51 (c)).

## needs Q31 edit (I did not touch QUESTIONS.md)

- Item 51 (c): says the spare is 171 and the slack after a repeat is 24; if the lead keeps the Tuesday control the spare is 157 (146 with a hand-run gate) and the slack 11 (0). If the 24-min cap stands, items 69, 80 and 81 ("up to 30 min") and RUNBOOK step 4a should say 24 (this file keeps 30 as the upper bound).
- Item 15: "step 4b needs the name by 04:26Z at the latest" while item 48 says 03:30Z; item 15 should say 03:30Z, with 04:26Z as the first read.
- Item 27: its default (ask Monday night) now matches the who-table; no change needed unless the lead picks reading 2.

## Final verification (from the flows-audit folder; raw)

```
$ diff <(sed -n 14,47p FIX-PLAN.md) <(sed -n 8,41p TAKE-CHECKLIST.md); echo "diff rc $?"
diff rc 0
$ diff who-tables (FIX-PLAN 49-61 vs TAKE-CHECKLIST 43-55)
diff rc 0
$ python3 -I tools/check_refs.py
PASS 5176 references
$ python3 -I tools/check_names.py
PASS 655 rows
$ python3 -I tools/check_secrets.py
PASS 0 hits in 2668 files
$ ruff format --check .
816 files already formatted
```

Not checked: the 139 command spans of RUNBOOK rows 1 to 17 were scanned by a script for a missing first part; I fixed the ones that write, delete, create a folder, run `git apply`, or make a "prints nothing" check pass falsely (steps 2, 6, 9, 10, 12, 14). The remaining spans append to `$TESTLOG` or read with `git -C "$REPO"`; with an empty name they fail on the redirect or run in the current folder without writing, but I did not add the prefix to each; section 4 already requires it. If the lead wants all of them prefixed it is a mechanical pass.
