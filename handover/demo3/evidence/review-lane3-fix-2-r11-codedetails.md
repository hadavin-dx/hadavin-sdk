# R23b code review, fix-2 round 11 (tree 77fa1c0d). Saved by lane3 from the reviewer's inline report (read-only, ran nothing). 0 Blocker, 2 Major, 4 minor, 4 nit.

Core change (link kind, RawStub order, read_secret_file order) technically correct: open flags O_RDONLY|O_NONBLOCK|O_NOCTTY|O_NOFOLLOW(+O_BINARY); fstat S_ISREG, lstat link and (ino,dev) compare, mode mask 0o077; ELOOP mapped to link; fixed texts, no path or OSError echoed; all path callers route via refuse_unusable_file / env_file_problem; book check before mkdir and lock.

MAJOR 1: stale test fails on every non-root run, no root twin. tests/test_n8n_api_url.py:510-524 test_a_key_file_without_read_permission_is_a_clean_message_with_the_error_type_only is skipped when euid 0 and asserts "PermissionError" in msg; read_secret_file (envnum.py:146-149) now answers the fixed text "the n8n API key file cannot be read" with no error type (sibling at :501-507 already updated). Red in CI for any non-root run. Fix: assert msg == the fixed text plus no-path/no-key; add root twin patching os.open to raise PermissionError(13,"x") for the key path (as r6:96 and r8:277 do), in read_secret_file directly (SettingRefused, fixed text, no path) and in n8n_api import (same SystemExit text).
MAJOR 2: new `link` refusal not in docs (docs/settings.md:7 db_path list; docs/limits.md:134; docs/settings.md:87; contract.md exit-4 list). OPEN-FOR-STACK-DOCS is not an allowed fix-dont-defer exception: fix now.
minor 1: sibling names: run_stats.py:16-19 (`<path>.tmp` write_text), lockfile.py:39 and :60 (`<resolved>.lock` "a+b"), live_claude.py:230 and :162 (`<ledger>.lock`): a dangling link at the derived name is followed and creates a file at its target. Fix: .tmp via os.open O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW; locks: env_file_problem on the derived path or O_NOFOLLOW; one test per name (planted dangling link, refusal, no file at target).
minor 2: S2 real gap: autouse fixture in tests/conftest.py wrapping lockfile.acquire, collecting handles, teardown asserts all closed (outer wrapper to the opt-in fixture).
minor 3: no valid red evidence for r9 rows 5 and 7 (4 failures from incomplete scratch copy missing fresh_script import): redo red run with complete scratch copy.
minor 4: mutant N5 not isolated (fails 73 tests, 72 same as N7): re-plant as pure move. No mutants for parent-walk _is_link branch alone or the open flags.
nit 1: envnum.py:80 docstring "every probe goes through path_kind" but _is_link calls os.lstat (envnum.py:204).
nit 2: RawStub counts an empty connection (support.py:656-667): guard increment with b"\r\n\r\n" in buf.
nit 3: loop test tests/test_one_key_file_rule_and_path_walk.py:326 (via _loop :320-323) has no POSIX marker.
nit 4: redundant assert after wait_until r7:1250-1251.
Counts r11 file (13 items): 12 fail on old code = 7 real behaviour + 1 function-absent/text pin + 4 scratch artefacts; 1 pass-on-old-code regression guard. Mutants 8 killed, S2 survived, baseline x3 green (825).
Not checked: nothing run; no non-root run (Major 1 by reading); Windows/NTFS not exercised; hygiene "31 passed" unverified by the reviewer.
