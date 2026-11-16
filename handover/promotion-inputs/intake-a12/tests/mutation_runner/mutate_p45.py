"""Mutation runner for the WP2c request path (P45) and the DF5 cost controls. Breaks one rule at a time and works on a SCRATCH COPY of the repository (the real tree is never written, so a killed run cannot leave it mutated).

Run from the repository root:  python tests/mutation_runner/mutate_p45.py [--package base|a1|a2|b1|b2|all] [--only SUBSTRING]

Each mutant is ``(name, package, file, old, new, must_fail)``. ``must_fail`` is a pytest node id (or ``None`` = run the four ``TESTS`` modules). A mutant is
KILLED only when pytest exits with 1 (a test failed); any other non-zero code, a missing ``must_fail`` node or a timeout is a CRASH, and 0 is SURVIVED.
The unmutated suite and every ``must_fail`` node must be green first. ``old`` must be found exactly once (``# mut:<name>`` anchors mark new sites).
The run ends with ``git diff --exit-code -- src``: a tree left mutated (or uncommitted) fails it. Exit code 0 only when nothing is left unkilled."""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "src" / "intake"
TESTS = ["tests/test_request_path.py", "tests/test_extract_mask.py", "tests/test_money_path.py", "tests/test_queue_sink.py"]
TIMEOUT_S = 300
PACKAGES = ("base", "a1", "a2", "b1", "b2")

BODY_UNSAFE = '        return "body_unsafe"'
CHECK_THEN_RESERVE = (
    "            if _run_check(body_check, body) is not None:\n"
    '                return failed("body_unsafe")\n'
    "            res = self.budget.reserve(req.doc_sha, req.tier, body, self.live)"
)
RESERVE_THEN_CHECK = (
    "            res = self.budget.reserve(req.doc_sha, req.tier, body, self.live)\n"
    "            if _run_check(body_check, body) is not None:\n"
    '                return failed("body_unsafe")'
)

