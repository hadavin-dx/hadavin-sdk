# Final gate report: dpld-fix7-00e30c5.tar.gz  (full mode)

This file records commands, exit codes and the tools' own output, word for word. It makes no pass/fail judgement of its own.

## Header

- tarball: `/home/user/hadavin-sdk/handover/demo/dpld-fix7-00e30c5.tar.gz`
- tarball_sha256: `658d1ef47868d59223eaae88a4034ebc9d317881303e445925f21917d0cff283`
- tree: `/tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5`
- workdir: `/tmp/final-gate-full-fix7`
- host: `Linux-6.18.44-fc-v310-x86_64-with-glibc2.39`
- cores: `4`
- python: `Python 3.12.3`
- venv: `/tmp/final-gate-full-fix7/venv (the unpacked copy was made a throw-away git repository so the git-based hygiene tests can run)`
- started_utc: `2026-11-09 12:08:01`
- mode: `full`
- server_py_hooks: `PATCHED hooks 1 and 2 in /tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5/src/lead_desk/server.py | hook 3: constants.LISTEN_QUEUE = 1024`

**Edit applied to the UNPACKED COPY only (never to the tarball):** the `server.py` hook edits from CONTRACT-DELTA.md ("server.py hooks": catch LockHeldError and OSError, `start_background()` before `startup()`, `stop_background()` first in `finally`). Result of the patch step: `PATCHED hooks 1 and 2 in /tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5/src/lead_desk/server.py | hook 3: constants.LISTEN_QUEUE = 1024`.

Stage order is fixed and one thing runs at a time; free ports are picked per step. Exit code 124 here means the step hit its time limit and was stopped by this script.

## Stage 0: Set-up (unpack, own venv, hook patch)

| step | exit | seconds | limit s | raw file |
|---|---|---|---|---|
| patch-server-hooks | 0 | 0.0 | 60 | `/tmp/final-gate-full-fix7/raw/0-patch-server-hooks.txt` |
| pip-install-hashed | 0 | 5.9 | 900 | `/tmp/final-gate-full-fix7/raw/0-pip-install-hashed.txt` |
| venv-create | 0 | 2.5 | 300 | `/tmp/final-gate-full-fix7/raw/0-venv-create.txt` |

### patch-server-hooks

Command: `cat /tmp/final-gate-full-fix7/raw-patch.txt`  (cwd `None`)  exit code: 0

(whole output, verbatim)
```
PATCHED hooks 1 and 2 in /tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5/src/lead_desk/server.py | hook 3: constants.LISTEN_QUEUE = 1024
```

### pip-install-hashed

Command: `/tmp/final-gate-full-fix7/venv/bin/python -m pip install --require-hashes -r requirements-dev.txt`  (cwd `/tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5`)  exit code: 0

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

Command: `/usr/bin/python3.12 -m venv /tmp/final-gate-full-fix7/venv`  (cwd `None`)  exit code: 0

(whole output, verbatim)
```

```

## Stage 1: Lint, types, security scan, schema check

| step | exit | seconds | limit s | raw file |
|---|---|---|---|---|
| bandit | 0 | 0.3 | 300 | `/tmp/final-gate-full-fix7/raw/1-bandit.txt` |
| check-schema | 0 | 0.1 | 300 | `/tmp/final-gate-full-fix7/raw/1-check-schema.txt` |
| mypy-linux | 0 | 1.1 | 900 | `/tmp/final-gate-full-fix7/raw/1-mypy-linux.txt` |
| ruff-check | 0 | 0.0 | 300 | `/tmp/final-gate-full-fix7/raw/1-ruff-check.txt` |
| ruff-format-check | 0 | 0.0 | 300 | `/tmp/final-gate-full-fix7/raw/1-ruff-format-check.txt` |

### bandit

Command: `/tmp/final-gate-full-fix7/venv/bin/bandit -q -ll -r src tools -c pyproject.toml`  (cwd `/tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5`)  exit code: 0

(whole output, verbatim)
```

```

### check-schema

Command: `/tmp/final-gate-full-fix7/venv/bin/python scripts/check_schema.py`  (cwd `/tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5`)  exit code: 0

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

Command: `/tmp/final-gate-full-fix7/venv/bin/mypy --platform linux`  (cwd `/tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5`)  exit code: 0

(whole output, verbatim)
```
Success: no issues found in 16 source files
```

### ruff-check

