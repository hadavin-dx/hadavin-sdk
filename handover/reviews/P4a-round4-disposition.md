# P4a round 4 disposition (applied in P4a.md revision 5)

Written 2026-11-05 about 19:15 UTC (2026-11-06 00:45 IST). Text only: no code, no suite, no git write. Nothing in the ticket was run; the checks I did were reading code on core ce70eb5 (read-only), counting table rows, and one `git diff --stat ce70eb5 HEAD -- src tests demos` (printed nothing; HEAD moved to 9c8508c while I worked because other agents commit in this worktree, so the lead re-runs it at the reviewed head, ADV-R4-13).

Input: `P4a-round4-resolve.md` (23 finding ids: ADV-R4-1..13, COR-C4-1..10; two merged pairs, so 21 rows below).

| Finding | Status | Ticket location (P4a.md) | Note |
|---|---|---|---|
| ADV-R4-1 | applied | Answer first 1(a), 8; P4a-1 `openai_compat` bullet; rows U4, U4b; mutants a1-21, a1-21b; P4a-2 `k1b/loop.py` bullet (UsageMissing branch) | A failure of request 2 after request 1 was answered is re-raised as `UsageMissing("absent","usage")` chained from the real error; a first-request failure is unchanged. The loop then charges the worst case instead of 0. |
| ADV-R4-2 + ADV-R4-7 | applied | Answer first 8(c); Interfaces rows `_charge_factor`, `Budget.charge`; P4a-2 `k1b/loop.py` bullet; C13 rows (b2), (c), (d), (g1-g5); mutants a2-24d, a2-24e, a2-25b, a2-25c | Three billed-but-unknown branches (`CallTimeout`, `UsageMissing`, `ProviderExhausted`) each charge `worst_case_usd(..., requests=_charge_factor(llm))` under `route_prices is not None`; plain `ProviderError` stays 0. PENDING LEAD 31. |
| ADV-R4-3 | applied | Answer first 1(c); P4a-1 `reply()` bullet; rows U2, U2c; mutants a1-20, a1-20b; PENDING LEAD 5 (rewritten), 33 | Output 0 with text or a tool call is `implausible_zero("output_tokens")`; kept at 0 only for an empty reply, a refusal or a blocked prompt. Not applied to `FakeLLM` (all 24 recordings have output 50). |
| ADV-R4-4 | applied | Answer first 6; Interfaces row "Config zero-price check"; P4a-2 Config validator bullet; C8b; mutants a2-32, a2-32b; V12; PENDING LEAD 32 | Zero route price refused at config load for every non-fake `backends.llm.kind`, in its own `model_validator`. Applies to every route in the config, including unused ones (my disagreement 6). |
| ADV-R4-5 | applied (narrowed by the resolve) | Answer first 5; Notes for P4b1 items 13 and 16; Lead merge-time checklist item 0 (hard gate); V2 | The resolve narrowed it: no code in P4a. A P4b1 relay and lead gate: a pre-call refusal above 100,000 prompt tokens, with a row and a mutant. The number is UNVERIFIED against an official page. |
| ADV-R4-6 + COR-C4-1 (BLOCKER) | applied (with two disagreements) | "What changed from revision 4" (honest blocker note); Verified facts ("a stub reaches the charge"); Rules stated once ("Reservation strict, charge total"); Interfaces rows `request_bound`, `_charge_factor`; P4a-2 `k1b/loop.py`, `tests/k1b_support.py`, `FakeLLM.max_attempts = 1`; C13 rows a, a2/b2, c, d, e, f, g1-g5, h, i, C13p; mutants a2-33, a2-33b, a2-33c, a2-34, a2-35, a2-35b, a2-36, a2-37, a2-37b | `request_bound` stays strict (TypeError missing, ValueError bad, bool refused) for the reservation; the charge uses the total `_charge_factor`. `tests/test_k1b_replay.py:502` is named and not edited. Disagreements 1 and 3 below. |
| ADV-R4-8 | applied (narrowed by the resolve) | Plain words; Answer first; P4a-2 Problem text (L228); security notes; V18 | "Refuses unknown pricing words" now says Anthropic kind only; the OpenAI-compatible and Gemini kinds read no tier field and price flat (V18). |
| ADV-R4-9 | applied (with one disagreement) | P4a-1 Gemini rule; rows U3 Gemini rows; mutant a1-12b; V19; PENDING LEAD 34 | Output 0 only for the no-candidates plus `blockReason` path. Disagreement 2. |
| ADV-R4-10 | applied (narrowed by the resolve; one mutant dropped) | U14 max-case rows; U6 floor `Fraction(1024*10,10**6)`; C7(f) ("ALONE" removed); mutants a1-22, a2-25b (guard), a2-31 (requests domain); removal note for a2-30 | U14 now calls `round_cost_up` on a max case; U6 floor derived in Verified facts; a2-30 removed (no natural patch). Disagreement 7. |
| ADV-R4-11 | applied | P4a-1 Done (first line, HARD GATE); Lead merge-time checklist item 0; Notes for P4b1 items 13-16 | Hard gate before P4a-1 merges, checked by grep in `P4b1.md` on disk. P4b1-b gets the wrapper-forwarding mutant (literal 1). |
| ADV-R4-12 | applied | Rules stated once ("Wrappers forward", "Settle in finally"); Notes for P4b1 items 14, 15; checklist item 0(iv) | Wrapper requirement: a non-`ProviderError` from `round_cost_up` or `request_bound` after a paid call must still settle the reservation at the reserved amount (P4b1-b row). |
| ADV-R4-13 | applied | Header (revision line, HEAD, diff-stat); Lead merge-time checklist (last paragraph) | Empty diff-stat quoted for e4f6f07; lead re-runs it at the reviewed head. |
| COR-C4-2 | applied | Rules "Wrappers forward"; Notes for P4b1 item 14; C13 row (h) pins; checklist item 0(iii); mutants a2-37, a2-37b | Both attributes are forwarded by wrappers; a missing attribute no longer fails open to 1 (the charge uses the fallback factors). |
| COR-C4-3 | applied | C13 preamble; rows (a), (a2/b2) | Expected token counts come from the real first message built at `k1b/loop.py:144-149`, or the row asserts via `worst_case_usd`; no unreachable `messages=[]` literals. |
| COR-C4-4 | applied | Fail-before wording rule; rows U1, U3 (Bedrock via `chat()` with a stub `converse` client); U14b, U14c labels | Bedrock rows driven through `chat()`; rows with no fail-before are labelled "new interface, no fail-before". |
| COR-C4-5 | applied | Answer first 3; Interfaces `round_cost_up` row; Notes for P4d | P4d cited by item name (and PL19), not by line number. |
| COR-C4-6 | applied | Verified facts (two estimate tests); U9 | "two" tests: `tests/warden_port/test_providers.py:30, 37`. |
| COR-C4-7 | applied | P4a-1 zero-rule text (PL5) | Cites PENDING LEAD 5, not 3. |
| COR-C4-8 | applied | This file (re-map below) | See the round-3 id re-map. The lead adds the questions-for-lead line (PL29 reading). |
| COR-C4-9 | applied | "What the lead needs to check" item 1; C15 | Cites fixed (`loop.py:166-179`, `table.py:593, 595`, `test_llm.py:94-95`); C15 no longer says UNVERIFIED for what is checkable at `tests/contracts/test_llm.py:81-83`. |
| COR-C4-10 | applied | C7(b) | Domain excludes `input_tokens == 0` and bounds output by `max_tokens`. |

