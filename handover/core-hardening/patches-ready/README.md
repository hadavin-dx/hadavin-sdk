# Core patches: the single index (rewritten 2026-11-16; replaces the old "nothing was run" page)

Words: "the take" = the one real-v5 video run. "Base" = commit `b4cce5b`. Every number below names the file and line it was read from.
Numbers from a patch set that is not the kept scope are listed so nobody mistakes them for the kept scope. Only the kept-scope count counts.

## What was NOT run or not checked (read first)
- **The 455 Postgres tests were never run.** They are skipped in every full run (no Postgres in the build container): `v5/README.md:16`, `v5/raw/full-suite-c01min.txt:140`.
- **The real head `de6b574` was never tested.** All runs are on base `b4cce5b` (`v3/handback-c7b-fix4.md:3`, "Not done" list). Re-check the patches apply at the real head before use.
- **n8n was never run** for these patches. No test, run or log in this folder touches n8n. No file here shows an n8n run of these patches. (`review/necessity-r1.md:2,4` says the take claim is carried by n8n plus `scripts/run_real_check_n8n.py`, which that reviewer did not read.)
- Also never run: the dead-man query (`v5/README.md:16`), any check that the audit database identity cannot UPDATE or DELETE `audit_entries` (same line, `v5/README.md:16`), any live model, cloud or network call for the patch tests.
- The repo guard tests ran on a git-initialised copy with `handover/` removed, not on the real repository (`v5/README.md:16-18`).
- The `200_000` `max_tokens` ceiling in C-01-MINIMAL is a typo guard, not a provider limit; no provider page was looked up (`v5/README.md:23`). The studio head must confirm the number.
- The C7b fix was not re-run in the full suite after "fix 4" (fix 4 changed no `src/` or `tests/`): `review/design-c7b-fix4-r5.md:4`.
- I (the author of this index) re-read the files named below and ran `sha256sum` on the C7b patch; I ran no tests.

