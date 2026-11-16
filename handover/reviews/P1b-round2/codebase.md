# P1b round 2 - codebase details review (condensed, ids kept)

Reviewer: fresh read-only, no execution. Snapshot: core/P1b-fixwip b0f54b1. Verdict: NOT CLEAN (1 Blocker, 5 Major, Minors).
Nothing was executed by the reviewer; items marked UNVERIFIED were not computed.

- F1 Blocker, CHANGELOG cost entry for Cyrillic/Greek: says the word "пароль" registers fine ("it is accepted"). By the shipped tables the squeeze view is 3 characters and the script view 3 characters, both under the minimum 4, so ViewTooShort (refused) is expected. No test pins the outcome. Fix the sentence or the code and pin the real outcome. Outcome UNVERIFIED (table reading only).
- F2 Major: CHANGELOG says 66.1% of 4 letters with example "Земля" (5 letters). Log: length 4 = 66.1% (e.g. день), length 5 = 35.3% (e.g. Земля). Fix the pairing.
- F3 Major: mutant logs (both Pythons) show 173 of 180 good, rc=1; 2 SURVIVED (scan_holds scripts of the value; runmap invisible characters), 5 WRONG_REASON. No head SHA in the logs; r3 chain outputs absent. No mutant evidence at b0f54b1. Rerun at the final head, SHA on line 1.
- F4 Major: full-suite logs rc=1, 1 failed 11246 passed 1 skipped; the failure is dblink-connect (default socket vs port used). CHANGELOG says one skip but does not name the failing test. Name it or fix (order 133 item 4).
- F5 Major: fail-before logs stale (old head e3f946f / 70eb0f5); 12 new tests pass on old code (fact pins: Latin limit, Hebrew word, mixed value, Cyrillic cost, _script_of, tables digest); many failures are AttributeError on private names. CHANGELOG sentence "each new test fails on the merge 7 code" is false as written. Say which are fact pins; rerun fail-before on the final set with behavioural asserts before private-name access.
- F6 Major: ViewTooShort fires only inside scan_holds/scan_needles; no src code calls scan_holds, scan_needles or scan_keyset (only injection.py scan_views(text, None) and app.py require_pinned_unidata). The refusal is not wired to any product path; "no code in this repository catches it" is true only because nothing calls it. State plainly or add a registration check. (Relates to ORDER 137 D2/D5.)
- F7 Minor: a value like script part plus digits only turns the script part into a needle; a text with only the digits is not flagged. Refuse or state the narrowing.
- F8 Minor: digit minimum 6 has only the 4-digit "99 of 100" figure; add the 6-digit false-hit figure. Table size UNVERIFIED.
- F9 Minor: scan-key cap test uses a lowered cap (13 vs 12) because 16/17 is unreachable; CHANGELOG does not disclose; code comment gives the wrong reason (real: T3 does not depend on the variant, 2x6+1); cap guard has no mutant.
- F10 Minor: CHANGELOG timing ranking wrong (rows 1.28, 1.26, 1.19 s sit between 1.6 and 1.0).
- F11 Minor: test docstrings name killer mutants that do not exist; the digits half of the tables digest pin has no mutant; no mutants for max vs min in _insertion_minimum, _one_off else True, or the cap guard.
- F12 Minor: stale references: (a) fix7 note about the merged-dict line is obsolete; (b) docstring cites a CHANGELOG heading that does not exist; (c) module docstring names the wrong test file; (d) ViewTooShort docstring omits TEXTNORM_MIN_DIGIT_CHARS; (e) test sources contain literal homoglyphs though the header says chr() is used.
- F13 Minor: batch edits CHANGELOG lines owned by P1a (PR 63) and removes review codes; merge-conflict and provenance risk.
- F14 Nit: _text_bundle lru_cache(maxsize=2) keeps the last two scanned texts and views in memory (redaction-sensitive); script view not cached per scripts set so "500 values cost one text pass" is true only for the shared part. (Relates to ORDER 137 R2-09/D7.)
- F15 Minor: Cyrillic refusal rates match the log (94.0, 66.1, 35.3, 13.7, 0 from 7). Greek 100.0/46.4/12.6/2.1 for lengths 3-6 on a small (368,103 characters) non-permissive (CC BY-NC-SA) corpus; disclosed. 0.51% and 1.62% figures UNVERIFIED. (ORDER 137 requires a permissive Greek re-measure.)

Checked fine: callers (scan_views only in injection.py with None; ast test pins src callers); manifest hash for textnorm.py equals CHANGELOG hash (file hash itself UNVERIFIED); mutant arithmetic sums to 180; stage mutants 37/37 both Pythons; perf 43 passed 1 skipped; lint rc=0 (no head SHA in lint log); matcher boundaries traced correct (brute force covers a two-letter alphabet, needles 2 to 6).
Not verified: nothing executed; runmap.composed adds up to three extra NFKC passes on non-ASCII input with no perf test near the cap.
