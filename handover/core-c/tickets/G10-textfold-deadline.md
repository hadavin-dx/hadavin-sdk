# G10: a deadline for the text fold, the published false-hit rates, and the NOT RUN cost items (lead ORDER 023, escalation E11)

Status: DRAFT v2 for plan review, core-c drafter, 2026-11-20. Nothing is built. Path class: guard (textnorm, injection). A builder with no other
context builds from this file. Sections: 0 base, 1 goal, 2 what exists today, 3 design (part a), 4 pins and counts that change, 5 tests,
6 mutants, 7 the false-hit text (part b), 8 the NOT RUN items (part c), 9 decisions for the lead, 10 stated limits, 11 measured by the drafter,
12 NOT verified. v2 replaces v1 (same file, same day): prototype measured, the `scan_views` signature pin found (it keeps no deadline), the 9
re-pointed mutants found, the injection budget measured on a 2,000,000-character mixed text.

## 0. Base and what was read
- Base: cloud/core-c 374e6f3ff (board 09:35:38Z; code head 9d8bc580a, G7 fix round 6). Line numbers are of that head. guard/textnorm.py at the base
  has sha256 `e7a93738f10e7ea66e164c929d20c0405a0730d41852e0ff88856720ea6cdbee` (equals the manifest). HEAD moved during the drafting to a230de438
  (E9 code e8ff6de2b and board commits; the board committed v1 of this file as 831571d21): of the files G10 touches or cites only guard/redact.py
  changed (E9), by -8 lines before `_fold_scan`: `_over_budget` is at 1287, `_fold_scan` at 1328, its first read at 1363 on a230de438 (1295, 1336,
  1371 below). textnorm.py, injection.py, defaults.py, the CHANGELOG, the meta test, the mutant list and the fixtures are unchanged.
- Read: evidence/G1-false-hits-and-cost.md, ESCALATIONS.md E11, ORDERS.md ORDER 023, guard/textnorm.py (the whole scan path), guard/injection.py,
  guard/redact.py (`_Redactor.__init__`, `find`, `settle`, `_check_deadline`, `_over_budget`, `_line_hits`, `_fold_scan`, `_aligned_fold`,
  `_alias_keys`), guard/runmap.py (`InputTooLarge`, `redact_text`, `_decoded_masks`, `EnforceBudget`), app.py:132 (the Unicode check), defaults.py
  (`REDACT_BUDGET_S` and its comment, the `TEXTNORM_*` block), tests/test_textnorm_meta.py, tests/textnorm_mutants.py, tests/fixtures/textnorm_manifest.json,
  tests/test_textnorm.py (names and manifest pins), tests/test_textnorm_fixbatch.py (names, signature and cache pins), tests/test_textnorm_callers.py
  (the refusal lint), tests/test_textnorm_order137.py (`_counting_readings`), CHANGELOG.md (the fold items), tests/test_redact_settle_loop.py
  (`_stepping_clock`), tests/test_redact_fold_budget.py (`CountedClock`), SECURITY-README-final.md 2.6 (L43, L44), tickets/G1-result-review-1.md (M3-M5),
  the four callers of `injection_check`.
- Measured: on `git archive 374e6f3ff` copies in the drafter's scratchpad (`g10drafter/base`, and `g10drafter/proto` = base + the prototype of
  section 3 applied by a script); the shared tree was not edited and no test was run in it. Python 3.13.18, unidata 15.1.0, 4 cores; box load 3 to 7
  during the runs (other agents): CPU seconds of the thread (`time.thread_time()`), noisy upward. No pytest run (load above the rule, section 12).

## 1. Goal
(a) The DENY scan of the fold (`scan_holds`) and the injection read (`scan_views_no_value` through `RegexDetector`) stop at a caller's CPU
deadline (`time.thread_time()`), in the redactor's style: read at fixed points inside the work, refusal on expiry (fail closed: never a "no hit",
never a partial answer); the caller keeps its wall-clock guard. With no deadline (the default, None) every result is what it is today.
(b) The measured false-hit rates are published with date and unit, and the sentences that say "about 1 percent" or "not measured" are corrected.
(c) The NOT RUN items of the cost evidence that fit the box are named, sized and given a default.

## 2. What exists today (HEAD 9d8bc580a)
### 2.1 No clock in the fold
- grep of guard/textnorm.py and guard/injection.py for `time`, `thread_time`, `monotonic`, `perf_counter`, `deadline`, `timeout`: only the
  docstring of `scan_keyset` (textnorm.py:1272, "there is no clock or deadline"). Neither file imports `time`.
- Cost (evidence G1 B, CPU s): one `scan_holds` on 262,144 ASCII characters 0.36; 1 percent non-ASCII (longest prefix the weight cap takes,
  about 260,800) about 0.9; 236,879 distinct non-ASCII characters 4.8 to 5.5. 100 values without `scan_cache()` 39 s (ASCII), 105 s (1 percent);
  with it 0.43 and 1.7 s. 2,000 values with the cache 2.3 s (ASCII), about 20 s (1 percent), about 1,030 s extrapolated (distinct).
  `RegexDetector` on 2,000,000 characters 3.6 s (ASCII), 9.6 s (1 percent non-ASCII). The drafter's re-runs agree (section 11).
- The weight cap (`TEXTNORM_MAX_CHARS` = 262,144, `_checked`, `TextTooLong`) bounds the SIZE of one call, not its time.

