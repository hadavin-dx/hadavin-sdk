# Edit list: plan-wp6-resmoke-v5.md -> real-v5 (TEXT FOR THE LEAD; the plan itself is NOT edited)

Written 2026-11-16 (UTC and IST: see the checkpoint file). Source plan: `handover/core-hardening/inputs/plan-wp6-resmoke-v5.md` (558 lines as read). Every `old` text below was machine-checked to occur exactly once in that file at the line given; apply with an exact-match replace. Edits are listed in plan order. A tag line under each edit says VERIFIED (read) or UNVERIFIED (what the lead must check).

**Fact base read for this list (git, read only):** `origin/cloud/flows-audit:handover/demo/n8n-flows-real-v5/` (4 flow files, `V5-README.md`, `V5-NODE-DIFF.txt`) and the same folder at demo sha `5fdc659d1` (identical, `git diff` empty). Real-v5 against the film flow set: `mf-form.json` and `mf-hook.json` are byte-identical (`cmp`); `mf-recovery.json` differs only in the two alert-mail address strings; `mf-sub-crm-mail.json` differs in `Qualify` (`$env.DESK_URL`, `$env.DESK_TIMEOUT_MS` against `MF_STAGE_*`), the two mail address strings and the `CrmUpsert` node (HubSpot node with a credential against a plain HTTP call to the loopback CRM stand-in). That single node is the only reason 2.1b exists.

## R1 (plan line 4)
Why: Header must say which flows run.
Status: VERIFIED (plan text only)

```diff
- Status: v5 FINAL EDIT 2026-11-16 after plan-review round 3 of 3 (no further plan-review round).
+ Status: v5 FINAL EDIT 2026-11-16 after plan-review round 3 of 3 (no further plan-review round). REAL-V5 EDIT 2026-11-16 (lead answer Q15.1; DECISIONS-2026-11-16 item 1: the ONE video is real-v5 only): the flow set filled, imported and driven here is real-v5, with ONE node swapped for the loopback stand-in (step 2.1b); the earlier film flow set is not run (LATER VIDEO). Every change is in "CHANGES FROM v5 (real-v5 edit)".
```

## R2 (plan line 8)
Why: New section header and table at the top of the changes.
Status: VERIFIED (plan text); INSERT before line 8, replacing nothing

Action: INSERT the block below immediately BEFORE the heading line (so the heading stays). In diff form:

```diff
- ## CHANGES FROM v4 (every round-3 finding and lead ruling, and the step that fixes it)
+ ## CHANGES FROM v5 (real-v5 edit, 2026-11-16; lead answer Q15.1, Q15.2, Q15.3)
+ | id | finding | fixed in / verdict |
+ |---|---|---|
+ | Q15.1 | step 2.1 filled the film flow set; cases A, B, B2 ran on it | 2.1 fills `n8n-flows-real-v5`; P-2 archives it; 2.1b swaps only `CrmUpsert` for the loopback stand-in (the HubSpot node would leave loopback); every film reference removed or marked LATER VIDEO (R3-R8, R10, R18) |
+ | verifier 2 | plan:493 listed "real-v5 at run time" without saying what runs | section 9 now says: real-v5 runs minus one node; the HubSpot node, its credential and its real answer are not exercised (R16) |
+ | verifier 4 | "processed once" overreaches | claim wording limited to the claim step and scenes C and E, lease-expiry sentence added (R17) |
+ | Q15.2 | no clean start before the take | row CS in section 7 (R15) and the lead step in section 10 (R17) |
+ | static pass 6 | empty or missing lead id untested | named in section 9 as not proven (R16) |
+ | not changed | A, B, B2 pass rules; the Claim node is byte-identical in real-v5 and the film set (cmp, 2026-11-16) | so the claim-path result carries over; only the CRM call differs |
+ 
+ ## CHANGES FROM v4 (every round-3 finding and lead ruling, and the step that fixes it)
```

## R3 (plan line 120)
Why: Section 2 `code` row, source of the flow files.
Status: VERIFIED that real-v5 exists at 5fdc659d1 (git ls-tree in this repo, 6 files; identical to origin/cloud/flows-audit by git diff, empty). UNVERIFIED that the laptop worktree `$HD` has it: run `git -C $HD ls-tree --name-only 5fdc659d1 handover/demo/n8n-flows-real-v5/`.

