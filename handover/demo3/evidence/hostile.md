# Hostile-input pass, PR #12 (evidence runner B: raw output only, no verdicts)

Made-up data only. PR12 = worktree /home/user/work/pr12b at 8d655773c70f17545795f70c0f85ea5cadaf2719. MAIN = /home/user/work/mainb at 61ded9ebdb17397904aa850830f3d9837114f8f7. Python /usr/bin/python3.12 (system, stdlib only, no venv needed). Linux only: the Windows cases could run only through the helper's `path_module=ntpath` parameter (text level, no Windows, no real SQLite open on a network path). Studio backslash files (bible\RULES.md etc.) are not in this checkout; not read, nothing invented. Scripts: scratch/*.py, scratch/fs_cases.sh. Raw logs: evidence/raw/hostile-*.log. Worktrees were left clean (`git status --short` empty in both).

## Things that failed or were unexpected (first)

| # | What | Where |
|---|---|---|
| F1 | A foreign `tools` package that has the SAME function names as tools/pathconfine.py (test dir foreignD) is silently used by load_tools/catcher.py on BOTH main and PR12 (log prints `FOREIGN confine used`; a `--control /nonexistent_dir/zz` was accepted, then the catcher listened). PR12 only drops a foreign `tools` when the import raises ImportError. | raw/hostile-foreign-tools2.log |
| F2 | `python -m demo_only.fake_model_server --help` now FAILS with a traceback when another project's `tools` is first on the path (PYTHONPATH=foreignA:repo). Main prints the help. The module docstring says so; the exit is a traceback, not a message. | raw/hostile-foreign-tools2.log |
| F3 | `python tools/scrub_n8n_export.py ...` (README says tools start directly without PYTHONPATH) still fails with a double traceback `ModuleNotFoundError: No module named 'tools.pathconfine'` when a foreign `tools` is on PYTHONPATH, on main and on PR12 (PR12 did not change its import block). | raw/hostile-foreign-tools2.log |
| F4 | scripts/n8n_api.py: with PYTHONPATH=foreign:repo[:src] (foreign first, repo already on the path), import fails, exit 1, `ModuleNotFoundError: No module named 'tools.pathconfine'`, main and PR12 alike. Also the PR12 ordering change does not apply when PYTHONPATH already lists repo and src (the script sees them in `sys.path` and does not re-insert): with `PYTHONPATH=src:repo` order stays `scripts, src, repo`, with `PYTHONPATH=repo:src` stays `scripts, repo, src`. The "src ahead of repo" order only holds when neither is on PYTHONPATH. | raw/hostile-n8n-import.log, raw/hostile-n8n-syspath.log |
| F5 | PR12 n8n_api.py, `tools` of another project already imported (foreignD has pathconfine but no `ROOTS_ENV`): `ImportError cannot import name 'ROOTS_ENV' from 'tools.pathconfine' (.../foreignD/tools/pathconfine.py)`. Main has no such failure (it did not import ROOTS_ENV). | raw/hostile-n8n-import.log (last lines) |
| F6 | Hard links: a hard link inside the confined root to a file outside it passes confine/confine_existing/confine_anywhere on main and PR12, reads return the outside content and a write through it changed the outside file (`FAKE-OVERWRITTEN-VIA-HARDLINK`). PR12 documents it; behaviour is the same on main. | raw/hostile-hardlink-*.log |
| F7 | NT object path `\??\UNC\host\share\x` with ntpath is NOT refused: `file:///tmp/%5C%3F%3F%5CUNC%5Chost%5Cshare%5Cx?mode=ro`. Empty string and NUL text are not refused by `readonly_sqlite_uri` either: `''` -> `file:///tmp?mode=ro`, `'\x00'` -> `file:///tmp/%00?mode=ro` (those two are normally stopped earlier by confine_*). | raw/hostile-unc2-pr12b.log |
| F8 | `LEAD_DESK_PATH_ROOTS=/` lets `--key-file /etc/hostname` start the fake server on PR12 (by design of the variable, recorded). A relative root (`relative/outside`) and an empty value were refused. | raw/hostile-fakeserver-extra.log |

