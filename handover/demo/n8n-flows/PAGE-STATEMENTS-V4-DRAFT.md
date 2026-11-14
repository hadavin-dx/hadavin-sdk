# Page statements, v4 additions (draft, written 16:25Z). Replaces sentence 7 of section C only when lane3 final numbers exist.
Tags: RELAYED = the lead told me a raw run printed this, I have not read the file. READ-ONLY = read from the flows. NOT RUN = no run yet.
V4-1. "On v4 the alert claim window is 720 seconds and a failed alert send backs off 60 seconds times the attempt count (capped at 5)." [READ-ONLY: build_mainframe.py MF_V4=1, folder n8n-flows-v4]
V4-2. "On v3, holding the alert answer for 90 seconds gave two alert e-mails (lane3, one run)." [RELAYED, lane3 n=1, v3 flows 6ebb7f62; raw file name not given to me]
V4-3. "On v4 the same hold (B90) gave N alert e-mails in M runs." [NOT RUN by me; fill N and M ONLY from lane3 final raw files, name the file here: ______ ]
V4-4. "On v4 a duplicate alert is still possible if the mark step fails after a successful send, or if a send outlasts 720 seconds." [READ-ONLY design limit; no test]
V4-5. "How long the Send Email node waits for a silent server is not measured (AF2 not run)." [NOT RUN: my sandbox has no room to start Postgres; the laptop v4 runner may run AF2]
Rule: do not print "fixed" until V4-3 has a named raw file with n and the same pass flag B90 prints.
