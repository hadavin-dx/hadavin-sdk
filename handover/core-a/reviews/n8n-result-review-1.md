# Goldfish Annotated Review Report: RESULT review of the n8n pack (README-trigger.md, hadavin-trigger.json, hadavin-trigger-error.json), round 1 of 3. Status: resolved; fixes pending. 07:10 UTC / 12:40 IST

Reviewers (fresh, not the author, model sonnet on the call; transcripts show claude-sonnet-5-5): egm:egm-comprehension (NC: the naive reader, 83k tokens) and egm:egm-design (ND: hostile design, 144k tokens). Evidence that only records: raw/n8n-template-tests-4.log (193 passed, STATIC checks of JSON shape and README words) and the lead's run of an EARLIER version in a real n8n 2.47.7 (inputs/lead-evidence-n8n-1.md). Resolve through the egm-resolve skill; no human present for the gate, auto accept.
**Weak points (first):** nobody ran any of this pack in an n8n; reviewers ran nothing; several findings are SUSPECT n8n behaviour that only a real n8n can settle (ND-3, ND-4); the naive reader said it could not decide who the audience of the set-up steps is (a client, or the operator?).
**Result: 1 Blocker (NC-1), 14 Major, 10 Nit. NOT clean.** The earlier lead Majors A and B are closed on paper (verified by ND in the files).

