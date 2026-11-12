# PR H batch 7 (resume): builder notes (REDACTION path, no round cap)

Two builders worked on this batch. The first ran out of its 90 minutes with nothing committed. The second (this record, started 2026-11-12 04:57 UTC, 10:27 IST) took over the uncommitted tree at base c802cc0f, fixed what failed, and committed. This is the builder's own record, not independent evidence: the evidence runner and the `egm:*` reviewers judge the head.

## What failed, was uncertain or was not checked (read first)

- On takeover 22 existing redaction tests failed and no mutant 82 to 95 had ever been shown killed. All 22 are fixed (causes below) and the redaction test files now pass: `2543 passed` (the `test_prh_*` files except perf, plus `test_k5_fixes3.py`), exit 0.
- Seven mutants survived my first runs (83, 86, 87, 88, 90, 95, 100). Six now have a killer test that fails on the mutated code (checked one by one). Mutant 100 could not be killed because the code it removes is redundant: after the other fixes the decoded readings already carry no ignorable characters. I proved it on 7000 texts (3000 fuzz texts, 4000 texts with percent, entity and JSON escapes) with identical output with and without that code, then removed the code and the mutant. Mutant 90 as written (guard is ESC only) is equivalent too (9000 texts with the 8-bit openers, identical output); it is re-pointed to "the direct `redact()` never reads the consuming reading", which a new test kills.
- The "withheld" figure is higher than main on hostile mixes: 143 of 3000 texts (4.8 percent) are withheld on the final tree against 0 on main (main leaks instead: 1408 texts show an 8-character stretch of a secret). See the Issue 10 table. This is a real availability cost on texts that mix secrets with hidden characters; ordinary text is never withheld (clean corpus: 0 of 60 runs).
- Issue 9 (a secret written with a space between each character is not masked) is NOT fixed. It needs an owner decision (it can hide ordinary text); the question is `q-prh-spaced-secrets` in `handover/questions-for-lead.md`; SECURITY.md and CHANGELOG say so; three rows are pinned. This is exception (b), needs the owner.
- Not run by me (impossible here): Python 3.12 and the CI-only jobs (CodeQL, SonarCloud, CodeRabbit). EGM result review, resolve and drift report are the lead's step; I cannot invoke those agents from here.
- The gate record at the end of this file says which gates ran on which head.

## Causes of the 22 failures, and the fix at the shared place

| Class | Where fixed |
|---|---|
| A spy in the wiring test did not pass the new `readings` argument through | `tests/test_prh_wiring.py` |
| Test harness named the redactor class by its own name, not its parents' names | `tests/test_prh_regressions.py`, `tests/record_prh_main.py` (names from the class chain) |
| A later reading overwrote the "(details withheld)" answer of the first reading | `redact.py` `find`: a withheld first reading ends the search |
| The consuming reading kept a bell (BEL) the sequence reader had not removed | `redact.py`: consuming reading is read on the text with ignorable characters out |
| The folding rule demanded equal sets, so one reading that masks more was refused | `redact.py` `compare_readings`: coverage rule, "same", "first", "second" or "conflict"; shared with `runmap._consuming_wins` |
| A CJK stretch in the piece unit test | `tests/test_prh_tools.py` |

## Resume-brief item: U+0090, U+009D, U+009E, U+009F in the direct `redact()` (`AKIAIOSF` stayed readable)

Class: a string sequence (OSC, DCS, SOS, PM, APC) that no terminator closes swallows the rest of the line in the grammar reading, so a key cut by it shows only its front. Fix at the choke point (`_Redactor.find`): `hidden.has_open_string(text)` says whether such a sequence is open; only then the character reading (every hidden character deleted on its own) is computed, and only as a CHECK: if only that reading can see a value, the result is the withheld note; the character reading is never shown. First attempt (using it as a result) leaked text of the unterminated sequence in 24 accidental pairs and withheld ordinary coloured secrets; the check-only form fixes both (accidental fixture: 8 `[direct]` rows moved out, 73 left).

## Issue 10: withheld share on the fixed fuzz (seed 20261112, 3000 texts), by tree

