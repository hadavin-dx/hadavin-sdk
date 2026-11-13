# Review map for PR #4 (branch pr-3-tests 2db3926 into pr-2-demo-folder f31e261)

Repo: hadavin-dx/duplicate-proof-lead-desk-n8n. Read-only work: a clone in /tmp/work/rm-base, only git and grep, no tests run, nothing pushed or commented.
Evidence file: list-rows.tsv (one row per changed file: lines added, lines removed, group, risk, read-first rank, new or modified).
Preamble rules used: R-numbers not looked up (bible folder not available to me); rules applied from BRIEF-PREAMBLE items 3, 6, 11, 14.

Labels: **[read]** = I read it in the diff. **[inferred]** = my reasoning, not shown by the diff. **[not checked]** = I did not look.

## 0. Headline numbers [read, git diff --numstat]

142 files changed. 93 are new test files under tests/ (33,254 lines added, 0 removed; all 93 are new, none modified). The other 49 files are modified, none are new or deleted. Outside tests/: 1,116 lines added, 164 removed (sum of the group rows in list-rows.tsv). Of those, 371 added lines are generated lock and input files (G4); so the non-test, non-lock change is about 745 added and 164 removed.

Honest warning: everything below describes the change as read in the diff. I did NOT run the code or the tests, so "behaviour change" means what the diff text shows, not a measured result.

## 1. Read-first order for a reviewer with 30 minutes

| Rank | Group | Minutes | Why first |
|---|---|---|---|
| 1 | G1 src Python (9 files, 108 lines changed) | 8 | The only runtime code of the product; two real behaviour changes (memory book refusal, CRM copy ordering). |
| 2 | G2 hardening: scripts/n8n_api.py, scripts/http_guard.py, tools/scrub_n8n_export.py (3 files, 333 lines) | 8 | Handles an API key and scrubs a public export; security-relevant. |
| 3 | G3 allowlists: .gitleaks.toml, exceptions.txt, .codeant/configuration.json (3 files, 26 lines) | 4 | Each line weakens a scanner a little; small but worth every second. |
| 4 | G4 locks (5 files) | 4 | Check names and pins only; do not read hashes. |
| 5 | G5 workflow sonar.yml (1 file, 28 lines) | 3 | CI that now runs repository tests in the job that holds a secret. |
| 6 | G7 + G8 smaller scripts, n8n/proof.json, demo_only | 2 | Low risk; skim. |
| 7 | G6 portal CSS/JS (7 files, 59 lines) | 1 | Display only. |
| 8 | G9, G10 docs and config | skim | No runtime effect. |
| 9 | G11 tests (93 files): spot-check only | rest | Too large to read; see section 4 for where to dip in. |

Exact commands (run inside a clone with both branches fetched; the base is `origin/pr-2-demo-folder`, the head `origin/pr-3-tests`):

- G1: `git diff origin/pr-2-demo-folder origin/pr-3-tests -- 'src/lead_desk/*.py'`
- G2: `git diff origin/pr-2-demo-folder origin/pr-3-tests -- scripts/http_guard.py scripts/n8n_api.py tools/scrub_n8n_export.py`
- G3: `git diff origin/pr-2-demo-folder origin/pr-3-tests -- .gitleaks.toml exceptions.txt .codeant/configuration.json`
- G4: `git diff origin/pr-2-demo-folder origin/pr-3-tests -- requirements-browser.in requirements-coverage.in` and `git diff --stat origin/pr-2-demo-folder origin/pr-3-tests -- 'requirements-*'`
- G5: `git diff origin/pr-2-demo-folder origin/pr-3-tests -- .github/workflows/sonar.yml sonar-project.properties pyproject.toml .gitignore`
- G6: `git diff origin/pr-2-demo-folder origin/pr-3-tests -- src/lead_desk/portal`
- G7: `git diff origin/pr-2-demo-folder origin/pr-3-tests -- scripts/reset.ps1 load_tools n8n/proof.json`
- G8: `git diff origin/pr-2-demo-folder origin/pr-3-tests -- demo_only`
- G9: `git diff origin/pr-2-demo-folder origin/pr-3-tests -- contract.md docs versions.md`
- G11: `git diff --stat origin/pr-2-demo-folder origin/pr-3-tests -- tests`

## 2. The groups

