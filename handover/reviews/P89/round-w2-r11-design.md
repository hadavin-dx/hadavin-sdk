# PR89 round 11, design and security lens, head 025ec61570c98b201aa10de4713072960c6c221a
Verdict: 0 Blocker, 2 Major, 6 Minor. Reviewer ran nothing (no shell); no independent evidence existed yet; sha256 and timings not recomputed; Windows branch, lock-file code and tests/test_mutation_runner.py not read; read the snapshot files and only the first 271 lines of the 4,011-line diff. Saved by the cloud session from the reviewer's inline report (condensed).

## r10-01 and r10-03: FIXED
r10-01: _run_pattern (tools/mutation_runner.py:497-525) over the run view (_run_view 443-445), real encoders via _char_looks (449-454), wired at 589 and 622-628 with widen=False; depth-blind because a print never removes a quote mark. Test keywords:2062-2083 (more than 10,000 cases), mutants 438-441. r10-03: old `!=` pin gone; test 2214-2232 asserts exact outputs; mutant 431. No new way found for a whole secret to reach a log or result row (all output paths go through _masked).

## Major
1. Short head or tail pieces next to `...` are shown unmasked: _edge_patterns (:534) and :614/:617 require at least 6 stripped characters, edges built only for 7 or more kept characters. A 7-character secret can show 5 of its 7 characters when pytest's 12/13-character cut lands inside it. Studio rule: fix, not document; redaction uncapped. Fix (cheap, bounded): next to a literal `...` (at most 1,000 hits) mask any head or tail of 2 or 3 or more characters. If the floor stays at 6, CHANGELOG must say plainly that 5 characters can show.
2. Docs do not match code: _run_pattern (:497-525) has no FRAGMENT_MIN check, so long bases get a redundant run pattern (same as codebase Major 1, BL-core-a2-w2-r11-01); no test or mutant pins the decision.

## Minor
3. An unquoted password holding `'`, `;` or `&` is masked in full only when printed alone; a piece after that character is not a base (docstring 90-92). Cheap fix: add every split piece to the bases.
4. Quote-only claim stronger than test: only bodies up to 3 characters (:2091); only checks no run of 10 or more survives; mutants 443/444 show 10 is the smallest unhidden run but not that nothing shorter leaks.
5. Depth 3-5 tests print the secret alone (_printed_n, :2077), never embedded in a larger text with both quote kinds; mixed bodies (plain letter plus é without a quote) only via `+`.
6. Worst-case perf test does not stress the run pattern (kept = _stripped(value) has no quotes; :2265-2287); _view_with_places is a Python loop over runs; a multi-million-character alternating line is unmeasured.
7. Mutant 350 killed only by switching off the stripped layer (:2126 uses _exact_forms_only); for 7 or more kept characters _fragment_spans is redundant with _edge_patterns in production.
8. CHANGELOG line 11 still one 12 KB bullet with 3 levels of parentheses; split into what is hidden, how printed, how found, what is not covered.

## Design (lead decision, not forced)
Five overlapping mechanisms (exact forms, stripped pattern, run pattern, edge patterns, _fragment_spans); ten review rounds, each found a gap in the last. Simplest rung: refuse instead of mask. run_mutants refuses at start (ValueError, like PASS_ENV_ALLOWED) any value or derived password holding a quote, backslash, control or non-ASCII character, checked after percent-decoding (%27, %C3). Then the secret is plain printable ASCII, a print never changes it, and layers (b), (c), the 6-character floor, quote-run limit, layer-1/2 exact forms and quote-escape mixes are no longer needed; only `...` head/tail pieces and long-word and `+` cases remain. Cost: a throwaway DB with an exotic password is refused (docs already say use a random alphanumeric password). If masking stays, add the len(kept) check in _run_pattern.

## Checked fine
Mutants 438-445 present (builder: 192 of 192 on 3.13; not re-run by reviewer); manifest and CHANGELOG sha entries consistent in the diff (not recomputed); all call sites pass the _SecretSet with bases.
