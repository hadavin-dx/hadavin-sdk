# G3: port of the fold scan of P2d-1 onto the fold (ticket G, part G3)

Written by the G3 builder agent of core-c (role TEXT), 2026-11-20. Nothing was pushed. No head was checked out: P2d-1 was read with git only (for one comparison its `src/hadavin_sdk` was unpacked with `git archive` into a scratch directory outside every worktree and imported from there).

## 1. Where the work is

- Worktree: `/tmp/core-c-g3` (its own `.venv`). Branch: local `wip-g3-p2d`, cut from `wip-g1-fold` (8e4d234). Linear, 6 commits, no merge commit. Working tree clean.
- The task asked for five commits. A sixth holds what the first test batch showed (section 2, D6): it is separate so the straight port (commits 1 to 5) and the adaptation can be read apart.

| SHA | message (first line) |
|---|---|
| 568932bc94a74bec8898cb2da1fac5613754f08f | code G: G3 step 1: textnorm names for the fold scan (fold_view, without_spacing_marks, SPACING_CATEGORIES; weight memo) |
| 7de1c4f86119548be6277c39b517537830e77ef5 | code G: G3 step 2: port the fold scan of P2d-1 (76adadb) into guard/redact.py; runmap views and CPU-time deadline |
| 456c32a615b14539c48485600f92c799b89c7ee7 | code G: G3 step 3: P2d-1's fold-scan tests brought over (six new files, the fuzz row) and shared test files adapted |
| 2be153143f65a778754d0668c801c343b7b3a3e5 | code G: G3 step 4: re-pin after the port (manifest hash of textnorm.py, CHANGELOG re-copy list and entry) |
| 7d6b5fbffdcad79e5ca76908fa3b34f591d519b9 | code G: G3 step 5: the redactor counts its own actions (RedactionResult.actions) and the test of review finding cb-1-1 |
| ef09bf52ca7f93abbcf71ea12a1b0af450a6eefe | code G: G3 step 6: adapt the fold scan to fold5 after the first batch; fold-head record tests updated |

Whole change against `wip-g1-fold`: 20 files, +2,900 -57 (`git diff --shortstat wip-g1-fold HEAD`).

## 2. FAILURES, expected values changed, decisions (read this first)

### Failing tests on the final tree (ef09bf5): 1

| test | first error line | label |
|---|---|---|
| `tests/test_textnorm_round1.py::test_m16_a_spacing_mark_or_modifier_symbol_does_not_split_a_mixed_script_word` | `E       AssertionError: assert (True is False)` / `+  where True = has_mixed_script('ab' + U+0903 + 'cd')` | KNOWN-FROM-FOLD (waits for the lead; not touched) |

NEW failures on the final tree: none. The FIRST batch (on 7d6b5fb, before commit 6) had 7 failures: the known one and 6 NEW. All 6 are closed in commit 6; each is listed here because four of them were closed by editing a test, not only code:

| # | test (first batch) | first error line | cause | how closed |
|---|---|---|---|---|
| F1 | `tests/test_redact_fold.py::test_withhold_rate_on_lines_with_signs_is_measured_and_pinned` | `AssertionError: ['½ cup, mail josé@example.com', 'contact josé@example.com — thanks']` | fold4 vs fold5: fold5 maps the fraction slash to `/` and every dash and typographic quote to ASCII (gap 4). P2d-1's `_char_class` then called `½`, `—`, curly quotes "not an ordinary fold" and the line was withheld | CODE (`redact._char_class`), test not edited |
| F2 | `tests/test_redact_fold.py::test_one_half_is_masked_around_but_a_full_width_slash_is_still_an_attack` | `assert '[line withhe...ue] <EMAIL_1>' == '½ cup, mail <EMAIL_1> now'` | same | CODE, test not edited |
| F3 | `tests/test_redact_fold_budget.py::test_dm_2_257_decomposed_names_refuse_the_text_and_256_do_not` | `Failed: DID NOT RAISE InputTooLarge` | NOT fold4/fold5: the fold's `runmap.canonical` (P1b) is NFKC of one character at a time and composes nothing, so `undo(NFD name) == NFD name`, `_decoded_masks` pairs nothing and never reaches `MAX_DECODED_MASKS`. On P2d-1's base `canonical` composed. Checked: 257 NFD names are all masked, none refused | TEST INPUT edited (section 2, expected values, row E1) |
| F4 | `tests/test_textnorm_order137.py::test_no_module_outside_textnorm_builds_its_own_views` | `AssertionError: a module builds its own views: [('redact.py', 'fold'), ...]` | a rule of the fold head (order 137, D5): no module but textnorm calls a view builder. The fold scan calls `fold` and `fold_view` by design | TEST edited: one exemption row (D4) |
| F5 | `tests/test_textnorm_siblings.py::test_only_the_guard_and_the_injection_detector_import_textnorm` | `AssertionError: ['app.py', 'guard/injection.py', 'guard/redact.py', 'guard/runmap.py']` | a record of the fold head: who imports textnorm; it also asserted the word "textnorm" is not in runmap.py. Decisions b and c of the task make redact.py and runmap.py import it | TEST (the record) edited |
| F6 | `tests/test_textnorm_siblings.py::test_every_place_in_src_that_normalises_or_case_folds_text_is_recorded` | `AssertionError: ['guard/redact.py']` | a record of the fold head: files that call `normalize(`; redact.py now does (`_char_class`, `_mark_flags`) | TEST (the record) edited: a row with its reason, as the test's docstring asks |

