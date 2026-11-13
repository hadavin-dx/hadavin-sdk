# crlf-guard-v3.patch (base 2db3926; 3 files: .editorconfig, docs/tests.md, tests/test_hygiene.py; +143/-3)
Built from v2. Changes: the scan failure text is now built by one function `_scan_failure_message(sub, flagged, root)`
(used by test_hygiene_scan_public); the guard test calls `_scan_files_with_cr(root)`; CRLF_HINT now also names
`sed -i 's/\r$//' <file>`; new tests: end-to-end message with a planted CRLF and a lone-CR copy of
sonar-project.properties (name, `git checkout --`, `sed -i`, no "renormalize"), the real guard test run against a planted tree
(must raise), a lone-CR unit test. Mutants M3 M5 M6 M8 M9 all fail tests: evidence-b3-2.
Not killed: a change at the call site in test_hygiene_scan_public that bypasses the message function (M3b); only a real
gitleaks run on a CRLF tree sees that, measured once by hand (evidence-b3-4), not as an automatic test (it is slow, 50 s).
Limits kept from v2: root-level files only; real Windows not tested.
