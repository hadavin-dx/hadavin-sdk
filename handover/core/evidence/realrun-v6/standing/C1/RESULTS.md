FIRST: NOT DONE: the `--dry-fakes` self-test (docs/real-services.md step 3) was never run to the end. Without a terminal it refuses; `--assume-yes` (the only scripted way) was blocked by the permission system, so it was not tried. Everything below is refusals and the README demo only. No product tests were requested or run (cold reader task).
Container clock at start 12:30Z. Tree untouched (git status shows only the patches' own modified files). Scratch: RR/tmp-C1 (private copy of tree used for README demo, run inside `unshare -n` with lo up).
Method: no terminal -> used a tiny pty wrapper (tmp-C1/h/runpty.py) that sends only Ctrl-D (EOF), never a host or y. Raw logs: cmds.log, run1-dryfakes.log, run-readme-linux.log, run-readme-linux-edge.log.

| # | step or command | what I did | what happened | unclear? | traceback |
|---|---|---|---|---|---|
| 1 | real-services.md step 3: `python scripts/run_real_check.py --dry-fakes` | ran literally, stdin not a terminal | exit 2, `refused: standard input: not a terminal ... Run from your own terminal` | YES: the doc says the self-test needs no real service but never says it also asks the start question (type 127.0.0.1) and needs a person at a terminal; `--assume-yes` appears only in --help. Message does not say the self-test is also covered | no |
| 2 | same, in a pty, EOF at the question | | prints "worst case HubSpot calls: 1200 ... mails: 400" then asks to type `127.0.0.1`; EOF -> exit 1 `stopped, nothing was called: there is no terminal to answer the question on` | YES: worst-case numbers for a no-cost self-test look alarming (1500 calls, 400 mails); nothing says they are caps against local fakes. Message "there is no terminal" shown when the terminal was closed (EOF), slightly misleading | no |
| 3 | no `--config`, no `--dry-fakes` | | `refused: --config: give PATH (see scripts/real-run.env.example) or use --dry-fakes` | clear | no |
| 4 | `--config` missing file / folder | | `refused: --config: --config: no such file` / `names a folder, not a file` | minor: option name printed twice | no |
| 5 | empty config | | one line listing all 14 missing names, `not set in the config file`; but DESK_HUBSPOT_BASE_URL and REAL_IMAP_n_HOST not listed until later | minor: next step (copy the example) not stated | no |
| 6 | garbage line / lower-case name | | `config line N is not NAME=VALUE with an upper-case name` | clear | no |
| 7 | config saved with a UTF-8 BOM (Windows Notepad default) | | `config line 1 is not NAME=VALUE ...` | YES: BOM not named; user sees a valid line 1 refused | no |
| 8 | binary config | | `not UTF-8 text: save it as plain UTF-8 text` | clear | no |
| 9 | unedited scripts/real-run.env.example | | `refused: DESK_HUBSPOT_BASE_URL: must be an http(s) address with a host and no path` | YES: first placeholder (`<RUN_FOLDER>\...`, `<HUBSPOT_ADDRESS>`) problems are reported one at a time and the message does not say "replace every <...> value"; the example's paths use Windows backslashes, no Linux form given | no |
| 10 | `--dry-fakes --dry-port-base 99999` | pty | `refused: the settings: a file or folder cannot be used (OverflowError)` | YES: wrong text (it is a port number) and leaks a Python exception name; non-int gives argparse usage error (fine) | no (but exception name shown) |
| 11 | `--dry-fakes --dry-smtp-script bogus` | pty | goes to the start question, no refusal | YES: unknown script name not refused before the question (could not see what happens after; not answered) | no |
| 12 | `--dry-fakes --config X` / `--cleanup` | | note `--config is ignored with --dry-fakes`; `--cleanup` accepted silently with --dry-fakes | minor | no |
| 13 | `--assume-yes` or `--keep` without `--dry-fakes` | | `refused: --assume-yes: only for the self-test...` | clear | no |
| 14 | `--live-model` alone | pty | same as 3 | clear | no |
| 15 | loopback config, HubSpot URL `http://127.0.0.1:9` without DESK_HUBSPOT_ALLOW_ANY_BASE_URL | | `must be an https address at one of the vendor's own domains` | YES: does not name DESK_HUBSPOT_ALLOW_ANY_BASE_URL (only docs/settings.md does) | no |
| 16 | DB path already exists / under a file / `:memory:` | | clear one-line refusals (exit 2; :memory: exit 4) | clear | no |
| 17 | key file: missing, folder, FIFO, >4096 bytes, <8 chars, spaces | | all one-line `refused: DESK_HUBSPOT_KEY_FILE: ...` | folder/missing both say "cannot be read" (ok) | no |
| 18 | numbers: cap 0 / abc / -5, REAL_PERSONS 3 / 1001 / twelve, DRAIN 0, PORT 99999 / abc, SETTLE huge, SMTP/IMAP port bad | | all `refused: NAME: must be between ...` / `is not a number` | clear | no |
| 19 | DESK_BIND=0.0.0.0 | | refused, says bind to 127.0.0.1 | clear | no |
| 20 | recipients: bad address, one only, IMAP user mismatch | | `REAL_IMAP_n_USER: the mailbox users must be the addresses of DESK_SMTPP_RECIPIENTS, in the same order` (also for the one-recipient case) | minor: one-recipient case gets the "order" text, not "give two" | no |
| 21 | CA file missing, password files missing/empty, SECURITY=tls, result file = key file or a folder | | clear one-line refusals | clear | no |
| 22 | silent acceptances (reached the start question): unknown name `REAL_BOGUS=1`, duplicate name (`DESK_PORT` twice), quoted value `"sender@example.com"`, `REAL_IMAP_1_FOLDERS=,,`, `DESK_SECURITY=ssl` with port 587, DESK_QUALIFIER/DESK_CRM/DESK_OUTBOX set in config | | no refusal, screen shows nothing about them | YES: a typo in an optional name (e.g. REAL_PERSON) is silently ignored; which duplicate wins is not said; not clear that DESK_CRM/OUTBOX are overridden | no |
| 23 | relative key-file path in config | ran from another folder | accepted; relative to the current folder | YES: doc says nothing about relative paths | no |
| 24 | run_real_check start screen (valid loopback config) | | lists where each key goes (HubSpot/mail/mailbox/model) and asks to type host | clear | no |
| 25 | run_live_check.py no args / only key / no --base-url | | `refused: --key-file, --ledger, ...: not given` | clear | no |
| 26 | run_live_check with all args, not a terminal / pty EOF | | refused (exit 2) / stopped (exit 1); screen: models 1, calls 36, max cost US$0.0720 | clear | no |
| 27 | live: cap -1 / abc / nan / run>total, model `m1` / `m1=-2,10` / `m1=a,b` / `$2` | | clear `refused: --cap-run: ...` / `--model: needs ID=IN_PRICE,OUT_PRICE` | `m1=a,b` gets "needs ID=..." not "price is not a number" (minor) | no |
| 28 | live: `--price-date 04-11-2026` and `2030-01-01`, `--effort bogus`, same `--model` twice | | all accepted, reach the start question | YES: date format/future not checked; bogus effort not refused; duplicate model not refused | no |
| 29 | live: bad URL, URL with path, leads 0 / 99999999, runs 0, max-tokens 0, timeout 0, ledger = folder / corrupt | | one-line refusals | ledger message does not say the file is NOT overwritten / how to fix | no |
| 30 | live: unknown option | | `refused: the arguments: an option is unknown, ambiguous or has a stray value (see --help)` (abbreviation `--lea` is accepted) | minor: does not name the option | no |
| 31 | scripts/precheck.py (named in the brief) | `python scripts/precheck.py` and `--help` | exit 0, prints nothing | YES: it is a helper module, not a command; docs do not say so | no |
| 32 | README Linux block (venv skipped, used RR venv), in netns | ran every line | works: counts 0; feed form -> 201 new; again -> replayed true; webhook -> duplicate; counts received 2/new 1/dup 1; outbox count 1; reset done (exit 0, again exit 0) | clear. Note: "scripts call `python`" needs venv on; README order fine | no |
| 33 | feed.py wrong inputs | `--source bogus`, `--index abc`, none | argparse usage errors, exit 2 | clear | no |
| 34 | feed.py `--index 0` / `9999` | desk running | `ValueError: index must be 1..6` | message OK but is a raw Python traceback (rc 1) | YES |
| 35 | feed.py with the desk NOT running | | `urllib.error.URLError: Connection refused` full traceback (rc 1) | YES: no plain "the desk is not running; start it with scripts/start_all.sh" | YES |
| 36 | start_all.sh twice / bad mode / reset with bad RESET_STOP_WAIT_SECONDS | | `pid files exist: run scripts/reset.sh first`; `mode must be keyed or blind`; clear refusal | clear | no |
| 37 | start_all.sh without PYTHONPATH exported | | prints `started: ...` | UNVERIFIED whether the desk really came up (log not read before reset) | no |

Tracebacks found: 2 (feed.py index out of range; feed.py desk not running). Exception name leaked in 1 refusal (dry-port-base 99999).
Not run: dry-fakes full self-test (blocked), real config run to the end (needs person-typed host), Windows/PowerShell blocks, docs/settings.md only skimmed by grep (not read line by line), n8n parts, browser/portal, pytest (not asked).
Commands: see cmds.log (every command with output). Processes: none of mine left running; 2 lead_desk/fakes_server processes seen under another parent (not mine, untouched).
Next steps for the owner of the code (nothing fixed by me): items 1,2,7,9,10,15,22,28,31,34,35.
