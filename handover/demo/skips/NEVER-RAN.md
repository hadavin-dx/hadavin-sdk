# NEVER-RAN: what has never run in any environment the demo session has (Linux), for the Windows run

Evidence builder (Q7 item 4). Repo: public pr-3-tests, head 2db3926, read-only clone /tmp/work/nr-base. No pytest was run (only `--collect-only -q`, one file at a time, from /tmp/work/int2-venv). No commit, no push, made-up data only. No personal names copied.
Labels: MEASURED = a command output I saw in this task (or the Q5 evidence files, named); INFERRED = read from code, never run. Bible R-numbers not looked up (read-only evidence task); preamble rules 6 and 14 applied.

## 0. Read first: what is uncertain

1. Nothing in section 1 has ever run on Windows by the demo session. The lead's Windows run (252 passed / 29 skipped, a targeted run, test list not in the handover) is the only Windows data, and its `-rs` skip lines are not saved. Section 3 therefore cannot say which tests make up the 29.
2. Correction to my Q5 reading: `reset.ps1` IS executed by tests on Windows. `tests/test_reset_scripts.py::_run()` starts `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\reset.ps1` when `sys.platform == "win32"` (INFERRED from code; MEASURED only that the file has 26 tests). 23 of the 26 run on Windows (3 skip there). This is the only place a `.ps1` file is run by a test. `start_all.ps1` is executed by no test on any platform.
3. All Windows expectations are read from code, not measured on Windows.

## 1. Table: what cannot have run on Linux

Commands are PowerShell, from the repository root, `.venv` switched on. NOT TESTED BY ME.

