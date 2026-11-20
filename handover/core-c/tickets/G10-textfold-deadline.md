# G10: a deadline for the text fold, the published false-hit rates, and the NOT RUN cost items (lead ORDER 023, escalation E11)

Status: DRAFT v1 for plan review, core-c drafter, 2026-11-20. Nothing is built. Path class: guard (textnorm, injection) and redaction (one loop
in redact.py). A builder with no other context builds from this file. Sections: 0 base, 1 goal, 2 what exists today, 3 design (part a),
4 pins that change, 5 tests, 6 mutants, 7 the false-hit text (part b), 8 the NOT RUN items (part c), 9 decisions for the lead, 10 stated
limits, 11 measured by the drafter, 12 NOT verified.

## 0. Base and what was read
- Base: cloud/core-c 374e6f3ff (board 09:35:38Z; code head 9d8bc580a, G7 fix round 6). Line numbers are of that head.
- Read: evidence/G1-false-hits-and-cost.md, ESCALATIONS.md E11, ORDERS.md ORDER 023, guard/textnorm.py (whole scan path), guard/injection.py,
  guard/redact.py (`_Redactor.__init__`, `find`, `settle`, `_check_deadline`, `_over_budget`, `_line_hits`, `_fold_scan`, `_aligned_fold`,
  `_alias_keys`), guard/runmap.py (`InputTooLarge`, `redact_text`, `_decoded_masks`, `EnforceBudget`), app.py (the Unicode check), defaults.py
  (`REDACT_BUDGET_S` and its comment, the `TEXTNORM_*` block), tests/test_textnorm_meta.py, tests/textnorm_mutants.py, tests/fixtures/textnorm_manifest.json,
  CHANGELOG.md (the fold items), tests/test_redact_settle_loop.py (`_stepping_clock`), tests/test_redact_fold_budget.py (`CountedClock`),
  SECURITY-README-final.md 2.6 (L43, L44), tickets/G1-result-review-1.md (M3, M4, M5).
- Measured: on a `git archive` copy of HEAD in the drafter's scratchpad (`head/`) and a prototype copy (`proto/`); the shared tree was not edited
  and no test was run in it. Python 3.13.18, unidata 15.1.0, 4 cores; box load 5 to 7 during the runs (other agents): CPU seconds of the thread, noisy upward.

## 1. Goal
(a) The DENY scan of the fold (`scan_holds`, `scan_views`) and the injection read (`scan_views_no_value` through `RegexDetector`) stop at a
caller's CPU deadline (`time.thread_time()`), in the redactor's style: checked at fixed points inside the work, refusal on expiry (fail
closed, never a "no hit" and never a partial answer), the caller keeps its wall-clock guard. With no deadline (the default, None) every
result is byte-for-byte what it is today. (b) The measured false-hit rates are published with their date and unit, and the sentences that
say "about 1 percent" or "not measured" are corrected. (c) The NOT RUN items of the cost evidence that fit the box are named and sized.

## 2. What exists today (HEAD 9d8bc580a)
### 2.1 No clock in the fold
- grep of guard/textnorm.py and guard/injection.py for `time`, `thread_time`, `monotonic`, `perf_counter`, `deadline`, `timeout`: only the
  docstring of `scan_keyset` (textnorm.py:1272, "there is no clock or deadline"). No import of `time` in either file.
- The cost (evidence G1 B, CPU s): one `scan_holds` on 262,144 ASCII characters 0.36; on 1 percent non-ASCII (the longest prefix the weight
  cap takes, about 260,800) about 0.9; on 236,879 distinct non-ASCII characters 4.8 to 5.5. 100 values without `scan_cache()` 39 s (ASCII) and
  105 s (1 percent); with it 0.43 and 1.7 s. 2,000 values with the cache 2.3 s (ASCII), about 20 s (1 percent), about 1,030 s extrapolated
  (distinct). `RegexDetector` on 2,000,000 characters 3.6 s (ASCII), 9.6 s (1 percent non-ASCII).
