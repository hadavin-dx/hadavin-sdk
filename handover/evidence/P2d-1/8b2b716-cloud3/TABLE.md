# EVIDENCE RUNNER table, PR77 core/P2d-1 head 8b2b71685c4a83d6e1d4abc8e93b90998dce36d1. Raw logs in this folder. No verdict.
Snapshot: detached /home/user/build/EV-P77-8b2b716/wt, HEAD printed first in each log. Run 18:47-19:46 UTC (IST = UTC+5:30), shared machine, 3 heavy slots via heavy.sh (qsubmit.sh does not exist on this machine; heavy.sh is the legacy wrapper). One Postgres 16 server for the run (port masked), 3.12 and 3.13 run one after the other. Fake DSN, trust auth.

## PR63 head check (needed: this evidence is void if it changed)
- `git ls-remote origin core/P1a` at 18:47 UTC: 27ae996bf770076dfa029c958a56a547057a4f49 (head.txt). Re-read at 18:50 UTC: same.
- The head 8b2b716 is a merge of origin/core/P1a at 2572847ee586 (second parent). 27ae996 is NOT an ancestor of 8b2b716 (git merge-base --is-ancestor exit 1); 2572847 is an ancestor of the current origin/core/P1a. So this evidence was run on a P2d-1 head that does not contain the current PR63 head.

| Check | Python | Result (from the log) | File |
|---|---|---|---|
| ruff check src tests demos tools | 3.13 | exit=0, All checks passed | ruff-check.txt |
| ruff format --check src tests demos tools | 3.13 | exit=1: 1 file would be reformatted (tests/test_redact_fold.py:473, one string concatenation), 323 already formatted | ruff-format.txt |
| tools/scan_repo.py | 3.13 | exit=0 | scan-repo.txt |
| bandit -q -r src demos tools -ll | 3.13 (uvx) | exit=0 (nosec warning lines only). First attempt exit=127: wrong path, kept as bandit-first-attempt-no-bin.txt | bandit.txt |
| gitleaks git, history reachable from HEAD (60 commits) | n/a | exit=0, no leaks | gitleaks.txt |
| gitleaks git, all refs of this clone (3299 commits) | n/a | exit=1, 720 findings (not broken down; other branches; CI scans only the PR checkout) | gitleaks-all-refs.txt |
| pytest -m "not live and not perf" -rA | 3.13 | 10893 passed, 1 skipped, 37 deselected, 14 xfailed in 455 s; exit=0. SUMMARY line added by hand (chain 1 died after pytest ended) | full-313.txt, full-313.xml |
| same | 3.12 | 10893 passed, 1 skipped, 37 deselected, 14 xfailed in 722 s; exit=0 | full-312.txt, full-312.xml |
| pytest -m perf, the 5 files named in ticket step 1 | 3.13 | 13 passed, 213 deselected in 70.9 s; exit=0 | perf-313.txt |
| tests/redact_mutants.py (all 42 rows) | 3.13 | "42 of 42 good; problems: []", exit=0; git status --porcelain empty before and after | mutants.txt |
| fail-before: head's 5 new/changed test files vs redact.py, runmap.py, defaults.py from the P1a parent 2572847 (PYTHONPATH to the old src) | 3.13 | 65 failed, 2 errors, 18 passed, 6 xfailed; exit=1 (per-row labels A/H/R/U NOT checked) | failbefore.txt |

## Slips of this run (raw files kept, marked WRONG)
- failbefore-WRONG-parent-ec5ecd6.txt: used HEAD^1 (P2d-1's own earlier commit); 87 passed. Wrong parent.
- failbefore-WRONG-imports-wt-src.txt: right parent, but the venv imports the snapshot's src (editable install), so the old source was not used; 87 passed. Fixed with PYTHONPATH=old/src; the final failbefore.txt shows the 3-file srcdiff in failbefore-srcdiff.txt.
- The first chain script died after the 3.13 full run ended (cause not found); chain 2 (run2.sh) lost the perf step (function undefined); chain 3 (run3.sh) ran perf and fail-before. Scripts: run-chain1.sh, run-chain3.sh.
- The 3.13 SUMMARY line was written by hand from full-313.xml.

## NOT RUN
- Ticket step 0 (blocking gate: the Windows failing test of 748849c, ruff on P2d-1 head per ticket), step 2 per-row A/H/R/U label check, step 3 first-run of N8 alone on a copy, spy counts of DM-1/DM-1b read out, step 4 class-level probes (p4, p8, p11-p14), step 6 cost measurement (CPU/wall of HOSTILE-1/2 shapes), step 7 build-time items (a)-(f), the sha256 print of redact.py, Python 3.14.
- Command 1 of the ticket (only redaction test files, 0 skips required): not run separately; the full suite shows 1 skip (tests/contracts/test_llm.py:95, Stubber) on both versions.
- ci.yml jobs: semgrep, zizmor, pip-audit, trivy, Vault contract tests (no Vault server).
- tests/stage_mutants.py and tests/textnorm_mutants.py (P1a's mutants): not named by the P2d-1 ticket.
- Test-name hits for "password=" in the full logs are fixture names (fake data); no other secret pattern checked beyond gitleaks.
