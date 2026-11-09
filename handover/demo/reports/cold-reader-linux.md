# Cold reader on Linux: duplicate-proof-lead-desk (tarball dpld-final5b-a5cf0b3d0eec)

EVIDENCE RUNNER report. Facts only, no judgement of acceptability.
Run 2026-11-09 about 17:33 to 17:45 UTC (23:03 to 23:15 IST). Linux, root user, `python3` = 3.13.18 (not 3.12). Tarball unpacked only into `/tmp/ag/cold/stranger/`. Own venv created as the README says. Nothing in the tarball was changed (the venv, `data/` and `__pycache__` were created by the README steps). Raw logs: `/tmp/ag/cold/run.log` (install), `run2b.log` (start), `pytest.log` (full test run), `pytest2.log` (re-run of 5 failed tests).

## Step table

| # | README quote | Command | Result | What was unclear |
|---|---|---|---|---|
| 1 | "Linux and macOS (Python 3.12 matches the lock file; ...): `python3 -m venv .venv && . .venv/bin/activate`" | `python3 -m venv .venv && . .venv/bin/activate` | worked (exit 0) | The machine's `python3` is 3.13.18; README says "3.12 or newer is needed" and "3.12 matches the lock file", so I took 3.13 as allowed. Worked. |
| 2 | "`python -m pip install --require-hashes -r requirements-dev.txt` # only needed for the tests" | same | worked (exit 0). 18 packages installed (pytest 9.2.0, ruff, mypy, bandit ...). Some came from a local pip cache, so this run does not prove a clean download. | None. |
| 3 | "`scripts/start_all.sh keyed` # or: blind (logs go under ./data)" | `scripts/start_all.sh keyed` | FAILED, exit 126: `Permission denied`. The file is mode `-rw-rw-r--` (not executable) in the tarball. Same for `scripts/reset.sh`. | The README line cannot be run as written. I guessed `bash scripts/start_all.sh keyed`. |
| 3b | same | `bash scripts/start_all.sh keyed` | worked (exit 0). Printed "started: fakes (keyed outbox) pid 1633, desk pid 1634", ports 8765 and 8766, logs `data/fakes.log` and `data/desk.log`. Ports were free first (checked with `ss`, later `ss` turned out to be absent on the second check; the first check printed "ports free"). | README says "`start_all` prints them [the ports]": true. README text says logs under `./data`; the error log it names later is `data/desk.err.log`, while the script printed `data/desk.log` and `data/fakes.log` (see step 9). |
| 4 | "`export PYTHONPATH=src`" | `export PYTHONPATH=src` | worked | None. |
| 5 | "`python scripts/feed.py --source form --index 1`" (comment on the Windows block: "a web-form lead: verdict new") | same | worked, exit 0. Output: `canned-1 form -> 201 {"receipt_id": 1, "verdict": "new", "lead_id": "Lad086e39cdc3", "replayed": false}` | None. |
| 6 | same command a second time ("the same request id again: replayed true, nothing changes") | same | worked, exit 0. `canned-1 form -> 201 {"receipt_id": 1, "verdict": "new", ..., "replayed": true, "payload_matches": true}`. Matches the README text (201, replayed true). | "verdict new" in a replayed answer may read oddly (the README does say it answers 201 with `"replayed": true`). `payload_matches` is never explained. |
| 7 | "`python scripts/feed.py --source webhook --index 1`" ("the same person through the email door: verdict duplicate") | same | worked, exit 0. `canned-1 webhook -> 200 {"receipt_id": 3, "verdict": "duplicate", "lead_id": "Lad086e39cdc3", "differing_fields": [], "replayed": false}` | "receipt_id" jumped from 1 to 3 (2 was never shown; the README does not explain it). The README does not say what status the duplicate answers (200 here, 201 for new). |
| 8 | "`curl http://127.0.0.1:8765/counts ; curl http://127.0.0.1:8766/fake/outbox ; curl http://127.0.0.1:8766/fake/crm`" (Windows comment: received 2, new 1, duplicate 1; 1 email; 1 CRM row) | same three, with `-w` status | worked, all HTTP 200. counts: `received 2, new 1, duplicate 1, review 0, open 0, ... expected_match null, ok null`. outbox: `mode keyed, count 1`. crm: `count 1`. Matches the README comments. | `expected_match` and `ok` are null and not explained. Not a failure. |
| 9 | "**Is it running?** The desk answers 404 `{"error":"not_found"}` for `/` and `/health` on purpose" | `curl` on `/` and `/health` | worked: both HTTP 404 `{"error": "not_found"}` (note: a space after the colon, the README shows none). | README says "look at `data/desk.err.log`"; I did not need it and did not check that the file exists (after a normal run `ls data` showed it; see step 11, `data` listing was empty after reset). |
| 10 | "## The portal (read-only pages): `/ui/` shows the lead book in a browser" | `curl http://127.0.0.1:8765/ui` , `/ui/` , `/ui/index.html` | FAILED. `/ui` gives HTTP 308 (matches `contract.md`). `/ui/` gives HTTP 404 `{"error": "not_found"}`. `/ui/index.html` gives 404. The folder `src/lead_desk/portal/` that `contract.md` says holds the page files does not exist in the tarball (`ls src/lead_desk/` shows no `portal` folder; I only listed it, I read no code). | The README says `/ui/` shows pages in a browser; no page exists in this tarball. No browser was available, only curl. |
| 10b | README/contract list `/api/ui/...` routes | `curl` on `/api/ui/summary`, `/leads`, `/leads/Lad086e39cdc3`, `/review`, `/log`, `/data-map` | worked, all HTTP 200 JSON. summary 4911 bytes (counts received 2/new 1/duplicate 1, `reconciled true`, `refused_at_door 0`, followups sent 1). leads: 1 row (Ada Example, state `sent`, arrivals 2, repeats 1). lead detail 804 bytes (shows the full email, phone, company and message of the made-up lead). review: `items []`. log: 2 items (webhook duplicate, form new). data-map: `ai_step.mode recorded`, receives `lead_id`, `email_key`. | The README itself lists no routes ("The exact routes are in `contract.md`"); I got them from `contract.md` (README links to it). |
| 11 | "`scripts/reset.sh` # stops what start_all started and deletes the lead book" | `scripts/reset.sh` | FAILED, exit 126 `Permission denied` (not executable). | Same as step 3. |
| 11b | same | `bash scripts/reset.sh` | worked, exit 0, printed "reset done". Afterwards no desk or fake process of mine was left, port 8765 refused (curl exit 7), `data/` was empty. | None. |
| 12 | "`python -m pytest -q` # the tests" | `PYTHONPATH=src python -m pytest -q` (one full run) | FAILED (exit 1): `10 failed, 641 passed, 1 skipped, 2 xfailed in 371.21s`. Failures listed in the table below. | The README says the full suite passes except `test_hygiene_wordlist`. Here 10 failed. Also: the README's test list says "35 test functions (45 test cases)", while this run collected 654 items; the README does not explain the difference. |
| 13 | (not in README: re-run of the 5 non-hygiene failures, one time, to see if they were timing luck) | `pytest -q` on the failed test files/tests | 5 failed again, 23 passed in 17 s. | Not a README step. Shows the 5 behaviour failures repeated on a second run. |

