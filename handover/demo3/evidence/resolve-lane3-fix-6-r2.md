# Resolve plan fix-6 round 2 (Opus egm-resolve; saved by lead, condensed; 24 accepted, 1 wording contested, 0 escalated, 3 declined)
Sources: review-lane3-fix-6-r2-comprehension.md (M1-M6 majors + minors + nits), review-lane3-fix-6-r2-technical.md.
1 M1 crash demo steps: steps 2-3 = plain run (window 2 desk, window 3 feed.py -> verdict new); separate paragraph "Crash demo (instead of step 2)": crash_desk.py prints flag file path; BEFORE sending the lead write D2 into it (echo D2 > path; PowerShell Set-Content path D2); desk prints "simulate crash", deletes flag, ends at once exit 137; run window 2 again to retry. (hooks.py:28-48, crash_desk.py:15-18)
2 M2 ONE demo server: start_all.sh:25 starts one fakes_server process; README:53 "two demo servers" is wrong -> "the demo server and the desk"; define "Demo server" in Words used here; keep code message text "cannot reach the demo servers" quoted and add that there is one program.
3 M3 macOS: "Linux shell syntax (macOS uses the same syntax but was not tried)"; start_all line "(Linux; macOS not tried)"; README:132 same.
4 M4 counts: drop "this patch"/"lane3" wording ("the commit that added this paragraph"); add expected total 3883+10=3893 (10 new tests: 8 + 2); use E9 measured numbers if evidence/e9-fix-6-r2-report.md exists; keep "reported, not re-measured" labels otherwise.
5 M5 eight vs ten: test_portal_mode.py (Node, not Playwright) is in the eight not the ten; add "(22 and 113 here are not the 22 and 113 above)"; Browser tests intro points to the ten files; reword the "22 for the eight files" how-to as older record.
6 M6 CONTEST part: reviewer wording "137 imitates a kill but is not one" is FALSE (hooks.py:45-46 os._exit(137), constants.py:32): use "the desk ended itself at once with os._exit, exit code 137: no clean-up runs, the process really ends; 156 by SIGKILL from outside". README:99: nine of ten simulated by exception; D2 is a real process end in the tests; the hand-run soak also ended the process at many points. Separate "in the tests" from "in the soak" in tests.md:110/127.
7 soak labels: define soak test, round, checks 1-4 (read load_tools/check_invariants.py), "the script" = soak script not in repo, "option" not "setting".
8 9154/9100: 54 no email (all UNKNOWN), 9100 exactly 1 (incl. the 143 UNKNOWN whose mail left); none 2.
9 "failed" expected on a blind mail system (default allows no UNKNOWN).
10 real-services.md: "addresses ending in example.com"; default 12 people + twin = 13 leads; self-test 8+1 and 6+3 = 9 in all; "an UNKNOWN"; "the moment the desk is stopped"; exit codes in docs/settings.md (check); one name for settings file; stored `unknown` shown UNKNOWN; self-test allows UNKNOWN only for sends in flight at the kill up to the number of send workers (script 427, 1034 - read first).
11 drop private file names and "b6b": "(seen on Linux with Python 3.12.3, on ports other than 8765 and 8766; the author's notes are not in this repository)".
12 "none of the 200 skipped tests gives Node as its reason".
13 241/72: "count every test in those files, including ones that already passed; 241 + 72 is therefore larger than 196"; keep label.
14 prerequisites: .venv on in each window; db folder ./data by default (check Config.db_path); Windows pointer in intro; window 3 may use src;. too (feed.py works with both).
15 README:10/132: "To start the desk and its demo server by hand"; "(the PowerShell lines were not tried on Windows)"; mention the third window that sends the lead.
16 start_all also sets DESK_LEADFLOW_FILE (lead owner, stage, reminder) and DESK_NUDGE_TO; by-hand commands do not.
17 contract.md:68 (not :23): "the start_all scripts set PYTHONPATH=src:."; PowerShell see docs/tests.md.
18 nits: heading "Running the desk by hand"; "README, Try it" for "steps above"; "browser lock file" for "this lock".
DECLINED: "book" undefined (older untouched text), N1 (deliberate pin), N2 (matches evidence).
Work order B6c: facts (6,1,2,3) first; 4,5; 7-17; 18; update/add pinning tests that fail on old text (<=120 chars, no noqa); targeted tests + hygiene while working, one full suite at end; produce lane3-fix-6-r3.patch and lane3-fix-6-r3-for-stack.patch (apply check on f3c39cf8 and on base+claims stack); one report when done.
Final fresh review checks: numbers vs code and raw/b6b-facts.txt; one-demo-server wording everywhere; crash demo steps; no sentence says 137 is not a kill; old counts labelled history; tests fail on old text; no private path/"b6b"/"lane3" in public text; for-stack applies.
