# RESULTS-C (builder C, round r7u): m6, n1, n2, n5 and three extra tests. Tree: tree-R7U-C. Written 2026-11-14.

## 0. NOT RUN / NOT CHECKED / FAILED first
- Nothing failed on the final bytes. Honest slip on the way: my first mutant run (`mut-results-INVALID-first-run.txt`) was INVALID: two of my own tests used `python -c`, which the repository helper `run_python` refuses, so test c2 failed on every mutant and every "KILLED" in that file is false. Found because every run took 0 s; fixed (the text now runs from a file), control run passed (103 passed), the whole mutant set was rerun (section 5).
- NOT run: the full suite (the lead runs ONE guard run after the merge). NOT run: a Windows machine, Python 3.13 (the venv is 3.12). The take-side banner test q1 is not mine and not run here.
- NOT done by me: the README text on disk (handover/ is not editable by builders): `README-r7u-SNIPPET.md` has exact lines to delete or replace (lead applies).
- One existing r7t test changed (section 4). Builder A/B files untouched: `scripts/run_real_check.py` is byte-equal to r7t in my tree.
- No pre-existing r7t bug found by the three extra tests: c5, c6, c7 PASS on r7t sources (they are PINS, see section 3), crm_hubspot.py code is unchanged (docstring only).

## 1. Findings and fixes
| id | what | fix | test ids |
|---|---|---|---|
| m6 | the two raw-socket fakes (`fake_imap.py`, `fake_smtp_tls.py`) got `require_loopback_host` through `demo_only/bad_request.py`, which loads `lead_desk.config`, `scripts.http_guard`, `tools.refusing_args` | new stdlib-only module `src/lead_desk/loopback.py` (only `ipaddress`): `is_loopback_host`, `require_loopback_host`, `LOOPBACK_HOST_TEXT`. `config.is_loopback_host`, `demo_only.bad_request.require_loopback_host` and `tools.refusing_args.LOOPBACK_HOST_TEXT` are now the SAME objects (imports, no copy). The two fakes import `lead_desk.loopback` directly. Package `lead_desk/__init__.py` is a docstring only, so importing `lead_desk.loopback` loads nothing else. | c1 (5 test functions, 23 cases incl. the text pin), c2, c3 (2) |
| m8 (module text only) | the rule judges a spelling; LOCALHOST accepted by design, no promise of a listener | stated in the module docstring (A/B own the rest of m8) | c4 (doc check) |
| n1 | run_stats docstring said no test checks atomicity | rewritten: says what t10 checks (JSON dump / os.replace made to fail: the previous file stays; the target name changes only by os.replace) and what no test does (stop a real process mid-write, fill a real disk); names `write_stats_strict` and `create_open` | n1 (doc check) |
| n2 | crm_hubspot docstring lacked create_open, create_unknown, CrmCounterUnwritable | new paragraph under "Counters": the four outcomes, the refusal when the counters file cannot be written, the settle rule, the stale-open-is-safe case | n2 (doc check) |
| n5 | superseded README lines | `README-r7u-SNIPPET.md` (delete fix/README.md line 31 and APPLY-README-SNIPPET.md; the "F3" sentence does NOT exist in R7S-RESULTS.md, only in frozen r7s snapshots and quotes; replacement for R7T-RESULTS.md section 9 bullet given) | none (text) |
| extra | put where `_settle_create` raises | none needed | c5 PIN |
| extra | two concurrent puts -> create_open == 2 | none needed | c6 PIN |
| extra | 201 without an id -> create_unknown | none needed (the 201 falls to `_fail`, which raises CrmError "unexpected reply", and the `except Exception` settles create_unknown) | c7 PIN |

Standalone import test (c2): fresh `python -I`, only `src/lead_desk` put on the path, `import loopback`; it accepts 127.0.0.1, refuses 0.0.0.0 (built from parts), "", None, 7, and `sys.modules` holds no module whose first name part is lead_desk, scripts, tools or demo_only (printed `HEAVY=` empty). c3: `import demo_only.fake_imap, demo_only.fake_smtp_tls` loads none of lead_desk.config, scripts.http_guard, tools.refusing_args, lead_desk.constants, lead_desk.envnum; `lead_desk.loopback` is loaded. Honest limit: `demo_only.fake_imap` still needs the repo root and `src` on the path (it imports `demo_only.fake_smtp_tls` and now `lead_desk.loopback`); only the HEAVY modules are gone, not the package roots.

## 2. Recipe used
`out/R7U-C/run.sh <tree> <pytest args>` = TMPDIR outside the tree, PYTHONPATH=<tree>/src, PYTHONDONTWRITEBYTECODE=1, venv-br python -m pytest -q -p no:cacheprovider -rfs, under `unshare -n` + `lo_up-q4g.py`. No sleep, no real kill, no spend, no prompt answered; no /dev path; no pkill.

## 3. Before / after on the r7t sources (`before-final.log`: final test file copied into a byte copy of tree-R7T, which was deleted after)
- Before (r7t sources): **29 failed, 3 passed**. The 3 passes are the PINS: `test_c5_pin_a_put_whose_settle_raises_...`, `test_c6_pin_two_puts_at_the_same_time_...`, `test_c7_pin_a_201_without_an_id_...`. The 29 failing ids: all of c1 (5 functions, 23 ids incl. the parametrized spellings and the text pin), c2, c3 (2), c4, n1, n2. HONEST NOTE: the c1/c2/c3/c4 failures on r7t are "the module does not exist / the fakes still import the heavy modules"; `test_c1_pin_the_refusal_text_is_the_fixed_line_the_scripts_show` fails on r7t only for that reason and is otherwise a literal pin of the wording. The refusal behaviour itself was already right on r7t (t6, t12 pass on both).
- After (final bytes): `final-own.log` 32 passed in 2.75 s. Wider: `after3.log` (earlier test bytes, before a formatting-only edit and the -c fix) 247 passed = my file + tests/test_r7t_findings.py + tests/test_r7s_findings.py + tests/test_bind_refusals.py; the final bytes of my own file were rerun alone (32 passed). The r7t file was NOT rerun after the final formatting edit of MY file (it does not import it).

