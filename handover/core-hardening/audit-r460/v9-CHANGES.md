# v9 changes: where every v8 finding went (2026-11-16 UTC)

Files: `CORE-PR-HANDOFF-v9.md` (spend track, "SP" below), `CORE-PR-HANDOFF-v9-other-tracks.md` ("OT"). Section numbers are those of the file named. "Fixed" means fixed **in the design text**; nothing is built, run or reviewed (section 0 of SP). Exceptions are named as impossible-now (IN), needs-owner (NO) or needs-third-party (N3).

## The shape change (answers the v7 zoom-out and the lead's Q33)
v8 (722 lines, 12 PRs, three new tables, two triggers, an advisory lock, an adjust role) became: one spend hand-off of **three PRs** (S-1 window end and one shared price formula; S-2 reserve per attempt and settle on the existing `add_spend` and `Limits`; S-3 the provider-side limit, owner action) plus a table of later PRs that each carry a named trigger (SP 5.7). Everything not spend moved to OT.

## v7 zoom-out (`review-handoff-v7-zoomout.md`)
| Id | Where fixed |
|---|---|
| B1 existing meter and `k1b/loop.py:115-122` never read | SP 0 item 4 (read), SP 2 F1-F3, SP 3 extend-or-replace evidence (verdict: extend the protocol, share one formula), SP 4 ladder |
| B2 D5 made a blocking lead decision against Q28 | SP 1 (money exception, dated) and SP 10 (D5 OWNER-OPEN, non-blocking, default ships with the first new table, exact owner question, POST-DEMO) |
| M1 smaller first step, no migration of money columns | SP 5 (S-1, S-2, S-3). One small migration is added (`CHECK usd >= 0`, SP 5.5 item 1); it is **my addition** and the lead can veto it: without it the negative-total class (security major 1) is open |
| M2 ledger too big | not in step 1; SP 5.7 L-1 and L-2 each need a trigger and the lead's yes |
| M3 only about 8 decisions block the first build | v8's D1-D30 table dropped; SP carries D5 only; OT O-1 carries the non-spend ones |
| M4 7 of 12 PRs have no spend content | split into OT (Q33 b). Conflict: the lead's wording says drop those with verdict NOT-NEEDED or DUPLICATE; the brief says carry unchanged. Followed the brief; per-PR verdicts are not supplied; module verdicts are in OT O-0 item 2 |
| M5 over-claims ("cannot" without Postgres, import graph, "no unmetered spend") | SP 0 items 2 and 6, SP 6 (no "no unmetered spend" sentence; table of every paid path), SP 8/E0-S1-5 (import graph program rerun, it found and fixed a real cycle, see below) |
| M6 PR-2 first though `extract()` has no caller; retry-storm test first | OT O-0 item 2 (stated); E0-S2-4 starts with the retry storm; PR-2 is in OT, no longer first in a money path |
| N1-N4 | history trimmed to SP 0 item 5; code detail kept only where a reviewer asked for a signature; D24 and indexes removed with the ledger; `limits correct` CLI removed (L-2) |
| "must exist before first build" list | SP 10 last paragraph: the lead's yes, D5, S-3 owner step (POST-DEMO), recorded replies, golden set |

## v8 security review (`review-handoff-v8-security.md`)
| Id | Where fixed |
|---|---|
| Major 1 old tables writable, negative usd wipes caps | SP 5.5 item 1: migration `0006` `CHECK (usd >= 0)` on both old tables, memory-store parity, pre-flight count of negative rows. Residual (a writer can lower a total to zero) stated; bound is S-3. Postgres behaviour UNVERIFIED (E0-S2-2) |
| Major 2 failed finish never retried | SP 5.3 "Failed settle": the reservation stays booked (over-count, fail closed), no blind retry because settle is not idempotent; the over-count is stated and the idempotent settle with a reservation id is L-1 with the exact trigger (any `spend_settle_failed` in a live window) |
| Major 3 Python lock stalls | SP 5.5 item 2: `lock.acquire(timeout)` and transaction-local `lock_timeout`, both mapped to a refused call; separate connection is L-3 with a measured trigger (the v8 "measure first" trigger was called too late; here a live-window `55P03` or a spend call over 1 s) |
| Major 4 direct write skipping the lock protocol; advisory-lock attack | SP 5.5 item 4: no advisory lock, no `direct` rows, so the attack does not exist in step 1; what a runtime-role session can still do (hold a row lock) is bounded by `lock_timeout` and role-level timeouts (UNVERIFIED, E0-S2-3 f) and by S-3 |
| Major 5 D29 per-agent roles vs one connection | SP 5.5 item 5: cannot work on one connection; dropped; L-4 (one store per agent role) only for a client that distrusts the agent process |
| Major 6 tier depends on a person noticing | SP 5.1 items 1-3: required `price_basis`, `tiered` refused, known-tiered model prefixes require `max_input_tokens`, cached-token guard test; cached tokens outside the input count marked UNVERIFIED |
| Nit day and ts separate | day taken from the reservation's own ticket day and the gate's clock; no `ts` argument exists in step 1 (SP 5.3) |
| Nit window uses caller clock (skew) | SP 5.2 "Exposure": host clock only, stated; database-time comparison is L-1 with trigger |
| Nit relief of a call in flight | no relief in step 1 (L-2); when it exists it needs a minimum age above socket timeout times attempts: recorded in SP 5.7 L-2 row by reference to this line |
| Nit "400 means not billed" as fact | SP 5.3: v9 releases nothing after a request was sent; per-vendor billing UNVERIFIED; release is L-6 with invoice evidence |

