# Carry-over checklist: inline bot review comments on pull requests #1 to #4

Generated from the public GitHub API (saved as raw-pulls-N-comments.json, fetched 2026-11-13) and a read-only clone at pr-3-tests 2db3926. Script: python3 -I checklist.py (no network).

Read this first:
- 'Open' here means every top-level inline comment. The public REST API does not say whether a thread is resolved (that needs the GraphQL API with a token; the token in this session was invalid). So none is known to be resolved; the lead ticks them off by hand.
- 'Final tree' says whether the exact line the bot pointed at (read at the commit it reviewed) is still in the final tree 2db3926: SAME line N = same text at the same line; MOVED = same text, other line; CHANGED = the file exists but that line text is gone (probably fixed or rewritten: check); FILE-GONE = the file is not in the final tree.
- No human wrote an inline review comment on any of the four pull requests (all authors are bots).
- Gists are the first 100 characters of the bot's own title, not a judgement of whether the finding is right.

| done | PR | comment id | bot | severity | file:line (as reviewed) | gist (first 100 chars) | final tree 2db3926 |
|---|---|---|---|---|---|---|---|
| [ ] | #1 | 4553581537 | github-advanced-security | code-scanning | `src/lead_desk/portal/portal.js:557` | CodeQL / Prototype-polluting assignment | MOVED to 558 |
| [ ] | #1 | 4553583379 | github-advanced-security | code-scanning | `scripts/run_real_check.py:178` | CodeQL / Clear-text storage of sensitive information | SAME line 178 |
| [ ] | #2 | 4554060065 | github-advanced-security | code-scanning | `scripts/run_real_check.py:178` | CodeQL / Clear-text storage of sensitive information | SAME line 178 |
| [ ] | #2 | 4554091521 | deepsource-io | minor | `load_tools/check_invariants.py:146` | 'check_receipts' has a cyclomatic complexity of 40 with "very-high" risk | SAME line 146 |
| [ ] | #2 | 4554091541 | deepsource-io | minor | `load_tools/catcher.py:101` | 'Catcher._session' has a cyclomatic complexity of 18 with "high" risk | SAME line 101 |
| [ ] | #2 | 4554091550 | deepsource-io | major | `load_tools/catcher.py:91` | Overlapping exceptions (OSError is an ancestor class of TimeoutError) | CHANGED (text gone) |
| [ ] | #2 | 4554091563 | deepsource-io | minor | `load_tools/check_invariants.py:228` | 'check_partition' has a cyclomatic complexity of 36 with "very-high" risk | SAME line 228 |
| [ ] | #2 | 4554091573 | deepsource-io | minor | `load_tools/check_invariants.py:294` | 'check_messages' has a cyclomatic complexity of 31 with "very-high" risk | SAME line 294 |
| [ ] | #2 | 4554091583 | deepsource-io | minor | `load_tools/check_invariants.py:388` | 'check_crm' has a cyclomatic complexity of 19 with "high" risk | SAME line 388 |
| [ ] | #2 | 4554091594 | deepsource-io | minor | `load_tools/check_invariants.py:473` | 'check_rate_503' has a cyclomatic complexity of 17 with "high" risk | SAME line 473 |
| [ ] | #2 | 4554091610 | deepsource-io | major | `load_tools/load_driver.py:238` | Unused variable 'j' | CHANGED (text gone) |
| [ ] | #2 | 4554091617 | deepsource-io | major | `load_tools/load_driver.py:267` | Redefining name 'run' from outer scope | SAME line 267 |
| [ ] | #2 | 4555610407 | codeant-ai | Major | `.gitleaks.toml:91` | Because these paths are not anchored, 'docs/requirements-dev.txt' is also exempt; matching 40- or 64 | CHANGED (text gone) |
| [ ] | #2 | 4555630237 | codeant-ai | Critical | `scripts/n8n_api.py:32` | 'N8N_URL' can name a remote HTTP server, so this sends the API key without encryption; anyone observ | MOVED to 131 |
| [ ] | #2 | 4555639522 | codeant-ai | Major | `tools/scrub_n8n_export.py:40` | 'URL' ignores schemes other than HTTP and HTTPS, so an FTP or file URL in node parameters retains it | CHANGED (text gone) |
| [ ] | #2 | 4555639542 | codeant-ai | Major | `tools/scrub_n8n_export.py:41` | 'MAIL' treats a word boundary after 'example.com' as an allowed-domain end, so 'user@example.com.evi | CHANGED (text gone) |
| [ ] | #2 | 4555640422 | codeant-ai | Major | `docs/settings.md:120` | This says a successful run leaves no contacts behind, but without --cleanup the script keeps every c | CHANGED (text gone) |
| [ ] | #2 | 4555650040 | codeant-ai | Critical | `src/lead_desk/desk.py:397` | ':memory:' creates a separate SQLite database for each thread-local connection. Startup initializes  | MOVED to 416 |
| [ ] | #2 | 4555650061 | codeant-ai | Major | `src/lead_desk/desk.py:785` | A timed-out PATCH can outlive this pass. Without per-lead exclusivity, a newer stage PATCH can finis | MOVED to 59,77,106... |
| [ ] | #2 | 4555651139 | codeant-ai | Critical | `scripts/reset.ps1:20` | 'GetFullPath' does not resolve junctions or symlinks, so a database directory redirected outside 'da | CHANGED (text gone) |
| [ ] | #2 | 4555653780 | codeant-ai | Major | `src/lead_desk/portal/pages/log.js:119` | After older rows load, polling refreshes the first page but keeps 'extra' and its cursor; rows pushe | CHANGED (text gone) |
| [ ] | #2 | 4555653797 | codeant-ai | Major | `src/lead_desk/portal/pages/overview.css:117` | These rules force four or five KPI columns at every viewport width; on phones, each tile becomes too | SAME line 117 |
| [ ] | #2 | 4555660211 | codeant-ai | Major | `src/lead_desk/portal/pages/data.js:121` | After a successful load, a non-200 poll sets 'failure' but leaves 'map'; 'render' still displays tha | SAME line 121 |
| [ ] | #2 | 4555676365 | codeant-ai | Major | `n8n/proof.json:272` | This reports PASS when CRM and outbox each have one row, even if only one of the ten requests reache | CHANGED (text gone) |
| [ ] | #3 | 4554108686 | deepsource-io | major | `demo_only/fakes.py:134` | Consider merging these comparisons with 'in' by using 'label in ('hot', 'warm', 'cold')'. Use a set  | SAME line 134 |
| [ ] | #3 | 4554108700 | deepsource-io | major | `demo_only/burst.py:83` | Consider merging these comparisons with 'in' by using 'res in (HTTP_BUSY, 'refused')'. Use a set ins | SAME line 83 |
| [ ] | #3 | 4554108711 | deepsource-io | major | `demo_only/fake_hubspot.py:117` | Redefining built-in 'format' | MOVED to 184 |
| [ ] | #3 | 4554108721 | deepsource-io | major | `demo_only/fakes_server.py:47` | Redefining built-in 'format' | SAME line 47 |
| [ ] | #3 | 4554108733 | deepsource-io | minor | `demo_only/fake_hubspot.py:133` | Attribute 'close_connection' defined outside __init__ | MOVED to 226,256,362 |
| [ ] | #3 | 4554108745 | deepsource-io | minor | `demo_only/fake_hubspot.py:162` | Attribute 'close_connection' defined outside __init__ | MOVED to 226,256,362 |
| [ ] | #3 | 4554108749 | deepsource-io | minor | `demo_only/fake_hubspot.py:253` | '_Handler._create' has a cyclomatic complexity of 16 with "high" risk | MOVED to 335 |
| [ ] | #3 | 4554108757 | deepsource-io | minor | `demo_only/fake_hubspot.py:282` | Attribute 'close_connection' defined outside __init__ | MOVED to 226,256,362 |
| [ ] | #3 | 4554108767 | deepsource-io | minor | `demo_only/fake_imap.py:60` | 'FakeImap._serve' has a cyclomatic complexity of 18 with "high" risk | SAME line 60 |
| [ ] | #3 | 4554108776 | deepsource-io | minor | `demo_only/fake_model_server.py:96` | '_handler' has a cyclomatic complexity of 34 with "very-high" risk | MOVED to 100 |
| [ ] | #3 | 4554108783 | deepsource-io | major | `demo_only/fake_model_server.py:100` | Redefining built-in 'format' | MOVED to 104 |
| [ ] | #3 | 4554108793 | deepsource-io | minor | `demo_only/fake_smtp_tls.py:97` | 'FakeSmtp._dialogue' has a cyclomatic complexity of 25 with "high" risk | SAME line 97 |
| [ ] | #3 | 4554108807 | deepsource-io | minor | `demo_only/fakes_server.py:60` | Attribute 'close_connection' defined outside __init__ | SAME line 60 |
| [ ] | #3 | 4554108816 | deepsource-io | minor | `demo_only/fakes_server.py:71` | Attribute 'close_connection' defined outside __init__ | SAME line 71 |
| [ ] | #3 | 4554108823 | deepsource-io | major | `demo_only/portal_demo.py:264` | Consider merging these comparisons with 'in' by using 'cfg.port not in (0, port)'. Use a set instead | SAME line 264 |
| [ ] | #3 | 4554108829 | deepsource-io | major | `demo_only/portal_demo.py:297` | Method doesn't use the class instance and could be converted into a static method | MOVED to 306 |
| [ ] | #3 | 4554108838 | deepsource-io | minor | `demo_only/portal_demo.py:319` | 'PortalDemo._fakes' has a cyclomatic complexity of 17 with "high" risk | MOVED to 328 |
| [ ] | #3 | 4554108845 | deepsource-io | major | `demo_only/portal_demo.py:326` | Possible unbalanced tuple unpacking with sequence defined at line 322: left side has 3 labels, right | CHANGED (text gone) |
| [ ] | #3 | 4554108856 | deepsource-io | minor | `demo_only/portal_demo.py:449` | 'PortalDemo._burst' has a cyclomatic complexity of 18 with "high" risk | MOVED to 458 |
| [ ] | #3 | 4555619643 | codeant-ai | Major | `demo_only/portal_demo.py:274` | When the configured server port is '0', '_url_from_config()' returns 'None' and no server code updat | SAME line 274 |
| [ ] | #3 | 4555619663 | codeant-ai | Critical | `demo_only/portal_demo.py:414` | If an arm request is writing while a later clear request unlinks, the arm can replace the file after | MOVED to 423 |
| [ ] | #4 | 4554106704 | deepsource-io | major | `tests/test_burst_retry.py:139` | Method doesn't use the class instance and could be converted into a static method | SAME line 139 |
| [ ] | #4 | 4554106713 | deepsource-io | major | `tests/support.py:252` | Possible SQL injection vector through string-based query construction. | MOVED to 253 |
| [ ] | #4 | 4554106720 | deepsource-io | major | `tests/support.py:271` | Redefining name 'sql' from outer scope | MOVED to 272 |
| [ ] | #4 | 4554106726 | deepsource-io | critical | `tests/test_burst_retry.py:75` | Call to 'next()' should be wrapped in 'try-except' | SAME line 75 |
| [ ] | #4 | 4554106737 | deepsource-io | critical | `tests/test_flow.py:537` | Call to 'next()' should be wrapped in 'try-except' | SAME line 537 |
| [ ] | #4 | 4554106749 | deepsource-io | minor | `tests/test_crash_points.py:36` | 'subprocess.run' used without explicitly defining the value for 'check'. | SAME line 36 |
| [ ] | #4 | 4554106764 | deepsource-io | critical | `tests/test_flow.py:538` | Call to 'next()' should be wrapped in 'try-except' | SAME line 538 |
| [ ] | #4 | 4554106781 | deepsource-io | minor | `tests/test_crash_points.py:40` | 'subprocess.run' used without explicitly defining the value for 'check'. | SAME line 40 |
| [ ] | #4 | 4554106792 | deepsource-io | critical | `tests/test_flow.py:501` | Call to 'next()' should be wrapped in 'try-except' | SAME line 501 |
| [ ] | #4 | 4554106808 | deepsource-io | major | `tests/test_hung_adapter_calls.py:537` | Consider merging collapsible 'With' statements' | SAME line 537 |
| [ ] | #4 | 4554106822 | deepsource-io | major | `tests/test_hung_adapter_calls.py:540` | Lambda may not be necessary | SAME line 540 |
| [ ] | #4 | 4554106836 | deepsource-io | critical | `tests/test_hung_adapter_calls.py:759` | Call to 'next()' should be wrapped in 'try-except' | SAME line 759 |
| [ ] | #4 | 4554106848 | deepsource-io | critical | `tests/test_hung_adapter_calls.py:771` | Call to 'next()' should be wrapped in 'try-except' | SAME line 771 |
| [ ] | #4 | 4554106867 | deepsource-io | critical | `tests/test_hung_adapter_calls.py:802` | Call to 'next()' should be wrapped in 'try-except' | SAME line 802 |
| [ ] | #4 | 4554106877 | deepsource-io | major | `tests/test_hung_model_call.py:315` | Unused variable 'status' | SAME line 315 |
| [ ] | #4 | 4554106888 | deepsource-io | critical | `tests/test_hung_model_call.py:316` | Call to 'next()' should be wrapped in 'try-except' | SAME line 316 |
| [ ] | #4 | 4554106900 | deepsource-io | major | `tests/support.py:252` | Redefining name 'sql' from outer scope | MOVED to 253 |
| [ ] | #4 | 4554106908 | deepsource-io | major | `tests/conftest.py:24` | Unused argument 'session' | MOVED to 25 |
| [ ] | #4 | 4554106918 | deepsource-io | major | `tests/conftest.py:43` | Method doesn't use the class instance and could be converted into a static method | MOVED to 44 |
| [ ] | #4 | 4554106930 | deepsource-io | critical | `tests/support.py:48` | Call to 'next()' should be wrapped in 'try-except' | MOVED to 49 |
| [ ] | #4 | 4554106941 | deepsource-io | major | `tests/support.py:84` | Redefining name 'sql' from outer scope | MOVED to 85 |
| [ ] | #4 | 4554106950 | deepsource-io | major | `tests/support.py:147` | Use of assert detected. The enclosed code will be removed when compiling to optimised byte code. | MOVED to 148 |
| [ ] | #4 | 4554106960 | deepsource-io | major | `tests/support.py:245` | Redefining name 'sql' from outer scope | MOVED to 246 |
| [ ] | #4 | 4554106966 | deepsource-io | major | `tests/support.py:400` | Redefining built-in 'format' | MOVED to 401 |
| [ ] | #4 | 4554106974 | deepsource-io | minor | `tests/support.py:420` | Attribute 'close_connection' defined outside __init__ | MOVED to 421 |
| [ ] | #4 | 4554106984 | deepsource-io | minor | `tests/support.py:473` | Access to a protected member _write of a client class | MOVED to 576 |
| [ ] | #4 | 4554106998 | deepsource-io | minor | `tests/support.py:477` | Access to a protected member _getframe of a client class | MOVED to 580 |
| [ ] | #4 | 4554107012 | deepsource-io | minor | `tests/support.py:495` | Access to a protected member _drives of a client class | MOVED to 598 |
| [ ] | #4 | 4554107025 | deepsource-io | minor | `tests/support.py:496` | Access to a protected member _drives of a client class | MOVED to 599 |
| [ ] | #4 | 4554107037 | deepsource-io | minor | `tests/support.py:498` | Access to a protected member _now of a client class | MOVED to 601 |
| [ ] | #4 | 4554107044 | deepsource-io | minor | `tests/support.py:498` | Access to a protected member _workers of a client class | MOVED to 601 |
| [ ] | #4 | 4554107055 | deepsource-io | minor | `tests/support.py:499` | Access to a protected member _abandoned of a client class | MOVED to 602 |
| [ ] | #4 | 4554107067 | deepsource-io | major | `tests/test_claim_checks_and_crm_mode.py:104` | Method doesn't use the class instance and could be converted into a static method | SAME line 104 |
| [ ] | #4 | 4554107076 | deepsource-io | major | `tests/test_claim_checks_and_crm_mode.py:135` | Method doesn't use the class instance and could be converted into a static method | SAME line 135 |
| [ ] | #4 | 4554107089 | deepsource-io | major | `tests/test_claim_checks_and_crm_mode.py:138` | Method doesn't use the class instance and could be converted into a static method | SAME line 138 |
| [ ] | #4 | 4554107104 | deepsource-io | major | `tests/test_claim_checks_and_crm_mode.py:142` | Method doesn't use the class instance and could be converted into a static method | SAME line 142 |
| [ ] | #4 | 4554107112 | deepsource-io | critical | `tests/test_crash_points.py:35` | Call to 'next()' should be wrapped in 'try-except' | SAME line 35 |
| [ ] | #4 | 4554107119 | deepsource-io | major | `tests/test_desk_edge_cases.py:203` | Reimport 'sqlite3' (imported line 11) | SAME line 203 |
| [ ] | #4 | 4554107130 | deepsource-io | major | `tests/test_desk_http_edge_cases.py:468` | Unused variable 'body' | SAME line 468 |
| [ ] | #4 | 4554107151 | deepsource-io | minor | `tests/test_env_numbers.py:133` | 'subprocess.run' used without explicitly defining the value for 'check'. | SAME line 133 |
| [ ] | #4 | 4554107169 | deepsource-io | major | `tests/test_env_numbers.py:565` | Consider merging collapsible if statements | SAME line 565 |
| [ ] | #4 | 4554107178 | deepsource-io | major | `tests/test_env_numbers.py:568` | Consider merging collapsible if statements | SAME line 568 |
| [ ] | #4 | 4554107186 | deepsource-io | major | `tests/test_env_numbers.py:651` | Consider merging collapsible if statements | SAME line 651 |
| [ ] | #4 | 4554107195 | deepsource-io | major | `tests/test_env_numbers.py:657` | Consider merging collapsible if statements | SAME line 657 |
| [ ] | #4 | 4554107202 | deepsource-io | major | `tests/test_env_numbers.py:785` | Consider merging collapsible if statements | MOVED to 786 |
| [ ] | #4 | 4554107212 | deepsource-io | critical | `tests/test_flow.py:499` | Raising NoneType while only classes or instances are allowed | SAME line 499 |
| [ ] | #4 | 4554107228 | deepsource-io | major | `tests/test_followup_edge_cases.py:448` | 'log_message' doesn't contain any code | BLANK-LINE (cannot match) |
| [ ] | #4 | 4554107239 | deepsource-io | critical | `tests/test_http_guard.py:40` | Call to 'next()' should be wrapped in 'try-except' | SAME line 40 |
| [ ] | #4 | 4554107255 | deepsource-io | major | `tests/test_hubspot_probe.py:71` | 'log_message' doesn't contain any code | SAME line 71 |
| [ ] | #4 | 4554107272 | deepsource-io | critical | `tests/test_hubspot_probe.py:292` | Call to 'next()' should be wrapped in 'try-except' | MOVED to 291 |
| [ ] | #4 | 4554107282 | deepsource-io | critical | `tests/test_hubspot_probe.py:386` | Call to 'next()' should be wrapped in 'try-except' | MOVED to 385 |
| [ ] | #4 | 4554107294 | deepsource-io | major | `tests/test_hung_adapter_calls.py:368` | Method doesn't use the class instance and could be converted into a static method | SAME line 368 |
| [ ] | #4 | 4554107304 | deepsource-io | major | `tests/test_hung_model_call.py:387` | Method doesn't use the class instance and could be converted into a static method | SAME line 387 |
| [ ] | #4 | 4554131160 | deepsource-io | major | `tests/test_burst_retry.py:139` | Method doesn't use the class instance and could be converted into a static method | SAME line 139 |
| [ ] | #4 | 4554131178 | deepsource-io | major | `tests/support.py:252` | Possible SQL injection vector through string-based query construction. | MOVED to 253 |
| [ ] | #4 | 4554131186 | deepsource-io | major | `tests/support.py:271` | Redefining name 'sql' from outer scope | MOVED to 272 |
| [ ] | #4 | 4554131196 | deepsource-io | critical | `tests/test_burst_retry.py:75` | Call to 'next()' should be wrapped in 'try-except' | SAME line 75 |
| [ ] | #4 | 4554131209 | deepsource-io | critical | `tests/test_flow.py:537` | Call to 'next()' should be wrapped in 'try-except' | SAME line 537 |
| [ ] | #4 | 4554131218 | deepsource-io | minor | `tests/test_crash_points.py:36` | 'subprocess.run' used without explicitly defining the value for 'check'. | SAME line 36 |
| [ ] | #4 | 4554131227 | deepsource-io | critical | `tests/test_flow.py:538` | Call to 'next()' should be wrapped in 'try-except' | SAME line 538 |
| [ ] | #4 | 4554131247 | deepsource-io | minor | `tests/test_crash_points.py:40` | 'subprocess.run' used without explicitly defining the value for 'check'. | SAME line 40 |
| [ ] | #4 | 4554131258 | deepsource-io | critical | `tests/test_flow.py:501` | Call to 'next()' should be wrapped in 'try-except' | SAME line 501 |
| [ ] | #4 | 4554131282 | deepsource-io | major | `tests/test_hung_adapter_calls.py:537` | Consider merging collapsible 'With' statements' | SAME line 537 |
| [ ] | #4 | 4554131298 | deepsource-io | major | `tests/test_hung_adapter_calls.py:540` | Lambda may not be necessary | SAME line 540 |
| [ ] | #4 | 4554131313 | deepsource-io | critical | `tests/test_hung_adapter_calls.py:759` | Call to 'next()' should be wrapped in 'try-except' | SAME line 759 |
| [ ] | #4 | 4554131321 | deepsource-io | critical | `tests/test_hung_adapter_calls.py:771` | Call to 'next()' should be wrapped in 'try-except' | SAME line 771 |
| [ ] | #4 | 4554131337 | deepsource-io | critical | `tests/test_hung_adapter_calls.py:802` | Call to 'next()' should be wrapped in 'try-except' | SAME line 802 |
| [ ] | #4 | 4554131345 | deepsource-io | major | `tests/test_hung_model_call.py:315` | Unused variable 'status' | SAME line 315 |
| [ ] | #4 | 4554131358 | deepsource-io | critical | `tests/test_hung_model_call.py:316` | Call to 'next()' should be wrapped in 'try-except' | SAME line 316 |
| [ ] | #4 | 4554131369 | deepsource-io | major | `tests/support.py:252` | Redefining name 'sql' from outer scope | MOVED to 253 |
| [ ] | #4 | 4554131380 | deepsource-io | major | `tests/conftest.py:24` | Unused argument 'session' | MOVED to 25 |
| [ ] | #4 | 4554131385 | deepsource-io | major | `tests/conftest.py:43` | Method doesn't use the class instance and could be converted into a static method | MOVED to 44 |
| [ ] | #4 | 4554131396 | deepsource-io | critical | `tests/support.py:48` | Call to 'next()' should be wrapped in 'try-except' | MOVED to 49 |
| [ ] | #4 | 4554131405 | deepsource-io | major | `tests/support.py:84` | Redefining name 'sql' from outer scope | MOVED to 85 |
| [ ] | #4 | 4554131415 | deepsource-io | major | `tests/support.py:147` | Use of assert detected. The enclosed code will be removed when compiling to optimised byte code. | MOVED to 148 |
| [ ] | #4 | 4554131425 | deepsource-io | major | `tests/support.py:245` | Redefining name 'sql' from outer scope | MOVED to 246 |
| [ ] | #4 | 4554131434 | deepsource-io | major | `tests/support.py:400` | Redefining built-in 'format' | MOVED to 401 |
| [ ] | #4 | 4554131446 | deepsource-io | minor | `tests/support.py:420` | Attribute 'close_connection' defined outside __init__ | MOVED to 421 |
| [ ] | #4 | 4554131456 | deepsource-io | minor | `tests/support.py:473` | Access to a protected member _write of a client class | MOVED to 576 |
| [ ] | #4 | 4554131464 | deepsource-io | minor | `tests/support.py:477` | Access to a protected member _getframe of a client class | MOVED to 580 |
| [ ] | #4 | 4554131473 | deepsource-io | minor | `tests/support.py:495` | Access to a protected member _drives of a client class | MOVED to 598 |
| [ ] | #4 | 4554131486 | deepsource-io | minor | `tests/support.py:496` | Access to a protected member _drives of a client class | MOVED to 599 |
| [ ] | #4 | 4554131498 | deepsource-io | minor | `tests/support.py:498` | Access to a protected member _now of a client class | MOVED to 601 |
| [ ] | #4 | 4554131508 | deepsource-io | minor | `tests/support.py:498` | Access to a protected member _workers of a client class | MOVED to 601 |
| [ ] | #4 | 4554131518 | deepsource-io | minor | `tests/support.py:499` | Access to a protected member _abandoned of a client class | MOVED to 602 |
| [ ] | #4 | 4554131527 | deepsource-io | major | `tests/test_claim_checks_and_crm_mode.py:104` | Method doesn't use the class instance and could be converted into a static method | SAME line 104 |
| [ ] | #4 | 4554131540 | deepsource-io | major | `tests/test_claim_checks_and_crm_mode.py:135` | Method doesn't use the class instance and could be converted into a static method | SAME line 135 |
| [ ] | #4 | 4554131550 | deepsource-io | major | `tests/test_claim_checks_and_crm_mode.py:138` | Method doesn't use the class instance and could be converted into a static method | SAME line 138 |
| [ ] | #4 | 4554131557 | deepsource-io | major | `tests/test_claim_checks_and_crm_mode.py:142` | Method doesn't use the class instance and could be converted into a static method | SAME line 142 |
| [ ] | #4 | 4554131569 | deepsource-io | critical | `tests/test_crash_points.py:35` | Call to 'next()' should be wrapped in 'try-except' | SAME line 35 |
| [ ] | #4 | 4554131580 | deepsource-io | major | `tests/test_desk_edge_cases.py:203` | Reimport 'sqlite3' (imported line 11) | SAME line 203 |
| [ ] | #4 | 4554131590 | deepsource-io | major | `tests/test_desk_http_edge_cases.py:468` | Unused variable 'body' | SAME line 468 |
| [ ] | #4 | 4554131598 | deepsource-io | minor | `tests/test_env_numbers.py:133` | 'subprocess.run' used without explicitly defining the value for 'check'. | SAME line 133 |
| [ ] | #4 | 4554131605 | deepsource-io | major | `tests/test_env_numbers.py:565` | Consider merging collapsible if statements | SAME line 565 |
| [ ] | #4 | 4554131613 | deepsource-io | major | `tests/test_env_numbers.py:568` | Consider merging collapsible if statements | SAME line 568 |
| [ ] | #4 | 4554131618 | deepsource-io | major | `tests/test_env_numbers.py:651` | Consider merging collapsible if statements | SAME line 651 |
| [ ] | #4 | 4554131623 | deepsource-io | major | `tests/test_env_numbers.py:657` | Consider merging collapsible if statements | SAME line 657 |
| [ ] | #4 | 4554131640 | deepsource-io | major | `tests/test_env_numbers.py:785` | Consider merging collapsible if statements | MOVED to 786 |
| [ ] | #4 | 4554131651 | deepsource-io | critical | `tests/test_flow.py:499` | Raising NoneType while only classes or instances are allowed | SAME line 499 |
| [ ] | #4 | 4554131660 | deepsource-io | major | `tests/test_followup_edge_cases.py:448` | 'log_message' doesn't contain any code | BLANK-LINE (cannot match) |
| [ ] | #4 | 4554131671 | deepsource-io | critical | `tests/test_http_guard.py:40` | Call to 'next()' should be wrapped in 'try-except' | SAME line 40 |
| [ ] | #4 | 4554131687 | deepsource-io | major | `tests/test_hubspot_probe.py:71` | 'log_message' doesn't contain any code | SAME line 71 |
| [ ] | #4 | 4554131697 | deepsource-io | critical | `tests/test_hubspot_probe.py:292` | Call to 'next()' should be wrapped in 'try-except' | MOVED to 291 |
| [ ] | #4 | 4554131705 | deepsource-io | critical | `tests/test_hubspot_probe.py:386` | Call to 'next()' should be wrapped in 'try-except' | MOVED to 385 |
| [ ] | #4 | 4554131718 | deepsource-io | major | `tests/test_hung_adapter_calls.py:368` | Method doesn't use the class instance and could be converted into a static method | SAME line 368 |
| [ ] | #4 | 4554131729 | deepsource-io | major | `tests/test_hung_model_call.py:387` | Method doesn't use the class instance and could be converted into a static method | SAME line 387 |
| [ ] | #4 | 4554174265 | deepsource-io | major | `tests/test_burst_retry.py:139` | Method doesn't use the class instance and could be converted into a static method | SAME line 139 |
| [ ] | #4 | 4554174278 | deepsource-io | major | `tests/support.py:252` | Possible SQL injection vector through string-based query construction. | MOVED to 253 |
| [ ] | #4 | 4554174289 | deepsource-io | major | `tests/support.py:271` | Redefining name 'sql' from outer scope | MOVED to 272 |
| [ ] | #4 | 4554174294 | deepsource-io | critical | `tests/test_burst_retry.py:75` | Call to 'next()' should be wrapped in 'try-except' | SAME line 75 |
| [ ] | #4 | 4554174301 | deepsource-io | critical | `tests/test_flow.py:537` | Call to 'next()' should be wrapped in 'try-except' | SAME line 537 |
| [ ] | #4 | 4554174307 | deepsource-io | minor | `tests/test_crash_points.py:36` | 'subprocess.run' used without explicitly defining the value for 'check'. | SAME line 36 |
| [ ] | #4 | 4554174319 | deepsource-io | critical | `tests/test_flow.py:538` | Call to 'next()' should be wrapped in 'try-except' | SAME line 538 |
| [ ] | #4 | 4554174328 | deepsource-io | minor | `tests/test_crash_points.py:40` | 'subprocess.run' used without explicitly defining the value for 'check'. | SAME line 40 |
| [ ] | #4 | 4554174338 | deepsource-io | critical | `tests/test_flow.py:501` | Call to 'next()' should be wrapped in 'try-except' | SAME line 501 |
| [ ] | #4 | 4554174350 | deepsource-io | major | `tests/test_hung_adapter_calls.py:537` | Consider merging collapsible 'With' statements' | SAME line 537 |
| [ ] | #4 | 4554174357 | deepsource-io | major | `tests/test_hung_adapter_calls.py:540` | Lambda may not be necessary | SAME line 540 |
| [ ] | #4 | 4554174370 | deepsource-io | critical | `tests/test_hung_adapter_calls.py:759` | Call to 'next()' should be wrapped in 'try-except' | SAME line 759 |
| [ ] | #4 | 4554174378 | deepsource-io | critical | `tests/test_hung_adapter_calls.py:771` | Call to 'next()' should be wrapped in 'try-except' | SAME line 771 |
| [ ] | #4 | 4554174392 | deepsource-io | critical | `tests/test_hung_adapter_calls.py:802` | Call to 'next()' should be wrapped in 'try-except' | SAME line 802 |
| [ ] | #4 | 4554174402 | deepsource-io | major | `tests/test_hung_model_call.py:315` | Unused variable 'status' | SAME line 315 |
| [ ] | #4 | 4554174416 | deepsource-io | critical | `tests/test_hung_model_call.py:316` | Call to 'next()' should be wrapped in 'try-except' | SAME line 316 |
| [ ] | #4 | 4554174423 | deepsource-io | major | `tests/support.py:252` | Redefining name 'sql' from outer scope | MOVED to 253 |
| [ ] | #4 | 4554174428 | deepsource-io | major | `tests/conftest.py:24` | Unused argument 'session' | MOVED to 25 |
| [ ] | #4 | 4554174436 | deepsource-io | major | `tests/conftest.py:43` | Method doesn't use the class instance and could be converted into a static method | MOVED to 44 |
| [ ] | #4 | 4554174443 | deepsource-io | critical | `tests/support.py:48` | Call to 'next()' should be wrapped in 'try-except' | MOVED to 49 |
| [ ] | #4 | 4554174452 | deepsource-io | major | `tests/support.py:84` | Redefining name 'sql' from outer scope | MOVED to 85 |
| [ ] | #4 | 4554174460 | deepsource-io | major | `tests/support.py:147` | Use of assert detected. The enclosed code will be removed when compiling to optimised byte code. | MOVED to 148 |
| [ ] | #4 | 4554174475 | deepsource-io | major | `tests/support.py:245` | Redefining name 'sql' from outer scope | MOVED to 246 |
| [ ] | #4 | 4554174492 | deepsource-io | major | `tests/support.py:400` | Redefining built-in 'format' | MOVED to 401 |
| [ ] | #4 | 4554174504 | deepsource-io | minor | `tests/support.py:420` | Attribute 'close_connection' defined outside __init__ | MOVED to 421 |
| [ ] | #4 | 4554174518 | deepsource-io | minor | `tests/support.py:473` | Access to a protected member _write of a client class | MOVED to 576 |
| [ ] | #4 | 4554174529 | deepsource-io | minor | `tests/support.py:477` | Access to a protected member _getframe of a client class | MOVED to 580 |
| [ ] | #4 | 4554174540 | deepsource-io | minor | `tests/support.py:495` | Access to a protected member _drives of a client class | MOVED to 598 |
| [ ] | #4 | 4554174552 | deepsource-io | minor | `tests/support.py:496` | Access to a protected member _drives of a client class | MOVED to 599 |
| [ ] | #4 | 4554174561 | deepsource-io | minor | `tests/support.py:498` | Access to a protected member _now of a client class | MOVED to 601 |
| [ ] | #4 | 4554174573 | deepsource-io | minor | `tests/support.py:498` | Access to a protected member _workers of a client class | MOVED to 601 |
| [ ] | #4 | 4554174583 | deepsource-io | minor | `tests/support.py:499` | Access to a protected member _abandoned of a client class | MOVED to 602 |
| [ ] | #4 | 4554174596 | deepsource-io | major | `tests/test_claim_checks_and_crm_mode.py:104` | Method doesn't use the class instance and could be converted into a static method | SAME line 104 |
| [ ] | #4 | 4554174608 | deepsource-io | major | `tests/test_claim_checks_and_crm_mode.py:135` | Method doesn't use the class instance and could be converted into a static method | SAME line 135 |
| [ ] | #4 | 4554174616 | deepsource-io | major | `tests/test_claim_checks_and_crm_mode.py:138` | Method doesn't use the class instance and could be converted into a static method | SAME line 138 |
| [ ] | #4 | 4554174628 | deepsource-io | major | `tests/test_claim_checks_and_crm_mode.py:142` | Method doesn't use the class instance and could be converted into a static method | SAME line 142 |
| [ ] | #4 | 4554174633 | deepsource-io | critical | `tests/test_crash_points.py:35` | Call to 'next()' should be wrapped in 'try-except' | SAME line 35 |
| [ ] | #4 | 4554174643 | deepsource-io | major | `tests/test_desk_edge_cases.py:203` | Reimport 'sqlite3' (imported line 11) | SAME line 203 |
| [ ] | #4 | 4554174658 | deepsource-io | major | `tests/test_desk_http_edge_cases.py:468` | Unused variable 'body' | SAME line 468 |
| [ ] | #4 | 4554174666 | deepsource-io | minor | `tests/test_env_numbers.py:133` | 'subprocess.run' used without explicitly defining the value for 'check'. | SAME line 133 |
| [ ] | #4 | 4554174675 | deepsource-io | major | `tests/test_env_numbers.py:565` | Consider merging collapsible if statements | SAME line 565 |
| [ ] | #4 | 4554174681 | deepsource-io | major | `tests/test_env_numbers.py:568` | Consider merging collapsible if statements | SAME line 568 |
| [ ] | #4 | 4554174690 | deepsource-io | major | `tests/test_env_numbers.py:651` | Consider merging collapsible if statements | SAME line 651 |
| [ ] | #4 | 4554174707 | deepsource-io | major | `tests/test_env_numbers.py:657` | Consider merging collapsible if statements | SAME line 657 |
| [ ] | #4 | 4554174717 | deepsource-io | major | `tests/test_env_numbers.py:785` | Consider merging collapsible if statements | MOVED to 786 |
| [ ] | #4 | 4554174727 | deepsource-io | critical | `tests/test_flow.py:499` | Raising NoneType while only classes or instances are allowed | SAME line 499 |
| [ ] | #4 | 4554174735 | deepsource-io | major | `tests/test_followup_edge_cases.py:448` | 'log_message' doesn't contain any code | BLANK-LINE (cannot match) |
| [ ] | #4 | 4554174749 | deepsource-io | critical | `tests/test_http_guard.py:40` | Call to 'next()' should be wrapped in 'try-except' | SAME line 40 |
| [ ] | #4 | 4554174761 | deepsource-io | major | `tests/test_hubspot_probe.py:71` | 'log_message' doesn't contain any code | SAME line 71 |
| [ ] | #4 | 4554174769 | deepsource-io | critical | `tests/test_hubspot_probe.py:292` | Call to 'next()' should be wrapped in 'try-except' | MOVED to 291 |
| [ ] | #4 | 4554174777 | deepsource-io | critical | `tests/test_hubspot_probe.py:386` | Call to 'next()' should be wrapped in 'try-except' | MOVED to 385 |
| [ ] | #4 | 4554174785 | deepsource-io | major | `tests/test_hung_adapter_calls.py:368` | Method doesn't use the class instance and could be converted into a static method | SAME line 368 |
| [ ] | #4 | 4554174795 | deepsource-io | major | `tests/test_hung_model_call.py:387` | Method doesn't use the class instance and could be converted into a static method | SAME line 387 |
| [ ] | #4 | 4555583928 | codeant-ai | Major | `tests/test_hygiene.py:312` | The scan misses valid inline YAML such as 'on: [pull_request_target]', so a workflow using that secr | CHANGED (text gone) |
| [ ] | #4 | 4555600753 | codeant-ai | Major | `tests/portal_contrast_probe.js:27` | When an element or ancestor has opacity, its background fades too, but this blends only the text; th | SAME line 27 |
| [ ] | #4 | 4555601198 | codeant-ai | Major | `tests/test_reset_scripts.py:71` | The fixture's fixed 'data/reset-guard-test' directory is removed recursively, so unrelated pre-exist | MOVED to 60,74 |
| [ ] | #4 | 4555807647 | deepsource-io | minor | `tests/test_hygiene.py:102` | 'test_hygiene_scan_public' has a cyclomatic complexity of 25 with "high" risk | MOVED to 118 |
| [ ] | #4 | 4555807654 | deepsource-io | minor | `tests/test_env_numbers.py:550` | '_touches' has a cyclomatic complexity of 22 with "high" risk | SAME line 550 |
| [ ] | #4 | 4555807663 | deepsource-io | minor | `tests/test_env_numbers.py:585` | '_analyse' has a cyclomatic complexity of 30 with "very-high" risk | SAME line 585 |
| [ ] | #4 | 4555807671 | deepsource-io | minor | `tests/test_env_numbers.py:633` | '_bare_casts' has a cyclomatic complexity of 20 with "high" risk | SAME line 633 |
| [ ] | #4 | 4555807683 | deepsource-io | minor | `tests/test_env_numbers.py:727` | '_unchecked_calls' has a cyclomatic complexity of 32 with "very-high" risk | MOVED to 728 |
| [ ] | #4 | 4556197571 | deepsource-io | minor | `src/lead_desk/portal/pages/overview.js:119` | All 'var' declarations must be at the top of the function scope | SAME line 119 |
| [ ] | #4 | 4556197576 | deepsource-io | major | `src/lead_desk/portal/pages/overview.js:119` | Unexpected var, use let or const instead | SAME line 119 |
| [ ] | #4 | 4556197582 | deepsource-io | minor | `src/lead_desk/portal/pages/overview.js:119` | Variable 'jj' should be initialized on declaration | SAME line 119 |
| [ ] | #4 | 4556197590 | deepsource-io | minor | `src/lead_desk/portal/pages/overview.js:119` | Variable 'jEnd' should be initialized on declaration | SAME line 119 |
| [ ] | #4 | 4556197596 | deepsource-io | minor | `src/lead_desk/portal/pages/overview.js:122` | ["new"] is better written in dot notation | SAME line 122 |
| [ ] | #4 | 4556197607 | deepsource-io | minor | `src/lead_desk/portal/pages/overview.js:122` | ["new"] is better written in dot notation | SAME line 122 |
| [ ] | #4 | 4556197620 | deepsource-io | minor | `src/lead_desk/portal/portal.js:471` | All 'var' declarations must be at the top of the function scope | SAME line 471 |
| [ ] | #4 | 4556197630 | deepsource-io | major | `src/lead_desk/portal/portal.js:471` | Unexpected var, use let or const instead | SAME line 471 |
| [ ] | #4 | 4556197637 | deepsource-io | minor | `src/lead_desk/portal/portal.js:636` | All 'var' declarations must be at the top of the function scope | SAME line 636 |
| [ ] | #4 | 4556197647 | deepsource-io | major | `src/lead_desk/portal/portal.js:636` | Unexpected var, use let or const instead | SAME line 636 |
| [ ] | #4 | 4556197653 | deepsource-io | major | `src/lead_desk/portal/portal.js:636` | 'demoKnown' is assigned a value but never used | SAME line 636 |
| [ ] | #4 | 4556197659 | deepsource-io | minor | `tests/portal_log_probe.js:9` | ["class"] is better written in dot notation | SAME line 9 |
| [ ] | #4 | 4556197666 | deepsource-io | minor | `tests/portal_log_probe.js:17` | Variable name is too small | SAME line 17 |
| [ ] | #4 | 4556197672 | deepsource-io | minor | `tests/portal_log_probe.js:12` | Unexpected empty method 'add' | SAME line 12 |
| [ ] | #4 | 4556197675 | deepsource-io | minor | `tests/portal_log_probe.js:12` | Unexpected empty method 'remove' | SAME line 12 |
| [ ] | #4 | 4556197683 | deepsource-io | minor | `tests/portal_log_probe.js:12` | Unexpected empty method 'toggle' | SAME line 12 |
| [ ] | #4 | 4556197691 | deepsource-io | minor | `tests/portal_log_probe.js:15` | Unexpected empty method 'focus' | SAME line 15 |
| [ ] | #4 | 4556197700 | deepsource-io | minor | `tests/portal_log_probe.js:15` | Unexpected empty method 'blur' | SAME line 15 |
| [ ] | #4 | 4556197708 | deepsource-io | minor | `tests/portal_log_probe.js:28` | Unexpected string concatenation | SAME line 28 |
| [ ] | #4 | 4556197717 | deepsource-io | minor | `tests/portal_log_probe.js:29` | Variable name is too small | SAME line 29 |
| [ ] | #4 | 4556197725 | deepsource-io | minor | `tests/portal_log_probe.js:32` | Unexpected string concatenation | SAME line 32 |
| [ ] | #4 | 4556197731 | deepsource-io | minor | `tests/portal_log_probe.js:50` | Unexpected empty method 'addEventListener' | SAME line 50 |
| [ ] | #4 | 4556197738 | deepsource-io | minor | `tests/portal_log_probe.js:50` | Unexpected empty method 'addEventListener' | SAME line 50 |
| [ ] | #4 | 4556197748 | deepsource-io | minor | `tests/portal_log_probe.js:51` | Unexpected empty method 'setItem' | SAME line 51 |
| [ ] | #4 | 4556197761 | deepsource-io | minor | `tests/portal_log_probe.js:51` | Unexpected empty method 'removeItem' | SAME line 51 |
| [ ] | #4 | 4556197770 | deepsource-io | minor | `tests/portal_log_probe.js:51` | Unexpected empty method 'setItem' | SAME line 51 |
| [ ] | #4 | 4556197773 | deepsource-io | minor | `tests/portal_log_probe.js:51` | Unexpected empty method 'removeItem' | SAME line 51 |
| [ ] | #4 | 4556197778 | deepsource-io | minor | `tests/portal_log_probe.js:51` | Unexpected empty method 'scrollTo' | SAME line 51 |
| [ ] | #4 | 4556197785 | deepsource-io | minor | `tests/portal_log_probe.js:53` | Expected method shorthand | SAME line 53 |
| [ ] | #4 | 4556197791 | deepsource-io | minor | `tests/portal_log_probe.js:53` | Unexpected empty arrow function | SAME line 53 |
| [ ] | #4 | 4556197797 | deepsource-io | minor | `tests/portal_log_probe.js:61` | Unexpected string concatenation | SAME line 61 |
| [ ] | #4 | 4556197802 | deepsource-io | major | `tests/portal_log_probe.js:79` | Avoid using console in code that runs on the browser | SAME line 79 |
| [ ] | #4 | 4556234487 | deepsource-io | minor | `src/lead_desk/portal/pages/overview.js:119` | All 'var' declarations must be at the top of the function scope | SAME line 119 |
| [ ] | #4 | 4556234496 | deepsource-io | major | `src/lead_desk/portal/pages/overview.js:119` | Unexpected var, use let or const instead | SAME line 119 |
| [ ] | #4 | 4556234507 | deepsource-io | minor | `src/lead_desk/portal/pages/overview.js:119` | Variable 'jj' should be initialized on declaration | SAME line 119 |
| [ ] | #4 | 4556234514 | deepsource-io | minor | `src/lead_desk/portal/pages/overview.js:119` | Variable 'jEnd' should be initialized on declaration | SAME line 119 |
| [ ] | #4 | 4556234520 | deepsource-io | minor | `src/lead_desk/portal/pages/overview.js:122` | ["new"] is better written in dot notation | SAME line 122 |
| [ ] | #4 | 4556234529 | deepsource-io | minor | `src/lead_desk/portal/pages/overview.js:122` | ["new"] is better written in dot notation | SAME line 122 |
| [ ] | #4 | 4556234537 | deepsource-io | minor | `src/lead_desk/portal/portal.js:471` | All 'var' declarations must be at the top of the function scope | SAME line 471 |
| [ ] | #4 | 4556234547 | deepsource-io | major | `src/lead_desk/portal/portal.js:471` | Unexpected var, use let or const instead | SAME line 471 |
| [ ] | #4 | 4556234563 | deepsource-io | minor | `src/lead_desk/portal/portal.js:636` | All 'var' declarations must be at the top of the function scope | SAME line 636 |
| [ ] | #4 | 4556234571 | deepsource-io | major | `src/lead_desk/portal/portal.js:636` | Unexpected var, use let or const instead | SAME line 636 |
| [ ] | #4 | 4556234579 | deepsource-io | major | `src/lead_desk/portal/portal.js:636` | 'demoKnown' is assigned a value but never used | SAME line 636 |
| [ ] | #4 | 4557129897 | deepsource-io | minor | `scripts/n8n_api.py:145` | 'main' has a cyclomatic complexity of 16 with "high" risk | MOVED to 182 |
| [ ] | #4 | 4558289960 | deepsource-io | major | `demo_only/portal_demo.js:124` | Unexpected var, use let or const instead | SAME line 124 |
| [ ] | #4 | 4558289972 | deepsource-io | minor | `demo_only/portal_demo.js:137` | Unexpected string concatenation | SAME line 137 |
| [ ] | #4 | 4558300137 | deepsource-io | minor | `demo_only/fake_hubspot.py:209` | Attribute '_body_read' defined outside __init__ | SAME line 209 |
| [ ] | #4 | 4558300147 | deepsource-io | minor | `demo_only/fake_hubspot.py:230` | Attribute '_body_read' defined outside __init__ | SAME line 230 |
| [ ] | #4 | 4558300156 | deepsource-io | minor | `demo_only/fake_hubspot.py:335` | '_Handler._create' has a cyclomatic complexity of 17 with "high" risk | SAME line 335 |

