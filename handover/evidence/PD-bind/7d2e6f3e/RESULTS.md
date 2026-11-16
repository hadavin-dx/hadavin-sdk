# EVIDENCE RUNNER results: PD-bind batch 7, head 7d2e6f3e379cbff6360077d857afb1fa763ad135

Runner only records, no judgement. Worktree `/home/user/build/ER-pdbind7` (detached; `git rev-parse HEAD` equals the sha above; `git status` clean at the end). Python 3.13.18. Raw logs: `/home/user/build/evidence-raw/pdbind7-runner/` (probes in `probes/`, probe scripts in `/home/user/build/pdbind7-er-probes/`). Nothing committed or pushed. No spend, no live calls, no secrets.

## Failures and gaps (first)
1. **`bind_mutants` is NOT all good: 170 of 174 good, 4 bad (exit 1).** Rows with the raw line:
   - B39 `the receiver builds its own server instead of calling listen`: `BAD ERROR ... [SNIPPET NOT FOUND]`
   - B43 `the receiver does not pass what the approvals hold`: `BAD ERROR ... [SNIPPET NOT FOUND]`
   - B60 `the start check forgets the frozen config facts`: `BAD ERROR ... [SNIPPET NOT FOUND]`
   - B153 `a hostile text key is shown again in its own handler`: `BAD WRONG_REASON`, killer `test_a_hostile_text_key_gets_a_fixed_label_and_nothing_is_called_on_it_again`; the first failing line was `ValueError: a key that is not a short plain word` (the row expects text `no text for this key` and crash type `RuntimeError`). Re-run alone (`bind-B153.log`): same, 0 of 1 good.
   - Why (seen, not judged): in `src/hadavin_sdk/approvals/receiver.py` the text `held=Approvals.held_services(approvals),` / `frozen=approvals.config_facts,` inside the `listen(...)` call no longer exists at this head (it is now `held=held,` / `frozen=frozen,`, line 187-188), so the three snippets of B39, B43, B60 find nothing to mutate. I did not check whether the guards those three rows covered are covered by another row. The builder's notes had only B1-B126 good at their handback; these four rows are in the later part. All other 170 rows: 163 `KILLED`, 7 `CRASH`, all marked `ok`. B158 ran (Python 3.13) and is `ok`.
2. **`serve()` with the `_config` slot deleted raises `AttributeError`, not `BindRefused`** (probe b, section e; the brief expects BindRefused for an unreadable object). The other unreadable cases give `BindRefused`. See probe results below.
3. **`serve()` still serves when the slot `_audit_sink`, `_registry` or `_clock` is deleted** (no refusal at start); each request is then answered 503 on the running server (probe c). Observed; `_clock` is documented as not read.
4. **`on_decided` made by `make_on_decided` whose holder dict holds a lambda is still read as the core's** (answered 401, served), also after the cell of a core closure is changed to a dict holding a lambda. A cell changed to a list reads as real (503). Observed; the guard checks the type of the cell (plain dict), not what the dict holds.
5. **Full suite here: 0 failures** (10829 passed, 2 skipped). The builder's one failure (`tests/demo_askdata/test_validate_harm.py[dblink-connect]`) is NOT reproduced on my server; I reproduced it only on a server without `PGHOST`/`PGPORT` and without the default socket (item 6 below), at both heads.
6. Deviations: (a) priority: `heavy.sh` reads the priority from its own arguments and the folder name; I ran `env tag=q8a1 heavy.sh ...`, but `env` strips `tag=q8a1` before `heavy.sh` sees it, so my jobs ran at priority 2 (folder name contains `pdbind`), not priority 1. (b) The dblink file runs (about 25 s each) and the lint tools and probes were run directly, not through `heavy.sh`. (c) The fail-before run needed one edit of the copied test file (see item 5 of the table). (d) A first dblink pair on server C used the head `src` for the "old" tree (editable install); only the later server-B pair set `PYTHONPATH` to the old `src` (checked). (e) I cannot report my own token use.

