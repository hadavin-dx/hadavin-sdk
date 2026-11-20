# Ticket F, EGM plan-review round 1 of 1 (egm:egm-review-loop through the Skill tool, direct dispatch)

Target: tickets/F-gate-wrapper-body.md (123 lines, draft of 05:23 UTC). Round run 05:24 to 05:30 UTC, 2026-11-20. Both reviewers model 'fable', fresh context, read-only, nothing executed.
| reviewer | status | result |
|---|---|---|
| egm:egm-implementation-readiness (rd) | completed | NOT READY: 6 Blockers, 6 Majors, 5 Nits |
| egm:egm-codebase-details (cb) | completed | NOT CLEAN: 2 Blockers, 9 Majors, 5 Nits; 13 of 15 cited lines VERIFIED, 2 DIFFER |
Round verdict: NOT CLEAN. No second round is run here (ORDER 004 item 3). After merging duplicates: 6 Blockers, 9 Majors, 7 Nits.
Honest note: this file is my condensed record. The reviewers' full texts were returned to the session as messages and are not stored as files; every finding is kept below, none dismissed.

## Blockers
| id | finding (evidence) | resolution |
|---|---|---|
| cb-1-B1 | THE MASK CHECK WOULD REFUSE NORMAL TRAFFIC. (a) Tool inputs are masked leaf by leaf (runmap.py:588-598) but sent as composed JSON (agent_loop.py:574-577; k1b/loop.py:147, 214): `"user_id": "abc123"` passes per leaf and matches a pattern when composed (redact.py:395-399, 428-440, 578-616). (b) The run map grows after each tool result (agent_loop.py:513, 534) while the document and earlier messages, masked with the smaller map, are re-sent unchanged (470-476): a value first found in tool result 2 that also occurs in the document makes step 3 "unmasked". (c) No test puts real producer output through the check | NOT RESOLVABLE BY TEXT ALONE: ESCALATED (E2). Either SPINE masks the composed string and re-masks earlier text when the map grows (agent_loop.py:574-581, k1b/loop.py:211-214), or these hits are a documented limit. For the build: a "no false refusal" test group feeds the gate real producer output and reports what happens; the predicate is in one function so the decision is a small change |
| rd-1-B1 = cb-1-M7 | the check-only function had no signature ("see G ticket" pointed at nothing) | FIXED: ticket G part G0 freezes `runmap.is_masked(text, mapping) -> bool`, raises the RedactionError family, never writes the map; built first |
| rd-1-B2 | Meter is provisional; error types undefined; settle above reserve and settle failure unspecified | ASSUMED for the build, marked in one place: Meter is a local structural Protocol in the module; ANY exception from reserve means no call and is re-raised unchanged; settle may exceed the reserve (cb-1-B2: the estimate is not a bound); a settle failure after a paid call returns the reply and writes an audit row with code settle_failed. Final names come from INTERFACE (ii) |
| rd-1-B3 = cb-1-M5 | the audit row is unspecified: principal, source, result values, the "provider raised" row; replay has a K1bAudit that is not an AuditSink; evals has no sink; agent_loop.py:483, 491 already write llm/chat rows | FIXED IN BUILD: `bind(..., principal=, source=)`; rows: ok / refused (mask_refused, reserve_refused) / failed (provider_error, settle_failed); audit may be None (evals: no sink); the audit write is wrapped so a raising sink never loses a paid reply. To SPINE: delete agent_loop.py:483, 491 with the charge sites; replay passes `audit.sink` |
| rd-1-B4 = cb-1-B2 | `worst_case` had no contract; k1b's worst_case_usd takes a Route object, ignores documents and tools, covers one attempt, and is an estimate (len // 3) | FIXED: `worst_case(route: str, system, messages, tools, documents, output_schema) -> Decimal`, supplied by the installer (resolves the route name, multiplies by max_attempts). Test: a large document raises the reservation. Named to SPINE as needed work; k1b's function is NOT reusable as it stands |
| rd-1-B5 | five open questions change the signature and the tests | ASSUMED for the build (DECISIONS 05:30), lead verdict still needed: Q1 bind keyword `mapping`, held BY REFERENCE (cb-1-M9); Q2 worst case on every exception (cb-1-N3 supports it: a billed reply that fails to parse is a ProviderError); Q3 no `chat` on the unbound gate; Q4 CHANGED to "placeholder not in the map passes" (rd-1-M2, cb-1-M2: refusing would stop every judge, evals and replay call); Q5 no flag, SPINE bypasses on the k1b acknowledge path |
| rd-1-B6 = cb-1-M6 | creating the module turns tests/test_k5_producers.py red until guard/producers.py (SPINE) lists it | PATCH REQUEST requests/1-producers.patch; the test is reported red on my branch until SPINE applies it; removed from this ticket's Done criteria |

