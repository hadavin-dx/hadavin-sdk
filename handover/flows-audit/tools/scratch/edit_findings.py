import re
p='FINDINGS.md'
s=open(p).read()
lines=s.split('\n')
rows={}
order=[]
for i,l in enumerate(lines):
    m=re.match(r'\| (F-\d+) \|',l)
    if m: rows[m.group(1)]=l; order.append(m.group(1))
def rep(fid,old,new):
    l=rows[fid]
    assert l.count(old)==1,(fid,old[:50],l.count(old))
    rows[fid]=l.replace(old,new)
# F-001
rep('F-001','n8n-flows-v3 and -v4 copies (byte-identical, checked with cmp) have them, the v5 folders ship no SQL, mf.py holds a fourth inline copy.','n8n-flows-v3 and -v4 copies (byte-identical, checked with cmp by the lead) have them, the v5 folders ship no SQL, mf.py holds a fourth inline copy. The n8n-table-screen READMEs point a reader at "DDL in n8n-flows-v4".')
rep('F-001','Patch F-001-one-ddl.patch (n8n-flows/mf_leads.sql becomes the v4 text, applies cleanly).','Patch F-001-one-ddl.patch (n8n-flows/mf_leads.sql becomes the v4 text, names the v5 flows, adds the ALTER lines for an existing table; applies cleanly). ORDER: apply this BEFORE the v3 and v4 folders are archived (CUT-LIST.md).')
# F-002
rep('F-002','a failed Postgres write loses the lead without an answer.**','a failed Postgres write answers the sender with a bare 500.**')
rep('F-002','Claim has no onError and no retry; the INSERT is the only place the lead is kept','Claim has no onError and no retry, so n8n answers a failed write with its default 500 and no reason; the INSERT is the only place the lead is kept')
rep('F-002','Patch F-002-take-key-check-and-claim-error-path.patch against build_mainframe.py: new IF KeyOk (empty key -> reply 422 rejected), Claim onError continueErrorOutput -> reply 503 not_stored. Lead evidence: patched generator rebuilt into tools/scratch, diff vs saved real-v5 shows only the 3 new nodes, the Claim onError and 5 edges, no dangling edge.','Patch F-002-take-key-check-and-claim-error-path.patch against build_mainframe.py: Valid trims the key, new IF KeyOk (empty key -> reply 422 rejected), Claim onError continueErrorOutput -> reply 503 with verdict "retry" ("store not confirmed; resend with the same lead_key is safe": the write may have succeeded before the error, and the INSERT is idempotent). Sender contract (written in the patch): 422 = never retry, 503 = retry with the same key. Rebuild check (lead, re-run after the review fixes; independent re-run in evidence-2.md): diff vs saved real-v5 shows only 3 new nodes (KeyOk, ReplyBadKey, ReplyStoreFail), Valid and Claim changed, no dangling edge, mf-recovery and mf-sub-crm-mail unchanged. No test exists for the new 422 and 503 replies: add T1 (empty key) and a Postgres-down case on the laptop.')
# F-003
rep('F-003','Patch F-003-runsheet-claims.patch (exact corrected sentences, applies cleanly). The 60.1 to 61.9 s and 18-run numbers are relayed (V7-NUMBERS-lead-read.md) and stay UNVERIFIED until the lane3 raw file is in the repo.','Patch F-003-runsheet-claims.patch (exact corrected sentences, applies cleanly). After the review it also fixes every line that said the opposite (scene 4 number and do-not-say cells, lease bullet, recovery-wording bullet, time-box line, risk 2, open question 5, the line that put the real CRM in scenes 1 to 5) and marks the scene 4 caption "relayed from the lane3 test, not seen by us". The 60.1 to 61.9 s and 18-run numbers are relayed (V7-NUMBERS-lead-read.md) and stay UNVERIFIED until the lane3 raw file is in the repo.')
# F-004
rep('F-004','Patch F-004-page-statement-17.patch.','Patch F-004-page-statement-17.patch (after the review it also rewrites the Tag, Test and Raw lines of statement 17 and the "Honest limits" line, so the file no longer says "45 s: NOT RUN" or "nothing measured").')
# F-006
rep('F-006','handover/demo/VIDEO-RUNSHEET.md:4, :12, :34;','handover/demo/VIDEO-RUNSHEET.md:4 (scenes 1 to 5), :11 (scenes 1 to 4), :12 (scene 5 on a stand-in), :34;')
rep('F-006','Say on the sheet which flow set each scene uses, and drop "real CRM in scenes 1 to 5".','The sheet contradicts itself: line 4 says scenes 1 to 5, line 11 says 1 to 4. Patch F-003 now sets line 4 to scenes 1 to 4 plus the stand-in note. Say on the sheet which flow set each scene uses.')
# F-007
rep('F-007','n8n-mainframe/mf.py:153, :159','n8n-mainframe/mf.py:153, :158, :159, :164 (def k3b/k3 and the kill_case lines that carry the descriptions)')
# F-008
rep('F-008','**No error workflow and no saved runs (saveData none) in all flows; six recovery nodes swallow database errors.**','**No error workflow and no saved runs (saveData none) in all flows; six recovery nodes swallow errors (five database nodes and RunSub).**')
rep('F-008','n8n-flows-real-v5/mf-recovery.json:ClaimStuck, MarkFailed,','n8n-flows-real-v5/mf-recovery.json:ClaimStuck, RunSub, MarkFailed,')
# F-012
rep('F-012','**Recovery: one 45 s lease for up to 5 leads processed one after another; worst path before the mail claim is about 42 s.**','**Recovery: one 45 s lease for up to 5 leads processed one after another; later leads can lose attempts without being tried.**')
rep('F-012','the lease is never renewed.','the lease is never renewed. The "about 42 s" worst path (two Qualify tries and two CrmUpsert tries at 10 s plus 1 s pauses) holds only for the film flows: in real-v5 CrmUpsert is the HubSpot node, which has a retry but no timeout option (build_mainframe.py:27), so the real worst case is not bounded at 42 s. Kept at Major, not Blocker, because RunSub runs one lead at a time and the batch is usually one lead; a lead that burns its third attempt goes to failed or unknown and alerts, it is not silently lost.')
rep('F-012','Proposed (not patched, needs T-test run in n8n): claim one row per sweep, or renew the lease before each stage.','Proposed (not patched, needs T-test run in n8n): LIMIT 1 in ClaimStuck (the sweep runs every 30 s), or renew the lease before each stage; add a timeout to the real CRM step if HubSpot allows one.')
# F-014
rep('F-014','AlertMark onError continue means a lead can be alerted again every sweep.','AlertMark onError continue means that if the mark fails alert_sent stays false and the lead is alerted again once the 720 s claim window ends (about every 12 minutes; after a failed send the backoff is 60 s times the attempt count, at most 5 times). It is not "every sweep". If DESK_ALERT_TO is not set the send fails the same way and the loop has no cap.')
# F-018
rep('F-018','SMTP and stage timeouts.**','SMTP and stage timeouts, and whether DESK_ALERT_TO is set (AlertSend reads it only from the environment, so a missing value fails every alert).**')
rep('F-018','third party (n8n runtime) / lead runs the laptop tests.','third party (n8n runtime) / lead runs the laptop tests. Add a take-day check that DESK_ALERT_TO and the other variables are set before the first lead (see F-029).')
# F-019
rep('F-019','(13 rows, 10 two-store problems)','(14 rows: 11 stores, 2 outside services, 1 portal found nowhere; 10 two-store problems T1 to T10)')
# F-020
rep('F-020','**Stage journal exception has no owner and no removal trigger written anywhere.**','**Stage journal exception has no owner and no removal trigger written anywhere, and it has two names (stage.journal and stage-journal.jsonl).**')
rep('F-020','OWNER: name an owner and a removal trigger (EXCEPTIONS.md has the entry ready).','OWNER: name an owner and a removal trigger (EXCEPTIONS.md has the entry ready) and fix one file name in the texts that say stage.journal (L3-stores.md T9).')
# F-023 -> take
rep('F-023','| claim-not-backed | not in take |','| claim-not-backed | take |')
rep('F-023','**Table screen: README claims conflict','**Table screen (filmed in scene 10 of the run sheet): README claims conflict')
# F-026
rep('F-026','CUT-LIST.md: owner yes, move to archive, never delete.','CUT-LIST.md: owner yes, move to archive, never delete. After the review the list also names the files each move touches and the order (apply F-001 first).')