Counts: 23 finding ids in 21 rows. Applied 21 rows (23 ids), of which 3 rows were narrowed by the resolve itself (ADV-R4-5, ADV-R4-8, ADV-R4-10) and 3 rows carry a disagreement of mine (ADV-R4-6 + COR-C4-1, ADV-R4-9, ADV-R4-10). Contested 0. Declined 0. Mutants after this revision: P4a-1 34 table rows (28 + 6; one of them, a1-14, is a signature check); P4a-2 46 (31 - 1 + 16). The arithmetic is shown in "What the lead needs to check" item 5.

## Round-3 id re-map (COR-C4-8)

The round-3 disposition file (`P4a-round3-disposition.md`, not edited by me) numbered some COR rows differently from `P4a-round3-resolve.md`. The resolve ids are the authority:

| Resolve id | What it is | Where the round-3 disposition put it |
|---|---|---|
| COR-R3-1 | "P4d on disk is revision 6" deleted; helper `round_cost_up` lives in `llm/common.py` | disposition row COR-R3-3 |
| (verdict row, no COR id) | `cost_usd` stays exact, rounding at the producers (PL29) | disposition row COR-R3-1 |
| COR-R3-3 | P6b1 sits after P4b1-b (PL27) | disposition row COR-R3-5 |
| COR-R3-5 | P4a-1 Done no longer lists later merges; stacked-review rule | disposition row COR-R3-4 (together with COR-R3-4) |
| COR-R3-12 | P4a-1 Rollback: U1, U2, U5 as loud-failure stand-in | disposition row COR-R3-12 (ids match; the row also mentions Done) |

