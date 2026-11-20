# Ticket D: thin signed endpoint, worker process, n8n template (step D of plan-v4-final B1)

- Package id and name: D, `triggers/` (signed inbound door). Path class: security. Extended review: one ticket round (ORDER 004 item 3), result reviews capped at three (plan-v4-final B1).
- Depends on (merged first): step E helpers (same PR group D+E); REQUEST 001 to core-b (section 7b). Nothing else.
- Owner: DOOR (core-a), new files only. Every change in an existing file is a request to core-b (section 6).
- Written 2026-11-20 from origin/main 51c9fc4fb. S = `src/hadavin_sdk`. Nothing was run. Every `file:line` below was opened in this run; anything else is marked UNVERIFIED. Lead verdicts of ORDER 006 (05:24Z) are folded in and marked "DECIDED (ORDER 006)".
- Length note: this ticket is over 250 lines because it carries the draft check table (section 3) and the test list (section 10) that ORDER 004 asks for.

> RECONCILIATION NOTE by core-a (05:31 UTC), wins over section 9 "Needed from step E": ticket E (tickets/E-test-helpers.md) was written at the same time and is the one being built. The three crash helpers asked for in section 9 (FlagFileCrash, RaisingCrash, CrashingStore) are ONE class there: `hadavin_sdk.testing.crash.CrashPoints` (`wrap(store, "store", [...])`, `arm("store.create_run:after")`, raise mode `SimulatedCrash`, exit mode with a flag file). `sockets.no_network` is CUT (ORDER 006 answer 7: no named test of D needs it). `signed.request`, `signed.fake_secret` and `wsgi.call` are small local helpers inside tests/triggers/, not a package under src. Builders code against these names.

## 1. PURPOSE (plain words)
The client runs an automation tool called n8n. When something happens there (a mail arrives, a record changes), n8n must be able to hand one text document to our agent runtime. The hand-over is one web request.
Three things can go wrong with a web request: a stranger sends a fake one, the tool sends the same one twice, or our process dies half way. This ticket builds the small "door" that handles all three:
1. Only the client's tool may ask. Each request carries a **signature**: a keyed checksum (HMAC-SHA256) made with a secret both sides know. We already have this checksum code for Slack buttons; we reuse it.
2. One request starts at most one piece of work. The tool puts a **request key** (a stable id it chooses, the same on every retry) into the request. We turn the key into the id of the **run** (one row in our `runs` table = one piece of agent work). The database refuses a second row with the same id, so a repeat finds the first run instead of starting a second.
3. We say "received" only when the run row is stored. If our process dies after that, a housekeeping pass that already exists (the **tick**) marks the run "needs a person"; nothing is silently lost and nothing runs twice.
The outcome of the run is shown to people the way it is today (the **shadow card**: a message that shows what the agent would do and never acts). The door returns only the run id and its state.
We also ship a ready n8n workflow that signs and sends the request, and a second small n8n workflow that reports a failed hand-over to a person.

## 2. RIGHT-SIZE, NEEDED-CHECK, RUNG TABLE
RIGHT-SIZE: new shipping code, guarantee-class (the "once-only start of a run per signed request key" sentence of plan-v4-final B3). The two n8n files are config, not code. About 250 source lines in two new modules.

NEEDED-CHECK (2026-11-20). Question: what does this add over an n8n Webhook node calling `Runtime.handle` or the ledger directly, and over what S already has?
- n8n cannot call `Runtime.handle`: it is a Python method and nothing in S exposes it (grep of S and demos for `.handle(` found no caller; S/approvals/receiver.py:22-37 serves only Slack approval clicks). n8n writing straight into our `runs` table would need the runtime database role inside n8n and would skip the agent-qualified check (S/runtime/agent_loop.py:377-378), redaction (406-426), limits (404) and audit (394). Refused on least privilege.
- n8n itself gives no once-only promise: atlas-n8n.md line 155 (a) "the Webhook node has no request-key dedupe", (b) no exactly-once statement; line 80 lists user reports of one call starting two runs. So the dedupe must sit on our side.
- Already in S and REUSED, not rebuilt: signing and checking (S/approvals/hmac_v0.py:26-51); one run per caller-chosen run id (S/runtime/agent_loop.py:380-393 with 335-349; primary key S/store/migrations/0001_core.sql:6; S/store/postgres.py:238-242; S/store/memory.py:51-55); crash clean-up (S/runtime/tick.py:112-145); HTTP status pattern (S/approvals/receiver.py:27-28, 45-52).
- Missing in S: any HTTP entry that reaches `Runtime.handle`; the key-to-run-id rule; acceptance of two secrets during a swap (hmac_v0.verify takes one, hmac_v0.py:37-39); sender configuration; a way for a process to read the sender secrets (App has no such field, S/app.py:46-60).
ONE-PLACE-PER-JOB: signature maths lives only in `approvals/hmac_v0.py`; dedupe lives only in `Runtime.handle` + the `runs` primary key; crash clean-up lives only in tick `stuck`; the door adds only derivation, checks and HTTP mapping. No second ledger, no second retry engine, no second signature scheme.

Verdict per part: endpoint NEEDED. Worker process NEEDED (something must host the endpoint and call `handle`; it is one process with the endpoint, see finding 1). n8n template NEEDED as config (rung 1). Error workflow: TOOL-COULD-DO, and it does: it is pure n8n config, we ship a template and no code. Receipt ledger (step H): DUPLICATE of `Runtime.handle` dedupe, cut (section 4).

RUNG TABLE (CODE-LAST v1, scale 1 to 5 of 2026-11-06)
| Component | Need | Rung tried | Evidence (source, date) | What only our code gives | Verdict |
|---|---|---|---|---|---|
| Receive the trigger from the client's event | client tool talks to us | 1 (n8n Webhook, Gmail, schedule nodes) | atlas line 40, read 2026-11-14 | nothing: n8n does it | CUT (stays in n8n) |
| Sign the outgoing request | prove the sender | 1 (n8n Code node with `crypto`, or Crypto node) | atlas line 66 (Cloud provides `crypto`); Crypto node UNVERIFIED (not in the atlas) | nothing | CUT-TO-CONFIG+GLUE (template) |
| Verify the signature | no forged start | 2 (`approvals/hmac_v0.verify`) | hmac_v0.py:37-51, read 2026-11-20 | two valid secrets during a swap (about 10 lines) | CUT-TO-CONFIG+GLUE |
| One run per request key | no doubled work | 2 (`Runtime.handle(run_id=...)`) | agent_loop.py:363-393; tests/test_peel_run_id.py:96, 114, 224 | the key-to-run-id rule (5 lines) | CUT-TO-CONFIG+GLUE |
| Same key, other payload answers conflict | no silent swap | 2 (`trigger_ref` compare, StaleState) | agent_loop.py:343-348 | payload hash put into `trigger_ref` (1 line) | CUT-TO-CONFIG+GLUE |
| Crash after "received" ends with a person | no lost request | 2 (tick `stuck`) | tick.py:112-145 | nothing | CUT (reused as is) |
| HTTP entry + process | a way in | 1 n8n cannot host Python; 3 none; 4 a WSGI server library (waitress, gunicorn) is a new dependency, not tested, not licence-checked: UNVERIFIED; 5 stdlib `wsgiref` + our callable | atlas 155; pyproject.toml:14-19 (four base dependencies, none a server) | the checked path from bytes to `handle` | KEEP-CODE (thin) |
| Report a failed hand-over | a person hears of it | 1 (n8n error workflow) | atlas lines 36, 109 | nothing | CUT (template only) |
| Receipt ledger, work items, door role (step H) | none proven | 2 covers it | section 4 | nothing | CUT |

