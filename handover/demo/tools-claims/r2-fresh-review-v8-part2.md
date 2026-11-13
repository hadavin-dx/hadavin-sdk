# Fresh review r2: fact check of the uncommitted text edits (tree /tmp/v8work)

Studio folder (`<studio>`, bible, handoff, memory) does not exist in this container, so no R-numbers were looked up or cited.
No lint, no pytest, no network, no agents, no file changes. Checked by reading the code, tests, scripts, workflows, lock files and JSON files in the same tree.
Not checked (cannot be, under the brief): every test count and timing that comes from a run (2449, 2462, 2513, 3683, 3883, 16 min 33 s, about 20 min, 56 failures with `--basetemp`, Chromium build 1243, Node versions, Semgrep run 43403502735); the SQLite 3.49.1 and 3.46.1 versions; the n8n run results (all from the author's own runs, no log). The "3883 tests collected" figure was not re-collected (92 test files exist, which matches the 92 lines; `tests/test_workflow_run_flags.py` has 4 test functions, two parametrized, which fits 10 only if WORKFLOWS has 4 files: not opened further).

Result: no Blocker. 3 Major, 6 Minor. Everything else I opened matched.

## Blockers and Majors

| file:line | changed sentence (short) | what I checked | verdict |
|---|---|---|---|
| docs/tests.md:98 | "nine of them are simulated by an exception ... and only D2 is a real process kill" | Contradicts the same file at :115 ("The stops are simulated inside the program for all ten points ... A real process kill ... was done only at D2"), README.md:99 ("All ten were simulated by an exception ... and D2 was also tried with a real process kill") and `docs/limits.md:63`. Code: `tests/test_flow.py` `test_crash_resume_each_point` (A, A2, B, D1, D2) plus `test_crash_resume_after_label_crm_send_mark_and_result` (L, C0, C1, D1b, D3) raise `SimulatedCrash` for all ten; `tests/test_http.py::test_crash_d2_subprocess` is the real kill at D2 only. So D2 is simulated and also killed; the "nine / only D2" wording says D2 is not simulated. | FIX. Replace with: "The desk was stopped on purpose at each of ten crash points and restarted; all ten are simulated by an exception raised inside the program, and D2 was also tried with a real process kill (`docs/limits.md`)." |
| docs/tests.md:131 (P10) | "its placeholder says names and addresses are searchable after hiding is turned off" | `src/lead_desk/portal/pages/leads.js:289` placeholder is "Company or lead number"; `:324` sets it to "Company or lead number" while masked and "Name, email, company or request number" when not masked. The sentence "Names and addresses are searchable after you turn off hiding" is a separate hint line (`searchHint`, class `search-hint`, `leads.js:297`), not the placeholder. | FIX. Replace "and its placeholder says names and addresses are searchable after hiding is turned off" with "and a hint line next to the search box says names and addresses are searchable after hiding is turned off (the placeholder reads \"Company or lead number\" while masked)". |
| docs/n8n-recipe.md:71 | "The author reports the same when the ten calls go through the n8n web address of the web form source." | `n8n/proof.json` node "Send all ten at the same moment" already posts to `http://127.0.0.1:5679/webhook/desk-form`, which is the n8n web address of the web form source; the same file's :28 says so. The sentence presents it as a second variant, which the shipped workflow does not have. | FIX. Delete the sentence, or replace with: "In the shipped `proof` workflow the ten calls already go through the n8n web address of the web form source (`/webhook/desk-form`), not straight to the desk." |

## Minor

| file:line | changed sentence (short) | what I checked | verdict |
|---|---|---|---|
| README.md:118 | "Off when the setting is unset or is the word `off`." | `src/lead_desk/config.py:599-601`: `flow = e.get("DESK_LEADFLOW_FILE","").strip(); if flow and flow != LEADFLOW_OFF` so an empty value is also off; `docs/settings.md:16` says "Unset, empty or the exact l..."; `scripts/start_all.sh:6-8` also treats empty as off. Same fact said two ways. | FIX. "Off when the setting is unset, empty or is the word `off`." |
| README.md:90 | reset exit 3: "or (Linux) `ps` is not installed" | `scripts/reset.sh` exits 3 for a missing `ps` only when `data/desk.pid` or `data/fakes.pid` exists. | FIX. "(Linux) `ps` is not installed while a pid file exists". |
| docs/real-services.md:18 | "Exit code 0 only when every check in its table passes" | `scripts/run_real_check.py:1109` returns `0 if result["ok"] and not left else EXIT_FAILED`: with `--cleanup`, a contact that could not be archived also gives a non-zero exit. Text promises nothing false, but omits that case. | FIX. Append: "With `--cleanup`, a contact that could not be archived also makes the exit code non-zero." |
| versions.md:47 | "`mypy --platform linux` and `mypy --platform win32` (strict, `src/` and `tools/`; ...)" | `pyproject.toml:46`: `files = ["src", "tools", "scripts/hubspot_probe.py"]`. | FIX. "(strict, `src/`, `tools/` and `scripts/hubspot_probe.py`; ...)". |
| docs/why-this-code.md:14 | "rules listed in `docs/limits.md` under \"Rules of the desk's records\"" | `docs/limits.md` has no heading of that name; the text is a paragraph at :89 inside the section "Counters and database rules" (:85). | FIX. "listed in `docs/limits.md`, section \"Counters and database rules\" (paragraph \"Rules of the desk's records\")". |
| docs/tests.md:131 (P10) | "`mask` function ... which masks only the fields email, phone, message and name" | `portal.js:267-272` also handles `email_key` (masked like email). | FIX. "fields email (and email_key), phone, message and name". |

## OK (changed sentences that state facts and matched)

| file:line | what I checked | verdict |
|---|---|---|
| README.md:8-10 | labels hot/warm/cold from `demo_only/replies.json`, `fakes.py` LABELS, default "warm"; `/counts` and replay in `tests/test_flow.py` | OK |
| README.md:20-22, 65, 82, 88 | `demo_only/leadflow.json` `nudge_after_seconds` 90, `scripts/start_all.sh:16-17` turns the file on; `/fake/outbox` count includes reminders (`fakes_server.py:85-88`); `feed.py` request ids | OK |
| README.md:28-36 | `identity.normalise_email` strip + lower; `_valid_email` refuses control chars, Kelvin sign etc.; verdicts new/duplicate/review | OK |
| README.md:39-44 | ten crash points A, A2, B, L, C0, C1, D1, D1b, D2, D3 plus N1 (`hooks.py`, `desk.py`); reaper `gate.py:51-53` `SEND_MAX_ATTEMPTS=5`, `SEND_BACKOFF_SECONDS=(1,2,4,8)` | OK |
| README.md:47, 68, 90 | ports 8765/8766 (`config.py:424-427`); both shell scripts refuse non-bash with exit 2 and "run this script with bash"; reset exit codes 2, 3, 4, 5, 6 and the 0-999 no-leading-zero rule match `reset.sh`, `reset.ps1`, `reset_check.py`; empty value means 10 | OK (see Minor for `ps`) |
| README.md:88 | `tests/test_http.py:154-158` (`/nope` 404), `tests/test_server_hardening.py:111-114`; no `/health` test | OK |
| README.md:99-100, 104-109 | `test_crash_d2_subprocess` (keyed, blind), `contract.md:99`; bind rule `config.py:465-476`; `docs/limits.md` items 5, 7, 9 | OK |
| README.md:117-120 | `DESK_LATER_MODE`, `LATER_MODES`, `_claim_nudge` does not read follow-up state; `crm_hubspot.set_fields` sends only `hs_lead_status` and, if set, `hubspot_owner_id`; `tests/test_lead_crm_copy.py:127-166` asserts the two-property body | OK |
| README.md:126, 130 | `docs/n8n-recipe.md` four patterns; lock file names and Python pairings; 16 min 33 s equals 993 s in `docs/tests.md:79` | OK |
| SECURITY.md | `hubspot_probe.py` reads token from `--token-env`; `N8N_API_KEY_FILE`; `DESK_FAKES_URL` and `DESK_SMTP_HOST` loopback-only (`config.py:519`, `smtp_outbox.py:85-89`); `public_bind_problem`; lint.yml gitleaks on `dir` and `git` | OK |
| versions.md | `LIVE_API_VERSION = "2026-10-21"` (`constants.py:172`); ruff 0.17.4, rule groups `E,F,W,I,S,PLR2004`; bandit command identical to `lint.yml:67`; action versions and SHAs in the workflows; 19 and 18 pinned lines in the two dev locks (counted); colorama only in the Windows lock; `playwright==1.63.0` and the browser lock headers/commands match; `--exclude-newer 2026-11-12`; coverage lock says uv 0.11.32; `ON CONFLICT ... DO UPDATE` at `desk.py:1363`; no `sqlite_version` check in `src`; `.codeant/configuration.json` lists the two browser locks; `.gitleaks.toml:97` path regex; 2449+15, 2462+2=2464, 2462+3=2465, 3683+200=3883, 166+30+4=200 add up | OK |
| docs/tests.md:19-30 | `sonar.yml:46,51` one pip call and `--cov`; `pyproject.toml [tool.coverage.run]`; `sonar-project.properties:14`; `crash_desk.py` flag file and `FlagFileHooks`; `--outbox keyed\|blind` | OK |
| docs/tests.md:30-52 | lint.yml step list; `test_workflows_are_pinned_and_limited` (`test_hygiene.py:509`); `.github/dependabot.yml` Actions only; semgrep.yml: five steps, `ubuntu-24.04`, 20 min, 3 tries, `RETRY_PAUSE_SECONDS=20`, `--metrics=off --disable-version-check --strict --error --severity ERROR`, five folders, `pip check`; `test_nosemgrep_form.py:270-334`; `requirements-semgrep.in` uv 0.13.8, quarterly note; sum 114-92=22=1+2+19; 113=22+28+60+3; 166 breakdown | OK |
| docs/tests.md:98-115 (table) | C0/C1/D1b/D2 cells equal `EXPECT_MORE` and `EXPECT` in `tests/test_flow.py:287-360` (including `crm_unconfirmed`, `crash_while_sending`) | OK |
| docs/tests.md:135-139 | `_COUNTS_SQL` (`received = new + duplicate + review + open`); `_rejected` is in memory; `schema.sql` triggers (receipts, leads, sent follow-ups); `test_mutants.py` symptoms "leads == 1"/"got 2" and "emails == 1"/"got 2"; seven checks in `load_tools/README.md` | OK |
| docs/tests.md:83 | four on-purpose skips found: `test_stall_eviction.py:526` (Windows only), `test_path_confinement.py:284` (Python 3.13), `test_server_hardening.py:224` (`LEAD_DESK_LOAD_N`), `test_n8n_api_url.py:510` (root) | OK |
| docs/why-this-code.md:28-38 | `CRM_CHOICES`, `OUTBOX_CHOICES`, `QUALIFIER_CHOICES`, `OUTBOX_STAND_INS`, `CRM_FIELDS_SENT`, `Config.real_services`, `contract.py` Crm/Outbox/Qualifier protocols; `test_no_demo_only_outside_loader` suffix list `.py .sql .md .txt .toml`; `test_mode_safety.py:510-518` set comparison; `tools/scrub_n8n_export.py` 205 lines; seven checks | OK |
| docs/n8n-recipe.md | three nodes and field mapping in `n8n/desk-form.json`; timeout 15000, `retryOnFail` true, 3 tries, 1000 ms; desk default send timeout 5.0 (`config.py:429`); workflow names, paths `desk-form`, `proof-run`, node ids `node-1...`; node types used = Webhook, Edit Fields, HTTP Request, Code, Manual Trigger; `fakes_server.py --crm/--outbox`; ten-request proof workflow wait 4000 ms and result rule | OK (see Major) |
| docs/hubspot-probe.md | `CALL_BUDGET=8`, planned 7, `DELETE_RESERVE`, `dpld_tag`, `OPEN`, owners `limit=10` and last 4 characters, `gdpr-delete` then archive; `tests/test_hubspot_probe.py:120,219` | OK |
| docs/real-services.md | `DEFAULT_PERSONS=12`, `EMAIL_DOMAIN example.com`, `y/N` prompt, `--cleanup`, `--live-model`, `X-Send-Key` header only with PEEK (`imap_count.py:154`), `two-leads:` check name | OK (see Minor) |

## Markdown and wording scan of the changed lines

No unbalanced backticks, split table rows or backslash-escaped quotes found in the changed lines of the eight files (every changed table row I opened is on one line). All `tests/...`, `src/...`, `scripts/...`, `docs/...`, `demo_only/...` paths and all backticked `test_...` names in the eight files exist (script check, wildcards `test_x_*` also matched at least one test).

## Counts

Blocker 0, Major 3, Minor 6, Nit 0.
Head SHA of the tree (f3c39cf8 plus patches, uncommitted edits): not recorded (git was only used read-only for `diff` and `status`).
