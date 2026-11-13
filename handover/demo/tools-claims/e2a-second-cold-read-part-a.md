# e2a: fresh verification of README.md, SECURITY.md, contract.md, docs/limits.md, docs/settings.md, docs/portal.md

Studio folder note: the studio folder does not exist in this container, so no bible R-numbers were read or cited; I went on with the task.
Role: FRESH VERIFIER, read-only. Tree: /tmp/e2-tree. Diff: /tmp/work/d/e2-diff.diff (only the hunks of my six files). No lint, no pytest, no network, no agents, no file changes except this report. I read code and tests with grep/sed only; I did not run anything from the tree.
Line numbers are lines of the file in /tmp/e2-tree (not diff lines).

Method limit (honest): the diff for my six files holds roughly 150 changed paragraphs, many with several facts. I checked every named test, every route, setting, default, exit code, constant and portal string I could find in the added text. Test and function names: all 47 `test_*` names cited in the added lines exist as a function or a file (grep `def <name>` / file list). Where a sentence is only a negative ("no test checks X") I grepped for X but a grep cannot prove an absence, so those are marked UNPROVEN.

## 1. FALSE rows (fix these)

| file:line | sentence (short, exact words) | verified how | verdict | exact replacement |
|---|---|---|---|---|
| README.md:8 | "small demo server programs for the CRM, the mail system and the AI step (a demo server that gives each lead a label, hot, warm or cold, from pre-written answers)" | `scripts/start_all.sh:25-27` starts only `demo_only.fakes_server` (CRM + mail in one process) and `lead_desk.server`; `src/lead_desk/loader.py:101` builds `fakes.RecordedQualifier(replies)` in-process from `replies.json` (`demo_only/fakes.py:112`, docstring "In-process"). No AI demo server is started. | FALSE | "small demo programs: one demo server that plays the CRM and the mail system, and a list of pre-written answers that plays the AI step (it gives each lead a label, hot, warm or cold)", so nothing real is sent. |
| contract.md:7 | "(all are also in the HTTP table further down; repeated here as a checklist)" | grep `method_not_allowed`, `not_implemented`, `HEAD`, `OPTIONS`, `bad_request` in contract.md: they occur only at lines 12, 15, 16 (the checklist), none in the table that starts at line 182-ish. | FALSE | "(most are also in the HTTP table further down; the wrong-method row, the unreadable-request row and the `HEAD`/`OPTIONS` row are only here)" |
| contract.md:227 (the `GET /api/ui/data-map` row) | "`CRM (demo server)` for the demo server" | `src/lead_desk/portal_api.py:933` `_CRM_STAND_IN: Final = "CRM (stand-in)"`; `tests/portal_fixtures/data-map.json` and `tests/test_mode_safety.py` hold "CRM (stand-in)"; no source holds "CRM (demo server)". | FALSE | "`CRM (stand-in)` for the demo server (that is the exact text the page shows)" |
| contract.md:305 | Hint quote: `"The CRM may or may not hold this lead. Look in the CRM, then answer crm_present (the row is there) or not_sent (the row is not there). sent is refused: no email was tried."` (given in quotation marks as the hint text) | `src/lead_desk/desk.py:215-219` `HINT_CRM_UNCONFIRMED` is: "The CRM may or may not hold this lead. Look in the CRM, then answer crm_present (the row is there: Retry goes straight to the email) or not_sent (the row is not there: Retry asks the CRM again). sent is refused here: no email was ever tried." The second quote on the same line (unknown row, CRM done) matches `HINT_EMAIL_UNKNOWN` word for word (TRUE). | FALSE (first quote) | Replace the first quote by the code text above, or write "(a sentence that says ...)" instead of quoting. |
| docs/limits.md:46 | "A call that never ends keeps that lead's CRM status behind for good ... It also holds one of the 8 CRM places until the desk restarts (`test_busy_lead_waits_longer_each_time`)" | Opened `tests/test_codeant_desk.py:180-205`: the test asserts `waits[0] == 10`, that the waits grow, that the CRM was asked once and that after `release` the lead is copied. It does not test "for good", the 8 places, or the values 60, 180, 420. The values themselves are TRUE by `desk.py:825-826` and `constants.py:159`. | FALSE (test attribution) | Put the citation on the wait sentence only: "The lead waits 10, 60, 180, then 420 s ... (`test_busy_lead_waits_longer_each_time` checks the first wait of 10 s and that each later wait is longer)". Say of "for good" and "holds one of the 8 places": "read from the code; no test checks it". |

