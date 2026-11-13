# NOTES p2-optional-gaps (delta on sonar-p2-regex-optional + sonar-p2-feed-optional)
Patch: sonar-p2-optional-gaps-delta.patch. TEST-ONLY: ONE NEW file, tests/test_sonar_p2_optional_gaps.py (33 tests, ~1.3 s). It edits no existing file, so it applies in any order with every other patch (none touches that path). Needs R (regex-optional) and F (feed-optional) APPLIED for the tests to pass (they test the patched code). Base: pr-3-tests head b573c41. Rung table: not applicable (test-only, no new product code; R448 satisfied).

## Failures / limits first
- The brief says feed.py has exactly --source and --index. The real file also has `--all` (send every canned lead). The test pins exactly {--source, --index, --all, -h/--help}; dests {source, index, all, help}.
- Several mutants SURVIVE this one file; each is explained: (a) equivalent mutants (same language, proven or per the reviewer), (b) covered by the two existing optional test files / test_scrub_n8n_export (lookbehind, timing, feed-address mutants F6-F12 were killed by the existing feed file in rv38; I ran only the new file here), see table.
- Apply matrix: the other pending/old deltas (v2.2, v2.3, v3.2.1, v3.2.2, p3-final) cannot be applied forward on b573c41 at all (they are ALREADY in that branch; with or without my patch), and nodemo-optional-hygiene does not apply on f3d9dca either; so the matrix proves order-independence only by (1) all 6 orders of R,F,G OK, (2) file-disjointness (no other patch in the folder touches my file; mine touches only it).
- Sonar not run (cannot); no code changed, so no Sonar expectation changes.
- Slip: my first apply-matrix script was broken (cwd deleted, clones failed, output noise); redone with git archive; the evidence file is the redo.
- Tokens: not measured.

## What each new test pins (N1, N2)
| Gap | Tests | Oracle |
| _ADDRESS domain class drops `;` (A11) | test_address_domain_stops_at_a_semicolon, ..._near (7 texts), small-alphabet exhaustive over a@;:space' len<=6 (>50k texts) | old pattern: sub output AND every match span |
| MAIL allow list gains org / net (M15b, M16) | ..._replaces_any_other_top_level_name (org, net, io, co, edu, local, example), ..._leaves_only_the_three_made_up_names_alone (com, test, invalid: plain, sub-domain, trailing dot, ; and space) | explicit expectations + old pattern |
| MAIL end guards (M6b, M10b; `a@example.com.evil.test`, `a@example.com-x`, `a@sub.example.com.`) | ..._replaces_a_longer_name_that_starts_with_an_allowed_one (8 tails x 3 names x 2 fronts), end_guard_cases (fronts x names x tails x local forms x both @), token-exhaustive differential (10 tokens, len<=5, >100k) | old pattern |
| feed: new --host/--address option (F5, F1, F3, F14) | test_feed_parser_defines_exactly_the_known_options (ArgumentParser introspection by recording parse_args), test_feed_source_adds_only_the_known_arguments (AST: every add_* call, parse_known_args refused) | none (exact lists) |
| feed: getattr(args,"url") (F4) | test_feed_main_reads_only_known_attributes (AST: attribute reads of args subset of {all,index,source}; getattr/vars/setattr/hasattr on args refused), test_feed_main_has_no_address_like_string_constant (no "url"/"host"/"address"/... string constant in main) | none |
Old patterns are literals in the test (copied from f3d9dca, as in the regex-optional test). Email shapes are built from AT/DOT parts: no literal address.

## Mutants (drivers evidence-p2optgaps-driver-*.py; outputs evidence-p2optgaps-4/5/6)
Killed by the NEW file alone: A3-A11 (incl. A11 `;`), M2, M3, M4, M5, M7, M9, M14, **M15b (org in both places)**, **M16 (net in both)**, **M6b (both end guards dropped)**, **M10b (both changed to (?![\w-]))**; feed F1, F2, F3, F4 (getattr url), F5 (new --host), F14. Run `-x`, one test file.
Survivors and why:
- M15 / M15c (org in ONE place) and M6 / M6c / M10 / M10c (one end guard dropped/changed, first or last): EQUIVALENT. Possessive repeats make the second guard redundant; exhaustive 1,111,111 texts (10 tokens, len<=6) show 0 differences in output and spans for all four single-place variants (evidence-6). Only the both-places variants differ (216 diffs): those are killed. This answers the brief's M6/M10: the distinguishing texts (`a@example.com.evil.test`, `a@example.com.x`, `a@example.com.a`) exist only when BOTH guards change.
- A2, A12, M8, M11, M12, M13: equivalent (as rv38). A1, M1 (lookbehind dropped): not pinned by this file; killed by the existing regex-optional/test_scrub_n8n_export timing tests (rv38: M1 by the repo 1 MB test); not rerun here with the full set.
- F6-F13: not this file's job (existing feed-optional test kills F6-F10, F12 in rv38; F11, F13 equivalent).

## Runs
- 30 runs of the new file on the patched tree: 30x "33 passed" (evidence-1). Each ~1.3 s (two differential tests ~0.3-0.5 s).
- On b573c41 WITHOUT R and F: 4 failed (the feed tests, because `--url` exists), 29 passed (the regex tests cannot fail there: old == new; honest: they are mutant tests, shown by evidence-4).
- ruff check, ruff format --check (157 files), mypy linux+win32 clean; no type-ignore, no noqa. Hygiene+gitleaks (8.30.1, DPLD_REQUIRE_SCAN=1, after git add -A) with the 3 optional files, test_scrub_n8n_export, test_real_check_dry: 390 passed.
- Literals: no address/URL strings; the S5332-style http scheme string is not used. Tests touch private `parser._actions`/`_subparsers` of argparse (mypy accepts).
- Sonar effect: none expected (test file; Sonar flags in tests are possible: the test accesses a protected member `_actions`, which may raise a minor smell S6019-type finding; not measurable here).

## Files: sonar-p2-optional-gaps-delta.patch, evidence-p2optgaps-1..7 and driver files, this note. Head: b573c41 + R + F + this.
