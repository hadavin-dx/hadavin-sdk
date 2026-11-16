Status: resolved

# Goldfish Annotated Review Report, PD Part 2 (bind guard and stand-in detection), round 10

**Target:** `/home/user/build/snap/pdbind-304c3bd3/DIFF.patch` (full), head `304c3bd34c50d740385003cf9b87168345c9d48d`, security and mode-safety path (no round cap).
**Inputs:** `pdbind-304c3bd3-design-r10.md` (0 Blocker, 3 Major, 4 Nit) and `pdbind-304c3bd3-codebase-r10.md` (0 Blocker, 3 Major, 16 Nit). Both reviewers read code only. Runner a1b9b30a has not reported; its findings are an addendum for the builder.
**Method:** each finding checked against what the reviewers could read; none contested. 30 findings merge into 9 issues. Settled from r9 stays settled (single atom judge, one Scan per request, models.now pins, copy/deepcopy of pinned classes).
**Binding decisions applied:** Part 2 is the source of `is_stand_in`; no suppressions; fake credentials built from parts; new tests fail on old code or are named `test_pin_*` with a truthful label; builders never commit under `handover/`.

## Handoff counts

- PROPOSE FIX accepted: 9 issues (all findings, nits included). CONTEST 0. ESCALATE 0. DECLINE 0.
- Remaining unaddressed: 0. **Round 11 is REQUIRED** (fail-open Major on a mode-safety path, no cap).

## Prioritized findings

### Issue 1, Major (fail-open), class SEAL-COMPLETE: hook contents (design M-1, codebase N11)
`requests.py:98-104`, `app.py:88,232`: hook fields are judged by identity only. `build()` records `overrides["tools"]=dict(tools)` but the runtime holds a second copy; `app.runtime.hooks.tools["x"]=real_fn` after the seal keeps identity, so a public POST is served with a real callable held. Same gap for toolbox internals and the closures `post_card` and `request_approval` (cell contents or `__code__` rewritten).
PROPOSE FIX: at seal time snapshot key set and value identities of every hook container (tools, toolbox members) and compare on each read; compare closure `__code__` by identity and judge cell contents through the same atom/stand-in judge; where a rewrite is genuinely outside the model (object.__setattr__, sys.modules) say so in CHANGELOG with the exact list. Tests: assign into `hooks.tools`, replace a toolbox member, rewrite a closure cell: each must read as real.

### Issue 2, Major, class SEAL-COMPLETE: Runtime instance members (codebase M1)
`agent_loop.py:212-213` writes `_evidence` and `_kinds`; `requests.py:52-67,123-140` judge neither. `rt._kinds = <object with __contains__>` is believed and foreign code runs on paths `on_decided` reaches.
PROPOSE FIX: seal or scan every key of the built runtime; add a test that the judged names (`_RUNTIME_SEALED + _RUNTIME_SERVICES`) equal the key set of a built `Runtime`, so a new member fails the test. Fix the comment at `requests.py:58-60`. Test and mutant row per member.

### Issue 3, Major, class LEAK (design M-2, codebase N8)
`requests.py:71,81-87`: the `_RUNTIME_SEALS` value references its key (hooks, closure, `on_decided`, holder, runtime), so the weak dictionary never frees; each `build()` leaks store, audit, registry and hooks; the docstring "a runtime that is gone leaves nothing" is false.
PROPOSE FIX: keep only derived data (names, ids as plain values, weakrefs) in the value, or hold the seal in a slot of the runtime-side object; add a gc test (build, drop, `gc.collect()`, weakref dead). Correct the docstring. Mutant row: store a strong reference.

### Issue 4, Major, class VACUOUS-TEST (design M-3, codebase M2)
`test_bindguard.py:4879-4887` runs neither a run nor a tick. The key-set rule would turn any lazily written attribute into a 503 on a public bind.
PROPOSE FIX: drive `handle` and a real `tick` (using real objects, not fakes of the runtime) between the two key snapshots; assert not counted; mutant row adds a lazy attribute in `Runtime`. Fail-before: must fail when a lazy attribute is added.

### Issue 5, Major, class CHANGELOG-TRUTH (codebase M3, N16, design N-4)
`CHANGELOG.md:270` says a pin is taken the first time a class is found live; the same bullet says import-time. 2,400 rows "use the whole budget" is untrue (limit 2,400 to 2,600). The shared budget now refuses what earlier code served (200k store values plus 60k model calls) and is not marked Breaking.
PROPOSE FIX: correct all three; mark the budget change Breaking with the old and new limits; add the in-process limit list from Issue 1. Replace the weak `rows or rows+1` check (`:5069`) by the exact check already at `:4117/4130` (delete the duplicate).

