# Cold reader Q5: README quick start on Linux (clean clone of f3c39cf)

Run: 2026-11-13 about 12:31-12:34 UTC (18:01-18:04 IST). Took about 3 minutes (the scripts are quick). Python used: `python3` = 3.13.18 (/usr/local/bin); README only says "3.12 or newer", so this was fine.

## 1. Steps that FAIL
None. Every command in the Linux block worked on the first try. Reset exited 0 and both ports were free afterwards (checked with curl: no answer).

## 2. UNCLEAR / ambiguous
- Steps 1-2 ("press the green Code button, copy the address, git clone") cannot be followed from inside the clone; I used the given local clone and skipped them.
- "python3 -m venv ... then the scripts call `python`": the shell state (venv, PYTHONPATH) lasts only in one terminal. If each command is run in a separate shell the later steps would use the wrong python. README does say "same terminal", so clear, but easy to miss.
- "curl -i .../counts ... the numbers are all 0": the output has about 20 fields; "numbers are all 0" is true only if you ignore `reaper_running: true`, `last_reaper_pass_at: 1794573119`, and `expected_match`/`ok` null. Mild.
- Line "port 8766 ... demo servers": README never says which of the two ports the desk uses (8765 = desk, 8766 = demo servers). It is inferable from the curl lines and the start script prints it.
- Comment on the second feed: "201 and replayed: true". Saw exactly that (see section 4).
- Third lead: receipt_id is 3, not 2 (the replay took no new number but the second receipt id was skipped?). Nothing in README explains receipt numbers; harmless.

## 3. Needs knowledge or tools not in README
- `ps` is required by reset (README mentions it, exit 3 "Linux ps not installed"): it exists here.
- `ss` is NOT installed on this machine; my own pre-check for free ports needed another way (README does not tell you how to check "ports must be free"; no command given).
- `curl` is used but not listed under "You need" (it was present).
- `sudo apt install python3-venv` was not needed.
- No environment variable beyond PYTHONPATH needed.

## 4. Claims checked
| README claim | Seen |
|---|---|
| counts first line "HTTP/1" with 200, numbers all 0 | `HTTP/1.0 200 OK`; received 0 new 0 duplicate 0 review 0 (plus other fields, see section 2) |
| first lead `"verdict": "new"` | `canned-1 form -> 201 {"receipt_id": 1, "verdict": "new", "lead_id": "L7deaf726bf0c", "replayed": false}` yes |
| same request again 201 and `"replayed": true` | `201 {... "replayed": true, "payload_matches": true}` yes |
| other door `"verdict": "duplicate"` | `200 {"receipt_id": 3, "verdict": "duplicate", ... "replayed": false}` yes (HTTP 200, not 201; README does not state the code for this one) |
| counts: received 2, new 1, duplicate 1 | received 2, new 1, duplicate 1, review 0: yes |
| outbox `"count": 1` | `{"mode": "keyed", "count": 1, "reminders": 0, "messages": [one]}` yes. Email subject "Thanks for getting in touch, Ada Example" matches the README text |
| portal at http://127.0.0.1:8765/ui/ | 200 text/html, title "Lead Desk"; css/js/icon assets 200. I did NOT render it in a browser (no browser, Bash only), so "overview, leads, items that need a person, a request log, what data it stores" was not seen visually; the page references the five page scripts (overview, leads, needs, log, data). `/ui/leads` gives 404 (probably a client-side tab; not stated) |
| `/` and `/health` answer 404 | yes, both 404 |
| reset deletes records and logs, stops programs | printed `reset done`, rc 0, `data/` empty, ports closed, `git status` clean |
| "Reset ... exit codes 2-6" | not tested (not needed) |

## 5. Time
About 3 minutes total for the Linux block (clone, venv, start, 3 feeds, 2 checks, reset). README says "a few minutes": true.

## 6. Wording a non-technical reader may not follow
- "Open ONE terminal" and "run the lines of your system below" with no word on what a terminal is.
- "CRM row", "SQLite database file", "loopback", "Host and Origin check", "keyed and blind", "UNKNOWN", "Crash point D2", "Reaper", "Webhook", "Playwright", "dash", "busybox sh, zsh", "pid" ("two process ids"), "Debian/Ubuntu". Some are explained under "Words used here", but "Words used here" comes AFTER "What you will see", which already uses "verdict", "replayed", "portal", "outbox" ("The demo mail system holds exactly one email" is clear, but the URL path is `/fake/outbox`).
- "the numbers are all 0", "a clock that jumps by 30 seconds", "bind", "loopback address".
- Step 3 sentence is a 60-word sentence with parentheses.
- The word `fake` appears in URLs while the text says "stand-ins" (README explains this).

## Files and links mentioned: all exist
docs/portal.md, docs/tests.md, docs/limits.md, docs/settings.md, docs/n8n-recipe.md, docs/real-services.md, docs/why-this-code.md, contract.md (has "Run commands" heading), versions.md, LICENSE, SECURITY.md, load_tools/README.md, demo_only/leadflow.json, scripts/{start_all.sh,reset.sh,start_all.ps1,reset.ps1,feed.py,hubspot_probe.py}, tools/hygiene.py, requirements-dev.txt, requirements-dev-win.txt, src/lead_desk/loader.py, n8n/. docs/limits.md has an item 5 on clock jumps (checked). Not checked: tests (not in quick start), Windows block (Linux machine), GitHub "Code button".

## Step log (all in /home/user/work/q5-clean, shell state chained within each call)
1. Quote: "python3 -m venv .venv && . .venv/bin/activate" -> ok, python = .venv/bin/python 3.13.18.
2. `export PYTHONPATH=src` -> ok.
3. `bash scripts/start_all.sh keyed` -> "started: demo servers (keyed outbox) pid 8936, desk pid 8937 / ports: desk 8765, demo CRM and outbox 8766 / logs: data/fakes.log and data/desk.log"; rc 0.
4. wait loop + `curl -i http://127.0.0.1:8765/counts` -> 200, all zero.
5. `python scripts/feed.py --source form --index 1` -> 201 new.
6. same again -> 201 replayed true.
7. `--source webhook --index 1` -> 200 duplicate.
8. `curl http://127.0.0.1:8765/counts` -> 2/1/1.
9. `curl http://127.0.0.1:8766/fake/outbox` -> count 1.
10. `bash scripts/reset.sh` -> "reset done", rc 0.
Processes: I started the two demo servers and the desk via the script; the reset script stopped them; ports verified closed. Progress lines in evidence/raw/progress-Q5.txt.
