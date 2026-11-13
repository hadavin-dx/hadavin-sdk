# semgrep-pr-body-v7.md: claim -> evidence (rebase check on main 61ded9e, builder, 2026-11-13; derived from v6 by the drafter)

**v7 note:** rows whose Status says CHANGED differ from v6 because main (61ded9e) differs from db54e13. Rows not named in the changed list were left as they were in v6 and keep their v6 status text (`db54e13` there means the earlier tree, not re-run). Key addition: **N** = re-run by the rebase builder on `61ded9e` + patch in /tmp/sgv, raw files /tmp/work/semgrep-main/evidence-1..10-*.txt (E1 gates, E2 tests, E3 extra tests, E4 no-demo, E5 measurements, E6 mutants, E7 stand-in, E8 docs-fix gates, E9 real Semgrep, E10 committed gitleaks; not the older E1..E7 below).

Scope: one row per sentence of `semgrep-pr-body-v6.md` that holds a number, a commit id, a hash, or a "confirms"/"passed"/"identical" word, plus the sentences changed from v5. 0 rows marked [UNVERIFIED]: every claim below is either re-measured or marked with the tree it was measured on.

Key to sources:
- **E1..E7** = `/tmp/demo-lead/handover/demo/semgrep/evidence-sg5-1..7-*.txt` (builder, on db54e13 + v5).
- **R6** = `/tmp/demo-lead/handover/demo/semgrep/REVIEW-6-v5-fresh.md` (byte-identical to `/tmp/work/rv26-report.md`; checked with `diff`), item number after the dot.
- **D** = re-run by this drafter on 2026-11-13 in a fresh scratch clone at `db54e13584d4` with the v5 patch applied (`/tmp/claude-0/-home-user/b34836a1-affe-5ae5-ba66-3c71b6499c1e/scratchpad/c6`). The command is in the row.
- **Old-*** = an older evidence file in `/tmp/demo-lead/handover/demo/semgrep/`; these results are **not re-run on db54e13**.
- **PS** = `/tmp/demo-lead/handover/demo/pr-stack/raw-pull-*.json` (GitHub API snapshot, read-only).

