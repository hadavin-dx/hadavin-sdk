# P3a-2 history memo: old branch or rewritten branch for PR73

Written 2026-11-11 (UTC) by an evidence/analysis runner. Nothing was committed, pushed, rewritten or deleted. Failures and unknowns come first.

Plain words used here: the *old branch* is `core/P3a-2` (head `ac94d18fb1cf`, the branch PR73 uses now). The *rewritten branch* is `core/P3a-2-rewritten` (head `8382bdd5b0e3`). The *handover review paths* are files under `handover/reviews/`, `handover/tickets/` and `handover/evidence/`.

## 1. Findings

### 1.1 What does NOT hold or is not yet proven (read this first)

1. **The rewritten branch alone does not turn the CI `security` job green.** The job step "Stale gitleaks ignore entries" (in `.github/workflows/ci.yml` on `main`, lines 187-226) does not look at the pull request's own history only. It runs `git log ... HEAD --all --not origin/core/cloud-handover` and fails if ANY fetched branch other than `core/cloud-handover` holds a handover review path in its history. I reproduced that logic locally (section 1.4). Six remote branches fail it today: `core/P3a-2` (213 paths), `wip/cloud-B-P73r2` (213), `wip/cloud-B-cilint-b3` (14), `wip/cloud-245-B-cilint-b3` (14), `wip/cloud-B-peel` (5), `wip/cloud-245-B-peel` (5). Deleting only `core/P3a-2` would still leave four failing branches. The cloud resume note (`CLOUD-RESUME-2026-11-11.md`, section 0) says the job "fails any PR whose history holds handover paths"; that is not what the code does. The PR's own history is not the trigger. PR89 has 0 handover paths in its own history and its `security` job still failed (PR89 job 130375431215; the last log lines list the `core/P3a-2` paths, then "files under handover/ exist in the history of HEAD or of a branch other than core/cloud-handover").
2. **The rewritten branch holds work the old branch does not have, and that work has no review and no independent evidence.** The old PR head `ac94d18` is round 10. The rewritten head is round 11 (4 extra commits: REPLICATION flag refusal, read-back of rights and owners that existed before the run, mutant-list fixes, sharper mutant killers). They change 11 non-handover files (+1349 / -200 lines, mostly `migrate.py`, `tests/test_migration_postgres.py`, `tests/migrate_mutants.py`). I found no review or evidence for round 11 in the files I read. Any "the trees match" claim is true only against `wip/cloud-B-P73r2`, not against the PR73 head (section 1.2).
3. **PostgreSQL 17 was not run by me**, and I ran no tests at all. CI uses 17; the ledger rows I read (`BL-core-a5-w2-ev-02`) say 17 was never run in the cloud.
4. **The "67 commits" figure in my brief is not reproduced.** I count 48 commits on the rewritten branch that are not on `main` (45 on the old branch) and 110 commits reachable from the rewritten head. The earlier questions file says "106 commits" for an older state of this branch. I do not know where 67 comes from.
5. **My local clone was shallow** (one boundary commit) when I started; I ran `git fetch --unshallow origin` (local objects only, remote untouched) and re-ran every count after that. The counts below are post-unshallow.
6. **Not checked:** the CodeRabbit, CodeQL and SonarCloud result on the rewritten head (it has no PR, and PR73 is a draft so its `check` and `security` jobs show "skipped"); whether the six offending branches hold content found nowhere else (see section 4).

### 1.2 Do the trees match outside the handover folders?

Commands: `git diff --name-status origin/core/P3a-2 origin/core/P3a-2-rewritten`, then comparisons per commit.

- The two branches differ in **219 paths**: 208 deletions (all under `handover/`) plus 11 modifications (all non-handover, all round 11).
- Against `wip/cloud-B-P73r2` (`58acdcc46b5e`, the old local head that descends from `ac94d18` and is on the remote), the difference is exactly **208 deletions and nothing else**. So the rewritten tree equals the old line of work at round 11 with the handover review paths removed.
- Against the old PR73 head (`ac94d18`), the non-handover tree of the rewritten branch's round-10 equivalent (`42fc2597`) is **identical** (empty `git diff` outside `handover/`).
- Per commit: 45 old commits; 44 have a counterpart with the same subject and an identical non-handover tree; 1 is dropped (`d41a0c0c` "P3a-2 round 9: builder evidence", handover-only). 4 commits are new (round 11).
- The old tip tree holds 208 handover paths; the old history holds 213 distinct handover paths (5 were deleted again before the tip).

### 1.3 Authorship, trailers, dates

For the 44 matched commits: author date differs in 0, full commit message differs in 0. All 48 rewritten commits have author `Claude <noreply@anthropic.com>` and a `Claude-Session:` trailer line (47 lines counted by `grep -c` over the messages, against 44 on the old branch; the count is lines, not commits, so I did not prove "every commit has one"). The commit ids all change (rewrite), so anything that cites an old sha needs the map in `handover/decisions/P3a2-sha-map.tsv` (49 rows: old `wip/cloud-B-P73r2` sha, new sha, whether it is on the PR73 head).

