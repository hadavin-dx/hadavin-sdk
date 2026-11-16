# QUESTIONS from core-hardening (lead-only; I keep working meanwhile; none blocks me)
Source: steps-edits/EDITS.md "NOT DECIDED" (round 2) and c6-skip-audit/REPORT.md.
1. HubSpot app 1: give it the delete right for the end-of-take removal of contacts, or have the owner remove leftovers by hand? (EDITS item 1)
2. Confirm decision 7 ("no real keys, mailboxes or client data") applies to agents, the loopback re-smoke and cloud sessions only, not to the owner's throwaway Gmail accounts, HubSpot test account and model key. (EDITS item 2, confirmation only)
3. Postgres logins for the real take: three logins or one; where n8n's database password lives. (item 3)
4. Which port the real take's n8n uses (rehearsal 5690; 5678/5679 are the owner's own). (item 4)
5. Is the real-account smoke (checks a to f) still planned, and in what order with the loopback re-smoke? (item 5)
6. Who does n8n's first-visit owner setup and switches the flows on at the real take. (item 6)
7. Confirm P14 (Windows browser reaches n8n inside WSL) from the first smoke evidence; EDITS rows E-07 and E-08 are held until then. (item 7)
8. Proof screen for the counts in the video: owner choice. (item 8)
9. Wording "one database" vs one Postgres server with two databases; fix DECISION-one-store line 14 too? (item 10)
10. Cut Phase 0 steps 1-7 and 9 out of OWNER-STEPS v3 (v4 already does; confirm v4 replaces v3). (item 12)
11. Scene 5: cut it or keep the stand-in (run sheet :56, :78); and run sheet :90 caption number "60.1 to 61.9 s" is unmeasured/unread: read the lane3 raw or drop the number (c6-skip-audit M1, F-006).
12. Mutation survivors: ceiling 200_000 for max_tokens needs the studio head's yes or a number from the provider page (patches-ready README).

13. (ORDER 019, lead only) The two baseline test failures are real defects in the tracked tree, not a scratch artefact (proof: patch-test-runs/FAIL-CAUSE.md, two fresh clones). Both are in files outside handover/core-hardening/, which this session may not edit: (a) the banned vendor word is in handover/BRIEF-PREAMBLE-studio-2026-11-06.md line 17 and handover/demo/portal/portal-design-v2.md line 234, and handover/reviews/P1a-idempotence-probe.txt is not UTF-8 text; (b) 10 licence problems under handover/promotion-inputs/ (7 LICENSE copies, 3 pyproject fields). Question: do you fix them (reword, convert to UTF-8, drop or re-license the copies) or do I get written permission to edit those paths? Note: my own raw logs also quoted the banned word; I redacted them (see report).

## Q14 (2026-11-16 core-hardening): scope of the C5 patches for the take
A necessity review (patches-ready/review/necessity-r1.md) says none of C-01, A-01, G5-wording is needed for the take's narrow claim; it recommends deferring A-01 and cutting C-01 to a minimal price/max_tokens check (only if the model program loads the Route config, which nobody has traced). We keep building C5 v3 as ordered. Please answer: (a) keep all three patches for the core regardless of the take, or (b) cut/defer A-01 and the C-01 extras for now? (c) Does the take's model program load Route? Also: A-01 makes the tick exit 1 while the audit outbox has rows left; does anything in the take watch the tick exit code?

## Q15 (2026-11-16 10:10Z core-hardening): findings of the static read of the real-v5 flows (cross-read/STATIC-PASS-real-v5.md; not yet independently verified, a verifier is running)
1. The re-smoke plan (plan-wp6-resmoke-v5.md:298) fills n8n-flows-FILM-v5, not real-v5. In film-v5 the CRM step is a plain HTTP POST to a stand-in, not the HubSpot node. So the same-id-twice cases A and B (plan :341) pass or fail on the film flows. Do you want the re-smoke to run real-v5 (with a stand-in CRM behind the node) or accept film-v5 as the proxy? How far the claim path of the two sets matches is UNKNOWN (nobody diffed them).
2. No step was found that empties the claim table (mf_leads) between rehearsal and take. The take id guards only the take program's tag. If the take reuses lead ids, the first send may be treated as a duplicate. Who owns the clean-start step, and is the take database new?
3. The lead id is sent by the caller (mf-form.json:27 submission_id; mf-hook.json:27 message_id), the claim is INSERT ... ON CONFLICT DO NOTHING on mf_leads.lead_key (mf-form.json:97), lease 45 s. A second send after lease expiry does NOT take over; only the recovery flow does (every 30 s, at most 3 attempts). The "120 s" and "20 s" lease numbers elsewhere are not this lease.
4. Model id and key file are not in the flows (n8n calls $env.DESK_URL/qualify); the spend limit lives in the stage program and is checked by the owner by eye. drive.py is not in any branch I can read.

