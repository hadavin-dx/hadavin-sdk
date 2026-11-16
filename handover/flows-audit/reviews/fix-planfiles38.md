# Fix report for reviews/plan-files-reader-r38.md (FIXER round 38; edited RUNBOOK.md, TAKE-CHECKLIST.md, FIX-PLAN.md only)

Not committed. No sub-agents. No spend. Nothing was run against n8n, Postgres or a mailbox; shell lines were checked with `bash -n` and tiny fake-data runs only. EGM review of this result is the lead's step.

## Not done or not checked (first)
- Item 12 (second half), the 04:46 / 04:56 versus 04:40 / 04:50 times: not changed; RUNBOOK step 4a (about line 215) and section 6 (about line 275) already say the 24-minute cap governs and 04:46Z is only the uncapped worst case. Which rule governs in Case B (message about 12:22Z, after the 12:00Z limit) stays a LEAD CHOICE (fix-planfiles37 decision 3); I only wrote that down next to the row.
- Item 13 section 1 is still a changelog; I added a reading note and the code key (B/M/N, I<n>), not a rewrite (rewrite would need the lead's decision about what section 1 holds).
- Item 16: whether n8n_drive.py is the T19-T21 runner is not in ORDERS; I wrote "the lead says (I18)". Needs lead.
- Item 15: the credits ceiling for about 10 sends is a lead question (needs lead; not a new money yes).
- Item 9: who the judge is, and whether the same person as PIN_NAME, stays the lead's open choice (Inputs-list item 24).
- The reviewer's line numbers came from snapshot r37; each item was re-found by text. Several were already fixed by the r37 fixer (below).
- RUNBOOK 177-end and TAKE-CHECKLIST 81-end were not part of this brief and I did not re-read them.

## Per item (reviewer words checked by text)
1. need_new on empty: r37 already refused empty; now it also refuses a REPLACE_ME word; text says `need_set` then `need_new` in one chain. Tested: empty rc=1, REPLACE_ME rc=1, new path ok-new-RECORDING rc=0, existing path rc=1.
2. keysave without openssl: already guarded (command -v openssl, length 17 test) before this round; reviewer was on an old snapshot. No change.
3. input_ready versus need_set: sentence added to "Answer cells" (who makes inputs/, input_ready never runs or sources a file, a stray NAME.sh for a value name is a lead error).
4. Bootstrap loop on empty: now `case "${!V:-}" in ''|REPLACE_ME*)`, message "still a placeholder or empty". Tested: NEW="" prints `still a placeholder or empty: NEW` and `bootstrap-BLOCKED`.
5. sha append: hex test `[[ "$SHA_X" =~ ^[0-9a-f]{40}$ ]]` added in the `&&` chain before every write (RUNBOOK steps 4, 4b, 6, 13; TAKE-CHECKLIST Block R3, P1c, P2c; FIX-PLAN Steps 3 and 4c); no pipe (table cells). Positive control: empty and `abc` refused, 40 hex accepted. Block R3: added `test -r/-s "$ENVSH"` refusal before the grep (grep exit 2 read as no match). The assignment already ended the chain on a git failure (status of an assignment is the command's), so the reviewer's "appends `SHA_X=`" case needed an empty output; now closed. Stale "this round does not edit Block R3" sentence replaced.
6. KEYS / "five keys": wording now "three keys (KEY, KEYF, KEYH) and two derived values (ADDR, KEYS)"; KEYS holds KEY only; 19a gate names KEYF and KEYH itself (step 19a text already says so).
7. Q31 numbers: REPO skeleton word is now REPLACE_ME_Q31_111 (item 111 is the eighth value of item 59); WAIT_S times were already given roles by r37 (08:29Z due; 05:45Z last time to change). No change there.
8. "only hand-typed line" and "typed in the call": both defined (one line in the same shell, no export, kept because the skeleton uses `${NAME:-default}`); section 4 line 72 corrected; heading "Per-run names survive re-sourcing" is in section 4 (line about 189), the reviewer did not read that far.
9. "lead" two meanings and judge: new Terms bullet ("lead" alone = Claude session; "send" defined) and a judge row in the roles table (person, not a session; same person as PIN_NAME is a lead choice).
10. Pin line writer: RUNBOOK item 3 of section 1 now says the person gives name and date and the lead writes line 2 with Block P1b/P2b; header says file line 1 is a comment, reviewed-by is file line 2, the checked header is lines 2 to 5.
11. key/gate: "the key revocation" is now "model-key revocation"; every bare "gate" inside the start-state gate term now says "start-state gate". NOT CHECKED: reviewer wrong on RB 61, that text already says only (e) may be NOT CHECKED and a not-run (a) to (d) is a FAILED gate; allowed uses are listed in TAKE-CHECKLIST line 6 (r37).
12. Recording-ready message: sentence added in both clock-block copies (identical edit). Table 4a: see above.
13. Status header: now "newest fix round 38" with the fix-log range; reading note and code key at the head of section 1.
14. Terms: new bullet defining F-nnn, T19-T21, Block R1-R8/P1a-P2c, Words box, Placeholder table (pointers to FINDINGS.md and TAKE-CHECKLIST headings).
15. Spend versus sends: "send" defined; the ~10-send versus "up to 3 sends" gap stated as a lead question (Inputs-list item 19, I41, I43).
16. Six scripts: listed in RUNBOOK section 1 item 5 and tied to Inputs-list item 7; branch-review sequence for run_real_check_n8n.py and the post-twice script stated.

## Checks (final run, from handover/flows-audit)
- python3 -I tools/check_refs.py: PASS 5192 references
- python3 -I tools/check_names.py: PASS 655 rows
- python3 -I tools/check_secrets.py: PASS 0 hits in 2842 files
- python3 -I tools/check_counts.py: PASS 52 files / 655 nodes
- Clock block: `diff <(sed -n 37,84p FIX-PLAN.md) <(sed -n 8,55p TAKE-CHECKLIST.md)` empty (CLOCK-SAME)
- bash -n: all 28 fenced blocks of RUNBOOK and TAKE-CHECKLIST (fence-tag parser, no failures) and the 7 changed inline sha commands: ok
- ruff format --check .: 967 files already formatted

## Lead must decide (unchanged from r37 plus new)
r37 list items 1 to 8 stay untouched. New: (a) who the judge is and whether same as PIN_NAME (Inputs-list item 24); (b) the credits ceiling for about 10 sends; (c) whether n8n_drive.py is the T19-T21 runner; (d) Case B recording-ready message after 12:00Z.

Scratch originals: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/orig38/
