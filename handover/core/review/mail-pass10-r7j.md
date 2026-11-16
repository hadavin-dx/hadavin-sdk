# Mail-path mutant pass 10 on patch r7j (EGM goldfish, fallback mode)

Verdict: **NOT CLEAN**. Two confirmed REAL GAPS (M9-69, M9-16), both sent to the r7k builder. Most of the ordered list was NOT finished. Tree under test: copy of tree-R7J (tree-M10, and tree-M10b for the second lane), made-up data, loopback only (each test run inside its own network namespace), no spend. Start 06:57Z, stop about 07:54Z. Raw files: /home/user/build/rr6/out/M10/ (checkpoint.md, results-LA.tsv, results-LB.tsv, raw-*.txt, clean-*.log, specs work/specs10.json, runner mut10.py, generator gen10.py).

## What was NOT run or not done (first)
- Not run: M9-73 to M9-82 (run_real_check: refusal text, exit code, mailbox folder check, secret pre-check order, login limit, time setting, live worst case, mask_result, scrub order, readback cap). Of run_real_check only M9-68, 69, 70, 71, 72 ran. So the scrubber of secrets in output (M9-80, 81), the secret pre-check order (M9-76) and the mailbox login limit (M9-77) were NOT re-probed in this pass. M10-J12 and M10-J13 were in flight or queued when the time box ended (no result). M9-73 was in flight and discarded.
- Big-set re-runs done for only two survivors (M9-69, M9-16). The other 14 selector-set survivors are UNJUDGED (suspect, not clean), listed below. One big-set run takes about 480 s under the machine load.
- The pass-9 unjudged rows M9-23, 33, 34, 64, 65, 67 were not touched. The tls group had no clean run and no mutants.
- jsonread.py is only 24 lines: it has NO size cap, depth cap of its own, duplicate-key check, BOM or encoding handling. Those live in src/lead_desk/regfile.py (load_json_file, read_regular_bytes). So the "new jsonread set" is 6 mutants of jsonread.py (J01-J06) and 7 of regfile.py (J07-J13, J12 and J13 not run).
- Clean runs (alone, before any mutant): reg on tree-M10: 504 passed, 3 deselected, 1 failed, rc 1, 151 s; rrc on tree-M10: 1015 passed, 1 failed, rc 1, 428 s; on tree-M10b (with the one failure deselected): mail 537 passed rc 0 170 s; live 453 passed rc 0 132 s; crm 409 passed rc 0 152 s. The one failure is the known-red test_r7f_findings.py::test_f1_a_connect_that_never_completes_ends_at_the_total_not_at_the_step (fails 3 of 3 alone in this sandbox: ImapConnectionError, not ImapTotalTimeout). The lead said: known-red, not mine, never counts as a killer. It is deselected in every mutant run, as are the 3 known socket-kind tests.
- Slips of mine, plainly: (1) I first started a clean run on the same tree a mutant lane was mutating; I stopped it at once and discarded it, then made tree-M10b; the copy caught a mutated run_real_check.py, which I replaced from R7J and verified with `diff -rq` (empty) before any result counted. (2) I stopped my lane A driver (SIGTERM) during M9-70 to free the slot for the lead's priority run; file restored from R7J, diff -rq empty. (3) At the end I stopped both drivers the same way and restored both trees from R7J (M10b regfile.py was mutated by J12 in flight); diff -rq empty for both.
- Selector sets: group files + tests/test_r7f..r7j_findings.py (rrc: 700 s limit). Big set: the 22 files of out/MAIL7/setC.txt + r7d..r7j finding files (900 s). Restore-by-sha after each mutant is in the TSV (all "restored-ok").

