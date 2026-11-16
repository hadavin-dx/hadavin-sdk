# fix-review40: fixer batch 40 for `REVIEW.md` (security/design path, no round cap)

Written 2026-11-16 by the fixer session. Only `REVIEW.md` was edited (plus this report). Nothing was committed. `patch-copies/README.md` and `DEAD-MAN-CHECK.md` were not touched.

## Failures and uncertainty first

- NOT RUN: nothing in `REVIEW.md` was run against Postgres. Every new test text (approver proof, drain writer, criterion (9) producer) is a PROPOSAL marked UNVERIFIED. No test was written or executed.
- NOT DECIDED, because no file answers it: (1) which channel authenticates an approver's click and what proof it leaves (new open question 5; studio head with the builder; due end of 2026-11-19 UTC, 05:30 IST on 2026-11-20, proposed by me); (2) whether the counting job's output is signed by a key of its own (open question 4; due with question 3); (3) why the baselines 9364 (README) and 9389 (heavy lane) differ by 25 (named in line 77; lead names who runs both on one tree; due end of 2026-11-18 UTC, 05:30 IST on 2026-11-19).
- The reader finding "ROLES-PROPOSAL says five logins": the text `five logins` I found (X-6.6a, line count "five logins" = agent/tick, receiver, operator, k1b, drain) is correct and I left it. The real slip was "five other roles" (ROLES-PROPOSAL section 3 lists five roles: one NOLOGIN table owner plus four logins). That wording is fixed. I read `../ROLES-PROPOSAL.md` lines 60-75 only.
- The round-tag removal is by regular expression. I read the resulting hits in a list, but I did not re-read all 59 edited lines in full; some sentences may read slightly clumsily ("REVIEW NOTE (F8):" now stands where "ROUND 30 (F8):" stood). Reviewer r40 should check readability, not facts.
- "Move superseded text under History only": only 6 parentheses of the form "(the earlier ...)" were found and moved (listed at the end of the History section). Other old-text remarks that are not in such a parenthesis may remain in live text; I did not find a reliable way to detect them by script.
- Long rows: all table rows over 2500 characters in cells 4 and up were split (X-2, X-4, X-5.3, X-5.7, C-3, C-7, C-8, A-1, A-2, A-3, A-6 and the `agent and tick` login row); the text moved unchanged to "TABLE CELL CONTINUATIONS" paragraphs under each table. Rows `operator` (3239 characters) and `k1b` (3513) stayed whole because no single cell exceeds the limit. Paragraphs outside tables (the longest live line is still over 9000 characters, in the decision blocks) were NOT split.
- Not checked: no line-number cite in any file other than the two named ones. Older reports (`../reviews/citation-patchcopies-r9.md`, `../reviews/fix-patchcopies9.md`, `../reviews/patchcopies-stranger-r8.md`) cite `REVIEW.md:142/179/397/402`; those are dated records of earlier rounds and were not edited.

## Cites kept

Line 5 still opens "Lead default of 2026-11-16". Line 77 still opens "3. C-01: DO NOT APPLY NOW." (`grep -n` output below). No line was added or removed above line 77. Every line from 153 down moved (row continuations were inserted); no file I know cites those lines except the old reports above.

## Finding to result

