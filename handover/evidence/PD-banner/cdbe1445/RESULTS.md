# EVIDENCE RUNNER results: PD Part 6 banner and guard, round 10, head cdbe1445fbff801a18d5deea6060fe2b66e3d982
Records only, no judgement. Raw logs: /home/user/build/evidence-raw/pdbanner-cdbe1445/ (probe scripts are there too).

## Not run, and deviations
- Not run (lead order): full pytest, complete banner_mutants table (307 rows), Playwright.
- Mutants: 89 of 307 rows run (29 named + 60 sampled, seed 10). The other 218 were not run.
- Deviation 1: `bandit` is not in the project venv (no bandit entry in the locked groups I synced). I ran the system bandit (/root/.local/bin/bandit) with the same arguments instead.
- Deviation 2: an early `uv run` call created a `.venv` inside the worktree (removed with the worktree). It did not touch tracked files.
- Deviation 3: item 4 builder claim does not match (see below). I copied all 5 changed files under tests/ into the old worktree (3 test files, banner_mutants.py, one .js probe).
- Slip in my probe 5b, first run: my first draft sealed the app differently from the tests; I fixed the probe and re-ran. The log kept is the fixed one.
- Env: names present before unsetting: GH_TOKEN, GITHUB_TOKEN, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_CA_BUNDLE, ANTHROPIC_BASE_URL (values never read). Unset for every command.
- hadavin_sdk.__file__ printed inside my worktree (new) and inside the old worktree (old) for every run.

## Table
| item | command | exit | last line |
|---|---|---|---|
| setup | worktree at cdbe1445, HEAD equal, status clean; uv sync --locked (3.13 and 3.12 venvs) | 0 | clean, 0 changes |
| 1 py3.12 | pytest test_banner_mutant_table, test_mode_banner, test_demo_only_guard, test_demo_only_guard_ci (these 4 files are all that import or name mode_banner / demo_only_guard / banner_mutants under tests/; src/hadavin_sdk/app.py imports mode_banner) | 0 | 322 passed in 23.23s (0 failed, 0 skipped) |
| 1 py3.13 | same | 0 | 322 passed in 23.04s (0 failed, 0 skipped) |
| 2 ruff check | src tests demos tools | 0 | All checks passed! |
| 2 ruff format --check | same | 0 | 327 files already formatted |
| 2 bandit | bandit -q -r src demos tools -ll (system bandit) | 0 | only warnings: "nosec encountered (B102), but no failed test on file src/hadavin_sdk/tools.py:389" |
| 2 gitleaks | git --redact --log-opts origin/main..HEAD (21 commits) | 0 | no leaks found |
| 3 mutants | 29 named rows (B12, J1b, R9A4, R9D6, R10A1-12, R10B1-4, R10C1-2, R10F1-7) + 60 sampled rows (seed 10 from the other 278) | 0 each of 8 slices | 89 of 89 good: 87 KILLED, 2 CRASH (R9A4, R9E4; both marked ok by the script), 0 BAD |
| 3 leftover | git status, git diff in worktree after runs | - | status 0 lines, diff 0 lines, HEAD still cdbe1445 |
| 4 fail-before | new test files copied onto dd827d79, 3 test files run | 1 | 24 failed, 290 passed |
| 5a | mode banner builder, 42 odd inputs (probe5a.log) | - | 0 banners with a made-up claim and a real service listed |
| 5b | app sealing probes (probe5b.log) | - | see below |
| 5c | guard on 10 made-up trees (probe5c.log) | - | exit codes below; matched text never printed |
| 5d | masker, 14 inputs (probe5d.log) | - | see below |

## Item 3 detail
Row names, verdicts and the seed list are in mut-*.log and rows.json. Slices of 6 to 15 rows, about 5 s per row. Every row: killed by its named killer test with its expected text (script verdict "ok").

