# REV7M: mail / secrets / TLS path, pass 5 (round 7 patch on frozen tree 49d3c85), independent review by REV7M (FALLBACK general-purpose; persona codebase_details)

## NOT checked or not run (first)
- Full suite: not run. Only the 16 relevant test files (1000 tests) per mutant, plus a final run of those files on the fix tree. A mutant that survived there could still be killed by a file outside the set (N8 was run against the whole set of 16 files only).
- Real mail servers, real model, real HubSpot: none (loopback fakes and a made-up CA only). The model, HubSpot adapter and n8n clients were only probed with an untrusted-certificate HTTPS server (no handshake completed, no key byte arrived); a wrong-NAME (trusted chain) case was done for SMTP and IMAP only.
- `scripts/hubspot_probe.py` accepts http loopback only, so its TLS path does not exist and was not probed; `crm_hubspot` adapter TLS rests on urllib's default context (read, not run against a hostile server).
- Python 3.14 imaplib (login quoting may differ) not checked; only 3.13.18 / OpenSSL 3.5.9.
- /proc-style "regular" files that return EAGAIN under O_NONBLOCK (read() could return None) not run (one read of /proc/kmsg happened in probe A; it returned text, no hang). Not judged.
- The full out/R7/RESULTS.md was NOT read before this report was written.
- "First failing test" in the mutation table is the first one pytest reached under `-x`, not necessarily the test that pins the line (the order is not file order); e.g. N1 shows the 5 MB literal test but test_f1_the_user_goes_to_the_server_as_one_quoted_word also pins it.
- Load was low (0.2 to 2.0) the whole time; at most 2 pytest processes at once; every probe was a plain python process.

## Verdict
Blockers: 0. Majors: 1 (G1: the patch ships 2 failing tests, so the gate is red; the code is right, the tests are stale). Minors: 2 (F1, F2). Low/Info: 4 (F3, F4, F5, F6).
Closure of r6: F1-F6 and G1-G4 all verified closed on the real path (all 7 r6 survivors M04 M18a M18b M20 M23 M29 M30 are KILLED now). Baseline of the 16 test files on the unfixed r7 tree: 997 passed, 1 skipped, 2 FAILED (G1). A fix tree (src fixes + test fixes + new tests) ran the same 16 files plus the new file: 1006 passed, 1 skipped, rc 0.

