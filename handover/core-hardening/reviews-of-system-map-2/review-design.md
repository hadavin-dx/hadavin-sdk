# Design reviewer (egm:egm-design), round 1 — condensed copy saved by core-hardening
Verdict: PARTLY CORRECTED, NOT CLEAN. 0 Blockers, 4 Majors, 6 Nits. Nothing edited by the reviewer. Base: SWEEP.md Fix plan 367-394, Decisions 396-422, Exceptions 424-454, ONE-PLACE-TABLE.md.

## Failures first
D-1 Major. SWEEP Decisions A (401-406): dollar cap not costed; limit left blank; option 2 "cost" cell holds finding ids; hard-stop claim UNVERIFIED with no fallback; not linked to L7-FD-005 / row 19. Fix: compute a rough dollar figure from the price page, give option 2 an agent-day estimate, add "if no hard stop then option 2 or prepaid cap", tie A to row 19.
D-2 Major. Decisions B (409-414) vs Fix plan row 5, line 19, ONE-PLACE-TABLE 112, Exceptions 454: table recommends option 2, prose recommends option 3 plus heartbeat for the video; watcher still called "open question for the laptop lead" in three places; no time/money per option; heartbeat does not cover slow SMTP (L2-FD-008); heartbeat on same machine shares failure domain; rows 4 and 6 (Blockers, default "after") have no decision note. Fix: one recommendation per period, name studio head everywhere, say what heartbeat misses and where it runs, add time estimates, add a note for row 4.
D-3 Major. L2-FD-018 (SWEEP line 52) is a Blocker while the row says values are made-up; Decision C says rotation then costs nothing; next step is old framing; public status rests on "CLAUDE.md says" (unconfirmed); gitleaks coverage unanswered. Fix: rate conditionally (Major if all stand-ins, Blocker if any real), point next step at row 7, mark publicness UNVERIFIED or cite evidence, say if gitleaks scans.
D-4 Major. Independence of the proof count is not checked before the video: ONE-PLACE-TABLE 74 makes the independent count the owner; claims check 471 says only artefact seen is a code node in the same n8n and Postgres; its identity and read scope are in no file; its scope checks (rows 12, 20) come after Wed 18 Nov. Fix: add a before-video check to row 22 or a new row naming process, user, credentials, and whether it runs outside n8n.
D-5 Nit. ONE-PLACE-TABLE L6-J-058 (131) verdict still NOT-NEEDED; lead asked CHANGE.
D-6 Nit. L6-FD-004 (SWEEP 59) says "no Fix plan row" but row 2 lists it.
D-7 Nit. Decisions D (419-420): option 3 "nothing" is the pre-video default; no interim mitigation named; costs only agent-days.
D-8 Nit. Decisions E (422) / row 13: cost of "normal commit now" not stated.
D-9 Nit. REPORT.md line 70 older FINAL still quotes 314/307; newest says 322/315. Mark superseded. (Reviewer checked the Counts arithmetic: 18+218+86=322; 14+215+86=315.)
D-10 Nit. REPORT.md line 14 "grep finds 0" does not prove the new rows say what the lead wanted.

## Lead's review items (design)
1 counter owner DONE (independence still open = D-4). 2 dollar cap PARTLY (D-1). 3 L6-FD-004 DONE. 4 rows 15-17 DONE. 5 key rotation/history MOSTLY DONE (D-3). 6 second alert channel PARTLY (D-2). 7 Postgres identities MOSTLY DONE (D-5). 8 LOG audit DONE. Missed items: L7-FD-001..007 present as findings and Fix plan rows 19-22; thin as ONE-PLACE-TABLE credentials rows.
Re-ratings L1c-FD-001, L1c-FD-021, L6-FD-004, L6-FD-003 (kept Blocker, flagged arguable), L7-FD-005 (Blocker) right and explained; L2-FD-018 not re-rated (D-3). L7-FD-008 rated Nit but tracks two Blockers: label as pointer.
Owner decisions A-E: options real; costs are the weak part (mostly "free tier UNVERIFIED", "about one agent-day", blank). Lock-in: A and B each add a vendor/channel with no replacement trigger.
## Not read / not checked by this reviewer
SWEEP findings table lines 38-366 except cited rows; Claims check beyond quotes; QUESTIONS, README, ORDERS, STATUS-BOARD; MASTER-MAP and lane files; take repo; n8n flows; GitHub state; whether repo is public; provider hard-limit behaviour; prices; whether stage runs as an n8n child process. Only three source lines grep-confirmed (limits.py:17, k1b/loop.py:41, tick.py:4).