### G1. Core src Python: 9 files, +86 / -22 [read]

Question for each file: does the change alter what the program does at run time, or only how the code is written?

| File | Function(s) changed (from hunk text; hunk headers only name the class, so method names were found by reading the file at the head) | Runtime behaviour? | What it does |
|---|---|---|---|
| src/lead_desk/desk.py (+47/-4) | new module function `book_problem`; `Desk.__init__`; `Desk._mirror_pass`; new constant `MEMORY_BOOK_PROBLEM`; new attribute `_mirror_busy` | YES (two changes) | (a) The desk now refuses a lead-book path of `:memory:` (a private memory database is empty for every thread but the first). Before, `__init__` kept `""` and `:memory:` as given; now it always resolves the path to an absolute path [read]. For the path `""`, the old code kept it as `""`; the new code resolves it, which gives the current folder [inferred: `Path("")` is "."; the code comment says the same]. (b) In the copy-to-CRM step the call is now always run exclusive, uses `functools.partial` instead of a lambda, and when the same lead's older call is still running the lead waits (10, 60, 180, 420 second steps from `MIRROR_RETRY_WAIT_SECONDS`) instead of ending the pass; the refusal count is kept in memory only. |
| src/lead_desk/server.py (+18/-2) | `_Handler.send_error`; `_Handler._step`; `make_server`; `main` (code plus docstring); import lines | YES | `send_error` and the `_step` too-large path now flush, half-close and read the unread request body before closing, so the client sees the answer instead of a reset. `make_server` hands the real address to a demo extension when the extension has `set_bound_address`. `main` refuses a `:memory:` book (exit 4) before the folder and lock steps. |
| src/lead_desk/loader.py (+10/-1) | new `KnowsBoundAddress` protocol class; import line | Structure only on its own | Adds an optional protocol so `make_server` can test `isinstance`. No behaviour until `make_server` uses it (it does, see server.py). |
| src/lead_desk/config.py (+2/-2) | `read_approvers`; `_read_leadflow` | Structure only [inferred] | `except (UnicodeError, ValueError, RecursionError)` becomes `except (ValueError, RecursionError)`. The comment says UnicodeError is a ValueError; that is a Python fact [inferred from my knowledge, not run], so the same exceptions are caught. |
| src/lead_desk/crm_hubspot.py (+1/-3) | `HubspotCrm._request` | Structure only [inferred] | Removes `except CrmError: raise`; the next handler lists only OSError, ValueError, HTTPException, and the comment says a CrmError is none of these. Same pass-through [inferred]. |
| src/lead_desk/live_claude.py (+2/-4) | `SpendLedger._totals`; `LiveQualifier._post_once`; unused `import socket` removed | Structure only [inferred] | Drops `except LiveCapReached: raise` (it is not one of the later listed kinds) and drops `URLError` and `socket.timeout` from a tuple that still holds OSError (both are OSError subclasses, per the comment). Security note: this file is the spend-cap ledger, so confirm the claim "LiveCapReached is not an OSError/ValueError" in the class definition [not checked by me]. |
| src/lead_desk/smtp_outbox.py (+2/-2) | `SmtpOutbox.send`; the QUIT helper near line 292 (nearest def: `_dialogue`) | Structure only [inferred] | Drops `UnicodeError` and `TimeoutError` from tuples that already hold ValueError and OSError. |
| src/lead_desk/smtp_provider.py (+2/-2) | `SmtpProviderOutbox.send`; the QUIT helper near line 313 (nearest def: `_dialogue`) | Structure only [inferred] | Same as smtp_outbox. |
| src/lead_desk/portal_api.py (+2/-2) | `_lead_detail` | Structure only | Unused tuple names renamed to underscore names. |

Reviewer focus inside G1: desk.py `_mirror_pass` (the new waiting logic and the `exclusive=True` flag) and `book_problem`; server.py `send_error` and `_step` (new body-draining calls: check they cannot block on a slow client; [not checked]). Pair with tests/test_codeant_desk.py, which names these cases [read the test names only].

Risk: BEHAVIOUR (desk.py, server.py), none for the other seven [inferred]. Not security, except live_claude.py is the spend ledger (handler change only).

Command: `git diff origin/pr-2-demo-folder origin/pr-3-tests -- 'src/lead_desk/*.py'`

