# TICKET E: test helpers (crash-point hook) for steps D, F, H

Session core-a (DOOR). Written 2026-11-20 from origin/main 51c9fc4fb (S = src/hadavin_sdk). Nothing was run for this ticket: no test, no build, no network. Every code claim carries a file:line opened in this run; the rest is marked UNVERIFIED. Scale of the rung table: 1 to 5 of 2026-11-06 (TICKET-TEMPLATE.md:20).

- Package id and name: E, test helpers (plan-v4-final.md:12).
- Path class: other (test tooling). Extended review: no. Ticket review: none (plan-v4-final.md:12, ORDERS.md:49).
- Depends on (merged first): nothing. Delivered first so that D and F carry their own proving tests (plan-v3.md:26).
- Source of the code: idea and one-shot flag rule from inputs/demo-hooks.py:29-50 and inputs/demo-crash_launcher.py:1-13. NOT taken: the demo point names (demo-hooks.py:12-20, project words), the sqlite argument (demo-hooks.py:24), the `Hooks` class name (taken already by S/runtime/agent_loop.py:172), `trace.CrashWindows` (inventory-promote.md:11; not in the inputs folder, NOT READ).

## 1. PURPOSE (plain words)
The core promises that a run which dies half-way is never done twice and ends as NEEDS_PERSON: acknowledged, then NEEDS_PERSON with no notification and no stored document; the sender must poll the run state. To prove that, a test must be able to stop the program at an exact place, for example "after the run row was written, before the model was called", and then look at what is left. Today no test can do that: tests only write an old row by hand and let the clean-up step find it (tests/test_p7_tick.py:216-232). This ticket adds one small test-only tool that wraps an object the test already hands to the runtime (the store, the model double) and, when the test has armed a named point, either raises a special error (same process) or kills the process (child process, for real PostgreSQL). It changes no existing file and no runtime code.

## 2. RIGHT-SIZE and NEEDED-CHECK
RIGHT-SIZE: new shipping code, small and test-only (crash.py is 295 lines as built, wc -l 2026-11-20; the first estimate was about 110), but it is the proof tool of two guarantee-class steps (D door, F money), so it gets its own tests; no mutation run, no review round.
ONE-PLACE-PER-JOB: "stop the program at a named place" lives ONLY in `hadavin_sdk.testing.crash`. Steps D, F, H and the other sessions import it; none writes its own kill switch, flag file or exit code.

NEEDED-CHECK per proposed helper (what I read, then the verdict):
| Helper | Exists already? | pytest / pinned dependency / stdlib does it? | Needed by which named test | Verdict |
|---|---|---|---|---|
| `CrashPoints` with `wrap` (boundary proxy) and `SimulatedCrash` (same-process mode) | No. grep of `crash_point`, `os._exit` over src, tests, tools: no hit. `Runtime` has no crash hook: its `Hooks` holds only collaborators (S/runtime/agent_loop.py:172-191). | `monkeypatch.setattr` can make one method raise, but has no "nth call", no before/after, no one-shot rule and cannot cross a process. An ordinary exception does not work: the runtime catches `Exception` at 20 places (S/runtime/agent_loop.py:247, 293, 307, 409, 421, 425, ...) and `ProviderError` around the model call (S/runtime/agent_loop.py:477-483), so the error must be a `BaseException`; nothing in S/runtime catches that (grep in this run: runtime has no `BaseException`). | D: "a kill during the run (step E crash hook) then a tick -> NEEDS_PERSON interrupted, a repeat gives 200 with that state and no re-run", on memory and Postgres (draft-tickets-C-D.md:30). F: abandoned call between reserve and settle (plan-v3.md:37). T2 crash points (plan-v3.md:22). | NEEDED |
| Flag-file kill mode (`mode="exit"`) | No (same grep). | stdlib `os._exit` is the kill; the one-shot flag and the point match are ours (rule taken from demo-hooks.py:38-50). | D's same case on Postgres: the memory store dies with the process (S/store/memory.py:28-43), so a real kill only makes sense there. A's "test crosses a process boundary" may use it (plan-v4-final.md:8). | NEEDED |
| Socket guard | No. tests/conftest.py:14-36 only removes cloud credentials; S/guard/http.py:162-183 is the product's egress check, not a test guard. | pytest-socket would do it (not pinned: no hit in pyproject.toml or uv.lock). | None. Lead verdict ORDER 006 item 7: write it only if a named test of step D needs it. D's test list (draft-tickets-C-D.md:30) talks to loopback wsgiref only and names no "no outside network" case. | NOT-NEEDED this step: CUT (trigger in section 11) |
| Child-process launcher helper | No. | stdlib `subprocess.run` in 4 lines; and subprocess inside S would trip ruff S603 and bandit (pyproject.toml:72; ci.yml:181). | D and F each need their own child (it must build their own app). | TOOL-COULD-DO: CUT, recipe in section 5 |
| Scripted model double | YES: tests/k5_support.py:129-161, tests/k1b_support.py:17. | n/a | n/a | DUPLICATE: reuse |
| Runtime builder | YES: tests/k5_support.py:165-215. | n/a | n/a | DUPLICATE: reuse |
| PostgreSQL schema fixture | YES: tests/contracts/kinds/store_postgres.py:14-25 (needs HADAVIN_TEST_PG_DSN, else skip). | n/a | n/a | DUPLICATE: reuse |
| Clock helper for "replay after 6 minutes" | Not needed: `run_tick(app, now=...)` takes the time (S/runtime/tick.py:335) and D's `make_wsgi(..., clock=time.time)` takes a clock (draft-tickets-C-D.md:27). | n/a | n/a | NOT-NEEDED |
| pytest fixture wrapper for `CrashPoints` | No. | A `with` block is enough; pytest is only in the dev group (pyproject.toml:50), so a module under S must not import it. | none | NOT-NEEDED |

