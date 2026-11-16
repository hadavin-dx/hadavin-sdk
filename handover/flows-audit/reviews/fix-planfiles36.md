# fix-planfiles36 (round 36, fixer on RUNBOOK.md, FIX-PLAN.md, TAKE-CHECKLIST.md)
Real clock: 2026-11-16 (date only; I did not log the minute). Nothing was run on n8n, Postgres or HubSpot. Not committed.

## NOT done or uncertain (read first)
1. Shell behaviour: only `bash -n` on all 28 code fences (0 failures) plus one real run of the new `keysave` guard on made-up names in a scratch folder (key file written; with an empty PATH it printed the REFUSED openssl line). The new guarded commands in FIX-PLAN (Step 5 (v), Step 7, Step 14) are inline text, not in fences: NOT run, NOT syntax-checked.
2. M4 Nits not done: RUNBOOK lines 30-34 and 68 (old UTC-only history) left, as the reader rated them Nit; I did not scan all other lines for a bare UTC time.
3. Unread by me: the reader's unread ranges (RUNBOOK 1-29, 55-67, 177-end; FIX-PLAN 68-89, 120-end; TAKE-CHECKLIST 81-478) were not read in full.
4. Unrated item "echo exit $? after a group redirect is always 0" (FIX-PLAN Step 8a, same in RUNBOOK step 11): only a warning sentence was added in FIX-PLAN (the exit is the last echo's; the count 2 is the real pass). The RUNBOOK copy is frozen and still has no such note.
5. Line numbers: FIX-PLAN gained about 45 lines near the top (line 1 split), so any outside note that names "FIX-PLAN line N" for N > 1 (QUESTIONS.md lines 485, 600, 712; old fix-*.md reports) now points to the wrong line. QUESTIONS.md not touched, per brief. In the three plan files I found and fixed the only two "FIX-PLAN line 1" references (RUNBOOK 360, TAKE-CHECKLIST 59 -> "FIX-PLAN.md 'Plan overview' item 6").
6. M6 partly wrong in the reviewer's words: lines 11, 52, 53, 54 are 83, 229, 122 and 202 words, not 1000+; line 1 had 662 words and line 63 had 638. Lines 52-54 are table cells in the 48-line clock block, which must stay identical in both files, so I only numbered the sentences inside the cells of two rows (identical edit in FIX-PLAN and TAKE-CHECKLIST) rather than splitting the table; row 53 (122 words) left as is.

## Items (each checked against the text first)
- M1 CONFIRMED (RUNBOOK 175 `keysave`, no openssl check, openssl absent from the Machine list). DONE: `openssl` added to the Machine list (RUNBOOK section 4) with `command -v openssl`; keysave now refuses if openssl is missing and refuses (saves nothing) unless KEY, KEYF and KEYH are each 17 characters (L + 16 hex). Checked by run on made-up data (see 1 above).
- M2 CONFIRMED (FIX-PLAN Step 8 and Step 8a said 06:39Z (12:09 IST); TAKE-CHECKLIST Inputs item 3 says Tue 05:54Z (11:24 IST); Step 6 and RUNBOOK I10 agree with 05:54Z). DONE: both Steps now say 05:54Z (11:24 IST) with the reason. The 06:39Z in TAKE-CHECKLIST 59 and RUNBOOK step 11 text for `stepjudge` is the later step 11 and is correct there.
- M3 CONFIRMED in FIX-PLAN Step 12 and (found by me, not named) FIX-PLAN rule (b7) "ANSWERED" and TAKE-CHECKLIST line 130 ("07:00 ... the governing time"), which contradicted TAKE-CHECKLIST 76 and FIX-PLAN line 1 (06:53Z, 12:23 IST). DONE: all three carry the earlier time 06:53Z (12:23 IST) as the operator's time, with the lead's 07:00Z (12:30 IST) named as the lead's own figure until he answers. RUNBOOK not touched (it already states the clash).
- M4 CONFIRMED. DONE with IST recomputed by hand: 03:30Z = 09:00 IST (RUNBOOK 116, 151); 10:30Z = 16:00 IST (155); 04:00Z = 09:30 IST and 06:39Z = 12:09 IST (157); Wed window 09:47 to 10:32 UTC = 15:17 to 16:02 IST (44; the old text gave IST for the end only). Nits at lines 30-34 and 68 not done (item 2 above).
- M5 CONFIRMED for the three FIX-PLAN copies. RUNBOOK step 8 (v) and step 10 already had guards (I read step 8 (v); I did not re-read step 10 in full). DONE: Step 5 (v) insert test guarded with `. "$ENVSH" && need_set PGCONN_SELECT_ONLY INSERTLOG && { ...; }` and its grep now uses RUNBOOK's `-F "permission denied for table mf_leads"` (the old FIX-PLAN grep matched any "permission denied", which RUNBOOK step 8 says is wrong); Step 7 four greps guarded (`need_set FLOWS` / `FILLED`; the echo of the exit number sits inside the braces so it cannot print after a refusal); Step 14 two count commands guarded (`need_set PGCONN_SELECT_ONLY KEYS`).
- M6 DONE: FIX-PLAN line 1 split into 9 numbered items under a new "Plan overview" heading (the operator rule stays on line 1; times and the Q-list mapping became sub-bullets, same words); the line 63 map paragraph split into 9 numbered items with one sub-bullet per step; two clock-block rows numbered (see 6 above); bare "step N" in Steps 5, 7, 8, 8a, 9b, 10, 11, 12, 14 and in the new overview items labelled "FIX-PLAN Step N" (12 places). Bare "step N" inside Steps 5-10 text that already names a file ("walk-through step 7", "Pin procedure, step 4") left. Meaning not changed; checked by reading the new text, not by a diff tool.
- Unrated TAKE-CHECKLIST 6: `grep -c JUDGED` must print 1; added "2 or more is not a pass; stop and tell the lead". "Pass:" text order in Step 5: not changed.

## Outputs (from handover/flows-audit, after the last edit)
- python3 -I tools/check_refs.py: PASS 5182 references
- check_names.py: PASS 655 rows
- check_secrets.py: PASS 0 hits in 2812 files
- check_counts.py: PASS 52 files / 655 nodes
- python3 -I tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md: RESULT: PASS
- ruff format --check .: 938 files already formatted
- bash -n on all 28 code fences (RUNBOOK and TAKE-CHECKLIST; FIX-PLAN has none): 0 failures
- Clock block (48 lines from the bold "Tuesday 17 Nov: the re-pin event" line, FIX-PLAN line 38, TAKE-CHECKLIST line 9): `cmp` of the two blocks printed DIFF-EMPTY; 48 lines.
Files changed: RUNBOOK.md, FIX-PLAN.md, TAKE-CHECKLIST.md, reviews/fix-planfiles36.md. R-numbers: none looked up (static wording pass). EGM skipped for the sequence: lead runs the review step.
