# Edit list v6 (fix pass 1): plan-wp6-resmoke-v5.md -> real-v5 minus ONE node (TEXT FOR THE LEAD; the plan itself is NOT edited)  **[SUPERSEDED by plan-v10-real-v5-edits.md plus plan-v10-corrections-after-chain.md; see SUPERSEDED-INDEX.md]**

**This list has 28 edits.** Replaces `plan-v5-real-v5-edits.md` (19 edits, review `review-real-v5-edits.md`: 6 findings and the nits). Edits are listed in plan order and named by their plan location (not by R-numbers: the plan has its own R1-R6 rules). Apply each as an exact-match replace of the OLD block by the NEW block; every OLD text occurs exactly once in `inputs/plan-wp6-resmoke-v5.md` (558 lines) and was machine-checked. The OLD and NEW blocks carry no `+ ` or `- ` prefixes (copy them as they stand; in particular the heredoc ends with a bare `PYEOF`). A dry-run apply to a scratch copy is in `dryrun-v6.txt`; its result is in `REPORT-real-v5-edits-v6.md`.

Evidence label for this run (lead answer Q17): "real-v5 minus ONE node (CrmUpsert)". The HubSpot node itself is covered by the owner's HubSpot probe and the take.

What closes each review finding: 1 time and step totals = edits at plan lines 5, 22, 295, 433, 441, 443, 445; 2 clean start = section 10b (export before emptying, `current_database()` guard, prep lead first, numbered row) and row CS; 3 row CS reworded; 4 lease sentence labelled read, not run, and moved to a new section 10b; 5 plan locations instead of R-ids; 6 `; true` and the eight count lines in 2.1b. Nits: film node copied verbatim (only `url` differs) with a diff recipe; CRM_URL assertion; prefixes removed; line 4 and line 6 updated; re-run instruction at plan line 296; INDEX line for the hashes; the garbled sentence at plan line 493 rewritten; "lead record" used for the data row.

## Edit 1: plan line 4 (header Status line, tail)
Why: Header must say which flow set runs and how the evidence is labelled.
Status: VERIFIED (plan text)

~~~~old
Status: v5 FINAL EDIT 2026-11-16 after plan-review round 3 of 3 (no further plan-review round).
~~~~
~~~~new
Status: v5 FINAL EDIT 2026-11-16 after plan-review round 3 of 3 (no further plan-review round). REAL-V5 EDIT 2026-11-16 (lead answers Q15.1 and Q17; DECISIONS-2026-11-16 item 1: the ONE video is real-v5 only): the flow set filled, imported and driven here is real-v5 with ONE node swapped for the loopback stand-in (step 2.1b). Label this evidence exactly "real-v5 minus ONE node (CrmUpsert)" everywhere; never write "real-v5 passed". The HubSpot node itself is covered by the owner's HubSpot probe and the take, not by this run. The earlier film flow set is not run (LATER VIDEO). Every change is in "CHANGES FROM v5 (real-v5 edit)".
~~~~

## Edit 2: plan line 5 (RIGHT-SIZE, floor time)
Why: Time total after 2.1b (2 minutes, builder estimate, not measured).
Status: VERIFIED (plan text); arithmetic: 171 + 2 = 173 min = 2 h 53 min

~~~~old
Floor about 2 h 51 min clean
~~~~
~~~~new
Floor about 2 h 53 min clean
~~~~

## Edit 3: plan line 6 ("New in v5" list)
Why: Name what is new in this edit.
Status: VERIFIED (plan text)

~~~~old
the one E repeat as case `E2`, 13.5k.
~~~~
~~~~new
the one E repeat as case `E2`, 13.5k. New in the real-v5 edit: 2.1b (the one swapped node), row CS in section 7, section 10b (clean start before the take).
~~~~

## Edit 4: plan line 8 (insert BEFORE the heading "## CHANGES FROM v4 ...")
Why: New changes table at the top of the changes.
Status: VERIFIED (plan text); the heading stays, the new block goes in front of it

