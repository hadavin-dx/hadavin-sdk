# Evidence for PD Part 6 (mode banner and demo-only guard), head 06ed4b4cd59041c3ab4f2c8c59a841faccc7ac36

Evidence runner output: raw results only, no judging. Date 2026-11-13 (UTC). Branch wip/cloud-pd-banner. Old heads compared: cdbe1445fbff801a18d5deea6060fe2b66e3d982 (batch 10) and dd827d79e00bea6da81e757e0fa0746bbbd3449d (batch 9). Raw logs: /home/user/build/evidence-raw/pdbanner-06ed4b4c/ (not in the repository).

## 0. What failed, what was not run (first)

FAILED / needs a person to look:
1. bandit -ll on the changed files from the diff reports 1 Medium finding: B102 exec_used at tests/test_mode_banner.py:400 (`exec("from hadavin_sdk.mode_banner import *", star)`, carries `# noqa: S102`, which ruff honours and bandit does not). The CI command in .github/workflows/ci.yml is `bandit -q -r src demos tools -ll` (tests are not scanned); I ran that form on src and tools: exit 0 (section 2). So the CI gate does not see it; the strict reading of "bandit -ll on the changed files" does.
2. Guard masker: a token of 11 characters after a Bearer word, or 7 after a Basic word, stays visible in a git message (section 5, rows marked FLAG). The source calls this a stated limit (tools/demo_only_guard.py comment lines 269 onward) and a test pins it. Recorded as found; under the repo rule "fix, do not defer" this is a gap by design, not a bug in the tests.
3. Label vs result: test_a_copy_keeps_the_file_mode_where_os_has_no_fchmod carries the comment "on dd827d79 it passes; on cdbe1445 it passes. It is proof of a fix." It passes on both old heads (section 4), so it is not fail-before proof; its own label says so in the first half and contradicts it in the second.
4. Fail-before strength: many of the failures on old code are a bare `ImportError: cannot import name '_Given'` (that name does not exist on the old code): 25 of the 34 failures on cdbe1445 and 24 of the 52 failures on dd827d79. They fail because a name is missing, not because a behaviour differs.
5. 8 tests that fail on old code have no "fail-before" comment line (4 tests, each on both old heads): test_every_replaced_connected_part_reads_unconfirmed, test_the_recorded_names_cannot_be_laundered, test_every_row_of_the_table_has_its_own_label_and_a_search_text_found_exactly_once, test_the_changelog_states_the_row_count_of_the_table.

NOT RUN / limits of this run:
- No full pytest suite (cloud limit). The wider "other files that import app" set (26 files, 1108 tests per interpreter) WAS run, see section 1.
- Postgres tests skipped (HADAVIN_TEST_PG_DSN not set): 6 skipped in the wider set (listed in the raw logs). Nothing else skipped.
- Mutants: 112 of the 317 rows were run (52 required rows + 60 sampled), not all 317. Mutants were run on Python 3.13 only.
- Fail-before ran on Python 3.13 only, with the focused files (5 files), not the wider set.
- No Playwright, no real browser: the page script was run with node (v22) through the repo's own stand-in page (tests/mode_banner_probe.js), not a browser.
- CodeQL, SonarCloud, CodeRabbit, semgrep, pip-audit, zizmor not run (not requested).
- In the probes (section 5) the unreadable-app banner for ordinary tampering was recorded for one tooled app shape (one real tool host plus one unknown-kind source). Other shapes are not covered.

Environment: cloud variable names present in the shell of this runner (values never printed): GH_TOKEN, GITHUB_TOKEN, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_CA_BUNDLE, ANTHROPIC_BASE_URL. Every command below was run with `env -u` on all six names, so none reached a child process. hadavin_sdk.__file__ printed inside the worktree in every run (new head: /home/user/build/ER-pdbanner11-new/src/hadavin_sdk/__init__.py; cdbe: .../ER-pdbanner11-cdbe/...; dd82: .../ER-pdbanner11-dd82/...). Worktrees were detached and are removed (see end).

## 1. Focused tests, new head 06ed4b4c

Command shape: `PYTHONPATH=<worktree>/src python -m pytest -p no:cacheprovider -q -rfEs --tb=line <files>`, exit code read from pytest itself (written as PYTEST_EXIT in the log).

| interpreter | files | result | pytest exit code |
|---|---|---|---|
| Python 3.12.3 (uv venv built from the same 75 pins as the quick-check venv) | 26 | 1102 passed, 6 skipped in 108.62s | 0 |
| Python 3.13.18 (/home/user/build/wt/q8c1-b17fix/.venv) | 26 | 1102 passed, 6 skipped in 102.09s | 0 |

Files (found by grep for mode_banner, demo_only_guard, hadavin_sdk.app, banner_mutants): the four named files plus test_demo_only_guard_ci.py, test_cuj.py, test_k1a_pass_k.py, test_k3_leftovers.py, test_k3_pilot.py, test_k3_pilot_env.py, test_k3_review_fixes.py, test_k5_fixes1.py, test_k5_postgres.py, test_k5_review.py, test_k5_round10.py, test_k5_round5.py, test_k5_round8_postgres.py, test_k5_round9b.py, test_k5_tools.py, test_p1b_backends.py, test_p6_detectors.py, test_p7_tick.py, test_repo_rules.py, test_review_pr3_round2.py, test_stage_names.py, warden_port/test_audit_chain.py. Logs: focus-new-py312.log, focus-new-py313.log, focus_files.txt.
Per-file counts on 3.13 (junit): test_mode_banner 171, test_demo_only_guard 147, test_demo_only_guard_ci 8, test_changelog_numbers 6, test_banner_mutant_table 17 (349 together, 0 failures).
Skipped (6): Postgres-dependent tests in test_k5_postgres, test_k5_round8_postgres, warden_port/test_audit_chain (reason in the log: HADAVIN_TEST_PG_DSN not set).

## 2. Lint, security, secrets, suppression markers

Changed files: `git diff --name-only origin/main...HEAD` (origin/main = 2a8c2aac; 21 files, 11730 insertions, 11 deletions; 14 are .py).
- ruff check on the 14 .py files: exit 0, "All checks passed!" (ruff 0.16.9).
- ruff format --check: exit 0, "14 files already formatted".
- bandit -ll -q on the 14 .py files: exit 1. One Medium issue: B102 exec_used, tests/test_mode_banner.py:400:4. 770 Low issues (below -ll) not shown. See item 1 at the top.
- bandit -ll -r src tools (the CI scope without demos): exit 0.
- gitleaks 8.30.1 `git --log-opts="origin/main..HEAD"`: exit 0, "22 commits scanned", "no leaks found".
- Suppression markers on added lines (raw grep, 69 matching lines in suppress-added.log): noqa 43, type: ignore 15, fmt: skip 11, nosonar 0, nosec 0. (A line with two markers counts once per marker pattern; the 69 is lines.) Every noqa line carries a rule code; none is a blanket `# noqa`. The raw lines:

