# fix-review37: fixer round 37 of REVIEW.md (answers design review r36 and reader review r36), 2026-11-16 17:16 UTC / 22:46 IST
Edited only `reviews-of-core-patches/REVIEW.md`. Nothing committed, applied or run against a database. Before-copy of the file: scratchpad `REVIEW.before37.md`.

## Failures and uncertainty first
1. Not fixed: single lines over 3000 characters remain. I split the three prose bullets (hold sentence, Decision 27, criterion (9)) at their capital-letter labels. Table rows (for example the X-5 and X-6 rows, line numbers about 198-269 before the edit) cannot be split without breaking the table; turning them into labelled lists is a larger rewrite I did not do (design m8, reader M3). Markdown still joins the split lines into one paragraph when rendered.
2. The new text in Decision 27 is all proposal. Whether `ssh-keygen -Y verify`, `ADMIN OPTION` on one role (Postgres 16), a read-only mount, or a second signature tool behave as written is UNVERIFIED (no run). I wrote that in the text.
3. The reviewers' coverage was partial (design review read about 40 percent of the file). I checked each reviewer claim against REVIEW.md text, and against source only where cheap (tick.py:184-217 and config.py:192 for the 400-day limits: confirmed; `git rev-list`, `git diff --name-status`, `heavy-test-lane/SUMMARY.md` lines 20-21: confirmed). I did not re-read the 4 sections they did not read.
4. Decisions I did not take (kept as questions in the text): where the next key is kept; whether the checkpoint checker and heartbeat sender have their own logins; who may lift an evidence hold; the client signing route (a/b/c); who is verifier person; who the session named by the lead is.
5. `holds` moved out of the "thirteen names": list A is now twelve names (eleven logins while agent and tick share one), list B (conditional) five names. Any outside file that says "thirteen" would now disagree; I found none in this folder's live text except the places I edited.

## Finding-to-result table
| finding | result |
|---|---|
| design B1 (expected (T) not in signed record) | Fixed as proposal: new sub-block T of Decision 27 plus Hash table; (B) now holds expected (T), mutant list, exact command, whole tests tree + conftest + pytest config + test lockfile + env allowlist; verifier refuses mismatch; six negative tests; "old code" replaced by "mutant". In-text pointers added in (T)(a) and the (B) contents sentence. Kept: one-person limit stated (sub-block O). |
| design M1 key set | Fixed: in-text contradictions edited (next key signs only revocation lists and succession; promotion needs BOTH keys); sub-block K (both signatures for any (B) or key-set change, revocation list signed only by next key, one succession message, 4 negative tests, "one drawer is nominal separation"). Open question: where next key is kept. |
| design M2 client key | Fixed: sub-block C; fingerprint also in client's own signed contract schedule; old-key countersignature to change; "detects, does not prevent"; options (a)(b)(c) as a question. Same wording edits in Decision 27 text and in ACCEPTANCE NOTE sixth part. |
| design M3 / reader M5 identity list | Fixed: IDENTITY LIST A/B/C at the class rule of the login table; criterion (9) refuses on lists A and B only and must say it does not cover C; "thirteen" corrected in 3 places; pointer added in WHICH LOGINS MUST EXIST; checkpoint checker, heartbeat sender, approver check, counting job, signing keys, spool OS users, breakglass/CI/humans placed in list C. |
| design M4 one key signs everything | Fixed: sub-block I (six keys, none shared; release key differs from routine keys; evidence key signs a short canonical summary); "about 14 signatures" marked per-key estimate. Hardware keys need the head's yes with numbers. |
| design M5 counting run | Fixed: sub-block R (offline job, no keys, read-only output, digest-pinned scratch image, result parsed from the test result file, negative tests). |
| design M6 operator split token | Fixed: database guard now MANDATORY, token only in addition; negative test must use a direct SQL write. |
| design m1 hold-and-purge race | Fixed in the `purge` row (NOT EXISTS in the same DELETE, event row first, reason field and audit for lifting, who may lift = question). |
| design m2 rotator CREATEROLE | Fixed as proposal: mechanism (ADMIN OPTION on one role, Postgres 16) or drop; marked UNVERIFIED. |
| design m3 single dependency | Fixed: sub-block D (signature tool, clock, dead-man channel; outline plus trigger each). |
| design m4 two "option (i)" | Fixed: Decision 3 choices renamed H-i and H-ii; both references re-pointed. |
| design m5 colliding M-numbers | Fixed: every bare "design review M/B/F n" now carries r32 or r30 (checked against review-design-r32.md and r30 headings); key in READ THIS FIRST (c). |
| design m6 receiver negative tests | Fixed (three refusals added). |
| design m7 one-person wording | Fixed: sub-block O wording "met (advisory, one person)". |
| design m8 long lines | Partly fixed (see failure 1). |
| reader M1 hold / ceiling | Fixed: glossary (a), (b) (evidence hold, `holds` login, retention limit; source word "ceilings" kept as a note); 6 uses in lines 215/385 changed. |
| reader M2 round tags | Fixed by correcting the two History sentences and adding the tag key; I did NOT strip the tags (about 45 lines). "a Blocker" for a reviewer's rating changed to "rated Blocker by that reviewer". |
| reader M3 hashes | Fixed: Hash table, "artefact digest" replaced by "build digest", (B) named "signed release record". |
| reader M4 dated actions | Fixed: "Who: the assistant" (5 places), Decision 22 rows and Decision 2 "builder" now "a session the lead names (not named yet)". |
| reader M6 Decision 29 | Fixed (3 places). |
| reader N1 cites | REVIEW.md edited (see re-points below). |
| reader N2 | Fixed (scoped "Nothing in THIS section"). |
| reader N3 | Fixed (3 places, 1 to 2 days low end). |
| reader N4 | Fixed (example numbers removed). |
| reader N5, N8 | Fixed (client notes go where Decision 26 says; "working day" replaced by the UTC-day wording, 3 places). |
| reader N6, N7 | Fixed in glossary (d), (e) (Q17-2 and RIGHT-SIZE stated as undefined labels). |
| reader N9 | Fixed in line 3 (fix logs are odd-numbered). |
| citations caveats | Fixed in the 487 paragraph: 964 commits at HEAD b5c1f6c00 (re-counted with git, was 952/955), 9861 is the patched lane and 9846 the baseline, "52 files under tests/ (40 with a test_ name)", 10553 stated as not re-checkable. |

## Re-points needed in files I did not edit (patch-copies)
- `patch-copies/README.md` line 8 and `patch-copies/DEAD-MAN-CHECK.md` line 4: replace `../REVIEW.md:67` by `../REVIEW.md:77` (text "3. C-01: DO NOT APPLY NOW"). It was already one line off (68) before this round. `../REVIEW.md:5` is still correct. Cite the text as well as the number; the number moves whenever a line is added above it.
- Reader N1 also: nothing else in `patch-copies/` cites a REVIEW.md line (grep).

## Raw outputs (end of batch)
```
count_review.py: rows 28; severity {'Nit': 11, 'Minor': 13, 'Major': 4}; decision {'DECLINE': 3, 'PROPOSE FIX': 25}
check_refs.py: PASS 5175 references
check_names.py: PASS 655 rows
check_secrets.py: PASS 0 hits in 2701 files
ruff format --check .: 849 files already formatted
git rev-list --count b4cce5b..HEAD: 964 (HEAD b5c1f6c00)
```
Personal handle not printed; no secret added. Times UTC with IST.
