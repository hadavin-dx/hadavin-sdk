# EGM RESULT review of the trigger config (D-config) (egm:egm-codebase-details, model sonnet, fresh reviewer, one round; 2026-11-20 06:49 to 06:58 UTC)
Nothing run; the reviewer had no git access, so core-a's test file on origin was not read. Result: 0 Blockers, 3 Majors, 6 Nits. DRAFT 2 matches the code on names, bounds, defaults, texts, strictness and the registry refusals; config_hash is unaffected.
| # | sev | finding | answer |
|---|---|---|---|
| 1 | Major | overlap and duplicate checks compare exact strings, but the secret kinds fold spellings onto one secret (env: upper-cased, non-alphanumerics to "_": "db-pass", "DB_PASS", "db.pass" are one variable; file: paths resolve: "x", "./x"); a sender can list "SLACK_TOKEN" while a backend uses "slack-token" and app.trigger_secret returns the Slack token; two senders "a-b" and "A_B" share one value | D-config fix round 2 RUNNING (builder adc513b3): one canonical name function compared in both places, "/" dropped from the charset |
| 2 | Major | app.trigger_secret calls the provider bare: provider errors name the secret (env provider, cache, file, Vault); the draft's "the name is never printed" holds only at start-up | F-store fix round 3 RUNNING (builder a99a298a, item F5): fixed-text error from None |
| 3 | Major | no trigger-config test in this tree (core-a's file lives on origin; 16 expected-failure marks to remove, one text to change) | stated; the merge of core-a's file is the lead's integration step; plus two tests I ask core-a for: an alias test and "provider not called for an unlisted name" (requests/001.answer.md DRAFT 3) |
| 4 | Nit | stale top half of the answer file | header "superseded by DRAFT 2" added; DRAFT 3 lists the rest |
| 5 | Nit | DRAFT 2 omits: sender secrets are checked in a step before the main check; a non-live sender agent refuses the whole start (also other senders); a bad sender key is shown in the pydantic location | DRAFT 3 |
| 6 | Nit | retired agent after start: the registry is loaded once; a sender keeps being served until restart, then the start is refused; Runtime.handle checks only that the agent exists | DRAFT 3; the worker must also check (stated) |
| 7 | Nit | ConfigError chained from the ValidationError keeps the bad input in .errors(); __context__ of a provider error keeps the name | noted: printing hides them, code that walks __cause__ does not; low risk |
| 8 | Nit | agent and principal id pattern is stricter than the registry's free text ("svc@corp" can never be a sender) | stated in DRAFT 3 |
| 9 | Nit | unhashable argument to trigger_secret raises TypeError | harmless |
Checked and held: names, fields and bounds; config.Triggers outside config_hash; strict types; trailing newline not accepted; no log line or audit row carries a sender secret name; the overlap check runs before any provider read; no config passes load and crashes at build.
Not checked: core-a's test file; AWS, Azure and GCP name rules; the worker code (not in this tree).