- The weight cap (`TEXTNORM_MAX_CHARS` = 262,144, `_checked`, `TextTooLong`) bounds the SIZE of one call, not its time: the 5.5 s row is under it.

### 2.2 Where the time goes inside one scan (drafter, section 11.1)
One `scan_holds` = `_checked` (the weight; memoised per text, 0.5 s on the distinct text) + `_text_bundle` = `_readings` (2 texts x up to 3
readings, each a `_prefix` pass: a Python generator over every character, then NFKC and three `translate`) + `_squeezed` (the same readings again,
uppercase and a regex) + `_scan_keys` (2 variants x up to 4 tag texts x 2 steps, each `_converge`d over up to `TEXTNORM_MAX_PASSES` = 3 passes
of `_prepare` + translate + casefold) + the needle loop (`needle in view`, C speed) + the one-inserted-letter loop (`_holds_with_one_insertion`, a
Python `find` loop). Measured on the distinct text: readings 0.76 s, squeezed 0.82 s, scan keys 3.9 s, one `_prefix` pass 0.17 s, one `fold` 0.18 s.
The biggest single step that cannot be interrupted without changing the fold is ONE pass (one `_prefix` or one `_scan_key` step): 0.17 to 0.35 s on the
worst text measured. NFKD/NFKC are context-dependent (a mark belongs to the letter before it), so the fold is NOT cut into character chunks:
a chunk boundary inside a combining sequence changes the result. The clock is read between passes, never inside one.

### 2.3 Who calls what (grep of src, the whole package)
| function | callers in src | today's bound | what a TextnormError does there |
|---|---|---|---|
| `scan_holds`, `scan_views`, `scan_cache`, `register_value`, `scan_needles` | NONE (tests and evidence scripts only; G1 review M3 still true) | none | the docstring rule: REFUSE (DENY path) |
| `scan_views_no_value` | guard/injection.py `_holds`, `RegexDetector._read`, `_fit` | none (`TEXTNORM_INJECTION_MAX_CHARS` = 2,097,152 is a size, not a time) | `_read` and `_fit` CATCH `TextTooLong` (fall back to pieces, halve a piece); anything else reaches `injection_check`, which flags `guard_unavailable` (fail closed) |
| `fold`, `fold_view` | guard/redact.py `_fold_scan` (per line, per view), `_line_hits` and `_dry_hits` (per match), `_aligned_fold` (whole line, then per character), `_alias_keys` (per stored value) | the redactor's deadline, read AFTER all views of all lines are built (redact.py:1371), then per pattern, per suspect line, every 4,096 characters of the alignment | `redact_text` turns any non-RedactionError into `RedactionError(type name)`: fail closed, but not the `InputTooLarge` code |
| `require_pinned_unidata` | app.py:132 (start-up) | constant (no text) | `UnidataMismatch`: refuse to start |
| `without_spacing_marks` | guard/runmap.py | per text, linear | as above |

The injection callers (runtime/agent_loop.py `_screen`, k1b/loop.py:205, approvals/requests.py:37, approvals/cards.py:79) have NO wall-clock guard
around `injection_check` (read: none of the four wraps it in a timeout). The redactor's callers have none either (G7 ticket "For core-b").

### 2.4 The redactor's deadline (the style to copy)
- A deadline is a `time.thread_time()` value (CPU seconds of the calling thread: load from other threads does not change the outcome; a thread
  waiting on the GIL or a lock does not advance it). `redact_text` sets ONE deadline `started + REDACT_BUDGET_S` (6.0) for the text and every
  view (runmap.py:555-587); `redact(_deadline=)` and `redact_many(_deadline=)` pass it on; `_Redactor(…, deadline)` keeps it.
- `_Redactor._over_budget(deadline)` (redact.py:1295): `if time.thread_time() > deadline: raise InputTooLarge("InputTooLarge")`; `_check_deadline`
  does it when the call has one. `_fold_scan` uses the call's deadline or, with none, a FRESH `REDACT_BUDGET_S` per `find`.
