# Final gate report: dpld-final5a-5d352f7302dd.tar.gz  (full mode)

This file records commands, exit codes and the tools' own output, word for word. It makes no pass/fail judgement of its own.

## Header

- tarball: `/tmp/linux-ev/dpld-final5a-5d352f7302dd.tar.gz`
- tarball_sha256: `e99cb75d03ddddb8532eb30463e1d95446336d0796a23d6ac0319f2a7aae93f2`
- tree: `/tmp/linux-ev/wA/src/dpld-final5a-5d352f7302dd`
- workdir: `/tmp/linux-ev/wA`
- host: `Linux-6.18.44-fc-v310-x86_64-with-glibc2.39`
- cores: `4`
- python: `Python 3.12.3`
- venv: `/tmp/linux-ev/wA/venv (the unpacked copy was made a throw-away git repository so the git-based hygiene tests can run)`
- started_utc: `2026-11-09 16:09:44`
- mode: `full`
- server_py_hooks: `PATCHED hooks 1 and 2 in /tmp/linux-ev/wA/src/dpld-final5a-5d352f7302dd/src/lead_desk/server.py | hook 3: constants.LISTEN_QUEUE = 1024`

**Edit applied to the UNPACKED COPY only (never to the tarball):** the `server.py` hook edits from CONTRACT-DELTA.md ("server.py hooks": catch LockHeldError and OSError, `start_background()` before `startup()`, `stop_background()` first in `finally`). Result of the patch step: `PATCHED hooks 1 and 2 in /tmp/linux-ev/wA/src/dpld-final5a-5d352f7302dd/src/lead_desk/server.py | hook 3: constants.LISTEN_QUEUE = 1024`.

Stage order is fixed and one thing runs at a time; free ports are picked per step. Exit code 124 here means the step hit its time limit and was stopped by this script.

## Stage 0: Set-up (unpack, own venv, hook patch)

| step | exit | seconds | limit s | raw file |
|---|---|---|---|---|
| patch-server-hooks | 0 | 0.0 | 60 | `/tmp/linux-ev/wA/raw/0-patch-server-hooks.txt` |
| pip-install-hashed | 0 | 5.4 | 900 | `/tmp/linux-ev/wA/raw/0-pip-install-hashed.txt` |
| venv-create | 0 | 2.6 | 300 | `/tmp/linux-ev/wA/raw/0-venv-create.txt` |

### patch-server-hooks

Command: `cat /tmp/linux-ev/wA/raw-patch.txt`  (cwd `None`)  exit code: 0

(whole output, verbatim)
```
PATCHED hooks 1 and 2 in /tmp/linux-ev/wA/src/dpld-final5a-5d352f7302dd/src/lead_desk/server.py | hook 3: constants.LISTEN_QUEUE = 1024
```

### pip-install-hashed

Command: `/tmp/linux-ev/wA/venv/bin/python -m pip install --require-hashes -r requirements-dev.txt`  (cwd `/tmp/linux-ev/wA/src/dpld-final5a-5d352f7302dd`)  exit code: 0

