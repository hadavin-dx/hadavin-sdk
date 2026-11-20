# Goldfish Annotated Review Report: ticket D, round 1 of 1

**Target:** `handover/core-a/tickets/D-signed-endpoint.md` (full file, 343 lines at review time)
Written 05:38 UTC / 11:08 IST. Started through the Skill tool: egm:egm-review-loop (direct dispatch), then egm:egm-resolve. No round 2 (ORDER 004 item 3).

**What is weak about this review (first):** the findings below are my condensed copy of the two reviewer reports (one line each, the reviewers' line numbers kept); the full reviewer texts exist only in the session transcript, not in a file. The decision gate of egm-resolve asks a person to choose; nobody was present, so "auto accept" was applied on the lead's standing order. The reviewers reviewed the TICKET; neither reviewed the code already built (they say so). Both reviewers ran nothing.

| reviewer | agent | model | status | tokens | result |
|---|---|---|---|---|---|
| IR | egm:egm-implementation-readiness (standard: implementation-readiness-standard) | fable | completed | 130,670 | 2 Blocker, 13 Major, 8 Nit; verdict "not ready to build as written" |
| CB | egm:egm-codebase-details (no standard) | fable | completed | 200,403 | 1 Blocker, 7 Major, 10 Nit; "most file:line citations I opened are correct" |

Round result: NOT CLEAN (3 Blocker, 20 Major). Counts after resolve: PROPOSE FIX 33, ESCALATE 4, DECLINE 4, CONTEST 0.

## Findings and resolution
Category: FIX = valid, ticket text is repaired (and code, where code is named); ESC = needs the lead (in ESCALATIONS.md); DECL = nit recorded, not fixed.

| id | sev | ticket lines | finding (condensed) | cat | what is done |
|---|---|---|---|---|---|
| IR-B1 = CB-M3 | Blocker / Major | 165, 257, 259 | Runner.start as written gives 503 to parallel same-key requests when no slot is free (always with max_running 1): cases C1 and C3 cannot pass | FIX | Code: no-slot path polls the stored run row until the ack wait ends (DECISIONS row; worker builder resumed). Ticket line 165 rewritten; C1 and C3 state their max_running |
| IR-B2 = CB-B1 | Blocker | 9, 120, 157-164, 217-219, 263-265, 278 | Crash-test interface of the ticket (RaisingCrash, FlagFileCrash, main(crash=), points verified/submitted/row_seen, dotted names) does not exist in the built helper; K2 and K3 cannot be written | FIX | Sections 6, 7, 9, 10 rewritten to hadavin_sdk.testing.crash.CrashPoints with wrap points (store.create_run:before/after, store.touch:before, store.get_run:after with nth); the launcher wraps app.store then calls make_app, not main; crash parameters dropped |
| IR-M1 | Major | 9, 120, 216-222 | Sections 6, 9, 10 contradict the reconciliation note | FIX | Sections rewritten; note removed |
| IR-M2 = CB-M4 | Major | 119, 136-165, 215, 301 | File list and signatures do not match what is on disk (make_wsgi(settings, secrets, start, clock), Protocols not a Sender dataclass, Runner arguments, check_secrets, check_senders, read_secrets, check_bind, make_server, --config-dir, test file names); skeleton test_t5_cases.py not mentioned and disagrees with the ticket | FIX | Section 6 and 7 rewritten from the built modules; test-file map added; skeleton aligned by its writer (see ESCALATIONS E3 if it cannot be) |
| IR-M3 | Major | 4, 215, 342 | No phases; "REQUEST 001 merged first" conflicts with "code against a stand-in" | FIX | Phase list added: 1 endpoint, 2 Runner, 3 make_app and main (blocked on core-b R1, R1b, R1c, R1d), 4 PostgreSQL and crash cases, 5 n8n files; each with its tests and what is blocked |
| IR-M4 | Major | 335-339 | Open questions that change code are undecided: audit event on a signed 409 (Q4), exit 4 after 3 store errors (Q5), warn or refuse on two secret names (Q8) | ESC | E1: lead decides Q4 and Q5; until then NOT built (409 writes nothing; no exit after store errors). Q8 fixed in text: warn |
| IR-M5 = CB-M2 | Major | 172-174, 183, 233, 240 | First answer is 202 or 200 by thread timing; N6 and E6 assert a fixed 200; rule for middle states unclear | FIX | One rule: 202 while state is RECEIVED or WORKING, else 200; tests accept 202 or 200 first and assert 200 only on a repeat after the run settled (worker already does this) |
| IR-M6 | Major | 94, 103, 163, 243 | Short or timed-out body read undefined; wsgiref's own error path may send a 500 with text and a traceback | FIX + ESC | Text: a read that raises or returns fewer bytes gives 400 with an empty body (endpoint does this; in-process test only). E2: behaviour of wsgiref on a real socket timeout is NOT RUN; needs one real-socket test |
| IR-M7 | Major | 144, 167, 177, 249 | parse_body edges: RecursionError on deep nesting, lone surrogate, duplicate document member, NaN, BOM; BadRequest undefined | FIX | Rules written from endpoint.py (RecursionError caught, duplicate member 400, BadRequest(ValueError) in endpoint.py); lone surrogate, NaN and BOM added as test cases to check in the batch |
| IR-M8 | Major | 159-165, 182 | Pool type, slot release, daemon threads, close semantics, clean stop of main unspecified; no close test | FIX | Text from worker.py (ThreadPoolExecutor, slot released in the done callback, close(wait_s) cancels work not begun and waits, closed Runner answers 503); open risk stated: a loop still running after wait_s keeps the process alive |
| IR-M9 | Major | 95, 101, 108, 160, 253 | Where start-up checks live; what loopback means; how H8 gets a pilot App | FIX | Checks named: check_secrets (in make_wsgi), check_senders, check_bind (ipaddress is_loopback plus localhost), raising ValueError or ConfigError; main turns them into exit 2; H8 calls the pure functions |
| IR-M10 | Major | 103, 254, 298, 322 | Log contract (logger name, levels, format, reason codes) not fixed | FIX | Logger hadavin_sdk.triggers, one INFO line with status and sender id, WARNING with the exception class name; no reason codes exist in the code: stated, README lists statuses only |
| IR-M11 | Major | 118, 327-328 | n8n files are an outline: node types, sign node choice, where the secret lives, export format undecided; no acceptance check | ESC | E4: cannot be decided without a real n8n (none in this box). Acceptance checks added that CAN run here: JSON parses, no secret-shaped literal, error workflow starts with an Error Trigger |
| IR-M12 | Major | 342 | Done criterion unmeetable: invariants 2 (no early stop), 9, 12, 13, 14, 16 have no test | FIX | Invariant-to-test table added; 9 marked "statement, not testable"; 16 marked core-b's; missing tests listed as TO WRITE (verify call-count spy, exception after the row, resolver refuses other names, close) |
| IR-M13 | Major | 226, 258-264 | PostgreSQL and two-process fixtures not described; agent and principal not named | FIX | Agent test-agent and principal svc:test-agent named; C4 (two processes) marked NOT BUILT here, lead's laptop campaign |
| CB-M1 | Major | 263 | run_tick(steps=[stuck]) is wrong: steps are TickStep objects | FIX | steps=[TickStep("stuck", 0, stuck)] (the built worker test must be checked for this in the batch) |
| CB-M5 | Major | 68, 91, 186 | config_hash description is wrong: the hashed dict is registry.py:132-173 and includes two Config-level fields | FIX | Sentence replaced: "only fields listed in that dict are hashed; Config.triggers is not listed" |
| CB-M6 | Major | 69, 199 | Body cap 2 x MAX_DOCUMENT_BYTES is no guarantee: JSON escaping can triple or six-fold a document | FIX | Limit stated honestly (a document near the cap with many escaped characters gets 413); edge test added; core-b told in request 001 draft 3 |
| CB-M7 | Major | 24, 27, 64, 78, 113 | "No caller of handle, no n8n file, only mutation.py" are false against the working tree | FIX | "as of main 51c9fc4fb, before this step's files" added |
| IR-N1 = CB-N5 | Nit | 138-139, 167 | KEY_RE and ID_RE: say fullmatch | FIX | Text says fullmatch; a trailing-newline hostile case is in the test list (check in batch that endpoint.py uses fullmatch) |
| IR-N2 = CB-N1 | Nit | 163 | Exit codes: _tick uses 2 for other start-up errors; StoreUnavailable subclasses ConfigError and must be caught first | FIX | Text corrected (0, 2, 4, 3 as worker.py does; StoreUnavailable first) |
| IR-N3 | Nit | 165 | get_run raises NotFound, not None; name what "store unreachable" is | FIX | Text corrected |
| IR-N4 | Nit | 142, 150 | Say how headers come from the WSGI environ and that secrets is keyed by sender id | FIX | One line added |
| IR-N5 | Nit | 163, 243 | Socket timeout ack_wait_s + 10 makes a test slow | DECL | recorded |
| IR-N6 | Nit | 180, 255 | Does 405 carry an Allow header | FIX | Yes (endpoint sends Allow: POST); H10 wording changed to "no header that names the refusal reason" |
| IR-N7 | Nit | 95 | 32 characters or bytes; where the constant lives | FIX | Characters; MIN_SECRET_CHARS in endpoint.py until core-b's defaults exist |
| IR-N8 | Nit | 130 | Three tree-walking guard tests left UNVERIFIED | FIX | To run in the batch (test_lockin_guard, test_client_profile, test_k5_round11) |
| CB-N2 | Nit | 113, 118 | pyproject line numbers off | FIX | corrected (56-58, 81-82) |
| CB-N3 | Nit | 286 | bandit is in the scan group; subprocess launcher needs the repo's noqa S603 form | FIX | corrected |
| CB-N4 | Nit | 58, 87, 318, 335 | "received" event hashes the hex string of the document, never equal to the sha256 in trigger_ref | FIX | sentence added |
| CB-N6 | Nit | 116 | "does not import the store" holds for direct imports only | FIX | limit stated |
| CB-N7 | Nit | 66, 124 | R1c also needs a change in platform_secrets.check itself | FIX | request 001 draft 3 |
| CB-N8 | Nit | 107, 125 | Closer pattern for a name-limited reader is _own_secrets (app.py:304-313) | FIX | request 001 draft 3 |
| CB-N9 | Nit | 205 | A duplicate sender id joined to the "refused" list would read as a stage refusal | FIX | request 001 draft 3: own ValueError |
| CB-N10 | Nit | 313 | openai_compat.py:88-89 holds no client object | DECL | sentence removed with the fix of 11b |
| CB remark | - | 163 | worker copies the qualification loop of cli.py:289-298 | ESC | E3: a shared helper would be a change in core-b's file; lead decides |
| CB remark | - | H4 | RecursionError relies on a catch the contract did not mention | FIX | covered by IR-M7 |
| IR "defaults twice" (in CB-M4) | - | 206 | Default numbers are literals in endpoint.py and worker.py and will exist twice once core-b adds TRIGGER_* | DECL | recorded as a follow-up for the PR after core-b lands (replace literals by defaults.TRIGGER_*) |
| IR-M2 part | - | 215 | No file named for the stand-in settings object | DECL | it lives inside the test files; stated in section 6 |

## Open after this round
See ../ESCALATIONS.md entries E1 to E4. No second round is started (lead order).
