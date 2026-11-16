# F4: documentation that says something the code or the tool does not

FIRST (what failed or is uncertain):
* I did NOT run the whole test suite (the evidence runner does that). Run: 11 test files, 878 passed, 29 skipped (gitleaks missing x28, ntpath 3.13 x1). I did not run n8n, any real service, or Windows.
* Not reproducible in this tree: the `--collect-only -q` shape claims of versions.md:9 and docs/tests.md:79 (C8 saw them in a later tree, head e683069). In this tree (ee3d6ce) versions.md:9 and docs/tests.md contain no such text (`grep collect-only` finds only the 2516 sentence in tests.md:61, which says "counted with `--collect-only -q`": true, the last line is the total). So nothing to fix there; I wrote the two shapes down in docs/tests.md and pinned them in a test.
* Old test records (2449/2462/2516 passed, versions.md:9, limits.md:71, tests.md:60-64) are dated, commit-named run records, true for their commit. I kept them and labelled them as older than the count of this tree. I have NOT re-timed the full run, so README no longer promises a time.
* C10 hunks are claims from reading code. I re-ran only M1/M2 (partly: Config 8.0 shown; the two defaults read from code lines smtp_outbox.py:79, smtp_provider.py:88,323-330) and read the rest in code. C10's "script checks relative path from its own folder" is wrong in wording; code shows relative paths are opened from the folder you start in (scripts/run_real_check.py opens paths as given; desk child cwd=REPO line 1019): the patch text itself says "the folder you start the script in", which is right.

## Bug class
A documentation claim that was never checked against the tool's own output (a count that grew, a command that prints another shape, a start line missing a needed folder). Standard broken: honesty rule "never write verified without the command and its output" plus the project's wording rule.
Choke point: new test file `tests/test_docs_match_tools.py` reads each sentence from the page and runs the real command.

## Changes (file:line in the new tree)
* C10 patch applied (git apply, clean) and every hunk read against code: README.md:148 (precheck.py is not a command), docs/settings.md:3 (key files read at every call; live key kept in memory), :51 area (rota `crm_owner_id` key required, value may be empty), SMTP/SMTPP timeout defaults (5 s), HubSpot key bullet (every call, BOM accepted), allow-any-base-URL names, DPLD_REQUIRE_SCAN two files; docs/real-services.md:3, step 1 (replace `<...>`, no BOM, full paths), step 3 (start question, `--assume-yes`), checks F1-F6 location; scripts/real-run.env.example:19.
* scripts/crash_desk.py:3-5 and docs/tests.md:26: `PYTHONPATH=src:.`, demo servers must run first, the failure text named. REPRODUCED (out/F4/repro-crash-desk.log): with `src` only: `RuntimeError: ... the folder demo_only is missing`; with `src:.`: `desk listening on http://127.0.0.1:8765`. (In a netns with no loopback the `src` run fails earlier with "cannot reach the demo servers", so the error needs the demo servers running.)
* docs/tests.md:60 (new bullet): what `-q` and `-qq` print, and "This tree holds 3989 tests in 97 test files" (pinned). docs/tests.md:62: the 2516 run labelled "An earlier full run ... not the count of this tree".
* README.md:130: "about 20 minutes" replaced by the last timed figure (16 min 33 s for 2516 tests), "suite has grown since", "not timed again".
* README.md:20, :63, :80: replay note. Checked in code: desk.py:1361 `INSERT ... ON CONFLICT DO UPDATE` with `receipt_id INTEGER PRIMARY KEY AUTOINCREMENT` (schema.sql:7); SQLite 3.45.1 here consumes a number on the replay (raw check: rows (1,form,..),(3,webhook,..), sqlite_sequence 3). Also old "changes nothing" corrected (attempts counter goes up; no second lead or mail).
* docs/hubspot-probe.md:52-53: `--plan` does not check `--token-env`; a bad name is refused (and not printed) only with `--yes-spend-calls`. Run with a bad name: `--plan` prints the plan, exit path returns before the check (scripts/hubspot_probe.py:300 vs :305).
* load_tools/README.md:15-30: whole run start to finish. RUN as written in a no-network namespace with loopback up (out/F4/recipe-run.log): driver 30 requests, `/counts` pending_followups 0, "ALL 7 CHECKS HOLD", check rc=0. Empty model log explained (check 5 = 0 calls for 0 leads).
* tests/test_docs_match_tools.py (new, 7 tests): -q shape, -qq shape and sum, doc count vs collected count (tests and files), both crash texts name the same path, crash script really starts with the documented path and stops at D2 (exit 137, one mail), replay skips a receipt number, probe name check.

## Sibling sweep
grep PYTHONPATH over *.md,*.py,*.sh,*.ps1,*.yml: contract.md:68, README.md:58,75,132 and docs/tests.md use `-m` forms (cwd goes on the path, correct); scripts/feed.py:3 uses `src` only: `feed.py --help` runs with it (feed imports no demo_only); start_all/reset use `src:.`; load_tools/README.md:4 `src:.`. Only crash_desk was wrong. "first CRM call / first send" and "same as DESK_SEND_TIMEOUT" no longer occur (grep empty). Not edited (not mine / need code): C5 `scripts/n8n_api.py --help` prints no usage; C10 "NEEDS CODE" list (feed.py tracebacks, --dry-port-base 99999 text, run_live_check --price-date/--effort validation); C3 DPLD_REQUIRE_DEMO "only conftest.py" left (the guard test only sets it for a child run, so the text is true).

## Fails before (raw: failing-before.log, failing-before-2.log)
Old text of the 4 changed pages/scripts + new tests: `5 failed, 2 passed` (count sentence missing, `-q` text missing, crash script RuntimeError demo_only missing, README receipt_id 3 missing, probe sentence missing). Second run, new text with stale number 2516: `assert 2516 == 3987` failed (1 failed, 4 passed).
## Passes after (passing-after.log)
`878 passed, 29 skipped in 103.85s` (test_docs_match_tools, test_hygiene, test_gitleaks_exceptions, test_env_numbers, test_path_confinement, test_load_tools, test_desk_address_required, test_real_run_v6, test_hubspot_probe, test_crash_points, test_vendor_hosts); `lead_desk.__file__` was under tree-F4/src.
## Ruff (ruff.log)
`ruff format --check`: 2 files already formatted; `ruff check`: All checks passed! (tests/test_docs_match_tools.py, scripts/crash_desk.py; markdown not covered by ruff.) mypy does not cover tests/ in this repo (pyproject files list).
## Not run
Full suite; mutation; Windows text (`src;.`) not run; README Try-it block not re-run end to end (receipt 3 shown by the new test instead); gitleaks (absent); n8n.
Processes started by me still running: 0 (pgrep empty). Scratch: tmp-F4, tree-F4 has `git add -N` on the new test file only (so it shows in the diff); no commit.
