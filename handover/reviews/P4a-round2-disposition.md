# P4a round 2 disposition (author: revision 3 of `handover/tickets/P4a.md`)

Written 2026-11-05 (UTC about 18:10, IST about 23:40). Applies `P4a-round2-resolve.md` one decision per finding. Nothing in revision 3 was run (text only); every cite I kept was re-read on ce70eb5, every other claim is marked UNVERIFIED in the ticket. Line numbers below are lines of the new ticket file at the time of writing.

Counts: 25 finding ids (ADV-R2-1..14, COR-R2-C1..C11). Applied 25 (of which 3 applied with a flagged interpretation: ADV-R2-7, ADV-R2-9 and COR-R2-C6 share one, see "Things the lead should check"; 4 applied as a cut or a moot). Contested 0. Declined 0.

| id | status | where in the ticket | what was done |
|---|---|---|---|
| ADV-R2-1 | applied | Answer first 2 (line 25); P4a-1 and P4a-2 "Depends on" (110, 194); PENDING LEAD 1 | One sequence: P4a-1, P4a-2, P4b1-a, P4b1-b in one sitting, nothing between; rule "no live provider call until P4c-2 has merged". X1 is now a local stub row in P4a-1 (honest scope: it tests the stub contract, not the real wrapper). |
| ADV-R2-2 | applied (narrowed as resolved) | Verified facts (line 44); Notes for P4c (99) | Claim corrected: a billed but unusable judge call books 0. The wiring is P4c-2's; one note row for P4c-2. Nothing P4a edits. |
| ADV-R2-3 | applied | P4a-2 Interface `k1b/loop.py`; test row C13; mutants a2-24a/b, a2-25 | New `except UsageMissing` before `except ProviderExhausted`, charges the worst case, run ends "aborted". "k1b diff empty" dropped from P4a-1. |
| ADV-R2-4 | applied (cut) | "What changed" (9); v1.1 row V11; P4a-2 mutation table "Removed" line | Cache prices, cache cost, cache fields on `Reply` and their rows and mutants cut. Refusal of any non-zero cache class kept (P4a-1 U2b, P4a-2 C3, C2-fb). |
| ADV-R2-5 | applied (cut) | v1.1 row V2; Answer first 5; PENDING LEAD 24 | `max_prompt_tokens`, its row and mutants removed; plain statement that tiered-price models are not priced. |
| ADV-R2-6 | applied | Interfaces table (94); Notes for P4b1; P4a-2 C7(d); C12 | `request_bound` and `estimated_worst_case_usd` kept, two consumers named (P4b1-b coupling row, k1b charge); `askdata/meter.py` edit dropped from the file list. |
| ADV-R2-7 | applied (deviation flagged) | P4a-2 Interface `k1b/loop.py`; C13(b)(c); a2-24a | The abandoned-call charge uses `requests=request_bound(llm)`. The resolve wrote `getattr(llm, "request_bound", 1)`; I made `request_bound` a function (`request_bound(llm)`) so P4b1-b and k1b share one definition. Behaviour is the same (2 for OpenAI-compatible, 1 otherwise). Two-request route row and `requests=1` mutant added. |
| ADV-R2-8 (= COR-R2-C3) | applied (cut) | v1.1 row V13; P4a-2 "Removed" line | C11 and mutant a2-17 cut. C5 cut with row V14 (no mutant left without a killer). |
| ADV-R2-9 (= COR-R2-C6) | applied (interpretation flagged) | Rules stated once (65); Interfaces (91); P4a-1 Interface `common.py` | Helper home `llm/common.py`; hot-file orders: `config.py` P2a-1, P4a-2, P4b1-a, P4b2-b, P5b3, P5c, P6a (P6b1 raised as PENDING LEAD 27); `fake.py` P4d-a2-i, P4a-1, P4a-2. See flag 1 below. |
| ADV-R2-10 | applied | Answer first 6; v1.1 row V12; PENDING LEAD 25 | Zero-priced servers unusable in v1, `k1b/replay.py:85-90` interplay stated, so "price 0" is not a remedy. |
| ADV-R2-11 | applied (narrowed as resolved) | P4a-1 row U8; mutants a1-7 (U8 added), a1-11b, a1-11c | Guard covers `or`, `.get(<token key>, <default>)` and `not <token>`; `max_tokens` allow-list; no ternary form. |
| ADV-R2-12 (= COR-R2-C8) | applied (cut) | P4a-2 Interface `models.py`; C9 | `Reply` validator dropped; `usage` property and the one backstop in `Usage` (P4a-1 U13) kept. |
| ADV-R2-13 | applied | P4a-2 C8; Source field of P4a-2 | Negative-zero row uses the string "-0" and says YAML `-0` loads as 0; Source says MANIFEST ids none (UNVERIFIED that the Intake copy has none). |
| ADV-R2-14 | applied | Rules stated once; Interfaces (94); P4a-2 C7(d); PENDING LEAD 7 | Multiple is the request count of one call (2 OpenAI-compatible, 1 otherwise), not times `max_attempts`; a cap sized for N calls admits N/2 for that kind. |
| COR-R2-C1 | applied (moot) | v1.1 row V2 | `StrictInt` question disappears with `max_prompt_tokens`. |
| COR-R2-C2 | applied | P4a-2 Interface (Anthropic nested cache rule); C3b; mutant a2-8 | Absent or null `cache_creation` accepted; present non-object refused; rows use the two existing fixtures (`text.json:20-23`, `tool_call.json:25-28`, re-read). |
| COR-R2-C3 | applied | see ADV-R2-8 | |
| COR-R2-C4 | applied (relay) | "What the lead needs to check" item 4; Notes for P4b1, P4b2 | P4b1 and P4b2 must be re-read and changed by their owners (tier language, monotone rule, price-date check, W2, `request_bound` coupling row). The P4b2 line cites `:48,66` are reviewer-reported and UNVERIFIED by me (I did not re-read them). |
| COR-R2-C5 | applied | P4a-2 Interface `common.py`; C12 | New `reply(route, *, text, calls, usage, stop, started, facts=<empty>)` stated and pinned. |
| COR-R2-C6 | applied | see ADV-R2-9 | |
| COR-R2-C7 | applied | P4a-2 C3d; mutant a2-20b | (b) and (d) moot; (c): the redundant regex was replaced by equality with `standard`, with a mutant for lenient comparison. |
| COR-R2-C8 | applied | see ADV-R2-12 | |
| COR-R2-C9 | applied | UNVERIFIED section (P4a-2) | Worded as "25 constructions plus the class line"; not each read. |
| COR-R2-C10 | applied | "What the lead needs to check" item 1 | Cites re-read: `config.py:40-44`, `agent_loop.py:432-439`, `llm/common.py:193, 206`, `bedrock.py:172-176`; stale `registry.py:105` corrected to `:106,116-118`. |
| COR-R2-C11 | applied | P4a-1 Interface (Bedrock) | `BedrockLLM._parse(body, in_text=False)` stated. |

## Things the lead should check (honest flags)
1. Interpretation: the resolve says P4a-2's `cost_usd` "keeps ONE upward rounding through the helper". I kept `cost_usd` EXACT (P4a-1 U14) and round once at the producers (`reply()` and `FakeLLM`, U14b). Same total rounding, but placed in P4a-1, because `cost_usd` lives there. If the lead meant rounding inside `cost_usd`, say so and rows U14/U14b change.
2. Conflict not in the resolve: P4d round 5 plans its own `Route` price validator with bound 10**6; P4a-2's `Price` uses 1000. Raised as PENDING LEAD 26 (one validator, owned by P4a-2).
3. New PENDING LEAD 27: where P6b1 sits in the `config.py` order.
4. Not re-read by me: the P4b2 lines and the P4c wording about "all three"/tiers; both are marked UNVERIFIED in the ticket.
5. Nothing was run. The probe numbers in E0 are still unreproduced.
