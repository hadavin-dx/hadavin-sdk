Status: resolved

# Goldfish Annotated Review Report, PD Part 2 (stand-in bind guard), round 12

**Target:** `/home/user/build/snap/pdbind-54c3d8a2/DIFF.patch` (full, merge-base diff, 23 files), head `54c3d8a297c697eaa5f78aae7363a59c635fbe27`, security path (no round cap).
**Inputs:** `pdbind-54c3d8a2-design-r12.md` (1 reported Blocker, 2 Major, 5 Minor, 1 Nit) and `pdbind-54c3d8a2-codebase-r12.md` (2 reported Blockers that are statements contradicting the code, 4 Major, minors and nits). Both reviewers read code only and ran nothing. Evidence runner a555e712 has not reported (`handover/evidence/PD-bind/54c3d8a2/RESULTS.md`); its findings are an addendum for the builder.
**Method:** every finding checked against what the reviewers could read. 27 findings merge into 9 issues: 1 CONTEST, 1 FOLLOW-UP item (not part of this change), 7 PROPOSE FIX. Settled from r11 stays settled: identity and weak-mark seal; only the exact pinned class is entered; no suppressions and no per-file ignores except `tests/**` S101; named tuple plus surprise-error test for broad excepts.
**Result:** no fail-open path found. The named tuple itself is sound and every path that catches fails closed: no path leaves the runtime served, answers a request as real, or executes an action (design m4, checked against `receiver.py:90,147,173` and `requests.py:441,512`, `standins.py:696`). What remains: two real gaps in what the seal detects (whole containers; plain values), CHANGELOG sentences that are now false or overstated, missing tests on four sites, wrong pin labels, duplicate mutant row names. Batch 13 changes code on a security path, so a fresh round is required.

## CONTEST (with evidence)

**Design B1 "diff also reverts unrelated main content" (`ci.yml`, `pytest-xdist` in `pyproject.toml` and `uv.lock`, README test section, CHANGELOG "Client-profile check" entries, `tests/fixtures/timing.py`): CONTESTED, it is not in the branch.**
Evidence the reviewer could not read but which is checkable from the repository: the lead cut `DIFF.patch` as a two-dot diff against the current `origin/main`; the branch base is `2a8c2aac` and `main` has moved on since, so newer `main` content shows as removed. The merge-base diff (`git diff origin/main...54c3d8a2`) has 23 files, the two-dot diff had 49. The snapshot was re-cut at 05:29Z (old file kept as `DIFF-twodot-includes-main-drift.patch`). The branch is rebased onto current `main` by the lead at PR time, not by the builder. The reviewer's one suppression hit (`# shellcheck disable=SC2086` in `ci.yml`) is inside the same chunk and is not in the branch diff. Lesson recorded: snapshots use `origin/main...HEAD` from now on (this is the lead's slip).

## Follow-up item (not part of this change; recorded as its own ledger item)

The four broad catches already on `main` (`requests.py:818, :887, :925` and `app.py:210`, each `except Exception` with `noqa: BLE001`) wrap channel client or store code. Both reviewers agree they do not belong here: they are not guard reads, and they fail open to "keep going" on purpose (an undelivered card, an unsent message, a tick that ends the run). Narrowing them to `READ_ERRORS` would make `request()` and `sweep()` crash after the approval request is saved, because a channel's own errors (HTTP client, Slack client, store backend) are `Exception` subclasses outside the tuple. A safe tuple needs `READ_ERRORS` plus the channel client error bases plus `StaleState` and `NotFound` (set unverified). Separate work item with its own tests and its own review; the lead is told in the report block. The `agent_loop.py` sites and `guard/http.py:140` (a `BaseException` catch with no `noqa`) are on `main` and outside this change; the builder checks `guard/http.py:140` re-raises and reports.

## Decisions made here