### 2.2 Where the time of one scan goes (section 11.1)
`scan_holds` = `_checked` (the weight; memoised per long text, 0.55 s on the distinct text) + `_text_bundle` = `_readings` (2 texts x up to 2
`_prefix` passes: a Python generator over every character, NFKC, three `translate`; then 3 `_finish`) + `_squeezed` (the readings again with
other options, uppercase, a regex) + `_scan_keys` (2 marks variants x up to 4 tag texts x 2 steps, each `_converge`d over up to
`TEXTNORM_MAX_PASSES` = 3 passes) + the needle loop (`needle in view`, C speed) + the one-inserted-letter loop (`_holds_with_one_insertion`, a
Python `find` loop). On the distinct text: readings 0.65 s, squeezed 0.71, scan keys 4.24, one `_prefix` pass 0.18, one `fold` 0.18.
The fold is NOT cut into character chunks: NFKD and NFKC are context-dependent (a combining mark belongs to the letter before it, NFKC joins), so a
chunk boundary inside a sequence changes the result. The clock is read BETWEEN passes, never inside one; the overrun is one pass.

### 2.3 Who calls what (grep of the whole of src)
| function | callers in src | today's time bound | what a TextnormError does there |
|---|---|---|---|
| `scan_holds`, `scan_views`, `scan_cache`, `register_value`, `scan_needles` | NONE (tests and evidence scripts only; G1 review M3 still holds) | none | the docstring rule: a DENY caller REFUSES |
| `scan_views_no_value` | guard/injection.py `_holds` (via `_start_of_next`), `RegexDetector._read`, `RegexDetector._fit` | none (`TEXTNORM_INJECTION_MAX_CHARS` = 2,097,152 is a size) | `_read` and `_fit` CATCH `TextTooLong` (read in pieces, halve a piece); anything else reaches `injection_check`, which flags the run `guard_unavailable` (fail closed) |
| `fold`, `fold_view` | guard/redact.py `_fold_scan` (per line and view), `_line_hits` and `_dry_hits` (per match), `_aligned_fold`, `_alias_keys` | the redactor's deadline: first read AFTER the views of all lines are built (redact.py:1371), then per pattern, per suspect line, every 4,096 characters of the alignment | `redact_text` turns any non-RedactionError into `RedactionError(type name)` |
| `require_pinned_unidata` | app.py:132 (start-up) | constant (reads no text) | `UnidataMismatch`: refuse to start |
| `without_spacing_marks` | guard/runmap.py | linear, under the redactor's deadline between stages | as above |
The four callers of `injection_check` (runtime/agent_loop.py:323 `_screen`, k1b/loop.py:205, approvals/requests.py:37, approvals/cards.py:79) have no
wall-clock guard around it (read: none wraps it in a timeout or a thread). The redactor's callers have none either (G7 ticket, "For core-b").

### 2.4 The redactor's deadline (the style copied)
- A deadline is a `time.thread_time()` value (CPU seconds of the calling thread: load from other threads does not change the outcome; a thread
  that waits for the GIL or a lock does not advance it). `redact_text` sets ONE deadline `started + REDACT_BUDGET_S` (6.0) for the text and every
  view (runmap.py:555-587) and passes it as `redact(_deadline=)`; `_Redactor(…, deadline)` keeps it; `_fold_scan` uses it, or with none a FRESH
  `REDACT_BUDGET_S` per `find`.
- `_Redactor._over_budget(deadline)` (redact.py:1295): `if time.thread_time() > deadline: raise InputTooLarge("InputTooLarge")`;
  `_check_deadline` does it when the call has a deadline. Read at fixed points inside loops (per pattern, per line, per round, every 4,096
  characters, every 512 values, every 32 segments, every 1,024 units), never inside one C call (a regex pass, a `str.replace`). The overrun is stated
  as "budget + the unit in progress"; tests pin the reading points with a stepping clock patched on the MODULE attribute (`_stepping_clock`:
  `monkeypatch.setattr(R, "time", SimpleNamespace(thread_time=clock))`, one second more per reading) and `CountedClock`.
- A refusal is fail closed: nothing is shown; a legitimate document in the same text is lost (G7 SECURITY wording).

## 3. Design (part a)
### 3.1 The deadline is read INSIDE textnorm.py (default; D1)
The callers' loops cannot bound the cost: the injection read of a text under the cap is ONE call of `scan_views_no_value` (5.8 s measured on the
distinct text, no point to stop at), and a `scan_holds` consumer makes one call per value. A check only in the callers bounds the overrun at one
whole scan, about the size of the budget itself. Inside textnorm the overrun is one pass: 0.03 to 0.10 s measured on the distinct text (11.2).
So textnorm.py changes, and with it the hash, the manifest, the CHANGELOG re-copy list, the public names and the mutant list (section 4).

### 3.2 API (keyword-only; default None = unchanged)
- `scan_holds(*, text, value, deadline=None)` and `scan_views_no_value(raw, *, deadline=None)`.
- `deadline`: None or a `time.thread_time()` value; an `int` or `float`, not `bool`, not NaN (NaN compares false and would be "no deadline").
  Anything else raises `NotText("deadline must be a time.thread_time() value or None")` before any work.
