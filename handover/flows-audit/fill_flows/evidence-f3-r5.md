# evidence-f3-r5 (EVIDENCE RUNNER: raw output, no judgement)
Date 2026-11-16 UTC. Run as root unless said. Code under test: fill_flows.py and test_fill_flows.py as on disk (head bf1acc701 + working tree). Nothing committed or edited in the repo.

## Things that did not go as expected / not checked (first)
- Mutation run (20 single-line mutants, fixed seed 20261116, tests = python3.11 -I -m unittest): 8 SURVIVED (m1, m3, m5, m9, m10, m11, m12, m18), 12 killed. Details below.
- First non-root attempt had 28 errors: my own set-up copied only the real-v5 flows, the tests also need the film flows (FileNotFoundError .../n8n-flows-film-v5). Not a tool defect. Re-run with the whole demo folder: 113 OK as nobody.
- 'old code' = fill_flows.py from commit da0935751 (09:36 UTC, last commit of that file before review-security-r2.md at 09:50 UTC; the fix builder's own saved old copy is not available to me). Result matches the claim (27 failures + 4 errors of 113).
- 19 files reported by ruff format (claim said 18): one more .py/.pyi file in the folder than the fix note counted; not investigated.
- noqa found (6): fill_flows.py:887 BLE001; test_fill_flows.py:77, 1356, 1658 S603; 784 S311; 1357 S607. No nosec, no type: ignore.
- Not run: Python 3.9/3.10, macOS, real n8n.

## (1) python -I -m unittest in the folder
### python3.11
.................................................................................................................
----------------------------------------------------------------------
Ran 113 tests in 11.958s

OK
rc=0
### python3.12
.................................................................................................................
----------------------------------------------------------------------
Ran 113 tests in 12.556s

OK
rc=0
### python3.13
.................................................................................................................
----------------------------------------------------------------------
Ran 113 tests in 12.602s

OK
rc=0

## (2) gates (from repo root, scoped to the folder)
### pytest -q handover/flows-audit/fill_flows
.........................................                                [100%]
113 passed in 11.33s
rc=0
### ruff check
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
All checks passed!
rc=0
### ruff format --check
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
19 files already formatted
rc=0
### bandit -ll -r
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: None
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	running on Python 3.13.18
Run started:2026-11-16 10:05:49.143294+00:00

Test results:
	No issues identified.

Code scanned:
	Total lines of code: 2199
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 6
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 6
Files skipped (0):
rc=0
### grep noqa/nosec/type: ignore
handover/flows-audit/fill_flows/fill_flows.py:887:    except Exception as e:  # noqa: BLE001  never print the exception text: it could carry a path or value
handover/flows-audit/fill_flows/test_fill_flows.py:77:    p = subprocess.run(  # noqa: S603
handover/flows-audit/fill_flows/test_fill_flows.py:784:            rnd = random.Random(seed)  # noqa: S311 - test data only
handover/flows-audit/fill_flows/test_fill_flows.py:1356:        p = subprocess.run(  # noqa: S603
handover/flows-audit/fill_flows/test_fill_flows.py:1357:            ["node", "-e", script],  # noqa: S607
handover/flows-audit/fill_flows/test_fill_flows.py:1658:        p = subprocess.run(cmd + args, capture_output=True, text=True, timeout=60, check=False)  # noqa: S603

## (3) NEW tests against OLD fill_flows.py (commit da0935751)
Ran 113 tests in 7.929s

FAILED (failures=27, errors=4)
rc=1
ERROR: test_delete_handles_the_not_ready_note (test_fill_flows.Round5.test_delete_handles_the_not_ready_note)
ERROR: test_fd_path_follows_the_handle_not_the_name (test_fill_flows.Round5.test_fd_path_follows_the_handle_not_the_name)
ERROR: test_token_forms (test_fill_flows.Unit.test_token_forms)
ERROR: test_token_refusals_in_process (test_fill_flows.Unit.test_token_refusals_in_process)
FAIL: test_nothing_there (test_fill_flows.Delete.test_nothing_there)
FAIL: test_delete_no_manifest_refuses_a_symlink_or_folder_in_the_manifest_place (test_fill_flows.Hardening.test_delete_no_manifest_refuses_a_symlink_or_folder_in_the_manifest_place)
FAIL: test_delete_refuses_a_parent_link_made_by_another_user (test_fill_flows.Hardening.test_delete_refuses_a_parent_link_made_by_another_user)
FAIL: test_lexer_agrees_with_a_real_js_engine (test_fill_flows.Hardening.test_lexer_agrees_with_a_real_js_engine)
FAIL: test_manifest_delete_refuses_a_folder_that_is_not_yours (test_fill_flows.Hardening.test_manifest_delete_refuses_a_folder_that_is_not_yours)
FAIL: test_no_manifest_force_hash_refuses_a_folder_named_like_a_json_file (test_fill_flows.Hardening.test_no_manifest_force_hash_refuses_a_folder_named_like_a_json_file)
FAIL: test_no_manifest_needs_the_marker_file (test_fill_flows.Hardening.test_no_manifest_needs_the_marker_file)
FAIL: test_no_manifest_refuses_a_fifo_without_hanging (test_fill_flows.Hardening.test_no_manifest_refuses_a_fifo_without_hanging)
FAIL: test_no_manifest_refuses_a_marker_for_another_folder_or_format (test_fill_flows.Hardening.test_no_manifest_refuses_a_marker_for_another_folder_or_format)
FAIL: test_no_manifest_refuses_wrong_file_mode_folder_mode_and_owner (test_fill_flows.Hardening.test_no_manifest_refuses_wrong_file_mode_folder_mode_and_owner)
FAIL: test_symlinked_out_dir_with_no_manifest_and_with_copied_manifest (test_fill_flows.Hardening.test_symlinked_out_dir_with_no_manifest_and_with_copied_manifest)
FAIL: test_write_cut_in_the_middle_leaves_nothing_and_rerun_works (test_fill_flows.Hardening.test_write_cut_in_the_middle_leaves_nothing_and_rerun_works)
FAIL: test_nested_template_refused (test_fill_flows.Negative.test_nested_template_refused)
FAIL: test_plain_token_outside_the_address_fields_is_refused (test_fill_flows.Positive.test_plain_token_outside_the_address_fields_is_refused)
FAIL: test_real_and_film (test_fill_flows.Positive.test_real_and_film)
FAIL: test_a_number_that_reads_as_infinity_is_refused (test_fill_flows.Round5.test_a_number_that_reads_as_infinity_is_refused)
FAIL: test_a_real_ctrl_c_during_creation_leaves_nothing (test_fill_flows.Round5.test_a_real_ctrl_c_during_creation_leaves_nothing)
FAIL: test_delete_force_hash_removes_an_empty_or_cut_manifest_when_no_folder (test_fill_flows.Round5.test_delete_force_hash_removes_an_empty_or_cut_manifest_when_no_folder)
FAIL: test_fill_folder_swapped_for_a_link_after_the_open_writes_nothing_there (test_fill_flows.Round5.test_fill_folder_swapped_for_a_link_after_the_open_writes_nothing_there)
FAIL: test_fill_refusal_names_the_way_out_of_a_cut_manifest (test_fill_flows.Round5.test_fill_refusal_names_the_way_out_of_a_cut_manifest)
FAIL: test_incomplete_copy_is_marked_not_ready (test_fill_flows.Round5.test_incomplete_copy_is_marked_not_ready)
FAIL: test_input_names_with_a_backslash_or_control_character_are_refused (test_fill_flows.Round5.test_input_names_with_a_backslash_or_control_character_are_refused)
FAIL: test_interrupt_right_after_a_file_is_written_leaves_nothing (test_fill_flows.Round5.test_interrupt_right_after_a_file_is_written_leaves_nothing)
FAIL: test_no_manifest_does_not_remove_an_invalid_sibling_manifest (test_fill_flows.Round5.test_no_manifest_does_not_remove_an_invalid_sibling_manifest)
FAIL: test_output_folder_name_with_a_backslash_is_refused (test_fill_flows.Round5.test_output_folder_name_with_a_backslash_is_refused)
FAIL: test_output_parent_swapped_into_git_after_the_name_check_writes_nothing (test_fill_flows.Round5.test_output_parent_swapped_into_git_after_the_name_check_writes_nothing)
FAIL: test_values_file_swapped_into_git_after_the_name_check_is_refused (test_fill_flows.Round5.test_values_file_swapped_into_git_after_the_name_check_is_refused)

## (4) 20 single-line mutants (scratch copies; list: scratchpad/mut/list.json)
m1 line 778: dfd = -1  =>  dfd = -0  | SURVIVED (OK)
m2 line 81: return ascii(str(x))[1:-1]  =>  return ascii(str(x))[0:-1]  | killed (FAILED (failures=2))
m3 line 615: "use a folder on a normal Linux or macOS disk"  =>  "use a folder on a normal Linux and macOS disk"  | SURVIVED (OK)
m4 line 673: ph[name] = ph.get(name, 0) + 1  =>  ph[name] = ph.get(name, 0) + 2  | killed (FAILED (failures=2))
m5 line 163: real = _fd_path(fd, rp)  # the place of the OPEN file, in case the path was swapped  =>  real = _fd_path(fd, rp)  # the place of the OPEN file, not in case the path was swapped  | SURVIVED (OK)
m6 line 212: raise Refused(f"values file line {no}: value of {key} has a space at its start or end")  =>  raise Refused(f"values file line {no}: value of {key} has a space at its start and end")  | killed (FAILED (failures=1))
m7 line 598: dfd = -1  =>  dfd = -0  | killed (FAILED (failures=2))
m8 line 245: "not filled)"  =>  " filled)"  | killed (FAILED (failures=1))
m9 line 116: real = os.fsdecode(buf.split(b"\0", 1)[0])  =>  real = os.fsdecode(buf.split(b"\0", 0)[0])  | SURVIVED (OK)
m10 line 803: raise Refused("manifest is not owned by you; nothing deleted")  =>  raise Refused("manifest is  owned by you; nothing deleted")  | SURVIVED (OK)
m11 line 835: raise Refused(f"{_a(n)}: not owned by you; nothing deleted")  =>  raise Refused(f"{_a(n)}:  owned by you; nothing deleted")  | SURVIVED (OK)
m12 line 338: raise Refused(f"a $env token sits in a {ctx} field (program code; not filled)")  =>  raise Refused(f"a $env token sits not in a {ctx} field (program code; not filled)")  | SURVIVED (OK)
m13 line 441: return True  =>  return False  | killed (FAILED (failures=4))
m14 line 568: if shape(new) != before:  =>  if shape(new) == before:  | killed (FAILED (failures=34, errors=20))
m15 line 207: if key.endswith("_MS") and not DIGITS.match(value):  =>  if key.endswith("_MS") and  DIGITS.match(value):  | killed (FAILED (failures=50, errors=20))
m16 line 463: if st.st_uid != os.getuid() or stat.S_IMODE(st.st_mode) != 0o600:  =>  if st.st_uid != os.getuid() or stat.S_IMODE(st.st_mode) != 0o644:  | killed (FAILED (failures=26, errors=20))
m17 line 296: slash = True  =>  slash = False  | killed (FAILED (failures=1))
m18 line 680: bad += 1  =>  bad += 0  | SURVIVED (OK)
m19 line 291: elif ch in "'\"`":  =>  elif ch not in "'\"`":  | killed (FAILED (failures=35, errors=21))
m20 line 497: if st is not None and stat.S_ISLNK(st.st_mode) and st.st_uid not in (me, 0):  =>  if st is None and stat.S_ISLNK(st.st_mode) and st.st_uid not in (me, 0):  | killed (FAILED (failures=3))

## (5) end to end, real-v5 copy, 3 DESK_* + 6 placeholders (made-up canary values), root
filled 4 files, 3 names and 6 placeholders
no placeholders left; run check before importing
fill rc=0
check: 4 files, 0 problem(s)
check rc=0
keep:
total 20
drwx------ 3 root root 4096 Nov 16 10:07 .
drwx------ 4 root root 4096 Nov 16 10:07 ..
drwx------ 2 root root 4096 Nov 16 10:07 filled
-rw------- 1 root root  515 Nov 16 10:07 filled.manifest.json
-rw------- 1 root root  355 Nov 16 10:07 v.env

keep/filled:
total 68
drwx------ 2 root root  4096 Nov 16 10:07 .
drwx------ 3 root root  4096 Nov 16 10:07 ..
-rw------- 1 root root    27 Nov 16 10:07 .fill_flows-output
-rw------- 1 root root  9796 Nov 16 10:07 mf-form.json
-rw------- 1 root root  9811 Nov 16 10:07 mf-hook.json
-rw------- 1 root root  8895 Nov 16 10:07 mf-recovery.json
-rw------- 1 root root 18503 Nov 16 10:07 mf-sub-crm-mail.json
-- canary in filled files (expected yes):
4
-- unfilled env tokens:
0
deleted 4 files, the folder and the manifest
delete rc=0
nothing to delete: the output folder and its manifest are both missing
delete again rc=0
values file left after delete: only keep/v.env (mode 600); filled folder and manifest gone (ls above).
canary strings in this log / run.log: 0. Input folder diff vs repo copy: identical. git status of repo: no new changes from this run.

## (5b) non-root user nobody (uid 65534)
unittest (whole demo folder copied to a nobody-owned /tmp dir, because the scratchpad is root-only):
Ran 113 tests in 11.058s

OK
rc=0
end to end fill/check/delete as nobody (first attempt, flows real-v5):
filled 4 files, 3 names and 6 placeholders
no placeholders left; run check before importing
fill rc=0
check: 4 files, 0 problem(s)
check rc=0
deleted 4 files, the folder and the manifest
delete rc=0
v.env
canary strings in that log: 0