```
240:+        except Exception as exc:  # noqa: BLE001 - a tampered or hand-made app: the unconfirmed banner, not a crash
257:+        except Exception as exc:  # noqa: BLE001 - whatever is wrong with the app, the screen must still say something
841:+    except Exception:  # noqa: BLE001 - any failure means "unknown", and unknown is shown as real
1019:+    except Exception as exc:  # noqa: BLE001 - whatever went wrong, the screen must still say something
1032:+        tag = words.not_confirmed_tag  # type: ignore[attr-defined]
1033:+        text = words.not_confirmed  # type: ignore[attr-defined]
1045:+    except Exception:  # noqa: BLE001, S110 - malformed words: fall through to the fixed defaults
2140:+        '    except Exception:  # noqa: BLE001 - any failure means "unknown", and unknown is shown as real',
2141:+        '    except KeyError:  # noqa: BLE001 - any failure means "unknown", and unknown is shown as real',
2356:+        "    except Exception as exc:  # noqa: BLE001 - whatever went wrong, the screen must still say something",
2357:+        "    except ZeroDivisionError as exc:  # noqa: BLE001",
3118:+        "        except Exception as exc:  # noqa: BLE001 - whatever is wrong with the app, the screen must still say something",
3119:+        "        except KeyError as exc:  # noqa: BLE001 - whatever is wrong with the app, the screen must still say something",
4394:+    return g.GuardConfig(**base)  # type: ignore[arg-type]
4405:+        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)  # noqa: S603, S607
4411:+    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)  # noqa: S603, S607
4740:+    rng = random.Random(20261112)  # noqa: S311 - a seeded test generator, not a secret
4846:+    done = subprocess.run(  # noqa: S603 (our own interpreter and script)
4858:+NEEDS_FOLDER_TEST = "def test_needs_folder():\n    import demo_only.fakes  # noqa: F401\n"
4928:+    subprocess.run(["git", "-C", str(repo), "add", "src/pkg/added.py"], check=True)  # noqa: S603, S607
5022:+    subprocess.run(  # noqa: S603
5023:+        ["git", "-C", str(repo), "update-index", "--add", "--cacheinfo", f"160000,{sha},{rel}"],  # noqa: S607
5141:+    subprocess.run(  # noqa: S603
5142:+        ["git", "-C", str(repo), "add", "src/pkg/pipe.py", "elsewhere/pipe.py"],  # noqa: S607
5569:+            subprocess.run(["chown", "-R", "65534:65534", str(base)], check=True)  # noqa: S603, S607
5571:+        done = subprocess.run(  # noqa: S603
5581:+        subprocess.run(["chmod", "-R", "u+rwx", str(base)], check=False)  # noqa: S603, S607
5933:+        return real_run(*a, **kw)  # type: ignore[call-overload]
5937:+    mod.subprocess.run = watch  # type: ignore[assignment]
5941:+        mod.subprocess.run = real_run  # type: ignore[assignment]
7245:+        _b("demo", [3])  # type: ignore[list-item]
7261:+    rng = random.Random(20261112)  # noqa: S311 - a seeded test generator, not a secret
7352:+    rng = random.Random(20261112)  # noqa: S311 - a seeded test generator, not a secret
7393:+    exec("from hadavin_sdk.mode_banner import *", star)  # noqa: S102 - the public surface, a fixed string
7426:+    out = subprocess.run(  # noqa: S603 (fixed argument list, no shell)
7427:+        ["node", str(PROBE), str(JS), arg, scenario],  # noqa: S607
7469:+}  # fmt: skip
7515:+    real = {"mode": "pilot", "tone": "real", "tag": "PILOT", "text": "Real services: CRM.", "standins": "", "real": ["CRM"], "stand_ins": []}  # fmt: skip
7516:+    quiet = {"mode": "pilot", "tone": "quiet", "tag": "PILOT", "text": "None.", "standins": "", "real": [], "stand_ins": [], "overridden": []}  # fmt: skip
7605:+    }  # fmt: skip
7754:+    rng = random.Random(20261113)  # noqa: S311 - a seeded test generator, not a secret
7880:+        mb.banner_from_config(cfg, overridden=())  # type: ignore[call-arg]
7882:+        mb._services_in(cfg)  # type: ignore[call-arg]
8114:+        }  # fmt: skip
8160:+    except Exception as exc:  # noqa: BLE001 - reported with its type, so the failing line names the case
8236:+    )  # fmt: skip
8246:+        except Exception:  # noqa: BLE001 - a malformed url that raises elsewhere is refused all the same
8337:+        mb.banner_or_unconfirmed(good)  # type: ignore[call-arg]
8402:+    )  # fmt: skip
8594:+]  # fmt: skip
8603:+]  # fmt: skip
8618:+    )  # fmt: skip
8628:+    except Exception:  # noqa: BLE001 - any refusal is a refusal
8661:+        mb._clean_names("real_services", ["a"], {})  # type: ignore[call-arg]
8831:+        mb._tool_hosts_leave({"agent": (x for x in ())})  # type: ignore[dict-item]
9226:+        mb.banner_from_config(_demo_config(), tool_specs={})  # type: ignore[call-arg]
9234:+        mb.banner_or_unconfirmed(_demo_config(), tool_specs={})  # type: ignore[call-arg]
9346:+    out = subprocess.run(  # noqa: S603 (fixed argument list, no shell)
9347:+        ["node", str(PROBE.with_name("mode_banner_blank_probe.js")), str(JS)],  # noqa: S607
9748:+        mb._banner_for("demo", real_services=[], stand_ins=[])  # type: ignore[call-arg]
10490:+        ["git", "ls-files", "-z"],  # noqa: S607 - git from PATH, fixed argv; -z: exact names, no quoting
10674:+)  # fmt: skip
10947:+    done = subprocess.run(  # noqa: S603 (fixed argument list, no shell)
10948:+        ["git", "-C", str(repo), *GIT_NO_USER_EXCLUDES, "ls-files", "-z", *flags],  # noqa: S607
10961:+    done = subprocess.run(  # noqa: S603 (fixed argument list, no shell)
10962:+        ["git", "-C", str(repo), "ls-files", "-s", "-z", "--cached"],  # noqa: S607
11610:+            checked = subprocess.run(  # noqa: S603 (our own interpreter; arguments are a list, no shell)
11621:+        return subprocess.run(  # noqa: S603 (our own interpreter; arguments are a list, no shell)
11726:+    listing = subprocess.run(cmd, capture_output=True, check=True).stdout  # noqa: S603
```

## 3. Mutants (tests/banner_mutants.py, mode of the table)

How the table runs (from the file itself): each row is a `Mutant` that reverts ONE guard in a temp copy; `python tests/banner_mutants.py <text>...` runs only rows whose name contains one of the texts (no text = all 317 rows). The runner works on temp copies (tools/mutation_runner.py), runs an unmutated baseline per call, and a row is good only if the pinned test fails first with the expected message fragment (a CRASH row is one that is allowed to crash, with its exception type checked). I passed full row names, in 10 slices of 12 (last slice 4), two slices at a time, each under 470 s. Selection (mutant_selection.json): ALL rows starting R11 (15), R10 (25), R9D (14), plus R7B2, R7F1, J1b (52 required rows) plus a random sample of 60 of the other 265 rows (random.Random(11).sample).

