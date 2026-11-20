# G10 v4: a CPU budget for the text fold, the published false-hit rates, and the NOT RUN cost items (lead ORDER 023, escalation E11)

Status: DRAFT v4 for plan review round 3, core-c drafter (opus), 2026-11-20. Nothing is built in the repo. Path class: guard (textnorm, injection).
v4 replaces v3 (`G10-textfold-deadline-v3.md`, kept as the record) and answers `G10-review-2-design.md` (M1-M4, N1-N6) and
`G10-review-2-readiness.md` (B1, M1, M2, N1-N6); section 16 lists every finding and where it is resolved. Every change from v3 is marked
"CHANGED in v4". A builder with no other context builds from THIS file and the four files of `handover/core-c/tickets/G10-files/` (0.1).
Sections: 0 base and files, 1 goal, 2 what exists, 3 design, 4 pins and counts, 5 tests, 6 mutants, 7 PHASES, 8 false hits (part b), 9 NOT RUN
items (part c), 10 decisions, 11 stated limits, 12 measured, 13 NOT verified, 14 what was run, 15 round-1 findings (v3, kept), 16 round-2 findings.

RULE FOR THE BUILDER: build the DEFAULT of every decision D1-D10 (section 10). An alternative is out of scope unless the lead says so.

EVIDENCE LABELS used below: MEASURED (run by the v4 drafter on the v4 prototype, section 14), MEASURED v3 (run by the v3 drafter on the v3
prototype; the code path it measured is unchanged in v4, said per row), BY GREP (re-derived on HEAD f91f56a04 by the v4 drafter), BY CONTENT
(the line is named by its text, not its number), ESTIMATE, NOT RUN.

## 0. Base, and what was read (CHANGED in v4)
- Base: cloud/core-c HEAD f91f56a04 (board 10:39:38Z). CHANGED in v4: v3's base was 78a0c8bcf; between the two, these files G10 touches changed
  (BY GREP, `git diff --stat 78a0c8bcf HEAD`): `src/hadavin_sdk/defaults.py` (G7 round 7: `SPELLED_MAX_CHARS` and its comment; the INSERTION
  comment moved to :247-254), `tests/test_textnorm_meta.py` (the killer-file set at :179-189 is now split over lines), `tests/test_textnorm_round2.py`
  (:222 now carries `# noqa: BLE001`, so `ruff check` of that file is clean), `tests/test_textnorm_q9.py` (+164 lines; the three Q9 re-pointed
  mutants were re-run against it, 14), `src/hadavin_sdk/guard/redact.py` (G7). UNCHANGED (BY GREP, `cmp` of the archives): `guard/textnorm.py`
  (sha256 `e7a93738f10e7ea66e164c929d20c0405a0730d41852e0ff88856720ea6cdbee`, equal to tests/fixtures/textnorm_manifest.json:4),
  `guard/injection.py`, `tests/textnorm_mutants.py`, `tests/test_textnorm.py`, `_fixbatch`, `_callers`, `_order137`, the manifest.
- Line numbers: every "HEAD :n" below is BY GREP on f91f56a04 unless it says "proto" (the v4 prototype, section 14) or BY CONTENT.
- Read for v4 (in addition to v3's list): the two round-2 reviews; v3's prototype scripts and test file; HEAD's textnorm.py 555-620, 1350-1380,
  1440-1540; injection.py 20-240; redact.py 1295-1380; k1b/loop.py 130-210; the six call sites; tests/test_textnorm_meta.py 85-380;
  tests/textnorm_mutants.py 960-1000 (`__main__`); evidence/G1-false-hits-and-cost.md 100-166 (Round 2).

### 0.1 The build files (CHANGED in v4: readiness B1). In `handover/core-c/tickets/G10-files/`, written by the v4 drafter from the v4 prototype:
| file | what | sha256 |
|---|---|---|
| `test_textnorm_deadline.py` | the new test file, 359 lines, 11 tests, `ruff format` + `ruff check` clean; copy it to `tests/test_textnorm_deadline.py` | `06c417d16ae0e1f73d9cc835a3d8262de035a10d6dc7cfb07d44e0193e995fa8` |
| `g10-v4-src.diff` | unified diff, HEAD -> prototype, of `src/hadavin_sdk/guard/textnorm.py`, `guard/injection.py`, `defaults.py` (38 hunks, post-`ruff format`) | `3bf75f6235ac57fe3bd144991235c2cc6cb48bf9f19eda22692e33364ed0d620` |
| `g10-v4-tests.diff` | unified diff, HEAD -> prototype, of the pin edits (test_textnorm, _fixbatch, _callers, _order137, _round2, _meta), `tests/textnorm_mutants.py` and the manifest | `a6126b0de36adcb55c34cee9252133e726fe0b0fb658d6908a6354f9debd711a` |
| `changelog_item.md` | the CHANGELOG item, 7 lines starting with one blank line; `<NEW-HASH>` is the builder's sha256 | `e22a98e75e04117ad169a7eee4a7fdfccedd6abfbcb567b0578937564d56ddeb` |
Both diffs pass `git apply --check` on HEAD f91f56a04 (MEASURED). They ARE the exact edits; the code quoted in sections 3-6 is copied from them.
These replace v3's pointer to the drafter's scratchpad. They are v4 files: the v3 prototype test file (`scratchpad/g10v3/files/test_textnorm_deadline.py`)
uses the absolute `deadline=` API that v4 drops (M1), so it was adapted, not copied byte for byte (decision for the lead, 10 L1).
The prototype textnorm.py sha256 (LF) is `9f7e0ad0c087e4d61e7790e0eda9e26069694a8c8e4a7a02549b5bc98362b237`; the diff applied to HEAD gives exactly that
file, so the builder's hash equals it unless a byte differs; the manifest and the CHANGELOG take the builder's own `sha256sum` after the last edit.

## 1. Goal (CHANGED in v4)
(a) The DENY scan of the fold (`scan_holds`) and the injection read (`scan_views_no_value` through `RegexDetector`) stop at a CPU BUDGET given
in seconds (`budget_s`), in the redactor's style: the call reads `time.thread_time()` once at its start, ON THE THREAD THAT RUNS IT, and then at
fixed points between whole passes; refusal at or past start + budget (fail closed: never a "no hit", never a part of the views). With no budget
(the default, None) every result is what it is today and no clock is read. CHANGED in v4 (design M1): v3 took an absolute `deadline` value; a
value read on one thread meant nothing on another (the callers run checks in `asyncio.to_thread` workers), so v4 takes a relative budget that
the callee turns into a deadline on its own thread. CHANGED in v4 (design M2): v3 said "the caller keeps its wall-clock guard"; no call site
has one (2.3), so the text now says: the budget is CPU only and no call site of the injection check bounds the check by wall clock.
(b) The measured false-hit rates are published with date, unit, versions and caveats, and the sentences that say "about 1 percent" or "not
measured" are corrected. CHANGED in v4 (design M4): "UPPER BOUND" is restricted to the one sense in which it holds (8.1).
(c) The NOT RUN items of the cost evidence that fit the box are named, sized and given a default.
OUTCOME the builder delivers: the source, test, mutant and pin edits of sections 3-7 (the two diffs and the test file of 0.1), the defaults.py
comments and the CHANGELOG item (8.2, 8.3). The SECURITY wording (8.4) is applied by the SECURITY wording lane (D9); the lane's reviewer
verifies it against 8.4; the G10 result review checks only that the builder did NOT edit those files.

## 2. What exists today (HEAD)
### 2.1 No clock in the fold
- grep of guard/textnorm.py and guard/injection.py for `time`, `thread_time`, `monotonic`, `perf_counter`, `deadline`, `timeout`: only the
  docstring of `scan_keyset` (textnorm.py:1272, "there is no clock or deadline"). Neither file imports `time`. (BY GREP)
- Cost (evidence G1 B; CPU seconds): one `scan_holds` on 262,144 ASCII characters 0.36 s; 1 percent non-ASCII about 0.9 s; 236,879 distinct
  non-ASCII characters 4.8 to 5.5 s. `RegexDetector` on 2,000,000 characters 3.6 s (ASCII), 9.6 s (1 percent non-ASCII). CHANGED in v4: a
  constructed 2,000,000-character text whose pieces the chunked read halves (runs of U+FDFA) takes 185 s (MEASURED, 12.4): the evidence's
  figures are not the worst case.
- The weight cap (`TEXTNORM_MAX_CHARS` = 262,144, `_checked` :560, `TextTooLong`) bounds the SIZE of one call, not its time. A text longer than
  262,144 characters is refused from its length alone before any per-character work (textnorm.py:566).

### 2.2 Where the time of one scan goes (v3 2.2, unchanged code)
`scan_holds` = `_checked` (the weight; memoised per long text; 0.55 s on the distinct text when first seen) + the value's needles
(`_needles_or_refuse`) + `_text_bundle` (:1353) = `_readings` (:724; 2 texts x 2 `_prefix` passes + 3 `_finish`) + `_squeezed` (:1054) + `_scan_keys`
(:1287; 2 marks variants x up to 4 tag texts x 2 steps, each `_converge`d (:1225) over at most `TEXTNORM_MAX_PASSES` = 3 passes) + the needle loop
+ the insertion loop (`_holds_with_one_insertion`, :1444). SOUNDNESS OF THE READING POINTS: NFKD (`unicodedata.normalize("NFKD", text)`, :742)
and NFKC (in `_prefix`, :695) are single C calls over the whole text; a reading is placed only BETWEEN such whole passes, so no normalisation unit
is ever split and no chunk boundary exists.

### 2.3 Who calls what (grep of the whole of src; BY GREP)
| function | callers in src | today's time bound | what a TextnormError does there |
|---|---|---|---|
| `scan_holds`, `scan_views`, `scan_cache`, `register_value`, `scan_needles` | NONE (tests and evidence scripts only) | none | the docstring rule: a DENY caller REFUSES |
| `scan_views_no_value` | guard/injection.py `_holds` (:72), `RegexDetector._read` (:127), `RegexDetector._fit` (:144) | none (`TEXTNORM_INJECTION_MAX_CHARS` = 2,097,152, defaults.py:285, is a size) | `_read` (:129) and `_fit` (:145, :155) CATCH `TextTooLong` only; anything else reaches `injection_check` (:217-233), which flags the run `guard_unavailable` |
| `fold`, `fold_view` | guard/redact.py `_fold_scan` (:1340) and the per-match helpers | the redactor's deadline; first read after the view building, `self._over_budget(started)` redact.py:1375 | `redact_text` turns any non-RedactionError into `RedactionError(type name)` |
| `require_pinned_unidata` | app.py:132 | constant | `UnidataMismatch`: refuse to start |
| `without_spacing_marks` | guard/runmap.py | linear, under the redactor's deadline | as above |
`injection_check` has SIX call sites (BY GREP): runtime/agent_loop.py:323 (`_screen`), k1b/loop.py:205, approvals/requests.py:37,
approvals/cards.py:79, guard/judge.py:107 (`qualify`, the golden set of a judge detector) and guard/injection.py:202 (`AnyOf.check`). All six go
through `injection_check`, so a `DeadlinePassed` is a flag at every one (fail closed). CHANGED in v4 (design M2): NO call site bounds the check
by wall clock. k1b/loop.py checks its case's wall clock (`clock() - started > timeout_s`, :151) only BETWEEN steps, never during a check; the
other five do not wrap the check in any wall-clock limit (BY GREP of the five files for `timeout`, `wait_for`, `to_thread`; the `timeout` hits
in approvals/requests.py are approval-step expiry times, not a bound on the check). The scan cache's own docstring
(textnorm.py:1339) names `asyncio.to_thread` as a way a scope is shared across threads.

### 2.4 The redactor's deadline (the style copied)
- `runmap` sets ONE deadline `started + REDACT_BUDGET_S` (6.0) from `time.thread_time()` and passes it as `redact(_deadline=)` (runmap.py:564,
  BY GREP); `_Redactor._over_budget(deadline)` (redact.py:1299, `@staticmethod` at :1298): `InputTooLarge` once the CPU clock passed it; read at
  fixed points inside loops. Tests pin the readings with a stepping clock patched on the MODULE attribute (tests/test_redact_settle_loop.py:687
  `_stepping_clock`) and `CountedClock` (tests/test_redact_fold_budget.py:186).
- A refusal is fail closed: nothing is shown; a legitimate document in the same text is lost for that run.

## 3. Design (part a)
### 3.1 The clock is read INSIDE textnorm.py (D1; unchanged from v3)
The callers' loops cannot bound the cost: the injection read of a text under the cap is ONE call of `scan_views_no_value` (5.8 s on the
distinct text), and a `scan_holds` consumer makes one call per value. Inside textnorm the overrun is the longest stretch between two readings
(12.2). So textnorm.py changes, and with it the hash, the manifest, the CHANGELOG re-copy list, the public names and the mutant list (section 4).