RUNG TABLE (CODE-LAST v1)
| Component | Need | Rung tried | Evidence (source, date) or UNVERIFIED | What only our code gives | Verdict |
|---|---|---|---|---|---|
| Crash at a named boundary, same process | leave a run row exactly as a crash would | 1 n/a (a test tool, no client tool does it); 2 own core: none (agent_loop.py:172-191, test_p7_tick.py:216-232; read 2026-11-20); 3 pytest monkeypatch covers one raising method, about half the need; 4 a fault-injection library: UNVERIFIED (no network in this run; would be a new dependency) | read of the files named, 2026-11-20 | one-shot, nth call, before/after, an error the runtime cannot swallow, the same point names in both modes | KEEP-CODE (thin) |
| Kill of a child process at the same boundary | prove the guarantee on real PostgreSQL | 3 stdlib `os._exit` + `subprocess` give the kill, not the "where" | demo-hooks.py:38-50 (works in the demo per its docstring; UNVERIFIED here) | point match and one-shot flag shared with the same-process mode | KEEP-CODE (about 25 lines of the same class) |
| Socket guard | none named | 4 pytest-socket (UNVERIFIED version and licence) | ORDER 006 item 7 | nothing proven | CUT |
| Launcher helper, clock helper, fixture wrapper, model double, runtime builder, schema fixture | see above | 2 and 3 | lines in the table above | nothing | CUT |

