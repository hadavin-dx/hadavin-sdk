# P3 path helper and connection-string builder (patch: sonar-p3-path-helper.patch, base db54e13)

## Failed or uncertain first
* I cannot see the Sonar result. Whether Sonar's taint analysis (rules S8707, S8706) accepts my validation as a sanitizer is NOT verified. Confidence 30-40 percent for the path issues, 55 percent for S8706.
* The rule description text is not served by the public API (rules/show returns no htmlDesc), rules.sonarsource.com is blocked in this session, and the issues in issues-pr4-0253.json carry no flow metadata (flows is null). So the sanitizer list could not be researched; the rule names only say "Agentic workflows should not be vulnerable to path injection / connection string injection" and the messages say the source is "faulty LLM-supplied CLI arguments".
* The core cloud session (core/cloud-handover REPORT.md) has NO Sonar-verified pattern: its pathguard (wip/cloud-sonar-path ddf1d584) says "Sonar result NOT checked". I did not reuse it (it is a large per-component rule set and was never Sonar-tested); I used the same resolve + is_relative_to idea in a smaller form.
* Policy change to know: a path now must be in the current folder, the repository folder or the temp folder (or LEAD_DESK_PATH_ROOTS). A run that keeps logs in another folder is refused until it is listed. Documented in load_tools/README.md. Windows run not tested here (Linux only; mypy checked win32 typing).
* Full test suite NOT run (lead runs it). Not checked: Sonar, CodeQL, Windows behaviour.

## What changed
tools/pathconfine.py (new, stdlib only): confine(path, what=..., roots=None) = os.path.realpath (follows links, removes ..), refuse empty/NUL/control chars/over 4096 chars/unresolvable/outside every allowed folder (os.path.commonpath after normcase; other drive = outside). Message names the argument, never the value. readonly_sqlite_uri(path) = confined path .as_uri() (percent-encodes ? and #) + fixed "?mode=ro".
Call sites (the check is the first statement of the function that holds the sink, and only the returned path is used after):
* load_tools/check_invariants.py: read_jsonl L63, read_crm L82, read_book L96 (S8706 via readonly_sqlite_uri, no f-string), _intended, _facts_say_live, _drain_marker; also --json output (sibling, not flagged).
* load_tools/load_driver.py run(): log and facts_path confined before both writes (L366, L377).
* scripts/n8n_api.py import FILE; scripts/run_real_check.py load_env; tools/scrub_n8n_export.py in and out.
Siblings left alone: n8n_api reads N8N_API_KEY_FILE (environment, not argv); demo_only and tests are out of Sonar scope.

## Sanitizer pattern expected to be accepted
The strongest conventional one (OWASP / CWE-22): realpath then commonpath-in-allowed-folder, refusing by exception, right before the sink and returning a new Path made from the resolved text. The check lives in a helper in another module, one call deep; Sonar's taint engine follows calls, so if it only knows inline realpath+startswith style sanitizers the flow may still be reported. FALLBACK if the lead sees the issues remain after pushing: inline the same three lines (realpath, commonpath check, raise) in each flagged function instead of calling the helper, or look at the new flow text in the re-run (it will now show the sanitizer-free path). I did not inline preemptively because the brief asks for one helper.

## Expected to clear (guess, not measured)
S8707 x11 (check_invariants 63, 82, 597, 605, 614; load_driver 366, 377; n8n_api 192; run_real_check 645; scrub 178, 179) and S8706 x1 (check_invariants 96). The S8706 fix is the more certain one: the connection string no longer contains the argument text built with an f-string (as_uri quotes it, only the fixed option is appended).

## Tests (tests/test_path_confinement.py, 25 tests)
Fails before: with the helper present but the five tool files restored to db54e13, 8 failed, 17 passed (evidence-P3-fails-before.txt; the 17 are helper-only tests that cannot fail on old tool code). After: 579 passed, 4 skipped over test_path_confinement, test_load_tools, test_scrub_n8n_export, test_n8n_api_url, test_real_check_dry, test_hygiene (evidence-P3-after.txt). Covered: .. escape, absolute path, symlink to a file and to a folder, NUL/newline/ESC/empty/too long, bytes/None, a prefix-sibling folder (inside-evil), the message never prints the value, env extra folder, sqlite URI with ? # & in the file name opens read-only, each tool refuses outside paths and still works inside.
Lint (evidence-P3-lint.txt): ruff check, ruff format --check, mypy --platform linux and win32 clean (27 files), bandit -ll no findings (only comment warnings).

## Rung table
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| path confinement | refuse paths that leave the work folder | stdlib os.path.realpath + commonpath; pathlib is_relative_to (python 3.12 has it); werkzeug/flask helpers not applicable (no web) | stdlib docs; Sonar acceptance UNVERIFIED | allowed-folder policy, one error text | CUT-TO-CONFIG+GLUE (about 50 lines, stdlib only) |
| sqlite connection string | no injected option via a file name | Path.as_uri (stdlib) | tested with ? # & in the name | fixed mode=ro | CUT-TO-CONFIG+GLUE |
| core pathguard (wip/cloud-sonar-path) | same | read it | not Sonar-tested | too large for six CLI tools | CUT (not reused) |
| run | what |
|---|---|
| run | ruff check/format, mypy linux+win32, bandit -ll, 6 test files, fails-before on old tool code, git apply --check on a fresh clone at db54e13 |
| not run | full suite, Sonar, CodeQL, Windows, a real multi-folder run |

## Issues fixed per rule (by code, Sonar clearing not seen)
pythonsecurity:S8707 11 of 11 sites changed; pythonsecurity:S8706 1 of 1.

## Series conflicts
Touches load_tools/check_invariants.py, load_tools/load_driver.py, scripts/n8n_api.py, scripts/run_real_check.py, tools/scrub_n8n_export.py, load_tools/README.md plus new tools/pathconfine.py and tests/test_path_confinement.py. P1/P2 may also touch run_real_check.py or n8n_api.py (other rules in those files): textual conflict only if they edit the same lines (imports near line 92 of run_real_check, sys.path block of n8n_api, main of scrub). git apply --check alone on db54e13 passes; P3 applies cleanly on top of P1 (checked with git apply --check after applying P1); P2 not yet present, not checked.
R-numbers: preamble rules 5, 6, 7, 12, 20 (the bible folder is not in this environment; R-numbers beyond the preamble not looked up). EGM skipped here: the lead runs the EGM step (no EGM skills used by me). Head: db54e13 + uncommitted patch.
