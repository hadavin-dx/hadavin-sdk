# PR89 round 15, reviewer mutants (egm-implementation-readiness), head 13b7124
Coverage: mutants file 1-519 of 519; meta test 1-194 of 194; manifest 1-10 of 10; runner 434-483 and 1145-1224 plus grep; parts of the keyword and runner test files. Read-only, nothing run.
Result: no Blocker/Major in slice. Counts: 208 mutants (62 + 146) = EXPECTED_MUTANTS; no equivalent mutants found beyond the three the header names; Windows/POSIX header matches skip markers one to one. r14-02, r14-03, r14-04 judged fixed.
Not verified by reviewer: sha256 values in the manifest; the older olds not grepped one by one (covered by the every-search-string-occurs-once test).
Minor/Nit:
- M-01 Minor, mutants 38-40 vs 371: header says the failing-body-plus-teardown test has no mutant, but line 371 is one. Stale sentence.
- M-02 Minor, mutants 38-40: "tests with no mutant" lists 4 but many more exist (pass-env, property tests, clean-database cost, one-spelling, lock-name property, one-character secret).
- M-03 Minor, mutants 393: mutant 0o600 -> 0o666 survives under process umask 077 because no umask is set in the killer test (killed under the usual 022).
- M-04 Nit, mutants 391, 438: head-scan and tail-scan mutants share one assertion message.
