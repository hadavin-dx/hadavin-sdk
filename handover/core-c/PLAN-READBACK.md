# PLAN-READBACK of core-c (role TEXT), queue item T1, written 2026-11-20

Read in full: ORDERS.md ORDER 002 to 004, inputs/plan-v2.md, plan-v3.md, plan-v4-final.md, review-plan-3-codebase.md, review-plan-3-zoom-out.md, TICKET-TEMPLATE.md, QUEUE.md. Short names below: v2, v3, v4, R3-code, R3-zoom, O4. SRC = src/hadavin_sdk on branch cloud/core-c (origin/main plus handover files). "VERIFIED" = I opened that line in SRC and saw the stated fact. Nothing was run.

## 1. The plan in 10 lines
1. The build: finish the guarantee-class core of hadavin-sdk (tier 1) with three cloud sessions, on code baseline origin/main 51c9fc4fb; tier 2 is not built this round (v2 title, s.1 default 1, s.4). Sessions: SPINE = core-b, TEXT = core-c (us), DOOR = core-a (v3 A1).
2. Step A, audit drain: a new tick step drains the outbox table and the runtime drains its own in-memory `_pending`. Owner SPINE. No ticket review (v4 B1).
3. Step B, stop state with a reset identity, migration 0006. Owner SPINE. Input PR #76 (v4 B1).
4. Step C, price constraint alone (no zero or negative price except kind fake in stage demo, dated `as_of`, unknown model refused). Owner SPINE. Input #78 (v4 B1).
5. Step D, thin signed endpoint `triggers/endpoint.py` + `triggers/worker.py` + n8n template and T5. Owner DOOR (new files only); SPINE adds the config fields (v4 B1).
6. Step E, test helpers (crash-point hook, socket guard), test-only. Owner DOOR. No ticket review (v4 B1).
7. Step F, money reserve/settle (migration 0007) + the model gate, built together. Owner SPINE (store, installs, sweep, T1) + TEXT (wrapper body) (v4 B1).
8. Step G, text deltas. Owner TEXT (v4 B1).
9. Step H (last letter), receipt ledger delta (migration 0008), only if a delta is proven, else cut. Owner SPINE (store) + DOOR (logic) (v4 B1).
10. Landing: "five PR groups (A+B, C, D+E, F, G, then H if proven)", each one commit whose tree equals its tag's tree; smallest client-ready set = A, B, C, D plus the B3 wording; review rounds capped at THREE per item (v4 B1). Phases: 1 tickets, 2 build, 3 integrate and test (lead), 4 review, 5 land (v2 s.6).

## 2. OUR STEPS in full detail

### 2.1 Step G, text deltas (owner TEXT)
The normative row, quoted in full (v4 B1 table, row G): "Text deltas: P1a+P1b fold (one head), P1c, P2d-1 on, P1d-a; a check-only mask function (runmap.redact_text always mutates the map, runmap.py:524-525); "pattern redactor kind" and "put-back" only as a named delta against `_Redactor` (guard/redact.py:890) and runmap restore functions (601, 607), else cut; G5 wording in approvals/gate.py:42-44, 59, 63 and guard/redact.py:16 (owner TEXT)". Inputs (read-only): "#63, rebase/P1a, #70 and its fix heads, #77, core/P1d-a". Ticket review: one round.

Branch heads (what each is, and where it lives):
| Code | Meaning (v4 B5 glossary) | Head named by the plan | Source |
|---|---|---|---|
| P1a | "P1a/P1b text folding" | PR #63 = core/P1a, and rebase/P1a | v3 A2 item 5; QUEUE Q3 |
| P1b | "P1a/P1b text folding" | PR #70 = core/P1b "and its fix heads"; QUEUE Q4 names core/P1b-fixwip and rebase/P1b-o140 | v3 A2 item 5; QUEUE Q4 |
| P1c | "P1c redactor gaps" | plan is silent: no PR or branch is named for P1c in any inputs column | v4 B5; v3 A2 item 5; v4 B1 row G |
| P2d-1 | "P2d fold scan"; the step says "P2d-1 on" | PR #77 = core/P2d-1 | v4 B5; v3 A2 item 5; QUEUE Q5 |
| P1d-a | "P1d known-secret re-display" | branch core/P1d-a (no PR number given) | v4 B5; v3 A2 item 5; QUEUE Q6 |
Not inputs: #74 "is tier 2 and is not an input" (v3 A2); "P1d rest" is tier 2 (v3 A2); P2d-2/2b, P5b3 and the diagnostics chain #74/#80/#85 are tier 2 (v2 s.4). Presidio is an outline written by the lead, not by a session (v3 A2).