### Issue 6, Minor, class PIN-LABELS (codebase N1-N4, N15)
`test_every_build_argument_...` (`:4570`) says it passes on 83cdb7a2 but it fails there; the pin-count test (`:5044`) is a pin and unlabelled, hard-codes "3", and has no row that changes a count by one; `:4890` says "checked below in the notes" (none); `:4841` does no POST (name overclaims); the lookalike-letter test is no longer the named killer of B31/B221 or B210/B230/B231.
PROPOSE FIX: labels from a real old-code run in a git worktree at 83cdb7a2 with raw lines in the evidence; rename `test_pin_*`; fix names to match behaviour; add a row for the count; name a real killer for each merged row.

### Issue 7, Minor, class MUTANT-KILLER (codebase N5, N13, N14, design N-3)
`:4594` guards a folder search that no longer exists; B253 missing from the header note; the equivalent-row comment at `bind_mutants.py:1917-1920` gives the wrong reason (the other nine slots are also read by `held_services`, `config`, `config_facts`; only the loop reads `_audit_sink` and `_registry`).
PROPOSE FIX: delete the dead test; correct the header and comment; state B253 in the note.

### Issue 8, Minor, class API (design N-1)
`seal_runtime` is public and unauthenticated (`requests.py:74`).
PROPOSE FIX: make it private (underscore) and update callers and tests; add a test that the public namespace does not export it.

### Issue 9, Minor, class TEXT (codebase N6, N9, N10, N12, design N-2)
`_nested` defined twice (`:2631`, `:4710`; ruff F811); `rt.tick = f` text names a method that does not exist (say "an extra name"); stale `standins.py:57` (20 of 22; now 23), `standins.py:152,289-293` omit `Hooks`, `receiver.py:125` omits ASCII; shared `Scan` blames the wrong object after the budget is used.
PROPOSE FIX: all in the same push; for the Scan, record the object that crossed the limit.

## ONE FIX BRIEF (single small builder, batch 11; fast-forward only onto `wip/cloud-pd-bind`)

Rules: `PYTHONPATH=<worktree>/src` and print `hadavin_sdk.__file__` before any run; cloud limits (no full suite, focused tests and focused rows only, at most 2 heavy processes); re-measure fail-before with `git worktree` at 83cdb7a2 and at 304c3bd3, printing raw pass/fail lines; no suppressions; fake credentials built from parts; never commit under `handover/`.

| # | Class | File and change | Test | Mutant row | Fail-before |
|---|---|---|---|---|---|
| A | SEAL-COMPLETE | `requests.py`/`app.py`: snapshot hook container keys and value identities; compare closure `__code__`; judge cells | assign into `hooks.tools`; replace toolbox member; rewrite closure cell | one row per comparison dropped | each fails on 304c3bd3 |
| B | SEAL-COMPLETE | seal or scan `_evidence`, `_kinds`; key-set test | `_kinds`/`_evidence` replaced; judged names equal built key set | row per member | fails on 304c3bd3 |
| C | LEAK | derived data only in seal value; docstring | gc test (weakref dead after drop) | strong-reference row | fails on 304c3bd3 |
| D | VACUOUS-TEST | real `handle` and `tick` in the lazy-attribute test | lazy attribute added in Runtime reads as not counted | row adds lazy attribute | fails on 304c3bd3 |
| E | CHANGELOG | line 270, budget wording, Breaking mark, limit list; drop weak row-count check | exact count check stays | none | fails when a row is added |
| F | PIN-LABELS, MUTANT, API, TEXT | issues 6-9 as listed | per item | rows named | by real old-code runs |

Builder reports once when ALL of A-F are done: new head sha, raw fail-before lines, anything not done and why.

## Round 11 and evidence for the final head

- **Round 11 is required** (fail-open Major on a mode-safety path). Fresh design and codebase reviewers on a new snapshot.
- **Cloud evidence (runner, records only):** focused tests on Python 3.12 and 3.13; new and changed rows plus a 60-row sample; fail-before worktree runs with raw lines.
- **RUN ON LAPTOP (Linux Docker, final head only, requested only after a fresh round finds 0 Blocker and 0 Major):** hadavin-sdk `<final sha>` full pytest plus the complete bind mutant table (244 rows now, 243 on 3.14; more after batch 11), py313 and py312, Postgres, CI flags. Windows is not valid evidence.
- Ledger rows PDBIND-r10-1..7 exist; the caller adds new rows for issues 3 and 6-9.
