# evidence-cheap-1 (raw, trimmed)
## 1 patch dry-run (copy of git HEAD tree for handover/demo in temp dir)
$ patch --dry-run -p1 -d <tmpcopy> < flowcheck/in/patches/F-001-one-ddl.patch
can't find file to patch at input line 5
Perhaps you used the wrong -p or --strip option?
The text leading up to this was:
--------------------------
|diff --git a/handover/demo/n8n-flows/mf_leads.sql b/handover/demo/n8n-flows/mf_leads.sql
|index 752c64e..33fbcc2 100644
|--- a/handover/demo/n8n-flows/mf_leads.sql
|+++ b/handover/demo/n8n-flows/mf_leads.sql
--------------------------
File to patch: 
Skip this patch? [y] 
Skipping patch.
2 out of 2 hunks ignored
rc=1
$ patch --dry-run -p1 -d <tmpcopy> < flowcheck/in/patches/F-002-take-key-check-and-claim-error-path.patch
can't find file to patch at input line 5
Perhaps you used the wrong -p or --strip option?
The text leading up to this was:
--------------------------
|diff --git a/handover/demo/n8n-mainframe/build_mainframe.py b/handover/demo/n8n-mainframe/build_mainframe.py
|index 2b59bf9..20f71ae 100644
|--- a/handover/demo/n8n-mainframe/build_mainframe.py
|+++ b/handover/demo/n8n-mainframe/build_mainframe.py
--------------------------
File to patch: 
Skip this patch? [y] 
Skipping patch.
2 out of 2 hunks ignored
rc=1
$ patch --dry-run -p1 -d <tmpcopy> < flowcheck/in/patches/F-003-runsheet-claims.patch
can't find file to patch at input line 3
Perhaps you used the wrong -p or --strip option?
The text leading up to this was:
--------------------------
|--- a/handover/demo/VIDEO-RUNSHEET.md
|+++ b/handover/demo/VIDEO-RUNSHEET.md
--------------------------
File to patch: 
Skip this patch? [y] 
Skipping patch.
5 out of 5 hunks ignored
rc=1
$ patch --dry-run -p1 -d <tmpcopy> < flowcheck/in/patches/F-004-page-statement-17.patch
can't find file to patch at input line 5
Perhaps you used the wrong -p or --strip option?
The text leading up to this was:
--------------------------
|diff --git a/handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md b/handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md
|index 103d55a..c12eadb 100644
|--- a/handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md
|+++ b/handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md
--------------------------
File to patch: 
Skip this patch? [y] 
Skipping patch.
1 out of 1 hunk ignored
rc=1
$ patch --dry-run -p1 -d <tmpcopy> < flowcheck/in/patches/F-008-save-runs-for-the-take.patch
can't find file to patch at input line 5
Perhaps you used the wrong -p or --strip option?
The text leading up to this was:
--------------------------
|diff --git a/handover/demo/n8n-mainframe/build_mainframe.py b/handover/demo/n8n-mainframe/build_mainframe.py
|index 2b59bf9..8d8a16f 100644
|--- a/handover/demo/n8n-mainframe/build_mainframe.py
|+++ b/handover/demo/n8n-mainframe/build_mainframe.py
--------------------------
File to patch: 
Skip this patch? [y] 
Skipping patch.
2 out of 2 hunks ignored
rc=1
## 2 json.load
flowcheck/in/film-v5/mf-form.json rc=0
flowcheck/in/film-v5/mf-recovery.json rc=0
flowcheck/in/film-v5/mf-hook.json rc=0
flowcheck/in/film-v5/mf-sub-crm-mail.json rc=0
flowcheck/in/real-v5/mf-form.json rc=0
flowcheck/in/real-v5/mf-recovery.json rc=0
flowcheck/in/real-v5/mf-hook.json rc=0
flowcheck/in/real-v5/mf-sub-crm-mail.json rc=0
## 3 env vars
-- real-v5
      1 $env.DESK_ALERT_TO
      1 $env.DESK_TIMEOUT_MS
      1 $env.DESK_URL
-- film-v5
      1 $env.MF_CRM_URL
      1 $env.MF_STAGE_TIMEOUT_MS
      1 $env.MF_STAGE_URL
-- all
      2 $env.DESK_ALERT_TO
      1 $env.DESK_TIMEOUT_MS
      1 $env.DESK_URL
      2 $env.MF_CRM_URL
      1 $env.MF_STAGE_TIMEOUT_MS
      1 $env.MF_STAGE_URL