Requirements and rules for G:
- "P1a+P1b fold (one head)": one head is chosen. "Head choices (P3a-2, P1b, rebase copies) are made in the ticket from the baseline evidence and approved by the lead in DECISIONS.md" (v2 s.5).
- Existing PR branches and `core/*`, `rebase/*` are "READ-ONLY inputs; the session merges or cherry-picks them into its wip branch and the lead closes superseded PRs at the end" (v2 s.5).
- "P2d-1 on": the plan gives only these words. What "on" switches (a default, a config flag) is not stated: plan is silent.
- Check-only mask function: the plan says only (a) that it is needed because "runmap.redact_text always mutates the map, runmap.py:524-525" (v4 B1 row G; R3-code N4: "a check-only mask function is missing from interface (iii)"), and (b) how the gate uses it: "Mask step: checks the documents and messages a caller passes, using the check-only function; the system prompt and tool schemas are operator text and are not checked" (v4 B2). Its name, file, signature, return type and error are not given: plan is silent. The behaviour it must serve is in v3 A3: "the mask step takes the caller's run map and REFUSES unmasked content, it never creates a new map (put-back and the restored-hash check at agent_loop.py:844-876 keep working)".
- "pattern redactor kind" and "put-back": only "as a named delta against `_Redactor` (guard/redact.py:890) and runmap restore functions (601, 607), else cut" (v4 B1). So the ticket must name what is missing versus the existing code or cut both. R3-zoom verdict on item 5: "yes for fold and fixes, redactor kind and put-back unproven against existing code".
- Frozen interface: "the existing runmap signatures at 464, 568, 601, 607, 617 are the frozen interface"; interface ticket (iii) redact/put-back is "Dropped as ceremony" (v4 B1). So G must not change those five signatures.
- G5 wording: the plan gives the places and the owner only: "G5 wording in approvals/gate.py:42-44, 59, 63 and guard/redact.py:16 (owner TEXT)" (v4 B1), after R3-code M7: "`guard/gate.py` does not exist: G5 text is in approvals\gate.py:42-44, 59, 63 and guard\redact.py:16; one owner". Earlier mentions: "G5 and README rewording" (v2 s.3 item 1), "G5/README rewording incl. the guarantee statement of A4" (v3 A2 item 1). What the new G5 sentences must say is not written in v2, v3 or v4: plan is silent. The nearest normative text is the masked-input guarantee sentence of v4 B3: "every document and message passes the pattern redactor and a mask failure means no call; this is not "nothing secret can reach a model" (patterns catch the named kinds only; operator prompts and tool schemas are not masked; text sent to tools and sources is out of scope)", and v3 A4: "No client text may claim otherwise".
- Migration need for G: none named. (v4 B1 says "receipts 0008 only if G proves a delta"; see contradiction C7.)
- Tests for G: ticket carries "test cases incl. hostile ones" (O4 item 3); template asks for unit tests, "the FAIL-BEFORE test", hostile inputs, a mutation plan (TICKET-TEMPLATE). Evidence campaign runs "hostile inputs = the corpus already in the repo tests plus each ticket's hostile cases" and the mutant "mask-failure-means-no-call" (v2 s.6 phase 3; v3 A6). While building: "only compile, ruff and the tests of the files you just wrote; ONE full pytest per session when all its steps are coded (recorded, not gated: list each failure as INHERITED or NEW)" (O4 item 6). Known red input: "red #63/#74/#89" (v2 s.1 default 4).
- Done: "ticket invariants each have a passing test ... CI green on its PR; review clean" (v2 s.8). G lands as its own PR group after F (v4 B1 Landing).