## 3. DRAFT CHECK (lead draft `inputs/draft-tickets-C-D.md`, ticket D part and finding lines)
| # | Draft claim | File:line opened | Result | What the code says |
|---|---|---|---|---|
| 1 | MAX_AGE_S is 300 | S/approvals/hmac_v0.py:19 | VERIFIED | `MAX_AGE_S = 300` |
| 2 | sign at 31-34 | hmac_v0.py:31-34 | VERIFIED | `sign(body, ts, secret, prefix) -> dict` |
| 3 | verify at 37-51: one secret, ASCII timestamp of at most 12 digits, `abs(now - ts)`, constant-time compare | hmac_v0.py:37-51 | VERIFIED | one `secret`; `len(ts) <= 12` (47); `abs(now_ts - int(ts)) > MAX_AGE_S` (47); `hmac.compare_digest` (51); empty secret refused (41-42) |
| 4 | HTTP pattern receiver.py:17, 27-28, 45-52 | S/approvals/receiver.py:17, 27-28, 45-52 | VERIFIED | MAX_BODY 64 KiB; 413 on oversize; Content-Length digits-only, else 400. Note: a MISSING length is read as "0" there (45), not 400 |
| 5 | `handle` signature at 352-362 | S/runtime/agent_loop.py:352-362 | VERIFIED | exactly as quoted |
| 6 | STUCK table at tick.py:113-120 | S/runtime/tick.py:112-119 | WRONG (line numbers only) | the dict is 112-119; RECEIVED, WORKING, PLAN_READY map to "interrupted" (113-115) |
| 7 | `stuck` at 122-145 moves quiet runs to NEEDS_PERSON | tick.py:122-145 | VERIFIED | plus an audit outcome event (133-143). It posts NO card: a person sees it only in the portal or the audit |
| 8 | principals at identity.py:10-15, registry.py:69, 219 | S/identity.py:10-15; S/registry.py:69, 219 | VERIFIED | |
| 9 | an unknown principal is not refused by `handle` | agent_loop.py:377-393, 770-774 | VERIFIED | only the agent is checked (377); the gate later gives an unknown principal no rights (772-774) |
| 10 | proof (a): one run per run_id | agent_loop.py:380-393, 335-349; tests/test_peel_run_id.py:96, 114, 224, 348; tests/contracts/test_store.py:368, 392 | VERIFIED | all six test lines are the named tests |
| 11 | proof (b): repeat with another document is NOT a conflict today; document not stored; only its hash is audited | agent_loop.py:343-348, 394; 0001_core.sql:5-19 | VERIFIED | docstring says so outright (369-370) |
| 12 | `trigger_ref` is read nowhere else | grep of S and demos: S/models.py:100, 0001_core.sql:11, agent_loop.py:336-385 only | VERIFIED | NOTE: `runs` is portal-readable (S/store/migrate.py:47 `portal=True`), so whatever we put in `trigger_ref` is visible to the portal role |
| 13 | proof (c): run rows are never purged | S/store/postgres.py:487, 522, 529; S/audit/chain.py:244; S/store/migrate.py:47, 59, 62-65 | VERIFIED | grep of S for DELETE/TRUNCATE finds no statement on `runs`; runtime grant on runs is SELECT, INSERT, UPDATE (40, 47); purge role has only column SELECT on runs (47) |
| 14 | proof (d): `create_run` unique | 0001_core.sql:6; postgres.py:238-242; S/store/memory.py:51-55 | VERIFIED | |
| 15 | proof (e): preconditions of `handle` | agent_loop.py:377-378, 106-109; S/models.py:29, 99; 0001_core.sql:10 | VERIFIED | order is Unqualified first, then InvalidRunId (380), before any write |
| 16 | App has no secrets field | S/app.py:46-60 | VERIFIED | fields: config, registry, store, audit, limits, executor, approvals, runtime, sources, disabled_sources, purge_store |
| 17 | nothing in S calls `Runtime.handle` | grep `\.handle(` over S and demos: no hit | VERIFIED | |
| 18 | synchronous form can hold a connection up to `stuck_after_s` (tick.py:100-110) | tick.py:100-109 | VERIFIED | `max_steps x call_timeout_s x max_attempts + 60` |
| 19 | app.py adds sender secret names to `extra_secret_names` (150-168) | S/app.py:158-169; S/backends/platform_secrets.py:36-63 | WRONG (lines and effect) | the set is built at 158-168 (150 is the fetch counter). `check` treats that set as READ-TOOL names (40-51): a sender secret named like a backend secret is refused with a "read tool" message. Good behaviour, misleading text: core-b decides (R1c) |
| 20 | registry `_cross_check` checks that the sender's principal exists and is a service | S/registry.py:226, 339 | WRONG | `_cross_check(config, agents, chains, contracts)` gets no principals; they are loaded at 219. The request must add a parameter or a separate check after 219 |
| 21 | `Config.triggers` is not in `config_hash` | S/registry.py:132-145 | VERIFIED | the hash covers agent, route, actions, llm backend fields only |
| 22 | `max_body_bytes` default 262144, at most 2 x `defaults.MAX_DOCUMENT_BYTES` | S/defaults.py:31-33; agent_loop.py:399-401 | WRONG (design) | MAX_DOCUMENT_BYTES is 262144 and the body is the document wrapped in JSON, so a document at the cap could never be sent. Fixed in section 7 (default 2 x, bound 8 x) |
| 23 | key rule `^[A-Za-z0-9._:-]{1,128}$` and n8n key "a mail Message-ID" | draft lines 29 and 31 | WRONG (contradiction inside the draft) | a Message-ID holds `<`, `>`, `@`, which the rule refuses. Fixed: the template sends the SHA-256 hex of the business id (also keeps addresses out of `trigger_ref`, see row 12) |
| 24 | case 7b "Content-Length longer than the body sent gives 400" | receiver.py:45-55 (no such case exists there) | WRONG | a server reading N bytes from a socket that sent fewer blocks until the socket times out; there is no 400 to send. Fixed as case E9 |
| 25 | "the error workflow must be published (atlas section 3)" | atlas-n8n.md lines 36, 40 | WRONG (not in the atlas) | line 36 (section 2): set in Workflow Settings, must start with Error Trigger. "Publish" is said only of the production webhook URL (40). Moved to the UNVERIFIED list |
| 26 | other atlas claims: 2.47.7; Community has no custom variables; HTTP Request success = 2xx only; Cloud Code node has `crypto`; checklist says secrets are read by our code, not n8n; Crypto node not covered | atlas lines 7, 23, 47, 54, 66, 104; grep "crypto node" no hit | VERIFIED | |
| 27 | kill switch on gives state STOPPED | agent_loop.py:250-253, 404-405 | VERIFIED | the run row is still created first (389) |
| 28 | hmac_v0.py needs no change; two secrets = `any(verify(...))` | hmac_v0.py:37-51 | VERIFIED, with a fix | `any()` stops at the first match; section 5 invariant 2 says: check every secret, no early stop |
| 29 | guard/producers.py needs a row only if a pin requires it | tests/test_k5_producers.py:22, 97-106; S/guard/producers.py:55 | VERIFIED: no row needed | the pin covers modules that call `.chat` or `.apply_guardrail`; `triggers/` calls neither |
| 30 | whether a test pins App's fields: UNVERIFIED | grep `fields(App`, `App(` over tests/*.py: no hit | VERIFIED: no pin found by grep | App is built only by `app.build` (S/app.py:286-298) |
| 31 | where n8n files live in the repo: UNVERIFIED | `git ls-files` grep for n8n and workflow; find for `*.json` | VERIFIED: none exist | only `.github/workflows/ci.yml` and `handover/core-a/inputs/atlas-n8n.md` match. New folder `n8n/` at the repo root (section 6) |
| 32 | a first request writes one "received" audit event | agent_loop.py:394 | VERIFIED | |
| 33 | finding 3 basis: Route is inside `config_hash` (registry.py:116-119, 125, 135) | S/registry.py:116-119, 125, 135 | VERIFIED | |
Totals: 33 claims; 26 VERIFIED; 7 WRONG (6, 19, 20, 22, 23, 24, 25; row 6 is a line number only).

