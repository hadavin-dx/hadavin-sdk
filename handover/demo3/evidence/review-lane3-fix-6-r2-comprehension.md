**Review of the round 2 documentation patch (read-only, naive-reader audit)**

I read the patch and the full patched files: `docs/tests.md`, `README.md` (the Words used here, Try it and claims sections), `docs/real-services.md`, and the `contract.md` Run commands paragraph in the patch. I did not check any code fact. Line numbers refer to the patched tree at `/home/user/work/b6b-base`. I found 0 Blockers, 6 Majors, and the Minors and Nits listed after them.

## What this proposes
The patch does four things.
- It replaces the old one-line "run the desk" instructions with a step list. Window 1 runs the demo server, window 2 runs the desk (or the crash-demo script), and window 3 sends one made-up lead. It explains why `src:.` is needed and gives a PowerShell alternative.
- It rewrites the test-count bullets. The current count is 3683 passed and 200 skipped, with the 200 broken down, and the older counts are kept as history.
- It adds a paragraph on a long hand-run stop-and-restart test with a blind mail system (the soak run).
- It documents `--assume-yes`, the 8-people-plus-twin self-test, and two self-test runs. It also adds a "see the paragraph" pointer and the sentence "a real kill only at D2 in the tests".

## How the existing system works, per this document
The desk needs a separate demo server process that plays the made-up CRM and the made-up mail outbox. A "keyed" mail system sends once per send key, and a "blind" one cannot recognise a repeat. Stopping the desk mid-send on a blind system can leave a follow-up as UNKNOWN, which the desk never resends and a person must check. The tests ran without Playwright (a browser-driving package) and without gitleaks (a secret-scanning program), so 200 tests are skipped. Those were run separately and passed.

## Majors

**M1. `docs/tests.md:28-30`, window 3 and the crash demo do not connect.**
- Step 2 says writing `D2` into the flag file "arms the stop". It does not say in which window, with what command, or whether this must happen before the lead is sent.
- Step 3 then says "when the desk reaches the armed point", but a reader doing the plain desk run (no crash script) never arms anything.
- The exit code 137, the "simulate crash" message and the flag-file removal are listed as the result of step 3. But they appear in window 2, and only in the crash variant.
- Nothing says what a normal step 3 prints, or what to do after the crash (restart the desk in window 2).
- Suggested wording:
  - "3. Window 3, one made-up lead: `...feed.py...` sends the first made-up lead. In the plain run the desk answers with the verdict `new`."
  - "Crash demo only: before you send the lead, arm the stop with `echo D2 > <flag file path printed in window 2>` (Windows: `Set-Content <path> D2`). When the desk reaches that point, window 2 prints "simulate crash", the desk ends at once with exit code 137 (a code the desk gives itself to imitate a power cut) and removes the flag file. Run the window 2 command again to restart the desk."

**M2. `docs/tests.md:26-32` and `README.md:10` vs `README.md:53`, one demo server or two?**
- README line 53 says `start_all` "starts the two demo servers and the desk". The new text says "the demo server program ... plays the made-up CRM and the made-up mail outbox at once", which is one process. The desk's message says "the demo servers".
- A reader cannot tell whether they need to start one or two things.
- The README's own defined term is "Demo stand-ins" (line 31). The new text uses "demo server" without defining it, and README line 53 calls the same things "demo servers".
- Suggested wording: add to Words used here, "**Demo server**: the one program `demo_only.fakes_server`. It plays the CRM and the mail system at once; both are demo stand-ins." Then say "the demo server" everywhere, and change README line 53 to "starts the demo server and the desk".

**M3. `docs/tests.md:30` ("Linux or macOS") and `README.md:10` vs `README.md:47`.**
- README line 47 says "macOS was not tried". The new text calls the commands "Linux and macOS syntax", and `docs/tests.md:32` says `start_all.sh` runs on "Linux, macOS".
- A reader could take that as "macOS works".
- Suggested wording: "shell syntax used on Linux (macOS uses the same syntax but was not tried)".