Command: `/tmp/final-gate-full-fix7/venv/bin/ruff check`  (cwd `/tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5`)  exit code: 0

(whole output, verbatim)
```
All checks passed!
```

### ruff-format-check

Command: `/tmp/final-gate-full-fix7/venv/bin/ruff format --check`  (cwd `/tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5`)  exit code: 0

(whole output, verbatim)
```
46 files already formatted
```

## Stage 2: Full pytest, repeated

| step | exit | seconds | limit s | raw file |
|---|---|---|---|---|
| pytest-run-1 | 1 | 160.0 | 1200 | `/tmp/final-gate-full-fix7/raw/2-pytest-run-1.txt` |
| pytest-run-2 | 1 | 160.5 | 1200 | `/tmp/final-gate-full-fix7/raw/2-pytest-run-2.txt` |
| pytest-run-3 | 1 | 160.2 | 1200 | `/tmp/final-gate-full-fix7/raw/2-pytest-run-3.txt` |

### pytest-run-1

Command: `/tmp/final-gate-full-fix7/venv/bin/python -m pytest -q -rf -p no:cacheprovider --no-header`  (cwd `/tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5`)  exit code: 1

Last line (verbatim):
```
7 failed, 296 passed, 1 skipped in 159.70s (0:02:39)
```
FAILED/ERROR lines (verbatim, all):
```
FAILED tests/test_flow.py::test_failed_retry - AssertionError: assert ('pendi...
FAILED tests/test_flow.py::test_retry_twice_concurrent - AssertionError: asse...
FAILED tests/test_hygiene.py::test_hygiene_scan_public - AssertionError: hard...
FAILED tests/test_hygiene.py::test_hygiene_wordlist - AssertionError: set HYG...
FAILED tests/test_infra.py::test_demo_adapters - AssertionError: assert 'unkn...
FAILED tests/test_mutants.py::test_mutant_no_claim - AssertionError: Regex pa...
FAILED tests/test_server_hardening.py::test_reply_write_fails_after_commit_followup_still_runs
```

### pytest-run-2

Command: `/tmp/final-gate-full-fix7/venv/bin/python -m pytest -q -rf -p no:cacheprovider --no-header`  (cwd `/tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5`)  exit code: 1

Last line (verbatim):
```
6 failed, 297 passed, 1 skipped in 160.22s (0:02:40)
```
FAILED/ERROR lines (verbatim, all):
```
FAILED tests/test_flow.py::test_failed_retry - AssertionError: assert ('pendi...
FAILED tests/test_flow.py::test_retry_twice_concurrent - AssertionError: asse...
FAILED tests/test_hygiene.py::test_hygiene_scan_public - AssertionError: hard...
FAILED tests/test_hygiene.py::test_hygiene_wordlist - AssertionError: set HYG...
FAILED tests/test_infra.py::test_demo_adapters - AssertionError: assert 'unkn...
FAILED tests/test_mutants.py::test_mutant_no_claim - AssertionError: Regex pa...
```

### pytest-run-3

Command: `/tmp/final-gate-full-fix7/venv/bin/python -m pytest -q -rf -p no:cacheprovider --no-header`  (cwd `/tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5`)  exit code: 1

Last line (verbatim):
```
7 failed, 296 passed, 1 skipped in 159.86s (0:02:39)
```
FAILED/ERROR lines (verbatim, all):
```
FAILED tests/test_flow.py::test_failed_retry - AssertionError: assert ('pendi...
FAILED tests/test_flow.py::test_retry_twice_concurrent - AssertionError: asse...
FAILED tests/test_hygiene.py::test_hygiene_scan_public - AssertionError: hard...
FAILED tests/test_hygiene.py::test_hygiene_wordlist - AssertionError: set HYG...
FAILED tests/test_infra.py::test_demo_adapters - AssertionError: assert 'unkn...
FAILED tests/test_mutants.py::test_mutant_no_claim - AssertionError: Regex pa...
FAILED tests/test_server_hardening.py::test_reply_write_fails_after_commit_followup_still_runs
```

## Stage 3: Four concurrency tests, repeated

| step | exit | seconds | limit s | raw file |
|---|---|---|---|---|
| conc-test_concurrent_same_source_ref | 0 | 68.6 | 120 | `/tmp/final-gate-full-fix7/raw/3-conc-test_concurrent_same_source_ref.txt` |
| conc-test_reconcile_counts | 0 | 68.2 | 120 | `/tmp/final-gate-full-fix7/raw/3-conc-test_reconcile_counts.txt` |
| conc-test_retry_twice_concurrent | 1 | 38.8 | 120 | `/tmp/final-gate-full-fix7/raw/3-conc-test_retry_twice_concurrent.txt` |
| conc-test_ten_parallel | 0 | 79.5 | 120 | `/tmp/final-gate-full-fix7/raw/3-conc-test_ten_parallel.txt` |

