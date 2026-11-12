# Evidence, Q8b batch 9, head c36ce0dc37b4c230116668505ffdafee1ef2d7bb (REDACTION path, round 9)
EVIDENCE RUNNER: results recorded, nothing judged, nothing fixed. Raw logs: /home/user/build/evidence-raw/Q8bb9-c36ce0dc/ (outside the repo). Main compared: 2a8c2aac. Previous reviewed head: 3eaae7c1. Head sha confirmed (`git rev-parse HEAD`), tree clean after every mutant run.

## What failed, differed or was not run (first)
- CI install `uv sync --locked --no-build --all-extras --group test` exits 2 here ("hadavin-sdk editable can't be installed because it is marked as --no-build"). I installed without `--no-build` (exit 0). Same as the previous round.
- Timing test `test_the_timing_harness_flags_a_quadratic_stand_in`, alone: head fail, pass, pass; main fail, fail, fail (known flake, not touched).
- Perf marker run (`pytest -m perf`, the CI step "Performance of the redaction patterns") NOT run: the brief item 9 names the timing flake only. Python 3.12 job, Windows, CodeQL, SonarCloud, CodeRabbit, semgrep, zizmor NOT run. The ticket's A1-A5 / X1-X9 rows NOT run as such (own probe only).
- Cost run: machine load average was about 5 during the cost runs (other agents), so absolute times are noisy; ratios below are from two sets of 3 runs.
- Hostile probe, cells readable on head (own probe9.py, 432 cells x redact path and channel `clean` path): 64 cells readable on at least one path; 21 of them readable on head and masked on main (list below); 0 readable on head and masked on 3eaae7c1.
- Fuzz (own; raw case list kept outside the repo in evidence-raw/Q8bb9-c36ce0dc/8-fuzz-head.txt because it holds secret-shaped made-up values; 2500 seeded cases, made-up secrets built from parts): head leaves a stretch of 12+ characters of the secret readable in 552 cases (redact path) / 390 (clean path); main 690 / 542; head-only readable cases 0; main-only readable 140. My generator also cuts keywords in places no pattern could join (`passwor d`, zero-width space inside a key, `<b></b>` inside a key), so most of the readable cases are those cuts.

## Table
| item | command | exit | last line |
|---|---|---|---|
| 1 diff list | `git diff --name-only origin/main...HEAD` | 0 | 46 files (1-difflist.txt) |
| 2a ruff | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2b format | `ruff format --check src tests demos tools` | 0 | 334 files already formatted |
| 3 bandit | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | only a nosec B102 warning at tools.py:389 |
| 4a scan | `python tools/scan_repo.py` | 0 | no output |
| 4b stage mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| 4c gitleaks | `gitleaks git --log-opts origin/main..HEAD` | 0 | no leaks found |
| 5 full pytest (own Postgres 16, heavy.sh) | `pytest -p no:cacheprovider -q -m "not live and not perf" -rs` | 0 | 10945 passed, 1 skipped, 29 deselected, 16 xfailed in 471.49s |
| 6a q8b mutants | `python tests/q8b_mutants.py` | 0 | 175 of 175 good; problems: []; 0 lines with SNIPPET NOT FOUND |
| 6b runner mutants as user nobody, from `git archive HEAD` | `python tests/mutation_runner_mutants.py` | 0 | 64 of 64 good; problems: [] |
| 6c CI steps named for Q8b in ci.yml | stage mutants and q8b mutants only (perf step not run, see above) | | |
| 7 fail-before, 6 changed or new test files copied onto 3eaae7c1 src | pytest -rA on the 6 files | 1 | 61 failed, 145 passed (same files on head: 206 passed) |
| 8 probe | probe9.py on head, 3eaae7c1, main | 0 | probe-table.md |
| 8 fuzz | fuzz9.py | 0 | 552 readable (head), 690 (main) |
| 8 cost | cost9.py | 0 | cost.md |
| 9 flake | the timing test alone, 3 x head, 3 x main | | head F P P; main F F F |

## Item 7 detail
The six files copied were test_q8b_batch9, test_q8b_batch8, test_q8b_batch8_lines, test_k5_round11, test_k5_producers, test_mutation_runner_meta (q8b_mutants.py as support). Of 33 test function names added in DELTA.patch: 58 test ids (with parametrisation) fail on old code, 47 pass on old code (43 in test_q8b_batch9.py, 4 in test_q8b_batch8_lines.py): list in 7-new-pass-on-old.txt. 3 failed ids on old code are not among the added names (in 7-failbefore-old.log). Builder's count was 61 failed, 69 passed; I collect 206 ids in the six files (parametrised ids counted), so only the failed count (61) matches.

## Item 8: cells readable on head and masked on main (cell = redact path / channel clean path)
Authorization: Token + LF or CRLF + value; ApiKey + LF or CRLF + value; Digest + LF or CRLF + value; Basic + LF + lowercase-only 20-letter value alone; Token + LF + lowercase-only 20-letter value alone; `bypass=V`, `bypass: V`, JSON `bypass`; JSON `compass_code`, `compass_key`, `overpass_key`, `encompass_key` (the text forms `compass_code=V` etc. are readable on main as well); `possession_id` and `obsession_id` in `=`, `:` and JSON forms. All of these are equally readable on 3eaae7c1. Wrapped `Authorization: Basic` + LF/CRLF/tab/FF/VT/other white-space controls + base64: masked on head in every separator I tried. wget cookie flags followed by a URL (`--no-cookies`, `--keep-session-cookies`, `--junk-session-cookies`, `--load-cookies`, `--save-cookies`, `--cookies`): readable on redact path on head, 3eaae7c1 and main alike (not a change versus main in my cells). `Digest` + LF + prose line: readable on head and main alike. `bypass_key`, `bypass_code`, `bypass-code`, `bypass_value`, `protection_bypass`, `x-vercel-protection-bypass`, `cookie2`, `Cookie2`, digit runs of 21, 22, 30, 40, 41 after pass, password, auth, session, bearer: masked on head in my cells. Full list of the 64 readable cells and the 178 cells masked on head and readable on main: probe-table.md. Other readable cells on head and main alike: `--max_tokens`, `cookiejar`/`cookiestore` lower case, `password`/`api_key` + 21 or more tail characters, 8 prefix words before `--password`, `pass\nword=V`.

## Item 8: cost, 200 kB hostile text (cost.md has all 20 shapes)
Ratios head / main: E (--a*39 pass flag) 3.47, L (cookie prefixes) 2.60, M (glued plural tokens) 2.95, S (--a-authorization) 3.04; lowest 0.92 (unclosed-quote Digest); highest absolute head time 1.20 s (F, `--a-` runs). No error on any shape. Builder CHANGELOG ratios: E 3.44, L 3.05, M 3.26.

## Controls (test_q8b_batch8_lines.py)
UNPLANTED_MAX = 28 (pin present). Of 74 control ids: 39 with a planted fault, 28 with neither a planted fault nor a reason, 7 with a stated no-fault reason (the 28 ids are listed in controls-groups.txt).

## Files in this folder
1-difflist.txt, probe-table.md, probe9.py, fuzz9.py, cost9.py, cost.md, controls-groups.txt, 7-new-pass-on-old.txt, 7-new-fail-on-old.txt. Agent hygiene: own Postgres stopped and its folder removed; own worktrees removed; no other process touched.
