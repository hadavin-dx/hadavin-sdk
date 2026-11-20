# G10 v3: a deadline for the text fold, the published false-hit rates, and the NOT RUN cost items (lead ORDER 023, escalation E11)

Status: DRAFT v3 for plan review round 2, core-c drafter (opus), 2026-11-20. Nothing is built in the repo. Path class: guard (textnorm, injection).
v3 replaces v2 (`G10-textfold-deadline.md`, kept as the record) and answers `G10-review-1.md` (readiness: B1-B5, M1-M10, N1-N10; codebase: the
Blocker, M1-M6, nits, citations); section 15 lists every finding TAKEN or CONTESTED. A builder with no other context builds from THIS file.
Sections: 0 base, 1 goal, 2 what exists, 3 design, 4 pins and counts, 5 tests, 6 mutants, 7 PHASES (build order, commands, red and green ids),
8 false hits (part b), 9 NOT RUN items (part c), 10 decisions, 11 stated limits, 12 measured, 13 NOT verified, 14 what was run, 15 findings.

RULE FOR THE BUILDER: build the DEFAULT of every decision D1-D9 (section 10). An alternative is out of scope unless the lead says so.

## 0. Base, and what was read
- Base: cloud/core-c HEAD 78a0c8bcf (board 10:08:09Z). Code and tests are those of 746cab51f (no file under src, tests, tools, CHANGELOG.md or
  the two SECURITY-README files changed between 746cab51f and 78a0c8bcf; `git diff --stat` empty). Every line number below is of that HEAD unless
  it says "proto" (the prototype, section 14). `guard/textnorm.py` at HEAD: sha256 `e7a93738f10e7ea66e164c929d20c0405a0730d41852e0ff88856720ea6cdbee`
  (equals the manifest, tests/fixtures/textnorm_manifest.json:4).
- Changed since v2's base (374e6f3ff) in the files G10 touches: tests/textnorm_mutants.py gained `Q9 = "tests/test_textnorm_q9.py"` (line 36), a
  `param` argument of `mutant()` (line 47), `TESTS = [T, G, SC, SB, FB, O, RO, R2, Q9, D]` (line 40), and four mutants now killed in the Q9 file
  (among them three of the nine that G10 re-points, section 6.2); tests/test_textnorm_meta.py:161-165 accepts a parametrized pin and :179 the killer
  set holds `mm.Q9`; CHANGELOG.md gained one line before the fold item (the hash line is :651, the mutant sentence :638-639); guard/redact.py
  moved (E9): `_over_budget` :1293, `_fold_scan` :1334, its first read `self._over_budget(started)` :1369. textnorm.py, injection.py and defaults.py
  are unchanged since v2's base.