## Which patch set is the KEPT scope
**The kept scope is `v5/`:** `G5-wording.patch` (apply now) + `C-01-MINIMAL.patch` (optional, only if the take's model program loads `Route` config) + `DEAD-MAN-CHECK.md` (a note, nothing to apply).
- Decision 4 (lead scope cut, 10:02Z): `A-01` is DEFERRED, the C-01 extras are CUT. Source: `v3/README.md:3-12`; also `v5/README.md:5-13`; `STATUS-BOARD.md:25`.
- Q18 (lead answer 10:31Z, `ANSWER-Q18-lead.md:2`): stop NEW work on C8, C5 and C7; finish only rounds already running; keep G5 wording and the dead-man note. No new patch work is open.
- Round 5 design review of v5: no blocker, no major (`review/design-r5-c5v5.md:2`).
- Apply command and the one-line grep that decides whether `C-01-MINIMAL.patch` is needed: `v5/README.md:9-13`.

| Item | State | Where |
|---|---|---|
| `G5-wording.patch` (comments and docstrings only, 3 files, no behaviour change) | APPLY NOW | `v5/G5-wording.patch` |
| `C-01-MINIMAL.patch` (refuse a live model price of 0 or below; refuse `max_tokens` above a ceiling; pilot and prod only, plus the replay command) | OPTIONAL | `v5/C-01-MINIMAL.patch` |
| `DEAD-MAN-CHECK.md` (note, four steps watched; audit-outbox gap marked UNCOVERED while A-01 is deferred) | NOTE only | `v5/DEAD-MAN-CHECK.md` |
| `DEFERRED-A-01.patch` (audit events waiting in the outbox) | DEFERRED, do not apply | `v5/DEFERRED-A-01.patch`; `v5/README.md:80-90` |
| `CUT-C-01-FULL-NOT-FOR-THE-TAKE.patch` (C-01 with extras) | CUT, do not apply | `v5/CUT-C-01-FULL-NOT-FOR-THE-TAKE.patch`; `v5/README.md:92-98` |
| `v6-extra/FIX-id-vs-command-withheld.patch` (C7b gate fix) | DESCRIBE-ONLY, see below | `v6-extra/` |

## Superseded folders (v1 to v4), do not use
Banner wording for a folder if you add one (file `SUPERSEDED-NOTE.md`): "SUPERSEDED. The kept scope is `../v5/` (decision 4, Q18). Kept only for its raw evidence. Do not apply anything from this folder."

| Folder | What it is | Why superseded |
|---|---|---|
| top level `A-01.patch`, `C-01.patch`, `G5-wording.patch`, `DEAD-MAN-CHECK.md`, `unverified-claims-check.md` | the first set, made on a scratch copy; the old page said "nothing run" | replaced by v2 to v5; `A-01` and full `C-01` are not in the kept scope |
| `v2/` | second set (C-01, A-01, G5) | replaced by v3 |
| `v3/` | all three patches with fixes; its `C-01.patch` still holds the cut extras and its `A-01.patch` is deferred (`v3/README.md:3-12`) | replaced by v4 and v5; its raw files and C7b evidence are still cited |
| `v4/` | first minimal C-01 (`C-01-MINIMAL.patch`) | replaced by v5 (v4 dead-man note was the unedited v3 text, `v5/README.md:32`) |

Do not delete v3 or v4: v5 cites their raw files (`v5/README.md:66`).

## Test counts: which patch set each belongs to
All are `pytest` on a scratch copy of base `b4cce5b`. Only the v5 row is the kept scope; the others are listed to stop confusion.

| Count | Tree it was run on | In the kept scope? | Source (file:line) |
|---|---|---|---|
| **9418 passed, 455 skipped, 0 failed**, 231 s | base + G5 + C-01-MINIMAL (v5 final tree) | **YES, the only count that counts** | `v5/raw/full-suite-c01min.txt:140`; quoted `v5/README.md:66` |
| 9413 passed, 455 skipped, 0 failed | base + G5 + the earlier C-01-MINIMAL (v4) | no, v4 superseded | `v4/raw/full-suite-c01min.txt:140`; `v4/README.md:62` |
| 9491 passed, 455 skipped, 0 failed | base + G5 + full C-01 + A-01 (v3) | no, includes cut C-01 extras and deferred A-01 | `v3/raw/full-suite.txt:141`; `v3/README.md:182` |
| 9514 passed, 455 skipped, 0 failed | v3 tree + the C7b id fix (full C-01, A-01, G5 and fix) | no, same reason; only evidence for the C7b fix | `v3/raw-c7b-fix3/full-run.log:145`; `v3/REPORT-c7b-fix3.md:13` |
| 9391 passed, 455 skipped, 0 failed | pristine base, git-initialised copy, `handover/` removed (the baseline for the v3 to v5 counts) | baseline | `v3/raw/pristine-full-suite.txt:139`; `v3/README.md:181` |
| 2 failed, 9389 passed, 455 skipped | pristine base WITH `handover/` present; the same two repo-guard tests fail with and without patches | baseline, a branch artefact (Q16.2, `ORDERS.md:140`) | `../patch-test-runs/raw/base-pytest.log:255`; `v3/raw-c7b/base-pytest.log:181` |
| 2 failed, 9451 passed, 455 skipped (v2) | v2 tree | no, superseded | `v2/README.md:109` |

Reading the arithmetic: v5 9418 = 9391 + 27 new tests (23 in the new file + 4 replay cases) (`v5/README.md:66`, `:56`). The 9391 figure was quoted from v3, not re-run in v5 (`v5/README.md:66`).
The kept-scope result of the 23 new tests on the unpatched tree: 19 failed, 4 passed; only 11 of the 19 prove the rule is missing, the other 8 fail on an unrelated key-file refusal (`v5/README.md:63`).
12 of 12 hand-made mutants were killed (`v5/README.md:69`).

## C7b gate fix: status DESCRIBE-ONLY
- What it is: `v6-extra/FIX-id-vs-command-withheld.patch`, one lookahead in `src/hadavin_sdk/approvals/gate.py` plus a 23-test file. It stops the approval card showing `[command withheld (G4)]` in place of an id that starts with `ec2` plus a letter a to f (display only, it does not widen what the gate approves): `v6-extra/README.md:3,16`. The failing ids occur in 24 of 262,144 id shapes, about 1 test run in 2,731 (`v6-extra/DESCRIBE-ONLY-flaky-id-test.md:3`).
- Status: **describe-only** per lead answer Q16.1 (`ORDERS.md:139`, 10:42Z): accept the flake, do not edit `src/` or `tests/`, write it up for a later core branch. It is not part of the take and is not applied.
- sha256 of the patch: `12e4be6f42e2f47ae254276cdcf27b1cb31b50d5fa40a1adcedde4acfeb6b9ce`. I re-ran `sha256sum` on `v6-extra/FIX-id-vs-command-withheld.patch` and it matches `v6-extra/FIX-id-vs-command-withheld.patch.sha256`.
- Evidence: old code 11 failed, 12 passed; new code 23 passed (`v3/REPORT-c7b-fix3.md`, g4 section); full run 9514 (table above, not kept scope).
- Review: round 5 design review of the evidence, 0 blockers, 0 majors, recommendation accept (`review/design-c7b-fix4-r5.md:2-5`). This is a review of the evidence files, not a result review by the lead. The patch is a security path and still needs the lead's independent result review (`v6-extra/README.md:14`).
- Open, described only: the cloud-cmdlet rule may not match `Remove-EC2*`, `gcm Remove-EC2*` or a bare `Remove-EC2`; whether another rule still catches them is unchecked (`v6-extra/DESCRIBE-ONLY-flaky-id-test.md:8`). Next step for the lead: a test feeding those three strings to the gate and a decision on a fix in `src/`.
- The "no network" claim of an earlier pass was withdrawn (`v3/REPORT-c7b-fix3.md:4`).

## Other things the lead must decide (from v5)
- Open siblings of the same bug class, not fixed: `registry.py` `Budget.daily`, `Budget.monthly` and `max_run_usd` accept 0 or negative; `deferred.py:62` checks only "not None" (`v5/README.md:26`). Next step: the lead says go, then one predicate in `registry.py`.
- If A-01 is ever un-cut: read `v3/README.md` "A-01" and "Owner decisions" first, and re-run the mutation check on the final tree (`v5/README.md:73-78`).

## Where to read more
`v5/README.md` (full detail), `v5/REPORT-v5.md`, `v5/SHA256SUMS.txt`, `review/` (all review rounds), `v6-extra/README.md`. Cross-check source for this index: `../cross-read/one-place-sweep-r1.md:21` (item 8).
