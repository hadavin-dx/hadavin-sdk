# P1a PR 63 fix5 evidence (lead ORDER 90 FIX5 list, ORDER 89 q192a and q192c)

Base: c05ba58 (fix4) on core/P1a. Nothing is pushed when this file is written; the new head SHA is in the report, not here (a file cannot hold the
hash of the commit that contains the work). Raw logs are in this directory.

## 0. FAILURES AND SLIPS FIRST (brutally honest)

1. **I ran my first full-suite and mutant runs on a tree I was still editing.** I started the heavy jobs, then edited test files under them. I
   killed my own runs (only processes I had started: the `heavy.sh` wrappers and one pytest child of `venv-fix5-313`) and discarded their logs.
   Every number in this file is from a run started AFTER the last code change (the last change was one test, `test_squeeze_views_removes_every_character_that_reads_as_no_ascii_letter_or_digit`).
2. **Mutant list was wrong on its first run: 80 of 90 good.** Ten BAD, all my own spec mistakes, none a product bug: six generator mutants died
   with `KeyError` (a crash, not an assertion), one killer's message did not name the guard (`WRONG_REASON`), and three mutants SURVIVED:
   - `reading (c) has no table of the case-fold image`: the old killer used U+00D8, which the new name rules now read directly, so the test no
     longer reached the case-fold table. Re-pointed to U+0275 (a letter that only the case-fold image table reads as `o`).
   - `squeeze_views keeps non-alphanumeric characters`: the marks-dropped views hid the mutation for Mc, Lm and Sk, so the old killer passed. A new
     test (every code point that `squeeze` reads as nothing, inside "pass...word") kills it. Its first version used a filter that the mutant itself
     changed (wrong reason again); the filter now uses `squeeze`, not `squeeze_views`.
   - `capital does not follow its small letter`: my test built the table from NO data row, so the rule it guards never ran. Now built with the one data row.
   Final: 91 of 91 good (section 3). The fixes changed test code only.
3. **One mutant is EQUIVALENT and I dropped it: "a modifier symbol (Sk) is not dropped".** Removing `Sk` from the set of dropped categories changes no
   result on any code point of Unicode 15.0.0 or 15.1.0: `squeeze_views` strips every non-alphanumeric character anyway, and no Sk code point reads as a
   letter or digit by NFKC or by the table. Sk stays in the set (defensive for a later Unicode version); no test can tell. Replaced by the Mc and the Lm mutants.
4. **Pin test (p1a5-004) cannot be killed by a source mutant when the variable is unset**, and the mutant runner passes an allow-listed environment to
   the child (no `HADAVIN_REQUIRE_PINNED_UNIDATA`). See section 5 for what kills which pin test, and what does not.
5. **Time-stamps:** one early checkpoint line of mine had a wrong clock time; corrected in `checkpoint.md`.
6. **Sweep gaps are not all "closed".** 379 code points whose name or numeric value says one letter or digit are NOT read. They are in four named
   families (section 4), each justified; I did not add a corpus row per gap code point (the raw list is in `sweep-py313.txt`/`sweep-py312.txt`, one line per code point).
7. **`alg` stays `fold4` although the keys of about 345 more characters changed.** No text has been stored under `fold4` (unmerged), so I judged a bump
   unnecessary and said so in the CHANGELOG. This is a decision the lead can reverse in one line (`_ALG`) plus the golden file; confidence medium.
8. **Deviation from the order:** the order spoke of "a reading"; the code adds the marks-dropped counterpart of EACH of the three spelling variants, so a
   scan has up to SIX views (not four). `identity_keys` still has at most three. Stated in the CHANGELOG and both docstrings.
9. The 3.12 numbers come from the same final chain (mutants then suite), started after the last code change.

## 1. Gates (final tree)

Interpreters: each run used its OWN `UV_PROJECT_ENVIRONMENT`: 3.13 = `<build-dir>/venv-fix5-313` (Python 3.13.18, Unicode 15.1.0), 3.12 =
`<build-dir>/venv-fix5-312` (Python 3.12.13, Unicode 15.0.0). Import path: `PYTHONPATH=<worktree>/src` (the venvs hold no editable install of this tree).
ruff 0.17.1 (from the venv); bandit from the older shared venv (not in `venv-fix5-*`).

