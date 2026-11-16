# fix-findings-ledger3 (fixer, 2026-11-16, static; nothing ran in n8n; edited only FINDINGS.md and LEDGER-ROWS.md; not committed)
Source: reviews/findings-ledger-design-r1.md (reviewer words unverified; each cited line opened first).
1. F-011 CONFIRMED by script before the fix: FINDINGS 5542 chars vs LEDGER 5467; the 3 deleted pieces were `PGPASSWORD="$PGADMIN_PW" ` before the three psql lines (CREATE ROLE, password, CREATE DATABASE). The older LEDGER:1 claim 'compared by script after fix-findings8' was WRONG (that comparison missed F-011); header now says how the new comparison was done. Only F-011 differed besides the two expected prefixes (F-001, F-013).
2. All 45 fix cells re-copied from FINDINGS into LEDGER (column 7), summaries (column 5), status (column 6), severity (column 3) re-derived; then the comparison below was run.
3. F-037/F-018/F-029: read the 4 flow files of handover/demo/n8n-flows-real-v5. $env reads: mf-sub-crm-mail.json:Qualify (DESK_URL, DESK_TIMEOUT_MS) 2, mf-recovery.json:AlertSend (DESK_ALERT_TO) 1; mf-form and mf-hook none. The alert path DOES read $env (AlertSend). Wiring if blocked: Qualify error -> OutStage, row stays processing, ClaimStuck retries (attempts<3), MarkFailed sets failed after 3 attempts, AlertClaim selects it, AlertSend fails under the same block -> AlertBackoff, no mail. So F-037's 'every lead ends unknown and alert' is WITHDRAWN (state is failed, no mail); F-029 'could fail silently' fits for the mailbox; F-018 fits. All marked UNVERIFIED. Severities unchanged. (My first reading missed the MarkFailed node; found by a second query and corrected before editing.)
4. FINDINGS glossary: new bullet after the 'take' bullet (sales lead, studio lead, owner, take x4, re-pin, GO row 6, claim, review, unknown, K3/K3B, Reading A, ORDER/Q/N7/round cites). 'the lead' in the 10 rows converted by rule (sales lead vs studio lead); compound names (lead key, lead ID, lead table, lead data, lead name), 'LEAD FILLS', quoted pasted text (F-007 K3B table and spoken line) left as written. Other 35 rows and other files still say 'the lead' (not converted; glossary says same meaning).
5. One 'DECISION (summary ...)' line appended to the fix cell of each of the 10 Blocker/Major rows (what is wrong, take risk, fix, who decides by when, what if nobody answers; 'not stated' where no file says). Lead decisions not invented.
6. 'out' rows: F-002 consequence from its row (NO-GO if open at Wed 18 Nov 07:30Z); F-007 and F-031: stay Blocker until applied and re-read by Wed 06:00Z (Q30 item 2); effect on the take not stated, studio lead decides. F-003: no default exists; question is for the studio lead; LEDGER area flag now 'studio lead decides (no default exists; ...)'.
7. UNVERIFIED marks added: F-002 (default 500, ON CONFLICT idempotent, '4 harmless posts', N = test limit not a video line), F-007 (one alert vs F-014 repeat, 0 mails/1 mail), F-008 (2,880 runs a day), F-029 (placeholder fails at first run), F-041 (count 15), F-037/F-018 alert half. F-031: where state review is set is now cited (mf-form.json:Claim, mf-hook.json:Claim) - checked in the files, so not UNVERIFIED. F-029 'last two names' now named with counts (PG_CREDENTIAL_ID 14, SMTP_CREDENTIAL_ID 2, grep -o). F-029 bold sentence 'the only trace is' -> 'the trace named here is' (the ledger summary follows). F-011 'OWNER decided' label reconciled with the evidence cell; 'remove the SQLite exception' vs 'NOT an exception' clash stated in the DECISION line (studio lead says which edit), not guessed.
8. F-001 status wording: FIXED-UNVERIFIED here = patch dropped, nothing applied, only the psql gate unrun.
## Comparison script (inline python3, run from flows-audit; result printed below)
```
import re
def rows(p):
    d={}
    for l in open(p,encoding='utf-8'):
        if l.startswith('| F-'):
            c=[x.strip() for x in l.rstrip('\n').strip().strip('|').split(' | ')]
            d[c[0]]=c
    return d
F=rows('FINDINGS.md'); L=rows('LEDGER-ROWS.md')
print('ids FINDINGS',len(F),'LEDGER',len(L),'only in one:',sorted(set(F)^set(L)))
PRE={'F-001':"DROPPED by the lead (Q17-3, 2026-11-16); status FIXED-UNVERIFIED because the psql check is not run yet. ",'F-013':"ACCEPTED as a trade-off by the lead (ORDERS.md line 138, item 2; severity unchanged, status stays OPEN as in FINDINGS). "}
cols=['id','source','severity','take-path','summary','status','fix']
diff=collections=[]
n=0
for i in sorted(F):
    f,l=F[i],L[i]
    m=re.match(r"\*\*(.*?)\*\*",f[6])
    exp={'id':(f[0],l[0]),'source':('FINDINGS.md '+i,l[1]),'severity':(f[1],l[2]),
     'take-path':('yes' if f[3].startswith('take') else 'no', re.search(r"TAKE-PATH: (yes|no)",l[3]).group(1)),
     'summary':(m.group(1) if m else None,l[4]),'status':(f[9].split()[0],l[5]),'fix':(PRE.get(i,'')+f[7],l[6])}
    for c in cols:
        n+=1
        a,b=exp[c]
        if a!=b: diff.append((i,c,len(a or ''),len(b)))
print('cells compared',n,'(45 ids x 7 columns); differences:',len(diff))
for d in diff: print('DIFF',d)
```
## Result
```
ids FINDINGS 45 LEDGER 45 only in one: []
cells compared 315 (45 ids x 7 columns); differences: 0
--- count_findings
rows 45 unique 45
| Blocker | 5 | 0 | 5 |
| Major | 5 | 0 | 5 |
| Nit | 1 | 34 | 35 |
| all | 11 | 34 | 45 |
sev {'Blocker': 5, 'Major': 5, 'Nit': 35}
--- check_refs
PASS 5176 references
--- check_names
PASS 655 rows
--- check_secrets
PASS 0 hits in 1987 files
--- ruff format --check .
701 files already formatted
```
Not checked: flow-check/raw (check_secrets passed over 1986 files this time); no n8n run; the lead-word conversion is by rule, so a few pre-existing bare words may be in the wrong sense (list reviewed by eye).