## Item 4 detail (fail-before), by AST of test functions between dd827d79 and cdbe1445
- Real numbers: 62 new or changed test functions (59 new, 3 changed); builder claimed 36. DOES NOT MATCH.
- Of the 62: 23 fail on old code (matches the builder's 23); 39 pass on old code (builder: 13). DOES NOT MATCH.
- All 39 passing on old are named test_pin_* (list in failbefore analysis below); none of the 23 failing ones are named test_pin_*.
- One unchanged-by-AST test also fails on old: test_every_row_of_the_table_has_its_own_label_and_a_search_text_found_exactly_once (it reads the new table file copied in; first line: test_banner_mutant_table.py:15 assert [('J1b an unc...)] == []).
- Failing on old (23) with first failing line (from failbefore.log, file:line message): the unconfirmed-banner and sealing tests at test_mode_banner.py lines 2136, 2400, 2659, 2677, 2831, 2925, 2935, 2948, 2962, 2974, 2995, 3005, 3026 (AttributeError: app has no attribute _WARNED), 3059 (same), 451 (painted demo with overridden missing); guard tests at test_demo_only_guard.py 2214 (authorization=Bearer / Basic token stayed visible), 2230 (limit of the masker not stated), 2360 (bare OSError out of the copy), 2379, 2391, 2402 (loader, exempt file, marker read through a link), 2417 (chain of 45 links not named). Full names: failing-on-old.txt.
- Passing on old (39 names): in the AST list ast-changed.txt minus failing-on-old.txt. Examples: test_pin_the_lists_are_required..., test_pin_bzip2_needs_a_level_from_1_to_9, test_pin_the_masker_costs_time_in_proportion..., test_pin_a_copy_keeps_the_file_mode_when_os_has_fchmod, test_pin_every_killer_named_in_the_table_is_a_test_that_exists_in_its_file.
- Caveat: AST counts a function as changed if its dump differs, so a changed decorator or helper-name edit counts; I did not read each diff.

## Item 5 detail
(a) Banner builder, 42 inputs (unknown mode, None mode, list mode, bare string / dict / set / generator / None / bytes where a list is wanted, overridden None / str / unknown / dict, empty lists in demo and prod, names with newline, NUL, ESC, accents and Chinese characters, right-to-left mark, zero-width space, made-up words in a name in 4 spellings and fullwidth letters, 41-char and empty and None names, 10000 real names, 10000 stand-ins, duplicates, reworded German words, blank made-up sentence): 30 raised ValueError or TypeError, 12 returned a banner. None of the 12 has a made-up claim with a real service listed (0 of 42). Observations: overridden=["tools"] gave tone unconfirmed with no real list; one real service in demo gave tone real, no made-up text; German reword with real service gave tone real; a reworded real_connected of just "{names}" was accepted (tone real).
(b) App sealing (probe5b.log), each against a built app sealed with () as the tests do: control gives demo. After sealing with a real tool host: tool spec deleted -> unconfirmed; host list emptied -> unconfirmed; host added to a no-host spec -> unconfirmed; config.sources item added -> unconfirmed; config.systems item added -> unconfirmed; toolbox function replaced, spec added, specs cleared -> unconfirmed; hook execute replaced -> unconfirmed; dataclasses.replace -> unconfirmed; _sealed=None -> unconfirmed; overridden edited after build -> unconfirmed; registry or config replaced by a stub -> unconfirmed. copy.copy(app) -> demo (same parts, as designed). copy.deepcopy -> TypeError "an App cannot be deep-copied". Recorded as visible: calling the private _seal(()) again after tampering restores demo (the code comment says it is private by name only). Also: config.sources.clear() on an app whose sources were already empty left demo (nothing changed). banner_or_unconfirmed with a fake config with a real llm kind and overridden=() gave real; overridden=None gave unconfirmed; omitting overridden is a TypeError.
(c) Guard, CLI exit codes with matched text never printed in any run: clean tree 0; demo_only inside src 1 (folder-inside-product-root); product file naming the folder 1 (path:line:rule only); made-up id string 1 (fake-record-id); symlink in product root 1; src/pkg as a link to an outside folder 1 (symlink-in-product-root); BOM file 1; CRLF file 1; 9 MiB file 1 (file-too-large); missing product root 1 (product-root-missing); --root nonexistent 1 ("not a git checkout"). Copy run: entry swapped (check saw a link, entry is a file) -> SystemExit "changed or could not be copied (OSError); refusing", no traceback; file replaced by a link to /etc/hostname just before the read -> SystemExit "could not be opened as a plain file; refusing".
(d) Masker (_hide_secrets), made-up tokens built from parts: authorization=Bearer, auth=Bearer, secret=Basic, token=Bearer, authorization=Basic, AUTHORIZATION=bearer, tab after Bearer, x-auth-token=Bearer, api_secret=Basic with trailing words, quoted, two spaces, colon form, url with user info: token and scheme word hidden in all 13 (output shows "<hidden>"). Stays visible: a token of 11 characters after "token=Bearer " (the first 11 characters of the made-up token printed as-is); the tested forms were 12+ characters and were hidden.

## Not checked
Full suite, Playwright page tests, the other 218 mutant rows, the page script (JS) under a real browser, Windows behaviour, any later head than cdbe1445. Item 4 per-test diffs not read.
No commit, no push, no spend, no live call. Helpers: none left running by me. Both temp worktrees and my venvs and temp dir removed.
