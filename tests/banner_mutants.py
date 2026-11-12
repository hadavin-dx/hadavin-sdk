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
        "does not name every real service",  # now stopped by the claim post-condition, before the old assertion
        crash="ValueError",
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
        "claims made-up data",  # now stopped by the claim post-condition, before the old assertion
        crash="ValueError",
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
        "if (!hasName(text, real[i])) return NOT_CONFIRMED;",
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
        "var MODES = Object.freeze(['demo', 'pilot', 'prod']);",
        "var MODES = Object.freeze(['demo', 'pilot', 'prod', 'canary']);",
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
        "elif not name.search(_nfkc(f.read_text(",
        "elif False and not name.search(_nfkc(f.read_text(",
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
        "if rel not in loaders and name.search(_nfkc(parts[-1])):",
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
        "if suffix in cfg.skip_suffixes and _looks_binary(data):",
        'if suffix not in (".py", ".md", ".json"):',
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
        "if suffix in cfg.skip_suffixes and _looks_binary(data):",
        "if path.suffix in cfg.skip_suffixes and _looks_binary(data):",
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
        r'+ re.escape(p) + r"(?![\w/\\-])"',
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
        "    for rel in listed:",
        "    for rel in [r for r in listed if '__pycache__' not in r]:",
        "test_every_symlink_under_a_product_root_is_a_hit",
        "assert",
    ),
    # -- round 3: endpoints beyond the backends, the claim post-condition, the page and guard minors ------------------
    mb(
        "B20 a system that is not this machine is not counted as real",
        "        found.append(EXTERNAL_SYSTEMS)",
        "        pass",
        "test_a_demo_config_that_can_reach_beyond_this_machine_is_not_called_made_up",
        "AssertionError: ('systems'",
    ),
    mb(
        "B21 an egress host that is not this machine is not counted as real",
        "        found.append(EGRESS_HOSTS)",
        "        pass",
        "test_a_demo_config_that_can_reach_beyond_this_machine_is_not_called_made_up",
        "AssertionError: ('egress_hosts'",
    ),
    mb(
        "B22 a read source that is not this machine is not counted as real",
        "        found.append(READ_SOURCES)",
        "        pass",
        "test_a_demo_config_that_can_reach_beyond_this_machine_is_not_called_made_up",
        "AssertionError: ('sources'",
    ),
    mb(
        "B23 every address counts as this machine",
        "    return isinstance(host, str) and bool(host) and normalise_host(host) in LOOPBACK",
        "    return True",
        "test_a_demo_config_that_can_reach_beyond_this_machine_is_not_called_made_up",
        "AssertionError: ('",
    ),
    mb(
        "B24 a value that is not text is read as this machine",
        "if not isinstance(url, str) or re.search",
        "if not isinstance(url, str):\n        return False\n    if re.search",
        "test_a_demo_config_that_can_reach_beyond_this_machine_is_not_called_made_up",
        "AssertionError: ('systems', {'crm': namespace(base_url=None)",
    ),
    mb(
        "B25 a source whose endpoint cannot be worked out is read as this machine",
        "and unknown is shown as real\n        return True",
        "and unknown is shown as real\n        return False",
        "test_a_demo_config_that_can_reach_beyond_this_machine_is_not_called_made_up",
        "unknown-kind",
    ),
    mb(
        "B26 a banner may leave without naming every real service",
        "        if missing:",
        "        if False:",
        "test_a_banner_is_checked_against_what_it_claims_before_it_leaves",
        "DID NOT RAISE",
    ),
    mb(
        "B27 a real or quiet banner may hold the made-up sentence",
        '    if banner.tone != "demo" and any(',
        "    if False and any(",
        "test_a_banner_is_checked_against_what_it_claims_before_it_leaves",
        "DID NOT RAISE",
    ),
    mb(
        "B28 a demo banner may name a real service",
        '    if banner.tone == "demo" and banner.real:',
        "    if False:",
        "test_a_banner_is_checked_against_what_it_claims_before_it_leaves",
        "DID NOT RAISE",
    ),
    js(
        "J10 the fallback banner can be changed by a page",
        "var NOT_CONFIRMED = Object.freeze({",
        "var NOT_CONFIRMED = ({",
        "test_the_page_exports_and_the_fallback_cannot_be_changed_by_a_page",
        "assert",
    ),
    js(
        "J11 the exports can be changed by a page",
        "var api = Object.freeze({",
        "var api = ({",
        "test_the_page_exports_and_the_fallback_cannot_be_changed_by_a_page",
        "assert",
    ),
    js(
        "J12 the last-resort write does not unhide the element first",
        "        el.hidden = false; // first: whatever else fails below, the element is never left hidden\n",
        "",
        "test_a_failed_last_resort_write_never_leaves_the_banner_hidden",
        "assert",
    ),
    js(
        "J14 a real name is matched inside another word",
        "if (!hasName(text, real[i])) return NOT_CONFIRMED;",
        "if (text.indexOf(real[i]) < 0) return NOT_CONFIRMED;",
        "test_a_real_name_is_matched_as_a_whole_word_only",
        "assert",
    ),
    gd(
        "G24 a submodule under a product root is not a hit",
        "            if _under(rel, roots) is not None and rel not in exempt:",
        "            if False:",
        "test_a_submodule_under_a_product_root_is_a_hit_and_one_outside_is_not",
        "assert",
    ),
    gd(
        "G25 every file with a binary ending is skipped unread",
        "if suffix in cfg.skip_suffixes and _looks_binary(data):",
        "if suffix in cfg.skip_suffixes:",
        "test_a_text_file_renamed_to_a_binary_ending_is_read_and_a_real_binary_is_searched_as_bytes",
        "assert",
    ),
    gd(
        "G26 a NUL byte anywhere in the file makes it binary",
        'if b"\\0" in data[:8192]:',
        'if b"\\0" in data:',
        "test_a_text_file_renamed_to_a_binary_ending_is_read_and_a_real_binary_is_searched_as_bytes",
        "assert",
    ),
    gd(
        "G27 a listed phrase may stand beside a dash",
        "(?<![\\w/\\\\-])",
        "(?<![\\w/\\\\])",
        "test_a_listed_phrase_is_matched_in_its_own_case_and_not_beside_a_dash",
        "x-DEMO_ONLY",
    ),
    gd(
        "G28 a listed phrase may be followed by a dash",
        '(?![\\w/\\\\-])")',
        '(?![\\w/\\\\])")',
        "test_a_listed_phrase_is_matched_in_its_own_case_and_not_beside_a_dash",
        "DEMO_ONLY-x",
    ),
    gd(
        "G29 a listed phrase is matched in any case",
        '+ re.escape(p) + r"(?![\\w/\\\\-])")',
        '+ re.escape(p) + r"(?![\\w/\\\\-])", re.IGNORECASE)',
        "test_a_listed_phrase_is_matched_in_its_own_case_and_not_beside_a_dash",
        "demo_only",
    ),
    # -- round 4: tool hosts, the page fallback, guard rules, URL parity, name parity --------------------------------------
    mb(
        "B30 tool_specs gets a default",
        "    *,\n    tool_specs: object,\n",
        "    *,\n    tool_specs: object = {},\n",
        "test_tool_specs_has_no_default_so_forgetting_it_is_an_error",
        "DID NOT RAISE",
    ),
    mb(
        "B31 a tool manifest host is not counted as real",
        "            found.append(TOOL_HOSTS)",
        "            pass",
        "test_a_tool_manifest_host_that_is_not_this_machine_is_a_real_service",
        "assert",
    ),
    mb(
        "B32 tool modules without manifests count as nothing",
        "        if modules:\n            found.append(TOOL_MODULES)",
        "        if False:\n            found.append(TOOL_MODULES)",
        "test_tool_modules_without_the_manifests_count_as_one_real_service",
        "assert",
    ),
    mb(
        "B33 a tool host on this machine is counted as real",
        "            not _is_this_machine(host)\n            for by_name in tool_specs.values()",
        "            True\n            for by_name in tool_specs.values()",
        "test_tool_hosts_on_this_machine_or_none_keep_the_demo_banner",
        "AssertionError: {'a'",
    ),
    mb(
        "B34 a tool_specs that is not a mapping is accepted",
        "        if not isinstance(tool_specs, Mapping):",
        "        if False:",
        "test_tool_modules_without_the_manifests_count_as_one_real_service",
        "has no attribute 'values'",
        crash="AttributeError",
    ),
    mb(
        "B35 the services of a config ignore the tool specs",
        "    real += _outside_endpoints(config, tool_specs)",
        "    real += _outside_endpoints(config, {})",
        "test_a_tool_manifest_host_that_is_not_this_machine_is_a_real_service",
        "assert",
    ),
    mb(
        "B36 banner_from_config drops the tool specs",
        "    real, stand_ins = _services_in(config, tool_specs)",
        "    real, stand_ins = _services_in(config, {})",
        "test_a_real_registry_tools_mapping_is_what_the_banner_reads",
        "assert",
    ),
    mb(
        "B37 a host is compared without the shared normaliser",
        "bool(host) and normalise_host(host) in LOOPBACK",
        "bool(host) and host in LOOPBACK",
        "test_the_shared_normaliser_treats_these_as_this_machine",
        "localhost./",
    ),
    mb(
        "B38 a backslash in a url does not count as leaving",
        r'r"[\\\s\x00-\x1f\x7f]"',
        r'r"[\s\x00-\x1f\x7f]"',
        "test_an_odd_url_is_shown_as_leaving_this_machine",
        "a\\\\b",
    ),
    mb(
        "B39 white space or a control character in a url does not count as leaving",
        r'r"[\\\s\x00-\x1f\x7f]"',
        r'r"[\\]"',
        "test_an_odd_url_is_shown_as_leaving_this_machine",
        "/a b",
    ),
    mb(
        "B40 a non-ASCII url is read by its host only",
        " or not url.isascii():",
        ":",
        "test_an_odd_url_is_shown_as_leaving_this_machine",
        "caf\u00e9",
    ),
    mb(
        "B41 a percent sign in a url does not count as leaving",
        '    if "%" in parts.netloc or "%" in parts.path or "@" in parts.netloc:',
        '    if "@" in parts.netloc:',
        "test_an_odd_url_is_shown_as_leaving_this_machine",
        "%2e%2e",
    ),
    mb(
        "B42 credentials in a url do not count as leaving",
        '    if "%" in parts.netloc or "%" in parts.path or "@" in parts.netloc:',
        '    if "%" in parts.netloc or "%" in parts.path:',
        "test_an_odd_url_is_shown_as_leaving_this_machine",
        "user@127.0.0.1",
    ),
    mb(
        "B43 a source that does not build is read as this machine",
        '    except Exception:  # noqa: BLE001 - any failure means "unknown", and unknown is shown as real',
        '    except KeyError:  # noqa: BLE001 - any failure means "unknown", and unknown is shown as real',
        "test_a_demo_config_that_can_reach_beyond_this_machine_is_not_called_made_up",
        "ValidationError",
        crash="ValidationError",
    ),
    mb(
        "B44 a config field that is missing reads as empty",
        "    value = getattr(config, name, None)",
        "    value = getattr(config, name, ())",
        "test_a_config_that_lost_an_endpoint_field_raises_and_is_never_read_as_nothing",
        "is a tuple",
        crash="TypeError",
    ),
    mb(
        "B45 an empty made-up sentence switches the check off",
        "    if not all(isinstance(c, str) and c.strip() for c in claim):",
        "    if False:",
        "test_an_empty_made_up_sentence_is_an_error_not_a_switched_off_check",
        "DID NOT RAISE",
    ),
    mb(
        "B46 a name next to a word character is matched",
        'rf"(?<![{word}])(?<![A-Za-z0-9]\\.)"',
        'rf"(?<![A-Za-z0-9]\\.)"',
        "test_names_in_follows_the_table",
        "xCRM",
    ),
    mb(
        "B47 a name followed by a dot and a letter is matched",
        'rf"(?![{word}])(?!\\.[A-Za-z0-9])"',
        'rf"(?![{word}])"',
        "test_names_in_follows_the_table",
        "CRM.v2",
    ),
    js(
        "J15 the page clears the old text before it writes the new words",
        "    el.textContent = b.tag + ' ' + b.text;\n    el.textContent = '';",
        "    el.textContent = '';",
        "test_a_failed_last_resort_write_never_leaves_the_banner_hidden",
        "previous banner text",
    ),
    js(
        "J16 the fallback writes empty text",
        "        el.textContent = b.tag + ' ' + b.text;\n        el.setAttribute('data-tone', b.tone);",
        "        el.textContent = '';\n        el.setAttribute('data-tone', b.tone);",
        "test_a_failed_append_leaves_words_on_the_screen_never_an_empty_banner",
        "assert",
    ),
    js(
        "J17 the page lets a prefix of another word count as the name",
        "    var joinedBefore = isWordPart(before) ||",
        "    var joinedBefore = false ||",
        "test_the_page_and_python_agree_on_every_row_of_the_name_table",
        "xCRM",
    ),
    js(
        "J18 the page stops at the first partial match",
        "      at = text.indexOf(name, at + 1);",
        "      break;",
        "test_the_page_and_python_agree_on_every_row_of_the_name_table",
        "CRMS and CRM",
    ),
    gd(
        "G30 a line is not normalised before it is searched",
        "        line = _nfkc(raw)",
        "        line = raw",
        "test_a_full_width_spelling_of_the_name_is_a_hit_in_a_line_and_in_a_path",
        "ｄｅｍｏ",
    ),
    gd(
        "G31 a path part is not normalised before it is searched",
        "            part = _nfkc(parts[depth - 1])",
        "            part = parts[depth - 1]",
        "test_a_full_width_spelling_of_the_name_is_a_hit_in_a_line_and_in_a_path",
        "assert",
    ),
    gd(
        "G32 a compiled or packed file is not refused",
        "    if suffix in REFUSED_SUFFIXES:",
        "    if False:",
        "test_a_compiled_or_packed_file_in_a_product_folder_is_refused",
        "assert",
    ),
    gd(
        "G33 one refused ending is missing",
        '(".pyc", ".so", ".zip", ".whl")',
        '(".pyc", ".so", ".zip")',
        "test_a_compiled_or_packed_file_in_a_product_folder_is_refused",
        "assert",
    ),
    gd(
        "G34 a binary is searched in UTF-8 only",
        "        hit = any(rx.search(data) for rx in byte_names.values())",
        '        hit = bool(byte_names["utf-8"].search(data))',
        "test_a_binary_is_searched_as_bytes_in_utf8_and_both_utf16_orders",
        "AssertionError: le",
    ),
    gd(
        "G35 a binary is not searched at all",
        '        return [f"{rel}: names-demo-only-folder (inside a binary file)"] if hit else []',
        "        return []",
        "test_a_binary_is_searched_as_bytes_in_utf8_and_both_utf16_orders",
        "AssertionError: u8",
    ),
    gd(
        "G36 bytes that are not valid text and hold no NUL are not binary",
        "    except UnicodeDecodeError:\n        return True\n    return False",
        "    except UnicodeDecodeError:\n        return False\n    return False",
        "test_a_binary_that_is_not_valid_text_and_has_no_nul_is_searched_not_skipped",
        "assert",
    ),
    gd(
        "G37 UTF-16 text in a text file is not searched",
        '    if b"\\0" in data and any(',
        "    if False and any(",
        "test_text_written_as_utf16_without_a_mark_is_found_in_a_text_ending",
        "assert",
    ),
    gd(
        "G38 an exempt submodule is still reported as a submodule",
        "            if _under(rel, roots) is not None and rel not in exempt:",
        "            if _under(rel, roots) is not None:",
        "test_a_submodule_that_is_listed_as_exempt_is_not_a_second_hit",
        "assert",
    ),
    gd(
        "G39 a submodule whose folder is missing is not a hit",
        '        if path and info.startswith("160000 "):',
        '        if path and info.startswith("160000 ") and (repo / path).is_dir():',
        "test_a_submodule_whose_folder_is_missing_is_still_a_hit",
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
