# Mail path mutation pass 6 (round r7b, money and mail path, no round cap)

Reviewer: EGM goldfish, fallback mode (general-purpose agent with the codebase_details persona). Date: 2026-11-13 (UTC; IST = UTC + 5:30). Made-up data, loopback only, no spend.

## 0. What I did NOT check, and what failed (read first)

1. NOT run: the whole suite (53 test files touch the mail files). Every mutant ran only the 18 files of "set B" (the 16 files of the last pass, plus `tests/test_r7m_new.py` and `tests/test_real_check_dry.py`; 1090 tests, `-x`). Baseline of set B on the clean r7b tree: 1090 passed, 1 skipped, 0 failed, 377 s (`baseline-B.log`). I did not find which test is the one skip. A mutant that set B does not kill could still be killed by a file outside set B; for the 4 survivors below I did NOT re-run the other 35 files (only set B).
2. FAILED, my own harness: the first run of the 78 mutants gave 4 false kills (D05, D11, D20, D21 were "killed" by `test_r7_no_replace_of_special.py::...[socket]` with `OSError: AF_UNIX path too long`, caused by my scratch path, not by the mutant). I re-ran those 4 (and N9) with a short TMPDIR; the table shows the re-run result (tag C). All 4 then SURVIVED set B.
3. NOT tested: the two PowerShell scripts; TLS below 1.0 with a real old server beyond the existing TLS 1.1 fake; Windows.
4. Not a mutation: the stale-tests patch (G1) is part of r7b; I did not judge it.
5. Time: started 22:57 UTC, report written about 23:40 UTC. Checkpoint notes in `/home/user/build/rr6/out/MAIL6/checkpoint.md`.

## 1. Result in one paragraph

Tree: git archive of `frozen2` (tree object 49d3c85938fe5323a3378a49195d3b8da434b3ca, commit 58aa4031e911e682ec5702e0641d11cbaf927817), `core-fix-on-frozen-r7b.patch` applied cleanly (`git apply`), tree at `/home/user/build/rr6/out/MAIL6/tree-M6` (deleted at the end). 78 mutants (48 from the last pass, 30 new): 74 KILLED, 4 SURVIVED (D05, D11, D20, D21; D21 is equivalent). N8, the survivor of the last pass, is now KILLED by a real run: `tests/test_r7m_new.py::test_n8_the_one_context_maker_names_tls_1_2_itself_even_if_the_library_default_is_lower` (4 s, `work/raw-N8-B.txt`). Besides mutation I found 3 real defects by reading and probing (section 4): one Major in `run_real_check.py` (a bad secret file is not refused before the "Start?" question), one Major in `imap_count.py` (the total time limit is not held inside one slow reply line or literal, greeting included), one Minor in `smtp_outbox.py` (the reply size cap does not apply to a multi-line reply).

Verdict for the guarantees:

| Guarantee | Holds? |
|---|---|
| secrets never printed, logged or in exceptions (repr=False on stats_file, ledger_path) | Yes on every path I read and on mutants D16, D17, N6a, N6b (killed). Settings of `ProviderSettings`, `HubspotSettings`, `LiveSettings`, `ImapSettings` print no path, user or key. |
| a bad secret refused BEFORE any ledger reserve or connection | Yes inside the library (live key before reserve: M25, M26; smtp password before connect: N16, D25). NO for the script `run_real_check.py`: finding F-B. |
| named CA file REPLACES the system authorities | Yes (M02, M19, M20, M23, D29 killed). |
| CERT_REQUIRED and check_hostname on at construction and at every use | Yes (M03, M04, M17, M18a, M18b, M21, D26, D27, D30 killed). |
| handshake below TLS 1.2 refused before AUTH/LOGIN | Yes for smtp (ssl and starttls) and imap (D01-D04, D06, D10, D23, N4, N8, N15, D28 killed); a refused imap connection still gets a LOGOUT (D05 survives; it carries no secret). A refused smtp TLS connection is not closed at once (D11 survives). |
| IMAP reads have a total deadline | NO inside one reply line or literal and not for the greeting: finding F-A. Yes between lines (D07, D08, N12 killed). |
| a reply over the cap is refused whole | imap literal: yes (D09, N3 killed). smtp multi-line reply: no, finding F-C. HubSpot and model replies: read by code only (`crm_hubspot.py:317-328`, `live_claude.py:467-484`), not mutated. |

## 2. Mutation table