## v8 readiness review (`review-handoff-v8-readiness.md`)
| Id | Where fixed |
|---|---|
| Major 1 fake-kind window mechanism | SP 5.2 "Fake kind": `build_gate(cfg, clock, limits)` reads `cfg.backends.llm.kind`; fake gets no gate and no window; test E0-S1-3 |
| Major 2 guardrail gate attribute, who raises | SP 5.6: `window` argument on `GuardrailDetector.__init__`, `make` reads `deps.gate`, `ALLOWED["detector"]` gains `gate`, `check` raises `SpendRefused`, `injection_check` re-raises; nobody raises `ConfigError` |
| Major 3 census test owners and head greenness | SP 6 last paragraph (S-1 owns C1, C2 and the import test; S-2 owns C3, C4); S-2 stacked on S-1, each head green alone; the `cli.py:150,221-222` sites move to S-1 |
| Major 4 `_retry` closure signatures | SP 5.3: `_retry(self, call)` unchanged, `attempt()` closure, `CallGate.reserve/settle/keep` signatures, `_CALL` contextvar set in `chat`, `_retry_args()` helper |
| Major 5 one owner of `max_call_usd` | SP 5.4: `Limits.call_cap`, `Limits.scope`; runtime and CLI both call it |
| Major 6 `_REASON_TEXT` keys | SP 5.4: exact keys listed; `_wall_stop` builds `limits.<code>` or the bare code |
| Major 7 E0 items runnable | SP 7.2 and OT O-7: each item has a command, an output file, a pass rule and an author PR; no circular dependency (R and G wait on their evidence items, which are authored by themselves and run on the old tree first); one command each for the import graph and the gates |
| Nit line 15 `SpendBookkeepingError` stale | removed: the word does not appear in v9 (grep count in `raw-greps-v9.txt`); pricing failures are "keep", SP 5.3 table |
| Nit cites: Money `config.py:47`, `_money` `:40-44`, `_SAFE_CREATE` `migrate.py:80-85`, migrate parser `cli.py:97-105` | SP 2 F11 and F12 use `:47`, `:40-44`, `:80-85`; the migrate parser cite is not used in v9 (CLI parser change is not part of step 1); citation program: `raw-cite-check-v9.txt` |
| Nit `res-` and `dir-` id forms | no reservation ids in step 1; when L-1 ships, ids come from `models.new_id` (`res-<hex>`); noted in SP 5.7 |
| Nit `bandit -ll` without target | SP 7.2 E0-S1-1 and OT E0-O1: `bandit -q -r src demos -ll` (`ci.yml:119`) |
| Nit module-prefix rule dot boundary | the module-prefix test-double rule is gone with `MeteredLLM` and `classify_llm` (SP 5.2: no double detection; a gate-less network kind is refused at build); nothing to bound |
| Nit `Reply.cost_usd` equals sum of settles can fail with tiers | SP 5.3 "Reply": equal for a flat price (test E0-S2-4), `tiered` refused |
| Nit "six-part" vs seven in 4.3 | v8 4.3 removed; SP 5.1 lists the settings once |
| Nit memory store `finish_spend` must update run cost | no `finish_spend` in step 1; the run cost path is the runtime's `store.add_cost` (SP 5.4, "The run's own cost") |
| Closure leftovers: `cli._migrate` fourth argument, `model_copy` nulls for adjust dsn, judge test `model` | no new database role or setting is added in step 1, so none apply; recorded as not-applicable, not as fixed |

