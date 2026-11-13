# Cold reader Q6: n8n recipe and limits (clean clone f3c39cf, Linux, Python 3.12.3, 2026-11-13)

Scope warning: n8n is NOT installed on this machine, there is no Docker daemon (`docker images` -> "failed to connect to the docker API"), and the brief forbids new downloads. So no workflow was imported into or run in a real n8n. I tested only: the recipe's commands (`scripts/n8n_api.py`), the workflow JSON files, and the desk and demo servers the workflows talk to. My own stand-in for n8n's REST interface (scratchpad `stub_n8n.py`, not n8n) was used once to exercise the helper. Desk ran on private ports 20651/20652. Time: part A about 1.5 min of commands (12:31:52-12:33:00 UTC; plus reading), part B about 2.5 min (12:33:00-12:35 UTC). IST = UTC+5:30. All my processes were stopped (reset.sh; stub exited).

## 1. Failures / mismatches
F1. `docs/n8n-recipe.md` line 27 and 11: the recipe tells the freelancer to start n8n on port 5679 and says workflows use "host and port from docs/settings.md" (line 24, 44). In reality `n8n/desk-form.json`, `desk-webhook.json` and `proof.json` have 8765 / 8766 / 5679 written into the URLs (`http://127.0.0.1:8765/leads`, `.../8766/fake/crm`, `http://127.0.0.1:5679/webhook/desk-form`). Anyone who runs the desk on another port (as the shared machine forced me to: 20651) cannot use the files unchanged, but line 8 (Licence) forbids editing them. The recipe never says this clash exists or what to do.
F2. Recipe line 13 says the file's `"active"` flag is ignored by import and you must switch the workflow on. All three files contain `"active": true`. Against my stand-in, `import` sent only connections, name, nodes, settings (flag dropped) and the workflow stayed `inactive`: matches, but a reader seeing `true` in the file will be confused.
F3. Not runnable: recipe steps 1-7 of section 1 (import through the n8n screen, form call via `/webhook/desk-form`, retry behaviour, proof workflow). No n8n, so "checked" lines in the recipe are unverifiable here. `curl http://127.0.0.1:5679/webhook/desk-form` -> connection refused (000), as expected.
F4. limits.md line 120 (exit code 1): "the sender cannot be reached". Real behaviour: `python -m lead_desk.server` with no demo servers running exits 1 with "cannot reach the demo servers (are they running? see scripts/start_all)". The doc word "sender" does not match the message (nothing in the docs calls the demo server "the sender"; in the README "sender" means the caller posting leads).
F5. limits.md line 91 says for one lead sent many times "the lead count and the follow-up count should each be 1". True only on a fresh desk; on the desk I had already used, `/counts` showed new 2 after the burst. Not stated that the desk must be fresh (reset script).
Everything else in the claims table matched.

## 2. Unclear steps (had to guess)
* Recipe line 11: "needs an n8n API key in a file you name, see the top of that script": the recipe does not say how to make the key in n8n, nor that the variable is `N8N_API_KEY_FILE` (only the script docstring and settings.md say it); I had to open the script. A bare `python scripts/n8n_api.py list` without it prints "N8N_API_KEY_FILE must be the path of a one-line file..." (OK, clear).
* Recipe line 6 vs 54: whether "Retry On Fail" is a setting of the node you must tick: it is already in the JSON (retryOnFail true, maxTries 3, wait 1000). Fine, but the recipe never says so up front.
* Section 3 tells the reader to "remove the old copy" by hand in the screen, but the screen route is "not tried" and the menu names are "not compared"; I could not tell which button to press.
* Recipe uses `python scripts/n8n_api.py` but never says to activate the `.venv` or set `PYTHONPATH`; it worked without PYTHONPATH (only stdlib). OK, but "from the repository root" is only in the script docstring.
* The example inputs (`sub-0001`, `Ada@example.com`) are the same person as `scripts/feed.py`'s canned lead; after the README demo the recipe's form call returns `duplicate`, not `new` (I got `duplicate`, receipt 4). The recipe does not say to reset first. Step 2 of "What was checked" (verdict `new`) therefore only holds on a fresh desk.
* `import` of a second copy: confirmed adds a duplicate, and `activate` then refuses ("2 workflows named '...'", rc 1). `list` reads only the first 250 workflows (`?limit=250`); not mentioned.

