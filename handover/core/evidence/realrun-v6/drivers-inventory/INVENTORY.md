# Mutation-driver inventory, real-run v6 chain (LEAD 12:14Z order, step 1)
Patched tree = main 61ded9e + 2 patches + survivor-tests-v1.patch. Sources searched: README.md, docs/tests.md, NOTES-v6.md, evidence-q4h-*.txt, drivers/mutants/*, the four patches (added lines), tests/ names.

| source | what | count | run on the patched tree? | where |
|---|---|---|---|---|
| muts1.json (start-prompt) | M1-M23 | 23 | yes, B2 | B2/res-M.tsv |
| muts-r.json | R1-R20 | 20 | yes, B2 | B2/res-R.tsv |
| muts-s.json | S1-S12 | 12 | yes, B2 | B2/res-S.tsv |
| muts-k.json | K1-K15 | 15 | yes, B2 (K6, K10 once more together by T2) | B2/res-K.tsv, triage/T2 |
| muts-n.json | C1-C9 + N1-N20 ("mutants of the three hunks" = C1-C9) | 29 | yes, B2 | B2/res-CN.tsv |
| muts2.json | P1-P10 | 10 | yes, B2 (+P2b, P4b) | B2/res-P.tsv |
| muts-sp.json / mo-sp.txt | start-prompt copy of muts1 (same 23) | 23 | duplicate of M | - |
| mo-*.txt | first-pass OUTPUT of the same sets on the demo's own tree | 100 lines | not a driver | - |
| run-ap/cmb/h/old/p2/v4.sh, mut-b12.py, mut2b-b12.py | wrappers with hardcoded /tmp/work old-tree paths; run the SAME JSON sets on earlier trees / combined | - | combined rows: yes (B2 res-combo.txt); old-tree runs: not the chain | - |
| tests/test_mutants.py, test_mutants_more.py, test_mutation_guards.py (+ others naming "mutant") | test-side mutation guards (weaken a copy, re-run a real test body); run by pytest, no driver | 3 files | inside the full suite (3781 passed on the patched tree; AFTER-run in progress) | A3, AF |
| ids named only in patch text | M10, K6, K10 | 3 | all inside the sets above | - |

Result: no mutant file or script named by the v6 demo evidence is outside the sets B2 already ran. Not run, stated honestly: the old-tree wrapper runs (they target earlier trees, not this chain) and the runs of M under Python 3.12 only (B2 used the lead-confirmed driver on the venv312 tree).