- Read at fixed points inside loops (per pattern, per line, per round, per 4,096 characters, per 512 values, per 32 segments, per 1,024 units);
  never inside one C call (one regex pass, one `str.replace`). The overrun is stated as "budget + the unit in progress", and the tests pin the
  reading points with a stepping clock (`_stepping_clock`, one second more per reading; `CountedClock`).
- A refusal is fail closed: nothing is shown, the legitimate rest of the document is lost (SECURITY wording of G7).

## 3. Design (part a)
### 3.1 Where the deadline lives: in textnorm.py (drafter's default; alternative in 9, D1)
The callers' loops cannot bound the cost: the injection read of a text under the cap is ONE call of `scan_views_no_value` (5.5 s on the distinct
text, no point to stop at), and a future `scan_holds` caller has one call per value. A check in the callers only bounds the overrun at one whole
scan (up to 5.5 s, about the budget itself). Inside textnorm the overrun is one pass (0.17 to 0.35 s measured). So the clock is read in textnorm.py,
and textnorm.py changes (its hash, the manifest, the CHANGELOG re-copy list, the mutant count: section 4).

### 3.2 API (keyword-only, default None = unchanged behaviour)
- `scan_holds(*, text, value, deadline=None)`, `scan_views(raw, value, *, deadline=None)`, `scan_views_no_value(raw, *, deadline=None)`.
- `deadline`: `None` or a `time.thread_time()` value (a `float` or `int`, not `bool`); anything else raises `NotText("deadline must be a
  time.thread_time() value or None")` before any work (a typo must not turn into "no deadline").
- NOT given a deadline (decision D3): `fold`, `fold_view`, `fold_views`, `squeeze*`, `identity_key(s)`, `could_be_same_person`, `allow_equal`,
  `names_equal`, `register_value`, `scan_keyset`, `scan_needles`, `has_hidden_channel`, `has_mixed_script`. They are one pass (or a few) over one
  text, or run on a value (short), and the redactor's loops already read its clock around each `fold` call (3.6).

### 3.3 The error: `DeadlinePassed(TextnormError)`
- New class in textnorm.py, added to `__all__` (the public-name count changes: section 4): "The scan passed the caller's deadline (a
  `time.thread_time()` value); nothing was decided. A DENY caller REFUSES, as for any TextnormError." Message: `"the scan passed its deadline"`
  (no text, no value, no length that could leak).
- It is NOT a `TextTooLong`: `RegexDetector._read` and `_fit` catch `TextTooLong` and then read the text in pieces or halve a piece; a deadline
  refusal caught there would start MORE work after the deadline (every piece would raise again, the halving would recurse to one character).
  Pinned by a test and a mutant (6, K4).
- Why not runmap's `InputTooLarge`: textnorm.py is a byte-copied module (manifest; the demos copy it alone with the `TEXTNORM_*` constants);
  importing runmap would make the copy fail at import and would add a cycle (runmap imports textnorm). The redactor converts (3.6).

### 3.4 Reading points (the clock is `time.thread_time()`, read by one helper)
```python
def _tick(deadline: float | None) -> None:
    """Fail closed (``DeadlinePassed``) when the caller's CPU deadline has passed; nothing when there is none."""
    if deadline is not None and time.thread_time() > deadline:
        raise DeadlinePassed("the scan passed its deadline")
```
Read (each a fixed point, the same for every text, so the NUMBER of readings is a function of the text alone):
1. ENTRY of `scan_holds` / `scan_views` / `scan_views_no_value`: before `_checked` and again after it (the weight of a distinct text is 0.5 s). The
   entry read is BEFORE the cache lookup, so an expired deadline raises on a cache hit too (mutant K2).
2. `_readings`: before each `_prefix` pass (per text variant, per iota variant): at most 4.
3. `_squeezed`: per view (at most 6) and before its `_views` call.
4. `_scan_keys`: before each `_scan_key` (at most 16), and `_converge`: before each pass (at most 3 per key).
5. `scan_holds`: after the bundle (one read), per view in the needle loop is NOT needed (C speed: 31 views x needles of a 262,144-character text
   is milliseconds); before the insertion loop, per script view of it, and every 4,096 `find` hits inside `_holds_with_one_insertion` (the worst
   text, copies of half a needle, makes one hit per needle length).