### G2. Security hardening: scripts/n8n_api.py, scripts/http_guard.py, tools/scrub_n8n_export.py: 3 files, +296 / -37 [read]

- **scripts/http_guard.py (+20/-2).** `open_http` gets two new options. `follow_redirects=False` refuses to follow a 3xx (urllib would resend request headers, an API key included). `use_proxy=False` ignores HTTP_PROXY and similar and goes straight. Both options default to the old behaviour (follow, use proxy), so callers that do not pass them are unchanged [read]. The scheme check (http and https only) is untouched.
- **scripts/n8n_api.py (+162/-26).** The biggest hardening. Read in the diff: `N8N_URL` must be https, or http to a loopback host (127.0.0.1, ::1, localhost) and is checked at import time, before the key file is opened (`checked_base`, using a strict netloc regex, a ban on `@` and on blank or non-printable characters, and a port range 1..65535). The key file is read with a size cap (4096), must be one printable ASCII word, and a bad key file gives a fixed message that does not show the file text. Every call uses `follow_redirects=False`, and `use_proxy` only when the address is https. Error output carries only exception type names, never the address, key or response body. Non-200 answers keep no body. Output goes through `say()` which replaces unencodable characters. `main` now prints usage and returns 2 on a bad command. The module still runs `checked_base(...)` and `_read_key()` at import time, so importing it with bad environment raises SystemExit [read]. Risk: SECURITY (positive, narrows what can happen to the key). Reviewer checks: the regex `NETLOC`, and whether loopback-http plus no-proxy is the intended rule (it is stated in the docstring).
- **tools/scrub_n8n_export.py (+114/-9).** The public-export scrubber. Read in the diff: the URL pattern now matches any scheme, not only http and https, and JSON-escaped slashes; `data:` and `javascript:` links are replaced; e-mail matching is Unicode-aware and includes the full-width at-sign; a localhost address is kept only up to the end of its path (query and fragment dropped); look-alike localhost addresses with a tab, CR, LF or a space-then-at-sign are replaced whole; node names are cleaned and the `connections` part is rewritten with the cleaned names (duplicates get " (2)"). The docstring lists what is NOT cleaned (for example an address with no scheme, a secret in a kept localhost path, `data:` with no media type). Risk: SECURITY (positive; but the docstring itself admits gaps, so the claim "safe for a public repo" is not made by the diff). Reviewer: read the "NOT cleaned" list and decide if it is acceptable.

Command: `git diff origin/pr-2-demo-folder origin/pr-3-tests -- scripts/http_guard.py scripts/n8n_api.py tools/scrub_n8n_export.py`

### G3. Allowlist and security config: 3 files, +21 / -5 [read]

| File | What it allows | How narrowly |
|---|---|---|
| .gitleaks.toml (+14/-4) | (1) The text `requirements-browser.in` (its name ends like a host name) via an anchored regex `^requirements-browser\.in[^A-Za-z0-9_-]?$`. (2) `requirements-coverage.in` joins the existing `requirements-(dev\|coverage)\.in` entry. (3) A 64-hex SHA-256 line in `requirements-browser.txt` and `requirements-browser-win.txt`: the entry uses `condition = "AND"` and `paths = ^requirements-browser(-win)?\.txt$`. (4) The existing 40 or 64 hex allowance now anchors its paths with `^` and adds `requirements-coverage.txt`. (5) The sonar project key rule changes from "any `hadavin-dx_` key" to exactly `hadavin-dx_duplicate-proof-lead-desk-n8n`, using `regexTarget = "match"`. | Narrow: whole-line anchors, and (5) is narrower than before. One loose point to question: the paths in (3) are root-anchored, but versions.md says the existing test scan passes absolute paths, so a planted hash in `docs/requirements-browser.txt` may not be reported [read in versions.md; the real behaviour not checked by me]. |
| exceptions.txt (+5/-1) | Regex lines for hash lines in `requirements-coverage.txt` and `requirements-browser(-win).txt`; the file names `requirements-coverage.in` and `requirements-browser.in`; the sonar project key is now exact (also allowed inside `.gitleaks.toml`, written as `[d]uplicate` so the line does not match itself). | Narrow; each is anchored (`^` and `$`). The `^[^:]+:[0-9]+:requirements-...\.in...` lines allow the file name text in ANY file, not only the lock input [read]; low risk because it is a file name. |
| .codeant/configuration.json (+2/0) | Adds the two browser lock files to the list of files the CodeAnt review bot skips. | Effect (stated in versions.md, read): the bot's dependency vulnerability check no longer reads these two lock files; it still reads `requirements-browser.in`. |

