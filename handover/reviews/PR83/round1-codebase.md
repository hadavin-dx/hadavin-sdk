# PR 83 (P0t-followup) round 1, egm-codebase-details, head 7f24178 (condensed). Reading only; DIFF.patch not read.
Blocker: none found in what was read.
- M1 Gate evidence (bandit, ruff, scan_repo, pytest tails, mutants) carries sha 72389db, not head 7f24178; scan_repo.txt has only the sha line. Re-run on 7f24178 or prove equal tree.
- M2 Scope grew past ticket P0t: new commonwords.py, stages.fold_name/is_stage_name/check_id/check_tenant_id, 5 id types in config.py:65-73, 608 test lines (test_tenant_ids.py); CHANGELOG says guards no live path; is_stage_name has no src caller. Needs own ticket or order reference (orders 126/132 only in test comments). fold_name duplicates guard.runmap.canonical (pin test only).
- M3 Mutant runner does not copy root CHANGELOG, so M11 "KILLED" claim is doubtful; no mutants for check_id/fold_name/29 words in mutants.txt.
- N1 ticket superseded by BN-fix1 (annotate); N2 fail-before shows 3 failures only; N3 ticket drift (15/34/52 tsv rows, len==3 hardcode); N4/N5 plain-wording of CHANGELOG and stages.py:61 message.
Passed: 29 words claim; single _COMMON list; 4-char rule; TENANT regex; is_live/is_prod fail closed.
Not checked: k1b/redaction.py own word list (sibling), DIFF.patch, full CHANGELOG.
