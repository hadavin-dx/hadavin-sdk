# C8 independent cross-check of "numbers and names check: 1046 items, 0 real mismatches"
Runner: EVIDENCE RUNNER (no judging, nothing fixed). Tree: /home/user/build/rr6/tree-C8, head e683069 (read-only).
Date 2026-11-13, 12:33-12:40Z. I did not read the demo session's notes. Python: RR/venv312/bin/python, PYTHONPATH=tree-C8/src (+ tree-C8 for demo_only/load_tools), TMPDIR=RR/tmp-C8.

## Headline
* 70 claim groups checked (about 330 individual values, boundaries counted one by one). 1 MISMATCH found, all others match.
* Not read in full: long table cells and bullet lines were printed cut at 230-420 characters, so the tail of very long lines (settings.md rows 8,12,13,15,16,24,28; limits.md 50,58,60,61,68,71-72,84-89,106-112; contract.md lines 18-31, 85-123, 131-173 and rows 182-225 tails; README 60,68,99,104,108,117,120; tests.md 19,30,34-48,74-82,90-92,101-113,120-137; versions.md 37,40,57-61,69-71,74-75) were NOT read past the cut. Claims in those tails are unchecked.
* Not run: no full pytest, no 408/503 live path, no Windows claim, no real service, no n8n.

## MISMATCH (1)
| # | doc says (file:line) | code/tool says | match |
|---|---|---|---|
| 1 | versions.md:9: `python -m pytest --collect-only -q` "prints one line per test file ... `tests/test_workflow_run_flags.py: 10` (that is its last line), 92 lines in all"; "with `-q` or `-qq` the output is these per-file lines and no total" | pytest 9.2.0 (RR/venv312, Linux, Py 3.12.3): `--collect-only -q` prints one NODE ID per test (3885 lines; last lines are a test id, a blank line, then `3883 tests collected in 4.70s`). Only `-qq` prints per-file lines (92 lines, sum 3883, last line `tests/test_workflow_run_flags.py: 10`). Plain (no -q) ends `3883 tests collected in 5.43s`. Raw: RR/tmp-C8/collect.txt, c-qq.txt, c.txt. Same -q form is used at docs/tests.md:79 for `tests/test_except_clause_hierarchy.py` (gives `52 tests collected`; the number 52 is right, the output shape described is not). | NO (the numbers 3883, 92 files, 52 match; the claimed output of `-q` does not) |