6. `scan_views_no_value` / `scan_views`: after `_all_views`.
The deadline is passed as an argument down the private chain (`_text_bundle(raw, deadline)`, `_readings(..., deadline=None)`, `_squeezed(...,
deadline=None)`, `_scan_keys(raw, deadline=None)`, `_scan_key(text, step, deadline=None)`, `_converge(text, step, deadline=None)`,
`_holds_with_one_insertion(view, needle, deadline=None)`), the redactor's style (explicit, no hidden state). Every private default is None, so the
callers that do not pass one (`fold_views`, `identity_keys`, `register_value`, the tests that call the private functions) are unchanged.
Alternative (D2): a `contextvars` scope set by the three entry points; fewer signatures, hidden state; not the default.

### 3.5 Cache, determinism, overrun
- `scan_cache()`: the bundle is built under the deadline of the call that builds it. A call that finds the bundle cached still reads the clock at
  entry (point 1) and in the needle and insertion loops (point 5). A bundle whose build raised is NOT stored (the store is after the build, so
  this is already so: a raise leaves the scope unchanged); pinned by a test (6, K5).
- Determinism: with `deadline=None` nothing reads a clock: identical results. With a deadline the call returns EXACTLY what it returns without
  one, or raises `DeadlinePassed`: no partial view list, no "no hit". Which of the two happens depends on the CPU speed of the machine (as for
  the redactor): stated.
- Overrun after the deadline: at most one pass (one `_prefix` or one `_converge` step over the whole text), measured 0.17 to 0.35 s on the
  worst text of section 2.2 under load, or 4,096 insertion hits.
- Clock-read cost: section 11.2 (measured on the prototype).

### 3.6 Callers
- guard/injection.py `RegexDetector`: `check` computes `deadline = time.thread_time() + defaults.INJECTION_BUDGET_S` when that constant is not None
  (D4: default 20.0 s; None keeps today's behaviour) and passes it to every `scan_views_no_value` of `_read`, `_fit` and `_holds` (through
  `_start_of_next`), and reads `_tick`-style once per piece in `_read`'s loop (a raw `time.thread_time()` read in injection.py raising
  `textnorm.DeadlinePassed`). A `DeadlinePassed` is not caught by `_read`/`_fit` (it is not a `TextTooLong`); `injection_check` flags the run
  `guard_unavailable` (fail closed). The `Detector` protocol (`check(text, source)`) is unchanged.
- guard/redact.py: the redactor calls `fold` / `fold_view` only (no `scan_holds`). Change: in `_fold_scan`'s view-building loop (redact.py:1352-1370),
  read `self._over_budget(started)` before each line that is not plain, once every 4,096 characters of such lines (the `_aligned_fold` rule), so a
  text of many non-ASCII lines is stopped while its views are built (today the first read is after ALL views of ALL lines). One `fold` of one
  262,144-character line stays uninterrupted (0.18 s measured on the distinct text; at most 4 views per line). No `DeadlinePassed` can reach the
  redactor (it passes no deadline into textnorm).
- The redactor's deadline reaching `scan_holds`: nothing to wire at HEAD (no caller). The rule for the consumer that lands (G3 known values, a
  blocklist, a has-secret check): it passes the redactor's deadline (`self._deadline`, or `self._scan_deadline` inside `_fold_scan`) as
  `deadline=` and converts `DeadlinePassed` into `InputTooLarge("InputTooLarge")` at the call (`except textnorm.DeadlinePassed: raise
  InputTooLarge("InputTooLarge") from None`), so the gate code stays `mask_budget_exceeded`. Written into the `scan_holds` docstring.
- app.py `require_pinned_unidata`: no text, no deadline.