Risk: SECURITY (weakens scanners slightly, narrowly). Command: `git diff origin/pr-2-demo-folder origin/pr-3-tests -- .gitleaks.toml exceptions.txt .codeant/configuration.json`

### G4. Dependency locks: 5 files, +371 / -0 [read]

| File | Packages and pins | Hash lines |
|---|---|---|
| requirements-browser.in | `playwright==1.63.0` | none |
| requirements-browser.txt (Linux, Python 3.12) | greenlet 3.5.6, playwright 1.63.0, pyee 13.0.1, typing-extensions 4.16.0 | 91 |
| requirements-browser-win.txt (Windows, Python 3.13) | the same four pins | 91 |
| requirements-coverage.in | `pytest-cov` (unpinned in the .in, resolved in the lock) | none |
| requirements-coverage.txt | coverage 7.17.2, iniconfig 2.3.1, packaging 26.3, pluggy 1.7.0, pygments 2.21.0, pytest 9.2.0, pytest-cov 7.1.0 | 131 |

Newly added packages (not in requirements-dev.txt): playwright, greenlet, pyee (browser lock); coverage, pytest-cov (coverage lock). Shared with the dev lock and pinned the same: typing-extensions 4.16.0, iniconfig, packaging, pluggy, pygments, pytest 9.2.0 [read: I compared pin lists]. requirements-dev.txt, requirements-dev-win.txt and requirements-dev.in are not changed [read: same pin list on both branches, and git diff --stat empty for them]. Both new locks were made with `-c requirements-dev.txt`, so existing pins should not move [read in the file headers and versions.md; not re-run].

Reviewer checks: (a) these are the only new third-party packages; Playwright ships a bundled Node driver whose notices versions.md says were not examined; (b) the sonar workflow installs the coverage lock with `--only-binary=:all:` and `--require-hashes` (see G5). I did NOT verify any hash against the package index [not checked].

Generated or bulk: all 3 `.txt` locks are generated by `uv` (headers say so). Hash lines are 64-hex, why G3 needs allowlist entries.

Command: `git diff origin/pr-2-demo-folder origin/pr-3-tests -- requirements-browser.in requirements-coverage.in` then `git diff --stat ... -- 'requirements-*'`

### G5. Workflow, sonar.yml: 1 file (+ sonar-project.properties, pyproject.toml, .gitignore in G10) [read]

`.github/workflows/sonar.yml` (+24/-4): runner changes from `ubuntu-latest` to `ubuntu-24.04`; timeout 20 to 60 minutes; adds setup-python (pinned by commit SHA, v7.1.0 per comment), one `pip install --require-hashes --only-binary=:all:` of the dev and coverage locks, and a test step `pytest --cov` with `DPLD_REQUIRE_DEMO=1`, so repository test code now runs in the same job as the scan. The file's own comment states the risk plainly: SONAR_TOKEN is only on the scan step, but all steps share one runner, so test code could tamper with `$GITHUB_ENV`, the cache or `coverage.xml`; it argues forks and Dependabot do not run the job and a same-repo author can already edit the workflow, and calls a two-job split an open owner decision [read]. Risk: SECURITY (CI, accepted risk written in the file). Reviewer: decide whether you accept it or want the two-job split. Command: `git diff origin/pr-2-demo-folder origin/pr-3-tests -- .github/workflows/sonar.yml sonar-project.properties pyproject.toml .gitignore`

### G6. CSS and JS portal: 7 files, +41 / -18 (4 CSS, 3 JS) [read]

