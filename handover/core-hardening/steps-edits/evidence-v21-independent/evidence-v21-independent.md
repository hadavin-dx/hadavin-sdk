# Evidence v21 (independent EVIDENCE RUNNER), Mon 16 Nov 2026 about 13:10 to 13:20 UTC
I ran checks and saved raw output. I did not fix anything and I do not judge. No secrets, no spend, no network. The key-save tests used a fake key built from parts, in a scratch folder under the session scratchpad (not deleted: the delete command was blocked by the safety check and I created nothing inside the evidence folder that needs removing).

## Failures and gaps first
F1. Wrong pointer, sheet R10: it says "`echo $?` once as R6 says". The R6 row never mentions `echo $?` (0 hits in the R6 row). The only place is the command list ("once, after R3 is complete and the prompt has returned"). Raw: 03b-pointer-semantics.txt.
F2. Wrong pointer, note section 0 item 6: "Open 1 and 2 carry the decision". Open 1 in v21-OPEN-FOR-LEAD.md is "ANSWERED by Q23: removed" and has nothing to do with the older key. Only Open 2 (and Open 31) carry it.
F3. Note section 0 is numbered 1, 2, 3, 4, 5, 6, 8, 7 (item 8 comes before item 7). Open 47 cites "Note section 0 item 8". Cosmetic but a reader can lose the order.
F4. Note section 5 says "the v16 sheet section 5 says person A is sent twice ...". OWNER-SHEET-v16.md has no numbered sections (headings are named). The counts are in its "Words" part (line 18) and its appendix (line 304). The pointer "section 5" does not exist.
F5. R8 charset against two set phrases: R8 limits typed values to letters, digits, single spaces and `. _ / - : = @ + ,`. The set phrase "got a message that says <in words>; is it yours?" holds `;` and `?`. The report line `name | last used time | zone` (8.1) holds `|`. R8 says it covers "values you type (names, mail addresses, the yes, the post)"; whether it also covers messages is not stated. Unclear, not proven wrong.
F6. Placeholder spelling differs: set phrase list and R2/6.2 use `"I cancel the older key <its name>"`; the order-of-the-day row 6 uses `<name>`.
F7. Quoted phrases that look like set phrases but are not in the set-phrase list (they are "report in words" items): "a long text was on the screen" (R1), "first 16 match" / "first 16 differ" (glossary, 7.2), "long text in setting <name>" (5.7), "no Recall page" (6.1). The list says "anything else is a report in words", so this is consistent only if the owner reads them as examples; the sheet does not say they are examples.
F8. The builder's check-v21.py did NOT catch 2 of my 13 planted mistakes (section 6). It cannot check whether a set phrase is on the list (M5), and it does not check what an R-pointer points at (M11, which is exactly F1's class).
F9. Sample date oddity: the sheet's run day sample is Wed 18 Nov, but the 6.6 `ps` example reads `Mon Nov 16 11:42:07 2026` and the `ls` example `2026-11-16 11:40:55`. Both are weekday-correct; they are on a different day than the sample run day. Cosmetic.
F10. Open 30 says "v20: 6,650 words as counted by v20". `wc -w` gives 6,638 for v20. The v21 figure 7,943 matches `wc`. Small mismatch of 12 words.
Not checked: whether the facts in the sheet are true (no take program, flow, model program or Windows machine here); the repo's own pytest guard test (this folder is not a git checkout, I only counted its BANNED words); the quality of the wording.

## 1. Fingerprints (01-sha256.txt)
- OWNER-SHEET-v20.md: 36a31fbe62a2894c6b7a7de0be8f2cfc670ae34d29a782ddf896dd6d03f215c8 = the recorded value. UNCHANGED (PASS).
- OWNER-SHEET-v21.md: dec3ba6349ef1ce852c1389bdb6a767650b350278e7eb36b55966c69d650bbb7
- LEAD-RELEASE-NOTE-v5.md: 4b480a64c1741705442205f59f19eee69d1cd968a6488050fc86f820883ae7cd
- LEAD-RELEASE-NOTE-v4.md: 986b3bdb5ef56eb82f2b5b2a47be37c041ca16bed858b1681de6a4b9208154c4 (no recorded value was given; just listed)
- v21-MAP.md cadfa1a3...21e7f9, v21-OPEN-FOR-LEAD.md 11bc1303...ecfa4, check-v21.py e519978c...d7805 (full values in the file). Files were not changed by me.

