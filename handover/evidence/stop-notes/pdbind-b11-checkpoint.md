# pdbind batch 11 checkpoint (start 04:01 UTC)
- 04:20 read all inputs. Found G cause: batch 10 touches __slotnames__ at pin; a cloned base then differs by its own fresh __slotnames__ list, so the mro check is not the only thing that notices (test's clone was caught by that, B98 survived). Fix: share __slotnames__ in test namespace.
- Plan: A+B+C in requests.py (marks of weakref/atom/type/id, no strong ref to runtime chain), D test, E changelog, F labels.
- Nothing committed yet.
- 04:09 A-D code+tests+mutants B257-B269 done, 32 rows killed. Next: G (B98), E changelog, F issues 6-9. Not committed.
- 04:13 F items + G + E done in tree; running mutants/focused tests; then fail-before at 304c3bd3 and 83cdb7a2, then commit
