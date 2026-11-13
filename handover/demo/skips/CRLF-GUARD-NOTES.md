# CRLF guard patch (C1). Base pr-3-tests 2db3926. File: crlf-guard.patch (3 files, +81/-3)
- tests/test_hygiene.py: (1) test_hygiene_scan_public now writes a JSON report for the tree/history scans; on failure the message names the flagged files and, if one holds a CR, adds the CRLF hint (scan not weakened, same exit-code assertion). (2) new test_the_secret_scan_files_have_no_carriage_return (sonar-project.properties, .gitleaks.toml, exceptions.txt, patterns.txt, requirements-*.txt; .ps1/.bat/.cmd skipped). (3) two helper unit tests (CRLF tmp files, report parsing).
- .editorconfig: `[*] end_of_line = lf`, `[*.ps1] end_of_line = crlf` = exactly .gitattributes (added; nothing else set).
- docs/tests.md: one sentence with the fix command.
- Evidence: evidence-c1-1 (62 pass on LF tree), -2 (new tests fail on CRLF sonar file, with hint), -3 (old message on same tree: no CRLF word), -4 gates, -5 apply orders + clean checkout gitleaks dir/git 0, -6 combined with semgrep v4: 62 pass.
- Not checked: real Windows; versions-md-allowance.patch and real-run-fixes.patch do not exist on disk (not tested). Not committed.

## v2 (crlf-guard-v2.patch; v1 kept)
- MEASURED cure for a CRLF working copy of sonar-project.properties (evidence-c1-7): `git checkout -- file` works (tests pass), `sed -i 's/\r$//' file` works, `git add --renormalize .` does NOT (CR stays: it changes only the index; the scan reads the working copy), rm + checkout works. CRLF_HINT and docs/tests.md now say: save with LF, or discard your edits with `git checkout -- <file>`; docs also say renormalize does not help.
- With core.autocrlf=true and the repo's eol=lf attribute a checkout is already LF (CRLF-EMULATION.md case A), so the hint only matters for a hand-saved CRLF file.
- Nit fixes: only .ps1 is CRLF by design (CRLF_BY_DESIGN = (".ps1",); .bat/.cmd get LF via `*`); code comment says the hint reads the working copy, not the historic blob, for `gitleaks git`.
- Limits: the checked file list is hard-coded (LF_ONLY_FILES) and matches ROOT-level files only (fnmatch on the full git path: nested requirements-*.txt are not checked).
- Evidence: -8 gates (62 pass), -9 CRLF failure with new hint, -10 apply checks on fresh clones (v2 alone, both orders with semgrep v4 and versions-md-allowance: all OK).
