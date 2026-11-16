# P5b4 round 3, adversarial review

Status: REPORTED (saved from the reviewer hand-back, which is model output, not user authority).

P5b4 ticket review, round 3 (adversarial). Verdict: 0 Blockers, 4 Majors, 6 Minors, 1 Nit. The ticket is close to buildable. The Majors are one spec gap, two mutants that cannot be killed as written and one possible lock deadlock. All cites into src and tests held on the on-disk tree (list under Verified). Current main differs from the ticket's cited commit in no cite I tried. Cites into P5a and P5b3 were checked by grep only.

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R3-ADV-1 | Major | 14, 134-139, 159-161, 328; S1 `print` channel (line 314), S8 | The ticket never says where the stream guard sends its rewritten `stream_line len=N` text. This matters most on the tick. After fd 2 and fd 1 point at the null device, the guard's wrapped original `sys.stderr` and `sys.stdout` write into that null device. S8 and the S1 stdout half expect `stream_line` to be visible, so it must go through the saved-fd stream. A builder who sends it to the captured or original stream gets invisible lines. The stdout guard is worse: fd 1 is null, so its lines have nowhere to go unless they go to stderr. The ticket only says "emit" uses the saved duplicate. | State that both guards (stderr and stdout) write their `stream_line len=N` through the same sink as `LoggingHandle.emit`. That sink is the saved-fd stream when the redirect is active, otherwise the stream captured at session start. Add one assertion to S8 that stdout-origin text also shows as `stream_line` on stderr. |
| R3-ADV-2 | Major | 73 vs 245; K13 rows (355) | Equivalent mutants in K13. `root level` is set to WARNING by a non-unattended install, and pytest's default root level is WARNING. So the K13 entry that skips restoring the root level changes nothing and survives. The same holds for `sys.stderr` and `sys.stdout`. A non-unattended install never replaces them, yet U1 says "after one install restores all 10 globals". Line 73 says the first call "changes all of them", but line 74-80 says the stream guard comes only with `unattended`. | U1 must pre-set the root level to a non-default value (for example 5 or 25) before the install. The `sys.stderr` and `sys.stdout` cases must use `unattended=True`. Reword line 73 to "changes all except the stream guard". |
| R3-ADV-3 | Major | 261 (U9 row ii); K8 (350) | The killer for K8 cannot fail on `raiseExceptions` as described. A foreign handler "whose `emit` raises" does not reach `handleError`. `Handler.handle` does not catch it, so the exception goes into the logging call and the test crashes. That is a CRASH verdict, not an assertion kill. `--- Logging error ---` is printed only if the foreign handler's `emit` catches the error and calls `self.handleError(record)`, as `StreamHandler` does. The ticket does not say so. With a hand-written `emit`, K8 is also not killed by assertion. | Specify the foreign handler as a `StreamHandler` subclass whose `emit` calls `self.handleError(record)` after a raised error with the canary, with a real stream, so the assertion is on "no Logging error text". Or move K8's `only_test` to U10 and say so. |
| R3-ADV-4 | Major | 85 (Lock), 114-127 | Possible cross-thread deadlock between the logging handler's own lock and the shared RLock. `logging.Handler.handle` takes `OwnHandler.lock` (its own RLock) and then calls `emit`, which takes the shared RLock. Thread A holds the shared lock in a guarded `write`. A GC pass runs a `__del__` that calls `_LOG.error` and needs `OwnHandler.lock`. Thread B holds `OwnHandler.lock` and waits for the shared lock. Both wait on each other and the tick hangs. The ticket's RLock reasoning covers only same-thread re-entry, and U29 tests only that case. I did not run this (UNVERIFIED), but the lock order is inverted by construction. | State that `OwnHandler.lock` IS the shared RLock (override `createLock`, or assign `self.lock = shared`), so there is one lock. Add an assertion to U29 that `OwnHandler.lock is handle._lock`, with a mutant. Add a cross-thread finalizer row if wanted. |
| R3-ADV-5 | Major | 272, 382, 526 | K39 (`uninstall` does not take the lock) has no deterministic killer. The test needs "a barrier inside a test double of the lock", but the Interface adds no seam and says "Nothing new is added to the interface". How the test replaces the lock is a guess. The ticket itself lists this as UNVERIFIED. | Name the seam: a module-level lock factory, or a lock created in `bootstrap_logging` that tests patch before install. Or kill by behaviour: a writer thread blocks inside a stream double on an `Event` while `uninstall()` runs in another thread. Assert `uninstall` waits (it has not returned before the Event is set). |
| R3-ADV-6 | Minor | 127 | "Goes to the standard `handleError`" is not specified as a call. If `OwnHandler.emit` has no `try/except Exception: self.handleError(record)` around the write, a failure (closed stream, `OSError`) propagates into the application's logging call. Library mode is the case where this matters most, because the exception then reaches pytest or the embedder. There is no U row for it. | Write the `try/except Exception` around the whole of `emit` in the spec, calling `self.handleError(record)`. Add a U9 row where the captured stream raises on `write`: no exception reaches the caller. |
| R3-ADV-7 | Minor | 162 | `errno=<int>` is wrong when `OSError.errno` is `None` (a monkeypatched `OSError("x")` in U25 gives `None`). The builder would print `errno=None`, or crash in the format. | Say `errno=0` when `exc.errno` is not an int. U25 raises `OSError(errno.EBADF, ...)`. |
| R3-ADV-8 | Minor | 166-167 | The ticket does not say that the `atexit` flush is registered only at process entry. It says only that an in-process `cli_entry` would register an `atexit` inside pytest (line 177). In library mode, registering per session leaves one stale `atexit` function per test that runs at pytest exit against an old, closed stream. | State "registered once, at process entry only (`library_mode=False`)". Add one U row that library mode leaves `atexit._ncallbacks()` unchanged, or accept it as a build-time check. |
| R3-ADV-9 | Minor | 137 | `fileno()` raising `io.UnsupportedOperation` breaks any dependency that calls `faulthandler.enable()` (default file is `sys.stderr`) or passes `sys.stderr` to a subprocess during the tick. It raises inside a step, so the step fails (exit 1) for a harmless call. The ticket says `src/` has no such use (grep: none, confirmed) but does not cover the pinned dependencies. | Add it to limit (e) and the evidence note, or return a fileno of the null device. UNVERIFIED for pinned dependencies. |
| R3-ADV-10 | Minor | 228 (limit i) | `captureWarnings` does not cover `warnings.showwarning(..., file=<stream>)` called with an explicit `file`. The standard replacement passes that call to the original function, which writes raw text to that file. On the tick the stream guard or the null device catches it. On non-tick commands it reaches the terminal raw. | Add it to limit (i) and its owner-visible sentence. |
| R3-ADV-11 | Minor | 259, 297, 367 | Test hygiene. U7 `logging.addLevelName(30, <canary>)` changes global state for the whole session and must be undone, or later tests print the canary as the level name. K24 refers to S6 case `interrupt_in_main`, which S6 does not list; its case is "`KeyboardInterrupt` through the real `main`". U21 `--conf DIR tick` would run a real `_tick` in library mode; it needs `_tick` stubbed, and the ticket does not say so. | Name the restore (`monkeypatch` of `logging._levelToName` and `_nameToLevel`, or a `finally` with `addLevelName(30, "WARNING")`). Rename the S6 case id. State that U21 stubs `cli._tick`. |
| R3-ADV-12 | Nit | 407 | "The killers name 61 + 9 = 70 test functions or cases" is true only if the ids stay unique. Several killers are named by the function without a case id (for example the `test_s6_exit_mapping` family). The text reads as a count of distinct functions. | Say "70 runs, 70 distinct killer ids", or drop the sentence. |

