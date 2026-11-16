# EVIDENCE RUNNER results: PD-bind batch 6, head b8c88cacc8d7d4dba1c6a858d763e16364f6f716

Runner only records, no judgement. Worktree `/home/user/build/ER-pdbind6` (detached; `git rev-parse HEAD` equals the sha above; `git status` clean after all runs). Raw logs: `/home/user/build/evidence-raw/pdbind6-b8c88cac/` (probes in `probes/`, probe scripts in `/home/user/build/pdbind6-probes/`). Nothing committed or pushed. No spend, no live calls, no secrets.

## Not run / deviations (first)
1. **My first setup was wrong and was redone.** `uv sync --locked` (without extras) gave a venv with no cloud libraries; the first `bind_mutants` run stopped at "the unmutated copy does not pass its tests" (cause: `test_importing_the_package_binds_no_socket` could not import 18 modules). I killed my own queued/running jobs, re-synced with `uv sync --locked --all-extras --group test --group scan` (exit 0) and reran everything. The failed run is kept as `FAILED-setup-bind_mutants-no-extras.log`; only the reruns are in the table.
2. **The full run has 2 skips, not 1.** Second skip: `tests/test_bindguard.py:478` "this machine has no IPv6 loopback" (this machine, not database setup). The other skip is `tests/contracts/test_llm.py:95` (Stubber). Not skipped: the database tests (own Postgres, `HADAVIN_TEST_PG_DSN` set). So the builder's "458 skipped" is NOT reproduced here: those 458 are not skipped in this setup (10800 passed). I did not see the builder's environment, so I cannot say why theirs skipped.
3. Priority: `heavy.sh` takes the queue priority from the folder name or arguments; I passed the extra word `q8a1` as the last argument (and `HEAVY_TAG=q8a1`, which the script does not read) so the job ran at priority 1, as the brief asks. Jobs ran with `nice -n 19`.
4. Fail-before ran only `tests/test_bindguard.py` (the only changed test file with tests that run on old code). `tests/bind_mutants.py` (also changed) is a runner of mutants and was not run on old code.
5. `gitleaks` ran with `refs/remotes/origin/main..HEAD` (15 commits). Bandit prints a "nosec but no failed test" warning for `src/hadavin_sdk/tools.py:389` (exit 0).
6. Time box: about 25 minutes of real clock (00:10 to about 00:35 UTC, which is 05:40 to about 06:05 IST).

## Results
| # | Item | Command (short) | Exit | Last line |
|---|---|---|---|---|
| 1 | full suite | `heavy.sh uv run --no-sync pytest -p no:cacheprovider -q -m "not live and not perf" -rs` (own Postgres on a private port) | 0 | `10800 passed, 2 skipped, 28 deselected in 257.36s` |
| 2 | bind mutants | `heavy.sh python tests/bind_mutants.py` | 0 | `154 of 154 good; problems: []` (154 rows `ok`, none `BAD`) |
| 3 | stage mutants | `heavy.sh python tests/stage_mutants.py` | 0 | `37 of 37 good; problems: []` |
| 4a | ruff check | `ruff check src tests demos tools` | 0 | `All checks passed!` |
| 4b | ruff format | `ruff format --check src tests demos tools` | 0 | `326 files already formatted` |
| 4c | bandit | `bandit -q -r src demos tools -ll` | 0 | only the nosec warning (item 5 above) |
| 4d | scan_repo | `python tools/scan_repo.py` | 0 | no output |
| 4e | server_scan | `python tools/server_scan.py` | 0 | no output |
| 4f | gitleaks | `gitleaks git --redact --no-banner --config .gitleaks.toml --log-opts refs/remotes/origin/main..HEAD` | 0 | `no leaks found` |
| 4g | handover files | `check-no-handover-files.sh wip/cloud-pd-bind <sha>` | 0 | no output |
| 5 | fail-before | head `tests/test_bindguard.py` + `tests/bind_mutants.py` copied into a detached worktree of d5537f99; `PYTHONPATH` = old `src` (checked: `hadavin_sdk.__file__` is the old tree) | 1 | `20 failed, 179 passed, 1 skipped` |
| 6a-e | hostile probes | see below | 0 | see below |

Skips in the full run (`-rs`, grouped): `tests/contracts/test_llm.py:95` Stubber refuses a malformed Converse shape (1); `tests/test_bindguard.py:478` no IPv6 loopback on this machine (1).

## Fail-before (item 5)
Delta d5537f99..HEAD touches 8 files: CHANGELOG.md, `approvals/receiver.py`, `approvals/requests.py`, `bindguard.py`, `defaults.py`, `standins.py`, `tests/bind_mutants.py`, `tests/test_bindguard.py`. Test functions added in `test_bindguard.py`: 22 (none removed). On old code, 20 tests fail (raw `failbefore-ids.txt`).
- Added tests that FAIL on old code: 18 of 22.
- Added tests that PASS on old code (4): `test_a_function_put_in_after_an_earlier_question_is_seen_at_the_next_one`, `test_one_hundred_threads_logging_one_hundred_sets_each_raise_nothing`, `test_a_class_attribute_equal_to_the_pinned_one_but_not_the_same_object_reads_as_real`, `test_a_class_dictionary_key_that_is_a_text_subclass_is_not_the_pinned_key`.
- 2 further failing ids are older tests changed in the delta: `test_a_function_hidden_inside_a_stand_in_reads_as_real_up_to_the_depth_limit`, `test_the_listener_reaches_the_approvals_only_through_the_signature_check`.
- Round 5 recorded 19 failed on the previous head; this run records 20 (the batch 6 tests are a different set). I did not compare against the builder's own count.

