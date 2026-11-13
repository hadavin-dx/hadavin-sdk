# Cold reader Q5b: settings, portal, why-this-code, contract, SECURITY

Clone: `/home/user/work/q5b-clean`, commit f3c39cf89ec989f032ea48a23cfd824b88da9c68 (checked out; git status clean at the end).
Venv: `/usr/bin/python3.12 -m venv .venv`, then `pip install --require-hashes -r requirements-dev.txt` (worked, no hash error).
Private ports used: desk 21765 / 21777 / 21780 / 21790, demo servers 21766 (trials); README steps and portal on 8765/8766 (both were free).
Every process I started was stopped (desk via `scripts/reset.sh`, the rest by PID). One other agent's `fakes_server` (port 18686) was left alone.
Raw trial outputs: `/home/user/work/q5b-scratch/A-trials1.out`, `A-trials2.out`, `A-trials3.out` (trials2 rows that say "cannot reach the demo servers" are MY slip: I stopped my demo server too early; those rows were re-run in trials3 and are the ones quoted here).

## 1. FAILS or does not match (exact output)

F1. `docs/settings.md` line 3 says "A bad value stops the start with an error." Not true for these (desk started and answered `/counts` 200, or stopped with a traceback):
- `DESK_BIND="not an address"`: no error, the desk starts ("RUNNING"). No refusal, no exit code.
- `DESK_DB_PATH=""` (empty): `sqlite3.OperationalError: unable to open database file`, Python traceback, exit 1 (not 4; the table row for `db_path` only mentions `:memory:` exit 4).
- `DESK_DB_PATH=/proc/nope/x.sqlite3`: `FileNotFoundError: [Errno 2] No such file or directory: '/proc/nope'`, traceback, exit 1.
- `DESK_REPLIES_PATH=<file with broken JSON>` and `DESK_REPLIES_PATH=<missing file>`: Python traceback, exit 1. `contract.md` line 131 says exit 1 with a traceback is for "a constant that is out of range", and says exit 4 is for "any other bad DESK_* value". Neither matches.
- `DESK_HUBSPOT_KEY_FILE` pointing at a file that does not exist, or a 5-character key file; `DESK_LIVE_KEY_FILE` the same; `DESK_SMTPP_PASSWORD_FILE` a missing path or a directory: all START normally (counts 200). `settings.md` says the key must be "at least 8 characters" and `LIVE_KEY_MIN_CHARS` "refused"; it does not say these files are only read at first use.
F2. `docs/why-this-code.md` line 24: "n8n export scrub (`tools/`) ... Under 100 lines, no business logic". `wc -l tools/scrub_n8n_export.py` = 205 lines.
F3. `contract.md` line 222 (data-map row): the switch is called "Hide email addresses". The portal text (`src/lead_desk/portal/pages/leads.js`, `log.js`) and `docs/portal.md` say "Hide names and email addresses". The string "Hide email addresses" exists nowhere in the portal files.
F4. `contract.md` line 229: `GET /fake/outbox` -> `{"mode","count","messages":[...]}`. Actual: `{"mode": "keyed", "count": 1, "reminders": 0, "messages": [...]}` (an extra `reminders` key; README's `"count": 1` is fine).
F5. `docs/portal.md` and README name pages (Overview, Leads, Needs a person, Request log, Data and AI) but only ONE URL: `http://127.0.0.1:8765/ui/`. The pages are not separate URLs; they are browser-side routes (`#/overview` etc.) drawn by JavaScript. A reader following "open each page with curl" gets the same 5 KB HTML shell for all of them. What curl CAN open: `/api/ui/summary`, `/api/ui/leads`, `/api/ui/review`, `/api/ui/log`, `/api/ui/data-map` (all 200). The document never names these API addresses (they are in `contract.md`); I found the page names in the JavaScript. So the claims about what each page SHOWS and what is masked on screen could NOT be checked with curl (see section 2).
No 404 from any address the documents name. Unnamed addresses I tried: `/ui/demo.js`, `/ui/portal_demo.js`, `/ui/pages/`, `/ui/nosuch` -> 404 `{"error": "not_found"}`; `/ui` -> 308 to `/ui/` (documented in contract.md, not in portal.md).

## 2. UNCLEAR (what I had to guess)

U1. README "Try it" and `docs/tests.md`: README says "The desk needs no extra packages" and starts with `python3 -m venv`; `docs/tests.md` says Python 3.12 + `requirements-dev.txt` for tests. Fine, but the README first-step block does not say which Python (`python3` here is 3.12; on another machine it may differ). I used `/usr/bin/python3.12` as the task told me.
U2. `docs/portal.md` line 7 says the "Every lead is demo data..." banner appears "when ... the demo tools are not installed". With the demo tools installed (the default) a different line shows ("Demo: Every lead is demo data. The demo CRM (customer records) and the demo mail are stand-ins. AI ratings are pre-written. Nothing here is sent..." from `/api/demo/state`). The portal doc never says what the default reader will actually see.
U3. `docs/portal.md` line 5: "masked on screen by default", the eye button, the 30-second reveal, the session-only switch: browser behaviour; I have no browser (Bash only), so "cannot check". I did confirm the JSON carries the unmasked values (`/api/ui/leads/<id>` returned name, email, phone, message) as the doc states.
U4. `docs/settings.md` row `DESK_SMTP_HOST` default `127.0.0.1`: in code the default is `Config().bind`, so with `DESK_BIND=127.0.0.2` the default changes. Not stated.
U5. `docs/settings.md` says a number setting "with a message that names the setting (never the value)"; true. But "Every number setting that is not a number ... exit code 4" and the statement for `DESK_FAKES_PORT` that is valid but nothing listens: exit 1 ("cannot reach the demo servers (are they running? see scripts/start_all)"), which the settings table does not list.
U6. `contract.md` line 222: "`stored` also lists the row `later_decision` (...; approval mode only)". With mode `off` the row IS listed (purpose text says "(approval mode only)"). Reads two ways.
U7. `DESK_HUBSPOT_ALLOW_ANY_BASE_URL`: a plain word "yes"; any other word (e.g. "true") silently means no. Not stated.
U8. `DESK_SEND_TIMEOUT_SECONDS` accepts up to 600 but the doc also says every send is cut at 9 s; a reader cannot tell which number matters (the doc does say so in one sentence; fine, but easy to miss).

## 3. Wording a non-technical reader would not understand (quotes)
- "Crash point", "keyed and blind", "UNKNOWN" are explained in README, but `docs/settings.md` uses without explanation: "wildcard address", "loopback", "TIME_WAIT" (contract), "STARTTLS", "reaper", "capability read", "write-ahead", "DNS rebinding" (explained only partly), "SIGKILL", "ledger" (explained once), "the all-zeros address above all".
- `docs/settings.md`: "`DESK_LEADFLOW_FILE` ... `rota`, `steps`, `closed`, `first`, `after_followup`, `reminder_until`" are file keys named with no plain-language gloss in that table row ("rota" is not an everyday word).
- `docs/portal.md`: "Request to check", "Not decided yet", "Repeat" as Overview counters are used before explained; "blind mail system" ("a wrong 'not sent' answer can cause a second email on a blind mail system") needs the README glossary.
- `contract.md` is written for engineers (e.g. "BEGIN IMMEDIATE", "ON CONFLICT DO NOTHING", "EMFILE/ENFILE", "SO_EXCLUSIVEADDRUSE"); no plain summary at the top besides the first table.
- `SECURITY.md`: "no result of them is claimed here" (about automatic checks) is hard to parse.

## 4. Part A: every setting in `docs/settings.md`
Default column = code (`Config.from_env()` with an empty environment, or constants). "valid other" = value I set and the desk started (RUNNING = `desk listening on ...`, `/counts` 200). "invalid" = what I set, exit code, text. Messages are printed as `the desk refuses a setting: <text>`, exit 4, unless noted. Doc defaults (verbatim from the table) matched the code in every row unless marked DIFF.

| Setting (settings.md line) | Doc default / meaning | Code default | Valid other | Invalid -> result |
|---|---|---|---|---|
| `DESK_DB_PATH` (7) | `./data/desk.sqlite3` | `PosixPath('data/desk.sqlite3')` | other path: RUNNING | `:memory:` -> exit 4 "the desk refuses to start: the lead book must be a file: ':memory:' is empty for every thread but the first" (documented); `""` -> exit 1 traceback (F1); `/proc/nope/x` -> exit 1 traceback (F1) |
| `DESK_BIND` (8) | `127.0.0.1`; other address warns; real service -> refuse | `127.0.0.1` | `127.0.0.2` RUNNING; `0.0.0.0` RUNNING + warning "warning: the desk is bound to 0.0.0.0, which other computers can reach. The portal shows every lead ... Bind to 127.0.0.1, or ..." (matches doc) | `0.0.0.0` + `DESK_CRM=hubspot` -> exit 4 "DESK_BIND is not a loopback address while a real service is set (crm): anyone who can reach the port could write to it. Bind to 127.0.0.1" (matches); `""` -> exit 4 "DESK_BIND and DESK_FAKES_HOST must not be empty"; `not an address` -> NO error (F1) |
| `DESK_PORT` (9) | `8765`, 0 = free port | `8765` | `21777` RUNNING; `0` RUNNING on 40207 (prints real port); ` 21777 ` (spaces) RUNNING (documented) | `65536`/`-1` -> exit 4 "DESK_PORT must be between 0 and 65535"; `abc`, `8e3`, `""` -> exit 4 "DESK_PORT is not a number" |
| `DESK_ADAPTERS` (10) | `demo` only | `demo` | `demo` | `other` and `""` -> exit 4 "DESK_ADAPTERS must be one of demo" |
| `DESK_QUALIFIER` (11) | `recorded` | `recorded` | `recorded` | `bogus` -> exit 4 "DESK_QUALIFIER must be one of recorded, live_claude"; `live_claude` alone -> exit 4 "DESK_LIVE_MODEL is required for the live model" |
| `DESK_OUTBOX` (12) | `http` | `http` | `smtp` RUNNING; `smtp_provider` needs the DESK_SMTPP_* set (below) | `bogus` -> exit 4 "DESK_OUTBOX must be one of http, smtp, smtp_provider"; `smtp_provider` alone -> exit 4 "DESK_SMTPP_HOST is required for the smtp provider" |
| `DESK_CRM` (13) | `fake` | `fake` | `hubspot` with key file + max calls RUNNING | `bogus` -> exit 4 "DESK_CRM must be one of fake, hubspot"; `hubspot` alone -> exit 4 "DESK_HUBSPOT_KEY_FILE is required for the hubspot CRM" |
| `DESK_LATER_MODE` (14) | `off` | `off` | `approval` RUNNING | `bogus` -> exit 4 "DESK_LATER_MODE must be one of off, approval" |
| `DESK_APPROVERS_FILE` (15) | none; approval mode uses `demo_only/approvers.json`; refused when mode off | `None` | mode approval + the demo file RUNNING; mode approval, no file RUNNING (documented) | mode off + file -> exit 4 "DESK_APPROVERS_FILE is set but DESK_LATER_MODE is not approval"; broken JSON -> exit 4 "the approvers file is not valid JSON text"; `{}` -> exit 4 "the approvers file needs a list named approvers (and a text label, if any)"; missing file -> exit 4 "the approvers file cannot be read" |
| `DESK_LEADFLOW_FILE` (16) | none (off); `""`/`off` = off; refused file exits 4 | `None` | `""` RUNNING, `off` RUNNING; `demo_only/leadflow.json` + `DESK_NUDGE_TO=r@example.test` RUNNING | `leadflow.json` without NUDGE_TO -> exit 4 "reminders are on in the leadflow file but DESK_NUDGE_TO is not set"; broken JSON -> exit 4 "DESK_LEADFLOW_FILE is not valid JSON text"; `{}` -> exit 4 "DESK_LEADFLOW_FILE needs exactly the keys rota, steps, closed, first, after_followup, reminder_until and optionally nudge_after_seconds" (doc says "only the keys ... allowed, any other key is refused": the message says "exactly the keys"); missing -> exit 4 "DESK_LEADFLOW_FILE cannot be read" |
| `DESK_NUDGE_TO` (17) | none; refused unless leadflow file | `''` | with leadflow RUNNING; `""` RUNNING | alone -> exit 4 "DESK_NUDGE_TO is set but DESK_LEADFLOW_FILE is not" |
| `DESK_FAKES_HOST` (18) | `127.0.0.1` | `127.0.0.1` | `localhost` RUNNING | `example.com`, `10.1.2.3` -> exit 4 "DESK_FAKES_HOST (or DESK_FAKES_URL) must be this computer: localhost or a loopback address" |
| `DESK_FAKES_PORT` (18) | `8766` | `8766` | `21766` RUNNING | `0`,`70000` -> exit 4 "DESK_FAKES_PORT must be between 1 and 65535"; `x` -> exit 4 "is not a number"; valid port with nothing listening -> exit 1 "cannot reach the demo servers (are they running? see scripts/start_all)" (not in settings.md) |
| `DESK_FAKES_URL` (19) | built from host+port; wins | built | `http://127.0.0.1:21766` RUNNING | `http://example.com:80` -> exit 4 (loopback message above); `http://[/` -> exit 4 "DESK_FAKES_URL is not a valid address" (matches doc); `ftp://...` -> exit 4 "DESK_FAKES_URL must use http" |
| `DESK_REPLIES_PATH` (20) | none; loader uses demo_only/replies.json | `None` | `demo_only/replies.json` RUNNING | broken JSON / missing -> traceback, exit 1 (F1) |
| `DESK_SEND_TIMEOUT_SECONDS` (21) | `5.0` | `5.0` | `5.0`, `2` RUNNING | `0` -> exit 4 "must be above 0 and at most 600.0"; `601` -> "must be at most 600.0"; `nan`,`abc` -> "is not a number" |
| `DESK_SIZE_CAP_BYTES` (22) | `65536`, larger gets 413 | `65536` | `65536`,`1000` RUNNING; 413 confirmed at 70000 (default cap) | `0`,`16777217` -> exit 4 "must be between 1 and 16777216"; `1.5`,`0x10` -> "is not a number" |
| `DESK_STALL_SECONDS` (23) | `120` | `120` | `120`, `0` RUNNING | `86401`,`-5` -> exit 4 "must be between 0 and 86400"; `1_0` -> "is not a number" |
| `DESK_ALLOWED_HOSTS` (24) | none | `()` | `myhost.local`, `a,b`, `[::1]` RUNNING | `-bad`, `*`, `0.0.0.0`, `UPPER` -> exit 4 "DESK_ALLOWED_HOSTS holds a name that is not a lower-case host name" |
| `DESK_SMTP_HOST` (Sender) | `127.0.0.1`, loopback IP only | `Config().bind` (U4) | `127.0.0.1`,`127.0.0.5` RUNNING | `localhost`,`example.com` -> exit 4 "DESK_SMTP_HOST must be an IP address (no name lookup is made)"; `8.8.8.8` -> "must be a loopback address (the test mail server runs on this computer)" |
| `DESK_SMTP_PORT` | `2525` | `2525` | `2525`,`2526` | `0`,`65536` -> "must be between 1 and 65535"; `x` -> not a number |
| `DESK_SMTP_FROM` | `desk@example.test` | same | `a@b.example` | `not an address`, non-ASCII -> exit 4 "DESK_SMTP_FROM is not a plain ASCII address" |
| `DESK_SMTP_MESSAGE_ID_DOMAIN` | `example.test` | same | `other.example` | `UPPER.example`, `bad domain` -> exit 4 "must be a lower-case host name" |
| `DESK_SMTP_TIMEOUT_SECONDS` | same as send timeout | `5.0` | `5.0`,`2` | `0` -> "must be above 0 and at most 600.0"; `601` -> "at most 600.0"; `x` -> not a number |
| `DESK_SMTPP_HOST`,`_USER`,`_PASSWORD_FILE`,`_FROM`,`_RECIPIENTS`,`_MAX_SENDS` | required | none | all six set: RUNNING | each missing -> exit 4 "DESK_SMTPP_<NAME> is required for the smtp provider" (6 of 6 confirmed) |
| `DESK_SMTPP_SECURITY` | `starttls` (or `ssl`) | `starttls` (code line 86) | `starttls`,`ssl` RUNNING | `tls` -> exit 4 "DESK_SMTPP_SECURITY must be starttls or ssl" |
| `DESK_SMTPP_PORT` | 587 / 465 | 587 starttls, 465 ssl (code) | `587` RUNNING | `0`,`65536` -> "must be between 1 and 65535" |
| `DESK_SMTPP_MAX_SENDS` | required cap | none | `1`,`10000` RUNNING | `0`,`10001` -> "must be between 1 and 10000" |
| `DESK_SMTPP_TIMEOUT_SECONDS` | same as send timeout; max 9 | `5.0` | `9` RUNNING | `9.1` -> "must be at most 9.0"; `0` -> "must be above 0 and at most the desk's call deadline" |
| `DESK_SMTPP_PASSWORD_FILE` | path of one-line file <= 4096 bytes | - | - | missing path / a directory: STARTS (F1, read later) |
| `DESK_SMTPP_MESSAGE_ID_DOMAIN` | `example.invalid` | same | `x.example` | `Bad Domain` -> "must be a lower-case host name" |
| `DESK_SMTPP_STATS_FILE`, `DESK_SMTPP_CA_FILE` | listed only | - | NOT TESTED (no real mail server; cannot check) | - |
| `DESK_HUBSPOT_KEY_FILE` | required, >= 8 chars | none | key file (made-up, 14 chars) RUNNING | missing from env -> exit 4 "DESK_HUBSPOT_KEY_FILE is required for the hubspot CRM"; 5-char file or missing path -> STARTS (F1) |
| `DESK_HUBSPOT_MAX_CALLS` | required cap | none | `10` RUNNING | missing -> exit 4 "is required for the hubspot CRM"; `0`,`10001` -> "must be between 1 and 10000"; `x` -> not a number |
| `DESK_HUBSPOT_BASE_URL` | vendor address | `https://api.hubapi.com` | that value RUNNING | `https://example.com` -> exit 4 "must be an https address at one of the vendor's own domains"; with `DESK_HUBSPOT_ALLOW_ANY_BASE_URL=yes` RUNNING; `http://[/` -> "is not a valid address" |
| `DESK_HUBSPOT_TIMEOUT_SECONDS` | default 4.5, max 9 | `4.5` | `4.5`,`9` RUNNING | `10` -> "must be at most 9.0"; `0` -> "must be above 0 and at most the desk's call deadline" |
| `DESK_HUBSPOT_MAX_429_RETRIES` | default 2, 0 to 5 | `2` | `0`,`2`,`5` RUNNING | `6`,`-1` -> "must be between 0 and 5" |
| `DESK_HUBSPOT_STATS_FILE`, `DESK_HUBSPOT_ALLOW_ANY_BASE_URL` | listed | - | `yes` shown above; STATS_FILE NOT TESTED | - |
| `DESK_LIVE_MODEL`,`_KEY_FILE`,`_PRICE_IN_PER_MTOK`,`_PRICE_OUT_PER_MTOK`,`_PRICE_DATE`,`_CAP_RUN_USD`,`_CAP_TOTAL_USD`,`_LEDGER_PATH`,`_RUN_ID` | required | none | all nine set (made-up): RUNNING | each missing -> exit 4 "DESK_LIVE_<NAME> is required for the live model" (9 of 9 confirmed) |
| `DESK_LIVE_PRICE_*` | each 0.000001 to 1,000,000 | - | `0.000001`,`1000000` RUNNING | `0.0000001`,`1000001` -> "DESK_LIVE_PRICE_IN_PER_MTOK is outside the allowed range"; `abc` -> "is not a number" |
| `DESK_LIVE_CAP_RUN_USD`,`_TOTAL_USD` | >0, <= 1,000,000, run <= total | - | 1 / 2 RUNNING | run 3, total 2 -> "DESK_LIVE_CAP_RUN_USD is above DESK_LIVE_CAP_TOTAL_USD"; run `0` -> "must be a positive number"; total `1000001` -> "is outside the allowed range" |
| `DESK_LIVE_TIMEOUT_SECONDS` | default 8, max 9 | `8.0` | `8`,`9` RUNNING | `9.5` -> "must be at most 9.0"; `0` -> "must be above 0 and at most the desk's AI call budget" |
| `DESK_LIVE_MAX_TOKENS` | default 64, 1 to LIVE_MAX_TOKENS_MAX | `64` | `64`,`1000000` RUNNING | `1000001`,`0` -> "must be between 1 and 1000000" |
| `DESK_LIVE_BASE_URL` | default provider address; http only loopback | `https://api.anthropic.com` | that, `http://127.0.0.1:9` RUNNING | `https://example.com` -> exit 4 "is not the provider's own address (DESK_LIVE_ALLOW_ANY_BASE_URL=yes allows it)"; `http://example.com` -> "plain http is allowed for a loopback address only"; with ALLOW_ANY=yes RUNNING |
| `DESK_LIVE_API_VERSION`,`_EFFORT` | defaults `2026-10-21`, `low` | `2026-10-21`, `low` | effort `high` RUNNING | empty -> exit 4 "DESK_LIVE_EFFORT and DESK_LIVE_API_VERSION must not be empty" |
| `DESK_LIVE_KEY_FILE` | >= 8 chars | - | - | 5-char file or missing: STARTS (F1) |
| `DESK_LIVE` + `DESK_BIND=0.0.0.0` | refused | - | - | exit 4 "DESK_BIND is not a loopback address while a real service is set (ai) ..." |
| `DESK_LIVE_ALLOW_ANY_BASE_URL`, `DESK_LIVE_LEDGER_PATH`/`RUN_ID` use, ledger behaviour, spend caps | - | - | NO live call made (no spend); behaviour of ledger NOT TESTED (cannot check without a model server) | - |
| `nudge_after_seconds` and the other leadflow-file bounds (table "The leadflow file") | 1 to 2678400 etc. | - | demo file (90) RUNNING | only whole-file errors tested (above); per-entry bounds NOT TESTED one by one |
| Number-setting rules (spaces ok, `0x10`, `nan`, `1_0`, `1.5`, `""` refused) | as doc | - | `" 21777 "` RUNNING | `0x10`,`nan`,`1_0`,`1.5`,`""`,`8e3` all "is not a number", exit 4: MATCHES doc |
| Constants "fixed in code" (settings.md 105-): `MAX_CONNECTIONS` 256, `MAX_HANDLER_THREADS` 1024, header/body deadline 10 s, Retry-After 1 | as doc | 256, 1024, 10.0, 10.0 | - | yes, values match `constants.py` (Retry-After 1 not run; cannot check) |
| `LIVE_KEY_MIN_CHARS` 8, `LIVE_LEDGER_FILE_MAX_BYTES` 8,000,000 | as doc | 8, 8000000 | - | constants match; refusal behaviour NOT RUN |
| Helper-script settings: `scripts/run_real_check.py`, `n8n_api.py`, `tools/scrub_n8n_export.py`, `LEAD_DESK_*`, `DPLD_*`, `LEAD_DESK_PATH_ROOTS` | listed | defaults `REAL_PERSONS` 12, min 8, `REAL_DRAIN_SECONDS` 150, `REAL_MAIL_WAIT_SECONDS` 90, settle 10, `N8N_URL` `http://127.0.0.1:5679`, IMAP port 993 all match code | - | `run_real_check.py --config <empty>` -> exit 2 "refused: the config lacks: DESK_DB_PATH, DESK_HUBSPOT_KEY_FILE, ..." (matches doc, exit 2). `n8n_api.py list` with `N8N_URL=http://example.com` -> exit 1 "N8N_URL must be an https address, or http to this computer (127.0.0.1, ::1 or localhost); for an n8n on another computer use https, or an SSH tunnel to 127.0.0.1" (matches). No `N8N_API_KEY_FILE` -> exit 1 "N8N_API_KEY_FILE must be the path of a one-line file with the n8n API key". Closed port -> exit 1 "cannot reach n8n (URLError: ConnectionRefusedError)". The rest (scrub tool rules, load vars, DPLD_*) NOT RUN. Note `run_real_check.py` takes `--config PATH`; the doc says "reads its names from the config file you give it" without naming `--config`. |

## 5. Part B: `docs/portal.md` followed literally
Started with `bash scripts/start_all.sh keyed` (README block): printed `started: demo servers (keyed outbox) pid 17759, desk pid 17760`; counts all 0, `HTTP/1.0 200 OK`. README feed steps: 1st `201 ... "verdict": "new"`, repeat `201 ... "replayed": true`, webhook `200 ... "verdict": "duplicate"`; counts received 2 / new 1 / duplicate 1; outbox `"count": 1`. All as documented. (The README says "HTTP/1" and 200: the status line is `HTTP/1.0 200 OK`.) `reset.sh` printed `reset done`.
| Claim | Check | Result |
|---|---|---|
| `/ui/` opens | curl 200 `text/html` | yes |
| five pages named | page ids/titles in `pages/*.js` (Overview, Leads, Needs a person, Request log, Data and AI) | yes, but only as `#/` routes (F5) |
| files `app.css`, `portal.js`, `theme.js`, `icon.png`, `pages/*.js|css` | all 200 | yes |
| JSON endpoints | `/api/ui/summary|leads|leads/<id>|review|log|data-map` all 200; unknown id 404 `{"error": "not_found"}` | yes |
| "Hide names and email addresses" switch, "Needs a person", "Request log", "Data and AI" | strings in JS | yes |
| "Next step:" line | text built in `portal_api.py` ("Next step: ...") | yes |
| "Actions are paused until the desk answers." | in `needs.js`, `leads.js` | yes (not exercised in a browser) |
| "Waiting for the CRM check", "CRM not confirmed" chips | in `portal.js` | yes |
| "I checked: it was sent", "I checked: it was not sent", "The CRM entry is there/not there" | `portal.js`, `portal_api.py` | yes |
| banner "Every lead is demo data. The demo CRM and demo mail are not connected. Nothing here is sent to real customers or real systems." | exact text in `portal.js` line 652 (only when demo tools missing) | yes (U2) |
| banner "Real services are connected" | `portal.js`: " Real services are connected: <names>. Lead data this desk handles may be sent to them." | yes; NOT run live |
| "JSON replies still carry the values" | `/api/ui/leads/<id>` returned name, email, phone, message | yes |
| Host/Origin check: other Host or Origin -> 403 | `Host: evil.example` -> 403 `{"error": "forbidden_host"}`; `Origin: http://evil.example` -> 403 `{"error": "forbidden_origin"}` on pages and API; `Host: localhost:8765`, `[::1]` -> 200 | yes |
| `POST /api/demo/crash` and `/burst` exist | GET on them -> 405 `{"error": "method_not_allowed"}` (so routes exist); I did NOT POST (crash stops the desk) | yes |
| read-only second connection, "one test shows that" | cannot check without running tests | cannot check |
| masking on screen, eye button 30 s, session-only switch | browser only | cannot check |
| "every open page asks the desk every few seconds" | JS polling | cannot check |

## 6. Part C: checkable claims in `docs/why-this-code.md`, `contract.md`, `SECURITY.md`
Automated pass over every back-ticked token in all five documents: 759 file/path/identifier tokens checked, 1 not found (`result.json`, a file the real-check script creates: fine). 37 test names in `contract.md`: all exist as `def` in `tests/`. Then specific checks:
| Claim (document, line) | Check | Matches |
|---|---|---|
| why-this-code 28: `CRM_CHOICES` (`fake`,`hubspot`), `OUTBOX_CHOICES` (`http`,`smtp`,`smtp_provider`), `QUALIFIER_CHOICES` (`recorded`,`live_claude`), `OUTBOX_STAND_INS`, `CRM_FIELDS_SENT` in `portal_api.py`, `Config.real_services`, `loader.py` | constants.py lines 119-128, portal_api.py:937, config.py:451 | yes |
| why-this-code 24: scrub tool "Under 100 lines" | 205 lines | NO (F2) |
| why-this-code 23: gitleaks in the checks | `.github/workflows/lint.yml` runs gitleaks 8.30.1 | yes |
| why-this-code 13/19: workflows/logs of n8n-only tries "not in this repository" | `n8n/` holds only `desk-form.json`, `desk-webhook.json`, `proof.json` (desk workflows, not the n8n-only attempts) | yes (reads ambiguous: the folder `n8n/` exists) |
| why-this-code 22: two copies of the retry rule kept in step by a test | `tests/test_burst_retry.py` exists; I did not run it | partly (test exists; not run) |
| contract 34-49: `MODEL_HUNG_MAX` 4, `MODEL_BUSY_BACKOFF_SECONDS` 5, `SEND_MAX_ATTEMPTS` 5, `MODEL_GRACE_MARGIN_SECONDS` 15, grace 30 s = 5 + 5x5, 9+15=24 < 25 | `gate.py`, `constants.py`; computed 30.0 | yes |
| contract 99/97: hook points A, A2, B, D1, D2 / L, C0, C1, D1b, D3, N1 | `hooks.py` | yes |
| contract 104-110: Host rules, Origin exact, Sec-Fetch-Site | curl: Origin null 403; exact 200; `localhost:port` 200; wrong port 403; Sec-Fetch cross-site 403, same-origin 200, none 200, same-site 403; Host port 70000 403; `Host: LOCALHOST:21780` 200 | yes |
| contract 14-24 reply table: 404 not_found, 405, `/counts?expected=x|empty|-1` 400 bad_expected, TRACE 501, HEAD/OPTIONS 404/405, bad_envelope, 413, `http://[/` target -> 400 bad_request | live probe | yes (all) |
| contract 158: no Content-Length / abc / two different values -> 400 bad_envelope; 4301-digit length -> 413; over cap 413; resolve over cap 413 `{"error": "too_large"}`; resolve missing length 400 bad_decision; short body+closed -> 400 bad_envelope | raw socket probe | yes (all). The 408 stall case NOT run (10 s wait) |
| contract 25-27: deep JSON -> 400 bad_envelope; lone surrogate -> review `bad_field:name`; 255+ char lowered email -> `invalid_email`; no email -> `incomplete:email`; no name+email -> `incomplete:name,email` | live POSTs | yes (all) |
| contract 22: Content-Type not checked (text/plain accepted) | POST with `text/plain` -> 201 | yes |
| contract 64: exact hint "Send a corrected submission with a NEW request number." for an R item (retry and resolve) | live | yes; D/O/N hints not run |
| contract 113-117: `GET /ui` 308 `Location: /ui/`; PUT -> 405; `/ui/demo/x` 404; demo POST non-JSON -> 400 `bad_body`; `q` over 100 chars 400 `bad_query` field `q`; `limit` 201 -> 400 `bad_query` field `limit`; `limit=200` ok | live | yes |
| contract 120: security headers on replies | seen in `curl -i` (CSP, nosniff, no-referrer, same-origin, no-store) | yes |
| contract 214/222: summary keys, counts keys, data-map keys, `login`/`encryption_at_rest`/`masking` false, `host_check`/`origin_check` true | live JSON | yes; `masking` text: F3 |
| contract 190: `GET /leads/{id}` has owner/step/reminder null when flow off; `POST /leads/{id}/step` -> 404 `no_state` | live | yes |
| contract 227-233 fakes: outbox keyed sent/already_sent, bad body 400 bad_body, info keys, crm put/already_present, crm/fields set / 404 no_contact, control bad target 400 bad_control, reset | live against the fakes server | yes except extra `reminders` key (F4); the error text for no_contact is `{"error": "no_contact"}` 404 as documented |
| contract 131: exit codes 1/2/3/4/5 | 1 (demo server unreachable), 4 observed; 2, 3, 5 NOT run | partly |
| contract 136-138: need = 4 x 1024 + 96 = 4192; `FD_RESERVE_ITEMS` sum <= 96 | arithmetic from constants; item sum = 66 | yes |
| contract 156-157: `DRAIN_TOTAL_SECONDS` 1, header/body 10 s, `REPLY_WRITE_TIMEOUT_SECONDS` 5, `REQUEST_TIMEOUT_SECONDS` 30, `LINGER_MAX_SOCKETS` 16, `LISTEN_QUEUE` 1024, `PORTAL_MAX_INFLIGHT` 8 | constants | yes |
| contract 161/168: `MAX_CONNECTIONS` range 8-4096, `MAX_HANDLER_THREADS` 8-65536 | `MAX_CONNECTIONS_MAX`=4096, `MAX_HANDLER_THREADS_MAX`=65536 present (lower bound 8 not looked at) | partly |
| contract 241-: schema: `user_version` 1, triggers `followups_no_delete`, `later_decisions_no_update/_delete`, indexes `receipts_open_ix`, `followups_active_ix`, `receipts_time_ix`, `leads_email_key_uq`, view `review_items` | `schema.sql` | yes |
| contract: `DECIDE_FAIL_LIMIT` 3, write deadline 10 s, request deadline 15 s, `DRIVE_MAX` 8, `REAPER_PASS_SECONDS` 10, `OUTBOX_REFRESH_SECONDS` 30, `REPLY_MAX_BYTES` 1 MiB | `gate.py`, `constants.py` | yes |
| contract 84: `allow_reuse_address = (os.name != "nt")`, `SO_EXCLUSIVEADDRUSE` under win32 | `server.py` 300-316 | yes |
| contract 68/71: `pythonpath = ["src", "."]`; quality commands `ruff`, `mypy --platform linux|win32`, `bandit -ll -r src tools scripts -c pyproject.toml`, `python scripts/check_schema.py` | `pyproject.toml` lines 10, 38, 42; `scripts/check_schema.py` exists | yes (tools not run) |
| contract 129: fakes flag `--crm keyed|blind` | not run (`--outbox`, `--port` used and worked) | cannot check |
| contract 135, 149 SIGTERM/shutdown timing (reaper join 10 s), 408 stall, Windows items, container ulimit | not run / Windows only | cannot check |
| contract 240-: burst script command line and output lines | not run | cannot check |
| contract "Known limits": "no test proves it" for the put-side stale-answer rule | honest statement; not checked | cannot check |
| SECURITY: no secrets needed with defaults; the six real-service settings need a key/password FILE | matches settings (key via file paths); `hubspot_probe.py` reads its token from an env var named by `--token-env` | yes |
| SECURITY 59: LICENSE exists; `.github/workflows/` exists | `LICENSE`, `codeql.yml lint.yml semgrep.yml sonar.yml` | yes |
| SECURITY 38: sales@hadavin.com, GitHub "Report a vulnerability" button | outside the clone | cannot check |
| SECURITY 57: `DESK_FAKES_URL`, `DESK_SMTP_HOST`, `DESK_OUTBOX=smtp` accept only this computer's own address | `example.com`, `8.8.8.8`, `10.1.2.3` all refused exit 4 | yes |
| SECURITY 57: real service + non-loopback bind refused | exit 4, shown above | yes |

## 7. Time per part (container clock, UTC / IST = UTC+5:30)
- Setup (clone, venv, hash-locked install, reading docs): 12:33 - 12:34 UTC (18:03 - 18:04 IST).
- Part A (89 + 104 + 23 desk start trials, plus helper-script checks): 12:34 - 12:41 UTC (about 7 min; trials ran in the background while Parts B and C were done).
- Part B: 12:36 - 12:37 UTC (about 1.5 min for the steps, plus 3 min of JS and header checks).
- Part C: 12:37 - 12:41 UTC (about 4 min).
- Total about 9 min wall of the 50 min time box; hard stop 14:20Z not near.
Progress lines appended to `evidence/raw/progress-Q5b.txt`.

## 8. What I did not check
Browser behaviour (masking, eye button, polling, buttons paused), banners in a live real-service run, `DESK_SMTPP_STATS_FILE`/`CA_FILE`/`HUBSPOT_STATS_FILE`, per-entry leadflow-file bounds, 408 stall, open-file limit exit 3, bind-retry exit 5, lock exit 2, Windows items, every test named in the documents (only existence checked, none run), the burst script, the load tools, the scrub tool rules.
