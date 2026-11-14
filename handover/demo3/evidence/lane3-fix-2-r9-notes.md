# Lane 3 fix-2 round 9: builder notes (B22)

Plan: `resolve-lane3-fix-2-r8.md`, rows 1-19. Inputs: the r8 design review, the r8 code-details review and `lint-lane3-fix-2-r8.md`.
Tree before: `812a97afc9b6af5e869871c13076404bc6ac62f4` (checked). Tree after: `151f9eff50eb3a4a523cba11fcf1dd811e448719`. Nothing was committed or pushed.

## What failed or is weak (read first)
1. Row 3 is NOT decided here. The mode refusal stays exactly as it was (any group or other bit is refused, no switch). Only wording and docs changed. The lead must take the owner-level choice: (a) keep the refusal (the builder recommends this), (b) add an owner check, (c) add an explicit setting that allows looser modes.
2. The plan said "exit 8" for a refused book path. The real exit code is `EXIT_REFUSED` = 2 (one line `refused: ...`). The tests use `mod.EXIT_REFUSED`.
3. The chmod-000 test (row 4) is SKIPPED here because the session runs as root. Its code path is covered by a twin test that monkeypatches `path_kind` to "unreadable" (it runs as root), and by mutant M14. A real non-root run was not done: `useradd` was refused by the session's permission check and I did not retry it.
4. The line in `checkpoint-b22.md` that said "a monkeypatched twin runs" was wrong when written (the twin did not exist yet). Mutant M14 exposed it; the twin was added afterwards. The checkpoint now carries the correction.
5. The fails-before log (`raw/b22-fails-before.log`) was run before the twin test and before two small docs wording edits; its counts are 79 failed, 720 passed, 1 skipped, 0 function-absent. The final run of the changed files is 836 passed, 1 skipped.
6. First hygiene run on the final tree FAILED: the text "/mnt/c" in `docs/settings.md` and in the r9 test is a hardcoded-path hit. Fixed (reworded to "a Windows drive seen from WSL"); the hygiene test now passes (`raw/b22-guards-alone.log`). A second hygiene failure was only my PATH (gitleaks lives in `priv/gitleaks-bin/x`); not a code issue.
7. The repeat scan (row 1) only flags lines that mention a key-file word AND one of the rule words. Reason: contract.md lines 116, 138, 165, 249 and limits.md line 128 use "4096", "byte-order" or "symbolic link" in unrelated contexts. This is a tripwire, not proof.

## Not checked
No full test run (brief rule). Windows. Docker and Kubernetes behaviour (the docs say "not tried by the author"; it is reported, not tested). No EGM skill was invoked by me: the lead runs the EGM review of this result.

