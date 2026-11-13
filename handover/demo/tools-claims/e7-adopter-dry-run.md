# E7 adopter dry run, README "Try it" (Linux block)

EVIDENCE RUNNER: I ran and recorded; I did not judge. Studio folder does not exist in this container, so no bible/R-number lookups (none cited).

## What was not done literally / not checked (read first)
* Step 3 `python3 -m venv .venv && . .venv/bin/activate` was NOT run. As the brief requires, `PATH=/tmp/work/fresh-venv5/bin:$PATH` stood in for it (`which python` -> /tmp/work/fresh-venv5/bin/python, Python 3.12.3). So the README's venv-creation line is untested here. Steps 1-2 (GitHub Code button, `git clone`) were replaced by `git clone /tmp/v8work /tmp/e7-work` plus `cp -a` of the working tree (the cp printed two "same file" errors for .git pack files; harmless).
* The 90-second reminder was NOT waited for. Right after the leads, `/fake/outbox` shows `"reminders": 0`, `"count": 1`; `/counts` has no reminder field.
* Windows block not run. macOS not run. `/health` and `/` 404 were checked once each (head of response only).
* Ran twice (second run after I added a `ps` line to step 12b). Run 1 log: /tmp/work/d/e7-raw-run1.log. Final log: /tmp/work/d/e7-raw.log. Both gave the same results; lead ids differ (random). Quoted outputs below are from run 1 unless noted.
* The curl progress meter in raw log rows is an artefact of capturing output to a file (curl shows it when stdout is not a terminal); not a README difference.

## Result: 0 MISMATCH rows. Every step matched. Observations are listed after the table.

| Step | Command (as written) | README says | Really happened | Verdict | Replacement words |
|---|---|---|---|---|---|
| 4 | `bash scripts/start_all.sh keyed` | starts demo servers and desk in background, returns at once | printed `started: demo servers (keyed outbox) pid 21363, desk pid 21364`, ports line (desk 8765, demo 8766), logs line; exit 0 | MATCH | none |
| 5 | wait loop then `curl -i http://127.0.0.1:8765/counts` | first line starts "HTTP/1", has 200, numbers all 0 | loop ended at i=2; `HTTP/1.0 200 OK`; body `{"received": 0, "new": 0, "duplicate": 0, ...}` all 0; exit 0 | MATCH | none |
| 6 | `python scripts/feed.py --source form --index 1` | prints 201 ... "verdict": "new" | `canned-1 form -> 201 {"receipt_id": 1, "verdict": "new", "lead_id": "L46bd50630b5d", "replayed": false}`; exit 0 | MATCH | none |
| 7 | same command again | 201 and "replayed": true, nothing changes | `201 {"receipt_id": 1, "verdict": "new", ..., "replayed": true, "payload_matches": true}`; exit 0 | MATCH | none |
| 8 | `python scripts/feed.py --source webhook --index 1` | "verdict": "duplicate" | `200 {"receipt_id": 3, "verdict": "duplicate", "lead_id": "L46bd50630b5d", "differing_fields": [], "replayed": false}`; exit 0 | MATCH | none (note: status is 200, README does not name a status for this line; receipt_id is 3, not 2) |
| 9 | `curl http://127.0.0.1:8765/counts` | received 2, new 1, duplicate 1 | `{"received": 2, "new": 1, "duplicate": 1, "review": 0, "open": 0, ..., "pending_followups": 0, "failed_followups": 0, ...}`; exit 0 | MATCH | none |
| 10 | `curl http://127.0.0.1:8766/fake/outbox` | "count": 1, one email, reminder later | `{"mode": "keyed", "count": 1, "reminders": 0, "messages": [{"key": "L46bd50630b5d", "to": "Ada@example.com", "subject": "Thanks for getting in touch, Ada Example"}]}`; exit 0 | MATCH | none |
| portal | `curl -i http://127.0.0.1:8765/ui/` | portal page at /ui/ | `HTTP/1.0 200 OK`, `text/html`, 5156 bytes, `<title>Lead Desk</title>`; exit 0 (HTML only fetched, not rendered; no browser, so overview/leads/needs pages not looked at) | MATCH (page served; content not visually checked) | none |
| 404 claim | `curl -si /` and `/health` | no page at `/` or `/health`, 404 | both `HTTP/1.0 404 Not Found` | MATCH | none |
| files | `ls -l data`, `head data/desk.log` | `data/desk.log`; `data/desk.err.log` on Windows | desk.log exists (`desk listening on http://127.0.0.1:8765`); desk.err.log does not exist on Linux; also present: desk.sqlite3 (+-wal, -shm, .lock), desk.pid, fakes.log, fakes.pid | MATCH | none |
| 12 | `bash scripts/reset.sh` | stops what start_all started, DELETES records and logs (only inside ./data) | printed `reset done`; exit 0; `ls -la data` afterwards shows an empty folder | MATCH | none |
| after reset | ps by saved pids; `curl /counts` | stops the programs | pids 21745/21746 (run 2) show state `Z`, `[python] <defunct>`: stopped but not yet collected by their parent (my bash script, which did not `wait`); curl exit 7 (connection refused). No lead_desk/fakes_server process remained | MATCH | none |

## Observations (not mismatches)
1. A first-time reader who copies line 5 sees one more thing in a terminal: nothing differs; the README's "numbers are all 0" is true.
2. `reset.sh` treats a stopped-but-uncollected process as gone (state Z); my `kill -0` check still said "alive" for those two pids, which is why run 1 printed "STILL ALIVE" (run 1 log, step 12b). Run 2 shows the state is Z. Not a README issue.
3. README step order "reset" is run while desk is up; the script stops the processes itself, as written. I did not run reset with the desk already stopped.
4. `desk.pid` and `fakes.pid` in data/ were created by start_all and removed by reset, as the README's reset-refusal paragraph implies. I did not trigger any of the reset refusal codes (2-6); not checked.

## Script
Full script: /tmp/e7-work/e7-run.sh (run as `timeout 120 unshare -n python3 .../scratchpad/lo_up_exec.py /usr/bin/bash /tmp/e7-work/e7-run.sh`, exit 0). Raw log: /tmp/work/d/e7-raw.log (run 1: /tmp/work/d/e7-raw-run1.log).

## Cleanup
No process of mine remains (`ps aux | grep -E "lead_desk|fakes_server"` printed nothing; the namespace is gone). `__pycache__` folders under /tmp/e7-work deleted. data/ is empty. Repository tracked files not changed (only the untracked e7-run.sh added in the clone).
Files changed: none in /tmp/v8work. Head SHA: not recorded (clone of the working tree; not asked). EGM: skipped, evidence-runner brief, reviewers judge this output. My own token use: not measured.