## Q16 (2026-11-16, C7b evidence): flaky core test, two repo-guard failures, outside my folder
1. tests/test_s4_llm_guard.py::test_ids_and_plan_hashes_survive_redaction fails by chance, about 0.015 to 0.045 percent per run (a random pln- id sometimes triggers the command-withheld rule in approvals.channel.clean). It also fails on the unpatched base, so it is not caused by A-01, C-01 or G5. I may not edit src/ or tests/. Lead: allow a fix on a separate core branch, or accept the flake? (Class: random id collides with a redaction pattern; the fix belongs at the redaction rule.)
2. With handover/ present both trees fail the same 2 guard tests (vendor string and non-UTF-8 file under handover/; non-proprietary LICENSE files in promotion-inputs, which decision 11 says never to touch). Lead: confirm these are known and expected on this branch.
3. The brief's assumption that `git archive b4cce5b` leaves out handover/ was wrong; the C7b evidence says so.
Evidence: patches-ready/v3/evidence-c7b.md.

## Q17 (2026-11-16, real-v5 plan edits): HubSpot node swap
Real-v5's CrmUpsert is n8n's HubSpot node, which calls the internet, so the loopback re-smoke cannot run real-v5 unchanged. The edit list (paste-check/plan-v5-real-v5-edits.md, R8 step 2.1b) swaps ONLY that node for a loopback stand-in. Evidence then reads "real-v5 minus one node". Lead: accept, or choose another route? Also read the glue fill_flows.py and drive.py (not on this branch) and fix step 2.1's expected line.

## Q18 (2026-11-16 10:30Z, lane c "not checked" read; lead decision needed)
The zoom-out lane suggests: (1) stop C8 (mutation lane, run.py) and the C5 v5/C7 re-runs because decision 4 and necessity-r1.md say they are not in the take path; keep G5 wording + dead-man note only; (2) make the loopback re-smoke cases A and B (same id twice) plus one psql count on mf_leads the explicit pass/fail gate; (3) collapse C9/C10/C11/C4b into one who-types-what sheet; (4) QUEUE header rule 6 "ONE database" is stale vs decision 10. Default if no answer: I finish the rounds already running (run.py r2, C5 v5, C7b fix), start nothing new on C8/C5/C7, and keep v11 as the single owner sheet. Answer needed: stop C8/C5/C7 now? yes / no.

## Q19 (2026-11-16 10:45Z, v11 security review; lead decision needed, money/secret path)
1. The take's final clean-up archives contacts with a DELETE call inside a finally (AGENT-SCOPE section 3), which breaks decision 2. Can the program be changed (or the call removed) before the take? Until then go condition 5 cannot be given, and "close the terminal" is not a safe exit.
2. Which counter does the backstop use (account total from the usage page, or the program's own ledger), and does the ledger reset between a trial run and the real run?
3. The model program runs as the same Linux user as the lead, so the lead can read the key file and edit the backstop. Accept this in writing, or run the program as a separate user? v11 currently says the owner makes and cancels the key, which limits damage but does not remove access.
4. Real n8n stop and start commands, and whether the program prints cue lines. Does the model program re-read its settings file after it starts?
5. Default for old model keys: cancel all except the run key unless the owner writes a reason and an end date. OK?
Source: steps-edits/review-v11-security.md; builder questions Q1-Q11 in steps-edits/v11-NOTES-FOR-LEAD.md.

## Q20 (from the contradiction re-read, steps-edits/review-contradictions-r1.md)
1. Which cue line does the take program print to tell the owner to stop n8n (O:135 lists only y, challenge, end)? Or is there none and the owner stops n8n on a card cue?
2. Which database role empties mf_leads for the clean start, and which database does the real take use after the rehearsal container is removed?
3. How many HubSpot private apps exist and which scope has each (probe: create/change; n8n: write; take: read-only)? One line for the card.
4. After re-pin: which exit code does the code give when case C ends done/unknown?
5. Inputs S (AGENT-SCOPE) lines 5, 9, 13, 20 and X (DECISIONS) lines 2 and 9 are stale against your answers; I cannot edit inputs. Do you want a patch text for them?
