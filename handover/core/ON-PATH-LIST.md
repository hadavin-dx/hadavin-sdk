# ON-PATH LIST: changed files the take's real-check run uses (r7o)

Written 2026-11-14 about 10:35 UTC (16:05 IST) by the core lead. **Method and limit:** read from the import lines and call sites of `scripts/run_real_check.py` in `/home/user/build/rr6/tree-R7O`, then matched against the file list of `core-fix-on-frozen-r7o-crlf.patch.gz`. It is a reading of the code, NOT a traced run: nothing was executed to confirm a file is really reached, and indirect imports below the first level were only partly followed. "Changed" means the file is in the r7o patch relative to the frozen tree 49d3c859. A file that is not in the patch is unchanged.

## 1. Independent mail count (the run counts mails itself, from the mailboxes)
| file | what the run uses | changed in r7o |
|---|---|---|
| src/lead_desk/imap_count.py | `counts_by_inbox`, `ImapSettings`, `bad_folder_name`, the three error classes (login, count, total time) | yes |
| scripts/run_real_check.py | `imap_settings`, `check_mailbox_order`, the banner lines "worst case mailbox reading" and "worst case mails", the poll loop | yes |
| src/lead_desk/netconnect.py | `connect_bounded` (the mailbox and mail connections) | yes |
| src/lead_desk/tls_trust.py | `context_from_ca_file`, verifying context, protocol checks | yes |
| src/lead_desk/smtp_outbox.py | `_HOST_NAME` read by imap_count | yes |
| src/lead_desk/scrub.py | `secret_boundary` (mailbox password never in an error) | yes (new file) |
| src/lead_desk/smtp_provider.py | `read_secret_file` used by imap_count | yes |
| src/lead_desk/constants.py | IMAP limits, spam folder name, `IMAP_LOGINS_MAX` | yes |
| src/lead_desk/contract.py, src/lead_desk/envnum.py | `SendRefused`, `SettingRefused`, `env_number` | contract.py no; envnum.py yes |

## 2. Spend caps (what stops the run from sending or spending too much)
| file | what the run uses | changed in r7o |
|---|---|---|
| src/lead_desk/live_claude.py | `worst_case_usd`, `request_body`, `question_text`, the per-run cap, the live call itself | yes |
| src/lead_desk/config.py | `Config.from_env`, `LiveSettings` (`cap_run_usd`, key file, base-URL check) | yes |
| src/lead_desk/smtp_provider.py | `ProviderSettings.from_env` (`max_sends`, `recipients`), the send path, stats write | yes |
| src/lead_desk/crm_hubspot.py | `HubspotSettings.from_env` (`max_calls`), `HubspotCrm` | yes |
| src/lead_desk/run_stats.py | `write_stats` (counts that survive a restart) | yes |
| src/lead_desk/gate.py | `SEND_WORKERS_MAX` | no |
| scripts/run_real_check.py | banner worst cases (mails x desk processes, HubSpot calls, live model dollars), the Start question, the refusals | yes |
| load_tools/load_driver.py | `send_with_retries` | yes |

## 3. Settings and file readers (every setting and secret the run reads)
| file | what | changed in r7o |
|---|---|---|
| src/lead_desk/envnum.py | `env_number`, `check_url_port`, `split_url` (every numeric setting) | yes |
| src/lead_desk/regfile.py | `read_secret_line`, `read_regular_text` (now accepts a leading BOM), `load_json_file`, `open_output`, `write_regular_text`, `open_regular` | yes |
| src/lead_desk/jsonread.py | `loads_bounded` | yes |
| src/lead_desk/tls_trust.py | `context_from_ca_file` | yes |
| src/lead_desk/config.py | `Config.from_env` and the config file | yes |
| src/lead_desk/hooks.py, db.py, lockfile.py, trace.py, errcode.py, portal_api.py, server.py, desk.py, adapters.py | desk process and plumbing started by the run | yes |
| tools/pathconfine.py, tools/refusing_args.py | `confine_anywhere`, `has_control_character`, `RefusingParser` | yes |
| scripts/http_guard.py | `open_http`, `read_reply` | yes |

## 4. Not on the path (changed, but only read when other scripts run)
scripts/start_all.*, reset.*, crash_desk.py, feed.py, n8n_api.py, hubspot_probe.py, check_schema.py, reset_check.py, run_live_check.py, desk_setting.py, refusals.py, tools/scrub_n8n_export.py, demo_only/*, load_tools/catcher.py and check_invariants.py (the last is imported by run_real_check, so it is on the path for the final table only).

## Not checked
No run was traced; `scripts/run_real_check.py` was not executed for this list. PowerShell scripts never run. Indirect imports (for example contract.py, identity.py, urls.py) were not opened beyond the import line. Next step if wanted: a runner that records `sys.modules` after a dry run under `unshare -n` and diffs it against this table.
