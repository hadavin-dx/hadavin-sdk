# TICKET P4b2: billing classes (owner core-b SPINE). DRAFT written 2026-11-20 for QUEUE Q14. No source was edited.
- Package: P4b2 "billing classes" (plan-v3 split of P4b: P4b1 meter kind, built as F-store and F-install; P4b2 billing classes and orphan sweep; handover/core-b/inputs/old-plan-v4-3.md:199). Path class: money. Extended review: no. Ticket review: ONE EGM plan-review round, ordered in ORDER 003 (not run here). Depends on: F-store (migrations 0007 and 0008 on cloud/core-b), the provider mark commit, and core-c's gate for the exhausted-mark request.
- S = src/hadavin_sdk. Stages are demo, pilot, prod. Tests are written by a different agent than the builder. NO source code before "GO BUILD P4b2" in ORDERS.md.
- Size: a short ticket; the code part is small because most of the job is already built (see NEEDED-CHECK).

## Purpose in plain words
Before a model call the meter books the worst case. After the call it must book the truth. For a call that the provider certainly did not bill (never sent, refused for a bad key, throttled) the booking should go back to 0 at once; for a call that may have been billed (timeout, cut off, server error, unknown) the worst case must stay booked. A "billing class" is the name of that decision for one failed call: `unbilled`, `billed` or `unknown`. Today the decision exists only as one yes/no mark on the error (`refused_before_response`), set by one function, and the per-provider facts behind it are unverified. P4b2 turns the yes/no mark into a named, tested class table per provider kind, with each entry saying where its billing fact comes from, and settles what happens to holds that nobody settles (the orphan sweep).

