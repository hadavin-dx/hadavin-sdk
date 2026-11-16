# P5b4 round 3 resolve (egm:egm-resolve, AUTO mode; LAST round)

**Status:** resolved (categorised; AUTO, so the skill's interactive gate is skipped per the lead's order 20 item 6 brief). The ticket is NOT edited. The fixes are build notes BN-1 to BN-17 below. They win over the ticket text. This file replaces the skill's default file name `goldfish_review_report.md`.
**Target:** `handover/tickets/P5b4.md` revision 3, full file read (582 lines; Tier A, redaction path).
**Findings:** 23 ids.
- `reviews/P5b4-round3-adversarial.md`, R3-ADV-1..12: 0 Blocker, **5 Major** (ADV-1 to ADV-5; the report's header says 4, but its table has 5, and the table is counted), 6 Minor, 1 Nit.
- `reviews/P5b4-round3-correctness.md`, R3-COR-1..11: 0 Blocker, 2 Major, 6 Minor, 3 Nit.
- Severity is taken from the tables and never changed here.
**Gate:** order 20 item 6 caps ticket review at 3 rounds. A redaction ticket gets a round 4 only if its last round had no Blocker and at most 2 Majors. Round 3 has 7 Majors (5 ADV, 2 COR). R3-ADV-2 and R3-COR-2 are one defect, so there are 6 distinct Major defects. The gate counts the round, not each report. So there is **NO round 4**. The ticket freezes at revision 3 with this file attached. The banner below goes under the ticket's status line. The build-start review (order 19 A, order 20 item 3) reads the ticket and this file together.
- Nothing is escalated to the owner.
- PENDING LEAD 17 is a NEEDS LEAD (redaction: owner-visible limits). The new items 18 to 21 are INFORM.

## Honest note (what I did NOT check, first)
- **Nothing was run.** No pytest, mutant, probe script, ruff or install. I wrote no git state, did not edit the ticket and did not touch `DECISIONS.md` or `owner-visible-limits.md`.
- **I read standard-library and pytest SOURCE only.** I used `inspect` with the repository's `.venv` interpreter, which is Python 3.13.18 and pytest 9.1.1. This is reading, not behaviour:
  - the ADV-4 deadlock was not reproduced;
  - the `--- Logging error ---` output of the ADV-3 recipe was not seen;
  - the R14 shim was not run.
- **The R3-COR-7 contest rests on the 3.13.18 source.** Python 3.12 was not read. My memory says that bpo-46557 landed in 3.11, which would make 3.12 behave the same, but that is UNVERIFIED.
- **BN-5 leaves one residual hang risk** (PENDING LEAD 21), and I did not measure how likely it is. The pattern is the one stock `logging` already has, and I reasoned that from the source, not from a run.
- **The six owner-visible entries in BN-15 are drafts** for the lead to append. Their "what a person must do" lines are my proposal.
- These were not re-read by me: P5a, P5b1 (`P5b1.md:43`), P1m, `tests/test_provider_errors_wire.py` (not on this tree), and the pinned dependencies' wheels. The UNVERIFIED items the ticket already lists stay as they are.

## Facts I checked myself (read on disk or in installed source)
- **F1, R3-ADV-3 and R3-ADV-4 are TRUE.** `logging.Handler.handle` (`/usr/local/lib/python3.13/logging/__init__.py:1011-1028`) does `with self.lock: self.emit(record)`. It has no `try` around the call, so an exception raised in a hand-written `emit` reaches the logging call. `self.lock` is the handler's OWN `threading.RLock`, made by `Handler.createLock` (`:958-963`), and it is not the guard's shared lock. `handleError` (`:1060-1105`) prints only `if raiseExceptions and sys.stderr`.
- **F2, R3-COR-1 is TRUE.** `basicConfig` adds a handler only `if len(root.handlers) == 0` (`:2092`). pytest 9.1.1 `LoggingPlugin._runtest_for` (`_pytest/logging.py:827`) wraps every test phase in `catching_logs(caplog_handler)` and `catching_logs(report_handler)`, which put two handlers on root. So the shim's `basicConfig` adds nothing under pytest.
- **F3, R3-COR-7 is FALSE on 3.13.18.** `logging._showwarning` (`:2301-2319`) calls `logger.warning(str(s))`, with the comment at `:2317`: "bpo-46557: Log str(s) as msg instead of logger.warning("%s", s)". So `record.msg` is the whole formatted warning, and `msg_len` is its real length, not 2.
- **F3 continued, R3-ADV-10 is TRUE.** The same function, when `file is not None`, calls the saved original `showwarning` with that file (`:2311-2313`). That writes raw text to the file.
- **F4, the module lock.** `Logger.isEnabledFor` (`:1774-1791`) takes logging's module lock `_lock` on a cache miss. `Logger.setLevel` takes it through `Manager._clear_cache`, and `Logger.removeHandler` takes it too. This is the base of the own finding in BN-5.
- **F5, R3-COR-5 is TRUE.** There are 25 own logger calls on this tree: the 24 that the `_LOG.<level>(` grep finds, plus `k1b/loop.py:100`, which calls `logging.getLogger(__name__).warning(`. The count is 24 after P5b3 deletes `approvals/receiver.py:63`.
- **F6, R3-COR-4 is TRUE.** P5b3 is "Revision 3" (`tickets/P5b3.md:1`). It still says `handle.emit` (`:108`, `:193`, `:604`), still lists "the `run_tick` move" (`:635`), and still cites `P5b4.md:414-419` (`:31`, `:612`). `handover/owner-visible-limits.md` exists. It holds entry 1 (P5b3) and has the rule "append one entry per limit at the end, numbered … Do not edit another author's entry".
- **F7, the cites for COR-8 and COR-11.** `cli.py:131` is `args = p.parse_args(argv)` inside `_main`, and `cli.py:134-135` dispatches `tick` before `load_config` at `:136`. `gate` calls `evals.gate(...)` through the module attribute (`cli.py:36`, `:148`) and `make(...)` (`:39`, `:150`), prints its result line to stdout (`:158-162`) and returns `0 if run.green else 1` (`:163`). `safe_head` is at `guard/runmap.py:485`.
- **F8, `atexit._ncallbacks` exists on 3.13.18.** It is private CPython API. BN-10's test uses it, and the builder replaces it with a counting spy on `atexit.register` if it is missing.

## Banner for the ticket (placed under the status line, word for word)
> **BUILD NOTES WIN.** Review round 3 (`reviews/P5b4-round3-adversarial.md`, `reviews/P5b4-round3-correctness.md`) had 7 Majors, so there is no round 4 (order 20 item 6). This ticket is FROZEN at revision 3. The builder applies build notes BN-1 to BN-17 in `reviews/P5b4-round3-resolve.md`. Where a build note and the text below disagree, the build note wins. The build-start review (order 19 A) reads this ticket together with those notes. The CHANGELOG sections are history, not instructions. Totals after the notes: 36 automated rows (unchanged), 68 mutant table rows, 66 active mutants, K13 = 9 entries, 74 mutant runs, 9 restored globals. In library mode the root logger level is never touched (BN-2).

## Decisions (one category per finding id)

| id(s) | category | decision (build note) |
|---|---|---|
| R3-ADV-1 (Major) | PROPOSE FIX | TRUE. Both guards write `stream_line len=N` through the session sink (the same stream as `LoggingHandle.emit`), never to the stream they replaced. A new S8 test checks the stdout half, and mutant K63 is added. **BN-1.** |
| R3-ADV-2 (Major), R3-COR-2 (Major) | PROPOSE FIX (surface cut for the root-level half) | TRUE: three K13 entries were equivalent mutants. The root-level entry is removed by the BN-2 cut, so library mode no longer touches the root level and K13 has 9 entries. The `sys.stderr` and `sys.stdout` entries become real because U1 installs with `unattended=True`. Line 73 is reworded. **BN-2, BN-3.** |
| R3-COR-6 (Minor) | PROPOSE FIX (surface cut; INFORM 19) | TRUE. In library mode the root level is never set or restored. Only the `OwnHandler` level changes. The embedder's level decides which records reach our handler. U28 (i) is rewritten and mutant K64 is added. **BN-2.** |
| R3-ADV-3 (Major) | PROPOSE FIX | TRUE (F1). The U9 (ii) foreign handler catches its own error and calls `self.handleError(record)`, and is installed with `unattended=False`. K8 is then killed on the assertion. **BN-4.** |
| R3-ADV-4 (Major) | PROPOSE FIX (with own finding N1; INFORM 21) | TRUE by construction (F1). `OwnHandler.lock` IS the shared RLock. Own finding N1: our code calls no `logging` API while it holds that lock (F4). New U29 (iii) identity test and mutant K65. The residual finalizer hang is stated. **BN-5.** |
| R3-ADV-5 (Major) | PROPOSE FIX (surface cut: no lock seam) | TRUE. K39 is killed by behaviour: a writer is blocked inside the sink double while `uninstall()` runs in a thread. No lock double and no new interface. The UNVERIFIED line 526 is closed. **BN-6.** |
| R3-COR-1 (Major) | PROPOSE FIX | TRUE (F2). The shim adds an explicit root `StreamHandler(sys.stderr)`, so R14's stated fail-before reason (the canary assertion) is what really fails. **BN-7.** |
| R3-ADV-6 (Minor) | PROPOSE FIX | TRUE. `OwnHandler.emit` is wrapped whole in `try/except Exception: self.handleError(record)`. New U9 (iii) and mutant K62. **BN-8.** |
| R3-ADV-7 (Minor) | PROPOSE FIX | TRUE. `errno=0` when `exc.errno` is not an `int`. U25 uses `errno.EBADF` and gains a case for an errno that is not an `int`. **BN-9.** |
| R3-ADV-8 (Minor) | PROPOSE FIX | TRUE. The `atexit` flush is registered once per process, at process entry only. New U1 test and mutant K66. **BN-10.** |
| R3-ADV-9 (Minor) | PROPOSE FIX (limit and check; INFORM 20) | TRUE as a gap. `fileno()` keeps raising (D12; it fails closed and adds no code). Limit (e) names `faulthandler.enable()` and passing `sys.stderr` to a subprocess. The builder greps the pinned packages. **BN-11.** |
| R3-ADV-10 (Minor) | PROPOSE FIX | TRUE (F3). `showwarning(..., file=...)` is added to limit (i) and to its owner-visible entry. **BN-12.** |
| R3-ADV-11 (Minor) | PROPOSE FIX | TRUE. U7 restores through `monkeypatch.setitem`, the S6 case ids are named, and U21 stubs `cli._tick`. **BN-13.** |
| R3-COR-8 (Minor) | PROPOSE FIX | TRUE. The U21 stubs and the S4 recipe are written out (F7). **BN-13.** |
| R3-COR-3 (Minor) | PROPOSE FIX | TRUE. Under pytest, the K9 mutant prints nothing, so its killer is U11's positive assertion `py.warnings line missing`. **BN-14.** |
| R3-COR-4 (Minor) | PROPOSE FIX (NEEDS LEAD 17 updated) | TRUE (F6). The stale lines are re-pointed. The six limits are drafted as separate numbered entries in the file's own format, for the lead to append. **BN-15.** |
| R3-COR-7 (Minor) | CONTEST | FALSE on 3.13.18 (F3): `_showwarning` logs `str(s)` as `msg`, so `msg_len` is the real length of the formatted warning. A reader can check this at `/usr/local/lib/python3.13/logging/__init__.py:2317`. The reviewer flagged it as "from memory … UNVERIFIED". No build note. 3.12 is UNVERIFIED (Honest note). |
| R3-COR-5 (Minor) | PROPOSE FIX | TRUE (F5): 25 calls, 24 after P5b3. **BN-16.** |
| R3-COR-9 (Nit) | PROPOSE FIX | K19, K20 and K40 are marked "POSIX-only?". **BN-16.** |
| R3-ADV-12 (Nit), R3-COR-10 (Nit) | PROPOSE FIX | The count sentence reads "74 runs, 74 distinct pytest ids". The function-name count is dropped. **BN-16.** |
| R3-COR-11 (Nit) | PROPOSE FIX | `safe_head` at `guard/runmap.py:485`. **BN-16.** |
| (resolve, own) N1 | PROPOSE FIX | No `logging` API call is made while the shared lock is held (F4). Part of **BN-5.** |
| (resolve) table delta | fact only | **BN-17** holds the full mutant-table delta and the totals, so the builder has one place to read them. |

## Build notes (round 3), to be copied into the ticket as the section "Build notes (round 3)"

**BN-1. Where the stream guard writes (R3-ADV-1).**
- Both stream guards, on `sys.stderr` and on `sys.stdout`, write every `stream_line len=N` line through the **session sink**. The session sink is the stream that `LoggingHandle.emit` writes to:
  - at process entry, once the fd redirect is in place, it is the stream opened on the saved duplicate of fd 2;
  - otherwise, it is the `sys.stderr` captured when the install session started.
- A guard never writes to the stream object it replaced. So text written to stdout during the tick shows up as `stream_line` lines on stderr, and nothing is written to stdout (fd 1 is the null device at process entry).
- The sink is switched to the saved-fd stream by step (1) of the upgrade (the fd redirect), before step (2) puts the guards up (Interface "Order inside the upgrade").
- In library mode, U14, U15 and U16 read the `stream_line` lines from `capsys.readouterr().err`. That includes the `print()` row of U16.
- **S8 gains one test.** In the same tick, a step also calls `sys.stdout.write(<canary2> + "\n")`. A `stream_line len=N` line for it appears on stderr, `<canary2>` is absent from both streams, and stdout is empty (`test_s8_stdout_line_on_stderr`, message `stdout stream_line missing on stderr`).
- **New mutant K63:** "the stream guard writes its `stream_line` to the stream it replaced instead of the session sink". Its killer is p `test_s8_stdout_line_on_stderr`, with `expect` `stdout stream_line missing on stderr`. Also fails (note): `test_s8_partial_line_at_exit`.

**BN-2. Library mode never touches the root level (R3-COR-6; the root-level half of R3-ADV-2 and R3-COR-2; INFORM 19; surface cut).**
- The root logger's level is set ONLY when `library_mode` is False. It is WARNING at the first call and INFO at the tick upgrade. Nothing restores it, because nothing is uninstalled at process entry.
- In library mode, a level changes only the `OwnHandler`'s level: WARNING at the first call, INFO when unattended. The embedder's root level decides which records reach the handler.
- The level stack therefore restores 9 globals by identity: root handlers, `raiseExceptions`, the `captureWarnings` state, `logging.lastResort`, the three hooks, `sys.stderr` and `sys.stdout`. The tick upgrade also restores, by value, the `OwnHandler` level it recorded (K55b, unchanged). "Root level, by value" is deleted from `uninstall` and from U1.
- The sentence "Unattended gives INFO and non-unattended gives WARNING, the same as today" now applies to process entry only.
- **Limit (a) gains:** "In library mode the embedder's root level decides which records reach our handler. With root at WARNING (Python's default), the tick's INFO heartbeat is not printed."
- **Tests that need INFO or DEBUG records set the root level themselves**, with `caplog.set_level(...)`, which pytest restores after the test:
  - U2, U28 (i) and (ii), U27 if it needs INFO records, and U1's two `cli.main([... "tick"])` rows set INFO;
  - R14 uses `caplog.set_level(logging.DEBUG)` for root, instead of a bare `setLevel` that nothing would undo, and sets the `OwnHandler` level with `setLevel` as before.
- **U28 (i)** "root level restored" becomes `test_u28_library_tick_root_level_untouched`. A made-up tick step records `logging.getLogger().level` during the tick, and the test reads it again after `main` returns. Both must equal the value set before the call (message `root level changed in library mode`).
- **New mutant K64:** "library mode sets the root level as at process entry". Its killer is u `test_u28_library_tick_root_level_untouched`, with `expect` `root level changed in library mode`.
- K55 is unchanged. Its killer, `test_u28_library_tick_heartbeat_visible` (root preset to INFO), still fails when the upgrade leaves the `OwnHandler` at WARNING.

**BN-3. U1 installs unattended, so every K13 entry is a real change (R3-ADV-2, R3-COR-2).**
- Line 73 reads: "the first call of a session changes all of them, except the stream guard (`sys.stderr`, `sys.stdout`), which only a call with `unattended=True` installs".
- `test_u1_uninstall_restores_global[<global>]` installs with `bootstrap_logging(unattended=True, library_mode=True)`.
  - Before the install, the test reads each of the 9 globals. After one `uninstall()`, each must be the same object as before, by identity (message `not restored: <global>`).
  - Each of the 9 globals is changed by this install. `raiseExceptions` goes True to False and `captureWarnings` goes off to on. `lastResort`, the three hooks and both streams are replaced, and root gains the `OwnHandler`. So no spy values are needed. The hooks may be pytest's own (its threadexception and unraisableexception plugins), and identity with the value read before the install still holds.
- **K13 is 9 entries** (the root-level entry is removed by BN-2).

**BN-4. U9 (ii): a foreign handler that really reaches `handleError` (R3-ADV-3).**
- The guard is installed in library mode with `unattended=False`, so that `handleError`'s writes to `sys.stderr` reach `capsys` as text and are not turned into `stream_line`.
- The foreign handler is `class _Foreign(logging.Handler)`, put on a made-up logger `vendorlib`. Its `emit` is `try: raise ValueError(<canary>)` / `except Exception: self.handleError(record)`. This is the pattern that `StreamHandler.emit` uses (F1).
- One record is logged on `vendorlib`. Then:
  - no exception reaches the test;
  - `capsys.readouterr().err` holds no `--- Logging error ---`, no `Arguments` and no canary (message `Logging error printed`).
- With K8, `raiseExceptions` stays True (pytest's default), and `handleError` prints the header and the traceback, canary included. So K8 is KILLED on the assertion, not as a CRASH.

**BN-5. One lock, and no `logging` call under it (R3-ADV-4; own finding N1; INFORM 21).**
- **`OwnHandler.lock` IS the session's shared `threading.RLock`.** The builder either overrides `createLock` to assign the shared lock, keeping the standard at-fork registration, or assigns `self.lock = shared` right after `super().__init__()`. `Handler.handle`'s `with self.lock:` and our `emit`, guarded `write` and `uninstall` then take one lock, so there is one lock order.
- **No `logging` call while the shared lock is held (own finding N1).** Logging's own module lock `_lock` is taken by `isEnabledFor` on a cache miss, by `setLevel` and by `addHandler`/`removeHandler` (F4). So our own code, while it holds the shared lock, makes no call into the `logging` module and takes no other lock.
  - `uninstall` holds the shared lock only to flush the stream guard's half line, put `sys.stderr` and `sys.stdout` back and mark the guard closed. It restores the root handlers, `lastResort`, `captureWarnings`, `raiseExceptions`, the `OwnHandler` level and the hooks after it releases the lock.
  - `audit_handlers` takes its list from a snapshot (`list(logging.Logger.manager.loggerDict.items())`), removes handlers with `removeHandler`, and emits its lines only after each logging call has returned. It never emits from inside a logging call.
  - The build-start and result reviewers check this rule by reading the code. No mutant can kill it deterministically, and this is said plainly.
- **U29 gains row (iii), in process** (it cannot hang): after a library-mode install, `assert root_own_handler.lock is handle._lock, "OwnHandler.lock is not the shared lock"` (`test_u29_own_handler_uses_shared_lock`). It lives in `tests/test_output_guard.py`, as U26 row (i) does.
- **New mutant K65:** "`OwnHandler` keeps its own `RLock` from `createLock`". Its killer is u `test_u29_own_handler_uses_shared_lock`, with `expect` `OwnHandler.lock is not the shared lock`.
- **No cross-thread timing row is added.** There is no point between `Handler.handle` taking its lock and calling `emit` at which a test can signal, so such a row could only rely on a sleep. It could let the mutant survive and could never fail the right code, and the identity test kills the mutant without timing.
- **Residual, stated (PENDING LEAD 21):** a garbage-collection pass can run a finalizer that logs while one thread holds our lock. That finalizer can then wait for logging's `_lock`, which a second thread holds while its own finalizer waits for our lock. Stock `logging` has the same two-lock pattern with any handler (`Handler.lock` and `_lock`). P5b4 adds entry points (guarded writes) but no new pair of locks. The result is a possible hang, not a leak.

**BN-6. K39 is killed by behaviour (R3-ADV-5; no lock seam).**
- `test_u14_uninstall_waits_for_write_in_flight` (new; `test_u14_writer_during_uninstall` stays as written, with the words "a barrier inside a test double of the lock" deleted and no mutant):
  - before the install, `monkeypatch` puts a sink double in `sys.stderr`. The session captures it. The double's `write` sets an `Event` called `entered` and then waits on an `Event` called `release`;
  - after `bootstrap_logging(unattended=True, library_mode=True)`, thread W calls `sys.stderr.write("x\n")`. The guard holds the shared lock while it writes `stream_line len=1` to the sink (BN-1), so W blocks inside the double with the lock held. The test waits on `entered`;
  - thread U calls `handle.uninstall()`. Then `U.join(timeout=0.5)`, and `assert U.is_alive(), "uninstall did not wait for the write in flight"`;
  - then `release.set()`, both threads are joined, and U has returned.
- With K39, U never takes the lock and returns at once, so the assertion fails. With the correct code, U cannot finish before `release` is set, so the row cannot fail on a slow machine. A slow machine can only let the mutant survive, never fail a correct build.
- K39's `only_test` is u `test_u14_uninstall_waits_for_write_in_flight`, and its `expect` is `uninstall did not wait for the write in flight`. The UNVERIFIED line "That K39 can be killed deterministically with the barrier described in U14" is deleted.
- Interface: nothing new. "Nothing new is added to the interface" holds.

**BN-7. The R14 fail-before shim really meets the old handler (R3-COR-1).**
- The shim's `bootstrap_logging(unattended=True)` does not call `logging.basicConfig` (F2: that does nothing while pytest's handlers are on root).
  - It adds `h = logging.StreamHandler(sys.stderr)` with `h.setFormatter(logging.Formatter("%(message)s"))` to root and sets root to INFO. This is what the old tick's `cli.py:287` gives in a real process, where root has no handler.
  - The shim handle's `uninstall()` removes `h` and puts the root level back.
- R14's expected failure then stays as written: "fails on its canary assertion", because the old handler prints the `httpx2` INFO line and, after R14's DEBUG setting, the DEBUG lines, all with the canary.
- R3-AUTH-6's sentence reads "the shim adds a root `StreamHandler(sys.stderr)` as the old tick did (not `basicConfig`, which is a no-op under pytest)". The runner pastes the failing assertion line, as before.

**BN-8. `OwnHandler.emit` cannot raise into the caller (R3-ADV-6).**
- The whole body of `OwnHandler.emit` sits inside `try: ... except Exception: self.handleError(record)`. The formatting case keeps its own inner `try` and its `withheld=format_error` line.
- With `raiseExceptions` False, the standard `handleError` prints nothing. Line 127 ("goes to the standard `handleError`") is now true by construction.
- **U9 gains row (iii):** before the install, `monkeypatch` puts in `sys.stderr` a stream double whose `write` raises `OSError(errno.EBADF, "made-up")`. After `bootstrap_logging(library_mode=True)`, `logging.getLogger("hadavin_sdk.tick").error("x")` raises nothing (message `write failure reached the caller`) (`test_u9_own_handler_write_failure_is_silent`).
- **New mutant K62:** "the outer `try/except` of `OwnHandler.emit` removed". Its killer is u `test_u9_own_handler_write_failure_is_silent`, with `expect` `write failure reached the caller`.

**BN-9. `errno` in the redirect failure line (R3-ADV-7).**
- The line is `output_guard: fd_redirect_failed errno=<n>`. Here `<n>` is `exc.errno` when `type(exc.errno) is int`, else `0`.
- U25's `os.dup2` and `os.dup` patches raise `OSError(errno.EBADF, "made-up")`, and the rows assert `errno=` followed by `errno.EBADF`.
- New case: `os.dup2` raises `OSError("made-up")` (errno `None`), giving exit 2 and `errno=0` (`test_u25_errno_not_int_prints_0`, message `errno not 0 for a non-int errno`). No mutant: a mutant that prints `errno=None` fails this test, and that is noted here.

**BN-10. The `atexit` flush is registered once, at process entry only (R3-ADV-8).**
- `output_guard` registers its `atexit` flush once per process, at the process-entry upgrade, when `library_mode` is False and the stream guard goes up. It is never registered in library mode.
- **U1 gains:** `atexit._ncallbacks()` is read before and after a `bootstrap_logging(unattended=True, library_mode=True)` plus `uninstall()`, and both values must be equal (message `atexit callback added in library mode`) (`test_u1_library_mode_registers_no_atexit`). If `_ncallbacks` is missing (F8), the test spies on `atexit.register` instead.
- **New mutant K66:** "the `atexit` flush is registered by every install session". Its killer is u `test_u1_library_mode_registers_no_atexit`, with `expect` `atexit callback added in library mode`.

**BN-11. `fileno()` keeps raising; limit (e) says what that costs (R3-ADV-9; INFORM 20).**
- `_GuardedStream.fileno()` still raises `io.UnsupportedOperation` (D12). It fails closed, and no code is added.
- **Limit (e) gains:** "During the tick, a dependency that calls `faulthandler.enable()` with its default file (`sys.stderr`), or that passes `sys.stderr` or `sys.stdout` to a subprocess, gets `io.UnsupportedOperation`. The step then fails (exit 1) instead of running. Nothing leaks."
- **Evidence (new line for the runner):** `grep -rn -E "faulthandler\.enable|stderr\.fileno|stdout\.fileno|stderr=sys\.stderr|stdout=sys\.stdout"` over the installed pinned packages that the tick imports (psycopg, anthropic, boto3/botocore, the azure and google packages, httpx). The runner pastes the hits.
- If a hit runs during the tick, the builder stops and writes the question to `questions-for-lead.md`, with the option of making `fileno()` return the redirected fd at process entry. That fd points at the null device. UNVERIFIED until the grep runs.

**BN-12. Warnings shown with an explicit file (R3-ADV-10).**
- **Limit (i) gains:** "A library that calls `warnings.showwarning(..., file=<stream>)` with an explicit file is not covered by `captureWarnings`. The standard library passes that call to the original function, which writes the raw text to that file (`logging/__init__.py:2311-2313`)."
  - During the tick, that text meets the stream guard or the null device.
  - During a non-tick command, it reaches the terminal raw.
- The owner-visible entry for limit (i) in BN-15 includes this.

**BN-13. Test hygiene and missing recipes (R3-ADV-11, R3-COR-8).**
- **U7:** the level name is changed with `monkeypatch.setitem(logging._levelToName, 30, <canary>)` and `monkeypatch.setitem(logging._nameToLevel, <canary>, 30)`, not with `logging.addLevelName`, so pytest undoes it after the test. `record.levelname` reads the same table, so the test still checks the same thing.
- **S6 case ids (fixed; the builder keeps them):** `exit_3`, `none_payload`, `canary_payload`, `false_payload`, `base_exception`, `interrupt_in_main`, `interrupt_during_import`. These match K23 (`canary_payload`), K49 (`false_payload`), K57 (`interrupt_during_import`) and K24's note (`interrupt_in_main`).
- **U21:** `monkeypatch.setattr(cli, "_tick", lambda: 0)` and `monkeypatch.setattr(cli, "load_config", <stub that raises a test-local _Reached>)`.
  - So `tick` and `--conf DIR tick` return 0 without running a real tick.
  - `--config tick audit verify` and `--config=tick gate a` stop at `load_config` (`cli.py:136`; `main()` maps `_Reached` to exit 3).
  - The row asserts only the recorder's calls.
- **S4 recipe:** the helper uses S2's valid made-up config folder with the same fake-secret patch. Inside the child, before `cli_entry`, it patches two things:
  - `hadavin_sdk.evals.gate`, with a made-up function. It logs the canary on `logging.getLogger("vendorlib")` at WARNING and calls `warnings.warn(<canary>)`. Then it returns a `types.SimpleNamespace` with the fields that `cli.py:153-162` reads: `agent_id`, `n=1`, `k=1`, `passed=0`, `pass_rate=0.0`, `threshold`, `green=False`, `pass_k`, `abstain_rate`, `upper_error_bound`;
  - `hadavin_sdk.cli.make`, with a function that returns a placeholder, so that no llm or secrets backend is built.
- The agent id is one that the made-up registry holds; the builder names it from the fixture. The expected exit code is 1 (`cli.py:163`). `test_s4_stdout_kept` compares stdout with the exact result line that those fields give.

**BN-14. K9 is killed by the positive assertion (R3-COR-3).**
- `test_u11_warning_from_made_up_module` first asserts that the line exists: `assert re.search(r"^logger=py\.warnings level=WARNING msg_len=\d+$", err, re.M), "py.warnings line missing"`. Then it checks that the canary is absent.
- K9's `expect` becomes `py.warnings line missing`. Under pytest, the mutant's warning is recorded by pytest's own `catch_warnings` and not printed, so the negative assertion alone would let it survive.
- `N` is the real length of the formatted warning (F3; R3-COR-7 contested). The row does not pin a number.

**BN-15. P5b3 revision 3 and the limits file (R3-COR-4; NEEDS LEAD 17).**
- **Depends on** reads: "`tickets/P5b3.md` revision 3 (on disk; the input to P5b3's round 3)". The UNVERIFIED line on P5b3 reads: "P5b3's final interface: revision 3 on disk; its round 3 has not run yet".
- **Couplings (1) to (3) still hold** against P5b3 revision 3 (F6: `:108`, `:193`, `:604` `handle.emit`; `:635` the `run_tick` move; `:31`, `:612` `P5b4.md:414-419`). Relay them to P5b3's round 3 resolve or its build notes.
- **Couplings (4)** reads: "`handover/owner-visible-limits.md` exists (P5b3 wrote entry 1). P5b4 adds nothing to it in the pull request. The lead appends P5b4's six limits as separate numbered entries, in the file's own format."
- **Done** reads: "P5b4's six entries are in `handover/owner-visible-limits.md`".
- **PENDING LEAD 17** reads as in the PENDING LEAD section below.
- **Draft entries for the lead to append**, numbered with the next free numbers when appended (2 to 7 if nothing else was appended first; P6a's and P6b2's entries may come first). Each entry gets the file's "Added <date, UTC and IST>" line when it is appended.

  > ## N. Starting the program the wrong way lets library start-up text through
  > - **What can go wrong.** If the program is started with `python -m hadavin_sdk.cli` instead of the `hadavin-sdk` command, any text a library prints while the program is loading reaches the screen or the log unchanged. Such text can hold a customer's name or part of a secret.
  > - **What the program checks.** Started with the `hadavin-sdk` command, the log filter is in place before any library is loaded.
  > - **What it does not check.** It does not notice, and does not warn, when it was started the other way.
  > - **What a person must do, and when.** Before the first pilot, the person who sets up the scheduler and the run scripts checks that they call `hadavin-sdk`, never `python -m hadavin_sdk.cli`.
  > - Studio reference: package P5b4, limit (b), PENDING LEAD 17, lead order 24 item 39.

  > ## N. During a background run, a library's own log file or log sender can receive its messages for a short time
  > - **What can go wrong.** If a library sets up its own log file or its own network log sender in the middle of a step of the background run, its messages, which can hold customer data, go there until the end of that step.
  > - **What the program checks.** At four points in every background run it looks for log outputs it did not set up, writes one line naming each kind, and removes it.
  > - **What it does not check.** It does not look between those points, so messages sent there in between are not taken back.
  > - **What a person must do, and when.** Before the first pilot, a person checks the pinned libraries (database, model and cloud libraries) for code that adds its own log output while it runs, and tells the lead about any that does. During the pilot, a person reads the `foreign_handler` lines in the run log once a day and tells the lead about any new one.
  > - Studio reference: package P5b4, limit (c), v1.1 row V-OG-3, PENDING LEAD 4 and 17.

  > ## N. During a command run by hand, a library's own log output can print until the command ends
  > - **What can go wrong.** During a command run by hand (not the background run), a library that sets up its own log output while the command runs can print its messages, which can hold customer data, until the command ends.
  > - **What the program checks.** At the end of every command it reports any log output it did not set up (a `foreign_handler` line).
  > - **What it does not check.** It cannot take back what was already printed.
  > - **What a person must do, and when.** During the pilot, whoever runs a command by hand reads its last lines. If a `foreign_handler` line appears, they treat the screen or log of that run as possibly holding customer data and tell the lead.
  > - Studio reference: package P5b4, limit (d), v1.1 row V-OG-3, PENDING LEAD 17.

  > ## N. During a background run, text a library prints while the program loads is not filtered
  > - **What can go wrong.** The program learns that it is doing a background run only after it has loaded its parts. Anything a library prints directly while loading goes into the run log unchanged.
  > - **What the program checks.** Log messages, warnings and crash reports are filtered from the very start. No configuration or customer document has been read at that moment.
  > - **What it does not check.** It does not filter direct printing during loading.
  > - **What a person must do, and when.** Before the first pilot, a person checks the pinned libraries for printing at load time and tells the lead about any that does. The lead then orders the small separate start-up module (v1.1 row V-OG-6).
  > - Studio reference: package P5b4, limit (g), v1.1 row V-OG-6, PENDING LEAD 13 and 17, lead order 24 item 37.

  > ## N. A library that names its log like ours can print messages that look like ours
  > - **What can go wrong.** Our filter trusts a log whose name starts with `hadavin_sdk.`. A library that gives its log such a name has its messages printed when they are built like ours, and such a message can carry customer data.
  > - **What the program checks.** Even then, only messages made of plain text and numbers are printed. Anything else is replaced by its length.
  > - **What it does not check.** Whether the code that wrote the message is really ours.
  > - **What a person must do, and when.** Before the first pilot, and whenever a pinned library is upgraded, a person searches that library for the name `hadavin_sdk` and tells the lead about any hit.
  > - Studio reference: package P5b4, limit (h), v1.1 row V-OG-9, PENDING LEAD 17.

  > ## N. During a command run by hand, text a library prints directly reaches the screen
  > - **What can go wrong.** During a command run by hand (not the background run), text that a library prints directly, crash text it prints itself, a warning it shows into a named output, or text written by code in C reaches the screen unchanged. If such a command is started by a scheduler, that text lands in the scheduler's log.
  > - **What the program checks.** Log messages, ordinary warnings and crash reports are filtered for these commands too.
  > - **What it does not check.** Direct printing, warnings shown into a named output, and writes from C code during these commands.
  > - **What a person must do, and when.** During the pilot, only the background run is started by a scheduler. Before any other command is scheduled, a person tells the lead, who orders the filter for that command (v1.1 row V-OG-8).
  > - Studio reference: package P5b4, limit (i) with BN-12, v1.1 row V-OG-8, PENDING LEAD 17.

**BN-16. Small cites, marks and counts (R3-COR-5, R3-COR-9, R3-ADV-12, R3-COR-10, R3-COR-11).**
- Line 122 reads "grep finds 25 own logger calls in `src/` on this tree (24 match `_LOG.<level>(`; one is `k1b/loop.py:100`, `logging.getLogger(__name__).warning(`), and 24 after P5b3 deletes `approvals/receiver.py:63`".
- K19, K20 and K40 (their only killers are S1's `os.write` channels) are marked "POSIX-only?", like K34, K36, K43, K52 and K61. The Windows paragraph's candidate list gains "S1's `fd1` and `fd2` channels and its heartbeat row".
- The count sentence reads "The killers are 74 distinct pytest ids, one per run (each K13 entry is its own case)". The count of function names is not stated.
- "Looked at and NOT reused" reads "`guard/runmap.py:485` `safe_head`".

**BN-17. Mutant table delta and totals (one place for the builder).**
- **Added:** K62 (BN-8), K63 (BN-1), K64 (BN-2), K65 (BN-5), K66 (BN-10).
- **Changed:**
  - K8: killer recipe (BN-4);
  - K9: `expect` is `py.warnings line missing` (BN-14);
  - K13: 9 entries, with the root-level entry removed (BN-2, BN-3);
  - K24: its note names S6 `interrupt_in_main` (BN-13);
  - K39: new `only_test` and `expect` (BN-6);
  - K19, K20 and K40: marked POSIX-only? (BN-16).
- **Totals:**
  - 68 table rows, of which K7 and K29 are withdrawn, giving **66 active mutants**;
  - **74 runs** (66 - 1 + 9), with 74 distinct killer ids;
  - the arithmetic from revision 3 is 61 + 5 = 66 active, and 70 - 1 (the root-level K13 entry) + 5 = 74 runs.
- **Test rows:** still 36 automated rows, plus S5, plus R14. New test functions sit inside existing rows: U1 (+1), U9 (iii), U14 (+1), U25 (+1), U28 (i) (renamed), U29 (iii) (in process) and S8 (+1).
- Done's "61 mutants, 70 runs" reads "66 mutants, 74 runs".

## Positions
- **BN-2 cuts surface instead of adding a row (order 8).**
  - It deletes the library-mode root-level change and its restore. That closes R3-COR-6 and the root-level half of R3-ADV-2 and R3-COR-2, and removes one equivalent K13 entry.
  - The cost: an embedder or a test must set root to INFO to see the heartbeat in library mode. No existing test depends on that, because the old tick's `basicConfig` already does nothing under pytest (F2).
  - The only new test (K64) pins the cut.
- **BN-5 takes the one-lock form.** A lock seam (ADV-5's first option) or a second lock would add interface. One lock plus "no logging call under it" removes our own lock pair.
  - The residual (PENDING LEAD 21) is the pattern stock `logging` already has, and it can cause a hang, not a leak.
  - A non-blocking write with a timeout would close it, but it would drop lines and need a new threshold from config. That is not worth it before a hang is seen.
- **BN-11 keeps `fileno()` raising.** A fileno that points at the null device only at process entry would be new code with a mode split, for a need that no grep has shown yet. The builder's grep decides, and the builder asks the lead if a hit appears.
- **Five mutants are added (BN-1, 2, 5, 8, 10)** because each build note adds or cuts a rule. That follows the revision 3 precedent (R3-AUTH-1: every rule gets a mutant). BN-9's rule gets a test and no mutant, with the reason stated.
- **R3-COR-7 is contested on a cite a reader can open** (`logging/__init__.py:2317` on 3.13.18). The contest does not cover 3.12 (Honest note).

## Couplings
- **BN-1 and BN-6:** K39's killer relies on the guard writing to the sink while it holds the lock, which BN-1 makes explicit. BN-5's "uninstall holds the lock for the stream part" keeps that wait in place.
- **BN-2 and R14 / P5b1:** R14 now sets root with `caplog.set_level(logging.DEBUG)`. P5b1's R14 text needs no edit, because P5b4 changes that file in its own pull request (Files).
- **BN-2 and U1/U28/U2/U27:** each sets its own root level through `caplog`. The old "both levels popped, all 10 globals back" reads "all 9 globals back".
- **BN-5 and K58/U29:** K58 (a plain `Lock`) still fails U29 (i) and (ii) in the child. K65 is separate and is killed in process.
- **BN-7 and evidence item 6:** the shim file `handover/evidence/P5b4/shim-output_guard.py` follows BN-7. The runner pastes R14's failing canary assertion.
- **BN-15 and P5b3:** Couplings (1) to (3) are relayed to P5b3's round 3. P5b3's text is not edited here.
- **BN-15 and the limits file:** P6a (order 27 item 50) and P6b2 (its resolve, owner-visible line 4) may append first. The lead numbers P5b4's entries when it appends them.
- **P5b5 (information only):** P5b5's build note on fd 2 relies on P5b4 sending fd 2 to the null device at the process-entry tick. That is unchanged.

## PENDING LEAD (continuing the ticket's numbering after 17)
Routing rule: an item that touches an owner hard rule (least privilege, thresholds, money, redaction) is NEEDS LEAD. Everything else is INFORM, and the builder takes the recommendation meanwhile.
- **17 (updated, NEEDS LEAD, redaction: owner-visible limits; BN-15, BN-12).** `handover/owner-visible-limits.md` exists. Recommend: the lead appends the six drafted entries (limits (b), (c), (d), (g), (h), and (i) with the explicit-file warnings) as separate numbered entries, before any pilot, and shows them to the owner. The "what a person must do" lines are my proposals. Reversible: the entries can be reworded at any time.
- **18. NEW, INFORM. Freeze with build notes, no round 4.** Round 3 had 7 Majors (6 distinct). Recommend: yes, per order 20 item 6. The banner goes under the status line, and the build-start review reads the ticket plus this file.
- **19. NEW, INFORM. Library mode never touches the root level (BN-2, a cut).** Recommend: accept. The embedder's level is respected, there is one restore path fewer, and K13 has 9 entries. Cost: the heartbeat is not printed in library mode unless the caller sets root to INFO. Confidence 80 percent. Reversible by one edit before the merge.
- **20. NEW, INFORM. `fileno()` keeps raising (BN-11).** Recommend: accept, with the grep in evidence. If a pinned dependency calls `faulthandler.enable()` or passes `sys.stderr` on during the tick, the builder asks before changing it. This is not a redaction change: it fails closed.
- **21. NEW, INFORM. Residual hang from finalizers across two locks (BN-5).** Recommend: accept for v1, with a new v1.1 row **V-OG-10**: a writer that never blocks (try-acquire with a timeout taken from config) if a tick hang is ever seen with both locks held in a stack dump. No leak is possible from it. A timeout value would be a threshold, so choosing (b) now would turn this into a NEEDS LEAD.

## Counts
- Finding ids: 23 (ADV 12, COR 11). Majors 7 (ADV-1 to ADV-5, COR-1, COR-2; ADV-2 and COR-2 are one defect). Minors 12. Nits 4. No Blocker. No severity changed.
- PROPOSE FIX 22:
  - ADV-1 to ADV-12;
  - COR-1 to COR-6 and COR-8 to COR-11.
  - Two of them are surface cuts (BN-2: ADV-2/COR-2 root half and COR-6; BN-6: no lock seam for ADV-5).
- CONTEST 1 (COR-7). DECLINE 0. ESCALATE 0.
- Own findings: 1 (N1, in BN-5).
- Build notes: 17 (BN-1 to BN-17; BN-17 is the table delta).
- Mutants after the notes: 68 table rows, 66 active, 74 runs. Automated rows: 36 (unchanged).
- PENDING LEAD: 1 updated (17, NEEDS LEAD) and 4 new (18 to 21, INFORM).
- Owner-visible entries drafted: 6 (BN-15), for the lead to append.
- Fixes applied to the ticket in this step: 0 (they are build notes). Remaining unaddressed findings: 0.
