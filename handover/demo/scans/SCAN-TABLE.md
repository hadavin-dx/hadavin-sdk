# Q6 scan table (EVIDENCE RUNNER: commands run and output recorded, no judgement)

Repo hadavin-dx/duplicate-proof-lead-desk-n8n, clone /tmp/work/q6-clone, run 2026-11-13 (UTC). gitleaks 8.30.1 (/tmp/work/gl/gitleaks), python /tmp/work/int2-venv, ruff 0.16.9 (/root/.local/bin/ruff, not the dev-lock one).
Branch SHAs at start and end of run were identical (evidence-q6-branches-start.txt, evidence-q6-branches-end.txt). Rows with any non-zero exit are listed first. Raw output per head: evidence-q6-<branch>.txt. Re-run: ./scan-heads.sh [branches] (rewrites scan-rows.tsv and the evidence files).

| branch | head sha | gitleaks dir (exit, findings) | gitleaks git (exit, findings; top rule ids) | hygiene scan | test_hygiene | ruff | notes |
|---|---|---|---|---|---|---|---|
| cfg-review-tools | 30b555d72aa1 | exit=0, 0 | exit=1, 2; generic-api-key(2) | n/a | n/a | n/a | toml=none; no tools/hygiene.py, no ruff config |
| cfg-sonar | 53daf3787cb7 | exit=1, 1 | exit=1, 2; generic-api-key(2) | n/a | n/a | n/a | toml=none; no tools/hygiene.py, no ruff config |
| initial-code | 43110e75b8ad | exit=0, 0 | exit=1, 325; long-hex-token(313) hardcoded-hostname(10) generic-api-key(2) | exit=0, 0 findings | exit=1; 1 failed, 9 passed in 11.31s | check exit=0; format exit=0 | toml=present |
| main | a0b97a4a6ee7 | exit=1, 1 | exit=1, 2; generic-api-key(2) | n/a | n/a | n/a | toml=none; no tools/hygiene.py, no ruff config |
| pr-1-code | d23cf8f0c470 | exit=1, 1 | exit=1, 325; long-hex-token(313) hardcoded-hostname(10) generic-api-key(2) | exit=0, 0 findings | n/a | check exit=0; format exit=0 | toml=present |
| pr-2-demo-folder | f31e2619ad51 | exit=1, 1 | exit=1, 325; long-hex-token(313) hardcoded-hostname(10) generic-api-key(2) | exit=0, 0 findings | n/a | check exit=0; format exit=0 | toml=present |
| pr-3-tests | 2db392650e8b | exit=0, 0 | exit=0, 0; none | exit=0, 0 findings | exit=0; 15 passed in 14.92s | check exit=0; format exit=0 | toml=present |

Notes on how the cells were made:
- gitleaks dir: run on a `git archive` of the head (tracked files only). gitleaks git: run on a detached worktree of the head (history reachable from that head). Both with the head's own .gitleaks.toml (picked up automatically from the scan folder; "toml=none" means the head has none). I added `--redact -r <json> -f json` to the exact commands so counts and rule ids could be read; the count is gitleaks' own "leaks found: N" line.
- tools/hygiene.py has no command-line entry point (no main). The "hygiene scan" cell is the same call tests/test_hygiene.py makes: `hygiene.pipeline(repo, patterns.txt, exceptions.txt)` in the checkout; exit 1 would mean findings listed.
- main and cfg-* heads have no pyproject, no hygiene, no tests; pr-1-code and pr-2-demo-folder have hygiene.py but no tests/test_hygiene.py. Recorded as n/a, not as failures.
- initial-code test_hygiene: 1 failed, 9 passed; the failing assertion is "gitleaks git reported findings" (325 findings, see row); detail in evidence-q6-initial-code.txt.
- main (and any head without .gitleaks.toml) gitleaks dir shows 1 finding; I did not open which file (not asked; detail would need the unredacted or JSON report).

What was not run: pytest beyond tests/test_hygiene.py (no full suite, no test_codeant_hygiene/test_gitleaks_exceptions); bandit, mypy; ruff via `uv run` (used the standalone ruff 0.16.9); CI-side checks (CodeQL, Sonar, CodeRabbit); heads of forks or PRs not in `git branch -r`; gitleaks without --redact/json (so output format differs from the CI command); unredacted finding locations.

Q6 rule: re-run scan-heads.sh whenever the lead pushes a head (one line per head goes to scan-rows.tsv).
