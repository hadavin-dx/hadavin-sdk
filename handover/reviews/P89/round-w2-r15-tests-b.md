# PR89 round 15, reviewer tests-B (egm-implementation-readiness), head 13b7124
Coverage: keyword test file 1330-2657 of 2657; runner 300-486 and 645-675 plus helpers. Read-only, nothing run (traced by hand).
Result: no Blocker/Major in slice. 32-case table traced by hand: all 32 expected values right (6 parsed, 26 unparsed). Property test reaches both outcomes. r14-01, r14-03 fixed; r14-02 right now.
Minor:
- t-01 2505-2548: generator never builds a space directly followed by host=/dbname=/port=/hostaddr= after a password part; pwd=, passwd=, PASSWORD= not pinned by any lock-name row (a mutant dropping "pwd" passes). Add table rows.
- t-02 2519-2545: counter calm_pairs>=300 counts all forms; forms 4-9 are vacuous (~240 of 360). Count real pairs for forms 1-3 and hostile passwords by outcome.
- t-03 2318-2322: both key=value values use ssl+password so both "unparsed"; comparison shows nothing. Drop or make explicit.
- t-04 2447-2449: table assertion message lacks row index (not value).
Nit: 2430 fake password word as one literal (build from parts); 1908 comment "two cases" but one; 2276-2277 "second depth" should be third; 2564-2566 repeats 2388; 1730 string starts with space so plain path; 2381 loose startswith; 2471-2473 docstring-word check; wall-clock bounds 2602, 2630 (<2 s), 2621 (<5 s) could flake; two seeded generators; lock-file tests all map to "unparsed" (harmless).
