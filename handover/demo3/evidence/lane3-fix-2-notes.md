# Lane 3 fix 2 (B2): settings that start silently, portal and contract wording
Base f3c39cf89ec989f032ea48a23cfd824b88da9c68. Worktree /home/user/work/b2-base (patched). UTC 12:43 to 13:12.
Patch: `lane3-fix-2.patch` SHA256 4043f86076dd67b979ec83a78df38878d5f260392dac8462751f9b7d51d9b942 (12 files).
Variant for the claims stack: `lane3-fix-2-for-stack.patch` SHA256 05eaa0152661af6a2834a150b0dadbe65ee30a891f186e200cbc5c40d67e1d80 (same, without docs/why-this-code.md).

## Failures and gaps first
- Finding 1 (DESK_BIND) NOT reproduced as "starts with no error": on this machine `DESK_BIND="not an address"` ended with "cannot bind not an address:0: gaierror", exit 5 (late, after the bind retries), no traceback. The cold reader's machine resolved it differently. The defect (a bad bind is not exit 4 at the start) is real, so it is fixed anyway.
- The old test `test_a_plain_value_error_that_is_not_a_setting_is_not_called_a_setting_refusal` (tests/test_env_numbers.py) pinned "broken replies file = not exit 4". That contradicted the documented rule, so I CHANGED it (now uses an unreachable demo server, exit 1). A reviewer should look at this edit.
- Not done: a DESK_DB_PATH that is an existing folder still gives exit 2 "cannot take the lock file" (not 4). Not in the cold reader's list; not reproduced or changed.
- Not run: the full suite (only the 48 files that mention config/settings/exit codes/docs; 2504 passed). Mutation run not done.
- I first ran `pkill -f` once (the system refused it; nothing was killed). My own fakes server was stopped by its saved PID.
- Claims-stack overlap: `docs/why-this-code.md` hunk conflicts (the stack already made the same "About 200 lines" edit, same words, other context lines). Use the for-stack variant there. With B1 (`lane3-fix-1.patch`): both apply in either order only because I dropped my docs/limits.md edit (B1 changes the same exit-codes line). So the exit-code list in limits.md is NOT updated by me; settings.md line 3 carries the detail.

## Findings table
| # | Finding | Reproduced? | Decision | Test | Before / after |
|---|---|---|---|---|---|
| 1a | DESK_BIND bad value | partly (exit 5 late, not "no error") | CODE: `_is_bind_name` in `Config.__post_init__` (config.py), exit 4 "DESK_BIND must be an IP address or a host name" | test_a_bind_that_is_no_address_*, ..._refused_by_the_settings[7], ..._still_accepted[11] | before: 5 + gaierror; after: 4 |
| 1b | DESK_DB_PATH="" | yes, `sqlite3.OperationalError` traceback, exit 1 | CODE: `Config.from_env` refuses empty/blank (Path("") is "." a folder; desk.py:313 comment) | test_an_empty_db_path_* | before: 1 + traceback; after: 4 |
| 1b2 | DB folder cannot be made (/proc/nope/x) | yes, FileNotFoundError traceback exit 1 | CODE: server.main wraps `mkdir` (OSError), exit 4, no path printed | test_a_db_folder_that_cannot_be_made_* | 1 -> 4 |
| 1c | DESK_REPLIES_PATH missing or broken | yes, traceback exit 1 | CODE: loader.py wraps `RecordedQualifier` (OSError, ValueError) into SettingRefused, no path | test_a_missing_or_broken_replies_file_* [4 cases] | 1 -> 4 |
| 1d | key/password files missing or too short start normally | yes (hubspot, live key; provider password too) | CODE (loud failure): `check_secret_files` in loader.py, called by server.main; each kind has `check_key_file` / `check_password_file` that read the file once with the existing reader; message "DESK_x_FILE: <fixed text>", never path or secret. Reason: a desk that starts and then fails every call is worse than a refusal; hubspot still re-reads each call (a replaced key works); live key cached as before | test_a_missing_short_or_wrong_key_file_* [9], test_a_good_key_file_starts_* [3] | before: starts (rc 124 = still running); after: 4 |
| 2 | "Under 100 lines" vs 205 | yes (`wc -l` 205) | DOC: "About 200 lines" (docs/why-this-code.md:24) | none (prose) | |
| 3 | "Hide email addresses" | yes, contract.md:222; tests/test_portal_mode.py:98-99 already pin the portal strings | DOC: "Hide names and email addresses" | existing test_portal_mode | |
| 4 | `reminders` key in GET /fake/outbox | yes, demo_only/fakes_server.py:88 | DOC: contract.md:229 lists `reminders` | none (prose) | |
| 5 | portal pages not separate URLs | yes (hash routes, portal.js:515,548) | DOC: docs/portal.md line 5 says so and points to `GET /api/ui/...` | none (prose) | |
Docs also changed in docs/settings.md: line 3 (exit 4, key files read once at start), rows db_path, bind, replies_path.

## FAILS-BEFORE evidence
New file tests/test_settings_lane3.py (39 tests). On BASE (clean worktree of f3c39cf8 plus only the test file): `25 failed, 14 passed in 548.79s`; first failure line: `E       Failed: DID NOT RAISE SettingRefused`. The 14 passes are the 11 "still accepted" binds and the 3 good-key starts (they must pass on both). Patched: `39 passed in 4.45s`. Logs: /home/user/work/b2-tmp/base.log, new.log, patched.log.
Patched family run (every tests/test_*.py that mentions Config, from_env, returncode, contract.md, why-this-code, portal.md, settings.md or exit code; 48 files; no tests/test_config*.py exists): `2504 passed, 54 skipped in 668.53s`, EXIT=0. After reverting the limits.md edit: test_hygiene, test_codeant_hygiene, test_portal_mode `67 passed, 4 skipped`. `ruff check .`, `ruff format --check .` clean; `bandit -ll -r src` no issue lines (only comment-parse warnings). The skips are the existing skips (other OS, missing tools).

## RUNG TABLE
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| bind name check | refuse a bad address at start | 1 reuse `ipaddress`, existing `_HOST_NAME` | config.py:61 | exit-4 contract of the desk | KEEP-CODE (12 lines) |
| empty DB path | refuse | 1 | config.from_env | | KEEP-CODE (2 lines) |
| db folder / replies file | exit 4 not traceback | 1 reuse SettingRefused path in main | server.py, loader.py | the documented exit-code table | KEEP-CODE |
| key files at start | loud failure | 1 reuse existing readers (`_key`, `_read_key`, `read_secret_file`) | no new parsing | secret never printed | KEEP-CODE (3 short methods) |
| prose findings 2-5 | sentence wrong | fix the sentence | | | CUT-TO-DOC |

## Files changed
contract.md, docs/portal.md, docs/settings.md, docs/why-this-code.md, src/lead_desk/{config,crm_hubspot,live_claude,loader,server,smtp_provider}.py, tests/test_env_numbers.py (one test changed), tests/test_settings_lane3.py (new).

## Not changed, and why
- DESK_SMTPP_STATS_FILE, DESK_SMTPP_CA_FILE and the other "NOT TESTED" cold-reader rows: outside this brief.
- Wording items U1-U8 and section 3 of the cold-reader file (jargon): outside this brief (U4, U5, U7 are doc gaps worth a later pass).
- docs/limits.md exit-code line: left to B1 (conflict).
- Claims stack: nothing changed in it.