## Verified (by reading or grep on the on-disk tree)
- **Template fields:** all 17 are present and in order (package id through rollback).
- **Counts:** these hold:
  - 28 unit rows (U1-U19 = 19, U21-U29 = 9) + 8 process rows (S1-S4, S6-S9) = 36 automated rows.
  - 63 mutant table rows (K1-K61, with K17 split and K55b added). Withdrawn: K7 and K29. 61 active.
  - 61 - 1 + 10 = 70 runs for the K13 entries.
  - The 54 - 1 + 5 = 58, then 61, chain.
  - The CHANGELOG has 28 rows and 33 ids.
- **Cites into `cli.py`:**
  - `cli.py:70-83`, `:81-82` (debug branch) and `:87` (ArgumentParser).
  - `:131`, `:132-133`, `:134-135` and `:282-284`.
  - `:287` (basicConfig), `:296-307`, `:299` (`build`) and `:309` (`run_tick`).
  - `:413-414` and the imports at `:36-46`.
  - `import logging` at `:29` is used only at `:287`.
  - `import traceback` (`:32`) is used only by the debug branch, which P5b3 deletes.
- **Cites into `src/`:**
  - Thread starts at `k1b/loop.py:104`, `tools.py:1122` and `guard/http.py:93`.
  - `approvals/receiver.py:40`, `:62-63` and `:65`.
  - `pyproject.toml:46-47`.
  - `defaults.py:10` is its only import.
  - `runtime/tick.py:246` (heartbeat format), `:273-278` (`_safe_log`), `:284-292` and `:316-317`.
  - `ci.yml` lines 34, 73, 88, 94 and 119.
  - `test_p7_tick.py` asserts at `:371-374`.
  - `test_k1b_cli.py:98` and `:260-261`, and `test_k1a_pass_k.py:116` (`SystemExit`).
  - `src/` has no `print`, `sys.stderr`, `sys.stdout` or `warnings.warn` outside `cli.py`, and no `subprocess`, `asyncio`, `faulthandler` or `.buffer` use.
