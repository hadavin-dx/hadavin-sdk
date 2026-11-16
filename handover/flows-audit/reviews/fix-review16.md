# Fix log, round 24 (fixer for reader-r23 and design-r23)

Scope: only `reviews-of-core-patches/REVIEW.md` was edited. Not committed. Static only: nothing was run in Postgres or n8n. The Postgres defaults used (PUBLIC holds TEMPORARY on databases and EXECUTE on functions) come from the manual and are UNVERIFIED, not run. The machine clock (15:13 UTC) is earlier than the previous file stamp (15:30 UTC), so the header records no clock time.

Severity counts unchanged: 28 rows, 4 Major / 13 Minor / 11 Nit (`count_review.py` output below). No finding proved a row wrong. No reviewer finding was disputed; every cited source line I opened matched.

Line numbers refer to REVIEW.md after the edit (search the quoted heading if the file moves).

## Findings
| Finding | Status | Where |
|---|---|---|
| Q1 has no block | fixed | first bullet of "One plain block per decision"; Q1 heading points to it |
| Deployer unnamed in answer order, table, blocks | fixed as Decision 25 | answer-order line, table row 25, block 25, numbered paragraph 25 in "Matter today". WHO the deployer is: needs studio head |
| Decision 20 options and counts, 5 vs 6 Major | fixed | block 20 and paragraph 20: six options with counts (T2 alone = 5/12/11; both money-limit rows Major = option 6 = 6/11/11); lines about T2 in Words and scales fixed in part A |
| Decision 22 "Size and by when" | fixed | block 22 (about 3 hours, date end of 2026-11-18 UTC = 05:30 IST on 11-19, only if answered); table row 22 |
| Blocks do not say what a "no" does to the hold | fixed | every block now has a Hold part |
| Decision 1: "met", critical path, split-hold | fixed | block 1 and table row 1; terms line defines MET; option 3 = split hold, needs studio head yes (not applied) |
| Criterion (8) and "six criteria" count | fixed | criteria row 8 and text, "CANNOT end on a note" paragraph now lists each criterion |
| Decision 5 block: 5-K, K-A/K-B, recommendation | fixed | block 5, paragraph 5, criterion (3) text and row. 5-K answer: needs studio head |
| Build order vs "same time" claim | fixed | waves 1 to 3 in the blocks intro |
| Decision 2: A-01 un-defer, X-2/A-6 first, date | fixed | block 2 and paragraph 2 |
| Criterion (9): baseline, allowlist, Decision 9 "no", 1-2 days, dependencies | fixed | criterion (9) text (modes A and B), table row 9, criteria row 9, block 9, paragraph 9. Whether `signer` needs the lock function: unknown, to be read before building |
| Minor: cite :312 | fixed | `models.py:139-148` (REVIEW.md now has 2 such cites; I did not re-open models.py after the edit, relying on the reviewer's line and the earlier read) |
| Minor: :216 X-6.4 wording | fixed (part A) | X-6.4 row facts and who cell |
| Minor: signer SELECT alg/key_label | fixed (part A) | signer identity row |
| Minor: stale "X-5.1 says only the drain needs DELETE" | fixed | paragraph 2 |
| Minor: (2) is PART | fixed | criteria wording |
| Minor: k1b outbox path | fixed | block 2, paragraph 2, k1b row: only the score-report failure path parks (`cli.py:262-270`; `emit` raises, `k1b/audit_sink.py:31-35`) |
| Minor: k-A signing test | fixed | criterion (3) text and row |
| Minor: `hadavin-sdk audit` login | fixed (part A) | new `verifier` identity row (ten logins) |
| Minor: DSN gloss | fixed | "connection string" in blocks and prose |
| Minor: UTC + IST in blocks | fixed | dates in blocks, table, work-possible-now |
| Minor: lower-case sentence start | fixed | paragraph 2 |
| Minor: grouping of 21/22 | fixed | moved into "Matter today"; round-19 heading renamed |
| Minor: "Who is who" heading | fixed (part A) | bold list label; cross-references name it |
| Minor: codes explained | fixed | terms line in the blocks intro; Decision 23a reason added |

## Needs the studio head (no invented answers)
Who the deployer is (Decision 25); question 5-K (do the K1b commands sign); Q1 (which program makes the model call); who rewrites the branch (23b); the rotation lead (21); whether to split the hold (Decision 1 option 3); whether `signer` needs the lock function.

## Check outputs
- count_review.py: `rows 28`, severity Nit 11, Minor 13, Major 4, decision DECLINE 3, PROPOSE FIX 25.
- check_refs.py: PASS 5176 references.
- check_names.py: PASS 655 rows.
- check_secrets.py: PASS 0 hits in 1994 files.
- Leftover grep outside History: no "24 decisions", "Twenty-four", "five gaps", "ten names", "six criteria", "audit session", "DSN" wording remains. Every remaining "every login" is qualified or true.

## Not checked
No reader or design re-review of the new text was done by me (the author does not count as a reviewer). The new blocks were not read back line by line for tone; a fresh reviewer should.