| Gate | Command | Result | Raw file |
|---|---|---|---|
| ruff check | `ruff check .` | All checks passed, rc 0 | ruff-check.txt |
| ruff format | `ruff format --check .` | 321 files already formatted, rc 0 | ruff-format.txt |
| bandit | `bandit -ll -q -r src tools demos` | rc 0 (only the usual nosec warnings) | bandit.txt |
| repo scan | `python tools/scan_repo.py` | rc 0, no output | scan_repo.txt |
| full suite 3.13 | `heavy.sh python -m pytest -rf --tb=short -p no:cacheprovider -q` | 10294 passed, 455 skipped, 10 xfailed, 0 failed, exit 0 | pytest-py313.txt |
| full suite 3.12 | same | 10294 passed, 455 skipped, 10 xfailed, 0 failed, exit 0 | pytest-py312.txt |
| mutants 3.13 | `heavy.sh python tests/textnorm_mutants.py` | 91 of 91 good, exit 0 | mutants-py313.txt |
| mutants 3.12 | same | 91 of 91 good, exit 0 | mutants-py312.txt |
| hygiene | the repo hygiene grep (placeholders, home paths, model ids, build dirs) over every added line of the diff | 0 matches | hygiene.txt |

ruff and bandit were run before the final one-test edit; I re-ran `ruff check` and `ruff format --check` after it (clean, rc 0; the pre-commit re-run is in ruff-*.txt).
Postgres tests SKIP without `HADAVIN_TEST_PG_DSN` (455 skipped on each interpreter are those); I did not run them and no Postgres gate is claimed.
Before fix5: 10113 passed, 5 xfailed (fix4). Now +181 passed, +5 xfailed (the strict `could_be_same_person` rows: r114 to r117 plus the fifth p1b row r085).

## 2. Items

### p1a5-002 letters and digits (item 1)
- Generator (`tools/gen_confusables.py`): name rules for negative circled/squared Latin capital letters, crossed negative squared P, squared small letters,
  regional indicator letters, small capitals with a mark, `LATIN ... LETTER X WITH ...`, and circled/negative circled/double circled/sans-serif digits and numbers.
  Table 507 to 852 entries. Rebuild is offline from `tools/data/confusables.txt` plus the interpreter's `unicodedata` names (generate on 3.13; 3.12 gives the same table except the header line).
  Test: `test_the_generator_reproduces_the_checked_in_table_offline` (passes).
