# Agent C: end-to-end scenario report

Head under test: f3c39cf (fresh clone into <scratch>/C/repo, not edited, not pushed).
Environment: python3.12 (3.12.3), fresh venv made by python3.12 -m venv; network namespace made with unshare -n, then the loopback interface brought up by a small script; the interface list inside it was only "lo". Nothing could leave the machine. No prompt appeared at any point. No spend, no live model, no real mail. Made-up canned leads only.
Studio notes: the studio folder with the rule list and topic notes is not present in this environment, so no R-numbers were looked up or cited (rule 1 not satisfiable here). EGM skipped: read-only evidence run, no plan, code or document was produced for the project (rule 13 permits skipping for a read-only task).
Raw logs (command, rc, wall time, output tail per step): <scratch>/C/aux/raw-run1.log (first run) and <scratch>/C/aux/raw.log (second run).

## Result in one line
The README-literal path works for the first half (one lead through both doors). The documented crash command, run exactly as written, does NOT start (finding F1). With the one-word fix in the environment setting, the crash, restart and re-send ended with exactly one CRM contact and one mail per distinct person.

## Run 1: commands exactly as the README and docs/tests.md give them
| Step | Command | rc | Wall | Outcome |
|---|---|---|---|---|
| venv | python3.12 -m venv .venv, then activate | 0 | 5.4 s | ok |
| start | PYTHONPATH=src, bash scripts/start_all.sh keyed | 0 | 0.18 s | printed "started" with two process ids and the ports |
| form 1 | scripts/feed.py --source form --index 1 | 0 | 0.11 s | 201, verdict new, replayed false |
| form 1 again | same command | 0 | 0.11 s | 201, replayed true, payload_matches true |
| webhook 1 | scripts/feed.py --source webhook --index 1 | 0 | 0.11 s | 200, verdict duplicate |
| counts | curl counts page | 0 | 0.01 s | received 2, new 1, duplicate 1 |
| outbox | curl outbox page | 0 | 0.01 s | count 1 |
| stop desk | kill -TERM on the pid in the pid file | 0 | 1.5 s | stopped |
| crash scene | PYTHONPATH=src python scripts/crash_desk.py (docs/tests.md line 26 and the script's own header) | 1 | n/a | FAILED to start, see F1 |
| arm and feed form 2 | flag file D2, feed.py form index 2 | 1 | 0.2 s | connection refused (nothing was listening) |

Because the desk was down, run 1 never reached the crash. Counts after the failed crash scene were unchanged: mail 1, CRM 1. Run 1 then restarted the desk normally and went on; its later numbers are the same kind as run 2 and are not used below. Reset ran with rc 0.

## Run 2: same steps, crash scene started with the environment setting PYTHONPATH=src:. (the only change)
Every stage, taken by one small read-only script (<scratch>/C/aux/snap.py: the counts page, the demo mail count, the demo CRM count, and row counts read from the desk's database opened read-only).

| Stage | received | new | duplicate | mails | CRM contacts | receipts (db rows) | leads | follow-ups (state) |
|---|---|---|---|---|---|---|---|---|
| S0 after start | 0 | 0 | 0 | 0 | 0 | 0 | 0 | none |
| S1 form lead 1 (Ada) | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 sent |
| S2 same request again (replay) | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 sent |
| S3 webhook lead 1 (same person, other door) | 2 | 1 | 1 | 1 | 1 | 2 | 1 | 1 sent |
| S4 desk stopped, crash_desk running | 2 | 1 | 1 | 1 | 1 | 2 | 1 | 1 sent |
| S5 form lead 2 (Grace) sent with D2 armed; desk ended with "simulate crash", exit code 137 | counts page unreachable | - | - | 2 | 2 | 3 | 2 | 1 sent, 1 sending |
| S6 desk restarted (python -m lead_desk.server) | 3 | 2 | 1 | 2 | 2 | 3 | 2 | 1 sent, 1 pending |
| S7 form lead 2 re-sent (same request number) | 3 | 2 | 1 | 2 | 2 | 3 | 2 | 2 sent |
| S8 webhook lead 2 (other door) | 4 | 2 | 2 | 2 | 2 | 4 | 2 | 2 sent |
| S9 after 15 more seconds | 4 | 2 | 2 | 2 | 2 | 4 | 2 | 2 sent |

Final: exactly one CRM contact and exactly one mail per distinct person. Mail recipients: Ada's address once, Grace's address once. CRM rows: Ada once, Grace once. Review 0, open 0, unknown 0, failed 0.
Observations (facts only):
* At S5 the mail for Grace had already left (mail count 2) and the follow-up was still marked "sending" in the desk's records: this is the D2 moment. The re-sent request at S7 was answered with replayed true, and the follow-up went from pending to sent without a third mail (the demo mail system was in keyed mode).
* The feed call that armed D2 got its normal 201 answer; the desk ended afterwards (the crash happened after the answer, in the follow-up work).
* Receipt ids are not consecutive (Ada's webhook got receipt number 3 after a replay at number 1; Grace's webhook got 6 after 4). The database holds 4 receipt rows at the end, equal to the received counter. The README does not say receipt numbers are gap-free.
* Only keyed mail mode and the default (keyed) CRM were run. Blind mail and blind CRM were not run.
* Reset (bash scripts/reset.sh) rc 0 "reset done", 1.3 s. After it: the desk port and the demo server port both refused connections (curl rc 7); a process list search for the desk, the demo server and the crash script found none; the data folder kept only my two log files (crash_desk.log, desk2.log), which are not created by the scripts (my redirect targets). The whole network namespace also ended with the driver.
* Process cleanup: every process was started inside the private namespace under its own session (setsid); the restarted desk and the crash desk were stopped by exit/reset; no other process was touched, no pkill used.

## Findings
F1 (README line 59 area for start, docs/tests.md line 26, header of scripts/crash_desk.py): the crash command as documented, PYTHONPATH=src python scripts/crash_desk.py, ends at once with "the folder demo_only is missing" (ModuleNotFoundError for demo_only, then RuntimeError from the loader), exit code 1. A stranger who follows the crash line gets a stack trace, and a crash test that never runs. The start script sets PYTHONPATH=src:. but docs/tests.md and the script header say src only. Would change: in docs/tests.md line 26 and the header line in scripts/crash_desk.py, old words "PYTHONPATH=src python scripts/crash_desk.py" new words "PYTHONPATH=src:. python scripts/crash_desk.py" (Windows: "src;."). The README sentence about Windows "src;." is already there for "two needed".
F2 (docs/tests.md line 26): the crash scene text does not say the normal desk must be stopped first (both want the same port), nor how to stop it only (reset.sh also deletes the records, so it cannot be used for that). A stranger would not know to stop the one desk process by its pid in data/desk.pid. Also the text does not say how to restart the desk afterwards, or that a restarted desk started by hand lacks the start script's demo settings (leadflow file, reminder address) unless they are exported. In run 2 the restarted desk was started with only PYTHONPATH=src:. so the lead-flow feature (owner, stage, reminder) was off for the restart; the counts still matched. Would add one sentence after line 26 naming these steps.
F3 (README line 60): the wait-and-curl one-liner is correct; no issue. Not a finding, recorded because it was run as written.
F4 (not checked): with the README's own start command the crash/restart was only run once, at D2. The other nine points, blind mail and blind CRM were not run (tests in docs/tests.md cover them; I did not run the pytest suite).

## Not checked
The portal pages in a browser; Windows commands; blind mode; the other crash points; the demo servers' own logs (not read); behaviour on a second restart; concurrency (two leads at once).

## Files changed
None in the clone. Created outside it: <scratch>/C/aux/driver.sh, snap.py, raw.log, raw-run1.log, and this report.
Head SHA: f3c39cf.
Token use: about 60 thousand tokens, one model tier (Sonnet 5.5), no sub-agents.
