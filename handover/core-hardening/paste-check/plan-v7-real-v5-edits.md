# Edit list v7 (fix pass 2, the last non-security round): plan-wp6-resmoke-v5.md -> real-v5 minus ONE node (TEXT FOR THE LEAD; the plan itself is NOT edited)

**This list has 29 edits.** Replaces `plan-v6-real-v5-edits.md` (28 edits; reviews `review-v6-readiness.md`: 8 majors and the nits; `review-v6-facts.md`: 4 majors and the minors). Edits are listed in plan order and named by their plan location (not by R-numbers: the plan has its own R1-R6 rules). Apply each as an exact-match replace of the OLD block by the NEW block; every OLD text occurs exactly once in `inputs/plan-wp6-resmoke-v5.md` (558 lines) and was machine-checked (`apply-v7.py`, result in `dryrun-v7.txt`). The OLD and NEW blocks carry no `+ ` or `- ` prefixes (copy them as they stand; in particular the heredoc ends with a bare `PYEOF`). Words: "the lead" means only the Claude session that runs this plan; the data the plan sends and stores is called a "made-up lead record" (its key, "lead-record id", is the `lead_key` column).

Evidence label for this run (lead answer Q17): "real-v5 minus ONE node (CrmUpsert)". The HubSpot node itself is covered by the owner's HubSpot probe and the take.