(whole output, verbatim)
```
Collecting ast-serialize==0.13.1 (from -r requirements-dev.txt (line 7))
  Using cached ast_serialize-0.13.1-cp39-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (1.3 MB)
Collecting bandit==1.9.4 (from -r requirements-dev.txt (line 66))
  Using cached bandit-1.9.4-py3-none-any.whl (134 kB)
Collecting iniconfig==2.3.1 (from -r requirements-dev.txt (line 70))
  Using cached iniconfig-2.3.1-py3-none-any.whl (7.6 kB)
Collecting librt==0.16.0 (from -r requirements-dev.txt (line 74))
  Using cached librt-0.16.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (531 kB)
Collecting markdown-it-py==4.2.0 (from -r requirements-dev.txt (line 213))
  Using cached markdown_it_py-4.2.0-py3-none-any.whl (91 kB)
Collecting mdurl==0.1.2 (from -r requirements-dev.txt (line 217))
  Using cached mdurl-0.1.2-py3-none-any.whl (10.0 kB)
Collecting mypy==2.4.1 (from -r requirements-dev.txt (line 221))
  Using cached mypy-2.4.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (15.6 MB)
Collecting mypy-extensions==1.2.0 (from -r requirements-dev.txt (line 275))
  Using cached mypy_extensions-1.2.0-py3-none-any.whl (5.1 kB)
Collecting packaging==26.3 (from -r requirements-dev.txt (line 279))
  Using cached packaging-26.3-py3-none-any.whl (129 kB)
Collecting pathspec==1.1.1 (from -r requirements-dev.txt (line 283))
  Using cached pathspec-1.1.1-py3-none-any.whl (57 kB)
Collecting pluggy==1.7.0 (from -r requirements-dev.txt (line 287))
  Using cached pluggy-1.7.0-py3-none-any.whl (27 kB)
Collecting pygments==2.21.0 (from -r requirements-dev.txt (line 291))
  Using cached pygments-2.21.0-py3-none-any.whl (1.3 MB)
Collecting pytest==9.2.0 (from -r requirements-dev.txt (line 297))
  Using cached pytest-9.2.0-py3-none-any.whl (411 kB)
Collecting pyyaml==6.0.3 (from -r requirements-dev.txt (line 301))
  Using cached pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (807 kB)
Collecting rich==15.0.0 (from -r requirements-dev.txt (line 376))
  Using cached rich-15.0.0-py3-none-any.whl (310 kB)
Collecting ruff==0.17.4 (from -r requirements-dev.txt (line 380))
  Using cached ruff-0.17.4-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (10.6 MB)
Collecting stevedore==5.9.1 (from -r requirements-dev.txt (line 400))
  Using cached stevedore-5.9.1-py3-none-any.whl (54 kB)
Collecting typing-extensions==4.16.0 (from -r requirements-dev.txt (line 404))
  Using cached typing_extensions-4.16.0-py3-none-any.whl (45 kB)
Installing collected packages: typing-extensions, stevedore, ruff, pyyaml, pygments, pluggy, pathspec, packaging, mypy-extensions, mdurl, librt, iniconfig, ast-serialize, pytest, mypy, markdown-it-py, rich, bandit
Successfully installed ast-serialize-0.13.1 bandit-1.9.4 iniconfig-2.3.1 librt-0.16.0 markdown-it-py-4.2.0 mdurl-0.1.2 mypy-2.4.1 mypy-extensions-1.2.0 packaging-26.3 pathspec-1.1.1 pluggy-1.7.0 pygments-2.21.0 pytest-9.2.0 pyyaml-6.0.3 rich-15.0.0 ruff-0.17.4 stevedore-5.9.1 typing-extensions-4.16.0
```

### venv-create

Command: `/usr/bin/python3.12 -m venv /tmp/linux-ev/wA/venv`  (cwd `None`)  exit code: 0

(whole output, verbatim)
```

```

## Stage 1: Lint, types, security scan, schema check

| step | exit | seconds | limit s | raw file |
|---|---|---|---|---|
| bandit | 0 | 0.4 | 300 | `/tmp/linux-ev/wA/raw/1-bandit.txt` |
| check-schema | 0 | 0.1 | 300 | `/tmp/linux-ev/wA/raw/1-check-schema.txt` |
| mypy-linux | 0 | 1.3 | 900 | `/tmp/linux-ev/wA/raw/1-mypy-linux.txt` |
| ruff-check | 0 | 0.0 | 300 | `/tmp/linux-ev/wA/raw/1-ruff-check.txt` |
| ruff-format-check | 0 | 0.0 | 300 | `/tmp/linux-ev/wA/raw/1-ruff-format-check.txt` |

### bandit

Command: `/tmp/linux-ev/wA/venv/bin/bandit -q -ll -r src tools -c pyproject.toml`  (cwd `/tmp/linux-ev/wA/src/dpld-final5a-5d352f7302dd`)  exit code: 0

(whole output, verbatim)
```

```

### check-schema

Command: `/tmp/linux-ev/wA/venv/bin/python scripts/check_schema.py`  (cwd `/tmp/linux-ev/wA/src/dpld-final5a-5d352f7302dd`)  exit code: 0

