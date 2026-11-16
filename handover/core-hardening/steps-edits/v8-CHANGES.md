# v8 changes: one row per finding (review-c4b-v7-naive.md, review-c4b-v7-security.md)
Lines are lines of `OWNER-STEPS-realrun-v8.md`. FIXED = changed in the sheet; no one but me has read the result and nothing was run. LEAD = needs the studio lead (question number in `v8-NOTES-FOR-LEAD.md`, "NFL").

## Security review
| Id | Status | Where |
|---|---|---|
| B1 backstop above yes total | FIXED in sheet; code side LEAD (NFL 1) | L21 (backstop must be at most yes total), L127-135 (cost section), E.2 L225-229 ("more than the total in my yes" = no), step A L178 |
| B1 model key stays valid, no revoke step | FIXED default; LEAD (NFL 2) | row 16 L66, table "I.5b", step I.5b L286, I.6 model key file rule |
| B1 stage stopped after the run | FIXED; LEAD confirms (NFL 3) | table row "After the run: model program", step E finish line, step I intro |
| M-1 paths form check vacuous | FIXED forms; real names LEAD (NFL 15) | Words "Secret files" L22, step 0 intro, step A (`cat` form, equal to row 8), C.3 form, I.6 |
| M-1 `cat` of stage.env prints a secret | FIXED | rule 9 L148, step A L178, E.2, NFL 14 |
| M-2 delete not proven by exit 0 | FIXED | Words "Exit code" L, step 0 item 6 and 7, table 0.3 |
| M-2 8th call / read-back / delete route / sibling files / plan after checksum | FIXED in sheet; facts LEAD (NFL 4, 5, 6) | row 14 L64, step 0 items 1-2 (checksum first, then plan), item 7 |
| M-3 scopes, clash, key expiry, kept-key date | PARTLY (scope names not written: unverifiable); decision LEAD (NFL 7, 8) | step 0 paragraph, row 14, row 15 L65, I.2 |
| M-4 clean-up deadlock | FIXED defaults; LEAD (NFL 9, 10) | row 15, "card rows change" paragraph after the run card, I.1, I.4 "If the check cannot succeed" |
| M-5 shred/rm lead-supplied names | FIXED | I.6; lock-file box and form at "Other refusals" L335-337; wording "removed" |
| M-6 trial run | FIXED default no trial; LEAD (NFL 11) | Words "trial run" L14, row 6, step T L252, table, step G heading, step A |
| M-7 masked sender/receiver | FIXED; LEAD (NFL 13) | Words "The notice", step A, step E, table E.0, E.2 |
| M-8 film check account ids | FIXED | step D item 8 L210; D end line |
| M-9 post wording | FIXED; LEAD (NFL 16) | step J: conditional "processed once", no "separate check/login" (Words entry "Separate login"), crash-safe ban not lifted by rehearsal (also Words "Crash-safe"), added bans "deleted permanently" and approval |
| N-1 clipboard/scrollback | FIXED | C.3 (close the terminal window, never paste into chat) |
| N-2 Snipping Tool originals | FIXED | I.1 |
| N-3 checksum for run_real_check_n8n.py; BL-wp6-G1; provisional head | FIXED except BL-wp6-G1 (not found, NFL 21) | row 14, step E, "What is not proven yet" |
| N-4 saved runs hold throwaway addresses | FIXED words; deletion by lead stated | Words "n8n's saved runs", I.5 |
| N-5 lead runs as same Linux user | FIXED | Words box, "The studio lead's commands run as the same Linux user" |
| N-6 evidence-2 real names | LEAD only (NFL 20) | not a sheet item |
| N-7 "tick them" select-all | FIXED | step G item 2 |

## Naive review
| Id | Status | Where |
|---|---|---|
| Major 1 step 0 no box / safe default / stop cases / general go-ahead | FIXED | L5 box, L152 box, step 0 item stop list, "go step 0" row 0.0 |
| Major 2 exit 0 reading; SKIPPED | FIXED | step 0 items 6-7; table 0.3, Words "Exit code" |
| Major 3 8th call contradiction | FIXED in sheet (N from the card); fact LEAD (NFL 4) | step 0 items 2 and 4 |
| Major 4 `cat` of stage.env, filming, do-not-paste | FIXED; LEAD (NFL 14) | rule 9 L148, step A, C.3, step 0 item 3 |
| Major 5 model key owner step | FIXED default; LEAD (NFL 2) | I.5b, row 16 |
| Major 6 who stops n8n / films | PARTLY: cue added, names LEAD (NFL 12) | step E (run started cue), rows 4-5 unchanged |
| Major 7 C.3 vs "owner does not rebuild" | FIXED | intro L7, table C.3, C.3 closing sentence |
| Minor editor text L3, L12, L19, L136, L112 | FIXED | L3 header sentence removed; stand-in re-smoke wording removed; source note removed; "the studio lead says the script should" removed; "aim is missed" replaced (L127) |
| Minor undefined terms (re-smoke, Postgres program, saved runs, database container) | FIXED | Words L24-25 and step J, "not proven" (re-smoke no longer in owner text; "rehearsal" used) |
| Minor table vs prose (C.1, E.0 omit row 13; "Rehearsal values" row position; send-table) | FIXED | table rows C.1, C.2, C.3, D, G; Rehearsal values row moved before the gate (L83); send table updated; screenshots path: send table says saved, not sent |
| Minor contact count with unknown C; alert mail | PARTLY: owner told the lead will say; decision LEAD (NFL 17) | Send counts paragraph |
| Minor two-meaning words run/check/pass | PARTLY: "run" and "trial run" defined; "pass" only in rehearsal gate wording; not fully audited | Words box |
| Minor I.1 browser profile | FIXED | step I intro: normal profile, not `demo-take` |
| Minor run name reuse after login stop | FIXED | step E run-name bullet |
| Minor CHANGES line numbers off | FIXED by recomputing from this file; "open absent" claim dropped | this file |

## Must-do list from the brief
Box and safe default above step 0: L5 and L152. Exit 0: step 0 item 6. 8th call: step 0 items 2/4. Printed forms: Words, step 0, A, C.3, I.6. Full-path shred with ls -l: I.6. Trial-run step: T. Masked notice: step E. Account ids: D.8. Post wording: J. Editor text: removed. Plain words: added.

## Not verified / not done
- Not run, not independently reviewed; I could not verify any script fact (hubspot_probe.py absent from inputs), the 204-on-missing-id, scope names, Snipping Tool or clipboard behaviour, or BL-wp6-G1 (not found).
- C9 not applied (file missing).
- Whole-sheet audit of "run/check/pass" two-meaning words not completed.