### conc-test_concurrent_same_source_ref

Command: `/tmp/final-gate-full-fix7/venv/bin/python -m pytest -q --tb=short -p no:cacheprovider --no-header -k test_concurrent_same_source_ref   (x50, one after another)`  (cwd `/tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5`)  exit code: 0

Run summary: exit0=50 nonzero=0 of 50; 1 passed, 303 deselected in 1.05s

```
COUNTS test_concurrent_same_source_ref: exit0=50 nonzero=0 (of which timeout=0) of 50; last run summary line: 1 passed, 303 deselected in 1.05s
```
Output of failing runs is in the raw file (0 failing run(s) recorded).

### conc-test_reconcile_counts

Command: `/tmp/final-gate-full-fix7/venv/bin/python -m pytest -q --tb=short -p no:cacheprovider --no-header -k test_reconcile_counts   (x50, one after another)`  (cwd `/tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5`)  exit code: 0

Run summary: exit0=50 nonzero=0 of 50; 1 passed, 303 deselected in 1.04s

```
COUNTS test_reconcile_counts: exit0=50 nonzero=0 (of which timeout=0) of 50; last run summary line: 1 passed, 303 deselected in 1.04s
```
Output of failing runs is in the raw file (0 failing run(s) recorded).

### conc-test_retry_twice_concurrent

Command: `/tmp/final-gate-full-fix7/venv/bin/python -m pytest -q --tb=short -p no:cacheprovider --no-header -k test_retry_twice_concurrent   (x50, one after another)`  (cwd `/tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5`)  exit code: 1

Run summary: exit0=0 nonzero=50 of 50; 1 failed, 303 deselected in 0.47s

```
COUNTS test_retry_twice_concurrent: exit0=0 nonzero=50 (of which timeout=0) of 50; last run summary line: 1 failed, 303 deselected in 0.47s
```
Output of failing runs is in the raw file (50 failing run(s) recorded).

### conc-test_ten_parallel

Command: `/tmp/final-gate-full-fix7/venv/bin/python -m pytest -q --tb=short -p no:cacheprovider --no-header -k test_ten_parallel   (x50, one after another)`  (cwd `/tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5`)  exit code: 0

Run summary: exit0=50 nonzero=0 of 50; 1 passed, 303 deselected in 1.25s

```
COUNTS test_ten_parallel: exit0=50 nonzero=0 (of which timeout=0) of 50; last run summary line: 1 passed, 303 deselected in 1.25s
```
Output of failing runs is in the raw file (0 failing run(s) recorded).

## Stage 4: Hostile matrix, single runner

| step | exit | seconds | limit s | raw file |
|---|---|---|---|---|
| hostile-class-A | 0 | 40.4 | 1800 | `/tmp/final-gate-full-fix7/raw/4-hostile-class-A.txt` |
| hostile-classes-B-to-H | 0 | 187.5 | 1800 | `/tmp/final-gate-full-fix7/raw/4-hostile-classes-B-to-H.txt` |