## The 10 failed tests (one full run; reasons are the first assertion line of each)

| Test | Reason shown |
|---|---|
| `test_flow.py::test_failed_retry` | `('pending','refused') == ('failed','refused')`: state is `pending`, test expected `failed`. Failed again on re-run. |
| `test_flow.py::test_retry_twice_concurrent` | same assertion. Failed again on re-run. |
| `test_infra.py::test_demo_adapters` | `'unknown' == 'failed'`. Failed again on re-run. |
| `test_hardening_cloud_b.py::test_f14_lock_file_unopenable` | assertion on the text "another desk is using this database": the message was printed where the test expects it not to be. Failed again on re-run. I ran as root (uid 0); I did not test whether that matters. |
| `test_server_hardening.py::test_reply_write_fails_after_commit_followup_still_runs` | state `pending`, expected `sent`. Failed again on re-run. |
| `test_mutants.py::test_mutant_no_claim` | the mutation guard expected "emails == 1" and got the same `pending` vs `failed` message as `test_failed_retry`. (Not re-run alone.) |
| `test_hygiene.py::test_no_control_characters_in_markdown` | `git ls-files` exit 128: the tarball has no `.git` folder. |
| `test_hygiene.py::test_sh_blobs_no_cr` | same cause (no `.git`). |
| `test_hygiene.py::test_hygiene_scan_public` | `git grep failed (128): fatal: not a git repository`. |
| `test_hygiene.py::test_hygiene_wordlist` | "set HYGIENE_WORDLIST to the private word list": the README says this one is expected to fail. |

