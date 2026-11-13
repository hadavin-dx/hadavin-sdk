# REVIEW real-run v6 (after sonar-p3-final), fresh reader

Target: /tmp/demo-push/handover/demo/real-run/real-run-fixes-v6-after-sonar-p3-final.patch, sha256 9fc11e9ac19b3279f76241555fe9e0531f0b98c4e97291e55207e9d46c19eead (checked).
Base: main 61ded9e (fresh clone /tmp/work/rv6). `git apply --check` and `git apply` of the variant: OK. Core hunks not re-reviewed.
Preamble rules used: 5, 6, 7, 11, 12, 13 (the lead runs EGM), 19, 20. The studio bible is not on this machine: no R-numbers cited.

## Verdict: CLEAN for the guarantee class (no Blocker, no Major). 9 Minors and 2 Nits are listed; the lead decides which to fix.

I never answered y/yes and never typed a destination host at any prompt. The only answers given at the real-run start question were `n` (one pty run under `unshare -rn`).
Every run was under `unshare -rn` with loopback up and the connect blocker (sitecustomize logging every connect and name lookup).
Blocker logs: tests run 1 (358 tests): 286 lines, 0 BLOCK; combined run on variant + desk-address-required-v6: 1994 lines, 0 BLOCK; the harness runs: 0 BLOCK.
Settings used by my own scripts/harnesses: every URL loopback (`http://127.0.0.1:9` with `DESK_HUBSPOT_ALLOW_ANY_BASE_URL=yes`, mail hosts `localhost`). The repo's own tests build configs that name the vendor's HubSpot address as text; they only reach the question with a mocked `n` or an input that fails the test, and ran under unshare + blocker.