Result: 112 rows run; 109 KILLED, 3 CRASH (B5, B44, B62: rows declared allow_crash, each marked "ok" by the runner), 0 SURVIVED, 0 WRONG_REASON, 0 OTHER_TEST, 0 ERROR, 0 NO_TESTS. Every slice: "N of N good; problems: []", exit 0. `git status` in the worktree after all slices: clean (0 lines). Raw: mut-slice-00..09.log, mut-all-rows.txt.

The 52 required rows are the first part of this table in the order the runner listed them (J1b, R7B2, R7F1, R9D1..R9D14, R10..., R11...); the sample rows follow.

```
ok  KILLED       J1b an unconfirmed banner is painted as given even when its words are not the not-confirmed words  [test_pin_an_unconfirmed_banner_that_also_lists_real_servic
ok  KILLED       R7B2 the timeout parameter is dropped from the not-connectivity list  [test_the_not_connectivity_list_is_exactly_the_parameters_tha]
ok  KILLED       R7F1 a key= or token= value in git's message is shown  [test_pin_git_message_hides_names_with_key_or_token_but_shows]
ok  KILLED       R9D1 a bearer token of 11 characters is hidden  [test_a_bearer_token_of_11_and_a_basic_token_of_7_stay_visibl]
ok  KILLED       R9D2 a basic token of 7 characters is hidden  [test_a_bearer_token_of_11_and_a_basic_token_of_7_stay_visibl]
ok  KILLED       R9D3 the bearer token class is wider than the core's  [test_the_guard_bearer_and_basic_patterns_are_the_text_of_the]
ok  KILLED       R9D4 a bare bearer scheme word is not hidden  [test_a_bare_scheme_word_hides_what_the_core_hides_and_no_mor]
ok  KILLED       R9D5 a bare basic scheme word is not hidden  [test_a_bare_scheme_word_hides_what_the_core_hides_and_no_mor]
ok  KILLED       R9D6 the Authorization header is read as one word without a space after the colon (a space after the colon hides nothing)  [test_after_an_authorization_header
ok  KILLED       R9D7 a quoted value is read as an unquoted one  [test_a_name_value_pair_hides_quoted_and_odd_values_and_the_w]
ok  KILLED       R9D8 an inner quote or ampersand ends an unquoted value  [test_a_name_value_pair_hides_quoted_and_odd_values_and_the_w]
ok  KILLED       R9D9 the name pwd is not a secret name  [test_a_name_value_pair_hides_quoted_and_odd_values_and_the_w]
ok  KILLED       R9D10 the name auth is not a secret name  [test_a_name_value_pair_hides_quoted_and_odd_values_and_the_w]
ok  KILLED       R9D11 the name credential is not a secret name  [test_a_name_value_pair_hides_quoted_and_odd_values_and_the_w]
ok  KILLED       R9D12 the name passwd is not a secret name  [test_a_name_value_pair_hides_quoted_and_odd_values_and_the_w]
ok  KILLED       R9D13 a url password is hidden only up to the first at sign  [test_url_credentials_are_hidden_up_to_the_last_at_sign_whate]
ok  KILLED       R9D14 the name check reads the whole line for every equals sign  [test_pin_the_masker_costs_time_in_proportion_to_the_line_and]
ok  KILLED       R10A1 the sealed value drops the references of its parts  [test_the_seal_keeps_a_replaced_part_alive_so_its_number_cann]
ok  KILLED       R10A2 the services the banner reads are not compared with the sealed ones  [test_the_address_of_a_system_changed_after_build_reads_uncon]
ok  KILLED       R10A3 the tool specs of each agent are not read as parts  [test_a_tool_spec_without_a_host_deleted_after_build_reads_un]
ok  KILLED       R10A4 the sources of the config are not read as parts  [test_a_config_source_replaced_after_build_reads_unconfirmed]
ok  KILLED       R10A5 the functions of the toolbox are not read as parts  [test_a_toolbox_function_or_spec_swapped_after_build_reads_un]
ok  KILLED       R10A6 the specs of the toolbox are not read as parts  [test_a_toolbox_function_or_spec_swapped_after_build_reads_un]
ok  KILLED       R10A7 the action contracts of the registry are not read as parts  [test_an_action_contract_replaced_or_added_after_build_reads_]
ok  KILLED       R10A8 an app can be deep-copied again  [test_a_deep_copy_of_an_app_that_could_be_copied_is_refused_a]
ok  KILLED       R10A9 a banner error is logged on every call, not once  [test_a_banner_error_is_logged_once_at_warning_level_with_the]
ok  KILLED       R10A10 the unreadable parts of an app are not logged  [test_a_banner_error_is_logged_once_at_warning_level_with_the]
ok  KILLED       R10A11 an error that stops the banner is not logged  [test_an_error_in_the_services_or_in_the_banner_is_logged_at_]
ok  KILLED       R10A12 the banner error is logged at debug level  [test_a_banner_error_is_logged_once_at_warning_level_with_the]
ok  KILLED       R10B1 the page paints demo or quiet when overridden is missing or null  [test_a_banner_without_overridden_is_not_painted_as_demo_or_q]
ok  KILLED       R10B2 the page drops the names of an unconfirmed banner that was reworded  [test_a_reworded_not_confirmed_text_is_painted_by_the_page_as]
ok  KILLED       R10B3 the page paints the tag of an unconfirmed banner as given  [test_pin_a_forged_tag_on_an_unconfirmed_banner_is_painted_as]
ok  KILLED       R10B4 the page paints the mode of an unconfirmed banner as given  [test_a_reworded_not_confirmed_text_is_painted_by_the_page_as]
ok  KILLED       R10C1 a bearer token after a secret-looking name is hidden by the pair step first  [test_a_bearer_token_after_a_secret_looking_name_is_hidden_wi]
ok  KILLED       R10C2 a basic token after a secret-looking name is hidden by the pair step first  [test_a_basic_token_after_a_secret_looking_name_is_hidden_wit]
ok  KILLED       R10F1 the copy sets the file mode to nothing (fchmod)  [test_pin_a_copy_keeps_the_file_mode_when_os_has_fchmod]
ok  KILLED       R10F2 the copy sets the file mode to nothing (chmod)  [test_a_copy_keeps_the_file_mode_where_os_has_no_fchmod]
ok  KILLED       R10F3 an entry swapped during the copy is a bare OSError  [test_an_entry_swapped_between_the_check_and_the_copy_is_refu]
ok  KILLED       R10F4 a loader behind a folder that became a link is read through it  [test_a_loader_behind_a_folder_that_became_a_link_is_a_hit]
ok  KILLED       R10F5 an exempt file behind a folder that became a link is read through it  [test_an_exempt_file_behind_a_folder_that_became_a_link_is_a_]
ok  KILLED       R10F6 the copy-run marker behind a folder that became a link is read through it  [test_the_copy_run_marker_behind_a_folder_that_became_a_link_]
ok  KILLED       R10F7 a chain of links that is too long is called only a loop  [test_pin_a_chain_of_45_links_is_a_hit_and_the_rule_text_name]
ok  KILLED       R11A1 a named container that is missing is skipped without a word  [test_a_named_container_that_is_missing_stops_the_reading_and]
ok  KILLED       R11A2 the agents of the registry are not read as parts  [test_a_replaced_agent_entry_after_build_reads_unconfirmed]
ok  KILLED       R11A3 the principals of the registry are not read as parts  [test_a_replaced_principal_entry_after_build_reads_unconfirme]
ok  KILLED       R11A4 the chains of the registry are not read as parts  [test_a_replaced_chain_entry_after_build_reads_unconfirmed]
ok  KILLED       R11A5 the systems of the config are not read as parts  [test_a_replaced_system_entry_after_build_reads_unconfirmed]
ok  KILLED       R11A6 the tool manifests of the registry are not read as parts  [test_a_replaced_tool_manifest_of_an_agent_after_build_reads_]
ok  KILLED       G26 a NUL byte anywhere in the file makes it binary  [test_a_text_file_renamed_to_a_binary_ending_is_read_and_a_re]
ok  KILLED       G27 a listed phrase may stand beside a dash  [test_a_listed_phrase_is_matched_in_its_own_case_and_not_besi]
ok  KILLED       G29 a listed phrase is matched in any case  [test_a_listed_phrase_is_matched_in_its_own_case_and_not_besi]
ok  KILLED       R7D1 the page paints an unconfirmed text that only starts with the own words  [test_a_forged_unconfirmed_text_is_not_painted_only_the_exact]
ok  KILLED       R7E5 a file of only the RAR mark and NUL bytes is not a RAR kind  [test_pin_a_file_that_is_only_the_rar_mark_and_nul_bytes_is_a]
ok  KILLED       R7E10 the repository path is not masked in git's message  [test_a_failed_git_call_shows_the_first_line_of_gits_own_mess]
ok  KILLED       R9E3 the compiled Python upper end ignores the running interpreter  [test_the_compiled_python_range_follows_the_running_interpret]
ok  KILLED       R9E7 a folder swapped for a link on the way to a listed file is read through  [test_a_tracked_file_whose_parent_folder_became_a_link_is_a_l]
ok  KILLED       R11A7 the seal accepts any value, not only the names build worked out  [test_a_plain_tuple_cannot_seal_an_app_and_a_sealed_app_canno]
ok  KILLED       R11B1 an app the seal cannot read stops the build  [test_a_config_the_banner_cannot_read_does_not_stop_build_and]
ok  KILLED       R11B2 an app the seal cannot read is not logged  [test_a_config_the_banner_cannot_read_does_not_stop_build_and]
ok  KILLED       R11C1 the name before an equals sign is looked for from the start of the line  [test_pin_the_masker_reads_each_character_a_bounded_number_of]
ok  CRASH        B5 made-up data is claimed in the demo stage next to a real service  [test_a_real_service_is_named_and_made_up_data_is_never_claim]
ok  KILLED       B10e the stage of the config is taken from nowhere (always demo)  [test_banner_from_config_reads_the_stage_and_both_lists_from_]
ok  KILLED       J7 any mode string is accepted  [test_pin_a_banner_that_contradicts_itself_is_not_painted_as_]
ok  KILLED       G3 the loader files are not exempt  [test_a_loader_may_name_the_folder_once_only_and_may_not_hold]
ok  KILLED       G22 a listed phrase that nothing holds is not stale  [test_a_listed_phrase_that_no_product_file_holds_is_a_stale_h]
ok  KILLED       B58 text after a bracketed address is allowed  [test_a_port_that_is_not_digits_or_text_after_a_bracket_is_no]
ok  KILLED       G46 a bzip2 file is not recognised  [test_a_compiled_or_packed_file_is_refused_by_its_first_bytes]
ok  KILLED       G56 UTF-32 little-endian is not searched  [test_the_name_is_found_as_utf32_in_a_binary_and_in_a_text_en]
ok  KILLED       G71 the byte patterns are built again for each file  [test_the_byte_patterns_are_built_once_for_a_whole_scan]
ok  KILLED       N9 a banner with a blank tag or text may leave  [test_a_tag_or_text_of_only_white_space_is_not_painted_on_the]
ok  KILLED       R7A3 overridden has a default again in banner_from_config  [test_pin_banner_from_config_has_no_default_for_overridden]
ok  KILLED       R7A4 the not-known message of overridden=None names something else  [test_pin_overridden_none_says_it_is_not_known_and_gives_the_]
ok  KILLED       B3 a name is checked by its start only  [test_a_name_that_could_change_the_sentence_is_refused]
ok  KILLED       B9b an unnamed key is shown as the bare key  [test_a_key_without_a_shown_name_is_read_as_component_and_the]
ok  KILLED       J8d tone quiet is accepted with a real service listed  [test_pin_a_banner_that_contradicts_itself_is_not_painted_as_]
ok  KILLED       B33 a tool host on this machine is counted as real  [test_tool_hosts_on_this_machine_or_none_keep_the_demo_banner]
ok  KILLED       B47 a name followed by a dot and a letter is matched  [test_pin_names_in_follows_the_table]
ok  KILLED       B56 an empty name is found in any text  [test_an_empty_name_is_never_in_a_text]
ok  KILLED       G51 a .gz ending is not refused  [test_every_archive_ending_is_refused_like_a_zip]
ok  KILLED       G53 a .tar ending is not refused  [test_every_archive_ending_is_refused_like_a_zip]
ok  KILLED       G60 a control character in a hit is printed as it is  [test_a_hit_is_printed_with_control_characters_escaped_and_ne]
ok  KILLED       G61 a format character in a hit is printed as it is  [test_a_hit_is_printed_with_control_characters_escaped_and_ne]
ok  KILLED       G81 a file with an allowed ending may hold any content  [test_a_foreign_file_with_a_picture_font_or_pdf_ending_is_a_h]
ok  KILLED       G94 a ttf file that starts with true is refused  [test_webp_ttf_and_otf_with_wrong_first_bytes_are_hits_and_wi]
ok  KILLED       B3e a key that is not text is accepted  [test_a_service_key_that_is_not_text_is_refused]
ok  KILLED       B4 a real service is also listed as a stand-in  [test_a_service_that_is_both_real_and_listed_as_stand_in_coun]
ok  KILLED       B9 the names from the caller are ignored  [test_names_come_from_the_caller_and_repeats_are_shown_once_i]
ok  KILLED       G9c a folder that is not a git checkout is scanned as empty  [test_the_scan_refuses_a_folder_that_is_not_a_git_checkout]
ok  KILLED       B24 a value that is not text is read as this machine  [test_a_demo_config_that_can_reach_beyond_this_machine_is_not]
ok  CRASH        B44 a config field that is missing reads as empty  [test_a_config_that_lost_an_endpoint_field_raises_and_is_neve]
ok  KILLED       J18 the page stops at the first partial match  [test_pin_the_page_and_python_agree_on_every_row_of_the_name_]
ok  KILLED       G45 a gzip file is not recognised  [test_a_compiled_or_packed_file_is_refused_by_its_first_bytes]
ok  KILLED       G47 an xz file is not recognised  [test_a_compiled_or_packed_file_is_refused_by_its_first_bytes]
ok  KILLED       N1 tool modules are read without the collection check  [test_a_generator_for_tool_modules_is_refused_like_egress_hos]
ok  KILLED       R7A1 an App made by hand records no overrides, as if build had been given none  [test_an_app_made_by_hand_gives_the_unconfirmed_banner_not_th]
ok  KILLED       R9C1 the guard docstring leaves a first-byte kind out  [test_the_module_docstring_lists_exactly_the_kinds_of_first_b]
ok  KILLED       B2 a bare string is read letter by letter  [test_pin_a_bare_string_dict_set_or_non_list_is_refused_not_r]
ok  KILLED       B10f the real list is derived from the prod gate table again  [test_a_kind_added_to_the_prod_gate_table_later_still_reads_a]
ok  KILLED       G3c a loader is not checked for fake ids  [test_a_loader_may_name_the_folder_once_only_and_may_not_hold]
ok  KILLED       G9 files that git does not list yet are not scanned  [test_a_file_is_scanned_whether_it_is_added_to_git_or_not]
ok  KILLED       G20 the copy run without a package to check is accepted  [test_the_copy_run_without_a_package_to_check_is_refused]
ok  KILLED       J17 the page lets a prefix of another word count as the name  [test_pin_the_page_and_python_agree_on_every_row_of_the_name_]
ok  KILLED       G38 an exempt submodule is still reported as a submodule  [test_a_submodule_that_is_listed_as_exempt_is_not_a_second_hi]
ok  KILLED       B53 a tool spec without a hosts list is read as no hosts  [test_a_tool_spec_without_hosts_or_with_odd_hosts_raises_nami]
ok  KILLED       G57 UTF-32 big-endian is not searched  [test_the_name_is_found_as_utf32_in_a_binary_and_in_a_text_en]
ok  KILLED       G63 a line separator in a hit is printed as it is  [test_a_hit_is_printed_with_control_characters_escaped_and_ne]
ok  KILLED       G97 an exempt file may be a binary  [test_an_exempt_file_that_is_a_binary_is_a_hit_by_kind]
ok  KILLED       R7E9 the first line of git's own message is not shown  [test_a_failed_git_call_shows_the_first_line_of_gits_own_mess]
ok  KILLED       G16 the guard's own files are not exempt  [test_the_exempt_files_are_exactly_the_guard_itself_and_each_]
ok  KILLED       B36 banner_from_config drops the tool specs  [test_the_tools_of_a_real_registry_are_what_the_banner_reads]
ok  CRASH        B62 banner_or_unconfirmed lets the error out  [test_banner_or_unconfirmed_gives_the_banner_or_the_not_confi]
ok  KILLED       G93 a webp file is recognised by RIFF alone  [test_webp_ttf_and_otf_with_wrong_first_bytes_are_hits_and_wi]
```

