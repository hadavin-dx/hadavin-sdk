# Package ticket P0c (TEXT ONLY: the lead executes it on the laptop; the cloud session runs nothing from it)

Drafted 2026-11-05 (UTC; IST = UTC+5:30) by the cloud session on core `ce70eb5` plus `handover/`. Tier B (order 6(b)): one fresh reviewer, one round, at most 2 fix batches. Applies plan-v3 section 6 row P0c and note 2, section 2 (S0 exit), section 10, section 11, amendments A3, A8, A9 (F3, F4), A13, A14, memo-5 and `handover/studio-notes/s0-merge-probe.md`. R-numbers: the bible (`handover/bible/RULES.md`, grep for heavy slot, first client, merge probe, conflict) has no rule on this subject; I cite none. Studio rules used: 4 (no spend), 5 (fix, do not defer), 6 (honesty), 8 (tooling), 14 (wording), 17 (speed), 19 (hygiene).
"UNVERIFIED" = I did not read it or could not run it here. "PENDING LEAD" = a position only the lead can confirm (list at the end).

What I checked in the cloud (read-only, for this ticket): both helper scripts below were run once on this clone (`s0_measure.py` against `ce70eb5` with the refs in the table; `suite_diff.py` on a made-up two-line file); `git merge-tree --write-tree` conflict counts for #41 (10), #43 (4), #47 (0), #48 (15), #49 (4), #50 pushed and local (0), c1a (4) equal the lead's probe in `s0-merge-probe.md`; the merge-result worktree recipe (`merge-tree`, `commit-tree`, `worktree add --detach`) works and its worktree was removed again. The test suite was NOT run (order 4).

## Template fields (17, in template order)

- **Package id and name:** P0c, measure every branch and pull request against `ce70eb5` and write `handover/s0-report.md` (the "S0 report"): per row a verdict, the slot count, the first measured counts, the overlap table, and the answer to "is refunds the first client".
- **Path class:** other (read-only measurement; no code, no setting changes). Extended review (no round cap): no.
- **Depends on (merged first):** none (plan-v3 row). Used by: P0d, P0e, P0b (they read the S0 report); P0b re-runs its conflict and test columns after the Dependabot merges. The S0 exit also needs P0a, P0d, P0e, P0b finished (plan-v3 note 2); this ticket covers P0c only.
- **Problem in plain words:** Many unmerged branches hold work the core needs, and nobody has yet measured, on one fixed base, how badly each one clashes with the current main (`ce70eb5`) and whether its tests pass there. Without that, the lead cannot decide which branch to merge, rebuild, split or retire, and cannot tell how many review rounds and machine slots the plan needs. P0c produces one report that answers this with commands and raw output, not with the earlier probe's numbers (note 2: "the merge probe is re-run, not trusted"). It also records two answers only the lead and the owner can give: how many heavy test jobs the laptop can run at once, and whether the refunds project is the first paying client.
- **Source of the code (MANIFEST ids, source repo, commit sha) and what is NOT taken:** no code is promoted. The two helper scripts below are new, are kept in the studio folder (not in any repo), and are the only code this ticket introduces. NOT taken: any change to a branch, a pull request, `main`, a setting or a tag.
- **Target module and path in `src/hadavin_sdk/`:** none. Outputs: `handover/s0-report.md` (pushed to branch `core/cloud-handover` by the lead; PENDING LEAD, location) and masked evidence files `handover/evidence/P0c-<n>.md`. Raw logs stay in the studio folder `<studio>/egm/s0/raw/` and are never committed (they contain laptop paths).
- **Interface (names, argument and return types, errors):** commands and files only.
  - `s0_measure.py <repo> <base> <out.json> NAME=REF ...` prints one line per row (changed files, conflict files, exit code) and writes JSON with, per row: head sha, merge base, commits ahead and behind, changed files, conflict files, and a pairwise table of shared files. A ref that does not exist prints `ref not found`; the row is then UNMEASURED and is never guessed. Exit status: always 0; the lead reads the lines.
  - `suite_diff.py <baseline.xml> <run.xml>` prints counts, then one line per failing test marked `NEW_FAILURE` (not failing at the base) or `SAME_AS_BASELINE`, `FIXED_VS_BASELINE`, and one line per skipped test marked `DB_SKIP` (reason mentions the database) or `skip`.
  - Error rule for the whole ticket: any command that cannot run or any missing measurement is written into the report as UNMEASURED with the reason. An unmeasured cell never counts as a pass.