# (name, package, file, old text, new text, must_fail node id or None)
MUTANTS = [
    (
        "doc_sha tie removed",
        "base",
        "model.py",
        "if req.doc_sha != body_check.source_sha256:",
        "if False:",
        "tests/test_request_path.py::test_body_check_doc_sha_tie",
    ),
    (
        "gate hashes the model text",
        "base",
        "model.py",
        "gate_check(s, body_check.document_text)",
        "gate_check(s, req.model_text)",
        "tests/test_request_path.py::test_gate_still_hashes_document_text_not_model_text",
    ),
    (
        "body check ignored",
        "base",
        "model.py",
        "if _run_check(body_check, body) is not None:",
        "if False:",
        "tests/test_request_path.py::test_a_refusing_body_check_costs_nothing[anything]",
    ),
    (
        "raising check not caught",
        "base",
        "model.py",
        "    except Exception:\n" + BODY_UNSAFE,
        "    except ValueError:\n" + BODY_UNSAFE,
        "tests/test_request_path.py::test_a_body_check_that_raises_is_body_unsafe_with_no_reservation",
    ),
    (
        "ConfigError swallowed by the check wrapper",
        "base",
        "model.py",
        "    except ConfigError:\n        raise\n    except Exception:\n" + BODY_UNSAFE,
        "    except Exception:\n" + BODY_UNSAFE,
        "tests/test_request_path.py::test_a_config_error_from_the_body_check_passes_through",
    ),
    (
        "backend body_unsafe passes",
        "base",
        "model.py",
        'elif result.error == "body_unsafe":',
        "elif False:",
        "tests/test_request_path.py::test_a_backend_cannot_return_body_unsafe_after_reserve",
    ),
    (
        "check after reserve",
        "base",
        "model.py",
        CHECK_THEN_RESERVE,
        RESERVE_THEN_CHECK,
        "tests/test_request_path.py::test_a_refusing_body_check_costs_nothing[anything]",
    ),
    (
        "fake body without the text",
        "base",
        "model_fake.py",
        ', "text": req.model_text}',
        "}",
        "tests/test_request_path.py::test_the_body_check_sees_the_exact_bytes_that_are_reserved",
    ),
    (
        "fake backend can reply body_unsafe",
        "base",
        "model_fake.py",
        ' and value != "body_unsafe" else "bad_reply")',
        ' else "bad_reply")',
        "tests/test_model_fake.py::test_a_fake_reply_cannot_name_body_unsafe_it_is_a_bad_reply",
    ),
    (
        "in-extract gate removed",
        "base",
        "extract.py",
        "gate_check(settings, document_text)",
        "pass",
        "tests/test_request_path.py::test_gate_refusal_shape_unchanged",
    ),
    (
        "a2 and a3 skipped",
        "base",
        "extract.py",
        "        mask.check_model_text(masked)  # a3 and a2\n",
        "        pass\n",
        "tests/test_extract_mask.py::test_checks_a3_and_a2_run_before_any_call",
    ),
    (
        "restore skipped",
        "base",
        "extract.py",
        "rest = mask.restore(r.fields, masked, k, document_text)",
        "rest = mask.Restored(r.fields)",
        "tests/test_extract_mask.py::test_a_mark_copied_by_the_ai_is_put_back_into_a_description",
    ),
    (
        "judge on the model text",
        "base",
        "extract.py",
        "bad = judge(restored_fields, document_text,",
        "bad = judge(restored_fields, masked.text,",
        "tests/test_extract_mask.py::test_judge_gets_the_restored_record_and_the_original_text",
    ),
    (
        "last_code ignored",
        "base",
        "extract.py",
        'bc.last_code or "mask_failed"',
        '"mask_failed"',
        "tests/test_extract_mask.py::test_body_unsafe_carries_last_code[body_has_original]",
    ),
    (
        "tracer not called",
        "base",
        "extract.py",
        "tracer.mask_done(masked, k, document_text)",
        "pass",
        "tests/test_extract_mask.py::test_a_sink_that_cannot_write_means_no_call",
    ),
    (
        "new key on retry",
        "base",
        "extract.py",
        "k = key if key is not None else os.urandom(32)",
        "k = os.urandom(32)",
        "tests/test_extract_mask.py::test_clean_invoice_masks_once_per_request_and_restores_nothing",
    ),
    (
        "unrestored fields returned",
        "base",
        "extract.py",
        "return done(copy.deepcopy(restored_fields), (), tier, r.model_id, None)",
        "return done(copy.deepcopy(r.fields), (), tier, r.model_id, None)",
        "tests/test_extract_mask.py::test_judge_gets_the_restored_record_and_the_original_text",
    ),
    (
        "restore failure drops the code",
        "base",
        "extract.py",
        "return done(None, (), tier, r.model_id, None, e.code)",
        "return done(None, (), tier, r.model_id, None, None)",
        "tests/test_extract_mask.py::test_a_bank_mark_in_a_plain_field_is_hidden_value_in_field_and_costs_the_call[invoice_no]",
    ),
    (
        "backend uses document text",
        "base",
        "extract.py",
        "ExtractRequest(doc_sha=parsed.source_sha256, tier=tier, model_text=masked.text)",
        "ExtractRequest(doc_sha=parsed.source_sha256, tier=tier, model_text=document_text)",
        "tests/test_extract_mask.py::test_clean_invoice_masks_once_per_request_and_restores_nothing",
    ),
    (
        "sink failure not handled",
        "base",
        "extract.py",
        "    except OSError:  # the trace sink",
        "    except KeyError:  # the trace sink",
        "tests/test_extract_mask.py::test_a_sink_that_cannot_write_means_no_call",
    ),
    (
        "refused stored as pass",
        "base",
        "extract.py",
        '"refused": "fail"',
        '"refused": "pass"',
        "tests/test_queue_sink.py::test_row_stores_a_trace_row_and_maps_the_result_words",
    ),
    (
        "refused row answered True",
        "base",
        "extract.py",
        "except (ValueError, Refused):\n            return False",
        "except (ValueError, Refused):\n            return True",
        "tests/test_queue_sink.py::test_a_row_outside_the_closed_vocabulary_is_refused_not_raised",
    ),
    (
        "sink stores no spans",
        "base",
        "extract.py",
        "self.document_text, key, spans)",
        "self.document_text, key, spans[:0])",
        "tests/test_queue_sink.py::test_mask_done_stores_spans_and_key_so_the_marks_restore",
    ),
    (
        "minimum limit from the document cap",
        "base",
        "budget.py",
        "n_chars = MASKED_MAX_CHARS",
        "n_chars = 20000",
        "tests/test_money_path.py::test_the_minimum_limit_is_derived_from_the_masked_cap",
    ),
    (
        "prompt path back to v1",
        "base",
        "prompt_file.py",
        '"prompts" / "extract_v3.txt"',
        '"prompts" / "extract_v1.txt"',
        "tests/test_money_path.py::test_readme_min_limit_numbers_match",
    ),
    (
        "forced tool_choice back",
        "a2",
        "model_anthropic.py",
        '"tool_choice": {"type": "auto", "disable_parallel_tool_use": True},  # mut:tool_choice',
        '"tool_choice": {"type": "tool", "name": _TOOL},  # mut:tool_choice',
        "tests/test_model_anthropic.py::test_body_uses_auto_tool_choice_without_parallel_calls",
    ),
    (
        "parallel tool calls allowed",
        "a2",
        "model_anthropic.py",
        '"disable_parallel_tool_use": True}',
        '"disable_parallel_tool_use": False}',
        "tests/test_model_anthropic.py::test_body_uses_auto_tool_choice_without_parallel_calls",
    ),
    (
        "extra_body not sent",
        "a2",
        "model_anthropic.py",
        "for k, v in extra.items():  # mut:extra_loop",
        "for k, v in {}.items():  # mut:extra_loop",
        "tests/test_model_anthropic.py::test_body_uses_between_tools_for_sonnet",
    ),
    (
        "strict flag always sent",
        "a2",
        "model_anthropic.py",
        "if m.strict_tool:  # mut:strict_flag",
        "if True:  # mut:strict_flag",
        "tests/test_model_anthropic.py::test_strict_tool_flag_follows_config",
    ),
    (
        "max_tokens verdict skipped",
        "a2",
        "model_anthropic.py",
        'if stop == "max_tokens":  # mut:max_tokens_first',
        "if False:  # mut:max_tokens_first",
        "tests/test_model_anthropic.py::test_max_tokens_with_complete_block_is_max_tokens",
    ),
    (
        "stop reason not checked",
        "a2",
        "model_anthropic.py",
        'if stop != "tool_use":  # mut:stop_check',
        "if False:  # mut:stop_check",
        "tests/test_model_anthropic.py::test_end_turn_with_tool_block_is_bad_reply",
    ),
    (
        "two tool blocks accepted",
        "a2",
        "model_anthropic.py",
        'if len(tools) != 1 or not isinstance(tools[0].get("input"), dict):  # mut:one_tool',
        'if len(tools) < 1 or not isinstance(tools[0].get("input"), dict):  # mut:one_tool',
        "tests/test_model_anthropic.py::test_two_record_blocks_is_bad_reply",
    ),
    (
        "unknown blocks ignored",
        "a2",
        "model_anthropic.py",
        'if kind != "tool_use" or b.get("name") != _TOOL:  # mut:other_block',
        'if kind == "tool_use" and b.get("name") != _TOOL:  # mut:other_block',
        "tests/test_model_anthropic.py::test_a_reply_with_only_an_unknown_block_type_is_bad_reply",
    ),
    (
        "real usage dropped on refusal",
        "a2",
        "model_anthropic.py",
        "return ModelResult(fields, mid, i, o, 0, code, clean_diag(diag), cw, cr, th)",
        "return ModelResult(fields, mid, 0, 0, 0, code, clean_diag(diag), cw, cr, th)",
        "tests/test_model_anthropic.py::test_truncated_and_refused_replies_carry_their_real_usage[refusal-bad_reply]",
    ),
    (
        "odd service tier ignored",
        "a2",
        "model_anthropic.py",
        'if u.get(k) is not None and u.get(k) != "standard":  # mut:odd_tier',
        "if False:  # mut:odd_tier",
        "tests/test_model_anthropic.py::test_odd_usage_sets_the_flag_the_guard_halts_on[usage0]",
    ),
    (
        "provider limit not detected",
        "a2",
        "model_anthropic.py",
        "if limit:  # mut:limit_detect",
        "if False:  # mut:limit_detect",
        "tests/test_model_anthropic.py::test_spend_cap_429_is_provider_limit_no_second_call",
    ),
    (
        "429 enforced_spend_limit retried",
        "a2",
        "model_anthropic.py",
        "(status == 429 and code == _SPEND_CAP_CODE)",
        "(False)",
        "tests/test_model_anthropic.py::test_provider_limit_detection_cases[code_in_details]",
    ),
    (
        "console limit 400 not detected",
        "a2",
        "model_anthropic.py",
        "or (status == 400 and isinstance(msg, str) and msg.startswith(_LIMIT_MESSAGE))",
        "or (False)",
        "tests/test_model_anthropic.py::test_console_limit_400_is_provider_limit_not_breaker",
    ),
    (
        "cut error body parsed",
        "a2",
        "model_anthropic.py",
        "if len(raw) > _ERR_BODY_MAX:  # mut:err_cap",
        "if False:  # mut:err_cap",
        "tests/test_model_anthropic.py::test_provider_limit_detection_cases[body_cut_by_the_4_KB_cap]",
    ),
    (
        "retry-after rounded down",
        "a2",
        "model_anthropic.py",
        "return min(math.ceil(float(s)), 3600)  # mut:ra_parse",
        "return min(int(float(s)), 3600)  # mut:ra_parse",
        "tests/test_model_anthropic.py::test_retry_after_formats[1.5-2]",
    ),
    (
        "retry-after not capped",
        "a2",
        "model_anthropic.py",
        "return min(math.ceil(float(s)), 3600)  # mut:ra_parse",
        "return math.ceil(float(s))  # mut:ra_parse",
        "tests/test_model_anthropic.py::test_retry_after_formats[99999-3600]",
    ),
    (
        "request id not checked",
        "a2",
        "model_anthropic.py",
        '_REQUEST_ID = re.compile(r"req_[A-Za-z0-9]{8,64}", re.ASCII)',
        '_REQUEST_ID = re.compile(r"[\\s\\S]*")',
        "tests/test_model_anthropic.py::test_request_id_helper_accepts_only_the_documented_shape",
    ),
    (
        "sonnet may disable thinking",
        "a2",
        "model_anthropic.py",
        '"claude-sonnet-5-5": ({}, {"thinking": {"type": "between_tools"}}),',
        '"claude-sonnet-5-5": ({}, {"thinking": {"type": "between_tools"}}, {"thinking": {"type": "disabled"}}),',
        "tests/test_model_anthropic.py::test_disabled_thinking_refused_for_sonnet",
    ),
    (
        "wait above its cap accepted",
        "a2",
        "settings.py",
        "if model.fallback_wait_s > model.fallback_wait_max_s:",
        "if False:",
        "tests/test_df5_settings.py::test_the_wait_keys_have_defaults_ranges_and_an_order",
    ),
    (
        "unapproved read model accepted",
        "a2",
        "settings.py",
        "if model.tier_read not in model.approved_read_models:",
        "if False:",
        "tests/test_df5_settings.py::test_read_model_must_be_approved",
    ),
    (
        "any fallback model accepted",
        "a2",
        "settings.py",
        "if model.tier_fallback != model.tier_read and model.tier_fallback not in model.stronger_than_read:",
        "if False:",
        "tests/test_df5_settings.py::test_fallback_model_must_be_same_or_listed_stronger",
    ),
    (
        "send_temperature accepted",
        "a2",
        "settings.py",
        'if "send_temperature" in m:',
        "if False:",
        "tests/test_df5_settings.py::test_send_temperature_is_removed_and_refused",
    ),
    (
        "flat extra_body accepted",
        "a2",
        "settings.py",
        "if not isinstance(v, dict) or set(v) != set(TIER_KEYS):",
        "if not isinstance(v, dict):",
        "tests/test_model_review1.py::test_old_flat_extra_body_refused",
    ),
    (
        "bad purpose accepted",
        "a2",
        "settings.py",
        "if purpose not in PURPOSES:",
        "if False:",
        "tests/test_df5_settings.py::test_purpose_default_other_and_bad_value_refused",
    ),
    (
        "provider_limit missing from wall codes",
        "a2",
        "codes.py",
        '"provider_limit",  # mut:wall_provider_limit',
        "# mut:wall_provider_limit",
        "tests/test_codes.py::test_wall_codes_are_pinned_and_listed",
    ),
    (
        "prompt path back to v2",
        "a2",
        "prompt_file.py",
        '"prompts" / "extract_v3.txt"',
        '"prompts" / "extract_v2.txt"',
        "tests/test_money_path.py::test_prompt_path_single_constant",
    ),
    (
        "quality failure continues to the fallback",
        "a1",
        "extract.py",
        "        if error is None:\n            return done(None, bad, tier, r.model_id, None)  # mut:x10_stop",
        "        if error is None:\n            continue",
        "tests/test_extract.py::test_read_ungrounded_costs_one_call_only",
    ),
    (
        "retry-after cap removed",
        "a1",
        "extract.py",
        "return None if ra > m.fallback_wait_max_s else ra  # mut:ra_cap",
        "return ra",
        "tests/test_df5.py::test_retry_after_above_cap_makes_no_second_call[http_429]",
    ),
    (
        "wait cap off by one (the cap itself refused)",
        "a1",
        "extract.py",
        "return None if ra > m.fallback_wait_max_s else ra  # mut:ra_cap",
        "return None if ra >= m.fallback_wait_max_s else ra",
        "tests/test_df5.py::test_retry_after_at_the_cap_still_sleeps_and_calls_again",
    ),
    (
        "no sleep before the second call",
        "a1",
        "extract.py",
        "            _sleep(wait)  # mut:sleep",
        "            pass",
        "tests/test_df5.py::test_retry_after_5_sleeps_5_then_calls_again[http_429]",
    ),
    (
        "bad_reply back in FALLBACK_CODES",
        "a1",
        "model.py",
        'FALLBACK_CODES = frozenset({"timeout", "net", "tls", "http_429", "http_5xx"})',
        'FALLBACK_CODES = frozenset({"timeout", "net", "tls", "http_429", "http_5xx", "bad_reply"})',
        "tests/test_extract.py::test_fallback_codes_are_exactly_the_transport_codes",
    ),
    (
        "provider_limit retried",
        "a1",
        "model.py",
        'FALLBACK_CODES = frozenset({"timeout", "net", "tls", "http_429", "http_5xx"})',
        'FALLBACK_CODES = frozenset({"timeout", "net", "tls", "http_429", "http_5xx", "provider_limit"})',
        "tests/test_df5.py::test_no_fallback_after_a_stop_code[provider_limit]",
    ),
    (
        "transport streak removed",
        "a1",
        "extract.py",
        "return self.wall or self.n >= self._limit  # mut:streak",
        "return False",
        "tests/test_df5.py::test_five_transport_failures_in_a_row_stop_the_scan_and_a_success_resets",
    ),
    (
        "odd usage halts nothing",
        "a1",
        "model.py",
        'halt_reason = "estimate_exceeded"',
        "pass",
        "tests/test_df5.py::test_odd_usage_settles_at_reserved_and_halts_as_estimate_exceeded[extra0]",
    ),
    (
        "provider_limit does not halt",
        "a1",
        "model.py",
        'usage, halt_reason = None, "provider_limit"',
        "pass",
        "tests/test_df5.py::test_provider_limit_halts_ledger_stops_the_scan_and_is_not_the_breaker",
    ),
    (
        "max_tokens settled at reserved",
        "a1",
        "model.py",
        'result.error in (None, "max_tokens", "bad_reply")',
        'result.error in (None, "bad_reply")',
        "tests/test_df5.py::test_a_cut_off_or_refused_reply_settles_at_actual_usage_not_reserved[max_tokens]",
    ),
    (
        "bad_reply settled at reserved",
        "a1",
        "model.py",
        'result.error in (None, "max_tokens", "bad_reply")',
        'result.error in (None, "max_tokens")',
        "tests/test_df5.py::test_a_cut_off_or_refused_reply_settles_at_actual_usage_not_reserved[bad_reply]",
    ),
    (
        "http_5xx settled at usage",
        "a1",
        "model.py",
        'result.error in (None, "max_tokens", "bad_reply")',
        'result.error in (None, "max_tokens", "bad_reply", "http_5xx")',
        "tests/test_df5.py::test_no_usage_means_settled_at_the_reservation[res2]",
    ),
    (
        "unreadable Retry-After not flagged",
        "a1",
        "model_anthropic.py",
        "if ra_bad:  # mut:ra_bad",
        "if False:  # mut:ra_bad",
        "tests/test_model_anthropic.py::test_a_present_but_unreadable_retry_after_is_flagged_bad",
    ),
    (
        "repeated Retry-After takes the first",
        "a1",
        "model_anthropic.py",
        "return max(parsed), True, False  # mut:ra_max",
        "return parsed[0], True, False  # mut:ra_max",
        "tests/test_model_anthropic.py::test_a_repeated_retry_after_header_takes_the_max",
    ),
    (
        "odd 429 not flagged",
        "a1",
        "model_anthropic.py",
        'if status == 429 and etype != "rate_limit_error":  # mut:odd_429',
        "if False:  # mut:odd_429",
        "tests/test_model_anthropic.py::test_a_429_that_is_not_an_ordinary_rate_limit_is_flagged_odd",
    ),
    (
        "cache count not odd",
        "a1",
        "model_anthropic.py",
        "if cache_n > 0:  # mut:cache_odd",
        "if False:  # mut:cache_odd",
        "tests/test_model_anthropic.py::test_a_cache_count_makes_the_reply_odd_and_zero_does_not",
    ),
    (
        "thinking above output not odd",
        "a1",
        "model_anthropic.py",
        "if cw is None or cr is None or th is None or th > out_tok:",
        "if cw is None or cr is None or th is None:",
        "tests/test_model_anthropic.py::test_odd_usage_sets_the_flag_the_guard_halts_on",
    ),
    (
        "haiku disabled-thinking entry dropped",
        "a1",
        "model_anthropic.py",
        '"claude-haiku-5-5": ({}, {"thinking": {"type": "disabled"}}),',
        '"claude-haiku-5-5": ({},),',
        "tests/test_model_anthropic.py::test_haiku_accepts_only_the_disabled_thinking_shape",
    ),
    (
        "spend-limit second clause dead",
        "a1",
        "model_anthropic.py",
        "and not had_retry_after and",
        "and False and",
        "tests/test_model_anthropic.py::test_the_spend_limit_second_clause_needs_no_retry_after",
    ),
    (
        "prompt hash not recorded",
        "a1",
        "model_anthropic.py",
        ', "prompt_sha_sent": psha}',
        "}",
        "tests/test_model_anthropic.py::test_the_recorded_prompt_hash_is_the_hash_of_the_sent_bytes",
    ),
    (
        "unreadable Retry-After still retried",
        "a1",
        "extract.py",
        'if d.get("retry_after_bad"):  # mut:ra_bad_stop',
        "if False:  # mut:ra_bad_stop",
        "tests/test_df5.py::test_an_unreadable_retry_after_means_no_second_call",
    ),
    (
        "odd 429 still retried",
        "a1",
        "extract.py",
        'if code == "http_429" and (d.get("odd_429") or repeat_429):  # mut:odd_429_stop',
        'if code == "http_429" and (repeat_429):  # mut:odd_429_stop',
        "tests/test_df5.py::test_a_429_we_cannot_read_as_a_rate_limit_means_no_second_call",
    ),
    (
        "repeat 429 still retried",
        "a1",
        "extract.py",
        '(d.get("odd_429") or repeat_429)',
        '(d.get("odd_429"))',
        "tests/test_df5.py::test_a_429_on_two_documents_in_a_row_gets_no_second_call_on_the_second",
    ),
    (
        "timeout/net/tls wait is the configured wait",
        "a1",
        "extract.py",
        "return 0  # mut:wait_net",
        "return m.fallback_wait_s  # mut:wait_net",
        "tests/test_df5.py::test_timeout_net_tls_do_not_sleep",
    ),
    (
        "zero wait sleeps",
        "a1",
        "extract.py",
        "        if wait > 0:",
        "        if wait >= 0:",
        "tests/test_df5.py::test_retry_after_0_means_no_sleep_and_an_immediate_second_call",
    ),
    (
        "wall code does not stop the scan",
        "a1",
        "extract.py",
        "if doc.error in SCAN_STOP_CODES or (doc.error in _NO_NETWORK and doc.refusal in SCAN_STOP_CODES):  # mut:wall_stop",
        "if False:  # mut:wall_stop",
        "tests/test_df5.py::test_a_wall_code_stops_the_scan_before_the_transport_count",
    ),
    (
        "streak ignores the wall",
        "a1",
        "extract.py",
        "return self.wall or self.n >= self._limit  # mut:streak",
        "return self.n >= self._limit  # mut:streak",
        "tests/test_df5.py::test_a_real_scan_loop_stops_on_the_first_wall_code",
    ),
    (
        "previous 429 not remembered",
        "a1",
        "extract.py",
        'self.prev_429 = sent[-1].error == "http_429"  # mut:prev_429',
        "self.prev_429 = False  # mut:prev_429",
        "tests/test_df5.py::test_a_429_on_two_documents_in_a_row_gets_no_second_call_on_the_second",
    ),
    (
        "pipeline never feeds the streak",
        "a1",
        "pipeline.py",
        "streak.add(doc)  # mut:pipeline_streak",
        "pass  # mut:pipeline_streak",
        "tests/test_df5.py::test_a_real_scan_loop_over_pipeline_process_stops_after_five_transport_failures",
    ),
    (
        "approved_read_models absent is accepted",
        "a1",
        "settings.py",
        "        if default is None:",
        "        if False:",
        "tests/test_df5_settings.py::test_approved_read_models_absent_or_null_is_refused",
    ),
    (
        "prose counter never counts",
        "a1",
        "budget.py",
        "elif error == STOP_PROSE:  # mut:prose_counter",
        "elif False:  # mut:prose_counter",
        "tests/test_df5_b3.py::test_ten_prose_documents_halt_nine_do_not",
    ),
    (
        "hostile counter never counts",
        "a1",
        "budget.py",
        "elif error == HOSTILE_SHAPE:  # mut:hostile_counter",
        "elif False:  # mut:hostile_counter",
        "tests/test_df5_b3.py::test_three_hostile_shaped_replies_halt_with_their_own_reason",
    ),
    (
        "valid reply does not reset the prose count",
        "a1",
        "budget.py",
        '_set_meta(c, "prose_streak", 0)',
        "pass",
        "tests/test_df5_b3.py::test_a_valid_tool_reply_resets_the_prose_count",
    ),
    (
        "valid reply does not reset the hostile count",
        "a1",
        "budget.py",
        '_set_meta(c, "hostile_streak", 0)',
        "pass",
        "tests/test_df5_b3.py::test_a_valid_reply_resets_the_hostile_count",
    ),
    (
        "prose back in the breaker",
        "a1",
        "model.py",
        'if result.error == "bad_reply" and usage is not None and stop in PROSE_STOPS:  # mut:prose_not_breaker',
        "if False:  # mut:prose_not_breaker",
        "tests/test_df5_b3.py::test_ten_prose_documents_halt_nine_do_not",
    ),
    (
        "hostile shapes back in the breaker",
        "a1",
        "model.py",
        'elif result.error == "max_tokens" or stop:  # mut:hostile_class',
        "elif False:  # mut:hostile_class",
        "tests/test_df5_b3.py::test_three_hostile_shaped_replies_halt_with_their_own_reason",
    ),
    (
        "usage taken without the billable check",
        "a1",
        "model.py",
        " and budget_mod.valid_usage(tokens) is not None:  # mut:usage_guard",
        ":  # mut:usage_guard",
        "tests/test_df5_b3.py::test_a_prose_reply_without_usable_usage_is_not_prose_class_and_feeds_the_breaker",
    ),
    (
        "model_mismatch outranks odd usage (order swapped)",
        "a1",
        "model.py",
        "if odd:  # mut:odd_first",
        "if odd and not mismatch:  # mut:odd_first",
        "tests/test_df5.py::test_odd_usage_settles_at_reserved_and_halts_as_estimate_exceeded",
    ),
    (
        "cooldown never refuses",
        "a1",
        "budget.py",
        "if until and clock() < float(until):  # mut:cooldown",
        "if False:  # mut:cooldown",
        "tests/test_df5_b3.py::test_the_limit_starts_a_cooldown_that_refuses_new_reserves_until_it_ends",
    ),
    (
        "transport window ignored",
        "a1",
        "budget.py",
        "if now - last > m.transport_window_s:  # mut:transport_window",
        "if False:  # mut:transport_window",
        "tests/test_df5_b3.py::test_a_pause_longer_than_the_window_restarts_the_count",
    ),
    (
        "add counts the same document twice",
        "a1",
        "extract.py",
        "if id(doc) in self._seen:  # mut:idempotent",
        "if False:  # mut:idempotent",
        "tests/test_df5_b3.py::test_add_is_idempotent_per_document_object",
    ),
    (
        "repeated refusals do not stop the scan",
        "a1",
        "extract.py",
        "(doc.error in _NO_NETWORK and doc.refusal in SCAN_STOP_CODES)",
        '(doc.error in _NO_NETWORK and doc.refusal in ("budget_total",))',
        "tests/test_df5_b3.py::test_a_refusal_that_repeats_for_every_document_stops_the_scan",
    ),
    (
        "prose reply not flagged as prose",
        "a1",
        "extract.py",
        'prose_stop.append(error == "bad_reply" and d.get("stop_reason") in PROSE_STOPS)',
        "prose_stop.append(False)",
        "tests/test_df5_b3.py::test_a_prose_reply_is_flag_l03_not_the_outage_flag",
    ),
    (
        "pipeline ignores the prose reason",
        "a1",
        "pipeline.py",
        "elif doc.prose:",
        "elif False:",
        "tests/test_df5_b3.py::test_a_prose_reply_is_flag_l03_not_the_outage_flag",
    ),
    (
        "stop reason not stored",
        "a1",
        "budget.py",
        'stop = stop_reason if stop_reason in KNOWN_STOPS else ("other" if stop_reason else None)',
        "stop = None",
        "tests/test_df5_b3.py::test_the_stop_reason_word_is_stored_in_the_calls_table",
    ),
    (
        "old ledger not given the column",
        "a1",
        "budget.py",
        'if not any(r[1] == "stop_reason" for r in c.execute("PRAGMA table_info(calls)").fetchall()):',
        "if False:",
        "tests/test_df5_b3.py::test_an_old_ledger_without_the_column_gets_it_when_settling",
    ),
    (
        "every non-global region is odd again",
        "a1",
        "model_anthropic.py",
        'if u.get("inference_geo") in _GEO_PRICED and geo_permille == 1000:  # mut:geo_priced',
        'if u.get("inference_geo") not in (None, "global") and geo_permille == 1000:  # mut:geo_priced',
        "tests/test_df5_b3.py::test_only_a_region_with_a_known_price_effect_is_odd",
    ),
    (
        "nested cache counts ignored",
        "a1",
        "model_anthropic.py",
        "if cc is not None and (not isinstance(cc, dict) or any(_count(v) is None or _count(v) > 0 for v in cc.values())):  # mut:nested_cache",
        "if False:  # mut:nested_cache",
        "tests/test_df5_b3.py::test_nested_cache_creation_counts_follow_the_flat_rule",
    ),
    (
        "late 429 body is a hostile 4xx again",
        "a1",
        "model_anthropic.py",
        "if status == 429:  # mut:late_429",
        "if False:  # mut:late_429",
        "tests/test_df5_b3.py::test_a_late_429_body_is_http_429_without_retry_not_a_hostile_reply",
    ),
    (
        "display name family not compared",
        "a1",
        "settings.py",
        "if other_family:  # mut:family_equal",
        "if False:  # mut:family_equal",
        "tests/test_df5_settings.py::test_a_label_must_name_the_same_family_as_its_id",
    ),
    (
        "display names may name unconfigured models",
        "a1",
        "settings.py",
        "if not set(model.display_names) <= configured:  # mut:names_configured",
        "if False:  # mut:names_configured",
        "tests/test_df5_settings.py::test_display_names_may_only_name_configured_models",
    ),
    (
        "gate: streak never read accepted",
        "a1",
        "tools/scan_gate.py",
        'elif not (isinstance(kw.value, ast.Name) and kw.value.id == "streak" and "streak" in params) and not reads_stop:',
        "elif False:",
        "tests/test_scan_gate.py::test_bad_shape_is_reported",
    ),
    (
        "gate: getattr bypass accepted",
        "a1",
        "tools/scan_gate.py",
        "if s in TARGETS and TARGETS[s] != module:",
        "if False:",
        "tests/test_scan_gate.py::test_bad_shape_is_reported",
    ),
    (
        "gate: renaming import accepted",
        "a1",
        "tools/scan_gate.py",
        "if a.asname and a.asname != a.name:",
        "if False:",
        "tests/test_scan_gate.py::test_bad_shape_is_reported",
    ),
    (
        "gate: bare name passed on accepted",
        "a1",
        "tools/scan_gate.py",
        "elif isinstance(n, ast.Name) and n.id in direct and id(n) not in call_funcs and not isinstance(n.ctx, ast.Store):",
        "elif False:",
        "tests/test_scan_gate.py::test_bad_shape_is_reported",
    ),
    (
        "late non-429 4xx becomes a plain timeout",
        "a1",
        "model_anthropic.py",
        "elif 400 <= status <= 499:  # mut:late_status",
        "elif False:  # mut:late_status",
        "tests/test_model_anthropic.py::test_a_non_429_4xx_body_that_trickles_past_the_deadline_is_http_4xx",
    ),
    (
        "gate: call without streak= accepted (report dropped)",
        "a1",
        "tools/scan_gate.py",
        'out.append(f"line {n.lineno}: {t} called without streak=")  # mut:gate_no_kw',
        "pass  # mut:gate_no_kw",
        "tests/test_scan_gate.py::test_bad_shape_is_reported",
    ),
]