## 4. Fail-before (new tests copied onto old src; python 3.13)

Method: for each old head a detached worktree; every file under tests/ that differs between the old head and 06ed4b4c was copied over from the new head (cdbe: 5 files, dd82: 6 files); src/, tools/, templates/ stay old. Files run: test_mode_banner, test_demo_only_guard, test_demo_only_guard_ci, test_changelog_numbers, test_banner_mutant_table (349 tests). Logs: failbefore-cdbe.log, failbefore-dd82.log, junit-*.xml, failbefore-analysis.txt (generated by analyse.py).

| head | failed | passed | pytest exit |
|---|---|---|---|
| 06ed4b4c (control) | 0 | 349 | 0 |
| cdbe1445 | 34 | 315 | 1 |
| dd827d79 | 52 | 297 | 1 |

test_pin_* tests: 51 on the new head. Pins that pass on cdbe1445: 51 of 51. Pins that do NOT pass on dd827d79: 7 (all 7 carry the label "on dd827d79 it FAILS; on cdbe1445 it passes", so these are pins of the batch 10 code, consistent with their labels): the_page_and_python_agree_on_a_missing_or_null_overridden_for_demo_and_quiet, an_unconfirmed_banner_with_other_tag_or_text_is_painted_with_the_pages_words_and_the_names, a_real_built_app_lists_every_named_container_entry_in_its_connected_parts, a_banner_error_is_logged_once_at_warning_level_whatever_the_name_of_the_log_helper, a_bearer_token_of_11_characters_stays_visible_as_on_main, the_masker_hides_the_scheme_word_and_the_token_of_a_bearer_and_a_basic_line, a_chain_of_45_links_is_a_hit_and_the_rule_text_names_both_causes.