## 4. THE THREE FINDINGS OF THE DRAFT
1. One process, ack once the run row exists: **KEEP** (DECIDED, ORDER 006 item 1). Evidence: the `runs` table has no document column (0001_core.sql:5-19); a repeat call returns the stored run and does no work (agent_loop.py:388-393, 366-367). A second process therefore has nothing to pick up. Limits that follow and are stated, not hidden: (a) the document lives only in process memory until the run ends; (b) a crash after the ack ends the run with a person and it is never re-run under that key (tick.py:112-145; B3 of the plan says the same); (c) bursts above `max_running` get 503 and depend on the sender retrying.
2. Step H has no proven delta: **KEEP, verdict NO ticket H this round.** Each candidate delta of plan-v4-final B1 row H, checked against the code:
   - "same key, different payload must answer conflict": given by putting the payload hash into `trigger_ref`; the existing compare raises StaleState and writes nothing (agent_loop.py:343-348, 368). No table.
   - "a stored payload hash": it is in `trigger_ref` (durable, never updated: no store method writes that column, postgres.py:257-280) and in the "received" audit event (agent_loop.py:394).
   - "requests kept beyond run retention": there is no run retention; nothing deletes a run row (row 13 above).
   - "asynchronous work items if the ack cannot wait for the stored request": the ack waits only for one INSERT (agent_loop.py:389 is the first store write of `handle`).
   What would reopen H (write a ledger row with these triggers): a purge of `runs` is ever added; a client needs automatic re-run after a crash; a sender that cannot retry must be served through bursts; the document must survive a restart. ORDER 006 item 4 applies: the 25-hour and 31-day replay cases are cut with H.
3. `as_of` on Config, not Route (belongs to ticket C): **KEEP**, one-line view: Route is dumped into `config_hash` (S/registry.py:125, 135), so a date there would un-qualify every agent on each price refresh; a Config-level field is outside the hash (132-145).

## 5. INVARIANTS (the draft's 12, fixed; reason given where changed)
1. Check order: method and path, Content-Length present and digits, size cap, read body, signature, JSON, fields. Nothing of the body is parsed before the signature verifies. (kept)
2. A request is accepted only if its signature verifies under a configured secret; the sender is the one whose secret verified; there is no sender header (DECIDED, ORDER 006 item 2). Every configured secret is tried on every request, with no early stop (CHANGED: draft used `any()`, which leaks by timing which position matched). Start-up refuses: an empty value, a value under 32 characters, the same value under two senders, more than `MAX_SENDERS` (8) senders. Exactly one sender can match because values are distinct.
3. A timestamp more than 300 s from now, in either direction, is refused before any store call (hmac_v0.py:47). Exactly 300 s is accepted. (kept, boundary added)
4. `run_id = "run-" + sha256(tenant + "\0" + sender + "\0" + key).hexdigest()[:32]` (UTF-8). The three charsets exclude NUL, so two different triples cannot give the same input string. (kept)
5. `trigger_ref = sender + "/" + key + "#" + sha256(document bytes).hexdigest()`. (kept) ADDED consequence: this text is portal-readable (migrate.py:47), so the key must not be personal data; the template sends a hash of the business id.
6. For one (tenant, sender, key) at most one run row ever exists and at most one `handle` loop runs. This rests on the `runs` primary key, never on process memory; it holds across restarts and across several worker processes. (kept)
7. A 2xx is sent only after `store.get_run(run_id)` returned a row whose agent, principal and `trigger_ref` equal the request's. The answer is decided from the ROW, never from which exception `handle` raised (CHANGED: `StaleState` is also raised by a lost state race inside the loop, S/runtime/runs.py:37-42 via postgres.py:266-267, when the row exists and matches). Row present and different: 409, nothing written.
8. Agent and principal come from config per sender, never from the request. `trigger_kind` is the constant "event" (models.py:99). The worker refuses to start if a sender's agent is not in `runtime.agents`, or its principal is missing from the registry or is not of kind `service` (identity.py:13). (kept; the check is in the worker too, so it holds even before core-b's load-time check lands)
9. Run rows are not deleted. A future run purge must keep the key first (reopens H). (kept)
10. The response body holds only `run_id` and `state`. Every refusal has an empty body. Logs hold: status, reason code, sender id (only after verification), run_id, body length. Never the body, key, signature, timestamp header or a secret. (kept, log fields named)
11. No free slot, store unreachable, or no row within `ack_wait_s`: 503, no ack; the sender retries with the same key. (kept)
12. The tick must run in the deployment, or a crashed run never reaches NEEDS_PERSON. The worker logs this once at start; it cannot check it. (kept; honest limit added)
13. ADDED: `handle` runs on a worker thread; an exception there is logged by class name only and never crashes the process; the run is then left to tick `stuck`. Reason: `handle` can raise after the row exists (for example a store error mid-loop, agent_loop.py:468).
14. ADDED: the secrets are read once at start through a resolver that can read only the names listed under `triggers`; the door never receives the whole secret provider. Reason: least privilege, same pattern as platform_secrets.bound (platform_secrets.py:23-33).
15. ADDED: with stage pilot or prod the worker refuses `--host` values other than loopback unless `triggers.allow_non_loopback: true`; TLS is the client's proxy. Reason: the stdlib server is not hardened; default-deny exposure.
16. ADDED: `max_running` default is 1 until step F lands. Reason: spend is charged after each model call (agent_loop.py:485; S/limits.py:17-30), so N parallel runs can pass a budget by up to N calls instead of one. See section 12.
DROPPED: none.