## v8 contradiction review (`review-handoff-v8-contradiction.md`)
| Id | Where fixed |
|---|---|
| M1 `SpendBookkeepingError` | as above |
| M2 unread `agent_loop.py` 345-541 marked read | I read 340-545 this pass; SP 0 item 4 and SP 2 F7 mark exactly what was read; the handler design in SP 5.4 names the real locals |
| M3 "no unmetered spend" | SP 0 item 6 and SP 6: not claimed; the guardrail is not metered and the gate is not closed; direct provider calls are not stoppable here; L-5 and S-3 are the next steps |
| M4 limitations deferred with a trigger | each is fixed, or is an exception: forged agent id and database-enforced cap: IN/L-4 and S-3 stated plainly (SP 5.5 items 4-5); settled 0 hides spend: replaced by keep (SP 5.3); Python lock: bounded (SP 5.5 item 2), second connection has a measured trigger; channel down: failure is logged at error level and counted in the audit row, a card is not promised, said so (SP 5.4). Items that need the owner or a third party are marked NO or N3 |
| M5 owner tasks on the take day, Q24, Q30, Q31 | SP header, 7.3, 10: every owner step POST-DEMO, needs a new owner yes, no date, no second account |
| M6 D5 vs Q28; money exception not named | SP 1 and 10: D5 OWNER-OPEN, non-blocking, default ships; the `Decimal` fields are named as a dated exception with an exit |
| M7 owner-facing terms undefined | SP 1 defines call, attempt, spend record, reservation, settle, keep, release, wall, window end, gate, scope, "the demo" vs the `demo` stage, before first use; the word "relief" is not used in step 1; SP section 0 uses them only after section 1 is referenced in the header (plain sentences in section 0) |
| M8 adjust role grants contradiction | no adjust role in step 1; L-2 states it must ship its own grant table and over-breadth line |
| Nit D26 line mismatch, "if it exists", "changed in v7" header | v8 decision table not carried |
| Nit finish "never raises" vs BaseException | SP 5.3: `keep` on `BaseException`, re-raised unchanged |
| Nit `begin` raises only SpendRefused vs naive-clock ValueError | SP 5.2 states the naive-clock ValueError is a programmer error |
| Nit alarm vs rule (ii) | v8 rule dropped with the ledger |
| Nit 23505 vs ON CONFLICT DO NOTHING | no unique-final rows in step 1 |
| Nit outcomes stated as fact though "designed to" | every behaviour sentence is under "specified, unverified" (SP 0 item 1); Postgres items carry E0 ids |
| Nit NUMERIC(24,8) vs config 9 decimals | no new `NUMERIC` money column; new table uses nano-dollar BIGINT (9 decimals) by default, SP 1 |
| Nit "never/cannot" without a named test | each remaining "never/cannot" names the test in the same sentence or was removed |
| Nit "not searched" at v8 288 and 546 | greps run: `raw-nit-greps-v9.txt` (callers of `add_spend`: positive amounts only, so the new `CHECK` conflicts with none; configs with a non-fake kind: six test sites listed in SP 5.1 item 5; no demo or doc site; `environment: dev` sites: two) |
| Nit CH says M-G test "done" but only specified | no such claim in v9; every test is "specified" |
| Nit off-by-default control presented as fix | D29 dropped; not claimed |
| Nit adjust role has no over-breadth line | SP 5.7 final paragraph: step 1 adds no identity; L-2 and L-4 must ship the line |
| Nit times UTC only | UTC and IST wherever a clock time or day boundary appears (SP 1, 5.2, 5.4, 7.2 E0-S1-3, 7.3) |
| Nit words with several meanings | defined in SP 1; "the demo" and the `demo` stage kept apart; "double" is not used |

## v8 citation check (`review-handoff-v8-citation-summary.md`, `evidence-handoff-v8-independent/00-TABLE.md`)
| Finding | Where fixed |
|---|---|
| Money cite `config.py:47`, `_money` `:40-44` (wrong 4 times in v8) | SP F11, SP 2 and 1: `:47`, `:40-44`; the extraction program `cite_check_v9.py` resolves every cite (104 in SP, 72 in OT, none missing or out of range; `raw-cite-check-v9*.txt`) and I checked each anchor flag by eye (the flagged ones are lists or ranges, not wrong lines) |
| Import-cycle counts: 3 with `TYPE_CHECKING`, approvals set has 4 modules | SP 8 section 4.2 note and `raw-import-graph-v9.txt`: today 1 cycle run-time only (3 modules), 3 cycles counting type-only imports (the approvals set has 4 modules incl. `approvals.cards`), reported for both countings |
| Program planned-edges differs from the 4.2 table | `import_graph_v9.py` reads the planned-edges table **from the document** (marker lines), so the program cannot differ from the table; `--diff` compares it with the future test file (not run: the file does not exist until S-1; E0-S1-5 runs it) |
| `test_licences_are_proprietary` fails | not caused by this work (10 LICENSE copies under `handover/promotion-inputs/`, a lead-branch artefact); not touched (outside my folder); needs the lead |

## Found by the v9 programs (not in any review)
- **The import-graph program found a new cycle in my own first table** (a type-only import of `config` from `llm.spend` joined the existing `config` / `registry` / `deferred` / `replay_records` cycle, counting `TYPE_CHECKING` imports). Fixed in the table (`llm.spend` and `limits` import `config` neither at run time nor for typing; `llm.spend` defines a small `Protocol` for a priced route). First run kept as `raw-import-graph-v9-first-run.txt`.
- **F15 was wrong in my first draft** ("no thinking hits in `llm/*.py`"): the grep found two comments; `gemini.py:98-100` adds `thoughtsTokenCount` to the output count. Corrected in SP F15.
- **Config sites** (SP 5.1 item 5): six test sites build a non-fake kind and would fail under the new required fields; listed so S-1 edits them.
- `tests/test_k5_tools.py:723-731` and the `0.00225` cost tests are expected to pass unchanged; unverified (E0-S2-1).
