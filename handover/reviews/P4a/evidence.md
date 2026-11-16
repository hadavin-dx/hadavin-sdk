# P4a evidence (builder; records only, no verdict). Head: see `git -C <build-dir>/P4a log -1` (core/P4a). Base: f0465df.
RUNG TABLE: BN-14 in the ticket (P4a.md build notes) holds it; I added none and replaced nothing.

## FAILURES AND SLIPS FIRST
1. Inherited failure, not P4a: `tests/test_p7_tick.py::test_cli_migrate_warns_when_new_tables_get_no_grants` fails in the py3.13 full suite (1 failed, 10176 passed, 561 skipped) with "refused: give --reset-role or set limits.reset_group". It fails identically on base f0465df (single-test run on the base worktree). It belongs to the P2a-1 stack; the P2a-1 builder is fixing it; not fixed here (lead order).
2. bandit -ll exits 1 on one Medium/Low-confidence finding B608 at src/hadavin_sdk/store/postgres.py:768. It exists on base f0465df too (same file, same line, run on the base worktree). File is not in the P4a diff. Not fixed here (P4d/store code); needs the owner of that file.
3. Slip: first full-suite run used `-n0` with no xdist (rc=4), re-run without it. Slip: a chained `&&` hid ruff's exit status once, so a commit carried unused-noqa/import issues; fixed in a follow-up commit.
4. Slip: the E0 probes (below) were run AFTER the code was written, on base and head, not before building. They are unchanged between the two, so they show the old facts still hold and nothing P4a did moved them.
5. Ticket count mismatch: ticket says 38 + 48 = 86 mutants; its tables list 36 + 47 + a2-62 and BN-11 adds a1-30/31. I ran 87 (the 86 plus an extra a1-25b, the other `__reduce__`).
6. Mutant killers: every mutant is killed (below) but by the test named in the table only where noted; differences: a2-27 is killed first by U4 not C14(b); a2-27b by U3b not C14(b); a2-28 by C7(d) (as named). The harness runs four test files together with -x, so "first failure" is the first in file order, not proof that no other row fails; I did not run each mutant against each named row alone.

## What was NOT run
- No live model call, no spend. No Postgres-backed job beyond what the full suite does. No CodeQL/SonarCloud/CodeRabbit (CI, after the PR).
- E0 probe 1 and 2 (Anthropic usage deleted via wire harness; Bedrock Stubber) were not re-run as separate scripts; their facts are covered by rows U1/C-rows that pass.
- Diff scope: files listed below; I did not check each against the ticket's file list line by line (P4a-1 files such as backends/table.py, llm/__init__.py, tests/contracts/test_cost_rounding.py, tests/warden_port/test_providers.py are P4a-1 changes).
- uv-based runs: used the shared venvs (venv313, venv312) with PYTHONPATH=src, not `uv run`.
- Mutants were not run on py3.12.

## Commands and results
### Head and diff scope
c86e685 P4a-2: tests import on the base tree (local stub helper, cap stand-in)
8abe234 P4a-2: shim Usage so the fail-before run fails by assertion
f3227f2 P4a-2: tests for the cache classes, pricing words, request counts, k1b bookings, replay guards, zero prices
f349f0b P4a-2: ruff fixes (unused noqa)
781b8ba P4a-2: cache classes read and refused, pricing words, request_bound, k1b whole-call bookings, replay guards, zero-price load check
df80c12 P4a-1: refuse instead of estimate (Usage, UsageMissing, exact cost_usd, one upward rounding)
 CHANGELOG.md                             |    2 +
 demos/ask-your-data/askdata/pipeline.py  |    4 +-
 src/hadavin_sdk/backends/table.py        |    4 +-
 src/hadavin_sdk/config.py                |   16 +
 src/hadavin_sdk/defaults.py              |   19 +
 src/hadavin_sdk/k1b/loop.py              |   54 +-
 src/hadavin_sdk/k1b/replay.py            |   22 +-
 src/hadavin_sdk/llm/__init__.py          |   18 +-
 src/hadavin_sdk/llm/anthropic.py         |   36 +-
 src/hadavin_sdk/llm/bedrock.py           |   18 +-
 src/hadavin_sdk/llm/common.py            |   61 +-
 src/hadavin_sdk/llm/fake.py              |   24 +-
 src/hadavin_sdk/llm/gemini.py            |   47 +-
 src/hadavin_sdk/llm/openai_compat.py     |   46 +-
 src/hadavin_sdk/llm/pricing.py           |   74 ++
 src/hadavin_sdk/llm/protocol.py          |   93 ++-
 src/hadavin_sdk/models.py                |   31 +
 tests/contracts/kinds/llm_wire.py        |  118 +++-
 tests/contracts/test_cost_rounding.py    |   10 +-
 tests/contracts/test_llm.py              |   35 +
 tests/demo_askdata/test_usage_missing.py |   81 +++
 tests/k1b_support.py                     |   11 +
 tests/test_usage_classes.py              |  914 +++++++++++++++++++++++++
 tests/test_usage_refuse.py               | 1078 ++++++++++++++++++++++++++++++
 tests/warden_port/test_providers.py      |   13 +-
 25 files changed, 2730 insertions(+), 99 deletions(-)

### Full suite py3.13 (full313.log, last lines)
FAILED tests/test_p7_tick.py::test_cli_migrate_warns_when_new_tables_get_no_grants
1 failed, 10176 passed, 561 skipped in 303.59s (0:05:03)
rc=1

### Full suite py3.12 (full312.log, last lines)
FAILED tests/test_p7_tick.py::test_cli_migrate_warns_when_new_tables_get_no_grants
1 failed, 10176 passed, 561 skipped in 298.13s (0:04:58)
rc=1

### ruff / bandit (lint.txt)
## ruff check
All checks passed!
rc=0
## ruff format --check
320 files already formatted
rc=0
## bandit -ll
		Medium: 1
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 1
		Medium: 2
		High: 5
Files skipped (0):
rc=1
bandit on base f0465df store/postgres.py: same B608 finding (Medium severity, Low confidence) at :768.

### ConfigError( delta (BN-9/10): replay.py 6 -> 9 (+3); src/ 179 -> 182 (+3), measured on this tree
### BN-12 encode( in k1b/: bundle.py:123, causelist.py:53 (load-time), loop.py:126 and replay.py:67 (surrogatepass), tools.py:221/:238 (render of bundle records; no model text; the filter name is compared, never echoed). Nothing can hold model text.

### BN-16 price pin
# BN-16 price pin (step run 2026-11-06, read from the vendor page by WebFetch)
Source URL for every row: https://platform.claude.com/docs/en/about-claude/pricing
Date read: 2026-11-06. The page shows no "last updated" date of its own; the read date is the date pinned.
USD per million tokens, exact decimals as printed (base rows, standard tier):
| model (as the page names it)              | input | output | cache read | 5m write | 1h write |
| Claude Opus 5.5                           | 4     | 20     | 0.20       | 5        | 8        |
| Claude Sonnet 5.5                         | 2     | 10     | 0.10       | 2.50     | 4        |
| Claude Haiku 5.5, prompt up to 100,000    | 0.10  | 0.50   | 0.01       | 0.125    | 0.20     |
| Claude Haiku 5.5, prompt over 100,000     | 0.50  | 2.50   | 0.05       | 0.625    | 1        |
Cross-check: matches the 2026-11-04 figures in the studio rule model-choice-and-cost-follow-bible (Haiku 0.10/0.50 and 0.50/2.50, Sonnet 2/10, Opus 4/20). litellm file not used.
Notes (honest): (1) The repo itself holds no price table: prices come from config, so this pin is evidence only and nothing was written into src. "Models we price" = the three the studio rules route to. (2) Haiku has two price bands by prompt size; one config Route holds one rate pair, so a Haiku route configured at 0.10/0.50 under-prices prompts over 100,000 tokens. P4a does not change this; it is a config choice the operator must make (use the upper band for a safe bound). (3) Cache-read and cache-write prices are listed but P4a refuses non-zero cache counts instead of pricing them.

### Old code, new data (cache_read_tokens: 0 recording)
OLD f0465df: RAISED ValidationError (Reply cache_read_tokens: Extra inputs are not permitted)
HEAD: ACCEPTED, cost 0.000035

