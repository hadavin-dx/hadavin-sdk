# evidence-r3: roles-coverage-check mutation run (raw, no judgement)
Scratch: /tmp/rolesev/. Script: check_grants_cover_queries.py (grants are hardcoded in the script, dict G; it reads no grants file). Flows: handover/demo/n8n-flows-real-v5 and -film-v5 (copied).

## SURVIVED (exit code 0)
- g7 extra table-level grant (added email name crm_id to mf_sub SELECT): rc=0 (script only checks missing grants, cannot see extra ones; a table-level grant has no representation in G)
- f3 add DELETE (MarkDone query replaced by DELETE FROM mf_leads...): rc=0 (script reads no DELETE privilege)
- f4 second table (Stored reads FROM secret_other): rc=0 (script ignores table names)
- zero Postgres nodes folder: rc=0, "0 postgres nodes" (passes silently)
- nonexistent folder: rc=0, "0 postgres nodes" (passes silently)

## KILLED (non-zero)
- g1 door SELECT minus claim_token: rc=1
- g2 door INSERT minus attempts: rc=1
- g3 sub UPDATE minus mail_sent: rc=1
- g4 recover SELECT minus claimed_until: rc=1
- g5 recover UPDATE minus claim_token: rc=1
- g6 alert UPDATE minus alert_sent: rc=1
- g8 missing role mf_alert: rc=1 (by uncaught KeyError traceback, not a clean message)
- f1 new column read (email in MarkDone): rc=1
- f2 UPDATE target changed (SET attempts=0 in MailClaim): rc=1
- malformed JSON: rc=1 (uncaught JSONDecodeError traceback)

## Baseline
real-v5 + film-v5: rc=0, 14 postgres nodes each, TOTAL UNCOVERED OR UNMAPPED: 0

## Raw output
### base
```
real: 14 postgres nodes
film: 14 postgres nodes
TOTAL UNCOVERED OR UNMAPPED: 0
```
### out_g1_door_select
```
real mf-form Claim -> mf_door: UNCOVERED [('SELECT', 'claim_token')]
real mf-hook Claim -> mf_door: UNCOVERED [('SELECT', 'claim_token')]
real: 14 postgres nodes
film mf-form Claim -> mf_door: UNCOVERED [('SELECT', 'claim_token')]
film mf-hook Claim -> mf_door: UNCOVERED [('SELECT', 'claim_token')]
film: 14 postgres nodes
TOTAL UNCOVERED OR UNMAPPED: 4
```
### out_g2_door_insert
```
real mf-form Claim -> mf_door: UNCOVERED [('INSERT', 'attempts')]
real mf-hook Claim -> mf_door: UNCOVERED [('INSERT', 'attempts')]
real: 14 postgres nodes
film mf-form Claim -> mf_door: UNCOVERED [('INSERT', 'attempts')]
film mf-hook Claim -> mf_door: UNCOVERED [('INSERT', 'attempts')]
film: 14 postgres nodes
TOTAL UNCOVERED OR UNMAPPED: 4
```
### out_g3_sub_update
```
real mf-sub-crm-mail MailClaim -> mf_sub: UNCOVERED [('UPDATE', 'mail_sent')]
real: 14 postgres nodes
film mf-sub-crm-mail MailClaim -> mf_sub: UNCOVERED [('UPDATE', 'mail_sent')]
film: 14 postgres nodes
TOTAL UNCOVERED OR UNMAPPED: 2
```
### out_g4_recover_select
```
real mf-recovery ClaimStuck -> mf_recover: UNCOVERED [('SELECT', 'claimed_until')]
real mf-recovery MarkFailed -> mf_recover: UNCOVERED [('SELECT', 'claimed_until')]
real: 14 postgres nodes
film mf-recovery ClaimStuck -> mf_recover: UNCOVERED [('SELECT', 'claimed_until')]
film mf-recovery MarkFailed -> mf_recover: UNCOVERED [('SELECT', 'claimed_until')]
film: 14 postgres nodes
TOTAL UNCOVERED OR UNMAPPED: 4
```
### out_g5_recover_update_claim_token
```
real mf-recovery ClaimStuck -> mf_recover: UNCOVERED [('UPDATE', 'claim_token')]
real: 14 postgres nodes
film mf-recovery ClaimStuck -> mf_recover: UNCOVERED [('UPDATE', 'claim_token')]
film: 14 postgres nodes
TOTAL UNCOVERED OR UNMAPPED: 2
```
### out_g6_alert_update_alert_sent
```
real mf-recovery AlertMark -> mf_alert: UNCOVERED [('UPDATE', 'alert_sent')]
real: 14 postgres nodes
film mf-recovery AlertMark -> mf_alert: UNCOVERED [('UPDATE', 'alert_sent')]
film: 14 postgres nodes
TOTAL UNCOVERED OR UNMAPPED: 2
```
### out_g7_extra_table_level_grant
```
real: 14 postgres nodes
film: 14 postgres nodes
TOTAL UNCOVERED OR UNMAPPED: 0
```
### out_g8_missing_role_mf_alert
```
Traceback (most recent call last):
  File "/tmp/rolesev/g8_missing_role_mf_alert.py", line 67, in <module>
    sel, ins, upd = G[login]
                    ~^^^^^^^
KeyError: 'mf_alert'
```
### out_f1_new_col_read
```
f1_new_col_read mf-sub-crm-mail MarkDone -> mf_sub: UNCOVERED [('SELECT', 'email')]
f1_new_col_read: 14 postgres nodes
TOTAL UNCOVERED OR UNMAPPED: 1
```
### out_f2_update_target
```
f2_update_target mf-sub-crm-mail MailClaim -> mf_sub: UNCOVERED [('UPDATE', 'attempts')]
f2_update_target: 14 postgres nodes
TOTAL UNCOVERED OR UNMAPPED: 1
```
### out_f3_delete
```
f3_delete: 14 postgres nodes
TOTAL UNCOVERED OR UNMAPPED: 0
```
### out_f4_second_table
```
f4_second_table: 14 postgres nodes
TOTAL UNCOVERED OR UNMAPPED: 0
```
### out_zero
```
empty: 0 postgres nodes
TOTAL UNCOVERED OR UNMAPPED: 0
```
### out_bad
```
        parse_float=parse_float, parse_int=parse_int,
        parse_constant=parse_constant, object_pairs_hook=object_pairs_hook, **kw)
  File "/usr/local/lib/python3.13/json/__init__.py", line 352, in loads
    return _default_decoder.decode(s)
           ~~~~~~~~~~~~~~~~~~~~~~~^^^
  File "/usr/local/lib/python3.13/json/decoder.py", line 345, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.13/json/decoder.py", line 361, in raw_decode
    obj, end = self.scan_once(s, idx)
               ~~~~~~~~~~~~~~^^^^^^^^
json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
```
### out_nodir
```
nonexist: 0 postgres nodes
TOTAL UNCOVERED OR UNMAPPED: 0
```