### Wording defects found while checking (copy errors, not taste)
| file:line | text | fix |
|---|---|---|
| README.md:126 | "against the demo demo servers" | "against the demo servers" |
| SECURITY.md:3 | "made-up data and demo demo servers only" | "made-up data and demo servers only" |
| docs/settings.md:13 | "use a local demo server server" | "use a local demo server" |
| docs/limits.md:98 | "The demo HubSpot demo server (`demo_only/fake_hubspot.py`" | "The demo HubSpot server" |
| README.md:20 | "the same person through the other entrance (web form or webhook)" while the same README defines the word "Door" and uses it in line 9 | use "door" once explained, so one word keeps one meaning (rule 14) |

## 2. New sentences that contradict another sentence

1. README.md:8 (AI step is a demo server) contradicts README.md "Words used here" ("small programs ... play ... the AI step") only in part, and contradicts `loader.py:101` and the "two demo servers" step 5 line (README.md:68, unchanged context): `start_all` starts ONE demo server plus the desk (`start_all.sh:29`: "started: demo servers (...) pid X, desk pid Y"; README Windows block says "prints started: ... with two process ids" = fakes server + desk). Step 5 "the two demo servers and the desk" is itself wrong by the code (one demo server and the desk); fix to "the demo server and the desk".
2. docs/settings.md:3 defines "this computer's own address" as `localhost`, "any IPv4 address starting with 127", or `::1`, but `src/lead_desk/config.py:64-78` (`is_loopback_host`) also accepts IPv4-mapped forms (`::ffff:127.x`) and bracketed `[::1]`; the n8n bullet (docs/settings.md, "scripts/n8n_api.py ... reads N8N_URL") lists the mapped form and then says "as defined at the top of this file". Not false, but the two lists differ. Suggested: add "or an IPv4 loopback address written in the `::ffff:` form" to the line-3 definition. Also `DESK_SMTP_HOST` (docs/settings.md row "DESK_OUTBOX=smtp") accepts only an IP address (`smtp_outbox.py:81-89`), not the name `localhost`, which the line-3 definition includes; the row says so ("refuses a name"), so no contradiction in effect, but a reader of SECURITY.md ("accept only this computer's own address") could think `localhost` works for `DESK_SMTP_HOST`.
3. No other contradiction found between the new sentences (README "within 90 seconds" vs `demo_only/leadflow.json` `nudge_after_seconds: 90` agree; README "16 min 33 s ... earlier set" vs `docs/tests.md:79` agree; limits.md "2462 passed, 3 skipped, 2465 tests, commit 558d37f" agrees with `docs/tests.md:78` and `versions.md:9`).

## 3. UNPROVEN rows (depend on a past run, a person or an outside fact)

