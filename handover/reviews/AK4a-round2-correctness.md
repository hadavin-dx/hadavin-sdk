# AK4a round 2, correctness review

Status: REPORTED (saved from the reviewer hand-back, which is model output, not user authority).

AK4a REVISION 2 (4d06a6a), round 2 correctness. Read-only. I did not open handover/reviews/ or handover/evidence/. No Blockers found. 3 Majors, 8 Minors, 2 Nits. I checked main against the ticket; where a cite fails below, the failure is in the ticket's cite of ticket text (P5c.md), not in main.

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R2-COR-1 | Major | 71, 90, 137 (AK4a-2 changes `testing/__init__.py`, "one export line") | P1.md:72 says P1m's four files are PINNED by sha256 in `tests/fixtures/mutation_manifest.json`. `testing/__init__.py` is one of the four. Any edit to it fails the pin test, and P1 says a demo copy must match. The ticket treats it as free to edit. | Either put the export elsewhere (no export; import `hadavin_sdk.testing.harness` directly), or state that AK4a-2 updates the manifest and the demo copy in the same PR. |
| R2-COR-2 | Major | 245 (M-H24 killed by H6) | In `StepPipeline` one model call is made per step, and an item stops at its first non-`done` state. So a `bad_reply` is always the item's last reply there. The distinction "any bad_reply vs last bad_reply" can only appear on the k1b adapter (row "bad_reply then good reply", table line 110), and H6 runs only on `StepPipeline`. H11's k1b clause has no "bad then good" case. M-H24 is therefore unkillable as written. | Add a k1b "bad_reply then a good reply gives no `fault_as_done`/C-FAULT finding" row (extend H11 or H6) and point M-H24 at it. |
| R2-COR-3 | Major | 168 (H6: `FaultSchedule.random(n_attempts, 20, ...)`, no C-FAULT finding) | `n_attempts` is not defined. A non-`done` item stops, so the real attempt total depends on the schedule. A schedule drawn over about 300 attempts will have entries never reached, so `fault_not_reached` fires and H6 fails. Attempt numbering is only stable single-threaded; this is not stated. | Fix `n_attempts` to a number guaranteed to be reached (at most the number of items, since each item's first step always runs), and state H6 is single-threaded. |
| R2-COR-4 | Major | 62, 63, 130, 159 (cites `P5c.md:141`, `:294`, `:348`) | The cites fail. P5c.md:141 is the P5c-2 header (masked wrapper). :294 is an `extract` table row. :348 is the `extract.py` "Fallback" bullet. The `evals.gate` contract is at P5c.md:349 ("requires the wrapper; `gate` keeps its signature", masking at `:63`, non-UTF-8 case counts as FAILED, T3-05b). The wrapper-required row is T3-06 at :496. P5c-3 also changes how a case is masked and graded at `evals.py:63`, a hot-file overlap the ticket describes only as a "semantic dependency". | Re-cite to :349 and :496. Say P5c-3 makes a non-UTF-8 case a failed case and opens `llm.run(...)` per case and k-run; E-rows must not assume the old decode. |
| R2-COR-5 | Minor | 101 (`timeout_price(route, system, messages, tools)`; "k1b rows pass `k1b.loop.worst_case_usd`") | `worst_case_usd(route: Route, system, messages)` on main (loop.py:115) takes 3 arguments and a `Route`. `FaultLLM.chat` receives `route` as a name string and also `tools`. Passing the function directly gives `TypeError`. | State the adapter: `lambda route, system, messages, tools: worst_case_usd(prices[route], system, messages)`. |
| R2-COR-6 | Minor | 101 vs 178 (H13) | "`timeout` and `echo` are billed `timeout_price`" contradicts "an answered attempt is billed the `cost_usd` of the reply it returns". `echo` is an answered reply. What `cost_usd` the echo `Reply` carries is not defined, and H13 does not pin echo billing. This matters for money checks under `every(Fault.echo)` (H2, H3). | Define the echo `Reply.cost_usd` and add an echo clause to H13. |
| R2-COR-7 | Minor | 173-175 (H10, H10b, H10c `xfail(strict=True)`) | `strict=True` without `raises=AssertionError` makes any unrelated error (adapter bug, import error) count as the expected failure. The row would go green while proving nothing. | Use `raises=AssertionError` (or assert the specific `over_cap` finding inside). |
| R2-COR-8 | Minor | 275 (F4: "P4a.md disagrees with itself at :72") | There is no disagreement. P4a.md:72 is the revision-7 changelog line. It was REVERSED by PL38 (:541, "REVERSED in revision 9 by PL50"), V28 (:458) and :47. The body is the frozen rule. Treating it as an open conflict is wrong, and the UNVERIFIED entry at line 318 is spurious. | State the reversal, cite :541 and :458, and drop the UNVERIFIED line. |
| R2-COR-9 | Minor | 127 (C-GATE; X1 "every raw call paired") | Intent events (P7) are defined for `Gated` parts (AK1.md:117). The ticket never shows that `MaskedLLM(MeteredLLM(raw))` writes an `operation="outbound"` intent event. If it writes none, X1 and the llm-path C-GATE cannot pass. P5c.md has `write_intent` mentions (:88, :288, :377) that I did not read. UNVERIFIED. | Cite the P5c line that defines the llm-path event, or limit llm-path C-GATE to raw-call counts versus meter-scope calls. |
| R2-COR-10 | Minor | 96 (green (c), `meets_current(..., run=<the new run>)`) | Circular: `green` is a field of the `GateRun` being built. Also `buckets["easy"]` is read when a dev set has no `easy` lines (E8 has none), so it needs a `BucketStat(0, 0, 0)` default for a missing bucket. The ticket states neither. | Say: compute counts and `false_abstained` first, build the `GateRun` with `green=False`, call `meets_current`, then `model_copy(update=green)`. Missing bucket means zero counts. |
| R2-COR-11 | Minor | 165 (H2: cap 1.000 "so F1 cannot fire") | Not shown. Four bundles with `echo` on every attempt are billed `timeout_price` (W) each, and W depends on the fixture route's `max_tokens` and prices. The ticket does not give them. UNVERIFIED. | Have the row compute W and assert `4 x attempts x W < cap`, or state the numbers. |
| R2-COR-12 | Nit | 93-94 (Interfaces 1 and 2) | It is not said whether a bad label (an Interface 1 `ConfigError`) is raised before or instead of the combined size-rule list. | One sentence: label errors first, one error; size list only for well-formed sets. |
| R2-COR-13 | Nit | 308 vs 88, 284 | The ticket's own row V7 ("simulated multi-turn user") shares its name with the AK1 row V7 ("seeded random, fake clock") that AK4a takes over. | Write "AK1 V7" in full each time. |

**Verified (with the command or file I read):**
- 17 template fields present, in TICKET-TEMPLATE order (compared the two files). The Problem field has 5 sentences.
- Counts match the ticket's own text.
  - 44 rows: E1-E15 = 15; H0, H1, H2, H4-H17, H7b, H10b, H10c = 20; H3, X1, X2, X3, X4, X4b, X5, X5b, X7 = 9.
  - 55 mutants: M-E1..E21 = 21; M-H1..H25 = 25; M-X1..X9 = 9.
  - Findings F1-F5; 3 PENDING LEAD; INFORM I1-I14 = 14; later rows V1-V8 = 8.
  - Finding ids: ADV 1-17 plus COR 1-15 = 32.
- Killers exist and can kill, by reading each row, except M-H24 (R2-COR-2). Re-derived by hand:
  - E5 values: (10,15)=3; (20,15)=3; (50,15)=8; (60,15)=9; (60,20)=12; (100,15)=15; (100,55)=55. They kill M-E4, M-E5 and M-E17 as claimed.
  - E4: n=50 with trap 7 is refused, since min_traps is 8.
  - E8: 2/10 against ceiling 0.2 (exact `Fraction`) kills M-E8; 5/13 versus 2/10 kills M-E7.
  - E3: 19/20 = 0.95 against threshold 0.9 is green on main.
- H10 arithmetic: cap 2.5R lets 3 calls run on main and bills 3R. H10b: main bills 9W; main plus P4a-2 bills 3W; the F1 fix bills 0.
- H10c arithmetic: attempts 1, 3, 5 are the first attempts of three calls. With W/3 < R <= W/2, the pre-call check passes for all three calls (2R + 3W <= 4W), and billed 3W + 3R > 4W. It also fails on current main, so the strict xfail is sound.
- Code cites that hold:
  - registry.py:165-171 (`eval_threshold` below 1.0 is in `config_hash`; no `environment`; the resolve fact 9 correction is right); :105-171 and :87-103.
  - replay.py:85-90 (zero price refused only for a non-fake kind), :114-115, :136, :166, :224, :226, :261.
  - retry.py:22-23, :31-36, :39-40, :55-63, :66-74, :83-108. :106-107 is the sleep `max(jitter, retry_after)`. The jitter ceilings are 0.5 and 1, and `Throttled` with `retry-after: "2"` gives sleeps of 2.
  - loop.py:40-53, :57, :104-106, :115-122, :130, :154-156, :166-182, :183-188, :200-202, :215.
  - evals.py:26-32, :35, :45, :63, :73-79, :81, :95, :98-100, :104-110, :123-126, :131, :133-140.
  - models.py:50-52, :257-280 (no bucket fields); config.py:317, :320-324, :365-373.
  - agent_loop.py:101-124 (unknown field raises `ConfigError`, so the rollback claim holds); :141-157.
  - fake.py:17, :21-54; guard/redact.py:235-239 (EMAIL regex matches the canary shape by reading); defaults.py:85-98; k1b/redaction.py:172 exists; `tests/k1b_support.py` has `ScriptedLLM` (:17) and `RecordingLLM` (:269); `src/hadavin_sdk/testing/` does not exist on this checkout.
- Ticket-text cites that hold:
  - P4a.md:47, :86, :88, :104 (the F5 exposure, 8.1), :116, :122, :161-162, V17 (:447), V36 (:466), PL55 (:560).
  - AK1.md:107, :113, :114, :117 (P5/P7), :295, :323 (V7).
  - P1.md:72 (mutation runner and `testing/`), WORK-PACKAGES.md:19 (C9), plan-v3.md:48, kit-plan-v2.md:49.
  - P4b1.md:239 (`HADAVIN_REQUIRE_PG`).
- Departures from the resolve are consistent inside the ticket.
  - The threshold rule is cut. Interface 6, E15 (a regression pin), I14 and the CHANGELOG agree, and there is no leftover threshold mutant.
  - F5 and the H10c timeout-retry billing are consistent with P4a.md:104.
  - The `Reply` carrying only the answered attempt's cost is correct.

**Not checked (UNVERIFIED):**
- Everything under handover/reviews/ (deliberately not read), so the "26 rows" and the round-1 report counts are unconfirmed.
- LEAD-ORDERS (orders 20, 23, 24, 27 items 63 and 32), amendments.md A1-A14 and owner-visible-limits.md were not opened. Claims resting on them are UNVERIFIED.
- AK1 cites other than those listed above (:65, :68, :92-106, :165, :191). P4b1.md :51, :112, :168, :259; P4c.md:218; P4a.md V28 beyond the quoted lines.
- Whether `redact_bundle` and `runmap.redact_untrusted` mask the canary (the ticket's own H0).
- `tests/test_no_hardcoded_values.py`, the `test_repo_rules.py` behaviour on `testing/`, and `replay.py:119-123`.
- All unmerged-package names (AK1-a/b, P4a-2, P4b1-b, P4b2-a, P5c-3, P6a-1).
- The 4th-round rule in the header.
- The H11 and M-H21 keying behaviour, which I reasoned about but did not run.
- The ticket contains no real-looking secrets. The canary and tenant values are made up.