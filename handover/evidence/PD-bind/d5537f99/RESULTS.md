# Evidence (PARTIAL): Part 2 bind guard batch 5, head d5537f99852b39c12721cfe053bd284c73bc1a81 (EVIDENCE RUNNER abaa885e, no judgement)

Saved by the lead from the runner's hand-back. THIS RUN IS INCOMPLETE. Raw logs: /home/user/build/evidence-raw/pdbind-r5/.

## Not done (no result)
- Full suite `-m "not live and not perf"`: started 22:58Z, about 84% when the runner handed back; result in `full-suite.rc` and `full-suite.log` there (the lead reads it when it ends).
- `tests/bind_mutants.py` (expect 130) and `tests/stage_mutants.py` (37): not run.
- Fail-before against ddf930f8: not run (worktree prepared). The builder reports 29 failed, and says `test_a_forged_class_with_the_same_module_and_name_is_not_a_stand_in` passes on old code.
- Gitleaks, ruff etc. below ran at the head; Semgrep, pip-audit, Trivy not run.

## Done (exit code, last line)
| Item | Exit | Last line |
|---|---|---|
| clean detached worktree at the head | - | `git rev-parse HEAD` equals the sha, status clean before and after |
| own Postgres 16, UTF8, PGHOST/PGPORT in the server environment | - | read back from /proc environ |
| ruff check | 0 | All checks passed |
| ruff format --check src tests demos tools | 0 | 326 files already formatted |
| bandit -q -r src demos tools -ll (CI form) | 0 | no findings |
| tools/scan_repo.py | 0 | no output |
| gitleaks origin/main..HEAD (10 commits) | 0 | no leaks found |
| check-no-handover-files.sh wip/cloud-pd-bind d5537f99 | 0 | no output |
(An early `bandit -ll -r src tests tools demos` exit 1 was not the CI form; log deleted.)

## Hostile probes (python -I, recorded without judgement; DIFF = differs from stated behaviour)
Stand-ins and guard: forged class with the same `__module__`/`__qualname__` as FakeLLM: not a stand-in (real FakeLLM True; `stand_in` no longer exists). Subclass of MemoryStore or FakeChannel: counted as held and refused on a public bind. Base swap after the pin: TypeError (cannot be done). Method patched after the pin: False; patched BEFORE the first question (MemoryStore): True (stated "not promised"). Detector tuple or AnyOf with a function, nested depth 7, cyclic, list, tuple subclass: False; plain AnyOf and depth 2: True.
Instance contents (MemoryStore): function in a nested list at depth 3, tuple, deque, frozenset: False. Function at depth 5 or 8: **True (passes)**; a dict at depth 4 holding a function: True. A list of 100001 ints, and a list of exactly 100000 ints plus the other values: False; cyclic list or dict: True. **A list subclass or dict subclass with a hostile `__iter__` or `values`: True (passes); a hostile object value, mappingproxy, iterator, SimpleNamespace holding a function, a plain object holding a function: True (passes).** Bare partial or function: False.
Hostile held mappings: non-string keys give (); mapping subclass with raising `items()` gives ('held (unreadable)',); object with raising `__getattribute__` or `__class__` counted real; control-character key shows "(unreadable)"; long key cut with "...".
Module not imported, removed, rebound, or replaced by a ModuleType subclass: False (restored: True). Module-level `__getattr__` planted: True, not run.
Approvals and receiver: public bind with stand-ins serves; after `object.__setattr__(a, "_channel", Real())` a POST goes 401 to 503 with one log line. `a._config=None`, `a._channel=x`, `a.config=None`, a new attribute, `a.__class__=Sub`, `a.__setattr__('_channel', None)`: AttributeError; `a.clock = f` allowed. weakref, `vars(a)`, copy, deepcopy, pickle 0-5: TypeError. Class swap via `object.__setattr__(a,"__class__",Sub)` then POST: 503 and log.
- DIFF 1: `object.__setattr__(a,"_config",None)` then a POST on a public bind with stand-ins: 401 (still served).
- DIFF 2: `del a._config` works (no `__delattr__` guard).
- DIFF 3: after `object.__setattr__(a,"_channel",Real())` then `del a._channel`, a POST gets no 503: `real_now` raises AttributeError, the stdlib server prints a traceback, the client sees RemoteDisconnected (not served, but not the documented 503).
- DIFF 4: replacing `Approvals.__setattr__` at class level by plain assignment lets `a._channel = Real()` through (outside the guard per the docstring).
Refusal log: two refused requests back to back give 1 line; a different set of services inside 60 s gives a second; the same services after 61 s a third; BIND_REFUSAL_LOG_KEYS 64.
Server scan: seen: `from socketserver import *`, alias inside a function, class-scope import, lambda, `importlib.import_module('socketserver')`, `__import__('http.server')`, subclass of aliased server, wsgiref, uvicorn.run, asyncio.start_server, launchers (gunicorn entrypoint, `python -m`, nc -l, socat, runserver, `python -m http.server`, Dockerfile uvicorn, compose flask run), pyproject scripts and tasks. Not seen: `_socket.socket().bind`, `socket.socket().bind`, `from _socket import socket as S`, `getattr(socketserver,'TCPServer')`, `s = importlib.import_module(...)` used later, an alias used in a different function (stated). Hex words not hosts. Invalid TOML or Python raises from the scan itself. Import-time bind check: 108 modules, 0 errors, no bind or listen.

## Processes left running by the runner (the lead stops them)
Full-suite chain (nohup sh, nice, heavy.sh, uv, pytest); Postgres 16 on port 54895 (data /home/user/build/pg-r5, stop with `runuser -u postgres -- pg_ctl -D /home/user/build/pg-r5/data stop` after the suite ends); Monitor output watchers; worktrees ER-pdbind-r5 and ER-pdbind-r5-old; venv ER-pdbind-r5-venv.