### 3.2 API (keyword-only; default None = unchanged) (CHANGED in v4: design M1, N4)
- `scan_holds(*, text: str, value: str, budget_s: float | None = None) -> bool` and
  `scan_views_no_value(raw: str, *, budget_s: float | None = None) -> tuple[str, ...]`.
- `budget_s`: None, or an `int` or `float` (`type(budget_s) in (int, float)`, so not a `bool`) that is FINITE (`math.isfinite`: NaN and both
  infinities are refused). Anything else raises `NotText("budget_s must be a finite number of CPU seconds or None")` BEFORE any clock reading
  and any work. Zero or a negative number is accepted: a budget already spent (the first reading after the size rule raises).
- WHY RELATIVE (M1): the callee reads `time.thread_time()` itself, once, as its first act after the argument rule (`_deadline_of`), so the
  deadline is always on the clock of the thread that runs the scan. A caller in an `asyncio.to_thread` worker gets the worker's clock; no value
  read on one thread can reach a scan on another, because the public API takes no clock value at all. Pinned by test D-10 (two threads, a
  per-thread clock) and mutant 254 (the budget taken as an absolute deadline).
- The private chain still carries an absolute `deadline` (a value read by `_deadline_of` in the same call, on the same thread, never stored).
- ORDER OF REFUSALS (N4): the argument rule of `budget_s` first, then the start reading, then `_checked` (type and size of the text and the value),
  then the first deadline reading. So a non-`str` text with a spent budget raises `NotText`, a 300,000-character text with a spent budget raises
  `TextTooLong` (MEASURED by probe, 14 item 7; not a pinned test). v3 read the clock before `_checked` (its P1) and gave `DeadlinePassed` there.
- NOT given a budget (D3): `scan_views` (parameters pinned: tests/test_textnorm_fixbatch.py:280 `list(sig.parameters) == ["raw", "value"]`),
  `fold`, `fold_view`, `fold_views`, `squeeze`, `squeeze_views`, `identity_key(s)`, `could_be_same_person`, `allow_equal`, `names_equal`,
  `register_value`, `scan_keyset` (parameters pinned, tests/test_textnorm_scan.py:91), `scan_needles`, `has_hidden_channel`, `has_mixed_script`.

### 3.3 The error: `DeadlinePassed(TextnormError)` (D6), directly BEFORE `class EmptyView` (HEAD :381; proto :396)
Docstring (proto, exact): "The scan used up the caller's CPU budget (``budget_s`` seconds of ``time.thread_time()`` of the thread that runs the
call, counted from the call's start); nothing was decided. A DENY caller REFUSES, as for any ``TextnormError``; the injection check flags the run.
It is not a ``TextTooLong``: a reader that halves a text that is too long must not start more work after the deadline. The message holds no text,
no value and no length." (CHANGED in v4: the first sentence.) Message `"the scan passed its deadline"`. In `__all__` (HEAD :309) directly after
`"CoverageRefused",` (HEAD :315) and before `"EmptyView",` (HEAD :316).
- NOT a `TextTooLong`: `_read` and `_fit` catch `TextTooLong` and then read the text in pieces or halve a piece. Mutant 243 (the class made a
  `TextTooLong`): 4 calls of `scan_views_no_value` instead of 2 on a 300,000-character text with a spent budget (MEASURED, killed by D-6).
- Not runmap's `InputTooLarge`: textnorm.py is byte-copied with the `TEXTNORM_*` constants only; an import of runmap would break the copy and add
  a cycle. A future redaction consumer converts (3.6).
- The refusal lint (tests/test_textnorm_callers.py:40-48) builds `BANNED` from `__all__`, so `DeadlinePassed` is banned in handlers at once and the
  pinned set (test at :214, the names up to :226) gets `"DeadlinePassed"` (section 4). `REFUSAL_HANDLERS` is unchanged.

