# Review brief: the 13 sentence-fix commits (EVIDENCE RUNNER)

EVIDENCE RUNNER. I read the 13 diffs and a few lines of code and wrote this brief. I did not run lint, pytest, the network or any agent, and I changed no file in the tree. I do not judge any sentence. Every "expected result" below is what a reader should see IF the sentence is true. The reviewers decide.

Studio folder: `<studio>/` does not exist in this container, so no bible R-numbers were read or cited.

Tree: `/tmp/d-tree`, HEAD `f1ba4ad`, base `f3c39cf8`. Run every command from `/tmp/d-tree`. File:line values are taken at HEAD (`f1ba4ad`), so a line may differ from the one in the commit's own diff. Re-find a sentence with the grep term in the command.

Total change: 30 files, 230 lines added, 215 removed (`git diff --stat f3c39cf8..HEAD`). Only 5 files are code or tests: `tests/test_input_edge_cases.py` (one assertion), `scripts/start_all.ps1` (one PowerShell condition), and docstring or comment lines in `src/lead_desk/*.py`, `scripts/*.py`, `load_tools/catcher.py`.

## Reading order

1. Oldest first: `git log --reverse f3c39cf8..HEAD`. Later commits correct earlier ones, so a sentence in commit 1 may already be rewritten in commit 10.
2. Judge against HEAD, but read each commit's diff (`git show <sha>`) to see what the author thought was wrong before.
3. Start with the code-touching commits (2: 5671981 and 13: f1ba4ad), then the number-heavy ones (1, 4, 6, 11, 12), then the sentence-by-sentence docs commits (8, 10).
4. Commits 3, 5, 7, 9 are small review-fix follow-ups of commits 1, 4, 6, 8.

## Trap classes seen in this series

1. **Denial of a test that exists** ("no test checks X", "not tested"). The author searched `tests/` and had to fix several (commit 10 is titled for this). Check with `grep -rn` on the key words in `tests/`; also check the reverse, a test claimed that does not exist.
2. **A named test that asserts less than the sentence says** (for example `test_write_once_triggers` named for a rule list, `test_ten_parallel` for the "only one email", `test_replays_cannot_burn_the_cap` for "replays do not use up the 5 tries"). Open the test and compare what it asserts with every clause.
3. **Numbers from memory**: test totals (2449, 2462, 2465, 2513, 2516, 2329, 3726, 91 or 92 lines), line numbers in `docs/tests.md`, run times (16 min 33 s, 993 s, 958 s), "about 150 connections", 55 s, version numbers, file counts (34 lines of `exceptions.txt`, "About 200 lines"). Re-count each one.
4. **Tries versus retries**: `SEND_MAX_ATTEMPTS = 5` counts tries in total (the first drive counts); the n8n node's "3 tries" is also total tries; "retries up to three times" (older text) versus "three times in all" (newer text) for Semgrep exit 2. Check each against the code or workflow.
5. **Units and scale**: seconds versus minutes, 9 s versus 5 s timeouts, 1 MiB versus 7 digits, "about 11 minutes" (10+60+180+420 = 670 s), bytes versus characters.
6. **"From the author's own run, no log shipped"**: the series turns unverifiable claims into attributed claims. Check that the attribution is not itself an overclaim ("checked", "measured", "confirmed") and that no sentence still states such a run as a plain fact.
7. **Counts of "all" or "every"** ("every kind is listed", "all five read through that connection", "every request on every route passes the gate").
8. **Fixed a sentence in one place, left its twin in another** (same figure in `README.md`, `docs/limits.md`, `docs/tests.md`, `versions.md`, `contract.md`). After each commit, grep for the old wording across the whole tree.
9. **Comment and docstring edits that change a guarantee** (`gate.py`, `desk.py`, `live_claude.py`, `imap_count.py`): the code was not changed, so the new sentence must match the code as it is.

---

## 1. 04ad414 Fix false and stale sentences in the docs and workflow comments

Files (added/removed lines): `.github/workflows/lint.yml` 2/2, `.github/workflows/semgrep.yml` 1/1, `contract.md` 9/9, `docs/limits.md` 1/1, `docs/portal.md` 1/1, `docs/settings.md` 5/5, `docs/tests.md` 5/5, `docs/why-this-code.md` 2/2, `scripts/hubspot_probe.py` 2/1, `src/lead_desk/loader.py` 2/2, `versions.md` 5/3.

Claims: the first big fix pass. It corrects the UTF-16 body statement (not accepted: 400), the `not_sent` 409 `call_still_running` case, the schema write-once rules, the `crm_done` backfill classes, the reaper-pass overrun, the SMTP timeout defaults, `scripts/feed.py` hosts, the rota key rule, the demo extension (`crash` versus `burst`), and adds "earlier commit, no log, not repeated here" wording to every test-run figure.

Riskiest sentences:

1. `contract.md:275`: "a row whose `last_error` is `refused`, `unreachable`, `ambiguous` or `crash_while_sending` ... gets 1, in any state except `sending`" and "`test_backfill_classes` checks nine of these cases".
   - Verify: `grep -n "def test_backfill_classes" tests/test_review_item_edge_cases.py`, then open it and list the cases; `grep -n "crash_while_sending\|CrmNothingStored" src/lead_desk/db.py`.
   - Expected if true: the migration code in `db.py` has exactly this order of classes; the test body has 9 distinct row cases; the sentence's list (sending=2, four send errors=1, four `internal:` names=0, other `internal:`=2, failed+label=1, other tried=2) matches the code branch by branch.
