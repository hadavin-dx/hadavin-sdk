# fix-findings-ledger27 (2026-11-16): the 12 Nit items of reviews/findings-ledger-reader-r27.md

Fixer: sole editor of FINDINGS.md and LEDGER-ROWS.md; also wrote ledger-history-cells.md (moved history) and this report. No severity, status or count was changed (45 rows, 5 Blocker, 5 Major, 35 Nit; 11 take-path, 34 not). Not committed. EGM skipped for the fixer: text edits of an audit file whose review is run by the lead (egm-comprehension reader r27 is the review of this result's input; the lead runs the next one).

## What was checked first (the reviewer's words are unverified)
All 12 points were checked against the row text and the cited files. All 12 are right. Two were worse than stated:
- Item 4 (F-015): the old fix said "connect SendMail straight to OutUnknown". In mf-sub-crm-mail.json SendMail does not feed the two IF nodes at all: its first output goes to MarkDone, its second (error) output to MarkUnknownA, and UnknownNewA follows MarkUnknownA; UnknownNew follows MarkUnknownB (second output of MailRowBack). The old fix text was wrong, not only unclear. Corrected.
- Item 5 (F-014): the two periods are two different paths, not a contradiction (send fails: AlertBackoff, 60 to 300 s; send works but AlertMark fails: 720 s window). Reconciled with the arithmetic 86400/300 = 288 and 86400/720 = 120.
- Item 6: unknown_model is the flag name in stage_server.py:51; the label returned is "unknown". Plan lines :79 and :82 confirmed (same lock).
- Item 9: DOUBTFUL-SCENE.md is not a README; "verdict 4" is row 4 of the table "Verdict per part of the build" in FINDINGS.md.
- Item 10: Q15 is QUESTIONS.md:278, Q19 item 5 is QUESTIONS.md:307.
- Item 11, F-046: the old text called the empty-key test T1; the real new id is T20 (T19 is the same-key-twice test). Wording written with T20.

## Changes (each mirrored into LEDGER-ROWS.md where the text is in the fix cell; evidence-cell-only edits are FINDINGS only, because the ledger carries the fix cell word for word plus the bold summary)
1. F-004 pass line fails closed: parts (0) patch applies, (1) positive control prints 4, (2) after apply exactly FOLDER-OK / 0 / grep-exit=1, (3) heading count 1. Each starts with `test -n "$REPO" && test -f <file>`, prints FOLDER-OK, gives the file path, and tests the grep exit status. Evidence cell now points to it instead of the open-ended "Today it prints 4 lines".
2. F-004 split: fix and pass line first, then who/when/what closed proves, order and time, the still-open statement 14 item (named in plain words), file fact. Round history moved to ledger-history-cells.md (section fix-findings-ledger27). Source cell now says :120 vs :148-161 (NAMING at :150), "before the patch". The TAKE-PATH yes vs "no scene reads it" is explained in one sentence.
3. F-010: role count marked as undecided and by whom; shared mail credential (mf-mail-smtp used by SendMail and AlertSend) added as an OWNER step; "No test: Nit, closed by reading".
4. F-015: correct nodes named (MarkUnknownA and MarkUnknownB, with which output); pass line (grep -c UnknownNew) added.
5. F-014: the two repeat periods reconciled (evidence cell).
6. F-013: title and body say the answer is "unknown" (flag unknown_model); "single flight" explained as the same lock as "single-flight lock"; closing condition added (status stays OPEN, studio lead sets the word).
7. F-012: "up to 5" is LIMIT 5 in the ClaimStuck query (also L1-7).
8. F-033: names the template (templates\project\scoping.md via the options-first rule; not in this repository, UNVERIFIED) and a suggested line.
9. F-023: the three texts named (two READMEs plus DOUBTFUL-SCENE.md:13); verdict 4 defined; pass line (grep -c "was run live").
10. F-032: "SUPERSEDED by Q15 and Q19-5" replaced by the decision in plain words with line numbers.
11. F-005, F-006: the lane wording is now inline; F-016: grep command for the 1/1/1/0 claim, with the four folder names; F-046: replacement wording inline (M1 and T20).
12. Pass lines or "No test: Nit, closed by reading": F-009 (grep headerAuth, spelling UNVERIFIED), F-015, F-017 (reading), F-021 (grep DESK_URL), F-025 (test ! -e v1-superseded), F-030 (reading), F-033 (reading), F-036 (T-FLOOD named as the pass test; needs the new proxy).

## Commands and output (from handover/flows-audit, 2026-11-16)
- `python3 .../scratchpad/compare14.py FINDINGS.md LEDGER-ROWS.md` printed `45 45 differences: 0`.
- `python3 -I tools/count_findings.py`: 45 rows, Blocker 5, Major 5, Nit 35 (all 45 = 11 take path + 34 not).
- check_refs PASS 5192 references; check_names PASS 655 rows; check_secrets PASS 0 hits in 2836 files; check_counts PASS 52 files / 655 nodes; `ruff format --check .`: 961 files already formatted.
- New pass lines were extracted from FINDINGS.md by script and run (REPO = the real repository = the BEFORE state; REPO empty; scratch copies for AFTER and planted hit):
  - F-004 (0) real: `FOLDER-OK`, `apply-exit=0`; empty REPO: only `apply-exit=1` (no FOLDER-OK = FAIL).
  - F-004 (1) real: `FOLDER-OK`, `4`, `grep-exit=0`. Scratch after `git apply` of the patch: `FOLDER-OK`, `0`, `grep-exit=1` (PASS); heading count `FOLDER-OK`, `1`, `grep-exit=0`.
  - F-004 planted hit (line "see 61.9 s" appended): `FOLDER-OK`, `1`, `grep-exit=0` (FAIL as it should). Missing file and empty REPO: only `grep-exit=1`, no FOLDER-OK (FAIL as it should).
  - Real repo for the others: F-023 `FOLDER-OK`,`1`,`grep-exit=0`; F-015 `FOLDER-OK`,`6`,`grep-exit=0`; F-021 `FOLDER-OK`,`1`,`grep-exit=0`; F-009 `:0` and `:0`; F-016 `:1 :1 :1 :0`; F-025 `FOLDER-OK` only. Empty REPO: no FOLDER-OK for each.
  - Scratch after-state: F-015 (names removed) `FOLDER-OK`,`0`,`grep-exit=1`; F-021 after rename `FOLDER-OK`,`0`,`grep-exit=1`.

## Not checked / lead decisions
- Not run: F-009 after-state against a real exported flow (the n8n spelling "authentication": "headerAuth" is UNVERIFIED; the cell says so); F-015, F-016, F-021 after-states ran only on edited scratch copies, not on a real fixed flow; F-025 after-state not run (folder not archived); no n8n test (IMPOSSIBLE-NOW here, as the rows already say).
- templates\project\scoping.md (F-033) is outside this repository and was not opened.
- Pre-existing: git status shows QUESTIONS.md modified; not by this fixer.
- Lead decisions: (a) F-010 role count (two, four or five) stays open until the ROLES decision; (b) F-013 closing condition wording and status word; (c) F-033 suggested line and the template owner; (d) F-017 "no test of this row alone" accepted?
- Slips: the first run of my edit script failed on an assertion before writing anything (no file changed); fixed and rerun.
