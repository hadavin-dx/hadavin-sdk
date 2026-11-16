# Limit sentences for the studio lead's "rehearsal passed" message (draft, saved 2026-11-16 11:57 UTC / 17:27 IST by the system-map session)
Status: DRAFT. Not checked against any rehearsal result file, because no rehearsal has run (decision 12: the studio lead runs the first laptop rehearsal, target "tonight or tomorrow morning IST"). Scope is real-v5 scenes 1 to 4 only (decision 1). Recipient: the owner (the person who types the answers). Words, one per line:
- Take = the recorded video run.
- Rehearsal = a practice run on the laptop with fake mail and a fake contact list instead of real Gmail and HubSpot.
- Lead id = the number the program gives each made-up test person (the program prints it as 'lead key', decision 2).
- Closed gate = a lock that stops all spending before the owner types both answers (not built).
- Loopback re-smoke = a short check the studio lead runs on its own machine before the rehearsal (decision 12).
- Row DM = the crash test in handover/system-map/TAKE-BLOCKERS.md, run twice.
- Studio lead = the Claude session that does the technical steps; owner = the person who types the answers and deletes by hand; rehearsal = a test run on the laptop with stand-in mail and a stand-in contact list, no real account (decision 8); `end` = the word the owner types to close the film pause.
Rule for the studio lead: write "rehearsal passed with stand-in services"; never write "no egress", "crash-safe", or "nothing can spend before both typed answers" (decision 5: no closed gate is built; S9-1 and S9-4 are deferred). Put each limit below in the same message as the pass.
1. About `end`: "The rehearsal did not test `end` on a real HubSpot. By the written design (decision 2), `end` only closes the pause and prints the made-up contacts left in HubSpot (lead id and contact id). It deletes nothing. The owner deletes the leftover made-up contacts by hand after the take."
2. About "processed once". Write the sentence that matches the result of row DM (the crash test: the program is stopped after it sends the mail and before it saves that it sent it):
   - DM: each of the 2 forced crashes produced exactly 1 mail: "We stopped the program twice, right after it sent the mail and before it saved that it had sent it. Each time only one mail went out. We did not test other crash moments or real Gmail or HubSpot, so we do not claim it can never send twice."
   - DM: a forced crash produced 2 or more mails for one lead: "We saw two mails for one lead when the program crashed after sending and before saving. We do not claim it is crash-safe."
   - DM was not run, or neither of its 2 tries stopped the program at that moment: "The crash test did not run. The claim 'a lead sent twice with the same id is processed once' is not shown."
3. About the start deadline: "The rehearsal did not test the late-start refusal. The latest start the studio lead's orders give is Mon 23 Nov 18:14:40 UTC / 23:44:40 IST; UNVERIFIED, I have not read the program's start check, so do not rely on it. The owner should start well before it."
4. About the count (decision 9): "The count of contacts in the film is a screenshot from the rehearsal or the Postgres node preview. It is not a separate count made with its own login."
5. About real accounts (decision 8): "No real-account check was done before the take (it replaces the earlier plan of a separate real-account smoke test, TAKE-BLOCKERS rows a to f). The take prep sends one made-up lead."
Owner of this draft: system-map session. Next step: the studio lead adds items 1 to 5 to the INDEX when the rehearsal result file exists. Gap: these limits are not yet rows in the plan's test-row list (PLAN-002.md section 7) or its limits bullets (section 9).