## Mutation table (48 mutants: 31 r6 rows re-run on r7 + 17 new; each in a scratch copy of the tree; 16 test files, `-x`)
Result: 47 KILLED, 1 SURVIVED (N8, equivalent on this runtime; killed by a new test that simulates a lower library default).
| id | file | mutation | result |
|---|---|---|---|
| M01 | tls_trust.py | blank-setting check removed (empty cadata) | KILLED by `test_ca_file_reads.py::test_an_unusable_ca_file_is_refused_at_once_with_fixed_text[empty-trust]` |
| M02 | tls_trust.py | cadata PLUS system store | KILLED by `test_ca_file_reads.py::test_the_context_trusts_only_the_file_and_checks_the_name` |
| M03 | tls_trust.py | check_hostname test removed | KILLED by `test_r7_mail_context.py::test_m18a_a_context_weakened_after_construction_is_refused_before_any_connection[no_hostname-ssl]` |
| M04 | tls_trust.py | verify_mode test removed | KILLED by `test_r7_mail_context.py::test_m04_optional_chain_check_with_name_check_on_is_refused` |
| M05 | tls_trust.py | PEM always read as DER | KILLED by `test_ca_file_reads.py::test_a_valid_ca_file_still_works[trust]` |
| M06 | tls_trust.py | non-ASCII inside PEM block allowed | KILLED by `test_ca_file_reads.py::test_a_non_ascii_character_inside_a_certificate_block_is_refused[body-line-trust]` |
| M07 | tls_trust.py | ssl error translation removed | KILLED by `test_ca_file_reads.py::test_an_unusable_ca_file_is_refused_at_once_with_fixed_text[text-trust]` |
| M08 | regfile.py | S_ISREG check removed (open_regular) | KILLED by `test_r5_refusals.py::test_a_key_file_or_ledger_that_is_a_pipe_is_refused_before_the_cost_line[ledger]` |
| M09 | regfile.py | O_NONBLOCK removed | KILLED by `test_r5_refusals.py::test_a_key_file_or_ledger_that_is_a_pipe_is_refused_before_the_cost_line[key]` |
| M10 | regfile.py | size check removed (read_secret_line) | KILLED by `test_smtp_provider.py::test_password_file_formats_give_a_helpful_fixed_text[raw5-too` |
| M11 | regfile.py | unbounded read (read_secret_line) | KILLED by `test_r6_refusals.py::test_secret_read_is_bounded` |
| M12 | regfile.py | UTF-16 check removed | KILLED by `test_smtp_provider.py::test_password_file_formats_give_a_helpful_fixed_text[\xff\xfep\x00w\x00-\x00f\x00o\x00r\x00-\x00t\x00e\x00s\x00t\x00s\x00-\x00o\x00n\x00l\x00y\x00-UTF-16]` |
| M13 | regfile.py | multi-line check removed | KILLED by `test_smtp_provider.py::test_password_file_formats_give_a_helpful_fixed_text[pw-for-tests-only\nsecond` |
| M14 | regfile.py | control-char (isprintable) check removed | KILLED by `test_r6_refusals.py::test_non_ascii_or_control_key_refused[aaaaaaaa\x7f]` |
| M15 | regfile.py | ASCII check removed | KILLED by `test_r7_mail_context.py::test_m29_a_non_ascii_token_is_refused_with_exit_2_and_no_connection` |
| M16 | regfile.py | BOM strip removed | KILLED by `test_r7_mail_context.py::test_f2_ascii_white_space_around_a_key_is_still_dropped` |
| M17 | smtp_provider.py | no require_verifying in __init__ | KILLED by `test_r7_mail_context.py::test_m04_the_outbox_and_the_mailbox_reader_refuse_it_too` |
| M18a | smtp_provider.py | no re-check in send | KILLED by `test_r7_mail_context.py::test_m18a_a_context_weakened_after_construction_is_refused_before_any_connection[no_hostname-ssl]` |
| M18b | smtp_provider.py | no re-check in _wrap | KILLED by `test_r7_mail_context.py::test_m18b_a_context_weakened_between_the_send_check_and_the_wrap_sends_no_login[no_hostname-ssl]` |
| M19 | smtp_provider.py | ca_file + context both allowed | KILLED by `test_r6_refusals.py::test_context_and_ca_file_together_refused` |
| M20 | smtp_provider.py | blank DESK_SMTPP_CA_FILE falls back | KILLED by `test_r7_mail_context.py::test_m20_a_blank_ca_file_setting_is_refused_not_read_as_system_authorities[]` |
| M21 | imap_count.py | no require_verifying in _session | KILLED by `test_r7_mail_context.py::test_a_mailbox_context_weakened_after_the_settings_were_made_sends_no_login[no_hostname]` |
| M22 | imap_count.py | default context unverified (None) | KILLED by `test_smtp_provider.py::test_imap_default_trust_rejects_an_untrusted_certificate_and_sends_no_password` |
| M23 | run_real_check.py | blank REAL_IMAP_n_CA_FILE falls back | KILLED by `test_r7_mail_context.py::test_m23_a_blank_mailbox_ca_file_setting_is_refused[]` |
| M24 | imap_count.py | imap user control-char (isprintable) check removed | KILLED by `test_r7_mail_context.py::test_f1_a_bad_mailbox_user_is_refused_where_the_settings_are_made[a\nb]` |
| M25 | live_claude.py | live key read AFTER ledger reserve | KILLED by `test_live_claude.py::test_ok_label_and_cost_log` |
| M26 | run_live_check.py | key validation skipped before reserve | KILLED by `test_r7_mail_context.py::test_f2_the_live_key_file_with_a_trailing_odd_space_is_refused_and_no_ledger_line_is_written[\xa0]` |
| M27 | n8n_api.py | own weaker reader restored | KILLED by `test_r7_mail_context.py::test_f2_the_n8n_key_file_with_a_trailing_odd_space_is_refused_with_exit_4[\xa0]` |
| M28 | regfile.py | read_regular_bytes size check removed | KILLED by `test_file_reader_refusals.py::test_the_one_reader_refuses_every_bad_content_with_one_error_type` |
| M29 | hubspot_probe.py | hubspot token weak check | KILLED by `test_r7_mail_context.py::test_m29_a_non_ascii_token_is_refused_with_exit_2_and_no_connection` |
| M30 | smtp_provider.py | smtp user non-ASCII check removed | KILLED by `test_r7_mail_context.py::test_m30_a_non_ascii_smtp_user_is_refused_where_the_settings_are_made[\u03b1\u03b2@example.invalid]` |
| N1 | imap_count.py | IMAP user quote removed | KILLED by `test_r7_mail_context.py::test_f5_a_five_megabyte_literal_is_refused_without_being_read` |
| N2 | imap_count.py | IMAP user check removed | KILLED by `test_r7_mail_context.py::test_f1_a_bad_mailbox_user_is_refused_where_the_settings_are_made[]` |
| N3 | imap_count.py | literal cap removed | KILLED by `test_r7_mail_context.py::test_f5_a_five_megabyte_literal_is_refused_without_being_read` |
| N4 | tls_trust.py | min-TLS check removed | KILLED by `test_r7_mail_context.py::test_f4_the_default_context_passes_and_an_old_minimum_version_is_refused` |
| N5 | regfile.py | ASCII-only strip reverted to str.strip | KILLED by `test_r7_mail_context.py::test_f2_the_smtp_password_file_with_a_trailing_odd_space_is_refused[\xa0]` |
| N6a | smtp_provider.py | ProviderSettings stats_file repr=False reverted | KILLED by `test_r7_mail_context.py::test_f3_the_settings_print_no_ca_or_stats_path` |
| N6b | smtp_provider.py | ProviderSettings ca_file repr=False reverted | KILLED by `test_r7_mail_context.py::test_f3_the_settings_print_no_ca_or_stats_path` |
| N7 | regfile.py | secret_text_ok: inner whitespace check removed | KILLED by `test_r5_refusals.py::test_the_secret_reader_refuses_each_bad_shape_with_a_fixed_text_that_never_repeats_the_content[has` |
| N8 | tls_trust.py | new_verifying_context: min TLS 1.2 not set | SURVIVED |
| N9 | regfile.py | refuse_replacing_special: kind check removed | KILLED by `test_r7_no_replace_of_special.py::test_the_counters_writer_leaves_a_special_target_alone[fifo]` |
| N10 | tls_trust.py | weak cipher check removed | KILLED by `test_r7_mail_context.py::test_f4_a_context_with_a_security_level_zero_cipher_list_is_refused` |
| N11 | regfile.py | secret length min/max removed | KILLED by `test_r6_refusals.py::test_plain_ascii_key_accepted` |
| N12 | imap_count.py | read: deadline check removed | KILLED by `test_r7_mail_context.py::test_f5_the_read_cap_and_the_deadline_hold_on_the_reader_class` |
| N13 | imap_count.py | quote_user backslash escape removed | KILLED by `test_r7_mail_context.py::test_f1_the_user_goes_to_the_server_as_one_quoted_word[rea\\der]` |
| N14 | imap_count.py | IMAP user leading/trailing space check removed | KILLED by `test_r7_mail_context.py::test_f1_a_bad_mailbox_user_is_refused_where_the_settings_are_made[` |
| N15 | tls_trust.py | MINIMUM_SUPPORTED shortcut inverted (all contexts pass) | KILLED by `test_r7_mail_context.py::test_f4_the_default_context_passes_and_an_old_minimum_version_is_refused` |
| N16 | smtp_provider.py | smtp password read after verifying (order) -> read removed from send | KILLED by `test_smtp_provider.py::test_starttls_login_and_one_message_to_a_test_inbox_never_to_the_lead` |