## 2. Recompute (my own script, 02-recompute-raw.txt): 69 checks, 0 FAIL
All pass: price 0.27 = (40000 x 3 + 10000 x 15) / 1,000,000; 3 x 0.27 = 0.81; 12.40 + 0.81 = 13.21 = 1321 cents; settings in cents give 27 cents per call; 13.00 ok and 13.50 not; 3.10 to 3.90 = 0.80 and 4.00 would be 0.90; 13.21 <= 180; balance 189 >= 0.81.
Times: 25 = 5 + 10 + 10; B = 18:29:00 - 860 s = 18:14:40 (= 23:44:40 IST); deadline - 45 min = 17:44:00; LS 11:30, LF 11:55, CB 12:05 (17:00, 17:25, 17:35 IST); Mon 23 Nov example 17:44:00, 18:09:00, 18:19:00 (23:14, 23:39, 23:49 IST), CB exactly 10 minutes before the deadline; post-by 15:00 UTC = 20:30 IST; ps example start 11:42:07 is later than the file time 11:40:55; 2 + 10 + 1 = 13 submissions.
UTC to IST pairs: 18 found (9 sheet, 9 note), 18 PASS. Weekday mentions: 21 found (sheet, note, open list), 21 PASS (Mon 16, Wed 18, Mon 23, Wed 25 Nov 2026; ISO dates 2026-11-23 and 2026-11-16 are Mondays, 2026-11-10 is Tuesday, 2026-11-15 Sunday, 2026-11-13 Friday).

## 3. Pointers and cites (03-*.txt)
- Item pointers N.M in sheet, note and open list: all exist (items per section: 5=8, 6=6, 7=8, 8=5). The two "BAD" lines in 03-pointers-raw.txt are "section 0" in the note and open list, which do exist (false alarm of my script).
- Section pointers in the sheet, rule ids R1 to R10, gate ids G1 to G38 and Open numbers (max 50 rows) all resolve by number. The meaning of each of the 25 "Open n -> G" pairs matches by title (03b). Meaning failures: F1, F2, F4.
- Sheet cites no gate id (checked by my own regex; also see M9).
- File and line cites, each read against the file: ORDERS.md line 150 (Q21.1, text equals the quote), line 152 (Q21.3), lines 186 to 194 (Q22 to Q29, Q30/Q31); OWNER-STEPS-realrun-v3.md line 130 (Step 23); QUESTIONS.md line 55 (Q21 item 1); FACTS line 3 (US$180 of 189, "no limit questions") and line 4 (written yes with the numbers shown by the notice); AGENT-SCOPE line 15 (180 of 189 quote), line 20 (`:1051` DELETE, section 3), line 22 (typed worst-case figure shown in the notice), line 23 (`:573`, "B ten times at once"); DECISION-one-store line 14 (ONE database), lines 25 and 26 (CORRECTIONS (a), "decision 4"); plan-wp6 line 121 (ports 5690 to 5693); DECISIONS items 1, 2, 7, 8, 9, 10, S9-2. All match. Exit codes 0/1/2/3 match v3 line 172. 860 s matches v3 line 171. Exception: F4 (v16 "section 5").
- Set phrases: 13 listed. All listed phrases are used elsewhere only in their stated places. See F5, F6, F7 for the phrases that are quoted but not listed. "go", "post", "continue", "n8n is off" are lead words and are covered by R8.

