# fix-review15 (round 23 fixer log; static only; no Postgres, no tests, nothing committed)
Edited ONLY `REVIEW.md` (plus this log). Inputs: `../reviews/review-design-r22.md` (M1, M2, L1-L7; the file has no L3, so nothing was done for an L3) and `../reviews/review-reader-r22.md` (M1-M7). Reviewer words were treated as unverified; each cited src line was opened first (`migrate.py:190-300, 335-360`, `audit/chain.py:180-320`, `k1b/audit_sink.py`, `models.py:100-150`, `config.py:415-422`, `agent_loop.py:766-770`).

## What the source showed that differs from the reviewers
- Design M1 confirmed: `effective_problems` (`migrate.py:193-262`) already checks effective rights incl. membership/PUBLIC/ownership, schema CREATE, superuser/createrole/createdb/bypassrls, every relation. Missing (grep count 0 for `has_function_privilege`, `has_database_privilege`, `pg_default_acl` in `migrate.py`): EXECUTE, TEMPORARY, future default privileges, calls for the new logins (it is called for runtime and purge only; portal gets `_excess_privileges`, `:265-280`).
- Design M2 confirmed: `checkpoint()` SELECT MAX(seq) + INSERT on `audit_checkpoints` (`chain.py:290-293`, `:310-314`), failure swallowed (`:315-317`). Both options for `k1b` written (K-A signs, K-B does not sign); NOT decided; studio head question named as 5-K inside Decision 5.
- Design L1: reviewer's counts were muddled; I counted: INSERT on `audit_entries` for six names (agent, tick, receiver, operator, k1b, drain) = five logins.
- Design L5: the docstring `audit_sink.py:38` says the SINK keeps a failed event for `reconcile`; that is true of the sink, so "false promise" was too strong; reworded.
- Design L6: working-tree check run (below).

## Commands run (raw)
$ git diff --quiet 176a0cbe0 -- src tests pyproject.toml   -> rc=0 ; `git diff --stat` printed 0 lines
$ git status --porcelain -- src tests pyproject.toml | wc -l   -> 0
$ git rev-parse HEAD   -> 1be1b541eb345a0758176332312c9141dcb7d078
$ git reflog --format=%h | grep -c b4cce5b   -> prints 0, grep exit=1
$ grep -c "has_function_privilege\|has_database_privilege\|pg_default_acl" src/hadavin_sdk/store/migrate.py  -> 0
$ python3 -I count_review.py REVIEW.md
rows 28 ['C-1', 'C-2', 'C-3', 'C-4', 'C-5', 'C-6', 'C-7', 'C-8', 'A-1', 'A-2', 'A-3', 'A-4', 'A-5', 'A-6', 'A-7', 'A-8', 'A-9', 'G-1', 'G-2', 'D-1', 'D-2', 'D-3', 'X-1', 'X-2', 'X-3', 'X-4', 'X-5', 'X-6']
severity {'Nit': 11, 'Minor': 13, 'Major': 4}
decision {'DECLINE': 3, 'PROPOSE FIX': 25}
(counts unchanged: 28 rows, 4 Major, 13 Minor, 11 Nit, 25 PROPOSE FIX, 3 DECLINE; the counts block in REVIEW.md needs no change; new table rows are criteria rows and rows 23a/23b, which the script does not count)

## NEEDS THE STUDIO HEAD (named decisions) or the lead
- Name the deployer (Who-is-who bullet; no file names one).
- Decision 5, question 5-K: do the K1b commands sign (K-A) or not (K-B)? Also settles Decision 2(b).
- Decision 23b: who rewrites branch `cloud/flows-audit` (or accept in writing), and when.
- The lead to confirm the dated first action (2026-11-17 start, 2026-11-19 report, 2026-11-20 range): assistant proposal, nobody assigned.

## Not done / not verified
- No Postgres, no tests run; every Postgres behaviour claim stays UNVERIFIED.
- Reader M3: blocks added as a new section before "Matter today"; the older long paragraphs were kept (not replaced), so the decisions are still in two places, now cross-pointed.
- Reader M5: headline run-on kept; a plain version was put in front and the 4/9/11 mapping added, not a full rewrite of the paragraph.
- Reader M7: I searched all lines before History for "owner" and "step" by grep and fixed person-word and non-tick uses; History keeps old words by design. "see below" pointers: fixed the four I could resolve (lines for C-5, Decision 18, X-2, X-6.6); two others (the `k1b` row pointer and the Decision table pointer) name a real place already.
- Decision 23b: the effect "commits before 34540bfa2 keep their ids" is general git behaviour, not tested here; I did not search for files that quote later commit ids.
- Sizes for criterion (9) (1 to 2 days) and for 23b are my judgement, not measured.
