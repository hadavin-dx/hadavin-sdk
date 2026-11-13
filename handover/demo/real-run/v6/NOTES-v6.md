# NOTES v6 (builder Q4h): which patch is which, what each touches in core, what was measured

Preamble rules used: 5, 6, 7, 11, 12, 13, 19, 20. The studio bible is not on this machine: no R-numbers were grepped, none are cited.
EGM skipped: I cannot invoke the egm:* skills here; the lead runs the independent reads (the lead's fresh read of v6, and the standalone read of
core-touches-3.patch). I did not review my own result as if it were EGM.
Hard rules kept: I never typed y, yes or a destination host at any question of the desk, the take script or the real-run script. Every script run and every
pytest run went through `unshare -rn` (loopback brought up by lo_up-q4g.py, the connect blocker sitecustomize-q4g.py logging every connect and name lookup).
The blocker log of the final test run: 12494 lines, 0 BLOCK lines. The only outside read was the clone of the public repository. No push, made-up data only.
One test (in p3, see below) used to answer `y` against the local fakes; I did NOT keep it: see "after sonar-p3".
Nothing was run on Windows. The whole 140-file suite was NOT run (the lead runs it): only the files named in evidence-q4h-tests-v6.txt.

## 1. Which patch is which (apply order)

| file in real-run/ | what it is | touches core `src/`? |
|---|---|---|
| `core-touches-3.patch` | ONLY the three core hunks of v5 (the three readers) and their tests (`tests/test_core_key_readers.py`). Applies on db54e13, 2db3926, 9c53207. For the lead's standalone safety read. | YES, 3 files, listed in section 2 |
| `real-run-fixes-v6.patch` | THE consolidated patch: v5 + start-prompt-hardening-v2 (merged by me) + the fixes of the fresh read of v5 + core-touches-3 (it contains those three hunks verbatim). Applies ALONE on db54e13, on 2db3926 and on 9c53207 (measured, section 6). | YES: exactly the same 3 files as core-touches-3 (checked: `git diff base v6 -- src` equals core-touches-3's src part) |
| `real-run-fixes-v6-rest.patch` | v6 minus core-touches-3, for a reader who has read core-touches-3 and applies it first: `core-touches-3` then `v6-rest` gives exactly the tree of `v6` alone (git write-tree compared). Scripts, tests, docs only. | NO |
| `desk-address-required-v6.patch` | THE BREACH-CLASS choke point, in its OWN patch, rebased on v6 (apply AFTER v6; it does not apply on the plain base). Omitted or blank DESK_HUBSPOT_BASE_URL / DESK_LIVE_BASE_URL are refused at start. | YES, listed in section 3 |
| `real-run-fixes-v6-after-sonar-p3-final.patch` | v6 resolved for use AFTER `sonar/sonar-p3-final.patch` (the P3 FINAL). | same as v6 |
| `real-run-fixes-v6-after-sonar-p3.patch` | v6 resolved for use AFTER `sonar-p3-path-helper-v3.patch` (older P3; not for p3-v2: its test file differs). | same as v6 |

Order if everything is taken: [p1-v3.2, p2-v2.1 (= 9c53207)], then v6 (or core-touches-3 then v6-rest), then desk-address-required-v6. With sonar-p3 FINAL: sonar-p3-final.patch, then
v6-after-sonar-p3-final, then desk-address-required-v6 (measured to apply, section 7).
Not part of the series any more (all replaced by v6): real-run-fixes-v5.patch, real-run-fixes-v5-after-sonar-p3.patch, start-prompt-hardening*.patch, desk-address-required*.patch (older). v6 replaces them.

## 2. Exact core touches: core-touches-3.patch (and therefore v6)

Class: the three readers of a one-line secret file all said the same thing, "holds no key", for an empty file, a too short key and a key with odd characters. The real-run
script needs to tell the person which of the three, before the start question. One of them (the live key) also had a real gap: a key of more than one line was accepted.

| # | file | function | exact change | why | behaviour change? |
|---|---|---|---|---|---|
| 1 | `src/lead_desk/live_claude.py` | `LiveQualifier._read_key` | (a) after the read and `strip()`: a key that still holds a line break (`\n` or `\r`) is refused with "the key file has more than one line: it must hold only the key"; (b) the old single refusal `len(key) < 8` -> "holds no key" is split: empty -> "holds no key", 1 to 7 characters -> "holds a key that is too short (at least 8 characters)". | the key goes into a request header; a second line was sent with it. The HubSpot and SMTP readers already refused more than one line. | YES, one: a key file with more than one line and at least 8 characters was accepted before and is refused now. Everything else the same (the short and empty cases are refused as before, only the text differs). The live key still does NOT get the HubSpot reader's "no inner spaces" rule (unchanged). |
| 2 | `src/lead_desk/crm_hubspot.py` | `HubspotCrm._key` | the single refusal `len(key) < 8 or any(c.isspace() or not c.isprintable() ...)` -> "holds no key" is split into three `if`s with three texts: empty / too short / "a key with spaces or unprintable characters". The checks keep their order and conditions. | the script's pre-question check shows which of the three | NO: what is accepted and refused is identical (measured, below). Only the text of the refusal. |
| 3 | `src/lead_desk/smtp_provider.py` | `read_secret_file` | the single refusal `len(secret) < 8 or not secret.isascii() or not secret.isprintable()` -> "holds no password" is split into three: empty / too short / "characters other than plain printable ASCII". | same | NO: identical accept/refuse (measured). Only the text. |

Tests (all in `tests/test_core_key_readers.py`, 12 tests, 1512 generated key files per reader from a fixed seed plus hand cases: BOM, UTF-16, invalid UTF-8, 4096 and 4097 bytes, CR, CRLF, NUL, no-break space, zero-width space):
* condition (b), the tests that FAIL on the old code: `test_the_reason_text_of_every_refused_key_file_is_the_new_fixed_text` (3 cases), `test_each_reader_has_three_different_texts_...`, `test_the_live_reader_refuses_a_key_of_more_than_one_line_that_is_long_enough`, `test_live_accept_and_refuse_equal_the_old_rule_except_a_key_of_more_than_one_line`, `test_the_set_of_texts_is_closed_...`: measured on the db54e13 source: 7 failed, 5 passed (evidence-q4h-fail-before.txt).
* condition (b), the "nothing else moved" pins, which PASS on old and new on purpose: `test_hubspot_accept_and_refuse_are_identical_to_the_old_rule_on_1512_key_files` and the smtp twin compare the real reader with a copy of the OLD rule written out in the test (an oracle): identical accept/refuse and identical accepted value on 1512 files (366 and 448 accepted, the rest refused, so both sides are exercised). The live twin expects the old rule minus the multi-line keys. These two cannot fail on the old code: that is their point (they say the old behaviour is unchanged); the mutants below show they fail when the new code moves.
* the same comparison with the REAL old code (not an oracle): `core-differential-q4h.py` runs the 1512 files through the db54e13 tree and the v6 tree and compares: hubspot: accepted by both 366, refused by both 1146 (text changed in 848), accepted only by old 0, only by new 0; smtp: 448 / 1064 (766) / 0 / 0; live: 582 / 833 (677) / only old 97 (the multi-line keys) / only new 0 (evidence-q4h-core-differential.txt).
* condition (c), no message holds key, secret, file name or folder: `test_no_message_holds_the_key_text_the_file_name_or_the_folder` (3 readers; every refusal of every generated file, the key text and its stripped form when 3 or more characters, the file name, the folder, the temp folder; a missing file names neither the path nor the OS error) and `test_the_set_of_texts_is_closed...` (over all 1512 files each reader says one of at most 8 fixed texts, so no text is built from the file). The first passes on old and new code (the rule is "never"); the second fails on the old code.
* mutants of the three hunks (section 5): all killed.
Condition (d): `core-touches-3.patch` is the standalone read (416 lines: 22 added and 3 removed lines of `src/`, and the test file).

## 3. Exact core touches: desk-address-required-v6.patch (its own patch, BEFORE nothing, AFTER v6)

Class: a default address that is the vendor's own. It passes the "vendor's own domain" check, so omitting the setting sent the key to the vendor with no refusal and no question.
Fix at the shared choke point (the settings classes, so every caller is covered: server, crash_desk.py, start_all, scripts, tests).

| file | function / place | exact change | why |
|---|---|---|---|
| `src/lead_desk/crm_hubspot.py` | `HubspotSettings.from_env` | an absent or blank `DESK_HUBSPOT_BASE_URL` -> `SettingRefused` naming the setting (the desk prints "the desk refuses a setting: ...", exit 4); docstring updated | the choke point for the desk, crash_desk.py and every script |
| `src/lead_desk/crm_hubspot.py` | `HubspotSettings.base_url` (field) | no default any more (required field); the import of `HUBSPOT_BASE_URL` is removed | Python code cannot omit it either. Separable: drop these two hunks for the smaller touch, then only the env reader refuses |
| `src/lead_desk/crm_hubspot.py` | `HubspotSettings.__post_init__` | a `%` in the host is refused (2 lines) | urllib and urlsplit read `https://evil.test%2f.hubapi.com` differently; the vendor-suffix check accepted it |
| `src/lead_desk/config.py` | `_live_from_env` | an absent or blank `DESK_LIVE_BASE_URL` -> `SettingRefused`; `kw` always carries the base url | same, for the model host |
| `src/lead_desk/config.py` | `LiveSettings.base_url` (field) | no default (required field) | same |
| `src/lead_desk/config.py` | `LiveSettings.__post_init__` | a `%` in the host is refused (2 lines) | same as above |
| `src/lead_desk/constants.py` | three comments only | the constants keep their values (they are still the vendor's own address for the host check, tests, examples) | wording |
| `docs/settings.md`, `contract.md` | text | the address is required | docs |

Tests: `tests/test_desk_address_required.py` (16 tests, new) and the edits of tests that relied on the default (`test_crm_hubspot.py`, `test_env_numbers.py`, `test_live_claude.py`, `test_ledger_amounts.py`).
On the v6 source without the core change: 13 failed, 3 passed (evidence-q4h-da-fail-before.txt; the 3 that pass are controls: a named address still works). The desk-process tests start a real desk child process and show it
exits 4 and connects nowhere. A tripwire test walks `src/` and fails if one of the three vendor constants is used anywhere but the live host check.
Behaviour change for existing private configs: a desk started with `DESK_CRM=hubspot` and no `DESK_HUBSPOT_BASE_URL` (or `DESK_QUALIFIER=live_claude` without `DESK_LIVE_BASE_URL`) now stops at start, exit 4.
Fix: name the address on purpose (the vendor's own, or a loopback address for a test).
v6 itself does NOT depend on it: the real-run script already refuses an unnamed address before its question (`unnamed_remote_default`).

## 4. What the fresh read of v5 found, and what v6 does about each (tests: tests/test_real_run_v6.py unless noted; "fail-before" = measured on m0 = v5 + start-prompt merged, evidence-q4h-fail-before-scripts.txt: 86 failed of 316)

| finding | fix | test |
|---|---|---|
| Major 1: FIXES.md said ONE core touch | three, listed in section 2 and in FIXES.md; the v5 text is corrected in FIXES.md | core tests above |
| Minor 2: DESK_DB_PATH whose folder is a regular file reached the question | `precheck.folder_part_is_a_file` (walks up to the first part that exists: must be a folder; a dangling link counts as not a folder); refused `refused: DESK_DB_PATH: a part of the folder path is a file, not a folder: the run folder cannot be made`, exit 2, nothing written | 3 spellings + dangling link + control (a new folder is still fine): folder snapshot before and after identical |
| Minor 3: keep_scan holes | CLOSED: `.format`, `%` (also with a tuple), a word assigned before `"--" + word` (also in the module or a class: names are resolved from the assignments), temp patch AFTER the run (order is checked), patch to `"/tmp"` / `tempfile.gettempdir()` / any name not built from `tmp_path`, `tmp_path_factory`, `tmpdir` (X must come from the test's own folder fixture), a decorator that is only called usefixtures (must end in `mark.usefixtures`), a local object or import or `with ... as monkeypatch` (monkeypatch must be the test's own parameter and not rebound), `_pieces` now in source order. DOCUMENTED, not closed: flags read from `os.environ` or a file, flags built by arithmetic (`chr`, `bytes([...])`, a reversed slice), the two flags put together by two different places. The test that reads every `.py` under tests/ still passes on the real suite. | 64 sample sources in `tests/keep_scan_cases.txt` (was 40), 17 of the samples fail on the old scan; `test_the_scan_reads_the_pieces_of_a_place_in_source_order` |
| Minor 4: live script refusal form | every refusal is ONE line `refused: <OPTION>: <fixed text>`, exit 2; the slot is the command-line option (the desk's DESK_LIVE_* names are shown as the option that fills them); a custom `RefusingParser` replaces argparse's own texts (they echoed the value); our argument types raise fixed texts; empty `--model` id / `--price-date` / `--effort` are named; the `--assume-yes` and no-terminal lines follow the form (`refused: standard input: ...` in BOTH scripts, which v5/start-prompt had left out) | 37 cases (a canary value in every option: never echoed), 6 argparse-error spellings, the no-terminal form in both scripts, a control that the good command line still runs |
| Nit 5: REAL_RESULT_FILE | refused when it is the same file as ANY other file or folder path the config names (every name ending in `_FILE` or `_PATH`) or the config file itself, also through a symlink or hard link (os.path.samefile, realpath for a path that does not exist yet); blank gives its own text; a pipe or device is refused | key file, password file (also spelled `./`), book path, config, symlink, hard link, blank, spaces, FIFO; each: folder snapshot before and after identical, one line, no path |
| Nit 6: a FIFO hangs | the real script refuses a pipe, device or socket (os.stat only, before anything is opened) for `--config`, every key / password / certificate / approvers / leadflow / replies file, the result file and, with `--live-model`, the live key and the ledger; the live script for `--key-file` and `--ledger` | 9 + 1 + 1 + 1 tests, each under a 15 second watchdog that frees the pipe (on the old code: every one fails with "it hung on a pipe") |
| Nit 7: wording | settings.md first paragraph now names all the secret files that are opened late; the comment in `_read_key` says "one line only, as in the HubSpot and SMTP readers (their other rules differ)"; the test `..._exits_1` is renamed `..._exits_3`; the "y/N" wording left in docs, help texts and comments is now "start question" (the question is a typed host, never y) | grep shows no `y/N` in scripts, tests, docs |
| Nit 7: `--leads 99999999999` allocates until killed | `--leads` 1 to 1000, `--runs` 1 to 100 (named constants, documented); not asked for in the brief: I added it because rule 5 says fix, and it is one `if` per option | the 37 cases include 99999999999, 1001, 0, 101 |
| Nit 7: bandit | measured 9 low, 0 medium, 0 high on db54e13 and on v6 (FIXES.md said 4 in v3, v4 and v5: wrong) | evidence-q4h-lint-mypy-bandit.txt |

## 5. Failures first (what went wrong or is not covered)

1. v4 and v5 FAILED an existing test that nobody ran: `tests/test_portal_wording_and_masking.py::test_no_first_person_plural_in_comments_of_the_listed_files` (a comment in `scripts/run_real_check.py` said "we do"). It was in v4 and v5 (`git show v4:scripts/run_real_check.py | grep -nE '\b(we|our|us)\b'`). Found when I ran the test file for the first time on the merged tree; fixed in v6 (one comment). The earlier evidence lists did not include that file.
2. Merging v5 with start-prompt-hardening-v2 by `git merge` (v4 as the common base): ONE textual conflict (docs/settings.md, resolved by keeping both blocks, taking v5's detail and start-prompt's "start question"), and one test (`test_an_unreplaced_or_odd_mailbox_host_...`) failed semantically: the start-prompt test expected the old v4 wording of the mailbox refusal; v5's form `refused: <SETTING>: <text>` wins, the test text was changed. The five test edits of NOTES-start-prompt-v2.md were all found in the merged `test_take_script_refusals.py` (checked by grep: fixture, `--assume-yes`, `DESK_LIVE_BASE_URL` in `_live_lines`, no piped `y`, "To start" text).
3. My first test file failed the hygiene scan (literal addresses) and then gitleaks (an address with a user and password in it): rebuilt from parts and without the password. The scan runs on a clean clone of the public repo (running it in my working clone found my own earlier commits in the history, which is not what CI scans).
4. Two existing tests in `tests/test_ledger_amounts.py` pinned the old argparse behaviour (text in stderr, `SystemExit`); changed to the new one-line form. That is a deliberate change of those two tests.
5. I wrote early on that sonar-p3-final.patch did not exist: wrong (see section 7). Windows was NOT run. `terminal_guard._windows_console_input` was not run (see NOTES-start-prompt-v2.md failure 1); precheck.py uses only os.stat (no Windows-only call) and `os.mkfifo`-based tests are skipped there.
6. One v6 test ends differently on a user namespace: p3's `test_v1_anywhere_reads_a_config_below_a_traverse_only_folder_as_an_unprivileged_user` needs `os.setuid` (EINVAL inside `unshare -rn`); same as the earlier fresh read; not caused by v6 (a test of p3).
7. `run-dry-checks.sh` (the studio harness, outside the repo) was NOT run and still expects the v4 exit codes and texts (see NOTES-start-prompt-v2.md); it must be updated by whoever owns it.
8. What the checks before the question still do NOT cover: relative paths (the script looks at a relative key path from its own folder, the desk child process starts in the repository folder); a path that changes between the check and the use; permission and free space; a regular file on a stalled network share; a FIFO opened by the desk itself later (core: the desk opens the key file at its first call; only the script protects its own run).
9. A program that drives a pseudo-terminal and types the host is not stopped (start-prompt limit 2, unchanged).

## 6. Measurements (files in this folder)

| what | result | file |
|---|---|---|
| tests on the v6 tree (12 files, under unshare + blocker, NOT the whole suite) | 1097 passed | evidence-q4h-tests-v6.txt |
| fail-before, core readers (db54e13 source) | 7 failed, 5 passed (pins) | evidence-q4h-fail-before.txt |
| fail-before, scripts (m0 + new tests) | 86 failed, 230 passed (of 316 selected; 2 deselected) | evidence-q4h-fail-before-scripts.txt |
| fail-before, desk-address-required-v6 | 13 failed, 3 passed (controls) | evidence-q4h-da-fail-before.txt |
| differential, real old code vs new code, 1512 key files x 3 readers | see section 2 | evidence-q4h-core-differential.txt |
| ruff check, ruff format --check, mypy linux and win32 (28 files), git diff --check, bandit -ll | all clean; bandit 9 low / 0 medium / 0 high (the same 9 on the base) | evidence-q4h-lint-mypy-bandit.txt |
| hygiene + gitleaks exceptions with gitleaks 8.30.1, DPLD_REQUIRE_SCAN=1, `git add -A`, clean clone of the public repo | 59 passed; `gitleaks dir`: no leaks | evidence-q4h-hygiene-gitleaks.txt |
| mutants (start-prompt 23, R1-R20, S1-S12, new K1-K15, C1-C9, N1-N20) | all killed after the re-runs; 4 first-pass survivors explained (1 equivalent, 3 fixed by added tests); K6/K10 only together | evidence-q4h-mutants.txt |
| apply matrix (3 bases x v6 / core-touches-3 / v6-rest / + desk-address-required-v6; p1+p2; p3-v3; p3-final; expected failures shown) | all expected OK, expected FAIL shown as such | evidence-q4h-apply-matrix.txt |
| desk-address-required-v6 on top of v6 (15 files, under unshare + blocker, not the whole suite); lint, mypy linux+win32, bandit, hygiene + gitleaks on that tree | 1177 passed; all clean; bandit 9 low | evidence-q4h-da-tests.txt, evidence-q4h-hygiene-gitleaks.txt |
| v6 after sonar-p3-final (12 files) | 1207 passed, 1 failed (setuid test, namespace artefact, not run outside) | evidence-q4h-tests-p3final.txt |

Applies on 9c53207 (= db54e13 + sonar-p1-quickwins-v3.2 + sonar-p2-regex-http-bug-v2.1): measured with `git apply --check` and `git apply`; the tree of p1 + p2 on db54e13 is identical to commit 9c53207 (write-tree compared). Tests were not run on a 9c53207 tree.

## 7. After sonar-p3 (P3 FINAL = `sonar/sonar-p3-final.patch`, which exists; I first thought it did not: a slip of my `ls | grep`, found later)

Plain v6 conflicts with p3-v2, p3-v3 and p3-final. With p3-v2 and p3-v3: in ONE place, the `--config` block of `_run` (the lines of v4, v5 and start-prompt inside it conflict, not v6's own).
With p3-final the same idea moved: p3-final puts the path check inside `load_env` (`config = confine_anywhere(path, what="--config")`), and that hunk conflicts with v5's "config file is not UTF-8 text" handling of the same function.
In both I kept v6's own new `--config` check (a pipe) OUT of those places (it sits at the top of `_run`, with a comment), so the conflicting hunks are only the inherited text.
* `real-run-fixes-v6-after-sonar-p3-final.patch` (for `sonar-p3-final.patch`): `load_env` calls `confine_anywhere` first, then reads with the UTF-8 refusal of v5; `tests/test_path_confinement.py`: an autouse terminal fixture, the new wording "not set in the config file", and
  `test_a_real_run_with_every_path_outside_the_allowed_folders_...` now stops at the question with `n` instead of running the whole run (a run now needs the destination host typed; I will not type it and no test should script it). Coverage lost: the end-to-end run with a config and book outside the allowed folders.
  Measured on p3-final + this patch (under unshare): `tests/test_path_confinement.py` 226 passed, 1 failed, 1 skipped; the one failure is the unprivileged-user test (`os.setuid` EINVAL inside the namespace); I was not allowed to run that one outside the namespace, so it is NOT run. The other test files on that tree: see evidence-q4h-tests-p3final.txt.
* `real-run-fixes-v6-after-sonar-p3.patch` (older, for p3-v3): the `--config` block uses `load_env(confine(...))` inside the try; same test edits. Measured on p3-v3 + patch: `tests/test_path_confinement.py` 150 passed, 1 failed (the same unprivileged-user test), 1 skipped. The rest of the suite was not run on that tree.
* Both apply with `git apply` on db54e13 plus their p3 (evidence-q4h-apply-matrix.txt); plain v6 after any p3 does not (expected, shown).

## 8. Rung table (CODE-LAST)
| component | need | rung tried | verdict |
|---|---|---|---|
| refusal before the question for pipes | do not hang on a typo | `os.stat` + `stat.S_IS*` (stdlib) | KEEP: 30 lines, a safety guarantee (no hang before the start question) |
| same-file check for the result file | do not overwrite a key | `os.path.samefile` (stdlib) + realpath | KEEP |
| live script argument form | one fixed refusal form | argparse subclass overriding `error` (stdlib) | KEEP: small |
| keep_scan | tripwire for a test hygiene rule | none free | KEEP as a tripwire in tests only; the behaviour test carries the guarantee |
| core readers' split texts | tell the person which of three reasons | none | KEEP-CODE: 22 lines, listed above |
Token use: not measured.