**M4. `docs/tests.md:88-89, 94, 96`, "current" count contradicted by the patch's own tests.**
- Line 88 says the counts are for commit f3c39cf8, "the main branch before the changes in this patch". Line 94 says "the current suite has 3883".
- Line 89 says this patch adds 6, then 8, then 2 more tests, and that 3689 is "not the count for the latest text".
- A reader who runs the suite on this tree should see about 3893 tests, but no passage says so, and they will not know whether 3893 is right.
- "This patch", "the first version of this documentation patch" and `test_run_commands_lane3.py` mean nothing to someone outside this review; "lane3" is internal jargon.
- Suggested wording: "Expected total with these documentation tests: 3883 + 10 = 3893 tests (the 3883 of commit f3c39cf8 plus 10 new documentation tests in `tests/test_docs_tests_md_lane3.py` and `tests/test_run_commands_lane3.py`). A full run of this exact text was not made; the nearest full run (3689 passed, 200 skipped) was made before 4 of those 10 tests existed." Replace "this patch" with "the commit that added this paragraph".

**M5. `docs/tests.md:94` and `docs/tests.md:91`, "ten files" vs "eight files", and the 22 and 113 clash.**
- Line 94 says the eight older files "are only part of the ten browser files named above". But the eight include `test_portal_mode.py`, and the ten listed in line 91 do not. The statement is false as written.
- The "Browser tests" intro at line 62 lists only seven files and does not match the ten.
- The numbers 22 and 113 each have two meanings in this file.
  - In the current counts, 22 is skips in `test_mode_safety.py` and 113 is skips in `test_portal_lead_pages.py`.
  - In the older record, 22 is the number of tests needing Node and 113 is the total number of browser skips.
- Lines 95 and 96 use "22 for the eight files" as a how-to without saying the older record no longer matches the current files.
- Suggested wording:
  - Line 94: "...the eight files below are not a subset of the ten: `test_portal_mode.py` is in the eight, not in the ten."
  - Add after the numbers: "(These 22 and 113 are unrelated to the 22 and 113 in the current counts above.)"
  - Make line 62 list all the files, or say "see the ten files named under 'The 196 browser and gitleaks tests'".

**M6. `README.md:99`, `docs/tests.md:110`, and `docs/tests.md:127-129`, "only D2 is a real kill" vs the soak.**
- The README and the intro to the table still say only D2 is a real process kill.
- The new line 127 says the soak "ended the whole desk process at many points" and that 156 stops were SIGKILL.
- The sentence "In the tests ... only at D2" tries to reconcile these, but "the tests" vs "the soak" is not defined, and README line 99 was not updated.
- Line 129 also calls the exit-137 stops "a named crash point (the desk ended at once)". Line 110 calls those same points "simulated by an exception". A reader cannot tell whether 137 means a real kill.
- Suggested wording:
  - README line 99: "Of the ten, nine are simulated by an exception inside the program; only one (D2) is a real process kill in the test suite. A separate hand-run stress test (`docs/tests.md`, "Blind mail system, many follow-ups at once") also killed the process at random times."
  - Line 129: "229 at a named crash point (the program ends itself with exit code 137, which imitates a kill but is not one)".

## Minors

- **`docs/tests.md:129`, undefined labels.**
  - "Soak test" is never defined and is first used at line 127. Suggested wording: "a soak test (one long run that stops and restarts the desk again and again)".
  - "The script" (which one?), "round", and "check 2 / checks 3 and 4" have no definitions. Add the script path, and say what check 1 and checks 3 and 4 are.
  - "setting `--max-unknown`" is a command option, not a setting.
- **`docs/tests.md:129`, 9154 and 9100.**
  - The sentence says 197 UNKNOWN, 143 with 1 email, 54 with none, and 9100 with exactly 1.
  - It never says how 9154 − 54 = 9100 fits with the 143, which sit inside the 9100. Suggested wording: "Of the 9154 leads, 54 had no email (all of them UNKNOWN) and 9100 had exactly 1 (including the 143 UNKNOWN ones that had left)."