The other round-3 ids matched. Read all disposition rows through this table. The note the round-3 resolve asked for in `questions-for-lead.md` (the PL29 reading, "cost_usd stays exact, round once at the producers") is not in my allowed files; I could not check whether it exists. The lead adds it.

## Disagreements and notes (also in P4a.md "What changed from revision 4")

1. A zero charge is accepted. The resolve says a zero or negative charge "would LOWER the spend total". A zero does not lower it, and a free reply is a normal case, so `Budget.charge` refuses only negative and non-finite amounts. Row C13(i) and mutant a2-35b (a zero amount refused) pin it.
2. Gemini `MALFORMED_FUNCTION_CALL` never reaches the usage rule. The resolve calls it a cut-off reply with output absent; in code (`llm/gemini.py:108-111`, re-read) it raises `ValueError` before usage is read, so it books 0 today. I did not widen P4a: V19 and PENDING LEAD 34 hand it to P4b2. UNVERIFIED: whether a SAFETY candidate may lack `candidatesTokenCount`; the rule is safe either way.
3. Fallback factors: attempts 10, requests 2. The resolve says 3 attempts. I chose 10 because I found no validated cap of 3 on `max_attempts` in what I read (UNVERIFIED: I did not search every config path), and over-charging is the safe side. PENDING LEAD 30; the lead may pick 3.
4. `FakeLLM.max_attempts = 1` and `ScriptedLLM` declarations are added (the resolve names `ScriptedLLM` only). Without `FakeLLM.max_attempts` the fallback would charge a fake run 10 times.
5. The Route price validator has two possible owners: P4d-a (single validator on `Route`) and the P4a-2 `Price` clauses. I wrote the clauses and said P4d must not add a second validator (PENDING LEAD 26); I did not read code that settles which lands first.
6. The Config zero-price check applies to every route in a non-fake config, including routes that are never used (PENDING LEAD 32, recommended yes).
7. a2-30 dropped: C15 passes on ce70eb5 and on every small patch because the failed attempt carries no usage in code, so the mutant had no natural patch. C15 stays as a documentation pin and says so.
8. New PENDING LEAD items in revision 5: 30 (fallback factors), 31 (`ProviderExhausted` charge), 32 (Config zero-price refusal), 33 (output 0 with content), 34 (parse failures after HTTP 200); items 5, 26 and 28 changed.
9. My own slips found while writing: the P4b1 text claiming "Tier A" money status was an overclaim and was removed; one `:266` cite became `:267`; a garbled sentence was rewritten; the U4 per-request zero wording was corrected. None was reported by a reviewer.
