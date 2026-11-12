"""The mutants of the mode banner and the demo-only folder guard, run by the mutation runner (``tools/mutation_runner.py``).

Each mutant reverts ONE guard in a temp copy; the test in ``killer`` must fail first, and its first failing line must hold
``expect`` (a fragment of the assertion MESSAGE). A separate list (not in ``tests/mutation_runner_mutants.py`` and not in
``tests/stage_mutants.py``: their meta-tests pin those lists by count). Not collected by pytest. Run from the repo root:

    python tests/banner_mutants.py            # all mutants; exit 1 if any is not good
    python tests/banner_mutants.py G3         # only mutants whose name contains the text
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
T_MB = "tests/test_mode_banner.py"
T_G = "tests/test_demo_only_guard.py"
MB = "src/hadavin_sdk/mode_banner.py"
JS = "templates/mode-banner/mode_banner.js"
GD = "tools/demo_only_guard.py"


def mutant(name, file, old, new, test_file, killer, expect, crash=""):
    return Mutant(
        name,
        file,
        old,
        new,
        expect,
        allow_crash=bool(crash),
        crash_type=crash,
        test_file=test_file,
        only_test=killer,
        pinned=test_file.removesuffix(".py") + "::" + killer,
    )


def mb(name, old, new, killer, expect, crash=""):
    return mutant(name, MB, old, new, T_MB, killer, expect, crash)


def js(name, old, new, killer, expect):
    return mutant(name, JS, old, new, T_MB, killer, expect)


def gd(name, old, new, killer, expect):
    return mutant(name, GD, old, new, T_G, killer, expect)


M = [
    mb(
        "B1 an unknown stage is accepted",
        "if mode not in STAGES:",
        "if False:",
        "test_an_unknown_stage_is_refused",
        "KeyError",
        crash="KeyError",
    ),
    mb(
        "B2 a bare string is read letter by letter",
        "isinstance(keys, (str, bytes)) or ",
        "",
        "test_a_bare_string_or_non_list_is_refused_not_read_letter_by_letter",
        "DID NOT RAISE",
    ),
    mb(
        "B3 a name is checked by its start only",
        "_NAME_OK.fullmatch(shown)",
        "_NAME_OK.match(shown)",
        "test_a_name_that_could_change_the_sentence_is_refused",
        "DID NOT RAISE",
    ),
    mb(
        "B4 a real service is also listed as a stand-in",
        "if n not in real)",
        "if True)",
        "test_a_service_that_is_both_real_and_listed_as_stand_in_counts_as_real",
        "assert",
    ),
    mb(
        "B5 made-up data is claimed in the demo stage next to a real service",
        "    if real:\n",
        "    if real and mode != STAGES[0]:\n",
        "test_a_real_service_is_named_and_made_up_data_is_never_claimed",
        "assert",
    ),
    mb(
        "B6 the loud stand-ins line is replaced by the quiet one",
        "if pretend else words.standins_none",
        "if False else words.standins_none",
        "test_demo_with_only_stand_ins_says_made_up_and_lists_the_stand_ins_loudly",
        "assert",
    ),
    mb(
        "B7 a pilot or live screen says made-up",
        'return ModeBanner(mode, "quiet", tag, words.none_real,',
        'return ModeBanner(mode, "quiet", tag, words.made_up,',
        "test_pilot_or_live_with_nothing_real_is_quiet_and_not_made_up",
        "assert",
    ),
    mb(
        "B8 the order of the names is lost",
        "return tuple(out)",
        "return tuple(sorted(out))",
        "test_names_come_from_the_caller_and_repeats_are_shown_once_in_order",
        "assert",
    ),
    mb(
        "B9 the names from the caller are ignored",
        "shown = names.get(key, key)",
        "shown = key",
        "test_names_come_from_the_caller_and_repeats_are_shown_once_in_order",
        "assert",
    ),
    mb(
        "B10 the stand-ins are the kinds that are NOT demo-only",
        "if (c, s.kind) in DEMO_ONLY)",
        "if (c, s.kind) not in DEMO_ONLY)",
        "test_stand_ins_in_lists_the_components_whose_kind_is_demo_only",
        "assert",
    ),
    mb(
        "B11 the Python fallback differs from the page fallback",
        '"tone": "unconfirmed",\n        "tag": words.not_confirmed_tag',
        '"tone": "real",\n        "tag": words.not_confirmed_tag',
        "test_the_page_fallback_has_the_same_words_as_the_python_fallback",
        "assert",
    ),
    js(
        "J1 a banner with an unknown tone is painted",
        "if (TONES.indexOf(b.tone) < 0 || ",
        "if (",
        "test_a_missing_or_odd_banner_is_never_hidden_it_says_not_confirmed",
        "assert",
    ),
    js(
        "J2 a quiet banner is hidden",
        "el.hidden = false;",
        "el.hidden = b.tone === 'quiet';",
        "test_the_page_paints_exactly_what_python_wrote",
        "assert",
    ),
    js(
        "J3 the text is put in as HTML",
        "n.textContent = text;",
        "n.innerHTML = text;",
        "test_the_page_script_has_no_way_to_parse_html_or_load_anything",
        "innerHTML",
    ),
    js(
        "J4 the stand-ins line is not painted",
        "if (isText(b.standins)) el.appendChild",
        "if (false) el.appendChild",
        "test_the_page_paints_exactly_what_python_wrote",
        "assert",
    ),
    js(
        "J5 a very long text is painted",
        "v.length <= 600",
        "v.length <= 6000",
        "test_a_missing_or_odd_banner_is_never_hidden_it_says_not_confirmed",
        "assert",
    ),
    gd(
        "G1 a product file that names the folder is not a hit",
        "if cfg.folder in line:",
        "if False:",
        "test_product_code_that_names_the_folder_is_a_hit_with_file_and_line_only",
        "assert",
    ),
    gd(
        "G2 a fake record id is not a hit",
        "if any(p.search(line) for p in cfg.fake_id_patterns):",
        "if False:",
        "test_a_fake_record_id_in_product_code_is_a_hit_and_the_id_is_not_printed",
        "assert",
    ),
    gd(
        "G3 the loader files are not exempt",
        "if rel in loaders:\n                continue",
        "if False:\n                continue",
        "test_a_loader_may_name_the_folder_and_nothing_else_may",
        "assert",
    ),
    gd(
        "G4 a loader that does not name the folder is not stale",
        "elif cfg.folder not in f.read_text",
        "elif False and cfg.folder not in f.read_text",
        "test_a_stale_loader_entry_is_a_hit",
        "assert",
    ),
    gd(
        "G5 the folder inside a product root is not a hit",
        "any((repo / r / cfg.folder).exists() for r in cfg.product_roots)",
        "False",
        "test_the_folder_inside_a_product_root_is_a_hit",
        "assert",
    ),
    gd(
        "G6 a missing product root is not a hit",
        "if not (repo / root).is_dir():",
        "if False:",
        "test_a_missing_product_root_is_a_hit_not_a_silent_pass",
        "assert",
    ),
    gd(
        "G7 a required folder that is missing does not stop the run",
        "        return 2\n",
        "        return 0\n",
        "test_exit_codes_clean_dirty_and_required_folder_missing",
        "assert",
    ),
    gd(
        "G8 the copy keeps the folder",
        "skip.add(cfg.folder)",
        "pass",
        "test_the_copy_has_no_folder_and_nothing_else_is_lost",
        "assert",
    ),
    gd(
        "G9 caches are scanned",
        "if any(part in SKIP_DIRS for part in p.relative_to(root).parts):",
        "if False:",
        "test_caches_and_other_file_types_are_skipped",
        "assert",
    ),
    gd(
        "G10 a pattern that matches everything is accepted",
        'if any(p.search("") for p in patterns):',
        "if False:",
        "test_a_pattern_that_matches_the_empty_text_stops_the_guard",
        "DID NOT RAISE",
    ),
    gd(
        "G11 any text is a folder name",
        r'r"[A-Za-z0-9_][A-Za-z0-9_.-]*"',
        'r".+"',
        "test_a_folder_name_that_is_a_path_stops_the_guard",
        "DID NOT RAISE",
    ),
    gd(
        "G12 a failed copy run reports a pass",
        "check=False,\n        ).returncode",
        "check=False,\n        ).returncode * 0",
        "test_a_product_that_reaches_into_the_folder_fails_in_the_copy",
        "assert",
    ),
]


if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in m.name for m in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)
    first_lines: dict[str, str] = {}

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
        [T_MB, T_G],
        extra_dirs=("tests", "tools", "templates"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
