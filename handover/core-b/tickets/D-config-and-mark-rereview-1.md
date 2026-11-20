# D-config fix 2 and provider-mark fix round 1: hostile re-review 1 (fresh reviewer, read only, 2026-11-20; nothing in src or tests edited)
Read: config.py, secret_name.py, platform_secrets.check_senders, app.py (_sender_secrets, build), defaults.py, requests/001.answer.md, CHANGELOG, llm/retry.py, anthropic.py, openai_compat.py, common.py, protocol.py, and core-c's guard/model_gate.py at 0e33c0641 (an ancestor of origin/cloud/core-c, head 501301311). Run: tests/test_refused_before_response.py 174 passed; test_trigger_secret_names, _secret_reader, _conflict_setting, _hardening_round4 152 passed (own database hadavin_test_rp4).
Result: 0 Blocker, 1 Major (new, provider mark), 3 Minor.

## Part 1: D-config
| finding | fixed? | where |
|---|---|---|
| D-config-review-1 M1 aliases (env folds, "x" vs "./x") | FIXED | one canonical fold secret_name.py:12-20 (non-alnum runs to "_" first, then lower); used in config.py:428-437 (duplicate and cross-sender overlap on the canonical form) and platform_secrets.py:107-113 (sender vs other names); "/" out of the charset config.py:363 |
| D-config-review-1 M2 provider error names the secret at runtime | FIXED | app.py:375-388: fixed text, `from None`, raised after the handler (no __context__) |
| D-config-review-1 M3 no trigger-config test | FIXED in this tree for names, reader, conflict setting, hardening 3 and 4 (tests/test_trigger_*.py, 152 passed). core-a's test_trigger_config.py is still not in this tree (lead's merge step, as stated) |
| hostile-2 M1 "a/../x" in an other-name gets past the overlap check | FIXED by refusal, not fold | platform_secrets.py:95-106 (any dot segment in a sender name or `path_form_problem` of an other name refuses the start); secret_name.py:36-47; app.py:207 does the same for reset/release refs. Verified: `path_form_problem("a/../x", False)` is True |
| hostile-2 L1 Unicode fold order (dotted I, Kelvin) | FIXED | secret_name.py:20 replaces first, lowers second; run: canonical("slackİtoken") and ("slackKtoken") give "slack_token" / "slackktoken" (the Kelvin sign is a separator, as the env kind treats it) |
| hostile-2 L2 reader trusts `in` on a str subclass; unhashable | FIXED | app.py:376 `type(name) is not str or name not in allowed`. The closure limit is now stated in the docstring (app.py:371-372) and in 001 FINAL |
| hostile-2 L3 floors | FIXED | defaults.py:146-147 (1024, 0.1), config.py:405-413 `ge=` floors, strict |
| hostile-2 L4 chained input / typed value | FIXED for triggers | config.py:706-722 `raise ConfigError(trigger_text) from None`; the bad key in the location is stated |
| hostile-2 L5 CHANGELOG | PARTLY | the reader text is in (CHANGELOG.md:144); see Minor D1 |
| conflict_events_per_minute | CLEAN | config.py:415-420 strict int 1..1000 default 10 (defaults.py:153-155), outside config_hash; CHANGELOG.md:15; answer in requests/005.answer.md |
| 001.answer.md FINAL vs built config | MATCHES on names, bounds, defaults, texts, floors, reader behaviour, fold order, refusal list; one omission, Minor D2 |

New, D-config:
- Minor D1: CHANGELOG has no line for the canonical comparison ("db-pass" = "DB_PASS" = "db.pass"), the path-shaped refusal text, or that a non-live sender agent refuses the whole start (001 FINAL item 7 claims it is "documented in CHANGELOG.md as stated limit (d)"; grep of CHANGELOG for "canonical", "path form", "not live" finds none outside the unrelated lines). Fix: add the three lines to the CHANGELOG trigger entry, or drop the "documented in CHANGELOG" claim from 001 FINAL.
- Minor D2: requests/001.answer.md FINAL lists TriggerSettings fields as "tenant, senders, max_body_bytes, max_running, ack_wait_s" and omits `conflict_events_per_minute` (built later, 14eeb5099; answered only in 005.answer.md). core-a reading 001 alone will not see it. Fix: add the field to the Names line with a pointer to 005.
- Minor D3: a sender name that differs from an other-name only in a leading or trailing "_" or by non-ASCII (e.g. "x_" vs "x") is refused as a collision (over-refusal, canonical strips "_"). Safe direction; no action, noting so a sender is not surprised.
No new Blocker or Major in D-config.