| # | Group | What it checks | What could go wrong on Windows | Command | Expected if all is well |
|---|---|---|---|---|---|
| 1 | Windows-only stall test: `tests/test_stall_eviction.py::test_without_the_lingerer_the_reply_is_lost_on_windows` (skipif not win32; MEASURED skipped in every Linux full run; file has 37 tests) | Negative control for the test above it: with a socket closed WITHOUT the lingering helper (`_NoLinger`), a Windows client loses the 503 "busy" reply to a TCP reset in at least 1 of 5 tries; this proves the lingerer is needed | Windows may not lose the reply (OS version or loopback timing), so `lost >= 1` fails and the control proves nothing; or the positive test beside it fails | `python -m pytest tests/test_stall_eviction.py -rs -v -p no:cacheprovider` | 37 collected, all pass, 0 skipped (this test is NOT skipped on Windows). A fail is a real finding: record it, do not rerun until green |
| 2 | `reset.ps1` EXECUTED: `tests/test_reset_scripts.py` (23 of 26 run on Windows) | refuses a db outside `data\` (exit 2), deletes a db inside, refuses when something answers the desk port, when a process holds the db, when a pid file belongs to another program (exit 6), RESET_STOP_WAIT_SECONDS validation (exit 2), reset_check lock-file messages | `powershell.exe` not on PATH (test then skips "Windows PowerShell is not installed"), execution policy, PowerShell 5.1 handling of `-cnotmatch`, `Get-CimInstance Win32_Process` command-line match, `Wait-Process` timing | `python -m pytest tests/test_reset_scripts.py -rs -v -p no:cacheprovider` | 23 passed, 3 skipped (the three `test_reset_sh_*`: "Windows ends a process at once..." x2, "a process that ended but is not collected..." x1). A PowerShell-missing skip means not covered |
| 3 | `reset.ps1` Stop-Process behaviour (part of row 2: pid-file-of-another-program, process-holds-database, still-deletes tests) | script stops ONLY a process whose command line matches `lead_desk.server` or `demo_only.fakes_server`, waits `$stopWait` s, exit 5 if it will not stop | The three POSIX stop-wait tests are skipped on Windows and have no Windows twin, so the "did not stop in time" branch (exit 5) and a real stop of a real desk are covered by no test (INFERRED) | partly row 2; manual: `.\scripts\start_all.ps1` then `.\scripts\reset.ps1` | "reset done", exit 0, `data\desk.pid` and db files gone, no leftover lead_desk python process (`Get-CimInstance Win32_Process -Filter "Name='python.exe'" \| Select CommandLine`). The manual step is outside pytest |
| 4 | PowerShell scripts read as TEXT only: `tests/test_reset_ps1_links.py` (15 tests, MEASURED collect), `tests/test_lead_step_route.py::test_demo_launchers_name_the_demo_file_and_the_off_switch` (reads start_all.ps1 and .sh), `tests/test_portal_wording_and_masking.py:322` and `tests/test_vendor_hosts.py:24` (scan `.ps1` as text) | reset.ps1 uses python `realpath` (not GetFullPath); the refusal comes before every Get-Content / Stop-Process / Remove-Item and their short names; one test runs the cut-out python snippet on a symlink | They run on Linux (text only), so the logic is shown there; Windows adds: `.gitattributes` makes `*.ps1` CRLF on checkout and the regexes must still match; the symlink case needs the symlink right | `python -m pytest tests/test_reset_ps1_links.py tests/test_lead_step_route.py tests/test_vendor_hosts.py -rs -v -p no:cacheprovider` | all pass; at most 1 skip ("this computer cannot make a symbolic link") |
| 5 | Lock files: `lockfile.acquire` on Windows uses `msvcrt.locking` (`src/lead_desk/lockfile.py:55`; also `live_claude.py:167,188`) | one desk per lead book; "held" = EACCES/EDEADLK; `_same_file` returns True | REAL `msvcrt.locking` has never run in a test here: on Linux a FAKE msvcrt is used (`test_desk_http_edge_cases.py:1166-1193`); `test_ledger_amounts.py:388` takes its real msvcrt branch only on Windows. A second real desk on the same book might not be refused | `python -m pytest tests/test_desk_http_edge_cases.py tests/test_desk_edge_cases.py tests/test_ledger_amounts.py tests/test_stamp_locks_and_budget.py -rs -v -p no:cacheprovider` | pass; skips: `test_lock_file_replaced` (fcntl), `test_replaced_lock_file`, possibly 2 symlink tests. Collected 77+57+104+23 (MEASURED) |
| 6 | Windows lock-file installs: `requirements-dev-win.txt`, `requirements-browser-win.txt` (Python 3.13, hashes) | `docs/tests.md:56` states "the Windows lock file was made but never installed" (read) | a package with no Windows wheel, hash mismatch, Python 3.12 instead of 3.13, a compiler need | see block 4d (new venv) | no hash error; `pip check` says "No broken requirements found"; Playwright reports 1.63.0 (version from docs, not run) |
| 7 | Hygiene and gitleaks on Windows: `tests/test_hygiene.py` (15 tests), `tests/test_gitleaks_exceptions.py` (44), `tests/test_codeant_hygiene.py` (7) | `_gitleaks_exe()`: bare name via `shutil.which`, `.exe` added for a path with a folder part (`os.name == "nt"`), `normcase` compare (`.EXE` vs `.exe`); planted files written as bytes (no newline translation by the test); `test_sh_blobs_no_cr` reads the git index, not the work tree | gitleaks.exe not on PATH (27 skip, or fail with `DPLD_REQUIRE_SCAN=1`); backslashes in gitleaks report paths (only `x["File"].replace(chr(92), "/")` handles it); a relative path across drives (that test skips) | `$env:DPLD_REQUIRE_SCAN='1'; $env:GITLEAKS_BIN='C:\path\to\gitleaks.exe'; python -m pytest tests/test_hygiene.py tests/test_gitleaks_exceptions.py tests/test_codeant_hygiene.py -rs -v -p no:cacheprovider` | 15 + 44 + 7 pass; 0 gitleaks skips with gitleaks 8.30.1 (CI version); at most 1 symlink skip and 1 "different drives" skip |
| 8 | CRLF and `.gitattributes` (`* text=auto eol=lf`, `*.ps1 text eol=crlf`) | `test_gitleaks_exceptions.py` case "CRLF line ending" pins that gitleaks DOES report a CR before a line end (a hand-saved CRLF file only); `test_sh_blobs_no_cr` | A clone with global `core.autocrlf=true` or without the rules could hold CRLF in `.sh`/`.py`; the work-tree scan could then report lines the index does not have | `git ls-files --eol \| Select-String 'w/crlf'` then row 7's command | only `*.ps1` lines show `w/crlf`; tests pass |
| 9 | Windows halves of branches inside shared tests: `test_load_tools.py:650` (`ulimit_n` null, no `resource` module), `test_portal_demo.py:1007` (200 or 409 allowed), `test_ledger_amounts.py:388` (real msvcrt) | the Windows half of an `if sys.platform` in a test that runs on both | Linux only ever took the other half | `python -m pytest tests/test_load_tools.py tests/test_portal_demo.py tests/test_ledger_amounts.py -rs -v -p no:cacheprovider` | pass; up to 2 symlink skips in portal_demo |
| 10 | Windows socket choices `src/lead_desk/server.py:298` (`allow_reuse_address = os.name != "nt"`), `:490` (`SO_EXCLUSIVEADDRUSE`) | a second listener on a busy port is refused on Windows | MEASURED by grep: no test mentions `EXCLUSIVEADDRUSE` or `allow_reuse_address`; only indirect cover through the desk-port tests | manual: `$env:PYTHONPATH='src;.'`, start `python -m lead_desk.server` twice in two windows | second start exits with a port-in-use message. This is a gap: no test exists to run |
| 11 | Playwright / Chromium on Windows: 166 browser tests (portal_lead_pages and the files that use its helper, portal_browser, mode_safety, portal_wording_and_masking; 166 MEASURED in Q5 emulation) and 36 Node tests (MEASURED in Q5 with node removed) | real-browser pages, layout, colours, Node probe scripts | Never run on Windows (ORDERS.md: not run); needs `playwright install chromium`; Windows fonts change layout/contrast numbers; no `node` = 36 skip | `python -m playwright install chromium; python -m pytest tests/test_portal_browser.py tests/test_portal_lead_pages.py tests/test_portal_layout.py tests/test_portal_look.py tests/test_portal_phone_layout.py tests/test_portal_long_values.py tests/test_portal_drawer_long_name.py tests/test_stage_confirm_browser.py tests/test_mode_safety.py tests/test_portal_wording_and_masking.py -rs -v -p no:cacheprovider` | 0 browser skips ("no browser" skips = not covered). On Linux with Chromium 1243 these ran with no skips (Q5, h3 chunks) |
| 12 | Whole suite on Windows | everything above plus the rest | never run in full on Windows at this head | block 4a | Linux expectation at 2db3926 with all tools present, as root: 3 skipped (n8n root test, load measurement, the Windows-only stall test; INFERRED from Q5, final totals not confirmed by me). On Windows the stall test runs, so it is not in the Windows skip list |

Also never run by any test anywhere I have: `start_all.ps1` (text only), `tests/crash_launcher.py` and `scripts/crash_desk.py` child processes on Windows, and `cmd.exe` `set X=8765 ` parsing (envnum strips blanks; Linux tests use literal strings only, `tests/test_env_numbers.py:364`).

## 2. Meaning of Windows skip reasons

Expected and fine: the 3 `test_reset_sh_*` tests (POSIX stop-wait), `test_reset_sh_refuses_when_ps_is_missing`. A real coverage hole if they appear: "no gitleaks", "no browser", "node is not installed", "Windows PowerShell is not installed", "cannot make a symbolic link", "openssl".

## 3. The unreconciled Windows skip count (29)

Lead's figure: 252 passed + 29 skipped = 281 tests, targeted run, file list unknown.

Candidate skip reasons. "Skips on Windows" is INFERRED from the skipif line; test counts are MEASURED on Linux (`--collect-only`, Q5 inventory):

| Reason | File:line | Tests | Skips on Windows? |
|---|---|---|---|
| POSIX stop-wait / defunct process | test_reset_scripts.py:117,138,165 | 3 | yes, certain |
| reset.sh needs `ps` | test_mode_safety.py:332 | 1 | yes, certain |
| `/proc/self/fd` | test_model_stamp_and_reaper.py:249,292 | 2 | yes |
| `fcntl` lock replaced | test_desk_http_edge_cases.py:555 | 1 | yes |
| lock file replaced while held | test_desk_edge_cases.py:890 | 1 | yes |
| in-process restart same port | test_portal_api.py:1457 | 1 | yes |
| root or Windows reads a no-permission file | test_n8n_api_url.py:510 | 1 | yes (no geteuid) |
| load measurement (env var unset) | test_server_hardening.py:224 | 1 | yes, any platform |
| **subtotal certain** | | **11** | |
| symlink right missing | test_desk_edge_cases:871, test_desk_http_edge_cases:511, test_portal_api:854, test_reset_ps1_links:80, test_hygiene:465, test_portal_demo (2 tests via `symlink_or_skip`) | about 7 | only if the account has no symlink right |
| gitleaks program missing | test_hygiene (3) + test_gitleaks_exceptions (24) | 27 (Q5 MEASURED without gitleaks) | only if gitleaks is absent; with `DPLD_REQUIRE_SCAN=1` they fail instead |
| Node missing | 6 files | 36 (Q5 MEASURED) | only if node is absent |
| Playwright or Chromium missing | 10 files | 166 (Q5 MEASURED) | would exceed 29, so these files were not in the run (or Playwright was installed) |
| openssl missing | test_smtp_provider.py (whole file 62), test_real_check_dry.py:829 (1) | up to 63 | would exceed 29: openssl was present or those files were not in the run |
| Windows-only stall test | test_stall_eviction.py:526 | 1 | NO, it runs on Windows |

Arithmetic: 11 certain skips leave 18 of the 29 unexplained. 18 is not any single group; symlinks reach about 7, gitleaks is 27 as a whole. Combinations I can form: 11 + 27 = 38; 11 + 24 = 35; 11 + 3 = 14; 11 + 7 + 3 = 21. None gives 29, so the 29 stays UNRECONCILED. The lead's note ("POSIX signal and gitleaks-binary tests") fits the 11 plus part of the gitleaks group, but a part cannot be named from reading. The `-rs` list from block 4a (about 30 lines, one reason per line) settles it.

## 4. Windows command block (PowerShell). NOT TESTED BY ME.

```powershell
# NOT TESTED BY ME. Run from the repository root with the .venv switched on. Made-up data only.
# The reset tests delete only folders they create under data\.
$env:PYTHONPATH = 'src;.'

