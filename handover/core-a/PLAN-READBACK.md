# PLAN-READBACK of core-a (session role DOOR), queue item T1, 2026-11-20

Read fully: inputs/plan-v2.md, plan-v3.md, plan-v4-final.md, review-plan-3-codebase.md, review-plan-3-zoom-out.md, TICKET-TEMPLATE.md, all of ORDERS.md, the two demo helper files. Short names below: v2, v3, v4, R-code (codebase review), R-zoom (zoom-out review), SRC = src/hadavin_sdk. Where files differ, v4 wins over v3 over v2 (v4 line 2), and ORDER 004 is the lead's newest word on top of all three.

## 1. MY STEPS
Order for this session: E, then D, then H-logic only if proven (ORDER 004 item 1). The plan table lists D before E and lands them as one group "D+E" (v4 B1 landing line).

**Step E: test helpers.** A crash-point hook (a named point in code where a test can make the process die, to prove nothing is lost or doubled) and a socket guard (a test fails if code opens a network connection).
- What: "Test helpers (crash-point hook, socket guard), test-only, no interface ticket" (v4 B1 row E). "test-only, not public API" (v2 s.3 item 9). The extras once in this item (P3a-2 migrate wiring, #83, #89) are tier 2 now (v3 A2 "Moved to tier 2").
- Inputs: "demo `hooks.py`, crash launcher (inputs folder)" (v4 B1 row E) = inputs/demo-hooks.py and inputs/demo-crash_launcher.py.
- Exit artifact: ticket tickets/E-<short-name>.md, no ticket review (v4 B1 row E "none"; ORDER 004 item 3); then code on branch wip/cloud-core-a/E cut from origin/main 51c9fc4fb, allowed as soon as the ticket is written (ORDER 004 item 5). Phase-2 exit: pushed SHAs, ruff clean, import smoke of every new module (v2 s.6 phase 2).
- Depends on: nothing. Its purpose is to prove the money step and the door step (v2 s.3 item 9 "prove items 2 and 7"; v3 A2 "helpers first so the PRs ... carry their own proving tests").

**Step D: thin signed endpoint + n8n template.** A small private web endpoint that a client's automation tool (n8n) calls with a signed request to start one agent run, at most once per request key.
- What (v4 B1 row D): `triggers/endpoint.py`, a WSGI callable (stdlib wsgiref in tests), verifies the signature by reusing approvals/hmac_v0; "two valid secrets during rotation is new behaviour and is tested"; derives `run_id` = `run-` + 32 hex from (tenant constant from config, sender, key in the signed body); "records the request and acks". `triggers/worker.py` (own `__main__`) calls `Runtime.handle`, "which already gives one run per run_id". Plus n8n workflow template, error workflow, T5 cases. The result goes back to the client tool "as the existing shadow card (no new return path)".
- T5 cases: signed, replayed, reordered, malformed, retry after six minutes, same key different payload (v2 s.3 item 8). Each replay case must say whether the sender re-signs: an original signature older than 300 s is refused before any lookup and that refusal is the expected result; a re-signed retry with the same key returns the stored run (v4 B4).
- Invariants named by the plan: `Runtime.handle` preconditions: agent in `runtime.agents`, principal in the registry, trigger_kind one of event/schedule/user, document as raw bytes (v4 B4). Headers and signing "exactly as approvals/hmac_v0 (two valid secrets during rotation, one secret per sender)" (v3 A5). Shape to copy: `handle_slack_action` (v2 s.3 item 7).
- Inputs: branches core/ak-g2-a and core/T1-T2-tests, "ideas and tests only" (v4 B1 row D); atlas n8n.md (v3 A5).
- Exit artifact: tickets/D-<short-name>.md with the template fields plus NEEDED-CHECK, numbered INVARIANTS, files, signatures, migration need, interfaces, tests, what stays out; ONE EGM review round saved as tickets/D-review-1.md; no round 2 (ORDER 004 item 3). No code before the lead writes "GO BUILD D" (ORDER 004 item 5).
- Depends on: core-b adding the config fields ("SPINE adds the config fields", v4 B1 row D); E for crash tests. No migration of its own. D is part of the smallest client-ready set A, B, C, D (v4 B1).
- Guarantee sentence that D earns (v4 B3): once-only START of a run per signed request key; a repeat returns the stored run; a crashed run ends with a person (NEEDS_PERSON), it is not re-run; n8n retry and re-signing behaviour is UNVERIFIED until T5 runs against a real n8n.

**Step H-logic: receipt ledger delta (conditional).**
- What (v4 B1 row H): "ONLY what `Runtime.handle` dedupe does not give, proven in the ticket by a failing case (same key with a different payload must answer conflict; a stored payload hash; requests kept beyond run retention)". A work-items table and a door role "only if step D's ticket shows the ack cannot wait for the stored request". "cut if no delta is proven".
- Split: core-b writes the store part and migration 0008; this session writes the logic in `triggers/` (v4 B1 row H owner column).
- Inputs: core/ak-g2-a. Exit: ticket H with the failing case, one review round. Depends on: the D ticket (it holds the proof), core-b's store methods of interface (i), migration 0008.

## 2. MY FILES (new files only)
| Step | Path | Source |
|---|---|---|
| E | src/hadavin_sdk/testing/<crash hook module>.py, <socket guard module>.py | folder `testing/` named in v3 A1; file names INFERRED |
| E | tests for the two helpers, in the new tests folder | INFERRED |
| D | src/hadavin_sdk/triggers/__init__.py | package named in v3 A1; file INFERRED |
| D | src/hadavin_sdk/triggers/endpoint.py | v3 A5, v4 B1 row D |
| D | src/hadavin_sdk/triggers/worker.py (own `__main__`) | v4 B1 row D |
| D | n8n workflow template + error workflow (JSON files) | named in v4 B1 row D; location INFERRED (not given anywhere) |
| D | T5 tests "under a new tests folder" | v3 A1; folder name INFERRED (e.g. tests/triggers/) |
| H | further new modules in src/hadavin_sdk/triggers/ (ledger logic) and their tests | v3 A1 "ledger logic on top of the Store Protocol"; names INFERRED |
| wait time | new test files for core-b's interface (i), under tests/contracts/ | ORDER 004 item 2; names INFERRED |
| always | handover/core-a/tickets/*, requests/*, boards, reports | ORDER 002 A.7, ORDER 004 item 3 |

## 3. MUST NOT TOUCH
- core-b (SPINE) owns "EVERY existing file of the package and tests (default clause)" and all persistence: store Protocol, memory and Postgres stores, migrations, migrate.py, roles, tick STEPS, app.py, cli.py, config.py, limits.py, evals.py, k1b/*, llm/*, pyproject, lock file, CHANGELOG, README, tests/conftest.py, tests/fixtures/migrations_released.json, the store contract test (v3 A1). Note: SRC/testing/__init__.py and testing/mutation.py already exist, so they are core-b's; exporting a helper from that `__init__` is a request.
- core-c (TEXT) owns guard/textnorm*, guard/redact.py, guard/runmap.py, G5 wording, the model gate wrapper (v3 A1; v4 B1 rows F, G).
- Migrations: written and numbered only by core-b (0006 stop state, 0007 reservations, 0008 receipts only if proven) (v4 B1; ORDER 004 item 3).
- Not built: `pipeline/` package and AK1-a step contract (v3 A2, tier 2); any tier-2 item; executor made live; a new store kind (v2 s.7).
- MUST NOT (ORDER 002 C + v2 s.7): no secrets, real keys, real client data; no live model call; no spend; no merge; no force-push; no GitHub settings change; no push except cloud/core-a and wip/cloud-core-a/*; existing PR, `core/*`, `rebase/*` branches are read-only; no stage names other than demo, pilot, prod; no project words (lead, incident, refund, invoice, intake) in core types; no scanner finding dismissed; no migration applied to a durable database; no stub merged; a step that cannot run is NOT RUN, never faked. ORDER 003: 3-try cap. ORDER 004: no source code before "GO BUILD <letter>" (E excepted); no second review round.

## 4. INTERFACES
Needed from core-b:
- Config fields for D: the tenant constant, the per-sender signing secrets (two valid at once during rotation), and whatever the worker needs to build the runtime. Names and types are NOT given by the plan; the D ticket must propose them as a request file handover/core-a/requests/<n>-<file>.patch (v2 s.5; v3 A1; ORDER 004 item 2).
- Interface (i): "store methods for reservations, receipts, work items: author SPINE, path `src/hadavin_sdk/store/protocol.py` + `tests/contracts/`" (v3 A5; kept by v4 B1). No signatures given. Not yet in inputs/ (checked: no Protocol or contract file there). ORDER 004 item 2: while waiting, write store contract tests for it as NEW test files.
- For H only: store methods and migration 0008; a door role, if created, "needs SELECT on the key and hash columns as well as INSERT" (v4 B2).
Used as they are (existing code, read only):
- `Runtime.handle(agent_id, principal_id, document, trigger_kind="event", trigger_ref="-", mapping=None, *, run_id=None) -> Run`.
- `hmac_v0.verify(headers, body, now_ts, secret, prefix) -> bool`, `hmac_v0.sign(body, ts, secret, prefix)`, `MAX_AGE_S = 300`.
- `handle_slack_action(approvals, headers, body) -> tuple[int, bytes]` as the handler shape.
Offered by this session:
- The crash-point hook and the socket guard, used by the tests of step F (money) and of D. No interface ticket: (iv) was "dropped as ceremony" (v4 B1).
- The endpoint contract for the client tool (path, headers, body fields, answers), fixed by the D ticket and the n8n template.
- Test files for other steps: store contract tests, T1, grants negative tests per role, mutant cases (v4 B1 never-idle rule).

## 5. CODE FACTS a ticket for E or D must respect (checked on this checkout, branch cloud/core-a)
1. VERIFIED. `Runtime.handle` signature at agent_loop.py:352-362; with a run_id, a repeat whose agent, principal and trigger_ref are equal returns the stored run with no model call; a mismatch raises StaleState (docstring 363-376, code 385-391, `_same_message_run` 335-349) (R-code Confirmed; R-zoom M1). Seen in addition: the repeat call's document is IGNORED, so "same key, different payload" returns the old run and no conflict today. This is the candidate delta for H. The endpoint must also send the same trigger_ref every time for one key.
2. VERIFIED. run_id must be `run-` + 32 lower-case hex, else InvalidRunId (agent_loop.py:105-108; pattern at models.py:29) (R-code N1 cites 106-109).
3. VERIFIED. `hmac_v0.verify` takes ONE secret (hmac_v0.py:37-51); MAX_AGE_S = 300 at line 19 (R-code N2). Seen in addition: the age check is `abs(now - ts)`, so a timestamp over 300 s in the future is refused too; the header names come from a `prefix` argument. Two secrets can be done in the new file by calling verify twice; hmac_v0.py needs no change.
4. VERIFIED. `handle` runs the whole model loop before it returns (`for _step in range(agent.max_steps)` at agent_loop.py:465, ends at 585), so it cannot sit in the endpoint before the ack; hence worker.py (R-code M6).
5. VERIFIED. trigger_kind is `Literal["event", "schedule", "user"]` (models.py:99) (R-code N1).
6. VERIFIED WITH A DIFFERENCE. Agent check: `if agent_id not in self.agents: raise Unqualified` (agent_loop.py:377-378) matches. Principal (770-774): an unknown principal does NOT raise; it gets no rights and the gate denies and audits. So "principal in the registry" is a precondition for a useful run, not an error the endpoint will see.
7. VERIFIED. A run left in RECEIVED/WORKING/PLAN_READY goes to NEEDS_PERSON "interrupted" by the tick step `stuck` (tick.py:112-145; function at 122) (R-code N1; R-zoom M1). Truth (door review B1): acknowledged, then NEEDS_PERSON with no notification and no stored document; the sender must poll the run state; it is not "never lost" and not "handed to a person".
8. VERIFIED. store/postgres.py:257-268 `transition` is a conditional `UPDATE ... WHERE state = %s RETURNING` (R-zoom M1).
9. VERIFIED by grep. Nothing in SRC calls `Runtime.handle` (R-code Confirmed); Runtime is built once, at app.py:275.
10. VERIFIED. `handle_slack_action` (receiver.py:22-38): 413 for a body over 64 KB, 401 for a bad signature, else 200.
11. VERIFIED by grep. config.py has no tenant or sender field today; `tests/contracts/` exists with test_store.py and kinds/store_postgres.py (R-code Confirmed, N5).
12. DOES NOT MATCH by my grep (not a D/E fact, noted for honesty): R-code M1 says Runtime is built directly in 17 test files (33 hits); `grep "Runtime("` over tests/ finds 7 files, 8 hits. The review may count helper builders; not followed up.
Not verified, taken from the reviews: the tick is a separate process (cli.py:280-309); purge-DSN pattern (app.py:133-136, 198-207); GRANTS mechanism lines in migrate.py.

## 6. WHERE THE PLAN FILES DISAGREE OR ARE UNCLEAR
1. Scope of the door. v2 item 7: a permanent receipt ledger. v3 item 7: ledger + work items + atomic claim + T2 tests. v4 row D: thin endpoint on `Runtime.handle`, ledger only as proven delta H. v4 wins (B1 "REPLACES plan-v3 A2 table").
2. Order. v3 A5: "DOOR 9, 7, 8". v4 lists D before E; ORDER 004 says E first. ORDER 004 wins (newest, and it matches v3's reason: helpers first).
3. Migration numbers. v3 A1: 0006 reservations, 0007 stop state, 0008 receipts. v4 B1 and ORDER 004: 0006 stop state, 0007 reservations, 0008 receipts only if proven. v4 wins.
4. Crash-hook interface ticket. v3 A5 (iv) names DOOR as author; v4 B1 drops it. v4 wins: E has no interface ticket.
5. Where contract tests go. v4 never-idle rule names the existing files tests/contracts/test_store.py and kinds/store_postgres.py; ORDER 004 says "as new test files". ORDER 004 and the ownership rule win: new files only.
6. UNCLEAR: "records the request and acks" (v4 row D). Without migration 0008 there is no table to record a request in, and nothing that hands a request from endpoint.py to worker.py. The run row is created only inside `Runtime.handle`, which the worker calls. See question 1.
7. UNCLEAR: T2 (replay after 6 minutes, 25 hours, 31 days; crash points) belonged to DOOR in v3 item 7; v4 row D lists only T5, but v4 B4 still speaks of "T2 and T5". See question 4.
8. UNCLEAR: v4 B4 reads "trigger_kind one of event, schedule, user, document as raw bytes". The code has three kinds; "document as raw bytes" is a separate precondition, not a fourth kind.
9. UNCLEAR: "test-only, not public API" (v2 item 9) while the folder is SRC/testing/, which ships with the package ("Test and review tooling shipped with the SDK", testing/__init__.py). Read as: shipped but not exported and not used at run time.
10. QUEUE.md rows Q3-Q6 (baselines of #83, #89, #73, core/ak1-a) are for items v3 moved to tier 2; the table header says ORDER 004 replaces only the TICKET DRAFT and CROSS-CHECK rows. See question 6.

## 7. OPEN QUESTIONS for the lead
1. How does a request get from endpoint.py to worker.py in step D when no receipts or work-items table exists? Checked: v4 rows D and H; R-code M6; agent_loop.py:465-585 (handle blocks through all model calls); no queue table in migrations 0001-0005. Recommended: the D ticket states plainly that the ack cannot wait for `handle`, which is the trigger v4 row H names for a small work-items table (migration 0008, core-b). Alternative if the lead wants zero migration in D: the endpoint runs `handle` in a worker thread of the same process and acks at once; a crash then loses the request unless n8n retries (weaker; needs the error workflow).
2. Which sender identifies a request, and where is it read before the signature is checked (one secret per sender)? Checked: v3 A5, v4 row D, hmac_v0.py (prefix-based header names, no sender). Recommended: a sender id header under the endpoint's own header prefix, used only to pick the secret pair; the same sender id inside the signed body must equal it, else 401.
3. Which header prefix and URL path does the endpoint use? Checked: not in any plan file; Slack uses `X-Slack` and `/slack/actions` (receiver.py:18). Recommended: decide in the D ticket (a neutral prefix such as `X-Hadavin`, one fixed path), lead verdict in DECISIONS.md.
4. Who writes T2 (replay and crash-point tests) now? Checked: v3 A2 item 7, v4 B1, B4. Recommended: DOOR writes the T2 cases that apply to the thin endpoint inside the T5 folder (replay re-signed after 6 minutes; crash between ack and run); the 25-hour and 31-day cases move to H because they need stored receipts.
5. Where do the n8n template files live, and are they shipped in the wheel? Checked: v2 item 8, v3 A1, v4 row D give no path; top-level folders are demos/, docs/, tools/, src/, tests/. Recommended: a new folder inside the new package (src/hadavin_sdk/triggers/n8n/), so the T5 tests can load them and no existing file changes; if pyproject must change to ship JSON files, that is a request to core-b.
6. Do baselines Q3-Q6 still run, and does core/T1-T2-tests (an input of D, no queue row) get one? Checked: QUEUE.md, ORDER 004 item 4 ("baselines of your input heads"). Recommended: stop Q3-Q6 (tier 2), keep Q7 (core/ak-g2-a), add core/T1-T2-tests.
7. Socket guard source: the inputs folder has only the crash hook and the launcher; no socket guard exists in SRC or tests/conftest.py (grep). Recommended: write it new and small in step E (patch `socket.socket.connect` to raise unless the address is loopback), stated in the E ticket.
8. Tenant constant: name and type of the config field, and what the worker uses as principal_id and agent_id for a request. Checked: config.py has no such field. Recommended: the D ticket proposes the fields in one request file to core-b; agent and principal come from config per sender, never from the request body.

## 8. NOT READ / NOT CHECKED
- Not read: old-plan-v4-1.md, old-plan-v4-3.md, atlas-n8n.md (no frozen plan file pointed to a specific part needed for this readback; the D ticket will need n8n.md s.4 and 8.6), review-plan-1-*, review-plan-2-*, resolve-plan-1.md, inventory-*.md, handover/BRIEF-PREAMBLE.md, MODEL-ROUTING.md, RULE-R456.
- Not checked: any branch or PR (core/ak-g2-a, core/T1-T2-tests); the other sessions' handover folders; whether run rows are ever purged (grep found DELETE only for tool_calls and redaction_maps in postgres.py, memory store not read); `create_run` uniqueness beyond the UniqueViolation handler at postgres.py:240-242; n8n timeout, retry and signing behaviour; whether core-b has published interface (i).
- Nothing was run: no tests, no ruff, no git command that changes anything. Line numbers are from the working tree on cloud/core-a, not compared with origin/main 51c9fc4fb.