### 2.2 Step F, the gate wrapper BODY (owner TEXT; everything else in F is SPINE)
Normative words:
- "Money reserve/settle (migration 0007) + the model gate, built together: gate wrapper module by TEXT; SPINE installs it INSIDE the consumers" (v4 B1 row F). Ticket review: "one round, both sessions' tickets reviewed together" (v4 B1).
- "ONE wrapper class in one new module (body by TEXT, three install lines by SPINE)" (v3 A2 item 6; the "three install lines" wording is REPLACED by v4 B2 and row F).
- "the wrapper has an explicit `bind(agent_id, run_id)` that returns an `LLM` (no ContextVar: k1b/loop.py:104 starts a new thread)" (v3 A3 Rules).
- "meter and audit are constructor arguments" (v3 A3).
- "the mask step takes the caller's run map and REFUSES unmasked content, it never creates a new map (put-back and the restored-hash check at agent_loop.py:844-876 keep working)" (v3 A3); O4 item 1: "mask CHECK with the caller's run map, never a new map".
- "one reservation covers the whole `chat` call including the client's internal retries and settles at worst case when a call is abandoned" (v3 A3).
- "the audit row of a successful call is written with the non-raising outcome writer, and a call whose reserve or mask fails is refused before any provider contact" (v3 A3).
- "the existing charge sites (agent_loop.py:325, 485; k1b/loop.py:170, 179, 206) are deleted in the same change and `add_cost` per run stays" (v3 A3). The deletion is SPINE's (v4 B1 row F: SPINE "deletes the five charge sites in the same change").
- "zero or negative price is refused by a field constraint for every kind except the fake client in the demo stage" (v3 A3); v4 moves this to step C as a "Config-level validator (not a Route field, config.py:72-76)" (SPINE). Not wrapper work.
- Mask step scope: "checks the documents and messages a caller passes, using the check-only function; the system prompt and tool schemas are operator text and are not checked; the k1b acknowledge flag (replay.py:119-123) stays as the one documented unmasked path, demo stage only" (v4 B2).
- Judge: "The judge keeps its own map (judge.py:71) and redacts its own input; the gate's mask check applies to it like to any caller" (v4 B2).
- Evals CLI: "no audit sink exists there (cli.py:146-164): its gate audit is stdout only, stated as such; it has a required cap" (v4 B2).
- MODEL_CALLERS: SPINE "adds the wrapper to MODEL_CALLERS in the same change" (v4 B1); R3-code M4: "the new wrapper module must be in MODEL_CALLERS with a PRODUCERS row or OUTSIDE entry (test_k5_producers.py:78-107)".

Per-site table the wrapper must serve (v3 A3 table, with v4 B2 replacing the judge and evals rows):
| Site | Payer via bind | Meter (constructor arg) | Audit sink (constructor arg) | Masking |
|---|---|---|---|---|
| runtime/agent_loop.py:470 | the run's agent and run id | Limits + Store reserve/settle | chain audit | caller's run map |
| guard/judge.py:72 (screen and shadow card) | the agent of the run being judged; shadow-card judge call charged to the run's agent (v4 B1 F) | Limits + Store | chain audit | judge keeps its own map (v4 B2) |
| evals.py:73 | a named eval payer with a REQUIRED cap, refused in pilot/prod without it | k1b-style in-memory budget | stdout only (v4 B2) | per-case redaction as today (evals.py:63) |
| k1b/loop.py:94 and its judge | the replay's payer | k1b `Budget` (gets reserve and settle, SPINE) | k1b audit sink | as today; acknowledge flag = the one unmasked path |
| extract.py:47 | file DELETED by SPINE | n/a | n/a | n/a |
| guard/bedrock_guardrail.py:101 | outside the gate, stays as is | not metered | n/a | redacts itself |

