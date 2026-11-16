<!-- full hand-back report of sub-agent a5cfa82b, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

Q8c-1 FIX BATCH 2: pushed fast-forward, new head 6bdfadc139e23f8d80627c849c4e1c033917622e (a77fab72..6bdfadc1) on core/q8c-1-policy-vault-kubernetes. Not independently reviewed.

WHAT IS NOT DONE OR NOT VERIFIED (first)
1. The 12 Vault server tests were not run. No vault/bao/openbao binary exists here and I downloaded nothing. OpenBao was not run. The page says "not run yet". A CI run with HADAVIN_REQUIRE_VAULT_ENGINE=1 and `-rs` output showing 12 passed, 0 skipped is needed; this is appended to handover/questions-for-lead.md.
2. The R17 `+` claim is still read by the earlier builder only. It is now `claims_unverified=("the + matches exactly one whole path part, nothing deeper",)`, so the page shows it as "not yet checked" and gives no copy-ready text for that kind. The same wording now covers the never entries undelete, subkeys and byok-export (`verified: None`, with PENDING_NAMES dated entries). No guard was removed.
3. The sources fixture header lists 12 rows with full 40-char ids. The 7 Vault doc rows (V-POL, V-TOK, V-KV, V-TR, V-API, V-APPROLE, V-K8S) have only 7-char ids, because the GitHub API refused here. I did not guess them. The fixture header lists what an evidence runner must re-read: V-POL/B-POL, V-ACL/B-ACL, V-PARSE, V-KV/B-KV/V-TR/B-TR. V-ACL, V-PARSE and B-ACL were not re-fetched. The OpenBao release for the doc rows was not looked up.
4. The full suite has one failure that is not from this branch. tests/demo_askdata test_validate_harm [dblink-connect] failed: the dblink connect tried the default /var/run/postgresql socket. The evidence runner showed it also fails alone on clean origin/main. I did not re-run it on main myself, and I identified the failing test from the error text because `-rs` did not print the FAILED line.
5. Of the 45 mutants, 35 have a weak first-line check, because the killer asserts through `same()`, which puts the expected text in its own message. The run now prints the weak count and the shared killers.
6. Fail-before limit: the new guard-rule tests live in the test file, so they pass on old src. For those, the proof is the mutants. The minors cross-check (Vault never-path vs grants) was not done.
7. CodeQL, Sonar, CodeRabbit and CI were not run.

EVIDENCE
- Guard, docs and engine tests: 293 passed, 12 skipped.
- policy_mutants: 45 of 45 good, exit 0 (41 old plus 4 new: sender pin, paging query text, settings flow, `.call` outside the Vault modules). stage_mutants: 37 of 37 good, exit 0.
- Fail-before on the a77fab72 tree with the new test files over old src/tools: 8 failed, 279 passed in guard+docs. The failures include the unchecked-claim tests, the page-default test, m16, a source-id test and the page-limits test. Mutating `_NAME` to admit `%+?#*` fails 11 of 13 cases; space and newline stay refused by the mutated regex.
- Full suite via heavy.sh with my own Postgres 16: exit 1, 1 failed (the dblink test above), 10816 passed, 13 skipped, 28 deselected, 353.8 s.
- ruff check exit 0; ruff format --check exit 0 (328 files); bandit -ll -r src tools exit 0 (Low 12, Medium 0, High 0); scan_repo.py exit 0; policy_page.py --check exit 0 (docs/declared-permissions.md regenerated); gitleaks origin/main..HEAD exit 0.

WHAT CHANGED
- Minors fixed: query-name regex plus `_items` query check; one Request/open pinned in VaultProvider.call, with `.call` callers allowlisted by (file, receiver); `_NAME` test parametrized; AST test of `build` settings plus the namespace check; "whose first part is" wording; a sentence that Vault calls signing `update` and stores nothing, plus a column legend; OpenBao-not-run trigger (BL-core-q8c1-openbao, review date 2026-12-11); BL-core-q8c1-lifetime row for long-lived tokens; stale-allowlist message says to move the line in SHAPES; README assertion scoped; `page(root=None)`; non-ASCII char escaped; CHANGELOG updated.
- Ledger rows BL-core-q8c1-lifetime, BL-core-q8c1-openbao and Q8c-1-r2-fb2 (FIXED-UNVERIFIED) are appended to /home/user/hadavin-sdk/handover/ledger.md.
- Uncommitted in the main checkout for the lead to commit: handover/ledger.md and handover/questions-for-lead.md. The evidence folder handover/evidence/Q8c-1/a77fab7/ is also untracked there. The pushed commit holds only the 10 worktree files.
- Cleanup: my Postgres cluster is stopped and its directory removed; no stray processes of mine. The evidence runner's leftover worktrees (/home/user/build/EV-Q8c1-a77fab7*) are not mine and were left alone.
- Checkpoint note: /home/user/build/checkpoints/B-Q8c1-b2.md.