1. **Whole-container replacement (design M1): FIX.** The seal marks each non-deep container (dict, list, tuple) in an entered field by `(id, kind)`, not by class only. Replacing `registry.contracts`, `agents`, `tools` or a limits field with another container of the same class is then a change. Tests: replace each named container with an equal copy and with a different one; both read as a change. If a field is legitimately re-created by the runtime at run time (a cache), the builder lists it with the reason in the CHANGELOG OUTSIDE list instead.
2. **Plain values in an entered instance (design M2, codebase 4): FIX for the fields that govern limits, evidence and redaction; OUTSIDE for the rest.** For `limits` (all numeric and bool fields read by `agent_loop`: `max_*`, `fetch_ceiling_bytes`), `_evidence` (`scrub` and the redaction settings) and the hook objects' text fields that name a target (URL, host, channel, model name), the seal records a keyed digest of the value (the existing blake2b path) and compares it. Values that change in normal use (counters, clocks, `RunState` fields) are listed by name in the OUTSIDE list as "may move in use, not compared". The builder lists, per class, which fields are compared and which are not, so the list is exact. This fixes the repo-rule gap instead of documenting it.
3. **B279 (`type(hooks) is not sealed[5]`):** KEEP as defence in depth (a second source of truth beside `_PINNED`) and make it killable: monkeypatch `standins.is_pinned_instance` to return True in the test, restore row B279; fix the test docstring at `test_bindguard.py:6075-6077` and the `bind_mutants.py` header so they agree.
4. **Pin tests:** the 15 tests the codebase reviewer lists pass on 82dd69c1 (name-only or behaviour-equal); they are renamed `test_pin_*` with the label "same behaviour on the old tree" unless the runner's raw run at 82dd69c1 shows a behaviour failure.
5. **Unnamed error at the receiver:** accepted behaviour (loud, fails closed, connection dropped with traceback), now stated truthfully in the code docstrings and CHANGELOG; the socket-level tests pin it.

## Prioritized findings

### Issue 1, Major, class SEAL-COMPLETE / WHOLE-CONTAINER (design M1)
`requests.py:136-137` marks dict, list and tuple by class only (`_MARK_KIND`), and `_member_fields` (`:285`) uses it. Replacing a whole container of the same class in `registry`, `limits`, `audit` or `_evidence` is not detected; CHANGELOG OUTSIDE item 8 ("compared by identity only") is false. Tests `test_bindguard.py:6091` (appends inside) and `:5433` (replaces with `_Opaque`) do not cover it.
PROPOSE FIX: decision 1. Mark non-deep containers by `(id, kind)`; fix item 8's text to what the code does; tests for equal-copy and different-container replacement of each named container; a mutant row that reverts to the class-only mark.

### Issue 2, Major, class SEAL-COMPLETE / PLAIN-VALUES (design M2, codebase 4)
`_member_fields` and `slot()` (`requests.py:146-149, 200-210, 270-290`) accept ANY text, number, bool, None, set or deque in an entered instance: a URL swapped, `False` flipped to `True`, `max_*`, `fetch_ceiling_bytes`, `_evidence.scrub` (read at `agent_loop.py:315-318, 400, 428, 509, 527, 573`) can change silently. Test `:5961` and row B278 pin the current acceptance; CHANGELOG item 9 lists only set, frozenset, deque.
PROPOSE FIX: decision 2. Digest-compare the governing fields; list the rest by name in an eleventh OUTSIDE item; tests that flip a bool, change a number and swap a URL read as a change; the existing pin at `:5961` is rewritten to cover only the listed non-compared fields; mutant rows for dropping the value comparison.

### Issue 3, Major, class CHANGELOG-TRUTH (codebase 1, 2; design m4, m5; nits)
- `CHANGELOG.md:289` "Any error reads as real ... the guard's own checks raise nothing that is not caught" is false: 13 uses of `standins.READ_ERRORS` (`standins.py:103-111`: AttributeError, TypeError, ValueError, LookupError, ArithmeticError, RuntimeError, OSError); anything else (StopIteration, AssertionError, ImportError, MemoryError, a custom Exception) propagates. In `receiver.do_POST` (`:172-174`) it is not a 503 (connection dropped, traceback on stderr); in `serve()` it leaves as itself, not `BindRefused`. `CHANGELOG:7` still says a slot error gives "a 503 and not a dropped connection". No Changed entry names `READ_ERRORS` or this behaviour.
- "Closed in batch 12 (each has a test that fails on the batch 11 code)" is overstated: defaults items, `__func__` and `__self__` of a bound method, closure cell code and content, dict keys and items, list items were done in the old walk; their new tests pass on 82dd69c1. Genuinely new: fields of limits/audit/registry/_evidence, `__kwdefaults__` content, function `__dict__`, the keyed digest (plus issues 1 and 2 above).
- Site count: 9 `except READ_ERRORS` plus 4 `suppress(*READ_ERRORS)` = 13 uses, plus 2 `except ValueError` (`requests.py:239, :478`): say exactly that; fix the note, the CHANGELOG and any test text that says "one ValueError".
- Node cap is per walk (hooks and each of four members get their own cap, up to 10,000 objects per runtime): fix CHANGELOG item 10 and the `_WALK_NODES` comment (`requests.py:102`, says "per runtime").
- "It holds no strong reference to a runtime object" is off: `agents` (`_MARK_STRONG`, `requests.py:352`) and the `_kinds` frozenset are held strongly (text only). Say "no strong reference to anything that reaches the runtime".
- "items (1) to (3) are the paths that need code already running in the server process" misleads (all ten need in-process code).
- State that the walk's reach for defaults is one level shallower than before (test `:5934` fails on the old tree by behaviour).
- "store, model and detector" in the CHANGELOG: the attribute is `llm` (`_RUNTIME_SERVICES`).
- Cost figures cite source head 3bb8c145, not the final head: re-measure at the final head (alone on the machine) or say they were measured at 3bb8c145; keyed digesting is O(size) and outside the node budget (say so).
PROPOSE FIX: all of the above, each changed sentence with a claim test (the CHANGELOG-numbers test style already in the repo).

