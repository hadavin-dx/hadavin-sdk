# fix-review49: Z1 part (4A) and tests, design review r49 (10 Majors, 5 Nits), FIXER round 49, security path
Edited ONLY REVIEW.md. Everything new is a PROPOSAL: nothing built, nothing run (the tests are test descriptions). Reviewer words were checked against the text; the old text is saved in the scratchpad copy REVIEW.before49.md (not in the repo).

## Gaps first
- Nothing was run against code; every start case and test is a design text, UNVERIFIED.
- Reason phrases in square brackets (about 20 phrases) are new proposals; the builder may reword them, but each refusal test must then assert its own exact phrase.
- Tests (w) and (x) stay one lettered test each that runs a table of inputs of ONE cause (same phrase); that is now a written rule.
- Hash coverage (signed body, not signature blocks) is a design CHOICE I made to settle M4; marked "builder to confirm".
- Part (8)(iii) mitigation (timer re-check raises the host record) is a proposal for the studio head; no "LEAD DECIDES" line was needed because every choice has a stated default.
- Other files still saying 114 or Z1 28 (review-reader-r38.md) are history files; not touched.

## Per finding
- M1 FIXED (agreed: with an empty log L does not exist, and a first release with H=1 hit case 4's "previous file" rule). New order, six cases plus a pointer (old "7" was 6 cases plus a pointer): 1 log unreadable; 2 NO ENTRY for client id (S present: refused 'the log has no entry but this host has a record'; S absent: START only with signed 'first release', H=1, no previous file); 3 S above the log; 4 H=L; 5 H=L+1; 6 anything else. Z2 and Z17 refs moved (old 4/3 -> 5/4); part (4)(c) "case (a)" -> "case 4".
- M2 FIXED (agreed). (ab) now START only (S.r=3, L=5, H=5, S raised to 5); new (ac) REFUSE: same host handed H=4 (S<H<L), case 6. Counts of START tests restated: 8.
- M3 FIXED. S is a triple (S.r, S.v, S.g) per client id (4A letters, part (3)); case 3 refuses if ANY exceeds the log's; tests (ai) two client ids on one host (START), (aj) S.v above log, (ak) S.g above log; (u) now says S.r.
- M4 FIXED. Case 4 now lists part (6) (revoked signing key), part (9) (revoked or below-minimum (A)), next-key check, hash, and SIGNATURE COUNT >= the log's SIGNATURE RECORD; states what the hash covers (signed body, not signature blocks). Tests (al) revoked key at H=L on a wiped host, (am) one signature against record 2. Case 4 still skips Z2 (stated why).
- M5 FIXED. Deployer ALWAYS hands both files (the (B) to start and the one counter lower); file (ii) used only in case 5, ignored in case 4 (test (at)). Race rule: refused append -> re-read ONCE -> case 4; second refusal 'append refused twice'. Crash after append -> retry meets H=L, case 4. Tests (ao), (ap). Z17 sentence updated.
- M6 FIXED. Scope sentence at the head of 4A and in part (7): table binds ACT and COUNTER-CONFIRMED; STOP-ALWAYS and light profile bypass it (test (l)).
- M7 FIXED. Pointer line, part (5): an override never starts H < S.r, S never lowered; on a wiped host S is absent so the rule binds nothing there (said plainly). Test (an).
- M8 FIXED. Part (8)(b) restricted to hosts whose record is up to date; REMAINING WEAKNESS (iii) names the lagging-host case with the n-2/n-1 example plus a proposed mitigation; OL-20 question widened.
- M9 FIXED. (v) split into (v) wrong/missing signature, (ad) nonce used twice, (ae) captured valid pair to a new process on a wiped host, (af) same on the original host; each asserts its phrase ('nonce not made by this process' for ae, af). Rule block: every refusal test asserts the exact phrase; 40 refusal tests = 40 phrases (counted by script).
- M10 FIXED. (a), (e) run on a host with a state file and on a wiped host; new (ag) wiped host H=L wrong hash, (ah) lagging host H=L+2.
- Nits: N1 fixed (previous file's counter field must equal L, in case 5). N2 fixed (REMAINING WEAKNESS (iv) squatting; recovery succession and epoch rollover). N3 PARTLY CONTESTED: old line 614 shows (m) is refusal only ("in the same case an ACT process is refused"); (w) holds a STOP start as a control and (ab) held both; now stated: 8 START tests, 40 refusal tests, (w) counted as refusal with a control. N4 fixed ((t) marked conditional on the real object-lock store or append program). N5 fixed (client id check before the cases, new test (av), phrase 'client id differs').
- Also split (z) into (z) revoke stop and (au) maximum run time (two causes, two phrases).

## Counts (recomputed; python output)
Z1 letters: (a) to (z) = 26, (aa) to (av) = 22, total 48 (was 28; 20 new letters (ac) to (av)). START 8 [(l),(aa),(ab),(ai),(ao),(ap),(as),(at)], refusal 40 (was 25). Z block: 48+5+3+2+8+13+3+3+1+2+3+1+1+2 = 95 (was 75); total 39 + 95 = 134 (was 114). Running sums 53,56,58,66,79,82,85,86,88,91,92,93,95. Updated: Z1 header, test line, COUNT paragraph (VERIFIER NEGATIVE TESTS), history line (batch 44 note).

## Checks (output)
- count_review.py: rows 28, severity Nit 11 / Minor 13 / Major 4, PROPOSE FIX 25 / DECLINE 3 (unchanged).
- sed -n 5p sha256 prefix e6db355c; sed -n 77p 7f8da2ce (unchanged). REVIEW.md still 943 lines.
- check_refs PASS 5190 references; check_names PASS 655 rows; check_secrets PASS 0 hits in 2933 files; check_counts PASS 52 files / 655 nodes; ruff format --check . : 1058 files already formatted.
- grep for stale "28 in all", "(l), (aa) and (ab)", "case (a)" in Z1: none left. No commit-id line or personal handle printed. Nothing committed.
- Not done: no reader (non-technical) pass on the new text; round 50 review of the new 4A is needed (security path, uncapped).