# 4a. same targeted run as before, but keep the skip reasons (these are the 29)
#     (if a subset was used before, replace `tests` with the same file list and say which)
python -m pytest tests -rs -q -p no:cacheprovider 2>&1 | Tee-Object -FilePath win-full-run.txt | Select-String 'SKIPPED|passed|failed|error' | Tee-Object -FilePath win-skips.txt

# 4b. a missing gitleaks must fail, not skip
$env:DPLD_REQUIRE_SCAN = '1'; $env:GITLEAKS_BIN = 'C:\path\to\gitleaks.exe'   # real path; CI uses gitleaks 8.30.1
python -m pytest tests/test_hygiene.py tests/test_gitleaks_exceptions.py tests/test_codeant_hygiene.py -rs -v -p no:cacheprovider 2>&1 | Tee-Object -FilePath win-gitleaks.txt

# 4c. Windows-only and PowerShell tests
python -m pytest tests/test_stall_eviction.py tests/test_reset_scripts.py tests/test_reset_ps1_links.py -rs -v -p no:cacheprovider 2>&1 | Tee-Object -FilePath win-ps-stall.txt

# 4d. lock-file installs in a NEW venv (an old one could hide a failure)
python -m venv .venv-lockcheck; .\.venv-lockcheck\Scripts\Activate.ps1
python -m pip install --require-hashes -r requirements-dev-win.txt
python -m pip install --require-hashes -r requirements-browser-win.txt
python -m pip check
deactivate

# 4e. only *.ps1 should be CRLF in the work tree
git ls-files --eol | Select-String 'w/crlf'

# 4f. facts to send back with the files
python --version; node --version; (Get-Command gitleaks -ErrorAction SilentlyContinue).Source; $PSVersionTable.PSVersion
```

Expected on a complete Windows run with gitleaks, node, Chromium and openssl present (INFERRED, not from any Windows run): 11 skips (the certain group in section 3) plus up to about 7 symlink skips if the account lacks the symlink right, so 11 to 18. Any "no gitleaks", "no browser", "node", "PowerShell" or "openssl" skip is a coverage hole, not an expected skip.

## 5. Not done / not checked

- No Windows machine and no pytest run by me; every Windows expectation is read from code.
- Playwright 1.63.0 is from docs/tests.md, not run.
- test_smtp_provider's openssl count is only the collected number (62).
- Final totals of the running Linux full run were not read (not my run).
