# Notes for the P1b builder (from P1a fix4, orders 79 items 3, 5, 6)

Merge P1a fix4 first, then do these. Nothing here is done in P1a.

## 1. The Mc / Lm / Sk corpus for the sibling-paths test

Add to the P1b sibling-paths test (the test that puts a hidden-character between the letters of a secret and runs every scan path):
EVERY code point of the three general categories, taken from the interpreter's Unicode data (not a hand list), inserted as `"pass" + c + "word"`.
Counts on Unicode 15.1.0 (Python 3.13) and also on 15.0.0 (Python 3.12), measured: Mc 452, Lm 397, Sk 125.
Expected result for each, in the P1a test `test_squeeze_views_finds_a_secret_hidden_with_any_spacing_mark_modifier_letter_or_modifier_symbol`:
- `squeeze_views(...)` holds `PASSWORD` for every code point except the ones that are themselves read as a letter or digit. The exception list
  is derived from the data (NFKC form holds an ASCII letter or digit, or the character or its NFKC form is a table source); on 15.1.0 it is 5 of
  Mc (U+0B03, U+0C02, U+0C82, U+0D02, U+0D82, anusvaras and a visarga that the table reads as `o` or `8`), 140 of Lm (the superscript and
  modifier letters, for example U+02B0) and none of Sk. For the excepted ones the view must hold `PASS` + the letter + `WORD`.
- `fold_views(..., casefold=True)` does NOT hold `password` for any Mc (decision kept: Mc is kept by `fold`). So a scan that reads only
  `fold_views` misses a secret hidden with a spacing mark.
Reuse `_code_points_of` and `_reads_as_letters` from `tests/test_textnorm.py` (or copy them).

## 2. Redaction MUST scan BOTH views

A redaction or blocklist scan must look through `fold_views` AND `squeeze_views` and match when ANY view of the text holds ANY view of the
protected value. `fold_views` alone is not safe (Mc stays in it); `squeeze_views` alone is not safe for the other direction. The P1a module
docstring says so (section "MARKS AND SCANS"); put it in P1b's BN-18 list and test it on every scan path.

## 3. P1b must refuse an empty view

`squeeze`, `squeeze_views` (and a fold of a text that is all dropped characters) return `""` for a text with no ASCII letter or digit. An empty
string is a substring of every text, so an empty protected value or an empty view of the value would match everything (or, if skipped, match
nothing). P1b must refuse an empty view (raise, or skip with an audit event; the ticket decides which) and have a test for it.

## 4. P1b enforces the pinned Unicode in `app.build`

P1a ships `require_pinned_unidata()` and calls it nowhere. P1b calls it in `app.build` for production and pilot (Python 3.13.x, Unicode 15.1.0).
A demo may run on Python 3.12 and then gets check names that start with the tag from `key_tag()`. The warn-only `check_pinned_unidata` is deleted.
The message of `UnidataMismatch` already says "run Python 3.13 (Unicode 15.1.0) for pilot or prod".

## 5. P1b renames `same_person` after merging fix4

After merging fix4: rename `same_person` to `could_be_same_person` in P1b code, tests (`tests/test_textnorm_scan.py`, `textnorm_mutants.py`,
`test_textnorm.py`), the CHANGELOG and docs; stop using `fold_key` (use `identity_key`); drop the duplicate vendored confusables file and the
interpreter filter (P1b had its own 15.1.0 copy; fix4 vendors the same file); use the words "spelling variants" and "check name".
The `core/P1b` branch at the time of writing still names `same_person` and `fold_key` in its tests and mutants (read with `git show`).
