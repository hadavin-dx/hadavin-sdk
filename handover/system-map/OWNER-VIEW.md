# Owner view: where we stand for the filmed take on Wed 18 Nov 2026
Written Mon 16 Nov 2026, about 09:15 UTC / 14:45 IST, by the system-map session from the other sessions' files. Made-up data only. A number or claim taken from another file shows its source as file:line. "OS" = handover/system-map/inputs/OWNER-STEPS-realrun-v3.md.

Words (each used in one meaning only): **the take** = the one real recorded run of the lead desk demo (n8n takes leads in, writes a CRM contact, sends a mail). **n8n** = the tool that moves each lead from step to step. **the lead** = the Claude session that runs this with you. **an audit** = a read-through of the files that lists faults; there are three (core-hardening, flows-audit, system-map). **re-smoke** = a short trial run of the whole chain with no paid model call (cost US$0), before any real take.

## 1. One-minute summary
**Finished (reading only, nothing run):** the three audits are written. Flows-audit: 45 faults found, 8 Blocker, 8 Major, 29 Nit; 17 should be fixed before the video, 28 after (flows-audit REPORT.md:5). Core-hardening's cross-review of flows-audit found all five flows-audit patches apply (core-hardening REPORT.md:3). Our own check of the five flow patches: all apply and none breaks the flow graph (flowcheck/REPORT.md:14).
**Running now (09:02 UTC / 14:32 IST board):** this session is at 40 percent: a fact check of the cross-check document, a check that the take documents agree with each other, and this page (STATUS-BOARD.md:7,17-22). Core-hardening is at 33 percent, checking the paste commands of the re-smoke plan (its board, lines 8, 17-20). Flows-audit is at 35 percent, building a tool that fills the flows (its board, lines 8, 17-22).
**Stuck:** nothing is blocked on you today except the account steps in section 2. One gap is real: **no one has run the changed flows in n8n.** The cloud session has no running Docker (the program that starts throw-away containers), so every n8n behaviour is untested (STATUS-BOARD.md:17, flowcheck/REPORT.md:9). A laptop run is the only fix.

