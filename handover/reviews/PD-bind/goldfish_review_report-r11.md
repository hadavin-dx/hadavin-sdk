Status: resolved

# Goldfish Annotated Review Report, PD Part 2 (bind guard and stand-in detection), round 11

**Target:** `/home/user/build/snap/pdbind-82dd69c1/DIFF.patch` (full), head `82dd69c12f506b9484de7e9ec59593fa943b86e7`, security and mode-safety path (no round cap).
**Inputs:** `pdbind-82dd69c1-design-r11.md` (0 Blocker, 3 Major, 9 Nit) and `pdbind-82dd69c1-codebase-r11.md` (0 Blocker, 5 Major, 12 Nit). Both reviewers read code only; nothing was run by them. Evidence runner a909a11d has not reported; its findings are an addendum for the builder.
**Method:** each finding checked against what the reviewers could read; none contested. 8 Major and 21 Nit findings plus the lead's suppression count merge into 8 issues. Settled from r10 stays settled (single atom judge, one Scan per request, models.now pins, copy/deepcopy of pinned classes, seal value holds derived data only, `_seal_runtime` private, 23 pinned keys, B98 killer by shared `__slotnames__`).
**Binding decisions applied:** Part 2 is the source of `is_stand_in`; no suppressions; fake credentials built from parts; new tests fail on old code or are named `test_pin_*` with a truthful label; builders never commit under `handover/`.
**No Blocker.** Two Majors are possible fail-open or pre-auth code paths (issue 1); they are reasoned from reading, not shown by a test, so the builder must first PROVE or REFUTE each with a test before fixing.

## Handoff counts

- PROPOSE FIX accepted: 8 issues (all Major and the Nits worth the change). CONTEST 0. DECLINE: 3 Nits (listed in issue 8). ESCALATE: 1 (issue 5, broad `except` sites, lead decides).
- Remaining unaddressed: 0. **Round 12 is REQUIRED** (possible fail-open Major on a mode-safety path, no cap).

## Decisions made here

1. **limits / audit / registry / `_evidence` internals (design M1):** decide by a TRACE, not by hope. The builder traces every path from `handle`, `tick` and `on_decided` that reaches a field of these four objects that holds a service (for `Limits`: `store`, `audit`, `registry`). If a path exists, walk them with the same walk and judge service fields with `is_stand_in` (preferred, same choke point as `hooks`). If no path exists, the CHANGELOG states the trace result and a test asserts that the trace set equals the walked set. Either way a test replaces `rt.limits.store` with a real-held stand-in-failing object and expects "counted".
2. **Order inside the walk (codebase M1):** identity first. The weak mark of an object is compared BEFORE its instance dictionary is read; an object not equal to its mark is "changed" and is never entered. Entering is allowed only for an object that IS the recorded one (so a hostile descriptor on a replacement never runs). Also require the exact pinned class for entered objects.
3. **Suppression rule applies to the whole diff against main,** not only new lines of this round. Mutant-row texts that embed a suppression are edited together with the source.

## Prioritized findings

### Issue 1, Major (possible fail-open and pre-auth foreign code), class SEAL-COMPLETE (design M1, codebase M1)
`requests.py:215-228,281`: `registry`, `audit`, `limits`, `_evidence` are sealed by identity only; `rt.limits.store = <real store>` keeps `limits` identical (`Limits.__init__` stores three services and `charge`/`blocked` call them). `requests.py:127-168,174-179,196-203`: `_marks_match` walks current fields first and `_walk` reads `object.__getattribute__(obj, "__dict__")` of every entered object (also `__self__` of bound methods), so a foreign class with `__dict__ = property(...)` runs code before the signature check (still ends 503 by the outer `except`, but it is the foreign-code-before-auth class).
PROPOSE FIX: decisions 1 and 2. Tests (each must FAIL on 82dd69c1 or be named `test_pin_*`): (a) replace `rt.limits.store`, `rt.audit` store, `rt.registry` member, `rt._evidence` member: reads real (counted); (b) a hook field replaced by an object whose class defines `__dict__` as a property that records a call: the call list stays empty and the request is counted. Mutant rows: drop each new comparison; walk before identity.

### Issue 2, Major, class CHANGELOG-TRUTH (design M2, codebase M2, nits 6, 9)
`CHANGELOG.md:271` "exact list of what stays OUTSIDE" is not exact: depth above 4 (identity only), `set`/`frozenset`/`deque` contents, `__kwdefaults__` items, callable-object / `functools.partial` / builtin internals in tools, function `__dict__` and `__wrapped__`, containers matched by exact class and rebuilt. The bullet is one 12,000-character line; "weak references and plain values only" is not literal (strong refs to the `agents` set of text, `_kinds` frozenset, classes).
PROPOSE FIX: walk `__kwdefaults__` items (like `__defaults__`) and function `__dict__` and `__wrapped__`; walk set/frozenset/deque contents or list them; raise the depth limit only if the node cap and its cost figure allow; list every remaining item in the CHANGELOG as its own sub-bullet; for each kept limit add a test that shows the change is NOT seen (so the claim cannot drift) and name `_seal_runtime` and `_RUNTIME_SEALS` as in-process blessing paths; reword the "weak references" sentence literally.