- **Class names in own records:** P5b3 (grep, `P5b3.md`) changes `runtime/tick.py:73`, `:207` and `:328` to `class_name_of`. So a class name carrying text is not printed raw through the own-record allow-list, if P5b3 lands as written.
- **P5a:** `class_name_of(exc_or_type)` accepts a type (`P5a.md:63`), so `class_name_of(type(h))` is valid.
- **Mutant killers:** I traced the killers for K1-K6, K9-K12, K14-K28, K30-K38, K40-K61 and found them able to fail on the described change. The exceptions are the R3-ADV items above. K49 is killed because `bool` is an `int` subclass.
- **argparse head rule:** the first-colon rule plus full-match regex fails closed to `invalid arguments` in every message shape I walked through (ambiguous option, invalid choice, required arguments).
- **pytest config:** `pyproject.toml` has no `filterwarnings = error`, so the `warnings.warn` rows are not turned into exceptions.

## Not checked (UNVERIFIED)
- No code ran. Every claim about runtime behaviour is by reading: the lock-order deadlock (ADV-4), `faulthandler`, `showwarning(file=)`, and the pytest threadexception and unraisable plugins coexisting with our hooks.
- The P1m runner fields (`only_test`, `expect`, the empty-ini rule) and pull request 61. They are not on this tree.
- `tests/test_provider_errors_wire.py` (R14) and the library log levels behind it. The file is absent here.
- The claim of "24 own logger calls". A grep showed 34 matching lines in 10 files, including `getLogger` definitions, and I did not separate them.
- That every `approval_id` and `run_id` is exactly `str`.
- The P5a corpus and its R2 rows. P5b3 revision 3 and its final text of the `cli.py` lines.
- Windows behaviour. Python 3.12 behaviour. The pydantic 2.14.1 warning text.
- The Python 3.13.18 probes the ticket cites. The `atexit` order probe (evidence item 8). The `os.dup2(null, 1)` recipe for stopping exit code 120.
- Whether `migrate --p` is still ambiguous.
- The 11-15 agent-hour estimate.
- The files under `handover/reviews/` and `handover/evidence/`, which I did not read, per the order.