Non-pin tests: 34 fail on cdbe1445 (all of the 34 failures are non-pin); 45 non-pin fail on dd827d79. Non-pin tests that PASS on old code and carry a fail-before label: 12 on cdbe1445 (every one labelled "on cdbe1445 it passes", consistent), 1 on dd827d79 (test_a_copy_keeps_the_file_mode_where_os_has_no_fchmod, labelled passes/passes; see item 3 at the top).
Label vs result: 86 tests carry a fail-before comment; parsed every "on dd827d79 it FAILS|passes" and "on cdbe1445 it FAILS|passes" claim against the runs: 0 mismatches in the claim itself. Exceptions: the wording contradiction of item 3, and the 4 unlabelled tests of item 5.
Of the failures, 25 (cdbe) and 24 (dd82) are `ImportError: cannot import name '_Given'`.

First failing line per failing test (from junit; the new head fails nothing):

```
-- cdbe
   test_an_app_copied_or_changed_after_build_gives_the_unconfirmed_banner :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_every_replaced_connected_part_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_a_source_value_replaced_or_changed_in_place_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_the_seal_keeps_a_replaced_part_alive_so_its_number_cannot_be_reused :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_a_tampered_or_stub_app_gives_the_unconfirmed_banner_and_never_raises :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_copies_of_a_built_app_which_keep_the_same_parts_stay_known_and_the_others_do_not :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_the_recorded_names_cannot_be_laundered :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_a_normal_production_tick_keeps_its_banner :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_an_object_first_set_on_a_part_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_a_tool_spec_deleted_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_a_tool_spec_without_a_host_deleted_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_the_address_of_a_system_changed_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_config_sources_cleared_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_a_config_source_replaced_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_a_toolbox_function_or_spec_swapped_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_an_action_contract_replaced_or_added_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_an_error_in_the_services_or_in_the_banner_is_logged_at_warning_level_too :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_a_named_container_that_is_missing_stops_the_reading_and_names_it :: AssertionError: config.systems was missing and the parts were read all the same
   test_an_app_sealed_while_a_container_is_missing_reads_unconfirmed_and_build_goes_on :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_a_plain_tuple_cannot_seal_an_app_and_a_sealed_app_cannot_be_given_a_new_answer :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_a_hand_made_app_is_unconfirmed_even_after_a_stray_seal_call :: AssertionError: assert 'demo' == 'unconfirmed' /    /   - unconfirmed /   + demo
   test_the_banner_of_a_real_app_is_the_same_after_an_agent_run :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_a_config_the_banner_cannot_read_does_not_stop_build_and_reads_unconfirmed :: AssertionError: a tool spec without hosts: build stopped on it: tool 't' of agent 'a' has no `hosts` list of text: the banner cannot say where it reaches
   test_a_replaced_agent_entry_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_a_replaced_principal_entry_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_a_replaced_chain_entry_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_a_replaced_system_entry_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_a_replaced_tool_manifest_of_an_agent_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-cdbe/src/hadavin_sdk/app.py)
   test_the_changelog_says_the_masker_has_as_many_passes_as_the_code_lists :: AssertionError: the CHANGELOG does not state a number of masker passes / assert []
   test_the_changelog_limits_of_the_bearer_and_basic_rules_are_the_numbers_of_their_patterns :: AssertionError: assert None /  +  where None = <function search at 0x7ff429dbe2a0>('\\bbearer needs 12 characters, basic 8\\b', '# Changelog\n\n## Unreleased\n\n###
   test_the_three_equal_listings_and_the_one_superset_are_the_files_the_changelog_names :: AssertionError: assert None /  +  where None = <function search at 0x7ff429dbe2a0>('\\bThree listings of the tracked files\\b', '# Changelog\n\n## Unreleased\n\n### Upgr
   test_the_changelog_pyc_range_is_the_rule_of_the_code_with_the_numbers_of_its_two_interpreters :: AssertionError: assert None /  +  where None = <function search at 0x7ff429dbe2a0>('\\b4531 on Python 3\\.12, 4627 on Python 3\\.14\\b', '# Changelog\n\n## Unre
   test_every_row_of_the_table_has_its_own_label_and_a_search_text_found_exactly_once :: AssertionError: assert [('R7B2 the t... times'), ...] == [] /    /   Left contains 12 more items, first extra item: ('R7B2 the timeout parameter is dropped from the not-co
   test_the_changelog_states_the_row_count_of_the_table :: AssertionError: the CHANGELOG does not say that the table has 317 rows / assert 'the table has 317 rows' in '# Changelog\n\n## Unreleased\n\n### Upgrade steps\n- **Breaking: the first stage 
-- dd82
   test_pin_an_unconfirmed_banner_with_other_tag_or_text_is_painted_with_the_pages_words_and_the_names :: AssertionError: painted odd unconfirmed {'mode': 'demo', 'tone': 'unconfirmed', 'tag': 'UNCONFIRMED', 'text': 'Every record here is made-up demo data.', '
   test_an_app_copied_or_changed_after_build_gives_the_unconfirmed_banner :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_a_forged_unconfirmed_text_is_not_painted_only_the_exact_words_and_a_note_built_by_the_page :: AssertionError: painted a forged text 'The mode of this system could not be confirmed. Treat everything here as real. Every record here is made-up demo data.'
   test_every_replaced_connected_part_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_a_source_value_replaced_or_changed_in_place_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_the_seal_keeps_a_replaced_part_alive_so_its_number_cannot_be_reused :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_a_tampered_or_stub_app_gives_the_unconfirmed_banner_and_never_raises :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_copies_of_a_built_app_which_keep_the_same_parts_stay_known_and_the_others_do_not :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_a_deep_copy_of_an_app_that_could_be_copied_is_refused_as_well :: AssertionError: an app of plain parts was deep-copied
   test_the_recorded_names_cannot_be_laundered :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_a_normal_production_tick_keeps_its_banner :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_an_object_first_set_on_a_part_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_a_reworded_not_confirmed_text_is_painted_by_the_page_as_its_english_fallback_with_the_names :: AssertionError: the names of the overrides were not shown: [{'cls': 'mode-banner__tag', 'text': 'UNCONFIRMED'}, {'cls': 'mode-banner__text', 'text': ' The mo
   test_a_tool_spec_deleted_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_a_tool_spec_without_a_host_deleted_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_the_address_of_a_system_changed_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_config_sources_cleared_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_a_config_source_replaced_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_a_toolbox_function_or_spec_swapped_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_an_action_contract_replaced_or_added_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_a_banner_error_is_logged_once_at_warning_level_with_the_exception_type :: AttributeError: <module 'hadavin_sdk.app' from '/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py'> has no attribute '_WARNED'
   test_an_error_in_the_services_or_in_the_banner_is_logged_at_warning_level_too :: AttributeError: <module 'hadavin_sdk.app' from '/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py'> has no attribute '_WARNED'
   test_a_banner_without_overridden_is_not_painted_as_demo_or_quiet_by_the_page :: AssertionError: painted demo with overridden missing / assert (False is False and 'demo' == 'unconfirmed' /    /   - unconfirmed /   + demo)
   test_pin_the_page_and_python_agree_on_a_missing_or_null_overridden_for_demo_and_quiet :: AssertionError: the page painted demo with overridden missing / assert 'demo' == 'unconfirmed' /    /   - unconfirmed /   + demo
   test_pin_a_real_built_app_lists_every_named_container_entry_in_its_connected_parts :: AssertionError: config.systems['fixture-records'] is not among the connected parts / assert "config.systems['fixture-records']" in {'approvals', 'approvals.audit', 'approv
   test_a_named_container_that_is_missing_stops_the_reading_and_names_it :: AssertionError: config.systems was missing and the parts were read all the same
   test_an_app_sealed_while_a_container_is_missing_reads_unconfirmed_and_build_goes_on :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_a_plain_tuple_cannot_seal_an_app_and_a_sealed_app_cannot_be_given_a_new_answer :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_a_hand_made_app_is_unconfirmed_even_after_a_stray_seal_call :: AssertionError: assert 'demo' == 'unconfirmed' /    /   - unconfirmed /   + demo
   test_the_banner_of_a_real_app_is_the_same_after_an_agent_run :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_a_config_the_banner_cannot_read_does_not_stop_build_and_reads_unconfirmed :: AttributeError: module 'hadavin_sdk.app' has no attribute '_services_in'
   test_pin_a_banner_error_is_logged_once_at_warning_level_whatever_the_name_of_the_log_helper :: AssertionError: logged below warning: ['DEBUG', 'DEBUG'] / assert False /  +  where False = all(<generator object test_pin_a_banner_error_is_logged_once_at_warnin
   test_a_replaced_agent_entry_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_a_replaced_principal_entry_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_a_replaced_chain_entry_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_a_replaced_system_entry_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_a_replaced_tool_manifest_of_an_agent_after_build_reads_unconfirmed :: ImportError: cannot import name '_Given' from 'hadavin_sdk.app' (/home/user/build/ER-pdbanner11-dd82/src/hadavin_sdk/app.py)
   test_a_bearer_token_after_a_secret_looking_name_is_hidden_with_its_scheme_word :: AssertionError: authorization=Bearer: the token stayed visible: 'fatal: authorization=<hidden> a1a1a1a1a1a1a1a1a1a1' / assert 'a1a1a1a1a1a1a1a1a1a1' not in 'fatal: auth...a1a1
   test_a_basic_token_after_a_secret_looking_name_is_hidden_with_its_scheme_word :: AssertionError: authorization=Basic: the token stayed visible: 'fatal: authorization=<hidden> b2b2b2b2b2b2' / assert 'b2b2b2b2b2b2' not in 'fatal: auth...b2b2b2b2b2b2' /    /  
   test_pin_a_bearer_token_of_11_characters_stays_visible_as_on_main :: AssertionError: a 12 character token stayed / assert 'c3c3c3c3c3c3' not in 'fatal: toke...c3c3c3c3c3c3' /    /   'c3c3c3c3c3c3' is contained here: /     fatal: token=<hidden> c3c3c3c3c3c3 
   test_pin_the_masker_hides_the_scheme_word_and_the_token_of_a_bearer_and_a_basic_line :: AssertionError: assert 'fatal: autho...1a1a1a1a1a1a1' == 'fatal: autho...den> <hidden>' /    /   - fatal: authorization=<hidden> <hidden> /   + fatal: authorization=<hid
   test_an_entry_swapped_between_the_check_and_the_copy_is_refused_in_words_never_a_traceback :: AssertionError: a bare OSError came out of the copy: OSError(22, 'Invalid argument')
   test_a_loader_behind_a_folder_that_became_a_link_is_a_hit :: AssertionError: a loader behind a link was read through it: ['src/pkg: symlink-in-product-root', 'src/pkg/__init__.py: symlink-in-product-root', 'src/pkg/loader.py: symlink-in-product-root']
   test_an_exempt_file_behind_a_folder_that_became_a_link_is_a_hit :: AssertionError: an exempt file behind a link was read through it: ['src/pkg: symlink-in-product-root', 'src/pkg/__init__.py: symlink-in-product-root'] / assert False /  +  where False = any(
   test_the_copy_run_marker_behind_a_folder_that_became_a_link_is_a_hit :: AssertionError: the marker behind a link was read through it: [] / assert False /  +  where False = any(<generator object test_the_copy_run_marker_behind_a_folder_that_became_a_link_is_
   test_pin_a_chain_of_45_links_is_a_hit_and_the_rule_text_names_both_causes :: AssertionError: a chain of 45 links was not named as a chain: ['docs/link40: symlink-loop (a loop of links cannot be followed)', 'docs/link41: symlink-loop (a loop of links cannot 
   test_the_changelog_says_the_masker_has_as_many_passes_as_the_code_lists :: AssertionError: the CHANGELOG does not state a number of masker passes / assert []
   test_the_changelog_limits_of_the_bearer_and_basic_rules_are_the_numbers_of_their_patterns :: AssertionError: assert None /  +  where None = <function search at 0x7ff5a5f4e2a0>('\\bbearer needs 12 characters, basic 8\\b', '# Changelog\n\n## Unreleased\n\n###
   test_the_three_equal_listings_and_the_one_superset_are_the_files_the_changelog_names :: AssertionError: assert None /  +  where None = <function search at 0x7ff5a5f4e2a0>('\\bThree listings of the tracked files\\b', '# Changelog\n\n## Unreleased\n\n### Upgr
   test_the_changelog_pyc_range_is_the_rule_of_the_code_with_the_numbers_of_its_two_interpreters :: AssertionError: assert None /  +  where None = <function search at 0x7ff5a5f4e2a0>('\\b4531 on Python 3\\.12, 4627 on Python 3\\.14\\b', '# Changelog\n\n## Unre
   test_every_row_of_the_table_has_its_own_label_and_a_search_text_found_exactly_once :: AssertionError: assert [('J1b an unc... times'), ...] == [] /    /   Left contains 43 more items, first extra item: ('J1b an unconfirmed banner is painted as given even wh
   test_the_changelog_states_the_row_count_of_the_table :: AssertionError: the CHANGELOG does not say that the table has 317 rows / assert 'the table has 317 rows' in '# Changelog\n\n## Unreleased\n\n### Upgrade steps\n- **Breaking: the first stage 
```