## Table
| # | Item | Command (short) | Exit | Last line |
|---|---|---|---|---|
| 1 | full suite | `env tag=q8a1 heavy.sh uv run --no-sync pytest -p no:cacheprovider -q -m "not live and not perf" -rs` (own Postgres 16.15, UTF8, port 54931, `PGHOST`/`PGPORT` in the server environment, checked in `/proc/<pid>/environ`) | 0 | `10829 passed, 2 skipped, 28 deselected in 338.32s (0:05:38)` |
| 2 | bind mutants | `heavy.sh uv run --no-sync python tests/bind_mutants.py` | 1 | `170 of 174 good; problems: [B39, B43, B60, B153]` (174 rows) |
| 2b | B153 alone | same, `B153` | 1 | `0 of 1 good; problems: ['B153 ...']` |
| 3 | stage mutants | `heavy.sh ... python tests/stage_mutants.py` | 0 | `37 of 37 good; problems: []` |
| 4a | ruff check | `ruff check src tests demos tools` | 0 | `All checks passed!` |
| 4b | ruff format | `ruff format --check src tests demos tools` | 0 | `326 files already formatted` |
| 4c | bandit | `bandit -q -r src demos tools -ll` | 0 | warning only: `nosec encountered (B102), but no failed test on file src/hadavin_sdk/tools.py:389` |
| 4d | scan_repo | `python tools/scan_repo.py` | 0 | no output |
| 4e | server_scan | `python tools/server_scan.py` | 0 | no output (uv deprecation warning on `UV_NATIVE_TLS` only) |
| 4f | gitleaks | `gitleaks git --redact --no-banner --config .gitleaks.toml --log-opts refs/remotes/origin/main..HEAD` | 0 | `no leaks found` |
| 4g | handover files | `check-no-handover-files.sh wip/cloud-pd-bind 7d2e6f3e` | 0 | no output |
| 5 | fail-before | head `tests/test_bindguard.py` + `tests/bind_mutants.py` copied into a detached worktree of b8c88cac, `PYTHONPATH` = old `src` (checked: `hadavin_sdk.__file__` is the old tree) | 2, then 1 | run A: collection error `ImportError: cannot import name 'make_on_decided'` (nothing runs); run B (that one import wrapped in try/except in the copy): `62 failed, 166 passed, 1 skipped` |
| 6a-h | hostile probes | see below | 0 | see below |
| 7 | dblink test, environmental check | `pytest tests/demo_askdata/test_validate_harm.py` | see below | see below |

Skips (`-rs`, grouped): `tests/contracts/test_llm.py:95` Stubber refuses a malformed Converse shape (1); `tests/test_bindguard.py:479` no IPv6 loopback on this machine (1). Both expected; none from the database tests.

Queue waits (`heavy.sh`): full suite and bind mutants waited 0 s (queued 00:43:44 UTC = 06:13:44 IST, started 00:43:44); stage mutants waited about 4 min 10 s (started 00:47:54 UTC); the B153 re-run about 0 s. Runtimes: full 5:38 test time (ended 00:49:26), bind mutants about 3 min 24 s (ended 00:47:08), stage about 40 s.

## Fail-before (item 5)
Delta b8c88cac..HEAD touches 9 files (CHANGELOG.md, 7 files in `src/`, `tests/bind_mutants.py`, `tests/test_bindguard.py`). `tests/test_bindguard.py`: 20 test functions added, 1 removed (`test_the_five_stand_in_classes_hold_no_class_level_container`). Raw: `failbefore.log`, `failbefore2.log`, `failbefore2-failed-ids.txt`, `newtests-names.txt`.
- Run A (head test file as is): the module cannot be collected on old code.
- Run B (import of `make_on_decided` wrapped in try/except in the scratch copy; so tests that call it fail on old code for that reason too): 62 failed. Of the 20 added tests, **17 fail on old code, 3 pass on old code**: `test_a_container_referenced_many_times_is_charged_each_time_it_is_entered`, `test_every_plain_data_class_keeps_all_its_state_in_the_instance_dictionary`, `test_the_slot_list_of_the_approvals_is_pinned`. One added test names `make_on_decided` directly (it fails on old code for that reason alone). The 62 count includes older tests that fail only because `make_on_decided` is `None` in the scratch copy; I did not separate them.
- `tests/bind_mutants.py` (a runner) was not run on old code.