### Expected values and test inputs that had to change

P2d-1's own fold tests (the invariant "pass under fold5 without edits"): ONE test changed (E1), two calls adapted to a changed signature (E2), one mutant search text (E3, E4). No expected OUTPUT value of P2d-1's fold tests was changed.

| # | file | old | new | reason |
|---|---|---|---|---|
| E1 | `tests/test_redact_fold_budget.py::test_dm_2_...` | names are `NFD("Zoé<X><nnnn> Müller")`; 257 raise `InputTooLarge`, 256 do not | names start with full-width `Z` (U+FF3A), same 257 / 256 edge; added: 257 NFD names without it are NOT refused and all masked | the fold's `canonical` composes nothing (P1b), so an NFD name takes no decoded-mask slot (F3). Not fold4 vs fold5 |
| E2 | `tests/test_redact_marks.py` lines 32 and 201 | `textnorm.fold_views(text)` | `textnorm.fold_views(text, scripts=frozenset())` | the fold head (fix7/fix8) made `scripts` a required keyword; values compared are unchanged |
| E3 | `tests/redact_mutants.py` W13 | old text `        canonical(without_spacing_marks(text)),\n` -> `""` | `    unmarked = without_spacing_marks(text)\n` -> `    unmarked = text\n` | `_views` on the fold is written differently (two views from one `unmarked`) |
| E4 | `tests/redact_mutants.py` SLASH | `... (c == "/" and "\\u2044" in f)` | `... (c == "/" and "\\u2044" in src)` | fold5 writes U+2044 as `/`; the sign is known by its NFKD form (D6) |