## 4 names
flowcheck/in/film-v5/mf-recovery.json:196:     "name": "mf-mail-smtp"
flowcheck/in/film-v5/mf-sub-crm-mail.json:259:     "name": "mf-mail-smtp"
flowcheck/in/builder/build_mainframe.py:30:             "options": {}}, pos, credentials={"hubspotAppToken": {"id": HSID, "name": "hubspot-app-token"}}, retryOnFail=True, maxTries=TRIES, waitBetweenTr
flowcheck/in/builder/build_mainframe.py:39:             credentials={"smtp": {"id": SMTPID, "name": "mf-mail-smtp"}}, **x)
flowcheck/in/builder/mf.py:50:    c = api.call("POST", "/credentials", {"name": "mf-mail-smtp", "type": "smtp", "projectId": inst["project_id"],
flowcheck/in/real-v5/mf-recovery.json:196:     "name": "mf-mail-smtp"
flowcheck/in/real-v5/mf-sub-crm-mail.json:104:     "name": "hubspot-app-token"
flowcheck/in/real-v5/mf-sub-crm-mail.json:275:     "name": "mf-mail-smtp"
## 5 mf-form
flowcheck/in/film-v5/mf-form.json:7:    "path": "mf-form",
flowcheck/in/film-v5/mf-form.json:18:   "webhookId": "mf-form-wh"
flowcheck/in/builder/build_mainframe.py:120:              ("mf-form.json", main_flow("Lead desk main frame: form entry", "mf-form", "mf-form-wh", "submission_id
flowcheck/in/builder/mf.py:57:    for fn, nm in (("mf-form.json", "mf-form"), ("mf-hook.json", "mf-hook"), ("mf-recovery.json", "mf-recovery")): res[nm] = api.d
flowcheck/in/builder/mf.py:60:def restart_n8n(**env): return n8n_restart(paths=("mf-form", "mf-hook"), **env)
flowcheck/in/builder/mf.py:121:    for path, mk in (("mf-form", form), ("mf-hook", hook)):
flowcheck/in/builder/mf.py:125:    k = uid("rev"); st, rep = req("mf-form", form(k, email="not-an-email")); o = outcome(k); good = rep.get("verdict") == "review
flowcheck/in/builder/mf.py:134:            st, rep = req("mf-form", fbody(k))
flowcheck/in/builder/mf.py:143:        th = threading.Thread(target=lambda: req("mf-form", fbody(k))); th.start()
flowcheck/in/builder/mf.py:147:        st, rep = req("mf-form", fbody(k)); tdone = wait_final(k, t0); o = outcome(k)             # the caller sends the same req
flowcheck/in/builder/mf.py:148:        st3, rep3 = req("mf-form", fbody(k)); o["caller_resend_after_restart"] = [st, rep.get("verdict") if isinstance(rep, dict)
flowcheck/in/builder/mf.py:184:        stage_ctl(mode=mode, sleep=40); k = uid("t8-" + mode); ids.append(k); t0 = time.time(); st, rep = req("mf-form", fbody(k)
flowcheck/in/builder/mf.py:195:        k = uid("t9-" + nm); ids.append(k); b = form(k, email=f["email"], name=f["name"]); b.update({x: f[x] for x in ("to", "rec
flowcheck/in/builder/mf.py:196:    k = uid("t9-subj"); st, rep = req("mf-form", form(k + "\r\nBcc: evil@example.test", email="ok@example.test")); rec("T9", case
flowcheck/in/builder/mf.py:208:            th = threading.Thread(target=lambda: req("mf-form", fbody(k), t=120)); th.start(); t0 = time.time()
flowcheck/in/builder/mf.py:218:        k = uid("t11-%d" % (i + 1)); ids.append(k); threading.Thread(target=lambda k=k: req("mf-form", fbody(k), t=100)).start();
flowcheck/in/builder/mf.py:224:        open(MAIL + ".drop", "w").write("1"); k = uid("t12-%d" % (i + 1)); ids.append(k); st, rep = req("mf-form", fbody(k)); t0 
flowcheck/in/builder/mf.py:231:    t0 = time.time(); st, rep = req("mf-form", fbody(k)); tf = wait_final(k, t0, 150, need_alert=False); time.sleep(20); early = 
flowcheck/in/builder/mf.py:241:    t0 = time.time(); st, rep = req("mf-form", fbody(ka)); wait_final(ka, t0, 150, need_alert=False); tu = round(time.time() - t0
flowcheck/in/builder/mf.py:242:    time.sleep(40); crm_ctl(upsert_ack_delay_ms=40000); conn_a = smtp_conns(); tb0 = time.time(); stb, repb = req("mf-form", fbod
flowcheck/in/builder/mf.py:258:    t0 = time.time(); st, rep = req("mf-form", fbody(k)); tu = wait_final(k, t0, 150, need_alert=False); time.sleep(20); early = 
flowcheck/in/builder/mf.py:268:        k = uid("t15-%d" % (i + 1)); ids.append(k); t0 = time.time(); st, rep = req("mf-form", fbody(k)); tf = wait_final(k, t0, 
flowcheck/in/builder/mf.py:281:        k = uid("t7b-%d" % (i + 1)); ids.append(k); st, rep = req("mf-form", form(k, email="planted7b-%d@example.test" % i if i e
flowcheck/in/builder/mf.py:332:    dup = uid("t13dup"); ids.append(dup); out = []; th = [threading.Thread(target=lambda: out.append(req("mf-form", fbody(dup))))
flowcheck/in/builder/mf.py:335:        k = uid("t13b-%d" % (i + 1)); ids.append(k); threading.Thread(target=lambda k=k: req("mf-form", fbody(k), t=100)).start()
flowcheck/in/builder/mf.py:344:        k = uid("t17-%d" % (i + 1)); ids.append(k); t0 = time.time(); st, rep = req("mf-form", fbody(k)); tf = wait_final(k, t0, 
flowcheck/in/builder/mf.py:353:        k = uid("t18-%d" % (i + 1)); ids.append(k); t0 = time.time(); st, rep = req("mf-form", fbody(k)); tf = wait_final(k, t0, 
flowcheck/in/patches/F-003-runsheet-claims.patch:25: | 2. One lead goes in | Runs the one prepared send note (saved text, owner pastes it) that posts one made-u
flowcheck/in/patches/F-003-runsheet-claims.patch:30: | 6. Doubtful case, step 1: the lead goes in | Sends a made-up lead through the film-flows entry (LOOPBACK 
flowcheck/in/patches/F-003-runsheet-claims.patch:61: 2. The prepared send note: one lead through mf-form on the LOOPBACK address on the real flows; check reply 
flowcheck/in/patches/F-008-save-runs-for-the-take.patch:25:               ("mf-form.json", main_flow("Lead desk main frame: form entry", "mf-form", "mf-form-wh"
flowcheck/in/real-v5/mf-form.json:7:    "path": "mf-form",
flowcheck/in/real-v5/mf-form.json:18:   "webhookId": "mf-form-wh"
## 6 typeVersion / pins
      2 "typeVersion": 1.1
      8 "typeVersion": 1.2
     12 "typeVersion": 1.4
      4 "typeVersion": 2
      4 "typeVersion": 2.1
     27 "typeVersion": 2.2
     28 "typeVersion": 2.5
     20 "typeVersion": 3.4
      3 "typeVersion": 4.2
-- n8nio|image:
flowcheck/REPORT.md:22:| real validity (does n8n import and run it) | prove the patch works | rung 3: n8n itself in a throw-away container (owner rule 5b allows it) | `docker info` and `docker pull n8
## 7 table rows
drift/REPORT.md 190-221: 32
plan 464-486: 22
## 8 other cloud branches
branches: cloud/core-hardening cloud/flows-audit (cloud/system-map = this one, skipped)
### core-hardening files found: STATUS-BOARD paths below
$ git show origin/cloud/core-hardening:handover/core-hardening/STATUS-BOARD.md | head -30
UPDATED_UTC: 2026-11-16T09:58:00Z
SESSION: core-hardening
ORDER: 021
STATE: WORKING
BOOT_ID: 3dcae981
ITEMS_TOTAL: 13
ITEMS_OPEN: 8
PERCENT: 84
AGENTS_RUNNING: 8
CAPACITY: load 0.7 of 4 cores (18%; agents are model-bound, ORDER 021 count is the lever), mem 0 of 15 GB used (3 GB cache), disk 20 GB free, 8 light + 0 heavy agents (C5 v3 suite run pending)
INTERRUPTED: none
FAILED: C5 v2 NOT READY (blocker: route refusals dropped in pilot/prod) -> C5 v3 running. C4b v7 security review: 1 blocker (backstop above the written yes) + 9 majors; naive 7 majors -> v8 building. run.py review: 6 majors (absolute path, symlink, guard fails open, leftover exit code, SIGINT rc, no except-widening mutants) -> fix pass running. C6b: lane3 run fl45k3b voided with no reason, "killed
NEXT: C5 v3 then 2 reviewers then C7b/C8c on v3; C3b v3 reviewers; C4b v8 then fresh naive reader; run.py fixes then reviewer; C6b reviewer then fold into C6; C9 blocked on APPLIED-S9.md
PUSHED_UTC: 2026-11-16T09:58:00Z

## ITEMS (QUEUE.md ids; detail in REPORT.md)
| # | item | state | % | evidence file | note |
|---|---|---|---|---|---|
| C1 | cross-review flows-audit | done | 100 | reviews-of-flows-audit/REVIEW.md | |
| C2 | hygiene patches | done | 100 | hygiene-patches/ | static |
| C3 | paste check of re-smoke plan | done | 100 | paste-check/REPORT.md | nothing run with pwsh or n8n |
| C3b | re-pin patch (ORDER 017) | v3 built, reviewing | 85 | paste-check/REPORT-repin-v3.md | 7 LEAD-FILL questions; 2 reviewers running |
| C4 | steps vs decisions edits | done | 100 | steps-edits/EDITS.md | |
| C4b | OWNER-STEPS | v8 building | 85 | steps-edits/review-c4b-v7-*.md | v7 reviewed twice; v8 fixing blocker + majors |
| C5 | polish ready patches | v3 building | 60 | patches-ready/review/ | v2 blocker fixed in v3 |
| C6 | R460 audit of 7 skipped findings | done; C6b reviewing | 100 | c6-skip-audit/REPORT-c6b.md | lane3 raw found; 1 reviewer running |
| C7 | heavy lane: tests per patch | evidence done, reviewing | 90 | patch-test-runs/REPORT.md | v1 patches only; v2 to rerun |
| C8 | mutation lane C-01 A-01 | run.py fix pass | 90 | mutation-lane/REPORT.md | 20+27 mutants, 19 survivors with proof tests; rerun on v2 later |
| C9 | apply system-map S9-1..S9-5 into owner steps | blocked | 0 | - | APPLIED-S9.md not on origin/cloud/system-map yet |
| C10 | who-types-what table | in v7, reviewed | 85 | steps-edits/OWNER-STEPS-realrun-v7.md | naive round 2 done; gaps listed |
### flows-audit files found: STATUS-BOARD paths below
$ git show origin/cloud/flows-audit:handover/flows-audit/STATUS-BOARD.md | head -30
UPDATED_UTC: 2026-11-16T09:52:53Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 7
PERCENT: 85
AGENTS_RUNNING: 5
CAPACITY: 0.43 load of 4 cores, mem 0/15 GB, disk free 28G, agents 5 (light+heavy per list)
INTERRUPTED: none
FAILED: F8: $env nodes, 2 webhooks without auth, 7 false-pass Majors (fixer running)
F3: rerun clean earlier; fresh security review r2 found no Blocker but 12 real Minor/Nit (nested-template lexer, delete recovery dead end, delete not idempotent, missing-value copy written); r5 fixer running; 3.9/3.10, macOS, live import not run
ROLES: v4 doc has a security Blocker (Part C unguarded, can lock out the administrator) + 8 Majors, marked in file, NOT fixed (parked pending Q11); script r5 fixer says lint gate passes, 64 tests, independent rerun running; split-string SQL in Code nodes still only caught if text names mf_leads
claims: reviews found 16 Majors (swapped rows 13/18 cites, wrong OWNER-STEPS line, "lead" word, undefined labels, 114 SUPPORTED includes rows needing a run); r4 fixer running; F-01 still unreadable
F5: round 4 reviews found 4 Blockers + about 20 Majors incl. false "not in this checkout" reason (programs ARE in handover/demo); r4 fixer running
NEXT: collect F8, F3 r5, F5 r4, claims r4, ROLES script evidence; coordinator answers Q11
PUSHED_UTC: 2026-11-16T09:52:53Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| F1 | claims table | running | 95 | CLAIMS-TABLE.md | round 2 applied; checker + reader running; citation fixes running |
| F2 | core patches cross-review | done | 100 | reviews-of-core-patches/REVIEW.md | 6 Majors, apply after fixes |
| F3 | fill_flows tool | running | 95 | fill_flows/ | round 2 fixed (68 tests); delta evidence running |
| F4 | patch apply check | done | 100 | patch-apply/REPORT.md | F-002 needs T19 on the laptop |
| F5 | run-sheet wording | running | 85 | RUNSHEET-WORDING.md | final fixer running |
| F6 | idle fallback + recovery audit | done | 100 | F6-AUDIT.md, F6B-AUDIT.md | n8n facts unverified; F6b SQL untested |
| F7 | facts already done | done | 100 | inputs/FACTS-ALREADY-DONE.md | applied |
| F8 | stronger JSON flow checker | running | 88 | flow-check/ | 3 reviews in; fixer running |
