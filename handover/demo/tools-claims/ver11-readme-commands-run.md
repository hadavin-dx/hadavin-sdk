# out-v11: README command run (Linux, scratch copy /tmp/run19, python /tmp/work/fresh-venv5/bin/python 3.12.3)
Studio rules cited: R-numbers not looked up (task was a run-and-record; I did not grep bible\RULES.md). EGM skipped: read-only run, no files changed except /tmp/run19 and this file.
Setup notes: no `unshare` used (all traffic was 127.0.0.1 only). Venv step replaced by PATH=fresh-venv5/bin (as instructed). No prompts occurred. README has NO fenced blocks (commands are 4-space indented); the crash command is NOT in README.md but in docs/tests.md line 26; I ran it from there.
Exit codes: for the first pass (start, wait-loop, feed x3, counts, outbox) my wrapper lost the exit code, so I re-ran the repeatable ones (counts, feed replay, outbox) and recorded exit codes; start_all rc=0 was captured. The very first feed (new) exit code was not captured (output matched).

| # | command | exit | first output line (verbatim) | README sentence matches? |
|---|---|---|---|---|
| 1 | python3 -m venv .venv && . .venv/bin/activate / export PYTHONPATH=src | not run (used given venv instead) | - | - |
| 2 | bash scripts/start_all.sh keyed | 0 | started: demo servers (keyed outbox) pid 305, desk pid 306 | yes (returns at once, background) |
| 3 | wait loop + curl -i http://127.0.0.1:8765/counts | 0 (200 seen) | HTTP/1.0 200 OK | yes; first line is "HTTP/1.0 200 OK" (README says starts with "HTTP/1", ok); numbers all 0 shown later in crash run (received 0); in first run I did not print the body of the all-zero check |
| 4 | feed.py --source form --index 1 (1st) | not captured | canned-1 form -> 201 {"receipt_id": 1, "verdict": "new", "lead_id": "L2f1e1c84f64c", "replayed": false} | yes |
| 5 | same again (2nd) | 0 | canned-1 form -> 201 {"receipt_id": 1, "verdict": "new", "lead_id": "L2f1e1c84f64c", "replayed": true, "payload_matches": true} | yes: 201, replayed true, same receipt 1 |
| 6 | feed.py --source webhook --index 1 | not captured first time; 0 on rerun | canned-1 webhook -> 200 {"receipt_id": 3, "verdict": "duplicate", "lead_id": "L2f1e1c84f64c", "differing_fields": [], "replayed": false} | yes duplicate. Receipt id is 3, not 2: the replay used up number 2, exactly as README says ("numbers can skip") |
| 7 | curl http://127.0.0.1:8765/counts | 0 | {"received": 2, "new": 1, "duplicate": 1, "review": 0, ... "pending_followups": 0 ...} | yes: 2 / 1 / 1 |
| 8 | curl http://127.0.0.1:8766/fake/outbox | 0 | {"mode": "keyed", "count": 1, "reminders": 0, "messages": [{"key": "L2f1e1c84f64c", "to": "Ada@example.com", "subject": "Thanks for getting in touch, Ada Example"}]} | yes count 1 |
| 8b | extra: outbox again after ~95 s | 0 | {"mode": "keyed", "count": 2, "reminders": 1, ... "nudge:L2f1e1c84f64c", "to": "reminder@example.test" ...} | yes: reminder email after 90 s, as README says |
| 9 | bash scripts/reset.sh | 0 | reset done (printed twice) | yes; no desk/fakes process left (ps count 0) |
| 10 | (docs/tests.md) PYTHONPATH=src:. python -m demo_only.fakes_server --outbox keyed (nohup, own PID) | n/a running | fakes server keyed on port 8766 | yes |
| 11 | (docs/tests.md) PYTHONPATH=src:. python scripts/crash_desk.py (nohup, own PID) | n/a running | crash flag file: data/crash.flag  (write a point name such as D2 into it to arm the crash) | yes; flag path is relative (data/crash.flag) |
| 12 | echo D2 > data/crash.flag, then feed.py --source form --index 1 | 0 | canned-1 form -> 201 {"receipt_id": 1, "verdict": "new", "lead_id": "L66d3c5449d8f", "replayed": false} | desk log then shows "simulate crash"; desk process gone; outbox count 1 (email had been sent). Exit code of the desk (137 per docs) NOT captured (started in another shell) |
| 13 | restart crash_desk.py, replay feed --index 1 | 0 | canned-1 form -> 201 {"receipt_id": 1, "verdict": "new", "lead_id": "L66d3c5449d8f", "replayed": true, "payload_matches": true} | after restart: counts received 1 / new 1; outbox still count 1 with reminders 0, same key. So one email, one lead after crash at D2 |
| 14 | stop commands | kill by own PIDs, no error | - | processes gone; scratch data/ removed |

Receipt ids seen: normal run 1 (new), 1 (replayed), 3 (webhook duplicate, 2 consumed by replay); crash run 1 and 1 (replayed).
Windows/PowerShell commands (py -3 -m venv, Set-ExecutionPolicy, Activate.ps1, start_all.ps1, Invoke-WebRequest, reset.ps1, the manual python start): not run.
Not checked: `sh scripts/start_all.sh` refusal (exit 2); reset.sh refusal cases 2-6; the 3 s portal /ui/; the crash desk's real exit code; the hostile/all-zero counts body in the first run (seen in the crash run instead). README.md says nothing about crash_desk (it points to docs/tests.md); the "PYTHONPATH=src:." form appears in docs/tests.md and contract.md, not README.
Mismatches found: none. Tokens: small (~25k).
Files changed: /tmp/run19 (scratch, data/ deleted), /tmp/work/d/out-v11.md, temp logs /tmp/run19-*.log/pid. Head SHA: no git repo checked.