2. `docs/settings.md:70` and `:76`: "`DESK_SMTP_TIMEOUT_SECONDS` (default `5.0`, built into the mail sender; it does not follow `DESK_SEND_TIMEOUT_SECONDS`)" and "`DESK_SMTPP_TIMEOUT_SECONDS` (default `5.0` ... `DESK_SEND_TIMEOUT_SECONDS` can only lower it: the sender never waits longer than that setting)".
   - Verify: `grep -n "timeout_seconds" src/lead_desk/smtp_outbox.py src/lead_desk/smtp_provider.py` and `grep -n "send_timeout_seconds" src/lead_desk/config.py`.
   - Note from my glance: both senders default to `Config().send_timeout_seconds` (value 5.0 at `config.py:429`), evaluated when the module loads. The old text said "the same as `DESK_SEND_TIMEOUT_SECONDS`". Check which wording is right for the env-var case, and whether "can only lower it" is true for `smtp_provider.py:110` (limit is `CALL_DEADLINE_MAX_SECONDS`).
   - Expected if true: the sender default is a literal 5.0 not read from the environment, and the desk always passes its own `send_timeout_seconds` as the call limit.
3. `versions.md:9` / `docs/limits.md:72` (numbers from memory): "Windows with Python 3.13 reported 2449 passed, 15 skipped; Linux with Python 3.12 (a container) reported 2462 passed, 2 skipped", and "(collection ...) 91 lines in all, and the counts on them add up to 3726" (rewritten to 92 in commit 11).
   - Verify: `grep -n "2462 passed\|2449 passed\|3726" versions.md docs/limits.md docs/tests.md`, and `ls tests/test_*.py | wc -l` (the file count of test files).
   - Expected if true: the same figures in all files; 2462+2 = 2464 versus `docs/tests.md` 2462+3 = 2465 would NOT agree (commit 12 adds a note that admits this). No log exists, so the figures can only be checked for consistency, not for truth.

Also check (extra, one line each): `docs/why-this-code.md:24` "About 200 lines" -> `wc -l tools/scrub_n8n_export.py` (205 at HEAD); `scripts/hubspot_probe.py` header "tries to delete it ... if the delete fails the script warns" -> `grep -n "warn\|delete" scripts/hubspot_probe.py`; `contract.md:269` the five verdict columns -> `grep -n "TRIGGER\|CREATE TRIGGER" src/lead_desk/schema.sql` (or `find . -name schema.sql`).

---

## 2. 5671981 Fix start_all.ps1 empty-value check, tighten one assertion, unify two comments

Files: `.github/workflows/lint.yml` 1/1, `.github/workflows/sonar.yml` 1/1, `scripts/start_all.ps1` 1/1, `src/lead_desk/loader.py` 2/1 (docstring line break), `tests/test_input_edge_cases.py` 4/3.

Claims: the PowerShell launcher no longer sets `DESK_NUDGE_TO` when `DESK_LEADFLOW_FILE` is the empty string (empty means off). `test_two_drives_one_email` now asserts the AI step ran exactly once (`== 1`, was `in (1, 2)`), and its docstring says only the thread that won the claim asks the AI step. The two workflow timeout comments are made identical.

Riskiest sentences:

1. `tests/test_input_edge_cases.py:72-74` and `:80`: "The AI step runs once (only the thread that wins the claim asks it; `tests/test_ai_after_claim.py` pins that too)" and `assert rig.qualifier.calls == 1`. This is a code change, not a sentence: a tightened assertion can be flaky.
   - Verify: `sed -n 68,90p tests/test_input_edge_cases.py`; `grep -n "calls" tests/test_ai_after_claim.py | head`; `grep -n "qualifier\|claim" src/lead_desk/desk.py | sed -n 1,30p`.
   - Expected if true: the claim is taken before the AI step in `Desk._send_claimed` / the drive path, so a second thread loses the claim before asking; the new test is deterministic (also try it 50 times in the review run: `uv run --all-extras --group test pytest tests/test_input_edge_cases.py -k two_drives -p no:randomly --count 50` if the plugin exists, else a shell loop).
2. `scripts/start_all.ps1:9`: `if ($env:DESK_LEADFLOW_FILE -cne 'off' -and -not [string]::IsNullOrEmpty($env:DESK_LEADFLOW_FILE) -and $null -eq $env:DESK_NUDGE_TO) {...}`.
   - Verify: `sed -n 5,12p scripts/start_all.ps1`; `grep -n "LEADFLOW_FILE" src/lead_desk/config.py` to see that empty or unset or `off` all mean off.
   - Expected if true: PowerShell logic matches Python: unset -> demo default set earlier on line 8 (check that line 8 sets the file when `$null`), `off` or empty -> no nudge address. Note `-cne` is case-sensitive; check Python is case-sensitive for `off` as well.
3. `.github/workflows/lint.yml:20` and `sonar.yml:30`: "60 minutes on purpose: the run time on a hosted runner is not measured yet; after real runs, set it to 1.6 times the longest observed run".
   - Verify: `grep -n "timeout-minutes" .github/workflows/*.yml`.
   - Expected if true: both say 60 and both give the same rule; "1.6" appears in both; `semgrep.yml` (20) and `codeql.yml` (30) are different workflows and carry their own words.

---

## 3. b4375bd Review fixes of the first docs change

Files: `.github/workflows/lint.yml` 3/2 (comment re-wrapped), `contract.md` 2/2, `docs/settings.md` 1/1.

Claims: contract says a non-UTF-8 body gives 400 `bad_envelope` on `POST /leads`, `bad_decision` on the resolve route, `bad_step` on the step route, "any other route that reads a body answers 400 with its own code". Backfill: "in any state except `sending`". SMTP timeout "is only the fallback when a send is made without a time limit (a limit of 0 or less), and the desk always gives one".

Riskiest sentences:

1. `contract.md:22`: "`POST /leads` answers 400 `bad_envelope`, the resolve route 400 `bad_decision` and the step route 400 `bad_step`; any other route that reads a body answers 400 with its own code".
   - Verify: `grep -n "bad_decision\|bad_step\|bad_envelope" src/lead_desk/server.py src/lead_desk/desk.py | head -30`; `grep -rn "utf-16\|utf16\|UTF-16" tests | head`.
   - Expected if true: a decode failure of the body ends in those three codes on those three routes; some test sends UTF-16 to at least `POST /leads`. Find which routes read a body (`grep -n "read_body\|rfile.read" src/lead_desk/*.py`) and check each answers 400.
