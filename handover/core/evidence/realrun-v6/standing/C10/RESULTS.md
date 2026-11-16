# C10 docs-only fix proposal (patch NOT applied anywhere)
Patch: /home/user/build/rr6/out/C10/docs-fix-v1.patch (107 lines; diff of tree-A1 vs tree-C10 for 4 files: README.md, docs/settings.md, docs/real-services.md, scripts/real-run.env.example). `git apply --check` in tree-A1: clean. tree-C10 edited in those 4 files only (no src, no tests).
Check run: pytest on tests/test_desk_address_required.py test_env_numbers.py test_real_run_v6.py test_path_confinement.py test_hygiene.py in tree-C10: no failure printed (tail showed only skips: ntpath 3.13, gitleaks missing x4); the pass count line was cut by my tail, so I do not state a count. Other test files not run.

## Items (all verified against code before editing)
| id | file (line before in tree-A1 -> after in tree-C10) | before | after | proof (command / code read) |
|---|---|---|---|---|
| M1 | docs/settings.md DESK_SMTP_TIMEOUT_SECONDS | default same as DESK_SEND_TIMEOUT_SECONDS | default 5 seconds whatever the send timeout; own value used as given | RUN python -I with DESK_SEND_TIMEOUT_SECONDS=8: Config 8.0, SmtpSettings().timeout_seconds 5.0; smtp_outbox.py:79, :303 |
| M2 | docs/settings.md DESK_SMTPP_TIMEOUT_SECONDS | same | default 5; only lowered to min(send timeout, 9); real run sets send timeout 8 so mail still uses 5 | RUN: ProviderSettings default 5.0; smtp_provider.py:88, make_outbox :323-330; run_real_check setdefault 8 (C3) |
| M3 | docs/settings.md rota row | optional crm_owner_id | key required, value may be empty | config.py:406 exact keys; C3 run showed refusal text. Not re-run by me (code read) |
| M4 | docs/real-services.md "full list of checks" | in --help text | F1-F6 in function comment; seven load checks in load_tools/check_invariants.py | run_real_check.py:335,347 grep; check_invariants.py docstring "seven checks" |
| M5 | docs/settings.md line 3 and HubSpot key bullet | first CRM call / first send | every CRM call / every send, file reopened; live key kept in memory | crm_hubspot.py:257-285 `_key()` opens file each call; smtp_provider.py:237 read_secret_file per send; live_claude.py:417 cached. Mailbox-password wording left unchanged (not verified) |
| M6 | docs/settings.md DPLD_REQUIRE_SCAN bullet | only tests/test_hygiene.py | two test files | grep REQUIRE_SCAN tests/*.py: test_hygiene.py:27,149,195; test_gitleaks_exceptions.py:121,143. GITLEAKS_BIN likewise reaches both (GITLEAKS_ENV imported, :144) |
| M7 | docs/real-services.md line 3 | "The steps above..." | "The demo in README.md uses only the demo stand-ins; nothing in this file is part of it." | file starts at line 1 with that sentence; read |
| W1 | docs/settings.md run_live_check flags | list lacked 3 | adds --leads, --runs, --assume-yes (loopback --base-url only) | run_live_check.py:213-227, :238 |
| C1-a | docs/real-services.md step 3 | self-test "no real service" | also asks start question: terminal, type 127.0.0.1; --assume-yes for scripted use; worst-case numbers are caps vs local fakes | run_real_check.py:1249 question; --assume-yes help :1086; C1 rows 1,2,13 (pty run, EOF only). I did not run the self-test (brief: never answer prompts) |
| C1-b | docs/real-services.md step 1 | - | replace every <...>; plain UTF-8 without BOM, line-1 refusal text | load_env reads encoding="utf-8" (run_real_check.py:747), so BOM stays in the first name; C1 row 7 observed |
| C1-c | same step 1 | - | write every path as a full path | script checks relative path from its own folder; desk child started with cwd=REPO (run_real_check.py:1019). READ only, not run; this is stronger than C1 row 23 |
| C1-d | README.md Layout (line ~148) | scripts: helpers | precheck.py is an imported helper, not a command | scripts/run_live_check.py:38, run_real_check.py:74 import it; C1 row 31 |
| C1-e | docs/settings.md "Addresses a key goes to" + scripts/real-run.env.example:19 | - | names DESK_HUBSPOT_ALLOW_ANY_BASE_URL (and DESK_LIVE_ALLOW_ANY_BASE_URL) next to the loopback rule and the refusal text | crm_hubspot.py:171; config.py:185,220 |
| BOM note | docs/settings.md HubSpot key bullet | - | BOM accepted in key file | crm_hubspot.py: decode("utf-8-sig"); smtp_provider.py:152,164 (password file too) |

## Skipped / not confirmed
* W2 (" off " with spaces) and W3: harmless / matches, no edit.
* C3 minor: DPLD_REQUIRE_DEMO also set by tests/test_demo_folder_guard.py:42 (doc says only conftest.py): reported by C3, I did not edit (not in my list); next step: reword settings.md last bullet.
* Not edited: C1 rows 5,20,22,29 doc-only parts (silent unknown names, duplicate names, ledger message): need code or owner decision.

## NEEDS CODE (not patched)
1. scripts/feed.py: `--index 0/9999` prints a raw ValueError traceback; desk not running prints a URLError traceback (C1 rows 34,35). Next step: catch ValueError and URLError in main, print one plain line ("the desk is not running; start it with scripts/start_all.sh"), exit 2; add test.
2. scripts/run_real_check.py `--dry-port-base 99999`: refusal says "a file or folder cannot be used (OverflowError)" (C1 row 10). Next step: check 1..65535 minus the ports used before building settings; plain port message.
3. scripts/run_live_check.py `--price-date`: not checked for format or future date; also `--effort bogus` and duplicate `--model` accepted (C1 row 28). Next step: validate YYYY-MM-DD, not in the future; refuse unknown effort and repeated model ids.
4. run_real_check.py `--dry-smtp-script bogus` not refused before the question (C1 row 11); config BOM (utf-8-sig in load_env) and unknown/duplicate config names (rows 7, 22): code options if the owner prefers code to the doc note.
Processes started by me still running: 0. Scratch: RR/tmp-C10 (empty), tree-C10/.tmp-run.
