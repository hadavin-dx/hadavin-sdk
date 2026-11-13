# CRLF guard patch (C1). Base pr-3-tests 2db3926. File: crlf-guard.patch (3 files, +81/-3)
- tests/test_hygiene.py: (1) test_hygiene_scan_public now writes a JSON report for the tree/history scans; on failure the message names the flagged files and, if one holds a CR, adds the CRLF hint (scan not weakened, same exit-code assertion). (2) new test_the_secret_scan_files_have_no_carriage_return (sonar-project.properties, .gitleaks.toml, exceptions.txt, patterns.txt, requirements-*.txt; .ps1/.bat/.cmd skipped). (3) two helper unit tests (CRLF tmp files, report parsing).
- .editorconfig: `[*] end_of_line = lf`, `[*.ps1] end_of_line = crlf` = exactly .gitattributes (added; nothing else set).
- docs/tests.md: one sentence with the fix command.
- Evidence: evidence-c1-1 (62 pass on LF tree), -2 (new tests fail on CRLF sonar file, with hint), -3 (old message on same tree: no CRLF word), -4 gates, -5 apply orders + clean checkout gitleaks dir/git 0, -6 combined with semgrep v4: 62 pass.
- Not checked: real Windows; versions-md-allowance.patch and real-run-fixes.patch do not exist on disk (not tested). Not committed.
