# Fresh review 3 of followup-ab-v3.patch (sha256 f971de87... verified) -- CLEAN (no Blocker, no Major)
Scratch /tmp/work/rv-v3 (clone of 61ded9e, forward apply OK: 13 modified + tests/test_followup_b.py). Pytest only via run-un.sh (unshare -n, loopback up).

Suppressions: all added lines grepped (noqa, type: ignore, nosec, NOSONAR, nosemgrep, pragma, pylint: disable, fmt: off/skip): ONE hit,
`from tools.pathconfine import ROOTS_ENV, PathRefused, confine_existing  # noqa: E402` (n8n_api.py:51). Base has the same line with the same
noqa (`... import confine_existing  # noqa: E402`, line 49): pre-existing suppression, import list changed. The patch removes one `# type: ignore[call-overload]`. No new suppression.

## Blocker / Major: none

## Minor (brief)
1. default_control_name: not collision-free against a deliberately built name. "my mail.jsonl" -> my_mail.jsonl.bd2f33ac.mode, and the plain name
   "my_mail.jsonl.bd2f33ac" -> the same file. Needs someone to compute the hash; accidental chance ~2^-32. Brute force over alphabet "ab _.e-acute" length 1-5: 9330 names, 0 collisions. Docstring says "never share" (slightly strong).
2. Walker gaps (not in the docstring's limit list): `os.environ[...]`/`input()` as a path source and `io.open` as a sink are not flagged (probe). Docstring claims only command line, parameters, file content, so not false, but the "cannot see" list omits them.
3. M16-type mutant `sqlite3.connect(os.fspath(path)+"x")` on a clean path survives: equivalent (path is clean), not a real survivor.
4. default_control_name adds 9 chars; a 250-char --out name could pass the check and fail at the file system (name-length limit). Pre-existing class.
5. fake_model_server run as a FILE (python demo_only/fake_model_server.py) with a foreign `tools` first on PYTHONPATH: ModuleNotFoundError traceback. Docstring says so (honest). `-m` from the repo root works.

## (1) M1: fixed
read_book now splits the URI build into its own try: `except PathRefused -> InputError`. Three new tests (read_book both anywhere modes; check_invariants.main -> EXIT_INPUT, stderr "INPUT ERROR:", no Traceback; run_real_check.sending_rows -> 0) pass, and fail on 61ded9e sources. Other callers of readonly_sqlite_uri/read_book: only check_invariants.py:145/740, run_real_check.py:422 (catches InputError, returns 0) and :984 (catches InputError, prints, EXIT_FAILED). None escape. Tests use a monkeypatched stand-in (ntpath text only); real Windows not run.

## (2) Walker
20 own mutants on the real sources (script /tmp/work/rv3-mut/mut.py; test_no_flagged_site_opens_a_raw_argument only): raw dst write, if-branch rebind, IfExp raw, tuple-unpack raw, raw touch, alias of args, raw key open, call_log rebound raw, os.replace raw, raw open before confine, n8n raw import file, load_driver argv write, nested helper with param, os.utime raw, shutil.copy raw, walrus, for-loop, f-string path, try/except rebinding, sqlite connect: 19 KILLED, 1 survivor (M16, equivalent, see Minor 3).
Direct probes of _raw_opens (25 shapes, /tmp/work/rv3-mut/probe.py): flagged correctly: identity helper, dict container, lambda, getattr, vars, join, comprehension, os.rename/makedirs/listdir/symlink/rmtree/os.open, Path.mkdir/unlink, class-method param, sqlite raw. Clean correctly: confine then use, confine IfExp, rebind-then-confine, tainted CONTENT written to a fixed file (the v2 false rejection is gone), argv used only for len. Missed: environ, input(), io.open (Minor 2).
False rejections of current real sites: none (all 7 files pass; run_real_check outside main/load_env is out of scope, stated). Docstring limit list: honest for what it lists; incomplete per Minor 2.

## (3) default_control_name
Plain names unchanged (mail.jsonl -> mail.jsonl.mode; "x.1234abcd.mode" -> "...mode.mode"). Names with replaced characters get .<8 hex of sha256 of original>. my mail/my_mail, bé/bè, "a b"/"a_b", newline, RTL char: all distinct. A name already ending in 8 hex chars: unchanged and fine unless it equals a constructed hash name (Minor 1).

## (4) UNC absolute-first
splitroot()[0] of abspath: posix never reports a drive, so "//server/share/x.db" is accepted on Linux (test asserts). 326 tests of test_path_confinement + test_followup_b + test_sonar_p2_choke_points pass (1 skipped, ntpath.isreserved needs 3.13). ntpath stand-in refuses 9 shapes incl `\\?\C:`, `\\.\C:`, `\\localhost\c$`, mixed separators, and relative-name-in-share via fake abspath; message now says "device or network path".

## (5) foreign tools and fake_model_server
Foreign `tools` (empty package with other.py) first on PYTHONPATH, started from another cwd: check_invariants, catcher, load_driver --help all work. fake_model_server probe (jail in /home/user, no roots env, run under unshare): symlink-to-outside key file, symlink dir, `../`, absolute outside, dangling symlink to outside, non-existent parent, `.`, space in name: all exit 2 "refused: --opt: ..." with nothing printed as listening, outside dir unchanged (only k.txt); inside new files start; LEAD_DESK_PATH_ROOTS widens as documented. (A first run with the jail under /tmp was accepted: /tmp is an allowed root, expected, not a defect.) Jail dirs removed.

## (6) fails-before
Test files copied onto an unmodified 61ded9e tree, the 26 new test names (83 ids): 29 FAILED, 54 passed. Ids confirmed failing on old code (more than 10): read_book x3 network tests, test_a_windows_network_path_is_refused..., fake_model_server refuse x3 + hands-checked-paths, foreign-tools x9, hard-link doc, read_book not-a-path x3 + printable label, catcher control name with space, portal_demo re-export, urls docstring, n8n_api src order, start_all comment, no_flagged_site[fake_model_server]. The 54 that pass are finder shape self-tests, per-site guards on already compliant sites, characterisation (hard link passes the check, sys left alone, exclusive bind) as the builder says.

## (7) hang pair
test_followup_b.py then test_load_tools.py under unshare -n, 3 runs: 83 passed (11.8 s, 12.8 s, 11.9 s). Not reproduced.

## (8) gates (applied tree)
ruff check clean; ruff format --check 157 files clean; mypy --platform linux and win32: no issues in 28 files each; bandit -ll: 0 medium, 0 high (12 low, in line with base); hygiene + gitleaks_exceptions + codeant_hygiene with DPLD_REQUIRE_SCAN=1 (git add -A, gpgsign off via GIT_CONFIG_COUNT): 75 passed; gitleaks dir hits only in untracked __pycache__/.mypy_cache/.ruff_cache (no source file). Touched tests: 326 passed, 1 skipped.

Not checked: Windows itself (UNC/ntpath text-level only), macOS, Python 3.13, full suite (ordered not to), CI literal-scan git grep beyond hygiene tests.
Processes: only test subprocesses and the probe servers (terminated by the probe); no pkill; worktrees /tmp/work/rv-v3, rv-v3b left in place.