## 3. Steps needing knowledge, tool or file the document does not give
* How to install and start n8n (Node version, `npx n8n`, `N8N_PORT=5679` is given but not the command), how to create the owner account and the API key, the licence question. versions.md gives only "2.46.6 / Node 24.22.2". Machine has Node 22 only, so even the named Node would be missing.
* How to delete a workflow (no delete command in the helper; only "use the screen").
* How to hand the sender's "stable request id" to the form (recipe example JSON uses `submission_id`; fine).
* n8n in Docker: only a warning about `localhost`; no command.

## 4. Wording a non-technical reader would not follow (quotes)
* "n8n creates its own web-address id for each webhook node" (recipe l.11).
* "regular mode (no queue), one process, SQLite inside n8n" (l.19).
* "the placeholder node ids (`node-1`, `node-2`, ...) are accepted on import".
* "Retry On Fail ... 'Never Error'" and "the desk counts each rejected call 3 times" (l.54).
* "limited to one request at a time", "Remove Duplicates node", "Data Table upsert", "equal created and updated times" (l.58-63).
* limits.md: "the reaper", "claimed", "stall", "keyed/blind" (defined only in README), "abandoned, not stopped", "the stamp", "triggers", "`INSERT OR REPLACE`", "CHECK on receipts", "ModelAnswerLost", "backpressure".
* limits.md item 1 of the short list ("one process") and "hung_workers" without a definition at first use.
* limits.md l.120 "the sender cannot be reached" (see F4).

## 5. Time per part
Part A: about 1 min 8 s of recorded commands (12:31:52-12:33:00 UTC = 18:01:52-18:03:00 IST), venv + hash-locked dev install (pip install --require-hashes -r requirements-dev.txt, rc 0, pytest 9.2.0) done before that inside the clone step. Part B: 12:33:00-12:35 UTC (18:03-18:05 IST). Whole job well under the 50 min box.

## 6. Part A step log (recipe, literal)
| # | Quoted text | Command | Result | Worked? |
|---|---|---|---|---|
| 0 | "Start the demo servers and the desk first (README, 'Try it')" | `python3.12 -m venv .venv; pip install --require-hashes -r requirements-dev.txt` then `DESK_PORT=20651 DESK_FAKES_PORT=20652 bash scripts/start_all.sh keyed`, `feed.py` x3, `/counts`, `/fake/outbox` | "started: ... pid 9715, desk pid 9716"; 201 new; 201 replayed true; 200 duplicate; received 2, new 1, duplicate 1; outbox count 1 | yes (README as written; private ports chosen via DESK_PORT/DESK_FAKES_PORT from settings.md) |
| 1 | "start n8n with N8N_PORT=5679" | none available | n8n not installed, no docker | cannot run |
| 2 | "`scripts/n8n_api.py import <file>` ... needs an n8n API key in a file you name" | `python scripts/n8n_api.py list` (no key var) | "N8N_API_KEY_FILE must be the path of a one-line file with the n8n API key" rc 1 | yes (message clear) |
| 3 | same, FAKE key file built from parts, default URL | `list` / `import n8n/desk-form.json` / `activate "Lead Desk: Web Form Intake"` | "cannot reach n8n (URLError: ConnectionRefusedError)" rc 1 | as expected (no n8n) |
| 4 | N8N_URL rules (settings.md) | `N8N_URL=http://example.com:5679 ... list` | refused: "must be an https address, or http to this computer" rc 1 | matches |
| 5 | usage; bad key file `a b`; `delete` | no args; key with space; `delete x` | usage rc 2; "key file must hold one word..." rc 1; `delete` -> usage rc 2 | matches (no delete command, as recipe says) |
| 6 | import / activate against MY stand-in on 20653 | `import desk-form.json; activate NAME; import proof.json x2; activate proof; list` | "... 200", "activate 200"; second proof import 200; activate -> "2 workflows named '...'" rc 1; list shows all inactive except none activated | matches recipe l.13, l.70 |
| 7 | "Webhook path desk-form ... posts source, source_ref and payload to the desk's /leads" | POSTed the mapped bodies directly to desk `/leads` | form example: 200 duplicate (same person as canned lead; see unclear); email example: 200 duplicate | partly (verdict depends on fresh desk) |
| 8 | "A request with no email shows 202 review" | payload without email | 202 `{"verdict":"review","reason":"incomplete:email"}` | yes |
| 9 | "a body that is not valid JSON, or one over the size cap shows red (400, 413)" | `{bad`; 2 MB body | 400 bad_envelope; 413 too_large | yes (desk side) |
| 10 | "403 forbidden_host to any Host name it does not know" | `-H 'Host: desk.internal'`; localhost; [::1] | 403 `{"error":"forbidden_host"}`; 200; 200 | yes |
| 11 | "`/counts?expected=1`" (proof workflow) | curl | has `expected_match` false, ok false (desk had 5 receipts) | works |
| 12 | "`/fake/crm`, `/fake/outbox`" | curl | crm count 1 row; outbox count 1 | yes |
| 13 | JSON facts: Retry 3 tries / 1000 ms; timeout 15 s "well above 5 s"; responseMode lastNode | read the files | retryOnFail true, maxTries 3, wait 1000; timeout 15000; lastNode | yes |
| 14 | n8n steps 1-7 of "What was checked", proof workflow, `/webhook/proof-run` | n/a | needs n8n | cannot run |
| 15 | "`demo_only/burst.py` fires the same burst without n8n" | `python -m demo_only.burst --url .../leads --n 100 --email ada2@example.com --ref-prefix run1 --source form` | SENT n=100; STATUS 201=1 200=99; RETRIES busy503=0 refused=0; RESULT sent=100 expected=100 | yes |