## CodeAnt 'Nitpicks' (one conversation comment per pull request, not inline threads)

These have no thread to resolve and live only in the conversation comment named. Their final-tree status was NOT checked line by line.

| done | PR | comment id | gist (first 100 chars) | file:lines named by the bot |
|---|---|---|---|---|
| [ ] | #3 | 6834456214 | 1. When the remaining retry time is shorter than the back-off, this sleeps to the deadline and the l | `demo_only/burst.py:91` |
| [ ] | #3 | 6834456214 | 2. '--n 0' is accepted as an integer, but 'Barrier(0)' raises 'ValueError' and prevents the command  | `demo_only/burst.py:114` |
| [ ] | #3 | 6834456214 | 3. 'ThreadingHTTPServer' handles this search alongside creates and deletes, so a concurrent change c | `demo_only/fake_hubspot.py:247` |
| [ ] | #3 | 6834456214 | 4. Concurrent creates can both pass this check before either increments 'failed', causing more than  | `demo_only/fake_hubspot.py:267-268` |
| [ ] | #3 | 6834456214 | 5. Concurrent creates with different emails can both see 'hung_once' as false, so more than the firs | `demo_only/fake_hubspot.py:279-280` |
| [ ] | #3 | 6834456214 | 6. '{"mode":[]}' is valid JSON but makes 'ALIASES.get' raise 'TypeError'; the uncaught err | `demo_only/fake_model_server.py:72-75` |
| [ ] | #3 | 6834456214 | 7. 'slow_seconds' and 'hang_seconds' are stored without type checks; a string returns 200 from contr | `demo_only/fake_model_server.py:134-140` |
| [ ] | #3 | 6834456214 | 8. The first call has 'call_no == 1', so this index returns 'warm'; mixed mode therefore does not be | `demo_only/fake_model_server.py:192-194` |
| [ ] | #3 | 6834456214 | 9. Because the delay runs before '_fail' is consumed, a send already sleeping can take a later 'fail | `demo_only/fakes.py:82-85` |
| [ ] | #3 | 6834456214 | 10. '_fire' can return string statuses such as 'timeout' or 'refused'; this numeric comparison treat | `demo_only/portal_demo.js:126` |
| [ ] | #3 | 6834456214 | 11. This value is captured only on mount; if a restart changes stop-test availability, subsequent de | `demo_only/portal_demo.js:191` |
| [ ] | #3 | 6834456214 | 12. If either follow-up poll request rejects during an outage, this chain never clears 'dblBusy'; re | `demo_only/portal_demo.js:278` |
| [ ] | #3 | 6834456214 | 13. With an older fakes server that omits 'reminders' but already stores reminder emails, this fallb | `demo_only/portal_demo.py:333` |
| [ ] | #3 | 6834456214 | 14. 'step' and 'step_label' indicate an active lead flow, but empty 'steps' contradicts the response | `tests/portal_fixtures/lead-detail-later.json:83` |
| [ ] | #4 | 6834410258 | 1. An aliased import such as 'import time as wall; wall.time()' is not matched, so calendar-clock re | `tests/test_clock_steps.py:39-42` |
| [ ] | #4 | 6834410258 | 2. '_cast_aliases' ignores annotated assignments, so 'conv: Any = int' followed by 'conv(os.environ[ | `tests/test_env_numbers.py:524` |
| [ ] | #4 | 6834410258 | 3. '_unchecked_calls' ignores annotated aliases, so 'parse: Any = env_number' followed by a call wit | `tests/test_env_numbers.py:749` |
| [ ] | #4 | 6834410258 | 4. This sleep does not ensure the waiter enqueued its ticket; scheduler delays can change the observ | `tests/test_followup_edge_cases.py:55-57` |
| [ ] | #4 | 6834410258 | 5. The socket closes before 'open_http' uses its port, leaving a race where another process can bind | `tests/test_http_guard.py:29-33` |
| [ ] | #4 | 6834410258 | 6. This input is rejected by '_lower_keeps_ascii_apart' before the expanded-length check, so the tes | `tests/test_input_edge_cases.py:60` |
| [ ] | #4 | 6834410258 | 7. When 'HTTP_PROXY' is set without a loopback bypass, 'urlopen' sends this request through the prox | `tests/test_load_tools.py:678` |
| [ ] | #4 | 6834410258 | 8. 'make_book_at_schema_version_1' leaves the added 'send_started' column intact, so this legacy cas | `tests/test_migration_triggers.py:54` |
| [ ] | #4 | 6834410258 | 9. 'server.main()' reads inherited 'DESK_*' settings, so a live qualifier or public bind can exit be | `tests/test_model_stamp_and_reaper.py:319-320` |
| [ ] | #4 | 6834410258 | 10. The replacement returns the literal 'email', not 'mailSender', so the supposed unmasked mutation | `tests/test_mutants_more.py:283-285` |
| [ ] | #4 | 6834410258 | 11. If an existing demo module imports a missing 'demo_only.*' dependency, this treats it as the del | `tests/test_portal_demo.py:48-50` |
| [ ] | #4 | 6834410258 | 12. This test scans whole files, not just comments, so an ordinary use of 'we', 'our', or 'us' in co | `tests/test_portal_wording_and_masking.py:114-121` |
| [ ] | #4 | 6834410258 | 13. Each dry-fake run leaves its temporary run directory behind, including the database, logs, and r | `tests/test_real_check_dry.py:31` |
| [ ] | #4 | 6834410258 | 14. 'refresh()' makes a real connection to localhost port 1; an unrelated listener can change this t | `tests/test_review_item_edge_cases.py:156` |
| [ ] | #4 | 6834410258 | 15. 'page.clock' is unavailable in older Playwright releases; with no version pinned, this test rais | `tests/test_stage_confirm_browser.py:79` |
| [ ] | #4 | 6834410258 | 16. When a vendor host is copied into an unlisted root text file such as '.coderabbit.yaml', this sc | `tests/test_vendor_hosts.py:56` |
