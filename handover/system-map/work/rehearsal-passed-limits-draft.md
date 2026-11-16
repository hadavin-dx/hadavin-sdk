# Message the studio lead sends the owner after the rehearsal (one clean draft; NOT SENT)
Status: DRAFT, written 16 Nov 2026 by the system-map session. No rehearsal has run, so nothing below is checked against a result. Old stacked versions are in rehearsal-passed-limits-history.md (ignore them).

## Words (once each)
- **studio lead**: the Claude session that does the technical steps and messages the owner. **owner**: the human who types the answers and deletes by hand. **studio head**: the human who runs the studio; whether this is the owner is NOT SETTLED.
- **take**: the filmed run. **rehearsal**: a practice run on the laptop with a stand-in mail service and a stand-in contact list, no real account.
- **lead id**: the number the program gives each made-up test person. **contact id**: the contact's number in HubSpot.
- **film pause**: the moment the program waits for the owner after 3 contacts exist; the owner types `end` to close it.
- **crash test**: the program is stopped twice, after it sends a mail and before it saves that it sent it. It is row DM of handover/system-map/TAKE-BLOCKERS.md (that row name stays out of the owner's message).

## Who decides and the pass rule
The studio lead proposes; the studio head decides (unsettled). The pass rule is NOT SET. Proposal, not confirmed: passed only if both crash-test tries stopped the program at that moment and each gave exactly 1 mail.

## The message
Headline: "rehearsal passed with stand-in services" only if the pass rule is met; otherwise "rehearsal did not pass with stand-in services" plus the matching crash-test sentence below. Never write "no egress", "crash-safe" or "nothing can spend before both typed answers". Then the four limits, in this order:
1. About `end`: "The rehearsal did not test `end` on a real HubSpot. By the written design, `end` only closes the pause and prints the made-up contacts left in HubSpot (lead id and contact id). It deletes nothing. You delete the leftover made-up contacts by hand after the take."
2. About "processed once" (choose by the crash-test result):
   - (a) both tries stopped the program at that moment and each gave exactly 1 mail: "We stopped the program twice, right after it sent the mail and before it saved that it had sent it. Each time only one mail went out. We did not test other crash moments or real Gmail or HubSpot, so we do not claim it can never send twice."
   - (b) any result other than exactly 1 mail for one lead: "The crash test gave a result other than exactly 1 mail for one lead. We do not claim it is crash-safe."
   - (c) not run: "The crash test did not run. The claim 'a lead sent twice with the same id is processed once' is not shown."
   - (d) ran, but neither try stopped the program at that moment: "The crash test ran, but neither try stopped the program at that moment. It shows nothing."
3. About the start deadline: "The program may refuse a late start. We have not checked. Start before Mon 23 Nov 18:14:40 UTC / 23:44:40 IST." (Source: ORDERS and the decision list; the program's start check was not read.)
4. About real accounts: "No real-account check was done before the take. The take preparation sends one made-up lead."

## Open items (all UNVERIFIED or NOT SET)
- Pass rule: NOT SET. Owner and date for it: NOT SET.
- These limits are not yet rows in PLAN-002.md section 7 (test rows) or section 9 (limits). Owner and date: NOT SET.
- Next step: when the rehearsal result file exists, the studio lead adds limits 1 to 4 to the INDEX (the table of open items).