**What closes each round-2 finding.** Readiness: 1 and 2 = edit 27 (section 10b: one `psql` call that checks `current_database()` against a name the lead fills in and only then empties the table; n8n stopped, one transaction with the table locked, count read again after); 3 = edit 27 step 8 (the v11 sheet has no running numbers; no wrong anchor given); 4 = wording throughout; 5 = edit 26; 6 = edit 13 (recipe uses `git -C $HD show 5fdc659d1:...` and names the swapped file); 7 = edit 13 (what the stand-in answers; `CrmIdOk` takes it); 8 = edit 13 (the negative run was really run: `swap-test-negative.txt`, with the script and input in `swap-test/`). Facts: 1 = edit 27 step 8; 2 = edit 27 opening (marked as drafter additions beyond Q15.2, and the two database names reconciled); 3 = edit 26 (the unsourced citation is gone; the digits rule is sourced); 4 = edit 13 and the `swap-test/` folder; minors 5, 6, 7 = edits 4, 13, 26 and the table in edit 4. Nits: exact match of the stand-in address; plan steps cited by name in edit 29; file-count sentences include `2.1b.sh` (edits 16 and 20); `INDEX.md` line order stated in edit 21; crm_id empty after a lost answer and where the rehearsal ids are named in edit 27.

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
| what runs | the plan said "real-v5 at run time" without saying what runs | section 9 now says: real-v5 runs minus one node; the HubSpot node, its credential and its real answer are not exercised |
| claim wording | "processed once" overreaches | claim wording limited to the claim step and scenes C and E; lease-expiry sentence in section 10b, labelled read in the flow files, not run |
| Q15.2 | no clean start before the take | row CS in section 7 (proves only that the table is empty at T0 here) and section 10b (the lead's steps; the parts beyond Q15.2 are marked there as drafter additions) |
| static pass 6 | empty or missing lead-record id untested | named in section 9 as not proven |
| time | 2.1b adds a step | S2 12 to 14 min, steps 151 to 153, clean floor 171 to 173 min = 2 h 53 min (2.1b = 2 min, a builder estimate, not measured) |
| not changed | A, B, B2 pass rules; `mf-form.json` (holds the Claim node) has the same whole-file sha256 in real-v5 and film-v5: `74a823d4bc99`, `evidence-A2.md:7` and `:11` (`mf-hook.json` too, `:6` and `:10`; `mf-recovery.json` and `mf-sub-crm-mail.json` differ) | so the claim-path result carries over; only the CRM call (and the recovery and mail files) differ |

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
Status: UNVERIFIED (ids come from the glue `fill_flows.py`, a take-branch file the lead verifies at re-pin)

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
Status: VERIFIED path exists at 5fdc659d1 (see edit 6)

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
Status: The paste was run on Linux in a scratch copy of the real-v5 file (whole-file sha256 `b3277363ae04...`, equal to `evidence-A2.md:9`) with one right value and six wrong values of `CRM_URL`: output in `swap-test-negative.txt`; script, input copy and re-run command in `swap-test/` (`bash swap-test/run.sh`). UNVERIFIED on the laptop and in n8n 2.46.6 (UNVERIFIED 14)

~~~~old
- **2.1** `. $HOME/hadavin-smoke/env.sh; python3 -I $R/fill_flows.py $R/demo/handover/demo/n8n-flows-film-v5 $T/flows $T film object; sed "s#@@TAKE@@#$T#g" $W/egm/duplicate-proof-lead-desk/wp6/probe-smoke.json > $T/probe.json` -> `filled film 4 object`.
~~~~
~~~~new
- **2.1** `. $HOME/hadavin-smoke/env.sh; python3 -I $R/fill_flows.py $R/demo/handover/demo/n8n-flows-real-v5 $T/flows $T real object; sed "s#@@TAKE@@#$T#g" $W/egm/duplicate-proof-lead-desk/wp6/probe-smoke.json > $T/probe.json` -> `filled real 4 object` (the lead verifies at re-pin: the glue is a take-branch file, not readable in this run's inputs; the expected word and line are the lead's to edit, the runner never adapts them; UNVERIFIED 13). Any other output, or a non-zero exit, = STOP.
- **2.1b** (NEW; paste file `pastes/2.1b.sh`; runs after 2.1 and BEFORE 2.2 and before any import). Why: real-v5's `CrmUpsert` is n8n's HubSpot node, which calls the HubSpot web address on the internet; this run is loopback only, US$0, with no real HubSpot (section 0, owner's smoke yes). So exactly ONE node of the filled copy, `$T/flows/mf-sub-crm-mail.json`, is swapped for the loopback CRM stand-in (`crm_stub.py`, port 8771); every other node, every connection and the Claim step stay real-v5's own. Where the new `parameters` come from: they are a copy of the film flow's `CrmUpsert` `parameters`, with ONE difference (the `url`: film has `={{ $env.MF_CRM_URL }}/upsert`, this paste writes the literal stand-in address). The film node's `retryOnFail`, `maxTries` 2, `waitBetweenTries` 1000 and `onError` `continueErrorOutput` are identical to real-v5's and stay. Checked on 2026-11-16 by the diff recipe below, run on Linux against scratch copies (`swap-test-recipe-check.txt`): the only differing line was `url`. The lead repeats the recipe once at re-pin, because the film file is not archived to the run (edits 6 and 9) and is read from git instead: `P='import json,sys; d=json.load(open(sys.argv[1])); w=d[0] if isinstance(d,list) else d; print(json.dumps([x for x in w["nodes"] if x["name"]=="CrmUpsert"][0]["parameters"],sort_keys=True,indent=1))'; git -C $HD show 5fdc659d1:handover/demo/n8n-flows-film-v5/mf-sub-crm-mail.json > $T/film-crm.json; python3 -I -c "$P" $T/film-crm.json > $T/p-film.txt; python3 -I -c "$P" $T/flows/mf-sub-crm-mail.json > $T/p-swap.txt; diff $T/p-film.txt $T/p-swap.txt` (`diff` exits 1 when the files differ; only the `url` line may be listed; a second differing line = STOP).
  **What the stand-in answers, and why the next node accepts it.** `POST /upsert` answers HTTP 200 with `{"id": <whole number counted from 1>, "created": true or false}` while its control field `upsert_answer` is `id`, which is the default (`crm_stub.py` lines 3, 9 and 33-43 in a scratch copy of the demo archive, read 2026-11-16; `evidence-A4.md:2105` quotes `V5-README.md:19` for the default). The node after `SetCrmId` is `CrmIdOk`; it stays in the swapped file and takes the stand-in's answer, so it IS exercised here, on the stand-in's answer. Its rule is "digits only" (`^[0-9]+$` on `id ?? vid ?? empty`: quoted from `handover/demo/REPORT.md:4` in `evidence-A4-tree-hits.tsv:995`; the node's own expression was not read, because the flow files are not in this plan's inputs). By that reading a whole-number id passes. UNVERIFIED 14 holds the rest: if the stand-in's id ever failed `CrmIdOk`, every made-up lead record in A, B and C would end in the failure path and the run would STOP at A.
  Paste (the heredoc is part of the paste file; the text below carries no `+` or `-` prefixes: copy it as it stands):
```sh
. $HOME/hadavin-smoke/env.sh; CRM=$(grep '^CRM_URL=' $T/flow-values.env | cut -d= -f2-); F=$T/flows/mf-sub-crm-mail.json; echo "before $(sha256sum $F | cut -c1-12)"
python3 -I - "$F" "$CRM" <<'PYEOF'
import json, sys
p, crm = sys.argv[1], sys.argv[2]
assert crm == "http://127.0.0.1:8771", "CRM_URL is not exactly http://127.0.0.1:8771: STOP"
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
  -> `CrmUpsert swapped to the loopback stand-in`; `python rc=0`; the `before` and `after` hashes differ; then 8 count lines (4 files x 2 greps, each `<path>:0`). Any assertion text, traceback, `python rc` other than 0, equal hashes, or any count above 0 = STOP (the HubSpot node must never reach n8n in this run: it would try the internet). The address check is an exact match of `CRM_URL` with `http://127.0.0.1:8771` (an empty value, a missing line, two lines, another port, another host and an address with a user-name trick were each refused in the negative run, and the file stayed unchanged: `swap-test-negative.txt`). The paste ends with `; true` on purpose: `grep -c` exits 1 when a count is 0, which is the PASS case here, so the `exit=<n>` line of R5 shows `exit=0` whenever the last command ran; the verdict is the printed lines, never the exit code. The runner writes the two hashes, `python rc` and the eight counts into PROGRESS and, as line 2 of `INDEX.md` (line 1 is the evidence label of edit 21), one line headed `real-v5 minus ONE node (CrmUpsert): before <hash> after <hash>`. The imported but now unused HubSpot credential (`smkHs00000000001`, 2.3, 2.5) stays: the credential count of 3 is unchanged. UNVERIFIED 14 (the heredoc python is not syntax-checked by `bash -n` on the laptop; UNVERIFIED 2 says so for every paste's python).
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
B: 10 replies, every one with a verdict, at most 1 with repeat false (STOP otherwise: the headline claim; A, B and B2 are evidence "real-v5 minus ONE node (CrmUpsert)", 2.1b; the step that decides `repeat` is real-v5's own `Claim` node, `mf-form.json:97`, `INSERT ... ON CONFLICT (lead_key) DO NOTHING`);
~~~~

## Edit 16: plan line 428 (section 5, P-3a row, file count)
Why: The count of files to write must include the new paste file `2.1b.sh` (and the time stays 13 min: one more small file).
Status: VERIFIED (plan text); the count 70 is the plan's own "about"

~~~~old
P-3a 13 (about 70 paste files + 6 glue files,
~~~~
~~~~new
P-3a 13 (about 71 paste files, `2.1b.sh` included, + 6 glue files,
~~~~

## Edit 17: plan line 433 (section 5, S2 row)
Why: Time: 2.1b added (2 min, a builder estimate, not measured).
Status: VERIFIED (plan text)

~~~~old
| S2 | 2.0 1, 2.1 1, 2.2 1, 2.3 2, 2.4 3, 2.5 1, 2.6 2, 2.7 1 | 12 |
~~~~
~~~~new
| S2 | 2.0 1, 2.1 1, 2.1b 2 (builder estimate, not measured), 2.2 1, 2.3 2, 2.4 3, 2.5 1, 2.6 2, 2.7 1 | 14 |
~~~~

## Edit 18: plan line 441 (section 5, steps total)
Why: Time total.
Status: VERIFIED (plan text)

~~~~old
| **steps** | | **151** |
~~~~
~~~~new
| **steps** | | **153** |
~~~~

## Edit 19: plan line 443 (section 5, clean total)
Why: Time total.
Status: VERIFIED (plan text)

~~~~old
| **clean total (a FLOOR, not a quote)** | | **171 min = 2 h 51 min** |
~~~~
~~~~new
| **clean total (a FLOOR, not a quote)** | | **173 min = 2 h 53 min** |
~~~~

## Edit 20: plan line 445 (section 5, quote sentence)
Why: Time total, and the count of unrun files (the new paste file `2.1b.sh` makes 77).
Status: VERIFIED (plan text)

~~~~old
2 h 51 min is a floor: about 76 files are unrun
~~~~
~~~~new
2 h 53 min is a floor: about 77 files are unrun
~~~~

## Edit 21: plan line 464 (section 7 heading)
Why: Row CS added (20 to 21 rows) and the evidence label.
Status: VERIFIED (plan text)

~~~~old
## 7. PASS/FAIL table to fill in `evidence-2\INDEX.md` (20 rows)
~~~~
~~~~new
## 7. PASS/FAIL table to fill in `evidence-2\INDEX.md` (21 rows)
Line 1 of `INDEX.md` reads "Evidence: real-v5 minus ONE node (CrmUpsert), loopback; not real-v5 as shipped" (lead answer Q17); line 2 is the hash line of 2.1b.
~~~~

## Edit 22: plan line 473 (row B1)
Why: B1 must not read as a test of the HubSpot node.
Status: VERIFIED (plan text)

~~~~old
| B1 | same-id burst on the new stack: <= 1 first-time verdict; B2 killed in flight ends final |
~~~~
~~~~new
| B1 | same-id burst on the new stack (evidence "real-v5 minus ONE node (CrmUpsert)", 2.1b): <= 1 first-time verdict; B2 killed in flight ends final |
~~~~

## Edit 23: plan line 477 (row NC)
Why: NC names what is not exercised.
Status: VERIFIED (plan text)

~~~~old
Exercised: "CRM row written, ack not returned" (C) and "mail stored, ack not returned" (E) | statement |
~~~~
~~~~new
Exercised: "CRM row written, ack not returned" (C) and "mail stored, ack not returned" (E); NOT exercised: the real-v5 HubSpot node itself (swapped at 2.1b), its credential and its real answer | statement |
~~~~

## Edit 24: plan line 486 (after row Z1: new row CS)
Why: New row CS, reworded: it proves only that the table is empty at T0 here. The earlier wording "ids used once" was false (A, B, B2, C, E, E2 deliberately resend the same id) and `keys.txt` has no comparison set.
Status: VERIFIED (plan text); the empty-table proof rests on 3.4 reading `mf_leads` through `smk_count`

~~~~old
| Z1 | clean-up: no pid, container, port, `$R`; Docker names equal baseline; owner's 5678/5679 listeners and pids unchanged; no marker in `evidence-2\`; keep-alive gone (listed, never killed) | STOP | P-1, P-4, S13 | all empty / equal / unchanged; scan lists nothing; `keepalive-gone` | | |
~~~~
~~~~new
| Z1 | clean-up: no pid, container, port, `$R`; Docker names equal baseline; owner's 5678/5679 listeners and pids unchanged; no marker in `evidence-2\`; keep-alive gone (listed, never killed) | STOP | P-1, P-4, S13 | all empty / equal / unchanged; scan lists nothing; `keepalive-gone` | | |
| CS | clean start, this run only: the table of made-up lead records is empty before the first send (a brand-new container; `T0 rows {}` is the proof). This row says nothing about lead-record ids (the cases resend ids on purpose) and nothing about the take; the take's clean start is in section 10b (steps for the lead) | STOP | 1b.2, 3.4 | `T0 rows {}` | | |
~~~~

## Edit 25: plan line 489 (section 8 MUST-NOT)
Why: The HubSpot node never runs.
Status: VERIFIED (plan text)

~~~~old
no grant, role or database beyond 1b.2;
~~~~
~~~~new
no grant, role or database beyond 1b.2; the real-v5 HubSpot node never runs (2.1b swaps it before any import, and its counts of 0 are checked);
~~~~

## Edit 26: plan line 493 (section 9 first bullet)
Why: Say exactly what is proven and not proven; fix the garbled last sentence; correct the claim about the empty key.
Status: VERIFIED by reading the plan's 1b.2 table (`lead_key text PRIMARY KEY`) and by running the Postgres rule on a scratch server on 2026-11-16 (the last lines of `clean-start-test-output.txt`: on a scratch Postgres 16 server a `text PRIMARY KEY` refused NULL, accepted `''` once and refused a second `''`); `mf-form.json:27` (copies `body.submission_id` unchecked) was read by an earlier agent and not re-read here; what the caller sees for an empty or missing id is UNVERIFIED (nothing run)

~~~~old
Real HubSpot (O1, O2), real Gmail SMTP/IMAP (O3-O5), a real model call and ledger (O9), real-v5 at run time; the take's own `N8N_HEALTH_URL` value (only grepped in 0.1).
~~~~
~~~~new
Real HubSpot (O1, O2), including the real-v5 `CrmUpsert` HubSpot node itself: it is swapped for the loopback stand-in at 2.1b, so its credential and its real answer (`id` or `vid`) are NOT exercised (the digits rule of the next node, `CrmIdOk`, IS exercised, but only on the stand-in's whole-number id; a non-numeric real id would send the made-up lead record to the failure path: rule quoted from `handover/demo/REPORT.md:4` in `evidence-A4-tree-hits.tsv:995`); real Gmail SMTP/IMAP (O3-O5), a real model call and ledger (O9); the take's own `N8N_HEALTH_URL` value (only grepped in 0.1). The real-v5 flows DO run here, minus that one node: same-id-twice (A, B, B2), the in-flight crashes (C, E) and the restarts are tested on the real-v5 claim, recovery and mail nodes. Not proven by this run: an empty or missing lead-record id (`mf-form.json:27` copies `body.submission_id` unchecked; a missing id probably becomes NULL, which the table's primary key refuses, so the insert fails; an empty text `''` is accepted by the primary key and would be stored as a record with an empty key; what the caller then sees was tested for neither).
~~~~

## Edit 27: plan line 508 (insert BEFORE the heading "## 11. Quoted strings ...")
Why: The clean-start step and the claim wording get their own heading: section 10 is titled "After the run (lead, not runner)", which does not fit a take-prep step.
Status: VERIFIED (plan text); the heading stays, the new block goes in front of it. The paste in step 4 was run on Linux against a scratch Postgres 16 server with made-up rows (`clean-start-test-output.txt`; script and re-run command in `clean-start-test/`); UNVERIFIED on the take's server (UNVERIFIED 15)

~~~~old
## 11. Quoted strings and their source lines (for re-pinning in minutes)
~~~~
~~~~new
## 10b. Before the take (steps for the lead, the Claude session; NOT part of this run; the runner never does these)
**Drafter addition, going beyond lead answer Q15.2.** Q15.2 (`ORDERS.md:123`) says: use fresh made-up lead-record ids never used in the rehearsal AND the lead empties `mf_leads` in the rehearsal database before the take; add it as one numbered row in the owner and lead steps (v4 and later), owner of the step: the lead. This section keeps that and adds, for the lead to accept or strike: the database-name check, the export before emptying, n8n stopped plus one locked transaction, the read-back of 0 through the read-only count role, the made-up prep lead record sent first (DECISIONS item 8) and the list for deleting contacts by hand (DECISIONS item 2: the take never deletes contacts; the owner deletes leftovers by hand in HubSpot).
**Which database.** Q15.2 says "the rehearsal database"; DECISIONS item 10 says one Postgres server with two databases (n8n's own and the take's). Reconciled here: this section empties `mf_leads` in the database THE TAKE will use, named by the lead in `TAKE_DB_NAME`. If the take reuses the rehearsal's database, that is the rehearsal database and Q15.2 holds as written. If the take has its own, new database, the table is empty already and the same paste serves as the check (export of 0 rows, count 0). A rehearsal database the take does not use is not touched by this section.
1. **Fill-ins (UNVERIFIED 15):** `TAKE_DB_NAME` (the take's database name), `SCHEMA` (the take's schema), `PGURL` (a login of the database owner or a superuser for that database; the app role cannot empty tables: N4 and N9 here), `OUT` (the export file, outside any repository, a path without spaces).
2. **Prep lead record first.** Send the ONE made-up prep lead record (DECISIONS item 8) through the flows while n8n runs, and wait until its row has a final state, read through the read-only count role. Its row is then in the export of step 4 and its HubSpot contact is on the deletion list.
3. **Stop arrivals.** Stop n8n, or make every flow inactive, and check with the lead's own listing that none is active. Why: the recovery flow runs every 30 seconds (`evidence-A2.md:176`) and any row written between the export and the emptying would be emptied without being on the list, leaving a HubSpot contact nobody knows about. The lock in step 4 is a second guard, not a replacement.
4. **One call: check the database, export, empty, count again.** Run the paste below once. It connects with `PGURL`, compares `current_database()` with `TAKE_DB_NAME` and stops with an error if they differ (nothing is changed); otherwise, inside ONE transaction with the table locked, it counts the rows, writes `lead_key` and `crm_id` of every row to `OUT`, compares the file's line count with the row count, empties the table, counts again and commits only if the count is 0. Any failed check rolls the transaction back.
```sh
# Lead fill-ins before running (UNVERIFIED 15): TAKE_DB_NAME, SCHEMA, PGURL (owner or superuser login to the take's database), OUT (export file, outside any repo).
# Stop n8n (or deactivate every flow) first, so no row can arrive while this runs. The LOCK below is a second guard, not a replacement.
export OUT
psql "$PGURL" -X -q -v ON_ERROR_STOP=1 -v want="$TAKE_DB_NAME" -v tbl="$SCHEMA.mf_leads" -v out="$OUT" <<'SQL'
SELECT current_database() = :'want' AS db_ok \gset
\if :db_ok
\else
  \echo WRONG DATABASE: current_database() is not the expected name. STOP, nothing was changed.
  SELECT 1/0 AS wrong_database_stop;
\endif
BEGIN;
LOCK TABLE :tbl IN ACCESS EXCLUSIVE MODE;
SELECT count(*) AS n FROM :tbl \gset
\echo rows before: :n
\o :out
COPY (SELECT lead_key, crm_id FROM :tbl ORDER BY created_at) TO STDOUT;
\o
\set lines `wc -l < "$OUT"`
SELECT (:lines = :n) AS export_ok \gset
\if :export_ok
  TRUNCATE :tbl;
  SELECT count(*) AS n_after FROM :tbl \gset
  SELECT (:n_after = 0) AS empty_ok \gset
  \if :empty_ok
    COMMIT;
    \echo OK: exported :n rows to the file, table emptied, count now :n_after
  \else
    ROLLBACK;
    \echo COUNT AFTER TRUNCATE IS NOT 0. STOP, rolled back.
    SELECT 1/0 AS not_empty_stop;
  \endif
\else
  ROLLBACK;
  \echo EXPORT LINE COUNT (:lines) DOES NOT MATCH ROW COUNT (:n). STOP, nothing was emptied.
  SELECT 1/0 AS export_mismatch_stop;
\endif
SQL
echo "psql rc=$?"
```
   -> `rows before: <n>`, then `OK: exported <n> rows to the file, table emptied, count now 0`, then `psql rc=0`. Anything else (`WRONG DATABASE`, `DOES NOT MATCH`, `NOT 0`, an `ERROR` line, `psql rc` other than 0) = STOP; nothing was emptied. Tested on a scratch server (`clean-start-test-output.txt`): the wrong database stopped with 4 rows left; an export file that could not match stopped with 4 rows left; the right database exported 4 rows (a key holding a line break stayed on ONE line, written as `\n`), emptied the table and ended with `psql rc=0`; a second session that inserted while the first held the lock waited and its row landed after the emptying, so a late row would show up as a non-zero count, never as a hidden loss.
5. **Read back 0.** Read the count through the read-only count role of the take (its name is the lead's to fill in: UNVERIFIED 15): it must be `0` before the first send of the take, or the take does not start. Then start n8n or make the flows active again.
6. **Deletion list for the owner.** Keep `OUT`: it holds the lead-record id and the HubSpot contact id of every made-up lead record (the prep lead record included). A row whose `crm_id` is empty may still have a HubSpot contact (in cases like C and E the answer is lost after the contact was written): for those, the owner searches HubSpot for the lead-record id. The owner deletes the contacts by hand after the take.
7. **Fresh ids.** The take uses lead-record ids made up for it and never sent in any rehearsal. The lead compares them with the `lead_key` column of the export in step 4 (the rehearsal's rows, when the take reuses the rehearsal's database) and with the case ids in `drive.py` (a take-branch file, not readable here: UNVERIFIED 13), and picks new ones if one matches.
8. **The row in the owner and lead steps.** The v11 owner sheet has no running step numbers (it uses Step 0, A to J and I.0), and the v3 sheet's numbering (steps 1 to 23) is archived and no anchor for v11. The lead therefore places ONE row where the v11 sheet puts the lead's own tasks and gives it a name or letter the lead picks; this plan names none. Row text: "Before the take (the lead): send the prep lead record, check the database name, export the lead-record list, empty the table, read back 0; use fresh lead-record ids only. Owner of this step: the lead. The owner has nothing to do here except, after the take, deleting by hand in HubSpot the contacts on the exported list." Version 3 is archived, never deleted (DECISIONS item 10).

**Claim wording the plan supports (lead answer Q15.3; "lead" in the claim means the made-up lead record).** "A lead sent twice with the same id inside the lease (45 seconds in real-v5) is processed once." Honest limit, to be written in the claim text; READ in the flow files by an earlier agent (`evidence-A2.md:73` and `:80`: the insert holds `ON CONFLICT (lead_key) DO NOTHING` and a 45 second lease; `:223`: the recovery update takes only rows whose lease has run out and with fewer than 3 attempts), NOT run in this plan: after the lease has run out, a second send is still stopped by the stored row (the insert checks only the lead-record id, never `claimed_until`) and the reply shows the stored state; only the recovery flow (every 30 seconds, at most 3 attempts) runs a stuck made-up lead record again. This plan shows "processed once" only for the claim step and the crash scenes C and E; it does not show it for a crash between the CRM call and the claim write beyond what row NC lists.

## 11. Quoted strings and their source lines (for re-pinning in minutes)
~~~~

## Edit 28: plan line 543 (section 11 table, row M3)
Why: Row M3 names real-v5 and its line.
Status: VERIFIED (the string is present in the real-v5 file at line 258, by grep)

~~~~old
| M3 | n8n-flows-film-v5/mf-sub-crm-mail.json | `'[demo] lead ' + $('SubIn').first().json.lead_key` | (subject) |
~~~~
~~~~new
| M3 | n8n-flows-real-v5/mf-sub-crm-mail.json | `'[demo] lead ' + $('SubIn').first().json.lead_key` | 258 (subject) |
~~~~

## Edit 29: plan line 558 (after UNVERIFIED item 12)
Why: New UNVERIFIED items 13 to 16.
Status: VERIFIED (plan text); the facts inside are UNVERIFIED by definition

~~~~old
A refusal of the flag fails 1b.1 (no container) = STOP, never a pull.
~~~~
~~~~new
A refusal of the flag fails 1b.1 (no container) = STOP, never a pull.
13. The glue `fill_flows.py` and `drive.py` (take-branch files, local only, not readable in this plan's inputs; the lead verifies at re-pin): that the glue accepts the flow-set word `real`, prints `filled real 4 object`, fills the real-v5 tokens (`DESK_URL`, `DESK_TIMEOUT_MS`, `DESK_ALERT_TO`) and the placeholders only real-v5 has (`FROM_ADDRESS_PLACEHOLDER`, `INTAKE_ADDRESS_PLACEHOLDER`, `HS_CRED_PLACEHOLDER`) from `flow-values.env`, and exits non-zero while a placeholder is left. The lead edits 2.1's expected line before the run.
14. Step 2.1b: that n8n 2.46.6 imports and runs the swapped `CrmUpsert` (an HTTP Request node, version 4.2: the node type and version of the film flow's `CrmUpsert` and of `Qualify` in the same file); that the heredoc python is free of syntax errors on the laptop (it ran on Linux in scratch copies: `swap-test-negative.txt`); that `CRM_URL=http://127.0.0.1:8771` is a line of `flow-values.env` (step 1.2 of the plan lists it; not run); that `$HD` holds commit `5fdc659d1` for the recipe's `git show`; that `crm_stub.py` on the laptop answers `{"id": <whole number>}` as the scratch copy does and that `CrmIdOk` accepts it (the node's own expression was not read). The node's 10000 ms timeout is the film node's own value and is above the 8000 ms CRM hold (section 2, row `crash holds`), as it was in the film set.
15. The take's database, schema, table, login and read-only count role names for section 10b: the plan's own container uses database `postgres`, schema `app`, table `mf_leads`; DECISIONS item 10 says the take has its own database; the take's names are not read; the lead fills `TAKE_DB_NAME`, `SCHEMA`, `PGURL` and `OUT` (the paste was tested only with a scratch server, user `postgres`, database `take_db`, schema `app`). Also unverified: `COPY` and `\o` output on the take's `psql` version (tested with psql 16.15).
16. That the exported list matches the contacts really created in HubSpot: the list holds the made-up lead records sent to the flows, not what HubSpot holds; the owner checks the HubSpot contact list against it after the take.
~~~~
