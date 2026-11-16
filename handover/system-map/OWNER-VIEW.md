# Owner view: what is still yours for the take
Written Mon 16 Nov 2026 about 10:05 UTC / 15:35 IST; updated by the system-map session, round 3 (fixes from the fresh read). Everything in the demo is made-up data. Cards: OWNER-RUN-DAY-CARD.md and OWNER-CLEANUP-CARD.md. Accounts, keys, Docker, audits and decisions for the lead are in LEAD-PAGE.md in this folder, not here. The lead's written answers to the open questions are in work/LEAD-ANSWERS.md.

**What this page is for.** It lists what is still yours before, during and after the recorded run of the lead-intake demo (the "take"), in order. Read it first; then use the two cards for the typing.

**Verdict: Wed 18 Nov is NOT yet confirmed.** The changed flows have not been run in n8n yet, and the rehearsal has not been run. The lead sends the exact date and start time in UTC and IST (the lead page asks for at least 3 hours ahead). Until then do nothing except read this page; laptop settings (row 2 of the table below) are done only after that message arrives.

## Words, one meaning each
- **Take** = one recorded run of the lead-intake demo (the steps file says "run"; same meaning). The take sends 3 made-up test people through a web form. Expected result: 3 contacts in HubSpot and mails in the Gmail label `demo`. This has not been run yet.
- **Lead** = the Claude engineering session that does the technical steps. It cannot see your screen and talks to you in the chat of this project. (Not to be confused with a "lead" in the demo, which is a made-up sales contact.)
- **Run name** = a short name you pick fresh for each run, before you write your yes (the yes contains it). The lead confirms the name is unused. The program's own screens call it "take id".
- **Linux window** = the Ubuntu terminal on your Windows laptop (WSL).
- **Stop time** = the last minute the program allows: Mon 23 Nov 18:29 UTC / 23:59 IST.
- **Rehearsal** = a test run with stand-in programs and no real account. It is not a take, and you do nothing for it.
- **Loopback re-smoke** = a short test the lead runs on the lead's own side: one made-up contact is sent through, then `end`. It is how the "archives contacts" step below gets checked.
- **T19** = the name of the test for "a lead sent twice with the same id is processed once". It has not been run.
- **real-v5** = the version-5 steps file of the real-account run (inputs/OWNER-STEPS-realrun-v5-core-hardening.md); its steps are lettered A to J.
- **Typed answers** = your answers to the two questions the program asks at the start (see "The yes" and message order step 5). They are what the program waits for; they are not a control that stops spending, and this page does NOT claim they lock any paid call (decision of 16 Nov).
- **Film pause** = the moment the program waits for you after the 3 contacts exist, so they can be filmed.
- **Retire check** = a command that proves the old passwords no longer work.
- **Ledger** = the list of paid calls to the AI service that the program prints. Nothing proves the list is complete, so do not treat it as proof of the total.
- **Spending backstop** = a dollar figure written in the settings file `stage.env` that nothing enforces. A person checks it. The program does NOT enforce a dollar limit, so the numbers you approve are the only control.

## Dates
- **Take:** target Wed 18 Nov. If that fails, the latest possible day is Mon 23 Nov (no later day exists). The take can only follow a passed rehearsal; the rehearsal has not run, so no confirmed date exists yet.
- **Start no later than 17:30 UTC / 23:00 IST** on the take day, so the 10-minute film pause still ends before the stop time of 18:29 UTC / 23:59 IST. (The program itself accepts a start up to 17:40 UTC / 23:10 IST, because it counts no pause; its own run needs 49 minutes.) Starting by 12:00 UTC / 17:30 IST is only a planning target, so that a failed run still has the afternoon; it is not a promise of a second run.
- **Notice:** the lead's message with the start time must arrive at least 3 hours before that start time (for a 17:30 UTC start: before 14:30 UTC / 20:00 IST). This applies every day.
- **Post:** Wed 25 Nov 15:00 UTC / 20:30 IST. The post date does not move if the take slips, but a take after Mon 23 Nov is impossible.

## Rehearsal
A rehearsal has not been run. No separate real-account smoke happens before the take: the lead runs a short technical self-check on the lead's own side and sends one made-up lead through, then the laptop rehearsal.

## What the video may claim
This video is real-v5 only (scenes 1 to 4). The only claim it may make is "a lead sent twice with the same id is processed once" (inside one take folder). It is NOT proven yet: the changed flows and the T19 test have not been run.

## The yes (one definition)
Your written yes holds three things: the call count (at most 3 model calls, a model call being one paid call to the AI service), the US dollar total (3 times the worst-case price of one call), and the stop time. Two more figures, the money spent so far and the spending backstop, are in the lead's message and are NOT in your yes; the program does not print them. Before you send your yes, open `stage.env` yourself and compare these two figures with the lead's message. If any figure differs from the message or from your yes, type nothing and tell the lead. The yes is given once per paid run, only after the lead says the rehearsal passed and names its result file. If a number is missing, answer no.

