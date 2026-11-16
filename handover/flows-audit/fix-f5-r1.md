# fix-f5-r1: F5 fixer round 1 (of max 2), change log for RUNSHEET-WORDING.md, 2026-11-16
Static reading only; nothing ran. Findings checked against the flow JSON and the sources first. No reviewer has seen the rework yet.
W-01 fixed: new "Goes where" column (SCREEN, VOICE, CARD, PAGE, LEAD) plus flow set and scene per row; "Paste this" split from "Note to lead".
W-02 fixed (blocker, confirmed): AlertClaim 720 s hold, AlertMark only after a good send, AlertBackoff, no cap, so the alert can repeat. Spoken text has no count; written text says "normally one; it can repeat". Rows A-021, A-057, A-076, A-077, B-077, N-4.
W-03 fixed (blocker, confirmed): scene 9 shows the mail in the stand-in list. New wording: n8n got no confirmation, so it cannot know whether the mail arrived. Rows A-021, A-033, A-035, A-077.
W-04 fixed: "took" replaced by "received" (A-030).
W-05 fixed: "went" replaced by "arrived"; the cut connection is described (A-033, A-035).
W-06 fixed: viewer line has no K1, lane3 or film-v4; D1 default is no number, alternative given; sources only in lead column (A-017, A-019, A-051, A-081).
W-07 fixed: lease explained before the label; row N-5 and the words list.
W-08 fixed: "mail" = e-mail message, "e-mail address" always says address; words list; A-010, A-053, B-010.
W-09 fixed: plain sentence on what n8n may keep and what the lead table keeps (A-010, A-053).
W-10 fixed: "six columns, none holds a name or e-mail address"; "capture one screenshot" (A-040, A-042).
W-11 fixed partly: spoken line added; the built alert text "A person decides." stays on screen because I may not edit the flow (FIX-PLAN item 7 has no patch). Needs lead decision D3.
W-12 fixed: review row sentence in N-3 and A-057, A-091 (only marked, no alert, someone must check the table).
W-13 fixed: scene 5 pane tag is "Stand-in CRM: a test copy of the customer list, not a real CRM" (lead answer kept, jargon glossed).
W-14 fixed: mail pane resolved by address evidence (example.test cannot be a real mailbox) with its own tag; C2 closed unless the lead overrules.
W-15 fixed, differs from claims table: the card no longer holds "say on screen" (note about the video); reason stated at the top of the file.
W-16 fixed: A-005 plain words, same string as the claims table.
W-17 fixed: A-016 result spoken only after it is read off the take.
W-18 fixed: one numbers rule; no pooled range; per-stop-point figures only (A-073, A-076, A-081, A-019).
W-19 fixed: T8, harness, lane3, K3=K3B moved to lead column; page text is plain (A-059, A-073, A-076, A-077).
W-20 fixed: "not lost in those 2 runs" (A-023, A-075, A-088).
W-21 fixed: page statements marked PAGE (public reader) vs LEAD; unknown-audience problem removed.
W-22 fixed: "capture one screenshot", "take" kept only for a filming run.
W-23 fixed: one name per column, with the on-screen name once in the words list.
W-24 fixed: double quotes outside, single quotes inside.
W-25 fixed: "claim window" explained in A-098; "claim" and "window" no longer used loosely.
Disputed: none. Unverified: all relayed numbers, P1, P2, P3, D1 to D3, what program is the stand-in mail server, T8/T15 meaning.
