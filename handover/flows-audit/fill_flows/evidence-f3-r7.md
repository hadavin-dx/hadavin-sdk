# Evidence f3 round 7 (EVIDENCE RUNNER, raw, no judgement)

Date 2026-11-16. Target: snapshot .../scratchpad/snap-f3r7/ (fill_flows.py sha256 8aefe66fd3af6308..., test_fill_flows.py, README.md). Work copy /tmp/f3m7 (removed at the end).
NOTE: the live file handover/flows-audit/fill_flows/fill_flows.py was changed after the snapshot (mtime 10:54:17 UTC; it now has _warn_no_handle_path / _WARNED_NO_HANDLE_PATH, 57721 bytes). Everything below ran on the SNAPSHOT copy, not on that newer file.
NOTE: the tests find the demo folder through env FF_DEMO_DIR (default is HERE/../../demo, which does not exist for a copy under /tmp). Runs 1a used no FF_DEMO_DIR and no README.md in the copy: that is a setup miss of mine, shown for honesty; runs 1b are the real ones (FF_DEMO_DIR=/home/user/hadavin-sdk/handover/demo, README.md copied next to the files).

## 1. unittest (python -I -m unittest, in the copy)
1a (no FF_DEMO_DIR, no README): py3.11 rc=1, py3.12 rc=1, py3.13 rc=1; each 'Ran 157 tests ... FAILED (errors=83)' (FileNotFoundError: /demo/n8n-flows-real-v5). With FF_DEMO_DIR but no README: rc=1, errors=1 (test_old_python_is_refused_plainly_and_the_readme_names_the_same_version: README.md not found).
1b (final):
- python3.11 rc=0: Ran 157 tests in 17.932s  OK 
- python3.12 rc=0: Ran 157 tests in 19.069s  OK 
- python3.13 rc=0: Ran 157 tests in 18.208s  OK 

## 2. lint and security
- ruff check . (default config in the copy): rc=0 'All checks passed!'; with --config repo pyproject.toml: rc=0.
- ruff format --check . (default config, line-length 88): rc=1, '2 files would be reformatted' (fill_flows.py and test file; first diff: EXIT_INCOMPLETE and TOKEN lines wrapped). With the repo's pyproject.toml (line-length 100): rc=0, '3 files already formatted'. The copy has no config file of its own.
- bandit -ll -r . : rc=0. Raw head:
```
[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: None
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	running on Python 3.13.18
Run started:2026-11-16 10:48:59.249892+00:00

Test results:
	No issues identified.

Code scanned:
	Total lines of code: 3281
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 1
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 1
Files skipped (0):
```
(The log says 'No issues identified' while the metrics table shows 'Low: 1'; I did not look into this: -ll hides Low.)

## 3. suppression counts (grep -c)
fill_flows.py: noqa 0, nosec 0, type: ignore 0. test_fill_flows.py: noqa 0, nosec 0, type: ignore 0.

