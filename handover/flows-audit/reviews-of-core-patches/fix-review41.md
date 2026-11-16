# Fix round 41 (fixer, security/design path, uncapped). Only `REVIEW.md` was edited, plus this report.

Nothing was run in n8n, Postgres or HubSpot; nothing was committed. Evidence for each item below is "text found by search or by script after the edit", not a test run. A copy of the file before the edit is in the session scratchpad (`REVIEW.bak`).

## NOT done or uncertain (first)

1. **Reader r35 M2 (very long rows) is NOT fixed.** Lines 12, 31, 38 to 44, 166, 167, 235, 253, 272, 310, 314 and the table cells 243 to 249 and 276 to 289 are still single paragraphs of thousands of characters. Reason: splitting any line above line 77 moves the heading that other files cite as `REVIEW.md:77` (and `:5`); splitting the table cells needs a new three-line cell shape (SHOWN / NOT SHOWN / rating reason) for about 25 cells. Exact missing input from the lead: either allow `REVIEW.md:77` to move (then README.md line 8 and DEAD-MAN-CHECK.md line 3 are re-pointed by text), or keep the numbers and accept that the rows above line 77 stay long. I did not split rows below line 77 either, because a half-split file is harder to read than a consistent one. I added no new paragraph over 1,500 characters; I checked by script (the only lines over 1,500 characters that grew are the pre-existing line 12, which grew by about 230 characters from the rename of (B), and table rows 263 and 267, which are false positives of my prefix matching).
2. **Reader r35 M1 (orientation) is only partly fixed.** I added a 5-sentence orientation block at line 6 (it replaced a blank line, so no line moved), but the glossary before the first finding is still long; I did not shorten it.
3. **Design r35 M1 (owners)** cannot be closed by me: the builder session name and the human roles (deployer, verifier person) are inputs only the lead and the studio head have. I wrote the exact missing input into line 41 (the lead writes one builder session name; each human role stays empty until the studio head writes a name, and he may name himself). The criteria that need those roles stay unmet in the text.
4. **Tool facts stay UNVERIFIED** (`ssh-keygen -Y verify` touch option, `ed25519-sk` behaviour). I gave them a doer and a date (open question 6) but verified nothing.
5. **Minors and Nits of the three reviews not touched:** forward uses of G5, T2, RIGHT-SIZE and Q17-2 (glossary defines RIGHT-SIZE and Q17-2 as "not defined in any file read"; unchanged); "wave" definition location; login spellings (`dead-man reader`, `deadman_reader`); dates without a zone at old lines 133, 637; "fix-reviewN.md" folder rule; reader r35b m1, m2, m4, m6, m8, m9, m10 and the nits (CODEOWNERS unglossed, "hard rule 11", "was on line N" in History, History "current" counts). I did not read lines 751 to 804 (History) again. These are Minor or Nit; I list them rather than claim them fixed.
6. **Two files I was told not to edit need a wording fix (agent a0fef7e3 owns them):** `patch-copies/README.md` line 8 and `DEAD-MAN-CHECK.md` line 3 quote `../REVIEW.md:5` as "the C-01 extras (the **token ceiling**) are CUT", but `REVIEW.md:5` says "(the **token limit**)". I left line 5 unchanged (I am sure of its wording), so change "token ceiling" to "token limit" in both files. README.md line 10 also says "the ceiling on `max_tokens`" in a plain meaning; that one is a description, not a quote, and may stay.
7. **Contest (no change made):** the design reviewer recommends writing the ten Major parts into the ledger as Blocker whatever Decision 20 says. I did not change any severity. The rating is the studio head's Decision 20; my text only keeps "Blocker-equivalent".
8. Scope judgement I made that the lead may reverse: I added a PRICE TEST to criterion (1) and a MASKING CANARY TEST to criterion (7), as the design review asked. That makes the price refusal part of an exit criterion, while Decision 18 was "not an exit criterion" before; I changed Decision 18's Hold line to say so. If the lead thinks that widens the hold too much, remove the PRICE TEST sub-bullet under (1) and the Hold sentence of Decision 18.

## Fixed items, by id

