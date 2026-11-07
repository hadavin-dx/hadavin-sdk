# PR 70 (P1b, head 4f14ec8) code review 1 (fresh read-only reviewer, diff from P1a 2ff0afe)

Saved verbatim apart from path scrubbing. The reviewer ran nothing (Read/Grep/Glob only) and relied on the merge6 evidence (10778 passed / 455 skipped on 3.13 and 3.12, 118/118 textnorm mutants, 37/37 stage mutants). No Postgres run was read. The diff also holds main-merge content (migration_numbers, timing fixtures, stage guard) that is not P1b work and was not reviewed. Design file read to line 70 of 243 only.

## BLOCKER
B1. `could_be_same_person` docstring (textnorm.py ~683-688) is stale: it says punctuation is not folded and that O'Brien vs O+U+2019+Brien and U+2010 vs "-" compare as different, citing strict expected failures r114-r117. P1b gap 4 makes them equal and flips r114-r117 to `current`; no hunk touches the docstring. Fix: reword.

## MAJOR
M1. `runmap.canonical` composes nothing now (runmap.py 276-285, via per-character NFKC in `_canonical_view`). Before, whole-text NFKC composed e+U+0301 to the precomposed form. Stage 2 of `redact_text` scans `canonical(text)`; redact.py has no normalisation of its own. Scenario: map holds "José Müller" (NFC), a tool result writes it decomposed; stage 2 no longer composes, the literal sweep misses, the name reaches the model. Same for Hangul conjoining jamo. The new test pins the loss (`canonical("á") == "á"`) and the CHANGELOG calls it a KNOWN GAP; no test covers a stored precomposed value written decomposed. `undo()` rounds also lose composition. Better fix: compose per starter+marks cluster inside `_canonical_view` keeping the index back. Add a fail-before test for the NFD copy. Redaction path, no round cap; needs a lead decision (order 81 / q178 chose the per-character form) or a fix.
M2. `scan_holds` ignores per-view minimum lengths (`_all_views`). A value "a" or "ok" matches any text containing it. Docs call it the one scan for redaction/blocklist/has-secret; the CHANGELOG says the redactor should use `scan_needles`, so the two scans disagree on what a needle is. Under fix7 route through `scan_needles` rules (`ViewTooShort`, per-kind minimums).
M3. `EmptyView` makes `scan_holds` unusable for any value with no ASCII letter or digit (Chinese, Arabic, Thai) although `scan_keyset` keys them and fix6/fix7 scan them through script views. Decide with the lead: keep `EmptyView` only for an empty/invisible value (`ViewTooShort` covers that) or drop it.
M4. `scan_holds(text, value)` rebuilds all views of the text for every value (uncached `_all_views`, no way to pass precomputed text views). Scanning a 262k-char result against a 500-entry map is 500 full view builds. Not on the P2d-2 `check_lookalike` path (it calls `scan_keyset`), but a redactor following the docstring pays it. Add a `text_views` parameter or document few-values-only.
M5. Spec drift from P1.md not flagged in the PR body. (a) P1.md says `same_person = identity_key equality or _scan_match`, with `allow_equal("Li Na","Lina")` returning LOOKALIKE; the PR leaves `could_be_same_person` unwidened, so it returns DIFFERENT; the only Li Na/Lina test is `shares()` on `scan_keyset`. (b) P1.md says P1b adds exactly `FoldNotConverged` and `scan_keyset` (19 names) and that `scan_holds`, `scan_views`, `EmptyView` belong to the cut needle API; the PR ships 27 public names. Possibly covered by a later order the reviewer did not read: confirm or flag.