2. `contract.md:275`: "gets 1, in any state except `sending`" (the "in any state" of commit 1 is changed).
   - Verify: same as commit 1, risk 1; check the order: a `sending` row whose `last_error` is `refused` must get 2 (first rule), not 1.
   - Expected if true: the code tests `sending` first.
3. `docs/settings.md:70`: "it is only the fallback when a send is made without a time limit (a limit of 0 or less), and the desk always gives one: `DESK_SEND_TIMEOUT_SECONDS`, with the whole deadline capped at `CALL_DEADLINE_MAX_SECONDS`, 9 seconds".
   - Verify: `grep -n "A \`timeout\` of zero or less" src/lead_desk/smtp_outbox.py`; `grep -n "CALL_DEADLINE_MAX_SECONDS" src/lead_desk/constants.py src/lead_desk/adapters.py src/lead_desk/desk.py`; `grep -n "timeout" src/lead_desk/adapters.py | head`.
   - Expected if true: constant is `9.0` (`constants.py:82`); `adapters.py` calls the sender with a positive timeout. Check that the cap applies to SMTP and that the 5.0 default can never be reached from the desk.

---

## 4. 616f8c4 Soften or source unbacked sentences in README, SECURITY and versions.md

Files: `README.md` 6/6, `SECURITY.md` 3/3, `docs/limits.md` 1/1, `versions.md` 15/15.

Claims: unbacked statements are replaced by "the author's own run, no log is shipped". README: no review record kept; the 404 statement for `/` and `/health` is "tested for other unknown addresses"; the test run time was 16 min 33 s on an earlier set. SECURITY: reporting address and the GitHub private-report button "works only if the owner has switched it on". `versions.md`: Python, SQLite, n8n, Node, lock-file tool versions are marked as the author's records, plus a licence table and a "Side effect" note on `.codeant/configuration.json`.

Riskiest sentences:

1. `README.md:88`: "The desk has no page at `/` or `/health` and answers 404 for an address it does not know (`tests/test_http.py` checks this for other unknown addresses; `/` and `/health` were not tested separately)" (rewritten again in commit 10).
   - Verify: `grep -n "not_found\|404" tests/test_http.py | head`; `grep -rn '"/health"\|"/"' tests/*.py | head`; `grep -n "not_found" src/lead_desk/server.py | head`.
   - Expected if true: `/` and `/health` have no route in `server.py`, so they take the 404 path. (`/` has a test through `test_unparsable_target_is_json`, see commit 10.)
2. `README.md:130`: "A full run was last timed at 16 minutes 33 seconds on an earlier, smaller set of tests (`docs/tests.md` ...); it has not been timed on the current set, which is larger."
   - Verify: `grep -n "16 minutes 33\|993 s\|958 s" README.md docs/tests.md`; `ls tests/test_*.py | wc -l`; compare 2516 (`docs/tests.md:79`) with the collected total in `versions.md:9`.
   - Expected if true: the run figure in `docs/tests.md` is 993 s = 16 min 33 s (993/60 = 16.55: yes); the current collected total is above 2516, so "larger" is true.
3. `versions.md:10, 16, 17, 40`: "SQLite library | 3.49.1 in the author's run ... `ON CONFLICT ... DO UPDATE` ... SQLite supports from version 3.24", "n8n | 2.46.6", "Node.js | 24.22.2", "pip-tools 7.6.2", and the lock-file claims "19 pinned lines" (Windows) and "18 pinned lines" (Linux).
   - Verify: `grep -n "ON CONFLICT" src/lead_desk/desk.py`; `grep -c '^[a-z].*==' requirements-dev.txt requirements-dev-win.txt` (and compare with the sentence `versions.md:71`); `grep -n "n8n\|Node" versions.md`.
   - Expected if true: `ON CONFLICT ... DO UPDATE` exists (`desk.py:1363`); pinned-line counts are 18 and 19 and the only extra line is `colorama`; tool versions cannot be checked from the repository and are labelled as author's records (so the reviewer should check the label is present, not the number).

---

## 5. 5f22cd7 Review fixes: README timing sentence, versions.md notes

Files: `README.md` 1/1, `SECURITY.md` 2/2, `versions.md` 2/2.

Claims: README's "16 minutes 33 seconds" sentence now says no log is shipped; SECURITY says the e-mail "reaches the author" and the GitHub private-report button exists; `versions.md` says no lock-file header records the Python patch version, pip-tools version or the container, and gives the `.codeant` note with "greenlet and pyee; typing-extensions".

Riskiest sentences:

1. `SECURITY.md:9`: "Send a report by e-mail to sales@hadavin.com (it reaches the author)" (commit 4 had a softer "this repository cannot show who reads it"; this is a stronger claim than the previous text).
   - Verify: `grep -n "sales@\|vulnerability" SECURITY.md`; `git show 616f8c4 -- SECURITY.md | grep '^[-+]'`.
   - Expected if true: the claim is backed by something. Nothing in the repository can show who reads a mailbox; the reviewer should treat "it reaches the author" as an unverifiable fact stated flatly, and decide whether it needs the owner's confirmation.
2. `versions.md:40`: "no lock file header records them (this file names them, and `requirements-semgrep.in` names the container image)".
   - Verify: `head -8 requirements-dev.txt requirements-dev-win.txt`; `grep -n "python:3.12-slim" requirements-*.in requirements-*.txt versions.md`.
   - Expected if true: the headers show only the `pip-compile` / `uv` command, not 3.12.16 or 7.6.2; `requirements-semgrep.in` names the image.
3. `versions.md` (browser lock note): ".codeant/configuration.json lists both browser lock files ... among the files its review bot skips" and "(greenlet and pyee; typing-extensions is also listed only in the lock files, which are skipped)".
   - Verify: `grep -n "requirements-browser" .codeant/configuration.json`; `cat requirements-browser.in`; `grep -n "^[a-z]" requirements-browser.txt`.
   - Expected if true: both lock files appear in the skip list; `requirements-browser.in` names only `playwright==1.63.0`; the lock holds `playwright`, `greenlet`, `pyee`, `typing-extensions`.