### Issue 4, Major, class MUTANT-KILLER / NAMES (codebase 3, 6, 7, 8)
`tests/bind_mutants.py` has duplicate row names: B270, B271, B272 each appear twice (`:2440/2449/2458` pin-count and budget blame; `:2476/2485/2494` hook defaults, kwdefaults, `__dict__`). A run by name hits two different rows. Count 279 is right. B280's expectation "DID NOT RAISE" is correct only if no `slot()` call occurs past position `need//2` (`slot()` still raises `_Over`, `requests.py:202`); B279 per decision 3.
PROPOSE FIX: rename the three new rows to unused numbers; add a uniqueness test over row names (names are the row key, the test fails on a duplicate); the runner confirms B280 killed and the builder re-runs it on the final head; restore B279 (decision 3). The row count in the CHANGELOG is derived by the claim test.

### Issue 5, Major, class PIN-LABELS (codebase 5 and pin list)
`test_bindguard.py:5043` and `:5056` say "Fails on 83cdb7a2 (no HOOKS there)": a missing name only. Fifteen tests pass on 82dd69c1 and need the `test_pin_` prefix: `:5670, 5875, ~5913, 5961, ~5990-6015 (kept-limit tests), 6091, 6106, 5531, 5553, 5586, 5642, 5724, 5808, 5706, 6072`. `:5934` fails on the old tree by behaviour and is fine.
PROPOSE FIX: decision 4; set every label from the runner's raw old-tree run (82dd69c1 and 83cdb7a2 with the new tests copied in); tests that pass there are `test_pin_*`; tests that fail there for a behaviour stay with the raw line in the header.

### Issue 6, Major, class SURPRISE-TESTS (design m1, m3, m4; codebase checks)
The four `contextlib.suppress(*READ_ERRORS)` sites (`standins.py:245, 250, 307, 337`: annotations, slotnames, `pin_module`, `pin_all`) have no surprise-error test although `standins.py:101` says "a test per site". `:307` and `:337` are fail-open-adjacent: a swallowed pin error leaves the class unpinned until the first question, after any tamper. Tests call `_recheck` and `_refused` directly; nothing shows that when `do_POST` (`receiver.py:173`) raises, nothing is answered as real.
PROPOSE FIX: for each of the four sites a named error is swallowed and the class is read as real/unpinned in the documented way (state it), and an unnamed error propagates; `pin_module` and `pin_all`: a named error leaves the class unpinned and the first question still reads a tamper as not-real (the test proves the guard still refuses a tampered class); one socket-level test for each of `_recheck` and `_refused` (an unnamed error in `do_POST`: the connection is closed, `handle_slack_action` is never reached, no action runs). Add a sentence to the receiver docstring and the CHANGELOG (issue 3). Row for each new site that restores `Exception`.

### Issue 7, Minor, class TEXT (design nit; codebase nits)
Formatter-mangled comments (`requests.py:102-104, 140-143, 164-168`, `bindguard.py:165-167`, `test_bindguard.py:5799`: `except (\n    TypeError\n):  # ...`, `target = (\n    held()\n)  # ...`): put the comment on its own line above. Duplicated `ApprovalDecision`-building blocks (`:5553`, `:5586`): extract one helper; `_fresh` (`:3509`) vs `_run_python` (`:443`) overlap: merge or say why not. `_run_python` docstring: say plainly it is behaviour-equal to `subprocess.run` (fixed argv, no shell, `sys.executable`, timeout with kill and wait) and not a lint workaround; note the two differences (a timeout raises `TimeoutError`, output decoded strictly as UTF-8). Long lines: 227 in `standins.py` and `bindguard.py`, 179 in `receiver.py` and `requests.py`, 422 in tests; E501 is not selected, so wrap only the added lines over 100 in the diff (not the whole files).
PROPOSE FIX: as listed.

### Issue 8, Minor, DECLINE
Design m7 "pre-existing suppressions in untouched files" and codebase "mypy 166 vs 122": mypy is not in the dev dependencies, there is no `[tool.mypy]`, and CI runs only ruff; the +44 comes mostly from new untyped test helpers and `cast(Any, ...)`. Recorded, no change in this batch; the builder does not add type-ignore to quiet it. (A typed-test-helper clean-up is optional and not a gate.)