Signatures the plan gives for the wrapper: only `bind(agent_id, run_id)` returning an `LLM`, plus "meter and audit are constructor arguments". Module path, class name, constructor argument names, the meter's reserve/settle method names, the refusal exception types, and how the caller's run map reaches `chat` are not given: plan is silent (see Q1 to Q4). The `LLM` Protocol it must satisfy is SRC llm/protocol.py:18-28: `chat(self, messages: list[dict[str, Any]], *, system: str, route: str, tools=None, documents: list[bytes] | None = None, output_schema=None) -> Reply` (VERIFIED; note it has no map argument and documents are bytes).

Tests for the wrapper: mutants "cap, zero price, reserve/settle idempotence ... mask-failure-means-no-call" run in the evidence campaign (v2 s.6 phase 3); "tests must be written by a different agent than the builder anyway" (v4 B1 never-idle rule); T1 with 50 separate connections is SPINE's (v4 B1 row F). Guarantee served: "Masked model input (single enforcement point after F and G)" and "Capped spend (after C and F): for model calls made through the gate on PostgreSQL with the grants applied" (v4 B3).

## 3. OUR FILES
Ownership words: TEXT "owns `guard/textnorm*`, `guard/redact.py`, `guard/runmap.py`, `guard/gate.py` wording, and NEW modules: redactor kind, put-back, and the ONE model gate wrapper (item 6 body)" (v3 A1); O4 item 2 corrects the wording part to "the G5 wording in approvals/gate.py and guard/redact.py".
- Create: ONE new module for the gate wrapper (path not named by the plan). Possibly a new module for a "pattern redactor kind" or "put-back" only if the ticket proves a delta (v4 B1 row G). `guard/textnorm*` (does not exist on this branch: `ls SRC/guard` shows no textnorm file, VERIFIED; it presumably arrives with the P1a/P1b heads, not checked).
- Modify: `guard/redact.py` (1256 lines), `guard/runmap.py` (625 lines), and ONLY the G5 wording lines of `approvals/gate.py` (42-44, 59, 63) and `guard/redact.py:16`.
- New test files for our steps: plan is silent on the paths. For other sessions' steps we write test files "as new files" (O4 item 2; v4 B1 never-idle rule: tests/contracts/test_store.py and kinds/store_postgres.py, T1, grants negative tests per role, mutant cases), but `tests/conftest.py`, `tests/fixtures/migrations_released.json` and "the store contract test" are SPINE's (v3 A1).
- Neighbours: everything else in `guard/` (injection.py, judge.py, producers.py, egress.py, http.py, bedrock_guardrail.py), all of `approvals/` except the G5 lines, `llm/*`, `runtime/*`, `k1b/*`, `limits.py`, `evals.py`, `app.py`, `cli.py`, `config.py`, store and migrations = SPINE ("SPINE = core-b owns EVERY existing file of the package and tests (default clause)", v3 A1). `triggers/`, `testing/` helpers, n8n pack = DOOR (v3 A1).
- Handover: `handover/core-c/` on branch cloud/core-c only (ORDER 002 A.7); tickets at `handover/core-c/tickets/<letter>-<short-name>.md`, reviews `tickets/<letter>-review-1.md` (O4 item 3). Code branch pattern `wip/cloud-core-c/<letter>` (O4 item 5).