---

## 6. 2880c80 Soften or source unbacked sentences in docs/tests, limits, settings and portal

Files: `docs/limits.md` 20/20, `docs/portal.md` 3/3, `docs/settings.md` 5/5, `docs/tests.md` 17/17.

Claims: limits, settings, portal and test docs now state which test pins each behaviour and mark unlogged runs. Examples: five put-backs in a row end `failed` (the two ends are tested, the loop is not); a slow sender holds a connection place; "about 150 simultaneous connections" on the author's Windows computer; the exit-code list of `main`; the stall-eviction rule (`EVICT_MIN_IDLE_SECONDS`, 2 s); lifecycle/lead/deal stages "not written by the desk"; masking rules; Semgrep section with a first live run (run 43403502735); secret-scan measurements; the P8 and P10 rows; the mutation-check text.

Riskiest sentences:

1. `docs/limits.md:80`: "The two ends are tested in `tests/test_model_stamp_and_reaper.py` (a row at the limit ends `failed` with nothing sent; one below it goes to `pending`); no single test repeats five put-backs in a row."
   - Verify: `grep -n "def test_" tests/test_model_stamp_and_reaper.py`; `grep -n "SEND_MAX_ATTEMPTS" src/lead_desk/gate.py src/lead_desk/desk.py`; `sed -n 1955,1980p src/lead_desk/desk.py`.
   - Expected if true: `SEND_MAX_ATTEMPTS = 5`; one test puts back a row with 4 (or 5) tries and checks `failed`/`pending`; no test loops 5 put-backs. If such a loop test exists, the denial is false (trap class 1).
2. `docs/limits.md:126` (and `docs/limits.md:67`): "when 256 connections are being read, the oldest one ... that has sent no byte for `EVICT_MIN_IDLE_SECONDS` (2 s) is closed ... (`tests/test_stall_eviction.py` checks a crowd that sends a byte every 0.1 s and one whose work has started)".
   - Verify: `sed -n 205,222p src/lead_desk/constants.py`; `grep -n "256\|MAX_READING\|READ_PLACES" src/lead_desk/constants.py`; `grep -n "def test_\|0.1\|sleep" tests/test_stall_eviction.py | head -30`.
   - Expected if true: constant is 2 (seconds), the read-place count is 256, and the test file has a test with 0.1 s drips and one with a started drive.
3. `docs/tests.md:36` (the Semgrep status) and `docs/tests.md:137` (mutation check): "run 43403502735, 2026-11-13, head 15b8b15e ... "Scanning 64 files tracked by git with 79 Code rules" ... "Ran 77 rules on 47 files: 0 findings"" and "`test_mutant_no_claim` removes the check ... (and, so that this check alone is tested, also switches off the second guard that stops a blind send while another send of the same lead runs)" (the second part was added in this commit).
   - Verify: `grep -n "def test_mutant_no_claim" -A25 tests/test_mutants.py`; `grep -rn "43403502735" . --include=*.md --include=*.yml`; `git log --oneline | grep 15b8b15e` (the commit is not in this tree's history if the grep is empty).
   - Expected if true: the mutant test patches two things (the claim and the blind-send guard) and asserts "emails == 1" and "got 2" text; the run id is only quoted from the lead's reading of a log nobody here can open (cannot be checked from the repository).

---

## 7. 19043f7 Review fixes: licence sentence, reminders, slow-sender, masking, n8n file count

Files: `.github/workflows/semgrep.yml` 3/3, `docs/limits.md` 2/2, `docs/tests.md` 2/2.

Claims: the Semgrep licence is described as "the terms were not read or checked for this repository; the repository owner agreed to use them here"; the slow-sender sentence now says the test also "checks that a connection closed for room after its body was read but before the desk acts leaves nothing stored; that nothing is stored after a 408 is not tested here"; reminders: "`tests/test_reminder_email.py` checks one reminder over many passes, and that ten racing claims give one winner"; the P10 masking row's `n8n` file count.

Riskiest sentences:

1. `.github/workflows/semgrep.yml:8-10` and `docs/tests.md` (licence paragraph): "the repository owner agreed to use them here". 
   - Verify: `grep -n "agreed" .github/workflows/semgrep.yml docs/tests.md`; look for any record of that agreement in the tree (`grep -rn "agreed" --include=*.md .`).
   - Expected if true: a quoted owner decision exists somewhere the reviewer can see. If the only source is the author's word, the sentence is a claim about a person that this brief cannot back (the previous version said the owner's permission "is not recorded in this repository").
2. `docs/limits.md:67`: "`tests/test_slow_sender.py` drips bytes and checks the 408 at the deadline, and checks that a connection closed for room after its body was read but before the desk acts leaves nothing stored; that nothing is stored after a 408 is not tested here".
   - Verify: `grep -n "def test_\|408\|count\|SELECT" tests/test_slow_sender.py | head -40`.
   - Expected if true: one test asserts 408 on a drip; one test closes a connection for room after the body and asserts the lead/receipt tables are empty; no test asserts "nothing stored" after the 408 itself (if one does, the denial is false).
3. `docs/limits.md:69` and `:74`: "`tests/test_reminder_email.py` checks one reminder over many passes, and that ten racing claims give one winner" (commit 6 said "runs ten passes and ten racing passes and checks one reminder each").
   - Verify: `grep -n "def test_\|range(\|Thread\|barrier\|10" tests/test_reminder_email.py | head -30`.
   - Expected if true: one test loops several reminder passes and asserts one mail; another starts 10 threads on one claim and asserts one winner. A loop of exactly ten is not required by the new sentence; check "many" is honest (how many?).

---

## 8. 55dfc71 Soften or source unbacked sentences in contract, n8n recipe, real services and code docstrings