Not run: Windows itself (no SQLite open of a UNC path, no real `\\?\` handling); full suite, ruff, mypy, bandit, gitleaks (agent A); mapped-drive case.

## (1) UNC / network paths, `readonly_sqlite_uri(text, path_module)` (PR12 only has the second parameter; main has one parameter)

With `path_module=ntpath` on PR12 (log raw/hostile-unc-pr12b.log, raw/hostile-unc2-pr12b.log). Exception text for every refusal: `PathRefused: book path: a Windows device or network path (\\server\share, \\?\C:\) cannot be opened read-only by SQLite`.

| Exact input (Python repr) | PR12 result with ntpath | MAIN |
|---|---|---|
| `'\\\\host\\share\\x.db'` | refused (text above) | 2nd argument not accepted: `TypeError: readonly_sqlite_uri() takes 1 positional argument but 2 were given` |
| `'//host/share/x.db'` | refused | same TypeError |
| `'\\\\?\\UNC\\host\\share\\x.db'` | refused | same |
| `'\\/host/share/x.db'` | refused | same |
| `'/\\host\\share\\x.db'` | refused | same |
| `'\\\\?\\C:\\x.db'` | refused | same |
| `'\\\\.\\C:\\x.db'` | refused | same |
| `'\\\\localhost\\share\\x.db'` | refused | same |
| `'//localhost/c$/x.db'` | refused | same |
| `'\\\\host'`, `'\\\\host\\share'`, `'\\\\?\\UNC\\'`, `'///host/share/x.db'`, `'\\\\\\host\\share'`, `'//'`, `'\\\\'` | refused | same |
| `'\\\\?\\unc\\host\\share\\x'`, `'//?/UNC/host/share/x'`, `'//./C:/x'`, `'\\\\host/share/x'`, `'/\\/host/x'` | refused | same |
| `'C:\\x.db'` | `file:///tmp/C%3A%5Cx.db?mode=ro` (not refused) | not run with ntpath |
| `'\\??\\UNC\\host\\share\\x'` | NOT refused: `file:///tmp/%5C%3F%3F%5CUNC%5Chost%5Cshare%5Cx?mode=ro` | n/a |
| `''` | `file:///tmp?mode=ro` | n/a |

With the real `os.path` on Linux (default argument), PR12 and MAIN give identical output (diff of the two logs is empty for that section): `'\\\\host\\share\\x.db'` -> `file:///tmp/%5C%5Chost%5Cshare%5Cx.db?mode=ro` (a backslash name in cwd /tmp); `'//host/share/x.db'` -> `file:////host/share/x.db?mode=ro`; `'///host/share/x.db'` -> `file:///host/share/x.db?mode=ro`. Nothing refused on Linux (as the docstring says).

`confine`, `confine_existing`, `confine_anywhere` with the same strings on Linux (identical on main and PR12): `\\host\share\x.db` -> confine: `the name of a new file may only use letters, digits, '.', '_' and '-'`; confine_existing / confine_anywhere: `no such file`; `//host/share/x.db` -> confine and confine_existing: `path is outside the allowed folders (add a folder with LEAD_DESK_PATH_ROOTS)`, confine_anywhere: `no such file`.

`load_tools.check_invariants.read_book(path)` on Linux:

| Input | MAIN | PR12 |
|---|---|---|
| `'\\\\host\\share\\x.db'` | `AttributeError: 'str' object has no attribute 'name'` | `InputError: book \\host\share\x.db: no such file` |
| `'//host/share/x.db'` | AttributeError (same text) | `InputError: book x.db: path is outside the allowed folders (add a folder with LEAD_DESK_PATH_ROOTS)` |
| `'\\\\?\\UNC\\host\\share\\x.db'` | AttributeError | `InputError: book \\?\UNC\host\share\x.db: no such file` |
| `'\\/host/share/x.db'` | AttributeError | `InputError: book x.db: no such file` |
| `123`, `None`, `b'x'` | `AttributeError: 'int'/'NoneType'/'bytes' object has no attribute 'name'` | `InputError: book: not a path` |
| `'\x00'` | AttributeError | `InputError: book ?: contains a control character` |

(read_book takes a Path in normal use; strings were the hostile input.)

## (2) Hard links in a confined root (cwd = scratch/hl-*/root, outside file in the sibling folder `outside/`)

Setup: `os.link(outside/secret.txt, root/hl_out.txt)` (nlink=2, same inode), `os.link(root/inside.txt, root/hl_in.txt)`, `os.symlink(outside/secret.txt, root/sym_out.txt)`. Results identical on MAIN and PR12:

| Input | confine_existing | confine | confine_anywhere |
|---|---|---|---|
| `hl_out.txt` (hard link to outside) | returns `.../root/hl_out.txt` | returns it | returns it |
| `hl_in.txt` (hard link inside) | returns path | returns path | returns path |
| `sym_out.txt` (symlink to outside) | `PathRefused --f: path is outside the allowed folders (add a folder with LEAD_DESK_PATH_ROOTS)` | same | returns the outside real path |
| absolute path of outside file | same refusal | same refusal | returns it |

Read via `confine_existing('hl_out.txt').read_text()` -> `'FAKE-OUTSIDE\n'`. Write via `confine('hl_out.txt').write_text(...)` -> outside file afterwards `'FAKE-OVERWRITTEN-VIA-HARDLINK\n'`.

## (3) Foreign `tools` package (raw/hostile-foreign-tools.log, -tools2.log)

Foreign dirs (scratch/): A = `tools/__init__.py` only; B = has `pathconfine.py` without `PathRefused`; C = namespace package (no `__init__`); D = `pathconfine.py` with all the same names. Each put first on sys.path through PYTHONPATH, cwd = the repo copy.

| Command | A / B / C on MAIN | A / B / C on PR12 | D on MAIN / PR12 |
|---|---|---|---|
| `python load_tools/catcher.py --help` | traceback at line 37 `from tools.pathconfine import PathRefused, confine` (ModuleNotFoundError; for B ImportError) | usage text printed | usage printed on both (foreign module used) |
| same for load_driver.py, check_invariants.py | traceback | usage printed | usage printed |
| `python -m tools.scrub_n8n_export` | usage line (cwd first on path) | usage line | usage |
| `python tools/scrub_n8n_export.py` | traceback `ModuleNotFoundError: No module named 'tools.pathconfine'` (twice, "During handling...") | same traceback | usage |
| `python -m demo_only.fake_model_server --help` (cwd=repo) | usage | usage | usage |
| `PYTHONPATH=foreignA:repo python -m demo_only.fake_model_server --help` from /tmp | usage | traceback `ModuleNotFoundError: No module named 'tools.pathconfine'` exit 1 | not run |
| `PYTHONPATH=repo:foreignA` import `tools.pathconfine` | n/a | repo file imported | n/a |

D, catcher with `--out <scratch file> --control /nonexistent_dir/zz`: both main and PR12 print `FOREIGN confine used` twice then `LISTENING 127.0.0.1 <port>` (killed by `timeout 20`).

## (4) scripts/n8n_api.py import order (raw/hostile-n8n-import.log, hostile-n8n-syspath.log)

Run as `python /repo/scripts/n8n_api.py` (no args) and via an import probe, cwd in {/tmp, repo, repo/scripts}, PYTHONPATH in {empty, src, src:repo, repo:src, foreignA, foreignD, foreignA:repo, foreignA:repo:src, foreignA:src:repo}. Normal outcome: exit 1, `N8N_API_KEY_FILE must be the path of a one-line file with the n8n API key` (the imports worked). Same on MAIN and PR12 for all rows except:

| PYTHONPATH | MAIN | PR12 |
|---|---|---|
| empty | sys.path = repo, src, scripts, ... | sys.path = src, repo, scripts, ... |
| `src:repo` | scripts, scratch, src, repo (unchanged) | same (unchanged) |
| `repo:src` | scripts, scratch, repo, src | same |
| `foreignA:repo` (and with src) | exit 1 `ModuleNotFoundError: No module named 'tools.pathconfine'` | same |
| foreignA or foreignD alone | normal | normal (the script puts repo first) |
| `tools` of foreignD imported before n8n_api | normal | `ImportError cannot import name 'ROOTS_ENV' from 'tools.pathconfine' (.../foreignD/tools/pathconfine.py)` |
| `tools` of foreignA imported before | `ModuleNotFoundError` (probe) | `ModuleNotFoundError` |

## (5) Fake model server options (raw/hostile-fakeserver-mainb.log, -pr12b.log, -extra.log)

Setup: cwd = scratch/fs/cwd, TMPDIR = scratch/fs/tmp, repo on PYTHONPATH, each start with `timeout 8` (exit 124 = server was listening and killed by the timeout). Fake key text `FAKE-KEY-1111`. Server ports 0 except the e2e (48999, stopped by pkill). No process left (pgrep empty).

| Case (option, exact value) | MAIN | PR12 |
|---|---|---|
| `--key-file` absolute outside file | starts | `refused: --key-file: path is outside the allowed folders (add a folder with LEAD_DESK_PATH_ROOTS)` exit 2 |
| `--key-file ../outside/outside.key` | starts | same refusal, exit 2 |
| `--key-file sub/../../outside/outside.key` | starts | same refusal |
| `--key-file sym_key` (symlink in cwd to outside file) | starts | same refusal |
| `--key-file <tmp>/sym_key_tmp` (symlink in TMPDIR to outside) | starts | same refusal |
| `--key-file dirlink/k.key` (dir symlink to outside) | starts | same refusal |
| `--key-file outlink/outside/outside.key` | FileNotFoundError traceback (path wrong, my layout) | same refusal |
| `--key-file in.key`, `<tmp>/tmp.key`, `sub/../in.key` (inside) | starts | starts |
| `--key-file empty.key` | starts | starts |
| `--key-file sub` (folder) | traceback (IsADirectoryError path) | `refused: --key-file: names a folder, not a file` exit 2 |
| `--key-file nope.key` | FileNotFoundError traceback | `refused: --key-file: no such file` exit 2 |
| `--key-file /etc/hostname`, `/proc/self/environ` | starts | outside refusal exit 2 |
| `--call-log` abs outside new / `../outside/new.jsonl` / symlink to outside file (`sym_log`) / dangling symlink to outside / through dir symlink `outlink/new2.jsonl` / `/etc/passwd` | starts | `refused: --call-log: path is outside the allowed folders ...` exit 2 (all six) |
| `--call-log log1.jsonl`, `<tmp>/log2.jsonl` | starts | starts |
| `--call-log "my log.jsonl"` | starts | `refused: --call-log: the name of a new file may only use letters, digits, '.', '_' and '-'` |
| `--call-log nul.txt` | starts | `refused: --call-log: a Windows device name cannot be the name of a new file` |
| `--call-log log.` | starts | `refused: --call-log: not usable as the name of a new file (empty, too long, or ends with a dot)` |
| `--call-log $'a\x01b.jsonl'` | starts | `refused: --call-log: contains a control character` |
| `--call-log nodir/x.jsonl` | starts | `refused: --call-log: a folder on the path does not exist` |
| `--control-file` abs outside / `../outside/ctl.txt` / `sym_ctl` symlink / `outlink/ctl3.txt` | starts | outside refusal exit 2 (all four) |
| `--control-file ctl1.txt`, `<tmp>/ctl2.txt` | starts | starts |
| `--control-file '\\h\s\x'` | starts | `refused: --control-file: the name of a new file may only use letters, digits, '.', '_' and '-'` |
| `--control-file //host/share/x` | starts | outside refusal |

LEAD_DESK_PATH_ROOTS on PR12: `=<scratch/fs/outside>` with `--key-file <outside>/outside.key` starts; `=<outside>/../outside` with `--call-log <outside>/newx.jsonl` starts; `=<cwd>/outlink` with `--key-file outlink/outside.key` starts; `=/` with `--key-file /etc/hostname` starts; `=relative/outside` refused; `=` (empty) refused.

End to end (`--call-log sym_log`, symlink to outside/outlog.jsonl, one POST /v1/messages with no key header):
- MAIN: `curl http=401`; outside file gained `{"ts": 1794563321.5235178, "lead_id": "", "mode": "ok", "status": 401}`.
- PR12: `refused: --call-log: path is outside the allowed folders (add a folder with LEAD_DESK_PATH_ROOTS)`, server not started (`curl http=000`), outside file unchanged (`x`).

Progress notes: evidence/raw/progress-B.txt.
