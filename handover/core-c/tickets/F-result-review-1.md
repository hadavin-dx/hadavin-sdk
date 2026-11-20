# Gate (step F) RESULT review, EGM round 1 (egm:egm-review-loop through the Skill tool, direct dispatch)

Target: src/hadavin_sdk/guard/model_gate.py and the run map functions at commit f16d48e, read from a fixed plain-file snapshot. Reviewers got the code, the ticket (spec) and the raw evidence file, not my verdict. Round 06:22 to 06:33 UTC, 2026-11-20. Both model 'fable', read-only. NOTHING was executed by either: every scenario is "by reading" and is being reproduced by the gate builder where it is in my files.
| reviewer | status | result |
|---|---|---|
| egm:egm-design (dz) | completed | NOT ready to install: 1 Blocker, 9 Majors, 9 Nits |
| egm:egm-codebase-details (cb) | completed | no Blocker in the gate body; 9 Majors, 10 Nits; two Majors break numbered guarantees (I14, I15) |
Round verdict: NOT CLEAN. After merging: 1 Blocker, 14 Majors, 14 Nits. None dismissed. The reviewers' full texts came back as messages; this is my condensed record.
Both reviewers agree on what is SOUND: no path calls the provider after a failed enforce or reserve step or with the caller's original text; at most one settle on every path; a raising sink or settle never loses the reply; UnmaskedInput carries no text; the caller's lists, dicts, map and cache are not written; BoundGate has no mutable state; the map write without clear() is a superset for a single writer.

## Blocker
| id | finding | state |
|---|---|---|
| dz-B1 = cb-M5 | `bind()` without `mapping=` skips the enforce step with no trace, and core-b's install draft binds the run loop and the judge that way (draft lines 31, 69). A forgotten keyword silently voids the guarantee sentence | ESCALATED E6 item 1 (lead decision: required keyword + explicit NO_MAP). Non-breaking half being built: no-map calls are marked in the audit row (D1) |

## Majors
| id | finding | state |
|---|---|---|
| dz-M8 = cb-M1 = lead MJ2 | enforce_map is not idempotent when an identifier is glued to a shorter secret (three independent reads) | BEING FIXED: sweep to a fixed point with a small cap |
| cb-M2 | FALSE REFUSAL: the gate applies the redaction size cap to already-redacted text, which is longer than its input; a document near the cap made of short values is refused on every call (breaks I15) | BEING FIXED (E1): own larger cap for the enforce step + near-cap test |
| cb-M3 = dz-N7 | a value straddling the edge of a placeholder written in the same pass corrupts the token (`<SECRET_1<SECRET_2>`); no leak, wrong put-back | BEING FIXED (E2) |
| dz-M7 = cb-M4 | the enforce step has no time budget and an attacker-triggerable slow path (one planted token-piece value drops the cache for the whole run; cost per call = messages x map size) | BEING FIXED: lead m-new-1 + D9 (one snapshot and one redactor per chat call; budget; numbers measured) |
| dz-M4 = cb-M6 | `worst_case` is trusted blindly (0, negative, NaN reach reserve), and no function in the tree fits the six-argument signature: core-b's README helper and k1b's function both raise TypeError when passed in | BEING FIXED in the gate (D2: finite Decimal >= 0 or refuse, own codes). The signature is for core-b: ORDER 016c item 13 gives core-b the formula; a contract test with the real helper is needed at install |
| dz-M9 = cb-N2, N4 | unstated limits: the sweep is case-sensitive; ANSI- or NUL-split copies pass; extra message keys, role and output_schema are forwarded untouched; the "backslash-encoded copy" pin does not exist | BEING FIXED (D7): limits stated and pinned |
| cb-M9 | both thread tests cannot catch the race they name (the client is released before any thread blocks; the clear() test only catches a literal clear) | BEING FIXED (E3) |
| dz-M6 | UNVERIFIED: untrusted text can plant a "secret" equal to a word of the trusted tool-result marker; the gate would then rewrite the markers in later messages | BEING REPRODUCED (D6); fix is a design decision: E6 item 6 |
| dz-M1 | `Reply.cost_usd` defaults to Decimal(0): an adapter that sets no cost is settled at 0 | ESCALATED E6 item 2 (models.py / adapters: core-b) |
| dz-M2 | a call that succeeds after retries settles only the last attempt | ESCALATED E6 item 3 (adapters: core-b) |
| dz-M3 | every failed call holds worst case x attempts until the sweep; three unbilled failures can stop an agent for the day | ESCALATED E6 item 4 (needs request 2 answered before install) |
| dz-M5 | reserve-side failures (no call, nothing booked) cannot be told from client-side failures (worst case booked) | ESCALATED E6 item 5 (shared contract) |
| cb-M7 | the gate conflicts with every call site as it is today: see the per-site list below | FOR CORE-B (install); copied below |
| cb-M8 | test doubles: FakeLLM and ScriptLLM keep the messages list by reference (each step is now its own list); FakeLLM keys recordings on the document bytes, which the gate can change within a run, giving UnknownRecording (a KeyError, run left in WORKING) | FOR CORE-B (install): grep tests for `calls[`, `sent[`; document bytes are not stable across the steps of a run |

