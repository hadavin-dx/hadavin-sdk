# Reader 1, guard/redact.py lines 1-300 (range 40-260 plus context), saved condensed by core-hardening 2026-11-16. Static read, nothing run. Reader report is unverified until I spot-check.
Not confirmed: (1) mask reversibility: header says masked values are "stored restored" (redact.py:35-37), so a map placeholder-to-value exists; where it lives and who can read it was NOT READ (restore, redact_many, _sweep). (2) flag sets differ: JWT eyJ prefix, key prefixes and IBAN country code are case-sensitive (redact.py:187, 195, 249-252); whether a case-folding pass exists is NOT READ.
Per pattern (tests = grep of tests/warden_port only):
- PRIVKEY PEM :156-162 catches BEGIN..END PRIVATE KEY or to end of text; test positive only (test_redaction_review.py:54); no test of missing END.
- PRIVKEY PuTTY :164-167 positive only (:57).
- ARN :169 12-digit or empty account; stops at ; , = ( ) ? & # quotes; ARN: uppercase not matched; one positive test (test_redaction.py:47); lookahead bounded at 40.
- GCPRESOURCE :171-174 projects/<id>; no test; false positive: ordinary paths like /home/me/projects/myapp over-masked.
- AZURERESOURCE :175-181 /subscriptions/<uuid>; no test; correctly before UUID.
- JWT :184-189 eyJ + 3-5 segments up to 4096 each; no test; longer segments leave a tail in clear.
- APIKEY prefixes :195 (24 prefixes at :120-143, 8+ chars); positive only (test_redaction.py:285-289, :392); case-sensitive; over-masks words like sk-learn-docs, npm_ identifiers.
- SendGrid :197, whsec_ :200, Vault s./b./r. :203: no tests; Vault rule over-masks b.AbCd...-style names.
- GCPTOKEN :206 ya29.: positive only (test_redaction.py:409).
- AZURESAS :208 sig= 16+ chars: positive (:87), no negative; any sig= value over-masked.
- WEBHOOK :211-220 Slack, Discord, Teams webhookb2 only; no Teams test; other chat hooks and new Teams workflows URLs not covered.
- URLCRED :226-231 password only masked; positive (test_redaction.py:179, test_redaction_review.py:24), no negative; bounded 1024; timing UNVERIFIED.
- EMAIL :235-240 misses quoted local parts, [at], IDN, line-split, double-encoded %2540; over-masks git@github.com style.
- IBAN :246-254 only [A-Za-z0-9]: the spaced display form "DE89 3704 ..." is NOT matched (likely real leak, UNVERIFIED whether a later bank/phone pattern catches it); lower-case country code not matched; tests positive and negative (test_redaction.py:296-303, test_redaction_bank.py:256), none for spaced form.
- UUID :256-260 masks every UUID incl. request ids (by design); no negative test.
Ordering: no broad-before-narrow problem found in 40-260. Possessive quantifiers used on purpose (:58). _CRED_FLAG (:40-44) use not seen (NOT READ).
Reader's severities: Major: spaced IBAN (:252); Major: no mask-type test for PEM, ARN, GCP, Azure resource, JWT, SendGrid, Vault (tests outside warden_port UNVERIFIED); Major UNVERIFIED: reversibility; Nit: GCP and Vault over-mask; Nit: webhook coverage.