### hostile-class-A

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/runA.py`  (cwd `/tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5`)  exit code: 0

(whole output, verbatim)
```
A size/framing body exactly 65536 bytes (cap 65536), valid envelope but mes HTTP/1.0 202 Accepted []
A size/framing body 65537 bytes (cap+1) HTTP/1.0 413 Request Entity Too Large []
A size/framing body 10 MB of 'x'  ['conn err:BrokenPipeError']
A size/framing chunked, no Content-Length HTTP/1.0 400 Bad Request []
A size/framing Content-Length larger than body (+50), client keeps socket o HTTP/1.0 408 Request Timeout ['slow 30.0s']
A size/framing Content-Length smaller than body (-10) HTTP/1.0 400 Bad Request []
A size/framing Content-Length: -5 HTTP/1.0 400 Bad Request []
A size/framing Content-Length: abc HTTP/1.0 400 Bad Request []
A size/framing Content-Length: 99999999999999999999 HTTP/1.0 413 Request Entity Too Large []
A size/framing two Content-Length headers (len, len+5) HTTP/1.0 400 Bad Request []
A size/framing no Content-Length on POST /leads HTTP/1.0 400 Bad Request []
A size/framing Content-Length: 0 HTTP/1.0 400 Bad Request []
A size/framing Content-Length with unicode digit (arabic-indic 5) HTTP/1.0 400 Bad Request []
A size/framing header block 100 KB HTTP/1.0 431 Request Header Fields Too Large []
A size/framing 200 headers HTTP/1.0 431 Request Header Fields Too Large []
A size/framing request line 70 KB HTTP/1.0 414 Request-URI Too Long []
A size/framing liveness True True
class A done, stopping
```

### hostile-classes-B-to-H

Command: `/tmp/final-gate-full-fix7/venv/bin/python hostile_run.py`  (cwd `/tmp/final-gate-full-fix7/src/dpld-fix7-00e30c5`)  exit code: 0

(last 40 lines, verbatim; whole output in raw file)
```
F routes/methods/traversal header injection: bare LF in header / folded header HTTP/1.0 200 OK []
F routes/methods/traversal header with CR only, NUL in header value HTTP/1.0 200 OK []
F routes/methods/traversal Expect: 100-continue on POST /leads HTTP/1.0 201 Created []
F routes/methods/traversal Host header missing / duplicate / huge HTTP/1.0 200 OK []
F routes/methods/traversal Connection: keep-alive then 2nd request on same socket HTTP/1.0 200 OK []
F routes/methods/traversal liveness True True
G concurrency/replay replay: first g-rep HTTP/1.0 201 Created []
G concurrency/replay replay same id, changed payload (phone 222, name Eve) HTTP/1.0 201 Created []
G concurrency/replay replay same id, changed email HTTP/1.0 201 Created []
G concurrency/replay replay same id, other source (webhook) same ref HTTP/1.0 200 OK []
G concurrency/replay replay same id, key order changed HTTP/1.0 201 Created []
G concurrency/replay replay same id, whitespace-changed values HTTP/1.0 201 Created []
G concurrency/replay new id, same email, new phone HTTP/1.0 200 OK []
G concurrency/replay 1000 distinct request ids, same email, 100 parallel workers  ['no reply']
G concurrency/replay re-sent the 0 non-2xx ids of the 1000 (up to 5 tries)  ['no reply']
G concurrency/replay GET /counts?expected=1002 after 1000 + 2 earlier lead rows HTTP/1.0 200 OK []
G concurrency/replay 50 parallel posts of ONE request id, same payload  ['no reply']
G concurrency/replay 50 parallel posts of ONE request id, 50 different names  ['no reply']
G concurrency/replay setup: lead with mail reply lost -> unknown follow-up HTTP/1.0 201 Created []
G concurrency/replay resolve FL40821af1a62e 10x concurrently (5 sent, 5 not_sent)  ['no reply']
G concurrency/replay GET /leads for that lead HTTP/1.0 200 OK []
G concurrency/replay resolve FL40821af1a62e again after final HTTP/1.0 409 Conflict []
G concurrency/replay retry FL40821af1a62e after final HTTP/1.0 200 OK ['mails>leads']
G concurrency/replay resolve FL8041ec665638 body: empty body HTTP/1.0 400 Bad Request ['mails>leads']
G concurrency/replay resolve FL8041ec665638 body: not json HTTP/1.0 400 Bad Request ['mails>leads']
G concurrency/replay resolve FL8041ec665638 body: decision list HTTP/1.0 400 Bad Request ['mails>leads']
G concurrency/replay resolve FL8041ec665638 body: decision SENT upper HTTP/1.0 400 Bad Request ['mails>leads']
G concurrency/replay resolve FL8041ec665638 body: decision ' sent' HTTP/1.0 400 Bad Request ['mails>leads']
G concurrency/replay resolve FL8041ec665638 body: decision with NUL HTTP/1.0 400 Bad Request ['mails>leads']
G concurrency/replay resolve FL8041ec665638 body: nested depth 10000 HTTP/1.0 400 Bad Request ['mails>leads']
G concurrency/replay resolve FL8041ec665638 body: duplicate keys HTTP/1.0 200 OK ['mails>leads']
G concurrency/replay resolve FL8041ec665638 body: decision null HTTP/1.0 400 Bad Request ['mails>leads']
G concurrency/replay resolve FL8041ec665638 body: invalid utf8 HTTP/1.0 400 Bad Request ['mails>leads']
G concurrency/replay resolve FL8041ec665638 body: array body HTTP/1.0 400 Bad Request ['mails>leads']
G concurrency/replay resolve FL8041ec665638 body: 10 MB body  ['conn err:BrokenPipeError', 'mails>leads']
G concurrency/replay resolve on R/D/O/F-missing ids HTTP/1.0 404 Not Found ['mails>leads']
G concurrency/replay retry F of sent lead / unknown HTTP/1.0 200 OK ['mails>leads']
G concurrency/replay liveness True True
H kill and restart kill -9 desk mid-burst (300 posts, 7 emails), restart same D  ['no reply']
H kill and restart liveness True True
```

## Stage 5: Load (same lead, different leads) and kill -9 rounds

| step | exit | seconds | limit s | raw file |
|---|---|---|---|---|
| kill9-blind-round1 | 0 | 6.9 | 900 | `/tmp/final-gate-full-fix7/raw/5-kill9-blind-round1.txt` |
| kill9-blind-round2 | 0 | 6.8 | 900 | `/tmp/final-gate-full-fix7/raw/5-kill9-blind-round2.txt` |
| kill9-blind-round3 | 0 | 6.9 | 900 | `/tmp/final-gate-full-fix7/raw/5-kill9-blind-round3.txt` |
| kill9-blind-round4 | 0 | 6.8 | 900 | `/tmp/final-gate-full-fix7/raw/5-kill9-blind-round4.txt` |
| kill9-blind-round5 | 0 | 6.9 | 900 | `/tmp/final-gate-full-fix7/raw/5-kill9-blind-round5.txt` |
| kill9-keyed-round1 | 0 | 6.8 | 900 | `/tmp/final-gate-full-fix7/raw/5-kill9-keyed-round1.txt` |
| kill9-keyed-round2 | 0 | 6.9 | 900 | `/tmp/final-gate-full-fix7/raw/5-kill9-keyed-round2.txt` |
| kill9-keyed-round3 | 0 | 6.9 | 900 | `/tmp/final-gate-full-fix7/raw/5-kill9-keyed-round3.txt` |
| kill9-keyed-round4 | 0 | 7.0 | 900 | `/tmp/final-gate-full-fix7/raw/5-kill9-keyed-round4.txt` |
| kill9-keyed-round5 | 0 | 6.9 | 900 | `/tmp/final-gate-full-fix7/raw/5-kill9-keyed-round5.txt` |
| load-blind-diff-100 | 0 | 3.7 | 900 | `/tmp/final-gate-full-fix7/raw/5-load-blind-diff-100.txt` |
| load-blind-diff-1000 | 0 | 6.8 | 900 | `/tmp/final-gate-full-fix7/raw/5-load-blind-diff-1000.txt` |
| load-blind-same-10 | 0 | 3.4 | 900 | `/tmp/final-gate-full-fix7/raw/5-load-blind-same-10.txt` |
| load-blind-same-100 | 0 | 3.7 | 900 | `/tmp/final-gate-full-fix7/raw/5-load-blind-same-100.txt` |
| load-blind-same-1000 | 0 | 6.6 | 900 | `/tmp/final-gate-full-fix7/raw/5-load-blind-same-1000.txt` |
| load-blind-same-500 | 0 | 4.9 | 900 | `/tmp/final-gate-full-fix7/raw/5-load-blind-same-500.txt` |
| load-keyed-diff-100 | 0 | 3.7 | 900 | `/tmp/final-gate-full-fix7/raw/5-load-keyed-diff-100.txt` |
| load-keyed-diff-1000 | 0 | 6.7 | 900 | `/tmp/final-gate-full-fix7/raw/5-load-keyed-diff-1000.txt` |
| load-keyed-same-10 | 0 | 3.4 | 900 | `/tmp/final-gate-full-fix7/raw/5-load-keyed-same-10.txt` |
| load-keyed-same-100 | 0 | 3.7 | 900 | `/tmp/final-gate-full-fix7/raw/5-load-keyed-same-100.txt` |
| load-keyed-same-1000 | 0 | 6.4 | 900 | `/tmp/final-gate-full-fix7/raw/5-load-keyed-same-1000.txt` |
| load-keyed-same-500 | 0 | 5.0 | 900 | `/tmp/final-gate-full-fix7/raw/5-load-keyed-same-500.txt` |

### kill9-blind-round1

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py kill blind 1`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[blind] kill-9 round 1 n=200: n=200 status={201: 200} 5xx=0 client_errors={} max_latency_s=1.59
   desk_counts={'received': 200, 'new': 200, 'duplicate': 0, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 200} open_receipts= 0
   received=200 vs new+dup+review+rejected=200 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=200 distinct_leads_in_crm=200 max_rows_per_lead=1; emails=200 distinct_recipients=200 max_emails_per_lead=1; expected_leads=200
   acked_2xx=200 of 200; acked_but_no_receipt_id=0; retries_total=399