## Matches (doc says | code says | match). "live" = I ran it.
| # | doc (file:line) | code / run | match |
|---|---|---|---|
| 2 | settings.md:7 db_path default `./data/desk.sqlite3` | Config() db_path = data/desk.sqlite3 (config.py, live) | yes |
| 3-9 | settings.md:8-14 defaults bind 127.0.0.1, port 8765, adapters demo, qualifier recorded, outbox http, crm fake, later_mode off | Config() live: same 7 values | yes |
| 10 | settings.md:18 fakes 127.0.0.1:8766 | Config() live | yes |
| 11-13 | settings.md:21-23 send_timeout 5.0, size_cap 65536, stall 120 | Config() live | yes |
| 14 | settings.md:7 `:memory:` refused at start, exit 4, before any file | live: rc=4 "the lead book must be a file", dir empty (0 files) | yes |
| 15 | settings.md:32-38 ranges: PORT 0-65535, FAKES_PORT 1-65535, SIZE_CAP 1-16777216, STALL 0-86400, SEND_TIMEOUT >0..600, SMTPP/HUBSPOT timeout >0..9, MAX_SENDS/MAX_CALLS 1-10000, 429 retries 0-5 | live boundary runs (value, value+1, 0): every edge accepted/refused as stated (e.g. 9 ok 9.1 refused, 600 ok 600.1 refused, 5 ok 6 refused) | yes |
| 16 | settings.md:28 number format: spaces ignored, `8_0` `1e3` empty `nan` `inf` refused | live: ' 80 ' ok; '8_0','1e3','','nan','inf' refused | yes |
| 17 | settings.md:46-58 leadflow: file 16384 B, rota 1-20, steps 3-12, id 32 chars, owner name 64, label 32, crm value 64, owner crm id may be empty but key present, nudge 1-2678400 or null, extra key refused, first<after_followup order, duplicate ids refused | live, 31 boundary cases via read_leadflow: all as stated (size 16385 refused, 0/21 rota refused, 2/13 steps refused, nudge 0 and 2678401 refused) | yes |
| 18 | settings.md:15 approvers: id <=32, name <=64, label <=64, names unique | live via config._check_approvers: 32/33, 64/65, label 64/65, dup refused | yes |
| 19 | settings.md:74,76 SMTPP default port 587 (starttls) / 465 (ssl), msg-id domain example.invalid, timeout 5.0 | live ProviderSettings.from_env: 587, 465, example.invalid, 5.0 | yes |
| 20 | settings.md:84 HUBSPOT timeout 4.5, 429 retries 2 | live HubspotSettings: 4.5, 2 (crm_hubspot.py:91-92) | yes |
| 21 | settings.md:102 live API version 2026-10-21, effort low, timeout 8, max tokens 64 | constants.py LIVE_API_VERSION, LIVE_DEFAULT_EFFORT/TIMEOUT/MAX_TOKENS | yes |
| 22 | settings.md:111-112 key min 8 chars; ledger 8,000,000 bytes | constants.py LIVE_KEY_MIN_CHARS=8, LIVE_LEDGER_FILE_MAX_BYTES=8_000_000 | yes |
| 23 | settings.md:117 REAL_PERSONS 12 (min 8, max 1000), DRAIN 150, MAIL_WAIT 90, SETTLE 10 | run_real_check.py:102-107,873-875 | yes |
| 24 | settings.md:116,120 run_real_check exit 2 refused, 1 stopped, 3 failed | run_real_check.py:96 EXIT_REFUSED,EXIT_STOPPED,EXIT_FAILED = 2,1,3 | yes |
| 25 | settings.md:121 N8N_URL default http://127.0.0.1:5679 | scripts/n8n_api.py:89 | yes |
| 26 | settings.md:107 MAX_CONNECTIONS 256, MAX_HANDLER_THREADS 1024, 10 s deadlines, Retry-After 1 | constants.py (live import) | yes |
| 27 | README:41,99; tests.md:98 ten crash points A,A2,B,L,C0,C1,D1,D1b,D2,D3 + N1 | hooks.ALL_HOOK_POINTS = 11 names, same list (live) | yes |
| 28 | README:42; contract.md:256 waits 1,2,4,8 s, 5 automatic tries | gate.py:51,53 SEND_MAX_ATTEMPTS=5, SEND_BACKOFF_SECONDS=(1,2,4,8) | yes |
| 29 | README:47 ports 8765/8766, Python 3.12+ | config defaults; pyproject.toml:5 `>=3.12` | yes |
| 30 | README:90 reset exits 2,3,4,5,6; RESET_STOP_WAIT default 10, range 0-999 | scripts/reset.sh:9-52, reset_check.py:36-52 (3,4) | yes |
| 31 | README:153; contract.md:237 mail subject/body text | constants.py FOLLOWUP_SUBJECT_TEMPLATE / BODY_TEMPLATE | yes |
| 32 | README:21 counts 2 received/1 new/1 duplicate; replayed id not counted | live: 5 POSTs incl. 1 replay -> received counted 4 distinct; replay not counted; dup 200 | yes |
| 33 | contract.md:11,12,15,16,178 404 not_found, 405 method_not_allowed, 501 not_implemented, HEAD 404/405 no body, OPTIONS 405 | live: 404, 405, TRACE 501, HEAD /nope 404 (empty), HEAD /counts 405, OPTIONS 405 | yes |
| 34 | contract.md:13,210 `/counts?expected=` x / -1 / empty -> 400 bad_expected; N -> 200 | live: 400,400,400; =2 -> 200 | yes |
| 35 | contract.md:182-186 201 new / 200 duplicate / 202 review incomplete:email / 400 bad_envelope / 413 too_large | live: 201,200,202,400,413 with the stated bodies | yes |
| 36 | contract.md:182,244 source_ref 1-128 chars | live: 129 -> 400, 128 -> 201; constants SOURCE_REF_MAX=128 | yes |
| 37 | contract.md:178 replay returns `"replayed": true` and `"payload_matches"` | live replay body has both | yes |
| 38 | contract.md:211,213 GET /ui -> 308 Location /ui/ ; unknown file 404 | live: 308 + `Location: /ui/`; /ui/nope.txt 404 | yes |
| 39 | contract.md:86-88,225 403 forbidden_host / forbidden_origin; Sec-Fetch-Site same-origin or none | live: Host evil.test 403 forbidden_host; Origin null 403; cross-site 403; none 200 | yes |
| 40 | contract.md:120 every reply carries CSP, nosniff, no-referrer, CORP same-origin, no-store | live /counts and /ui headers show all 5 | yes |
| 41 | contract.md:209 /counts keys | live /counts: all 19 listed keys present, hung_workers{model,crm,send,refresh} | yes |
| 42 | contract.md:216,221 /api/ui bad_query: leads limit max 100, log limit max 200, q max 100 | live: limit 101 -> 400 field limit, 100 -> 200; log 201 -> 400, 200 -> 200; q 101 -> 400, 100 -> 200 | yes |
| 43 | contract.md:33-34,38-40 MODEL_HUNG_MAX 4, MODEL_BUSY_BACKOFF 5 s, margin 15 s (10+5), smallest grace 25 s, 9+15=24, grace 30 s (5+5x5) | gate.py:47,67,72; constants.py:MODEL_*; arithmetic checked | yes |
| 44 | contract.md:134-138; limits.md:119 open files 4 x 1024 + 96 = 4192; exit 3 below that | live with hard limit 4000: rc=3 "needs about 4192 open files ... limit is 4000" ; FD_RESERVE_ITEMS sum 66 <= 96 | yes |
| 45 | contract.md:131; limits.md:121 exit codes 1,2,3,4,5 | live: 1 (demo servers down), 2 (second desk same db), 3 (fd), 4 (bad port; wildcard bind + hubspot; :memory:), 5 (port busy) | yes |
| 46 | contract.md:148 accept pause 0.05 s | constants.py ACCEPT_PAUSE_SECONDS=0.05 | yes |
| 47 | contract.md:253,311 32 places in flight, 5 s wait; drives 8 places | gate.py:19-23 INFLIGHT_MAX 32, DRIVE_MAX 8, waits BUSY_WAIT 5 | yes |
| 48 | contract.md:247 3 failed tries (DECIDE_FAIL_LIMIT) | gate.py:41 = 3 | yes |
| 49 | contract.md:308-310 refresh 30 s, reaper pass 10 s, write deadline 10 s, request deadline 15 s | gate.py:28,36,24,26 | yes |
| 50 | contract.md:264 item id > 18 chars -> 404 | constants.py MAX_DIGITS=18 | yes |
| 51 | contract.md:266 adapter reply limit 1 MiB | constants.py REPLY_MAX_BYTES=1_048_576 | yes |
| 52 | contract.md:271-272 user_version 1; columns payload_conflict, crm_done, auto_attempts, ambiguous_prior, send_started; indexes receipts_open_ix, followups_active_ix, receipts_time_ix, leads_email_key_uq | schema.sql:2,18,57-60,43,118-120 | yes |
| 53 | contract.md:278 lock file replaced: 3 tries | lockfile.py:24 _LOCK_TRIES=3 | yes |
| 54 | contract.md:123 `just now` under 5 s; Leads table hides 2 columns up to 1300 px | portal.js:188; pages/leads.css:67-69; tests/test_portal_layout.py:76 | yes |
| 55 | limits.md:81 worst pass 10 + 27 + 18 = 55 s | gate.py:32-36 comment and REAPER_PASS 10.0, 3x9, 2x9 | yes |
| 56 | limits.md:129 copy waits 10, 60, 180, 420 s, five tries, about 11 minutes | constants.py MIRROR_RETRY_WAIT_SECONDS (10,60,180,420)=670 s, MIRROR_MAX_TRIES 5 | yes |
| 57 | limits.md:40 (caps) 4 AI, 8 CRM, 8 sends, 4 reads | constants.py ADAPTER_WORKER_CAPS | yes |
| 58 | limits.md:105,114 portal 8 at once; 256/1024 limits; evict 2 s; reply write 5 s | constants.py PORTAL_MAX_INFLIGHT 8, MAX_*, EVICT_MIN_IDLE 2.0, REPLY_WRITE 5.0 | yes |
| 59 | limits.md:112 later-messages answer bound 3,132,800 bytes | tests/test_later_messages.py:166 asserts `bound == 3_132_800` (test not run) | yes (by assertion text only) |
| 60 | limits.md:97 fake HubSpot: Content-Length >7 digits or >1 MiB -> 400 unread | demo_only/fake_hubspot.py:177,195-200 (len <= len(str(1_048_576)) = 7) | yes |
| 61 | versions.md:44-54,65-67 pins pytest 9.2.0, ruff 0.17.4, bandit 1.9.4, mypy 2.4.1, iniconfig 2.3.1, pluggy 1.7.0, librt 0.16.0, rich 15.0.0, pyyaml 6.0.3, packaging 26.3, pygments 2.21.0, stevedore 5.9.1, typing-extensions 4.16.0, pathspec 1.1.1, colorama 0.4.6 (win only), playwright 1.63.0, greenlet 3.5.6, pyee 13.0.1 | requirements-dev.txt, requirements-dev-win.txt, requirements-browser.txt greps: all identical; colorama only in -win | yes |
| 62 | versions.md:31-35 actions v7.0.1, v7.1.0, codeql v4.39.3, cache v4.3.0, sonar-scan v8.4.0 | .github/workflows/*.yml pin comments | yes |
| 63 | versions.md:24 anthropic-version 2026-10-21; :57 uv 0.11.32 | constants.py:LIVE_API_VERSION; requirements-coverage.in:4 | yes |
| 64 | versions.md:9 3883 tests, 92 per-file lines, 52 in test_except_clause_hierarchy; arithmetic 2449+15=2464, 2462+2=2464, 2462+3=2465, 2516-2465=51 | `pytest --collect-only` (plain and -qq): 3883, 92, 52; arithmetic ok (the `-q` wording is row 1) | yes (counts) |
| 65 | n8n-recipe.md:44,54,27,22; limits n8n lines: 3 nodes per desk workflow, paths desk-form / desk-webhook / proof-run, retry 3 tries 1 s, 5679, only Webhook/Edit Fields/HTTP/Code/Manual nodes | n8n/*.json parsed (live): 3,3 nodes; paths and URLs as stated; maxTries 3, waitBetweenTries 1000; proof node types webhook,set,code,httpRequest,manualTrigger | yes |
| 66 | hubspot-probe.md:11,14,31,33,52; settings 36 | `scripts/hubspot_probe.py --plan` (live, no network): "planned calls: 7 (hard budget 8 ...)"; CALL_BUDGET 8; owners limit=10; id last 4 chars; msg [:100]; default env HUBSPOT_PROBE_TOKEN; flags --plan/--yes-spend-calls/--token-env/--dry-run; tag dpld_tag; status OPEN | yes |
| 67 | load_tools/README.md:71-99,125,105 seven checks, model bound 3, drain 120, max failed/unknown/review 0, exit 0/1/2, catcher port 2525, dupmix default 200/s, model-server modes + aliases | check_invariants.py:34-46,56,645 ("ALL 7 CHECKS HOLD"); live missing input rc=2; catcher.py:202; load_driver.py:69; fake_model_server.py:40-41 | yes |
| 68 | why-this-code.md:24 scrub tool "about 200 lines" | tools/scrub_n8n_export.py = 205 lines | yes |
| 69 | all docs: backticked names | scripted over 8 docs + load_tools/README: 424 test names/file paths -> 0 missing test names, 1 missing path (`playwright/driver/package/browsers.json` at tests.md:76, a path inside Playwright's own package, not this repo); 138 env/constant names -> only N8N_PORT (n8n's own variable) and PLAYWRIGHT_BROWSERS_PATH (Playwright's) are absent from this repo's code, both documented as external | yes |
| 70 | README/SECURITY/limits: route names `/ui`, `/api/ui/*`, `/review/{id}/retry|resolve`, `/leads/{id}/step`, `/fake/*` | live: /ui, /api/ui/leads, /api/ui/log, /review/X1/retry, /leads/{id}/step, /counts responded as listed; /fake/outbox seen by desk mail step (fakes server up) | yes |

## Commands run (all loopback, ports 18765/18766/18770, own dir)
* grep/sed/cat of docs and src; python -I scripts over config (Config.from_env, read_leadflow, _check_approvers, ProviderSettings, HubspotSettings).
* `python -m demo_only.fakes_server --outbox keyed --port 18766` and `python -m lead_desk.server` (DESK_DB_PATH under RR/tmp-C8) for the HTTP probe, exit-code runs (1,2,3,4,5), and shutdown by kill of my own pids.
* `python -m pytest --collect-only [-q|-qq] -p no:cacheprovider` (collection only; no test body run), plus on tests/test_except_clause_hierarchy.py.
* `python scripts/hubspot_probe.py --plan`; `python -m load_tools.check_invariants -h` and a missing-input run; `catcher.py -h`.
* Probe script: RR/tmp-C8/probe.py, lf.py. Raw: RR/tmp-C8/*.txt.
* Test files not run: all of tests/ (collection only). No ruff/mypy/bandit/gitleaks.

## Notes (no judging)
* One run of `python -I -m load_tools...` failed because `-I` ignores PYTHONPATH; I reran without -I (my error, not a repo fault).
* The exit-3 test used `ulimit -n 4000`; bash printed "cannot modify limit: Invalid argument" for the extra `-Hn` call, but the desk reported hard 4000 and exited 3.
* Processes left running by me: 0 (checked with ps). Scratch worktrees made: none.