- **Neutral default / working alternative (or written outline with trigger):** git and Python are the only tools; the database is a throwaway container (the same pinned image CI uses). Alternative if Docker is unavailable on the laptop: a locally installed Postgres 17 started by the lead on a throwaway data directory with made-up data only; same environment variable. No vendor service is involved.
- **Files to create, change, delete (each with the reason):** create `handover/s0-report.md` (the deliverable); create `handover/evidence/P0c-1.md` to `P0c-6.md` (masked command and output summaries, below); create `<studio>/egm/s0/measure/s0_measure.py` and `suite_diff.py` (scripts); no other file is changed or deleted. Existing test failures are listed in the report, never fixed here (fixing is a package's job, and each one gets a row in the report's "failures already on ce70eb5" table).
- **Existing core code reused (what I checked):** the CI recipe in `.github/workflows/ci.yml` (lines 77-94: `uv sync --locked --no-build --all-extras --group test`, then `pytest -q -m "not live and not perf" -rs`, then `pytest -q -m perf -rs` as its own step; Postgres 17.10 service, DSN variable `HADAVIN_TEST_PG_DSN`, Vault dev server variable `HADAVIN_TEST_VAULT_ADDR`); `pyproject.toml` (`requires-python >=3.12`; markers `live` and `perf`; the `test` group); `s0-merge-probe.md` (the earlier probe, used only to cross-check); memo-5 section 1 (measured branch-pair overlaps, cross-check). Not reused: any `tests/` file (nothing is edited).
- **Security and least-privilege notes (identity, rights, secrets, personal data, dev-only flag):** read-only on every branch: the commands use `git merge-tree`, `git diff`, `git rev-list`, `git worktree add --detach` into a scratch folder, and `git commit-tree` for a local, unreferenced probe commit (never pushed, never given a branch name). Never `git fetch --prune` (it would delete remote-tracking refs, including the `handover-src/*` backups); plain `git fetch origin` only. No secrets: before every suite run check that the environment holds no cloud settings (`env | grep -E 'AWS|ANTHROPIC|GOOGLE|AZURE|OPENAI|VAULT_|HADAVIN'` shows only the two test variables, `HADAVIN_TEST_PG_DSN` and `HADAVIN_TEST_VAULT_ADDR`). The database container is a throwaway with trust login and made-up data; the Vault dev root token `root` is the dev-server convention, not a secret (as in `ci.yml:53-60`). No model call, no paid service. Personal data: none; the committed evidence files replace laptop user names and paths with `<studio>` and `<scratch>`. Least privilege: the lead's own laptop identity; the cloud token is not used for measurement.
- **Tests (unit; the FAIL-BEFORE test; hostile inputs; race/process tests; contract suite):** P0c writes no tests. Instead each measurement carries a check that it can fail:
  1. Probe check (the "fail-before" of this ticket): run `s0_measure.py` on a row known to conflict (`#48`, expected 15 conflict files from the lead's probe) and on one known clean (`#47`, expected 0); if either differs from the earlier probe, stop and find out why before going on (git version, stale refs, wrong base).
  2. Suite check: run the baseline suite twice on `ce70eb5`; the failure sets must be equal. If they differ, the failing tests are flaky: list them as FLAKY and never count them as new failures.
  3. Planted failure check: in a scratch copy only, run `pytest -q tests/contracts` after pointing `HADAVIN_TEST_PG_DSN` at an unused port; `suite_diff.py` must print `DB_SKIP` or a failure, proving that a missing database is visible and not silently green.
  4. Hostile input: a ref name that does not exist (`c18a` in the cloud clone) must give `ref not found`, never a verdict.
- **Mutation plan:** not applicable (no code under test). The three checks above stand in for it.
- **Evidence commands (exact), and where the raw output is saved:** see "Procedure" below. Raw output: `<studio>/egm/s0/raw/`; masked summaries: `handover/evidence/P0c-<n>.md`.
  - P0c-1: environment, tool versions, refs and heads at measurement time.
  - P0c-2: merge probe output (all rows) and the cross-check against `s0-merge-probe.md`.
  - P0c-3: baseline suite on `ce70eb5` (two runs, 3.12 and 3.13) and the baseline failure list.
  - P0c-4: suite results per row.
  - P0c-5: overlap table and slot count.
  - P0c-6: the refunds answer and the first counts.
- **Reviewers:** one fresh reviewer (Sonnet 5.5), one round, at most 2 fix batches (order 6(b)). The reviewer gets this ticket and the evidence files only, never the lead's verdict. EVIDENCE RUNNER wording applies to whoever executes: the executor runs and records and does not judge; the lead decides verdicts and writes the reasons.
- **Done =** the report exists with every table below filled (no empty cell; UNMEASURED is allowed only with its reason and the next step), evidence files P0c-1 to P0c-6 exist, the pass criteria below hold, and the reviewer's round has no blocker or major. Gates for a documents-only change: `ruff check`, `ruff format --check` and the repo guard tests pass on the handover branch (these files are not Python, so only the banned-name scan and the secret scan can fail: run them).
- **Rollback:** read-only measurement, so nothing needs rolling back and no `pre-P0c` tag is needed. Clean-up only: (a) remove the scratch worktrees with `git worktree remove --force <dir>` (never `git worktree prune` without the dry run `git worktree prune -n -v` first, as the studio rule of 2026-11-03 says); (b) stop and remove the two containers the lead started (`docker rm -f s0-pg s0-vault`; never touch other containers); (c) the unreferenced probe commits and tree objects fall away at the next `git gc`; (d) delete nothing else. Non-revertible changes: none. Loud-failure test: not applicable.

## What is measured (rows of the report)

Heads are read at the moment of measurement with `git fetch origin` first (the cloud clone's local copies of the Dependabot branches were older than GitHub's heads when I looked, so stale refs are a real risk). Live state read through the GitHub tool at drafting time: open pull requests are #41 (head 06a75b0), #43 (fa12aeb), #47 (03755d1), #48 (8986cb5), #49 (draft, cd62212), #50 (2e8a28c), #53 moto (1311d75), #54 sqlglot (955f94f), #55 boto3 (08c3a50). The plan says Dependabot #51-#56; only #53-#55 are open: whether #51, #52, #56 were merged or closed is UNVERIFIED (check with `gh pr list --state all --limit 20`).

| Row | Ref to measure | Head known at drafting | Note |
|---|---|---|---|
| #41 K6 | `origin/k6` | 06a75b0 | merge base 308558a, not ce70eb5 |
| #43 ask-your-data gaps | `origin/demo-gaps` | fa12aeb | base 6608146 |
| #47 ask-your-data export | `origin/demo-askdata-export` | 03755d1 | base 6608146 |
| #48 hardening | `origin/core-hardening-1` | 8986cb5 | base 6608146 |
| #49 refunds promotion (draft) | `origin/core/promote-refunds-r8` | cd62212 | base 6608146 |
| #50 pushed | `origin/core/promote-apexc-review8` | 2e8a28c | base ce70eb5 |
| #50 local | `origin/handover-src/pr50-local-748849c` | 748849c | backup branch of the unpushed head; differs from pushed by `audit/labelkey.py`, `errors.py` and 3 `test_pr50_fix_batch*.py` (memo-5) |
| c1a | `origin/handover-src/c1a-8460813` | 8460813 | backup branch of the C1a head |
| c18a (old diagnostics design) | the lead gives the ref | 198a6b6 (from the probe) | NOT a ref in the cloud clone (`git cat-file -t 198a6b6` fails there): UNMEASURED in the cloud; the lead measures it on the laptop |
| other `handover-src/*` | `git branch -r --list 'origin/handover-src/*'` | two exist (the #50 local and c1a rows above) | add one row for any further branch; do not double count |
| Dependabot #53, #54, #55 | their `dependabot/uv/*` heads | see above | verdict is P0b's (rule 12); P0c measures conflicts and suite only |
| baseline | `ce70eb5` | ce70eb5 (= `origin/main` at drafting) | the reference for "failures already present" |

Also record for context (not rows): `origin/core/cloud-handover` (this handover; check `git diff --stat ce70eb5 origin/core/cloud-handover -- . ':!handover'` is empty, so it changes nothing outside `handover/`: UNVERIFIED) and `origin/claude/wizardly-allen-5k7qre` (equals ce70eb5 at drafting).

## Procedure (the lead runs these on the laptop; bash shown, PowerShell equivalents are the lead's choice; Python scripts are run with `python -I` from a folder other than the data they read)

Heavy jobs (full suites) go only through `python tools\heavy_slot.py ...` (studio rule 2026-11-03; exact flags UNVERIFIED here because that tool is in the studio root, not in this repo) and, if a run may exceed 25 minutes, are started detached and followed by log, because background tasks are stopped at about 30 minutes (studio rule "long jobs run detached"). Never run two suites on one worktree, never run evidence on a worktree anyone is editing.

Step 0, set up (write `<scratch>` = a new empty folder; `<core>` = the core repo clone on the laptop):
```
git -C <core> fetch origin                      # no --prune
git -C <core> rev-parse ce70eb5 origin/main     # both must print ce70eb5...; if main moved, STOP and tell the lead (the base is fixed by the plan)
git -C <core> --version ; uv --version ; python --version ; uv python list --only-installed   # need 3.12 and 3.13
docker run -d --name s0-pg -e POSTGRES_HOST_AUTH_METHOD=trust -p 55432:5432 postgres:17.10@sha256:7958605b474b3d264a969cb3a123d6aa00ad1e1fe9da8a69984dabb704d93317
docker run -d --name s0-vault -e VAULT_DEV_ROOT_TOKEN_ID=root -e VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200 -e SKIP_SETCAP=true -p 58200:8200 hashicorp/vault:2.2.0@sha256:e0acd3c681bdf57f002d7214e5d050b876e1704678005c6b0406dd96a65be919
psql --version                                  # the database tests shell out to psql (ci.yml:82); without it they skip
```
Record all of it in P0c-1. If Python 3.12 is missing, installing it (`uv python install 3.12`) is the lead's call on the laptop; the cloud session cannot (it has only 3.13 and installing software is on its Never list).

Step 1, conflict and overlap measurement (one command for all rows; it is read-only):
```
python -I <studio>/egm/s0/measure/s0_measure.py <core> ce70eb5 <studio>/egm/s0/raw/measure.json \
  pr41=origin/k6 pr43=origin/demo-gaps pr47=origin/demo-askdata-export pr48=origin/core-hardening-1 \
  pr49=origin/core/promote-refunds-r8 pr50push=origin/core/promote-apexc-review8 \
  pr50local=origin/handover-src/pr50-local-748849c c1a=origin/handover-src/c1a-8460813 c18a=<laptop ref of 198a6b6> \
  dep53=<head of dependabot/uv/moto-kmss3secretsmanager--5.2.5> dep54=<head of dependabot/uv/sqlglot-30.25.0> dep55=<head of dependabot/uv/boto3-1.43.120>
```
How conflict files are counted (one definition): the number of distinct paths printed by `git merge-tree --write-tree --name-only --no-messages <base> <ref>` after its first line (the tree id). Exit code 0 means clean, 1 means conflicts, anything else is an error (UNMEASURED). A path conflicting in two ways (for example add/add) counts once. `CHANGELOG.md` is counted as a conflict file when git reports it, and also shown separately (see question 3). Cross-check: the counts must equal `s0-merge-probe.md` for the rows it lists (cloud result: #41 10, #43 4, #47 0, #48 15, #49 4, #50 both 0, c1a 4; c18a 4 in the probe, UNMEASURED in the cloud). Any difference is written in P0c-2 with the reason (new commit on a branch, base moved, tool version).

Step 2, suites. Baseline first, because "failures already present on ce70eb5 are listed, not hidden" needs it:
```
git -C <core> worktree add --detach <scratch>/wt-base ce70eb5
# per python in 3.12 3.13, run twice (run A and run B) for the baseline:
cd <scratch>/wt-base
UV_PROJECT_ENVIRONMENT=<scratch>/venv-base-<py> uv sync --python <py> --locked --no-build --all-extras --group test
docker exec s0-pg createdb -U postgres s0_base_<py>_<run>
HADAVIN_TEST_PG_DSN=postgresql://postgres@localhost:55432/s0_base_<py>_<run> HADAVIN_TEST_VAULT_ADDR=http://127.0.0.1:58200 \
  UV_PROJECT_ENVIRONMENT=<scratch>/venv-base-<py> uv run --python <py> --all-extras --group test \
  pytest -q -m "not live and not perf" -rs -p no:cacheprovider --junitxml=<studio>/egm/s0/raw/base-<py>-<run>.xml \
  > <studio>/egm/s0/raw/base-<py>-<run>.log 2>&1 ; echo "exit=$?" >> <studio>/egm/s0/raw/base-<py>-<run>.log
# perf tests run alone, once per python, never together with another job:
... pytest -q -m perf -rs --junitxml=<studio>/egm/s0/raw/base-<py>-perf.xml
```
Notes: the command is plan-v3's `uv run --all-extras --group test pytest` plus the CI flags (`-m "not live and not perf"` keeps paid-service tests and timing tests out; `-rs` prints skip reasons). This deviates from the plan's bare command on purpose; the deviation is stated in the report. Gate on pytest's exit code, never on a pipe to `tail`. One database per run (`createdb`) so that parallel or repeated runs cannot collide; whether the tests would collide in one database is UNVERIFIED.

Rows. For every row with exit code 0 in Step 1 (MERGE candidates: expected #47, #50 pushed, #50 local), build and test the merge result, on 3.12 and 3.13:
```
T=$(git -C <core> merge-tree --write-tree ce70eb5 <ref>)
C=$(git -C <core> -c user.name=s0-probe -c user.email=s0-probe@example.invalid commit-tree "$T" -p ce70eb5 -p <ref> -m "s0 probe merge")
git -C <core> worktree add --detach <scratch>/wt-<row>-merged "$C"
```
then the same sync and pytest commands as the baseline in that worktree (and the perf run once, on 3.13). For every row with conflicts, run the same pytest commands on the branch head itself on 3.13 only (worktree of `<ref>`), so the report states the branch's own failures; if `uv sync --locked` fails on a branch (its lock file is older), record "sync failed" and the message; never edit `uv.lock`. Then for each run: `python -I suite_diff.py <baseline-same-python-run-A>.xml <row-run>.xml`. A test that fails in baseline run A or B only is FLAKY. A skipped test whose reason mentions the database (`DB_SKIP`) is a FAILED run (the database was not reached); a skipped Vault test is allowed only if the report says why the Vault container was not used. Record per run: tests, failed, skipped, new failures, same-as-baseline failures, exit code, wall-clock minutes.

Step 3, overlap table. From `measure.json` "pairs": for every pair of rows the shared files (a pair of the same branch, such as #50 pushed and #50 local, is shown once and marked "same work"). Cross-check against memo-5 section 1 (it excludes `CHANGELOG.md`; the differences are written down, for example the new rows c18a and the Dependabot rows). The per-package overlap table (memo-5 sections 2-4) is not rebuilt here: copy it into the report and replace each "E" (expected) cell by the "Files" list of the package's ticket at its commit id, leaving "E" where no ticket exists yet. After the first merge, every row that shares a file with the merged row must be re-measured against the new main: put this sentence in the report and name the rows for each possible first merge (P0b re-runs the table).

Step 4, slot count (method below), Step 5, the refunds question (method below), Step 6, first counts (method below), Step 7, write `s0-report.md` in the format below, Step 8, clean up (Rollback), Step 9, commit `s0-report.md` and `evidence/P0c-*.md` to `core/cloud-handover` (allowed paths, fast-forward only, `git pull --rebase` first) and record in the report the commit id of `handover/TICKET-TEMPLATE.md` on that branch:
```
git -C <core> log -1 --format=%H origin/core/cloud-handover -- handover/TICKET-TEMPLATE.md
git -C <core> ls-tree origin/core/cloud-handover handover/TICKET-TEMPLATE.md   # must list the file
```
(plan-v3 note 2: the S0 exit records that the template is on the branch with its commit id; the cloud clone shows 59bee90f53ede9c5704838693c35caa6fcf0edf2 for it, to be re-read on the laptop after the final push: UNVERIFIED there.)

## Verdict rules (plan-v3 note 2, applied mechanically; the lead decides the final column)

| Rule result | Condition (all must hold) |
|---|---|
| MERGE-eligible | 0 conflict files AND the full suite on the merge result shows no new failure compared with the baseline on Python 3.12 and 3.13 AND no database skip |
| REBASE-eligible | at most 5 conflict files AND the row shares no file with any other row of the report (`CHANGELOG.md` excluded, see question 3) |
| NEEDS LEAD | anything else: the lead writes SPLIT or RETIRE with a written reason; RETIRE also needs a ledger disposition for every open ledger row of that branch (find them with `grep -n -i '<branch or PR number>' handover/ledger.md handover/ledger-seed.md` and the studio ledger `egm/BLOCKER-LEDGER.md`) |

Honest limits of the rule, to be written into the report so nobody reads more into it: (1) a clean merge with zero conflict files can still break behaviour; that is why the suite decides MERGE, and a merge result that passes does not prove the branch's own new tests are sufficient (the reviews decide that, not this report); (2) the probe is against `ce70eb5` only, so after the first merge the others change (said above); (3) #50 pushed and #50 local are the same work at two heads: only one can be merged, and the plan sends #50 through P1, P2a and P2d with a disposition for the rest (A4, A9 F4, P0d), so for #50 the rule result is not the plan's decision; the report shows both and the lead writes the final verdict.

Plan and amendment expectations, shown in a separate column labelled "plan expectation (not a result)" so that the lead can compare them with the measurement: #41 goes to P3c (rebase later, needs P3a and P4d); #43 and #47 to P3d (v1.1, ask-your-data); #48 is cut into separate pull requests after P4a and P4b1 (A1: its extract-leak and spend-cap-429 items stay separate; its `llm/metered.py` loses the money-base decision); #49 to P3b (v1.1; reservations only if refunds is the first client, A1 item 6); #50 to P1, P2a, P2d and the P0d disposition of its other files (A2, A4, F4); c1a is an input to P5c (rebuilt); c18a is an input to P5a (the old design; the new one is rebuilt on `ce70eb5`); Dependabot rows are P0b's (plan rule 12; major bumps such as pytest 9 and sqlglot 30 first re-run `tests/test_migrate_regex_linear.py` and the SQL parser tests). These expectations are the plan's words, not measurements.

## Slot count (method)

Definition (from the studio notes, plan-v2 glossary line 64): a heavy-job slot is one of N machine slots managed by `tools/heavy_slot.py` in the studio root (laptop only); N is its `TOTAL` constant; builders use slots 0-2 and the lead 3-4. Sources disagree, which is why P0c must measure and not repeat them:
| Source | Value |
|---|---|
| plan-v2 line 64; review-plan-2 and review-plan-3 (they cite `heavy_slot.py` lines 8 and 34 as `TOTAL=5`) | 5 (slots 0-4) |
| inventory-B line 106 ("3 slots"); studio rule of 2026-11-03 ("max 3 at once machine-wide", `--slots 3`) | 3 |
| studio rule of 2026-11-02 ("max 4 heavy jobs at once") | 4 |
| owner rule of 2026-11-04 (speed plan: "5 heavy slots, 6 cores") | 5 slots, 6 cores |
| review-brainstorm-1 M8 ("heavy_slot commits suggest it is changing") | unstable |
Measure: (1) read the `TOTAL` constant and the `--help` text of `<studio>/tools/heavy_slot.py` and copy the lines with their line numbers; (2) `git -C <studio> log -3 --format='%h %cI %s' -- tools/heavy_slot.py` to see whether it changed lately; (3) record the laptop's logical cores and memory (`nproc` or `Get-CimInstance Win32_Processor`); (4) run the baseline suite once alone and once while one other heavy job runs, and write both wall-clock times (this gives the real cost of sharing); (5) write the report line: "TOTAL = N (file, line); operating limit in force = M (rule and date); cores = C; baseline suite alone = X min, with one other job = Y min". The number that the plan uses as the work-in-progress limit is M (see question 2). If TOTAL and the rule disagree, the report says so and does not pick silently.

## "Is refunds the first client" (method; an owner question, plan-v3 section 11, default no)

The cloud session cannot answer it and must not guess. The lead asks the owner once, in plain words (studio wording rule 14): "Will the first paying client's project be the refunds project (the build that approves or refuses customer refund requests), yes or no? If yes, the table that holds approved refund amounts (called reservations in PR #49) ships with the core; if no, it waits." The answer is recorded in the report as: the owner's exact words, the date and time (UTC and IST), and where it was given. If the owner has not answered when the report is written, the report says "NOT ANSWERED; the default no applies" and shows both consequences: no means P3b brings nothing for reservations (A1 item 6, P3b stays v1.1); yes means PR #49's reservations ships only as the integer business-money hold table beside the meter (A1 item 6; plan-v3 section 11 row 1). The report must also say that the money meter's winner (Intake `budget.py`, not PR #48, A1, A9 F1) does not depend on the answer. Never write "no" without saying whether the owner answered or the default was used.

## First measured counts (S0 exit item "first measured package and round counts")

"First measured counts" is not defined in plan-v3 beyond section 10 ("after S0 the lead reports per step the package count, rounds seen, wall-clock days") and plan-v1 line 54 ("package count, builder hours, expected review rounds, reviewer-slots, wall-clock days; no calendar promise"). My reading (PENDING LEAD, question 4): the table below, filled from files, no calendar promise.
| Item | How it is counted |
|---|---|
| Packages and pull requests per step | count rows of plan-v3 section 6 per step, with the splits of A8, A9 (F2, F4, F6), A12 and the numbers in `questions-for-lead.md` Q7 (P1 four PRs, P2a five, P4d four sub-tickets); list every split with its source |
| Review rounds seen so far | `ls handover/reviews/` per ticket: round files `P<id>-round<n>-adversarial.md` and `-correctness.md` (at drafting: P1, P2a, P3a had rounds 1 to 3; P4d round 3 was still running); count findings by severity from the files' headings |
| Wall-clock actually spent | `git log --reverse --format=%cI -- handover/tickets/<id>.md` first and last timestamps per ticket (UTC, with IST beside it) |
| Heavy slots needed | from the slot count above and the suite wall-clock times of Step 2 |
Do not turn these into a calendar estimate (plan-v3 section 10: no estimate until S0 exits, and then per step, not in days of human work: studio rule on agent throughput).

## Report format (`handover/s0-report.md`)

Lead with what failed, what is uncertain, what was not measured (studio rule 6). Then, in this order:
1. Header: base commit, date and time (UTC and IST), who ran it, tool versions, the commit id of `handover/TICKET-TEMPLATE.md` on `core/cloud-handover`, the commands deviation (CI flags).
2. Verdict table, one row per branch or pull request:
| Row | Ref and head | Changed files | Conflict files (non-CHANGELOG) | Shares files with | Suite 3.12 (new failures / skips) | Suite 3.13 (new failures / skips) | Rule result | Plan expectation (not a result) | Final verdict MERGE / REBASE / SPLIT / RETIRE | Reason (one plain sentence) |
Rows in this order: #41, #43, #47, #48, #49, #50 pushed, #50 local, c1a, c18a, other `handover-src/*` branches, then Dependabot #53, #54, #55 (verdict "P0b" in the final column). Every cell is filled or says UNMEASURED with its reason. The final verdict and reason are written by the lead.
3. Failures already on `ce70eb5`: table of test ids, Python version, failing in run A and B, and the first lines of the message (masked).
4. Overlap table (branch pairs and the package table), and the re-measure sentence.
5. Slot count line and its table.
6. The refunds answer (words, date, source) and its consequence.
7. First measured counts.
8. What the cloud session could not measure and what the laptop run could not measure (below), each with the next step.
9. Ledger dispositions for every RETIRE or SPLIT row (ids), and the list of WAIVED rows, if any.

## Pass criteria

1. Every row in the table exists with a measured head sha; none is guessed. UNMEASURED cells carry reason and next step.
2. The baseline suite ran twice on each Python, the failure sets are listed (equal, or the difference marked FLAKY).
3. The conflict counts equal the earlier probe for the rows it lists, or the difference is explained.
4. No suite run had a `DB_SKIP`; Vault skips are explained.
5. Every MERGE-eligible row has both Python versions green on the merge result (no new failure compared with the baseline).
6. The refunds answer line says whether the owner answered or the default was used.
7. The slot line gives TOTAL, the operating limit, and the cores, with sources.
8. `s0-report.md` contains the template commit id and the overlap table (S0 exit, plan-v3 note 2).
9. No branch, tag, setting or `main` was changed (check: `git -C <core> for-each-ref --format='%(refname) %(objectname)' > after.txt` equals the Step 0 listing taken before, except for new remote-tracking refs from `git fetch`).
10. Clean-up done: worktrees removed, the two containers removed, no process of the lead's left running (studio rule 19).

## What the cloud session could not measure (and what the laptop run may also miss)

- Test suites: none run (order 4: no tests before "S0 EXIT"); the cloud has Python 3.13 only (no 3.12), no Docker daemon, no database server running for tests, and no `tools/heavy_slot.py` (studio root). Every suite number in the report comes from the laptop.
- c18a (198a6b6): not a ref in the cloud clone; its probe numbers are the lead's, not re-measured.
- The cloud clone's Dependabot refs were older than GitHub's heads; the pull-request list above was read through the GitHub tool, not from refs.
- The real slot count and operating limit (studio files); the owner's answer on refunds.
- Whether Dependabot #51, #52, #56 were merged or closed; whether `origin/core/cloud-handover` changes only `handover/`; whether two suites may share one database; whether `uv sync --locked` works on the older branches (#41 base 308558a, #43, #47, #48, #49 base 6608146): all UNVERIFIED.
- Even on the laptop the measurement cannot show: Windows-only behaviour on the Linux CI image (CI is the Linux check; the lead should compare the 3.13 baseline with the latest green CI run of `main` and list any difference), flaky timing tests (the perf run is the only place they are measured), and live-service behaviour (`-m live` is never run: no spend).

## PENDING LEAD (positions I took; each with my recommended answer)

1. Location and name of the report: `handover/s0-report.md` on `core/cloud-handover` (plan says only `s0-report.md`). Recommended: yes. Raw logs stay in `<studio>/egm/s0/raw/`.
2. Slot count: define it as `TOTAL` in `heavy_slot.py` and also record the operating limit; use the operating limit as the work-in-progress limit and make it the smaller of the two if they differ. Recommended: yes; and, if TOTAL is 5, state the operating limit explicitly (the studio notes give 3 and 4 as well as 5).
3. Is `CHANGELOG.md` excluded when asking whether a REBASE candidate "shares a file with another row"? Recommended: yes (every branch edits it and rule 10 makes it append-only, resolved by the lead), but it still counts as a conflict file when git reports it, and it is shown separately.
4. Meaning of "first measured package and round counts": my reading is the counts table above (packages and pull requests per step, rounds seen, wall-clock, slots; no calendar). Recommended: accept; if the lead meant "the first package to be measured through the full process" (for example P1), say so and I add one line.
5. Suite scope: both Pythons for the baseline and every clean merge result; 3.13 only for conflicting branches (their verdict does not depend on it, and each full suite costs slot time). Recommended: accept; if the lead wants 3.12 for all rows, add it in Step 2.
6. Dependabot rows: measured here, decided in P0b. Recommended: yes.

Model used: Sonnet 5.5 (set by the lead). Files changed: this file only. Head read: `ce70eb5` (main), cloud branch `core/cloud-handover`.

## Build notes (rung table, lead order 56)

**BN-1 (RUNG TABLE, lead order 56, R448; written 2026-11-06 by reading this ticket; short form; no new review round; the ticket stays frozen; no verdict is applied and nothing is replaced).** Evidence is UNVERIFIED unless a ticket line is cited. I could not name a safety guarantee for either script: P0c is read-only measurement for the lead's decisions.

| Component | Why our code (guarantee) | Higher rung seen in the ticket | Evidence | Verdict |
|---|---|---|---|---|
| `s0_measure.py` (merge probe per branch: changed files, conflict files, pairwise overlap; `ref not found` is UNMEASURED) | no safety guarantee from the R448 list; it makes sure an unmeasured row never counts as a pass | git itself does the work (`git merge-tree`, `git diff`, `git rev-list`; Security notes, P0c.md:23); the script is glue around them | Interface (P0c.md:17), P0c.md:23 | QUESTION for lead: is a 3-line shell loop enough? kept outside the repo, so no repo cost |
| `suite_diff.py` (baseline against run: NEW_FAILURE, DB_SKIP) | no safety guarantee; it makes a skipped database visible | pytest's own junit XML; a diff of two XML files could be a maintained tool (UNVERIFIED) | Interface (P0c.md:18), planted failure check (P0c.md:27) | QUESTION for lead: same |
| Slot count, "is refunds the first client", first counts | none: reading a constant, one owner question, counting files | no code written | P0c.md (Slot count, refunds, counts sections) | NO CODE (nothing to decide) |

**BN-2 (TOOL CHECK, lead order 59 item 6; written 2026-11-06; append-only; the ticket stays frozen).** *Question: for `s0_measure.py` and `suite_diff.py`, is a shell loop plus pytest junit output enough?* Checked (T-111): (a) in a toy git repository (git 2.43.0) a 12-line shell loop over `NAME=REF` pairs using `git rev-parse --verify`, `git merge-tree --write-tree --name-only`, `git diff --name-only base...ref` and `git rev-list --left-right --count` printed for a conflicting ref `changed=1 conflicts=1 rc=1`, for a clean ref `conflicts=0 rc=0`, and for a missing ref `ref not found UNMEASURED`, which is the table the Interface asks for except the JSON file and the pairwise shared-file table (the pairwise table is a `comm` over two `--name-only` lists; not written). (b) For `suite_diff`, two pytest runs with `--junitxml` (one baseline, one run) of a five-test toy suite were compared by an 11-line shell using `xmllint --xpath`, `sort`, `comm`: it printed `NEW_FAILURE`, `SAME_AS_BASELINE`, `FIXED_VS_BASELINE`, `DB_SKIP` (skip message contains "database") and `skip`, plus the counts line, each correct on the toy suite. No maintained junit-diff tool was needed; junitparser 5.0.3 installs from PyPI and parses junit files, but I did not look for a diff function in it (T-104 stays UNVERIFIED). I did not run the core suite or the real refs (order 4; the real measurement is this ticket's job). `xmllint` exists on this machine; whether it exists on the studio machine is UNVERIFIED. **Verdict: CUT-TO-CONFIG+GLUE for both scripts.** They name no safety guarantee (R448 list); the one property that matters is that an unmeasured row and a skipped database test can never read as a pass. The single property the shell version can fail with: it prints `UNMEASURED` and `DB_SKIP` only if the loop and the message match are written exactly (a typo reads as clean); the planted-failure check at P0c.md:27 and the `#48`/`#47` probe check at :25 are the pins, and both stay. Cost note: the builder writes the two shell files in `<studio>/egm/s0/measure/` instead of two Python scripts; the Interface lines at P0c.md:17-18 then describe plain text output, not JSON.

**BN-3 (lead order 61 item 7; Q3).** The shell-loop replacement must FAIL CLOSED: a missing tool (git, xmllint), a missing ref or an unreadable junit file prints UNMEASURED and exits non-zero, never a pass.
