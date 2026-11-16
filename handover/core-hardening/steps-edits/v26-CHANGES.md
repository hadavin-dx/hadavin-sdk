# v26 changes (builder, Mon 16 Nov 2026). Failures and gaps first.

## NOT fixed, not shown, or not decided
1. Nothing here was run on real vendor pages, buttons, Windows, WSL, PowerShell, n8n or HubSpot. All of it stays UNVERIFIED. The only things run are the build, the checker, the planting test, the fail proof, `bash -n` on the key-save line, the arithmetic and the banned-word count (evidence-v26/).
2. No independent review of v26 has happened. The builder did not start EGM or the evidence runner (the brief said not to). The lead runs both on the built files.
3. Word limit: met, with a margin of 65 words by `wc -w` and about 38 by a `\w+` count. Sheet A has 6,435 words and sheet B 6,434 by `wc -w` (limit 6,500; the brief asked for under 6,300, which is NOT met: the v26 safety steps added about 480 words after the first cut of wording, and further cuts would have removed safety steps). The independent regex count of v25 was 25 words above `wc -w`; mine is 27 above (6,462 for A), so the margin below 6,500 is thin.
4. Decisions that stay with the lead and the owner: sheet A or B (Open 71, 82), the 7 day rule and the time of 7.11 (Open 78, 79, 86), the whole balance as exposure (Open 83), the phone walk-through (Open 80, 84). B is worse than A for money after the fixes (Open 82); the choice is not made here. ORDER 034 is not shown as met.
5. The checkers test listed properties, not meaning. A different wrong figure in a place no check watches still passes. Pointer check C19 was rewritten with `ACCEPT_POINTERS=1` after I read the new pointers myself; it was not read by anyone else.
6. The Gmail label and the Chrome profile: no click path is written (not known); the sheet tells the owner to ask the lead (5.4, 5.5) and the lead must answer from a tested path, never a guess (Open 85).
7. The three checks of v25 are summarised, not re-run: I read review-v25-stranger.md, review-v25-security.md and evidence-v25-independent/ only.

## Findings of the v25 checks: finding, fix, check that fails on v25
Checks C70 to C103 are in newchecks-v26.py (Part 3). `python3 v26-fail-proof.py` plants each missed plant in the built v25 files and shows the intended check failing on the planted files and not on the unplanted ones (evidence-v26/05-fail-proof.txt). Plants that only exist in the new text (no v25 equivalent) are proved by mut26.py (144 plants; a plant counts as caught only if the check meant for it fails; evidence-v26/04-mut26-output.txt).
| Finding | Fix in v26 | Check that fails when the fix is undone |
|---|---|---|
| Stranger blocker: the irreversible older-key cancel came too early | A: cancel only at 6.7, after 6.6 (new key saved, size checked) and the last checks; "restarted" word at 6.6 | C89, C85, C28 |
| Security M3: A cancelled before the key was saved | same as above | C89 |
| Card: N and N-1 counting, shared blanks | "exactly the rows you wrote minus K"; separate blanks for the run key and the older key | C87, C28 |
| Card: blanks filled after create looked like blanks filled before | three labelled groups of blanks | C90 |
| Card: two lettered lists with the same look | renamed W1 to W9 and L1 to L5 | C53, C28 |
| Card: per-key limit and scopes missing before create | 6.3 form step | C100 |
| No signal that the lead restarted the model program | "restarted" (6.6), one of six lead words (R8) | C85, C60 |
| No human backup channel | backup person is a human you can call; none named: no run | C92 |
| FREEZE with a live key | FREEZE says the card first | C91 |
| Security M2: B older-key cancel had no time and could be missed | own step 7.11, latest time 16:00 UTC = 21:30 IST (before 18:14 UTC), irreversibility repeated, owner confirms even if the lead is silent | C86, C27, C88 |
| Sample numbers message lacked slots the steps need | all slots added | C99 |
| Seven fixed setting names, recording OFF before 5.7 | 5.7 names the seven settings and does 6.1 first | C81 |
| Key-file path rules | no `..`, file name contains the run name, inside the take folder | C82 |
| R7 prefix | `take-<run name>-` or `prep-`, ending `@example.com` | C83 |
| Deleting the key file | 8.1 `rm --` then `ls -l` must say no such file | C84 |
| Last-resort reversibility, entry to revoke | named in the numbers message; the entry is the exact name given | C99, C27 |
| Post checker valid answer | only "matches the sentences", in their own words | C93 |
| 7.10 mismatch action | send the counts, do not post, FREEZE | C94 |
| Gmail label and Chrome profile how | ask the lead (both places) | C95 |
| Words with two meanings; deadline unexplained; 8.7 profile name | glossary wording; deadline defined; `demo-take` removed only | C98, C96, C97, C103 |
| N01 IST label, N05 R5 word, N10 warning, N11 post-by date, N12 passive R7, N14 `date` for `date -u` | one check each | C70, C71, C72, C73, C74, C75 |
| Security M4: price line, tokens, DEADLINE line, yes-line deadline pair swapped | one check each | C76, C77, C78, C79 |
| C55 slash gap: a 47-character secret with a slash was skipped | the skip rule now applies only to the start-line name; a self-test of the scan | C80, C55 |

## Words cut to pay for the fixes (nothing safety-related)
About 680 words of explanation were shortened or removed (examples in the glossary, repeated reminders, parenthetical hints, the second sentence of several steps). No step, stop rule, limit or set phrase was removed. The `.used` file-name rule of v25 is gone with the file-name check it belonged to.

## What changed in the packaging
build-v26.py, check-v26.py, newchecks-v26.py, mut26.py, facts-v26.py, pointers-v26.txt and v26-fail-proof.py are copies of the v25 files with the changes above. facts-v26.py gained one fact (the 7.11 time) with an assertion that it is before 18:14 UTC.
