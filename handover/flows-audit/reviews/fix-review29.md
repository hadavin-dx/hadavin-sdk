# fix-review29: fixes to REVIEW.md after round 28 (design, reader and citation reviews)
Fixer: one assistant session, static only (nothing run except the four check commands below). Edited only `reviews-of-core-patches/REVIEW.md` and this file. Reviewer words were checked against REVIEW.md and `src/hadavin_sdk` before use.

## What was NOT done or is uncertain (first)
- Nothing here is built; every design change is a proposal text in REVIEW.md. Postgres statements stay UNVERIFIED.
- Ledger rows (R28-15): `handover/ledger.md` does not exist in this checkout; I wrote the gap into the hold sentence and did not create a ledger. NEEDS THE LEAD: add rows for X-2, X-4, X-5 (X-5.1, .2, .3, .7), X-6 (X-6.1 to .4, .6, .8).
- Named doer for the first dated actions (R28-15): I may not assign a session. NEEDS THE LEAD: name the builder session by end of 2026-11-16 UTC. The file now says this is an open defect.
- `../QUEUE.md` line 12 (reader 7) is the lead's file: a superseded note was put at the top of REVIEW.md; NEEDS THE LEAD to edit QUEUE.md.
- I added X-5.7 (Major) and X-6.6e (Minor departure): my judgement under the written rating rule. The studio head may overrule (Decision 20).
- Own slip found: the old X-6.6d row said that rating it Major raises "Major parts 9 to 10 and items 11 to 12". That was wrong (a departure is not a part). Corrected.

## Finding -> result
- R28-01 -> fixed: Decision 27 (one "build digest": installed package files, lockfile, shipped config, image digest; tests/demos out; computed by the running program; signed fields add client code, scope, issue/expiry, nonce; option (ii) marked human process the program cannot check; binding stated as only as strong as the deployer's trust), hold sentence, Decision 28, criteria (8) and (9), word list. Reader 5 -> fixed by the same.
- R28-02 -> fixed in Decision 27 (hardware key with touch or separate OS user; cloud signer kinds forbidden for this key; only `verify_signature` reused, `audit/signer.py:45`; a signature is not a review; WebAuthn wording left to the head).
- R28-03 -> fixed in Decision 25 (protected environment with human reviewer; subject pinned to protected ref; agent-influenced tests never in the job holding deploy credentials).
- R28-04 -> confirmed by source (`stages.py:18-23`, `config.py:419-420`: pilot is spared). Fixed in Decision 29 (refuse signer/anchor none in every live environment unless declared non-signer; verified-signature head age check) and in X-5.1.
- R28-05 -> fixed (one liveness table per long-running program; reader uses newest VERIFIED checkpoint, not `MAX(seq)`, `chain.py:290-293`; row 242 reconciled with the 262 reads).
- R28-06 -> confirmed by source (`migrate.py:61-65`, `tick.py:196-215`, `app.py:86-89,151-160`). New row X-5.7 (Major); counts updated everywhere (Major parts 10, Major items 12, headline 10; counted rows still 4/13/11); Decision 3, table row 3, criterion (6) extended.
- R28-07 -> fixed: receiver row corrected; new departure X-6.6e; Decision 12 "WHO FREEZES" (R1 widen receiver / R2 separate program, R2 suggested), Decisions 11 and 13 cross-referenced. Design choice left to the head.
- R28-08 -> fixed: per-criterion rule departed from and exception (b) stated in the acceptance-note definition (each note also names a doer and date); criterion (2) (X-6.4) no longer ends on a note, like X-6.3 (hold sentence, criterion rows, Decisions 1, 12, 13 updated). Head can re-open via Decision 1 option 3.
- R28-09 -> fixed: the head decides all 33 (checked: each has a risk-accepting option); "Who:" = who does the work. Reader 3 -> same fix.
- R28-10 -> fixed: closing X-6.6c needs a performed rotation plus a test, or short-lived sign-in (`iam_auth` exists, `store/postgres.py:71`); Decision 21 and criterion (8) updated.
- R28-11 -> partly contested. The reviewer is right that the line "a missing design ... is Minor" is not in the written rule; it was removed. But the rule text does not settle whether an absent identity is "broken", so X-6.6d stays Minor and the question is Decision 20 option 7 (no count changes). The headline already quotes both halves (0 patch Blockers, 10 present Blocker-equivalent parts); no silent rule change.
- R28-12 -> fixed (gaps 6 to 9 added to "Undeclared logins" and criterion (9)).
- R28-13 -> fixed (decide-after cells for rows 2, 4, 8, 9a, 9b, 10, 21). Row 10 -> 29 is the reviewer's reading, marked as such by the wording.
- R28-14 -> fixed (bounded tamper claim in the Chain definition).
- R28-15 -> needs the lead (see above); text now states the defect.
- Reader 1 (Q1 pointer: item 4, plus items 1 and 7) fixed. Reader 2 (criterion signpost) fixed. Reader 4 ("no, note to follow") fixed. Reader 6 (test count units/versions; 15 = 13 failing on old + 2 passing) fixed, with the "exactly which two" part marked unchecked. Reader 7 fixed as a note. Below-Major: RIGHT-SIZE, egm-resolve, "the take", "the ceiling", D-3 four names vs six steps, duplicate sentence in line 67 all fixed.
- Citation review: M1 -> fixed by not stating a clause count and citing the clause by its wording (README is being edited by another fixer). M2 -> verified (`DEAD-MAN-CHECK.md` says rows 1, 3, 4 and 5 were run); both places corrected.

## Raw outputs (last lines)
```
$ count_review.py REVIEW.md
rows 28 ['C-1', 'C-2', 'C-3', 'C-4', 'C-5', 'C-6', 'C-7', 'C-8', 'A-1', 'A-2', 'A-3', 'A-4', 'A-5', 'A-6', 'A-7', 'A-8', 'A-9', 'G-1', 'G-2', 'D-1', 'D-2', 'D-3', 'X-1', 'X-2', 'X-3', 'X-4', 'X-5', 'X
severity {'Nit': 11, 'Minor': 13, 'Major': 4}
decision {'DECLINE': 3, 'PROPOSE FIX': 25}
$ check_refs.py
PASS 5176 references
$ check_names.py
PASS 655 rows
$ check_secrets.py
PASS 0 hits in 2795 files
```