## 4. MUST NOT TOUCH
- Any existing file outside our four names: it is SPINE's by the default clause (v3 A1). "no edit to another owner's hot file" (v2 s.7). In particular NOT ours: the install of the gate inside `Runtime.__init__`, `_replay` (after replay.py:136) and `evals.gate`; deleting the five charge sites; `Budget` reserve/settle; binding the judge (`Runtime._screen`, agent_loop.py:650-652, approvals/cards.py:76-79, guard/injection.py); deleting extract.py with its tests and fixtures; the MODEL_CALLERS and PRODUCERS rows in guard/producers.py; the expired-reservation sweep; T1 (all v4 B1 row F, SPINE).
- Migrations, store methods, grants rows, manifest rows, test-pin bumps: "SPINE authors all of them" (v4 B1). We never number or write a migration.
- README, SECURITY, CHANGELOG, pyproject, lock file, package `__init__` exports: SPINE (v2 s.5; v3 A1). The B3 guarantee sentences go into README and SECURITY, which are not ours.
- Existing PR branches and `core/*`, `rebase/*`: read-only inputs (v2 s.5). "you may push only cloud/core-c and wip/cloud-core-c/*" (O4 item 5).
- "NO SOURCE CODE until the lead writes "GO BUILD <letter>" for that step" (O4 item 5; the A and E exception is not ours).
- "Do not start round 2 on a ticket: unresolved findings go to ESCALATIONS.md for the lead" (O4 item 3).
- ORDER 002 C: "No secrets, real keys, real client data, real mailboxes; no live model call; no spend; no merge; no force-push; no GitHub settings change; no `.gitleaksignore` change; no push to main or to another session's branch or to an existing PR branch ...; no stage name other than demo, pilot, prod; no project words (lead, incident, refund, invoice, intake) in core types; no scanner finding dismissed or suppressed; no bare `git stash` in a shared worktree; a step that cannot run in your box is reported as NOT RUN with the reason, never faked."
- v2 s.7: "no migration applied to a durable database; no new store kind; no executor made live; no code for tier 2; no stub merged; no finding dismissed."
- Design bans from the plan: no ContextVar in the wrapper (v3 A3); the gate never creates a new redaction map (v3 A3); no second wrapper in the text step ("redact and put-back FUNCTIONS (no wrapper)", v3 A2 item 5); LiteLLM "never a dependency" (v2 s.3 item 2); no Presidio backend (tier 2, v2 s.4).

## 5. INTERFACES
We need from SPINE (core-b):
- Interface ticket (ii) "reserve/settle API used by the gate: author SPINE" as "a Protocol file + an executable contract test", copied by the lead into all three `inputs/` (v3 A5; kept by v4 B1: "Interface tickets kept: (i) store methods, (ii) reserve/settle API"). Method names and signatures: not in any file I read, and nothing beyond the plan files is in inputs/ yet. Semantics the plan fixes: one reservation per `chat` call, settle at worst case when abandoned (v3 A3); `Budget` gets "reserve and settle with `spent` including held reservations and a lock" (v4 B1), so the same meter shape must fit both Limits + Store and k1b `Budget`.
- Migration numbers (SPINE gives them, we use none): "stop state 0006, reservations 0007, receipts 0008 only if G proves a delta" (v4 B1); O4 item 3: "0006 stop state, 0007 reservations, 0008 receipts only if proven".
- The installs, the charge-site deletions, the producers.py rows and the judge carrier (section 4), landing in the same change as our module (v4 B1 row F; R3-code M4).
- The audit sink object passed to our constructor: chain audit with a "non-raising outcome writer" (v3 A3). In SRC that is `write_outcome` at audit/chain.py:215 (VERIFIED the name and line; the file is `audit/chain.py`, the reviews write `chain.py`).
- Baselines of our input heads: the board says Q3 to Q9 are "SKIPPED-BY-LEAD ... the lead runs these on the laptop and puts results in inputs/" (STATUS-BOARD.md QUEUE ITEMS); they are not in inputs/ yet.
Others need from us:
- SPINE needs the wrapper module path and class name (for its installs and the MODEL_CALLERS / PRODUCERS rows), `bind(agent_id, run_id) -> LLM`, and the constructor shape (meter, audit) (v3 A3; v4 B1).
- Everyone keeps the frozen runmap signatures (v4 B1): `redact_text(text: str, mapping: dict[str, str], neutralise: Callable[[str], str] | None = None) -> str` (464), `redact_value(value: Any, mapping: dict[str, str]) -> Any` (568), `restore_text(text: str, mapping: dict[str, str], kinds: frozenset[str] | None = None) -> str` (601), `restore_value(value: Any, mapping: dict[str, str], kinds: frozenset[str] | None = None) -> Any` (607), `has_placeholder(value: Any) -> bool` (617). All five lines VERIFIED in SRC guard/runmap.py.
- The check-only mask function (new, ours): the gate uses it (v4 B2). No signature in the plan.
- Patch route for surprises only: `handover/<own>/requests/<n>-<file>.patch` against a named SHA with the reason; owner answers in `requests/<n>.answer.md` (v3 A1).