# new findings
new={
'F-029':"| F-029 | Major | ops | take | n8n-flows-real-v5/mf-sub-crm-mail.json:SendMail (lines 256-257), mf-recovery.json:AlertSend (line 177), mf-sub-crm-mail.json:CrmUpsert credential id (line 103), mf-form.json, mf-hook.json, mf-recovery.json:RunSub (SUB_WORKFLOW_ID) | **The take flows still contain placeholder values (FROM_ADDRESS_PLACEHOLDER, INTAKE_ADDRESS_PLACEHOLDER, HS_CRED_PLACEHOLDER, SUB_WORKFLOW_ID); if one is left in, mail or the sub-flow call fails and the only trace is an alert sent over the same mail server.** grep of the 4 real-v5 files shows these values; nothing in FIX-PLAN made replacing them a gate. | Take-day gate: after import, run `grep -c PLACEHOLDER` on the imported flow text and `grep -c SUB_WORKFLOW_ID` and require 0 (the generator arguments in V5-README fill them). Not patched: needs the laptop import. | design review (D-add-1) | OPEN |",
'F-030':"| F-030 | Major | security | take | n8n-flows-real-v5/mf-recovery.json:AlertSend and mf-sub-crm-mail.json:SendMail (same SMTP credential) | **The alert mail and the lead mail use the same mail server, so one mail outage stops both and nobody is told.** Single-dependency rule: a channel with no second route. F-010 names the shared credential but not the shared channel. | OWNER: second alert channel after the take (trigger: first real client build); until then the sheet must not claim alerts survive a mail outage. | design review (D-add-2) | OPEN |",
'F-031':"| F-031 | Major | ops | take | n8n-flows-real-v5/mf-recovery.json:ClaimStuck (state NOT IN done, review, unknown, failed) and AlertClaim (state IN unknown, failed) | **A lead with an invalid e-mail address ends in state review, and nothing alerts on it and nothing reads it again.** Checked in the two queries: review is excluded from both. Page statement 1 does not claim otherwise, but the order says no lost lead. | Decide a stop condition: either alert on review rows older than N minutes, or state in the sheet that review needs a person to look at the table. Not patched: flow change to test in n8n. | design review (D-add-5) | OPEN |",
'F-032':"| F-032 | Nit | store | take | n8n-flows-real-v5/mf-sub-crm-mail.json (writes), n8n-flows/mf_leads.sql (name, email columns) | **The lead table keeps name and e-mail with no expiry.** Made-up data in the take, so a Nit; for a client build it is a Major (purpose limit, delete after use). | OWNER: a purge sweep or a retention line in every client contract; F-003 patch already puts the retention line on the card. | design review (D-add-6) | OPEN |",
'F-033':"| F-033 | Nit | store | take | n8n-flows-real-v5/mf-sub-crm-mail.json:CrmUpsert | **HubSpot is wired directly into the real flow with no interface in front; only the film flow has a stand-in HTTP call.** Single-dependency rule: a second CRM kind is only half-outlined. | OWNER: one line in the client discovery options list (options-first rule); no change for the take. | design review (D-add-3) | OPEN |",
'F-034':"| F-034 | Nit | ops | not in take | n8n-tests/dn1_common.py:7, :59-61 | **A test helper deletes every file under DN1_DESK_REPO/data (default /tmp/rr/t3exp) with no check that the folder is a throwaway one.** Wrong DN1_DESK_REPO would delete real data. Part of the door-test chain (dn1.py, dn1_common.py, desk_proxy.py, run_dn1.py) that goes with the retired desk doors; mf.py imports dn1_common.py, so it cannot be archived alone. | CUT-LIST.md: archive the chain together with the doors after the owner's yes; until then run it only with a throwaway folder. | zoom-out review (Z-3) | OPEN |",
}
rows.update(new); order+=list(new)
# sort: take first then not in take; severity inside; id inside
sev={'Blocker':0,'Major':1,'Nit':2}
def key(fid):
    cells=[c.strip() for c in rows[fid].split('|')]
    return (0 if cells[4]=='take' else 1, sev[cells[2]], fid)
ids=sorted(order,key=key)
# build file
head=[l for l in lines if not l.startswith('| F-')]
# find table header index
hi=[i for i,l in enumerate(head) if l.startswith('| id |')][0]
out=head[:hi+2]+[rows[i] for i in ids]+head[hi+2:]
open(p,'w').write('\n'.join(out))
print(len(ids),'rows')