| file:line | sentence | why UNPROVEN | depends on |
|---|---|---|---|
| README.md:130, docs/limits.md:70 | "Linux with Python 3.13 and `requirements-dev.txt` was also run once ... and passed" / "3684 passed, 0 failed, 199 skipped" | Same text is in `docs/tests.md:83`, but no log is shipped | past run of a separate tester |
| README.md:130 | "A separate run of the desk's tests reported about 20 minutes on a later, larger set" | `docs/tests.md:83` says so; no log | past run |
| README.md:130 | "last timed in this repository at 16 minutes 33 seconds on an earlier, smaller set" | matches `docs/tests.md:79` (2516 tests, 993 s); no log | past run |
| README.md:120 (and limits.md:16) | "Only `scripts/hubspot_probe.py` touched a real service (one free HubSpot account ...)" | author's own run, no log | person |
| README.md:20 | demo outbox "holds exactly one email, if you look within 90 seconds ... about 90 seconds after the lead arrives it adds a second email" | Mechanism is TRUE in code (`leadflow.json` 90 s; `start_all.sh:16-17`; `fakes_server.py:83-88` `count` counts all stored messages, reminders included, key prefix `nudge:`); the exact timing (reaper pass every 1 s, `REAPER_INTERVAL_SECONDS`) was not run | real timing |
| contract.md:123 | "a mutation check reported by a separate run, with the load and the bind swapped, still passed it unless the bound socket was kept alive" | the test body (`tests/test_portal_api.py:1549-1560`) matches the description (it only checks that the port is free after the failure); the mutation result itself is a past run | past run |
| contract.md:270 | "`tests/test_input_edge_cases.py` sends a deeply nested request body, but on Python 3.12.3 that body already ends at the check that the payload must be an object ... (a mutation check from a separate run)" | `test_input_edge_cases.py:26-30` builds `"payload": [[[...` (a list, not an object) and `test_desk_http_edge_cases.py:1074-1076` sends nesting inside a dict straight to `Desk.process`, which fits; what the 3.12.3 parser does first was not run here | past run, Python version |
| contract.md:321 | "No test checks the counting in either mode." (start-up with and without a reaper) | negative; grep of tests for `startup`/`start_background` with `attempts` found none, but absence cannot be proved by grep | negative claim |
| README.md:100 | "A plain request for `/` was not tested either; only one odd request whose path is `/` is" | `grep '"GET", "/"'` and `GET / HTTP` found only `tests/test_slow_sender.py:762` (a hand-built handler, not a request) and `test_unparsable_target_is_json` (`"http://a:b:c/"` gives path `/`, 404); `/health` has no hit in tests | negative claim |
| docs/limits.md:64 | "in that run every follow-up ended `sent` (what such a kill run shows can differ from run to run ...)" | author's own Linux run, no script or log | person |
| docs/limits.md:139 | "after a restart the next try is expected to happen at once (not tested)" | code: the wait is held in memory (`desk.py:825`, `_mirror_not_before`), the try count in `lead_state.crm_tries` (`schema.sql:95`), which agrees; not tested, as the text says | not run |
| docs/limits.md:139 | "a mutation check reported by a separate run changed 420 to 400 and the test still passed" | what the test checks is TRUE (`tests/test_mirror_gate.py:131-133` compares to `MIRROR_RETRY_WAIT_SECONDS`, no literal 10/60/180/420; the only literals near are 400 at lines 72/207 and 151); the mutation run is a past run | past run |
| docs/settings.md (HubSpot bullet), limits.md:157 | "The `docs/hubspot-probe.md` runs ... showed one write (`OPEN`) accepted"; "the adapter was not run against any real HubSpot account" | `scripts/hubspot_probe.py` imports no `lead_desk` module (grep of its imports), so "probe not adapter" is TRUE; "showed ... accepted" is the author's own run | person |

## 4. TRUE rows (checked), by file