(last 40 lines, verbatim; whole output in raw file)
```
PASS journal_mode is wal
PASS second init_schema is a no-op
PASS schema text can be re-run (IF NOT EXISTS): no error, same objects -> 18 objects before and after
PASS leads: NULL lead_id refused -> IntegrityError: NOT NULL constraint failed: leads.lead_id
PASS followups: NULL lead_id refused -> IntegrityError: NOT NULL constraint failed: followups.lead_id
PASS receipts: bad source rejected -> IntegrityError: CHECK constraint failed: source IN ('form','webhook')
PASS receipts: empty source_ref rejected -> IntegrityError: CHECK constraint failed: length(source_ref) BETWEEN 1 AND 128
PASS receipts: 129-char source_ref rejected -> IntegrityError: CHECK constraint failed: length(source_ref) BETWEEN 1 AND 128
PASS receipts: UNIQUE(source, source_ref) -> IntegrityError: UNIQUE constraint failed: receipts.source, receipts.source_ref
PASS receipts: upsert bumps attempts, receipts_immutable NOT fired, payload untouched -> (2, '{"email":"ada@example.test","name":"Ada Example"}')
PASS receipts: update payload aborts -> IntegrityError: receipt fields never change
PASS receipts: update source_ref aborts -> IntegrityError: receipt fields never change
PASS receipts: update received_at aborts -> IntegrityError: receipt fields never change
PASS receipts: delete aborts -> IntegrityError: receipts are never deleted
PASS receipts: INSERT OR REPLACE aborts (delete trigger fires with recursive_triggers=ON) -> IntegrityError: receipts are never deleted
PASS receipts: bad outcome value rejected -> IntegrityError: CHECK constraint failed: outcome IN ('new','duplicate','review')
PASS receipts: first verdict write (one UPDATE, five columns) passes
PASS receipts: second verdict write aborts -> IntegrityError: a verdict is written once
PASS receipts: attempts can still be bumped after a verdict
PASS leads: unique email_key (second lead, same key) -> IntegrityError: UNIQUE constraint failed: leads.email_key
PASS leads: one lead per receipt (UNIQUE receipt_id) -> IntegrityError: UNIQUE constraint failed: leads.receipt_id
PASS leads: foreign key to receipts enforced -> IntegrityError: FOREIGN KEY constraint failed
PASS leads: empty name rejected -> IntegrityError: CHECK constraint failed: length(name) BETWEEN 1 AND 200
PASS leads: 201-char name rejected -> IntegrityError: CHECK constraint failed: length(name) BETWEEN 1 AND 200
PASS leads: email_key shorter than 3 rejected -> IntegrityError: CHECK constraint failed: length(email_key) BETWEEN 3 AND 254
PASS leads: update aborts -> IntegrityError: lead lines are write-once
PASS leads: delete aborts -> IntegrityError: lead lines are write-once
PASS leads: INSERT OR REPLACE aborts -> IntegrityError: lead lines are write-once
PASS followups: bad state rejected -> IntegrityError: CHECK constraint failed: state IN ('pending','sending','sent','failed','unknown')
PASS followups: bad ai_label rejected -> IntegrityError: CHECK constraint failed: ai_label IN ('hot','warm','cold')
PASS followups: ai_label written once with WHERE ai_label IS NULL (1 row, then 0) -> (1, 0)
PASS followups: claim changes exactly one row, the second claim changes 0 -> (1, 0)
PASS followups: sent is final (state) -> IntegrityError: a sent follow-up is final
PASS followups: sent is final (any column) -> IntegrityError: a sent follow-up is final
PASS view review_items: R, D and F(unknown) rows; clean duplicate and sent follow-up absent -> ['D6', 'FL000000000006', 'R5']
PASS view review_items has 7 columns
PASS stalled branches run with a bound :before (open receipts r2, r6; no stalled follow-up) -> [('O4', 'receipt', 'stalled', 'open receipt', None, 1000, 'webhook'), ('O8', 'receipt', 'stalled', 'open receipt', None, 1000, 'form')]
PASS mutation seam: without the block two leads share one email_key
PASS mutation seam: the unique index is absent in the mutant
RESULT ALL PASS
```

### mypy-linux

Command: `/tmp/linux-ev/wA/venv/bin/mypy --platform linux`  (cwd `/tmp/linux-ev/wA/src/dpld-final5a-5d352f7302dd`)  exit code: 0

(whole output, verbatim)
```
Success: no issues found in 17 source files
```

### ruff-check

Command: `/tmp/linux-ev/wA/venv/bin/ruff check`  (cwd `/tmp/linux-ev/wA/src/dpld-final5a-5d352f7302dd`)  exit code: 0

(whole output, verbatim)
```
All checks passed!
```

### ruff-format-check

Command: `/tmp/linux-ev/wA/venv/bin/ruff format --check`  (cwd `/tmp/linux-ev/wA/src/dpld-final5a-5d352f7302dd`)  exit code: 0