### Issue 9, Minor, class SUPPRESSION-COUNT
Both reviewers count 0 suppression markers on added lines; the per-file-ignores in `pyproject.toml` are `tests/**` S101 only; about 9 `noqa: S603` and `BLE001` markers were removed. The builder's batch 13 report repeats the count against `origin/main...HEAD` (merge-base) and the runner confirms.
PROPOSE FIX: no code; keep the count in the report.

## Handoff counts

- PROPOSE FIX accepted: 7 issues (1-7 and 9 as a report line). CONTEST: 1 (design B1, snapshot artifact). FOLLOW-UP item: 1 (the four old broad catches on `main`). DECLINE: 1 (issue 8).
- ESCALATE: 0.
- Remaining unaddressed: 0. **Round 13 is REQUIRED** (security path, no cap, the batch changes the seal).

## ONE FIX BRIEF (single small builder, batch 13; fast-forward only onto `wip/cloud-pd-bind` from 54c3d8a2)

Rules: `PYTHONPATH=<worktree>/src` and print `hadavin_sdk.__file__` before any run; cloud limits (no full suite, focused tests and focused rows only, at most 2 heavy processes, each command under 8 minutes and resumable; run mutant rows detached with a log); real fail-before runs in `git worktree`s at 82dd69c1 and 83cdb7a2 with the new tests copied in over old src, raw lines; no suppressions and no per-file ignores; fake credentials built from parts; never commit under `handover/`; commit and push first, then finish runs; run the FULL test files of everything the change touches and list every test file you did not run; suppression-marker count on added lines against `origin/main...HEAD` (merge-base) in the report; remove every scratch worktree you made and stop your own processes; **NEVER answer y/yes to a start or confirm prompt of any script that can reach a network or send mail; run only loopback settings; a prompt means STOP and report.**

| # | Class | File and change | Test | Mutant row | Fail-before |
|---|---|---|---|---|---|
| A | SEAL-COMPLETE / WHOLE-CONTAINER | issue 1: mark containers by `(id, kind)`; fix OUTSIDE item 8 | equal-copy and different container replaced in registry, limits, audit, _evidence read as a change | revert to class-only mark | raw lines |
| B | SEAL-COMPLETE / PLAIN-VALUES | issue 2: digest-compare governing fields; list the non-compared fields per class in the OUTSIDE list | bool flip, number change, URL swap read as a change; listed fields do not | drop the digest comparison | raw lines |
| C | CHANGELOG-TRUTH | issue 3 (every bullet) | claim tests | none | wrong claim fails |
| D | MUTANT-KILLER / NAMES | issue 4: unique names, uniqueness test, B280 check, B279 killable | uniqueness test; B279 killer | B279 restored, new rows | duplicates fail the test |
| E | PIN-LABELS | issue 5: 15 renames, relabels from the old-tree run | relabelled set | rows follow renames | raw lines at 82dd69c1 and 83cdb7a2 |
| F | SURPRISE-TESTS | issue 6: four suppress sites, two socket-level tests | named swallowed, unnamed propagates, tamper still refused | rows restoring `Exception` | raw lines |
| G | TEXT | issue 7 | none (read check) | none | n/a |

Builder reports once when ALL of A-G are done: new head sha; per class: which fields are digest-compared and which are listed as not compared; raw fail-before lines; list of test files not run; suppression grep; mutant rows run and their result on the final head (name each row); whether `guard/http.py:140` re-raises; anything not done and why.

## Round 13 and evidence for the final head

- **Round 13 is required.** Fresh design and codebase reviewers on a new snapshot cut with `git diff origin/main...<head>`; they count suppression markers on added lines, inspect `pyproject.toml` for per-file ignores beyond `tests/**`, and read the seal change as a security change.
- **Cloud evidence (one runner on the final head, records only):** focused tests on Python 3.12 and 3.13 including the full bind, netguard, loopback-sites, stage-name and receiver files; all new and changed mutant rows plus a 60-row sample, with expectation-in-first-failing-line check; fail-before with raw lines; suppression grep; surprise-exception injection at each `READ_ERRORS` site; the digest-compare cost measured alone.
- **RUN ON LAPTOP (Linux Docker, final head only, after a fresh round finds 0 Blocker and 0 Major):** hadavin-sdk `<final sha>` full pytest plus the complete bind mutant table (279+ rows), py313 and py312, Postgres, CI flags. Windows is not valid evidence.
- Ledger rows PDBIND-r12-1..5 exist; the caller adds one for the follow-up item.