- NOT given a deadline (D3): `scan_views` (its parameters are pinned: tests/test_textnorm_fixbatch.py:280 `list(sig.parameters) == ["raw", "value"]`,
  and it has no caller), `fold`, `fold_view`, `fold_views`, `squeeze`, `squeeze_views`, `identity_key(s)`, `could_be_same_person`, `allow_equal`,
  `names_equal`, `register_value`, `scan_keyset` (parameters pinned, test_textnorm_scan.py:91), `scan_needles`, `has_hidden_channel`,
  `has_mixed_script`. They are one or a few passes over one text or run on a value; the redactor reads its own clock around each `fold` call.

### 3.3 The error: `DeadlinePassed(TextnormError)` (name: D6)
```python
class DeadlinePassed(TextnormError):
    """The scan passed the caller's deadline (a ``time.thread_time()`` value); nothing was decided. A DENY caller REFUSES, as for any
    ``TextnormError``; the injection check flags the run."""
```
- Message `"the scan passed its deadline"`: no text, no value, no length.
- It is NOT a `TextTooLong`: `RegexDetector._read` and `_fit` catch `TextTooLong` and then read the text in pieces or halve a piece. Measured
  on a mutant that makes it a `TextTooLong` (11.3): a spent deadline on 300,000 characters reaches `scan_views_no_value` 4 times instead of once (the
  catch starts piece work after the deadline). Pinned (D-6, K4).
- Not runmap's `InputTooLarge`: textnorm.py is byte-copied by the demos with the `TEXTNORM_*` constants only (CHANGELOG re-copy rule); an import of
  runmap would break the copy and add a cycle (runmap imports textnorm). A future redaction consumer converts (3.6).
- The refusal lint (tests/test_textnorm_callers.py) builds its banned names from `__all__`, so `DeadlinePassed` is banned in handlers at once;
  a consumer that converts it must be listed in `REFUSAL_HANDLERS`.

### 3.4 Reading points
One helper, the clock read through the module attribute `time` (so a test patches `textnorm.time`):
```python
def _tick(deadline: float | None) -> None:
    """Fail closed (``DeadlinePassed``) when the caller's CPU deadline has passed; nothing when there is none."""
    if deadline is not None and time.thread_time() > deadline:
        raise DeadlinePassed("the scan passed its deadline")
```
| point | where | readings per call |
|---|---|---|
| P1 entry | `scan_holds` / `scan_views_no_value`: after the type check of `deadline`, BEFORE `_checked` and BEFORE the cache lookup (so a spent deadline raises on a cache hit too) | 1 |
| P2 after the weight | right after `_checked` (0.55 s on the distinct text) | 1 |
| P3 per prefix pass | `_readings`: before the NFKD + iota `_prefix`, and before the second `_prefix` (per marks variant) | 2 x 2 per readings call |
| P4 per squeeze view | `_squeezed`: per view of its `_views` call (the `_readings` inside it reads P3 too) | up to 6 |
| P5 per converge pass | `_converge`: before each pass (inside each `_scan_key`) | up to 3 x 16 |
| P6 after the bundle | `scan_holds` after `_text_bundle`, `scan_views_no_value` after `_all_views` | 1 |
| P7 insertion | `scan_holds`: before the insertion loop, per script view; `_holds_with_one_insertion`: every 4,096 `find` hits (both halves count) | 1 + views + hits/4,096 |
The needle loop (`needle in view` over at most 31 views) gets no reading: C speed, milliseconds at the cap. The number of readings is a function
of the text and the value only (fixed points), so a stepping clock pins each one. Measured: 18 readings for a 1,000-character Cyrillic/Han text
and a Han value; 17 for `"密码" x 5,000` with value `密码测试`, the 17th inside `_holds_with_one_insertion` (11.4).

The deadline is passed as an argument down the private chain (the redactor's style; explicit, no hidden state): `_text_bundle(raw, deadline=None)`,
`_readings(..., deadline=None)`, `_view_pairs(..., deadline=None)`, `_views(..., deadline=None)`, `_squeezed(..., deadline=None)`,
`_scan_keys(raw, deadline=None)`, `_scan_key(text, step, deadline=None)`, `_converge(text, step, deadline=None)`,
`_holds_with_one_insertion(view, needle, deadline=None)`. Every new parameter defaults to None, so `fold_views`, `identity_keys`,
`register_value`, `scan_views` and the tests that call or wrap the private functions (`_counting_readings` passes `*args, **kwargs` through;
test_textnorm_scan.py:287 calls `_converge(ch, _pass_b)`) are unchanged. Alternative (D2): a `contextvars` scope set by the two entry points.

### 3.5 Cache, determinism, overrun, cost
- `scan_cache()`: the bundle is built under the deadline of the call that builds it; it is stored only after a complete build (the store is after
  the build at HEAD, so a raise stores nothing); a call that finds it cached still reads P1, P6 and P7. Measured: a spent deadline on a cache hit
  raises (11.2).
- Determinism: with `deadline=None` no clock is read; results identical (measured on 564 corpus scans, 11.2). With a deadline the call returns
  EXACTLY what it returns without one, or raises `DeadlinePassed`. WHICH of the two depends on the machine's speed (as for the redactor): stated.
- Overrun: one pass (one `_prefix` or one `_converge` step) or 4,096 insertion hits; measured 0.03 to 0.10 s on the distinct text (11.2).
- Cost: one `time.thread_time()` read 0.28 to 0.31 us; about 20 to 60 readings per call: no measurable change on 262,144 ASCII characters
  (`scan_holds` 0.462 s without, 0.462 s with; ratio of bests 0.999; `scan_views_no_value` 0.994; 11.2).

### 3.6 Callers
- guard/injection.py: `RegexDetector.check` computes `deadline = time.thread_time() + defaults.INJECTION_BUDGET_S` when that constant is not
  None (D4) and passes it: `_score(text, deadline)` -> `_read(text, deadline)` -> `scan_views_no_value(..., deadline=deadline)`, `_fit(piece,
  deadline)`, `_start_of_next(text, start, end, deadline)` -> `_holds(window, need_kept, need_letters, deadline)`. The final raw squash of `_score`
  (one regex over the text) needs no reading. `DeadlinePassed` is not caught by `_read`/`_fit`; `injection_check` flags the run `guard_unavailable`.
  The `Detector` protocol (`check(text, source)`) is unchanged; other detectors are untouched. Measured on the prototype (11.5).
- guard/redact.py: NOTHING at HEAD. The redactor calls `fold` and `fold_view` only, under its own reads. Its one unread stretch is the view
  building of `_fold_scan` (all lines, all views, before the first read at redact.py:1371): one `fold` of the distinct 236,879-character text
  is 0.18 s, so at most about 4 x 0.18 s before the first read (ESTIMATE, not measured as one figure). A read per 4,096 characters of non-ASCII
  lines in that loop is optional (D8; mutant KR1 then goes to tests/redact_mutants.py).
- The redactor's deadline reaching `scan_holds`: nothing to wire at HEAD (no caller). Rule for the consumer that lands (G3 known values, a
  blocklist, a has-secret check), written into the `scan_holds` docstring: pass the call's deadline (`self._deadline`, or `self._scan_deadline`
  inside `_fold_scan`) as `deadline=`, and convert at the call: `except textnorm.DeadlinePassed: raise InputTooLarge("InputTooLarge") from None`
  (the gate code stays `mask_budget_exceeded`), with that function added to `REFUSAL_HANDLERS`.
