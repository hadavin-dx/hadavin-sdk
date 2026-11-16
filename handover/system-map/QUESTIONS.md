# QUESTIONS (only the studio lead or the owner can answer)
Decisions only; actions are in TAKE-BLOCKERS.md. Decisions made on 16 Nov are in inputs/DECISIONS-2026-11-16.md and are not repeated here. Open: item 2 only (D-04, D-05). Item 8 is answered (lead 10:23Z). Item 2 blocks the post (Wed 25 Nov), not the take. Item 1 is answered (lead 10:13Z).
1. ANSWERED (lead 10:13Z): the take never deletes. `end` stops the take and lists leftover made-up contacts by lead key and contact id; the owner deletes them by hand. Replacement lines: decisions/M17-end-never-deletes.md.
2. D-01 to D-03, D-10, S-03, L-01: ANSWERED, APPLY as text edits (lead 10:13Z). D-04 and D-05: note written (decisions/D04-D05.md); the lead decides; reply "D-04 apply, D-05 apply" and name who edits step J. Post only, not a take blocker.
3. Decision 12 makes the studio lead the runner of the first rehearsal, and plan-wp6-resmoke-v5.md:489 says "never start Docker Desktop (the lead does, P-4)". ANSWERED (lead 10:13Z): the lead starts Docker Desktop, not the owner.
4. ANSWERED (lead 10:13Z): the sender app-password file is owner-held; no session reads it. Item removed.
5. ANSWERED (lead 10:13Z): after the take, archive, never delete; the lead decides per row (ARCHIVE-CUT-LIST.md).
6. ANSWERED (lead 10:13Z): take prep is ONE made-up lead through the real chain inside the owner's written yes with numbers; the lead removes its contact and mail by hand before step 1.
7. ANSWERED (lead 16 Nov 10:13Z and 10:20Z): the take imports the PATCHED real-v5 copy (F-002 and F-008 applied, then the fill_flows values); the lead imports it; the file and its sha are named once in v5 and the plan. Still to do: regenerate, run flowcheck on the final folder, run test T19 on the laptop, check n8n's run list and the Postgres tables for stored lead data (F-008 turns saving on). "Processed once" stays NOT VERIFIED until T19 passes.
Answered by the 16 Nov decisions: scope (1), HubSpot delete scope (2; item 1 answered: the take never deletes), security items (5), licence test (11), who runs the first rehearsal (12; item 3 asks only who starts Docker).

## Note on item 7: SUPERSEDED by the lead's answer of 16 Nov 10:20Z (patched copy). The earlier recommendation of the unpatched files is withdrawn.
Checks that stay: regenerate the patched copy, run flowcheck on the final folder, record its sha, run T19 on the laptop, check n8n's run list and Postgres tables for stored lead data. Keep "processed once" out of the caption until T19 passes.

## 8. Does the film pause stay? ANSWERED (a) by the lead 16 Nov 10:23Z: the pause stays; `end` stops the take and lists leftovers, never deletes. Card v2 applied. (added 16 Nov, system-map session)
ANSWERS 10:13Z item 1 says "film-v5 is out, so no film pause" and also says `end` stops the take and lists leftover contacts. (Historic question, answered above.) Both cannot hold unless the program still pauses after the 3 contacts exist. Which is it: (a) the pause stays (the owner films the HubSpot list, then types `end`); (b) no pause. The run-day card draft (work/run-day-card-draft-v2.md) assumes (a). Needed before the card is replaced.