The README says tests "set the path for their own processes" and does not say the hygiene tests need a git checkout, or that the tarball has no git history. `git` 2.43.0 is installed.

## Every step that failed or was unclear

1. `scripts/start_all.sh keyed` and `scripts/reset.sh` as written in the README fail with `Permission denied` (files are not executable in the tarball). Worked with `bash` in front (a guess).
2. `/ui/` (README "The portal") returns 404; no portal page files exist in the tarball (`src/lead_desk/portal/` missing). Only the JSON routes `/api/ui/*` answer.
3. Full `pytest -q`: 10 failures (see table). 5 behaviour failures repeated on a second run (`test_failed_retry`, `test_retry_twice_concurrent`, `test_demo_adapters`, `test_f14_lock_file_unopenable`, `test_reply_write_fails_after_commit_followup_still_runs`); `test_mutant_no_claim` fails with the same symptom; 3 hygiene tests fail because there is no `.git` in the tarball; `test_hygiene_wordlist` fails as the README warns.
4. Python: machine `python3` is 3.13.18; README text says 3.12 matches the lock file (3.12 not available as `python3` here; I did not look for `python3.12`).
5. Unexplained words/numbers: `payload_matches`, `expected_match`/`ok` null, why `receipt_id` goes 1 then 3, "verdict new" shown on a replay, the 654 collected tests against the README's "35 test functions (45 test cases)".
6. README text between lines for the Windows reset step is garbled (`scripts` then a line break then `eset.ps1`, a stray carriage return). Only a Windows reader is affected; I did not run it.
7. The README names `data/desk.err.log` for troubleshooting, while `start_all.sh` printed `data/desk.log` and `data/fakes.log`. I did not check whether `desk.err.log` exists.
8. The pip install used a local cache for some packages, so it does not show a clean download from the internet.

## What I could not do

- Open the portal in a browser (curl only; and no page files exist anyway).
- Run the Windows commands, the `blind` mode, `video_crash.py`, n8n, Docker steps.
- Pass the three hygiene tests: they need a git checkout, which the tarball does not contain; I did not create one (not in the README).
- Check whether the 5 repeated failures depend on running as root or on Python 3.13; not tested.

## Process check

My processes: fake server (pid 1633) and desk (pid 1634) were stopped by `bash scripts/reset.sh`; pytest runs ended on their own. After my last command: `ps` showed no `lead_desk`, `fakes_server` or pytest process started by me; `data/` empty; port 8765 refused. `ps` still showed pytest processes of other runs (pid 19014/19016 under `/tmp/linux-ev/wB`, pid 21126/21127 using `/tmp/dpld-venv`); they are not mine and I did not touch them. Checkpoint note: `/home/user/build/cold-checkpoint.md`.
