# checkpoint-D1 (lane D1: tests/, except tests/demo_askdata)
Audited sha: b4cce5b. Written 2026-11-16 07:07 UTC (12:37 IST). pytest NOT run: nothing below says a test passes.

## Done (all opened by me, not copied from evidence)
- Test-to-module map by group (evidence 4a), src modules with no test importer (4b, 6 opened), unresolved test imports (4c, 1 opened), serial test files (9i, ratios plus own identical-body scan), vendor-import guard test read in full against a fresh AST scan of real `src/` imports.
- Weak-test scan: AST scan of 1419 test functions (tests/ minus demo_askdata); 12 had no direct assert, 8 only trivial asserts; all 20 opened. Plus a seeded sample of 26 test bodies across groups opened (see map-D1.md, section "assert-nothing sample").
- Fixtures: every file under tests/fixtures located in a reader (grep), except the 25 hash-named files in tests/fixtures/recorded (checked by reading their generator, not by hashing).
- Claims: README.md "Limits and trust" and SECURITY.md claims matched to test file:line.

## Final status (07:40 UTC)
- map-D1.md written. findings-D1.md and claims-D1.md were REFUSED by the Write tool ("Subagents should return findings as text, not write report files"); their full content is in the hand-back message to the lead, who must save them. I did not work around the refusal.

## Blockers
- None. NOT-AUDITED: tests/demo_askdata (lane D2); the 25 recorded-answer files are not matched one by one to their test (needs sha256 of redacted input = needs running repo code).