(whole output, verbatim)
```
50 files already formatted
```

## Stage 2: Full pytest, repeated

| step | exit | seconds | limit s | raw file |
|---|---|---|---|---|
| pytest-run-1 | 1 | 357.6 | 1200 | `/tmp/linux-ev/wA/raw/2-pytest-run-1.txt` |
| pytest-run-2 | 1 | 354.7 | 1200 | `/tmp/linux-ev/wA/raw/2-pytest-run-2.txt` |
| pytest-run-3 | 1 | 354.5 | 1200 | `/tmp/linux-ev/wA/raw/2-pytest-run-3.txt` |

### pytest-run-1

Command: `/tmp/linux-ev/wA/venv/bin/python -m pytest -q -rf -p no:cacheprovider --no-header`  (cwd `/tmp/linux-ev/wA/src/dpld-final5a-5d352f7302dd`)  exit code: 1

Last line (verbatim):
```
7 failed, 595 passed, 1 skipped, 2 xfailed in 357.22s (0:05:57)
```
FAILED/ERROR lines (verbatim, all):
```
FAILED tests/test_flow.py::test_failed_retry - AssertionError: assert ('pendi...
FAILED tests/test_flow.py::test_retry_twice_concurrent - AssertionError: asse...
FAILED tests/test_hygiene.py::test_hygiene_scan_public - AssertionError: gitl...
FAILED tests/test_hygiene.py::test_hygiene_wordlist - AssertionError: set HYG...
FAILED tests/test_infra.py::test_demo_adapters - AssertionError: assert 'unkn...
FAILED tests/test_mutants.py::test_mutant_no_claim - AssertionError: Regex pa...
FAILED tests/test_server_hardening.py::test_reply_write_fails_after_commit_followup_still_runs
```

### pytest-run-2

Command: `/tmp/linux-ev/wA/venv/bin/python -m pytest -q -rf -p no:cacheprovider --no-header`  (cwd `/tmp/linux-ev/wA/src/dpld-final5a-5d352f7302dd`)  exit code: 1

Last line (verbatim):
```
7 failed, 595 passed, 1 skipped, 2 xfailed in 354.34s (0:05:54)
```
FAILED/ERROR lines (verbatim, all):
```
FAILED tests/test_flow.py::test_failed_retry - AssertionError: assert ('pendi...
FAILED tests/test_flow.py::test_retry_twice_concurrent - AssertionError: asse...
FAILED tests/test_hygiene.py::test_hygiene_scan_public - AssertionError: gitl...
FAILED tests/test_hygiene.py::test_hygiene_wordlist - AssertionError: set HYG...
FAILED tests/test_infra.py::test_demo_adapters - AssertionError: assert 'unkn...
FAILED tests/test_mutants.py::test_mutant_no_claim - AssertionError: Regex pa...
FAILED tests/test_server_hardening.py::test_reply_write_fails_after_commit_followup_still_runs
```

### pytest-run-3

Command: `/tmp/linux-ev/wA/venv/bin/python -m pytest -q -rf -p no:cacheprovider --no-header`  (cwd `/tmp/linux-ev/wA/src/dpld-final5a-5d352f7302dd`)  exit code: 1

Last line (verbatim):
```
6 failed, 596 passed, 1 skipped, 2 xfailed in 354.19s (0:05:54)
```
FAILED/ERROR lines (verbatim, all):
```
FAILED tests/test_flow.py::test_failed_retry - AssertionError: assert ('pendi...
FAILED tests/test_flow.py::test_retry_twice_concurrent - AssertionError: asse...
FAILED tests/test_hygiene.py::test_hygiene_scan_public - AssertionError: gitl...
FAILED tests/test_hygiene.py::test_hygiene_wordlist - AssertionError: set HYG...
FAILED tests/test_infra.py::test_demo_adapters - AssertionError: assert 'unkn...
FAILED tests/test_mutants.py::test_mutant_no_claim - AssertionError: Regex pa...
```

## Stage 3: Four concurrency tests, repeated

NOT RUN in this invocation.

## Stage 4: Hostile matrix, single runner

NOT RUN in this invocation.

## Stage 5: Load (same lead, different leads) and kill -9 rounds

NOT RUN in this invocation.

## Other raw files

- `/tmp/linux-ev/wA/stages.jsonl` (one JSON line per step: command, cwd, exit, seconds)
