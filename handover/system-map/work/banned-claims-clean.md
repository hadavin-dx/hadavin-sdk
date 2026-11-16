# Banned claims: ONE CLEAN PAGE (written 16 Nov 2026)
This page is the only live version. Older notes (work/banned-claims.md and work/banned-claims-clean-history.md) are history only. Cite section names, not line numbers.
Made-up data only. Status: PROPOSAL from the system-map session (a Claude session); nothing here is approved. All dates are the system-map session's proposals.

## Files and words used on this page
- inputs/DECISIONS-2026-11-16.md = the lead session's twelve decisions (known second-hand only: UNVERIFIED). decisions/M17-end-never-deletes.md = the page that checks what the end step does. work/banned-claims.md = old stacked notes (history only).
- Decisions 2, 3 and 8 from that list are second-hand and unverified until the studio lead confirms them. One sentence each: 2 = the take never deletes anything; 3 = the plan to give each part its own login (the roles proposal) is parked, so no such login is built; 8 = no smoke test with a real account before the take (exact wording NOT RECORDED; no banned claim below depends on it).
- take = the one recorded run of the demo (the film is cut from it). 'processed once' = stored once and mailed once, not twice. contact record = one made-up sales contact (older pages say "lead"); id = that record's id. n8n = the workflow tool that runs the demo. crash test = stopping n8n in the middle of a run.
- count check = meaning not recorded. spend check = meaning not recorded. count login = a separate read-only database login for the count (not built).
- the program = the demo's Python runner script that drives n8n. end step = the program's last command, typed as `end`.
- two doors = the two ways a contact can enter the demo. The first is the normal entry. The second is the web address n8n listens on; inputs/OWNER-STEPS-realrun-v5-core-hardening.md calls it the "hook door" and says the program does not check it. How the two entries relate is not tested, so any claim about them stays banned.
- rehearsal = a test run on the laptop before the take, without a real account.

## Roles (one word, one person)
- **Owner (poster)** = the person who posts the video. **Studio head** = the person who runs the studio. **Claude session** = engineering software (called "studio lead" on older pages); it never approves anything here.
- **Approver** = the studio head. Only the studio head approves.
- **Checker** = a human role: a person who is not the author and not the approver; compares the post with this page. NOT NAMED yet. Nobody posts until the studio head writes the checker's name here.

## Allowed today (one sentence)
1. "A lead sent twice with the same id during one recorded run is processed once."

## Not allowed yet (becomes allowed only after a confirmation)
2. "After the film, the owner deletes the leftover made-up contacts by hand." Condition: the program's end step deletes nothing and only lists the leftover contacts. File to check: decisions/M17-end-never-deletes.md (UNVERIFIED today). Confirmer: the studio head, in writing; nobody else confirms. Until then exactly one sentence is allowed (sentence 1).

## Banned (do not say or show)
Do not say or show any of these. One claim per line; each "Why" gives the reason it is banned, and the Unlock rule below says what would lift a ban.
- A spending cap or limit. Why: not built.
- That the count check or the spend check is separate or independent. Why: not tested.
- That one person through two doors is one contact record. Why: not tested.
- That no contact data stays in n8n. Why: not checked.
- Any recovery time or alert time. Why: no test measured one.
- Anything about a portal, an approval step or an audit trail. Why: not part of this video.
- That n8n cannot reach the internet. Why: not checked.
- That the system is crash-safe. Why: not tested. Until a checker is named, this claim stays banned. After that it is unlocked only by a named result file showing the crash test passed (the crash test stops n8n in the middle of a run and checks that the contact record is still processed once), read by the checker.
- That the count uses an independent or read-only login. Why: that login is not built (decision 3 parks the plan).
- That the program deletes anything (the owner's own hand deletion in sentence 2 above is a different claim). Why: the take never deletes (decision 2). This one is never unlocked.

## Unlock rule
The studio head names a result file (a text file saying whether one named test passed or failed) and the checker reads it. No such file exists today, so no banned claim is unlocked today (the one allowed sentence, sentence 1, needs no unlocking). A claim that the program deletes anything can never be unlocked.

## Open items
Checker's name; date to name it (proposal: Tue 17 Nov 2026 12:00 UTC / 17:30 IST); the final video script wording, written after the rehearsal.

