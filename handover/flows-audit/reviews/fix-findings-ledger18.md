# Fix report, round 18 (findings and ledger rows)

Date: 2026-11-16. Author: the round 18 fixer sub-agent. Files edited: FINDINGS.md and LEDGER-ROWS.md only.

## Failures and uncertainty first

1. The typed commands I wrote into fix cells (SQL against Postgres, curl and awk against n8n) were NOT run, except the F-028 awk, which I ran on a scratch copy with the F-004 patch applied (result 19 against Total 19). The old awk printed 20 (it counted the struck statement); this was a real defect in the earlier pass line and is fixed.
2. compare14.py is a loose check (cell text equality); it does not prove the words mean the same thing in context. It shows 45 45 differences: 0.
3. "First send = step 16" is the audit's own reading of the runbook, not something I confirmed by running the flow.
4. The item 9 sweep ("sales lead" for a customer, "studio lead" for the person) is not exhaustive. I rewrote the clear cases; about 38 bare "lead" hits remained at the last scan, many of them quoted headings or already the studio-lead meaning. I did not re-read every one after the final replacement batch.
5. Item 11: two records disagree on the historical counts, so I did not restate the counts. Needs the studio lead if a single figure is wanted.
6. No EGM step was run from this sub-agent (the skills cannot be invoked from here). Review of this result is still needed from an independent reviewer.
7. Not committed. Mailbox count in F-002 is marked NOT WRITTEN: LEAD FILLS (input: the real mailbox count the studio lead sees on Tuesday).

## Finding to result

| Item | Result |
|---|---|
| 1 to 4, 6 to 8, 10 | Fixed in both files (F-002 stop rule and status 200 check, F-029 wording, F-001 psql gate, F-007, F-031, F-008, F-041, F-011 owner sheet control). |
| 5 | Partly contested with evidence: "names only R2-tables.md" checked by running TAKE-CHECKLIST Block R7 Parts A and B read only (Part B filters FINDINGS.md out by path). "15 ways" recounted as 15 numbered table rows. Wording adjusted. |
| 9 | Sales lead and studio lead separated in F-009, F-012 to F-017, F-021, F-035, F-011, F-018, F-043, F-001 and others. Not exhaustive (see 4). |
| 11 | Round 7 history bullet rewritten; counts not restated (see 5). |
| 12 | New row 12 in the inputs table (now "twelve rows"). |
| 13 | "ALSO USED EARLY" bullet added; grace period bullet expanded. |
| 14 | Item 59 grace noted: counts from the step 1 start (04:00Z, 09:30 IST; 03:31Z, 09:01 IST on start option 1); item 59 due 03:30Z (09:00 IST); 24-minute Tuesday cap on waits; re-pin 269 minutes ending 08:29Z (13:59 IST). In the item 59 row, inputs row 10 and F-003. |
| 15 | 08:53Z note added. |
| 16 | F-028 awk replaced (tested). |
| 17 | F-034, F-046, F-019, F-020 notes and wording. |

(The item numbers follow reviews/findings-ledger-reader-r17.md; the grouping above is by what I changed, so check the item to row mapping against that file.)

## Proposed Q31 texts

None needed. Items 111 (REPO eighth value of item 59) and 112 (who runs F-011 fix A) already exist and are referenced. The only open input is the mailbox count (see 7), which the studio lead supplies; if a Q31 item is wanted: "Q31: what mailbox count does the studio lead expect to see on Tuesday before step 1 (04:00Z, 09:30 IST)?"

## Raw outputs (from the final run)

== python3 -I tools/check_refs.py
PASS 5177 references
rc=0
== python3 -I tools/check_names.py
PASS 655 rows
rc=0
== python3 -I tools/check_secrets.py
PASS 0 hits in 2717 files
rc=0
== python3 tools/count_findings.py
rows 45 unique 45
| Blocker | 5 | 0 | 5 |
| Major | 5 | 0 | 5 |
| Nit | 1 | 34 | 35 |
| all | 11 | 34 | 45 |
sev {'Blocker': 5, 'Major': 5, 'Nit': 35}
rc=0
== ruff format --check .
865 files already formatted
rc=0
== python3 /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/compare14.py FINDINGS.md LEDGER-ROWS.md
45 45 differences: 0
rc=0
