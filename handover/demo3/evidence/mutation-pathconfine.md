# Q8 mutation check: tools/pathconfine.py (public main f3c39cf)

Run 2026-11-13 12:35-12:51 UTC (18:05-18:21 IST). Private worktree /home/user/work/q8-base, restored after every mutant; final `git status --short` empty. Runner: handover/demo3/tools/q8_mutate.py. Raw per-mutant logs: raw/q8-results.jsonl.

**Result: 34 mutants, 0 invalid, 29 killed, 5 survived. Mutation score 29/34 = 85.3%.** (30 asked; 4 extra run because time allowed.)

## Survivors (all passed tests/test_path_confinement.py, test_sonar_p2_choke_points.py, test_followup_b.py, test_n8n_api_url.py, test_load_tools.py)

- M03: `text = str.__str__(text)` -> `pass`
  REAL GAP. No test hands in a str subclass whose methods answer differently on a later call; the exact-str copy is untested.
- M08: `if len(text) > MAX_PATH_CHARS:` -> `if len(text) >= MAX_PATH_CHARS:`
  REAL GAP (off-by-one). Tests use limit+1 chars (refused) and 4095 chars; none uses exactly 4096, so `>=` is not caught.
- M11: `    except ValueError:
        return False` -> `    except ValueError:
        return True`
  Equivalent on Linux: after realpath both paths are absolute, so commonpath never raises ValueError. Only reachable on Windows (other drive); untested there, could be tested with an ntpath mock.
- M15: `except (OSError, RuntimeError, ValueError) as exc:` -> `except (OSError, RuntimeError) as exc:`
  Equivalent in practice: _text already refuses NUL before _resolve runs, so ValueError from realpath is not reachable through the public functions. Defence in depth only.
- M20: `len(name) > MAX_NAME_CHARS` -> `len(name) >= MAX_NAME_CHARS`
  REAL GAP (off-by-one). No test of a new file name of exactly 255 characters (should be accepted) vs 256.

## All mutants