## 3. INVARIANTS
1. E changes no existing file. `S/testing/__init__.py` and `S/testing/mutation.py` stay byte-identical: their hashes are pinned (tests/fixtures/mutation_manifest.json:4-5; tests/test_mutation_runner.py:1534-1553) and the lead forbade it (ORDER 006 item 10).
2. No module of S outside `S/testing/` imports `hadavin_sdk.testing.crash`. The helper ships in the wheel (section 4) but is dead code at run time; a test in this ticket scans for it.
3. A `CrashPoints` object cannot be built outside a pytest run: the constructor raises `RuntimeError` unless the environment variable `PYTEST_CURRENT_TEST` is set (pytest sets it per test and a child process inherits it; UNVERIFIED in this run, pinned by test H1).
4. Nothing fires unless a test armed that exact point. Unarmed, a wrapped object behaves as the target: same results, same exceptions, a missing attribute raises `AttributeError` (so the `getattr(..., None)` guard of S/runtime/tick.py:179 still works).
5. One arm, one crash: the point is disarmed (memory) or its flag file deleted BEFORE the crash; if another thread took it, no crash (demo-hooks.py:45-48). As built, a delete that is refused (for example by Windows while the file is open) is retried 20 times with 20 ms between tries (crash.py:75-76, `_disarm` 272-281); only when all tries fail is there no crash.
6. `SimulatedCrash` derives from `BaseException`, never from `Exception`.
7. Kill mode ends the process with `os._exit(CRASH_EXIT_CODE)` after writing `CRASH_MARKER` with `os.write` on descriptor 1 in a `try`/`finally` followed by `os._exit`: no `finally`, no `atexit`, no buffered write runs.
8. A point left armed at the end of the `with` block is an error (`RuntimeError` naming the point) and is disarmed all the same, so one test cannot crash the next. As built, a flag file that still cannot be deleted at that point raises a second, different `RuntimeError` ("the flag file could not be deleted"), a flag that is a directory counts as not armed (on Windows its read raises PermissionError, still not armed), a flag that vanished between the look and our delete (a child fired it) is not reported as never fired, and with an error already in flight `__exit__` raises nothing (crash.py:148-160).
9. Point names are generic: `<name>.<method>:before` or `:after`, where name and method match `[a-z_][a-z0-9_]*`. No project word, no stage name. The helper has no stage parameter.
10. No new dependency, no pytest import in S, absolute imports only, no dynamic import, no secret and no credential of any kind, no host name or URL even in a docstring (the scans of section 4 read docstrings).
11. The module never contains a literal call of an attribute named `chat` or `apply_guardrail`; calls go through `getattr(target, method)(...)` (see guard G4 in section 4).

## 4. FILES
Create (all new, ours):
- `src/hadavin_sdk/testing/crash.py` (295 lines, wc -l 2026-11-20; planned about 110): the helper.
- `tests/test_testing_crash.py` (1030 lines with 44 test functions, wc -l and grep 2026-11-20; planned about 190): its tests (flat name, like tests/test_mutation_runner.py:25 for the sibling module). The child script of the kill-mode tests is written into `tmp_path` by the test; no second file.
Modify: none by us. REQUESTS TO core-b: none required. One optional request at landing: R1 `CHANGELOG.md`, in the entry of the D+E group (plan-v4-final.md:19), one line "`hadavin_sdk.testing.crash`: test-only crash points (in the wheel, not used at run time)"; reason: CHANGELOG.md:347 already tells readers what of `testing` is in the wheel, and CHANGELOG is core-b's (plan-v3.md:6). NOT requested: any change to tests/conftest.py, pyproject.toml, uv.lock, guard lists.
Delete: none.

Where the helper lives, with evidence. Decision: `src/hadavin_sdk/testing/`.
- Plan: "DOOR = core-a owns only NEW files: ... `testing/` helpers" (plan-v3.md:8); "`testing/` helpers" (plan-v2.md:29); "Crash-point test harness into `hadavin_sdk.testing`" (inventory-promote.md:11); "test-only, not public API" (plan-v2.md:22; plan-v4-final.md:12). Lead: new files there are allowed (ORDER 006 item 10).
- The package exists and says what it is for: "Test and review tooling shipped with the SDK (not used at run time)" (S/testing/__init__.py:1). `tests/` and `tools/` already import from it (tests/test_mutation_runner.py:25-26; tools/mutation_runner.py:69).
- Wheel: build backend `uv_build` with no include or exclude setting (pyproject.toml:56-58, whole file read), so every file under src/hadavin_sdk ships; that the new file lands in the wheel is UNVERIFIED (no build run). "Not public API" is kept by: no export from any `__init__`, a docstring that says so, invariants 2 and 3.
- The other choice, `tests/` (like tests/k5_support.py), was weighed in section 10.