~~~~old
## CHANGES FROM v4 (every round-3 finding and lead ruling, and the step that fixes it)
~~~~
~~~~new
## CHANGES FROM v5 (real-v5 edit, 2026-11-16; lead answers Q15.1, Q15.2, Q15.3, Q17; DECISIONS-2026-11-16 items 1, 2, 8, 10)
| id | finding | fixed in / verdict |
|---|---|---|
| Q15.1 | step 2.1 filled the film flow set; cases A, B, B2 ran on it | 2.1 fills `n8n-flows-real-v5`; P-2 archives it; 2.1b swaps only `CrmUpsert` for the loopback stand-in (the HubSpot node would leave loopback); every film reference removed or marked LATER VIDEO |
| Q17 | what the loopback evidence is called | exactly "real-v5 minus ONE node (CrmUpsert)"; never "real-v5 passed" (header, section 7 title note, section 9) |
| verifier 2 | the plan said "real-v5 at run time" is not proven without saying what runs | section 9 now says: real-v5 runs minus one node; the HubSpot node, its credential and its real answer are not exercised |
| verifier 4 | "processed once" overreaches | claim wording limited to the claim step and scenes C and E; lease-expiry sentence in section 10b, labelled read in the flow files, not run |
| Q15.2 | no clean start before the take | row CS in section 7 (proves only that the table is empty at T0 here) and the lead step in section 10b (export the list first, then empty, with a database-name guard) |
| static pass 6 | empty or missing lead id untested | named in section 9 as not proven |
| time | 2.1b adds a step | S2 12 to 14 min, steps 151 to 153, clean floor 171 to 173 min = 2 h 53 min (2.1b = 2 min, a builder estimate, not measured) |
| not changed | A, B, B2 pass rules; the Claim node is byte-identical in real-v5 and the film set (cmp, 2026-11-16) | so the claim-path result carries over; only the CRM call differs |

## CHANGES FROM v4 (every round-3 finding and lead ruling, and the step that fixes it)
~~~~

## Edit 5: plan line 22 (CHANGES FROM v4 table, estimate row)
Why: Time total.
Status: VERIFIED (plan text)

~~~~old
171 min clean is a floor
~~~~
~~~~new
173 min clean is a floor (171 before the real-v5 edit)
~~~~

## Edit 6: plan line 120 (section 2, `code` row)
Why: The demo archive holds real-v5.
Status: VERIFIED that real-v5 exists at 5fdc659d1 (git ls-tree, read-only, by the earlier builder); UNVERIFIED that the laptop worktree `$HD` has it: run `git -C $HD ls-tree --name-only 5fdc659d1 handover/demo/n8n-flows-real-v5/`

~~~~old
`$R/demo` = `git archive` of handover-demo `5fdc659d1` (film-v5, n8n-mainframe, n8n-tests only)
~~~~
~~~~new
`$R/demo` = `git archive` of handover-demo `5fdc659d1` (real-v5, n8n-mainframe, n8n-tests only; the film flow folder is not archived: LATER VIDEO)
~~~~

## Edit 7: plan line 126 (section 2, `ids` row)
Why: The word film names the flow set; the ids are the glue's.
Status: UNVERIFIED (ids come from the glue `fill_flows.py`, a take-branch file the lead verifies at re-pin; real-v5 files carry no workflow id, json `id` is null in all four)

~~~~old
| ids | film `smkForm000000001`,
~~~~
~~~~new
| ids | flows (real-v5) `smkForm000000001`,
~~~~

## Edit 8: plan line 223 (section 3, glue note)
Why: Records that the glue is called with `real`.
Status: UNVERIFIED (glue not readable here; lead verifies at re-pin)

~~~~old
`fill_flows.py` (flows Postgres credential = `smk_app` with `pg-app.pw`)
~~~~
~~~~new
`fill_flows.py` (flows Postgres credential = `smk_app` with `pg-app.pw`; run in 2.1 with the flow-set word `real`, UNVERIFIED 13)
~~~~

## Edit 9: plan line 236 (P-2 archive command)
Why: The demo tar must hold real-v5.
Status: VERIFIED path exists at 5fdc659d1 (see plan line 120 edit)

~~~~old
handover/demo/n8n-mainframe handover/demo/n8n-tests handover/demo/n8n-flows-film-v5;
~~~~
~~~~new
handover/demo/n8n-mainframe handover/demo/n8n-tests handover/demo/n8n-flows-real-v5;
~~~~