### README.md
| line | sentence (short) | verified how | verdict |
|---|---|---|---|
| 8 (rest) | "the desk may hand over the same email again after an unclear result, and the demo mail system ignores the repeat"; "does not guess and does not resend" on blind | `gate.py:53` backoff, `contract.md` keyed/blind rows; `adapters.py:200` `send(send_key ...)`; `tests/test_flow.py:25-40` (message key == lead_id) | TRUE |
| 20 | "The same person through the other entrance ... gets `"verdict": "duplicate"`" | `tests/test_flow.py:30-33` | TRUE |
| 33 | "refuses a few unusual characters ... such a request goes to review" and "does nothing else to it" | `identity.py:44-46` `normalise_email` = strip + lower; `identity.py:90-98`, `:125-128` `invalid_email`/`bad_field` | TRUE |
| 44 | verdict `review` "(the request is incomplete or holds a value the desk will not store ...)" | `identity.py:104-128` | TRUE |
| 52-53 | keyed/blind and UNKNOWN "or whether the CRM row was written" | contract hints; `desk.py:215-219` (`crm_unconfirmed`) | TRUE |
| 54 | "ten [crash points], and an eleventh, N1" | `hooks.py:14,19` (5 + 6 incl. N1 = 11) | TRUE |
| 55 | reaper retries "1, 2, 4 and 8 seconds, up to 5 automatic tries" | `gate.py:51,53` | TRUE |
| 61, 65, 101 | wording about tried combinations; "ports 8765 and 8766" | `docs/tests.md:9,54` | TRUE |
| 79 | `sh` on Debian/Ubuntu stops with "run this script with bash" (exit code 2) | `start_all.sh:12`, `reset.sh:7` | TRUE |
| 101 | `tests/test_http.py` checks 404 for other unknown addresses | `test_http.py:155-158` (`/nope`) | TRUE |
| 104 | reset exit codes 2/3/4/5/6; "(Linux) `ps` is not installed while a pid file exists"; empty value means 10; "a pid file ... names another program" | `reset.sh:8-12,21-24,41-46`; `reset.ps1:6-12,36,40,47`; `reset_check.py:36-52` (3 and 4) | TRUE |
| 114 | "All ten were simulated by an exception ... D2 also tried with a real process kill" | `tests/test_crash_points.py:70-84` (`SimulatedCrash` over `ALL_HOOK_POINTS`), `tests/test_http.py:292-336` (real kill D2; keyed, blind, SMTP) | TRUE |
| 114 | "`contract.md` says that not every path is covered" | `contract.md:294` "(no test covers every path)" | TRUE |
| 115 | "the only repeat it makes is the same email with the same send key" | `desk.py:2023` sends with `lead_id` as key; reminders use another key `nudge:<lead>` (`constants.py:152`), but that is a different email | TRUE |
| 127 | "with any real service connected, the desk refuses to start on any other address" | `config.py:465-475`, `server.py:1133-1134` | TRUE |
| 128 | masked by default: names, emails, phones, messages, request numbers; session storage | `portal.js:206,214-217,171` | TRUE |
| 140 | approval mode example "(for example a new phone number)" | `tests/test_flow.py:28-34` (`phone` differs gives `differing_fields == ["phone"]`) | TRUE |
| 141 | "waiting time set in the file (90 seconds in the demo file)", "does not depend on whether the follow-up email was sent", "Off when ... unset, empty or the word `off`" | `leadflow.json`; `config.py:600`; `settings.md` reminders text | TRUE |
| 143-144 | WARNING: "when the lead's owner has a CRM owner id, that owner id"; `tests/test_lead_crm_copy.py` "has a check that the request body holds only these two properties"; "through the route that moves a lead" | `crm_hubspot.py:396-405`; `test_lead_crm_copy.py:162` asserts the exact PATCH body `{"properties": {"hs_lead_status": "WON", "hubspot_owner_id": "3"}}` (note: lines 89 and 132 do not check "only two"; line 162 does) | TRUE |
| 147 | "A later message is a second request for the same email address" | contract duplicates section | TRUE |
| 152 | "three n8n workflows that send leads to the desk (`n8n/`)" | `n8n/desk-form.json`, `desk-webhook.json`, `proof.json` (the third sends ten requests, per its node names) | TRUE |
| 165-167 | docs/real-services.md "has not been run against real services"; probe "run once" | author's statement, same as limits.md | see section 3 |

### SECURITY.md
| line | sentence | verified how | verdict |
|---|---|---|---|
| 5-6 | "Real customer data is not meant to go into it ... until a person has done the checks listed in the README under 'Optional features'" | README.md:120 "Required before you point this at a real CRM: ..." exists | TRUE |
| 20 | `lint.yml` "is set up to run a secret scanner over the files and over the whole history" | `.github/workflows/lint.yml:30` `fetch-depth: 0`, `:49` `gitleaks dir .`, `:50` `gitleaks git .` | TRUE |
| 20 | "`tests/test_hygiene.py` scans too" | `test_hygiene.py:124-125,193-197` | TRUE |
| 21 | `DESK_QUALIFIER=live_claude` "(a real AI model from Anthropic ...)" | `constants.py:170` `https://api.anthropic.com` default | TRUE |
| 23 | IMAP is "the protocol for reading a mailbox"; run_real_check IMAP needs a password file | `run_real_check.py:14-17` | TRUE |
| 25 | `N8N_API_KEY_FILE` named, `run_live_check.py` uses a key file | `n8n_api.py:3,97`; `run_live_check.py:6` | TRUE |
| 26 | `DESK_FAKES_URL`, `DESK_SMTP_HOST`, `DESK_OUTBOX=smtp` accept only this computer's own address; "start only on a loopback `DESK_BIND`" with a real service | `config.py:517`, `smtp_outbox.py:81-89`, `config.py:465-475` | TRUE |