## 4. Mutants (25, python3.13, full unittest per mutant, FF_DEMO_DIR set, original restored after each; final copy equals snapshot byte for byte)
| # | mutant | result | failing tests (first 3) |
|---|---|---|---|
| 1 | manifest compare: hash equality always true | KILLED | rc=1 n_failing=2 first: test_check_compares_the_folder_with_its_manifest; test_check_refuses_a_pipe_in_the_place_of_a_listed_file_without_hanging |
| 2 | manifest compare: stray files ignored | KILLED | rc=1 n_failing=1 first: test_check_names_a_stray_file |
| 3 | manifest compare: missing file not counted | KILLED (rerun, see note) | test_check_compares_the_folder_with_its_manifest |
| 4 | marker: content compare always true | KILLED | rc=1 n_failing=1 first: test_check_refuses_a_renamed_or_copied_folder |
| 5 | marker/folder name (delete --no-manifest): foreign marker accepted | KILLED | rc=1 n_failing=1 first: test_no_manifest_refuses_a_marker_for_another_folder_or_format |
| 6 | 0700 check weakened (check) | KILLED | rc=1 n_failing=1 first: test_check_refuses_loose_modes_on_a_marked_folder |
| 7 | 0600 check weakened (check) | KILLED | rc=1 n_failing=1 first: test_check_refuses_loose_modes_on_a_marked_folder |
| 8 | 0600 check removed (delete --no-manifest) | KILLED | rc=1 n_failing=1 first: test_no_manifest_refuses_wrong_file_mode_folder_mode_and_owner |
| 9 | --tokens-only: placeholders still listed | SURVIVED | rc=0 n_failing=0 first:  |
| 10 | --tokens-only: banner never printed | KILLED | rc=1 n_failing=2 first: test_check_mode; test_tokens_only_refuses_a_not_ready_copy_and_says_placeholders_were_skipped |
| 11 | delete: strays removed without --remove-others | KILLED | rc=1 n_failing=3 first: test_refuses_extra_file; test_delete_no_manifest_keeps_a_file_the_manifest_does_not_list; test_delete_stops_at_a_stray_file_and_remove_others_takes_it |
| 12 | delete --remove-others: owner check dropped | SURVIVED | rc=0 n_failing=0 first:  |
| 13 | signals: SIGHUP handler not installed | KILLED | rc=1 n_failing=2 first: test_terminate_and_hangup_signals_clean_up_the_copy; test_a_stop_signal_is_reported_as_such_and_not_as_a_crash |
| 14 | signals: mask blocks nothing | KILLED | rc=1 n_failing=3 first: test_a_real_ctrl_c_during_creation_leaves_nothing; test_a_stop_held_during_the_removal_does_not_hide_a_finished_delete; test_stop_signals_are_held_back_while_the_folder_is_made_and_removed |
| 15 | cloud folder: match only whole-name equality | KILLED | rc=1 n_failing=1 first: test_cloud_synced_folders_are_refused_for_values_and_output |
| 16 | size cap: never triggers | KILLED | rc=1 n_failing=1 first: test_a_file_nested_too_deeply_or_too_large_is_refused_plainly |
| 17 | size cap: JSON limit raised to 64 MB | SURVIVED | rc=0 n_failing=0 first:  |
| 18 | $env detect: needs a word boundary | KILLED | rc=1 n_failing=84 first: test_hash_change; test_manifest_has_no_values; test_manifest_left_without_folder |
| 19 | $env glued (a$env, x.$env): only alnum counts | KILLED | rc=1 n_failing=1 first: test_a_token_glued_to_a_name_or_a_dot_is_not_filled |
| 20 | empty value treated as present | KILLED | rc=1 n_failing=1 first: test_empty_value |
| 21 | empty placeholder value substituted | KILLED | rc=1 n_failing=1 first: test_an_empty_placeholder_value_is_the_same_as_none |
| 22 | values file: O_NONBLOCK dropped | KILLED | rc=1 n_failing=1 first: test_values_file_pipe_is_refused_without_hanging |
| 23 | values file: S_ISREG check removed | KILLED | rc=1 n_failing=2 first: test_values_file_must_be_a_regular_file; test_values_file_pipe_is_refused_without_hanging |
| 24 | Ctrl-C exit code 130 -> 1 | KILLED | rc=1 n_failing=1 first: test_ctrl_c_ends_with_one_plain_line_and_code_130_and_cleans_up |
| 25 | excepthook prints exception text | KILLED | rc=1 n_failing=3 first: test_failed_write_removes_everything_and_manifest_goes_first; test_exception_text_is_never_printed; test_an_unexpected_error_on_the_command_line_shows_its_type_only |