Guard tests the new file must pass (none needs a change; the builder runs these six files too):
- G1 tests/test_mutation_runner.py:1534-1553: hashes of `testing/__init__.py` and `mutation.py`, and the manifest KEY set (not a folder listing), so a new file is fine and an edit of `__init__.py` is red.
- G2 tests/test_lockin_guard.py:118-133: relative import or `import_module`/`__import__` in S is refused; :520-536 and :599: vendor-looking text in string constants (a 12-digit number, a region shape, a vendor name) is refused.
- G3 tests/test_no_hardcoded_values.py:22-39, 64-87: key-shaped strings, URLs and host names in ANY string constant of S, docstrings included.
- G4 tests/test_k5_producers.py:22, 79-106: a module of S with a call `x.chat(...)` or `x.apply_guardrail(...)` must be a registered model caller (S/guard/producers.py:55); invariant 11 keeps us out. Same file :122: no `str(x)[:N]` cut.
- G5 tests/test_repo_rules.py:48-62, 123-124: S never imports `tests` or `demos`.
- G6 tests/test_stage_names.py:33, 447, 518: the old first stage word must not appear in a stage position in src or tests.
- Also read, not touched by us: tests/test_k1b_redaction_layers.py:133-155 (do not name a function `redact`); tests/test_k5_round11.py:113-123, 137-149.
No test pins the wheel's file list or the module list of S (grep for wheel, RECORD, namelist, iter_modules over tests: only the pglast guard, tests/test_no_pglast_in_runtime.py).

## 5. SIGNATURES and usage
```python
# src/hadavin_sdk/testing/crash.py   (stdlib only: functools, inspect, os, re, threading, time, pathlib, typing, collections.abc)
CRASH_EXIT_CODE: Final[int] = 137
CRASH_MARKER: Final[str] = "simulate crash"
Mode = Literal["raise", "exit"]


class SimulatedCrash(BaseException):
    point: str

    def __init__(self, point: str) -> None: ...


class CrashPoints:
    def __init__(self, *, mode: Mode = "raise", flag_path: Path | None = None) -> None:
        ...
        # RuntimeError outside pytest; ValueError if mode is unknown, or "exit" without flag_path, or "raise" with one;
        # TypeError if flag_path is not a pathlib.Path (crash.py:132-133)

    def __enter__(self) -> "CrashPoints": ...
    def __exit__(
        self, exc_type, exc, tb
    ) -> None: ...  # disarms; RuntimeError if still armed and no error in flight, or if the flag file cannot be deleted (crash.py:148-160)
    def arm(
        self, point: str, *, nth: int = 1
    ) -> None: ...  # ValueError: bad name, nth < 1 or at least 10**9, or already armed; TypeError: nth is a bool (crash.py:174-176)
    def armed(self) -> str | None: ...  # "store.create_run:after" or None
    def hit(
        self, point: str
    ) -> (
        None
    ): ...  # one-shot: raise SimulatedCrash, or write the marker with os.write(1, ...) and os._exit
    def wrap[T](self, target: T, name: str, methods: Collection[str]) -> T:
        ...
        # proxy: hit("<name>.<m>:before"), call, hit("<name>.<m>:after"); AttributeError if target lacks m;
        # TypeError for a dunder, coroutine, async-generator or generator method, or a non-callable (crash.py:232-242);
        # each word of a name or point is at most 60 characters (crash.py:70)

    @property
    def fired(self) -> tuple[str, ...]: ...  # points that fired in this process, in order
```
Flag file (kill mode): one UTF-8 line `<point>` or `<point>#<nth>`; `arm` writes it, `hit` reads it on every call, counts matching calls in the process, deletes it, then exits. An unreadable or missing file means "not armed".

