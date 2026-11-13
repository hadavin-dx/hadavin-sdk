# numbers-names-check (mechanical cross-check of the docs against the code)

Tree: /tmp/realhead.pjMKqf/c. Items: 1046. MISMATCH 18, CANNOT-TELL 17, OK-tests-only 5, OK 1006

Method: every backticked token in README, SECURITY, versions.md, contract.md, docs/*.md is classified (ALL-CAPS name, test name, repo path with optional ::test or :line, bare file name, route, identifier) and looked up in the code (src, scripts, demo_only, load_tools, tools, n8n, .github) or tests; a constant followed by a number and a unit is compared to its value in constants.py; EXIT_* numbers and `DESK_X (default `v`)` pairs are compared to the code. A name found as a word anywhere is OK (it does not prove the sentence around it is right). Not checked: numbers with no constant named next to them.

| doc location | claim | where checked | verdict | note |
|---|---|---|---|---|
| README.md:88 | /health | route literal in src/demo_only | MISMATCH | /health not in code |
| README.md:88 | /fake/... | route literal in src/demo_only | MISMATCH | /fake/... not in code |
| contract.md:113 | /review/... | route literal in src/demo_only | MISMATCH | /review/... not in code |
| contract.md:3 | /fake/... | route literal in src/demo_only | MISMATCH | /fake/... not in code |
| docs/hubspot-probe.md:62 | POST /crm/v3/objects/contacts/gdpr-delete | route literal in src/demo_only | MISMATCH | /crm/v3/objects/contacts/gdpr-delete not in code |
| docs/limits.md:119 | `MAX_HANDLER_THREADS` ~ 4 files | constants.py MAX_HANDLER_THREADS = 1024 | MISMATCH | doc says 4 files, code value 1024 |
| docs/n8n-recipe.md:15 | POST /webhook/proof-run | route literal in src/demo_only | MISMATCH | /webhook/proof-run not in code |
| docs/n8n-recipe.md:58 | /fake/... | route literal in src/demo_only | MISMATCH | /fake/... not in code |
| docs/n8n-recipe.md:70 | /webhook/proof-run | route literal in src/demo_only | MISMATCH | /webhook/proof-run not in code |
| docs/portal.md:17 | POST /review/... | route literal in src/demo_only | MISMATCH | /review/... not in code |
| docs/settings.md:107 | `MAX_HANDLER_THREADS` ~ 10 s | constants.py MAX_HANDLER_THREADS = 1024 | MISMATCH | doc says 10 s, code value 1024 |
| docs/settings.md:117 | result.json | file name anywhere in tree | MISMATCH | no file of that name |
| docs/settings.md:124 | .gitleaks.toml | file name anywhere in tree | MISMATCH | no file of that name |
| docs/tests.md:79 | .gitleaks.toml | file name anywhere in tree | MISMATCH | no file of that name |
| docs/tests.md:90 | cfg.txt | file name anywhere in tree | MISMATCH | no file of that name |
| docs/tests.md:90 | x_api_key.txt | file name anywhere in tree | MISMATCH | no file of that name |
| versions.md:10 | sqlite3.sqlite_version | code and tests | MISMATCH | name not found in code or tests |
| versions.md:61 | .gitleaks.toml | file name anywhere in tree | MISMATCH | no file of that name |
| contract.md:76 | ALLOW_ANY_BASE_URL | grep src scripts demo_only tools .github tests | CANNOT-TELL | all-caps word not found in code (maybe a plain word or a foreign name) |
| contract.md:76 | MESSAGE_ID_DOMAIN | grep src scripts demo_only tools .github tests | CANNOT-TELL | all-caps word not found in code (maybe a plain word or a foreign name) |
| contract.md:76 | MAX_SENDS | grep src scripts demo_only tools .github tests | CANNOT-TELL | all-caps word not found in code (maybe a plain word or a foreign name) |
| contract.md:76 | STATS_FILE | grep src scripts demo_only tools .github tests | CANNOT-TELL | all-caps word not found in code (maybe a plain word or a foreign name) |
| contract.md:76 | KEY_FILE | grep src scripts demo_only tools .github tests | CANNOT-TELL | all-caps word not found in code (maybe a plain word or a foreign name) |
| contract.md:76 | BASE_URL | grep src scripts demo_only tools .github tests | CANNOT-TELL | all-caps word not found in code (maybe a plain word or a foreign name) |
| contract.md:76 | MAX_429_RETRIES | grep src scripts demo_only tools .github tests | CANNOT-TELL | all-caps word not found in code (maybe a plain word or a foreign name) |
| docs/hubspot-probe.md:4 | MISSING_SCOPES | grep src scripts demo_only tools .github tests | CANNOT-TELL | all-caps word not found in code (maybe a plain word or a foreign name) |
| docs/settings.md:121 | N8N_PORT | grep src scripts demo_only tools .github tests | CANNOT-TELL | all-caps word not found in code (maybe a plain word or a foreign name) |
| docs/settings.md:70 | DESK_SMTP_HOST default 127.0.0.1 | Config field of that name | CANNOT-TELL | no Config field of that name |
| docs/settings.md:70 | DESK_SMTP_FROM default desk@example.test | Config field of that name | CANNOT-TELL | no Config field of that name |
| docs/settings.md:70 | DESK_SMTP_MESSAGE_ID_DOMAIN default example.test | Config field of that name | CANNOT-TELL | no Config field of that name |
| docs/settings.md:70 | DESK_SMTP_TIMEOUT_SECONDS default 5.0 | Config field of that name | CANNOT-TELL | no Config field of that name |
| docs/settings.md:76 | DESK_SMTPP_MESSAGE_ID_DOMAIN default example.invalid | Config field of that name | CANNOT-TELL | no Config field of that name |
| docs/settings.md:76 | DESK_SMTPP_TIMEOUT_SECONDS default 5.0 | Config field of that name | CANNOT-TELL | no Config field of that name |
| docs/tests.md:28 | N8N_PORT | grep src scripts demo_only tools .github tests | CANNOT-TELL | all-caps word not found in code (maybe a plain word or a foreign name) |
| docs/tests.md:77 | PLAYWRIGHT_BROWSERS_PATH | grep src scripts demo_only tools .github tests | CANNOT-TELL | all-caps word not found in code (maybe a plain word or a foreign name) |
| contract.md:76 | MAX_CALLS | tests only | OK-tests-only |  |
| docs/settings.md:123 | LEAD_DESK_LOAD_N | tests only | OK-tests-only |  |
| docs/settings.md:123 | LEAD_DESK_LOAD_RETRY | tests only | OK-tests-only |  |
| docs/tests.md:78 | LEAD_DESK_LOAD_N | tests only | OK-tests-only |  |
| docs/tests.md:96 | EXPECT_MORE | tests only | OK-tests-only |  |
| README.md:104 | scripts/hubspot_probe.py | scripts/hubspot_probe.py | OK |  |
| README.md:11 | docs/limits.md | docs/limits.md | OK |  |
| README.md:117 | docs/settings.md | docs/settings.md | OK |  |
| README.md:118 | DESK_LEADFLOW_FILE | code (string or env use) | OK |  |
| README.md:118 | demo_only/leadflow.json | demo_only/leadflow.json | OK |  |
| README.md:120 | hs_lead_status | code or tests word | OK |  |
| README.md:120 | tests/test_lead_crm_copy.py | tests/test_lead_crm_copy.py | OK |  |
| README.md:120 | POST /leads | route literal in src/demo_only | OK |  |
| README.md:120 | DESK_BIND | code (string or env use) | OK |  |
| README.md:126 | versions.md | file name anywhere in tree | OK |  |
| README.md:126 | docs/n8n-recipe.md | docs/n8n-recipe.md | OK |  |
| README.md:130 | requirements-dev-win.txt | file name anywhere in tree | OK |  |
| README.md:130 | requirements-dev.txt | file name anywhere in tree | OK |  |
| README.md:141 | docs/real-services.md | docs/real-services.md | OK |  |
| README.md:142 | docs/why-this-code.md | docs/why-this-code.md | OK |  |
| README.md:147 | src/lead_desk/loader.py | src/lead_desk/loader.py | OK |  |
| README.md:149 | load_tools/README.md | load_tools/README.md | OK |  |
| README.md:150 | tools/hygiene.py | tools/hygiene.py | OK |  |
| README.md:161 | SECURITY.md | file name anywhere in tree | OK |  |
| README.md:24 | docs/portal.md | docs/portal.md | OK |  |
| README.md:32 | src/lead_desk | src/lead_desk | OK |  |
| README.md:41 | docs/tests.md | docs/tests.md | OK |  |
| README.md:68 | exit 2 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| README.md:86 | contract.md | file name anywhere in tree | OK |  |
| README.md:88 | /counts | route literal in src/demo_only | OK |  |
| README.md:88 | tests/test_http.py | tests/test_http.py | OK |  |
| README.md:88 | tests/test_server_hardening.py | tests/test_server_hardening.py | OK |  |
| README.md:88 | test_unparsable_target_is_json | tests/ def | OK |  |
| README.md:90 | RESET_STOP_WAIT_SECONDS | code (string or env use) | OK |  |
| README.md:90 | scripts/reset.sh | scripts/reset.sh | OK |  |
| README.md:90 | scripts/reset.ps1 | scripts/reset.ps1 | OK |  |
| SECURITY.md:19 | .github/workflows/lint.yml | .github/workflows/lint.yml | OK |  |
| SECURITY.md:19 | tests/test_hygiene.py | tests/test_hygiene.py | OK |  |
| SECURITY.md:22 | docs/settings.md | docs/settings.md | OK |  |
| SECURITY.md:24 | scripts/run_real_check.py | scripts/run_real_check.py | OK |  |
| SECURITY.md:26 | scripts/hubspot_probe.py | scripts/hubspot_probe.py | OK |  |
| SECURITY.md:26 | docs/hubspot-probe.md | docs/hubspot-probe.md | OK |  |
| SECURITY.md:27 | scripts/run_live_check.py | scripts/run_live_check.py | OK |  |
| SECURITY.md:27 | scripts/n8n_api.py | scripts/n8n_api.py | OK |  |
| SECURITY.md:28 | N8N_API_KEY_FILE | code (string or env use) | OK |  |
| SECURITY.md:28 | DESK_FAKES_URL | code (string or env use) | OK |  |
| SECURITY.md:28 | DESK_SMTP_HOST | code (string or env use) | OK |  |
| SECURITY.md:28 | DESK_BIND | code (string or env use) | OK |  |
| SECURITY.md:31 | .github/workflows/ | .github/workflows/ | OK |  |
| SECURITY.md:4 | docs/portal.md | docs/portal.md | OK |  |
| contract.md:103 | _gate_error | code or tests word | OK |  |
| contract.md:104 | Config.allowed_hosts | code or tests word | OK |  |
| contract.md:104 | DESK_ALLOWED_HOSTS | code (string or env use) | OK |  |
| contract.md:110 | DESK_BIND | code (string or env use) | OK |  |
| contract.md:113 | state_view | code or tests word | OK |  |
| contract.md:113 | POST /api/demo/crash | route literal in src/demo_only | OK |  |
| contract.md:113 | POST /api/demo/burst | route literal in src/demo_only | OK |  |
| contract.md:113 | GET /ui | route literal in src/demo_only | OK |  |
| contract.md:113 | /ui/ | route literal in src/demo_only | OK |  |
| contract.md:113 | GET /ui/<file> | route literal in src/demo_only | OK |  |
| contract.md:113 | src/lead_desk/portal/ | src/lead_desk/portal/ | OK |  |
| contract.md:113 | /ui/demo/<file> | route literal in src/demo_only | OK |  |
| contract.md:113 | GET /api/ui/summary | route literal in src/demo_only | OK |  |
| contract.md:113 | /api/ui/leads | route literal in src/demo_only | OK |  |
| contract.md:113 | /api/ui/leads/<lead_id> | route literal in src/demo_only | OK |  |
| contract.md:113 | /api/ui/review | route literal in src/demo_only | OK |  |
| contract.md:113 | /api/ui/log | route literal in src/demo_only | OK |  |
| contract.md:113 | GET /api/ui/data-map | route literal in src/demo_only | OK |  |
| contract.md:114 | desk.review_rows | code or tests word | OK |  |
| contract.md:114 | tests/test_portal_api.py | tests/test_portal_api.py | OK |  |
| contract.md:114 | src/lead_desk/portal_api.py | src/lead_desk/portal_api.py | OK |  |
| contract.md:114 | sqlite3.connect | code or tests word | OK |  |
| contract.md:114 | connect_readonly | code or tests word | OK |  |
| contract.md:114 | _snapshot | code or tests word | OK |  |
| contract.md:115 | PORTAL_MAX_INFLIGHT | constants.py / code definition | OK |  |
| contract.md:115 | summary.refused_at_door | code or tests word | OK |  |
| contract.md:115 | GET /api/ui/leads?q= | route literal in src/demo_only | OK |  |
| contract.md:116 | portal_api | code or tests word | OK |  |
| contract.md:116 | STATIC_FILE_MAX_BYTES | constants.py / code definition | OK |  |
| contract.md:117 | /api/demo/<rest> | route literal in src/demo_only | OK |  |
| contract.md:117 | DEMO_BODY_MAX | constants.py / code definition | OK |  |
| contract.md:118 | test_broken_extension_leaves_no_socket | tests/ def | OK |  |
| contract.md:118 | make_server | code or tests word | OK |  |
| contract.md:121 | POST /review/D<n>/resolve | route literal in src/demo_only | OK |  |
| contract.md:122 | tests/test_portal_layout.py | tests/test_portal_layout.py | OK |  |
| contract.md:122 | tests/test_portal_wording_and_masking.py | tests/test_portal_wording_and_masking.py | OK |  |
| contract.md:126 | Config.replies_path | code or tests word | OK |  |
| contract.md:126 | load_demo_adapters | code or tests word | OK |  |
| contract.md:126 | DESK_REPLIES_PATH | code (string or env use) | OK |  |
| contract.md:126 | loader.py | file name anywhere in tree | OK |  |
| contract.md:128 | lockfile.acquire | code or tests word | OK |  |
| contract.md:13 | GET /counts?expected=x | route literal in src/demo_only | OK |  |
| contract.md:131 | BIND_RETRY_SECONDS | constants.py / code definition | OK |  |
| contract.md:131 | EXIT_SIMULATED_KILL | constants.py / code definition | OK |  |
| contract.md:131 | `EXIT_SIMULATED_KILL` 137 | constants.py EXIT_SIMULATED_KILL = 137 | OK |  |
| contract.md:132 | _Lingerer | code or tests word | OK |  |
| contract.md:132 | LINGER_MAX_SOCKETS | constants.py / code definition | OK |  |
| contract.md:132 | DRAIN_TOTAL_SECONDS | constants.py / code definition | OK |  |
| contract.md:132 | FD_RESERVE_ITEMS | constants.py / code definition | OK |  |
| contract.md:134 | MAX_HANDLER_THREADS | constants.py / code definition | OK |  |
| contract.md:134 | exit 3 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| contract.md:135 | FDS_PER_HANDLER_THREAD | constants.py / code definition | OK |  |
| contract.md:135 | `FDS_PER_HANDLER_THREAD` ~ 4 files | constants.py FDS_PER_HANDLER_THREAD = 4 | OK |  |
| contract.md:136 | FD_RESERVE | constants.py / code definition | OK |  |
| contract.md:139 | test_connection_holds_counted_files | tests/ def | OK |  |
| contract.md:139 | test_reserve_covers_its_items | tests/ def | OK |  |
| contract.md:141 | exit 2 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| contract.md:142 | /fake/info | route literal in src/demo_only | OK |  |
| contract.md:142 | exit 1 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| contract.md:143 | EXIT_DESK_SETTING_REFUSED | constants.py / code definition | OK |  |
| contract.md:143 | db_path | code or tests word | OK |  |
| contract.md:143 | exit 4 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| contract.md:143 | exit 1 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| contract.md:144 | exit 5 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| contract.md:145 | desk.start_background() | code or tests word | OK |  |
| contract.md:147 | Desk.startup() | code or tests word | OK |  |
| contract.md:148 | ACCEPT_PAUSE_SECONDS | constants.py / code definition | OK |  |
| contract.md:148 | `ACCEPT_PAUSE_SECONDS` ~ 0.05 s | constants.py ACCEPT_PAUSE_SECONDS = 0.05 | OK |  |
| contract.md:149 | desk.stop_background() | code or tests word | OK |  |
| contract.md:149 | KeyboardInterrupt | code or tests word | OK |  |
| contract.md:150 | Desk.run_followup | code or tests word | OK |  |
| contract.md:150 | test_retry_step_error_is_pending | tests/ def | OK |  |
| contract.md:151 | differing_fields | code or tests word | OK |  |
| contract.md:152 | duplicate_with_new_info | code or tests word | OK |  |
| contract.md:152 | item_id | code or tests word | OK |  |
| contract.md:152 | src/lead_desk/desk.py | src/lead_desk/desk.py | OK |  |
| contract.md:155 | size_cap_bytes | code or tests word | OK |  |
| contract.md:155 | DRAIN_MAX_BYTES | constants.py / code definition | OK |  |
| contract.md:155 | `DRAIN_TOTAL_SECONDS` ~ 1 s | constants.py DRAIN_TOTAL_SECONDS = 1.0 | OK |  |
| contract.md:156 | HEADER_READ_DEADLINE_SECONDS | constants.py / code definition | OK |  |
| contract.md:156 | BODY_READ_DEADLINE_SECONDS | constants.py / code definition | OK |  |
| contract.md:156 | `DRAIN_TOTAL_SECONDS` ~ 1 s | constants.py DRAIN_TOTAL_SECONDS = 1.0 | OK |  |
| contract.md:156 | `HEADER_READ_DEADLINE_SECONDS` ~ 10 s | constants.py HEADER_READ_DEADLINE_SECONDS = 10.0 | OK |  |
| contract.md:156 | `BODY_READ_DEADLINE_SECONDS` ~ 10 s | constants.py BODY_READ_DEADLINE_SECONDS = 10.0 | OK |  |
| contract.md:157 | REPLY_WRITE_TIMEOUT_SECONDS | constants.py / code definition | OK |  |
| contract.md:157 | REQUEST_TIMEOUT_SECONDS | constants.py / code definition | OK |  |
| contract.md:157 | `REPLY_WRITE_TIMEOUT_SECONDS` ~ 5 s | constants.py REPLY_WRITE_TIMEOUT_SECONDS = 5.0 | OK |  |
| contract.md:157 | `REQUEST_TIMEOUT_SECONDS` ~ 30 s | constants.py REQUEST_TIMEOUT_SECONDS = 30.0 | OK |  |
| contract.md:158 | POST /review/<id>/resolve | route literal in src/demo_only | OK |  |
| contract.md:158 | request_timeout | code or tests word | OK |  |
| contract.md:158 | `BODY_READ_DEADLINE_SECONDS` ~ 10 s | constants.py BODY_READ_DEADLINE_SECONDS = 10.0 | OK |  |
| contract.md:159 | tests/test_server_hardening.py | tests/test_server_hardening.py | OK |  |
| contract.md:159 | not_found | code or tests word | OK |  |
| contract.md:160 | LISTEN_QUEUE | constants.py / code definition | OK |  |
| contract.md:161 | MAX_CONNECTIONS | constants.py / code definition | OK |  |
| contract.md:163 | EVICT_MIN_IDLE_SECONDS | constants.py / code definition | OK |  |
| contract.md:163 | `EVICT_MIN_IDLE_SECONDS` ~ 2 s | constants.py EVICT_MIN_IDLE_SECONDS = 2.0 | OK |  |
| contract.md:164 | start_work | code or tests word | OK |  |
| contract.md:167 | BUSY_WRITE_TIMEOUT_SECONDS | constants.py / code definition | OK |  |
| contract.md:167 | QUIET_DRAIN_SECONDS | constants.py / code definition | OK |  |
| contract.md:167 | `QUIET_DRAIN_SECONDS` ~ 0.05 s | constants.py QUIET_DRAIN_SECONDS = 0.05 | OK |  |
| contract.md:17 | /api/ui | route literal in src/demo_only | OK |  |
| contract.md:171 | no_descriptors | code or tests word | OK |  |
| contract.md:171 | NO_DESCRIPTORS_BACKOFF_SECONDS | constants.py / code definition | OK |  |
| contract.md:173 | send_timeout_seconds | code or tests word | OK |  |
| contract.md:178 | /ui/<file> | route literal in src/demo_only | OK |  |
| contract.md:187 | `BODY_READ_DEADLINE_SECONDS` ~ 10 s | constants.py BODY_READ_DEADLINE_SECONDS = 10.0 | OK |  |
| contract.md:190 | GET /leads/{lead_id} | route literal in src/demo_only | OK |  |
| contract.md:190 | auto_attempts | code or tests word | OK |  |
| contract.md:198 | POST /review/D{n}/resolve | route literal in src/demo_only | OK |  |
| contract.md:20 | bad_decision | code or tests word | OK |  |
| contract.md:204 | POST /leads/{lead_id}/step | route literal in src/demo_only | OK |  |
| contract.md:208 | tests/test_lead_step_route.py | tests/test_lead_step_route.py | OK |  |
| contract.md:208 | Desk.set_step | code or tests word | OK |  |
| contract.md:209 | GET /counts?expected=N | route literal in src/demo_only | OK |  |
| contract.md:212 | GET /ui/ | route literal in src/demo_only | OK |  |
| contract.md:214 | mode.demo_tools | code or tests word | OK |  |
| contract.md:214 | mode.sample_data | code or tests word | OK |  |
| contract.md:214 | mode.real_services | code or tests word | OK |  |
| contract.md:214 | needs_action | code or tests word | OK |  |
| contract.md:214 | tabs.action | code or tests word | OK |  |
| contract.md:214 | GET /api/ui/review | route literal in src/demo_only | OK |  |
| contract.md:214 | stall_seconds | code or tests word | OK |  |
| contract.md:215 | GET /api/ui/leads?q=&state=&offset=&limit=&by_email= | route literal in src/demo_only | OK |  |
| contract.md:215 | did_not_finish | code or tests word | OK |  |
| contract.md:215 | by_email | code or tests word | OK |  |
| contract.md:215 | src/lead_desk/constants.py | src/lead_desk/constants.py | OK |  |
| contract.md:217 | GET /api/ui/leads/{lead_id} | route literal in src/demo_only | OK |  |
| contract.md:217 | stage_writes_real_crm | code or tests word | OK |  |
| contract.md:217 | step_label | code or tests word | OK |  |
| contract.md:217 | crm_copy | code or tests word | OK |  |
| contract.md:217 | not_copied | code or tests word | OK |  |
| contract.md:217 | step_only | code or tests word | OK |  |
| contract.md:217 | seconds_after_first | code or tests word | OK |  |
| contract.md:217 | received_at | code or tests word | OK |  |
| contract.md:217 | first_receipt.received_at | code or tests word | OK |  |
| contract.md:217 | str.strip | code or tests word | OK |  |
| contract.md:217 | duplicates_total | code or tests word | OK |  |
| contract.md:218 | lead_id | code or tests word | OK |  |
| contract.md:219 | reason_text | code or tests word | OK |  |
| contract.md:22 | POST /leads | route literal in src/demo_only | OK |  |
| contract.md:22 | bad_envelope | code or tests word | OK |  |
| contract.md:22 | bad_step | code or tests word | OK |  |
| contract.md:22 | too_large | code or tests word | OK |  |
| contract.md:220 | GET /api/ui/log?limit=&before= | route literal in src/demo_only | OK |  |
| contract.md:220 | new_details | code or tests word | OK |  |
| contract.md:220 | lead_name | code or tests word | OK |  |
| contract.md:220 | followup_state | code or tests word | OK |  |
| contract.md:220 | bad_query | code or tests word | OK |  |
| contract.md:220 | request_id | code or tests word | OK |  |
| contract.md:220 | tests/test_portal_log.py | tests/test_portal_log.py | OK |  |
| contract.md:222 | mail_sender | code or tests word | OK |  |
| contract.md:222 | sender_address | code or tests word | OK |  |
| contract.md:222 | Qualifier.qualify | code or tests word | OK |  |
| contract.md:222 | email_key | code or tests word | OK |  |
| contract.md:222 | never_receives | code or tests word | OK |  |
| contract.md:222 | sent_to | code or tests word | OK |  |
| contract.md:222 | crm_hubspot.py | file name anywhere in tree | OK |  |
| contract.md:222 | access.bind | code or tests word | OK |  |
| contract.md:222 | host_check | code or tests word | OK |  |
| contract.md:222 | origin_check | code or tests word | OK |  |
| contract.md:222 | portal_pages_read_only | code or tests word | OK |  |
| contract.md:222 | portal_actions | code or tests word | OK |  |
| contract.md:222 | demo_controls | code or tests word | OK |  |
| contract.md:222 | encryption_at_rest | code or tests word | OK |  |
| contract.md:222 | later_decision | code or tests word | OK |  |
| contract.md:227 | POST /fake/outbox | route literal in src/demo_only | OK |  |
| contract.md:227 | GET /fake/outbox | route literal in src/demo_only | OK |  |
| contract.md:227 | GET /fake/info | route literal in src/demo_only | OK |  |
| contract.md:227 | POST /fake/crm | route literal in src/demo_only | OK |  |
| contract.md:227 | POST /fake/crm/fields | route literal in src/demo_only | OK |  |
| contract.md:227 | GET /fake/crm | route literal in src/demo_only | OK |  |
| contract.md:227 | POST /fake/control | route literal in src/demo_only | OK |  |
| contract.md:227 | POST /fake/reset | route literal in src/demo_only | OK |  |
| contract.md:227 | bad_body | code or tests word | OK |  |
| contract.md:227 | bad_control | code or tests word | OK |  |
| contract.md:231 | Crm.set_fields | code or tests word | OK |  |
| contract.md:231 | no_contact | code or tests word | OK |  |
| contract.md:231 | record_then_drop | code or tests word | OK |  |
| contract.md:231 | store_then_delay | code or tests word | OK |  |
| contract.md:231 | CrmNothingStored | code or tests word | OK |  |
| contract.md:231 | CrmError | code or tests word | OK |  |
| contract.md:232 | crm_capability | code or tests word | OK |  |
| contract.md:232 | crm_mode | code or tests word | OK |  |
| contract.md:232 | FakesState | code or tests word | OK |  |
| contract.md:234 | delay_ms | code or tests word | OK |  |
| contract.md:235 | test_reply_does_not_wait_for_send | tests/ def | OK |  |
| contract.md:238 | BURST_BACKOFF_SECONDS | constants.py / code definition | OK |  |
| contract.md:238 | BURST_BACKOFF_MAX_SECONDS | constants.py / code definition | OK |  |
| contract.md:238 | BURST_RETRY_DEADLINE_SECONDS | constants.py / code definition | OK |  |
| contract.md:24 | tests/test_input_edge_cases.py | tests/test_input_edge_cases.py | OK |  |
| contract.md:24 | tests/test_desk_edge_cases.py | tests/test_desk_edge_cases.py | OK |  |
| contract.md:24 | tests/test_desk_http_edge_cases.py | tests/test_desk_http_edge_cases.py | OK |  |
| contract.md:24 | tests/test_stamp_locks_and_budget.py | tests/test_stamp_locks_and_budget.py | OK |  |
| contract.md:24 | tests/test_model_stamp_and_reaper.py | tests/test_model_stamp_and_reaper.py | OK |  |
| contract.md:24 | tests/test_claim_checks_and_crm_mode.py | tests/test_claim_checks_and_crm_mode.py | OK |  |
| contract.md:24 | tests/test_hung_model_call.py | tests/test_hung_model_call.py | OK |  |
| contract.md:24 | tests/test_hung_adapter_calls.py | tests/test_hung_adapter_calls.py | OK |  |
| contract.md:244 | Desk.process | code or tests word | OK |  |
| contract.md:246 | internal_unstorable | code or tests word | OK |  |
| contract.md:246 | sqlite3.DataError | code or tests word | OK |  |
| contract.md:247 | gate.DECIDE_FAIL_LIMIT | code or tests word | OK |  |
| contract.md:248 | sqlite3.OperationalError | code or tests word | OK |  |
| contract.md:249 | decide_transient_errors | code or tests word | OK |  |
| contract.md:25 | rejected_envelopes | code or tests word | OK |  |
| contract.md:25 | /resolve | route literal in src/demo_only | OK |  |
| contract.md:250 | sqlite3.IntegrityError | code or tests word | OK |  |
| contract.md:250 | decide_integrity_errors | code or tests word | OK |  |
| contract.md:254 | mode_mismatch | code or tests word | OK |  |
| contract.md:258 | _label_step | code or tests word | OK |  |
| contract.md:26 | ensure_ascii | code or tests word | OK |  |
| contract.md:26 | src/lead_desk/identity.py | src/lead_desk/identity.py | OK |  |
| contract.md:260 | test_reconcile_counts | tests/ def | OK |  |
| contract.md:261 | failed_followups | code or tests word | OK |  |
| contract.md:261 | unknown_followups | code or tests word | OK |  |
| contract.md:261 | sending_followups | code or tests word | OK |  |
| contract.md:261 | pending_followups | code or tests word | OK |  |
| contract.md:261 | reaper_running | code or tests word | OK |  |
| contract.md:261 | last_reaper_pass_at | code or tests word | OK |  |
| contract.md:265 | Desk._process | code or tests word | OK |  |
| contract.md:265 | tests/test_followup_edge_cases.py | tests/test_followup_edge_cases.py | OK |  |
| contract.md:265 | Desk.review | code or tests word | OK |  |
| contract.md:266 | constants.REPLY_MAX_BYTES | code or tests word | OK |  |
| contract.md:269 | test_write_once_triggers | tests/ def | OK |  |
| contract.md:269 | outcome_reason | code or tests word | OK |  |
| contract.md:269 | decided_at | code or tests word | OK |  |
| contract.md:269 | outcome_lead_id | code or tests word | OK |  |
| contract.md:269 | payload_conflict | code or tests word | OK |  |
| contract.md:269 | tests/test_claim_ownership.py | tests/test_claim_ownership.py | OK |  |
| contract.md:269 | followups_no_delete | code or tests word | OK |  |
| contract.md:27 | invalid_email | code or tests word | OK |  |
| contract.md:270 | db._migrate | code or tests word | OK |  |
| contract.md:270 | tests/test_migration_triggers.py | tests/test_migration_triggers.py | OK |  |
| contract.md:270 | later_decisions_no_update | code or tests word | OK |  |
| contract.md:270 | later_decisions_no_delete | code or tests word | OK |  |
| contract.md:271 | receipts.payload_conflict | code or tests word | OK |  |
| contract.md:271 | followups.crm_done | code or tests word | OK |  |
| contract.md:271 | followups.auto_attempts | code or tests word | OK |  |
| contract.md:271 | followups.ambiguous_prior | code or tests word | OK |  |
| contract.md:271 | followups.send_started | code or tests word | OK |  |
| contract.md:272 | review_items | code or tests word | OK |  |
| contract.md:272 | receipts_open_ix | code or tests word | OK |  |
| contract.md:272 | followups_active_ix | code or tests word | OK |  |
| contract.md:272 | receipts_time_ix | code or tests word | OK |  |
| contract.md:272 | leads_email_key_uq | code or tests word | OK |  |
| contract.md:275 | test_backfill_classes | tests/ def | OK |  |
| contract.md:277 | db.connect | code or tests word | OK |  |
| contract.md:278 | LockUnavailableError | code or tests word | OK |  |
| contract.md:279 | Desk.__init__ | code or tests word | OK |  |
| contract.md:279 | Desk._db_path | code or tests word | OK |  |
| contract.md:28 | tests/test_ai_after_claim.py | tests/test_ai_after_claim.py | OK |  |
| contract.md:283 | _crm_step | code or tests word | OK |  |
| contract.md:288 | nothing_stored | code or tests word | OK |  |
| contract.md:288 | HttpCrm | code or tests word | OK |  |
| contract.md:289 | tests/test_crash_points.py | tests/test_crash_points.py | OK |  |
| contract.md:29 | _abort_unsent | code or tests word | OK |  |
| contract.md:291 | HttpCrm.refresh() | code or tests word | OK |  |
| contract.md:294 | test_late_refresh_keeps_newer_mode | tests/ def | OK |  |
| contract.md:294 | test_late_put_keeps_newer_mode | tests/ def | OK |  |
| contract.md:294 | HttpOutbox | code or tests word | OK |  |
| contract.md:294 | test_shipped_fake_answers_crm_mode | tests/ def | OK |  |
| contract.md:295 | _refresh_outbox | code or tests word | OK |  |
| contract.md:299 | wrong_decision | code or tests word | OK |  |
| contract.md:3 | FakeCrm | code or tests word | OK |  |
| contract.md:3 | RecordedQualifier | code or tests word | OK |  |
| contract.md:30 | ModelAnswerLost | code or tests word | OK |  |
| contract.md:301 | SendAmbiguous | code or tests word | OK |  |
| contract.md:302 | _locked_retry | code or tests word | OK |  |
| contract.md:303 | test_replay_same_source_ref | tests/ def | OK |  |
| contract.md:303 | test_replays_cannot_burn_the_cap | tests/ def | OK |  |
| contract.md:307 | start_background() | code or tests word | OK |  |
| contract.md:308 | gate.OUTBOX_REFRESH_SECONDS | code or tests word | OK |  |
| contract.md:309 | gate.REAPER_PASS_SECONDS | code or tests word | OK |  |
| contract.md:309 | gate.py | file name anywhere in tree | OK |  |
| contract.md:31 | Desk._ask_model | code or tests word | OK |  |
| contract.md:31 | MODEL_CALL_BUDGET_SECONDS | constants.py / code definition | OK |  |
| contract.md:31 | timeout_seconds | code or tests word | OK |  |
| contract.md:31 | `MODEL_CALL_BUDGET_SECONDS` ~ 9 s | constants.py MODEL_CALL_BUDGET_SECONDS = 9.0 | OK |  |
| contract.md:310 | gate.gate_for | code or tests word | OK |  |
| contract.md:310 | Desk._write | code or tests word | OK |  |
| contract.md:310 | gate.WRITE_DEADLINE_SECONDS | code or tests word | OK |  |
| contract.md:310 | gate.REQUEST_DEADLINE_SECONDS | code or tests word | OK |  |
| contract.md:311 | gate.FairSemaphore | code or tests word | OK |  |
| contract.md:311 | gate.DRIVE_MAX | code or tests word | OK |  |
| contract.md:316 | Desk._bounded | code or tests word | OK |  |
| contract.md:316 | docs/limits.md | docs/limits.md | OK |  |
| contract.md:32 | ModelTimeout | code or tests word | OK |  |
| contract.md:33 | test_reaper_survives_hung_model | tests/ def | OK |  |
| contract.md:33 | test_hung_model_spends_the_try | tests/ def | OK |  |
| contract.md:33 | test_late_answer_writes_nothing | tests/ def | OK |  |
| contract.md:34 | MODEL_HUNG_MAX | constants.py / code definition | OK |  |
| contract.md:34 | test_workers_stay_within_the_cap | tests/ def | OK |  |
| contract.md:35 | Thread.start | code or tests word | OK |  |
| contract.md:35 | RuntimeError | code or tests word | OK |  |
| contract.md:35 | ModelBusy | code or tests word | OK |  |
| contract.md:35 | last_error | code or tests word | OK |  |
| contract.md:35 | model_busy | code or tests word | OK |  |
| contract.md:35 | MODEL_BUSY_BACKOFF_SECONDS | constants.py / code definition | OK |  |
| contract.md:36 | updated_at | code or tests word | OK |  |
| contract.md:36 | test_busy_give_back_keeps_the_age | tests/ def | OK |  |
| contract.md:36 | test_busy_give_back_race_keeps_age | tests/ def | OK |  |
| contract.md:36 | _closed_kind | code or tests word | OK |  |
| contract.md:36 | test_full_model_cap_shows_the_row | tests/ def | OK |  |
| contract.md:36 | /counts | route literal in src/demo_only | OK |  |
| contract.md:36 | hung_workers | code or tests word | OK |  |
| contract.md:36 | test_hung_workers_are_counted | tests/ def | OK |  |
| contract.md:36 | test_full_cap_logs_once | tests/ def | OK |  |
| contract.md:36 | test_thread_start_failure_is_busy | tests/ def | OK |  |
| contract.md:37 | SEND_MAX_ATTEMPTS | constants.py / code definition | OK |  |
| contract.md:37 | test_hung_tries_end_in_failed | tests/ def | OK |  |
| contract.md:38 | test_reaper_needs_age_above_grace | tests/ def | OK |  |
| contract.md:39 | MODEL_GRACE_MARGIN_SECONDS | constants.py / code definition | OK |  |
| contract.md:39 | `MODEL_GRACE_MARGIN_SECONDS` ~ 15 s | constants.py MODEL_GRACE_MARGIN_SECONDS = 15.0 | OK |  |
| contract.md:40 | test_margin_counts_the_busy_wait | tests/ def | OK |  |
| contract.md:40 | constants.py | file name anywhere in tree | OK |  |
| contract.md:40 | desk.py | file name anywhere in tree | OK |  |
| contract.md:40 | is_positive_seconds | code or tests word | OK |  |
| contract.md:40 | DeskSettingRefused | code or tests word | OK |  |
| contract.md:40 | SettingRefused | code or tests word | OK |  |
| contract.md:40 | Config.from_env | code or tests word | OK |  |
| contract.md:40 | from_env | code or tests word | OK |  |
| contract.md:40 | test_bad_declared_timeout_refused | tests/ def | OK |  |
| contract.md:40 | test_declared_above_budget_is_refused | tests/ def | OK |  |
| contract.md:40 | test_huge_number_is_a_refusal | tests/ def | OK |  |
| contract.md:40 | exit 1 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| contract.md:40 | exit 4 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| contract.md:40 | exit 4 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| contract.md:42 | test_label_store_lost_claim_quiet | tests/ def | OK |  |
| contract.md:42 | test_label_store_needs_the_claim | tests/ def | OK |  |
| contract.md:43 | test_locked_stamp_cannot_ask_for_ever | tests/ def | OK |  |
| contract.md:43 | test_model_stamp_lock_spends_the_try | tests/ def | OK |  |
| contract.md:43 | test_answer_lost_real_lock_keeps_try | tests/ def | OK |  |
| contract.md:44 | ambiguous_prior | code or tests word | OK |  |
| contract.md:44 | test_answer_lost_card_not_email_left | tests/ def | OK |  |
| contract.md:44 | test_may_have_left_card_stays | tests/ def | OK |  |
| contract.md:46 | crm_done | code or tests word | OK |  |
| contract.md:46 | send_started | code or tests word | OK |  |
| contract.md:48 | crash_while_sending | code or tests word | OK |  |
| contract.md:49 | test_unsent_row_at_cap_fails_visibly | tests/ def | OK |  |
| contract.md:51 | POST /review/{item_id}/resolve | route literal in src/demo_only | OK |  |
| contract.md:52 | server.py | file name anywhere in tree | OK |  |
| contract.md:56 | replay_payload_differs | code or tests word | OK |  |
| contract.md:56 | not_actionable | code or tests word | OK |  |
| contract.md:56 | later_decisions | code or tests word | OK |  |
| contract.md:56 | already_decided | code or tests word | OK |  |
| contract.md:59 | not_sent | code or tests word | OK |  |
| contract.md:59 | crm_present | code or tests word | OK |  |
| contract.md:61 | call_still_running | code or tests word | OK |  |
| contract.md:61 | crm_unconfirmed | code or tests word | OK |  |
| contract.md:63 | POST /review/{item_id}/retry | route literal in src/demo_only | OK |  |
| contract.md:63 | GET /review | route literal in src/demo_only | OK |  |
| contract.md:64 | internal_error | code or tests word | OK |  |
| contract.md:64 | not_unknown | code or tests word | OK |  |
| contract.md:64 | in_progress | code or tests word | OK |  |
| contract.md:64 | unknown_needs_person | code or tests word | OK |  |
| contract.md:64 | not_retryable | code or tests word | OK |  |
| contract.md:65 | GET /counts?expected= | route literal in src/demo_only | OK |  |
| contract.md:65 | expected_match | code or tests word | OK |  |
| contract.md:68 | tests/crash_launcher.py | tests/crash_launcher.py | OK |  |
| contract.md:68 | lead_desk.server | code or tests word | OK |  |
| contract.md:68 | os.pathsep | code or tests word | OK |  |
| contract.md:68 | importlib.resources | code or tests word | OK |  |
| contract.md:68 | lead_desk | code or tests word | OK |  |
| contract.md:71 | requirements-dev.txt | file name anywhere in tree | OK |  |
| contract.md:71 | requirements-dev-win.txt | file name anywhere in tree | OK |  |
| contract.md:71 | requirements-browser.txt | file name anywhere in tree | OK |  |
| contract.md:71 | requirements-browser-win.txt | file name anywhere in tree | OK |  |
| contract.md:71 | versions.md | file name anywhere in tree | OK |  |
| contract.md:71 | .github/workflows/lint.yml | .github/workflows/lint.yml | OK |  |
| contract.md:74 | Config.fakes_url | code or tests word | OK |  |
| contract.md:74 | fakes_host | code or tests word | OK |  |
| contract.md:74 | fakes_port | code or tests word | OK |  |
| contract.md:75 | live_claude | code or tests word | OK |  |
| contract.md:75 | DESK_OUTBOX | code (string or env use) | OK |  |
| contract.md:75 | smtp_provider | code or tests word | OK |  |
| contract.md:75 | DESK_CRM | code (string or env use) | OK |  |
| contract.md:76 | docs/settings.md | docs/settings.md | OK |  |
| contract.md:76 | PASSWORD_FILE | code (string or env use) | OK |  |
| contract.md:76 | TIMEOUT_SECONDS | constants.py / code definition | OK |  |
| contract.md:76 | CA_FILE | code (string or env use) | OK |  |
| contract.md:77 | src/lead_desk/ | src/lead_desk/ | OK |  |
| contract.md:77 | DESK_FAKES_URL | code (string or env use) | OK |  |
| contract.md:77 | DESK_FAKES_HOST | code (string or env use) | OK |  |
| contract.md:77 | DESK_FAKES_PORT | code (string or env use) | OK |  |
| contract.md:77 | ValueError | code or tests word | OK |  |
| contract.md:77 | DESK_LATER_MODE | code (string or env use) | OK |  |
| contract.md:77 | DESK_LEADFLOW_FILE | code (string or env use) | OK |  |
| contract.md:77 | DESK_NUDGE_TO | code (string or env use) | OK |  |
| contract.md:77 | DESK_APPROVERS_FILE | code (string or env use) | OK |  |
| contract.md:77 | config.approvers | code or tests word | OK |  |
| contract.md:77 | config.approvers_label | code or tests word | OK |  |
| contract.md:77 | server.main | code or tests word | OK |  |
| contract.md:77 | loader.load_approvers | code or tests word | OK |  |
| contract.md:77 | exit 4 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| contract.md:77 | exit 4 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| contract.md:80 | demo_only/replies.json | demo_only/replies.json | OK |  |
| contract.md:81 | demo_only/canned_leads.json | demo_only/canned_leads.json | OK |  |
| contract.md:81 | test_demo_adapters | tests/ def | OK |  |
| contract.md:81 | replies.json | file name anywhere in tree | OK |  |
| contract.md:81 | canned_leads.json | file name anywhere in tree | OK |  |
| contract.md:81 | source_ref | code or tests word | OK |  |
| contract.md:81 | KeyError | code or tests word | OK |  |
| contract.md:81 | demo_only/fakes.py | demo_only/fakes.py | OK |  |
| contract.md:81 | fakes_server.py | file name anywhere in tree | OK |  |
| contract.md:81 | burst.py | file name anywhere in tree | OK |  |
| contract.md:81 | demo_only/approvers.json | demo_only/approvers.json | OK |  |
| contract.md:84 | wfile.flush() | code or tests word | OK |  |
| contract.md:84 | desk.run_followup | code or tests word | OK |  |
| contract.md:84 | SO_EXCLUSIVEADDRUSE | code (string or env use) | OK |  |
| contract.md:84 | server_bind | code or tests word | OK |  |
| contract.md:84 | PermissionError | code or tests word | OK |  |
| contract.md:87 | run_followup | code or tests word | OK |  |
| contract.md:88 | _after_claim | code or tests word | OK |  |
| contract.md:88 | _send_claimed | code or tests word | OK |  |
| contract.md:9 | receipt_id | code or tests word | OK |  |
| contract.md:90 | _claim | code or tests word | OK |  |
| contract.md:91 | _record_send_result | code or tests word | OK |  |
| contract.md:91 | _give_back | code or tests word | OK |  |
| contract.md:91 | _mark_crm | code or tests word | OK |  |
| contract.md:91 | _touch | code or tests word | OK |  |
| contract.md:91 | _requeue_sending | code or tests word | OK |  |
| contract.md:91 | _pending_to_unknown | code or tests word | OK |  |
| contract.md:96 | scripts/crash_desk.py | scripts/crash_desk.py | OK |  |
| contract.md:97 | hooks.ALL_HOOK_POINTS | code or tests word | OK |  |
| contract.md:97 | HOOK_POINTS | constants.py / code definition | OK |  |
| contract.md:97 | outbox.send | code or tests word | OK |  |
| contract.md:97 | MORE_HOOK_POINTS | constants.py / code definition | OK |  |
| contract.md:98 | SimulatedCrash | code or tests word | OK |  |
| contract.md:98 | test_crash_resume_each_point | tests/ def | OK |  |
| contract.md:98 | tests/test_flow.py | tests/test_flow.py | OK |  |
| contract.md:99 | tests/test_http.py::test_crash_d2_subprocess | tests/test_http.py | OK |  |
| contract.md:99 | tests/test_http.py | tests/test_http.py | OK |  |
| docs/hubspot-probe.md:13 | dpld_tag | code or tests word | OK |  |
| docs/hubspot-probe.md:31 | crm_hubspot.py | file name anywhere in tree | OK |  |
| docs/hubspot-probe.md:36 | SECURITY.md | file name anywhere in tree | OK |  |
| docs/hubspot-probe.md:4 | tests/test_hubspot_probe.py | tests/test_hubspot_probe.py | OK |  |
| docs/hubspot-probe.md:4 | CALL_BUDGET | constants.py / code definition | OK |  |
| docs/hubspot-probe.md:52 | HUBSPOT_PROBE_TOKEN | code (string or env use) | OK |  |
| docs/hubspot-probe.md:58 | POST /crm/v3/objects/contacts | route literal in src/demo_only | OK |  |
| docs/hubspot-probe.md:59 | PATCH /crm/v3/objects/contacts/{email}?idProperty=email | route literal in src/demo_only | OK |  |
| docs/hubspot-probe.md:61 | DELETE /crm/v3/objects/contacts/{id} | route literal in src/demo_only | OK |  |
| docs/hubspot-probe.md:61 | GET /crm/v3/owners | route literal in src/demo_only | OK |  |
| docs/hubspot-probe.md:66 | hs_lead_status | code or tests word | OK |  |
| docs/limits.md:105 | /api/ui | route literal in src/demo_only | OK |  |
| docs/limits.md:105 | refused_at_door | code or tests word | OK |  |
| docs/limits.md:114 | tests/test_later_approval.py | tests/test_later_approval.py | OK |  |
| docs/limits.md:116 | /api/ui/leads?by_email=1 | route literal in src/demo_only | OK |  |
| docs/limits.md:116 | test_later_values_word_for_word | tests/ def | OK |  |
| docs/limits.md:116 | test_later_lower_receipt_number | tests/ def | OK |  |
| docs/limits.md:116 | test_later_review_verdict_not_listed | tests/ def | OK |  |
| docs/limits.md:116 | test_later_repeat_still_listed | tests/ def | OK |  |
| docs/limits.md:116 | test_later_reply_size_is_bounded | tests/ def | OK |  |
| docs/limits.md:116 | test_leads_email_search_needs_reveal | tests/ def | OK |  |
| docs/limits.md:116 | test_personal_hidden_rule | tests/ def | OK |  |
| docs/limits.md:116 | test_reveal_one_value_rules | tests/ def | OK |  |
| docs/limits.md:116 | test_log_calls_carry_no_values | tests/ def | OK |  |
| docs/limits.md:116 | test_later_messages_log_no_values | tests/ def | OK |  |
| docs/limits.md:117 | tests/test_portal_wording_and_masking.py | tests/test_portal_wording_and_masking.py | OK |  |
| docs/limits.md:117 | tests/test_later_messages.py | tests/test_later_messages.py | OK |  |
| docs/limits.md:117 | src/lead_desk | src/lead_desk | OK |  |
| docs/limits.md:118 | REPLY_WRITE_TIMEOUT_SECONDS | constants.py / code definition | OK |  |
| docs/limits.md:118 | `REPLY_WRITE_TIMEOUT_SECONDS` ~ 5 s | constants.py REPLY_WRITE_TIMEOUT_SECONDS = 5.0 | OK |  |
| docs/limits.md:119 | MAX_HANDLER_THREADS | constants.py / code definition | OK |  |
| docs/limits.md:120 | exit 3 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/limits.md:121 | BIND_RETRY_SECONDS | constants.py / code definition | OK |  |
| docs/limits.md:123 | MAX_CONNECTIONS | constants.py / code definition | OK |  |
| docs/limits.md:124 | test_idle_sockets_closed_at_deadline | tests/ def | OK |  |
| docs/limits.md:125 | HEADER_READ_DEADLINE_SECONDS | constants.py / code definition | OK |  |
| docs/limits.md:125 | `BODY_READ_DEADLINE_SECONDS` ~ 10 s | constants.py BODY_READ_DEADLINE_SECONDS = 10.0 | OK |  |
| docs/limits.md:126 | EVICT_MIN_IDLE_SECONDS | constants.py / code definition | OK |  |
| docs/limits.md:126 | `EVICT_MIN_IDLE_SECONDS` ~ 2 s | constants.py EVICT_MIN_IDLE_SECONDS = 2.0 | OK |  |
| docs/limits.md:127 | /leads | route literal in src/demo_only | OK |  |
| docs/limits.md:134 | src/lead_desk/config.py | src/lead_desk/config.py | OK |  |
| docs/limits.md:134 | exceptions.txt | file name anywhere in tree | OK |  |
| docs/limits.md:138 | tests/test_mirror_gate.py | tests/test_mirror_gate.py | OK |  |
| docs/limits.md:138 | tests/test_stage_confirm_browser.py | tests/test_stage_confirm_browser.py | OK |  |
| docs/limits.md:138 | tests/test_mode_safety.py | tests/test_mode_safety.py | OK |  |
| docs/limits.md:142 | hs_lead_status | code or tests word | OK |  |
| docs/limits.md:142 | DESK_LEADFLOW_FILE | code (string or env use) | OK |  |
| docs/limits.md:142 | tests/test_lead_crm_copy.py | tests/test_lead_crm_copy.py | OK |  |
| docs/limits.md:148 | ATTEMPTED_TO_CONTACT | code (string or env use) | OK |  |
| docs/limits.md:148 | OPEN_DEAL | code (string or env use) | OK |  |
| docs/limits.md:15 | scripts/hubspot_probe.py | scripts/hubspot_probe.py | OK |  |
| docs/limits.md:154 | src/lead_desk/crm_hubspot.py | src/lead_desk/crm_hubspot.py | OK |  |
| docs/limits.md:26 | docs/hubspot-probe.md | docs/hubspot-probe.md | OK |  |
| docs/limits.md:29 | docs/settings.md | docs/settings.md | OK |  |
| docs/limits.md:31 | Desk._bounded | code or tests word | OK |  |
| docs/limits.md:32 | MODEL_CALL_BUDGET_SECONDS | constants.py / code definition | OK |  |
| docs/limits.md:32 | `MODEL_CALL_BUDGET_SECONDS` ~ 9 s | constants.py MODEL_CALL_BUDGET_SECONDS = 9.0 | OK |  |
| docs/limits.md:37 | test_reaper_survives_hung_model | tests/ def | OK |  |
| docs/limits.md:37 | test_hung_model_spends_the_try | tests/ def | OK |  |
| docs/limits.md:38 | test_late_answer_writes_nothing | tests/ def | OK |  |
| docs/limits.md:38 | test_blind_send_timeout_is_unknown | tests/ def | OK |  |
| docs/limits.md:38 | test_keyed_send_timeout_same_key | tests/ def | OK |  |
| docs/limits.md:39 | test_blind_crm_timeout_is_unknown | tests/ def | OK |  |
| docs/limits.md:39 | test_late_send_writes_nothing | tests/ def | OK |  |
| docs/limits.md:39 | test_late_crm_put_writes_nothing | tests/ def | OK |  |
| docs/limits.md:40 | ADAPTER_WORKER_CAPS | constants.py / code definition | OK |  |
| docs/limits.md:42 | stall_seconds | code or tests word | OK |  |
| docs/limits.md:42 | test_busy_give_back_keeps_the_age | tests/ def | OK |  |
| docs/limits.md:43 | test_full_model_cap_shows_the_row | tests/ def | OK |  |
| docs/limits.md:43 | test_blind_call_for_lead_blocks_claim | tests/ def | OK |  |
| docs/limits.md:44 | /counts | route literal in src/demo_only | OK |  |
| docs/limits.md:45 | hung_workers | code or tests word | OK |  |
| docs/limits.md:51 | crm_error | code or tests word | OK |  |
| docs/limits.md:52 | test_busy_lead_waits_longer_each_time | tests/ def | OK |  |
| docs/limits.md:53 | not_sent | code or tests word | OK |  |
| docs/limits.md:53 | call_still_running | code or tests word | OK |  |
| docs/limits.md:54 | test_blind_retry_waits_for_old_send | tests/ def | OK |  |
| docs/limits.md:58 | timeout_seconds | code or tests word | OK |  |
| docs/limits.md:58 | exit 1 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/limits.md:59 | db_path | code or tests word | OK |  |
| docs/limits.md:59 | exit 4 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/limits.md:62 | test_locked_stamp_cannot_ask_for_ever | tests/ def | OK |  |
| docs/limits.md:62 | test_answer_lost_real_lock_keeps_try | tests/ def | OK |  |
| docs/limits.md:64 | test_late_refresh_keeps_newer_mode | tests/ def | OK |  |
| docs/limits.md:67 | tests/test_slow_sender.py | tests/test_slow_sender.py | OK |  |
| docs/limits.md:67 | tests/test_stall_eviction.py | tests/test_stall_eviction.py | OK |  |
| docs/limits.md:69 | tests/test_reminder_email.py | tests/test_reminder_email.py | OK |  |
| docs/limits.md:70 | load_tools/README.md | load_tools/README.md | OK |  |
| docs/limits.md:71 | DESK_BIND | code (string or env use) | OK |  |
| docs/limits.md:72 | versions.md | file name anywhere in tree | OK |  |
| docs/limits.md:72 | .github/workflows/lint.yml | .github/workflows/lint.yml | OK |  |
| docs/limits.md:74 | reminder_until | code or tests word | OK |  |
| docs/limits.md:74 | no_state | code or tests word | OK |  |
| docs/limits.md:77 | _restamp_future | code or tests word | OK |  |
| docs/limits.md:77 | src/lead_desk/desk.py | src/lead_desk/desk.py | OK |  |
| docs/limits.md:77 | tests/test_clock_steps.py | tests/test_clock_steps.py | OK |  |
| docs/limits.md:78 | SEND_MAX_ATTEMPTS | constants.py / code definition | OK |  |
| docs/limits.md:79 | ModelAnswerLost | code or tests word | OK |  |
| docs/limits.md:80 | tests/test_model_stamp_and_reaper.py | tests/test_model_stamp_and_reaper.py | OK |  |
| docs/limits.md:81 | REAPER_PASS_SECONDS | constants.py / code definition | OK |  |
| docs/limits.md:81 | stop_background | code or tests word | OK |  |
| docs/limits.md:81 | test_stop_waits_only_its_timeout | tests/ def | OK |  |
| docs/limits.md:86 | rejected_envelopes | code or tests word | OK |  |
| docs/limits.md:86 | failed_followups | code or tests word | OK |  |
| docs/limits.md:86 | decide_transient_errors | code or tests word | OK |  |
| docs/limits.md:86 | decide_integrity_errors | code or tests word | OK |  |
| docs/limits.md:86 | test_reconcile_counts | tests/ def | OK |  |
| docs/limits.md:88 | test_write_once_triggers | tests/ def | OK |  |
| docs/limits.md:88 | tests/test_migration_triggers.py | tests/test_migration_triggers.py | OK |  |
| docs/limits.md:92 | tests/test_http.py::test_ten_parallel | tests/test_http.py | OK |  |
| docs/limits.md:93 | LISTEN_QUEUE | constants.py / code definition | OK |  |
| docs/limits.md:93 | src/lead_desk/constants.py | src/lead_desk/constants.py | OK |  |
| docs/limits.md:95 | load_tools/load_driver.py | load_tools/load_driver.py | OK |  |
| docs/limits.md:95 | BURST_BACKOFF_SECONDS | constants.py / code definition | OK |  |
| docs/limits.md:95 | BURST_BACKOFF_MAX_SECONDS | constants.py / code definition | OK |  |
| docs/limits.md:95 | BURST_RETRY_DEADLINE_SECONDS | constants.py / code definition | OK |  |
| docs/limits.md:95 | constants.py | file name anywhere in tree | OK |  |
| docs/limits.md:95 | tests/test_burst_retry.py | tests/test_burst_retry.py | OK |  |
| docs/limits.md:96 | src/lead_desk/server.py | src/lead_desk/server.py | OK |  |
| docs/limits.md:97 | demo_only/fake_hubspot.py | demo_only/fake_hubspot.py | OK |  |
| docs/limits.md:97 | tests/test_codeant_fakes.py | tests/test_codeant_fakes.py | OK |  |
| docs/limits.md:98 | request_timeout | code or tests word | OK |  |
| docs/limits.md:98 | BODY_READ_DEADLINE_SECONDS | constants.py / code definition | OK |  |
| docs/limits.md:98 | POST /leads | route literal in src/demo_only | OK |  |
| docs/limits.md:98 | POST /review/<id>/resolve | route literal in src/demo_only | OK |  |
| docs/n8n-recipe.md:12 | /webhook/desk-form | route literal in src/demo_only | OK |  |
| docs/n8n-recipe.md:25 | docs/settings.md | docs/settings.md | OK |  |
| docs/n8n-recipe.md:26 | DESK_BIND | code (string or env use) | OK |  |
| docs/n8n-recipe.md:26 | forbidden_host | code or tests word | OK |  |
| docs/n8n-recipe.md:26 | DESK_ALLOWED_HOSTS | code (string or env use) | OK |  |
| docs/n8n-recipe.md:27 | scripts/n8n_api.py | scripts/n8n_api.py | OK |  |
| docs/n8n-recipe.md:27 | N8N_URL | code (string or env use) | OK |  |
| docs/n8n-recipe.md:34 | submission_id | code or tests word | OK |  |
| docs/n8n-recipe.md:34 | message_id | code or tests word | OK |  |
| docs/n8n-recipe.md:4 | versions.md | file name anywhere in tree | OK |  |
| docs/n8n-recipe.md:44 | source_ref | code or tests word | OK |  |
| docs/n8n-recipe.md:44 | /leads | route literal in src/demo_only | OK |  |
| docs/n8n-recipe.md:48 | payload.name | code or tests word | OK |  |
| docs/n8n-recipe.md:48 | from_name | code or tests word | OK |  |
| docs/n8n-recipe.md:48 | payload.email | code or tests word | OK |  |
| docs/n8n-recipe.md:48 | from_email | code or tests word | OK |  |
| docs/n8n-recipe.md:48 | payload.message | code or tests word | OK |  |
| docs/n8n-recipe.md:58 | contract.md | file name anywhere in tree | OK |  |
| docs/n8n-recipe.md:70 | demo_only/burst.py | demo_only/burst.py | OK |  |
| docs/n8n-recipe.md:70 | tests/test_n8n_proof_result.py | tests/test_n8n_proof_result.py | OK |  |
| docs/n8n-recipe.md:70 | n8n/proof.json | n8n/proof.json | OK |  |
| docs/n8n-recipe.md:70 | src/lead_desk/server.py | src/lead_desk/server.py | OK |  |
| docs/n8n-recipe.md:74 | desk-form.json | file name anywhere in tree | OK |  |
| docs/n8n-recipe.md:74 | desk-webhook.json | file name anywhere in tree | OK |  |
| docs/n8n-recipe.md:74 | proof.json | file name anywhere in tree | OK |  |
| docs/n8n-recipe.md:74 | docs/n8n-recipe.md | docs/n8n-recipe.md | OK |  |
| docs/n8n-recipe.md:77 | n8n/desk-form.json | n8n/desk-form.json | OK |  |
| docs/portal.md:11 | /review | route literal in src/demo_only | OK |  |
| docs/portal.md:17 | GET /api/ui/... | route literal in src/demo_only | OK |  |
| docs/portal.md:19 | POST /api/demo/crash | route literal in src/demo_only | OK |  |
| docs/portal.md:19 | POST /api/demo/burst | route literal in src/demo_only | OK |  |
| docs/portal.md:21 | DESK_ALLOWED_HOSTS | code (string or env use) | OK |  |
| docs/portal.md:21 | contract.md | file name anywhere in tree | OK |  |
| docs/portal.md:23 | tests/test_portal_api.py | tests/test_portal_api.py | OK |  |
| docs/portal.md:3 | DESK_LEADFLOW_FILE | code (string or env use) | OK |  |
| docs/portal.md:5 | tests/test_portal_layout.py | tests/test_portal_layout.py | OK |  |
| docs/portal.md:5 | tests/test_portal_wording_and_masking.py | tests/test_portal_wording_and_masking.py | OK |  |
| docs/portal.md:5 | test_name_search_needs_reveal | tests/ def | OK |  |
| docs/portal.md:5 | tests/test_portal_lead_pages.py | tests/test_portal_lead_pages.py | OK |  |
| docs/real-services.md:11 | scripts/real-run.env.example | scripts/real-run.env.example | OK |  |
| docs/real-services.md:12 | docs/limits.md | docs/limits.md | OK |  |
| docs/real-services.md:13 | hadavin_lead_id | code or tests word | OK |  |
| docs/real-services.md:13 | src/lead_desk/crm_hubspot.py | src/lead_desk/crm_hubspot.py | OK |  |
| docs/real-services.md:13 | tests/test_crm_hubspot.py | tests/test_crm_hubspot.py | OK |  |
| docs/real-services.md:16 | tests/test_load_tools.py | tests/test_load_tools.py | OK |  |
| docs/real-services.md:16 | src/lead_desk/imap_count.py | src/lead_desk/imap_count.py | OK |  |
| docs/real-services.md:20 | docs/settings.md | docs/settings.md | OK |  |
| docs/real-services.md:22 | DESK_DB_PATH | constants.py / code definition | OK |  |
| docs/real-services.md:22 | REAL_RESULT_FILE | code (string or env use) | OK |  |
| docs/real-services.md:22 | tests/test_path_confinement.py | tests/test_path_confinement.py | OK |  |
| docs/real-services.md:22 | load_tools/README.md | load_tools/README.md | OK |  |
| docs/real-services.md:22 | LEAD_DESK_PATH_ROOTS | code (string or env use) | OK |  |
| docs/real-services.md:5 | tests/test_real_check_dry.py | tests/test_real_check_dry.py | OK |  |
| docs/real-services.md:7 | scripts/hubspot_probe.py | scripts/hubspot_probe.py | OK |  |
| docs/real-services.md:7 | docs/hubspot-probe.md | docs/hubspot-probe.md | OK |  |
| docs/real-services.md:9 | scripts/run_real_check.py | scripts/run_real_check.py | OK |  |
| docs/real-services.md:9 | tests/test_smtp_provider.py | tests/test_smtp_provider.py | OK |  |
| docs/settings.md:10 | DESK_ADAPTERS | code (string or env use) | OK |  |
| docs/settings.md:100 | LIVE_DEFAULT_BASE_URL | constants.py / code definition | OK |  |
| docs/settings.md:100 | scripts/run_real_check.py | scripts/run_real_check.py | OK |  |
| docs/settings.md:100 | scripts/run_live_check.py | scripts/run_live_check.py | OK |  |
| docs/settings.md:101 | DESK_LIVE_ALLOW_ANY_BASE_URL | code (string or env use) | OK |  |
| docs/settings.md:102 | DESK_LIVE_API_VERSION | code (string or env use) | OK |  |
| docs/settings.md:102 | DESK_LIVE_EFFORT | code (string or env use) | OK |  |
| docs/settings.md:102 | output_config | code or tests word | OK |  |
| docs/settings.md:104 | src/lead_desk/trace.py | src/lead_desk/trace.py | OK |  |
| docs/settings.md:107 | MAX_CONNECTIONS | constants.py / code definition | OK |  |
| docs/settings.md:107 | MAX_HANDLER_THREADS | constants.py / code definition | OK |  |
| docs/settings.md:11 | DESK_QUALIFIER | code (string or env use) | OK |  |
| docs/settings.md:11 | live_claude | code or tests word | OK |  |
| docs/settings.md:111 | LIVE_KEY_MIN_CHARS | constants.py / code definition | OK |  |
| docs/settings.md:112 | LIVE_LEDGER_FILE_MAX_BYTES | constants.py / code definition | OK |  |
| docs/settings.md:116 | scripts/real-run.env.example | scripts/real-run.env.example | OK |  |
| docs/settings.md:116 | REAL_IMAP_1_USER | constants.py / code definition | OK |  |
| docs/settings.md:116 | REAL_IMAP_1_PASSWORD_FILE | constants.py / code definition | OK |  |
| docs/settings.md:116 | REAL_IMAP_2_USER | constants.py / code definition | OK |  |
| docs/settings.md:116 | REAL_IMAP_2_PASSWORD_FILE | constants.py / code definition | OK |  |
| docs/settings.md:116 | exit 2 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/settings.md:117 | REAL_DRAIN_SECONDS | code (string or env use) | OK |  |
| docs/settings.md:117 | REAL_MAIL_WAIT_SECONDS | code (string or env use) | OK |  |
| docs/settings.md:117 | REAL_MAIL_SETTLE_SECONDS | code (string or env use) | OK |  |
| docs/settings.md:117 | REAL_RESULT_FILE | code (string or env use) | OK |  |
| docs/settings.md:119 | REAL_IMAP_n_USER | code or tests word | OK |  |
| docs/settings.md:119 | PASSWORD_FILE | code (string or env use) | OK |  |
| docs/settings.md:119 | MAIL_IMAP_DEFAULT_HOST | constants.py / code definition | OK |  |
| docs/settings.md:119 | CA_FILE | code (string or env use) | OK |  |
| docs/settings.md:119 | MAIL_SPAM_FOLDER | constants.py / code definition | OK |  |
| docs/settings.md:12 | DESK_OUTBOX | code (string or env use) | OK |  |
| docs/settings.md:12 | smtp_provider | code or tests word | OK |  |
| docs/settings.md:12 | tests/test_smtp_outbox.py | tests/test_smtp_outbox.py | OK |  |
| docs/settings.md:12 | tests/test_smtp_provider.py | tests/test_smtp_provider.py | OK |  |
| docs/settings.md:121 | scripts/n8n_api.py | scripts/n8n_api.py | OK |  |
| docs/settings.md:121 | N8N_URL | code (string or env use) | OK |  |
| docs/settings.md:121 | N8N_API_KEY_FILE | code (string or env use) | OK |  |
| docs/settings.md:121 | is_loopback_host | code or tests word | OK |  |
| docs/settings.md:121 | HTTP_PROXY | code (string or env use) | OK |  |
| docs/settings.md:121 | no_proxy | code or tests word | OK |  |
| docs/settings.md:121 | docs/n8n-recipe.md | docs/n8n-recipe.md | OK |  |
| docs/settings.md:121 | exit 1 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/settings.md:122 | tools/scrub_n8n_export.py | tools/scrub_n8n_export.py | OK |  |
| docs/settings.md:122 | tests/test_hygiene.py | tests/test_hygiene.py | OK |  |
| docs/settings.md:122 | //host/path | route literal in src/demo_only | OK |  |
| docs/settings.md:122 | /webhook/<token> | route literal in src/demo_only | OK |  |
| docs/settings.md:123 | tests/test_server_hardening.py | tests/test_server_hardening.py | OK |  |
| docs/settings.md:123 | test_measure_burst | tests/ def | OK |  |
| docs/settings.md:124 | DPLD_REQUIRE_SCAN | code (string or env use) | OK |  |
| docs/settings.md:124 | GITLEAKS_BIN | code (string or env use) | OK |  |
| docs/settings.md:124 | .github/workflows/lint.yml | .github/workflows/lint.yml | OK |  |
| docs/settings.md:125 | LEAD_DESK_PATH_ROOTS | code (string or env use) | OK |  |
| docs/settings.md:125 | load_tools/README.md | load_tools/README.md | OK |  |
| docs/settings.md:125 | docs/real-services.md | docs/real-services.md | OK |  |
| docs/settings.md:126 | DPLD_REQUIRE_DEMO | code (string or env use) | OK |  |
| docs/settings.md:126 | tests/conftest.py | tests/conftest.py | OK |  |
| docs/settings.md:126 | demo_only | code or tests word | OK |  |
| docs/settings.md:126 | lint.yml | file name anywhere in tree | OK |  |
| docs/settings.md:126 | sonar.yml | file name anywhere in tree | OK |  |
| docs/settings.md:126 | exit 2 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/settings.md:13 | tests/test_crm_hubspot.py | tests/test_crm_hubspot.py | OK |  |
| docs/settings.md:13 | scripts/hubspot_probe.py | scripts/hubspot_probe.py | OK |  |
| docs/settings.md:14 | later_mode | code or tests word | OK |  |
| docs/settings.md:14 | DESK_LATER_MODE | code (string or env use) | OK |  |
| docs/settings.md:15 | approvers_path | code or tests word | OK |  |
| docs/settings.md:15 | DESK_APPROVERS_FILE | code (string or env use) | OK |  |
| docs/settings.md:15 | approvers.json | file name anywhere in tree | OK |  |
| docs/settings.md:16 | leadflow_path | code or tests word | OK |  |
| docs/settings.md:16 | DESK_LEADFLOW_FILE | code (string or env use) | OK |  |
| docs/settings.md:16 | after_followup | code or tests word | OK |  |
| docs/settings.md:16 | reminder_until | code or tests word | OK |  |
| docs/settings.md:16 | nudge_after_seconds | code or tests word | OK |  |
| docs/settings.md:16 | demo_only/leadflow.json | demo_only/leadflow.json | OK |  |
| docs/settings.md:16 | scripts/start_all.ps1 | scripts/start_all.ps1 | OK |  |
| docs/settings.md:16 | scripts/start_all.sh | scripts/start_all.sh | OK |  |
| docs/settings.md:16 | docs/limits.md | docs/limits.md | OK |  |
| docs/settings.md:16 | exit 4 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/settings.md:17 | nudge_to | code or tests word | OK |  |
| docs/settings.md:17 | DESK_NUDGE_TO | code (string or env use) | OK |  |
| docs/settings.md:18 | fakes_host | code or tests word | OK |  |
| docs/settings.md:18 | fakes_port | code or tests word | OK |  |
| docs/settings.md:18 | DESK_FAKES_HOST | code (string or env use) | OK |  |
| docs/settings.md:18 | DESK_FAKES_PORT | code (string or env use) | OK |  |
| docs/settings.md:19 | DESK_FAKES_URL | code (string or env use) | OK |  |
| docs/settings.md:20 | replies_path | code or tests word | OK |  |
| docs/settings.md:20 | DESK_REPLIES_PATH | code (string or env use) | OK |  |
| docs/settings.md:20 | replies.json | file name anywhere in tree | OK |  |
| docs/settings.md:21 | send_timeout_seconds | code or tests word | OK |  |
| docs/settings.md:21 | DESK_SEND_TIMEOUT_SECONDS | code (string or env use) | OK |  |
| docs/settings.md:22 | size_cap_bytes | code or tests word | OK |  |
| docs/settings.md:22 | DESK_SIZE_CAP_BYTES | code (string or env use) | OK |  |
| docs/settings.md:23 | stall_seconds | code or tests word | OK |  |
| docs/settings.md:23 | DESK_STALL_SECONDS | code (string or env use) | OK |  |
| docs/settings.md:24 | allowed_hosts | code or tests word | OK |  |
| docs/settings.md:24 | DESK_ALLOWED_HOSTS | code (string or env use) | OK |  |
| docs/settings.md:24 | scripts/feed.py | scripts/feed.py | OK |  |
| docs/settings.md:28 | src/lead_desk/constants.py | src/lead_desk/constants.py | OK |  |
| docs/settings.md:28 | DESK_LIVE_BASE_URL | code (string or env use) | OK |  |
| docs/settings.md:28 | DESK_HUBSPOT_BASE_URL | code (string or env use) | OK |  |
| docs/settings.md:28 | exit 4 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/settings.md:3 | src/lead_desk/config.py | src/lead_desk/config.py | OK |  |
| docs/settings.md:33 | DESK_SMTP_PORT | code (string or env use) | OK |  |
| docs/settings.md:33 | DESK_SMTPP_PORT | code (string or env use) | OK |  |
| docs/settings.md:34 | SIZE_CAP_BYTES_MAX | constants.py / code definition | OK |  |
| docs/settings.md:35 | STALL_SECONDS_MAX | constants.py / code definition | OK |  |
| docs/settings.md:36 | DESK_SMTP_TIMEOUT_SECONDS | code (string or env use) | OK |  |
| docs/settings.md:36 | SEND_TIMEOUT_SECONDS_MAX | constants.py / code definition | OK |  |
| docs/settings.md:37 | DESK_SMTPP_TIMEOUT_SECONDS | code (string or env use) | OK |  |
| docs/settings.md:37 | DESK_HUBSPOT_TIMEOUT_SECONDS | code (string or env use) | OK |  |
| docs/settings.md:37 | CALL_DEADLINE_MAX_SECONDS | constants.py / code definition | OK |  |
| docs/settings.md:38 | DESK_SMTPP_MAX_SENDS | constants.py / code definition | OK |  |
| docs/settings.md:38 | DESK_HUBSPOT_MAX_CALLS | constants.py / code definition | OK |  |
| docs/settings.md:38 | CAP_COUNT_MAX | constants.py / code definition | OK |  |
| docs/settings.md:39 | DESK_HUBSPOT_MAX_429_RETRIES | code (string or env use) | OK |  |
| docs/settings.md:40 | NUDGE_AFTER_MAX_SECONDS | constants.py / code definition | OK |  |
| docs/settings.md:41 | DESK_LIVE_TIMEOUT_SECONDS | code (string or env use) | OK |  |
| docs/settings.md:41 | DESK_LIVE_MAX_TOKENS | code (string or env use) | OK |  |
| docs/settings.md:41 | LIVE_MAX_TOKENS_MAX | constants.py / code definition | OK |  |
| docs/settings.md:42 | REAL_PERSONS | code (string or env use) | OK |  |
| docs/settings.md:42 | REAL_PERSONS_MAX | constants.py / code definition | OK |  |
| docs/settings.md:42 | REAL_HUBSPOT_READBACK_MAX_CALLS | constants.py / code definition | OK |  |
| docs/settings.md:46 | constants.py | file name anywhere in tree | OK |  |
| docs/settings.md:46 | config.py | file name anywhere in tree | OK |  |
| docs/settings.md:46 | exit 4 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/settings.md:50 | LEADFLOW_FILE_MAX_BYTES | constants.py / code definition | OK |  |
| docs/settings.md:51 | LEADFLOW_ROTA_MAX | constants.py / code definition | OK |  |
| docs/settings.md:51 | crm_owner_id | code or tests word | OK |  |
| docs/settings.md:53 | LEADFLOW_NAME_MAX | constants.py / code definition | OK |  |
| docs/settings.md:54 | LEADFLOW_STEPS_MAX | constants.py / code definition | OK |  |
| docs/settings.md:54 | crm_status | code or tests word | OK |  |
| docs/settings.md:55 | LEADFLOW_LABEL_MAX | constants.py / code definition | OK |  |
| docs/settings.md:62 | no_state | code or tests word | OK |  |
| docs/settings.md:68 | example.test | code or tests word | OK |  |
| docs/settings.md:68 | docs/hubspot-probe.md | docs/hubspot-probe.md | OK |  |
| docs/settings.md:7 | db_path | code or tests word | OK |  |
| docs/settings.md:7 | DESK_DB_PATH | constants.py / code definition | OK |  |
| docs/settings.md:7 | exit 4 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/settings.md:70 | DESK_SMTP_HOST | code (string or env use) | OK |  |
| docs/settings.md:70 | DESK_SMTP_FROM | code (string or env use) | OK |  |
| docs/settings.md:70 | DESK_SMTP_MESSAGE_ID_DOMAIN | code (string or env use) | OK |  |
| docs/settings.md:70 | `CALL_DEADLINE_MAX_SECONDS` ~ 9 seconds | constants.py CALL_DEADLINE_MAX_SECONDS = 9.0 | OK |  |
| docs/settings.md:74 | DESK_SMTPP_HOST | constants.py / code definition | OK |  |
| docs/settings.md:74 | DESK_SMTPP_USER | constants.py / code definition | OK |  |
| docs/settings.md:74 | DESK_SMTPP_PASSWORD_FILE | constants.py / code definition | OK |  |
| docs/settings.md:74 | DESK_SMTPP_FROM | constants.py / code definition | OK |  |
| docs/settings.md:74 | DESK_SMTPP_RECIPIENTS | constants.py / code definition | OK |  |
| docs/settings.md:74 | DESK_SMTPP_SECURITY | code (string or env use) | OK |  |
| docs/settings.md:76 | DESK_SMTPP_MESSAGE_ID_DOMAIN | code (string or env use) | OK |  |
| docs/settings.md:76 | example.invalid | code or tests word | OK |  |
| docs/settings.md:78 | DESK_SMTPP_STATS_FILE | code (string or env use) | OK |  |
| docs/settings.md:78 | DESK_SMTPP_CA_FILE | code (string or env use) | OK |  |
| docs/settings.md:8 | DESK_BIND | code (string or env use) | OK |  |
| docs/settings.md:8 | DESK_CRM | code (string or env use) | OK |  |
| docs/settings.md:82 | DESK_HUBSPOT_KEY_FILE | constants.py / code definition | OK |  |
| docs/settings.md:84 | HUBSPOT_BASE_URL | constants.py / code definition | OK |  |
| docs/settings.md:84 | DESK_HUBSPOT_STATS_FILE | code (string or env use) | OK |  |
| docs/settings.md:85 | DESK_HUBSPOT_ALLOW_ANY_BASE_URL | code (string or env use) | OK |  |
| docs/settings.md:87 | exit 4 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/settings.md:9 | DESK_PORT | code (string or env use) | OK |  |
| docs/settings.md:95 | DESK_LIVE_MODEL | code (string or env use) | OK |  |
| docs/settings.md:96 | DESK_LIVE_KEY_FILE | code (string or env use) | OK |  |
| docs/settings.md:97 | DESK_LIVE_PRICE_IN_PER_MTOK | code (string or env use) | OK |  |
| docs/settings.md:97 | DESK_LIVE_PRICE_OUT_PER_MTOK | code (string or env use) | OK |  |
| docs/settings.md:97 | DESK_LIVE_PRICE_DATE | code (string or env use) | OK |  |
| docs/settings.md:98 | DESK_LIVE_CAP_RUN_USD | code (string or env use) | OK |  |
| docs/settings.md:98 | DESK_LIVE_CAP_TOTAL_USD | code (string or env use) | OK |  |
| docs/settings.md:99 | DESK_LIVE_LEDGER_PATH | code (string or env use) | OK |  |
| docs/settings.md:99 | DESK_LIVE_RUN_ID | code (string or env use) | OK |  |
| docs/tests.md:101 | tests/test_crash_points.py | tests/test_crash_points.py | OK |  |
| docs/tests.md:104 | crm_unconfirmed | code or tests word | OK |  |
| docs/tests.md:111 | tests/test_portal_log_poll.py | tests/test_portal_log_poll.py | OK |  |
| docs/tests.md:111 | tests/test_codeant_demo_only.py | tests/test_codeant_demo_only.py | OK |  |
| docs/tests.md:111 | tests/test_n8n_proof_result.py | tests/test_n8n_proof_result.py | OK |  |
| docs/tests.md:113 | src/lead_desk/hooks.py | src/lead_desk/hooks.py | OK |  |
| docs/tests.md:113 | tests/test_reminder_email.py | tests/test_reminder_email.py | OK |  |
| docs/tests.md:120 | test_cross_source_dupe | tests/ def | OK |  |
| docs/tests.md:120 | test_dupe_diff_first_untouched | tests/ def | OK |  |
| docs/tests.md:120 | test_write_once_triggers | tests/ def | OK |  |
| docs/tests.md:120 | test_replay_same_source_ref | tests/ def | OK |  |
| docs/tests.md:120 | test_concurrent_same_source_ref | tests/ def | OK |  |
| docs/tests.md:121 | test_dedupe_before_ai | tests/ def | OK |  |
| docs/tests.md:122 | test_incomplete_to_review | tests/ def | OK |  |
| docs/tests.md:123 | test_crash_resume_each_point | tests/ def | OK |  |
| docs/tests.md:123 | tests/test_http.py::test_crash_d2_subprocess | tests/test_http.py | OK |  |
| docs/tests.md:123 | tests/test_http.py | tests/test_http.py | OK |  |
| docs/tests.md:124 | tests/test_http.py::test_ten_parallel | tests/test_http.py | OK |  |
| docs/tests.md:124 | test_reconcile_counts | tests/ def | OK |  |
| docs/tests.md:125 | test_unknown_blind | tests/ def | OK |  |
| docs/tests.md:125 | test_failed_retry | tests/ def | OK |  |
| docs/tests.md:125 | test_retry_twice_concurrent | tests/ def | OK |  |
| docs/tests.md:126 | test_later_first_record_untouched | tests/ def | OK |  |
| docs/tests.md:127 | strip() | code or tests word | OK |  |
| docs/tests.md:127 | src/lead_desk/identity.py | src/lead_desk/identity.py | OK |  |
| docs/tests.md:127 | test_later_values_word_for_word | tests/ def | OK |  |
| docs/tests.md:127 | test_later_seconds_after_first | tests/ def | OK |  |
| docs/tests.md:127 | test_later_lower_receipt_number | tests/ def | OK |  |
| docs/tests.md:127 | test_later_order_by_receipt_number | tests/ def | OK |  |
| docs/tests.md:127 | test_later_burst_ten_each_own_values | tests/ def | OK |  |
| docs/tests.md:127 | test_lead_detail_lists_at_most_the_cap | tests/ def | OK |  |
| docs/tests.md:127 | test_later_reply_size_is_bounded | tests/ def | OK |  |
| docs/tests.md:127 | test_time_after_first_words | tests/ def | OK |  |
| docs/tests.md:128 | test_later_messages_never_call_the_ai | tests/ def | OK |  |
| docs/tests.md:128 | test_later_reply_keys_are_fixed | tests/ def | OK |  |
| docs/tests.md:129 | src/lead_desk/portal/portal.js | src/lead_desk/portal/portal.js | OK |  |
| docs/tests.md:129 | print() | code or tests word | OK |  |
| docs/tests.md:129 | demo_only | code or tests word | OK |  |
| docs/tests.md:129 | test_personal_hidden_rule | tests/ def | OK |  |
| docs/tests.md:129 | test_reveal_one_value_rules | tests/ def | OK |  |
| docs/tests.md:129 | test_later_panel_rules_in_the_source | tests/ def | OK |  |
| docs/tests.md:129 | test_leads_email_search_needs_reveal | tests/ def | OK |  |
| docs/tests.md:129 | test_name_search_needs_reveal | tests/ def | OK |  |
| docs/tests.md:129 | test_demo_pick_lists_neutral | tests/ def | OK |  |
| docs/tests.md:129 | test_log_calls_carry_no_values | tests/ def | OK |  |
| docs/tests.md:129 | test_later_messages_log_no_values | tests/ def | OK |  |
| docs/tests.md:131 | tests/test_input_edge_cases.py | tests/test_input_edge_cases.py | OK |  |
| docs/tests.md:133 | /counts | route literal in src/demo_only | OK |  |
| docs/tests.md:133 | src/lead_desk/desk.py | src/lead_desk/desk.py | OK |  |
| docs/tests.md:135 | load_tools/README.md | load_tools/README.md | OK |  |
| docs/tests.md:137 | test_mutant_no_unique_key | tests/ def | OK |  |
| docs/tests.md:137 | test_mutant_no_claim | tests/ def | OK |  |
| docs/tests.md:144 | /fake/crm | route literal in src/demo_only | OK |  |
| docs/tests.md:19 | .github/workflows/sonar.yml | .github/workflows/sonar.yml | OK |  |
| docs/tests.md:24 | pyproject.toml | file name anywhere in tree | OK |  |
| docs/tests.md:24 | sonar.python.coverage.reportPaths | code or tests word | OK |  |
| docs/tests.md:28 | N8N_URL | code (string or env use) | OK |  |
| docs/tests.md:28 | N8N_API_KEY_FILE | code (string or env use) | OK |  |
| docs/tests.md:28 | docs/n8n-recipe.md | docs/n8n-recipe.md | OK |  |
| docs/tests.md:28 | docs/settings.md | docs/settings.md | OK |  |
| docs/tests.md:28 | docs/limits.md | docs/limits.md | OK |  |
| docs/tests.md:30 | .github/workflows/lint.yml | .github/workflows/lint.yml | OK |  |
| docs/tests.md:30 | .github/workflows/codeql.yml | .github/workflows/codeql.yml | OK |  |
| docs/tests.md:30 | .github/workflows/semgrep.yml | .github/workflows/semgrep.yml | OK |  |
| docs/tests.md:30 | sonar.yml | file name anywhere in tree | OK |  |
| docs/tests.md:30 | .github/dependabot.yml | .github/dependabot.yml | OK |  |
| docs/tests.md:30 | test_workflows_are_pinned_and_limited | tests/ def | OK |  |
| docs/tests.md:30 | SONAR_TOKEN | code (string or env use) | OK |  |
| docs/tests.md:30 | tools/hygiene.py | tools/hygiene.py | OK |  |
| docs/tests.md:34 | requirements-semgrep.txt | file name anywhere in tree | OK |  |
| docs/tests.md:34 | load_tools | code or tests word | OK |  |
| docs/tests.md:34 | lint.yml | file name anywhere in tree | OK |  |
| docs/tests.md:34 | tests/test_nosemgrep_form.py | tests/test_nosemgrep_form.py | OK |  |
| docs/tests.md:34 | github.head_ref | code or tests word | OK |  |
| docs/tests.md:34 | github.ref_name | code or tests word | OK |  |
| docs/tests.md:34 | exit 2 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/tests.md:34 | exit 2 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/tests.md:36 | exit 0 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/tests.md:42 | exit 2 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/tests.md:42 | exit 3 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/tests.md:42 | exit 0 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/tests.md:42 | exit 0 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/tests.md:42 | exit 0 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/tests.md:42 | exit 2 | EXIT_* constants in constants.py (+1 for traceback) | OK |  |
| docs/tests.md:48 | requirements-dev.txt | file name anywhere in tree | OK |  |
| docs/tests.md:48 | requirements-dev-win.txt | file name anywhere in tree | OK |  |
| docs/tests.md:48 | requirements-coverage.txt | file name anywhere in tree | OK |  |
| docs/tests.md:52 | tests/test_portal_browser.py | tests/test_portal_browser.py | OK |  |
| docs/tests.md:52 | tests/test_portal_lead_pages.py | tests/test_portal_lead_pages.py | OK |  |
| docs/tests.md:52 | tests/test_stage_confirm_browser.py | tests/test_stage_confirm_browser.py | OK |  |
| docs/tests.md:52 | tests/test_portal_wording_and_masking.py | tests/test_portal_wording_and_masking.py | OK |  |
| docs/tests.md:52 | tests/test_mode_safety.py | tests/test_mode_safety.py | OK |  |
| docs/tests.md:52 | tests/test_portal_layout.py | tests/test_portal_layout.py | OK |  |
| docs/tests.md:52 | tests/test_portal_look.py | tests/test_portal_look.py | OK |  |
| docs/tests.md:52 | tests/test_portal_phone_layout.py | tests/test_portal_phone_layout.py | OK |  |
| docs/tests.md:52 | tests/test_portal_long_values.py | tests/test_portal_long_values.py | OK |  |
| docs/tests.md:52 | tests/test_portal_drawer_long_name.py | tests/test_portal_drawer_long_name.py | OK |  |
| docs/tests.md:54 | requirements-browser.txt | file name anywhere in tree | OK |  |
| docs/tests.md:54 | requirements-browser-win.txt | file name anywhere in tree | OK |  |
| docs/tests.md:78 | tests/test_hygiene.py | tests/test_hygiene.py | OK |  |
| docs/tests.md:78 | tests/test_gitleaks_exceptions.py | tests/test_gitleaks_exceptions.py | OK |  |
| docs/tests.md:78 | tests/test_gitleaks_semgrep_lock.py | tests/test_gitleaks_semgrep_lock.py | OK |  |
| docs/tests.md:79 | tests/test_except_clause_hierarchy.py | tests/test_except_clause_hierarchy.py | OK |  |
| docs/tests.md:79 | tests/test_lead_crm_copy.py | tests/test_lead_crm_copy.py | OK |  |
| docs/tests.md:79 | tests/test_portal_mode.py | tests/test_portal_mode.py | OK |  |
| docs/tests.md:79 | exceptions.txt | file name anywhere in tree | OK |  |
| docs/tests.md:80 | test_mode_safety.py | file name anywhere in tree | OK |  |
| docs/tests.md:80 | test_portal_browser.py | file name anywhere in tree | OK |  |
| docs/tests.md:80 | test_portal_lead_pages.py | file name anywhere in tree | OK |  |
| docs/tests.md:80 | test_portal_mode.py | file name anywhere in tree | OK |  |
| docs/tests.md:80 | test_portal_wording_and_masking.py | file name anywhere in tree | OK |  |
| docs/tests.md:80 | test_portal_layout.py | file name anywhere in tree | OK |  |
| docs/tests.md:80 | test_portal_look.py | file name anywhere in tree | OK |  |
| docs/tests.md:80 | test_stage_confirm_browser.py | file name anywhere in tree | OK |  |
| docs/tests.md:86 | contract.md | file name anywhere in tree | OK |  |
| docs/tests.md:88 | GITLEAKS_BIN | code (string or env use) | OK |  |
| docs/tests.md:90 | notes.properties | code or tests word | OK |  |
| docs/tests.md:92 | patterns.txt | file name anywhere in tree | OK |  |
| docs/tests.md:92 | sonar.projectKey | code or tests word | OK |  |
| docs/tests.md:92 | test_hygiene_scan_public | tests/ def | OK |  |
| docs/tests.md:96 | tests/test_flow.py | tests/test_flow.py | OK |  |
| docs/why-this-code.md:13 | tests/test_crash_points.py | tests/test_crash_points.py | OK |  |
| docs/why-this-code.md:13 | src/lead_desk/desk.py | src/lead_desk/desk.py | OK |  |
| docs/why-this-code.md:13 | gate.py | file name anywhere in tree | OK |  |
| docs/why-this-code.md:13 | db.py | file name anywhere in tree | OK |  |
| docs/why-this-code.md:14 | docs/limits.md | docs/limits.md | OK |  |
| docs/why-this-code.md:15 | http.server | code or tests word | OK |  |
| docs/why-this-code.md:19 | src/lead_desk/crm_hubspot.py | src/lead_desk/crm_hubspot.py | OK |  |
| docs/why-this-code.md:19 | smtp_provider.py | file name anywhere in tree | OK |  |
| docs/why-this-code.md:19 | imap_count.py | file name anywhere in tree | OK |  |
| docs/why-this-code.md:19 | live_claude.py | file name anywhere in tree | OK |  |
| docs/why-this-code.md:19 | scripts/hubspot_probe.py | scripts/hubspot_probe.py | OK |  |
| docs/why-this-code.md:19 | scripts/run_real_check.py | scripts/run_real_check.py | OK |  |
| docs/why-this-code.md:20 | load_tools/load_driver.py | load_tools/load_driver.py | OK |  |
| docs/why-this-code.md:20 | load_tools/README.md | load_tools/README.md | OK |  |
| docs/why-this-code.md:21 | load_tools/check_invariants.py | load_tools/check_invariants.py | OK |  |
| docs/why-this-code.md:22 | demo_only/portal_demo.py | demo_only/portal_demo.py | OK |  |
| docs/why-this-code.md:22 | demo_only/burst.py | demo_only/burst.py | OK |  |
| docs/why-this-code.md:28 | src/lead_desk/contract.py | src/lead_desk/contract.py | OK |  |
| docs/why-this-code.md:28 | src/lead_desk/constants.py | src/lead_desk/constants.py | OK |  |
| docs/why-this-code.md:28 | CRM_CHOICES | constants.py / code definition | OK |  |
| docs/why-this-code.md:28 | OUTBOX_CHOICES | constants.py / code definition | OK |  |
| docs/why-this-code.md:28 | smtp_provider | code or tests word | OK |  |
| docs/why-this-code.md:28 | QUALIFIER_CHOICES | constants.py / code definition | OK |  |
| docs/why-this-code.md:28 | live_claude | code or tests word | OK |  |
| docs/why-this-code.md:28 | src/lead_desk/loader.py | src/lead_desk/loader.py | OK |  |
| docs/why-this-code.md:28 | tests/test_mode_safety.py | tests/test_mode_safety.py | OK |  |
| docs/why-this-code.md:28 | constants.py | file name anywhere in tree | OK |  |
| docs/why-this-code.md:28 | CRM_FIELDS_SENT | constants.py / code definition | OK |  |
| docs/why-this-code.md:28 | real_services | code or tests word | OK |  |
| docs/why-this-code.md:28 | loader.py | file name anywhere in tree | OK |  |
| docs/why-this-code.md:28 | src/lead_desk/smtp_provider.py | src/lead_desk/smtp_provider.py | OK |  |
| docs/why-this-code.md:28 | OUTBOX_STAND_INS | constants.py / code definition | OK |  |
| docs/why-this-code.md:28 | Config.real_services | code or tests word | OK |  |
| docs/why-this-code.md:28 | config.py | file name anywhere in tree | OK |  |
| docs/why-this-code.md:28 | portal_api.py | file name anywhere in tree | OK |  |
| docs/why-this-code.md:28 | src/lead_desk/adapters.py | src/lead_desk/adapters.py | OK |  |
| docs/why-this-code.md:28 | src/lead_desk/ | src/lead_desk/ | OK |  |
| docs/why-this-code.md:28 | test_no_demo_only_outside_loader | tests/ def | OK |  |
| docs/why-this-code.md:28 | tests/test_hygiene.py | tests/test_hygiene.py | OK |  |
| docs/why-this-code.md:28 | demo_only | code or tests word | OK |  |
| docs/why-this-code.md:28 | docs/hubspot-probe.md | docs/hubspot-probe.md | OK |  |
| docs/why-this-code.md:7 | docs/tests.md | docs/tests.md | OK |  |
| versions.md:10 | src/lead_desk/desk.py | src/lead_desk/desk.py | OK |  |
| versions.md:19 | docs/n8n-recipe.md | docs/n8n-recipe.md | OK |  |
| versions.md:24 | LIVE_API_VERSION | constants.py / code definition | OK |  |
| versions.md:28 | .github/workflows/ | .github/workflows/ | OK |  |
| versions.md:34 | sonar.yml | file name anywhere in tree | OK |  |
| versions.md:37 | lint.yml | file name anywhere in tree | OK |  |
| versions.md:40 | requirements-dev.txt | file name anywhere in tree | OK |  |
| versions.md:40 | requirements-dev-win.txt | file name anywhere in tree | OK |  |
| versions.md:46 | .github/workflows/lint.yml | .github/workflows/lint.yml | OK |  |
| versions.md:57 | requirements-browser.txt | file name anywhere in tree | OK |  |
| versions.md:57 | requirements-browser-win.txt | file name anywhere in tree | OK |  |
| versions.md:61 | tests/test_hygiene.py | tests/test_hygiene.py | OK |  |
| versions.md:61 | exceptions.txt | file name anywhere in tree | OK |  |
| versions.md:61 | test_exceptions_narrow | tests/ def | OK |  |
| versions.md:74 | SO_EXCLUSIVEADDRUSE | code (string or env use) | OK |  |
| versions.md:74 | PermissionError | code or tests word | OK |  |