## 5. Hostile probes (loopback only, in-process, no network)

Script: /home/user/build/ER-pdbanner11-probe/probe.py (removed with the probe folder; its output is kept as probe-new.log). The app is the repo's own test fixture (fakes only), built with `build(..., secrets=FakeSecretProvider)` and sealed with no overrides, as the repo tests do (`_seal(_Given())`), then given one real tool host (api.example.com, a name that is not this machine) and one source of an unknown kind so that the untouched banner reads "real". Each tamper starts from a fresh app. "FLAG" = a real service is held while the banner claims made-up or quiet. Banner tone words: demo = made-up claim, quiet = nothing real, unconfirmed = could not be confirmed, real = names the services.

Flags in the banner and page rows: none (0). Flags in the masker rows: 4 (the 11 and 7 character limits).

| case | what the banner says / result | flag |
|---|---|---|
| control: plain app, nothing real | tone=demo real=[] text='Every record here is made-up demo data. Nothing here is set up to send data to real custom' |  |
| delete a tool spec from app.registry.tools | tone=unconfirmed real=[] text='The mode of this system could not be confirmed. Treat everything here as real.' |  |
| delete the whole agent entry from app.registry.tools | tone=unconfirmed real=[] text='The mode of this system could not be confirmed. Treat everything here as real.' |  |
| clear app.config.sources | tone=unconfirmed real=[] text='The mode of this system could not be confirmed. Treat everything here as real.' |  |
| replace a toolbox _fns entry | tone=unconfirmed real=[] text='The mode of this system could not be confirmed. Treat everything here as real.' |  |
| replace a toolbox specs entry | tone=unconfirmed real=[] text='The mode of this system could not be confirmed. Treat everything here as real.' |  |
| remove the toolbox container _fns (del __dict__) | tone=unconfirmed real=[] text='The mode of this system could not be confirmed. Treat everything here as real.' |  |
| rename the toolbox container _fns | tone=unconfirmed real=[] text='The mode of this system could not be confirmed. Treat everything here as real.' |  |
| rename registry.principals | tone=unconfirmed real=[] text='The mode of this system could not be confirmed. Treat everything here as real.' |  |
| config.systems set to None | tone=unconfirmed real=[] text='The mode of this system could not be confirmed. Treat everything here as real.' |  |
| call app._seal(()) (plain tuple) | tone=real real=['component read-sources', 'component tool-hosts'] text='Real services are connected: component read-sources, component tool-hosts. Data this syste' [tamper raised TypeError: an app is sealed only with the names that build worked out] |  |
| call app._seal(None) | tone=real real=['component read-sources', 'component tool-hosts'] text='Real services are connected: component read-sources, component tool-hosts. Data this syste' [tamper raised TypeError: an app is sealed only with the names that build worked out] |  |
| copy.deepcopy(app) | refused: TypeError |  |
| copy.copy(app) (same parts) | tone=real real=['component read-sources', 'component tool-hosts'] text='Real services are connected: component read-sources, component tool-hosts. Data this syste' |  |
| dataclasses.replace(app) | tone=unconfirmed real=[] text='The mode of this system could not be confirmed. Treat everything here as real.' |  |
| reworded words (made_up/nothing_sent) on tooled app | tone=real real=['component read-sources', 'component tool-hosts'] text='Real services are connected: component read-sources, component tool-hosts. Data this syste' |  |
| reworded real_connected without the word real (tooled app) | tone=real real=['component read-sources', 'component tool-hosts'] text='Fine: component read-sources, component tool-hosts. Data this system handles may be sent t' |  |
| reworded made_up with own reserved word on tooled app | tone=real real=['component read-sources', 'component tool-hosts'] text='Real services are connected: component read-sources, component tool-hosts. Data this syste' |  |
| reworded words on plain app | tone=demo real=[] text='All is well here. Nothing leaves.' |  |
| service name that holds the made-up words | tone=real real=['component read-sources', 'component tool-hosts'] text='Real services are connected: component read-sources, component tool-hosts. Data this syste' |  |
| page: demo-banner with `overridden` missing | shownTone=unconfirmed dataTone=unconfirmed hidden=False lines=['UNCONFIRMED', ' The mode of this system could not be confirmed. Treat everything here'] threw='' |  |
| page: demo-banner with `overridden` null | shownTone=unconfirmed dataTone=unconfirmed hidden=False lines=['UNCONFIRMED', ' The mode of this system could not be confirmed. Treat everything here'] threw='' |  |
| page: demo-banner with overridden=['llm'] (control) | shownTone=unconfirmed dataTone=unconfirmed hidden=False lines=['UNCONFIRMED', ' The mode of this system could not be confirmed. Treat everything here'] threw='' |  |
| page: quiet-banner with `overridden` missing | shownTone=unconfirmed dataTone=unconfirmed hidden=False lines=['UNCONFIRMED', ' The mode of this system could not be confirmed. Treat everything here'] threw='' |  |
| page: quiet-banner with `overridden` null | shownTone=unconfirmed dataTone=unconfirmed hidden=False lines=['UNCONFIRMED', ' The mode of this system could not be confirmed. Treat everything here'] threw='' |  |
| page: quiet-banner with overridden=['llm'] (control) | shownTone=unconfirmed dataTone=unconfirmed hidden=False lines=['UNCONFIRMED', ' The mode of this system could not be confirmed. Treat everything here'] threw='' |  |
| page: demo-banner with overridden=[] (control, should paint demo) | shownTone=demo dataTone=demo hidden=False lines=['DEMO', ' Every record here is made-up demo data. Nothing here is set up to sen', 'MADE-UP STAND-INS IN USE: component secrets, component store, componen'] threw='' |  |
| page: real banner with `overridden` missing | shownTone=real dataTone=real hidden=False lines=['DEMO', ' Real services are connected: component read-sources, component tool-h', 'Still stand-ins, not connected: component secrets, component store, co'] threw='' |  |
| page: real banner with `overridden` null | shownTone=real dataTone=real hidden=False lines=['DEMO', ' Real services are connected: component read-sources, component tool-h', 'Still stand-ins, not connected: component secrets, component store, co'] threw='' |  |
| page: demo tone + a real service listed | shownTone=unconfirmed dataTone=unconfirmed hidden=False lines=['UNCONFIRMED', ' The mode of this system could not be confirmed. Treat everything here'] threw='' |  |
| page: unconfirmed banner reworded text 'All good, made-up data.' | shownTone=unconfirmed dataTone=unconfirmed hidden=False lines=['UNCONFIRMED', ' The mode of this system could not be confirmed. Treat everything here'] threw='' |  |
| page: unconfirmed banner reworded tag 'DEMO' | shownTone=unconfirmed dataTone=unconfirmed hidden=False lines=['UNCONFIRMED', ' The mode of this system could not be confirmed. Treat everything here'] threw='' |  |
| page: reworded demo text (made-up sentence changed) on a real banner | shownTone=unconfirmed dataTone=unconfirmed hidden=False lines=['UNCONFIRMED', ' The mode of this system could not be confirmed. Treat everything here'] threw='' |  |
| guard mask: authorization=Bearer + 12 chars | in='authorization=Bearer aaaaaaaaaaaa' out='authorization=<hidden> <hidden>' |  |
| guard mask: authorization=Bearer + 20 chars | in='authorization=Bearer A1A1A1A1A1A1A1A1A1A1' out='authorization=<hidden> <hidden>' |  |
| guard mask: auth=Bearer + 12 chars | in='auth=Bearer bbbbbbbbbbbb' out='auth=<hidden> <hidden>' |  |
| guard mask: auth=Bearer + 11 chars | in='auth=Bearer bbbbbbbbbbb' out='auth=<hidden> bbbbbbbbbbb' | FLAG: token value visible |
| guard mask: secret=Basic + 8 chars | in='secret=Basic cccccccc' out='secret=<hidden> <hidden>' |  |
| guard mask: secret=Basic + 7 chars | in='secret=Basic ccccccc' out='secret=<hidden> ccccccc' | FLAG: token value visible |
| guard mask: token=Bearer + 12 chars | in='token=Bearer dddddddddddd' out='token=<hidden> <hidden>' |  |
| guard mask: token=Bearer + 11 chars | in='token=Bearer ddddddddddd' out='token=<hidden> ddddddddddd' | FLAG: token value visible |
| guard mask: token=Bearer + 11 chars, in a longer line | in='fatal: cannot read token=Bearer eeeeeeeeeee more' out='fatal: cannot read token=<hidden> eeeeeeeeeee more' | FLAG: token value visible |
| guard mask: Authorization: Bearer + 12 chars | in='Authorization: Bearer ffffffffffff' out='Authorization: <hidden>' |  |