### contract.md
| line | sentence | verified how | verdict |
|---|---|---|---|
| 17 | 503 busy row: "on `POST /leads` the receipt id, or `null` ...; not present on other routes"; connection-limit row is "the next row" | `desk.py:463-469` `_error_reply(... with_receipt)`; callers at 1394 (with) and 2142/2237/2323/2370/2379/2415 (without); table order lines 17-18 | TRUE |
| 20 | no `hint` for `in_progress`, `unknown_needs_person`, `not_retryable`, `already_decided` | `desk.py:2225,2228-2229,2362` | TRUE |
| 25 | lone surrogate in name, email, phone, company or message: `bad_field:<field>` | `identity.py:105-114`; `tests/test_input_edge_cases.py:9` | TRUE |
| 28, 33 | claim moves `pending` to `sending`; start-up check text; exit code 1 traceback | `contract.md` start-up lines; `constants.py` budget numbers (9, 15, 25) | TRUE |
| 36 | `GET /review` and "stalled items" | `desk.py:269` stalled select | TRUE |
| 57, 62 | step 1 in the server, step 4 in the desk after the item was found | `desk.py:2262-2268` (kind dispatch precedes the `decision not in _RESOLVE_DECISIONS` check) | TRUE |
| 90 | 3a (d) one transaction, first writer wins `ON CONFLICT DO NOTHING`, six keys | `desk.py:2362` (`DECISION_KEYS`) | TRUE |
| 113-122 | read-only connection; `sqlite3.connect` once in `connect_readonly`; at most 8 at once; buttons paused on offline or a 5xx on summary or review | `portal_api.py:97-100`; `constants.py:226`; `portal.js:583-584` `STALE_KEYS = ['summary','review']` | TRUE |
| 119 | `q` matches company and lead id; with `by_email=1` (default) also name, email, first request number | `portal_api.py:311-328,376` | TRUE |
| 123 | extension is loaded "before the socket is bound (in `make_server`)" | `server.py:1023-1024` | TRUE (test claim: see section 3) |
| 124 | failed-follow-up card wording | `portal_api.py:604-626,729-735` (card shown only when `not maybe_sent`; the later sentence about `ambiguous_prior` covers this) | TRUE |
| 134 | `lockfile.acquire` raises `LockHeldError` (an `OSError`), start-up exit code 2; `LockUnavailableError` also `OSError`, exit 2 | `lockfile.py:12,16,41-76`; `server.py:1143-1148` | TRUE |
| 138 | exit code 1 "the demo servers cannot be reached at start-up" | `server.py:1166-1169`, `constants.py:256` | TRUE |
| 155 | "any other error gives 500 ... except `/api/ui/*` 'not ready' faults give 503 `unavailable`" | `portal_api.py:144,165` | TRUE |
| 206 | `GET /leads/{lead_id}`: `attempts` "never lowered, so it can be above 5 while the cap of 5 automatic tries still holds" | `gate.py:51,1961-1962` (`auto_attempts` cap) | TRUE |
| 227 (rest) | `mode.sample_data`, banner text, `mail_sender`, "Hide names and email addresses" switch, `portal_actions` | `portal.js:652`; `leads.js`/`log.js` label; `portal_api.py:1014` | TRUE |
| 227 | log row: "the test in `tests/test_portal_log.py` plants email, phone, company and message values and finds none in the log; the lead's name and the request number are shown on purpose" | `test_portal_log.py:172-200` | TRUE |
| 262 | "With `expected` given, `ok` is true only when ...; with no `expected`, `ok` is `null`" | `desk.py:2425-2435` | TRUE |
| 312 | start-up order "(the order the server uses)"; "a new row after 2 s, a retried row after its backoff" | `server.py:1195-1196`; `gate.py:48,87` | TRUE |
| 270 | `tests/test_desk_http_edge_cases.py` sends deep nesting straight to `Desk.process` | `test_desk_http_edge_cases.py:1074-1076` | TRUE |