- **`docs/tests.md:129`, the word "failed".** It could be read as "the desk is faulty". Add: "this failure is expected on a blind mail system: the checker's default allows no UNKNOWN follow-up at all".
- **`docs/real-services.md:9`, 12 people vs 9 leads.**
  - "People" and "leads" are both used, and `REAL_PERSONS` is the people count.
  - It is not said whether the real run's 12 (or whatever `REAL_PERSONS` is set to) also gets a twin, giving 13 leads.
  - "The address ending `example.com`" reads as one address. Suggested wording: "addresses ending in `example.com`".
  - Link or define "lead" (README, Words used here).
- **`docs/real-services.md:14`.**
  - "A UNKNOWN" should be "an UNKNOWN".
  - "The crash window" is undefined. Suggested wording: "the moment the desk is stopped".
  - It is not stated that 8+1 and 6+3 both equal the 9 leads. Add "(9 in all)".
  - "Exit code 1 / 2": add "(listed in `docs/settings.md`)".
  - The settings file, the config and the env file are three names for one thing (`real-services.md` lines 9, 11 and 22).
  - Lowercase `unknown` (line 18) vs UNKNOWN: use one form, or say "stored as `unknown`; shown as UNKNOWN".
- **`docs/real-services.md:14`, `docs/tests.md:34, 88, 91`, references to the author's notes.**
  - The labels "raw/b6b-facts.txt", "b6b-dry-fakes-assume-yes.log" and "those notes" point at files a reader cannot get.
  - The text does say they are not in the repository, which is good.
  - Drop the internal label "b6b", or say "the author's private notes".
- **`docs/tests.md:88`, "200 skip reasons".** The 200 is the number of skipped tests, not distinct reasons. Suggested wording: "none of the 200 skipped tests gives Node as its reason".
- **`docs/tests.md:91`.**
  - "Whole-file totals" is explained, but the point is hard to read.
  - Suggested wording: "241 and 72 count every test in those files, including ones that already passed in the full run; 241 + 72 is therefore larger than 196."
- **`docs/tests.md:26-30, 36`, missing prerequisites.**
  - The `.venv` is not mentioned. README line 51 says a new window needs `.venv` switched on again.
  - Add "each window needs the `.venv` switched on, as in README, "Try it"".
  - The "folder that holds the desk's database file" is not said where (the README points to `./data`).
  - The Windows instruction sits after the Linux steps. Put a one-line pointer in the intro: "On Windows, read the PowerShell paragraph below first."
  - Add one line to the PowerShell paragraph: "in window 3 you may leave the variable as `src;.` too; `feed.py` works with it".
  - The Windows part is untried, which is honestly stated.
- **`README.md:10`.**
  - "The desk alone needs two terminal windows" is misleading, since the desk needs the demo server. Suggested wording: "To start the desk and its demo server by hand".
  - "(not tried here)" is ambiguous; say "(the PowerShell lines were not tried on Windows)".
  - Window numbers 1 and 2 here vs 1, 2 and 3 in `docs/tests.md` are fine but not linked. There is no step that sends a lead.
- **`docs/tests.md:34`, "on private ports".** Unexplained. Suggested wording: "on ports other than 8765 and 8766".
- **`contract.md:23`.**
  - "Scripts set `PYTHONPATH=src:.`" sits against README line 58, which has the reader set `src` and says `start_all.sh` adds `:.`.
  - Name the scripts ("the `start_all` scripts set...").
  - For Windows readers it only mentions `;` and offers no commands; point to `docs/tests.md` for the PowerShell form.

## Nits

- `docs/tests.md:26`: the by-hand paragraph sits under "How to run the tests" straight after the SonarQube coverage paragraph. It would read better under its own short heading.
- `docs/tests.md:151` and `docs/real-services.md:20`: "book" is undefined. This is older text but now sits next to the new text.
- `docs/real-services.md:3-5`: "the steps above" and "this section" refer to a README that is not on the page.
- `docs/tests.md:93`: "this lock" is unclear (the browser lock?).

Files: `/home/user/work/b6b-base/docs/tests.md`, `/home/user/work/b6b-base/README.md`, `/home/user/work/b6b-base/contract.md`, `/home/user/work/b6b-base/docs/real-services.md`.