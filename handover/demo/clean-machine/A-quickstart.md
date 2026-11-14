# Agent A: README quick start, python3.12 then python3.13

Head of the clone: f3c39cf (matches the brief). Machine: clean Linux, no packages installed beyond the Python venv. <scratch> = my own folder under the cm1 work area. One fresh clone per Python version (py312, py313), one new .venv inside each clone, nothing installed with pip (the README says the desk needs no extra packages).
Note on the brief: it gave no repository address. I used the origin of the local demo repo clone found in the home folder (read access, no login). Anonymous clone worked in about 1 s.
Not available to me: the studio folder (bible, memory, handoff), so no R-numbers could be looked up or cited. EGM skills not run: this was a run-and-record task, not a design or code change (EGM skipped: read-only run of documented commands, nothing in the repo edited).

## Result in one line
Every README Linux quick-start step returned rc 0 under both versions, with the output the README describes. No step failed. Findings below are small wording or clarity points only.

## Steps (same 13 steps for both versions; wall time in seconds; rc taken from the command itself)
Python 3.12 = 3.12.3 (system), 3.13 = 3.13.18. Runner script: <scratch>/run.sh (each README line run with eval in one bash shell, one terminal, venv active). Raw logs: <scratch>/log312.txt and <scratch>/log313.txt.

| # | Command (README line) | 3.12 rc/wall | 3.13 rc/wall |
|---|---|---|---|
| 1 | interpreter -V | 0 / 0s | 0 / 0s |
| 2 | README 57: `<python> -m venv .venv && . .venv/bin/activate` (README writes `python3`; I wrote the full interpreter path to select the version) | 0 / 3s | 0 / 3s |
| 3 | check: which python, python -V, pip --version (my addition, read-only) | 0 / 0s | 0 / 0s |
| 4 | README 58: `export PYTHONPATH=src` | 0 / 0s | 0 / 0s |
| 5 | README 59: `bash scripts/start_all.sh keyed` | 0 / 0s | 0 / 0s |
| 6 | README 60: wait loop then `curl -i .../counts` | 0 / 1s | 0 / 1s |
| 7 | README 61: feed form index 1 | 0 / 0s | 0 / 0s |
| 8 | README 62: same again | 0 / 0s | 0 / 0s |
| 9 | README 63: feed webhook index 1 | 0 / 0s | 0 / 0s |
| 10 | README 64: curl counts | 0 / 0s | 0 / 0s |
| 11 | README 65: curl outbox | 0 / 0s | 0 / 0s |
| 12 | README 66: `bash scripts/reset.sh` | 0 / 2s | 0 / 1s |
| 13 | after reset: list data folder, git status (my addition) | 0 / 0s | 0 / 0s |

## Output tails (python 3.12 run; 3.13 identical except values noted)
- Step 5: `started: demo servers (keyed outbox) pid 1175, desk pid 1176` / `ports: desk 8765, demo CRM and outbox 8766 ...` / `logs: data/fakes.log and data/desk.log`
- Step 6: first line `HTTP/1.0 200 OK`, header `Server: lead-desk Python/3.12.3` (3.13: `Python/3.13.18`); body `{"received": 0, "new": 0, "duplicate": 0, "review": 0, "open": 0, ... "reaper_running": true, ... "ok": null}` (all counters 0, as README says). The wait loop took 1 s.
- Step 7: `canned-1 form -> 201 {"receipt_id": 1, "verdict": "new", "lead_id": "Ledcbe0b19e24", "replayed": false}` (3.13: lead id L370d27ba6dd5)
- Step 8: `canned-1 form -> 201 {"receipt_id": 1, "verdict": "new", ..., "replayed": true, "payload_matches": true}`
- Step 9: `canned-1 webhook -> 200 {"receipt_id": 3, "verdict": "duplicate", "lead_id": "Ledcbe0b19e24", "differing_fields": [], "replayed": false}`
- Step 10: `{"received": 2, "new": 1, "duplicate": 1, "review": 0, "open": 0, ... "pending_followups": 0, "failed_followups": 0, "unknown_followups": 0, ...}` matches README ("received 2, new 1, duplicate 1").
- Step 11: `{"mode": "keyed", "count": 1, "reminders": 0, "messages": [{"key": "...", "to": <made-up address of Ada>, "subject": "Thanks for getting in touch, Ada Example"}]}` matches README ("count": 1).
- Step 12: `reset done`
- Step 13: data folder empty, git status clean (the .venv is not listed, so it is ignored by git).
- After each run: process list checked for lead_desk and fakes_server: none left. Ports 8765/8766 were free before the first run and after each reset (the second run started on them without trouble).