## 4. Pins and counts that change (exact)
| pin | where | today | after G10 |
|---|---|---|---|
| sha256 of guard/textnorm.py | tests/fixtures/textnorm_manifest.json `files` | `e7a93738f10e7ea66e164c929d20c0405a0730d41852e0ff88856720ea6cdbee` | recomputed after the LAST edit (`sha256sum` of the LF file); `test_the_manifest_pins_the_files_a_demo_copies` (tests/test_textnorm.py:3246) fails until it is |
| the same hash in the CHANGELOG re-copy list | CHANGELOG.md:650 (and the test checks `sha in text` for every manifest hash) | same | new hash, in a NEW CHANGELOG item (the old line stays as the record of the fold; the test needs the new hash to occur somewhere) |
| mutant count | tests/textnorm_mutants.py docstring line 12 "240 mutants", `test_a_the_list_has_240_mutants_…` (meta:90-92, name AND `== 240` twice), `test_a_print_the_placement_table` (meta:200), `test_the_split_…` (meta:363 `== 240`) | 240 (228 behaviour, 12 wording) | 240 + k (k = the new mutants of section 6 that live in textnorm_mutants.py, 9 by default): 249; the test NAME of meta:90 changes (it spells the counts) and a new `len(names[240:]) == 9, "the 9 of G10"` assert is added; split recount by `split_counts()` (expected 249 behaviour+wording, wording 12 unchanged if every G10 mutant changes behaviour) |
| CHANGELOG mutant sentence | meta test i: `f"{len(mm.M)} mutants in\n  `tests/textnorm_mutants.py`"` must occur | "The list holds 240 mutants in\n  `tests/textnorm_mutants.py`" (CHANGELOG:637-638) | the new item says "249 mutants in\n  `tests/textnorm_mutants.py`" (line break exactly there) |
| public names | `__all__` of textnorm.py and any test that counts them | as is | + `DeadlinePassed` (builder: `grep -rn "__all__\|public names" tests/test_textnorm*.py` and update the count that pins it) |
| `TESTS` list of textnorm_mutants.py | tests/textnorm_mutants.py:44 | 9 files | + `tests/test_textnorm_deadline.py` (killer file first, before `D`) |
| scan_keyset docstring "there is no clock or deadline" | textnorm.py:1272 | as is | "with no deadline (the default) there is no clock" |
| defaults.py | new `INJECTION_BUDGET_S` (D4) | absent | 20.0 with its comment (not hashed; the demo copy list names the `TEXTNORM_*` constants only, so no re-copy item) |
| tests/test_textnorm_siblings.py / callers pins | the set of files that import textnorm | unchanged (no new importer) | unchanged |
The demos: the CHANGELOG re-copy rule ("every repository that keeps a byte copy re-copies the five files in one commit") applies; only textnorm.py
of the five changes.

