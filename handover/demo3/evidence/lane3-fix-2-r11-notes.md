# lane3 fix-2 round 11 (B22): notes

## FAILED / UNCERTAIN (first)
1. UNCERTAIN, mutant S2 SURVIVED: removing the `main_lock_handles_closed` fixture from the two `server_main` tests changes no test result in-process (the fixture only closes lock handles, so its absence leaves no failing signal). Row 4 is done by the two added marker lines; no test proves they are needed. Stated plainly, not claimed as proven.
2. NOT DONE: no real non-root run of the chmod-000 book-path case (row 17 stays escalated; this session is root). The parent-unreadable branch of `env_file_problem` is reached only by a test that makes `Path.stat` raise for the parent alone.
3. NOT DONE (lead order 08:01Z, listed OPEN-FOR-STACK-DOCS, no code or text changed): row 10 (Python-version words: the one comment that said "3.12 and later" now reads "3.11 to 3.13", checked as non-root on 3.11/3.12/3.13; no docs page repeats it), row 13 (helper dedupe in tests/support.py: `_doc`, `_make_link`, `KEY` x4, `REPO`/`POSIX`, key-file write idiom, local `server` re-imports), row 14 (`test_text_only_*` names, REGRESSION GUARD marker on r9:420/:407), row 15 (settings.md 114-115 wording for the device node and Windows). The docs pages also do not yet list the new "link" refusal (contract.md exit-4 list, limits/settings "folder, inside a file" lists): OPEN-FOR-STACK-DOCS.
4. Row 16 declined as in the resolve file (declared regression guards pass on any code); row 17 escalated (rule 2a/2b: needs a non-root account and owner/ACL checks).
5. No full test run (order). Other suites that touch links/paths were run once as a check: 1121 passed, 8 skipped (`raw` not saved as evidence file; log `/home/user/work/b22-logs/other-suites.log`).
6. One existing test changed meaning on purpose: `test_a_loop_of_links_is_never_a_traceback_in_any_of_the_five_file_settings` used to expect the loop to pass the setting read; it now expects one fixed refusal text naming the setting, no path (new behaviour of row 3).

## Rows
| Row | Status | Where |
|---|---|---|
| 1 stub race | FIXED | `tests/support.py` `RawStub` (count under a lock BEFORE `sendall`, `pause_after_send` knob); r7 uses it and waits with `wait_until`; proof test in r11; every other `.hits` user checked: only `tests/test_load_tools.py` `_Flaky` (counts before replying, no change) |
| 2 mutation log | DONE | `raw/b22-r11-mutation.log`: BASELINE x3 green (825 passed each); N2, N5, N7, S1, T1-T4 each KILLED-BY-TARGET with all failures listed; S2 survived (see above) |
| 3 dangling link / loop | FIXED | `envnum.env_file_problem` kind `link` (a few lines, one helper), text via `file_problem_text`; `desk.BOOK_PROBLEMS` derived from all kinds; `run_real_check`, `desk.book_problem`, `refuse_unusable_file`, `server.main` all route through it; tests in r11 (dangling, loop, loop in parent, dangling parent; folder/file link keep their answer; no file or folder created at the target; one line, no path, `EXIT_REFUSED`) |
| 4 lock fixture | FIXED (see UNCERTAIN 1) | r9, two marker lines |
| 5 twin docstring, parent branch | FIXED | r9 docstring; test with `Path.stat` patched for the parent only; `env_file_problem` docstring says the branch is practically unreachable |
| 6 umask toggle | FIXED | r8 reads the Umask line of `/proc/self/status` (skip with a reason elsewhere); no `os.umask` call left in tests except `tests/conftest.py` (the one place) |
| 7 sys.modules | FIXED | `support.fresh_script` (monkeypatch finalizer) used by r7, r9, r11 |
| 8 port | FIXED | path_walk uses `port_nobody_listens_on` (whole body inside the `with`) |
| 9 timing | FIXED | `STUB_IO_SECONDS`, `BLOCK_CHECK_SECONDS` (10 s) in support; the 0.2 s accept timeout is only the stop-flag poll |
| 11 live key docs claim | TRACED | `live_claude.py` reads at start and again at the first call; real test added in r9 |
| 12 repeat scan | FIXED | words derived from `KINDS` names plus token file; `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, build, dist, `*.egg-info` skipped; planted tests (T3 proves the derived part) |
| 10, 13, 14, 15 | OPEN-FOR-STACK-DOCS | lead order |
| 16 | DECLINED | | 
| 17 | ESCALATED | |

## Evidence (all under `raw/`)
- `b22-r11-fails-before.log`: r10 tree plus the r11 tests (support with the OLD stub order): 12 failed, 147 passed on r8/r9/r11. Classes: real behaviour (stub count one short, dangling/loop/parent link, desk start) = r11 tests; the four r9 `run_real_check` failures there are a scratch-copy gap (the old tree copy lacked the `fresh_script` import), not a behaviour claim.
- Lint of a clean `git ls-files` copy: `b22-lint-*.log`, all rc=0 (ruff check, ruff format --check, mypy linux and win32, bandit -ll, E501); head tree `77fa1c0d3aa1e50226f4b1d8501b8d82acb604e6` (`b22-r11-lint-head.txt`).
- `b22-r11-changed-run.log`: 9 changed or `.hits` files, three runs in a row, 778 passed, 2 skipped each. `b22-r11-guards-alone.log`: hygiene 31 passed; wall-clock/burst 47 passed.
- Patch `lane3-fix-2-r11-on-fix-1-r6.patch`, sha256 in `raw/b22-r11-patch-sha256.txt`; fresh clone of base + fix-1 r6 gives the same tree `77fa1c0d...`; 211 passed, 1 skipped on r8/r9/r11/path_walk there. Parts: `lane3-fix-2-r11-parts/` (delta r10 to r11, 3 files, each under 18 KB).
- Files changed vs r10: `src/lead_desk/envnum.py`, `src/lead_desk/desk.py`, `tests/support.py`, tests r6, r7, r8, r9, r11 (new), path_walk, settings_lane3. No docs changed.
- Mutation script: `/home/user/work/b22-mut3.py` (outside the repo).