## Not run, on purpose
- The portal page (README line 24, browser) was not opened: no browser step is in the Linux block; I did not request it.
- No pytest at all: the README quick start gives no test command (the test command is under "Tests and more commands" and needs the dev lock file; that is agent B's task).
- Windows block: not applicable (Linux).
- Blind mode (`start_all.sh blind`), the 404 for `/` and `/health`, the reset refusal exit codes 2 to 6: not tried, not part of the quick-start steps.
- `sudo apt install python3-venv` (README line 52): not needed, venv creation worked with both interpreters.
- `python3` itself (the exact word in README line 57): I used the explicit 3.12 and 3.13 paths. What plain `python3` points to on this machine was not tested.

## Findings (all minor; none blocked the quick start)
F1. README line 57, `python3 -m venv .venv`: a stranger with several Pythons gets whichever `python3` is first on the path. README line 47 says "Python 3.12 or newer" and line 130 says only 3.12 (Linux) and 3.13 (Windows) were tried for tests. Both 3.12.3 and 3.13.18 worked for the quick start here, so the "3.12 or newer" claim holds for these two versions only. Stranger would do: run `python3 -V` first; the README does not say to.
F2. README lines 61 and 63: the README comment for line 61 says "prints 201 ... "verdict": "new"", which matches. The webhook feed (line 63) actually prints status 200, not 201, with receipt_id 3. README line 63's comment names only the verdict, so it is not wrong; a stranger comparing status codes may expect 201 for every feed line. Proposed change to README line 63 comment, old words: `same person through the other door: "verdict": "duplicate"`; new words: `same person through the other door: 200 and "verdict": "duplicate"`.
F3. Receipt numbers: the webhook answer shows "receipt_id": 3 although only two requests were sent by the stranger and counts say received 2. The README line 64 comment explains the repeated request is not counted, but does not say why the receipt number skips 2. A stranger may read it as a lost request. Not explained anywhere in the quick start text.
F4. README line 60: when output goes to a file or a pipe, curl prints its progress table (the `% Total ... Dload` lines) into the output. This appears only because my runner captured output to a file; in a terminal curl without `-s` also shows it on a screen unless the output is a pipe. A stranger copying lines 64 and 65 into a terminal will see a progress table above the JSON. Possible new words: add `-s` to the curl commands on lines 64 and 65 (line 60 already uses `-sf` in the loop but its final `curl -i` has no `-s`).
F5. README line 59 comment says the script "starts the demo servers and the desk in the background". The start script itself returns after 0 s; the desk was ready at the first check (1 s total in the wait loop on both versions). No gap found; recorded as a timing fact.
F6. README 3.13 run: venv pip is 26.2.2 (3.13) versus 24.0 (3.12). Nothing was installed with pip, so this had no effect; recorded because README line 130 says a hash mismatch can appear with the wrong Python version, and that was not exercised.

## Hygiene and process
- No push, no clone edits (git status clean after each run), no secrets, no spend, no prompt appeared (no y/yes typed, no host typed), loopback only.
- Processes started: the two demo servers and the desk per run (stopped by reset.sh, verified none left). No sub-agents, no background loops left.
- Files created by me: the two clones, run.sh and two logs in <scratch>, and this report.
- Not done: studio-rule lookups (no access to the studio folder), so R-numbers: none cited.
- Tokens: not measured by me.
- Head SHA: f3c39cf (both clones).
