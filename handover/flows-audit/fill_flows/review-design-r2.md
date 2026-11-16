# F3 review round 2: egm:egm-design (agent a4bc9f6927ac9fb69), condensed by flows-audit 2026-11-16
Verdict: no Blocker. 4 Majors, 5 Nits. Ran nothing (no shell). The six real $env uses (real-v5: DESK_URL, DESK_TIMEOUT_MS, DESK_ALERT_TO; film-v5: MF_STAGE_URL, MF_STAGE_TIMEOUT_MS, MF_CRM_URL) all pass the new refusal rules; no path printing a value, leaving a token with exit 0 or writing inside a repo found.
| id | sev | where | finding | fix |
|---|---|---|---|---|
| M1 | Major | do_delete --no-manifest (~481-486), README 69-71 | removes every .json in any folder holding only .json files; wrong --out loses user files | require tool signature (folder 0700, files 0600, owner = user); refuse folder with files still containing $env content; negative test; keep out of main README flow |
| M2 | Major | do_fill exit 0 + 'NOT READY TO IMPORT' | exit code says success while copy is not importable | distinct non-zero code (3) for written-but-incomplete, or --allow-placeholders; NOT READY line to stderr; test; count placeholders inside longer strings |
| M3 | Major | README step 1 | lead cannot follow credential/sub-flow id steps; second import creates a second sub-flow copy | numbered walk-through naming mf-sub-crm-mail.json, where ids are, delete the first import; rehearsal |
| M4 | Major | README | platform not stated; native Windows lacks os.O_NOFOLLOW; run location, --in relative path, ~/keep must exist; film keys not listed | say Linux/macOS/WSL; startup platform check; copy-paste block with full paths and key list per flow set |
| N1..N5 | Nit | scope surface; code key nested deeper loses ctx; bare repos documented; numeric *_MS not validated, URL trailing slash; add mutant disabling final scan | as stated |