## 6. FILES
Layout facts: tests are flat `tests/test_*.py` with `tests/__init__.py`, plus `tests/contracts/` and `tests/fixtures/`; pytest collects `tests` only (pyproject.toml:79-82); shipped test tooling lives in `S/testing/` (today only `mutation.py`); Postgres tests skip without `HADAVIN_TEST_PG_DSN` (tests/contracts/kinds/store_postgres.py:22-24; tests/test_peel_run_id.py:335-336). No n8n file exists in the repo (row 31).
Create (DOOR):
- `S/triggers/__init__.py` (docstring only).
- `S/triggers/endpoint.py`: pure functions and the WSGI callable; imports `approvals/hmac_v0` and stdlib only; does not import Runtime, the store or any secret module.
- `S/triggers/worker.py`: `Runner`, `make_app`, `main`, `__main__` guard; the only module that touches App.
- `n8n/hadavin-trigger.json`, `n8n/hadavin-trigger-error.json`, `n8n/README-trigger.md` at the REPO ROOT (DECIDED, ORDER 006 item 5). Confirmed: pyproject.toml:59-61 uses the `uv_build` backend with no include or package-data setting, and the package is `src/hadavin_sdk`, so a root folder is outside the wheel. UNVERIFIED: what `uv_build` puts into the source archive (sdist) by default.
- `tests/triggers/__init__.py`, `tests/triggers/test_endpoint.py`, `test_worker.py`, `test_t5_wsgiref.py`, `test_t5_postgres.py`, `crash_launcher.py` (test bodies written by a different agent than the builder).
- Step E files (own ticket): `S/testing/crash.py`, `S/testing/sockets.py`, `S/testing/signed.py` (names proposed in section 9).
Modify: nothing by DOOR. REQUESTS TO core-b:
- R1 = REQUEST 001 (section 7b): `S/config.py` after line 377 and in `_cross_checks` (392-431): add `TriggerSender`, `TriggerSettings`, `Config.triggers`. Reason: `Config` forbids unknown keys (config.py:67-69), so a `triggers:` block cannot load today.
- R1b `S/defaults.py` (after line 33): the default numbers of section 7b. Reason: rule 3, one place for defaults (defaults.py:1-8).
- R1c `S/app.py:158-169`: add every `secret_names` entry of `Config.triggers` to the names checked at start, kept apart from backend, tool and executor names (platform_secrets.py:36-63). Reason: a missing or shared secret must fail before the first request.
- R1d `S/app.py:46-60` and 286-298: one new App field `trigger_resolve: Callable[[str], str] | None = None`, a reader limited to the trigger secret names (pattern platform_secrets.py:23-33), None when `Config.triggers` is None. Reason: App has no way to hand a secret to the worker.
- R2 `S/registry.py:226 and 339`: after principals are loaded (219), refuse a sender whose `agent_id` is not in agents or whose `principal_id` is missing or not kind `service`. Reason: fail at load; today `_cross_check` has no principals argument.
- R3 `README.md`, `SECURITY.md`, `CHANGELOG.md`: the once-only sentence of plan-v4-final B3 with its limits, in this step's PR. Reason: B3 says each sentence enters with its step. (Not read: wording is core-b's.)
- R4 `.github/workflows/ci.yml` only if a guard needs it (line 181 runs bandit on `src demos tools`, which already covers the new package): no change expected.
- R5 `pyproject.toml`: no change (no new dependency, no new script; the worker starts with `python -m hadavin_sdk.triggers.worker`).
Guard pins checked: tests/test_repo_rules.py:296 (`SECRET_FREE` lists runtime, approvals, llm, sources; `triggers` is not in it and must not be added, since the worker reads secrets); tests/test_no_hardcoded_values.py:22-39 (no host name, URL or 12-digit literal may appear in the new modules; the loopback default comes from config). UNVERIFIED: tests/test_lockin_guard.py, tests/test_client_profile.py and tests/test_k5_round11.py walk the source tree (grep hit on `rglob`); whether a new package trips them was not read.
Delete: nothing.

## 7. SIGNATURES, WIRE FORMAT, STATUS CODES
`triggers/endpoint.py`
```
PREFIX: Final = "X-Hadavin"            # header prefix handed to hmac_v0
PATH: Final = "/v1/trigger"
KEY_RE: Final = re.compile(r"[A-Za-z0-9._:-]{1,128}")
ID_RE: Final = re.compile(r"[a-z0-9-]{1,40}")           # tenant and sender ids
def derive_run_id(tenant: str, sender: str, key: str) -> str        # ValueError on a bad charset
def trigger_ref(sender: str, key: str, document: bytes) -> str
def verify_any(headers: Mapping[str, str], body: bytes, now_ts: float,
               secrets: Mapping[str, tuple[str, ...]]) -> str | None  # sender id, or None; tries all
def parse_body(body: bytes) -> tuple[str, bytes]                    # (key, document); raises BadRequest
@dataclass(frozen=True)
class Sender:   id: str; agent_id: str; principal_id: str
@dataclass(frozen=True)
class Accepted: sender: str; agent_id: str; principal_id: str; run_id: str; trigger_ref: str; document: bytes
Start = Callable[[Accepted], tuple[int, dict[str, str] | None]]
def make_wsgi(*, tenant: str, senders: Mapping[str, Sender], secrets: Mapping[str, tuple[str, ...]],
              max_body_bytes: int, start: Start, clock: Callable[[], float] = time.time) -> WSGIApplication
```
`triggers/worker.py`
```
class Runner:
    def __init__(self, runtime: Runtime, store: Store, *, max_running: int, ack_wait_s: float,
                 poll_s: float, crash: Callable[[str], None] | None = None) -> None
    def start(self, req: Accepted) -> tuple[int, dict[str, str] | None]
    def close(self, wait_s: float) -> None        # stop taking work, wait for running loops
def make_app(app: App, *, clock=time.time, crash=None) -> tuple[WSGIApplication, Runner]   # for a client-chosen WSGI server
def main(argv: list[str] | None = None, *, crash: Callable[[str], None] | None = None) -> int
```
`main`: `--host` and `--port` default from `Config.triggers`; exit 0 on a clean stop, 2 config error, 4 store unreachable at start (same codes as `tick`, S/cli.py:300-308), 3 any other failure. It builds the App like `_tick` does (cli.py:289-299: every qualified agent), then serves with stdlib `wsgiref.simple_server` plus `socketserver.ThreadingMixIn`, daemon threads, a per-connection socket timeout of `ack_wait_s + 10`.
`crash` is the step E crash hook; named points in our code: `verified` (before `start`), `submitted` (after the pool took the job), `row_seen` (row read, before the answer is written). Default None = no-op.
Runner.start: (1) `get_run`: row and match gives 200 or 202; row and mismatch gives 409; (2) no row: take a slot (none free gives 503), submit `runtime.handle(agent_id, principal_id, document, "event", trigger_ref, run_id=run_id)`; (3) poll `get_run` every `poll_s` until the row exists or the job ended or `ack_wait_s` passed; (4) decide from the row as in (1); no row: 503.