## Hostile probes (item 6). Made-up public-bind config (wildcard host, bound on loopback only through the same patch the repo tests use); no real network.
Verdict words: `is_stand_in` True = the object still reads as a core stand-in; REAL / 503 = counted as a real service, request refused; 401 = served (the unsigned made-up request was answered 401 by the signature check, i.e. not refused).

**(a) 25 held values** put into a `FakeChannel` instance dictionary on a running public-bind server (`probes/probe_a.log`):
- Read as REAL (refused, HTTP 503), 22 of 25: bytearray, str subclass, class object, function, lambda, bound method, functools.partial, generator, property, memoryview, set of functions, dict with a function key, dict key with hostile `__eq__`/`__hash__`, defaultdict with a function factory, deque of functions at depth 3, 4 and 5, 100001 small values, cyclic list, list nested 5 deep (atoms only), int subclass, plain `object()`.
- Read as stand-in (served, 401), 3 of 25: `Decimal`, `Path`, `threading.Lock` (all three are in the module's plain-data list).
- No foreign value read as held. Controls (plain str, dict of ints, 3 and 4 levels of lists of atoms, deque of ints) read as stand-in; after cleanup the channel reads as stand-in again.
- Note: a list nested 5 deep that holds only atoms also reads as REAL (the depth limit is 4); recorded as observed.

**(b) Approvals tampering, answer of the receiver on a public bind** (`probes/probe_b.log`; each row: control before, answer after, answer after restore):
- 503: class attribute patched (`real_now`, `held_services`, `receive`, `channel`, `store`); slot deleted with `object.__delattr__` for `_channel`, `_store`, `_config_facts`, `_detector`, `_overrides`, `_hand_built`; `__class__` replaced by a subclass; name `receiver.Approvals` rebound to a subclass; property raising `AttributeError` for `channel`, `store`, `detector`, `config_facts`, `overrides`; real channel put in with `object.__setattr__`. All returned to 401 after restore.
- **401 (still served, not refused), 3 rows:** slot `_config`, `_audit_sink` or `_registry` deleted with `object.__delattr__` (control 401, after 401). No dropped connection and no traceback in any row.

**(c) Concurrency** (`probes/probe_c.log`, `probe_c2.log`):
- 100 threads asking `is_stand_in` at once on an unchanged stand-in: 100 True. The same 100 threads POSTing at once: 58 got 401 and 42 got `ConnectionResetError` (the stdlib server's listen queue; this is a connection reset, no verdict).
- 100 threads x 30 questions while one thread adds a lambda at a random moment: 2460 questions started after the add all read REAL (`is_stand_in` False and `held_services_found` non-empty); 540 started before or during read stand-in; questions started after the add that did not read REAL: 0.
- HTTP with retry on a reset connection (up to 20 retries): round A (stand-in only) 100 x 401; round B (function added between rounds) 100 x 503; round C (function removed) 100 x 401.

**(d) Refusal log with hostile text** (`probes/probe_d.log`):
- Never raised in any case (control characters, 10000 characters, lone surrogate, bytes, int, None, tuple).
- Through the server end to end (hostile key in the overrides): control-character, lone-surrogate, bytes, int, None and tuple keys are logged as `held (unreadable): object`; the 10000-character key is logged cut to its first 80 characters followed by `...` (log line 170 characters; the first 80 characters of that hostile text do appear in the log); the answer was 503 in all cases.
- Calling `receiver._refused` directly with a non-text name (bytes, int, None, tuple) writes no log line at all (the join fails inside the guarded block); the control-character text written directly appears with its control characters inside the logged message; those direct calls are not reachable through `held_services_found`, which already turns such keys into `held (unreadable)`. The 503 was not affected.

**(e) `FakeSecretProvider` pin moment** (`probes/probe_e.log`, fresh interpreters):
- Pinned **at import** of `hadavin_sdk.approvals.receiver` only if `hadavin_sdk.actions.secrets` was already imported (E2: pinned True). Otherwise it is pinned at the **first question** (E1/E3: not pinned after the receiver import, pinned afterwards).
- E2 (module imported first): `FakeSecretProvider.get` patched after import and before the first question, `is_stand_in` -> **False** (seen).
- E3 (receiver imported first): same patch before the first question, `is_stand_in` -> **True** (not seen; the pin is taken from the patched class). Control E4 unpatched: True.
- E5 (E3 layout): a same-name subclass put in the module dictionary before the first question: new instance -> True, original instance -> False.

## Cleanup
Own Postgres stopped (`pg_ctl stop`, "server stopped"); extra worktree `ER-pdbind6-old` removed; worktree `ER-pdbind6` and its venv kept. Own queued and killed runs stopped; no process of mine left. Nothing added to git.