## Hostile probes (item 6). Made-up public-bind config (wildcard host, landing on loopback only through the same patch the repo tests use); no real network. Verdict words: REAL / 503 = counted as a real service, request refused; stand-in / 401 = served (the unsigned made-up request is answered 401 by the signature check).
Probe scripts changed from the batch 6 runner's: the test helper now builds the approvals with `make_on_decided({})` (a lambda is counted as held at this head).

**(a) metaclass spoofs and look-alikes** held in a `FakeChannel` instance dictionary (`probes/probe_a.log`): 13 of 13 read REAL (503): instance of a class whose metaclass defines `__eq__`/`__hash__`/`__instancecheck__` (also named `str`), the same as a dict key, in a list, nested at depth 5, a metaclass whose `__eq__`/`__hash__` raise, a subclass of `FakeChannel` named `FakeChannel`, a plain class named `FakeChannel` with the real module name, a `type` subclass named `Decimal` in module `decimal`, spoof classes named `dict` and `RunState`, the spoof class object itself, a metaclass instance, a class with a `__class__` property claiming `str`. Controls (str, dict of ints, Decimal) read stand-in (401). Nothing raised.

**(b) populated store** (`probes/probe_a.log`, `probe_b.log`): a lambda inside the channel stand-in AND inside the store stand-in at depth 1, 4, 7, 8, 9: all REAL (503). Atoms-only nesting: depth 7 and 8 read stand-in, depth 9 and 10 read REAL (fail closed). Size and cost (wall time for the question; Python peak extra memory):
- `[1]*10**6`: REAL, 0.8 ms, 0.01 MB. `[inner]*10**6` (one shared inner list): REAL, 0.9 ms. `[inner]*10**5`: REAL, 0.9 ms. Tuple of 10**6 shared values, set of 10**6 distinct ints, 10**6 references to a 1000-element list: all REAL, under 1 ms.
- 1000 references to one 1000-element list: REAL, 4.2 ms, 0.80 MB.
- 99999 atoms in one list: REAL (the instance's other values count toward the 100000 budget; the exact edge was not searched). 100001 atoms: REAL. Dict of 60000 int pairs (120000 values): REAL. Empty control: stand-in.
- No case took more than 5 ms or more than 1 MB extra.

**(c) every `Approvals` slot deleted with `object.__delattr__`** (11 slots, `probes/probe_b.log`): on the running public-bind server all 11 answer 503 (control 401; restored then 401; no dropped connection). New `serve()` call on the damaged object: `BindRefused` for `_channel`, `_config_facts`, `_detector`, `_hand_built`, `_on_decided`, `_overrides`, `_store`; **SERVED (no refusal) for `_audit_sink`, `_clock`, `_registry`; `AttributeError` (not `BindRefused`) for `_config`**. Class attribute patched (`real_now`, `held_services`, `receive`, `channel`, `config_facts`, `on_decided`): 503. `__class__` replaced by a subclass: 503. Name `receiver.Approvals` rebound to a subclass: 503. Name `requests.Approvals` rebound to a same-named subclass: 503. Property raising `AttributeError` for `channel`, `store`, `detector`, `config_facts`, `overrides`, `on_decided`, `config`, `registry`, `audit`, `clock`: 503 each. All back to 401 after restore.

**(d) RunState and on_decided** (`probe_b.log`): real member 401; member of another enum 503; `RunState` instance made with `str.__new__` 503; real member with a lambda hung in its dict 503, 401 again after removal. `on_decided`: core closure 401; lambda 503; closure whose holder is a `defaultdict` 503; **closure whose holder is a plain dict holding a lambda 401**; `str.upper` 503; core closure with its cell set to a list 503; **core closure whose dict holds a lambda 401**.

**(e) `serve()` with an unreadable held object** (`probe_b.log`): `BindRefused` for overrides that raise on iteration (also for a mapping proxy over a raising mapping), a channel with a raising `__getattr__` and a store holding a list subclass whose `__len__` raises (the last two with the held-service message). Slots: see (c); the `_config` case is `AttributeError`.

**(f) refusal text with hostile keys** (`probes/probe_d.log`): never raised for 15 keys and 4 class names, direct, through the running server, and through a new `serve()`. Keys with control characters, 10000 characters, 41 characters, lone surrogate, bytes, int, None, tuple, str subclass with hostile methods, and a line separator give the fixed label `held (unreadable)`; a key of 40 and 39 characters, `café` and `my_service` are written as plain words (`held <word>: <ClassName>`); the empty string gives `held : Obj`. Class names of 10000 characters, 41 characters and with control characters give `(unreadable)`; a plain class name is shown. Every logged line and every `BindRefused` text was printable. The class name with a NUL character cannot be made (Python refuses it). Answer was 503 each time.

**(g) `FakeSecretProvider` pin moment** (`probes/probe_e.log`, fresh interpreters): pinned **when the secrets module is imported** (its last line), whichever of the two modules is imported first (E2: pinned right after the receiver import when secrets was already loaded; E3: not pinned after the receiver import, pinned right after the secrets import). With only the receiver imported (E1) it is not pinned and the secrets module is not loaded. Patched after import and before the first question: not seen as stand-in (False) in E2, E3, and for an added class attribute (E6); a replaced class in the module dictionary: new and original instance both False (E5); instance holding a function False (E8); unpatched control True (E4). Changing `__bases__` is refused by Python (E7).

**(h) 100 threads at once** (`probes/probe_c.log`, `probe_c2.log`): 100 threads asking `is_stand_in` at once on an unchanged stand-in: 100 True. 100 threads x 30 questions while one thread adds a lambda at a random moment: 2790 questions (second run) started after the add all read REAL; questions started after the add that did not read REAL: 0 (first run 2670 / 0). HTTP posts from 100 threads: connection resets for 58 to 84 of 100 in the plain run (the stdlib server's small listen queue; no verdict); with up to 20 retries on a reset: round A 100 x 401, round B (function added) 100 x 503, round C (removed) 100 x 401.

## Dblink test (item 7): environmental, not caused by the change
`tests/demo_askdata/test_validate_harm.py` (253 tests), same file, same server setups:
- Server on port 54932 with NO `PGHOST`/`PGPORT` in its environment and nothing on the default socket: **1 failed, 252 passed at HEAD and at b8c88cac (old `src`, path checked)**; the failure is `[dblink-connect]`: `connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: No such file or directory`.
- Server on port 5432 with socket dir `/var/run/postgresql` (port was free, checked): `253 passed` (HEAD; the "old" run there used the head `src`, see deviation d).
- My main server with `PGHOST`/`PGPORT` in the server environment: the file passes inside the full suite (exit 0).
- One server run of port 54932 while a server on 5432 was running also passed (253): the dblink connected to the other server's default socket; I discarded that as a test of the setup and redid it with only one server running.

## Cleanup
My Postgres servers (ports 54931, 54932, 5432) stopped (`pg_ctl stop`, "server stopped"), extra data folders removed; extra worktree `ER-pdbind7-old` removed; worktree `ER-pdbind7` and its venv kept. No process of mine is left; the builder's Postgres (port 54897) and its `heavy.sh` jobs were not touched. Nothing added to git.

Time: about 20 minutes of real clock (00:37 to about 00:57 UTC = 06:07 to 06:27 IST).
