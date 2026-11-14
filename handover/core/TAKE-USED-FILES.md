# Take used-core-files list (fix-19 box, part 1)

Written 2026-11-14 by the laptop take builder. Take head: 27a1ed8 (worktree dpld-fix19). Patch: handover2/handover/core/fix/core-fix-on-frozen-r7n-lf.patch, 162 files (from `grep ^diff --git`).

Method: a small Python `ast` walk (run with -I) from scripts/run_real_check.py, following `import` and `from x import y` statements (module level and inside functions) to files under src/, scripts/, tools/, demo_only/, load_tools/. Then I read run_real_check.py, crash_desk.py, loader.py and server.py imports by hand for what the walk cannot see (child processes, importlib). Non-Python runtime files (schema.sql, demo_only json, portal assets) and tests were not walked.

Counts: 88 patch files have no counterpart in the take (all tests/ and docs/ new files plus 12 src/scripts/tools files named below); 74 have a counterpart.

## Python files outside tests/

| patch file | counterpart in take | imported by the take run | why |
|---|---|---|---|
| demo_only/bad_request.py | NO | n/a | file does not exist in the take (new in the patch); the take run cannot import it, but changed take files may need it (not checked) |
| demo_only/burst.py | yes | no (static) | not reached by the import walk; may run as a separate script (not checked) |
| demo_only/fake_hubspot.py | yes | yes | static import chain from scripts/run_real_check.py |
| demo_only/fake_imap.py | yes | yes | static import chain from scripts/run_real_check.py |
| demo_only/fake_model_server.py | yes | yes | static import chain from scripts/run_real_check.py |
| demo_only/fake_smtp_tls.py | yes | yes | static import chain from scripts/run_real_check.py |
| demo_only/fakes.py | yes | yes (dynamic) | loader.py line 81 import_module("demo_only.fakes") when adapters=demo; whether the real-check run selects demo adapters was not checked |
| demo_only/fakes_server.py | yes | UNVERIFIED | not found imported by the run; not opened |
| demo_only/portal_demo.py | yes | yes (dynamic) | loader.py line 38 import_module("demo_only.portal_demo"), only when adapters=demo; not checked for the real-check run |
| load_tools/catcher.py | yes | no (static) | not reached by the import walk; may run as a separate script (not checked) |
| load_tools/check_invariants.py | yes | yes | static import chain from scripts/run_real_check.py |
| load_tools/load_driver.py | yes | yes | static import chain from scripts/run_real_check.py |
| scripts/check_schema.py | yes | no (static) | not reached by the import walk; may run as a separate script (not checked) |
| scripts/crash_desk.py | yes | yes (child process) | run_real_check.py line 1048 starts it with sys.executable; it imports config, hooks, server |
| scripts/desk_setting.py | NO | n/a | file does not exist in the take (new in the patch); the take run cannot import it, but changed take files may need it (not checked) |
| scripts/feed.py | yes | no (static) | not reached by the import walk; may run as a separate script (not checked) |
| scripts/http_guard.py | yes | yes | static import chain from scripts/run_real_check.py |
| scripts/hubspot_probe.py | yes | no (static) | not reached by the import walk; may run as a separate script (not checked) |
| scripts/n8n_api.py | yes | no (static) | not reached by the import walk; may run as a separate script (not checked) |
| scripts/refusals.py | NO | n/a | file does not exist in the take (new in the patch); the take run cannot import it, but changed take files may need it (not checked) |
| scripts/reset_check.py | NO | n/a | file does not exist in the take (new in the patch); the take run cannot import it, but changed take files may need it (not checked) |
| scripts/run_live_check.py | yes | no (static) | not reached by the import walk; may run as a separate script (not checked) |
| scripts/run_real_check.py | yes | yes | static import chain from scripts/run_real_check.py |
| src/lead_desk/adapters.py | yes | yes | static import chain from scripts/run_real_check.py |
| src/lead_desk/config.py | yes | yes | static import chain from scripts/run_real_check.py |
| src/lead_desk/constants.py | yes | yes | static import chain from scripts/run_real_check.py |
| src/lead_desk/crm_hubspot.py | yes | yes | static import chain from scripts/run_real_check.py |
| src/lead_desk/db.py | yes | yes | static import chain from scripts/run_real_check.py |
| src/lead_desk/desk.py | yes | yes | static import chain from scripts/run_real_check.py |
| src/lead_desk/envnum.py | yes | yes | static import chain from scripts/run_real_check.py |
| src/lead_desk/errcode.py | NO | n/a | file does not exist in the take (new in the patch); the take run cannot import it, but changed take files may need it (not checked) |
| src/lead_desk/hooks.py | yes | yes | static import chain from scripts/run_real_check.py |
| src/lead_desk/imap_count.py | yes | yes | static import chain from scripts/run_real_check.py |
| src/lead_desk/jsonread.py | NO | n/a | file does not exist in the take (new in the patch); the take run cannot import it, but changed take files may need it (not checked) |
| src/lead_desk/live_claude.py | yes | yes | static import chain from scripts/run_real_check.py |
| src/lead_desk/lockfile.py | yes | yes (child process) | imported by server.py (line 33) |
| src/lead_desk/netconnect.py | NO | n/a | file does not exist in the take (new in the patch); the take run cannot import it, but changed take files may need it (not checked) |
| src/lead_desk/portal_api.py | yes | yes | static import chain from scripts/run_real_check.py |
| src/lead_desk/regfile.py | NO | n/a | file does not exist in the take (new in the patch); the take run cannot import it, but changed take files may need it (not checked) |
| src/lead_desk/run_stats.py | yes | yes | static import chain from scripts/run_real_check.py |
| src/lead_desk/scrub.py | NO | n/a | file does not exist in the take (new in the patch); the take run cannot import it, but changed take files may need it (not checked) |
| src/lead_desk/server.py | yes | yes (child process) | imported by scripts/crash_desk.py, which run_real_check.py spawns |
| src/lead_desk/smtp_outbox.py | yes | yes | static import chain from scripts/run_real_check.py |
| src/lead_desk/smtp_provider.py | yes | yes | static import chain from scripts/run_real_check.py |
| src/lead_desk/tls_trust.py | NO | n/a | file does not exist in the take (new in the patch); the take run cannot import it, but changed take files may need it (not checked) |
| src/lead_desk/trace.py | yes | UNVERIFIED | no static import found from the run; not opened |
| tools/pathconfine.py | NO | n/a | file does not exist in the take (new in the patch); the take run cannot import it, but changed take files may need it (not checked) |
| tools/refusing_args.py | NO | n/a | file does not exist in the take (new in the patch); the take run cannot import it, but changed take files may need it (not checked) |
| tools/scrub_n8n_export.py | yes | no (static) | not reached by the import walk; may run as a separate script (not checked) |

