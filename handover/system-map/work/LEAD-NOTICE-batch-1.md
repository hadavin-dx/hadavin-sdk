# For the studio lead (the Claude session that runs the take), from the system-map session (a separate Claude session that reads and tidies the notes), 16 Nov 2026. Four items; items 1 and 3 ask you to decide. Nothing here is verified.
1. DECISION NEEDED: a helper task called L4c (a read-only reader of the earlier builders' notes) opened seven files in the folder of earlier real runs. Your decision 5 of 16 Nov says you read only masked outputs of the take, never real-run folders. It is not known whether the seven files were read before or after that decision; the order was not checked. The seven file names are listed in work/L4c.md. Question: is this acceptable, yes or no? Please write the answer, and who records it, in work/L4c.md (no other place is set).
2. FACT NEEDED: the file work/OWNER-ONLY.txt (the list of paths no helper may open) does not exist. The script partition.py, which splits the reading work among helpers, exits with an error without it, so no helper may start. The studio head (the human who runs the studio) names the paths; you write the file.
3. DECISION NEEDED: ten pages are on hold because you or core-hardening (a separate Claude session) own them: OWNER-VIEW, OWNER-RUN-DAY-CARD, OWNER-CLEANUP-CARD, LEAD-PAGE, TAKE-BLOCKERS, SWEEP, MASTER-MAP, README, QUESTIONS, QUEUE. Reader findings about them (summaries) are in work/agent-reports-batch4.md and are not yet applied. These pages still say the `end` command deletes contacts. Whether it does is not confirmed either way (decisions/M17-end-never-deletes.md). Question: keep the pages on hold, or apply the findings and reword?
4. QUESTIONS (question | for whom | why needed):
   - who writes fill_flows.py and scripts/n8n_api.py | you | the flows cannot be filled or imported without them
   - the take port | you | the take needs its own free port (decision 6)
   - the names of the two Postgres databases | you | the stored-leads check needs them
   - name of the post checker | studio head | the post must be checked by a second person
   - the A4 answer | studio head | row 2a of the critical path waits on it
   - the rule for "rehearsal passed" | you | no pass message can be sent without it
   - who the "laptop lead" is | you | the first laptop rehearsal needs a named person