- Read for v3 (in addition to v2's list): the two reviews; guard/textnorm.py 110-400, 536-860, 970-1070, 1198-1640; guard/injection.py whole;
  defaults.py 228-272; tests/textnorm_mutants.py 1-60 and the nine re-pointed mutants and 860-940 (`split_counts`, `__main__`);
  tests/test_textnorm_meta.py 86-376; tools/mutation_runner.py 1-120 and `_run_mutants` (436-586); hadavin_sdk/testing/mutation.py `judge`,
  `first_failure_junit`; tests/test_textnorm_fixbatch.py 240-330, 655-680; tests/test_textnorm_callers.py 36-50, 214-230;
  tests/test_textnorm_order137.py 300-345, 478-515; tests/test_textnorm.py 1198-1243, 3155-3175, 3240-3275; tests/test_textnorm_round2.py 1-40,
  205-235, 340-365; tests/test_textnorm_q9.py 1-40; CHANGELOG.md 625-655; SECURITY-README-final.md 140-146, 255-259; SECURITY-README-v5.md
  (grep: K50, K51, the tables); evidence/G1-false-hits-and-cost.md whole, including "Round 2 (2026-11-20, low load)" (committed e70aecaa9);
  guard/judge.py 95-110; the six `injection_check` call sites; runmap.py 190-225 (the size cap of the redactor).

## 1. Goal
(a) The DENY scan of the fold (`scan_holds`) and the injection read (`scan_views_no_value` through `RegexDetector`) stop at a caller's CPU
deadline (`time.thread_time()` of the calling thread), in the redactor's style: read at fixed points between whole passes, refusal on expiry
(fail closed: never a "no hit", never a part of the views); the caller keeps its wall-clock guard. With no deadline (the default, None) every
result is what it is today and no clock is read.
(b) The measured false-hit rates are published with date, unit, versions and caveats (an UPPER BOUND; the Latin split of Round 2), and the
sentences that say "about 1 percent" or "not measured" are corrected.
(c) The NOT RUN items of the cost evidence that fit the box are named, sized and given a default.
OUTCOME the builder delivers: the source, test, mutant and pin edits of sections 3-7, the defaults.py comment and the CHANGELOG item (section 8.2,
8.3). The SECURITY wording (SECURITY-README-final.md and -v5.md lines of section 8.4) is applied by the SECURITY wording lane (D9); the lane's
reviewer verifies it against section 8.4; the G10 result review checks only that the builder did NOT edit those files.

## 2. What exists today (HEAD)
### 2.1 No clock in the fold
- grep of guard/textnorm.py and guard/injection.py for `time`, `thread_time`, `monotonic`, `perf_counter`, `deadline`, `timeout`: only the
  docstring of `scan_keyset` (textnorm.py:1272, "there is no clock or deadline"). Neither file imports `time`.
- Cost (evidence G1 B; its CPU seconds are `time.process_time()`, the drafter's are `time.thread_time()`, one process, so the same here): one
  `scan_holds` on 262,144 ASCII characters 0.36 s; 1 percent non-ASCII (about 260,800, the longest prefix the weight cap takes) about 0.9 s;
  236,879 distinct non-ASCII characters 4.8 to 5.5 s. `RegexDetector` on 2,000,000 characters 3.6 s (ASCII), 9.6 s (1 percent non-ASCII).
- The weight cap (`TEXTNORM_MAX_CHARS` = 262,144, `_checked`, `TextTooLong`) bounds the SIZE of one call, not its time. A text longer than
  262,144 characters is refused from its length alone before any per-character work (textnorm.py:566).

### 2.2 Where the time of one scan goes (v2 11.1, unchanged code)
`scan_holds` = `_checked` (the weight; memoised per long text; 0.55 s on the distinct text when first seen) + the value's needles
(`_needles_or_refuse`) + `_text_bundle` = `_readings` (2 texts x 2 `_prefix` passes + 3 `_finish`) + `_squeezed` (the readings again inside
`_views`, then per view upper / translate / regex) + `_scan_keys` (2 marks variants x up to 4 tag texts x 2 steps, each `_converge`d over at
most `TEXTNORM_MAX_PASSES` = 3 passes) + the needle loop (`needle in view`, C speed) + the insertion loop (`_holds_with_one_insertion`). On the
distinct text: readings 0.65 s, squeezed 0.71, scan keys 4.24, one `_prefix` pass 0.18, one `fold` 0.18.
SOUNDNESS OF THE READING POINTS: NFKD (`unicodedata.normalize("NFKD", text)`, textnorm.py:742) and NFKC (in `_prefix`, :695) are single C calls
over the whole text; a reading is placed only BETWEEN such whole passes, so no normalisation unit is ever split and no chunk boundary exists
(the fold is not cut into character chunks: a combining mark belongs to the letter before it and NFKC joins, so a boundary inside a sequence
would change the result).

### 2.3 Who calls what (grep of the whole of src)
| function | callers in src | today's time bound | what a TextnormError does there |
|---|---|---|---|
| `scan_holds`, `scan_views`, `scan_cache`, `register_value`, `scan_needles` | NONE (tests and evidence scripts only) | none | the docstring rule: a DENY caller REFUSES |
| `scan_views_no_value` | guard/injection.py `_holds` (:72, via `_start_of_next`), `RegexDetector._read` (:127), `RegexDetector._fit` (:144) | none (`TEXTNORM_INJECTION_MAX_CHARS` = 2,097,152 is a size) | `_read` (:129) and `_fit` (:145, :155) CATCH `TextTooLong` only; anything else reaches `injection_check` (:217-233), which flags the run `guard_unavailable` |
| `fold`, `fold_view` | guard/redact.py `_fold_scan` and the per-match helpers | the redactor's deadline; first read after the view building, redact.py:1369 | `redact_text` turns any non-RedactionError into `RedactionError(type name)` |
| `require_pinned_unidata` | app.py:132 | constant | `UnidataMismatch`: refuse to start |
| `without_spacing_marks` | guard/runmap.py | linear, under the redactor's deadline | as above |
`injection_check` has SIX call sites: runtime/agent_loop.py:323 (`_screen`), k1b/loop.py:205, approvals/requests.py:37, approvals/cards.py:79,
guard/judge.py:107 (`qualify`, the golden set of a judge detector: a `guard_unavailable` verdict counts as a failed case) and
guard/injection.py:202 (`AnyOf.check`, one call per detector of a list). All six go through `injection_check`, so a `DeadlinePassed` is a flag
at every one (fail closed); none wraps the call in a wall-clock timeout or a thread.

### 2.4 The redactor's deadline (the style copied)
- A deadline is a `time.thread_time()` value (CPU seconds of the CALLING thread: load from other threads does not change the outcome; a thread
  that waits for the GIL or a lock does not advance it; a value taken in one thread means nothing in another). `redact_text` sets ONE deadline
  `started + REDACT_BUDGET_S` (6.0) and passes it as `redact(_deadline=)`.
- `_Redactor._over_budget(deadline)` (redact.py:1293): `if time.thread_time() > deadline: raise InputTooLarge("InputTooLarge")`; read at fixed
  points inside loops, never inside one C call. Tests pin the readings with a stepping clock patched on the MODULE attribute
  (tests/test_redact_settle_loop.py `_stepping_clock`) and `CountedClock` (tests/test_redact_fold_budget.py).
- A refusal is fail closed: nothing is shown; a legitimate document in the same text is lost for that run.

## 3. Design (part a)
### 3.1 The deadline is read INSIDE textnorm.py (D1)
The callers' loops cannot bound the cost: the injection read of a text under the cap is ONE call of `scan_views_no_value` (5.8 s measured on the
distinct text, no point to stop at), and a `scan_holds` consumer makes one call per value. Inside textnorm the overrun is the longest stretch
between two readings (measured, section 12.2). So textnorm.py changes, and with it the hash, the manifest, the CHANGELOG re-copy list, the public
names and the mutant list (section 4).

### 3.2 API (keyword-only; default None = unchanged)
- `scan_holds(*, text: str, value: str, deadline: float | None = None) -> bool` and
  `scan_views_no_value(raw: str, *, deadline: float | None = None) -> tuple[str, ...]`.
- `deadline`: None, or an `int` or `float` (`type(deadline) in (int, float)`, so not a `bool`) that is not NaN (`math.isnan`; NaN compares False
  and would be "no deadline"). Anything else raises `NotText("deadline must be a time.thread_time() value or None")` BEFORE any clock reading
  and any work. A value of `time.thread_time()` taken in ANOTHER thread is accepted but means nothing (per-thread clock): said in the docstring.
- NOT given a deadline (D3): `scan_views` (parameters pinned: tests/test_textnorm_fixbatch.py:280 `list(sig.parameters) == ["raw", "value"]`;
  no caller), `fold`, `fold_view`, `fold_views`, `squeeze`, `squeeze_views`, `identity_key(s)`, `could_be_same_person`, `allow_equal`,
  `names_equal`, `register_value`, `scan_keyset` (parameters pinned, tests/test_textnorm_scan.py:91), `scan_needles`, `has_hidden_channel`,
  `has_mixed_script`.

### 3.3 The error: `DeadlinePassed(TextnormError)` (D6), defined in guard/textnorm.py directly BEFORE `class EmptyView` (HEAD :381)
```python
class DeadlinePassed(TextnormError):
    """The scan passed the caller's deadline (a ``time.thread_time()`` value of the calling thread); nothing was decided. A DENY caller REFUSES,
    as for any ``TextnormError``; the injection check flags the run. It is not a ``TextTooLong``: a reader that halves a text that is too long must
    not start more work after the deadline. The message holds no text, no value and no length."""
```
- Message `"the scan passed its deadline"`. In `__all__` (HEAD :309-346, sorted) directly after `"CoverageRefused",` (:315) and before
  `"EmptyView",`.
- NOT a `TextTooLong`: `_read` and `_fit` catch `TextTooLong` and then read the text in pieces or halve a piece. Measured on mutant 243 (the class
  made a `TextTooLong`): a spent deadline on 300,000 characters reaches `scan_views_no_value` several times instead of once (test D-6 kills it).
- Not runmap's `InputTooLarge`: textnorm.py is byte-copied with the `TEXTNORM_*` constants only (CHANGELOG re-copy rule); an import of runmap
  would break the copy and add a cycle (runmap imports textnorm). A future redaction consumer converts (3.6).
- The refusal lint (tests/test_textnorm_callers.py:40-48) builds `BANNED` from `__all__`, so `DeadlinePassed` is banned in handlers at once and
  the pinned set at :218-227 gets `"DeadlinePassed"` (section 4). Nothing in src handles it today, so `REFUSAL_HANDLERS` is unchanged.

### 3.4 Reading points (exact placement)
Two helpers, placed in textnorm.py directly AFTER `_checked` (HEAD :560-575; "the input rules in one place") and before the comment
`# COMBINING GREEK YPOGEGRAMMENI` (:578); the clock is read through the module attribute `time` (`import time` after `import threading`, :297;
`import math` after `import logging`, :294), so a test replaces `textnorm.time`:
```python
def _deadline_checked(deadline: float | None) -> float | None:
    """The ``deadline`` rule of ``scan_holds`` and ``scan_views_no_value``: None, or an ``int`` or ``float`` that is not a ``bool`` and not NaN (NaN
    compares False, so it would be no deadline at all)."""
    if deadline is None:
        return None
    if type(deadline) not in (int, float) or math.isnan(deadline):
        raise NotText("deadline must be a time.thread_time() value or None")
    return deadline


def _tick(deadline: float | None) -> None:
    """One reading of the calling thread's CPU clock (``time.thread_time()``, through the module attribute so a test can replace it):
    ``DeadlinePassed`` once the deadline has passed (fail closed); nothing at all without a deadline."""
    if deadline is not None and time.thread_time() > deadline:
        raise DeadlinePassed("the scan passed its deadline")
```
(`deadline != deadline` is refused by ruff PLR0124 in this repo; `math.isnan` is the form that passes `ruff check`.)

| point | function | exact place | conditional? | readings |
|---|---|---|---|---|
| P1 entry | `scan_holds`, `scan_views_no_value` | first statement after `deadline = _deadline_checked(deadline)`, BEFORE `_checked` and so before the cache lookup | no | 1 |
| P2 after the size rule | same | right after `_checked(...)` | no | 1 |
| P2b after the value's needles | `scan_holds` | right after `needles = _needles_or_refuse(value, scripts)` | no | 1 |
| P3 prefix passes | `_readings` | inside `for marks, text in enumerate(texts):` after the `marks_only` skip: (a) before `nfkd = unicodedata.normalize("NFKD", text)`; (b) after `with_iota = _prefix(...)`, before `prefixes = {` | NO: (b) is read whether or not the second `_prefix` runs (`if _YPOGEGRAMMENI in nfkd`), so the count is 2 per text, fixed | 2 per text (texts = 1 or 2) per `_readings` call; `scan_holds` calls `_readings` twice per bundle (the bundle, and inside `_squeezed` -> `_views` -> `_view_pairs`) |
| P4 per squeeze view | `_squeezed` | first statement of the body of `for view in _views(..., deadline=deadline):`. `_views` returns a finished tuple, so its own work (the `_readings` inside) is read by P3; P4 bounds the per-view `upper` / `translate` / `_NON_ALNUM.sub` | no | one per distinct view (at most 6) |
| P5 per converge pass | `_converge` | first statement of the body of `for _ in range(passes):` | no | at most 3 per scan key, at most 16 keys |
| P6 after the views | `scan_holds`: right after `bundle = _text_bundle(text, deadline)`; `scan_views_no_value`: right after `bundle = _text_bundle(raw, deadline)` | no | 1 |
| P7a insertion | `scan_holds`: after `if not inserts: return False`, before `script_views = {...}` | only when the value has a script needle in the insertion band | 1 |
| P7b per script view | `scan_holds`: first statement of `for view in script_views:` | same | one per script view |
| P7c insertion hits | `_holds_with_one_insertion`: in BOTH `while start != -1:` loops, `hits += 1` then `if not hits % 4096: _tick(deadline)` (one counter for both halves) | every 4,096 hits | hits // 4,096 |
The needle loop (`needle in view` over at most 31 views) gets no reading: C speed. Unread stretches by design: `_checked` (the weight, between
P1 and P2), the value's needles (between P2 and P2b), `_without_spacing_marks` and the `_tag_texts` / `no_lm` / `no_marks` comprehensions of
`_scan_keys` and the final `"".join` of `_scan_key` (each between two P5 or P3 readings), `_all_views` / `_pairs_from` and the script views
(between P6 and P7a). Their size is in the measured longest stretch (12.2).
The number of readings is a function of the text and the value only (fixed points): measured 19 for T and 18 for T2 of D-3, 16 for
`scan_views_no_value(T)` (section 5).

The deadline is passed as an explicit argument (keyword `deadline=None` in every signature, D2) down this private chain:
`_readings(raw, *, casefold, collapse_ws, marks_dropped=False, marks_only=False, deadline=None)`,
`_view_pairs(..., scripts=frozenset(), deadline=None)` (passes `deadline=deadline` to `_readings`),
`_views(..., scripts=frozenset(), deadline=None)` (passes `deadline=deadline` to `_view_pairs`),
`_squeezed(raw, *, loose=False, deadline=None)`, `_converge(text, step, deadline=None)`, `_scan_key(text, step, deadline=None)`,
`_scan_keys(raw, deadline=None)` (calls `_scan_key(text, step, deadline)` positionally), `_text_bundle(raw, deadline=None)`,
`_holds_with_one_insertion(view, needle, deadline=None)`. `_all_views` is NOT given a deadline (codebase M5): both entry points build the bundle
themselves with `_text_bundle(..., deadline)` and pass it in; `_all_views(text, scripts, bundle)` (HEAD :1522, the old string of three
mutants) stays byte for byte. `fold_views`, `identity_keys`, `register_value`, `scan_views`, `scan_needles` call the chain without the
argument and are unchanged. Tests that replace a private function: `_counting_readings` (order137:349) and the fixbatch spy (:256) take
`*args, **kwargs` (fine); test_textnorm_scan.py:287 calls `_converge(ch, _pass_b)` (fine, default None); the `_one_off` spies (fixbatch:611,
round1:491) are untouched (`_one_off` gets no deadline); the `work(*args, **kwargs)` stub at test_textnorm.py:2930-2934 is fine; the
`_scan_key` stub `key(tag_text, step)` at order137:494 is NOT fine: it is widened (section 4, B3).

### 3.5 Cache, determinism, overrun, cost
- `scan_cache()`: the bundle is built under the deadline of the call that builds it and stored only after a complete build (the store follows
  the build at HEAD :1371-1378, so a raise stores nothing; D-5). A call that finds the bundle cached reads P1, P2, P2b and P6 (and P7 when the
  value has insertion needles): six readings for T and V, all in `scan_holds` (D-4). A spent deadline raises on a cache hit.
- Determinism: with `deadline=None` no clock is read; results identical (D-1 over 188 corpus rows x 3, measured). With a deadline the call
  returns EXACTLY what it returns without one, or raises `DeadlinePassed`; WHICH depends on the machine's speed (as for the redactor): stated.
- Overrun: the longest stretch between two readings, MEASURED (12.2): <PENDING>. The value work (P2 to P2b) is outside the per-pass bound:
  measured <PENDING> for a value at the weight cap; a protected value comes from the operator's registration, not from the text, so a slow value
  is the operator's input (stated limit 11).
- Injection: a text over 262,144 characters is refused by `_checked` from its LENGTH before any per-character work, so the injection read never
  folds more than one piece (`TEXTNORM_INJECTION_CHUNK_CHARS` = 32,768) or one window (at most `TEXTNORM_INJECTION_OVERLAP_MAX_CHARS` = 8,192)
  per `scan_views_no_value` call. Between two calls `_score` runs `_RX.search` and `_SQUASH.sub` over the piece and its views (at most 28 + 1
  strings of at most about 32,768 characters each); the next piece's P1 follows. After the last piece the raw squash over the whole text
  (`_SQUASH.sub("", text.lower())`, injection.py:177) runs with no reading. Decision (codebase M1): NO reading in `_score` (D10 below); the
  regex work of a piece sits between two readings and is inside the measured longest stretch; the tail after the last reading ends the call
  (a reading there could only turn a finished answer into a refusal). Measured: <PENDING>.
- Cost of the readings: one `time.thread_time()` read 0.28 to 0.31 us (v2 12); no measurable change on 262,144 ASCII characters (v2: ratio of
  bests 0.999 for `scan_holds`, 0.994 for `scan_views_no_value`). Not re-measured on the v3 prototype (it adds P2b and moves P7 inside the
  loop; three readings more per call).

### 3.6 Callers
guard/injection.py (exact post-edit lines; proto line numbers):
- `import time` after `import re` (proto :10).
- New function after `_check_geometry` (HEAD :41-61), before `_holds`:
```python
def _deadline() -> float | None:
    """The CPU deadline of one ``RegexDetector.check``: ``defaults.INJECTION_BUDGET_S`` seconds of the calling thread's CPU clock from now
    (``time.thread_time()``), or None (no deadline) when the budget is None. A budget that is not a positive finite number (a ``bool``, a string,
    zero, a negative number, NaN, infinity) raises ``ValueError``, which ``injection_check`` turns into a flag, as for a bad setting of the chunked
    read (``_check_geometry``)."""
    budget = defaults.INJECTION_BUDGET_S
    if budget is None:
        return None
    if type(budget) not in (int, float) or not 0 < budget < float("inf"):
        raise ValueError(
            "defaults.INJECTION_BUDGET_S must be a positive number of CPU seconds or None"
        )
    return time.thread_time() + budget
```
- The chain, every new parameter `deadline: float | None = None` (positional-or-keyword; the two `@staticmethod` generators stay static):
  `def _holds(window: str, need_kept: int, need_letters: int, deadline: float | None = None) -> bool:` with
  `    views = textnorm.scan_views_no_value("|" + window + "|", deadline=deadline)`;
  `def _start_of_next(text: str, start: int, end: int, deadline: float | None = None) -> int:` with
  `        if back >= low and _holds(text[end - back : end], need_kept, need_letters, deadline):`;
  `    def _read(text: str, deadline: float | None = None) -> Iterator[tuple[str, tuple[str, ...]]]:` with
  `            yield text, textnorm.scan_views_no_value(text, deadline=deadline)`,
  `            yield from RegexDetector._fit(text[start:end], deadline)`, `            start = _start_of_next(text, start, end, deadline)`;
  `    def _fit(piece: str, deadline: float | None = None) -> Iterator[tuple[str, tuple[str, ...]]]:` with
  `            yield piece, textnorm.scan_views_no_value(piece, deadline=deadline)`,
  `                    second = _start_of_next(piece, 0, cut, deadline)`,
  `            yield from RegexDetector._fit(piece[:cut], deadline)`, `            yield from RegexDetector._fit(piece[second:], deadline)`;
  `    def _score(self, text: str, deadline: float | None = None) -> float:` with `        for piece, views in self._read(text, deadline):`
  and two docstring lines appended: "``deadline`` (None: none) goes to every ``textnorm.scan_views_no_value`` call; past it ``textnorm`` raises
  its ``DeadlinePassed``, which no reader here catches, so ``injection_check`` flags the run (``guard_unavailable``)."
  `RegexDetector.check`: `        score = self._score(text, _deadline())`.
  Tests that call `_score` / `_read` / `_fit` directly keep working (the new argument has a default); the `Detector` protocol
  (`check(text, source)`) is unchanged; other detectors are untouched.
- injection.py never names `textnorm.DeadlinePassed` (so the allow-list of order137:332-341, `seen <= allowed`, stays as is); a future
  consumer that converts it must add `"DeadlinePassed"` to that allow-list and its handler to `REFUSAL_HANDLERS`.
- guard/redact.py: NOTHING (D8). The redactor calls `fold` and `fold_view` only, under its own reads; its unread stretch is the view building of
  `_fold_scan` before redact.py:1369. The redactor's input is capped before that: `runmap.redact_text` refuses a text over
  `defaults.MAX_REDACT_CHARS` (= `TEXTNORM_MAX_CHARS`, runmap.py:197 length, :222 expanded length), so the estimate "about 4 folds of one
  capped text, about 4 x 0.18 s" (ESTIMATE, v2) is for capped texts only.
- The consumer rule (in the `scan_holds` docstring): pass the call's deadline and convert at the call
  (`except textnorm.DeadlinePassed: raise InputTooLarge("InputTooLarge") from None`), with that function in `REFUSAL_HANDLERS`.
- app.py `require_pinned_unidata`: no text, no deadline.

### 3.7 The source change of textnorm.py (exact; prototyped, `ruff format` and `ruff check` clean)
1. `import math` after `import logging`; `import time` after `import threading`.
2. `"DeadlinePassed",` in `__all__` after `"CoverageRefused",`; the class of 3.3 before `class EmptyView`; `_deadline_checked` and `_tick` (3.4)
   after `_checked`.
3. Module docstring, HEAD :126-127 become:
   `THE PUBLIC NAMES (37, pinned by ``tests/test_textnorm.py``; ``__all__`` is sorted). Errors: ``TextnormError`` (base, not a ``ValueError``),`
   `` ``TextTooLong``, ``NotText``, ``UnidataMismatch``, ``FoldNotConverged``, ``EmptyView``, ``ViewTooShort``, ``CoverageRefused``, ``DeadlinePassed``. Check names (DENY and ALLOW):``
   and after HEAD :249 (the last line of "ONE INSERTED LETTER", before the blank line and "WHERE ``could_be_same_person`` IS USED") these eleven
   lines (two leading spaces each, as the paragraph above; no `"3.13"` or `"15.1.0"` literal, test_textnorm.py:3169):
```
  DEADLINE (G10, ORDER 023): ``scan_holds`` and ``scan_views_no_value`` take a keyword ``deadline``: None (the default: no clock is read and
  every result is what it was before) or a value of ``time.thread_time()`` of the CALLING thread (CPU seconds of that thread; a value from another
  thread means nothing here). Anything else (a ``bool``, a string, NaN) raises ``NotText`` before any work. The clock is read at fixed points
  BETWEEN whole passes, never inside one (NFKD and NFKC are single calls over the whole text, so a pass is never cut): at the entry (before the
  size rule and before the cache), after the size rule, after the value's needles, before each of the two prefix passes of each text of
  ``_readings``, per squeeze view, before each pass of each scan key, after the views of the text, before the insertion match and per script
  view of it, and every 4,096 hits of the insertion match. A reading after the deadline raises ``DeadlinePassed`` (fail closed: never a False,
  never a part of the views); a bundle is stored in ``scan_cache()`` only after a whole build, and a call that finds it cached still reads the
  clock. With a deadline a call returns exactly what it returns without one, or raises; which of the two depends on the speed of the machine.
  The overrun is the longest stretch between two readings (the size rule of a long text of distinct letters is the longest one); the work on the
  VALUE (its needles and scan keys) has no reading inside it, only before and after. No other function takes a deadline.
```
4. `scan_keyset` docstring HEAD :1272: `...; over-matching is the safe side; there is no clock or deadline;` becomes
   `...; over-matching is the safe side; it reads no clock (the deadline is` + new line `    ``scan_holds``'s and ``scan_views_no_value``'s);`.
5. The parameters and readings of 3.4. `_text_bundle` (HEAD :1366-1370) becomes:
```python
    bundle: _Bundle = (
        tuple(
            _readings(raw, casefold=True, collapse_ws=True, marks_dropped=True, deadline=deadline)
        ),
        _squeezed(raw, deadline=deadline),
        tuple(sorted(_scan_keys(raw, deadline))),
    )
```
   `_squeezed` (HEAD :1054-1058) becomes:
```python
def _squeezed(raw: str, *, loose: bool = False, deadline: float | None = None) -> tuple[str, ...]:
    """``squeeze_views`` on a text that was already checked."""
    out: list[str] = []
    for view in _views(
        raw, casefold=True, collapse_ws=False, marks_dropped=True, deadline=deadline
    ):
        _tick(deadline)
        s = view.upper()
```
   `scan_views_no_value` (HEAD :1410-1415) becomes (docstring first line unchanged, last line gains one sentence):
```python
def scan_views_no_value(raw: str, *, deadline: float | None = None) -> tuple[str, ...]:
    """...
    scan that reads no script. ``deadline``: see "DEADLINE" in the module docstring (None: no clock is read)."""
    deadline = _deadline_checked(deadline)
    _tick(deadline)
    _checked(raw)
    _tick(deadline)
    bundle = _text_bundle(raw, deadline)
    _tick(deadline)
    return tuple(view for view in _all_views(raw, frozenset(), bundle) if view)
```
   `_holds_with_one_insertion` (HEAD :1453-1464): `    hits = 0  # both halves count; the clock is read every 4,096 hits` before
   `    start = view.find(first)`, and as the first three lines of each `while start != -1:` body:
   `        hits += 1` / `        if not hits % 4096:` / `            _tick(deadline)`.
   `scan_holds` (HEAD :1506-1536): signature `def scan_holds(*, text: str, value: str, deadline: float | None = None) -> bool:`; the docstring's
   last line `hundreds of values at the cost of one text pass, call this inside ``with scan_cache():``."""` gains the four lines of the deadline and
   the consumer rule (proto :1577-1580, quoted in 3.6); the body from `_checked` to the end:
```python
    deadline = _deadline_checked(deadline)
    _tick(deadline)
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
6. Prototype sha256 of the edited file (LF): `06a3f882986154580b9a90f9f25d41d2207b162a0d02ff74f34f7bc6d2c7c6e3`. The builder's hash will differ if any
   byte differs; the manifest and the CHANGELOG take the builder's own `sha256sum` after the LAST edit of the file.

### 3.8 defaults.py
After `TEXTNORM_INJECTION_MAX_CHARS = MAX_BUNDLE_CHARS` (HEAD :272), exactly:
```python
# INJECTION_BUDGET_S (guard.injection, G10): the CPU seconds of the calling thread (time.thread_time()) one RegexDetector check may spend in the
# text fold; past it textnorm raises DeadlinePassed and the run is flagged guard_unavailable (fail closed). None: no deadline. A positive number;
# anything else flags every run. 30.0: about 2x the slowest text of up to 2,097,152 characters measured on the build box (G10 ticket, D4); a
# machine more than about 2x slower refuses that text. A CPU clock: waiting for the GIL, a lock or I/O does not count; the wall clock is the caller's.
INJECTION_BUDGET_S = 30.0
```
(The value follows D4 and section 12.3; if the lead picks another value, only the number and "about 2x" change.) The false-hit comment is 8.2.

## 4. Pins and counts that change (exact; every row VERIFIED by running the edited tests on the prototype, section 14)
| pin | where (HEAD) | today | after G10 |
|---|---|---|---|
| sha256 of guard/textnorm.py | tests/fixtures/textnorm_manifest.json:4 | `e7a937...cdbee` | the builder's `sha256sum` after the last edit (prototype `06a3f882...c7c6e3`); `test_the_manifest_pins_the_files_a_demo_copies` (tests/test_textnorm.py:3246) is red from the first edit of textnorm.py to this edit |
| the hash in the CHANGELOG | CHANGELOG.md:651 (the fold item's re-copy list; the manifest test asserts `sha in text` for every manifest hash) | old hash | a NEW item at the end of CHANGELOG.md (after :655) lists the new hash (8.3); :651 stays as the record |
| the mutant sentence | CHANGELOG.md:638-639 ("The list holds 240 mutants in" / "  `tests/textnorm_mutants.py`"); meta test i (tests/test_textnorm_meta.py:259) wants `f"{len(mm.M)} mutants in\n  `tests/textnorm_mutants.py`"` | 240 | the new item holds "... The list holds 253 mutants in" at the END of a line and "  `tests/textnorm_mutants.py` ..." as the next line (8.3) |
| public names | tests/test_textnorm.py:1200 `def test_the_public_names_are_exactly_the_listed_thirty_six():`, the list (:1202-1239), `== 36` at :1241 | 36 | `def test_the_public_names_are_exactly_the_listed_thirty_seven():`; `            "DeadlinePassed",` after `            "CoverageRefused",` (:1208); `    assert len(textnorm.__all__) == len(set(textnorm.__all__)) == 37` |
| module docstring count | tests/test_textnorm_fixbatch.py:666 docstring, :668 `== 36` | 36 | `    """Item 8. The 37 names (34 of the fold, 3 for the fold scan of the redactor) are documented once, ...` and `    assert len(textnorm.__all__) == 37` |
| the call lint (B2, codebase Blocker 1) | tests/test_textnorm_fixbatch.py:323 `            assert nargs == 1 and not kws, (` in `test_no_caller_in_the_package_omits_the_value_or_the_scripts` (def :298) | red once injection.py passes `deadline=` | `            assert nargs == 1 and kws <= {"deadline"}, (` (message unchanged) |
| banned names (codebase Blocker 2) | tests/test_textnorm_callers.py:218-227 `test_refusal_handlers_has_five_entries_and_the_banned_names_follow_textnorm` | 8 names | `        "DeadlinePassed",` after `        "CoverageRefused",` (:226); `REFUSAL_HANDLERS` stays 5 |
| the `_scan_key` stub (B3, codebase Blocker 3) | tests/test_textnorm_order137.py:494 `    def key(tag_text, step):` in `_stub_keys` (:483-500), used by `test_exactly_the_cap_in_scan_keys_is_allowed_and_one_over_is_refused` (:503) | `TypeError` once `_scan_keys` passes the deadline | `    def key(tag_text, step, deadline=None):` (DECIDED: widen the stub; the source passes the deadline unconditionally) |
| allow-list of textnorm names in src | tests/test_textnorm_order137.py:332-341 | unchanged (src never writes `textnorm.DeadlinePassed`) | unchanged; the future consumer edits it |
| the ceiling perf row | tests/test_textnorm_round2.py:344 `def test_perf_the_chunked_read_at_its_ceiling_is_not_flagged_and_stays_within_the_bound(name):` | runs under the default budget | `def ...(\n    name, monkeypatch\n):` and before `    start = time.perf_counter()` (:355): `    monkeypatch.setattr(\n        defaults, "INJECTION_BUDGET_S", None\n    )  # the row times the read; the budget has its own tests (G10)` (ruff-formatted form) |
| mutant count and the meta test | tests/test_textnorm_meta.py:90 name, :92, :97, :123, :149, :179, :184-191, :204, :367 | 240 | section 4.1 |
| `TESTS` and the killer files | tests/textnorm_mutants.py:36-40 | `TESTS = [T, G, SC, SB, FB, O, RO, R2, Q9, D]` | `DL = "tests/test_textnorm_deadline.py"  # the killers of G10: the deadline of the fold scan and of the injection read` before `R2 = ...` (:37); `TESTS = [T, G, SC, SB, FB, O, RO, R2, Q9, DL, D]`; meta :173-175 (`TESTS[:3]`, `TESTS[-1] == D`, no perf/meta/notices) still hold |
| the mutant list's docstring | tests/textnorm_mutants.py:12 "240 mutants (the list of P1b, 216, the 10 of P1a fix8 and the 14 of the two P1b fix rounds, 9 of round 1 and 5 of round 2), in the order" | 240 | "253 mutants (the list of P1b, 216, the 10 of P1a fix8 and the 14 of the two P1b fix rounds, 9 of round 1 and 5 of round 2, and the 13 of G10, the deadline of the fold, last), in the order" |
| split | `split_counts()` | 228 behaviour, 12 wording | 241 behaviour, 12 wording (RUN on the prototype: `(241, 12)`; no G10 mutant is wording-only) |
| unchanged, checked by running | `scan_views` parameters (fixbatch:280), `scan_keyset` parameters (scan:91), the cache read counts (fixbatch:246-272, order137:357-366), siblings, importers, `_counting_readings` | — | green on the prototype (1,234 passed, section 14) |
| defaults.py | new `INJECTION_BUDGET_S` (3.8); the INSERTION comment (8.2) | absent | not hashed; not a `TEXTNORM_*` constant, so not in the demo re-copy list (injection.py is not copied) |

### 4.1 tests/test_textnorm_meta.py, exact post-edit lines (ruff-formatted, run green on the prototype)
- :90 `def test_a_the_list_has_253_mutants_77_of_p1a_fix4_26_of_p1b_14_of_p1a_fix5_5_of_fix6_31_of_fix7_10_of_p1a_fix8_77_of_the_p1b_fix_batch_and_13_of_g10_with_unique_names():`
- :92 `    assert len(names) == 253 and len(set(names)) == 253, names`
- :97 `        len(names[28:]) == 225` (the comment of :98 gains ", and the 13 of G10 last" at its end)
- :123 `    assert len(names[163:240]) == 77, (`; :149 `        for n in names[163:240]`; after :150 (`    ), "the fix batch mutants"`):
```python
    assert len(names[240:]) == 13 and all(
        n.split(":")[0] in {"deadline", "injection"} for n in names[240:]
    ), "the 13 of G10 (the deadline of the fold)"
```
- :179 becomes (ruff splits it):
```python
    assert {m.test_file for m in mm.M} == {
        mm.T,
        mm.G,
        mm.SC,
        mm.SB,
        mm.FB,
        mm.O,
        mm.RO,
        mm.R2,
        mm.Q9,
        mm.DL,
    }
```
- :190 after `        TESTS / "test_textnorm_app.py",`: `        TESTS / "test_textnorm_deadline.py",`
- :204 `    assert len(rows) == 253`; :367 `    assert behaviour + wording == len(mm.M) == 253`

## 5. Tests: new file tests/test_textnorm_deadline.py (10 tests, no conftest fixture: the mutation runner runs pytest with `--noconftest`)
The whole file is in the drafter's scratchpad (`g10v3/files/test_textnorm_deadline.py`, 290 lines, ruff clean, 10 of 10 green on the prototype);
the builder copies it. Its parts:
- Constants: `T = "the summary of " + "жизнь " * 200 + "密的码测试"` (holds V with one Han letter
  inserted), `T2 = "密码" * 5_000` (the first half of V 5,000 times, never V), `V = "密码测试"`, and the pinned reading
  sequences (measured on the prototype):
```python
POINTS_T = (
    ("scan_holds",) * 3 + ("_readings",) * 8 + ("_squeezed",) + ("_converge",) * 4 + ("scan_holds",) * 3
)
POINTS_T2 = (
    ("scan_holds",) * 3
    + ("_readings",) * 8
    + ("_squeezed",)
    + ("_converge",) * 2
    + ("scan_holds",) * 3
    + ("_holds_with_one_insertion",)
)
POINTS_NO_VALUE = (
    ("scan_views_no_value",) * 2
    + ("_readings",) * 8
    + ("_squeezed",)
    + ("_converge",) * 4
    + ("scan_views_no_value",)
)
```
  (T: P1, P2, P2b in `scan_holds`; 4 P3 of the bundle readings and 4 P3 of the readings inside `_squeezed`; 1 P4; 4 P5 (one tag text, two
  steps, two passes each); P6, P7a, one P7b. T2: two P5 only (the text converges in one pass per step), then P6, P7a, P7b, and one P7c at hit 4,096.)
- THE STEPPING CLOCK (M4):
```python
class SteppingClock:
    """``time.thread_time`` for a test: reading n (1, 2, 3, ...) returns n; ``where`` names the function that called the reader (the caller of
    ``textnorm._tick``, or ``injection._deadline``'s caller for the injection budget)."""

    def __init__(self) -> None:
        self.reads = 0
        self.where: list[str] = []

    def thread_time(self) -> float:
        self.reads += 1
        self.where.append(sys._getframe(2).f_code.co_name)
        return float(self.reads)


def _clock(monkeypatch) -> SteppingClock:
    clock = SteppingClock()
    monkeypatch.setattr(textnorm, "time", clock)
    return clock
```
  Arithmetic: the counter starts at 0; reading n returns n (1.0 for the first). `_tick` raises when `n > deadline`. With `deadline = k + 0.5`,
  readings 1..k pass (n <= k < k + 0.5) and reading k + 1 raises, so `clock.reads == k + 1` after the raise. A far deadline is `1e9`.
  The frame method: `sys._getframe(2)` inside `thread_time` is the caller of `_tick` (frame 0 `thread_time`, 1 `_tick`, 2 the reading point).
  The patch replaces the module ATTRIBUTE `textnorm.time` (and `injection.time` in D-8) with the instance, which has `thread_time` only:
  textnorm.py and injection.py use `time.thread_time` and nothing else of `time` (grep of the prototype), and the global `time` module is not
  touched, so pytest and other modules are unaffected; `monkeypatch` restores the attribute.
| id | function | what it asserts | tags |
|---|---|---|---|
| D-1 | `test_no_deadline_and_a_far_deadline_give_every_answer_of_today` | 188 string rows of tests/fixtures/textnorm_corpus.json x 3 ways (a in b, b in a, `f"x {a} y"` and b): the answer or the error class name with no argument, `deadline=None`, `deadline=time.thread_time() + 600.0` is the same; `scan_views_no_value` of a and b equal with and without a far deadline | `DEADLINE-NONE` |
| D-2 | `test_a_spent_deadline_raises_and_never_answers` | `deadline=time.thread_time() - 1.0` raises `DeadlinePassed` for `("a summary", "Mary")` and `("密的码测试", V)` (both HOLD the value) and for `scan_views_no_value("a summary", ...)`; an answer False fails with DEADLINE-NOT-FALSE, any other answer with DEADLINE-SPENT | `DEADLINE-SPENT`, `DEADLINE-NOT-FALSE` |
| D-3 | `test_every_reading_point_of_scan_holds_is_pinned_and_each_one_refuses` | `scan_holds(text=T, value=V, deadline=1e9) is True` and `tuple(clock.where) == POINTS_T`; for k in 1..18, `deadline=k + 0.5` raises with `clock.reads == k + 1`; `scan_holds(text=T2, value=V, deadline=1e9) is False` and `== POINTS_T2` | `DEADLINE-POINTS` |
| D-3b | `test_every_reading_point_of_the_injection_views_is_pinned` | `scan_views_no_value(T, deadline=1e9)` reads `POINTS_NO_VALUE`; for k in 1..15 the raise is at reading k + 1 (review N10) | `NO-VALUE-POINTS` |
| D-4 | `test_a_text_found_in_the_cache_still_reads_the_clock` | in `scan_cache()`: a first call with a far deadline; the second call reads exactly `("scan_holds",) * 6`; a spent deadline raises on the cache hit | `DEADLINE-CACHE` |
| D-5 | `test_a_build_cut_by_the_deadline_stores_nothing` | in `scan_cache()`: `deadline=5.5` raises at reading 6, in `_readings` (inside the build); `textnorm._SCAN_CACHE.get().bundles` is empty; the next call without a deadline answers True | `DEADLINE-NO-PARTIAL` |
| D-6 | `test_the_error_is_not_a_size_refusal_and_ends_the_chunked_read_at_once` | `issubclass(DeadlinePassed, TextnormError)`; a spy on `textnorm.scan_views_no_value`; `RegexDetector(0.5)._score("ab " * 100_000, time.thread_time() - 1.0)` raises `DeadlinePassed` after exactly 1 call; `not issubclass(DeadlinePassed, TextTooLong)` | `DEADLINE-NOT-SIZE` |
| D-7 | `test_a_bad_deadline_is_refused_before_any_reading` | `True`, `False`, `"1"`, `float("nan")`, `[1.0]` raise `NotText` for both functions; the stepping clock was read 0 times | `DEADLINE-TYPE` |
| D-8 | `test_the_injection_check_flags_a_run_past_its_budget` | stepping clock on `textnorm.time` AND `injection.time`, `INJECTION_BUDGET_S = 0.5` (the budget is set at reading 1, so the deadline is 1.5; P1 of the fold reads 2): `injection_check(RegexDetector(0.5), "hello world", "t")` is flagged `guard_unavailable` and `caplog` (logger `hadavin_sdk.guard`, WARNING) holds `DeadlinePassed`; with the budget None and the real clock a steering text is `injection_suspected` and "hello world" is not flagged | `DEADLINE-INJECTION` |
| D-9 | `test_the_injection_budget_setting_is_checked` | `defaults.INJECTION_BUDGET_S == 30.0` (a fact pin of D4); `True`, `"30"`, `0`, `-1.0`, NaN, `inf`, `[30.0]`: `injection._deadline()` raises `ValueError` naming `INJECTION_BUDGET_S`, and `injection_check` flags the run `guard_unavailable` | `BUDGET-DEFAULT`, `BUDGET-UNCHECKED` |
Every failing assertion raises `AssertionError` whose message STARTS with its tag (the runner's `judge` reads the first `E ` line and needs an
`AssertionError` there; an escaping `DeadlinePassed` would be a CRASH, so every test catches it and asserts). Two `except Exception` lines
carry `# noqa: BLE001` (ruff's blind-except rule; the same pattern at tests/test_textnorm_round2.py:222 is already red under `ruff check` at
HEAD, a pre-existing finding, not G10's).
Not built (v2 rows dropped, reasons): D-9 of v2 (the redactor view-loop read) and its mutant KR1 exist only with D8's alternative: NOT built in
G10 (N9). D-10 of v2 (a perf ratio row): dropped; a timing ratio is noise on a loaded box and the overhead is measured once (3.5).

## 6. Mutants
### 6.1 The 13 new mutants (appended after the last mutant, "tables: the lazy tables are never kept", before `]  # fmt: skip`; `test_file=DL`)
Each `old` occurs exactly once in the edited, formatted file (meta test g, run green on the prototype). The rows are written in the list's own
style (one `mutant(...)` call, strings with `\n` escapes). Each was run ALONE with the runner's rules on the prototype (section 14): every one KILLED.
| # | name | file | old | new | killer (`only_test`) | expect |
|---|---|---|---|---|---|---|
| 241 | `deadline: the clock is never read` | TN | `"    if deadline is not None and time.thread_time() > deadline:\n"` | `"    if False:\n"` | `test_a_spent_deadline_raises_and_never_answers` | `DEADLINE-SPENT` |
| 242 | `deadline: a spent deadline answers no hit` | TN | `"    deadline = _deadline_checked(deadline)\n    _tick(deadline)\n    _checked(text, value)\n"` | `"    deadline = _deadline_checked(deadline)\n    if deadline is not None and time.thread_time() > deadline:\n        return False\n    _checked(text, value)\n"` | `test_a_spent_deadline_raises_and_never_answers` | `DEADLINE-NOT-FALSE` |
| 243 | `deadline: the error is a TextTooLong` | TN | `"class DeadlinePassed(TextnormError):"` | `"class DeadlinePassed(TextTooLong):"` | `test_the_error_is_not_a_size_refusal_and_ends_the_chunked_read_at_once` | `DEADLINE-NOT-SIZE` |
| 244 | `deadline: a bad value is no deadline` | TN | `"    if type(deadline) not in (int, float) or math.isnan(deadline):\n"` | `"    if False:\n"` | `test_a_bad_deadline_is_refused_before_any_reading` | `DEADLINE-TYPE` |
| 245 | `deadline: the views of the text are built without the deadline` | TN | `"    bundle = _text_bundle(text, deadline)\n"` | `"    bundle = _text_bundle(text)\n"` | `test_every_reading_point_of_scan_holds_is_pinned_and_each_one_refuses` | `DEADLINE-POINTS` |
| 246 | `deadline: the injection views are built without the deadline` | TN | `"    bundle = _text_bundle(raw, deadline)\n"` | `"    bundle = _text_bundle(raw)\n"` | `test_every_reading_point_of_the_injection_views_is_pinned` | `NO-VALUE-POINTS` |
| 247 | `deadline: the scan keys get no deadline` | TN | `"        tuple(sorted(_scan_keys(raw, deadline))),\n"` | `"        tuple(sorted(_scan_keys(raw))),\n"` | `test_every_reading_point_of_scan_holds_is_pinned_and_each_one_refuses` | `DEADLINE-POINTS` |
| 248 | `deadline: no reading before a prefix pass` | TN | `"        _tick(deadline)\n        nfkd = unicodedata.normalize(\"NFKD\", text)\n"` | `"        nfkd = unicodedata.normalize(\"NFKD\", text)\n"` | same as 245 | `DEADLINE-POINTS` |
| 249 | `deadline: no reading between the passes of a scan key` | TN | `"        _tick(deadline)\n        out = step(text)\n"` | `"        out = step(text)\n"` | same as 245 | `DEADLINE-POINTS` |
| 250 | `deadline: no reading after the needles of the value` | TN | `"    needles = _needles_or_refuse(value, scripts)\n    _tick(deadline)\n"` | `"    needles = _needles_or_refuse(value, scripts)\n"` | same as 245 | `DEADLINE-POINTS` |
| 251 | `deadline: no reading in the insertion loop` | TN | `"        hits += 1\n        if not hits % 4096:\n            _tick(deadline)\n        stop = start + h\n"` | `"        stop = start + h\n"` | same as 245 | `DEADLINE-POINTS` |
| 252 | `injection: the detector passes no deadline` | INJ | `"        score = self._score(text, _deadline())\n"` | `"        score = self._score(text)\n"` | `test_the_injection_check_flags_a_run_past_its_budget` | `DEADLINE-INJECTION` |
| 253 | `injection: the budget setting is not checked` | INJ | `"    if type(budget) not in (int, float) or not 0 < budget < float(\"inf\"):\n"` | `"    if False:\n"` | `test_the_injection_budget_setting_is_checked` | `BUDGET-UNCHECKED` |
Collision check (codebase M6): 241's old text occurs once in the source (only in `_tick`; every reading point is a `_tick(deadline)` call, P1
is not written inline); 242's NEW text holds 241's old text, which is harmless (each mutant is applied alone to the unmutated file; meta g counts
`old` in the unmutated file). 242 is ONE replacement of a three-line block (the review's "move P1" form is gone; v2's cache mutant is dropped,
see below). 251's old text holds the loop's own line `stop = start + h`, which makes it unique (the second loop has the same three reading
lines before `lo = max(...)`).
Intentionally without a mutant (each is still pinned by D-3 / D-3b's exact reading sequence): P1 of `scan_views_no_value`, P2, P3b, P4, P6,
P7a, P7b, the second-loop P7c, the `_squeezed`/`_views`/`_view_pairs` deadline wiring (a removal changes the sequence; 245-251 already show the
sequence kills every removal of that kind). v2's mutant 242 ("ignored on a cache hit") is DROPPED (readiness M5): the cache-hit path reads in
`scan_holds` itself (P1, P2, P2b, P6), so no single replacement skips them all; D-4 pins the six readings as a test with no mutant.

### 6.2 The 9 re-pointed mutants (same mutation, same killer and expect; only `old` and `new` re-copied from the edited source)
| HEAD line | name | killer file | old (after G10) | new (after G10) |
|---|---|---|---|---|
| 328-330 | `scan: squeeze_views gives one view` | T | `"    for view in _views(\n        raw, casefold=True, collapse_ws=False, marks_dropped=True, deadline=deadline\n    ):"` | `"    for view in (_fold(raw, casefold=True),):"` |
| 450-453 | `marks: squeeze_views has no marks-dropped views` | T | the same old as above | `"    for view in _views(\n        raw, casefold=True, collapse_ws=False, marks_dropped=False, deadline=deadline\n    ):"` |
| 460-462 | `marks: a view is repeated` | T | `"        scripts=scripts,\n        deadline=deadline,\n    ):\n        if view not in out:\n            out.append(view)"` | `"        scripts=scripts,\n        deadline=deadline,\n    ):\n        out.append(view)"` |
| 688-690 | `insertion: the match is never made` | FB | `"    for view in script_views:\n        _tick(deadline)\n        if any(_holds_with_one_insertion(view, needle, deadline) for needle in inserts):\n            return True\n    return False\n"` | `"    return False\n"` |
| 676-678 | `injection: the call names no value` (killer `test_no_caller_in_the_package_omits_the_value_or_the_scripts`, expect `names no value`: with the new lint rule the mutated `scan_views(text, deadline=deadline)` call has one argument and no `value` keyword) | FB | `"textnorm.scan_views_no_value(text, deadline=deadline)"` | `"textnorm.scan_views(text, deadline=deadline)"` |
| 770-772 | `injection: a module builds its own views` | O | `"            yield text, textnorm.scan_views_no_value(text, deadline=deadline)\n"` | `"            yield text, textnorm.scan_keyset(text)\n"` |
| 849-851 | `injection: the pieces do not overlap` | Q9 | `"        if back >= low and _holds(text[end - back : end], need_kept, need_letters, deadline):\n"` | `"        if back >= 1:\n"` |
| 855-857 | `injection: the new piece ignores the letters it holds` | Q9 `[300]` | the same old as above | `"        if back >= low:\n"` |
| 864-866 | `injection: the second half of a halved piece starts at the halfway point` | Q9 | `"            yield from RegexDetector._fit(piece[second:], deadline)\n"` | `"            yield from RegexDetector._fit(piece[cut:], deadline)\n"` |
Two old strings are shared by two mutants each (the `_views` call of `_squeezed`; the `_holds` line): allowed, each occurs once in the source.
Every other mutant's old string still occurs exactly once (meta test g green on the prototype).

## 7. PHASES (build order; every command from the repo root; the box rule: `uptime` first, wait while the load is above 6, `-n 3` at most, one heavy process at a time)
Variables used below: `TN_ALL="tests/test_textnorm*.py"` (16 files at HEAD plus the new one: test_textnorm, _app, _callers, _deadline, _differential,
_fixbatch, _generator, _meta, _mixed_script_micro, _order137, _perf, _q9, _round1, _round2, _scan, _siblings);
`INJ="tests/test_k5_fixes5.py tests/test_injection_chunk_boundary.py tests/test_p6_detectors.py tests/test_p1a_fixes.py tests/test_s4_llm_guard.py tests/test_review_pr3_round2.py tests/test_p5p6_followups.py"`;
`CANARY="tests/test_redact_fold_budget.py tests/test_redact_settle_loop.py"`.
MUST-STAY-GREEN (the whole gate, run at the end of every phase from phase 3 on; earlier phases name their expected reds):
`uv run pytest -n 3 -m "not live and not perf" $TN_ALL $INJ $CANARY` (prototype: 1,234 passed, 154 s at load 1.4 to 3.1), then the perf rows
alone: `uv run pytest -m perf tests/test_textnorm_round2.py -s` and `uv run pytest -m perf tests/test_textnorm_perf.py` (NOT run by the drafter),
then `uv run ruff format --check src tests tools && uv run ruff check src tests/test_textnorm_deadline.py tests/textnorm_mutants.py tests/test_textnorm_meta.py`.

Phase 0, fail-before (before any source edit). Copy `tests/test_textnorm_deadline.py` in and run `uv run pytest tests/test_textnorm_deadline.py`:
RED, collection error `ImportError: cannot import name 'DeadlinePassed'` (all 10 tests red by name; measured on HEAD). The behavioural
fail-before of each assertion is the mutant run of phase 4 (each mutant puts back one piece of HEAD's behaviour and its killer fails with its tag).
Phase 1, guard/textnorm.py (3.3, 3.4, 3.7) and the four pin edits that follow from it: tests/test_textnorm.py:1200-1241,
tests/test_textnorm_fixbatch.py:666-668, tests/test_textnorm_callers.py:226, tests/test_textnorm_order137.py:494. Then
`uv run ruff format src/hadavin_sdk/guard/textnorm.py && uv run ruff check src/hadavin_sdk/guard/textnorm.py` and
`uv run pytest -n 3 -m "not live and not perf" $TN_ALL $INJ $CANARY`. EXPECTED RED until phase 5 (and only these):
`tests/test_textnorm.py::test_the_manifest_pins_the_files_a_demo_copies` (hash), and the meta tests that read the mutant list against the source:
`tests/test_textnorm_meta.py::test_g_every_search_string_occurs_exactly_once_in_the_file_it_targets` (4 textnorm old strings gone) until phase 4.
Without the four pin edits these are red too (measured on HEAD tests + the prototype source): `test_the_public_names_are_exactly_the_listed_thirty_six`,
`test_the_module_docstring_lists_every_public_name`, `test_refusal_handlers_has_five_entries_and_the_banned_names_follow_textnorm`,
`test_exactly_the_cap_in_scan_keys_is_allowed_and_one_over_is_refused` (and see 14 for the exact red list).
Phase 2, guard/injection.py (3.6), defaults.py (3.8 and 8.2), the fixbatch lint (:323) and the round2 perf row (:344, :355). Same commands
(ruff on the two files). EXPECTED RED: the manifest test; meta g (now also the 5 injection old strings) until phase 4.
`tests/test_textnorm_fixbatch.py::test_no_caller_in_the_package_omits_the_value_or_the_scripts` is red if its pin edit is left out.
Phase 3, the new test file (section 5) and the meta lines that do not count mutants (:179 killer set, :190 uniqueness list) together with the
`DL` constant and `TESTS` of tests/textnorm_mutants.py. `uv run pytest tests/test_textnorm_deadline.py -v`: 10 GREEN. Meta: red until phase 4
(g, and the count tests :90, :204, :367 once the list grows).
Phase 4, the mutant list: the 9 re-points (6.2), the 13 new mutants (6.1), the docstring (:12), the meta counts (4.1). Then
`uv run pytest tests/test_textnorm_meta.py`: GREEN (25 tests with the deadline file, measured: the meta file alone is the gate).
Run every new and re-pointed mutant ALONE: `uv run python tests/textnorm_mutants.py "deadline:"` and, one at a time,
`uv run python tests/textnorm_mutants.py "<name>"` for each of the 9 re-pointed names and the two `injection:` names of 6.1. NOTE: each run
first runs the unmutated BASELINE over all 11 files of `TESTS` (minutes); the drafter ran the same `run_mutants` with `tests=[the killer's file]`
instead (section 14). Every row must print `ok  killed`.
Phase 5, the manifest hash and the docs: `sha256sum src/hadavin_sdk/guard/textnorm.py` -> tests/fixtures/textnorm_manifest.json:4; the CHANGELOG
item (8.3) with that hash and the mutant sentence; the defaults.py comment (8.2, if not done in phase 2). Then MUST-STAY-GREEN in full.
The SECURITY lines (8.4) are NOT the builder's (D9).

## 8. The false-hit rates (part b)
### 8.1 What is documented today, and what is wrong with it
- defaults.py:234-241 (the INSERTION comment; :238 holds "...stay near 1% or lower per 10,000 characters of text; a needle holding several
  groups takes the largest minimum, ..."): the "1%" measures only what the ONE-INSERTED-LETTER match ADDS, per script, on Bible text (CHANGELOG
  "ONE INSERTED LETTER"). It is the only rate in the code and is read as the scan's rate (G1 review M5, E11). True for what it measures,
  misleading by what it leaves out.
- The evidence (handover/core-c/evidence/G1-false-hits-and-cost.md): run 1 (section A) and "Round 2 (2026-11-20, low load)" (:106 on, committed
  e70aecaa9, script `g1_split.py`). Round 2 re-ran the Latin classes on a newer export (HEAD 2e3a081: the repository corpus is larger, so the rates
  are comparable to run 1, not equal) and SPLIT every hit: whole word, inside a longer word, across a space or punctuation.
- What the numbers are: an UPPER BOUND on false hits. The values are drawn at random (random pronounceable strings plus a 70-name hand list, about
  30 percent of the 4-letter names; the street/host class draws ordinary corpus words), so a value that is a literal word of the text (`black`,
  `Omar`, `Robert`) counts as a hit although a person would call it a true match of that word. Round 2 counts them: over all 21,591 located Latin
  hits, 32.8 percent are a whole word, 33.0 percent inside a longer word, 34.2 percent across a space or punctuation.
- SECURITY wording today: SECURITY-README-v5.md (the live draft, 08:24Z) K50 at :622-624 ("Not measured") and K51 at :625-627 ("Not limited"),
  table rows :835-836, the status count :873 (K50 and K51 OPEN), the evidence list :883 (K51 UNVERIFIED only), :958 ("no evidence file (K50)"),
  the review-nit table :1031 (N16) and :1034 (N19) (records of review round 4: NOT changed). SECURITY-README-final.md (the earlier draft, 07:17Z)
  L43 at :144, L44 at :145, table rows :257-258. SECURITY.md (repo root) says nothing about the fold; docs/ has no fold page.
- At HEAD no redaction path calls `scan_holds` (2.3): the rates have NO consumer yet.

### 8.2 defaults.py: the finished comment lines (the builder's; phase 2)
HEAD :237-238 become three lines (the tail "; a needle holding several groups ..." is kept on the third, the sentence reads through):
```
# The numbers come from a measurement on running text (CHANGELOG, "ONE INSERTED LETTER"): for each script, the shortest needle for which the
# extra matches the insertion adds stay near 1% or lower per 10,000 characters of text (that figure is only what the one-inserted-letter match ADDS,
# per script, on Bible text; it is NOT the false-hit rate of the whole scan, see FALSE HITS below); a needle holding several groups takes the largest minimum, except a needle of Han and kana only (a Japanese word), which takes the Han
```
and after HEAD :241 (`# the matcher takes (its work grows with the needle length for each hit); a longer needle is matched exactly only.`),
before `TEXTNORM_INSERTION_MIN_CHARS = 12`:
```
# FALSE HITS of the whole scan_holds, an UPPER BOUND (measured 2026-11-20, Python 3.13.18, Unicode 15.1.0; handover/core-c/evidence/
# G1-false-hits-and-cost.md, "Round 2"): the share of 10,000-character chunks of ordinary Latin text (repository prose and code, standard-library
# docstrings, generated text) in which scan_holds reports a value drawn at random (random pronounceable strings and a 70-name hand list, not real
# protected values): 4 letters 5.3%, 5 letters 1.0%, 6 letters 0.4%, 8 or more 0; a common word of 5-10 letters 3.9%; ASCII ids of 4-5 characters
# 0.22%; 6 digits 0.007%. A value that is a whole word of the text counts as a hit (about one third of all hits); for values of 4-5 characters
# 94-99% of the hits are a FRAGMENT of ordinary words, for 6-letter names 91% are the whole name. Non-Latin: one program's real interface text
# (Russian 4-8 letters 7.6%; Chinese of 2 characters drawn by frequency 5.2%, of 3-4 characters 0); Arabic and Devanagari synthetic only, unknown.
```
(Prototyped in `g10v3/scripts/patch_src.py`; defaults.py is not hashed and no test reads these comment lines: grep of tests for "1% or lower".)

### 8.3 The CHANGELOG item (the builder's; phase 5; appended after CHANGELOG.md:655, the last line of the file)
```
(blank line)
### Changed (G10: a deadline for the text fold, the published false-hit rates; ORDER 023, escalation E11)
- **The fold scan and the injection read stop at a CPU deadline (`guard/textnorm.py`, `guard/injection.py`, `defaults.py`).** <the text of the prototype item, g10v3/files/changelog_item.md, with the overrun numbers of 12.2>
- **False hits of the fold scan, measured (E11).** <8.4 L43/K50 text, with "per 10,000-character chunk" and the evidence path>
- **Counts.** New tests in `tests/test_textnorm_deadline.py` (10 tests). ... The list holds 253 mutants in
  `tests/textnorm_mutants.py` (the 240 of the fold and the 13 of G10; 9 earlier mutants re-pointed ...). Every repository that keeps a byte copy ...:
  - `src/hadavin_sdk/guard/textnorm.py`: `<the builder's sha256>`
```
The exact first and third bullets are in the scratchpad file (`g10v3/files/changelog_item.md`, run green with meta test i and the manifest
test on the prototype); the line "...The list holds 253 mutants in" must END the line and the next line must start with two spaces and
`` `tests/textnorm_mutants.py` `` (meta test i). Line numbers re-derived: the fold item's hash line is :651 (not :650, N2); its mutant sentence
:638-639; both stay unedited as the record.

### 8.4 The SECURITY wording (NOT the builder's: the SECURITY wording lane applies it, D9; the lane's reviewer verifies it against this section)
Into the live draft SECURITY-README-v5.md (or its successor):
- :622-624 K50 becomes: "**K50. Over-matching, measured:** a known name is found inside a longer word or across a space. Example: known `mary`
  found in `summary`. MEASURED 2026-11-20 (evidence/G1-false-hits-and-cost.md, Round 2), an upper bound, per scan of one 10,000-character chunk
  of ordinary Latin text with a value drawn at random: 4 letters 5.3 %, 5 letters 1.0 %, 6 letters 0.4 %, 8 or more 0; common words of 5 to 10
  letters 3.9 %; ASCII ids of 4 to 5 characters 0.22 %; 6 digits 0.007 %. About two thirds of the hits are not a whole word; for 4 to 5
  characters almost all (94 to 99 %) damage a word. Real Russian and Chinese interface text: 7.6 % and 5.2 % for short values; Arabic and Hindi:
  synthetic text only, unknown. No masking path uses this scan yet; when one does, innocent text may be masked or withheld at about these rates.
  Status: STATED. Evidence: MEASURED. Who acts: nobody (the consumer's ticket re-measures)."
- :625-627 K51 becomes: "**K51. Limited by a CPU budget:** the planted-instruction check stops at `INJECTION_BUDGET_S` (30 CPU seconds of the
  calling thread) and flags the run (`guard_unavailable`) when the fold passes it. Measured before the limit: 3.6 to 9.6 s for 2,000,000
  characters (evidence G1 B), up to <12.3 worst> s on the drafter's heaviest text (G10 ticket 12.3). A machine about 2x slower than the build box
  flags that text. Only CPU time counts; the wall clock is the caller's. Status: PINNED once G10 lands (tests/test_textnorm_deadline.py).
  Evidence: TESTED. Who acts: nobody." (Until G10 lands, K51 stays OPEN.)
- Rows :835-836: `| K50 over-matching | STATED | MEASURED | evidence/G1-false-hits-and-cost.md run 1 and Round 2 | nobody |` and
  `| K51 folding time | PINNED (after G10) | TESTED | tests/test_textnorm_deadline.py; G10 ticket 12 | nobody |`; the counts at :870-885 move K50
  to STATED/MEASURED and K51 to PINNED/TESTED (the lane recomputes the totals); :958 "no evidence file (K50)" becomes "measured: evidence/
  G1-false-hits-and-cost.md (K50)"; :1031 and :1034 stay (records).
- If the lane still places from SECURITY-README-final.md: :144 L43 takes the K50 text, :145 L44 the K51 text, :257 the row
  `| L43 name inside longer word | evidence/G1-false-hits-and-cost.md (run 1, Round 2) | STATED, MEASURED (upper bound) | core-c |`, :258 the row
  `| L44 no deadline in fold | tests/test_textnorm_deadline.py (G10) | PINNED after G10 | core-c |`.
- SECURITY.md (repo root): no fold section exists; the lane places part 2 of its draft there (its own ticket).
- For the "G1 ticket": this branch has no G1 design ticket (tickets/G1-result-review-1.md is the review); the review table gets M4 "DEADLINE: G10
  (ORDER 023)" and M5 "MEASURED (E11; evidence G1-false-hits-and-cost.md run 1 and Round 2); published G10 8.2-8.4; consumer pending" (the
  board lane's edit, not the builder's).

## 9. The NOT RUN items (part c)
| item | status now | default (D7) |
|---|---|---|
| split of the Latin hits into whole word / inside a word / across spaces | DONE by the evidence runner (Round 2, e70aecaa9) | quoted in 8.2-8.4; nothing more to run |
| real non-Latin text | PARTLY DONE (Round 2: Russian and Chinese from the vim `.mo` catalogs, one program's interface text, 7 and 15 chunks); Arabic and Devanagari: none on the box | stays "synthetic only, unknown" for Arabic and Devanagari; a real corpus needs the lead's leave to fetch (christos-c/bible-corpus, UD treebanks were used before) |
| 2,000 values without `scan_cache()` | NOT RUN: ASCII about 756 s (fits one process only at load below 2), 1 percent about 2,023 s, distinct about 3 h (does not fit) | run ASCII only, at load below 2, when the lead wants the row; it has no consumer (no code scans per value without the cache; the consumer rule says to use `scan_cache()`) |
| the redactor's view-building stretch as one figure (D8) | NOT RUN | not needed while D8's default stands |
The drafter ran none of the evidence runs (the measurements of section 12 are of the deadline, not of the false-hit rates).

## 10. Decisions for the lead (the builder builds the DEFAULT; an alternative is out of scope unless the lead says so)
ORDER 023 says "add a deadline to the text fold in the redactor's style; publish the measured false-hit rates with a date; run the NOT RUN items
that fit the box at low load". It does not choose D1-D10; the defaults below are the drafter's, unapproved until the lead says so.
| id | decision | DEFAULT (built) | fallback (alternative) | consequence of the default / of the fallback |
|---|---|---|---|---|
| D1 | where the clock is read | inside textnorm.py at the points of 3.4 | only in the callers' loops (no textnorm change) | default: overrun = the longest stretch (12.2), textnorm pins change (4). Fallback: overrun one whole scan (up to 5.8 s), the injection read of one text under the cap stays unbounded, no re-copy |
| D2 | how the deadline travels | an explicit `deadline=None` argument down the private chain | a `contextvars` scope set by the two entry points | default: more signatures, explicit, as the redactor. Fallback: fewer signatures, hidden state (a scope leaking into a thread copy), the same readings |
| D3 | which public functions take it | `scan_holds`, `scan_views_no_value` | also `scan_views` | default: the fixbatch:280 pin stays. Fallback: that pin changes; `scan_views` has no caller |
| D4 | the injection budget | `defaults.INJECTION_BUDGET_S = 30.0` | None (no deadline, E11 half open), or `REDACT_BUDGET_S` (6.0) | default: about <12.3 ratio>x the slowest measured 2,000,000-character text (12.3); a machine that much slower flags that text (`guard_unavailable`). None: the deadline exists, nothing uses it. 6.0: the Cyrillic or Devanagari ceiling text is flagged on this box (a new false abstain) |
| D5 | readings without a mutant | P1 of `scan_views_no_value`, P2, P3b, P4, P6, P7a, P7b, the second P7c: pinned by the exact sequences of D-3 / D-3b, no mutant of their own | a mutant each (8 more, 261 in all) | default: a removal of one of them is still killed by D-3 (the sequence), but the list does not show it. Fallback: 8 more runs of D-3 (12 s each), longer list |
| D6 | the error name and message | `DeadlinePassed("the scan passed its deadline")` | a code-style message like the redactor's (`DeadlinePassed("FoldDeadline")`) | default: plain words in the log line of `injection_check`. Fallback: a stable code to grep for; no other change |
| D7 | the NOT RUN rows | as in section 9 | run the 2,000-value ASCII row now | default: no extra CPU on a loaded box; the row stays extrapolated. Fallback: about 13 minutes of one core at load below 2 |
| D8 | a reading in the redactor's view building (`_fold_scan`) | not in G10 (redact.py unchanged) | in G10, with a test and mutant KR1 in tests/redact_mutants.py | default: the redactor's first read stays after the view building (about 4 folds of a capped text, ESTIMATED 0.7 s); redact.py stays G4/G8's. Fallback: a redact.py change in another lane's file |
| D9 | who writes the SECURITY wording | the SECURITY wording lane applies 8.4; the builder writes defaults.py and the CHANGELOG only | the G10 builder edits the SECURITY drafts too | default: the builder's file list has no SECURITY file; the lane's reviewer verifies 8.4. Fallback: two lanes edit one draft (merge risk) |
| D10 | a reading in `injection._score` | none (the regex work of a piece is between two readings; the tail ends the call) | a reading per piece after its regex loop (injection.py raises `textnorm.DeadlinePassed`; the order137 allow-list gains it) | default: a run can end up to <tail> s after its deadline WITH a complete answer (12.3). Fallback: one more mutant and an allow-list edit; the late answer becomes a refusal |

## 11. Stated limits after G10
- CPU clock of the CALLING thread only (as the redactor): waiting for the GIL, a lock or I/O does not advance it; a deadline value from another
  thread means nothing. The wall-clock guard stays the caller's; none of the six `injection_check` call sites has one today (for core-b, next to
  the G7 list).
- Overrun: the longest stretch between two readings, measured <12.2> on the distinct text (the weight of a first-seen text of distinct letters
  is the longest unread stretch, between P1 and P2); a call can also end after its deadline WITH a complete answer (the stretch after the last
  reading: the needle loop, or `_score`'s regex tail, D10).
- The value's work (its needles and scan keys, between P2 and P2b) has no reading inside it: measured <12.2 value> for a value at the weight cap.
- The outcome depends on the machine: a slow machine refuses a text a fast one scans (fail closed: the injection run is flagged, a DENY caller refuses).
- A hostile author can force the refusal of the injection check (a text built to be slow, `guard_unavailable`): the run is flagged, the legitimate
  rest of that text is not read for that run.
- No deadline in `register_value`, `fold`, `fold_view`, `identity_keys`, `scan_views`, `scan_keyset`, `scan_needles` and the other single-pass
  functions.
- 2,000 values without `scan_cache()` stays O(values x text) (deadline-bounded per call, not faster).
- The false-hit rates are an UPPER BOUND on ordinary Latin text with random values; real protected values, other registers and Arabic/Devanagari
  text are not measured.

## 12. Measured by the drafter
<PENDING>

## 13. NOT verified
<PENDING>

## 14. What the drafter ran
<PENDING>

## 15. Findings of review round 1: TAKEN or CONTESTED
Readiness reviewer:
- B1 TAKEN: section 7 (phases 0-5, commands, expected reds measured on the prototype, the fail-before step, the full must-stay-green command
  including the injection files, the canary and the perf rows).
- B2 TAKEN: fixbatch:323 becomes `nargs == 1 and kws <= {"deadline"}`; mutant `injection: the call names no value` re-pointed and run (6.2, 14).
- B3 TAKEN: DECIDED to widen the stub (`key(tag_text, step, deadline=None)`, order137:494); the source passes the deadline unconditionally.
- B4 TAKEN: every test name (5), every mutant's exact old/new, killer and expect (6.1, 6.2), the post-edit lines (3.6, 3.7); all prototyped and
  each mutant run alone with the runner's rules.
- B5 TAKEN: the builder's rule at the top and in 10; every Dn has a default, a fallback and both consequences; the ORDER 023 text is quoted.
- M1 TAKEN (second option): a reading P2b after the value's needles, with a mutant (250); the value work itself is stated as outside the
  per-pass bound with its measured cost (11, 12.2). Threading the deadline into the value work was not chosen: a value is the operator's input.
- M2 TAKEN: the bound for 2,000,000 characters is stated from the code (one piece of at most 32,768 or one window of at most 8,192 per fold call,
  the raw squash after the last piece) and measured (12.3).
- M3 TAKEN: P3b is unconditional (2 readings per text whatever the iota rule); P4's place is inside `_squeezed`'s loop after `_views` returned;
  the NFKD/NFKC soundness sentence is in 2.2.
- M4 TAKEN: the clock class, its arithmetic, the frame method (`sys._getframe(2)`), the patch shape and why nothing else breaks (5); D-5 cuts at
  reading 6, which is in `_readings` by the pinned sequence.
- M5 TAKEN: v2's 242 dropped with the reason; the unmutated points listed (6.1, D5).
- M6 TAKEN: every injection parameter `deadline: float | None = None`; the generators stay static and take it positionally; `INJECTION_BUDGET_S`
  is validated by `_deadline()` (`ValueError`, test D-9, mutant 253).
- M7 TAKEN: the finished defaults.py lines (3.8, 8.2) with the tail spliced.
- M8 TAKEN: line numbers are of HEAD (redact.py :1293, :1334, :1369); the redactor caps its input (runmap.py:197, :222) so the D8 estimate is for
  capped texts.
- M9 TAKEN: "values drawn at random (random pronounceable strings and a 70-name hand list), not real protected values" in every published text.
- M10 TAKEN: the outcome is stated in 1 (the builder: defaults.py and the CHANGELOG; the lane: 8.4; the lane's reviewer verifies 8.4).
- N1 TAKEN (before `class EmptyView`). N2 TAKEN (:651). N3 TAKEN: no copy of textnorm.py exists in this repository (demos/ holds README.md and
  ask-your-data, which has no textnorm file); the byte copies are in other repositories that this lane does not see; the CHANGELOG item is the
  notice. N4 TAKEN (the published text gives per-chunk rates, not "199,000 scans"; the short-id row has 198,801). N5 TAKEN (2.1). N6 TAKEN (every
  number names its source: evidence run 1, Round 2, or this ticket's section 12). N7 TAKEN (:1200, :1241). N8 TAKEN (3.7 item 3). N9 TAKEN (5).
  N10 TAKEN (D-3b).
Codebase reviewer:
- BLOCKER TAKEN: all three red tests are in section 4 with their exact new lines, and the run of HEAD's tests against the prototype source found
  exactly them plus the five expected ones (14).
- M1 TAKEN in part, CONTESTED in part: the overrun is restated as "the longest stretch between two readings" and MEASURED with a sweep of
  expiry offsets (12.2). CONTESTED: a reading in `_score` per piece (D10): the regex work of a piece is already between two readings (the next
  piece's P1 or `_start_of_next`'s fold), and after the last piece a reading could only turn a finished answer into a refusal; the measured tail is
  stated instead (12.3).
- M2 TAKEN: the Devanagari-like text with Mc marks and the tag-heavy text were built from the corpus classes and measured (12.3); the ceiling
  perf row runs with the budget None (4); the budget is validated (M6).
- M3 TAKEN: "an UPPER BOUND", and Round 2's split is quoted (8).
- M4 TAKEN: the SECURITY files and every line (8.4).
- M5 TAKEN: both entry points build the bundle with `_text_bundle(..., deadline)` and pass it to `_all_views`; `_all_views` is unchanged and so
  is the three mutants' old string.
- M6 TAKEN: P1 is a `_tick` call everywhere; 242 is one block replacement; uniqueness checked by meta g on the prototype.
- Nits TAKEN: line drift (0, 4), the defaults splice (8.2), the `"3.13"` literal (3.7), the demos copy (N3), six call sites (2.3), the per-thread
  deadline (3.2, 11).
- Citation table: the DIFFERS rows are corrected in place (TESTS is :40 at HEAD after Q9; the killer-file set :179; the names test :1200 and :1241;
  CHANGELOG :638-639 and :651; redact.py :1293 / :1334 / :1369; the defaults comment :234-241). The NOT VERIFIABLE rows are re-measured (12).