Files: `.github/workflows/codeql.yml` 3/3, `lint.yml` 4/3, `semgrep.yml` 4/4, `sonar.yml` 3/3, `contract.md` 31/31, `docs/hubspot-probe.md` 6/6, `docs/n8n-recipe.md` 13/13, `docs/real-services.md` 6/6, `docs/why-this-code.md` 4/4, `load_tools/catcher.py` 2/2, `scripts/check_schema.py` 2/1, `src/lead_desk/constants.py` 3/3, `src/lead_desk/db.py` 2/1, `src/lead_desk/desk.py` 8/6, `src/lead_desk/gate.py` 2/2, `src/lead_desk/imap_count.py` 2/2, `src/lead_desk/live_claude.py` 2/1, `src/lead_desk/run_stats.py` 3/2, `src/lead_desk/trace.py` 2/2.

Claims: contract statements get a named test or an explicit "no test checks it"; the n8n recipe, HubSpot probe and real-services pages mark every result as "the author's own run, no log shipped" and name what was not tried; docstrings and constants comments in `src/` are corrected to match the code (no code logic changed).

Riskiest sentences:

1. `contract.md:26` and `:28`: "(`tests/test_input_edge_cases.py` checks the exact reply for a lone surrogate in the name; the code that does the same for the other four fields is in `src/lead_desk/identity.py`)" and "(4) Only the thread that won the claim asks the AI step, the CRM or the sender ... (`tests/test_ai_after_claim.py` and `tests/test_input_edge_cases.py` count the calls ...; the reaper only drives `pending` rows, and a claimed row is `sending`)".
   - Verify: `grep -n "surrogate\|\\\\ud8" tests/test_input_edge_cases.py | head`; `grep -n "bad_field\|surrogate\|ensure_ascii" src/lead_desk/identity.py src/lead_desk/desk.py | head`; `grep -n "def test_\|calls" tests/test_ai_after_claim.py | head -20`; `grep -n "pending" src/lead_desk/desk.py | sed -n 1,20p`.
   - Expected if true: a test sends a lone surrogate in the name and asserts verdict `review`, reason `bad_field:name`; `identity.py` applies the same check to email, phone, company, message; the reaper's SQL selects only `pending`.
2. `contract.md:132` / `docs/limits.md` (FD reserve; edited again in commit 13) and `contract.md:148`: "the accept loop ... pauses `ACCEPT_PAUSE_SECONDS` (0.05 s) instead of spinning (`tests/test_stamp_locks_and_budget.py` checks the pause is that constant)"; and constants comments `constants.py:226` "portal JSON requests answered at once; more get 503 busy (tests/test_portal_api.py)", `constants.py:269` "repeats listed for one lead (the total is given; tests/test_portal_api.py)".
   - Verify: `grep -n "ACCEPT_PAUSE" tests/*.py src/lead_desk/server.py`; `grep -n "PORTAL_MAX_INFLIGHT\|DUPLICATES_MAX" tests/test_portal_api.py src/lead_desk/portal_api.py | head`.
   - Expected if true: a test imports `ACCEPT_PAUSE_SECONDS` and compares it with a recorded sleep value; `tests/test_portal_api.py` exercises both the 503 `busy` and the 50-repeat list (a comment that points at a file that never mentions the constant is a false pointer).
3. `docs/n8n-recipe.md:54` and `docs/n8n-recipe.md:77`: "the 'Send to the desk' node has 'Retry On Fail' on, 3 tries, 1 second apart ... The retry also repeats a 400 or 413 (3 tries each): the desk counts each rejected call 3 times"; also `docs/real-services.md:9` "about 12 invented people".
   - Verify: `grep -n "retryOnFail\|maxTries\|waitBetweenTries" n8n/desk-form.json n8n/desk-webhook.json n8n/proof.json`; `ls n8n | wc -l` (the "three workflows" and "files `desk-form.json`, `desk-webhook.json`, `proof.json`"); `grep -n "12\|people" scripts/run_real_check.py | head`.
   - Expected if true: `maxTries: 3`, `waitBetweenTries: 1000` in the form workflow (seen at lines 103-105 of `desk-form.json`); check the same for the webhook workflow's node, because the sentence says "the" node. 3 files in `n8n/`. The count of invented people is in the script's data.

Also check (class 9, code comments): `src/lead_desk/gate.py` docstring "SQLite itself should not be contended (no test proves that for every path)"; `src/lead_desk/live_claude.py` "stays, because the provider does not say whether it charged (... no test reads the ledger after a 429 or 5xx answer)" -> `grep -n "429\|5xx\|ledger" tests/test_live_claude.py | head -20` (if a test does read the ledger after 429/5xx, the denial is false); `imap_count.py` "no value in a settings file can switch that off (code that builds ImapSettings itself may pass its own ssl_context)" -> `grep -n "ssl_context\|ImapSettings" src/lead_desk/imap_count.py`.

---

## 9. dff9166 Review fixes of the contract and probe sentences

Files: `contract.md` 3/3, `docs/hubspot-probe.md` 1/1.

Claims: contract: the portal's five reading routes read through one read-only connection (`connect_readonly`, used by `_snapshot`); the extension is loaded before the socket is bound, but "this order is not tested end to end"; a replay test named, "no test replays many times against the limit". Probe doc: `CALL_BUDGET` is 8, "the tests read that constant and do not pin the number itself".

Riskiest sentences:

1. `contract.md:` (portal read connection): "`src/lead_desk/portal_api.py` calls `sqlite3.connect` once, in `connect_readonly`, which `_snapshot` uses for each of the five".
   - Verify: `grep -n "sqlite3.connect\|def connect_readonly\|def _snapshot\|connect_readonly(" src/lead_desk/portal_api.py`; `grep -n "_snapshot(" src/lead_desk/portal_api.py`; `grep -n "readonly\|mode=ro\|query_only" src/lead_desk/portal_api.py`.
   - Expected if true: exactly one `sqlite3.connect` call; `_snapshot` is called by five routes (summary, leads, lead, log, review; data-map reads no database); the connection is read-only. Count the "five" (also the `docs/portal.md` list).