| Tree | Exceptions | Texts with an 8-character stretch of a secret showing | Strict withheld (the note or marker only) | Cause of the strict withheld | "Only placeholders" count (independent runner's measure) |
|---|---|---|---|---|---|
| main | 0 | 1408 | 0 (0.0%) | none | 47 |
| c802cc0f (batch 6 head) | 7 (`InputTooLarge`) | 548 | 102 (3.4%) | piece check 88, readings 14 | 226 |
| final tree (this head) | 0 | 0 | 143 (4.8%) | readings or other 92, piece check 44, work limit 7 | 527 |

Plain reading of the table: the final tree never shows a stretch of a secret and never raises. It withholds 4.8 percent of this hostile mix (every text mixes secrets with escape characters on purpose). The "only placeholders" column counts texts whose whole output is placeholders and spaces; 583 of them are texts made only of secrets (correctly fully masked), so that column is not a withheld count. Clean corpus (`handover/evidence/PRH/b7/clean_corpus.py`, 15 texts, 60 runs): withheld or wrong 0.

Reproduce: `PYTHONPATH=src python handover/evidence/PRH/b7/fuzz_classify.py 3000` (do not use `-I`, it ignores PYTHONPATH).

## Issue 14: new tests that PASS on the old code c802cc0f (46 of 95), one line each

Fail-before output: `handover/evidence/PRH/b7/fail-before-c802cc0f.txt` (49 of 95 fail on c802cc0f).

| Test (count) | Why it passes on c802cc0f | Guarded by |
|---|---|---|
| `i1_encoded_escape_and_encoded_first_letter` (21 of 30 rows) | control rows (the old builder's note: encodings the old code already handled; I did not trace each row) | the 9 rows that fail; mutants 82 to 85 |
| `i4_a_cut_copy_beside_a_masked_copy_is_not_left` | the old tree lacks the code path that mutant 86 removes; the row needs the new tests to guard it (reason from the old builder's note, not traced by me) | mutant 86 (and the new `mutant_86` test) |
| `i5_a_key_cut_by_an_opener_never_shows_its_tail` (5) | tail check only; old code also hid the tail | pin |
| `i5_a_known_value_cut_by_any_opener_is_withheld` (4) | old code withheld these openers too | pin; mutant 91 |
| `i5_a_string_opener_ended_by_a_bell...` (6) | the rows that end with a line break are expected to break the key | pin; mutant 98 for the bell rows |
| `i5_a_key_cut_by_tput_sgr0...` | the old direct `redact()` already read the consuming reading | mutant 90 |
| `i8_d6_a_combining_mark_is_not_a_hidden_item` | decision d6, documented behaviour | pin |
| `i8_plain_text_with_a_zero_width_joiner_is_unchanged` | control (no over-withholding) | pin |
| `i9_spaced_out_secret_is_documented_behaviour` | Issue 9 is a documented limit (owner question) | pin |
| `i10_a_key_cut_by_an_ignorable_character...` | passes on c802cc0f; reason not traced; it fails when the ignorable-character handling of mutant 99 is removed | pin; mutant 99 |
| `i10_the_clean_corpus_is_never_withheld` | the old code did not withhold clean text either (a control, not traced further) | pin (guards the new code) |
| `i12_h2_fixed_row...` and `i12_mutant_95...` (3 rows) | passes on c802cc0f; reason not traced; the new tree's fragment cut is guarded by mutant 95 and its own killer test | mutant 95 |

## Other observations

- A mangled marker can remain in a result that was cut inside a string sequence (cosmetic: the result still shows no stretch of a secret).
- Hostile cases that fail closed (withheld note) are intended: two readings that mask different values, a value only the character reading can see, and a remnant of a masked value beside another copy.
- Issue 12: the docstring says 14 passes (the worst row in the pass-count test); the CHANGELOG states `piece_min` (4 to 32, default 6) as the stretch width. Both checked against the code.
- Decision d6: U+0301 is not a hidden item; pinned.

## Equivalence evidence for the removed mutant 100 (and the old form of mutant 90)

Command (from the repo root): `PYTHONPATH=src python handover/evidence/PRH/b7/equivalence_100.py` (exit 0). Output, saved in `equivalence_100.out`:

`texts 7000 | outputs differing with the extra view 0`

It runs the tool path (`prepare_output`) and the error path (`error_reason`) on 7000 texts (the 3000 fuzz texts, plus 4000 texts with a secret cut by an ignorable character and written in plain, percent, entity or JSON form), once with the code mutant 100 removes and once without it, and compares both outputs per text. The script is the reviewer's check; to re-test, put the line back and run it. The same check for the old form of mutant 90 (`has_seq` only for ESC) gave 0 differing outputs in 9000 direct `redact()` texts with the 8-bit string openers (script kept in the scratchpad, not committed: the replacement mutant 90 and its killer test are what the repository keeps).