## Counts
40 mutants run (5 run_real_check, 11 smtp, 7 live_claude, 5 crm, 1 regfile from pass 9's list, 11 new JSON set). KILLED by the selector set: 23. SURVIVED the selector set: 17. Of those 17: 2 REAL GAP (big set), 1 EQUIVALENT (argued), 14 UNJUDGED.

## Confirmed REAL GAPS (sent to the r7k builder a6bc3c560189482f1; tests/test_r7k_findings.py is its file; lead told)
| id | file:line | mutation | what no test sees | killing test in words | evidence |
|---|---|---|---|---|---|
| M9-69 | scripts/run_real_check.py:1075 | `if answer != "y":` -> `if answer == "n":` | At the Start question every answer except exactly "n" (Enter, "yes", "x", "ok") starts the run. Worst kind: a mistyped answer starts a mail run, and in take mode touches the owner's real mailbox. | Drive the real `_run` with the answers "", " ", "yes", "Y es", "ok", "x", "no", "N": each must print "stopped, nothing was called", return EXIT_STOPPED, with no desk process, no mail attempt and no run folder; "y", "Y", " y " start; EOF stops. | selector rc 0 448 s; big set 1444 passed 1 skipped rc 0 481 s (raw-M9-69-wide.txt) |
| M9-16 | src/lead_desk/smtp_provider.py:154 | default port ssl 465 / starttls 587 swapped | With no DESK_SMTPP_PORT the provider picks the wrong port. | settings with starttls and no port must give 587, ssl and no port 465; an explicit port wins. | selector 164 s survived; big set rc 0 493 s (raw-M9-16-wide.txt) |

## EQUIVALENT (written argument)
- M9-68 (run_real_check.py:1069, `not (assume_yes and dry_fakes)` -> `not assume_yes`): line 973 refuses `--assume-yes` without `--dry-fakes` before the Start question is reached, so the two conditions agree on every reachable input. Two independent guards; each alone is enough. Selector set only, 385 s.

## UNJUDGED selector-set survivors (no big-set re-run; suspect; my reading is an opinion, not a verdict)
| id | file:line | mutation | note |
|---|---|---|---|
| M9-70 | run_real_check.py:1055 | banner worst-case mail count not multiplied by desk processes | banner understates what the person agrees to before Start; likely real gap |
| M9-71 | run_real_check.py:1052 | banner worst-case HubSpot calls not multiplied by desk processes | same |
| M9-13 | smtp_provider.py:126 | provider timeout 0 allowed | zero-budget class |
| M9-17 | smtp_provider.py:257 | recipient not checked ASCII in send | the outbox twin M9-26 is killed, the provider copy is not |
| M9-25 | smtp_outbox.py:149 | bare 3-char reply code not required to be digits | |
| M9-43 | live_claude.py:509 | worst case counts the question only, not the whole body | money path: reserve may be lower than the real worst case; likely real gap |
| M9-54 | crm_hubspot.py:392 | email path part not quoted strictly | |
| M9-55 | crm_hubspot.py:194 | allow-any-base-url on any non-empty text, not only "yes" | the key could go to a non-default host; likely real gap |
| M9-56 | crm_hubspot.py:164 | base url user name part not refused | |
| M9-57 | crm_hubspot.py:400 | 408 reply treated as plain refusal | |
| M9-58 | crm_hubspot.py:269 | _once: no check that time is left | |
| M10-J02 | jsonread.py:24 | `from None` removed | probably equivalent in effect (chained traceback only), not proven |
| M10-J06 | jsonread.py:23 | every ValueError relabelled "nested too deeply" | callers treat both as ValueError; only the refusal word differs |
| M10-J09 | regfile.py:146 | JSON file: BOM accepted (utf-8-sig) | no test says a BOM must be refused; likely low gap |

## KILLED (first failing test)
rrc: M9-72 test_real_check_dry::test_the_desk_child_gets_desk_and_real_names_from_the_config_only. smtp: M9-05 test_every_attempt_has_its_own_message_id...; M9-09 and M9-15 test_starttls_login_and_one_message_to_a_test_inbox...; M9-10 test_settings_validation; M9-11 test_r7m_new::test_f3_a_blank_or_space_padded_smtp_user...; M9-24 test_smtp_outbox::test_settings_from_env_and_checks; M9-26 test_odd_recipients_refused_early. live: M9-36 test_total_cap_spans_runs...; M9-42 test_worst_case_reserve_uses_max_tokens_as_output; M9-44 test_bad_token_counts_keep_the_worst_case_reserve; M9-45 and M9-47 test_error_body_and_retry_after_are_read_defensively; M9-46 test_ledger_append_is_flushed_to_disk. regfile: M9-63 test_r7_no_replace_of_special::test_the_check_and_open_output_both_refuse[fifo]. JSON set: J01, J03, J04 test_r7c_one_json_loader::test_the_loader_turns_deep_text...; J05 test_file_reader_refusals deep case; J07, J10 test_the_one_reader_refuses_every_bad_content...; J08 ...number_that_is_not_finite[1e999]; J11 ...[NaN]. Seconds and restore proofs: results-LA.tsv, results-LB.tsv.

## Observation (not a mutant result)
No JSON reader in the library refuses a repeated key (`{"a":1,"a":2}` silently gives 2). No code exists to mutate and no test pins either behaviour; the lead decides whether it matters for the config or ledger files.

## Next steps
Big-set runs for the 14 unjudged rows (about 8 min each; order M9-43, 55, 70, 71, 13, 17, 56, 54, 25, 57, 58, J09, J06, J02), then M9-73..82, J12, J13, a tls clean and mutants, and the pass-9 unjudged six. My drivers and their children are stopped; I touched no process of anyone else's.