Note on #3: my first version of this mutant only appended a comment and left 'bad += 1' in place, so it changed nothing (invalid, reported SURVIVED). Rerun with the line 'bad += 1' removed after 'listed in the manifest but missing': rc=1, killed by test_check_compares_the_folder_with_its_manifest.
Totals: 25 mutants applied, 22 killed, 3 survived (#9 --tokens-only still lists placeholders; #12 --remove-others owner check dropped; #17 JSON size limit raised 32 to 64 MB). Mutant #22 (O_NONBLOCK removed) was killed by a normal test failure (test_values_file_pipe_is_refused_without_hanging), no 240 s timeout.
Not covered by me: #9 and #12 survive because no test fails; for #12 a test would need a stray file owned by another user (I am root here, chown would work). #17: the 33 MB hand test (section 5) is refused at the right size, but no unit test pins the 32 MiB constant.

## 5. Hostile inputs by hand (made-up data; each command under timeout 60; raw rc)
Setup: /tmp/f3m7/h, copy of demo/n8n-flows-real-v5, values file mode 600 with 3 DESK_ keys + 6 placeholder names. Baseline fill rc=0 ('filled 4 files, 3 names and 6 placeholders'), baseline check rc=0 ('check: 4 files, 0 problem(s)'). First script run used a values file missing the placeholder names, so fills were refused with rc=1 (my setup miss); the table is from the corrected rerun.
```
### baseline fill good
rc=0
filled 4 files, 3 names and 6 placeholders
no placeholders left; run check before importing

### baseline check
rc=0
manifest compare: ran against base.manifest.json
check: 4 files, 0 problem(s)

1048577
### values file 1 MiB+1 byte
rc=1
refused: values file is larger than 1048576 bytes; nothing was done

1048576
### values file exactly 1 MiB (boundary)
rc=1
refused: mf-recovery.json: cannot fill these names (missing or empty in the values file, or not a DESK_/MF_ name): DESK_ALERT_TO

### 33 MB JSON flow file
rc=1
refused: a.json is larger than 33554432 bytes; nothing was done

### 33 MB JSON check
rc=1
manifest compare: not run (no fingerprint file next to the folder and no marker file: an input folder has neither)
a.json: a.json is larger than 33554432 bytes; nothing was done
check: 1 files, 1 problem(s)

### deeply nested JSON fill
rc=1
refused: a.json: not valid JSON (RecursionError)

### deeply nested JSON check
rc=1
manifest compare: not run (no fingerprint file next to the folder and no marker file: an input folder has neither)
a.json: a.json: not valid JSON (RecursionError)
check: 1 files, 1 problem(s)

### FIFO as values file
rc=1
refused: values file is not a regular file

### FIFO as flow file (fill)
rc=1
refused: input file a.json: symlink or not a regular file

### FIFO as flow file (check)
rc=1
refused: input file a.json: symlink or not a regular file

### symlinked --out folder (fill)
rc=1
refused: output folder or its manifest already exists (run delete --out on it first; add --force-hash if a kill cut the manifest short)

0
### output below symlinked parent
rc=0
filled 4 files, 3 names and 6 placeholders
no placeholders left; run check before importing

2
### cp -r copy with loosened modes then check
rc=1
mf-recovery.json: not mode 0600 and yours (a copy can loosen it; run chmod 600)
mf-sub-crm-mail.json: not mode 0600 and yours (a copy can loosen it; run chmod 600)
copied.manifest.json: not next to the folder, so the folder was NOT compared with it (a copied or moved folder, or the file was lost); it cannot be shown unchanged
check: 4 files, 7 problem(s)

### same, manifest copied too
rc=1
mf-recovery.json: not mode 0600 and yours (a copy can loosen it; run chmod 600)
mf-sub-crm-mail.json: not mode 0600 and yours (a copy can loosen it; run chmod 600)
manifest compare: ran against copied.manifest.json
check: 4 files, 6 problem(s)

### loosened modes but folder renamed (marker names other folder)
rc=1
mf-recovery.json: not mode 0600 and yours (a copy can loosen it; run chmod 600)
mf-sub-crm-mail.json: not mode 0600 and yours (a copy can loosen it; run chmod 600)
manifest compare: ran against base2.manifest.json
check: 4 files, 6 problem(s)

### loosen original in place then check
rc=1
the folder is not mode 0700 and yours (a copy can loosen it; run chmod 700)
mf-form.json: not mode 0600 and yours (a copy can loosen it; run chmod 600)
manifest compare: ran against base.manifest.json
check: 4 files, 2 problem(s)

### marker without manifest then check
rc=1
.fill_flows-output: does not name this folder (the folder was renamed or copied; fill again instead of copying)
mnm.manifest.json: not next to the folder, so the folder was NOT compared with it (a copied or moved folder, or the file was lost); it cannot be shown unchanged
check: 4 files, 2 problem(s)

### baseline fill for delete
rc=0
filled 4 files, 3 names and 6 placeholders
no placeholders left; run check before importing

### delete with stray .DS_Store, no flag
rc=1
refused: folder holds files not in the manifest: .DS_Store; nothing deleted (stray plain files of yours, such as .DS_Store, go with --remove-others)

.DS_Store
.fill_flows-output
mf-form.json
### delete with stray .DS_Store, --remove-others
rc=0
deleted 4 files, the folder and the manifest
also removed 1 other file(s): .DS_Store

ls: cannot access 'd1': No such file or directory
ls: cannot access 'd1.manifest.json': No such file or directory
### fill for no-manifest variant
rc=0
filled 4 files, 3 names and 6 placeholders
no placeholders left; run check before importing

### delete --no-manifest with .DS_Store, no --remove-others
rc=1
refused: .DS_Store: not a plain .json file; nothing deleted

### delete --no-manifest with .DS_Store, --remove-others
rc=0
deleted 4 files, the folder and the manifest
also removed 1 other file(s): .DS_Store

ls: cannot access 'd2': No such file or directory
--- part 2
ls pr (symlinked parent target):
o5
o5.manifest.json
### fill m1
rc=0
filled 4 files, 3 names and 6 placeholders
no placeholders left; run check before importing

### marker present, manifest removed, then check
rc=1
m1.manifest.json: not next to the folder, so the folder was NOT compared with it (a copied or moved folder, or the file was lost); it cannot be shown unchanged
check: 4 files, 1 problem(s)

### marker present, manifest removed, delete (no flag)
rc=1
refused: manifest is missing; nothing deleted (to remove the folder anyway, use --no-manifest: it removes only the marker, the not-ready note and .json files that look like this tool's output: mode 0600, yours, valid JSON)

### same, delete --no-manifest
rc=0
deleted 4 files, the folder and the manifest

10
--- signals (python driver, signal sent when the output folder held 3 entries, process alive)
### SIGINT mid-fill | signalled while alive: True | files seen in folder at signal: 3 | rc= 130
warning: key HS_CRED_PLACEHOLDER in the values file is not used by any node
warning: key INTAKE_ADDRESS_PLACEHOLDER in the values file is not used by any node
warning: key SMTP_CREDENTIAL_ID in the values file is not used by any node
refused: stopped by Ctrl-C; if a line above says something was left behind, run delete --out on that folder
left: [] folder content: None
### SIGKILL mid-fill | signalled while alive: True | files seen in folder at signal: 3 | rc= -9
warning: key FROM_ADDRESS_PLACEHOLDER in the values file is not used by any node
warning: key HS_CRED_PLACEHOLDER in the values file is not used by any node
warning: key INTAKE_ADDRESS_PLACEHOLDER in the values file is not used by any node
warning: key SMTP_CREDENTIAL_ID in the values file is not used by any node
left: ['s2', 's2.manifest.json'] folder content: ['.fill_flows-output', 'NOT-READY-DO-NOT-IMPORT.txt', 'f0.json']
### SIGTERM mid-fill | signalled while alive: True | files seen in folder at signal: 3 | rc= 1
warning: key HS_CRED_PLACEHOLDER in the values file is not used by any node
warning: key INTAKE_ADDRESS_PLACEHOLDER in the values file is not used by any node
warning: key SMTP_CREDENTIAL_ID in the values file is not used by any node
refused: stopped by a signal; if a line above says something was left behind, run delete --out on that folder
left: [] folder content: None
--- after SIGKILL
### check s2 rc=1
f9.json: listed in the manifest but missing
manifest compare: ran against s2.manifest.json
f0.json: f0.json: not valid JSON (JSONDecodeError)
NOT-READY-DO-NOT-IMPORT.txt is in the folder: fill left placeholders; do not import
check: 1 files, 26 problem(s)
### delete --out s2 rc=1
refused: f0.json: content changed since it was written (use --force-hash); nothing deleted
### delete --out s2 --force-hash rc=0
deleted 1 files, the folder and the manifest
```

Caveats on part 5: the first SIGINT attempt from bash was invalid (background jobs ignore SIGINT; fill finished normally rc=0) and an earlier SIGKILL at a fixed 0.8 s came before the folder existed; both were replaced by sig.py above. In the hostile.out block the 'baseline' / 'cp -r' sections come from the corrected rerun. In the first-pass fills the 'symlinked --out folder' case was refused because the target 'linkout' (a symlink) already exists (rc=1). 'output below symlinked parent' (--out linkparent/o5) returned rc=0 and wrote into the symlink target (pr/o5, pr/o5.manifest.json); I did not judge it.

## 6. What I could not run or did not do
- No run on the newer live fill_flows.py (changed after the snapshot).
- No Windows, macOS or WSL run; no non-root user (all runs as uid 0), so 'file owned by another user' cases were not exercised by hand.
- No full mutation run of the whole file; only the 25 listed mutants.
- Memory use of the 33 MB / nested-JSON inputs not measured.
- Bandit 'Low: 1' not investigated.
