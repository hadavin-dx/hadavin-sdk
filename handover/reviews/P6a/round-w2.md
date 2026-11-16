# PR72 core/P6a head 0ae044b (P6a-1 only), result review, wave 2

Two fresh reviewers read /tmp/snap/core_P6a-0ae044b/DIFF.patch, the ticket and the evidence TABLE.md. Neither ran code.
Path class: least privilege (uncapped).

## Design critic: 0 Blocker, 3 Major, 5 Nit
- M1 tools/p6a1_mutants.py fails `ruff check` (14 errors: EXE001, S603, S607, PLW1510). CI scope (src tests demos) skips tools/, yet a repo test already scans tools/ as product code.
- M2 Private process ids still in public text: test_t7f docstring says "mutant 50" (number wraps to next line), ticket row ids in banners and test names, tools header names "PR 72", "R2-01" and the lost runner's history.
- M3 Strict-bool sweep over 7 extra src files (models.py, replay_records.py, tools.py, actions/contract.py, backends/table.py, config.py) plus tests/test_strict_flags.py (232 lines) is outside the ticket. No old-code run for it at this head.
- Nits: weak CLIENT_REVIEWED reasons; S2 is an accident guard, not a boundary (aliased build not seen); 17 invented mutants (56-72) killed by "any failing test"; no fail-before table at this head; process facts (CI, CodeQL, Sonar, CodeRabbit, gitleaks, Vault not run; Postgres 16 local vs 17 CI).

## Codebase-details: 0 Blocker, 4 Major
- M1 tests/test_client_profile.py:444-445 import `LOCAL_DETECTORS` and `_sends_text_out` at module level, so on the base the whole file fails at collection. The ticket's import rule is broken and a fail-before table (19 fail, 19 pass) cannot be produced.
- M2 Same ruff failure and lint scope gap as above.
- M3 Mutant counts inconsistent: header says "45 from records" (really 41), "73" is an id not a count, mutant 73 labelled invented but has a killer, id 57 collides with the by-hand script, 61 and 62 target tests outside the baseline run, ticket body still says 35 mutants, no recount file.
- M4 Strict-bool sweep not in the ticket (same as design M3).
- Nits: unquoted YAML `yes` still turns made_up_data_only on (no row pins it); CHANGELOG calls the S6 rule "bedrock_guardrail" though the code is an allow-list; `given = dict(locals())` guarded only by a comment; a test of a test stub is padding; ticket errata still says dev vs DEMO_ONLY.
- Stage names (R449): pass. Reuse: good. Default deny, S2 order, no secrets: found sound.
