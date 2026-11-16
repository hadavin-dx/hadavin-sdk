<!-- full hand-back report of sub-agent a9678c99, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT review round 4, Q8a-1, head 0b97d55a (delta review, read-only; reading only, nothing executed)

## Verdict: NOT CLEAN. 1 Blocker: 0. Major: 1. Minor: 6.

No evidence folder exists for this head (/home/user/hadavin-sdk/handover/evidence/Q8a-1/0b97d55/ is empty). Every run-dependent claim is unproven: full suite, Postgres tests, the mutant count (71 claimed), ruff, format, bandit, and the PR notes' test counts (198 and 103).

Snapshot root below: /home/user/build/snap/q8a1-0b97d55/

## Findings

### M1. Major: outside demo, "a real TickContext" is decided by isinstance, so a `Mock(spec=TickContext)` or a subclass hands a made-up time to the evidence purge
- Where: src/hadavin_sdk/runtime/tick.py:83 (`if not isinstance(ctx, TickContext) and is_live(...)`). The `__post_init__` refusal at tick.py:73-77 is the only other guard.
- Input, pilot app:
  - `ctx = unittest.mock.Mock(spec=TickContext); ctx.app = app; ctx.now = datetime.now(UTC) + timedelta(days=500); purge_evidence(ctx)`. A spec'd Mock reports `__class__` as `TickContext`, so `isinstance` is True and `_now` returns the 500-days-ahead time. Every stored tool call and redaction map is deleted. That is the exact outcome the ticket exists to stop.
  - A subclass that overrides `__post_init__` also works: `class T(TickContext): def __post_init__(self): pass`, then `purge_evidence(T(app, ahead))`. `T` is not decorated, so it inherits `__init__` and runs its own `__post_init__`. The frozen flag does not help, because the time is set in the constructor.
- Expected: refused with "now= is for tests...". Actual: accepted.
- Why Major: a stand-in object reaching a live process by accident is the stated threat model. A spec'd Mock is the usual stand-in in test code. The CHANGELOG sentence "outside demo a step refuses an object that only looks like a context" and the `_now` docstring ("a stand-in object that merely has a `now` is refused") are false for these two cases.
- Smallest fix at the choke point: change tick.py:83 to `type(ctx) is not TickContext`. A Mock's `type()` is `Mock`, so it is refused. Add `def __init_subclass__(cls, **kw): raise TypeError(...)` so a subclass cannot exist. Add a Mock(spec=...) case and a subclass case to the stand-in test (tests/test_q8a_live_overrides.py around line 959).

### Route list for question (1)
Each route is marked as named by the builder or not. Docs checked: the CHANGELOG limit paragraph, the tick.py `run_tick` docstring, and PR-NOTES "NOT covered".

| Route | Line | Gets a made-up time into a deleting step outside demo? | Named by builder as not covered? |
|---|---|---|---|
| `Mock(spec=TickContext)` | tick.py:83 | Yes (M1) | No |
| Subclass of TickContext (override `__post_init__` or `now`) | tick.py:73-77, 83 | Yes (M1) | No |
| Object with a `__class__` property returning TickContext | tick.py:83 | Yes (hostile; fixed by the exact-type check) | No |
| `object.__setattr__(ctx, "now", t)` on a real context | frozen only blocks normal assignment | Yes | No. The docstring says "The time cannot be changed afterwards (the object is frozen)", which is true for assignment only. |
| `TickContext.__new__(TickContext)` then `__dict__.update(...)`, or a crafted pickle | tick.py:73 | Yes (hostile) | No |
| `dataclasses.replace(ctx, now=t)` | tick.py:76 | No: `__post_init__` raises (tested) | Not needed |
| `copy.copy` or `deepcopy` of a real context | n/a | No: it copies the existing time | Not needed |
| Stand-in with `app` set to a wrapper whose `config.environment` is "demo" and which delegates the rest to the real app | tick.py:83 reads the stage from the stand-in's own `app` | Yes (hostile) | No (falls under "assigning attributes after build" only loosely) |
| Positional argument order | n/a: steps take one argument; `run_tick(app, t)` is refused as `now=`; `TickContext(t, app)` fails with AttributeError | No | n/a |
| Importing `_now` | read-only accessor | No | n/a |
| `app.approvals.clock` replaced after build, then `TickContext(app)` | tick.py:75 | Yes | Yes ("a clock replaced after build") |
| `app.config` swapped to a demo copy after build | tick.py:76, 83 | Yes | Only by the general "assigning attributes after build" |
| Rebinding `tick._BUILT_IN` or `tick.NO_GIVEN_TIME` | tick.py:309 | Disables the steps check | Not named (see m5) |