```

### kill9-blind-round2

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py kill blind 2`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[blind] kill-9 round 2 n=200: n=200 status={201: 200} 5xx=0 client_errors={} max_latency_s=1.42
   desk_counts={'received': 200, 'new': 200, 'duplicate': 0, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 200} open_receipts= 0
   received=200 vs new+dup+review+rejected=200 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=200 distinct_leads_in_crm=200 max_rows_per_lead=1; emails=200 distinct_recipients=200 max_emails_per_lead=1; expected_leads=200
   acked_2xx=200 of 200; acked_but_no_receipt_id=0; retries_total=261
```

### kill9-blind-round3

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py kill blind 3`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[blind] kill-9 round 3 n=200: n=200 status={201: 199, 'IncompleteRead': 1} 5xx=0 client_errors={'IncompleteRead': 1} max_latency_s=1.51
   desk_counts={'received': 200, 'new': 200, 'duplicate': 0, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 200} open_receipts= 0
   received=200 vs new+dup+review+rejected=200 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=200 distinct_leads_in_crm=200 max_rows_per_lead=1; emails=200 distinct_recipients=200 max_emails_per_lead=1; expected_leads=200
   acked_2xx=199 of 200; acked_but_no_receipt_id=0; retries_total=297
```

### kill9-blind-round4

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py kill blind 4`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[blind] kill-9 round 4 n=200: n=200 status={201: 200} 5xx=0 client_errors={} max_latency_s=1.47
   desk_counts={'received': 200, 'new': 200, 'duplicate': 0, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 200} open_receipts= 0
   received=200 vs new+dup+review+rejected=200 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=200 distinct_leads_in_crm=200 max_rows_per_lead=1; emails=200 distinct_recipients=200 max_emails_per_lead=1; expected_leads=200
   acked_2xx=200 of 200; acked_but_no_receipt_id=0; retries_total=366
