# P4a ticket, round 1, CORRECTNESS review

- Reviewer: `egm:egm-codebase-details` (fresh, read-only, Sonnet 5.5 set by the lead). Ticket `tickets/P4a.md` rev 1 (bd061b3), core ce70eb5. Nothing run. Template check: all 17 fields in order in all three sub-tickets; order 6(b) Tier A applied; A9 B1/F10/A11/F6 reflected.
- Result: BLOCKER 0; MAJOR 3 (F1-F3); MINOR 10 (F4-F13); NIT 3 (F14-F16). Stop rule NOT met.
- Saved by the lead 2026-11-05, CONDENSED (the long "verified true" list is summarised: Route/Money/reply/openai_compat/pipeline/registry/call-site/retry/Intake cites and the arithmetic 0.00945, 0.4065006, 0.2070003, 0.00462, 1E-7, 0.001005, 0.0009 all recompute correctly). Ledger rows `BL-core-p4a-r1-cor-*`.

| id | sev | section | problem | fix |
|---|---|---|---|---|
| F1 | MAJOR | P4a-1 Gemini rule; test_p5_llm.py:260; P4a-2 C4 "unchanged" | `test_gemini_thinking_tokens_are_charged_as_output` sets thoughtsTokenCount=93 on a fixture whose totalTokenCount stays 307 (gemini/text.json:23-27); P4a-1 refuses total != prompt+candidates+thoughts (400) as `UsageMissing("invalid")`: the test fails by exception; not in the break-by-design list; same trap in the C2 Gemini row. | List it under tests that break by design; set totalTokenCount 400 in the test and C2; fail-before row; drop "unchanged" from C4. |
| F2 | MAJOR | P4a-2 `Usage.__post_init__`; USAGE_REASONS `invalid` | `Usage(...)` raises ValueError when thinking > output but nothing turns it into `UsageMissing("invalid", ...)`; inside the retried call it becomes a plain `ProviderError` ("anthropic: ValueError") and settles at zero (pipeline.py:163); if built in `reply()` the raw ValueError escapes `agent_loop` (catches only ProviderError). Same for an openai_compat two-request sum above 10**9. | Each kind checks thinking <= output and sum <= cap before building `Usage`, raising `UsageMissing("invalid", field)`; row + mutant. |
| F3 | MAJOR | P4a-2 C2, C7 fail-before | Both need a Route with cache prices; ce70eb5 `Route` has `extra="forbid"` (config.py:52): fixture raises ValidationError, banned by the ticket's own fail-before rule; C7's old-code claim is inexpressible. | Shim pattern `route, err = build(...)`; or flat route with the same usage; label C7 "new feature". |
| F4 | MINOR | Interface notes | "48 under tests/fixtures/recorded/" is 24 reply files + README. | Correct; builder probes all `*.json` incl. output_tokens. |
| F5 | MINOR | Evidence commands | `grep \bor\b ... \| grep -i token` cannot be empty (common.py:125 comment). | Use the AST guard output or exclude comments. |
| F6 | MINOR | Mutant a1-3 (2nd half) | Equivalent: `with_retry` re-raises ProviderError at once (retry.py:95-96). | Drop it. |
| F7 | MINOR | U3 / a1-5 | `checked_count` cap boundary not tested at 10**9 / 10**9+1. | Add both and a1-5b. |
| F8 | MINOR | Mutant a2-18 | Unkillable: prices <= 1000 with <= 6 decimals, counts <= 10**9, sums fit 28 digits. | Remove or restate; 60-digit context is defensive only. |
| F9 | MINOR | Gemini rule | Missing `totalTokenCount` with missing candidates undefined. | `UsageMissing("absent")` + U3 row. |
| F10 | MINOR | openai_compat / U4 | Not said whether a second request is sent after the first lacks usage. | State "raise before the second request"; assert request count. |
| F11 | MINOR | Answer first 1(d), Interim window | Zero-booking window in the unsafe direction, "dated" without date or merge-order guard. | Hold P4a-1 until P4b1 can merge directly after, or a minimal worst-case charge at call sites (see adversarial F1). |
| F12 | MINOR | Hot-file order | Omits P5b1/P4b2 files (`anthropic.py`, `bedrock.py`, `retry.py`, `protocol.py`, `fake.py`, `gemini.py`, `openai_compat.py`, `defaults.py`, `__init__.py`); `askdata/meter.py` listed but not in P4a-1's file list. | Reconcile with P5b1/P4b2. |
| F13 | MINOR | Done | "After round 5 escalates to the lead" conflicts with "no round cap" (order 6b). | Remove or cite. |
| F14 | NIT | C8 | No expected result for bool, empty string, float rows. | List them. |
| F15 | NIT | P4a-3 Files | `test_k3_pilot_env.py:47` cite (routes at :44 via `pilot_cfg`); every `pilot_cfg` test needs `price_checks`; demos/templates pilot/prod configs unchecked. | Grep `environment: pilot` / `prod`. |
| F16 | NIT | Rollback | Loud-failure test replaced by an evidence step: deliberate departure from template. | State it. |

Not checked by the reviewer: provider live behaviour, installed SDK definitions, Intake budget semantics, plan sections 3-9, every `Reply(`/`Route(` construction in tests/demos, whether Reply is serialised.

Model used: Sonnet 5.5 (set by the lead).