| Item | Result |
|---|---|
| Decision 29 size stated once | Done: the figure "about 3 to 6 days" now appears only in the Decision 29 block; table row 29, X-5.3, Decision 5 row and block, Decision 3 row, Decision 27 signing load, criteria (3) and (6) rows point to the block without a figure. `grep` for "3 to 6": block only (plus "Decisions 3 to 6", a range of decisions). |
| "wave 1/2/3" defined before first use | Done: defined as item (g) of the READ THIS FIRST glossary (line 12); first use is later (X-2 row). |
| Wave-1 circularity (Decision 5 option (i)) | Done: Decision 5 (the signing program itself) needs no "does not sign" setting to be built; the production start of the OTHER programs is tested in wave 2; Decision 29 stays wave 1 and Decisions 3 and 10 wave 2. |
| Receiver vs freezer (Decisions 12/13) | Done: Decision 13 and item 13 name "the program that freezes the digest (receiver under R1, `freezer` under R2)"; wave text likewise. |
| Owner of Decisions 20/23a/24 | Done: table rows now say "a session the lead names (not named yet; an assistant session may not assign itself)", as the blocks do; the sentence in Decision 20's ask uses the same words. |
| Who decides the branch rewrite | Done: line 320 now says the studio head decides and names who rewrites; the lead is not proposed (as Decision 23b and item 23b). |
| Sixth part mandatory | Done: Decision 27 text, C.4(c) ("not offered") and the acceptance-note text now agree that it is mandatory for pilot and production notes. |
| "Does not sign" sized and gated one way | Done: line 41 no longer says "if the studio head wants it before the pilot"; it says criteria (1) and (6) need it, before the proposal under Decision 1 option 1. Size only in Decision 29. |
| Decision 3 order note vs block | Done: block and table row say 2, 5, 7 and 29 are answered first (answer order already put 29 before 3). |
| Drain as only deleter vs k1b DELETE | Done: Decision 3 says `k1b` is a second deleter only if Decision 2 option (b) is chosen, as criterion (6) already said. |
| Key table vs sub-blocks K/I | Done (a round-39 slip): the release key signs only (B); the next key signs revocation lists and the succession message. |
| Approver-proof test, criteria (1)/(2) | Added as a proposal (UNVERIFIED); blocked on open question 5. |
| Criterion (9) producer | Added: P1 verifier runs the catalog queries itself as `admission-reader`; P2 a separate read-only login with a result signed by a key the owner lacks; allowlist and login list go into (B); one test. |
| Drain writer column | Added as the third test of criterion (5) with a hostile-drain test; column name left to the builder. Expiry clock: closed by pointing to Decision 27 EXPIRY. |
| "round 3x" tags | Live text (before History): 0 left (checked by script, below). The old tags ROUND 14, 19 and 28 were also removed from live text. History keeps its round numbers. |
| "ceiling" | Live text: 5 left, all quotations of the source word or code names (`HELD_MAPS_CEILING`, two test names, "the source says 'ceilings'"). Token meaning is now "token limit"; the 400-day meaning is "retention limit". |
| Counts | See below. |

## Recounts (method)

- Login names, BY HAND-LISTING in a script (`python3 -I`): list A = agent, tick, receiver, operator, k1b, drain, signer, dead-man reader, chain-checker, admission-reader, portal, purge = 12 names. List B = holds, freezer, rotator-<secret class>, operator-stop, operator-reset = 5. Because operator-stop and operator-reset replace operator: 12 + 5 - 1 = 16. With two undecided programs: 18. The text said "up to seventeen"; that was wrong and is now 16.
- Advisory-lock signatures, by listing the 8 names in the text: 8 x 2 forms = 16.
- "About 14 signatures": 9 + 1 + 1 = 11 fixed, the number of key-set files is not fixed, so 14 stays an estimate and now says so.
- Review rows: by `count_review.py` (below).

## Raw output

```
$ python3 -I reviews-of-core-patches/count_review.py reviews-of-core-patches/REVIEW.md
rows 28 ['C-1', 'C-2', 'C-3', 'C-4', 'C-5', 'C-6', 'C-7', 'C-8', 'A-1', 'A-2', 'A-3', 'A-4', 'A-5', 'A-6', 'A-7', 'A-8', 'A-9', 'G-1', 'G-2', 'D-1', 'D-2', 'D-3', 'X-1', 'X-2', 'X-3', 'X-4', 'X-5', 'X
severity {'Nit': 11, 'Minor': 13, 'Major': 4}
decision {'DECLINE': 3, 'PROPOSE FIX': 25}
$ python3 -I tools/check_refs.py
PASS 5178 references
$ python3 -I tools/check_names.py
PASS 655 rows
$ python3 -I tools/check_secrets.py
PASS 0 hits in 2734 files
$ ruff format --check .
881 files already formatted
$ grep -n first words of lines 5 and 77
Lead default of 2026-11-16, item 4 (`../
3. C-01: DO NOT APPLY NOW. A price-only 
$ live-section scan (script): round 3x tags before History
History at line 648 ; live round-3x hits: 0 ; live ceiling hits: 5
```
