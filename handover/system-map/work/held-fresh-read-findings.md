# Fresh-read findings on held pages (one read after the archive-sentence edit; cap: no third read)
Rules for fixers: fix every item that needs NO new fact from the lead. Where a fact is missing, write "[lead fills: <what>]" once, say who and by when if known, and keep UNVERIFIED marks. Never write the owner's personal name. Use "owner" for the person, "lead" for the Claude session giving orders. Plain words, UTC and IST.

## README.md
Blocker L1-7: no purpose sentence; undefined: real-v5, film-v5, BL-wp6-G1, T19, "processed once", DESK_URL, loopback re-smoke, M17, D-01..D-10, S9-n. Add a first line saying what the demo shows and one-line meanings; move glossary (L28-29) to the top.
Blocker L3: row 1 has no named owner: write "Row 1 owner: [lead fills: name], due [lead fills: date]; until named, the lead does it".
Major L6: long conditional sentence with <tag> undefined: split into what happens / what is unverified / what you do.
Major L5, L19: "decision 1", "decision 12", "lead 10:13Z item 3" point to no file: link work/LEAD-ANSWERS.md or decisions/.
Major L16 vs L19: who sets the take time: say the lead sets it (row 4).

## QUESTIONS.md
Blocker L1-4: never defines take, post, step J, D-04/D-05, T19, F-002/F-008: add a short glossary and one line per D-04/D-05 (read decisions/D04-D05.md). Ask: "D-04 apply, D-05 apply" and who edits step J (answer 14: core-hardening edits step J).
Major item 1: one long sentence: use "Answer / Status UNVERIFIED until loopback re-smoke 17 or 18 Nov".
Major item 2 says ANSWERED and open together: split.
Major item 8: option (a)/(b) question after ANSWERED: move to a history note.
Major item 7: five undefined checks (flowcheck, T19, sha, n8n run list, F-008): one-line meaning each.
Major L10 says "(2)" and "item 2" for different things.

## OWNER-VIEW.md
Blocker L12, L14: line 14 is one 400-word paragraph of about 12 steps; step 7b pasted twice (L14 and L23) with a [UNVERIFIED] note the owner cannot act on; the yes is defined in three places (L12, 14, 21) with different lists. Rewrite as a numbered list, one action per line (who / says what / you do); keep 7b in one place; one definition of the yes.
Blocker L6: "no later day exists on Mon 23 Nov" beside "target Wed 18 Nov"; "noon" has no referent. Rewrite: "Take on Wed 18 Nov; if that fails, at the latest Mon 23 Nov. Start no later than 17:30 UTC / 23:00 IST."
Major L12: glossary "Words" mixes rules; move to top, one-line definitions.
Major L2, L29: "round 2", "ORDER 017", "rules A, E, F and I", "T19", "decision 3 of 16 Nov", "real-v5", "loopback re-smoke": define or remove.
Major L27 row 7: "HubSpot check" and "which login key to replace": say what each is and who owns it.

## OWNER-RUN-DAY-CARD.md
Blocker L31, 35, 59: "[studio lead fills: ...]" placeholders: keep as "[lead fills: ...]" with a one-line what-to-look-for the owner can use; say these must be filled before the card is used (this is a lead fact: do not invent).
Blocker L38: no way to check a run name is new: add "The lead confirms the name is unused".
Blocker L41, 49: "spending backstop figure in stage.env" and "UNKNOWN" for how the lead sees the pause: add a fallback: the owner writes "program paused" in the chat and waits for the lead's reply.
Major L2, 5, 8, 25: "studio lead" vs the Claude session: use "the lead (a Claude session)" at first use, then "lead".
Major L50, 54, 59: archive/delete conflict: "Archive by hand only. Delete only on the lead's written word 'contacts may be deleted'." Make steps 22, 23, 25 agree.
Major L45: step 15 vs step 21 circular: reference step 21 explicitly.
Major L49, 52, 53: "click chat box" repeated: move once to the rules section.

## OWNER-CLEANUP-CARD.md
Blocker L2: one 400-word sentence: split into labelled blocks Words / Start conditions / Safety rules.
Blocker L15 step 4: result codes muddled (0 refused, 3 STILL WORKS, 2 could not tell): make a table output / number / action. Name the check one thing ("retire check") and define it in step 4.
Blocker L16 step 5: "retire check passed" defined only mid-sentence.
Major L10 and L17: deadline paragraph contradicts itself; move stray L17 note into step 4.
Major L2, L6, L20: "see OWNER-VIEW, the order of messages" has no path; define v5, run-day card, demo-take Chrome profile.
Major L6: HubSpot contacts paragraph marked UNVERIFIED and "not again here": drop or say why it is here.
Major step 3 says "four file names" but step 2 gives before/after screenshots: state count per step.
Major step 6: collect the exact phrases to say in one list.