- SWEEP: `sweep-py313.txt` and `sweep-py312.txt`, raw: 2251 code points, 1872 read, 379 unread; unread by family
  {G1 dropped on purpose 113, G2 numeral of another script 261, G3 turned digit 2, G4 read as another letter by UTS #39 3}. Identical on 3.12 and 3.13. Every unread row names its family; a code point in no family fails
  `test_every_code_point_whose_name_says_one_ascii_letter_or_digit_is_read_as_it_or_is_in_a_named_gap_family`.
  The 3 G4 rows are U+01B2, U+028B, U+1D8C (UTS #39 reads them as `u`/`y`).
- Corpus rows r182 to r191 (classes "letters written as symbols" and "digits written as symbols"); family tests:
  `test_negative_circled_negative_squared_and_regional_indicator_letters_read_as_their_letter`, `test_circled_negative_circled_double_circled_and_sans_serif_digits_read_as_their_digit`,
  `test_latin_letters_with_a_stroke_hook_bar_or_tail_read_as_their_letter_in_the_case_of_the_name`.

### p1a5-001 Mc, Lm, Sk (item 2)
- `squeeze_views` has the views built from the RAW text with every Mc, Lm, Sk dropped before NFKD/NFKC/table. Test
  `test_squeeze_views_finds_a_secret_hidden_with_every_spacing_mark_modifier_letter_or_modifier_symbol` runs every Mc, Lm, Sk code point, NO exemption list.
  Size and weight: `test_the_marks_dropped_views_are_at_most_six_and_keep_every_script_and_letter`, `test_the_marks_dropped_views_are_never_longer_than_the_weight_of_the_text` (every code point); perf row
  `test_a_text_at_the_cap_with_spacing_marks_is_scanned_in_linear_time_with_the_marks_dropped_views` (text at the cap, about 1 s on this machine, ceiling 5 s).

### p1a5-003 fold_views (item 3)
- `fold_views` has the same marks-dropped views (scripts kept). Test `test_a_value_with_no_ascii_letter_or_digit_is_found_by_the_fold_views_scan_when_a_mark_is_inserted`
  (Devanagari + U+0903, Chinese + U+02C6, Thai + U+0E48, Thai + U+02C6, each found by the two-view scan). The Thai tone mark U+0E48 is Mn and was already found on old code (a pin); the other three fail on old code (section 6).
- Docstring sentence (in `fold_views` and in the module docstring "WHAT A SCAN RELIES ON"), the SAME sentence for P1b-notes item 2:
  "A value with NO ASCII letter or digit (Chinese, Arabic, Hindi, Thai) is scanned with `fold_views` alone: `squeeze_views` is empty for it, so the marks-dropped views here are the ones that find it when a mark is inserted; an inserted look-alike letter of that script is not covered."
- `could_be_same_person` did not change behaviour: all its tests pass (full suite, section 1); the differential test for it now runs on EVERY `equal` corpus row (new test, section 2 p1a5-005).

### p1a5-004 pin test (item 4)
- `test_the_interpreter_is_on_the_pinned_unicode_version_when_the_run_requires_it` fails when `unicodedata.unidata_version != defaults.TEXTNORM_PINNED_UNIDATA` and `HADAVIN_REQUIRE_PINNED_UNIDATA=1`; passes without the variable.
  Shown on 3.12: with the variable it FAILS, without it PASSES (`pin-test-312.txt`); on 3.13 both pass. Companion tests: `test_the_pin_check_fails_only_when_required_and_off_the_pin`, `test_the_pin_constant_is_the_version_of_the_vendored_table_and_of_the_golden_file`.
- PR body wording: "Until P1b merges (`require_pinned_unidata()` called in `app.build`), the CI variable `HADAVIN_REQUIRE_PINNED_UNIDATA=1` (in the lead's ci.yml) is the only enforcement; this PR adds the test, not the CI line."
  I did NOT touch ci.yml and cannot see that the variable is set there.

### p1a5-005 docstrings, docs, provenance (item 5)
- `could_be_same_person` docstring: Mn/Me and invisible characters; the Mc/Lm/Sk limit; the punctuation limit (O'Brien vs the curly apostrophe, a Unicode hyphen vs "-"); rows r114 to r117.
  New test `test_could_be_same_person_agrees_with_the_stated_principle_for_every_equal_row`: the p1b rows r114 to r117 are strict `xfail` with `raises=AssertionError` (they xfail; none XPASS).
- Internal codes (order 79, review 4, fix3, BN-18, D146, fold4) removed from the public docstrings (grep of `textnorm.py`: only `_ALG = "fold4"`, a value). "same person" reworded to "may be the same person".
- `UnidataMismatch` duplicate sentence fixed. `THIRD-PARTY-NOTICES.md` quotes the exact header line `# © 2023 Unicode®, Inc.`.
- `gen_confusables.py` provenance: one statement (fetched by the lead on 2026-11-06 from the Unicode site, 718,291 bytes; checking the upstream sha256 needs network access; other copies are "said to" hold the same bytes and this package does not check them).
- CHANGELOG sentence now lists `FILLERS` (the 20th name; the earlier list named 19). The BN-20 text in the ticket already says "20"; `reviews/p1a-fix4/erratum.md` numbers 19 names (no FILLERS): that file is under the handover folder, which I must not edit, so the lead should add `FILLERS`.
- `tests/test_k5_round9.py:239` writes U+2060 as the escape `"⁠"` (82 tests of the file pass).
- Trigger for a vendored UCD (the one line; in the module docstring, the repo has no `docs/designs` file for this package): "A vendored copy of the Unicode character data ... becomes the alternative when a deployment must run a Python whose Unicode version is not the pin and cannot be changed."

### P1b-notes additions (text for the lead; I cannot edit the handover file)
1. Item 2 sentence: the one in p1a5-003 above.
2. Pin-call test in `app.build`: a test that `app.build` calls `require_pinned_unidata()` (a mutant that removes the call must fail it) and that a Python whose Unicode version is not 15.1.0 stops start-up in pilot and prod. P1a has no caller.
3. BN-18: names assigned after Unicode 15.1 (category `Cn` on the pinned interpreter) are DROPPED by the fold; a name rule or a table entry for a character added after 15.1 cannot take effect on 3.13.x until the pin moves (a data migration, not a version bump).
4. F3 decision (injection detector does not fold): needs a lead decision in P2d or P1b: either fold before the regex or record the ledger row; P1a does not touch `guard/injection.py`.

## 3. Mutants (91: 77 earlier + 14 new)
Runs: `mutants-py313.txt` (91 of 91 good), `mutants-py312.txt` (91 of 91 good, exit 0). Each "KILLED" line shows the killer test; the runner checks that the failing test is the pinned one and that the first failing line holds the `expect` fragment of an assertion MESSAGE (so an ImportError cannot count). New mutants and killers:

| Mutant | Killer (assertion-level) |
|---|---|
| marks: the marks-dropped reading is not built | `test_squeeze_views_finds_a_secret_hidden_with_every_spacing_mark_modifier_letter_or_modifier_symbol` |
| marks: dropped after NFKD, not from the raw text | same |
| marks: squeeze_views has no marks-dropped views | same |
| marks: Mc not dropped / Lm not dropped | same |
| marks: fold_views has no marks-dropped views | `test_a_value_with_no_ascii_letter_or_digit_is_found_by_the_fold_views_scan_when_a_mark_is_inserted` |
| marks: a view is repeated | `test_the_marks_dropped_views_are_at_most_six_and_keep_every_script_and_letter` |
| marks: squeeze_views keeps non-alphanumeric characters (re-pointed) | `test_squeeze_views_removes_every_character_that_reads_as_no_ascii_letter_or_digit` |
| names: negative circled/squared; regional; squared small; circled digits; WITH letters; capital follows partner (6) | `test_the_name_rules_of_the_generator_read_the_letter_and_digit_forms` |
| pin: the pin constant differs from the data of the table | `test_no_table_source_is_in_a_dropped_category` |

Also repaired: "reading (c) has no table of the case-fold image" (killer re-pointed, section 0.2), "table: small capital rule missing" (search string re-pointed to the name-rule loop).

## 4. q192a: per pin test, the mutant that kills it
| Pin test | Killing mutant | Note |
|---|---|---|
| `test_the_pin_constant_is_the_version_of_the_vendored_table_and_of_the_golden_file` | defaults pin constant changed (hand run, `pin-test-mutant-constant.txt`; the runner mutant "pin: the pin constant differs" is killed by `test_no_table_source_is_in_a_dropped_category`, not by this test) | the runner cannot list this test as a killer: the differential file is not a killer file by the meta rule |
| `test_the_interpreter_is_on_the_pinned_unicode_version_when_the_run_requires_it` | hand mutant: pin constant 15.0.0 with `HADAVIN_REQUIRE_PINNED_UNIDATA=1` on 3.13: FAILS; without the variable it PASSES (`pin-test-mutant-constant.txt`) | cannot be killed in the runner (no env var in the child); it asserts nothing when the variable is unset, by design |
| `test_the_pin_check_fails_only_when_required_and_off_the_pin` | hand mutant of the TEST helper (`!=` to `==`), `pin-helper-mutant.txt` | tests test code; no source mutant can touch it |
| the weight-cap test, the perf row, the sweep, the three family tests (T file) | none in the runner | killed only by "new tests on old code" (section 6); the generator-rule mutants are killed by the generator test, because the committed table is not regenerated inside a mutant tree |

## 5. Ledger rows p1a-005 and p1a-007 (ORDER 89 d)
I could NOT find the ledger rows. `handover/reviews/p1a-round3/` holds only `review-3-codebase.md`, `review-3-design.md`, two probe scripts and two probe outputs; no file in the handover folder contains the id "p1a-005" or "p1a-007" as a row (`grep -rn` over the folder: only the fix3 finding map, which says the same, and `review-4-code.md`, which says "p1a-007 row text unreadable"). I therefore cannot answer the rows as written. The nearest findings and their state at fix5:
- codebase F5 (punctuation limit not named in the docstring/changelog; rows r085, r114 to r117): FIXED in fix5 (docstring sentence, strict `could_be_same_person` xfail rows, CHANGELOG sentence).
- codebase F7 (table provenance, generator needs Python 3.13): FIXED in fix4/fix5 (15.1.0 data vendored; generator provenance now one statement; table rebuild offline).
If p1a-005 and p1a-007 are other findings, the lead needs to paste the two rows.

## 6. Fail-before (new tests on the c05ba58 src)
`fail-before-new-tests-on-c05ba58.txt`: the new tests of this tree against the fix4 `src` (tools and tests new): 29 failed, 160 passed in the selection. Failing on old code: the Mc/Lm/Sk all-code-points test, the six-view test, the Mc-kept test, the Devanagari/Chinese test, the sweep, the three family tests, the perf marks row, and the 20 corpus rows r182 to r191 (identity_key and could_be_same_person). PASSING on old code (so they are pins, not fail-before): the generator name-rules test (it reads the NEW generator), the three pin tests, the weight-cap test.

## 7. What I did NOT run
- Postgres tests (no `HADAVIN_TEST_PG_DSN`); 455 skips on each interpreter.
- Windows; Python 3.14; a wheel-install check.
- The upstream sha256 check of `confusables.txt` (no network by rule; the lead said they would).
- CI (I did not touch ci.yml; I cannot see that the lead's `HADAVIN_REQUIRE_PINNED_UNIDATA=1` is set there).
- gitleaks (not installed here).
- Mutants against the reviewer's own probes; no `alg` bump test.
- The answers for p1a-005 and p1a-007 as ledger rows (not found, section 5).

## 8. CodeRabbit Major on textnorm.py:173 (ORDER 95): NOT real on this head
`coderabbit-case-pair.txt`: for the cited input U+0460 U+0415 U+0412, `identity_keys` = ['web'], `squeeze` = WEB, `squeeze_views` = ('WEB',), `could_be_same_person(., 'web')` and `(., 'WEB')` both True (reading (c) of fold4 and the table-after-casefold step already do what the comment asks). The raw "case-pair gap" the comment counts is real as a set (72 characters not in the table whose case-fold is) but every one of them is read by `identity_keys` and `squeeze_views` except U+0345, the combining iota, dropped by design. The thread is already marked resolved/outdated by the reviewer ("addressed in commits afdb4bc to 5693d79"). No code change; I added no test for it (a new test would have made the final runs stale); the output file is the evidence.

## 9. Head
The final tree equals commit 5693d79 (committed with the message "WIP, finals still running" at the lead's request, before the 3.12 finals ended; no tracked file changed afterwards, `git status` clean). No second push is needed.

## 10. Merge of origin/main (13ebfaf) and the CodeRabbit case-handling note
Merged head 2572847ee58681988a8e845906ecf2b90c5c4bca (plain merge, no conflict, pushed fast-forward from 5693d79). Main changed 32 files; overlap with my files: CHANGELOG.md only (merged cleanly, manifest hashes still present); guard/redact.py and defaults.py came from main. On the merged head: ruff check and format clean; targeted tests (textnorm, generator, differential, meta, perf, third-party notices, stage names, k5_round9) 818 passed, 10 xfailed on 3.13 and on 3.12 (merge-targeted.txt). Full suites, gitleaks, Postgres, Windows, CI not rerun.
CodeRabbit "case-handling inconsistency": coderabbit-case-mixed.txt, 20 mixed-case confusable pairs, both argument orders and identity_keys intersection: all agree, no asymmetry. Not reproduced.