| id | change (old -> new) | result | killed by (first failing test) |
|---|---|---|---|
| M01 | `if not isinstance(path, (str, os.PathLike)):` -> `if False:` | KILLED | test_not_a_path_is_refused - TypeError... |
| M02 | `if not isinstance(text, str):` -> `if False:` | KILLED | test_sqlite_uri_refuses_a_path_object_that_gives_bytes_and_a_text_that_is_too_long |
| M03 | `text = str.__str__(text)` -> `pass` | SURVIVED |  |
| M04 | `if not text.strip():` -> `if not text:` | KILLED | test_empty_or_blank_text_is_refused_as_empty_by_every_function[ -confine] |
| M05 | `[\x00-\x1f\x7f-\x9f]")` -> `[\x00-\x1f\x7f]")` | KILLED | test_c0_del_and_c1_controls_are_refused_by_every_function[\x80-confine] |
| M06 | `[\x00-\x1f\x7f-\x9f]")` -> `[\x01-\x1f\x7f-\x9f]")` | KILLED | test_c0_del_and_c1_controls_are_refused_by_every_function[\x00-confine] |
| M07 | `[\x00-\x1f\x7f-\x9f]")` -> `[\x00-\x1f\x80-\x9f]")` | KILLED | test_c0_del_and_c1_controls_are_refused_by_every_function[\x7f-confine] |
| M08 | `if len(text) > MAX_PATH_CHARS:` -> `if len(text) >= MAX_PATH_CHARS:` | SURVIVED |  |
| M09 | `if len(text) > MAX_PATH_CHARS:` -> `if len(text) > MAX_PATH_CHARS + 1:` | KILLED | test_v5_the_path_length_limit_is_checked_before_resolving |
| M10 | `return os.path.commonpath([os.path.normcase(real), os.path.normcase(root)]) == os.path.normcase(root)` -> `return True` | KILLED | test_dot_dot_escape_is_refused - Asser... |
| M11 | `    except ValueError:\n        return False` -> `    except ValueError:\n        return True` | SURVIVED |  |
| M12 | `if relative == os.curdir:` -> `if False:` | KILLED | test_a_path_that_names_an_allowed_folder_itself_is_refused_as_a_folder[confine] |
| M13 | `for root in allowed:` -> `for root in allowed[:1]:` | KILLED | test_extra_folder_from_the_environment |
| M14 | `return os.path.realpath(text)  # follows` -> `return os.path.abspath(text)  # follows` | KILLED | test_the_returned_path_is_the_resolved_target_of_an_inside_link |
| M15 | `except (OSError, RuntimeError, ValueError) as exc:` -> `except (OSError, RuntimeError) as exc:` | SURVIVED |  |
| M16 | `if entry.is_symlink():` -> `if False:` | KILLED | test_a_link_loop_is_refused_and_not_a_traceback |
| M17 | `if last and is_folder:` -> `if False:` | KILLED | test_load_env_resolves_its_own_path_from_the_top_of_the_file_system |
| M18 | `if not last and not is_folder:` -> `if False:` | KILLED | test_v5_a_file_in_the_middle_of_the_path_is_refused_as_not_a_folder[confine] |
| M19 | ` or name.endswith(".")` -> `` | KILLED | test_v3_a_new_name_that_ends_with_a_dot_is_refused[new.] |
| M20 | `len(name) > MAX_NAME_CHARS` -> `len(name) >= MAX_NAME_CHARS` | SURVIVED |  |
| M21 | `name.split(".", 1)[0].lower() in _DEVICES` -> `name.split(".", 1)[0] in _DEVICES` | KILLED | test_v3_a_new_name_may_not_be_a_windows_device_name[{}-con] |
| M22 | `for n in range(10)})` -> `for n in range(1, 10)})` | KILLED | test_v3_a_new_name_may_not_be_a_windows_device_name[{}-com0] |
| M23 | `return "".join(_NAME_CHARS[c] for c in name)` -> `return name` | KILLED | test_v2_a_missing_file_that_is_read_says_no_such_file[my log.jsonl] |
| M24 | `unicodedata.normalize("NFC", name)` -> `name` | KILLED | test_v4_a_fake_macos_listing_is_matched_in_the_other_unicode_form |
| M25 | `if loose is None and _key(e.name)` -> `if loose is not None and _key(e.name)` | KILLED | test_v4_a_fake_macos_listing_is_matched_in_the_other_unicode_form |
| M26 | `            if not last:\n                raise PathRefused(f"{what}: a folder on the path does not exist")` -> `            if False:\n                raise PathRefused(f"{what}: a folder on the path does not exist")` | KILLED | test_v5_the_path_length_limit_is_checked_before_resolving |
| M27 | `            raise PathRefused(f"{what}: no such file")` -> `            return os.path.join(current, part)` | KILLED | test_inside_path_is_accepted_and_returned_resolved |
| M28 | `if path_module.sep == "\\" and flat.startswith("\\??\\"):` -> `if False:` | KILLED | test_sqlite_uri_refuses_each_windows_device_or_network_form_on_ntpath[\\??\\UNC\\host\\sha |
| M29 | `.replace("/", "\\")[:2] == "\\\\":` -> `.replace("/", "\\")[:2] == "xx":` | KILLED | test_read_book_turns_the_network_path_refusal_into_an_input_error |
| M30 | `return text  # the caller must use ONLY` -> `return str(path)  # the caller must use ONLY` | KILLED | test_sqlite_uri_accepts_a_path_object_and_a_text_alike |
| M31 | `.as_uri() + "?mode=ro"` -> `.as_uri() + ""` | KILLED | test_sqlite_uri_encodes_query_and_fragment_characters |
| M32 | `except UnicodeEncodeError:  # text` -> `except KeyError:  # text` | KILLED | test_a_lone_surrogate_is_a_plain_refusal_not_a_unicode_error |
| M33 | `if not tail:\n        raise` -> `if False:\n        raise` | KILLED | test_the_top_of_the_file_system_is_refused_as_a_folder_in_anywhere_mode |
| M34 | `return drive + root, tail` -> `return root, tail` | KILLED | test_split_root_gives_the_top_of_each_kind_of_path |

Notes: each mutant is one exact-text change; the file imported for all 34. Baseline (unmutated) test_path_confinement.py: 378 passed, 1 skipped in 99 s. Survivors were also run against the other four files; all passed (nothing kills them). Nothing was fixed.