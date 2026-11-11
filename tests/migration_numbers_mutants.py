"""Mutants of `store/migration_numbers.py` (the lexer, the refusal list, the fix-1 and order-100 guards) and of the shared
timing rule `tests/fixtures/timing.py`. Not collected by pytest.

Each mutant reverts ONE guard in a temp copy; the test in `killer` must be the one that fails first, with a failing line
that holds `expect`. The first 17 are the lexer mutants of the ticket (M26 a-h, M74, M50, M51, M52, M72, M73, M96, M97,
M98; the "strings before comments" mutant of M26(i) cannot be written as a one-line revert and M86 is the timing
stand-in, which lives in the `perf` tests); the rest are the guards added in fix 1 and order 100. Run from the repo
root (CI-ready: needs only the ordinary test environment, no database, no network, about a minute (measured, see the changelog); exit 0 only when every
mutant is good, and the last line is `N of N good; problems: []`):

    uv run python tests/migration_numbers_mutants.py            # all; exit 1 if any is not good
    uv run python tests/migration_numbers_mutants.py hidden     # only names that hold the text

A cheap check that runs with the ordinary tests, `test_every_mutant_still_applies_to_the_source`, fails when a mutant's
`old` text is no longer in its file or its killer test no longer exists, so the list cannot rot between two runs.
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
T1 = "tests/test_migration_numbers.py"
T2 = "tests/test_migration_numbers_guards.py"
T3 = "tests/test_timing_fixture.py"
TIMING = "tests/fixtures/timing.py"
SRC = "src/hadavin_sdk/store/migration_numbers.py"


def mutant(name, old, new, test_file, killer, expect, src=SRC, **kw):
    pin = test_file[:-3] + "::" + killer
    return Mutant(
        name,
        src,
        old,
        new,
        expect,
        test_file=test_file,
        only_test=killer.split("[")[0],
        pinned=pin,
        **kw,
    )


M = [
    mutant(
        "lexer: no -- comment rule",
        'if text.startswith("--", j):',
        "if False:",
        T1,
        "test_apostrophe_in_a_comment_does_not_hide_a_statement",
        "assert False",
    ),
    mutant(
        "lexer: block comments are not nested",
        'if text.startswith("/*", k):\n                        depth, k = depth + 1, k + 2',
        "if False:\n                        depth, k = depth + 1, k + 2",
        T1,
        "test_apostrophe_in_a_comment_does_not_hide_a_statement",
        "a nested comment hides it",
    ),
    mutant(
        "lexer: no '' escape in a string",
        "if text.startswith(\"''\", s.start()):",
        "if False:",
        T1,
        "test_statement_text_exact_output",
        "SELECT",
    ),
    mutant(
        "lexer: no E backslash rule",
        'e_mode = j - run == 1 and text[run] in "Ee"',
        "e_mode = False",
        T1,
        "test_e_string_and_dollar_cases",
        "SELECT E",
    ),
    mutant(
        'lexer: no "" escape in a name',
        "if text.startswith('\"\"', s.start()):",
        "if False:",
        T1,
        "test_statement_text_exact_output",
        "SELECT",
    ),
    mutant(
        "lexer: no dollar-quote rule",
        '_SPECIAL = re.compile(r"[-/\'\\"$]")',
        '_SPECIAL = re.compile(r"[-/\'\\"]")',
        T1,
        "test_non_ascii_dollar_tag",
        "assert",
    ),
    mutant(
        "lexer: $1 opens a tag",
        "if k < n and text[k].isascii() and text[k].isdigit():",
        "if False:",
        T1,
        "test_parameters_are_left_alone",
        "SELECT",
    ),
    mutant(
        "lexer: an unclosed string is not refused",
        'fail("string not closed", j)',
        "pass",
        T2,
        "test_lex_returns_the_text_and_the_problem",
        "(\"SELECT '\", '')",
    ),
    mutant(
        "lexer: statement-start anchor removed",
        "if m := _TRANSACTION.match(s):",
        "if m := _TRANSACTION.search(s):",
        T1,
        "test_statement_start_anchor",
        "SELECT CASE",
    ),
    mutant(
        "lexer: tag characters are ASCII only",
        'return ch.isascii() and (ch.isalpha() or ch == "_") or not ch.isascii()',
        'return ch.isascii() and (ch.isalpha() or ch == "_")',
        T1,
        "test_non_ascii_dollar_tag",
        "assert",
    ),
    mutant(
        "lexer: a -- comment ends at LF only",
        'while k < n and text[k] not in "\\n\\r":',
        'while k < n and text[k] != "\\n":',
        T1,
        "test_comment_ends_at_cr",
        "COMMIT",
    ),
    mutant(
        "lexer: the blank set lacks CR, FF, VT",
        '_WS = " \\t\\n\\r\\f\\v"',
        '_WS = " \\t\\n"',
        T1,
        "test_comment_ends_at_cr",
        "COMMIT",
    ),
    mutant(
        "lexer: dollar tags compared without case",
        "end = text.find(tag, k + 1)",
        "end = text.lower().find(tag.lower(), k + 1)",
        T1,
        "test_e_string_and_dollar_cases",
        "SELECT",
    ),
    mutant(
        "lexer: a body ends at the first $",
        "end = text.find(tag, k + 1)",
        'end = text.find("$", k + 1)',
        T1,
        "test_e_string_and_dollar_cases",
        "SELECT",
    ),
    mutant(
        "lexer: a $ after a name opens a tag",
        "if run < j and _ident_start(text[run]):",
        "if False:",
        T1,
        "test_dollar_after_identifier_is_not_a_tag",
        "assert",
    ),
    mutant(
        "lexer: E after a name char is a prefix",
        'e_mode = j - run == 1 and text[run] in "Ee"',
        'e_mode = run < j and text[j - 1] in "Ee"',
        T1,
        "test_e_after_identifier_is_not_a_prefix",
        "assert",
    ),
    mutant(
        "lexer: CRLF counts as two lines",
        'return 1 + head.count("\\n") + head.count("\\r") - head.count("\\r\\n")',
        'return 1 + head.count("\\n") + head.count("\\r")',
        T1,
        "test_crlf_counts_as_one_line",
        "assert",
    ),
    # --- fix 1
    mutant(
        "fix1: only Cc is a hidden character",
        '_HIDDEN_CATEGORIES = frozenset({"Cc", "Cf", "Zl", "Zp"})',
        '_HIDDEN_CATEGORIES = frozenset({"Cc"})',
        T2,
        "test_hidden_characters_are_refused_in_a_file_and_in_a_late_file[U+202E]",
        "Error: []",
    ),
    mutant(
        "fix1: a byte order mark is not named",
        'if text.startswith("\\ufeff"):',
        "if False:",
        T2,
        "test_a_byte_order_mark_at_the_start_is_named",
        "hidden character U+FEFF",
    ),
    mutant(
        "fix1: a late file skips the refusal list",
        "    if reasons := refused_statements(text):\n        return reasons[0]\n",
        "",
        T2,
        "test_a_late_file_with_transaction_control_or_a_setting_gets_no_recipe[COMMIT;]",
        "Failed",
    ),
    mutant(
        "fix1: a $ after a $ in a name opens a tag",
        "if run == i and carried >= 0:",
        "if False:",
        T2,
        "test_a_dollar_right_after_a_dollar_inside_a_name",
        "assert",
    ),
    mutant(
        "fix1: a $ after a number is part of a name",
        "if run < j and _ident_start(text[run]):",
        "if run < j:",
        T2,
        "test_dollar_tag_right_after_a_number",
        "assert",
    ),
    mutant(
        "fix1: checked_statement_text returns a cut text",
        "        raise SqlReadError(problem)",
        "        pass",
        T2,
        "test_checked_statement_text_raises_instead_of_returning_a_cut_text",
        "Failed",
    ),
    mutant(
        "fix1: gone_message names are not capped",
        "shown = [_esc(n) for n in names[:MAX_PROBLEMS_SHOWN]]",
        "shown = [_esc(n) for n in names]",
        T2,
        "test_gone_message_caps_the_names_and_stays_fast",
        "names not capped",
    ),
    mutant(
        "fix1: GRANT without ON is not refused",
        "elif m := _ROLE_MEMBERSHIP.match(s):",
        "elif False:",
        T2,
        "test_more_blind_statements_are_refused[GRANT r TO s]",
        "('GRANT r TO s', [])",
    ),
    mutant(
        "fix1: COPY PROGRAM is not refused",
        "elif _COPY_PROGRAM.match(s):",
        "elif False:",
        T2,
        "test_more_blind_statements_are_refused[COPY t TO PROGRAM 'x']",
        "TO PROGRAM",
    ),
    mutant(
        "fix1: a changed released file is not found",
        'elif hashlib.sha256(p.read_bytes().replace(b"\\r\\n", b"\\n")).hexdigest() != manifest[stem]:',
        "elif False:",
        T2,
        "test_released_problems_catches_an_edit_a_deletion_and_a_low_new_number",
        "assert",
    ),
    mutant(
        "fix1: a missing text raises KeyError",
        "if missing := [p.name for p in late if p not in texts]:",
        "if False:",
        T2,
        "test_order_problems_with_a_missing_text_is_a_message_not_an_exception",
        "KeyError",
        allow_crash=True,
        crash_type="KeyError",
    ),
    # --- order 100
    mutant(
        "o100: statement_text returns the bare text, not the pair",
        "    return lex(text, keep_quoted)\n",
        "    return lex(text, keep_quoted)[0]\n",
        T2,
        "test_statement_text_called_the_ticket_way_returns_the_pair",
        "too many values to unpack",
        allow_crash=True,
        crash_type="ValueError",
    ),
    mutant(
        "o100: the error is not rebuilt from its problems on copy",
        "    def __reduce__(self):",
        "    def _not_reduce(self):",
        T2,
        "test_migration_number_error_survives_copy_deepcopy_and_pickle",
        "and 13 more",
    ),
    mutant(
        "o100: MIGRATE_LOCK differs from the key migrate uses",
        'MIGRATE_LOCK = int.from_bytes(b"hadvnmig", "big") >> 1',
        'MIGRATE_LOCK = int.from_bytes(b"hadvnmig", "big") >> 2',
        T2,
        "test_the_lock_key_and_the_folder_are_the_ones_migrate_uses",
        "BinOp(left=C",
    ),
    mutant(
        "o100: MIGRATIONS names another folder than migrate does",
        'MIGRATIONS = Path(__file__).parent / "migrations"',
        'MIGRATIONS = Path(__file__).parent / "migration"',
        T2,
        "test_the_lock_key_and_the_folder_are_the_ones_migrate_uses",
        "BinOp(left=A",
    ),
    mutant(
        "o100: NAME lets any character into a file name",
        'NAME = re.compile(r"[0-9]{4}_[a-z0-9_]+\\.sql")',
        'NAME = re.compile(r"[0-9]{4}_.+\\.sql")',
        T1,
        "test_a_hostile_name_never_reaches_the_order_message",
        "== []",
    ),
    mutant(
        "o100: the timing limit is not a ratio (everything passes)",
        "PER_SIZE, MIN_GROWTH = 3.0, 8",
        "PER_SIZE, MIN_GROWTH = 1000.0, 8",
        T3,
        "test_a_quadratic_cost_is_flagged_at_any_speed[1e-11-gap8]",
        "a quadratic cost was not flagged",
        src=TIMING,
    ),
    mutant(
        "o100: the timing limit is too tight (everything is flagged)",
        "PER_SIZE, MIN_GROWTH = 3.0, 8",
        "PER_SIZE, MIN_GROWTH = 0.001, 8",
        T3,
        "test_a_linear_cost_passes_at_any_speed[1e-09-gap8]",
        "a linear cost was flagged",
        src=TIMING,
    ),
    mutant(
        "timing: the limit is 1.2 times the size ratio, not 3",
        "PER_SIZE, MIN_GROWTH = 3.0, 8",
        "PER_SIZE, MIN_GROWTH = 1.2, 8",
        T3,
        "test_the_limit_is_three_times_the_size_ratio",
        "23.9x for 8x the size is within the limit",
        src=TIMING,
    ),
    mutant(
        "timing: the limit is 3.99 times the size ratio, not 3",
        "PER_SIZE, MIN_GROWTH = 3.0, 8",
        "PER_SIZE, MIN_GROWTH = 3.99, 8",
        T3,
        "test_the_limit_is_three_times_the_size_ratio",
        "24.1x for 8x the size is over the limit",
        src=TIMING,
    ),
    mutant(
        "timing: a fast small run is raised to a 4 ms floor again (a fast quadratic cost passes)",
        "return PER_SIZE * (big / small) * t_small",
        "return PER_SIZE * (big / small) * max(t_small, 0.004)",
        T3,
        "test_a_fast_small_run_is_not_raised_to_a_floor",
        "a 1 ms small run was raised to a floor",
        src=TIMING,
    ),
    mutant(
        "timing: a run of zero seconds is passed, not refused",
        "if not (math.isfinite(seconds) and seconds > 0):",
        "if False:",
        T3,
        "test_a_small_run_that_is_not_a_time_is_refused_not_passed[0.0]",
        "DID NOT RAISE",
        src=TIMING,
    ),
    mutant(
        "timing: the big run is not checked (not-a-number passes as linear)",
        '_check_time(t_big, "big")',
        "pass",
        T3,
        "test_a_big_run_that_is_not_a_time_is_refused_not_passed[0.0]",
        "DID NOT RAISE",
        src=TIMING,
    ),
    mutant(
        "timing: sizes that are not 0 < small < big are not refused",
        "if not 0 < small < big:",
        "if False:",
        T3,
        "test_sizes_that_cannot_show_a_quadratic_cost_are_refused_before_any_work[negative]",
        "DID NOT RAISE",
        src=TIMING,
    ),
    mutant(
        "timing: a size gap under 8 is not refused",
        "if big < MIN_GROWTH * small:",
        "if False:",
        T3,
        "test_a_gap_of_exactly_eight_is_the_smallest_allowed",
        "DID NOT RAISE",
        src=TIMING,
    ),
    mutant(
        "timing: the smallest size gap allowed is 4, not 8",
        "PER_SIZE, MIN_GROWTH = 3.0, 8",
        "PER_SIZE, MIN_GROWTH = 3.0, 4",
        T3,
        "test_a_gap_of_exactly_eight_is_the_smallest_allowed",
        "DID NOT RAISE",
        src=TIMING,
    ),
    mutant(
        "timing: the sizes and the unit are checked after the work has run",
        '    check_sizes(small, big)\n    if not unit:\n        raise Untimeable("the unit to repeat is empty")\n    texts = [(unit * (n // len(unit) + 1))[:n] for n in (small, big)]\n    t_small, t_big = seconds_per_call_each(fn, texts, clock)\n    return Growth(t_small, t_big, small, big)\n',
        '    texts = [((unit or "a") * (n // len(unit or "a") + 1))[:n] for n in (small, big)]\n    t_small, t_big = seconds_per_call_each(fn, texts, clock)\n    check_sizes(small, big)\n    if not unit:\n        raise Untimeable("the unit to repeat is empty")\n    return Growth(t_small, t_big, small, big)\n',
        T3,
        "test_an_empty_unit_is_refused_before_any_work",
        "the work was run before the unit was checked",
        src=TIMING,
    ),
    mutant(
        "timing: the middle batch counts, not the fastest (median)",
        "best = [min(r) for r in runs]",
        "best = [sorted(r)[len(r) // 2] for r in runs]",
        T3,
        "test_a_pause_in_four_of_five_batches_changes_nothing[0.007]",
        "a pause was counted as the work's own time",
        src=TIMING,
    ),
    mutant(
        "timing: the slowest batch counts, not the fastest",
        "best = [min(r) for r in runs]",
        "best = [max(r) for r in runs]",
        T3,
        "test_a_pause_in_four_of_five_batches_changes_nothing[0.007]",
        "a pause was counted as the work's own time",
        src=TIMING,
    ),
    mutant(
        "timing: one repeat, not five",
        "MIN_BATCH_S, REPEATS, MAX_CALLS = 0.02, 5, 10_000_000",
        "MIN_BATCH_S, REPEATS, MAX_CALLS = 0.02, 1, 10_000_000",
        T3,
        "test_a_slow_call_is_run_once_to_size_the_batch_and_once_in_each_of_five_repeats",
        "one sizing call and five repeats",
        src=TIMING,
    ),
    mutant(
        "timing: the batch length is a tenth",
        "MIN_BATCH_S, REPEATS, MAX_CALLS = 0.02, 5, 10_000_000",
        "MIN_BATCH_S, REPEATS, MAX_CALLS = 0.002, 5, 10_000_000",
        T3,
        "test_a_fast_call_is_batched_to_the_batch_length_and_repeated_five_times",
        "a batch that counts is shorter than the batch length",
        src=TIMING,
    ),
    mutant(
        "timing: a batch sized during a pause is not sized again",
        "short = [i for i, seconds in enumerate(best) if not seconds >= MIN_BATCH_S]",
        "short = [i for i, seconds in enumerate(best) if seconds < 0]",
        T3,
        "test_a_pause_while_the_batch_is_sized_cannot_shorten_the_batches_that_count",
        "a pause while the batch was sized left the batches too short",
        src=TIMING,
    ),
    mutant(
        "timing: all the small batches run before the big ones (the sizes do not take turns)",
        "        for _ in range(REPEATS):\n            for i, batch in enumerate(batches):\n                runs[i].append(batch(calls[i]))",
        "        for i, batch in enumerate(batches):\n            for _ in range(REPEATS):\n                runs[i].append(batch(calls[i]))",
        T3,
        "test_the_two_sizes_take_turns",
        "the repeats must alternate small, big",
        src=TIMING,
    ),
    mutant(
        "timing: a hand loop with the garbage collector on, not timeit",
        "timed = timeit.Timer(functools.partial(fn, text), timer=clock).timeit",
        "timed = lambda n: (lambda t0: [fn(text) for _ in range(n)] and clock() - t0)(clock())",
        T3,
        "test_the_collector_is_off_while_the_clock_runs_and_back_on_after",
        "the collector must be off while the clock runs",
        src=TIMING,
    ),
    mutant(
        "timing: a case that cannot be timed stops the sweep",
        "except Untimeable as refused:",
        "except KeyError as refused:",
        T3,
        "test_a_sweep_names_each_slow_case_and_each_case_it_could_not_time",
        "too fast to time",
        src=TIMING,
        allow_crash=True,  # the refusal itself leaves the sweep: the first line is that ValueError, not an assertion
        crash_type="Untimeable",
    ),
    mutant(
        "timing: the wall clock everywhere (a busy machine moves the result)",
        'return time.perf_counter if platform == "win32" else time.process_time',
        "return time.perf_counter",
        T3,
        "test_the_clock_is_processor_time_off_windows[linux]",
        "off Windows the rule must time processor time",
        src=TIMING,
    ),
    mutant(
        "timing: Windows is not told from the platform name (the wall clock is not used there)",
        'return time.perf_counter if platform == "win32" else time.process_time',
        'return time.perf_counter if platform == "windows" else time.process_time',
        T3,
        "test_the_clock_is_the_wall_clock_on_windows",
        "on Windows the rule must use the wall clock",
        src=TIMING,
    ),
    mutant(
        "timing: a call without a clock uses the wall clock, not the rule's clock",
        "batches = [_batch_timer(fn, text, clock or CLOCK, wall) for text in texts]",
        "batches = [_batch_timer(fn, text, clock or time.perf_counter, wall) for text in texts]",
        T3,
        "test_the_rules_clock_is_the_one_picked_for_this_platform",
        "a call without a clock must use the rule's clock",
        src=TIMING,
    ),
    mutant(
        "timing: exactly the limit is flagged (more than, not at least)",
        "return t_big > time_limit(t_small, small, big)",
        "return t_big >= time_limit(t_small, small, big)",
        T3,
        "test_exactly_the_limit_passes_and_a_hair_over_is_flagged",
        "exactly the limit must pass",
        src=TIMING,
    ),
    mutant(
        "timing: a call too fast to time is not refused at the cap",
        "    if calls >= MAX_CALLS:\n",
        "    if False:\n",
        T3,
        "test_a_call_too_fast_to_time_is_refused_not_passed",
        "did not match",
        src=TIMING,
    ),
    mutant(
        "timing: work that waits is timed from its processor time (no wall-clock check)",
        "wall = time.perf_counter if clock is None else None",
        "wall = None",
        T3,
        "test_work_that_sleeps_is_refused_not_timed_from_a_few_microseconds_of_processor_time",
        "did not match",
        src=TIMING,
    ),
    mutant(
        "timing: the waiting check also runs with a made-up clock",
        "wall = time.perf_counter if clock is None else None",
        "wall = time.perf_counter",
        T3,
        "test_the_waiting_check_is_for_the_real_clock_only",
        "did not match",
        src=TIMING,
    ),
    mutant(
        "timing: a case that raises is not named",
        '            error.add_note(\n                f"in the sweep case {name!r} on {unit!r}; problems found before it: {found}"\n            )\n',
        "            pass\n",
        T3,
        "test_a_case_that_raises_keeps_its_type_and_is_named_with_the_problems_found_before_it",
        "does not name the case",
        src=TIMING,
    ),
    mutant(
        "timing: a clock difference of almost nothing overflows (infinity is not capped)",
        "wanted = math.ceil(min(calls * 1.2 * MIN_BATCH_S / took, MAX_CALLS)) if took > 0 else calls * 10",
        "wanted = math.ceil(calls * 1.2 * MIN_BATCH_S / took) if took > 0 else calls * 10",
        T3,
        "test_a_clock_difference_of_almost_nothing_is_refused_not_an_overflow[5e-324]",
        "OverflowError",
        src=TIMING,
        allow_crash=True,
        crash_type="OverflowError",
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
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:70]}]",
            flush=True,
        )
        if not good:
            print("      first line:", first_lines.get(name, "")[:200], flush=True)

    res = run_mutants(
        ROOT,
        M,
        [T1, T2, T3],
        extra_dirs=("tests/fixtures",),
        only=only,
        on_result=show,
        first_lines=first_lines,
        timeout=300,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
