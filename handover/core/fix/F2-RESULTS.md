# F2 results: command-line parsing (builder F2, tree /home/user/build/rr6/tree-F2, baseline ee3d6ce, nothing committed)

## What failed or is uncertain (first)
- NOT run: the full suite, mutation runs, Windows, any live call, any network. I ran only the touched test files (logs below). The evidence runner must do the full suite.
- UNVERIFIED: the effort words in `LIVE_EFFORTS` (low, medium, high, xhigh, max; src/lead_desk/constants.py:175) were NOT checked against the vendor page (no network). Re-verify before a live run.
- MY CHOICES, not given by the brief: price-date must be YYYY-MM-DD, not before 2023-01-01, and at most 1 day in the future; the key-file limit is 4096 bytes (the value the HubSpot and SMTP readers already had).
- Still shown on purpose: scripts/n8n_api.py prints the exception CLASS name for an unreadable workflow file (no typed value). Existing tests pin it (tests/test_n8n_api_url.py:651 needs "RecursionError"), so I kept it. run_real_check also shows a class name for a generic OSError (pinned by tests/test_take_script_refusals.py:726).
- Tests run under `unshare -n` when the machine allows it, else plain (no network is opened either way; stdin is closed so no prompt can be answered; no prompt appeared).
- One existing test pinned the old live key rule; I changed it (tests/test_core_key_readers.py): the new size limit is the deliberate fix C2(b), so a file over 4096 bytes is now refused. This is a changed expectation, not a deleted test.
- During the last run the kernel killed a process for memory (shared limit); the run still finished with 355 passed, no failure.

## Bug class
User-typed text echoed back, or an exception name shown, instead of one fixed refusal line; and checks that can still raise after the start question. Standard broken: the studio rule "no secret is ever printed" and the repo rule "fixed refusal text, no typed value". Fix at the choke point `RefusingParser.error` (tools/refusing_args.py): output is always `refused: <OPTION>: <fixed text>` on stdout, exit 2; argparse's own text (which holds the typed value) is never printed. Values are validated in one function per script (`option_problem`).

## Changed files (see fix.patch; line numbers at the final state)
- tools/refusing_args.py (new): shared parser, `refusal()`.
- scripts/run_live_check.py: import :53, `option_problem` :197 (leads, runs, base-url, price-date form/floor/future, effort :215, duplicate model, empty values), parser :224, ledger stop text :321 (fixed text, no class name; C2(c)).
- scripts/run_real_check.py: import :114, DRY_PORT_COUNT :117, parser :1083, `option_problem` :1103 (--dry-port-base 1..PORT_MAX-4; --dry-smtp-script must be a known script and needs --dry-fakes), `run_dir.mkdir` guarded :1294 plus pre-question check (C2(a)).
- scripts/precheck.py: `folder_cannot_be_made` :40; TypeError guards in `is_special_file` :14, `folder_part_is_a_file` :25, `same_file` :55 (C2(d)).
- scripts/feed.py :26/:64 (class swap only; the `ap.error("give exactly one of --index or --all")` line is untouched and maps to a fixed text in tools/refusing_args.py; F1 owns the rest of feed.py).
- scripts/hubspot_probe.py :34/:289 (its _Quiet class removed), scripts/n8n_api.py (two messages made fixed, no typed value).
- load_tools/catcher.py :183, check_invariants.py :669, load_driver.py :406 (also scenario message and float ValueError handling).
- demo_only/fakes_server.py :241, fake_model_server.py :243, burst.py :140; demo_only/fake_smtp_tls.py (SCRIPTS tuple).
- src/lead_desk/constants.py :175 LIVE_EFFORTS, :185 SECRET_FILE_MAX_BYTES; live_claude.py :426-428 bounded read and too-large refusal (C2(b)); crm_hubspot.py and smtp_provider.py use the shared constant.
- tests: tests/test_cli_refusals.py (new), tests/test_core_key_readers.py (live oracle updated), tests/test_sonar_p2_feed_optional.py (stdout is the generic refusal and the typed word is not printed).

## Sibling sweep (every ArgumentParser use, grep ArgumentParser)
All now RefusingParser: scripts/run_live_check.py, run_real_check.py, feed.py, hubspot_probe.py; load_tools/catcher.py, check_invariants.py, load_driver.py; demo_only/fakes_server.py, fake_model_server.py, burst.py. n8n_api.py has no argparse (messages only). Tests cover each with a fake key (built from parts) as option value, `--opt=K`, stray positional, abbreviation, and subcommand slot.

## C2 items and their tests (all in tests/test_cli_refusals.py; all fail on the old code)
(a) run folder cannot be made (NUL byte in DESK_DB_PATH, read-only mount): refused before the start question. (b) one key-file limit for live, HubSpot, SMTP. (c) ledger stop text fixed. (d) precheck TypeError guard (one-line guards like the siblings).

## Fails before / passes after (raw logs)
- failing-before.log: baseline code (ee3d6ce) plus only the two new constants copied in so the tests import: 109 failed, 32 passed. The fake key appears in that log 356 times (the echo).
- passing-after.log: tests/test_cli_refusals.py, test_core_key_readers.py, test_sonar_p2_feed_optional.py, test_real_check_dry.py, test_take_script_refusals.py: 355 passed.
- passing-after-3.log: also test_hygiene, live_claude, smtp_provider, crm_hubspot, env_numbers: 678 passed, 4 skipped (no gitleaks program).
- earlier batch passing-after-1: 1065 passed, 2 skipped (before the last small edits).
- ruff.log: `ruff check` All checks passed; `ruff format --check` 21 files already formatted (line length is 120 in this repo, not 100).