## Nits (accepted; in the builder's list unless marked)
Reservation id not checked (D3); overshoot dropped (D4); a raising worst_case is mislabelled reserve_refused (D2); AuditEvent built inside suppress so bad bind arguments drop every row (D5); docstring claims more than the code (D8); `enforce=` injection, AUDIT_CODES and rule (b) exist mainly for tests (kept: core-b's draft passes a function there; AUDIT_CODES becomes enforced, E4); single-writer rule for the run map stated (D9); same original under two placeholders follows the weaker rule (E5); limit 5 wording (E5); `_within_cap` outside the try (E5); tests that cannot fail and mutant gaps (E4); observability: the ok row does not say whether anything was replaced, and has no route or model (NOT DONE: needs a lead decision on audit fields); on KeyboardInterrupt the gate does sink I/O before re-raising (NOT DONE: stated); `is_masked` has no caller (deleted by lead decision m7).
Citations: the reviewer verified 20 of 26 cited facts; the 6 that DIFFER are stale numbers in ticket F's AS BUILT section (269 lines is now 347; 12 mutants is now 27; redact.py line numbers moved): being corrected by the builder's ticket update.

## For core-b (install), per call site (reviewer cb-M7, by reading; line numbers at f16d48e)
- runtime/agent_loop.py:470-486 (run loop): bind with `mapping=rmap` (the live RunMap of line 397) and `principal=run.principal_id`; supply `worst_case`; line 477 catches ProviderError only: UnmaskedInput, SpendRefused, KeyError and store errors would leave the run in WORKING (map kill_switch to STOPPED as line 253 does, budgets to limits codes; decide limits_unavailable and bad_amount); delete 485-486 (the store adds run cost at settle: keeping add_cost double-counts); line 483 becomes a second `llm/chat failed` row beside the gate's; 491-493 give `stopped` beside the gate's `ok`; every successful call now writes an `llm/chat ok` row where none was written: tests that count audit rows change.
- agent_loop.py:321-327 and 650-652 (judge): delete the charge and add_cost, bind the judge with no map.
- guard/judge.py:72 and guard/injection.py:211-227: a budget stop or gate refusal is turned into `guard_unavailable` (reported as a guard failure): map it.
- k1b/loop.py:94, 157-179, 206: `run_case` promises "never raises" but catches only timeout and provider errors; Budget has no reserve, settle or lock; lines 169-170, 179, 206 go; the gate runs inside the daemon thread, so an abandoned call that returns late IS settled and audited from that thread; k1b's audit sink uses write_intent and domain k1b, the gate write_outcome and domain llm.
- k1b/replay.py:136, 152, 166, 227: Budget type, route_prices, the meaning of run_usd.
- evals.py:73, 109: no try around chat: a refusal is a traceback; inside judge.qualify a cap hit becomes failed judge cases.
- extract.py:47: still present and unwrapped until deleted. guard/producers.py: no row for the gate (requests/1-producers.patch).
- Stale lines in the install draft: line 7 (reserve argument order), line 149 H1 ("still gets a settle": the rule now says no settle), line 150 H2 (tests the withdrawn check).