Usage 1, same process, memory store (D's case on memory; `ScriptLLM`, `build_runtime`, `handle` from tests/k5_support.py:129, 165, 218):
```python
with CrashPoints() as cp:
    rt, _ = build_runtime(cfg_dir, cp.wrap(ScriptLLM([{"noaction": True}]), "llm", ["chat"]))
    cp.arm("llm.chat:before")
    with pytest.raises(SimulatedCrash):
        handle(rt, run_id=RID)  # the row stays WORKING; then run the tick
```
Usage 2, wrap the store after the app is built (the chain audit factory type-checks the store, S/audit/chain.py:520-525, so wrap afterwards; `Runtime.store` is a plain attribute, S/runtime/agent_loop.py:208):
```python
rt.store = cp.wrap(rt.store, "store", ["create_run", "transition"])
cp.arm("store.transition:after", nth=1)  # RECEIVED -> WORKING is written, nothing after it
with pytest.raises(SimulatedCrash):
    handle(rt, run_id=RID)
```
Usage 3, kill a child on PostgreSQL (the child script is the consumer's; it builds its app, wraps with `CrashPoints(mode="exit", flag_path=Path(sys.argv[1]))` and serves):
```python
CrashPoints(mode="exit", flag_path=flag).arm("store.create_run:after")
done = subprocess.run(
    [sys.executable, str(child), str(flag)], capture_output=True, text=True, timeout=60
)
assert done.returncode == CRASH_EXIT_CODE and CRASH_MARKER in done.stdout and not flag.exists()
```

## 6. MIGRATION NEED
None. No table, no store method, no grant, no config field.

## 7. INTERFACES
Offered by E:
- To step D (ours; decided shape: ONE process with endpoint and worker, ack once the run row exists, no new table, POST /v1/trigger with headers X-Hadavin-Request-Timestamp and X-Hadavin-Signature; draft-tickets-C-D.md:24, 28): the three points D's tests need. `store.create_run:before` = no row, so no ack (D invariants 7 and 11); `store.create_run:after` = row exists, ack may go out, run never continues; `llm.chat:before` = run is WORKING, no model call made (this was the third point when E was written; D ticket section 9 now uses `store.touch:before`, the run is WORKING at its first heartbeat, agent_loop.py:468, and also `store.get_run:after`; `llm.chat:before` is still a valid point of the helper, Usage 1 below). After each, D runs `run_tick(app, now=later)` and expects NEEDS_PERSON "interrupted" (S/runtime/tick.py:112-145), then repeats the signed request and expects 200, that state, zero model calls. The helper knows nothing about HTTP, headers or signing.
- To step F (core-b builds, core-c writes the wrapper body; plan-v4-final.md:13): `wrap(store, "store", [<reserve and settle method names>])` gives "crash between reserve and settle" without touching the gate; names come from core-b's interface ticket (ii).
- To step A (core-b): kill mode can be the "test crosses a process boundary" (plan-v4-final.md:8), if core-b wants it.
- To step H (only if proven; the draft says cut, draft-tickets-C-D.md:5): the same `wrap` on any new store method.
- To core-c (step G): nothing needed.
Needed by E: nothing from core-b or core-c. From step D's own code: the worker must be buildable from already-built objects (`Runner(runtime, store, ...)`, draft-tickets-C-D.md:27), so a test launcher can wrap them; `python -m hadavin_sdk.triggers.worker` itself never imports the helper (invariant 2).
No interface ticket for the crash hook (dropped as ceremony, plan-v4-final.md:18).

## 8. TEST CASES for the helper (tests/test_testing_crash.py)
(Planned list. The built file has 44 test functions in 1030 lines, wc -l and grep 2026-11-20, and also tests the behaviour added later: delete retries, a stuck flag, type errors for `flag_path`, `nth` and `wrap`.) All run on the memory store or with plain objects in this box, except P1. Normal:
- N1 unarmed wrap of a `MemoryStore`: create_run then get_run return the same run as unwrapped; `fired == ()`.
- N2 arm `store.create_run:before`: SimulatedCrash, the store holds no run. N3 arm `:after`: SimulatedCrash, the run is there.
- N4 one-shot: the second call of the same method passes; `fired` has one entry.
- N5 `nth=2`: first call passes, second crashes.
- N6 through the real runtime: Usage 1 leaves the run in state WORKING (not NEEDS_PERSON, which is what an ordinary exception from the model would give, S/runtime/agent_loop.py:477-483); `pytest.raises(Exception)` does NOT catch SimulatedCrash.
- N7 kill mode: a child written to tmp_path wraps a small object, parent arms, child exits with CRASH_EXIT_CODE, prints the marker, the flag is gone, a line the child would print in a `finally` block is absent; a second start of the same child ends with exit 0.
Edge:
- E1 a method not in `methods` is passed through untouched; a non-callable attribute too; `getattr(proxy, "nope", None)` is None.
- E2 the target's own exception passes through unchanged and `:after` does not fire for that call.
- E3 two threads hit the armed point at once: exactly one crashes (both modes; kill mode checked with two child threads and one flag).
- E4 `SimulatedCrash` inside a `ThreadPoolExecutor` task lands in the future and the pool keeps working (D runs handle in a pool; UNVERIFIED until this test runs).
- E5 arm twice without a hit: ValueError. E6 kill mode with a missing, empty or garbage flag file: no crash, no error.
Hostile:
- H1 built with `PYTEST_CURRENT_TEST` removed (monkeypatch.delenv): RuntimeError; same in a child started with that variable stripped: it must not be able to kill itself.
- H2 left armed: leaving the `with` block raises RuntimeError naming the point; the next `hit` of that point does nothing; in kill mode the flag file is deleted.
- H3 bad names refused at `arm`: empty, upper case, a path, `..`, a newline, a name with `#`, 300 characters; `wrap` with a method the target lacks: AttributeError at wrap time.
- H4 a flag file holding another point, or `point#0`, `point#-1`, `point#x`: never fires.
- H5 class test of invariant 2: no file under S outside `testing/` has an import whose module starts with `hadavin_sdk.testing.crash` (own 10-line AST scan; not imported from another test file, rule of tests/fixtures/timing.py:1); a planted file in tmp_path is caught.
- H6 class test of invariant 11 and G3 on our own file: no `chat` attribute call, no URL-shaped constant.
Needs real PostgreSQL 16 (lead, laptop; skipped here without HADAVIN_TEST_PG_DSN, tests/contracts/kinds/store_postgres.py:22-24):
- P1 kill mode with a child that opens the postgres store on a fresh schema and is killed at `store.create_run:after`: the parent reads the row afterwards (each statement commits at once, S/store/postgres.py:146); at `:before` the row is absent.
FAIL-BEFORE: N6 is the behaviour no existing test can show. Mutants (hand list, for the confirming run): drop the disarm before the crash (N4 kills it); derive SimulatedCrash from Exception (N6); drop the pytest gate (H1); swap before and after (N2, N3).

## 9. BUILD NOTES
- Branch: `cloud/core-a`, in separate commits that touch only src/ and tests/, message starting `code E:` (ORDERS.md:59, ORDER 005 item 2, confirmed by ORDER 006). This replaces the "wip/cloud-core-a/E cut from origin/main" of the brief and of ORDERS.md:51. Base: src/ and tests/ of the branch equal origin/main 51c9fc4fb.
- While building run only: `uv run --all-extras --group test python -m compileall -q src/hadavin_sdk/testing/crash.py tests/test_testing_crash.py`; `uv run --all-extras --group test ruff check src tests`; `uv run --all-extras --group test ruff format --check src tests`; `uv run --all-extras --group test pytest -q tests/test_testing_crash.py`; then the six guard files of section 4 once. No full pytest (ORDERS.md:52).
- ruff rule S is on for src with only S101 lifted for tests (pyproject.toml:72, 78-79): no `assert` in crash.py; line length 100 (pyproject.toml:68).
- The marker is written with `os.write(1, ...)` (no `print`) and `os._exit` is called once. Bandit runs at `-ll` on src (ci.yml:181); a finding there is reported, never suppressed (UNVERIFIED that none appears: not run).
- Python 3.12 and 3.13 (ci.yml:74, 142): `def wrap[T]` is 3.12 syntax, allowed by requires-python (pyproject.toml:6).
- Size estimate (first plan): crash.py about 110 lines, test file about 190 lines, 2 files, 0 existing files touched. As built (wc -l 2026-11-20): crash.py 295 lines, test file 1030 lines, still 2 files. Three-try cap applies (ORDERS.md:40).
- Evidence: the pytest output of the one test file, saved to handover/core-a/raw/E-tests.log; P1 is NOT RUN here unless PostgreSQL starts as a non-root user (ORDERS.md:61).
- Rollback: delete the two files; nothing else refers to them.

## 10. BEST-FIRST trade-offs
1. Crash at the edge of an injected object, not at marks inside the runtime. Simpler option: `crash_point("name")` lines inside agent_loop.py as the demo does (demo-hooks.py:24-26). It would reach places between two lines of one method, but it puts test hooks into guarantee-class runtime code, needs edits in core-b's hot file and widens what must be reviewed. Chosen: wrap only. Given up: crash points inside a single store method; on PostgreSQL each statement commits alone (S/store/postgres.py:146), so method edges are the real crash windows.
2. Two modes behind one set of point names. Simpler: kill mode only. It would cost one child process per case and cannot be used with the memory store at all. Chosen: raise for memory, kill for PostgreSQL, same names, so D writes each case once and runs it on both.
3. `BaseException` for the same-process crash. Simpler: a normal exception. The runtime would catch it and tidy up (S/runtime/agent_loop.py:477-483), which is exactly what a real crash does not do, so the test would prove the wrong thing.
4. Home in `S/testing/` although it then ships in the wheel. Simpler and tighter on paper: a module under tests/. That keeps it out of the wheel, but then other repos and client builds that use the core cannot reuse it, and the plan and the lead name `testing/`. The risk of shipping it is closed by invariants 2 and 3 with tests H1 and H5, not by trust.
5. Refuse to build outside pytest. Simpler: no gate. One environment check costs one line and turns "a kill switch in the wheel" into a tool that cannot arm in a deployment.
6. Left-armed is an error. Simpler: disarm silently. A point that never fired means the test did not test what it says; loud is better.
7. No socket guard, no launcher helper. The simpler option here IS the chosen one: nothing a named test needs is missing, and each would be code without a user.

## 11. WHAT STAYS OUT
Socket guard (trigger: the reviewed D or F ticket names a test that must prove "no outside network"; then decide pytest-socket against about 45 stdlib lines, as a request to core-b if a dependency is added). A suite-wide autouse guard in tests/conftest.py. Crash marks inside any existing module. A child launcher, a clock, fixtures, model doubles, runtime builders, schema fixtures (all exist or are stdlib). Helpers for T1's 50 connections (step F's test, written against core-b's interface). Any HTTP, signing or n8n code (step D). Timing or random fault injection, network fault injection, disk-full simulation. Any change to `testing/__init__.py` exports.

## 12. OPEN QUESTIONS, UNVERIFIED, NOT READ
Open questions for the lead (none blocks the build):
1. Is the pytest-only gate (invariant 3) acceptable, given a child process must inherit `PYTEST_CURRENT_TEST`? Checked: no existing use of that variable in src, tests, tools (grep). Recommended: yes.
2. CI runs postgres 17.10 (ci.yml:41, 111) while the plan's evidence run is PostgreSQL 16 on the laptop (plan-v4-final.md:2). Which one counts for P1? Recommended: both; the helper has no version-specific code.
3. Exit code 137 on the laptop: on Windows `os._exit(137)` should give return code 137 as well (UNVERIFIED). Recommended: keep 137 from the demo (demo-hooks.py:33) and let N7 on the laptop confirm; tests compare with the constant, never with a signal number.
4. May core-b use kill mode for step A's process-boundary test? Recommended: yes, offered in section 7; no change in E either way.
5. Optional CHANGELOG line R1: wanted at landing or not? Recommended: yes, one line by core-b in the D+E PR.
6. `trace.CrashWindows` of the demo (inventory-promote.md:11) is not in the inputs. Recommended: not taken; no named test needs it.

UNVERIFIED: that uv_build puts the new file into the wheel (no build run); that pytest sets `PYTEST_CURRENT_TEST` in `os.environ` during fixtures and tests and that children inherit it (test H1 and N7 pin it); that `ThreadPoolExecutor` stores a `BaseException` in the future (E4 pins it); that bandit and ruff raise nothing on `os._exit` and `os.write`; the Windows exit code; any fault-injection library on rung 4; pytest-socket version and licence; the method names of core-b's reserve and settle interface; the final signatures of step D (taken from the draft, not from a reviewed ticket).

NOT READ: S/store/postgres.py outside lines 125-146, 192-270 and its method list; S/runtime/agent_loop.py outside 172-232, 352-412, 462-492 and its `except` list; S/runtime/tick.py outside 100-183 and 335-369; S/store/memory.py after line 104; tests/k1b_support.py, tests/tls_support.py, tests/fixtures/*, tests/contracts/*, tests/demo_askdata/*, tests/warden_port/fakes.py beyond their function lists; tests/contracts/kinds/store_postgres.py beyond lines 1-25 and its grep hits; the bodies of the guard tests beyond the cited lines; tools/mutation_runner.py beyond lines 10 and 69; uv.lock (one grep); README, SECURITY, docs; old-plan-v4-1.md, old-plan-v4-3.md, atlas-n8n.md, review-plan-1 and -2 files, resolve-plan-1.md; ticket C of the draft beyond a skim; any PR or branch; the demo's `trace.py` and tests.
