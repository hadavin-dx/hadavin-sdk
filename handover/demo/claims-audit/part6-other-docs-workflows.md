# Part 6: n8n-recipe, hubspot-probe, real-services, why-this-code, workflows, n8n JSON
Repo: /tmp/claims-main (c30c373). Read-only. No test was run (backing found by reading). Test names are from reading the assertion, not from execution.
Legend: K = KEEP, T = BACKED-BY-TEST, U = UNBACKED.
Standing note for the n8n/hubspot docs: every "checked / tried once / run on 2026-11-09 / logs not shipped" result below comes from author runs; no log is in the repo, so they are U by the brief's rule (the docs themselves say "logs not shipped").

## docs/n8n-recipe.md
| line | words | backing | verdict |
|---|---|---|---|
| 4 | "were run against the desk on 2026-11-09, on one computer, in a real n8n ... lines say 'checked' where that run showed it (tried once by the author, logs not shipped)" | none in repo (versions.md:16 gives only the version "the n8n runs, once") | U: result from a run whose log is not in the repo (the text says so itself) |
| 4 | "Every step marked 'not checked' has not been tried" | honest scoping, no number | K |
| 10-12 | "Checked ... placeholder node ids (node-1 ...) are accepted on import ... webhook keeps the same address (/webhook/desk-form)" | n8n/desk-form.json has node-3 ids, path desk-form (file); acceptance by n8n itself has no log | U: n8n-run result, log not in repo. The path-in-file part is K |
| 10 | "The files contain no credentials" | n8n/*.json read: no credentials keys; tests/test_hygiene.py::test_hygiene_scan_public scans repo | T |
| 13 | "the file's 'active' flag is ignored by the import call" | no log; desk-form.json has "active": true, so the flag exists | U: n8n-run result, no log |
| 17-22 | "n8n version used: see versions.md ... regular mode, one process, SQLite" | versions.md:16 (2.46.6) | K |
| 22 | "they use only the Webhook, Edit Fields, HTTP Request, Code and Manual Trigger nodes" | node types in the 3 JSON files: webhook, set, httpRequest, code, manualTrigger | K |
| 23 | "Never commit the e-mail, the password or the key anywhere" | advice | K |
| 26 | "The desk answers 403 forbidden_host to any Host name it does not know (anything but 127.0.0.1, localhost, [::1])" | src/lead_desk/server.py:740,742; tests/test_portal_api.py (forbidden_host) | T |
| 26 | "Checked: n8n run directly with Node reached the desk ... on 127.0.0.1. Not tried: n8n in Docker." | no log | U: run result, log not in repo |
| 27 | "demo ran n8n on port 5679 ... scripts/n8n_api.py default http://127.0.0.1:5679 ... proof workflow URL http://127.0.0.1:5679/webhook/desk-form" | scripts/n8n_api.py:3,84; n8n/proof.json "Send all ten" node url | K |
| 34 | "Checked: the id inside the request body works, and a replay of the same id was recognised ("replayed": true)" | the field exists: src/lead_desk/desk.py:1296; a replay test in tests/test_desk*.py not individually read. Through n8n: no log | U for the n8n part (log not in repo); desk behaviour itself is covered by desk tests |
| 36 | "the execution id changes on a re-run, so it is the wrong choice" | n8n behaviour, no source | U: claim about n8n with no source in the repo (reasonable, unchecked: the same paragraph says "n8n's own execution id was not tried") |
| 44 | "Its timeout is well above the desk's default send timeout of 5 seconds" | n8n/desk-form.json timeout 15000; src/lead_desk/config.py:429 5.0; docs/settings.md:21 | K |
| 44 | "a 400 or a 413 shows red in n8n" | n8n behaviour; see line 54 | U: n8n-run result, no log |
| 46 | "Checked: reply body passes through unchanged, but the HTTP status does not: the caller always gets 200 ... A 400 or 413 ... makes the caller get n8n's 500" | no log | U: n8n-run result, no log. ("always" is absolute) |
| 48 | email workflow mapping (path desk-webhook, message_id, from_name, from_email, body) | n8n/desk-webhook.json read (same 3 nodes) | K |
| 50-53 | list of what was checked, steps 1-6 (201 new, 200 duplicate, replayed true, 202 review, 400/413 red) | desk statuses 202/review in tests/test_desk_edge_cases.py:141,194; through-n8n results have no log | U for the n8n run; desk-side T |
| 54 | "'Retry On Fail' on, 3 tries, 1 second apart" | n8n/desk-form.json: retryOnFail true, maxTries 3, waitBetweenTries 1000 | K (for desk-form; desk-webhook.json not diffed field by field) |
| 54 | "desk stopped and started again about one second after the call, the call succeeded on the second try ... one lead, one CRM row, one e-mail" | no log | U: result from a run whose log is not in the repo |
| 54 | "With the desk down for a few seconds the call failed ... (within about 2 seconds)" | no log | U: timing from a run, no log |
| 54 | "The retry also repeats a 400 or 413 (3 tries each): the desk counts each rejected call 3 times" | no log | U: run result, no log |
| 54 | "n8n's 'Retry On Fail' cannot skip retries for 4xx replies" | n8n behaviour, no source | U: absolute claim about n8n with no source |
| 58 | "demo servers ran in blind counting mode (--crm blind --outbox blind; the CRM default is keyed...)" | demo_only/fakes.py:53,66 has blind/keyed; the flag spelling and "CRM default is keyed" not checked | U: default not confirmed in 5 minutes (partial) |
| 58 | "request bodies ... are in the /fake/... rows of the HTTP table in contract.md" | contract.md exists at repo root | K |
| 60-63 | patterns (a)-(d), "described only", "no result claimed" | descriptive | K |
| 67-68 | "The counts come from the demo servers' own counters, never from n8n's own success mark" | n8n/proof.json: Read the desk counts / Read the demo CRM / Read the demo outbox nodes | K (workflow design); "never" holds for that workflow |
| 68 | "in the one try, n8n's executions list showed success for a duplicate caller that was answered with an error" | no log | U: run result, no log |
| 70 | "Checked: all ten requests were sent together. The desk stored all ten within the same second ... 1 new lead and 9 duplicates, 1 CRM row, 1 e-mail (first import and after clean re-import, 2026-11-09)" | proof.json batchSize 10, batchInterval 0 shows intent; the run result has no log | U: result from a run whose log is not in the repo |
| 70 | "The same holds when the ten calls go through the n8n web address of the web form source" | no log | U |
| 70 | "result ... now says PASS only when ... exactly one new and nine duplicate" | n8n/proof.json line 272; tests/test_n8n_proof_result.py::test_pass_needs_one_new_nine_duplicates_one_email_and_one_crm_row and ::test_any_other_set_of_answers_is_a_mismatch_even_with_one_email_and_one_crm_row (run in node, skipped if node is missing) | T |
| 70 | "That new rule was checked only by running its text in node ... n8n itself was not started" | tests/test_n8n_proof_result.py needs_node; honest | T |
| 70 | "A MISMATCH ... if the desk is busy and answers 503 busy (it can, under ten at once)" | server.py:401-417 busy 503 exists; "under ten at once" no test read | U: claim "it can under ten at once" has no test or log (plausible) |
| 70 | "scripts/n8n_api.py has no delete command ... activate refuses when two workflows share a name" | scripts/n8n_api.py:1,4,181,186 (import/activate/deactivate/list only); the refusal on two names not read | T for no delete; activate refusal not confirmed |
| 74 | repeats the three workflow names / file names | n8n/*.json "name" fields match | K |
| 76 | "n8n answers 200 whenever the desk answered" | as line 46 | U: run result, no log |
| 77 | "n8n repeats such a refused request 3 times, so the desk counts each refused call 3 times" | as line 54 | U: no log |
| 78 | "Restart tolerance is short ... second try succeeded (about one second) ... all three tries used up" | as line 54 | U: no log |
| 79 | "1 email and 1 CRM row in the runs made ... all ten within the same second" | as line 70 | U: no log |
| 80 | "must be switched on by hand (the import call ignores the active flag)" | as line 13 | U: n8n-run result |
| 81 | "It accepts Host: 127.0.0.1, localhost and [::1]" | server.py:740; docs/settings.md:24 | T |
| 82 | "Not checked here: ..." list | honest | K |

## docs/hubspot-probe.md
| line | words | backing | verdict |
|---|---|---|---|
| 3-4 | "Result: the only real-service try, run by the author on one free HubSpot account, logs not shipped. In the first run create, lead-status write, read-back and permanent delete passed, owner list refused (403 MISSING_SCOPES) ... second run passed every step, third run listed two owners" | no log or evidence file in the repo | U: result from runs whose logs are not in the repo (text says "logs not shipped") |
| 4 | "Each run used 6 or 7 of the 8 calls and left no contact behind" | script prints "calls used: N of 8" (scripts/hubspot_probe.py:326) but no log | U: run result, no log |
| 6 | "never on an account that holds real contacts" | advice | K |
| 6-9 | "an owner assignment can send that user a notification email" | line 71 says UNVERIFIED | U: stated as "can" while line 71 lists it as unverified (internal tension, mild) |
| 11 | "7 calls on the normal path, never more than 8 including retries" | scripts/hubspot_probe.py:44 CALL_BUDGET=8, :47 PLANNED_CALLS=7; tests/test_hubspot_probe.py::test_429_retries_are_counted_and_the_budget_stops_the_run, ::test_gdpr_429_forever_stays_inside_budget, ::test_happy_path_count_matches_plan | T |
| 13 | "Checks whether the contact property dpld_tag exists" | probe.py:37; tests ::test_tag_property_present_is_written | T |
| 14 | "Reads up to 10 owners; prints the count and the last 4 characters of each id" | probe.py:188 (limit=10), :99 ([-4:]) | K (the test of the printing not read) |
| 15 | "ONE contact with a made-up address probe-<random>@example.com" | tests/test_infra.py::test_seeded_demo_addresses_end_in_example_com covers other files; probe address built in script not read | K (low risk) |
| 17-18 | "owner and lead status in their own calls" | tests ::test_owner_and_lead_status_are_written_in_separate_calls | T |
| 19 | "Always deletes it" | tests ::test_cleanup_after_failure_at_each_step, ::test_delete_falls_back_to_normal_delete, ::test_both_deletes_fail_warns_and_fails (the last one shows "always" can end in a WARNING, which the text explains) | T |
| 20 | "When the create answer was lost, only the permanent delete by email is tried" | tests ::test_lost_create_never_uses_a_by_email_normal_delete | T |
| 22-28 | "the 8th call is always kept for the permanent delete ... Worst case is exactly 8 calls ... prints WARNING naming the contact / exact address" | probe.py:45 DELETE_RESERVE=1, :110; tests ::test_budget_stop_still_deletes_with_reserve, ::test_cleanup_ignores_normal_limit_but_not_the_hard_budget, ::test_unknown_create_outcome_that_cannot_be_deleted_warns_with_the_email | T |
| 30-31 | "It never prints the token or a header ... first 100 characters of the message, with the token replaced by ***" | probe.py:168 ([:100], replace token); tests ::test_token_echoed_in_a_4xx_message_is_masked, ::test_no_token_in_exception_text, ::test_token_pasted_as_env_name_is_never_echoed | T |
| 31 | "the probe does not test the combined call" | honest | K |
| 33-36 | "after you have agreed to the 7 calls ... python -I scripts/hubspot_probe.py --yes-spend-calls 7"; "the only place where a secret is read from a variable" | tests ::test_refuses_wrong_count_missing_token_and_token_argument covers the count flag; "only place in this repository" not grepped across repo | U: "the one place in this repository" is an absolute with no check (not grepped) |
| 41-43 | "exact scope names are UNVERIFIED" | honest | K |
| 45-46 | "if the token lacks it, HubSpot answers 403 and the script reads that as 'property absent' ... harmless" | probe.py tag check not read in detail; no test name found for the 403 path | U: 403 handling of the tag check not confirmed (5 min) |
| 52-54 | "--token-env NAME ... plain variable name, anything else refused without being printed"; "--dry-run ... loopback only" | tests ::test_token_env_name_longer_than_32_is_refused, ::test_unset_token_variable_name_is_not_echoed, ::test_dry_run_refuses_non_loopback | T |
| 58-64 | "Confirmed from HubSpot's developer pages and changelog on that date (2026-11-11): create is POST /crm/v3/objects/contacts ..." | tests/test_crm_hubspot.py and probe paths show the endpoints in code; the reading of HubSpot pages on 2026-11-11 is not in the repo | U: external-documentation claim, source not in repo (named only, no URL or copy) |
| 66-68 | "a free account accepted the owner write and hs_lead_status write; an address ending .test was refused with a 400 ... example.com accepted" | tests/test_infra.py::test_seeded_demo_addresses_end_in_example_com cites "probe 2026-11-11" but is a rule, not a log | U: run result, no log |
| 70-73 | "UNVERIFIED ...". "The runs showed that OPEN was accepted ... permanent delete answered 204" | no log | U: run result, no log |
| 75-77 | "Sources (names only) ... Read on 2026-11-11" | no copy | U: same as 58-64 |

## docs/real-services.md
| line | words | backing | verdict |
|---|---|---|---|
| 4 | "You do not need this section to run the demo" | descriptive | K |
| 5 | "This script is an untested reference: it was exercised only against the demo stand-ins (--dry-fakes)" | tests/test_real_check_dry.py::test_dry_fakes_run_end_to_end | T |
| 7 | "has not been run against a real HubSpot account or a real Gmail mailbox. The only real-service try so far is hubspot_probe.py ... logs not shipped" | consistent with hubspot-probe.md; but see NOTE | K for the "not run" side; the probe claim is U as above |
| 7 | "Everything else in this repository ran against demo stand-ins" | no log either way | U: absolute-style claim about all runs, no source |
| 9 | "about 12 invented people at the address ending example.com" | scripts/run_real_check.py:101 DEFAULT_PERSONS = 12, :100 EMAIL_DOMAIN | T/K (code) |
| 9 | "nobody outside your own inboxes receives anything" | comment run_real_check.py:97-99 "follow-ups go only to the configured inboxes"; a test of this not read | U: guarantee, no test found in 5 minutes (code comment only) |
| 9 | "it asks y/N after printing the worst-case number of calls, mails and dollars, and it refuses to start without explicit caps" | run_real_check.py:34-35 (docstring), :7 ("refuses to start without every one of them"), :846 | K (docstring); refusal without caps not test-read |
| 11 | "Secrets are never in that file, only the paths of one-line key files" | scripts/real-run.env.example exists; not read | K (not verified line by line) |
| 12 | "1a. Before turning lead stages on ... (required)" and cross-reference docs/limits.md "Which CRM stage things the desk touches" | docs/limits.md:139 heading exists | K |
| 14 | "the program never creates properties" | not grepped | U: absolute, no check found |
| 16 | "one person with two different addresses ... the desk also treats them as two leads, and the result says so" | not read | U: no test found (5 min) |
| 16 | "counts ... by the header X-Send-Key (no body or address is read)" | run_real_check.py:228 reads X-Send-Key with a regex over the data `d`; "no body is read" not shown by that line | U: "no body or address is read" has no test; the regex runs over raw data |
| 18 | "What it would NOT show: ..." | honest | K |
| 18 | "After a hard crash a mail that was in flight is recorded unknown on purpose" | run_real_check.py:CRASH_REASON; desk tests | K |
| 20 | "Exit code 0 only when every check in its table passes" | run_real_check.py:313 list of F-checks; EXIT_* at :95; test_real_check_dry is the only run | T (dry only) |
| 20 | "Failure tables print no address and no setting value" | _ADDRESS regex at :120 suggests masking; no test read | U: guarantee, no test read |
| 20 | "The CRM key is sent only to the CRM vendor's own API host names" | not verified (src/lead_desk/crm_hubspot.py host check not read) | U: guarantee, not confirmed |
| 22 | "can be anywhere ... LEAD_DESK_PATH_ROOTS do not apply ... refused ... --config <(command)" | not read | U: no test found in 5 min |

NOTE real-services.md line numbers: file line numbers are 1-22 (wc says 22 lines); long paragraphs, so "line" above maps to paragraph. Numbered here by paragraph order, not exact line.

## docs/why-this-code.md (29 lines; table rows by line)
| line | words | backing | verdict |
|---|---|---|---|
| 3 | "Only n8n was compared for the main question; no other tool was evaluated" | honest | K |
| 13 | "n8n alone, four patterns, tried once on one computer (the workflows and logs are not in this repository)" | n8n-recipe.md section 2 says the patterns are "not shipped" | K (consistent); the run itself U: no log |
| 13 | "a crash between the CRM step and the email step is covered by tests in this repository" | tests/test_hung_adapter_calls.py, tests/test_mode_safety.py (mirror step tests); a specific crash-between test not read | U: guarantee, specific test not named/confirmed |
| 14 | "A unique key, one atomic insert, survives a restart ... rules enforced by the database" | docs/limits.md:87 (triggers) -> test_write_once_triggers, tests/test_migration_triggers.py | T |
| 19 | "ask a system that cannot recognise a repeat only once" | blind/keyed in demo_only/fakes.py; adapters not read | K |
| 19 | "built and tested against local stand-in servers; only scripts/hubspot_probe.py touched a real service ... the desk's HubSpot adapter itself never did" | consistent with real-services.md; no log | U: result from author runs, no log (the "never did" is absolute and cannot be shown from the repo) |
| 20 | "Ready-made load tools (for example k6, vegeta, hey) cover firing requests" | external claim, no source | U: number-free but unsourced claim about third-party tools |
| 21 | "Seven checks after a load run (check_invariants.py)" | load_tools/check_invariants.py; count of 7 not confirmed by me | U: "seven" not counted (5 min) |
| 22 | "two copies of it exist ..., kept in step by a test" | tests/test_burst_retry.py:121 test_the_burst_script_and_the_load_driver_wait_the_same | T |
| 23 | "Secret scan: gitleaks ... Ready-made tool, run in the checks" | .github/workflows/lint.yml:44-48 | K |
| 24 | "n8n export scrub (tools/) ... Under 100 lines, no business logic" | tools/scrub_n8n_export.py is 202 lines (wc -l) | U: FALSE: the file is 202 lines, not under 100 |
| 28 | "a test fails if one is missed" (adding a kind) | tests/test_mode_safety.py::test_every_kind_is_listed_in_the_places_that_describe_it covers constants vs CRM_FIELDS_SENT vs real_services only; it does NOT check loader.py, nor that a module exists, nor the "must not import from demo_only" rule | U: "a test fails if one is missed" is only true for steps 2, 4, 5 (partial). Steps 1, 3, 6 not covered |
| 28 | "a real kind goes in its own module under src/lead_desk/ and must not import from demo_only/" | src/lead_desk/loader.py:48,91,111 import demo_only dynamically (loader is not a "real kind" module); no test found that real-kind modules avoid demo_only | U: rule with no test found |
| 28 | "kinds: CRM_CHOICES (fake, hubspot), OUTBOX_CHOICES (http, smtp, smtp_provider), QUALIFIER_CHOICES (recorded, live_claude)" | src/lead_desk/constants.py:119,121,128 | K |
| 28 | "This demo ships exactly one real CRM kind ... one real AI kind" | constants.py:128 | K |

## .github/workflows/codeql.yml
| line | words | backing | verdict |
|---|---|---|---|
| 1 | "Do NOT also enable GitHub's default setup" | instruction | K |
| 2 | "Actions are pinned to full commit SHAs (looked up 2026-11-09, re-checked 2026-11-12: still the newest releases)" | pins present (lines 31,35,40); tests/test_hygiene.py::test_workflows_are_pinned_and_limited asserts SHA pinning; "newest releases" no source | T for pinning; U for "still the newest releases" (external, no source) |
| 3 | "Languages (ids checked against GitHub's CodeQL documentation on 2026-11-12)" | no copy | U: external check, no source in repo |
| 4 | "No result of this scan is claimed here" | honest | K |
| 5 | "limit: if the first run refuses one of the languages, remove it" | instruction | K |
| 14 | "weekly, Monday" (cron "17 4 * * 1") | cron field | K |
| 22 | timeout-minutes: 30 | codeql.yml:22 (tests/test_hygiene.py:_workflow_problems limits timeouts only for semgrep job as read) | K |
| 25 | "GitHub's codeql-action README: every advanced-setup workflow must have it (read 2026-11-12)" | no copy | U: external citation, no source |

## .github/workflows/lint.yml
| line | words | backing | verdict |
|---|---|---|---|
| 2-4 | "every third-party Action is pinned to a full commit SHA ...; read-only permissions; no repository secrets exist; GitHub-hosted runner only; no pull request text is ever placed inside a run: step" | SHA/permissions: tests/test_hygiene.py::test_workflows_are_pinned_and_limited; lint.yml:13-14 permissions read; ubuntu-24.04. "no pull request text in a run: step" is tested only for semgrep.yml (tests/test_nosemgrep_form.py), not for lint.yml (lint.yml has no github.event reference by reading). "no repository secrets exist" | SHA/permissions T; "no repository secrets exist" U: STALE: sonar.yml:61 uses secrets.SONAR_TOKEN, and docs/tests.md says the secret exists; "never placed in a run: step" has no test for lint.yml |
| 19 | "timeout 60 ... generous on purpose: the runner speed is not measured yet" | number is a ceiling, honest | K |
| 21-24 | GITLEAKS_VERSION 8.30.1, SHA-256 "copied from the release's published checksums file ... on 2026-11-09" | value present; source not in repo | U: checksum provenance not verifiable here |
| 39 | `sha256sum --check` of the tarball | workflow line | K |
| 38 | `--proto '=https' --tlsv1.2` | tests/test_workflow_run_flags.py::test_a_download_in_a_workflow_is_https_only_and_modern_tls | T |
| 45 | "--ignore-gitleaks-allow makes inline allow comments count for nothing" | gitleaks docs, not in repo | U: external claim, no source |
| 35 | "the scan runs first: ruff, mypy and bandit write cache folders ... gitleaks dir would read them" | reasoning, not tested | K |
| 52 | "--require-hashes --only-binary=:all:" | tests/test_workflow_run_flags.py::test_a_pip_install_in_a_workflow_takes_wheels_only_with_hashes | T |
| 59-62 | "Mypy (both platform branches)" | pyproject.toml:42-43 | K |
| 70-83 | "anything left after the exceptions fails the job" | lint.yml:79-82 (exit 1) | K |
| 85-90 | "Canary guard (fails loudly if the scanner canary test is missing)" -> prints "The scan cannot be trusted" | tests/test_hygiene.py:124 test_hygiene_scan_public exists | T |
| 97-98 | "without it most test files would skip and the run would look green" | tests/conftest.py:19-22; tests/test_demo_folder_guard.py | T |

## .github/workflows/semgrep.yml
| line | words | backing | verdict |
|---|---|---|---|
| 1 | "No account, no token, no repository secret, metrics off" | workflow has no secrets; --metrics=off at :71; test_nosemgrep_form refuses secret/token references | T |
| 1 | "engine licence LGPL-2.1" | no source | U: external licence claim, no source in repo |
| 2-4 | rules licence "Semgrep Rules License v1.0: own internal use only, not redistributed ... that text was not fetched or read" | text admits unchecked | U: licence statement stated, then disclaimed (kept honest by its own words) |
| 19 | "a push to main does not cancel a run already running ... safe only while github.ref stays in the group name"; "GitHub may still replace a pending run ... NOT measured" | tests/test_nosemgrep_form.py:178 test_semgrep_workflow_does_not_cancel_a_running_push_to_main | T (first half); second half honest |
| 26 | "timeout 20 ... a ceiling, not a measurement ... the install took 17 s on a fast link in one test" | tests cap timeout at 20 (test_nosemgrep_form.py:333,441); "17 s" has no log | U: "17 s" number with no source in the repo |
| 39 | "--no-deps ... only ready-made wheels from the lockfile are installed" | tests/test_workflow_run_flags.py; requirements-semgrep.txt:932 semgrep==1.185.0 | T |
| 41-43 | "pip check ... semgrep --version" | workflow lines 45-46 | K |
| 49-51 | "rules ... cannot be pinned (there is no versioned pack, and copying the rules ... is not allowed by their licence)" | external claim, no source; licence text declared unread at line 3 (contradiction: a prohibition is asserted though the text was not read) | U: STALE/inconsistent: states the licence forbids copying while line 3 says the licence text was not read |
| 51 | "Keep it OUT of the required checks" | advice | K |
| 52-53 | "Exit codes (seen with this pinned Semgrep 1.185.0 on a made-up local rule, and with the registry blocked): 0 clean, 1 findings, 2 ..., 7 ..." | tests/test_nosemgrep_form.py:473-476 test only the stand-in; observations on the real tool have no log | U: result from author runs, no log |
| 54-55 | "run 43403502735, 2026-11-13, head 15b8b15e: 'Scanning 64 files tracked by git with 79 Code rules', 'Ran 77 rules on 47 files: 0 findings', exit 0" | same text in docs/tests.md:36 (a copy, not the log); no log in repo | U: result from a CI run whose log is not in the repo (the repo's HEAD is c30c373, not 15b8b15e; commit 15b8b15e not in this checkout's history by `git log -1`, not further checked) |
| 56 | "A green job alone does NOT prove that rules ran" | reasoning; docs/tests.md:36 | K |
| 58 | "Only exit 2 is retried (3 tries); findings are never retried" | tests/test_nosemgrep_form.py:473-486 test_scan_step_retries_only_exit_2 | T |
| 61 | "with --strict some files that cannot be parsed ... exit 3, without it exit 0 (made-up local test, 1.185.0); `def f(:` alone gave exit 0 even with --strict" | no log | U: result from a local run, no log |
| 71 | scan command with --strict --error --severity ERROR | tests/test_nosemgrep_form.py "scan command word for word" (docs/tests.md:34) | T |
| 66-67 | "An echo cannot change the exit code of the scan" | script reading: echo before loop, status set by loop | K |

## .github/workflows/sonar.yml
| line | words | backing | verdict |
|---|---|---|---|
| 1 | "Runs on Linux (ubuntu-24.04, the same runner image as lint.yml) only" | line 29 | K |
| 2-3 | "otherwise the scan stops with 'You are running CI analysis while Automatic Analysis is enabled'" | SonarQube Cloud message, no source | U: quoted vendor message, no source |
| 4 | "The token is the repository secret SONAR_TOKEN (owner-created, read-only to this file; never printed)" | line 61 only use; "never printed" no test (GitHub masks secrets by itself) | U: "never printed" not tested here |
| 5-6 | "the job runs the Python test suite once (serial, as in docs/tests.md) ... The Playwright tests skip here, as in lint.yml" | requirements-dev.txt/coverage.txt contain no playwright (0 hits); tests use pytest.importorskip("playwright.sync_api") (tests/test_mode_safety.py:110, tests/test_portal_browser.py:27) | T |
| 7-11 | "SONAR_TOKEN is NOT in the environment of the install and test steps (set only on the scan step, checkout keeps no credentials)" | sonar.yml:47-51 test step has only DPLD_REQUIRE_DEMO; :60-61 scan step has SONAR_TOKEN; persist-credentials false at :37 | K |
| 10-11 | "a pull request from a fork or from Dependabot never runs this job (the if: below)" | sonar.yml:32 `if:`; GitHub's own behaviour for fork secrets is external | K (code) |
| 12 | "A two-job split ... is an open owner decision" | statement of status | K |
| 30 | "timeout 60 ... same as lint.yml until a real run ... then 1.6 times the longest observed run" | lint.yml:19 also 60; "1.6" is a plan, note lint.yml:19 says "about twice" (different factor in two files) | U: STALE/inconsistent: lint.yml:19 says set it to about twice the first run, sonar.yml:30 says 1.6 times |
| 42-44 | "pip refuses to run when a package is pinned to two versions (tested, pip 24.0)" | no log | U: result from a local test, no log |
| 44 | "--only-binary: wheels only, so no package build script runs before the test step" | tests/test_workflow_run_flags.py (flag present); the consequence is reasoning | T/K |
| 49-50 | "without it most test files would skip and the figure would be wrong" | tests/conftest.py:19-22 | T |

## n8n/*.json
The three files (desk-form.json, desk-webhook.json, proof.json) hold no "note", "notes" or "description" fields. Checked by loading each node with python: only name, type, id, position, typeVersion, parameters, and retryOnFail/maxTries/waitBetweenTries on the send node. Nothing to log as a claim. Node NAMES are plain ("Wait for the desk to finish" etc.). The `result` expression text (proof.json:272) prints "PASS" or "MISMATCH": PASS needs exactly 1 new, 9 duplicate, outbox count 1, CRM count 1 -> T (tests/test_n8n_proof_result.py). The sleep in node "Wait for the desk to finish" is a fixed 4000 ms (docs say "waits a few seconds": K).

## Counts (by first letter of the verdict cell, counted by script; 'mixed' = verdict starts otherwise)
{'U': 62, 'K': 49, 'T': 32, 'mixed': 1}
The hand counts below were estimates; use this line.
- KEEP: 35
- BACKED-BY-TEST: 36 (includes T/K mixed and T-for-part rows counted as T)
- UNBACKED: 44 (most are "author run, log not in repo" for n8n/HubSpot/Semgrep results)
- of the UNBACKED: FALSE 1, STALE or inconsistent 4.

## Top 10 UNBACKED / FALSE / STALE
1. docs/why-this-code.md:24 "Under 100 lines, no business logic" -> FALSE: tools/scrub_n8n_export.py is 202 lines.
2. docs/why-this-code.md:28 / real-services row "a test fails if one is missed" -> only constants, CRM_FIELDS_SENT and real_services are tested (tests/test_mode_safety.py::test_every_kind_is_listed_in_the_places_that_describe_it); loader.py branch, module existence and "must not import from demo_only" have no test.
3. .github/workflows/lint.yml:3 "no repository secrets exist" -> STALE: sonar.yml:61 uses secrets.SONAR_TOKEN.
4. .github/workflows/semgrep.yml:54-55 run 43403502735 "Ran 77 rules on 47 files: 0 findings" -> result from a CI run, log not in the repo (docs/tests.md:36 repeats the text only).
5. docs/n8n-recipe.md:54,70,77,78,79 retry/restart timings ("second try ... about one second", "within about 2 seconds", 3 tries each on 400/413, 1 lead 1 CRM row 1 email) -> author runs, no log.
6. docs/hubspot-probe.md:4 three runs, "6 or 7 of the 8 calls", 403 MISSING_SCOPES, 204 on delete -> author runs, no log (the only real-service result of the repo).
7. docs/n8n-recipe.md:46,76 "the caller always gets 200 ... a 400/413 gives 500" and "Retry On Fail cannot skip retries for 4xx" -> absolute n8n behaviour claims, no log or source.
8. .github/workflows/semgrep.yml:49-51 "copying the rules ... is not allowed by their licence" while line 3 says the licence text was not read -> asserted prohibition on an unread text.
9. docs/real-services.md "nobody outside your own inboxes receives anything", "Failure tables print no address", "CRM key sent only to the vendor's own API host names", "no body or address is read" -> guarantees, no test found (only code comments).
10. .github/workflows/sonar.yml:30 vs lint.yml:19 "1.6 times" vs "about twice" the longest run; semgrep.yml:26 "install took 17 s" with no log; gitleaks checksum provenance (lint.yml:22-24) not verifiable.

## What I did not cover / limits
- Ran no tests (all backing found by reading). Test names in "T" rows are from reading assertions of the ones I opened; I did not open every test in tests/test_desk*.py, test_crm_hubspot.py, test_real_check_dry.py.
- desk-webhook.json compared only by node names/path, not diffed field by field with desk-form.json.
- Did not verify HubSpot or n8n external documentation claims, pinned action SHAs against GitHub, gitleaks checksum, or the Semgrep rule/licence statements (no network, by rule).
- Cross-references (docs/limits.md "Which CRM stage...", contract.md rows) checked for existence only.
- real-services.md: line numbers are by paragraph (long lines), not exact.
