19:50 start r14; copied r13 to r14
20:00 r14 code edits done (M1 tests T102, M2 refuse_unsafe_output_path+T103a/b, M3 is_test_leader+T103c, m1-m5); T102/T103 pass on r14 (58/58), 30 of 58 fail on r13 (the new guards); next: mutants table, decoy no-pgid test, final full run after r13 independent evidence arrives
20:05 mutation table started (heavy-slot), r14 head 75d5034f5aff

## 20:36Z
Done: M1-M3, m1-m5, late items 2 and 3 (tool place check; text fixed). Final mutation table: evidence-r14/MUTATION-TABLE.md (60 mutants: 57 killed as expected, 3 survive for written reasons incl. raw-no-resolve; 0 unexpected). Next: one full run on the final head via heavy-slot (first try got no slot in 25 min; retried), then clean and hand back. Not re-measured: start-up signal window (unchanged from r13 by design).
