# EVIDENCE RUNNER results: PD-bind round 4, head ddf930f89fb37d56201c893ba50ef3923229e797

Runner only records; it does not judge. Raw logs: `/home/user/build/evidence-raw/pdbind-r4/` (outside the repo). Probe scripts: `/home/user/build/pdbind-r4-probes/`. Worktree `/home/user/build/ER-pdbind-r4` (detached, `git rev-parse HEAD` = the head above, `git status` clean before and after every run).

## Not run / deviations (first)

1. **Full suite was run twice; the first run had a setup slip of mine.** I started the Postgres test cluster without PGHOST/PGPORT in the server's own environment, so one test (`tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]`) failed: the server tried the default socket `/var/run/postgresql`. Result of run 1: 1 failed, 10750 passed, 2 skipped (kept as `full-suite-run1-pgenv-missing.log`). I restarted the cluster with PGHOST=127.0.0.1 and PGPORT=54891 in the server environment (confirmed in `/proc/<pid>/environ`) and ran the full suite again (run 2: below). Not part of the change.
2. **gitleaks** is not on PATH; used `/tmp/claude-0/gl/gitleaks` (v8.30.1). Range `origin/main..HEAD`; the local `origin/main` ref moved to a8b4d8e8 during my session (fetched); merge-base with HEAD is 2a8c2aac; 9 commits scanned.
3. **Fail-before, test_bindguard.py:** against the 06e762bc `src` this file cannot be collected at all (ImportError on `held_services_found`), so there are no per-test failed ids for it, one collection error for the whole file. The other three changed test files (test_loopback_sites, test_netguard, test_p7_tick) are byte-identical to 06e762bc's own copies and pass against the old src (they were not changed in this round's delta, so they cannot fail before).
4. **Mutant runners** run each mutant in a temp copy of the package, one at a time; `git status` was empty after each runner. I did not run them while the suite ran.
5. **bandit** was run as `bandit -ll -r src` (not over tests/tools/demos).
6. **Skipped tests (not mine to fix):** `tests/test_bindguard.py:476` (this machine has no IPv6 loopback); `tests/contracts/test_llm.py:95` (Stubber). So the IPv6 loopback bind test did not execute here.
7. No live model call, no secret, no commit, nothing added to git. The timing test had no failure in run 2 (and none in run 1).

## Results

| # | Item | Command | Exit | Last line |
|---|---|---|---|---|
| 1a | Full suite, run 1 (cluster env slip) | `heavy.sh uv run --no-sync pytest -p no:cacheprovider -q -m "not live and not perf" -rs` | 1 | `1 failed, 10750 passed, 2 skipped, 28 deselected in 287.82s` |
| 1b | Full suite, run 2 (cluster env fixed) | same | 0 | `10751 passed, 2 skipped, 28 deselected in 294.36s (0:04:54)` |
| 2 | Bind mutants | `python tests/bind_mutants.py` | 0 | `83 of 83 good; problems: []` |
| 3 | Stage mutants | `python tests/stage_mutants.py` | 0 | `37 of 37 good; problems: []` (git status empty after both) |
| 4 | Fail-before: head's 4 changed test files + `tools/server_scan.py` + mutants file on 06e762bc src (PYTHONPATH to old src, import path checked) | `pytest -q -rfE --continue-on-collection-errors tests/test_bindguard.py tests/test_loopback_sites.py tests/test_netguard.py tests/test_p7_tick.py` | 1 | `118 passed, 1 error`; failed id: `ERROR tests/test_bindguard.py` (`ImportError: cannot import name 'held_services_found' from 'hadavin_sdk.bindguard'`) |
| 5a | ruff check | `ruff check` | 0 | `All checks passed!` |
| 5b | ruff format | `ruff format --check src tests demos tools` | 0 | `326 files already formatted` |
| 5c | bandit | `bandit -ll -r src` | 0 | severity Medium 0, High 0 (7 Low, below the -ll line) |
| 5d | repo scan | `python tools/scan_repo.py` | 0 | no output |
| 5e | gitleaks | `gitleaks detect --source . --log-opts "origin/main..HEAD" --redact` | 0 | `no leaks found` (9 commits) |
| 6 | Hostile probes | see below | | |

## Hostile probes (raw: probes-approvals.log, probes-scan.log, probes-importbind.log)