Wire (DECIDED, ORDER 006 item 3): `POST /v1/trigger`; headers `X-Hadavin-Request-Timestamp` (Unix seconds, at most 12 ASCII digits) and `X-Hadavin-Signature` = `"v0=" + hex(HMAC_SHA256(secret, "v0:" + ts + ":" + raw body))` (hmac_v0.py:26-28); body = one JSON object with exactly `key` (string matching KEY_RE) and `document` (string; sent to `handle` as its UTF-8 bytes). Success body: `{"run_id": "run-...", "state": "<RunState>"}`, `Content-Type: application/json`.

Status codes
| Case | Status | Body | Row written |
|---|---|---|---|
| new key, row exists within `ack_wait_s`, state RECEIVED or WORKING | 202 | run_id, state | yes (one) |
| new key, run already ended when we look | 200 | run_id, state | yes (one) |
| repeat, same key and same document | 200 (202 while RECEIVED or WORKING) | run_id, current state | no |
| same key, different document | 409 | empty | no |
| signature bad, missing, stale, wrong prefix, non-ASCII; timestamp bad | 401 | empty | no |
| signed but body not the exact JSON shape, bad key charset, invalid UTF-8, duplicate JSON key | 400 | empty | no |
| Content-Length missing, not digits, or zero | 400 | empty | no |
| Content-Length over `max_body_bytes` | 413, body not read | empty | no |
| other method on the path | 405 | empty | no |
| other path | 404 | empty | no |
| no slot, store unreachable, no row within `ack_wait_s`, worker closing | 503 | empty | no (or unknown: the retry finds it) |
Notes: a document over `evidence.max_document_bytes` is NOT refused by the door; `handle` creates the run and ends it NEEDS_PERSON `document_too_large` (agent_loop.py:399-401), so the answer is 200 with that state. Kill switch on: 200 with state STOPPED (250-253). Sender's agent no longer qualified is impossible after start (qualification is checked at start only, 206-207).