## Other files

| patch file | counterpart in take | imported by the take run | why |
|---|---|---|---|
| CHANGELOG.md | NO | n/a (not Python) | docs/data file; runtime use not checked |
| README.md | yes | n/a (not Python) | docs/data file; runtime use not checked |
| contract.md | yes | n/a (not Python) | docs/data file; runtime use not checked |
| docs/hubspot-probe.md | yes | n/a (not Python) | docs/data file; runtime use not checked |
| docs/limits.md | yes | n/a (not Python) | docs/data file; runtime use not checked |
| docs/real-services.md | yes | n/a (not Python) | docs/data file; runtime use not checked |
| docs/settings.md | yes | n/a (not Python) | docs/data file; runtime use not checked |
| load_tools/README.md | yes | n/a (not Python) | docs/data file; runtime use not checked |
| scripts/reset.ps1 | yes | n/a (not Python) | docs/data file; runtime use not checked |
| scripts/reset.sh | yes | n/a (not Python) | docs/data file; runtime use not checked |
| scripts/start_all.ps1 | yes | n/a (not Python) | docs/data file; runtime use not checked |
| scripts/start_all.sh | yes | n/a (not Python) | docs/data file; runtime use not checked |
| tests/conftest.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/support.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_ai_after_claim.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_book_folder_refusals.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_burst_retry.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_ca_file_reads.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_cli_refusals.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_codeant_demo_only.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_codeant_hygiene.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_crash_flag_reads.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_crash_points.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_crm_hubspot.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_demo_folder_guard.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_desk_http_edge_cases.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_env_numbers.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_except_clause_hierarchy.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_file_call_guard.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_file_reader_refusals.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_followup_b.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_followup_edge_cases.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_gitleaks_exceptions.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_hubspot_probe.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_hung_model_call.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_hygiene.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_lead_step_route.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_ledger_amounts.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_ledger_and_bind_retry.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_live_claude.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_load_driver_facts.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_load_tools.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_mode_safety.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_mutation_guards.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_n8n_api_url.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_n8n_proof_result.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_no_placeholders.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_no_terminal_questions.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_nosemgrep_form.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_path_confinement.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_portal_demo.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_portal_lead_pages.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_portal_log_poll.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_portal_mode.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r4_refusals.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r5_refusals.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r6_refusals.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7_class_names.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7_exit_codes.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7_fake_bad_requests.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7_fake_slow_senders.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7_inputs_and_replies.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7_mail_context.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7_no_replace_of_special.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7b_burst_closed_port.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7b_fake_deep_and_head.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7b_guard_replant.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7b_portal_view_cap.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7b_program_helper.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7c_bad_request_layers.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7c_burst_probe_and_names.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7c_clean_tree_guard.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7c_head_deadline_errors.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7c_invariants_output_size.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7c_mail6_killers.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7c_mail_killers.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7c_model_fake_cli.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7c_one_json_loader.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7c_portal_view_size.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7c_program_helper_rejects.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7c_reset_exact_command.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7c_smtp_reply_total_cap.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7c_start_all_parity.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7d_findings.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7e_findings.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7f_findings.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7g_findings.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7h_findings.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7i_findings.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7j_findings.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7k_findings.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7l_findings.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7m_new.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_r7n_findings.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_real_check_dry.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_regfile_limits_in_constants.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_reminder_email.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_reset_ps1_links.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_reset_scripts.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_review_item_edge_cases.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_script_number_limits.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_script_refusals_feed.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_scrub_n8n_export.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_smtp_outbox.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_smtp_provider.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_sonar_p2_feed_optional.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_special_files_and_plain_text.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_special_output_files.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_stamp_locks_and_budget.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_tools_and_fakes_pipes.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_vendor_hosts.py | yes | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/test_wrapper_setting_refusals.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |
| tests/tree_guard.py | NO | no (test file) | tests are not run by the take run itself; they matter for the suite merge |

