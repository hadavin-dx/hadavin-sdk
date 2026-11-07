"""The mutants of the provider error plumbing (provider errors): 54 live mutants, M1 to M57 without the three deleted ones (M26, M34, M36).

Each mutant changes ONE thing in a temp copy of the package (``tools.mutation_runner`` does the copy). The test named in ``only_test``
must fail, it must be the test pinned in ``pinned``, and the first failing line must hold ``expect``: a fragment of the assertion
MESSAGE or of the compared values that test gives for that one guard (never a fragment of the test's own name). Not collected by
pytest. Search strings are exact copies of the formatted source; ``check_search_strings`` fails if one occurs 0 times. Run from the
repo root:

    uv run python tests/provider_mutants.py            # all mutants; exit 1 if any is not good
    uv run python tests/provider_mutants.py M20        # only mutants whose name contains the text
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
W = "tests/test_provider_errors_wire.py"
F = "tests/test_provider_errors_failbefore.py"
FA = "tests/test_provider_facts.py"
D = "tests/test_diagnostic.py"
NR = "tests/test_never_raise_guards.py"
TESTS = [W, F, FA, D, NR, "tests/test_diagnostic_codes.py",
         "tests/provider_wire_helpers.py", "tests/import_order_child.py"]  # fmt: skip
S = "src/hadavin_sdk/"
RT, PF, PR, AN, BD, DG, CD, NV = (
    S + "llm/retry.py", S + "llm/provider_facts.py", S + "llm/protocol.py", S + "llm/anthropic.py",
    S + "llm/bedrock.py", S + "guard/diagnostic.py", S + "codes.py", S + "neverraise.py",
)  # fmt: skip

# (number, name, file, old, new, killer function, killer file, expect, pinned id or "")
SPECS: list[tuple[str, str, str, str, str, str, str, str, str]] = []


# Measured by the P1m runner on the head: (a fragment of the first failing line, the test that must be the one failing).
_KILL: dict[str, tuple[str, str]] = {
    "M1": (
        "AssertionError: (0, 'bedrock-code', 'bedrock: An",
        "tests/test_provider_errors_failbefore::test_r6_500_random_hostile_failures_keep_the_message_grammar",
    ),
    "M2": (
        "AssertionError: assert (429, None, 3, True) == (",
        "tests/test_provider_errors_wire::test_r16_every_modelled_converse_code[ThrottlingException]",
    ),
    "M3": (
        "AssertionError: assert 'req_AAAAAAAAAAAAAAAAAAAA",
        "tests/test_provider_errors_failbefore::test_r5_claude_request_ids['req_AAAAAAAAA]",
    ),
    "M4": (
        "AssertionError: assert 'req_AAAAAAAAAAAAAAAAAAAA",
        "tests/test_provider_errors_failbefore::test_r5_claude_request_ids['req_AAAAAAAAA]",
    ),
    "M5": (
        "AssertionError: assert 0 is None",
        "tests/test_provider_facts::test_r3_a_wrong_type_or_range_becomes_none_and_never_raises[status-0]",
    ),
    "M6": (
        "AssertionError: a raw AttributeError escaped wit",
        "tests/test_provider_errors_failbefore::test_r5_hook_returning_the_wrong_type_or_a_subclass_or_raising_gives_no_facts",
    ),
    "M7": (
        "assert (0, False) == (1, False)",
        "tests/test_provider_errors_wire::test_r1_golden_wire_rows[row1-anthropic]",
    ),
    "M8": (
        "assert (1, True) == (1, False)",
        "tests/test_provider_errors_wire::test_r1_golden_wire_rows[row1-anthropic]",
    ),
    "M9": (
        "AssertionError: ['bool', 'len']",
        "tests/test_provider_facts::test_r4d_a_str_body_is_never_read_or_measured",
    ),
    "M10": (
        "AssertionError: assert (None, None, None, None, ",
        "tests/test_provider_facts::test_r3_pickle_and_copy_keep_the_attributes[ProviderError]",
    ),
    "M11": (
        "AssertionError: assert 'rate_limit' == 'authenti",
        "tests/test_provider_errors_failbefore::test_r5_claude_body_cases[dict-subclass-body-401]",
    ),
    "M12": (
        "AssertionError: {'args'}",
        "tests/test_provider_facts::test_r4a_direct_adapter_reads_only_its_allow_list[anthropic]",
    ),
    "M13": (
        "AssertionError: assert 'rate_limit' is None",
        "tests/test_provider_facts::test_r3_a_wrong_type_or_range_becomes_none_and_never_raises[error_type-rate_limit]",
    ),
    "M14": (
        "assert (1 == 3)",
        "tests/test_provider_errors_wire::test_r2_claude_library_777_is_retried_three_times",
    ),
    "M15": (
        "assert (False is True)",
        "tests/test_provider_errors_failbefore::test_r8a_refused_at_once_closes_the_connection_without_a_read",
    ),
    "M16": (
        "AssertionError: with_retry still takes a detail ",
        "tests/test_provider_errors_failbefore::test_r9_detail_hook_is_removed_everywhere",
    ),
    "M17": (
        "AssertionError: assert 'bedrock: Thr...er 3 atte",
        "tests/test_provider_errors_wire::test_r16_every_modelled_converse_code[ThrottlingException]",
    ),
    "M18": (
        "AssertionError: assert (<class 'hadavin_sdk.llm.",
        "tests/test_provider_errors_wire::test_r1_row10_vertex_refresh_error_is_authentication",
    ),
    "M19": (
        "AssertionError: assert 'req_AbCd1234Ef56Gh78' is",
        "tests/test_provider_facts::test_r19_each_kind_accepts_only_its_own_request_id_shape",
    ),
    "M20": (
        "AssertionError: a raw RuntimeError escaped with_",
        "tests/test_provider_errors_failbefore::test_r10_a_wait_computation_that_raises_is_a_decision_failure[headers.get-raises]",
    ),
    "M21": (
        "assert (1, False) == (2, False)",
        "tests/test_provider_errors_wire::test_r1_golden_wire_rows[row29-anthropic]",
    ),
    "M22": (
        "AssertionError: assert 1001 is None",
        "tests/test_provider_facts::test_r3_a_wrong_type_or_range_becomes_none_and_never_raises[retry_count-1001]",
    ),
    "M23": (
        "AssertionError: assert {429: <Provid...equest'>,",
        "tests/test_provider_facts::test_t_s_status_table_both_directions",
    ),
    "M24": (
        "AssertionError: assert {'rate_limit_...cation'>,",
        "tests/test_provider_facts::test_t_c_claude_table_both_directions",
    ),
    "M25": (
        "AssertionError: assert 'ABCDEFGHIJ' == None",
        "tests/test_provider_errors_failbefore::test_r5_claude_request_ids['ABCDEFGHIJ']",
    ),
    "M27": (
        "assert (None, <Provi...>, None, None) == (418, <",
        "tests/test_provider_errors_wire::test_r1_row28_a_provider_error_raised_in_call_passes_through_unchanged",
    ),
    "M28": (
        "AssertionError: assert (401 is None)",
        "tests/test_provider_errors_failbefore::test_r5_hook_returning_the_wrong_type_or_a_subclass_or_raising_gives_no_facts",
    ),
    "M29": (
        "assert (None is not None)",
        "tests/test_provider_errors_failbefore::test_r5_bedrock_code_not_a_short_exact_string_gives_the_status_type[str-subclass]",
    ),
    "M30": (
        "AssertionError: assert <ProviderErrorType.quota:",
        "tests/test_provider_facts::test_t_l_a_65_character_key_is_never_looked_up",
    ),
    "M31": (
        "AssertionError: a raw RuntimeError escaped with_",
        "tests/test_provider_errors_failbefore::test_r8c_a_close_that_raises_never_replaces_the_real_error",
    ),
    "M32": (
        "assert ([False, False, True] == [True, True, Tru",
        "tests/test_provider_errors_failbefore::test_r8b_three_retried_attempts_close_all_three",
    ),
    "M33": (
        "AssertionError: assert (None, <Provi...on'>, 3, ",
        "tests/test_provider_errors_wire::test_r1_stand_in_rows[row9]",
    ),
    "M35": (
        "AssertionError: a raw RuntimeError escaped with_",
        "tests/test_provider_errors_failbefore::test_r5_a_decision_that_crashed_is_the_billed_class[status_code-raises]",
    ),
    "M37": (
        "AssertionError: assert (<class 'hadavin_sdk.llm.",
        "tests/test_provider_errors_failbefore::test_r10_a_wait_computation_that_raises_is_a_decision_failure[headers.get-raises]",
    ),
    "M38": (
        "AssertionError: (<function facts at ",
        "tests/test_provider_facts::test_r19_bare_exceptions_give_the_class_based_types[bedrock]",
    ),
    "M39": (
        "AssertionError: assert (URLError(OSError('CANARY",
        "tests/test_provider_errors_failbefore::test_r17_the_traceback_never_prints_the_original_error_text[urlerror-reason]",
    ),
    "M40": (
        "AssertionError: {'reason.__str__'}",
        "tests/test_provider_facts::test_r4a_direct_adapter_reads_only_its_allow_list[default]",
    ),
    "M41": (
        "AssertionError: assert <class 'hadavin_sdk.llm.p",
        "tests/test_provider_errors_failbefore::test_r5_a_decision_that_crashed_is_the_billed_class[status_code-raises]",
    ),
    "M42": (
        "AssertionError: ('request_id', 'rrrrrrrrrrrrrrrr",
        "tests/test_diagnostic::test_provider_attributes_are_read_with_exact_types",
    ),
    "M43": (
        "AssertionError: assert 'provider_rate_limit' == ",
        "tests/test_diagnostic::test_provider_codes_follow_status_then_type",
    ),
    "M44": (
        "AssertionError: ('status', True, 'error_type', '",
        "tests/test_diagnostic::test_provider_attributes_are_read_with_exact_types",
    ),
    "M45": (
        "AssertionError: assert 'provider_auth' == 'provi",
        "tests/test_diagnostic::test_provider_codes_follow_status_then_type",
    ),
    "M46": (
        "assert ((None, 3) == (None, 2)",
        "tests/test_provider_errors_failbefore::test_r5_attempt_two_hook_failure_is_billed_with_attempt_two",
    ),
    "M47": (
        "AssertionError: assert 'permission' == 'other'",
        "tests/test_provider_errors_failbefore::test_r5_claude_body_cases[type-injected-short-code]",
    ),
    "M49": (
        "AssertionError: assert {} == {'diag_class_name': 1}",
        "tests/test_never_raise_guards::test_every_diagnostic_guard_site_records_into_the_shared_counter[class_name]",
    ),
    "M50": (
        "AssertionError: a retried 429 is not an absorbed fault",
        "tests/test_never_raise_guards::test_an_ordinary_retried_failure_is_not_counted_and_a_genuine_fault_is",
    ),
    "M51": (
        "AssertionError: record() blocked on a lock held by its own thread",
        "tests/test_never_raise_guards::test_record_can_be_entered_again_on_the_same_thread",
    ),
    "M52": (
        "AssertionError: a production module does not expose a way to zero the counters",
        "tests/test_never_raise_guards::test_one_counter_not_two",
    ),
    "M53": (
        "AssertionError: SqlReadError: diag_v=1 code=config_invalid",
        "tests/test_diagnostic_codes::test_a_sql_file_that_cannot_be_read_is_a_repository_defect_not_an_operator_config_error",
    ),
    "M54": (
        "AssertionError: the loop stops: no further request after a failed wait computation",
        "tests/test_never_raise_guards::test_a_failed_wait_computation_stops_the_loop_and_is_recorded",
    ),
    "M55": (
        "AssertionError: assert {} == {'retry_wait': 1}",
        "tests/test_never_raise_guards::test_a_failed_wait_computation_stops_the_loop_and_is_recorded",
    ),
    "M56": (
        "AssertionError: tests/fixtures/guard_ledger.txt and the except-Exception handlers",
        "tests/test_never_raise_guards::test_ledger_lists_exactly_the_guards_in_the_code_by_file_function_and_site",
    ),
    "M57": (
        "AssertionError: a Site member that no guard records",
        "tests/test_never_raise_guards::test_every_site_name_is_recorded_by_exactly_one_guard_and_none_is_dead",
    ),
    "M48": (
        "AssertionError: a raw RuntimeError escaped with_",
        "tests/test_provider_errors_failbefore::test_r5_a_decision_that_crashed_is_the_billed_class[bool-raises-BN1c]",
    ),
}


def spec(num, name, file, old, new, killer, test_file, expect="", pinned=""):
    expect, pinned = expect or _KILL[num][0], pinned or _KILL[num][1]
    SPECS.append((num, name, file, old, new, killer, test_file, expect, pinned))


# --- the message grammar and the retry loop -----------------------------------------------------------------------------------
spec("M1", "the message is built from str(exc) again", RT,
     'f"{label}: {describe(exc, f)}",', 'f"{label}: {exc}",',
     "test_r6_500_random_hostile_failures_keep_the_message_grammar", F)  # fmt: skip
spec("M2", "bedrock.facts uses the raw error code, not the closed table", BD,
     "error_type = _CODE_TYPE.get(code, ProviderErrorType.other)", "error_type = code",
     "test_r16_every_modelled_converse_code", W)  # fmt: skip
spec("M3", "the request-id shape check is removed", PF,
     "if pattern.fullmatch(value) is not None:", "if True:",
     "test_r5_claude_request_ids", F)  # fmt: skip
spec("M4", "the request-id check uses match, not fullmatch", PF,
     "if pattern.fullmatch(value) is not None:", "if pattern.match(value) is not None:",
     "test_r5_claude_request_ids", F)  # fmt: skip
spec("M5", "clean_status has no range check", PF,
     "return value if type(value) is int and lo <= value <= hi else None",
     "return value if type(value) is int else None",
     "test_r3_a_wrong_type_or_range_becomes_none_and_never_raises", FA)  # fmt: skip
spec("M6", "safe_facts is bypassed (an adapter exception escapes)", RT,
     "safe_facts(facts or default_facts, exc)", "(facts or default_facts)(exc)",
     "test_r5_hook_returning_the_wrong_type_or_a_subclass_or_raising_gives_no_facts", F)  # fmt: skip
spec("M7", "retry_count is counted from 0", RT,
     "retry_count=attempt,", "retry_count=attempt - 1,",
     "test_r1_golden_wire_rows", W)  # fmt: skip
spec("M8", "retryable is always True on a refusal", RT,
     "retryable=False,", "retryable=True,",
     "test_r1_golden_wire_rows", W)  # fmt: skip
spec("M9", "anthropic.facts measures a str body", AN,
     "    if type(body) is not dict:\n        return None\n",
     "    if type(body) is not dict:\n        return None if len(body or '') < 0 else None\n",
     "test_r4d_a_str_body_is_never_read_or_measured", FA)  # fmt: skip
spec("M10", "pickling drops the attributes", PR,
     "    retry_count: int | None = None\n\n    def __init__(",
     "    retry_count: int | None = None\n\n    def __reduce__(self):\n        return (type(self), self.args)\n\n    def __init__(",
     "test_r3_pickle_and_copy_keep_the_attributes", FA)  # fmt: skip
spec("M11", "isinstance(body, dict) instead of the exact type", AN,
     "if type(body) is not dict:", "if not isinstance(body, dict):",
     "test_r5_claude_body_cases", F)  # fmt: skip
spec("M12", "anthropic.facts reads exc.args", AN,
     'status = clean_status(safe_attr(exc, "status_code"))',
     'status = clean_status(safe_attr(exc, "status_code")) if safe_attr(exc, "args") is not None else None',
     "test_r4a_direct_adapter_reads_only_its_allow_list", FA)  # fmt: skip
spec("M13", "the constructor stores an unchecked error_type", PR,
     "self.error_type = clean_error_type(error_type)", "self.error_type = error_type",
     "test_r3_a_wrong_type_or_range_becomes_none_and_never_raises", FA)  # fmt: skip
spec("M14", "transient reads the status through clean_status", RT,
     "    code = status(exc)\n", "    code = clean_status(status(exc))\n",
     "test_r2_claude_library_777_is_retried_three_times", W)  # fmt: skip
spec("M15", "a failed HTTPError is not closed", RT,
     "            _close_failed_http(exc)\n            try:\n                decision",
     "            try:\n                decision",
     "test_r8a_refused_at_once_closes_the_connection_without_a_read", F)  # fmt: skip
spec("M16", "the detail text hook is reintroduced", RT,
     "    facts: Facts | None = None,\n) -> T:",
     "    facts: Facts | None = None,\n    detail: Callable[[BaseException], str] | None = None,\n) -> T:",
     "test_r9_detail_hook_is_removed_everywhere", F)  # fmt: skip
spec("M17", "describe prints the class __name__", RT,
     "class_text = class_name_of(exc)", "class_text = type(exc).__name__",
     "test_r16_every_modelled_converse_code", W)  # fmt: skip
spec("M18", "the Google refresh error becomes other", AN,
     "    if isinstance(exc, google_auth.RefreshError):\n        return ProviderErrorType.authentication",
     "    if isinstance(exc, google_auth.RefreshError):\n        return ProviderErrorType.other",
     "test_r1_row10_vertex_refresh_error_is_authentication", W)  # fmt: skip
spec("M19", "bedrock.facts accepts any request-id shape", BD,
     'clean_request_id(_dict_get(meta, "RequestId"), "uuid")', 'clean_request_id(_dict_get(meta, "RequestId"))',
     "test_r19_each_kind_accepts_only_its_own_request_id_shape", FA)  # fmt: skip
spec("M20", "the guard around the wait computation is removed", RT,
     "            try:\n                wait = max(jitter, retry_after(exc))\n"
     "            except Exception:  # noqa: BLE001 - never-raise guard: a crashed wait is booked as billed, never raised raw\n"
     "                record(Site.retry_wait)\n"
     "                raise _billed(exc, label, attempt, facts) from None\n",
     "            wait = max(jitter, retry_after(exc))\n",
     "test_r10_a_wait_computation_that_raises_is_a_decision_failure", F)  # fmt: skip
spec("M21", "retry_count stays 1 across a retried refusal", RT,
     "                    retryable=False,\n                    retry_count=attempt,",
     "                    retryable=False,\n                    retry_count=1,",
     "test_r1_golden_wire_rows", W)  # fmt: skip
spec("M22", "the retry_count bound admits 1001", CD,
     "FactKey.retry_count: (0, 1000),", "FactKey.retry_count: (0, 1001),",
     "test_r3_a_wrong_type_or_range_becomes_none_and_never_raises", FA)  # fmt: skip
spec("M23", "the 408 row of the status table is dropped", CD,
     "        408: ProviderErrorType.timeout,\n", "",
     "test_t_s_status_table_both_directions", FA)  # fmt: skip
spec("M24", "the timeout_error row of the Claude table is dropped", AN,
     '    "timeout_error": ProviderErrorType.timeout,\n', "",
     "test_t_c_claude_table_both_directions", FA)  # fmt: skip
spec("M25", "anthropic accepts a request id without req_", CD,
     '"prefixed": r"req_[A-Za-z0-9]{8,36}",', '"prefixed": r"(req_)?[A-Za-z0-9]{8,36}",',
     "test_r5_claude_request_ids", F)  # fmt: skip
spec("M27", "a ProviderError raised in call is rebuilt", RT,
     "        except ProviderError:\n            raise\n",
     "        except ProviderError as pe:\n            pe.status = None\n            raise\n",
     "test_r1_row28_a_provider_error_raised_in_call_passes_through_unchanged", W)  # fmt: skip
spec("M28", "safe_facts accepts a subclass", PF,
     "return got if type(got) is ProviderFacts else NO_FACTS", "return got if isinstance(got, ProviderFacts) else NO_FACTS",
     "test_r5_hook_returning_the_wrong_type_or_a_subclass_or_raising_gives_no_facts", F)  # fmt: skip
spec("M29", "bedrock.facts accepts any str code of any length", BD,
     "if type(code) is str and len(code) <= TYPE_NAME_MAX:", "if isinstance(code, str):",
     "test_r5_bedrock_code_not_a_short_exact_string_gives_the_status_type", F)  # fmt: skip
spec("M30", "the length bound is removed from the Claude type lookup", AN,
     "if type(word) is str and len(word) <= TYPE_NAME_MAX:", "if type(word) is str:",
     "test_t_l_a_65_character_key_is_never_looked_up", FA)  # fmt: skip
spec("M31", "the close step is not inside try/except", RT,
     "    try:\n        if isinstance(exc, urllib.error.HTTPError):\n            exc.close()\n"
     "    except Exception:  # noqa: BLE001 - never-raise guard: a close that fails never replaces the real provider error\n"
     "        record(Site.retry_close_failed_http)\n",
     "    if isinstance(exc, urllib.error.HTTPError):\n        exc.close()\n",
     "test_r8c_a_close_that_raises_never_replaces_the_real_error", F)  # fmt: skip
spec("M32", "only the last failed HTTPError is closed", RT,
     "            _close_failed_http(exc)\n", "            if attempt == max_attempts:\n                _close_failed_http(exc)\n",
     "test_r8b_three_retried_attempts_close_all_three", F)  # fmt: skip
spec("M33", "the connection test comes before the timeout test", AN,
     "    if isinstance(exc, anthropic.APITimeoutError):\n        return ProviderErrorType.timeout\n"
     "    if isinstance(exc, anthropic.APIConnectionError):\n        return ProviderErrorType.connection\n",
     "    if isinstance(exc, anthropic.APIConnectionError):\n        return ProviderErrorType.connection\n"
     "    if isinstance(exc, anthropic.APITimeoutError):\n        return ProviderErrorType.timeout\n",
     "test_r1_stand_in_rows", W)  # fmt: skip
spec("M35", "the guard around the retry decision is removed", RT,
     "            try:\n                decision: object = bool(transient(exc, retryable))\n"
     "            except Exception:  # noqa: BLE001 - never-raise guard: a crashed retry decision is booked as billed, never raised raw\n"
     "                record(Site.retry_decision)\n                decision = DECISION_FAILED\n",
     "            decision: object = bool(transient(exc, retryable))\n",
     "test_r5_a_decision_that_crashed_is_the_billed_class", F)  # fmt: skip
spec("M37", "a wait failure is swallowed as wait 0 and the loop goes on", RT,
     "            except Exception:  # noqa: BLE001 - never-raise guard: a crashed wait is booked as billed, never raised raw\n"
     "                record(Site.retry_wait)\n"
     "                raise _billed(exc, label, attempt, facts) from None\n",
     "            except Exception:  # noqa: BLE001\n                record(Site.retry_wait)\n                wait = 0.0\n",
     "test_r10_a_wait_computation_that_raises_is_a_decision_failure", F)  # fmt: skip
spec("M38", "a kind adapter does not end in default_facts", BD,
     "neutral = default_facts(exc)", "neutral = ProviderFacts(None, None, None)",
     "test_r19_bare_exceptions_give_the_class_based_types", FA)  # fmt: skip
spec("M39", "the refusal is raised from the original error", RT,
     "                    retryable=True,\n                    retry_count=attempt,\n                ) from None",
     "                    retryable=True,\n                    retry_count=attempt,\n                ) from exc",
     "test_r17_the_traceback_never_prints_the_original_error_text", F)  # fmt: skip
spec("M40", "default_facts reads the text of the reason", RT,
     "    error_type = status_error_type(status_value)\n",
     "    error_type = status_error_type(status_value)\n    str(safe_attr(exc, \"reason\"))\n",
     "test_r4a_direct_adapter_reads_only_its_allow_list", FA)  # fmt: skip
spec("M41", "a decision failure raises a plain ProviderError", RT,
     "    return ProviderExhausted(\n        text,", "    return ProviderError(\n        text,",
     "test_r5_a_decision_that_crashed_is_the_billed_class", F)  # fmt: skip
spec("M42", "diagnose accepts any str as a request id", DG,
     "            if pattern.fullmatch(value) is not None:\n                return SafeToken(str.__str__(value), SafeToken._MINT)",
     "            if True:\n                return SafeToken(str.__str__(value), SafeToken._MINT)",
     "test_provider_attributes_are_read_with_exact_types", D)  # fmt: skip
spec("M43", "the status rule is applied to ProviderExhausted", DG,
     "if own_cls is tp and own_key == _PROVIDER_ERROR_KEY:", "if own_key in _PROVIDER_KEYS:",
     "test_provider_codes_follow_status_then_type", D)  # fmt: skip
spec("M44", "diagnose drops every provider fact when one fails", DG,
     "    if status is not None:\n        found[FactKey.http_status] = status\n",
     '    if status is None and "status" in attrs:\n        return {}\n    if status is not None:\n        found[FactKey.http_status] = status\n',
     "test_provider_attributes_are_read_with_exact_types", D)  # fmt: skip
spec("M45", "the error type decides the code although a valid status is present", DG,
     "    if type(status) is int:\n        if status in CODED_STATUSES:",
     "    if type(status) is int and found.get(FactKey.provider_error_type) is None:\n        if status in CODED_STATUSES:",
     "test_provider_codes_follow_status_then_type", D)  # fmt: skip
spec("M46", "a decision failure uses max_attempts instead of the current attempt", RT,
     "raise _billed(exc, label, attempt, facts) from None", "raise _billed(exc, label, max_attempts, facts) from None",
     "test_r5_attempt_two_hook_failure_is_billed_with_attempt_two", F)  # fmt: skip
spec("M47", "an unlisted Claude type falls through to the status table", AN,
     "error_type = _TYPE.get(word, ProviderErrorType.other)", "error_type = _TYPE.get(word) or status_error_type(status)",
     "test_r5_claude_body_cases", F)  # fmt: skip
spec("M48", "the bool() around the retry decision is removed", RT,
     "decision: object = bool(transient(exc, retryable))", "decision: object = transient(exc, retryable)",
     "test_r5_a_decision_that_crashed_is_the_billed_class", F)  # fmt: skip

# --- the one counter, the faults-only counter, the ledger (review 1 fixes; tests in test_never_raise_guards.py and neighbours) -----
CT = "tests/test_diagnostic_codes.py"
spec("M49", "the diagnostic guards stop recording into the shared counter", DG,
     "    record(_SITES[site])\n", "    pass\n",
     "test_every_diagnostic_guard_site_records_into_the_shared_counter", NR)  # fmt: skip
spec("M50", "with_retry counts every failed call again", RT,
     "            _close_failed_http(exc)\n", "            record(Site.retry_decision)\n            _close_failed_http(exc)\n",
     "test_an_ordinary_retried_failure_is_not_counted_and_a_genuine_fault_is", NR)  # fmt: skip
spec("M51", "the counter lock is not reentrant", NV,
     "_LOCK: Final = threading.RLock()", "_LOCK: Final = threading.Lock()",
     "test_record_can_be_entered_again_on_the_same_thread", NR)  # fmt: skip
spec("M52", "neverraise exposes reset() again", NV,
     "def counts() -> dict[str, int]:", "def reset() -> None:\n    with _LOCK:\n        _COUNTS.clear()\n\n\ndef counts() -> dict[str, int]:",
     "test_one_counter_not_two", NR)  # fmt: skip
spec("M53", "SqlReadError gives config_invalid again", CD,
     '_P + "store.migration_numbers:SqlReadError": Code.internal_bug,', '_P + "store.migration_numbers:SqlReadError": Code.config_invalid,',
     "test_a_sql_file_that_cannot_be_read_is_a_repository_defect_not_an_operator_config_error", CT)  # fmt: skip
spec("M54", "a failed wait computation lets the loop go on", RT,
     "                record(Site.retry_wait)\n                raise _billed(exc, label, attempt, facts) from None\n",
     "                record(Site.retry_wait)\n                wait = jitter\n",
     "test_a_failed_wait_computation_stops_the_loop_and_is_recorded", NR)  # fmt: skip
spec("M55", "a failed wait computation is not recorded", RT,
     "                record(Site.retry_wait)\n", "                pass\n",
     "test_a_failed_wait_computation_stops_the_loop_and_is_recorded", NR)  # fmt: skip
spec("M56", "the adapter-hook guard records under another guard's site", PF,
     "record(Site.facts_adapter_hook)", "record(Site.facts_safe_attr)",
     "test_ledger_lists_exactly_the_guards_in_the_code_by_file_function_and_site", NR)  # fmt: skip
spec("M57", "a Site member that no guard records", NV,
     '    retry_wait = "retry_wait"\n', '    retry_wait = "retry_wait"\n    retry_unused = "retry_unused"\n',
     "test_every_site_name_is_recorded_by_exactly_one_guard_and_none_is_dead", NR)  # fmt: skip


def check_search_strings() -> list[str]:
    """Every ``old`` must occur in its file (the runner replaces every occurrence); returns the problems."""
    bad = []
    for num, _name, file, old, new, *_ in SPECS:
        text = (ROOT / file).read_text(encoding="utf-8")
        if text.count(old) < 1 or old == new:
            bad.append(f"{num}: {text.count(old)} occurrences in {file}")
    return bad


def build() -> list[Mutant]:
    return [
        Mutant(
            f"{num} {name}",
            file,
            old,
            new,
            expect or "ssert",
            test_file=tf,
            only_test=killer,
            pinned=pinned,
        )
        for num, name, file, old, new, killer, tf, expect, pinned in SPECS
    ]


if __name__ == "__main__":
    problems = check_search_strings()
    if problems:
        print("search strings that do not apply:", problems, file=sys.stderr)
        sys.exit(2)
    only = sys.argv[1:]
    mutants = build()
    if only and not any(o in m.name for m in mutants for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)

    def show(row):
        name, v, test_id, good = row
        print(
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:70]}]",
            flush=True,
        )
        if not good:
            print("      first line:", first_lines.get(name, "")[:200], flush=True)

    first_lines: dict[str, str] = {}
    res = run_mutants(
        ROOT, mutants, TESTS, extra_dirs=("tests/fixtures", "tests/contracts", "tests/data"), only=only,
        on_result=show, first_lines=first_lines, timeout=300.0,
    )  # fmt: skip
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