## NEEDED-CHECK (code read before this draft; "read" means opened with line numbers, nothing was run)
Read for this draft (file:lines):
- handover/core-b/QUEUE.md:20 (Q14, full row); PLAN-READBACK.md:1-42 (rows A-H, sections 2-4, 6); LANE-MAP.md (sections on reserve/settle, lines 18 and 183 for the missing-in-package list, 193 for tick); tickets/F-store.md (head, RUNG TABLE line, R1 file table, resolutions Q2-Q10) and tickets/C-price-constraint.md (whole, as the format example); interfaces/ii-meter.md (whole, points 1-14); inputs/TICKET-TEMPLATE.md; requests/to-core-c-1-exhausted-mark.md; notes/core-c-model_gate-copy.md:30-72, 108-137 (core-c's copy of the gate rules, not code on this tree); inputs/old-plan-v4-3.md lines 199, 427, 522-523, 757 (P4b2 rows and T1.4b).
- S/limits.py:24-44 (SpendRefused, Meter), 47-127 (in-memory Budget incl. forfeit 118-127), 133-219 (Limits.reserve 152-185, settle and settle_for 187-219, overshoot audit 205-218), 232-245 (stop, reset).
- S/llm/protocol.py:10-23 (ProviderError with `refused_before_response`, ProviderExhausted); S/llm/retry.py:12-33 (the mark's rules in prose), 54-69 (status, REFUSED_STATUSES = 400 401 403 404 413 422, THROTTLED_STATUS 429), 75-98 (never_sent), 129-166 (with_retry: the only place the mark is set True); S/llm/openai_compat.py:75-78 (narrowed list 401 403 404) and 120-131 (second request clears the mark); S/llm/common.py:335-351 (the per-kind hooks `retryable`, `detail`, `http_status`, `refused_statuses`); S/llm/bedrock.py:104-128 (http_status hook). NOT opened: S/llm/anthropic.py and S/llm/gemini.py bodies (only a grep for the hooks, which found none in them), S/llm/fake.py, S/llm/common.py outside 335-351.
- S/config.py:50-80 only (`__all__`, Money, Route: model_id and two prices, no billing field) and 557-568 (stage refusals and the zero-price helper from step C); S/models.py:322-335 (SpendReservation: status open | settled | expired, settled_usd, closed_at; no billing field); S/defaults.py:148-155 (RESERVATION_EXPIRE_S = 3600, WORST_CASE_OVERHEAD_BYTES).
- S/runtime/tick.py:263-283 (reservation_expire_s, step expire_reservations), 205-229 (purge of closed rows), 310 (step list); S/store/protocol.py:165-188 (SpendRelease, SpendReleaser), 299-336 (reserve_spend, settle_spend, expire_spend_reservations, purge_spend_reservations); S/store/migrations/0008_release_expired_spend.sql:1-14 (header; the release function), listing of S/store/migrations/ (0001 to 0008); S/cli.py:481-560 (release-expired command).
- Not read: n8n, Make, CRM and any vendor billing page (no network use; the facts below are UNVERIFIED for every provider), the bodies of tests/, store/postgres.py and store/memory.py.

Does something already do it?
1. n8n / Make / CRM (rung 1): their model nodes keep no spend cap and no worst-case booking (plan-v2 item 2 and the n8n atlas, as quoted in tickets/F-store.md RUNG TABLE; UNVERIFIED by core-b, atlas not opened here). The decision "was this failed call billed" runs inside our own provider adapters, between an HTTP error and the meter; a workflow tool never sees that error. TOOL-COULD-DO: no.
2. Free library (rung 4): the provider SDKs expose error classes and status codes, not billing facts; llm/retry.py already uses them through the per-kind hooks. DUPLICATE of nothing; no library states "this status is not billed". UNVERIFIED per vendor.
3. Module already in S (rung 2): the following is BUILT and is NOT redone here:
   - the yes/no decision: `ProviderError.refused_before_response` (llm/protocol.py:19), set only in `with_retry` (llm/retry.py:157 and 165), per-kind status list (openai_compat.py:78), cleared on a second request (openai_compat.py:130). Verdict for the mark itself: DUPLICATE.
   - settle at 0 or at the worst case, never lower than the truth: `Limits.settle_for` / `settle` (limits.py:187-219), interface (ii) points 3-6.
   - the orphan sweep (marking): tick step `expire_reservations` (tick.py:277-283) turns an open hold nobody settled into `expired`, worst case kept; purge of old closed rows (tick.py:205-229).
   - the orphan release (lowering): command `hadavin-sdk release-expired` and migration 0008 (cli.py:481-560; 0008:1-14), by design a person under a separate login, audited first (interface (ii) point 12).
4. What is NOT in S: (a) a named class (the mark is a bool); (b) a recorded source and date per provider kind for each status; (c) the gate honouring the mark on `ProviderExhausted` (open request, requests/to-core-c-1-exhausted-mark.md; the gate is core-c's, so with the request unanswered such calls stay at the worst case, the safe side); (d) a test that the class table agrees between the four network kinds and the Budget meter; (e) any automatic lowering of expired holds.

VERDICT per part: mark and expiry and manual release: DUPLICATE (built). Named class table with sources per kind: NEEDED (small, own code; rewrites no behaviour, only names and tests it). Automatic orphan release by the tick: NOT-NEEDED on the evidence read (the release command exists, and lowering a booked amount without a person is the property interface (ii) point 12 deliberately forbids); it becomes NEEDED only if the lead rules otherwise (OPEN QUESTION 2). Overall: NEEDED, narrowed to the class table.

## RUNG TABLE (CODE-LAST v1; scale of 2026-11-06: 1 no-code tools, 2 our core modules, 3 existing free tools, 4 free libraries, 5 own code)
| Component | Need | Rung tried | Evidence (2026-11-20) | What only our code gives | Verdict |
|---|---|---|---|---|---|
| Unbilled failed call settled at 0 | a refused or never-sent call is not counted against the cap | 2 core: `with_retry` mark, `Limits.settle` | built: retry.py:129-166, limits.py:187-219 | nothing new | DUPLICATE (CUT; keep) |
| Named class (`unbilled` / `billed` / `unknown`) per failed call | the gate and the audit say why a call was or was not counted, not only true/false | 2 core: the bool mark | bool mark only (protocol.py:19) | one place that maps an error to a class, with a per-kind source note | KEEP-CODE (about 40 lines, plus tests) |
| Per-provider billing facts | a status counts as unbilled only if the vendor's own page says so | 1 and 3: client's tools, vendor pages | NOT READ; the only page read earlier (a Claude errors page, per old-plan-v4-3.md:267, 427) states nothing about billing of failed calls; other vendors UNVERIFIED | the table with its source and read-date column | KEEP-CODE as data, each unverified cell stays on the worst-case side |
| Orphan hold: mark expired | a hold nobody settled stops being "open" | 2 core: `expire_reservations` | built: tick.py:277-283 | nothing new | DUPLICATE (CUT; keep) |
| Orphan hold: lower the counters | a hold of a call known unbilled does not use the cap for the rest of the day | 2 core: `release-expired` command + 0008 | built: cli.py:481-560 | an automatic variant would need a role that may lower money without a person | CUT (automatic variant held for the lead's ruling, Q2) |
| Rungs 1, 3, 4 for the class table | n/a | n8n, MCP, model features, libraries | the decision sits between an adapter error and the meter, inside our process | n/a | not applicable |

## Generic-words check
Core types and names carry no project, client or product word: `BillingClass`, `billing_class`, `unbilled`, `billed`, `unknown`, `refused_before_response`, `reservation`, `hold`. Stage names appear only as demo, pilot, prod. Provider kinds are the existing neutral kind names (anthropic, bedrock, openai_compat, gemini, fake); vendor names appear only in the source column of the evidence table, as data, not in a type or a function name. No client names, no workflow-tool names and no stage words other than the three in S.

## INVARIANTS
1. Every error a provider adapter raises carries a billing class; the default is `unknown` (the worst case stays booked). Only `with_retry` may produce `unbilled`; a kind may only lower `unbilled` to `unknown`, never raise `unknown` to `unbilled` (the rule of retry.py:12-33 kept).
2. `unbilled` only when no attempt was answered, timed out, was cut off or failed to parse, as today (retry.py:12-33). Unchanged behaviour: every existing mark test stays green; the bool `refused_before_response` stays readable and equals (`billing_class == "unbilled"`).
3. The status-to-class table is one place per kind (the existing `refused_statuses` hook, common.py:351, becomes the table's source) with a comment per entry: source, read-date, or the word UNVERIFIED. An UNVERIFIED entry is allowed only on the side that keeps the worst case booked, or on the side already built and stated as a limit in retry.py:28-32.
4. A class never changes a number by itself: it only feeds the settle decision the gate already makes (settle 0 for `unbilled`, no settle or the worst case for the others). No new store method, no new counter move.
5. Expired holds are lowered only through the audited release command (interface (ii) point 12 unchanged), unless the lead rules otherwise in OPEN QUESTION 2 before build.
6. No secret, request body, prompt or price appears in a class name, an error string or an audit row.

## Files to create, modify, delete (S = src/hadavin_sdk)
Create: tests/test_billing_classes.py (by a different agent); tests/contracts/test_meter_billing.py only if the gate test (core-c) does not already cover the interface (see Interfaces).
Modify (reason): S/llm/protocol.py (add `BillingClass` and the attribute; keep the bool as a derived read); S/llm/retry.py (set the class where the mark is set, same conditions; module docstring updated); S/llm/openai_compat.py (the clear at line 130 lowers the class); S/llm/common.py (the per-kind table hook, around line 351); S/llm/bedrock.py only if its table needs an entry; CHANGELOG.md (behaviour note: none for callers, the class is additive); interfaces/ii-meter.md (the class sentence under "Provider errors", the file is core-b's).
Delete: nothing. Not touched: S/limits.py, S/store/*, S/runtime/tick.py, migrations, S/config.py, S/models.py (the draft needs none of them; if the build finds it does, stop and ask).

## Public signatures (names only; neutral)
```python
BillingClass = Literal["unbilled", "billed", "unknown"]   # S/llm/protocol.py
class ProviderError(RuntimeError):
    billing_class: BillingClass = "unknown"
    refused_before_response: bool            # kept: property, True only for "unbilled"
# S/llm/retry.py: with_retry(...) signature unchanged; it sets error.billing_class where it set the mark.
# per kind (common.py): refused_statuses stays; a new read-only table maps a status to a class with its source note.
```
`billed` is for a status a vendor page says is billed (none today: no entry is VERIFIED). Errors: none new.

## Migration number needed: ASK, DO NOT PICK
The draft needs NO migration: the class lives on an error object and in an audit row's existing fields. IF the lead rules for automatic release (Q2) or for a stored class on the reservation row, a migration is needed. The next free number is 0009, after 0008 (written, not yet released: QUESTIONS.md item 5 asks the lead to confirm 0008). core-b does not choose 0009 or any other number; the lead gives it, and a table or column added in a migration also needs its GRANTS row and its sha256 in tests/fixtures/migrations_released.json only at release.

## Interfaces
Offered by core-b: (ii) Meter is unchanged (interfaces/ii-meter.md points 1-14). New sentence for "Provider errors": `ProviderError.billing_class`, values `unbilled | billed | unknown`, default `unknown`; the bool mark stays and equals "unbilled".
Needed from core-c (gate): (a) answer to requests/to-core-c-1-exhausted-mark.md (honour the mark on `ProviderExhausted`; until then rule 2 of retry.py:20-22 stays inert); (b) optionally read `billing_class` instead of the bool and put it in the audit outcome code; if core-c keeps the bool, nothing breaks. Needed from core-a: nothing. Needed from the lead: OPEN QUESTIONS 1-4.

## Tests (tests/test_billing_classes.py; the contract test for each interface is marked CT)
Normal:
- N1 a refused connection on the only attempt, 401, 403: `unbilled`; the bool is True.
- N2 500, 502, 529, a timeout, a cut-off read, a bad answer: `unknown`; bool False.
- N3 a successful call: no error, no class.
Edge:
- E1 429 on every attempt then exhausted: `ProviderExhausted` with class `unbilled` (as the mark is today); a mix of refused connections and 429: `unbilled`; one 500 anywhere: `unknown`.
- E2 429 then 400: `unknown` (the retry.py:23-24 rule); 400 as the only attempt on a kind with the default list: `unbilled`; the same 400 on openai_compat: `unknown` (narrowed list, openai_compat.py:78); 413 and 422 likewise.
- E3 openai_compat second request fails after a first answered one: `unknown` (openai_compat.py:126-131).
- E4 a cause chain longer than 8: `unknown` (retry.py:75-98).
- E5 the bool and the class agree for every case above (property test over the table).
Hostile:
- H1 an error object whose `status_code` is a string, a bool, a float, negative, or 10**12: `unknown`, no exception from the classifier.
- H2 a kind that tries to set `billing_class = "unbilled"` on an error with an answered attempt: refused by the test of invariant 1 (the only writer is `with_retry`; a grep-style test on the package pins it, as tests/test_k5_producers.py pins producers).
- H3 an SDK error message that quotes the prompt and a key: the class and the described text contain neither (describe, retry.py:123-126, unchanged).
- H4 a value outside the three names assigned to the attribute: the gate and the audit map it to `unknown` (the safe side).
- H5 a streamed call (no adapter streams today; interface (ii) point 13): a test that no adapter sets `unbilled` when the reply was partly received, written as a fake adapter.
CT (contract tests):
- CT1 interface (ii) with a real `Limits` on the memory store and, with HADAVIN_TEST_PG_DSN set, PostgreSQL: for each class, the gate-shaped sequence reserve, call that raises, settle per class; `unbilled` leaves the day and month counters at their value before the reserve, `unknown` leaves them at the worst case, a later settle with a higher real cost raises it and never lowers it. Both meters (Limits, Budget) give the same result.
- CT2 the Provider-error interface: every kind (anthropic, bedrock, openai_compat, gemini with their SDK errors faked) yields only the three class names and obeys invariants 1 and 2.
- CT3 orphan path, using what exists: a hold left open past the expiry age is marked expired by the tick step, the counters do not move, a settle racing it never lowers them; release-expired lowers them once (these cases exist in F-store tests; the new test only names the three classes in its comments and must not duplicate them).
FAIL-BEFORE (fails on today's tree by assertion, not by import error): `ProviderError().billing_class` is "unknown" and a 401 error has class "unbilled" (on today's tree the attribute does not exist: AttributeError counts as the failing assertion only if the test reads it through `getattr(..., None)` and asserts equality).
Mutants (one edit each; the test in brackets kills it): drop the all-attempts-unsent condition [E1]; widen openai_compat to the default list [E2]; remove the clear at openai_compat.py:130 [E3]; default class "unbilled" [N2, H4]; bool and class disagree [E5]; `billed` assigned without a source [H2].

## Evidence commands (raw output saved under handover/core-b/evidence/P4b2/)
`uv run --all-extras --group test pytest tests/test_billing_classes.py tests/test_limits_reserve.py tests/contracts/test_store_spend.py` (PostgreSQL cases with HADAVIN_TEST_PG_DSN set; the lead's PostgreSQL 17 run is the one that counts); the existing llm and gate test files; `uv run --all-extras --group test ruff check src tests` and `ruff format --check src tests`; the mutant script; then the full suite once.

## Rollback
Tag `pre-P4b2`. No migration, no stored data: reverting the commit restores the bool mark exactly. The class is additive; the bool stays.

## WHAT STAYS OUT
- Any migration, table, column or store method (ASK first, see above); any change to `Limits`, `Budget`, the store contract, tick steps, `release-expired` or its role.
- An automatic release of expired holds by the tick or the runtime role (point 12 of interface (ii)); a "refund" of a counter.
- Prices, price tables, vendor price lookups, any live call to a vendor, any spend; reading vendor billing pages is a build-start task for a person with web access, and every cell not read stays UNVERIFIED on the worst-case side.
- The model gate, its audit codes and the install sites (core-c); streaming; a new provider kind; a retry policy change (which statuses are retried stays as in retry.py:62-63); the README and SECURITY guarantee sentences (they enter only with the step that lands them, plan rule B3).
- Any stage word other than demo, pilot, prod; any project, client or product word in a core type.

## OPEN QUESTIONS (recommended answers)
1. Is a named class worth a change, or is the bool enough? Recommended: build the class only with CT1/CT2; if the lead prefers, CUT P4b2 to a documentation pass on retry.py and the vendor-page task (the mark and the sweep are built).
2. Automatic orphan release by the tick? Recommended NO (keep the audited command). If YES: a migration number is needed (ASK: next free is 0009 after unreleased 0008), a new role, and the point-12 invariant is rewritten.
3. May a person read the vendor billing pages before build start (old-plan-v4-3.md:443, 757) so some cells become `billed` or VERIFIED? Recommended YES, as a separate step; until then all stay UNVERIFIED.
4. core-c: honour the mark on `ProviderExhausted` (request already open)? Recommended YES; it is the largest practical effect for the cap, and it is core-c's file.