N8 survivor: `ctx.minimum_version = TLSv1_2` removed from `new_verifying_context`. On Python 3.13 / OpenSSL 3.5.9 `ssl.create_default_context().minimum_version` is already TLSv1_2 (printed 771), so no behaviour changes and no black-box test can fail. Killer (new-tests.patch, `test_n8_the_one_context_maker_names_tls_1_2_itself_even_if_the_library_default_is_lower`): wraps `create_default_context` so the library default is MINIMUM_SUPPORTED; passes on the r7 code, fails on the N8 mutant (verified: `MINIMUM_SUPPORTED != TLSv1_2`).

## Findings
| id | sev | where | failing input (proved by a loopback probe) | exact fix |
|---|---|---|---|---|
| G1 | Major (gate) | tests/test_smtp_provider.py::test_a_non_ascii_user_is_a_clear_fixed_error_not_a_crash and tests/test_file_reader_refusals.py::test_n8n_api_key_file_and_workflow_file_that_are_pipes_are_refused_not_waited_for | both FAIL on the patched tree (pytest, deterministic). First builds `ImapSettings(HOST, "usér", ...)` outside `pytest.raises`: the r7 settings now refuse it at construction (ImapSettingRefused). Second expects exit 1 and gets 4 (r7 exit code for a refused key file). The patch itself adds the stale `(1, ...)` line. The rule says no PR with a red suite. | stale-tests-fix.patch (first test: expect ImapSettingRefused at construction and no server command; second: expect exit 4). Verified green on the fix tree. |
| F1 | Minor (must fix, no deferral) | tls_trust.require_verifying / smtp_provider._wrap / imap_count._session | A caller context with `minimum_version=MINIMUM_SUPPORTED` and `set_ciphers("ALL:@SECLEVEL=0")` (no weak cipher word, so `require_verifying` passes; its docstring admits the security level cannot be read) against a server that speaks only TLS 1.1: SMTP ssl, SMTP starttls and IMAP all completed the handshake and the server received `AUTH` (SMTP) / `LOGIN` (IMAP) over TLS 1.1 (probes/tls.out). Not reachable from a settings file; reachable by code that builds the classes. Guarantee "minimum TLS 1.2" fails on the real path. Same with "DEFAULT:@SECLEVEL=0" (documented as undetected). | Check the RESULT of the handshake, which the context cannot hide: `require_modern_protocol(conn)` in tls_trust (conn.version() must be TLSv1.2 or TLSv1.3), called in SMTP `_wrap` after wrap_socket (close and SendRefused before AUTH) and in IMAP `_session` right after the connect and before login (deadline set to the past so no LOGOUT). core-fix-REV7M-src.patch; 3 tests in new-tests.patch (fail on r7, pass on fix). |
| F2 | Minor | imap_count._BoundedImap (deadline) | A server that answers EXAMINE with an endless run of short untagged lines (no literal): `total_seconds=3.0` call ran 13.5 s (lines, 53 MB read) and 12.1 s (one line per 0.5 s): it ends only when the server stops. The r6 F5 text said "deadline only checked between steps"; the r7 fix covers literal reads only. Many small literals (1000 bytes each) DO end at 3.0 s. Memory stayed small in this probe (61 MB) because EXISTS replaces itself; another untagged type grows. | Override `readline()` in `_BoundedImap` with the same deadline check (imaplib reads every reply line there). In core-fix-REV7M-src.patch; test in new-tests.patch (total_seconds=1.0, must end under 4 s; fails on r7). |
| F3 | Low | smtp_provider.ProviderSettings.__post_init__ | SMTP user "  ", " bob", "bob " are accepted (IMAP refuses the same shapes, F1 of r6): the AUTH PLAIN login goes out with a blank or padded user (base64, so no injection, but the password goes to the server with a blank user). | add `or self.user != self.user.strip(" ")` (fix patch; test in new-tests.patch). |
| F4 | Low (sibling of r6 F3) | crm_hubspot.HubspotSettings.stats_file, config.LiveSettings.ledger_path | `repr()` prints both paths (`stats_file=PosixPath('/secret/stats')`, `ledger_path=PosixPath(...)`). ProviderSettings and ImapSettings are clean. | `field(repr=False)` on both (fix patch; sibling test in new-tests.patch). |
| F5 | Info | mutation harness | N8 equivalent on this runtime (above). | new test above. |
| F6 | Low | scripts/run_real_check.load_env (`raw.strip()`, `value.strip()`) | `DESK_SMTPP_USER=bob@example.test<NBSP>` and `REAL_IMAP_1_USER=<NBSP>carol@...` are silently trimmed to a valid user (verified). The same silent-Unicode-trim class as r6 F2, on a user name, not a secret. | `.strip(" \t")` for name and value (not in my patch; one-line change plus a test; not run). |

