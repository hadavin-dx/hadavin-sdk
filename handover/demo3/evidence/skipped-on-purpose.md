# Skipped tests on main f3c39cf (agent M, read-only analysis)

Source: `/home/user/work/i-logs/suite-base.log` (grep '^SKIPPED'; last line: 3683 passed, 200 skipped, 1188.75 s; run on Python 3.12.3 in `/home/user/work/final-venv`). Test sources read in `/home/user/work/i-base`. Nothing was run. Studio backslash files are not in this checkout (BRIEF-PREAMBLE.md read; studio notes absent).

Gaps first: (1) counts match 200 = 166 + 30 + 4, no other split. (2) I did not run any command, so the "could run safely" lines are read from source, not proven. (3) Whether user `nobody` can read the venv and worktree was not checked.

## Counts
| class | tests | meaning |
|---|---|---|
| a | 2 | on purpose, Windows-only (1) or Python-3.13-only (1); the 3.13 one runs under a Python 3.13 interpreter |
| b | 1 | opt-in switch (load measurement) |
| c | 1 | skipped because we run as root |
| d | 196 | missing install: playwright 166 (agent K), gitleaks 30 (agent L) |
| total | 200 | |

## The 4 other skips
| test (file:line of skip condition) | skip text verbatim | class | what makes it run |
|---|---|---|---|
| `tests/test_stall_eviction.py:526` `test_without_the_lingerer_the_reply_is_lost_on_windows` (skipif `sys.platform != "win32"`) | the reset that destroys the reply happens on Windows only | a (Windows-only) | Only a Windows machine. Cannot run on Linux under any install. Its Linux twin `test_late_request_does_not_reset_the_refusal` (line 515) already passes. |
| `tests/test_path_confinement.py:284` `test_v3_our_device_list_covers_what_python_says_windows_reserves` (skipif `not hasattr(ntpath, "isreserved")`) | ntpath.isreserved needs Python 3.13 | a (Python-3.13-only) | Run under Python 3.13 (the suite ran on 3.12.3). `/usr/local/bin/python3.13` exists (3.13.18, has `ntpath.isreserved`) but has no pytest or project dependencies, so a full run needs a new 3.13 environment (an install). Needs a person's decision: pyproject allows >=3.12, the mypy target is 3.12. |
| `tests/test_server_hardening.py:224` `test_measure_burst` (skipif `not os.environ.get("LEAD_DESK_LOAD_N")`) | measurement run: set LEAD_DESK_LOAD_N | b (opt-in) | `LEAD_DESK_LOAD_N=300 python -m pytest tests/test_server_hardening.py -k measure_burst -s -p no:cacheprovider` (from docs/limits.md:92; optional `LEAD_DESK_LOAD_RETRY=1`, read at line 227). Cost: starts its own local desk and fires N simultaneous connections on this machine; no network, no paid call. It only prints counts (no pass criterion, docs/limits.md says results vary and are machine-dependent). 300 connections is also run (with retry) by `test_300_burst_with_retry`, which is not skipped. Safe to run, no install; do it alone, not beside other heavy jobs. |
| `tests/test_n8n_api_url.py:510-512` (skipif `not hasattr(os,"geteuid") or os.geteuid()==0`) | root (and Windows) can read a file with no permissions | c (root) | Run the suite as a non-root user, e.g. `setpriv --reuid=nobody --regid=nogroup --clear-groups -- <venv python> -m pytest tests/test_n8n_api_url.py -k <that test>`. `setpriv`, `runuser` and user `nobody` exist; not checked: whether `nobody` can read the venv, the worktree and write a temp dir. Needs a person's decision only if a permanent non-root CI step is wanted. (Opposite test `tests/test_path_confinement.py:192` needs root and does run.) |

## The 196 install skips (handled by K and L)
| group | tests | skip text | skip condition file:line | what runs them |
|---|---|---|---|---|
| playwright (d) | 22 | could not import 'playwright.sync_api': No module named 'playwright' | `tests/test_mode_safety.py:110` (`pytest.importorskip`) | install playwright and its browser (agent K) |
| playwright (d) | 28 | same | `tests/test_portal_browser.py:27` | same |
| playwright (d) | 113 | same | `tests/test_portal_lead_pages.py:113` | same |
| playwright (d) | 3 | same | `tests/test_portal_wording_and_masking.py:171, 204, 257` (1 each) | same |
| gitleaks (d) | 24 | no gitleaks program (set GITLEAKS_BIN); set DPLD_REQUIRE_SCAN=1 to make this a failure | `tests/test_gitleaks_exceptions.py:145` | gitleaks binary on PATH or `GITLEAKS_BIN` (agent L); `DPLD_REQUIRE_SCAN=1` turns the skip into a failure |
| gitleaks (d) | 2 | no gitleaks program on PATH (set GITLEAKS_BIN); set DPLD_REQUIRE_SCAN=1 to make this a failure | `tests/test_gitleaks_semgrep_lock.py:38` | same |
| gitleaks (d) | 3 | same text | `tests/test_hygiene.py:150, 344, 533` | same |
| gitleaks (d) | 1 | no gitleaks program on PATH (set GITLEAKS_BIN) | `tests/test_hygiene.py:580` | same (this one has no `DPLD_REQUIRE_SCAN` failure switch in its text) |

Sums: playwright 22+28+113+3 = 166; gitleaks 24+2+3+1 = 30.

## Can run here safely without installing anything new (read from source, not run)
- `test_measure_burst`: the command in the table above.
- n8n permission test: via `setpriv` as `nobody`, if file permissions allow (unchecked).
## Need a person's decision
- Python 3.13 test run (needs a new environment); a standing non-root run; whether Windows-only test needs any Windows runner (it is a negative control, the Linux twin passes).
## Cannot run on this machine under any install
- `test_without_the_lingerer_the_reply_is_lost_on_windows` (needs win32).
