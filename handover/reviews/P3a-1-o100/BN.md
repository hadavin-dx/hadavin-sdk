# Ticket errors and unclear points found in ORDER 100 for P3a-1

1. Ticket P3a says statement_text returns a pair; fix 1 had made it return str. Restored. For P3a-2: `statement_text(text, True)` and `lex(...)` both return the pair; the str-raising form is `checked_statement_text`. P3a-2's migration_numbers.py still has hand_recipe calling `statement_text(text)` as a str: after merging core/P3a it must read `checked_statement_text(text)` (a tuple there would raise AttributeError, loudly).
2. The module test file was renamed tests/test_migration_numbers_fix1.py -> tests/test_migration_numbers_guards.py. BN-P3a-2-c in reviews/P3a-2/BN.md names the old path; P3a-2 will need the rename on merge. tests/fixtures/timing.py lost FLOOR_S; P3a-2 and anything else importing it must use tests.fixtures.timing.is_superlinear / grows_faster_than_size.
3. Ticket has no tickets/P7.md; item 2 could only grep the tickets that exist.
4. AK-G15-b/AK-G2 BN-28 plan GRANT/REVOKE of a role membership in "-b's migration"; with the refusal list a .sql file doing that is refused. Roles are migrate() arguments, so it must be Python; the ticket should say so.
5. The 15+ PostgreSQL version assumption has no source in the tickets I read; documented as an assumption.
6. Ticket says docstring/evidence pointers into P3a-fix1-evidence/ ; that folder is outside the repository, so repository text must not cite it.
7. handoff/later-fixes.md does not exist in the handover checkout.