### 7b. REQUEST 001 to core-b: config triggers
File `S/config.py`. New optional block `triggers:` in config.yaml; absent means the worker refuses to start with a ConfigError. Not part of `config_hash` (registry.py:132-145), so no agent is un-qualified. All models use the `_Strict` base (config.py:67-69).
```
class TriggerSender(_Strict):
    id: str                       # ^[a-z0-9-]{1,40}$
    secret_names: list[str]       # 1 or 2 names (2 only during a swap), distinct, non-empty
    agent_id: str
    principal_id: str
class TriggerSettings(_Strict):
    tenant: str                   # ^[a-z0-9-]{1,40}$, required, no default
    senders: list[TriggerSender]  # 1 to defaults.TRIGGER_MAX_SENDERS (8); ids unique; secret_names disjoint across senders
    host: str = "127.0.0.1"       # literal lives in defaults.py or here: core-b's choice under the no-hardcoding guard
    port: int = 8081              # 1 to 65535
    allow_non_loopback: bool = False       # StrictBool
    max_body_bytes: int = 2 * defaults.MAX_DOCUMENT_BYTES   # > 0, at most 8 x MAX_DOCUMENT_BYTES
    max_running: int = 1          # 1 to 64 (raise the default to 4 after step F, see invariant 16)
    ack_wait_s: float = 5.0       # > 0, at most 30
    poll_s: float = 0.05          # >= 0.01, at most 1.0, and < ack_wait_s
Config.triggers: TriggerSettings | None = None
```
Cross-checks wanted in `Config._cross_checks` (joined to the existing `refused` list, config.py:407-430, names only, never values): duplicate sender id; a secret name used by two senders; `allow_non_loopback` true in demo is allowed, in pilot and prod it is allowed only when set explicitly (no extra rule, just no default). Checks that need the registry (agent exists, principal exists and is kind service) are R2. Checks that need the secret VALUES (length at least 32, distinct across senders) are done by the worker at start, because config never holds values.
Defaults to add in `S/defaults.py` (R1b): `TRIGGER_MAX_SENDERS = 8`, `TRIGGER_MAX_RUNNING = 1`, `TRIGGER_ACK_WAIT_S = 5.0`, `TRIGGER_POLL_S = 0.05`, `TRIGGER_PORT = 8081`, `TRIGGER_MIN_SECRET_CHARS = 32`.
App wiring (R1c, R1d): names into the start-up secret check; `App.trigger_resolve` limited to those names.
Fixture change (core-b's file): `tests/fixtures/config/config.yaml` stays without `triggers`; the T5 tests write their own block into the tmp copy (tests/conftest.py `make_cfg`), so no existing fixture changes.

## 8. MIGRATION NEED
None. No table, column, index, role or grant. `trigger_ref` and `run_id` already exist (0001_core.sql:6, 11). What would change that: any item of the reopen list in section 4 finding 2 (then core-b numbers it; DOOR picks no number).

## 9. INTERFACES
Offered to other sessions: `triggers.endpoint.derive_run_id`, `trigger_ref`, `verify_any`, `make_wsgi`; `triggers.worker.make_app` (a WSGI callable for a client-chosen server), `main`. The wire format of section 7 is the contract for the n8n template and for any later Make or Activepieces outline.
Needed from core-b: REQUEST 001 (config), R1b defaults, R1c and R1d (`App.trigger_resolve`), R2 load check, R3 wording. Until they land the builder codes against a local stand-in dataclass with the same field names in the TEST folder only (never merged into S).
Needed from step E (test helpers, `S/testing/`, test-only), so the E ticket can line up:
- `crash.FlagFileCrash(flag_path) -> Callable[[str], None]`: when the one-shot flag file names the point, delete the file, print a marker line, `os._exit(137)`; otherwise do nothing (port of inputs/demo-hooks.py `FlagFileHooks`, without the sqlite argument and the project point names). Point names are free strings chosen by the caller.
- `crash.RaisingCrash(point)`: same call shape, raises a `SimulatedKill(BaseException)` in the calling thread instead of exiting (for memory-store tests in one process).
- `crash.CrashingStore(inner, crash, points)`: a store proxy that calls `crash("store.<method>.before|after")` around the named methods and passes everything else through (same idea as `SpyStore`, tests/test_peel_run_id.py:40). Needed to kill the process inside `handle` (after `create_run`, at `touch`) without editing S.
- `sockets.no_network()`: a context manager or fixture that makes any non-loopback socket connect fail the test.
- `signed.request(body: bytes, secret: str, ts: int, prefix: str) -> dict[str, str]` (thin wrapper over hmac_v0.sign, hmac_v0.py:31-34) and `signed.fake_secret(*parts: str) -> str` (builds a 32+ character value from parts, so no secret-shaped literal sits in a test, BRIEF rule 3 and tests/test_no_hardcoded_values.py:22-30).
- `wsgi.call(app, method, path, headers, body) -> (status, headers, body)`: calls a WSGI callable in-process with a correct environ (CONTENT_LENGTH, `HTTP_X_...` keys, `wsgi.input`), no socket.
Not needed from E: a fake clock (the endpoint takes `clock=`; the tick takes `now=`, tick.py:335-338, so a plain lambda and a datetime are enough).

## 10. TEST CASES
Store column: M = memory store, runs in this session; PG = needs real PostgreSQL 16 with `HADAVIN_TEST_PG_DSN`, run by the lead on the laptop (the same test bodies run on both unless marked). "Re-signed" = the sender made a new timestamp and signature (plan-v4-final B4).
Normal
- N1 signed fresh request: 202 or 200 with run_id and state; one run row; one "received" audit event; run_id equals `derive_run_id`. M, PG.
- N2 re-signed retry, same key, same document: 200 or 202, same run_id, one row, zero extra model calls (`llm.calls` unchanged, as tests/test_peel_run_id.py:114-131). M, PG.
- N3 byte-identical replay inside 300 s (original signature): same as N2. M.
- N4 two secrets for one sender: signed with the old, then with the new, same key: both 2xx, same run_id. M.
- N5 two senders, same key text: two different run_ids, two rows. M.
- N6 kill switch on: 200, state STOPPED, no model call. M.
Edge
- E1 timestamp exactly 300 s old and exactly 300 s ahead: accepted; 301 either way: 401 and `store.get_run` never called (spy store). M.
- E2 timestamp of 13 digits, empty, with a sign, with spaces, non-ASCII digits: 401. M.
- E3 key of 1 and of 128 characters accepted; 129 or 0: 400. M.
- E4 body exactly `max_body_bytes`: accepted; one byte more: 413 and `wsgi.input.read` never called. M.
- E5 document is the empty string: accepted, run created (what the agent does with it is the runtime's). M.
- E6 document over `evidence.max_document_bytes` but inside the body cap: 200, state NEEDS_PERSON, reason `document_too_large`. M.
- E7 old secret removed from config and worker restarted: a request signed with it gets 401. M.
- E8 GET on the path 405; POST on another path 404; both before any signature work (spy on `verify_any`). M.
- E9 Content-Length larger than the bytes sent, over a real socket: the connection ends by the socket timeout, no row, the server keeps serving the next request. (Replaces draft 7b, row 24.) M, wsgiref.
- E10 Content-Length missing, `abc`, `-1`, `0`: 400. M.
Hostile
- H1 bad signature: wrong secret, one body byte changed, header missing, `v1=` prefix, upper-case hex, non-ASCII: 401, empty body, no row, `parse_body` never called (spy). M.
- H2 signed with sender A's secret but claiming to be sender B in an extra `X-Hadavin-Sender` header: the header is ignored, the run belongs to A. M.
- H3 same key, different document (re-signed): 409, row unchanged, no model call. M, PG.
- H4 signed but malformed: not JSON, array, missing field, extra field, wrong type, bad key charset, invalid UTF-8, duplicate `key` member, nesting depth 10,000, a 200 KB key: 400, no row. M.
- H5 malformed and unsigned: 401 (signature is checked first). M.
- H6 key that tries to collide through the separator (`a/b`, `a#b`, a NUL written as `\u0000`): 400 by KEY_RE. M.
- H7 replay after 300 s with the original signature: 401 before any lookup (expected result per B4). M.
- H8 start-up refusals: two senders with the same secret value; a secret under 32 characters; an empty value; a sender whose agent is not qualified; a principal that is missing or of kind person; 9 senders; non-loopback host in pilot without the flag: `main` exits 2, nothing listens. M.
- H9 log capture over H1 to H7: no body text, key, signature or secret value in any log record. M.
- H10 response to every refusal has an empty body and no header that names the reason. M.
Concurrency
- C1 50 parallel requests with one key (re-signed each): one row, every answer 2xx with the same run_id, one model call. M, PG.
- C2 `max_running` = 4, 8 parallel requests with 8 keys, LLM double that blocks on a barrier: 4 answered 202, 4 answered 503; after release a retry of each 503 key gives 2xx; 8 rows, 8 model calls, no exception in any thread, spend total equals the sum of the 8 costs. This is the test that settles the thread question of section 11b. M, PG.
- C3 two requests, same key, different documents, released together (gated store as tests/test_peel_run_id.py:196-221): exactly one 2xx and one 409; one row. M, PG.
- C4 two worker PROCESSES on one database, 20 parallel requests with one key split across both: one row. PG only.
- C5 slot full (max_running 1, a run blocked): a second key gets 503 within `ack_wait_s`; a repeat of the FIRST key still gets 202 (the pre-check needs no slot). M.
Crash (ORDER 006 item 4: DOOR writes these thin-endpoint T2 cases)
- K1 in-process: `RaisingCrash` inside `handle` after `create_run`; then `run_tick(app, now=later, steps=[stuck])`: state NEEDS_PERSON, reason `interrupted`; a re-signed repeat gives 200 with that state and no model call. M.
- K2 subprocess: `crash_launcher.py` starts `main(crash=FlagFileCrash(path))`; kill at `store.create_run.after`, at `row_seen`, at `store.touch.before`; restart the worker; repeat the request: 200 or 202 with the stored state, one row; after the tick: NEEDS_PERSON `interrupted`. PG only (the memory store dies with the process).
- K3 subprocess kill at `verified` (before the row): the client saw no answer; after restart the same request gives 2xx and exactly one row and one run. PG only.
- K4 store unreachable (store double raising a connectivity error, S/store/protocol.py:29-38): 503, no ack; when the store is back the retry gives 2xx. M.
Property and fuzz ideas (plain pytest loops with a seeded `random`, no new dependency)
- P1 `derive_run_id` always matches `run-[0-9a-f]{32}` (models.py:29) for any triple inside the charsets; changing any one of tenant, sender, key changes the id (10,000 seeded triples).
- P2 any single-byte change of body, timestamp or signature of a valid request gives 401 (500 seeded mutations).
- P3 random bytes as body with a VALID signature never give 5xx and never create a row unless they parse to the exact shape.
- P4 `parse_body(json.dumps({"key": k, "document": d}))` round-trips any valid `k` and any Unicode `d` without lone surrogates.
Mutants (each must be killed by an assertion, judged with S/testing/mutation.py)
| Mutant | Killed by |
|---|---|
| skip the timestamp window | H7, E1 |
| stop trying secrets after the first sender | N4, N5 |
| drop the payload hash from `trigger_ref` | H3 |
| answer 2xx before the row is read | K3 (row count), C2 |
| drop tenant, sender or key from the derivation | P1, N5 |
| parse the body before verifying | H1 (spy), H5 |
| decide 409 from the exception type instead of the row | C3 plus a unit case where `handle` raises StaleState and the row matches |
| remove the 32-character or the distinct-value start check | H8 |
| read the body before the size check | E4 |
FAIL-BEFORE: N2 and H3 fail on main by import error (no `triggers` package); the behaviour-level fail-before is H3 with the hash mutant (today's `handle` returns the old run for a different document, agent_loop.py:369-370).
Not testable here, UNVERIFIED until run against a real n8n (plan B3): every item of the "verify on a real n8n" list in section 13.
Evidence commands: `uv run --all-extras --group test pytest tests/triggers -q` (session, memory); the lead runs the same with `HADAVIN_TEST_PG_DSN` set; `uv run --all-extras --group test ruff check src/hadavin_sdk/triggers tests/triggers`; `bandit -ll -r src/hadavin_sdk/triggers`. Raw output to `handover/core-a/raw/D-evidence-<n>.log`.

## 11. SECURITY AND LEAST PRIVILEGE
Identities and secrets
| Identity or secret | Held by | Reads | Writes | Notes |
|---|---|---|---|---|
| Sender secret(s), one or two per sender | the client's n8n and our secrets backend (named lookup, never in config, code or tests) | n/a | n/a | proves the sender; gives no database or model right; at least 32 characters; distinct per sender and per deployment |
| Worker process = the existing RUNTIME database role | worker | as the runtime role today (S/store/migrate.py:46-68) | same; on `runs`: SELECT, INSERT, UPDATE; no DELETE anywhere except the audit outbox | NO new role, no new grant, no purge DSN use. The worker holds model and channel credentials because it runs `handle`; that is the cost of one process (section 12) |
| `App.trigger_resolve` | worker only | the sender secret names, nothing else | nothing | bound reader (R1d); the endpoint module gets values as a plain mapping and never a provider |
| n8n side | the client's n8n | its own trigger data | one HTTP POST to the door | the secret is the one deliberate exception to "secrets stay out of n8n" (atlas line 104); it must be named as such in n8n/README-trigger.md and stored as an n8n credential where the edition allows it (UNVERIFIED) |
The agent (model) never sees a sender secret; the door has no executor or approver credential.
Two-secret rotation: (1) store the new value under a new secret name; (2) list both names for the sender, restart the worker (secrets are read once at start); (3) switch n8n to the new value; (4) remove the old name, restart. During 2 to 3 both values verify (N4); after 4 the old one is refused (E7). A config with two names for longer than a swap is allowed but the worker logs a warning at every start.
Logged: one line per request with status, reason code, verified sender id or `-`, run_id or `-`, body length, duration. Not logged: section 5 invariant 10. Refused requests write NO audit row (an unsigned caller must not be able to grow the audit chain); see open question 4 for signed conflicts.
What the signature does not cover: method, path, tenant. One path only, so the first two do not matter; two deployments must never share a secret (README sentence), or a request for one verifies at the other for 300 s.
Abuse bounds: body cap before reading; at most 16 HMACs per request (8 senders x 2); per-connection socket timeout; bounded running loops; no rate limit (out, the client's proxy).
Negative tests: H1, H2, H5, H7, H8, H9, E7, and the import rule: a new test asserts `triggers/endpoint.py` imports no module of `actions`, `backends`, `store` or `runtime` (AST scan, same method as tests/test_repo_rules.py:167-169).

### 11b. Is `Runtime.handle` safe to call from several threads at once?
Found, with lines:
- Runtime keeps no per-run state on `self`: fields are set once in `__init__` (agent_loop.py:208-213); a run's working data are locals (396-398, 462-463).
- Both stores serialise every statement behind one lock and one connection: memory (S/store/memory.py:31, 52, 58, 64), Postgres (S/store/postgres.py:193-197, 217, 226, 260, 271). The chain audit uses the SAME lock and connection on Postgres and holds it for its whole transaction (S/audit/chain.py:95-96, 116-122, 525-527). So database work of parallel runs is strictly one at a time: safe, and also the throughput ceiling.
- Create race: the loser gets StaleState and returns the winner's run (agent_loop.py:388-393); tested with two threads on one Runtime (tests/test_peel_run_id.py:196-234) and at store level with eight (tests/contracts/test_store.py:392-409).
- Read tools: admission and rate counters are locked (S/tools.py:1021-1031, 1080-1083).
- Fake model client: locked (S/llm/fake.py:27, 40-43).
- NOT safe in the money sense: spend is added after the call and the budget is read before it (S/limits.py:17-30; agent_loop.py:404, 466, 485-486), so N parallel runs of one agent can exceed a budget by up to N calls. Not a crash, a wider overshoot; step F (reserve before the call) closes it. Hence invariant 16.
- Unlocked shared state: `ChainAudit._pending` list and `_unanchored` dict (chain.py:173, 176, 229, 334-340). A parallel change during `_retry_anchors` could raise inside `checkpoint`, which catches everything and retries next time (301-317). Low risk, reported as a finding for core-b, not fixed here.
- One Postgres connection, no reconnect (postgres.py:193-194): after a dropped connection every request fails until the worker restarts. The door answers 503; see open question 5.
UNVERIFIED: thread safety of the real model clients (S/llm/anthropic.py:104 and S/llm/openai_compat.py:88-89 keep one client object; bodies not read), of the detector members and of the channel `post_card` path. Two full loops with DIFFERENT run ids in parallel are not covered by any existing test (the existing race test's loser returns at once). Test that settles it for the fake kinds: C2 on memory and on PostgreSQL. For real model clients it stays UNVERIFIED this round (no live calls), another reason for `max_running` 1 by default.

## 12. BEST-FIRST TRADE-OFFS (plain words)
- One process, ack after the row (DECIDED). Simpler option: answer only when the run has finished. Gives up: nothing in safety; but it holds the sender's connection for minutes (tick.py:100-109) and n8n's timeout is unknown. Stronger option: a stored work item and a separate worker (step H). Gives up today: simplicity, a migration and a new role, for a case nobody has shown.
- Sender found by trying every secret, no sender header (DECIDED). Gives: one header fewer for the client to get wrong, no "unknown sender" answer to probe. Costs: up to 16 checksum runs per request instead of 2, bounded by the sender cap of 8; secrets must be distinct, checked at start.
- Payload hash in `trigger_ref` instead of a receipts table. Gives: conflict detection with no schema change. Gives up: the hash and key are visible to the portal role, so the key must not be personal data (the template hashes the business id); a plain SHA-256 of a short, guessable document can be confirmed by guessing, which is already true of the "received" audit event (agent_loop.py:394).
- `max_running` default 1, not the draft's 4. Chosen for spend control (section 11b). Gives up: bursts get 503 and rely on the sender's retry. The operator may raise it; the default moves to 4 when step F is in and C2 passes on PostgreSQL.
- Stdlib threaded server on loopback behind the client's proxy. Simpler than adding a server library (no dependency, BRIEF rule 2). Gives up: hardening and throughput of a real WSGI server; `make_app` lets a client host the same callable in the server of its choice. UNVERIFIED: the Python documentation's exact production warning for `wsgiref` and `http.server` (not opened in this run).
- Secrets read once at start. Simpler than re-reading per request. Gives up: a swap needs two restarts. Safer on spend and latency (no secret-store call per request).
- Refusals have an empty body and one status per class. Gives up: easy debugging for the client; the README lists the reasons per status and the operator reads the reason code in our log.
- Missing Content-Length is 400 here; the Slack receiver reads it as 0 and then answers 401 (receiver.py:45). Chosen: 400, because an empty trigger can never be valid.

## 13. WHAT STAYS OUT
Receipts and work-items tables, a door role or DSN, any migration (step H: cut); the 25-hour and 31-day replay cases (cut with H, ORDER 006 item 4); a result callback to n8n (the outcome is the existing shadow card); per-request choice of agent or principal; rate limiting and TLS (the client's proxy); binary or multi-part documents; an n8n community node; Make and Activepieces (lead's outline); audit rows for unsigned refusals; automatic re-run after a crash; re-reading secrets without a restart; a new WSGI server dependency; any change to `hmac_v0.py`, `Runtime` or the stores; project words in core types (the door knows only tenant, sender, key, document).
n8n outline (config, not code). Main workflow: (1) the client's own trigger; (2) Set node: `key` = SHA-256 hex of a stable business id (never the execution id), `body` = `JSON.stringify({key, document})` as ONE string; (3) sign: `ts` = Unix seconds, `sig` = `"v0=" + HMAC-SHA256(secret, "v0:" + ts + ":" + body)` in hex; (4) HTTP Request: POST, raw body = that same string, the two headers, Never Error off, Retry On Fail on for this node only; (5) optional IF on `state`. Error workflow: Error Trigger, then a message to a person with workflow name, execution URL, last node, error text (atlas line 36). 401 and 409 land there by design; 503 is retried first.
Verify on a real n8n before any client text (all UNVERIFIED): the raw body is sent byte-identical to the signed string; where the secret can live (Community has no custom variables, atlas lines 23, 47; Code node credential access not documented, line 66); the Crypto node; HTTP Request timeout unit and default (line 54); Retry On Fail maximum tries and wait (line 37); whether a retry re-runs the sign node (if not, a retry later than 300 s gets 401); whether the error workflow must be published; one webhook call starting two executions (line 80) must still give one run.

## 14. OPEN QUESTIONS, UNVERIFIED, NOT READ
Open questions for the lead (checked; recommended answer)
1. `max_running` default 1 until step F? Checked: limits.py:17-30, agent_loop.py:485. Recommended: yes, 1 now, 4 after F with C2 green on PostgreSQL.
2. Which server hosts the callable in pilot and prod? Checked: pyproject.toml:14-19 has no server; receiver.py:5 says production hosting is undecided. Recommended: stdlib threaded server bound to loopback behind the client's TLS proxy for the pilot, `make_app` for a client-chosen server; no new dependency this round.
3. May the key be the raw business id? Checked: migrate.py:47 (portal can read `trigger_ref`). Recommended: no; the template sends its SHA-256 hex; KEY_RE stays narrow.
4. Should a SIGNED conflict (409) write one audit outcome event? Checked: `write_outcome` never raises (chain.py:215-230); AuditEvent fields are free text codes (models.py:193-220). Recommended: yes, one event `trigger.conflict` with run_id and the new payload hash, only for verified senders; unsigned refusals stay log-only. This changes the draft's "409 writes nothing" to "writes no run data".
5. After a store connectivity error, should the worker exit 4 so the client's supervisor restarts it? Checked: postgres.py:193-194 (no reconnect), cli.py:300-302 (tick exits 4). Recommended: yes, after 3 consecutive connectivity errors, answering 503 meanwhile.
6. Should the stuck-run move also tell a person (card)? Checked: tick.py:129-143 writes state and audit only. Recommended: out of this ticket; report to core-b as a finding, because "ends with a person" today means "visible in the portal".
7. Is `X-Hadavin` acceptable as the fixed header prefix literal in `endpoint.py`? Recommended: yes (DECIDED wire, ORDER 006 item 3); it is a protocol name, not a host or secret.
8. Two-name sender config left in place for weeks: warn or refuse? Recommended: warn at start; refusing would break a slow client swap.
UNVERIFIED: every n8n item of section 13; Python documentation wording on `wsgiref` production use; `uv_build` sdist contents; real model client and channel thread safety; whether tests/test_lockin_guard.py, test_client_profile.py or test_k5_round11.py flag a new package; pydantic behaviour for the proposed field bounds (core-b's tests pin it); README, SECURITY, CHANGELOG current wording.
NOT READ: branches core/ak-g2-a and core/T1-T2-tests (inputs named by the plan; no git fetch in this run); PR heads; `inputs/old-plan-v4-1.md`, `old-plan-v4-3.md`, the round-1 and round-2 reviews, `inventory-*.md`; atlas-n8n.md beyond lines 7, 23, 36-40, 47-48, 54, 66, 80, 100, 104, 109, 155; S/llm/* bodies except fake.py:15-60; S/actions/secrets_cache.py; S/tools.py except 1015-1045; S/store/postgres.py:300-440; S/runtime/tick.py:150-248 and 266-334; S/guard/*; S/approvals/cards.py; README.md, SECURITY.md, CHANGELOG.md.
Reviewers: egm:egm-implementation-readiness and egm:egm-codebase-details (one round, ORDER 004 item 3). Done = every invariant 1 to 16 has a passing test, on PostgreSQL where marked PG; every mutant killed; ruff, bandit and the guard tests green. Rollback: tag `pre-D`; the change is new files plus core-b's additive config, so removal is a file delete and a config field with default None.
