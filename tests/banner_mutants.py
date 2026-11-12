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


def gt(name, old, new, killer, expect):
    return mutant(name, "tools/demo_only_guard.toml", old, new, T_G, killer, expect)


M = [
    # -- Python: the banner words and choice (src/hadavin_sdk/mode_banner.py) ----------------------------------------
    mb(
        "B1 an unknown stage is accepted (the code keeps running)",
        "    if mode not in STAGES:",
        "    mode = mode if mode in STAGES else STAGES[0]\n    if False:",
        "test_an_unknown_stage_is_refused",
        "DID NOT RAISE",
    ),
    mb(
        "B2 a bare string is read letter by letter",
        "isinstance(keys, (str, bytes, Mapping, set, frozenset)) or ",
        "",
        "test_a_bare_string_dict_set_or_non_list_is_refused_not_read_by_accident",
        "DID NOT RAISE",
    ),
    mb(
        "B2b a dict or a set is accepted as a list",
        "(str, bytes, Mapping, set, frozenset)",
        "(str, bytes)",
        "test_a_bare_string_dict_set_or_non_list_is_refused_not_read_by_accident",
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
        "B3b the name class allows a sentence break and edge spaces again",
        '    r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9_-])?(?: [A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9_-])?)*"',
        '    r"[A-Za-z0-9][A-Za-z0-9 ._-]{0,39}"',
        "test_a_name_that_could_change_the_sentence_is_refused",
        "DID NOT RAISE",
    ),
    mb(
        "B3c the length bound is gone (the 41-character name)",
        "            or len(shown) > _NAME_MAX\n",
        "",
        "test_a_plain_name_of_the_longest_allowed_length_is_shown_and_one_more_character_is_not",
        "DID NOT RAISE",
    ),
    mb(
        "B3d the reserved words are allowed in a name",
        "            or _NAME_RESERVED.search(shown)\n",
        "",
        "test_a_name_that_could_change_the_sentence_is_refused",
        "DID NOT RAISE",
    ),
    mb(
        "B3e a key that is not text is accepted",
        "if not isinstance(key, str) or not key:",
        "if False:",
        "test_a_service_key_that_is_not_text_is_refused",
        "DID NOT RAISE",
    ),
    mb(
        "B3f a repeated name is shown twice",
        "out.setdefault(shown, None)",
        "out[shown + str(len(out))] = None",
        "test_names_come_from_the_caller_and_repeats_are_shown_once_in_order",
        "assert",
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
        "    if real and mode != _DEMO_STAGE:\n",
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
        'ModeBanner(mode, "quiet", tag, words.none_real,',
        'ModeBanner(mode, "quiet", tag, words.made_up,',
        "test_pilot_or_live_with_nothing_real_is_quiet_and_not_made_up",
        "assert",
    ),
    mb(
        "B7b a pilot or live screen hides its stand-ins",
        '    else:\n        extra = words.standins_still.format(names=", ".join(pretend)) if pretend else ""',
        '    else:\n        extra = ""',
        "test_pilot_or_live_still_lists_the_stand_ins_in_the_quiet_tone",
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
        'shown = names.get(key, f"component {key}")',
        "shown = key",
        "test_names_come_from_the_caller_and_repeats_are_shown_once_in_order",
        "assert",
    ),
    mb(
        "B9b an unnamed key is shown as the bare key",
        'f"component {key}"',
        "key",
        "test_a_key_without_a_shown_name_is_read_as_component_and_the_key",
        "assert",
    ),
    mb(
        "B10 the stand-ins are the kinds that are NOT demo-only",
        "if (component, kind) in DEMO_ONLY:",
        "if (component, kind) not in DEMO_ONLY:",
        "test_banner_from_config_reads_the_stage_and_both_lists_from_the_config",
        "assert",
    ),
    mb(
        "B10b the real list is derived as empty",
        "        elif (component, kind) not in _NOTHING_CONNECTED:\n            real.append(component)",
        "        elif False:\n            real.append(component)",
        "test_a_real_kind_in_the_config_is_named_and_the_made_up_sentence_is_never_given",
        "assert",
    ),
    mb(
        "B10c the kinds that connect to nothing are listed as real",
        "_NOTHING_CONNECTED = NOT_PROD | {",
        "_NOTHING_CONNECTED = frozenset() | {",
        "test_banner_from_config_reads_the_stage_and_both_lists_from_the_config",
        "assert",
    ),
    mb(
        "B10d an entry without a kind is guessed into the real list",
        "or not isinstance(kind, str) or not kind",
        "",
        "test_an_entry_without_a_kind_is_refused_not_guessed_into_a_list",
        "DID NOT RAISE",
    ),
    mb(
        "B10e the stage of the config is taken from nowhere (always demo)",
        "        config.environment, real_services=real",
        "        _DEMO_STAGE, real_services=real",
        "test_banner_from_config_reads_the_stage_and_both_lists_from_the_config",
        "assert",
    ),
    mb(
        "B11 the Python fallback differs from the page fallback",
        '"tone": "unconfirmed",\n        "tag": words.not_confirmed_tag',
        '"tone": "real",\n        "tag": words.not_confirmed_tag',
        "test_the_page_fallback_has_the_same_words_as_the_python_fallback",
        "assert",
    ),
    mb(
        "B12 the lists get a default again (nothing real unless said)",
        "real_services: Iterable[str],\n    stand_ins: Iterable[str],",
        "real_services: Iterable[str] = (),\n    stand_ins: Iterable[str] = (),",
        "test_the_lists_are_required_so_an_unchecked_call_cannot_say_nothing_real",
        "DID NOT RAISE",
    ),
    mb(
        "B13 names that are not a mapping are accepted",
        "    if names is not None and not isinstance(names, Mapping):",
        "    if False:",
        "test_names_that_are_not_a_mapping_are_refused_with_a_type_error",
        "AttributeError",
        crash="AttributeError",
    ),
    mb(
        "B14 a text longer than the page accepts is returned",
        "    if len(banner.text) > MAX_TEXT_LENGTH or len(banner.standins) > MAX_TEXT_LENGTH:",
        "    if False:",
        "test_a_banner_longer_than_the_page_script_accepts_is_refused_in_python",
        "DID NOT RAISE",
    ),
    mb(
        "B15 words without a tag for every stage are accepted",
        "        if missing:\n",
        "        if False:\n",
        "test_the_default_words_have_a_tag_for_every_stage_and_a_missing_one_is_refused",
        "DID NOT RAISE",
    ),
    mb(
        "B16 the old public name banner_for is back",
        "def not_confirmed(",
        "banner_for = _banner_for\n\n\ndef not_confirmed(",
        "test_the_old_public_names_are_gone_and_banner_from_config_is_the_only_entry",
        "banner_for",
    ),
    # -- the page script (templates/mode-banner/mode_banner.js) -------------------------------------------------------
    js(
        "J1 a banner with an unknown tone is painted",
        "if (TONES.indexOf(tone) < 0 || tone === 'unconfirmed') return NOT_CONFIRMED;",
        "if (tone === 'unconfirmed') return NOT_CONFIRMED;",
        "test_a_missing_or_odd_banner_is_never_hidden_it_says_not_confirmed",
        "assert",
    ),
    js(
        "J1b a banner that says it is unconfirmed is painted as given",
        "if (TONES.indexOf(tone) < 0 || tone === 'unconfirmed') return NOT_CONFIRMED;",
        "if (TONES.indexOf(tone) < 0) return NOT_CONFIRMED;",
        "test_a_missing_or_odd_banner_is_never_hidden_it_says_not_confirmed",
        "assert",
    ),
    js(
        "J2 a quiet banner is hidden",
        "el.hidden = false;\n  }\n  // Paints",
        "el.hidden = b.tone === 'quiet';\n  }\n  // Paints",
        "test_the_page_paints_exactly_what_python_wrote",
        "assert",
    ),
    js(
        "J3 the text is put in as HTML",
        "n.textContent = text;",
        "n.innerHTML = text;",
        "test_markup_in_the_text_is_shown_as_text_never_parsed",
        "innerHTML",
    ),
    js(
        "J4 the stand-ins line is not painted",
        "if (b.standins !== '') nodes.push",
        "if (false) nodes.push",
        "test_the_page_paints_exactly_what_python_wrote",
        "assert",
    ),
    js(
        "J5 a very long text is painted",
        "var MAX_TEXT = 600;",
        "var MAX_TEXT = 6000;",
        "test_a_missing_or_odd_banner_is_never_hidden_it_says_not_confirmed",
        "assert",
    ),
    js(
        "J6 a throwing getter escapes the painter",
        "    } catch (e) {\n      return NOT_CONFIRMED;\n    }",
        "    } finally {\n    }",
        "test_the_painter_never_throws_and_never_leaves_the_page_blank",
        "boom",
    ),
    js(
        "J7 any mode string is accepted",
        "      if (MODES.indexOf(mode) < 0) return NOT_CONFIRMED;\n",
        "",
        "test_a_banner_that_contradicts_itself_is_not_painted_as_given",
        "assert",
    ),
    js(
        "J8 tone demo is accepted with another mode",
        "(mode !== 'demo' || real.length !== 0)",
        "(real.length !== 0)",
        "test_a_banner_that_contradicts_itself_is_not_painted_as_given",
        "assert",
    ),
    js(
        "J8b tone demo is accepted with a real service listed",
        "(mode !== 'demo' || real.length !== 0)",
        "(mode !== 'demo')",
        "test_a_banner_that_contradicts_itself_is_not_painted_as_given",
        "assert",
    ),
    js(
        "J8c tone quiet is accepted in the demo mode",
        "(mode === 'demo' || real.length !== 0)",
        "(real.length !== 0)",
        "test_a_banner_that_contradicts_itself_is_not_painted_as_given",
        "assert",
    ),
    js(
        "J8d tone quiet is accepted with a real service listed",
        "(mode === 'demo' || real.length !== 0)",
        "(mode === 'demo')",
        "test_a_banner_that_contradicts_itself_is_not_painted_as_given",
        "assert",
    ),
    js(
        "J8e tone real is accepted with nothing real listed",
        "if (real.length === 0) return NOT_CONFIRMED;",
        "",
        "test_a_banner_that_contradicts_itself_is_not_painted_as_given",
        "assert",
    ),
    js(
        "J8f tone real is accepted when the text does not name the service",
        "if (text.indexOf(real[i]) < 0) return NOT_CONFIRMED;",
        "if (false) return NOT_CONFIRMED;",
        "test_a_banner_that_contradicts_itself_is_not_painted_as_given",
        "assert",
    ),
    js(
        "J9 the lists are not checked to be lists of text",
        "if (!isTextList(real) || !isTextList(standIns)) return NOT_CONFIRMED;",
        "",
        "test_a_missing_or_odd_banner_is_never_hidden_it_says_not_confirmed",
        "assert",
    ),
    js(
        "J11 a missing element changes what is reported",
        "if (el === null || el === undefined) return b;",
        "",
        "test_the_painter_never_throws_and_never_leaves_the_page_blank",
        "assert",
    ),
    js(
        "J12 a failed painting leaves nothing on the page",
        "el.textContent = b.tag + ' ' + b.text;",
        "",
        "test_the_painter_never_throws_and_never_leaves_the_page_blank",
        "assert",
    ),
    js(
        "J13 the page mode list differs from the stages",
        "var MODES = ['demo', 'pilot', 'prod'];",
        "var MODES = ['demo', 'pilot', 'prod', 'canary'];",
        "test_the_page_lists_are_the_python_lists",
        "assert",
    ),
    # -- the demo-only folder guard (tools/demo_only_guard.py and its settings) -------------------------------------
    gd(
        "G1 a product file that names the folder is not a hit",
        "        if name.search(shown):\n",
        "        if False:\n",
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
        "            if not is_loader:\n",
        "            if True:\n",
        "test_a_loader_may_name_the_folder_once_only_and_may_not_hold_a_fake_id",
        "assert",
    ),
    gd(
        "G3b a loader may name the folder any number of times",
        "if loader_lines > cfg.loader_max_lines:",
        "if False:",
        "test_a_loader_may_name_the_folder_once_only_and_may_not_hold_a_fake_id",
        "assert",
    ),
    gd(
        "G3c a loader is not checked for fake ids",
        "        if any(p.search(line) for p in cfg.fake_id_patterns):",
        "        if not is_loader and any(p.search(line) for p in cfg.fake_id_patterns):",
        "test_a_loader_may_name_the_folder_once_only_and_may_not_hold_a_fake_id",
        "assert",
    ),
    gd(
        "G4 a loader that does not name the folder is not stale",
        "elif not name.search(f.read_text",
        "elif False and not name.search(f.read_text",
        "test_a_stale_loader_entry_is_a_hit",
        "assert",
    ),
    gd(
        "G5 a folder deeper than the product root is not a hit",
        'for depth in range(len(root.split("/")) + 1, len(parts)):',
        "for depth in range(0):",
        "test_the_folder_inside_a_product_root_is_a_hit_at_any_depth_and_in_any_spelling",
        "Demo_Only",
    ),
    gd(
        "G5b a file name that holds the folder name is not a hit",
        "if rel not in loaders and name.search(parts[-1]):",
        "if False:",
        "test_a_file_or_folder_name_that_holds_the_folder_name_is_a_hit",
        "assert",
    ),
    gd(
        "G5c the name is matched in lower case only",
        "re.IGNORECASE)",
        "0)",
        "test_a_line_that_names_the_folder_in_another_spelling_is_a_hit",
        "Demo_Only",
    ),
    gd(
        "G5d only the underscore spelling is matched",
        '_SEP = r"[ _-]+"',
        '_SEP = r"_"',
        "test_a_line_that_names_the_folder_in_another_spelling_is_a_hit",
        "demo-only",
    ),
    gd(
        "G6 a missing product root is not a hit",
        "        if not top.is_dir():",
        "        if False:",
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
        "G9 files that git does not list yet are not scanned",
        '"--cached", "--others", "--exclude-standard"',
        '"--cached"',
        "test_a_file_is_scanned_whether_it_is_added_to_git_or_not",
        "assert",
    ),
    gd(
        "G9b files that git ignores are scanned",
        '"--cached", "--others", "--exclude-standard"',
        '"--cached", "--others"',
        "test_ignored_files_and_binary_endings_are_skipped",
        "assert",
    ),
    gd(
        "G9c a folder that is not a git checkout is scanned as empty",
        '    if not (repo / ".git").exists():',
        "    if False:",
        "test_the_scan_refuses_a_folder_that_is_not_a_git_checkout",
        "did not match",
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
        "test_the_copy_run_really_has_no_folder",
        "assert",
    ),
    gd(
        "G13 a symlink under a product root is not a hit",
        '        if is_link:\n            hits.append(f"{rel}: symlink-in-product-root")',
        '        if False:\n            hits.append(f"{rel}: symlink-in-product-root")',
        "test_every_symlink_under_a_product_root_is_a_hit",
        "assert",
    ),
    gd(
        "G13b a link outside the product folders into the folder is not a hit",
        "if is_link and full.resolve().is_relative_to(folder_target):",
        "if False:",
        "test_a_link_outside_the_product_folders_that_points_into_the_folder_is_a_hit",
        "assert",
    ),
    gd(
        "G14 only an allowlist of file endings is read",
        "if full.suffix.lower() in cfg.skip_suffixes:",
        'if full.suffix.lower() not in (".py", ".md", ".json"):',
        "test_every_file_type_is_read_not_only_a_list_of_endings",
        "a.cfg",
    ),
    gd(
        "G14b a file that is not text passes",
        '        return [f"{rel}: unreadable-file (not text and not on the list of known binary endings)"]',
        "        return []",
        "test_a_file_that_is_not_text_and_not_a_known_binary_ending_is_refused",
        "assert",
    ),
    gd(
        "G14c the binary skip list is not case-insensitive",
        "full.suffix.lower() in cfg.skip_suffixes",
        "full.suffix in cfg.skip_suffixes",
        "test_ignored_files_and_binary_endings_are_skipped",
        "assert",
    ),
    gt(
        "G15 only src is a product folder",
        'product_roots = ["src", "templates", "tools", "demos"]',
        'product_roots = ["src"]',
        "test_the_settings_of_this_repository_scan_every_product_folder",
        "assert",
    ),
    gd(
        "G16 the guard's own files are not exempt",
        "    exempt = set(cfg.exempt_files) | {cfg.copy_run_marker}",
        "    exempt = set()",
        "test_the_exempt_files_are_exactly_the_guard_itself_and_each_is_skipped_whole",
        "assert",
    ),
    gd(
        "G17 the copy-run marker is not required",
        "    if (repo / cfg.folder).is_dir() and not (repo / cfg.copy_run_marker).is_file():",
        "    if False:",
        "test_a_repository_that_has_the_folder_needs_the_copy_run_marker",
        "assert",
    ),
    gd(
        "G18 the copy run keeps the inherited import path",
        'env = {**os.environ, "PYTHONPATH": str(dest / "src")}',
        "env = {**os.environ}",
        "test_the_copy_run_imports_the_copy_even_if_the_original_is_on_the_import_path",
        "assert",
    ),
    gd(
        "G19 a package that is not from the copy is accepted",
        "            if checked.returncode != 0:",
        "            if False:",
        "test_the_copy_run_fails_when_the_package_comes_from_somewhere_else",
        "assert",
    ),
    gd(
        "G20 the copy run without a package to check is accepted",
        "    if not cfg.product_packages:",
        "    if False:",
        "test_the_copy_run_without_a_package_to_check_is_refused",
        "DID NOT RAISE",
    ),
    gd(
        "G21 a listed phrase is also accepted as part of a path or a longer word",
        r'+ re.escape(p) + r"(?![\w/\\])"',
        "+ re.escape(p)",
        "test_the_table_name_and_listed_phrases_are_not_hits_but_a_path_or_a_longer_word_is",
        "DEMO_ONLY/x",
    ),
    gd(
        "G22 a listed phrase that nothing holds is not stale",
        "        if p not in used",
        "        if False",
        "test_a_listed_phrase_that_no_product_file_holds_is_a_stale_hit",
        "assert",
    ),
    gd(
        "G23 a symlink named like a cache folder is not reported",
        "    for rel in tracked_paths(repo):",
        "    for rel in [r for r in tracked_paths(repo) if '__pycache__' not in r]:",
        "test_every_symlink_under_a_product_root_is_a_hit",
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
        extra_dirs=("tests", "tools", "templates", "demos"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