Risk: NONE for security, display and front-end behaviour only.
- app.css (+13/-8): `.tab` nowrap; `.table-wrap` position relative; drawer head wraps long titles; `overflow-wrap: anywhere` for dialog, toast; media queries rewritten with range syntax (`width > 860px`) so there is no gap at 860.5 px.
- pages/leads.css (+5): company column ellipsis above 1200 px; phone rules for the search box.
- pages/needs.css (+6/-2): long text wraps; tabs scroll sideways on phones.
- pages/overview.css (+3): phone grid for tiles.
- pages/log.js (+8/-2): `openRun` moved out of a loop; when older rows are loaded, a refresh keeps rows from page one that new requests pushed out, and the cursor is only replaced when nothing is loading. This is the one JS change that alters behaviour (log paging) [read].
- pages/overview.js (+2/-2): a `forEach` closure replaced by a plain loop (same sums) [read; not run].
- portal.js (+4/-4): `var` declarations moved above their first use; `Portal.demo` becomes `window.Portal.demo`. Structure [inferred: the comments say "declared before the functions that read them"].

Command: `git diff origin/pr-2-demo-folder origin/pr-3-tests -- src/lead_desk/portal`

### G7. Other scripts and tools: 4 files, +6 / -7 [read]
- scripts/reset.ps1: the data-folder check now uses real paths (`os.path.realpath`) so a junction or symlink pointing elsewhere is followed; refuses unless inside `data`. Risk: BEHAVIOUR of a delete script (safer; it guards file deletion). Worth 2 minutes. The PowerShell part uses an inline `python -c` with the path as an argument, not string-built [read].
- n8n/proof.json: the PASS expression now also requires exactly one status `new` and nine `duplicate` from the node "Wait for the desk to finish", in addition to the old outbox and CRM counts. Behaviour of a demo workflow; tests/test_n8n_proof_result.py runs the expression in node [read in its docstring].
- load_tools/catcher.py: drops `TimeoutError` from a tuple (it is an OSError). load_tools/load_driver.py: `for j` becomes `for _`. Structure only.

### G8. demo_only: 7 files, +169 / -56 [read]
Made-up stand-in servers, not the product. fake_hubspot.py (+114/-34): every access to `contacts` now goes through locked methods that return copies (`public`, `contacts_page`, `search`, `patch`, `take_failure`, `take_hang`), the request body is read before replying, and a bad Content-Length gives 400. fake_model_server.py (+30/-12): control call checks the whole body first, rejects non-string modes and non-finite or over-86,400-second times; the "mixed" cycle now starts at hot. fake_imap.py and fake_smtp_tls.py: drop `ssl.SSLError` from tuples (an OSError subclass, [inferred]). portal_demo.py: URL building split into `_url_for(bind, port)` and an optional `set_bound_address` [read hunk headers; body of this hunk not fully read]. portal_demo.js and .css: a "without an answer" counter and a phone wrap. Risk: NONE for the product; it is excluded from Sonar (`sonar.exclusions`).

### G9. Docs: 7 files, +85 / -15 [read for contract.md and versions.md; others skimmed]
contract.md, versions.md (browser lock section, licence table, the CodeAnt side effect and the "interim" secret-scan state), docs/limits.md, n8n-recipe.md, portal.md, settings.md, tests.md (+48: quality-check instructions and the secret-scan measurements). Risk: NONE. Reading tip: contract.md and versions.md are the only ones that state rules which G3 and G4 depend on. docs/tests.md contains a note that a count of 2329 passed and 135 skipped from the owner's machine has "no known cause" [read in the diff text, partly truncated].

### G10. Build and test config: 3 files, +17 / 0 [read]
pyproject.toml: `faulthandler_timeout = 300` (stack dump after 5 minutes, run not stopped) and a `[tool.coverage.run]` block. sonar-project.properties: coverage report path. .gitignore: `.coverage.*` and `coverage.xml`. Risk: none.

### G11. Tests: 93 new files, +33,254 / 0 [read: names and numstat; I read only the first lines and test names of a sample]
By theme (my grouping by file name; approximate [inferred]):

