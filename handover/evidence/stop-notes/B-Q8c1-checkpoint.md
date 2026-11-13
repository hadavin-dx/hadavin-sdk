# B-Q8c1 checkpoint (builder of ticket Q8c, PR 1)
## 1. 2026-11-11 about 14:33 UTC (20:03 IST)
start 14:28 UTC. `which vault bao`: neither found (exit 1). Worktree /home/user/build/B-Q8c1 at origin/main 2a8c2aac, venv /home/user/build/venv-q8c1 synced.
Literal `resource` strings for the PR 1 rows (errata E5), written before coding:
| id | kind | name | resource | bound |
|---|---|---|---|---|
| R17 | vault | read | `{mount}/data/{path_prefix}*` | the prefix is this deployment's `path_prefix` setting; it must not be empty |
| R18 | vault_transit | update | `{transit_mount}/sign/{key_name}` | (none) |
| R19 | vault_transit | read | `{transit_mount}/keys/{key_name}` | (none) |
| R20 | kubernetes | list | `apps/deployments in {namespaces}` | (none) |
| R21 | kubernetes | list | `core/events in {namespaces}` | (none) |
| R22 | kubernetes | get | `core/pods/log in {namespaces}` | (none) |
Deviation: section 5 wrote R17 as `<PATH_PREFIX>`; `path_prefix` is a setting of the kind, so by the ticket's own 4.1 definition it is `{path_prefix}` (and the evidence row G35 verified that form).
Ticket facts found false so far:
- E3 "SHA-256 of the saved text; take them from the evidence file": the evidence file holds no SHA-256 and no saved text. I fetched the 21 cited files for the three kinds myself (14:30 UTC) and hashed them; the fixture says so.
- E6 sink list for Kubernetes omits `._items` (the two list calls go through it, kubernetes.py:232, :247); added.
done: reading. next: tool, guard tests, must-fail run on main, literals, engine tests, page, CI variable, gates. blockers: none. sha: 2a8c2aac (nothing committed yet).

## 2. 2026-11-11 14:47 UTC
done: tools/policy_page.py; tests/test_policy_guard.py (84 tests with the engine file: 84 passed, 11 skipped locally); tests/test_policy_engine.py (11 Vault server tests written, skipped here, required in CI); three POLICY literals (appended at the END of each module so the allowlisted line numbers of the ticket stay true); docs page; sources fixture; CI variable in both jobs; tests/policy_mutants.py 14 of 14 good; README and CHANGELOG. Must-fail on main's src recorded (2 labelled failures; whole file 65 failed).
next: ruff, format, bandit, scan_repo, ONE full pytest on own Postgres 16 (port 56120), commit, gitleaks, push.
blockers: none. Vault engine tests not run by me (no server here). sha: nothing committed yet (base 2a8c2aac).
proof files: /home/user/build/B-Q8c1-proofs

## 3. 2026-11-11 15:05 UTC
done: committed 7af13809 on core/q8c-1-policy-vault-kubernetes (not pushed yet). ruff check, ruff format --check, bandit -ll, scan_repo, guard family (155 passed, 11 skipped), 14 of 14 mutants: all exit 0 on this tree. Waited the full 15 minutes for other pytest runs (15 to 22 were running the whole time), then started the ONE full pytest anyway.
next: full pytest result, gitleaks, push the new ref, report. Stop Postgres (port 56120) and delete /home/user/build/pg-q8c1.
blockers: none. Vault engine tests not run by me. sha: 7af13809

## 4. 2026-11-11 15:17 UTC (20:47 IST) FINAL
done: full pytest on head 7af13809: 10636 passed, 12 skipped, exit 0 (11 of the skips are the Vault server tests). gitleaks: no leaks found. Pushed new ref core/q8c-1-policy-vault-kubernetes at 7af1380963ed2303d53499b6edef762268c48f58. No PR opened. Postgres on 56120 stopped, /home/user/build/pg-q8c1 deleted; the scratch stand-in server stopped; no process of mine left.
not done: Vault engine tests not run by me (no Vault server here); they run first when CI runs on a pull request.
proofs: /home/user/build/B-Q8c1-proofs. real clock: 49 minutes.

## 5. 2026-11-11 15:50 UTC (21:20 IST) second builder, FIX BATCH 1 on head 7af13809
start 15:32 UTC. done (not committed yet): `+` verified in V-POL, B-POL and in Vault/OpenBao source code (acl.go, policy.go at the commits of tags v2.2.0 / v2.4.0); R17 now `{mount}/data/{path_prefix}+`; guard rules for getattr literal, import list, alias, opener, other modules, kept `self.` in folded paths, Vault grant = path and capability of its request, Kubernetes path and query rule; tool: control characters, duplicate keys, leftover placeholders, reserved values, length limits, data_problems for --check, pinned sources; page renamed docs/declared-permissions.md, "have not run yet" wording; engine tests: teardown, 200/204 control, repr; CI mutant step. Guard + engine files: 241 passed, 12 skipped locally; ruff check and format clean.
next: more mutants, PR notes, fail-before overlays on a clean 7af13809 worktree, own Postgres on 56121, ONE full suite through heavy.sh, gates, commit, gitleaks, push.
blockers: none. Vault engine tests still not run by anyone (no server here). sha: 7af13809 + uncommitted work.

## 6. 2026-11-11 16:05 UTC (21:35 IST) fix batch 1
done: committed a77fab72 (not pushed yet). Full pytest ONCE on a77fab72: 10806 passed, 13 skipped, exit 0 (12 of the skips are the Vault server tests). ruff check, ruff format --check, bandit -ll, scan_repo, policy_page --check, gitleaks: exit 0. Policy mutants 41 of 41 good (run before the commit on the same content). Postgres on 56121 stopped, data folder deleted.
next: stage mutants and policy mutants on the committed head (queued for a heavy slot), push (fast-forward), report.
blockers: none. Vault engine tests not run by anyone. sha: a77fab72
proofs: /home/user/build/B-Q8c1-proofs/fix1 ; PR notes: /home/user/build/B-Q8c1-pr-notes.md
