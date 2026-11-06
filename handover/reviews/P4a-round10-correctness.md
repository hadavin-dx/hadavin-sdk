# P4a round 10, correctness review (ticket revision 10, 511 lines)

Status: REPORTED (complete; saved by the lead session from the reviewer's hand-back, which is model output, not user authority).
Reviewer: `egm:egm-codebase-details`, read-only, nothing run, did not read `reviews/`. All traces UNVERIFIED.

Verdict: 0 Blocker, 2 Major, 11 Nit. The ticket does not contradict the code anywhere except one off-by-one cite.

## MAJOR

**MAJOR-1 (lines 273, 504; C18 / PL55 / V36).** The replay guard makes `k1b replay` unusable outside dev, and the ticket never says so. The PL55 guard refuses every non-fake `llm_kind`. `config.py:366-369` refuses DEV_ONLY kinds when environment is not dev; `backends/table.py:593-595` lists ("llm","fake") as DEV_ONLY. So after P4a-2 replay is refused in every non-dev environment. The ticket says only "cannot run a real model". Fix: state the consequence in CHANGELOG item 5, the PL55 cost and Answer first 8; lead confirms, or scope the guard (explicit replay-only fake allowance).

**MAJOR-2 (lines 121, 128).** "Same order as PL45 and P4d.md:17" is false. P4d.md:17 lists defaults.py as: P1a, P2a, P2d-1, P1b, P2d-2, then P4d-a2-i, P4d-b, P4a-1, then P4b2; it names neither P4a-2 nor P4b1-a. P4a's defaults.py order omits P2a-1 although P2a.md:30 adds a defaults.py block; the models.py order (line 128) also omits P2a-1. P4d.md:17 is itself inconsistent (P2a-1 after all five P4d PRs for config.py, before P4d-a2-i for defaults.py). The config.py order does match. Fix: add P1a, P2a, P2d to the defaults.py order and P2a-1 to models.py; reword to "consistent with, extended by"; send P4d a note.

## NIT

- NIT-1: pre-PL54 numbers remain at V19 (395), V34 (410, "over-booked by W" now 5W), checklist item 3 (431), PL30 (477), PL38 (485), PL48 (496).
- NIT-2: line 6 says no scripted rewrite; lines 454(d) and 455 disclose a `python3 -I` script.
- NIT-3: line 107 cites cli.py `make("llm", ...)` at :220; it is :221.
- NIT-4: line 310 (e),(d) "killers of a2-51" differs from line 357 and item 5 (line 421): C13(a),(d), j7(3).
- NIT-5: 8.2 table row "one-request kind with 3 attempts = 3W" is prose with no test row; line 66 says every row asserts equality.
- NIT-6: fail-before list at 366 omits C13(j7).
- NIT-7: line 365 says a2-25 reused above; a2-25 is deleted.
- NIT-8: "Depends on P2a-1" (265) should be a merge order, not a code dependency.
- NIT-9: "47 live numbers" (458) includes withdrawn/replaced PLs; line 64 omits PL57-PL59.
- NIT-10: the guard keys on the label `llm_kind or cfg.backends.llm.kind`, not the object type; state it.
- NIT-11: line 292 never says C1 was deleted.

## Verified correct (summary)

Code cites in llm/retry.py, openai_compat.py, common.py, gemini.py, bedrock.py, anthropic.py, fake.py, k1b/loop.py, k1b/replay.py, runtime/agent_loop.py, config.py, backends/table.py, models.py, registry.py, guard/*, tests and fixtures. Arithmetic: W 0.027360; 2W 0.054720; 3W 0.082080; 5W 0.136800; 6W 0.164160; 20W 0.547200; C13p 0.016260 (and mutants 0.000900, 0.019860, 0.016254); C13q 30,004 bytes = 0.105372; U14 (i) 2,000,000, (ii) 1999999.99600001; cache write 0.118080; Gemini 0.002400. Counts: P4a-1 32 mutants, P4a-2 38, total 70; test rows 17+17; C13 18 sub-rows; PL 1-11 and 24-59 = 47; V1-V37 present; 17 template fields per sub-ticket. Cross-ticket: P4d config.py/common.py/fake.py orders match; defaults.py does not. P4b2.md:26 stale.

UNVERIFIED by the reviewer: the 2,568-byte TOOL_SPECS figure; all runtime behaviour; pickle behaviour of `UsageMissing`; P4b1 lines 142/167/184 beyond grep; test_k1b_cli configs; the roughly 50 `run_case` test stubs that may assert exact USD.
