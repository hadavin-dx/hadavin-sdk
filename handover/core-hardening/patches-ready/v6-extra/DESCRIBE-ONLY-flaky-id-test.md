# Describe-only item (lead answer Q16.1, 10:42Z): random id matches a redaction pattern
Class: a random id collides with a redaction pattern. The cmdlet-shape rule in the write-command withholding list reads ids of the form prefix + 32 hex digits as a cloud command when they start with ec2 and the next character is a-f.
Effect: test_s4_llm_guard.py::test_ids_and_plan_hashes_survive_redaction fails about 1 run in 2,731 (exact sweep: 24 of 262,144 id shapes on the unpatched base). Not in the take path.
Where the fix belongs: at the redaction rule (one lookahead). A ready patch and 14 tests exist in FIX-id-vs-command-withheld.patch; it is a security path and not yet independently reviewed. Nothing under src/ or tests/ was edited on this branch. Decision for a later core branch is the lead's.
Guard failures on this branch are BRANCH ARTEFACTs (Q16.2): the vendor-string and non-UTF-8 file under handover/, and the non-proprietary LICENSE copies in promotion-inputs (decision 11).

## Added 2026-11-16 (C7b round 3 security review): pre-existing gap, describe-only per Q16
The cloud-cmdlet branch of `_WRITE_SHAPES` needs a letter after the module word, so `Remove-EC2*` (wildcard), `gcm Remove-EC2*` and a bare `Remove-EC2` may not match that branch. Unchecked whether `_PROGRAM` or another rule still catches them. Not caused by FIX-id-vs-command-withheld.patch. Next step for the lead: a test that feeds those three strings to the gate and a decision on a fix in src (we do not edit src/ or tests/).