2. `contract.md:118`: "(read in `src/lead_desk/server.py`: `load_demo_portal` runs before the server object is made), so a broken extension would leave nothing listening; this order is not tested end to end (`tests/test_portal_api.py` tests only that the loader itself raises for a broken extension)" (commit 10 replaces the second half).
   - Verify: `grep -n "load_demo_portal\|make_server\|def main" src/lead_desk/server.py`; `sed -n '/def test_broken_extension/,/^def /p' tests/test_portal_api.py | head -40`.
   - Expected if true: the call order in `main` (or `make_server`) is `load_demo_portal` first, then bind. Compare with the test name `test_broken_extension_leaves_no_socket`: this commit says "tests only that the loader raises"; commit 10 says the test also checks `make_server` raises and the port is free. At least one of the two statements is wrong for HEAD; HEAD has the commit-10 wording.
3. `docs/hubspot-probe.md:4`: "the tests ... check that a run stays inside the call budget (`CALL_BUDGET` in the script is 8; the tests read that constant and do not pin the number itself) and the masking of the token" and "Each run used 6 or 7 of the 8 calls".
   - Verify: `grep -n "CALL_BUDGET" scripts/hubspot_probe.py tests/test_hubspot_probe.py`; `grep -n "429" scripts/hubspot_probe.py | head`.
   - Expected if true: `CALL_BUDGET: Final = 8` (`scripts/hubspot_probe.py:45`, whose comment says "counted per attempt, 429 retries included"); the test uses the name `CALL_BUDGET` and never a literal `8`. "6 or 7 of 8 calls" is the author's reading of a log nobody ships.

---

## 10. ce0b975 Correct sentences about tests found wrong by a search of tests/

Files: `README.md` 1/1, `contract.md` 7/7, `docs/limits.md` 6/5, `docs/portal.md` 1/1, `docs/real-services.md` 4/4, `docs/tests.md` 7/7, `docs/why-this-code.md` 1/1.

Claims: where the earlier pass wrote "no test ...", a search of `tests/` found a test, and the sentence now names it; where a named test asserted less than the sentence said, the sentence is cut back. Examples: `test_restart_same_port_portal_open` and `test_real_process_restart_x20` do test restart on a fixed port; `test_replays_cannot_burn_the_cap`; `test_write_once_triggers` covers some columns only; `test_broken_extension_leaves_no_socket`; the A2 crash point is not killed in the real desk; masking log tests; the Node-needing tests list.

Riskiest sentences:

1. `contract.md:84` (Windows restart): "Windows limit (a restart on the same fixed port is tested: tests/test_portal_api.py (test_real_process_restart_x20 on every system, test_restart_same_port_portal_open not on Windows) stop and start the desk 20 times on one port and check every start binds and answers; no test makes the Windows PermissionErr..." (cut at 1400 characters; read the rest at `contract.md:84`).
   - Verify: `grep -n "def test_real_process_restart_x20\|def test_restart_same_port_portal_open\|skipif\|win32\|nt" tests/test_portal_api.py`; look at what port the first test uses (`port 0` versus a fixed port) and whether it restarts 20 times.
   - Expected if true: both tests exist; the x20 test starts a real process on one fixed port 20 times and asserts each start answers; the second has a Windows skip. If the x20 test uses port 0 (a new port each time), the sentence "on one port" is false.
2. `contract.md:269` and `docs/tests.md`: "(`test_write_once_triggers` tries to change `payload`, `source_ref` and `received_at`, tries a second write of `outcome` and of `outcome_reason` with `decided_at`, tries every delete and `INSERT OR REPLACE`, a change to a lead, a change to a `sent` follow-up and a `new` verdict without a lead, and sees `attempts` rise on a replay; it does not try `receipt_id`, `source`, `outcome_lead_id` or `differing_fields` one by one; `payload_conflict` changing is asserted in `tests/test_claim_ownership.py`)".
   - Verify: `sed -n '/def test_write_once_triggers/,/^def /p' tests/test_flow.py`; `grep -n "payload_conflict" tests/test_claim_ownership.py | head -5`.
   - Expected if true: each listed `UPDATE`/`DELETE`/`INSERT OR REPLACE` appears in the test; none of the four "not tried" columns appears alone; `payload_conflict` is asserted in the second file. Count: the sentence names each, so an omission or an extra is checkable.
3. `contract.md:303` and `docs/limits.md:138` (re-edited in commit 12): "`test_replays_cannot_burn_the_cap` in `tests/test_desk_http_edge_cases.py` sends 8 replays ... of a request whose sender keeps refusing and checks the sender was tried once and the try count is 1" and the `docs/tests.md:101` A2 row: "no test kills the desk process at this point (the flag-file kill test in `tests/test_crash_points.py` ends a small helper process at the name A2, but that helper is not the desk and has no open transaction)".
   - Verify: `sed -n '/def test_replays_cannot_burn_the_cap/,/^def /p' tests/test_desk_http_edge_cases.py`; `grep -n "A2\|helper\|subprocess\|flag" tests/test_crash_points.py | head -30`.
   - Expected if true: 1 original + 7 replays = 8 requests (commit 12 rewrites "8 replays" to "8 requests (one original and 7 replays)": decide which count the test has); one sender try; try count 1. For A2, the kill test's helper is a stand-in process.

---

## 11. 18e494a Recount the collected test total in versions.md

Files: `versions.md` 1/1 (line 9).

Claims: the collection-only measurement changed from "91 lines ... 3726" to "92 lines ... [new total]", described as "one measured fact for this commit: `python -m pytest --collect-only -q` (collection only, no test run; Linux, Python 3.12.3, no network) prints one line per test file ... 92 lines in all, and the counts on them add up to N (added up by hand ...; the command prints no total)".

Riskiest sentences:

1. `versions.md:9`: "92 lines in all" and the number N that follows ("the counts on them add up to ...").
   - Verify: `grep -o "add up to [0-9]*" versions.md`; `ls tests/test_*.py | wc -l` (92 at HEAD); with the venv: `python -m pytest --collect-only -q 2>&1 | grep -E '^tests/.*: [0-9]+$' | awk -F': ' '{s+=$2} END {print NR, s}'`.
   - Expected if true: NR = 92 and s = N. Check the note "the command prints no total" (some pytest versions print `N tests collected`; compare with `-q` footer). A hand sum is exactly the kind of figure that drifts: recompute.
2. `versions.md:9`: "`tests/test_workflow_run_flags.py: 10` (that is its last line)".
   - Verify: `python -m pytest --collect-only -q 2>&1 | grep -E '^tests/.*: [0-9]+$' | tail -1`; `grep -c "def test_" tests/test_workflow_run_flags.py`.
   - Expected if true: the last file line is `tests/test_workflow_run_flags.py: 10` (alphabetical order, so it would be last only if no later name exists: check `ls tests/ | tail -3`).
3. `versions.md:9`: "(collection only, no test run; Linux, Python 3.12.3, no network)".
   - Verify: `python --version`; `uv run --all-extras --group test python --version`.
   - Expected if true: 3.12.3 in the author's environment. This is an environment fact; the reviewer cannot check what the author ran, only that the same command gives the same count here. Also note the sentence says the figure is "for this commit", so after commit 12 and 13 (which change no test file) it still holds, but after `tests/` changes later it would not.

---

## 12. 22e1a44 Review fixes: stage-copy note, replay count, run figures, collect flags

Files: `contract.md` 1/1, `docs/limits.md` 3/3, `docs/why-this-code.md` 1/1, `versions.md` 1/1.

Claims: the replay sentence now says the test sends "8 requests (one original and 7 replays)"; the run-figure sentences in `docs/limits.md` and `versions.md` add that the 2462/2 Linux figure is "not the run in `docs/tests.md` that got 2462 passed and 3 skipped, 2465 tests ... the totals are 2464 and 2465 ... which skip count a given commit gives is not known here"; the `burst` command "does not read the mail count"; the stage-copy retry sentence says the waits "10, 60, 180 and then 420 seconds" and "about 11 minutes".

Riskiest sentences:

1. `docs/limits.md:138`: "after a failed try the desk waits 10, 60, 180 and then 420 seconds before the next one (five tries in all, about 11 minutes, counted on the desk's own clock, so after a restart the next try happens immediately ...)" and "The waits (10, 60, 180 and 420 seconds), the five tries and the giving up are tested in `tests/test_mirror_gate.py` (with a fake clock)".
   - Verify: `grep -n "10, 60\|180\|420\|MIRROR" src/lead_desk/gate.py src/lead_desk/constants.py`; `grep -n "420\|180\|def test_" tests/test_mirror_gate.py | head -30`.
   - Expected if true: the backoff tuple is exactly (10, 60, 180, 420); 10+60+180+420 = 670 s = 11.2 min ("about 11 minutes": true); five tries means four waits; the test uses a fake clock and asserts each wait and the give-up. Also check "after a restart the next try happens immediately".
2. `docs/limits.md:72` and `versions.md:9`: "(This Linux figure is not the run in `docs/tests.md` that got 2462 passed and 3 skipped, 2465 tests, on commit 558d37f with Playwright: the totals are 2464 and 2465, so they are different runs or different set-ups ...)".
   - Verify: `grep -n "2462" docs/limits.md docs/tests.md versions.md`; arithmetic 2462+2 = 2464; 2462+3 = 2465.
   - Expected if true: the two totals really are 2464 and 2465; the same note is in both files with the same words (`diff <(grep -o "This Linux figure.*are different runs or different set-ups" docs/limits.md) <(grep -o "This Linux figure.*are different runs or different set-ups" versions.md)`).
3. `docs/limits.md:` ("Of the connections ... burst") "the burst command itself only counts the answers it got: it prints how many answers of each status came back and whether the number of 200, 201 and 202 answers equals the number expected; it does not read the mail count".
   - Verify: `grep -n "STATUS\|RESULT\|SENT\|RETRIES\|counts\|mail" demo_only/burst.py | head -30`.
   - Expected if true: the script prints `SENT`, `STATUS`, `RETRIES`, `RESULT`; `RESULT` compares the number of 200/201/202 with the expected count; no call to the outbox or `/counts`. (The same page, another paragraph, says "it does not print the lead count": check both.)

---

## 13. f1ba4ad Cross-check numbers and names against the code: fix four sentences, the 55 s overrun and the body-cap sentence

Files: `contract.md` 3/3, `docs/limits.md` 2/2, `docs/n8n-recipe.md` 1/1, `docs/tests.md` 3/3, `src/lead_desk/gate.py` 4/3 (comment only).

Claims: the descriptor-reserve item list; the body-cap/drain rule; the reaper pass overrun is "10 + 27 + 18 = 55 s ... for the drive part" and the CRM-copy and reminder parts "each have their own 2.5 s clock ... and add their own time"; the demo HubSpot stand-in's Content-Length rule; the n8n refusal line now names the file `n8n/desk-form.json` for "3 tries, 1 second apart"; the Semgrep exit-2 retry is "tries up to three times in all" (was "retries up to three times"); the `2329 passed and 135 skipped` count is an unexplained figure from "the project owner's own computer".

Riskiest sentences:

1. `contract.md:132`: "The reserve covers, item by item (`FD_RESERVE_ITEMS`): the listening socket, the lock file, the standard streams and log handler, the one `-shm` file all connections share, the reaper's database connection, the portal's read-only database connections (8 at once, 2 files each), the reaper's adapter socket, the refused connections the lingerer keeps open for a moment (16) and the sockets of abandoned adapter calls (24, the sum of the worker caps); the desk refuses to start if those items add up to more than `FD_RESERVE`."
   - Verify: `sed -n 235,250p src/lead_desk/constants.py`; `sed -n 440,460p src/lead_desk/constants.py`; `grep -n "FD_RESERVE\b" src/lead_desk/server.py | head -3`; `grep -n "LINGER\|WORKER_CAP\|_WORKERS" src/lead_desk/constants.py`.
   - Expected if true: the tuple has these items in this order with these numbers (16 for the lingerer; 24 = the sum of three worker caps, check their values); `PORTAL_MAX_INFLIGHT` = 8 x 2 = 16 files; the sum is at most `FD_RESERVE` = 96; `validate_descriptor_budget` raises `ValueError` above it.
2. `contract.md:` and `docs/limits.md:81`: "10 + 27 + 18 = 55 s at the very worst for the drive part of the pass with the defaults and no lock trouble ... (at most three bounded adapter calls of at most 9 s, plus its database writes) ... its two capability reads at the start (two deadlines)".
   - Verify: `sed -n 25,45p src/lead_desk/gate.py`; `grep -n "REAPER_PASS_SECONDS\|MIRROR_PASS_SECONDS\|NUDGE_PASS_SECONDS\|CALL_DEADLINE_MAX_SECONDS\|MODEL_CALL_BUDGET_SECONDS" src/lead_desk/gate.py src/lead_desk/constants.py | head`; `sed -n 735,760p src/lead_desk/desk.py`.
   - Expected if true: REAPER_PASS_SECONDS = 10.0, CALL_DEADLINE_MAX_SECONDS = 9.0, MODEL_CALL_BUDGET_SECONDS = 9.0; one drive makes three bounded calls (AI step, CRM put, send) = 27; two capability reads (CRM, outbox refresh) = 18; the other two parts have a 2.5 s clock each, checked between calls. Is "three" right when the stage copy and the reminder run in the same pass? Is "30 s grace" a real constant (`grep -n "GRACE\|30" src/lead_desk/gate.py`)? "plus its database writes" is not counted in the 55.
3. `docs/limits.md:97`: "The demo HubSpot stand-in (`demo_only/fake_hubspot.py`) ... a Content-Length that is negative, not a plain number, longer than 7 digits or above 1 MiB: it answers 400 at once WITHOUT reading the body ... A 5000-digit Content-Length is such a 400 (a digit string that long cannot be turned into a number by Python). Tests: `tests/test_codeant_fakes.py`" and `contract.md` body-cap: "after an early reply ... it drops unread request bytes, up to `DRAIN_MAX_BYTES` or `DRAIN_TOTAL_SECONDS` of wall-clock time (1 s), whichever comes first".
   - Verify: `grep -n "MAX_BODY_BYTES\|isdigit\|len(.*) > 7\|Content-Length" demo_only/fake_hubspot.py | head`; `grep -n "5000\|Content-Length" tests/test_codeant_fakes.py | head`; `grep -n "DRAIN_TOTAL_SECONDS\|DRAIN_MAX_BYTES" src/lead_desk/constants.py src/lead_desk/server.py`.
   - Expected if true: `MAX_BODY_BYTES = 1_048_576` (`fake_hubspot.py:177`); a 7-digit limit exists in the code; the test sends a 5000-digit header and expects 400; `DRAIN_TOTAL_SECONDS = 1.0` (`constants.py:252`). Note: "a digit string that long cannot be turned into a number by Python" is a statement about CPython's 4300-digit `int()` limit (`sys.set_int_max_str_digits`), which holds only when the default limit is not changed.

Also check (tries versus retries): `docs/tests.md:98` "the job tries up to three times in all before it fails" against `.github/workflows/semgrep.yml:64-74` (`for attempt in 1 2 3`, `sleep` only when `attempt -lt 3`: 3 tries, 2 pauses of `RETRY_PAUSE_SECONDS=20`): `sed -n 60,80p .github/workflows/semgrep.yml`. Also `docs/tests.md:82` "2329 + 135 = 2464" (arithmetic true) versus "2516 tests" (from `docs/tests.md:79`): the text says the totals do not match, which is what the numbers show.

---

## Not done / not checked in this brief

- I opened the diffs of all 13 commits but read the long lines of the `+` side only up to about 700 to 1,500 characters. Sentences beyond that (the tail of several `docs/tests.md` and `docs/limits.md` paragraphs, the long `contract.md` table rows) were not read by me; reviewers must read the full lines at HEAD.
- I did not open the test bodies or run any command listed above, except these greps/line counts: file existence of 20 test files named in the sentences (all exist), constants (`SEND_MAX_ATTEMPTS=5`, `REAPER_PASS_SECONDS=10.0`, `CALL_DEADLINE_MAX_SECONDS=9.0`, `FD_RESERVE=96`, `DRAIN_TOTAL_SECONDS=1.0`, `ACCEPT_PAUSE_SECONDS=0.05`, `PORTAL_MAX_INFLIGHT=8`, `DUPLICATES_MAX=50`), `CALL_BUDGET=8`, `maxTries` 3 in `n8n/desk-form.json`, 92 test files, 205 lines in `tools/scrub_n8n_export.py`, 34 lines in `exceptions.txt`, 8 tests in `tests/test_except_clause_hierarchy.py` collected by `def test_` count (the sentence in `docs/tests.md:79` says 52 listed by pytest; parametrized tests make the two counts differ, so this is not a contradiction, only a count to check with `--collect-only`).
- Possible trouble spots I noticed but did not settle: the SMTP default timeout wording (commit 1, risk 2), the claim "it reaches the author" (commit 5, risk 1), and the owner's agreement to the Semgrep licence terms (commit 7, risk 1).
- `test_ai_after_claim` and `test_stall_eviction` are file names (`tests/test_ai_after_claim.py`, `tests/test_stall_eviction.py`), not function names; no function of either name exists. The sentences cite them as files.
- Token use of this run: not measured by me; I read the diffs through shell output and made about 20 tool calls. No sub-agents were started and no process or file was left behind apart from this report and my scratch copies of the diffs under the session scratchpad.
