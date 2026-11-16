# Fix report, patch-copies, pass 23 (fixer; security path)

Written 2026-11-16. Files edited: `patch-copies/README.md` and `patch-copies/DEAD-MAN-CHECK.md` only.

## What failed or was not checked (first)
- The full recipe was NOT run (no real uv, no pytest, no proof, no gates, no macOS). The brief forbade it.
- The new untracked-file check (clause (e)) was run only on a local clone with stand-in logs, never through real test runs. Whether real runs leave other untracked files is unknown; the check fails safe and the text says so.
- The minimum git version for `git patch-id --verbatim` (set to 2.32) was not verified.
- I could not call the EGM skills from this agent; the lead runs the EGM review of this result.
- DEAD-MAN-CHECK.md: static edits only; 4 fenced blocks fail `bash -n`, the same 4 as before my edits (SQL and sample output, not shell).

## Evidence
- Patch fingerprints before and after are identical (sha256sum):
  - A-01.patch 64fdf315221fb9d653fe8defc844aa438c39c56bc32c5a86c70d8aab67892095
  - C-01-price-only.patch e7ff677e70d0c1fd61e9c4e2f1024c58fd35b83bc715abd3d0449202038dae01
  - C-01.patch ca4982ebb9daef2d5c96e1538d2cdde5291d2d9a948c70553b5661a0a17fded0
- `bash -n` on fenced blocks: README.md fenced 12, bad 0; DEAD-MAN-CHECK.md fenced 12, bad 4 (baseline 4).
- `ruff format --check .` (handover/flows-audit): "1098 files already formatted".
- tools: check_refs PASS 5190; check_names PASS 655; check_secrets PASS 0 hits in 2973 files; check_counts PASS 52 files / 655 nodes.
- Local-clone test with stand-ins: setup rc=0, patches apply, clause (e) ok, verdict prints PART 1; untracked `conftest.py` gives `(e) FAILED`; `.hypothesis/` does not; cleanup refuses when final.txt was not kept.

## README.md
- FIXED: personal GitHub handle removed from the recipe (placeholder `OWNER_NAME`, setup stops while it stands); `scrub` has a rule replacing the account segment of github.com URLs with OWNER; failure-report text says so. The old name is 0 times in both files. It may remain in git history and other folders (not touched).
- FIXED: cleanup refuses when final.txt exists but was not copied to K; `DISCARD_LOGS` lasts one call; keep_logs stops on 0 files.
- FIXED: `|| echo STOP` on the silent chains (fingerprint heredoc, SRC_CACHE, SRC_PY); netrc refusal; git 2.32 check; `GIT_CONFIG_NOSYSTEM`; fingerprint grep exact.
- FIXED: clause (e) refuses untracked files (new `ut`); scope string names the missing self-hosted price test and "NOT a merge clearance"; pass-rule lists clause names.
- FIXED: "step" vs "part" wording (8 parts plus 5b); one exit-code list; "t on 14 and older" note; definitions before use; date line; history entry for pass 23; stale text marked OBSOLETE.

## DEAD-MAN-CHECK.md
- FIXED: exit rows 72 and 74 and fact 3 (alert tried, stderr line if it fails, code unchanged; 75 defined).
- FIXED: D8 blocks T2 and carries an audit proposal (90 days, reminder 14 days before); "never expires" default removed.
- FIXED: one silent-exit list (1, 70, 71, 73, 75, 76, 77, 129 to 143) in rule 4 and fact 3.
- FIXED: `limit_s=240` example; angle-bracket words explained; glossary (studio head, lead, PUBLIC, Blocks, checks, S1 to S8, facts, psql exit codes); programs list gains `env`, `psql`, `rmdir`, `ls`; D9 gap check; fact 8 programs before the scrub; check 3f Postgres 14 note; VALUES-list wording; manual-test healthy output; "seventeen" replaced by a pointer; pass-23 history entry.
- NOT APPLICABLE: the old phrase "line 142 of the script" no longer exists in the file (nothing to fix).

## Needs patch author
- r20c m9 and the r24 M2 root cause: no test for the self-hosted model price (section C-01), and the RV-A1 wording; both need edits to the frozen patch files. The recipe scope string now names the gap.

## Needs lead
- Confirm whether the removed owner name was a personal handle; where failure reports go; whether the repository is public; who holds the merge credential; the archive copy of b4cce5b; run the EGM review and evidence runner.

## Not fixed
- Nothing else deferred.