**Reader r35b B1 (key mapping)**
- New "SIGNING AUTHORITY MAP" (a table, after the KEY TABLE bullet 'CURRENT'): which key signs which file, how many signatures, which keys are refused. It says "current key" and "next key" are not extra keys and that "dedicated approval key" means the note key, the evidence key or the release key by file type. There is no seventh key.
- Who signs (B): release key alone for an ordinary release; release key AND next key for a key-set or pin change (Decision 27 sub-block K.1 now says "release key and next key"; the old text at "which the approval key signs" and "signed with BOTH the current and the next key" was changed to match).
- Minimum counter: one rule in the new bullet "MINIMUM COUNTER, one rule" (set to the counter of the newest existing list, changed only when a list is issued, not at every release). Old text "raised at every release" replaced; K.2 now says "equal to or higher than the minimum"; the "refuses a list below" wording agrees.
- Superseded sentences were replaced in place (not only marked): "KEY SET ... two public keys, current and next, in the pinned config", the option (i) "dedicated approval key" and "pinned in the deployment's validated config", the EVIDENCE BINDING "dedicated approval key", "result hash" (now "hash of the evidence summary, sub-block I"), the WHAT IS SIGNED line (now one list for notes, evidence files and release records), (B) = "security configuration digest" (now "the signed release record"; the configuration digest is a part of (B)), and the note-signing sentence of the long Decision 27 text (the sixth part is now described once, under ACCEPTANCE NOTE). The orphan heading "REVIEW NOTE (design review r34 M7, M2, Minor 10)" was removed. BUILD IDENTITY is marked as the same object as PROPOSED CONTENT. The sub-block header now says the map and the KEY TABLE win over both the sub-blocks and the long text.
- Remaining uses of "approval key" (lines 43, 278, 446, 470) were rewritten to name the key-table keys. Remaining "current key" uses are explained by the map.

**Reader r35b M1, M6 (which run closes; notes have no force)**: new paragraphs after the criteria table: WHICH RUN CLOSES A CRITERION (trial run by an evidence runner vs counting run by the counting job of sub-block R; until the counting job and verifier exist, (1), (2), (6), (9) are "built, proved on trial run, counting run pending", never "met") and A NOTE HAS NO FORCE UNTIL THE VERIFIER EXISTS (covers Decisions 2, 4, 5, 8). Decision 27 text point (e) and the verifier test sentence were aligned.
**Reader r35b M2**: new bullet VERIFIER NEGATIVE TESTS (one list: the Decision 27 tests, T.6, K.4, R.4, the SEPARATION TESTS, the two start tests; run once per new verifier hash and per new (B) or (T), not per release); criterion (8) now says all of them are needed, and its proof column names them.
**Reader r35b M3**: size of (8) and of Decision 28 changed from "small to medium" to "large" by the size-label rule (no day figure until the verifier person is named); tool-fact doer and date written (open question 6).
**Reader r35b M4**: the stored result of (9) is now called a convenience, and the proof is the verifier's own run; `admission-reader` rights now name the catalog queries.
**Reader r35b M5**: criterion (5): tests 2 and 3 are required when the audit-writer function closes (5), otherwise a note closes it with the reduced claim.
**Reader r35b M7**: "client code" as an identifier renamed to "client id" (key table, hash table, notes text, folder text); "client code" now means only software (8 uses remain, all of that meaning); defined in the glossary.
**Reader r35b M8**: see B1 (superseded sentences). The verifier-person timing conflict (Decision 26 vs 27) fixed in open question 3 (due with his answer to Decision 27, which needs 26 first).
**Reader r35b M9**: the five parts of an acceptance note are numbered PART 1 to PART 5 (so "part 2" and "part 5" now point at something), PART 1 names which text is copied ('Cost of accepting' of the matching item), a note without a date in part 2 or a doer in part 5 does not count; the sixth part is described once.
**Reader r35b minor m3, m4 (partly)**: criterion (9) login list names the two undecided programs and a recount rule; `k1b` login conflict resolved (see design M3).

