# SUMMARY codeant3 security fixes (builder 10c-1b hand-back, saved by the session lead; unreviewed). Base 0841f36. Patches: codeant3-gitleaks.patch, codeant3-scripts.patch, codeant3-n8n-proof.patch (unchanged from codeant2), codeant3-docs.patch.
FAILED / UNCERTAIN FIRST
- First full run failed (1 failed): the repo literal scan flagged `127.0.0.0` in a new settings.md sentence and a literal address in a scrub comment; fixed, rerun green (first run kept: evidence-codeant3-sec-3-final-pytest-FIRST-RUN-1-failed.txt).
- Item 10 (node switch): NO CHANGE; the repo has no DPLD_REQUIRE_NODE and other node tests use the same plain skipif.
- Several new tests pass on the previous state by nature (rule-id/requirements-coverage test, redirect pin, linearity tests); proven with mutants (evidence 7, 8).
- Not run: PowerShell, Windows, Python 3.13, a real n8n, the 3 playwright tests (module missing), the full suite (13 files only).
- Plain `gitleaks dir .` in a work folder: 43 leaks, all in cache folders made by its own runs; tracked files only (git archive): 0.
- CROSS-LANE: docs-and-deps-v4 and semgrep-rebased conflict at .codeant/configuration.json:17. docs-and-deps-v4 keeps the unanchored `(^|[/\\])requirements-browser(-win)?\.txt$` line (intended interim); after codeant3-gitleaks it must become `^requirements-(dev(-win)?|coverage|browser(-win)?)\.txt$` and the name added to the planting test `ok` set.
FIXES (11 items)
1. Garbled docs sentence restored byte for byte; parenthetical is its own sentence.
2. scrub URL regex: look-behind removed, scheme bounded {0,31}; `5http://h/x` -> `5http://localhost/REPLACE-ME`. ACTIVE_LINK `\b` removed (`5javascript:`, `_data:`, `xvbscript:` no longer pass). Prefix table: evidence 1.
3. One linearity test per regex, 1 MB x 17 worst shapes, own process, 64 s stop; worst URL 0.105 s, MAIL 0.046 s, ACTIVE_LINK 0.053 s (limit 2 s). Quadratic mutant fails URL and MAIL (evidence 8).
4. n8n_api `workflows()` helper: non-200 on list/find/activate/deactivate = clean SystemExit; tests cover list, activate, deactivate redirects, odd body.
5. GITLEAKS_BIN resolved to an absolute path in both places + relative-path test.
6. Planting test asserts RuleID `long-hex-token`; requirements-coverage.txt in `ok`; values built from parts.
7. Loopback wording matches `is_loopback_host`; --dry-fakes sentence; scan-from-repo-root sentence in settings.md.
8. 737 leaks belong to the literal old patch on 2ce1f98; on 0841f36 the old idea shows 1 failed, 9 passed.
9. Recipe: plain instruction to delete the old copy in the n8n screen (not tried); no delete command (second destructive action would need its own guard/tests/review).
11. reset.ps1 test: `exit 2` before Get-Content, Stop-Process, Remove-Item, one test per action; mutant moving Stop-Process up fails only the new test.
PROOF (fresh 0841f36 + four patches, gitleaks 8.30.1, DPLD_REQUIRE_SCAN=1): 13 test files 877 passed, 3 skipped, 168 s (3c); new tests on previous state: 53 failed, 188 passed (6); gitleaks dir/git 0; ruff, mypy linux/win32, bandit -ll clean (4a, 4b, 5).
APPLY MATRIX (evidence 9): 11 of 11 other patches apply alone and in both orders with these, plain and --3way. Hunks overlap only in docs/settings.md, .gitleaks.toml, tests/test_hygiene.py, disjoint. With semgrep-rebased the tracked tree scans clean (evidence 10).