### m1. Minor: "frozen" and the TickContext docstring overclaim
tick.py:66 says the time cannot be changed afterwards; the CHANGELOG says the same. This holds for ordinary assignment and `dataclasses.replace`, not for `object.__setattr__`. Add one clause to the docstring and the CHANGELOG limit list: a context altered with `object.__setattr__`, built without its constructor, or a subclass is not covered. If M1 is fixed as suggested, the subclass part drops out.

### m2. Minor: a step appended with a name already in STEPS hides a failed built-in step
- Where: tick.py:432 (`ctx.results[step.name] = _run_step(...)`), and the tick_state row keyed by name; `_missing_built_in_steps` (tick.py:312-315) checks names only.
- Sequence in pilot: `STEPS.append(TickStep("purge_evidence", 0, lambda ctx: None))`. The built-in purge fails and records FAILED. The appended step has the same name and every_s of 0, so it runs, overwrites `results["purge_evidence"]` with OK, and overwrites the tick_state row with `last_error=None`. `run_tick` returns 0 even though the purge failed, which is the silent outcome the check exists to stop.
- The same applies to a step with a built-in name but a huge `every_s` or `interval`: that is "replacing a step", but the limit texts name only "replacing a step's function".
- Fix: in the check at tick.py:416, also refuse duplicate names (`len({s.name for s in STEPS}) != len(STEPS)`). The TickStep comment at tick.py:90 already says "unique". Name the interval and every_s case in the limit text.

### m3. Minor: the ticket's errata do not record this round's deviations, and the PR notes say they do
- TICKET.md R5 (line 46) still gives the message "between 0 (not included) and 3600" and has no lower bound. There is no erratum for the 0.001 lower bound, the shared message wording, or the frozen and optional-time TickContext. R7 covers STEPS only.
- PR-NOTES-builder.md line 33 says the deviations are "all recorded in the ticket's errata rev 3 to rev 5". That is false for deviations 7, 8 and 9, and the notes number them out of order (7, 9, 8).
- Fix: the lead adds errata rev 6 for the lower bound and the TickContext change, or the PR notes say plainly that these are not yet in the errata.

### m4. Minor: the config error text echoes the offending value and the validator wording is unpinned
- Where: config.py:185-190 and the `load_config` handler at config.py:520-521, which uses `str(ValidationError)`. That text carries `input_value=...`, `input_type=...` and a documentation URL beside the sentence.
- For `executor_timeout_s: '5'` the message holds `'5'`. The keyword message (app.py:94) is value-free. It is not a secret, but "messages free of values" does not hold on the config route. The CHANGELOG says "the same sentence", which is true, but it is not the whole message.
- Fix: strip the value (a `PydanticCustomError`, or format only `loc` and `msg` as `_validation_text` already does for the stage rename).

### m5. Minor: the shared timeout rule is checked before the config library converts, but YAML 1.1 forms are accepted as ints and not documented
- Config route (checked by reading): `mode="before"` runs before pydantic converts, so `true`, `'5'`, `.inf`, `.nan` and `3601` are refused. `Config(**raw)` is the only construction route in `load_config`.
- YAML forms, from PyYAML's resolver, by reading and not run:
  - `0x10` loads as 16, `1_0` as 10 and `010` as 8, all accepted as ints.
  - `1:30` loads as the sexagesimal int 90 (YAML 1.1), accepted.
  - `5e-324` has no dot, so it loads as text and is refused (a misleading reason).
  - `5.0e-324` loads as a float and is refused. `1.0e400` loads as inf and is refused.
  - `10**400` as a YAML int is compared as an int, with no overflow.
- The grammar is int or float, not bool, 0.001 <= v <= 3600 with both bounds included. `Decimal`, `Fraction` and text are refused. float and int subclasses (numpy floats, IntEnum) pass. The config field converts the int 3 to 3.0 afterwards; the keyword keeps the int.
- Not a defect in the rule. Fix: one sentence in the CHANGELOG that the config file is read with YAML 1.1 rules, so `0x10` means 16 and `1:30` means 90. Pilot and prod configs that held an out-of-range `executor_timeout_s` now fail to load. The CHANGELOG says the field is checked in every stage, so that is stated.

### m6. Minor: no run evidence for this head
See the top of this report. Also unproven: line length of config.py:158 (the `EXECUTOR_TIMEOUT_RULE` f-string is about 130 characters) against the repo's lint settings, which I could not see.

## Answers by area

**(2) Shared timeout rule:** see m4 and m5. The keyword and the config field use one function, with the same bounds and the same wording; the config text adds pydantic's wrapper.