## Summary

- Take run imports (static walk, 29 files incl. run_real_check itself): demo_only/fake_hubspot.py, demo_only/fake_imap.py, demo_only/fake_model_server.py, demo_only/fake_smtp_tls.py, load_tools/check_invariants.py, load_tools/load_driver.py, scripts/env_guard.py, scripts/http_guard.py, scripts/run_real_check.py, src/lead_desk/__init__.py, src/lead_desk/adapters.py, src/lead_desk/config.py, src/lead_desk/constants.py, src/lead_desk/contract.py, src/lead_desk/crm_hubspot.py, src/lead_desk/db.py, src/lead_desk/desk.py, src/lead_desk/envnum.py, src/lead_desk/gate.py, src/lead_desk/hooks.py, src/lead_desk/identity.py, src/lead_desk/imap_count.py, src/lead_desk/lazy_opener.py, src/lead_desk/live_claude.py, src/lead_desk/loader.py, src/lead_desk/portal_api.py, src/lead_desk/run_stats.py, src/lead_desk/smtp_outbox.py, src/lead_desk/smtp_provider.py.
- Added by hand (child process / importlib): scripts/crash_desk.py, src/lead_desk/server.py, src/lead_desk/lockfile.py; demo_only/fakes.py and demo_only/portal_demo.py when adapters=demo.
- Patch-only modules with no counterpart: errcode, jsonread, netconnect, regfile, scrub, tls_trust (src), tools/pathconfine, tools/refusing_args, scripts/refusals, desk_setting, reset_check, demo_only/bad_request. Take files that import none of them now; if a merged on-path file imports one of these, that module must come with it.
- Take-only modules the patch does not touch (e.g. src/lead_desk/gate.py, identity.py, lazy_opener.py, loader.py, contract.py) imply the patch was cut on a different base than the take: it does not apply (as the lead said).
- NOT checked: whether each patch hunk in an imported file is behaviour-relevant to the run; diff content was not read.