### Issue 3, Major, class LIMITS (codebase M3, nit 10)
`requests.py:137,156-161,165,206-228,85-86`: the node cap is checked only on entry, so a huge dict/list is iterated fully each pre-auth request; no check at seal time (a build over about 5,000 nodes seals, then every public POST is 503, and the refusal names `on_decided` as a held service); no test or mutant for `_WALK_NODES`, `_WALK_DEPTH`, `len(out) == len(marks)`, the `__defaults__` walk, the `__func__` walk, `_EMPTY_CELL`, the atom/state skip, `type(hooks) is not sealed[5]`; the CHANGELOG figures 40 / 95 / 61 ms were not re-measured with the walk.
PROPOSE FIX: count inside the loops and stop at the cap; at seal time raise a build error that says "too many hook objects to check (N over 5,000): refused at build, not at the first request" (build refuses on a public bind; on a loopback-only bind it logs once); the refusal text names the cause ("seal over budget"). Tests and rows for each listed item (one killer each). Re-measure the per-request cost with the walk at 1,000 and 2,400 rows and at the cap, record raw numbers in the evidence, update the CHANGELOG figures with "measured on <date>, this head".

### Issue 4, Major, class TEST-QUALITY (codebase M4, M5, nits 1-4, 9, 12; design nits 3, 4, 7)
`test_bindguard.py:4864-4872` vacuous misnamed test still present beside the real one at `:5345`. False-positive coverage: no real tool call or executed action between the seal snapshots; `Executor`, `ToolBox` and `validate_proposal` cells may hold lazily created state (None to object, cache dict/list) and would 503 a public bind. Also: tautology assert at `:5327`; stale docstring `:4576-4581`; two `_nested` helpers with different off-by-one meaning (`:2636`, `:4606`); dead `_seal` fallback to `R.seal_runtime` (`:5144-5149`); `test_pin_a_real_run_...` label vs 83cdb7a2; `on_decided` not driven in the lazy-name test; `_seal_runtime` accepts any object.
PROPOSE FIX: delete the vacuous test (move any unique assertion into the real one); add one test that makes a real tool call and one executed action (and verify and rollback if reachable) between the snapshots then asserts "still believed"; add a decision through `on_decided` to the lazy-name test; drop the tautology, fix the docstring, one `_nested`, delete the fallback; `_seal_runtime` checks `type(rt) is Runtime` (raise otherwise); pin labels re-measured at 83cdb7a2 with raw lines. If the false-positive test finds a lazily created value, fix it with the same choke point (record an "absent or atom" marker, not a new object compare), not by loosening the compare.

### Issue 5, Major, class SUPPRESSIONS (design M3; lead count 244)
Added lines of the diff against main: `noqa` code comments 19 (src 9: receiver 3, requests 2, bindguard 2, standins 2; tests 10: `BLE001` 11 in total, `S603` 4, `F401` 3, `S311` 1), `noqa` inside mutant-row strings 12, `type: ignore` 212 (src 11, `test_bindguard.py` about 190, mutant strings 9, `tools/server_scan.py` 2), `pragma: no cover` 1 (`do_POST`), `fmt: skip` 0. The delta against 304c3bd3 adds none; they were never counted against main. The project rule is no suppressions.
PROPOSE FIX (builder): remove all. Typing: Protocol, `cast`, typed fakes and correct signatures, never a bare ignore (the 190 test ignores come from a few helper patterns: fix the helper once, grep siblings). `S603`: absolute paths by `shutil.which` and a list argument. `S311`: `secrets` or a counter. `F401`: use or drop the import (a re-export test imports the name and asserts it). `pragma: no cover`: a test or delete. Mutant-row texts: edit with the source. Run `git diff origin/main...HEAD | grep '^+' | grep -E 'noqa|type: *ignore|fmt: *skip|pragma: *no cover'` and report the raw result.
**ESCALATE (lead decision):** the broad `except Exception` sites that the design needs so any failure reads as "counted / 503" and never as served: `requests.py` (about 2, near `:293`, `:329`), `app.py:210`, `standins.py:672` (+ about 2 more), `receiver.py` (3), `bindguard.py` (2). The builder lists each site with the exact exceptions it can name and narrows what it can. For any site it cannot narrow (a hostile object can raise anything, including `BaseException` subclasses of its own choosing): options (a) module-level rule in `pyproject.toml` with the reason, (b) a named tuple plus a test that a surprise error still gives the refusal. Recommended (b); lead decides. No silent inline suppression stays. Note: `contextlib.suppress(Exception)` at `standins.py:225,:229` is the same class in another form and is listed in the same report.