## 7. Part B claims table (docs/limits.md)
| Claim (line) | What I ran | What happened | Matches? |
|---|---|---|---|
| l.9-ff "Python 3.12 ... Linux lock file ... 2462 passed" (l.71) | not run (full suite ~20 min) | - | cannot run here: time |
| l.31-39 call budget 9 s, `min(send_timeout,9)`, tests named | read constants; ran all 30 cited test names (39 tests) | `MODEL_CALL_BUDGET_SECONDS 9.0`, `CALL_DEADLINE_MAX_SECONDS 9.0`, send_timeout default 5.0; "39 passed, 3844 deselected in 24.08s" | yes |
| l.40 caps 4 AI / 8 CRM / 8 sends / 4 reads | printed `ADAPTER_WORKER_CAPS` | (("model",4),("crm",8),("send",8),("refresh",4)) | yes |
| l.42 `stall_seconds` | Config | stall 120 (default not in limits.md; not checked against settings table) | yes (name exists) |
| l.54 grace 30 s (send timeout + 5 waits of 5 s) | read `stuck_grace_seconds` | docstring/formula: 5 + 5*5 = 30 | yes |
| l.55-56 "24 s strictly below the smallest grace 25 s" | not computed end to end | formula consistent; load-time guard not triggered | partly checked |
| l.58 :memory: refused, exit 4, before folder made | `DESK_DB_PATH=:memory:` | "the lead book must be a file: ':memory:' ..." rc 4 | yes |
| l.58 AI adapter `timeout_seconds` >9 or <=0 gives exit 4 | not run | needs a custom adapter | cannot run: no documented way |
| l.58 constant out of range -> Python error exit 1 at load | not run | needs editing constants | cannot run (no edits allowed) |
| l.68 ten crash points, real kill only at D2 | not run | needs crash_desk scene | cannot run in time |
| l.76 stuck >30 s put back by reaper, one pass every second | not run | clock tests | cannot run quickly |
| l.80 REAPER_PASS_SECONDS 10 s; "10 + 27 + 18 = 55 s" | read constant | `REAPER_PASS_SECONDS 10.0` | yes (arithmetic not re-derived) |
| l.85 `/counts` fields incl. `rejected_envelopes`, `decide_transient_errors`, `decide_integrity_errors`, `failed_followups`, `hung_workers` | curl `/counts` | all present; `received = new + duplicate + review + open`: 105 = 2+102+1+0 | yes |
| l.85 refused requests counted in `rejected_envelopes` | bad JSON + 2 MB | 0 -> 2 | yes |
| l.91 burst command and output lines | ran it | SENT/STATUS/RETRIES/RESULT, no lead count, 201=1 200=99 | yes |
| l.91 "lead count and follow-up count should each be 1" | counts after burst | new 2 on a used desk | no on a used desk (F5) |
| l.92 `LEAD_DESK_LOAD_N=300 pytest ... measure_burst` | not run | would add load on a shared 4-core machine | cannot run here: shared machine |
| l.92 `LISTEN_QUEUE` 1024 | constant | 1024 | yes |
| l.94 burst backoff 0.1 s, doubling to 1 s, 30 s deadline; constants names | printed constants | 0.1 / 1.0 / 30.0 | yes |
| l.97 body shorter than Content-Length: 408 at 10 s if kept open | raw socket | 408 after 10.0 s `{"error":"request_timeout","receipt_id":null}` | yes |
| l.97 ... or 400 if the sender closes | raw socket, closed after 1 s | 400 bad_envelope after 1.0 s | yes |
| l.97 both counted in `rejected_envelopes`; header stall 408 not counted | counter before/after | +5 for the five body cases; header stall (idle) not counted | yes |
| l.97 Content-Length over cap, "however long the number": 413 at once | 5000-digit and 30-digit CL | 413 too_large in 0.0 s | yes |
| l.97 two different Content-Length: 400 | raw | 400 bad_envelope | yes |
| l.97 unparseable request target: 400 | `POST http://[bad/leads` | 400 `{"error":"bad_request"}` | yes |
| l.97 413 also for `/review/<id>/resolve` after Host/Origin check | not run | needs a review id | cannot run in time |
| l.96 demo HubSpot stand-in Content-Length 400 | not run | covered by cited tests? (`tests/test_codeant_fakes.py` file exists) | not separately run |
| l.104 portal `/api/ui` max 8 at once, then 503 `busy` | `/ui/` 200; `/api/ui/leads` answers | 8-at-once not tried | partly |
| l.114-115 masking; `/api/ui/leads?by_email=1` still returns names/emails | curl | rows with name and email in clear | yes |
| l.117 reply write timeout 5 s | constant | 5.0 | yes (behaviour not run) |
| l.118 open files: 4 per thread + 96 = 4192 with 1024 threads | printed `FDS_PER_HANDLER_THREAD 4`, `FD_RESERVE 96`, `MAX_HANDLER_THREADS 1024`; ran desk with hard limit 4096 | arithmetic 4192; "needs about 4192 open files (4 per thread plus 96), but the limit ... is 4096 (hard 4096)" rc 3 | yes (note: bash printed "ulimit: cannot modify limit: Invalid argument" for my setup, not the desk) |
| l.120 exit 2 another desk holds lock | second desk, same db | "another desk is using this database" rc 2 | yes |
| l.120 exit 3 | above | rc 3 | yes |
| l.120 exit 4 not-a-number / out of range / any other bad DESK_ value | `DESK_PORT=abc`, `70000`, `DESK_OUTBOX=zzz` | "DESK_PORT is not a number" / "must be between 0 and 65535" / "must be one of http, smtp, smtp_provider", all rc 4, name in message | yes |
| l.120 exit 5 port not bound within `BIND_RETRY_SECONDS` | port already used | "cannot bind 127.0.0.1:20651: OSError" rc 5 after 5 s | yes |
| l.120 exit 1 "the sender cannot be reached" | start desk with no demo servers | "cannot reach the demo servers ..." rc 1 | wording differs (F4) |
| l.121 Ctrl+C/SIGTERM stop; second signal ignored; ~10 s | not run | needs signal timing | cannot run in time |
| l.122 256 / 1024 limits | constants | 256 / 1024 | yes (503 behaviour not run) |
| l.123-124 idle connection: 408 at the 10 s header deadline, body `{"error":"request_timeout","receipt_id":null}` | raw socket idle; headers stalled | both 408 at 10.0 s, exact body | yes |
| l.125 eviction after `EVICT_MIN_IDLE_SECONDS` 2 s | constant | 2.0 | yes (behaviour not run) |
| l.127 "single digit 0 bind is a wildcard" | not run | - | cannot run in time |
| l.133 `exceptions.txt`, scan `tools/hygiene.py` | files exist | `tools/hygiene.py` named in README exists | not run |
| l.137 CRM retry waits 10/60/180/420 s | not run | ~11 min | cannot run here: time |
| l.147-153 `hs_lead_status` values `NEW, ATTEMPTED_TO_CONTACT, CONNECTED, OPEN_DEAL` | grep in demo_only/leadflow.json (not in src) | names appear only outside `src`; /fake/crm showed `ATTEMPTED_TO_CONTACT` | yes |
| File and test names cited (30 tests, 6 files, `_bounded`, `_restamp_future`, all `DESK_*` names) | script search | all exist, none missing | yes |
| Short version item 7/9 (real services, Windows measurements) | - | not checkable | cannot run here: needs real services/Windows |
