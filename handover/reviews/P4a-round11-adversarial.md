# P4a round 11, adversarial review (ticket revision 11, 553 lines, commit 4fff3cc)

Status: REPORTED (complete; saved by the lead session from the reviewer's hand-back, which is model output, not user authority).
Reviewer: `egm:egm-design`, read-only, nothing run, did not open `reviews/`; did not read lines 198-243 (P4a-1 rows) and 293-325 (P4a-2 file list, C2-C7), 410-450 (v1.1), PL1-PL43. PL60-PL63 not re-litigated. Every trace UNVERIFIED unless read on disk.

Verdict: no Blocker; 2 Major, 8 Nit. Core rule held: every k1b booking after a possibly billed call is requests x attempts x W.

## MAJOR

- **M-1. No row or mutant kills a round-down or missing round-up in `k1b.loop.worst_case_usd` (lines 68, 343-345, 355-360).** Under-books by up to 1e-8 USD on the path order 14 item 3 says must never book less. Every C13p/C13q literal (0.016260, 0.032520, 0.097560, 0.105372, 0.015381) is whole at 6 decimals, so truncate/round-to-nearest/no-`round_cost_up` mutants give the same values. a1-22 covers only the producers. Fix: C13p clause with a non-whole W (e.g. price 3.123457, odd byte count) expected as the `Fraction` ceiling at 8 decimals, plus a `requests=3` case; mutant "`worst_case_usd` rounds down, to nearest, or not at all". Test-only.
- **M-2. Stale relay weakens the live-call gate (line 197 vs 292, 81, PL51).** P4a-1 Depends-on ends "no live provider call until P4c-2 has merged"; P4a-2, Answer first 2 and PL51 say "P4c-2 AND P4b2-a". Fix line 197. Also say plainly in Done/CHANGELOG that nothing in code enforces the gate (`DEV_ONLY` refuses only the fake kind outside dev, `config.py:365-373`; a real kind passes load and books the answered attempt only).

## NIT

- N-1: stale on order 16: line 4 "LEAD-ORDERS 1-15"; PL60-PL63 (548-551) still "Recommended", PL63 status unrecorded: mark CONFIRMED by order 16, freeze noted; "two rounds in a row" (line 283) is result review only.
- N-2: line 342 cites `k1b/loop.py:236-238`; file has 217 lines; append at 211-214, unknown-tool branch 200-202 (mechanics hold: `_dumps` uses `ensure_ascii=False`, line 74). Same at line 19.
- N-3: `encode(` sibling search too narrow: `run_case` `out.raw = safe_head(_dumps(call.input), RAW_LIMIT)` (`loop.py:194`) can carry a lone surrogate; whether the outcome writer encodes and raises after the charge is UNVERIFIED; v1 runs only the fake kind. Name it.
- N-4: `cli.py:240` is 241 on disk; `ConfigError(` over `src/` is 169 lines vs ticket 168-170 (disk head 9678a42): pin the counting command.
- N-5: line 457 allows 82/81/80 mutants depending on later runs; pick a rule (a2-11e becomes a regression pin if equivalent; a1-28/a1-29 stay separate).
- N-6: Depends-on incomplete: `P2a.md:22` makes P2a-1 depend on P1m, P3a and ALL FIVE P4d PRs, so P4a-1 is gated behind all of them (P4d.md:150 agrees); write the chain once in Depends-on.
- N-7: line 462 "Item 1 is a HARD GATE" but the gate is item 0 (463); gate needs text in `P4b1.md` not yet present (`UsageMissing` once, no `request_bound`): P4a-1 cannot merge until P4b1 rev 2 exists.
- N-8: a2-48b literal 0.015660 depends on 300 vs 298 characters (0.015657): say "any value other than the literal"; a2-33 names two outcomes (not one hunk); say in CHANGELOG that a legitimate zero on request 2 is refused (U4 clauses 3, 4).

## Held

Upper-bound rule on all three failure branches (CallTimeout, ProviderExhausted, ProviderError incl. UsageMissing); equality rows fail below and above; order 14 item 3 cases (j1, j2, j4); no double booking found (loop.py:166-179 read); request 2 body equals request 1 (`openai_compat.py:118-132`); arithmetic W 0.027360, 2W..20W, C13p 0.016260, a2-9 0.000900, a2-9c 0.019860, a2-49 0.016254, C13q 0.105372, surrogate row 0.015381; counts a1 36, a2 46, total 82; 17 test rows; C13 13+6 = 19, killed list 18; PL 1-11 + 24-63 = 51, 8 withdrawn, 43 live; cites loop.py 115/166/173/176/47, common.py 164-165, config.py 365-373, table.py 40/593/595, openai_compat.py 118; ownership of MAX_USD/round_cost_up/validator by P4d-a2-i; hot-file orders consistent; PL61 matches config.py.

## Not checked

P4a-1 rows 198-243, C2-C7 rows 293-325, v1.1 table, PL1-PL43; other tickets only grepped (P4d, P2a, P4b1); P4b2, P4c, P5b1, P6b1 relays; llm/* beyond two files; agent_loop.py; provider billing; ScriptedLLM tool-call step; pydantic `le` metadata; whether the byte bound holds for every tokenizer (stated limit V35, PL47, PL59).