### 1.4 CI `security` job logic, reproduced

- The only path rule is the one quoted in 1.1 (pattern `^handover/(reviews|tickets|evidence)/`). It also fails if the checked-out TREE holds such a path. The old branch tree holds 208, so the old branch can never merge into `main` as it is (the `pyproject.toml` comment also says the handover folder is removed before the final merge). The rewritten tree holds 0.
- Reproduction (local, `--remotes=origin` instead of `--all`, which also covers `refs/pull/*` in CI): for each remote branch `r`, `git log -m --name-only -z --format= r --not origin/core/cloud-handover -- | tr '\0' '\n' | grep -E '^handover/(reviews|tickets|evidence)/'`. Offenders: the six branches in 1.1. `origin/main` and the rewritten branch: 0.
- The rewritten branch's whole history: 0 handover paths of any kind.
- gitleaks 8.30.1 (the CI version; downloaded, SHA-256 matched the pinned value), config and ignore file taken from `origin/main`: whole history of the rewritten branch, **no leaks found**, exit 0. The same command on the old branch also gives exit 0. So gitleaks is not what fails PR89; the path rule is.
- Other steps of the job (pip-audit, bandit, semgrep, zizmor, Trivy) were not run by me.

### 1.5 PR73's review threads and old shas

- PR73 on GitHub: draft, base `main` (`0dabf1fa`), head `ac94d18`, 237 changed files, 45 commits. Review threads: **0**. Reviews: **0**. Comments: 1 (the SonarCloud bot, quality gate passed). So no GitHub review thread depends on an old sha.
- The PR description is stale (it says head `d01c84b4...` and carries internal order numbers and `R448` in public text). A new PR needs a fresh description anyway.
- The real review record lives in `handover/reviews/P3a-2*`, `handover/evidence/P3a-2/<sha>-...` and `handover/ledger.md`, keyed by old shas (`ef2adc7`, `cb0930f`, `acc5bfc`, `ffe896e`, `c727453`, ...). Those shas stay readable only while a branch holds them. The ledger rows I read (BL-core-a5-w2-*) say many items are FIXED-UNVERIFIED or OPEN; a head change voids evidence anyway (studio rule), so evidence must be re-run on the final head whichever branch is chosen.

### 1.6 Do PR89, PR77, PR74 and PR85 need a rebase onto the rewritten history?

They are **not stacked on the old P3a-2 history**. For each, `git merge-base` with the old `core/P3a-2` is an older commit on `main` (`0dabf1fa` or `13ebfafe`), not `ac94d18`, and none contains the old or rewritten tip. So the choice of branch does not break them. What they do share is a normal merge conflict with PR73's content, identical under both branches:

| PR (branch) | onto `main` | onto old `core/P3a-2` | onto `core/P3a-2-rewritten` |
|---|---|---|---|
| PR89 `core/mutation-runner-keywords` | clean | CHANGELOG.md | CHANGELOG.md |
| PR77 `core/P2d-1` | clean | CHANGELOG.md | CHANGELOG.md |
| PR74 `core/P5a` | clean | CHANGELOG.md, tests/conftest.py | CHANGELOG.md, tests/conftest.py |
| PR85 chain `core/P5b1` | clean | CHANGELOG.md, tests/conftest.py | CHANGELOG.md, tests/conftest.py |
| PR85 `core/P5b2` | clean | CHANGELOG.md, migrate.py, tests/conftest.py | CHANGELOG.md, migrate.py, tests/conftest.py |

Method: `git merge-tree --write-tree --name-only <target> origin/<branch>` (no files touched). I also ran the cherry-pick replay the brief asked for, in a throwaway worktree `/home/user/build/memo-dry` (now removed; `git worktree list` shows none): replaying each PR's non-merge commits onto the rewritten head stops at the first commit with a conflict in `CHANGELOG.md` for all four (PR89 24 commits, PR77 17, PR74 22, PR85/P5b2 33). That is a whole-file changelog clash, so a per-commit replay is the wrong tool; resolve by merging whichever PR lands second. `core/P5b2` also touches `migrate.py` where PR73 changes it: that one needs a real read, not a mechanical fix. No rebase is needed to *start* with the rewritten branch.

## 2. Options

| | A. Keep the old branch (PR73 as is) | B. New PR from a new branch name (additive) | C. Other |
|---|---|---|---|
| What | PR73 stays on `core/P3a-2` | Open a new PR from `core/P3a-2-rewritten` (already a new name) or from a copy named `core/P3a-2-clean`; leave `core/P3a-2` and PR73 untouched | C1: change the CI path rule so handover branches no longer block (a CI change, owner decision). C2: remove the handover paths with a new commit on top of the old branch (tree check passes, history check still fails; useless). C3: rewrite `core/P3a-2` itself (force push) |
| Cost | none now | one `gh pr create`, a fresh PR description, then round 11 review and evidence on the new head (needed in A as well) | C1: a CI PR plus the owner's yes; C3: the human's decision, see risk |
| Risk | Can never pass the tree check (208 handover files in the tree) and fails the `security` job through the six branches. Not mergeable. | Same six-branch problem until those refs are dealt with (section 3 step 3); the new PR is clean in itself (0 handover paths, gitleaks 0) | C1 weakens a security gate. C3 rewrites a remote branch and invalidates the PR's recorded head; refused by the safety classifier before |
| Reversible | n/a | Yes: close the new PR, delete the new branch; old refs untouched | C1 yes (revert); C3 no unless a backup bundle exists |
| Lock-in or loss | none | Old shas become unreachable only if the human later deletes the old refs; the sha map and the bundles cover that | |