| id | sev | finding | category | what the builder does |
|---|---|---|---|---|
| NC-1 | Blocker | the README never says where the Hadavin side comes from (endpoint URL; who creates the secret and where; the sender is found by trying secrets: no sender id in the request; secret form: at least 32 random characters, no trailing newline; the triggers config block is not on this branch yet) | PROPOSE FIX | a section 'Before you start: what you need from the Hadavin operator' (URL through a reverse proxy with TLS, the secret value and how to generate it (a command line example that avoids a trailing newline), confirmation that the sender is configured, the stated fact that the endpoint's configuration block is not merged yet) |
| NC-2 | Major | the caller's payload shape is never stated | PROPOSE FIX | one curl example against the webhook URL with the body {record_id, text} (placeholder values) and the expected 202 answer |
| NC-3 + ND-7 + ND-minor key | Major | the template hashes only record_id; README says 'record id plus event name'; two events on one record share a key; a re-send needs a NEW key the template cannot make; the id is not trimmed; large numeric ids lose precision | PROPOSE FIX | the hashed value becomes recordId, a colon, eventName, and an optional colon plus a 'rerun' field (new optional caller fields event and rerun; the guard requires record_id and text and, if event is present, a non-empty event); trim the id; require a string id or Number.isSafeInteger; README explains how an operator re-runs (a rerun value) and that a Message-ID must be normalised the same way every time |
| NC-4 | Major | the 'made-up event' of step 10 starts a REAL run | PROPOSE FIX | warning: use a test sender or test agent; add 'send one event with an empty text to see the notice reach you' as the failure test |
| NC-5 + ND-1 | Major | a duplicate reaches 'Done'; the follow-up runs twice; Done also covers NO_ACTION and WAITING_FOR_APPROVAL | PROPOSE FIX | README step 8: follow-up steps must tolerate running twice for one key; 'Done' does not mean the action happened |
| NC-6 | Major | the error message holds no key or event | PROPOSE FIX | README: the person opens the execution to find the event; optionally add a non-secret event reference (the record id, not the text) to the error message |
| NC-7 | Major | publish steps need an id; restart; editor toggle | PROPOSE FIX | name 'n8n list:workflow', the restart requirement, the editor Publish toggle (UNVERIFIED) |
| NC-8 | Major | credential order fragile | PROPOSE FIX | one numbered sentence: create the credential, write its id and name into the Sign node, import, check the node shows the credential |
| NC-9 + ND-2 | Major | 30 busy rounds x 60 s (about 32 min) is shorter than the README's own example stuck limit (37 min); numbers hide inside expressions; 31 sends not 30; Retry-After ignored; the test only asserts above 300 s | PROPOSE FIX | busy rounds placeholder 45; README names the two expressions and says where to find max_steps; the numbers are a floor; a test ties busy span x wait to the stuck-limit formula plus a tick gap; Retry-After stated as ignored |
| NC-10 | Major | some 'SEEN IN n8n 2.47.7' notes are not backed by the evidence (changed expressions); '26 of 26' is 26 of 27; earlier signing was not Crypto v2 | PROPOSE FIX | correct the notes and the count; mark changed expressions unverified |
| ND-3 | Major (suspect) | the 202 to the caller is sent before anything is durable; loops live in n8n memory up to about 77 minutes; an n8n restart loses the event and the caller will not retry; 'wait at or under 60 s' points the wrong way for durability | PROPOSE FIX (text) + ESCALATE (verification) | README stated limit about n8n restarts and waits; the lead's next n8n evidence step must test a wait above 65 s and an n8n restart during a wait (ESCALATIONS E6) |
| ND-4 | Major (suspect) | (a) 'Answer caller: taken' relies on canvas order beside Hash; (b) 'refused' Respond then Stop: if Respond returns no items Stop does not run and a refused event ends as SUCCESS | PROPOSE FIX + ESCALATE | (a) chain in series: guard true, Answer taken, Hash; (b) remove the 'Answer caller: refused' node so the Stop node always fails (the caller then sees n8n's own error answer: stated, unverified); the lead's evidence step verifies a Respond-then-Stop shape (E6) |
| ND-5 | Major | the webhook has no authentication: anyone who can reach it starts runs, pre-claims keys, floods the error workflow | PROPOSE FIX | webhook authentication (header auth with a credential placeholder: UNVERIFIED shape) or an unguessable path as a REQUIRED set-up step; a test that the webhook node carries an authentication setting |
| ND-6 | Major | WAITING_FOR_APPROVAL ends as success but the tick can turn it into NEEDS_PERSON approval_missing | PROPOSE FIX (text) | stated limit |
| ND-8 | Nit | busy statuses: 500 and 520 to 524 stop at once; the stop message is wrong in the check phase; the shared round counter is spent by the check phase | PROPOSE FIX (partly) | add 520 to 524 to busy (not 500: the worker never sends 500 itself); fix the stop message; state the shared counter |
| NC-11 | Nit | undefined labels | PROPOSE FIX | short glossary at the top |
| NC-12 | Nit | secret quoting in the import file; N8N_ENCRYPTION_KEY; HTTP timeout must exceed ack_wait_s (up to 30 s); 500 and 3xx not named; item 17 is policy | PROPOSE FIX | one line each |
| ND-9, ND-10 | Nit | n8n keeps the document in its execution store (retention); manual retry, error workflow coverage on an n8n crash, Respond and Crypto v2 pass-through unverified | PROPOSE FIX (text) | state, mark unverified |
| ND-11 | Nit | the 193 tests are static checks | DECLINE | stated in the README and in the report: they prove shape and wording, not behaviour in n8n |

Counts: PROPOSE FIX: the Blocker and all Majors (some with ESCALATE for the verification), 7 Nits; DECLINE 1; CONTEST 0; ESCALATE 1 (needs a real n8n: ESCALATIONS E6).
## What happens next
A sonnet BUILDER (not the author, not a reviewer) edits n8n/*.json, n8n/README-trigger.md and tests/triggers/test_n8n_template.py; a separate evidence runner records; round 2 by fresh reviewers (not these two). Audience decision for the README: the set-up steps are for the Hadavin OPERATOR together with the client's automation builder (state it at the top).

## Round 2 (builder, core-a)

| # | Finding | Done |
|---|---|---|
| 1 | Header Auth import recipe, credential id location | README: recipe added, marked UNVERIFIED (field names `name`/`value` in no evidence file) |
| 2 | How a person finds the stored run | No lookup command exists in cli.py; README and the Stop messages say "ask the Hadavin operator with the run id"; key text = `key` field of "Hash business id" in the failed execution (the Stop message holds only the run id) |
| 3 | Notify note began SEEN | Now starts UNVERIFIED; test ERROR set pins "Notify placeholder" |
| 4 | Non-existent README passage | Sentence deleted |
| 5 | 26 of 27 wording | Fixed |
| 6 | Build request / Stamp time notes | Start UNVERIFIED (input path); both added to OPEN_NODES |
| 7 | "below" -> "above" | Done |
| 8 | `{{ $json.message }}` in step 5 | Done |
| 9 | Words used here | tenant, agent, principal, ack_wait_s, max_running, max_steps, registry added |
| 10 | Wait advice conflict | Now "keep 60 s; do not restart n8n while events are in flight" |
| 11 | Test docstring | Added 520-524 and state check |

## Round 3 (builder, core-a; text only, no loop numbers changed)

| # | Nit | Done |
|---|---|---|
| 1 | 400 row Content-Length "missing or wrong" | README: missing, zero or longer than the bytes sent; shorter gives a cut body and a 401 |
| 2 | falsy rerun ignored | README says "non-empty rerun value" (0, empty text, false ignored); expression unchanged; Hash note and test pin updated |
| 3 | lone surrogate gets 400 "document is not valid text" | README 400 row and Build-guard note: a STOP |
| 4 | "about 45 minutes" for no answer | README: 45 minutes plus up to 45 s per send (about 79 minutes when each send times out) |
| 5 | "changed twice" / "round 1 changed only notes" | trigger json, error json, README line 3: "after review rounds 1 and 2 (round 3 text only)" |
| 6 | Number.isFinite detail in guard note | Dropped; marked "recalled, not in the evidence" |
| 8 | 414 and 431 origin | README: from the stdlib HTTP server layer in server.py |
| 7 | (not in this list) | n/a |

Checks: both JSON files load; ruff check and format clean; pytest log handover/core-a/raw/n8n-template-tests-7.log. Not run: n8n.

## n8n-fix4 (builder, core-a; evidence `handover/core-a/inputs/evidence-n8n-3.md`, real n8n 2.47.7, each case ran once)

Facts checked against the evidence text before use: (1) restart in a wait: 60 s, restart at about second 20, execution crashed and never resumed, lines 51 to 63; 120 s, restart at about second 30, saved as waiting, survived, success about 2 s after the planned end, lines 65 to 78. (2) Respond then Stop and Error: caller 200 with the Respond body, execution error, error workflow once 0.12 s after the start, lines 82 to 96. (3) Respond then Respond: caller got the first body only; with a Set node between, R2 received the Set item; no warning in the log, lines 98 to 118.

Choice (a): wait 70 s (kept the 45 rounds and 45 checks). Arithmetic from the code: stuck limit 12 x 60 x 3 + 60 = 2220 s, plus one tick gap 60 s = 2280 s. 45 x 70 = 3150 s > 2280 (about 52 minutes; busy rounds and checks both). Minimum checks: `max_steps` 6 (1200 s) more than 17, 12 (2280 s) more than 32, 20 (3720 s) more than 53 (were 20/38/62 at 60 s). No-answer worst case: 3150 s + 46 sends x 45 s = 5220 s, about 87 minutes (was 79); both loops together 6300 s, about 105 minutes (was about 90). 70 s is an inference above the 65 s threshold; only 60 s and 120 s were run.

| Change | Where |
|---|---|
| wait 70, numbers 52/87/105 minutes, 17/32/53, notes and error message of "Stop: still running" | trigger json, README (numbers, limit 15, set-up steps 10 and 12, verify 8 and 22), tests |
| behaviours 1 to 3 marked SEEN, each once, with line cites; UNVERIFIED kept for the node as written (noData, 202), early answer before a long chain, 70 s in a restart, lost execution notice, crash of n8n, longer stop timeout | JSON notes, README, tests |
| restart fact moved into the stated limits and the set-up checklist ("do not restart n8n while an event is in flight" is now a known fact with the 60 s and 120 s numbers) | README step 12, limit 15 |
| new tests: wait above 65 and every derived number, restart fact in limits and checklist, Respond then Stop and Error and the guard shape | `tests/triggers/test_n8n_template.py` |

Checks: both JSON files load; ruff check and format clean; pytest log `handover/core-a/raw/n8n-template-tests-9.log` (91 passed; three runs were needed because two of my new test phrases did not match the wording, no code changed between them). Not run: the real loop with 70 s waits.
