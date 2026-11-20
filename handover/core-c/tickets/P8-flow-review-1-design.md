# P8: end-to-end design review of gate + guard + redact + runmap (fresh, design, read only, NOT RUN), head f065c628e
Severity is relative to: the gate is not installed anywhere yet (SECURITY.md ~36).
Blocker (both already known and in flight)
1. F1: BoundGate._settle (model_gate ~724) calls meter.settle(res, usd) but real Limits.settle needs agent_id: TypeError -> settle_failed, every paid call stays at its worst case; SECURITY ~210 "TESTED: the gate settles the real cost" and ~30 "No test of the store ran" are contradicted by P3. Fix: adapter side (P7 builds LimitsMeter), fold F1-F3 into SECURITY.md as gap entries. Related: the 3600 s sweep floor drains the daily budget after any unmarked failure (P3-notes ~29); K20 does not say so.
2. F2: the reply is returned unmasked (model_gate ~714); SECURITY has no gap entry; module docstring (~3) defines the guarantee only for what is sent. Fix: a gap entry now; owner decision E25 (mask replies in the gate / caller's put-back / audit only).
Major
3. Spend can be under-counted in three places: a worst case of 0 accepted (model_gate ~390-399, K25; no worst-case function covering tools/documents exists); cost Decimal(0) settled as free (K21, ~158-160); only the last retry attempt settled (K23) and the refused_before_response mark trusted though unverifiable (~350-368). Fix: refuse 0 for non-empty input or a floor from input length; treat 0 with a non-empty reply as cost_unknown.
4. A client can force a permanent refusal of a run: the map only grows, the whole history is re-enforced every call (~756-766) with no memo (quadratic over a run); the shared 6 s CPU budget (runmap ~1052-1055) covers the snapshot build and every message; K41 measures a 262,144-char `curl -u ` text at 4.5-5.4 s alone; planted values (`the quick brown fox`; a value equal to a tool name, K14; the 4,096 head-hit cap) refuse forever. Fix: per-message result cache keyed by map version; a quarantine/drop path for the offending history message.
5. One regex scan in the redactor is not interruptible and the docs disagree on its cost: gate docstring (~108-109) 256 KB of `a` + 500 planted values ~7 s; K13 "NOT REPRODUCED, 0.47 s"; K51 7.2-7.5 s. Reproduce and pick one number; slice the scan if real.
6. The safety net is not independent of the sweep: the checker is the same `_Redactor` machinery (runmap ~1339-1340, 1587). Add an independent plain-substring/Aho-Corasick final check.
7. The audit row is lossy and can fail silently: failure swallowed by contextlib.suppress (~880), audit=None accepted (~874); no masked flag or route (K31); reserve_interrupted/reservation_invalid rows lack object_ref; KeyboardInterrupt inside _settle leaves no row (K16). Fix: count dropped rows and surface it.
Nit: 8 the guarantee is stated in too many places (gate docstring ~190 lines, enforce_map docstring, K-items) and the first sentence over-promises vs ~60 stated limits; drift: docstring says CPU deadline but K13/EnforceBudget.check use CPU and wall; runmap ~995 comment says NotSettled text kept but the code raises it with none (~1186): one "promised / not promised" table in SECURITY.md, docstrings point to it. 9 K20/K42 premises stale (core-b's ProviderError now carries refused_before_response; model_gate ~362-363 docstring still says unset). 10 `<<TOOL RESULT>>` framing is an in-band trust marker (64 tokens per message read, ~416; invariant "assistant line first" only in _ASSISTANT_CALL.match ~445, ~819).
Naive-reader summary: not explainable in one page today; shortest honest sentence: "the gate replaces values the redactor already registered, in message content and documents only, and refuses the call if a raw copy or a decoded or partial copy of a secret remains." Everything else is a stated limit.
Not read: redact.py beyond grep, textnorm, producers beyond grep, SECURITY ~511-565, runmap 1-955 and 1355-1550, all tests.

## Ledger (owner / fix time) set by core-c
| # | item | owner | next step / fix time |
|---|---|---|---|
| 1 | F1 meter adapter | core-c (P7 running) | LimitsMeter on wip/cloud-core-c/f-findings; core-b confirms the call shape; today |
| 2 | F2 reply masking | OWNER decision (E25) | options a/b/c in ESCALATIONS E25; strict xfail pins today |
| 3 | spend under-count (0 worst case, Decimal(0), last attempt) | OWNER decision + core-b (worst-case function) | needs the worst-case cost function (core-b lane) |
| 4 | permanent refusal / quadratic history | core-c builder after the current merges | per-message cache keyed by map version: next package (G14) |
| 5 | scan cost numbers disagree | core-c | reproduce at idle (P10), pick one number |
| 6 | independent final net | core-c, OWNER decision on scope | candidate G15: plain-substring net over secret values |
| 7 | audit row loss | core-b (audit sink) + core-c (gate counter) | counter of dropped rows: G14 |
| 8-10 | docs drift, stale premises | core-c | after P7 merges: fold F1-F3 and the promised/not-promised table into SECURITY.md (docs change, no review round) |
