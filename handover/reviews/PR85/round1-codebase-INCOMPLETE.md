# PR 85 (P5b2) round 1 codebase review, head 4b1b3f9: INCOMPLETE (snapshot had no ticket/evidence/CLAUDE.md; fixed in snapshot now, re-review needed). Partial findings, condensed:
- B1 CHANGELOG.md:512 says corpus not changed, CORPUS_STEP stays R1P; code has CORPUS_STEP="R3a" (c18a_hostile_corpus.py:27; test_provider_errors_wire.py:780-788).
- M2 CHANGELOG:510 "no change under src/" but migration_numbers.py:80-102 MigrationNumberError changed; M2a untested message/cap? M3 CHANGELOG:507 stale R1P. M4 "46 mutants" unverified (~35 counted).
- N5 FOREIGN_LIMIT=28 zero headroom; N6 xfail(strict) documents open gap.
Not read: tools/gen_config_error_sites.py, mutants file, CSV classes, test file lines 1131+, all ConfigError src sites.