**(3) Built-in STEPS check:**
- Names are remembered at import (tick.py:309). The check runs at tick.py:416 and reads the module global `STEPS` at call time, so a rebound `STEPS` is seen.
- A step replaced by another function with the same name passes the check. That is named ("replacing a step's function").
- In-place mutation between the check (tick.py:416) and the loop (tick.py:431) needs a second thread. It is not named. Low severity.
- Appended steps run after the built-in ones (tested).
- The duplicate-name and interval cases are m2. Rebinding `_BUILT_IN` is unnamed (the same class as a patched `STEPS`; add "or `_BUILT_IN`").

**(4) The two changed existing tests: nothing weakened.**
- tests/test_k5_round8_postgres.py: `TickContext(app, datetime.now(UTC))` became `TickContext(app)`. The pilot app's clock is the real clock, so the purge-identity deletion check still runs. It also gained assertions that the audit and channel got the runtime store, not the purge store.
- tests/test_k5_round9b.py: the stand-in app gained `environment="demo"`, which the context needs to read. The test target (the reprobe) is unchanged. Note that it now depends on the "demo" exemption.
- Not an existing test but related: tests/test_stage_names.py's timeout test moved from "no lower bound" to the 0.001 bound deliberately (see m3).

**(5) Honest-limit texts:**
- Named correctly: the store's own `purge_tool_calls(before)` and `purge_redaction_maps(before)`; `Approvals.sweep(at=)` and `resend_unsent(at=)` (their docstrings now say `at=` is the tick's own parameter); a replaced clock; a changed or patched STEPS; `TickContext(app)` by hand not being a supported entry point.
- Not named: the routes in M1, m1, m2 and the `_BUILT_IN` rebinding.
- Over-claims: "a step refuses an object that only looks like a context" (CHANGELOG, tick.py:81-82) and "cannot be changed afterwards" (tick.py:66).
- The owner questions in PR-NOTES are in plain words. I did not find an owner-question wording problem. The ledger entries and dates were not checked.

**(6) Message texts, made-up credentials, suppressions:**
- Messages: "now= is for tests; it is refused in pilot and prod", "a built-in tick step is missing: <names>" and the timeout sentence are plain and value-free. The config route echoes the value (m4).
- Credentials in tests: the new tests I read build them from parts (`"tok" + "-steps"`, `"stag" + "ing"`). No key-shaped literal was found in the diff.
- Suppressions: no new noqa, nosec, type-ignore or pragma in DIFF-fix3.patch (the lines I read).

## Round-3 checklist

| Finding | Status |
|---|---|
| Design N1, codebase F3: STEPS route unnamed and untested | Resolved: names check at tick.py:416, limit text names patching, tests for cut, emptied, appended and demo lists. Residual: m2 and `_BUILT_IN` rebinding. |
| Design N2, codebase F1: config field had no upper bound | Resolved in code: shared rule, `.inf`, `true`, `'5'`, 3601 refused (config.py:158-190). Residuals: m4, m5. |
| Design N3: no evidence for fcd77a6 | Not resolved for this head (m6). |
| Design N4, codebase F5: seam recorded names, not objects | Resolved: `Call.available` is a dict of objects and the store identity is asserted (tests/test_k3_pilot_env.py, tests/test_k5_round8_postgres.py). |
| Design N5: scheduled-job sentence thin in the docstring; "accepted" wording | Resolved in the app.py docstring and the CHANGELOG ("is not refused either"). `Approvals.sweep` and `resend_unsent` docstrings gained the `at=` clause. Ledger and owner trail not verified. |
| Design nit: `at or self.clock()` | Resolved (`is None`, requests.py). |
| Codebase F2: errata missing for timeout rule | Not resolved: TICKET.md R5 is unchanged and now disagrees with the code (m3). |
| Codebase F4: killer's last assertion proved less than its message | Resolved: a fresh app is built and each step is asserted run (test_stage_names.py hunk). |
| Codebase nit: "six keywords" falsy sentence | Resolved ("five keywords plus sources and tools"). |
| defaults.py docstring and header nit | Resolved (own header, docstring updated). |
| tick.py "RAISES ... then" unclear sentence | Resolved. |
| SIGN_IN_FIELDS nit | Resolved (five fields). |

## Not checked
- Any test, mutant, lint, format, bandit or gitleaks run.
- DIFF-vs-main.patch beyond the fix3 hunks. I read all hunks of DIFF-fix3.patch and the full tick.py, the changed parts of config.py, and the test hunks in the patch. The other src files (app.py, requests.py, defaults.py) were read through the diff, not in full.
- PyYAML resolver behaviour (m5) is from knowledge, not a run. Pydantic's error text format (m4) is also from knowledge.
- Whether mutants M13h-M13j and M9e-M9f kill their tests.
- Ledger, D-012, and the owner-question trail.
- Repo files outside the snapshot, for other callers of `TickContext` (src grep inside the snapshot shows none outside tick.py).
