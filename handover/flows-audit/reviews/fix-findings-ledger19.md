# fix-findings-ledger19 (round 19 fixer; edited only FINDINGS.md and LEDGER-ROWS.md; nothing committed)

## Failures and uncertainty first
- Nothing I typed was run against n8n or Postgres. New commands I only wrote into the rows (not run): the F-029 four-name loop, the F-008 two recovery-file greps, the F-041 Part A and Part B commands (copied from TAKE-CHECKLIST Block R7 lines 315 to 325), the F-011 `cd "$REPO" &&` prefix, the F-002 patch apply line (copied from RUNBOOK step 2).
- Commands I ran (read-only): `grep -n` on handover/demo/VIDEO-RUNSHEET.md (copy at handover/demo/VIDEO-RUNSHEET.md, 22485 bytes), `grep -rn -i "killed after the mail left" handover/demo --include='*.md'` (4 hits today), the tool checks below.
- NOT filled, because no file gives the value (stay "NOT WRITTEN: LEAD FILLS"): the take folder path (Q31 item 59); the mailbox count command (T19 part 2 still cannot pass until written); $N8N_ROLE, $N8N_DB, $N8N_PW (F-011; no file defines them); the command that makes $EXPORT (F-029; scripts\n8n_api.py is not in the tree); the allowed-places list for F-041 part B and the second filter command is not copied (too long; the row says copy it from Block R7); the studio lead's dated re-read line that accepts the single F-007 allowed hit.
- Contested reviewer point: none. Reviewer words were each checked against the file text first. One reviewer claim checked and found true only in part: "cited :39 carries only K3/K3B": line 39 does carry the "seven safe columns" text, so it stays cited, for that text.
- Remaining bare word "lead" inside rows (all re-read, all kept on purpose): quoted ORDERS.md headings 'ANSWER (lead, ...' (verbatim file headings), the quote 'measured at rehearsal, lead sets', the file name V7-NUMBERS-lead-read.md, the quoted file word 'lead' in F-011, and the quoted video sentence 'a person has to look at this lead in the table' (F-042, a sales lead). Compound names (lead key, lead ID, mf_leads) were left, as the words list says.

## Finding to result
| # | Finding | Result |
|---|---|---|
| 1 | F-003 before/after order | Pass line now says part (1) runs BEFORE the apply, (2) and (3) AFTER it (RUNBOOK step 14); "today" replaced by "before the apply"; (1) saved before, (2)(3) after. |
| 2 | F-002 T19/T21 not doable from the row | New block COMMAND VARIABLES before the T19 command: the shas.env load line, $N8N_PORT (N8N_PORT="5690", RUNBOOK section 4), $KEEP/pg-secrets.env for $PGADMIN_PW and $FLOWS_PW (RUNBOOK I53), patch path and apply command (RUNBOOK step 2). Mailbox count command stays NOT WRITTEN: LEAD FILLS, now pointing to TAKE-CHECKLIST line 295. T20/T21 pointers changed. |
| 3 | F-007 allowed-hit list | Part (1) is now mechanical: output must be exactly one line starting `handover/demo/REPORT.md:49:`; today the grep prints 4 lines, so it fails before the patches. Studio lead's acceptance line stays NOT WRITTEN: LEAD FILLS. |
| 4 | F-029 grep form | One form: four runs of grep -rlF, one per name, loop written out, passing output stated; export command NOT WRITTEN; $FILLED/$EXPORT/$FLOWS set-once lines from RUNBOOK section 4 named. Artifact line changed to "four runs". |
| 5 | F-008 | Check (2) written out as two commands; check (3) says 0 is not passed; the ACCEPTED line and "(decision 4)" are stated as the script's own wording and numbering; $LOG/$FILLED defined from shas.env; default "nobody" means the checks are not run. |
| 6 | F-041 / F-011 | F-041: grep written out (Part A and Part B first command; filter command pointed to Block R7); "lead table" is now "sales lead table"; egm pointer added. F-011: `cd "$REPO" &&` added; password variables and undefined names listed; variables note pointer fixed. |
| 7 | word "lead" | Sweep of all 45 rows in both files (regex on "| F-" lines): "by lead order", "lead to confirm", "lead decides", "lead answers", "the lead ..." etc. became "studio lead"; "lead table/mail/e-mail" became "sales lead ...". Rescan: only the quoted items above remain. |
| smaller | F-002 "Intake:" | Summary now starts "In short:"; new words-list bullet defines "intake mailbox" once (and says bare "Intake" is not used). |
| smaller | F-002 08:22 UTC | "(13:52 IST)" added. |
| smaller | F-003 $REPO LEAD FILLS | Replaced by "the line REPO of shas.env (FIX-PLAN Step 0a (2) and (4))" in the 4 pass lines that used it (F-003, F-007, F-031, one more). |
| evidence slip | F-003 cites | Cite now `:33, :41, :51` (each holds "25 to 30"; also :5, :23, :79; :90 holds "60.1"), `:39` and `:62` ("seven" text). Checked with grep -n in handover/demo/VIDEO-RUNSHEET.md; the F-003 patch removes or rewords all 7 lines (6 lines with "25 to 30" are '-' lines of the patch plus line 90). |

## Raw outputs (run from handover/flows-audit)
- `python3 -I tools/check_refs.py` -> PASS 5178 references
- `python3 -I tools/check_names.py` -> PASS 655 rows
- `python3 -I tools/check_secrets.py` -> PASS 0 hits in 2727 files
- `python3 -I tools/count_findings.py` -> rows 45 unique 45; Blocker 5/0/5, Major 5/0/5, Nit 1/34/35, all 11/34/45
- compare14.py FINDINGS.md LEDGER-ROWS.md -> `45 45 differences: 0`
- `python3 -I tools/check_counts.py` -> PASS 52 files / 655 nodes
- `ruff format --check .` -> 874 files already formatted
Backups of the two files before my edit: scratchpad FINDINGS.bak and LEDGER.bak (/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/).
Token use: not measured.