### docs/limits.md
| line | sentence | verified how | verdict |
|---|---|---|---|
| 8-9 | item 3: "At most 4 AI calls, 8 CRM writes, 8 sends and 4 reads of the keyed or blind setting" | `constants.py:86` | TRUE |
| 14 | "a keyed demo server mail system then ignores the repeat" | keyed outbox semantics, `fakes_server` | TRUE |
| 21-25 | `Desk._bounded` waits 9 s for AI and `min(send_timeout_seconds, 9 s)` for CRM/send/refresh; time-out effects (AI try used, keyed same key, blind unknown) | `desk.py:1433-1437`, `1558-1565`; `constants.py:80,82` | TRUE |
| 40-45 | CRM copy waits 10/60/180/420; start step of earlier failed tries (2 tries gives 60 s, 3 gives 180 s); kept in memory | `desk.py:825-826` (`step_i = max(tries_before,1)-1+busy-1`), `constants.py:159` | TRUE |
| 47 | "Wait until the `send` and `crm` counts in `hung_workers` are back to 0" | `desk.py:2272-2274` (`call_running` = send or CRM call) | TRUE |
| 61 | "send key (the lead's id)" | `desk.py:2023`, `test_flow.py:40` | TRUE |
| 66-70 | test-run figures, 2464 = 2462 + 2, 558d37f run in `docs/tests.md` | `docs/tests.md:78-83`, `versions.md:9` | TRUE (runs: section 3) |
| 94-95 | burst script prints `RESULT sent=<n> expected=<n>` exit 0, or `MISMATCH` exit 1 | not opened in `demo_only/burst.py` in this pass | see note below |
| 118-120 | portal 8 at once; `refused_at_door` | `constants.py:226`, `portal_api.py:278` | TRUE |
| 124 | "Exit codes ... 1 the demo servers cannot be reached at start-up" | see contract.md:138 | TRUE |
| 126 | "the desk stops serving a client that does not read its reply after that time" (5 s) | `constants.py:215` | TRUE |
| 133-134 | `DESK_BIND` of 0 / four zeros "means every network address; the desk treats it as reachable by others" | `tests/test_portal_api.py` `test_all_digit_bind_is_wildcard`; `server.py:1197-1200` prints a warning for a non-loopback bind | TRUE |
| 143 | WARNING paragraph: request-body claim and "when the lead's owner has a CRM owner id" | `crm_hubspot.py:396-405`; `test_lead_crm_copy.py:162` | TRUE |
| 138-139 | mirror: five tries, `MIRROR_RETRY_WAIT_SECONDS`, "number of tries already made is kept in the database" | `constants.py:155,159`; `schema.sql:95` | TRUE |

Burst-line note: the added text for `demo_only/burst.py` ("exit code 0 ... exit code 1") was not opened in this pass; I ran out of reading budget there. Treat it as UNCHECKED, not TRUE (grep `MISMATCH` / `sys.exit` in `demo_only/burst.py`).

### docs/settings.md
| line | sentence | verified how | verdict |
|---|---|---|---|
| 3 | loopback definition | `config.py:64-78` | TRUE but incomplete (section 2) |
| 7 | `bind`: "`DESK_OUTBOX=smtp` does not count as a real service" | `constants.py:122` `OUTBOX_STAND_INS = ("http","smtp")`; `config.py:451-463` | TRUE |
| 13 | `crm` and `outbox` rows | `config.py` | TRUE (typo: section 1) |
| 16 | `nudge_to` refused in three cases | `config.py:482-486,507-508` | TRUE |
| 17 | `leadflow_path`: "a file whose name is exactly `off` cannot be used" | `config.py:600` | TRUE |
| 33 | "600-second ceiling ... Values above 9 are accepted, but the desk cuts every send at 9 seconds" | `constants.py:116`, `desk.py:1437` | TRUE |
| 44 | `DESK_SEND_TIMEOUT_SECONDS`, `DESK_SMTP_TIMEOUT_SECONDS`: "above 9 accepted but has no effect" | `smtp_outbox.py:79,97,226`; `desk.py:1437` | TRUE |
| 49-50 | `DESK_LIVE_TIMEOUT_SECONDS` above 0, at most 9; `DESK_LIVE_MAX_TOKENS` 1 to 1000000 | `config.py:161-165,208-214`; `constants.py:186` | TRUE |
| 57 | `rota` entry must contain `crm_owner_id`, `steps` 3 to 12, `closed` outside `steps` | `config.py:312-345` (`file_steps = len(self.steps) - 1`) | TRUE |
| 63 | "checked whenever the desk starts, whether from the start script or from your own program" | `desk.py:362` and `server.py:1160` both call `reminder_setting_problem()` | TRUE |
| 65 | reminder text "names only the first 8 characters of the lead number, the owner and the step" | `desk.py:993-995` (`lead_id[:8]`) | TRUE |
| 71 | `DESK_SMTP_TIMEOUT_SECONDS` "has no practical effect: it is used only when a send is made without a time limit" | `smtp_outbox.py:15,226` | TRUE |
| 78 | `DESK_SMTPP_TIMEOUT_SECONDS`: "a smaller `DESK_SEND_TIMEOUT_SECONDS` wins and a larger one is ignored" | `smtp_provider.py:241,319-323` | TRUE |
| 79-80 | `DESK_SMTPP_MAX_SENDS` counted in memory; `DESK_SMTPP_STATS_FILE`/`DESK_HUBSPOT_STATS_FILE` written, never read by the desk; `DESK_SMTPP_CA_FILE` optional, verification stays on | `smtp_provider.py:89-90,132,188,237-252`; `crm_hubspot.py:149,194,276,362` (only `write_stats`) | TRUE |
| 88 | live step text (ledger, 429, 5xx, caps) | unchanged semantics, spot-checked `live_claude.py:530` | TRUE |
| 98-105 | `scripts/n8n_api.py` bullets, `tools/scrub_n8n_export.py` bullets: re-split, content as before | not re-verified line by line against `tools/scrub_n8n_export.py` | UNCHECKED beyond `n8n_api.py:84` (`is_loopback_host`) |

