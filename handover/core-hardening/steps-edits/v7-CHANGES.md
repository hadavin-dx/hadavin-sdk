# v7 changes: one row per review finding (review-c4b-v6-naive.md, review-c4b-v6-design.md) plus the extra naive findings in the brief
Line numbers are lines of `OWNER-STEPS-realrun-v7.md`. FIXED = changed in the sheet (not run, not verified by anyone but me; reviewers judge). LEAD-OPEN = needs the studio lead, question in `v7-NOTES-FOR-LEAD.md`.

## Naive reader
| Id | Status | Where in v7 / reason |
|---|---|---|
| 1 who stops n8n, who films | LEAD-OPEN (not invented) | run card rows 4, 5 (L43, L48); table rows "Run: n8n stop and restart", "Run: filming"; owner text says "the person named on run card row N"; exact questions in NOTES section 1 |
| 2 boxed warning before step E; step G Trash | FIXED | boxed warning before E (L193); G box says emptying Trash cannot be undone and when not to empty (L227); G.1 repeats the check (L231) |
| 3 `cat` from the scripts folder; unset if step 3 fails | FIXED | step 0 item 3 (full path or `~/<name>`, why plain name fails); "If you stop for any reason in step 0 ... unset" (L150) |
| 4 missing who-types-what rows | FIXED | table rows E.0 (throwaway message), E.2 (notice compared), 0.3 / E.5 / I.4 (`echo $?` and paste), I.1 / I.2 / I.3 (screenshots), I.6 ("secret files deleted"), J ("posted"); send-table in sync (L275 on) |
| 5 editor notes in owner text (L3, L13, L66, L136, L153, L168, L169, L173, L199, L214, L231) | FIXED | removed; moved to NOTES section 2 with the original v6 line for each; grep of v7 for "UNVERIFIED", "[Not", "open" finds none in owner text |
| 6 run date vs stop time; "default is no" | FIXED (date itself LEAD-OPEN, L33) | Dates paragraph (L112); run card column renamed "If the row is missing" with the right action per row (L38 on) |
| 7 words with two meanings | FIXED | "lead" only in "studio lead" (Words box line 1); test person's id renamed "person id" with screen names given once; "run" = recording run, "start" for the verb; archive/Archive/"archived" separated in "Delete" entry; "take" explained; key vs token explained in "Key"; "step" = lettered step, "item" = number in a step; "pass" replaced by "succeeds / success"; notice vs notification defined in "The notice" |
| 8 backstop rule; US$189 | FIXED | Words box "Spending backstop" explains US$189 (credit in the model account, backstop at US$180 of it); step E "Compare the notice" gives five concrete answer-no cases (L202 on); cost section points to it |
| Minor: finding contacts by run name unchecked; expected contact count | FIXED | step F: expected 2 or 3 contacts, stop and wait if the search shows nothing or another count |
| Minor: "closed input", "piped", "hard budget 8" | FIXED | "closed input" explained in step E; "piped" replaced by "fed in by another program"; "hard budget 8" dropped |
| Minor: Words box too long | FIXED | dropped hook door, Postgres, saved runs, journal detail, edited video, live accounts, label folder detail, rehearsal detail shortened |
| Minor: "rules 1 to 7" count | FIXED | "rules 1 to 8" in intro and rule list |

## Design review
| Id | Status | Where |
|---|---|---|
| M1 false "delete works" | FIXED | step 0 item 7: three answers; SKIPPED or FAIL on create or delete = "delete not shown"; owner gives no written yes until told; key permissions named on run card row 14 (names themselves LEAD-OPEN); read-only key called a permission problem. The "no yes until told" rule is my choice (NOTES L30) |
| M2 script copy not current | FIXED in sheet, checksum LEAD-OPEN (L19) | checksum row 14, step 0 item 2, table row 0.2; "should" wording; `echo $?` right after the probe, before `unset` (item 5); paste rule for `pat-` text (item 6); unset and close terminal in every stop case (L150) |
| M3 lead values clause, rule 8, form check, shred list | FIXED | intro paragraph (rules 1 to 8, exact form rule); I.6 refusal list (L257); `cat` path from the card only (step 0 item 3); model key file rule needs confirmation (NOTES L32) |
| M4 clean-up deadlock | FIXED in sheet, decision LEAD-OPEN (L31) | run card row 15; I.2 branch "kept on purpose"; I.4 three "STILL WORKS" cases |
| M5 memory check, CHANGES overclaim | PARTLY FIXED | tags replaced by run card row 13 (covers C.1, C.2, D, G, I.2, I.3, I.7); the memory check itself was NOT done (files unreadable), L28 stays open. The v6 CHANGES line "tagged" overclaimed: v6 had tags on C.2, D, G, I.2 only, not on C.1, I.3, I.7; v6 is not edited, this row is the correction |
| N1 spend wording | FIXED | cost section ("at most one per test person ... failed call is not tried again"); step J "at most once" |
| N2 step J DM limit, least-privilege claims | FIXED | step J must-not-say list (crash between sending and noting; permissions claims) |
| N3 person id; one word for second count | FIXED | Words box "Test person" (L + hex, subject `[demo] lead <person id>`); "separate check" used everywhere |
| N4 L3 wrong question; tab-title note | FIXED / LEAD-OPEN | L3 moved to NOTES; step D.1 tab-title note restored (wording from my knowledge of Gmail, NOTES section 3) |
| N5 untagged paths | FIXED | "(path not checked)" on Remove (I.1), Trash icon (G.1), Empty Trash, clipboard history (C.3); C.3 sign-in is in the profile step; I.7 sign-out is under row 13 (no click path given) |
| N6 C.2 vs C.3 contradiction; clipboard | FIXED | C.2 says sign in to n8n only if item 3 says so; C.3 clears clipboard history |
| N7 6 lines vs 7 calls; `--yes-spend-calls`; probe contact in film; Trash | FIXED | step 0 item 4 and 6; D.8 (probe contact must not be filmed); G.1 "if Trash holds anything else, stop" |
| N8 table order; python vs python3 | FIXED / LEAD-OPEN (L29) | rehearsal gate row now before A; `python3 -I` everywhere |
| N9 v3 deadline 18:29 UTC | FIXED | Dates paragraph: watch and clean-up by Mon 23 Nov 18:29 UTC (earlier plan), card may be earlier |

## Not done
- C9 (S9-1..S9-5): not available; placeholder in NOTES only.
- Memory check against the memory files: not possible here (L28).
- Nothing was run or tested; the sheet has not been read by an independent reviewer.