## 4. Commands (04a to 04d)
- Fenced blocks: 2 (sheet numbers-message sample, note template). Both are data templates, not commands; `bash -n` says syntax error (rc 2), as expected for prose. 26 inline command spans were also extracted: 21 rc 0 as written; 5 had bare `<placeholder>` text (rc 2); with a value put in, all 5 are rc 0.
- Key-save line (6.4), copied from the sheet, run with `bash -c` (pipes, no terminal), made-up data:
  - empty line: prints `exit 1`, no file.
  - fake key built from parts (29 characters): `exit 0`, file size 30 (= length + 1), mode `-rw-------`.
  - stdin closed (no input): `exit 1`, no file.
  - key without a final newline (EOF): `exit 1`, no file.
  - a single space: `exit 1`, no file.
  - run again on the existing file: "cannot overwrite existing file", `exit 1`, file unchanged (30).
  - missing folder: "No such file or directory", `exit 1`.
- Same line in a real pseudo-terminal: Enter after the fake key: `exit 0`, size 30, key text never shown on screen. Ctrl-D at the prompt: `exit 1`, no file. Empty Enter: `exit 1`, no file. Ctrl-D typed after text then Enter: `exit 0`, size 30 (the terminal passes the text on; Ctrl-D alone is what fails). Ctrl-C: the whole line ends with no `exit` line and no file.
- `ps -o pid=,lstart=,comm=` form, `ls --time-style=full-iso`, `date -u`, `grep "^NAME="`, `sha256sum` first 16, `pgrep -f` (no match rc 1) behave as the sheet describes. `ls ~/.hadavin-take-tags` with no folder prints "No such file or directory" (matches the 5.1 wording).

## 5. Counts (05-counts-banned.txt)
| file | lines | words |
|---|---|---|
| OWNER-SHEET-v20.md | 110 | 6638 |
| OWNER-SHEET-v21.md | 118 | 7943 (+1305, +19.7 percent) |
| LEAD-RELEASE-NOTE-v4.md | 145 | 6985 |
| LEAD-RELEASE-NOTE-v5.md | 147 | 7281 |
Banned words: 10 listed in BANNED; occurrences in the sheets, notes, open list, map, changes, checkpoint, builder evidence and check-v21.py (11 files): 0 case-sensitive, 0 case-insensitive, 0 with spaces, hyphens and underscores removed. Also 0 in all my own evidence files.

## 6. Builder's check-v21.py and my mutation test (06a, 06b)
Unmodified run: exit 0, "TOTAL PROBLEMS 0" (18 pairs, 12 weekdays, 68 glossary terms, G1..G38, 50 open rows).
Mutation test: I copied the files to a scratch folder per mutation, pointed a copy of the script at it, planted ONE mistake each. Baseline M0 clean.
| id | planted mistake | caught |
|---|---|---|
| M1 | wrong IST pair (12:05 UTC = 17:45 IST) | YES |
| M2 | wrong weekday (Thu 18 Nov 2026) | YES |
| M3 | broken pointer (6.9) | YES |
| M4 | a banned word inserted | YES (counts only) |
| M5 | an unlisted set phrase ("started ok" in 7.4) | NO (rc 0) |
| M6 | a rule phrase repeated ("ONE cancel rule") | YES |
| M7 | minute sum 26 instead of 25 | YES |
| M8 | program limit 13.31 | YES |
| M9 | a gate id (G30) in the sheet | YES |
| M10 | wrong IST pair in the note | YES |
| M11 | R10 pointer changed from R6 to R5 (the F1 class) | NO (rc 0) |
| M12 | Open 99 pointer in the note | YES |
Required five (M1 to M5): 4 caught, 1 missed (M5). Extra eight: 7 caught, 1 missed (M11). Total 11 of 13 planted caught; the 2 misses show the checker proves form only, as its header says.

## Files (all in /home/user/hadavin-sdk/handover/core-hardening/steps-edits/evidence-v21-independent/)
01-sha256.txt, 02-recompute-raw.txt, 03-pointers-raw.txt, 03b-pointer-semantics.txt, 03c-quoted-phrases.txt, 03d-cites.txt, 04a-bash-n.txt, 04b-keysave-pipes.txt, 04c-keysave-pty.txt, 04d-readcommands.txt, 05-counts-banned.txt, 06a-check-v21-raw.txt, 06b-mutation-raw.txt, this file. Scratch (mine): /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/v21ind/ (scripts recompute.py, mutate.py, keytest2/, blocks/, mut/).
