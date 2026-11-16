# R7U-MUT results (merged tree-R7U), 69 mutants applied, 0 not run

## FAILED / NOT RUN / OPEN first
- WIDE RE-RUNS NOT DONE as ordered (stopped on the lead's order). Only partial wide runs happened (caps 100-300 s, `-x`, stopped at the cap, so only the first ~16 tests of the wide set ran, Z01 about 46%): X01, X05, X10, X11, X19, Y13, Y15, Y16, Y17, Y18, Y19 survived until the cap (no failure seen, set not finished); X12 and X14 were KILLED by wide (test_real_check_dry::test_dry_fakes_run_end_to_end), so they are not real survivors. Never reached in the wide phase at all: Y09, Y10, Y25, Y28, Z02, Z03, Z04, Z08, Z10, Z11, Z12, Z15, Z16.
- OPEN ROW Z01 (loopback.py:27, `startswith("[") and endswith("]")` -> `or`): survived the narrow set (111 tests: C, B b8, T t6/t12) and the partial wide run (300 s, about 46% of C+T+fake_bad_requests+bind_refusals+codeant_fakes+file_call_guard, no failure). Unjudged: it may be equivalent (a half bracket becomes an invalid address either way) or a missing test (inputs "[::1" and "::1]"). The same narrow-survivor pattern holds for Z02, Z03, Z04 (loopback.py:27-28), Z08 (`return host.strip()`), Z10 (fake_imap re-imports the refusal from demo_only.fake_smtp_tls), Z11 (fakes_server.py:247 refusal dropped), Z12 (fake_model_server.py:275 refusal dropped), Z15 (refusing_args.py:190 text replaced), Z16 (smtp_outbox.py:87 check inverted): all SURVIVED narrow; no wide result. Z11/Z12/Z16 look like real test gaps (refusal removed, nothing fails in the selected tests; the narrow set was only C, B-b8, T-t6/t12, so other test files may catch them: not checked).
- BASELINE: a full run of tests/test_r7u_a_findings.py on an untouched copy gave 1 failed (test_a4_the_readback_note_with_no_open_create_does_not_mention_one, line 407), 40 passed; alone it passes (34 s). Cause not found (lead notes it passed 6 single runs).
- NARROW test sets were small on purpose (time): a "SURVIVED narrow" row means only the named -k set did not fail. Mutants Z05 and Z14 made every test crash at start (rc=4, nothing ran): counted as caught, no test id.
- Slip: one `sed -i` was sent at /dev/null by mistake (it failed, nothing written). Two orphan crash_desk.py processes of my own pytest were killed by pid after the stop.

## Counts
KILLED 40, SURVIVED (narrow) 27 (2 of them killed by the partial wide run: X12, X14), CRASH 2, NOT-APPLIED 0.
Narrow results above come from out/R7U-MUT/res1.tsv and res2.tsv; wide from wide1.tsv, wide2.tsv, wide2a.tsv; raw tails raw-<id>.txt.

## Table (id | file:line | mutation | expected catcher | result | restored byte-equal)
Restore check: sha256 per mutant by the runner; after the kills of the runners the trees were restored from tree-R7U and compared (cmp / diff -rq): byte-equal, run_real_check.py sha256 prefix c33591dc6b2cad7d, loopback.py b6b1b1ff5f9b0137, same as tree-R7U.

| id | file:line | mutation | expected catcher | result | restored |
|---|---|---|---|---|---|
| X01 | scripts/run_real_check.py:997 | seam: 'if not all(type(v) is int and v >= 0 for v in valu' -> 'if suffix == ".hubspot.json" and not all(type(v) i' | test_r7u_a a2 / b7 (smtp file with bad value) | SURVIVED narrow (test_a2 and not real_run or b7_one_unreadable or b7_a_real_m); wide: SURVIVED-UNTIL-TIMEOUT 120s ['................'] | yes |
| X02 | scripts/run_real_check.py:1382 | seam: 'counter_known = counter_is_known(hub_read)\n    # t' -> 'counter_known = counter_is_known(hub_read) or smtp' | test_r7u_a a3 not-known | KILLED by test_a3_a_counter_that_is_not_known_is_in_the_result_and_the_result_is_not_ok | yes |
| X03 | scripts/run_real_check.py:1392 | seam: 'counter_check(counter_known, unseen, hub_stats))' -> 'counter_check(smtp_known, unseen, hub_stats))' | test_r7u_a a3 counter_check | KILLED by test_a3_a_counter_that_is_not_known_is_in_the_result_and_the_result_is_not_ok | yes |
| X04 | scripts/run_real_check.py:1389 | seam: 'hub_stats.get("create_open", 0) + hub_stats.get("c' -> 'hub_stats.get("create_open", 0) + hub_stats.get("c' | test_r7u_a a1c cap by leads | KILLED by test_a1c_a_create_with_no_known_outcome_counts_as_a_possible_contact_at_main_level[create_ | yes |
| X05 | scripts/run_real_check.py:1389 | seam: 'hub_stats.get("create_open", 0) + hub_stats.get("c' -> 'hub_stats.get("create_open", 0) * 2 + hub_stats.ge' | test_r7u_a a1c open term | SURVIVED narrow (a1c); wide: SURVIVED-UNTIL-TIMEOUT 120s ['.................'] | yes |
| X06 | scripts/run_real_check.py:1389 | seam: 'hub_stats.get("create_open", 0) + hub_stats.get("c' -> 'hub_stats.get("create_open", 0) + hub_stats.get("c' | test_r7u_a a1c (open used twice, unknown dropped) | KILLED by test_a1c_a_create_with_no_known_outcome_counts_as_a_possible_contact_at_main_level[create_ | yes |
| X07 | scripts/run_real_check.py:599 | seam: 'f", and {hub_stats.get(\'create_open\', 0)} create r' -> 'f", and {hub_stats.get(\'create_unknown\', 0)} creat' | test_r7u_a a4 note numbers swapped | KILLED by test_a4_the_readback_note_shows_the_open_and_unknown_creates | yes |
| X08 | scripts/run_real_check.py:1392 | seam: 'result["checks"].append(counter_check(counter_know' -> 'result["ok"] = all(c["ok"] for c in result["checks' | test_r7u_a a3 (F7 after ok computed) | KILLED by test_a3_a_counter_that_is_not_known_is_in_the_result_and_the_result_is_not_ok | yes |
| X09 | scripts/run_real_check.py:1424 | seam: '"counter_known": counter_known,\n        "unseen_co' -> '' | test_r7u_a a3 summary fields | KILLED by test_a3_contacts_not_accounted_for_are_in_the_result_and_the_result_is_not_ok | yes |
| X10 | scripts/run_real_check.py:671 | seam: 'return 0 if ok and written and not left and not un' -> 'return 0 if ok and written and not left and not un' | test_r7t/r7s exit_code_of or a2 real run | SURVIVED narrow (test_a3_a_counter_that_is_not_known or b5_a_hidden_contact_a); wide: SURVIVED-UNTIL-TIMEOUT 120s ['.................'] | yes |
| X11 | scripts/run_real_check.py:1369 | seam: 'smtp_stats = smtp_read.totals if smtp_known else {' -> 'smtp_stats = smtp_read.totals if smtp_known else d' | test_r7u_b b7 stale dict | SURVIVED narrow (b7_one_unreadable); wide: SURVIVED-UNTIL-TIMEOUT 120s ['.................'] | yes |
| X12 | scripts/run_real_check.py:1363 | seam: 'smtp_known = smtp_counter_is_known(smtp_read)' -> 'smtp_known = smtp_counter_is_known(hub_read)' | test_r7u_b b7 hub read used for mail | SURVIVED narrow (b7_one_unreadable or b7_a_real_mail); wide: KILLED 37s ['FAILED tests/test_real_check_dry.py::test_dry_fakes_run_end_to_end - Assertio...'] | yes |
| X13 | scripts/run_real_check.py:1364 | seam: 'if not smtp_known:  # fail closed' -> 'if smtp_known:  # fail closed' | test_r7u_b b7 in_words | KILLED by test_b7_the_run_says_in_words_that_the_mail_count_is_not_known | yes |
| X14 | scripts/run_real_check.py:1382 | seam: 'counter_known = counter_is_known(hub_read)\n    # t' -> 'counter_known = counter_is_known(smtp_read)\n    # ' | test_r7u_a a3 / b5 | SURVIVED narrow (test_a3_a_counter_that_is_not_known or b5_a_hidden); wide: KILLED 36s ['FAILED tests/test_real_check_dry.py::test_dry_fakes_run_end_to_end - Assertio...'] | yes |
| X16 | scripts/run_real_check.py:586 | seam: 'known = counter_is_known(hub_read)\n    created = h' -> 'known = bool(hub_read.totals)\n    created = hub_st' | test_r7u_a a4 not-known note (unreadable but partial sum) | KILLED by test_a4_the_readback_note_does_not_name_a_number_when_the_counter_is_not_known | yes |
| X17 | scripts/run_real_check.py:1317 | seam: 'a, run_dir, env, e, len(lead_ids), read_counter_fi' -> 'a, run_dir, env, e, len(lead_ids), read_counter_fi' | test_r7u_a a4 readback reads hubspot file | KILLED by test_a4_the_readback_note_shows_the_open_and_unknown_creates | yes |
| X18 | scripts/run_real_check.py:603 | seam: 'most = contacts_not_accounted_for(created, 0, unkn' -> 'most = contacts_not_accounted_for(created, 1, unkn' | test_r7u_a a4 most that may be left | KILLED by test_a4_the_readback_note_gives_the_most_contacts_that_may_be_left[100-0 | yes |
| X19 | scripts/run_real_check.py:611 | seam: '{"ok": False, "note": note, "leads_in_book": leads' -> '{"ok": False, "note": note, "leads_in_book": leads' | test_r7u_a a4 / r7s readback result file | SURVIVED narrow (test_a4_the_readback_note_shows); wide: SURVIVED-UNTIL-TIMEOUT 120s ['................'] | yes |
| X20 | scripts/run_real_check.py:664 | seam: '"values": {"counter_known": known, "unseen_contact' -> '"values": {"counter_known": not known, "unseen_con' | test_r7u_a a3 counter_check values | KILLED by test_a3_the_counter_check_is_ok_only_for_a_known_counter_and_no_unseen_contact | yes |
| X21 | scripts/run_real_check.py:1008 | seam: 'return read.files > 0 and read.unreadable == 0 and' -> 'return read.files > 0 and read.unreadable == 0 and' | test_r7u_b b7 (zero mails sent is a known number) | KILLED by test_b7_the_mail_counter_rule_needs_a_file_no_unreadable_file_and_the_sent_number | yes |
| X22 | scripts/run_real_check.py:1008 | seam: 'return read.files > 0 and read.unreadable == 0 and' -> 'return read.files > 1 and read.unreadable == 0 and' | test_r7u_b b7 | KILLED by test_b7_a_run_with_a_readable_mail_counter_ends_with_zero | yes |
| X23 | scripts/run_real_check.py:1362 | seam: 'smtp_read = read_counter_files_checked(run_dir, ".' -> 'smtp_read = CounterRead(read_counter_files(run_dir' | test_r7u_b b7 unchecked read | KILLED by test_b7_one_unreadable_mail_counter_file_is_not_a_smaller_number_it_fails_closed | yes |
| X24 | scripts/run_real_check.py:1360 | seam: 'hub_read = read_counter_files_checked(run_dir, ".h' -> 'hub_read = CounterRead(read_counter_files(run_dir,' | test_r7u_a a2 real run / b5 | KILLED by test_b5_a_hidden_contact_and_a_counter_file_that_cannot_be_read_ends_as_failed | yes |
| Y01 | scripts/run_real_check.py:643 | fresh: 'open_part = min(open_part, max(0, leads - created)' -> 'open_part = min(open_part, max(0, leads - created ' | test_r7u_a a1 rule oracle | KILLED by test_a1_the_rule_equals_the_brute_force_oracle_on_every_small_input | yes |
| Y02 | scripts/run_real_check.py:644 | fresh: 'return max(0, created + open_part - accounted)' -> 'return max(0, created + open_part - accounted - 1)' | test_r7u_a a1 oracle / named | KILLED by test_a1_one_more_created_than_leads_is_not_hidden_by_the_cap[1 | yes |
| Y03 | scripts/run_real_check.py:639 | fresh: 'if created is None:\n        raise CounterUnreadabl' -> 'if not created:\n        raise CounterUnreadable' | test_r7u_a a1 named (created 0 is a number) | KILLED by test_a1_the_rule_equals_the_brute_force_oracle_on_every_small_input | yes |
| Y04 | scripts/run_real_check.py:639 | fresh: 'if created is None:\n        raise CounterUnreadabl' -> 'if created is not None:\n        raise CounterUnrea' | test_r7u_a a1/a3 | KILLED by test_a1_one_more_created_than_leads_is_not_hidden_by_the_cap[1 | yes |
| Y05 | scripts/run_real_check.py:999 | fresh: 'total.update(values)' -> 'total.update({k: 1 for k in values})' | test_r7u_a a2 whole numbers read | KILLED by test_a2_whole_numbers_from_zero_are_read | yes |
| Y06 | scripts/run_real_check.py:1000 | fresh: 'except (OSError, ValueError, AttributeError, TypeE' -> 'except (OSError, ValueError, AttributeError, TypeE' | test_r7u_a a2 / b7 | KILLED by test_a2_a_counter_value_that_is_not_a_whole_number_from_zero_is_unreadable[1e999 | yes |
| Y07 | scripts/run_real_check.py:1000 | fresh: 'except (OSError, ValueError, AttributeError, TypeE' -> 'except (OSError, ValueError, TypeError, Arithmetic' | test_r7u_a a2 not an object | KILLED by test_a2_a_counter_that_is_not_an_object_is_unreadable | yes |
| Y08 | scripts/run_real_check.py:1000 | fresh: 'except (OSError, ValueError, AttributeError, TypeE' -> 'except (OSError, AttributeError, TypeError, Arithm' | test_r7u_a a2 (bad value raises our ValueError) | KILLED by test_a2_a_counter_value_that_is_not_a_whole_number_from_zero_is_unreadable[1e999 | yes |
| Y09 | scripts/run_real_check.py:1000 | fresh: 'except (OSError, ValueError, AttributeError, TypeE' -> 'except (ValueError, AttributeError, TypeError, Ari' | test_r7u_a/b OSError (folder instead of file) | SURVIVED narrow (test_a2 and not real_run or b7_a_real_mail); wide: not run | yes |
| Y10 | scripts/run_real_check.py:1000 | fresh: 'except (OSError, ValueError, AttributeError, TypeE' -> 'except (OSError, ValueError, AttributeError, Arith' | test_r7u_a a2 TypeError | SURVIVED narrow (test_a2 and not real_run); wide: not run | yes |
| Y11 | scripts/run_real_check.py:996 | fresh: 'values = dict(load_json_file(p).items())' -> 'values = dict(list(load_json_file(p).items())[:1])' | test_r7u_a a2 / r7t sums | KILLED by test_a2_whole_numbers_from_zero_are_read | yes |
| Y12 | scripts/run_real_check.py:1384 | fresh: 'unseen = 0\n    if counter_known:' -> 'unseen = 1\n    if counter_known:' | test_r7u_a a3 not-known (unseen 0) | KILLED by test_a3_a_counter_that_is_not_known_is_in_the_result_and_the_result_is_not_ok | yes |
| Y13 | scripts/run_real_check.py:1387 | fresh: 'hub_stats.get("created"),\n            len(crm_pair' -> 'hub_stats.get("created", 0),\n            len(crm_p' | (equivalent probe: default 0 behind counter_known) | SURVIVED narrow (test_a1_one_more or test_a1_the_rule or test_a1_named or tes); wide: SURVIVED-UNTIL-TIMEOUT 100s ['.................'] | yes |
| Y14 | scripts/run_real_check.py:1393 | fresh: 'result["ok"] = all(c["ok"] for c in result["checks' -> 'result["ok"] = any(c["ok"] for c in result["checks' | test_r7u_a a3 / dry | KILLED by test_a3_a_counter_that_is_not_known_is_in_the_result_and_the_result_is_not_ok | yes |
| Y15 | scripts/run_real_check.py:1466 | fresh: 'return exit_code_of(result["ok"], written, left, u' -> 'return exit_code_of(result["ok"], written, left, 0' | test_r7u_a a3 real run (list lag) exit | SURVIVED narrow (test_a3_contacts_not_accounted); wide: SURVIVED-UNTIL-TIMEOUT 100s ['................'] | yes |
| Y16 | scripts/run_real_check.py:1466 | fresh: 'return exit_code_of(result["ok"], written, left, u' -> 'return exit_code_of(result["ok"], written, left, u' | test_r7u_a a2/a3 real run exit | SURVIVED narrow (test_a3_a_counter_that_is_not_known or test_a2_a_counter_wit); wide: SURVIVED-UNTIL-TIMEOUT 100s ['................'] | yes |
| Y17 | scripts/run_real_check.py:1450 | fresh: 'if not counter_known:\n        print(\n            "' -> 'if counter_known:\n        print(\n            "the ' | test_r7u_a a3 (words printed) | SURVIVED narrow (test_a3_a_counter_that_is_not_known); wide: SURVIVED-UNTIL-TIMEOUT 100s ['................'] | yes |
| Y18 | scripts/run_real_check.py:1456 | fresh: 'if (\n        unseen\n    ):' -> 'if (\n        False\n    ):' | test_r7u_a a3 unseen message printed | SURVIVED narrow (test_a3_contacts_not_accounted); wide: SURVIVED-UNTIL-TIMEOUT 100s ['................'] | yes |
| Y19 | scripts/run_real_check.py:1461 | fresh: 'f"{hub_stats.get(\'create_open\', 0) + hub_stats.get' -> 'f"{hub_stats.get(\'create_open\', 0)} create request' | test_r7u_a a1c main-level message | SURVIVED narrow (a1c); wide: SURVIVED-UNTIL-TIMEOUT 100s ['................'] | yes |
| Y20 | scripts/run_real_check.py:587 | fresh: 'created = hub_stats.get("created") if known else N' -> 'created = hub_stats.get("created") if known else 0' | test_r7u_a a4 not-known note | KILLED by test_a4_the_readback_note_does_not_name_a_number_when_the_counter_is_not_known | yes |
| Y21 | scripts/run_real_check.py:596 | fresh: 'if created is not None:\n        if unknown_outcome' -> 'if created is not None:\n        if not unknown_out' | test_r7u_a a4 open/unknown note | KILLED by test_a4_the_readback_note_shows_the_open_and_unknown_creates | yes |
| Y22 | scripts/run_real_check.py:594 | fresh: '+ " contacts in total (its own counter)"\n    )\n   ' -> '+ " contacts in total (its own counter)"\n    )\n   ' | test_r7u_a a4 not-known note | KILLED by test_a4_the_readback_note_does_not_name_a_number_when_the_counter_is_not_known | yes |
| Y23 | scripts/run_real_check.py:607 | fresh: 'note += "their lead ids start with L and are liste' -> 'note += "their lead ids start with L and are liste' | test_r7u_a a4 note printed | KILLED by test_a4_the_readback_note_shows_the_open_and_unknown_creates | yes |
| Y24 | scripts/run_real_check.py:604 | fresh: 'note += f"; up to {most} contacts may still be in ' -> 'note += f"; up to {created} contacts may still be ' | test_r7u_a a4 most | KILLED by test_a4_the_readback_note_gives_the_most_contacts_that_may_be_left[100-0 | yes |
| Y25 | scripts/run_real_check.py:606 | fresh: 'note += "; an unknown number of contacts may still' -> 'note += "; up to 0 contacts may still be in HubSpo' | test_r7u_a a4 not-known note | SURVIVED narrow (test_a4_the_readback_note_does_not_name); wide: not run | yes |
| Y26 | scripts/run_real_check.py:653 | fresh: 'elif unseen:\n        detail = f"{unseen} contacts ' -> 'elif not unseen:\n        detail = f"{unseen} conta' | test_r7u_a a3 counter_check detail | KILLED by test_a3_the_counter_check_is_ok_only_for_a_known_counter_and_no_unseen_contact | yes |
| Y27 | scripts/run_real_check.py:658 | fresh: '"id": "F7",' -> '"id": "F6",' | test_r7u_a a3 id of the check | KILLED by test_a3_the_counter_check_is_ok_only_for_a_known_counter_and_no_unseen_contact | yes |
| Y28 | scripts/run_real_check.py:662 | fresh: '"offender_count": 0,\n        "offenders": [],\n    ' -> '"offender_count": unseen,\n        "offenders": [],' | test_r7u_a a3 counter_check shape | SURVIVED narrow (test_a3_the_counter_check); wide: not run | yes |
| Y29 | scripts/run_real_check.py:651 | fresh: 'if not known:\n        detail = "the desk\'s count o' -> 'if known:\n        detail = "the desk\'s count of cr' | test_r7u_a a3 | KILLED by test_a3_the_counter_check_is_ok_only_for_a_known_counter_and_no_unseen_contact | yes |
| Y30 | scripts/run_real_check.py:1366 | fresh: '"the desk\'s mail counter cannot be trusted (no fil' -> '"the desk\'s mail counter is fine."' | test_r7u_b b7 in_words | KILLED by test_b7_the_run_says_in_words_that_the_mail_count_is_not_known | yes |
| Z01 | src/lead_desk/loopback.py:27 | fresh: 'bare = name[1:-1] if name.startswith("[") and name' -> 'bare = name[1:-1] if name.startswith("[") or name.' | test_r7u_c / r7t loopback spellings | SURVIVED narrow (b8 or c1 or c2 or c3 or c4 or c5 or c6 or c7 or t6 or t12); wide: SURVIVED-UNTIL-TIMEOUT 300s ['........................................................................ [ 23% | yes |
| Z02 | src/lead_desk/loopback.py:27 | fresh: 'bare = name[1:-1] if name.startswith("[") and name' -> 'bare = name[1:-1] if name.endswith("]") else name' | test_r7u_c / r7t | SURVIVED narrow (b8 or c1 or c2 or c3 or c4 or c5 or c6 or c7 or t6 or t12); wide: not run | yes |
| Z03 | src/lead_desk/loopback.py:28 | fresh: 'if "[" in bare or "]" in bare or "%" in bare:' -> 'if "[" in bare or "%" in bare:' | test_r7u_c half bracket | SURVIVED narrow (b8 or c1 or c2 or c3 or c4 or c5 or c6 or c7 or t6 or t12); wide: not run | yes |
| Z04 | src/lead_desk/loopback.py:28 | fresh: 'if "[" in bare or "]" in bare or "%" in bare:' -> 'if "]" in bare or "%" in bare:' | test_r7u_c half bracket | SURVIVED narrow (b8 or c1 or c2 or c3 or c4 or c5 or c6 or c7 or t6 or t12); wide: not run | yes |
| Z05 | src/lead_desk/loopback.py:34 | fresh: 'if isinstance(ip, ipaddress.IPv6Address) and ip.ip' -> 'if isinstance(ip, ipaddress.IPv4Address) and ip.ip' | test_r7u_c mapped | CRASH (ERR rc=4, whole run aborted at start; counts as caught, no single test id) | yes |
| Z06 | src/lead_desk/loopback.py:34 | fresh: 'ip.ipv4_mapped is not None:' -> 'ip.ipv4_mapped is None:' | test_r7u_c mapped v4/v6 | KILLED by  | yes |
| Z07 | src/lead_desk/loopback.py:34 | fresh: 'if isinstance(ip, ipaddress.IPv6Address) and ip.ip' -> 'if isinstance(ip, ipaddress.IPv6Address):' | test_r7u_c plain ::1 (mapped None) | KILLED by  | yes |
| Z08 | src/lead_desk/loopback.py:46 | fresh: 'return host' -> 'return host.strip()' | test_r7u_c returns the host unchanged | SURVIVED narrow (b8 or c1 or c2 or c3 or c4 or c5 or c6 or c7 or t6 or t12); wide: not run | yes |
| Z09 | src/lead_desk/loopback.py:17 | fresh: 'import ipaddress' -> 'import ipaddress\nimport http.server' | test_r7u_c light module imports | KILLED by test_c1_the_light_module_imports_only_the_standard_library | yes |
| Z10 | demo_only/fake_imap.py:16 | fresh: 'from lead_desk.loopback import require_loopback_ho' -> 'from demo_only.fake_smtp_tls import require_loopba' | test_r7u_c light-import | SURVIVED narrow (b8 or c1 or c2 or c3 or c4 or c5 or c6 or c7 or t6 or t12); wide: not run | yes |
| Z11 | demo_only/fakes_server.py:247 | fresh: 'where = require_loopback_host(Config().fakes_host ' -> 'where = Config().fakes_host if host is None else h' | test_r7u_b b8 / c refusal in fakes_server | SURVIVED narrow (b8 or c1 or c2 or c3 or c4 or c5 or c6 or c7 or t6 or t12); wide: not run | yes |
| Z12 | demo_only/fake_model_server.py:275 | fresh: 'require_loopback_host(host)  # a stand-in' -> 'pass  # a stand-in' | test_r7u_c / r7t fake model refuses | SURVIVED narrow (b8 or c1 or c2 or c3 or c4 or c5 or c6 or c7 or t6 or t12); wide: not run | yes |
| Z13 | demo_only/bad_request.py:46 | fresh: 'require_loopback_host(host)  # fails closed' -> 'pass  # fails closed' | test_r7u_c QuietServer refuses | KILLED by test_t6_every_entry_point_refuses_the_host_before_any_socket[quiet-0.0.0.0 | yes |
| Z14 | src/lead_desk/config.py:515 | fresh: 'if not is_loopback_host(self.fakes_host):' -> 'if is_loopback_host(self.fakes_host):' | test_config / r7t fakes_host | CRASH (ERR rc=4, whole run aborted at start; counts as caught, no single test id) | yes |
| Z15 | tools/refusing_args.py:190 | fresh: 'raise ArgumentTypeError(LOOPBACK_HOST_TEXT) from N' -> 'raise ArgumentTypeError("x") from None' | test_r7u_c text / r7t refusing_args | SURVIVED narrow (b8 or c1 or c2 or c3 or c4 or c5 or c6 or c7 or t6 or t12); wide: not run | yes |
| Z16 | src/lead_desk/smtp_outbox.py:87 | fresh: 'if not is_loopback_host(self.host):' -> 'if is_loopback_host(self.host):' | smtp_outbox loopback | SURVIVED narrow (b8 or c1 or c2 or c3 or c4 or c5 or c6 or c7 or t6 or t12); wide: not run | yes |

## Classification hints (mine, unverified)
- X10, Y15, Y16: exit_code_of's `not unseen` / `counter_known` are shadowed by F7 in result["ok"] in the main flow: probably equivalent in main(), a unit test on exit_code_of would kill them.
- X11 (stale dict hand-over): probably equivalent (hub_stats has no "sent" key, so F4 still fails).
- Y13 (`get("created", 0)` behind counter_known): equivalent.
- Y17, Y18, Y19, X19, Y28, Y25, X05, X01: assertions missing (printed words, result-file field, offender_count, "up to 0 contacts" text, create_open doubled, smtp file with a bad value).
- Y09, Y10 (drop OSError / TypeError from the except): maybe covered by load_json_file wrapping; not checked.

## Survivors with exact old/new text (narrow survivors; file as in the table)
### X01 at scripts/run_real_check.py:997
expected catcher: test_r7u_a a2 / b7 (smtp file with bad value)
OLD:
```
            if not all(type(v) is int and v >= 0 for v in values.values()):
```
NEW:
```
            if suffix == ".hubspot.json" and not all(type(v) is int and v >= 0 for v in values.values()):
```
wide: ['X01', 'SURVIVED-UNTIL-TIMEOUT', '120s', '[]', "['................']", 'restored=True']

### X05 at scripts/run_real_check.py:1389
expected catcher: test_r7u_a a1c open term
OLD:
```
            hub_stats.get("create_open", 0) + hub_stats.get("create_unknown", 0),
            len(lead_ids),
        )
    result["checks"].append
```
NEW:
```
            hub_stats.get("create_open", 0) * 2 + hub_stats.get("create_unknown", 0),
            len(lead_ids),
        )
    result["checks"].append
```
wide: ['X05', 'SURVIVED-UNTIL-TIMEOUT', '120s', '[]', "['.................']", 'restored=True']

### X10 at scripts/run_real_check.py:671
expected catcher: test_r7t/r7s exit_code_of or a2 real run
OLD:
```
return 0 if ok and written and not left and not unseen and counter_known else EXIT_FAILED
```
NEW:
```
return 0 if ok and written and not left and not unseen else EXIT_FAILED
```
wide: ['X10', 'SURVIVED-UNTIL-TIMEOUT', '120s', '[]', "['.................']", 'restored=True']

### X11 at scripts/run_real_check.py:1369
expected catcher: test_r7u_b b7 stale dict
OLD:
```
    smtp_stats = smtp_read.totals if smtp_known else {}
```
NEW:
```
    smtp_stats = smtp_read.totals if smtp_known else dict(hub_stats)
```
wide: ['X11', 'SURVIVED-UNTIL-TIMEOUT', '120s', '[]', "['.................']", 'restored=True']

### X12 at scripts/run_real_check.py:1363
expected catcher: test_r7u_b b7 hub read used for mail
OLD:
```
    smtp_known = smtp_counter_is_known(smtp_read)
```
NEW:
```
    smtp_known = smtp_counter_is_known(hub_read)
```
wide: ['X12', 'KILLED', '37s', "['FAILED tests/test_real_check_dry.py::test_dry_fakes_run_end_to_end - Assertio...']", "['1 failed, 1 passed in 36.69s']", 'restored=True']

### X14 at scripts/run_real_check.py:1382
expected catcher: test_r7u_a a3 / b5
OLD:
```
    counter_known = counter_is_known(hub_read)
    # the clean-up
```
NEW:
```
    counter_known = counter_is_known(smtp_read)
    # the clean-up
```
wide: ['X14', 'KILLED', '36s', "['FAILED tests/test_real_check_dry.py::test_dry_fakes_run_end_to_end - Assertio...']", "['1 failed, 1 passed in 36.32s']", 'restored=True']

### X19 at scripts/run_real_check.py:611
expected catcher: test_r7u_a a4 / r7s readback result file
OLD:
```
{"ok": False, "note": note, "leads_in_book": leads, "hubspot_calls_by_the_desk": hub_stats},
```
NEW:
```
{"ok": False, "note": note, "leads_in_book": leads, "hubspot_calls_by_the_desk": {}},
```
wide: ['X19', 'SURVIVED-UNTIL-TIMEOUT', '120s', '[]', "['................']", 'restored=True']

### Y09 at scripts/run_real_check.py:1000
expected catcher: test_r7u_a/b OSError (folder instead of file)
OLD:
```
        except (OSError, ValueError, AttributeError, TypeError, ArithmeticError):
```
NEW:
```
        except (ValueError, AttributeError, TypeError, ArithmeticError):
```
wide: None

### Y10 at scripts/run_real_check.py:1000
expected catcher: test_r7u_a a2 TypeError
OLD:
```
        except (OSError, ValueError, AttributeError, TypeError, ArithmeticError):
```
NEW:
```
        except (OSError, ValueError, AttributeError, ArithmeticError):
```
wide: None

### Y13 at scripts/run_real_check.py:1387
expected catcher: (equivalent probe: default 0 behind counter_known)
OLD:
```
            hub_stats.get("created"),
            len(crm_pairs),
            hub_stats.get("create_open", 0) + hub_stats.get("create_unknown", 0),
            len(lead_ids),
        )
    result["checks"].append
```
NEW:
```
            hub_stats.get("created", 0),
            len(crm_pairs),
            hub_stats.get("create_open", 0) + hub_stats.get("create_unknown", 0),
            len(lead_ids),
        )
    result["checks"].append
```
wide: ['Y13', 'SURVIVED-UNTIL-TIMEOUT', '100s', '[]', "['.................']", 'restored=True']

### Y15 at scripts/run_real_check.py:1466
expected catcher: test_r7u_a a3 real run (list lag) exit
OLD:
```
return exit_code_of(result["ok"], written, left, unseen, counter_known)
```
NEW:
```
return exit_code_of(result["ok"], written, left, 0, counter_known)
```
wide: ['Y15', 'SURVIVED-UNTIL-TIMEOUT', '100s', '[]', "['................']", 'restored=True']

### Y16 at scripts/run_real_check.py:1466
expected catcher: test_r7u_a a2/a3 real run exit
OLD:
```
return exit_code_of(result["ok"], written, left, unseen, counter_known)
```
NEW:
```
return exit_code_of(result["ok"], written, left, unseen, True)
```
wide: ['Y16', 'SURVIVED-UNTIL-TIMEOUT', '100s', '[]', "['................']", 'restored=True']

### Y17 at scripts/run_real_check.py:1450
expected catcher: test_r7u_a a3 (words printed)
OLD:
```
    if not counter_known:
        print(
            "the desk's HubSpot counter cannot
```
NEW:
```
    if counter_known:
        print(
            "the desk's HubSpot counter cannot
```
wide: ['Y17', 'SURVIVED-UNTIL-TIMEOUT', '100s', '[]', "['................']", 'restored=True']

### Y18 at scripts/run_real_check.py:1456
expected catcher: test_r7u_a a3 unseen message printed
OLD:
```
    if (
        unseen
    ):
```
NEW:
```
    if (
        False
    ):
```
wide: ['Y18', 'SURVIVED-UNTIL-TIMEOUT', '100s', '[]', "['................']", 'restored=True']

### Y19 at scripts/run_real_check.py:1461
expected catcher: test_r7u_a a1c main-level message
OLD:
```
            f"{hub_stats.get('create_open', 0) + hub_stats.get('create_unknown', 0)} create requests with no known "
```
NEW:
```
            f"{hub_stats.get('create_open', 0)} create requests with no known "
```
wide: ['Y19', 'SURVIVED-UNTIL-TIMEOUT', '100s', '[]', "['................']", 'restored=True']

### Y25 at scripts/run_real_check.py:606
expected catcher: test_r7u_a a4 not-known note
OLD:
```
        note += "; an unknown number of contacts may still be in HubSpot, "
```
NEW:
```
        note += "; up to 0 contacts may still be in HubSpot, "
```
wide: None

### Y28 at scripts/run_real_check.py:662
expected catcher: test_r7u_a a3 counter_check shape
OLD:
```
        "offender_count": 0,
        "offenders": [],
        "values"
```
NEW:
```
        "offender_count": unseen,
        "offenders": [],
        "values"
```
wide: None

### Z01 at src/lead_desk/loopback.py:27
expected catcher: test_r7u_c / r7t loopback spellings
OLD:
```
    bare = name[1:-1] if name.startswith("[") and name.endswith("]") else name
```
NEW:
```
    bare = name[1:-1] if name.startswith("[") or name.endswith("]") else name
```
wide: ['Z01', 'SURVIVED-UNTIL-TIMEOUT', '300s', '[]', "['........................................................................ [ 23%]\\n........................................................................ [ 46%]\\n..............']", 'restored=True']

### Z02 at src/lead_desk/loopback.py:27
expected catcher: test_r7u_c / r7t
OLD:
```
    bare = name[1:-1] if name.startswith("[") and name.endswith("]") else name
```
NEW:
```
    bare = name[1:-1] if name.endswith("]") else name
```
wide: None

### Z03 at src/lead_desk/loopback.py:28
expected catcher: test_r7u_c half bracket
OLD:
```
    if "[" in bare or "]" in bare or "%" in bare:
```
NEW:
```
    if "[" in bare or "%" in bare:
```
wide: None

### Z04 at src/lead_desk/loopback.py:28
expected catcher: test_r7u_c half bracket
OLD:
```
    if "[" in bare or "]" in bare or "%" in bare:
```
NEW:
```
    if "]" in bare or "%" in bare:
```
wide: None

### Z08 at src/lead_desk/loopback.py:46
expected catcher: test_r7u_c returns the host unchanged
OLD:
```
    return host
```
NEW:
```
    return host.strip()
```
wide: None

### Z10 at demo_only/fake_imap.py:16
expected catcher: test_r7u_c light-import
OLD:
```
from lead_desk.loopback import require_loopback_host

```
NEW:
```
from demo_only.fake_smtp_tls import require_loopback_host as _r
require_loopback_host = _r

```
wide: None

### Z11 at demo_only/fakes_server.py:247
expected catcher: test_r7u_b b8 / c refusal in fakes_server
OLD:
```
    where = require_loopback_host(Config().fakes_host if host is None else host)
```
NEW:
```
    where = Config().fakes_host if host is None else host
```
wide: None

### Z12 at demo_only/fake_model_server.py:275
expected catcher: test_r7u_c / r7t fake model refuses
OLD:
```
    require_loopback_host(host)  # a stand-in
```
NEW:
```
    pass  # a stand-in
```
wide: None

### Z15 at tools/refusing_args.py:190
expected catcher: test_r7u_c text / r7t refusing_args
OLD:
```
        raise ArgumentTypeError(LOOPBACK_HOST_TEXT) from None
```
NEW:
```
        raise ArgumentTypeError("x") from None
```
wide: None

### Z16 at src/lead_desk/smtp_outbox.py:87
expected catcher: smtp_outbox loopback
OLD:
```
        if not is_loopback_host(self.host):
```
NEW:
```
        if is_loopback_host(self.host):
```
wide: None


## Processes
All my runners and pytest children stopped (pgrep of R7U-MUT paths empty). Copies tree, tree2, tmp1, tmp2 deleted after this file was written.
