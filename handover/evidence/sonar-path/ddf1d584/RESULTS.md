# EVIDENCE RUNNER results: sonar-path (ORDER 260, path containment, security path)

Head: ddf1d584c280593d4db82e81489b440fae3b876f (origin/wip/cloud-sonar-path), tree 9a79548c419949c0bd0e501dbc8d4788834d3dd7.
Base for fail-before: origin/main a8b4d8e83f9fb29c09079417505682fd8b5464be. Run 2026-11-12 about 20:32 to 20:50 UTC (02:02 to 02:20 IST on 13 Nov).
Linux, Python 3.13.18, clean detached worktree, own venv, cloud and API environment variables unset. This file records raw results and does not judge them.
Raw logs (outside the repository): /home/user/build/evidence-raw/sonarpath-ddf1d584/

## Not run / deviations (read first)

1. Full pytest FAILED on the first run: 1 failed, 10686 passed, 1 skipped, 28 deselected (item 1). The failure is
   `tests/demo_askdata/test_validate_harm.py::...[dblink-connect]`: the database SERVER (not the test) tried to connect to the default
   socket path and my own Postgres runs on a private port. Same cause as the earlier ledger row for dd5c7242. I restarted my own Postgres
   with the port in the server's environment and re-ran that one file: 253 passed (item 1b). The whole suite was NOT re-run after that, so
   there is no single green full-suite run at this head. The first run's one failure is environment, and nothing in it touches path code,
   but that is my reading, not a result.
2. `bandit` is not in the project's test group (only in the `scan` group), so `uv run ... bandit` failed to start (exit 2, item 3d). I ran
   `uvx --from bandit==1.9.4 bandit -q -r src demos tools -ll` instead (version pinned to the one in pyproject's scan group, not the
   locked one). Output has only warnings (unknown names in comments, one `nosec` on src/hadavin_sdk/tools.py:389), no findings.
3. Fail-before (item 4) used a name-only stub `pathguard.py` that has the same public names and does no checks (path functions return their
   input; `PathRefused` keeps its `rule`). I also copied the two tripwire fixture files tests/fixtures/pathguard_tripwire_*.py (the tripwire
   test needs them). Result on the 4 files: 37 failed, 36 passed (counts below). **`tests/test_pathguard_callers.py` passed 5 of 5 on
   origin/main code**, although its docstring says these tests fail on main. I did not investigate why; the raw log is
   failbefore-test_pathguard_callers.log. A reviewer should look at this.
4. Hostile inputs (item 5) ran in a throw-away temp folder, made-up names only, through `pathguard` and `k1b.atomic.atomic_write`.
   Not run: Windows-only behaviour (the rules are text rules and were exercised on Linux only); `O_NOFOLLOW` has no effect off Linux.
5. Mutants ran one heavy job at a time through heavy.sh, after the full pytest finished (they rewrite files). Lint, bandit, scan and gitleaks
   ran while pytest was running, before the mutant scripts started. `git status` after all runs: clean (0 changed files).
6. Ledger: no earlier row for this head, so nothing was skipped as a repeat.
7. Not run: ruff on files outside src tests demos tools; CodeQL, SonarCloud, CodeRabbit (CI services); the performance and live markers (excluded by the brief).

## Results table

| Item | Command | Exit | Counts | Seconds |
|---|---|---|---|---|
| 1 | heavy.sh uv run --all-extras --group test pytest -m "not live and not perf" -p no:cacheprovider -q -rs (own Postgres 16.15, private port 34871) | 1 | 1 failed, 10686 passed, 1 skipped, 28 deselected | 271 |
| 1b | same runner, only tests/demo_askdata/test_validate_harm.py, Postgres restarted with the port in its own environment | 0 | 253 passed | 23 (test time) |
| 2a | heavy.sh uv run ... python tests/pathguard_mutants.py | 0 | 22 of 22 good, problems [] | 21 |
| 2b | heavy.sh uv run ... python tests/stage_mutants.py | 0 | 37 of 37 good, problems [] | 41 |
| 3a | ruff check src tests demos tools | 0 | All checks passed | <1 |
| 3b | ruff format --check src tests demos tools | 0 | 327 files already formatted | <1 |
| 3c | uvx --from bandit==1.9.4 bandit -q -r src demos tools -ll | 0 | no findings (warnings only, see deviation 2) | 1 |
| 3d | uv run bandit (as the brief said) | 2 | failed to spawn, not installed in the test group | 0 |
| 3e | python tools/scan_repo.py | 0 | no output | <1 |
| 3f | gitleaks git --redact --log-opts origin/main..HEAD (config .gitleaks.toml) | 0 | no leaks found | 1 |
| 4a | fail-before: tests/test_pathguard.py on main + stub | 1 | 35 failed, 13 passed | 4 |
| 4b | fail-before: tests/test_pathguard_callers.py | 0 | 5 passed, 0 failed (see deviation 3) | 1 |
| 4c | fail-before: tests/test_pathguard_tripwire.py | 1 | 1 failed, 6 passed | 1 |
| 4d | fail-before: tests/test_k1b_cli.py | 1 | 1 failed, 20 passed | 4 |
| 5 | hostile inputs, script hostile.py (raw dir) | 0 | 76 rows below | 1 |