## Majors
| id | finding | resolution |
|---|---|---|
| rd-1-M1 = cb-1-M1 | every caller passes `content` as a plain str; adapters send `str(m["content"])` and decode documents with "replace" (llm/common.py:86-100) | FIXED: the gate checks exactly what is sent: `str` content only (anything else is refused), documents decoded as common.py does; T6 becomes a secret inside a tool-result user string |
| rd-1-M2 = cb-1-M2 | Q4 conflicts with the judge, evals and k1b, which have no run map | FIXED (see B5/Q4); those sites bind with an empty map |
| rd-1-M3 = cb-1-M4 | the gate cannot see "abandoned" (k1b runs the call in a daemon thread) | FIXED: the gate settles when its own call returns or raises (worst case on any BaseException, re-raise); an abandoned call is a held reservation for SPINE's sweep; test with a blocked fake client |
| rd-1-M4 = cb-1-M3 | no call site handles GateRefused or meter errors (agent_loop.py:477-484, k1b/loop.py:166-178, evals.py:73; the judge path would record a cap refusal as suspected injection) | TO SPINE: per-site handling table added to the ticket's interface section in the as-built notes; every gate exception carries a stable `code` |
| rd-1-M5 | tests missing for I6, I10, I3 on the pass path, the positive masked case; no concrete fixtures | FIXED IN BUILD (reuse tests/k5_support.py ScriptLLM, llm/fake.py) |
| rd-1-M6 | reservation understated | same as B4 |
| cb-1-M8 | the RunMap cache: `_Redactor._build` writes found originals into `mapping.redact_cache` (redact.py:1007-1009) | FIXED: is_masked passes no cache; test asserts redact_cache unchanged. COST stated: the gate re-scans the document and all messages on every step, up to REDACT_BUDGET_S (6 s) per text: reported to the lead as a performance risk, not measured |
| cb-1-M9 | bind must hold the live map object | FIXED: invariant and test (map grows between two calls) |
| cb-1-M6b | if is_masked is added to CHOKE_FAMILY it must reach redact_text by call graph | FIXED BY DESIGN: redact_text and is_masked share `_scan`; is_masked is not added to CHOKE_FAMILY |

## Nits (all accepted)
T7 literal restored (backslash-u-0-0-4-1); cited runmap lines corrected (views built 401-414, scanned 507-518); problem statement corrected (extract.py sends raw and charges nothing; evals only sums; fifth charge site agent_loop.py:325); BoundGate signature copied from protocol.py; the module has no logger and never uses str(exc) or __cause__ in a row; evidence file listed; phases G0 then module then tests; the "demo only" stage refusal of the k1b flag is new work for SPINE; write_outcome is non-raising in both sinks (chain.py:215-230, local_dir.py:110-124).

## Open after this round (to the lead, see ESCALATIONS.md E2)
1. cb-1-B1: is a composed-JSON hit or a grown-map sweep hit a refusal (then SPINE changes the producers in the same change) or a documented limit?
2. Lead verdict on the assumed answers Q1 to Q5 and on the Meter shape.
3. The per-step re-scan cost (cb-1-M8).
