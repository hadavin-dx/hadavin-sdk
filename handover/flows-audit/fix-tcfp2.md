# fix-tcfp2 (fixer; edited only TAKE-CHECKLIST.md and FIX-PLAN.md; backup in scratchpad bak-tcfp2/)

## Failures, gaps and things not checked (first)
- Nothing was run except two read-only repository checks and greps. No take_check.sh, no patch check, no n8n, no ledger_check. Every command written in the two files is "not run".
- `egm/tools/ledger_check.py` is not in this repository (no `egm/` folder). The command is written for the lead's machine; coverage of the topic `duplicate-proof-lead-desk` is unproven (Inputs item 11).
- The reviewer's "line 157 -> 210" was wrong for the 'not found' text: line 210 of OWNER-STEPS-q16-rows.md is the re-pin row T5. The 'not found' text is line 63 (also line 50). I used 63 and said so in the file. Also the old cite "lines 57 and 88" of that file did not match; replaced with lines 83 and 120 to 123 (read).
- Reviewer B1 was right for take_check.sh: it no longer prints "must be deleted at clean-up" (line 139 says it never deletes). The "decision 4" text is at take_check.sh lines 10, 175, 176 (not 158/159) AND at check_flows.py line 156 (SAVE_ACCEPT_REASON); both listed now.
- New finding while reading take_check.sh: `flow-check/take-warns.pin` reviewer line says "flows-audit session ... lead to confirm"; take_check.sh line 227 treats that as "pin not yet confirmed" and exits 4. So check 1 cannot exit 0 until the lead replaces that line. Added to TAKE-CHECKLIST check 1, Inputs item 14 and FIX-PLAN step 4. Not run, read from script text.
- Because take-warns.pin is one file, step 4 on the unfilled copy must be run (and its log kept) before the export pin replaces it; written in both files (read from script text, not run).
- Still open, cannot be answered from ORDERS (all marked LEAD FILLS and collected in the list at the top of TAKE-CHECKLIST.md): scripts missing at re-pin (no fallback in ORDERS), T21 failure and the alwaysOutputData fallback, F-011/F-041 downgrade evidence, whether round 24 is needed for GO, which flows the re-smoke fills, two shas (I24), who confirms the pin, HubSpot id search yes (now marked INFERENCE, not Q25 item 1), clock times of owner items 2 to 4, whether pass A and pass B both fit the one 2 h rehearsal window, and durations of the positive control and Step D message 1.
- FINDINGS.md "NOT COVERED" item 20 still carries the old "owner's written yes with numbers" wording; FINDINGS is not my file: the lead/owner of that file should reword it.
- `ruff format --check`: no Python file was edited, so nothing to check (not run).

## Applied: citations-tc-fp-r1.md
- B1 stale "must be deleted at clean-up": removed in TAKE-CHECKLIST (check 1 fail text, Still open 6) and FIX-PLAN (step 4 end, saved-runs paragraph, lead fixes (1), rule (h)); kept what is true (fill_flows/README.md line 240 still says it; checked by reading line 240).
- M2 line 3 range now 105 to 171, newest Q30. M3 disowned 13:00Z / 18:30 IST heading in FIX-PLAN removed (heading now "Q26, ORDERS.md", with a note that Q30 disowns the stamps). M4 HubSpot "no new yes, Q25 item 1": now stated as inference in one Words-box paragraph and pointed to from checks 4, 10 and FIX-PLAN step 10b, step 14, rule b7. M5 line 157 -> line 63 (see above).
- Nits: "on 2026-11-16 on 2026-11-16" fixed. Other nits (OWNER-STEPS-realrun-v3 line 121, n8n_api.py also in Q27 item 1) are in the lead-fix list of other files; the `inputs/` line 121 cite was left as it is in TAKE-CHECKLIST Still open 6 (not re-checked).

## Applied: readiness-tc-fp-r2.md
- B1 Tuesday GO: new "Tuesday GO test" table (7 rows: merge, review, final evidence, re-pin, short re-smoke with steps, ledger, F-011/F-041), each with who, command, pass line or LEAD FILLS. `git branch -a --contains <sha>` for merge, take_check command for re-pin, `python3 egm/tools/ledger_check.py --topic duplicate-proof-lead-desk` marked "run on the lead's machine from the studio folder, pass = exit 0". r23/r24 question and the flows used by the re-smoke are inputs 9 and 10.
- B2 F-011/F-041: FIX-PLAN item 8 rewritten (no "ONLY if" / "after the video" contradiction); item 8b kept; FP58 now says due before Tue 14:00Z; TAKE-CHECKLIST check 12 added.
- B3 slot table added in FIX-PLAN item 3 (ORDERS anchors vs inference); T19 to T21 runner marked LEAD FILLS; sub-flow import order is FIX-PLAN step 6 (unchanged, read).
- B4 F-002 lift rule: one sentence in TAKE-CHECKLIST Words box (Codes); FIX-PLAN item 2 has the same sentence; checks 3b, GO row, step 10, GO bullet point to it. States what ORDERS says (Q27-9 T19 to T21 lift; Q29-3 T19/T20 failure is NO-GO; Wed 07:30Z) and what is open (T21 failure, fallback).
- B5 Wednesday scripts: Inputs item 7 (no fallback in ORDERS; inference stated).
- M1 FP1 vs FP12: the opening "rebuild in real-v5" now says regeneration into the NEW folder, never in place.
- M2 rehearsal count: "rehearsal 1/2" renamed pass A / pass B inside ONE window (ORDERS); start-state gate (step 14) heading now states it runs before steps 10, 10b and each send; check 14 added; durations not in ORDERS marked LEAD FILLS.
- M3 grep -c exact counts replaced with grep -q "at least one line" and "no line" tests (counts not verified; script text builds INFO at line 139 once but whole-output count was not checked). "decision 4" grep changes in the same commit as the script edit (stated).
- M4 pins: described above (one file, order, reviewer line, I24, sha256 of the four flows printed by the FINAL line).
- M5 owner list: times from ORDERS (about 10:00Z, post 15:00Z) written; items 2 to 4 times LEAD FILLS; S9-2 / S9-3 defined (QUESTIONS.md line 144 quotes the decisions file).
- M6 F-031/F-007: files (handover/demo/VIDEO-RUNSHEET.md, handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md), greps, who/new wording LEAD FILLS; check 13 added. The F-031 sentence is not in the run sheet today (grep found none when I looked), so the test fails now and should pass after the edit.
- M7 ledger command: forward slashes, python3, machine, pass exit 0.
- M8 claims without command: FP step 1 apply-order now "earlier session reported, not re-run"; patches F-003/F-004 given check_patches.sh and a grep for 60.1 / 61.9 in added lines (not run); "exit 0 does prove" softened to "should mean ... read in script text, not run"; node counts cited to take_check.sh lines 53 to 79; lock-guard "round 23" now "being built, not merged".
- M9 steps with no command/input: marked LEAD FILLS (steps 9, 10, 10b, 11) and listed in Inputs.

## Checks after editing (run from handover/flows-audit)
```
$ python3 -I tools/check_secrets.py
PASS 0 hits in 1742 files            (exit 0)
$ python3 tools/check_refs.py
PASS 5147 references                 (exit 0)
```
ruff format --check: not applicable (no Python file edited), not run.
Note: these two scripts check secrets and file references only; they say nothing about whether the new text is right. No independent review of the new text was done by this fixer.