- app.py `require_pinned_unidata`: no text, no deadline.

### 3.7 The source change (exact, as prototyped; textnorm.py)
1. `import time` after `import threading`.
2. `"DeadlinePassed",` in `__all__` after `"CoverageRefused",`; the class of 3.3 after `CoverageRefused` or before `EmptyView`; `_deadline_checked`
   (the type rule of 3.2) and `_tick` (3.4) after it.
3. Module docstring: "THE PUBLIC NAMES (36" -> "(37", and ``DeadlinePassed`` added to the "Errors:" list (pinned by
   test_textnorm_fixbatch.py:666 `test_the_module_docstring_lists_every_public_name`); a paragraph "DEADLINE" after "ONE INSERTED LETTER": the
   text of 3.2, 3.4 (the table in words), 3.5.
4. `scan_keyset` docstring: "there is no clock or deadline" -> "it reads no clock (the deadline is ``scan_holds``'s and ``scan_views_no_value``'s)".
5. The parameters and reads of 3.4; `scan_holds` ends with an explicit loop over the script views (P7) instead of the `any(...)` generator.
6. `scan_holds` docstring: the deadline sentence and the consumer rule of 3.6.

## 4. Pins and counts that change (exact)
| pin | where | today | after G10 |
|---|---|---|---|
| sha256 of guard/textnorm.py | tests/fixtures/textnorm_manifest.json `files` | `e7a93738f10e7ea66e164c929d20c0405a0730d41852e0ff88856720ea6cdbee` | recomputed after the LAST edit of the file (`sha256sum` of the LF bytes); `test_the_manifest_pins_the_files_a_demo_copies` (tests/test_textnorm.py:3246) fails until it is |
| the hash in the CHANGELOG | CHANGELOG.md:650 (the manifest test asserts `sha in text` for every manifest hash) | the old hash | a NEW CHANGELOG item for G10 that lists the new hash (the fold item at 647-654 stays as the record) and repeats the re-copy rule: the demos re-copy textnorm.py (the other four files are unchanged) |
| mutant count | tests/textnorm_mutants.py docstring line 12 ("240 mutants"); tests/test_textnorm_meta.py:90 the test NAME (`test_a_the_list_has_240_mutants_77_of_…`) and `== 240` twice at :92; `len(names[28:]) == 212` at :97; `len(names[163:]) == 77` at :123; the prefix set over `names[163:]` at :126-150 ("the fix batch mutants": `deadline` is not in it); :200 `assert len(rows) == 240`; :363 `== 240` | 240 (228 behaviour, 12 wording) | 249 = 240 + the 9 textnorm/injection mutants of section 6 (appended at the end: names[240:]); the test name becomes `test_a_the_list_has_249_mutants_…_77_of_the_p1b_fix_batch_and_9_of_g10_…`; `names[28:]` 221; `names[163:]` -> `names[163:240]` at :123 and :149 (stays 77, same prefix set) and a new `assert len(names[240:]) == 9 and all(n.split(":")[0] in {"deadline", "injection"} for n in names[240:]), "the 9 of G10"`; split by `split_counts()`: expected 237 behaviour, 12 wording (every G10 mutant changes behaviour; VERIFY by running `split_counts`) |
| the set of killer files | tests/test_textnorm_meta.py:179 `{m.test_file for m in mm.M} == {mm.T, mm.G, mm.SC, mm.SB, mm.FB, mm.O, mm.RO, mm.R2}`; :181-190 the list of files whose test names must be unique | 8 files | + the new constant (`DL = "tests/test_textnorm_deadline.py"`) in the set, and the new file in the uniqueness list |
| CHANGELOG mutant sentence | meta test i: `f"{len(mm.M)} mutants in\n  `tests/textnorm_mutants.py`"` must occur | "The list holds 240 mutants in\n  `tests/textnorm_mutants.py`" (CHANGELOG:637-638) | the G10 item holds "249 mutants in\n  `tests/textnorm_mutants.py`" (the line break exactly there) |
| re-pointed mutants | tests/textnorm_mutants.py: the `old` text of 9 mutants no longer occurs once in the prototype (meta test g fails): indices 63 "scan: squeeze_views gives one view", 106 "marks: squeeze_views has no marks-dropped views", 109 "marks: a view is repeated", 181 "insertion: the match is never made" (textnorm.py), 177 "injection: the call names no value", 207 "injection: a module builds its own views", 233 "injection: the pieces do not overlap", 235 "injection: the new piece ignores the letters it holds", 238 "injection: the second half of a halved piece starts at the halfway point" (injection.py) | as is | each `old` and `new` re-copied from the edited source (same mutation, new text), killer and expect unchanged; each re-run alone (`uv run python tests/textnorm_mutants.py "<name>"`) and recorded |
| public names | tests/test_textnorm.py:1199 `test_the_public_names_are_exactly_the_listed_thirty_six` (name, list, `== 36` at :1241); tests/test_textnorm_fixbatch.py:665-668 (docstring "The 36 names (33 of the fold, 3 for the fold scan of the redactor)", `== 36`) | 36 | 37: name `…_listed_thirty_seven`, `"DeadlinePassed"` in the list, `== 37`; fixbatch docstring "The 37 names (34 of the fold, …)" and `== 37` |
| `TESTS` list | tests/textnorm_mutants.py:44 | 9 files | `DL` added before `D` (a killer file; meta :173-175 keeps `TESTS[:3]` and `TESTS[-1] == D`) |
| unchanged, checked | `scan_views` parameters (fixbatch:280), `scan_keyset` parameters (scan:91), the cache read counts (fixbatch:250-272, order137:357-366: the build still calls `_readings` the same number of times), the siblings / importers pins | — | unchanged (the prototype changes none of them; NOT run, section 12) |
| defaults.py | new `INJECTION_BUDGET_S` (D4) with its comment | absent | not hashed; not a `TEXTNORM_*` constant, so not in the demo re-copy list (injection.py is not copied) |

