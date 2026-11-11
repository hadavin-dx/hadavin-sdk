"""The mutants of the diagnostics (``guard/diagnostic.py`` and ``codes.py``), run through the P1m runner (``tools.mutation_runner``).

Each mutant changes ONE thing in a temp copy of the package. The test named in ``only_test`` must fail, it must be the test pinned in
``pinned``, and the first failing line must hold ``expect`` (a fragment of the assertion message, not of the test name). Search strings are
exact copies of the formatted source. Not collected by pytest. Run from the repo root:

    uv run python tests/diagnostic_mutants.py            # all mutants; exit 1 if any is not good
    uv run python tests/diagnostic_mutants.py frame      # only mutants whose name contains the text

Equivalent, stated and not run: removing ``type(frame.f_code.co_filename) is str`` from frame rule (c): no frame with a non-``str``
``co_filename`` can be built (``code.replace`` raises ``TypeError``), so the check stays as cheap defence.
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
D = "src/hadavin_sdk/guard/diagnostic.py"
C = "src/hadavin_sdk/codes.py"
TD, TC, TV = (
    "tests/test_diagnostic.py",
    "tests/test_diagnostic_codes.py",
    "tests/test_diagnostic_validation.py",
)
TH = "tests/test_diagnostics_hostile.py"
ORACLE = "tests/data/c18a_oracle.py"
CORPUS = "tests/data/c18a_hostile_corpus.py"
TESTS = [TD, TC, TV, TH]


def mutant(name, file, old, new, test_file, killer, expect, **kw):
    pin = test_file.removesuffix(".py") + "::" + killer
    return Mutant(
        name, file, old, new, expect, test_file=test_file, only_test=killer, pinned=pin, **kw
    )


M = [
    # codes and table
    mutant(
        "code set: a member is removed",
        C,
        '    tool_refused = "tool_refused"\n',
        '    tool_refused = "tool_refusedx"\n',
        TC,
        "test_code_set_is_the_frozen_list",
        "assert [",
    ),
    mutant(
        "table: NotFound row removed",
        C,
        '        _P + "store.protocol:NotFound": Code.store_conflict,\n',
        "",
        TC,
        "test_pinned_code_per_class",
        "differs from the pinned rows",
    ),
    mutant(
        "table: VaultError set back to config_invalid",
        C,
        '"actions.secrets_vault:VaultError": Code.provider_http',
        '"actions.secrets_vault:VaultError": Code.config_invalid',
        TC,
        "test_pinned_code_per_class",
        "differs from the pinned rows",
    ),
    mutant(
        "table: TextnormError row removed",
        C,
        '        _P + "guard.textnorm:TextnormError": Code.scan_failed,\n',
        "",
        TC,
        "test_textnorm_error_family_maps_to_scan_failed",
        "scan_failed",
    ),
    mutant(
        "identity check removed from the own-class lookup",
        D,
        "            if code is not None and _is_the_named_class(cls, (mod, qual)):",
        "            if code is not None:",
        TC,
        "test_spoofed_class_gets_no_own_code",
        "foreign_exception",
    ),
    mutant(
        "step token: a Where name as text is accepted",
        C,
        "        if type(value) is Where:",
        "        if type(value) is Where or value in Where._value2member_map_:",
        TC,
        "test_step_token_is_closed_and_final",
        "assert",
    ),
    # families and facts
    mutant(
        "timeout is not tested before os error",
        D,
        "    if issubclass(tp, TimeoutError):",
        "    if False:",
        TD,
        "test_family_order_timeout_before_os_error",
        "code=timeout",
    ),
    mutant(
        "gaierror handled as a plain os error",
        D,
        "    if issubclass(tp, socket.gaierror):",
        "    if False:",
        TD,
        "test_gaierror_gives_gai_not_errno",
        "gaierror facts",
    ),
    mutant(
        "a bool is accepted as a number",
        D,
        "    return value if type(value) is int and lo <= value <= hi else None",
        "    return value if isinstance(value, int) and lo <= value <= hi else None",
        TD,
        "test_facts_bounds_table",
        "assert",
    ),
    mutant(
        "the upper bound is off by one",
        D,
        "    return value if type(value) is int and lo <= value <= hi else None",
        "    return value if type(value) is int and lo <= value < hi else None",
        TD,
        "test_facts_bounds_table",
        "kept http_status=599",
    ),
    mutant(
        "sqlstate uses match instead of fullmatch",
        D,
        "_SQLSTATE_RE.fullmatch(value) is None",
        "_SQLSTATE_RE.match(value) is None",
        TD,
        "test_fact_patterns_use_fullmatch",
        "assert",
    ),
    mutant(
        "phase: 08 and 28 swapped",
        D,
        '{"28": Phase.auth, "08": Phase.connect}',
        '{"28": Phase.connect, "08": Phase.auth}',
        TD,
        "test_psycopg_phase_is_sqlstate_class_only",
        "sqlstate=",
    ),
    mutant(
        "psycopg also detected by module name",
        D,
        "    if type(base) is type and issubclass(tp, base):",
        '    if type(base) is type and (issubclass(tp, base) or tp.__module__.startswith("psycopg")):',
        TD,
        "test_psycopg_claimed_module_name_is_not_trusted",
        "assert",
    ),
    mutant(
        "facts merged from the more than 12 limit removed",
        D,
        "    return tuple(ordered[: defaults.DIAG_MAX_FACTS])",
        "    return tuple(ordered)",
        TD,
        "test_more_than_12_facts_keeps_priority_12",
        "assert 13 == 12",
    ),
    # rules 3 and 4
    mutant(
        "group: nested groups are walked",
        D,
        "        if nested:\n            return Code.foreign_exception, {}",
        "        if False:\n            return Code.foreign_exception, {}",
        TD,
        "test_exception_group_takes_first_member_code",
        "code=",
    ),
    mutant(
        "internal_bug is decided on any counted frame, not the raise frame",
        D,
        "    name = _counted_module(links[-1][0])",
        "    name = next((n for n in (_counted_module(f) for f, _ in reversed(links)) if n), None)",
        TD,
        "test_internal_bug_is_decided_on_the_raise_frame",
        "os.environ from own code",
    ),
    mutant(
        "built-in identity check removed",
        D,
        "    return type(tname) is str and getattr(builtins, tname, None) is tp",
        "    return type(tname) is str and hasattr(builtins, tname)",
        TD,
        "test_internal_bug_is_decided_on_the_raise_frame",
        "look-alike class",
    ),
    mutant(
        "the traceback step bound is removed",
        D,
        "        if steps > defaults.DIAG_TB_STEPS:",
        "        if False:",
        TD,
        "test_long_traceback_is_foreign",
        "long traceback",
    ),
    mutant(
        "diagnose catches BaseException",
        D,
        "    except Exception:  # noqa: BLE001 - a hostile exception object may raise any Exception: the fixed fallback",
        "    except BaseException:  # noqa: BLE001",
        TD,
        "test_baseexception_from_hostile_getattr_propagates",
        "DID NOT RAISE",
    ),
    mutant(
        "the fallback fp is changed",
        D,
        'FALLBACK_FP: Final = _fingerprint("unknown", Code.foreign_exception.value, "-", "-")',
        'FALLBACK_FP: Final = _fingerprint("unknown", Code.foreign_exception.value, "-", "x")',
        TD,
        "test_fallback_fp_is_pinned",
        "assert",
    ),
    # kind and frames
    mutant(
        "kind identity check removed",
        D,
        '        if not _is_the_named_class(tp, (mod, qual)):\n            return "dynamic_class"',
        '        if False:\n            return "dynamic_class"',
        TD,
        "test_kind_identity_rule",
        "assert",
    ),
    mutant(
        "the foreign package list is not checked",
        D,
        '        if mod.split(".")[0] in FOREIGN_PACKAGES_OK and _KIND_RE.fullmatch(text):',
        "        if _KIND_RE.fullmatch(text):",
        TD,
        "test_off_list_foreign_class_prints_foreign_class",
        "assert",
    ),
    mutant(
        "the fp ignores the relative path",
        D,
        '    text = f"{kind}|{code}|{function}|{relpath}"',
        '    text = f"{kind}|{code}|{function}"',
        TD,
        "test_locator_and_fp",
        "fp=ed342ffb",
    ),
    mutant(
        "frame rule a removed",
        D,
        "        if type(name) is not str:  # rule a",
        "        if False:  # rule a",
        TD,
        "test_frame_rule_a_name_must_be_exactly_str",
        "frame rule",
    ),
    mutant(
        "frame rule b removed",
        D,
        "        if module is None or g is not vars(module):  # rule b",
        "        if module is None:  # rule b",
        TD,
        "test_frame_rule_b_globals_must_be_the_module_namespace",
        "frame rule",
    ),
    mutant(
        "frame rule c removed",
        D,
        "        if type(filename) is not str or filename != module.__file__:  # rule c, raw strings",
        "        if type(filename) is not str:  # rule c, raw strings",
        TD,
        "test_frame_rule_c_filename_must_be_the_module_file",
        "frame rule",
    ),
    mutant(
        "the per-frame try/except is removed",
        D,
        "    except Exception:  # noqa: BLE001 - a hostile frame object may raise any Exception: not counted\n"
        '        _guard_failed("counted_module")\n'
        "        return None",
        "    except ZeroDivisionError:\n        return None",
        TD,
        "test_frame_check_that_raises_means_not_counted",
        "frame rule: unknown",
    ),
    # rendering and validation
    mutant(
        "the line cap is off by one",
        D,
        "            if len(line) + 1 + len(part) > defaults.DIAG_LINE_CHARS:",
        "            if len(line) + 1 + len(part) > defaults.DIAG_LINE_CHARS + 1:",
        TD,
        "test_grammar_a_shape_and_cap_boundary",
        "cap boundary",
    ),
    mutant(
        "the line cap is removed",
        D,
        "            if len(line) + 1 + len(part) > defaults.DIAG_LINE_CHARS:",
        "            if False:",
        TD,
        "test_grammar_a_shape_and_cap_boundary",
        "cap boundary",
    ),
    mutant(
        "pydantic input is requested",
        D,
        "include_url=False, include_context=False, include_input=False)  # type: ignore[attr-defined]\n    types",
        "include_url=False, include_context=False, include_input=True)  # type: ignore[attr-defined]\n    types",
        TV,
        "test_pydantic_error_reads_are_closed_ast",
        "assert",
    ),
    mutant(
        "more than 5 types are printed",
        D,
        "    for entry in found[: defaults.DIAG_MAX_ERRORS]:",
        "    for entry in found:",
        TV,
        "test_more_than_5_errors_gives_plus_n_more",
        "types printed",
    ),
    mutant(
        "the +N more tail is wrong",
        D,
        'text += f"; +{count - defaults.DIAG_MAX_ERRORS} more"',
        'text += f"; +{count} more"',
        TV,
        "test_more_than_5_errors_gives_plus_n_more",
        "tail:",
    ),
    mutant(
        "a type outside the closed list is printed",
        D,
        "    return value if value in VALIDATION_TYPES else VALIDATION_OTHER",
        "    return value",
        TV,
        "test_a_type_outside_the_closed_list_prints_other",
        "outside the closed list",
    ),
    # fix batch w3: reserved codes, step names, table lookup, tokens, order of facts, the reverse check and the teeth test
    mutant(
        "a reserved code is removed from RESERVED_FOR",
        C,
        '        "provider_timeout": "P5b1",\n',
        "",
        TC,
        "test_every_code_member_is_reachable_or_reserved",
        "provider_timeout",
    ),
    mutant(
        "TICK_STEPS gains a name",
        C,
        '{"sweep", "reconcile", "stuck", "checkpoint", "purge_evidence", "reprobe_sources"}',
        '{"sweep", "reconcile", "stuck", "checkpoint", "purge_evidence", "reprobe_sources", "zzz_step"}',
        TC,
        "test_tick_steps_match_tick_module",
        "TICK_STEPS differ",
    ),
    mutant(
        "the own code is read from a class attribute named code",
        D,
        "def _own_code(tp: type) -> Code | None:\n    for cls in tp.__mro__:",
        "def _own_code(tp: type) -> Code | None:\n    _c = getattr(tp, 'code', None)\n    if isinstance(_c, str) and _c in Code._value2member_map_:\n        return Code(_c)\n    for cls in tp.__mro__:",
        TC,
        "test_instance_and_class_attribute_named_code_is_ignored",
        "foreign_exception",
    ),
    mutant(
        "SafeToken.of stores the caller's object",
        D,
        "                return SafeToken(member, SafeToken._MINT)",
        "                return SafeToken(value, SafeToken._MINT)",
        TD,
        "test_safe_token_holds_the_member_of_the_allowed_set_not_the_callers_object",
        "the caller's object",
    ),
    mutant(
        "the fp ignores the function name",
        D,
        '    text = f"{kind}|{code}|{function}|{relpath}"',
        '    text = f"{kind}|{code}|{relpath}"',
        TD,
        "test_locator_and_fp",
        "fp=ed342ffb",
    ),
    mutant(
        "two adjacent fact names are swapped in FACT_PRIORITY",
        C,
        "    FactKey.http_status,\n    FactKey.sqlstate,\n    FactKey.phase,",
        "    FactKey.sqlstate,\n    FactKey.http_status,\n    FactKey.phase,",
        TC,
        "test_fact_priority_order_is_the_d9_literal",
        "differs from the D9 literal order",
    ),
    mutant(
        "the oracle sees only whole keys (half blind)",
        ORACLE,
        "            if any(w in k for w in wanted for k in keys):",
        "            if any(w == k for w in wanted for k in keys):",
        TH,
        "test_reverse_check_fails_90_percent",
        "AssertionError: (0, 124",
    ),
    Mutant(
        "a validation row names a canary that is not in its document",
        CORPUS,
        'val("pydantic_input", "lit", json.dumps({"pick": EMAIL}), E_, "literal_error quoting the input")',
        'val("pydantic_input", "lit", json.dumps({"pick": EMAIL}), (IBAN,), "literal_error quoting the input")',
        "none of",
        test_file=TH,
        only_test="test_every_active_row_has_teeth",
        pinned=TH.removesuffix(".py")
        + "::test_every_active_row_has_teeth[HC-pydantic_input-03]",  # the one row that is changed
    ),
    mutant(
        "every exception row is exempt from the teeth test (the cap of 15 is exceeded)",
        CORPUS,
        'expect: str = "no_canary", code: Code | None = None, step: str = "extract", golden: str | None = None,',
        'expect: str = "grammar", code: Code | None = None, step: str = "extract", golden: str | None = None,',
        TH,
        "test_exempt_rows_are_chosen_by_the_field_and_capped",
        "rows are exempt from the teeth test, the cap is 15",
    ),
    mutant(
        "phase: a member is renamed",
        C,
        '    connect = "connect"\n',
        '    connect = "connectx"\n',
        TC,
        "test_phase_is_the_frozen_list",
        "assert [",
    ),
    mutant(
        "validation types: a name is changed",
        C,
        '        "literal_error",\n',
        '        "literal_errorx",\n',
        TC,
        "test_validation_types_are_the_frozen_list",
        "assert",
    ),
    mutant(
        "table: a row key names a class that does not exist",
        C,
        '        _P + "config:_RenamedStage": Code.config_invalid,\n',
        '        _P + "config:_RenamedStageX": Code.config_invalid,\n',
        TC,
        "test_every_row_key_is_found_by_the_scan",
        "rows whose class the scan does not find",
    ),
    mutant(
        "table: NotFound gives another code",
        C,
        '        _P + "store.protocol:NotFound": Code.store_conflict,\n',
        '        _P + "store.protocol:NotFound": Code.config_invalid,\n',
        TC,
        "test_builtin_ancestry_never_beats_the_row",
        "code=store_conflict",
    ),
    mutant(
        "table: VaultError gives another code",
        C,
        '        _P + "actions.secrets_vault:VaultError": Code.provider_http,\n',
        '        _P + "actions.secrets_vault:VaultError": Code.config_invalid,\n',
        TD,
        "test_t7_a_vault_server_answer_is_a_vault_error_with_code_provider_http",
        "provider_http",
    ),
    mutant(
        "class name: the module name is read twice",
        D,
        "        if not _is_the_named_class(tp, (mod, qual)):",
        "        if not _is_the_named_class(tp):",
        TD,
        "test_class_name_reads_the_module_name_once",
        "was read",
    ),
    mutant(
        "group: the member's facts are read",
        D,
        "first_member, type(first_member), read_facts=False, nested=True",
        "first_member, type(first_member), read_facts=True, nested=True",
        TD,
        "test_a_group_gives_the_code_of_its_first_member_and_no_member_facts",
        "errno",
    ),
    mutant(
        "links: every frame is kept",
        D,
        "deque(maxlen=defaults.DIAG_MAX_FRAMES)",
        "deque(maxlen=None)",
        TD,
        "test_links_keep_the_innermost_frames_only_up_to_the_step_cap",
        "assert",
    ),
    mutant(
        "links: the step cap is one too high",
        D,
        "        if steps > defaults.DIAG_TB_STEPS:",
        "        if steps > defaults.DIAG_TB_STEPS + 1:",
        TD,
        "test_links_flag_a_traceback_over_the_step_cap_and_keep_nothing",
        "assert",
    ),
    mutant(
        "links: the traceback is walked again by the classifier",
        D,
        "code, derived = _classify(exc, tp, read_facts=True, walked=walked)",
        "code, derived = _classify(exc, tp, read_facts=True, walked=None)",
        TV,
        "test_t6_five_thousand_links_of_a_cause_chain_read_zero_hostile_names",
        "reads: the chain was walked",
    ),
    mutant(
        "pydantic: error_count is called outside the one helper",
        D,
        "        count, types = _error_types(exc)\n",
        "        count, types = _error_types(exc)\n        exc.error_count()\n",
        TV,
        "test_error_count_is_called_only_in_the_one_helper_and_no_input_is_read_by_name",
        "outside _error_types",
    ),
]

if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in m.name for m in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)
    first_lines = {}

    def show(row):
        name, v, test_id, good = row
        print(
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:60]}]",
            flush=True,
        )
        if not good:
            print("      first line:", first_lines.get(name, "")[:150], flush=True)

    res = run_mutants(
        ROOT,
        M,
        TESTS,
        extra_dirs=("tests/data", "tests/fixtures"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