### 3.4 Reading points (exact placement) (CHANGED in v4: the start replaces P1; `>=`)
Two helpers, directly AFTER `_checked` (HEAD :560-575) and before the comment `# COMBINING GREEK YPOGEGRAMMENI` (HEAD :578); the clock is read
through the module attribute `time` (`import time` after `import threading`, HEAD :297; `import math` after `import logging`, HEAD :294), so a
test replaces `textnorm.time`. Proto :600-614, exact:
```python
def _deadline_of(budget_s: float | None) -> float | None:
    """The ``budget_s`` rule of ``scan_holds`` and ``scan_views_no_value``: None (no deadline, no reading), or a finite ``int`` or ``float``
    that is not a ``bool``. The deadline is the CPU clock of the thread that runs the call, read here once, plus the budget (zero or less: spent)."""
    if budget_s is None:
        return None
    if type(budget_s) not in (int, float) or not math.isfinite(budget_s):
        raise NotText("budget_s must be a finite number of CPU seconds or None")
    return time.thread_time() + budget_s


def _tick(deadline: float | None) -> None:
    """One reading of the calling thread's CPU clock (``time.thread_time()``, through the module attribute so a test can replace it):
    ``DeadlinePassed`` once the clock has reached the deadline (fail closed); nothing at all without a deadline."""
    if deadline is not None and time.thread_time() >= deadline:
        raise DeadlinePassed("the scan passed its deadline")
```
`>=` (CHANGED in v4): a budget of exactly 0 raises at the first reading even when the clock has not moved between the start and that reading.
The stepping clock of the tests returns integers and the budgets are k - 0.5, so `>` and `>=` give the same sequences there.
| point | function | exact place | conditional? | readings |
|---|---|---|---|---|
| S start (CHANGED in v4; replaces v3's P1) | `scan_holds`, `scan_views_no_value` (inside `_deadline_of`) | the first statement: `deadline = _deadline_of(budget_s)`, BEFORE `_checked` and the cache lookup | only with a budget | 1 |
| P2 after the size rule | same | right after `_checked(...)` | no | 1 |
| P2b after the value's needles | `scan_holds` | right after `needles = _needles_or_refuse(value, scripts)` | no | 1 |
| P3 prefix passes | `_readings` | inside `for marks, text in enumerate(texts):` after the `marks_only` skip: (a) before `nfkd = unicodedata.normalize("NFKD", text)`; (b) after `with_iota = _prefix(...)`, before `prefixes = {` | NO: (b) is read whether or not the second `_prefix` runs | 2 per text per `_readings` call; `scan_holds` calls `_readings` twice per bundle |
| P4 per squeeze view | `_squeezed` | first statement of the body of `for view in _views(..., deadline=deadline):` | no | one per distinct view (at most 6) |
| P5 per converge pass | `_converge` | first statement of the body of `for _ in range(passes):` | no | at most 3 per scan key, at most 16 keys |
| P6 after the views | both | right after `bundle = _text_bundle(text, deadline)` / `_text_bundle(raw, deadline)` | no | 1 |
| P7a insertion | `scan_holds` | after `if not inserts: return False`, before `script_views = {...}` | only when the value has a script needle in the insertion band | 1 |
| P7b per script view | `scan_holds` | first statement of `for view in script_views:` | same | one per script view |
| P7c insertion hits | `_holds_with_one_insertion` | in BOTH `while start != -1:` loops, `hits += 1` then `if not hits % 4096: _tick(deadline)` (one counter for both halves) | every 4,096 hits | hits // 4,096 |
Unread stretches by design: `_checked` (the weight, between S and P2), the value's needles (between P2 and P2b), `_without_spacing_marks` and the
comprehensions of `_scan_keys`, the final `"".join` of `_scan_key`, `_all_views` / `_pairs_from` and the script views (between P6 and P7a), the
needle loop (C speed). Their size is in the measured longest stretch (12.2, 12.3). Reading counts (MEASURED, 12.1): 19 for T, 18 for T2, 16 for
`scan_views_no_value(T)`: the same as v3 (S takes P1's place in the sequence).

THE PRIVATE CHAIN (CHANGED in v4: readiness N1, the exact keyword order; mutant old strings depend on it). Every new parameter is
`deadline: float | None = None`, LAST in its signature, and every forwarded keyword `deadline=deadline` is LAST in its call:
`_readings(raw, *, casefold, collapse_ws, marks_dropped=False, marks_only=False, deadline=None)`;
`_view_pairs(..., marks_only=False, scripts=frozenset(), deadline=None)` and its call of `_readings(..., marks_dropped=marks_dropped,
marks_only=marks_only, deadline=deadline)`; `_views(..., marks_dropped=False, scripts=frozenset(), deadline=None)` and its call of `_view_pairs(...,
marks_dropped=marks_dropped, scripts=scripts, deadline=deadline)` (so the lines read `        scripts=scripts,` then `        deadline=deadline,`:
the old string of re-pointed mutant 110, 6.2); `_squeezed(raw, *, loose=False, deadline=None)` calls `_views(raw, casefold=True, collapse_ws=False,
marks_dropped=True, deadline=deadline)`; `_converge(text, step, deadline=None)`; `_scan_key(text, step, deadline=None)` calls
`_converge(text, step, deadline)`; `_scan_keys(raw, deadline=None)` calls `_scan_key(text, step, deadline)` POSITIONALLY; `_text_bundle(raw,
deadline=None)`; `_holds_with_one_insertion(view, needle, deadline=None)`. `_all_views` is NOT given a deadline: both entry points build the
bundle with `_text_bundle(..., deadline)` and pass it in; `_all_views(text, scripts, bundle)` stays byte for byte. The exact text is in
`g10-v4-src.diff`. Test doubles: `_counting_readings` (order137:345) and the fixbatch spy (:253-260) take `*args, **kwargs`; test_textnorm_scan.py
calls `_converge(ch, _pass_b)` (default None); the `_one_off` spies (fixbatch:611, round1 BY CONTENT) are untouched; the `work(*args, **kwargs)`
stub (test_textnorm.py:2930) is fine; the `_scan_key` stub `key(tag_text, step)` (order137:494) is widened (section 4).

### 3.5 Cache, determinism, overrun, cost (CHANGED in v4: design M3)
- `scan_cache()`: the bundle is built under the deadline of the call that builds it and stored only after a complete build (the store follows the
  build, HEAD :1371-1378; D-5). A call that finds the bundle cached reads S, P2, P2b, P6, P7a, P7b: six readings for T and V (D-4).
- Determinism: with `budget_s=None` no clock is read; results identical (D-1, 188 corpus rows x 3). With a budget a call returns EXACTLY what it
  returns without one, or raises `DeadlinePassed`; WHICH depends on the machine's speed (as for the redactor): stated.
- Overrun (CHANGED in v4): stated ONLY as measured maxima on named texts, not as a bound for every text (12.2-12.4):
  - `scan_holds` / `scan_views_no_value` on the 236,879-character text of distinct letters: longest stretch 0.52 to 0.63 s (MEASURED v3 and v4; S
    or P1 to P2, the weight of a first-seen text); sweeps of 12 budgets: overruns at most 0.21 s.
  - CHANGED in v4: 262,144-character texts of Devanagari words with spacing marks (Mc 9.1 %), of tag-character words (tags 44.6 %) and of both
    mixed, values `Zqxvbn` and a Devanagari name: longest stretch at most 0.24 s (a converge pass), sweeps at most 0.22 s (MEASURED, 12.3).
  - The value work (P2 to P2b) is outside these figures: 7.2 to 7.5 s for a value of 236,879 distinct letters, 0.58 to 0.63 s for 262,144 ASCII
    letters (MEASURED v3 and v4). A protected value comes from the operator's registration (stated limit, 11).
- Injection: a text over 262,144 characters is refused by `_checked` from its LENGTH before any per-character work, so the injection read never
  folds more than one piece (`TEXTNORM_INJECTION_CHUNK_CHARS` = 32,768) or one window per `scan_views_no_value` call. Between two calls `_score`
  runs `_RX.search` and `_SQUASH.sub` over the piece and its views; after the last piece the raw squash over the whole text (injection.py:177)
  runs with no reading. Decision D10: NO reading in `_score`. MEASURED maxima: the longest stretch of a whole 2,000,000-character read is 0.04 to
  0.13 s on six texts (MEASURED v3), 0.05 to 0.11 s on three `ignore all`-dense texts and 0.26 s on the halved U+FDFA text (MEASURED, 12.4); the
  regex work of one `ignore all`-dense piece and its views is 0.011 to 0.020 s. Sweeps: CPU after the budget 0.001 to 0.020 s; at budget 30.0
  the U+FDFA text was flagged at 30.08 s.
- Cost of the readings: one `time.thread_time()` read 0.28 to 0.31 us (MEASURED v2); ratio of bests on 262,144 ASCII characters with a budget vs
  without: 1.027 (`scan_holds`) and 0.957 (`scan_views_no_value`), best of 5 each, i.e. within the noise of the box (MEASURED).

### 3.6 Callers (CHANGED in v4: the injection passes the seconds LEFT)
guard/injection.py (exact text in `g10-v4-src.diff`; proto line numbers):
- `import time` after `import re` (proto :10).
- `_deadline()` after `_check_geometry` (HEAD :41-61), proto :65: unchanged from v3 except its first docstring sentence (the CPU clock "of the
  thread that runs the check, from now (``time.thread_time()``; read and used in that one call, never handed to another thread)"). It reads
  `defaults.INJECTION_BUDGET_S`; None gives None; `type(budget) not in (int, float) or not 0 < budget < float("inf")` raises
  `ValueError("defaults.INJECTION_BUDGET_S must be a positive number of CPU seconds or None")`; else `return time.thread_time() + budget`.
- NEW in v4, proto :80, exact:
```python
def _left(deadline: float | None) -> float | None:
    """The CPU seconds left before ``deadline`` (from ``_deadline``, in the thread that runs the check), as the ``budget_s`` of one
    ``textnorm.scan_views_no_value`` call; None without a deadline. Zero or less: that call raises ``DeadlinePassed`` after its size rule."""
    return None if deadline is None else deadline - time.thread_time()
```
- The chain (every new parameter `deadline: float | None = None`, positional-or-keyword; the two `@staticmethod` generators stay static): `_holds`,
  `_start_of_next`, `_read`, `_fit`, `_score` carry the check's absolute deadline (read in `check`, used in the same synchronous call on the same
  thread; the generators are consumed by `_score` in that call). The three fold calls become
  `textnorm.scan_views_no_value("|" + window + "|", budget_s=_left(deadline))` (proto :94),
  `yield text, textnorm.scan_views_no_value(text, budget_s=_left(deadline))` (proto :149) and
  `yield piece, textnorm.scan_views_no_value(piece, budget_s=_left(deadline))` (proto :166). `RegexDetector.check`:
  `        score = self._score(text, _deadline())` (proto :207). The drift of the relative hand-over: each fold call's deadline is the check's
  deadline plus the time between `_left`'s reading and the fold's start reading (two consecutive reads, about 1 us; it does not add up over calls,
  each call re-reads). Tests that call `_score` / `_read` / `_fit` directly keep working (default None). The `Detector` protocol is unchanged.
- injection.py never names `textnorm.DeadlinePassed` (so the allow-list of order137:332-341, `seen <= allowed` at :341, stays as is).
- guard/redact.py: NOTHING (D8). Its unread stretch is the view building of `_fold_scan` (:1340) before redact.py:1375; its input is capped
  (`runmap.redact_text`, runmap.py:197 length, :222 expanded length).
- The consumer rule (in the `scan_holds` docstring, quoted in 3.7): pass a budget, convert `DeadlinePassed` to the consumer's own refusal at the call.

### 3.7 The source change of textnorm.py (exact text: `g10-v4-src.diff`; prototyped, `ruff format` and `ruff check` clean)
1. `import math` after `import logging` (HEAD :294); `import time` after `import threading` (HEAD :297).
2. `"DeadlinePassed",` in `__all__` after `"CoverageRefused",`; the class of 3.3 before `class EmptyView`; `_deadline_of` and `_tick` (3.4) after
   `_checked`.
3. Module docstring: HEAD :126-127 (37 names, `DeadlinePassed` in the error list) and, after HEAD :249 (`...that stays a limit.`), a 12-line
   paragraph "DEADLINE (G10, ORDER 023): ..." (proto :250-261; CHANGED in v4: it describes `budget_s`, the start reading on the thread that runs the
   call, `>=`, and no P1; no `"3.13"` or `"15.1.0"` literal, test_textnorm.py:3169).
4. `scan_keyset` docstring HEAD :1272: `there is no clock or deadline;` becomes `it reads no clock (the budget is` + new line
   `    ``scan_holds``'s and ``scan_views_no_value``'s);`.
5. The parameters and readings of 3.4. `scan_views_no_value` (proto :1463-1472) body: `deadline = _deadline_of(budget_s)`, `_checked(raw)`,
   `_tick(deadline)`, `bundle = _text_bundle(raw, deadline)`, `_tick(deadline)`, `return tuple(view for view in _all_views(raw, frozenset(), bundle) if view)`;
   docstring last line `scan that reads no script. ``budget_s``: see "DEADLINE" in the module docstring (None: no clock is read)."""`.
6. `scan_holds` (proto :1570-1610). THE DOCSTRING LINES, EXACT (CHANGED in v4: readiness B1; HEAD :1517 is extended and four lines follow it, proto
   :1581-1585):
```
    hundreds of values at the cost of one text pass, call this inside ``with scan_cache():``. ``budget_s``: None (no clock is read) or the
    CPU seconds this call may spend, counted from its start on the thread that runs it; past them the scan raises ``DeadlinePassed`` (see
    "DEADLINE" in the module docstring). A consumer passes its own budget (the redactor: the seconds left before its deadline) and converts at
    the call, ``except textnorm.DeadlinePassed: raise InputTooLarge("InputTooLarge") from None``, with that function listed in the refusal
    handlers of ``tests/test_textnorm_callers.py``."""
```
   The body (proto :1586-1610):
```python
    deadline = _deadline_of(budget_s)
    _checked(text, value)
    _tick(deadline)
    scripts = _value_scripts(value)
    needles = _needles_or_refuse(value, scripts)
    _tick(deadline)
    bundle = _text_bundle(text, deadline)
    _tick(deadline)
    views = [view for view in _all_views(text, scripts, bundle) if view]
    if any(needle in view for view in views for _kind, needle in needles):
        return True
    limit = defaults.TEXTNORM_INSERTION_MAX_CHARS
    inserts = [
        needle
        for kind, needle in needles
        if kind == "script" and _insertion_minimum(needle) <= len(needle) <= limit
    ]
    if not inserts:
        return False
    _tick(deadline)
    script_views = {_script_view(view, scripts) for marks, view in bundle[0] if marks} - {""}
    for view in script_views:
        _tick(deadline)
        if any(_holds_with_one_insertion(view, needle, deadline) for needle in inserts):
            return True
    return False
```
7. Prototype sha256 (LF): `9f7e0ad0c087e4d61e7790e0eda9e26069694a8c8e4a7a02549b5bc98362b237` (CHANGED in v4).

### 3.8 defaults.py (CHANGED in v4: design M2, N1)
After `TEXTNORM_INJECTION_MAX_CHARS = MAX_BUNDLE_CHARS` (HEAD :285), exactly (proto :295-301):
```python
# INJECTION_BUDGET_S (guard.injection, G10): the CPU seconds (time.thread_time() of the thread that runs the check) that ONE RegexDetector check,
# one detector call on one text, may spend in the text fold; past them textnorm raises DeadlinePassed and the run is flagged guard_unavailable
# (fail closed). Per check, not per run: a run that checks many texts (k1b: one check per tool result) may spend it once per check. None: no
# deadline. A positive finite number; anything else flags every run. 30.0: about 1.9x the slowest text of 2,000,000 characters measured on the
# build box (16.0 s; G10 ticket, D4); on a machine more than about 1.9x slower that text is flagged on every run. CPU only: waiting for the GIL,
# a lock or I/O does not count, and no call site of the injection check has a wall-clock limit.
INJECTION_BUDGET_S = 30.0
```
(If the lead picks another value, only the number and "about 1.9x" change.) The false-hit comment is 8.2.

## 4. Pins and counts that change (exact text: `g10-v4-tests.diff`; every row run green on the prototype, section 14)
| pin | where (HEAD, BY GREP) | today | after G10 |
|---|---|---|---|
| sha256 of guard/textnorm.py | tests/fixtures/textnorm_manifest.json:4 | `e7a937...cdbee` | the builder's `sha256sum` after the last edit (prototype `9f7e0ad0...b237`); `test_the_manifest_pins_the_files_a_demo_copies` (tests/test_textnorm.py:3246) is red from the first edit of textnorm.py to phase 5 |
| the hash in the CHANGELOG | CHANGELOG.md:651 | old hash | the new item appended after :655 (the last line) lists the new hash (8.3); :651 stays as the record |
| the mutant sentence | CHANGELOG.md:638 ("...The list holds 240 mutants in") and :639; meta test i (tests/test_textnorm_meta.py:269, the assert at :273) | 240 | the new item: "... The list holds 255 mutants in" ENDS a line, "  `tests/textnorm_mutants.py` ..." starts the next (CHANGED in v4: 255) |
| public names | tests/test_textnorm.py:1200 `..._listed_thirty_six():`, list :1202-1239 (`"CoverageRefused",` :1208), `== 36` at :1241 | 36 | `..._listed_thirty_seven():`; `"DeadlinePassed",` after `"CoverageRefused",`; `== 37` |
| module docstring count | tests/test_textnorm_fixbatch.py:665 (def), :666 docstring, :668 `== 36` | 36 | "The 37 names (34 of the fold, 3 for the fold scan of the redactor)" and `== 37` |
| the call lint | tests/test_textnorm_fixbatch.py:323 `assert nargs == 1 and not kws, (` in the test at :298 | red once injection.py passes a keyword | `assert nargs == 1 and kws <= {"budget_s"}, (` (CHANGED in v4: `budget_s`) |
| banned names | tests/test_textnorm_callers.py, test at :214, `"CoverageRefused",` :226 | 8 names | `"DeadlinePassed",` after it; `REFUSAL_HANDLERS` stays 5 |
| the `_scan_key` stub | tests/test_textnorm_order137.py:494 `def key(tag_text, step):` in `_stub_keys` (:483), used by the test at :504 | `TypeError` once `_scan_keys` passes the deadline | `def key(tag_text, step, deadline=None):` |
| allow-list of textnorm names in src | order137:332-341 | unchanged | unchanged |
| the ceiling perf row | tests/test_textnorm_round2.py:344, `start = time.perf_counter()` :355 | runs under the default budget | gains `monkeypatch`, and `monkeypatch.setattr(defaults, "INJECTION_BUDGET_S", None)` before :355 (ruff-formatted form in the diff) |
| `TESTS` and the killer files | tests/textnorm_mutants.py:36-40 | `TESTS = [T, G, SC, SB, FB, O, RO, R2, Q9, D]` (:40) | `DL = "tests/test_textnorm_deadline.py"  # ...` before `R2 = ...` (:37); `TESTS = [T, G, SC, SB, FB, O, RO, R2, Q9, DL, D]` |
| the list's docstring | tests/textnorm_mutants.py:12 | 240 | "255 mutants (..., 9 of round 1 and 5 of round 2, and the 15 of G10, the deadline of the fold, last), in the order" (CHANGED in v4) |
| split | `split_counts()` | (228, 12) | (243, 12) (MEASURED; CHANGED in v4: 15 G10 mutants, none wording-only) |
| meta test | tests/test_textnorm_meta.py, 4.1 | 240 | 255 |
| unchanged, checked by running | `scan_views` parameters (fixbatch:280), `scan_keyset` parameters (scan:91), the cache read counts (fixbatch:247-272, order137 `_counting_readings` :345), siblings, importers | — | green on the prototype (1,247 passed, 14) |
| defaults.py | new `INJECTION_BUDGET_S` (3.8); the INSERTION comment (8.2) | absent | not hashed; not a `TEXTNORM_*` constant |

### 4.1 tests/test_textnorm_meta.py (CHANGED in v4: 15 G10 mutants; HEAD line numbers BY GREP; exact text in `g10-v4-tests.diff`)
- :90 the def name becomes `test_a_the_list_has_255_mutants_..._77_of_the_p1b_fix_batch_and_15_of_g10_with_unique_names` (the full name is in the diff);
  :92 `== 255`; :97 `len(names[28:]) == 227` (the comment of :98 gains ", and the 15 of G10 last"); :123 `len(names[163:240]) == 77`; :149
  `for n in names[163:240]`; after :150 three lines: `assert len(names[240:]) == 15 and all(n.split(":")[0] in {"deadline", "injection"} for n
  in names[240:]), "the 15 of G10 (the deadline of the fold)"`.
- :179-189 (the killer-file set, already one name per line at HEAD): `        mm.DL,` after `        mm.Q9,` (:188).
- :199 after `        TESTS / "test_textnorm_app.py",`: `        TESTS / "test_textnorm_deadline.py",`.
- :214 `assert len(rows) == 255`; :377 `assert behaviour + wording == len(mm.M) == 255`.
- :175-177 (`TESTS[:3]`, `TESTS[-1] == D`, no perf/meta/notices) hold unchanged.

## 5. Tests: `tests/test_textnorm_deadline.py` (CHANGED in v4: 11 tests; the file is `G10-files/test_textnorm_deadline.py`, copy it as is)
No conftest fixture (the mutation runner runs pytest with `--noconftest`). Constants (unchanged from v3): `T = "the summary of " + "жизнь " * 200 +
"密的码测试"` (holds V with one Han letter inserted), `T2 = "密码" * 5_000` (never V), `V = "密码测试"`; `POINTS_T`, `POINTS_T2`, `POINTS_NO_VALUE`
are v3's sequences unchanged (the first `scan_holds` / `scan_views_no_value` entry is now the start reading S instead of P1).
THE STEPPING CLOCK: `SteppingClock.thread_time()` returns n at reading n and records `sys._getframe(2).f_code.co_name` (frame 0 `thread_time`,
1 `_tick` or `_deadline_of`, 2 the reading point); `_clock(monkeypatch)` patches the module attribute `textnorm.time`. ARITHMETIC (CHANGED in v4):
reading 1 is the start, so `budget_s=b` gives the deadline 1 + b; with `b = k - 0.5` the deadline is k + 0.5, readings 2..k pass and reading k + 1
raises, so `clock.reads == k + 1` after the raise, exactly as v3's `deadline=k + 0.5`. A large budget is `1e9`. NEW: `ThreadClock` (per thread:
reading n of a thread returns n, plus 1,000 on the thread that made the clock).
| id | function (CHANGED in v4 where renamed) | what it asserts | tags |
|---|---|---|---|
| D-1 | `test_no_budget_and_a_large_budget_give_every_answer_of_today` | 188 string rows x 3 ways: the answer or error class with no argument, `budget_s=None`, `budget_s=600.0` is the same; the views of `scan_views_no_value` too | `DEADLINE-NONE` |
| D-2 | `test_a_spent_budget_raises_and_never_answers` | `budget_s=-1.0` raises `DeadlinePassed` for `("a summary", "Mary")`, `("密的码测试", V)` and `scan_views_no_value("a summary")`; False fails with DEADLINE-NOT-FALSE, any other answer with DEADLINE-SPENT | `DEADLINE-SPENT`, `DEADLINE-NOT-FALSE` |
| D-3 | `test_every_reading_point_of_scan_holds_is_pinned_and_each_one_refuses` | `budget_s=1e9`: True and `POINTS_T`; for k in 1..18, `budget_s=k - 0.5` raises with `clock.reads == k + 1`; T2: False and `POINTS_T2` | `DEADLINE-POINTS` |
| D-3b | `test_every_reading_point_of_the_injection_views_is_pinned` | `POINTS_NO_VALUE`; k in 1..15 raises at reading k + 1 | `NO-VALUE-POINTS` |
| D-4 | `test_a_text_found_in_the_cache_still_reads_the_clock` | in `scan_cache()`: first call `budget_s=600.0`; the second reads exactly `("scan_holds",) * 6`; `budget_s=-1.0` raises on the cache hit | `DEADLINE-CACHE` |
| D-5 | `test_a_build_cut_by_the_deadline_stores_nothing` | in `scan_cache()`: `budget_s=4.5` (deadline 5.5) raises at reading 6, in `_readings`; no bundle stored; the next call without a budget answers True | `DEADLINE-NO-PARTIAL` |
| D-6 | `test_the_error_is_not_a_size_refusal_and_ends_the_chunked_read_at_once` | `RegexDetector(0.5)._score("ab " * 100_000, time.thread_time() - 1.0)` (a private, same-thread absolute deadline) raises after EXACTLY 2 calls of `scan_views_no_value` (CHANGED in v4 from 1: the whole text is refused by its length first, then the first piece raises after its size rule; v3's P1 is gone); `not issubclass(DeadlinePassed, TextTooLong)` | `DEADLINE-NOT-SIZE` |
| D-7 | `test_a_bad_budget_is_refused_before_any_reading` | `True`, `False`, `"1"`, NaN, `inf`, `-inf`, `[1.0]` raise `NotText` for both functions; 0 readings (CHANGED in v4: the two infinities) | `DEADLINE-TYPE` |
| D-8 | `test_the_injection_check_flags_a_run_past_its_budget` | stepping clock on `textnorm.time` and `injection.time`, `INJECTION_BUDGET_S = 0.5`; FOR `RegexDetector(0.5)` AND `AnyOf([RegexDetector(0.5)])` (CHANGED in v4: design N3, the `AnyOf.check` call site, injection.py:202): flagged `guard_unavailable`, `caplog` holds `DeadlinePassed`, and `clock.where == ["check", "_read", "scan_views_no_value", "scan_views_no_value"]` (the check's start, the seconds left, the fold's start, its reading after the size rule; NEW, kills mutant 255); with the budget None a steering text is `injection_suspected` and "hello world" is not flagged | `DEADLINE-INJECTION` |
| D-9 | `test_the_injection_budget_setting_is_checked` | unchanged from v3 (`== 30.0`; seven bad values raise `ValueError` naming the setting and flag the run) | `BUDGET-DEFAULT`, `BUDGET-UNCHECKED` |
| D-10 | `test_the_budget_is_counted_on_the_thread_that_runs_the_scan` (NEW in v4: design M1) | `ThreadClock` on `textnorm.time`; `asyncio.run(asyncio.to_thread(...))` runs `scan_holds(text=T, value=V, budget_s=2.5)` in a worker: it raises at the worker's reading 4 (start 1, deadline 3.5) and the test's own thread (clock 1,000 ahead) is read 0 times; then `injection_check(RegexDetector(0.5), "hello world", "t")` in a worker with the budget 0.5 is flagged `guard_unavailable` and reads the test's thread 0 times | `DEADLINE-THREAD` |
Every failing assertion raises `AssertionError` whose message STARTS with its tag. Two `except Exception` lines carry `# noqa: BLE001`.
WHAT CHANGED IN THE TESTS FOR M1 (asked by the lead): every `deadline=` argument became `budget_s=` with a relative value (`time.thread_time() +
600.0` -> `600.0`, `time.thread_time() - 1.0` -> `-1.0`, `k + 0.5` -> `k - 0.5`, `5.5` -> `4.5`); D-1, D-2, D-7 were renamed; D-6 expects 2 calls,
not 1; D-7 adds the infinities; D-8 covers `AnyOf` and pins the reading sequence; D-10 is new. No reading sequence constant changed.

## 6. Mutants (CHANGED in v4: 15 new, 255 in all)
### 6.1 The 15 new mutants (appended after the last mutant, "tables: the lazy tables are never kept", before `]  # fmt: skip`; `test_file=DL`; exact rows in `g10-v4-tests.diff`)
Each `old` occurs exactly once in the edited, formatted file (meta test g, green on the prototype). Each was run with the runner's rules on the
prototype (14): all 15 KILLED with the tag below.
| # | name | file | old | new | killer (`only_test`) | expect |
|---|---|---|---|---|---|---|
| 241 | `deadline: the clock is never read` | TN | `"    if deadline is not None and time.thread_time() >= deadline:\n"` (CHANGED: `>=`) | `"    if False:\n"` | `test_a_spent_budget_raises_and_never_answers` | `DEADLINE-SPENT` |
| 242 | `deadline: a spent deadline answers no hit` | TN | `"    _checked(text, value)\n    _tick(deadline)\n"` (CHANGED: P2 of `scan_holds`, P1 is gone) | `"    _checked(text, value)\n    if deadline is not None and time.thread_time() >= deadline:\n        return False\n"` | same as 241 | `DEADLINE-NOT-FALSE` |
| 243 | `deadline: the error is a TextTooLong` | TN | `"class DeadlinePassed(TextnormError):"` | `"class DeadlinePassed(TextTooLong):"` | `test_the_error_is_not_a_size_refusal_and_ends_the_chunked_read_at_once` | `DEADLINE-NOT-SIZE` |
| 244 | `deadline: a bad budget is no budget` (CHANGED: name) | TN | `"    if type(budget_s) not in (int, float) or not math.isfinite(budget_s):\n"` | `"    if False:\n"` | `test_a_bad_budget_is_refused_before_any_reading` | `DEADLINE-TYPE` |
| 245 | `deadline: the views of the text are built without the deadline` | TN | `"    bundle = _text_bundle(text, deadline)\n"` | `"    bundle = _text_bundle(text)\n"` | `test_every_reading_point_of_scan_holds_is_pinned_and_each_one_refuses` | `DEADLINE-POINTS` |
| 246 | `deadline: the injection views are built without the deadline` | TN | `"    bundle = _text_bundle(raw, deadline)\n"` | `"    bundle = _text_bundle(raw)\n"` | `test_every_reading_point_of_the_injection_views_is_pinned` | `NO-VALUE-POINTS` |
| 247 | `deadline: the scan keys get no deadline` | TN | `"        tuple(sorted(_scan_keys(raw, deadline))),\n"` | `"        tuple(sorted(_scan_keys(raw))),\n"` | same as 245 | `DEADLINE-POINTS` |
| 248 | `deadline: no reading before a prefix pass` | TN | `"        _tick(deadline)\n        nfkd = unicodedata.normalize(\"NFKD\", text)\n"` | `"        nfkd = unicodedata.normalize(\"NFKD\", text)\n"` | same as 245 | `DEADLINE-POINTS` |
| 249 | `deadline: no reading between the passes of a scan key` | TN | `"        _tick(deadline)\n        out = step(text)\n"` | `"        out = step(text)\n"` | same as 245 | `DEADLINE-POINTS` |
| 250 | `deadline: no reading after the needles of the value` | TN | `"    needles = _needles_or_refuse(value, scripts)\n    _tick(deadline)\n"` | `"    needles = _needles_or_refuse(value, scripts)\n"` | same as 245 | `DEADLINE-POINTS` |
| 251 | `deadline: no reading in the insertion loop` | TN | `"        hits += 1\n        if not hits % 4096:\n            _tick(deadline)\n        stop = start + h\n"` | `"        stop = start + h\n"` | same as 245 | `DEADLINE-POINTS` |
| 252 | `injection: the detector passes no deadline` | INJ | `"        score = self._score(text, _deadline())\n"` | `"        score = self._score(text)\n"` | `test_the_injection_check_flags_a_run_past_its_budget` | `DEADLINE-INJECTION` |
| 253 | `injection: the budget setting is not checked` | INJ | `"    if type(budget) not in (int, float) or not 0 < budget < float(\"inf\"):\n"` | `"    if False:\n"` | `test_the_injection_budget_setting_is_checked` | `BUDGET-UNCHECKED` |
| 254 | `deadline: the budget is taken as a deadline` (NEW in v4: M1) | TN | `"    return time.thread_time() + budget_s\n"` | `"    return budget_s\n"` | `test_the_budget_is_counted_on_the_thread_that_runs_the_scan` | `DEADLINE-THREAD` |
| 255 | `injection: the deadline is passed as the budget` (NEW in v4: the absolute value handed to the relative API, a near no-deadline on a real clock) | INJ | `"    return None if deadline is None else deadline - time.thread_time()\n"` | `"    return deadline\n"` | `test_the_injection_check_flags_a_run_past_its_budget` | `DEADLINE-INJECTION` |
WHAT CHANGED IN THE COUNT FOR M1 (asked by the lead): v3's 13 become 15: 241, 242 and 244 were re-written for the new code (same intent), 254 and 255
are new; v3's 242 "move P1" form and v2's cache mutant stay dropped. The list goes 240 -> 255; `names[240:]` has 15; `split_counts()` (243, 12).
Collision check: 241's old text occurs once (only in `_tick`); 242's NEW text holds 241's old text, harmless (each mutant is applied alone to the
unmutated file). 251's old holds the loop's own line `stop = start + h` (the second loop has the same three reading lines before `lo = max(...)`).
254's old is in textnorm.py only (injection.py's `_deadline` returns `... + budget`, another file and another string).
Intentionally without a mutant (each still pinned by D-3 / D-3b's exact sequence): P2 of `scan_views_no_value`, P3b, P4, P6, P7a, P7b, the
second-loop P7c, the `_squeezed`/`_views`/`_view_pairs` wiring. D10 (no reading in `_score`) has NO pin at all: no test fails if a reading is
added there (CHANGED in v4: design N5, said in D5).

### 6.2 The 9 re-pointed mutants (same mutation, same killer and expect; only `old` and `new` re-copied; list line numbers of HEAD BY GREP)
| HEAD list lines (BY GREP) | index in `M` | name | killer file | old (after G10) | new (after G10) |
|---|---|---|---|---|---|
| 328-330 | 64 | `scan: squeeze_views gives one view` | T | `"    for view in _views(\n        raw, casefold=True, collapse_ws=False, marks_dropped=True, deadline=deadline\n    ):"` | `"    for view in (_fold(raw, casefold=True),):"` |
| 450-453 | 107 | `marks: squeeze_views has no marks-dropped views` | T | the same old as above | the same with `marks_dropped=False` |
| 460-462 | 110 | `marks: a view is repeated` | T | `"        scripts=scripts,\n        deadline=deadline,\n    ):\n        if view not in out:\n            out.append(view)"` | `"        scripts=scripts,\n        deadline=deadline,\n    ):\n        out.append(view)"` |
| 688-690 | 182 | `insertion: the match is never made` | FB | `"    for view in script_views:\n        _tick(deadline)\n        if any(_holds_with_one_insertion(view, needle, deadline) for needle in inserts):\n            return True\n    return False\n"` | `"    return False\n"` |
| 676-678 | 178 | `injection: the call names no value` | FB | `"textnorm.scan_views_no_value(text, budget_s=_left(deadline))"` (CHANGED) | `"textnorm.scan_views(text, budget_s=_left(deadline))"` (CHANGED) |
| 770-772 | 208 | `injection: a module builds its own views` | O | `"            yield text, textnorm.scan_views_no_value(text, budget_s=_left(deadline))\n"` (CHANGED) | `"            yield text, textnorm.scan_keyset(text)\n"` |
| 849-851 | 234 | `injection: the pieces do not overlap` | Q9 | `"        if back >= low and _holds(text[end - back : end], need_kept, need_letters, deadline):\n"` | `"        if back >= 1:\n"` |
| 855-857 | 236 | `injection: the new piece ignores the letters it holds` | Q9 `[300]` | the same old as above | `"        if back >= low:\n"` |
| 864-866 | 239 | `injection: the second half of a halved piece starts at the halfway point` | Q9 | `"            yield from RegexDetector._fit(piece[second:], deadline)\n"` | `"            yield from RegexDetector._fit(piece[cut:], deadline)\n"` |
All 9 run on the v4 prototype against HEAD f91f56a04's killer files (Q9 grew since v3): 9 KILLED (14).

## 7. PHASES (CHANGED in v4: readiness M1, N2-N6; the box rule: `uptime` first, wait while the load is above 6, `-n 2` at most, one heavy process at a time)
Variables: `TN_ALL="tests/test_textnorm*.py"` (15 files at HEAD, BY GREP: test_textnorm, _app, _callers, _differential, _fixbatch, _generator,
_meta, _mixed_script_micro, _order137, _perf, _q9, _round1, _round2, _scan, _siblings; 16 once `_deadline` is in);
`INJ="tests/test_k5_fixes5.py tests/test_injection_chunk_boundary.py tests/test_p6_detectors.py tests/test_p1a_fixes.py tests/test_s4_llm_guard.py tests/test_review_pr3_round2.py tests/test_p5p6_followups.py"`;
`CANARY="tests/test_redact_fold_budget.py tests/test_redact_settle_loop.py"`; `F=handover/core-c/tickets/G10-files`.
MUST-STAY-GREEN (run at the end of phase 5): `uv run pytest -n 2 -m "not live and not perf" $TN_ALL $INJ $CANARY` (prototype: 1,247 passed in
207 s at -n 2), then the perf rows alone: `uv run pytest -m perf tests/test_textnorm_round2.py -s` and `uv run pytest -m perf tests/test_textnorm_perf.py`
(NOT RUN by the drafter), then `uv run ruff format --check src tests tools && uv run ruff check src tests/test_textnorm_deadline.py tests/textnorm_mutants.py tests/test_textnorm_meta.py tests/test_textnorm.py tests/test_textnorm_fixbatch.py tests/test_textnorm_callers.py tests/test_textnorm_order137.py tests/test_textnorm_round2.py`
(CHANGED in v4, readiness N4: every edited test file is now `ruff check`ed, not only format-checked; clean on the prototype).
THE DELETE/COPY RULE (CHANGED in v4, readiness M1): the new test file is in the tree in phase 0 only and again from phase 3 on. Delete it at the end
of phase 0. Reason: with it in the tree, phase 1 has SEVEN reds, not three (D-6, D-8, D-9 and D-10 need phase-2 code: `injection._score`'s
deadline, `injection.time`, `INJECTION_BUDGET_S`, `injection._deadline`; MEASURED, 14 item 3).
Phase 0, fail-before. `cp $F/test_textnorm_deadline.py tests/` and `uv run pytest tests/test_textnorm_deadline.py`: ONE collection error,
`ImportError: cannot import name 'DeadlinePassed'`; no test runs (CHANGED in v4, readiness N5: v3 said "10 red"). Then `rm tests/test_textnorm_deadline.py`.
The behavioural fail-before of each assertion is the mutant run of phase 4.
Phase 1, guard/textnorm.py and the four pin files that follow from it:
`git apply --include=src/hadavin_sdk/guard/textnorm.py $F/g10-v4-src.diff` and `git apply --include=tests/test_textnorm.py
--include=tests/test_textnorm_fixbatch.py --include=tests/test_textnorm_callers.py --include=tests/test_textnorm_order137.py $F/g10-v4-tests.diff`
(the fixbatch file also carries the call-lint edit of :323, which holds with HEAD's injection.py too). Then `uv run ruff format --check
src/hadavin_sdk/guard/textnorm.py && uv run ruff check src/hadavin_sdk/guard/textnorm.py` and `uv run pytest -n 2 -m "not live and not perf"
$TN_ALL $INJ $CANARY`. EXPECTED RED after phase 1 (the test file deleted; exactly these three):
`tests/test_textnorm.py::test_the_manifest_pins_the_files_a_demo_copies` (hash; until phase 5),
`tests/test_textnorm_meta.py::test_g_every_search_string_occurs_exactly_once_in_the_file_it_targets` (old strings gone; until phase 3),
`tests/test_textnorm_meta.py::test_the_split_of_the_mutants_into_behaviour_and_wording_only_is_derived_from_the_syntax_trees` (until phase 3).
Without the four pin files these are red too: `test_the_public_names_are_exactly_the_listed_thirty_six`, `test_the_module_docstring_lists_every_public_name`,
`test_refusal_handlers_has_five_entries_and_the_banned_names_follow_textnorm`, `test_exactly_the_cap_in_scan_keys_is_allowed_and_one_over_is_refused`.
If the builder keeps the test file in the tree instead, add these four to the reds: `tests/test_textnorm_deadline.py::test_the_error_is_not_a_size_refusal_and_ends_the_chunked_read_at_once`,
`::test_the_injection_check_flags_a_run_past_its_budget`, `::test_the_injection_budget_setting_is_checked`, `::test_the_budget_is_counted_on_the_thread_that_runs_the_scan`.
Phase 2, guard/injection.py, defaults.py and the round2 perf row: `git apply --include=src/hadavin_sdk/guard/injection.py
--include=src/hadavin_sdk/defaults.py $F/g10-v4-src.diff` and `git apply --include=tests/test_textnorm_round2.py $F/g10-v4-tests.diff`. Same
commands (ruff on the two source files). EXPECTED RED: the same three (meta g now also misses the injection old strings).
Phase 3, the test file and the mutant list: `cp $F/test_textnorm_deadline.py tests/`, `git apply --include=tests/textnorm_mutants.py
--include=tests/test_textnorm_meta.py $F/g10-v4-tests.diff` (the killer-file set, the uniqueness list, the counts and the 15 + 9 mutant rows land in
one step, so the meta file is never half-edited; CHANGED in v4: v3's phases 3 and 4 are one). Then
`uv run pytest tests/test_textnorm_deadline.py tests/test_textnorm_meta.py`: 26 passed (11 + 15; CHANGED in v4, readiness N3: v3's "25 tests" was
10 + 15). Still red: the manifest test only (ESTIMATE from the prototype: meta g and the split are green once the list is re-pointed).
Phase 4, the mutants. ONE command (CHANGED in v4, readiness N6: the runner's filter is a SUBSTRING match on the name, `o in m.name`
(tests/textnorm_mutants.py `__main__`, BY CONTENT); "deadline:" matches exactly the 12 `deadline:` mutants, 241-251 and 254, and NOT the three
`injection:` ones, which are named in full):
`uv run python tests/textnorm_mutants.py "deadline:" "injection: the detector passes no deadline" "injection: the budget setting is not checked" "injection: the deadline is passed as the budget" "scan: squeeze_views gives one view" "marks: squeeze_views has no marks-dropped views" "marks: a view is repeated" "insertion: the match is never made" "injection: the call names no value" "injection: a module builds its own views" "injection: the pieces do not overlap" "injection: the new piece ignores the letters it holds" "injection: the second half of a halved piece starts at the halfway point"`
-> 24 mutants (each argument matches exactly one name, MEASURED on the prototype list, except "deadline:" with 12). It first runs the unmutated
baseline over all 11 files of `TESTS` (minutes). Every row must print `ok  killed`; the last line `24 of 24 good`.
Phase 5, the manifest hash and the docs: `sha256sum src/hadavin_sdk/guard/textnorm.py` -> tests/fixtures/textnorm_manifest.json:4 (the tests diff
already holds the prototype hash: if the builder's hash differs, write the builder's); append `$F/changelog_item.md` to CHANGELOG.md with
`<NEW-HASH>` replaced by the same hash. Then MUST-STAY-GREEN in full. The SECURITY lines (8.4) are NOT the builder's (D9).

## 8. The false-hit rates (part b)
### 8.1 What is documented today, and what is wrong with it (CHANGED in v4: design M4)
- defaults.py:247-254 (the INSERTION comment; :251 holds "...stay near 1% or lower per 10,000 characters of text; a needle holding several groups
  takes the largest minimum, ..."; BY GREP, CHANGED in v4 from v3's :234-241): the "1%" measures only what the ONE-INSERTED-LETTER match ADDS, per
  script, on Bible text. It is read as the scan's rate (G1 review M5, E11).
- The evidence (handover/core-c/evidence/G1-false-hits-and-cost.md): run 1 (section A) and "Round 2 (2026-11-20, low load)" (:106 on, committed
  e70aecaa9, script `g1_split.py`). Round 2 re-ran the Latin classes on a newer export (rates comparable to run 1, not equal) and SPLIT every hit.
- WHAT THE NUMBERS ARE (CHANGED in v4): an upper bound in ONE sense only: a value that is a whole word of the text (`black`, `Omar`, `Robert`) counts
  as a hit although a person would call it a true match. They are NOT an upper bound for other registers (tickets, email, chat: not in the corpora,
  which are repository prose and code, standard-library docstrings and generated Markov text) nor for real protected values (the values are random
  pronounceable strings plus a 70-name hand list, about 30 % of the name values).
- THE SPLIT, per row (evidence :125-130, :151): hits that mask a fragment of a word: name-4 94.1 %, name-5 63.4 %, name-6 9.1 %, street/host 33.7 %,
  digits-6 84.6 %, short id 98.8 %. v3's "for values of 4-5 characters 94-99 %" was wrong for 5-letter names (63.4 %): CHANGED in v4.
- THE POOLED SHARE (evidence :117, :151): 21,591 hits, of which 21,590 located and 1 unlocated; of the located: whole 7,086 (32.8 %), inside 7,129
  (33.0 %), across 7,375 (34.2 %). It is POOLED over six rows of very different sizes (name-4 alone is 10,600 hits): stated as pooled (CHANGED in v4).
- THE STREET/HOST ROW is hash-seeded (evidence :120: it draws from a `set`; two runs of the same script gave 4.46 % and 3.91 %): published as
  "3.9 to 4.5 %" (CHANGED in v4; v3 gave 3.9 %).
- SECURITY wording today: SECURITY-README-v5.md K50 :622-624, K51 :625-627, table rows :835-836, the status count :873, the evidence list :883, :958,
  :1031 (N16) and :1034 (N19) (records: NOT changed). SECURITY-README-final.md L43 :144, L44 :145, rows :257-258. (BY GREP, all unchanged from v3.)
- At HEAD no redaction path calls `scan_holds` (2.3): the rates have NO consumer yet.

### 8.2 defaults.py: the finished comment lines (the builder's; phase 2; exact text in `g10-v4-src.diff`, proto :250-263)
HEAD :250-251 become three lines (the tail "; a needle holding several groups ..." is kept on the third), as v3 8.2 (unchanged). After HEAD :254
(`# the matcher takes ...; a longer needle is matched exactly only.`), before `TEXTNORM_INSERTION_MIN_CHARS = 12`, CHANGED in v4:
```
# FALSE HITS of the whole scan_holds (measured 2026-11-20, Python 3.13.18, Unicode 15.1.0; handover/core-c/evidence/G1-false-hits-and-cost.md,
# "Round 2"): the share of 10,000-character chunks of ordinary Latin text (repository prose and code, standard-library docstrings, generated
# text) in which scan_holds reports a value drawn at random (random pronounceable strings and a 70-name hand list, not real protected values):
# 4 letters 5.3%, 5 letters 1.0%, 6 letters 0.4%, 8 or more 0; a common word of 5-10 letters 3.9-4.5% (its draw is hash-seeded: two runs);
# ASCII ids of 4-5 characters 0.22%; 6 digits 0.007%. An upper bound in ONE sense only: a value that is a whole word of the text counts as a
# hit. It is NOT a bound for other registers (tickets, email, chat) or for real protected values. Share of the hits that cut a word: 4 letters
# 94%, 5 letters 63%, ids of 4-5 characters 99%, 6-letter names 9% (91% are the whole name). Non-Latin: one program's real interface text
# (Russian 4-8 letters 7.6%; Chinese of 2 characters drawn by frequency 5.2%, of 3-4 characters 0); Arabic and Devanagari synthetic only, unknown.
```
(defaults.py is not hashed; no test reads these lines: grep of tests for "1% or lower".)

### 8.3 The CHANGELOG item (the builder's; phase 5): `G10-files/changelog_item.md`, appended after CHANGELOG.md:655 (the last line)
CHANGED in v4: the headline names what is bounded ("a CPU budget for the injection read and for the fold scan's future consumer"; design N6: no
redaction path calls `scan_holds`, the redactor is unchanged); the overrun is stated as measured maxima on named texts (M3); "no call site of the
injection check has a wall-clock limit" replaces "the wall clock is the caller's" (M2); the value work (7.2 to 7.5 s) is in the item (M3); the
false-hit bullet has the one-sense upper bound, the per-row fragment shares, the pooled sample and 3.9 to 4.5 % (M4); counts 11 tests, 255 mutants,
(243, 12), `budget_s` in the lint. Run green on the prototype: meta test i and the manifest test (14).

### 8.4 The SECURITY wording (NOT the builder's: the SECURITY wording lane applies it, D9)
Into SECURITY-README-v5.md (or its successor):
- :622-624 K50 becomes: "**K50. Over-matching, measured:** a known name is found inside a longer word or across a space. Example: known `mary`
  found in `summary`. MEASURED 2026-11-20 (evidence/G1-false-hits-and-cost.md, Round 2), per scan of one 10,000-character chunk of ordinary Latin
  text (repository prose and code, library docstrings, generated text) with a value drawn at random: 4 letters 5.3 %, 5 letters 1.0 %, 6 letters
  0.4 %, 8 or more 0; common words of 5 to 10 letters 3.9 to 4.5 %; ASCII ids of 4 to 5 characters 0.22 %; 6 digits 0.007 %. An upper bound
  only in that a value that is a whole word counts as a hit; NOT a bound for tickets, email, chat or real values. The share of hits that cut a
  word: 94 % for 4 letters, 63 % for 5 letters, 99 % for short ids, 9 % for 6-letter names. Real Russian and Chinese interface text: 7.6 % and
  5.2 % for short values; Arabic and Hindi: synthetic text only, unknown. No masking path uses this scan yet. Status: STATED. Evidence: MEASURED.
  Who acts: nobody (the consumer's ticket re-measures)." (CHANGED in v4: M4.)
- :625-627 K51 becomes: "**K51. Limited by a CPU budget:** the planted-instruction check stops at `INJECTION_BUDGET_S` (30 CPU seconds of the
  thread that runs the check, per check) and flags the run (`guard_unavailable`) when the fold passes it. Measured before the limit: 3.6 to 9.6 s
  for 2,000,000 characters (evidence G1 B), up to 16.0 s on ordinary texts built by the drafter, 185 s on a constructed text (G10 ticket 12); a
  machine about 1.9x slower than the build box flags the 16-second text on every run. Only CPU time counts; no call site bounds the check by wall
  clock. Status: PINNED once G10 lands (tests/test_textnorm_deadline.py). Evidence: TESTED. Who acts: nobody." (CHANGED in v4: M2, N1.)
- Rows :835-836, counts :870-885, :958, the final.md rows :144-145 and :257-258, SECURITY.md, the G1 review table: as v3 8.4 (unchanged).

## 9. The NOT RUN items (part c) (unchanged from v3 except the last row)
| item | status now | default (D7) |
|---|---|---|
| split of the Latin hits | DONE by the evidence runner (Round 2, e70aecaa9) | quoted in 8.1-8.4 |
| real non-Latin text | PARTLY DONE (Russian and Chinese, vim `.mo` catalogs); Arabic and Devanagari: none on the box | stays "synthetic only, unknown"; a real corpus needs the lead's leave to fetch |
| 2,000 values without `scan_cache()` | NOT RUN: ASCII about 756 s, 1 percent about 2,023 s, distinct about 3 h | run ASCII only, at load below 2, when the lead wants it |
| the redactor's view-building stretch as one figure (D8) | NOT RUN | not needed while D8's default stands |
| CHANGED in v4: the injection read of a text whose pieces are halved (design N1) | MEASURED (12.4): 185 s without a budget, flagged at 30.08 s with 30.0 | nothing more |

## 10. Decisions for the lead (the builder builds the DEFAULT)
ORDER 023 says "add a deadline to the text fold in the redactor's style; publish the measured false-hit rates with a date; run the NOT RUN items
that fit the box at low load". It does not choose D1-D10; the defaults are the drafter's, unapproved until the lead says so.
| id | decision | DEFAULT (built) | fallback | consequence |
|---|---|---|---|---|
| D1 | where the clock is read | inside textnorm.py at the points of 3.4 | only in the callers' loops | default: overrun = the longest stretch (12); textnorm pins change. Fallback: overrun one whole scan, the injection read of one text under the cap unbounded |
| D2 | how the budget travels (CHANGED in v4) | public: a RELATIVE `budget_s` turned into a deadline by the callee on its own thread; private: an explicit absolute `deadline=None` argument down the chain | (a) v3's absolute public `deadline` plus an owner-thread check that raises `NotText`; (b) a `contextvars` scope | default: no cross-thread value is possible (D-10, mutant 254); the injection hands each fold call the seconds left (`_left`, mutant 255). (a): more state (the owner thread id), a new refusal; (b): hidden state |
| D3 | which public functions take it | `scan_holds`, `scan_views_no_value` | also `scan_views` | default: the fixbatch:280 pin stays |
| D4 | the injection budget (CHANGED in v4: design N1) | `defaults.INJECTION_BUDGET_S = 30.0`, PER CHECK | None, `REDACT_BUDGET_S` (6.0) or 48.0 | default: about 1.9x the slowest ordinary 2,000,000-character text measured (16.0 s; 15.8 s Devanagari words with spacing marks mixed with English). PER CALL, NOT PER RUN: k1b checks every tool result (k1b/loop.py:205), so a run can spend up to `max_tool_calls` x 30 s of CPU in checks. On a machine about 1.9x slower the 15.8 s Devanagari document is flagged `guard_unavailable` on EVERY run (a permanent false abstain for that document there). A hostile text is flagged at 30 s (185 s without the budget, 12.4). 48.0: 3x headroom, 48 s per hostile check. None: E11 half open. 6.0: the 1-percent, Devanagari and distinct texts are flagged on this box |
| D5 | readings without a mutant (CHANGED in v4: N5) | P2 of `scan_views_no_value`, P3b, P4, P6, P7a, P7b, the second P7c: pinned by D-3 / D-3b's exact sequences, no mutant of their own. D10's "no reading in `_score`" has NO pin (no test, no mutant) | a mutant each (7 more) | default: a removal is still killed by D-3, the list does not show it |
| D6 | the error name and message | `DeadlinePassed("the scan passed its deadline")` | a code-style message | default: plain words in the log line |
| D7 | the NOT RUN rows | as in section 9 | run the 2,000-value ASCII row now | default: no extra CPU |
| D8 | a reading in the redactor's view building | not in G10 | in G10 with mutant KR1 | default: redact.py stays G4/G8/G7's |
| D9 | who writes the SECURITY wording | the SECURITY wording lane applies 8.4 | the G10 builder | default: no SECURITY file in the builder's list |
| D10 | a reading in `injection._score` | none | a reading per piece after its regex loop | default: a check can end after its budget WITH a complete answer: measured 0.066 s after (12.4); fallback: one more mutant, an allow-list edit |
| L1 (NEW in v4) | the build files | `G10-files/` holds the v4 test file and diffs (adapted to `budget_s`), not a byte copy of v3's scratchpad test file | copy v3's file too, as a record | default: one test file, matching the ticket |
| L2 (NEW in v4) | pin the order of refusals (N4) | stated and probed (3.2), not pinned by a test | add a NotText-before-DeadlinePassed assertion to D-7 | default: no new test; a reorder would go unnoticed |

## 11. Stated limits after G10 (CHANGED in v4: M1, M2, M3, N1, N2)
- CPU clock of the thread that runs the call only: waiting for the GIL, a lock or I/O does not advance it. The budget is relative and read by the
  callee on that thread, so a check run in an `asyncio.to_thread` worker is timed on the worker (D-10). No call site of the injection check
  bounds the check by wall clock (k1b checks its case's wall clock between steps only, 2.3): a check can take longer than 30 s of wall time.
- Overrun: MEASURED maxima on named texts only (3.5, 12): 0.63 s for one `scan_holds` (a first-seen distinct-letter text), 0.24 s on the
  tag/Mc-heavy texts, 0.26 s for the injection read. Not a bound for every text. A call can also end after its budget WITH a complete answer (the
  stretch after the last reading: the needle loop, or `_score`'s regex tail, D10).
- The value's work (between P2 and P2b) has no reading inside it: measured 7.2 to 7.5 s for a value of 236,879 distinct letters.
- Per check, not per run (D4): a k1b run can spend up to `max_tool_calls` x `INJECTION_BUDGET_S` of CPU in checks.
- The outcome depends on the machine: a slow machine refuses a text a fast one scans; on a machine about 1.9x slower the 15.8 s Devanagari document
  of 12.3 is flagged on every run.
- A hostile author can force the refusal of the injection check (a text built to be slow, 12.4): the run is flagged, the rest of that text is not
  read for that run.
- `time.thread_time` must exist (CHANGED in v4: design N2, stated once): where it does not (a platform without a per-thread CPU clock), the
  default budget makes `injection._deadline()` raise `AttributeError` on every check, so EVERY run is flagged `guard_unavailable` (fail closed,
  a total outage of the check); `INJECTION_BUDGET_S = None` restores the old behaviour there. Linux, macOS and Windows have it.
- No budget in `register_value`, `fold`, `fold_view`, `identity_keys`, `scan_views`, `scan_keyset`, `scan_needles` and the other single-pass functions.
- 2,000 values without `scan_cache()` stays O(values x text).
- The false-hit rates are an upper bound in one sense only (whole-word hits count); other registers, real values and Arabic/Devanagari text are
  not measured.

## 12. Measured (CPU seconds of the measuring thread, `time.thread_time()`; one process; MEASURED = v4 prototype, load 0.3 to 2.3; MEASURED v3 = v3 prototype, load 3 to 6.7)
### 12.1 Reading sequences (`g10v4_opus/scripts/overrun4.py seq`, stepping clock; MEASURED)
T and V: 19 readings (`POINTS_T`); T2: 18; `scan_views_no_value(T)`: 16; `("a summary", "Mary")`: 15; `("passంword", "password")`: 20. D-3 and
D-3b (k in 1..18 and 1..15) green.
### 12.2 The distinct-letter text, 236,879 characters (`overrun4.py scan`, `value`; MEASURED, v3 figures in brackets)
| call | readings | call | longest stretch (where) | sweep of 12 budgets: worst overrun |
|---|---|---|---|---|
| `scan_holds`, value `Zqxvbn` | 56 | 6.06 s | 0.585 s (S -> P2: the weight) [0.599] | 0.202 s [0.209] |
| `scan_holds`, value `密码测试` | 58 | 6.36 s | 0.520 s (S -> P2) [0.514] | 0.155 s [0.094] |
| `scan_views_no_value` | 55 | 5.97 s | 0.552 s (S -> P2) [0.630] | 0.129 s [0.109] |
Value work (`scan_holds(text="x", value=...)`): 236,879 distinct letters 7.49 s [7.19]; 262,144 ASCII letters 0.634 s [0.583].
### 12.3 NEW in v4 (design M3): tag/Mc-heavy texts of 262,144 characters, `scan_holds` (`g10v4_opus/scripts/m4.py scan`; MEASURED)
Words from the corpus classes "Hindi and Thai marks" (दिपक, दीपक, दुःख, दुख, महन, मोहन, समन, सुमन, हंस, हस) and "tag characters" (the six strings);
values `Zqxvbn` (answer False) and `मोहनदीपक` (8 Devanagari letters). Weight memo cleared for "cold"; "warm" is a second call.
| text | marks / tags | value | answer | readings | call | longest stretch cold / warm (where) | sweep of 12: worst |
|---|---|---|---|---|---|---|---|
| Devanagari words | Mc 9.1 %, Mn 9.0 % | Zqxvbn | False | 22 | 1.77 s | 0.166 / 0.241 s (a converge pass) | 0.221 s |
| Devanagari words | same | मोहनदीपक | True | 22 | 2.75 s | 0.223 / 0.230 s (converge) | 0.154 s |
| tag words | tags 44.6 % | Zqxvbn | False | 21 | 1.06 s | 0.122 / 0.103 s | 0.129 s |
| tag words | same | मोहनदीपक | False | 21 | 0.76 s | 0.091 / 0.113 s | 0.047 s |
| Devanagari 50 % + tag words 50 % | Mc 4.2 %, tags 24.1 % | Zqxvbn | False | 42 | 4.01 s | 0.205 / 0.212 s | 0.186 s |
| same | same | मोहनदीपक | True | 42 | 3.80 s | 0.208 / 0.162 s | 0.181 s |
An earlier run of the first row (stopped by a too-short value in the second) gave 0.146 to 0.161 s and a worst sweep of 0.102 to 0.145 s.
### 12.4 The injection read of 2,000,000 characters (D4, design M3 and N1)
MEASURED v3 (`g10v3/scripts/overrun.py`, `inj2.py`; the injection code differs in v4 only by `_left`, about 1 us per fold call):
| text | spacing marks / tags | no budget | verdict | readings | longest stretch (where) |
|---|---|---|---|---|---|
| ASCII sentences | 0 | 4.45 s | not flagged | 2,001 | 0.043 s (tail) |
| 1 percent non-ASCII | 0 | 9.72 s | not flagged | — | — |
| every other character a distinct non-ASCII letter | 0 | 16.01 s | not flagged | 2,210 | 0.094 s (tail) |
| Devanagari words only | Mc 9.1 % | 0.53 s | flagged by the boundary rule (L45/K52), not the budget | — | — |
| Devanagari 70 %, English 30 % | Mc 5.6 % | 15.80 s | not flagged | 2,626 | 0.132 s (tail) |
| Devanagari 50 %, English 50 % | Mc 3.7 % | 15.29 s | not flagged | 2,626 | 0.117 s (tail) |
| tag words 30 %, English 70 % | tags 16.4 % | 6.52 s | not flagged | 2,641 | 0.078 s (tail) |
| tag words 10 %, English 90 % | tags 5.8 % | 8.30 s | not flagged | 8,021 | 0.075 s (tail) |
NEW in v4, MEASURED (`m4.py inj`, `m4.py halve`, `m4b.py`):
| text | no budget | verdict | readings | longest stretch (where) | regex of one piece + its 3 views | sweep of 6 budgets: CPU after the budget |
|---|---|---|---|---|---|---|
| `"ignore all "` repeated | 5.30 s | not flagged | 1,877 | 0.072 s (tail) | 0.020 s | all 6 flagged, 0.003 to 0.020 s |
| `"ignore " + "all " * 9` repeated | 4.88 s | not flagged | 1,877 | 0.105 s (tail) | 0.019 s | 5 flagged, 0.002 to 0.004 s; the 6th (4.9 s) finished with a complete answer 0.066 s after its budget |
| `"ignore disregard forget override all all all "` repeated | 4.41 s | not flagged | 1,847 | 0.052 s (tail) | 0.011 s | all 6 flagged, 0.003 to 0.014 s |
| `"ﷺ" * 40 + " the report "` repeated (U+FDFA: an NFKD of 18 letters, so 32,768-character pieces are over the weight cap and `_fit` halves them; 315 fold calls) | 185.27 s | not flagged | 4,395 | 0.260 s (a converge pass) | — | at the default 30.0: flagged at 30.08 s |
D4 from these: the slowest ORDINARY text is 16.0 s (MEASURED v3); 30.0 gives about 1.9x. The U+FDFA text is constructed; it is what the budget is for.
### 12.5 Equality and overhead
D-1 green (MEASURED). Overhead: ratio of bests 1.027 and 0.957 (3.5; MEASURED; within noise).

## 13. NOT verified (CHANGED in v4)
- The perf rows (`-m perf`): not run.
- The phase-4 command form (`tests/textnorm_mutants.py` with 13 arguments; the 11-file baseline first); the drafter ran `run_mutants` with the
  killer's file only. The whole 255-mutant run: not run.
- A full phase-1 or phase-2 run: the drafter ran the phase-1 tree on the eight named tests plus the new file only (14 item 3); v3 ran the
  equivalent full run (HEAD's tests against the v3 source: exactly the eight named reds). The phase-3 "manifest test only" red: ESTIMATE.
- The full gate AFTER mutant 255 and D-8's sequence assertion were added: the gate (1,247 passed) ran before; afterwards the new file, the meta
  file and the manifest test were re-run (27 passed) and the 15 new mutants re-run (15 killed). No other file changed between the two.
- The full repository suite outside TN_ALL, INJ and CANARY.
- The injection texts of v3's table (12.4, first part) on the v4 prototype.
- Python 3.12; a slower machine; a platform without `time.thread_time`; the GIL-contended case.
- The SECURITY lines of 8.4 and the "G1 review table" edit.

## 14. What the v4 drafter ran (all on scratch copies; the repo tree was not edited except this file and `G10-files/`; no commit)
Scratchpad `/tmp/claude-0/-home-user/1ecfcb92-30a8-505b-a8c3-27491ed2aff6/scratchpad/g10v4_opus/`: `base` = `git archive` of HEAD f91f56a04;
`proto` = base + v3's `patch_src.py` + `scripts/patch_v4.py` (the v4 source changes) + `ruff format` + `scripts/patch_tests.py` (v4) +
`scripts/patch_docs.py` (manifest, CHANGELOG item); `scripts/build.sh` rebuilds it. Python 3.13.18 (the repo's .venv), Unicode 15.1.0, 4 cores;
pytest with `PYTHONPATH=<tree>/src`; measurement scripts with `python -I` and the tree's src first on `sys.path`. Load 0.3 to 2.3. One pytest
batch at `-n 2`, every other pytest run serial.
1. `ruff format` + `ruff check` of the three source files and of the eight edited test files: clean.
2. Phase 0: the new file against HEAD's source: one collection error (`ImportError: cannot import name 'DeadlinePassed'`).
3. A phase-1 tree (base + the prototype's textnorm.py + the four pin files + the new file), serial run of the new file and the eight named
   tests: 7 failed, 12 passed: D-6, D-8, D-9, D-10, the manifest test, meta g, the split; the five pin tests green.
4. The full prototype: `pytest -n 2 -m "not live and not perf" $TN_ALL $INJ $CANARY`: 1,247 passed in 207 s. After the last test and mutant
   edits: the new file, the meta file and the manifest test: 27 passed. `split_counts()` (243, 12); `len(M)` 255.
5. Mutants with `tools.mutation_runner.run_mutants` (unmutated baseline first, `judge` with `expect` and `pinned`), the test list cut to the
   killer's file (`g10v3/scripts/runmut.py`, copied): the 15 new: 15 KILLED in 12 s, each with its tag (DEADLINE-THREAD: "the worker raised at
   reading 3, not 4"; 255: DEADLINE-INJECTION on the reading sequence). The 9 re-pointed: 9 KILLED (T: 3 in 139 s; FB: 2 in 5 s; O: 1 in 2 s;
   Q9: 3 in 4 s, HEAD's grown Q9 file).
6. The measurements of section 12 (`overrun4.py`, `m4.py`, `m4b.py`).
7. Probe of the refusal order (3.2): `scan_holds(text=1, ...)`, `(value=b"Mary")`, `scan_views_no_value(None)` with `budget_s=-1.0`: `NotText`;
   a 300,000-character text: `TextTooLong`.
8. `git apply --check` of both diffs on the repo's HEAD: clean. The CHANGELOG of the prototype ends with exactly `changelog_item.md` (hash filled).
NOT run: the perf rows, the full suite outside the listed files, the phase-4 command form, Python 3.12, the 2,000-value rows, any evidence run.

## 15. Findings of review round 1 (v3, kept as the record)
See `G10-textfold-deadline-v3.md` section 15: every round-1 finding was TAKEN or CONTESTED there; v4 keeps those resolutions except where a
round-2 finding below changes them (the API of M1/M6, the phase plan of B1).

## 16. Findings of review round 2: where each is resolved (all TAKEN)
Design critic (`G10-review-2-design.md`):
- M1 TAKEN (preferred option): relative `budget_s` computed in the callee on the calling thread (1, 3.2, 3.4, 3.6, D2); tests changed (5, "WHAT
  CHANGED IN THE TESTS"); new cross-thread test D-10 and mutants 254 and 255; the count 13 -> 15 (6.1, "WHAT CHANGED IN THE COUNT").
- M2 TAKEN: "the wall clock is the caller's" removed from section 1, 3.8 (defaults), 8.3 (CHANGELOG), 8.4 (K51) and 11; replaced by "no call site
  of the injection check has a wall-clock limit; the budget is CPU only", with k1b's between-steps check named (2.3).
- M3 TAKEN: the overrun is restated as measured maxima on named texts in 3.5, 8.3 and 11; the tag/Mc-heavy 262,144-character `scan_holds` case
  (12.3) and three `ignore all`-dense injection texts (12.4) measured; the value work (7.2 to 7.5 s) is in the CHANGELOG item and K51 keeps the
  measured figures.
- M4 TAKEN: an upper bound in one sense only, not for other registers or real values; 5-letter names 63.4 %; the pooled sample (21,590 located +
  1 unlocated); street/host 3.9 to 4.5 % (8.1, 8.2, 8.3, 8.4).
- N1 TAKEN: per check, not per run, with the k1b multiple (3.8, D4, 11); the halving path measured (12.4: 185 s, flagged at 30.08 s); the 15.8 s
  Devanagari document flagged on every run on a 1.9x slower machine (D4, 11).
- N2 TAKEN: stated once (11).
- N3 TAKEN in part: D-8 runs through `AnyOf` (the injection.py:202 call site) as well as the bare detector; the other five call sites call
  `injection_check` directly (BY GREP) and get no test of their own (stated, 2.3).
- N4 TAKEN: no reading before `_checked`; a non-`str` text with a spent budget raises `NotText` (3.2, probed; pinning it is L2).
- N5 TAKEN: D5 says D10 has no pin (D5, 6.1).
- N6 TAKEN: the CHANGELOG headline and first bullet say the injection read is what is bounded now; the redactor is unchanged (8.3).
Readiness reviewer (`G10-review-2-readiness.md`):
- B1 TAKEN: the test file and the source and test diffs are in `handover/core-c/tickets/G10-files/` (0.1); the `scan_holds` docstring lines are
  quoted exactly (3.7 item 6).
- M1 TAKEN: the delete/copy rule (7); the reds with the file kept are listed (seven: the three plus D-6, D-8, D-9, D-10; MEASURED).
- M2 TAKEN: every cite re-derived BY GREP on f91f56a04 (defaults :247-254, :251, :285; redact.py :1298-1299, :1340, :1375; meta :179-189, :199,
  :214, :269/:273, :377; the rest unchanged and re-checked) or named BY CONTENT.
- N1 TAKEN: the keyword order of the private chain (3.4, "THE PRIVATE CHAIN").
- N2 TAKEN: 15 files at HEAD, 16 with the new one (7).
- N3 TAKEN: 26 = 11 + 15 (7, phase 3).
- N4 TAKEN: `ruff check` covers every edited test file (7).
- N5 TAKEN: one collection error (7, phase 0).
- N6 TAKEN: the substring filter is stated; one command names the injection mutants in full (7, phase 4).