```diff
- `$R/demo` = `git archive` of handover-demo `5fdc659d1` (film-v5, n8n-mainframe, n8n-tests only)
+ `$R/demo` = `git archive` of handover-demo `5fdc659d1` (real-v5, n8n-mainframe, n8n-tests only; the film flow folder is not archived: LATER VIDEO)
```

## R4 (plan line 126)
Why: The word film names the flow set; the ids themselves are the glue's. 2.4, 2.5 and 2.6 use these ids and must still match.
Status: UNVERIFIED (ids are given by the glue `fill_flows.py`; real-v5 files carry no workflow id: json `id` is null in all four)

```diff
- | ids | film `smkForm000000001`,
+ | ids | flows (real-v5) `smkForm000000001`,
```

## R5 (plan line 223)
Why: Records that the glue is now called with `real`.
Status: UNVERIFIED (glue not on this branch)

```diff
- `fill_flows.py` (flows Postgres credential = `smk_app` with `pg-app.pw`)
+ `fill_flows.py` (flows Postgres credential = `smk_app` with `pg-app.pw`; run in 2.1 with the flow-set word `real`, UNVERIFIED 13)
```

## R6 (plan line 236)
Why: P-2 archive command (line 236): the demo tar must hold real-v5, else 2.1 has no folder.
Status: VERIFIED path exists at 5fdc659d1 (see R3)

```diff
- handover/demo/n8n-mainframe handover/demo/n8n-tests handover/demo/n8n-flows-film-v5;
+ handover/demo/n8n-mainframe handover/demo/n8n-tests handover/demo/n8n-flows-real-v5;
```

## R7 (plan line 284)
Why: The least-privilege grant list of `smk_app` (1b.2) was justified against film-v5; it now stands on real-v5.
Status: VERIFIED by reading all `query` fields of the four real-v5 files (verbs found: INSERT INTO, UPDATE, SELECT; tables: `mf_leads` only; `gen_random_uuid()` needs PostgreSQL 13 or later, the image is 16)

```diff
- (film-v5: no DELETE, CREATE, TRUNCATE)
+ (real-v5: the four flow files hold only INSERT INTO, UPDATE and SELECT on `mf_leads`, with `FOR UPDATE SKIP LOCKED` inside the recovery claims; no DELETE, CREATE, TRUNCATE, DROP or ALTER; drafter read 2026-11-16 at 5fdc659d1)
```