Item 1 failure name: test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect] (psycopg SqlclientUnableToEstablishSqlconnection, socket /var/run/postgresql/.s.PGSQL.5432 not found).
Item 4 failing tests on main: 35 in test_pathguard.py (R1 to R11 rule tests), test_no_file_operation_in_k1b_or_the_cli_works_on_an_unchecked_path, test_report_write_failure_leaves_started_then_failed_and_no_score_run.
Item 2a: 22 mutants KILLED. Item 2b: 37 KILLED.

## Item 5: hostile inputs against pathguard (command: python hostile.py with PYTHONPATH=src; T = temp folder)

"base" holds real/, plus planted links. "ACCEPTED" shows the returned path. Rule numbers are the module's own (R1 empty or dot, R2 separator, R3 colon,
R4 control character, R5 length, R6 trailing dot or space, R7 device name, R8 escape, R10 cannot resolve, R11 wrong type).

| # | Case (call) | Input | Outcome |
|---|---|---|---|
| H01 | component, NUL byte | 'a\x00b' | REFUSED R4 |
| H02 | join, NUL byte | 'a\x00b' | REFUSED R4 |
| H03 | inside, NUL in path | base + '/a\x00b' | REFUSED R10 |
| H04 | operator_dir, NUL | base + '\x00y' | REFUSED R4 |
| H05 | join, '..' | '..' | REFUSED R1 |
| H06 | join, 'a..b' | 'a..b' | ACCEPTED T/base/a..b |
| H07 | join, '../outside' as one name | '../outside' | REFUSED R2 |
| H08 | join, '..' then 'outside' | two names | REFUSED R1 |
| H09 | inside, .. segments leaving base | base/real/../../outside/secret.txt | REFUSED R8 |
| H10 | inside, .. segments staying in base | base/real/../real | ACCEPTED T/base/real |
| H11 | join, absolute name | '/etc/passwd' | REFUSED R2 |
| H12 | join, absolute second name | 'real', '/etc' | REFUSED R2 |
| H13 | inside, absolute path outside | /etc/passwd | REFUSED R8 |
| H14 | join, backslash | 'a\\b' | REFUSED R2 |
| H15 | join, drive-relative | 'C:x' | REFUSED R3 |
| H16 | join must_exist, symlink at the end to outside file | filelink | REFUSED R8 |
| H17 | join, same symlink, not must_exist | filelink | REFUSED R8 |
| H18 | join, symlink in the middle (to outside folder) | dirlink, secret.txt | REFUSED R8 |
| H19 | inside, symlink in the middle | base/dirlink/secret.txt | REFUSED R8 |
| H20 | join, symlink inside base to inside base | innerlink | ACCEPTED, returns the target T/base/real |
| H21 | join, symlink loop (not must_exist) | loop1 <-> loop2 | **ACCEPTED T/base/loop1** (Python 3.13 non-strict resolve does not raise on a loop; the code's comment expects RuntimeError from 3.12) |
| H22 | join must_exist, dangling symlink | dangling | REFUSED R10 |
| H23 | join, dangling symlink pointing outside | dangling2 | REFUSED R8 |
| H24 to H27 | join, trailing dot or space | 'a.', 'a ', 'a. ', 'a .' | REFUSED R6 (all four) |
| H28 to H33 | join, device names | CON, con.txt, NUL, COM1, COM+superscript 1, LPT3.log | REFUSED R7 (all six) |
| H34 | join, leading space | ' a' | ACCEPTED T/base/ a |
| H35 | join, colon | 'a:b' | REFUSED R3 |
| H36 | join, CONIN$ | 'CONIN$' | REFUSED R7 |
| H37 | join, 255-byte name | 'a'*255 | ACCEPTED |
| H38 | join, 256-byte name | 'a'*256 | REFUSED R5 |
| H39 | join, 128 two-byte letters (256 bytes) | 'é'*128 | REFUSED R5 |
| H40 | inside, path over 4096 characters | base/ + 'a/'*2100 | REFUSED R5 |
| H41 | operator_dir, 5000 characters | 'a'*5000 | REFUSED R5 |
| H42 | join, U+2024 x2 (one dot leader) | look-alike dots | **ACCEPTED** (a plain name, not a dot segment on Linux) |
| H43 | join, U+FF0E x2 (fullwidth full stop) | look-alike dots | **ACCEPTED** |
| H44 | join, U+2025 (two dot leader) | look-alike dots | **ACCEPTED** |
| H45 | join, U+FE52 x2 (small full stop) | look-alike dots | **ACCEPTED** |
| H46 | join, U+2215 (division slash) in a name | 'a∕b' | **ACCEPTED** |
| H47 | join, U+FF0F (fullwidth solidus) in a name | 'a／b' | **ACCEPTED** |
| H48 | join, U+202E (right-to-left override) | 'a‮txt' | REFUSED R4 |
| H49 | join, U+0085 | 'a\x85b' | REFUSED R4 |
| H50 | join, U+200B (zero-width space) | 'a​b' | **ACCEPTED** (not in the control set) |
| H51 | join, trailing U+2024 | 'a․' | **ACCEPTED** (R6 only looks at ASCII dot and space) |
| H52 | join, decomposed e + U+0301 | 'é' | ACCEPTED, name kept as typed (documented: no normal-form repair) |
| H53 | join, lone surrogate | 'a\udc80b' | ACCEPTED |
| H54 | join, empty name | '' | REFUSED R1 |
| H55 | join, '.' | '.' | REFUSED R1 |
| H56 | join, no names | () | ACCEPTED, returns the resolved base |
| H57 | component, None | None | REFUSED R1 |
| H58 | component, bytes | b'a' | REFUSED R1 |
| H59 | symlink swapped AFTER the check, returned path reused | folder replaced by a link to outside, then a file written via the returned path | **the file landed outside the base** (documented in the module as not closed: the attacker is text, not a racing process) |
| H60 | atomic_write, plain | ok.txt | wrote 'hello\n' |
| H61 | atomic_write, '..' | '..' | REFUSED R1 |
| H62 | atomic_write, NUL | 'a\x00b' | REFUSED R4 |
| H63 | atomic_write, 'CON' | 'CON' | REFUSED R7 |
| H64 | atomic_write, 'a/b' | 'a/b' | REFUSED R2 |
| H65 | atomic_write, 240-byte name (temp name would exceed 255) | 'a'*240 | REFUSED R5 |
| H66 | atomic_write, final name is a symlink to an outside file | filelink | REFUSED R8; the outside file unchanged ('outside-content') |
| H67 | atomic_write, temp file already exists (token forced to collide) | .t.txt.0000000000000000.tmp | **FileExistsError (plain OS error, not PathRefused)**; the existing temp file unchanged, no t.txt created (O_EXCL held) |
| H68 | atomic_write, temp name pre-planted as a symlink to an outside file | .u.txt.1111111111111111.tmp | REFUSED R8 (the join check, before open); outside file unchanged |
| H69 | atomic_write over a target that is a hard link to an outside file | hard.txt | ACCEPTED; the outside file stayed 'outside-content', the target now holds 'NEW', the two no longer share an inode (os.replace breaks the link, nothing is written through it) |
| H70 | join, a file in base that is a hard link to an outside file, kind=file | hardin | **ACCEPTED** (documented as out of scope) |
| H71 | operator_dir, existing folder | base | ACCEPTED |
| H72 | operator_dir, missing, must_exist=False | base/new | ACCEPTED |
| H73 | operator_dir, a file | hardin | REFUSED R11 |
| H74 | operator_file, a folder | real | REFUSED R11 |
| H75 | operator_dir, empty string | '' | **ACCEPTED, resolves to the current folder** |
| H76 | operator_dir, newline | 'a\nb' | REFUSED R4 |

Accepted-looking rows a reviewer may want to judge (recorded, not judged): H21, H42 to H47, H50, H51, H53, H59, H67, H70, H75.