### Issue 6, Minor, class MUTANT-KILLER (codebase nit 8, 10, 11)
Rows embed suppression text (B98 `:1023` and string rows); no rows for the walk items (issue 3); B253 note unverifiable.
PROPOSE FIX: with issues 3 and 5; B253 note says how it was checked or is dropped.

### Issue 7, Minor, class HARDENING (codebase nits 5, 6, 7; design nits 2, 5, 8)
Seal comment `requests.py:59-61` says identity for all sealed members but `_kinds` is by value and `agents` is identity plus content; comment `:88-91` garbled. Every atom is stored by value in a module table, including `Hooks.restored_key` bytes: a second long-lived copy of a secret. A dead weakref matches `None`. `bindguard.py:165` a very long f-string calls `type(crossed).__name__` on a possibly hostile object (second site of a pre-existing pattern).
PROPOSE FIX: store a digest of secret-bearing atoms (keyed per process); dead weakref recorded by a sentinel, "was alive" flag; rewrite both comments; `bindguard.py:165` use a fixed text, never a class name, and add a hostile-`__name__` test (the same class as line 151).

### Issue 8, Nit, DECLINE (three items)
- design nit 1 (`__kwdefaults__`): accepted in issue 2, not declined.
- DECLINE: design nit 3 vacuous last assert wording is covered by issue 4; codebase nit 11 B253 note claim is covered by issue 6; design nit 7 duplicates codebase nit 1. Recorded; nothing separate to fix.
(Declined items add no work; they are folded into issues 4 and 6.)

## ONE FIX BRIEF (single small builder, batch 12; fast-forward only onto `wip/cloud-pd-bind`)

Rules: `PYTHONPATH=<worktree>/src` and print `hadavin_sdk.__file__` before any run; cloud limits (no full suite, focused tests and focused rows only, at most 2 heavy processes); real fail-before runs in `git worktree` at 83cdb7a2 and at 82dd69c1 with raw lines; no suppressions; fake credentials built from parts; never commit under `handover/`; NEVER answer y/yes to a start or confirm prompt of a script that can reach a network or send mail (loopback only; a prompt means STOP and report). Time box: checkpoint every 30 min, stop at 60.

| # | Class | File and change | Test | Mutant row | Fail-before |
|---|---|---|---|---|---|
| A | SEAL-COMPLETE | `requests.py`: trace then walk (or prove) `limits`, `audit`, `registry`, `_evidence`; identity before `__dict__`; exact pinned class before entering | replace each member's service field; hostile `__dict__` descriptor records no call | one row per new comparison; row for walk-before-identity | each fails on 82dd69c1 |
| B | CHANGELOG-TRUTH | walk `__kwdefaults__`, function `__dict__`, `__wrapped__`, set/deque contents; exact OUTSIDE list as sub-bullets; literal wording | one test per kept limit (change not seen); one per closed item | rows for the new walks | closed items fail on 82dd69c1 |
| C | LIMITS | cap inside the loops; build error at seal time naming the cause; refusal text; re-measure cost | build over cap raises; request over cap says "seal over budget" | rows for `_WALK_NODES`, `_WALK_DEPTH`, length check, defaults, `__func__`, `_EMPTY_CELL`, atom skip, hooks class | raw numbers at 1,000, 2,400 rows and the cap |
| D | TEST-QUALITY | delete vacuous test; real tool call + executed action test; `on_decided` in the lazy-name test; tautology, docstring, one `_nested`, dead fallback; `type(rt) is Runtime` check | the new tests | row: lazy attribute written in `on_decided` or in an executed action | labels re-measured at 83cdb7a2 |
| E | SUPPRESSIONS | remove all (list in issue 5); list the ESCALATE sites with exact exceptions | ruff, type check, existing tests green; grep of added lines shows none | none | n/a |
| F | MUTANT-KILLER, HARDENING | issues 6 and 7 | per item | rows named; hostile `__name__` row | by real runs |

Builder reports once when ALL of A-F are done: new head sha, raw fail-before lines, grep result for suppressions on added lines, the ESCALATE list with exact sites, trace result for issue 1, cost figures, anything not done and why.

## Round 12 and evidence for the final head

- **Round 12 is required.** Fresh design and codebase reviewers on a new snapshot; tell them to count suppression markers on added lines against main and to try the foreign-code-before-identity case.
- **Cloud evidence (runner, records only):** focused tests on Python 3.12 and 3.13; new and changed rows plus a 60-row sample; fail-before worktree runs with raw lines; the suppression grep; cost figures.
- **RUN ON LAPTOP (Linux Docker, final head only, after a fresh round finds 0 Blocker and 0 Major):** hadavin-sdk `<final sha>` full pytest plus the complete bind mutant table (263 rows now, 262 on 3.14; more after batch 12), py313 and py312, Postgres, CI flags. Windows is not valid evidence.
- Ledger rows PDBIND-r11-0..8 exist.