| Theme | Files | Lines | Biggest files |
|---|---|---|---|
| Desk core (flow, HTTP, env, claim, crash, ledger, mode, review) | 29 | 9,969 | test_desk_http_edge_cases.py 1,551; test_desk_edge_cases.py 949; test_env_numbers.py 841; support.py 604 |
| Portal API and page logic | 6 | 5,276 | test_portal_api.py 1,800; test_portal_demo.py 1,210; test_portal_mode.py 726 |
| Adapters and stand-in servers (HubSpot, SMTP, Claude, reminders) | 12 | 5,286 | test_smtp_provider.py 669; test_live_claude.py 708; test_crm_hubspot.py 580 |
| Scripts, tools, hygiene (n8n, scrub, reset, load tools, secret scan) | 13 | 4,456 | test_load_tools.py 1,039; test_real_check_dry.py 834; test_n8n_api_url.py 717; test_scrub_n8n_export.py 475; test_hygiene.py 480 |
| Timing, hang, stall | 9 | 3,835 | test_slow_sender.py 948; test_hung_adapter_calls.py 884 |
| Real-browser portal tests (Playwright; skipped when not installed) | 15 | 2,223 | test_portal_browser.py 314; test_stage_confirm_browser.py 252; plus 7 `*_probe.js` helper files |
| Mutation-style guards | 4 | 1,394 | test_mutants_more.py 508; test_mutation_guards.py 386; test_mutants.py 284 |
| Review-finding regression tests (names start `test_codeant_`) | 4 | 790 | test_codeant_fakes.py 410 |

Dip in here, in this order: (1) tests/test_codeant_desk.py (222 lines; covers the two desk.py behaviour changes); (2) tests/test_n8n_api_url.py and tests/test_http_guard.py (cover G2); (3) tests/test_scrub_n8n_export.py; (4) tests/test_gitleaks_exceptions.py and tests/test_hygiene.py (cover G3); (5) tests/test_except_clause_hierarchy.py (pins the exact `except` clauses that G1 tidied; it reads source with `ast`, per its docstring).

Bulk files: test_portal_api.py (1,800), test_desk_http_edge_cases.py (1,551), test_portal_demo.py (1,210), test_load_tools.py (1,039) are large and best sampled, not read whole. No test file is a generated snapshot; I found no snapshot or fixture-dump file in the list [read the file list; tests/portal_fixtures is referenced by sonar.exclusions but not in this diff; I did not look in it].

Names that do not match content (checked 16 files by test names and docstring): none clearly wrong. Mild mismatches [inferred]: the four `test_codeant_*` files are named after the review tool that found the issues, not the subject (subjects: fake HubSpot locking, memory book and CRM ordering, demo-extension port, workflow triggers); `test_infra.py` is a catch-all (adapters, database factory, demo wiring); `test_mutants.py`, `test_mutants_more.py` and `test_mutation_guards.py` overlap in purpose and could confuse a reader about which holds which guard; `test_portal_long_values.py` and `test_portal_drawer_long_name.py` are close in topic.

## 3. Security-relevant items, in one list [read unless marked]

1. n8n_api.py: URL allow-rule, no redirects, no proxy for http, key file validation, no key or body in errors (G2).
2. http_guard.py: opt-in no-redirect and no-proxy (G2); defaults unchanged.
3. scrub_n8n_export.py: wider scrub; its own docstring lists what stays uncleaned (G2).
4. Gitleaks and exceptions allowlists: all anchored; one acknowledged gap (versions.md: the hash allowance for `requirements-browser*.txt` is path-loose today) (G3).
5. CodeAnt skips the browser locks, so playwright's transitive pins are not vulnerability-checked by that bot (G3, stated in versions.md).
6. sonar.yml runs repo test code in the job that has the Sonar token on a later step (G5, stated in the file).
7. reset.ps1: realpath containment before a delete (G7).
8. desk.py/server.py: memory-book refusal and body draining are robustness changes, not auth changes [inferred].
9. Not found in the diff: any change to authentication, approvals or secrets handling in src/ [inferred from reading all src Python hunks].

## 4. What I did not check

- I ran no tests, no linter, no gitleaks; every "behaviour" statement is from reading hunks, and "inferred" ones rest on Python semantics I did not execute.
- I did not read the full body of any of the 93 test files, only names, docstrings and sizes; I did not verify that tests fail on the old code.
- I did not verify lock hashes or look up the packages' advisories or licences.
- I did not read docs/limits.md, docs/n8n-recipe.md, docs/portal.md, docs/settings.md hunks in detail, nor the whole portal_demo.py hunk bodies.
- I did not confirm whether `LiveCapReached` is a subclass of the exceptions in the shortened tuples (live_claude.py), nor `CrmError` in crm_hubspot.py.
- Time: the whole map took one pass; line counts come from `git diff --numstat`.