Tests of the fold head (not P2d-1's) whose pins changed, all because the port adds callers and names:

| # | file | old | new | reason |
|---|---|---|---|---|
| E5 | `tests/test_textnorm.py` names test | `..._thirty_three`, 33 names | `..._thirty_six`, 36 names (+ `SPACING_CATEGORIES`, `fold_view`, `without_spacing_marks`) | decision a (P2d-1 made the same edit, 20 -> 23) |
| E6 | `tests/test_textnorm_fixbatch.py:668` | `len(__all__) == 33` | 36 | same |
| E7 | `tests/test_textnorm_meta.py` | `BANNED = ("fold", "squeeze", "identity_key")`; `EXEMPTIONS = {}` | `BANNED` + `"fold_view"`; `EXEMPTIONS = {"src/hadavin_sdk/guard/redact.py": <reason>}` | D3; the file's own comment said "PR 77 adds its own row" (PR 77 = P2d-1) |
| E8 | `tests/test_textnorm_order137.py` | `BUILDERS` without `fold_view`; calls must be `[]` | `BUILDERS` + `fold_view`; `BUILDER_EXEMPTIONS = {"redact.py": {"fold", "fold_view"}}`, the row must be used and exact | D4 |
| E9 | `tests/test_textnorm_siblings.py` users | `["app.py", "guard/injection.py"]`; "textnorm" not in runmap.py, evidence.py, egress.py | + `guard/redact.py`, `guard/runmap.py`; "textnorm" not in evidence.py, egress.py; runmap imports exactly `without_spacing_marks` and has no `textnorm.` call | decisions b, c |
| E10 | `tests/test_textnorm_siblings.py` `RECORDED_SIBLINGS` | 5 rows | + `guard/redact.py` with its reason | redact.py calls `unicodedata.normalize` on one character |

That is more than "a handful" only if E5 to E10 are counted; they are pins of names and of who-calls-what, not expected values of P2d-1's fold tests, so I did not stop. Lead: say so if you count them otherwise.

### Decisions (numbered; the simpler option not taken is named)

- D1. `fold_view` is P2d-1's body, unchanged in meaning, on the fold head's `_prefix` and `_finish` (the fold5 steps; `_prefix` holds the fold5 punctuation map). No fold4 code was copied. Checked: for three texts with U+0345, marks and typographic punctuation the four `fold_view` switches give exactly the set `fold_views(raw, scripts=frozenset())` returns; `fold_view(raw) == fold(raw)` (P2d-1's `test_marks_11`). The private `_without_spacing_marks` STAYS (two textnorm mutants search for its call text); `without_spacing_marks` is the checked public wrapper, as on P2d-1. `_SPACING_CATEGORIES` is renamed with no alias (nothing else used it). Simpler option not taken: rename the private function too (breaks two mutant search texts).
- D2. P2d-1's speed-ups in textnorm are ported too (`functools.lru_cache` on `_char_weight`, the digest-keyed `_WEIGHT_MEMO` of `_weight`): `tests/test_redact_marks.py::test_marks_12` and mutant W15 need them. Simpler option not taken: leave them out and drop that test.
- D3. TID251: `fold_view` is added to the banned-api list the way `fold` is (it is one view; unbanned it would be a way round the ban on `fold`), and `src/hadavin_sdk/guard/redact.py` gets a per-file-ignore for TID251 with a reason row in `EXEMPTIONS` (`tests/test_textnorm_meta.py`). Without the row `ruff check src` fails on redact.py's `fold` import. CI step A (`--ignore-noqa`) passes; step B still counts 6 (not re-run by hand: the fixtures did not change). Simpler option not taken: call only `fold_view` in redact.py and leave it unbanned (hides the single-view calls from the rule).
- D4. The fold's rule "no module outside textnorm builds its own views" (order 137, D5) got ONE exemption row for redact.py, limited to `fold` and `fold_view`, and `fold_view` joined the builders the rule watches. THIS IS A RULE OF THE FOLD THAT THE PORT BREAKS BY DESIGN: the lead should confirm the exemption. Simpler option not taken: leave F4 failing for the lead.
- D5. `runmap._views`: BOTH new views, `canonical(unmarked)` and `composed(unmarked)`. They can differ: `"jose" + U+0903 + U+0301` gives `jose` + U+0301 in the first and precomposed `josé` in the second (`tests/test_redact_g3_port.py::test_views_the_marks_dropped_views_...`). I found NO input where the twin changes the OUTPUT of `redact_text` (the fold scan inside `redact()` already masks the decomposed spelling in place), so there is no behaviour test and no mutant for the twin alone; it costs one more `redact()` pass on texts where it differs from every earlier view. Simpler option not taken: only `canonical(unmarked)` (the task ordered the twin unless shown identical).
- D6. `redact._char_class` adapted to fold5 (commit 6). Unported, 50 code points changed class against P2d-1 (all from the fold5 punctuation map, gap 4) and lines with `½`, an em dash or a curly quote plus a fold hit were withheld whole. Now: (a) a fraction sign (`½`) is recognised by the U+2044 in its NFKD form and is `('1/2', 1)` again, as on P2d-1; (b) a dash (Pd, not a compatibility form), the minus sign and the six typographic quotes are their ASCII form with flag 0 = ordinary typography: a value beside, around or written with them is masked in the line as written (a UUID with en dashes becomes `<UUID_1>`, the map keeps the written spelling); (c) U+2215, U+2571, U+29F8 are refused (line withheld when it has a fold hit): on P2d-1 they were left alone because fold4 did not map them; (d) U+FFFD is dropped (fold5 drops it). 30 code points differ from P2d-1 after the adaptation: table in section 6. Simpler options not taken: leave all 50 refused (2 of P2d-1's tests fail and ordinary prose with a dash is withheld); or flag 1 for dashes and quotes (a value written with a dash withholds the line: safer, more withheld lines). THE LEAD SHOULD CONFIRM flag 0.
- D7. The action counter (decision d): `RedactionResult.actions: int = 0`. +1 per value masked by `_mask` (pattern pass and each hit of a withheld line), +1 per `_register_written` (in-place fold mask), + the number of copies the sweep replaced, +1 per withheld line or block. The masks of a fold round that is rolled back are taken back (`_open_journal` remembers the count, `_rollback` restores it), so a line withheld after one in-place round counts its hits and the line, not the discarded round. A line the fold scan reads and leaves alone counts 0. `redact_many` returns a tuple and was NOT given the count. Simpler option not taken: count without the rollback (the number would then include masks that are in no text).
- D8. The verify batch ran TWICE (the task said once): once on 7d6b5fb (7 failures), once on the final tree ef09bf5 after commit 6 changed redact.py. Between them one targeted run of 10 files. Each failing thing had 2 tries.
- D9. `tests/redact_mutants.py` has no meta-test that pins its count (63, measured by import). I added none. Simpler option taken.
- D10. CHANGELOG: one new entry under "Upgrade steps" (P2d-1's entry, adapted: 36 names, the fold5 difference, `actions`; P2d-1's timing numbers are NOT repeated as measured here). P2d-1's three small edits of old CHANGELOG lines (20 -> 23 names, 90 -> 91 mutants) were not ported: those lines read differently on the fold.

## 3. P2d-1's 14 files (`git diff 2572847 refs/inputs/core/P2d-1`)

| file | verdict | reason |
|---|---|---|
| CHANGELOG.md | ADAPT | new entry written for the fold (D10); the re-copy hash is the measured one |
| src/hadavin_sdk/defaults.py | TAKE | the hunk applied as written (comment of `REDACT_BUDGET_S`: CPU seconds); one word added (`composed`) |
| src/hadavin_sdk/guard/redact.py | TAKE, then ADAPT | the file was byte-equal on the fold and on P2d-1's base, so P2d-1's diff applied as written (commit 2: all of decision b, `MAX_FOLD_ROUNDS`, `FOLD_NOTE`, `_deadline`, the alias index, PuTTY before PEM). Then `_char_class` for fold5 (D6) and the counter (D7) |
| src/hadavin_sdk/guard/runmap.py | ADAPT | written by hand on the fold's six-view `_views`; `thread_time`, `_decoded_masks(current, text, deadline=None)`, the deadline to both `redact()` calls. `redact_text` signature unchanged |
| src/hadavin_sdk/guard/textnorm.py | ADAPT | D1, D2; `__all__` and the docstring's name list (36) |
| tests/fixtures/textnorm_manifest.json | ADAPT | re-pinned to the measured hash (section 5) |
| tests/redact_mutants.py | TAKE, 2 edits | E3, E4. All 63 search texts occur once in the source (mutant 21 twice, on purpose, as its docstring says). NOT RUN |
| tests/test_k5_round12_fuzz.py | TAKE | file was byte-equal; hunk applied as written |
| tests/test_redact_fold.py | TAKE | unchanged |
| tests/test_redact_fold_budget.py | TAKE, 1 test edited | E1 |
| tests/test_redact_fold_property.py | TAKE | unchanged |
| tests/test_redact_fold_seams.py | TAKE | unchanged |
| tests/test_redact_marks.py | TAKE, 2 calls | E2 |
| tests/test_textnorm.py | ADAPT | E5 (P2d-1's edit was 20 -> 23 on another list) |

Not in P2d-1, added or changed by the port: `pyproject.toml` (D3), `tests/test_redact_g3_port.py` (new: counter, views, fold5 classes; 11 tests), `tests/test_textnorm_fixbatch.py`, `tests/test_textnorm_meta.py`, `tests/test_textnorm_order137.py`, `tests/test_textnorm_siblings.py` (E6 to E10).

## 4. The final `_views` list (`src/hadavin_sdk/guard/runmap.py`)

```python
    unescaped = fits_after_nfkc(json_unescape(text, simple="/"))
    undone = fits_after_nfkc(undo(text))
    unmarked = without_spacing_marks(text)
    for view in (
        canonical(text),
        canonical(unescaped),
        undone,
        composed(text),
        composed(unescaped),
        composed(undone),
        canonical(unmarked),
        composed(unmarked),
    ):
        view = _clean(view)
        if view != text and view not in out:
            out.append(view)
```

`without_spacing_marks` runs textnorm's input check (`NotText`, `TextTooLong`): inside `redact_text` both become `RedactionError`, as every other failure there. A direct caller of `runmap._views` sees the textnorm error.

## 5. Pins, old -> new

| pin | old (wip-g1-fold) | new | how |
|---|---|---|---|
| sha256 of `src/hadavin_sdk/guard/textnorm.py` in `tests/fixtures/textnorm_manifest.json` and in the CHANGELOG re-copy list | 1b923f323822fc4059e0a401851a0abe129aa0bb80e81923d2bb0735f469a174 | e7a93738f10e7ea66e164c929d20c0405a0730d41852e0ff88856720ea6cdbee | file bytes, CRLF read as LF, sha256, as `test_the_manifest_pins_the_files_a_demo_copies` computes it. textnorm.py did not change after commit 1; the manifest test passes on the final tree |
| the other four manifest files | (unchanged) | same | re-hashed: equal |
| textnorm mutant count (`tests/test_textnorm_meta.py`, three literals; header; CHANGELOG) | 240 | 240 | measured `len(tests.textnorm_mutants.M)` = 240: no literal moved. `test_g_every_search_string_occurs_exactly_once...` passes on the changed textnorm.py |
| redact mutant count | (file not on the fold) | 63 | measured `len(tests.redact_mutants.M)`; no test pins it (D9) |
| public names of textnorm | 33 | 36 | E5, E6; docstring "THE PUBLIC NAMES (36" |
| TID251 banned names | 3 | 4 (`fold_view`) | D3 |

## 6. The 30 code points whose class differs from P2d-1 (fold4) after the adaptation

Made by calling `redact._char_class` for every code point outside printable ASCII and the surrogates on both trees (P2d-1 unpacked from git, and the port; the port side was computed on the working tree of commit 6 before it was committed). Class = (folded text, flag) or null = "not an ordinary fold" (the line is withheld when it has a fold hit).

| code point | cat | name | P2d-1 (fold4) | port (fold5) |
|---|---|---|---|---|
| U+058A | Pd | ARMENIAN HYPHEN | `["\u058a", 0]` | `["-", 0]` |
| U+05BE | Pd | HEBREW PUNCTUATION MAQAF | `["\u05be", 0]` | `["-", 0]` |
| U+1400 | Pd | CANADIAN SYLLABICS HYPHEN | `["\u1400", 0]` | `["-", 0]` |
| U+1806 | Pd | MONGOLIAN TODO SOFT HYPHEN | `["\u1806", 0]` | `["-", 0]` |
| U+2010 | Pd | HYPHEN | `["\u2010", 0]` | `["-", 0]` |
| U+2012 | Pd | FIGURE DASH | `["\u2012", 0]` | `["-", 0]` |
| U+2013 | Pd | EN DASH | `["\u2013", 0]` | `["-", 0]` |
| U+2014 | Pd | EM DASH | `["\u2014", 0]` | `["-", 0]` |
| U+2015 | Pd | HORIZONTAL BAR | `["\u2015", 0]` | `["-", 0]` |
| U+2018 | Pi | LEFT SINGLE QUOTATION MARK | `["\u2018", 0]` | `["'", 0]` |
| U+2019 | Pf | RIGHT SINGLE QUOTATION MARK | `["\u2019", 0]` | `["'", 0]` |
| U+201B | Pi | SINGLE HIGH-REVERSED-9 QUOTATION MARK | `["\u201b", 0]` | `["'", 0]` |
| U+201C | Pi | LEFT DOUBLE QUOTATION MARK | `["\u201c", 0]` | `["\"", 0]` |
| U+201D | Pf | RIGHT DOUBLE QUOTATION MARK | `["\u201d", 0]` | `["\"", 0]` |
| U+201F | Pi | DOUBLE HIGH-REVERSED-9 QUOTATION MARK | `["\u201f", 0]` | `["\"", 0]` |
| U+2212 | Sm | MINUS SIGN | `["\u2212", 0]` | `["-", 0]` |
| U+2215 | Sm | DIVISION SLASH | `["\u2215", 0]` | `null` |
| U+2571 | So | BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT | `["\u2571", 0]` | `null` |
| U+29F8 | Sm | BIG SOLIDUS | `["\u29f8", 0]` | `null` |
| U+2E17 | Pd | DOUBLE OBLIQUE HYPHEN | `["\u2e17", 0]` | `["-", 0]` |
| U+2E1A | Pd | HYPHEN WITH DIAERESIS | `["\u2e1a", 0]` | `["-", 0]` |
| U+2E3A | Pd | TWO-EM DASH | `["\u2e3a", 0]` | `["-", 0]` |
| U+2E3B | Pd | THREE-EM DASH | `["\u2e3b", 0]` | `["-", 0]` |
| U+2E40 | Pd | DOUBLE HYPHEN | `["\u2e40", 0]` | `["-", 0]` |
| U+2E5D | Pd | OBLIQUE HYPHEN | `["\u2e5d", 0]` | `["-", 0]` |
| U+301C | Pd | WAVE DASH | `["\u301c", 0]` | `["-", 0]` |
| U+3030 | Pd | WAVY DASH | `["\u3030", 0]` | `["-", 0]` |
| U+30A0 | Pd | KATAKANA-HIRAGANA DOUBLE HYPHEN | `["\u30a0", 0]` | `["-", 0]` |
| U+FFFD | So | REPLACEMENT CHARACTER | `["\ufffd", 0]` | `["", 0]` |
| U+10EAD | Pd | YEZIDI HYPHENATION MARK | `["\ud803\udead", 0]` | `["-", 0]` |

## 7. Files that are not TEXT's own (`git diff --numstat wip-g1-fold HEAD`)

| file | + | - | note |
|---|---|---|---|
| src/hadavin_sdk/defaults.py | 10 | 4 | comment of `REDACT_BUDGET_S` only; the value 6.0 is unchanged, its MEANING changed (CPU seconds of the thread, not wall time) |
| pyproject.toml | 4 | 0 | banned-api row for `fold_view`; per-file-ignore TID251 for guard/redact.py |
| CHANGELOG.md | 9 | 1 | |

`guard/redact.py` (+551 -18), `guard/runmap.py` (+29 -9), `guard/textnorm.py` (+68 -8) are TEXT's. `.github/workflows/ci.yml` was not changed (the two TID251 steps hold word for word). Callers of `redact_text` (judge, bedrock_guardrail, evals, tools, channel) were not edited; their behaviour changes with it: a look-alike line is withheld, and the budget is CPU time.

## 8. NOT checked / NOT RUN

- The mutant runners: `tests/redact_mutants.py` (63) and `tests/textnorm_mutants.py` (240) NOT RUN. Only checked statically: every redact mutant's search text occurs in its file (once; mutant 21 twice) and every killer test name exists. Whether each mutant is still KILLED under fold5 is UNVERIFIED (W13 and 18/19 had their search text changed).
- The whole repository suite NOT RUN (ordered). Run: 62 test files (list below). `tests/contracts`, `tests/demo_*` not run.
- Python 3.12 / Unicode 15.0.0: nothing run.
- P2d-1's timing numbers were not measured on the fold. The three perf-marked tests passed once, serially (56 s for the file); no number was recorded.
- G3-I5 / the `is_masked` test of the ticket: `_scan` and `is_masked` (part G0) are NOT in this worktree, so the test "is_masked returns False for a look-alike spelling" could not be written; `tests/test_redact_g3_port.py` tests the counter on `redact()` instead. G3-I6 (P1d-a rows on the same tree): P1d-a is not in this worktree, not checked.
- `redact_many` does not expose the counter (D7).
- CI TID251 step B (the six fixture forms) not re-run by hand; step A was (passes).
- The G1 finding about an invisible character between a letter and its accent, and the m16 decision, are untouched.
- The fold scan was ported by applying P2d-1's diff, not re-read line by line against fold5 beyond `_char_class`: other places where P2d-1 reasons about what the fold does to a character (`_aligned_fold`'s `.replace(U+2044, "/")`, now a no-op) were left as they are. The all-code-points test of P2d-1 (`test_redact_fold_budget.py`, the class of every character agrees with `fold`) passes.
- 4 xfailed tests are P2d-1's own strict "open hole" marks (GAP-1, VARIANT-1(a), VARIANT-1(c), L5), brought over unchanged. 19 skips: all "HADAVIN_TEST_PG_DSN not set" (postgres tests) as far as the tail shows; the full skip list is in the raw output, not compared with a baseline.
- No credential-shaped text was added; the test values are the made-up ones P2d-1 uses (`AKIA` + `IOSFODNN7EXAMPLE` built from two parts) and example.com addresses.

## 9. Commands and raw output (last 30 lines each; lines cut at 300 characters)

All run in `/tmp/core-c-g3` on the tree of ef09bf5 unless said. The pytest command differs from the task's in three small ways: the file list is de-duplicated, `-rsx` is added, and it was run twice (D8).

### `uv sync --all-extras --group test`

```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
Resolved 103 packages in 7ms
Checked 78 packages in 0.60ms
exit=0
```

### `uv run --all-extras --group test ruff check src tests tools`

```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
All checks passed!
exit=0
```

### `uv run --all-extras --group test ruff format --check src tests tools`

```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
324 files already formatted
exit=0
```

### `uv run --all-extras --group test pytest -q -m "not perf" -p no:cacheprovider -n 2 -rsx <62 files>` on ef09bf5 (second batch, exit 1)

```
        )
E       AssertionError: assert (True is False)
E        +  where True = has_mixed_script('abःcd')

tests/test_textnorm_round1.py:428: AssertionError
=========================== short test summary info ============================
SKIPPED [1] tests/test_k2_migrations.py:214: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k2_migrations.py:230: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k2_migrations.py:249: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k2_migrations.py:275: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [2] tests/contracts/kinds/store_postgres.py:24: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k2_migrations.py:357: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k2_migrations.py:374: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k2_migrations.py:387: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k2_migrations.py:430: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k5_postgres.py:36: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k5_round10_postgres.py:33: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k5_round10_postgres.py:52: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k5_round10_postgres.py:72: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k5_round10_postgres.py:113: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k5_round10_postgres.py:118: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k5_round10_postgres.py:137: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k5_round10_postgres.py:145: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k5_round10_postgres.py:153: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
XFAIL tests/test_redact_fold.py::test_gap_1_tag_characters_hide_a_key_open_hole - open hole GAP-1: closed by P2d-2 (a pass here means it is closed: remove this mark)
XFAIL tests/test_redact_fold.py::test_variant_1_a_bare_redact_zwsp_copy_open_hole - open hole VARIANT-1(a): closed by P2d-2 (a pass here means it is closed: remove this mark)
XFAIL tests/test_redact_fold.py::test_variant_1_c_redact_text_lookalike_copy_open_hole - open hole VARIANT-1(c): closed by P2d-2 (a pass here means it is closed: remove this mark)
XFAIL tests/test_redact_fold.py::test_restore_2_a_withheld_line_does_not_restore_a_value_the_input_did_not_hold - open hole L5: closed by the P5c marker (a pass here means it is closed: remove this mark)
1 failed, 8237 passed, 19 skipped, 4 xfailed in 404.87s (0:06:44)
exit=1
```

The one failure of this run, from the same output:

```
E       AssertionError: assert (True is False)
E        +  where True = has_mixed_script('abःcd')
tests/test_textnorm_round1.py:428: AssertionError
```

### The same command with `-rs` on 7d6b5fb (first batch, before commit 6; exit 1; 7 failed, 8227 passed, 19 skipped, 4 xfailed in 299.37s)

```
>       assert found == set(RECORDED_SIBLINGS), sorted(found ^ set(RECORDED_SIBLINGS))
E       AssertionError: ['guard/redact.py']
E       assert {'config.py',.../evidence.py'} == {'config.py',.../evidence.py'}
E         
E         Extra items in the left set:
E         'guard/redact.py'
E         Use -v to get more diff

tests/test_textnorm_siblings.py:312: AssertionError
=========================== short test summary info ============================
SKIPPED [1] tests/test_k2_migrations.py:214: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k2_migrations.py:230: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k2_migrations.py:249: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k2_migrations.py:275: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [2] tests/contracts/kinds/store_postgres.py:24: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k2_migrations.py:357: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k2_migrations.py:374: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k2_migrations.py:387: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k2_migrations.py:430: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k5_postgres.py:36: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k5_round10_postgres.py:33: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k5_round10_postgres.py:52: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k5_round10_postgres.py:72: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k5_round10_postgres.py:113: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k5_round10_postgres.py:118: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k5_round10_postgres.py:137: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k5_round10_postgres.py:145: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
SKIPPED [1] tests/test_k5_round10_postgres.py:153: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
7 failed, 8227 passed, 19 skipped, 4 xfailed in 299.37s (0:04:59)
exit=1
```

Its error lines:

```
E       AssertionError: ['½ cup, mail josé@example.com', 'contact josé@example.com — thanks']
E       AssertionError: assert '[line withhe...ue] <EMAIL_1>' == '½ cup, mail <EMAIL_1> now'
E       Failed: DID NOT RAISE InputTooLarge
E       AssertionError: a module builds its own views: [('redact.py', 'fold'), ('redact.py', 'fold'), ('redact.py', 'fold'), ('redact.py', 'fold'), ('redact.py', 'fold'), ('redact.py', 'fold')]
E       AssertionError: assert (True is False)
E       AssertionError: ['app.py', 'guard/injection.py', 'guard/redact.py', 'guard/runmap.py']
E       AssertionError: ['guard/redact.py']
```

### `uv run --all-extras --group test pytest -q -m perf -p no:cacheprovider -rs tests/test_redact_fold_budget.py tests/test_redact_fold.py tests/test_redact_fold_property.py tests/test_redact_fold_seams.py tests/test_redact_marks.py` (serial, once)

```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
...                                                                      [100%]
3 passed, 113 deselected in 56.21s
exit=0
```

### `uv run --group scan bandit -q -r src/hadavin_sdk/guard -ll`

```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
Installed 22 packages in 47ms
exit=0
```

### `uv run --all-extras --group test ruff check --select TID251 --ignore-noqa src demos tools` (CI step A)

```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
All checks passed!
exit=0
```

### The files of the pytest batch

tests/redact_mutants.py tests/stage_mutants.py tests/test_ci_gitleaks_scope.py tests/test_evidence_decomposed.py tests/test_k1b_cli.py tests/test_k1b_redaction.py tests/test_k1b_redaction_layers.py tests/test_k2_migrations.py tests/test_k3_pilot.py tests/test_k5_classes.py tests/test_k5_fixes1.py tests/test_k5_fixes2.py tests/test_k5_fixes3.py tests/test_k5_fixes4.py tests/test_k5_fixes5.py tests/test_k5_fixes6.py tests/test_k5_fixes7.py tests/test_k5_fixes9.py tests/test_k5_layers.py tests/test_k5_perf.py tests/test_k5_postgres.py tests/test_k5_producers.py tests/test_k5_review.py tests/test_k5_round10.py tests/test_k5_round10_postgres.py tests/test_k5_round11.py tests/test_k5_round12_fuzz.py tests/test_k5_round5.py tests/test_k5_round6.py tests/test_k5_round6_contracts.py tests/test_k5_round7.py tests/test_k5_round8.py tests/test_k5_round9.py tests/test_k5_round9b.py tests/test_k5_tools.py tests/test_lockin_guard.py tests/test_no_hardcoded_values.py tests/test_p5p6_followups.py tests/test_redact_fold.py tests/test_redact_fold_budget.py tests/test_redact_fold_property.py tests/test_redact_fold_seams.py tests/test_redact_g3_port.py tests/test_redact_marks.py tests/test_repo_rules.py tests/test_runmap_partial_escape.py tests/test_s4_llm_guard.py tests/test_stage_names.py tests/test_textnorm.py tests/test_textnorm_app.py tests/test_textnorm_callers.py tests/test_textnorm_differential.py tests/test_textnorm_fixbatch.py tests/test_textnorm_generator.py tests/test_textnorm_meta.py tests/test_textnorm_order137.py tests/test_textnorm_perf.py tests/test_textnorm_round1.py tests/test_textnorm_round2.py tests/test_textnorm_scan.py tests/test_textnorm_siblings.py tests/textnorm_mutants.py