## MINOR
m1. `defaults.TEXTNORM_MAX_PASSES` unvalidated (float 3.0 makes `range()` raise TypeError, not a TextnormError; 0 or negative makes every scan raise `FoldNotConverged`). Apply the int>=1 validation fix7 uses.
m2. Generator docstring contradicts itself and the CHANGELOG (re-adds "REGENERATION LIMIT" while the CHANGELOG says it is gone in fix4 and the same docstring says no interpreter filter).
m3. `_build_punct_table` / `_build_digit_table` scan 1.1M code points at import using the interpreter's Pd set; `has_mixed_script` uses vendored data. A Python pin move would change keys silently except through the golden hash. Prefer vendored data or a fixed list.
m4. `injection.py` `_score`: non-ASCII benign text with weight above 262,144 now raises `TextTooLong` which becomes a `guard_unavailable` flag; 20+ views per text on every document and tool result. Stated in CHANGELOG and listed NEEDS LEAD in q-for-lead (open, not hidden).
m5. Two script systems after the fix7 merge: P1b `_scripts.py` (Scripts.txt, used by `has_mixed_script`) and fix7 `_script_of` (first word of the character name). They disagree on grouping (Han/kana, UNNAMED, IDEOGRAPHIC). Breaks reuse-before-writing; two answers to "what script is this letter".

## NIT
n1. `tests/fixtures/textnorm_golden.json` "note" has duplicated garbled text.
n2. CHANGELOG still says built on fix6 (2ff0afe); sha256 pins, "27 names", "23 views" and mutant totals change with fix7.
n3. `tests/test_textnorm_app.py` second test ends with `except Exception: pass` so it can only fail on `UnidataMismatch`.
n4. `app.build` guards only `is_live` stages; P1.md gives client-profile wiring to P6a, CHANGELOG says P1b wires it: two tickets claim it.

## Checked and found sound
`scan_keyset` follows SK-1..SK-6 (Lm removal first, tag texts T0-T3, passes A and B to a fixed point, z->3 and l->i maps, isalnum and not-Lm drop, no empty key). No off-by-one in `_converge` (at most 3 calls, raises on a change at the third). `_kept`, the iota rule and gap 4 behave as ticketed; golden `squeeze` hashes unchanged. Generator pins version, date and sha256 for Scripts.txt; `.gitattributes -text` set. `has_mixed_script` Script-property change coherent. 3.13 and 3.12 exit 0; 118/118 mutants killed.

## What must change for the fix7 API (merge7)
1. defaults.py: delete `TEXTNORM_MIN_VIEW_CHARS`, keep fix7's four minimums (spelling 2, squeeze 4, script 4, ideograph 2), keep `TEXTNORM_MAX_PASSES` with validation (m1); resolve the adjacent-line conflict.
2. `_all_views` calls `_views(..., script=True)`; fix7 `_views` takes `scripts: frozenset[str]` (default empty) so this is a TypeError on first call. `_all_views` and `scan_views` need a `scripts` argument; `scan_holds` must call `_all_views(text, scripts=_value_scripts(value))`, same for the needle side.
3. Replace P1b's one-argument `_script_view(view)` with fix7's `_script_view(view, scripts)`.
4. `scan_views(raw)` without a value has no script views unless given `scripts`: doc counts 6+6+8=20 without, 9+6+8=23 with. Injection needs none.
5. `scan_holds`: build needles from `scan_needles(value)` (per-kind minimums, `ViewTooShort`) plus the value's `scan_keyset` keys with an explicit minimum; decide `EmptyView` (M3).
6. Drop references to `TEXTNORM_MIN_VIEW_CHARS` in the CHANGELOG and module docstring.
7. `__all__` becomes 28 with `value_scripts`; fix the "exactly the listed twenty-seven" test and CHANGELOG count.
8. Regenerate `tests/fixtures/textnorm_golden.json` (`fold_views` no longer includes script views by default); recompute manifest sha256 pins, CHANGELOG re-copy list, mutant counts. fix7 mutants plus P1b's 22 must still be killed.
9. `has_mixed_script`: pick one script source (m5).
10. `test_textnorm_scan.py` and `test_textnorm_siblings.py` rows calling `fold_views` or `scan_holds` with scripts or Chinese values need updating (EmptyView expectations).

Key files (snapshot): src/hadavin_sdk/guard/textnorm.py, guard/runmap.py (276-298), guard/injection.py, tests/test_textnorm_siblings.py (69-80), tests/fixtures/textnorm_golden.json; fix7 API in the P1a tree textnorm.py 460-731.
