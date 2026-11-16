WHO DOES WHAT: (1) The laptop lead runs these steps; the first rehearsal is the laptop lead's too (decision 12). (2) The system-map session wrote the steps and keeps this file current; it runs nothing. (3) Nothing here has been run; every duration is "estimate, unverified" unless a file:line is given.
Terms for this page: see work/t19-terms.md. Earlier version of this page: work/t19-and-stored-data-steps-history-1.md (not current; do not run it). Decisions used: inputs/DECISIONS-2026-11-16.md, items 1-2, 5-12 (cited as "dec N"). The plan is inputs/plan-wp6-resmoke-v5.md.

# T19 and stored-data steps: CURRENT (16 Nov 2026, edited after the 15:45Z lead order)
Words: T19 = send the same made-up lead twice (same lead id) and expect exactly 1 mail, 1 HubSpot write and 1 stored row. take = the one filmed run on made-up data; it is the real-v5 flows only, scenes 1-4 (dec 1). Rehearsal = a practice run of the same steps before the take. mf_leads = the table of stored leads (meaning from L1c line 237; name for the take's database NOT SET). Studio lead = the Claude session; laptop lead = the Claude session on the owner's laptop that runs the steps; owner = the studio head. Not defined, ignore: KeyOk, Claim, recovery, F-002, T1-8, F8 shorthand beyond what is written here.

## Fixed by decisions (nothing here is open)
- Ports (dec 6): rehearsal uses port 5690. The take uses its OWN free port, not 5678 or 5679 (those are the owner's own n8n). The port number for the take is NOT SET; the plan names it in one place, and the laptop lead picks a free one and writes it there before the take.
- Storage (dec 10): one Postgres server with two databases: n8n's own and the take's. Not two servers.
- No real-account smoke (dec 8): it is replaced by the loopback re-smoke (all on 127.0.0.1) plus ONE made-up lead during take preparation. No extra smoke against real accounts.
- Proof of counts (dec 9): a screenshot taken during the rehearsal, or the Postgres node preview. There is no live table screen in the take.
- The take never deletes (dec 2): it deletes no HubSpot contacts. Made-up contacts left over are listed by lead key and contact id, and the owner deletes them by hand in HubSpot after the take.
- Licence copies (dec 11): files under handover/promotion-inputs (Apache-2.0 from other holders) are never overwritten or re-licensed by any step. Patch tests run on a clean sdk tree.
- Flows (dec 7): already imported and activated by the laptop lead with scripts\n8n_api.py on made-up data. The owner only types y, the challenge and end.
- Secrets (dec 5): the laptop lead reads only masked take outputs and never the owner-only secrets or the real-run folders. The owner revokes the model key at clean-up (owner-only).

## Steps
| Step | Actor | Command | Expected | Duration (UTC / IST) |
|---|---|---|---|---|
| R1 loopback re-smoke | laptop lead | NOT SET (plan section 4 onward; not rewritten here) | all traffic on 127.0.0.1; it must pass before R2 (dec 12) | not run; duration: estimate, unverified; start time NOT SET |
| R2 first rehearsal of the changed flows on port 5690 | laptop lead | NOT SET (send one made-up lead twice with the same lead id to the rehearsal webhook; command not built, fill_flows.py not built) | mail 1, HubSpot write 1, stored row 1 in the stored-leads table (name NOT SET); take a screenshot of the counts (dec 9) | not run; target tonight or tomorrow morning IST per dec 12, exact time NOT SET; duration: estimate, unverified |
| P1 prep lead | laptop lead | NOT SET (send ONE made-up lead on the take's own free port) | 1 made-up lead processed; no real-account smoke (dec 8) | not run; duration: estimate, unverified |
| T19 in the take | owner types y, the challenge and end; laptop lead watches | NOT SET | same lead id sent twice: mail 1, HubSpot write 1, stored row 1 (the narrow claim of dec 1) | not run; duration: estimate, unverified; time NOT SET |
| Leftover list | laptop lead | NOT SET | list of leftover made-up contacts by lead key and contact id; the take deletes nothing (dec 2) | not run; duration: estimate, unverified |
| Hand delete in HubSpot | owner | by hand in HubSpot, from the leftover list | listed contacts gone | not run; duration: estimate, unverified |
| F8 check after clean-up | NOT SET (no actor named) | NOT SET (query each n8n table for the test lead id; table list NOT SET) | 0 rows (pass rule proposed, NOT SET by anyone) | not run; time NOT SET |
Times for the handoff (dec 12): the laptop lead writes the real UTC and IST start and end of R1 and R2 in the handoff. Only duration the plan states: whole old re-smoke 170 min clean (plan:72); that is the plan's own estimate for a different run, so it is NOT used for these steps.

## What I could not settle (see report)
Take port number; commands for R1-F8; stored-leads table name; F8 table list and actor; the real owner of both checks; any dates or clock times.