| # | Claim in body v6 (short) | Evidence | Status |
|---|---|---|---|
| 1 | Semgrep version 1.185.0, runs on PRs to main and pushes to main | D: patch `semgrep.yml` (`on: pull_request/push: branches: [main]`), `requirements-semgrep.txt` line 932 `semgrep==1.185.0` | measured (file content) |
| 2 | Reports only severity ERROR; not scanning tests/ and demo_only/ | D: scan command `--severity ERROR ... src scripts load_tools tools n8n` | measured (file content) |
| 3 | Intended not to be a required check | D: workflow comment "Keep it OUT of the required checks"; GitHub branch settings NOT checked (said in body) | measured (file content) |
| 4 | Adds or changes 9 files (list) | N: `git status --short` after apply on 61ded9e = the same 9 (4 A, 5 M); E5 | re-measured on 61ded9e [unchanged claim] |
| 5 | No code under `src/` changed | N: `git diff --cached --name-only | grep -c '^src/'` = 0; E5 | re-measured on 61ded9e [unchanged claim] |
| 6 | `0841f36` was the scanned commit | `lead-registry-run.txt` ("Tree: pr-3-tests at origin head 0841f36") | lead's run, not re-run |
| 7 | `61ded9e` (head of main, the squash of #2-#4) is the commit this PR is cut from; same tree as `3598120` | N: `git rev-parse 3598120^{tree}` (in /tmp/work/fc-ap) = `git rev-parse 61ded9e^{tree}` = `4aa3ea0c3ede...`; `git log -1 61ded9e` message: 'Squash of the demo code series (PR #2, #3 and #4 content, head 3598120)'. **Was: db54e13 head of pr-3-tests** | **CHANGED** re-measured |
| 8 | #2-#4 are merged into main as one squash commit `61ded9e` (so no stack, no merge order) | N: commit message of 61ded9e (above). GitHub state of PRs #2/#3/#4 and the branches NOT checked (no network); the PS snapshot is older. **Was: pr-3-tests is the head of PR #4, last of the stack** | **CHANGED**; PR states not measured |
| 9 | 61ded9e holds the sonar.yml fix, `tests/` and `tests/test_workflow_files_parse.py` | N: `git ls-tree --name-only 61ded9e` lists tests, .github; `tests/test_workflow_files_parse.py` exists; 5 tests pass (E2). **Was: db54e13 vs 2db3926 diff stat** | **CHANGED** re-measured |
| 10 | Patch sha256 `024250007740...3744dc2` (docs-fix variant, recommended) / `7c7c7269bed9...fa09076` (pure regeneration, byte-identical to v5.1 except one `index` line) | N: `sha256sum` of `semgrep-on-main-61ded9e-docsfix.patch` and `semgrep-on-main-61ded9e.patch` in /tmp/work/semgrep-main. v5.1 was `fac20b03...03aac37`. Pure patch vs v5.1: `diff <(grep -v '^index ' A) <(grep -v '^index ' B)` empty; 1 `index` line differs (docs/tests.md base blob changed on main). Docs-fix differs from pure in 2 lines (docs/tests.md line 36 text, semgrep.yml comment line 54); see row 29 | **CHANGED** re-measured |
| 11 | No GitHub run seen; no registry rules fetched for this PR | NOTES-semgrep-v5.md "NOT run"; R6 header "Not run: Semgrep with the registry packs (offline) ... a real GitHub run" | stated by builder and reviewer; nothing found that contradicts |
| 12 | Full suite not run on 61ded9e | N: not run (lead runs it); only 7+1 focused files (E2, E3) | as stated [was db54e13] |
| 13 | Lock: 67 packages in 1130 lines | N: `wc -l` = 1130; 67 `==` lines; 919 `--hash` lines; sha256 `a791abb7e447...`; E5 | re-measured on 61ded9e [unchanged claim] |
| 14 | Install check `pip check` + `semgrep --version` | D: patch step "Check the install" | measured (file content) |
| 15 | Two packs `p/python`, `p/javascript`, no others | D: scan command has exactly these two `--config` | measured (file content) |
| 16 | Findings only in the log, no code-scanning upload | D: no upload step in the 5 steps (patch read in full) | measured (file content) |
| 17 | Exit 2 retried, up to 3 tries, 20 s apart; exit 1 never retried | D: `for attempt in 1 2 3`, `RETRY_PAUSE_SECONDS: "20"`, `-ne 2 ... break`; E5 (exit 2 -> 3 tries; exit 1 -> 1 try); R6.3 | re-measured on db54e13 (stand-in program) |
| 18 | Exit 3 under `--strict` for a Python or JS syntax error | Old-sg-21-unparsable-files.txt (d1/d2: exit 3 strict, 0 without) | **not re-run on db54e13**; made-up rule |
| 19 | Exit 3 in two other made-up tests, cause not described | Old-sg-21 (d5, d6: exit 3 strict, ~100% parsed) | **not re-run on db54e13** |
| 20 | Job reports exit 3 as tool error, prints "NOT findings", 1 try | E5 (stub exit 3: rc 3, tries 1, "NOT findings"); R6.3 | re-measured on db54e13 (stand-in program) |
| 21 | Four number tests use `[[ ]]` | N: `grep -n '\[\[' .github/workflows/semgrep.yml` = lines 70, 72, 74, 76 (`-ne 2`, `-lt 3`, `-eq 1`, `-ne 0`); E5 | re-measured on 61ded9e |
| 22 | S7688 asks for `[[`; lint.yml on main now also uses `[[ ]]` | issues-pr4-0253.json (10 issues S7688); N: `git diff db54e13 61ded9e -- .github/workflows/lint.yml` changes two `[ ... ]` to `[[ ... ]]` (lines 77, 79 of lint.yml on main). Rule text not read; SonarCloud has not scanned semgrep.yml | measured (issue export, diff); rule text not read. Sentence about lint.yml is **new** |
| 23 | Behaviour unchanged by `[[ ]]`: exit, tries, messages identical, both bash forms | old-vs-new: E5/E3 and R6.3 on db54e13. On 61ded9e: only the new run block was run, 8 sequences x 2 bash forms (E7); semgrep.yml is byte-identical to the db54e13 version (non-`index` lines of the two patches identical) | old-vs-new measured on db54e13; new block only on 61ded9e (stand-in, not Semgrep) |
| 24 | n8n holds 3 JSON files | N: `git ls-files n8n` = desk-form.json, desk-webhook.json, proof.json; E5 | re-measured on 61ded9e [unchanged claim] |
| 25 | ERROR-level clean on 0841f36 of `pr-3-tests` (lead's run) | `lead-registry-run.txt` (exit 0, no output) | lead's run 2026-11-12, **not re-run on db54e13** |
| 26 | That run: image `semgrep/semgrep:1.185.0`, two packs, ERROR, five folders, exit 0 | `lead-registry-run.txt` command line | as recorded |
| 27 | Differs in three ways (no `--strict`, no `--disable-version-check`, other option order) + `--quiet` | `lead-registry-run.txt` command vs patch scan command (compared by drafter) | measured (text compare) |
| 28 | 0841f36 is an earlier commit of the branch; not in main's history | N: `git merge-base --is-ancestor 0841f36 61ded9e` = no (squash); in /tmp/work/fc-ap `0841f36` is an ancestor of `3598120`. **Was: ancestor of db54e13** | **CHANGED** re-measured |
| 29 | Since 0841f36: 25 files, 912 added, 118 removed in the scanned folders | N: `git -C /tmp/work/fc-ap diff --shortstat 0841f36 3598120 -- src scripts load_tools tools n8n` = '25 files changed, 912 insertions(+), 118 deletions(-)' (3598120 has the same tree as 61ded9e); same `git diff --name-status 0841f36 61ded9e` in /tmp/sgv-hist = 25 entries. **Was: 13 files, 405, 60 (0841f36..db54e13)**. New files among them: src/lead_desk/urls.py, tools/pathconfine.py. Also stated in docs/tests.md line 36 (docs-fix patch) | **CHANGED** re-measured; the pure patch still says 13/405/60 in docs/tests.md line 36 |
| 30 | Job log prints version and pack names at start | D: `echo "semgrep $(semgrep --version ...), packs: ..."` before the loop | measured (file content) |
| 31 | Engine LGPL-2.1; rules under Semgrep Rules License v1.0; licence text not read | D: `semgrep.yml` lines 1-3; `docs/tests.md` line 38; R6.11 | measured (file content); licence text NOT read |
| 32 | Owner's yes given for `p/python` and `p/javascript` only, this repository only | `/tmp/demo-lead/handover/demo/ORDERS.md` line 93 (memory semgrep-rules-licence-yes-2026-11-12); D: `docs/tests.md` line 38 | as recorded by the lead |
| 33 | No copy of any rule in the repository | D: `docs/tests.md` line 38 states it; no rule YAML among the 9 files | measured (file list) |
| 34 | Concurrency group `semgrep-${{ github.ref }}`, cancel only for pull_request | D: patch lines `group:` and `cancel-in-progress: ${{ github.event_name == 'pull_request' }}` | measured (file content) |
| 35 | Test `test_semgrep_workflow_never_cancels_a_push_to_main` exists | N: tests/test_nosemgrep_form.py line 180; E5 | re-measured on 61ded9e [unchanged] |
| 36 | Lock-file tools per file (pip-compile: dev; uv: dev-win, coverage, 2 browser; uv 0.13.8 Semgrep; 0.11.32 written for coverage only) | D: `head -3` of each `requirements-*.txt`; `requirements-coverage.in` line 4; `requirements-semgrep.in` line 4 | re-measured on db54e13 |
| 37 | Lock rebuilt with uv 0.13.8, `cmp` identical, sha `a791abb7e447`, 1130 lines; Python 3.13; docker not run | Old-sg-17-uv-lock-identical.txt | **not re-run on db54e13**; D: the lock on db54e13 has the same sha256 |
| 38 | Install command with `--require-hashes --only-binary=:all: --no-deps` | D: patch install step | measured (file content) |
| 39 | `pip check` confirms no package missing or in conflict | Old-sg-1-install.txt ("No broken requirements found") | design statement; result **not re-run on db54e13** |
| 40 | Two Actions pinned to full commit id; `persist-credentials: false` | D: patch `actions/checkout@3d3c42e5...`, `actions/setup-python@6d4fd22b...` | measured (file content) |
| 41 | `contents: read` only; no secret, no token, no account | D: patch `permissions:` block; no `secrets.` in semgrep.yml | measured (file content) |
| 42 | Timeout 20 minutes; install took 17 s once | D: `timeout-minutes: 20`; Old-sg-1-install.txt ("seconds: 17") | 17 s **not re-run on db54e13** |
| 43 | Suppression test refuses case, extra letters, long s | N: lines 21 and 127 of tests/test_nosemgrep_form.py (comment text hit); old Semgrep evidence not re-run | test file re-measured; Semgrep behaviour not re-run |
| 44 | Lock test runs real gitleaks; second part widens on purpose | N: `def test_semgrep_lock_allowances_are_narrow` line 101, `def test_widening_an_allowance_makes_the_negative_cases_pass` line 120; 3 passed with gitleaks 8.30.1 (E2) | re-measured on 61ded9e |
| 45 | `.gitleaks.toml` / `exceptions.txt` exceptions | N: exceptions.txt lines 32-34 (checked); .gitleaks.toml lines 56 and 102 | re-measured on 61ded9e [unchanged] |
| 46 | CodeAnt skips the lock file | N: .codeant/configuration.json line 20 = `"requirements-semgrep.txt",` | re-measured on 61ded9e [unchanged] |
| 47 | Hash-line exception only for `^requirements-semgrep\.txt$` | N: .gitleaks.toml line 102 | re-measured on 61ded9e [unchanged] |
| 48 | Tightened from an earlier looser pattern | Old-sg-14 ("left anchor removed (the old r2 regex)") | as recorded |
| 49 | 67 packages not checked by CodeAnt / Dependabot | D: `.github/dependabot.yml` = github-actions only; row 13 | measured |
| 50 | Lock fits Linux x86_64 and Python 3.12 only | D: `requirements-semgrep.in` line 4 (`--python-platform x86_64-manylinux_2_34 --python-version 3.12`) | measured |
| 51 | No repo test checks the retry/exit logic | R6 Nit 2 and R6.12 | reviewer finding |
| 52 | Focused tests 139 passed = 24 + 63 + 3 + 44 + 5 (also flags 10 and shell-bracket 146: 295 in 7 files) | N: E2 `295 passed in 85.06s` for 7 files; `--co` counts per file: hygiene 24, nosemgrep 63, lock 3, exceptions 44, files_parse 5, run_flags 10, shell_single_bracket 146. With test_codeant_hygiene (7): 302 on the docs-fix tree (E8). **Was: 130 = 15 + 63 + 3 + 44 + 5 (hygiene grew from 15 to 24 on main)** | **CHANGED** re-measured |
| 53 | Real gitleaks 8.30.1 and DPLD_REQUIRE_SCAN=1 | N: both set in the command (E2 header line is written by me, the test output does not show them) | as stated |
| 54 | Workflow mutants: cancel-in-progress true -> 1 failed, 62 passed; constant group -> 1 failed, 62 passed | N: E6 on 61ded9e (baseline 63 passed; each mutant 1 failed, 62 passed; restored 63 passed) | re-measured on 61ded9e [was not re-run] |
| 55 | 4 gitleaks-exception mutants, each made the lock test fail | Old-sg-14-gitleaks-allowance-tests-and-mutants.txt | **not re-run on db54e13** (earlier version) |
| 56 | 24 comment shapes; old test missed 23, new refuses 24 | Old-sg-13b-test-old-vs-new-nosem.txt (D: `grep -c` 24 shape rows, 23 MISSED) | **not re-run on db54e13** (earlier version) |
| 57 | `git apply --check` on 61ded9e: OK | N: both patches, in /tmp/sgmain (clean 61ded9e) | re-measured on 61ded9e |
| 58 | gitleaks: no leaks in files and history | N: E10: scratch commit of the docs-fix tree, fresh clone: `gitleaks dir` and `gitleaks git` no leaks; hygiene+lock+exceptions tests 71 passed with DPLD_REQUIRE_SCAN=1. (A first test run failed only because of extra refs I fetched into the test clone; see E2 header) | re-measured on 61ded9e |
| 59 | ruff clean; mypy Linux and Windows 28 source files | N: E1 `All checks passed!`, `158 files already formatted`, mypy `no issues found in 28 source files` x2. **Was: 26 source files (urls.py and pathconfine.py are new on main)** | **CHANGED** re-measured |
| 60 | bandit `-ll` exit 0 | N: E1 (lint.yml form `src tools scripts` and the `+ load_tools` form: rc 0) | re-measured on 61ded9e |
| 61 | Stand-in: 0, 1, 2, 3, 7, 2-0, 2-2-0, 2-2-2, 2-1 identical; exit 2 -> 3 tries; exit 3 -> 1 try | N: E7 (8 sequences x 2 bash forms on the new block: 0, 1, 2-0, 2-2-0, 2-2-2, 2-1, 3, 7; scan calls 1,1,2,3,3,2,1,1). R6.3 for old-vs-new | new block re-measured on 61ded9e; old-vs-new on db54e13 |
| 62 | Real Semgrep exit codes 0, 1, 2, 7 on a made-up rule | Old-sg-6-exit-codes-local.txt | **not re-run on db54e13**; not with the registry packs |
| 63 | Syntax-error files: exit 3 strict, 0 without; 2 more folders exit 3; finding -> exit 1 both ways | Old-sg-21-unparsable-files.txt (summary line) | **not re-run on db54e13** |
| 64 | Real scanned folders: 47 files, ~100% parsed, exit 0 with and without `--strict` (made-up rule, 61ded9e) | N: E9 (semgrep 1.185.0, /tmp/work/sg21/rule.yml, `Targets scanned: 47`, `Parsed lines: ~100.0%`, exit 0 both). **Was: 45 files on 2db3926** | **CHANGED** re-measured (made-up rule, not the registry packs) |
| 65 | Five folders: 47 `.py`/`.js` tracked files on 61ded9e; NOT identical to db54e13 (16 files differ: 511 added, 62 removed) | N: `git ls-files src scripts load_tools tools n8n | grep -E '\.(py|js)$' | wc -l` = 47 (30 src, 9 scripts, 4 load_tools, 4 tools); `git diff --shortstat db54e13 61ded9e -- src scripts load_tools tools n8n` = '16 files changed, 511 insertions(+), 62 deletions(-)'. **Was: 'identical on db54e13', 45 files** | **CHANGED**: the old claim is false on main |
| 66 | Full suite on 0841f36: 2426 passed, 115 skipped | Old-sg-10-full-pytest.txt | earlier version, not re-run |
| 67 | Python 3.13 only for the lock rebuild | Old-sg-17 ("Python host 3.13.18") | as recorded |
| 68 | `--verbose` shows "Syntax error" warning with the file name | Old-sg-21 last command (`[WARN] Syntax error at line d1/broken.py:2`) | **not re-run on db54e13** |
| 69 | `tests/` IS on main now (61ded9e has `tests`) | N: `git ls-tree --name-only 61ded9e` lists `tests`; `git ls-tree origin/main` in the /tmp/sgv clone shows an old ref (no tests): do not use it. **Was: 'tests/ not on main yet'** | **CHANGED**: the old claim is false |
| 70 | Exception needs the `cwd=target` change in `tests/test_hygiene.py` (line 200 on 61ded9e) | N: `grep -n 'cwd=target' tests/test_hygiene.py` = line 200. **Was: line 194 on db54e13** | **CHANGED** (line number) |
| 71 | Missing folder -> Semgrep exit 2 | Old-sg-6 (`no_such_folder` -> exit 2) | **not re-run on db54e13** |
| 72 | Patch applies to clean main and touches only the 9 files | N: `git apply --check` OK both patches; `grep '^diff --git'` = the 9 paths; `git apply --stat` 1583 insertions, 1 deletion | re-measured on 61ded9e (**new row**) |
| 73 | Pure regeneration equals v5.1 except one `index` line | N: `diff` of non-`index` lines empty; sizes both 124316 bytes | measured (**new row**) |
| 74 | Semgrep workflow comment 'Same house rules as lint.yml' (full-SHA pins, read-only permissions, hosted runner, installs checked by hash) still true of lint.yml on main | N: lint.yml lines 13-14 (`contents: read`), 18 (`ubuntu-24.04`), 26 and 31 (same two SHAs as semgrep.yml), 52 (`--require-hashes`) | re-measured on 61ded9e (**new row**) |
| 75 | Body says gitleaks secret scan stays in lint.yml | N: lint.yml lines 47-48 run `gitleaks dir` and `gitleaks git` | re-measured on 61ded9e (**new row**) |
| 76 | In a no-demo copy the semgrep tests are skipped, not run | N: E4: `tests/conftest.py` skips 6 whole files (`import support` needs demo_only); 15 passed, 6 skipped; ruff, mypy, bandit clean | measured (**new row**; same design as main, not caused by the patch) |

## Discrepancies found while measuring (not fixed in the patch; the drafter does not edit patches)

- v5 body said "`pip-compile` made the development locks, `uv` 0.11.32 made the coverage lock and the two browser locks". Measured: `requirements-dev-win.txt` was made by `uv` (its header), and the browser lock headers do not record a uv version. v6 says only what the headers show. **The same wrong sentence is in the patch**: `docs/tests.md` line 48 ("`pip-compile` (the dev locks ...)" and "`uv` 0.11.32 (`requirements-coverage.txt` and the two browser locks ...)"). The lead should fix that in a v6 patch, or confirm the browser locks' uv version from somewhere I did not find.
- R6 item 1 says "exactly 7 changed lines" between v4 and v5. My diff of added/removed lines (`diff <(grep -E '^[+-][^+-]' v4) <(grep -E '^[+-][^+-]' v5)`) shows 6 changed line pairs: the 4 tests, the semgrep.yml "Status:" comment, the docs/tests.md "Status of the scan" paragraph. The content matches R6's own list (which also names 6 items). v6 does not state a count.