Setup: fixture config (check_modules emptied), `Approvals` built from the core's stand-ins, `config=cfg`, `overrides={}`. The all-zero address is built from parts.

| Probe | Outcome (exception type and message, or result) |
|---|---|
| P1a public bind, no reason, stand-ins; then a real (unlisted) channel put in with `object.__setattr__(a, "_channel", ...)`; POST to /slack/actions | no exception at start; status before = 401, after = 503; log line `request refused: a real service is held on a public bind with no reason (held channel: Real)` |
| P1b public bind, no reason, real channel from the start | BindRefused: `bind '0.0.0.0' can be reached from other computers while a real service is configured (held channel: Real) ...` |
| P1c public bind, blank reason | BindRefused: `allow_public_bind_reason must say why, in at least 10 characters` |
| P2a/b/c/d `copy.copy`, `copy.deepcopy`, `pickle.dumps` (protocols 0 to 5) of an Approvals | TypeError each: `an Approvals cannot be copied or pickled: it holds sealed objects and frozen facts` (deepcopy: `cannot be copied`) |
| P3a register a class not on the list (`@standins.stand_in`) | TypeError: `... is not a stand-in the core lists (standins._ALLOWED); it cannot be registered` |
| P3b register a class defined in a script whose `__module__` and `__qualname__` were set to `hadavin_sdk.llm.fake` / `FakeLLM` | **no exception; it registered.** (The check reads the name text only; the module docstring says "only from a module of this package".) |
| P3c, after P3b: an instance of that forged class | `is_stand_in_object` = True |
| P3c' (fresh interpreter, forged class NOT registered) | `is_stand_in_object` = False |
| P4 subclass of `MemoryStore` | `is_stand_in_object` = False; serve on a public bind with it: BindRefused `(held store: SubStore)` |
| P5a/b callable in an instance `__dict__` (MemoryStore) | not a stand-in (False); serve public: BindRefused `(held store: MemoryStore)` |
| P5c FakeChannel with a function in its instance dict | serve public: BindRefused `(held channel: FakeChannel)` |
| P6a `a.config = None` | AttributeError `property 'config' of 'Approvals' object has no setter` |
| P6b `a._config = None` (ordinary setattr on the private slot) | **no exception; the slot was set to None** (the docstring places writes to private slots outside the guard) |
| P6c `a.store = ...` | AttributeError `property 'store' ... has no setter` |
| P6d `vars(a)` | TypeError `vars() argument must have __dict__ attribute` |
| P6e new attribute | AttributeError `'Approvals' object has no attribute 'nonslot' and no __dict__ ...` |
| S1 `import socketserver as s; s.TCPServer(...)` | forms: `['socketserver.TCPServer@2']` |
| S2 `from http.server import ThreadingHTTPServer as T` | `['http.server.ThreadingHTTPServer@2']` |
| S3 subclass of aliased `socketserver.ThreadingTCPServer` | `['class X(socketserver.ThreadingTCPServer)@2', 'socketserver.ThreadingTCPServer@2']` |
| S4 `importlib.import_module('socketserver')` alone | `[]` (no hit) |
| S5 `import wsgiref.simple_server as w; w.make_server` | `['wsgiref.simple_server.make_server@2']` |
| S7 `__import__('socketserver').TCPServer(...)` | `[]` (**no hit**) |
| S6 / L4 controls (plain code, `echo hello`) | `[]` |
| L1 launcher `python -m http.server 8000` | `['http.server@2']` |
| L2 Dockerfile `CMD ["uvicorn",...,"--host","0.0.0.0"]` | `['uvicorn@2', '--host@2', '0.0.0.0@2']` |
| L3 compose `flask run --host=0.0.0.0` | `['flask run@3', '--host@3', '0.0.0.0@3']` |
| Import-time bind, clean interpreter (`python -I`, `socket.socket.bind/listen` wrapped, every `hadavin_sdk` module imported) | 108 modules imported, 0 import errors, bind/listen calls: `[]` |

## Cleanup

Postgres test cluster stopped (`pg_ctl stop`, confirmed); no other process started by me remains (`pgrep` empty); the extra worktree `/home/user/build/ER-pdbind-r4-old` removed; `/home/user/build/ER-pdbind-r4` kept for reviewers (HEAD ddf930f8, status clean). Not added to git, not committed.
