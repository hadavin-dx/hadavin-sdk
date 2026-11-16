> Headline rule in plain words: write "rehearsal passed with stand-in services" only if the crash test ran, both tries stopped the program right after it sent the mail and before it saved that it sent it, and each try gave exactly 1 mail. If the test did not run or never stopped the program, write "rehearsal not completed". If it gave any other mail count, write "rehearsal did not pass". Stand-in services = a fake mail service and a fake contact list on the laptop; no real Gmail or HubSpot was used. The owner decides this rule: reply "rule OK" or give a new rule. Not verified by any run.

# Message the studio lead sends the owner after the rehearsal (one clean draft; NOT SENT)
Status: DRAFT, written 16 Nov 2026 by the system-map session. No rehearsal has run, so nothing below is checked against a result. Old stacked versions are in rehearsal-passed-limits-history.md (ignore them).

## Words (once each)
- **studio lead**: the Claude session that does the technical steps and messages the owner. **owner**: the human who types the answers and deletes by hand. **studio head**: the human who runs the studio and would set the pass rule; not yet named, and whether this is the owner is NOT SETTLED. Until it is named, the owner decides.
- **take**: the filmed run. **rehearsal**: a practice run on the laptop with a stand-in mail service and a stand-in contact list, no real account.
- **lead id**: the number the program gives each made-up test person. **contact id**: the contact's number in HubSpot.
- **film pause**: the moment the program waits for the owner after 3 contacts exist; the owner types `end` to close it.
- **try**: one crash-test run. **processed once**: one lead sent twice with the same lead id gives one mail, one HubSpot write and one stored row. **IST**: India time, UTC plus 5 h 30 min. **stand-in**: a fake service on the laptop.
- **crash test**: the program is stopped twice, after it sends a mail and before it saves that it sent it. (Studio note, not for the owner: it is row DM of handover/system-map/TAKE-BLOCKERS.md.) "Saves that it sent it" = the program writes a record that the mail went out; if it stops before that, a restart might send again, which is what the test checks.

## Who decides and the pass rule
The studio lead proposes; the studio head decides (unsettled). Working rule until the studio head sets another (NOT confirmed by anyone): the headline says passed only if both crash-test tries stopped the program at that moment and each gave exactly 1 mail.

## The message
Headline (send one): "rehearsal passed with stand-in services" if the working rule above holds; otherwise "rehearsal did not pass with stand-in services" plus the crash-test sentence chosen from the list under limit 2. Never write (nothing in the files shows these are true) "no egress", "crash-safe" or "nothing can spend before both typed answers". Then the four limits, in this order:
1. About `end`: "The rehearsal did not test `end` on a real HubSpot. By the written design (inputs/OWNER-STEPS-realrun-v5-core-hardening.md, the owner's step list), `end` only closes the pause and prints the made-up contacts left in HubSpot (lead id and contact id). It deletes nothing. You delete the leftover made-up contacts by hand after the take."
2. About "processed once" (choose by the crash-test result):
   - (a) both tries stopped the program at that moment and each gave exactly 1 mail: "We stopped the program twice, right after it sent the mail and before it saved that it had sent it. Each time only one mail went out. We did not test other crash moments or real Gmail or HubSpot, so we do not claim it can never send twice."
   - (b) any result other than exactly 1 mail for one lead: "The crash test gave a result other than exactly 1 mail for one lead. We do not claim it is crash-safe."
   - (c) not run: "The crash test did not run. The claim 'a lead sent twice with the same id is processed once' is not shown."
   - (d) ran, but neither try stopped the program at that moment: "The crash test ran, but neither try stopped the program at that moment. It shows nothing."
3. About the start deadline: "The take is the filmed run. The program may refuse to start after a set time. We did not read its start check. Start before Mon 23 Nov 18:14:40 UTC / 23:44:40 IST." (Source: ORDERS.md and inputs/DECISIONS-2026-11-16.md; the program's start check was not read.)
4. About real accounts: "No real-account check was done before the take. The take preparation sends one made-up lead, to the stand-in services only."

## Open items (all UNVERIFIED or NOT SET)
- Pass rule: NOT SET. Owner and date for it: NOT SET.
- These limits are not yet rows in PLAN-002.md section 7 (test rows) or section 9 (limits). Owner and date: NOT SET.
- Next step: when the rehearsal result file exists, the studio lead adds limits 1 to 4 to the INDEX (the table of open items; path unknown, find it first).
