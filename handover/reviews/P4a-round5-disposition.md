# P4a round 5 disposition (applied in `tickets/P4a.md` REVISION 6)

Written 2026-11-05 about 20:00 UTC (2026-11-06 about 01:30 IST). Source: `P4a-round5-resolve.md` (17 table rows, 21 finding ids, 4 merged groups; every row PROPOSE FIX; CONTEST, DECLINE and ESCALATE: 0). Line numbers are those of revision 6 and move when the file changes. "Applied" means the text now says what the resolve names; nothing was run (text only).

| Id | Answer | Where in `tickets/P4a.md` rev 6 |
|---|---|---|
| ADV-R5-1 | applied (home of `round_cost_up` stated PENDING, one lead check) | Answer first 3 (line 37); checklist 4; UNVERIFIED; PL18 note |
| COR-R5-1 | applied (merged with ADV-R5-1: P4d rev 8 line 71 says `llm/common.py`, rev 9 moves it) | Answer first 3; Notes for P4d; UNVERIFIED |
| ADV-R5-2 | applied (hard gate leaves P4a-1 Done; lead check plus relay to P4b1 rev 2) | Done line of P4a-1; Notes for P4b1; checklist 0 |
| ADV-R5-3 | applied (chained request-2 failure keeps today's run behaviour; admission of the wrong claim) | "What changed" para 1; Answer first 8 CONTROL FLOW; P4a-1 agent_loop expression; P4a-2 `k1b/loop.py` branch; rows U10b, C13(j); mutants a1-23, a2-38; PL35 |
| COR-R5-6 | applied (merged with ADV-R5-3: same cause check) | same places as ADV-R5-3 |
| ADV-R5-4 | applied ("never under-charge" and "safe direction" reworded) | Plain words; Answer first 8; P4a-2 `k1b/loop.py` paragraph |
| ADV-R5-5 | applied (Gemini thoughts-only reply accepted, output = thoughts) | P4a-1 Gemini rule; row U3; mutant a1-12c; PL36; V25 |
| COR-R5-7 | applied (merged with ADV-R5-5) | same places |
| ADV-R5-6 | applied (cuts: `Budget.charge` check, C13(i), a2-35, a2-35b; worst-case argument validation, a2-31; C14(a) row) | CUT para; Answer first 2/4; P4a-2 `k1b/loop.py`; C7, C13, C14; V20, V21, V23; PL37 |
| ADV-R5-7 | applied (cuts: `Reply.thinking_tokens`, C9b, a2-13c; C15 pin) | interface table `Reply` row; P4a-2 `models.py`; C9; V17, V22; PL28 text; PL37 |
| ADV-R5-8 | applied (U4b(a) states what the temporary demo edit books) | row U4b(a) |
| ADV-R5-9 | applied (`RecordingLLM` forwards both declarations; stub inventory) | P4a-2 stub bullet; row C13(h); mutant a2-37c; Rules stated once |
| COR-R5-5 | applied (merged with ADV-R5-9) | same places |
| ADV-R5-10 | applied (reason for rejecting the narrow rule corrected: `with_retry` chains the last error only) | Answer first 8; PL31 |
| COR-R5-2 | applied (`P4b2.md` lines 48, 66, 305 named) | Rules stated once (hot files); Notes for P4b2; checklist 3 |
| COR-R5-3 | applied (layer (c) is a REQUIREMENT on P4b2 checked by the lead) | Answer first 1; Notes for P4b2; checklist 3 |
| COR-R5-4 | applied (header states orders 1-8; status of every PENDING LEAD item) | line 3 header; PENDING LEAD heading and per-item STATUS |
| COR-R5-8 | applied (recount wording) | checklist item 5 |
| COR-R5-9 | applied (U14 names a1-22) | row U14 killers line |
| COR-R5-10 | applied (`_chat` and `chat` cites) | P4a-2 `openai_compat` bullet; Verified facts |
| COR-R5-11 | applied (canary written `<CANARY>`, built from parts) | row U3b |

## Counts
- Ids: 21 (ADV-R5-1..10 = 10, COR-R5-1..11 = 11). Applied 21, contested 0, declined 0, escalated 0.
- Resolve rows: 17. Check: 21 ids minus 4 merged duplicates (COR-R5-1, COR-R5-6, COR-R5-7, COR-R5-5 folded into ADV-R5-1, ADV-R5-3, ADV-R5-5, ADV-R5-9) = 17.
- Disposition table rows in this file: 21 (one per id).

## Where I extend or read differently (not contests)
1. The `agent_loop.py` edit makes P4a-1 a new editor of that file; F6 lists P4c and P5c only. Logged as PL35 for the lead.
2. The "old code, new data" evidence row had to be re-keyed (zero `cache_read_tokens` key) because `thinking_tokens` is cut.
3. The `agent_loop.py` rule applies only to a `UsageMissing` whose cause is a `ProviderExhausted`.
4. Revision 5's "at most once per run" was false for the exhausted branch (it ends the case, not the run); corrected.

## Recount (revision 6; counted by grep of the tables)
- Mutants P4a-1: 36 rows (34 + a1-12c + a1-23). P4a-2: 40 rows = 42 - 4 (a2-13c, a2-31, a2-35, a2-35b) + 2 (a2-37c, a2-38); `a2-11a-e` stands for 5, so 44 single mutants. Total 36 + 44 = 80.
- Test rows: P4a-1 21; P4a-2 16; total 37.
- v1.1 rows: V1-V25 (V20-V25 new). PENDING LEAD: 1-37 (35-37 new).
