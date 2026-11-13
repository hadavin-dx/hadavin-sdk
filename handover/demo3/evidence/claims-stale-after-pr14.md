# Claims patches vs public main f3c39cf (after PR #14): stale check (AGENT J, read-only)

Checked 2026-11-13 ~11:40Z / IST 17:10. Sources: six patches in /home/user/work/claims-in (v1, code-fix-v1, v1b, v2, v2b, v3), 125 added lines read in full. Object store: /home/user/work/src (f3c39cf8 and c30c373). No tests, lint or collection were run (brief). The backslash studio files are not in this checkout; `handover/BRIEF-PREAMBLE.md` was read.

## Count summary
Of 125 added lines, 8 mention something PR #14 changed or a number checkable on f3c39cf8. Result: 2 STALE rows (both in v1 `versions.md`: the collection count 3726 and "91 lines"), 4 CANNOT TELL rows, 10 STILL TRUE rows. The patches touch none of the 14 files PR #14 changed (no overlap), and all six apply cleanly, in order v1, code-v1, v1b, v2, v2b, v3, to both c30c373 and f3c39cf8 (`git apply --check` on `git archive` copies in the scratchpad). PR #14's path-confinement, read-only-URI, refusal wording, option names and exit-code 2 changes are NOT mentioned by any added sentence. Biggest gap: no patch states the 3683 count; the only live test-count claim is stale.

## Gaps and CANNOT TELL (first)
| patch | file | sentence | what PR #14 changed | verdict |
|---|---|---|---|---|
| v1 | versions.md | "...counts on them add up to 3726 (added up by hand...)" | Brief says main before PR #14 collected 3605, not 3726; PR #14 added tests (new `tests/test_followup_b.py`; `test_path_confinement.py` +692 lines; sonar_p2 +76). On the last PR head the run had 3683 passed + 200 skipped = 3883 (brief). I did not run `--collect-only`. | CANNOT TELL why 3726 differs from 3605 even on the old base (the patch author's tree may have differed); STALE against f3c39cf8 either way, see below |
| v1/v3 | docs/tests.md, limits.md, versions.md | "2449 passed, 15 skipped", "2462 passed, 2 skipped", "2516 tests: 2513 passed", "114 passed and 113 skipped", "16 minutes 33 seconds" | Dated run results of earlier commits, each saying it was not repeated on this commit. PR #14 does not change them. | CANNOT TELL: no log shipped; they stay true only as history and are far below 3683/3883 |
| v3 | docs/tests.md | "the same file lists 52 on the commit that holds this file (`test_except_clause_hierarchy.py`)" | File not touched by PR #14. It has 8 `def test_` (parametrised), so the count needs a collect run. | CANNOT TELL (unchanged by PR #14; not collected) |
| v3 | docs/tests.md | semgrep log "Scanning 64 files tracked by git ... 47 files" | PR #14 added no file under src, scripts, load_tools, tools, n8n (65 files in both commits, all file types). | CANNOT TELL (log of run 43403502735 not available; scope unchanged) |