## Edit 10: plan line 284 (1b.2 grant justification)
Why: The grant list of `smk_app` now stands on real-v5.
Status: VERIFIED by reading all `query` fields of the four real-v5 files (verbs INSERT INTO, UPDATE, SELECT; table `mf_leads` only; `gen_random_uuid()` needs PostgreSQL 13 or later, the image is 16)

~~~~old
(film-v5: no DELETE, CREATE, TRUNCATE)
~~~~
~~~~new
(real-v5: the four flow files hold only INSERT INTO, UPDATE and SELECT on `mf_leads`, with `FOR UPDATE SKIP LOCKED` inside the recovery claims; no DELETE, CREATE, TRUNCATE, DROP or ALTER; drafter read 2026-11-16 at 5fdc659d1)
~~~~

## Edit 11: plan line 295 (S2 header)
Why: Time: S2 gains 2.1b.
Status: VERIFIED (plan text)

~~~~old
### S2 fill and import, route A (STOP / 12 min, `s2`; n8n NOT running)
~~~~
~~~~new
### S2 fill and import, route A (STOP / 14 min, `s2`; n8n NOT running)
~~~~

## Edit 12: plan line 296 (S2 re-run recipe)
Why: After a re-run of 2.1 the swap must be done again, else the HubSpot node reaches n8n.
Status: VERIFIED (plan text)

~~~~old
(`fill_flows.py:10` opens with `O_EXCL`, readiness B1).
~~~~
~~~~new
(`fill_flows.py:10` opens with `O_EXCL`, readiness B1); then run 2.1 and run 2.1b again (2.1 writes a fresh filled copy, so the swap is gone).
~~~~

## Edit 13: plan line 298 (step 2.1; new step 2.1b right after it)
Why: Step 2.1 fills real-v5; 2.1b is the one loopback-only swap, without which the run would leave loopback.
Status: The heredoc was run once in a scratch copy of real-v5 on 2026-11-16 (see REPORT-real-v5-edits-v6.md and `swap-test.txt`): UNVERIFIED on the laptop and in n8n 2.46.6 (UNVERIFIED 14)

