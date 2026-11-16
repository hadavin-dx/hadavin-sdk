# TAKE-BLOCKERS: the one page for the studio lead (16 Nov 2026 about 11:15 UTC / 16:45 IST)
Made-up data only. This page lists only what stops the filmed take. Everything else in this folder is a record. The owner reads OWNER-VIEW.md and the two cards, not this page.

**Dates.** The take must happen by Mon 23 Nov 18:29 UTC / 23:59 IST (stop time); latest start about 18:15 UTC / 23:45 IST; the lead's 3-hours-ahead notice must therefore reach the owner before about 15:15 UTC / 20:45 IST on that day. The post is Wed 25 Nov 15:00 UTC / 20:30 IST. Target take Wed 18 Nov is NOT confirmed.

| # | blocker | who decides or does it | state |
|---|---|---|---|
| 1 | Take-time substitution of the `$env` values is not built (BL-wp6-G1); with it missing neither flow set can run | builder via the studio lead | open; nothing in this folder closes it |
| 2 | The five changed flows have never run in n8n; nobody is named to start Docker and run the first rehearsal | studio lead | open |
| 3 | Scope question: does the video need the stand-in scenes 5 to 11 (film-v5) at all? A real-v5-only video (scenes 1 to 4 and the last scene) removes flow-set decisions A to D, the live flow switch and the stand-in mail risk. Proposal from a zoom-out reviewer, not decided | studio lead, with the owner for what the video shows | open |
| 4 | If film-v5 stays: mail credential `mf-mail-smtp` holds the real sender password and a stand-in scene could send a real mail; no written fix | studio lead | open |
| 5 | Take date and start time (v5 gives none) | studio lead | open |
| 6 | Security edits S9-1 to S9-5 and S9-12 are not applied in v5 or the scope sheet, and cannot be as written: seven decisions are needed first (last paragraph of drift/APPLIED-S9.md; QUESTIONS.md item 6). S9-1 is new program work (a closed spend gate and program-side flow switch-on); say whether it is in the take or deferred | studio lead, then core-hardening | open |
| 7 | HubSpot key must be able to delete contacts (drift R8-5); HubSpot check and login-key choice (OWNER-VIEW row 7) have no exact lines | studio lead | open |

**Before the post, not before the take:** drift D-04 and D-05, the exact post words, the person who checks the post. **Not a take blocker:** the failing licence guard test on core-hardening (blocks a pull request; QUESTIONS.md item 7); archive lists (after the take).
