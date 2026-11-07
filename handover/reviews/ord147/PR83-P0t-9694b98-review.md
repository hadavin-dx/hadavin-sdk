# PR83 (P0t follow-up / fix132) result review, head 9694b98 (condensed; saved by the lead)
Verdict: 0 Blocker, 2 Major, 5 Nit. Head check ok (14 logs line 1 = 9694b98; job312/313 logs carry no SHA). Confirmed: 29 refused words (6 stage + 28 common... union 29) via check_id; five config id types wired; one shared list commonwords.py (identity test); folds NFKC, Cf removal, casefold; full 10567 passed both Pythons; stage mutants 69/69; lint/perf clean.
- Major 1: CHANGELOG "Not refused: an id shorter than 3 characters" contradicts code (db, 2 chars, is refused). Fix wording + make the changelog test catch it.
- Major 2: fail-before proof moderate: A and B end in collection ERROR for test_tenant_ids.py; only variant C (author shim) shows behavioural failures (18 failed, 12 tenant). Show new tests failing on real e2d8971 source with only new symbols stubbed (attach stub diff), or publish the shim and call it an approximation.
- Nit: no mutant for a dropped common word (M10 drops only pilot/demo/prod; mutant runner runs only test_tenant_ids + stage test, not the changelog list test; docstring cites nonexistent T17b; OrgId and CustomerId mutated, AccountId and UserId not).
- Nit: spelling gaps not handled or disclosed: Cc controls, interior spaces, variation selectors, combining marks, Cyrillic/Greek look-alikes (disclosed), Turkish dotted I; CHANGELOG headline "any spelling" overclaims. Decide whether confusables are acceptable (lead item).
- Nit: guards no live path; walk misses argparse --tenant, dict keys, setattr, locals.
- Nit: CHANGELOG demo wording split (order 126 vs 132) should be recorded as deliberate; test forbids string "a demo database" anywhere in Unreleased (brittle); 1000-char test.
- Nit: duplicate rows in tests/stage_exemptions.tsv; reviewer did not confirm counts.
- Not checked: diff lines 592-1639, scanner changes, redactor min-length logic, no runs.