Columns: mutant | file:line (of the changed text in the r7b tree) | change | result | first killing test | raw output (under `/home/user/build/rr6/out/MAIL6/`). Tests run for every row: set B, 18 files, `-x`, with `unshare -n python .../lo_up-q4g.py .../venv-br/bin/python -m pytest -q -p no:cacheprovider --tb=short -rf`, TMPDIR outside the tree, PYTHONPATH=<copy>/src, PYTHONDONTWRITEBYTECODE=1, each mutant on its own copy. M30 and N12 had to be re-made for the r7b text (M30: the r7b line has a second condition; N12: `read` and `readline` now both hold the check, the mutant removes only the one in `read`). D-numbers are new mutants at places the r7b delta touched.

| id | file:line | change | result | first killing test | raw output |
|---|---|---|---|---|---|
| M01 | tls_trust.py:68 | blank-setting check removed (empty cadata) | KILLED | test_ca_file_reads.py::test_an_unusable_ca_file_is_refused_at_once_with_fixed_text[empty-trust] | work/raw-M01-B.txt |
| M02 | tls_trust.py:98 | cadata PLUS system store | KILLED | test_ca_file_reads.py::test_the_context_trusts_only_the_file_and_checks_the_name | work/raw-M02-B.txt |
| M03 | tls_trust.py:123 | check_hostname test removed | KILLED | test_r7_mail_context.py::test_m18a_a_context_weakened_after_construction_is_refused_before_any_connection[no_h | work/raw-M03-B.txt |
| M04 | tls_trust.py:123 | verify_mode test removed | KILLED | test_r7_mail_context.py::test_m04_optional_chain_check_with_name_check_on_is_refused | work/raw-M04-B.txt |
| M05 | tls_trust.py:71 | PEM always read as DER | KILLED | test_ca_file_reads.py::test_a_valid_ca_file_still_works[trust] | work/raw-M05-B.txt |
| M06 | tls_trust.py:49 | non-ASCII inside PEM block allowed | KILLED | test_ca_file_reads.py::test_a_non_ascii_character_inside_a_certificate_block_is_refused[body-line-trust] | work/raw-M06-B.txt |
| M07 | tls_trust.py:83 | ssl error translation removed | KILLED | test_ca_file_reads.py::test_an_unusable_ca_file_is_refused_at_once_with_fixed_text[text-trust] | work/raw-M07-B.txt |
| M08 | regfile.py:49 | S_ISREG check removed (open_regular) | KILLED | test_r5_refusals.py::test_a_key_file_or_ledger_that_is_a_pipe_is_refused_before_the_cost_line[ledger] | work/raw-M08-B.txt |
| M09 | regfile.py:31 | O_NONBLOCK removed | KILLED | test_r5_refusals.py::test_a_key_file_or_ledger_that_is_a_pipe_is_refused_before_the_cost_line[key] | work/raw-M09-B.txt |
| M10 | regfile.py:78 | size check removed (read_secret_line) | KILLED | test_smtp_provider.py::test_password_file_formats_give_a_helpful_fixed_text[raw5-too | work/raw-M10-B.txt |
| M11 | regfile.py:75 | unbounded read (read_secret_line) | KILLED | test_r6_refusals.py::test_secret_read_is_bounded | work/raw-M11-B.txt |
| M12 | regfile.py:80 | UTF-16 check removed | KILLED | test_smtp_provider.py::test_password_file_formats_give_a_helpful_fixed_text[\xff\xfep\x00w\x00-\x00f\x00o\x00r | work/raw-M12-B.txt |
| M13 | regfile.py:88 | multi-line check removed | KILLED | test_smtp_provider.py::test_password_file_formats_give_a_helpful_fixed_text[pw-for-tests-only\nsecond | work/raw-M13-B.txt |
| M14 | regfile.py:104 | control-char (isprintable) check removed | KILLED | test_r6_refusals.py::test_non_ascii_or_control_key_refused[aaaaaaaa\x7f] | work/raw-M14-B.txt |
| M15 | regfile.py:103 | ASCII check removed | KILLED | test_r7_mail_context.py::test_m29_a_non_ascii_token_is_refused_with_exit_2_and_no_connection | work/raw-M15-B.txt |
| M16 | regfile.py:83 | BOM strip removed | KILLED | test_r7_mail_context.py::test_f2_ascii_white_space_around_a_key_is_still_dropped | work/raw-M16-B.txt |
| M17 | smtp_provider.py:194 | no require_verifying in __init__ | KILLED | test_r7_mail_context.py::test_m04_the_outbox_and_the_mailbox_reader_refuse_it_too | work/raw-M17-B.txt |
| M18a | smtp_provider.py:251 | no re-check in send | KILLED | test_r7_mail_context.py::test_m18a_a_context_weakened_after_construction_is_refused_before_any_connection[no_h | work/raw-M18a-B.txt |
| M18b | smtp_provider.py:296 | no re-check in _wrap | KILLED | test_r7_mail_context.py::test_m18b_a_context_weakened_between_the_send_check_and_the_wrap_sends_no_login[no_ho | work/raw-M18b-B.txt |
| M19 | smtp_provider.py:191 | ca_file + context both allowed | KILLED | test_r6_refusals.py::test_context_and_ca_file_together_refused | work/raw-M19-B.txt |
| M20 | smtp_provider.py:147 | blank DESK_SMTPP_CA_FILE falls back | KILLED | test_r7_mail_context.py::test_m20_a_blank_ca_file_setting_is_refused_not_read_as_system_authorities[] | work/raw-M20-B.txt |
| M21 | imap_count.py:140 | no require_verifying in _session | KILLED | test_r7_mail_context.py::test_a_mailbox_context_weakened_after_the_settings_were_made_sends_no_login[no_hostna | work/raw-M21-B.txt |
| M22 | imap_count.py:142 | default context unverified (None) | KILLED | test_smtp_provider.py::test_imap_default_trust_rejects_an_untrusted_certificate_and_sends_no_password | work/raw-M22-B.txt |
| M23 | scripts/run_real_check.py:633 | blank REAL_IMAP_n_CA_FILE falls back | KILLED | test_r7_mail_context.py::test_m23_a_blank_mailbox_ca_file_setting_is_refused[] | work/raw-M23-B.txt |
| M24 | imap_count.py:84 | imap user control-char (isprintable) check removed | KILLED | test_r7_mail_context.py::test_f1_a_bad_mailbox_user_is_refused_where_the_settings_are_made[a\nb] | work/raw-M24-B.txt |
| M25 | live_claude.py:496 | live key read AFTER ledger reserve | KILLED | test_live_claude.py::test_ok_label_and_cost_log | work/raw-M25-B.txt |
| M26 | scripts/run_live_check.py:177 | key validation skipped before reserve | KILLED | test_r7_mail_context.py::test_f2_the_live_key_file_with_a_trailing_odd_space_is_refused_and_no_ledger_line_is_ | work/raw-M26-B.txt |
| M27 | scripts/n8n_api.py:137 | own weaker reader restored | KILLED | test_r7_mail_context.py::test_f2_the_n8n_key_file_with_a_trailing_odd_space_is_refused_with_exit_4[\xa0] | work/raw-M27-B.txt |
| M28 | regfile.py:114 | read_regular_bytes size check removed | KILLED | test_file_reader_refusals.py::test_the_one_reader_refuses_every_bad_content_with_one_error_type | work/raw-M28-B.txt |
| M29 | scripts/hubspot_probe.py:327 | hubspot token weak check | KILLED | test_r7_mail_context.py::test_m29_a_non_ascii_token_is_refused_with_exit_2_and_no_connection | work/raw-M29-B.txt |
| M30 | smtp_provider.py:114 | smtp user non-ASCII check removed | KILLED | test_r7_mail_context.py::test_m30_a_non_ascii_smtp_user_is_refused_where_the_settings_are_made[\u03b1\u03b2@ex | work/raw-M30-B.txt |
| N1 | imap_count.py:159 | IMAP user quote removed | KILLED | test_r7_mail_context.py::test_f1_the_user_goes_to_the_server_as_one_quoted_word[reader | work/raw-N1-B.txt |
| N2 | imap_count.py:84 | IMAP user check removed | KILLED | test_r7_mail_context.py::test_f1_a_bad_mailbox_user_is_refused_where_the_settings_are_made[] | work/raw-N2-B.txt |
| N3 | imap_count.py:104 | literal cap removed | KILLED | test_r7_mail_context.py::test_f5_a_five_megabyte_literal_is_refused_without_being_read | work/raw-N3-B.txt |
| N4 | tls_trust.py:125 | min-TLS check removed | KILLED | test_r7_mail_context.py::test_f4_the_default_context_passes_and_an_old_minimum_version_is_refused | work/raw-N4-B.txt |
| N5 | regfile.py:83 | ASCII-only strip reverted to str.strip | KILLED | test_r7_mail_context.py::test_f2_the_smtp_password_file_with_a_trailing_odd_space_is_refused[\xa0] | work/raw-N5-B.txt |
| N6a | smtp_provider.py:100 | ProviderSettings stats_file repr=False reverted | KILLED | test_r7_mail_context.py::test_f3_the_settings_print_no_ca_or_stats_path | work/raw-N6a-B.txt |
| N6b | smtp_provider.py:103 | ProviderSettings ca_file repr=False reverted | KILLED | test_r7_mail_context.py::test_f3_the_settings_print_no_ca_or_stats_path | work/raw-N6b-B.txt |
| N7 | regfile.py:105 | secret_text_ok: inner whitespace check removed | KILLED | test_r5_refusals.py::test_the_secret_reader_refuses_each_bad_shape_with_a_fixed_text_that_never_repeats_the_co | work/raw-N7-B.txt |
| N8 | tls_trust.py:99 | new_verifying_context: min TLS 1.2 not set | KILLED | test_r7m_new.py::test_n8_the_one_context_maker_names_tls_1_2_itself_even_if_the_library_default_is_lower | work/raw-N8-B.txt |
| N9 | regfile.py:247 | refuse_replacing_special: kind check removed | KILLED | test_r7_no_replace_of_special.py::test_the_counters_writer_leaves_a_special_target_alone[fifo] | work/raw-N9-C.txt |
| N10 | tls_trust.py:125 | weak cipher check removed | KILLED | test_r7_mail_context.py::test_f4_a_context_with_a_security_level_zero_cipher_list_is_refused | work/raw-N10-B.txt |
| N11 | regfile.py:102 | secret length min/max removed | KILLED | test_r6_refusals.py::test_plain_ascii_key_accepted | work/raw-N11-B.txt |
| N12 | imap_count.py:107 | read: deadline check removed | KILLED | test_r7_mail_context.py::test_f5_the_read_cap_and_the_deadline_hold_on_the_reader_class | work/raw-N12-B.txt |
| N13 | imap_count.py:93 | quote_user backslash escape removed | KILLED | test_r7_mail_context.py::test_f1_the_user_goes_to_the_server_as_one_quoted_word[rea\\der] | work/raw-N13-B.txt |
| N14 | imap_count.py:84 | IMAP user leading/trailing space check removed | KILLED | test_r7_mail_context.py::test_f1_a_bad_mailbox_user_is_refused_where_the_settings_are_made[ | work/raw-N14-B.txt |
| N15 | tls_trust.py:93 | MINIMUM_SUPPORTED shortcut inverted (all contexts pass) | KILLED | test_r7_mail_context.py::test_f4_the_default_context_passes_and_an_old_minimum_version_is_refused | work/raw-N15-B.txt |
| N16 | smtp_provider.py:250 | smtp password read after verifying (order) -> read removed from send | KILLED | test_smtp_provider.py::test_starttls_login_and_one_message_to_a_test_inbox_never_to_the_lead | work/raw-N16-B.txt |
| D01 | tls_trust.py:103 | TLS_OK_VERSIONS also lists TLSv1.1 | KILLED | test_r7m_new.py::test_f1_smtp_login_never_goes_out_over_a_tls_version_below_1_2[ssl] | work/raw-D01-B.txt |
| D02 | tls_trust.py:110 | require_modern_protocol: check removed | KILLED | test_r7m_new.py::test_f1_smtp_login_never_goes_out_over_a_tls_version_below_1_2[ssl] | work/raw-D02-B.txt |
| D03 | tls_trust.py:110 | require_modern_protocol: refuses only a None version | KILLED | test_r7m_new.py::test_f1_smtp_login_never_goes_out_over_a_tls_version_below_1_2[ssl] | work/raw-D03-B.txt |
| D04 | imap_count.py:153 | imap: modern-protocol call removed | KILLED | test_r7m_new.py::test_f1_imap_login_never_goes_out_over_a_tls_version_below_1_2 | work/raw-D04-B.txt |
| D05 | imap_count.py:155 | imap: refused connection still sends LOGOUT (deadline not cut) (first run B was a harness false kill: AF_UNIX path too long; re-run C is the result) | SURVIVED |  | work/raw-D05-C.txt |
| D06 | imap_count.py:152 | imap: modern-protocol check moved AFTER login | KILLED | test_r7m_new.py::test_f1_imap_login_never_goes_out_over_a_tls_version_below_1_2 | work/raw-D06-B.txt |
| D07 | imap_count.py:114 | imap readline: deadline check removed | KILLED | test_r7m_new.py::test_f2_an_endless_run_of_untagged_lines_ends_at_the_total_time_limit | work/raw-D07-B.txt |
| D08 | imap_count.py:114 | imap readline: deadline comparison inverted | KILLED | test_r7_mail_context.py::test_f1_the_user_goes_to_the_server_as_one_quoted_word[reader | work/raw-D08-B.txt |
| D09 | imap_count.py:104 | imap read: literal cap x10 | KILLED | test_r7_mail_context.py::test_f5_a_five_megabyte_literal_is_refused_without_being_read | work/raw-D09-B.txt |
| D10 | smtp_provider.py:300 | smtp _wrap: modern-protocol call removed | KILLED | test_r7m_new.py::test_f1_smtp_login_never_goes_out_over_a_tls_version_below_1_2[ssl] | work/raw-D10-B.txt |
| D11 | smtp_provider.py:302 | smtp _wrap: refused connection not closed (first run B was a harness false kill: AF_UNIX path too long; re-run C is the result) | SURVIVED |  | work/raw-D11-C.txt |
| D12 | smtp_provider.py:114 | smtp user: space-at-either-end check removed | KILLED | test_r7m_new.py::test_f3_a_blank_or_space_padded_smtp_user_is_refused_where_the_settings_are_made | work/raw-D12-B.txt |
| D13 | smtp_provider.py:114 | smtp user: only a leading space refused (lstrip) | KILLED | test_r7m_new.py::test_f3_a_blank_or_space_padded_smtp_user_is_refused_where_the_settings_are_made | work/raw-D13-B.txt |
| D14 | imap_count.py:84 | imap user: only a leading space refused (lstrip) | KILLED | test_r7_mail_context.py::test_f1_a_bad_mailbox_user_is_refused_where_the_settings_are_made[a | work/raw-D14-B.txt |
| D15 | imap_count.py:84 | imap user: trailing-space refused only (rstrip) | KILLED | test_r7_mail_context.py::test_f1_a_bad_mailbox_user_is_refused_where_the_settings_are_made[ | work/raw-D15-B.txt |
| D16 | config.py:135 | LiveSettings.ledger_path repr=False removed | KILLED | test_r7m_new.py::test_sibling_repr_of_settings_shows_no_path | work/raw-D16-B.txt |
| D17 | crm_hubspot.py:147 | HubspotSettings.stats_file repr=False removed | KILLED | test_r7m_new.py::test_sibling_repr_of_settings_shows_no_path | work/raw-D17-B.txt |
| D18 | scripts/run_real_check.py:668 | load_env: line strip -> str.strip (all white space) | KILLED | test_file_reader_refusals.py::test_run_real_check_config_value_with_an_odd_space_is_not_silently_trimmed[\xa0] | work/raw-D18-B.txt |
| D19 | scripts/run_real_check.py:674 | load_env: value strip -> str.strip | KILLED | test_file_reader_refusals.py::test_run_real_check_config_value_with_an_odd_space_is_not_silently_trimmed[\xa0] | work/raw-D19-B.txt |
| D20 | scripts/run_real_check.py:672 | load_env: name strip(.. ) in fullmatch -> str.strip (first run B was a harness false kill: AF_UNIX path too long; re-run C is the result) | SURVIVED |  | work/raw-D20-C.txt |
| D21 | scripts/run_real_check.py:677 | load_env: stored name strip -> str.strip (first run B was a harness false kill: AF_UNIX path too long; re-run C is the result) | SURVIVED |  | work/raw-D21-C.txt |
| D22 | smtp_provider.py:319 | smtp: STARTTLS refusal no longer checked | KILLED | test_smtp_provider.py::test_starttls_login_and_one_message_to_a_test_inbox_never_to_the_lead | work/raw-D22-B.txt |
| D23 | smtp_provider.py:321 | smtp starttls: wrap skipped (AUTH over plaintext) | KILLED | test_r7_mail_context.py::test_m18b_a_context_weakened_between_the_send_check_and_the_wrap_sends_no_login[no_ho | work/raw-D23-B.txt |
| D24 | tls_trust.py:48 | ascii_outside_blocks: END line check dropped | KILLED | test_ca_file_reads.py::test_a_pem_file_with_non_ascii_words_around_the_certificate_still_loads[comment-after-t | work/raw-D24-B.txt |
| D25 | smtp_provider.py:250 | smtp send: password read after verifying/ connect (read removed before reserve -> read in dialogue) | KILLED | test_smtp_provider.py::test_starttls_login_and_one_message_to_a_test_inbox_never_to_the_lead | work/raw-D25-B.txt |
| D26 | smtp_provider.py:251 | smtp send: context re-check at use removed | KILLED | test_r7_mail_context.py::test_m18a_a_context_weakened_after_construction_is_refused_before_any_connection[no_h | work/raw-D26-B.txt |
| D27 | imap_count.py:140 | imap _session: ssl_context verify at use removed | KILLED | test_r7_mail_context.py::test_a_mailbox_context_weakened_after_the_settings_were_made_sends_no_login[no_hostna | work/raw-D27-B.txt |
| D28 | tls_trust.py:93 | _below_tls12 always False | KILLED | test_r7_mail_context.py::test_f4_the_default_context_passes_and_an_old_minimum_version_is_refused | work/raw-D28-B.txt |
| D29 | smtp_provider.py:147 | smtp ca_file blank-check removed | KILLED | test_r7_mail_context.py::test_m20_a_blank_ca_file_setting_is_refused_not_read_as_system_authorities[] | work/raw-D29-B.txt |
| D30 | smtp_provider.py:296 | smtp _wrap: re-check of context at wrap removed | KILLED | test_r7_mail_context.py::test_m18b_a_context_weakened_between_the_send_check_and_the_wrap_sends_no_login[no_ho | work/raw-D30-B.txt |

Notes on the table:
- D05 (tls: imap `m.deadline = -inf` after a refused handshake removed, so LOGOUT is sent): SURVIVED. The server then sees `['CAPABILITY', 'LOGOUT']`. No secret is sent, but the refused connection is talked to. Existing test `test_f1_imap_login_never_goes_out_over_a_tls_version_below_1_2` only asserts that LOGIN is absent.
- D11 (`conn.close()` removed in `_wrap` after the refusal): SURVIVED. `wrap_socket` detaches the plain socket, so the `sock.close()` in `send` closes nothing; the refused TLS connection stays open until garbage collection.
- D20 (`load_env`: `name.strip()` instead of `name.strip(" \t")` in the name check): SURVIVED. `REAL_PERSONS<NBSP>=8` is then accepted as a name.
- D21 (`load_env`: stored key `name.strip()` instead of `name.strip(" \t")`): SURVIVED and EQUIVALENT: the name already passed `CONFIG_NAME.fullmatch` of the `" \t"`-stripped form, which holds only upper-case letters, digits and underscore, so a second strip changes nothing. No test is needed.
- D18 and D19 (r7b F6 on `line` and `value`) are killed (`test_run_real_check_config_value_with_an_odd_space_is_not_silently_trimmed[\xa0]`).
- Some mutants (for example M01, M10, D18) are killed late (50 to 100 s) because the killing file comes late in the order, not because the test is weak.

## 3. Killing tests for the survivors (drafts, outside the tree)

File: `/home/user/build/rr6/out/MAIL6/killers/test_m6_new.py`. I ran them: on the clean r7b tree D05, D11, D20 killers pass (3 passed); on each mutant its own killer fails (D05: `AssertionError: ['CAPABILITY', 'LOGOUT']`; D11: `the refused TLS connection was left open`; D20: `DID NOT RAISE ValueError`). The same file also holds the killers for the 2 Major findings, which FAIL on r7b (4 failed on the unmodified tree, see section 4). Text of the survivor killers:

```python
# ---- killers for D05, D11, D20 (written only after the mutation run; see the review text) ----


def test_m6_d11_a_connection_refused_for_its_tls_version_is_closed_at_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from demo_only.fake_smtp_tls import FakeSmtp  # noqa: PLC0415
    from lead_desk import smtp_provider as sp  # noqa: PLC0415
    from lead_desk.contract import SendRefused  # noqa: PLC0415
    from lead_desk.smtp_outbox import _Budget  # noqa: PLC0415
    from lead_desk.tls_trust import CaFileRefused  # noqa: PLC0415

    made = make_cert(tmp_path, HOST)
    if made is None:
        pytest.skip("no openssl")
    pw = tmp_path / "pw.txt"
    pw.write_text(FAKE_PASSWORD + "\n", encoding="utf-8")
    srv = FakeSmtp(made[0], made[1], HOST, implicit_tls=True)
    closed: list[bool] = []
    real_close = ssl.SSLSocket.close

    def spy(self: ssl.SSLSocket) -> None:
        closed.append(True)
        real_close(self)

    def refuse(conn: ssl.SSLSocket, name: str) -> None:
        raise CaFileRefused("forced")

    try:
        s = sp.ProviderSettings(HOST, srv.port, "sender-user", pw, "sender@example.test", ("a@example.test",), 5,
                                security="ssl", timeout_seconds=3.0)
        box = sp.SmtpProviderOutbox(s, ssl.create_default_context(cafile=str(made[0])))
        monkeypatch.setattr(sp, "require_modern_protocol", refuse)
        monkeypatch.setattr(ssl.SSLSocket, "close", spy)
        sock = socket.create_connection((HOST, srv.port), timeout=3)
        with pytest.raises(SendRefused):
            box._wrap(sock, _Budget(3.0))
        assert closed, "the refused TLS connection was left open"
    finally:
        srv.close()


def test_m6_d20_a_config_name_with_a_no_break_space_is_refused(tmp_path: Path) -> None:
    import run_real_check as rrc  # noqa: PLC0415

    cfg = tmp_path / "c.env"
    cfg.write_text("REAL_PERSONS\xa0=8\n", encoding="utf-8")
    with pytest.raises(ValueError, match="config line 1"):
        rrc.load_env(cfg)


def test_m6_d05_a_mailbox_connection_refused_for_its_tls_version_gets_no_logout_either(tmp_path: Path) -> None:
    from demo_only.fake_imap import FakeImap  # noqa: PLC0415
    from lead_desk.imap_count import ImapCountError as Err  # noqa: PLC0415

    made = make_cert(tmp_path, HOST)
    if made is None:
        pytest.skip("no openssl")
    pw = tmp_path / "pw.txt"
    pw.write_text(FAKE_PASSWORD + "\n", encoding="utf-8")
    srv = FakeImap(made[0], made[1], HOST, {"INBOX": ["RUN1-L1"]})
    try:
        try:
            srv._ctx.minimum_version = ssl.TLSVersion.TLSv1
            srv._ctx.maximum_version = ssl.TLSVersion.TLSv1_1
            srv._ctx.set_ciphers("ALL:@SECLEVEL=0")
        except (ValueError, ssl.SSLError):
            pytest.skip("this OpenSSL cannot make a TLS 1.1 only test server")
        c = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        c.load_verify_locations(cafile=str(made[0]))
        c.minimum_version = ssl.TLSVersion.MINIMUM_SUPPORTED
        c.set_ciphers("ALL:@SECLEVEL=0")
        s = ImapSettings(HOST, srv.user, pw, port=srv.port, folders=("INBOX",), timeout_seconds=3.0, ssl_context=c)
        with pytest.raises(Err):
            counts_by_key(s, "RUN1-")
        time.sleep(0.3)
        assert "LOGOUT" not in srv.commands and "LOGIN" not in srv.commands, srv.commands
    finally:
        srv.close()

```

## 4. Findings from reading and probing (not from mutation)

Severity words: Major = a stated guarantee is false on a reachable input; Minor = guarantee false but bounded.

### F-B (Major): `scripts/run_real_check.py` asks "Start?" and starts real services with a bad secret file

- Where: `main` lines 981-1035: `HubspotSettings.from_env` (981), `ProviderSettings.from_env` (982) and `imap_settings` (990) read only the settings, never the secret files; `input("Start? [y/N] ")` is at 1035. The files are first read by the desk and the mailbox reader after the run has begun (the desk makes real HubSpot calls before the first mail; the mailbox read is the last step).
- Failing inputs (all made up, `printf 'n\n' |` as the only answer, run inside `unshare -n`): a config whose `DESK_HUBSPOT_KEY_FILE` holds `fake-hs-key-with-nbsp-<NBSP>`, or `DESK_SMTPP_PASSWORD_FILE` holds `pw-bad-<NBSP>-xx12`, or `REAL_IMAP_1_PASSWORD_FILE` / `REAL_IMAP_2_PASSWORD_FILE` holds the same. Each of the four prints the cost lines and `Start? [y/N]`; only my "n" stopped them. Raw: `probes/real_check_order.out` (config files in `probes/cfg/`).
- Why it matters: the guarantee "a bad secret is refused before any connection" is false for this script; with a bad IMAP password the run would create real HubSpot contacts and send real mails and only then fail to count them. The comment on `positive_seconds` says the opposite goal ("a typo cannot surface after real mails were sent").
- Fix at the one choke point: in the refusal block before the cost lines, call `read_secret_line` (regfile) for the HubSpot key file, the SMTP password file and every mailbox password file, and map `FileRefused` to the existing refusal line with the setting name only.
- Killer: `test_m6_real_check_refuses_a_bad_secret_file_before_the_start_question` in the file above (fails on r7b: `hs: the Start? question was reached with a bad secret file`).

### F-A (Major): the IMAP total time limit is not held inside one line, one literal or the greeting

- Where: `imap_count.py:103-116` (`read`, `readline` check the deadline only when called), `imap_count.py:149-150` (`m.deadline` is set AFTER `_BoundedImap(...)` has read the greeting). The per-step socket timeout (`timeout_seconds`, here 3 s) restarts with every byte that arrives.
- Failing inputs (TLS server on loopback, `total_seconds=3.0`, `timeout_seconds=3.0`; raw `probes/imap_drip.out`, script `probes/probe_imap_drip.py`):
  - greeting: one `*` byte every 0.3 s, no line end: the call ended after 9.0 s (server stopped then);
  - one reply line to EXAMINE: one `*` every 0.3 s: 12.1 s (server stopped then);
  - a literal `{2000}` delivered one byte every 0.3 s: 12.1 s, then `ImapTotalTimeout`.
  With a patient server the call runs until the line limit (imaplib `_MAXLINE` 1,000,000 bytes) or the 5 MB literal cap, that is hours at one byte per 0.3 s. The earlier "endless untagged lines" case (F2 of r7) is closed, this is the same class one level lower.
- Why it matters: the mailbox read is part of the money and mail check; a slow server holds the run for much longer than `total_seconds` states, and the doc text says the clock "starts BEFORE the connection and the server greeting".
- Fix at the choke point (`_BoundedImap`): cut the socket at the deadline from outside, for example a `threading.Timer(total_seconds, ...)` started before the connection that calls `shutdown(SHUT_RDWR)` on the socket (the socket is made in `_create_socket`/`open`, override it to keep a reference), cancelled in `finally`; map the resulting `OSError` after the deadline to `ImapTotalTimeout` (the `_session` code at 172-175 already does this when `time.monotonic() > deadline`).
- Killer: `test_m6_the_total_time_limit_holds_inside_one_slow_line_or_literal[greeting|line|literal]` (fails on r7b: 10.2 s, 10.3 s, 10.3 s against a limit of 2 s plus 4 s slack).

### F-C (Minor): an SMTP reply is capped only while it is unfinished

- Where: `smtp_outbox.py:139-162` (`_read_reply`): continuation lines (`250-x`) are deleted from the buffer at 152 and the cap check `len(buf) > _REPLY_MAX_BYTES` (156) only sees what is left, so the size of a whole multi-line reply is not limited, only the time budget is.
- Failing input: a server that sends 600,000 lines `250-x\r\n` (4.2 MB) and then `250 done\r\n`: accepted as code 250 although the cap is 65536 (`probes/smtp_multiline.out`, `probes/probe_smtp_multiline.py`).
- Fix: count the bytes of the whole reply (a running total reset at each reply) and refuse above the cap. Killer: feed the lines above through `_read_reply` on a socketpair and expect `_Closed`.

### Read and found clean (no finding)

- Secrets in messages: every `raise` and `print` in `smtp_provider.py`, `imap_count.py`, `tls_trust.py`, `regfile.py`, `live_claude.py` (`_read_key`, `_writable`), `crm_hubspot.py` (`_key`), `config.py` (`read_leadflow`), `run_real_check.py` (`load_env`, `main`, the mailbox message at line 534) carries a fixed text, a setting name, a status code or a line number; I found no path, user, key, password, CA path or typed value reaching an exception, log line or `repr`. Exception classes are reported by name only (`SendUnreachable(type(e).__name__)`).
- Typed values reaching a message: `send_key` (regex), `to` (regex, ASCII), subject (`_breaks_a_header`), user (control characters, non-ASCII, space at either end refused in `ProviderSettings`; `ImapSettings` also non-printable), IMAP user (quoted by `quote_user`), folder names (`bad_folder_name`), prefix and keys (`_PREFIX`): all checked before any connection in `send` / `_session`. A smtp user with a space INSIDE (`a b`) is accepted by design (it travels base64 in AUTH PLAIN); an IMAP user with an inner space is quoted. Not a defect.
- Connection before validation inside the library: smtp `send` order is header checks, address check, password read (250), context re-check (251), build, cap, connect (262); imap `_session` order is folder names, password, context, deadline, connect; both hold (D25, D26, D27, N16 killed).
- STARTTLS: the buffer is cleared after the wrap (`smtp_provider.py:322`), so plaintext injected before the upgrade cannot be read as a reply after it; AUTH is sent only after the wrap (D23 killed).

## 5. Commands

- Tree: `git archive frozen2 | tar -x` into `tree-M6`, `git init`, commit, `git apply --whitespace=nowarn core-fix-on-frozen-r7b.patch` (applied, 130 changed files).
- Baseline and probes: `unshare -n python3 .../lo_up-q4g.py .../venv-br/bin/python ...` as above; the probes never answered "y" (run_real_check probe was answered "n" on stdin, no /dev path used).
- Runner: `work/mut6.py` (copies the tree, replaces the text, runs set B), mutant list `work/specs6.json`, results `work/spec*.json.results`, table `work/table.md`.
- Processes: 4 mutation runners and 5 re-run processes were started by me, all have ended (checked with `ps`).
