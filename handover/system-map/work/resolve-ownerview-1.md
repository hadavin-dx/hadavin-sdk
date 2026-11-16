Status: PARTLY RESOLVED. Findings were accepted headless; some fixes are applied, others are marked 'Still to add' below. Round 2 is pending. In this page: OS = OWNER-STEPS numbered steps, D-04/S-01 = items in drift/REPORT.md, take = the one filmed run, lead = the Claude session giving orders.

# Goldfish Annotated Review Report, OWNER-VIEW.md round 1

**Target:** `handover/system-map/OWNER-VIEW.md` (full file). Findings: work/review-ownerview-r1.md (egm-codebase-details, egm-comprehension). Merged duplicates: stale FINAL-CROSSCHECK cites (fact M1 + comprehension M5, one fix); post content (fact M3 + comprehension M6); missing steps (fact M2 + comprehension M7); word meanings (comprehension M1, M2, M3, M4 and fact Nit "take").

## Blocker
### 1. [comprehension B1] No go/no-go; today's deadline and the person for the laptop n8n run not stated. PROPOSE FIX
Add a verdict line under the summary: "Wed 18 Nov is NOT yet shown to be reachable: nobody has run the changed flows in n8n, and the files name nobody and no time for that run." Spell out today's deadline: steps 1-7 due Mon 16 Nov 18:29 UTC / 23:59 IST (OS:27; OS says they take 60-90 minutes); step 9 sentences and the decisions due Mon 16 (OS:144). Put the Docker and laptop-run question to the laptop lead in section 3 with "who and by when" as the open item. Replace every "same" in the by-when column with the date.

## Majors (all PROPOSE FIX)
2. Stale cites to FINAL-CROSSCHECK: cite by section name, never by line. Already applied except one remaining cite (line 29); finish.
3. Post content (step 23): quote OS:131 permitted and forbidden sentences; say the decision in force allows only the duplicate claim; drift D-04 lists the conflict. Applied; check the wording once more.
4. Missing steps: add steps 20, 21 reply, 22 retire check and secret-file deletion, rule OS:25 (applied). Still to add: the "never send a password, address or key to the lead" rule, the "STOP and tell the lead" rule, the lead sends the numbers message in step 16, the take id is chosen new for each take, row 17 "number, a space, the id", the read-only HubSpot token goes into a WSL file, save screenshots under the lead's names, set sleep and lid settings back.
5. Words: rename "lead" for a sales request to "sales request" (keep "the lead" only for the Claude session? choose one: write "the engineering session (the lead)" once, then "the lead"; and "sales request" for what arrives through the form); define "take id", "take" once (one recorded run; up to two possible), "session", "window" (time window = "cap and window end" explained as "the date and time after which the take may not run"), "app password" versus the form-address access check (call the second "access check on the form address"), "audit" only for the three audits, "form address" = the web address where the form sends a sales request (the webhook); explain Blocker/Major/Nit, CRM, HubSpot, Postgres, flows, egress, cap, and write "OS" as "the owner-steps file".
6. Line 29 DISAGREES paragraph: the drift report now exists; replace with the six Blockers sentence (applied) and name who acts: the laptop lead decides D-01 to D-05 and S-01 before the take. Docker: "OS has no step to start Docker; the lead starts the database; nobody is named for starting Docker: open question to the laptop lead".
7. Decisions need deadlines and plain words: add "due Mon 16 Nov" where OS:144 says so; decision 4 explain token count, zero price, fake model; decision 2 "2 safe now" only after an archive place outside the repository is named; decision 5 keep OS:137 "accept despite the 16-hour rule failing".
8. Table order: move row 19 (fresh Chrome profile) before row 17; add "be reachable while the lead runs the smoke test (OS:87)".

## Nits (PROPOSE FIX, cheap)
"Stuck" heading to "Blocked"; row 2 define RECEIVER (the account that receives the form mails) and SENDER (the account that sends); row 16 "worst case per call" explained; remove repeated US$0; line 34 name the fault ("anyone who knows the address can send a sales request"); line 39 plain words for "order to fix saving and Postgres"; "headed 13, listing 14" explain or drop.

## Counts: accepted 1 Blocker + 7 Majors + all Nits; contested 0; escalated 0; declined 0.
Round 2 needed: yes for Blocker 1 and Majors 4, 5, 6 (one reviewer, comprehension, after the rewrite). Round cap: 2.