```

### kill9-blind-round5

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py kill blind 5`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[blind] kill-9 round 5 n=200: n=200 status={201: 200} 5xx=0 client_errors={} max_latency_s=1.51
   desk_counts={'received': 200, 'new': 200, 'duplicate': 0, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 200} open_receipts= 0
   received=200 vs new+dup+review+rejected=200 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=200 distinct_leads_in_crm=200 max_rows_per_lead=1; emails=200 distinct_recipients=200 max_emails_per_lead=1; expected_leads=200
   acked_2xx=200 of 200; acked_but_no_receipt_id=0; retries_total=396
```

### kill9-keyed-round1

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py kill keyed 1`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[keyed] kill-9 round 1 n=200: n=200 status={201: 200} 5xx=0 client_errors={} max_latency_s=1.40
   desk_counts={'received': 200, 'new': 200, 'duplicate': 0, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 200} open_receipts= 0
   received=200 vs new+dup+review+rejected=200 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=200 distinct_leads_in_crm=200 max_rows_per_lead=1; emails=200 distinct_recipients=200 max_emails_per_lead=1; expected_leads=200
   acked_2xx=200 of 200; acked_but_no_receipt_id=0; retries_total=267
```

### kill9-keyed-round2

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py kill keyed 2`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[keyed] kill-9 round 2 n=200: n=200 status={201: 200} 5xx=0 client_errors={} max_latency_s=1.54
   desk_counts={'received': 200, 'new': 200, 'duplicate': 0, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 200} open_receipts= 0
   received=200 vs new+dup+review+rejected=200 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=200 distinct_leads_in_crm=200 max_rows_per_lead=1; emails=200 distinct_recipients=200 max_emails_per_lead=1; expected_leads=200
   acked_2xx=200 of 200; acked_but_no_receipt_id=0; retries_total=324