## 6. CODE FACTS from the two round-3 reviews that touch our steps
| Fact (source) | Check in SRC |
|---|---|
| `redact_text` always mutates the caller's map, runmap.py:524-525 (R3-code N4) | VERIFIED: `mapping.clear()` / `mapping.update(current)` at 524-525; def at 464 |
| runmap has redact_text 464, redact_value 568, restore_text 601, restore_value 607, has_placeholder 617 (R3-zoom N1) | VERIFIED, all five |
| `_Redactor` at guard/redact.py:890 (R3-zoom N1) | VERIFIED: `class _Redactor:` at 890 |
| G5 text at approvals/gate.py:42-44, 59, 63 and guard/redact.py:16; `guard/gate.py` does not exist (R3-code M7) | VERIFIED. Also: approvals/gate.py:203 mentions G5 too (a comment, not in the plan's list). The docstring around lines 45-64 uses another product's words ("WARDEN", "notify", "MCP results", "P13") |
| Model call sites: agent_loop.py:470, judge.py:72, evals.py:73, k1b/loop.py:94 (R3-code Confirmed) | VERIFIED, all four are `llm.chat(` lines |
| Charge sites exactly agent_loop.py:325, 485 and k1b/loop.py:170, 179, 206 (R3-code Confirmed) | VERIFIED, all five |
| k1b/loop.py:104 starts a new thread, so no ContextVar (v3 A3) | VERIFIED: `threading.Thread(target=work, ...)` at 104 |
| `Detector.check(text, source)` has no agent or run, injection.py:19-20 (R3-code B1) | VERIFIED |
| Judge uses a fresh `{}` map, judge.py:71 (R3-code B1) | VERIFIED: `runmap.redact_text(text, {})` at 71 |
| No summary-screen judge call: app.py:216 removes llm_judge; client built at app.py:209 (R3-code B1) | VERIFIED |
| Shadow card is the unmetered judge call: agent_loop.py:650-652 into cards.py:76-79 (R3-code B1) | VERIFIED |
| k1b acknowledge flag sends unmasked, replay.py:119-123; Budget at 136, run id 135 (R3-code N7, M1) | VERIFIED |
| Budget has no reserve/settle and is not thread-safe (R3-code M1) | VERIFIED: k1b/loop.py:40-52 has only `charge` and `exhausted` |
| Bedrock guardrail redacts itself, bedrock_guardrail.py:98-100 (R3-code Confirmed) | VERIFIED |
| extract.py:47 calls the model; producers.py:36 and 58 hold its rows (R3-code M4) | VERIFIED (extract row at 36, `"extract.py"` in MODEL_CALLERS at 58) |
| Evals redacts per case at evals.py:63; second judge client at evals.py:109 (v3 A3; R3-code) | VERIFIED |
| Restored-hash check at agent_loop.py:844-876 (v3 A3) | VERIFIED (block starts at 844, compare at 867) |
| write_outcome falls back to in-memory `_pending`, chain.py:215-230 (R3-code M2) | Only the def line 215 seen; body not read |
| Runtime built directly in 17 test files, 33 hits (R3-code M1) | DIFFERS: `grep -rn "Runtime(" tests` gives 8 hits in 7 files on this branch; the review may have counted other spellings. Not our file either way |
| System prompt and tool schemas are never redacted (R3-code N7) | not checked |
| Masked input is "true today on the run path, judge and evals" (R3-code Confirmed) | Seen: agent_loop.py:397 builds `runmap.RunMap`, 412 redacts the document, 534 redacts tool inputs with the run map |

## 7. CONTRADICTIONS that touch our steps, and which wins
- C1 Who writes the gate wrapper. v2 item 6: SPINE. v3 A2 item 6: "body by TEXT, three install lines by SPINE". v4 B1 row F: "gate wrapper module by TEXT; SPINE installs it INSIDE the consumers". v4 wins.
- C2 A wrapper in the text step. v2 item 5 lists "masked model wrapper"; v3 item 5 says "redact and put-back FUNCTIONS (no wrapper)"; v4 row G keeps "pattern redactor kind" and "put-back" "only as a named delta ... else cut". v4 wins: one wrapper only, in F.
- C3 What the mask step does. v2 item 6: "mask (runmap.redact_text)". v3 A3: takes the caller's map, refuses unmasked content, never a new map. v4 B2: uses the check-only function because redact_text mutates. v4 wins: the gate CHECKS, it does not redact.
- C4 Judge masking. v3 A3 judge row: "caller's run map". v4 B2: "The judge keeps its own map (judge.py:71)". v4 wins. Left open by this: which map the gate's check uses for a judge call (Q2).
- C5 Interface (iii). v3 A5: redact and put-back interface ticket, "author TEXT". v4 B1: dropped, the existing runmap signatures are the frozen interface. v4 wins; but R3-code N4 says the check-only function was "missing from interface (iii)", so the new function now has no interface ticket at all (Q1).
- C6 G5 wording owner and file. v2 item 1 and v3 A2 item 1: SPINE. v3 A1: TEXT owns "`guard/gate.py` wording" (file does not exist). v4 row G and O4: TEXT, in approvals/gate.py and guard/redact.py. v4 and O4 win. approvals/gate.py is otherwise SPINE's by the default clause, so we touch only the named lines.
- C7 Inside v4 B1: "receipts 0008 only if G proves a delta", while the receipts step is H and row H says "proven in the ticket by a failing case". O4 item 3 says "0008 receipts only if proven". Read as a slip for H; G needs no migration (Q8).
- C8 Migration numbering. v2: local numbers, lead renumbers. v3 A1: 0006 reservations, 0007 stop state. v4 B1: stop state 0006, reservations 0007. v4 wins. No effect on our code, only on words in tickets.
- C9 Ticket review rounds. v2 s.6: "max 3 rounds" per ticket. v4 table and O4 item 3: ONE round per ticket, then ESCALATIONS.md. O4 wins for ticket reviews; the cap of three is for result reviews (v4 B1).
- C10 Order of our two steps. v3 A5: wip branches stack "TEXT 5, 6" (text first, then gate). v4 lands F before G and says the single enforcement point exists "after F and G". Which of our branches is cut first under the letters: plan is silent (Q5).
- C11 wip branch name and base. v2 s.5: `wip/cloud-<name>/<item>` cut from origin/main "plus the item's input heads". O4 item 5: `wip/cloud-core-c/<letter>` cut from origin/main (written for A and E). For G the input heads must come in by merge or cherry-pick (v2 s.5); for F there are no heads for our part.
- C12 Zero-price refusal. v3 A3 puts it in the gate rules as "a field constraint"; v4 row C makes it a Config-level validator by SPINE. v4 wins: not in the wrapper.

## 8. OPEN QUESTIONS for the lead
1. Check-only mask function: name, file and signature. Looked at: v4 B1 row G, v4 B2, v3 A3, R3-code N4, runmap.py:464-526. Plan gives no signature. Recommended: put it in guard/runmap.py as `check_masked(text: str, mapping: dict[str, str]) -> None`, raising `RedactionError` when a redaction pass over a COPY of the map would change the text or add an entry; the caller's map is read, never written. Plus a value form for message lists.
2. How does the caller's run map reach the wrapper? Looked at: `LLM.chat` (llm/protocol.py:18-28) has no map argument; `bind(agent_id, run_id)` carries none; v4 B2 says the judge keeps its own map. Recommended: `bind(agent_id, run_id, mapping=None)` keyword addition (SPINE passes the run map at agent_loop.py and the judge its own map), or the lead rules that the check needs no map. Needs a lead verdict because the plan names the bind signature exactly.
3. Wrapper module path and class name. Looked at: v3 A1, v4 B1 ("one new module"), R3-code M4, M7. Plan is silent; `guard/gate.py` was a wrong name in v3. Recommended: `src/hadavin_sdk/guard/model_gate.py`, class `ModelGate`, so it is not confused with approvals/gate.py (the outbound message gate with G5).
4. The k1b acknowledge flag ("the one documented unmasked path, demo stage only", v4 B2) and the evals "stdout only" audit: how does the wrapper know? Looked at: replay.py:119-123, v3 A3 table. Plan is silent. Recommended: constructor arguments only (`mask_check: bool = True`, settable to False by `_replay` only, refused outside stage demo; audit = any object with the outcome-writer method, SPINE supplies a stdout one for evals).
5. Which step do we build and stack first, G or F? Looked at: v3 A5 (TEXT 5, 6), v4 landing order (F, G), C10. Recommended: ticket both now; build the check-only function first as its own small commit at the base of the F branch (F needs it), then the rest of G; ask SPINE to confirm.
6. P1c has no head and "P2d-1 on" has no definition. Looked at: v2 s.3 item 5, v3 A2 item 5, v4 B1 row G, B5 glossary, QUEUE Q11 and Q12, round-1 and round-2 reviews (grep only). Recommended: lead names the P1c source (a branch, or a section of old-plan-v4-1 / old-plan-v4-3 that we may read) and says what "on" switches.
7. G5 wording: what must the new text say? Looked at: v2 item 1, v3 A2 item 1 and A4, v4 B1 row G and B3, R3-code M7, the four lines in SRC. Plan gives places only. Recommended: rewrite to match v4 B3 limits (patterns catch the named kinds only; G5 is the outbound message check, not the model gate; remove other-product words in lines 42-63), and the lead confirms the sentences in the ticket.
8. "0008 only if G proves a delta" (v4 B1): confirm it means H (C7). Recommended: yes, G has no migration.
9. `add_cost` per run "stays" (v3 A3): does the wrapper call `store.add_cost(run_id, cost)` at settle, or does Runtime keep the call? Looked at: agent_loop.py:325-326, 485-486. Recommended: the meter object SPINE hands us does it at settle, so the wrapper holds no store.
10. Who writes the wrapper's tests and where? v4 says tests are "written by a different agent than the builder". Recommended: a different agent of core-c in a new file `tests/test_model_gate.py`; SPINE writes none for the body.
11. Baselines of #63, #70 (and fix heads), #77, core/P1d-a are not in inputs/ (board: SKIPPED-BY-LEAD). Ticket G needs them for the head choice and the INHERITED list. Recommended: lead drops them into inputs/ or lifts the skip.

## 9. NOT CHECKED
- The branch heads P1a, P1b, P1c, P2d-1, P1d-a and every PR: not fetched, not read (as ordered). So what `guard/textnorm*` contains, and whether a head already has a check-only function, is unknown.
- old-plan-v4-1.md, old-plan-v4-3.md, atlas-n8n.md: not opened (as ordered). The round-1 and round-2 reviews, resolve-plan-1.md and the two inventories: grep for G5 and P-codes only, not read in full.
- Not read in SRC: cli.py, config.py, store/*, tick.py, hmac_v0.py, test files (including test_k5_producers.py:78-107), llm/common.py and retry.py (the "client's internal retries"), audit/chain.py bodies, most of guard/redact.py.
- Whether system prompts and tool schemas are really never redacted; the "17 test files" count (my grep differs, see section 6).
- Nothing was run: no tests, no ruff, no import. Line numbers are from this branch's snapshot only.
- LANE-MAP.md (queue item Q2, written by another agent at the same time) was not read.