## Part 2: provider mark
| finding | fixed? | where |
|---|---|---|
| review-1 M1 rule 2 inert / gate ignores exhausted mark | OBSOLETE and now the reverse: core-c's gate at 0e33c0641 HONOURS the mark on ProviderExhausted (model_gate.py:224-231, 350-368, 693-695: `getattr(...) is True and isinstance(exc, ProviderError)` then `_settle(reservation, Decimal(0), ...)`). So an exhausted call marked True settles at 0 | see M1 below |
| review-1 M2 router 400/413/422 after upstream work | FIXED | openai_compat.py:78 `refused_statuses = {401, 403, 404}`; per-kind list passed by common.py:400; retry.py:161 |
| ABC/Claude kinds behind Vertex/Foundry | FIXED | anthropic.py:81-117: ALLOWlist `DIRECT_API_PLATFORM = "api"` is the only value that widens; vertex, foundry, unknown stay {401,403,404}; test_make_wide_list_only_for_the_exact_api_platform |
| N3 chain truncated counts as not never-sent | FIXED | retry.py:90-103 (`_chain` returns the flag, `never_sent` returns False on it) |
| N5, N6 docs | FIXED | retry.py docstring, protocol.py:15-17 |
| N7 tests (429 then 400, no-retry kind, TLS, second request) | PRESENT, 174 pass |
| second openai_compat request clears the mark (also ProviderExhausted) | OK | openai_compat.py:126-131 |
Mark values vs the gate: name `refused_before_response`, type bool, set to the exact `True` (retry.py:161, 169), default False class attribute (protocol.py:20); the gate demands `is True` and a ProviderError instance; ProviderExhausted subclasses ProviderError (protocol.py:25). Exhausted with every attempt never-sent or 429 gives True and the gate settles 0 with code provider_refused. Names, types and the exhausted case match.

### M1 Major (new): a router's 429 is still marked on exhaustion, and the gate now settles it at 0 (under-count)
- retry.py:156 `unbilled = unbilled and (this_unsent or code == THROTTLED_STATUS)` and :169 do not look at the kind's `refused_statuses`; rule 2 was never narrowed for routers. The docstring (retry.py:35-37) says "a gate honouring it must treat that kind as unmarked", but the gate (core-c 0e33c0641) cannot know the kind (it reads only the exception) and honours it; so the safeguard the docstring relies on does not exist, and the docstring line "NOT YET CONSUMED" (retry.py:32-34, protocol.py:16-17) is now false.
- Scenario: openai_compat with base_url of OpenRouter, LiteLLM or Groq. Upstream model starts or completes work, the router answers 429 (upstream rate limit after a partial failover, or the router's own post-work limit) three times; ProviderExhausted marked True; gate settles 0; real spend (the router may bill a failed-over attempt) is unbooked. The same applies to anthropic on Vertex/Foundry (non-"api" platform): a gateway 429. The test file pins it as correct: tests/test_refused_before_response.py:252-258 (`[_http(429)] * 3` on OpenAICompatLLM asserts `refused_before_response is True`).
- Safe behaviour now: for any kind whose list is narrowed (openai_compat; anthropic when not direct_api) a 429 does not count as unbilled, only never-sent attempts do; the wide list kinds (direct Claude API, bedrock, gemini) keep rule 2.
- One-line fix: pass `throttled_unbilled: bool` (False for openai_compat and non-direct anthropic) to with_retry, or equivalently put 429 into the wide `REFUSED_STATUSES`-style set only for direct kinds and compute `unbilled and (this_unsent or code in throttled_ok)`; change test line 252-258 to expect False for the 429 case on openai_compat; fix the stale docstrings.

### Minor P1
- tests/test_refused_before_response.py 'gate-level case once core-c's gate honours the mark' (F-provider-mark RESOLUTION N7) is still not here though the gate now honours it; core-b can add one against the model_gate on origin/cloud/core-c after the merge, and it should cover the router 429 case above (expected: stays booked).
- Minor P2: core-c's model_gate.py:362-363 docstring still says "llm/retry.py sets no mark yet"; ask core-c to update (their file).
