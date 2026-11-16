# v31 changes (owner sheet v31, round 3, builder Sonnet 5.5)

Times are "UTC = IST" (IST = UTC+5:30). Nothing here was committed, pushed or spent. No secret was used.

## 1. Failures and open items FIRST

Not done or not proven:
- Every vendor page, button and file path in the sheets is still UNVERIFIED (no live check was made).
- The pointer ledger (pointers-v31.txt, 950 entries) was read by the builder only. A person who is not the author has not read it.
- OWNER-OPEN: who may cancel an older key when the owner cannot (Open 107; security M2). The sheets now say the helper may cancel any of the owner's keys, limited to key-cancel, and carry an accepted-risk sentence when there is none. The name is the owner's to give.
- Needs lead confirmation (new Open row): the yes binds the owner to 7.11 even when no "go" comes, on a decline, or when time passes.
- Open 103 (derivation of 18:04 UTC = 23:34 IST) is still asked. Open 102 (does the card count toward the 6,300 words) is still asked.
- Open 71 (sheet A or B): the lead does not choose for the owner. Default A carries the warning beside it (A will probably fail on Wed 18 Nov).
- Still OWNER-OPEN from earlier: L7, DB-2, the delete-path criterion, Q27.
- The reading load is NOT reduced: the four pages together are longer than v30 (sheet A 6,287 words of 6,300 allowed, but the card, appendix and film page grew).
- Check C224 (placeholder spelling and count) cannot fail on built v30 (v30 already had the five lead slots in order); it is a guard proven only by plants Y18 and the others.
- The mutation script says "MISSED" for the negative control NEG1 on purpose.

## 2. Counts (run at the final head)
- Sheet A 6,287 words; sheet B 6,087; card A 1,959, B 1,876; appendix A 4,458, B 4,389; film page 519.
- Four-page totals: A 13,223; B 12,871. Lead note v15 13,032; open list 7,679.
- check-v31.py: 0 failures. build-v31.py: ok. v31-fail-proof.py: 0 problems; 17 of 18 Part 8 checks fail on built v30; C224 cannot (see above); none fail on built v31.
- mut31.py: 230 plants, 229 caught by the meant check, 0 missed, 0 anchor-not-found, negative control ok (printed MISSED as designed). Baseline failures 0.
- Banned-string scan over v31 files: 0 hits (list read at run time from the repo guard test). Time pair and weekday scan: C04 clean.

## 3. Findings and fixes (class, fix, check, plant)
- Security M1 (Mon 23 Nov): owner reminder 18:09 UTC = 23:39 IST; cancel-by 18:19 UTC = 23:49 IST; L2 lets a key found valid after the deadline be cancelled; dead Mon 23 Nov paragraph of part 10 deleted. Checks C210; plants Y01, Y02.
- Security M2: helper may cancel any of the owner's keys, key-cancel only; accepted-risk sentence if none; who stays OWNER-OPEN. C211 and C217; Y09.
- Security M3: lead note and open list rows 64, 144, 226, 71 carry the warning beside default A; no choice made for the owner. C212; Y03.
- Security m1 to m5: revoke names compared exactly (C214, Y06), B warning (C215, Y07), card step 5 sentence (C216, Y08), yes binding and "There is no older key." (C217, Y09), film-person guard honesty (C218, Y10).
- Stranger M-A1 to M-A4: 5.1 split into a, b, c with the run day (C219, Y11); last-5-minutes rule (C220, Y12); film page shows only the page area (C221, Y13); minors m1 to m11 (C222; Y14 to Y16).
- Open list: minimum 40 minutes is not checked by the sheet (C223, Y17).
- Sheet A stays at 6,287 words (cap 6,300); detail moved to the appendix, nothing deleted.

## 4. The four evidence-runner items
1. H06 (lead message releasing the older-key cancel, any phrasing): C213 now uses a generic, case-insensitive pattern including release/allow/permit verbs. Plants Y04, Y05 (Y04 slipped first: capital "When"; fixed by case-insensitive match, then caught).
2. H09 (placeholder spelling and count): C224 checks all five [LEAD FILLS at re-pin: ...] and every [OWNER FILLS: ...] by exact spelling and count. Plant Y18.
3. ls_t: removed with other dead facts; C225 fails on any fact no source or check uses. Plant Y19.
4. Pairs 18:19 UTC = 23:49 IST and 18:04 UTC = 23:34 IST are in the owner pages (C210); the masked email examples are replaced by a non-email placeholder (C226; plant Y20).

## 5. Other fixes by the builder
- C227: run-time file times and no absolute path in any script. The banned-list path is found by walking up; mut31.py passes it to scratch copies by an environment variable (without it C06 failed in every scratch copy, baseline 1: found and fixed). Plant Y21.
- Re-anchored plants V13, V14, X02, X03, X10, X23, X27; M26 now caught.

## 6. Rules cited
No single dependency; least privilege; no hardcoding or secrets; fix and do not defer; honesty; wording for everyone; class-level fixes; reviewer independence (this is builder evidence, not a review).