## LEAD-PAGE.md
Blocker L2,13,17,32-39: v3/v5/OS/OWNER-VIEW/cards/TAKE-BLOCKERS rows used undefined. L17 glossary is a 3,000-character paragraph: split into bullets, each definition once ("OS = v3 (archived). v5 = current; cite v5 only"); repeats at L23 and L34.
Major L8: LP-2/LP-3 missing from the list; "section 3" cited for both list and deadline: "LP-1, LP-4, LP-5 are open; LP-3 may wait". Expand LP = lead point.
Major L5 vs L43: match items.
Major L20 vs L6: one rehearsal-time statement.
Major L62, 64, 72: "UNKNOWN" / "ORDER 013 unknown": delete or give a source.
Major: "lead" in LP-4 / L48 / L66 means a sales request: write "sales lead (a person who asked)".

## TAKE-BLOCKERS.md
Blocker L2: "Next action: row 1" needs a builder: "Lead: name the row 1 builder and a finish date (UTC and IST) today."
Blocker L33 (row 1): 400-word cell: split into numbered steps INPUTS / RULES / done-when; name the tool (fill_flows.py) and which patches first.
Major L34 row 2 ends mid-thought; "must choose" without when.
Major L37 row 5: mixes clean-up wording, HubSpot check, login-key choice; "OWNER-VIEW row 7" undefined; no deadline.
Major L47-55: legend for T1, B1, C3, X1, E1, E3, E5, L4, C1, H1.
Major L28: deadline sentence nests four overrides: one table with the final times.
Major undefined: F-002/F-008, QUESTIONS.md item 7, MASTER-MAP L8-X-005, "stage".

## QUEUE.md
Blocker L1-9, 36: terms undefined (take, real-v5, film-v5, N-lite, board, board beat, STATE FINAL, decisions 1,2,4,5,7,11, ORDER 021, ring): add a 10-line glossary at top.
Blocker L6: "Decisions in force" run-on: numbered lines, who decided what.
Blocker L1 vs L11-39: status brackets unreadable (M3, M14): one fixed order State | date | owner | due | percent | open items, detail on a line below.
Major L41: percent legend to the top. Major L13,14,20,28: explain drift/REPORT.md row 101, "B3 row-number keying", "licence files". Major L2, 41: UTC and IST throughout (no bare Z). Major L23-40: REFILL headings repeat: add the REFILL time in IST.

## SWEEP.md
Blocker L135-158 and L303-326 (L3-FD-001..042, L3c rows): rows hold only citations; L157 admits "claim sentence missing". Rewrite each as "<one-sentence defect>; evidence: <cites>" (read the cited files to write the sentence; if a row cannot be stated, mark it NOT-READ with the reason).
Major L44 (L1-FD-021): counts contradict ("two files", "2 files", 79 lines in 9 files vs 72 in 5): restate as "Full name on 1 line in each of 2 files (list); login name on 7 lines in 3 files (list)" after re-checking (never print the personal name).
Major: undefined ORDER 007 (5, 491), ONE-PLACE-TABLE.md (5, 390), ARCHITECTURE-AUDIT-CHECKLIST.md (452, 474), mf-form/mf-hook/mf-recovery (47+), GREP, Fc, GO-1, WP6 P11, "ARCHIVE BLOCKED" (380, 390), ids L6-J-028, L6-J-058, L1-J-004, L5a-C-015: add to glossary at L36.
Major L5, L11-17: 797 map rows vs per-job totals of 49 not reconciled: add one reconciling sentence.
Major: "Re-smoke" used from L373, defined L400: move into glossary.
Major L403-404: owner's dollar limit and agent-day estimate blank "___": mark "[lead fills]" with who and by when (decision due 17 Nov); do not invent.
Major L34 severity rule vs L100 and L192 ("Blocker by the table" but rated Major): make consistent.
Major L491: "3 merged rows" vs 4 Blockers removed: reconcile.
Major L455 vs fix plan row 5: second alert channel responsible person: make consistent.