## The order of messages, once, for the whole take
1. The lead sends the date and start time (at least 3 hours ahead).
2. The lead writes "rehearsal passed", names the result file and sends the figures message: the numbers, the `stage.env` path, the `cd` line and the start line.
3. You send your written yes (see "The yes"). Example: "Yes, run <run name>, 3 model calls planned and a worst-case total of US$<total> (3 times the worst-case price of one call; the program does not enforce this), stop time Mon 23 Nov 2026 18:29 UTC / 23:59 IST."
4. The lead writes "start now".
5. Only after "start now": you read the start notice and compare it with your yes. Only if it matches, type `y`. Then type the 6-digit number (the start notice shows it) and the run name. Then follow the run-day card's other steps up to the pause.
5b. The lead writes "program paused".
5c. You film. Then you send the two words "film done" in the chat to the lead, not into the Linux window (even if the program's screen asks for `end`, type nothing until message 6).
6. The lead answers with a NEW message that begins exactly "film done, type end". Do not type `end` on your own "film done" message.
7. You type `end`.
7b. After you type end, the program archives this take's three made-up contacts in HubSpot (archived is not the same as erased: HubSpot keeps them for a time); any it could not archive are listed, and you archive or delete them by hand from the list it prints. [UNVERIFIED until the lead's loopback re-smoke test run, planned for Tue 17 or Wed 18 Nov before the take; the clean-up list prints search text take-<tag>-a, -b, -c with the example.com domain; where <tag> first shows on screen is not verified (the lead has asked core-hardening). Until then, if the list on your screen differs from this description, stop and tell the lead.]
7c. You tell the lead how many contacts the program could not archive, and their HubSpot ids only (addresses replaced by X).
7d. The lead names the three test addresses and writes "demo mails may be deleted". You delete the demo mails by hand, then reply "contacts done" and how many contacts you archived or deleted by hand.
8. Later the lead writes "last run done", then each clean-up step as the clean-up card says.

**Extra safety words.** The lead agreed extra safety rules. In messages 2, 4, 5b, 6, 7d and 8 above, do not act until the lead writes the exact words quoted in that step. Follow them even if an older steps file says otherwise.

## What is still yours (in order of the take; steps file letters in brackets)
Two cards hold the typing and the deletes, one action per line: **OWNER-RUN-DAY-CARD.md** (steps C to H) and **OWNER-CLEANUP-CARD.md** (step I). This page is the plan.
| # | what | by when | how you know it worked |
|---|---|---|---|
| 1 | Written yes with numbers [A], once per paid run: see "The yes" and message order step 3. Do not give it until the lead says the rehearsal passed and names its result file. The lead's message lists: at most 3 model calls, the worst-case price of one call in US dollars, 3 times that, the money spent so far, the spending backstop, the stop time, and the path of `stage.env`. The start notice prints what will happen (run-day card steps 11 and 12). | before each run | the lead says it holds your yes |
| 2 | Laptop settings [B]: first write down the current sleep and lid-close values (keep the note; clean-up card step 7 needs it); then, for the whole take: plugged in to mains power, sleep Never, lid action Do nothing (Control Panel, Power Options); close programs that show addresses or alerts. | before the run | tell the lead only if a screen differs from the steps file |
| 3 | Run day [C to H]: follow OWNER-RUN-DAY-CARD.md. The one dangerous moment is the film pause. Typing `end` closes the pause; what happens next is message 7b above (one place, not repeated here). Your demo mails are deleted by hand only after the lead writes "demo mails may be deleted"; that phrase does not cover contacts. The 10-minute limit for the film pause is your own clock alarm: the program has no timer, waits for the typed word end (2 tries; end of input also ends it) and never types end itself. Type `end` only after a NEW message from the lead that begins exactly "film done, type end" (card step 21). | the run | the card's "you should see" lines |
| 4 | Watch the edited video twice [H] (card step 27). | after the cut; deadline from the lead | the lead holds your reply |
| 5 | Clean-up [I]: follow OWNER-CLEANUP-CARD.md, one step at a time as the lead releases it. | deadline from the lead | screenshots of the lists that show none of this run's entries; the check printed "refused as expected" for both logins |
| 6 | Post the video yourself [J] (Claude never posts for you). The post may say only this one sentence: "A lead sent twice with the same id is processed once." (a second send with the same lead id, inside one take folder). Do not say anything else about how the system works. In particular do NOT say: a spending cap, that the count or spend check is separate or independent, that one person through two doors is one contact, that no contact data stays in n8n, any recovery or alert time, anything about a portal, approval or audit trail, that n8n cannot reach the internet, that it is crash-safe (unless the rehearsal's crash test passed and the lead says so), or that the count is made with an independent or read-only login (that login is not built: parked, decision 3 of 16 Nov). The exact final words come from the lead after the rehearsal; until you have them, do not post. The lead reads the final post against the studio's written rules and the evidence, and sends you the result; you approve and post it yourself (there is no second person). Send the post text to the lead first. | Wed 25 Nov 15:00 UTC / 20:30 IST | the check is done and you posted |
| 7 | OPEN, owned by the lead. Two items: (a) a HubSpot check: one line you run in HubSpot and paste the result back; [lead fills: the exact line, and by when]. (b) the choice of which login key to replace before a public file with your name is rewritten; the lead's pattern scan of the seven files found no key-shaped text (counts only, not a read; see work/LEAD-ANSWERS.md item 8), so [lead fills: whether item (b) is closed or still needed]. No action for you now. If either is still open when the rehearsal has passed, the lead cannot start the take; the lead chases it. | the lead sends the exact lines | you reply with what was asked |

**Source.** Rows 1 to 6: inputs/OWNER-STEPS-realrun-v5-core-hardening.md, steps A to J. Row 7 is named only in the lead's order number 017 (an internal list of the lead's orders); its exact lines are in no file this session holds. **Not shown to work:** none of these steps has run against real accounts and the changed flows have not run in n8n. Row 7 can also block the start.

**Security items decided on 16 Nov:** the four security rules of the steps file (lettered A, E, F and I there) cannot be changed by a chat message during the take (a working rule, not enforced by a lock) [lead fills: one-line meaning of each of A, E, F, I]; the lead reads only masked take outputs, never your secrets; you revoke the model key yourself at clean-up. A closed lock before your typed answers is NOT built.

**Not from the steps file (they come from this session's wording or the lead's orders):** the 3-hours-ahead notice, the target Wed 18 Nov, the earliest-take and post-date remarks, and the words ledger and web form are this session's wording or the lead's orders, not v5's.