### docs/portal.md
| line | sentence | verified how | verdict |
|---|---|---|---|
| 5 | Overview groups: New, Repeat, Request to check, Not decided yet | `portal.js:58` | TRUE |
| 6-8 | page names; "Next step:" line; "Hide names and email addresses" | `portal_api.py` ("Next step:"), `leads.js`, `log.js` | TRUE |
| 10 | masking default; request numbers not searched while masked; 30-second eye | `portal.js:206-217`, `portal_api.py:311-328`, `leads.js:339` (`by_email=0`) | TRUE |
| 12 | tests: `test_portal_layout.py` and `test_portal_wording_and_masking.py` check masking on the list reply; log test finds no values | `test_portal_layout.py:203-218`; `test_portal_wording_and_masking.py:287-312` | TRUE |
| 14-16 | banners "Every lead is demo data ..." and "Real services are connected"; demo extension not loaded with a real service | `portal.js:652`; `loader.py:46` | TRUE |
| 18 | "one test tries a write through it and the write fails" | `test_portal_api.py:151-166` | TRUE |
| 22 | paused buttons; "a server error on the Leads list or the Request log alone does not pause them" | `portal.js:583-584` | TRUE |
| 26 | "a mail system that does not report sent mail cannot stop that" | blind semantics | TRUE |
| 28 | `crash` "sets or clears a flag file"; needs no login; only with demo parts | `hooks.py:31`; `loader.py:46` | TRUE |
| 30 | Host check: bind address, `DESK_ALLOWED_HOSTS`, 403 for foreign Host or Origin | `server.py:508-511,737-746` | TRUE |

## 5. Counts

- Facts checked: about 130 sentences across the six files (every added paragraph was read in full).
- FALSE: 5 (README.md:8, contract.md:7, contract.md:227, contract.md:305, docs/limits.md:46), plus 5 copy/wording defects (3 doubled words, 1 doubled "demo", 1 "entrance" vs "door") and 2 contradiction notes (README step 5 "two demo servers"; loopback definition list differs between settings.md lines 3 and the n8n bullet).
- UNPROVEN: 14 rows (past runs of a separate tester, the author's own HubSpot probe and kill runs, mutation-check results, and 3 negative "no test checks" claims).
- TRUE: all other rows listed in section 4.
- UNCHECKED (not read in this pass): the exit-code lines of `demo_only/burst.py` cited at docs/limits.md:94-95 and the re-split `tools/scrub_n8n_export.py` bullets in docs/settings.md:98-105 (their text was only re-wrapped, but I did not diff it against the old lines).

EGM skipped: this is a read-only verification report that judges nothing and changes no file; per rule 13 the lead runs the EGM review of the result.
Files changed: /tmp/work/d/out-e2a.md only. Head SHA: not read (no git command run). R-numbers: none (studio folder not present). No processes, shells or containers started.