## 2. What you must do for the take (steps only from OS; click paths on your accounts were never checked, OS:7)
Who: you, unless it says "lead". "Worked" = what you should see.
| # | what | by when | how you know it worked | source |
|---|---|---|---|---|
| 1 | Revoke the old practice-mailbox app password (a 16-letter password that opens a whole mailbox) | Mon 16 Nov 18:29 UTC / 23:59 IST | list of app passwords is empty or has no old demo name | OS:27-32 |
| 2 | Create two throwaway Gmail accounts, a RECEIVER and a SENDER, 2-step sign-in on, not the recovery address of anything else | same | tell the lead the one sentence; send no address | OS:34-38 |
| 3 | In SENDER: add the company address under "Send mail as" and verify it | same | company address listed as verified | OS:40-44 |
| 4 | In RECEIVER: filter on subject `[demo] lead`, skip inbox, label `demo` | same | label `demo` and the Inbox both empty | OS:46-54 |
| 5 | Make one app password per account; type the receiver one into a file in WSL (the Linux window inside Windows) | same | `ls -l` shows `-rw-------` | OS:56-61 |
| 6-7 | HubSpot test account: add property `hadavin_label`; make two private apps (one read-only, one read and write) | same | property and two apps visible | OS:63-72 |
| 8 | Type three secrets into n8n yourself when the lead says n8n is running | when the lead says so | you can tell the lead "three credentials created" | OS:74-80 |
| 9 | Send the lead only the short sentences listed, never a secret | after step 8 | lead confirms receipt | OS:82-83 |
| 16 | Written yes with numbers, once per paid take: at most 3 model calls, worst case per call, 3 times that, money spent so far, cap and window end (check the last two on the lead's screen) | before each take; no numbers means answer no | the lead holds your one-line yes | OS:91-92 |
| 17 | In your own WSL window answer `y`, then the 6-digit number plus the take id; no tool or helper may type for you | during the take | the take prints its result; wrong line sends nothing | OS:94-100 |
| 18 | Type `end` yourself when the lead has filmed the contact list | during the take | the script archives the take's contacts | OS:102-104 |
| 19 | Fresh Chrome profile `demo-take`; no real address on screen | before recording; scan every frame afterwards | frame scan finds only `take-<id>-a/b/c@example.com` | OS:106-109 |
| 21-22 | Watch the cut; revoke both app passwords; delete both HubSpot apps; the lead deletes the take's saved runs | by Mon 23 Nov 18:29 UTC / 23:59 IST | screenshots of empty lists | OS:116-128 |
| 23 | You post (Claude never posts) on Wed 25 Nov 15:00 UTC / 20:30 IST | that day | post says only "a lead sent twice with the same id is processed once" | OS:130-131 |
**DISAGREES: see drift/REPORT.md when it exists** (not yet written, board M3 at 10 percent, STATUS-BOARD.md:19) on two points. (a) The date: OS never names Wed 18 Nov. Its set-up deadline is Mon 16 Nov 18:29 UTC (OS:27) and its window ends Mon 23 Nov (OS:92); the take date comes only from FINAL-CROSSCHECK.md:3 and the queue. (b) Docker: OS contains no step for you to start Docker and the word does not appear in it; the lead starts the database (OS:5). The instruction "Docker running" is therefore NOT in the steps. I do not guess who starts it or when.
The step numbers jump from 9 to 16 on purpose (OS:138).

## 3. Decisions only you can make
Source: FINAL-CROSSCHECK.md:94 and :42-52, OS:133-137, flows-audit QUESTIONS.md. The flows-audit questions Q4 to Q9 are already answered by the lead (QUESTIONS.md:17-22), so they are not asked again.
1. **Does the form address get a password before Wed 18 Nov?** Today anyone who knows the address can send a lead (flowcheck/REPORT.md:7). Yes: closes the hole, needs a change and a laptop test, which uses time before the filming. No: faster, fine only on your own closed laptop network, and the video must not claim the intake is secure.
2. **Where do the old files go (archive), and do you say yes to each move?** Nothing is deleted. 39 rows: 2 safe now, 28 not yet, 9 no (FINAL-CROSSCHECK.md:65). Put the archive outside the repository, because a repository test fails on banned words in any file inside it (:51, :65). Your yes is needed before any move.
3. **Keep or archive `extract.py`?** Keep: two tests use it, nothing is lost (:83). Archive: less code, but the tests must change.
4. **Which numbers go into the core-hardening patch C-01?** The largest token count is 200,000 in one audit and 1,000,000 in another; zero price only for the fake model, or also for a local model (:49). A low number may refuse a real long call; a high number weakens the cap.
5. **Narrow claim, throwaway mailboxes, and the build-time estimate.** Defaults: say only "same lead id sent twice is processed once"; use throwaway mailboxes, not your company mailbox; accept the 20-hour build estimate (OS:135-137). Say yes or no to each.
6. **Taken by the lead, listed for you:** which order to fix saving and Postgres, and the setting that lets flow steps read environment values (:42-43, :94).

## 4. What is NOT verified
1. **The changed flows were never run in n8n.** Docker had no running service in the cloud session, so n8n could not start (flowcheck/REPORT.md:9, :22). That the key check, the 422 and 503 replies, and "stored nothing on a repeat" work is untested.
2. Nothing in the three audits was run against Gmail, HubSpot, mail sending or a model call (flows-audit REPORT.md:4; core-hardening REPORT.md:2).
3. The click paths in OS and a list of further points (OS:178-193, headed 13, listing 14) are marked UNVERIFIED by their author (OS:7); no live take, Gmail filter or real label behaviour has run (OS:161-166).
4. Test counts in OS:151-159 come from an older head (4d7c335) and are not the take's current state; the current head is named in the re-smoke plan (OS:151).
5. Network egress (outside connections) from n8n is switched off by setting names; it is observed, not enforced (QUEUE.md:8). The re-smoke costs US$0 and runs before any real take; the take branches stay on the laptop (QUEUE.md:8).
6. The core-hardening patches were checked with a copy of the guard scan, not the real test (pytest not installed there) (core-hardening REPORT.md:2). Three files still fail the vendor-word test (:8).