### E0 probes (run late; identical on base and head)
'NaN' refused ValidationError
'sNaN' refused ValidationError
'Infinity' refused ValidationError
'-Infinity' refused ValidationError
'-1' refused ValidationError
'0' accepted
'-0' refused ValidationError
'1e30' refused ValidationError
'1001' accepted
'' refused ValidationError
'True' refused ValidationError
'3.123457' accepted
'1.0000001' refused ValidationError
True(bool) refused ValidationError
anthropic Usage(input=1,output=2).model_dump(): {'cache_creation': None, 'cache_creation_input_tokens': None, 'cache_read_input_tokens': None, 'inference_geo': None, 'input_tokens': 1, 'output_tokens': 2, 'output_tokens_

### Class guard U8
=========================== short test summary info ============================
PASSED tests/test_usage_refuse.py::test_u8_no_llm_module_turns_a_missing_count_into_a_number
PASSED tests/test_usage_refuse.py::test_u8_each_form_is_caught_in_a_planted_file[or]
PASSED tests/test_usage_refuse.py::test_u8_each_form_is_caught_in_a_planted_file[get]
PASSED tests/test_usage_refuse.py::test_u8_each_form_is_caught_in_a_planted_file[not]
PASSED tests/test_usage_refuse.py::test_u8_each_form_is_caught_in_a_planted_file[or on a Gemini field]
PASSED tests/test_usage_refuse.py::test_u8_max_tokens_is_exempt_and_get_with_none_is_fine
6 passed, 209 deselected in 1.64s
rc=0

### Fail-before on base f0465df (286 failed, 100 passed, 1 skipped). Failed tests:
FAILED tests/contracts/test_llm.py::test_cache_and_thinking_counts_on_every_wire[anthropic.api]
FAILED tests/contracts/test_llm.py::test_cache_and_thinking_counts_on_every_wire[anthropic.foundry]
FAILED tests/contracts/test_llm.py::test_cache_and_thinking_counts_on_every_wire[anthropic.vertex]
FAILED tests/contracts/test_llm.py::test_cache_and_thinking_counts_on_every_wire[bedrock]
FAILED tests/contracts/test_llm.py::test_cache_and_thinking_counts_on_every_wire[gemini]
FAILED tests/contracts/test_llm.py::test_cache_and_thinking_counts_on_every_wire[openai_compat]
FAILED tests/demo_askdata/test_usage_missing.py::test_c16a_a_failed_request_two_after_an_answered_request_one_is_booked_not_free
FAILED tests/demo_askdata/test_usage_missing.py::test_usage_missing_is_charged_exactly_what_a_billed_failure_is
FAILED tests/test_usage_classes.py::test_c12_reply_and_answer_shape_and_one_price_formula
FAILED tests/test_usage_classes.py::test_c13a_usage_missing_one_request_one_attempt_books_w
FAILED tests/test_usage_classes.py::test_c13b_b2_the_factor_is_requests_times_attempts
FAILED tests/test_usage_classes.py::test_c13c_an_abandoned_call_books_the_whole_call_maximum[declare0-6]
FAILED tests/test_usage_classes.py::test_c13c_an_abandoned_call_books_the_whole_call_maximum[declare1-1]
FAILED tests/test_usage_classes.py::test_c13d2_provider_exhausted_books_the_whole_call_maximum
FAILED tests/test_usage_classes.py::test_c13d_a_plain_provider_error_books_the_whole_call_maximum
FAILED tests/test_usage_classes.py::test_c13e_unpriced_usage_is_booked_as_a_usage_missing
FAILED tests/test_usage_classes.py::test_c13g1_an_object_that_declares_nothing_is_booked_the_fallbacks
FAILED tests/test_usage_classes.py::test_c13g2_a_bad_declared_value_is_booked_the_fallback_for_that_factor
FAILED tests/test_usage_classes.py::test_c13g_charge_factor_is_total
FAILED tests/test_usage_classes.py::test_c13h_recording_llm_forwards_the_inner_declarations
FAILED tests/test_usage_classes.py::test_c13h_the_fallbacks_are_not_below_any_declaration
FAILED tests/test_usage_classes.py::test_c13j_a_failed_request_two_books_six_w_whatever_the_cause[j1]
FAILED tests/test_usage_classes.py::test_c13j_a_failed_request_two_books_six_w_whatever_the_cause[j2]
FAILED tests/test_usage_classes.py::test_c13j_a_failed_request_two_books_six_w_whatever_the_cause[j3]
FAILED tests/test_usage_classes.py::test_c13j_a_failed_request_two_books_six_w_whatever_the_cause[j4i]
FAILED tests/test_usage_classes.py::test_c13j_a_failed_request_two_books_six_w_whatever_the_cause[j4ii]
FAILED tests/test_usage_classes.py::test_c13j_a_failed_request_two_books_six_w_whatever_the_cause[j6-408]
FAILED tests/test_usage_classes.py::test_c13j_a_failed_request_two_books_six_w_whatever_the_cause[j6-429]
FAILED tests/test_usage_classes.py::test_c13j_a_failed_request_two_books_six_w_whatever_the_cause[j6-unknown]
FAILED tests/test_usage_classes.py::test_c13j_a_failed_request_two_books_six_w_whatever_the_cause[j7-decimal]
FAILED tests/test_usage_classes.py::test_c13j_a_failed_request_two_books_six_w_whatever_the_cause[j7-nocause]
FAILED tests/test_usage_classes.py::test_c13k_a_lone_surrogate_in_a_tool_call_input_does_not_crash_the_booking
FAILED tests/test_usage_classes.py::test_c13k_clause_2_the_audit_hash_of_a_tool_name_with_a_lone_surrogate
FAILED tests/test_usage_classes.py::test_c13p_clause_2_the_rounding_goes_up_once_on_the_exact_product
FAILED tests/test_usage_classes.py::test_c13p_the_pure_function_literals
FAILED tests/test_usage_classes.py::test_c13q_bytes_not_characters_and_the_surrogate_counts_three_bytes
FAILED tests/test_usage_classes.py::test_c14b_the_loop_sends_exactly_the_declared_number_of_requests
FAILED tests/test_usage_classes.py::test_c16_a_failed_request_two_is_a_usage_missing_chained_from_the_real_error[i-exhausted]
FAILED tests/test_usage_classes.py::test_c16_a_failed_request_two_is_a_usage_missing_chained_from_the_real_error[ii-http-400]
FAILED tests/test_usage_classes.py::test_c16_a_failed_request_two_is_a_usage_missing_chained_from_the_real_error[iii-unparsable]
FAILED tests/test_usage_classes.py::test_c16_iv_a_usage_missing_of_request_two_is_not_wrapped
FAILED tests/test_usage_classes.py::test_c18a_a_real_kind_label_is_refused_before_anything_is_written
FAILED tests/test_usage_classes.py::test_c18b_a_detector_kind_other_than_regex_and_llm_judge_is_refused
FAILED tests/test_usage_classes.py::test_c18c_a_network_object_under_the_fake_label_is_refused
FAILED tests/test_usage_classes.py::test_c2_anthropic_cache_fields_null_zero_or_absent_price_as_two_counts
FAILED tests/test_usage_classes.py::test_c2_bedrock_zero_cache_counts_price_as_two_counts
FAILED tests/test_usage_classes.py::test_c2_fb_a_cached_reply_on_a_flat_route_is_not_returned_at_the_flat_cost
FAILED tests/test_usage_classes.py::test_c3_and_c9_zero_cache_keys_load_and_are_dropped_before_the_reply
FAILED tests/test_usage_classes.py::test_c3_anthropic_non_zero_cache_class_is_unpriced[classes0-cache_write_tokens]
FAILED tests/test_usage_classes.py::test_c3_anthropic_non_zero_cache_class_is_unpriced[classes1-cache_read_tokens]
FAILED tests/test_usage_classes.py::test_c3_anthropic_non_zero_cache_class_is_unpriced[classes2-cache_write_tokens]
FAILED tests/test_usage_classes.py::test_c3_bedrock_non_zero_cache_class_is_unpriced[cacheReadInputTokens-cache_read_tokens]
FAILED tests/test_usage_classes.py::test_c3_bedrock_non_zero_cache_class_is_unpriced[cacheWriteInputTokens-cache_write_tokens]
FAILED tests/test_usage_classes.py::test_c3_fake_recording_with_a_non_zero_cache_key_is_unpriced[cache_read_tokens]
FAILED tests/test_usage_classes.py::test_c3_fake_recording_with_a_non_zero_cache_key_is_unpriced[cache_write_tokens]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed[''-service_tier]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed[''-speed]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['Priority'-service_tier]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['Priority'-speed]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['Standard'-service_tier]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['Standard'-speed]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['batch'-service_tier]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['batch'-speed]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['canary-valu-service_tier]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['canary-valu-speed]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['fast'-service_tier]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['fast'-speed]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['priority'-service_tier]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['priority'-speed]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['standard '-service_tier]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['standard '-speed]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['xxxxxxxxxxx-service_tier]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['xxxxxxxxxxx-speed]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed[7-service_tier]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed[7-speed]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed[True-service_tier]
FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed[True-speed]
FAILED tests/test_usage_classes.py::test_c3d_check_facts_directly_and_reply_calls_it
FAILED tests/test_usage_classes.py::test_c7d_every_kind_declares_its_request_count_whatever_max_attempts_is
FAILED tests/test_usage_classes.py::test_c7e_request_bound_is_strict
FAILED tests/test_usage_classes.py::test_c8b_a_zero_price_is_refused_at_load_for_every_real_kind[0-0-anthropic]
FAILED tests/test_usage_classes.py::test_c8b_a_zero_price_is_refused_at_load_for_every_real_kind[0-0-bedrock]
FAILED tests/test_usage_classes.py::test_c8b_a_zero_price_is_refused_at_load_for_every_real_kind[0-0-gemini]
FAILED tests/test_usage_classes.py::test_c8b_a_zero_price_is_refused_at_load_for_every_real_kind[0-0-openai_compat]
FAILED tests/test_usage_classes.py::test_c8b_a_zero_price_is_refused_at_load_for_every_real_kind[0-15.00-anthropic]
FAILED tests/test_usage_classes.py::test_c8b_a_zero_price_is_refused_at_load_for_every_real_kind[0-15.00-bedrock]
FAILED tests/test_usage_classes.py::test_c8b_a_zero_price_is_refused_at_load_for_every_real_kind[0-15.00-gemini]
FAILED tests/test_usage_classes.py::test_c8b_a_zero_price_is_refused_at_load_for_every_real_kind[0-15.00-openai_compat]
FAILED tests/test_usage_classes.py::test_c8b_a_zero_price_is_refused_at_load_for_every_real_kind[3.00-0-anthropic]
FAILED tests/test_usage_classes.py::test_c8b_a_zero_price_is_refused_at_load_for_every_real_kind[3.00-0-bedrock]
FAILED tests/test_usage_classes.py::test_c8b_a_zero_price_is_refused_at_load_for_every_real_kind[3.00-0-gemini]
FAILED tests/test_usage_classes.py::test_c8b_a_zero_price_is_refused_at_load_for_every_real_kind[3.00-0-openai_compat]
FAILED tests/test_usage_classes.py::test_c9_a_count_at_the_cap_loads_and_above_it_is_invalid
FAILED tests/test_usage_classes.py::test_c9_reply_usage_is_read_only_and_equals_the_two_counts
FAILED tests/test_usage_refuse.py::test_u13_usage_accepts_the_cap_sums_the_prompt_and_is_frozen
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[0-'1']
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[0--1]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[0-1.0]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[0-1000000001]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[0-None]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[0-True]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[1-'1']
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[1--1]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[1-1.0]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[1-1000000001]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[1-None]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[1-True]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[2-'1']
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[2--1]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[2-1.0]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[2-1000000001]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[2-None]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[2-True]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[3-'1']
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[3--1]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[3-1.0]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[3-1000000001]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[3-None]
FAILED tests/test_usage_refuse.py::test_u13_usage_refuses_a_bad_count_in_any_class[3-True]
FAILED tests/test_usage_refuse.py::test_u14_cost_usd_is_exact_over_seeded_cases
FAILED tests/test_usage_refuse.py::test_u14_max_case_at_the_price_bound_is_exact
FAILED tests/test_usage_refuse.py::test_u14_max_case_rounding_goes_up
FAILED tests/test_usage_refuse.py::test_u14b_an_exact_eight_decimal_cost_is_unchanged_and_cost_usd_does_not_round
FAILED tests/test_usage_refuse.py::test_u14b_every_producer_rounds_the_exact_cost_up_once
FAILED tests/test_usage_refuse.py::test_u14c_a_nan_or_infinite_price_is_a_value_error_not_a_provider_error
FAILED tests/test_usage_refuse.py::test_u14c_a_signalling_nan_price_is_usage_missing_invalid
FAILED tests/test_usage_refuse.py::test_u1_a_usage_that_is_not_an_object_is_absent[7]
FAILED tests/test_usage_refuse.py::test_u1_a_usage_that_is_not_an_object_is_absent[bad0]
FAILED tests/test_usage_refuse.py::test_u1_a_usage_that_is_not_an_object_is_absent[usage]
FAILED tests/test_usage_refuse.py::test_u1_absent_usage_is_refused_with_one_request[anthropic.api]
FAILED tests/test_usage_refuse.py::test_u1_absent_usage_is_refused_with_one_request[anthropic.foundry]
FAILED tests/test_usage_refuse.py::test_u1_absent_usage_is_refused_with_one_request[anthropic.vertex]
FAILED tests/test_usage_refuse.py::test_u1_absent_usage_is_refused_with_one_request[gemini]
FAILED tests/test_usage_refuse.py::test_u1_absent_usage_is_refused_with_one_request[openai_compat]
FAILED tests/test_usage_refuse.py::test_u1_bedrock_absent_usage_is_refused_with_one_call
FAILED tests/test_usage_refuse.py::test_u2_a_blocked_gemini_prompt_has_output_zero
FAILED tests/test_usage_refuse.py::test_u2_a_zero_output_on_an_empty_reply_is_kept[anthropic.api]
FAILED tests/test_usage_refuse.py::test_u2_a_zero_output_on_an_empty_reply_is_kept[anthropic.foundry]
FAILED tests/test_usage_refuse.py::test_u2_a_zero_output_on_an_empty_reply_is_kept[anthropic.vertex]
FAILED tests/test_usage_refuse.py::test_u2_a_zero_output_on_an_empty_reply_is_kept[gemini]
FAILED tests/test_usage_refuse.py::test_u2_a_zero_output_on_an_empty_reply_is_kept[openai_compat]
FAILED tests/test_usage_refuse.py::test_u2_bedrock_a_zero_output_on_an_empty_reply_is_kept
FAILED tests/test_usage_refuse.py::test_u2b_a_cache_count_is_unpriced_and_checked_before_zero_input[usage_kw0-cache_write_tokens]
FAILED tests/test_usage_refuse.py::test_u2b_a_cache_count_is_unpriced_and_checked_before_zero_input[usage_kw1-cache_read_tokens]
FAILED tests/test_usage_refuse.py::test_u2b_a_free_route_accepts_a_zero_input_at_cost_zero
FAILED tests/test_usage_refuse.py::test_u2b_cost_usd_refuses_a_zero_input_on_a_priced_route
FAILED tests/test_usage_refuse.py::test_u2b_through_chat_a_zero_input_is_refused[anthropic.api]
FAILED tests/test_usage_refuse.py::test_u2b_through_chat_a_zero_input_is_refused[anthropic.foundry]
FAILED tests/test_usage_refuse.py::test_u2b_through_chat_a_zero_input_is_refused[anthropic.vertex]
FAILED tests/test_usage_refuse.py::test_u2b_through_chat_a_zero_input_is_refused[gemini]
FAILED tests/test_usage_refuse.py::test_u2b_through_chat_a_zero_input_is_refused[openai_compat]
FAILED tests/test_usage_refuse.py::test_u2c_bedrock_zero_output_with_content_is_refused[text]
FAILED tests/test_usage_refuse.py::test_u2c_bedrock_zero_output_with_content_is_refused[tool_call]
FAILED tests/test_usage_refuse.py::test_u2c_zero_output_with_a_tool_call_is_refused[anthropic.api]
FAILED tests/test_usage_refuse.py::test_u2c_zero_output_with_a_tool_call_is_refused[anthropic.foundry]
FAILED tests/test_usage_refuse.py::test_u2c_zero_output_with_a_tool_call_is_refused[anthropic.vertex]
FAILED tests/test_usage_refuse.py::test_u2c_zero_output_with_a_tool_call_is_refused[gemini]
FAILED tests/test_usage_refuse.py::test_u2c_zero_output_with_a_tool_call_is_refused[openai_compat]
FAILED tests/test_usage_refuse.py::test_u2c_zero_output_with_text_is_refused[anthropic.api]
FAILED tests/test_usage_refuse.py::test_u2c_zero_output_with_text_is_refused[anthropic.foundry]
FAILED tests/test_usage_refuse.py::test_u2c_zero_output_with_text_is_refused[anthropic.vertex]
FAILED tests/test_usage_refuse.py::test_u2c_zero_output_with_text_is_refused[gemini]
FAILED tests/test_usage_refuse.py::test_u2c_zero_output_with_text_is_refused[openai_compat]
FAILED tests/test_usage_refuse.py::test_u3_anthropic_null_counts_reach_the_check_from_the_wire
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[input-'']
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[input-'7']
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[input--1]
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[input-1000000000000000000]
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[input-7.0]
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[input-9223372036854775808]
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[input-False]
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[input-True]
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[input-[]]
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[input-{}]
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[output-'']
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[output-'7']
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[output--1]
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[output-1000000000000000000]
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[output-7.0]
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[output-9223372036854775808]
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[output-False]
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[output-True]
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[output-[]]
FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[output-{}]
FAILED tests/test_usage_refuse.py::test_u3_anthropic_usage_that_is_missing_or_not_an_object
FAILED tests/test_usage_refuse.py::test_u3_boundary_exactly_the_cap_is_accepted_and_one_more_is_refused[gemini]
FAILED tests/test_usage_refuse.py::test_u3_boundary_exactly_the_cap_is_accepted_and_one_more_is_refused[openai_compat]
FAILED tests/test_usage_refuse.py::test_u3_checked_count_boundary_and_forms
FAILED tests/test_usage_refuse.py::test_u3_gemini_a_bad_total_is_invalid[-1]
FAILED tests/test_usage_refuse.py::test_u3_gemini_a_bad_total_is_invalid[1.5]
FAILED tests/test_usage_refuse.py::test_u3_gemini_a_bad_total_is_invalid[5]
FAILED tests/test_usage_refuse.py::test_u3_gemini_a_bad_total_is_invalid[True]
FAILED tests/test_usage_refuse.py::test_u3_gemini_missing_candidates_count_is_zero_only_for_a_blocked_prompt
FAILED tests/test_usage_refuse.py::test_u3_gemini_missing_candidates_count_with_a_candidate_is_absent[cut off by SAFETY]
FAILED tests/test_usage_refuse.py::test_u3_gemini_missing_candidates_count_with_a_candidate_is_absent[empty text]
FAILED tests/test_usage_refuse.py::test_u3_gemini_missing_candidates_count_with_a_candidate_is_absent[text, no thoughts count]
FAILED tests/test_usage_refuse.py::test_u3_gemini_missing_candidates_count_with_a_candidate_is_absent[text, thoughts count]
FAILED tests/test_usage_refuse.py::test_u3_gemini_missing_candidates_count_with_a_candidate_is_absent[thoughts only]
FAILED tests/test_usage_refuse.py::test_u3_gemini_missing_prompt_count_is_absent
FAILED tests/test_usage_refuse.py::test_u3_gemini_the_total_can_raise_the_output_count
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-''-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-''-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-'7'-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-'7'-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini--1-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini--1-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-1000000000000000000-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-1000000000000000000-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-7.0-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-7.0-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-9223372036854775808-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-9223372036854775808-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-False-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-False-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-None-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-None-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-True-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-True-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-[]-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-[]-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-{}-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-{}-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-''-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-''-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-'7'-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-'7'-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat--1-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat--1-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-1000000000000000000-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-1000000000000000000-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-7.0-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-7.0-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-9223372036854775808-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-9223372036854775808-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-False-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-False-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-None-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-None-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-True-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-True-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-[]-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-[]-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-{}-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-{}-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[''-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[''-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat['7'-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat['7'-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[-1-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[-1-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[1000000000000000000-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[1000000000000000000-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[7.0-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[7.0-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[9223372036854775808-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[9223372036854775808-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[False-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[False-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[None-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[None-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[True-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[True-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[[]-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[[]-output]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[{}-input]
FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_through_bedrock_chat[{}-output]
FAILED tests/test_usage_refuse.py::test_u3b_build_usage_and_add_usage_refuse_with_typed_errors
FAILED tests/test_usage_refuse.py::test_u3b_the_same_sum_through_two_openai_requests_is_a_typed_refusal
FAILED tests/test_usage_refuse.py::test_u4_a_zero_on_one_request_is_refused_before_the_sum_hides_it[both report 0 with text]
FAILED tests/test_usage_refuse.py::test_u4_a_zero_on_one_request_is_refused_before_the_sum_hides_it[clause 1: request 1 output 0]
FAILED tests/test_usage_refuse.py::test_u4_a_zero_on_one_request_is_refused_before_the_sum_hides_it[clause 2: request 1 input 0]
FAILED tests/test_usage_refuse.py::test_u4_a_zero_on_one_request_is_refused_before_the_sum_hides_it[clause 3: request 2 output 0]
FAILED tests/test_usage_refuse.py::test_u4_a_zero_on_one_request_is_refused_before_the_sum_hides_it[clause 4: request 2 input 0]
FAILED tests/test_usage_refuse.py::test_u4_the_first_without_usage_sends_no_second_request
FAILED tests/test_usage_refuse.py::test_u4_the_second_without_usage_is_refused_after_two_requests
FAILED tests/test_usage_refuse.py::test_u5_a_boolean_count_is_invalid
FAILED tests/test_usage_refuse.py::test_u5_a_recording_at_the_cap_loads_and_one_above_is_refused
FAILED tests/test_usage_refuse.py::test_u5_a_recording_without_a_count_is_refused[input_tokens]
FAILED tests/test_usage_refuse.py::test_u5_a_recording_without_a_count_is_refused[output_tokens]
FAILED tests/test_usage_refuse.py::test_u5_every_recorded_reply_in_the_repo_still_loads
FAILED tests/test_usage_refuse.py::test_u5_input_zero_on_a_priced_route_is_implausible_and_on_a_free_route_is_fine
FAILED tests/test_usage_refuse.py::test_u7_a_reason_or_field_outside_the_closed_lists_is_a_programming_error
FAILED tests/test_usage_refuse.py::test_u7_the_error_message_holds_no_reply_text_or_value
FAILED tests/test_usage_refuse.py::test_u7_the_format_is_fixed_with_and_without_a_field
FAILED tests/test_usage_refuse.py::test_u8_no_llm_module_turns_a_missing_count_into_a_number
FAILED tests/test_usage_refuse.py::test_u9_reply_takes_no_sent_and_never_estimates

Passing on base (regression pins):
tests/test_usage_classes.py::test_c9_old_recording_loads_and_a_thinking_key_is_refused
tests/test_usage_classes.py::test_c3d_pricing_words_standard_absent_and_null_are_accepted[None-service_tier]
tests/test_usage_classes.py::test_c3d_pricing_words_standard_absent_and_null_are_accepted[None-speed]
tests/test_usage_classes.py::test_c3d_pricing_words_standard_absent_and_null_are_accepted[absent-service_tier]
tests/test_usage_classes.py::test_c3d_pricing_words_standard_absent_and_null_are_accepted[absent-speed]
tests/test_usage_classes.py::test_c3d_pricing_words_standard_absent_and_null_are_accepted[standard-service_tier]
tests/test_usage_classes.py::test_c3d_pricing_words_standard_absent_and_null_are_accepted[standard-speed]
tests/test_usage_classes.py::test_c4_gemini_thoughts_are_counted_once
tests/test_usage_classes.py::test_c12_the_guard_catches_a_planted_formula
tests/test_usage_classes.py::test_c8b_small_prices_load_on_every_real_kind[anthropic]
tests/test_usage_classes.py::test_c8b_small_prices_load_on_every_real_kind[bedrock]
tests/test_usage_classes.py::test_c8b_small_prices_load_on_every_real_kind[gemini]
tests/test_usage_classes.py::test_c8b_small_prices_load_on_every_real_kind[openai_compat]
tests/test_usage_classes.py::test_c8b_the_fake_kind_may_carry_a_zero_price
tests/test_usage_classes.py::test_c8_a_bool_price_and_the_empty_string_are_refused
tests/test_usage_classes.py::test_c10_config_hash_is_the_same_as_before_for_valid_prices
tests/test_usage_classes.py::test_c13f_no_prices_books_nothing_and_raises_nothing[<lambda>0]
tests/test_usage_classes.py::test_c13f_no_prices_books_nothing_and_raises_nothing[<lambda>1]
tests/test_usage_classes.py::test_c13f_no_prices_books_nothing_and_raises_nothing[<lambda>2]
tests/test_usage_classes.py::test_c13f_an_abandoned_call_without_prices_books_nothing
tests/test_usage_classes.py::test_c16_counter_request_one_failing_keeps_its_original_error[i-exhausted]
tests/test_usage_classes.py::test_c16_counter_request_one_failing_keeps_its_original_error[ii-http-400]
tests/test_usage_classes.py::test_c16_counter_request_one_failing_keeps_its_original_error[iii-unparsable]
tests/test_usage_refuse.py::test_u2c_one_output_token_with_text_is_accepted[anthropic.api]
tests/test_usage_refuse.py::test_u2c_one_output_token_with_text_is_accepted[anthropic.vertex]
tests/test_usage_refuse.py::test_u2c_one_output_token_with_text_is_accepted[anthropic.foundry]
tests/test_usage_refuse.py::test_u2c_one_output_token_with_text_is_accepted[openai_compat]
tests/test_usage_refuse.py::test_u2c_one_output_token_with_text_is_accepted[gemini]
tests/test_usage_refuse.py::test_u3_gemini_malformed_function_call_stays_a_plain_provider_error
tests/test_usage_refuse.py::test_u3_gemini_a_missing_or_low_total_is_accepted_without_a_cross_check[None]
tests/test_usage_refuse.py::test_u3_gemini_a_missing_or_low_total_is_accepted_without_a_cross_check[100]
tests/test_usage_refuse.py::test_u3_gemini_a_missing_or_low_total_is_accepted_without_a_cross_check[307]
tests/test_usage_refuse.py::test_u3_gemini_a_missing_or_low_total_is_accepted_without_a_cross_check[250]
tests/test_usage_refuse.py::test_u4_both_requests_carry_usage_and_the_totals_are_the_sums
tests/test_usage_refuse.py::test_u4_one_empty_request_reporting_zero_is_accepted_and_summed
tests/test_usage_refuse.py::test_u5_with_both_counts_the_cost_is_the_formula_and_zero_is_allowed
tests/test_usage_refuse.py::test_u5_the_output_zero_rule_does_not_apply_to_a_hand_made_recording
tests/test_usage_refuse.py::test_u8_each_form_is_caught_in_a_planted_file[or]
tests/test_usage_refuse.py::test_u8_each_form_is_caught_in_a_planted_file[get]
tests/test_usage_refuse.py::test_u8_each_form_is_caught_in_a_planted_file[not]
tests/test_usage_refuse.py::test_u8_each_form_is_caught_in_a_planted_file[or on a Gemini field]
tests/test_usage_refuse.py::test_u8_max_tokens_is_exempt_and_get_with_none_is_fine
tests/test_usage_refuse.py::test_u10_class_relations
tests/test_usage_refuse.py::test_u10_pickle_and_copy_keep_type_reason_field_and_text[<lambda>0]
tests/test_usage_refuse.py::test_u10_pickle_and_copy_keep_type_reason_field_and_text[<lambda>1]
tests/test_usage_refuse.py::test_u10_the_agent_loop_ends_needs_person_provider_error_after_one_call
tests/contracts/test_llm.py::test_a_tool_call_becomes_a_toolcall_priced_from_the_route[anthropic.api]
tests/contracts/test_llm.py::test_a_tool_call_becomes_a_toolcall_priced_from_the_route[anthropic.foundry]
tests/contracts/test_llm.py::test_a_tool_call_becomes_a_toolcall_priced_from_the_route[anthropic.vertex]
tests/contracts/test_llm.py::test_a_tool_call_becomes_a_toolcall_priced_from_the_route[bedrock]
tests/contracts/test_llm.py::test_a_tool_call_becomes_a_toolcall_priced_from_the_route[gemini]
tests/contracts/test_llm.py::test_a_tool_call_becomes_a_toolcall_priced_from_the_route[openai_compat]
tests/contracts/test_llm.py::test_output_schema_is_a_forced_tool_call[anthropic.api]
tests/contracts/test_llm.py::test_output_schema_is_a_forced_tool_call[anthropic.foundry]
tests/contracts/test_llm.py::test_output_schema_is_a_forced_tool_call[anthropic.vertex]
tests/contracts/test_llm.py::test_output_schema_is_a_forced_tool_call[bedrock]
tests/contracts/test_llm.py::test_output_schema_is_a_forced_tool_call[gemini]
tests/contracts/test_llm.py::test_output_schema_is_a_forced_tool_call[openai_compat]
tests/contracts/test_llm.py::test_a_text_answer_reports_text_tokens_and_model[anthropic.api]
tests/contracts/test_llm.py::test_a_text_answer_reports_text_tokens_and_model[anthropic.foundry]
tests/contracts/test_llm.py::test_a_text_answer_reports_text_tokens_and_model[anthropic.vertex]
tests/contracts/test_llm.py::test_a_text_answer_reports_text_tokens_and_model[bedrock]
tests/contracts/test_llm.py::test_a_text_answer_reports_text_tokens_and_model[gemini]
tests/contracts/test_llm.py::test_a_text_answer_reports_text_tokens_and_model[openai_compat]
tests/contracts/test_llm.py::test_three_throttles_exhaust_after_exactly_max_attempts[anthropic.api]
tests/contracts/test_llm.py::test_three_throttles_exhaust_after_exactly_max_attempts[anthropic.foundry]
tests/contracts/test_llm.py::test_three_throttles_exhaust_after_exactly_max_attempts[anthropic.vertex]
tests/contracts/test_llm.py::test_three_throttles_exhaust_after_exactly_max_attempts[bedrock]
tests/contracts/test_llm.py::test_three_throttles_exhaust_after_exactly_max_attempts[gemini]
tests/contracts/test_llm.py::test_three_throttles_exhaust_after_exactly_max_attempts[openai_compat]
tests/contracts/test_llm.py::test_a_throttle_then_an_answer_succeeds[anthropic.api]
tests/contracts/test_llm.py::test_a_throttle_then_an_answer_succeeds[anthropic.foundry]
tests/contracts/test_llm.py::test_a_throttle_then_an_answer_succeeds[anthropic.vertex]
tests/contracts/test_llm.py::test_a_throttle_then_an_answer_succeeds[bedrock]
tests/contracts/test_llm.py::test_a_throttle_then_an_answer_succeeds[gemini]
tests/contracts/test_llm.py::test_a_throttle_then_an_answer_succeeds[openai_compat]
tests/contracts/test_llm.py::test_a_cut_off_answer_is_charged_and_its_tool_call_dropped[anthropic.api]
tests/contracts/test_llm.py::test_a_cut_off_answer_is_charged_and_its_tool_call_dropped[anthropic.foundry]
tests/contracts/test_llm.py::test_a_cut_off_answer_is_charged_and_its_tool_call_dropped[anthropic.vertex]
tests/contracts/test_llm.py::test_a_cut_off_answer_is_charged_and_its_tool_call_dropped[bedrock]
tests/contracts/test_llm.py::test_a_cut_off_answer_is_charged_and_its_tool_call_dropped[gemini]
tests/contracts/test_llm.py::test_a_cut_off_answer_is_charged_and_its_tool_call_dropped[openai_compat]
tests/contracts/test_llm.py::test_a_malformed_answer_is_a_provider_error[anthropic.api]
tests/contracts/test_llm.py::test_a_malformed_answer_is_a_provider_error[anthropic.foundry]
tests/contracts/test_llm.py::test_a_malformed_answer_is_a_provider_error[anthropic.vertex]
tests/contracts/test_llm.py::test_a_malformed_answer_is_a_provider_error[gemini]
tests/contracts/test_llm.py::test_a_malformed_answer_is_a_provider_error[openai_compat]
tests/contracts/test_llm.py::test_a_refused_key_fails_at_once_and_is_not_exhaustion[anthropic.api]
tests/contracts/test_llm.py::test_a_refused_key_fails_at_once_and_is_not_exhaustion[anthropic.foundry]
tests/contracts/test_llm.py::test_a_refused_key_fails_at_once_and_is_not_exhaustion[anthropic.vertex]
tests/contracts/test_llm.py::test_a_refused_key_fails_at_once_and_is_not_exhaustion[bedrock]
tests/contracts/test_llm.py::test_a_refused_key_fails_at_once_and_is_not_exhaustion[gemini]
tests/contracts/test_llm.py::test_a_refused_key_fails_at_once_and_is_not_exhaustion[openai_compat]
tests/contracts/test_llm.py::test_the_evals_gate_is_green_on_the_kinds_fixtures[anthropic.api]
tests/contracts/test_llm.py::test_the_evals_gate_is_green_on_the_kinds_fixtures[anthropic.foundry]
tests/contracts/test_llm.py::test_the_evals_gate_is_green_on_the_kinds_fixtures[anthropic.vertex]
tests/contracts/test_llm.py::test_the_evals_gate_is_green_on_the_kinds_fixtures[bedrock]
tests/contracts/test_llm.py::test_the_evals_gate_is_green_on_the_kinds_fixtures[gemini]
tests/contracts/test_llm.py::test_the_evals_gate_is_green_on_the_kinds_fixtures[openai_compat]
tests/demo_askdata/test_usage_missing.py::test_a_plain_refusal_is_still_free

### Mutants (87 of 87 killed; full unified diffs in mutants.md, pasted below)
# Mutation results (harness: scratch script; copy of the built head)

BASELINE (unmutated): rc=0 386 passed, 1 skipped in 10.49s (13s)

## a1-1: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u2b_through_chat_a_zero_input_is_refused[openai_compat]`

```diff
--- a/src/hadavin_sdk/llm/openai_compat.py
+++ b/src/hadavin_sdk/llm/openai_compat.py
@@ -164,5 +164,5 @@
             text=message.get("content") or "",
             calls=[c for c in map(_call, message.get("tool_calls") or []) if c is not None],
-            usage=build_usage(raw.get("prompt_tokens"), raw.get("completion_tokens")),
+            usage=build_usage(raw.get("prompt_tokens") or 7, raw.get("completion_tokens")),
             stop=choice.get("finish_reason"),
         )
```

## a1-2: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-None-input]`

```diff
--- a/src/hadavin_sdk/llm/protocol.py
+++ b/src/hadavin_sdk/llm/protocol.py
@@ -65,5 +65,5 @@
     float, a string), a negative, or a value above the cap is invalid. Exactly the cap is accepted."""
     if value is None:
-        raise UsageMissing("absent", field)
+        return 1
     if type(value) is not int:
         raise UsageMissing("invalid", field)
```

## a1-3a: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u1_absent_usage_is_refused_with_one_request[anthropic.api]`

```diff
--- a/src/hadavin_sdk/llm/protocol.py
+++ b/src/hadavin_sdk/llm/protocol.py
@@ -31,5 +31,5 @@
 
 
-class UsageMissing(ProviderError):
+class UsageMissing(ProviderExhausted):
     """The provider answered (so it may have billed) but the cost cannot be known or priced: no usable count, a
     count that cannot be real, or a class this core does not price. Refuse; nothing is estimated and nothing is
```

## a1-3b: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u10_the_agent_loop_ends_needs_person_provider_error_after_one_call`

```diff
--- a/src/hadavin_sdk/runtime/agent_loop.py
+++ b/src/hadavin_sdk/runtime/agent_loop.py
@@ -434,5 +434,5 @@
                 )
             except (
-                ProviderError
+                ProviderExhausted
             ) as exc:  # a refused key or request must not strand the run in WORKING
                 code = (
```

## a1-4: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-True-input]`

```diff
--- a/src/hadavin_sdk/llm/protocol.py
+++ b/src/hadavin_sdk/llm/protocol.py
@@ -66,5 +66,5 @@
     if value is None:
         raise UsageMissing("absent", field)
-    if type(value) is not int:
+    if not isinstance(value, int):
         raise UsageMissing("invalid", field)
     if value < 0:
```

## a1-5: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-9223372036854775808-input]`

```diff
--- a/src/hadavin_sdk/llm/protocol.py
+++ b/src/hadavin_sdk/llm/protocol.py
@@ -70,6 +70,4 @@
     if value < 0:
         raise UsageMissing("invalid", field)
-    if value > defaults.MAX_USAGE_TOKENS_PER_CLASS:
-        raise UsageMissing("invalid", field)
     return value
 
```

## a1-5b: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u3_boundary_exactly_the_cap_is_accepted_and_one_more_is_refused[openai_compat]`

```diff
--- a/src/hadavin_sdk/llm/protocol.py
+++ b/src/hadavin_sdk/llm/protocol.py
@@ -70,5 +70,5 @@
     if value < 0:
         raise UsageMissing("invalid", field)
-    if value > defaults.MAX_USAGE_TOKENS_PER_CLASS:
+    if value >= defaults.MAX_USAGE_TOKENS_PER_CLASS:
         raise UsageMissing("invalid", field)
     return value
```

## a1-5d: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u3_boundary_exactly_the_cap_is_accepted_and_one_more_is_refused[openai_compat]`

```diff
--- a/src/hadavin_sdk/llm/protocol.py
+++ b/src/hadavin_sdk/llm/protocol.py
@@ -70,5 +70,5 @@
     if value < 0:
         raise UsageMissing("invalid", field)
-    if value > defaults.MAX_USAGE_TOKENS_PER_CLASS:
+    if value > defaults.MAX_USAGE_TOKENS_PER_CLASS + 1:
         raise UsageMissing("invalid", field)
     return value
```

## a1-6: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[openai_compat-None-output]`

```diff
--- a/src/hadavin_sdk/llm/openai_compat.py
+++ b/src/hadavin_sdk/llm/openai_compat.py
@@ -164,5 +164,5 @@
             text=message.get("content") or "",
             calls=[c for c in map(_call, message.get("tool_calls") or []) if c is not None],
-            usage=build_usage(raw.get("prompt_tokens"), raw.get("completion_tokens")),
+            usage=build_usage(raw.get("prompt_tokens"), raw.get("completion_tokens") or 0),
             stop=choice.get("finish_reason"),
         )
```

## a1-6b: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u1_absent_usage_is_refused_with_one_request[openai_compat]`

```diff
--- a/src/hadavin_sdk/llm/openai_compat.py
+++ b/src/hadavin_sdk/llm/openai_compat.py
@@ -131,5 +131,5 @@
                 )
             except UsageMissing:
-                raise  # request 2 answered without usage stays visible as itself (its cause is not wrapped)
+                continue  # request 2 answered without usage stays visible as itself (its cause is not wrapped)
             except ProviderError as exc:
                 if n == 0:
```

## a1-6c: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u3b_build_usage_and_add_usage_refuse_with_typed_errors`

```diff
--- a/src/hadavin_sdk/llm/protocol.py
+++ b/src/hadavin_sdk/llm/protocol.py
@@ -102,5 +102,5 @@
     }
     for name, total in sums.items():
-        if total > defaults.MAX_USAGE_TOKENS_PER_CLASS:
+        if False:
             raise UsageMissing("invalid", name)
     return Usage(**sums)
```

## a1-7: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u5_a_recording_without_a_count_is_refused[input_tokens]`

```diff
--- a/src/hadavin_sdk/llm/fake.py
+++ b/src/hadavin_sdk/llm/fake.py
@@ -59,6 +59,6 @@
         )
         usage = build_usage(
-            data.get("input_tokens"),
-            data.get("output_tokens"),
+            data.get("input_tokens", 0),
+            data.get("output_tokens", 0),
             cache_write_tokens=cache_write,
             cache_read_tokens=cache_read,
```

## a1-8: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u2b_cost_usd_refuses_a_zero_input_on_a_priced_route`

```diff
--- a/src/hadavin_sdk/llm/pricing.py
+++ b/src/hadavin_sdk/llm/pricing.py
@@ -30,5 +30,5 @@
     """An input count of zero on a route with a positive input price cannot be true. The count is tested BEFORE the
     price, so a NaN price is never ordered when the count is above 0."""
-    if usage.input_tokens == 0 and route.input_usd_per_mtok > 0:
+    if False:
         raise UsageMissing("implausible_zero", "input_tokens")
 
```

## a1-8d: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u2b_a_free_route_accepts_a_zero_input_at_cost_zero`

```diff
--- a/src/hadavin_sdk/llm/pricing.py
+++ b/src/hadavin_sdk/llm/pricing.py
@@ -30,5 +30,5 @@
     """An input count of zero on a route with a positive input price cannot be true. The count is tested BEFORE the
     price, so a NaN price is never ordered when the count is above 0."""
-    if usage.input_tokens == 0 and route.input_usd_per_mtok > 0:
+    if usage.input_tokens == 0:
         raise UsageMissing("implausible_zero", "input_tokens")
 
```

## a1-8c: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u2b_a_cache_count_is_unpriced_and_checked_before_zero_input[usage_kw0-cache_write_tokens]`

```diff
--- a/src/hadavin_sdk/llm/pricing.py
+++ b/src/hadavin_sdk/llm/pricing.py
@@ -43,6 +43,6 @@
 def cost_usd(usage: Usage, route: Any) -> Decimal:
     """Exact USD for one call; never rounds. Order: cache class, then zero input, then the sum."""
+    check_input_plausible(usage, route)
     check_priceable(usage)
-    check_input_plausible(usage, route)
     ctx = decimal.Context(prec=60, traps=[decimal.Inexact, decimal.InvalidOperation])
     try:
```

## a1-8b: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u2b_cost_usd_refuses_a_zero_input_on_a_priced_route`

```diff
--- a/src/hadavin_sdk/llm/pricing.py
+++ b/src/hadavin_sdk/llm/pricing.py
@@ -44,5 +44,4 @@
     """Exact USD for one call; never rounds. Order: cache class, then zero input, then the sum."""
     check_priceable(usage)
-    check_input_plausible(usage, route)
     ctx = decimal.Context(prec=60, traps=[decimal.Inexact, decimal.InvalidOperation])
     try:
--- a/src/hadavin_sdk/llm/common.py
+++ b/src/hadavin_sdk/llm/common.py
@@ -184,4 +184,5 @@
     incomplete."""
     check_output_plausible(usage, text, calls)
+    __import__('hadavin_sdk.llm.pricing', fromlist=['x']).check_input_plausible(usage, route)
     check_facts(route, facts)
     cost = round_cost_up(cost_usd(usage, route))
```

## a1-9: KILLED
first failure: `FAILED tests/demo_askdata/test_usage_missing.py::test_usage_missing_is_charged_exactly_what_a_billed_failure_is`

```diff
--- a/demos/ask-your-data/askdata/pipeline.py
+++ b/demos/ask-your-data/askdata/pipeline.py
@@ -161,5 +161,5 @@
             except (ProviderError, OSError, TimeoutError) as err:
                 # A call that failed AFTER the request was sent is charged its worst case; a refusal is free.
-                billed = isinstance(err, ProviderExhausted | UsageMissing | OSError | TimeoutError)
+                billed = isinstance(err, ProviderExhausted | OSError | TimeoutError)
                 if billed:  # the reservation stands as the charge
                     run.cost += worst
```

## a1-10: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u7_the_error_message_holds_no_reply_text_or_value`

```diff
--- a/src/hadavin_sdk/llm/protocol.py
+++ b/src/hadavin_sdk/llm/protocol.py
@@ -67,5 +67,7 @@
         raise UsageMissing("absent", field)
     if type(value) is not int:
-        raise UsageMissing("invalid", field)
+        _e = UsageMissing("invalid", field)
+        _e.args = (f"usage missing: invalid ({field}) {value}",)
+        raise _e
     if value < 0:
         raise UsageMissing("invalid", field)
```

## a1-11: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u8_each_form_is_caught_in_a_planted_file[or]`

```diff
--- a/tests/test_usage_refuse.py
+++ b/tests/test_usage_refuse.py
@@ -835,5 +835,5 @@
         ):
             found.append(f"{node.lineno}: `not` on a token count")
-    return found
+    return []
 
 
```

## a1-11b: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u8_each_form_is_caught_in_a_planted_file[get]`

```diff
--- a/tests/test_usage_refuse.py
+++ b/tests/test_usage_refuse.py
@@ -825,5 +825,5 @@
             and isinstance(node.args[0], ast.Constant)
             and isinstance(node.args[0].value, str)
-            and _mentions_token(source, node.args[0])
+            and False
             and not (isinstance(node.args[1], ast.Constant) and node.args[1].value is None)
         ):
```

## a1-11c: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u8_each_form_is_caught_in_a_planted_file[not]`

```diff
--- a/tests/test_usage_refuse.py
+++ b/tests/test_usage_refuse.py
@@ -832,5 +832,5 @@
             isinstance(node, ast.UnaryOp)
             and isinstance(node.op, ast.Not)
-            and _mentions_token(source, node.operand)
+            and False
         ):
             found.append(f"{node.lineno}: `not` on a token count")
```

## a1-12: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-None-input]`

```diff
--- a/src/hadavin_sdk/llm/gemini.py
+++ b/src/hadavin_sdk/llm/gemini.py
@@ -99,5 +99,5 @@
         `candidatesTokenCount` is 0 only for a blocked prompt (no candidates plus a `blockReason`); anywhere else
         a candidate may have been billed for what it wrote, so it is refused."""
-        prompt = checked_count(raw.get("promptTokenCount"), "input_tokens")
+        prompt = checked_count(raw.get("promptTokenCount") or 0, "input_tokens")
         cand_raw = raw.get("candidatesTokenCount")
         cand = 0 if cand_raw is None and blocked else checked_count(cand_raw, "output_tokens")
```

## a1-12b: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u3_hostile_counts_are_refused_on_the_json_wires[gemini-None-output]`

```diff
--- a/src/hadavin_sdk/llm/gemini.py
+++ b/src/hadavin_sdk/llm/gemini.py
@@ -101,5 +101,5 @@
         prompt = checked_count(raw.get("promptTokenCount"), "input_tokens")
         cand_raw = raw.get("candidatesTokenCount")
-        cand = 0 if cand_raw is None and blocked else checked_count(cand_raw, "output_tokens")
+        cand = 0 if cand_raw is None else checked_count(cand_raw, "output_tokens")
         thoughts_raw = raw.get("thoughtsTokenCount")
         thoughts = 0 if thoughts_raw is None else checked_count(thoughts_raw, "output_tokens")
```

## a1-13: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u3_anthropic_unit_row_not_wire[input-'']`

```diff
--- a/src/hadavin_sdk/llm/anthropic.py
+++ b/src/hadavin_sdk/llm/anthropic.py
@@ -141,5 +141,5 @@
             raise UsageMissing("absent", "usage")
         usage = build_usage(
-            raw.get("input_tokens"),
+            resp.usage.input_tokens,
             raw.get("output_tokens"),
             cache_write_tokens=raw.get("cache_creation_input_tokens"),
```

## a1-15: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u14_cost_usd_is_exact_over_seeded_cases`

```diff
--- a/src/hadavin_sdk/llm/pricing.py
+++ b/src/hadavin_sdk/llm/pricing.py
@@ -53,5 +53,5 @@
             ),
             Decimal(1_000_000),
-        )
+        ).quantize(Decimal("1E-8"))
     except decimal.DecimalException as exc:
         raise UsageMissing("invalid") from exc
```

## a1-16: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u14_cost_usd_is_exact_over_seeded_cases`

```diff
--- a/src/hadavin_sdk/llm/pricing.py
+++ b/src/hadavin_sdk/llm/pricing.py
@@ -49,5 +49,5 @@
         return ctx.divide(
             ctx.add(
-                ctx.multiply(Decimal(usage.input_tokens), route.input_usd_per_mtok),
+                ctx.multiply(Decimal(usage.input_tokens), Decimal(float(route.input_usd_per_mtok))),
                 ctx.multiply(Decimal(usage.output_tokens), route.output_usd_per_mtok),
             ),
```

## a1-14: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u9_reply_takes_no_sent_and_never_estimates`

```diff
--- a/src/hadavin_sdk/llm/common.py
+++ b/src/hadavin_sdk/llm/common.py
@@ -176,4 +176,5 @@
     stop: str | None,
     started: float,
+    sent: Any = None,
     facts: Mapping[str, object] = _NO_FACTS,
 ) -> Reply:
```

## a1-20: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u2c_zero_output_with_text_is_refused[anthropic.api]`

```diff
--- a/src/hadavin_sdk/llm/common.py
+++ b/src/hadavin_sdk/llm/common.py
@@ -183,5 +183,4 @@
     (`models.round_cost_up`). A cut-off answer keeps its cost but loses its tool calls: their input may be
     incomplete."""
-    check_output_plausible(usage, text, calls)
     check_facts(route, facts)
     cost = round_cost_up(cost_usd(usage, route))
```

## a1-20b: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u2_a_zero_output_on_an_empty_reply_is_kept[anthropic.api]`

```diff
--- a/src/hadavin_sdk/llm/pricing.py
+++ b/src/hadavin_sdk/llm/pricing.py
@@ -37,5 +37,5 @@
     """A reported output of 0 is kept only for an empty reply (no text, no tool call): a refusal, an empty answer or a
     blocked prompt. A reply with text or a tool call cannot have used no output tokens."""
-    if usage.output_tokens == 0 and (text.strip() or calls):
+    if usage.output_tokens == 0 and True:
         raise UsageMissing("implausible_zero", "output_tokens")
 
```

## a1-22: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u14_max_case_rounding_goes_up - Asser...`

```diff
--- a/src/hadavin_sdk/models.py
+++ b/src/hadavin_sdk/models.py
@@ -42,5 +42,5 @@
     if x.as_tuple().exponent >= -8:  # type: ignore[operator]  # already exact at 8 decimals: keep its form
         return x
-    return x.quantize(_COST_UNIT, rounding=ROUND_UP)
+    return x.quantize(_COST_UNIT)
 
 
```

## a1-24: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u4_a_zero_on_one_request_is_refused_before_the_sum_hides_it[both report 0 with text]`

```diff
--- a/src/hadavin_sdk/llm/openai_compat.py
+++ b/src/hadavin_sdk/llm/openai_compat.py
@@ -141,5 +141,5 @@
             # or a tool call, or a zero input on a priced route, is refused here (PL57). Two statements.
             check_input_plausible(got.usage, route)
-            check_output_plausible(got.usage, got.text, got.calls)
+            pass
             used = got.usage if used is None else add_usage(used, got.usage)
             # Done when answered, or when asking again would end the same way (cut off, refused).
```

## a1-25: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u10_pickle_and_copy_keep_type_reason_field_and_text[<lambda>0]`

```diff
--- a/src/hadavin_sdk/llm/protocol.py
+++ b/src/hadavin_sdk/llm/protocol.py
@@ -47,6 +47,6 @@
         )
 
-    def __reduce__(self) -> tuple[Any, ...]:
-        return (type(self), (self.reason, self.field), self.__dict__)
+    def _r(self):
+        return None
 
 
```

## a1-25b: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u10_pickle_and_copy_keep_type_reason_field_and_text[<lambda>1]`

```diff
--- a/src/hadavin_sdk/llm/protocol.py
+++ b/src/hadavin_sdk/llm/protocol.py
@@ -57,6 +57,6 @@
         super().__init__("unpriced_class", field)
 
-    def __reduce__(self) -> tuple[Any, ...]:
-        return (type(self), (self.field,), self.__dict__)
+    def _r(self):
+        return None
 
 
```

## a1-26: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u4_a_zero_on_one_request_is_refused_before_the_sum_hides_it[clause 2: request 1 input 0]`

```diff
--- a/src/hadavin_sdk/llm/openai_compat.py
+++ b/src/hadavin_sdk/llm/openai_compat.py
@@ -140,5 +140,5 @@
             # Each request is checked on its own before the sum hides it: a zero on one request that holds text
             # or a tool call, or a zero input on a priced route, is refused here (PL57). Two statements.
-            check_input_plausible(got.usage, route)
+            pass
             check_output_plausible(got.usage, got.text, got.calls)
             used = got.usage if used is None else add_usage(used, got.usage)
```

## a1-27: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u3_gemini_the_total_can_raise_the_output_count`

```diff
--- a/src/hadavin_sdk/llm/gemini.py
+++ b/src/hadavin_sdk/llm/gemini.py
@@ -105,5 +105,5 @@
         thoughts = 0 if thoughts_raw is None else checked_count(thoughts_raw, "output_tokens")
         out = cand + thoughts
-        if raw.get("totalTokenCount") is not None:
+        if False:
             # The total counts the prompt too, so it may pass the per-class cap legitimately: only its form is
             # checked here, and the output derived from it goes through `build_usage` and its cap below.
```

## a1-28: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u4_a_zero_on_one_request_is_refused_before_the_sum_hides_it[clause 3: request 2 output 0]`

```diff
--- a/src/hadavin_sdk/llm/openai_compat.py
+++ b/src/hadavin_sdk/llm/openai_compat.py
@@ -141,5 +141,5 @@
             # or a tool call, or a zero input on a priced route, is refused here (PL57). Two statements.
             check_input_plausible(got.usage, route)
-            check_output_plausible(got.usage, got.text, got.calls)
+            if n == 0: check_output_plausible(got.usage, got.text, got.calls)
             used = got.usage if used is None else add_usage(used, got.usage)
             # Done when answered, or when asking again would end the same way (cut off, refused).
```

## a1-29: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u4_a_zero_on_one_request_is_refused_before_the_sum_hides_it[clause 4: request 2 input 0]`

```diff
--- a/src/hadavin_sdk/llm/openai_compat.py
+++ b/src/hadavin_sdk/llm/openai_compat.py
@@ -140,5 +140,5 @@
             # Each request is checked on its own before the sum hides it: a zero on one request that holds text
             # or a tool call, or a zero input on a priced route, is refused here (PL57). Two statements.
-            check_input_plausible(got.usage, route)
+            if n == 0: check_input_plausible(got.usage, route)
             check_output_plausible(got.usage, got.text, got.calls)
             used = got.usage if used is None else add_usage(used, got.usage)
```

## a1-30: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u1_absent_usage_is_refused_with_one_request[openai_compat]`

```diff
--- a/src/hadavin_sdk/llm/openai_compat.py
+++ b/src/hadavin_sdk/llm/openai_compat.py
@@ -159,5 +159,5 @@
         message = choice.get("message") or {}
         raw = resp.get("usage")
-        if not isinstance(raw, dict):
+        if False:
             raise UsageMissing("absent", "usage")
         return Answer(
```

## a1-31: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u1_absent_usage_is_refused_with_one_request[gemini]`

```diff
--- a/src/hadavin_sdk/llm/gemini.py
+++ b/src/hadavin_sdk/llm/gemini.py
@@ -117,5 +117,5 @@
     def _parse(resp: dict[str, Any]) -> Answer:
         raw = resp.get("usageMetadata")
-        if not isinstance(raw, dict):
+        if False:
             raise UsageMissing("absent", "usage")
         if not resp.get("candidates"):
```

## a2-6: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u2b_a_cache_count_is_unpriced_and_checked_before_zero_input[usage_kw0-cache_write_tokens]`

```diff
--- a/src/hadavin_sdk/llm/pricing.py
+++ b/src/hadavin_sdk/llm/pricing.py
@@ -21,7 +21,7 @@
     """A non-zero cache class is `UnpricedUsage` (this core never asks a provider to use a cache, so a count is a
     surprise: it is refused, not priced)."""
-    if usage.cache_write_tokens != 0:
+    if False:
         raise UnpricedUsage("cache_write_tokens")
-    if usage.cache_read_tokens != 0:
+    if False:
         raise UnpricedUsage("cache_read_tokens")
 
```

## a2-9: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13a_usage_missing_one_request_one_attempt_books_w`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -128,5 +128,4 @@
     one = (
         Decimal(tokens_in) * route.input_usd_per_mtok
-        + Decimal(route.max_tokens) * route.output_usd_per_mtok
     )
     return round_cost_up(one * requests / Decimal(1_000_000))
```

## a2-9c: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13a_usage_missing_one_request_one_attempt_books_w`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -127,5 +127,5 @@
     tokens_in = -(-len(prompt) // defaults.PROMPT_BYTES_PER_TOKEN)
     one = (
-        Decimal(tokens_in) * route.input_usd_per_mtok
+        Decimal(tokens_in) * route.output_usd_per_mtok
         + Decimal(route.max_tokens) * route.output_usd_per_mtok
     )
```

## a2-9b: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13b_b2_the_factor_is_requests_times_attempts`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -130,5 +130,5 @@
         + Decimal(route.max_tokens) * route.output_usd_per_mtok
     )
-    return round_cost_up(one * requests / Decimal(1_000_000))
+    return round_cost_up(one * 1 / Decimal(1_000_000))
 
 
```

## a2-48: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13k_a_lone_surrogate_in_a_tool_call_input_does_not_crash_the_booking`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -125,5 +125,5 @@
     price, plus ``max_tokens`` of output at the output price. Charged when a call's real cost is unknown."""
     prompt = (system + _dumps(messages) + _dumps(tools)).encode("utf-8", "surrogatepass")
-    tokens_in = -(-len(prompt) // defaults.PROMPT_BYTES_PER_TOKEN)
+    tokens_in = -(-len(prompt.decode("utf-8", "surrogatepass")) // defaults.PROMPT_BYTES_PER_TOKEN)
     one = (
         Decimal(tokens_in) * route.input_usd_per_mtok
```

## a2-48b: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13a_usage_missing_one_request_one_attempt_books_w`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -125,5 +125,5 @@
     price, plus ``max_tokens`` of output at the output price. Charged when a call's real cost is unknown."""
     prompt = (system + _dumps(messages) + _dumps(tools)).encode("utf-8", "surrogatepass")
-    tokens_in = -(-len(prompt) // defaults.PROMPT_BYTES_PER_TOKEN)
+    tokens_in = max(1, len(prompt.decode("utf-8", "surrogatepass")) // 3)
     one = (
         Decimal(tokens_in) * route.input_usd_per_mtok
```

## a2-49: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13a_usage_missing_one_request_one_attempt_books_w`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -124,5 +124,5 @@
     (system, messages and tool specs, in UTF-8; one token per byte at most, `PROMPT_BYTES_PER_TOKEN`) at the input
     price, plus ``max_tokens`` of output at the output price. Charged when a call's real cost is unknown."""
-    prompt = (system + _dumps(messages) + _dumps(tools)).encode("utf-8", "surrogatepass")
+    prompt = (system + _dumps(messages)).encode("utf-8", "surrogatepass")
     tokens_in = -(-len(prompt) // defaults.PROMPT_BYTES_PER_TOKEN)
     one = (
```

## a2-13: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c2_anthropic_cache_fields_null_zero_or_absent_price_as_two_counts`

```diff
--- a/src/hadavin_sdk/models.py
+++ b/src/hadavin_sdk/models.py
@@ -357,5 +357,5 @@
     def usage(self) -> Usage:
         """The counts this reply was priced from (input and output; a cache class is refused before a Reply exists)."""
-        return Usage(self.input_tokens, self.output_tokens)
+        return Usage(self.output_tokens, self.input_tokens)
 
     @field_validator("cost_usd")
```

## a2-13b: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c3_and_c9_zero_cache_keys_load_and_are_dropped_before_the_reply`

```diff
--- a/src/hadavin_sdk/llm/fake.py
+++ b/src/hadavin_sdk/llm/fake.py
@@ -55,6 +55,6 @@
         data = dict(data)
         cache_write, cache_read = (
-            data.pop("cache_write_tokens", None),
-            data.pop("cache_read_tokens", None),
+            data.get("cache_write_tokens"),
+            data.get("cache_read_tokens"),
         )
         usage = build_usage(
```

## a2-14: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c3_bedrock_non_zero_cache_class_is_unpriced[cacheWriteInputTokens-cache_write_tokens]`

```diff
--- a/src/hadavin_sdk/llm/bedrock.py
+++ b/src/hadavin_sdk/llm/bedrock.py
@@ -178,5 +178,5 @@
                 raw.get("inputTokens"),
                 raw.get("outputTokens"),
-                cache_write_tokens=raw.get("cacheWriteInputTokens"),
+                cache_write_tokens=raw.get("cacheWriteTokens"),
                 cache_read_tokens=raw.get("cacheReadInputTokens"),
             ),
```

## a2-16: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c10_config_hash_is_the_same_as_before_for_valid_prices`

```diff
--- a/src/hadavin_sdk/config.py
+++ b/src/hadavin_sdk/config.py
@@ -84,5 +84,5 @@
         if v != v.quantize(Decimal("1E-6")):
             raise ValueError("a price may have at most 6 decimal places")
-        return v
+        return v.quantize(Decimal("1E-6"))
 
 
```

## a2-20: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['priority'-service_tier]`

```diff
--- a/src/hadavin_sdk/llm/pricing.py
+++ b/src/hadavin_sdk/llm/pricing.py
@@ -71,4 +71,4 @@
         if value is None:
             continue
-        if type(value) is not str or value != _STANDARD:
+        if False:
             raise UnpricedUsage(word)
```

## a2-20c: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c3d_pricing_words_standard_absent_and_null_are_accepted[standard-service_tier]`

```diff
--- a/src/hadavin_sdk/llm/pricing.py
+++ b/src/hadavin_sdk/llm/pricing.py
@@ -71,4 +71,4 @@
         if value is None:
             continue
-        if type(value) is not str or value != _STANDARD:
+        if type(value) is not str or value == _STANDARD:
             raise UnpricedUsage(word)
```

## a2-20b: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['Standard'-service_tier]`

```diff
--- a/src/hadavin_sdk/llm/pricing.py
+++ b/src/hadavin_sdk/llm/pricing.py
@@ -71,4 +71,4 @@
         if value is None:
             continue
-        if type(value) is not str or value != _STANDARD:
+        if type(value) is not str or value.lower() != _STANDARD:
             raise UnpricedUsage(word)
```

## a2-23a: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c7e_request_bound_is_strict - Failed...`

```diff
--- a/src/hadavin_sdk/llm/common.py
+++ b/src/hadavin_sdk/llm/common.py
@@ -162,5 +162,5 @@
         n = llm.REQUESTS_PER_CHAT
     except AttributeError:
-        raise TypeError(f"{type(llm).__name__} declares no REQUESTS_PER_CHAT") from None
+        return 1
     if type(n) is not int or n < 1:
         raise ValueError(f"{type(llm).__name__}.REQUESTS_PER_CHAT must be an int of at least 1")
```

## a2-23b: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c7d_every_kind_declares_its_request_count_whatever_max_attempts_is`

```diff
--- a/src/hadavin_sdk/llm/common.py
+++ b/src/hadavin_sdk/llm/common.py
@@ -165,5 +165,5 @@
     if type(n) is not int or n < 1:
         raise ValueError(f"{type(llm).__name__}.REQUESTS_PER_CHAT must be an int of at least 1")
-    return n
+    return n * getattr(llm, "max_attempts", 1)
 
 
```

## a2-23c: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c7e_request_bound_is_strict - Failed...`

```diff
--- a/src/hadavin_sdk/llm/common.py
+++ b/src/hadavin_sdk/llm/common.py
@@ -163,5 +163,5 @@
     except AttributeError:
         raise TypeError(f"{type(llm).__name__} declares no REQUESTS_PER_CHAT") from None
-    if type(n) is not int or n < 1:
+    if False:
         raise ValueError(f"{type(llm).__name__}.REQUESTS_PER_CHAT must be an int of at least 1")
     return n
```

## a2-24a: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13c_an_abandoned_call_books_the_whole_call_maximum[declare0-6]`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -198,5 +198,5 @@
             # worst case and stop the run: at most one such call per invocation, and the cap still holds.
             if route_prices is not None:
-                budget.charge(_worst_case_of_call(llm, route_prices, system, messages))
+                budget.charge(worst_case_usd(route_prices, system, messages, tools=TOOL_SPECS, requests=1))
             out.status, out.stop_reason, out.halt = "timeout", "call_timeout", "aborted"
             return out
```

## a2-24b: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13b_b2_the_factor_is_requests_times_attempts`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -142,5 +142,5 @@
     return _count_or(
         getattr(llm, "REQUESTS_PER_CHAT", None), defaults.CHARGE_FALLBACK_REQUESTS
-    ) * _count_or(getattr(llm, "max_attempts", None), defaults.CHARGE_FALLBACK_ATTEMPTS)
+    )
 
 
```

## a2-24c: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13b_b2_the_factor_is_requests_times_attempts`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -210,5 +210,5 @@
             # Every other provider failure (a `UsageMissing` included) may have been billed too: same booking.
             if route_prices is not None:
-                budget.charge(_worst_case_of_call(llm, route_prices, system, messages))
+                budget.charge(worst_case_usd(route_prices, system, messages, tools=TOOL_SPECS, requests=1))
             out.status, out.stop_reason, out.halt = "error", "aborted", "aborted"
             return out
```

## a2-52: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13b_b2_the_factor_is_requests_times_attempts`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -141,5 +141,5 @@
     Total and plain: an object that declares nothing usable is charged the fallbacks, never an error."""
     return _count_or(
-        getattr(llm, "REQUESTS_PER_CHAT", None), defaults.CHARGE_FALLBACK_REQUESTS
+        1, 1
     ) * _count_or(getattr(llm, "max_attempts", None), defaults.CHARGE_FALLBACK_ATTEMPTS)
 
```

## a2-53: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13d2_provider_exhausted_books_the_whole_call_maximum`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -204,5 +204,5 @@
             # Out of retries: the attempts may all have been billed, so the whole-call maximum is booked.
             if route_prices is not None:
-                budget.charge(_worst_case_of_call(llm, route_prices, system, messages))
+                budget.charge(worst_case_usd(route_prices, system, messages, tools=TOOL_SPECS, requests=1))
             out.status, out.stop_reason = "error", "provider_exhausted"
             return out
```

## a2-54: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13f_no_prices_books_nothing_and_raises_nothing[<lambda>2]`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -203,5 +203,5 @@
         except ProviderExhausted:
             # Out of retries: the attempts may all have been billed, so the whole-call maximum is booked.
-            if route_prices is not None:
+            if True:
                 budget.charge(_worst_case_of_call(llm, route_prices, system, messages))
             out.status, out.stop_reason = "error", "provider_exhausted"
```

## a2-55: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13f_no_prices_books_nothing_and_raises_nothing[<lambda>0]`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -209,5 +209,5 @@
         except ProviderError:
             # Every other provider failure (a `UsageMissing` included) may have been billed too: same booking.
-            if route_prices is not None:
+            if True:
                 budget.charge(_worst_case_of_call(llm, route_prices, system, messages))
             out.status, out.stop_reason, out.halt = "error", "aborted", "aborted"
```

## a2-56: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c18a_a_real_kind_label_is_refused_before_anything_is_written`

```diff
--- a/src/hadavin_sdk/k1b/replay.py
+++ b/src/hadavin_sdk/k1b/replay.py
@@ -127,5 +127,5 @@
     # The loop books only the answered attempt of an answered call and has no meter, so the hidden billed attempts of
     # a real model have no owner here (PL55): v1 replays only the fake kind and the detectors that cost nothing.
-    if (llm_kind or cfg.backends.llm.kind) != "fake":
+    if False:
         raise ConfigError("k1b replay runs only on the fake llm kind in v1")
     if isinstance(
```

## a2-57: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13k_a_lone_surrogate_in_a_tool_call_input_does_not_crash_the_booking`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -124,5 +124,5 @@
     (system, messages and tool specs, in UTF-8; one token per byte at most, `PROMPT_BYTES_PER_TOKEN`) at the input
     price, plus ``max_tokens`` of output at the output price. Charged when a call's real cost is unknown."""
-    prompt = (system + _dumps(messages) + _dumps(tools)).encode("utf-8", "surrogatepass")
+    prompt = (system + _dumps(messages) + _dumps(tools)).encode("utf-8")
     tokens_in = -(-len(prompt) // defaults.PROMPT_BYTES_PER_TOKEN)
     one = (
```

## a2-58: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13f_an_abandoned_call_without_prices_books_nothing`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -197,5 +197,5 @@
             # The abandoned call may still be running and billed (a retry layer can re-send), so charge the
             # worst case and stop the run: at most one such call per invocation, and the cap still holds.
-            if route_prices is not None:
+            if True:
                 budget.charge(_worst_case_of_call(llm, route_prices, system, messages))
             out.status, out.stop_reason, out.halt = "timeout", "call_timeout", "aborted"
```

## a2-59: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c18b_a_detector_kind_other_than_regex_and_llm_judge_is_refused`

```diff
--- a/src/hadavin_sdk/k1b/replay.py
+++ b/src/hadavin_sdk/k1b/replay.py
@@ -133,5 +133,5 @@
     ):  # a real network object under a "fake" label is refused too (PL66)
         raise ConfigError("k1b replay runs only on the fake llm kind in v1")
-    if any(d.kind not in _REPLAY_DETECTORS for d in cfg.backends.detector):
+    if False:
         raise ConfigError("k1b replay runs only the regex and llm_judge detector kinds in v1")
     if not cfg.k1b.redact and not acknowledge_masked:
```

## a2-60: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13p_clause_2_the_rounding_goes_up_once_on_the_exact_product`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -130,5 +130,5 @@
         + Decimal(route.max_tokens) * route.output_usd_per_mtok
     )
-    return round_cost_up(one * requests / Decimal(1_000_000))
+    return (one * requests / Decimal(1_000_000)).quantize(Decimal('1E-8'), rounding=__import__('decimal').ROUND_DOWN)
 
 
```

## a2-61: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13k_clause_2_the_audit_hash_of_a_tool_name_with_a_lone_surrogate`

```diff
--- a/src/hadavin_sdk/k1b/replay.py
+++ b/src/hadavin_sdk/k1b/replay.py
@@ -65,5 +65,5 @@
     # "surrogatepass": a model's tool name can hold a lone surrogate, which plain UTF-8 refuses (every valid string
     # hashes as before).
-    return hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()
+    return hashlib.sha256(text.encode("utf-8")).hexdigest()
 
 
```

## a2-62: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c18c_a_network_object_under_the_fake_label_is_refused`

```diff
--- a/src/hadavin_sdk/k1b/replay.py
+++ b/src/hadavin_sdk/k1b/replay.py
@@ -129,7 +129,5 @@
     if (llm_kind or cfg.backends.llm.kind) != "fake":
         raise ConfigError("k1b replay runs only on the fake llm kind in v1")
-    if isinstance(
-        llm, NetworkLLM
-    ):  # a real network object under a "fake" label is refused too (PL66)
+    if False:  # a real network object under a "fake" label is refused too (PL66)
         raise ConfigError("k1b replay runs only on the fake llm kind in v1")
     if any(d.kind not in _REPLAY_DETECTORS for d in cfg.backends.detector):
```

## a2-33: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13g1_an_object_that_declares_nothing_is_booked_the_fallbacks`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -141,5 +141,5 @@
     Total and plain: an object that declares nothing usable is charged the fallbacks, never an error."""
     return _count_or(
-        getattr(llm, "REQUESTS_PER_CHAT", None), defaults.CHARGE_FALLBACK_REQUESTS
+        __import__('hadavin_sdk.llm.common', fromlist=['x']).request_bound(llm), 1
     ) * _count_or(getattr(llm, "max_attempts", None), defaults.CHARGE_FALLBACK_ATTEMPTS)
 
```

## a2-33b: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13g1_an_object_that_declares_nothing_is_booked_the_fallbacks`

```diff
--- a/src/hadavin_sdk/defaults.py
+++ b/src/hadavin_sdk/defaults.py
@@ -163,5 +163,5 @@
 OPENAI_COMPAT_REQUESTS_PER_CHAT = 2  # the forced answer missing: one more request (design 4.3)
 CHARGE_FALLBACK_REQUESTS = (
-    2  # k1b charge for a llm that declares no usable REQUESTS_PER_CHAT; not below any kind's
+    1  # k1b charge for a llm that declares no usable REQUESTS_PER_CHAT; not below any kind's
 )
 CHARGE_FALLBACK_ATTEMPTS = (
```

## a2-33c: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13g1_an_object_that_declares_nothing_is_booked_the_fallbacks`

```diff
--- a/src/hadavin_sdk/defaults.py
+++ b/src/hadavin_sdk/defaults.py
@@ -166,5 +166,5 @@
 )
 CHARGE_FALLBACK_ATTEMPTS = (
-    10  # k1b charge for a llm that declares no usable max_attempts; not below the setting's `le`
+    3  # k1b charge for a llm that declares no usable max_attempts; not below the setting's `le`
 )
 PROMPT_BYTES_PER_TOKEN = (
```

## a2-37: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13h_the_fallbacks_are_not_below_any_declaration`

```diff
--- a/tests/k1b_support.py
+++ b/tests/k1b_support.py
@@ -19,6 +19,4 @@
     ``documents`` (the K1a helper's ``documents[0]`` use is why this is a new class)."""
 
-    REQUESTS_PER_CHAT = 1  # what the k1b charge helper reads: one request, one attempt
-    max_attempts = 1
 
     def __init__(self, replies: list[Reply | Callable[[list[dict[str, Any]]], Reply]]) -> None:
```

## a2-37b: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c7d_every_kind_declares_its_request_count_whatever_max_attempts_is`

```diff
--- a/src/hadavin_sdk/llm/fake.py
+++ b/src/hadavin_sdk/llm/fake.py
@@ -23,5 +23,4 @@
     # A recorded run replays one attempt and one request: the k1b charge helper reads both.
     REQUESTS_PER_CHAT = 1
-    max_attempts = 1
 
     def __init__(self, recorded_dir: Path, routes: dict[str, Route]) -> None:
```

## a2-37c: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13h_the_fallbacks_are_not_below_any_declaration`

```diff
--- a/tests/k1b_support.py
+++ b/tests/k1b_support.py
@@ -276,11 +276,4 @@
         self.inner, self.dir, self.attempts = inner, Path(recorded_dir), {}
 
-    @property
-    def REQUESTS_PER_CHAT(self) -> int:
-        return self.inner.REQUESTS_PER_CHAT
-
-    @property
-    def max_attempts(self) -> int:
-        return self.inner.max_attempts
 
     def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
```

## a2-42: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c16_a_failed_request_two_is_a_usage_missing_chained_from_the_real_error[i-exhausted]`

```diff
--- a/src/hadavin_sdk/llm/openai_compat.py
+++ b/src/hadavin_sdk/llm/openai_compat.py
@@ -137,5 +137,5 @@
                 # Request 1 was answered and billed; its counts would be lost. `UsageMissing` already means
                 # "book the reserved amount or the worst case" to every caller. The real error stays as the cause.
-                raise UsageMissing("absent", "usage") from exc
+                raise
             # Each request is checked on its own before the sum hides it: a zero on one request that holds text
             # or a tool call, or a zero input on a priced route, is refused here (PL57). Two statements.
```

## a2-43: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c16_counter_request_one_failing_keeps_its_original_error[i-exhausted]`

```diff
--- a/src/hadavin_sdk/llm/openai_compat.py
+++ b/src/hadavin_sdk/llm/openai_compat.py
@@ -133,5 +133,5 @@
                 raise  # request 2 answered without usage stays visible as itself (its cause is not wrapped)
             except ProviderError as exc:
-                if n == 0:
+                if False:
                     raise  # a failed first request is unchanged: the original error, free of charge
                 # Request 1 was answered and billed; its counts would be lost. `UsageMissing` already means
```

## a2-45: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c16_iv_a_usage_missing_of_request_two_is_not_wrapped`

```diff
--- a/src/hadavin_sdk/llm/openai_compat.py
+++ b/src/hadavin_sdk/llm/openai_compat.py
@@ -130,6 +130,8 @@
                     lambda: self._parse(post_json(self.url, body, self._headers(), self.timeout_s))
                 )
-            except UsageMissing:
-                raise  # request 2 answered without usage stays visible as itself (its cause is not wrapped)
+            except UsageMissing as exc2:
+                if n == 0:
+                    raise
+                raise UsageMissing('absent', 'usage') from exc2  # request 2 answered without usage stays visible as itself (its cause is not wrapped)
             except ProviderError as exc:
                 if n == 0:
```

## a2-50: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13d2_provider_exhausted_books_the_whole_call_maximum`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -204,5 +204,5 @@
             # Out of retries: the attempts may all have been billed, so the whole-call maximum is booked.
             if route_prices is not None:
-                budget.charge(_worst_case_of_call(llm, route_prices, system, messages))
+                budget.charge(Decimal(0))
             out.status, out.stop_reason = "error", "provider_exhausted"
             return out
```

## a2-51: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c13a_usage_missing_one_request_one_attempt_books_w`

```diff
--- a/src/hadavin_sdk/k1b/loop.py
+++ b/src/hadavin_sdk/k1b/loop.py
@@ -210,5 +210,5 @@
             # Every other provider failure (a `UsageMissing` included) may have been billed too: same booking.
             if route_prices is not None:
-                budget.charge(_worst_case_of_call(llm, route_prices, system, messages))
+                budget.charge(Decimal(0))
             out.status, out.stop_reason, out.halt = "error", "aborted", "aborted"
             return out
```

## a2-32: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c8b_a_zero_price_is_refused_at_load_for_every_real_kind[0-15.00-anthropic]`

```diff
--- a/src/hadavin_sdk/config.py
+++ b/src/hadavin_sdk/config.py
@@ -405,5 +405,5 @@
         """A zero price makes every reply cost 0, so no spend cap could fire. Only the fake llm kind may have one.
         Names the routes only, never their prices."""
-        if self.backends.llm.kind != "fake":
+        if False:
             zero = [
                 name
```

## a2-32b: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c8b_the_fake_kind_may_carry_a_zero_price`

```diff
--- a/src/hadavin_sdk/config.py
+++ b/src/hadavin_sdk/config.py
@@ -405,5 +405,5 @@
         """A zero price makes every reply cost 0, so no spend cap could fire. Only the fake llm kind may have one.
         Names the routes only, never their prices."""
-        if self.backends.llm.kind != "fake":
+        if True:
             zero = [
                 name
```

## a2-26: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed['priority'-service_tier]`

```diff
--- a/src/hadavin_sdk/llm/common.py
+++ b/src/hadavin_sdk/llm/common.py
@@ -184,5 +184,4 @@
     incomplete."""
     check_output_plausible(usage, text, calls)
-    check_facts(route, facts)
     cost = round_cost_up(cost_usd(usage, route))
     stop = stop_reason(stop, calls)
```

## a2-27: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u4_both_requests_carry_usage_and_the_totals_are_the_sums`

```diff
--- a/src/hadavin_sdk/llm/openai_compat.py
+++ b/src/hadavin_sdk/llm/openai_compat.py
@@ -123,7 +123,5 @@
             body["tool_choice"] = {"type": "function", "function": {"name": forced}}
         started, used = time.monotonic(), None
-        for n in range(
-            self.REQUESTS_PER_CHAT
-        ):  # the forced answer missing: one more request (design 4.3)
+        for n in range(3):  # the forced answer missing: one more request (design 4.3)
             try:
                 got = self._retry(
```

## a2-27b: KILLED
first failure: `FAILED tests/test_usage_refuse.py::test_u3b_the_same_sum_through_two_openai_requests_is_a_typed_refusal`

```diff
--- a/src/hadavin_sdk/defaults.py
+++ b/src/hadavin_sdk/defaults.py
@@ -161,5 +161,5 @@
 # --- model request counts and k1b charges (P4a-2): one named block. Rebase note: if another package adds a block at the
 # end of this file first, keep both blocks and keep this one whole ------------------------------------------------------
-OPENAI_COMPAT_REQUESTS_PER_CHAT = 2  # the forced answer missing: one more request (design 4.3)
+OPENAI_COMPAT_REQUESTS_PER_CHAT = 1  # the forced answer missing: one more request (design 4.3)
 CHARGE_FALLBACK_REQUESTS = (
     2  # k1b charge for a llm that declares no usable REQUESTS_PER_CHAT; not below any kind's
```

## a2-28: KILLED
first failure: `FAILED tests/test_usage_classes.py::test_c7d_every_kind_declares_its_request_count_whatever_max_attempts_is`

```diff
--- a/src/hadavin_sdk/llm/gemini.py
+++ b/src/hadavin_sdk/llm/gemini.py
@@ -40,5 +40,4 @@
 class GeminiLLM(NetworkLLM):
     label = "gemini"
-    REQUESTS_PER_CHAT = 1  # one request a chat; `common.request_bound` reads it
 
     def __init__(
```


# Summary: 87 killed of 87; not killed: 
## UPDATE: merged head 4a0976f (core/P4a + origin/core/P2a-1 e323ac7), full suites
py3.13 (merged313.log): 10190 passed, 562 skipped in 313.11s (0:05:13)  rc=0
py3.12 (merged312.log): 10190 passed, 562 skipped in 292.73s (0:04:52)  rc=0
The inherited test_p7_tick failure is gone on the merged head (fixed in P2a-1). Mutant killers per test: killers.md (14 differ from ticket row names; first-failure under -x over four files). bandit B608 at store/postgres.py:768 still on the base, handled in P4d-a2. Mutants were not re-run on the merged head.