```

### kill9-keyed-round3

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py kill keyed 3`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[keyed] kill-9 round 3 n=200: n=200 status={201: 200} 5xx=0 client_errors={} max_latency_s=1.49
   desk_counts={'received': 200, 'new': 200, 'duplicate': 0, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 200} open_receipts= 0
   received=200 vs new+dup+review+rejected=200 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=200 distinct_leads_in_crm=200 max_rows_per_lead=1; emails=200 distinct_recipients=200 max_emails_per_lead=1; expected_leads=200
   acked_2xx=200 of 200; acked_but_no_receipt_id=0; retries_total=339
```

### kill9-keyed-round4

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py kill keyed 4`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[keyed] kill-9 round 4 n=200: n=200 status={201: 200} 5xx=0 client_errors={} max_latency_s=1.57
   desk_counts={'received': 200, 'new': 200, 'duplicate': 0, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 200} open_receipts= 0
   received=200 vs new+dup+review+rejected=200 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=200 distinct_leads_in_crm=200 max_rows_per_lead=1; emails=200 distinct_recipients=200 max_emails_per_lead=1; expected_leads=200
   acked_2xx=200 of 200; acked_but_no_receipt_id=0; retries_total=384
```

### kill9-keyed-round5

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py kill keyed 5`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[keyed] kill-9 round 5 n=200: n=200 status={201: 200} 5xx=0 client_errors={} max_latency_s=1.51
   desk_counts={'received': 200, 'new': 200, 'duplicate': 0, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 200} open_receipts= 0
   received=200 vs new+dup+review+rejected=200 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=200 distinct_leads_in_crm=200 max_rows_per_lead=1; emails=200 distinct_recipients=200 max_emails_per_lead=1; expected_leads=200
   acked_2xx=200 of 200; acked_but_no_receipt_id=0; retries_total=399
```

### load-blind-diff-100

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py scen blind diff 100`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[blind] diff n=100: n=100 status={201: 100} 5xx=0 client_errors={} max_latency_s=0.32
   desk_counts={'received': 100, 'new': 100, 'duplicate': 0, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 100} open_receipts= 0
   received=100 vs new+dup+review+rejected=100 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=100 distinct_leads_in_crm=100 max_rows_per_lead=1; emails=100 distinct_recipients=100 max_emails_per_lead=1; expected_leads=100
```

### load-blind-diff-1000

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py scen blind diff 1000`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[blind] diff n=1000: n=1000 status={201: 1000} 5xx=0 client_errors={} max_latency_s=3.26
   desk_counts={'received': 1000, 'new': 1000, 'duplicate': 0, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 433, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 1, 'expected_match': None, 'ok': None}
   followup_states= {'pending': 427, 'sending': 5, 'sent': 568} open_receipts= 0
   received=1000 vs new+dup+review+rejected=1000 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=568 distinct_leads_in_crm=568 max_rows_per_lead=1; emails=568 distinct_recipients=568 max_emails_per_lead=1; expected_leads=1000
```

### load-blind-same-10

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py scen blind same 10`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[blind] same n=10: n=10 status={201: 1, 200: 9} 5xx=0 client_errors={} max_latency_s=0.03
   desk_counts={'received': 10, 'new': 1, 'duplicate': 9, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 1} open_receipts= 0
   received=10 vs new+dup+review+rejected=10 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=1 distinct_leads_in_crm=1 max_rows_per_lead=1; emails=1 distinct_recipients=1 max_emails_per_lead=1; expected_leads=1
```

### load-blind-same-100

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py scen blind same 100`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[blind] same n=100: n=100 status={201: 1, 200: 99} 5xx=0 client_errors={} max_latency_s=0.32
   desk_counts={'received': 100, 'new': 1, 'duplicate': 99, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 1} open_receipts= 0
   received=100 vs new+dup+review+rejected=100 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=1 distinct_leads_in_crm=1 max_rows_per_lead=1; emails=1 distinct_recipients=1 max_emails_per_lead=1; expected_leads=1
```

### load-blind-same-1000

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py scen blind same 1000`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[blind] same n=1000: n=1000 status={201: 1, 200: 999} 5xx=0 client_errors={} max_latency_s=2.74
   desk_counts={'received': 1000, 'new': 1, 'duplicate': 999, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 1} open_receipts= 0
   received=1000 vs new+dup+review+rejected=1000 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=1 distinct_leads_in_crm=1 max_rows_per_lead=1; emails=1 distinct_recipients=1 max_emails_per_lead=1; expected_leads=1
