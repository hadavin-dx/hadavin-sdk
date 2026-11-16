# PR89 round 5 review (redaction path) - head 386875c, reviewer egm-codebase-details

Verdict: 0 Blockers, 0 Majors, 6 Minors (m1 to m6), 2 Nits. The reviewer could not run code or hash files; all masking conclusions come from reading the code.

## Round-4 minors re-checked
- M1 main-runner evidence: FIXED (sha256 and commit in CHANGELOG, docstring and collection-error-old-row.txt; hash not recomputed by reviewer).
- M2 "-q -vv" wording: FIXED (limited to what was observed with pytest 9.2.0).
- M3 handover paths in copied files: FIXED for new text. Older text at CHANGELOG.md:386 and tests/test_mutation_runner_keywords.py:1420 still cites handover/reviews (pre-existing).
- M4 lock file: PARTLY FIXED (O_NOFOLLOW and 0600 added; file never deleted, no private folder; documented).
- M5 fragment-span cost: FIXED (MAX_FRAGMENT_HITS 10,000 plus find window).
- M6 unmasked forms listed: FIXED (JSON and bytes forms added; list in CHANGELOG.md:8).
- Nits (CanaryFailed sentence, -1000/-1001 as words): FIXED.

## New findings
- m1 (real leak path): mixed quote kinds. Python repr of a larger string picks its quote from the whole string. A value containing a single quote but no double quote, printed inside a string that also holds a double quote elsewhere, appears with the escaped form that is in no form set (tools/mutation_runner.py:296-308). Property test never adds a double quote elsewhere. Fix: add the forms with the quote escaped to `_written_forms` and extend the property test.
- m2: libpq backslash escapes (password='it\'s', password=ab\ cd) and URL passwords with unencoded slash, question mark or hash are not read by the password regex or urlsplit (:291-293, :320-324). The whole value stays masked.
- m3: a 1 to 2 character secret on a huge line costs millions of loop iterations in `_masked` (:373-377). Slowdown, not a leak.
- m4: CHANGELOG.md:8 and runner docstring :64-67 do not list: mixed-quote repr, head or tail piece not next to "...", pprint line wrapping, quoted password with escape.
- m5: lock-file owner and mode are not checked after opening; the file is left behind and blocks another user (:429-436).
- m6: round-4 evidence names no head sha, no file hashes, no mutants total line.
- Nit: `_masked` rebuilds text with no secret set (O(n)). Nit: `os.fdopen` failure would leak a descriptor.

Reviewer note: under the no-round-cap redaction rule, m1 must be fixed and re-checked before the verdict is final.