## 5. Tests (new file tests/test_textnorm_deadline.py; the clock is patched on the MODULE attribute, `monkeypatch.setattr(tn, "time",
SimpleNamespace(thread_time=clock))`, as `_stepping_clock` does for redact.py)
- D-1 None is unchanged: on 40 corpus rows (tests/fixtures/textnorm_corpus.json a/b) and 3 long texts, `scan_holds(..., deadline=None)` and
  `deadline=time.thread_time()+600` equal the call without the argument; `scan_views_no_value` likewise (tuples equal).
- D-2 a spent deadline raises before any work: `deadline=time.thread_time()-1` raises `DeadlinePassed` for `scan_holds`, `scan_views`,
  `scan_views_no_value`, also for a text that HOLDS the value (never True, never False).
- D-3 the stepping clock (one second per reading): `scan_holds(text=T, value=V, deadline=k + 0.5)` raises at reading k+1 for every k from 1 to the
  number of readings minus 1 (the count of readings of a fixed text is recorded first with a far deadline): it raises INSIDE the loop, not only at
  entry. Each reading point of 3.4 is reached (a spy on `_tick` callers by `sys._getframe(1).f_code.co_name` records the set: `scan_holds`,
  `_readings`, `_squeezed`, `_scan_keys`, `_converge`, `_holds_with_one_insertion`).
- D-4 the cache path: inside `scan_cache()`, a first call with a far deadline builds the bundle; a second call with a spent deadline raises
  `DeadlinePassed` (no hit is answered from the cache).
- D-5 a raise during the build leaves no bundle: inside `scan_cache()`, a stepping clock trips the build; the scope then holds no bundle, and a
  next call with no deadline builds and answers as without one.
- D-6 the error class: `issubclass(DeadlinePassed, TextnormError) and not issubclass(DeadlinePassed, TextTooLong)`; and behaviour: with a spent
  deadline, `RegexDetector(0.5)._score` on a 300,000-character text raises `DeadlinePassed` after ONE `scan_views_no_value` call (counted by a
  spy; a TextTooLong subclass would read pieces).
- D-7 bad deadline values: `True`, `"1"`, `float("nan")` (NaN compares false: decision, refuse it), raise `NotText` before work.
- D-8 injection: `injection_check(RegexDetector(0.5), text, "t")` with `defaults.INJECTION_BUDGET_S` monkeypatched to `-1.0` is flagged
  `guard_unavailable` (fail closed); with None the verdict equals today's.
- D-9 the redactor's view loop (tests/test_redact_fold_budget.py, next to `test_mid_1_…`): a text of 3 non-ASCII lines of 5,000 characters with a
  `CountedClock(0.0, 1, 100.0)` raises `InputTooLarge` from the view-building loop before `_line_hits` runs (a spy on `_line_hits` is not called).
- D-10 perf (marked `perf`, not in the mutant lists): the ASCII 262,144 text, best of 3, with and without a far deadline: ratio under 1.10.

## 6. Mutants (tests/textnorm_mutants.py, test_file `tests/test_textnorm_deadline.py`; the redact.py one in tests/redact_mutants.py)
| id | name | change | killer | expect (assertion message fragment) |
|---|---|---|---|---|
| K1 | deadline: the clock is never read | `_tick` body `return` | D-2 | `DEADLINE-SPENT` |
| K2 | deadline: ignored on a cache hit | entry `_tick` moved after the bundle lookup returns (or removed from the cached branch) | D-4 | `DEADLINE-CACHE` |
| K3 | deadline: a spent deadline answers no hit | `raise DeadlinePassed` -> `return False` path in `scan_holds` (the entry read caught and `return False`) | D-2 | `DEADLINE-NOT-FALSE` |
| K4 | deadline: the error is a TextTooLong | `class DeadlinePassed(TextnormError)` -> `(TextTooLong)` | D-6 | `DEADLINE-NOT-SIZE` |
| K5 | deadline: not passed into the scan keys | `_scan_keys(raw, deadline)` -> `_scan_keys(raw)` in `_text_bundle` | D-3 | `DEADLINE-POINTS` |
| K6 | deadline: no read between passes | `_tick` removed from `_converge` | D-3 | `DEADLINE-POINTS` |
| K7 | deadline: no read in the insertion loop | `_tick` removed from `_holds_with_one_insertion` | D-3 | `DEADLINE-POINTS` |
| K8 | deadline: a bad value is no deadline | the type check removed | D-7 | `DEADLINE-TYPE` |
| K9 | injection: the detector passes no deadline | `deadline=deadline` dropped in `RegexDetector._read` | D-8 | `DEADLINE-INJECTION` |
| KR1 | (redact_mutants.py) the view loop reads no clock | the new `_over_budget` in `_fold_scan`'s view loop removed | D-9 | `VIEW-LOOP-BUDGET` |
Equivalent, no entry: the second entry read after `_checked` (only time, not a result, changes; covered by D-10's reading count only if pinned:
decision D5).

## 7. The false-hit rates (part b)
### 7.1 What is documented today, and why it is wrong
- defaults.py:234-242 (the INSERTION comment): "the extra matches the insertion adds stay near 1% or lower per 10,000 characters of text". It is
  a rate of the ONE-INSERTED-LETTER band only (the extra matches of the insertion, per script, measured on Bible text). It is read (G1 review M5,
  ESCALATIONS E11) as the rate of the scan; the whole scan (`scan_holds`, exact needles included) hits ordinary text far more often for short values:
  4-letter Latin names 5.2 percent of 10,000-character chunks. The sentence is true for what it measures and misleading by omission.
- SECURITY-README-final.md 2.6 L43: "Not measured on ordinary text. UNVERIFIED. OPEN." Now measured (Latin; non-Latin only on synthetic text).
  L44: "The fold's own time use has no deadline … Not measured." Now measured (E11); the deadline is this ticket.
- L43 also says "innocent text may be masked or withheld": at HEAD no redaction path calls `scan_holds` (2.3), so today the rate has NO
  consumer; it is the rate a consumer will see when it lands. The wording must say so.
### 7.2 Text to publish (dated; the unit is stated in every place)
For docs (SECURITY.md limits list, and the CHANGELOG item of G10), exactly:
> FALSE HITS OF THE FOLD SCAN (measured 2026-11-20, Python 3.13.18, Unicode 15.1.0; evidence handover/core-c/evidence/G1-false-hits-and-cost.md).
> Unit: the share of 10,000-character chunks of ordinary text holding NO protected value in which `scan_holds` reports the value anyway (a
> "hit" per scan of one chunk for one value). Latin text (repository prose and code, Python standard library docstrings, generated Markov
> text; 199,000 scans per class): names of 4 letters 5.2 percent, 5 letters 0.8 percent, 6 letters 0.25 percent, 8 letters or more 0 (none in
> 199,000); a common word of 5 to 10 letters used as a street or host name 4.10 percent; short ASCII identifiers of 4 to 5 characters 0.196
> percent; 6 digits 0.005 percent, 8 digits or more 0. The hits include a value found inside a longer word ("Mary" in "summary") and across spaces
> and punctuation ("ab12" in "ab 12"): the three kinds were not counted apart. Non-Latin values (Chinese, Russian, Arabic, Hindi) were measured
> only on SYNTHETIC text built from letter-frequency guesses (no real text of those languages was available): their real rates are UNKNOWN; on the
> synthetic text short values hit often (2 Han ideographs drawn by frequency 26 percent, Cyrillic 4 to 8 letters 14 percent). A hit is the safe
> side (more masking or a refusal, never a leak). Today no redaction path uses `scan_holds`; these are the rates its consumer will see.
For defaults.py (replace the clause "stay near 1% or lower per 10,000 characters of text" by):
> "…stay near 1% or lower per 10,000 characters of text. That figure is the share the ONE-INSERTED-LETTER match ADDS, per script, on Bible text;
> it is not the false-hit rate of the scan: the whole of scan_holds (exact needles included) hits a 10,000-character chunk of ordinary Latin
> text for 5.2% of 4-letter names, 0.8% of 5-letter, 0.25% of 6-letter, 0 at 8+ (measured 2026-11-20, evidence G1-false-hits-and-cost.md)."
For SECURITY L43: "Over-matching. MEASURED 2026-11-20 on Latin text (per 10,000-character chunk): 4-letter names 5.2%, 5 letters 0.8%, 6
letters 0.25%, 8+ 0; common words of 5-10 letters 4.10%; ASCII ids of 4-5 characters 0.196%; 6 digits 0.005%. Non-Latin: synthetic text only,
real rates unknown. No redaction path uses this scan yet (it applies when one does). STATED." L44: "The fold has no deadline (measured: one
scan up to 5.5 s CPU on a 236,879-character text; the injection read of 2,000,000 characters 3.6 to 9.6 s). G10 adds one."
For the G1 ticket: there is no `tickets/G1-*.md` design ticket on this branch (only G1-result-review-1.md; the fold ticket is the CHANGELOG
item "The fold (ticket G, part G1)"); the review table's M5 state becomes "MEASURED (E11, G10 7.2); consumer pending", M4 "DEADLINE: G10".

## 8. The NOT RUN items (part c)
| item | fits the box at low load? | size | owner / state |
|---|---|---|---|
| split of the Latin hits into whole-word / inside a word / across spaces | yes | the same 199 chunks x 1,000 values x 9 Latin classes, with cache: about the CPU of the original run 1 Latin part (minutes), one process | an evidence runner is doing it (not duplicated here) |
| 2,000 values without the cache | ASCII: about 756 s, ONE process: fits at load below 2 (13 min); 1 percent non-ASCII about 2,023 s (34 min): fits only in a quiet window; distinct about 10,000-11,400 s (3 h): does NOT fit | extrapolations of E11 | not run by the drafter (box load 5 to 7); and the row has no consumer: no code calls `scan_holds` per value without the cache. Default (D7): run ASCII only, at load < 2 |
| real non-Latin prose | NO: no Han, Cyrillic, Arabic or Devanagari text on the box (E11 search) and no network corpus allowed | — | needs the lead to allow a fetch (the CHANGELOG names the corpora used for the insertion minimums: christos-c/bible-corpus, UD Japanese GSD/PUD) |

## 9. Decisions for the lead (default first)
- D1 Where the clock is read. Default: inside textnorm.py (3.1; hash, manifest, CHANGELOG, 9 mutants change). Alternative: only in the callers'
  loops (injection `_read` per piece; no textnorm change, no re-copy): overrun = one whole scan (up to 5.5 s measured).
- D2 How it is passed. Default: an explicit `deadline` argument down the private chain (redactor style). Alternative: a contextvar scope.
- D3 Which functions take it. Default: `scan_holds`, `scan_views`, `scan_views_no_value` only.
- D4 The injection budget. Default: new `defaults.INJECTION_BUDGET_S = 20.0` CPU s (about 2x the 9.6 s measured for 2,000,000 characters with 1
  percent non-ASCII; a 2,000,000-character text of distinct non-ASCII characters is NOT measured and may be refused: a new false abstain).
  Alternative: None (no deadline until a caller sets one; E11 then stays half open), or `REDACT_BUDGET_S` (6.0: the 9.6 s text would be refused).
- D5 The second entry read after the weight: keep (default; 0.5 s of weight on the distinct text) without a mutant.
- D6 The error name: `DeadlinePassed` (default) or a code-style message like the redactor's (`"FoldDeadline"`).
- D7 NOT RUN rows: run 2,000 values without the cache for ASCII only, at load < 2; leave 1 percent and distinct as extrapolations.
- D8 The redactor view loop read (3.6, KR1): in this ticket (default) or with the G4/G8 redact.py work.

## 10. Stated limits after G10
- The CPU clock only (as the redactor): a thread waiting for the GIL, a lock or I/O does not advance it; the wall-clock guard stays the caller's,
  and none of the four injection callers has one today (for core-b).
- Overrun: one pass over the whole text (0.17 to 0.35 s measured) or 4,096 insertion hits; one `fold` of one line in the redactor (0.18 s).
- Outcome depends on machine speed: a slow machine refuses a text a fast one scans (fail closed: the injection run is flagged, a DENY caller refuses).
- A hostile author can force a refusal (`DeadlinePassed`, `guard_unavailable`): a legitimate document in the same text is lost.
- `register_value`, `fold`, `identity_keys` and the other single-pass functions have no deadline (short inputs or bounded by the redactor's loop).

## 11. Measured by the drafter
### 11.1 Cost of the parts (HEAD archive, one run each, best of 1, CPU s, load 6.6)
| text | weight | fold | one `_prefix` | readings | squeezed | scan keys | `scan_views_no_value` | `scan_holds` |
|---|---|---|---|---|---|---|---|---|
| 262,144 ASCII | 0.000 | 0.044 | 0.043 | 0.137 | 0.133 | 0.190 | 0.463 | 0.454 |
| 260,400 chars, 1 percent non-ASCII | 0.010 | 0.096 | 0.082 | 0.336 | 0.336 | 0.556 | 1.310 | 1.135 |
| 236,879 distinct non-ASCII | 0.503 | 0.176 | 0.168 | 0.755 | 0.823 | 3.927 | 5.510 | 5.531 |
### 11.2 Prototype (overhead, raise inside the loop): PENDING

## 12. NOT verified
- The prototype numbers of 11.2 (pending at v1). No test file was written or run; no mutant was run.
- That no test counts textnorm's public names (the builder greps).
- The injection read of a 2,000,000-character distinct non-ASCII text (D4).
- Python 3.12.