~~~~old
- **2.1** `. $HOME/hadavin-smoke/env.sh; python3 -I $R/fill_flows.py $R/demo/handover/demo/n8n-flows-film-v5 $T/flows $T film object; sed "s#@@TAKE@@#$T#g" $W/egm/duplicate-proof-lead-desk/wp6/probe-smoke.json > $T/probe.json` -> `filled film 4 object`.
~~~~
~~~~new
- **2.1** `. $HOME/hadavin-smoke/env.sh; python3 -I $R/fill_flows.py $R/demo/handover/demo/n8n-flows-real-v5 $T/flows $T real object; sed "s#@@TAKE@@#$T#g" $W/egm/duplicate-proof-lead-desk/wp6/probe-smoke.json > $T/probe.json` -> `filled real 4 object` (lead verifies at re-pin: the glue is a take-branch file, not readable in this run's inputs; the expected word and line are the lead's to edit, the runner never adapts them; UNVERIFIED 13). Any other output, or a non-zero exit, = STOP.
- **2.1b** (NEW; paste file `pastes/2.1b.sh`; runs after 2.1 and BEFORE 2.2 and before any import). Why: real-v5's `CrmUpsert` is n8n's HubSpot node, which calls the HubSpot web address on the internet; this run is loopback only, US$0, with no real HubSpot (section 0, owner's smoke yes). So exactly ONE node of the filled copy is swapped for the loopback CRM stand-in (`crm_stub.py`, port 8771); every other node, every connection and the Claim step stay real-v5's own. Where the new `parameters` come from: they are a verbatim copy of the film flow's `CrmUpsert` `parameters` (read 2026-11-16 in `n8n-flows-film-v5/mf-sub-crm-mail.json`: same method, `sendBody`, `contentType`, `specifyBody`, `jsonBody` and `options.timeout` 10000; the film node's `retryOnFail`, `maxTries` 2, `waitBetweenTries` 1000 and `onError` `continueErrorOutput` are identical to real-v5's and stay), with ONE difference: film's `url` is `={{ $env.MF_CRM_URL }}/upsert`, this paste writes the literal stand-in address. The lead re-checks the copy once at re-pin: print the `parameters` of `CrmUpsert` from the film file and from the swapped copy with `python3 -I -c "import json,sys; d=json.load(open(sys.argv[1])); w=d[0] if isinstance(d,list) else d; print(json.dumps([x for x in w['nodes'] if x['name']=='CrmUpsert'][0]['parameters'],sort_keys=True,indent=1))" <file>` and `diff` the two outputs: only the `url` line may differ. Paste (the heredoc is part of the paste file; the text below carries no `+` or `-` prefixes: copy it as it stands):
```sh
. $HOME/hadavin-smoke/env.sh; CRM=$(grep '^CRM_URL=' $T/flow-values.env | cut -d= -f2-); F=$T/flows/mf-sub-crm-mail.json; echo "before $(sha256sum $F | cut -c1-12)"
python3 -I - "$F" "$CRM" <<'PYEOF'
import json, sys
p, crm = sys.argv[1], sys.argv[2]
assert crm.startswith("http://127.0.0.1:") and len(crm) > len("http://127.0.0.1:"), "CRM_URL empty or not the loopback address: STOP"
d = json.load(open(p)); w = d[0] if isinstance(d, list) else d
n = [x for x in w["nodes"] if x["name"] == "CrmUpsert"]
assert len(n) == 1 and n[0]["type"] == "n8n-nodes-base.hubspot", "CrmUpsert is not the HubSpot node: STOP"
n = n[0]; n["type"] = "n8n-nodes-base.httpRequest"; n["typeVersion"] = 4.2; n.pop("credentials", None)
n["parameters"] = {"method": "POST", "url": crm + "/upsert", "sendBody": True, "contentType": "json", "specifyBody": "json", "jsonBody": "={{ { hadavin_lead_id: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email, label: $('Qualify').first().json.label } }}", "options": {"timeout": 10000}}
json.dump(d, open(p, "w"))
print("CrmUpsert swapped to the loopback stand-in")
PYEOF
echo "python rc=$?"; echo "after $(sha256sum $F | cut -c1-12)"; grep -c 'n8n-nodes-base.hubspot' $T/flows/*.json; grep -c 'hubapi' $T/flows/*.json; true
```
  -> `CrmUpsert swapped to the loopback stand-in`; `python rc=0`; the `before` and `after` hashes differ; then 8 count lines (4 files x 2 greps, each `<path>:0`). Any assertion text, traceback, `python rc` other than 0, equal hashes, or any count above 0 = STOP (the HubSpot node must never reach n8n in this run: it would try the internet). The paste ends with `; true` on purpose: `grep -c` exits 1 when a count is 0, which is the PASS case here, so the `exit=<n>` line of R5 shows `exit=0` whenever the last command ran; the verdict is the printed lines, never the exit code. The runner writes the two hashes, `python rc` and the eight counts into PROGRESS and, as one line headed `real-v5 minus ONE node (CrmUpsert): before <hash> after <hash>`, at the top of `INDEX.md`. The imported but now unused HubSpot credential (`smkHs00000000001`, 2.3, 2.5) stays: the credential count of 3 is unchanged. UNVERIFIED 14 (the heredoc python is not syntax-checked by `bash -n`; UNVERIFIED 2 says so for every paste's python).
~~~~

## Edit 14: plan line 302 (2.5 expected text)
Why: Workflow ids name the real-v5 set.
Status: UNVERIFIED (depends on the glue ids)

~~~~old
6 workflow ids (4 `smk` film, `smkProbe00000001`, `smkExec000000001`)
~~~~
~~~~new
6 workflow ids (4 `smk` real-v5 flows, `smkProbe00000001`, `smkExec000000001`)
~~~~

## Edit 15: plan line 341 (11.1 expected text, case B)
Why: A, B, B2 name the flow set they test.
Status: VERIFIED by reading `mf-form.json:97` (2026-11-16)

~~~~old
B: 10 replies, every one with a verdict, at most 1 with repeat false (STOP otherwise: the headline claim);
~~~~
~~~~new
B: 10 replies, every one with a verdict, at most 1 with repeat false (STOP otherwise: the headline claim; A, B and B2 run on the real-v5 flows with only `CrmUpsert` swapped, 2.1b; the step that decides `repeat` is real-v5's own `Claim` node, `mf-form.json:97`, `INSERT ... ON CONFLICT (lead_key) DO NOTHING`);
~~~~

## Edit 16: plan line 433 (section 5, S2 row)
Why: Time: 2.1b added (2 min, a builder estimate, not measured).
Status: VERIFIED (plan text)

~~~~old
| S2 | 2.0 1, 2.1 1, 2.2 1, 2.3 2, 2.4 3, 2.5 1, 2.6 2, 2.7 1 | 12 |
~~~~
~~~~new
| S2 | 2.0 1, 2.1 1, 2.1b 2 (builder estimate, not measured), 2.2 1, 2.3 2, 2.4 3, 2.5 1, 2.6 2, 2.7 1 | 14 |
~~~~

## Edit 17: plan line 441 (section 5, steps total)
Why: Time total.
Status: VERIFIED (plan text)

~~~~old
| **steps** | | **151** |
~~~~
~~~~new
| **steps** | | **153** |
~~~~

## Edit 18: plan line 443 (section 5, clean total)
Why: Time total.
Status: VERIFIED (plan text)

~~~~old
| **clean total (a FLOOR, not a quote)** | | **171 min = 2 h 51 min** |
~~~~
~~~~new
| **clean total (a FLOOR, not a quote)** | | **173 min = 2 h 53 min** |
~~~~

## Edit 19: plan line 445 (section 5, quote sentence)
Why: Time total.
Status: VERIFIED (plan text)

~~~~old
2 h 51 min is a floor
~~~~
~~~~new
2 h 53 min is a floor
~~~~

## Edit 20: plan line 464 (section 7 heading)
Why: Row CS added (20 to 21 rows) and the evidence label.
Status: VERIFIED (plan text)

~~~~old
## 7. PASS/FAIL table to fill in `evidence-2\INDEX.md` (20 rows)
~~~~
~~~~new
## 7. PASS/FAIL table to fill in `evidence-2\INDEX.md` (21 rows)
The first line of `INDEX.md` reads "Evidence: real-v5 minus ONE node (CrmUpsert), loopback; not real-v5 as shipped" (lead answer Q17).
~~~~

## Edit 21: plan line 473 (row B1)
Why: B1 must not read as a test of the HubSpot node.
Status: VERIFIED (plan text)

~~~~old
| B1 | same-id burst on the new stack: <= 1 first-time verdict; B2 killed in flight ends final |
~~~~
~~~~new
| B1 | same-id burst on the new stack, on the real-v5 flows with `CrmUpsert` swapped (2.1b): <= 1 first-time verdict; B2 killed in flight ends final |
~~~~

## Edit 22: plan line 477 (row NC)
Why: NC names what is not exercised.
Status: VERIFIED (plan text)

~~~~old
Exercised: "CRM row written, ack not returned" (C) and "mail stored, ack not returned" (E) | statement |
~~~~
~~~~new
Exercised: "CRM row written, ack not returned" (C) and "mail stored, ack not returned" (E); NOT exercised: the real-v5 HubSpot node itself (swapped at 2.1b), its credential and its real answer | statement |
~~~~

## Edit 23: plan line 486 (after row Z1: new row CS)
Why: New row CS, reworded: it proves only that the table is empty at T0 here. The earlier wording "lead ids used once" was false (A, B, B2, C, E, E2 deliberately resend the same id) and `keys.txt` has no comparison set.
Status: VERIFIED (plan text); the empty-table proof rests on 3.4 reading `mf_leads` through `smk_count`

~~~~old
| Z1 | clean-up: no pid, container, port, `$R`; Docker names equal baseline; owner's 5678/5679 listeners and pids unchanged; no marker in `evidence-2\`; keep-alive gone (listed, never killed) | STOP | P-1, P-4, S13 | all empty / equal / unchanged; scan lists nothing; `keepalive-gone` | | |
~~~~
~~~~new
| Z1 | clean-up: no pid, container, port, `$R`; Docker names equal baseline; owner's 5678/5679 listeners and pids unchanged; no marker in `evidence-2\`; keep-alive gone (listed, never killed) | STOP | P-1, P-4, S13 | all empty / equal / unchanged; scan lists nothing; `keepalive-gone` | | |
| CS | clean start, this run only: the table of lead records is empty before the first send (a brand-new container; `T0 rows {}` is the proof). This row says nothing about lead ids (the cases resend ids on purpose) and nothing about the take; the take's clean start is a lead step in section 10b | STOP | 1b.2, 3.4 | `T0 rows {}` | | |
~~~~

## Edit 24: plan line 489 (section 8 MUST-NOT)
Why: The HubSpot node never runs.
Status: VERIFIED (plan text)

~~~~old
no grant, role or database beyond 1b.2;
~~~~
~~~~new
no grant, role or database beyond 1b.2; the real-v5 HubSpot node never runs (2.1b swaps it before any import, and its counts of 0 are checked);
~~~~

## Edit 25: plan line 493 (section 9 first bullet)
Why: Say exactly what is proven and not proven; fix the garbled last sentence.
Status: VERIFIED by reading `mf-form.json:27` and the plan's 1b.2 table (`lead_key text PRIMARY KEY`); the reply for a missing id is UNVERIFIED (nothing run)

~~~~old
Real HubSpot (O1, O2), real Gmail SMTP/IMAP (O3-O5), a real model call and ledger (O9), real-v5 at run time; the take's own `N8N_HEALTH_URL` value (only grepped in 0.1).
~~~~
~~~~new
Real HubSpot (O1, O2), including the real-v5 `CrmUpsert` HubSpot node itself: it is swapped for the loopback stand-in at 2.1b, so its credential, its real answer (`id` or `vid`) and the `CrmIdOk` digits rule on a real answer are NOT exercised (a non-numeric real id would fail the lead record: `V5-README.md`, GO-1 update); real Gmail SMTP/IMAP (O3-O5), a real model call and ledger (O9); the take's own `N8N_HEALTH_URL` value (only grepped in 0.1). The real-v5 flows DO run here, minus that one node: same-id-twice (A, B, B2), the in-flight crashes (C, E) and the restarts are tested on the real-v5 claim, recovery and mail nodes. Not proven by this run: an empty or missing lead id (`mf-form.json:27` copies `body.submission_id` unchecked; the table key cannot be empty, so the insert fails; the reply the caller then sees was not tested).
~~~~

## Edit 26: plan line 508 (insert BEFORE the heading "## 11. Quoted strings ...")
Why: Clean-start step and claim wording get their own heading: section 10 is titled "After the run (lead, not runner)", which does not fit a take-prep step.
Status: VERIFIED (plan text); the heading stays, the new block goes in front of it

~~~~old
## 11. Quoted strings and their source lines (for re-pinning in minutes)
~~~~
~~~~new
## 10b. Before the take (lead steps; NOT part of this run; the runner never does these)
**Clean start before the take (row CS for the take; owner of the step: the lead; lead answer Q15.2; DECISIONS item 2: the take never deletes contacts, the owner deletes leftovers by hand in HubSpot).** This run proves a clean start only inside its own throwaway container. In the take's own database (one Postgres server with two databases, n8n's own and the take's; DECISIONS item 10), in this order:
1. **Prep lead first.** The ONE made-up prep lead (DECISIONS item 8) is sent BEFORE the table is emptied, so its row is in the export of step 3 and its HubSpot contact is on the hand-deletion list.
2. **Check the database, then print the count.** As the database owner or superuser (the app role cannot delete or truncate: N4, N9 here), run `SELECT current_database(), count(*) FROM <schema>.mf_leads;` and read the database name against the take's database name. If the name is not the take's database (for example it is n8n's own, or a rehearsal database that still matters), STOP: do not truncate.
3. **Export before emptying.** Write `lead_key` and `crm_id` of every row to a file the lead keeps (`COPY (SELECT lead_key, crm_id FROM <schema>.mf_leads ORDER BY created_at) TO STDOUT`; made-up data only). This is the list the owner needs to delete the leftover contacts by hand in HubSpot after the take. Check that the file's line count equals the count from step 2. Only then continue.
4. **Empty the table:** `TRUNCATE <schema>.mf_leads` (schema and database names as the take's database has them: UNVERIFIED 15). Read the count back through the read-only count role: it must be `0` before the first send of the take, or the take does not start.
5. **Fresh ids.** The take uses lead ids made up for it and never sent in any rehearsal; the lead compares them with the rehearsal's sent ids and picks new ones if one matches.
6. **Numbered row in the owner and lead steps.** One numbered row goes into OWNER-STEPS version 4 and later (the lead picks the next free number; the highest in version 3 is step 18). Row text: "Step N (the lead): before the take, send the prep lead, check the database name, export the lead list, empty the lead table, read back 0; use fresh lead ids only. Owner of this step: the lead. The owner has nothing to do here except, after the take, deleting by hand in HubSpot the contacts on the exported list." Version 3 is archived, never deleted (DECISIONS item 10).

**Claim wording the plan supports (lead answer Q15.3).** "A lead sent twice with the same id inside the lease (45 seconds in real-v5) is processed once." Honest limit, to be written in the claim text; READ in `mf-form.json:97` and `mf-recovery.json:26`, NOT run in this plan: after the lease has run out, a second send is still stopped by the stored row (the insert checks only the lead id, never `claimed_until`) and the reply shows the stored state; only the recovery flow (every 30 seconds, at most 3 attempts) runs a stuck lead record again. This plan shows "processed once" only for the claim step and the crash scenes C and E; it does not show it for a crash between the CRM call and the claim write beyond what row NC lists.

## 11. Quoted strings and their source lines (for re-pinning in minutes)
~~~~

## Edit 27: plan line 543 (section 11 table, row M3)
Why: Row M3 names real-v5 and its line.
Status: VERIFIED (the string is present in the real-v5 file at line 258, by grep)

~~~~old
| M3 | n8n-flows-film-v5/mf-sub-crm-mail.json | `'[demo] lead ' + $('SubIn').first().json.lead_key` | (subject) |
~~~~
~~~~new
| M3 | n8n-flows-real-v5/mf-sub-crm-mail.json | `'[demo] lead ' + $('SubIn').first().json.lead_key` | 258 (subject) |
~~~~

## Edit 28: plan line 558 (after UNVERIFIED item 12)
Why: New UNVERIFIED items 13 to 16.
Status: VERIFIED (plan text); the facts inside are UNVERIFIED by definition

~~~~old
A refusal of the flag fails 1b.1 (no container) = STOP, never a pull.
~~~~
~~~~new
A refusal of the flag fails 1b.1 (no container) = STOP, never a pull.
13. The glue `fill_flows.py` and `drive.py` (take-branch files, local only, not readable in this plan's inputs; the lead verifies at re-pin): that the glue accepts the flow-set word `real`, prints `filled real 4 object`, fills the real-v5 tokens (`DESK_URL`, `DESK_TIMEOUT_MS`, `DESK_ALERT_TO`) and the placeholders only real-v5 has (`FROM_ADDRESS_PLACEHOLDER`, `INTAKE_ADDRESS_PLACEHOLDER`, `HS_CRED_PLACEHOLDER`) from `flow-values.env`, and exits non-zero while a placeholder is left. The lead edits 2.1's expected line before the run.
14. 2.1b: that n8n 2.46.6 imports and runs the swapped `CrmUpsert` (an HTTP Request node, version 4.2: the node type and version of the film flow's `CrmUpsert` and of `Qualify` in the same file); that the heredoc python is free of syntax errors on the laptop (it ran once in a scratch copy of real-v5 here, not on the laptop); that `CRM_URL=` is a line of `flow-values.env` (plan line 271 lists it; not run). The node's 10000 ms timeout is the film node's own value and is above the 8000 ms CRM hold (plan line 129), as it was in the film set.
15. The take's database, schema and table names for section 10b: the plan's own container uses database `postgres`, schema `app`, table `mf_leads`; DECISIONS item 10 says the take has its own database; the take's names are not read.
16. That the exported lead list matches the contacts really created in HubSpot: the list holds the leads sent to the flow, not what HubSpot holds; the owner checks the HubSpot contact list against it after the take.
~~~~
