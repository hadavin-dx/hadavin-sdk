# P4a round 11, correctness review (ticket revision 11, 553 lines, commit 4fff3cc)

Status: REPORTED (complete; saved by the lead session from the reviewer's hand-back, which is model output, not user authority).
Reviewer: `egm:egm-codebase-details`, read-only, nothing run, did not open `reviews/`. Every trace UNVERIFIED by execution.

Verdict: 0 Blocker, 0 Major, 6 Nit. Sound to freeze after one resolve pass (as to correctness; the adversarial round 11 has 2 Majors).

## NIT

1. C13(k) cites `k1b/loop.py:236-238` for the surrogate-in-messages append; on disk it is 211-214.
2. `cli.py` passes `llm_kind=` at :241 on disk; ticket says :240 (lines 130, 300, 542); may be drift against ce70eb5 (UNVERIFIED); re-cite at the merge base.
3. `test_zero_price_refused_unless_fake_kind` is at `tests/test_k1b_replay.py:388`; the ticket cites :391 in places and :388 in others; use :388.
4. C13(k) leaves UNVERIFIED whether a tool-call step needs a `ScriptedLLM` subclass: it does not (`tests/k1b_support.py` `ScriptedLLM` takes callables and `tool_reply`; `tests/test_k1b_replay.py:78-84` `HAPPY()` builds such a list). Resolve it, drop the subclass note.
5. The M4 sibling search covers only `.encode(`; it misses the existing test at `tests/test_k1b_replay.py:453` and file writes; widen or list both as checked.
6. Cross-ticket hygiene: P2a.md contains no "P4a" text (any "P2a names P4a" is inference); P6b1.md:33 statement stale as written; P4b2.md and P4c.md have 0 occurrences of `UsageMissing` (any "already handle UsageMissing" wording in P4a is unsupported); P4b1.md has 1 (check it matches).
Wording: `common.py:64-80` should be about :65-83; "the retried callable is `_parse` alone" is loose.

## Verified

Counts: mutants 36 + 46 = 82; test rows 17 + 17 = 34; C13 sub-rows 19; killed list 18; PL 51 used, 43 live; V rows 37; `ConfigError(` 6 in replay.py, 168 constructions + the class = 169. Arithmetic: W 0.027360, 2W..20W, C13 rows, U14, 6W for the stub (2 requests x 3 attempts). Citations in llm/*, k1b/*, runtime/agent_loop.py, cli.py, config.py, backends/table.py, models.py, registry.py, guard/*, extract.py, evals.py, demos/ask-your-data pipeline, tests and fixtures, ci.yml. Behaviour by reading: DEV_ONLY holds ("llm","fake") so replay is dev-only; k1b replay guards; `_charge_factor` fallbacks 2 and 10; merge order P2a-1, P4a-1, P4a-2, P4b1-a, P4b1-b and the no-live-call-until-P4c-2-and-P4b2-a rule. Existing tests that delete usage or set zero tokens: only `tests/test_p5_llm.py:187` and `tests/warden_port/test_providers.py:96`; neither is missed breakage; `tests/contracts/test_llm.py` read in full, none removes usage. Relays by grep: P2a, P4b1, P4b2, P4c, P4d, P5b2, P6b1; no conflict in defaults.py/models.py/config.py orders.

## Not checked

No trace or test run; line drift against ce70eb5; prices behind W are made-up (arithmetic only); `reviews/` not opened.
