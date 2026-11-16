# M16 flow-set question: which n8n flow set does each scene of the one video need? (16 Nov 2026, about 10:55 UTC / 16:25 IST)
Made-up data only. Read-only research from the files this session holds; one reviewer pair still to run (round 1 below).

## FAILED / NOT FOUND first
- No source I hold gives a manual switch procedure between the two flow sets: no `scripts/n8n_api.py` command line, no who-runs-it, no time. `scripts/n8n_api.py` is not in this checkout (it is only named in handover/demo/skips/* and handover/demo/coverage/PLAN.md:147), and `WP6-RUNBOOK.md` (cited by inputs/OWNER-STEPS-realrun-v3.md:5 and :87) is not in this checkout, so its line 16 could not be read. The flow JSON folders (real-v5, film-v5) exist only on origin/cloud/flows-audit and origin/demo/handover, not here (flowcheck/REPORT.md:12).
- The run sheet itself (handover/demo/VIDEO-RUNSHEET.md) is not here either; only the patch flowcheck/in/patches/F-003-runsheet-claims.patch is, so the scene list below is from that patch.
- Scene 5 is ambiguous: the patch says scene 5 "uses a stand-in CRM" (patch:8, :29) but still asks "Scene 5 on the stand-in CRM or cut (risk 7)?" (patch:66-67) as an open question for the owner.

## Scene list (from F-003 patch)
| scenes | what | flow set it needs | source |
|---|---|---|---|
| 1 to 4 | real mail and real CRM service, made-up people only (scene 2 posts through path mf-form on the loopback address) | real-v5 (HubSpot step is `n8n-nodes-base.hubspot`) | patch:8, :25; flowcheck/third-read.md:12 |
| 5 | stand-in CRM that refuses every call | film-v5 by inference (film-v5 CRM step is an HTTP call to `$env.MF_CRM_URL/upsert`); no file says "scene 5 = film-v5" in words | patch:8, :29; third-read.md:12 |
| 6 to 10 | doubtful-case scene on stand-ins (mail and CRM) through the film-flows entry; label "test scene on stand-ins"; scene 8 may be cut; scene 10 "UNBACKED, fallback" | film-v5 (stated: "through the film-flows entry") | patch:9, :30, :34-35, :43, :62 |
| 11 | optional, fault on the stand-in; audit recommends cut | film-v5 | patch:36, :66 |
| 12 | no flow | none | patch:41-42 |
Core scenes are 1 to 10 and 12 (380 s with scene 11) per patch:41-42.

## Answer
1. The ONE video, as the run sheet is worded, contains BOTH flow sets: real-v5 for scenes 1 to 4 and film-v5 for scenes 6 to 10 (and scene 5, and 11 if kept). "film-v5 not in this video" is NOT supported by any file. Two other files name both sets for the video take: inputs/DECISION-one-store.md:7 and MASTER-MAP.md:9, :187.
2. The owner's steps (v5) cover only the real take (3 made-up people, v5:10) and contain NO switch step; the lead does the n8n import (v5:5). So who switches, how, and how long is OPEN.
3. Differences that matter (flowcheck/REPORT.md:53, :151-152): real-v5 reads DESK_URL, DESK_TIMEOUT_MS, DESK_ALERT_TO; film-v5 reads MF_STAGE_URL, MF_STAGE_TIMEOUT_MS, MF_CRM_URL; the `hubspot-app-token` credential on the CRM step is real-v5 only. The take-time literal substitution into a local flow copy is "not yet built" (AGENT-SCOPE:23, BL-wp6-G1).

## What the studio lead must decide (nothing here can be decided by this session)
- A. Is scene 5 on the stand-in CRM or cut (the open owner question patch:66-67)? If cut, real-v5 for scenes 1 to 4 and film-v5 for 6 to 10 only.
- B. How film-v5 is activated and real-v5 deactivated between scene 4 and the next scene (or two separate n8n runs, one per flow set, which would avoid a live switch): command, who types it, expected seconds. The rehearsal should time it. Until then the video's flow-set plan is untested.
- C. Take order: filming the stand-in scenes in a separate session from the real take keeps real credentials out of the film-v5 set (least privilege), at the cost of editing two takes together. Suggested, not decided.
Not checked: the actual flow JSON; any n8n API command; how long a switch takes.
