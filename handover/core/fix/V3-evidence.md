# V3 EVIDENCE RUNNER results (raw logs in this folder; no judging)
Date 2026-11-13 12:57Z-13:25Z. Both trees head 61ded9e (patched, uncommitted). Patch RR/out/F3/fix.patch sha256 15c7e124c12718d1...; `git apply --check -R` on tree-V3 passes (V3 contains the patch); diff -rq V3old vs V3 = only the 8 patch files + new test.
lead_desk.__file__: tree-V3old -> /home/user/build/rr6/tree-V3old/src/lead_desk/__init__.py ; tree-V3 -> /home/user/build/rr6/tree-V3/src/lead_desk/__init__.py
Edit made: the new test file was copied into tree-V3old/tests (as the brief says; it is still there).

## FAILED / UNCERTAIN FIRST
- GAP FOUND (not fixed, I never fix): the live model key reader (live_claude.py `_read_key`, `f.read()` with no size cap) reads a whole regular file. A 100 MB sparse file as key file is ACCEPTED in V3 and V3old (key = 104857600 NUL characters, ~233 MB peak memory). The other four readers refuse it ("too big"/"too large"). Next step: cap the read like the smtp/hubspot readers and refuse NUL. On V3old, /dev/zero as live key file ran until the kernel killed it (exit -9, memory); V3 refuses it (regfile).
- The one-shot full run of 72 files (3305 tests) projected ~100 min on the shared 4-core box (4% after 4 min); I killed it (my own two processes) and ran the files one by one instead. Totals below are the sum of per-file runs, not one pytest session.
- Ruff with `--line-length 100` FAILS (E501 x366, I001 x1) on the 9 touched files; with the project's own pyproject (line-length 120) check and format --check pass. 366 E501 are mostly older lines of the same files (not split here by new vs old).
- DESK_PORT "12\n" is ACCEPTED (by design; the new test pins it).
- Not run: 30 test files (list in files-not-run.txt), two helper files collected as 0 tests (edge_case_helpers.py, support.py), playwright and gitleaks tests skip (no module/program).