## STALE
| patch | file | sentence (verbatim, short) | what PR #14 changed (f3c39cf8) | verdict |
|---|---|---|---|---|
| v1 | versions.md | "`pytest --collect-only -q` ... 91 lines in all" (one line per test file) | PR #14 ADDED `tests/test_followup_b.py` (git diff --name-status: `A`, defines test functions: line 1 docstring "sys.path order of scripts/n8n_api.py and the comment of scripts/start_all.sh"). Test files with `test_*.py`: 91 on c30c373, 92 on f3c39cf8. | STALE: 92 test files on f3c39cf8 |
| v1 | versions.md | "add up to 3726 ... a count of listed tests" and "`tests/test_workflow_run_flags.py: 10` (that is its last line)" | Number: more tests exist now (def-test count over tests/: 1640 on c30c373, 1679 on f3c39cf8, +39 definitions, more with parametrisation). Last-line part: `test_workflow_run_flags.py` is still the alphabetically last test file on f3c39cf8 (its 10 is parametrised, 4 `def test_`; not collected). | STALE for the total 3726; last-line part STILL TRUE. Do not write 3726, 3605 or 3683 as "this commit" without a fresh collect run on the final head (the brief's 3683 passed + 200 skipped is a PR-head run, not the merge commit). |

## STILL TRUE
| patch | file | sentence | check on f3c39cf8 | verdict |
|---|---|---|---|---|
| code-v1 | scripts/start_all.ps1 | `-not [string]::IsNullOrEmpty($env:DESK_LEADFLOW_FILE) -and $null -eq $env:DESK_NUDGE_TO` | PR #14 changed `scripts/start_all.sh` (comment lines 6-8: "unless DESK_LEADFLOW_FILE is off or empty, DESK_NUDGE_TO is reminder@example.test"; code line 17 has `[[ -n "$DESK_LEADFLOW_FILE" ]]`). `start_all.ps1` line 9 on f3c39cf8 still lacks the empty check. | STILL TRUE, and now needed: it makes the .ps1 match the .sh and its new comment |
| code-v1 | tests/test_input_edge_cases.py | "`assert rig.qualifier.calls == 1`; `tests/test_ai_after_claim.py` pins that too" | Line 79 on f3c39cf8 is still `in (1, 2)` (patch applies); `tests/test_ai_after_claim.py` exists ("one claimed row, one model call"). Not run, so whether `== 1` always holds is unproven. | STILL TRUE as to the files; behaviour CANNOT TELL (not run) |
| v3 | docs/settings.md | `tools/scrub_n8n_export.py` (... "no settings") replaces ... localhost ... | PR #14 changed only its import comment and sent usage and "refused:" text to stderr (exit code 2 unchanged); `scrub()` logic untouched. Note: line 125 of the same file says `LEAD_DESK_PATH_ROOTS` is read by this tool, which sits oddly beside "no settings" (the same wording was already in c30c373). | STILL TRUE for the cleaning rules; "no settings" is a pre-existing near-contradiction |
| v1 | docs/why-this-code.md | n8n scrub tool "About 200 lines" | `tools/scrub_n8n_export.py`: 205 lines on f3c39cf8 (202 before) | STILL TRUE |
| v1 | docs/why-this-code.md | `CRM_CHOICES` (`fake`, `hubspot`), `OUTBOX_CHOICES` (`http`, `smtp`, `smtp_provider`), `QUALIFIER_CHOICES` (`recorded`, `live_claude`) in constants.py | `constants.py` lines 119-128 match | STILL TRUE |
| v1/v3 | docs/portal.md | `POST /api/demo/crash`, `POST /api/demo/burst`; "http://127.0.0.1:8765/ui/" | `demo_only/portal_demo.py` changed one line (the `DESK_SCHEME as DESK_SCHEME` re-export); the routes appear in `portal_demo.js` lines 163, 207; `config.py:424` port 8765 | STILL TRUE |
| v3 | docs/limits.md | 256 connections; `EVICT_MIN_IDLE_SECONDS` 2 s; open-file reserve 96 | `constants.py`: MAX_CONNECTIONS 256 (l.203), EVICT_MIN_IDLE_SECONDS 2.0 (l.212), FD_RESERVE 96 (l.248) | STILL TRUE |
| v1b | docs/settings.md | "`CALL_DEADLINE_MAX_SECONDS`, 9 seconds"; `DESK_SMTP_TIMEOUT_SECONDS` default `5.0` | `constants.py:82` = 9.0; `config.py:429` send_timeout_seconds 5.0 (the SMTP 5.0 default itself was not found by grep; CANNOT TELL for that part) | STILL TRUE (9 s); SMTP default CANNOT TELL |
| v3 | docs/settings.md | `DPLD_REQUIRE_DEMO` read only by tests/conftest.py, set to 1 in lint.yml and sonar.yml | conftest.py:22; lint.yml:98 and sonar.yml:50 both `"1"` | STILL TRUE |
| v3 | docs/limits.md | exit codes 1, 2, 4 (and 5) of `server.py main` | Constants: EXIT_ADAPTERS_UNREACHABLE 1, EXIT_ANOTHER_DESK 2, EXIT_DESK_SETTING_REFUSED 4, EXIT_PORT_UNAVAILABLE 5; server.py not changed by PR #14. (Code 3 not located by my grep.) | STILL TRUE for 1, 2, 4; 3 and 5 not checked line by line |

## Not touched, no PR #14 overlap
All lines in lint.yml, sonar.yml, semgrep.yml, contract.md, loader.py, SECURITY.md, README.md, versions.md lock-file text, hubspot_probe.py: the files and the facts they state are outside the 14 files PR #14 changed.

## Follow-ups for the demo session
1. Replace the 3726 / "91 lines" sentence with a fresh collect result on the final commit (92 test files).
2. Optional: v3's `docs/settings.md` could add that PR #14 made the scrub tool refuse out-of-folder paths with exit 2; the patches say nothing wrong there.

---
ADDED BY THE LANE LEAD (11:44Z / 17:14 IST), measured on f3c39cf8 in /home/user/work/i-base: `pytest --collect-only -q` = **3883 tests collected** (3 seconds, nothing run); `ls tests/test_*.py | wc -l` = **92** files. 3883 = 3683 passed + 200 skipped (the last PR head run by agent F), so the "3726" in the v1 patch's versions.md is wrong for f3c39cf8 (it was neither 3605 on the old main nor 3883 now) and "91 lines" should read 92 for the test files if that is what the sentence counts.