Notes on the rows (facts only):
- Tampering after build (spec deleted, sources cleared, a toolbox function or spec replaced, a container removed or renamed, config.systems set to None, dataclasses.replace) gives the unconfirmed banner, never made-up/quiet. The text the person sees: "The mode of this system could not be confirmed. Treat everything here as real."
- app._seal(()) and app._seal(None) raise TypeError and leave the old seal; the banner stays "real" (correct for the untouched app). copy.deepcopy(app) is refused (TypeError). copy.copy(app) keeps the real banner.
- Reworded words: the Python side kept the real banner for a tooled app. A reworded banner for a plain app (nothing real) says the reworded text with tone demo.
- Page script (node, the repo's stand-in page): a demo or quiet banner with `overridden` missing or null is painted as unconfirmed; with `overridden: []` it is painted demo (control); a demo tone with a real service listed is painted unconfirmed; a reworded unconfirmed text or tag is painted with the page's own words. One logged line appeared in the run: "mode banner: the connected parts of the app could not be read (TypeError)" (warning, once).
- Masker (git messages): tokens of 12 or more (Bearer) and 8 or more (Basic) are hidden in all four name forms; the 11-character Bearer and 7-character Basic tokens stay visible (4 rows flagged). The Authorization: header form hides everything to the end of the line.

## 6. Cleanup

Worktrees ER-pdbanner11-new, -cdbe, -dd82, the 3.12 venv, the probe folder and temp folders under /tmp created by the probe were removed (see the lead report for the final listing). Raw logs stay in /home/user/build/evidence-raw/pdbanner-06ed4b4c/. This file is not added to git and not committed.