## Probes that found nothing wrong (all on r7, raw output in probes/)
- Secret reader (probes/secrets.out, 45 contents x spaced on/off + SMTP wrapper): non-ASCII (Greek, full-width), NBSP/VT/FF/U+2003/U+0085/U+2028/U+3000 at either end or inside, zero-width, bidi, NUL, BEL, ESC, DEL, C1, empty, whitespace-only, 7 chars, two lines, lone CR, inner space/tab (refused in plain mode, dropped only in spaced mode), 70 000 B and 5 MB, UTF-16 LE/BE, bad UTF-8, overlong NUL, surrogate, double BOM: all refused with a fixed text, no path or content in any text. Paths: FIFO, symlink to FIFO, /dev/zero, symlink to /dev/zero, /dev/urandom, directory, missing, symlink loop, NUL path, surrogate path, empty path, ".": all refused in 0.00 s.
- End to end (probes/cli.out, smtp_paths.out): live key (run_live_check), n8n key (n8n_api), HubSpot env token (hubspot_probe), SMTP/IMAP password file with each bad content and FIFO / dev-zero / dir / missing: refused before any connection (counting listener: 0 connections), live key: no ledger file created, SMTP `attempts` stays 0; exit 2 / 4 / 2; the made-up marker never appeared in stdout, stderr, ledger. A pasted token given as `--token-env` is not echoed.
- TLS (probes/tls.out): wrong-name certificate (trusted chain) refused for SMTP ssl, SMTP starttls (server saw only EHLO/STARTTLS, no AUTH) and IMAP (no LOGIN); contexts weakened after construction (check_hostname off, CERT_NONE, CERT_OPTIONAL, min TLS 1.0, "ALL:COMPLEMENTOFALL:@SECLEVEL=0") refused with no server event for SMTP ssl/starttls and IMAP; max TLS 1.1 fails the handshake. HTTPS clients (model, n8n) against an untrusted certificate: 0 completed handshakes, 0 request bytes, key never on the wire; the ledger line holds no key.
- IMAP: users with space, quote, backslash, `{5}`, parentheses, `*`, `%`, `]` reach the server as one quoted word (LOGIN pair equals the user); bad users refused at construction for all 13 shapes; 5 MB literal refused unread; named CA file replaces system authorities (M02 killed); CA file shapes FIFO, /dev/zero, dir, empty, garbage refused with a fixed text, no path.

## Files
- probes: /home/user/build/rr6/out/REV7M/probes/ (probe_*.py, *.out)
- fix: /home/user/build/rr6/out/REV7M/core-fix-REV7M-src.patch (src), stale-tests-fix.patch (G1), new-tests.patch (tests/test_r7m_new.py, 7 tests: F1 x3, F2, F3, F4, N8; the first 6 fail on r7, N8 passes on r7 and fails on the N8 mutant)
- all three apply cleanly with `git apply --check` to the r7 tree at /home/user/build/rr6/tree-REV7M
- raw mutation rows: work/runA.log, work/runB.log; baseline: baseline.log