## 4. Existing test changed
`tests/test_r7t_findings.py`, table NOT_A_BIND of t6b. Old: contained the line `("demo_only/bad_request.py", "require_loopback_host"): "the refusal itself (tested directly in t6c)",`. New: that line deleted (the def moved to `src/lead_desk/loopback.py`; t6b's second assertion "table entry that no longer exists" would otherwise fail; it did fail on the first run, `after2.log`). t6c, t12 still import `require_loopback_host` from `demo_only.bad_request` (the re-export) and pass. I edited a test file I do not own, because the table is a name list that the move invalidates; the lead should know the r7t test file differs by this one line.

## 5. Mutants (`mut_c.py`, one at a time, one runner; restore byte-equal verified by sha256 each time; `mut-results.txt`)
Tests per mutant: my file + r7t `-k "c1 or c2 or c3 or c4 or c5 or c6 or c7 or t6 or t12"`, `-x`.
28 mutants: 27 KILLED, 1 SURVIVED (equivalent), 0 not applied:
- light module: L01 accept non-loopback, L02 drop isinstance, L03 refuse nothing, L04 refuse everything, L05 case-sensitive localhost, L06 localhost prefix, L07 empty string loopback, L08 wildcard loopback, L09 any private address, L10 scope id allowed, L12 mapped v4 not unwrapped, L13 unreadable text is loopback, L14 text changed (first SURVIVED, killed after I added the literal pin test), L15 returns a constant, L16 heavy import: all KILLED.
- L11 "half bracket allowed" (drop the `"[" in bare or "]" in bare` clause, keep `%`): SURVIVED, EQUIVALENT: `ipaddress.ip_address` raises ValueError for `[::1`, `[[::1]]` and `[::1]` (run and shown), so the explicit clause is belt and braces. I added `[[::1]]`, `[::1`, `::1]` to the refused list so a future change that parses brackets is caught.
- re-export and callers: R01 re-export replaced by a copy, R02 config no longer shares the rule, R03 refusing_args own text, R04/R05 each fake skips the refusal, R06 fake_imap imports the heavy path: all KILLED.
- settle/put (code unchanged by me; mutants test the three new pins): S01 settle drops the outcome (killed by c6), S02 settle does not close the open (c6), S03 open not written before the request (c5), S04 201 without an id taken as created (c7), S05 unknown counted as none (c7): all KILLED.

## 6. Guard files run in full (`guard.log`, `guard-files.txt`: 13 files)
test_file_call_guard, test_r7n_findings, test_except_clause_hierarchy, test_r7_fake_bad_requests, test_r7_mail_context, test_script_number_limits, test_demo_folder_guard, test_http_guard, test_mutation_guards, test_r7b_guard_replant, test_r7c_clean_tree_guard, test_server_stop_guard, tree_guard: **458 passed, 2 warnings in 170 s** (same run line `REPLANT: 145 of 145 shapes found`). Run on the tree without a `.git` and without DPLD_REQUIRE_SCAN; the git-dependent guards pass or skip themselves there (no skips shown: `grep skipped` empty). The lead's single guard run on a staged git copy remains the authority.

## 7. Ruff and suppressions
Ruff 0.17.1 on a copy of src, tools, demo_only, scripts and my two changed test files plus support.py (check and format --check): my files clean. The one remaining item, `scripts/run_real_check.py` import order, is an artifact of my copy lacking `load_tools/` (same file, same bytes as r7t, not mine). Format: 59 files already formatted after one `ruff format` of my test file. Suppressions by the one grep: **367**, delta 0 on r7t.

## 8. Residuals
- None open that I found. Stated limit: the fakes still need repo root and `src` on the path (section 1).
- The pins c5-c7 do not fail on r7t because r7t was already right there; the review's "missing tests" gap is closed, not a bug.

## 9. Ask back (from the order)
The take-side banner test q1 is in `tests/test_r7q_findings.py`: `test_q1_the_banner_cost_counts_the_longest_request_the_run_can_send` (line 110); the same file has `test_q1_longest_request_bytes_...` (135, 151) and `test_q1_the_email_key_is_the_one_the_desk_asks_with` (171). The banner-figure test of r7t is `tests/test_r7t_findings.py::test_t13_*`. I read these names from tree-R7U-C; I could not check which of them the lead means by "take-side banner test", the take tree is not reachable.

## 10. Files (out/R7U-C)
r7u-C.diff (10 files: loopback.py new, config.py, bad_request.py, fake_imap.py, fake_smtp_tls.py, refusing_args.py, run_stats.py, crm_hubspot.py, test_r7t_findings.py, test_r7u_c_findings.py new), sha256.txt (f4e94d1d45b38cb43fbbf2f980640c81e34f535141f478fd43bf0fb20f7d563e), RESULTS-C.md, README-r7u-SNIPPET.md, mut_c.py, mut-results.txt, mut-results-INVALID-first-run.txt, before.log (first run, earlier test bytes), before-final.log, after*.log, final-own.log, guard.log, run.sh, checkpoint.md.