```

### load-blind-same-500

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py scen blind same 500`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[blind] same n=500: n=500 status={200: 499, 201: 1} 5xx=0 client_errors={} max_latency_s=1.49
   desk_counts={'received': 500, 'new': 1, 'duplicate': 499, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 1} open_receipts= 0
   received=500 vs new+dup+review+rejected=500 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=1 distinct_leads_in_crm=1 max_rows_per_lead=1; emails=1 distinct_recipients=1 max_emails_per_lead=1; expected_leads=1
```

### load-keyed-diff-100

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py scen keyed diff 100`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[keyed] diff n=100: n=100 status={201: 100} 5xx=0 client_errors={} max_latency_s=0.34
   desk_counts={'received': 100, 'new': 100, 'duplicate': 0, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 100} open_receipts= 0
   received=100 vs new+dup+review+rejected=100 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=100 distinct_leads_in_crm=100 max_rows_per_lead=1; emails=100 distinct_recipients=100 max_emails_per_lead=1; expected_leads=100
```

### load-keyed-diff-1000

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py scen keyed diff 1000`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[keyed] diff n=1000: n=1000 status={201: 1000} 5xx=0 client_errors={} max_latency_s=2.84
   desk_counts={'received': 1000, 'new': 1000, 'duplicate': 0, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 440, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 8, 'expected_match': None, 'ok': None}
   followup_states= {'pending': 432, 'sending': 6, 'sent': 562} open_receipts= 0
   received=1000 vs new+dup+review+rejected=1000 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=566 distinct_leads_in_crm=566 max_rows_per_lead=1; emails=563 distinct_recipients=563 max_emails_per_lead=1; expected_leads=1000
```

### load-keyed-same-10

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py scen keyed same 10`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[keyed] same n=10: n=10 status={201: 1, 200: 9} 5xx=0 client_errors={} max_latency_s=0.03
   desk_counts={'received': 10, 'new': 1, 'duplicate': 9, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 1} open_receipts= 0
   received=10 vs new+dup+review+rejected=10 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=1 distinct_leads_in_crm=1 max_rows_per_lead=1; emails=1 distinct_recipients=1 max_emails_per_lead=1; expected_leads=1
```

### load-keyed-same-100

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py scen keyed same 100`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[keyed] same n=100: n=100 status={201: 1, 200: 99} 5xx=0 client_errors={} max_latency_s=0.32
   desk_counts={'received': 100, 'new': 1, 'duplicate': 99, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 1} open_receipts= 0
   received=100 vs new+dup+review+rejected=100 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=1 distinct_leads_in_crm=1 max_rows_per_lead=1; emails=1 distinct_recipients=1 max_emails_per_lead=1; expected_leads=1
```

### load-keyed-same-1000

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py scen keyed same 1000`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[keyed] same n=1000: n=1000 status={201: 1, 200: 999} 5xx=0 client_errors={} max_latency_s=2.49
   desk_counts={'received': 1000, 'new': 1, 'duplicate': 999, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 1} open_receipts= 0
   received=1000 vs new+dup+review+rejected=1000 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=1 distinct_leads_in_crm=1 max_rows_per_lead=1; emails=1 distinct_recipients=1 max_emails_per_lead=1; expected_leads=1
```

### load-keyed-same-500

Command: `/tmp/final-gate-full-fix7/venv/bin/python /home/user/hadavin-sdk/handover/demo/tools/final_gate/load.py scen keyed same 500`  (cwd `/home/user/hadavin-sdk/handover/demo/tools/final_gate`)  exit code: 0

```
[keyed] same n=500: n=500 status={201: 1, 200: 499} 5xx=0 client_errors={} max_latency_s=1.59
   desk_counts={'received': 500, 'new': 1, 'duplicate': 499, 'review': 0, 'open': 0, 'rejected_envelopes': 0, 'pending_followups': 0, 'failed_followups': 0, 'unknown_followups': 0, 'sending_followups': 0, 'expected_match': None, 'ok': None}
   followup_states= {'sent': 1} open_receipts= 0
   received=500 vs new+dup+review+rejected=500 (failed/unknown shown in open/pending) lost_receipt=0
   crm_rows=1 distinct_leads_in_crm=1 max_rows_per_lead=1; emails=1 distinct_recipients=1 max_emails_per_lead=1; expected_leads=1
```

## Other raw files

- `/tmp/final-gate-full-fix7/rows-A.jsonl` (17 lines)
- `/tmp/final-gate-full-fix7/rows-BH.jsonl` (220 lines)
- `/tmp/final-gate-full-fix7/stages.jsonl` (one JSON line per step: command, cwd, exit, seconds)