## Not run / not verified
* Windows: nothing run (GetConsoleMode path is code-read only).
* `test_v1_a_config_below_a_traverse_only_folder_is_refused_with_a_message_as_an_unprivileged_user` fails inside the user namespace (`os.setuid` EINVAL), as the builder said; NOT run outside. Not caused by v6.
* The whole suite was not run (lead's job). Run: 14 files (see section 8), 1 namespace failure, 1 failure that was MY harness slip (git gpgsign not overridden in that call); re-run of tests/test_hygiene.py + test_gitleaks_exceptions.py with the override: all passed.
* The studio harness `run-dry-checks.sh`: not run.

## 1. The choke point (stdin must be a terminal)
Scripts that ask a question: exactly two, `scripts/run_real_check.py` and `scripts/run_live_check.py`, both through `terminal_guard.ask_to_start(host, ...)`. Sweep of scripts/, tools/, load_tools/, src/ for `input(`, `sys.stdin`, `readline`, `getpass`, `msvcrt`, `isatty`: only terminal_guard.py calls `input()`. `load_tools/catcher.py` readline is a network stream, not stdin. reset.sh/start_all.sh/.ps1 have no prompts. `hubspot_probe.py` has no prompt but a flag confirmation (see Minor 9).
Measured (script run, config loopback, exit codes): stdin from a pipe with `n`, /dev/null, closed (`<&-`), a regular file, a FIFO with a writer, /dev/zero: all refused, exit 2, one line `refused: standard input: it is not a terminal ...`, nothing read. `--config` as a FIFO, a symlink to a FIFO, /dev/null, /dev/zero, a unix socket (with a pty stdin so the stdin check passes): all `refused: --config: not a regular file ...`, exit 2, nothing opened.
Way around terminal_guard: a pty IS accepted. `printf 'n\n' | script -qec "python scripts/run_real_check.py --config C" /dev/null` (under unshare) reached the question and stopped on `n` (measured). So a pty driver that types the host would start the run. What stops a pty-driven `y`: `ask_to_start` compares the typed text to the destination host, and `y`, `yes`, `n`, `no`, empty are refused as the word itself (ValueError, fail closed). A pty-driven host is out of the tests' scope: no test types a host (grep of tests: every mocked `input` returns `n` or fails the test; one returns `y` but the run is refused before the question, see Minor 7). It is the documented limit 2 of NOTES-start-prompt-v2. isatty lies (a replaced `sys.stdin`) need code execution in the process; the scripts do not run in isolated mode, so a `sitecustomize`/PYTHONPATH on the environment is the same class: out of scope.
Windows (code read): `stdin_is_terminal` = `isatty()` AND `GetConsoleMode(handle)`; closed handle -> OSError from get_osfhandle -> caught -> False; `sys.stdin` None -> AttributeError -> False; NUL passes isatty on old runtimes but fails GetConsoleMode. Logic is sound; the call itself is unrun.
Result: no bypass for a `y`. Host-typed-by-pty is the accepted limit.

## 2. Refusal texts and exit codes
Own fuzz, 216 command lines against `run_live_check.main` (canary in every option, in 18 shapes: bad numbers, nan/inf/1e999, NUL, userinfo, bad port/bracket, `%2f`, 500-char): no refusal repeats the canary; every exit-2 refusal is exactly one stdout line, nothing on stderr. The only echo of a typed value is `--price-date` in the cost banner after all refusals (not a refusal). Own fuzz of `run_real_check` with canary content in the HubSpot key, SMTP password, mailbox password (8 shapes each: space, short, 2 lines, non-ASCII, empty, tab, invalid UTF-8, 100 KB) and in the leadflow, replies, approvers and CA files (5 shapes each): 0 leaks of content or folder, one line each, exit 2.
Exit codes in code and docs agree: refused 2, stopped 1, failed 3, book path 4 (docs/settings.md lines 116-123 read).
Findings: Minor 1 (run_real_check argparse errors still echo the value, two lines, stderr).

## 3. Pipes, same file, caps
* `--config`, every key/password/CA/approvers/leadflow/replies file, result file, live key and ledger, live `--key-file`/`--ledger`: refused by `os.stat` before opening (above, and tests: 9+1+1+1 pipe tests pass).
* REAL_RESULT_FILE (own harness, in-process, folder snapshot before/after identical for every case): key file, key via `d/../d/hub.key`, symlink to key, hard link to key, hard link to password file, the config itself, a dangling symlink whose target is DESK_DB_PATH, DESK_DB_PATH itself: all refused `the same file as <NAME>`; blank and spaces: own text; FIFO, /dev/null, a folder: refused. A dangling link to a missing folder reaches the question and fails softly at write (write_result catches OSError): fine.
  Not refused (Minor 4): REAL_RESULT_FILE equal to `<run>/desk-1.log`, `<run>/crash.flag`, `<db>-wal`: files the run itself makes inside the run folder.
* `--leads` 1..1000, `--runs` 1..100: they are above the defaults (12 and 3); the only documented use is docs/settings.md line 122 (the caps themselves). No doc, test or script uses a larger number: documented use is not broken. Boundary is not tested (Minor 5).

## 4. DESK_DB_PATH parent is a file
Own cases, all exit 2 with the one fixed line and a tree snapshot unchanged: parent a file, folder part a file (sub, deeper), dangling link, link to a file, parent a FIFO; a path that is already a folder: "names a file that already exists". Gap (Minor 2): `afile/../x/desk.db` is lexically collapsed by `os.path.abspath` so `folder_part_is_a_file` says no, the script reaches the question, and `run_dir.mkdir` (unchanged `db.parent`) then raises NotADirectoryError after the question: traceback with exit 1, before any desk or real call (measured: mkdir raises). Also a relative DESK_DB_PATH reaches the question (documented limit 8).

## 5. keep_scan: 8 source shapes it wrongly accepts, 5 it wrongly rejects (own run, /tmp/work/rv6-t/ks.py)
Wrongly ACCEPTED (leak missed): S1 `monkeypatch.undo()` between the patch and the run; S2 a patch value that mentions `tmp_path` but is `None if tmp_path else None`; S16 patch to `str(tmp_path.anchor)` ("/"); S3 child process with an unrelated string containing `TEMP`/`TMP` (the regex is a substring search: "ATTEMPT" passes); S4 child started with `asyncio.create_subprocess_exec` (not in `_CHILD_NAMES`) and patch only; S5 flag built by `chr` (documented); S6 flags from `os.environ[...]` (documented); also not read: a patch placed in a nested helper.
Wrongly REJECTED (false alarm, conservative): S7 class-level `usefixtures`; S8 module `pytestmark = usefixtures(...)`; S9 `with monkeypatch.context() as m: m.setattr(...)`; S12 a helper called by a test that owns the fixture; S15 `request.getfixturevalue("own_tempdir")`; also S13 patch inside try/finally.
Judgement: a tripwire only (the builder says so); none of the false accepts is in the real suite (the scan of every tests/*.py passes). Minor.

## 6. Loss of the end-to-end test after P3
The deleted test was the only test in the suite (also on 61ded9e) that ran `run_real_check.main(["--config", ...])` to the end (clean base: `git grep` shows one). Now NO test runs a config-driven run past the question. What remains: `test_dry_fakes_run_end_to_end` and 5 other `--dry-fakes --assume-yes` runs (post-question code, but `--config` is ignored there), plus the pre-question tests (the config outside the allowed folders reaches the question and the book is readable: `..._reaches_the_y_n_question_and_the_book`, and the renamed `..._reaches_the_question`). `confine_anywhere` is called once (line 746, `load_env`), nothing after the question calls the jail, so the jail is covered; what is not covered is everything after the question that comes from the config: run folder from DESK_DB_PATH, REAL_RESULT_FILE written, child env from config. v6 itself touched post-question lines (result_line, the `return 0 if ... wrote else EXIT_FAILED` line). It is a real gap, narrow: Minor 3. A closer that needs no `y` and no scripted answer: move the body after the question into `_execute(...)` and call that from a test with `fakes.env` (no `input`, no `ask_to_start`).

## 7. Fails-before and mutants
Fails-before: clean 61ded9e + only the two NEW modules (terminal_guard.py, precheck.py, so the imports work) + the v6 tests, `tests/test_real_run_v6.py` (all in-process or devnull-stdin tests; nothing there answers y): 70 test cases failed, in 16 distinct test functions (live refusals 38, pipe-per-file 9, argparse form 6, book below a file 3+1, result file link 2, blank result 2, result file names a key, pipe result, live/real pipe, no-terminal form, argument types, limits named, good command line). Old code asked `Start? [y/N]` and the mocked input failed the test; nothing was answered. Blocker log: 0 lines.
Own 18 mutants (tests/test_real_run_v6.py + tests/test_start_prompt_hardening.py, `-x`): killed 17, survived 1.
M1 stdin_is_terminal always True; M2 Windows probe skipped; M3 y/yes allowed as the word; M4 `==` -> `in` (empty answer accepted); M5 ask_to_start without terminal test; M6 char devices not special; M7 folder_part_is_a_file False; M8 no realpath fallback; M9 `--assume-yes` loopback check off; M11 runs cap removed; M12 result same-file loop off; M13 `--config` pipe check off; M14 early stdin check off; M15 approvers file not stat-checked; M16 refusal exit 2 -> 1; M17 db folder check off; M18 live key/ledger pipe check off: all KILLED.
M10 `--leads` cap `<=` -> `<` (1000 refused): SURVIVED (Minor 5).

## 8. Lint, hygiene, tests
On the variant tree: `ruff check` clean; `ruff format --check` 163 files clean; `mypy --platform linux` and `--platform win32` clean (30 files); `bandit -ll` no medium/high (warnings are "Test in comment" only); `git diff --check` clean. gitleaks 8.30.1 `dir` with the repo config, after removing my `__pycache__`: no leaks. (First run showed 67 hits: all in `__pycache__`/.ruff_cache from my own runs, none in sources.) tests/test_hygiene.py + tests/test_gitleaks_exceptions.py with DPLD_REQUIRE_SCAN=1 and the gpgsign override: passed (twice, also on the tree after desk-address-required-v6).
Tests run under unshare + blocker: test_real_run_v6, test_start_prompt_hardening, test_core_key_readers, test_take_script_refusals: 358 passed. Combined set on variant + desk-address-required-v6 (test_desk_address_required, test_crm_hubspot, test_env_numbers, test_live_claude, test_ledger_amounts, test_real_check_dry, test_path_confinement, test_clock_steps, test_real_run_v6, test_start_prompt_hardening, test_take_script_refusals, test_core_key_readers, test_portal_wording_and_masking, test_hygiene): all passed except the two failures explained above.
src/ of the variant equals core-touches-3.patch src hunks: confirmed (diff of `git diff --cached -- src` after applying each, index lines removed: equal).
New suppression comments added by the patch (against "no new noqa"): 32 lines (scripts/run_real_check.py 11, scripts/run_live_check.py 1, tests: test_take_script_refusals 8, test_real_run_v6 6, test_start_prompt_hardening 4, test_real_check_dry 1, conftest 1): E402 on imports after `sys.path` setup (the repo's existing pattern, the base already has 22 in run_real_check.py), plus S603, S404, PLC0415 and `type: ignore` lines. Minor 8: decide whether the rule applies.

## 9. Apply order on main
`real-run-fixes-v6-after-sonar-p3-final.patch` then `desk-address-required-v6.patch` (sha256 66679357...: checked): `git apply --check` and `git apply` OK; ruff, format, mypy linux+win32 clean on the result; the desk-address-required patch alone on 61ded9e does NOT apply (docs/settings.md:81), as expected.

## Findings, by severity
Blocker: none. Major: none.

Minor 1. `run_real_check.py` still uses plain argparse: `--dry-port-base CANARY` or `--bogus=CANARY` prints a usage block and `error: ... 'CANARY'` on stderr (the typed value is echoed, several lines, not the `refused:` form). Exit code is 2 by argparse's habit. Nothing secret by design, but it is the inconsistency v6 closed for the live script only. Fix: the same `RefusingParser`.
Minor 2. DESK_DB_PATH containing `..` after a file (`afile/../x/desk.db`) passes `folder_part_is_a_file` (lexical abspath) and fails after the question with an uncaught NotADirectoryError (traceback, exit 1, nothing real started yet). Fix: use the path as given for the walk (no abspath collapse), or catch OSError around `run_dir.mkdir` and add one fixed line.
Minor 3. No test runs a `--config` real run past the question any more (section 6). Real, narrow gap; proposed split of `_run`.
Minor 4. REAL_RESULT_FILE may equal a file the run writes itself in the run folder (`desk-1.log`, `desk-2.log`, `crash.flag`, `<db>-wal`/`-shm`); the result would be overwritten or deleted. Made-up data only; low harm.
Minor 5. `--leads 1000` and `--runs 100` boundaries untested; mutant M10 survives. Add the two accepted-boundary cases next to 1001/101.
Minor 6. keep_scan wrongly accepts/rejects (section 5): a tripwire; at least S1 (`undo`), S3 (substring `TEMP`) and S4 (asyncio child) are cheap to close.
Minor 7. A `y` answer is still scripted in the repo: `tests/test_real_check_dry.py` line 455, `monkeypatch.setattr("builtins.input", lambda prompt="": started.append("asked") or "y")` (not added by v6, but the studio rule is never y). It is harmless today (the run is refused first and the guard needs a host), but if the refusal order changes it would be a `y` at a start question. Change it to `_no_question`.
Minor 8. 32 new suppression comments (section 8).
Minor 9. Out of the diff, same class: `scripts/hubspot_probe.py --yes-spend-calls 7` confirms a real spend by a flag, with no terminal test, using the HubSpot address constant and a token from an environment variable (needs a real token; a reviewer without one cannot trigger it). Decide whether it needs the same guard.
Nit 1. `run_live_check` accepts `--base-url http://127.0.0.1:CANARY` (non-numeric port) and `:99999`, `:80:90`; with `--assume-yes` it would then only fail every call. No key leaves this computer.
Nit 2. `run_live_check._read_key` ValueError (a path with NUL) is an uncaught traceback if called in-process; a command line cannot carry NUL, so unreachable from the shell.

Positive checks: `--assume-yes` against 29 URL spellings (userinfo, `127.0.0.1.evil.test`, octal/hex/decimal IPv4, mapped IPv6, `%2f`, tab, full-width digits, `0.0.0.0`, link-local): `_loopback_url` and `LiveSettings` agree; only real loopback names pass.

## Files
* This report: /tmp/work/REVIEW-real-run-v6-fresh.md
* My harnesses (outside the repo): /tmp/work/rv6-t/ (mkcfg.py, rr.py, leak.py, fuzz_live.py, lb.py, ks.py, mut.py, pty*.sh, stdin.sh), /tmp/work/rv6-run.sh, trees /tmp/work/rv6 (variant), /tmp/work/rv6da (+ desk-address-required-v6), /tmp/work/rv6old (old code + new tests), /tmp/work/rv6m (mutants).
* Raw outputs: /tmp/work/rv6-old-run.txt, /tmp/work/rv6-mut.txt, /tmp/work/rv6-da-run.txt.
Head SHA: base 61ded9e (variant applied uncommitted; no commit, no push).
Token use: not measured.
