# P0e memo 5: file-overlap table for the v1 code packages, and the hot-file order check (plan-v3 rule 10)

Author: research agent (read-only), 2026-11-05. Base `origin/main` = ce70eb5.
How reliable: the file lists are of two kinds. (A) MEASURED: the changed files of each source branch (`git diff --name-only $(git merge-base origin/main <ref>) <ref>`, CHANGELOG.md excluded from the pair list below because every PR touches it). (B) EXPECTED: for packages that are rebuilt (P3a, P4a-P4d, P5a-P5b5, P6a, P6b) I list the files their work-package text and the cited line numbers point at (`WORK-PACKAGES.md` C2/C3/C4a/C8, `c18a-redesign/design-v3.md` sections 5-9, plan-v3 section 4 rule 9 and notes). Those are a reading, not a measurement; the builder's ticket must replace them with the real list. Nothing was executed. Lead: run `egm:egm-review-loop` on this memo.

## 1. Source branches: measured overlaps (files shared between two branches, CHANGELOG excluded)
| Pair | Shared files |
|---|---|
| #41 (K6) vs #48 | app.py, cli.py, models.py, runtime/agent_loop.py, store/memory.py, store/migrate.py, store/postgres.py, store/protocol.py (8) |
| #41 vs #49 | models.py, store/memory.py, store/migrate.py, store/postgres.py, store/protocol.py, tests/test_k2_migrations.py, tests/test_p2_postgres.py (7) |
| #48 vs #49 | limits.py, models.py, store/memory.py, store/migrate.py, store/postgres.py, store/protocol.py, tests/contracts/test_store.py (7) |
| #43 vs #48 | config.py, llm/{anthropic,bedrock,common,gemini,openai_compat,protocol,retry}.py, models.py (9) |
| #48 vs c1a (8460813) | backends/table.py, config.py, registry.py, tests/test_p1a_fixes.py (4) |
| #48 vs c18a (198a6b6) | cli.py, config.py, extract.py, llm/anthropic.py, registry.py (5) |
| #49 vs #50 | approvals/gate.py, guard/textnorm.py (both ADD it, different content), limits.py, tests/fixtures/textnorm_vectors.json (4) |
| #48 vs #50 | limits.py, tests/warden_port/test_redaction_review2.py (2) |
| #50 vs c1a | guard/redact.py (1) |
| c1a vs c18a | config.py, registry.py (2) |
| #41 vs c18a | cli.py, runtime/tick.py, tests/test_p7_tick.py (3) |
| #41 vs c1a | deferred.py, tests/test_k3_pilot_env.py (2) |
| #43 vs #47 | demos/ask-your-data/README.md (1) |
(#47 vs #48: pyproject.toml; #47 vs #50: .gitattributes; #43 vs c1a/c18a: config.py. `pr/50` and `handover-src/pr50-local-748849c` differ by `audit/labelkey.py`, `errors.py` and 3 `test_pr50_fix_batch*.py` files.) The c18a branch is the OLD diagnostics design (new design rebuilds it on ce70eb5, P5a); I used it only as a hint of where the new design will land. Note: `guard/safe_message.py` exists only on that branch; **it does not exist on main**, so P5b5 ("R5: delete old machinery") has nothing to delete unless P5a-P5b4 re-create it. P0e item for the lead: confirm P5b5's scope (the design says "R5 deletes old fold/vote machinery", `design-v3.md` lines 68 and 73, but the plan rebuilds R1 on ce70eb5, which has none).

## 2. Package-by-file table (v1 code rows)
`S/` = `src/hadavin_sdk/`. M = measured from a branch diff; E = expected. "new" = file created by the package.
| Package | Basis | Core files expected to be touched |
|---|---|---|
| P1 text folding | M (#50 pieces) | S/guard/textnorm.py (new), S/guard/_confusables.py (new), tools/gen_confusables.py, tools/data/confusables.txt, tests/fixtures/textnorm_manifest.json, tests/fixtures/textnorm_vectors.json, new tests/test_textnorm_differential.py, .gitattributes, CHANGELOG.md |
| P2a stop state (3 PRs) | M (#50) + E (fix of failing test, weak mutant) | S/runtime/stop_gate.py (new), S/runtime/rowstore.py (new), S/runtime/config_view.py (new), **S/limits.py** (#50 adds `is_stopped()`, `stop(by, source)`, `reset(by, source)`), tests/test_promoted_controls.py, tests/promoted_mutants.py, tools/mutation_runner.py, S/testing/mutation.py, CHANGELOG.md |
| P2d redact patterns | M (#50) | S/guard/redact.py, tests/warden_port/test_redaction{,_bank,_classes,_review,_review2,_review9}.py, tests/test_k5_round12_fuzz.py, CHANGELOG.md |
| P3a migration rule | E | S/store/migrate.py, tests/test_k2_migrations.py, new tests/test_migration_numbers.py, .github/workflows/ci.yml (lead only), CHANGELOG.md |
| P4d store contract suite | E | S/store/postgres.py, S/store/migrate.py (only if SQL composition moves, see memo 3), tests/contracts/test_store.py, tests/contracts/kinds/store_postgres.py, tests/test_lockin_guard.py (line 69), tests/test_p3b_neutral_audit.py (line 310), CHANGELOG.md |
| P4a usage, refuse-not-estimate, price tiers (3 PRs) | E (C2 `llm/common.py` l.163-168; C3 `llm/anthropic.py` l.142, `llm/bedrock.py` l.176; C4a `config.py` l.49-53) | S/llm/common.py, S/llm/protocol.py, S/llm/anthropic.py, S/llm/bedrock.py, S/config.py, S/models.py, CHANGELOG.md |
| P4b meter | E (+M from #48 `llm/metered.py`, `limits.py`, store files) | S/llm/metered.py (new), **S/limits.py**, S/store/protocol.py, **S/store/memory.py**, S/store/postgres.py, **S/store/migrate.py** (GRANTS, maybe a new migration), S/config.py, demos/ask-your-data/askdata/meter.py, tests/contracts/test_store.py, CHANGELOG.md |
| P4c run cap + alert | E (agent_loop.py:245 reads `max_run_usd`; registry.py:53 defines it) | S/runtime/agent_loop.py, **S/limits.py** (alert hook), **S/registry.py**, CHANGELOG.md |
| P5a diagnostics R1 | E (design-v3 section 9) | S/errors.py, new diagnostic modules (`diagnostic.py`, `diagnostic_schema.py`), new tests/test_diagnostics_hostile.py + tests/data/c18a_hostile_corpus.py, CHANGELOG.md |
| P5b1 R1P provider plumbing | E (design-v3 section 5) | S/llm/protocol.py, S/llm/retry.py, S/llm/common.py (`provider_facts`), tests, CHANGELOG.md |
| P5b2 R3a classification | E (design-v3 section 6) | tests/data/config_error_sites.csv (new), a generator script (new), a CI test (new) |
| P5b3 R3c+R3b | E (design-v3 section 9: cli 11, tick 10, extract 4, config 3, registry 2, anthropic 2, injection 2) | S/cli.py, S/runtime/tick.py, S/extract.py, **S/config.py**, **S/registry.py**, S/llm/anthropic.py, S/guard/injection.py, S/errors.py (`ConfigError.from_cause`), tests |
| P5b4 R2 logging layer | E (design-v3 section 7) | S/cli.py (`bootstrap_logging()` first statement of `main()`), S/runtime/tick.py (`_GuardedStream`), a new logging module, tests |
| P5b5 R5 delete old | E | S/errors.py, S/guard/injection.py, docs; see the safe_message note in section 1 |
| P5c redactor + masked model + put-back (4 PRs) | M (c1a-8460813: backends/builtin.py, backends/table.py, config.py, deferred.py, guard/__init__.py, guard/redact.py, guard/redactor.py (new), registry.py, tests/test_c1a_redactor.py, tests/test_k3_pilot_env.py, tests/test_lockin_guard.py, tests/test_p1a_fixes.py) + E (C1b-d: llm wrapper, `evals.py`, `runtime/agent_loop.py`, `k1b/loop.py`, `extract.py`; C1f put-back) | as listed; adds S/backends/table.py, **S/config.py**, **S/registry.py**, S/guard/redact.py, S/runtime/agent_loop.py, S/extract.py |
| P6a client-profile gate | E (config.py:368 uses `DEV_ONLY`; table.py:593 defines it) | **S/config.py**, S/backends/table.py, S/app.py, S/deferred.py, new tests/test_client_profile.py, tests/test_lockin_guard.py, CHANGELOG.md |
| P6b no-training lock, secret boundary, identity/rights, env lint | E (plan-v3 rule 9(e)-(g); env uses in memo 6) | S/llm/anthropic.py (and other llm backends), S/backends/table.py (`identity`, `rights`, `dev_only` fields), S/actions/secrets_env.py, S/actions/secrets_vault.py, S/audit/signer.py, S/cli.py, S/store/postgres.py, S/app.py, 4 new tests (`test_training_lock`, `test_secrets_import`, `test_env_lint`, `test_kind_identity`), tests/test_lockin_guard.py |
Not in a v1 row: PR #50's other files (`approvals/gate.py` + `tests/warden_port/test_gate*.py` (4 files), `guard/http.py`, `guard/runmap.py`, `tools.py`, `audit/capped.py`, `guard/egress_text.py`, `testing/contracts.py`, `docs/promoted-controls.md`, README, SECURITY.md). They are P2b/P2c (v1.1) or P0d "disposition". Important: P1/P2a/P2d as written would merge a PR #50 that is smaller than #50; `guard/redact.py` in #50 uses `textnorm` (P1) so P2d depends on P1 (the plan has it), but `approvals/gate.py` edits in #50 are tied to `tests/warden_port/test_gate*.py` and to `limits.py`; the P0d disposition must say which row owns them or they are dropped.
P8a/P8b/P8c, P0*, P6b-test additions to CI: report/tag/tool rows; they touch `tools/` and `docs`, not the hot files (P8c adds `tools/proof_pack.py`).

## 3. Pairs of v1 packages that share a file (from the E/M lists above; CHANGELOG.md excluded)
| Pair | File(s) | Are they ordered by plan-v3 section 7? |
|---|---|---|
| P3a / P4d | store/migrate.py | yes (P3a step 4, P4d step 5), same as rule 10 |
| P3a / P4b | store/migrate.py | yes |
| P4d / P4b | store/postgres.py, store/migrate.py, tests/contracts/test_store.py | yes (P4d step 5, P4b step 6; P4b depends on P4d) |
| P4d / P6b | store/postgres.py (env read at line 56), tests/test_lockin_guard.py | P4d step 5, P6b right after P4a: **not forced** (P6b depends on P4a only) |
| P4d / P5c, P4d / P6a | tests/test_lockin_guard.py | P5c/P6a are later steps; ordered in practice |
| P2a / P4b, P2a / P4c | S/limits.py | P2a step 5 vs P4b step 6: ordered by step, **not by a Depends-on**; and **P2a is not in rule 10's order list** |
| P4b / P4c | S/limits.py | yes (P4c depends on P4b) |
| P4a / P4b | S/config.py | yes (P4b depends on P4a) |
| P4a / P5b1 | S/llm/common.py, S/llm/protocol.py | P5b1 (step 6) after P4a (step 5) by step; **no Depends-on** (P5b1 depends on P5a only) |
| P4a / P5b3 | S/llm/anthropic.py, S/config.py | same remark |
| P4a / P6b | S/llm/anthropic.py, S/llm/bedrock.py | yes (P6b depends on P4a) |
| P4a / P5c, P4a / P6a | S/config.py | P5c, P6a are later |
| P4b / P5b3, P4b / P5c, P4b / P6a | S/config.py | P4b and P5b3 are in the SAME step (6): **unordered** |
| P4c / P5b3 | S/registry.py | both step 6: **unordered** |
| P4c / P5c | S/runtime/agent_loop.py, S/registry.py | P4c step 6, P5c step 7; no Depends-on |
| P5a / P5b3 / P5b5 | S/errors.py | chain by Depends-on (P5a -> P5b1 -> ... -> P5b5): ordered |
| P5b3 / P5b4 | S/cli.py, S/runtime/tick.py | yes (P5b4 depends on P5b3) |
| P5b3 / P5b5 | S/guard/injection.py, S/errors.py | yes |
| P5b3 / P5c | S/extract.py, S/config.py, S/registry.py | yes (P5c depends on P5b5) |
| P5b3 / P5b4 / P6b | S/cli.py, S/llm/anthropic.py | P6b vs P5b3/P5b4: **no Depends-on**; P6b starts at step 5, P5b3/b4 at step 6 |
| P2d / P5c | S/guard/redact.py | yes (P5c depends on P2d) |
| P5c / P6a, P5c / P6b | S/backends/table.py, S/config.py, S/deferred.py, tests/test_lockin_guard.py | P6a depends on P5c: yes; P6b vs P5c: **no Depends-on** |
| P6a / P6b | S/backends/table.py, S/app.py, tests/test_lockin_guard.py | P6a (step 7) after P6b (step 5) by step only |

## 4. Hot-file order check against plan-v3 rule 10
Rule 10 text: "`limits.py`, `store/memory.py`, `store/migrate.py`, `config.py`, `registry.py`, `CHANGELOG.md` are changed in this order: P3a, P4d, P4a, P4b."
Which v1 packages touch each hot file (measured or expected, section 2):
| Hot file | Touched by (v1) | Verdict against rule 10 |
|---|---|---|
| `store/migrate.py` | P3a, P4d (maybe), P4b | consistent with the order P3a -> P4d -> P4b |
| `store/memory.py` | P4b only (v1); later P3b (#49), P3c (#41), P7a/b/k | consistent; add "then P3b, P3c, P7a" for v1.1 |
| `limits.py` | **P2a**, P4b, P4c | **gap**: rule 10 names P4b only; P2a (before) and P4c (after) are missing; all three are real (measured: #50 edits limits.py, #48 and #49 edit it) |
| `config.py` | P4a, P4b, **P5b3, P5c, P6a** (and P6b if it adds profile fields) | **gap**: rule names P4a, P4b only; P5b3 (step 6) and P4b (step 6) are unordered; P5c and P6a follow by Depends-on |
| `registry.py` | **P4c, P5b3, P5c** | **gap**: not one of them is in the order list; P4c and P5b3 are both step 6 and unordered |
| `CHANGELOG.md` | every v1 code package (17 of them) | handled by the append-only rule + lead resolving conflicts |
Missing from rule 10 although measured as shared by 3+ rows: `backends/table.py` (P5c, P6a, P6b; also every kind package if rule 9(f)/(g) puts `identity`/`rights`/`dev_only` in its `Entry`), `tests/test_lockin_guard.py` (P4d, P5c, P6a, P6b), `cli.py` (P5b3, P5b4, P6b), `llm/anthropic.py` (P4a, P5b3, P6b), `runtime/agent_loop.py` (P4c, P5c), `llm/common.py` and `llm/protocol.py` (P4a, P5b1), `errors.py` (P5a, P5b3, P5b5), `app.py` (P6a, P6b), `store/postgres.py` (P4d, P4b, P6b).
Section 7 puts P4a, P2d, P5a in one step and P4b with P5b1 in the next: so `P4b` and `P5b1` run in parallel (they share no file; fine) but `P4b` and `P5b3` can overlap on `config.py`, and `P4c` and `P5b3` on `registry.py`.
Recommended amendment text for rule 10 (for the lead): "Hot files are changed in this order: limits.py: P2a, P4b, P4c. store/migrate.py: P3a, P4d, P4b. config.py: P4a, P4b, P5b3, P5c, P6a, P6b. registry.py: P4c, P5b3, P5c. backends/table.py: P5c, P6b, P6a. tests/test_lockin_guard.py: P4d, P5c, P6b, P6a. cli.py: P5b3, P5b4, P6b. A package that changes a listed file waits until the earlier packages of its list are merged or its work is rebased on them." Where the order contradicts a Depends-on (P6b starts at step 5 but its files overlap with P5b3/P5b4/P5c), either add Depends-on edges (P6b after P5b4 for cli.py and after P5c for table.py) or move P6b's `cli.py`/`table.py` parts into a later PR (P6b is 1 package in the plan; N PRs would be needed).

## 5. Findings the lead should act on
1. Rule 10 is incomplete (section 4). Without the amendment, "two packages that change the same file are never in progress together" cannot be applied mechanically.
2. P2a, P4b, P4c all edit `limits.py` while rule 10 lists only P4b.
3. P5b5's job may be empty on a ce70eb5 base (no `safe_message.py` on main). Check before the ticket is written.
4. P1/P2a/P2d together do not cover all of PR #50; the rest needs the P0d disposition (including `approvals/gate.py`, `guard/http.py`, `guard/runmap.py`, `tools.py`, `audit/capped.py`).
5. Expected file lists for rebuilt packages are my reading of line numbers; the builder's ticket must list the real files and the lead must diff the lists against this table at ticket review.
Not verified: any list marked E; whether P6b's lint test needs `pyproject.toml` or CI changes (CI files are lead-only).

R-numbers cited: none. Files changed: this file only. Head SHA read: origin/main = ce70eb5; branch refs as named in section 1.
