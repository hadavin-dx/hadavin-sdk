# F3 review round 1: egm:egm-codebase-details (agent a0671d900adfe41ac), saved condensed by flows-audit 2026-11-16
Verdict: no Blocker. 6 Majors, 12 Nits. Read evidence-f3.md at the end. Grep of 8 real flow files: exactly 6 $env uses, all in ={{ }} expressions as $env.NAME (real: DESK_URL, DESK_TIMEOUT_MS, DESK_ALERT_TO; film: MF_STAGE_URL, MF_STAGE_TIMEOUT_MS, MF_CRM_URL).
| id | sev | where | finding | fix |
|---|---|---|---|---|
| R1-01 | Major | fill_flows.py:262-270 do_check | check scans raw text: "$env.DESK_URL" as a plain JSON string and $env[\"X\"] are missed or mislabelled; check can say clean while a token exists | json.loads each file and scan walked strings and keys; test both forms |
| R1-02 | Major | test_fill_flows.py:201-216 | $env.PATH half passes for the wrong reason (leftover dyn entry) | clean flow for PATH case, assert exit 1 and PATH in stderr |
| R1-03 | Major | test_fill_flows.py:248-267 | "new\nline" case never reaches control-char check; asserts near-vacuous | assert specific message per bad value; test newline separately |
| R1-04 | Major | tests canary | mutant M2 (values dict appended to refusal message) survives; canary asserted only on success, CRLF, check paths | one helper over all Negative and Delete tests that fails if any VALS value appears in stdout/stderr; rerun M2 |
| R1-05 | Major | test_fill_flows.py:100-122 | film substitution content never asserted; canary vacuous for film | assert exact expressions for MF_STAGE_URL, MF_STAGE_TIMEOUT_MS, MF_CRM_URL |
| R1-06 | Major | tests | no fill test with token in dict key, list element, node name, credential, pinData | fixture with token in each location; assert substitute or refuse |
| R1-07..18 | Nit | token outside braces; quotes/space; bare repo; cleanup leaves state (mkdir inside try, manifest not in created); dead code :186; .JSON skipped silently; O_NOFOLLOW on input; unlink via dir_fd; NaN/Infinity; placeholder count; EXIT_NOTHING literal; fixed /tmp/ff13; README brace text | see agent text |