## Rows
| Row | Done | Evidence |
|---|---|---|
| 1 | Docs: the rule is written once (section "Key and password files" of `docs/settings.md`); contract.md, settings.md lines 75/82/131, limits.md, n8n-recipe.md, real-services.md point to it. Pin rewritten around `_repeats_of_the_rule` with planted and leave-alone tests (r8). | r8 docs pin tests; mutation M5-M7 |
| 2 | No code. The 13 base lines over 120 are fine: `ruff check --select E501` rc 0. | `raw/b22-lint-e501.log` |
| 3 | Escalated, behaviour unchanged. Docs now give the true reason (mode alone says who else can use the file; owner not checked) and the mounts that fail. The wrong "shared service account" reason is deleted. | `test_the_docs_do_not_give_the_wrong_reason...` (r9); M8 |
| 4 | Behaviour tests in r9: `run_real_check` with a book path inside a file (exit `EXIT_REFUSED`, one line), the chmod-000 variant (skips as root), and the root-safe twin. | M14 killed |
| 5 | `ruff format` applied to r7 and docs_claims_lane3 (format-only change for the second). | `raw/b22-lint-ruff-format.log` rc 0 |
| 6 | `import sys` removed. | `raw/b22-lint-ruff-check.log` rc 0 |
| 7 | Message is "the {what} file can be used by other users: run chmod 600 on it"; docs say "Linux, macOS and other POSIX systems"; write and execute bit tests added (r9). | 66 refusal-text tests fail on the old code |
| 8 | One docs sentence on mounts (Docker file secrets, Kubernetes secret volumes, filesystems that report 0777): copy to a regular file on a normal disk and run chmod 600. | r9 docs test |
| 9 | The 22 old-code passes are listed below; three tests carry a "REGRESSION GUARD" docstring; the order test is renamed `test_the_mode_refusal_has_no_way_round_in_the_signature`; new `test_the_link_and_kind_refusals_come_before_the_mode_refusal`. | below |
| 10 | `BOOK_IS_FOLDER_PROBLEM` and `BOOK_FOLDER_IS_FILE_PROBLEM` deleted; `desk.py` builds its texts from `file_problem_text`. | r9 lead-book test |
| 11 | Guard widened (`MODE_RULE_WORDS`: S_IRWXO, S_IRWXG, S_IMODE, `st_mode &`, `stat.S_I...`), planted-case test, and tests that a world-readable live key and the fake model server's key are refused. Tripwire, not proof. | M3, M4 killed |
| 12 | Plain words: named pipe, device, symbolic link and `chmod 600` explained once; "read at start and again before every call" in one sentence; contract.md exit-1 sentence split. | r9 wording pins |
| 13 | CONTESTED, no change: `live_claude.py` lines 16 and 480 only report `retry_after`; `crm_hubspot.py` lines 362-364 are bounded by the call deadline. | read by diff |
| 14 | CONTESTED, no change beyond row 6; the lint venv is the check. | lint logs |
| 15 | Two tests: bad key file with the smtp sender exits before any network call; the timing wrapper (`TracedCrm`) still refuses at start. | r9 |
| 16 | Done: doubled "* *" bullet, duplicate mode (now 0o700), `portal_demo` imports `retry_after_seconds` from `lead_desk.envnum`, `real-run.env.example` says chmod 600. DECLINED parts: merging the three spy-open-flags tests and the duplicate `_make_link` helper (no behaviour gain; a merge would hide which flag broke). | diff |
| 17 | `_names_own_file` is strict (only `Path(__file__)`, its `.parent` or `.parents[n]`); five planted probes and a leave-alone test added. | M17-M19 |
| 18 | `port_nobody_listens_on()` in `tests/support.py` holds a bound, non-listening socket for the whole block; the unreachable-servers test uses it. `free_port` import removed. | r9 held-port test |
| 19 | DECLINED as planned (test naming rule only; stack-docs owns wording). | none |

## The 22 tests that pass on the old (r7/r8) code (regression guards, by design)
18 x `test_a_key_file_only_its_owner_can_read_is_accepted_for_every_kind` (6 kinds x modes 384_0, 256, 384_1; the third mode is now 0o700), plus `test_a_zero_inode_number_does_not_stop_a_plain_file`, `test_the_file_is_opened_without_following_a_link`, `test_the_link_and_mode_rules_live_only_in_the_one_reader`, `test_the_copies_agree_with_the_one_reader_on_every_text_to_four_characters`. Earlier notes said 21; two tests were added after that count.
Other tests that pass on the old code by design: the smtp no-network test, planted-case tests of the tripwires, the `run_real_check` book tests, the held-port test. Rows 4, 11 and 17 are proved by mutation.

## Lint (clean copy of the final index, `raw/lint-head.txt` has the tree id)
ruff check, ruff format --check (no cache), mypy linux, mypy win32, bandit -ll, ruff E501: all rc 0. Logs: `raw/b22-lint-*.log`.
## Runs
Changed test files (6): 836 passed, 1 skipped, rc 0 (`raw/b22-changed-run.log`). `test_hygiene_scan_public` (DPLD_REQUIRE_SCAN=1, gitleaks on PATH): rc 0. Wall-clock guard: rc 0 (`raw/b22-guards-alone.log`, each alone).
## Mutation
`raw/b22-mutation.log` (a re-run on the final tree). The first pass had M3 and M4 "killed" only by a NameError, M8 killed by an unrelated test, and M14 surviving; all four were fixed and re-run and are killed by the intended test (M3, M4: `test_the_link_and_mode_rules_live_only_in_the_one_reader`; M8: the r9 owner-check-reason test; M14: the r9 twin test). The tree was restored after each mutant.
## Patch and parts
`lane3-fix-2-r9-on-fix-1-r6.patch` applied to a fresh clone of base + fix-1 r6 (tree `ad6060d...`) gives tree `151f9eff50eb3a4a523cba11fcf1dd811e448719`, same as the worktree (`raw/b22-patch-sha256.txt`). Review parts (r8 to r9 delta, each under 35 KB): `lane3-fix-2-r9-parts/`.
