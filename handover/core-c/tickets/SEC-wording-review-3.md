# Security wording v3: final review ROUND 3 (fresh sonnet reviewers)

Status: comprehension reviewer REPORTED (below); style reviewer still running (added when it reports).
Verdict (comprehension): NOT READY as is. Counts, statuses and the table agree (15 PINNED, 11 STATED, 7 WAITING, 19 OPEN, 7 FIXED, 4 FIXED ON BRANCH = 63; 13 UNVERIFIED-only; 7 decisions). Rounds 1 and 2 findings taken or contested with sound reasons, except finding 13.

## Comprehension findings (line numbers of SECURITY-README-v3.md)
BLOCKER
1. l.122 (summary item 22) "The stop switch works through that refusal." promises more than the evidence: 2.3 says the store's refusal while the switch is on has no named test (UNVERIFIED) and no end-to-end stop was tested (NOT RUN; l.98). Fix: "In the gate's tests a refused reservation means no call. That the store refuses while the stop switch is on is UNVERIFIED, and no stop of a live run was tested."
MAJOR
2. l.400 (2.7) "135 test files with no failure" vs l.155 "two failures in 135 files". Fix: "2 failures (see 2.0), neither in these path tests, if they were in it (UNVERIFIED)."
3. l.155 "the other was closed later" says not how; FIXED rows rest on that batch; the FIXED definition (l.22) says passed on the shared branch but 2.0 says the pick branch and the merge was not re-tested. Fix: say what the second failure was; reword FIXED to "passed in a batch before the merge; the merge result was not re-tested".
4. l.19 vs K12 (l.209-213): UNVERIFIED defined as "nothing was run" but K12 carries it while quoting a builder's run (`<SECRET_1><SECRET_2>`, no leak) and K13 carries it while quoting 0.018 s. Fix: a mark such as NOT REPRODUCED / DISPUTED, or widen the definition.
5. l.94, l.98 "tested alone" and five NOT RUN items; 2.9 (l.426-430) adds NOT RUN for the gate's WIP fixes, the merge result and the capped repeat (K10, K11, K15, K16, decision 1). Add them to the summary.
6. l.123 (item 23) "Booked money can still pass the cap (line 18 and part 2.2)": item 18 is about failed calls staying booked; the overshoot gap is K24, database rights K26 (decision 5), neither in the summary; "line" is ambiguous. Say "item".
7. l.121 (item 21) "Not when a tool states 'no map'": "tool" is the agent action in the glossary; K9 says the calling code. Fix wording.
8. Summary choice of the 13: certain measured leaks are left out (K35 24 of 43 bare numbers not masked; K46 `password="my secret phrase"` shows `secret phrase`; K38 glued IP/phone/bank numbers; K39, K40 tails) while UNVERIFIED items are in. Add an "also leak today" line or say why they rank lower.
9. l.444 "before the program connects to the secrets vault or any other outside service": evidence is one test on 3.13 with the version faked (K58, l.394). Hedge it.
10. STATED = "accepted and described" (l.25) with no who/when (K19 "plan decision", K35 "by decision"); K19 is in the owner summary but not in 1a. Add "accepted by the lead on <date>" or make K19 a decision.
11. K17 (l.223-225) is STATED "Who acts: nobody" but carries "Condition for core-b's install: one writer per run map" (no actor, not in 4.5's requests). Make it WAITING/OPEN with an actor or add to a request.
12. Decisions 3 and 5 (l.133, 135): decision 3's default makes the owner send a client note while item 5 says only "tell the lead which defaults you overrule"; no date; decision 5 default is circular ("Tighten them ... The lead decides"); decision 1's default depends on the lead confirming after core-c's batch passes. Add who does what by when.
13. l.198 (K8) PINNED yet "core-b is asked for a start-up check"; "approved list" undefined; the 4.7 log (l.640) claims K8 names no actor (false). Move the core-b ask to its own line; define the term in part 0.
NIT 14 summary items 10, 11 lack "on the main line"; 15 core-b's other open items (K18, K63) not named in "four other open requests"; K63 has no request (l.614); 16 item 14 puts an UNVERIFIED item before certain K19 against "wider exposure first"; 17 undefined terms: K10 "a test replacement was plugged in", K13 "6-second allowance", K38 "merged integration code", K62 "admin console", the currency of "cap 3.00"; 18 l.446 states "starts on 3.12" before its NOT RUN hedge; no way to check one's Python version; 19 item 16 (l.113) states "booked as free" as fact then hedges: hedge first.
Not read: code, tests, evidence files, ORDERS/DECISIONS/request files cited, v2; did not check the 4.2 table cell by cell.