## 3. Recommendation

**Option B, additive only.** It is the only route where the history is clean in itself (0 handover paths in the whole history, 0 gitleaks findings, tree identical to the old line outside the handover folders), it needs no rewrite of any existing remote branch, and it can be undone by closing the PR. Do not choose A: it cannot merge. Do not weaken the CI rule (C1) as a shortcut; if the owner wants it, that is a separate decision with its own review.

Steps, and who decides:

1. Lead (additive, safe): open a **draft** PR from `core/P3a-2-rewritten`, base `main`, with a new description (no order numbers, no private ids, say "round 11, not reviewed, PostgreSQL 17 not run"). Leave PR73 open and untouched.
2. Lead: run the review and evidence for round 11 on head `8382bdd5b0e3` (the independent runner, then fresh `egm:*` reviewers). Evidence for any old head is void for this head.
3. **Human decision (not me, not an agent):** the `security` job stays red for every PR until the six handover-bearing refs are no longer fetched. The only paths are deleting those refs, or changing the rule. If the owner chooses deletion, back up first (below), delete only refs the owner names, and re-check with the reproduction in 1.4. Their handover content is also in `wip/cloud-B-P73r2` (213 paths, same as `core/P3a-2`) and in the bundle `handover/bundles/p73-rewritten-rw.bundle`; the 14 and 5 paths on the cilint and peel branches exist only on those branches, so a bundle of them is mandatory.
4. After the new PR is green and reviewed, the lead (or owner) closes PR73 with a comment pointing to the new PR. Merging stays with the owner.

## 4. Exact next commands for the human

Run from the laptop clone. Every command up to the "STOP" line is read-only or additive.

```bash
git fetch origin --prune
# 1. confirm the heads you decide on
git rev-parse origin/core/P3a-2 origin/core/P3a-2-rewritten     # expect ac94d18f... and 8382bdd5...
# 2. open the new draft PR (additive; leaves PR73 alone)
gh pr create --draft --base main --head core/P3a-2-rewritten \
  --title "P3a-2: wire migrate() to the migration rule (clean history, round 11)" \
  --body-file <new-description.md>
# 3. back up every branch that holds handover paths BEFORE any decision to delete (additive, local file)
git bundle create ~/p3a2-handover-branches.bundle \
  origin/core/P3a-2 origin/wip/cloud-B-P73r2 origin/wip/cloud-B-cilint-b3 origin/wip/cloud-245-B-cilint-b3 \
  origin/wip/cloud-B-peel origin/wip/cloud-245-B-peel
git bundle verify ~/p3a2-handover-branches.bundle
# 4. re-run the CI path rule locally before and after any change
pat='^handover/(reviews|tickets|evidence)/'
for r in $(git for-each-ref --format='%(refname)' refs/remotes/origin | grep -v HEAD); do
  n=$(git log -m --name-only -z --format= $r --not origin/core/cloud-handover -- | tr '\0' '\n' | grep -E "$pat" | sort -u | wc -l)
  [ "$n" -gt 0 ] && echo "$n $r"
done
# STOP: deleting any remote branch (git push origin --delete <ref>) is a human/owner decision; not part of this plan.
```

## 5. What was not checked

- No test, lint, mutant run or bandit run; no PostgreSQL 17; no CodeQL, SonarCloud or CodeRabbit result on the rewritten head.
- The CI `security` steps other than the path rule and gitleaks (pip-audit, bandit, semgrep, zizmor, Trivy).
- Whether GitHub keeps pull-request refs (`refs/pull/*`) in the fetch that CI does; my reproduction used `refs/remotes/origin/*`. If PR refs of PR73 count, they carry the same old paths.
- The first lines of the failing PR89 job log (I read the last 45 lines only); the offender list there matched `core/P3a-2` paths, consistent with, but not proof of, the six-branch result.
- The contents of the 14 and 5 paths on the cilint and peel branches beyond their names; whether they are also kept elsewhere.
- Authorship beyond name, email and the trailer line count; no signature check (none expected).
- That the ledger has no round-11 rows: I read only the PR73/P3a-2 rows up to round 5 and the questions file entry.
- Helper files I created: `handover/decisions/P3a2-sha-map.tsv` (old to new sha map). Local side effect: `git fetch --unshallow` on this clone; scratch gitleaks binary and reports under the session scratchpad (not in the repo).
