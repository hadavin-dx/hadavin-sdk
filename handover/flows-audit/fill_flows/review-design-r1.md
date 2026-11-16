# F3 review round 1: egm:egm-design (agent a519a46e296a0d928), static, saved condensed by flows-audit 2026-11-16
Verdict: no Blocker. No path where a value reaches stdout, stderr, manifest or exception; no path where a token is left and exit is 0. 9 Majors, 6 Nits. Did not read evidence-f3.md; ran nothing.
| id | sev | where | finding | fix |
|---|---|---|---|---|
| R1-01 | Major | Subst.string, token outside {{ }} in "=" field | raw replace changes meaning; non-greedy split ends at first "}}" | refuse token outside clean {{ }}; refuse odd/nested braces; tests |
| R1-02 | Major | plain-field path | token in jsCode/functionCode/pythonCode becomes a syntax error | refuse in those params or state in README |
| R1-03 | Major | do_fill manifest last | kill between files and manifest leaves folder no tool can remove | manifest first; delete --no-manifest; README rm line |
| R1-04 | Major | read_values | values file not checked for mode, symlink, git repo, /mnt | refuse inside git, under /mnt, group/other bits; refuse --out under /mnt; README advice |
| R1-05 | Major | F-029 gate vs fill | fill exits 0 with 6 placeholders left (PG_CREDENTIAL_ID, SMTP_CREDENTIAL_ID, SUB_WORKFLOW_ID, HS_CRED_PLACEHOLDER, FROM_ADDRESS_PLACEHOLDER, INTAKE_ADDRESS_PLACEHOLDER) | values file may carry the placeholder names, whole-string replace; print NOT READY TO IMPORT: N left; README order |
| R1-06 | Major | JS-literal approach | token inside JS string in expression gives syntax error; raw value with "{{" starts an expression; n8n never parsed filled text | refuse token inside quoted JS string; refuse value with "{{"; loopback re-smoke on filled copy as named take-day gate |
| R1-07 | Major | README | unexplained terms (rung 7, O_EXCL, sha256, manifest, idempotent, stdout); no example, no sample values file, no after-fill steps | rewrite top-down, plain words |
| R1-08 | Major | read_values | quotes, trailing spaces, inline " # note", BOM are silent traps | refuse quoted/space-edged values; warn on " #"; BOM message |
| R1-09 | Major | delete scope | values file, imported workflows, saved executions stay; unlink is not a wipe | README clean-up checklist; say not a secure wipe |
| R1-10..15 | Nit | manifest sibling / reformat / exit 4 / empty value / tests dead condition / inside_git sync folders | see agent text | document; parallel-walk self-check; README lines; remove dead condition |