## 5. Tests (new file tests/test_textnorm_deadline.py; the clock is patched on the module attribute: `monkeypatch.setattr(tn, "time",
SimpleNamespace(thread_time=clock))`, as `_stepping_clock` does for redact.py; every assertion message carries the tag the mutants expect)
- D-1 None is unchanged: every string row of tests/fixtures/textnorm_corpus.json scanned three ways (a in b, b in a, a inside "x … y"): the result
  (bool or the error class name) with no argument, `deadline=None` and `deadline=time.thread_time() + 600` is the same (prototype: 564 of 564);
  `scan_views_no_value` tuples equal on the same texts. Tag `DEADLINE-NONE`.
- D-2 a spent deadline: `deadline=time.thread_time() - 1` raises `DeadlinePassed` for `scan_holds` (a text that HOLDS the value: `"a summary"`,
  `"Mary"`) and for `scan_views_no_value`; `pytest.raises` and, in the same test, a call that catches nothing else (a returned True or False fails
  with `DEADLINE-NOT-FALSE`). Tags `DEADLINE-SPENT`, `DEADLINE-NOT-FALSE`.
- D-3 every reading point (stepping clock, one second per reading): for T = `"the summary of " + "жизнь " x 200 + "密的码测试"`, V = `"密码测试"`, count the
  readings with a far deadline (N; 18 on the prototype); for every k in 1..N-1, `deadline=k + 0.5` raises at reading k+1; the set of functions that
  raised (frame of the `_tick` caller) is exactly {`scan_holds`, `_readings`, `_squeezed`, `_converge`}; and for T2 = `"密码" x 5,000`, V, the LAST
  reading is in `_holds_with_one_insertion`. Tag `DEADLINE-POINTS`.
- D-4 the cache path: inside `scan_cache()`, a call with a far deadline, then the same text with a spent deadline raises. Tag `DEADLINE-CACHE`.
- D-5 a raise during the build stores no bundle: inside `scan_cache()`, a stepping clock trips the build at reading 3; `_SCAN_CACHE.get().bundles`
  is empty; the next call without a deadline answers as without one. Tag `DEADLINE-NO-PARTIAL`.
- D-6 the class: `issubclass(DeadlinePassed, TextnormError)` and not `TextTooLong`; behaviour: `RegexDetector(0.5)._score("ab " * 100_000,
  time.thread_time() - 1)` raises `DeadlinePassed` after exactly ONE `scan_views_no_value` call (a spy; the TextTooLong mutant makes 4). Tag `DEADLINE-NOT-SIZE`.
- D-7 bad deadline values: `True`, `"1"`, `float("nan")`, `[1.0]` raise `NotText` (no clock read: the stepping clock counter stays 0). Tag `DEADLINE-TYPE`.
- D-8 injection: with `defaults.INJECTION_BUDGET_S` patched to `-1.0`, `injection_check(RegexDetector(0.5), "hello world", "t")` is flagged with
  `reason_code == "guard_unavailable"`; with None, the verdict of a steering text and of a clean text equals today's. Tag `DEADLINE-INJECTION`.
- D-9 (only with D8) tests/test_redact_fold_budget.py: three non-ASCII lines of 5,000 characters and `CountedClock(0.0, 1, 100.0)` raise
  `InputTooLarge` before `_line_hits` runs (a spy). Tag `VIEW-LOOP-BUDGET`.
- D-10 perf (`@pytest.mark.perf`, outside the mutant lists): 262,144 ASCII characters, best of 5, with and without a far deadline: ratio < 1.10.

## 6. Mutants (appended to tests/textnorm_mutants.py, test_file `tests/test_textnorm_deadline.py`)
| # | name | change | killer | expect |
|---|---|---|---|---|
| 241 | deadline: the clock is never read | `_tick`: `if deadline is not None and time.thread_time() > deadline:` -> `if False:` | D-2 | `DEADLINE-SPENT` |
| 242 | deadline: ignored on a cache hit | `_text_bundle`: on a cache hit return before P1 (move P1 of `scan_holds` after `_text_bundle`) | D-4 | `DEADLINE-CACHE` |
| 243 | deadline: a spent deadline answers no hit | P1 of `scan_holds` -> `if deadline is not None and time.thread_time() > deadline: return False` | D-2 | `DEADLINE-NOT-FALSE` |
| 244 | deadline: the error is a TextTooLong | `class DeadlinePassed(TextnormError):` -> `class DeadlinePassed(TextTooLong):` | D-6 | `DEADLINE-NOT-SIZE` |
| 245 | deadline: the scan keys get no deadline | `tuple(sorted(_scan_keys(raw, deadline)))` -> `tuple(sorted(_scan_keys(raw)))` | D-3 | `DEADLINE-POINTS` |
| 246 | deadline: no reading between passes | `_tick(deadline)` removed from `_converge` | D-3 | `DEADLINE-POINTS` |
| 247 | deadline: no reading in the insertion loop | the `_tick` of `_holds_with_one_insertion` removed | D-3 | `DEADLINE-POINTS` |
| 248 | deadline: a bad value is no deadline | the type check of `_deadline_checked` removed | D-7 | `DEADLINE-TYPE` |
| 249 | injection: the detector passes no deadline | `_score(text, …deadline…)` -> `_score(text)` in `RegexDetector.check` | D-8 | `DEADLINE-INJECTION` |
Measured on the prototype: 244 gives 4 calls instead of 1 (killed by D-6's count). The others are NOT RUN. No mutant for P2 (the read after the
weight): removing it changes only time, not a result (D5). KR1 "the view loop reads no clock" goes to tests/redact_mutants.py only with D8.
Search strings: copy each from the formatted source after `ruff format`; meta test g requires each to occur exactly once.

## 7. The false-hit rates (part b)
### 7.1 What is documented today, and what is wrong with it
- defaults.py:234-242 (the INSERTION comment): "the extra matches the insertion adds stay near 1% or lower per 10,000 characters of text". It
  measures only what the ONE-INSERTED-LETTER match ADDS, per script, on Bible text (CHANGELOG "ONE INSERTED LETTER"). It is the only rate in the
  code and is read as the scan's rate (G1 review M5, ESCALATIONS E11). The whole scan (`scan_holds`: exact needles, squeeze, scan keys and the
  insertion) hits ordinary Latin text far more often for short values: 4-letter names 5.22 percent of 10,000-character chunks, 5x the stated band.
  True for what it measures; misleading by what it leaves out; no unit says "per scan of one value".
- SECURITY-README-final.md 2.6 L43: "Not measured on ordinary text. UNVERIFIED. OPEN." Now measured for Latin text; non-Latin on synthetic text only.
  L43 also says "innocent text may be masked or withheld": at HEAD no redaction path calls `scan_holds` (2.3), so the rate has NO consumer yet.
- L44: "The fold's own time use has no deadline. The injection check reads up to 2,097,152 characters with no clock. Not measured." Now measured (E11).
- SECURITY.md (repo root) says nothing about the fold; docs/ has no fold page (docs holds the Slack app pages only).
### 7.2 Text to publish (dated, unit stated each time)
For SECURITY.md (stated-limits list) and the G10 CHANGELOG item, exactly:
> FALSE HITS OF THE FOLD SCAN (measured 2026-11-20; Python 3.13.18, Unicode 15.1.0; evidence handover/core-c/evidence/G1-false-hits-and-cost.md).
> Unit: the share of scans in which `scan_holds` reports a protected value in a 10,000-character chunk of ordinary text that does not hold it
> (one scan = one chunk, one value). Latin text (repository prose and code, Python standard-library docstrings, generated Markov text; 199,000
> scans per class): names of 4 letters 5.2 percent, 5 letters 0.8 percent, 6 letters 0.25 percent, 8 letters or more 0 (none in 199,000); a
> common word of 5 to 10 letters used as a street or host name 4.10 percent; short ASCII identifiers of 4 to 5 characters 0.196 percent; 6 digits
> 0.005 percent; 8, 12 or 16 digits 0. The hits include a value found inside a longer word ("Mary" in "summary") and across spaces and
> punctuation ("ab12" in "ab 12"); the kinds were not counted apart. Non-Latin values (Chinese, Russian, Arabic, Hindi) were measured only on
> SYNTHETIC text built from letter-frequency guesses, because no real text of those languages was available: their real rates are UNKNOWN (on
> the synthetic text short values hit often: 2 Han characters drawn by frequency 26 percent, 4 to 8 Cyrillic letters 14 percent). A false hit is
> the safe side (more masking, or a refusal), never a leak. No redaction path uses `scan_holds` today; these are the rates its first consumer
> will see.
For defaults.py, the clause "stay near 1% or lower per 10,000 characters of text" becomes:
> stay near 1% or lower per 10,000 characters of text. That figure is only what the one-inserted-letter match ADDS, per script, on Bible
> text; it is NOT the false-hit rate of the scan. The whole of scan_holds (exact needles included) reports a protected value that is not there
> in this share of 10,000-character chunks of ordinary Latin text: 4-letter names 5.2%, 5-letter 0.8%, 6-letter 0.25%, 8+ letters 0, common words
> of 5-10 letters 4.10%, ASCII ids of 4-5 characters 0.196%, 6 digits 0.005% (measured 2026-11-20; handover/core-c/evidence/G1-false-hits-and-cost.md;
> non-Latin: synthetic text only, real rates unknown).
For SECURITY-README L43 (the owner of the SECURITY wording applies it): "L43 Over-matching. A known name can be found inside a longer word
(`Mary` in `summary`) or across a space (`ab12` in `ab 12`). MEASURED 2026-11-20, per scan of one 10,000-character chunk of ordinary Latin
text: 4-letter names 5.2%, 5 letters 0.8%, 6 letters 0.25%, 8 or more 0; common words of 5-10 letters 4.10%; ASCII ids of 4-5 characters
0.196%; 6 digits 0.005%. Non-Latin: synthetic text only, real rates unknown. No redaction path uses this scan yet; when one does, innocent text
may be masked or withheld at these rates. STATED." L44: "The fold had no deadline (measured 2026-11-20: one scan up to 5.5 s CPU on a
236,879-character text, the injection read of 2,000,000 characters 3.6 to 9.6 s, up to 15.6 s on a mixed text). G10 adds one (CPU clock only)."
For the "G1 ticket": this branch has no G1 design ticket file (tickets/G1-result-review-1.md is the review; the fold's record is the CHANGELOG item
"The fold (ticket G, part G1)"). Add to the review table: M4 "DEADLINE: G10 (ORDER 023)", M5 "MEASURED (E11, evidence G1-false-hits-and-cost.md);
published text G10 7.2; consumer pending". The CHANGELOG fold item is not edited (record); the G10 item carries the text.

## 8. The NOT RUN items (part c)
| item | fits the box at low load? | size | default (D7) |
|---|---|---|---|
| split of the Latin hits into whole-word / inside a word / across spaces | yes: the Latin part of run 1 again with a classifier per hit, one process, minutes | 9 Latin classes x 1,000 values x 199 chunks, with the cache | an evidence runner is doing it: not duplicated. Its result goes into 7.2 (replace "the kinds were not counted apart") |
| 2,000 values without the cache | ASCII: about 756 s, one process: fits at load below 2; 1 percent non-ASCII about 2,023 s (34 min): only a quiet window; distinct about 10,000 to 11,400 s (3 h): does not fit | extrapolated from 20 values (E11) | run ASCII only, at load below 2, with `deadline=None`; the others stay extrapolations. The row has no consumer: no code scans per value without the cache; the consumer rule (3.6) says to use `scan_cache()` |
| real non-Latin prose | NO: no Han, Cyrillic, Arabic or Devanagari text on the box (E11's search), no network corpus allowed | — | needs the lead's leave to fetch (the CHANGELOG names corpora already used for the insertion minimums: christos-c/bible-corpus, UD Japanese GSD and PUD); until then 7.2 says "unknown" |
The drafter ran none of them (load 3 to 7 during this work).

## 9. Decisions for the lead (default first; each with the alternative and its consequence)
- D1 Where the clock is read. DEFAULT: inside textnorm.py (overrun one pass, 0.03-0.10 s measured; textnorm pins change, section 4). ALT: only in
  the callers' loops (no textnorm change, no re-copy): overrun one whole scan (up to 5.8 s measured), so the injection read of one text under the
  cap stays unbounded.
- D2 How it is passed. DEFAULT: an explicit `deadline` argument down the private chain. ALT: a contextvar scope (fewer signatures; hidden state;
  the same reading points).
- D3 Which public functions take it. DEFAULT: `scan_holds`, `scan_views_no_value`. ALT: also `scan_views` (breaks the fixbatch:280 pin, no caller).
- D4 The injection budget. DEFAULT: new `defaults.INJECTION_BUDGET_S = 30.0` CPU seconds, about 2x the worst text measured (15.6 s for 2,000,000
  characters with every other character a distinct non-ASCII letter; 9.8 s with 1 percent non-ASCII; 3.9 s ASCII; at load 3). A machine 2x slower
  than this box refuses that 15.6 s text (`guard_unavailable`, fail closed: the run is flagged). ALT: None (the deadline exists, nothing uses it;
  E11 half open); or `REDACT_BUDGET_S` (6.0: every 2,000,000-character text with 1 percent non-ASCII is flagged: a new false abstain).
- D5 The read after the weight (P2): keep without a mutant (it changes time only).
- D6 The error name: `DeadlinePassed`. ALT: a code-style message like the redactor's (`DeadlinePassed("FoldDeadline")`).
- D7 NOT RUN rows: as in section 8.
- D8 A read in the redactor's view-building loop (`_fold_scan`): DEFAULT not in G10 (the stretch is at most about 4 folds of one text, about 0.7 s
  on the distinct text, ESTIMATED; redact.py is G4/G8's file now). ALT: in G10 with D-9 and KR1.
- D9 The wording owner: SECURITY.md and the SECURITY-README L43/L44 lines are applied by the SECURITY wording lane, not by the G10 builder (default);
  the defaults.py comment and the CHANGELOG item are the builder's.

## 10. Stated limits after G10
- CPU clock of the thread only (as the redactor): waiting for the GIL, a lock or I/O does not advance it. The wall-clock guard stays the caller's;
  none of the four injection callers has one today (for core-b, next to the G7 list).
- Overrun: one pass over the whole text, or 4,096 insertion hits (0.03 to 0.10 s measured on the distinct text).
- The outcome depends on the machine: a slow machine refuses a text a fast one scans (fail closed: the injection run is flagged, a DENY caller refuses).
- A hostile author can force the refusal (`DeadlinePassed`, `guard_unavailable`): the legitimate rest of the text is lost for that run.
- No deadline in `register_value`, `fold`, `fold_view`, `identity_keys`, `scan_views`, `scan_keyset` and the other single-pass functions.
- 2,000 values without `scan_cache()` stays O(values x text) (deadline-bounded, not faster).

## 11. Measured by the drafter (scripts in the scratchpad `g10drafter/scripts/`: prof.py, patch.py, patch_inj.py, measure.py, inj.py, inj_dist.py, k4.py, ins.py)
### 11.1 Cost of the parts on HEAD (`g10drafter/base`, one run each, CPU s, load 3.3)
| text | weight | fold | one `_prefix` | readings | squeezed | scan keys | `scan_views_no_value` | `scan_holds` |
|---|---|---|---|---|---|---|---|---|
| 262,144 ASCII | 0.000 | 0.041 | 0.043 | 0.139 | 0.152 | 0.257 | 0.495 | 0.472 |
| 260,400 chars, 1 percent non-ASCII | 0.012 | 0.095 | 0.081 | 0.331 | 0.408 | 0.536 | 1.267 | 1.279 |
| 236,879 distinct non-ASCII | 0.545 | 0.177 | 0.177 | 0.652 | 0.705 | 4.244 | 5.829 | 5.668 |
### 11.2 The prototype (`g10drafter/proto`: base + patch.py; load 3.2)
- One `time.thread_time()` read: 0.28 to 0.31 us.
- Overhead on 262,144 ASCII characters, 7 alternating runs: `scan_holds` best 0.4622 s without, 0.4618 with a far deadline (ratio 0.999; medians
  0.473 / 0.483); `scan_views_no_value` best 0.4626 / 0.4598 (0.994; medians 0.468 / 0.475). Within noise.
- Equality: 564 corpus scans (the 188 of 191 rows whose a and b are strings, x 3) give the same result with and without a far deadline (303 of them refused both ways).
- Stepping clock: 18 readings (P1 x1, P2 x1, P3 x8, P4 x1, P5 x4, P6 x1, P7 x2); deadline k + 0.5 raised at reading k+1 in 18 of 18 cases;
  raising functions {scan_holds: 5, _readings: 8, _squeezed: 1, _converge: 4}.
- Cache: a spent deadline on a cache hit raises `DeadlinePassed`.
- Real deadline on the distinct text: `scan_holds` budget 0.5 s -> raised after 0.539 s (overrun 0.039), budget 2.0 -> 2.097 (0.097);
  `scan_views_no_value` 0.5 -> 0.531 (0.031), 2.0 -> 2.035 (0.035).
### 11.3 The TextTooLong mutant (244), prototype copy `g10drafter/k4`
`RegexDetector._score("ab " * 100000, spent)`: `DeadlinePassed` after 4 `scan_views_no_value` calls (prototype: 1).
### 11.4 The insertion reading point
T = "密码" x 5,000, V = "密码测试": result False, 17 readings; the 17th is in `_holds_with_one_insertion`.
### 11.5 The injection read with the deadline (prototype + patch_inj.py; 2,000,000-character texts; one run each)
| text | no deadline | far deadline (600 s) | budget 1.0 s |
|---|---|---|---|
| ASCII words | 3.88 s, not flagged | 3.99 s, same verdict | flagged `guard_unavailable` after 1.01 s |
| 1 percent non-ASCII | 9.83 s, not flagged | 10.03 s, same verdict | flagged after 1.01 s |
| every other character a distinct non-ASCII letter (1,000,000 of them, cycling from U+0081) | 15.6 s, not flagged | — | — |
| distinct non-ASCII letters only, no ASCII | 0.9 s, flagged `guard_unavailable` by `_start_of_next` (too few a-z letters: the known M6 behaviour, not the deadline) | — | — |

## 12. NOT verified
- No pytest run, no mutant run (box load 3 to 7, above the low-load rule for a suite): the pins of section 4 come from reading the tests and from
  the prototype's mutant-string count (9 search strings missing); the 237/12 split is computed by hand.
- The cache read-count tests (fixbatch:250-272, order137:357-366) and the signature pins were read, not run, against the prototype.
- The redactor's view-building stretch (D8) as one figure: estimated from one `fold` (0.18 s).
- The worst text for the injection read: only the four of 11.5; a text tuned for more passes (tag characters, Mc/Sk marks: 16 scan keys) was not built.
- The NOT RUN rows of section 8. Python 3.12. A slower machine than this box.