## (1) FAILS-BEFORE (new test file on V3old, 42 tests)
run1 `-q -v` 39 failed 3 passed 41.2 s wall; run2 `-rA` 39 failed 3 passed 40.3 s. No hang (child 5 s limit). Passed on old code: test_bind_still_accepts_every_plain_spelling, test_hubspot_base_url_plain_text_still_works, test_a_number_with_a_trailing_line_end_stays_accepted_on_purpose. Per-test: V3old-per-test.txt.
## (2) PASSES-AFTER
| run | tree | file(s) | passed | failed | skipped | errors | wall | hang |
|---|---|---|---|---|---|---|---|---|
| 1 | V3 | new test file | 42 | 0 | 0 | 0 | 3.9 s | no |
| 2 | V3 | new test file | 42 | 0 | 0 | 0 | 4.3 s | no |
| 3 | V3 | new test file | 42 | 0 | 0 | 0 | 4.9 s | no |
| per-file x71 | V3 | existing files that match the grep (minus the new file, 2 helper files, 0 tests) | 3175 | 0 | 130 | 0 | 1162 s summed | no |
| per-file x71 | V3old | same files | 3175 | 0 | 130 | 0 | 1181 s summed | no |
Per-test comparison (PASSED/SKIPPED lines sorted, V3 vs V3old): identical, zero tests differ (per-test-V3.txt, per-test-V3old.txt). Each file under `unshare -n` + lo_up, TMPDIR=RR/tmp-V3, cap 300 s per file; slowest test_portal_api 118 s, test_take_script_refusals 123 s / 151 s. "Traceback" text appears only in captured server output of passing tests in test_crm_hubspot, test_fakes_body_before_answer, test_infra, identical on both trees.
Skips: gitleaks absent (27), playwright absent (75), root-can-read (1), py3.13 only (1), Windows only (1), load measurement (1), others.
## (3) LINT
ruff check pyproject config: All checks passed (ruff-check-projcfg.txt). ruff format --check pyproject config: 9 files already formatted. With `--line-length 100`: check 367 errors (366 E501, 1 I001 smtp_provider.py:24), format 8 of 9 would be reformatted. bandit -ll regfile.py: 0 issues (rc 0).
## (4) MUTATION (copy tmp-V3/mut, files: new test, test_bind_refusals, test_path_confinement, test_env_numbers, test_core_key_readers, pytest -x; each mutant restored and cmp'd ok)
| mutant | killed? | first error line |
|---|---|---|
| m1 drop O_NONBLOCK | YES | tests/test_special_files_and_plain_text.py:64: Failed: the approvers reader waited for ever on a named pipe |
| m2 drop S_ISREG check | YES | E   AssertionError: assert 'the approver...lid JSON text' == 'the approver...annot be read' |
| m3 drop NUL-path refusal | YES | E   ValueError: embedded null byte |
| m4 config.read_approvers plain open | YES | tests/test_special_files_and_plain_text.py:64: Failed: the approvers reader waited for ever on a named pipe |
| m5 SpendLedger._totals plain open | YES | tests/test_special_files_and_plain_text.py:64: Failed: the ledger reader waited for ever on a named pipe |
| m6 split_url accepts newline | YES | tests/test_special_files_and_plain_text.py:159: Failed: DID NOT RAISE SettingRefused |
| m7 Config accepts newline in DESK_BIND | YES | tests/test_special_files_and_plain_text.py:144: Failed: DID NOT RAISE SettingRefused |
| m8 refuse :: | YES | src/lead_desk/config.py:531: lead_desk.envnum.SettingRefused: DESK_BIND and DESK_FAKES_HOST must be plain ASCII text on one line, with no spaces |
m8 (refuse "::") is killed by test_bind_still_accepts_every_plain_spelling (1 failed, 22 passed). Only 8 mutants, first-failure stops (-x).
## (5) HOSTILE INPUTS (raw: hostile-raw.tsv for both trees; NUL cases: hostile-nul.txt; each under `timeout 20`; exit code is the harness exit, it catches the exception and prints its class and text)
V3 (patched): every file case exit 0, hang no, "Traceback" no, path/typed text echoed no.
| input | reader | V3 outcome | V3old outcome |
|---|---|---|---|
| approvers-file=fifo | | SettingRefused | the approvers file cannot be read (hang no, tb no, echo no) |  (rc 124, hang YES, tb no, echo no) |
| leadflow-file=fifo | | SettingRefused | DESK_LEADFLOW_FILE cannot be read (hang no, tb no, echo no) |  (rc 124, hang YES, tb no, echo no) |
| smtp-file=fifo | | SendRefused | the smtp password file cannot be read (hang no, tb no, echo no) |  (rc 124, hang YES, tb no, echo no) |
| hubspot-file=fifo | | CrmConfigError | the hubspot key file cannot be read (hang no, tb no, echo no) |  (rc 124, hang YES, tb no, echo no) |
| live-file=fifo | | LiveTransport | the key file cannot be read (hang no, tb no, echo no) |  (rc 124, hang YES, tb no, echo no) |
| approvers-file=symlink-to-fifo | | SettingRefused | the approvers file cannot be read (hang no, tb no, echo no) |  (rc 124, hang YES, tb no, echo no) |
| leadflow-file=symlink-to-fifo | | SettingRefused | DESK_LEADFLOW_FILE cannot be read (hang no, tb no, echo no) |  (rc 124, hang YES, tb no, echo no) |
| smtp-file=symlink-to-fifo | | SendRefused | the smtp password file cannot be read (hang no, tb no, echo no) |  (rc 124, hang YES, tb no, echo no) |
| hubspot-file=symlink-to-fifo | | CrmConfigError | the hubspot key file cannot be read (hang no, tb no, echo no) |  (rc 124, hang YES, tb no, echo no) |
| live-file=symlink-to-fifo | | LiveTransport | the key file cannot be read (hang no, tb no, echo no) |  (rc 124, hang YES, tb no, echo no) |
| approvers-file=/dev/zero | | SettingRefused | the approvers file cannot be read (hang no, tb no, echo no) | SettingRefused | the approvers file is too big (hang no, tb no, echo no) |
| leadflow-file=/dev/zero | | SettingRefused | DESK_LEADFLOW_FILE cannot be read (hang no, tb no, echo no) | SettingRefused | DESK_LEADFLOW_FILE is too big (hang no, tb no, echo no) |
| smtp-file=/dev/zero | | SendRefused | the smtp password file cannot be read (hang no, tb no, echo no) | SendRefused | the smtp password file is too large: it must hold only the password (hang no, tb no, echo no) |
| hubspot-file=/dev/zero | | CrmConfigError | the hubspot key file cannot be read (hang no, tb no, echo no) | CrmConfigError | the hubspot key file is too large: it must hold only the key (hang no, tb no, echo no) |
| live-file=/dev/zero | | LiveTransport | the key file cannot be read (hang no, tb no, echo no) |  (rc -9, hang no, tb no, echo no) |
| approvers-file=/proc/self/mem | | SettingRefused | the approvers file cannot be read (hang no, tb no, echo no) | SettingRefused | the approvers file cannot be read (hang no, tb no, echo no) |
| leadflow-file=/proc/self/mem | | SettingRefused | DESK_LEADFLOW_FILE cannot be read (hang no, tb no, echo no) | SettingRefused | DESK_LEADFLOW_FILE cannot be read (hang no, tb no, echo no) |
| smtp-file=/proc/self/mem | | SendRefused | the smtp password file cannot be read (hang no, tb no, echo no) | SendRefused | the smtp password file cannot be read (hang no, tb no, echo no) |
| hubspot-file=/proc/self/mem | | CrmConfigError | the hubspot key file cannot be read (hang no, tb no, echo no) | CrmConfigError | the hubspot key file cannot be read (hang no, tb no, echo no) |
| live-file=/proc/self/mem | | LiveTransport | the key file cannot be read (hang no, tb no, echo no) | LiveTransport | the key file cannot be read (hang no, tb no, echo no) |
| approvers-file=directory | | SettingRefused | the approvers file cannot be read (hang no, tb no, echo no) | SettingRefused | the approvers file cannot be read (hang no, tb no, echo no) |
| leadflow-file=directory | | SettingRefused | DESK_LEADFLOW_FILE cannot be read (hang no, tb no, echo no) | SettingRefused | DESK_LEADFLOW_FILE cannot be read (hang no, tb no, echo no) |
| smtp-file=directory | | SendRefused | the smtp password file cannot be read (hang no, tb no, echo no) | SendRefused | the smtp password file cannot be read (hang no, tb no, echo no) |
| hubspot-file=directory | | CrmConfigError | the hubspot key file cannot be read (hang no, tb no, echo no) | CrmConfigError | the hubspot key file cannot be read (hang no, tb no, echo no) |
| live-file=directory | | LiveTransport | the key file cannot be read (hang no, tb no, echo no) | LiveTransport | the key file cannot be read (hang no, tb no, echo no) |
| approvers-file=sparse-100MB | | SettingRefused | the approvers file is too big (hang no, tb no, echo no) | SettingRefused | the approvers file is too big (hang no, tb no, echo no) |
| leadflow-file=sparse-100MB | | SettingRefused | DESK_LEADFLOW_FILE is too big (hang no, tb no, echo no) | SettingRefused | DESK_LEADFLOW_FILE is too big (hang no, tb no, echo no) |
| smtp-file=sparse-100MB | | SendRefused | the smtp password file is too large: it must hold only the password (hang no, tb no, echo no) | SendRefused | the smtp password file is too large: it must hold only the password (hang no, tb no, echo no) |
| hubspot-file=sparse-100MB | | CrmConfigError | the hubspot key file is too large: it must hold only the key (hang no, tb no, echo no) | CrmConfigError | the hubspot key file is too large: it must hold only the key (hang no, tb no, echo no) |
| live-file=sparse-100MB | | ACCEPTED (hang no, tb no, echo no) | ACCEPTED (hang no, tb no, echo no) |
| approvers-file=NUL-in-path | file | SettingRefused | the approvers file cannot be read | ValueError | embedded null byte |
| leadflow-file=NUL-in-path | file | SettingRefused | DESK_LEADFLOW_FILE cannot be read | ValueError | embedded null byte |
| smtp-file=NUL-in-path | file | SendRefused | the smtp password file cannot be read | ValueError | embedded null byte |
| hubspot-file=NUL-in-path | file | CrmConfigError | the hubspot key file cannot be read | ValueError | embedded null byte |
| live-file=NUL-in-path | file | LiveTransport | the key file cannot be read | ValueError | embedded null byte |
| DESK_BIND=\n | | SettingRefused | DESK_BIND and DESK_FAKES_HOST must be plain ASCII text on one line, with no spaces (hang no, tb no, echo no) | ACCEPTED (hang no, tb no, echo no) |
| DESK_BIND=ESC | | SettingRefused | DESK_BIND and DESK_FAKES_HOST must be plain ASCII text on one line, with no spaces (hang no, tb no, echo no) | ACCEPTED (hang no, tb no, echo no) |
| DESK_BIND=fullwidth | | SettingRefused | DESK_BIND and DESK_FAKES_HOST must be plain ASCII text on one line, with no spaces (hang no, tb no, echo no) | ACCEPTED (hang no, tb no, echo no) |
| DESK_BIND=tab | | SettingRefused | DESK_BIND and DESK_FAKES_HOST must be plain ASCII text on one line, with no spaces (hang no, tb no, echo no) | ACCEPTED (hang no, tb no, echo no) |
| DESK_FAKES_HOST=\n | | SettingRefused | DESK_BIND and DESK_FAKES_HOST must be plain ASCII text on one line, with no spaces (hang no, tb no, echo no) | SettingRefused | DESK_FAKES_HOST (or DESK_FAKES_URL) must be this computer: localhost or a loopback ad (hang no, tb no, echo no) |
| DESK_FAKES_URL=space | | SettingRefused | DESK_FAKES_URL is not a valid address (hang no, tb no, echo no) | SettingRefused | DESK_FAKES_URL must not have a path (hang no, tb no, echo no) |
| DESK_FAKES_URL=CRLF | | SettingRefused | DESK_FAKES_URL is not a valid address (hang no, tb no, echo no) | SettingRefused | DESK_FAKES_URL has a bad port (hang no, tb no, echo no) |
| DESK_FAKES_URL=U+2028 | | SettingRefused | DESK_FAKES_URL is not a valid address (hang no, tb no, echo no) | SettingRefused | DESK_FAKES_URL has a bad port (hang no, tb no, echo no) |
| DESK_PORT=12\n | | ACCEPTED (hang no, tb no, echo no) | ACCEPTED (hang no, tb no, echo no) |
| DESK_PORT=1\n2 | | SettingRefused | DESK_PORT is not a number (hang no, tb no, echo no) | SettingRefused | DESK_PORT is not a number (hang no, tb no, echo no) |
Echo note: for the NUL path and file cases "echo" means the temp path text appeared in output; for settings it means the typed value appeared. All no on V3; DESK_* refusals print fixed texts only. Harness first sent the NUL path through argv and failed (Python cannot pass it); redone via hex (hostile-nul.txt).
## (6) Commands / files
Commands: see run.sh, perfile.sh, mutate.py, hostile.py, hostile_drive.py, nul.py (copies in this folder). Files not run: files-not-run.txt (30 files). Files run: files-run2.txt (71).
Processes at end: 0 of mine running. Scratch: RR/tmp-V3/mut and hostile files (100 MB sparse file RR/tmp-V3/hostile/sparse100m) remain, no worktrees made.