def pytest_cmd(targets: list[str]) -> list[str]:
    return [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "--tb=no", "-rfE", *targets]


WORK = ROOT  # the tree the tests run in: a SCRATCH COPY while mutating (the real tree is never written)
WSRC = SRC
# the only failure messages that count as a kill: a failed assert, an AssertionError, pytest.fail ("Failed:") or a strict xfail that passed
GOOD_KILL = re.compile(r"^(assert\b|AssertionError\b|Failed:|\[XPASS|model_support\.UnexpectedCall\b)")


def kill_tree(proc: subprocess.Popen) -> None:
    """A test may start children (one racing test does): kill the whole tree, or a grandchild keeps the scratch copy open (Windows)."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
    else:
        import signal

        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass
    proc.kill()


def run_pytest(targets: list[str]) -> tuple[int, str]:
    env = {
        **os.environ,
        "COLUMNS": "400",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(WORK / "src") + os.pathsep + os.environ.get("PYTHONPATH", ""),
    }
    flags = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    proc = subprocess.Popen(pytest_cmd(targets), cwd=WORK, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, **flags)
    try:
        out, _ = proc.communicate(timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        kill_tree(proc)
        proc.communicate()
        return -9, "timeout"
    return proc.returncode, out


def purge_pyc() -> None:
    """A stale byte-code file (same size, same second as the restored source) would silently keep running the mutant: delete them all."""
    for c in (WSRC / "__pycache__").glob("*.pyc"):
        c.unlink(missing_ok=True)


def first_failed(out: str) -> str:
    m = re.search(r"^FAILED (.+?)(?: - |$)", out, re.M)  # a parameter id may hold spaces
    return m.group(1).strip() if m else "?"


def first_message(out: str) -> str:
    m = re.search(r"^FAILED .+? - (.*)$", out, re.M)
    return m.group(1) if m else ""


def is_kill(rc: int, out: str, must_fail: str | None) -> tuple[bool, str]:
    """KILLED only when pytest exits 1 with a FAILED line, no ERROR line (a collection or import error is not a kill), a failure message that is not an
    import/attribute/syntax error, and, when ``must_fail`` is named, the first failing test is that test (parameter ids are ignored)."""
    if rc != 1:
        return False, f"pytest rc {rc}"
    if re.search(r"^ERROR ", out, re.M):
        return False, "collection or setup error is not a kill"
    first = first_failed(out)
    if first == "?":
        return False, "no FAILED line"
    if not GOOD_KILL.match(first_message(out)):
        return False, f"killed by {first_message(out)[:40]!r}, not by an assertion"
    if must_fail and first.split("[")[0] != must_fail.split("[")[0]:
        return False, f"a different test failed first: {first}"
    return True, first


def sweep_stale(max_age_s: int = 3600) -> None:
    """A killed run can leave its scratch copy behind: remove old ones (never the ones a live run just made)."""
    import time

    for d in ROOT.parent.glob("mut-*"):
        try:
            if d.is_dir() and time.time() - d.stat().st_mtime > max_age_s:
                shutil.rmtree(d, ignore_errors=True)
        except OSError:
            pass


def scratch_copy() -> Path:
    """Only the files git tracks (no untracked secrets, local data or caches), never following a symlink."""
    sweep_stale()
    files = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout.split(b"\0")
    dst = Path(tempfile.mkdtemp(prefix="mut-", dir=ROOT.parent)) / "repo"
    for raw in files:
        if not raw:
            continue
        rel = raw.decode("utf-8")
        src = ROOT / rel
        if src.is_symlink() or not src.is_file():
            continue
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst / rel)
    return dst


def main() -> int:
    global WORK, WSRC
    argv = sys.argv[1:]
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    package = argv[argv.index("--package") + 1] if "--package" in argv else "all"
    if package != "all" and package not in PACKAGES:
        print(f"unknown package {package}")
        return 4
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "src", "tools"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if dirty:  # modified, staged AND untracked files
        print("src or tools has uncommitted or untracked changes (mutants would be measured against a moving tree); commit first")
        return 4
    chosen = [m for m in MUTANTS if (package == "all" or m[1] == package) and (not only or only in m[0])]
    nodes = sorted({m[5] for m in chosen if m[5]})
    work = scratch_copy()
    WORK, WSRC = work, work / "src" / "intake"
    bad = 0
    try:
        imp = subprocess.run(
            [sys.executable, "-c", "import intake,sys;print(intake.__file__)"],
            cwd=WORK,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": str(WORK / "src")},
        ).stdout.strip()
        if not Path(imp).resolve().is_relative_to(WORK.resolve()):
            print(f"the tests would import {imp}, not the scratch copy; aborting")
            return 4
        rc, out = run_pytest([*TESTS, *nodes])  # the unmutated suite, and every must_fail node, must be green first
        if rc != 0:
            print(f"baseline is not green (rc {rc}); aborting\n{out[-600:]}")
            return 4

        def target(f: str) -> Path:
            return WORK / f if f.startswith("tools/") else WSRC / f

        originals = {f: target(f).read_bytes() for f in {m[2] for m in chosen}}
        for name, _pkg, f, old, new, must_fail in chosen:
            text = originals[f].decode("utf-8")
            if text.count(old) != 1:
                print(f"CRASH      {name} :: pattern found {text.count(old)} times")
                bad += 1
                continue
            target(f).write_bytes(text.replace(old, new).encode("utf-8"))
            purge_pyc()
            rc, out = run_pytest([must_fail] if must_fail else TESTS)
            target(f).write_bytes(originals[f])  # restore at once: the next mutant must start from the original of EVERY file
            purge_pyc()
            killed, why = is_kill(rc, out, must_fail)
            if killed:
                print(f"KILLED     {name} :: {why}")
            elif rc == 0:
                print(f"SURVIVED   {name}")
                bad += 1
            else:
                print(f"CRASH      {name} :: {why}")
                bad += 1
    finally:
        WORK = ROOT
        shutil.rmtree(work.parent, ignore_errors=True)
    clean = not subprocess.run(
        ["git", "status", "--porcelain", "--", "src", "tools"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    print(f"scratch copy removed; real src clean vs HEAD: {clean}; not killed: {bad} of {len(chosen)}")
    return 1 if bad or not clean else 0


if __name__ == "__main__":
    sys.exit(main())