**Design r35 M1**: line 41 now says exactly what is missing (see item 3 above). Headings "OWNER OF ..." renamed "DOER OF ..." (also fixes reader r35 M7).
**Design M2**: RELEASE ORDER paragraph added to Decision 10 (release 1 adds logins and, if yes, removes the criterion (1) rights; release 2 is the narrowing release); Decision 15's Hold no longer says "timing only"; Decision 15 added to the chain in Decision 1's block, table row 1 and line 41 (THE PATH).
**Design M3**: `k1b` is in list A in every case; criterion (9) now says that, and that under Decision 2 (a) or (c) the K1b commands still write under `k1b` with a positive and a negative test.
**Design M4**: SUMMARY TEST added to criterion (2) (and Decision 13 points to it).
**Design M5**: Decision 18 trigger moved to "before the take's live call and before any pilot" in its block and in the table; PRICE TEST (zero or negative price, negative token count or amount, decimal to whole money units) added under criterion (1) as a sub-bullet.
**Design M6**: MASKING CANARY TEST added to criterion (7); a note covers only the read right; "may a note close (7) for a pilot" is put to the studio head under Decision 1 option 3.
**Design M7**: purge row of the login table now says the purge is its own program (X-5.7, criterion (6)) and that today it runs inside the tick; "which key" fixed by the map.
**Design M8**: DEPLOY IDENTITY added to criterion (8) (sub-bullet "(8) ADDITIONS") and to Decision 22's Hold, size line and table row trigger. (Table row 22 trigger text was not changed; see below.)
**Design M9**: table row 12 now "decide after 7 and 29"; row 5 "7 and 29"; row 7 has one sequence sentence (Decision 7 provider and refusal, then 29, then the profiles; ranges not added).
**Design M10**: notes are dated, owned postponements: part 2 date and part 5 doer required.
**Design M11**: open question 5 and 4 now say what stays unmet until they are answered and are on the hold path (line 41).

**Reader r35**: M3 and M4 (sign and verify words, one meaning each: new glossary bullet at line 29, and the three-hash wording), M5 (pointer "listed in Decision 1" now points to 'Matter today' item 1), M6 (one-sentence severity in the orientation), M7 (doer), setting renamed "this process does not checkpoint-sign" everywhere (17 plus 11 quoted uses; no other file used the old name). Glossary lists (a) to (g) are now in order; "READ THIS FIRST" label on the glossary item changed so there are fewer "read first" instructions (the Plain summary heading and the decision-block heading still say it; unchanged). One size label rule added to the size-label line.

**Citation review 40**: `limits.py:43-52` and `:48-52` (4 places) now end at 51; `test_p2_postgres.py:289` is now "the assert on the result of a `migrate` call" (2 places). Token ceiling vs limit: see item 6.

## Not changed because I could not confirm it from the text I read
- Table row 22 trigger cell: I did not edit it (the Decision 22 block and the criterion (8) text carry the deploy-identity condition; the row still says "not an exit criterion"). The lead should either accept this or add one sentence to the row.
- I did not recheck every old sentence that says "the current key" in a sentence outside Decision 27; the map's first sentence covers them.

## Commands run and outputs

```
$ cd /home/user/hadavin-sdk/handover/flows-audit
$ python3 -I reviews-of-core-patches/count_review.py reviews-of-core-patches/REVIEW.md
rows 28 ['C-1', ... 'X-6']
severity {'Nit': 11, 'Minor': 13, 'Major': 4}
decision {'DECLINE': 3, 'PROPOSE FIX': 25}
$ python3 -I tools/check_refs.py
PASS 5182 references
$ python3 -I tools/check_names.py
PASS 655 rows
$ python3 -I tools/check_secrets.py
PASS 0 hits in 2749 files
$ ruff format --check . .
896 files already formatted      (exit code 0)
```
Line 5 and line 77 start with the same words as before (`Lead default of 2026-11-16, item 4 ...` and `3. C-01: DO NOT APPLY NOW. ...`); the file grew from 804 to 822 lines, all of it below line 77 (line 6 and line 29 were blank lines reused, so no line above 77 moved). The secrets check counts one more file than before; I created only this report in the folder, which explains it.
