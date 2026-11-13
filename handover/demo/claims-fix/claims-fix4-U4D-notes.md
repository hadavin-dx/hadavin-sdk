# U4D notes (base 3ae42bd; patch /tmp/work/claims-fix4-U4D.patch). Audit verdict is U (UNBACKED) for every row unless noted.
Format: file | OLD | NEW | evidence | verdict
## docs/real-services.md
1. "Everything else in this repository ran against demo stand-ins" | -> "Apart from that probe, tests and scripts use demo stand-ins; no log of any real-service run is shipped" | no logs | F
2. "nobody outside your own inboxes receives anything" | -> mail kind picks the address only from the configured inbox list (test in tests/test_smtp_provider.py; code: smtp_provider.py recipient_for) | F (narrowed to what is tested)
3. "refuses to start without explicit caps" | -> refuses when a required cap/setting is missing (tests/test_real_check_dry.py first test; script docstring line 7) | S
4. "the program never creates properties" | -> contacts endpoints only (crm_hubspot.py top comment); not tested | F
5. two addresses "the result says so" | -> check list names "two-leads" (check_invariants.py:227; tests/test_load_tools.py:876) | S
6. "X-Send-Key (no body or address is read)" | -> imap_count.py fetches only that header (BODY.PEEK[HEADER.FIELDS]); no test shows nothing else read. NB the audit pointed at run_real_check.py:228, which is the demo-fake mirror, not the real IMAP read: audit partly wrong | F/S
7. "Failure tables print no address and no setting value" | -> addresses masked (test_real_check_dry.py mask test, asserts '@' absent); refusals do not echo a setting value (same file); no test covers every table line | F
8. "CRM key only to vendor's own API host names" | -> settings refuse a base address outside vendor domains unless a setting allows it (crm_hubspot.py:167-170; tests/test_crm_hubspot.py:448); no test follows the key on the wire | F
9. config location paragraph | pointer to tests/test_path_confinement.py added; `--config <(command)` refusal now "expected, no test covers it" | S + F
## docs/why-this-code.md
10. crash between CRM step and email step covered by tests | -> tests/test_crash_points.py kills the desk at each named point; no case named for that gap | F
11. "adapter itself never did" | -> "as far as the author knows, not run against one (no log either way is shipped)" | F
12. k6/vegeta/hey | -> "exist ... (named from general knowledge, not tried here)" | F
13. "must not import from demo_only" | -> "should not (no test enforces; a search of the 4 real adapter modules found none)" (grep of crm_hubspot, smtp_provider, imap_count, live_claude: 0 hits) | F
14. "Seven checks": code docstring says seven and 7 check_* functions exist (receipts, partition, messages, crm, model_calls, rate_503, drain) | W (words right, no change)
15. 'Under 100 lines' and 'test fails if missed': already fixed by stage 1 (current text says About 200 lines / names what the test checks): not redone.
## workflows (comments only)
16. lint.yml gitleaks checksum provenance | -> author's note, no copy in repo, step checks the download against this value | F
17. lint.yml --ignore-gitleaks-allow effect | -> "meant to ... per gitleaks' own documentation; not tested here" (tests only pass the flag) | F
18. codeql.yml "still the newest releases" | -> by the author; not checked again | F
19. codeql.yml "ids checked against docs" | -> read by the author; no copy | F
20. codeql.yml "read 2026-11-12" README citation | -> same wording | F
21. sonar.yml Automatic Analysis message | -> "expected to stop with ... (as quoted by the author; not checked here)" | F
22. sonar.yml "never printed" | -> file only passes the token to the scan step (sonar.yml: only use, no echo) and GitHub hides secrets | F
23. sonar.yml pip 24.0 "tested" | -> author's own local test; no log | F
24. semgrep.yml 17 s | labelled author's own run, no log | F (number unchanged)
25. semgrep.yml exit-codes | labelled author's own runs, no log | F
26. semgrep.yml run 43403502735 | added "job log not stored here; docs/tests.md repeats text only" | F
27. semgrep.yml --strict exit 3 | labelled author's own local test | F
Not redone: lint.yml "1.6 times" vs "about twice": already identical in current text. semgrep.yml lines 1-6 untouched; line 49-51 licence wording was already softened.
## Counts: S 3 (rows 3,5, 9a), F 21, O 0, W 1, already fixed 2 (some rows mixed S/F).
No owner questions. Not verified: no real HubSpot/IMAP/gitleaks runs here; "--config <(command)" refusal and gitleaks-allow behaviour untested.
## Checks run
- `/tmp/work/run-un.sh` (unshare -n) on tests/test_workflow_files_parse.py, test_workflow_run_flags.py, test_nosemgrep_form.py, test_gitleaks_semgrep_lock.py: 133 passed.
- Also tests/test_mode_safety.py, test_path_confinement.py, test_portal_wording_and_masking.py: 293 passed, 1 skipped.
- git apply --check on a fresh copy of the base: OK. Added lines grep: no 40+ char runs, links, IPs, suppressions. Workflow edits comment-only.
