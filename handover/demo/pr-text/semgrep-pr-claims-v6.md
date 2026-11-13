# semgrep-pr-body-v6.md: claim -> evidence (drafter, 2026-11-13)

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
| 4 | Adds or changes 9 files (list) | E2 (`git status` lists 9); D: `git apply` + `git status --short` = the same 9 | re-measured on db54e13 |
| 5 | No code under `src/` changed | D: the 9 files above, none under `src/` | re-measured on db54e13 |
| 6 | `0841f36` was the scanned commit | `lead-registry-run.txt` ("Tree: pr-3-tests at origin head 0841f36") | lead's run, not re-run |
| 7 | `db54e13` is the commit this PR is cut from: head of branch `pr-3-tests` | D: `git rev-parse origin/pr-3-tests` = `db54e13584d4...` in the reviewer's clone; R6.2 | re-measured |
| 8 | `pr-3-tests` is the head of PR #4, last of #2 to #4 | PS: #2 pr-1-code -> main, #3 pr-2-demo-folder -> pr-1-code, #4 pr-3-tests -> pr-2-demo-folder (snapshot showed head 2db3926 then) | measured (snapshot) |
| 9 | db54e13 already holds the sonar.yml fix and `tests/test_workflow_files_parse.py` | D: `git diff --stat 2db3926 db54e13` = sonar.yml, tests/test_workflow_files_parse.py, versions.md; R6.5 | re-measured |
| 10 | Patch sha256 `fac20b03...03aac37` | `sha256sum semgrep-on-db54e13-v5.1.patch` (v5 was 99c185b0...22b7c5; v5.1 rewrites one docs sentence about which tool made the locks) | re-measured |
| 11 | No GitHub run seen; no registry rules fetched for this PR | NOTES-semgrep-v5.md "NOT run"; R6 header "Not run: Semgrep with the registry packs (offline) ... a real GitHub run" | stated by builder and reviewer; nothing found that contradicts |
| 12 | Full suite not run on db54e13 | NOTES-semgrep-v5.md; R6 "Not checked: ... full suite" | as stated |
| 13 | Lock: 67 packages in 1130 lines | D: `wc -l` = 1130; `grep -cE '^[A-Za-z0-9_.-]+=='` = 67; E6; R6.2 | re-measured on db54e13 |
| 14 | Install check `pip check` + `semgrep --version` | D: patch step "Check the install" | measured (file content) |
| 15 | Two packs `p/python`, `p/javascript`, no others | D: scan command has exactly these two `--config` | measured (file content) |
| 16 | Findings only in the log, no code-scanning upload | D: no upload step in the 5 steps (patch read in full) | measured (file content) |
| 17 | Exit 2 retried, up to 3 tries, 20 s apart; exit 1 never retried | D: `for attempt in 1 2 3`, `RETRY_PAUSE_SECONDS: "20"`, `-ne 2 ... break`; E5 (exit 2 -> 3 tries; exit 1 -> 1 try); R6.3 | re-measured on db54e13 (stand-in program) |
| 18 | Exit 3 under `--strict` for a Python or JS syntax error | Old-sg-21-unparsable-files.txt (d1/d2: exit 3 strict, 0 without) | **not re-run on db54e13**; made-up rule |
| 19 | Exit 3 in two other made-up tests, cause not described | Old-sg-21 (d5, d6: exit 3 strict, ~100% parsed) | **not re-run on db54e13** |
| 20 | Job reports exit 3 as tool error, prints "NOT findings", 1 try | E5 (stub exit 3: rc 3, tries 1, "NOT findings"); R6.3 | re-measured on db54e13 (stand-in program) |
| 21 | Four number tests use `[[ ]]` | D: v4 vs v5 diff of added lines: the 4 `if [ ... ]` -> `if [[ ... ]]` (`-ne 2`, `-lt 3`, `-eq 1`, `-ne 0`); R6.1 | re-measured |
| 22 | S7688 asks for `[[` ("Use '[[' instead of '['") | `/tmp/demo-lead/handover/demo/sonar/issues-pr4-0253.json`: 10 issues `shell:S7688` with that message (on scripts/reset.sh, scripts/start_all.sh). The rule text itself was not read (sonar NOTES-p1-quickwins-v3.md line 7); SonarCloud has not scanned semgrep.yml v5 | measured (issue export), rule text not read |
| 23 | Behaviour unchanged: exit, tries, messages identical, both bash forms | E5 (6 sequences x 2 shells); R6.3 (9 sequences x 2 shells = 18 pairs, all identical); tripwire E3 (v4 fails, v5 107 passed) | re-measured on db54e13 (stand-in, not Semgrep) |
| 24 | n8n holds 3 JSON files | D: `git ls-files n8n` = desk-form.json, desk-webhook.json, proof.json | re-measured on db54e13 |
| 25 | ERROR-level clean on 0841f36 of `pr-3-tests` (lead's run) | `lead-registry-run.txt` (exit 0, no output) | lead's run 2026-11-12, **not re-run on db54e13** |
| 26 | That run: image `semgrep/semgrep:1.185.0`, two packs, ERROR, five folders, exit 0 | `lead-registry-run.txt` command line | as recorded |
| 27 | Differs in three ways (no `--strict`, no `--disable-version-check`, other option order) + `--quiet` | `lead-registry-run.txt` command vs patch scan command (compared by drafter) | measured (text compare) |
| 28 | 0841f36 is an earlier commit of the branch | D: `git merge-base --is-ancestor 0841f36 db54e13` -> yes; R6.5 | re-measured |
| 29 | Since 0841f36: 13 files, 405 added, 60 removed in the scanned folders | D: `git diff --shortstat 0841f36 db54e13 -- src scripts load_tools tools n8n` = "13 files changed, 405 insertions(+), 60 deletions(-)"; R6.5 | re-measured on db54e13 |
| 30 | Job log prints version and pack names at start | D: `echo "semgrep $(semgrep --version ...), packs: ..."` before the loop | measured (file content) |
| 31 | Engine LGPL-2.1; rules under Semgrep Rules License v1.0; licence text not read | D: `semgrep.yml` lines 1-3; `docs/tests.md` line 38; R6.11 | measured (file content); licence text NOT read |
| 32 | Owner's yes given for `p/python` and `p/javascript` only, this repository only | `/tmp/demo-lead/handover/demo/ORDERS.md` line 93 (memory semgrep-rules-licence-yes-2026-11-12); D: `docs/tests.md` line 38 | as recorded by the lead |
| 33 | No copy of any rule in the repository | D: `docs/tests.md` line 38 states it; no rule YAML among the 9 files | measured (file list) |
| 34 | Concurrency group `semgrep-${{ github.ref }}`, cancel only for pull_request | D: patch lines `group:` and `cancel-in-progress: ${{ github.event_name == 'pull_request' }}` | measured (file content) |
| 35 | Test `test_semgrep_workflow_never_cancels_a_push_to_main` exists | D: `tests/test_nosemgrep_form.py` line 180 | measured |
| 36 | Lock-file tools per file (pip-compile: dev; uv: dev-win, coverage, 2 browser; uv 0.13.8 Semgrep; 0.11.32 written for coverage only) | D: `head -3` of each `requirements-*.txt`; `requirements-coverage.in` line 4; `requirements-semgrep.in` line 4 | re-measured on db54e13 |
| 37 | Lock rebuilt with uv 0.13.8, `cmp` identical, sha `a791abb7e447`, 1130 lines; Python 3.13; docker not run | Old-sg-17-uv-lock-identical.txt | **not re-run on db54e13**; D: the lock on db54e13 has the same sha256 |
| 38 | Install command with `--require-hashes --only-binary=:all: --no-deps` | D: patch install step | measured (file content) |
| 39 | `pip check` confirms no package missing or in conflict | Old-sg-1-install.txt ("No broken requirements found") | design statement; result **not re-run on db54e13** |
| 40 | Two Actions pinned to full commit id; `persist-credentials: false` | D: patch `actions/checkout@3d3c42e5...`, `actions/setup-python@6d4fd22b...` | measured (file content) |
| 41 | `contents: read` only; no secret, no token, no account | D: patch `permissions:` block; no `secrets.` in semgrep.yml | measured (file content) |
| 42 | Timeout 20 minutes; install took 17 s once | D: `timeout-minutes: 20`; Old-sg-1-install.txt ("seconds: 17") | 17 s **not re-run on db54e13** |
| 43 | Suppression test refuses case, extra letters, long s `ſ` | D: `tests/test_nosemgrep_form.py` lines 21, 127; Old-sg-13-nosem-short-form-real-semgrep.txt; Old-sg-17-nosem-tab-unicode.txt | test file measured; Semgrep behaviour **not re-run on db54e13** |
| 44 | Lock test runs real gitleaks; second part widens on purpose | D: `tests/test_gitleaks_semgrep_lock.py` lines 101, 120; E2 (3 passed with gitleaks 8.30.1) | re-measured on db54e13 |
| 45 | `.gitleaks.toml` / `exceptions.txt` exceptions for hash lines and `requirements-semgrep.in` | D: `git diff .gitleaks.toml`; `exceptions.txt` lines 32-34 | measured |
| 46 | CodeAnt skips the lock file | D: `.codeant/configuration.json` line 20 | measured |
| 47 | Hash-line exception only for `^requirements-semgrep\.txt$` | D: `.gitleaks.toml` line 102 | measured |
| 48 | Tightened from an earlier looser pattern | Old-sg-14 ("left anchor removed (the old r2 regex)") | as recorded |
| 49 | 67 packages not checked by CodeAnt / Dependabot | D: `.github/dependabot.yml` = github-actions only; row 13 | measured |
| 50 | Lock fits Linux x86_64 and Python 3.12 only | D: `requirements-semgrep.in` line 4 (`--python-platform x86_64-manylinux_2_34 --python-version 3.12`) | measured |
| 51 | No repo test checks the retry/exit logic | R6 Nit 2 and R6.12 | reviewer finding |
| 52 | Focused tests 130 passed = 15 + 63 + 3 + 44 + 5 | E2 (per-file counts); R6.6 (130 passed, 107 s) | re-measured on db54e13 |
| 53 | Real gitleaks 8.30.1 and DPLD_REQUIRE_SCAN=1; only a header line shows it | E2 header line; R6.6 | as stated (header is not command output) |
| 54 | Workflow mutants: cancel-in-progress true -> 1 failed, 62 passed; constant group -> 1 failed, 62 passed | Old-sg-19-gates-on-2db3926.txt (cancel); Old-sg-19-v2-gates.txt (cancel and group); D: v4 vs v5 diff shows the concurrency lines unchanged | **not re-run on db54e13** |
| 55 | 4 gitleaks-exception mutants, each made the lock test fail | Old-sg-14-gitleaks-allowance-tests-and-mutants.txt | **not re-run on db54e13** (earlier version) |
| 56 | 24 comment shapes; old test missed 23, new refuses 24 | Old-sg-13b-test-old-vs-new-nosem.txt (D: `grep -c` 24 shape rows, 23 MISSED) | **not re-run on db54e13** (earlier version) |
| 57 | `git apply --check` on db54e13: OK | D: `git apply --check` -> OK; R6.2; E7 | re-measured |
| 58 | gitleaks: no leaks in files and history | E2 (`git`: 24 commits, no leaks; `dir` on clean clone: no leaks); R6.10 | re-measured on db54e13 |
| 59 | ruff clean; mypy Linux and Windows 26 source files | E1; R6.10 | re-measured on db54e13 |
| 60 | bandit `-ll` exit 0 | E1; R6.10 | re-measured on db54e13 |
| 61 | Stand-in: 0, 1, 2, 3, 7, 2-0, 2-2-0, 2-2-2, 2-1 identical; exit 2 -> 3 tries; exit 3 -> 1 try | R6.3 (9 sequences); E5 (6 of them) | re-measured on db54e13 |
| 62 | Real Semgrep exit codes 0, 1, 2, 7 on a made-up rule | Old-sg-6-exit-codes-local.txt | **not re-run on db54e13**; not with the registry packs |
| 63 | Syntax-error files: exit 3 strict, 0 without; 2 more folders exit 3; finding -> exit 1 both ways | Old-sg-21-unparsable-files.txt (summary line) | **not re-run on db54e13** |
| 64 | Real folders of 2db3926: 45 files, ~100% parsed, exit 0 with and without `--strict` | Old-sg-22-real-folders-strict-2db3926.txt | on 2db3926 only |
| 65 | Five folders identical on db54e13 | D: `git diff --stat 2db3926 db54e13 -- src scripts load_tools tools n8n` = empty; D: 45 `.py`/`.js` tracked files in those folders on db54e13; R6.5 | re-measured |
| 66 | Full suite on 0841f36: 2426 passed, 115 skipped | Old-sg-10-full-pytest.txt | earlier version, not re-run |
| 67 | Python 3.13 only for the lock rebuild | Old-sg-17 ("Python host 3.13.18") | as recorded |
| 68 | `--verbose` shows "Syntax error" warning with the file name | Old-sg-21 last command (`[WARN] Syntax error at line d1/broken.py:2`) | **not re-run on db54e13** |
| 69 | `tests/` not on main yet | D: `git ls-tree --name-only origin/main` in the reviewer's clone has no `tests` (ref as of that clone's last fetch) | measured (local ref) |
| 70 | Exception needs the `cwd=target` change in `tests/test_hygiene.py` | D: `.gitleaks.toml` comment; `tests/test_hygiene.py` line 194 (`cwd=target`) on db54e13 | measured |
| 71 | Missing folder -> Semgrep exit 2 | Old-sg-6 (`no_such_folder` -> exit 2) | **not re-run on db54e13** |

## Discrepancies found while measuring (not fixed in the patch; the drafter does not edit patches)

- v5 body said "`pip-compile` made the development locks, `uv` 0.11.32 made the coverage lock and the two browser locks". Measured: `requirements-dev-win.txt` was made by `uv` (its header), and the browser lock headers do not record a uv version. v6 says only what the headers show. **The same wrong sentence is in the patch**: `docs/tests.md` line 48 ("`pip-compile` (the dev locks ...)" and "`uv` 0.11.32 (`requirements-coverage.txt` and the two browser locks ...)"). The lead should fix that in a v6 patch, or confirm the browser locks' uv version from somewhere I did not find.
- R6 item 1 says "exactly 7 changed lines" between v4 and v5. My diff of added/removed lines (`diff <(grep -E '^[+-][^+-]' v4) <(grep -E '^[+-][^+-]' v5)`) shows 6 changed line pairs: the 4 tests, the semgrep.yml "Status:" comment, the docs/tests.md "Status of the scan" paragraph. The content matches R6's own list (which also names 6 items). v6 does not state a count.
