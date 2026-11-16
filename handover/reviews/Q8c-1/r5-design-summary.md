Q8c-1 round 5, head fbc837b4, design critic (agent accdac40, static read, ran nothing; RESULTS.md was not yet present).
Verdict: no Blocker, no Major. Issues 1-5 fixed at the lines; Issue 6 (12 Vault engine tests never run) open; Issue 7 not checkable from the snapshot.
New findings (all PROPOSE FIX at resolve):
- N1 Minor: free and never rows with an unchecked claim print their partly-read source without the "(partly builder only)" mark: tools/policy_page.py (`_checked_cell(f.verified)` / `(n.verified)` without claim=...), docs/declared-permissions.md:183 and :212 (K-SSRR on rules_review; K-AUTHZ on never create).
- N2 Minor: R17 "older versions" sentence (secrets_vault.py:241-243, docs :82) stated as fact with no source and no claim entry; wording rule does not read grant text.
- N3 Minor: page head says "the one secret it names" (docs :36-37, policy_page.py:1238) but the cell says every older version of every secret directly under the prefix.
- N4 Nit: BROADER_THAN_REASON is a hand list in the test (say so in the comment). N5 Nit: UNCHECKED_WORDING is a phrase list (tripwire, not proof; say so).
Not checked: any run, policy_page --check, byte equality, V-KV passage, unchanged part of test_policy_engine.py.