## R8 (plan line 298)
Why: Step 2.1 (line 298) now fills real-v5; 2.1b is the one loopback-only swap, without which the run would leave loopback.
Status: UNVERIFIED (the glue's accepted word, its output line, its handling of HS_CRED_PLACEHOLDER / FROM_ADDRESS_PLACEHOLDER / INTAKE_ADDRESS_PLACEHOLDER; the swap code is unrun). VERIFIED by reading: `CrmUpsert` is `n8n-nodes-base.hubspot` typeVersion 2.2 at `mf-sub-crm-mail.json:94-95` (real-v5), the replaced fields are the only ones that differ from the film node (diff of the two files, 2026-11-16); `crm_stub.py` `/upsert` answers `{id, created}`; `CrmIdOk` regex is `^[0-9]+$` (`mf-sub-crm-mail.json:159`).

```diff
- python3 -I $R/fill_flows.py $R/demo/handover/demo/n8n-flows-film-v5 $T/flows $T film object; sed "s#@@TAKE@@#$T#g" $W/egm/duplicate-proof-lead-desk/wp6/probe-smoke.json > $T/probe.json` -> `filled film 4 object`.
+ python3 -I $R/fill_flows.py $R/demo/handover/demo/n8n-flows-real-v5 $T/flows $T real object; sed "s#@@TAKE@@#$T#g" $W/egm/duplicate-proof-lead-desk/wp6/probe-smoke.json > $T/probe.json` -> `filled real 4 object` (UNVERIFIED 13: the glue's word for the real set; the lead reads the glue before the run and edits this expected line, the runner never adapts it). Any other output, or a non-zero exit, = STOP.
+ - **2.1b** (NEW; derived copy, `pastes/2.1b.sh`; runs BEFORE 2.2 and before any import). Why: real-v5's `CrmUpsert` is n8n's HubSpot node, which calls the HubSpot web address on the internet; this run is loopback only, US$0, with no real HubSpot (section 0, owner's smoke yes). So exactly ONE node of the filled copy is swapped for the loopback CRM stand-in (`crm_stub.py`, port 8771); every other node, every connection and the Claim step stay real-v5's own. Paste (the heredoc is part of the paste file):
+ ```sh
+ . $HOME/hadavin-smoke/env.sh; CRM=$(grep '^CRM_URL=' $T/flow-values.env | cut -d= -f2-); F=$T/flows/mf-sub-crm-mail.json; echo "before $(sha256sum $F | cut -c1-12)"
+ python3 -I - "$F" "$CRM" <<'PYEOF'
+ import json, sys
+ p, crm = sys.argv[1], sys.argv[2]
+ d = json.load(open(p)); w = d[0] if isinstance(d, list) else d
+ n = [x for x in w["nodes"] if x["name"] == "CrmUpsert"]
+ assert len(n) == 1 and n[0]["type"] == "n8n-nodes-base.hubspot", "CrmUpsert is not the HubSpot node: STOP"
+ n = n[0]; n["type"] = "n8n-nodes-base.httpRequest"; n["typeVersion"] = 4.2; n.pop("credentials", None)
+ n["parameters"] = {"method": "POST", "url": crm + "/upsert", "sendBody": True, "contentType": "json", "specifyBody": "json", "jsonBody": "={{ { hadavin_lead_id: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email, label: $('Qualify').first().json.label } }}", "options": {"timeout": 10000}}
+ json.dump(d, open(p, "w"))
+ print("CrmUpsert swapped to the loopback stand-in")
+ PYEOF
+ echo "after $(sha256sum $F | cut -c1-12)"; grep -c 'n8n-nodes-base.hubspot' $T/flows/*.json; grep -c 'hubapi' $T/flows/*.json
+ ```
+   -> `CrmUpsert swapped to the loopback stand-in`; the two hash lines differ; every count `0` (all four files, both greps). An assertion text, a traceback, a hash that did not change or any count above 0 = STOP (the HubSpot node must never reach n8n in this run: it would try the internet). `retryOnFail`, `maxTries`, `waitBetweenTries` and `onError` stay as real-v5 has them (only `type`, `typeVersion`, `credentials` and `parameters` change); the new `parameters` are the loopback stand-in's call (`POST <CRM_URL>/upsert`, body keys `hadavin_lead_id`, `email`, `label`), the same call `crm_stub.py` serves at `/upsert`; its answer `{id, created}` carries a number, so `CrmIdOk` (digits only) passes. The imported but now unused HubSpot credential (`smkHs00000000001`, 2.3, 2.5) stays: the credential count of 3 is unchanged. UNVERIFIED 14 (heredoc python is not syntax-checked by `bash -n`; UNVERIFIED 2 already says so for every paste's python).
```

## R10 (plan line 302)
Why: Line 302, 2.5 expected text.
Status: UNVERIFIED (depends on the glue ids)

```diff
- 6 workflow ids (4 `smk` film, `smkProbe00000001`, `smkExec000000001`)
+ 6 workflow ids (4 `smk` real-v5 flows, `smkProbe00000001`, `smkExec000000001`)
```

## R11 (plan line 341)
Why: Line 341, the same-id-twice cases (A, B) and B2 (9.4, 11.1) now name the flow set they test.
Status: VERIFIED by reading (`mf-form.json:97`, 2026-11-16)

```diff
- B: 10 replies, every one with a verdict, at most 1 with repeat false (STOP otherwise: the headline claim);
+ B: 10 replies, every one with a verdict, at most 1 with repeat false (STOP otherwise: the headline claim; A, B and B2 run on the real-v5 flows with only `CrmUpsert` swapped, 2.1b; the step that decides `repeat` is real-v5's own `Claim` node, `mf-form.json:97`, `INSERT ... ON CONFLICT (lead_key) DO NOTHING`);
```

## R12 (plan line 464)
Why: Row CS is added.
Status: VERIFIED (plan text)

```diff
- ## 7. PASS/FAIL table to fill in `evidence-2\INDEX.md` (20 rows)
+ ## 7. PASS/FAIL table to fill in `evidence-2\INDEX.md` (21 rows)
```

## R13 (plan line 473)
Why: Row B1 (line 473) must not read as a test of the HubSpot node.
Status: VERIFIED (plan text)

```diff
- | B1 | same-id burst on the new stack: <= 1 first-time verdict; B2 killed in flight ends final |
+ | B1 | same-id burst on the new stack, on the real-v5 flows with `CrmUpsert` swapped (2.1b): <= 1 first-time verdict; B2 killed in flight ends final |
```

## R14 (plan line 477)
Why: Row NC (line 477).
Status: VERIFIED (plan text)

```diff
- Exercised: "CRM row written, ack not returned" (C) and "mail stored, ack not returned" (E) | statement |
+ Exercised: "CRM row written, ack not returned" (C) and "mail stored, ack not returned" (E); NOT exercised: the real-v5 HubSpot node itself (swapped at 2.1b), its credential and its real answer | statement |
```

## R15 (plan line 486)
Why: NEW row CS = the clean-start row (lead answer Q15.2). Section 7 grows from 20 to 21 rows (R12).
Status: VERIFIED (plan text); the claim that `T0 rows {}` proves emptiness here rests on 3.4 reading `mf_leads` through `smk_count` (as the plan already says).

```diff
- | Z1 | clean-up: no pid, container, port, `$R`; Docker names equal baseline; owner's 5678/5679 listeners and pids unchanged; no marker in `evidence-2\`; keep-alive gone (listed, never killed) | STOP | P-1, P-4, S13 | all empty / equal / unchanged; scan lists nothing; `keepalive-gone` | | |
+ | Z1 | clean-up: no pid, container, port, `$R`; Docker names equal baseline; owner's 5678/5679 listeners and pids unchanged; no marker in `evidence-2\`; keep-alive gone (listed, never killed) | STOP | P-1, P-4, S13 | all empty / equal / unchanged; scan lists nothing; `keepalive-gone` | | |
+ | CS | clean start: the table of lead records is empty before the first send of this run (here: a brand-new container, so `T0 rows {}` is the proof), and this run's lead ids are made up and used once. For the TAKE the same row is a lead step (section 10, "Clean start before the take") | STOP (here) / lead step (take) | 1b.2, 3.4 (here); section 10 (take) | `T0 rows {}`; `keys.txt` ids all new | | |
```

## R19 (plan line 489)
Why: Section 8 MUST-NOT (line 489).
Status: VERIFIED (plan text)

```diff
- no grant, role or database beyond 1b.2;
+ no grant, role or database beyond 1b.2; the real-v5 HubSpot node never runs (2.1b swaps it before any import, and its counts of 0 are checked);
```

## R16 (plan line 493)
Why: Line 493, section 9 (verifier: plan:493 already says real-v5 is not proven at run time; this makes the exact gap and what is proven explicit).
Status: VERIFIED by reading `mf-form.json:27` and the plan's 1b.2 table (`lead_key text PRIMARY KEY`); the reply for a missing id is UNVERIFIED (nothing run).

```diff
- Real HubSpot (O1, O2), real Gmail SMTP/IMAP (O3-O5), a real model call and ledger (O9), real-v5 at run time; the take's own `N8N_HEALTH_URL` value (only grepped in 0.1).
+ Real HubSpot (O1, O2), including the real-v5 `CrmUpsert` HubSpot node itself: it is swapped for the loopback stand-in at 2.1b, so its credential, its real answer (`id` or `vid`) and the `CrmIdOk` digits rule on a real answer are NOT exercised (a non-numeric real id would fail the lead: `V5-README.md`, GO-1 update); real Gmail SMTP/IMAP (O3-O5), a real model call and ledger (O9); the take's own `N8N_HEALTH_URL` value (only grepped in 0.1). The real-v5 flows DO run here, minus that one node: same-id-twice (A, B, B2), the in-flight crashes (C, E) and the restarts are tested on the real-v5 claim, recovery and mail nodes. Not proven by this run: an empty or missing lead id (`mf-form.json:27` copies `body.submission_id` unchecked; the table key is not null, so a missing id is an insert error whose reply the caller sees is untested).
```

## R17 (plan line 505)
Why: Section 10 (line 505): the clean-start lead step and the lease sentence.
Status: VERIFIED by reading `mf-form.json:97` (`ON CONFLICT (lead_key) DO NOTHING`, 45 s interval) and `mf-recovery.json:26` and its schedule node (`secondsInterval` 30, line 10); `attempts < 3`, `claimed_until < now()`; the take's real database, schema and table names are UNVERIFIED.

```diff
- Only a DM PASS lets the claim cover that window.
+ Only a DM PASS lets the claim cover that window.
+ **Clean start before the take (row CS; lead step, named owner: the lead; lead answer Q15.2).** This run proves a clean start only inside its own throwaway container. For the rehearsal database and the take: (1) the take uses lead ids made up for it and never sent in any rehearsal (the lead checks them against the rehearsal's list of sent ids, `keys.txt` style, and picks new ones if one is found); (2) the lead empties `mf_leads` in the rehearsal database before the take, as the database owner or superuser, because the app role cannot delete or truncate (N4, N9 here): `TRUNCATE <schema>.mf_leads` (schema and database names as the take's database has them, UNVERIFIED 15); (3) the lead reads the row count back through the read-only count role and writes it down: `0` before the first send, or the take does not start. One numbered row with this wording goes into the owner and lead steps (version 4 and later), owner of the step: the lead.
+ **Claim wording the plan supports (lead answer Q15.3).** "A lead sent twice with the same id inside the lease (45 seconds in real-v5) is processed once." Honest limit, in the claim text: after the lease has run out, a second send is still stopped by the stored row (the insert checks only the lead id, never `claimed_until`; `mf-form.json:97`) and the reply shows the stored state; only the recovery flow (every 30 seconds, at most 3 attempts, `mf-recovery.json:26`) runs a stuck lead again. "Processed once" is shown by this plan only for the claim step and the crash scenes C and E; it is not shown for a crash between the CRM call and the claim write beyond what row NC lists.
```

## R18 (plan line 543)
Why: Part B row M3 (line 543).
Status: VERIFIED (string present in real-v5 at line 258 of the stored file, by grep)

```diff
- | M3 | n8n-flows-film-v5/mf-sub-crm-mail.json | `'[demo] lead ' + $('SubIn').first().json.lead_key` | (subject) |
+ | M3 | n8n-flows-real-v5/mf-sub-crm-mail.json | `'[demo] lead ' + $('SubIn').first().json.lead_key` | 258 (subject) |
```

## R20 (plan line 558)
Why: New UNVERIFIED items 13 to 15 (line 558 is item 12).
Status: VERIFIED (plan text); the facts inside are UNVERIFIED by definition

```diff
- 12. That the installed Docker CLI accepts `docker run --pull=never` (flag present since Docker 20.10; not run here). A refusal of the flag fails 1b.1 (no container) = STOP, never a pull.
+ 12. That the installed Docker CLI accepts `docker run --pull=never` (flag present since Docker 20.10; not run here). A refusal of the flag fails 1b.1 (no container) = STOP, never a pull.
+ 13. The glue `fill_flows.py` in `wp6-smoke` (not on this branch): that it accepts the flow-set word `real`, prints `filled real 4 object`, fills the real-v5 tokens (`DESK_URL`, `DESK_TIMEOUT_MS`, `DESK_ALERT_TO`) and the placeholders that only real-v5 has (`FROM_ADDRESS_PLACEHOLDER`, `INTAKE_ADDRESS_PLACEHOLDER`, `HS_CRED_PLACEHOLDER`) from `flow-values.env`, and still exits 0 (the repo's own tool exits 3 while a placeholder is left). The lead reads the glue and edits 2.1's expected line before the run.
+ 14. 2.1b: that n8n 2.46.6 imports and runs the swapped `CrmUpsert` (an HTTP Request node, version 4.2, the same node type and version as `Qualify` in the same file), and that the heredoc python is free of syntax errors.
+ 15. The take's database, schema and table names for the clean-start step (section 10): the plan's own container uses database `postgres`, schema `app`, table `mf_leads`; `DECISIONS-2026-11-16` item 10 says the take has its own database; the names are not read.
```

